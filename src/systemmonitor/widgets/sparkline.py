"""
Sparkline Widget - Mini line charts with gradient fill
"""
from collections import deque
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QSize

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.ui_tick import ui_tick


class SparklineWidget(QWidget, ScaleMixin):
    """
    Mini sparkline chart widget.
    Supports single or multi-line display with gradient fill.
    Auto-scales to max value seen, or use set_max_value() for fixed scale.
    Optimized with throttled repaints.
    """

    def __init__(self, colors=None, max_points=60, parent=None):
        super().__init__(parent)
        self._colors = list(colors) if colors else [theme_manager.colors.ACCENT_BLUE]
        self._max_points = max_points
        self._data = [deque(maxlen=max_points) for _ in self._colors]
        self._max_value = None  # None = auto-scale
        self._fixed_min = 0.0
        self._pending_update = False

        self.scale_connect()
        self.setMinimumHeight(S.px(50))
        self.setMinimumWidth(S.px(100))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Throttle repaints to ~30fps via the shared UI tick instead of a private QTimer
        ui_tick.tick.connect(self._on_tick)

    def _on_tick(self):
        if self._pending_update:
            self._pending_update = False
            self.update()

    def push(self, value):
        """Push a single value to the first line."""
        self._data[0].append(float(value))
        self._auto_scale(value)
        self._pending_update = True

    def push_multi(self, values):
        """Push multiple values, one per line."""
        for i, val in enumerate(values):
            if i < len(self._data):
                self._data[i].append(float(val))
                self._auto_scale(val)
        self._pending_update = True

    def _auto_scale(self, value):
        """Track max value for autoscaling."""
        if self._max_value is None:
            self._max_value = max(value, 1)
        else:
            # Slowly grow max to accommodate spikes
            if value > self._max_value:
                self._max_value = value

    def set_max_value(self, max_val):
        """Set fixed max value (disables autoscaling)."""
        self._max_value = float(max_val)

    def set_min_value(self, min_val):
        """Set fixed min value."""
        self._fixed_min = float(min_val)

    def clear(self):
        """Clear all data."""
        for d in self._data:
            d.clear()
        self._max_value = None
        self._pending_update = True

    def _get_display_max(self):
        """Get the effective max value for scaling."""
        if self._max_value is not None:
            return max(self._max_value, 1.0)
        # Find max across all lines
        max_val = 1.0
        for data in self._data:
            if data:
                max_val = max(max_val, max(data) * 1.2)
        return max_val

    def paintEvent(self, event):
        """Paint the sparkline."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Check we have data
        has_data = any(bool(d) for d in self._data)
        if not has_data:
            painter.end()
            return

        max_val = self._get_display_max()
        y_range = max_val - self._fixed_min
        if y_range <= 0:
            y_range = 1.0

        for data, color in zip(self._data, self._colors):
            if len(data) < 2:
                continue

            points = list(data)

            # Calculate x step
            step_x = width / self._max_points

            # Build coordinates
            coords = []
            for i, val in enumerate(points):
                x = i * step_x
                # Normalize to 0-max range
                normalized = (val - self._fixed_min) / y_range
                y = height - 2 - normalized * (height - 4)
                coords.append((x, max(2.0, y)))

            if len(coords) < 2:
                continue

            # ── Fill area ──────────────────────────────────────────────────
            fill_pts = [(0.0, height)]
            fill_pts.extend(coords)
            fill_pts.append((coords[-1][0], height))

            gradient = QLinearGradient(0, 0, 0, height)
            if theme_manager.current_theme == "heimdal":
                fill_color = QColor("#4A6CF7")
                fill_color.setAlpha(50)
                gradient.setColorAt(0, fill_color)
                gradient.setColorAt(1, Qt.GlobalColor.transparent)
            else:
                fill_color = QColor(color)
                fill_color.setAlpha(50)
                gradient.setColorAt(0, fill_color)
                gradient.setColorAt(1, Qt.GlobalColor.transparent)

            from PyQt6.QtCore import QPoint
            qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
            if len(qpoints) >= 3:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(gradient)
                painter.drawPolygon(*qpoints)

            # ── Line ───────────────────────────────────────────────────────
            line_color = "#4A6CF7" if theme_manager.current_theme == "heimdal" else color
            pen = QPen(QColor(line_color), 1.5)
            painter.setPen(pen)
            for i in range(len(coords) - 1):
                painter.drawLine(
                    int(coords[i][0]), int(coords[i][1]),
                    int(coords[i + 1][0]), int(coords[i + 1][1])
                )

        painter.end()

    def sizeHint(self):
        return QSize(S.px(100), S.px(50))