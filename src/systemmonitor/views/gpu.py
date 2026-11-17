"""
GPU View - Rik GPU-overvåking med klokker, temperaturer og sanntidsdata.
Støtter NVIDIA, AMD, Intel. Faner per GPU. Bærbar/integrert GPU-bevisst.
"""
from __future__ import annotations
import time
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, language_manager, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.widgets.gpu_widgets import COLORS, sync_colors, GPUSingleView, GPUInfoView, GlowCard
from systemmonitor.widgets.ref_design import StatusPill


class _RefHdr(QFrame):
    """Flat header frame (API-compatible with the old GlowCard header)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('RefHeader')

    def set_glow(self, _c):
        pass

    def apply_theme(self):
        self.update()


# ---------------------------------------------------------------------------
# GPUView â€“ hoved-widget med støtte for flere GPUer
# ---------------------------------------------------------------------------
class GPUView(QWidget, ScaleMixin, I18nMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gpu_views:  List[QWidget] = []
        self._gpu_names:  List[str]           = []
        self._pending_data: Optional[dict]    = None
        self._update_sched = False
        self._last_update_ts: Optional[float] = None
        self._live_ok = True

        self.scale_connect()
        self.i18n_connect()
        sync_colors()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        self._live_timer = QTimer(self)
        self._live_timer.timeout.connect(self._refresh_updated_label)
        self._live_timer.start(1000)

    def retranslate_ui(self):
        if hasattr(self, '_hdr_title_lbl'):
            self._hdr_title_lbl.setText(tr("Graphics"))
        if hasattr(self, '_live_lbl'):
            self._live_lbl.set_state("ok" if self._live_ok else "bad", tr("LIVE") if self._live_ok else tr("Offline"))
        if hasattr(self, '_no_gpu'):
            self._no_gpu.setText(
                tr("No GPU found.\nCheck that NVIDIA/AMD/Intel drivers are installed."))
        if hasattr(self, '_badge') and self._badge.isVisible():
            self._badge.setText(tr(self._badge_key) if hasattr(self, '_badge_key') else self._badge.text())
        self._refresh_updated_label()

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
            tr("No GPU found.\nCheck that NVIDIA/AMD/Intel drivers are installed.")
        )
        self._no_gpu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_gpu.setFont(QFont("Cutive", S.font_pt(11)))
        self._no_gpu.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        self._no_gpu.setVisible(False)
        root.addWidget(self._no_gpu)

    def _make_header(self) -> QFrame:
        hdr = _RefHdr()
        self._hdr_frame = hdr
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(S.px(4), S.px(2), S.px(4), S.px(2))
        hl.setSpacing(S.px(12))

        icon_box = QLabel()
        self._icon_box = icon_box
        icon_box.setFixedSize(S.px(40), S.px(40))
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(icon_box)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(0)

        title = QLabel(tr("Graphics"))
        self._hdr_title_lbl = title
        title.setObjectName("RefTitle")
        title.setFont(QFont("Cutive", S.font_pt(18), QFont.Weight.Bold))
        title_col.addWidget(title)

        self._gpu_name_lbl = QLabel("-")
        self._gpu_name_lbl.setObjectName("RefMuted")
        self._gpu_name_lbl.setFont(QFont("Cutive", S.font_pt(9)))
        title_col.addWidget(self._gpu_name_lbl)

        hl.addLayout(title_col)
        hl.addStretch()

        # kept for API compatibility; the LIVE pill replaces the dot
        self._status_dot = QLabel("")
        self._status_dot.setVisible(False)

        self._updated_lbl = QLabel("")
        self._updated_lbl.setObjectName("RefMuted")
        self._updated_lbl.setFont(QFont("Cutive", S.font_pt(8)))
        hl.addWidget(self._updated_lbl)

        self._badge = QLabel("")
        self._badge.setFont(QFont("Cutive", S.font_pt(8), QFont.Weight.Bold))
        self._badge.setStyleSheet(
            f"color: {COLORS['bg_primary']}; background: {COLORS['accent_blue']}; "
            f"border: none; border-radius: 4px; padding: 1px 6px;"
        )
        self._badge.setVisible(False)
        hl.addWidget(self._badge)

        self._live_lbl = StatusPill(tr("LIVE"))
        hl.addWidget(self._live_lbl)

        self._apply_icon_box_style()
        return hdr

    def _apply_icon_box_style(self):
        if not hasattr(self, '_icon_box'):
            return
        self._icon_box.setStyleSheet("background: transparent; border: none;")
        try:
            px = qta.icon('ph.monitor', color=COLORS['accent_green']).pixmap(QSize(S.px(30), S.px(30)))
            self._icon_box.setPixmap(px)
        except Exception:
            pass

    def _refresh_updated_label(self):
        if not hasattr(self, '_updated_lbl'):
            return
        if self._last_update_ts is None:
            self._updated_lbl.setText("")
            return
        elapsed = int(time.time() - self._last_update_ts)
        if elapsed < 1:
            self._updated_lbl.setText(tr("Updated just now"))
        else:
            self._updated_lbl.setText(tr("Updated {0}s ago", elapsed))

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
        self._last_update_ts = time.time()
        self._refresh_updated_label()

        # Hent liste over GPU-dicts (GPUInfo.to_dict() format)
        gpus: List[dict] = gpu_data.get('gpus', [])

        # Fallback: flat-format (bakoverkompatibilitet)
        if not gpus:
            gpus = [self._flat_to_dict(gpu_data)]

        if not gpus:
            self._show_no_gpu(True)
            return

        gpus = self._merge_duplicate_gpus(gpus)
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
            self._gpu_name_lbl.setText(gpu.get('name', '–'))
            self._update_badge(gpu)

    # ------------------------------------------------------------------
    # Hjelper-metoder
    # ------------------------------------------------------------------
    @staticmethod
    def _merge_duplicate_gpus(gpus: List[dict]) -> List[dict]:
        """The same physical GPU can be reported by several detectors (e.g. WMI
        with static driver info and ADL/NVML with live metrics). Show it as ONE
        tab: keep the entry with the most live data and fill its gaps from the
        others."""
        empty = (None, '', 'Unknown', 0, 0.0)
        groups: dict = {}
        order: list = []
        for g in gpus:
            key = (str(g.get('name', '')).strip().lower(), str(g.get('vendor', '')).strip().lower())
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(g)
        merged = []
        for key in order:
            entries = groups[key]
            if len(entries) == 1:
                merged.append(entries[0])
                continue
            entries.sort(key=lambda e: sum(1 for k, v in e.items() if k != 'raw_data' and v not in empty),
                         reverse=True)
            base = dict(entries[0])
            for other in entries[1:]:
                for k, v in other.items():
                    if base.get(k) in empty and v not in empty:
                        base[k] = v
            merged.append(base)
        return merged

    def _rebuild_tabs(self, gpus: List[dict]):
        self._tabs.clear()
        self._gpu_views.clear()
        for i, gpu in enumerate(gpus):
            gpu_type = (gpu.get('gpu_type') or '').lower()
            view: QWidget = GPUInfoView() if gpu_type == 'integrated' else GPUSingleView()
            self._gpu_views.append(view)
            name   = gpu.get('name', f'GPU {i}')
            vendor = (gpu.get('vendor') or '').upper()[:3]
            label  = f"{vendor} {name[:18]}..." if len(name) > 18 else f"{vendor} {name}"
            self._tabs.addTab(view, label.strip())
        # Skjul fanelinjen for enkelt-GPU
        self._tabs.tabBar().setVisible(len(gpus) > 1)

    def _update_badge(self, gpu: dict):
        gpu_type = (gpu.get('gpu_type') or '').lower()
        name     = (gpu.get('name') or '').lower()
        if gpu_type == 'integrated':
            self._badge_key = "iGPU"
            self._badge.setText(tr("iGPU"))
            self._badge.setVisible(True)
        elif any(x in name for x in ('laptop', 'mobile', 'max-q')):
            self._badge_key = "Mobile"
            self._badge.setText(tr("Mobile"))
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
        self._live_ok = True
        if hasattr(self, '_live_lbl'):
            self._live_lbl.set_state("ok", tr("LIVE"))

    def _set_status_bad(self):
        self._live_ok = False
        if hasattr(self, '_live_lbl'):
            self._live_lbl.set_state("bad", tr("Offline"))

    def on_scale_changed(self, _):
        self._setup_ui()

    def _on_theme_changed(self, _):
        sync_colors()
        self._apply_theme()

    def _apply_theme(self):
        """Update colors on existing widgets without rebuilding the layout."""
        if hasattr(self, '_hdr_frame'):
            self._hdr_frame.set_glow(COLORS['accent_cyan'])
            self._hdr_frame.apply_theme()
        self._apply_icon_box_style()
        if hasattr(self, '_tabs'):
            self._tabs.setStyleSheet(self._tab_css())
        if hasattr(self, '_no_gpu'):
            self._no_gpu.setStyleSheet(
                f"color: {COLORS['text_muted']}; background: transparent;"
            )
        if hasattr(self, '_badge'):
            self._badge.setStyleSheet(
                f"color: {COLORS['bg_primary']}; background: {COLORS['accent_blue']}; "
                f"border: none; border-radius: 4px; padding: 1px 6px;"
            )
        for view in self._gpu_views:
            if hasattr(view, 'apply_theme'):
                view.apply_theme()
            else:
                view.update()
        self.update()
