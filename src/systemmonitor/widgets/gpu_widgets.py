"""
Reusable widget components for the GPU view dashboard:
the colour palette, circular gauges, the realtime chart, info rows/section
cards and the per-GPU detail views (GPUSingleView / GPUInfoView).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager, css_color_to_hex
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.utils.helpers import format_temperature, format_temperature_parts


# ---------------------------------------------------------------------------
# Fargepalett
# ---------------------------------------------------------------------------
COLORS: Dict[str, str] = {
    'bg_primary':    '#0a0e14',
    'bg_card':       '#161f2a',
    'bg_card_solid': '#161f2a',
    'bg_deeper':     '#0d1117',
    'bg_hover':      '#1e2936',
    'border':        '#2a3441',
    'border_solid':  '#2a3441',
    'text_primary':  '#f0f4f8',
    'text_secondary':'#94a3b8',
    'text_muted':    '#64748b',
    'accent_blue':   '#3b82f6',
    'accent_green':  '#10b981',
    'accent_purple': '#8b5cf6',
    'accent_orange': '#f59e0b',
    'accent_cyan':   '#06b6d4',
    'accent_red':    '#ef4444',
    'accent_yellow': '#ffd740',
}


def sync_colors() -> None:
    try:
        c = theme_manager.colors
        bg_card = c.BG_CARD
        bg_card_solid = getattr(c, 'BG_CARD_SOLID', None) or css_color_to_hex(bg_card)
        border = c.BORDER
        COLORS.update({
            'bg_primary':    c.BG_PRIMARY,
            'bg_card':       bg_card,
            'bg_card_solid': bg_card_solid,
            'bg_deeper':     c.BG_HOVER,
            'bg_hover':      c.BG_HOVER,
            'border':        border,
            'border_solid':  css_color_to_hex(border),
            'text_primary':  c.TEXT_PRIMARY,
            'text_secondary':c.TEXT_SECONDARY,
            'text_muted':    c.TEXT_MUTED,
            'accent_blue':   c.ACCENT_BLUE,
            'accent_green':  c.ACCENT_GREEN,
            'accent_purple': c.ACCENT_PURPLE,
            'accent_orange': c.ACCENT_ORANGE,
            'accent_cyan':   c.ACCENT_CYAN,
            'accent_red':    c.ACCENT_RED,
            'accent_yellow': c.ACCENT_YELLOW,
        })
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------
def _fmt(v, fmt: str = "{:.0f}", fallback: str = "N/A") -> str:
    if v is None:
        return fallback
    try:
        return fmt.format(float(v))
    except Exception:
        return str(v) if v is not None else fallback


def _flt(d: dict, key: str, default=None):
    v = d.get(key)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# GPUGauge – sirkulær måler
# ---------------------------------------------------------------------------
class GPUGauge(QFrame, ScaleMixin, I18nMixin):
    def __init__(self, title: str = "", unit: str = "%",
                 min_val: float = 0.0, max_val: float = 100.0,
                 warn_threshold: float = 70.0, crit_threshold: float = 90.0,
                 size: int = 110, parent=None):
        super().__init__(parent)
        self._title_key    = title
        self._title        = tr(title) if title else title
        self._unit         = unit
        self._min_val      = min_val
        self._max_val      = max_val
        self._warn         = warn_threshold
        self._crit         = crit_threshold
        self._display_val  = 0.0
        self._target_val   = 0.0
        self._subtitle     = ""
        self._glow         = 0.0
        self._pending      = False
        self._value_formatter = None

        self.setMinimumSize(S.px(size), S.px(size))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent; border: none;")

        self._draw_timer = QTimer(self)
        self._draw_timer.setSingleShot(True)
        self._draw_timer.timeout.connect(self._do_draw)

        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._step_glow)

        self.scale_connect()
        self.i18n_connect()

    def on_scale_changed(self, _): self.update()

    def retranslate_ui(self):
        self._title = tr(self._title_key) if self._title_key else self._title_key
        self.update()

    def _do_draw(self):
        self._pending = False
        self.update()

    def _step_glow(self):
        self._glow = max(0.0, self._glow - 0.05)
        if self._glow <= 0:
            self._glow_timer.stop()
        self.update()

    def set_value(self, value: float):
        if value is None:
            value = 0.0
        old = self._target_val
        self._target_val = max(self._min_val, min(float(value), self._max_val))
        if abs(self._target_val - old) > 1.0:
            self._glow = 0.8
            if not self._glow_timer.isActive():
                self._glow_timer.start(16)
        if not self._pending:
            self._pending = True
            self._draw_timer.start(16)

    def set_max_value(self, v: float):
        self._max_val = v if v and v > 0 else self._max_val

    def set_value_formatter(self, fn):
        """Override how the centered value text is rendered — fn(raw_value) -> str.
        The gauge's fill/threshold scale always stays in the raw value's unit;
        only the displayed text is converted (e.g. for the temperature-unit setting)."""
        self._value_formatter = fn

    def set_subtitle(self, text: str):
        self._subtitle = text

    def _color(self, pct: float) -> str:
        if pct >= self._crit: return COLORS['accent_red']
        if pct >= self._warn: return COLORS['accent_orange']
        return COLORS['accent_green']

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        sz  = min(self.width(), self.height())
        cx  = sz / 2

        diff = self._target_val - self._display_val
        self._display_val += diff * 0.15 if abs(diff) > 0.1 else diff

        rng     = self._max_val - self._min_val
        pct     = (self._display_val - self._min_val) / rng if rng else 0
        pct     = max(0.0, min(1.0, pct))
        col     = self._color(pct * 100)

        pw   = S.px(7)
        ar   = S.px(13)
        arc_r = sz - ar * 2

        # Track
        painter.setPen(QPen(QColor(COLORS['border_solid']), pw))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(ar, ar, arc_r, arc_r, 135 * 16, -270 * 16)

        # Glow
        gc = QColor(col)
        gc.setAlpha(40 + int(self._glow * 80))
        gp = QPen(gc, pw + 5 + int(self._glow * 7))
        gp.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(gp)
        painter.drawArc(ar, ar, arc_r, arc_r, 135 * 16, -270 * 16)

        # Arc
        ap = QPen(QColor(col), pw)
        ap.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(ap)
        painter.drawArc(ar, ar, arc_r, arc_r, 135 * 16, int(-270 * 16 * pct))

        # Center text
        fm = painter.fontMetrics()
        painter.setPen(QColor(COLORS['text_primary']))
        painter.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Light))
        fm = painter.fontMetrics()

        if self._title == "VRAM":
            # Show total GB at center
            gb_str  = f"{self._max_val / 1024:.0f}" if self._max_val >= 1024 else f"{self._max_val:.0f}"
            tw = fm.horizontalAdvance(gb_str)
            painter.drawText(int(cx - tw / 2), int(cx + 5), gb_str)
            painter.setFont(QFont("Segoe UI", S.font_pt(8)))
            painter.setPen(QColor(COLORS['text_secondary']))
            fm2 = painter.fontMetrics()
            painter.drawText(int(cx - fm2.horizontalAdvance("GB") / 2), int(cx + S.px(18)), "GB")
        else:
            if self._value_formatter is not None:
                val_str = self._value_formatter(self._display_val)
            else:
                val_str = f"{self._display_val:.0f}{self._unit}"
            tw = fm.horizontalAdvance(val_str)
            painter.drawText(int(cx - tw / 2), int(cx + 5), val_str)

        # Title
        if self._title:
            painter.setFont(QFont("Segoe UI", S.font_pt(7)))
            painter.setPen(QColor(COLORS['text_muted']))
            fm3 = painter.fontMetrics()
            tw3 = fm3.horizontalAdvance(self._title)
            painter.drawText(int(cx - tw3 / 2), int(cx + S.px(32)), self._title)

        painter.end()


# ---------------------------------------------------------------------------
# RealtimeGraph – sanntidsgrafikk
# ---------------------------------------------------------------------------
class RealtimeGraph(QWidget, ScaleMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._load: List[float] = []
        self._temp: List[float] = []
        self._max_pts = 60
        self._sample_stride = 1
        self._sample_skip = 0
        self._pending = False
        self.scale_connect()
        self.setMinimumHeight(S.px(130))

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_draw)

    def _do_draw(self):
        self._pending = False
        self.update()

    def set_max_points(self, max_points: int):
        """Resize the rolling history buffers (e.g. from the History Length setting)"""
        self._max_pts = max(1, int(max_points))
        if len(self._load) > self._max_pts:
            self._load = self._load[-self._max_pts:]
            self._temp = self._temp[-self._max_pts:]

    def set_sample_stride(self, stride: int):
        """Keep only every Nth incoming sample so a fixed-size buffer can span
        a longer time window (e.g. from the History Length setting)."""
        self._sample_stride = max(1, int(stride))
        self._sample_skip = 0

    def push(self, load: float, temp: float):
        self._sample_skip += 1
        if self._sample_skip < self._sample_stride:
            return
        self._sample_skip = 0
        self._load.append(load or 0)
        self._temp.append(temp or 0)
        if len(self._load) > self._max_pts:
            self._load.pop(0)
            self._temp.pop(0)
        if not self._pending:
            self._pending = True
            self._timer.start(33)

    # keep old call-site name
    def update_chart(self, load: float, temp: float):
        self.push(load, temp)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        painter.setBrush(QColor(COLORS['bg_card_solid']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        painter.setPen(QPen(QColor(COLORS['border_solid']), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = int(h * i / 4)
            painter.drawLine(0, y, w, y)

        if len(self._load) > 1:
            step = w / (self._max_pts - 1)
            pts_load = [(i * step, h - (v / 100.0 * h)) for i, v in enumerate(self._load)]

            # Fill under load
            fill = [(0, h)] + pts_load + [(pts_load[-1][0], h)]
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0, QColor(16, 185, 129, 90))
            grad.setColorAt(1, QColor(16, 185, 129, 5))
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            from PyQt6.QtCore import QPoint
            painter.drawPolygon(*[QPoint(int(x), int(y)) for x, y in fill])

            # Load line
            painter.setPen(QPen(QColor(COLORS['accent_green']), 2))
            for i in range(len(pts_load) - 1):
                painter.drawLine(int(pts_load[i][0]), int(pts_load[i][1]),
                                 int(pts_load[i+1][0]), int(pts_load[i+1][1]))

            # Temp line (normalised to 0-110°C -> 0-100%)
            pts_temp = [(i * step, h - (min(v, 110) / 110.0 * h))
                        for i, v in enumerate(self._temp)]
            painter.setPen(QPen(QColor(COLORS['accent_blue']), 2))
            for i in range(len(pts_temp) - 1):
                painter.drawLine(int(pts_temp[i][0]), int(pts_temp[i][1]),
                                 int(pts_temp[i+1][0]), int(pts_temp[i+1][1]))

        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(COLORS['accent_green']))
        painter.drawText(S.px(10), S.px(14), f"● {tr('Load')}")
        painter.setPen(QColor(COLORS['accent_blue']))
        painter.drawText(S.px(70), S.px(14), f"● {tr('Temp')}")
        painter.end()


# ---------------------------------------------------------------------------
# InfoRow – en nøkkel/verdi-rad
# ---------------------------------------------------------------------------
class InfoRow(QWidget, I18nMixin):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._label_key = label
        self.i18n_connect()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, S.px(1), 0, S.px(1))
        layout.setSpacing(0)

        self._key = QLabel(tr(label))
        self._key.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._key.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent;")
        self._key.setFixedWidth(S.px(140))
        layout.addWidget(self._key)

        layout.addStretch()

        self._val = QLabel("–")
        self._val.setFont(QFont("Consolas", S.font_pt(9)))
        self._val.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self._val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._val)

        self._unit = QLabel("")
        self._unit.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._unit.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self._unit.setFixedWidth(S.px(52))
        self._unit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._unit)

    def set_value(self, val: str, unit: str = ""):
        self._val.setText(val if val else "N/A")
        self._unit.setText(f"  {unit}" if unit else "")

    def retranslate_ui(self):
        self._key.setText(tr(self._label_key))

    def apply_theme(self):
        self._key.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent;")
        self._val.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self._unit.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")


# ---------------------------------------------------------------------------
# SectionCard – kortbeholder med tittel og rader
# ---------------------------------------------------------------------------
class SectionCard(QFrame, I18nMixin):
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._title_key = title
        self._icon_name = icon
        self.i18n_connect()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: none;
                border-radius: 10px;
            }}
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(S.px(14), S.px(8), S.px(14), S.px(10))
        outer.setSpacing(S.px(2))

        header = QHBoxLayout()
        header.setSpacing(S.px(6))
        header.setContentsMargins(0, 0, 0, 0)

        if icon:
            icon_lbl = QLabel()
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            try:
                sz = S.px(12)
                px = qta.icon(icon, color=COLORS['accent_green']).pixmap(QSize(sz, sz))
                icon_lbl.setPixmap(px)
                icon_lbl.setFixedSize(sz, sz)
            except Exception:
                pass
            header.addWidget(icon_lbl)
            self._icon_lbl = icon_lbl

        lbl = QLabel(tr(title))
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent; border: none;")
        header.addWidget(lbl)
        header.addStretch()
        outer.addLayout(header)
        self._title_lbl = lbl

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none; max-height: 1px;")
        sep.setMaximumHeight(1)
        outer.addWidget(sep)
        self._sep = sep

        self._rows: Dict[str, InfoRow] = {}
        self._layout = outer

    def add_row(self, row_id: str, label: str) -> InfoRow:
        row = InfoRow(label)
        self._rows[row_id] = row
        self._layout.addWidget(row)
        return row

    def set_value(self, row_id: str, val: str, unit: str = ""):
        r = self._rows.get(row_id)
        if r:
            r.set_value(val, unit)

    def show_row(self, row_id: str, visible: bool):
        r = self._rows.get(row_id)
        if r:
            r.setVisible(visible)

    def retranslate_ui(self):
        self._title_lbl.setText(tr(self._title_key))

    def apply_theme(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: none;
                border-radius: 10px;
            }}
        """)
        if hasattr(self, '_title_lbl'):
            self._title_lbl.setStyleSheet(
                f"color: {COLORS['accent_green']}; background: transparent; border: none;")
        if hasattr(self, '_sep'):
            self._sep.setStyleSheet(
                f"background: {COLORS['border']}; border: none; max-height: 1px;")
        for row in self._rows.values():
            row.apply_theme()


