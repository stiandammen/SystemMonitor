"""
Theme Management - Professional theme system with glassmorphism and premium dark themes
"""
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QObject, pyqtSignal


# Premium Glassmorphism Dark Theme Colors
PREMIUM_DARK = {
    # Backgrounds - Deep dark base
    "BG_PRIMARY": "#080b10",
    "BG_SECONDARY": "#0d1117",
    "BG_CARD": "rgba(22, 27, 34, 0.75)",
    "BG_CARD_SOLID": "#161b22",
    "BG_HOVER": "rgba(33, 38, 45, 0.8)",
    "BG_INPUT": "#0d1117",

    # Glass effects
    "GLASS_BG": "rgba(13, 17, 23, 0.6)",
    "GLASS_BORDER": "rgba(48, 54, 61, 0.6)",
    "GLASS_SHADOW": "rgba(0, 0, 0, 0.4)",

    # Green glow - signature accent
    "ACCENT_GREEN": "#10b981",
    "ACCENT_GREEN_DIM": "rgba(16, 185, 129, 0.15)",
    "ACCENT_GREEN_GLOW": "rgba(16, 185, 129, 0.4)",
    "ACCENT_GREEN_BRIGHT": "#34d399",
    "ACCENT_GREEN_PULSE": "rgba(16, 185, 129, 0.6)",

    # Text
    "TEXT_PRIMARY": "#f0f6fc",
    "TEXT_SECONDARY": "#8b949e",
    "TEXT_MUTED": "#484f58",
    "TEXT_DISABLED": "#30363d",

    # Accent colors
    "ACCENT_BLUE": "#58a6ff",
    "ACCENT_ORANGE": "#f0883e",
    "ACCENT_RED": "#f85149",
    "ACCENT_YELLOW": "#d29922",
    "ACCENT_CYAN": "#39c5cf",
    "ACCENT_PURPLE": "#a371f7",
    "ACCENT_PINK": "#db61a2",

    # Status colors
    "STATUS_RED": "#f85149",
    "STATUS_ORANGE": "#f0883e",
    "STATUS_YELLOW": "#d29922",
    "STATUS_GREEN": "#3fb950",

    # Borders
    "BORDER": "rgba(48, 54, 61, 0.8)",
    "BORDER_SUBTLE": "rgba(48, 54, 61, 0.4)",
    "BORDER_GLOW": "rgba(16, 185, 129, 0.3)",

    # UI Elements
    "GAUGE_BG": "rgba(33, 38, 45, 0.6)",
    "GAUGE_FILL": "#10b981",
    "CHART_FILL": "rgba(16, 185, 129, 0.1)",
    "CHART_LINE": "#10b981",
    "CHART_GRID": "rgba(48, 54, 61, 0.4)",

    # Shadows & overlays
    "SHADOW": "rgba(0, 0, 0, 0.5)",
    "GLOW": "0 0 20px rgba(16, 185, 129, 0.15)",
    "GLOW_STRONG": "0 0 30px rgba(16, 185, 129, 0.25)",

    # Status backgrounds
    "SUCCESS_BG": "rgba(63, 185, 80, 0.1)",
    "WARNING_BG": "rgba(210, 153, 34, 0.1)",
    "ERROR_BG": "rgba(248, 81, 73, 0.1)",
    "INFO_BG": "rgba(88, 166, 255, 0.1)",
}


# Default colors (legacy compatibility)
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


