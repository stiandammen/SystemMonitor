"""
scaler.py  â€“  Auto-scaling and responsive layout system for PyQt6
Supports 1080p through 5K with automatic screen-tier detection, DPI scaling,
compact/wide/ultra layout modes, and per-user scale overrides.
"""
from __future__ import annotations
import re
from enum import Enum, auto
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QScreen, QFont


class LayoutMode(Enum):
    COMPACT  = auto()   # < 1600 px wide  (small/laptop)
    EXPANDED = auto()   # 1600â€“2559 px    (FHD / standard)
    WIDE     = auto()   # 2560â€“3839 px    (QHD / 2K)
    ULTRA    = auto()   # 3840 px+        (4K / 5K)


class ScreenTier(Enum):
    """Human-readable resolution category, auto-detected from physical pixels."""
    SD      = "SD"       # < 1280 wide
    HD      = "HD"       # 1280â€“1919
    FHD     = "FHD"      # 1920â€“2559  (1080p)
    QHD     = "QHD"      # 2560â€“3839  (1440p / 2K)
    UHD_4K  = "4K"       # 3840â€“5119  (2160p)
    UHD_5K  = "5K"       # 5120+      (2880p)


class _ScaleSignals(QObject):
    scale_changed       = pyqtSignal(float)
    layout_mode_changed = pyqtSignal(object)   # LayoutMode


_signals = _ScaleSignals()


