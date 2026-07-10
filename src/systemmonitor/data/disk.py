"""
Disk Data Collector
"""
import platform
from typing import Dict, Any, List


class DiskCollector:
    """Collect disk usage and I/O statistics"""
    
    def __init__(self):
        self._previous_io = None
        self._previous_time = 0
    
    def collect(self) -> Dict[str, Any]:
        """Collect current disk data"""
        try:
            import psutil
            import time
            
            # Get disk partitions
            partitions = self._get_partitions()
            
            # Get disk I/O
            io_stats = self._get_io_stats()
            
            return {
                'partitions': partitions,
                'io': io_stats,
                'total_read': io_stats.get('read_bytes', 0),
                'total_write': io_stats.get('write_bytes', 0),
            }
            
        except Exception as e:
            print(f"Disk collect error: {e}")
            return {'partitions': [], 'io': {}}
    
    def _get_partitions(self) -> List[Dict[str, Any]]:
        """Get disk partition information"""
        try:
            import psutil
            
            partitions = []
            disk_usage = psutil.disk_partitions(all=False)
            
            for part in disk_usage:
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
            
            return partitions
            
        except Exception as e:
            print(f"Partition error: {e}")
            return []
    
    def _get_io_stats(self) -> Dict[str, float]:
        """Get disk I/O statistics with rate calculation"""
        try:
            import psutil
            import time
            
            current_io = psutil.disk_io_counters()
            current_time = time.time()
            
            if self._previous_io is None:
                self._previous_io = current_io
                self._previous_time = current_time
                return {
                    'read_bytes': 0,
                    'write_bytes': 0,
                    'read_rate': 0,
                    'write_rate': 0,
                }
            
            # Calculate rates
            time_delta = current_time - self._previous_time
            if time_delta > 0:
                read_rate = (current_io.read_bytes - self._previous_io.read_bytes) / time_delta
                write_rate = (current_io.write_bytes - self._previous_io.write_bytes) / time_delta
            else:
                read_rate = 0
                write_rate = 0
            
            # Update previous
            self._previous_io = current_io
            self._previous_time = current_time
            
            return {
                'read_bytes': current_io.read_bytes,
                'write_bytes': current_io.write_bytes,
                'read_rate': max(0, read_rate),
                'write_rate': max(0, write_rate),
            }
            
        except Exception as e:
            print(f"IO stats error: {e}")
            return {
                'read_bytes': 0,
                'write_bytes': 0,
                'read_rate': 0,
                'write_rate': 0,
            }

