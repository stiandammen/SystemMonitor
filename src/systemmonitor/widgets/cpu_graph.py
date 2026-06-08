"""
Per-core CPU usage graph widget - extracted from views/cpu.py so it can be
reused outside the CPU view (e.g. a future "Dashboard" overlay).
"""
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.ui_tick import ui_tick


class CpuGraphWidget(QWidget, ScaleMixin):
    """Individual CPU core graph that adapts to container size - optimized with throttled repaints"""

    def __init__(self, core_index: int = 0, parent=None):
        super().__init__(parent)
        self._core_index = core_index
        self._history = []
        self._max_points = 50
        self._display_value = 0.0
        self._pending_update = False

        self.scale_connect()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(S.px(100), S.px(80))

        # Throttle repaints to ~30fps via the shared UI tick instead of a private QTimer
        ui_tick.tick.connect(self._on_tick)

    def _on_tick(self):
        if self._pending_update:
            self._pending_update = False
            self.update()

    def set_value(self, value: float):
        """Set current CPU value with smooth animation"""
        self._display_value += (value - self._display_value) * 0.3

        if not self._history or len(self._history) > 0:
            self._history.append(value)
            if len(self._history) > self._max_points:
                self._history.pop(0)

        self._pending_update = True

    def paintEvent(self, a0):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = theme_manager.colors
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            painter.end()
            return

        pad = S.px(8)
        graph_w = w - pad * 2
        graph_h = h - pad * 2 - S.px(20)

        painter.setBrush(QColor(colors.BG_CARD))
        painter.setPen(QPen(QColor(colors.BORDER), 0))  # No border
        painter.drawRoundedRect(0, 0, int(w), int(h), S.px(8), S.px(8))

        if not self._history:
            painter.setFont(QFont("Segoe UI", S.font_pt(8)))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Loading...")
            painter.end()
            return

        points = []
        step = graph_w / max(len(self._history) - 1, 1)
        for i, val in enumerate(self._history):
            x = pad + step * i
            y = pad + graph_h - (val / 100.0 * graph_h)
            points.append((x, y))

        current = self._history[-1] if self._history else 0
        if current > 80:
            line_color = QColor(colors.ACCENT_RED)
        elif current > 60:
            line_color = QColor(colors.ACCENT_ORANGE)
        elif current > 40:
            line_color = QColor(colors.ACCENT_YELLOW)
        else:
            line_color = QColor(colors.ACCENT_BLUE)

        if len(points) > 1:
            fill_pts = [(points[0][0], pad + graph_h)] + points + [(points[-1][0], pad + graph_h)]

            gradient = QLinearGradient(0, pad, 0, pad + graph_h)
            gradient.setColorAt(0, line_color.lighter(150))
            gradient.setColorAt(1, QColor(colors.BG_CARD))

            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)

            qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
            if len(qpoints) >= 3:
                painter.drawPolygon(*qpoints)

            painter.setPen(QPen(line_color, S.fpx(1.5), Qt.PenStyle.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))

        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(colors.TEXT_SECONDARY))
        painter.drawText(pad + S.px(4), pad + S.px(12), f"Core {self._core_index}")

        painter.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(w - pad - S.px(40), pad + S.px(12), f"{current:.0f}%")

        painter.end()