# ---------------------------------------------------------------------------
# GPUSingleView – komplett visning for én GPU
# ---------------------------------------------------------------------------
class GPUSingleView(QWidget, ScaleMixin, I18nMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self.i18n_connect()
        self._build()

        from systemmonitor.core.signals import signal_bus
        signal_bus.setting_changed.connect(self._on_setting_changed)
        self._apply_history_length()

    def _on_setting_changed(self, key: str, value):
        if key in ('history_duration', 'update_interval'):
            self._apply_history_length()

    def _apply_history_length(self):
        """Resize the realtime chart buffer based on the History Length setting"""
        from systemmonitor.config import settings, AppConfig
        points, stride = AppConfig.history_window(
            settings.get('history_duration', 300),
            settings.get('update_interval', 500))
        if hasattr(self, '_chart') and self._chart is not None:
            self._chart.set_max_points(points)
            self._chart.set_sample_stride(stride)

    def on_scale_changed(self, _):
        pass  # gauges repaint themselves

    def retranslate_ui(self):
        if hasattr(self, '_chart_title_lbl'):
            self._chart_title_lbl.setText(tr("Performance over time"))

    def apply_theme(self):
        if hasattr(self, '_chart_card'):
            self._chart_card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card']};
                    border: none;
                    border-radius: 10px;
                }}
            """)
        if hasattr(self, '_chart_title_lbl'):
            self._chart_title_lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; background: transparent; border: none;")
        for attr in ('_s_clk', '_s_temp', '_s_stat', '_s_vram', '_s_sys'):
            s = getattr(self, attr, None)
            if s is not None:
                s.apply_theme()
        for g in (self._gauge_load, self._gauge_temp, self._gauge_vram,
                  self._gauge_power, self._gauge_fan):
            g.update()
        if hasattr(self, '_chart'):
            self._chart.update()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(S.px(8))

        # --- Målere ---
        self._gauge_load  = GPUGauge("Load",  "%",   warn_threshold=70,  crit_threshold=90,  size=100)
        self._gauge_temp  = GPUGauge("Temp",  "°C",  max_val=110, warn_threshold=70, crit_threshold=90, size=100)
        self._gauge_temp.set_value_formatter(lambda v: format_temperature(v))
        self._gauge_vram  = GPUGauge("VRAM",  "%",   warn_threshold=70,  crit_threshold=90,  size=100)
        self._gauge_power = GPUGauge("Power", "W",   max_val=300, warn_threshold=200, crit_threshold=280, size=100)
        self._gauge_fan   = GPUGauge("Fan",   "%",   warn_threshold=60,  crit_threshold=85,  size=100)

        gauge_row = QWidget()
        gl = QHBoxLayout(gauge_row)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(S.px(6))
        for g in [self._gauge_load, self._gauge_temp, self._gauge_vram,
                  self._gauge_power, self._gauge_fan]:
            gl.addWidget(g, stretch=1)
        root.addWidget(gauge_row)

        # --- Rullbar detaljseksjon ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        dl = QVBoxLayout(inner)
        dl.setContentsMargins(0, 0, S.px(2), 0)
        dl.setSpacing(S.px(8))

        # Klokker
        self._s_clk = SectionCard("CLOCK SPEEDS", "ph.clock")
        self._r_core     = self._s_clk.add_row("core",     "Core (GPU):")
        self._r_core_max = self._s_clk.add_row("core_max", "Core Max:")
        self._r_mem      = self._s_clk.add_row("mem",      "Memory:")
        self._r_mem_max  = self._s_clk.add_row("mem_max",  "Memory Max:")
        dl.addWidget(self._s_clk)

        # Temperatur
        self._s_temp = SectionCard("TEMPERATURE", "ph.thermometer")
        self._r_t_edge = self._s_temp.add_row("edge",    "Edge (GPU):")
        self._r_t_hot  = self._s_temp.add_row("hotspot", "Hotspot:")
        self._r_t_mem  = self._s_temp.add_row("t_mem",   "Memory:")
        dl.addWidget(self._s_temp)

        # Status
        self._s_stat = SectionCard("STATUS", "ph.activity")
        self._r_load     = self._s_stat.add_row("load",    "GPU Usage:")
        self._r_mem_use  = self._s_stat.add_row("mem_use", "Memory Usage:")
        self._r_fan      = self._s_stat.add_row("fan",     "Fan:")
        self._r_power    = self._s_stat.add_row("power",   "Power:")
        self._r_volt     = self._s_stat.add_row("volt",    "GFX Voltage:")
        dl.addWidget(self._s_stat)

        # VRAM
        self._s_vram = SectionCard("VIDEO MEMORY", "ph.database")
        self._r_v_used  = self._s_vram.add_row("used",  "Used:")
        self._r_v_total = self._s_vram.add_row("total", "Total:")
        self._r_v_free  = self._s_vram.add_row("free",  "Free:")
        dl.addWidget(self._s_vram)

        # System
        self._s_sys = SectionCard("SYSTEM INFORMATION", "ph.info")
        self._r_pcie   = self._s_sys.add_row("pcie",   "PCIe:")
        self._r_driver = self._s_sys.add_row("driver", "Driver:")
        self._r_type   = self._s_sys.add_row("type",   "Type:")
        self._r_vendor = self._s_sys.add_row("vendor", "Vendor:")
        dl.addWidget(self._s_sys)

        # Ytelseskart
        chart_card = QFrame()
        self._chart_card = chart_card
        chart_card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 10px;
            }}
        """)
        cl = QVBoxLayout(chart_card)
        cl.setContentsMargins(S.px(10), S.px(8), S.px(10), S.px(8))
        cl.setSpacing(S.px(4))
        ct = QLabel(tr("Performance over time"))
        self._chart_title_lbl = ct
        ct.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        ct.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; border: none;")
        cl.addWidget(ct)
        self._chart = RealtimeGraph()
        cl.addWidget(self._chart)
        dl.addWidget(chart_card)

        dl.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    def update_gpu(self, gpu: dict):
        """Oppdater alle widgets med GPU-data fra GPUInfo.to_dict()."""
        load      = _flt(gpu, 'gpu_utilization_percent',  0.0)
        mem_use   = _flt(gpu, 'memory_utilization_percent', 0.0)
        temp_edge = _flt(gpu, 'temperature_celsius')
        temp_hot  = _flt(gpu, 'hotspot_temp_celsius')
        temp_mem  = _flt(gpu, 'memory_temp_celsius')
        core_mhz  = _flt(gpu, 'core_clock_mhz')
        core_max  = _flt(gpu, 'core_clock_boost_mhz')
        mem_mhz   = _flt(gpu, 'memory_clock_mhz')
        mem_max   = _flt(gpu, 'core_clock_base_mhz')  # may be 0
        vram_tot  = _flt(gpu, 'vram_total_mb',  0.0)
        vram_used = _flt(gpu, 'vram_used_mb',   0.0)
        vram_free = _flt(gpu, 'vram_free_mb',   0.0)
        vram_pct  = _flt(gpu, 'vram_percent',   0.0)
        power     = _flt(gpu, 'power_draw_watts')
        power_lim = _flt(gpu, 'power_limit_watts')
        fan_pct   = _flt(gpu, 'fan_speed_percent')
        fan_rpm   = _flt(gpu, 'fan_speed_rpm')
        pci_str   = gpu.get('pci_bus', '') or ''
        driver    = gpu.get('driver_version', 'Unknown') or 'Unknown'
        gpu_type  = gpu.get('gpu_type', 'Unknown') or 'Unknown'
        vendor    = gpu.get('vendor', 'Unknown') or 'Unknown'
        raw       = gpu.get('raw_data') or {}
        gfx_mv    = raw.get('gfx_mv')

        # --- Gauges ---
        self._gauge_load.set_value(load or 0)
        self._gauge_temp.set_value(temp_edge or 0)

        if not vram_pct and vram_tot > 0:
            vram_pct = (vram_used / vram_tot) * 100.0
        self._gauge_vram.set_value(vram_pct or 0)
        self._gauge_vram.set_max_value(vram_tot if vram_tot >= 1024 else vram_tot)

        if power_lim and power_lim > 0:
            self._gauge_power.set_max_value(power_lim)
        self._gauge_power.set_value(power or 0)

        self._gauge_fan.set_value(fan_pct or 0)
        self._gauge_fan.setVisible(fan_pct is not None or fan_rpm is not None)

        # --- Klokker ---
        has_core = core_mhz is not None and core_mhz > 0
        has_mem  = mem_mhz  is not None and mem_mhz  > 0
        self._s_clk.setVisible(has_core or has_mem)
        if has_core or has_mem:
            self._s_clk.set_value("core",     _fmt(core_mhz) if has_core else "N/A", "MHz")
            self._s_clk.show_row("core_max",  bool(core_max and core_max > 0))
            if core_max and core_max > 0:
                self._s_clk.set_value("core_max", _fmt(core_max), "MHz")
            self._s_clk.set_value("mem",      _fmt(mem_mhz)  if has_mem  else "N/A", "MHz")
            self._s_clk.show_row("mem_max",   False)

        # --- Temperatur ---
        has_temp = any(t is not None for t in [temp_edge, temp_hot, temp_mem])
        self._s_temp.setVisible(has_temp)
        if has_temp:
            edge_val, edge_unit = format_temperature_parts(temp_edge)
            self._s_temp.set_value("edge", edge_val, edge_unit)
            self._s_temp.show_row("hotspot",  temp_hot is not None)
            if temp_hot is not None:
                hot_val, hot_unit = format_temperature_parts(temp_hot)
                self._s_temp.set_value("hotspot", hot_val, hot_unit)
            self._s_temp.show_row("t_mem",    temp_mem is not None)
            if temp_mem is not None:
                mem_val, mem_unit = format_temperature_parts(temp_mem)
                self._s_temp.set_value("t_mem", mem_val, mem_unit)

        # --- Status ---
        self._s_stat.set_value("load",    _fmt(load),    "%")
        self._s_stat.set_value("mem_use", _fmt(mem_use), "%")

        has_fan = fan_pct is not None or fan_rpm is not None
        self._s_stat.show_row("fan", has_fan)
        if has_fan:
            if fan_rpm is not None and fan_rpm > 0:
                fan_str = f"{fan_rpm:.0f}"
                fan_unit = f"RPM  ({_fmt(fan_pct)}%)" if fan_pct is not None else "RPM"
            else:
                fan_str  = _fmt(fan_pct)
                fan_unit = "%"
            self._s_stat.set_value("fan", fan_str, fan_unit)

        has_pwr = power is not None
        self._s_stat.show_row("power", has_pwr)
        if has_pwr:
            if power_lim and power_lim > 0:
                self._s_stat.set_value("power", f"{power:.0f} / {power_lim:.0f}", "W")
            else:
                self._s_stat.set_value("power", _fmt(power), "W")

        has_volt = gfx_mv is not None and gfx_mv != 0
        self._s_stat.show_row("volt", has_volt)
        if has_volt:
            self._s_stat.set_value("volt", _fmt(gfx_mv), "mV")

        # --- VRAM ---
        has_vram = vram_tot is not None and vram_tot > 0
        self._s_vram.setVisible(has_vram)
        if has_vram:
            def mb_gb(mb):
                return f"{mb:.0f} MB  ({mb/1024:.1f} GB)"
            self._s_vram.set_value("used",  mb_gb(vram_used))
            self._s_vram.set_value("total", mb_gb(vram_tot))
            self._s_vram.show_row("free", vram_free > 0)
            if vram_free > 0:
                self._s_vram.set_value("free", mb_gb(vram_free))

        # --- System ---
        self._s_sys.show_row("pcie", bool(pci_str))
        if pci_str:
            self._s_sys.set_value("pcie", pci_str)
        self._s_sys.set_value("driver", driver if driver != "Unknown" else "N/A")
        self._s_sys.set_value("type",   self._type_label(gpu_type, gpu.get('name', '')))
        self._s_sys.set_value("vendor", vendor)

        # --- Kart ---
        self._chart.push(load or 0, temp_edge or 0)

    @staticmethod
    def _type_label(gpu_type: str, name: str) -> str:
        name_l = (name or '').lower()
        if gpu_type.lower() == 'integrated':
            return tr("Integrated (iGPU)")
        if any(x in name_l for x in ('laptop', 'mobile', 'max-q', ' m ')):
            return tr("Mobile (dGPU)")
        if gpu_type.lower() == 'dedicated':
            return tr("Desktop (dGPU)")
        return gpu_type or tr("Unknown")


