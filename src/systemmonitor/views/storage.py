"""
Storage View — Professional storage monitoring dashboard
Clean dashboard layout with live metrics, animated KPI cards, and per-disk panels.
"""
from typing import Dict
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
from systemmonitor.widgets.storage_widgets import StorageDiskCard
from systemmonitor.widgets.ref_design import (
    PageHeader, KpiTile, ReflowGrid, AreaChart, ChartPanel, BarPanel)


class _StorageHdr(PageHeader):
    """Reference header with the StorageHeader API (set_disk_count / set_live)."""

    def __init__(self, parent=None):
        super().__init__(tr("Storage"), tr("Disk space, performance and disk operations"),
                         "ph.database", pill=tr("LIVE"), parent=parent)
        self._count = 0

    def set_disk_count(self, n: int):
        if n != self._count:
            self._count = n
            self.sub_lbl.setText(f"{tr('Disk space, performance and disk operations')}  \u00b7  {n} {tr('disks')}")

    def set_live(self, live: bool):
        self.pill.set_state("ok" if live else "bad", tr("LIVE") if live else tr("Offline"))


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
        self._perf_latency = None
        self._perf_iops = None
        self._perf_bandwidth = None
        self._perf_load = None
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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main = QVBoxLayout()
        main.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        main.setSpacing(S.px(10))
        self.setLayout(main)

        # Header
        self._header = _StorageHdr()
        main.addWidget(self._header)

        # KPI row
        self._kpi_capacity = KpiTile("Total Capacity", "ph.hard-drives", "ACCENT_CYAN")
        self._kpi_used = KpiTile("Used", "ph.database", "ACCENT_GREEN")
        self._kpi_free = KpiTile("Free", "ph.check-circle", "STATUS_GREEN")
        self._kpi_read = KpiTile("Read Speed", "ph.arrow-down", "ACCENT_CYAN")
        self._kpi_write = KpiTile("Write Speed", "ph.arrow-up", "ACCENT_GREEN")

        # KPI tiles re-flow (5 across on wide windows, wrapping on narrow ones)
        kpi_grid = ReflowGrid([(k, 1) for k in (self._kpi_capacity, self._kpi_used, self._kpi_free,
                                                 self._kpi_read, self._kpi_write)],
                              max_cols=5, min_col_width=170)
        main.addWidget(kpi_grid)

        # ── Scroll area wraps disk cards + perf section ───────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")

        inner = QWidget()
        inner.setObjectName("RefContent")
        inner.setStyleSheet("QWidget#RefContent { background: transparent; }")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, S.px(4), 0)
        inner_lay.setSpacing(S.px(10))

        # Disk cards (re-flow into 1..3 columns)
        self._disk_cards_inner = ReflowGrid([], max_cols=3, min_col_width=520)
        inner_lay.addWidget(self._disk_cards_inner)

        # ── Performance charts ────────────────────────────────────────────────
        def _bytes_fmt(v):
            for unit, div in (("GB/s", 1024 ** 3), ("MB/s", 1024 ** 2), ("KB/s", 1024)):
                if v >= div:
                    n = v / div
                    return (f"{n:.0f}" if n >= 10 else f"{n:.1f}") + f" {unit}"
            return f"{v:.0f} B/s"

        self._perf_bandwidth = AreaChart(["ACCENT_GREEN", "ACCENT_CYAN"], None, y_fmt=_bytes_fmt)
        p_bw = ChartPanel(tr("Disk throughput"), "ph.chart-line", self._perf_bandwidth, tabs=True,
                          legend=[("ACCENT_GREEN", tr("Write")), ("ACCENT_CYAN", tr("Read"))])
        p_bw.setMinimumHeight(S.px(230))

        self._perf_iops = AreaChart(["ACCENT_GREEN", "ACCENT_CYAN"], None,
                                    y_fmt=lambda v: f"{v:.0f}", min_auto=10.0)
        p_iops = ChartPanel(tr("Disk Operations"), "ph.activity", self._perf_iops, tabs=True,
                            legend=[("ACCENT_GREEN", tr("Write")), ("ACCENT_CYAN", tr("Read"))])
        p_iops.setMinimumHeight(S.px(230))

        self._perf_latency = AreaChart(["ACCENT_GREEN", "ACCENT_CYAN"], None,
                                       y_fmt=lambda v: f"{v:.1f} ms", min_auto=1.0)
        p_lat = ChartPanel(tr("Disk Latency"), "ph.timer", self._perf_latency, tabs=True,
                           legend=[("ACCENT_GREEN", tr("Write")), ("ACCENT_CYAN", tr("Read"))])
        p_lat.setMinimumHeight(S.px(230))

        self._perf_load = AreaChart(["ACCENT_GREEN"], 100.0)
        p_load = ChartPanel(tr("Disk Load"), "ph.gauge", self._perf_load, tabs=True)
        p_load.setMinimumHeight(S.px(230))

        self._bw_panel = BarPanel(tr("Disk bandwidth"), "ph.arrows-down-up")
        self._bw_panel.add_row("write", "Write", "ACCENT_GREEN")
        self._bw_panel.add_row("read", "Read", "ACCENT_CYAN")
        self._bw_peak = 1.0

        perf = ReflowGrid([(p_bw, 1), (p_iops, 1), (p_lat, 1), (p_load, 1), (self._bw_panel, 2)],
                          max_cols=2, min_col_width=480)
        inner_lay.addWidget(perf)
        inner_lay.addStretch(1)

        scroll.setWidget(inner)
        perf.bind_viewport(scroll)
        main.addWidget(scroll, stretch=1)

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update_tick)
        self._update_timer.start(self._update_interval_ms)

    def _on_setting_changed(self, key: str, value):
        pass  # history length is handled by the chart range tabs

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
                self._disk_cards_inner.add_widget(card)
            else:
                self._disk_cards[dev].update_disk_info(disk)
            self._disk_cards[dev].update_speeds(
                disk.get("read_rate", 0), disk.get("write_rate", 0)
            )

        for dev in list(self._disk_cards.keys()):
            if dev not in current:
                gone = self._disk_cards.pop(dev)
                self._disk_cards_inner.remove_widget(gone)
                gone.deleteLater()

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

        # Performance history graphs (same data keys as before)
        if self._perf_latency is not None:
            self._perf_latency.push(
                data.get('total_write_latency_ms', 0),
                data.get('total_read_latency_ms', 0),
            )
        if self._perf_iops is not None:
            self._perf_iops.push(
                data.get('total_write_iops', 0),
                data.get('total_read_iops', 0),
            )
        if self._perf_bandwidth is not None:
            self._perf_bandwidth.push(total_write, total_read)
            self._bw_peak = max(total_write, total_read, self._bw_peak * 0.995, 1.0)
            self._bw_panel.set_row("write", total_write / self._bw_peak * 100,
                                   "{} {}".format(*self._fmt_speed(total_write)))
            self._bw_panel.set_row("read", total_read / self._bw_peak * 100,
                                   "{} {}".format(*self._fmt_speed(total_read)))
        if self._perf_load is not None:
            busy = data.get('total_busy_pct', 0) or 0
            self._perf_load.push(busy)
            self._perf_load.set_overlay(f"{busy:.0f} %")

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
