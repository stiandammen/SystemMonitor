"""
Network view building blocks (redesign): adapter cards with live gauges and
sparklines, virtual-adapter list, ranked bar lists, and a topology diagram
built from the machine's real adapters.
"""
from collections import deque
from typing import Dict, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr
from systemmonitor.scaler import S
from systemmonitor.utils.helpers import network_speed_value
from systemmonitor.widgets.ref_design import (
    Panel, BigGauge, AreaChart, BarRow, KV, _label, col, tc, hexcol,
)

_VIRTUAL_HINTS = (
    "vethernet", "loopback", "bluetooth", "local area connection*", "hyper-v", "vmware",
    "virtualbox", "wsl", "npcap", "tailscale", "zerotier", "teredo", "isatap", "vpn",
    "tap-", "tunnel", "pseudo", "docker", "vboxnet", "wi-fi direct",
)
_VPN_HINTS = ("tailscale", "zerotier", "vpn", "wireguard", "openvpn", "tap-")

PORT_NAMES = {
    20: "FTP", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    80: "HTTP", 110: "POP3", 123: "NTP", 135: "RPC", 137: "NetBIOS", 138: "NetBIOS", 139: "NetBIOS",
    143: "IMAP", 389: "LDAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP", 993: "IMAPS",
    995: "POP3S", 1433: "SQL Server", 1900: "SSDP", 3306: "MySQL", 3389: "RDP", 5353: "mDNS",
    5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-alt", 8443: "HTTPS-alt", 9012: "Lokal",
}


def is_virtual(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in _VIRTUAL_HINTS)


def is_vpn(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in _VPN_HINTS)


def is_wifi(name: str) -> bool:
    n = name.lower()
    return "wi-fi" in n or "wifi" in n or "wlan" in n or "wireless" in n


def link_text(mbps: int) -> str:
    """Realistic link speed label. Drivers report 0 / 4294 (0xFFFFFFFF) for virtual links."""
    if mbps is None or mbps <= 0 or mbps >= 100_000 or mbps == 4294:
        return ""
    if mbps >= 1000:
        return f"{mbps / 1000:.2f} Gbps".replace(".", ",").replace(",00", "")
    return f"{mbps} Mbps"


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return (f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}").replace(".", ",")
        n /= 1024
    return f"{n:.1f} PB".replace(".", ",")


