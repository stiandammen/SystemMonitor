"""
Theme Management - Dark and Light themes
"""
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QObject, pyqtSignal


class DarkTheme:
    """Modern dark theme color palette"""
    # Backgrounds
    BG_PRIMARY = "#0a0e14"      # Deepest black
    BG_SECONDARY = "#111820"    # Sidebar
    BG_CARD = "#161f2a"         # Cards
    BG_HOVER = "#1e2936"        # Hover states
    BG_INPUT = "#0d1117"        # Input fields
    
    # Text
    TEXT_PRIMARY = "#f0f4f8"    # Main text
    TEXT_SECONDARY = "#94a3b8"  # Secondary text
    TEXT_MUTED = "#64748b"      # Labels, hints
    TEXT_DISABLED = "#475569"   # Disabled elements
    
    # Accents
    ACCENT_GREEN = "#10b981"    # Primary - success
    ACCENT_BLUE = "#3b82f6"     # Info
    ACCENT_ORANGE = "#f59e0b"   # Warning
    ACCENT_RED = "#ef4444"      # Error
    ACCENT_YELLOW = "#ffd740"   # Caution
    ACCENT_CYAN = "#06b6d4"     # Network download
    ACCENT_PURPLE = "#8b5cf6"   # Network upload
    ACCENT_PINK = "#ec4899"     # Extra
    
    # UI Elements
    BORDER = "#2a3441"
    BORDER_FOCUS = "#3b82f6"
    GAUGE_BG = "#1e2936"
    GAUGE_FILL = "#10b981"
    CHART_FILL = "#064e3b"      # Dark green fill
    CHART_LINE = "#10b981"
    SHADOW = "rgba(0, 0, 0, 0.4)"
    OVERLAY = "rgba(0, 0, 0, 0.7)"


class MidnightTheme:
    """OLED-friendly dark theme with true black backgrounds"""
    # Backgrounds
    BG_PRIMARY = "#000000"       # True black
    BG_SECONDARY = "#0a0a0a"    # Near black
    BG_CARD = "#111111"         # Dark gray
    BG_HOVER = "#1a1a1a"        # Lighter gray
    BG_INPUT = "#0a0a0a"        # Input fields

    # Text
    TEXT_PRIMARY = "#ffffff"    # Pure white
    TEXT_SECONDARY = "#b0b0b0"  # Light gray
    TEXT_MUTED = "#707070"      # Medium gray
    TEXT_DISABLED = "#505050"   # Darker gray

    # Accents
    ACCENT_GREEN = "#10b981"    # Primary - success
    ACCENT_BLUE = "#3b82f6"    # Info
    ACCENT_ORANGE = "#f59e0b"   # Warning
    ACCENT_RED = "#ef4444"      # Error
    ACCENT_YELLOW = "#ffd740"   # Caution
    ACCENT_CYAN = "#06b6d4"    # Network download
    ACCENT_PURPLE = "#8b5cf6"   # Network upload
    ACCENT_PINK = "#ec4899"     # Extra

    # UI Elements
    BORDER = "#2a2a2a"
    BORDER_FOCUS = "#3b82f6"
    GAUGE_BG = "#1a1a1a"
    GAUGE_FILL = "#10b981"
    CHART_FILL = "#064e3b"
    CHART_LINE = "#10b981"
    SHADOW = "rgba(0, 0, 0, 0.8)"
    OVERLAY = "rgba(0, 0, 0, 0.9)"


class OceanTheme:
    """Dark theme with blue ocean accents"""
    # Backgrounds
    BG_PRIMARY = "#0a1628"       # Deep ocean blue
    BG_SECONDARY = "#0f1f3a"    # Sidebar
    BG_CARD = "#142247"         # Cards
    BG_HOVER = "#1a2d5a"        # Hover states
    BG_INPUT = "#0a1628"        # Input fields

    # Text
    TEXT_PRIMARY = "#e8f0ff"    # Main text
    TEXT_SECONDARY = "#8899bb"  # Secondary text
    TEXT_MUTED = "#556688"      # Labels, hints
    TEXT_DISABLED = "#3d4d66"   # Disabled elements

    # Accents
    ACCENT_GREEN = "#06b6d4"    # Cyan accent
    ACCENT_BLUE = "#3b82f6"     # Info blue
    ACCENT_ORANGE = "#f59e0b"   # Warning
    ACCENT_RED = "#ef4444"      # Error
    ACCENT_YELLOW = "#ffd740"   # Caution
    ACCENT_CYAN = "#06b6d4"     # Network download
    ACCENT_PURPLE = "#8b5cf6"   # Network upload
    ACCENT_PINK = "#ec4899"     # Extra

    # UI Elements
    BORDER = "#1e3a5f"
    BORDER_FOCUS = "#3b82f6"
    GAUGE_BG = "#1a2d5a"
    GAUGE_FILL = "#06b6d4"
    CHART_FILL = "#164e63"
    CHART_LINE = "#06b6d4"
    SHADOW = "rgba(0, 0, 0, 0.4)"
    OVERLAY = "rgba(0, 0, 0, 0.7)"


