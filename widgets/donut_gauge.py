"""
DonutGauge Widget - Circular progress indicator
"""
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QConicalGradient
from PyQt6.QtCore import Qt, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class DonutGauge(QWidget, ScaleMixin):
    """
    Donut gauge widget with animated value display
    """

    def __init__(self, color=None, label="", size=100, parent=None):
        super().__init__(parent)
        self._color = color  # None means use theme accent
        self._label = label
        self._size = size
        self._value = 0.0
        self._animated_value = 0.0

        self.scale_connect()
        self.setMinimumSize(S.px(size), S.px(size))
        self.setMaximumSize(S.px(size * 2), S.px(size * 2))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._setup_animation()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self.update()

    def get_animated_value(self):
        return self._animated_value

    def set_animated_value(self, val):
        self._animated_value = val
        self.update()

    animated_value = pyqtProperty(float, get_animated_value, set_animated_value)

    def _get_effective_color(self):
        """Get the effective gauge color"""
        if self._color:
            return self._color
        return theme_manager.colors.ACCENT_GREEN

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

        colors = theme_manager.colors

        # Use actual widget size for responsive rendering
        size = min(self.width(), self.height())
        if size <= 0:
            painter.end()
            return

        # Geometry
        margin = S.px(8)
        rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
        pen_width = S.px(10)

        # Background circle (full arc)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        bg_pen = QPen(QColor(colors.GAUGE_BG))
        bg_pen.setWidth(pen_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(int(margin), int(margin), int(size - 2 * margin), int(size - 2 * margin), 225 * 16, -270 * 16)

        # Progress arc with gradient
        progress = self._animated_value / 100.0
        angle = int(progress * 270)

        cx = size / 2
        cy = size / 2

        # Check if theme is heimdal for gradient, otherwise use solid color
        if theme_manager.current_theme == "heimdal":
            gradient = QConicalGradient(cx, cy, 225)
            gradient.setColorAt(0.0, QColor("#4A6CF7"))
            gradient.setColorAt(0.75, QColor("#7B5CF0"))
            gradient.setColorAt(1.0, QColor("#4A6CF7"))
            progress_pen = QPen(QBrush(gradient), pen_width)
        else:
            progress_pen = QPen(QColor(self._get_effective_color()))
        progress_pen.setWidth(pen_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(int(margin), int(margin), int(size - 2 * margin), int(size - 2 * margin), 225 * 16, -angle * 16)

        # Center text - value
        center_x = size / 2
        center_y = size / 2

        painter.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        value_text = f"{self._animated_value:.0f}%"
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(value_text)
        # Center text vertically with padding to avoid truncation
        text_y = int(center_y + S.px(6))
        painter.drawText(int(center_x - text_width / 2), text_y, value_text)

        # Label text (positioned below value)
        if self._label:
            painter.setFont(QFont("Segoe UI", S.font_pt(9)))
            painter.setPen(QColor(colors.TEXT_MUTED))
            label_width = fm.horizontalAdvance(self._label)
            # Position label below value, not overlapping
            label_y = int(center_y + S.px(26))
            painter.drawText(int(center_x - label_width / 2), label_y, self._label)

        painter.end()

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(S.px(self._size), S.px(self._size))
