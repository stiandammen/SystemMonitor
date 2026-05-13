"""
Device Data Collector
Unified device discovery and monitoring - coordinates all discovery modules
"""
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

from PyQt6.QtCore import QObject, pyqtSignal

from core.discovery.classification import DeviceClassifier, DeviceType
from core.discovery.network import NetworkDiscovery, DiscoveredDevice
from core.discovery.bluetooth import BluetoothDiscovery, BluetoothDevice
from core.discovery.usb import USBDiscovery, USBDevice
from core.discovery.audio import AudioDiscovery, AudioDevice


class DeviceCollector(QObject):
    """
    Unified device collector - coordinates all discovery modules.
    Emits signals with discovered devices for GUI consumption.
    """

    # Signal emitted when devices are updated: (all_devices_list)
    devices_updated = pyqtSignal(list)

    # Signal emitted during scan progress: (current_phase, percentage)
    scan_progress = pyqtSignal(str, int)

    # Signal emitted when a single device is updated
    device_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lock = threading.Lock()

        # Initialize discovery modules
        self._network = NetworkDiscovery()
        self._bluetooth = BluetoothDiscovery()
        self._usb = USBDiscovery()
        self._audio = AudioDiscovery()

        # Device state
        self._devices: Dict[str, dict] = {}
        self._scanning = False
        self._running = False
        self._scan_thread: Optional[threading.Thread] = None
        self._refresh_timer: Optional[threading.Timer] = None

        # Refresh interval in seconds
        self._refresh_interval = 15  # 15 seconds default

    def start(self):
        """Start device monitoring"""
        self._running = True
        self._do_initial_scan()

    def stop(self):
        """Stop device monitoring"""
        self._running = False
        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=2)
        if self._refresh_timer:
            self._refresh_timer.cancel()

    def _do_initial_scan(self):
        """Perform initial comprehensive scan"""
        if self._scanning:
            return

        self._scan_thread = threading.Thread(target=self._full_scan, daemon=True)
        self._scan_thread.start()

    def _full_scan(self):
        """Perform full device scan across all sources"""
        self._scanning = True
        all_devices = []

        try:
            # Phase 1: Network adapters (instant)
            self.scan_progress.emit("Network Adapters", 10)
            adapters = self._network.get_local_interfaces()
            for dev in adapters:
                dev["source"] = "adapter"
                all_devices.append(dev)
            self._emit_update(all_devices)

            # Phase 2: Network scan
            self.scan_progress.emit("Scanning Network", 30)
            def network_callback(devices):
                with self._lock:
                    for d in devices:
                        dev_dict = d.to_dict()
                        dev_dict["source"] = "network"
                        all_devices.append(dev_dict)
                        self._update_device(dev_dict)
                    self._emit_update(all_devices.copy())

            self._network.scan(callback=network_callback)

            # Phase 3: Bluetooth
            self.scan_progress.emit("Scanning Bluetooth", 60)
            def bluetooth_callback(devices):
                with self._lock:
                    for d in devices:
                        dev_dict = d.to_dict()
                        dev_dict["source"] = "bluetooth"
                        all_devices.append(dev_dict)
                        self._update_device(dev_dict)
                    self._emit_update(all_devices.copy())

            self._bluetooth.scan(callback=bluetooth_callback)

            # Phase 4: USB
            self.scan_progress.emit("Scanning USB", 75)
            def usb_callback(devices):
                with self._lock:
                    for d in devices:
                        dev_dict = d.to_dict()
                        dev_dict["source"] = "usb"
                        all_devices.append(dev_dict)
                        self._update_device(dev_dict)
                    self._emit_update(all_devices.copy())

            self._usb.scan(callback=usb_callback)

            # Phase 5: Audio
            self.scan_progress.emit("Scanning Audio", 90)
            def audio_callback(devices):
                with self._lock:
                    for d in devices:
                        dev_dict = d.to_dict()
                        dev_dict["source"] = "audio"
                        all_devices.append(dev_dict)
                        self._update_device(dev_dict)
                    self._emit_update(all_devices.copy())

            self._audio.scan(callback=audio_callback)

            # Final update
            self.scan_progress.emit("Complete", 100)
            self._emit_update(all_devices)

        except Exception as e:
            print(f"Device scan error: {e}")
        finally:
            self._scanning = False

            # Schedule refresh
            if self._running:
                self._refresh_timer = threading.Timer(self._refresh_interval, self._do_refresh_scan)
                self._refresh_timer.daemon = True
                self._refresh_timer.start()

    def _do_refresh_scan(self):
        """Quick refresh scan - incremental updates only"""
        if not self._running:
            return

        threading.Thread(target=self._refresh_scan, daemon=True).start()

    def _refresh_scan(self):
        """Incremental refresh - ping existing devices and check for new ones"""
        try:
            # Quick ping check on known devices
            with self._lock:
                device_ips = [dev["ip"] for dev in self._devices.values()
                            if dev.get("ip") and dev["ip"] != "N/A" and dev["ip"] != "0.0.0.0"]

            # Ping known devices
            for ip in device_ips:
                latency = self._network.ping_device(ip)
                if ip in self._devices:
                    self._devices[ip]["ping"] = int(latency)
                    self._devices[ip]["status"] = "online" if latency < 1000 else "offline"
                    self._devices[ip]["last_seen"] = datetime.now().strftime("%H:%M:%S")
                    self.device_updated.emit(self._devices[ip])

            # Emit current state
            self._emit_update(list(self._devices.values()))

        except Exception as e:
            print(f"Refresh scan error: {e}")
        finally:
            # Schedule next refresh
            if self._running:
                self._refresh_timer = threading.Timer(self._refresh_interval, self._do_refresh_scan)
                self._refresh_timer.daemon = True
                self._refresh_timer.start()

    def _update_device(self, device: dict):
        """Update internal device state"""
        device_id = device.get("id", device.get("mac", device.get("ip", "")))
        with self._lock:
            self._devices[device_id] = device

    def _emit_update(self, devices: List[dict]):
        """Emit devices updated signal"""
        self.devices_updated.emit(devices.copy())

    def get_devices(self) -> List[dict]:
        """Get all currently known devices"""
        with self._lock:
            return list(self._devices.values())

    def get_device_by_id(self, device_id: str) -> Optional[dict]:
        """Get specific device by ID"""
        with self._lock:
            return self._devices.get(device_id)

    def is_scanning(self) -> bool:
        """Check if scan is in progress"""
        return self._scanning

    def set_refresh_interval(self, seconds: int):
        """Set refresh interval in seconds"""
        self._refresh_interval = max(5, min(60, seconds))

    def force_refresh(self):
        """Force a full refresh scan"""
        if not self._scanning:
            self._do_initial_scan()


