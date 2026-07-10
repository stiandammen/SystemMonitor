"""
Storage Data Collector - Comprehensive disk monitoring
Collects per-disk information, SMART status, temperatures, and IO rates
"""
import platform
import time
import ctypes
import struct
import random
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from systemmonitor.utils.logger import get_logger, LogCategory, log_info, log_warning, log_error, log_exception


class StorageCollector(QThread):
    """
    Comprehensive storage data collector running in background thread.
    Optimized for low CPU impact and smooth UI updates.
    """
    data_updated = pyqtSignal(dict)

    REFRESH_INTERVAL = 1.0  
    EMA_ALPHA = 0.3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._data = {}
        self._previous_io = {}
        self._previous_time = {}
        self._smoothed_io = {}
        # Global system IO tracking
        self._prev_sys_io = None
        self._prev_sys_time = 0
        self._smoothed_sys_read = 0.0
        self._smoothed_sys_write = 0.0
        
        self._last_emit_time = 0
        self._min_emit_interval = 0.5
        self._smart_cache = {}
        self._smart_cache_time = {}
        self._smart_cache_ttl = 30.0

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

    def _collect(self) -> dict:
        """Collect all storage data"""
        try:
            import psutil

            disks_data = {
                'disks': [],
                'total_read_rate': 0.0,
                'total_write_rate': 0.0,
                'total_read_iops': 0.0,
                'total_write_iops': 0.0,
                'total_read_latency_ms': 0.0,
                'total_write_latency_ms': 0.0,
                'total_busy_pct': 0.0,
                'station_name': self._get_station_name(),
            }
            
            current_time = time.time()
            
            # --- GLOBAL SYSTEM IO (Robust method for top KPI cards) ---
            sys_io = psutil.disk_io_counters(perdisk=False)
            if self._prev_sys_io is None:
                self._prev_sys_io = sys_io
                self._prev_sys_time = current_time
            else:
                dt = current_time - self._prev_sys_time
                if dt > 0:
                    raw_sys_read = (sys_io.read_bytes - self._prev_sys_io.read_bytes) / dt
                    raw_sys_write = (sys_io.write_bytes - self._prev_sys_io.write_bytes) / dt
                    
                    # Responsive smoothing for global cards
                    alpha = 0.5 
                    self._smoothed_sys_read = (alpha * raw_sys_read) + ((1 - alpha) * self._smoothed_sys_read)
                    self._smoothed_sys_write = (alpha * raw_sys_write) + ((1 - alpha) * self._smoothed_sys_write)
                    
                    disks_data['total_read_rate'] = max(0, self._smoothed_sys_read)
                    disks_data['total_write_rate'] = max(0, self._smoothed_sys_write)
                
                self._prev_sys_io = sys_io
                self._prev_sys_time = current_time

            # Collect per-disk information
            disks = self._get_disk_list()
            disk_io = self._get_io_stats()

            for disk in disks:
                device = disk['device']
                norm_device = self._normalize_device_name(device)
                
                io_rates = disk_io.get(norm_device, {
                    'read_rate': 0, 'write_rate': 0,
                    'read_iops': 0, 'write_iops': 0,
                    'read_latency_ms': 0, 'write_latency_ms': 0,
                    'busy_pct': 0,
                })
                
                if norm_device not in self._smoothed_io:
                    self._smoothed_io[norm_device] = {'read': io_rates['read_rate'], 'write': io_rates['write_rate']}
                else:
                    self._smoothed_io[norm_device]['read'] = (self.EMA_ALPHA * io_rates['read_rate']) + \
                                                       ((1 - self.EMA_ALPHA) * self._smoothed_io[norm_device]['read'])
                    self._smoothed_io[norm_device]['write'] = (self.EMA_ALPHA * io_rates['write_rate']) + \
                                                        ((1 - self.EMA_ALPHA) * self._smoothed_io[norm_device]['write'])

                disk['read_rate']        = max(0, self._smoothed_io[norm_device]['read'])
                disk['write_rate']       = max(0, self._smoothed_io[norm_device]['write'])
                disk['read_iops']        = io_rates.get('read_iops', 0)
                disk['write_iops']       = io_rates.get('write_iops', 0)
                disk['read_latency_ms']  = io_rates.get('read_latency_ms', 0)
                disk['write_latency_ms'] = io_rates.get('write_latency_ms', 0)
                disk['busy_pct']         = io_rates.get('busy_pct', 0)

                disks_data['disks'].append(disk)

            # Aggregate performance metrics
            iops_r = iops_w = 0.0
            lat_r_sum = lat_w_sum = 0.0
            max_busy = 0.0
            for rates in disk_io.values():
                ir = rates.get('read_iops', 0)
                iw = rates.get('write_iops', 0)
                iops_r += ir
                iops_w += iw
                lat_r_sum += rates.get('read_latency_ms', 0) * ir
                lat_w_sum += rates.get('write_latency_ms', 0) * iw
                max_busy = max(max_busy, rates.get('busy_pct', 0))

            disks_data['total_read_iops']       = iops_r
            disks_data['total_write_iops']      = iops_w
            disks_data['total_read_latency_ms'] = lat_r_sum / iops_r if iops_r > 0 else 0.0
            disks_data['total_write_latency_ms'] = lat_w_sum / iops_w if iops_w > 0 else 0.0
            disks_data['total_busy_pct']        = max_busy

            return disks_data

        except Exception as e:
            log_exception(LogCategory.DISK, "Storage collection failed", e)
            return {}

    def _get_top_io_processes(self) -> List[Dict[str, Any]]:
        """Identify processes with highest disk I/O activity - Optimized version"""
        import psutil
        processes = []
        now = time.time()
        
        try:
            # Use as_dict for bulk property fetching (more efficient)
            for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
                try:
                    pinfo = proc.info
                    io = pinfo['io_counters']
                    if not io: continue
                    
                    pid = pinfo['pid']
                    if pid in self._process_io_history:
                        prev = self._process_io_history[pid]
                        dt = now - prev['time']
                        if dt > 0.5:
                            read_rate = (io.read_bytes - prev['read']) / dt
                            write_rate = (io.write_bytes - prev['write']) / dt
                            
                            if read_rate > 5000 or write_rate > 5000: # Threshold 5KB/s
                                processes.append({
                                    'pid': pid,
                                    'name': pinfo['name'],
                                    'read_rate': max(0, read_rate),
                                    'write_rate': max(0, write_rate)
                                })
                    
                    self._process_io_history[pid] = {
                        'read': io.read_bytes, 'write': io.write_bytes, 'time': now
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError, TypeError):
                    continue
            
            # Efficient cleanup
            if self._scan_counter % 10 == 0:
                current_pids = set(psutil.pids())
                self._process_io_history = {pid: data for pid, data in self._process_io_history.items() if pid in current_pids}
                    
            processes.sort(key=lambda x: x['read_rate'] + x['write_rate'], reverse=True)
            return processes[:8]
            
        except Exception as e:
            return []

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
                        # Use DeviceID (e.g. \\.\PHYSICALDRIVE0) or fallback to index-based name
                        device_id = drive.DeviceID or f"\\\\.\\PHYSICALDRIVE{drive.Index}"
                        
                        disk_info = {
                            'device': device_id,
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
        """Get per-disk IO statistics with rate, IOPS, latency and busy% calculation"""
        import psutil

        result = {}
        try:
            current_io = psutil.disk_io_counters(perdisk=True)
            current_time = time.time()

            for device, io in current_io.items():
                norm_device = self._normalize_device_name(device)

                if norm_device not in self._previous_io:
                    self._previous_io[norm_device] = io
                    self._previous_time[norm_device] = current_time
                    result[norm_device] = {
                        'read_rate': 0, 'write_rate': 0,
                        'read_iops': 0, 'write_iops': 0,
                        'read_latency_ms': 0, 'write_latency_ms': 0,
                        'busy_pct': 0,
                    }
                    continue

                prev = self._previous_io[norm_device]
                time_delta = current_time - self._previous_time[norm_device]

                if time_delta > 0 and prev:
                    read_rate  = (io.read_bytes  - prev.read_bytes)  / time_delta
                    write_rate = (io.write_bytes - prev.write_bytes) / time_delta

                    delta_rc = max(0, io.read_count  - prev.read_count)
                    delta_wc = max(0, io.write_count - prev.write_count)
                    delta_rt = max(0, io.read_time   - prev.read_time)   # ms
                    delta_wt = max(0, io.write_time  - prev.write_time)  # ms

                    read_iops  = delta_rc / time_delta
                    write_iops = delta_wc / time_delta
                    read_lat   = (delta_rt / delta_rc) if delta_rc > 0 else 0.0
                    write_lat  = (delta_wt / delta_wc) if delta_wc > 0 else 0.0
                    busy_pct   = min(100.0, (delta_rt + delta_wt) / (time_delta * 1000) * 100)
                else:
                    read_rate = write_rate = 0
                    read_iops = write_iops = 0
                    read_lat = write_lat = busy_pct = 0.0

                result[norm_device] = {
                    'read_rate':       max(0, read_rate),
                    'write_rate':      max(0, write_rate),
                    'read_iops':       max(0.0, read_iops),
                    'write_iops':      max(0.0, write_iops),
                    'read_latency_ms': max(0.0, read_lat),
                    'write_latency_ms': max(0.0, write_lat),
                    'busy_pct':        busy_pct,
                }

                self._previous_io[norm_device] = io
                self._previous_time[norm_device] = current_time

        except Exception as e:
            log_error(LogCategory.DISK, f"IO stats error: {e}")

        return result

    def _normalize_device_name(self, device: Any) -> str:
        """Normalize device name for consistent key matching between WMI and psutil"""
        if device is None: return ""
        d_str = str(device).upper().strip()
        if platform.system() == 'Windows':
            # Remove \\.\ prefix
            normalized = d_str.replace('\\\\.\\', '')
            # Handle "0" -> "PHYSICALDRIVE0"
            if normalized.isdigit():
                return f"PHYSICALDRIVE{normalized}"
            return normalized
        return d_str

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

