"""
Reference-design building blocks (Systemmonitor redesign).

Shared presentation-only widgets used by all views:
  Panel, PageHeader, StatusPill, BigGauge, Donut, HBar, RangeTabs, Legend,
  AreaChart, ChartPanel, KV, IconStat.

Styling that can be expressed in QSS lives in styles/theme.py (object names
RefPanel / RefTitle / RefMuted / RefSub / RefValue / RefPill / RefTab) so a
theme switch restyles everything automatically. Custom painted widgets read
theme_manager.colors on every paint.
"""
import math
import time
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QButtonGroup, QSizePolicy, QGridLayout,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSize, QTimer, QEvent
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QPainterPath, QLinearGradient, QBrush,
)
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S
from systemmonitor.i18n import tr
from systemmonitor.utils.ui_tick import ui_tick


_THEME_DEFAULTS = {
    "GAUGE_BG": "rgba(255, 255, 255, 0.08)",
    "CHART_GRID": "rgba(255, 255, 255, 0.06)",
    "TEXT_PRIMARY": "#f5f5f4", "TEXT_SECONDARY": "#a1a1a6", "TEXT_MUTED": "#6b6b72",
}


def _parse_css(v: str) -> QColor:
    """QColor from '#rrggbb' / named colours / 'rgba(r, g, b, a)' (alpha 0-1)."""
    import re as _re
    m = _re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+))?\s*\)', v or '')
    if m:
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return QColor(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(round(a * 255)))
    return QColor(v)


def tc(name: str) -> QColor:
    """Theme colour by attribute name, tolerant of missing attributes and rgba() strings."""
    v = getattr(theme_manager.colors, name, None) or _THEME_DEFAULTS.get(name, "#808080")
    return _parse_css(v)


def col(key_or_hex: str) -> QColor:
    """Resolve a theme colour key (e.g. 'ACCENT_GREEN') or a literal colour."""
    if not key_or_hex:
        return tc('ACCENT_GREEN')
    if key_or_hex.startswith('#') or key_or_hex.startswith('rgb'):
        return _parse_css(key_or_hex)
    return _parse_css(getattr(theme_manager.colors, key_or_hex, theme_manager.colors.ACCENT_GREEN))


def hexcol(key_or_hex: str) -> str:
    return col(key_or_hex).name()


