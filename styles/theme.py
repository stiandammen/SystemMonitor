"""
Theme Management - Professional theme system with 4 distinctive themes
"""
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QObject, pyqtSignal


# Default colors (saved as reference)
DEFAULT_COLORS = {
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
}


class MidnightTheme:
    """OLED-friendly dark theme with true black backgrounds and teal accent"""
    # Backgrounds
    BG_PRIMARY = "#101920"       # Dark blue-black background
    BG_SECONDARY = "#0d1218"    # Darker for sidebar
    BG_CARD = "#151d28"         # Elevated surfaces
    BG_HOVER = "#1c2838"        # Hover states
    BG_INPUT = "#101920"        # Input fields
    BG_ACTIVE = "#0c997f"       # Active/selected

    # Text - white primary for contrast
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#707070"
    TEXT_DISABLED = "#505050"

    # Accents
    ACCENT_GREEN = "#0c997f"    # Primary teal accent
    ACCENT_GREEN_BRIGHT = "#0fb89a"
    ACCENT_BLUE = "#3b82f6"
    ACCENT_ORANGE = "#f97316"
    ACCENT_RED = "#ef4444"
    ACCENT_YELLOW = "#fbbf24"
    ACCENT_CYAN = "#22d3ee"
    ACCENT_PURPLE = "#a855f7"
    ACCENT_PINK = "#ec4899"

    # Status colors (for CPU temp, disk %, etc)
    STATUS_RED = "#ef4444"
    STATUS_ORANGE = "#f97316"
    STATUS_YELLOW = "#fbbf24"
    STATUS_GREEN = "#22c55e"

    # UI Elements
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2530"
    BORDER_FOCUS = "#0c997f"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#0c997f"
    CHART_FILL = "#0a1a20"
    CHART_LINE = "#0c997f"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(0, 0, 0, 0.7)"

    SUCCESS_BG = "#0a2015"
    WARNING_BG = "#201a0a"
    ERROR_BG = "#200a0a"
    INFO_BG = "#0a1520"


class CustomTheme:
    """Custom user theme - loaded from settings"""
    # These will be set dynamically
    BG_PRIMARY = "#101920"
    BG_SECONDARY = "#0d1218"
    BG_CARD = "#151d28"
    BG_HOVER = "#1c2838"
    BG_INPUT = "#101920"
    BG_ACTIVE = "#0c997f"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#707070"
    TEXT_DISABLED = "#505050"
    ACCENT_GREEN = "#0c997f"
    ACCENT_GREEN_BRIGHT = "#0fb89a"
    ACCENT_BLUE = "#3b82f6"
    ACCENT_ORANGE = "#f97316"
    ACCENT_RED = "#ef4444"
    ACCENT_YELLOW = "#fbbf24"
    ACCENT_CYAN = "#22d3ee"
    ACCENT_PURPLE = "#a855f7"
    ACCENT_PINK = "#ec4899"
    STATUS_RED = "#ef4444"
    STATUS_ORANGE = "#f97316"
    STATUS_YELLOW = "#fbbf24"
    STATUS_GREEN = "#22c55e"
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2530"
    BORDER_FOCUS = "#0c997f"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#0c997f"
    CHART_FILL = "#0a1a20"
    CHART_LINE = "#0c997f"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(0, 0, 0, 0.7)"
    SUCCESS_BG = "#0a2015"
    WARNING_BG = "#201a0a"
    ERROR_BG = "#200a0a"
    INFO_BG = "#0a1520"

    @classmethod
    def load_from_dict(cls, colors_dict):
        """Load colors from dictionary"""
        for key, value in colors_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

    @classmethod
    def save_to_dict(cls):
        """Save colors to dictionary"""
        return {key: getattr(cls, key) for key in DEFAULT_COLORS.keys()}


class CyberpunkTheme:
    """Neon cyberpunk theme with hot pink and cyan accents"""
    # Backgrounds - same base with neon accents
    BG_PRIMARY = "#101920"
    BG_SECONDARY = "#0d1218"
    BG_CARD = "#151d28"
    BG_HOVER = "#1c2838"
    BG_INPUT = "#101920"
    BG_ACTIVE = "#ff2d6a"

    # Text - pure white for stability
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#c0c0c0"
    TEXT_MUTED = "#808080"
    TEXT_DISABLED = "#505050"

    # Accents - vibrant neon
    ACCENT_GREEN = "#00ff9f"
    ACCENT_GREEN_BRIGHT = "#00ffaa"
    ACCENT_BLUE = "#00d4ff"
    ACCENT_ORANGE = "#ff6b35"
    ACCENT_RED = "#ff0055"
    ACCENT_YELLOW = "#ffdd00"
    ACCENT_CYAN = "#00ffff"
    ACCENT_PURPLE = "#bd93f9"
    ACCENT_PINK = "#ff2d6a"

    # Status colors
    STATUS_RED = "#ff0055"
    STATUS_ORANGE = "#ff6b35"
    STATUS_YELLOW = "#ffdd00"
    STATUS_GREEN = "#00ff9f"

    # UI Elements
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2530"
    BORDER_FOCUS = "#ff2d6a"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#ff2d6a"
    CHART_FILL = "#0a1a20"
    CHART_LINE = "#00ff9f"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(16, 25, 32, 0.9)"

    SUCCESS_BG = "#0a2015"
    WARNING_BG = "#201a0a"
    ERROR_BG = "#200a0a"
    INFO_BG = "#0a1520"


