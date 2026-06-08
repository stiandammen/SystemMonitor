"""
Reusable widget components for the Network view dashboard:
sparklines, KPI cards, traffic graph, protocol donut, connections table,
interface rows and the topology radar.
"""
import math
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QLinearGradient,
    QPainterPath, QRadialGradient
)
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.typing import Dict, List


def _qcolor(color_str: str) -> QColor:
    """Parse hex or CSS rgba(...) string into QColor"""
    s = color_str.strip()
    if s.startswith("rgba("):
        try:
            parts = s[5:-1].split(",")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = float(parts[3].strip())
            c = QColor(r, g, b)
            c.setAlphaF(a)
            return c
        except Exception:
            pass
    return QColor(s)


# ---------------------------------------------------------------------------
# Sparkline
# ---------------------------------------------------------------------------

class _Sparkline(QWidget, ScaleMixin):
    """Mini sparkline for KPI cards"""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._history: deque = deque(maxlen=30)
        self._pending = False
        self.scale_connect()
        self.setMinimumHeight(S.px(36))
        self.setMinimumWidth(S.px(70))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)

    def _flush(self):
        self._pending = False
        self.update()

    def push(self, value: float):
        self._history.append(max(0.0, value))
        if not self._pending:
            self._pending = True
            self._timer.start(33)

    def set_color(self, color: str):
        self._color = color
        self.update()

    def paintEvent(self, a0):
        if len(self._history) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors
        w, h = self.width(), self.height()
        pts = list(self._history)
        mx = max(pts) or 1
        step = w / (len(pts) - 1)

        coords = [(step * i, h - pts[i] / mx * h * 0.85 - 2) for i in range(len(pts))]

        # filled area
        fill = QPainterPath()
        fill.moveTo(coords[0][0], coords[0][1])
        for x, y in coords[1:]:
            fill.lineTo(x, y)
        fill.lineTo(coords[-1][0], h)
        fill.lineTo(coords[0][0], h)
        fill.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        top_c = QColor(self._color)
        top_c.setAlpha(80)
        bot_c = QColor(self._color)
        bot_c.setAlpha(5)
        grad.setColorAt(0, top_c)
        grad.setColorAt(1, bot_c)
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(fill)

        # line
        p.setPen(QPen(QColor(self._color), 1.5))
        for i in range(len(coords) - 1):
            p.drawLine(QPointF(*coords[i]), QPointF(*coords[i + 1]))
        p.end()


# ---------------------------------------------------------------------------
# KPI Card
# ---------------------------------------------------------------------------

