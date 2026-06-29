"""
Storage Widgets - Professional storage monitoring UI components
Enterprise-grade design with real-time graphs and metrics
"""
import math
import re
from typing import Optional, List, Dict, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, pyqtSignal, QPoint,
    pyqtProperty, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.helpers import format_temperature
from systemmonitor.i18n import tr, I18nMixin


def c():
    """Access theme colors - shorthand for cleaner code"""
    return theme_manager.colors


# ---------------------------------------------------------------------------
# AnimatedProgressBar
# ---------------------------------------------------------------------------
class AnimatedProgressBar(QWidget):
    """
    Custom progress bar with smooth animation and colored gradient fill.
    Uses QPropertyAnimation on a 'progress' float property.
    """

    def __init__(self, color: str = "#10b981", parent=None):
        super().__init__(parent)
        self._progress: float = 0.0
        self._color: str = color
        self.setFixedHeight(S.px(7))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(900)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # --- pyqtProperty ---
    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float):
        self._progress = max(0.0, min(100.0, value))
        self.update()

    progress = pyqtProperty(float, fget=_get_progress, fset=_set_progress)

    def set_value(self, percent: float, color: str = None):
        """Animate to new percentage value, optionally changing bar color."""
        if color is not None:
            self._color = color
        if self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(max(0.0, min(100.0, percent)))
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        w = self.width()
        h = self.height()
        radius = h / 2

        # Background track
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Filled portion
        fill_w = int(w * self._progress / 100.0)
        if fill_w > 0:
            base_color = QColor(self._color)
            lighter = base_color.lighter(140)
            gradient = QLinearGradient(0, 0, fill_w, 0)
            gradient.setColorAt(0.0, lighter)
            gradient.setColorAt(1.0, base_color)
            painter.setBrush(gradient)
            painter.drawRoundedRect(0, 0, fill_w, h, radius, radius)

        painter.end()


