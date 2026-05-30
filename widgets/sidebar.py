"""
Nexus Monitor - Premium Sidebar Navigation Widget
Modern enterprise-grade design with dark theme
"""
import sys
import os

# Add project root to sys.path for standalone script execution
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

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
            {"key": "overview", "label": "Dashboard", "icon": "mdi.view-dashboard"},
            {"key": "cpu", "label": "Processor", "icon": "ph.cpu"},
            {"key": "gpu", "label": "Graphics", "icon": "ph.monitor"},
            {"key": "network", "label": "Network", "icon": "ph.wifi-high"},
            {"key": "memory", "label": "Memory", "icon": "mdi.memory"},
            {"key": "storage", "label": "Storage", "icon": "ph.database"},
                    ]
    },
    "tools": {
        "title": None,
        "items": [
            {"key": "settings", "label": "Settings", "icon": "ph.gear"},
        ]
    }
}


class PremiumNavItem(QPushButton, ScaleMixin):
    """Premium navigation item with glow and gradient effects"""

    clicked_with_name = pyqtSignal(str)

    def __init__(self, key: str, label: str, icon_name: str,
                 accent: str | None = None, parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self._icon_name = icon_name
        self._accent = accent  # None means use theme default
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
            c = theme_manager.colors
            normal_color = QColor(c.TEXT_MUTED)
            active_color = QColor(self._accent or c.ACCENT_GREEN)
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
        accent = self._accent or c.ACCENT_GREEN

        if theme_manager.current_theme == "heimdal":
            # Heimdal theme styling
            active_border = "border-left: 4px solid #4A6CF7;"
            normal_border = "border-left: 4px solid transparent;"
            active_bg = "background-color: rgba(74, 108, 247, 0.15);"
            hover_bg = "background-color: rgba(74, 108, 247, 0.08);"

            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #8A92B2;
                    border: none;
                    {normal_border}
                    padding: {S.px(12)}px {S.px(16)}px;
                    text-align: left;
                    border-radius: {S.px(6)}px;
                    font-family: "Segoe UI", sans-serif;
                    font-size: {S.px(13)}px;
                    font-weight: 500;
                }}

                QPushButton:hover {{
                    {hover_bg}
                    color: #E8ECFF;
                    border-left: 4px solid rgba(74, 108, 247, 0.4);
                }}

                QPushButton:checked {{
                    {active_bg}
                    color: #E8ECFF;
                    {active_border}
                }}

                QPushButton:pressed {{
                    {hover_bg}
                    color: #E8ECFF;
                }}
            """)
        else:
            # Subtle glow border for active state (no solid background)
            glow_border = f"""
                border-left: 2px solid {accent};
            """
            normal_border = "border-left: 2px solid transparent;"

            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c.TEXT_SECONDARY};
                    border: none;
                    {normal_border}
                    padding: {S.px(12)}px {S.px(16)}px;
                    text-align: left;
                    border-radius: {S.px(6)}px;
                    font-family: "Segoe UI", sans-serif;
                    font-size: {S.px(13)}px;
                    font-weight: 500;
                }}

                QPushButton:hover {{
                    background-color: {c.BG_HOVER};
                    color: {c.TEXT_PRIMARY};
                }}

                QPushButton:checked {{
                    background-color: transparent;
                    color: {c.TEXT_PRIMARY};
                    {glow_border}
                }}

                QPushButton:pressed {{
                    background-color: {c.BG_HOVER};
                    color: {c.TEXT_PRIMARY};
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
            c = theme_manager.colors
            accent = self._accent or c.ACCENT_GREEN
            color = accent if self._is_active else c.TEXT_MUTED
            icon = qta.icon(self._icon_name, color=color, color_active=accent)
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
                    icon_name=item_data["icon"]
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
        header.setFixedHeight(70)
        if theme_manager.current_theme == "heimdal":
            header.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                }}
            """)
        else:
            header.setStyleSheet(f"""
                QFrame {{
                    background-color: {c.BG_PRIMARY};
                    border: none;
                    border-radius: 0px;
                }}
            """)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setLayout(layout)

        # App icon - modern styled container
        icon_container = QFrame()
        icon_container.setFixedSize(44, 44)
        if theme_manager.current_theme == "heimdal":
            icon_container.setStyleSheet(f"""
                QFrame {{
                    background-color: #4A6CF7;
                    border-radius: 10px;
                }}
            """)
        else:
            icon_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {c.ACCENT_GREEN};
                    border-radius: 10px;
                }}
            """)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        try:
            icon = qta.icon("mdi.server", color=c.TEXT_PRIMARY, color_active=c.TEXT_PRIMARY)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(22, 22))
            icon_layout.addWidget(icon_label)
        except Exception:
            icon_label = QLabel("SM")
            icon_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            icon_label.setStyleSheet(f"color: {c.TEXT_PRIMARY};")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container)

        # App title
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        title_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        title_container.addWidget(title)

        version = QLabel("v2.0")
        version.setFont(QFont("Segoe UI", 9))
        version.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        title_container.addWidget(version)

        layout.addLayout(title_container)
        layout.addStretch()

        # Add header to main layout
        self.layout().insertWidget(0, header)

    def _setup_footer(self):
        """Setup premium footer with actions"""
        c = theme_manager.colors

        footer = QFrame()
        footer.setFrameShape(QFrame.Shape.NoFrame)
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_PRIMARY};
                border: none;
                border-radius: 0px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        footer.setLayout(layout)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        status_indicator = QFrame()
        status_indicator.setFixedSize(8, 8)
        status_indicator.setStyleSheet(f"""
            background-color: {c.ACCENT_GREEN};
            border-radius: 4px;
        """)
        status_layout.addWidget(status_indicator)

        status_text = QLabel("All systems operational")
        status_text.setFont(QFont("Segoe UI", 10))
        status_text.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        self.layout().insertWidget(self.layout().count(), footer)

    def _apply_theme(self):
        """Apply theme styles"""
        c = theme_manager.colors

        if theme_manager.current_theme == "heimdal":
            # Heimdal theme: vertical gradient background
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1A1E35,
                        stop:1 #12152A);
                    border: none;
                    border-radius: 0px;
                }}
            """)
        else:
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
