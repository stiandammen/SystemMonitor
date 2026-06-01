"""
CoreGraphWidget - Per-core CPU usage graph widget
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient, QFont
from PyQt6.QtCore import Qt, pyqtProperty, QRectF, QTimer, QPointF
from typing import List
import math

from systemmonitor.styles.theme import theme_manager


class CoreGraphWidget(QWidget):
    """
    Animated CPU core usage graph with smooth gradient fill
    Optimized with throttled repaints.
    """

    def __init__(self, core_index: int = 0, parent=None):
        super().__init__(parent)
        self._core_index = core_index
        self._history: List[float] = []
        self._max_points = 60  # 60 data points for smooth graph
        self._current_value = 0.0
        self._animation_progress = 1.0
        self._target_value = 0.0
        self._pending_update = False

        # Graph appearance
        self._line_color = theme_manager.colors.ACCENT_BLUE
        self._fill_opacity = 0.4

        self.setMinimumSize(150, 100)
        self.setMaximumHeight(120)

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def set_core_index(self, index: int):
        """Set core number"""
        self._core_index = index
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def add_data_point(self, value: float):
        """Add a new data point with animation"""
        self._target_value = value
        self._history.append(value)

        # Keep history limited
        if len(self._history) > self._max_points:
            self._history.pop(0)

        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def set_value(self, value: float):
        """Set current CPU value"""
        self._current_value = value
        if len(self._history) == 0:
            self._history = [value] * min(10, self._max_points)
        else:
            self._history.append(value)
            if len(self._history) > self._max_points:
                self._history.pop(0)
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def clear_history(self):
        """Clear graph history"""
        self._history = []
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def paintEvent(self, event):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        width = self.width()
        height = self.height()

        # Padding
        pad_left = 5
        pad_right = 5
        pad_top = 5
        pad_bottom = 20

        graph_width = width - pad_left - pad_right
        graph_height = height - pad_top - pad_bottom

        # Draw background
        painter.fillRect(self.rect(), QColor(c.BG_CARD))

        # Draw border/frame
        painter.setPen(QPen(QColor(c.BORDER), 1))
        painter.drawRect(pad_left, pad_top, graph_width, graph_height)

        if not self._history:
            # Draw "No Data" text
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(c.TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Initializing...")
            return

        # Calculate points
        max_val = 100.0
        points = []
        step_x = graph_width / max(len(self._history) - 1, 1)

        for i, val in enumerate(self._history):
            x = pad_left + step_x * i
            y = pad_top + graph_height - (val / max_val * graph_height)
            points.append((x, y))

        # Determine color based on usage
        avg_value = sum(self._history) / len(self._history) if self._history else 0
        if avg_value > 80:
            line_color = QColor(c.ACCENT_RED)
            fill_color = QColor(c.ACCENT_RED)
        elif avg_value > 60:
            line_color = QColor(c.ACCENT_ORANGE)
            fill_color = QColor(c.ACCENT_ORANGE)
        elif avg_value > 40:
            line_color = QColor(c.ACCENT_YELLOW)
            fill_color = QColor(c.ACCENT_YELLOW)
        else:
            line_color = QColor(c.ACCENT_BLUE)
            fill_color = QColor(c.ACCENT_BLUE)

        # Draw fill gradient
        if len(points) > 1:
            fill_path = []
            fill_path.append((points[0][0], pad_top + graph_height))
            fill_path.extend(points)
            fill_path.append((points[-1][0], pad_top + graph_height))

            # Create gradient
            gradient = QLinearGradient(0, pad_top, 0, pad_top + graph_height)
            gradient.setColorAt(0, fill_color.lighter(120).darker(110))
            gradient.setColorAt(0.5, fill_color.lighter(110))
            gradient.setColorAt(1, QColor(c.BG_CARD))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)

            # Draw fill polygon
            qpoints = [QPointF(int(x), int(y)) for x, y in fill_path]
            if len(qpoints) >= 3:
                painter.drawPolygon(*qpoints)

            # Draw line on top
            line_pen = QPen(line_color, 2, Qt.PenStyle.SolidLine)
            line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(line_pen)

            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i + 1][0]), int(points[i + 1][1])
                )

        # Draw core label
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(c.TEXT_SECONDARY))
        label = f"Core {self._core_index}"
        painter.drawText(pad_left + 6, pad_top + 14, label)

        # Draw current value
        if self._history:
            current = self._history[-1]
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QColor(c.TEXT_PRIMARY))
            value_text = f"{current:.0f}%"
            painter.drawText(width - pad_right - 40, pad_top + 14, value_text)

        # Draw Y-axis labels
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor(c.TEXT_MUTED))
        painter.drawText(pad_left + 2, pad_top + graph_height - 2, "0")
        painter.drawText(pad_left + 2, pad_top + 10, "100")

        painter.end()
