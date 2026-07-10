"""
Network View - Professional Network Monitoring Dashboard
Real-time network data with clean, readable design
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QHeaderView, QComboBox, QProgressBar, QPushButton, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import socket
import time
from typing import Dict, List, Optional
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, language_manager, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.core.signals import signal_bus
from systemmonitor.widgets.card import Card
from systemmonitor.config import settings
from systemmonitor.utils.helpers import network_speed_value
from systemmonitor.widgets.network_widgets import (
    KpiCard, TrafficGraph, _Donut, ConnectionsTable, _IfaceRow, _Radar
)


# ---------------------------------------------------------------------------
# Network View
# ---------------------------------------------------------------------------

class NetworkView(QWidget, ScaleMixin, I18nMixin):
    """Professional Network Monitoring Dashboard"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self.i18n_connect()
        self._last_sent = 0
        self._last_recv = 0
        self._last_ts = time.time()
        self._connections: List[Dict] = []

        self._build_ui()
        self._connect()
        self._start()

        from systemmonitor.core.signals import signal_bus
        signal_bus.setting_changed.connect(self._on_setting_changed)

    def _on_setting_changed(self, key: str, value):
        if key in ('history_duration', 'update_interval'):
            self._apply_history_length()

    def _apply_history_length(self):
        """Resize the traffic graph buffer based on the History Length setting"""
        from systemmonitor.config import settings, AppConfig
        points, stride = AppConfig.history_window(
            settings.get('history_duration', 300),
            settings.get('update_interval', 500))
        if hasattr(self, '_traffic_graph') and self._traffic_graph is not None:
            self._traffic_graph.set_max_points(points)
            self._traffic_graph.set_sample_stride(stride)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_layout_mode_changed(self, mode):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def retranslate_ui(self):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def _rebuild_and_restore(self):
        self._build_ui()

    def _build_ui(self):
        # Clear previous layout if this is a rebuild
        if self.layout() is not None:
            old_layout = self.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            
            dummy = QWidget()
            dummy.setLayout(old_layout)
            dummy.deleteLater()

        c = theme_manager.colors
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # scroll wrapper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        main = QVBoxLayout(container)
        main.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        main.setSpacing(S.px(12))

        self._build_topbar(main)
        self._build_kpi_row(main)
        self._build_traffic_card(main)
        self._build_middle_row(main)
        self._build_radar_row(main)

        self._apply_history_length()

    def _build_topbar(self, parent):
        c = theme_manager.colors

        bar = QFrame()
        bar.setFixedHeight(S.px(52))
        bar.setFrameShape(QFrame.Shape.NoFrame)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        row = QHBoxLayout(bar)
        row.setContentsMargins(S.px(16), 0, S.px(16), 0)
        row.setSpacing(S.px(12))

        # live badge
        dot = QFrame()
        dot.setFrameShape(QFrame.Shape.NoFrame)
        dot.setFixedSize(S.px(8), S.px(8))
        dot.setStyleSheet(f"background-color: {c.ACCENT_GREEN}; border: none; border-radius: {S.px(4)}px;")
        row.addWidget(dot)

        live = QLabel(tr("LIVE"))
        live.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        live.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        row.addWidget(live)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.NoFrame)
        sep.setFixedSize(1, S.px(24))
        sep.setStyleSheet(f"background: {c.BORDER}; border: none;")
        row.addWidget(sep)

        # host info
        try:
            hostname = socket.gethostname()
            ipv4 = socket.gethostbyname(hostname)
        except Exception:
            hostname, ipv4 = "—", "—"

        host_lbl = QLabel(f"{hostname}  ·  {ipv4}")
        host_lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
        host_lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        row.addWidget(host_lbl)

        row.addStretch()

        # refresh selector
        refresh_lbl = QLabel(tr("Refresh:"))
        refresh_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
        refresh_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        row.addWidget(refresh_lbl)

        self._refresh_cb = QComboBox()
        self._refresh_cb.addItems(["2s", "5s", "10s", "30s"])
        self._refresh_cb.setCurrentText("5s")
        self._refresh_cb.setFixedWidth(S.px(70))
        row.addWidget(self._refresh_cb)

        parent.addWidget(bar)

    def _build_kpi_row(self, parent):
        c = theme_manager.colors
        row = QHBoxLayout()
        row.setSpacing(S.px(12))

        _, _initial_speed_unit = network_speed_value(0)
        self._kpi_down  = KpiCard("Download",    "mdi.arrow-down-bold",   c.ACCENT_CYAN,   _initial_speed_unit)
        self._kpi_up    = KpiCard("Upload",       "mdi.arrow-up-bold",     c.ACCENT_PURPLE, _initial_speed_unit)
        self._kpi_conns = KpiCard("Connections",  "mdi.link-variant",      c.ACCENT_BLUE,   "")
        self._kpi_iface = KpiCard("Interfaces Up","mdi.lan-connect",       c.ACCENT_GREEN,  "")

        for card in [self._kpi_down, self._kpi_up, self._kpi_conns, self._kpi_iface]:
            row.addWidget(card, stretch=1)

        parent.addLayout(row)

    def _build_traffic_card(self, parent):
        card = Card(title=tr("Network Traffic"), icon="ph.chart-line")
        self._traffic_graph = TrafficGraph()
        self._traffic_graph.setMinimumHeight(S.px(170))
        card.add_widget(self._traffic_graph)
        parent.addWidget(card)

    def _build_middle_row(self, parent):
        row = QHBoxLayout()
        row.setSpacing(S.px(12))

        # LEFT: connections table
        conn_card = Card(title=tr("Active Connections"), icon="ph.link")
        conn_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._conn_table = ConnectionsTable()
        self._conn_table.setMinimumHeight(S.px(220))
        conn_card.add_widget(self._conn_table)
        row.addWidget(conn_card, stretch=3)

        # RIGHT: protocol + interfaces
        right_col = QVBoxLayout()
        right_col.setSpacing(S.px(12))

        # Protocol distribution
        proto_card = Card(title=tr("Protocol Distribution"), icon="ph.chart-pie")
        proto_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        proto_content = QHBoxLayout()
        proto_content.setSpacing(S.px(16))
        proto_content.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._donut = _Donut()
        proto_content.addWidget(self._donut)

        self._proto_legend = QVBoxLayout()
        self._proto_legend.setSpacing(S.px(6))
        legend_wrap = QWidget()
        legend_wrap.setStyleSheet("background: transparent;")
        legend_wrap.setLayout(self._proto_legend)
        proto_content.addWidget(legend_wrap)
        proto_content.addStretch()

        proto_wrap = QWidget()
        proto_wrap.setStyleSheet("background: transparent;")
        proto_wrap.setLayout(proto_content)
        proto_card.add_widget(proto_wrap)
        right_col.addWidget(proto_card)

        # Interface status
        iface_card = Card(title=tr("Network Interfaces"), icon="ph.globe")
        iface_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._iface_list = QVBoxLayout()
        self._iface_list.setSpacing(S.px(6))
        iface_wrap = QWidget()
        iface_wrap.setStyleSheet("background: transparent;")
        iface_wrap.setLayout(self._iface_list)
        iface_card.add_widget(iface_wrap)
        right_col.addWidget(iface_card)

        right_col.addStretch()
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_widget.setLayout(right_col)
        row.addWidget(right_widget, stretch=2)

        parent.addLayout(row)

    def _build_radar_row(self, parent):
        c = theme_manager.colors

        row = QHBoxLayout()
        row.setSpacing(S.px(12))

        # Radar / topology
        radar_card = Card(title=tr("Network Topology"), icon="ph.broadcast")
        radar_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._radar = _Radar()
        self._radar.setMinimumHeight(S.px(200))
        radar_card.add_widget(self._radar)
        row.addWidget(radar_card, stretch=2)

        # System status panel
        status_card = Card(title=tr("System Status"), icon="mdi.shield-check")
        status_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        status_card.setMinimumWidth(S.px(200))

        status_lay = QVBoxLayout()
        status_lay.setSpacing(S.px(14))
        status_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        def _stat_row(title: str, default: str, accent: str):
            w = QWidget(); w.setStyleSheet("background: transparent; border: none;")
            l = QVBoxLayout(w); l.setSpacing(S.px(2)); l.setContentsMargins(0, 0, 0, 0)
            t = QLabel(tr(title))
            t.setFont(QFont("Segoe UI", S.font_pt(9)))
            t.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent; border: none;")
            l.addWidget(t)
            v = QLabel(tr(default) if default not in ("—",) else default)
            v.setFont(QFont("Segoe UI", S.font_pt(13), QFont.Weight.Bold))
            v.setStyleSheet(f"color: {accent}; background: transparent; border: none;")
            l.addWidget(v)
            return w, v

        health_row, self._health_lbl = _stat_row("Health", "Good", c.ACCENT_GREEN)
        uptime_row,  self._uptime_lbl = _stat_row("Uptime",  "—",   c.TEXT_PRIMARY)
        sent_row,    self._sent_lbl   = _stat_row("Total Sent", "—", c.ACCENT_PURPLE)
        recv_row,    self._recv_lbl   = _stat_row("Total Recv", "—", c.ACCENT_CYAN)

        for w in [health_row, uptime_row, sent_row, recv_row]:
            status_lay.addWidget(w)
        status_lay.addStretch()

        status_wrap = QWidget(); status_wrap.setStyleSheet("background: transparent; border: none;")
        status_wrap.setLayout(status_lay)
        status_card.add_widget(status_wrap)
        row.addWidget(status_card, stretch=1)

        parent.addLayout(row)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect(self):
        signal_bus.data_updated.connect(self._on_data)
        theme_manager.theme_changed.connect(self._retheme)
        self._refresh_cb.currentTextChanged.connect(self._on_refresh_changed)

    def _on_refresh_changed(self, text: str):
        secs = int(text.replace("s", ""))
        self._conn_timer.setInterval(secs * 1000)

    # ------------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------------

    def _start(self):
        # boot time check
        try:
            import psutil
            self._boot_time = psutil.boot_time()
        except:
            self._boot_time = time.time()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(10000)
        QTimer.singleShot(800, self._refresh_status)

    # ------------------------------------------------------------------
    # Data handlers
    # ------------------------------------------------------------------

    def _on_data(self, data: dict):
        net = data.get("network")
        if not net:
            return

        # Use pre-calculated smoothed speeds from collector if available
        # Units: Bytes/s
        dn_bps_raw = net.get("download_speed", 0)
        up_bps_raw = net.get("upload_speed", 0)

        # Convert to the user's preferred network speed unit (Mbps or MB/s)
        dn_speed, speed_unit = network_speed_value(dn_bps_raw)
        up_speed, _ = network_speed_value(up_bps_raw)
        precision = settings.get('decimal_places', 1)

        sent = net.get("bytes_sent", 0)
        recv = net.get("bytes_recv", 0)

        self._last_sent = sent
        self._last_recv = recv
        self._last_ts   = time.time()

        # KPI
        self._kpi_down.set_unit(speed_unit)
        self._kpi_up.set_unit(speed_unit)
        self._kpi_down.set_value(f"{dn_speed:.{precision}f}", f"↓ {self._fmt_bytes(recv)}")
        self._kpi_up.set_value(  f"{up_speed:.{precision}f}", f"↑ {self._fmt_bytes(sent)}")

        # Graph
        self._traffic_graph.push(up_speed, dn_speed)

        # Sent / Recv labels in status panel
        self._sent_lbl.setText(self._fmt_bytes(sent))
        self._recv_lbl.setText(self._fmt_bytes(recv))

        # Connections update (from collector)
        conns = net.get("connections")
        if conns is not None:
            self._refresh_connections(conns)

        # Interfaces update (from collector)
        ifaces = net.get("interfaces")
        if ifaces is not None:
            self._refresh_interfaces(ifaces)

    def _refresh_connections(self, rows: List[Dict]):
        self._connections = rows
        self._conn_table.load(rows)
        self._kpi_conns.set_value(str(len(rows)), tr("TCP + UDP"))

        # protocol distribution
        tcp = sum(1 for r in rows if r["proto"] == "TCP")
        udp = sum(1 for r in rows if r["proto"] == "UDP")
        other = max(len(rows) - tcp - udp, 0)
        self._donut.set_data({"TCP": tcp, "UDP": udp, "Other": other})
        self._refresh_legend(tcp, udp, other)

    def _refresh_legend(self, tcp: int, udp: int, other: int):
        c = theme_manager.colors
        while self._proto_legend.count():
            item = self._proto_legend.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for label, count, color in [
            ("TCP",   tcp,   c.ACCENT_GREEN),
            ("UDP",   udp,   c.ACCENT_BLUE),
            (tr("Other"), other, c.ACCENT_ORANGE),
        ]:
            row = QHBoxLayout()
            row.setSpacing(S.px(8))

            dot = QFrame()
            dot.setFrameShape(QFrame.Shape.NoFrame)
            dot.setFixedSize(S.px(10), S.px(10))
            dot.setStyleSheet(f"background-color: {color}; border: none; border-radius: {S.px(5)}px;")
            row.addWidget(dot)

            lbl = QLabel(f"{label}: {count}")
            lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
            lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()

            wrap = QWidget(); wrap.setStyleSheet("background: transparent;")
            wrap.setLayout(row)
            self._proto_legend.addWidget(wrap)

    def _refresh_interfaces(self, ifaces: Dict):
        c = theme_manager.colors

        while self._iface_list.count():
            item = self._iface_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        up_count = 0
        # Show first 8 interfaces
        for name, info in list(ifaces.items())[:8]:
            row = _IfaceRow(name, info['isup'], info['speed'], info['ip'])
            self._iface_list.addWidget(row)
            if info['isup']:
                up_count += 1

        self._kpi_iface.set_value(str(up_count), tr("of {0} interfaces").format(len(ifaces)))

    def _refresh_status(self):
        # uptime
        up_secs = int(time.time() - self._boot_time)
        d, rem = divmod(up_secs, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        self._uptime_lbl.setText(f"{d}d {h:02d}h {m:02d}m")

    def _retheme(self, _name: str = ""):
        c = theme_manager.colors
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self._conn_table.retheme()
        self.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_bytes(n: float) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    # public API
    def update_data(self, data: dict):
        self._on_data(data)

