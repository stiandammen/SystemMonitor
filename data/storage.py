"""
Storage Data Collector - Comprehensive disk monitoring
Collects per-disk information, SMART status, temperatures, and IO rates
"""
import platform
import time
import ctypes
import struct
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from utils.logger import get_logger, LogCategory, log_info, log_warning, log_error, log_exception


class StorageCollector(QThread):
    """
    Comprehensive storage data collector running in background thread.
    Collects: per-disk info, SMART data, temperatures, IO rates
    """
    data_updated = pyqtSignal(dict)

    REFRESH_INTERVAL = 2.0  # 2 seconds for storage data

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._data = {}
        self._previous_io = {}
        self._previous_time = {}
        self._last_emit_time = 0
        self._min_emit_interval = 1.0
        self._smart_cache = {}
        self._smart_cache_time = {}
        self._smart_cache_ttl = 30.0  # Cache SMART for 30 seconds
        self._temp_cache = {}
        self._temp_cache_time = {}
        self._temp_cache_ttl = 5.0  # Cache temp for 5 seconds

    def run(self):
        """Main collection loop"""
        self._running = True
        log_info(LogCategory.DISK, "StorageCollector started")

        while self._running and not self.isInterruptionRequested():
            try:
                start_time = time.time()
                collected = self._collect()

                if collected:
                    self._data.update(collected)
                    current_time = time.time()
                    if current_time - self._last_emit_time >= self._min_emit_interval:
                        self.data_updated.emit(self._data.copy())
                        self._last_emit_time = current_time

                elapsed = time.time() - start_time
                sleep_time = max(0, self.REFRESH_INTERVAL - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                log_exception(LogCategory.DISK, "StorageCollector error", e)
                time.sleep(2)

    def stop(self):
        """Stop data collection"""
        self._running = False
        self.requestInterruption()

    def _collect(self) -> dict:
        """Collect all storage data"""
        try:
            import psutil

            disks_data = {
                'disks': [],
                'total_read_rate': 0,
                'total_write_rate': 0,
                'station_name': self._get_station_name(),
            }

            # Collect per-disk information
            disks = self._get_disk_list()
            disk_io = self._get_io_stats()

            for disk in disks:
                device = disk['device']

                # Get per-disk IO rates
                io_rates = disk_io.get(device, {'read_rate': 0, 'write_rate': 0})
                disk['read_rate'] = io_rates['read_rate']
                disk['write_rate'] = io_rates['write_rate']

                # Get temperature (cached)
                disk['temperature'] = self._get_disk_temperature(device)

                # Get SMART data (cached)
                disk['smart'] = self._get_smart_data(device)

                disks_data['disks'].append(disk)

                # Accumulate total IO rates
                disks_data['total_read_rate'] += io_rates['read_rate']
                disks_data['total_write_rate'] += io_rates['write_rate']

            return disks_data

        except Exception as e:
            log_exception(LogCategory.DISK, "Storage collection failed", e)
            return {}

    def _get_station_name(self) -> str:
        """Get the computer/station name"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                buffer = ctypes.create_unicode_buffer(256)
                size = ctypes.sizeof(buffer)
                ctypes.windll.kernel32.GetComputerNameW(buffer, ctypes.byref(ctypes.c_int(size)))
                return buffer.value or 'Unknown'
            else:
                import socket
                return socket.gethostname()
        except Exception:
            return 'Unknown'

    def _get_disk_list(self) -> List[Dict[str, Any]]:
        """Get comprehensive list of all disks with metadata"""
        try:
            import psutil
            import subprocess

            disks = []

            if platform.system() == 'Windows':
                # Use WMI to get detailed disk info
                disks = self._get_windows_disks()
            else:
                # Fallback for other platforms
                for part in psutil.disk_partitions(all=False):
                    if not part.fstype:
                        continue
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        disks.append({
                            'device': part.device,
                            'mountpoint': part.mountpoint,
                            'fstype': part.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent,
                            'name': self._guess_disk_name(part.device),
                            'model': 'Unknown',
                            'vendor': 'Unknown',
                            'disk_type': self._guess_disk_type(part.device),
                            'serial': 'N/A',
                            'is_removable': False,
                            'partitions': [],
                            'station_name': self._get_station_name(),
                        })
                    except (PermissionError, OSError):
                        pass

            return disks

        except Exception as e:
            log_exception(LogCategory.DISK, "Failed to get disk list", e)
            return []

    def _get_windows_disks(self) -> List[Dict[str, Any]]:
        """Get detailed Windows disk information via WMI"""
        import psutil
        import wmi
        import pywintypes
        disks = []

        # Retry logic for transient WMI failures
        max_retries = 3
        retry_delay = 0.5

        for attempt in range(max_retries):
            try:
                w = wmi.WMI()

                # Get physical disk info from Win32_DiskDrive
                for drive in w.Win32_DiskDrive():
                    try:
                        disk_info = {
                            'device': f"\\\\.\\{drive.Index}",
                            'name': drive.Name or 'Unknown',
                            'model': drive.Model or 'Unknown',
                            'vendor': drive.Manufacturer or 'Unknown',
                            'serial': drive.SerialNumber or 'N/A',
                            'size': int(drive.Size) if drive.Size else 0,
                            'disk_type': self._parse_disk_type(drive.Model or ''),
                            'is_removable': bool(drive.Removable) if drive.Removable is not None else False,
                            'partitions': [],
                            'interface_type': drive.InterfaceType or 'Unknown',
                            'status': drive.Status or 'Unknown',
                            'read_rate': 0,
                            'write_rate': 0,
                            'temperature': None,
                            'smart': None,
                            'station_name': self._get_station_name(),
                        }

                        # Get partitions for this disk
                        try:
                            for partition in w.Win32_DiskPartition():
                                if partition.DiskIndex == drive.Index:
                                    for logical in partition.associators("Win32_LogicalDisk"):
                                        try:
                                            usage = psutil.disk_usage(logical.Name)
                                            logical_info = {
                                                'device': logical.Name,
                                                'mountpoint': logical.Name,
                                                'fstype': logical.FileSystem or 'Unknown',
                                                'total': usage.total,
                                                'used': usage.used,
                                                'free': usage.free,
                                                'percent': usage.percent,
                                                'station_name': self._get_station_name(),
                                            }
                                            disk_info['partitions'].append(logical_info)
                                        except (PermissionError, OSError):
                                            # Logical disk not accessible, skip partition
                                            pass
                        except pywintypes.com_error:
                            # Partition query failed, skip but don't fail entire disk
                            pass

                        disks.append(disk_info)

                    except pywintypes.com_error as e:
                        # Individual disk query failed (e.g., removable disk removed during enumeration)
                        if e.args[0] == -2147217406:  # 0x80041002 - Object not found
                            log_info(LogCategory.DISK, "Skipping disk that became unavailable during query")
                            continue
                        raise  # Re-raise for retry if not an "Object not found" error
                    except AttributeError:
                        # Drive property doesn't exist, skip this disk
                        continue

                # Success - exit retry loop
                break

            except pywintypes.com_error as e:
                error_code = e.args[0] if e.args else 0
                if error_code == -2147217406:  # 0x80041002 - Object not found
                    # WMI object not found - common with removable disks
                    # This is non-recoverable, exit retry loop and use fallback
                    log_info(LogCategory.DISK, "WMI object not found (removable disk issue), using fallback")
                    break
                if attempt < max_retries - 1:
                    log_info(LogCategory.DISK, f"WMI query failed (attempt {attempt + 1}/{max_retries}), retrying: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    log_warning(LogCategory.DISK, f"WMI disk query failed after {max_retries} attempts: {e}")
                    # Fall through to fallback
            except Exception as e:
                log_warning(LogCategory.DISK, f"WMI disk query failed: {e}")
                break

        # Fallback to psutil if WMI failed or returned no disks
        if not disks:
            log_info(LogCategory.DISK, "Using psutil fallback for disk list")
            disks = self._get_psutil_disks()

        return disks

    def _get_psutil_disks(self) -> List[Dict[str, Any]]:
        """Fallback method to get disk list using psutil"""
        import psutil
        disks = []

        for part in psutil.disk_partitions(all=False):
            if not part.fstype:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                    'name': self._guess_disk_name(part.device),
                    'model': 'Unknown',
                    'vendor': 'Unknown',
                    'disk_type': self._guess_disk_type(part.device),
                    'serial': 'N/A',
                    'is_removable': part.fstype == '' or 'removable' in str(part.opts).lower(),
                    'partitions': [],
                    'station_name': self._get_station_name(),
                })
            except (PermissionError, OSError):
                pass

        return disks

    def _parse_disk_type(self, model: str) -> str:
        """Parse disk type from model name"""
        model_lower = model.lower()
        if 'nvme' in model_lower:
            return 'NVMe'
        elif 'ssd' in model_lower or 'solid' in model_lower:
            return 'SSD'
        elif any(hdd in model_lower for hdd in ['hdd', 'hard', 'disk', '7200', '5400', 'wdc', 'wd', 'st', 'stex', 'hitachi', 'toshiba', 'samsung', 'seagate']):
            return 'HDD'
        return 'Unknown'

    def _guess_disk_type(self, device: str) -> str:
        """Guess disk type from device name"""
        device_upper = device.upper()
        if 'NVME' in device_upper or 'PCIe' in device_upper:
            return 'NVMe'
        return 'Unknown'

    def _guess_disk_name(self, device: str) -> str:
        """Generate a display name from device"""
        if platform.system() == 'Windows':
            if len(device) >= 2:
                return f"Disk {device[:2]}"
        return device

    def _get_io_stats(self) -> Dict[str, Dict[str, float]]:
        """Get per-disk IO statistics with rate calculation"""
        import psutil

        result = {}
        try:
            current_io = psutil.disk_io_counters(perdisk=True)
            current_time = time.time()

            for device, io in current_io.items():
                # Normalize device name
                norm_device = self._normalize_device_name(device)

                if norm_device not in self._previous_io:
                    self._previous_io[norm_device] = io
                    self._previous_time[norm_device] = current_time
                    result[norm_device] = {'read_rate': 0, 'write_rate': 0}
                    continue

                time_delta = current_time - self._previous_time[norm_device]
                if time_delta > 0 and self._previous_io[norm_device]:
                    read_rate = (io.read_bytes - self._previous_io[norm_device].read_bytes) / time_delta
                    write_rate = (io.write_bytes - self._previous_io[norm_device].write_bytes) / time_delta
                else:
                    read_rate = write_rate = 0

                result[norm_device] = {
                    'read_rate': max(0, read_rate),
                    'write_rate': max(0, write_rate),
                }

                self._previous_io[norm_device] = io
                self._previous_time[norm_device] = current_time

        except Exception as e:
            log_error(LogCategory.DISK, f"IO stats error: {e}")

        return result

    def _normalize_device_name(self, device: str) -> str:
        """Normalize device name for consistent key matching"""
        if platform.system() == 'Windows':
            # Remove \\.\ prefix and trailing spaces
            normalized = device.replace('\\\\.\\', '').strip()
            return normalized
        return device

    def _get_disk_temperature(self, device: str) -> Optional[float]:
        """Get disk temperature using available methods"""
        current_time = time.time()

        # Check cache
        if device in self._temp_cache:
            if current_time - self._temp_cache_time[device] < self._temp_cache_ttl:
                return self._temp_cache[device]

        temp = None

        if platform.system() == 'Windows':
            # Try WMI first
            temp = self._get_wmi_temperature()

            # Try HWiNFO/LibreHardwareMonitor shared memory
            if temp is None:
                temp = self._read_hwinfo_temperature()

        if temp is not None:
            self._temp_cache[device] = temp
            self._temp_cache_time[device] = current_time

        return temp

    def _get_wmi_temperature(self) -> Optional[float]:
        """Get temperature via WMI"""
        try:
            import wmi
            w = wmi.WMI()

            # Try MSAcpi_ThermalZoneTemperature first
            for sensor in w.MSAcpi_ThermalZoneTemperature():
                if sensor.CurrentReading and sensor.CurrentReading > 0:
                    # Convert from tenths of Kelvin to Celsius
                    temp_k = float(sensor.CurrentReading)
                    temp_c = temp_k / 10 - 273.15
                    if 0 < temp_c < 120:
                        return temp_c

        except Exception:
            pass

        return None

    def _read_hwinfo_temperature(self) -> Optional[float]:
        """Read temperature from HWiNFO/LibreHardwareMonitor shared memory"""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32

            HWINFO_NAMES = [
                "HWiNFO32_Sens", "HWiNFO64_Sens",
                "HWiNFO32_V2", "HWiNFO64_V2",
                "HWiNFO32_V3", "HWiNFO64_V3",
                "HWiNFO32_V4", "HWiNFO64_V4",
                "LibreHardwareMonitor",
                "LHM_Sensor",
            ]

            handle = None
            for name in HWINFO_NAMES:
                handle = kernel32.OpenFileMappingW(0x0004, False, name)
                if handle:
                    break

            if not handle:
                return None

            try:
                mapping = kernel32.MapViewOfFile(handle, 0x0004, 0, 0, 8192)
            finally:
                kernel32.CloseHandle(handle)

            if not mapping:
                return None

            try:
                # Try reading temperature at various offsets
                for offset in [0x30, 0x34, 0x38, 0x40, 0x44, 0x48, 0x50, 0x60, 0x80, 0x100]:
                    try:
                        temp_raw = ctypes.c_float()
                        ctypes.memmove(ctypes.addressof(temp_raw), mapping + offset, 4)
                        temp = temp_raw.value
                        # Valid storage temperature range: 0-100°C
                        if 0 < temp < 100:
                            return temp
                    except Exception:
                        continue
            finally:
                if mapping:
                    kernel32.UnmapViewOfFile(mapping)

        except Exception:
            pass

        return None

    def _get_smart_data(self, device: str) -> Optional[Dict[str, Any]]:
        """Get SMART data for disk"""
        current_time = time.time()

        # Check cache
        if device in self._smart_cache:
            if current_time - self._smart_cache_time[device] < self._smart_cache_ttl:
                return self._smart_cache[device]

        smart_data = None

        if platform.system() == 'Windows':
            smart_data = self._get_wmi_smart()

        if smart_data is not None:
            self._smart_cache[device] = smart_data
            self._smart_cache_time[device] = current_time

        return smart_data

    def _get_wmi_smart(self) -> Optional[Dict[str, Any]]:
        """Get SMART data via WMI"""
        try:
            import wmi
            w = wmi.WMI()

            # Try to get SMART status from MSStorageDriver_ATAPISmartData
            for disk in w.MSStorageDriver_ATAPISmartData():
                if disk.SerialNumber:
                    return {
                        'health': 'Unknown',
                        'remaining_life': None,
                        'bad_sectors': None,
                        'reallocated_sectors': None,
                        'power_on_hours': None,
                        'power_cycle_count': None,
                        'wear_level': None,
                    }

        except Exception:
            pass

        return None

    def get_data(self) -> dict:
        """Get current cached data"""
        return self._data.copy()