# ---------------------------------------------------------------------------
# DiskUsageRing  – animated circular arc gauge with glow
# ---------------------------------------------------------------------------
class DiskUsageRing(QWidget):
    """
    Animated circular ring showing disk usage percentage.
    Uses QPropertyAnimation + QConicalGradient for a glowing sweep effect.
    InElastic easing gives a satisfying 'snap' when value changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ring_val: float = 0.0
        sz = S.px(108)
        self.setFixedSize(sz, sz)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._anim = QPropertyAnimation(self, b"ring_value")
        self._anim.setDuration(1100)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)

        theme_manager.theme_changed.connect(self.update)

    # --- animated property ---
    def _get_ring_value(self) -> float:
        return self._ring_val

    def _set_ring_value(self, v: float):
        self._ring_val = max(0.0, min(100.0, v))
        self.update()

    ring_value = pyqtProperty(float, fget=_get_ring_value, fset=_set_ring_value)

    def set_usage(self, percent: float):
        if self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        self._anim.setStartValue(self._ring_val)
        self._anim.setEndValue(max(0.0, min(100.0, percent)))
        self._anim.start()

    def _arc_color(self, v: float) -> QColor:
        colors = c()
        if v >= 90:
            return QColor(colors.ACCENT_RED)
        elif v >= 75:
            return QColor(colors.ACCENT_ORANGE)
        return QColor(colors.ACCENT_GREEN)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        w, h = self.width(), self.height()
        thickness = max(S.px(9), 9)
        margin = thickness // 2 + S.px(4)
        rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)

        # Background ring
        bg_pen = QPen(QColor(colors.BG_HOVER), thickness)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect.toRect(), 0, 360 * 16)

        val = self._ring_val
        if val > 0.5:
            span = int((val / 100.0) * 360 * 16)
            fill = self._arc_color(val)

            # Outer glow layer
            glow = QColor(fill)
            glow.setAlpha(35)
            glow_pen = QPen(glow, thickness + S.px(6))
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(rect.toRect(), 90 * 16, -span)

            # Mid glow layer
            glow2 = QColor(fill)
            glow2.setAlpha(60)
            glow_pen2 = QPen(glow2, thickness + S.px(2))
            glow_pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen2)
            painter.drawArc(rect.toRect(), 90 * 16, -span)

            # Main arc
            main_pen = QPen(fill, thickness)
            main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(main_pen)
            painter.drawArc(rect.toRect(), 90 * 16, -span)

        # Center: percentage text
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        font = QFont("Segoe UI", S.font_pt(14), QFont.Weight.Bold)
        painter.setFont(font)
        pct_str = f"{val:.0f}%"
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(pct_str)
        th = fm.ascent()
        painter.drawText(int(w / 2 - tw / 2), int(h / 2 + th / 3), pct_str)

        painter.end()


# ---------------------------------------------------------------------------
# LiveGraphWidget
# ---------------------------------------------------------------------------
class LiveGraphWidget(QWidget):
    """
    Smooth live-updating line/area graph for read/write speeds.
    Professional gradient fills with glow effects.
    """
    def __init__(self, max_points: int = 60, parent=None):
        super().__init__(parent)
        self._max_points = max_points
        self._read_history: List[float] = []
        self._write_history: List[float] = []
        self._read_max = 100_000_000  # Normalize to 100 MB/s full scale
        self.setMinimumHeight(S.px(70))
        self.setMaximumHeight(S.px(90))
        theme_manager.theme_changed.connect(self.update)

    def set_speeds(self, read_bps: float, write_bps: float):
        """Add new speed data point"""
        self._read_history.append(max(0, read_bps))
        self._write_history.append(max(0, write_bps))

        if len(self._read_history) > self._max_points:
            self._read_history.pop(0)
        if len(self._write_history) > self._max_points:
            self._write_history.pop(0)

        current_max = max(
            max(self._read_history) if self._read_history else 1,
            max(self._write_history) if self._write_history else 1,
            1024 * 1024
        )
        if current_max > self._read_max * 1.2:
            self._read_max = current_max * 1.5
        elif len(self._read_history) > 10 and current_max < self._read_max * 0.5:
            self._read_max = max(current_max * 2, 100_000_000)

        self.update()

    def clear(self):
        """Clear all history"""
        self._read_history.clear()
        self._write_history.clear()
        self.update()

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to human readable"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            painter.end()
            return

        # Background
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 4, 4)

        if not self._read_history and not self._write_history:
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(w // 2 - 25, h // 2 + 4, tr("Waiting for data..."))
            painter.end()
            return

        # Draw grid lines
        painter.setPen(QPen(QColor(colors.BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = h * i // 4
            painter.drawLine(0, y, w, y)

        step_w = w / self._max_points

        # Draw read line (green)
        if len(self._read_history) > 1:
            self._draw_graph(painter, self._read_history, step_w, h, colors.ACCENT_GREEN, True)

        # Draw write line (blue)
        if len(self._write_history) > 1:
            self._draw_graph(painter, self._write_history, step_w, h, colors.ACCENT_BLUE, False)

        # Current values in corner
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        read_text = f"↓ {self._format_speed(self._read_history[-1] if self._read_history else 0)}"
        write_text = f"↑ {self._format_speed(self._write_history[-1] if self._write_history else 0)}"

        painter.setPen(QColor(colors.ACCENT_GREEN))
        painter.drawText(8, 14, read_text)
        painter.setPen(QColor(colors.ACCENT_BLUE))
        painter.drawText(8, 28, write_text)

        painter.end()

    def _draw_graph(self, painter: QPainter, points: List[float], step_w: float, h: float, color: str, is_read: bool):
        """Draw a smooth graph line with proper gradient fill"""
        if len(points) < 2:
            return

        # Build path points
        path_points = []
        for i, val in enumerate(points):
            x = i * step_w
            y = h - (val / self._read_max) * (h - 8)
            y = max(4, min(h - 4, y))
            path_points.append((x, y))

        # Gradient fill
        fill_path = QPainterPath()
        fill_path.moveTo(0, h)
        for x, y in path_points:
            fill_path.lineTo(x, y)
        fill_path.lineTo((len(points) - 1) * step_w, h)
        fill_path.closeSubpath()

        fill_color = QColor(color)
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, fill_color.lighter(130))
        gradient.setColorAt(0.5, fill_color)
        gradient.setColorAt(1, fill_color)
        painter.setOpacity(0.25 if not is_read else 0.3)
        painter.fillPath(fill_path, QColor(color))
        painter.setOpacity(1.0)

        # Draw line
        line_path = QPainterPath()
        for i, (x, y) in enumerate(path_points):
            if i == 0:
                line_path.moveTo(x, y)
            else:
                line_path.lineTo(x, y)

        painter.setPen(QPen(QColor(color), 2))
        painter.drawPath(line_path)


class PerformanceHistoryGraph(QWidget):
    """
    Dashboard-style time-series graph with Y-axis labels, grid lines,
    gradient area fill, scatter-dot mode, and per-series min/max/avg legend.
    """

    _ML = 52   # left margin: Y-axis label area
    _MR = 10   # right margin
    _MT = 26   # top margin: title
    _MB = 60   # bottom margin: 2-row legend

    def __init__(self, title: str, unit: str = '', max_points: int = 90, parent=None):
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._max_points = max_points
        self._sample_stride = 1
        self._sample_skip = 0
        self._series: Dict[str, dict] = {}  # name -> {data, color, mode}
        self.setMinimumHeight(S.px(170))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        theme_manager.theme_changed.connect(self.update)

    def add_series(self, name: str, color: str, mode: str = 'line'):
        """Add a named data series. mode: 'line' (area fill) or 'scatter' (dots)."""
        self._series[name] = {'data': [], 'color': color, 'mode': mode}

    def set_max_points(self, max_points: int):
        """Resize all series buffers (e.g. from the History Length setting)"""
        self._max_points = max(1, int(max_points))
        for series in self._series.values():
            data = series['data']
            if len(data) > self._max_points:
                series['data'] = data[-self._max_points:]

    def set_sample_stride(self, stride: int):
        """Keep only every Nth incoming sample (applied uniformly across all
        series so they stay aligned in time) so a fixed-size buffer can span
        a longer time window (e.g. from the History Length setting)."""
        self._sample_stride = max(1, int(stride))
        self._sample_skip = 0

    def push(self, **values: float):
        """Push new values: push(Read=1024.0, Write=512.0)."""
        self._sample_skip += 1
        if self._sample_skip < self._sample_stride:
            return
        self._sample_skip = 0
        for k, v in values.items():
            if k in self._series:
                d = self._series[k]['data']
                d.append(max(0.0, float(v)))
                if len(d) > self._max_points:
                    d.pop(0)
        self.update()

    # ── paint ─────────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w, h = self.width(), self.height()

        ml = S.px(self._ML)
        mr = S.px(self._MR)
        mt = S.px(self._MT)
        mb = S.px(self._MB)
        pw = w - ml - mr
        ph = h - mt - mb

        # Card background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors.BG_CARD))
        painter.drawRoundedRect(0, 0, w, h, S.px(8), S.px(8))

        if pw <= 10 or ph <= 10:
            painter.end()
            return

        # Title
        painter.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_SECONDARY))
        painter.drawText(S.px(8), S.px(17), tr(self._title))

        # Gather all data for Y scale
        all_vals = [v for s in self._series.values() for v in s['data']]
        if not all_vals:
            painter.setFont(QFont("Segoe UI", S.font_pt(8)))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(ml + pw // 2 - S.px(50), mt + ph // 2 + S.px(4), tr("Waiting for data..."))
            painter.end()
            return

        y_max = self._nice_max(max(max(all_vals) * 1.1, 0.001))
        y_min = 0.0
        y_rng = y_max - y_min

        # Y-axis grid labels (5 lines including 0)
        N_GRID = 4
        for i in range(N_GRID + 1):
            frac = i / N_GRID
            val  = y_min + y_rng * frac
            gy   = mt + ph - int(ph * frac)
            label = self._fmt_val(val)
            painter.setFont(QFont("Segoe UI", S.font_pt(7)))
            painter.setPen(QColor(colors.TEXT_MUTED))
            fm = painter.fontMetrics()
            lw = fm.horizontalAdvance(label)
            painter.drawText(ml - lw - S.px(5), gy + fm.ascent() // 2, label)
            # Dotted grid line
            pen = QPen(QColor(colors.BORDER), 1, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawLine(ml, gy, ml + pw, gy)

        # Plot area clipping
        painter.setClipRect(ml, mt, pw, ph)
        step = pw / self._max_points

        for s in self._series.values():
            data = s['data']
            col  = QColor(s['color'])
            mode = s['mode']
            n    = len(data)
            if n == 0:
                continue

            offset = self._max_points - n
            pts: List[Tuple[float, float]] = []
            for i, v in enumerate(data):
                x = ml + (offset + i) * step
                frac = (v - y_min) / y_rng if y_rng > 0 else 0.0
                y = mt + ph - frac * ph
                y = max(float(mt), min(float(mt + ph), y))
                pts.append((x, y))

            if mode == 'scatter':
                r = S.px(2)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(col)
                for x, y in pts:
                    painter.drawEllipse(int(x - r), int(y - r), r * 2, r * 2)
            else:
                # Gradient area fill
                if len(pts) >= 2:
                    fill_path = QPainterPath()
                    fill_path.moveTo(pts[0][0], mt + ph)
                    for x, y in pts:
                        fill_path.lineTo(x, y)
                    fill_path.lineTo(pts[-1][0], mt + ph)
                    fill_path.closeSubpath()
                    grad = QLinearGradient(0.0, float(mt), 0.0, float(mt + ph))
                    top_c = QColor(col); top_c.setAlpha(60)
                    bot_c = QColor(col); bot_c.setAlpha(6)
                    grad.setColorAt(0.0, top_c)
                    grad.setColorAt(1.0, bot_c)
                    painter.setBrush(grad)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(fill_path)
                # Line
                if len(pts) >= 2:
                    line_path = QPainterPath()
                    line_path.moveTo(*pts[0])
                    for x, y in pts[1:]:
                        line_path.lineTo(x, y)
                    painter.setPen(QPen(col, 1.5))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPath(line_path)

        painter.setClipping(False)

        # Legend: one row per series, stacked at the bottom
        leg_top = h - mb + S.px(10)
        row_h   = S.px(20)
        for idx, (name, s) in enumerate(self._series.items()):
            data = s['data']
            col  = QColor(s['color'])
            row_y = leg_top + idx * row_h

            # Color swatch
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(col)
            painter.drawRect(ml, row_y + S.px(5), S.px(14), S.px(3))

            painter.setFont(QFont("Segoe UI", S.font_pt(8)))
            fm = painter.fontMetrics()
            tx = ml + S.px(18)
            ty = row_y + fm.ascent()

            # Series name
            disp_name = tr(name)
            painter.setPen(QColor(colors.TEXT_SECONDARY))
            painter.drawText(tx, ty, disp_name)
            tx += fm.horizontalAdvance(disp_name) + S.px(10)

            # min / max / avg
            if data:
                mn  = min(data)
                mx  = max(data)
                avg = sum(data) / len(data)
                stats = (f"min {self._fmt_val(mn)}"
                         f"   max {self._fmt_val(mx)}"
                         f"   avg {self._fmt_val(avg)}")
                painter.setPen(QColor(colors.TEXT_MUTED))
                painter.drawText(tx, ty, stats)

        painter.end()

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _nice_max(v: float) -> float:
        """Round up to a clean scale ceiling."""
        if v <= 0:
            return 1.0
        exp  = math.floor(math.log10(v))
        base = 10 ** exp
        frac = v / base
        if frac <= 1:  return base
        if frac <= 2:  return 2 * base
        if frac <= 5:  return 5 * base
        return 10 * base

    def _fmt_val(self, val: float) -> str:
        """Format a value with appropriate unit suffix for Y-axis / legend."""
        u = self._unit
        if u == 'ms':
            if val <= 0:       return "0"
            if val < 0.001:    return f"{val * 1_000_000:.0f} ns"
            if val < 1:        return f"{val * 1000:.2f} µs"
            if val < 10:       return f"{val:.2f} ms"
            return f"{val:.1f} ms"
        if u == 'iops':
            if val >= 1_000_000: return f"{val / 1_000_000:.1f}M"
            if val >= 1_000:     return f"{val / 1_000:.1f}k"
            return f"{val:.0f}"
        if u == 'B/s':
            if val >= 1_073_741_824: return f"{val / 1_073_741_824:.1f} GB"
            if val >= 1_048_576:     return f"{val / 1_048_576:.0f} MB"
            if val >= 1_024:         return f"{val / 1_024:.0f} KB"
            return f"{val:.0f} B"
        if u == '%':
            return f"{val:.0f}%"
        return f"{val:.2f}"


class TemperatureGauge(QWidget):
    """
    Circular temperature gauge with color-coded status.
    Shows temperature with normal/warning/critical zones.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp: float = 0
        self.setFixedSize(S.px(64), S.px(64))
        theme_manager.theme_changed.connect(self.update)

    def set_temperature(self, temp_c: float):
        """Set temperature in Celsius"""
        self._temp = max(0, min(120, temp_c))
        self.update()

    def _get_status_color(self) -> QColor:
        colors = c()
        if self._temp >= 85:
            return QColor(colors.ACCENT_RED)
        elif self._temp >= 70:
            return QColor(colors.ACCENT_ORANGE)
        return QColor(colors.ACCENT_GREEN)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        size = min(self.width(), self.height())
        center = size / 2
        radius = size / 2 - 6

        # Background arc
        bg_rect = QRectF(center - radius, center - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor(colors.BG_HOVER), 5))
        painter.drawArc(bg_rect.toRect(), 135 * 16, 270 * 16)

        # Temperature arc
        if self._temp > 0:
            temp_angle = min(270, (self._temp / 100) * 270)
            status_color = self._get_status_color()
            painter.setPen(QPen(status_color, 5, cap=Qt.PenCapStyle.RoundCap))
            painter.drawArc(bg_rect.toRect(), 135 * 16, -int(temp_angle) * 16)

        # Temperature text
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        temp_text = f"{self._temp:.0f}°"
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(temp_text)
        painter.drawText(int(center - text_w / 2), int(center + 4), temp_text)

        painter.end()


