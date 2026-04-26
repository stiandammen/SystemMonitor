"""
Data Collector - System data collection
"""
import time
import platform
import subprocess
import sys
from PyQt5.QtCore import QThread, pyqtSignal

# Logging function that works in packaged app
def _log(msg):
    """Log message - works both in dev and packaged mode"""
    if getattr(sys, 'frozen', False):
        try:
            import os
            log_file = os.path.join(os.environ.get('TEMP', ''), 'SystemMonitor', 'collector.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a') as f:
                from datetime import datetime
                f.write(f"[{datetime.now()}] {msg}\n")
        except:
            pass
    else:
        print(msg)


class DataCollector(QThread):
    """Collects system data in background thread"""

    data_ready = pyqtSignal(dict)
    processes_updated = pyqtSignal(list)
    storage_updated = pyqtSignal(list)
    system_info_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._data = {}
        self._gpu_collector = None
        self._gpu_init_error = None

        # Track collection intervals
        self._last_process_update = 0
        self._last_storage_update = 0
        self._last_system_info_update = 0
        self._process_interval = 3  # seconds
        self._storage_interval = 5  # seconds
        self._system_info_interval = 10  # seconds

        # Caches for expensive calls
        self._system_info_cache = {}
        self._system_info_cache_time = 0
        self._system_info_cache_ttl = 30

    def run(self):
        """Main collection loop"""
        self._running = True
        _log("DataCollector.run() started")

        # Initialize GPU collector - with error handling
        try:
            from data.gpu import GPUCollector
            self._gpu_collector = GPUCollector()
            _log("GPUCollector initialized OK")
        except Exception as e:
            self._gpu_init_error = str(e)
            _log(f"GPUCollector init error: {e}")
            self._gpu_collector = None

        while self._running:
            try:
                current_time = time.time()
                self._collect_data()
                if current_time - self._last_process_update >= self._process_interval:
                    try:
                        _log("Starting process collection...")
                        self._collect_processes()
                        _log("Process collection OK")
                    except Exception as e:
                        _log(f"Process collection failed: {e}")
                    self._last_process_update = current_time

                if current_time - self._last_storage_update >= self._storage_interval:
                    try:
                        _log("Starting storage collection...")
                        self._collect_storage()
                        _log("Storage collection OK")
                    except Exception as e:
                        _log(f"Storage collection failed: {e}")
                    self._last_storage_update = current_time

                if current_time - self._last_system_info_update >= self._system_info_interval:
                    try:
                        _log("Starting system info collection...")
                        self._collect_system_info()
                        _log("System info collection OK")
                    except Exception as e:
                        _log(f"System info collection failed: {e}")
                    self._last_system_info_update = current_time

                self.data_ready.emit(self._data.copy())
                time.sleep(1)  # Update every second
            except Exception as e:
                _log(f"Data collection error: {e}")
                import traceback
                _log(f"Traceback: {traceback.format_exc()}")
                time.sleep(1)
    
    def _collect_data(self):
        """Collect all system data"""
        import psutil

        # CPU - use non-blocking version (interval=None uses cached value since last call)
        # For the first call, we need a short interval for accuracy
        if not hasattr(self, '_cpu_initialized'):
            self._data['cpu'] = {
                'percent': psutil.cpu_percent(interval=0.1),
                'per_core': psutil.cpu_percent(percpu=True),
                'count': psutil.cpu_count(),
            }
            self._cpu_initialized = True
        else:
            self._data['cpu'] = {
                'percent': psutil.cpu_percent(interval=None),
                'per_core': psutil.cpu_percent(percpu=True, interval=None),
                'count': psutil.cpu_count(),
            }

        # Memory
        mem = psutil.virtual_memory()
        self._data['memory'] = {
            'percent': mem.percent,
            'used': mem.used,
            'total': mem.total,
            'available': mem.available,
        }

        # Disk
        disk = psutil.disk_usage('/')
        self._data['disk'] = {
            'percent': disk.percent,
            'used': disk.used,
            'total': disk.total,
            'free': disk.free,
        }

        # Network
        net = psutil.net_io_counters()
        self._data['network'] = {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
        }

        # GPU
        if self._gpu_collector is not None:
            self._data['gpu'] = self._gpu_collector.collect()
            gpu_info = self._gpu_collector.get_info()
            self._data['gpu_info'] = {
                'vendor': gpu_info.vendor,
                'name': gpu_info.name,
                'vram_mb': gpu_info.vram_mb,
                'driver_version': gpu_info.driver_version,
            }
        else:
            self._data['gpu'] = {'available': False}
    
    def stop(self):
        """Stop data collection"""
        self._running = False
        self.wait(1000)
    
    def get_data(self):
        """Get current data"""
        return self._data.copy()

    def _collect_processes(self):
        """Collect process list - runs in background thread"""
        import psutil
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if proc.is_running():
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
            self.processes_updated.emit(processes[:100])  # Emit top 100
        except Exception as e:
            _log(f"Process collection error: {e}")

    def _collect_storage(self):
        """Collect storage info - runs in background thread"""
        import psutil
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                if not partition.fstype:
                    continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    })
                except PermissionError:
                    continue
            self.storage_updated.emit(partitions)
        except Exception as e:
            _log(f"Storage collection error: {e}")

    def _collect_system_info(self):
        """Collect system info - runs in background thread"""
        import psutil
        now = time.time()
        info = {}

        try:
            # CPU name
            if now - self._system_info_cache_time < self._system_info_cache_ttl and 'cpu_name' in self._system_info_cache:
                info['cpu_name'] = self._system_info_cache['cpu_name']
            else:
                cpu_name = self._get_cpu_name()
                self._system_info_cache['cpu_name'] = cpu_name
                info['cpu_name'] = cpu_name

            # GPU name
            if now - self._system_info_cache_time < self._system_info_cache_ttl and 'gpu_name' in self._system_info_cache:
                info['gpu_name'] = self._system_info_cache['gpu_name']
            else:
                gpu_name = self._get_gpu_name()
                self._system_info_cache['gpu_name'] = gpu_name
                info['gpu_name'] = gpu_name

            # Motherboard
            if now - self._system_info_cache_time < self._system_info_cache_ttl and 'motherboard' in self._system_info_cache:
                info['motherboard'] = self._system_info_cache['motherboard']
            else:
                motherboard = self._get_motherboard()
                self._system_info_cache['motherboard'] = motherboard
                info['motherboard'] = motherboard

            # RAM info
            if now - self._system_info_cache_time < self._system_info_cache_ttl and 'ram_info' in self._system_info_cache:
                info['ram_info'] = self._system_info_cache['ram_info']
            else:
                ram_info = self._get_ram_info()
                self._system_info_cache['ram_info'] = ram_info
                info['ram_info'] = ram_info

            self._system_info_cache_time = now
            self.system_info_updated.emit(info)
        except Exception as e:
            _log(f"System info collection error: {e}")

    def _get_cpu_name(self):
        """Get CPU name via WMI with caching"""
        try:
            if platform.system() == 'Windows':
                import wmi
                w = wmi.WMI()
                for cpu in w.Win32_Processor():
                    if cpu.Name:
                        return cpu.Name.strip()
        except:
            pass
        return platform.processor() or "Unknown CPU"

    def _get_gpu_name(self):
        """Get GPU name with caching"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                name = gpus[0].name
                if len(name) > 28:
                    return name[:28] + "..."
                return name
        except:
            pass
        return "N/A"

    def _get_motherboard(self):
        """Get motherboard with caching"""
        try:
            if platform.system() == 'Windows':
                import wmi
                w = wmi.WMI()
                return w.Win32_BaseBoard()[0].Product
        except:
            return "Unknown"

    def _get_ram_info(self):
        """Get RAM info: size and type with caching"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3))

            ram_type = "Unknown"
            speed = 0

            try:
                if platform.system() == 'Windows':
                    import wmi
                    w = wmi.WMI()
                    for mem_obj in w.Win32_PhysicalMemory():
                        if hasattr(mem_obj, 'Speed') and mem_obj.Speed:
                            speed = int(mem_obj.Speed)
                        if hasattr(mem_obj, 'MemoryType') and mem_obj.MemoryType:
                            mem_type = int(mem_obj.MemoryType)
                            type_map = {20: "DDR5", 21: "DDR4", 22: "DDR3", 24: "DDR2"}
                            ram_type = type_map.get(mem_type, "Unknown")
                            if ram_type != "Unknown":
                                break

                    if ram_type == "Unknown" and speed > 0:
                        if speed >= 6400:
                            ram_type = "DDR5"
                        elif speed >= 3200:
                            ram_type = "DDR4"
                        elif speed >= 2133:
                            ram_type = "DDR3"
                        else:
                            ram_type = "DDR"
            except:
                pass

            if ram_type != "Unknown":
                return f"{total_gb} GB {ram_type}"
            return f"{total_gb} GB"
        except:
            return "Unknown"
