"""
Sidebar Navigation Widget
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from typing import List, Callable, Optional

from styles.theme import theme_manager
from utils.constants import ViewName, VIEW_ICONS, VIEW_TITLES, VIEW_ICON_IMAGES


class NavItem(QPushButton):
    """Individual navigation item"""

    clicked_with_name = pyqtSignal(str)

    def __init__(self, view_name: str, icon: str, label: str, icon_image: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._view_name = view_name
        self._icon = icon
        self._label = label
        self._active = False
        self._icon_image = icon_image

        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setMinimumWidth(180)

        font = QFont("Segoe UI", 12)
        self.setFont(font)

        if icon_image:
            pixmap = QPixmap(icon_image)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(scaled_pixmap))
                self.setIconSize(QSize(24, 24))
                self.setText(f"  {label}")
            else:
                self.setText(f"{icon}  {label}")
        else:
            self.setText(f"{icon}  {label}")

        self.setLayoutDirection(Qt.LeftToRight)

        self.clicked.connect(lambda: self.clicked_with_name.emit(view_name))
        self._apply_style()

    def _apply_style(self):
        """Apply navigation item style"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            NavItem {{
                background-color: transparent;
                color: {c.TEXT_SECONDARY};
                border: none;
                border-left: 3px solid transparent;
                padding: 10px 16px;
                text-align: left;
                border-radius: 0px;
            }}

            NavItem:hover {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
            }}

            NavItem:checked {{
                background-color: {c.BG_CARD};
                color: {c.ACCENT_GREEN};
                border-left: 3px solid {c.ACCENT_GREEN};
                font-weight: bold;
            }}
        """)
    
    def set_active(self, active: bool):
        """Set active state"""
        self._active = active
        self.setChecked(active)


class Sidebar(QFrame):
    """Navigation sidebar with items"""
    
    view_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: dict[str, NavItem] = {}
        self._current_view: str = ""
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup sidebar UI"""
        self.setFixedWidth(200)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)
        self.setLayout(layout)
        
        # Title
        title = QLabel("⚙  SYSTEM MONITOR")
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"padding: 0 16px 16px 16px;")
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme_manager.colors.BORDER};")
        layout.addWidget(separator)
        
        # Navigation items
        nav_container = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(2)
        nav_container.setLayout(nav_layout)
        
        for view_name in ViewName:
            name = view_name.value
            icon_image = VIEW_ICON_IMAGES.get(view_name)
            item = NavItem(
                name,
                VIEW_ICONS.get(view_name, "●"),
                VIEW_TITLES.get(view_name, name.capitalize()),
                icon_image=icon_image
            )
            item.clicked_with_name.connect(self._on_item_clicked)
            nav_layout.addWidget(item)
            self._items[name] = item
        
        layout.addWidget(nav_container)
        layout.addStretch()
        
        # Version
        version = QLabel("v2.0.0")
        version.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; padding: 0 16px;")
        layout.addWidget(version)
    
    def _apply_theme(self):
        """Apply theme styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {c.BG_SECONDARY};
                border-right: 1px solid {c.BORDER};
            }}
        """)
    
    def _on_item_clicked(self, view_name: str):
        """Handle navigation item click"""
        self.set_active_view(view_name)
        self.view_selected.emit(view_name)
    
    def set_active_view(self, view_name: str):
        """Set active view"""
        self._current_view = view_name
        for name, item in self._items.items():
            item.set_active(name == view_name)
