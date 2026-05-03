"""
DonutGauge Widget - Circular progress indicator
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve


class DonutGauge(QWidget):
    """
    Donut gauge widget with animated value display
    """

    def __init__(self, color="#3b82f6", label="", size=100, parent=None):
        super().__init__(parent)
        self._color = color
        self._label = label
        self._size = size
        self._value = 0.0
        self._animated_value = 0.0

        self.setFixedSize(size, size)
        self._setup_animation()

    def _setup_animation(self):
        """Setup value animation"""
        self._animator = QPropertyAnimation(self, b"animated_value")
        self._animator.setDuration(500)
        self._animator.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def get_animated_value(self):
        return self._animated_value

    def set_animated_value(self, val):
        self._animated_value = val
        self.update()

    animated_value = pyqtProperty(float, get_animated_value, set_animated_value)

    def set_value(self, value):
        """Set gauge value with animation"""
        self._value = max(0.0, min(value, 100.0))

        # Animate to new value
        self._animator.stop()
        self._animator.setStartValue(self._animated_value)
        self._animator.setEndValue(self._value)
        self._animator.start()

    def set_color(self, color):
        """Set gauge color"""
        self._color = color
        self.update()

    def set_label(self, label):
        """Set gauge label"""
        self._label = label
        self.update()

    def paintEvent(self, event):
        """Paint the donut gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Colors
        bg_color = QColor("#1e2936")
        gauge_color = QColor(self._color)

        # Geometry
        margin = 8
        rect = QRectF(margin, margin, self._size - 2 * margin, self._size - 2 * margin)
        pen_width = 10

        # Background circle (full arc)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        bg_pen = QPen(bg_color)
        bg_pen.setWidth(pen_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(int(margin), int(margin), int(self._size - 2 * margin), int(self._size - 2 * margin), 225 * 16, -270 * 16)

        # Progress arc
        progress = self._animated_value / 100.0
        angle = int(progress * 270)

        progress_pen = QPen(gauge_color)
        progress_pen.setWidth(pen_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(int(margin), int(margin), int(self._size - 2 * margin), int(self._size - 2 * margin), 225 * 16, -angle * 16)

        # Center text - value
        center_x = self._size / 2
        center_y = self._size / 2

        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        painter.setPen(QColor("#f0f4f8"))
        value_text = f"{self._animated_value:.0f}%"
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(value_text)
        painter.drawText(int(center_x - text_width / 2), int(center_y + 6), value_text)

        # Label text
        if self._label:
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor("#64748b"))
            label_width = fm.horizontalAdvance(self._label)
            painter.drawText(int(center_x - label_width / 2), int(center_y + 22), self._label)

        painter.end()

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(self._size, self._size)