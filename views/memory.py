"""
Memory View - Professional memory monitoring dashboard
Enterprise-grade design with real-time graphs, donut charts, and process list
"""
import time
import psutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPaintEvent, QShowEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QSizePolicy, QMenu, QPushButton
)

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from widgets.card import Card
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
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(S.px(90))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        # Top row: icon + title
        top_row = QHBoxLayout()
        top_row.setSpacing(S.px(8))

        icon_label = QLabel()
        try:
            icon = qta.icon(self._icon, color=self._accent, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(16), S.px(16)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        top_row.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        top_row.addWidget(title_label)
        top_row.addStretch()

        layout.addLayout(top_row)

        # Value
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
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


class MemoryDonutChart(QWidget, ScaleMixin):
    """Donut chart showing memory distribution"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._used_pct = 0
        self._cached_pct = 0
        self._available_pct = 0
        self.scale_connect()
        self.setMinimumSize(S.px(160), S.px(160))
        self.setMaximumSize(S.px(200), S.px(200))
        theme_manager.theme_changed.connect(lambda _: self.update())

    def set_values(self, used: float, cached: float, available: float):
        self._used_pct = max(0, min(100, used))
        self._cached_pct = max(0, min(100, cached))
        self._available_pct = max(0, min(100, available))
        self.update()

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            painter.end()
            return

        size = min(w, h)
        center = size / 2
        radius = (size - 40) / 2
        arc_rect = (size - 2 * radius) / 2

        # Background
        painter.setBrush(QColor(colors.BG_SECONDARY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(arc_rect), int(arc_rect), int(2 * radius), int(2 * radius))

        # Draw arc segments (270 degree arc)
        start_angle = 135 * 16
        total = self._used_pct + self._cached_pct + self._available_pct
        if total <= 0:
            total = 1

        # Used
        used_arc = int(self._used_pct / total * 270 * 16)
        painter.setPen(QPen(QColor(colors.ACCENT_GREEN), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(arc_rect), int(arc_rect), int(2 * radius), int(2 * radius),
                       start_angle, -used_arc)

        # Cached
        cached_start = start_angle - used_arc
        cached_arc = int(self._cached_pct / total * 270 * 16)
        painter.setPen(QPen(QColor(colors.ACCENT_PURPLE), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(arc_rect), int(arc_rect), int(2 * radius), int(2 * radius),
                       cached_start, -cached_arc)

        # Available
        avail_start = cached_start - cached_arc
        avail_arc = int(self._available_pct / total * 270 * 16)
        painter.setPen(QPen(QColor(colors.ACCENT_BLUE), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(arc_rect), int(arc_rect), int(2 * radius), int(2 * radius),
                       avail_start, -avail_arc)

        # Center text
        total_mem = getattr(psutil.virtual_memory(), 'total', 0) / (1024**3)
        painter.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(int(center - S.px(25)), int(center + S.px(5)), f"{total_mem:.0f} GB")

        painter.end()


class MemoryPressureGraph(QWidget, ScaleMixin):
    """Real-time memory pressure graph"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._max_points = 60
        self.scale_connect()
        self.setMinimumHeight(S.px(120))

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

        # Background
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        # Zone backgrounds
        zone_h = h / 4

        def zone_color(hex_color, alpha):
            c = QColor(hex_color)
            c.setAlpha(alpha)
            return c

        painter.setBrush(zone_color(colors.ACCENT_RED, 25))
        painter.drawRect(0, 0, w, int(zone_h * 0.4))
        painter.setBrush(zone_color(colors.ACCENT_ORANGE, 18))
        painter.drawRect(0, int(zone_h * 0.4), w, int(zone_h * 0.4))
        painter.setBrush(zone_color(colors.ACCENT_YELLOW, 12))
        painter.drawRect(0, int(zone_h * 0.8), w, int(zone_h * 0.6))
        painter.setBrush(zone_color(colors.ACCENT_GREEN, 8))
        painter.drawRect(0, int(zone_h * 1.4), w, int(zone_h * 2.6))

        # Zone labels
        painter.setFont(QFont("Segoe UI", S.font_pt(7)))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(S.px(4), S.px(10), "90-100%")
        painter.drawText(S.px(4), int(zone_h * 0.4 + S.px(10)), "70-90%")
        painter.drawText(S.px(4), int(zone_h * 0.8 + S.px(10)), "40-70%")
        painter.drawText(S.px(4), int(zone_h * 1.4 + S.px(10)), "0-40%")

        # Grid lines
        painter.setPen(QPen(QColor(colors.BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(4):
            y = int(zone_h * (i + 1))
            painter.drawLine(0, y, w, y)

        # Draw line
        if len(self._history) > 1:
            step = w / (self._max_points - 1)
            points = [(i * step, h - val / 100.0 * h) for i, val in enumerate(self._history)]

            # Gradient fill for pressure
            fill_pts = [(0, h)] + points + [(points[-1][0], h)]
            gradient = QLinearGradient(0, 0, 0, h)
            orange = QColor(colors.ACCENT_ORANGE)
            orange.setAlpha(60)
            orange_end = QColor(colors.ACCENT_ORANGE)
            orange_end.setAlpha(5)
            gradient.setColorAt(0, orange)
            gradient.setColorAt(1, orange_end)
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            from PyQt6.QtCore import QPoint
            qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
            if len(qpoints) >= 3:
                painter.drawPolygon(*qpoints)

            # Line
            painter.setPen(QPen(QColor(colors.ACCENT_ORANGE), 2))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))

        painter.end()


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

        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
        layout.setSpacing(S.px(10))
        self.setLayout(layout)

        self._rank_lbl = QLabel()
        self._rank_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        self._rank_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._rank_lbl.setMinimumWidth(S.px(22))
        layout.addWidget(self._rank_lbl)

        self._name_lbl = QLabel()
        self._name_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        self._name_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._name_lbl, stretch=1)

        self._mem_lbl = QLabel()
        self._mem_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._mem_lbl.setStyleSheet(f"color: {colors.ACCENT_CYAN}; background: transparent;")
        self._mem_lbl.setFixedWidth(S.px(70))
        self._mem_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._mem_lbl)

        self._pct_lbl = QLabel()
        self._pct_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._pct_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        self._pct_lbl.setFixedWidth(S.px(40))
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._pct_lbl)

        self._bar = QProgressBar()
        self._bar.setFixedWidth(S.px(80))
        self._bar.setFixedHeight(S.px(6))
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

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
        self._rank_lbl.setText(f"#{rank}")
        self._name_lbl.setText(str(name)[:25] if name else "--")
        self._name_lbl.setToolTip(f"PID: {pid}\n{name}" if pid and name else name)
        self._mem_lbl.setText(f"{memory_mb:.0f} MB")
        self._pct_lbl.setText(f"{percent:.1f}%")
        self._bar.setValue(int(min(100, max(0, percent))))
        self._memory_mb = memory_mb
        self._percent = percent

        bar_color = (c().ACCENT_RED if percent > 50 else
                    c().ACCENT_ORANGE if percent > 25 else
                    c().ACCENT_GREEN)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c().BG_PRIMARY};
                border: none;
                border-radius: {S.px(3)}px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: {S.px(3)}px;
            }}
        """)


class MemoryView(QWidget, ScaleMixin):
    """Memory monitoring dashboard with professional enterprise design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory_history = []
        self._pressure_history = []
        self._process_rows = []
        self._max_history = 60
        self._current_memory_data = None
        self._update_timer = None
        self._prev_top_pid = None
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        main_layout.setSpacing(S.px(12))
        self.setLayout(main_layout)

        # ===== HEADER BAR =====
        header = QFrame()
        header.setMinimumHeight(S.px(48))
        header.setMaximumHeight(S.px(58))
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        self._pressure_label = QLabel("Normal")
        self._pressure_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._pressure_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; padding: {S.px(3)}px {S.px(10)}px; background-color: {colors.BG_SECONDARY}; border-radius: {S.px(10)}px;")
        header_layout.addWidget(self._pressure_label)

        main_layout.addWidget(header)

        # ===== KPI CARDS ROW =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(S.px(12))

        self._used_kpi = MemoryKpiCard("Used", "fa5s.memory", colors.ACCENT_GREEN)
        self._available_kpi = MemoryKpiCard("Available", "fa5s.check", colors.ACCENT_BLUE)
        self._cached_kpi = MemoryKpiCard("Cached", "fa5s.archive", colors.ACCENT_PURPLE)
        self._free_kpi = MemoryKpiCard("Free", "fa5s.box-open", colors.ACCENT_ORANGE)

        for card in [self._used_kpi, self._available_kpi, self._cached_kpi, self._free_kpi]:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            kpi_layout.addWidget(card, stretch=1)

        main_layout.addLayout(kpi_layout)

        # ===== MAIN CONTENT (2 columns) =====
        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(S.px(12))
        content_container.setLayout(content_layout)

        # LEFT COLUMN - Charts
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(S.px(12))
        left_widget.setLayout(left_layout)

        # Distribution card
        dist_card = Card(title="Memory Distribution", icon="📊")
        donut_container = QWidget()
        donut_layout = QVBoxLayout()
        donut_layout.setContentsMargins(0, 0, 0, 0)
        donut_layout.setSpacing(S.px(8))
        donut_container.setLayout(donut_layout)

        self._donut_chart = MemoryDonutChart()
        donut_layout.addWidget(self._donut_chart, alignment=Qt.AlignmentFlag.AlignCenter)
        dist_card.add_widget(donut_container)
        left_layout.addWidget(dist_card, stretch=1)

        # Usage graph card
        graph_card = Card(title="Memory Usage Over Time", icon="📈")
        self._usage_graph = MemoryUsageGraph()
        self._usage_graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        graph_card.add_widget(self._usage_graph)
        left_layout.addWidget(graph_card, stretch=1)

        content_layout.addWidget(left_widget, stretch=2)

        # RIGHT COLUMN - Process list + Pressure
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(S.px(12))
        right_widget.setLayout(right_layout)

        # Process card
        process_card = Card(title="Top Processes", icon="🔍")

        # Header with view all button
        proc_header = QHBoxLayout()
        proc_header.setSpacing(S.px(12))

        self._view_all_btn = QPushButton("View all")
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

        # Column headers
        col_header = QHBoxLayout()
        col_header.setContentsMargins(0, S.px(4), 0, S.px(4))
        col_header.setSpacing(S.px(10))

        lbl = QLabel("#")
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(22)
        col_header.addWidget(lbl)

        lbl = QLabel("Process")
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        col_header.addWidget(lbl, stretch=1)

        lbl = QLabel("Memory")
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(S.px(70))
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(lbl)

        lbl = QLabel("%")
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(S.px(40))
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(lbl)

        lbl = QLabel("Usage")
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(S.px(80))
        col_header.addWidget(lbl)
        process_card.add_layout(col_header)

        # Process rows
        self._process_container = QWidget()
        self._process_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        process_vlayout = QVBoxLayout()
        process_vlayout.setContentsMargins(0, 0, 0, 0)
        process_vlayout.setSpacing(S.px(3))
        self._process_container.setLayout(process_vlayout)

        for i in range(10):
            row = ProcessRow(name="--", memory_mb=0, percent=0, rank=i + 1)
            row.setMinimumHeight(S.px(30))
            self._process_rows.append(row)
            process_vlayout.addWidget(row)

        process_card.add_widget(self._process_container)
        right_layout.addWidget(process_card, stretch=2)

        # Pressure card
        pressure_card = Card(title="Memory Pressure", icon="⚡")
        self._pressure_graph = MemoryPressureGraph()
        self._pressure_graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pressure_card.add_widget(self._pressure_graph)
        right_layout.addWidget(pressure_card, stretch=1)

        content_layout.addWidget(right_widget, stretch=1)

        main_layout.addWidget(content_container, stretch=1)

        # ===== STATUS BAR =====
        self._setup_status_bar(main_layout)

    def _setup_status_bar(self, parent_layout):
        """Setup bottom status bar"""
        colors = c()

        status_card = Card(title="System Status", icon="🛡️")
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

        # Pressure status
        pressure_widget = QWidget()
        pressure_layout = QVBoxLayout()
        pressure_layout.setSpacing(2)
        pressure_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pressure_title = QLabel("Pressure")
        pressure_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        pressure_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        pressure_layout.addWidget(pressure_title)

        self._pressure_status = QLabel("Normal")
        self._pressure_status.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._pressure_status.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        pressure_layout.addWidget(self._pressure_status)

        pressure_widget.setLayout(pressure_layout)
        status_layout.addWidget(pressure_widget)

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
            self._update_pressure()
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

        self._donut_chart.set_values(used_pct, cached_pct, available_pct)

        self._memory_history.append(used_pct)
        if len(self._memory_history) > self._max_history:
            self._memory_history.pop(0)
        self._usage_graph.add_value(used_pct)

    def _update_pressure(self):
        if not self._current_memory_data:
            return
        colors = c()
        pressure = self._current_memory_data['percent']

        self._pressure_history.append(pressure)
        if len(self._pressure_history) > self._max_history:
            self._pressure_history.pop(0)
        self._pressure_graph.add_value(pressure)

        if pressure >= 90:
            status, status_color = "Critical", colors.ACCENT_RED
        elif pressure >= 70:
            status, status_color = "High", colors.ACCENT_ORANGE
        elif pressure >= 40:
            status, status_color = "Moderate", colors.ACCENT_YELLOW
        else:
            status, status_color = "Normal", colors.ACCENT_GREEN

        self._pressure_status.setText(status)
        self._pressure_status.setStyleSheet(f"color: {status_color}; background: transparent; font-weight: bold;")
        self._pressure_label.setText(status)
        self._pressure_label.setStyleSheet(f"color: {status_color}; padding: {S.px(3)}px {S.px(10)}px; background-color: {colors.BG_SECONDARY}; border-radius: {S.px(10)}px;")

        # Update health indicator
        self._health_label.setText("Healthy" if pressure < 70 else "Warning" if pressure < 90 else "Critical")
        health_color = colors.ACCENT_GREEN if pressure < 70 else colors.ACCENT_ORANGE if pressure < 90 else colors.ACCENT_RED
        self._health_label.setStyleSheet(f"color: {health_color}; background: transparent; font-weight: bold;")

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