class SunsetTheme:
    """Warm-toned dark theme with orange/purple accents"""
    # Backgrounds
    BG_PRIMARY = "#1a0f0f"       # Deep burgundy black
    BG_SECONDARY = "#251a1a"    # Sidebar
    BG_CARD = "#2d1f1f"         # Cards
    BG_HOVER = "#3d2929"        # Hover states
    BG_INPUT = "#1a0f0f"        # Input fields

    # Text
    TEXT_PRIMARY = "#fff0f0"    # Main text
    TEXT_SECONDARY = "#cc9999"  # Secondary text
    TEXT_MUTED = "#886666"      # Labels, hints
    TEXT_DISABLED = "#553d3d"   # Disabled elements

    # Accents
    ACCENT_GREEN = "#f59e0b"    # Orange accent
    ACCENT_BLUE = "#8b5cf6"     # Purple accent
    ACCENT_ORANGE = "#f97316"   # Warning/Orange
    ACCENT_RED = "#ef4444"      # Error
    ACCENT_YELLOW = "#fbbf24"   # Caution/Yellow
    ACCENT_CYAN = "#06b6d4"     # Cyan
    ACCENT_PURPLE = "#a855f7"   # Network upload purple
    ACCENT_PINK = "#ec4899"     # Extra

    # UI Elements
    BORDER = "#3d2929"
    BORDER_FOCUS = "#f59e0b"
    GAUGE_BG = "#3d2929"
    GAUGE_FILL = "#f59e0b"
    CHART_FILL = "#78350f"
    CHART_LINE = "#f59e0b"
    SHADOW = "rgba(0, 0, 0, 0.4)"
    OVERLAY = "rgba(0, 0, 0, 0.7)"


class LightTheme:
    """Modern light theme color palette"""
    # Backgrounds
    BG_PRIMARY = "#f5f7fb"      # Light gray background
    BG_SECONDARY = "#e2e8f0"    # Sidebar
    BG_CARD = "#ffffff"         # Cards
    BG_HOVER = "#f1f5f9"        # Hover states
    BG_INPUT = "#ffffff"        # Input fields

    # Text
    TEXT_PRIMARY = "#0f172a"    # Main text
    TEXT_SECONDARY = "#475569"  # Secondary text
    TEXT_MUTED = "#64748b"      # Labels, hints
    TEXT_DISABLED = "#94a3b8"   # Disabled elements

    # Accents
    ACCENT_GREEN = "#059669"    # Primary - success
    ACCENT_BLUE = "#2563eb"     # Info
    ACCENT_ORANGE = "#d97706"   # Warning
    ACCENT_RED = "#dc2626"      # Error
    ACCENT_YELLOW = "#ca8a04"   # Caution
    ACCENT_CYAN = "#0891b2"     # Network download
    ACCENT_PURPLE = "#7c3aed"   # Network upload
    ACCENT_PINK = "#db2777"     # Extra

    # UI Elements
    BORDER = "#d1d5db"
    BORDER_FOCUS = "#3b82f6"
    GAUGE_BG = "#e2e8f0"
    GAUGE_FILL = "#059669"
    CHART_FILL = "#d1fae5"      # Light green fill
    CHART_LINE = "#059669"
    SHADOW = "rgba(0, 0, 0, 0.1)"
    OVERLAY = "rgba(0, 0, 0, 0.5)"


class ThemeManager(QObject):
    """Manages application theme (singleton)"""
    theme_changed = pyqtSignal(str)  # Emits theme name

    _instance = None

    _themes = {
        "dark": DarkTheme,
        "midnight": MidnightTheme,
        "ocean": OceanTheme,
        "sunset": SunsetTheme,
        "light": LightTheme,
    }

    _theme_names = {
        "dark": "Dark",
        "midnight": "Midnight (OLED)",
        "ocean": "Ocean",
        "sunset": "Sunset",
        "light": "Light",
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
        self._current_theme = "dark"
        self._colors = DarkTheme

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def colors(self):
        return self._colors

    def get_available_themes(self) -> list:
        """Get list of available theme names"""
        return list(self._themes.keys())

    def get_theme_display_name(self, theme_key: str) -> str:
        """Get human-readable theme name"""
        return self._theme_names.get(theme_key, theme_key.title())

    def set_theme(self, theme_name: str):
        """Switch between themes"""
        if theme_name not in self._themes:
            theme_name = "dark"

        if theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        self._colors = self._themes[theme_name]

        self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        """Toggle between dark and light"""
        new_theme = "light" if self._current_theme == "dark" else "dark"
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
            border-radius: 8px;
            padding: 8px 16px;
            font-family: "Segoe UI", sans-serif;
            font-size: 13px;
        }}
        
        QPushButton:hover {{
            background-color: {c.BG_HOVER};
            border-color: {c.BORDER_FOCUS};
        }}
        
        QPushButton:pressed {{
            background-color: {c.ACCENT_GREEN};
            color: #000000;
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
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c.BORDER};
            border-radius: 6px;
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
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c.BORDER};
            border-radius: 6px;
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
