"""
Audio Discovery Module
Audio device detection for internal, USB, and network audio devices
"""
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable

from .classification import DeviceClassifier, DeviceType


@dataclass
class AudioDevice:
    """Discovered audio device"""
    name: str
    device_type: DeviceType = DeviceType.AUDIO_INTERFACE
    device_id: str = ""
    manufacturer: str = ""
    driver: str = ""
    status: str = "online"
    is_input: bool = False
    is_output: bool = False
    channels: int = 0
    sample_rate: str = ""
    interface_type: str = "internal"
    last_seen: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        cfg = DeviceClassifier.get_type_config(self.device_type)
        return {
            "id": f"audio_{self.device_id.replace(' ', '_')[:30]}",
            "name": self.name or "Audio Device",
            "ip": "N/A",
            "mac": "N/A",
            "vendor": self.manufacturer or "Unknown",
            "type": self.device_type.value,
            "type_label": cfg.label,
            "type_color": cfg.color,
            "type_glyph": cfg.glyph,
            "status": self.status,
            "ping": 0,
            "ports": [],
            "services": [f"{self.channels}ch", self.sample_rate] if self.channels else [],
            "os": f"{self.interface_type.upper()}",
            "connection_type": self.interface_type,
            "last_seen": self.last_seen.strftime("%H:%M:%S"),
            "is_adapter": False,
            "driver": self.driver,
            "is_input": self.is_input,
            "is_output": self.is_output,
        }


