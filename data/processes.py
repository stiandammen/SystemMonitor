"""
Process Data Collector
"""
from typing import Dict, Any, List, Optional


class ProcessCollector:
    """Collect process information"""
    
    def __init__(self):
        self._process_cache: Dict[int, Dict[str, Any]] = {}
    
    def collect(self) -> Dict[str, Any]:
        """Collect process data"""
        try:
            import psutil
            
            processes = []
            total_processes = 0
            total_threads = 0
            
            for proc in psutil.process_iter([
                'pid', 'name', 'username', 'status', 
                'cpu_percent', 'memory_percent', 'memory_info',
                'num_threads', 'create_time'
            ]):
                try:
                    info = proc.info
                    total_processes += 1
                    total_threads += info.get('num_threads', 0)
                    
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'username': info.get('username', 'N/A'),
                        'status': info.get('status', 'unknown'),
                        'cpu_percent': info.get('cpu_percent', 0.0) or 0.0,
                        'memory_percent': info.get('memory_percent', 0.0) or 0.0,
                        'memory_rss': info['memory_info'].rss if info.get('memory_info') else 0,
                        'threads': info.get('num_threads', 0),
                        'create_time': info.get('create_time', 0),
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'list': processes,
                'total_count': total_processes,
                'total_threads': total_threads,
            }
            
        except Exception as e:
            print(f"Process collect error: {e}")
            return {'list': [], 'total_count': 0, 'total_threads': 0}
    
    def get_process_details(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific process"""
        try:
            import psutil
            
            proc = psutil.Process(pid)
            
            with proc.oneshot():
                return {
                    'pid': pid,
                    'name': proc.name(),
                    'exe': proc.exe(),
                    'cwd': proc.cwd(),
                    'cmdline': proc.cmdline(),
                    'username': proc.username(),
                    'status': proc.status(),
                    'create_time': proc.create_time(),
                    'cpu_percent': proc.cpu_percent(),
                    'memory_percent': proc.memory_percent(),
                    'memory_info': proc.memory_info()._asdict(),
                    'num_threads': proc.num_threads(),
                    'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else None,
                    'io_counters': proc.io_counters()._asdict() if hasattr(proc, 'io_counters') else None,
                }
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID"""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except Exception as e:
            print(f"Kill process error: {e}")
            return False