def _label(text: str, obj: str, pt: int = 10, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName(obj)
    f = QFont("Cutive", S.font_pt(pt))
    if bold:
        f.setWeight(QFont.Weight.Bold)
    lbl.setFont(f)
    return lbl


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
class Panel(QFrame):
    """Rounded card with an icon + title header. Add content to ``self.body``."""

    def __init__(self, title: str = "", icon: str = "", parent=None, margins=(12, 10, 12, 10)):
        super().__init__(parent)
        self.setObjectName("RefPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._icon = icon
        outer = QVBoxLayout(self)
        outer.setContentsMargins(S.px(margins[0]), S.px(margins[1]), S.px(margins[2]), S.px(margins[3]))
        outer.setSpacing(S.px(8))

        self.header = QHBoxLayout()
        self.header.setSpacing(S.px(8))
        self._icon_lbl = None
        if icon:
            self._icon_lbl = QLabel()
            self._icon_lbl.setStyleSheet("background: transparent; border: none;")
            self.header.addWidget(self._icon_lbl)
            self._refresh_icon()
        self.title_lbl = _label(title, "RefTitle", 10, True)
        # may shrink (clip) instead of forcing the whole grid wider
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.title_lbl.setMinimumWidth(S.px(40))
        self.header.addWidget(self.title_lbl, 1)
        self._has_header = bool(title or icon)
        if self._has_header:
            outer.addLayout(self.header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(S.px(6))
        outer.addLayout(self.body, stretch=1)
        theme_manager.theme_changed.connect(self._refresh_icon)

    def _refresh_icon(self, *_):
        if self._icon_lbl is None:
            return
        try:
            sz = S.px(16)
            self._icon_lbl.setPixmap(
                qta.icon(self._icon, color=theme_manager.colors.ACCENT_GREEN).pixmap(QSize(sz, sz)))
        except Exception:
            self._icon_lbl.setText("•")

    def set_title(self, text: str):
        self.title_lbl.setText(text)

    def add_header_widget(self, w: QWidget):
        self.header.addWidget(w)


# ---------------------------------------------------------------------------
# Header / pill
# ---------------------------------------------------------------------------
class StatusPill(QLabel):
    """Green outlined pill ('LIVE', 'Sunn', ...). Colour via set_state."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("RefPill")
        self.setProperty("state", "ok")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Cutive", S.font_pt(10), QFont.Weight.Bold))
        self.setMinimumWidth(S.px(88))

    def set_state(self, state: str, text: str | None = None):
        if text is not None:
            self.setText(text)
        if self.property("state") != state:
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)


class PageHeader(QFrame):
    """Icon + page title + subtitle on the left, status pill on the right."""

    def __init__(self, title: str, subtitle: str, icon: str, pill: str = "LIVE", parent=None):
        super().__init__(parent)
        self.setObjectName("RefHeader")
        self._icon = icon
        lay = QHBoxLayout(self)
        lay.setContentsMargins(S.px(4), S.px(2), S.px(4), S.px(2))
        lay.setSpacing(S.px(12))
        self._icon_lbl = QLabel()
        self._icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._icon_lbl)
        col_l = QVBoxLayout()
        col_l.setSpacing(0)
        self.title_lbl = _label(title, "RefTitle", 18, True)
        self.sub_lbl = _label(subtitle, "RefMuted", 9)
        col_l.addWidget(self.title_lbl)
        col_l.addWidget(self.sub_lbl)
        lay.addLayout(col_l)
        lay.addStretch()
        self.extra = QHBoxLayout()
        self.extra.setSpacing(S.px(8))
        lay.addLayout(self.extra)
        self.pill = StatusPill(pill) if pill else None
        if self.pill:
            lay.addWidget(self.pill)
        self._refresh_icon()
        theme_manager.theme_changed.connect(self._refresh_icon)

    def _refresh_icon(self, *_):
        try:
            sz = S.px(30)
            self._icon_lbl.setPixmap(
                qta.icon(self._icon, color=theme_manager.colors.ACCENT_GREEN).pixmap(QSize(sz, sz)))
        except Exception:
            pass

    def set_texts(self, title: str, subtitle: str):
        self.title_lbl.setText(title)
        self.sub_lbl.setText(subtitle)


# ---------------------------------------------------------------------------
# Gauges
# ---------------------------------------------------------------------------
class BigGauge(QWidget):
    """270-degree arc gauge with big centred value, caption and 0/100 end labels."""

    def __init__(self, color: str = "ACCENT_GREEN", caption: str = "", parent=None,
                 show_ends: bool = True, value_pt: int = 22):
        super().__init__(parent)
        self._color = color
        self._pct = 0.0
        self._text = "0 %"
        self._caption = caption
        self._show_ends = show_ends
        self._value_pt = value_pt
        self.setMinimumSize(S.px(110), S.px(110))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_percent(self, pct: float, text: str | None = None, caption: str | None = None):
        pct = max(0.0, min(100.0, float(pct or 0)))
        changed = abs(pct - self._pct) >= 0.2
        self._pct = pct
        new_text = text if text is not None else f"{pct:.0f} %"
        if new_text != self._text:
            self._text = new_text
            changed = True
        if caption is not None and caption != self._caption:
            self._caption = caption
            changed = True
        if changed:
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = theme_manager.colors
        side = min(self.width(), self.height() - (S.px(14) if self._show_ends else 0))
        pw = max(S.px(9), side * 0.09)
        rect = QRectF((self.width() - side) / 2 + pw, (self.height() - (S.px(14) if self._show_ends else 0) - side) / 2 + pw,
                      side - 2 * pw, side - 2 * pw)
        track = QPen(tc('GAUGE_BG'), pw)
        track.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(track)
        p.drawArc(rect, 225 * 16, -270 * 16)
        c = col(self._color)
        if self._pct > 0:
            glow = QColor(c); glow.setAlpha(45)
            gp = QPen(glow, pw + S.px(6)); gp.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(gp)
            span = int(-270 * 16 * self._pct / 100.0)
            p.drawArc(rect, 225 * 16, span)
            fp = QPen(c, pw); fp.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(fp)
            p.drawArc(rect, 225 * 16, span)
        # centre value
        cx, cy = rect.center().x(), rect.center().y()
        p.setPen(tc('TEXT_PRIMARY'))
        p.setFont(QFont("Cutive", S.font_pt(self._value_pt), QFont.Weight.Bold))
        vr = QRectF(rect.left(), cy - rect.height() * 0.26, rect.width(), rect.height() * 0.36)
        p.drawText(vr, Qt.AlignmentFlag.AlignCenter, self._text)
        if self._caption:
            p.setPen(tc('TEXT_SECONDARY'))
            p.setFont(QFont("Cutive", S.font_pt(9)))
            cr = QRectF(rect.left(), cy + rect.height() * 0.08, rect.width(), rect.height() * 0.2)
            p.drawText(cr, Qt.AlignmentFlag.AlignCenter, self._caption)
        if self._show_ends:
            p.setPen(tc('TEXT_MUTED'))
            p.setFont(QFont("Cutive", S.font_pt(8)))
            y = rect.bottom() + pw * 0.6
            p.drawText(QRectF(rect.left() - pw, y, rect.width() * 0.5, S.px(14)),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "0 %")
            p.drawText(QRectF(rect.center().x(), y, rect.width() * 0.5 + pw, S.px(14)),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, "100 %")
        p.end()


class Donut(QWidget):
    """Full ring. ``segments`` = [(pct, colorKey), ...] stacked from 12 o'clock."""

    def __init__(self, parent=None, value_pt: int = 15, sub_pt: int = 9):
        super().__init__(parent)
        self._segments = []
        self._line1 = ""
        self._line2 = ""
        self._value_pt = value_pt
        self._sub_pt = sub_pt
        self.setMinimumSize(S.px(100), S.px(100))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_data(self, segments, line1: str = "", line2: str = ""):
        segments = [(round(float(a or 0), 1), k) for a, k in segments]
        if segments != self._segments or line1 != self._line1 or line2 != self._line2:
            self._segments, self._line1, self._line2 = segments, line1, line2
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = theme_manager.colors
        side = min(self.width(), self.height())
        pw = max(S.px(10), side * 0.11)
        rect = QRectF((self.width() - side) / 2 + pw, (self.height() - side) / 2 + pw, side - 2 * pw, side - 2 * pw)
        p.setPen(QPen(tc('GAUGE_BG'), pw))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)
        start = 90 * 16
        for pct, key in self._segments:
            if pct <= 0:
                continue
            pen = QPen(col(key), pw)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            span = int(-360 * 16 * min(pct, 100.0) / 100.0)
            p.drawArc(rect, start, span)
            start += span
        cx, cy = rect.center().x(), rect.center().y()
        p.setPen(tc('TEXT_PRIMARY'))
        p.setFont(QFont("Cutive", S.font_pt(self._value_pt), QFont.Weight.Bold))
        p.drawText(QRectF(rect.left(), cy - rect.height() * 0.28, rect.width(), rect.height() * 0.30),
                   Qt.AlignmentFlag.AlignCenter, self._line1)
        if self._line2:
            p.setPen(tc('TEXT_SECONDARY'))
            p.setFont(QFont("Cutive", S.font_pt(self._sub_pt)))
            p.drawText(QRectF(rect.left(), cy + rect.height() * 0.02, rect.width(), rect.height() * 0.24),
                       Qt.AlignmentFlag.AlignCenter, self._line2)
        p.end()


class HBar(QWidget):
    """Thin rounded horizontal bar (0-100)."""

    def __init__(self, color: str = "ACCENT_GREEN", height: int = 7, parent=None):
        super().__init__(parent)
        self._color = color
        self._pct = 0.0
        self.setFixedHeight(S.px(height))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, pct: float, color: str | None = None):
        pct = max(0.0, min(100.0, float(pct or 0)))
        if color:
            self._color = color
        if abs(pct - self._pct) >= 0.2 or color:
            self._pct = pct
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tc('GAUGE_BG'))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), r, r)
        if self._pct > 0:
            p.setBrush(col(self._color))
            w = max(self.height(), self.width() * self._pct / 100.0)
            p.drawRoundedRect(QRectF(0, 0, w, self.height()), r, r)
        p.end()


