"""
Base View - Base class for all views
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from styles.theme import theme_manager
from core.signals import signal_bus


class BaseView(QWidget):
    """
    Base class for all views
    Provides common functionality and lifecycle hooks
    """
    
    view_activated = pyqtSignal()
    view_deactivated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup view UI - override in subclasses"""
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(16)
        self.setLayout(self._layout)
    
    def _connect_signals(self):
        """Connect to signal bus"""
        signal_bus.data_updated.connect(self._on_data_updated)
        signal_bus.theme_changed.connect(self._on_theme_changed)
    
    def on_enter(self):
        """Called when view becomes active"""
        self._is_active = True
        self.view_activated.emit()
    
    def on_leave(self):
        """Called when view becomes inactive"""
        self._is_active = False
        self.view_deactivated.emit()
    
    def _on_data_updated(self, data: dict):
        """Handle data update - override in subclasses"""
        pass
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change - override in subclasses"""
        pass
    
    def is_active(self) -> bool:
        """Check if view is currently active"""
        return self._is_active
