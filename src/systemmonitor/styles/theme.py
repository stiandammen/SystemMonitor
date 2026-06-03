"""
Theme Management - Professional theme system with glassmorphism and premium dark themes
"""
import re as _re
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QObject, pyqtSignal


def css_color_to_hex(color: str) -> str:
    """Convert a CSS rgba/rgb color string to #rrggbb for QColor compatibility.
    Hex colors and named colors are returned unchanged.
    """
    if not color or color.startswith('#'):
        return color or '#000000'
    m = _re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color)
    if m:
        return f'#{int(m.group(1)):02x}{int(m.group(2)):02x}{int(m.group(3)):02x}'
    return color


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




class CyberpunkTheme:
    """Neon cyberpunk theme — deep purple-black with hot pink primary accent"""
    # Backgrounds — deep purple-black (distinct from Midnight's blue-black)
    BG_PRIMARY = "#0d0015"
    BG_SECONDARY = "#160025"
    BG_CARD = "#1e1030"
    BG_HOVER = "#2a1550"
    BG_INPUT = "#0d0015"
    BG_ACTIVE = "#ff2d6a"

    # Text
    TEXT_PRIMARY = "#f0e6ff"
    TEXT_SECONDARY = "#b090d0"
    TEXT_MUTED = "#7050a0"
    TEXT_DISABLED = "#402060"

    # Primary accent — hot pink (iconic cyberpunk)
    ACCENT_GREEN = "#ff2d6a"
    ACCENT_GREEN_BRIGHT = "#ff5090"
    ACCENT_GREEN_DIM = "rgba(255, 45, 106, 0.15)"

    # Secondary accents
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
    BORDER = "#2d0e4a"
    BORDER_SUBTLE = "#1e0a33"
    BORDER_FOCUS = "#ff2d6a"
    GAUGE_BG = "#2a1050"
    GAUGE_FILL = "#ff2d6a"
    CHART_FILL = "rgba(255, 45, 106, 0.1)"
    CHART_LINE = "#ff2d6a"
    SHADOW = "rgba(0, 0, 0, 0.7)"
    OVERLAY = "rgba(13, 0, 21, 0.95)"

    SUCCESS_BG = "#0a2015"
    WARNING_BG = "#201a0a"
    ERROR_BG = "#200005"
    INFO_BG = "#0a0515"



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


class CyberCyanTheme:
    """Cyber-Cyan: dark navy with emerald-green accent"""
    BG_PRIMARY = "#0a0e17"
    BG_SECONDARY = "#0d1117"
    BG_CARD = "#161f2a"
    BG_HOVER = "#1c2535"
    BG_INPUT = "#0d1117"
    BG_ACTIVE = "#10b981"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8b949e"
    TEXT_MUTED = "#5a6370"
    TEXT_DISABLED = "#3a4350"
    ACCENT_GREEN = "#10b981"
    ACCENT_GREEN_BRIGHT = "#34d399"
    ACCENT_GREEN_DIM = "rgba(16, 185, 129, 0.15)"
    ACCENT_BLUE = "#00d4ff"
    ACCENT_ORANGE = "#f97316"
    ACCENT_RED = "#ef4444"
    ACCENT_YELLOW = "#fbbf24"
    ACCENT_CYAN = "#06b6d4"
    ACCENT_PURPLE = "#a371f7"
    ACCENT_PINK = "#ec4899"
    STATUS_RED = "#ef4444"
    STATUS_ORANGE = "#f97316"
    STATUS_YELLOW = "#fbbf24"
    STATUS_GREEN = "#10b981"
    BORDER = "#2a3a4a"
    BORDER_SUBTLE = "#1a2838"
    BORDER_FOCUS = "#10b981"
    GAUGE_BG = "#1c2838"
    GAUGE_FILL = "#10b981"
    CHART_FILL = "rgba(16, 185, 129, 0.1)"
    CHART_LINE = "#10b981"
    SHADOW = "rgba(0, 0, 0, 0.5)"
    OVERLAY = "rgba(13, 17, 23, 0.9)"
    SUCCESS_BG = "#0a2015"
    WARNING_BG = "#201a0a"
    ERROR_BG = "#200a0a"
    INFO_BG = "#0a1520"




class ThemeManager(QObject):
    """Manages application theme (singleton)"""
    theme_changed = pyqtSignal(str)  # Emits theme name

    _instance = None

    _themes = {
        "cyber-cyan": CyberCyanTheme,
        "premium": PremiumDarkTheme,
        "cyberpunk": CyberpunkTheme,
        "heimdal": HeimdalTheme,
    }

    _theme_names = {
        "cyber-cyan": "Cyber Cyan",
        "premium": "Premium Dark",
        "cyberpunk": "Cyberpunk",
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
        self._current_theme = "cyber-cyan"
        self._colors = CyberCyanTheme()

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

    def set_theme(self, theme_name: str):
        """Switch between themes"""
        if theme_name not in self._themes:
            theme_name = "cyber-cyan"

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

    def toggle_theme(self):
        """Toggle between cyber-cyan and premium"""
        new_theme = "premium" if self._current_theme == "cyber-cyan" else "cyber-cyan"
        self.set_theme(new_theme)

    def get_stylesheet(self) -> str:
        """Generate responsive global stylesheet based on current theme"""
        c = self._colors
        accent_dim = getattr(c, 'ACCENT_GREEN_DIM', 'rgba(16, 185, 129, 0.15)')
        glass_bg = getattr(c, 'GLASS_BG', c.BG_INPUT)
        glass_border = getattr(c, 'GLASS_BORDER', c.BORDER)
        accent_bright = getattr(c, 'ACCENT_GREEN_BRIGHT', c.ACCENT_GREEN)

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
            background-color: {accent_bright};
            color: #ffffff;
            border-color: {accent_bright};
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
            background-color: {c.ACCENT_GREEN_DIM};
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
            background-color: {c.ACCENT_GREEN_DIM};
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
            background-color: {c.BG_HOVER};
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
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c.ACCENT_GREEN}, stop:1 {accent_bright});
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
