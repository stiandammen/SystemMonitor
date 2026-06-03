"""
CPU View - Per-core CPU usage graphs
Optimized for professional technician-grade performance
"""
import platform
import time
import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.logger import get_logger, LogCategory, log_debug


def c():
    return theme_manager.colors


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

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def set_value(self, value: float):
        """Set current CPU value with smooth animation"""
        self._display_value += (value - self._display_value) * 0.3

        if not self._history or len(self._history) > 0:
            self._history.append(value)
            if len(self._history) > self._max_points:
                self._history.pop(0)

        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def paintEvent(self, a0):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = c()
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

            from PyQt6.QtCore import QPoint
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


class CPUView(QWidget, ScaleMixin):
    """CPU monitoring dashboard with per-core graphs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._core_graphs = []
        self._per_core = []
        self._total_usage = 0
        self._update_scheduled = False
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def _on_theme_changed(self, theme_name: str):
        self.update()

    def set_data_collector(self, collector):
        """Set data collector and connect signals"""
        if collector:
            collector.data_ready.connect(self._on_data_ready)

    def update_data(self, data: dict):
        """Handle data update from window"""
        if 'cpu' not in data:
            return
        cpu = data['cpu']
        self._per_core = cpu.get('per_core', [])
        self._total_usage = cpu.get('percent', 0)
        if not getattr(self, '_update_scheduled', False):
            self._update_scheduled = True
            QTimer.singleShot(16, self._perform_update)

    def _on_data_ready(self, data: dict):
        """Handle data from background thread"""
        if 'cpu' not in data:
            return
        cpu = data['cpu']
        self._per_core = cpu.get('per_core', [])
        self._total_usage = cpu.get('percent', 0)
        if not getattr(self, '_update_scheduled', False):
            self._update_scheduled = True
            QTimer.singleShot(16, self._perform_update)

    def _perform_update(self):
        """Perform the actual UI update"""
        self._update_scheduled = False
        try:
            per_core = self._per_core
            total_usage = self._total_usage
            colors = c()

            if total_usage > 80:
                usage_color = colors.ACCENT_RED
            elif total_usage > 60:
                usage_color = colors.ACCENT_ORANGE
            elif total_usage > 40:
                usage_color = colors.ACCENT_YELLOW
            else:
                usage_color = colors.ACCENT_BLUE

            if hasattr(self, '_usage_indicator'):
                self._usage_indicator.setStyleSheet(f"color: {usage_color}; font-size: {S.font_pt(18)}px; font-weight: bold; background: transparent;")
                self._usage_indicator.setText(f"{total_usage:.0f}%")

            for i, usage in enumerate(per_core if isinstance(per_core, list) else []):
                if i < len(self._core_graphs):
                    self._core_graphs[i].set_value(usage)
        except Exception:
            pass

    def _setup_ui(self):
        """Setup CPU view UI"""
        # Tear down the old layout so setLayout() succeeds on rebuild
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        self._core_graphs.clear()

        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(20), S.px(16), S.px(20), S.px(16))
        main_layout.setSpacing(S.px(16))
        self.setLayout(main_layout)

        header = self._create_header()
        main_layout.addWidget(header)

        graphs_section = self._create_graphs_section()
        main_layout.addWidget(graphs_section, stretch=1)

        main_layout.addStretch()

    def _create_header(self):
        """Header with title and overall usage"""
        colors = c()

        header = QFrame()
        header.setMinimumHeight(S.px(50))
        header.setMaximumHeight(S.px(60))
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(16), 0, S.px(16), 0)
        header.setLayout(layout)

        cpu_icon = QLabel()
        cpu_icon.setStyleSheet("background: transparent;")
        try:
            sz = S.px(22)
            cpu_icon.setPixmap(qta.icon("ph.cpu", color=colors.ACCENT_GREEN).pixmap(QSize(sz, sz)))
            cpu_icon.setFixedSize(sz, sz)
        except Exception:
            pass
        layout.addWidget(cpu_icon)

        title = QLabel("CPU Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        self._usage_indicator = QLabel("0%")
        self._usage_indicator.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        layout.addWidget(self._usage_indicator)

        return header

    def _create_graphs_section(self):
        """Core graphs in responsive grid"""
        colors = c()

        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(12), S.px(10), S.px(12), S.px(10))
        layout.setSpacing(S.px(10))
        section.setLayout(layout)

        sec_header = QHBoxLayout()
        sec_header.setSpacing(S.px(6))
        sec_header.setContentsMargins(0, 0, 0, 0)
        core_icon = QLabel()
        core_icon.setStyleSheet("background: transparent;")
        try:
            sz = S.px(14)
            core_icon.setPixmap(qta.icon("ph.squares-four", color=colors.TEXT_SECONDARY).pixmap(QSize(sz, sz)))
            core_icon.setFixedSize(sz, sz)
        except Exception:
            pass
        sec_header.addWidget(core_icon)
        title = QLabel("Per-Core Usage")
        title.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        sec_header.addWidget(title)
        sec_header.addStretch()
        layout.addLayout(sec_header)

        grid_container = QWidget()
        self._graphs_grid = QGridLayout()
        self._graphs_grid.setSpacing(S.px(8))
        self._graphs_grid.setContentsMargins(0, 0, 0, 0)
        grid_container.setLayout(self._graphs_grid)

        layout.addWidget(grid_container, stretch=1)

        self._init_core_graphs()

        return section

    def _init_core_graphs(self):
        """Initialize graph widgets based on CPU count"""
        while self._graphs_grid.count():
            item = self._graphs_grid.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        self._core_graphs.clear()

        try:
            logical_count = psutil.cpu_count(logical=True) or 1
        except Exception:
            logical_count = 1

        cols = max(4, min(logical_count, 6))
        rows = (logical_count + cols - 1) // cols

        for i in range(logical_count):
            row = i // cols
            col = i % cols

            graph = CpuGraphWidget(core_index=i)
            self._core_graphs.append(graph)
            self._graphs_grid.addWidget(graph, row, col)

    def resizeEvent(self, a0):
        """Handle resize"""
        super().resizeEvent(a0)
