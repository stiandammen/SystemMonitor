"""
CPU Data Collector
"""
import platform
from typing import Dict, Any, List, Optional


class CPUCollector:
    """Collect CPU usage and information"""
    
    def __init__(self):
        self._info_cache: Optional[Dict[str, Any]] = None
        self._cache_initialized = False
    
    def collect(self) -> Dict[str, Any]:
        """Collect current CPU data"""
        try:
            import psutil
            
            # Get CPU percent (blocking for accuracy)
            percent = psutil.cpu_percent(interval=0.1)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            
            # Get frequency
            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else 0
            freq_max = freq.max if freq else 0
            
            # Get CPU times
            times = psutil.cpu_times()
            
            # Get stats
            stats = psutil.cpu_stats()
            
            # Try to get temperature
            temperature = self._get_temperature()
            
            return {
                'percent': percent,
                'per_core': per_core,
                'core_count': psutil.cpu_count(logical=False) or 1,
                'thread_count': psutil.cpu_count(logical=True) or 1,
                'frequency_current': freq_current,
                'frequency_max': freq_max,
                'temperature': temperature,
                'ctx_switches': stats.ctx_switches if hasattr(stats, 'ctx_switches') else 0,
                'interrupts': stats.interrupts if hasattr(stats, 'interrupts') else 0,
            }
            
        except Exception as e:
            print(f"CPU collect error: {e}")
            return self._get_fallback_data()
    
    def _get_temperature(self) -> Optional[float]:
        """Try to get CPU temperature"""
        # Temperature collection is handled by CPUCollectorThread in collector.py
        # This method is a fallback and rarely works on modern Windows
        return None
    
    def get_info(self) -> Dict[str, Any]:
        """Get static CPU information (cached)"""
        if self._cache_initialized:
            return self._info_cache or {}
        
        try:
            import psutil
            
            # Get CPU name
            cpu_name = self._get_cpu_name()
            
            # Detect manufacturer
            manufacturer = self._detect_manufacturer(cpu_name)
            
            self._info_cache = {
                'name': cpu_name,
                'manufacturer': manufacturer,
                'cores': psutil.cpu_count(logical=False) or 1,
                'threads': psutil.cpu_count(logical=True) or 1,
                'architecture': platform.machine(),
            }
            
            self._cache_initialized = True
            return self._info_cache
            
        except Exception as e:
            print(f"CPU info error: {e}")
            return {}
    
    def _get_cpu_name(self) -> str:
        """Get CPU name from various sources"""
        # Try platform.processor()
        name = platform.processor()
        if name and name != '':
            return name
        
        # Try WMI on Windows
        if platform.system() == 'Windows':
            try:
                import wmi
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                    if cpu.Name:
                        return cpu.Name.strip()
            except Exception:
                pass
        
        # Try /proc/cpuinfo on Linux
        if platform.system() == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            return line.split(':', 1)[1].strip()
            except Exception:
                pass
        
        return "Unknown CPU"
    
    def _detect_manufacturer(self, cpu_name: str) -> str:
        """Detect CPU manufacturer from name"""
        name_upper = cpu_name.upper()
        if 'INTEL' in name_upper:
            return 'Intel'
        elif 'AMD' in name_upper:
            return 'AMD'
        elif 'ARM' in name_upper:
            return 'ARM'
        else:
            return 'Unknown'
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data when collection fails"""
        return {
            'percent': 0.0,
            'per_core': [],
            'core_count': 1,
            'thread_count': 1,
            'frequency_current': 0,
            'frequency_max': 0,
            'temperature': None,
            'ctx_switches': 0,
            'interrupts': 0,
        }
