"""
GPU View - Rik GPU-overvåking med klokker, temperaturer og sanntidsdata.
Støtter NVIDIA, AMD, Intel. Faner per GPU. Bærbar/integrert GPU-bevisst.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient

from styles.theme import theme_manager
from scaler import S, ScaleMixin


# ---------------------------------------------------------------------------
# Fargepalett
# ---------------------------------------------------------------------------
COLORS: Dict[str, str] = {
    'bg_primary':    '#0a0e14',
    'bg_card':       '#161f2a',
    'bg_deeper':     '#0d1117',
    'bg_hover':      '#1e2936',
    'border':        '#2a3441',
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
        COLORS.update({
            'bg_primary':    c.BG_PRIMARY,
            'bg_card':       c.BG_CARD,
            'bg_deeper':     c.BG_HOVER,
            'bg_hover':      c.BG_HOVER,
            'border':        c.BORDER,
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
class GPUGauge(QFrame, ScaleMixin):
    def __init__(self, title: str = "", unit: str = "%",
                 min_val: float = 0.0, max_val: float = 100.0,
                 warn_threshold: float = 70.0, crit_threshold: float = 90.0,
                 size: int = 110, parent=None):
        super().__init__(parent)
        self._title        = title
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

        self.setMinimumSize(S.px(size), S.px(size))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent; border: none;")

        self._draw_timer = QTimer(self)
        self._draw_timer.setSingleShot(True)
        self._draw_timer.timeout.connect(self._do_draw)

        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._step_glow)

        self.scale_connect()

    def on_scale_changed(self, _): self.update()

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
        painter.setPen(QPen(QColor(COLORS['border']), pw))
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
        self._pending = False
        self.scale_connect()
        self.setMinimumHeight(S.px(130))

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_draw)

    def _do_draw(self):
        self._pending = False
        self.update()

    def push(self, load: float, temp: float):
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

        painter.setBrush(QColor(COLORS['bg_card']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        painter.setPen(QPen(QColor(COLORS['border']), 1, Qt.PenStyle.DotLine))
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

            # Temp line (normalised to 0-110°C → 0-100%)
            pts_temp = [(i * step, h - (min(v, 110) / 110.0 * h))
                        for i, v in enumerate(self._temp)]
            painter.setPen(QPen(QColor(COLORS['accent_blue']), 2))
            for i in range(len(pts_temp) - 1):
                painter.drawLine(int(pts_temp[i][0]), int(pts_temp[i][1]),
                                 int(pts_temp[i+1][0]), int(pts_temp[i+1][1]))

        painter.setFont(QFont("Segoe UI", S.font_pt(8)))
        painter.setPen(QColor(COLORS['accent_green']))
        painter.drawText(S.px(10), S.px(14), "● Last")
        painter.setPen(QColor(COLORS['accent_blue']))
        painter.drawText(S.px(70), S.px(14), "● Temp")
        painter.end()


# ---------------------------------------------------------------------------
# InfoRow – en nøkkel/verdi-rad
# ---------------------------------------------------------------------------
class InfoRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, S.px(1), 0, S.px(1))
        layout.setSpacing(0)

        self._key = QLabel(label)
        self._key.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._key.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent;")
        self._key.setFixedWidth(S.px(140))
        layout.addWidget(self._key)

        layout.addStretch()

        self._val = QLabel("—")
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


# ---------------------------------------------------------------------------
# SectionCard – kortbeholder med tittel og rader
# ---------------------------------------------------------------------------
class SectionCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
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

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['accent_green']}; background: transparent; border: none;")
        outer.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none; max-height: 1px;")
        sep.setMaximumHeight(1)
        outer.addWidget(sep)

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


# ---------------------------------------------------------------------------
# GPUSingleView – komplett visning for én GPU
# ---------------------------------------------------------------------------
class GPUSingleView(QWidget, ScaleMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self._build()

    def on_scale_changed(self, _):
        pass  # gauges repaint themselves

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(S.px(8))

        # --- Målere ---
        self._gauge_load  = GPUGauge("Load",  "%",   warn_threshold=70,  crit_threshold=90,  size=100)
        self._gauge_temp  = GPUGauge("Temp",  "°C",  max_val=110, warn_threshold=70, crit_threshold=90, size=100)
        self._gauge_vram  = GPUGauge("VRAM",  "%",   warn_threshold=70,  crit_threshold=90,  size=100)
        self._gauge_power = GPUGauge("Power", "W",   max_val=300, warn_threshold=200, crit_threshold=280, size=100)
        self._gauge_fan   = GPUGauge("Vifte", "%",   warn_threshold=60,  crit_threshold=85,  size=100)

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
        self._s_clk = SectionCard("KLOKKEFREKVENSER")
        self._r_core     = self._s_clk.add_row("core",     "Core (GPU):")
        self._r_core_max = self._s_clk.add_row("core_max", "Core Maks:")
        self._r_mem      = self._s_clk.add_row("mem",      "Memory:")
        self._r_mem_max  = self._s_clk.add_row("mem_max",  "Memory Maks:")
        dl.addWidget(self._s_clk)

        # Temperatur
        self._s_temp = SectionCard("TEMPERATUR")
        self._r_t_edge = self._s_temp.add_row("edge",    "Edge (GPU):")
        self._r_t_hot  = self._s_temp.add_row("hotspot", "Hotspot:")
        self._r_t_mem  = self._s_temp.add_row("t_mem",   "Minne:")
        dl.addWidget(self._s_temp)

        # Status
        self._s_stat = SectionCard("STATUS")
        self._r_load     = self._s_stat.add_row("load",    "GPU Bruk:")
        self._r_mem_use  = self._s_stat.add_row("mem_use", "Minne Bruk:")
        self._r_fan      = self._s_stat.add_row("fan",     "Vifte:")
        self._r_power    = self._s_stat.add_row("power",   "Strøm:")
        self._r_volt     = self._s_stat.add_row("volt",    "GFX Spenning:")
        dl.addWidget(self._s_stat)

        # VRAM
        self._s_vram = SectionCard("VIDEOMINNE")
        self._r_v_used  = self._s_vram.add_row("used",  "Brukt:")
        self._r_v_total = self._s_vram.add_row("total", "Totalt:")
        self._r_v_free  = self._s_vram.add_row("free",  "Ledig:")
        dl.addWidget(self._s_vram)

        # System
        self._s_sys = SectionCard("SYSTEMINFORMASJON")
        self._r_pcie   = self._s_sys.add_row("pcie",   "PCIe:")
        self._r_driver = self._s_sys.add_row("driver", "Driver:")
        self._r_type   = self._s_sys.add_row("type",   "Type:")
        self._r_vendor = self._s_sys.add_row("vendor", "Leverandør:")
        dl.addWidget(self._s_sys)

        # Ytelseskart
        chart_card = QFrame()
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
        ct = QLabel("Ytelse over tid")
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
            self._s_temp.set_value("edge",    _fmt(temp_edge), "°C")
            self._s_temp.show_row("hotspot",  temp_hot is not None)
            if temp_hot is not None:
                self._s_temp.set_value("hotspot", _fmt(temp_hot), "°C")
            self._s_temp.show_row("t_mem",    temp_mem is not None)
            if temp_mem is not None:
                self._s_temp.set_value("t_mem",   _fmt(temp_mem), "°C")

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
            return "Integrated (iGPU)"
        if any(x in name_l for x in ('laptop', 'mobile', 'max-q', ' m ')):
            return "Mobile (dGPU)"
        if gpu_type.lower() == 'dedicated':
            return "Desktop (dGPU)"
        return gpu_type or "Unknown"


# ---------------------------------------------------------------------------
# GPUInfoView – driverinfo-visning for integrerte/sekundære GPUer
# ---------------------------------------------------------------------------
class GPUInfoView(QWidget):
    """Minimal driver and system info view for integrated/secondary GPUs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(S.px(8))

        self._s_drv = SectionCard("DRIVER & SYSTEMINFORMASJON")
        self._r_driver = self._s_drv.add_row("driver", "Driver Version:")
        self._r_drv_dt = self._s_drv.add_row("drv_dt", "Driver Date:")
        self._r_type   = self._s_drv.add_row("type",   "Type:")
        self._r_vendor = self._s_drv.add_row("vendor", "Leverandør:")
        self._r_pcie   = self._s_drv.add_row("pcie",   "PCIe:")
        root.addWidget(self._s_drv)

        self._s_hw = SectionCard("HARDWARE")
        self._r_arch  = self._s_hw.add_row("arch",  "Arkitektur:")
        self._r_vram  = self._s_hw.add_row("vram",  "VRAM:")
        self._r_mem_t = self._s_hw.add_row("mem_t", "Minnetype:")
        self._r_dx    = self._s_hw.add_row("dx",    "DirectX:")
        self._r_vk    = self._s_hw.add_row("vk",    "Vulkan:")
        root.addWidget(self._s_hw)

        root.addStretch()

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
            self._s_hw.set_value("vk", "Støttet")

        hw_visible = any([arch, has_vram, mem_type, has_dx, vk])
        self._s_hw.setVisible(hw_visible)


