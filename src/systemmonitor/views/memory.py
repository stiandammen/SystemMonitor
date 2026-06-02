"""
Memory View - Professional memory monitoring dashboard
Enterprise-grade design with real-time graphs, donut charts, and process list
"""
import math
import time
import psutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QPaintEvent, QShowEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QSizePolicy, QMenu, QPushButton, QScrollArea
)

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.widgets.card import Card
import qtawesome as qta


def c():
    """Access theme colors"""
    return theme_manager.colors


class MemoryKpiCard(QFrame, ScaleMixin):
    """Premium KPI stat card for memory metrics"""
    def __init__(self, title: str, icon: str, accent: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._accent = accent
        self._value = "--"
        self._unit = ""
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        colors = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)
        self._title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._unit_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(S.px(115))
        self.setMinimumWidth(S.px(130))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(6))
        self.setLayout(layout)

        # Top row: icon + title
        top_row = QHBoxLayout()
        top_row.setSpacing(S.px(8))

        icon_label = QLabel()
        icon_label.setFixedSize(S.px(16), S.px(16))
        try:
            icon = qta.icon(self._icon, color=self._accent, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(16), S.px(16)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        top_row.addWidget(icon_label)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        top_row.addWidget(self._title_label)
        top_row.addStretch()

        layout.addLayout(top_row)

        # Value
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(20), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        layout.addWidget(self._value_label)

        # Unit
        self._unit_label = QLabel("")
        self._unit_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._unit_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self._unit_label)

    def set_value(self, value: str, unit: str = ""):
        self._value = value
        self._value_label.setText(value)
        self._unit_label.setText(unit)