class TemperatureBar(QWidget):
    """
    Linear temperature bar with color-coded status.
    Clean horizontal bar with gradient fill.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp: float = 0
        self._has_data: bool = False
        self.setFixedHeight(S.px(28))
        theme_manager.theme_changed.connect(self.update)

    def set_temperature(self, temp_c):
        """Set temperature in Celsius (None or <=0 shows N/A)"""
        if temp_c is None or float(temp_c) <= 0:
            self._temp = 0
            self._has_data = False
        else:
            self._temp = max(0, min(120, float(temp_c)))
            self._has_data = True
        self.update()

    def _get_status_color(self) -> QColor:
        colors = c()
        if self._temp >= 85:
            return QColor(colors.ACCENT_RED)
        elif self._temp >= 70:
            return QColor(colors.ACCENT_ORANGE)
        return QColor(colors.ACCENT_GREEN)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        if not self._has_data:
            painter.setFont(QFont("Segoe UI", 10))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(0, 18, "N/A")
            painter.end()
            return

        bar_h = 6
        bar_y = 11
        bar_w = self.width() - 50
        bar_x = 44

        # Background
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_w), bar_h, 3, 3)

        # Fill
        fill_w = int((self._temp / 100) * bar_w)
        if fill_w > 0:
            status_color = self._get_status_color()
            painter.setBrush(status_color)
            painter.drawRoundedRect(int(bar_x), int(bar_y), fill_w, bar_h, 3, 3)

        # Label
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(0, int(bar_y + 14), format_temperature(self._temp))

        # Status dot
        icon_x = bar_x + bar_w + 8
        status_color = self._get_status_color()
        painter.setBrush(status_color)
        painter.drawEllipse(int(icon_x), int(bar_y), 8, 8)

        painter.end()


class SMARTStatusWidget(QWidget):
    """
    Widget displaying SMART status information.
    Shows health, wear level, and other SMART attributes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._smart_data: Optional[Dict] = None
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build SMART status widget layout"""
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Title
        title = QLabel("SMART Health")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        main_layout.addWidget(title)

        # Health status
        self._health_label = QLabel("Unknown")
        self._health_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        main_layout.addWidget(self._health_label)

        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)
        main_layout.addLayout(stats_layout)

        self._create_stat_item("Power On", "h", "power_on_hours", stats_layout)
        self._create_stat_item("Cycles", "", "power_cycle_count", stats_layout)
        self._create_stat_item("Bad Sectors", "", "bad_sectors", stats_layout)
        self._create_stat_item("Wear Level", "%", "wear_level", stats_layout)

    def _create_stat_item(self, label: str, unit: str, key: str, layout: QGridLayout):
        """Create a stat display item"""
        colors = c()

        label_w = QLabel(label)
        label_w.setFont(QFont("Segoe UI", 8))
        label_w.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")

        value_w = QLabel("--" if unit else "")
        value_w.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        value_w.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        value_w.setObjectName(f"smart_{key}")

        row = layout.rowCount()
        layout.addWidget(label_w, row, 0)
        layout.addWidget(value_w, row, 1)

    def set_smart_data(self, smart_data: Optional[Dict]):
        """Update SMART data"""
        self._smart_data = smart_data
        self._update_display()

    def _update_display(self):
        """Update SMART data display"""
        colors = c()

        if not self._smart_data:
            self._health_label.setText("N/A")
            self._health_label.setStyleSheet(f"color: {colors.TEXT_MUTED};")
            return

        health = self._smart_data.get('health', 'Unknown')
        self._health_label.setText(health)

        if health in ['OK', 'Healthy', 'Good']:
            health_color = colors.ACCENT_GREEN
        elif health in ['Warning', 'Caution']:
            health_color = colors.ACCENT_ORANGE
        else:
            health_color = colors.TEXT_SECONDARY

        self._health_label.setStyleSheet(f"color: {health_color};")

        stat_mappings = [
            ('power_on_hours', 'h'),
            ('power_cycle_count', ''),
            ('bad_sectors', ''),
            ('wear_level', '%'),
        ]

        for key, unit in stat_mappings:
            value = self._smart_data.get(key)
            label = self.findChild(QLabel, f"smart_{key}")
            if label:
                if value is not None:
                    label.setText(f"{value}{unit}")
                else:
                    label.setText("--")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        self._setup_ui()
        self._update_display()


class StorageDiskCard(QFrame, I18nMixin):
    """
    Professional disk panel: compact header row + partition usage table +
    live IO graph column. Left accent border color-coded by disk type.
    Hover tint and smooth bar animations. Partition rows update in-place.
    """
    disk_selected = pyqtSignal(str)
    _BORDER_W = 4

    def __init__(self, disk_info: Dict, parent=None):
        super().__init__(parent)
        self._disk_info = disk_info
        self._read_speed: float = 0.0
        self._write_speed: float = 0.0
        self._hover: bool = False
        self._io_graph: Optional[LiveGraphWidget] = None
        self._icon_label: Optional[QLabel] = None
        self._part_rows: List[Tuple] = []   # (bar, pct_lbl, sz_lbl) per partition
        self._agg_bar: Optional[AnimatedProgressBar] = None
        self._agg_pct_lbl: Optional[QLabel] = None
        self.setMouseTracking(True)
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def retranslate_ui(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    # ── hover ─────────────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ── paint: left accent border + header gradient + hover tint ──────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        bw = S.px(self._BORDER_W)
        r  = S.px(10)
        w, h = self.width(), self.height()
        bc  = QColor(self._get_type_color())

        # Left accent strip
        painter.save()
        painter.setClipRect(0, 0, bw, h)
        painter.setBrush(bc)
        painter.drawRoundedRect(0, 0, r * 2, h, r, r)
        painter.restore()

        # Subtle horizontal gradient behind the header area
        hdr_h = S.px(42)
        grad = QLinearGradient(float(bw), 0.0, float(bw + S.px(220)), 0.0)
        s_col = QColor(bc); s_col.setAlpha(18)
        e_col = QColor(bc); e_col.setAlpha(0)
        grad.setColorAt(0.0, s_col)
        grad.setColorAt(1.0, e_col)
        painter.setBrush(QBrush(grad))
        painter.drawRect(bw, 0, w - bw, hdr_h)

        if self._hover:
            hov = QColor(bc); hov.setAlpha(8)
            painter.setBrush(hov)
            painter.drawRoundedRect(0, 0, w, h, r, r)

        painter.end()

    # ── layout ────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        self._part_rows.clear()
        self._agg_bar = None
        self._agg_pct_lbl = None
        self._io_graph = None

        colors = c()
        bw = S.px(self._BORDER_W)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: {S.px(10)}px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        main = QVBoxLayout()
        main.setSpacing(0)
        main.setContentsMargins(bw + S.px(12), S.px(10), S.px(14), S.px(10))
        self.setLayout(main)

        # ── HEADER ROW ───────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(S.px(9))
        hdr.setContentsMargins(0, 0, 0, 0)

        # Disk icon
        self._icon_label = QLabel()
        try:
            ico = qta.icon(self._get_disk_icon_name(), color=self._get_type_color())
            self._icon_label.setPixmap(ico.pixmap(S.px(20), S.px(20)))
        except Exception:
            self._icon_label.setText("")
        self._icon_label.setStyleSheet("background: transparent;")
        self._icon_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hdr.addWidget(self._icon_label)

        # Disk name
        name_lbl = QLabel(self._get_disk_title())
        name_lbl.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        name_lbl.setStyleSheet(
            f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        hdr.addWidget(name_lbl)

        # Type badge — outlined pill
        dtype = self._disk_info.get('disk_type', '?')
        tc = self._get_type_color()
        tc_qc = QColor(tc)
        tc_dim = f"rgba({tc_qc.red()},{tc_qc.green()},{tc_qc.blue()},0.15)"
        badge = QLabel(f" {dtype} ")
        badge.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {tc_dim};
                color: {tc};
                border: 1px solid {tc};
                border-radius: {S.px(3)}px;
                padding: 0px {S.px(5)}px;
            }}
        """)
        hdr.addWidget(badge)

        # Interface type tag
        iface = self._disk_info.get('interface_type', '')
        if iface and iface not in ('Unknown', ''):
            iface_lbl = QLabel(iface)
            iface_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
            iface_lbl.setStyleSheet(
                f"color: {colors.TEXT_MUTED}; background: transparent;")
            hdr.addWidget(iface_lbl)

        # Model (truncated)
        model = self._disk_info.get('model', '')
        if model and model not in ('Unknown', 'Unknown Model'):
            short = (model[:26] + "…") if len(model) > 26 else model
            mdl_lbl = QLabel(short)
            mdl_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
            mdl_lbl.setStyleSheet(
                f"color: {colors.TEXT_MUTED}; background: transparent;")
            hdr.addWidget(mdl_lbl)

        hdr.addStretch()

        # Total capacity
        cap_lbl = QLabel(self._get_total_capacity())
        cap_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        cap_lbl.setStyleSheet(
            f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        hdr.addWidget(cap_lbl)

        # Status dot
        status = self._disk_info.get('status', 'OK')
        dot = QFrame()
        dot.setFixedSize(S.px(8), S.px(8))
        dot_col = colors.ACCENT_GREEN if status in ('OK', '', 'Unknown') else colors.ACCENT_ORANGE
        dot.setStyleSheet(
            f"background-color: {dot_col}; border-radius: {S.px(4)}px; border: none;")
        hdr.addWidget(dot)

        main.addLayout(hdr)
        main.addSpacing(S.px(8))

        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colors.BORDER}; border: none;")
        main.addWidget(sep)
        main.addSpacing(S.px(8))

        # ── BODY: partition table (left) + IO graph (right) ──────────────────
        body = QHBoxLayout()
        body.setSpacing(S.px(16))
        body.setContentsMargins(0, 0, 0, 0)

        # Left column: partition rows
        part_col = QVBoxLayout()
        part_col.setSpacing(S.px(6))
        part_col.setContentsMargins(0, 0, 0, 0)

        partitions = self._disk_info.get('partitions', [])

        if partitions:
            for part in partitions:
                row_lay = self._build_partition_row(part, colors)
                part_col.addLayout(row_lay)
        else:
            # No partition data — show aggregate bar
            pct = self._get_usage_percent()
            col = self._get_usage_color()

            row_lay = QHBoxLayout()
            row_lay.setSpacing(S.px(8))

            self._agg_bar = AnimatedProgressBar(color=col)
            self._agg_bar.setFixedHeight(S.px(6))
            self._agg_bar.set_value(pct)
            row_lay.addWidget(self._agg_bar, stretch=1)

            self._agg_pct_lbl = QLabel(f"{pct:.0f}%")
            self._agg_pct_lbl.setFixedWidth(S.px(34))
            self._agg_pct_lbl.setFont(
                QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
            self._agg_pct_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._agg_pct_lbl.setStyleSheet(
                f"color: {col}; background: transparent;")
            row_lay.addWidget(self._agg_pct_lbl)

            sz_lbl = QLabel(
                f"{self._fmt_size(self._disk_info.get('used', 0))} / "
                f"{self._fmt_size(self._disk_info.get('total', 0))}")
            sz_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
            sz_lbl.setStyleSheet(
                f"color: {colors.TEXT_SECONDARY}; background: transparent;")
            row_lay.addWidget(sz_lbl)
            row_lay.addStretch()

            part_col.addLayout(row_lay)

        body.addLayout(part_col, stretch=1)

        # Right column: compact IO graph
        io_frame = QWidget()
        io_frame.setFixedWidth(S.px(170))
        io_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        io_lay = QVBoxLayout(io_frame)
        io_lay.setContentsMargins(0, 0, 0, 0)
        io_lay.setSpacing(0)

        self._io_graph = LiveGraphWidget(max_points=40)
        self._io_graph.setMinimumHeight(S.px(52))
        self._io_graph.setMaximumHeight(S.px(64))
        io_lay.addWidget(self._io_graph)

        body.addWidget(io_frame)
        main.addLayout(body)
        main.addSpacing(S.px(7))

        # ── FOOTER: fstype · serial ───────────────────────────────────────────
        footer_parts: List[str] = []
        fstype_set = {
            p.get('fstype', '') for p in partitions
            if p.get('fstype') and p.get('fstype') not in ('Unknown', '')
        }
        if fstype_set:
            footer_parts.append("  ·  ".join(sorted(fstype_set)))
        serial = str(self._disk_info.get('serial', '') or '').strip()
        if serial and serial not in ('N/A', 'None', ''):
            footer_parts.append(f"SN: {serial[:14]}")

        if footer_parts:
            foot_lbl = QLabel("    ·    ".join(footer_parts))
            foot_lbl.setFont(QFont("Segoe UI", S.font_pt(7)))
            foot_lbl.setStyleSheet(
                f"color: {colors.TEXT_MUTED}; background: transparent;")
            main.addWidget(foot_lbl)

    def _build_partition_row(self, part: Dict, colors) -> QHBoxLayout:
        """Construct one partition row and register its live-update refs."""
        pct = float(part.get('percent', 0))
        col = self._part_color(pct)

        row = QHBoxLayout()
        row.setSpacing(S.px(8))
        row.setContentsMargins(0, 0, 0, 0)

        # Drive letter / mountpoint (e.g. "C:" or "/")
        mp = (part.get('mountpoint') or part.get('device') or '?').strip()
        mp = mp.rstrip('\\').rstrip('/')
        letter = mp[-2:] if len(mp) >= 2 else mp
        letter_lbl = QLabel(letter)
        letter_lbl.setFixedWidth(S.px(24))
        letter_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        letter_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        row.addWidget(letter_lbl)

        # Usage progress bar
        bar = AnimatedProgressBar(color=col)
        bar.setFixedHeight(S.px(6))
        bar.set_value(pct)
        row.addWidget(bar, stretch=1)

        # Percentage label
        pct_lbl = QLabel(f"{pct:.0f}%")
        pct_lbl.setFixedWidth(S.px(34))
        pct_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        pct_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        row.addWidget(pct_lbl)

        # Used / total size
        sz_lbl = QLabel(
            f"{self._fmt_size(part.get('used', 0))} / "
            f"{self._fmt_size(part.get('total', 0))}")
        sz_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        sz_lbl.setStyleSheet(
            f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        sz_lbl.setMinimumWidth(S.px(92))
        row.addWidget(sz_lbl)

        self._part_rows.append((bar, pct_lbl, sz_lbl))
        return row

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_disk_icon_name(self) -> str:
        t = self._disk_info.get('disk_type', 'Unknown')
        if t == 'NVMe': return 'mdi.expansion'
        if t == 'SSD':  return 'fa5s.hdd'
        return 'mdi.harddisk'

    def _get_disk_title(self) -> str:
        device = self._disk_info.get('device', '')
        name   = self._disk_info.get('name',   '')
        # Extract trailing digit(s): handles "\\.\0", "\\.\PHYSICALDRIVE0", etc.
        for src in (device, name):
            if src:
                m = re.search(r'(\d+)\s*$', src)
                if m:
                    return f"Disk {m.group(1)}"
        if name and name not in ('Unknown',) and not name.startswith('\\\\'):
            return name
        return tr("Unknown Disk")

    def _get_type_color(self) -> str:
        colors = c()
        t = self._disk_info.get('disk_type', 'Unknown')
        if t == 'NVMe': return colors.ACCENT_PURPLE
        if t == 'SSD':  return colors.ACCENT_BLUE
        if t == 'HDD':  return colors.ACCENT_ORANGE
        return colors.TEXT_MUTED

    def _get_usage_percent(self) -> float:
        partitions = self._disk_info.get('partitions', [])
        if partitions:
            total = sum(p.get('total', 0) for p in partitions)
            used  = sum(p.get('used',  0) for p in partitions)
            return (used / total * 100.0) if total > 0 else 0.0
        return float(self._disk_info.get('percent', 0))

    def _get_usage_color(self) -> str:
        return self._part_color(self._get_usage_percent())

    @staticmethod
    def _part_color(pct: float) -> str:
        colors = c()
        if pct >= 90: return colors.ACCENT_RED
        if pct >= 75: return colors.ACCENT_ORANGE
        return colors.ACCENT_GREEN

    def _get_total_capacity(self) -> str:
        size_b = self._disk_info.get('size', 0)
        if not size_b:
            size_b = sum(
                p.get('total', 0) for p in self._disk_info.get('partitions', []))
        if not size_b:
            size_b = self._disk_info.get('total', 0)
        return self._fmt_size(size_b)

    @staticmethod
    def _fmt_size(b: int) -> str:
        if b >= 1_099_511_627_776:
            return f"{b / 1_099_511_627_776:.1f} TB"
        if b >= 1_073_741_824:
            return f"{b / 1_073_741_824:.0f} GB"
        if b >= 1_048_576:
            return f"{b / 1_048_576:.0f} MB"
        return f"{b} B"

    def _format_speed(self, bps: float) -> str:
        if bps >= 1_073_741_824: return f"{bps / 1_073_741_824:.2f} GB/s"
        if bps >= 1_048_576:     return f"{bps / 1_048_576:.0f} MB/s"
        if bps >= 1024:           return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    # ── public update API ─────────────────────────────────────────────────────

    def update_disk_info(self, disk_info: Dict):
        """Update live elements. Rebuilds layout only when partition count changes."""
        old_parts = self._disk_info.get('partitions', [])
        new_parts = disk_info.get('partitions', [])
        self._disk_info = disk_info

        if len(new_parts) != len(old_parts):
            self._setup_ui()
            return

        if new_parts and self._part_rows:
            for i, part in enumerate(new_parts):
                if i >= len(self._part_rows):
                    break
                bar, pct_lbl, sz_lbl = self._part_rows[i]
                pct = float(part.get('percent', 0))
                col = self._part_color(pct)
                bar.set_value(pct, col)
                pct_lbl.setText(f"{pct:.0f}%")
                pct_lbl.setStyleSheet(f"color: {col}; background: transparent;")
                sz_lbl.setText(
                    f"{self._fmt_size(part.get('used', 0))} / "
                    f"{self._fmt_size(part.get('total', 0))}")
        elif self._agg_bar is not None:
            pct = self._get_usage_percent()
            col = self._get_usage_color()
            self._agg_bar.set_value(pct, col)
            if self._agg_pct_lbl:
                self._agg_pct_lbl.setText(f"{pct:.0f}%")
                self._agg_pct_lbl.setStyleSheet(
                    f"color: {col}; background: transparent;")

    def update_speeds(self, read_bps: float, write_bps: float):
        self._read_speed  = read_bps
        self._write_speed = write_bps
        if self._io_graph is not None:
            self._io_graph.set_speeds(read_bps, write_bps)

    def _on_theme_changed(self, _):
        self._setup_ui()


class StorageOverviewCard(QFrame):
    """
    Compact storage overview card for dashboard.
    Shows total usage and aggregate speeds with professional styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._total_used = 0
        self._total_free = 0
        self._total_size = 0
        self._read_speed = 0.0
        self._write_speed = 0.0
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build overview card layout"""
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = c()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(S.px(10))
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self.setLayout(main_layout)

        # Title row with icon
        title_row = QHBoxLayout()
        title_row.setSpacing(S.px(8))

        # Storage icon
        icon_label = QLabel()
        try:
            icon = qta.icon('mdi.database', color=colors.ACCENT_BLUE, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(18), S.px(18)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        title_row.addWidget(icon_label)

        title = QLabel("Storage Overview")
        title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_row.addWidget(title)

        title_row.addStretch()
        main_layout.addLayout(title_row)

        # Usage bar
        self._usage_bar = QProgressBar()
        self._usage_bar.setFixedHeight(S.px(10))
        self._usage_bar.setTextVisible(False)
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_HOVER};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {colors.ACCENT_BLUE};
                border-radius: 5px;
            }}
        """)
        main_layout.addWidget(self._usage_bar)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(S.px(16))

        self._used_label = QLabel("Used: -- GB")
        self._used_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._used_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        stats_row.addWidget(self._used_label)

        stats_row.addStretch()

        self._free_label = QLabel("Free: -- GB")
        self._free_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._free_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        stats_row.addWidget(self._free_label)

        main_layout.addLayout(stats_row)

        # Speed row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(S.px(16))

        self._read_label = QLabel("↓ -- MB/s")
        self._read_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._read_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        speed_row.addWidget(self._read_label)

        self._write_label = QLabel("↑ -- MB/s")
        self._write_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._write_label.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        speed_row.addWidget(self._write_label)

        speed_row.addStretch()
        main_layout.addLayout(speed_row)

    def set_storage_info(self, total_size: float, total_used: float, total_free: float,
                         read_speed: float, write_speed: float):
        """Update storage overview"""
        self._total_size = total_size
        self._total_used = total_used
        self._total_free = total_free
        self._read_speed = read_speed
        self._write_speed = write_speed

        # Update progress bar
        if total_size > 0:
            percent = (total_used / total_size) * 100
            self._usage_bar.setValue(int(percent))

        # Update labels
        used_gb = total_used / (1024**3)
        free_gb = total_free / (1024**3)

        self._used_label.setText(f"Used: {used_gb:.1f} GB")
        self._free_label.setText(f"Free: {free_gb:.1f} GB")
        self._read_label.setText(f"↓ {self._format_speed(read_speed)}")
        self._write_label.setText(f"↑ {self._format_speed(write_speed)}")

    def _format_speed(self, bps: float) -> str:
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def _on_theme_changed(self, theme_name: str):
        """Re-apply theme"""
        self._setup_ui()
        self.set_storage_info(self._total_size, self._total_used, self._total_free,
                             self._read_speed, self._write_speed)


class StatTile(QFrame):
    """
    Compact statistic tile for displaying key metrics.
    Professional glassmorphism style with icon and value.
    """
    def __init__(self, label: str, value: str = "--", accent: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = value
        colors = c()
        self._accent = accent or colors.ACCENT_BLUE
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build stat tile layout"""
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = c()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(S.px(12), S.px(10), S.px(12), S.px(10))
        self.setLayout(main_layout)

        # Value with accent color
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        self._value_label.setObjectName("value_label")
        main_layout.addWidget(self._value_label)

        # Label
        label_text = QLabel(self._label)
        label_text.setFont(QFont("Segoe UI", S.font_pt(9)))
        label_text.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        main_layout.addWidget(label_text)

    def set_value(self, value: str):
        """Update the displayed value"""
        self._value = value
        label = self.findChild(QLabel, "value_label")
        if label:
            label.setText(value)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply theme"""
        self._setup_ui()
        self.set_value(self._value)
