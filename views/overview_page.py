"""
Overview Page - Main dashboard with system overview
Professional enterprise-grade design with clean metrics and real-time data.
"""
import platform
import time
import psutil
import subprocess
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QGradient

from widgets.donut_gauge import DonutGauge
from widgets.sparkline import SparklineWidget
from styles.theme import theme_manager
from scaler import S, ScaleMixin


class MetricCard(QFrame):
    """Professional metric card with icon, value, and trend"""

    def __init__(self, title: str, icon: str, color: str = None, parent=None):
        super().__init__(parent)
        self._color = color  # None = use theme ACCENT_GREEN
        self._title = title
        self._icon = icon
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        card_color = self._color or colors.ACCENT_GREEN

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel(self._icon)
        icon_label.setFont(QFont("Segoe UI", 16))
        icon_label.setStyleSheet(f"color: {card_color}; background: transparent;")
        header.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._value_label)

        # Subtitle / status
        self._subtitle_label = QLabel("")
        self._subtitle_label.setFont(QFont("Segoe UI", 10))
        self._subtitle_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._subtitle_label)

        # Sparkline
        self._sparkline = SparklineWidget(colors=[card_color])
        self._sparkline.setFixedHeight(40)
        layout.addWidget(self._sparkline)

    def set_value(self, value: str, subtitle: str = ""):
        self._value_label.setText(value)
        self._subtitle_label.setText(subtitle)

    def set_color(self, color: str):
        self._color = color

    def push_sparkline(self, value: float):
        self._sparkline.push(value)


class QuickStat(QFrame):
    """Compact quick stat display"""

    def __init__(self, label: str, value: str, color: str = None, parent=None):
        super().__init__(parent)
        self._color = color  # None = use theme ACCENT_GREEN
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._apply_styles()
        layout.addWidget(self._value_label)

        self._label_label = QLabel(label)
        self._label_label.setFont(QFont("Segoe UI", 10))
        self._apply_styles()
        layout.addWidget(self._label_label)

        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._apply_styles()

    def _apply_styles(self):
        c = theme_manager.colors
        value_color = self._color or c.ACCENT_GREEN
        self._value_label.setStyleSheet(f"color: {value_color}; background: transparent;")
        self._label_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")

    def set_value(self, value: str):
        self._value_label.setText(value)


class SystemInfoRow(QFrame):
    """Single row in system info panel"""

    def __init__(self, label: str, value: str, color: str = None, parent=None):
        super().__init__(parent)
        self._color = color  # None = use theme ACCENT_GREEN
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(12)
        self.setLayout(layout)

        self._indicator = QFrame()
        self._indicator.setFixedSize(3, 18)
        layout.addWidget(self._indicator)

        self._lbl = QLabel(label)
        self._lbl.setFont(QFont("Segoe UI", 11))
        self._lbl.setMinimumWidth(90)
        layout.addWidget(self._lbl)

        self._val_lbl = QLabel(value)
        self._val_lbl.setFont(QFont("Segoe UI", 11))
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._val_lbl, stretch=1)

        self._apply_styles()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._apply_styles()

    def _apply_styles(self):
        c = theme_manager.colors
        indicator_color = self._color or c.ACCENT_GREEN
        self._indicator.setStyleSheet(f"background-color: {indicator_color}; border-radius: 1px;")
        self._lbl.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        self._val_lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")


