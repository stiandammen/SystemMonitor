"""
USB Discovery Module
USB device detection using pyusb and WMI
"""
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable

from .classification import DeviceClassifier, DeviceType


@dataclass
class USBDevice:
    """Discovered USB device"""
    name: str
    device_id: str
    device_type: DeviceType = DeviceType.USB_DONGLE
    vendor: str = ""
    description: str = ""
    driver: str = ""
    serial: str = ""
    status: str = "online"
    hub: str = ""
    parent_id: str = ""
    vid: str = ""
    pid: str = ""
    connected: bool = True
    last_seen: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        cfg = DeviceClassifier.get_type_config(self.device_type)
        return {
            "id": f"usb_{self.device_id.replace(':', '_').replace('\\', '_')}",
            "name": self.name or self.description or "USB Device",
            "ip": "N/A",
            "mac": self.serial.upper() if self.serial else "N/A",
            "vendor": self.vendor or "Unknown",
            "type": self.device_type.value,
            "type_label": cfg.label,
            "type_color": cfg.color,
            "type_glyph": cfg.glyph,
            "status": self.status,
            "ping": 0,
            "ports": [],
            "services": [self.driver] if self.driver else [],
            "os": self.description or "N/A",
            "connection_type": "usb",
            "last_seen": self.last_seen.strftime("%H:%M:%S"),
            "is_adapter": False,
            "vid": self.vid,
            "pid": self.pid,
            "device_id": self.device_id,
        }


