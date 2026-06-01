"""
Memory Data Collector
"""
import subprocess
import re
from systemmonitor.typing import Dict, Any, List, Optional

_SMBIOS_TYPES = {
    20: "DDR",
    21: "DDR2",
    24: "DDR3",
    26: "DDR4",
    30: "LPDDR4",
    34: "DDR5",
    35: "LPDDR5",
}
_ram_type_cache: str | None = None


def get_ram_type() -> str:
    """Detect RAM type via SMBIOSMemoryType (runs PowerShell once, then returns cached result)."""
    global _ram_type_cache
    if _ram_type_cache is not None:
        return _ram_type_cache
    try:
        cmd = "Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty SMBIOSMemoryType"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True, text=True, timeout=8,
        )
        codes = re.findall(r'\d+', result.stdout)
        if not codes:
            _ram_type_cache = ""
            return ""
        detected = [_SMBIOS_TYPES[int(c)] for c in codes if int(c) in _SMBIOS_TYPES]
        unique = list(dict.fromkeys(detected))
        _ram_type_cache = ", ".join(unique) if unique else ""
    except Exception:
        _ram_type_cache = ""
    return _ram_type_cache


class MemoryCollector:
    """Collect memory (RAM and Swap) usage"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect current memory data"""
        try:
            import psutil
            
            # Virtual memory (RAM)
            vm = psutil.virtual_memory()
            
            # Swap memory
            swap = psutil.swap_memory()
            
            return {
                'ram': {
                    'total': vm.total,
                    'available': vm.available,
                    'used': vm.used,
                    'free': vm.free,
                    'percent': vm.percent,
                    'cached': getattr(vm, 'cached', 0),
                    'buffers': getattr(vm, 'buffers', 0),
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                }
            }
            
        except Exception as e:
            print(f"Memory collect error: {e}")
            return self._get_fallback_data()
    
    def get_top_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory consuming processes"""
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 0:
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'memory_percent': info['memory_percent'],
                            'memory_rss': info['memory_info'].rss if info['memory_info'] else 0,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory percent
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            print(f"Top consumers error: {e}")
            return []
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data when collection fails"""
        return {
            'ram': {
                'total': 0,
                'available': 0,
                'used': 0,
                'free': 0,
                'percent': 0,
                'cached': 0,
                'buffers': 0,
            },
            'swap': {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0,
            }
        }

