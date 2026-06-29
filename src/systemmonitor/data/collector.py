"""
Data Collector - Optimized Threaded Architecture
Professional technician-grade system monitoring
Uses separate threads for different data types with optimal refresh intervals
"""
import time
import platform
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

from systemmonitor.utils.logger import get_logger, LogCategory, log_debug, log_info, log_warning, log_error, log_exception


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
        # Multiplier applied to REFRESH_INTERVAL, adjustable at runtime via the
        # "Update Speed" setting (Fast/Normal/Low). 1.0 = the class default.
        self._interval_scale = 1.0

    def set_interval_scale(self, scale: float):
        """Adjust the collection cadence at runtime (e.g. from the Update Speed setting).

        Also rescales the emit throttle so faster settings actually surface
        more frequent updates instead of being capped by a fixed throttle.
        """
        self._interval_scale = max(0.1, float(scale))
        self._min_emit_interval = max(0.05, self.REFRESH_INTERVAL * self._interval_scale * 0.8)

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

                # Sleep for optimal interval (scaled by the Update Speed setting)
                elapsed = time.time() - start_time
                sleep_time = max(0, self.REFRESH_INTERVAL * self._interval_scale - elapsed)
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
        self._cpu_manager = None
        self._init_cpu_manager()

    def _init_cpu_manager(self):
        """Initialize the centralized CPU manager (name/topology/temperature)"""
        try:
            from systemmonitor.data.hardware.cpu_manager import CPUManager
            self._cpu_manager = CPUManager()
        except Exception as e:
            log_error(LogCategory.CPU, f"CPU manager init failed: {e}")
            self._cpu_manager = None

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
                'temperature': self._cpu_manager.get_temperature() if self._cpu_manager else None,
                'interrupts': stats.interrupts if hasattr(stats, 'interrupts') else 0,
                'ctx_switches': stats.ctx_switches if hasattr(stats, 'ctx_switches') else 0,
            }

            return result

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
            from systemmonitor.data.memory import get_ram_type

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
                'ram_type': get_ram_type(),
            }

        except Exception as e:
            log_exception(LogCategory.MEMORY, "Memory collection failed", e)
            return {}