class PremiumDarkTheme:
    """Premium glassmorphism dark theme with green glow effects"""

    # Backgrounds - Deep dark base
    BG_PRIMARY = "#080b10"
    BG_SECONDARY = "#0d1117"
    BG_CARD = "rgba(22, 27, 34, 0.75)"
    BG_CARD_SOLID = "#161b22"
    BG_HOVER = "rgba(33, 38, 45, 0.8)"
    BG_INPUT = "#0d1117"
    BG_ACTIVE = "#10b981"

    # Glass effects
    GLASS_BG = "rgba(13, 17, 23, 0.6)"
    GLASS_BORDER = "rgba(48, 54, 61, 0.6)"
    GLASS_SHADOW = "rgba(0, 0, 0, 0.4)"

    # Green glow - signature accent
    ACCENT_GREEN = "#10b981"
    ACCENT_GREEN_DIM = "rgba(16, 185, 129, 0.15)"
    ACCENT_GREEN_GLOW = "rgba(16, 185, 129, 0.4)"
    ACCENT_GREEN_BRIGHT = "#34d399"
    ACCENT_GREEN_PULSE = "rgba(16, 185, 129, 0.6)"

    # Text
    TEXT_PRIMARY = "#f0f6fc"
    TEXT_SECONDARY = "#8b949e"
    TEXT_MUTED = "#484f58"
    TEXT_DISABLED = "#30363d"

    # Accent colors
    ACCENT_BLUE = "#58a6ff"
    ACCENT_ORANGE = "#f0883e"
    ACCENT_RED = "#f85149"
    ACCENT_YELLOW = "#d29922"
    ACCENT_CYAN = "#39c5cf"
    ACCENT_PURPLE = "#a371f7"
    ACCENT_PINK = "#db61a2"

    # Status colors
    STATUS_RED = "#f85149"
    STATUS_ORANGE = "#f0883e"
    STATUS_YELLOW = "#d29922"
    STATUS_GREEN = "#3fb950"

    # Borders
    BORDER = "rgba(48, 54, 61, 0.8)"
    BORDER_SUBTLE = "rgba(48, 54, 61, 0.4)"
    BORDER_FOCUS = "#10b981"
    BORDER_GLOW = "rgba(16, 185, 129, 0.3)"

    # UI Elements
    GAUGE_BG = "rgba(33, 38, 45, 0.6)"
    GAUGE_FILL = "#10b981"
    CHART_FILL = "rgba(16, 185, 129, 0.1)"
    CHART_LINE = "#10b981"
    CHART_GRID = "rgba(48, 54, 61, 0.4)"

    # Shadows & overlays
    SHADOW = "rgba(0, 0, 0, 0.5)"
    GLOW = "0 0 20px rgba(16, 185, 129, 0.15)"
    GLOW_STRONG = "0 0 30px rgba(16, 185, 129, 0.25)"

    # Status backgrounds
    SUCCESS_BG = "rgba(63, 185, 80, 0.1)"
    WARNING_BG = "rgba(210, 153, 34, 0.1)"
    ERROR_BG = "rgba(248, 81, 73, 0.1)"
    INFO_BG = "rgba(88, 166, 255, 0.1)"


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


class HeimdalTheme:
    """Heimdal Security-inspired deep navy blue enterprise theme"""

    # Backgrounds
    BG_PRIMARY = "#12152A"
    BG_SECONDARY = "#1A1E35"
    BG_CARD = "rgba(30, 35, 64, 0.85)"
    BG_CARD_SOLID = "#1E2340"
    BG_HOVER = "#252A47"
    BG_INPUT = "#1A1E35"
    BG_ACTIVE = "#4A6CF7"

    # Glass effects
    GLASS_BG = "rgba(26, 30, 53, 0.7)"
    GLASS_BORDER = "rgba(74, 108, 247, 0.25)"
    GLASS_SHADOW = "rgba(0, 0, 0, 0.5)"

    # Primary accent — Heimdal blue
    ACCENT_GREEN = "#4A6CF7"
    ACCENT_GREEN_DIM = "rgba(74, 108, 247, 0.15)"
    ACCENT_GREEN_GLOW = "rgba(74, 108, 247, 0.4)"
    ACCENT_GREEN_BRIGHT = "#6B8BF9"
    ACCENT_GREEN_PULSE = "rgba(74, 108, 247, 0.6)"

    # Text
    TEXT_PRIMARY = "#E8ECFF"
    TEXT_SECONDARY = "#8A92B2"
    TEXT_MUTED = "#525A7A"
    TEXT_DISABLED = "#2E3356"

    # Secondary accents
    ACCENT_BLUE = "#00D4FF"
    ACCENT_ORANGE = "#FF6B35"
    ACCENT_RED = "#FF4757"
    ACCENT_YELLOW = "#FFB830"
    ACCENT_CYAN = "#00D4FF"
    ACCENT_PURPLE = "#7B5CF0"
    ACCENT_PINK = "#FF4FCE"

    # Status colors
    STATUS_RED = "#FF4757"
    STATUS_ORANGE = "#FF6B35"
    STATUS_YELLOW = "#FFB830"
    STATUS_GREEN = "#00E096"

    # Borders
    BORDER = "rgba(74, 108, 247, 0.2)"
    BORDER_SUBTLE = "rgba(74, 108, 247, 0.1)"
    BORDER_FOCUS = "#4A6CF7"
    BORDER_GLOW = "rgba(74, 108, 247, 0.4)"

    # UI Elements
    GAUGE_BG = "rgba(255, 255, 255, 0.06)"
    GAUGE_FILL = "#4A6CF7"
    CHART_FILL = "rgba(74, 108, 247, 0.15)"
    CHART_LINE = "#4A6CF7"
    CHART_GRID = "rgba(255, 255, 255, 0.05)"

    # Shadows & overlays
    SHADOW = "rgba(0, 0, 0, 0.6)"
    GLOW = "0 0 20px rgba(74, 108, 247, 0.2)"
    GLOW_STRONG = "0 0 30px rgba(74, 108, 247, 0.35)"

    # Status backgrounds
    SUCCESS_BG = "rgba(0, 224, 150, 0.1)"
    WARNING_BG = "rgba(255, 107, 53, 0.1)"
    ERROR_BG = "rgba(255, 71, 87, 0.1)"
    INFO_BG = "rgba(74, 108, 247, 0.1)"


