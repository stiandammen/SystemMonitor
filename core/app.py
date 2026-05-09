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
        self._app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        
        # Load theme from settings
        theme = config_module.settings.get('theme', 'midnight')
        theme_module.theme_manager.set_theme(theme)

        # Load custom theme colors if custom theme is selected
        if theme == 'custom':
            custom_colors = config_module.settings.get('custom_theme_colors', {})
            if custom_colors:
                theme_module.theme_manager.load_custom_theme(custom_colors)

        # Apply stylesheet
        self._app.setStyleSheet(theme_module.theme_manager.get_stylesheet())
        
        # Connect theme change signal
        signals_module.signal_bus.theme_changed.connect(self._on_theme_changed)
        
        # Create main window
        self._window = window_module.MainWindow()

        # Start data collector
        self._start_data_collector()
        
        # Show window
        self._window.show()

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

    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change"""
        if self._app is not None:
            self._app.setStyleSheet(theme_module.theme_manager.get_stylesheet())
        config_module.settings.set('theme', theme_name)
