"""
CPU Data Collector
"""
import platform
import subprocess
from systemmonitor.typing import Dict, Any, List, Optional


class CPUCollector:
    """Collect CPU usage and information"""

    def __init__(self):
        self._info_cache: Optional[Dict[str, Any]] = None
        self._cache_initialized = False
        self._cache_sizes: Optional[Dict[str, int]] = None

    def collect(self) -> Dict[str, Any]:
        """Collect current CPU data"""
        try:
            import psutil

            percent = psutil.cpu_percent(interval=0.1)
            per_core = psutil.cpu_percent(interval=None, percpu=True)

            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else 0
            freq_max = freq.max if freq else 0

            times = psutil.cpu_times()

            stats = psutil.cpu_stats()

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
        """Get CPU temperature using multiple fallback methods"""
        import psutil

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

        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -First 1).CurrentTemperature"],
                    capture_output=True, text=True, timeout=3
                )
                if result.stdout.strip():
                    temp_k = float(result.stdout.strip())
                    return temp_k / 10 - 273.15
            except Exception:
                pass

        return None

    def get_info(self) -> Dict[str, Any]:
        """Get static CPU information (cached)"""
        if self._cache_initialized:
            return self._info_cache or {}

        try:
            import psutil

            cpu_name = self._get_cpu_name()

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
        name = platform.processor()
        if name and name.strip():
            return name.strip()

        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-CimInstance Win32_Processor).Name | Select-Object -First 1"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                pass

        return "Unknown CPU"

    def _detect_manufacturer(self, cpu_name: str) -> str:
        """Detect CPU manufacturer from name"""
        name_upper = cpu_name.upper()
        if 'INTEL' in name_upper:
            return 'Intel'
        elif 'AMD' in name_upper or 'RYZEN' in name_upper or ' EPYC' in name_upper:
            return 'AMD'
        elif 'ARM' in name_upper:
            return 'ARM'
        elif 'APPLE' in name_upper:
            return 'Apple'
        return 'Unknown'

    def get_cache_info(self) -> Dict[str, int]:
        """Get CPU cache sizes in KB - L1, L2, L3"""
        if self._cache_sizes is not None:
            return self._cache_sizes

        self._cache_sizes = {'L1': 0, 'L2': 0, 'L3': 0}

        if platform.system() != 'Windows':
            self._cache_sizes = self._get_cache_linux()
            return self._cache_sizes

        try:
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                if hasattr(cpu, 'L2CacheSize') and cpu.L2CacheSize:
                    self._cache_sizes['L2'] = int(cpu.L2CacheSize)
                if hasattr(cpu, 'L3CacheSize') and cpu.L3CacheSize:
                    self._cache_sizes['L3'] = int(cpu.L3CacheSize)
                break

            if self._cache_sizes['L2'] == 0 or self._cache_sizes['L3'] == 0:
                fallback = self._get_cache_via_powershell()
                if fallback['L1'] > 0:
                    self._cache_sizes['L1'] = fallback['L1']
                if fallback['L2'] > 0:
                    self._cache_sizes['L2'] = fallback['L2']
                if fallback['L3'] > 0:
                    self._cache_sizes['L3'] = fallback['L3']

        except Exception:
            self._cache_sizes = self._get_cache_via_powershell()

        return self._cache_sizes

    def _get_cache_via_powershell(self) -> Dict[str, int]:
        """Fallback to get cache info via PowerShell"""
        cache = {'L1': 0, 'L2': 0, 'L3': 0}
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 """
                 $cache = Get-CimInstance Win32_CacheMemory | Where-Object { $_.DeviceID -match 'L[123]' -and $_.InstalledSize -gt 0 }
                 foreach ($c in $cache) {
                     if ($c.DeviceID -match 'L1') { Write-Output "L1:$($c.InstalledSize)" }
                     elseif ($c.DeviceID -match 'L2') { Write-Output "L2:$($c.InstalledSize)" }
                     elseif ($c.DeviceID -match 'L3') { Write-Output "L3:$($c.InstalledSize)" }
                 }
                 """],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.strip().split(':')
                        if key in cache:
                            cache[key] = int(value) if value.isdigit() else 0

            if cache['L1'] == 0 and cache['L2'] == 0:
                result2 = subprocess.run(
                    ["powershell", "-Command",
                     """
                     $proc = Get-CimInstance Win32_Processor
                     Write-Output "L2:$($proc.L2CacheSize)"
                     Write-Output "L3:$($proc.L3CacheSize)"
                     """],
                    capture_output=True, text=True, timeout=5
                )
                if result2.stdout:
                    for line in result2.stdout.strip().split('\n'):
                        if ':' in line:
                            key, value = line.strip().split(':')
                            if key in cache and value.isdigit():
                                cache[key] = int(value)
        except Exception:
            pass
        return cache

    def _get_cache_linux(self) -> Dict[str, int]:
        """Get cache info from Linux /proc/cpuinfo"""
        cache = {'L1': 0, 'L2': 0, 'L3': 0}
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('cache size'):
                        size_str = line.split(':')[1].strip()
                        size_kb = int(''.join(filter(str.isdigit, size_str)))
                        if 'L2' in line:
                            cache['L2'] = size_kb
                        elif 'L3' in line:
                            cache['L3'] = size_kb
        except Exception:
            pass
        return cache

