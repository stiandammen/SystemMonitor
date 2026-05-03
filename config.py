"""
System Monitor - Configuration
Application settings, colors, fonts, and constants
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtGui import QFont


class AppConfig:
    """Application configuration constants"""
    
    # Window settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 700
    
    # Sidebar
    SIDEBAR_WIDTH = 200
    SIDEBAR_COLLAPSED_WIDTH = 60
    
    # Title bar
    TITLE_BAR_HEIGHT = 44
    
    # Update intervals (milliseconds)
    UPDATE_INTERVAL_MS = 500  # Main update loop
    FAST_UPDATE_MS = 250      # CPU, GPU, RAM, Network
    MEDIUM_UPDATE_MS = 1000   # Processes
    SLOW_UPDATE_MS = 5000     # Metadata, system info
    
    # History settings
    HISTORY_DURATION_SECONDS = 300  # 5 minutes
    HISTORY_POINTS = 600  # 1 point per 500ms
    
    # Gauge sizes
    GAUGE_LARGE = 160
    GAUGE_MEDIUM = 140
    GAUGE_SMALL = 120
    
    # Graph sizes
    GRAPH_HEIGHT_SMALL = 80
    GRAPH_HEIGHT_MEDIUM = 160
    GRAPH_HEIGHT_LARGE = 240
    
    # Card styling
    CARD_RADIUS = 10
    CARD_PADDING = 16
    CARD_SPACING = 12
    
    # Font settings
    FONT_FAMILY = "Segoe UI"
    FONT_FALLBACK = ["SF Pro Display", "Helvetica Neue", "Arial", "sans-serif"]


class FontConfig:
    """Font configuration"""
    
    @staticmethod
    def get_font(size: int, bold: bool = False) -> QFont:
        """Get font with specified size and weight"""
        font = QFont(AppConfig.FONT_FAMILY, size)
        if bold:
            font.setBold(True)
        return font
    
    # Predefined fonts
    TITLE = get_font(20, True)
    SUBTITLE = get_font(16, True)
    HEADING = get_font(14, True)
    BODY = get_font(13)
    BODY_BOLD = get_font(13, True)
    SMALL = get_font(11)
    SMALL_BOLD = get_font(11, True)
    CAPTION = get_font(10)
    VALUE_LARGE = get_font(24, True)
    VALUE_MEDIUM = get_font(18, True)


class SettingsManager:
    """Manages application settings with JSON persistence"""
    
    DEFAULT_SETTINGS = {
        # Appearance
        'theme': 'dark',
        'accent_color': '#10b981',
        'sidebar_collapsed': False,
        
        # Performance
        'update_interval': 500,
        'history_duration': 300,
        'enable_animations': True,
        
        # Alerts
        'alerts_enabled': True,
        'alert_cpu_threshold': 80,
        'alert_memory_threshold': 85,
        'alert_disk_threshold': 90,
        'alert_temperature_threshold': 80,
        'alert_gpu_threshold': 85,
        
        # Features
        'show_gpu': True,
        'show_network': True,
        'show_processes': True,
        'decimal_places': 1,
        
        # System
        'autostart': False,
        'minimize_to_tray': False,
        'start_minimized': False,
        
        # Export
        'export_format': 'csv',
        'export_directory': str(Path.home() / 'Documents'),
    }
    
    def __init__(self):
        self._settings: Dict[str, Any] = {}
        self._config_path = self._get_config_path()
        self._load()
    
    def _get_config_path(self) -> Path:
        """Get configuration file path"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'SystemMonitor'
        else:  # Linux/Mac
            config_dir = Path.home() / '.config' / 'systemmonitor'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'settings.json'
    
    def _load(self):
        """Load settings from file"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._settings = {**self.DEFAULT_SETTINGS, **loaded}
            else:
                self._settings = self.DEFAULT_SETTINGS.copy()
                self._save()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self.DEFAULT_SETTINGS.copy()
    
    def _save(self):
        """Save settings to file"""
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set setting value and save"""
        self._settings[key] = value
        self._save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self._save()
    
    def update(self, settings: Dict[str, Any]):
        """Update multiple settings at once"""
        self._settings.update(settings)
        self._save()


# Global instances
settings = SettingsManager()