class MemoryWaveChart(QWidget, ScaleMixin):
    """Animated liquid-fill memory chart – three fluid layers with sine wave boundaries and neon glow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cur_used      = 0.0
        self._cur_cached    = 0.0
        self._cur_available = 100.0
        self._tgt_used      = 0.0
        self._tgt_cached    = 0.0
        self._tgt_available = 100.0
        self._cur_pct  = 0.0
        self._phase1   = 0.0
        self._phase2   = math.pi
        self._pulse    = 0.0
        self.scale_connect()
        self.setMinimumSize(S.px(120), S.px(100))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        theme_manager.theme_changed.connect(self.update)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self):
        spd = 0.07
        def lp(cur, tgt):
            d = tgt - cur
            return tgt if abs(d) < 0.05 else cur + d * spd
        self._cur_used      = lp(self._cur_used,      self._tgt_used)
        self._cur_cached    = lp(self._cur_cached,    self._tgt_cached)
        self._cur_available = lp(self._cur_available, self._tgt_available)
        total = max(self._cur_used + self._cur_cached + self._cur_available, 0.01)
        self._cur_pct = lp(self._cur_pct, self._cur_used / total * 100)
        self._phase1  = (self._phase1 + 0.06) % (2 * math.pi)
        self._phase2  = (self._phase2 + 0.035) % (2 * math.pi)
        self._pulse   = (self._pulse  + 0.04) % (2 * math.pi)
        self.update()

    def set_values(self, used: float, cached: float, available: float):
        self._tgt_used      = max(0.0, min(100.0, used))
        self._tgt_cached    = max(0.0, min(100.0, cached))
        self._tgt_available = max(0.0, min(100.0, available))

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            p.end()
            return

        pad = float(S.px(6))
        bx, by = pad, pad
        bw, bh = float(w) - pad * 2, float(h) - pad * 2
        rad = float(S.px(12))
        amp = float(S.px(4))

        total    = max(self._cur_used + self._cur_cached + self._cur_available, 0.01)
        used_f   = self._cur_used / total
        cached_f = self._cur_cached / total

        # Base y for each layer boundary (fill rises from bottom)
        y_used_base   = by + bh * (1.0 - used_f)
        y_cached_base = by + bh * (1.0 - used_f - cached_f)

        def wave_used(x: float) -> float:
            rel = (x - bx) / bw if bw > 0 else 0.0
            return y_used_base + amp * math.sin(rel * math.pi * 4 + self._phase1) + \
                   amp * 0.4 * math.sin(rel * math.pi * 7 + self._phase2)

        def wave_cached(x: float) -> float:
            rel = (x - bx) / bw if bw > 0 else 0.0
            return y_cached_base + amp * 0.7 * math.sin(rel * math.pi * 3 + self._phase2 + math.pi)

        STEPS = 80

        def fill_up_to(wave_fn) -> QPainterPath:
            path = QPainterPath()
            path.moveTo(bx, by + bh)
            path.lineTo(bx + bw, by + bh)
            path.lineTo(bx + bw, wave_fn(bx + bw))
            for i in range(STEPS, -1, -1):
                path.lineTo(bx + bw * i / STEPS, wave_fn(bx + bw * i / STEPS))
            path.closeSubpath()
            return path

        # Clip all layer fills to the rounded container
        clip = QPainterPath()
        clip.addRoundedRect(bx, by, bw, bh, rad, rad)
        p.setClipPath(clip)

        pct = self._cur_pct
        used_hex = (colors.ACCENT_RED    if pct > 90 else
                    colors.ACCENT_ORANGE if pct > 70 else
                    colors.ACCENT_YELLOW if pct > 40 else
                    colors.ACCENT_GREEN)

        # Background
        p.setBrush(QBrush(QColor(colors.BG_SECONDARY)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(int(bx), int(by), int(bw + 1), int(bh + 1))

        # Layer 1: available (blue backdrop)
        avail_c = QColor(colors.ACCENT_BLUE); avail_c.setAlpha(45)
        p.setBrush(QBrush(avail_c))
        p.drawRect(int(bx), int(by), int(bw + 1), int(bh + 1))

        # Layer 2: cached (purple, rises to cached wave)
        cached_c = QColor(colors.ACCENT_PURPLE); cached_c.setAlpha(80)
        p.setBrush(QBrush(cached_c))
        p.drawPath(fill_up_to(wave_cached))

        # Layer 3: used (theme accent color, rises to used wave)
        used_c = QColor(used_hex); used_c.setAlpha(145)
        p.setBrush(QBrush(used_c))
        p.drawPath(fill_up_to(wave_used))

        # Glow along the used-layer wave: wide soft halo then bright hard line
        for pen_sz, alpha in ((S.px(6), 45), (S.px(3), 90), (max(1, S.px(1)), 230)):
            gc = QColor(used_hex); gc.setAlpha(alpha)
            p.setPen(QPen(gc, pen_sz, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            px0, py0 = bx, wave_used(bx)
            for i in range(1, STEPS + 1):
                px1 = bx + bw * i / STEPS
                py1 = wave_used(px1)
                if by <= py0 <= by + bh and by <= py1 <= by + bh:
                    p.drawLine(int(px0), int(py0), int(px1), int(py1))
                px0, py0 = px1, py1

        # Release clip for overlays
        p.setClipping(False)

        # Container border
        border_c = QColor(colors.BORDER); border_c.setAlpha(100)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(border_c, max(1, S.px(1))))
        p.drawRoundedRect(int(bx), int(by), int(bw), int(bh), int(rad), int(rad))

        # Side tick marks at 25 / 50 / 75%
        tick_c = QColor(colors.TEXT_MUTED); tick_c.setAlpha(70)
        p.setFont(QFont("Segoe UI", S.font_pt(7)))
        for frac, label in ((0.25, "75%"), (0.5, "50%"), (0.75, "25%")):
            ty = int(by + bh * frac)
            p.setPen(QPen(tick_c, max(1, S.px(1))))
            p.drawLine(int(bx + bw - S.px(10)), ty, int(bx + bw), ty)
            p.setPen(QColor(colors.TEXT_MUTED))
            p.drawText(int(bx + 4), ty + S.px(3), label)

        # Center text: animated % with drop shadow
        pct_str = f"{pct:.0f}%"
        cx, cy_c = bx + bw / 2, by + bh / 2
        p.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        fm = p.fontMetrics()
        tx = int(cx - fm.horizontalAdvance(pct_str) / 2)
        ty = int(cy_c + S.px(7))
        p.setPen(QColor(0, 0, 0, 90))
        p.drawText(tx + 1, ty + 1, pct_str)
        p.setPen(QColor(colors.TEXT_PRIMARY))
        p.drawText(tx, ty, pct_str)

        # Sublabel
        p.setFont(QFont("Segoe UI", S.font_pt(8)))
        fm2 = p.fontMetrics()
        p.setPen(QColor(colors.TEXT_MUTED))
        p.drawText(int(cx - fm2.horizontalAdvance("Used") / 2), ty + S.px(15), "Used")

        p.end()


class MemoryUsageGraph(QWidget, ScaleMixin):
    """Modern real-time memory usage line graph with smooth rendering"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._max_points = 60
        self.scale_connect()
        self.setMinimumHeight(S.px(140))

    def add_value(self, value: float):
        self._history.append(value)
        if len(self._history) > self._max_points:
            self._history.pop(0)
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            painter.end()
            return

        # Padding for labels
        pad_left = 45
        pad_right = 15
        pad_top = 20
        pad_bottom = 25
        graph_w = w - pad_left - pad_right
        graph_h = h - pad_top - pad_bottom
        graph_x = pad_left
        graph_y = pad_top

        # Background
        painter.setBrush(QColor(colors.BG_CARD))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        # Graph area background
        painter.setBrush(QColor(colors.BG_SECONDARY))
        painter.drawRect(int(graph_x), int(graph_y), int(graph_w), int(graph_h))

        # Grid lines and labels
        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(colors.TEXT_MUTED))

        # Horizontal grid (0%, 25%, 50%, 75%, 100%)
        for i in range(5):
            y = graph_y + graph_h * i / 4
            # Grid line
            painter.setPen(QPen(QColor(colors.BORDER), 1, Qt.PenStyle.DotLine))
            painter.drawLine(int(graph_x), int(y), int(graph_x + graph_w), int(y))
            # Label
            painter.setPen(QColor(colors.TEXT_MUTED))
            val = 100 - i * 25
            painter.drawText(int(graph_x - 5), int(y + 3), f"{val}%")

        # Draw the line and fill
        if len(self._history) > 1:
            step = graph_w / (self._max_points - 1)
            points = []
            for i, val in enumerate(self._history):
                x = graph_x + i * step
                y = graph_y + graph_h - (val / 100.0 * graph_h)
                points.append((x, y))

            # Gradient fill under the line
            fill_pts = [(graph_x, graph_y + graph_h)] + points + [(points[-1][0], graph_y + graph_h)]
            gradient = QLinearGradient(0, graph_y, 0, graph_y + graph_h)

            # Color based on current value
            current_val = self._history[-1]
            if current_val > 90:
                line_color = QColor(colors.ACCENT_RED)
            elif current_val > 70:
                line_color = QColor(colors.ACCENT_ORANGE)
            elif current_val > 40:
                line_color = QColor(colors.ACCENT_YELLOW)
            else:
                line_color = QColor(colors.ACCENT_GREEN)

            top_color = QColor(line_color)
            top_color.setAlpha(100)
            bottom_color = QColor(line_color)
            bottom_color.setAlpha(10)
            gradient.setColorAt(0, top_color)
            gradient.setColorAt(1, bottom_color)

            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            from PyQt6.QtCore import QPoint
            qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
            if len(qpoints) >= 3:
                painter.drawPolygon(*qpoints)

            # Main line
            painter.setPen(QPen(line_color, 2.5, Qt.PenStyle.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))

            # Glow effect
            glow_color = QColor(line_color)
            glow_color.setAlpha(40)
            painter.setPen(QPen(glow_color, 6, Qt.PenStyle.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))

            # Data points for last 10 values
            painter.setPen(QPen(line_color, 2))
            for i in range(max(0, len(points) - 10), len(points)):
                px, py = points[i]
                painter.drawEllipse(int(px - 3), int(py - 3), 6, 6)

        # Current value badge
        if self._history:
            val = self._history[-1]
            if val > 90:
                badge_color = colors.ACCENT_RED
            elif val > 70:
                badge_color = colors.ACCENT_ORANGE
            elif val > 40:
                badge_color = colors.ACCENT_YELLOW
            else:
                badge_color = colors.ACCENT_GREEN

            # Badge background (positioned top-right, away from graph content)
            badge_x = w - S.px(65)
            badge_y = S.px(8)
            painter.setBrush(QColor(colors.BG_SECONDARY))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(badge_x), int(badge_y), S.px(55), S.px(22), S.px(4), S.px(4))

            # Badge text
            painter.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            painter.setPen(QColor(badge_color))
            painter.drawText(int(badge_x + S.px(8)), int(badge_y + S.px(15)), f"{val:.1f}%")

        # Time indicator (positioned to avoid overlapping with badge)
        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(int(graph_x), int(h - S.px(5)), "60s ago")
        # Position "now" text with padding from right edge
        now_x = int(graph_x + graph_w - S.px(35))
        painter.drawText(now_x, int(h - S.px(5)), "now")

        # Y-axis label (rotated)
        painter.save()
        painter.translate(S.px(12), h / 2)
        painter.rotate(-90)
        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(-S.px(15), 0, "Usage %")
        painter.restore()

        painter.end()