class KpiCard(QFrame, ScaleMixin, I18nMixin):
    """Single KPI metric card"""

    def __init__(self, title: str, icon: str, accent: str, unit: str = "", parent=None):
        super().__init__(parent)
        self._title_key = title
        self._title = tr(title)
        self._icon_name = icon
        self._accent = accent
        self._unit = unit
        self.scale_connect()
        self.i18n_connect()
        self._build()
        theme_manager.theme_changed.connect(self._retheme)

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if hasattr(self, '_title_lbl'):
            self._title_lbl.setText(self._title)

    def _build(self):
        c = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(S.px(116))
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        lay = QVBoxLayout()
        lay.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        lay.setSpacing(S.px(4))
        self.setLayout(lay)

        # header row
        hdr = QHBoxLayout()
        hdr.setSpacing(S.px(8))

        ico = QLabel()
        try:
            ico.setPixmap(qta.icon(self._icon_name, color=self._accent).pixmap(S.px(16), S.px(16)))
        except Exception:
            ico.setText("")
        ico.setStyleSheet("background: transparent;")
        hdr.addWidget(ico)

        self._title_lbl = QLabel(self._title)
        self._title_lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._title_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        hdr.addWidget(self._title_lbl)
        hdr.addStretch()
        lay.addLayout(hdr)

        # value row — number + unit on the left, sparkline on the right
        vrow = QHBoxLayout()
        vrow.setSpacing(S.px(5))
        vrow.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # number + unit stacked in a mini VBox so they don't split across rows
        num_col = QVBoxLayout()
        num_col.setSpacing(0)
        num_col.setContentsMargins(0, 0, 0, 0)

        self._val_lbl = QLabel("--")
        self._val_lbl.setFont(QFont("Segoe UI", S.font_pt(28), QFont.Weight.Bold))
        self._val_lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
        num_col.addWidget(self._val_lbl)

        if self._unit:
            self._unit_lbl = QLabel(self._unit)
            self._unit_lbl.setFont(QFont("Segoe UI", S.font_pt(11)))
            self._unit_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
            num_col.addWidget(self._unit_lbl)

        num_wrap = QWidget()
        num_wrap.setStyleSheet("background: transparent;")
        num_wrap.setLayout(num_col)
        vrow.addWidget(num_wrap)

        vrow.addStretch()

        self._spark = _Sparkline(self._accent)
        self._spark.setFixedSize(S.px(88), S.px(44))
        vrow.addWidget(self._spark)
        lay.addLayout(vrow)

        # sub-label
        self._sub_lbl = QLabel("")
        self._sub_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._sub_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        lay.addWidget(self._sub_lbl)

    def _retheme(self, _name: str = ""):
        c = theme_manager.colors
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)
        if hasattr(self, "_title_lbl"):
            self._title_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        if hasattr(self, "_sub_lbl"):
            self._sub_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        if hasattr(self, "_unit_lbl"):
            self._unit_lbl.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")

    def set_unit(self, unit: str):
        """Update the unit label shown beneath the value (e.g. when the user
        switches between Mbps and MB/s)."""
        self._unit = unit
        if hasattr(self, "_unit_lbl"):
            self._unit_lbl.setText(unit)

    def set_value(self, value: str, sub: str = ""):
        self._val_lbl.setText(value)
        self._sub_lbl.setText(sub)
        try:
            self._spark.push(float(value.replace(",", ".")))
        except (ValueError, AttributeError):
            pass

    def set_accent(self, accent: str):
        self._accent = accent
        self._val_lbl.setStyleSheet(f"color: {accent}; background: transparent;")
        self._spark.set_color(accent)


# ---------------------------------------------------------------------------
# Traffic Graph
# ---------------------------------------------------------------------------

