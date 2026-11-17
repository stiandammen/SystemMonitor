"""
Network View - rebuilt dashboard.

Gauges scaled against the real link speed, traffic history with range tabs,
per-adapter cards (physical adapters only, virtual ones listed separately),
connection analytics (protocols, states, top ports, top remote hosts), a
topology diagram built from the machine's real adapters and a searchable
connection table. Same data feed as before (data['network']).
"""
import socket
import time
from collections import Counter, deque
from typing import Dict, List

import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QComboBox,
    QLineEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.core.signals import signal_bus
from systemmonitor.config import settings
from systemmonitor.utils.helpers import network_speed_value
from systemmonitor.widgets.network_widgets import ConnectionsTable
from systemmonitor.widgets.network_panels import (
    AdapterCard, VirtualAdapterList, RankPanel, TopologyView,
    is_virtual, is_vpn, is_wifi, link_text, fmt_bytes, PORT_NAMES,
)
from systemmonitor.widgets.ref_design import (
    Panel, PageHeader, GaugeKpi, KpiTile, KV, Donut, DotRow, AreaChart,
    ChartPanel, ReflowGrid, hexcol,
)

_PRIVATE_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.30.", "172.31.",
                     "169.254.", "127.", "fe80", "fc", "fd")


def _is_remote(ip: str) -> bool:
    return bool(ip) and ip not in ("—", "-", "0.0.0.0", "::", "::1") and not ip.startswith("127.")


