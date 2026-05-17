"""
Card Widget - Container component with title and content
Professional glassmorphism styling with responsive sizing
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class Card(QFrame, ScaleMixin):
    """
    Card component with title, optional icon, and content area
    Modern styling with rounded corners, glass effect, and responsive sizing
    """

    def __init__(self, title: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
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
        """Setup card UI"""
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self._layout.setSpacing(S.px(12))
        self.setLayout(self._layout)

        # Header (title + icon)
        if self._title or self._icon:
            self._header = QHBoxLayout()
            self._header.setSpacing(S.px(10))

            # Icon
            if self._icon:
                self._icon_label = QLabel(self._icon)
                self._icon_label.setFont(QFont("Segoe UI", S.font_pt(16)))
                self._icon_label.setStyleSheet("background: transparent;")
                self._header.addWidget(self._icon_label)

            # Title
            if self._title:
                self._title_label = QLabel(self._title)
                font = QFont("Segoe UI", S.font_pt(13), QFont.Weight.Bold)
                self._title_label.setFont(font)
                self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
                self._header.addWidget(self._title_label)

            self._header.addStretch()
            self._layout.addLayout(self._header)

        # Content area
        self._content_widget = QWidget()
        self._content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_widget.setLayout(self._content_layout)
        self._layout.addWidget(self._content_widget, stretch=1)

    def _apply_theme(self):
        """Apply current theme styles with glassmorphism effect"""
        colors = theme_manager.colors

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                Card, QFrame#Card {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                Card:hover, QFrame#Card:hover {{
                    border-color: rgba(74, 108, 247, 0.5);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                Card, QFrame#Card {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                Card:hover, QFrame#Card:hover {{
                    border-color: {colors.ACCENT_BLUE};
                    background-color: {colors.BG_HOVER};
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
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to content area"""
        self._content_layout.addLayout(layout)

    def set_title(self, title: str):
        """Update card title"""
        self._title = title
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)