class NordicTheme:
    """Nordic inspired theme with soft muted blue accents"""
    # Backgrounds - same base
    BG_PRIMARY = "#101920"
    BG_SECONDARY = "#0d1218"
    BG_CARD = "#151d28"
    BG_HOVER = "#1c2838"
    BG_INPUT = "#101920"
    BG_ACTIVE = "#5d8aa8"

    # Text - pure white for stability
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0adb8"
    TEXT_MUTED = "#6b7a86"
    TEXT_DISABLED = "#4a5660"

    # Accents - muted steel blue
    ACCENT_GREEN = "#5d8aa8"
    ACCENT_GREEN_BRIGHT = "#7aa8c8"
    ACCENT_BLUE = "#4a7a9a"
    ACCENT_ORANGE = "#d08770"
    ACCENT_RED = "#bf5656"
    ACCENT_YELLOW = "#ebcb8b"
    ACCENT_CYAN = "#8fbcbb"
    ACCENT_PURPLE = "#b48ead"
    ACCENT_PINK = "#d4789c"

    # Status colors
    STATUS_RED = "#bf5656"
    STATUS_ORANGE = "#d08770"
    STATUS_YELLOW = "#ebcb8b"
    STATUS_GREEN = "#7cb342"

    # UI Elements
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2530"
    BORDER_FOCUS = "#5d8aa8"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#5d8aa8"
    CHART_FILL = "#0a1a20"
    CHART_LINE = "#5d8aa8"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(16, 25, 32, 0.9)"

    SUCCESS_BG = "#1e3328"
    WARNING_BG = "#332822"
    ERROR_BG = "#331a1a"
    INFO_BG = "#1e2833"


class EmberTheme:
    """Warm ember theme with orange and amber accents"""
    # Backgrounds - warm dark with blue tint
    BG_PRIMARY = "#101920"
    BG_SECONDARY = "#0d1218"
    BG_CARD = "#151d28"
    BG_HOVER = "#1c2838"
    BG_INPUT = "#101920"
    BG_ACTIVE = "#ffab00"

    # Text - warm white
    TEXT_PRIMARY = "#fff8f0"
    TEXT_SECONDARY = "#e0c8b0"
    TEXT_MUTED = "#9a8066"
    TEXT_DISABLED = "#665544"

    # Accents - warm amber and orange
    ACCENT_GREEN = "#7cb342"
    ACCENT_GREEN_BRIGHT = "#8bc34a"
    ACCENT_BLUE = "#5c9ece"
    ACCENT_ORANGE = "#ff9100"
    ACCENT_RED = "#ff5252"
    ACCENT_YELLOW = "#ffd740"
    ACCENT_CYAN = "#4dd0e1"
    ACCENT_PURPLE = "#ce93d8"
    ACCENT_PINK = "#f48fb1"

    # Status colors
    STATUS_RED = "#ff5252"
    STATUS_ORANGE = "#ff9100"
    STATUS_YELLOW = "#ffd740"
    STATUS_GREEN = "#7cb342"

    # UI Elements
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2530"
    BORDER_FOCUS = "#ffab00"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#ffab00"
    CHART_FILL = "#0a1a20"
    CHART_LINE = "#ff9100"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(16, 25, 32, 0.9)"

    SUCCESS_BG = "#1a2d14"
    WARNING_BG = "#2d2210"
    ERROR_BG = "#2d1414"
    INFO_BG = "#141a20"