# ---------------------------------------------------------------------------
# Small content helpers
# ---------------------------------------------------------------------------
class KV(QWidget):
    """Muted label on the left, bold value on the right."""

    def __init__(self, label: str, value: str = "--", parent=None, value_color: str | None = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, S.px(2), 0, S.px(2))
        lay.setSpacing(S.px(8))
        self.key_lbl = _label(label, "RefSub", 9)
        self.val_lbl = _label(value, "RefValue", 9, True)
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if value_color:
            self.val_lbl.setStyleSheet(f"color: {hexcol(value_color)};")
        lay.addWidget(self.key_lbl)
        lay.addStretch()
        lay.addWidget(self.val_lbl)

    def set_value(self, text: str):
        self.val_lbl.setText(text)

    def set_label(self, text: str):
        self.key_lbl.setText(text)


class IconStat(QWidget):
    """Icon + value (+ caption below), used in the side column of gauge panels."""

    def __init__(self, icon: str, value: str = "--", caption: str = "", parent=None):
        super().__init__(parent)
        self._icon = icon
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(S.px(8))
        self._ico = QLabel()
        self._ico.setStyleSheet("background: transparent; border: none;")
        self._ico.setFixedWidth(S.px(22))
        lay.addWidget(self._ico)
        c = QVBoxLayout()
        c.setSpacing(0)
        self.val_lbl = _label(value, "RefValue", 11, True)
        self.cap_lbl = _label(caption, "RefMuted", 8)
        c.addWidget(self.val_lbl)
        c.addWidget(self.cap_lbl)
        lay.addLayout(c)
        lay.addStretch()
        self._refresh_icon()
        theme_manager.theme_changed.connect(self._refresh_icon)

    def _refresh_icon(self, *_):
        try:
            sz = S.px(18)
            self._ico.setPixmap(qta.icon(self._icon, color=theme_manager.colors.ACCENT_GREEN).pixmap(QSize(sz, sz)))
        except Exception:
            pass

    def set_value(self, value: str, caption: str | None = None):
        self.val_lbl.setText(value)
        if caption is not None:
            self.cap_lbl.setText(caption)