class StorageDriveRow(QFrame):
    """Single storage drive display row"""

    def __init__(self, letter: str, mountpoint: str, used_gb: float, total_gb: float, pct: float, parent=None):
        super().__init__(parent)
        self._letter = letter
        self._mountpoint = mountpoint
        self._used_gb = used_gb
        self._total_gb = total_gb
        self._pct = pct
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _get_pct_color(self):
        c = theme_manager.colors
        if self._pct < 75:
            return c.ACCENT_GREEN
        elif self._pct < 90:
            return c.ACCENT_ORANGE
        else:
            return c.ACCENT_RED

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()

    def _apply_theme(self):
        c = theme_manager.colors
        pct_color = self._get_pct_color()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_SECONDARY};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        self._badge.setStyleSheet(f"""
            background-color: {pct_color};
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
        """)
        self._name_lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_PRIMARY};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: 3px;
            }}
        """)
        self._usage_lbl.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        self._pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")

    def _setup_ui(self):
        c = theme_manager.colors
        pct_color = self._get_pct_color()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_SECONDARY};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        self.setLayout(layout)

        # Drive letter badge
        self._badge = QLabel(self._letter)
        self._badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._badge.setStyleSheet(f"""
            background-color: {pct_color};
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
        """)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setFixedWidth(36)
        layout.addWidget(self._badge)

        # Info
        info = QVBoxLayout()
        info.setSpacing(4)

        self._name_lbl = QLabel(self._mountpoint if self._mountpoint else "Local Disk")
        self._name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self._name_lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        info.addWidget(self._name_lbl)

        self._bar = QProgressBar()
        self._bar.setValue(int(self._pct))
        self._bar.setFixedHeight(6)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_PRIMARY};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: 3px;
            }}
        """)
        info.addWidget(self._bar)
        layout.addLayout(info, stretch=1)

        # Usage text
        self._usage_lbl = QLabel(f"{self._used_gb:.0f}/{self._total_gb:.0f} GB")
        self._usage_lbl.setFont(QFont("Segoe UI", 10))
        self._usage_lbl.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        self._usage_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._usage_lbl.setMinimumWidth(70)
        layout.addWidget(self._usage_lbl)

        # Percentage
        self._pct_lbl = QLabel(f"{self._pct:.0f}%")
        self._pct_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._pct_lbl.setMinimumWidth(40)
        layout.addWidget(self._pct_lbl)