class USBDiscovery:
    """USB device discovery using WMI and PowerShell"""

    def __init__(self):
        self._devices: Dict[str, USBDevice] = {}
        self._lock = threading.Lock()
        self._scanning = False
        self._available = platform.system() == "Windows"

    def is_available(self) -> bool:
        """Check if USB discovery is available"""
        return self._available

    def _classify_device(self, name: str, description: str, vendor: str) -> DeviceType:
        """Classify USB device by name and description"""
        name_lower = name.lower()
        desc_lower = description.lower()
        vendor_lower = vendor.lower()

        # Audio devices
        if any(x in name_lower + desc_lower for x in ["audio", "sound", "dac", "headset", "microphone", "mic", "speaker"]):
            if any(x in vendor_lower for x in ["focusrite", "scarlett", "behringer", "presonus", "universal audio", "motu", "rme", "steinberg", "native instruments"]):
                return DeviceType.AUDIO_INTERFACE
            return DeviceType.HEADSET

        # Webcams
        if any(x in name_lower + desc_lower for x in ["camera", "webcam", "video", "capture"]):
            return DeviceType.WEBCAM

        # Storage
        if any(x in name_lower + desc_lower for x in ["disk", "storage", "flash", "usb drive", "mass storage"]):
            return DeviceType.STORAGE

        # Network adapters
        if any(x in name_lower + desc_lower for x in ["network", "ethernet", "wifi", "wireless", "adapter", "nic"]):
            return DeviceType.NETWORKAdapter

        # Bluetooth adapters
        if any(x in name_lower + desc_lower for x in ["bluetooth", "bt adapter"]):
            return DeviceType.BLUETOOTH

        # Printers
        if any(x in name_lower + desc_lower for x in ["printer", "hp", "canon", "epson", "brother"]):
            return DeviceType.PRINTER

        # Input devices
        if any(x in name_lower + desc_lower for x in ["keyboard", "mouse", "pointing", "hid"]):
            return DeviceType.KEYBOARD if "keyboard" in name_lower + desc_lower else DeviceType.MOUSE

        # Game controllers
        if any(x in name_lower + desc_lower for x in ["controller", "gamepad", "joystick", "xbox", "playstation"]):
            return DeviceType.GAME_CONTROLLER

        # Mobile devices (connected via USB)
        if any(x in name_lower + desc_lower for x in ["iphone", "android", "mobile", "phone"]):
            return DeviceType.PHONE

        # Smart/IoT devices
        if any(x in name_lower + desc_lower for x in ["smart", "iot", "esp", "arduino", "particle"]):
            return DeviceType.IOT

        return DeviceType.USB_DONGLE

    def _get_wmi_devices(self) -> List[USBDevice]:
        """Get USB devices using WMI"""
        devices = []

        if not self._available:
            return devices

        try:
            ps_script = """
            $usb = Get-PnpDevice -Class USB -Status OK
            $skip = @('USB Composite Device', 'USB Root Hub', 'USB Controller',
                       'Generic USB Hub', 'Microsoft', 'Generic', 'USB Device')

            foreach ($d in $usb) {
                $name = $d.Name
                $friendly = $d.FriendlyName
                $desc = $d.Description
                $mfg = $d.Manufacturer
                $present = $d.Present
                $status = $d.Status
                $class = $d.Class
                $id = $d.InstanceId

                $isSkip = $false
                foreach ($s in $skip) {
                    if ($name -like "*$s*" -or $desc -like "*$s*") { $isSkip = $true; break }
                }

                if (-not $isSkip -and $present -and $name -and $name.Length -gt 3) {
                    Write-Output "$name|$mfg|$desc|$friendly|$status|$id"
                }
            }
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=30
            )

            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    name = parts[0].strip() if len(parts) > 0 else ""
                    manufacturer = parts[1].strip() if len(parts) > 1 else ""
                    description = parts[2].strip() if len(parts) > 2 else ""
                    friendly = parts[3].strip() if len(parts) > 3 else ""
                    status = parts[4].strip() if len(parts) > 4 else "OK"
                    instance_id = parts[5].strip() if len(parts) > 5 else ""

                    if name and len(name) > 2:
                        # Extract VID/PID from InstanceId
                        vid = ""
                        pid = ""
                        import re
                        vid_match = re.search(r'VID_([0-9A-F]{4})', instance_id, re.I)
                        pid_match = re.search(r'PID_([0-9A-F]{4})', instance_id, re.I)
                        if vid_match:
                            vid = vid_match.group(1)
                        if pid_match:
                            pid = pid_match.group(1)

                        device_type = self._classify_device(
                            friendly or name,
                            description,
                            manufacturer
                        )

                        devices.append(USBDevice(
                            name=friendly or name,
                            device_id=instance_id,
                            device_type=device_type,
                            vendor=manufacturer or "Unknown",
                            description=description,
                            status="online" if status == "OK" else status,
                            vid=vid,
                            pid=pid,
                            connected=True,
                        ))
        except Exception:
            pass

        return devices

    def _get_usb_storage(self) -> List[USBDevice]:
        """Get USB storage devices"""
        devices = []

        if not self._available:
            return devices

        try:
            ps_script = """
            $storage = Get-PnpDevice -Class DiskDrive -Status OK
            foreach ($s in $storage) {
                if ($s.Name -like "*USB*" -or $s.Description -like "*USB*") {
                    $name = $s.FriendlyName
                    $mfg = $s.Manufacturer
                    $id = $s.PNPDeviceID
                    Write-Output "$name|$mfg|USB Storage||$id"
                }
            }
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=15
            )

            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    name = parts[0].strip()
                    vendor = parts[1].strip() if len(parts) > 1 else ""
                    desc = parts[2].strip() if len(parts) > 2 else "USB Storage"
                    device_id = parts[3].strip() if len(parts) > 3 else ""

                    if name:
                        devices.append(USBDevice(
                            name=name,
                            device_id=device_id,
                            device_type=DeviceType.STORAGE,
                            vendor=vendor or "Unknown",
                            description=desc,
                            status="online",
                        ))
        except Exception:
            pass

        return devices

    def scan(self, callback: Callable = None) -> List[USBDevice]:
        """Scan for USB devices"""
        self._scanning = True
        devices = []

        try:
            # Get USB devices from WMI
            usb_devices = self._get_wmi_devices()
            devices.extend(usb_devices)

            # Get USB storage
            storage_devices = self._get_usb_storage()
            devices.extend(storage_devices)

            # Update internal state
            with self._lock:
                for dev in devices:
                    self._devices[dev.device_id] = dev

            if callback:
                callback(devices)

        finally:
            self._scanning = False

        return devices

    def scan_async(self, callback: Callable = None):
        """Scan in background thread"""
        if self._scanning:
            return

        thread = threading.Thread(target=self.scan, args=(callback,), daemon=True)
        thread.start()

    def get_devices(self) -> List[USBDevice]:
        """Get known USB devices"""
        with self._lock:
            return list(self._devices.values())

    def is_scanning(self) -> bool:
        return self._scanning
