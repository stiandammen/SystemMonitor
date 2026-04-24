"""
Memory Data Collector
"""
from typing import Dict, Any, List, Optional


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
