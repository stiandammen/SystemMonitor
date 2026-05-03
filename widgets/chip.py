"""
Stat Chip Widget - Compact stat display
"""
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class StatChip(QFrame, ScaleMixin):
    """
    Compact chip showing label and value
    """
    
    def __init__(self, label: str = "", value: str = "", trend: str = "", parent=None):
        super().__init__(parent)
        self._label_text = label
        self._value_text = value
        self._trend_text = trend
        self.scale_connect()
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Setup chip UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        self.setLayout(layout)
        
        # Label
        self._label = QLabel(self._label_text)
        label_font = QFont("Segoe UI", 10)
        self._label.setFont(label_font)
        layout.addWidget(self._label)
        
        # Value
        self._value = QLabel(self._value_text)
        value_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self._value.setFont(value_font)
        layout.addWidget(self._value)
        
        # Trend (optional)
        if self._trend_text:
            self._trend = QLabel(self._trend_text)
            trend_font = QFont("Segoe UI", 9)
            self._trend.setFont(trend_font)
            layout.addWidget(self._trend)
        
        layout.addStretch()
    
    def _apply_style(self):
        """Apply chip styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            StatChip {{
                background-color: {c.BG_CARD};
                border: 1px solid {c.BORDER};
                border-radius: 6px;
            }}
        """)
        
        self._label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        self._value.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
    
    def set_value(self, value: str):
        """Update value text"""
        self._value_text = value
        self._value.setText(value)
    
    def set_label(self, label: str):
        """Update label text"""
        self._label_text = label
        self._label.setText(label)