class Legend(QWidget):
    """Row of coloured squares with captions."""

    def __init__(self, items, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(S.px(10))
        self._items = []
        for key, text in items:
            dot = QLabel()
            dot.setFixedSize(S.px(9), S.px(9))
            lbl = _label(text, "RefSub", 8)
            lay.addWidget(dot)
            lay.addWidget(lbl)
            self._items.append((dot, key))
        self._restyle()
        theme_manager.theme_changed.connect(self._restyle)

    def _restyle(self, *_):
        for dot, key in self._items:
            dot.setStyleSheet(f"background-color: {hexcol(key)}; border: none; border-radius: 2px;")


# ---------------------------------------------------------------------------
# Range tabs + area chart
# ---------------------------------------------------------------------------
RANGES = [(60, "1 min"), (300, "5 min"), (900, "15 min"), (3600, "1 hour"), (21600, "6 hours")]


def default_range_seconds() -> int:
    """Closest tab to the user's 'History Length' setting."""
    try:
        from systemmonitor.config import settings
        want = float(settings.get('history_duration', 300))
    except Exception:
        want = 300
    return min(RANGES, key=lambda r: abs(r[0] - want))[0]


class RangeTabs(QWidget):
    range_changed = pyqtSignal(int)

    def __init__(self, parent=None, current: int | None = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(S.px(4))
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        current = current or default_range_seconds()
        for secs, text in RANGES:
            b = QPushButton(tr(text))
            b.setObjectName("RefTab")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFont(QFont("Cutive", S.font_pt(8)))
            b.setChecked(secs == current)
            b.clicked.connect(lambda _=False, s=secs: self.range_changed.emit(s))
            self._group.addButton(b)
            lay.addWidget(b)

    def set_range(self, secs: int):
        for b, (s, _t) in zip(self._group.buttons(), RANGES):
            b.setChecked(s == secs)


def _nice_max(v: float) -> float:
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    f = v / (10 ** exp)
    for n in (1, 2, 2.5, 5, 10):
        if f <= n:
            return n * (10 ** exp)
    return 10 * (10 ** exp)


class AreaChart(QWidget):
    """Time-series area chart: gridlines, y/x labels, filled gradient series.

    push(v1, v2, ...) appends one sample (timestamped). The visible window is
    set with set_window(seconds). y_max=None -> auto scale.
    """

    def __init__(self, series, y_max: float | None = 100.0, y_fmt=None, parent=None,
                 y_suffix: str = " %", min_auto: float = 1.0, store: deque | None = None,
                 compact: bool = False):
        super().__init__(parent)
        self._series = list(series)
        self._y_max_fixed = y_max
        self._compact = compact
        self._y_fmt = y_fmt or (lambda v: f"{v:.0f}{y_suffix}")
        self._min_auto = min_auto
        # ``store`` lets a view keep history across a UI rebuild (theme/scale/language)
        self._data = store if store is not None else deque(maxlen=60000)
        self._window = default_range_seconds()
        self._dirty = True
        self._overlay = ""
        self._overlay_sub = ""
        self.setMinimumHeight(S.px(90))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ui_tick.tick.connect(self._on_tick)

    # --- data ---
    def push(self, *vals):
        now = time.time()
        if self._data and now - self._data[-1][0] < 0.15:
            self._data[-1] = (self._data[-1][0], tuple(float(v or 0) for v in vals))
        else:
            self._data.append((now, tuple(float(v or 0) for v in vals)))
        self._dirty = True

    def set_window(self, seconds: int):
        self._window = int(seconds)
        self._dirty = True
        self.update()

    def set_overlay(self, text: str, sub: str = ""):
        if text != self._overlay or sub != self._overlay_sub:
            self._overlay, self._overlay_sub = text, sub
            self._dirty = True

    def clear(self):
        self._data.clear()
        self._dirty = True

    def _on_tick(self):
        if self._dirty and self.isVisible():
            self._dirty = False
            self.update()

    # --- painting ---
    _XTICKS = {60: 4, 300: 5, 900: 5, 3600: 6, 21600: 6}

    def _x_label(self, frac_from_right: float) -> str:
        if frac_from_right <= 0:
            return tr("now")
        secs = frac_from_right * self._window
        if self._window <= 90:
            return f"-{secs:.0f} s"
        if self._window <= 5400:
            return f"-{secs / 60:g} min"
        return f"-{secs / 3600:g} t"

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = theme_manager.colors
        w, h = self.width(), self.height()
        lm, rm, tm, bm = S.px(46), S.px(8), S.px(6), S.px(20)
        if self._compact:
            lm, rm, tm, bm = S.px(2), S.px(2), S.px(3), S.px(3)
        p.setFont(QFont("Cutive", S.font_pt(8)))
        gx, gy, gw, gh = lm, tm, w - lm - rm, h - tm - bm
        if gw < 20 or gh < 20:
            p.end()
            return
        now = time.time()
        t0 = now - self._window
        nb = max(2, int(gw / 2))
        nseries = len(self._series)
        sums = [[0.0] * nb for _ in range(nseries)]
        cnts = [0] * nb
        for t, vals in reversed(self._data):
            if t < t0:
                break
            i = min(nb - 1, int((t - t0) / self._window * nb))
            cnts[i] += 1
            for s in range(min(nseries, len(vals))):
                sums[s][i] += vals[s]
        pts = [[None if cnts[i] == 0 else sums[s][i] / cnts[i] for i in range(nb)] for s in range(nseries)]

        if self._y_max_fixed is not None:
            ymax = self._y_max_fixed
        else:
            peak = max([v for ser in pts for v in ser if v is not None] or [self._min_auto])
            ymax = _nice_max(max(peak * 1.1, self._min_auto))

        # widen the left margin to fit the longest y label, then re-derive the plot rect
        need = p.fontMetrics().horizontalAdvance(self._y_fmt(ymax)) + S.px(12)
        if need > lm and not self._compact:
            lm = need
            gx, gw = lm, w - lm - rm
        grid = tc('CHART_GRID')
        divs = 4
        for i in range(divs + 1):
            y = gy + gh - gh * i / divs
            p.setPen(QPen(grid, 1))
            p.drawLine(QPointF(gx, y), QPointF(gx + gw, y))
            if not self._compact:
                p.setPen(tc('TEXT_MUTED'))
                p.drawText(QRectF(0, y - S.px(8), lm - S.px(6), S.px(16)),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._y_fmt(ymax * i / divs))
        # x labels
        p.setPen(tc('TEXT_MUTED'))
        nt = self._XTICKS.get(self._window, 4)
        for i in range(0 if self._compact else nt + 1) if False else (range(nt + 1) if not self._compact else range(0)):
            frac = 1 - i / nt
            x = gx + gw * i / nt
            txt = self._x_label(frac if i < nt else 0)
            al = Qt.AlignmentFlag.AlignHCenter
            rx = x - S.px(30)
            if i == 0:
                rx, al = x, Qt.AlignmentFlag.AlignLeft
            elif i == nt:
                rx, al = x - S.px(60), Qt.AlignmentFlag.AlignRight
            p.drawText(QRectF(rx, gy + gh + S.px(3), S.px(60), S.px(14)), al | Qt.AlignmentFlag.AlignTop, txt)

        # series
        p.setClipRect(QRectF(gx, gy - 2, gw, gh + 4))
        for s in range(nseries):
            c = col(self._series[s])
            path = QPainterPath()
            started = False
            lastx = firstx = 0.0
            for i, v in enumerate(pts[s]):
                if v is None:
                    continue
                x = gx + gw * (i + 0.5) / nb
                y = gy + gh - gh * min(v / ymax, 1.0) if ymax else gy + gh
                if not started:
                    path.moveTo(x, y)
                    firstx = x
                    started = True
                else:
                    path.lineTo(x, y)
                lastx = x
            if not started:
                continue
            fill = QPainterPath(path)
            fill.lineTo(lastx, gy + gh)
            fill.lineTo(firstx, gy + gh)
            fill.closeSubpath()
            g = QLinearGradient(0, gy, 0, gy + gh)
            top = QColor(c); top.setAlpha(120)
            bot = QColor(c); bot.setAlpha(8)
            g.setColorAt(0, top)
            g.setColorAt(1, bot)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawPath(fill)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(c, max(1.5, S.px(1.6))))
            p.drawPath(path)
        p.setClipping(False)
        if self._overlay:
            p.setPen(tc('TEXT_PRIMARY'))
            p.setFont(QFont("Cutive", S.font_pt(16), QFont.Weight.Bold))
            p.drawText(QRectF(gx, gy, gw, gh * 0.6), Qt.AlignmentFlag.AlignCenter, self._overlay)
            if self._overlay_sub:
                p.setPen(tc('TEXT_SECONDARY'))
                p.setFont(QFont("Cutive", S.font_pt(9)))
                p.drawText(QRectF(gx, gy + gh * 0.38, gw, gh * 0.2), Qt.AlignmentFlag.AlignCenter, self._overlay_sub)
        p.end()


class ChartPanel(Panel):
    """Panel containing an AreaChart, optional legend and range tabs."""

    def __init__(self, title: str, icon: str, chart: AreaChart, tabs: bool = True,
                 legend=None, parent=None):
        super().__init__(title, icon, parent)
        self.chart = chart
        self.setProperty("flex", True)
        self.setProperty("flex_max", 520)
        self.tabs = None
        if tabs:
            self.tabs = RangeTabs(current=chart._window)
            self.tabs.range_changed.connect(chart.set_window)
            self.add_header_widget(self.tabs)
        self.body.addWidget(chart, stretch=1)
        if legend:
            leg_row = QHBoxLayout()
            leg_row.addStretch()
            leg_row.addWidget(Legend(legend))
            self.body.addLayout(leg_row)
        try:
            from systemmonitor.core.signals import signal_bus
            signal_bus.setting_changed.connect(self._on_setting)
        except Exception:
            pass

    def resizeEvent(self, event):
        """Narrow panels: move the range tabs below the title so nothing gets clipped."""
        super().resizeEvent(event)
        if self.tabs is None:
            return
        narrow = self.width() < S.px(540)
        if narrow != getattr(self, '_tabs_below', False):
            self._tabs_below = narrow
            if narrow:
                self.header.removeWidget(self.tabs)
                self.body.insertWidget(0, self.tabs, alignment=Qt.AlignmentFlag.AlignRight)
            else:
                self.body.removeWidget(self.tabs)
                self.header.addWidget(self.tabs)

    def _on_setting(self, key, _value):
        if key == 'history_duration' and self.tabs is not None:
            secs = default_range_seconds()
            self.tabs.set_range(secs)
            self.chart.set_window(secs)


# ---------------------------------------------------------------------------
# Row panels + responsive grid
# ---------------------------------------------------------------------------
class KVPanel(Panel):
    """Panel with id-addressable label/value rows (set_value / show_row)."""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(title, icon, parent)
        self._rows = {}
        self._row_labels = []

    def add_row(self, row_id: str, label: str, value_color: str | None = None) -> KV:
        kv = KV(tr(label), "--", value_color=value_color)
        self.body.addWidget(kv)
        self._rows[row_id] = kv
        self._row_labels.append((kv, label))
        return kv

    def set_value(self, row_id: str, val: str, unit: str = ""):
        kv = self._rows.get(row_id)
        if kv is not None:
            kv.set_value(f"{val} {unit}".strip())

    def show_row(self, row_id: str, visible: bool):
        kv = self._rows.get(row_id)
        if kv is not None:
            kv.setVisible(visible)

    def retranslate(self):
        for kv, label in self._row_labels:
            kv.set_label(tr(label))


class BarRow(QWidget):
    """label | bar | value"""

    def __init__(self, label: str, color: str = "ACCENT_GREEN", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, S.px(2), 0, S.px(2))
        lay.setSpacing(S.px(3))
        top = QHBoxLayout()
        self.key_lbl = _label(label, "RefSub", 9)
        self.val_lbl = _label("--", "RefValue", 9, True)
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.key_lbl)
        top.addStretch()
        top.addWidget(self.val_lbl)
        lay.addLayout(top)
        self.bar = HBar(color, 6)
        lay.addWidget(self.bar)

    def set_data(self, pct: float, text: str):
        self.bar.set_value(pct)
        self.val_lbl.setText(text)