class NetworkView(QWidget, ScaleMixin, I18nMixin):
    """Network monitoring dashboard"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self.i18n_connect()
        self._ifaces: Dict[str, dict] = {}
        self._conns: List[Dict] = []
        self._conn_interval = 5
        self._last_conn_ui = 0.0
        self._nic_prev: Dict[str, tuple] = {}
        self._nic_rate: Dict[str, tuple] = {}
        self._nic_total: Dict[str, tuple] = {}
        self._cards: Dict[str, AdapterCard] = {}
        self._card_order: List[str] = []
        self._peak_dn = 0.0
        self._peak_up = 0.0
        self._last_data = None
        self._traffic_store = deque(maxlen=60000)  # survives UI rebuilds

        try:
            import psutil as _ps
            self._boot_time = _ps.boot_time()
        except Exception:
            self._boot_time = time.time()

        self._build_ui()
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(10000)
        QTimer.singleShot(800, self._refresh_status)

    # ------------------------------------------------------------------
    # rebuild hooks
    # ------------------------------------------------------------------
    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_layout_mode_changed(self, mode):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def retranslate_ui(self):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def _rebuild_and_restore(self):
        self._cards = {}
        self._card_order = []
        self._build_ui()
        if self._last_data:
            self._on_data(self._last_data)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        if self.layout() is not None:
            old = self.layout()
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        outer.setSpacing(S.px(10))

        # ---- header -------------------------------------------------
        self._hdr = PageHeader(tr("Network"), tr("Network traffic, connections and protocol distribution"),
                               "ph.wifi-high", pill=tr("LIVE"))
        try:
            hostname = socket.gethostname()
            ipv4 = socket.gethostbyname(hostname)
        except Exception:
            hostname, ipv4 = "-", "-"
        self._hostname = hostname
        host_lbl = QLabel(f"{hostname}  ·  {ipv4}")
        host_lbl.setObjectName("RefSub")
        host_lbl.setFont(QFont("Cutive", S.font_pt(9)))
        self._hdr.extra.addWidget(host_lbl)
        refresh_lbl = QLabel(tr("Refresh:"))
        refresh_lbl.setObjectName("RefMuted")
        refresh_lbl.setFont(QFont("Cutive", S.font_pt(9)))
        self._hdr.extra.addWidget(refresh_lbl)
        self._refresh_cb = QComboBox()
        self._refresh_cb.addItems(["2s", "5s", "10s", "30s"])
        self._refresh_cb.setCurrentText(f"{self._conn_interval}s")
        self._refresh_cb.setFixedWidth(S.px(76))
        self._refresh_cb.currentTextChanged.connect(self._on_refresh_changed)
        self._hdr.extra.addWidget(self._refresh_cb)
        outer.addWidget(self._hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")
        outer.addWidget(scroll, stretch=1)

        # ---- KPI row: live gauges + protocol + connection states ------
        _, unit = network_speed_value(0)
        self._kpi_down = GaugeKpi(tr("Download"), "ph.arrow-down", "ACCENT_GREEN", unit)
        self._kpi_up = GaugeKpi(tr("Upload"), "ph.arrow-up", "ACCENT_CYAN", unit)

        proto = Panel(tr("Protocol Distribution"), "ph.chart-pie")
        prow = QHBoxLayout()
        prow.setSpacing(S.px(10))
        self._proto_donut = Donut(value_pt=16, sub_pt=8)
        self._proto_donut.setMinimumSize(S.px(110), S.px(110))
        prow.addWidget(self._proto_donut, 3)
        pl = QVBoxLayout()
        pl.addStretch()
        self._p_tcp = DotRow("ACCENT_GREEN", "TCP", "0")
        self._p_udp = DotRow("ACCENT_CYAN", "UDP", "0")
        self._p_oth = DotRow("TEXT_MUTED", tr("Other"), "0")
        for w in (self._p_tcp, self._p_udp, self._p_oth):
            pl.addWidget(w)
        pl.addStretch()
        prow.addLayout(pl, 2)
        proto.body.addLayout(prow)

        self._states = RankPanel(tr("Connection states"), "ph.plugs-connected", "ACCENT_GREEN")

        # ---- traffic history ------------------------------------------
        self._traffic_graph = AreaChart(
            ["ACCENT_GREEN", "ACCENT_CYAN"], None, store=self._traffic_store,
            y_fmt=lambda v: (f"{v:.1f}" if v < 10 else f"{v:.0f}") + f" {network_speed_value(0)[1]}")
        traffic = ChartPanel(tr("Network Traffic"), "ph.chart-line", self._traffic_graph, tabs=True,
                             legend=[("ACCENT_GREEN", tr("Download")), ("ACCENT_CYAN", tr("Upload"))])
        traffic.setMinimumHeight(S.px(240))
        traffic.setProperty("flex_max", 420)

        # ---- totals / peaks ---------------------------------------------
        self._t_recv = KpiTile("Total Recv", "ph.download-simple", "ACCENT_GREEN")
        self._t_sent = KpiTile("Total Sent", "ph.upload-simple", "ACCENT_CYAN")
        self._t_pdn = KpiTile("Peak download", "ph.trend-up", "ACCENT_GREEN")
        self._t_pup = KpiTile("Peak upload", "ph.trend-up", "ACCENT_CYAN")

        # ---- adapters ---------------------------------------------------
        self._adapters_panel = Panel(tr("Network adapters"), "ph.globe")
        self._cards_grid = ReflowGrid([], max_cols=2, min_col_width=330)
        self._adapters_panel.body.addWidget(self._cards_grid)
        self._no_adapter = QLabel(tr("No adapters found"))
        self._no_adapter.setObjectName("RefMuted")
        self._adapters_panel.body.addWidget(self._no_adapter)
        self._adapters_panel.body.addStretch()
        self._virtual = VirtualAdapterList()

        status = Panel(tr("System Status"), "ph.shield-check")
        self._s_health = KV(tr("Health"), tr("Good"), value_color="STATUS_GREEN")
        self._s_uptime = KV(tr("Uptime"), "-")
        self._s_up = KV(tr("Adapters up"), "-")
        self._s_active = KV(tr("Active interface"), "-")
        for w in (self._s_health, self._s_uptime, self._s_up, self._s_active):
            status.body.addWidget(w)
        status.body.addStretch()

        # ---- topology + connection analytics -----------------------------
        topo = Panel(tr("Network Topology"), "ph.broadcast")
        self._topology = TopologyView()
        topo.body.addWidget(self._topology)
        self._ports = RankPanel(tr("Top remote ports"), "ph.door-open", "ACCENT_CYAN")
        self._hosts = RankPanel(tr("Top remote hosts"), "ph.globe-hemisphere-west", "ACCENT_GREEN")

        # ---- connection table with search --------------------------------
        conn = Panel(tr("Active Connections"), "ph.link")
        self._search = QLineEdit()
        self._search.setPlaceholderText(tr("Search connections..."))
        self._search.setClearButtonEnabled(True)
        self._search.setMinimumWidth(S.px(150))
        self._search.setMaximumWidth(S.px(260))
        conn.add_header_widget(self._search)
        self._conn_count = QLabel("")
        self._conn_count.setObjectName("RefMuted")
        conn.add_header_widget(self._conn_count)
        self._conn_table = ConnectionsTable()
        self._conn_table.setMinimumHeight(S.px(280))
        self._search.textChanged.connect(self._conn_table.set_filter)
        conn.body.addWidget(self._conn_table)

        grid = ReflowGrid([
            (self._kpi_down, 1), (self._kpi_up, 1), (proto, 1), (self._states, 1),
            (traffic, 4),
            (self._t_recv, 1), (self._t_sent, 1), (self._t_pdn, 1), (self._t_pup, 1),
            (self._adapters_panel, 2), (self._virtual, 1), (status, 1),
            (topo, 2), (self._ports, 1), (self._hosts, 1),
            (conn, 4),
        ], max_cols=4, min_col_width=250)
        container = QWidget()
        container.setObjectName("RefContent")
        container.setStyleSheet("QWidget#RefContent { background: transparent; }")
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, S.px(4), 0)
        cl.addWidget(grid)
        cl.addStretch(1)
        scroll.setWidget(container)
        grid.bind_viewport(scroll)

    def _on_refresh_changed(self, text: str):
        try:
            self._conn_interval = int(text.replace("s", ""))
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # data
    # ------------------------------------------------------------------
    def update_data(self, data: dict):
        self._on_data(data)

    def _on_data(self, data: dict):
        net = data.get("network")
        if not net:
            return
        self._last_data = data

        dn_speed, unit = network_speed_value(net.get("download_speed", 0))
        up_speed, _ = network_speed_value(net.get("upload_speed", 0))
        precision = settings.get('decimal_places', 1)
        sent = net.get("bytes_sent", 0)
        recv = net.get("bytes_recv", 0)

        ifaces = net.get("interfaces")
        if ifaces:
            self._ifaces = ifaces
        elif not self._ifaces:
            self._ifaces = self._read_interfaces()
        active = net.get("active_interface") or ""
        link_mbps = (self._ifaces.get(active) or {}).get("speed", 0)
        link_lbl = link_text(link_mbps)
        if link_lbl:
            fixed = network_speed_value(link_mbps * 1_000_000 / 8.0)[0]
            self._kpi_down.set_fixed_max(fixed)
            self._kpi_up.set_fixed_max(fixed)
            of = f"{tr('of')} {link_lbl}"
        else:
            self._kpi_down.set_fixed_max(None)
            self._kpi_up.set_fixed_max(None)
            of = ""
        self._kpi_down.set_unit(unit)
        self._kpi_up.set_unit(unit)
        self._kpi_down.set_value(f"{dn_speed:.{precision}f}", " · ".join(x for x in (f"↓ {fmt_bytes(recv)}", of) if x))
        self._kpi_up.set_value(f"{up_speed:.{precision}f}", " · ".join(x for x in (f"↑ {fmt_bytes(sent)}", of) if x))

        self._traffic_graph.push(dn_speed, up_speed)
        self._peak_dn = max(self._peak_dn, dn_speed)
        self._peak_up = max(self._peak_up, up_speed)
        rv, ru = self._split(recv)
        sv, su = self._split(sent)
        self._t_recv.set_value(rv, ru)
        self._t_sent.set_value(sv, su)
        self._t_pdn.set_value(f"{self._peak_dn:.1f}".replace(".", ","), unit)
        self._t_pup.set_value(f"{self._peak_up:.1f}".replace(".", ","), unit)

        self._update_nic_rates()
        self._refresh_adapters(active)

        conns = net.get("connections")
        if conns is not None:
            self._conns = conns
            if time.time() - self._last_conn_ui >= self._conn_interval:
                self._last_conn_ui = time.time()
                self._refresh_connections(conns)

    @staticmethod
    def _read_interfaces() -> Dict[str, dict]:
        """Adapter list straight from the OS (the collector only refreshes it every 10 s,
        so this fills the view immediately after start)."""
        out: Dict[str, dict] = {}
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            for name, st in stats.items():
                ip = "—"
                for a in addrs.get(name, []):
                    if a.family == socket.AF_INET:
                        ip = a.address
                        break
                out[name] = {'isup': st.isup, 'speed': st.speed, 'ip': ip}
        except Exception:
            pass
        return out

    @staticmethod
    def _split(n: float):
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or unit == "TB":
                return (f"{n:.0f}" if unit == "B" else f"{n:.1f}".replace(".", ",")), unit
            n /= 1024
        return "0", "B"

    def _update_nic_rates(self):
        """Per-adapter throughput from the OS counters (cheap, once per data tick)."""
        try:
            now = time.time()
            cur = psutil.net_io_counters(pernic=True)
        except Exception:
            return
        for name, c in cur.items():
            self._nic_total[name] = (c.bytes_sent, c.bytes_recv)
            prev = self._nic_prev.get(name)
            if prev and now - prev[0] >= 0.25:
                dt = now - prev[0]
                self._nic_rate[name] = (max(0.0, (c.bytes_recv - prev[1]) / dt),
                                        max(0.0, (c.bytes_sent - prev[2]) / dt))
                self._nic_prev[name] = (now, c.bytes_recv, c.bytes_sent)
            elif not prev:
                self._nic_prev[name] = (now, c.bytes_recv, c.bytes_sent)

    def _refresh_adapters(self, active: str):
        ifaces = self._ifaces
        if not ifaces:
            return
        physical = [n for n in ifaces if not is_virtual(n)]
        physical.sort(key=lambda n: (not ifaces[n].get('isup'), n))
        virtual = [n for n in ifaces if is_virtual(n)]
        virtual.sort(key=lambda n: (not ifaces[n].get('isup'), n))

        if physical != self._card_order:
            for name in list(self._cards):
                self._cards_grid.remove_widget(self._cards[name])
                self._cards[name].deleteLater()
            self._cards = {}
            for name in physical:
                card = AdapterCard(name)
                self._cards[name] = card
                self._cards_grid.add_widget(card)
            self._card_order = physical
        self._no_adapter.setVisible(not physical)

        for name, card in self._cards.items():
            info = ifaces.get(name, {})
            dn, up = self._nic_rate.get(name, (0.0, 0.0))
            sent, recv = self._nic_total.get(name, (0, 0))
            card.update_adapter(bool(info.get('isup')), info.get('ip', ""), info.get('speed', 0), dn, up, sent, recv)

        self._virtual.set_adapters([(n, bool(ifaces[n].get('isup')), ifaces[n].get('ip', "")) for n in virtual])

        up_count = sum(1 for n in ifaces if ifaces[n].get('isup'))
        self._s_up.set_value(f"{up_count} / {len(ifaces)}")
        self._s_active.set_value(active or "-")
        phys_up = any(ifaces[n].get('isup') for n in physical)
        self._s_health.val_lbl.setStyleSheet(f"color: {hexcol('STATUS_GREEN' if phys_up else 'ACCENT_RED')};")
        self._s_health.set_value(tr("Good") if phys_up else tr("Offline"))

        topo = []
        for n in physical:
            topo.append({"name": n, "up": bool(ifaces[n].get('isup')), "ip": ifaces[n].get('ip', ""),
                         "kind": "wifi" if is_wifi(n) else "lan"})
        for n in virtual:
            if is_vpn(n) and ifaces[n].get('isup'):
                topo.append({"name": n, "up": True, "ip": ifaces[n].get('ip', ""), "kind": "vpn"})
        other_virtual = [n for n in virtual if not is_vpn(n)]
        if other_virtual:
            topo.append({"name": f"{tr('Virtual')} ({len(other_virtual)})",
                         "up": any(ifaces[n].get('isup') for n in other_virtual), "ip": "", "kind": "virtual"})
        self._topology.setMinimumHeight(max(S.px(190), S.px(70) * len(topo)))
        self._topology.set_state(self._hostname, topo)

    def _refresh_connections(self, rows: List[Dict]):
        self._conn_table.load(rows)
        self._conn_count.setText(f"{len(rows)}")

        tcp = sum(1 for r in rows if r.get("proto") == "TCP")
        udp = sum(1 for r in rows if r.get("proto") == "UDP")
        other = max(len(rows) - tcp - udp, 0)
        total = max(len(rows), 1)
        self._proto_donut.set_data(
            [(tcp / total * 100, "ACCENT_GREEN"), (udp / total * 100, "ACCENT_CYAN"), (other / total * 100, "TEXT_MUTED")],
            str(len(rows)), tr("connections"))
        self._p_tcp.set_value(f"{tcp} ({tcp / total * 100:.0f} %)")
        self._p_udp.set_value(f"{udp} ({udp / total * 100:.0f} %)")
        self._p_oth.set_value(f"{other} ({other / total * 100:.0f} %)")

        states = Counter(r.get("state", "") for r in rows if r.get("proto") == "TCP" and r.get("state"))
        self._states.set_items([(s, c, str(c)) for s, c in states.most_common(5)])

        ports = Counter(r.get("remote_port") for r in rows
                        if _is_remote(r.get("remote_ip", "")) and isinstance(r.get("remote_port"), int))
        port_items = []
        for port, cnt in ports.most_common(5):
            name = PORT_NAMES.get(port)
            port_items.append((f"{port} · {name}" if name else str(port), cnt, str(cnt)))
        self._ports.set_items(port_items)

        hosts = Counter(r.get("remote_ip") for r in rows if _is_remote(r.get("remote_ip", "")))
        self._hosts.set_items([(ip, cnt, str(cnt)) for ip, cnt in hosts.most_common(5)])

    def _refresh_status(self):
        up_secs = int(time.time() - self._boot_time)
        d, rem = divmod(up_secs, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        if hasattr(self, '_s_uptime'):
            try:
                self._s_uptime.set_value(f"{d}d {h:02d}h {m:02d}m")
            except RuntimeError:
                pass
