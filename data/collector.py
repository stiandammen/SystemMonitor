"""
Data Collector - Optimized Threaded Architecture
Professional technician-grade system monitoring
Uses separate threads for different data types with optimal refresh intervals
"""
import time
import platform
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

from utils.logger import get_logger, LogCategory, log_debug, log_info, log_warning, log_error, log_exception


class BaseCollector(QThread):
    """Base class for all data collectors with proper threading and signals"""

    # Signal emitted with collected data dict
    data_updated = pyqtSignal(dict)

    # Refresh interval in seconds
    REFRESH_INTERVAL = 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._data = {}
        self._last_emit_time = 0
        self._min_emit_interval = 0.5  # Minimum interval between emissions

    def run(self):
        """Main collection loop - runs in background thread"""
        self._running = True
        log_info(LogCategory.COLLECTOR, f"{self.__class__.__name__} started")

        while self._running:
            try:
                start_time = time.time()

                # Collect data
                collected = self._collect()

                if collected:
                    self._data.update(collected)

                    # Emit signal with throttling
                    current_time = time.time()
                    if current_time - self._last_emit_time >= self._min_emit_interval:
                        self.data_updated.emit(self._data.copy())
                        self._last_emit_time = current_time

                # Sleep for optimal interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.REFRESH_INTERVAL - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                log_exception(LogCategory.COLLECTOR, f"{self.__class__.__name__} collection error", e)
                time.sleep(1)

    def stop(self):
        """Stop data collection"""
        self._running = False

    def _collect(self) -> dict:
        """Override in subclasses to implement specific collection logic"""
        return {}

    def get_data(self) -> dict:
        """Get current cached data"""
        return self._data.copy()


class CPUCollectorThread(BaseCollector):
    """CPU data collector - runs in background thread"""

    REFRESH_INTERVAL = 0.5  # 500ms for CPU (high frequency data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cpu_initialized = False

    def _collect(self) -> dict:
        """Collect CPU data"""
        try:
            import psutil

            # First call needs a small interval for accuracy
            if not self._cpu_initialized:
                percent = psutil.cpu_percent(interval=0.1)
                per_core = psutil.cpu_percent(percpu=True, interval=None)
                self._cpu_initialized = True
            else:
                # Subsequent calls use cached value
                percent = psutil.cpu_percent(interval=None)
                per_core = psutil.cpu_percent(percpu=True, interval=None)

            freq = psutil.cpu_freq()

            # Get CPU stats for interrupts and ctx switches
            stats = psutil.cpu_stats()

            result = {
                'percent': percent,
                'per_core': per_core,
                'core_count': psutil.cpu_count(logical=False) or 1,
                'thread_count': psutil.cpu_count(logical=True) or 1,
                'frequency_current': freq.current if freq else 0,
                'frequency_max': freq.max if freq else 0,
                'frequency_min': freq.min if freq else 0,
                'temperature': self._get_cpu_temperature(),
                'interrupts': stats.interrupts if hasattr(stats, 'interrupts') else 0,
                'ctx_switches': stats.ctx_switches if hasattr(stats, 'ctx_switches') else 0,
            }

            return result

        except Exception as e:
            log_exception(LogCategory.CPU, "CPU collection failed", e)
            return {}

    def _get_cpu_temperature(self):
        """Get CPU temperature using psutil sensors or WMI fallback"""
        import psutil
        # Try psutil sensors first (only if available)
        if hasattr(psutil, 'sensors_temperatures'):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for key in ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower', 'cpu', 'cpu0']:
                        if key in temps:
                            entries = temps[key]
                            if entries:
                                for entry in entries:
                                    if hasattr(entry, 'current') and entry.current is not None:
                                        return float(entry.current)
            except (AttributeError, Exception):
                pass

        # Fallback for Windows - try WMI MSAcpi_ThermalZoneTemperature
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1).CurrentTemperature"],
                capture_output=True, text=True, timeout=3
            )
            if result.stdout.strip():
                # Returns temperature in tenths of Kelvin
                temp_k = float(result.stdout.strip())
                return temp_k / 10 - 273.15
        except Exception:
            pass

        # Try alternative via HWiNFO shared memory
        try:
            temp = self._read_hwinfo_temp()
            if temp is not None:
                return temp
        except Exception:
            pass

        return None

    def _read_hwinfo_temp(self):
        """Try to read CPU temp from HWiNFO shared memory"""
        import ctypes

        # HWiNFO shared memory signatures (V1-V4)
        HWINFO_SIGNATURES = [
            b"HWiNFO",   # V1/V2 64-bit
            b"HWiNFO32", # V1/V2 32-bit
            b"HWiNFO_V", # V3/V4 signature prefix
            b"HWiNFO32_V", # V3/V4 32-bit
        ]

        try:
            kernel32 = ctypes.windll.kernel32

            # HWiNFO shared memory names (newer versions use _V2, _V3, _V4)
            HWINFO_NAMES = [
                "HWiNFO32_Sens", "HWiNFO64_Sens",
                "HWiNFO32_V2", "HWiNFO64_V2",
                "HWiNFO32_V3", "HWiNFO64_V3",
                "HWiNFO32_V4", "HWiNFO64_V4",
            ]

            mapping = None
            found_name = None
            handle = None

            for name in HWINFO_NAMES:
                handle = kernel32.OpenFileMappingW(0x0004, False, name)
                if handle:
                    found_name = name
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
                # Read signature (16 bytes to be safe)
                sig = ctypes.create_string_buffer(16)
                ctypes.memmove(sig, mapping, 16)

                # Check if signature matches any HWiNFO variant
                is_hwinfo = any(sig.raw[:len(s)] == s for s in HWINFO_SIGNATURES)

                if not is_hwinfo:
                    return None

                # Try multiple offsets to find temperature data
                # Different HWiNFO versions use different offsets
                for offset in [0x30, 0x34, 0x38, 0x40, 0x44, 0x48, 0x50, 0x60, 0x80, 0x100]:
                    try:
                        temp_raw = ctypes.c_float()
                        ctypes.memmove(ctypes.addressof(temp_raw), mapping + offset, 4)
                        temp = temp_raw.value
                        # Valid CPU temperature range: 0-100°C (some systems may show up to 125°C under load)
                        if 0 < temp < 125:
                            return temp
                    except Exception:
                        continue

                # Also try reading as Intel/AMD specific format
                # Some systems store temperature at offset 0xB0 or higher
                for offset in [0xB0, 0xB4, 0xB8, 0xBC, 0xC0, 0xC4]:
                    try:
                        temp_raw = ctypes.c_float()
                        ctypes.memmove(ctypes.addressof(temp_raw), mapping + offset, 4)
                        temp = temp_raw.value
                        if 20 < temp < 100:  # CPUs rarely run below 20°C
                            return temp
                    except Exception:
                        continue

                return None
            finally:
                if mapping:
                    kernel32.UnmapViewOfFile(mapping)
        except Exception:
            return None