class BarPanel(Panel):
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(title, icon, parent)
        self._rows = {}
        self._row_labels = []

    def add_row(self, row_id: str, label: str, color: str = "ACCENT_GREEN") -> BarRow:
        r = BarRow(tr(label), color)
        self.body.addWidget(r)
        self._rows[row_id] = r
        self._row_labels.append((r, label))
        return r

    def set_row(self, row_id: str, pct: float, text: str):
        r = self._rows.get(row_id)
        if r is not None:
            r.set_data(pct, text)

    def show_row(self, row_id: str, visible: bool):
        r = self._rows.get(row_id)
        if r is not None:
            r.setVisible(visible)

    def retranslate(self):
        for r, label in self._row_labels:
            r.key_lbl.setText(tr(label))


class ReflowGrid(QWidget):
    """Responsive grid: re-flows items into 1..max_cols columns by available width
    and (optionally) lets "flex" panels (charts) grow to use spare viewport height.

    items: list of (widget, colspan). A widget with property ``flex`` = True is
    stretched, up to its ``flex_max`` px, when the page is taller than its content
    (portrait / fullscreen). Call bind_viewport(scroll_area) to enable that.
    """

    def __init__(self, items, max_cols: int = 3, min_col_width: int = 340, parent=None):
        super().__init__(parent)
        self.setObjectName("RefContent")
        self.setStyleSheet("QWidget#RefContent { background: transparent; }")
        self._items = list(items)
        self._max_cols = max_cols
        self._min_col_width = min_col_width
        self._cols = 0
        self._viewport = None
        self._flex_base = {}
        self._fitting = False
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(S.px(10))
        self._arrange(force=True)

    def bind_viewport(self, scroll):
        from PyQt6.QtWidgets import QScrollArea
        self._viewport = scroll.viewport() if isinstance(scroll, QScrollArea) else scroll
        self._viewport.installEventFilter(self)
        QTimer.singleShot(0, self._fit)

    def eventFilter(self, obj, event):
        if obj is self._viewport and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._fit)
        return False

    def _arrange(self, force: bool = False):
        w = self.width() or S.px(self._min_col_width * self._max_cols)
        # a column must be at least as wide as the widest panel really needs
        # (font / DPI dependent), so panels are never clipped on the right
        need = S.px(self._min_col_width)
        for wd, span in self._items:
            if span == 1 and not wd.isHidden():
                need = max(need, wd.minimumSizeHint().width())
        cols = max(1, min(self._max_cols, (w + self._grid.spacing()) // (need + self._grid.spacing())))
        if cols == self._cols and not force:
            return
        self._cols = cols
        while self._grid.count():
            self._grid.takeAt(0)
        r = c = 0
        for widget, span in self._items:
            span = max(1, min(span, cols))
            if c + span > cols:
                r += 1
                c = 0
            self._grid.addWidget(widget, r, c, 1, span)
            c += span
            if c >= cols:
                r += 1
                c = 0
        for i in range(self._max_cols):
            self._grid.setColumnStretch(i, 1 if i < cols else 0)
        QTimer.singleShot(0, self._fit)

    def _fit(self):
        """Distribute spare viewport height over the flex panels (one share per grid row)."""
        if self._viewport is None or self._fitting:
            return
        parent = self.parentWidget()
        if parent is None or parent.layout() is None:
            return
        flex = [wd for wd, _ in self._items if wd.property("flex") and not wd.isHidden()]
        if not flex:
            return
        self._fitting = True
        try:
            for wd in flex:
                base = self._flex_base.setdefault(wd, wd.minimumHeight())
                wd.setMinimumHeight(base)
            parent.layout().activate()
            natural = parent.layout().sizeHint().height()
            extra = self._viewport.height() - natural - S.px(6)
            if extra <= 0:
                return
            rows = {}
            for wd in flex:
                idx = self._grid.indexOf(wd)
                if idx < 0:
                    continue
                rows.setdefault(self._grid.getItemPosition(idx)[0], []).append(wd)
            if not rows:
                return
            share = extra // len(rows)
            for ws in rows.values():
                for wd in ws:
                    cap = S.px(int(wd.property("flex_max") or 520))
                    wd.setMinimumHeight(max(self._flex_base[wd], min(self._flex_base[wd] + share, cap)))
        finally:
            self._fitting = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange()


def flex(panel, max_px: int = 380):
    """Mark a panel as stretchable: it may grow (up to max_px) when the page is
    taller than its content, e.g. portrait or fullscreen windows."""
    panel.setProperty("flex", True)
    panel.setProperty("flex_max", max_px)
    return panel


class SegBar(QWidget):
    """Horizontal stacked bar: segments = [(pct, colorKey), ...] left to right."""

    def __init__(self, height: int = 18, parent=None):
        super().__init__(parent)
        self._segments = []
        self.setFixedHeight(S.px(height))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, segments):
        segments = [(round(float(a or 0), 1), k) for a, k in segments]
        if segments != self._segments:
            self._segments = segments
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.height() / 2
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), r, r)
        p.setClipPath(path)
        p.fillRect(self.rect(), tc('GAUGE_BG'))
        x = 0.0
        for pct, key in self._segments:
            w = self.width() * max(0.0, pct) / 100.0
            if w <= 0:
                continue
            p.fillRect(QRectF(x, 0, w, self.height()), col(key))
            x += w
        p.end()


