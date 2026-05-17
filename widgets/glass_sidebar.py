"""
Premium Glass Sidebar Navigation Widget
Responsive design with adaptive collapse, smooth animations, and glassmorphism
"""
import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QIcon, QPainter, QLinearGradient, QColor, QPen
import qtawesome as qta
from typing import Optional, Dict

from styles.theme import theme_manager
from scaler import S, ScaleMixin, LayoutMode


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


class GlassNavItem(QPushButton, ScaleMixin):
    """Premium glass navigation item with glow and gradient effects"""

    clicked_with_name = pyqtSignal(str)

    def __init__(self, key: str, label: str, icon_name: str,
                 accent: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self._icon_name = icon_name
        self._accent = accent or theme_manager.colors.ACCENT_GREEN
        self._is_active = False
        self._is_hovered = False
        self._collapsed = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(S.px(40))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        font = S.font("Segoe UI", 12)
        self.setFont(font)

        self._setup_icon()
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.clicked.connect(lambda: self.clicked_with_name.emit(key))
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.scale_connect()

    def _on_theme_changed(self, theme_name: str):
        self._apply_style()
        self._setup_icon()

    def on_scale_changed(self, factor: float):
        self._apply_style()
        self._setup_icon()

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        if collapsed:
            self.setText("")
            self.setIconSize(QSize(S.px(22), S.px(22)))
            self.setMinimumWidth(S.px(44))
            self.setMaximumWidth(S.px(64))
        else:
            self.setText(f"  {self._label}")
            self.setIconSize(QSize(S.px(20), S.px(20)))
            self.setMinimumWidth(S.px(100))
            self.setMaximumWidth(16777215)

    def _setup_icon(self):
        try:
            c = theme_manager.colors
            normal_color = QColor(c.TEXT_MUTED)
            active_color = QColor(self._accent)
            icon = qta.icon(
                self._icon_name,
                color=normal_color,
                color_active=active_color
            )
            self.setIcon(icon)
            self.setIconSize(QSize(S.px(20), S.px(20)))
            self.setText(f"  {self._label}")
        except Exception:
            self.setText(f"  {self._label}")

    def _apply_style(self):
        c = theme_manager.colors
        accent = self._accent

        if theme_manager.current_theme == "heimdal":
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
                    padding: {S.px(10)}px {S.px(14)}px;
                    text-align: left;
                    border-radius: {S.px(8)}px;
                    font-family: "Segoe UI", sans-serif;
                    font-size: {S.font_pt(12)}px;
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
            active_border = f"""
                border-left: 3px solid {accent};
                background-color: {c.ACCENT_GREEN_DIM};
            """
            normal_border = "border-left: 3px solid transparent; background-color: transparent;"

            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c.TEXT_SECONDARY};
                    border: none;
                    {normal_border}
                    padding: {S.px(10)}px {S.px(16)}px;
                    text-align: left;
                    border-radius: {S.px(8)}px;
                    font-family: "Segoe UI", sans-serif;
                    font-size: {S.font_pt(12)}px;
                    font-weight: 500;
                }}

                QPushButton:hover {{
                    background-color: {c.BG_HOVER};
                    color: {c.TEXT_PRIMARY};
                    border-left: 3px solid {accent};
                }}

                QPushButton:checked {{
                    background-color: {c.ACCENT_GREEN_DIM};
                    color: {c.TEXT_PRIMARY};
                    border-left: 3px solid {accent};
                }}

                QPushButton:pressed {{
                    background-color: {c.BG_HOVER};
                    color: {c.TEXT_PRIMARY};
                }}
            """)

    def set_active(self, active: bool):
        self._is_active = active
        self.setChecked(active)
        self._update_icon()
        self._apply_style()

    def _update_icon(self):
        try:
            c = theme_manager.colors
            color = self._accent if self._is_active else c.TEXT_MUTED
            icon = qta.icon(self._icon_name, color=color, color_active=self._accent)
            self.setIcon(icon)
        except Exception:
            pass


class GlassSidebar(QFrame, ScaleMixin):
    """Premium glassmorphism sidebar navigation - fully responsive"""

    view_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: Dict[str, GlassNavItem] = {}
        self._current_view: str = ""
        self._collapsed = S.is_compact()
        self._expanded_width = S.px(220)
        self._collapsed_width = S.px(58)
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.scale_connect()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setBlurRadius(20)
        shadow.setOffset(2, 0)
        self.setGraphicsEffect(shadow)

    def on_scale_changed(self, factor: float):
        self._expanded_width = S.px(220)
        self._collapsed_width = S.px(58)
        self._setup_ui()
        self._apply_theme()
        self.update()

    def on_layout_mode_changed(self, mode):
        if mode == LayoutMode.COMPACT:
            if not self._collapsed:
                self._toggle_collapse()
        else:
            if self._collapsed:
                self._toggle_collapse()

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()
        for item in self._items.values():
            item._apply_style()

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        target_width = self._collapsed_width if self._collapsed else self._expanded_width

        self._width_animation = QPropertyAnimation(self, b"sidebar_width")
        self._width_animation.setDuration(200)
        self._width_animation.setStartValue(self.width())
        self._width_animation.setEndValue(target_width)
        self._width_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._width_animation.start()
        self._width_animation.finished.connect(self._on_collapse_animation_finished)

    def _on_collapse_animation_finished(self):
        self._update_collapse_state()

    def _update_collapse_state(self):
        self.setFixedWidth(self._collapsed_width if self._collapsed else self._expanded_width)

        if hasattr(self, '_header'):
            self._header.setVisible(not self._collapsed)

        if hasattr(self, '_footer'):
            self._footer.setVisible(not self._collapsed)

        for item in self._items.values():
            item.set_collapsed(self._collapsed)

        if hasattr(self, '_collapse_btn'):
            if self._collapsed:
                self._collapse_btn.setText("▶")
            else:
                self._collapse_btn.setText("◀")

    def _setup_ui(self):
        self.setMinimumWidth(self._collapsed_width)
        self.setMaximumWidth(self._expanded_width + S.px(40))
        current_width = self._collapsed_width if self._collapsed else self._expanded_width
        self.setFixedWidth(current_width)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._setup_header()
        self._header.setVisible(not self._collapsed)

        nav_container = QFrame()
        nav_container.setObjectName("nav_container")
        nav_container.setStyleSheet("""
            #nav_container {
                background-color: rgba(26, 30, 53, 0.7);
                border-top: 1px solid rgba(74, 108, 247, 0.15);
                border-bottom: 1px solid rgba(74, 108, 247, 0.15);
            }
        """)
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(S.px(6), S.px(8), S.px(6), S.px(8))
        nav_layout.setSpacing(S.px(2))
        nav_container.setLayout(nav_layout)

        for section_key, section_data in NAV_STRUCTURE.items():
            title = section_data.get("title")
            if title:
                section_label = QLabel(title.upper())
                section_label.setObjectName("section_label")
                section_label.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.DemiBold))
                section_label.setStyleSheet("""
                    color: #525A7A;
                    letter-spacing: 1.5px;
                    padding: 12px 10px 6px 10px;
                    background: transparent;
                """)
                nav_layout.addWidget(section_label)

            for item_data in section_data["items"]:
                item = GlassNavItem(
                    key=item_data["key"],
                    label=item_data["label"],
                    icon_name=item_data["icon"]
                )
                item.clicked_with_name.connect(self._on_item_clicked)
                nav_layout.addWidget(item)
                self._items[item_data["key"]] = item

        layout.addWidget(nav_container, stretch=1)

        collapse_btn = QPushButton()
        collapse_btn.setMinimumHeight(S.px(36))
        collapse_btn.setMaximumHeight(S.px(44))
        collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        collapse_btn.setText("▶" if self._collapsed else "◀")
        collapse_btn.setFont(QFont("Segoe UI", S.font_pt(11)))
        collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 35, 64, 0.6);
                color: #8A92B2;
                border: none;
                border-top: 1px solid rgba(74, 108, 247, 0.15);
            }
            QPushButton:hover {
                background-color: rgba(74, 108, 247, 0.15);
                color: #E8ECFF;
            }
        """)
        collapse_btn.clicked.connect(self._toggle_collapse)
        self._collapse_btn = collapse_btn
        layout.addWidget(collapse_btn)

        self._setup_footer()
        self._footer.setVisible(not self._collapsed)

    def _setup_header(self):
        c = theme_manager.colors

        header = QFrame()
        header.setObjectName("sidebar_header")
        header.setMinimumHeight(S.px(48))
        header.setMaximumHeight(S.px(64))
        header.setStyleSheet(f"""
            #sidebar_header {{
                background-color: rgba(26, 30, 53, 0.5);
                border: none;
                border-bottom: 1px solid rgba(74, 108, 247, 0.15);
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(10), S.px(10), S.px(10), S.px(10))
        layout.setSpacing(S.px(8))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setLayout(layout)

        icon_container = QFrame()
        icon_container.setMinimumSize(S.px(32), S.px(32))
        icon_container.setMaximumSize(S.px(40), S.px(40))
        icon_container.setStyleSheet(f"""
            background-color: #4A6CF7;
            border-radius: {S.px(7)}px;
        """)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        icon_label = QLabel("SM")
        icon_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        icon_label.setStyleSheet("color: white;")
        icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container)

        title_container = QVBoxLayout()
        title_container.setSpacing(1)
        title_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.DemiBold))
        title.setStyleSheet("color: #E8ECFF; background: transparent;")
        title_container.addWidget(title)

        version = QLabel("v2.0")
        version.setFont(QFont("Segoe UI", S.font_pt(8)))
        version.setStyleSheet("color: #525A7A; background: transparent;")
        title_container.addWidget(version)

        layout.addLayout(title_container)
        layout.addStretch()

        self._header = header
        self.layout().insertWidget(0, header)

    def _setup_footer(self):
        footer = QFrame()
        footer.setObjectName("sidebar_footer")
        footer.setFrameShape(QFrame.Shape.NoFrame)
        footer.setMinimumHeight(S.px(36))
        footer.setMaximumHeight(S.px(48))
        footer.setStyleSheet(f"""
            #sidebar_footer {{
                background-color: rgba(26, 30, 53, 0.5);
                border: none;
                border-top: 1px solid rgba(74, 108, 247, 0.15);
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
        layout.setSpacing(2)
        footer.setLayout(layout)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(S.px(6))

        status_indicator = QFrame()
        status_indicator.setFixedSize(S.px(6), S.px(6))
        status_indicator.setStyleSheet(f"""
            background-color: #00E096;
            border-radius: {S.px(3)}px;
        """)
        status_layout.addWidget(status_indicator)

        status_text = QLabel("Operational")
        status_text.setFont(QFont("Segoe UI", S.font_pt(8)))
        status_text.setStyleSheet("color: #525A7A; background: transparent;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        self._footer = footer
        self.layout().insertWidget(self.layout().count(), footer)

    def _apply_theme(self):
        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet("""
                QFrame {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1A1E35,
                        stop:1 #12152A);
                    border: none;
                    border-radius: 0px;
                }
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme_manager.colors.BG_SECONDARY};
                    border: none;
                    border-radius: 0px;
                }}
            """)

    def _on_item_clicked(self, key: str):
        self.set_active_view(key)
        self.view_selected.emit(key)

    def set_active_view(self, view_name: str):
        self._current_view = view_name
        for key, item in self._items.items():
            item.set_active(key == view_name)

    def get_sidebar_width(self):
        return self.width()

    def set_sidebar_width(self, width):
        self.setFixedWidth(int(width))

    sidebar_width = pyqtProperty(int, get_sidebar_width, set_sidebar_width)


# Legacy compatibility
PremiumSidebar = GlassSidebar
NexusSidebar = GlassSidebar