class OverviewPage(QWidget, ScaleMixin):
    """Main overview dashboard - professional enterprise design."""

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0
        self._last_net = None
        self._net_down_mbps = 0.0
        self._net_up_mbps = 0.0
        self._cpu_history = deque(maxlen=60)
        self._gpu_history = deque(maxlen=60)
        self._ram_history = deque(maxlen=60)
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

    def _rebuild_styles(self):
        """Rebuild all dynamic styles when theme changes."""
        colors = theme_manager.colors

        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")

        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {colors.BG_PRIMARY}; border: none;")

        for card in getattr(self, '_metric_cards', []):
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: 1px solid {colors.BORDER};
                    border-radius: 12px;
                }}
            """)

    def _setup_ui(self):
        """Setup main layout."""
        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Header
        self._header = self._create_header()
        main_layout.addWidget(self._header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.BG_PRIMARY};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {colors.BG_PRIMARY};
            }}
        """)
        main_layout.addWidget(scroll, stretch=1)

        content = QWidget()
        content.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(28, 20, 28, 28)
        content_layout.setSpacing(20)
        content.setLayout(content_layout)
        scroll.setWidget(content)

        # Metric cards row
        metrics_row = self._create_metrics_row()
        content_layout.addWidget(metrics_row)

        # Charts section
        charts_section = self._create_charts_section()
        content_layout.addWidget(charts_section)

        # Info panels
        info_row = self._create_info_row()
        content_layout.addWidget(info_row)

        content_layout.addStretch()

    def _create_header(self):
        """Create page header with title, uptime, and system info."""
        colors = theme_manager.colors
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet(f"background-color: {colors.BG_PRIMARY}; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(24)
        header.setLayout(layout)

        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title_section.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_section.addWidget(title)

        subtitle = QLabel("System performance overview")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        title_section.addWidget(subtitle)
        layout.addLayout(title_section)

        layout.addStretch()

        # Status indicators
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Uptime
        uptime_block = QFrame()
        uptime_block.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 8px;")
        uptime_layout = QVBoxLayout()
        uptime_layout.setSpacing(0)
        uptime_layout.setContentsMargins(16, 8, 16, 8)
        uptime_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        uptime_block.setLayout(uptime_layout)

        self._uptime_val = QLabel("0m")
        self._uptime_val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._uptime_val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        uptime_layout.addWidget(self._uptime_val)

        uptime_lbl = QLabel("Uptime")
        uptime_lbl.setFont(QFont("Segoe UI", 9))
        uptime_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        uptime_layout.addWidget(uptime_lbl)
        status_layout.addWidget(uptime_block)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(40)
        sep.setStyleSheet(f"background-color: {colors.BORDER};")
        status_layout.addWidget(sep)

        # OS
        os_block = QFrame()
        os_block.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 8px;")
        os_layout = QVBoxLayout()
        os_layout.setSpacing(0)
        os_layout.setContentsMargins(16, 8, 16, 8)
        os_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        os_block.setLayout(os_layout)

        os_val = QLabel(self._short_os())
        os_val.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        os_val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        os_layout.addWidget(os_val)

        os_lbl = QLabel("Operating System")
        os_lbl.setFont(QFont("Segoe UI", 9))
        os_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        os_layout.addWidget(os_lbl)
        status_layout.addWidget(os_block)

        # Separator
        sep2 = QFrame()
        sep2.setFixedWidth(1)
        sep2.setFixedHeight(40)
        sep2.setStyleSheet(f"background-color: {colors.BORDER};")
        status_layout.addWidget(sep2)

        # CPU
        cpu_block = QFrame()
        cpu_block.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 8px;")
        cpu_layout = QVBoxLayout()
        cpu_layout.setSpacing(0)
        cpu_layout.setContentsMargins(16, 8, 16, 8)
        cpu_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cpu_block.setLayout(cpu_layout)

        self._cpu_name_val = QLabel(self._short_cpu()[:20])
        self._cpu_name_val.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._cpu_name_val.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        cpu_layout.addWidget(self._cpu_name_val)

        cpu_lbl = QLabel("Processor")
        cpu_lbl.setFont(QFont("Segoe UI", 9))
        cpu_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        cpu_layout.addWidget(cpu_lbl)
        status_layout.addWidget(cpu_block)

        layout.addLayout(status_layout)
        return header

    def _create_metrics_row(self):
        """Create the top metric cards row."""
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(16)
        row.setLayout(layout)

        self._metric_cards = []

        # CPU card
        cpu_card = MetricCard("CPU Load", "🖥")
        cpu_card.set_value("--", "Loading...")
        self._metric_cards.append(cpu_card)
        layout.addWidget(cpu_card, stretch=1)

        # GPU card
        gpu_card = MetricCard("GPU Load", "🎮")
        gpu_card.set_value("--", "Loading...")
        self._metric_cards.append(gpu_card)
        layout.addWidget(gpu_card, stretch=1)

        # RAM card
        ram_card = MetricCard("Memory", "💾")
        ram_card.set_value("--", "Loading...")
        self._metric_cards.append(ram_card)
        layout.addWidget(ram_card, stretch=1)

        # Network card
        net_card = MetricCard("Network", "📶")
        net_card.set_value("0.0 / 0.0", "Down / Up Mbps")
        self._metric_cards.append(net_card)
        layout.addWidget(net_card, stretch=1)

        # Disk card
        disk_card = MetricCard("Disk Activity", "💿")
        disk_card.set_value("-- / --", "R/W MB/s")
        self._metric_cards.append(disk_card)
        layout.addWidget(disk_card, stretch=1)

        return row

    def _create_charts_section(self):
        """Create charts section with sparklines."""
        section = QFrame()
        colors = theme_manager.colors
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(20)
        section.setLayout(layout)

        # CPU Chart
        cpu_chart = self._create_chart_panel("CPU Usage")
        self._cpu_sparkline = cpu_chart.sparkline
        layout.addWidget(cpu_chart, stretch=1)

        # RAM Chart
        ram_chart = self._create_chart_panel("Memory Usage")
        self._ram_sparkline = ram_chart.sparkline
        layout.addWidget(ram_chart, stretch=1)

        # Network Chart
        net_chart = self._create_chart_panel("Network Traffic")
        self._net_sparkline = net_chart.sparkline
        layout.addWidget(net_chart, stretch=1)

        # GPU Chart
        gpu_chart = self._create_chart_panel("GPU Load", color=colors.ACCENT_PURPLE)
        self._gpu_sparkline = gpu_chart.sparkline
        layout.addWidget(gpu_chart, stretch=1)

        return section

    def _create_chart_panel(self, title: str, color: str = None):
        """Create a single chart panel with title and sparkline."""
        colors = theme_manager.colors
        panel_color = color or colors.ACCENT_GREEN
        panel = QFrame()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        panel.setLayout(layout)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        title_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_lbl)

        sparkline = SparklineWidget(colors=[panel_color])
        sparkline.setFixedHeight(80)
        layout.addWidget(sparkline)

        panel.sparkline = sparkline
        return panel

    def _create_info_row(self):
        """Create system info and storage panels row."""
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(16)
        row.setLayout(layout)

        # System Info panel
        sysinfo_panel = self._create_sysinfo_panel()
        layout.addWidget(sysinfo_panel, stretch=1)

        # Storage panel
        storage_panel = self._create_storage_panel()
        layout.addWidget(storage_panel, stretch=1)

        return row

    def _create_sysinfo_panel(self):
        """System information panel."""
        colors = theme_manager.colors
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        panel.setLayout(layout)

        # Title
        title = QLabel("System Information")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colors.BORDER};")
        layout.addWidget(sep)

        # Info rows
        specs = QVBoxLayout()
        specs.setSpacing(0)

        cpu_row = SystemInfoRow("Processor", self._get_cpu_display())
        specs.addWidget(cpu_row)

        gpu_row = SystemInfoRow("Graphics", self._get_gpu_display())
        specs.addWidget(gpu_row)

        ram_row = SystemInfoRow("Memory", self._get_ram_display())
        specs.addWidget(ram_row)

        os_row = SystemInfoRow("Operating System", self._short_os())
        specs.addWidget(os_row)

        arch_row = SystemInfoRow("Architecture", platform.machine())
        specs.addWidget(arch_row)

        layout.addLayout(specs)
        layout.addStretch()

        return panel

    def _create_storage_panel(self):
        """Storage drives panel."""
        colors = theme_manager.colors
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        panel.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Storage Drives")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(title)

        header.addStretch()

        view_all_btn = QPushButton("View all →")
        view_all_btn.setFont(QFont("Segoe UI", 10))
        view_all_btn.setFixedHeight(26)
        view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_btn.clicked.connect(self._show_all_drives)
        view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_SECONDARY};
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {colors.ACCENT_ORANGE};
                color: white;
            }}
        """)
        header.addWidget(view_all_btn)
        layout.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colors.BORDER};")
        layout.addWidget(sep)

        # Storage container
        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(8)
        layout.addLayout(self._storage_container)

        self._update_storage_display([])

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
        # Use platform.processor() directly - it's instant and sufficient for display
        cpu = platform.processor()
        if not cpu:
            return "Unknown"
        if len(cpu) > 28:
            return cpu[:28] + "..."
        return cpu

    def _get_cpu_name(self):
        # Use platform.processor() directly - instant, no WMI needed
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
        # Use WMI directly for GPU name - faster than GPUtil
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

            ram_type = "Unknown"
            mem_obj = None
            try:
                import wmi
                w = wmi.WMI()
                for mem_obj in w.Win32_PhysicalMemory():
                    if hasattr(mem_obj, 'MemoryType') and mem_obj.MemoryType:
                        mem_type = int(mem_obj.MemoryType)
                        type_map = {20: "DDR5", 21: "DDR4", 22: "DDR3", 24: "DDR2"}
                        ram_type = type_map.get(mem_type, "Unknown")
                        if ram_type != "Unknown":
                            break
                if ram_type == "Unknown" and mem_obj is not None and hasattr(mem_obj, 'Speed') and mem_obj.Speed:
                    speed = int(mem_obj.Speed)
                    if speed >= 6400:
                        ram_type = "DDR5"
                    elif speed >= 3200:
                        ram_type = "DDR4"
                    elif speed >= 2133:
                        ram_type = "DDR3"
            except:
                pass

            if ram_type != "Unknown":
                result = f"{total_gb} GB {ram_type}"
            else:
                result = f"{total_gb} GB"

            self._system_info_cache['ram_info'] = result
            self._system_info_cache_time = now
            return result
        except:
            return "Unknown"

    def _update_storage_display(self, partitions):
        """Update storage drive display."""
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not partitions:
            placeholder = QLabel("No drives detected")
            placeholder.setFont(QFont("Segoe UI", 12))
            placeholder.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
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

            letter = drive_letter.replace("\\", "") if drive_letter else "?"
            row = StorageDriveRow(letter, mountpoint, used_gb, total_gb, pct)
            self._storage_container.addWidget(row)

    def _show_all_drives(self):
        """Show all drives dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout as QVBoxLayoutDialog, QHBoxLayout as QHBoxLayoutDialog
        from PyQt6.QtWidgets import QFrame, QLabel, QProgressBar, QPushButton

        colors = theme_manager.colors
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setMinimumSize(650, 450)
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

        main_layout = QVBoxLayoutDialog()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        dialog.setLayout(main_layout)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {colors.BG_CARD}; border-radius: 8px;")
        header_layout = QHBoxLayoutDialog()
        header_layout.setContentsMargins(20, 12, 12, 12)
        header.setLayout(header_layout)
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("Storage Drives")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFont(QFont("Segoe UI", 16))
        close_btn.setFixedSize(32, 32)
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

        # Drives
        drives_layout = QVBoxLayoutDialog()
        drives_layout.setSpacing(14)

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

            pct_color = "#238636" if pct < 75 else "#d29922" if pct < 90 else "#da3633"

            drive_card = QFrame()
            drive_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: 1px solid {colors.BORDER};
                    border-radius: 12px;
                }}
            """)
            drive_layout = QHBoxLayoutDialog()
            drive_layout.setSpacing(20)
            drive_layout.setContentsMargins(16, 16, 16, 16)
            drive_card.setLayout(drive_layout)

            # Drive letter
            letter = QLabel(drive_letter.replace("\\", ""))
            letter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            letter.setStyleSheet(f"color: {pct_color}; background: transparent;")
            letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter.setFixedSize(50, 50)
            drive_layout.addWidget(letter)

            # Info
            info = QVBoxLayoutDialog()
            info.setSpacing(8)

            name = QLabel(mountpoint if mountpoint else drive_letter)
            name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            name.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
            info.addWidget(name)

            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setFixedHeight(10)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {colors.BG_PRIMARY};
                    border: none;
                    border-radius: 5px;
                }}
                QProgressBar::chunk {{
                    background-color: {pct_color};
                    border-radius: 5px;
                }}
            """)
            info.addWidget(bar)

            stats = QHBoxLayoutDialog()
            used_lbl = QLabel(f"{used_gb:.1f} GB used")
            used_lbl.setFont(QFont("Segoe UI", 10))
            used_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
            stats.addWidget(used_lbl)
            stats.addStretch()
            free_lbl = QLabel(f"{free_gb:.1f} GB free")
            free_lbl.setFont(QFont("Segoe UI", 10))
            free_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            stats.addWidget(free_lbl)
            info.addLayout(stats)

            drive_layout.addLayout(info, stretch=1)

            # Percentage box
            pct_box = QFrame()
            pct_box.setStyleSheet(f"background-color: {colors.BG_SECONDARY}; border-radius: 10px;")
            pct_layout = QVBoxLayoutDialog()
            pct_layout.setSpacing(2)
            pct_layout.setContentsMargins(16, 8, 16, 8)
            pct_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_box.setLayout(pct_layout)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(pct_lbl)

            used_lbl2 = QLabel("used")
            used_lbl2.setFont(QFont("Segoe UI", 9))
            used_lbl2.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            used_lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(used_lbl2)

            drive_layout.addWidget(pct_box)
            drives_layout.addWidget(drive_card)

        main_layout.addLayout(drives_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 11))
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 28px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3185f0;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    def update_data(self, data):
        """Called by MainWindow whenever new data arrives."""
        self._last_data = data

        colors = theme_manager.colors

        # CPU
        if 'cpu' in data:
            cpu = data['cpu']
            pct = cpu.get('percent', 0)

            self._metric_cards[0].set_value(f"{pct:.0f}%", f"{pct:.1f}% utilization")
            self._metric_cards[0].push_sparkline(pct)
            self._cpu_history.append(pct)
            self._cpu_sparkline.push(pct)

        # GPU
        if 'gpu' in data:
            gpu = data['gpu']
            if gpu.get('available'):
                load = gpu.get('load')
                if load is not None:
                    self._metric_cards[1].set_value(f"{load:.0f}%", f"GPU load")
                    self._metric_cards[1].push_sparkline(load)
                    self._gpu_history.append(load)
                    self._gpu_sparkline.push(load)

        # Memory
        if 'memory' in data:
            mem = data['memory']
            pct = mem.get('percent', 0)
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)

            self._metric_cards[2].set_value(f"{used_gb:.1f} GB", f"{pct:.0f}% of {total_gb:.0f} GB")
            self._metric_cards[2].push_sparkline(pct)
            self._ram_history.append(used_gb)
            self._ram_sparkline.push(pct)

        # Network
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

                self._metric_cards[3].set_value(
                    f"{self._net_down_mbps:.1f} / {self._net_up_mbps:.1f}",
                    "Down / Up Mbps"
                )
                self._net_sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

            self._last_net = (bytes_sent, bytes_recv)

        # Disk
        if 'disk' in data:
            disk = data['disk']
            read_speed = disk.get('read_speed', 0)
            write_speed = disk.get('write_speed', 0)

            self._metric_cards[4].set_value(
                f"{read_speed:.0f} / {write_speed:.0f}",
                "R/W MB/s"
            )

        # Update storage display
        if 'partitions' in data:
            self._update_storage_display(data['partitions'])