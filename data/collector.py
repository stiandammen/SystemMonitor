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

            return {
                'percent': percent,
                'per_core': per_core,
                'core_count': psutil.cpu_count(logical=False) or 1,
                'thread_count': psutil.cpu_count(logical=True) or 1,
                'frequency_current': freq.current if freq else 0,
                'frequency_max': freq.max if freq else 0,
            }

        except Exception as e:
            log_exception(LogCategory.CPU, "CPU collection failed", e)
            return {}


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

    REFRESH_INTERVAL = 2.0  # 2 seconds for disk (slower changing data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._previous_io = None
        self._previous_time = 0

    def _collect(self) -> dict:
        """Collect disk data"""
        try:
            import psutil

            # Get partition info
            partitions = []
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
                except (PermissionError, OSError):
                    pass

            # Get IO rates
            io_stats = self._get_io_stats()

            return {
                'partitions': partitions,
                'read_rate': io_stats.get('read_rate', 0),
                'write_rate': io_stats.get('write_rate', 0),
            }

        except Exception as e:
            log_exception(LogCategory.DISK, "Disk collection failed", e)
            return {}

    def _get_io_stats(self) -> dict:
        """Get disk I/O with rate calculation"""
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
    """GPU data collector - runs in background thread"""

    REFRESH_INTERVAL = 1.0  # 1 second for GPU

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpu_collector = None
        self._gpu_init_error = None
        self._init_gpu()

    def _init_gpu(self):
        """Initialize GPU collector backend"""
        try:
            from data.gpu import GPUCollector
            self._gpu_collector = GPUCollector()
            log_info(LogCategory.GPU, "GPU collector initialized")
        except Exception as e:
            self._gpu_init_error = str(e)
            log_error(LogCategory.GPU, f"GPU collector init failed: {e}")
            self._gpu_collector = None

    def _collect(self) -> dict:
        """Collect GPU data"""
        if self._gpu_collector is None:
            return {'available': False}

        try:
            gpu_data = self._gpu_collector.collect()
            gpu_info = self._gpu_collector.get_info()

            return {
                'available': gpu_data.get('available', False),
                'load': gpu_data.get('load', 0),
                'memory_used': gpu_data.get('memory_used', 0),
                'memory_total': gpu_data.get('memory_total', 0),
                'memory_percent': gpu_data.get('memory_percent', 0),
                'temperature': gpu_data.get('temperature'),
                'power': gpu_data.get('power'),
                'fan_speed': gpu_data.get('fan_speed'),
                'vendor': gpu_info.vendor if gpu_info else 'Unknown',
                'name': gpu_info.name if gpu_info else 'Unknown',
                'vram_mb': gpu_info.vram_mb if gpu_info else 0,
                'driver_version': gpu_info.driver_version if gpu_info else 'N/A',
            }

        except Exception as e:
            log_exception(LogCategory.GPU, "GPU collection failed", e)
            return {'available': False}


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


# Alias for backwards compatibility
DataCollector = SystemInfoCollectorThread