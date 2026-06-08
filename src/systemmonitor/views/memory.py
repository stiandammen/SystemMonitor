"""
Memory View - Professional memory monitoring dashboard
Enterprise-grade design with real-time graphs and donut charts
"""
import time
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QShowEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QPushButton, QScrollArea
)

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, language_manager, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.widgets.card import Card
from systemmonitor.widgets.memory_widgets import MemoryKpiCard, MemoryWaveChart, MemoryUsageGraph
import qtawesome as qta


def c():
    """Access theme colors"""
    return theme_manager.colors


class MemoryView(QWidget, ScaleMixin, I18nMixin):
    """Memory monitoring dashboard with professional enterprise design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory_history = []
        self._max_history = 60
        self._current_memory_data = None
        self._update_timer = None
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        from systemmonitor.core.signals import signal_bus
        signal_bus.setting_changed.connect(self._on_setting_changed)

    def _on_setting_changed(self, key: str, value):
        if key in ('history_duration', 'update_interval'):
            self._apply_history_length()

    def _apply_history_length(self):
        """Resize the usage graph buffer based on the History Length setting"""
        from systemmonitor.config import settings, AppConfig
        points, stride = AppConfig.history_window(
            settings.get('history_duration', 300),
            settings.get('update_interval', 500))
        if hasattr(self, '_usage_graph') and self._usage_graph is not None:
            self._usage_graph.set_max_points(points)
            self._usage_graph.set_sample_stride(stride)

    def on_scale_changed(self, factor: float):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def retranslate_ui(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

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

        live_label = QLabel(tr("LIVE"))
        live_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        live_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_layout.addWidget(live_label)

        header_layout.addLayout(live_layout)

        title = QLabel(tr("Memory Monitor"))
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

        # ===== MAIN CONTENT =====
        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(S.px(12))
        content_container.setLayout(content_layout)

        # Charts column
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(S.px(12))
        left_widget.setLayout(left_layout)

        # Distribution card
        dist_card = Card(title=tr("Memory Distribution"), icon="ph.chart-pie")
        self._wave_chart = MemoryWaveChart()
        dist_card.add_widget(self._wave_chart)
        left_layout.addWidget(dist_card, stretch=1)

        # Usage graph card
        graph_card = Card(title=tr("Memory Usage Over Time"), icon="ph.chart-line")
        self._usage_graph = MemoryUsageGraph()
        self._usage_graph.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        graph_card.add_widget(self._usage_graph)
        left_layout.addWidget(graph_card, stretch=1)

        content_layout.addWidget(left_widget, stretch=1)

        main_layout.addWidget(content_container, stretch=1)

        # ===== STATUS BAR =====
        self._setup_status_bar(main_layout)

        self._apply_history_length()

    def _setup_status_bar(self, parent_layout):
        """Setup bottom status bar"""
        colors = c()

        status_card = Card(title=tr("System Status"), icon="mdi.shield-check")
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

        self._health_label = QLabel(tr("Healthy"))
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

        total_title = QLabel(tr("Total Memory"))
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

        used_title = QLabel(tr("Used"))
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

        type_title = QLabel(tr("Memory Type"))
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
            if 'memory' in data:
                self._current_memory_data = data['memory']
            
            self._schedule_display_update()
        except Exception:
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
        except Exception:
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

        # Health label
        if used_pct >= 90:
            h_text, h_color = tr("Critical"), colors.ACCENT_RED
        elif used_pct >= 70:
            h_text, h_color = tr("Warning"),  colors.ACCENT_ORANGE
        else:
            h_text, h_color = tr("Healthy"),  colors.ACCENT_GREEN
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
