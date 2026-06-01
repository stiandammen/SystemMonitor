"""
System Monitor - Configuration
Application settings, colors, fonts, and constants with responsive defaults
"""
import json
import os
from systemmonitor.pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtGui import QFont


class AppConfig:
    """Application configuration constants - responsive defaults"""

    # Window settings (these are minimums, window adapts to screen)
    WINDOW_MIN_WIDTH = 700
    WINDOW_MIN_HEIGHT = 500

    # Sidebar
    SIDEBAR_EXPANDED_WIDTH = 220
    SIDEBAR_COLLAPSED_WIDTH = 58

    # Title bar
    TITLE_BAR_HEIGHT = 40

    # Update intervals (milliseconds)
    UPDATE_INTERVAL_MS = 500
    FAST_UPDATE_MS = 250
    MEDIUM_UPDATE_MS = 1000
    SLOW_UPDATE_MS = 5000

    # History settings
    HISTORY_DURATION_SECONDS = 300
    HISTORY_POINTS = 600

    # Gauge sizes (base, will be scaled)
    GAUGE_LARGE = 160
    GAUGE_MEDIUM = 140
    GAUGE_SMALL = 120

    # Graph heights (base, will be scaled)
    GRAPH_HEIGHT_SMALL = 80
    GRAPH_HEIGHT_MEDIUM = 160
    GRAPH_HEIGHT_LARGE = 240

    # Card styling (base, will be scaled)
    CARD_RADIUS = 12
    CARD_PADDING = 16
    CARD_SPACING = 12

    # Font settings
    FONT_FAMILY = "Segoe UI"
    FONT_FALLBACK = ["Inter", "SF Pro Display", "Helvetica Neue", "Arial", "sans-serif"]

    # Responsive breakpoints (pixels)
    COMPACT_THRESHOLD = 1600
    MEDIUM_THRESHOLD = 2200

    # Overlay mode
    OVERLAY_MIN_WIDTH = 280
    OVERLAY_MIN_HEIGHT = 60


class FontConfig:
    """Font configuration - responsive font sizes"""

    FONT_FAMILY = AppConfig.FONT_FAMILY

    @staticmethod
    def get_font(size: int, bold: bool = False) -> QFont:
        return QFont(AppConfig.FONT_FAMILY, size, QFont.Weight.Bold if bold else QFont.Weight.Normal)


class SettingsManager:
    """Manages application settings with JSON persistence"""

    DEFAULT_SETTINGS = {
        # Appearance
        'theme': 'midnight',
        'accent_color': '#10b981',
        'sidebar_collapsed': False,
        'ui_scale': 1.0,

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
        'overlay_mode': False,

        # Export
        'export_format': 'csv',
        'export_directory': str(Path.home() / 'Documents'),

        # Custom theme (default colors)
        'custom_theme_colors': {
            "BG_PRIMARY": "#101920",
            "BG_SECONDARY": "#0d1218",
            "BG_CARD": "#151d28",
            "BG_HOVER": "#1c2838",
            "BG_INPUT": "#101920",
            "BG_ACTIVE": "#0c997f",
            "TEXT_PRIMARY": "#ffffff",
            "TEXT_SECONDARY": "#b0b0b0",
            "TEXT_MUTED": "#707070",
            "TEXT_DISABLED": "#505050",
            "ACCENT_GREEN": "#0c997f",
            "ACCENT_GREEN_BRIGHT": "#0fb89a",
            "ACCENT_BLUE": "#3b82f6",
            "ACCENT_ORANGE": "#f97316",
            "ACCENT_RED": "#ef4444",
            "ACCENT_YELLOW": "#fbbf24",
            "ACCENT_CYAN": "#22d3ee",
            "ACCENT_PURPLE": "#a855f7",
            "ACCENT_PINK": "#ec4899",
            "STATUS_RED": "#ef4444",
            "STATUS_ORANGE": "#f97316",
            "STATUS_YELLOW": "#fbbf24",
            "STATUS_GREEN": "#22c55e",
            "BORDER": "#2a3a4a",
            "BORDER_SUBTLE": "#1a2530",
            "BORDER_FOCUS": "#0c997f",
            "GAUGE_BG": "#1c2838",
            "GAUGE_FILL": "#0c997f",
            "CHART_FILL": "#0a1a20",
            "CHART_LINE": "#0c997f",
        },
    }

    def __init__(self):
        self._settings: Dict[str, Any] = {}
        self._config_path = self._get_config_path()
        self._load()

    def _get_config_path(self) -> Path:
        if os.name == 'nt':
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'SystemMonitor'
        else:
            config_dir = Path.home() / '.config' / 'systemmonitor'

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'settings.json'

    def _load(self):
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
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self._save()

    def get_all(self) -> Dict[str, Any]:
        return self._settings.copy()

    def reset_to_defaults(self):
        self._settings = self.DEFAULT_SETTINGS.copy()
        self._save()

    def update(self, settings: Dict[str, Any]):
        self._settings.update(settings)
        self._save()


# Global instances
settings = SettingsManager()
