"""
System Monitor - Configuration
Application settings, colors, fonts, and constants with responsive defaults
"""
import json
import os
from systemmonitor.paths_ext import Path
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

    # Graph history buffer bounds (used with the History Length setting).
    # MAX keeps a single graph's paint cost bounded (~15-30ms at a 30fps budget).
    HISTORY_POINTS_MIN = 30
    HISTORY_POINTS_MAX = 600

    @staticmethod
    def history_window(duration_seconds, interval_ms, target_points: int = None):
        """Compute (max_points, stride) for a rolling graph buffer so it visually
        spans `duration_seconds` of data sampled every `interval_ms`, while never
        holding/painting more than `target_points` samples.

        Rather than simply clamping the buffer length (which would make long
        windows look identical to short ones once the raw point count exceeds
        the cap), every `stride`-th raw sample is kept. That bounds paint cost
        to `target_points` while still letting the graph cover the requested
        time span at a coarser resolution.
        """
        target = AppConfig.HISTORY_POINTS_MAX if target_points is None else target_points
        try:
            interval_s = max(float(interval_ms), 1.0) / 1000.0
            raw_points = max(1.0, float(duration_seconds) / interval_s)
        except (TypeError, ValueError, ZeroDivisionError):
            raw_points = float(target)
        stride = max(1, round(raw_points / target))
        max_points = max(AppConfig.HISTORY_POINTS_MIN, min(round(raw_points / stride), target))
        return max_points, stride


class FontConfig:
    """Font configuration - responsive font sizes"""

    FONT_FAMILY = AppConfig.FONT_FAMILY

    @staticmethod
    def get_font(size: int, bold: bool = False) -> QFont:
        return QFont(AppConfig.FONT_FAMILY, size, QFont.Weight.Bold if bold else QFont.Weight.Normal)


class SettingsManager:
    """Manages application settings with JSON persistence"""

    DEFAULT_SETTINGS = {
        # Localization
        'language': 'en',                   # 'en' or 'no'

        # Appearance
        'theme': 'cyber-cyan',
        'accent_color': '#10b981',
        'sidebar_collapsed': False,
        'ui_scale': 1.0,
        'home_screen_style': 'sidebar',     # 'sidebar' (classic) or 'launcher' (module grid start screen)

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
        'notification_method': 'system',  # 'system' (tray popups) or 'in_app' (in-app banner)

        # Units & display
        'temperature_unit': 'celsius',      # 'celsius' or 'fahrenheit'
        'network_speed_unit': 'mbps',       # 'mbps' (megabits) or 'mbytes' (MB/s)
        'decimal_places': 1,                # precision used for temperature/speed readouts

        # Features
        'show_gpu': True,
        'show_network': True,
        'show_processes': True,
        'hidden_views': [],   # view keys hidden from the sidebar, e.g. ["gpu"]

        # System
        'autostart': False,
        'minimize_to_tray': False,
        'start_minimized': False,
        'overlay_mode': False,
        'check_for_updates': True,

        # Export
        'export_format': 'csv',
        'export_directory': str(Path.home() / 'Documents'),

        # External monitoring
        'prometheus_enabled': False,
        'prometheus_port': 9090,

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