class ProcessRow(QFrame, ScaleMixin):
    """Single process memory consumption row"""
    killed = None  # Class variable for callback

    def __init__(self, name: str = "", memory_mb: float = 0, percent: float = 0, rank: int = 0, parent=None):
        super().__init__(parent)
        self._rank = rank
        self._pid = None
        self._memory_mb = memory_mb
        self._percent = percent
        self.scale_connect()
        self._setup_ui()
        self.update_values(name, memory_mb, percent, rank)

    def _setup_ui(self):
        colors = c()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: {S.px(6)}px;
            }}
            QFrame:hover {{
                background-color: {colors.BG_HOVER};
            }}
        """)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(S.px(10), S.px(7), S.px(10), S.px(6))
        outer.setSpacing(S.px(3))

        # — Top row: rank  name  percent —
        top = QHBoxLayout()
        top.setSpacing(S.px(6))
        top.setContentsMargins(0, 0, 0, 0)

        self._rank_lbl = QLabel()
        self._rank_lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        self._rank_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._rank_lbl.setFixedWidth(S.px(22))
        top.addWidget(self._rank_lbl)

        self._name_lbl = QLabel()
        self._name_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        self._name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        self._name_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        top.addWidget(self._name_lbl, stretch=1)

        self._pct_lbl = QLabel()
        self._pct_lbl.setFont(QFont("Consolas", S.font_pt(9), QFont.Weight.Bold))
        self._pct_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        self._pct_lbl.setFixedWidth(S.px(42))
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self._pct_lbl)

        outer.addLayout(top)

        # — Bottom row: bar  memory —
        bot = QHBoxLayout()
        bot.setSpacing(S.px(8))
        bot.setContentsMargins(S.px(28), 0, 0, 0)

        self._bar = QProgressBar()
        self._bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._bar.setFixedHeight(S.px(5))
        self._bar.setTextVisible(False)
        bot.addWidget(self._bar, stretch=1)

        self._mem_lbl = QLabel()
        self._mem_lbl.setFont(QFont("Consolas", S.font_pt(8)))
        self._mem_lbl.setStyleSheet(f"color: {colors.ACCENT_CYAN}; background: transparent;")
        self._mem_lbl.setFixedWidth(S.px(64))
        self._mem_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bot.addWidget(self._mem_lbl)

        outer.addLayout(bot)

    def _show_context_menu(self, pos):
        if self._pid is None:
            return
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c().BG_CARD};
                border: 1px solid {c().BORDER};
                border-radius: {S.px(8)}px;
                padding: {S.px(4)}px;
            }}
            QMenu::item {{
                color: {c().TEXT_PRIMARY};
                padding: {S.px(6)}px {S.px(24)}px {S.px(6)}px {S.px(12)}px;
                border-radius: {S.px(4)}px;
            }}
            QMenu::item:selected {{
                background-color: {c().BG_HOVER};
            }}
        """)

        # Memory info action
        info_action = menu.addAction(f"Memory: {self._memory_mb:.1f} MB ({self._percent:.1f}%)")
        info_action.setEnabled(False)

        if self._name_lbl.text():
            kill_action = menu.addAction(f"Kill {self._name_lbl.text()[:20]}")
            kill_action.triggered.connect(lambda: self._kill_process())

        menu.exec(self.mapToGlobal(pos))

    def _kill_process(self):
        if self._pid is None:
            return
        try:
            proc = psutil.Process(self._pid)
            proc.kill()
            if ProcessRow.killed:
                ProcessRow.killed(self._name_lbl.text(), self._pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def update_values(self, name: str, memory_mb: float = 0, percent: float = 0, rank: int = 0, pid: int | None = None):
        self._rank = rank
        self._pid: int | None = pid
        self._memory_mb = memory_mb
        self._percent = percent

        colors = c()
        self._rank_lbl.setText(f"#{rank}")

        display_name = str(name)[:30] if name else "--"
        self._name_lbl.setText(display_name)
        self._name_lbl.setToolTip(f"PID: {pid}  |  {name}" if pid and name else (name or ""))

        self._mem_lbl.setText(f"{memory_mb:.0f} MB" if memory_mb >= 1 else "< 1 MB")
        self._pct_lbl.setText(f"{percent:.1f}%")
        self._bar.setValue(int(min(100, max(0, percent))))

        if percent >= 15:
            bar_color = colors.ACCENT_RED
            pct_color = colors.ACCENT_RED
        elif percent >= 5:
            bar_color = colors.ACCENT_ORANGE
            pct_color = colors.ACCENT_ORANGE
        elif percent >= 1:
            bar_color = colors.ACCENT_YELLOW
            pct_color = colors.TEXT_SECONDARY
        else:
            bar_color = colors.ACCENT_GREEN
            pct_color = colors.TEXT_MUTED

        self._pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-radius: {S.px(2)}px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: {S.px(2)}px;
            }}
        """)


class MemoryView(QWidget, ScaleMixin):
    """Memory monitoring dashboard with professional enterprise design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory_history = []
        self._process_rows = []
        self._max_history = 60
        self._current_memory_data = None
        self._update_timer = None
        self._prev_top_pid = None
        self._last_proc_update = 0
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Start update timer when view is shown"""
        super().showEvent(a0)
        self._start_update_timer()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply styles when theme changes"""
        self.update()

    def _start_update_timer(self):
        """Start the real-time update timer - called when view is shown"""
        if self._update_timer is not None:
            return
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display_from_signal)
        self._update_timer.start(1000)

    def _update_display_from_signal(self):
        """Called by timer to refresh data from collector signal"""
        pass

    def _setup_ui(self):
        colors = c()
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        main_layout.setSpacing(S.px(12))
        self.setLayout(main_layout)

        # ===== HEADER BAR =====
        header = QFrame()
        header.setMinimumHeight(S.px(48))
        header.setMaximumHeight(S.px(58))
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(S.px(16), 0, S.px(16), 0)
        header_layout.setSpacing(S.px(12))
        header.setLayout(header_layout)

        # Live indicator
        live_layout = QHBoxLayout()
        live_layout.setSpacing(S.px(8))

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(S.px(8), S.px(8))
        self._status_dot.setStyleSheet(f"background-color: {colors.ACCENT_GREEN}; border-radius: {S.px(4)}px;")
        live_layout.addWidget(self._status_dot)

        live_label = QLabel("LIVE")
        live_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        live_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_layout.addWidget(live_label)

        header_layout.addLayout(live_layout)

        title = QLabel("Memory Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._usage_indicator = QLabel("0%")
        self._usage_indicator.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
        self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        header_layout.addWidget(self._usage_indicator)

        main_layout.addWidget(header)

        # ===== KPI CARDS ROW =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(S.px(12))

        self._used_kpi = MemoryKpiCard("Used", "fa5s.memory", colors.ACCENT_GREEN)
        self._available_kpi = MemoryKpiCard("Available", "fa5s.check", colors.ACCENT_BLUE)
        self._cached_kpi = MemoryKpiCard("Cached", "fa5s.archive", colors.ACCENT_PURPLE)
        self._free_kpi = MemoryKpiCard("Free", "fa5s.box-open", colors.ACCENT_ORANGE)

        for card in [self._used_kpi, self._available_kpi, self._cached_kpi, self._free_kpi]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            kpi_layout.addWidget(card, stretch=1)

        main_layout.addLayout(kpi_layout)

        # ===== MAIN CONTENT (2 columns) =====
        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(S.px(12))
        content_container.setLayout(content_layout)

        # LEFT COLUMN - Charts
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(S.px(12))
        left_widget.setLayout(left_layout)

        # Distribution card
        dist_card = Card(title="Memory Distribution", icon="ph.chart-pie")
        self._wave_chart = MemoryWaveChart()
        dist_card.add_widget(self._wave_chart)
        left_layout.addWidget(dist_card, stretch=1)

        # Usage graph card
        graph_card = Card(title="Memory Usage Over Time", icon="ph.chart-line")
        self._usage_graph = MemoryUsageGraph()
        self._usage_graph.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        graph_card.add_widget(self._usage_graph)
        left_layout.addWidget(graph_card, stretch=1)

        content_layout.addWidget(left_widget, stretch=2)

        # RIGHT COLUMN - Process list (full height)
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_widget.setLayout(right_layout)

        # Process card
        process_card = Card(title="Top Processes", icon="ph.list-numbers")

        # "View all" button
        proc_header = QHBoxLayout()
        proc_header.setSpacing(S.px(12))
        self._view_all_btn = QPushButton("Vis alle")
        self._view_all_btn.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._view_all_btn.setMinimumHeight(S.px(24))
        self._view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_all_btn.clicked.connect(self._show_all_processes)
        self._view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_SECONDARY};
                color: {colors.TEXT_SECONDARY};
                border: 1px solid {colors.BORDER};
                border-radius: {S.px(4)}px;
                padding: 2px {S.px(12)}px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
                border-color: {colors.ACCENT_PURPLE};
            }}
        """)
        proc_header.addStretch()
        proc_header.addWidget(self._view_all_btn)
        process_card.add_layout(proc_header)

        # Scroll area — rows har alltid fast høyde, scroll tar seg av resten
        row_h     = S.px(46)
        row_gap   = S.px(4)
        n_rows    = 10
        container_h = n_rows * row_h + (n_rows - 1) * row_gap

        self._process_container = QWidget()
        self._process_container.setFixedHeight(container_h)
        self._process_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        process_vlayout = QVBoxLayout(self._process_container)
        process_vlayout.setContentsMargins(0, 0, 0, 0)
        process_vlayout.setSpacing(row_gap)

        self._process_rows = []
        for i in range(n_rows):
            row = ProcessRow(name="--", memory_mb=0, percent=0, rank=i + 1)
            row.setFixedHeight(row_h)
            self._process_rows.append(row)
            process_vlayout.addWidget(row)

        scroll = QScrollArea()
        scroll.setWidget(self._process_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#qt_scrollarea_viewport {{ background: transparent; }}
            QScrollBar:vertical {{
                background: {colors.BG_SECONDARY};
                width: {S.px(5)}px;
                border-radius: {S.px(2)}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors.BORDER};
                border-radius: {S.px(2)}px;
                min-height: {S.px(24)}px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {colors.TEXT_MUTED}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        process_card.add_widget(scroll)
        right_layout.addWidget(process_card, stretch=1)

        content_layout.addWidget(right_widget, stretch=1)

        main_layout.addWidget(content_container, stretch=1)

        # ===== STATUS BAR =====
        self._setup_status_bar(main_layout)

    def _setup_status_bar(self, parent_layout):
        """Setup bottom status bar"""
        colors = c()

        status_card = Card(title="System Status", icon="mdi.shield-check")
        status_layout = QHBoxLayout()
        status_layout.setSpacing(S.px(32))

        # Health
        health_widget = QWidget()
        health_layout = QVBoxLayout()
        health_layout.setSpacing(4)
        health_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        health_icon = QLabel()
        try:
            icon = qta.icon("mdi.shield-check", color=colors.ACCENT_GREEN, scale=1.5)
            health_icon.setPixmap(icon.pixmap(S.px(28), S.px(28)))
        except Exception:
            health_icon.setText("✓")
        health_icon.setStyleSheet("background: transparent;")
        health_layout.addWidget(health_icon)

        self._health_label = QLabel("Healthy")
        self._health_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        self._health_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        health_layout.addWidget(self._health_label)

        health_widget.setLayout(health_layout)
        status_layout.addWidget(health_widget)

        # Total memory
        total_widget = QWidget()
        total_layout = QVBoxLayout()
        total_layout.setSpacing(2)
        total_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        total_title = QLabel("Total Memory")
        total_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        total_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        total_layout.addWidget(total_title)

        self._total_label = QLabel("-- GB")
        self._total_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._total_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        total_layout.addWidget(self._total_label)

        total_widget.setLayout(total_layout)
        status_layout.addWidget(total_widget)

        # Used memory
        used_widget = QWidget()
        used_layout = QVBoxLayout()
        used_layout.setSpacing(2)
        used_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        used_title = QLabel("Used")
        used_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        used_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        used_layout.addWidget(used_title)

        self._used_label = QLabel("-- GB")
        self._used_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._used_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        used_layout.addWidget(self._used_label)

        used_widget.setLayout(used_layout)
        status_layout.addWidget(used_widget)

        # Memory Type
        type_widget = QWidget()
        type_layout = QVBoxLayout()
        type_layout.setSpacing(2)
        type_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        type_title = QLabel("Memory Type")
        type_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        type_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        type_layout.addWidget(type_title)

        self._ram_type_label = QLabel("–")
        self._ram_type_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._ram_type_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        type_layout.addWidget(self._ram_type_label)

        type_widget.setLayout(type_layout)
        status_layout.addWidget(type_widget)

        status_layout.addStretch()

        status_card.add_layout(status_layout)
        parent_layout.addWidget(status_card)

    def update_data(self, data: dict):
        """Handle data from collector signal - runs on UI thread"""
        try:
            if 'memory' not in data:
                return
            self._current_memory_data = data['memory']
            self._schedule_display_update()
        except Exception as e:
            pass

    def _schedule_display_update(self):
        """Throttle display updates to ~60fps"""
        if not getattr(self, '_update_scheduled', False):
            self._update_scheduled = True
            QTimer.singleShot(16, self._do_display_update)

    def _do_display_update(self):
        """Perform the actual display update"""
        self._update_scheduled = False
        if not self._current_memory_data:
            return
        try:
            self._update_stats(self._current_memory_data)
            self._update_charts()
            now = time.time()
            if now - self._last_proc_update >= 3:
                self._last_proc_update = now
                self._update_processes()
        except Exception as e:
            pass

    def _update_stats(self, mem_data):
        colors = c()
        total_gb = mem_data['total'] / (1024**3)
        used_gb = mem_data['used'] / (1024**3)
        available_gb = mem_data['available'] / (1024**3)
        cached_gb = mem_data.get('cached', 0) / (1024**3)
        free_gb = (mem_data.get('free', mem_data['available']) - mem_data.get('cached', 0)) / (1024**3)

        used_pct = mem_data['percent']
        available_pct = (mem_data['available'] / mem_data['total']) * 100 if mem_data['total'] > 0 else 0
        cached_pct = (mem_data.get('cached', 0) / mem_data['total']) * 100 if mem_data['total'] > 0 else 0
        free_pct = (free_gb / total_gb) * 100 if total_gb > 0 else 0

        # Update KPI cards
        self._used_kpi.set_value(f"{used_gb:.1f} GB", f"{used_pct:.0f}%")
        self._available_kpi.set_value(f"{available_gb:.1f} GB", f"{available_pct:.0f}%")
        self._cached_kpi.set_value(f"{cached_gb:.1f} GB", f"{cached_pct:.0f}%")
        self._free_kpi.set_value(f"{free_gb:.1f} GB", f"{free_pct:.0f}%")

        # Update header
        self._usage_indicator.setText(f"{used_pct:.0f}%")
        if used_pct > 90:
            color = colors.ACCENT_RED
        elif used_pct > 70:
            color = colors.ACCENT_ORANGE
        elif used_pct > 40:
            color = colors.ACCENT_YELLOW
        else:
            color = colors.ACCENT_GREEN

        self._usage_indicator.setStyleSheet(f"color: {color}; background: transparent; font-size: {S.font_pt(16)}px; font-weight: bold;")

        # Update status bar
        self._total_label.setText(f"{total_gb:.0f} GB")
        self._used_label.setText(f"{used_gb:.1f} GB")
        ram_type = mem_data.get('ram_type', '')
        if ram_type and hasattr(self, '_ram_type_label'):
            self._ram_type_label.setText(ram_type)

        # Health label (previously driven by pressure)
        if used_pct >= 90:
            h_text, h_color = "Critical", colors.ACCENT_RED
        elif used_pct >= 70:
            h_text, h_color = "Warning",  colors.ACCENT_ORANGE
        else:
            h_text, h_color = "Healthy",  colors.ACCENT_GREEN
        self._health_label.setText(h_text)
        self._health_label.setStyleSheet(f"color: {h_color}; background: transparent; font-weight: bold;")

    def _update_charts(self):
        if not self._current_memory_data:
            return
        mem = self._current_memory_data
        total = mem['total']
        if total <= 0:
            return

        used_pct = (mem['used'] / total) * 100
        cached_pct = (mem.get('cached', 0) / total) * 100
        available_pct = ((mem['available'] - mem.get('cached', 0)) / total) * 100

        self._wave_chart.set_values(used_pct, cached_pct, available_pct)

        self._memory_history.append(used_pct)
        if len(self._memory_history) > self._max_history:
            self._memory_history.pop(0)
        self._usage_graph.add_value(used_pct)

    def _update_processes(self):
        """Refresh top-10 memory consuming processes (called every ~3 s)."""
        try:
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 0:
                        procs.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'memory_percent': info['memory_percent'],
                            'rss': info['memory_info'].rss if info['memory_info'] else 0,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x['memory_percent'], reverse=True)
            top = procs[:10]
            for i, row in enumerate(self._process_rows):
                if i < len(top):
                    proc = top[i]
                    row.update_values(proc['name'], proc['rss'] / (1024 ** 2),
                                      proc['memory_percent'], i + 1, proc['pid'])
                else:
                    row.update_values("--", 0, 0, i + 1)
        except Exception:
            pass

    def _show_all_processes(self):
        """Show dialog with all running processes"""
        from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QHeaderView

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 650)
        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        dialog.setLayout(main_layout)

        # Title bar
        title_bar = QFrame()
        title_bar.setMinimumHeight(S.px(50))
        title_bar.setMaximumHeight(S.px(60))
        title_bar.setStyleSheet(f"background-color: {colors.BG_CARD}; border-bottom: 1px solid {colors.BORDER};")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 10, 0)
        title_bar.setLayout(title_layout)

        title = QLabel("All Processes by Memory")
        title.setFont(QFont("Segoe UI", S.font_pt(14), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(title)

        title_layout.addStretch()

        close_btn = QPushButton("X")
        close_btn.setFixedSize(S.px(36), S.px(36))
        close_btn.setFont(QFont("Segoe UI", S.font_pt(12)))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.TEXT_SECONDARY};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(dialog.close)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Process", "PID", "Memory (MB)", "Memory %", "Status"])
        table.setFont(QFont("Segoe UI", S.font_pt(10)))
        table.horizontalHeader().setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors.BG_PRIMARY};
                color: {colors.TEXT_PRIMARY};
                border: none;
                gridline-color: {colors.BORDER};
            }}
            QTableWidget::item {{
                padding: {S.px(8)}px {S.px(12)}px;
                border: none;
                border-bottom: 1px solid {colors.BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: {colors.BG_SECONDARY};
            }}
            QTableWidget::item:selected {{
                background-color: {colors.BG_HOVER};
            }}
            QHeaderView::section {{
                background-color: {colors.BG_CARD};
                color: {colors.TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {colors.BORDER};
                padding: {S.px(10)}px {S.px(12)}px;
                font-weight: bold;
            }}
            QHeaderView {{
                border: none;
            }}
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 80)

        # Populate data
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 0:
                        mem_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                        processes.append({
                            'name': info['name'],
                            'pid': info['pid'],
                            'memory_mb': mem_mb,
                            'percent': info['memory_percent'],
                            'status': proc.status() if hasattr(proc, 'status') else 'running',
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            processes.sort(key=lambda x: x['percent'], reverse=True)

            table.setRowCount(len(processes))
            for i, proc in enumerate(processes):
                name_item = QTableWidgetItem(proc['name'][:40])
                name_item.setForeground(QColor(colors.TEXT_PRIMARY))
                table.setItem(i, 0, name_item)

                pid_item = QTableWidgetItem(str(proc['pid']))
                pid_item.setForeground(QColor(colors.TEXT_MUTED))
                table.setItem(i, 1, pid_item)

                mem_item = QTableWidgetItem(f"{proc['memory_mb']:.1f}")
                mem_item.setForeground(QColor(colors.ACCENT_CYAN))
                table.setItem(i, 2, mem_item)

                pct_item = QTableWidgetItem(f"{proc['percent']:.1f}%")
                pct_item.setForeground(QColor(colors.TEXT_SECONDARY))
                table.setItem(i, 3, pct_item)

                status_item = QTableWidgetItem(proc['status'])
                status_item.setForeground(QColor(colors.TEXT_MUTED))
                table.setItem(i, 4, status_item)

        except Exception as e:
            print(f"Process list error: {e}")

        main_layout.addWidget(table)
        dialog.exec()
