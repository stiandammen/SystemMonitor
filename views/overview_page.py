"""
Overview Page - Premium Glass Dashboard
Responsive design with adaptive grid layout, collapsible panels, and real-time data
"""
import platform
import time
import psutil
import subprocess
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar, QGridLayout, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QGradient

from widgets.donut_gauge import DonutGauge
from widgets.sparkline import SparklineWidget
from widgets.responsive import CollapsiblePanel, ResponsiveGridLayout
from styles.theme import theme_manager
from scaler import S, ScaleMixin, LayoutMode


class GlassMetricCard(QFrame):
    """Premium glass metric card - responsive with minimum sizes"""

    def __init__(self, title: str, icon: str, color: str | None = None, parent=None):
        super().__init__(parent)
        self._color = color or theme_manager.colors.ACCENT_GREEN
        self._title = title
        self._icon = icon
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(S.px(120))
        self.setMinimumWidth(S.px(160))

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    background-color: {colors.BG_HOVER};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
                QFrame:hover {{
                    background-color: {colors.BG_HOVER};
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(6))
        self.setLayout(layout)

        header = QHBoxLayout()
        header.setSpacing(S.px(8))

        if self._icon:
            icon_label = QLabel(self._icon)
            icon_label.setFont(QFont("Segoe UI", S.font_pt(14)))
            icon_label.setStyleSheet(f"color: {self._color}; background: transparent;")
            header.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(24), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._value_label)

        self._subtitle_label = QLabel("")
        self._subtitle_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._subtitle_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._subtitle_label)

        self._sparkline = SparklineWidget(colors=[self._color])
        self._sparkline.setMinimumHeight(S.px(30))
        self._sparkline.setMaximumHeight(S.px(50))
        layout.addWidget(self._sparkline)

    def set_value(self, value: str, subtitle: str = ""):
        self._value_label.setText(value)
        self._subtitle_label.setText(subtitle)

    def set_color(self, color: str):
        self._color = color

    def push_sparkline(self, value: float):
        self._sparkline.push(value)


class GlassChartPanel(QFrame):
    """Premium glass chart panel with title and sparkline - responsive"""

    def __init__(self, title: str, color: str | None = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._color = color or theme_manager.colors.ACCENT_GREEN
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(S.px(80))
        self.setMinimumWidth(S.px(140))

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    border-color: rgba(74, 108, 247, 0.5);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)

        self._sparkline = SparklineWidget(colors=[self._color])
        self._sparkline.setMinimumHeight(S.px(50))
        self._sparkline.setMaximumHeight(S.px(90))
        layout.addWidget(self._sparkline, stretch=1)

    def push(self, value: float):
        self._sparkline.push(value)

    def push_multi(self, values: list):
        self._sparkline.push_multi(values)


class GlassInfoPanel(QFrame):
    """Premium glass info panel - responsive"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    border-color: rgba(74, 108, 247, 0.5);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title_label)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: transparent;")
        layout.addWidget(sep)

        self._content = QVBoxLayout()
        self._content.setSpacing(0)
        layout.addLayout(self._content)

    def add_info_row(self, label: str, value: str, color: str | None = None):
        row = QFrame()
        row.setStyleSheet("background: transparent;")

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, S.px(4), 0, S.px(4))
        row_layout.setSpacing(S.px(10))
        row.setLayout(row_layout)

        indicator = QFrame()
        indicator.setFixedSize(3, 16)
        accent_color = color or theme_manager.colors.ACCENT_GREEN
        indicator.setStyleSheet(f"background-color: {accent_color}; border-radius: 1px;")
        row_layout.addWidget(indicator)

        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", S.font_pt(10)))
        label_widget.setMinimumWidth(80)
        label_widget.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        row_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Segoe UI", S.font_pt(10)))
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_widget.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY}; background: transparent;")
        row_layout.addWidget(value_widget, stretch=1)

        self._content.addWidget(row)


class _AnimatedBar(QProgressBar):
    """Progress bar that smoothly fills to its target value via QPropertyAnimation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setMinimumHeight(S.px(8))
        self.setMaximumHeight(S.px(10))
        self._anim = QPropertyAnimation(self, b"value", self)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fill_from_zero(self, target: int):
        self._anim.stop()
        self._anim.setDuration(750)
        self._anim.setStartValue(0)
        self._anim.setEndValue(max(0, min(100, target)))
        self._anim.start()

    def update_value(self, target: int):
        self._anim.stop()
        self._anim.setDuration(300)
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(max(0, min(100, target)))
        self._anim.start()


