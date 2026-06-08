"""
Storage View — Professional storage monitoring dashboard
Clean dashboard layout with live metrics, animated KPI cards, and per-disk panels.
"""
from systemmonitor.typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, language_manager, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.logger import LogCategory, log_info, log_exception
from systemmonitor.data.storage import StorageCollector
from systemmonitor.widgets.storage_widgets import StorageDiskCard, PerformanceHistoryGraph
from systemmonitor.widgets.storage_view_widgets import StorageHeader, StorageKpiCard


# ─────────────────────────────────────────────────────────────────────────────
# StorageView
# ─────────────────────────────────────────────────────────────────────────────
class StorageView(QWidget, ScaleMixin, I18nMixin):
    """Main storage monitoring page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disk_cards: Dict[str, StorageDiskCard] = {}
        self._collector = None
        self._collector_started = False
        self._update_interval_ms = 1000
        self._perf_latency: PerformanceHistoryGraph | None = None
        self._perf_iops: PerformanceHistoryGraph | None = None
        self._perf_bandwidth: PerformanceHistoryGraph | None = None
        self._perf_load: PerformanceHistoryGraph | None = None
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        from systemmonitor.core.signals import signal_bus
        signal_bus.setting_changed.connect(self._on_setting_changed)

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._setup_ui)

    def retranslate_ui(self):
        QTimer.singleShot(0, self._setup_ui)

    def _setup_ui(self):
        self._disk_cards.clear()

        if hasattr(self, "_update_timer") and self._update_timer is not None:
            self._update_timer.stop()
            self._update_timer.deleteLater()
            self._update_timer = None

        # Stop the collector to prevent data updates during teardown
        if self._collector_started:
            self._collector.stop()
            if self._collector.isRunning():
                self._collector.requestInterruption()
                self._collector.wait(500)
            self._collector_started = False
            self._collector = None

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

        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main = QVBoxLayout()
        main.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        main.setSpacing(S.px(12))
        self.setLayout(main)

        # Header
        self._header = StorageHeader()
        main.addWidget(self._header)

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(S.px(10))

        self._kpi_capacity = StorageKpiCard(
            "Total Capacity", "fa5s.hdd", colors.ACCENT_BLUE)
        self._kpi_used = StorageKpiCard(
            "Used", "mdi.database", colors.ACCENT_ORANGE)
        self._kpi_free = StorageKpiCard(
            "Free", "mdi.check-circle", colors.ACCENT_GREEN)
        self._kpi_read = StorageKpiCard(
            "Read Speed", "mdi.arrow-down-bold", colors.ACCENT_GREEN)
        self._kpi_write = StorageKpiCard(
            "Write Speed", "mdi.arrow-up-bold", colors.ACCENT_BLUE)

        for kpi in [self._kpi_capacity, self._kpi_used, self._kpi_free,
                    self._kpi_read, self._kpi_write]:
            kpi_row.addWidget(kpi)

        kpi_widget = QWidget()
        kpi_widget.setLayout(kpi_row)
        main.addWidget(kpi_widget)

        # ── Scroll area wraps disk cards + perf section ───────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, S.px(2), 0)
        inner_lay.setSpacing(S.px(12))

        # Section divider — "PHYSICAL DISKS"
        section_row = QHBoxLayout()
        section_row.setSpacing(0)
        section_row.setContentsMargins(0, S.px(2), 0, 0)

        accent_bar = QFrame()
        accent_bar.setFixedSize(S.px(3), S.px(16))
        accent_bar.setStyleSheet(
            f"background-color: {colors.ACCENT_GREEN};"
            f"border-radius: {S.px(2)}px;"
        )
        section_row.addWidget(accent_bar)
        section_row.addSpacing(S.px(10))

        section_lbl = QLabel(tr("PHYSICAL DISKS"))
        section_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        section_lbl.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        section_row.addWidget(section_lbl)
        section_row.addSpacing(S.px(12))

        rule = QFrame()
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setFixedHeight(1)
        rule.setStyleSheet(f"background-color: {colors.BORDER}; border: none;")
        section_row.addWidget(rule, stretch=1)

        inner_lay.addLayout(section_row)

        # Disk card container — no stretch so cards stay compact
        disk_container = QWidget()
        disk_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._disk_cards_inner = QVBoxLayout()
        self._disk_cards_inner.setSpacing(S.px(10))
        self._disk_cards_inner.setContentsMargins(0, 0, 0, 0)
        disk_container.setLayout(self._disk_cards_inner)
        inner_lay.addWidget(disk_container)

        # ── TOTAL PERFORMANCE section ─────────────────────────────────────────
        perf_section_row = QHBoxLayout()
        perf_section_row.setSpacing(0)
        perf_section_row.setContentsMargins(0, S.px(6), 0, 0)

        perf_accent = QFrame()
        perf_accent.setFixedSize(S.px(3), S.px(16))
        perf_accent.setStyleSheet(
            f"background-color: {colors.ACCENT_BLUE};"
            f"border-radius: {S.px(2)}px;"
        )
        perf_section_row.addWidget(perf_accent)
        perf_section_row.addSpacing(S.px(10))

        perf_section_lbl = QLabel(tr("TOTAL PERFORMANCE"))
        perf_section_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        perf_section_lbl.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        perf_section_row.addWidget(perf_section_lbl)
        perf_section_row.addSpacing(S.px(12))

        perf_rule = QFrame()
        perf_rule.setFrameShape(QFrame.Shape.HLine)
        perf_rule.setFixedHeight(1)
        perf_rule.setStyleSheet(f"background-color: {colors.BORDER}; border: none;")
        perf_section_row.addWidget(perf_rule, stretch=1)
        inner_lay.addLayout(perf_section_row)

        # Row 1: Latency + IOPS
        perf_row1 = QHBoxLayout()
        perf_row1.setSpacing(S.px(10))

        self._perf_latency = PerformanceHistoryGraph("Disk Latency", unit='ms', max_points=90)
        self._perf_latency.add_series("Write", colors.ACCENT_YELLOW, 'scatter')
        self._perf_latency.add_series("Read", colors.ACCENT_ORANGE, 'scatter')
        self._perf_latency.setMinimumHeight(S.px(190))
        self._perf_latency.setMaximumHeight(S.px(220))
        perf_row1.addWidget(self._perf_latency)

        self._perf_iops = PerformanceHistoryGraph("Disk Operations", unit='iops', max_points=90)
        self._perf_iops.add_series("Write", colors.TEXT_SECONDARY, 'line')
        self._perf_iops.add_series("Read", colors.ACCENT_GREEN, 'line')
        self._perf_iops.setMinimumHeight(S.px(190))
        self._perf_iops.setMaximumHeight(S.px(220))
        perf_row1.addWidget(self._perf_iops)

        inner_lay.addLayout(perf_row1)

        # Row 2: Bandwidth + Load
        perf_row2 = QHBoxLayout()
        perf_row2.setSpacing(S.px(10))

        self._perf_bandwidth = PerformanceHistoryGraph("Disk Bandwidth", unit='B/s', max_points=90)
        self._perf_bandwidth.add_series("Write", colors.ACCENT_BLUE, 'line')
        self._perf_bandwidth.add_series("Read", colors.ACCENT_GREEN, 'line')
        self._perf_bandwidth.setMinimumHeight(S.px(190))
        self._perf_bandwidth.setMaximumHeight(S.px(220))
        perf_row2.addWidget(self._perf_bandwidth)

        self._perf_load = PerformanceHistoryGraph("Disk Load", unit='%', max_points=90)
        self._perf_load.add_series("Load", colors.ACCENT_ORANGE, 'line')
        self._perf_load.setMinimumHeight(S.px(190))
        self._perf_load.setMaximumHeight(S.px(220))
        perf_row2.addWidget(self._perf_load)

        inner_lay.addLayout(perf_row2)
        inner_lay.addStretch(1)

        scroll.setWidget(inner)
        main.addWidget(scroll, stretch=1)

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update_tick)
        self._update_timer.start(self._update_interval_ms)

        self._apply_history_length()

    def _on_setting_changed(self, key: str, value):
        if key in ('history_duration', 'update_interval'):
            self._apply_history_length()

    def _apply_history_length(self):
        """Resize the performance history graph buffers based on the History Length setting"""
        from systemmonitor.config import settings, AppConfig
        points, stride = AppConfig.history_window(
            settings.get('history_duration', 300),
            settings.get('update_interval', 500))
        for graph in (self._perf_latency, self._perf_iops,
                      self._perf_bandwidth, self._perf_load):
            if graph is not None:
                graph.set_max_points(points)
                graph.set_sample_stride(stride)

    # ── collector ─────────────────────────────────────────────────────────
    def start_collector(self):
        if self._collector_started:
            return
        try:
            self._collector = StorageCollector()
            self._collector.data_updated.connect(self._on_collector_data)
            self._collector.start()
            self._collector_started = True
            log_info(LogCategory.DISK, "Storage collector started")
        except Exception as e:
            log_exception(LogCategory.DISK, "Failed to start storage collector", e)

    def _on_collector_data(self, data: dict):
        self._update_from_data(data)

    def _on_update_tick(self):
        if not self._collector_started:
            self.start_collector()

    # ── data update ───────────────────────────────────────────────────────
    def _update_from_data(self, data: dict):
        disks = data.get("disks", [])
        self._header.set_disk_count(len(disks))

        current = set()
        for disk in disks:
            dev = disk.get("device", f"unknown_{id(disk)}")
            current.add(dev)
            if dev not in self._disk_cards:
                card = StorageDiskCard(disk)
                self._disk_cards[dev] = card
                self._disk_cards_inner.addWidget(card)
            else:
                self._disk_cards[dev].update_disk_info(disk)
            self._disk_cards[dev].update_speeds(
                disk.get("read_rate", 0), disk.get("write_rate", 0)
            )

        for dev in list(self._disk_cards.keys()):
            if dev not in current:
                self._disk_cards.pop(dev).deleteLater()

        # KPI aggregates
        total_size  = sum(d.get("total", 0) for d in disks)
        total_used  = sum(d.get("used",  0) for d in disks)
        total_free  = sum(d.get("free",  0) for d in disks)
        total_read  = data.get("total_read_rate",  0)
        total_write = data.get("total_write_rate", 0)

        total_tb = total_size / (1024 ** 4)
        if total_tb >= 1:
            self._kpi_capacity.set_value(f"{total_tb:.1f}", "TB")
        else:
            self._kpi_capacity.set_value(
                f"{total_size / (1024**3):.0f}", "GB")

        used_gb = total_used / (1024**3)
        self._kpi_used.set_value(
            f"{used_gb:.0f}" if used_gb >= 1 else f"{used_gb:.1f}", "GB")

        free_gb = total_free / (1024**3)
        self._kpi_free.set_value(
            f"{free_gb:.0f}" if free_gb >= 1 else f"{free_gb:.1f}", "GB")

        self._kpi_read.set_value(*self._fmt_speed(total_read))
        self._kpi_write.set_value(*self._fmt_speed(total_write))
        self._header.set_live(True)

        # Performance history graphs
        if self._perf_latency is not None:
            self._perf_latency.push(
                Write=data.get('total_write_latency_ms', 0),
                Read=data.get('total_read_latency_ms', 0),
            )
        if self._perf_iops is not None:
            self._perf_iops.push(
                Write=data.get('total_write_iops', 0),
                Read=data.get('total_read_iops', 0),
            )
        if self._perf_bandwidth is not None:
            self._perf_bandwidth.push(
                Write=total_write,
                Read=total_read,
            )
        if self._perf_load is not None:
            self._perf_load.push(
                Load=data.get('total_busy_pct', 0),
            )

    @staticmethod
    def _fmt_speed(bps: float):
        if bps >= 1_073_741_824: # 1 GB/s
            return f"{bps/1_073_741_824:.1f}", "GB/s"
        if bps >= 104_857: # Over 100 KB/s, show as MB/s with decimal
            return f"{bps/1_048_576:.1f}", "MB/s"
        if bps >= 1024:
            return f"{bps/1024:.0f}", "KB/s"
        return f"{bps:.0f}", "B/s"

    def _on_theme_changed(self, _):
        for card in self._disk_cards.values():
            card._on_theme_changed("")

    def update_data(self, data: dict):
        if "disks" in data:
            self._update_from_data(data)

    def shutdown(self):
        if hasattr(self, "_update_timer"):
            self._update_timer.stop()
        if self._collector_started:
            self._collector.stop()
            if self._collector.isRunning():
                self._collector.requestInterruption()
                self._collector.wait(500)
            self._collector_started = False
            self._collector = None
