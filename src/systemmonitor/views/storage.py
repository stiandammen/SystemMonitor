"""
Storage View — Professional storage monitoring dashboard
Clean dashboard layout with live metrics, animated KPI cards, and per-disk panels.
"""
from systemmonitor.typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QGraphicsOpacityEffect, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QResizeEvent, QPainter, QColor, QBrush
)

import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.logger import LogCategory, log_info, log_exception
from systemmonitor.data.storage import StorageCollector
from systemmonitor.widgets.storage_widgets import StorageDiskCard, PerformanceHistoryGraph, ProcessIoTable


# ─────────────────────────────────────────────────────────────────────────────
# StorageHeader
# ─────────────────────────────────────────────────────────────────────────────
class StorageHeader(QWidget, ScaleMixin):
    """Top header bar: pulsing LIVE dot · title · disk count chip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._live_state = True
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = theme_manager.colors
        self.setFixedHeight(S.px(60))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"background-color: {colors.BG_CARD};"
            f"border-radius: {S.px(12)}px;"
        )

        row = QHBoxLayout()
        row.setContentsMargins(S.px(20), 0, S.px(20), 0)
        row.setSpacing(S.px(14))
        self.setLayout(row)

        # ── LIVE dot + label ──────────────────────────────────────────────
        live_row = QHBoxLayout()
        live_row.setSpacing(S.px(7))

        self._live_dot = QFrame()
        self._live_dot.setFixedSize(S.px(9), S.px(9))
        self._live_dot.setStyleSheet(
            f"background-color: {colors.ACCENT_GREEN};"
            f"border-radius: {S.px(4)}px;"
        )
        live_row.addWidget(self._live_dot)

        # Pulsing animation
        self._pulse_fx = QGraphicsOpacityEffect(self._live_dot)
        self._pulse_fx.setOpacity(1.0)
        self._live_dot.setGraphicsEffect(self._pulse_fx)

        fade_out = QPropertyAnimation(self._pulse_fx, b"opacity")
        fade_out.setDuration(850)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.25)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutSine)

        fade_in = QPropertyAnimation(self._pulse_fx, b"opacity")
        fade_in.setDuration(850)
        fade_in.setStartValue(0.25)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse_anim = QSequentialAnimationGroup(self._live_dot)
        self._pulse_anim.addAnimation(fade_out)
        self._pulse_anim.addAnimation(fade_in)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

        live_lbl = QLabel("LIVE")
        live_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        live_lbl.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_row.addWidget(live_lbl)
        row.addLayout(live_row)

        # Thin vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(S.px(28))
        sep.setStyleSheet(f"background-color: {colors.BORDER};")
        row.addWidget(sep)

        # ── Title ─────────────────────────────────────────────────────────
        title = QLabel("Storage Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(17), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        row.addWidget(title)
        row.addStretch()

        # ── Disk count chip ───────────────────────────────────────────────
        chip = QWidget()
        chip.setStyleSheet(
            f"background-color: {colors.BG_HOVER};"
            f"border-radius: {S.px(8)}px;"
        )
        chip_row = QHBoxLayout(chip)
        chip_row.setContentsMargins(S.px(10), S.px(4), S.px(10), S.px(4))
        chip_row.setSpacing(S.px(6))

        hdd_icon = QLabel()
        try:
            ico = qta.icon("fa5s.hdd", color=colors.ACCENT_BLUE)
            hdd_icon.setPixmap(ico.pixmap(S.px(14), S.px(14)))
        except Exception:
            hdd_icon.setText("")
        hdd_icon.setStyleSheet("background: transparent;")
        chip_row.addWidget(hdd_icon)

        self._disk_count_label = QLabel("--")
        self._disk_count_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        self._disk_count_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        chip_row.addWidget(self._disk_count_label)

        unit = QLabel("disker")
        unit.setFont(QFont("Segoe UI", S.font_pt(9)))
        unit.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        chip_row.addWidget(unit)

        row.addWidget(chip)

    def set_disk_count(self, count: int):
        self._disk_count_label.setText(str(count))

    def set_live(self, live: bool):
        colors = theme_manager.colors
        self._live_state = live
        c = colors.ACCENT_GREEN if live else colors.TEXT_MUTED
        self._live_dot.setStyleSheet(
            f"background-color: {c}; border-radius: {S.px(4)}px;"
        )

    def _on_theme_changed(self, _):
        self._setup_ui()
        self.set_live(self._live_state)


# ─────────────────────────────────────────────────────────────────────────────
# StorageKpiCard — individual metric tile with animated top accent bar
# ─────────────────────────────────────────────────────────────────────────────
class StorageKpiCard(QFrame, ScaleMixin):
    """
    Metric tile: top colored accent line, responsive font scaling, icon + value + unit.
    """
    _ACCENT_H = 3  # px of top accent line (scaled)

    def __init__(self, title: str, icon_name: str, accent: str,
                 unit: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon_name = icon_name
        self._accent = accent
        self._unit = unit
        self._value_label: QLabel | None = None
        self._unit_label: QLabel | None = None
        self._title_label: QLabel | None = None
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _):
        self._setup_ui()

    def _setup_ui(self):
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(S.px(82))
        self.setMinimumWidth(S.px(90))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        lay = QVBoxLayout()
        ah = S.px(self._ACCENT_H)
        lay.setContentsMargins(S.px(14), ah + S.px(10), S.px(14), S.px(10))
        lay.setSpacing(S.px(3))
        self.setLayout(lay)

        # Icon + title row
        top = QHBoxLayout()
        top.setSpacing(S.px(6))

        icon_lbl = QLabel()
        try:
            ico = qta.icon(self._icon_name, color=self._accent)
            icon_lbl.setPixmap(ico.pixmap(S.px(14), S.px(14)))
        except Exception:
            icon_lbl.setText("")
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        top.addWidget(icon_lbl)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._title_label.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        top.addWidget(self._title_label, stretch=1)
        lay.addLayout(top)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        self._value_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        lay.addWidget(self._value_label)

        # Unit
        self._unit_label = QLabel(self._unit)
        self._unit_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._unit_label.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        lay.addWidget(self._unit_label)
        lay.addStretch()

    # ── top accent line drawn in paintEvent ──────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        r = S.px(12)
        ah = S.px(self._ACCENT_H)
        painter.save()
        painter.setClipRect(0, 0, self.width(), ah)
        painter.setBrush(QColor(self._accent))
        painter.drawRoundedRect(0, 0, self.width(), r * 2, r, r)
        painter.restore()
        painter.end()

    # ── adaptive font scaling ─────────────────────────────────────────────
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        w = event.size().width()
        if w < 10:
            return
        for lbl, lo, hi, div in [
            (self._value_label,  11, 22, 9),
            (self._title_label,   8, 11, 16),
            (self._unit_label,    7, 10, 18),
        ]:
            if lbl is None:
                continue
            pt = max(lo, min(hi, w // div))
            f = lbl.font()
            if f.pointSize() != pt:
                f.setPointSize(pt)
                lbl.setFont(f)

    def set_value(self, value: str, unit: str = ""):
        if self._value_label:
            self._value_label.setText(value)
        if unit and self._unit_label:
            self._unit_label.setText(unit)


# ─────────────────────────────────────────────────────────────────────────────
# StorageView
# ─────────────────────────────────────────────────────────────────────────────
class StorageView(QWidget, ScaleMixin):
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
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._setup_ui)

    def _setup_ui(self):
        self._disk_cards.clear()

        if hasattr(self, "_update_timer") and self._update_timer is not None:
            self._update_timer.stop()
            self._update_timer.deleteLater()
            self._update_timer = None

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
            "Total kapasitet", "fa5s.hdd", colors.ACCENT_BLUE)
        self._kpi_used = StorageKpiCard(
            "Brukt", "mdi.database", colors.ACCENT_ORANGE)
        self._kpi_free = StorageKpiCard(
            "Ledig", "mdi.check-circle", colors.ACCENT_GREEN)
        self._kpi_read = StorageKpiCard(
            "Lesehastighet", "mdi.arrow-down-bold", colors.ACCENT_GREEN)
        self._kpi_write = StorageKpiCard(
            "Skrivehastighet", "mdi.arrow-up-bold", colors.ACCENT_BLUE)

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

        # Section divider — "FYSISKE DISKER"
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

        section_lbl = QLabel("FYSISKE DISKER")
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

        # ── PROGRAM-AKTIVITET section ──────────────────────────────────────────
        proc_section_row = QHBoxLayout()
        proc_section_row.setSpacing(0)
        proc_section_row.setContentsMargins(0, S.px(6), 0, 0)

        proc_accent = QFrame()
        proc_accent.setFixedSize(S.px(3), S.px(16))
        proc_accent.setStyleSheet(
            f"background-color: {colors.ACCENT_ORANGE};"
            f"border-radius: {S.px(2)}px;"
        )
        proc_section_row.addWidget(proc_accent)
        proc_section_row.addSpacing(S.px(10))

        proc_section_lbl = QLabel("PROGRAM-AKTIVITET")
        proc_section_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        proc_section_lbl.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        proc_section_row.addWidget(proc_section_lbl)
        proc_section_row.addSpacing(S.px(12))

        proc_rule = QFrame()
        proc_rule.setFrameShape(QFrame.Shape.HLine)
        proc_rule.setFixedHeight(1)
        proc_rule.setStyleSheet(f"background-color: {colors.BORDER}; border: none;")
        proc_section_row.addWidget(proc_rule, stretch=1)
        inner_lay.addLayout(proc_section_row)

        self._proc_table = ProcessIoTable()
        inner_lay.addWidget(self._proc_table)

        # ── TOTAL YTELSE section ──────────────────────────────────────────────
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

        perf_section_lbl = QLabel("TOTAL YTELSE")
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
        self._perf_latency.add_series("Skriv", colors.ACCENT_YELLOW, 'scatter')
        self._perf_latency.add_series("Les", colors.ACCENT_ORANGE, 'scatter')
        self._perf_latency.setMinimumHeight(S.px(190))
        self._perf_latency.setMaximumHeight(S.px(220))
        perf_row1.addWidget(self._perf_latency)

        self._perf_iops = PerformanceHistoryGraph("Disk Operations", unit='iops', max_points=90)
        self._perf_iops.add_series("Skriv", colors.TEXT_SECONDARY, 'line')
        self._perf_iops.add_series("Les", colors.ACCENT_GREEN, 'line')
        self._perf_iops.setMinimumHeight(S.px(190))
        self._perf_iops.setMaximumHeight(S.px(220))
        perf_row1.addWidget(self._perf_iops)

        inner_lay.addLayout(perf_row1)

        # Row 2: Bandwidth + Load
        perf_row2 = QHBoxLayout()
        perf_row2.setSpacing(S.px(10))

        self._perf_bandwidth = PerformanceHistoryGraph("Disk Bandwidth", unit='B/s', max_points=90)
        self._perf_bandwidth.add_series("Skriv", colors.ACCENT_BLUE, 'line')
        self._perf_bandwidth.add_series("Les", colors.ACCENT_GREEN, 'line')
        self._perf_bandwidth.setMinimumHeight(S.px(190))
        self._perf_bandwidth.setMaximumHeight(S.px(220))
        perf_row2.addWidget(self._perf_bandwidth)

        self._perf_load = PerformanceHistoryGraph("Disk Load", unit='%', max_points=90)
        self._perf_load.add_series("Belastning", colors.ACCENT_ORANGE, 'line')
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

        # Update process activity table
        top_procs = data.get("top_processes", [])
        if hasattr(self, "_proc_table"):
            self._proc_table.update_processes(top_procs)

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
                Skriv=data.get('total_write_latency_ms', 0),
                Les=data.get('total_read_latency_ms', 0),
            )
        if self._perf_iops is not None:
            self._perf_iops.push(
                Skriv=data.get('total_write_iops', 0),
                Les=data.get('total_read_iops', 0),
            )
        if self._perf_bandwidth is not None:
            self._perf_bandwidth.push(
                Skriv=total_write,
                Les=total_read,
            )
        if self._perf_load is not None:
            self._perf_load.push(
                Belastning=data.get('total_busy_pct', 0),
            )

    @staticmethod
    def _fmt_speed(bps: float):
        if bps >= 1_073_741_824:
            return f"{bps/1_073_741_824:.1f}", "GB/s"
        if bps >= 1_048_576:
            return f"{bps/1_048_576:.0f}", "MB/s"
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
        if self._collector:
            self._collector.stop()
            if self._collector.isRunning():
                self._collector.requestInterruption()
                self._collector.wait(500)
