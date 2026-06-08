"""
Reusable widget components for the Memory view dashboard:
KPI cards, the animated wave chart, the usage-over-time graph and process rows.
"""
import math
import psutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QPaintEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QProgressBar, QSizePolicy, QMenu
)

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
import qtawesome as qta


def c():
    """Access theme colors"""
    return theme_manager.colors


class MemoryKpiCard(QFrame, ScaleMixin, I18nMixin):
    """Premium KPI stat card for memory metrics"""
    def __init__(self, title: str, icon: str, accent: str, parent=None):
        super().__init__(parent)
        self._title_key = title
        self._title = tr(title)
        self._icon = icon
        self._accent = accent
        self._value = "--"
        self._unit = ""
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if hasattr(self, '_title_label'):
            self._title_label.setText(self._title)

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
        used_lbl = tr("Used")
        p.drawText(int(cx - fm2.horizontalAdvance(used_lbl) / 2), ty + S.px(15), used_lbl)

        p.end()


class MemoryUsageGraph(QWidget, ScaleMixin):
    """Modern real-time memory usage line graph with smooth rendering"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._max_points = 60
        self._sample_stride = 1
        self._sample_skip = 0
        self.scale_connect()
        self.setMinimumHeight(S.px(140))

    def set_max_points(self, max_points: int):
        """Resize the rolling history buffer (e.g. from the History Length setting)"""
        self._max_points = max(1, int(max_points))
        if len(self._history) > self._max_points:
            self._history = self._history[-self._max_points:]
        self.update()

    def set_sample_stride(self, stride: int):
        """Keep only every Nth incoming sample so a fixed-size buffer can span
        a longer time window (e.g. from the History Length setting)."""
        self._sample_stride = max(1, int(stride))
        self._sample_skip = 0

    def add_value(self, value: float):
        self._sample_skip += 1
        if self._sample_skip < self._sample_stride:
            return
        self._sample_skip = 0
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
        painter.drawText(int(graph_x), int(h - S.px(5)), tr("60s ago"))
        # Position "now" text with padding from right edge
        now_x = int(graph_x + graph_w - S.px(35))
        painter.drawText(now_x, int(h - S.px(5)), tr("now"))

        # Y-axis label (rotated)
        painter.save()
        painter.translate(S.px(12), h / 2)
        painter.rotate(-90)
        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(-S.px(15), 0, tr("Usage %"))
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
        info_action = menu.addAction(
            tr("Memory: {0:.1f} MB ({1:.1f}%)").format(self._memory_mb, self._percent))
        info_action.setEnabled(False)

        if self._name_lbl.text():
            kill_action = menu.addAction(tr("Kill {0}").format(self._name_lbl.text()[:20]))
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
        self._name_lbl.setToolTip(tr("PID: {0}  |  {1}").format(pid, name) if pid and name else (name or ""))

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
