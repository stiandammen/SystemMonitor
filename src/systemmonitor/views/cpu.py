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
from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, language_manager, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.logger import get_logger, LogCategory, log_debug
from systemmonitor.widgets.cpu_graph import CpuGraphWidget
from systemmonitor.widgets.sensor_widgets import SensorsPanel


def c():
    return theme_manager.colors


class CPUView(QWidget, ScaleMixin, I18nMixin):
    """CPU monitoring dashboard with per-core graphs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._core_graphs = []
        self._per_core = []
        self._total_usage = 0
        self._update_scheduled = False
        self._sensors_panel = None
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def _on_theme_changed(self, theme_name: str):
        self.update()

    def retranslate_ui(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def set_data_collector(self, collector):
        """Set data collector and connect signals"""
        if collector:
            collector.data_ready.connect(self._on_data_ready)

    def update_data(self, data: dict):
        """Handle data update from window"""
        self._update_sensors(data)
        if 'cpu' not in data:
            return
        cpu = data['cpu']
        self._per_core = cpu.get('per_core', [])
        self._total_usage = cpu.get('percent', 0)
        if not getattr(self, '_update_scheduled', False):
            self._update_scheduled = True
            QTimer.singleShot(16, self._perform_update)

    def _update_sensors(self, data: dict):
        if self._sensors_panel is None:
            return
        sensors = data.get('system_info', {}).get('sensors')
        if not sensors:
            return

        fans = [
            (f.get('label', 'Fan'), f"{f['rpm']:.0f} RPM" if f.get('rpm') else "—")
            for f in sensors.get('fans', [])
        ]
        voltages = [
            (v.get('label', 'Rail'), f"{v['volts']:.2f} V" if v.get('volts') else "—")
            for v in sensors.get('voltages', [])
        ]
        self._sensors_panel.update_sensors(fans, voltages)

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

        self._sensors_panel = SensorsPanel()
        main_layout.addWidget(self._sensors_panel)

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

        title = QLabel(tr("CPU Monitor"))
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
        title = QLabel(tr("Per-Core Usage"))
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