class AudioDiscovery:
    """Audio device discovery"""

    def __init__(self):
        self._devices: Dict[str, AudioDevice] = {}
        self._lock = threading.Lock()
        self._scanning = False

    def is_available(self) -> bool:
        """Check if audio discovery is available"""
        return True

    def _classify_device(self, name: str, manufacturer: str, interface: str) -> DeviceType:
        """Classify audio device"""
        name_lower = name.lower()
        mfg_lower = manufacturer.lower()

        # Audio interfaces
        if any(x in mfg_lower for x in ["focusrite", "scarlett", "behringer", "presonus", "universal audio", "motu", "rme", "steinberg", "native instruments", "apogee", "audient", "ssl", "neve", "api", "universal audio"]):
            return DeviceType.AUDIO_INTERFACE

        # Headsets
        if any(x in name_lower for x in ["headset", "headphone", "airpods", "earbuds", "buds"]):
            return DeviceType.HEADSET

        # Speakers/Monitors
        if any(x in name_lower for x in ["speaker", "monitor", "soundbar", "subwoofer"]):
            return DeviceType.SPEAKER

        # Microphones
        if any(x in name_lower for x in ["microphone", "mic", "blue yeti", "snowball", "rode", "shure", "audio-technica"]):
            return DeviceType.HEADSET

        # Internal/high-quality audio
        if interface == "internal" or "high definition" in name_lower:
            return DeviceType.AUDIO_INTERFACE

        return DeviceType.AUDIO_INTERFACE

    def _get_windows_audio(self) -> List[AudioDevice]:
        """Get Windows audio devices using PowerShell"""
        devices = []

        try:
            # Get audio endpoints
            ps_script = """
            Add-Type -TypeDefinition @'
            using System;
            using System.Runtime.InteropServices;

            [Guid("7991EEC9-7E89-4D85-8390-33C58B1E5804"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDeviceEnumerator {
                int NotImpl1();
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IntPtr ppEndpoint);
            }
            [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), ClassType(ClassType.CLSCTX_INPROC_SERVER)]
            class MMDeviceEnumeratorComObject {}
'@

            try {
                $enumerator = [Activator]::CreateInstance([Type]::GetTypeFromCLSID([Guid]'BCDE0395-E52F-467C-8E3D-C4579291692E'))
                $null = $enumerator.GetDefaultAudioEndpoint(0, 1, [ref]$sink)
                $sink.EnumerateProperties()
            } catch {
                # Fallback to CIM
            }

            # Use CIM for audio endpoints
            $endpoints = Get-CimInstance -ClassName Win32_SoundDevice
            foreach ($dev in $endpoints) {
                $status = if ($dev.Status -eq 'OK') { 'online' } else { 'offline' }
                Write-Output "$($dev.Name)|$($dev.Manufacturer)|$($dev.DeviceID)|$($dev.Status)|internal"
            }

            # Also get USB audio
            $usb_audio = Get-PnpDevice -Class AudioEndpoint -Status OK
            foreach ($dev in $usb_audio) {
                $name = $dev.Name
                if ($name -and $name.Length -gt 2) {
                    Write-Output "$name||$($dev.InstanceId)|$($dev.Status)|usb"
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
                    name = parts[0].strip() if len(parts) > 0 else ""
                    manufacturer = parts[1].strip() if len(parts) > 1 else ""
                    device_id = parts[2].strip() if len(parts) > 2 else ""
                    status = parts[3].strip().lower() if len(parts) > 3 else "ok"
                    interface = parts[4].strip() if len(parts) > 4 else "internal"

                    if name and len(name) > 2:
                        device_type = self._classify_device(name, manufacturer, interface)

                        devices.append(AudioDevice(
                            name=name,
                            device_type=device_type,
                            device_id=device_id or name,
                            manufacturer=manufacturer,
                            status="online" if status == "ok" else status,
                            interface_type=interface,
                        ))
        except Exception:
            pass

        # Fallback: use psutil and simple detection
        if not devices:
            try:
                import psutil
                # Get audio from general device info
                ps_script = """
                $audio = Get-CimInstance -ClassName Win32_SoundDevice | Select-Object Name, Manufacturer, Status, DeviceID
                foreach ($a in $audio) {
                    Write-Output "$($a.Name)|$($a.Manufacturer)|$($a.DeviceID)|$($a.Status)"
                }
                """
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    capture_output=True, text=True, timeout=10
                )

                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|")
                        name = parts[0].strip()
                        manufacturer = parts[1].strip() if len(parts) > 1 else ""

                        if name:
                            devices.append(AudioDevice(
                                name=name,
                                device_type=self._classify_device(name, manufacturer, "internal"),
                                device_id=name,
                                manufacturer=manufacturer,
                                status="online",
                                interface_type="internal",
                            ))
            except Exception:
                pass

        return devices

    def _get_linux_audio(self) -> List[AudioDevice]:
        """Get Linux audio devices"""
        devices = []

        try:
            # Try to read from /proc/asound
            import os
            if os.path.exists("/proc/asound/cards"):
                with open("/proc/asound/cards") as f:
                    content = f.read()
                    # Parse card entries
                    import re
                    for match in re.finditer(r'(\d+) \[(\w+)\s*\]:.*?-\s*(.*?)$', content, re.M):
                        card_id = match.group(1)
                        card_name = match.group(2)
                        description = match.group(3).strip()

                        if description:
                            devices.append(AudioDevice(
                                name=description,
                                device_type=DeviceType.AUDIO_INTERFACE,
                                device_id=f"hw:{card_id}",
                                manufacturer=card_name,
                                status="online",
                                interface_type="internal",
                            ))
        except Exception:
            pass

        return devices

    def _get_network_audio(self) -> List[AudioDevice]:
        """Get network audio devices (RTSP, Chromecast, Sonos, etc.)"""
        devices = []

        # These would be discovered by network scanner, but we can
        # detect common network audio protocols here
        try:
            # Check for common network audio service ports
            import socket
            common_ports = {
                7000: ("Sonos", DeviceType.SPEAKER),
                1400: ("Denon HEOS", DeviceType.SPEAKER),
                3689: ("DAAP/iTunes", DeviceType.SPEAKER),
                8008: ("Google Cast", DeviceType.SPEAKER),
            }

            # Note: In practice, these are found via network scan
            # This is just for protocol detection
        except Exception:
            pass

        return devices

    def scan(self, callback: Callable = None) -> List[AudioDevice]:
        """Scan for audio devices"""
        self._scanning = True
        devices = []

        try:
            system = platform.system()

            if system == "Windows":
                devices.extend(self._get_windows_audio())
            elif system == "Linux":
                devices.extend(self._get_linux_audio())

            # Network audio devices are typically discovered via network scan
            # but we can include them here if needed
            # devices.extend(self._get_network_audio())

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

    def get_devices(self) -> List[AudioDevice]:
        """Get known audio devices"""
        with self._lock:
            return list(self._devices.values())

    def is_scanning(self) -> bool:
        return self._scanning