class TrafficGraph(QWidget, ScaleMixin):
    """Real-time upload / download graph"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._up: deque = deque(maxlen=60)
        self._dn: deque = deque(maxlen=60)
        self._peak = 1.0
        self._pending = False
        self._sample_stride = 1
        self._sample_skip = 0
        self.scale_connect()
        self.setMinimumHeight(S.px(160))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)

    def _flush(self):
        self._pending = False
        self.update()

    def set_max_points(self, max_points: int):
        """Resize the rolling history buffers (e.g. from the History Length setting)"""
        max_points = max(1, int(max_points))
        if max_points != self._up.maxlen:
            self._up = deque(self._up, maxlen=max_points)
            self._dn = deque(self._dn, maxlen=max_points)

    def set_sample_stride(self, stride: int):
        """Keep only every Nth incoming sample so a fixed-size buffer can span
        a longer time window (e.g. from the History Length setting)."""
        self._sample_stride = max(1, int(stride))
        self._sample_skip = 0

    def push(self, upload: float, download: float):
        self._sample_skip += 1
        if self._sample_skip < self._sample_stride:
            return
        self._sample_skip = 0
        self._up.append(max(0, upload))
        self._dn.append(max(0, download))
        all_vals = list(self._up) + list(self._dn)
        self._peak = max(max(all_vals) * 1.15, 0.1)
        if not self._pending:
            self._pending = True
            self._timer.start(33)

    def paintEvent(self, a0):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors
        w, h = self.width(), self.height()

        # background
        p.fillRect(self.rect(), _qcolor(c.BG_CARD))

        ml, mr, mt, mb = S.px(54), S.px(16), S.px(16), S.px(28)
        gw = w - ml - mr
        gh = h - mt - mb

        if gw <= 0 or gh <= 0:
            p.end()
            return

        # grid
        grid_pen = QPen(QColor(c.BORDER), 1, Qt.PenStyle.DotLine)
        p.setPen(grid_pen)
        for i in range(5):
            y = mt + gh * i / 4
            p.drawLine(int(ml), int(y), int(w - mr), int(y))

        # y-axis labels
        p.setFont(QFont("Segoe UI", S.font_pt(8)))
        p.setPen(QColor(c.TEXT_SECONDARY))
        fm = p.fontMetrics()
        for i in range(5):
            val = self._peak * (4 - i) / 4
            label = self._fmt(val)
            lw = fm.horizontalAdvance(label)
            p.drawText(int(ml - lw - S.px(4)), int(mt + gh * i / 4 + fm.ascent() / 2), label)

        def draw_series(hist, color_str):
            if len(hist) < 2:
                return
            pts = list(hist)
            step = gw / (len(pts) - 1)
            coords = [(ml + step * i, mt + gh - pts[i] / self._peak * gh) for i in range(len(pts))]

            fill = QPainterPath()
            fill.moveTo(coords[0][0], coords[0][1])
            for x, y in coords[1:]:
                fill.lineTo(x, y)
            fill.lineTo(coords[-1][0], mt + gh)
            fill.lineTo(coords[0][0], mt + gh)
            fill.closeSubpath()

            grad = QLinearGradient(0, mt, 0, mt + gh)
            top = QColor(color_str); top.setAlpha(55)
            bot = QColor(color_str); bot.setAlpha(5)
            grad.setColorAt(0, top)
            grad.setColorAt(1, bot)
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(fill)

            p.setPen(QPen(QColor(color_str), 2))
            for i in range(len(coords) - 1):
                p.drawLine(QPointF(*coords[i]), QPointF(*coords[i + 1]))

        draw_series(self._dn, c.ACCENT_CYAN)
        draw_series(self._up, c.ACCENT_PURPLE)

        # legend
        p.setFont(QFont("Segoe UI", S.font_pt(9)))
        lx = ml + S.px(8)
        ly = h - S.px(8)

        for color_str, sym, label in [
            (c.ACCENT_CYAN, "▼", tr("Download")),
            (c.ACCENT_PURPLE, "▲", tr("Upload")),
        ]:
            p.setPen(QColor(color_str))
            p.drawText(lx, ly, f"{sym} {label}")
            lx += fm.horizontalAdvance(f"{sym} {label}") + S.px(20)

        p.end()

    @staticmethod
    def _fmt(val: float) -> str:
        if val >= 1000:
            return f"{val / 1000:.1f}G"
        if val >= 1:
            return f"{val:.1f}M"
        return f"{val * 1000:.0f}K"


# ---------------------------------------------------------------------------
# Donut chart
# ---------------------------------------------------------------------------

class _Donut(QWidget, ScaleMixin):
    """Protocol distribution donut"""

    _PALETTE = ["ACCENT_GREEN", "ACCENT_BLUE", "ACCENT_ORANGE", "ACCENT_PINK", "ACCENT_PURPLE"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, float] = {}
        self.scale_connect()
        self.setFixedSize(S.px(120), S.px(120))
        theme_manager.theme_changed.connect(self.update)

    def set_data(self, data: Dict[str, float]):
        self._data = data
        self.update()

    def paintEvent(self, a0):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), _qcolor(c.BG_CARD))

        if not self._data:
            p.end()
            return

        cx, cy = w / 2, h / 2
        outer = min(w, h) / 2 - S.px(6)
        inner = outer * 0.58
        total = sum(self._data.values()) or 1
        angle = 90.0

        for i, (_, val) in enumerate(self._data.items()):
            if val <= 0:
                continue
            sweep = val / total * 360
            col = QColor(getattr(c, self._PALETTE[i % len(self._PALETTE)]))
            p.setBrush(col)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPie(int(cx - outer), int(cy - outer), int(outer * 2), int(outer * 2),
                      int(angle * 16), int(-sweep * 16))
            angle += sweep

        # hole
        p.setBrush(_qcolor(c.BG_CARD))
        p.drawEllipse(int(cx - inner), int(cy - inner), int(inner * 2), int(inner * 2))
        p.end()


# ---------------------------------------------------------------------------
# Connections Table
# ---------------------------------------------------------------------------

class ConnectionsTable(QTableWidget, I18nMixin):
    """Active TCP/UDP connections"""

    _HEADERS = ["Local IP", "Port", "Remote IP", "Port", "Proto", "State"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n_connect()
        self._build()

    def retranslate_ui(self):
        self._build()

    def _build(self):
        c = theme_manager.colors
        self.setColumnCount(len(self._HEADERS))
        self.setHorizontalHeaderLabels([tr(h) for h in self._HEADERS])
        self.horizontalHeader().setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.setFont(QFont("Segoe UI", S.font_pt(9)))
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: none;
                alternate-background-color: {c.BG_SECONDARY};
            }}
            QTableWidget::item {{
                padding: {S.px(6)}px {S.px(10)}px;
                color: {c.TEXT_PRIMARY};
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
            }}
            QTableWidget::item:alternate {{
                background-color: {c.BG_SECONDARY};
            }}
            QHeaderView::section {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_SECONDARY};
                padding: {S.px(8)}px {S.px(10)}px;
                border: none;
                font-weight: bold;
            }}
            QHeaderView {{
                border: none;
            }}
        """)

    def retheme(self):
        self._build()

    def load(self, rows: List[Dict]):
        self.setRowCount(0)
        c = theme_manager.colors
        state_colors = {
            "ESTABLISHED": c.ACCENT_GREEN,
            "LISTEN": c.ACCENT_BLUE,
            "TIME_WAIT": c.ACCENT_ORANGE,
            "CLOSE_WAIT": c.ACCENT_YELLOW,
            "SYN_SENT": c.ACCENT_CYAN,
            "NONE": c.TEXT_SECONDARY,
        }
        for row in rows[:60]:
            r = self.rowCount()
            self.insertRow(r)
            values = [
                row.get("local_ip", "-"),
                str(row.get("local_port", "-")),
                row.get("remote_ip", "-"),
                str(row.get("remote_port", "-")),
                row.get("proto", "-"),
                row.get("state", "-"),
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFont(QFont("Segoe UI", S.font_pt(9)))
                if col == 5:  # state column — colour coded
                    color = state_colors.get(text.upper(), c.TEXT_SECONDARY)
                    item.setForeground(QColor(color))
                self.setItem(r, col, item)


# ---------------------------------------------------------------------------
# Interface row
# ---------------------------------------------------------------------------

class _IfaceRow(QFrame, ScaleMixin):
    """One interface status row"""

    def __init__(self, name: str, is_up: bool, speed: int, ip: str, parent=None):
        super().__init__(parent)
        self.scale_connect()
        c = theme_manager.colors
        self.setFrameShape(QFrame.Shape.NoFrame)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_SECONDARY};
                border: none;
                border-radius: {S.px(8)}px;
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(S.px(12), S.px(10), S.px(12), S.px(10))
        row.setSpacing(S.px(12))

        # status dot
        dot = QFrame()
        dot.setFrameShape(QFrame.Shape.NoFrame)
        dot.setFixedSize(S.px(8), S.px(8))
        dot_color = c.ACCENT_GREEN if is_up else c.ACCENT_RED
        dot.setStyleSheet(f"background-color: {dot_color}; border: none; border-radius: {S.px(4)}px;")
        row.addWidget(dot)

        # name
        lbl_name = QLabel(name)
        lbl_name.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        lbl_name.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        row.addWidget(lbl_name)

        # ip
        lbl_ip = QLabel(ip or "—")
        lbl_ip.setFont(QFont("Segoe UI", S.font_pt(9)))
        lbl_ip.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        row.addWidget(lbl_ip)

        row.addStretch()

        # speed badge
        speed_str = f"{speed} Mbps" if speed > 0 else (tr("Up") if is_up else tr("Down"))
        lbl_speed = QLabel(speed_str)
        lbl_speed.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        color = c.ACCENT_CYAN if is_up else c.TEXT_SECONDARY
        lbl_speed.setStyleSheet(f"color: {color}; background: transparent;")
        row.addWidget(lbl_speed)