class _ScreenScaler:
    # Reference display: 24" FHD at 96 DPI
    _REF_DPI  = 96
    _REF_W    = 1920
    _REF_H    = 1080
    _REF_DIAG = 24.0

    # Layout-mode pixel-width thresholds
    _COMPACT_W  = 1600
    _WIDE_W     = 2560
    _ULTRA_W    = 3840

    # Kept for backward compat (used by config.py / external callers)
    COMPACT_THRESHOLD = 1600
    MEDIUM_THRESHOLD  = 2200

    def __init__(self):
        self.scale_factor  = 1.0
        self.font_scale    = 1.0
        self.screen_width  = 1920
        self.screen_height = 1080
        self.logical_dpi   = 96.0
        self.diag_inch     = 24.0
        self.layout_mode   = LayoutMode.EXPANDED
        self.screen_tier   = ScreenTier.FHD
        self.dpi_ratio     = 1.0
        self._screen: QScreen | None = None
        self._app: QApplication | None = None
        self._base_scale   = 1.0
        self._user_scale   = 1.0
        self._geometry_timer = QTimer()
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._delayed_compute)

    # â”€â”€ initialisation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def init(self, app: QApplication):
        self._app    = app
        self._screen = app.primaryScreen()
        self._compute()
        app.primaryScreenChanged.connect(self._on_primary_changed)
        for scr in app.screens():
            scr.geometryChanged.connect(self._on_geometry_changed)
            scr.logicalDotsPerInchChanged.connect(self._on_dpi_changed)

    # â”€â”€ screen-change handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _on_primary_changed(self, screen: QScreen):
        self._screen = screen
        self._compute()

    def _on_geometry_changed(self, _geom):
        if not self._geometry_timer.isActive():
            self._geometry_timer.start(100)

    def _on_dpi_changed(self, _dpi):
        self._compute()

    def _delayed_compute(self):
        self._compute()

    # â”€â”€ core calculation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _compute(self):
        if self._screen is None:
            return

        geom = self._screen.geometry()
        old_mode = self.layout_mode

        self.screen_width  = geom.width()
        self.screen_height = geom.height()
        self.logical_dpi   = self._screen.logicalDotsPerInch()

        mm = self._screen.physicalSize()
        if mm.width() > 0:
            self.diag_inch = ((mm.width()**2 + mm.height()**2) ** 0.5) / 25.4
        else:
            self.diag_inch = self._REF_DIAG

        self.dpi_ratio  = self.logical_dpi / self._REF_DPI
        self.screen_tier = self._detect_tier(self.screen_width)

        # --- resolution-based scale ---
        res_scale = (
            (self.screen_width  / self._REF_W) +
            (self.screen_height / self._REF_H)
        ) / 2

        # --- DPI-based scale ---
        dpi_scale = self.logical_dpi / self._REF_DPI

        # --- physical size adjustment ---
        if   self.diag_inch > 43: size_adj = 1.20
        elif self.diag_inch > 32: size_adj = 1.12
        elif self.diag_inch > 27: size_adj = 1.06
        elif self.diag_inch < 12: size_adj = 0.78
        elif self.diag_inch < 14: size_adj = 0.83
        elif self.diag_inch < 16: size_adj = 0.88
        elif self.diag_inch < 17: size_adj = 0.92
        else:                     size_adj = 1.00

        # Blend: DPI carries 55 %, resolution carries 45 %.
        # For high-res screens where the OS applies no scaling the res component
        # ensures the UI grows proportionally.
        raw = (dpi_scale * 0.55 + res_scale * 0.45) * size_adj

        self._base_scale  = raw
        effective         = raw * self._user_scale

        # Caps scale to 3.5 so 5 K / high-DPI screens are fully supported.
        self.scale_factor = max(0.60, min(3.50, effective))
        self.font_scale   = max(0.70, min(2.80, effective * 0.94))

        # --- layout mode ---
        if   self.screen_width < self._COMPACT_W:
            self.layout_mode = LayoutMode.COMPACT
        elif self.screen_width < self._WIDE_W:
            self.layout_mode = LayoutMode.EXPANDED
        elif self.screen_width < self._ULTRA_W:
            self.layout_mode = LayoutMode.WIDE
        else:
            self.layout_mode = LayoutMode.ULTRA

        _signals.scale_changed.emit(self.scale_factor)
        if old_mode != self.layout_mode:
            _signals.layout_mode_changed.emit(self.layout_mode)

    # â”€â”€ tier detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _detect_tier(width_px: int) -> ScreenTier:
        if   width_px >= 5120: return ScreenTier.UHD_5K
        elif width_px >= 3840: return ScreenTier.UHD_4K
        elif width_px >= 2560: return ScreenTier.QHD
        elif width_px >= 1920: return ScreenTier.FHD
        elif width_px >= 1280: return ScreenTier.HD
        else:                  return ScreenTier.SD

    # â”€â”€ public helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

    # â”€â”€ layout-mode queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def is_compact(self) -> bool:
        """True only on narrow screens (< 1600 px)."""
        return self.layout_mode == LayoutMode.COMPACT

    def is_expanded(self) -> bool:
        """True for any non-compact layout (FHD, QHD, 4K, 5K)."""
        return self.layout_mode != LayoutMode.COMPACT

    def is_wide(self) -> bool:
        """True for QHD / 2K screens (2560â€“3839 px)."""
        return self.layout_mode == LayoutMode.WIDE

    def is_ultra(self) -> bool:
        """True for 4K and 5K screens (3840 px+)."""
        return self.layout_mode == LayoutMode.ULTRA

    # â”€â”€ grid helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def grid_columns(self, max_cols: int = 5) -> int:
        """Suggested column count based on primary screen width."""
        return self.grid_columns_for(self.screen_width, max_cols)

    def grid_columns_for(self, width: int, max_cols: int = 5) -> int:
        """Suggested column count for a grid layout at the given pixel width.

        Thresholds match the responsive design spec:
        <800 → 1, <1200 → 2, <1600 → 3, <2200 → 4, ≥2200 → 5
        """
        if   width < 800:   return min(1, max_cols)
        elif width < 1200:  return min(2, max_cols)
        elif width < 1600:  return min(3, max_cols)
        elif width < 2200:  return min(4, max_cols)
        else:               return min(5, max_cols)

    # â”€â”€ user scale override â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def set_user_scale(self, factor: float):
        """Apply a user-defined scale multiplier on top of the auto-detected scale."""
        self._user_scale  = max(0.50, min(3.00, factor))
        effective         = self._base_scale * self._user_scale
        self.scale_factor = max(0.60, min(3.50, effective))
        self.font_scale   = max(0.70, min(2.80, effective * 0.94))
        _signals.scale_changed.emit(self.scale_factor)

    # â”€â”€ info / debug â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def info(self) -> str:
        mode_names = {
            LayoutMode.COMPACT:  "compact",
            LayoutMode.EXPANDED: "expanded",
            LayoutMode.WIDE:     "wide",
            LayoutMode.ULTRA:    "ultra",
        }
        return (
            f"{self.screen_width}x{self.screen_height} | "
            f"DPI {self.logical_dpi:.0f} | "
            f"{self.diag_inch:.1f}\" | "
            f"Tier {self.screen_tier.value} | "
            f"Scale x{self.scale_factor:.2f} | "
            f"Mode: {mode_names.get(self.layout_mode, '?')}"
        )

    def detect_screen_summary(self) -> dict:
        """Return a dict with all auto-detected screen properties."""
        return {
            "width":        self.screen_width,
            "height":       self.screen_height,
            "dpi":          round(self.logical_dpi, 1),
            "diagonal_in":  round(self.diag_inch, 1),
            "tier":         self.screen_tier.value,
            "layout_mode":  self.layout_mode.name,
            "scale_factor": round(self.scale_factor, 3),
            "font_scale":   round(self.font_scale, 3),
        }


# â”€â”€ singleton â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

S = _ScreenScaler()


# â”€â”€ mixin for QWidget subclasses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class ScaleMixin:
    def scale_connect(self):
        _signals.scale_changed.connect(self._handle_scale_changed)
        _signals.layout_mode_changed.connect(self._handle_layout_mode_changed)

    def scale_disconnect(self):
        try:
            _signals.scale_changed.disconnect(self._handle_scale_changed)
        except Exception:
            pass
        try:
            _signals.layout_mode_changed.disconnect(self._handle_layout_mode_changed)
        except Exception:
            pass

    def _handle_scale_changed(self, factor: float):
        self.on_scale_changed(factor)

    def _handle_layout_mode_changed(self, mode):
        self.on_layout_mode_changed(mode)

    def on_scale_changed(self, factor: float):
        pass

    def on_layout_mode_changed(self, mode):
        pass


# â”€â”€ stylesheet helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def scaled_stylesheet(template: str) -> str:
    def replacer(m):
        return str(S.px(int(m.group(1))))
    return re.sub(r'\{px_(\d+)\}', replacer, template)


# â”€â”€ initialiser called from __main__ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def init_scaler(app: QApplication):
    S.init(app)
    print(f"[Scaler init] {S.info()}")

