"""
Data Collector Coordinator - Manages all data collection threads
Professional technician-grade system monitoring
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from utils.logger import get_logger, LogCategory, log_info, log_warning, log_error


class DataCollectorCoordinator(QObject):
    """
    Central coordinator for all data collection threads.
    Aggregates data from all collectors and emits unified signals.
    Runs in main thread but spawns separate collector threads.
    """

    # Unified signal emitted with all aggregated data
    data_ready = pyqtSignal(dict)

    # Signal for storage/partition updates (less frequent)
    storage_updated = pyqtSignal(list)

    # Signal for system info (static info, cached)
    system_info_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collectors = {}
        self._aggregated_data = {}
        self._last_storage_update = 0
        self._last_system_info_update = 0
        self._storage_interval = 5  # seconds
        self._system_info_interval = 30  # seconds

        # Debounce timer to limit UI updates
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._emit_data)

        self._pending_update = False

    def start(self):
        """Start all data collection threads"""
        log_info(LogCategory.COLLECTOR, "Starting DataCollectorCoordinator")

        # Import and create collectors
        from data.collector import (
            CPUCollectorThread,
            MemoryCollectorThread,
            DiskCollectorThread,
            NetworkCollectorThread,
            GPUCollectorThread,
            SystemInfoCollectorThread,
        )

        # CPU collector - high frequency
        self._collectors['cpu'] = CPUCollectorThread()
        self._collectors['cpu'].data_updated.connect(lambda d: self._on_collector_update('cpu', d))
        self._collectors['cpu'].start()

        # Memory collector - medium frequency
        self._collectors['memory'] = MemoryCollectorThread()
        self._collectors['memory'].data_updated.connect(lambda d: self._on_collector_update('memory', d))
        self._collectors['memory'].start()

        # Disk collector - lower frequency
        self._collectors['disk'] = DiskCollectorThread()
        self._collectors['disk'].data_updated.connect(lambda d: self._on_collector_update('disk', d))
        self._collectors['disk'].start()

        # Network collector - high frequency
        self._collectors['network'] = NetworkCollectorThread()
        self._collectors['network'].data_updated.connect(lambda d: self._on_collector_update('network', d))
        self._collectors['network'].start()

        # GPU collector - medium frequency
        self._collectors['gpu'] = GPUCollectorThread()
        self._collectors['gpu'].data_updated.connect(lambda d: self._on_collector_update('gpu', d))
        self._collectors['gpu'].start()

        # System info collector - low frequency (static data)
        self._collectors['system_info'] = SystemInfoCollectorThread()
        self._collectors['system_info'].data_updated.connect(self._on_system_info_update)
        self._collectors['system_info'].start()

        log_info(LogCategory.COLLECTOR, f"Started {len(self._collectors)} collector threads")

    def stop(self):
        """Stop all data collection threads"""
        log_info(LogCategory.COLLECTOR, "Stopping DataCollectorCoordinator")

        for name, collector in self._collectors.items():
            collector.stop()
            collector.wait(2000)  # Wait up to 2 seconds for thread to finish

        self._collectors.clear()

    def _on_collector_update(self, name: str, data: dict):
        """Handle updates from individual collectors"""
        self._aggregated_data[name] = data

        # Schedule debounced emit
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(50)  # 50ms debounce

    def _emit_data(self):
        """Emit aggregated data to UI (debounced)"""
        self._pending_update = False
        self.data_ready.emit(self._aggregated_data.copy())

    def _on_system_info_update(self, data: dict):
        """Handle system info updates"""
        self._aggregated_data['system_info'] = data
        self.system_info_updated.emit(data)

    def get_data(self) -> dict:
        """Get current aggregated data"""
        return self._aggregated_data.copy()


# Backwards compatibility alias
DataCollector = DataCollectorCoordinator