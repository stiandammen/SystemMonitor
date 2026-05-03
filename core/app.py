"""
Application - Main application setup
"""
import sys
import os
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import with proper relative paths for Pylance
import styles.theme as theme_module
import config as config_module
import core.window as window_module
import core.signals as signals_module


class SystemMonitorApp:
    """Main application class"""
    
    def __init__(self):
        self._app: Optional[QApplication] = None
        self._window: Optional[window_module.MainWindow] = None
        self._data_collector: Optional[object] = None
    
    def run(self) -> int:
        """Run the application"""
        # Create Qt application
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("System Monitor")
        self._app.setApplicationVersion("2.0.0")
        
        # Enable high DPI scaling
        self._app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        self._app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # Load theme from settings
        theme = config_module.settings.get('theme', 'dark')
        theme_module.theme_manager.set_theme(theme)
        
        # Apply stylesheet
        self._app.setStyleSheet(theme_module.theme_manager.get_stylesheet())
        
        # Connect theme change signal
        signals_module.signal_bus.theme_changed.connect(self._on_theme_changed)
        
        # Create main window
        self._window = window_module.MainWindow()
        
        # Register views
        self._register_views()
        
        # Start data collector
        self._start_data_collector()
        
        # Show window
        self._window.show()
        
        # Set initial view
        self._window.set_active_view("overview")
        
        # Run application
        result = self._app.exec()
        
        # Stop data collector on exit
        self._stop_data_collector()
        
        return result
    
    def _start_data_collector(self) -> None:
        """Start the data collection thread"""
        import data.collector as collector_module
        self._data_collector = collector_module.DataCollector()
        self._data_collector.start()
    
    def _stop_data_collector(self) -> None:
        """Stop the data collection thread"""
        if self._data_collector is not None:
            self._data_collector.stop()
    
    def _register_views(self) -> None:
        """Register all views with the main window"""
        import views.overview as overview_module
        import views.cpu as cpu_module
        import views.gpu as gpu_module
        import views.network as network_module
        import views.memory as memory_module
        import views.disks as disks_module
        import views.processes as processes_module
        import views.settings as settings_view_module
        
        if self._window is None:
            return
        
        # Create and register views
        views_list = [
            ("overview", overview_module.OverviewView()),
            ("cpu", cpu_module.CPUView()),
            ("gpu", gpu_module.GPUView()),
            ("network", network_module.NetworkView()),
            ("memory", memory_module.MemoryView()),
            ("disks", disks_module.DisksView()),
            ("processes", processes_module.ProcessesView()),
            ("settings", settings_view_module.SettingsView()),
        ]
        
        for name, view in views_list:
            self._window.register_view(name, view)
    
    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change"""
        if self._app is not None:
            self._app.setStyleSheet(theme_module.theme_manager.get_stylesheet())
        config_module.settings.set('theme', theme_name)
