"""
Overview Page - reference redesign.

Layout (responsive grid, 3 / 2 / 1 columns):
  CPU gauge panel · GPU gauge panel · Memory donut panel
  CPU history · GPU history · Network history
  CPU cores · Storage disks · Network gauges + system status
All values come from the same data feed as before (update_data).
"""
import platform
import time
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.config import settings
from systemmonitor.utils.helpers import format_temperature, network_speed_value
from systemmonitor.widgets.ref_design import (
    Panel, PageHeader, BigGauge, Donut, HBar, IconStat, KV, AreaChart,
    ChartPanel, ReflowGrid, flex, _label, hexcol,
)


def _fmt_size(b: float) -> str:
    b = float(b or 0)
    for unit, div in (("TB", 1024 ** 4), ("GB", 1024 ** 3), ("MB", 1024 ** 2)):
        if b >= div:
            v = b / div
            return f"{v:.2f} {unit}".replace(".", ",") if unit == "TB" else f"{v:.1f} {unit}".replace(".", ",")
    return f"{b:.0f} B"


class _DriveRow(QWidget):
    """One storage row: 'C: (System)' + bar + 'used / total (pct %)'."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, S.px(2), 0, S.px(2))
        lay.setSpacing(S.px(2))
        top = QHBoxLayout()
        self.name_lbl = _label(name, "RefValue", 9, True)
        self.info_lbl = _label("", "RefSub", 8)
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.name_lbl)
        top.addStretch()
        top.addWidget(self.info_lbl)
        lay.addLayout(top)
        self.bar = HBar("ACCENT_GREEN", 6)
        lay.addWidget(self.bar)

    def set_data(self, used: float, total: float, pct: float):
        self.info_lbl.setText(f"{_fmt_size(used)} / {_fmt_size(total)} ({pct:.0f} %)")
        color = "ACCENT_RED" if pct >= 90 else ("ACCENT_YELLOW" if pct >= 80 else "ACCENT_GREEN")
        self.bar.set_value(pct, color)


class OverviewPage(QWidget, ScaleMixin, I18nMixin):
    """Reference-style overview dashboard - responsive grid"""

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0
        self._last_net = None
        self._net_down_speed = 0.0
        self._net_up_speed = 0.0
        self._net_peak = {"down": 1.0, "up": 1.0}
        self._last_data = {}
        self._battery_val_label = None
        self._battery_icon_label = None
        self._battery_row_value = None
        self._battery_block = None
        self._has_battery = self._detect_battery()
        self._core_rows = []
        self._drive_rows = {}
        self._drive_order = []
        # chart history survives UI rebuilds (theme / scale / language)
        self._stores = {k: deque(maxlen=60000) for k in ("cpu", "gpu", "net")}

        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        self._start_timers()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_data_collector(self, collector):
        self._data_collector = collector

    # --- rebuild hooks -------------------------------------------------
    def _on_theme_changed(self, theme_name: str):
        # QSS handles most restyling; rebuild refreshes icons/painted colours
        QTimer.singleShot(0, self._rebuild_and_restore)

    def retranslate_ui(self):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_layout_mode_changed(self, mode):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def _rebuild_and_restore(self):
        self._setup_ui()
        if self._last_data:
            self.update_data(self._last_data)

    # --- UI -------------------------------------------------------------
    def _setup_ui(self):
        old = self.layout()
        if old:
            try:
                while old.count():
                    item = old.takeAt(0)
                    w = item.widget()
                    if w:
                        w.hide()
                        w.deleteLater()
                tmp = QWidget()
                tmp.setLayout(old)
                tmp.deleteLater()
            except Exception:
                pass

        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main = QVBoxLayout()
        main.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        main.setSpacing(S.px(10))
        self.setLayout(main)

        main.addWidget(self._create_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background-color: {colors.BORDER}; border-radius: 3px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        content = QWidget()
        content.setObjectName("RefContent")
        content.setStyleSheet("QWidget#RefContent { background: transparent; }")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, S.px(4), 0)
        content_lay.setSpacing(0)

        self._panels = [
            flex(self._build_cpu_panel(), 340), flex(self._build_gpu_panel(), 340), flex(self._build_mem_panel(), 340),
            self._build_chart_panel("cpu"), self._build_chart_panel("gpu"), self._build_chart_panel("net"),
            self._build_cores_panel(), self._build_storage_panel(), self._build_net_column(),
        ]
        self._grid = ReflowGrid([(p, 1) for p in self._panels], max_cols=3, min_col_width=380)
        content_lay.addWidget(self._grid)
        content_lay.addStretch(1)
        scroll.setWidget(content)
        self._grid.bind_viewport(scroll)
        main.addWidget(scroll, stretch=1)

    # --- header ---------------------------------------------------------
    def _chip(self, value_attr: str | None, text: str, caption: str):
        box = QFrame()
        box.setObjectName("RefPanel")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(S.px(10), S.px(3), S.px(10), S.px(3))
        lay.setSpacing(0)
        v = _label(text, "RefValue", 10, True)
        c = _label(caption, "RefMuted", 7)
        lay.addWidget(v)
        lay.addWidget(c)
        if value_attr:
            setattr(self, value_attr, v)
        return box, v

    def _create_header(self):
        colors = theme_manager.colors
        self._hdr = PageHeader(tr("Dashboard"), tr("System performance overview"), "mdi.view-dashboard", pill=tr("Healthy"))
        box, _ = self._chip("_uptime_val", "0m", tr("Uptime"))
        self._hdr.extra.addWidget(box)
        box, _ = self._chip(None, self._short_os(), tr("OS"))
        self._hdr.extra.addWidget(box)

        self._battery_val_label = None
        self._battery_icon_label = None
        self._battery_block = None
        if self._has_battery:
            bb = QFrame()
            bb.setObjectName("RefPanel")
            bl = QHBoxLayout(bb)
            bl.setContentsMargins(S.px(10), S.px(3), S.px(10), S.px(3))
            bl.setSpacing(S.px(6))
            icon = QLabel()
            icon.setStyleSheet("background: transparent; border: none;")
            icon.setPixmap(qta.icon('ph.battery-charging', color=colors.STATUS_GREEN).pixmap(S.px(16), S.px(16)))
            bl.addWidget(icon)
            tc = QVBoxLayout()
            tc.setSpacing(0)
            val = _label("--%", "RefValue", 10, True)
            tc.addWidget(val)
            tc.addWidget(_label(tr("Battery"), "RefMuted", 7))
            bl.addLayout(tc)
            self._hdr.extra.addWidget(bb)
            self._battery_block = bb
            self._battery_icon_label = icon
            self._battery_val_label = val
        return self._hdr

    # --- panels ---------------------------------------------------------
    def _build_cpu_panel(self):
        p = Panel("CPU", "ph.cpu")
        row = QHBoxLayout()
        row.setSpacing(S.px(10))
        self._cpu_gauge = BigGauge("ACCENT_GREEN", "CPU")
        row.addWidget(self._cpu_gauge, stretch=3)
        side = QVBoxLayout()
        side.setSpacing(S.px(6))
        self._cpu_name = _label("", "RefValue", 8, True)
        self._cpu_name.setWordWrap(True)
        side.addWidget(self._cpu_name)
        self._cpu_freq = IconStat("ph.pulse", "--", tr("Current frequency"))
        self._cpu_cores = IconStat("ph.cpu", "--", tr("Cores / threads"))
        self._cpu_temp = IconStat("ph.thermometer", "--", tr("Temperature"))
        for w in (self._cpu_freq, self._cpu_cores, self._cpu_temp):
            side.addWidget(w)
        side.addStretch()
        row.addLayout(side, stretch=2)
        p.body.addLayout(row)
        return p

    def _build_gpu_panel(self):
        p = Panel("GPU", "ph.monitor")
        row = QHBoxLayout()
        row.setSpacing(S.px(10))
        self._gpu_gauge = BigGauge("ACCENT_CYAN", "GPU")
        row.addWidget(self._gpu_gauge, stretch=3)
        side = QVBoxLayout()
        side.setSpacing(S.px(6))
        self._gpu_name = _label("", "RefValue", 8, True)
        self._gpu_name.setWordWrap(True)
        side.addWidget(self._gpu_name)
        self._gpu_temp = IconStat("ph.thermometer", "--", tr("Temperature"))
        self._gpu_vram = IconStat("ph.memory", "--", tr("VRAM"))
        self._gpu_clock = IconStat("ph.pulse", "--", tr("Core clock"))
        for w in (self._gpu_temp, self._gpu_vram, self._gpu_clock):
            side.addWidget(w)
        side.addStretch()
        row.addLayout(side, stretch=2)
        p.body.addLayout(row)
        return p

    def _build_mem_panel(self):
        p = Panel(tr("Memory"), "ph.memory")
        row = QHBoxLayout()
        row.setSpacing(S.px(10))
        self._mem_donut = Donut()
        row.addWidget(self._mem_donut, stretch=3)
        side = QVBoxLayout()
        side.setSpacing(S.px(8))
        side.addStretch()
        self._mem_used_kv = KV(tr("In use"), "--")
        self._mem_avail_kv = KV(tr("Available"), "--")
        self._mem_swap_kv = KV(tr("Swap"), "--")
        for w in (self._mem_used_kv, self._mem_avail_kv, self._mem_swap_kv):
            side.addWidget(w)
        side.addStretch()
        row.addLayout(side, stretch=2)
        p.body.addLayout(row)
        return p

    def _build_chart_panel(self, which: str):
        if which == "cpu":
            ch = AreaChart(["ACCENT_GREEN"], 100.0, store=self._stores["cpu"])
            self._cpu_chart = ch
            panel = ChartPanel(tr("CPU load history"), "ph.chart-line", ch, tabs=True)
        elif which == "gpu":
            ch = AreaChart(["ACCENT_CYAN"], 100.0, store=self._stores["gpu"])
            self._gpu_chart = ch
            panel = ChartPanel(tr("GPU load history"), "ph.chart-line", ch, tabs=True)
        else:
            _, unit = network_speed_value(0)
            ch = AreaChart(["ACCENT_GREEN", "ACCENT_CYAN"], None,
                           y_fmt=lambda v: (f"{v:.1f}" if v < 10 else f"{v:.0f}") + f" {network_speed_value(0)[1]}",
                           store=self._stores["net"], min_auto=1.0)
            self._net_chart = ch
            panel = ChartPanel(tr('Network Traffic'), "ph.chart-line", ch, tabs=True,
                               legend=[("ACCENT_GREEN", tr("Download")), ("ACCENT_CYAN", tr("Upload"))])
        panel.setMinimumHeight(S.px(190))
        panel.setProperty("flex_max", 400)
        return panel

    def _build_cores_panel(self):
        p = Panel(tr("CPU cores"), "ph.cpu")
        self._cores_grid = QGridLayout()
        self._cores_grid.setHorizontalSpacing(S.px(14))
        self._cores_grid.setVerticalSpacing(S.px(5))
        p.body.addLayout(self._cores_grid)
        p.body.addStretch()
        self._core_rows = []
        return p

    def _build_storage_panel(self):
        p = Panel(tr("Storage Disks"), "ph.database")
        self._drives_lay = QVBoxLayout()
        self._drives_lay.setSpacing(S.px(8))
        p.body.addLayout(self._drives_lay)
        p.body.addStretch()
        self._io_kv_r = KV(tr("Read"), "--")
        self._io_kv_w = KV(tr("Write"), "--")
        p.body.addWidget(self._io_kv_r)
        p.body.addWidget(self._io_kv_w)
        self._drive_rows = {}
        self._drive_order = []
        return p

    def _build_net_column(self):
        wrap = QWidget()
        wrap.setObjectName("RefContent")
        wrap.setStyleSheet("QWidget#RefContent { background: transparent; }")
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(S.px(10))

        net = Panel(tr("Network"), "ph.wifi-high")
        row = QHBoxLayout()
        self._net_down_gauge = BigGauge("ACCENT_GREEN", "", show_ends=False, value_pt=13)
        self._net_up_gauge = BigGauge("ACCENT_CYAN", "", show_ends=False, value_pt=13)
        for title, g in ((tr("Download"), self._net_down_gauge), (tr("Upload"), self._net_up_gauge)):
            g.setMinimumSize(S.px(120), S.px(110))
            cell = QVBoxLayout()
            cell.setSpacing(0)
            t = _label(title, "RefSub", 9)
            t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            cell.addWidget(t)
            cell.addWidget(g, stretch=1)
            row.addLayout(cell)
        net.body.addLayout(row)
        lay.addWidget(net, stretch=3)

        st = Panel(tr("System Status"), "ph.heartbeat")
        self._status_rows = {}
        for key, label in (("cpu", "CPU"), ("gpu", "GPU"), ("mem", tr("Memory")),
                           ("disk", tr("Storage")), ("net", tr("Network"))):
            kv = KV(label, "--")
            self._status_rows[key] = kv
            st.body.addWidget(kv)
        lay.addWidget(st, stretch=2)
        return wrap

    # --- helpers --------------------------------------------------------
    def _start_timers(self):
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)
        self._uptime_timer.start(1000)

    def _update_uptime(self):
        self._uptime_seconds = int(time.time() - self._start_time)
        if hasattr(self, '_uptime_val') and self._uptime_val is not None:
            try:
                self._uptime_val.setText(self._format_uptime(self._uptime_seconds))
            except RuntimeError:
                pass

    def _format_uptime(self, seconds):
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def _detect_battery(self) -> bool:
        try:
            from systemmonitor.data.hardware.battery_manager import BatteryManager
            return BatteryManager().has_battery()
        except Exception:
            return False

    def _format_battery_display(self, battery: dict) -> tuple[str, str]:
        """Returns (display_text, accent_color) for a battery info dict."""
        colors = theme_manager.colors
        percent = battery.get('percent', 0)
        status = battery.get('status_text', 'Unknown')
        secs_left = battery.get('secs_left')

        text = f"{percent:.0f}% • {status}"
        if status == "On battery":
            from systemmonitor.data.hardware.battery_manager import BatteryManager
            remaining = BatteryManager.format_time_remaining(secs_left)
            if remaining != "—":
                text += f" • {remaining}"

        if status == "On battery" and percent <= 20:
            color = colors.ACCENT_RED
        elif status == "On battery" and percent <= 40:
            color = colors.ACCENT_ORANGE
        elif battery.get('power_plugged'):
            color = colors.STATUS_GREEN
        else:
            color = colors.TEXT_PRIMARY
        return text, color

    def _short_os(self):
        p = platform.platform()
        if "Windows" in p:
            return "Windows " + platform.win32_ver()[0]
        return p

    @staticmethod
    def _state(pct: float, warn: float = 75, crit: float = 90) -> tuple[str, str]:
        """(text, colour key) for a usage percentage."""
        if pct >= crit:
            return tr("Critical"), "ACCENT_RED"
        if pct >= warn:
            return tr("Warning"), "ACCENT_ORANGE"
        return tr("Normal"), "STATUS_GREEN"

    def _set_status(self, key: str, pct: float | None, text: str | None = None):
        kv = self._status_rows.get(key)
        if kv is None:
            return
        if text is None:
            if pct is None:
                kv.set_value("--")
                return
            text, ckey = self._state(pct)
        else:
            ckey = "STATUS_GREEN"
        kv.val_lbl.setStyleSheet(f"color: {hexcol(ckey)};")
        kv.set_value(text)

    # --- data -----------------------------------------------------------
    def update_data(self, data):
        """Called by MainWindow whenever new data arrives"""
        self._last_data = data
        worst = 0.0

        cpu = data.get('cpu')
        if cpu:
            pct = cpu.get('percent', 0) or 0
            worst = max(worst, pct)
            self._cpu_gauge.set_percent(pct)
            self._cpu_chart.push(pct)
            freq = cpu.get('frequency_current')
            self._cpu_freq.set_value(f"{freq / 1000:.2f} GHz".replace(".", ",") if freq else "--")
            phys, logi = cpu.get('core_count'), cpu.get('thread_count')
            if phys and logi:
                self._cpu_cores.set_value(f"{phys} / {logi}")
            temp = cpu.get('temperature')
            self._cpu_temp.set_value(format_temperature(temp) if temp else "--")
            sysinfo = data.get('system_info') or {}
            name = sysinfo.get('cpu_name')
            if name:
                self._cpu_name.setText(name)
            elif not self._cpu_name.text():
                self._cpu_name.setText(platform.processor() or "")
            self._update_cores(cpu.get('per_core') or [])
            self._set_status("cpu", pct)

        gpu = data.get('gpu')
        if gpu:
            if gpu.get('available'):
                from systemmonitor.views.gpu import GPUView
                g0 = (GPUView._merge_duplicate_gpus(gpu.get('gpus') or []) or [{}])[0]
                load = g0.get('gpu_utilization_percent')
                if load is None:
                    load = gpu.get('load')
                load = load or 0
                worst = max(worst, load)
                self._gpu_gauge.set_percent(load)
                self._gpu_chart.push(load)
                if g0.get('name'):
                    self._gpu_name.setText(str(g0['name']))
                temp = gpu.get('temperature')
                if temp is None:
                    temp = g0.get('temperature_celsius')
                self._gpu_temp.set_value(format_temperature(temp) if temp else "--")
                vt, vu = g0.get('vram_total_mb'), g0.get('vram_used_mb')
                if vt:
                    vp = (vu or 0) / vt * 100
                    self._gpu_vram.set_value(f"{(vu or 0) / 1024:.1f} / {vt / 1024:.1f} GB".replace(".", ","),
                                             f"{tr('VRAM')} ({vp:.0f} %)")
                else:
                    self._gpu_vram.set_value("N/A", tr("VRAM"))
                clk = g0.get('core_clock_mhz')
                self._gpu_clock.set_value(f"{clk:,.0f} MHz".replace(",", " ") if clk else "N/A")
                self._set_status("gpu", load)
            else:
                self._gpu_gauge.set_percent(0, text="N/A")
                self._set_status("gpu", None, tr("Not detected"))

        mem = data.get('memory')
        if mem:
            pct = mem.get('percent', 0) or 0
            worst = max(worst, pct)
            total = mem.get('total', 0) or 0
            used = mem.get('used', 0) or 0
            avail = mem.get('available', 0) or 0
            gb = 1024 ** 3
            self._mem_donut.set_data([(pct, "ACCENT_GREEN")],
                                     f"{used / gb:.1f} GB".replace(".", ","),
                                     f"/ {total / gb:.1f} GB".replace(".", ","))
            self._mem_used_kv.set_value(f"{used / gb:.1f} GB ({pct:.0f} %)".replace(".", ","))
            self._mem_avail_kv.set_value(f"{avail / gb:.1f} GB ({100 - pct:.0f} %)".replace(".", ","))
            su, st = mem.get('swap_used'), mem.get('swap_total')
            self._mem_swap_kv.set_value(f"{(su or 0) / gb:.1f} / {(st or 0) / gb:.1f} GB".replace(".", ","))
            self._set_status("mem", pct)

        net = data.get('network')
        if net:
            bytes_sent = net.get('bytes_sent', 0)
            bytes_recv = net.get('bytes_recv', 0)
            down_bps = net.get('download_speed')
            up_bps = net.get('upload_speed')
            if down_bps is None or up_bps is None:
                if self._last_net:
                    down_bps = max(0.0, (bytes_recv - self._last_net[0]) / 1.0)
                    up_bps = max(0.0, (bytes_sent - self._last_net[1]) / 1.0)
            self._last_net = (bytes_recv, bytes_sent)
            if down_bps is not None and up_bps is not None:
                dn, unit = network_speed_value(down_bps)
                up, _ = network_speed_value(up_bps)
                precision = settings.get('decimal_places', 1)
                self._net_down_speed, self._net_up_speed = dn, up
                self._net_chart.push(dn, up)
                self._net_peak["down"] = max(dn, self._net_peak["down"] * 0.995, 1.0)
                self._net_peak["up"] = max(up, self._net_peak["up"] * 0.995, 1.0)
                self._net_down_gauge.set_percent(dn / self._net_peak["down"] * 100,
                                                 text=f"{dn:.{precision}f}", caption=unit)
                self._net_up_gauge.set_percent(up / self._net_peak["up"] * 100,
                                               text=f"{up:.{precision}f}", caption=unit)
                self._set_status("net", None, tr("Connected"))

        disk = data.get('disk')
        if disk:
            parts = disk.get('partitions', [])
            if parts:
                self._update_drives(parts)
                self._set_status("disk", max((p.get('percent', 0) or 0) for p in parts))
            rd = disk.get('read_rate', disk.get('read_speed', 0)) or 0
            wr = disk.get('write_rate', disk.get('write_speed', 0)) or 0
            self._io_kv_r.set_value(f"{_fmt_size(rd)}/s")
            self._io_kv_w.set_value(f"{_fmt_size(wr)}/s")

        if worst >= 90:
            self._hdr.pill.set_state("bad", tr("Critical"))
        elif worst >= 75:
            self._hdr.pill.set_state("warn", tr("Warning"))
        else:
            self._hdr.pill.set_state("ok", tr("Healthy"))

        if self._has_battery and 'system_info' in data:
            battery = data['system_info'].get('battery')
            if battery:
                self._update_battery_display(battery)

    def _update_cores(self, per_core):
        if len(per_core) != len(self._core_rows):
            while self._cores_grid.count():
                it = self._cores_grid.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            self._core_rows = []
            two_cols = len(per_core) > 8
            rows_per_col = (len(per_core) + 1) // 2 if two_cols else len(per_core)
            for i in range(len(per_core)):
                cell = QWidget()
                cl = QHBoxLayout(cell)
                cl.setContentsMargins(0, 0, 0, 0)
                cl.setSpacing(S.px(6))
                name = _label(f"{tr('Core')} {i + 1}", "RefSub", 8)
                name.setMinimumWidth(S.px(52))
                bar = HBar("ACCENT_GREEN", 6)
                val = _label("0 %", "RefValue", 8, True)
                val.setMinimumWidth(S.px(34))
                val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                cl.addWidget(name)
                cl.addWidget(bar, stretch=1)
                cl.addWidget(val)
                self._cores_grid.addWidget(cell, i % rows_per_col, i // rows_per_col)
                self._core_rows.append((bar, val))
        for (bar, val), pct in zip(self._core_rows, per_core):
            bar.set_value(pct)
            val.setText(f"{pct:.0f} %")

    def _update_drives(self, partitions):
        keys = [p.get('device', '') for p in partitions]
        if keys != self._drive_order:
            while self._drives_lay.count():
                it = self._drives_lay.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            self._drive_rows = {}
            for p in partitions:
                dev = p.get('device', '')
                row = _DriveRow(dev.rstrip("\\"))
                self._drives_lay.addWidget(row)
                self._drive_rows[dev] = row
            self._drive_order = keys
        for p in partitions:
            row = self._drive_rows.get(p.get('device', ''))
            if row:
                row.set_data(p.get('used', 0), p.get('total', 0), p.get('percent', 0) or 0)

    def _update_battery_display(self, battery: dict):
        text, color = self._format_battery_display(battery)
        percent = battery.get('percent', 0)
        plugged = battery.get('power_plugged')
        if self._battery_val_label is not None:
            self._battery_val_label.setText(f"{percent:.0f}%")
            self._battery_val_label.setStyleSheet(f"color: {color};")
        if self._battery_icon_label is not None:
            if plugged:
                icon_name = 'ph.battery-charging'
            elif percent <= 15:
                icon_name = 'ph.battery-warning'
            elif percent <= 40:
                icon_name = 'ph.battery-low'
            elif percent <= 75:
                icon_name = 'ph.battery-medium'
            else:
                icon_name = 'ph.battery-full'
            self._battery_icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(S.px(16), S.px(16)))