class MemoryCollectorThread(BaseCollector):
    """Memory data collector - runs in background thread"""

    REFRESH_INTERVAL = 1.0  # 1 second for memory

    def _collect(self) -> dict:
        """Collect memory data"""
        try:
            import psutil

            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'percent': vm.percent,
                'used': vm.used,
                'total': vm.total,
                'available': vm.available,
                'free': vm.free,
                'cached': getattr(vm, 'cached', 0),
                'swap_percent': swap.percent,
                'swap_used': swap.used,
                'swap_total': swap.total,
            }

        except Exception as e:
            log_exception(LogCategory.MEMORY, "Memory collection failed", e)
            return {}


class DiskCollectorThread(BaseCollector):
    """Disk data collector - runs in background thread"""

    REFRESH_INTERVAL = 1.0  # 1 second for disk (higher frequency for speed tracking)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._previous_io = None
        self._previous_time = 0
        self._io_per_disk = {}  # device -> previous_io tuple
        self._disk_mapping = {}  # physical disk key -> drive letters

    def _collect(self) -> dict:
        """Collect disk data"""
        try:
            import psutil

            # Build mapping of physical disks to drive letters
            self._update_disk_mapping()

            # Get partition info
            partitions = []
            partition_io = {}  # mountpoint -> {read_rate, write_rate}

            for part in psutil.disk_partitions(all=False):
                if not part.fstype:
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    })

                    # Calculate per-partition IO rate using disk mapping
                    io_rates = self._get_partition_io_rates(part)
                    if io_rates:
                        partition_io[part.mountpoint] = io_rates

                except (PermissionError, OSError):
                    pass

            # Get total IO rates
            io_stats = self._get_total_io_stats()

            return {
                'partitions': partitions,
                'read_rate': io_stats.get('read_rate', 0),
                'write_rate': io_stats.get('write_rate', 0),
                'partition_io': partition_io,  # Per-partition IO rates
            }

        except Exception as e:
            log_exception(LogCategory.DISK, "Disk collection failed", e)
            return {}

    def _update_disk_mapping(self):
        """Build mapping of physical disks to drive letters using WMI"""
        if platform.system() != 'Windows':
            return
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_DiskDrive | ForEach-Object { $dd = $_; "
                 "Get-CimInstance -Query \"ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($dd.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition\" | "
                 "ForEach-Object { Get-CimInstance -Query \"ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($_.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition\" | "
                 "ForEach-Object { \"$($dd.Index)|$($_.DeviceID)\" } } }"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        parts = line.strip().split('|')
                        if len(parts) >= 2:
                            disk_idx = parts[0]
                            drive_letter = parts[1].replace(':', '').strip()
                            key = f"\\\\.\\PhysicalDrive{disk_idx}"
                            if key not in self._disk_mapping:
                                self._disk_mapping[key] = []
                            self._disk_mapping[key].append(f"{drive_letter}:\\")
        except Exception:
            pass

    def _get_partition_io_rates(self, partition) -> dict:
        """Get IO rates for a specific partition by mapping to physical disk"""
        try:
            import psutil

            current_io = psutil.disk_io_counters(perdisk=True)
            current_time = time.time()

            # Find the physical disk key for this partition's device
            partition_device = partition.device.replace('\\\\', '\\\\\\\\')

            # Try to match via our disk mapping
            physical_disk_key = None
            for disk_key, drive_letters in self._disk_mapping.items():
                if partition_device in drive_letters or partition.mountpoint in drive_letters:
                    physical_disk_key = disk_key
                    break

            # If no mapping found, try to find by device name pattern
            if physical_disk_key is None:
                for key in current_io.keys():
                    # Check if device matches partition device
                    if partition.device.replace('\\\\', '') in key.replace('\\\\', ''):
                        physical_disk_key = key
                        break
                    # Check if it's a drive letter match (e.g., partition.device = 'C:\\')
                    if partition.mountpoint and partition.mountpoint.rstrip('\\\\') in key:
                        physical_disk_key = key
                        break

            if physical_disk_key and physical_disk_key in current_io:
                io = current_io[physical_disk_key]
                prev = self._io_per_disk.get(physical_disk_key)

                if prev:
                    time_delta = current_time - prev['time']
                    if time_delta > 0:
                        read_rate = (io.read_bytes - prev['io'].read_bytes) / time_delta
                        write_rate = (io.write_bytes - prev['io'].write_bytes) / time_delta
                        self._io_per_disk[physical_disk_key] = {
                            'io': io,
                            'time': current_time
                        }
                        return {
                            'read_rate': max(0, read_rate),
                            'write_rate': max(0, write_rate)
                        }

                self._io_per_disk[physical_disk_key] = {
                    'io': io,
                    'time': current_time
                }

            return {}
        except Exception:
            return {}

    def _get_total_io_stats(self) -> dict:
        """Get total disk I/O with rate calculation"""
        try:
            import psutil

            current_io = psutil.disk_io_counters()
            current_time = time.time()

            if self._previous_io is None:
                self._previous_io = current_io
                self._previous_time = current_time
                return {'read_rate': 0, 'write_rate': 0}

            time_delta = current_time - self._previous_time
            if time_delta > 0 and self._previous_io:
                read_rate = (current_io.read_bytes - self._previous_io.read_bytes) / time_delta
                write_rate = (current_io.write_bytes - self._previous_io.write_bytes) / time_delta
            else:
                read_rate = write_rate = 0

            self._previous_io = current_io
            self._previous_time = current_time

            return {
                'read_rate': max(0, read_rate),
                'write_rate': max(0, write_rate),
            }

        except Exception:
            return {'read_rate': 0, 'write_rate': 0}


class NetworkCollectorThread(BaseCollector):
    """Network data collector - runs in background thread"""

    REFRESH_INTERVAL = 0.5  # 500ms for network (high frequency data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._previous_io = None
        self._previous_time = 0

    def _collect(self) -> dict:
        """Collect network data"""
        try:
            import psutil

            io = psutil.net_io_counters()
            current_time = time.time()

            if self._previous_io is None:
                self._previous_io = io
                self._previous_time = current_time
                return {'download_speed': 0, 'upload_speed': 0, 'bytes_sent': io.bytes_sent, 'bytes_recv': io.bytes_recv}

            time_delta = current_time - self._previous_time
            if time_delta > 0 and self._previous_io:
                download = (io.bytes_recv - self._previous_io.bytes_recv) / time_delta
                upload = (io.bytes_sent - self._previous_io.bytes_sent) / time_delta
            else:
                download = upload = 0

            self._previous_io = io
            self._previous_time = current_time

            return {
                'download_speed': max(0, download),
                'upload_speed': max(0, upload),
                'bytes_sent': io.bytes_sent,
                'bytes_recv': io.bytes_recv,
            }

        except Exception as e:
            log_exception(LogCategory.NETWORK, "Network collection failed", e)
            return {}


class GPUCollectorThread(BaseCollector):
    """GPU data collector - runs in background thread using enhanced GPU manager"""

    REFRESH_INTERVAL = 1.0  # 1 second for GPU

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpu_manager = None
        self._gpu_init_error = None
        self._init_gpu_manager()

    def _init_gpu_manager(self):
        """Initialize GPU manager"""
        try:
            from data.hardware.gpu_manager import GPUManager
            self._gpu_manager = GPUManager()
            log_info(LogCategory.GPU, "Enhanced GPU manager initialized")
        except Exception as e:
            self._gpu_init_error = str(e)
            log_error(LogCategory.GPU, f"GPU manager init failed: {e}")
            self._gpu_manager = None

    def _collect(self) -> dict:
        """Collect GPU data using the enhanced GPU manager"""
        if self._gpu_manager is None:
            return {'available': False, 'error': self._gpu_init_error or 'GPU manager not initialized'}

        try:
            # Detect all GPUs
            gpus = self._gpu_manager.detect_gpus()

            if not gpus:
                return {'available': False}

            # Format data for backward compatibility with existing UI
            # While also providing access to full GPU information
            primary_gpu = gpus[0] if gpus else None

            # Prepare comprehensive GPU data
            gpu_data = {
                'available': True,
                'count': len(gpus),
                'gpus': [gpu.to_dict() for gpu in gpus],  # Full information for all GPUs
            }

            # Add backward-compatible fields for primary GPU (for existing UI)
            if primary_gpu:
                gpu_data.update({
                    'name': primary_gpu.name,
                    'vendor': primary_gpu.vendor.value,
                    'load': primary_gpu.gpu_utilization_percent,
                    'memory_used': primary_gpu.vram_used_mb,
                    'memory_total': primary_gpu.vram_total_mb,
                    'memory_percent': primary_gpu.vram_percent,
                    'temperature': primary_gpu.temperature_celsius,
                    'hotspot_temp': primary_gpu.hotspot_temp_celsius,
                    'memory_temp': primary_gpu.memory_temp_celsius,
                    'power': primary_gpu.power_draw_watts,
                    'fan_speed': primary_gpu.fan_speed_percent,
                    'uuid': primary_gpu.uuid,
                    'device_id': primary_gpu.device_id,
                    'pci_bus': primary_gpu.pci_bus,
                    'driver_version': primary_gpu.driver_version,
                    'gpu_type': primary_gpu.gpu_type.value,
                })

            return gpu_data

        except Exception as e:
            log_exception(LogCategory.GPU, "GPU collection failed", e)
            return {'available': False, 'error': str(e)}


class SystemInfoCollectorThread(BaseCollector):
    """System static info collector - runs infrequently in background"""

    REFRESH_INTERVAL = 30.0  # 30 seconds for static info (rarely changes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._info_cache = {}
        self._cache_time = 0

    def _collect(self) -> dict:
        """Collect system info (cached for performance)"""
        current_time = time.time()

        # Return cache if still valid
        if self._info_cache and (current_time - self._cache_time) < self.REFRESH_INTERVAL:
            return self._info_cache

        try:
            import psutil

            cpu_name = self._get_cpu_name()
            gpu_name = self._get_gpu_name()
            motherboard = self._get_motherboard()
            ram_info = self._get_ram_info()

            self._info_cache = {
                'cpu_name': cpu_name,
                'gpu_name': gpu_name,
                'motherboard': motherboard,
                'ram_info': ram_info,
                'boot_time': psutil.boot_time(),
            }
            self._cache_time = current_time

            return self._info_cache

        except Exception as e:
            log_exception(LogCategory.HARDWARE, "System info collection failed", e)
            return {}

    def _get_cpu_name(self) -> str:
        """Get CPU name with caching"""
        if platform.system() == 'Windows':
            try:
                import subprocess
                result = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance Win32_Processor).Name"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return result.stdout.strip()
            except:
                pass
        return platform.processor() or "Unknown CPU"

    def _get_gpu_name(self) -> str:
        """Get GPU name"""
        if platform.system() == 'Windows':
            try:
                import subprocess
                result = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance Win32_VideoController).Name | Select-Object -First 1"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    name = result.stdout.strip()
                    return name[:40] + "..." if len(name) > 40 else name
            except:
                pass
        return "N/A"

    def _get_motherboard(self) -> str:
        """Get motherboard info"""
        if platform.system() == 'Windows':
            try:
                import subprocess
                result = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance Win32_BaseBoard).Product"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return result.stdout.strip()
            except:
                pass
        return "Unknown"

    def _get_ram_info(self) -> str:
        """Get RAM info"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3))
            return f"{total_gb} GB"
        except:
            return "Unknown"


# Legacy alias
SystemInfoCollector = SystemInfoCollectorThread
LegacyDataCollector = SystemInfoCollectorThread