# ---------------------------------------------------------------------------
# Adapter card
# ---------------------------------------------------------------------------
class AdapterCard(QFrame):
    """One physical adapter: status, link speed, load gauge (vs link speed),
    live down/up rates and a 60 s history chart."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("RefPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._name = name
        self._icon_name = "ph.wifi-high" if is_wifi(name) else "ph.plugs-connected"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(S.px(12), S.px(10), S.px(12), S.px(10))
        lay.setSpacing(S.px(8))

        head = QHBoxLayout()
        head.setSpacing(S.px(8))
        self._ico = QLabel()
        self._ico.setStyleSheet("background: transparent; border: none;")
        head.addWidget(self._ico)
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self._title = _label(name, "RefTitle", 11, True)
        self._title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._ip = _label("", "RefMuted", 8)
        title_col.addWidget(self._title)
        title_col.addWidget(self._ip)
        head.addLayout(title_col, 1)
        self._state = _label("", "RefPill", 8, True)
        self._state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(self._state)
        lay.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(S.px(10))
        self._gauge = BigGauge("ACCENT_GREEN", "", show_ends=False, value_pt=12)
        self._gauge.setMinimumSize(S.px(92), S.px(92))
        self._gauge.setMaximumWidth(S.px(130))
        body.addWidget(self._gauge)
        side = QVBoxLayout()
        side.setSpacing(S.px(2))
        side.addStretch()
        self._link = KV(tr("Link speed"), "--")
        self._dn = KV(tr("Download"), "--", value_color="ACCENT_GREEN")
        self._up = KV(tr("Upload"), "--", value_color="ACCENT_CYAN")
        self._total = KV(tr("Total"), "--")
        for w in (self._link, self._dn, self._up, self._total):
            side.addWidget(w)
        side.addStretch()
        body.addLayout(side, 1)
        lay.addLayout(body)

        self._chart = AreaChart(["ACCENT_GREEN", "ACCENT_CYAN"], None, y_fmt=lambda v: f"{v:.0f}", min_auto=1.0, compact=True)
        self._chart._window = 60
        self._chart.setMinimumHeight(S.px(70))
        self._chart.setMaximumHeight(S.px(110))
        lay.addWidget(self._chart)
        self._restyle()
        theme_manager.theme_changed.connect(self._restyle)

    def _restyle(self, *_):
        try:
            sz = S.px(20)
            self._ico.setPixmap(qta.icon(self._icon_name, color=theme_manager.colors.ACCENT_GREEN).pixmap(sz, sz))
        except Exception:
            pass

    def update_adapter(self, is_up: bool, ip: str, link_mbps: int, dn_bps: float, up_bps: float,
                       sent: float, recv: float):
        self._ip.setText(ip if ip and ip != "—" else tr("No address"))
        self._state.setText(tr("Connected") if is_up else tr("Disconnected"))
        self._state.setProperty("state", "ok" if is_up else "bad")
        self._state.style().unpolish(self._state)
        self._state.style().polish(self._state)
        lt = link_text(link_mbps)
        self._link.set_value(lt or "--")
        dn, unit = network_speed_value(dn_bps)
        up, _ = network_speed_value(up_bps)
        self._dn.set_value(f"{dn:.1f} {unit}".replace(".", ","))
        self._up.set_value(f"{up:.1f} {unit}".replace(".", ","))
        self._total.set_value(f"↓ {fmt_bytes(recv)}  ↑ {fmt_bytes(sent)}")
        # gauge: current load as a share of the real link speed
        if link_mbps and lt:
            load = (max(dn_bps, up_bps) * 8 / 1_000_000) / link_mbps * 100.0
            self._gauge.set_percent(min(100.0, load), text=f"{max(dn, up):.1f}".replace(".", ","), caption=unit)
        else:
            self._gauge.set_percent(0, text=f"{max(dn, up):.1f}".replace(".", ","), caption=unit)
        self._chart.push(dn, up)


# ---------------------------------------------------------------------------
# Virtual adapters list
# ---------------------------------------------------------------------------
class VirtualAdapterList(Panel):
    """Compact list of virtual / VPN / loopback adapters (no fake link speeds)."""

    def __init__(self, parent=None):
        super().__init__(tr("Virtual adapters"), "ph.cube", parent)
        self._lay = QVBoxLayout()
        self._lay.setSpacing(S.px(4))
        self.body.addLayout(self._lay)
        self.body.addStretch()
        self._sig = None

    def set_adapters(self, items: List[Tuple[str, bool, str]]):
        sig = tuple(items)
        if sig == self._sig:
            return
        self._sig = sig
        while self._lay.count():
            it = self._lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for name, up, ip in items:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, S.px(2), 0, S.px(2))
            h.setSpacing(S.px(8))
            dot = QLabel()
            dot.setFixedSize(S.px(8), S.px(8))
            colr = theme_manager.colors.STATUS_GREEN if up else theme_manager.colors.TEXT_MUTED
            dot.setStyleSheet(f"background-color: {colr}; border: none; border-radius: {S.px(4)}px;")
            h.addWidget(dot)
            nm = _label(name, "RefValue", 9, True)
            nm.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            h.addWidget(nm, 1)
            tag = "VPN" if is_vpn(name) else (tr("Loopback") if "loopback" in name.lower() else tr("Virtual"))
            h.addWidget(_label(tag, "RefMuted", 8))
            self._lay.addWidget(row)
            if ip and ip != "—":
                self._lay.itemAt(self._lay.count() - 1).widget().setToolTip(ip)


# ---------------------------------------------------------------------------
# Ranked list (top ports / hosts / states)
# ---------------------------------------------------------------------------
class RankPanel(Panel):
    """Panel listing up to N labelled bars, rebuilt only when the labels change."""

    def __init__(self, title: str, icon: str, color: str = "ACCENT_GREEN", parent=None):
        super().__init__(title, icon, parent)
        self._color = color
        self._rows: List[BarRow] = []
        self._labels: List[str] = []
        self._lay = QVBoxLayout()
        self._lay.setSpacing(S.px(4))
        self.body.addLayout(self._lay)
        self._empty = _label(tr("No data"), "RefMuted", 9)
        self.body.addWidget(self._empty)
        self.body.addStretch()

    def set_items(self, items: List[Tuple[str, float, str]]):
        """items = [(label, magnitude, right_text), ...] (already sorted)."""
        self._empty.setVisible(not items)
        labels = [i[0] for i in items]
        if labels != self._labels:
            self._labels = labels
            while self._lay.count():
                it = self._lay.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
            self._rows = []
            for lab in labels:
                r = BarRow(lab, self._color)
                self._lay.addWidget(r)
                self._rows.append(r)
        top = max([i[1] for i in items] or [1.0]) or 1.0
        for r, (_lab, mag, text) in zip(self._rows, items):
            r.set_data(mag / top * 100.0, text)


# ---------------------------------------------------------------------------
# Topology diagram (real adapters)
# ---------------------------------------------------------------------------
class TopologyView(QWidget):
    """This PC -> its adapters -> network category (LAN / Internet / VPN / virtual)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._host = "PC"
        self._adapters: List[Dict] = []
        self.setMinimumHeight(S.px(190))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_state(self, host: str, adapters: List[Dict]):
        """adapters: [{name, up, kind('lan'|'wifi'|'vpn'|'virtual'), ip}]"""
        sig = (host, tuple((a['name'], a['up'], a['kind']) for a in adapters))
        if sig != getattr(self, '_sig', None):
            self._sig = sig
            self._host, self._adapters = host, adapters
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors
        w, h = self.width(), self.height()
        acc, ok, mut = QColor(c.ACCENT_GREEN), QColor(c.STATUS_GREEN), QColor(c.TEXT_MUTED)
        adapters = self._adapters or []
        n = max(1, len(adapters))
        xs = (w * 0.10, w * 0.50, w * 0.90)
        row_h = h / n

        def node(x, y, label, sub, up=True, strong=False):
            r = S.px(15) if strong else S.px(11)
            colr = acc if strong else (ok if up else mut)
            ring = QColor(colr); ring.setAlpha(60)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(ring)
            p.drawEllipse(QPointF(x, y), r + S.px(5), r + S.px(5))
            p.setBrush(colr)
            p.drawEllipse(QPointF(x, y), r, r)
            p.setPen(QColor(c.TEXT_PRIMARY))
            p.setFont(QFont("Cutive", S.font_pt(9), QFont.Weight.Bold))
            p.drawText(QRectF(x - w * 0.16, y + r + S.px(6), w * 0.32, S.px(16)), Qt.AlignmentFlag.AlignHCenter, label)
            if sub:
                p.setPen(QColor(c.TEXT_MUTED))
                p.setFont(QFont("Cutive", S.font_pt(8)))
                p.drawText(QRectF(x - w * 0.16, y + r + S.px(21), w * 0.32, S.px(14)), Qt.AlignmentFlag.AlignHCenter, sub)

        def link(x1, y1, x2, y2, up):
            pen = QPen(ok if up else mut, S.px(2))
            if not up:
                pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            path = QPainterPath(QPointF(x1, y1))
            path.cubicTo(QPointF((x1 + x2) / 2, y1), QPointF((x1 + x2) / 2, y2), QPointF(x2, y2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        cy = h / 2 - S.px(10)
        targets = {"lan": tr("Local network"), "wifi": tr("Local network"), "vpn": "VPN", "virtual": tr("Virtual network")}
        placed = {}
        for i, a in enumerate(adapters):
            y = row_h * (i + 0.5) - S.px(10)
            link(xs[0], cy, xs[1], y, a['up'])
            tgt = targets.get(a['kind'], tr("Network"))
            if tgt not in placed:
                placed[tgt] = []
            placed[tgt].append((y, a))
        for tgt, lst in placed.items():
            ty = sum(y for y, _ in lst) / len(lst)
            any_up = any(a['up'] for _, a in lst)
            for y, a in lst:
                link(xs[1], y, xs[2], ty, a['up'])
            node(xs[2], ty, tgt, "", any_up)
        for i, a in enumerate(adapters):
            y = row_h * (i + 0.5) - S.px(10)
            sub = a['ip'] if a.get('ip') and a['ip'] != "—" else ""
            node(xs[1], y, a['name'][:22], sub, a['up'])
        node(xs[0], cy, self._host, tr("This PC"), True, strong=True)
        p.end()
