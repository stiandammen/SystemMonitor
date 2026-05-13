"""
Bluetooth Discovery Module
BLE and classic Bluetooth device scanning using Bleak
"""
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable

from .classification import DeviceClassifier, DeviceType


@dataclass
class BluetoothDevice:
    """Discovered Bluetooth device"""
    name: str
    mac: str
    device_type: DeviceType = DeviceType.BLUETOOTH
    rssi: int = 0
    vendor: str = ""
    paired: bool = False
    connected: bool = False
    last_seen: datetime = field(default_factory=datetime.now)
    services: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        cfg = DeviceClassifier.get_type_config(self.device_type)
        return {
            "id": f"bt_{self.mac.replace(':', '')}",
            "name": self.name or "Unknown Bluetooth Device",
            "ip": "N/A",
            "mac": self.mac.upper(),
            "vendor": self.vendor or "Unknown",
            "type": self.device_type.value,
            "type_label": cfg.label,
            "type_color": cfg.color,
            "type_glyph": cfg.glyph,
            "status": "online" if self.connected else ("paired" if self.paired else "discovered"),
            "ping": 0,
            "rssi": self.rssi,
            "ports": [],
            "services": self.services,
            "os": "N/A",
            "connection_type": "bluetooth",
            "last_seen": self.last_seen.strftime("%H:%M:%S"),
            "is_adapter": False,
        }


class BluetoothDiscovery:
    """Bluetooth device discovery using Bleak and PowerShell"""

    def __init__(self):
        self._devices: Dict[str, BluetoothDevice] = {}
        self._lock = threading.Lock()
        self._scanning = False
        self._available = platform.system() == "Windows"

    def is_available(self) -> bool:
        """Check if Bluetooth is available"""
        if not self._available:
            return False
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "Get-PnpDevice -Class Bluetooth -Status OK"],
                capture_output=True, timeout=10
            )
            return result.returncode == 0 or "Bluetooth" in result.stdout
        except Exception:
            return False

    def _get_paired_devices(self) -> List[BluetoothDevice]:
        """Get paired Bluetooth devices using PowerShell"""
        devices = []

        if not self._available:
            return devices

        try:
            ps_script = """
            $bt = Get-PnpDevice -Class Bluetooth -Status OK
            $skip = @('Generic', 'Microsoft', 'Enum', 'Protoc', 'Bluetooth Device',
                      'attributt', 'tjeneste', 'Enumerate', 'Intel(R) Wireless',
                      'Generic ATT', 'Generic Access', 'Generic Attribute',
                      'Enhetsinformasjon', 'Generisk', 'tilgangsprofil', 'Dienst')
            foreach ($d in $bt) {
                $name = $d.Name
                $manufacturer = $d.Manufacturer
                $present = $d.Present
                $enabled = $d.Status

                $isSkip = $false
                foreach ($s in $skip) {
                    if ($name -like "*$s*") { $isSkip = $true; break }
                }

                if (-not $isSkip -and $name -and $name.Length -gt 3 -and $present) {
                    Write-Output "$name|$manufacturer|$enabled"
                }
            }
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True, text=True, timeout=20
            )

            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    name = parts[0].strip()
                    manufacturer = parts[1].strip() if len(parts) > 1 else "Unknown"
                    status = parts[2].strip() if len(parts) > 2 else "Unknown"

                    if name and len(name) > 2:
                        # Classify device type
                        dev_type = self._classify_device(name, manufacturer)

                        devices.append(BluetoothDevice(
                            name=name,
                            mac="00:00:00:00:00:00",  # PS doesn't provide MAC
                            device_type=dev_type,
                            vendor=manufacturer,
                            paired=True,
                            connected=(status == "OK"),
                        ))
        except Exception:
            pass

        return devices

    def _classify_device(self, name: str, manufacturer: str) -> DeviceType:
        """Classify Bluetooth device by name and manufacturer"""
        name_lower = name.lower()
        mfg_lower = manufacturer.lower()

        # Headsets/Headphones
        if any(x in name_lower for x in ["headset", "headphone", "airpods", "earbuds", "buds", "pod"]):
            return DeviceType.HEADSET
        if any(x in mfg_lower for x in ["jabra", "sennheiser", "bose", "beats", "audio-technica", "shure", "blue"]):
            return DeviceType.HEADSET

        # Keyboards
        if "keyboard" in name_lower or any(x in mfg_lower for x in ["logitech", "keychron", "apple"]):
            if "keyboard" in name_lower:
                return DeviceType.KEYBOARD

        # Mice
        if "mouse" in name_lower or any(x in name_lower for x in ["mx master", "mx anywhere", "sculpt"]):
            return DeviceType.MOUSE

        # Speakers
        if any(x in name_lower for x in ["speaker", "soundbar", "home pod", "echo", "homepod", "sonos", "bose", "jbl"]):
            return DeviceType.SPEAKER

        # Phones
        if any(x in name_lower for x in ["iphone", "galaxy", "pixel", "oneplus", "xiaomi", "redmi", "note"]):
            return DeviceType.PHONE

        # Smart watches/Fitness trackers
        if any(x in name_lower for x in ["watch", "fitbit", "garmin", "wear", "band", "galaxy watch", "apple watch"]):
            return DeviceType.SMART

        # Game controllers
        if any(x in name_lower for x in ["controller", "gamepad", "xbox", "playstation", "dualshock", "joy-con"]):
            return DeviceType.GAME_CONTROLLER

        # Smart home devices
        if any(x in name_lower for x in ["hue", "smart bulb", "strip", "smart plug", "outlet"]):
            return DeviceType.SMART

        return DeviceType.BLUETOOTH

    def scan(self, callback: Callable = None) -> List[BluetoothDevice]:
        """Scan for Bluetooth devices"""
        self._scanning = True
        devices = []

        try:
            # Get paired devices
            paired = self._get_paired_devices()
            devices.extend(paired)

            # Try Bleak scan if available
            try:
                import asyncio
                from bleak import BleakScanner

                async def bleak_scan():
                    try:
                        devices_found = await BleakScanner.discover(timeout=5.0)
                        return devices_found
                    except Exception:
                        return []

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    bleak_devices = loop.run_until_complete(bleak_scan())

                    for d in bleak_devices:
                        mac = d.address.upper()
                        name = d.name or "Unknown"
                        rssi = d.rssi or -100

                        # Check if already in list
                        if not any(dev.mac == mac for dev in devices):
                            devices.append(BluetoothDevice(
                                name=name,
                                mac=mac,
                                device_type=self._classify_device(name, ""),
                                rssi=rssi,
                            ))
                except Exception:
                    pass
            except ImportError:
                pass  # Bleak not available

            # Update internal state
            with self._lock:
                for dev in devices:
                    self._devices[dev.mac] = dev

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

    def get_devices(self) -> List[BluetoothDevice]:
        """Get known Bluetooth devices"""
        with self._lock:
            return list(self._devices.values())

    def is_scanning(self) -> bool:
        return self._scanning