class DotRow(QWidget):
    """Coloured square + label on the left, value on the right."""

    def __init__(self, color: str, label: str, value: str = "--", parent=None):
        super().__init__(parent)
        self._color = color
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, S.px(2), 0, S.px(2))
        lay.setSpacing(S.px(8))
        self._dot = QLabel()
        self._dot.setFixedSize(S.px(9), S.px(9))
        self.key_lbl = _label(label, "RefSub", 9)
        self.val_lbl = _label(value, "RefValue", 9, True)
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._dot)
        lay.addWidget(self.key_lbl)
        lay.addStretch()
        lay.addWidget(self.val_lbl)
        self._restyle()
        theme_manager.theme_changed.connect(self._restyle)

    def _restyle(self, *_):
        self._dot.setStyleSheet(f"background-color: {hexcol(self._color)}; border: none; border-radius: 2px;")

    def set_value(self, text: str):
        self.val_lbl.setText(text)


class GaugeKpi(Panel):
    """Panel with a wide arc gauge showing a live value + unit and a footer line.
    Auto-scales to the recent peak (``set_value`` takes the numeric text)."""

    def __init__(self, title: str, icon: str, color: str, unit: str = "", parent=None):
        super().__init__(title, icon, parent)
        self._unit = unit
        self._peak = 1.0
        self._fixed_max = None
        self.gauge = BigGauge(color, unit, show_ends=False, value_pt=20)
        self.gauge.setMinimumHeight(S.px(130))
        self.body.addWidget(self.gauge, stretch=1)
        self.sub_lbl = _label("", "RefSub", 9)
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.addWidget(self.sub_lbl)

    def set_unit(self, unit: str):
        self._unit = unit
        self.gauge.set_percent(self.gauge._pct, caption=unit)

    def set_fixed_max(self, max_value):
        """Scale the gauge against a known maximum (e.g. the adapter's link speed);
        None restores peak-based auto scaling."""
        self._fixed_max = float(max_value) if max_value else None

    def set_value(self, value: str, sub: str = ""):
        self.sub_lbl.setText(sub)
        try:
            v = float(value.replace(",", "."))
        except ValueError:
            return
        self._peak = self._fixed_max or max(v, self._peak * 0.995, 1.0)
        self.gauge.set_percent(v / self._peak * 100.0, text=value, caption=self._unit)


