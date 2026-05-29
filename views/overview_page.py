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
    QScrollArea, QProgressBar, QPushButton, QGridLayout, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QGradient

from widgets.donut_gauge import DonutGauge
from widgets.sparkline import SparklineWidget
from widgets.responsive import CollapsiblePanel, ResponsiveGridLayout
from styles.theme import theme_manager
from scaler import S, ScaleMixin, LayoutMode


class GlassMetricCard(QFrame):
    """Premium glass metric card - responsive with minimum sizes"""

    def __init__(self, title: str, icon: str, color: str = None, parent=None):
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

    def __init__(self, title: str, color: str = None, parent=None):
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

    def add_info_row(self, label: str, value: str, color: str = None):
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


class GlassStoragePanel(QFrame):
    """Premium glass storage panel - responsive"""

    def __init__(self, parent=None):
        super().__init__(parent)
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

        header = QHBoxLayout()
        header.setSpacing(S.px(8))

        title = QLabel("Storage Drives")
        title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        view_all_btn = QPushButton("View all →")
        view_all_btn.setFont(QFont("Segoe UI", S.font_pt(9)))
        view_all_btn.setMinimumHeight(S.px(24))
        view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_btn.clicked.connect(self._show_all_drives)
        view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_SECONDARY};
                border: none;
                border-radius: {S.px(6)}px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors.ACCENT_ORANGE};
                color: white;
            }}
        """)
        header.addWidget(view_all_btn)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: transparent;")
        layout.addWidget(sep)

        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(S.px(6))
        layout.addLayout(self._storage_container)

    def update_drives(self, partitions):
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        colors = theme_manager.colors

        if not partitions:
            placeholder = QLabel("No drives detected")
            placeholder.setFont(QFont("Segoe UI", S.font_pt(11)))
            placeholder.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._storage_container.addWidget(placeholder)
            return

        for partition in partitions:
            if not partition.get('fstype'):
                continue

            drive_letter = partition.get('device', '')
            mountpoint = partition.get('mountpoint', '')
            total_gb = partition.get('total', 0) / (1024**3)
            used_gb = partition.get('used', 0) / (1024**3)
            pct = partition.get('percent', 0)

            pct_color = colors.ACCENT_GREEN if pct < 75 else colors.ACCENT_ORANGE if pct < 90 else colors.ACCENT_RED

            drive_card = QFrame()
            drive_card.setStyleSheet(f"""
                background-color: {colors.BG_SECONDARY};
                border-radius: {S.px(8)}px;
                padding: 4px;
            """)

            drive_layout = QHBoxLayout()
            drive_layout.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
            drive_layout.setSpacing(S.px(10))
            drive_card.setLayout(drive_layout)

            letter = QLabel(drive_letter.replace("\\", "") if drive_letter else "?")
            letter.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            letter.setStyleSheet(f"color: white; background: {pct_color}; padding: 3px 8px; border-radius: {S.px(5)}px;")
            letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter.setMinimumWidth(S.px(30))
            drive_layout.addWidget(letter)

            info = QVBoxLayout()
            info.setSpacing(2)

            name_lbl = QLabel(mountpoint if mountpoint else "Local Disk")
            name_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
            name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
            info.addWidget(name_lbl)

            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setMinimumHeight(5)
            bar.setMaximumHeight(7)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {colors.BG_PRIMARY};
                    border: none;
                    border-radius: {S.px(3)}px;
                }}
                QProgressBar::chunk {{
                    background-color: {pct_color};
                    border-radius: {S.px(3)}px;
                }}
            """)
            info.addWidget(bar)
            drive_layout.addLayout(info, stretch=1)

            usage_lbl = QLabel(f"{used_gb:.0f}/{total_gb:.0f} GB")
            usage_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
            usage_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            usage_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            usage_lbl.setMinimumWidth(S.px(60))
            drive_layout.addWidget(usage_lbl)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            pct_lbl.setMinimumWidth(S.px(35))
            drive_layout.addWidget(pct_lbl)

            self._storage_container.addWidget(drive_card)

    def _show_all_drives(self):
        from PyQt6.QtWidgets import QDialog

        colors = theme_manager.colors
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setMinimumSize(S.px(550), S.px(400))
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.BG_PRIMARY};
                color: {colors.TEXT_PRIMARY};
            }}
        """)

        drag_pos = [None]

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                drag_pos[0] = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == Qt.MouseButton.LeftButton and drag_pos[0]:
                dialog.move(event.globalPos() - drag_pos[0])
                event.accept()

        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                drag_pos[0] = None
                event.accept()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(S.px(16))
        main_layout.setContentsMargins(S.px(20), S.px(20), S.px(20), S.px(20))
        dialog.setLayout(main_layout)

        header = QFrame()
        header.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: {S.px(8)}px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(S.px(16), S.px(10), S.px(10), S.px(10))
        header.setLayout(header_layout)
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("Storage Drives")
        title.setFont(QFont("Segoe UI", S.font_pt(14), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFont(QFont("Segoe UI", 14))
        close_btn.setFixedSize(S.px(28), S.px(28))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.TEXT_MUTED};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        header_layout.addWidget(close_btn)
        main_layout.addWidget(header)

        drives_layout = QVBoxLayout()
        drives_layout.setSpacing(S.px(12))

        for partition in psutil.disk_partitions():
            if not partition.fstype:
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue

            drive_letter = partition.device
            mountpoint = partition.mountpoint
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            pct = usage.percent

            pct_color = colors.ACCENT_GREEN if pct < 75 else colors.ACCENT_ORANGE if pct < 90 else colors.ACCENT_RED

            drive_card = QFrame()
            drive_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(10)}px;
                }}
            """)
            drive_layout = QHBoxLayout()
            drive_layout.setSpacing(S.px(16))
            drive_layout.setContentsMargins(S.px(14), S.px(14), S.px(14), S.px(14))
            drive_card.setLayout(drive_layout)

            letter = QLabel(drive_letter.replace("\\", ""))
            letter.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
            letter.setStyleSheet(f"color: {pct_color}; background: transparent;")
            letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter.setMinimumSize(S.px(40), S.px(40))
            drive_layout.addWidget(letter)

            info = QVBoxLayout()
            info.setSpacing(S.px(6))

            name = QLabel(mountpoint if mountpoint else drive_letter)
            name.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
            name.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
            info.addWidget(name)

            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setMinimumHeight(8)
            bar.setMaximumHeight(10)
            bar.setTextVisible(False)
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

            stats = QHBoxLayout()
            used_lbl = QLabel(f"{used_gb:.1f} GB used")
            used_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
            used_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
            stats.addWidget(used_lbl)
            stats.addStretch()
            free_lbl = QLabel(f"{free_gb:.1f} GB free")
            free_lbl.setFont(QFont("Segoe UI", S.font_pt(9)))
            free_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            stats.addWidget(free_lbl)
            info.addLayout(stats)

            drive_layout.addLayout(info, stretch=1)

            pct_box = QFrame()
            pct_box.setStyleSheet(f"background-color: {colors.BG_SECONDARY}; border-radius: {S.px(8)}px;")
            pct_layout = QVBoxLayout()
            pct_layout.setSpacing(1)
            pct_layout.setContentsMargins(S.px(12), S.px(6), S.px(12), S.px(6))
            pct_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_box.setLayout(pct_layout)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
            pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(pct_lbl)

            used_lbl2 = QLabel("used")
            used_lbl2.setFont(QFont("Segoe UI", S.font_pt(8)))
            used_lbl2.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            used_lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(used_lbl2)

            drive_layout.addWidget(pct_box)
            drives_layout.addWidget(drive_card)

        main_layout.addLayout(drives_layout)

        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", S.font_pt(10)))
        close_btn.setMinimumHeight(S.px(32))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: {S.px(6)}px;
                padding: 6px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3185f0;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

        dialog.exec()


