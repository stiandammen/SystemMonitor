"""
Signal Bus - Central communication system
Singleton pattern for cross-component communication
"""
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any, Optional


class SignalBus(QObject):
    """
    Central signal bus for application-wide communication.
    Uses singleton pattern to ensure single instance.
    """
    
    # Data signals
    data_updated = pyqtSignal(dict)           # Emitted when new system data is available
    processes_updated = pyqtSignal(list)      # Emitted when process list is updated
    history_updated = pyqtSignal(str, list)   # Emitted when history buffer updates (metric_name, data)
    
    # Alert signals
    alert_triggered = pyqtSignal(dict)        # Emitted when alert threshold is crossed
    alert_cleared = pyqtSignal(str)           # Emitted when alert is cleared (alert_id)
    
    # UI signals
    theme_changed = pyqtSignal(str)           # Emitted when theme changes (theme_name)
    view_changed = pyqtSignal(str)            # Emitted when view changes (view_name)
    setting_changed = pyqtSignal(str, object) # Emitted when setting changes (key, value)
    
    # Window signals
    window_resized = pyqtSignal(int, int)     # Emitted when window resizes (width, height)
    window_moved = pyqtSignal(int, int)       # Emitted when window moves (x, y)
    
    # Export signals
    export_requested = pyqtSignal(str, str)   # Emitted when export is requested (format, path)
    export_completed = pyqtSignal(bool, str)  # Emitted when export completes (success, message)
    
    # Process signals
    process_killed = pyqtSignal(int)          # Emitted when process is killed (pid)
    process_selected = pyqtSignal(int)        # Emitted when process is selected (pid)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._alert_history: List[Dict[str, Any]] = []
        self._max_alert_history = 100
    
    def emit_data(self, data: Dict[str, Any]):
        """Emit system data update"""
        self.data_updated.emit(data)
    
    def emit_processes(self, processes: List[Dict[str, Any]]):
        """Emit process list update"""
        self.processes_updated.emit(processes)
    
    def emit_alert(self, alert: Dict[str, Any]):
        """Emit alert and store in history"""
        self._alert_history.append(alert)
        # Trim history if too long
        if len(self._alert_history) > self._max_alert_history:
            self._alert_history = self._alert_history[-self._max_alert_history:]
        self.alert_triggered.emit(alert)
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self._alert_history.copy()
    
    def clear_alert_history(self):
        """Clear alert history"""
        self._alert_history.clear()


# Global signal bus instance
signal_bus = SignalBus()
