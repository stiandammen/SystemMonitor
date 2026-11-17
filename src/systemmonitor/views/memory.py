"""
Memory View - reference redesign.

Usage donut + breakdown bar, history chart with range tabs, memory information.
Same data feed as before (update_data -> data['memory']).
"""
from collections import deque
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QScrollArea
)

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.widgets.ref_design import (
    Panel, PageHeader, Donut, SegBar, DotRow, KV, AreaChart, ChartPanel, ReflowGrid, flex, hexcol,
)


def c():
    """Access theme colors"""
    return theme_manager.colors


def _gb(b: float) -> str:
    return f"{b / (1024 ** 3):.1f} GB".replace(".", ",")


class MemoryView(QWidget, ScaleMixin, I18nMixin):
    """Memory monitoring dashboard (reference design)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_memory_data = None
        self._update_scheduled = False
        self._store = deque(maxlen=60000)  # chart history survives UI rebuilds
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._rebuild)

    def retranslate_ui(self):
        QTimer.singleShot(0, self._rebuild)

    def _rebuild(self):
        self._setup_ui()
        if self._current_memory_data:
            self._do_display_update()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main = QVBoxLayout()
        main.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        main.setSpacing(S.px(10))
        self.setLayout(main)

        self._hdr = PageHeader(tr("Memory"), tr("Monitoring of system memory, distribution and usage over time"),
                               "ph.memory", pill=tr("LIVE"))
        main.addWidget(self._hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }"
                             "QScrollArea > QWidget > QWidget { background: transparent; }")
        main.addWidget(scroll, stretch=1)

        # --- Usage donut ---
        p_usage = Panel(tr("Memory usage"), "ph.memory")
        row = QHBoxLayout()
        row.setSpacing(S.px(12))
        self._donut = Donut(value_pt=17)
        self._donut.setMinimumHeight(S.px(190))
        row.addWidget(self._donut, stretch=3)
        side = QVBoxLayout()
        side.setSpacing(S.px(6))
        side.addStretch()
        self._row_used = DotRow("ACCENT_GREEN", tr("In use"))
        self._row_avail = DotRow("ACCENT_CYAN", tr("Available"))
        self._row_cached = DotRow("ACCENT_PURPLE", tr("Cached"))
        self._row_free = DotRow("TEXT_MUTED", tr("Free"))
        for w in (self._row_used, self._row_avail, self._row_cached, self._row_free):
            side.addWidget(w)
        side.addStretch()
        row.addLayout(side, stretch=3)
        p_usage.body.addLayout(row)

        # --- Distribution ---
        p_dist = Panel(tr("Memory distribution"), "ph.chart-pie-slice")
        self._seg = SegBar(20)
        p_dist.body.addWidget(self._seg)
        p_dist.body.addSpacing(S.px(6))
        self._d_used = DotRow("ACCENT_GREEN", tr("In use"))
        self._d_cached = DotRow("ACCENT_PURPLE", tr("Cached"))
        self._d_avail = DotRow("ACCENT_CYAN", tr("Available"))
        self._d_free = DotRow("TEXT_MUTED", tr("Free"))
        for w in (self._d_used, self._d_cached, self._d_avail, self._d_free):
            p_dist.body.addWidget(w)
        p_dist.body.addStretch()

        # --- History ---
        self._chart = AreaChart(["ACCENT_GREEN"], 100.0, store=self._store)
        p_hist = ChartPanel(tr("Memory usage over time"), "ph.chart-line", self._chart, tabs=True)
        p_hist.setMinimumHeight(S.px(240))

        # --- Information ---
        p_info = Panel(tr("Memory information"), "ph.info")
        self._i_type = KV(tr("Memory Type"), "--")
        self._i_total = KV(tr("Total Memory"), "--")
        self._i_swap = KV(tr("Swap"), "--")
        self._i_health = KV(tr("System Status"), "--")
        for w in (self._i_type, self._i_total, self._i_swap, self._i_health):
            p_info.body.addWidget(w)
        p_info.body.addStretch()

        grid = ReflowGrid([(flex(p_usage, 360), 1), (p_dist, 1), (p_hist, 2), (p_info, 2)],
                          max_cols=2, min_col_width=420)
        inner = QWidget()
        inner.setObjectName("RefContent")
        inner.setStyleSheet("QWidget#RefContent { background: transparent; }")
        il = QVBoxLayout(inner)
        il.setContentsMargins(0, 0, S.px(4), 0)
        il.addWidget(grid)
        il.addStretch(1)
        scroll.setWidget(inner)
        grid.bind_viewport(scroll)

    # ------------------------------------------------------------------
    def update_data(self, data: dict):
        """Handle data from collector signal - runs on UI thread"""
        try:
            if 'memory' in data:
                self._current_memory_data = data['memory']
            if not self._update_scheduled:
                self._update_scheduled = True
                QTimer.singleShot(16, self._do_display_update)
        except Exception:
            pass

    def _do_display_update(self):
        self._update_scheduled = False
        mem = self._current_memory_data
        if not mem:
            return
        try:
            total = mem['total']
            if total <= 0:
                return
            used = mem['used']
            avail = mem['available']
            cached = mem.get('cached', 0)
            free = max(0, mem.get('free', avail) - cached)
            used_pct = mem['percent']
            avail_pct = avail / total * 100
            cached_pct = cached / total * 100
            free_pct = free / total * 100

            self._donut.set_data([(used_pct, "ACCENT_GREEN")], _gb(used), f"/ {_gb(total)}")
            self._row_used.set_value(f"{_gb(used)} ({used_pct:.0f} %)")
            self._row_avail.set_value(f"{_gb(avail)} ({avail_pct:.0f} %)")
            self._row_cached.set_value(f"{_gb(cached)} ({cached_pct:.0f} %)")
            self._row_free.set_value(f"{_gb(free)} ({free_pct:.0f} %)")

            self._seg.set_data([(used_pct, "ACCENT_GREEN"), (cached_pct, "ACCENT_PURPLE"),
                                (max(0.0, avail_pct - cached_pct), "ACCENT_CYAN")])
            self._d_used.set_value(f"{_gb(used)} ({used_pct:.0f} %)")
            self._d_cached.set_value(f"{_gb(cached)} ({cached_pct:.0f} %)")
            self._d_avail.set_value(f"{_gb(avail)} ({avail_pct:.0f} %)")
            self._d_free.set_value(f"{_gb(free)} ({free_pct:.0f} %)")

            self._chart.push(used_pct)
            self._chart.set_overlay(f"{used_pct:.0f} %", tr("Used"))

            ram_type = mem.get('ram_type', '')
            self._i_type.set_value(ram_type or "--")
            self._i_total.set_value(_gb(total))
            st, sp = mem.get('swap_used'), mem.get('swap_total')
            if sp:
                self._i_swap.set_value(f"{_gb(st or 0)} / {_gb(sp)}")

            colors = c()
            if used_pct >= 90:
                h_text, h_key, state = tr("Critical"), "ACCENT_RED", "bad"
            elif used_pct >= 70:
                h_text, h_key, state = tr("Warning"), "ACCENT_ORANGE", "warn"
            else:
                h_text, h_key, state = tr("Healthy"), "STATUS_GREEN", "ok"
            self._i_health.val_lbl.setStyleSheet(f"color: {hexcol(h_key)};")
            self._i_health.set_value(h_text)
            self._hdr.pill.set_state(state, tr("LIVE") if state == "ok" else h_text)
        except Exception:
            pass