class OverviewPage(QWidget, ScaleMixin):
    """Premium glass overview dashboard - responsive with adaptive grid"""

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0
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
        self._rebuild_styles()

    def on_scale_changed(self, factor: float):
        self._rebuild_styles()

    def on_layout_mode_changed(self, mode):
        self._rebuild_styles()

    def _rebuild_styles(self):
        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        if hasattr(self, '_main_scroll'):
            self._main_scroll.setStyleSheet(f"""
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

    def _setup_ui(self):
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
        except:
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
        colors = theme_manager.colors

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
            self._net_down_mbps = max(0, net.get('download_speed', 0)) / 1e6
            self._net_up_mbps   = max(0, net.get('upload_speed',   0)) / 1e6
            self._net_card.set_value(
                f"{self._net_down_mbps:.1f} / {self._net_up_mbps:.1f}",
                "Down / Up Mbps"
            )
            self._net_sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

        if 'disk' in data:
            disk = data['disk']
            read_mb  = max(0, disk.get('read_rate',  0)) / 1_048_576
            write_mb = max(0, disk.get('write_rate', 0)) / 1_048_576
            self._disk_card.set_value(
                f"{read_mb:.1f} / {write_mb:.1f}",
                "R/W MB/s"
            )

        if 'gpu' in data:
            gpu = data['gpu']
            temp = gpu.get('temperature')
            if temp is not None:
                self._temp_card.set_value(f"{temp:.0f}°C", "GPU temp")
                self._temp_card.push_sparkline(temp)

        if 'partitions' in data:
            self._storage_panel.update_drives(data['partitions'])