class DiskCollectorThread(BaseCollector):
    """Disk data collector - runs in background thread with robust tracking"""

    REFRESH_INTERVAL = 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._previous_io = None
        self._previous_time = 0
        self._io_per_disk = {}
        self._disk_mapping = {}
        self._last_partition_set = set()
        # Global robust metrics state
        self._prev_sys_io = None
        self._prev_sys_time = 0
        self._smoothed_read = 0.0
        self._smoothed_write = 0.0

    def _collect(self) -> dict:
        """Collect disk data with global robust smoothing"""
        try:
            import psutil
            import time
            current_time = time.time()

            # Global robust metrics calculation
            sys_io = psutil.disk_io_counters(perdisk=False)
            if self._prev_sys_io is None:
                self._prev_sys_io = sys_io
                self._prev_sys_time = current_time
            else:
                dt = current_time - self._prev_sys_time
                if dt > 0:
                    r_raw = (sys_io.read_bytes - self._prev_sys_io.read_bytes) / dt
                    w_raw = (sys_io.write_bytes - self._prev_sys_io.write_bytes) / dt
                    
                    alpha = 0.3
                    self._smoothed_read = (alpha * r_raw) + ((1 - alpha) * self._smoothed_read)
                    self._smoothed_write = (alpha * w_raw) + ((1 - alpha) * self._smoothed_write)
                
                self._prev_sys_io = sys_io
                self._prev_sys_time = current_time

            # Get current partition list
            current_partitions = psutil.disk_partitions(all=False)
            current_partition_set = set(p.device for p in current_partitions if p.fstype)

            # Build mapping only if partitions changed or not initialized
            if current_partition_set != self._last_partition_set:
                self._update_disk_mapping()
                self._last_partition_set = current_partition_set

            # Get partition info
            partitions = []
            partition_io = {}

            for part in current_partitions:
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

            return {
                'partitions': partitions,
                'read_rate': max(0, self._smoothed_read),
                'write_rate': max(0, self._smoothed_write),
                'partition_io': partition_io,
                'total_read': sys_io.read_bytes,
                'total_write': sys_io.write_bytes,
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
                ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_DiskDrive | ForEach-Object { $dd = $_; "
                 "Get-CimInstance -Query \"ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($dd.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition\" | "
                 "ForEach-Object { Get-CimInstance -Query \"ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($_.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition\" | "
                 "ForEach-Object { \"$($dd.Index)|$($_.DeviceID)\" } } }"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
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
    """Network data collector - runs in background thread with realistic speed tracking"""

    REFRESH_INTERVAL = 0.5  # 500ms for network (high frequency data)
    EMA_ALPHA = 0.3  # Smoothing factor (0.1 to 0.3 is usually good)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._previous_io = None
        self._previous_time = 0
        self._smoothed_download = 0.0
        self._smoothed_upload = 0.0
        self._active_interface = None

    def _collect(self) -> dict:
        """Collect network data with realistic speed calculation and smoothing"""
        try:
            import psutil
            import time

            # Get stats per interface to find the most active one
            io_dict = psutil.net_io_counters(pernic=True)
            stats = psutil.net_if_stats()
            current_time = time.time()

            # Find best interface if not set or periodically re-check
            if not self._active_interface or int(current_time) % 30 == 0:
                self._active_interface = self._find_active_interface(io_dict, stats)

            # Get global or interface-specific counters
            # Using total counters for fallback, but preferred interface if possible
            total_io = psutil.net_io_counters()
            
            # If we found a likely physical active interface, we can use its specific counters
            # for "realism", but users often want the sum of all physical traffic.
            # For now, let's use the sum but try to exclude virtual ones if we wanted to be very advanced.
            # Standard approach: use total but apply smoothing.
            
            if self._previous_io is None:
                self._previous_io = total_io
                self._previous_time = current_time
                return {
                    'download_speed': 0, 
                    'upload_speed': 0, 
                    'bytes_sent': total_io.bytes_sent, 
                    'bytes_recv': total_io.bytes_recv,
                    'active_interface': self._active_interface
                }

            time_delta = current_time - self._previous_time
            if time_delta > 0:
                raw_download = (total_io.bytes_recv - self._previous_io.bytes_recv) / time_delta
                raw_upload = (total_io.bytes_sent - self._previous_io.bytes_sent) / time_delta
                
                # Apply Exponential Moving Average (EMA) for smoothing
                self._smoothed_download = (self.EMA_ALPHA * raw_download) + ((1 - self.EMA_ALPHA) * self._smoothed_download)
                self._smoothed_upload = (self.EMA_ALPHA * raw_upload) + ((1 - self.EMA_ALPHA) * self._smoothed_upload)
            else:
                raw_download = raw_upload = 0

            self._previous_io = total_io
            self._previous_time = current_time

            # Get active connections (throttled)
            connections = []
            if int(current_time) % 5 == 0:
                try:
                    import socket
                    for conn in psutil.net_connections(kind="inet"):
                        try:
                            connections.append({
                                "local_ip":    conn.laddr.ip   if conn.laddr else "—",
                                "local_port":  conn.laddr.port if conn.laddr else "—",
                                "remote_ip":   conn.raddr.ip   if conn.raddr else "—",
                                "remote_port": conn.raddr.port if conn.raddr else "—",
                                "proto":       "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                                "state":       conn.status or "—",
                            })
                        except (OSError, ValueError):
                            pass
                except Exception:
                    pass

            # Get interface stats and addresses (throttled)
            interfaces = {}
            if int(current_time) % 10 == 0:
                try:
                    stats = psutil.net_if_stats()
                    addrs = psutil.net_if_addrs()
                    for name, stat in stats.items():
                        ip = "—"
                        for addr in addrs.get(name, []):
                            import socket
                            if addr.family == socket.AF_INET:
                                ip = addr.address
                                break
                        interfaces[name] = {
                            'isup': stat.isup,
                            'speed': stat.speed,
                            'ip': ip
                        }
                except Exception:
                    pass

            return {
                'download_speed': max(0, self._smoothed_download),
                'upload_speed': max(0, self._smoothed_upload),
                'bytes_sent': total_io.bytes_sent,
                'bytes_recv': total_io.bytes_recv,
                'active_interface': self._active_interface,
                'raw_download': max(0, raw_download),
                'raw_upload': max(0, raw_upload),
                'connections': connections if connections else None,
                'interfaces': interfaces if interfaces else None
            }

        except Exception as e:
            log_exception(LogCategory.NETWORK, "Network collection failed", e)
            return {}

    def _find_active_interface(self, io_dict, stats_dict) -> str:
        """Heuristic to find the likely primary physical interface"""
        best_iface = None
        max_traffic = -1
        
        # Keywords that often indicate virtual/internal interfaces
        virtual_keywords = ['loopback', 'lo', 'virtual', 'docker', 'veth', 'br-', 'vmnet', 'vbox', 'pseudo', 'teredo', 'tunnel']
        
        for name, io in io_dict.items():
            # Skip loopback and known virtuals
            lname = name.lower()
            if any(k in lname for k in virtual_keywords):
                continue
                
            # Check if interface is UP
            is_up = stats_dict.get(name).isup if name in stats_dict else False
            if not is_up:
                continue
                
            # Pick the one with the most total traffic (sent + recv)
            traffic = io.bytes_sent + io.bytes_recv
            if traffic > max_traffic:
                max_traffic = traffic
                best_iface = name
                
        return best_iface or "Total"


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
            from systemmonitor.data.hardware.gpu_manager import GPUManager
            self._gpu_manager = GPUManager()
            log_info(LogCategory.GPU, "Enhanced GPU manager initialized")
        except Exception as e:
            self._gpu_init_error = str(e)
            log_error(LogCategory.GPU, f"GPU manager init failed: {e}")
            self._gpu_manager = None

    def _get_wmi_gpu_temperature(self) -> Optional[float]:
        """Generic fallback to get GPU temperature via WMI or PowerShell"""
        if platform.system() != 'Windows':
            return None
            
        try:
            import subprocess
            # Try to get any temperature from MSAcpi or other thermal zones that might be GPU-related
            # on some laptops/systems
            cmd = "(Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Where-Object { $_.CurrentTemperature -gt 0 } | Select-Object -First 1).CurrentTemperature"
            result = subprocess.run(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=2, creationflags=0x08000000)
            if result.stdout.strip():
                return float(result.stdout.strip()) / 10 - 273.15
        except:
            pass
            
        return None

    def _collect(self) -> dict:
        """Collect GPU data using the enhanced GPU manager"""
        if self._gpu_manager is None:
            return {'available': False, 'error': self._gpu_init_error or 'GPU manager not initialized'}

        try:
            # Detect all GPUs
            gpus = self._gpu_manager.detect_gpus()

            # Prepare comprehensive GPU data
            gpu_data = {
                'available': len(gpus) > 0,
                'count': len(gpus),
                'gpus': [gpu.to_dict() for gpu in gpus],
            }

            # Find the best temperature across all GPUs
            best_temp = None
            for gpu in gpus:
                if gpu.temperature_celsius is not None and gpu.temperature_celsius > 0:
                    best_temp = gpu.temperature_celsius
                    break
            
            # If still no temp, try WMI fallback for any GPU/ThermalZone temp
            if best_temp is None:
                best_temp = self._get_wmi_gpu_temperature()

            # Format data for backward compatibility with existing UI
            primary_gpu = gpus[0] if gpus else None

            if primary_gpu:
                gpu_data.update({
                    'name':               primary_gpu.name,
                    'vendor':             primary_gpu.vendor.value,
                    'load':               primary_gpu.gpu_utilization_percent,
                    'memory_used':        primary_gpu.vram_used_mb,
                    'memory_total':       primary_gpu.vram_total_mb,
                    'vram_mb':            primary_gpu.vram_total_mb,
                    'memory_percent':     primary_gpu.vram_percent,
                    'temperature':        best_temp if best_temp is not None else primary_gpu.temperature_celsius,
                    'hotspot_temp':       primary_gpu.hotspot_temp_celsius,
                    'memory_temp':        primary_gpu.memory_temp_celsius,
                    'power':              primary_gpu.power_draw_watts,
                    'power_limit':        primary_gpu.power_limit_watts,
                    'fan_speed':          primary_gpu.fan_speed_percent,
                    'fan_speed_rpm':      primary_gpu.fan_speed_rpm,
                    'core_clock_mhz':     primary_gpu.core_clock_mhz,
                    'core_clock_boost_mhz': primary_gpu.core_clock_boost_mhz,
                    'memory_clock_mhz':   primary_gpu.memory_clock_mhz,
                    'pci_generation':     primary_gpu.pci_generation,
                    'pci_link_width':     primary_gpu.pci_link_width,
                    'uuid':               primary_gpu.uuid,
                    'device_id':          primary_gpu.device_id,
                    'pci_bus':            primary_gpu.pci_bus,
                    'driver_version':     primary_gpu.driver_version,
                    'gpu_type':           primary_gpu.gpu_type.value,
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
        self._cpu_manager = None
        self._battery_manager = None
        self._sensor_manager = None
        self._init_cpu_manager()
        self._init_battery_manager()
        self._init_sensor_manager()

    def _init_cpu_manager(self):
        """Initialize the centralized CPU manager (name cleanup/topology)"""
        try:
            from systemmonitor.data.hardware.cpu_manager import CPUManager
            self._cpu_manager = CPUManager()
        except Exception as e:
            log_error(LogCategory.CPU, f"CPU manager init failed: {e}")
            self._cpu_manager = None

    def _init_battery_manager(self):
        """Initialize the battery/power-plan reader (returns None on desktops)"""
        try:
            from systemmonitor.data.hardware.battery_manager import BatteryManager
            self._battery_manager = BatteryManager()
        except Exception as e:
            log_error(LogCategory.HARDWARE, f"Battery manager init failed: {e}")
            self._battery_manager = None

    def _init_sensor_manager(self):
        """Initialize the extended-sensor reader (fan RPM / voltages)"""
        try:
            from systemmonitor.data.hardware.sensor_manager import SensorManager
            self._sensor_manager = SensorManager()
        except Exception as e:
            log_error(LogCategory.HARDWARE, f"Sensor manager init failed: {e}")
            self._sensor_manager = None

    def _get_sensor_info(self):
        """Return {'fans': [...], 'voltages': [...]} of plain dicts (best-effort)"""
        if self._sensor_manager is None:
            return {'fans': [], 'voltages': []}
        try:
            fans = [{'label': f.label, 'rpm': f.rpm} for f in self._sensor_manager.get_fan_speeds()]
        except Exception:
            fans = []
        try:
            voltages = [{'label': v.label, 'volts': v.volts} for v in self._sensor_manager.get_voltages()]
        except Exception:
            voltages = []
        return {'fans': fans, 'voltages': voltages}

    def _get_battery_info(self):
        """Return a plain dict of battery status, or None if no battery is present"""
        if self._battery_manager is None:
            return None
        try:
            info = self._battery_manager.get_status()
        except Exception:
            return None
        if info is None:
            return None
        return {
            'percent': info.percent,
            'power_plugged': info.power_plugged,
            'secs_left': info.secs_left,
            'power_plan': info.power_plan,
            'status_text': info.status_text,
        }

    def _collect(self) -> dict:
        """Collect system info (cached for performance)"""
        current_time = time.time()

        # Return cache if still valid
        if self._info_cache and (current_time - self._cache_time) < self.REFRESH_INTERVAL:
            return self._info_cache

        try:
            import psutil

            cpu_info = self._cpu_manager.get_info() if self._cpu_manager else None
            gpu_name = self._get_gpu_name()
            motherboard = self._get_motherboard()
            ram_info = self._get_ram_info()

            self._info_cache = {
                'cpu_name': cpu_info.name if cpu_info else (platform.processor() or "Unknown CPU"),
                'cpu_topology': {
                    'physical_cores': cpu_info.physical_cores,
                    'logical_cores': cpu_info.logical_cores,
                    'performance_cores': cpu_info.performance_cores,
                    'efficiency_cores': cpu_info.efficiency_cores,
                    'has_hybrid_architecture': cpu_info.has_hybrid_architecture,
                } if cpu_info else None,
                'gpu_name': gpu_name,
                'motherboard': motherboard,
                'ram_info': ram_info,
                'boot_time': psutil.boot_time(),
                'battery': self._get_battery_info(),
                'sensors': self._get_sensor_info(),
            }
            self._cache_time = current_time

            return self._info_cache

        except Exception as e:
            log_exception(LogCategory.HARDWARE, "System info collection failed", e)
            return {}

    def _get_gpu_name(self) -> str:
        """Get GPU name"""
        if platform.system() == 'Windows':
            try:
                import subprocess
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_VideoController).Name | Select-Object -First 1"],
                    capture_output=True, text=True, timeout=5, creationflags=0x08000000
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
                    ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_BaseBoard).Product"],
                    capture_output=True, text=True, timeout=5, creationflags=0x08000000
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