class ThemeManager(QObject):
    """Manages application theme (singleton)"""
    theme_changed = pyqtSignal(str)  # Emits theme name

    _instance = None

    _themes = {
        "midnight": MidnightTheme,
        "custom": CustomTheme,
        "cyberpunk": CyberpunkTheme,
        "nordic": NordicTheme,
        "ember": EmberTheme,
    }

    _theme_names = {
        "midnight": "Midnight",
        "custom": "Custom",
        "cyberpunk": "Cyberpunk",
        "nordic": "Nordic",
        "ember": "Ember",
    }

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
        self._current_theme = "midnight"
        self._colors = MidnightTheme()

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def colors(self):
        return self._colors

    def get_available_themes(self) -> list:
        """Get list of available theme keys"""
        return list(self._themes.keys())

    def get_theme_display_name(self, theme_key: str) -> str:
        """Get human-readable theme name"""
        return self._theme_names.get(theme_key, theme_key.title())

    def load_custom_theme(self, colors_dict):
        """Load custom theme colors from dictionary"""
        CustomTheme.load_from_dict(colors_dict)

    def set_theme(self, theme_name: str):
        """Switch between themes"""
        if theme_name not in self._themes:
            theme_name = "midnight"

        if theme_name == self._current_theme:
            return

        old_theme = self._current_theme
        try:
            # Always create a fresh instance to avoid class attribute issues
            theme_class = self._themes[theme_name]
            self._current_theme = theme_name
            self._colors = theme_class()
            self.theme_changed.emit(theme_name)
        except Exception as e:
            print(f"Theme error: {e}")
            import traceback
            traceback.print_exc()
            # Roll back to previous theme if error
            if old_theme != theme_name:
                self._current_theme = old_theme
                self._colors = self._themes[old_theme]()
                self.theme_changed.emit(old_theme)

    def reset_to_default(self):
        """Reset custom theme to default colors"""
        CustomTheme.load_from_dict(DEFAULT_COLORS)
        # Always emit so UI can update even if not on custom theme
        self.theme_changed.emit("custom")

    def toggle_theme(self):
        """Toggle between dark and light"""
        new_theme = "light" if self._current_theme == "midnight" else "midnight"
        self.set_theme(new_theme)

    def get_stylesheet(self) -> str:
        """Generate global stylesheet based on current theme"""
        c = self._colors
        return f"""
        QMainWindow {{
            background-color: {c.BG_PRIMARY};
            color: {c.TEXT_PRIMARY};
            border: none;
        }}

        QWidget {{
            background-color: {c.BG_PRIMARY};
            color: {c.TEXT_PRIMARY};
        }}

        QFrame {{
            background-color: {c.BG_PRIMARY};
            color: {c.TEXT_PRIMARY};
            border: none;
        }}

        QLabel {{
            background-color: transparent;
            color: {c.TEXT_PRIMARY};
            border: none;
        }}

        QPushButton {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 16px;
            font-family: "Segoe UI", sans-serif;
            font-size: 13px;
        }}

        QPushButton:hover {{
            background-color: {c.BG_HOVER};
            border-color: {c.BORDER};
        }}

        QPushButton:pressed {{
            background-color: {c.ACCENT_GREEN};
            color: #ffffff;
            border-color: {c.ACCENT_GREEN};
        }}

        QPushButton:disabled {{
            background-color: {c.BG_SECONDARY};
            color: {c.TEXT_DISABLED};
            border-color: {c.BORDER};
        }}

        QLineEdit {{
            background-color: {c.BG_INPUT};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "Segoe UI", sans-serif;
            font-size: 13px;
        }}

        QLineEdit:focus {{
            border-color: {c.BORDER_FOCUS};
        }}

        QComboBox {{
            background-color: {c.BG_INPUT};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "Segoe UI", sans-serif;
            font-size: 13px;
        }}

        QComboBox:hover {{
            border-color: {c.BORDER_FOCUS};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            selection-background-color: {c.BG_HOVER};
        }}

        QScrollBar:vertical {{
            background-color: {c.BG_SECONDARY};
            width: 10px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {c.BORDER};
            border-radius: 5px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {c.TEXT_MUTED};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: {c.BG_SECONDARY};
            height: 10px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {c.BORDER};
            border-radius: 5px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {c.TEXT_MUTED};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        QTableWidget {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 8px;
            gridline-color: {c.BORDER};
        }}

        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {c.BORDER};
        }}

        QTableWidget::item:selected {{
            background-color: {c.BG_HOVER};
            color: {c.TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {c.BG_SECONDARY};
            color: {c.TEXT_SECONDARY};
            padding: 10px;
            border: none;
            border-bottom: 2px solid {c.BORDER};
            font-weight: bold;
        }}

        QHeaderView::section:hover {{
            background-color: {c.BG_HOVER};
        }}

        QTabWidget::pane {{
            border: 1px solid {c.BORDER};
            border-radius: 8px;
            background-color: {c.BG_CARD};
        }}

        QTabBar::tab {{
            background-color: {c.BG_SECONDARY};
            color: {c.TEXT_SECONDARY};
            padding: 10px 20px;
            border: none;
            border-bottom: 2px solid transparent;
        }}

        QTabBar::tab:selected {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border-bottom: 2px solid {c.ACCENT_GREEN};
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {c.BG_HOVER};
        }}

        QProgressBar {{
            background-color: {c.BG_SECONDARY};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {c.TEXT_PRIMARY};
        }}

        QProgressBar::chunk {{
            background-color: {c.ACCENT_GREEN};
            border-radius: 4px;
        }}

        QToolTip {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px;
        }}
        """


# Global theme manager instance
theme_manager = ThemeManager()
