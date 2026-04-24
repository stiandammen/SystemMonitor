"""
Gauge Widget - Circular progress indicator
"""
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPen, QConicalGradient
from PyQt5.QtCore import Qt, QRectF

from styles.theme import theme_manager
from config import FontConfig


class Gauge(QFrame):
    """
    Circular gauge widget with animated progress
    Supports color thresholds and glow effects
    """
    
    def __init__(self, title: str = "", max_value: float = 100.0, 
                 unit: str = "%", size: int = 140, parent=None):
        super().__init__(parent)
        self._title = title
        self._max_value = max_value
        self._unit = unit
        self._size = size
        self._value = 0.0
        self._target_value = 0.0
        
        self.setFixedSize(size, size)
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            Gauge {{
                background-color: transparent;
                border: none;
            }}
        """)
    
    def set_value(self, value: float):
        """Update gauge value"""
        self._target_value = max(0.0, min(value, self._max_value))
        # Simple animation step
        self._value = self._value + (self._target_value - self._value) * 0.3
        self.update()
    
    def set_max_value(self, max_value: float):
        """Update maximum value"""
        self._max_value = max(max_value, 1.0)
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        c = theme_manager.colors
        
        # Calculate geometry
        margin = 8
        rect = QRectF(margin, margin, 
                     self._size - 2 * margin, 
                     self._size - 2 * margin)
        
        # Draw background circle
        painter.setBrush(QBrush(QColor(c.GAUGE_BG)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect)
        
        # Calculate progress
        progress = self._value / self._max_value if self._max_value > 0 else 0
        angle = progress * 360
        
        # Draw progress arc
        pen_width = 8
        progress_rect = QRectF(
            margin + pen_width / 2,
            margin + pen_width / 2,
            self._size - 2 * margin - pen_width,
            self._size - 2 * margin - pen_width
        )
        
        # Get color based on value
        color = self._get_color_for_value(progress * 100)
        
        # Draw background arc
        bg_pen = QPen(QColor(c.BORDER))
        bg_pen.setWidth(pen_width)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(progress_rect, 0, 360 * 16)
        
        # Draw progress arc
        progress_pen = QPen(QColor(color))
        progress_pen.setWidth(pen_width)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(progress_rect, 90 * 16, -angle * 16)
        
        # Draw center text
        center_x = self._size / 2
        center_y = self._size / 2
        
        # Value text
        painter.setFont(FontConfig.VALUE_LARGE)
        painter.setPen(QColor(c.TEXT_PRIMARY))
        value_text = f"{int(self._value)}{self._unit}"
        
        # Center text
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(value_text)
        painter.drawText(int(center_x - text_width / 2), 
                        int(center_y - 5), 
                        value_text)
        
        # Title text
        if self._title:
            painter.setFont(FontConfig.SMALL)
            painter.setPen(QColor(c.TEXT_SECONDARY))
            title_width = fm.horizontalAdvance(self._title)
            painter.drawText(int(center_x - title_width / 2), 
                           int(center_y + 20), 
                           self._title)
        
        painter.end()
    
    def _get_color_for_value(self, percentage: float) -> str:
        """Get color based on percentage"""
        c = theme_manager.colors
        if percentage >= 90:
            return c.ACCENT_RED
        elif percentage >= 70:
            return c.ACCENT_ORANGE
        elif percentage >= 50:
            return c.ACCENT_YELLOW
        else:
            return c.ACCENT_GREEN