class DeviceMonitorWorker(QObject):
    """
    Worker for device monitoring in main GUI thread context.
    Provides signals for real-time device updates.
    """

    # Emitted when devices list is fully updated
    devices_changed = pyqtSignal(list)

    # Emitted when a single device changes
    device_changed = pyqtSignal(dict)

    # Emitted when scan status changes
    scan_status_changed = pyqtSignal(bool)

    def __init__(self, collector: DeviceCollector, parent=None):
        super().__init__(parent)
        self._collector = collector
        self._connected = False

    def start(self):
        """Start monitoring collector signals"""
        if self._connected:
            return

        self._collector.devices_updated.connect(self._on_devices_updated)
        self._collector.device_updated.connect(self._on_device_updated)
        self._collector.scan_progress.connect(self._on_scan_progress)
        self._connected = True
        self.scan_status_changed.emit(self._collector.is_scanning())

    def stop(self):
        """Stop monitoring collector signals"""
        if not self._connected:
            return

        try:
            self._collector.devices_updated.disconnect(self._on_devices_updated)
            self._collector.device_updated.disconnect(self._on_device_updated)
            self._collector.scan_progress.disconnect(self._on_scan_progress)
        except Exception:
            pass

        self._connected = False

    def _on_devices_updated(self, devices: List[dict]):
        self.devices_changed.emit(devices)

    def _on_device_updated(self, device: dict):
        self.device_changed.emit(device)

    def _on_scan_progress(self, phase: str, percent: int):
        # Could emit progress, but not currently connected to GUI
        pass

    def refresh(self):
        """Request a refresh"""
        self._collector.force_refresh()