# ---------------------------------------------------------------------------
# GPUInfoView – driverinfo-visning for integrerte/sekundære GPUer
# ---------------------------------------------------------------------------
class GPUInfoView(QWidget, I18nMixin):
    """Minimal driver and system info view for integrated/secondary GPUs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n_connect()
        self._build()

    def retranslate_ui(self):
        pass  # SectionCard/InfoRow children retranslate themselves

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(S.px(8))

        self._s_drv = SectionCard("DRIVER & SYSTEM INFORMATION", "ph.gear")
        self._r_driver = self._s_drv.add_row("driver", "Driver Version:")
        self._r_drv_dt = self._s_drv.add_row("drv_dt", "Driver Date:")
        self._r_type   = self._s_drv.add_row("type",   "Type:")
        self._r_vendor = self._s_drv.add_row("vendor", "Vendor:")
        self._r_pcie   = self._s_drv.add_row("pcie",   "PCIe:")
        root.addWidget(self._s_drv)

        self._s_hw = SectionCard("HARDWARE", "ph.cpu")
        self._r_arch  = self._s_hw.add_row("arch",  "Architecture:")
        self._r_vram  = self._s_hw.add_row("vram",  "VRAM:")
        self._r_mem_t = self._s_hw.add_row("mem_t", "Memory Type:")
        self._r_dx    = self._s_hw.add_row("dx",    "DirectX:")
        self._r_vk    = self._s_hw.add_row("vk",    "Vulkan:")
        root.addWidget(self._s_hw)

        root.addStretch()

    def apply_theme(self):
        for attr in ('_s_drv', '_s_hw'):
            s = getattr(self, attr, None)
            if s is not None:
                s.apply_theme()

    def update_gpu(self, gpu: dict):
        driver   = gpu.get('driver_version', '') or ''
        drv_dt   = gpu.get('driver_date', '') or ''
        gpu_type = gpu.get('gpu_type', 'Unknown') or 'Unknown'
        vendor   = gpu.get('vendor', 'Unknown') or 'Unknown'
        pci_str  = gpu.get('pci_bus', '') or ''
        arch     = gpu.get('architecture', '') or ''
        vram_tot = _flt(gpu, 'vram_total_mb')
        mem_type = gpu.get('memory_type', '') or ''
        dx_ver   = gpu.get('directx_version', '') or ''
        vk       = gpu.get('vulkan_support', False)

        self._s_drv.set_value("driver", driver if driver and driver != "Unknown" else "N/A")
        self._s_drv.show_row("drv_dt", bool(drv_dt and drv_dt != "Unknown"))
        if drv_dt and drv_dt != "Unknown":
            self._s_drv.set_value("drv_dt", drv_dt)
        self._s_drv.set_value("type", GPUSingleView._type_label(gpu_type, gpu.get('name', '')))
        self._s_drv.set_value("vendor", vendor if vendor != "Unknown" else "N/A")
        self._s_drv.show_row("pcie", bool(pci_str))
        if pci_str:
            self._s_drv.set_value("pcie", pci_str)

        self._s_hw.show_row("arch", bool(arch))
        if arch:
            self._s_hw.set_value("arch", arch)

        has_vram = vram_tot is not None and vram_tot > 0
        self._s_hw.show_row("vram", has_vram)
        if has_vram:
            self._s_hw.set_value("vram", f"{vram_tot:.0f} MB  ({vram_tot / 1024:.1f} GB)")

        self._s_hw.show_row("mem_t", bool(mem_type))
        if mem_type:
            self._s_hw.set_value("mem_t", mem_type)

        has_dx = bool(dx_ver) and dx_ver != "Unknown"
        self._s_hw.show_row("dx", has_dx)
        if has_dx:
            self._s_hw.set_value("dx", dx_ver)

        self._s_hw.show_row("vk", bool(vk))
        if vk:
            self._s_hw.set_value("vk", tr("Supported"))

        hw_visible = any([arch, has_vram, mem_type, has_dx, vk])
        self._s_hw.setVisible(hw_visible)
