"""
Memory View - Memory monitoring dashboard
Modern design with real-time graphs, donut charts, and process list
"""
import time
import psutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPaintEvent, QShowEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QScrollArea, QSizePolicy, QMenu, QPushButton
)

from styles.theme import theme_manager
from scaler import S, ScaleMixin


def c():
    """Access theme colors"""
    return theme_manager.colors


class MemoryDonutChart(QWidget):
    """Donut chart showing memory distribution"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._used_pct = 0
        self._cached_pct = 0
        self._available_pct = 0
        self.setMinimumSize(160, 160)
        self.setMaximumSize(180, 180)
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
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(int(center - 25), int(center + 5), f"{total_mem:.0f} GB")

        painter.end()


class MemoryPressureGraph(QWidget):
    """Real-time memory pressure graph"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._max_points = 60
        self.setMinimumHeight(120)

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
        painter.setBrush(QColor(colors.BG_CARD))
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
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(4, 10, "90-100%")
        painter.drawText(4, int(zone_h * 0.4 + 10), "70-90%")
        painter.drawText(4, int(zone_h * 0.8 + 10), "40-70%")
        painter.drawText(4, int(zone_h * 1.4 + 10), "0-40%")

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


class MemoryUsageGraph(QWidget):
    """Modern real-time memory usage line graph with smooth rendering"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._max_points = 60
        self.setMinimumHeight(140)

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
        painter.setFont(QFont("Segoe UI", 8))
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
            badge_x = w - 65
            badge_y = 8
            painter.setBrush(QColor(colors.BG_SECONDARY))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(badge_x), int(badge_y), 55, 22, 4, 4)

            # Badge text
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.setPen(QColor(badge_color))
            painter.drawText(int(badge_x + 8), int(badge_y + 15), f"{val:.1f}%")

        # Time indicator (positioned to avoid overlapping with badge)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(int(graph_x), int(h - 5), "60s ago")
        # Position "now" text with padding from right edge
        now_x = int(graph_x + graph_w - 35)
        painter.drawText(now_x, int(h - 5), "now")

        # Y-axis label (rotated)
        painter.save()
        painter.translate(12, h / 2)
        painter.rotate(-90)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(colors.TEXT_MUTED))
        painter.drawText(-15, 0, "Usage %")
        painter.restore()

        painter.end()


class ProcessRow(QFrame):
    """Single process memory consumption row"""
    killed = None  # Class variable for callback

    def __init__(self, name: str = "", memory_mb: float = 0, percent: float = 0, rank: int = 0, parent=None):
        super().__init__(parent)
        self._rank = rank
        self._pid = None
        self._memory_mb = memory_mb
        self._percent = percent
        self._setup_ui()
        self.update_values(name, memory_mb, percent, rank)

    def _setup_ui(self):
        colors = c()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_SECONDARY};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {colors.BG_CARD};
            }}
        """)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        self.setLayout(layout)

        self._rank_lbl = QLabel()
        self._rank_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._rank_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._rank_lbl.setFixedWidth(22)
        layout.addWidget(self._rank_lbl)

        self._name_lbl = QLabel()
        self._name_lbl.setFont(QFont("Segoe UI", 9))
        self._name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        self._name_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._name_lbl, stretch=1)

        self._mem_lbl = QLabel()
        self._mem_lbl.setFont(QFont("Segoe UI", 9))
        self._mem_lbl.setStyleSheet(f"color: {colors.ACCENT_CYAN}; background: transparent;")
        self._mem_lbl.setFixedWidth(70)
        self._mem_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._mem_lbl)

        self._pct_lbl = QLabel()
        self._pct_lbl.setFont(QFont("Segoe UI", 9))
        self._pct_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        self._pct_lbl.setFixedWidth(40)
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._pct_lbl)

        self._bar = QProgressBar()
        self._bar.setFixedWidth(80)
        self._bar.setFixedHeight(6)
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
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                color: {c().TEXT_PRIMARY};
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {c().BG_SECONDARY};
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
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
        """)


class MemoryStatCard(QFrame):
    """Memory stat card"""
    def __init__(self, label: str = "", value: str = "--", color: str | None = None, parent=None):
        super().__init__(parent)
        colors = c()
        self._color = color or colors.ACCENT_GREEN
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(20, 12, 20, 12)
        self.setLayout(layout)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 8))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(lbl)

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._value_lbl.setStyleSheet(f"color: {self._color}; background: transparent;")
        layout.addWidget(self._value_lbl)

        self._bar = QProgressBar()
        self._bar.setFixedHeight(3)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._bar)

    def set_value(self, value: str, percent: float | None = None):
        self._value_lbl.setText(str(value))
        if percent is not None:
            self._bar.setValue(int(min(100, max(0, percent))))

    def set_color(self, color: str):
        self._color = color
        self._value_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c().BG_SECONDARY};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)


class MemoryView(QWidget, ScaleMixin):
    """Memory monitoring dashboard"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory_history = []
        self._pressure_history = []
        self._process_rows = []
        self._max_history = 60
        self._current_memory_data = None
        self._update_timer = None
        self._prev_top_pid = None  # Track previous #1 process
        self._highlight_timer = QTimer()  # Timer to remove highlight
        self._highlight_timer.timeout.connect(self._clear_highlight)
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
            return  # Already started
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display_from_signal)
        self._update_timer.start(1000)

    def _update_display_from_signal(self):
        """Called by timer to refresh data from collector signal"""
        # Re-request data update from the current data we have
        # This ensures we still get updates even when not receiving signals
        pass  # Data comes from update_data signal

    def _setup_ui(self):
        colors = c()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        # Header
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 10px; border: 1px solid {colors.BORDER};")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(14, 0, 14, 0)
        header.setLayout(header_layout)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {colors.ACCENT_GREEN}; font-size: 12px; background: transparent;")
        header_layout.addWidget(self._status_dot)

        title = QLabel("Memory Monitor")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._usage_indicator = QLabel("0%")
        self._usage_indicator.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        header_layout.addWidget(self._usage_indicator)

        self._pressure_label = QLabel("Normal")
        self._pressure_label.setFont(QFont("Segoe UI", 9))
        self._pressure_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; padding: 3px 10px; background-color: {colors.BG_SECONDARY}; border-radius: 10px;")
        header_layout.addWidget(self._pressure_label)

        main_layout.addWidget(header)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self._card_used = MemoryStatCard("Used Memory", "-- GB", colors.ACCENT_GREEN)
        self._card_available = MemoryStatCard("Available", "-- GB", colors.ACCENT_BLUE)
        self._card_cached = MemoryStatCard("Cached", "-- GB", colors.ACCENT_PURPLE)
        self._card_free = MemoryStatCard("Free", "-- GB", colors.TEXT_SECONDARY)

        for card in [self._card_used, self._card_available, self._card_cached, self._card_free]:
            stats_layout.addWidget(card, stretch=1)

        main_layout.addLayout(stats_layout)

        # Charts section
        charts_frame = QFrame()
        charts_frame.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 10px; border: 1px solid {colors.BORDER};")
        charts_layout = QHBoxLayout()
        charts_layout.setContentsMargins(10, 8, 10, 8)
        charts_layout.setSpacing(12)
        charts_frame.setLayout(charts_layout)

        # Donut
        donut_container = QWidget()
        donut_layout = QVBoxLayout()
        donut_layout.setContentsMargins(0, 0, 0, 0)
        donut_container.setLayout(donut_layout)

        donut_title = QLabel("Memory Distribution")
        donut_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        donut_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        donut_layout.addWidget(donut_title)

        self._donut_chart = MemoryDonutChart()
        donut_layout.addWidget(self._donut_chart, alignment=Qt.AlignmentFlag.AlignCenter)

        charts_layout.addWidget(donut_container)

        # Line graph
        graph_container = QWidget()
        graph_layout = QVBoxLayout()
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_container.setLayout(graph_layout)

        graph_title = QLabel("Memory Usage Over Time")
        graph_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        graph_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        graph_layout.addWidget(graph_title)

        self._usage_graph = MemoryUsageGraph()
        graph_layout.addWidget(self._usage_graph, stretch=1)

        charts_layout.addWidget(graph_container, stretch=1)

        main_layout.addWidget(charts_frame, stretch=1)

        # Process section
        process_frame = QFrame()
        process_frame.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 10px; border: 1px solid {colors.BORDER};")
        process_layout = QVBoxLayout()
        process_layout.setContentsMargins(12, 10, 12, 10)
        process_layout.setSpacing(0)
        process_frame.setLayout(process_layout)

        # Header with title and view all button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)

        process_title = QLabel("Top Processes")
        process_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        process_title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(process_title)

        header_layout.addStretch()

        self._view_all_btn = QPushButton("View all")
        self._view_all_btn.setFont(QFont("Segoe UI", 9))
        self._view_all_btn.setFixedHeight(24)
        self._view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_all_btn.clicked.connect(self._show_all_processes)
        self._view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_SECONDARY};
                color: {colors.TEXT_SECONDARY};
                border: 1px solid {colors.BORDER};
                border-radius: 4px;
                padding: 2px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
                border-color: {colors.ACCENT_PURPLE};
            }}
        """)
        header_layout.addWidget(self._view_all_btn)
        process_layout.addLayout(header_layout)

        # Column headers
        col_header = QHBoxLayout()
        col_header.setContentsMargins(4, 0, 4, 4)
        col_header.setSpacing(10)

        lbl = QLabel("#")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(24)
        col_header.addWidget(lbl)

        lbl = QLabel("Process")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        col_header.addWidget(lbl, stretch=1)

        lbl = QLabel("Memory")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(70)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(lbl)

        lbl = QLabel("%")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(45)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(lbl)

        lbl = QLabel("Usage")
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        lbl.setFixedWidth(80)
        col_header.addWidget(lbl)
        process_layout.addLayout(col_header)

        # Process rows
        self._process_container = QWidget()
        process_vlayout = QVBoxLayout()
        process_vlayout.setContentsMargins(0, 0, 0, 0)
        process_vlayout.setSpacing(3)
        self._process_container.setLayout(process_vlayout)

        for i in range(10):
            row = ProcessRow(name="--", memory_mb=0, percent=0, rank=i + 1)
            row.setFixedHeight(30)
            self._process_rows.append(row)
            process_vlayout.addWidget(row)

        process_layout.addWidget(self._process_container)

        main_layout.addWidget(process_frame)

        # Pressure section
        pressure_frame = QFrame()
        pressure_frame.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 10px; border: 1px solid {colors.BORDER};")
        pressure_layout = QVBoxLayout()
        pressure_layout.setContentsMargins(10, 8, 10, 8)
        pressure_layout.setSpacing(8)
        pressure_frame.setLayout(pressure_layout)

        pressure_title_row = QHBoxLayout()
        pressure_title = QLabel("Memory Pressure Over Time")
        pressure_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        pressure_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        pressure_title_row.addWidget(pressure_title)
        pressure_title_row.addStretch()

        self._pressure_status = QLabel("Normal")
        self._pressure_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._pressure_status.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent; padding: 3px 10px; background-color: {colors.BG_SECONDARY}; border-radius: 8px;")
        pressure_title_row.addWidget(self._pressure_status)
        pressure_layout.addLayout(pressure_title_row)

        self._pressure_graph = MemoryPressureGraph()
        pressure_layout.addWidget(self._pressure_graph)

        main_layout.addWidget(pressure_frame)

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

        self._card_used.set_value(f"{used_gb:.1f} GB", used_pct)
        self._card_available.set_value(f"{available_gb:.1f} GB", available_pct)
        self._card_cached.set_value(f"{cached_gb:.1f} GB", cached_pct)
        self._card_free.set_value(f"{free_gb:.1f} GB", free_pct)

        if used_pct > 90:
            self._card_used.set_color(colors.ACCENT_RED)
        elif used_pct > 70:
            self._card_used.set_color(colors.ACCENT_ORANGE)
        elif used_pct > 40:
            self._card_used.set_color(colors.ACCENT_YELLOW)
        else:
            self._card_used.set_color(colors.ACCENT_GREEN)

        self._usage_indicator.setText(f"{used_pct:.0f}%")
        if used_pct > 90:
            self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_RED}; font-size: 16px; font-weight: bold; background: transparent;")
        elif used_pct > 70:
            self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_ORANGE}; font-size: 16px; font-weight: bold; background: transparent;")
        elif used_pct > 40:
            self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_YELLOW}; font-size: 16px; font-weight: bold; background: transparent;")
        else:
            self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_GREEN}; font-size: 16px; font-weight: bold; background: transparent;")

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
        self._pressure_status.setStyleSheet(f"color: {status_color}; background-color: {colors.BG_SECONDARY}; padding: 3px 10px; border-radius: 8px; font-weight: bold;")
        self._pressure_label.setText(status)
        self._pressure_label.setStyleSheet(f"color: {status_color}; padding: 3px 10px; background-color: {colors.BG_SECONDARY}; border-radius: 10px;")

    def _update_processes(self):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 0:
                        mem_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                        processes.append({
                            'name': info['name'],
                            'memory_mb': mem_mb,
                            'percent': info['memory_percent'],
                            'pid': info['pid'],
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            processes.sort(key=lambda x: x['percent'], reverse=True)
            top_10 = processes[:10]

            # Check if new #1 process
            if top_10 and top_10[0]['pid'] != self._prev_top_pid:
                self._prev_top_pid = top_10[0]['pid']
                self._highlight_row(0)  # Highlight new #1

            for i in range(10):
                if i < len(top_10):
                    proc = top_10[i]
                    self._process_rows[i].update_values(
                        proc['name'], proc['memory_mb'], proc['percent'], i + 1, proc['pid']
                    )
                    self._process_rows[i].show()
                else:
                    self._process_rows[i].hide()
        except Exception as e:
            print(f"Process update error: {e}")

    def _highlight_row(self, index):
        """Briefly highlight a row when it becomes the new #1"""
        if index >= len(self._process_rows):
            return
        row = self._process_rows[index]
        colors = c()

        # Apply highlight animation
        highlight_color = QColor(colors.ACCENT_GREEN)
        highlight_color.setAlpha(40)
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {highlight_color.name()};
                border-radius: 6px;
                border: 1px solid {colors.ACCENT_GREEN};
            }}
        """)

        # Stop any existing highlight timer and restart
        self._highlight_timer.stop()
        self._highlight_timer.start(1500)  # Remove highlight after 1.5s

    def _clear_highlight(self):
        """Remove highlight from highlighted row"""
        self._highlight_timer.stop()
        for row in self._process_rows:
            if row.isVisible():
                colors = c()
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {colors.BG_SECONDARY};
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        background-color: {colors.BG_CARD};
                    }}
                """)

    def _show_all_processes(self):
        """Show dialog with all running processes"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame, QLabel
        from PyQt6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 650)
        colors = c()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        dialog.setLayout(main_layout)

        # Title bar
        title_bar = QFrame()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet(f"background-color: {colors.BG_CARD}; border-bottom: 1px solid {colors.BORDER};")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 10, 0)
        title_bar.setLayout(title_layout)

        title = QLabel("All Processes by Memory")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(title)

        title_layout.addStretch()

        close_btn = QPushButton("X")
        close_btn.setFixedSize(36, 36)
        close_btn.setFont(QFont("Segoe UI", 12))
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
        table.setFont(QFont("Segoe UI", 10))
        table.horizontalHeader().setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
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
                padding: 8px 12px;
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
                padding: 10px 12px;
                font-weight: bold;
            }}
            QHeaderView {{
                border: none;
            }}
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.SectionResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.SectionResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.SectionResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.SectionResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.SectionResizeMode.Fixed)
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