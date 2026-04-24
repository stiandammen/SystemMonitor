"""
Data Collector - System data collection
"""
import time
from PyQt5.QtCore import QThread, pyqtSignal


class DataCollector(QThread):
    """Collects system data in background thread"""
    
    data_ready = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._data = {}
    
    def run(self):
        """Main collection loop"""
        self._running = True
        
        while self._running:
            try:
                self._collect_data()
                self.data_ready.emit(self._data.copy())
                time.sleep(1)  # Update every second
            except Exception as e:
                print(f"Data collection error: {e}")
                time.sleep(1)
    
    def _collect_data(self):
        """Collect all system data"""
        import psutil
        
        # CPU
        self._data['cpu'] = {
            'percent': psutil.cpu_percent(interval=0.1),
            'per_core': psutil.cpu_percent(percpu=True),
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
    
    def stop(self):
        """Stop data collection"""
        self._running = False
        self.wait(1000)
    
    def get_data(self):
        """Get current data"""
        return self._data.copy()
