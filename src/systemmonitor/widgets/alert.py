"""
Alert Badge Widget
"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from systemmonitor.styles.theme import theme_manager
from systemmonitor.utils.constants import AlertLevel


class AlertBadge(QPushButton):
    """
    Alert badge showing count and severity
    """
    
    def __init__(self, count: int = 0, level: AlertLevel = AlertLevel.INFO, parent=None):
        super().__init__(parent)
        self._count = count
        self._level = level
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(32, 32)
        self._update_display()
    
    def set_count(self, count: int):
        """Update badge count"""
        self._count = count
        self._update_display()
    
    def set_level(self, level: AlertLevel):
        """Update alert level"""
        self._level = level
        self._update_display()
    
    def _update_display(self):
        """Update badge display"""
        c = theme_manager.colors
        
        # Get color based on level
        if self._level == AlertLevel.CRITICAL:
            color = c.ACCENT_RED
        elif self._level == AlertLevel.WARNING:
            color = c.ACCENT_ORANGE
        else:
            color = c.ACCENT_BLUE
        
        # Show count or just dot
        if self._count > 0:
            self.setText(str(min(self._count, 99)))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            self.setFont(font)
        else:
            self.setText("")
        
        self.setStyleSheet(f"""
            AlertBadge {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: bold;
            }}
            
            AlertBadge:hover {{
                background-color: {color}DD;
            }}
        """)
        
        self.setVisible(self._count > 0)
