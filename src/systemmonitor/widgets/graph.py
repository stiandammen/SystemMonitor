"""
Graph Widget - Premium line/area charts for time-series data
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QLinearGradient, QFont
from PyQt6.QtCore import Qt, QRectF, QTimer, QPointF
from typing import List, Tuple, Optional

from systemmonitor.styles.theme import theme_manager


class Graph(QWidget):
    """
    Premium time-series graph widget with glass styling
    Supports multiple series and automatic scaling
    Optimized with throttled repaints.
    """

    def __init__(self, height: int = 160, fill: bool = True, parent=None):
        super().__init__(parent)
        self._height = height
        self._fill = fill
        self._data: List[Tuple[float, float]] = []
        self._color: str = theme_manager.colors.ACCENT_GREEN
        self._max_value: Optional[float] = None
        self._pending_update = False

        self.setFixedHeight(height)
        self.setMinimumWidth(200)

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def set_data(self, data: List[Tuple[float, float]]):
        """Set graph data as list of (timestamp, value) tuples"""
        self._data = data
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def set_color(self, color: str):
        """Set graph line color"""
        self._color = color
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def set_max_value(self, max_value: float):
        """Set fixed max value (auto-scale if None)"""
        self._max_value = max_value
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def paintEvent(self, event):
        """Paint the premium graph"""
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        width = self.width()
        height = self.height()

        # Calculate bounds
        values = [v for _, v in self._data]
        if not values:
            painter.end()
            return

        min_val = 0
        max_val = self._max_value if self._max_value else max(values) * 1.1
        if max_val == 0:
            max_val = 1

        # Margins
        margin_left = 45
        margin_right = 15
        margin_top = 12
        margin_bottom = 24

        graph_width = width - margin_left - margin_right
        graph_height = height - margin_top - margin_bottom

        # Draw subtle grid lines
        painter.setPen(QPen(QColor(c.CHART_GRID), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = margin_top + (graph_height * i / 4)
            painter.drawLine(int(margin_left), int(y), int(width - margin_right), int(y))

        # Draw Y-axis labels with premium styling
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(c.TEXT_MUTED))
        for i in range(5):
            value = max_val * (4 - i) / 4
            y = margin_top + (graph_height * i / 4)
            label = f"{value:.0f}"
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(label)
            painter.drawText(int(margin_left - text_width - 8), int(y + 4), label)

        # Draw graph line and fill
        if len(self._data) > 1:
            points = []
            for i, (timestamp, value) in enumerate(self._data):
                x = margin_left + (graph_width * i / max(len(self._data) - 1, 1))
                y = margin_top + graph_height - (graph_height * value / max_val)
                points.append((x, y))

            # Draw fill area with gradient
            if self._fill and len(points) > 1:
                fill_path = []
                fill_path.append((points[0][0], margin_top + graph_height))
                fill_path.extend(points)
                fill_path.append((points[-1][0], margin_top + graph_height))

                # Create gradient with Heimdal styling
                gradient = QLinearGradient(0, margin_top, 0, margin_top + graph_height)
                if theme_manager.current_theme == "heimdal":
                    gradient.setColorAt(0, QColor("#4A6CF7"))
                    gradient.setColorAt(0.6, QColor("rgba(74,108,247,0.15)"))
                    gradient.setColorAt(1, QColor("rgba(74,108,247,0.0)"))
                else:
                    gradient.setColorAt(0, QColor(self._color).lighter(130))
                    gradient.setColorAt(0.5, QColor(self._color))
                    gradient.setColorAt(1, QColor(c.BG_PRIMARY))

                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)

                # Draw polygon
                qpoints = [QPointF(int(x), int(y)) for x, y in fill_path]
                if len(qpoints) >= 3:
                    painter.drawPolygon(*qpoints)

            # Draw line
            painter.setPen(QPen(QColor(self._color), 2, Qt.PenStyle.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i + 1][0]), int(points[i + 1][1])
                )

        painter.end()

