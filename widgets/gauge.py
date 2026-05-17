"""
Gauge Widget - Circular progress indicator
"""
from PyQt6.QtWidgets import QFrame
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont, QPen, QConicalGradient
from PyQt6.QtCore import Qt, QRectF, QTimer

from styles.theme import theme_manager
from config import FontConfig


class Gauge(QFrame):
    """
    Circular gauge widget with animated progress
    Supports color thresholds and glow effects
    Optimized with throttled repaints.
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
        self._pending_update = False

        self.setFixedSize(size, size)
        self._apply_theme()

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

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
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def set_max_value(self, max_value: float):
        """Update maximum value"""
        self._max_value = max(max_value, 1.0)
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)
    
    def paintEvent(self, event):
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors

        # Calculate geometry
        margin = 8
        rect = QRectF(margin, margin,
                     self._size - 2 * margin,
                     self._size - 2 * margin)

        # Draw background circle
        painter.setBrush(QBrush(QColor(c.GAUGE_BG)))
        painter.setPen(Qt.PenStyle.NoPen)
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

        # Get color based on value (but baseline is accent_green)
        base_color = c.ACCENT_GREEN
        color = self._get_color_for_value(progress * 100)

        # Draw background arc
        bg_pen = QPen(QColor(c.BORDER))
        bg_pen.setWidth(pen_width)
        bg_pen.setCapStyle(Qt.PenStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(progress_rect, 0, 360 * 16)

        # Draw progress arc with gradient for Heimdal theme
        if theme_manager.current_theme == "heimdal":
            cx = self._size / 2
            cy = self._size / 2
            gradient = QConicalGradient(cx, cy, 225)
            gradient.setColorAt(0.0, QColor("#4A6CF7"))
            gradient.setColorAt(0.75, QColor("#7B5CF0"))
            gradient.setColorAt(1.0, QColor("#4A6CF7"))
            progress_pen = QPen(QBrush(gradient), pen_width)
        else:
            progress_pen = QPen(QColor(color))
        progress_pen.setWidth(pen_width)
        progress_pen.setCapStyle(Qt.PenStyle.RoundCap)
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