# ---------------------------------------------------------------------------
# Radar / Topology
# ---------------------------------------------------------------------------

class _Radar(QWidget, ScaleMixin):
    """Animated network topology radar"""

    _NODES = [
        {"id": "ROUTER", "dist": 0.26, "angle": 90,  "status": "active"},
        {"id": "SERVER", "dist": 0.52, "angle": 38,  "status": "active"},
        {"id": "NAS",    "dist": 0.52, "angle": 142, "status": "active"},
        {"id": "PC-01",  "dist": 0.78, "angle": 12,  "status": "active"},
        {"id": "PC-02",  "dist": 0.78, "angle": 72,  "status": "standby"},
        {"id": "CAM",    "dist": 0.78, "angle": 128, "status": "active"},
        {"id": "IOT",    "dist": 0.78, "angle": 168, "status": "offline"},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self.setMinimumHeight(S.px(200))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(25)
        theme_manager.theme_changed.connect(self.update)

    def _tick(self):
        self._angle = (self._angle + 1) % 360
        self.update()

    def _c(self):
        return theme_manager.colors

    def paintEvent(self, a0):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._c()
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), _qcolor(c.BG_CARD))

        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.42

        glow = QColor(0x0b, 0x9e, 0x70)  # JARVIS green

        # rings
        for frac in [0.25, 0.50, 0.75, 1.0]:
            rr = r * frac
            col = QColor(glow); col.setAlpha(30 if frac < 1 else 55)
            p.setPen(QPen(col, 1.2 if frac < 1 else 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), rr, rr)

        # crosshairs
        line_c = QColor(glow); line_c.setAlpha(20)
        p.setPen(QPen(line_c, 0.8, Qt.PenStyle.DotLine))
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            p.drawLine(QPointF(cx, cy), QPointF(cx + r * 1.02 * math.cos(rad),
                                                 cy + r * 1.02 * math.sin(rad)))

        # sweep afterglow
        for i in range(20):
            a = (self._angle - i * 3) % 360
            intensity = (1 - i / 20) ** 2
            alpha = int(35 * intensity)
            if alpha < 4:
                continue
            seg = QColor(glow); seg.setAlpha(alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(seg)
            path = QPainterPath()
            path.moveTo(cx, cy)
            path.arcTo(cx - r * 0.95, cy - r * 0.95, r * 1.9, r * 1.9, a - 90, -4)
            path.closeSubpath()
            p.drawPath(path)

        # sweep line
        sw_rad = math.radians(self._angle - 90)
        sx, sy = cx + r * math.cos(sw_rad), cy + r * math.sin(sw_rad)
        for width, alpha in [(18, 8), (12, 18), (7, 40), (3, 110), (1.5, 200)]:
            col = QColor(glow); col.setAlpha(alpha)
            p.setPen(QPen(col, width))
            p.drawLine(QPointF(cx, cy), QPointF(sx, sy))

        # nodes
        for node in self._NODES:
            rad = math.radians(node["angle"] - 90)
            nr = r * node["dist"]
            nx, ny = cx + nr * math.cos(rad), cy + nr * math.sin(rad)

            if node["status"] == "active":
                nc = QColor(glow)
            elif node["status"] == "standby":
                nc = QColor(c.ACCENT_ORANGE)
            else:
                nc = QColor(c.ACCENT_RED); nc.setAlpha(120)

            pulse = (math.sin(math.radians(self._angle * 1.2 + node["angle"])) + 1) / 2
            ns = int(4 + pulse * 3)

            for off, a in [(12, 14), (7, 25), (3, 50)]:
                g = QColor(nc); g.setAlpha(int(a * (0.5 + pulse * 0.5)))
                p.setBrush(g); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(nx, ny), ns + off, ns + off)

            p.setBrush(nc); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(nx, ny), ns, ns)

            # label
            lbl = node["id"]
            p.setFont(QFont("Segoe UI", S.font_pt(7), QFont.Weight.Bold))
            fm = p.fontMetrics()
            lw = fm.horizontalAdvance(lbl)
            lh = fm.height()
            lx, ly = nx - lw / 2, ny + ns + lh

            bg = _qcolor(c.BG_CARD); bg.setAlpha(200)
            p.fillRect(QRectF(lx - 3, ly - lh + 2, lw + 6, lh + 2), bg)
            p.setPen(QColor(c.TEXT_PRIMARY))
            p.drawText(QPointF(lx, ly), lbl)

        # center hub
        hub_grad = QRadialGradient(cx, cy, 16)
        hub_grad.setColorAt(0, glow)
        hub_grad.setColorAt(1, _qcolor(c.BG_CARD))
        p.setBrush(hub_grad)
        p.setPen(QPen(glow, 1.5))
        p.drawEllipse(QPointF(cx, cy), 14, 14)

        p.end()