class GlassStoragePanel(QFrame):
    """Storage panel with animated bars and live drive info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_partitions = []
        self._drive_keys = []       # ordered list of device strings currently shown
        self._drive_refs = {}       # device -> {bar, pct_lbl, used_lbl, free_lbl, letter, name}
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        colors = theme_manager.colors
        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)
        self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        if self._last_partitions:
            self._rebuild_drives(self._last_partitions, animate=False)

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        header = QHBoxLayout()
        self._title_label = QLabel("Storage Drives")
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(self._title_label)
        header.addStretch()
        layout.addLayout(header)

        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(S.px(8))
        layout.addLayout(self._storage_container)

    def _clear_drives(self):
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._drive_keys = []
        self._drive_refs = {}

    def _pct_color(self, pct: float) -> str:
        colors = theme_manager.colors
        return (colors.ACCENT_GREEN if pct < 75
                else colors.ACCENT_ORANGE if pct < 90
                else colors.ACCENT_RED)

    def _add_drive_card(self, partition: dict, animate: bool):
        colors = theme_manager.colors
        device = partition.get('device', '')
        mountpoint = partition.get('mountpoint', '')
        total_gb = partition.get('total', 0) / (1024 ** 3)
        used_gb = partition.get('used', 0) / (1024 ** 3)
        free_gb = total_gb - used_gb
        pct = partition.get('percent', 0)
        pct_color = self._pct_color(pct)
        label_text = device.replace("\\", "") if device else "?"

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        row = QHBoxLayout()
        row.setContentsMargins(S.px(14), S.px(12), S.px(14), S.px(12))
        row.setSpacing(S.px(14))
        card.setLayout(row)

        # Drive letter badge
        letter_lbl = QLabel(label_text)
        letter_lbl.setFont(QFont("Segoe UI", S.font_pt(15), QFont.Weight.Bold))
        letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        letter_lbl.setFixedWidth(S.px(44))
        letter_lbl.setStyleSheet(
            f"color: {pct_color}; background: transparent;"
        )
        row.addWidget(letter_lbl)

        # Center: name + bar + stats
        info = QVBoxLayout()
        info.setSpacing(S.px(4))

        name_lbl = QLabel(mountpoint if mountpoint else device)
        name_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        info.addWidget(name_lbl)

        bar = _AnimatedBar()
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-radius: {S.px(4)}px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: {S.px(4)}px;
            }}
        """)
        info.addWidget(bar)

        stats_row = QHBoxLayout()
        used_lbl = QLabel(f"{used_gb:.1f} GB used")
        used_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        used_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        stats_row.addWidget(used_lbl)
        stats_row.addStretch()
        free_lbl = QLabel(f"{free_gb:.1f} GB free")
        free_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        free_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        stats_row.addWidget(free_lbl)
        info.addLayout(stats_row)

        row.addLayout(info, stretch=1)

        # Right: percentage box
        pct_box = QFrame()
        pct_box.setStyleSheet(
            f"background-color: {colors.BG_PRIMARY}; border-radius: {S.px(8)}px;"
        )
        pct_col = QVBoxLayout()
        pct_col.setSpacing(1)
        pct_col.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
        pct_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_box.setLayout(pct_col)

        pct_lbl = QLabel(f"{pct:.0f}%")
        pct_lbl.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
        pct_col.addWidget(pct_lbl)

        sub_lbl = QLabel("used")
        sub_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        pct_col.addWidget(sub_lbl)

        row.addWidget(pct_box)
        self._storage_container.addWidget(card)

        # Animate or set directly
        if animate:
            bar.fill_from_zero(int(pct))
        else:
            bar.setValue(int(pct))

        self._drive_keys.append(device)
        self._drive_refs[device] = {
            'bar': bar, 'pct_lbl': pct_lbl,
            'used_lbl': used_lbl, 'free_lbl': free_lbl,
            'letter': letter_lbl, 'name': name_lbl,
        }

    def _update_drive_card(self, partition: dict):
        device = partition.get('device', '')
        refs = self._drive_refs.get(device)
        if not refs:
            return
        colors = theme_manager.colors
        total_gb = partition.get('total', 0) / (1024 ** 3)
        used_gb = partition.get('used', 0) / (1024 ** 3)
        free_gb = total_gb - used_gb
        pct = partition.get('percent', 0)
        pct_color = self._pct_color(pct)

        refs['bar'].update_value(int(pct))
        refs['bar'].setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-radius: {S.px(4)}px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: {S.px(4)}px;
            }}
        """)
        refs['pct_lbl'].setText(f"{pct:.0f}%")
        refs['pct_lbl'].setStyleSheet(f"color: {pct_color}; background: transparent;")
        refs['used_lbl'].setText(f"{used_gb:.1f} GB used")
        refs['free_lbl'].setText(f"{free_gb:.1f} GB free")
        refs['letter'].setStyleSheet(f"color: {pct_color}; background: transparent;")

    def _rebuild_drives(self, partitions: list, animate: bool):
        self._clear_drives()
        colors = theme_manager.colors
        valid = [p for p in partitions if p.get('fstype')]
        if not valid:
            placeholder = QLabel("No drives detected")
            placeholder.setFont(QFont("Segoe UI", S.font_pt(11)))
            placeholder.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._storage_container.addWidget(placeholder)
            return
        for partition in valid:
            self._add_drive_card(partition, animate=animate)

    def update_drives(self, partitions: list):
        self._last_partitions = partitions
        new_keys = [p.get('device', '') for p in partitions if p.get('fstype')]

        if new_keys != self._drive_keys:
            # Drive set changed – rebuild with entrance animation
            self._rebuild_drives(partitions, animate=True)
        else:
            # Same drives – update in place with smooth transition
            for partition in partitions:
                if partition.get('fstype'):
                    self._update_drive_card(partition)


class OverviewPage(QWidget, ScaleMixin):
    """Premium glass overview dashboard - responsive with adaptive grid"""

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0
        self._last_net = None
        self._net_down_mbps = 0.0
        self._net_up_mbps = 0.0
        self._last_data = {}
        self._system_info_cache = {}
        self._system_info_cache_time = 0
        self._system_info_cache_ttl = 30

        self.scale_connect()
        self._setup_ui()
        self._start_timers()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_data_collector(self, collector):
        self._data_collector = collector

    def _on_theme_changed(self, theme_name: str):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_scale_changed(self, factor: float):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def on_layout_mode_changed(self, mode):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def _rebuild_and_restore(self):
        self._setup_ui()
        if self._last_data:
            self.update_data(self._last_data)

    def _setup_ui(self):
        # Clear previous layout if this is a rebuild
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._header = self._create_header()
        main_layout.addWidget(self._header)

        scroll = QScrollArea()
        self._main_scroll = scroll
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.BG_PRIMARY};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors.BG_SECONDARY};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.ACCENT_GREEN_DIM};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(S.px(24), S.px(16), S.px(24), S.px(24))
        content_layout.setSpacing(S.px(16))
        content.setLayout(content_layout)

        self._metrics_row = self._create_metrics_row()
        content_layout.addWidget(self._metrics_row)

        self._charts_section = self._create_charts_section()
        content_layout.addWidget(self._charts_section, stretch=1)

        self._info_row = self._create_info_row()
        content_layout.addWidget(self._info_row)

        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)

    def _create_header(self):
        colors = theme_manager.colors
        header = QFrame()
        header.setMinimumHeight(S.px(60))
        header.setMaximumHeight(S.px(90))
        if theme_manager.current_theme == "heimdal":
            header.setStyleSheet("""
                background-color: #12152A;
                border: none;
            """)
        else:
            header.setStyleSheet(f"""
                background-color: {colors.BG_PRIMARY};
                border: none;
            """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(24), S.px(8), S.px(24), S.px(8))
        layout.setSpacing(S.px(16))
        header.setLayout(layout)

        title_section = QVBoxLayout()
        title_section.setSpacing(2)
        title_section.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_section.addWidget(title)

        subtitle = QLabel("System performance overview")
        subtitle.setFont(QFont("Segoe UI", S.font_pt(10)))
        subtitle.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        title_section.addWidget(subtitle)
        layout.addLayout(title_section)

        layout.addStretch()

        status_layout = QHBoxLayout()
        status_layout.setSpacing(S.px(12))
        status_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        uptime_block = QFrame()
        uptime_block.setStyleSheet(f"""
            background-color: {colors.BG_CARD};
            border: none;
            border-radius: {S.px(8)}px;
        """)
        uptime_layout = QVBoxLayout()
        uptime_layout.setSpacing(0)
        uptime_layout.setContentsMargins(S.px(12), S.px(6), S.px(12), S.px(6))
        uptime_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        uptime_block.setLayout(uptime_layout)

        self._uptime_val = QLabel("0m")
        self._uptime_val.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        self._uptime_val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        uptime_layout.addWidget(self._uptime_val)

        uptime_lbl = QLabel("Uptime")
        uptime_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        uptime_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        uptime_layout.addWidget(uptime_lbl)
        status_layout.addWidget(uptime_block)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setMinimumHeight(S.px(28))
        sep.setMaximumHeight(S.px(36))
        sep.setStyleSheet("background-color: transparent;")
        status_layout.addWidget(sep)

        os_block = QFrame()
        os_block.setStyleSheet(f"""
            background-color: {colors.BG_CARD};
            border: none;
            border-radius: {S.px(8)}px;
        """)
        os_layout = QVBoxLayout()
        os_layout.setSpacing(0)
        os_layout.setContentsMargins(S.px(12), S.px(6), S.px(12), S.px(6))
        os_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        os_block.setLayout(os_layout)

        os_val = QLabel(self._short_os())
        os_val.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        os_val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        os_layout.addWidget(os_val)

        os_lbl = QLabel("OS")
        os_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        os_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        os_layout.addWidget(os_lbl)
        status_layout.addWidget(os_block)

        layout.addLayout(status_layout)
        return header

    def _create_metrics_row(self):
        colors = theme_manager.colors
        row = QFrame()
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QGridLayout()
        layout.setSpacing(S.px(12))
        layout.setContentsMargins(0, 0, 0, 0)
        row.setLayout(layout)

        cpu_card = GlassMetricCard("CPU Load", "🖥", colors.ACCENT_GREEN)
        cpu_card.set_value("--", "Loading...")
        self._cpu_card = cpu_card
        layout.addWidget(cpu_card, 0, 0)

        gpu_card = GlassMetricCard("GPU Load", "🎮", colors.ACCENT_PURPLE)
        gpu_card.set_value("--", "Loading...")
        self._gpu_card = gpu_card
        layout.addWidget(gpu_card, 0, 1)

        ram_card = GlassMetricCard("Memory", "💾", colors.ACCENT_BLUE)
        ram_card.set_value("--", "Loading...")
        self._ram_card = ram_card
        layout.addWidget(ram_card, 0, 2)

        net_card = GlassMetricCard("Network", "📶", colors.ACCENT_CYAN)
        net_card.set_value("0.0 / 0.0", "Down / Up Mbps")
        self._net_card = net_card
        layout.addWidget(net_card, 1, 0)

        disk_card = GlassMetricCard("Disk Activity", "💿", colors.ACCENT_ORANGE)
        disk_card.set_value("-- / --", "R/W MB/s")
        self._disk_card = disk_card
        layout.addWidget(disk_card, 1, 1)

        temp_card = GlassMetricCard("Temperature", "🌡", colors.ACCENT_RED)
        temp_card.set_value("--°C", "CPU temp")
        self._temp_card = temp_card
        layout.addWidget(temp_card, 1, 2)

        return row

    def _create_charts_section(self):
        colors = theme_manager.colors
        section = QFrame()
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if theme_manager.current_theme == "heimdal":
            section.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
            """)
        else:
            section.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        layout.setSpacing(S.px(12))
        section.setLayout(layout)

        cpu_chart = GlassChartPanel("CPU Usage", colors.ACCENT_GREEN)
        self._cpu_sparkline = cpu_chart._sparkline
        layout.addWidget(cpu_chart, stretch=1)

        ram_chart = GlassChartPanel("Memory Usage", colors.ACCENT_BLUE)
        self._ram_sparkline = ram_chart._sparkline
        layout.addWidget(ram_chart, stretch=1)

        net_chart = GlassChartPanel("Network Traffic", colors.ACCENT_CYAN)
        self._net_sparkline = net_chart._sparkline
        layout.addWidget(net_chart, stretch=1)

        gpu_chart = GlassChartPanel("GPU Load", colors.ACCENT_PURPLE)
        self._gpu_sparkline = gpu_chart._sparkline
        layout.addWidget(gpu_chart, stretch=1)

        return section

    def _create_info_row(self):
        row = QFrame()
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QHBoxLayout()
        layout.setSpacing(S.px(12))
        row.setLayout(layout)

        sysinfo_panel = self._create_sysinfo_panel()
        layout.addWidget(sysinfo_panel, stretch=1)

        storage_panel = GlassStoragePanel()
        self._storage_panel = storage_panel
        layout.addWidget(storage_panel, stretch=1)

        return row

    def _create_sysinfo_panel(self):
        colors = theme_manager.colors
        panel = GlassInfoPanel("System Information")

        panel.add_info_row("Processor", self._get_cpu_display(), colors.ACCENT_BLUE)
        panel.add_info_row("Graphics", self._get_gpu_display(), colors.ACCENT_PURPLE)
        panel.add_info_row("Memory", self._get_ram_display(), colors.ACCENT_GREEN)
        panel.add_info_row("Operating System", self._short_os(), colors.TEXT_SECONDARY)
        panel.add_info_row("Architecture", platform.machine(), colors.TEXT_MUTED)

        return panel

    def _start_timers(self):
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)
        self._uptime_timer.start(1000)

    def _update_uptime(self):
        self._uptime_seconds = int(time.time() - self._start_time)
        self._uptime_val.setText(self._format_uptime(self._uptime_seconds))

    def _format_uptime(self, seconds):
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def _short_os(self):
        p = platform.platform()
        if "Windows" in p:
            return "Windows " + platform.win32_ver()[0]
        return p

    def _short_cpu(self):
        cpu = platform.processor()
        if not cpu:
            return "Unknown"
        if len(cpu) > 28:
            return cpu[:28] + "..."
        return cpu

    def _get_cpu_name(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'cpu_name' in self._system_info_cache:
            return self._system_info_cache['cpu_name']
        cpu = platform.processor()
        if cpu:
            self._system_info_cache['cpu_name'] = cpu
            self._system_info_cache_time = now
            return cpu
        return None

    def _short_gpu(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'gpu_name' in self._system_info_cache:
            return self._system_info_cache['gpu_name']
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name | Select-Object -First 1"],
                capture_output=True, text=True, timeout=3
            )
            if result.stdout.strip():
                name = result.stdout.strip()
                if len(name) > 24:
                    name = name[:24] + "..."
                self._system_info_cache['gpu_name'] = name
                self._system_info_cache_time = now
                return name
        except Exception:
            pass
        return "N/A"

    def _get_cpu_display(self):
        cpu = self._get_cpu_name()
        if not cpu:
            cpu = platform.processor()
        if not cpu:
            return "Unknown"
        if len(cpu) > 40:
            return cpu[:40] + "..."
        return cpu

    def _get_gpu_display(self):
        gpu = self._short_gpu()
        if not gpu or gpu == "N/A":
            return "Not detected"
        return gpu

    def _get_ram_display(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'ram_info' in self._system_info_cache:
            return self._system_info_cache['ram_info']
        try:
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3))
            from data.memory import get_ram_type
            ram_type = get_ram_type()
            result = f"{total_gb} GB {ram_type}" if ram_type else f"{total_gb} GB"
            self._system_info_cache['ram_info'] = result
            self._system_info_cache_time = now
            return result
        except Exception:
            return "Unknown"

    def update_data(self, data):
        """Called by MainWindow whenever new data arrives"""
        self._last_data = data

        if 'cpu' in data:
            cpu = data['cpu']
            pct = cpu.get('percent', 0)
            self._cpu_card.set_value(f"{pct:.0f}%", f"{pct:.1f}% utilization")
            self._cpu_card.push_sparkline(pct)
            self._cpu_sparkline.push(pct)

        if 'gpu' in data:
            gpu = data['gpu']
            if gpu.get('available'):
                load = gpu.get('load')
                if load is not None:
                    self._gpu_card.set_value(f"{load:.0f}%", "GPU load")
                    self._gpu_card.push_sparkline(load)
                    self._gpu_sparkline.push(load)

        if 'memory' in data:
            mem = data['memory']
            pct = mem.get('percent', 0)
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            self._ram_card.set_value(f"{used_gb:.1f} GB", f"{pct:.0f}% of {total_gb:.0f} GB")
            self._ram_card.push_sparkline(pct)
            self._ram_sparkline.push(pct)

        if 'network' in data:
            net = data['network']
            bytes_sent = net.get('bytes_sent', 0)
            bytes_recv = net.get('bytes_recv', 0)

            if self._last_net:
                dt = 1.0
                down_speed = (bytes_recv - self._last_net[0]) / dt / 1e6
                up_speed = (bytes_sent - self._last_net[1]) / dt / 1e6

                self._net_down_mbps = max(0, down_speed)
                self._net_up_mbps = max(0, up_speed)

                self._net_card.set_value(
                    f"{self._net_down_mbps:.1f} / {self._net_up_mbps:.1f}",
                    "Down / Up Mbps"
                )
                self._net_sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

            self._last_net = (bytes_sent, bytes_recv)

        if 'disk' in data:
            disk = data['disk']
            read_speed = disk.get('read_speed', 0)
            write_speed = disk.get('write_speed', 0)
            self._disk_card.set_value(
                f"{read_speed:.0f} / {write_speed:.0f}",
                "R/W MB/s"
            )

        if 'gpu' in data:
            gpu = data['gpu']
            temp = gpu.get('temperature')
            if temp is not None:
                self._temp_card.set_value(f"{temp:.0f}°C", "GPU temp")
                self._temp_card.push_sparkline(temp)

        if 'disk' in data:
            partitions = data['disk'].get('partitions', [])
            if partitions:
                self._storage_panel.update_drives(partitions)