class ThemeManager(QObject):
    """Manages application theme (singleton)"""
    theme_changed = pyqtSignal(str)  # Emits theme name

    _instance = None

    _themes = {
        "premium": PremiumDarkTheme,
        "midnight": MidnightTheme,
        "custom": CustomTheme,
        "cyberpunk": CyberpunkTheme,
        "nordic": NordicTheme,
        "ember": EmberTheme,
        "heimdal": HeimdalTheme,
    }

    _theme_names = {
        "premium": "Premium Dark",
        "midnight": "Midnight",
        "custom": "Custom",
        "cyberpunk": "Cyberpunk",
        "nordic": "Nordic",
        "ember": "Ember",
        "heimdal": "Heimdal Security",
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
        self._current_theme = "heimdal"
        self._colors = HeimdalTheme()

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
        """Generate responsive global stylesheet based on current theme"""
        c = self._colors
        accent_dim = getattr(c, 'ACCENT_GREEN_DIM', 'rgba(16, 185, 129, 0.15)')
        glass_bg = getattr(c, 'GLASS_BG', 'rgba(13, 17, 23, 0.6)')
        glass_border = getattr(c, 'GLASS_BORDER', 'rgba(48, 54, 61, 0.6)')

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
            background-color: {accent_dim};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 16px;
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 12px;
        }}

        QPushButton:hover {{
            background-color: {c.ACCENT_GREEN};
            border-color: {c.ACCENT_GREEN};
        }}

        QPushButton:pressed {{
            background-color: {getattr(c, 'ACCENT_GREEN_BRIGHT', '#34d399')};
            color: #ffffff;
            border-color: {getattr(c, 'ACCENT_GREEN_BRIGHT', '#34d399')};
        }}

        QPushButton:disabled {{
            background-color: {c.BG_SECONDARY};
            color: {c.TEXT_DISABLED};
            border-color: {c.BORDER};
        }}

        QLineEdit {{
            background-color: {glass_bg};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {glass_border};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 12px;
        }}

        QLineEdit:focus {{
            border-color: {c.ACCENT_GREEN};
        }}

        QComboBox {{
            background-color: {glass_bg};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {glass_border};
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 12px;
        }}

        QComboBox:hover {{
            border-color: {c.ACCENT_GREEN};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            selection-background-color: {c.BG_HOVER};
        }}

        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollBar:vertical {{
            background-color: {c.BG_SECONDARY};
            width: 6px;
            border-radius: 3px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background-color: rgba(74, 108, 247, 0.3);
            border-radius: 3px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {c.ACCENT_GREEN};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: {c.BG_SECONDARY};
            height: 6px;
            border-radius: 3px;
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: rgba(74, 108, 247, 0.3);
            border-radius: 3px;
            min-width: 30px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {c.ACCENT_GREEN};
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
            padding: 10px;
            border-bottom: 1px solid {c.BORDER};
        }}

        QTableWidget::item:hover {{
            background-color: rgba(74, 108, 247, 0.08);
        }}

        QTableWidget::item:selected {{
            background-color: {c.BG_HOVER};
            color: {c.TEXT_PRIMARY};
        }}

        QHeaderView::section {{
            background-color: {c.BG_PRIMARY};
            color: {c.TEXT_SECONDARY};
            padding: 10px;
            border: none;
            border-bottom: 2px solid {c.BORDER};
            font-weight: 600;
            font-size: 11px;
            letter-spacing: 0.5px;
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
            color: {c.ACCENT_GREEN};
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
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c.ACCENT_GREEN}, stop:1 {c.ACCENT_PURPLE});
            border-radius: 4px;
        }}

        QToolTip {{
            background-color: {c.BG_CARD};
            color: {c.TEXT_PRIMARY};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px;
            font-family: "Segoe UI", sans-serif;
        }}

        QSplitter::handle {{
            background-color: {c.BORDER};
            width: 2px;
            height: 2px;
        }}

        QSplitter::handle:hover {{
            background-color: {c.ACCENT_GREEN};
        }}
        """


# Global theme manager instance
theme_manager = ThemeManager()