# ---------------------------------------------------------------------------
# GPUView – hoved-widget med støtte for flere GPUer
# ---------------------------------------------------------------------------
class GPUView(QWidget, ScaleMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpu_views:  List[QWidget] = []
        self._gpu_names:  List[str]           = []
        self._pending_data: Optional[dict]    = None
        self._update_sched = False

        self.scale_connect()
        sync_colors()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _setup_ui(self):
        # Properly tear down existing layout so setLayout() succeeds.
        # Qt6 silently ignores setLayout() when one already exists, which
        # causes newly-created widgets (added to the rejected layout) to have
        # no parent and appear as floating top-level windows.
        old = self.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
            # Transfer the now-empty layout to a throwaway widget so that
            # self.layout() returns None and the new setLayout() call below works.
            _tmp = QWidget()
            _tmp.setLayout(old)
            _tmp.deleteLater()

        self._gpu_views = []
        self._gpu_names = []

        root = QVBoxLayout()
        root.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        root.setSpacing(S.px(10))
        self.setLayout(root)

        # Header
        root.addWidget(self._make_header())

        # Tabs (hidden bar when only 1 GPU)
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(self._tab_css())
        root.addWidget(self._tabs, stretch=1)

        # "Ingen GPU" fallback
        self._no_gpu = QLabel(
            "Ingen GPU funnet.\n"
            "Kontroller at NVIDIA/AMD/Intel-drivere er installert."
        )
        self._no_gpu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_gpu.setFont(QFont("Segoe UI", S.font_pt(11)))
        self._no_gpu.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self._no_gpu.setVisible(False)
        root.addWidget(self._no_gpu)

    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(S.px(52))
        hdr.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border-radius: 10px;
                border: none;
            }}
        """)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(S.px(14), 0, S.px(14), 0)
        hl.setSpacing(S.px(8))

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(
            f"color: {COLORS['accent_green']}; font-size: {S.font_pt(13)}px; background: transparent;"
        )
        hl.addWidget(self._status_dot)

        title = QLabel("GPU Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(14), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        hl.addWidget(title)

        self._gpu_name_lbl = QLabel("—")
        self._gpu_name_lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._gpu_name_lbl.setStyleSheet(
            f"color: {COLORS['accent_cyan']}; background: transparent;"
        )
        hl.addWidget(self._gpu_name_lbl)

        hl.addStretch()

        self._badge = QLabel("")
        self._badge.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        self._badge.setStyleSheet(
            f"color: {COLORS['bg_primary']}; background: {COLORS['accent_blue']}; "
            f"border: none; border-radius: 4px; padding: 1px 6px;"
        )
        self._badge.setVisible(False)
        hl.addWidget(self._badge)

        return hdr

    def _tab_css(self) -> str:
        return f"""
            QTabWidget::pane  {{ border: none; background: transparent; }}
            QTabBar::tab {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
                padding: {S.px(5)}px {S.px(12)}px;
                border-radius: {S.px(6)}px;
                margin-right: {S.px(4)}px;
                font-size: {S.font_pt(9)}px;
                border: none;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['accent_green']};
                color: {COLORS['bg_primary']};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """

    # ------------------------------------------------------------------
    # Dataoppdatering
    # ------------------------------------------------------------------
    def update_data(self, data: dict):
        self._pending_data = data
        if not self._update_sched:
            self._update_sched = True
            QTimer.singleShot(16, self._apply_update)

    def _apply_update(self):
        self._update_sched = False
        data = self._pending_data
        if not data:
            return

        gpu_data = data.get('gpu', {})
        if not gpu_data:
            return

        available = gpu_data.get('available', False)
        if not available:
            self._set_status_bad()
            self._show_no_gpu(True)
            return

        self._set_status_ok()

        # Hent liste over GPU-dicts (GPUInfo.to_dict() format)
        gpus: List[dict] = gpu_data.get('gpus', [])

        # Fallback: flat-format (bakoverkompatibilitet)
        if not gpus:
            gpus = [self._flat_to_dict(gpu_data)]

        if not gpus:
            self._show_no_gpu(True)
            return

        self._show_no_gpu(False)

        # Rebuild tabs hvis GPU-sammensetning endret seg
        names = [g.get('name', f'GPU {i}') for i, g in enumerate(gpus)]
        if names != self._gpu_names:
            self._rebuild_tabs(gpus)
            self._gpu_names = names

        # Oppdater hver GPU-visning
        for gpu, view in zip(gpus, self._gpu_views):
            view.update_gpu(gpu)

        # Oppdater header med aktiv fane
        idx = self._tabs.currentIndex()
        if 0 <= idx < len(gpus):
            gpu = gpus[idx]
            self._gpu_name_lbl.setText(gpu.get('name', '—'))
            self._update_badge(gpu)

    # ------------------------------------------------------------------
    # Hjelper-metoder
    # ------------------------------------------------------------------
    def _rebuild_tabs(self, gpus: List[dict]):
        self._tabs.clear()
        self._gpu_views.clear()
        for i, gpu in enumerate(gpus):
            gpu_type = (gpu.get('gpu_type') or '').lower()
            view: QWidget = GPUInfoView() if gpu_type == 'integrated' else GPUSingleView()
            self._gpu_views.append(view)
            name   = gpu.get('name', f'GPU {i}')
            vendor = (gpu.get('vendor') or '').upper()[:3]
            label  = f"{vendor} {name[:18]}…" if len(name) > 18 else f"{vendor} {name}"
            self._tabs.addTab(view, label.strip())
        # Skjul fanelinjen for enkelt-GPU
        self._tabs.tabBar().setVisible(len(gpus) > 1)

    def _update_badge(self, gpu: dict):
        gpu_type = (gpu.get('gpu_type') or '').lower()
        name     = (gpu.get('name') or '').lower()
        if gpu_type == 'integrated':
            self._badge.setText("iGPU")
            self._badge.setVisible(True)
        elif any(x in name for x in ('laptop', 'mobile', 'max-q')):
            self._badge.setText("Mobile")
            self._badge.setVisible(True)
        else:
            self._badge.setVisible(False)

    @staticmethod
    def _flat_to_dict(d: dict) -> dict:
        """Gjør flat bakover-kompatibelt format om til GPUInfo.to_dict() format."""
        mem_tot  = d.get('memory_total', 0) or 0
        mem_used = d.get('memory_used',  0) or 0
        mem_pct  = d.get('memory_percent') or (
            (mem_used / mem_tot * 100) if mem_tot > 0 else 0
        )
        return {
            'name':                     d.get('name', 'Unknown GPU'),
            'vendor':                   d.get('vendor', 'Unknown'),
            'gpu_type':                 d.get('gpu_type', 'Unknown'),
            'gpu_utilization_percent':  d.get('load', 0) or 0,
            'memory_utilization_percent': mem_pct,
            'temperature_celsius':      d.get('temperature'),
            'hotspot_temp_celsius':     d.get('hotspot_temp'),
            'memory_temp_celsius':      d.get('memory_temp'),
            'core_clock_mhz':           d.get('core_clock_mhz') or 0,
            'core_clock_boost_mhz':     d.get('core_clock_boost_mhz') or 0,
            'memory_clock_mhz':         d.get('memory_clock_mhz') or 0,
            'vram_total_mb':            mem_tot,
            'vram_used_mb':             mem_used,
            'vram_free_mb':             max(0.0, mem_tot - mem_used),
            'vram_percent':             mem_pct,
            'power_draw_watts':         d.get('power'),
            'power_limit_watts':        d.get('power_limit'),
            'fan_speed_percent':        d.get('fan_speed'),
            'fan_speed_rpm':            d.get('fan_speed_rpm'),
            'pci_bus':                  d.get('pci_bus', ''),
            'driver_version':           d.get('driver_version', 'Unknown'),
            'is_available':             True,
            'raw_data':                 {},
        }

    def _show_no_gpu(self, v: bool):
        self._tabs.setVisible(not v)
        self._no_gpu.setVisible(v)

    def _set_status_ok(self):
        self._status_dot.setStyleSheet(
            f"color: {COLORS['accent_green']}; font-size: {S.font_pt(13)}px; background: transparent;"
        )

    def _set_status_bad(self):
        self._status_dot.setStyleSheet(
            f"color: {COLORS['accent_red']}; font-size: {S.font_pt(13)}px; background: transparent;"
        )

    def on_scale_changed(self, _):
        self._setup_ui()

    def _on_theme_changed(self, _):
        sync_colors()
        self._apply_theme()

    def _apply_theme(self):
        """Update colors on existing widgets without rebuilding the layout."""
        if hasattr(self, '_tabs'):
            self._tabs.setStyleSheet(self._tab_css())
        if hasattr(self, '_no_gpu'):
            self._no_gpu.setStyleSheet(
                f"color: {COLORS['text_muted']}; background: transparent;"
            )
        if hasattr(self, '_status_dot'):
            self._status_dot.setStyleSheet(
                f"color: {COLORS['accent_green']}; font-size: {S.font_pt(13)}px; background: transparent;"
            )
        if hasattr(self, '_gpu_name_lbl'):
            self._gpu_name_lbl.setStyleSheet(
                f"color: {COLORS['accent_cyan']}; background: transparent;"
            )
        if hasattr(self, '_badge'):
            self._badge.setStyleSheet(
                f"color: {COLORS['bg_primary']}; background: {COLORS['accent_blue']}; "
                f"border: none; border-radius: 4px; padding: 1px 6px;"
            )
        # Force repaint of all GPU views (gauges and graphs read from COLORS at paint time)
        for view in self._gpu_views:
            view.update()
        # Trigger repaint of this widget
        self.update()