class NumKpi(Panel):
    """Panel with a big number and caption (connections, interfaces ...)."""

    def __init__(self, title: str, icon: str, color: str = "ACCENT_CYAN", parent=None):
        super().__init__(title, icon, parent)
        self.val_lbl = _label("--", "RefValue", 30, True)
        self.val_lbl.setStyleSheet(f"color: {hexcol(color)};")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_lbl = _label("", "RefSub", 9)
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.addStretch()
        self.body.addWidget(self.val_lbl)
        self.body.addWidget(self.sub_lbl)
        self.body.addStretch()

    def set_unit(self, _unit: str):
        pass

    def set_value(self, value: str, sub: str = ""):
        self.val_lbl.setText(value)
        self.sub_lbl.setText(sub)


class KpiTile(Panel):
    """Compact KPI tile: icon + label, big value with a unit (storage header row)."""

    def __init__(self, title: str, icon: str, color: str = "ACCENT_GREEN", parent=None):
        super().__init__(tr(title), icon, parent, margins=(12, 8, 12, 8))
        row = QHBoxLayout()
        row.setSpacing(S.px(6))
        self.val_lbl = _label("--", "RefValue", 20, True)
        self.val_lbl.setStyleSheet(f"color: {hexcol(color)};")
        self.unit_lbl = _label("", "RefSub", 10)
        row.addWidget(self.val_lbl)
        row.addWidget(self.unit_lbl, alignment=Qt.AlignmentFlag.AlignBottom)
        row.addStretch()
        self.body.addLayout(row)
        self._title_key = title

    def retranslate(self):
        self.title_lbl.setText(tr(self._title_key))

    def set_value(self, value: str, unit: str = ""):
        self.val_lbl.setText(value)
        self.unit_lbl.setText(unit)


def _reflow_add(self, widget, span: int = 1):
    self._items.append((widget, span))
    widget.setParent(self)
    widget.show()
    self._arrange(force=True)


def _reflow_remove(self, widget):
    self._items = [(w, s) for (w, s) in self._items if w is not widget]
    self._grid.removeWidget(widget)
    self._arrange(force=True)


ReflowGrid.add_widget = _reflow_add
ReflowGrid.addWidget = _reflow_add
ReflowGrid.remove_widget = _reflow_remove
