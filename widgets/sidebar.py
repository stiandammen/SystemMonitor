"""
Nexus Monitor - Premium Sidebar Navigation Widget
Modern enterprise-grade design with dark theme
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPainter, QLinearGradient, QColor
import qtawesome as qta
from typing import Optional, Dict

from styles.theme import theme_manager
from scaler import S, ScaleMixin


# Navigation structure with sections
NAV_STRUCTURE = {
    "main": {
        "title": None,
        "items": [
            {"key": "overview", "label": "Dashboard", "icon": "mdi.view-dashboard", "accent": "#00ab84"},
            {"key": "performance", "label": "Performance", "icon": "mdi.gauge", "accent": "#00ab84"},
            {"key": "cpu", "label": "Processor", "icon": "ph.cpu", "accent": "#3b82f6"},
            {"key": "gpu", "label": "Graphics", "icon": "ph.monitor", "accent": "#ec4899"},
            {"key": "network", "label": "Network", "icon": "ph.wifi-high", "accent": "#06b6d4"},
            {"key": "memory", "label": "Memory", "icon": "mdi.memory", "accent": "#8b5cf6"},
            {"key": "disks", "label": "Storage", "icon": "fa5s.database", "accent": "#f59e0b"},
        ]
    },
    "process": {
        "title": "PROCESS MANAGEMENT",
        "items": [
            {"key": "processes", "label": "Processes", "icon": "ph.list", "accent": "#f97316"},
            {"key": "services", "label": "Services", "icon": "fa5s.cogs", "accent": "#64748b"},
        ]
    },
    "tools": {
        "title": "TERMINAL & TOOLS",
        "items": [
            {"key": "cmd", "label": "Terminal", "icon": "fa5s.terminal", "accent": "#10b981"},
            {"key": "alerts", "label": "Alerts", "icon": "ph.bell", "accent": "#ef4444"},
            {"key": "settings", "label": "Settings", "icon": "ph.gear", "accent": "#94a3b8"},
        ]
    }
}


class PremiumNavItem(QPushButton, ScaleMixin):
    """Premium navigation item with glow and gradient effects"""

    clicked_with_name = pyqtSignal(str)

    def __init__(self, key: str, label: str, icon_name: str,
                 accent: str = "#00ab84", parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self._icon_name = icon_name
        self._accent = accent
        self._is_active = False
        self._is_hovered = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(S.px(48))
        self.setMinimumWidth(S.px(280))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        font = S.font("Segoe UI", 13)
        self.setFont(font)

        self._setup_icon()
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.clicked.connect(lambda: self.clicked_with_name.emit(key))
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.scale_connect()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def on_scale_changed(self, factor: float):
        self._apply_style()
        self._setup_icon()

    def _setup_icon(self):
        """Setup premium icon from qtawesome"""
        try:
            normal_color = QColor("#64748b")
            active_color = QColor(self._accent)
            icon = qta.icon(
                self._icon_name,
                color=normal_color,
                color_active=active_color
            )
            self.setIcon(icon)
            self.setIconSize(QSize(S.px(24), S.px(24)))
            self.setText(f"  {self._label}")
        except Exception:
            self.setText(f"  {self._label}")

    def _apply_style(self):
        """Apply premium navigation item style"""
        c = theme_manager.colors
        accent = QColor(self._accent)

        # Active background with gradient mix
        active_bg = f"""
            background-color: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {self._accent}22,
                stop: 1 {self._accent}11
            );
        """

        hover_bg = f"""
            background-color: {c.BG_HOVER};
        """

        normal_bg = "background-color: transparent;"

        active_border = f"border-left: {S.px(3)}px solid {self._accent};"
        normal_border = "border-left: 3px solid transparent;"

        self.setStyleSheet(f"""
            QPushButton {{
                {normal_bg}
                color: {c.TEXT_SECONDARY};
                border: none;
                {normal_border}
                padding: {S.px(14)}px {S.px(18)}px;
                text-align: left;
                border-radius: {S.px(8)}px;
                font-family: "Segoe UI", sans-serif;
                font-size: {S.px(14)}px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {c.TEXT_PRIMARY};
            }}

            QPushButton:checked {{
                {active_bg}
                color: {self._accent};
                {active_border}
                font-weight: 600;
            }}
        """)

    def set_active(self, active: bool):
        """Set active state with premium effect"""
        self._is_active = active
        self.setChecked(active)
        self._update_icon()
        self._apply_style()

    def _update_icon(self):
        """Update icon color based on state"""
        try:
            color = self._accent if self._is_active else "#64748b"
            icon = qta.icon(self._icon_name, color=color, color_active=self._accent)
            self.setIcon(icon)
        except Exception:
            pass


class PremiumSidebar(QFrame, ScaleMixin):
    """Premium enterprise sidebar navigation"""

    view_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: Dict[str, PremiumNavItem] = {}
        self._current_view: str = ""
        self._collapsed = False
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.scale_connect()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self._apply_theme()
        self.update()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply theme when colors change"""
        self._apply_theme()
        # Re-style all nav items
        for item in self._items.values():
            item._apply_style()

    def _setup_ui(self):
        """Setup premium sidebar UI"""
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Premium Header
        self._setup_header()

        # Navigation area
        nav_scroll = QWidget()
        nav_scroll.setStyleSheet(f"background-color: {theme_manager.colors.BG_CARD}; border: none;")
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(12, 8, 12, 8)
        nav_layout.setSpacing(6)
        nav_scroll.setLayout(nav_layout)

        # Build navigation sections
        for section_key, section_data in NAV_STRUCTURE.items():
            title = section_data.get("title")
            if title:
                section_label = QLabel(title)
                section_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
                section_label.setStyleSheet(f"""
                    color: {theme_manager.colors.TEXT_MUTED};
                    letter-spacing: 1.5px;
                    padding: 20px 16px 10px 16px;
                """)
                nav_layout.addWidget(section_label)

            for item_data in section_data["items"]:
                item = PremiumNavItem(
                    key=item_data["key"],
                    label=item_data["label"],
                    icon_name=item_data["icon"],
                    accent=item_data["accent"]
                )
                item.clicked_with_name.connect(self._on_item_clicked)
                nav_layout.addWidget(item)
                self._items[item_data["key"]] = item

        layout.addWidget(nav_scroll, stretch=1)

        # Premium Footer
        self._setup_footer()

    def _setup_header(self):
        """Setup premium branding header"""
        c = theme_manager.colors

        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: 0px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        header.setLayout(layout)

        # Premium icon container
        icon_container = QFrame()
        icon_container.setFixedSize(56, 56)
        icon_container.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #00ab84,
                    stop: 1 #00bcd4
                );
                border-radius: 16px;
            }
        """)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        try:
            icon = qta.icon("ph.monitor", color="#ffffff", color_active="#ffffff")
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(28, 28))
            icon_layout.addWidget(icon_label)
        except Exception:
            icon_label = QLabel("N")
            icon_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
            icon_label.setStyleSheet("color: #ffffff;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container)

        # Title area
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_widget.setLayout(title_layout)

        title = QLabel("System ")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"""
            color: {c.TEXT_PRIMARY};
            letter-spacing: 2px;
        """)

        subtitle = QLabel("Dashboard")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        layout.addWidget(title_widget, stretch=1)

        # Add header to main layout
        self.layout().insertWidget(0, header)

    def _setup_footer(self):
        """Setup premium footer with actions"""
        c = theme_manager.colors

        footer = QFrame()
        footer.setFrameShape(QFrame.Shape.NoFrame)
        footer.setFixedHeight(80)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: 0px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        footer.setLayout(layout)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)

        status_indicator = QFrame()
        status_indicator.setFixedSize(10, 10)
        status_indicator.setStyleSheet(f"""
            background-color: {c.ACCENT_GREEN};
            border-radius: 5px;
        """)
        status_layout.addWidget(status_indicator)

        status_text = QLabel("All systems operational")
        status_text.setFont(QFont("Segoe UI", 10))
        status_text.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Version row
        version_layout = QHBoxLayout()
        version_layout.setSpacing(10)

        version_text = QLabel("v2.0.0")
        version_text.setFont(QFont("Segoe UI", 10))
        version_text.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        version_layout.addWidget(version_text)

        version_layout.addStretch()

        layout.addLayout(version_layout)

        self.layout().insertWidget(self.layout().count(), footer)

    def _apply_theme(self):
        """Apply theme styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_SECONDARY};
                border: none;
                border-radius: 0px;
            }}
        """)

    def _on_item_clicked(self, key: str):
        """Handle navigation item click"""
        self.set_active_view(key)
        self.view_selected.emit(key)

    def set_active_view(self, view_name: str):
        """Set active view"""
        self._current_view = view_name
        for key, item in self._items.items():
            item.set_active(key == view_name)


# Legacy compatibility
Sidebar = PremiumSidebar
NavItem = PremiumNavItem
