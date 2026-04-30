"""
Card Widget - Container component with title and content
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from styles.theme import theme_manager


class Card(QFrame):
    """
    Card component with title, optional icon, and content area
    Modern styling with rounded corners and shadow effect
    """
    
    def __init__(self, title: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup card UI"""
        # Main layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        self.setLayout(self._layout)
        
        # Header (title + icon)
        if self._title or self._icon:
            self._header = QHBoxLayout()
            self._header.setSpacing(8)
            
            # Icon
            if self._icon:
                self._icon_label = QLabel(self._icon)
                self._icon_label.setStyleSheet("font-size: 16px;")
                self._header.addWidget(self._icon_label)
            
            # Title
            if self._title:
                self._title_label = QLabel(self._title)
                font = QFont("Segoe UI", 13)
                font.setBold(True)
                self._title_label.setFont(font)
                self._header.addWidget(self._title_label)
            
            self._header.addStretch()
            self._layout.addLayout(self._header)
        
        # Content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_widget.setLayout(self._content_layout)
        self._layout.addWidget(self._content_widget)
    
    def _apply_theme(self):
        """Apply current theme styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            Card {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: 10px;
            }}
        """)
    
    def set_content(self, widget: QWidget):
        """Set the content widget"""
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        # Add new content
        self._content_layout.addWidget(widget)
    
    def add_widget(self, widget: QWidget):
        """Add a widget to content area"""
        self._content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to content area"""
        self._content_layout.addLayout(layout)
    
    def set_title(self, title: str):
        """Update card title"""
        self._title = title
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)
