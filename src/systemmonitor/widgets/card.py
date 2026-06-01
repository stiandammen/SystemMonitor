"""
Card Widget - Container component with title and content
Professional glassmorphism styling with responsive sizing
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin


def _is_qta(icon: str) -> bool:
    """Return True if icon string is a qtawesome name like 'ph.cpu'."""
    return bool(icon) and '.' in icon and not icon.startswith('http')


class Card(QFrame, ScaleMixin):
    """
    Card component with title, optional icon, and content area
    Modern styling with rounded corners, glass effect, and responsive sizing
    """

    def __init__(self, title: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self.setObjectName("Card")
        self.scale_connect()
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()
        self.update()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup card UI with support for dynamic scaling without destroying content"""
        colors = theme_manager.colors
        
        # 1. Initialize main layout if not already present
        if self.layout() is None:
            self._layout = QVBoxLayout()
            self.setLayout(self._layout)
            
            # Header container (title + icon)
            self._header_layout = QHBoxLayout()
            self._layout.addLayout(self._header_layout)
            
            # Content container
            self._content_widget = QWidget()
            self._content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._content_layout = QVBoxLayout()
            self._content_layout.setContentsMargins(0, 0, 0, 0)
            self._content_layout.setSpacing(0)
            self._content_widget.setLayout(self._content_layout)
            self._layout.addWidget(self._content_widget, stretch=1)
            
            # Create header widgets if needed
            if self._icon:
                self._icon_label = QLabel()
                self._icon_label.setStyleSheet("background: transparent;")
                if _is_qta(self._icon):
                    self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    self._icon_label.setText(self._icon)
                self._header_layout.addWidget(self._icon_label)
            
            if self._title:
                self._title_label = QLabel(self._title)
                self._header_layout.addWidget(self._title_label)
            
            if self._icon or self._title:
                self._header_layout.addStretch()

        # 2. Update properties that change with scaling/theme
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self._layout.setSpacing(S.px(12))
        
        self._header_layout.setSpacing(S.px(10))
        
        if self._icon and hasattr(self, '_icon_label'):
            if _is_qta(self._icon):
                size = S.px(18)
                try:
                    pixmap = qta.icon(
                        self._icon,
                        color=theme_manager.colors.ACCENT_GREEN
                    ).pixmap(QSize(size, size))
                    self._icon_label.setPixmap(pixmap)
                    self._icon_label.setFixedSize(size, size)
                except Exception:
                    self._icon_label.setText("•")
            else:
                self._icon_label.setFont(QFont("Segoe UI", S.font_pt(16)))
            
        if self._title and hasattr(self, '_title_label'):
            font = QFont("Segoe UI", S.font_pt(13), QFont.Weight.Bold)
            self._title_label.setFont(font)
            self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")

    def _apply_theme(self):
        """Apply current theme styles with glassmorphism effect"""
        colors = theme_manager.colors
        self.setStyleSheet(f"""
            Card, QFrame#Card {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
            Card QWidget, Card QLabel {{
                border: none;
            }}
            Card:hover, QFrame#Card:hover {{
                background-color: {colors.BG_HOVER};
                border: none;
            }}
        """)

    def set_content(self, widget: QWidget):
        """Set the content widget"""
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        # Add new content
        self._content_layout.addWidget(widget)

    def add_widget(self, widget: QWidget):
        """Add a widget to content area"""
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to content area"""
        self._content_layout.addLayout(layout)

    def set_title(self, title: str):
        """Update card title"""
        self._title = title
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)