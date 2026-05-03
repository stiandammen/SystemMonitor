"""
scaler.py  –  Drop-in auto-skalering for PyQt6 prosjekter
"""

from __future__ import annotations
import re
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QScreen, QFont


class _ScaleSignals(QObject):
    scale_changed = pyqtSignal(float)

_signals = _ScaleSignals()


class _ScreenScaler:
    _REF_DPI  = 96
    _REF_W    = 1920
    _REF_H    = 1080
    _REF_DIAG = 24.0

    def __init__(self):
        self.scale_factor  = 1.0
        self.font_scale    = 1.0
        self.screen_width  = 1920
        self.screen_height = 1080
        self.logical_dpi   = 96.0
        self.diag_inch     = 24.0
        self._screen: QScreen | None = None

    def init(self, app: QApplication):
        self._app    = app
        self._screen = app.primaryScreen()
        self._compute()
        app.primaryScreenChanged.connect(self._on_primary_changed)
        for scr in app.screens():
            scr.geometryChanged.connect(self._on_geometry_changed)

    def _on_primary_changed(self, screen: QScreen):
        self._screen = screen
        self._compute()
        _signals.scale_changed.emit(self.scale_factor)

    def _on_geometry_changed(self, _geom):
        self._compute()
        _signals.scale_changed.emit(self.scale_factor)

    def _compute(self):
        if self._screen is None:
            return
        geom = self._screen.geometry()
        self.screen_width  = geom.width()
        self.screen_height = geom.height()
        self.logical_dpi   = self._screen.logicalDotsPerInch()

        mm = self._screen.physicalSize()
        if mm.width() > 0:
            self.diag_inch = ((mm.width()**2 + mm.height()**2) ** 0.5) / 25.4
        else:
            self.diag_inch = self._REF_DIAG

        res_scale = (
            (self.screen_width  / self._REF_W) +
            (self.screen_height / self._REF_H)
        ) / 2
        dpi_scale = self.logical_dpi / self._REF_DPI

        if   self.diag_inch > 32: size_adj = 1.10
        elif self.diag_inch > 27: size_adj = 1.05
        elif self.diag_inch < 13: size_adj = 0.80
        elif self.diag_inch < 15: size_adj = 0.85
        elif self.diag_inch < 17: size_adj = 0.91
        else:                     size_adj = 1.00

        raw = (dpi_scale * 0.55 + res_scale * 0.45) * size_adj
        self.scale_factor = max(0.60, min(2.20, raw))
        self.font_scale   = max(0.70, min(2.00, raw * 0.94))

    def px(self, value: int | float) -> int:
        return max(1, round(value * self.scale_factor))

    def fpx(self, value: int | float) -> float:
        return value * self.scale_factor

    def font(self, family: str, base_pt: int, bold: bool = False) -> QFont:
        f = QFont(family, self.font_pt(base_pt))
        if bold:
            f.setBold(True)
        return f

    def font_pt(self, base_pt: int) -> int:
        return max(6, round(base_pt * self.font_scale))

    def margins(self, top=8, right=8, bottom=8, left=8):
        return (self.px(left), self.px(top), self.px(right), self.px(bottom))

    def spacing(self, value: int) -> int:
        return self.px(value)

    def info(self) -> str:
        return (
            f"{self.screen_width}×{self.screen_height} | "
            f"DPI {self.logical_dpi:.0f} | "
            f"{self.diag_inch:.1f}\" | "
            f"Skala ×{self.scale_factor:.2f}"
        )


S = _ScreenScaler()


class ScaleMixin:
    def scale_connect(self):
        _signals.scale_changed.connect(self._handle_scale_changed)

    def scale_disconnect(self):
        try:
            _signals.scale_changed.disconnect(self._handle_scale_changed)
        except Exception:
            pass

    def _handle_scale_changed(self, factor: float):
        self.on_scale_changed(factor)

    def on_scale_changed(self, factor: float):
        pass


def scaled_stylesheet(template: str) -> str:
    def replacer(m):
        return str(S.px(int(m.group(1))))
    return re.sub(r'\{px_(\d+)\}', replacer, template)


def init_scaler(app: QApplication):
    from PyQt6.QtCore import Qt
    try:
        app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass
    S.init(app)
    print(f"[Scaler init] {S.info()}")