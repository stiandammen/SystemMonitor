"""
Overview Page - Main dashboard with system overview
Clean, text-focused design with large visible labels and values.
"""
import platform
import time
import psutil
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient

from widgets.donut_gauge import DonutGauge
from widgets.sparkline import SparklineWidget
from styles.theme import theme_manager
from scaler import S, ScaleMixin


COLORS = {
    'bg_primary': '#0a0e14',
    'bg_card': '#161f2a',
    'bg_deeper': '#0d1117',
    'bg_hover': '#1e2936',
    'border': '#2a3441',
    'text_primary': '#f0f4f8',
    'text_secondary': '#94a3b8',
    'text_muted': '#64748b',
    'accent_blue': '#3b82f6',
    'accent_green': '#10b981',
    'accent_purple': '#8b5cf6',
    'accent_orange': '#f59e0b',
    'accent_cyan': '#06b6d4',
    'accent_red': '#ef4444',
}


class OverviewPage(QWidget, ScaleMixin):
    """Main overview dashboard - text-focused design."""

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

        self._system_info_cache = {}
        self._system_info_cache_time = 0
        self._system_info_cache_ttl = 30

        self._setup_ui()
        self._start_timers()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.scale_connect()

    def set_data_collector(self, collector):
        self._data_collector = collector
        if collector:
            collector.processes_updated.connect(self._on_processes_updated)

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme_colors()

    def on_scale_changed(self, factor: float):
        self._apply_theme_colors()

    def _apply_theme_colors(self):
        """Apply theme colors to COLORS dict."""
        c = theme_manager.colors
        COLORS['bg_primary'] = c.BG_PRIMARY
        COLORS['bg_card'] = c.BG_CARD
        COLORS['bg_deeper'] = c.BG_HOVER
        COLORS['bg_hover'] = c.BG_HOVER
        COLORS['border'] = c.BORDER
        COLORS['text_primary'] = c.TEXT_PRIMARY
        COLORS['text_secondary'] = c.TEXT_SECONDARY
        COLORS['text_muted'] = c.TEXT_MUTED
        COLORS['accent_blue'] = c.ACCENT_BLUE
        COLORS['accent_green'] = c.ACCENT_GREEN
        COLORS['accent_purple'] = c.ACCENT_PURPLE
        COLORS['accent_orange'] = c.ACCENT_ORANGE
        COLORS['accent_cyan'] = c.ACCENT_CYAN
        COLORS['accent_red'] = c.ACCENT_RED

        self._rebuild_styles()

    def _rebuild_styles(self):
        """Rebuild all dynamic styles."""
        # Page background
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        # Header
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {COLORS['bg_primary']}; border: none;")
            self._header_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            self._header_subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")

        # Info blocks
        for block in self._info_blocks:
            block.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
            block.layout().setContentsMargins(16, 8, 16, 8)

        # Resource cards
        for card_key in ['cpu', 'gpu', 'ram', 'disk']:
            card = getattr(self, f'_{card_key}_card', None)
            if card:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_card']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 12px;
                    }}
                """)
                card.layout().setContentsMargins(16, 16, 16, 16)

    def _setup_ui(self):
        """Setup main layout."""
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        self._header = self._create_header()
        layout.addWidget(self._header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_primary']};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)
        layout.addWidget(scroll, stretch=1)

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 20, 24, 24)
        content_layout.setSpacing(16)
        content.setLayout(content_layout)
        scroll.setWidget(content)

        # Resource cards row
        resource_row = self._create_resource_row()
        content_layout.addWidget(resource_row)

        # Detail charts row
        chart_row = self._create_chart_row()
        content_layout.addWidget(chart_row)

        # Info panels row
        info_row = self._create_info_row()
        content_layout.addWidget(info_row)

        content_layout.addStretch()

    def _create_header(self):
        """Create page header with title and system info."""
        header = QFrame()
        header.setFixedHeight(110)
        header.setStyleSheet(f"background-color: {COLORS['bg_primary']}; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(32)
        header.setLayout(layout)

        # Title + Subtitle
        left = QVBoxLayout()
        left.setSpacing(6)
        left.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._header_title = QLabel("Overview")
        self._header_title.setFont(S.font("Segoe UI", 28, QFont.Bold))
        self._header_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        left.addWidget(self._header_title)

        self._header_subtitle = QLabel("Real-time system performance")
        self._header_subtitle.setFont(S.font("Segoe UI", 13))
        self._header_subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        left.addWidget(self._header_subtitle)
        layout.addLayout(left)

        layout.addStretch()

        # Info blocks
        self._info_blocks = []
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        uptime_block = self._create_info_block("Uptime", self._format_uptime(0))
        self._uptime_val = uptime_block._val_label
        info_layout.addWidget(uptime_block)
        self._info_blocks.append(uptime_block)

        info_layout.addWidget(self._create_sep())

        os_block = self._create_info_block("OS", self._short_os())
        info_layout.addWidget(os_block)
        self._info_blocks.append(os_block)

        info_layout.addWidget(self._create_sep())

        cpu_block = self._create_info_block("CPU", self._short_cpu())
        self._cpu_val = cpu_block._val_label
        info_layout.addWidget(cpu_block)
        self._info_blocks.append(cpu_block)

        info_layout.addWidget(self._create_sep())

        gpu_block = self._create_info_block("GPU", self._short_gpu())
        self._gpu_val = gpu_block._val_label
        info_layout.addWidget(gpu_block)
        self._info_blocks.append(gpu_block)

        layout.addLayout(info_layout)
        return header

    def _create_info_block(self, label, value):
        """Create info block with label and value."""
        block = QFrame()
        block.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        block.setLayout(layout)

        lbl = QLabel(label)
        lbl.setFont(S.font("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedHeight(18)
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setFont(S.font("Segoe UI", 14, QFont.Bold))
        val.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        val.setWordWrap(False)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setFixedHeight(22)
        layout.addWidget(val)

        block._val_label = val
        return block

    def _create_sep(self):
        """Create vertical separator."""
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(40)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        return sep

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
        cpu = self._get_cpu_name()
        if not cpu:
            cpu = platform.processor()
        if not cpu:
            return "Unknown"
        if len(cpu) > 32:
            return cpu[:32] + "..."
        return cpu

    def _get_cpu_name(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'cpu_name' in self._system_info_cache:
            return self._system_info_cache['cpu_name']
        try:
            import wmi
            w = wmi.WMI()
            for cpu in w.Win32_Processor():
                self._system_info_cache['cpu_name'] = cpu.Name
                self._system_info_cache_time = now
                return cpu.Name
        except:
            return None

    def _short_gpu(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'gpu_name' in self._system_info_cache:
            return self._system_info_cache['gpu_name']
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                name = gpus[0].name
                if len(name) > 28:
                    return name[:28] + "..."
                return name
        except:
            pass
        return "N/A"

    def _start_timers(self):
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)
        self._uptime_timer.start(1000)

        # Start cpu_percent-intervallet (første kall gir alltid 0.0 i psutil)
        psutil.cpu_percent(percpu=False)
        for proc in psutil.process_iter(['cpu_percent']):
            try:
                proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._refresh_process_list)
        self._process_timer.start(3000)

    def _refresh_process_list(self):
        """Hent og vis aktive prosesser sortert på CPU-bruk."""
        try:
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
                try:
                    if proc.is_running():
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            processes.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)
            self._update_process_list(processes[:6])
        except Exception as e:
            print(f"Process refresh error: {e}")

    def _update_uptime(self):
        self._uptime_seconds = int(time.time() - self._start_time)
        self._uptime_val.setText(self._format_uptime(self._uptime_seconds))

    def _on_processes_updated(self, processes):
        self._processes_cache = processes
        self._update_process_list(processes)

    # ─── Resource Cards Row ────────────────────────────────────────────────────

    def _create_resource_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        self._cpu_card = self._create_resource_card("CPU", COLORS['accent_blue'], "Load", "Temp", "Power")
        self._gpu_card = self._create_resource_card("GPU", COLORS['accent_green'], "Temp", "Fan", "Power")
        self._ram_card = self._create_resource_card("RAM", COLORS['accent_purple'], "Used", "Free", "Type")
        self._disk_card = self._create_resource_card("Disk", COLORS['accent_orange'], "Read", "Write", "Usage")
        self._net_card = self._create_network_card()

        layout.addWidget(self._cpu_card, stretch=1)
        layout.addWidget(self._gpu_card, stretch=1)
        layout.addWidget(self._ram_card, stretch=1)
        layout.addWidget(self._disk_card, stretch=1)
        layout.addWidget(self._net_card, stretch=1)

        return row

    def _create_resource_card(self, title, color, *labels):
        """Create a resource card with gauge, stats and sparkline."""
        card = QFrame()
        card.setMinimumHeight(220)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setFont(S.font("Segoe UI", 15, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title_lbl)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Gauge + Stats
        content = QHBoxLayout()
        content.setSpacing(16)
        content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        gauge = DonutGauge(color=color, size=100)
        content.addWidget(gauge)

        # Stats column
        stats = QVBoxLayout()
        stats.setSpacing(8)
        stats.setAlignment(Qt.AlignmentFlag.AlignTop)

        stat_labels = []
        for lbl_text in labels:
            stat_row = QHBoxLayout()
            stat_row.setSpacing(8)

            name_lbl = QLabel(lbl_text)
            name_lbl.setFont(S.font("Segoe UI", 11))
            name_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            name_lbl.setFixedWidth(50)
            stat_row.addWidget(name_lbl)

            val_lbl = QLabel("--")
            val_lbl.setFont(S.font("Segoe UI", 12, QFont.Bold))
            val_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            stat_row.addWidget(val_lbl)

            stats.addLayout(stat_row)
            stat_labels.append(val_lbl)

        content.addLayout(stats)
        content.addStretch()
        layout.addLayout(content)

        card.gauge = gauge
        card.stats = stat_labels

        return card

    def _create_network_card(self):
        """Create network card with up/down speeds."""
        card = QFrame()
        card.setMinimumHeight(220)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Title
        title_lbl = QLabel("Network")
        title_lbl.setFont(S.font("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Up/Down speeds
        speeds = QHBoxLayout()
        speeds.setSpacing(24)

        # Upload
        up_box = QVBoxLayout()
        up_box.setSpacing(2)
        up_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        up_icon = QLabel("▲")
        up_icon.setFont(S.font("Segoe UI", 14))
        up_icon.setStyleSheet(f"color: {COLORS['accent_cyan']}; background: transparent;")
        up_box.addWidget(up_icon)

        self._net_up_lbl = QLabel("0.0")
        self._net_up_lbl.setFont(S.font("Segoe UI", 26, QFont.Bold))
        self._net_up_lbl.setStyleSheet(f"color: {COLORS['accent_cyan']}; background: transparent;")
        up_box.addWidget(self._net_up_lbl)

        up_unit = QLabel("Mbps up")
        up_unit.setFont(S.font("Segoe UI", 11))
        up_unit.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        up_box.addWidget(up_unit)
        speeds.addLayout(up_box)

        # Divider
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setFixedHeight(50)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        speeds.addWidget(divider)

        # Download
        down_box = QVBoxLayout()
        down_box.setSpacing(2)
        down_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        down_icon = QLabel("▼")
        down_icon.setFont(S.font("Segoe UI", 14))
        down_icon.setStyleSheet(f"color: {COLORS['accent_blue']}; background: transparent;")
        down_box.addWidget(down_icon)

        self._net_down_lbl = QLabel("0.0")
        self._net_down_lbl.setFont(S.font("Segoe UI", 26, QFont.Bold))
        self._net_down_lbl.setStyleSheet(f"color: {COLORS['accent_blue']}; background: transparent;")
        down_box.addWidget(self._net_down_lbl)

        down_unit = QLabel("Mbps down")
        down_unit.setFont(S.font("Segoe UI", 11))
        down_unit.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        down_box.addWidget(down_unit)
        speeds.addLayout(down_box)

        speeds.addStretch()
        layout.addLayout(speeds)

        # Sparkline
        self._net_sparkline = SparklineWidget(colors=[COLORS['accent_cyan'], COLORS['accent_blue']])
        self._net_sparkline.setFixedHeight(55)
        layout.addWidget(self._net_sparkline)

        return card

    # ─── Detail Charts Row ─────────────────────────────────────────────────────

    def _create_chart_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        self._cpu_chart = self._create_detail_chart("CPU", COLORS['accent_blue'])
        self._gpu_chart = self._create_detail_chart("GPU", COLORS['accent_green'])
        self._ram_chart = self._create_detail_chart("RAM", COLORS['accent_purple'])
        self._net_chart = self._create_detail_chart("Network", COLORS['accent_cyan'])

        layout.addWidget(self._cpu_chart, stretch=1)
        layout.addWidget(self._gpu_chart, stretch=1)
        layout.addWidget(self._ram_chart, stretch=1)
        layout.addWidget(self._net_chart, stretch=1)

        return row

    def _create_detail_chart(self, title, color):
        """Create detail chart card with sparkline."""
        card = QFrame()
        card.setMinimumHeight(160)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setFont(S.font("Segoe UI", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Sparkline
        sparkline = SparklineWidget(colors=[color])
        sparkline.setFixedHeight(90)
        layout.addWidget(sparkline)

        card.sparkline = sparkline
        return card

    # ─── Info Panels Row ───────────────────────────────────────────────────────

    def _create_info_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        process_card = self._create_process_card()
        sysinfo_card = self._create_sysinfo_card()
        storage_card = self._create_storage_card()

        layout.addWidget(process_card, stretch=1)
        layout.addWidget(sysinfo_card, stretch=1)
        layout.addWidget(storage_card, stretch=1)

        return row

    def _create_process_card(self):
        """Process list card."""
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("Top Processes")
        title.setFont(S.font("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        badge = QLabel("6")
        badge.setFont(S.font("Segoe UI", 10, QFont.Bold))
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['accent_blue']};
                color: white;
                padding: 2px 10px;
                border-radius: 10px;
            }}
        """)
        header_layout.addWidget(badge)
        layout.addLayout(header_layout)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Column header
        col_header = QHBoxLayout()
        col_header.setContentsMargins(16, 2, 16, 2)
        col_header.setSpacing(0)

        proc_col = QLabel("Process")
        proc_col.setFont(S.font("Segoe UI", 10, QFont.Bold))
        proc_col.setStyleSheet("color: #64748b; background: transparent;")
        col_header.addWidget(proc_col)

        col_header.addStretch()

        cpu_col = QLabel("CPU")
        cpu_col.setFont(S.font("Segoe UI", 10, QFont.Bold))
        cpu_col.setStyleSheet("color: #64748b; background: transparent;")
        cpu_col.setFixedWidth(58)
        cpu_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(cpu_col)

        spacer_col = QLabel("")
        spacer_col.setFixedWidth(14)
        col_header.addWidget(spacer_col)

        ram_col = QLabel("RAM")
        ram_col.setFont(S.font("Segoe UI", 10, QFont.Bold))
        ram_col.setStyleSheet("color: #64748b; background: transparent;")
        ram_col.setFixedWidth(58)
        ram_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_header.addWidget(ram_col)

        layout.addLayout(col_header)

        # Process list
        self._process_list = QVBoxLayout()
        self._process_list.setSpacing(6)
        self._process_rows = []

        for i in range(6):
            row = self._create_process_row("--", "--", "--")
            self._process_list.addWidget(row)
            self._process_rows.append(row)

        layout.addLayout(self._process_list)

        # View all button
        btn = QPushButton("View all →")
        btn.setFont(S.font("Segoe UI", 10))
        btn.setFixedHeight(28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._show_all_processes)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue']};
                color: white;
            }}
        """)
        layout.addWidget(btn)

        return card

    def _create_process_row(self, name, cpu, ram):
        """Single process row."""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)
        row.setLayout(layout)

        name_lbl = QLabel(name)
        name_lbl.setFont(S.font("Segoe UI", 12, QFont.Bold))
        name_lbl.setStyleSheet("color: #f0f4f8; background: transparent;")
        layout.addWidget(name_lbl)
        row._name_lbl = name_lbl

        layout.addStretch()

        cpu_lbl = QLabel(cpu)
        cpu_lbl.setFont(S.font("Segoe UI", 11, QFont.Bold))
        cpu_lbl.setStyleSheet("color: #60a5fa; background: transparent;")
        cpu_lbl.setFixedWidth(58)
        cpu_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(cpu_lbl)
        row._cpu_lbl = cpu_lbl

        divider = QLabel("")
        divider.setFixedWidth(14)
        layout.addWidget(divider)

        ram_lbl = QLabel(ram)
        ram_lbl.setFont(S.font("Segoe UI", 11, QFont.Bold))
        ram_lbl.setStyleSheet("color: #a78bfa; background: transparent;")
        ram_lbl.setFixedWidth(58)
        ram_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(ram_lbl)
        row._ram_lbl = ram_lbl

        return row

    def _update_process_list(self, processes):
        try:
            for i in range(6):
                if i < len(processes):
                    proc = processes[i]
                    name = (proc.get('name') or 'Unknown')[:18]
                    cpu_val = proc.get('cpu_percent')
                    cpu_str = f"{cpu_val:.1f}%" if cpu_val is not None else "--"

                    mem_info = proc.get('memory_info')
                    if mem_info and hasattr(mem_info, 'rss'):
                        mem_pct = (mem_info.rss / psutil.virtual_memory().total) * 100
                        ram_str = f"{mem_pct:.1f}%"
                    else:
                        ram_str = "--"

                    self._process_rows[i]._name_lbl.setText(name)
                    self._process_rows[i]._name_lbl.setStyleSheet("color: #f0f4f8; background: transparent;")
                    self._process_rows[i]._cpu_lbl.setText(cpu_str)
                    self._process_rows[i]._cpu_lbl.setStyleSheet("color: #60a5fa; background: transparent;")
                    self._process_rows[i]._ram_lbl.setText(ram_str)
                    self._process_rows[i]._ram_lbl.setStyleSheet("color: #a78bfa; background: transparent;")
                else:
                    self._process_rows[i]._name_lbl.setText("--")
                    self._process_rows[i]._name_lbl.setStyleSheet("color: #f0f4f8; background: transparent;")
                    self._process_rows[i]._cpu_lbl.setText("--")
                    self._process_rows[i]._cpu_lbl.setStyleSheet("color: #60a5fa; background: transparent;")
                    self._process_rows[i]._ram_lbl.setText("--")
                    self._process_rows[i]._ram_lbl.setStyleSheet("color: #a78bfa; background: transparent;")
        except Exception as e:
            print(f"Process list update error: {e}")

    def _show_all_processes(self):
        """Show all processes dialog."""
        from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
        from PyQt6.QtCore import Qt, QPoint

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setMinimumSize(800, 550)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                border: none;
            }}
        """)

        # Drag state
        drag_position = QPoint()

        def mousePressEvent(event):
            nonlocal drag_position
            if event.button() == Qt.MouseButton.LeftButton:
                drag_position = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            nonlocal drag_position
            if event.buttons() == Qt.MouseButton.LeftButton and not drag_position.isNull():
                dialog.move(event.globalPos() - drag_position)
                event.accept()

        def mouseReleaseEvent(event):
            nonlocal drag_position
            if event.button() == Qt.MouseButton.LeftButton:
                drag_position = QPoint()
                event.accept()

        dialog.mousePressEvent = mousePressEvent
        dialog.mouseMoveEvent = mouseMoveEvent
        dialog.mouseReleaseEvent = mouseReleaseEvent

        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        dialog.setLayout(main_layout)

        # Header with drag support
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 12, 12, 12)
        header.setLayout(header_layout)
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("Running Processes")
        title.setFont(S.font("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFont(S.font("Segoe UI", 16))
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        header_layout.addWidget(close_btn)
        main_layout.addWidget(header)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Process", "PID", "CPU %", "RAM MB", "Status"])
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFont(S.font("Segoe UI", 11))
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:alternate {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                padding: 12px 16px;
                font-weight: bold;
                font-size: 11px;
            }}
            QHeaderView::section:pressed {{
                background-color: {COLORS['bg_hover']};
            }}
        """)

        table_header = table.horizontalHeader()
        table_header.setStretchLastSection(True)
        table_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        table_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        table_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                if proc.is_running():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)

        text_color = QColor(COLORS['text_primary'])
        table.setRowCount(len(processes))

        for i, proc in enumerate(processes):
            name_item = QTableWidgetItem(proc.get('name') or 'Unknown')
            name_item.setForeground(text_color)
            table.setItem(i, 0, name_item)

            pid_item = QTableWidgetItem(str(proc.get('pid', '--')))
            pid_item.setForeground(text_color)
            table.setItem(i, 1, pid_item)

            cpu_val = proc.get('cpu_percent')
            cpu_item = QTableWidgetItem(f"{cpu_val:.1f}" if cpu_val is not None else "--")
            cpu_item.setForeground(text_color)
            table.setItem(i, 2, cpu_item)

            mem_info = proc.get('memory_info')
            if mem_info and hasattr(mem_info, 'rss'):
                mem_item = QTableWidgetItem(f"{mem_info.rss / (1024**2):.0f}")
                mem_item.setForeground(text_color)
                table.setItem(i, 3, mem_item)
            else:
                mem_item = QTableWidgetItem("--")
                mem_item.setForeground(text_color)
                table.setItem(i, 3, mem_item)

            status_item = QTableWidgetItem("Running")
            status_item.setForeground(QColor(COLORS['accent_green']))
            table.setItem(i, 4, status_item)

        main_layout.addWidget(table, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFont(S.font("Segoe UI", 11))
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

        close_btn.clicked.connect(dialog.accept)
        dialog.exec()

    def _create_sysinfo_card(self):
        """System info card."""
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Title
        title = QLabel("System Info")
        title.setFont(S.font("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Specs
        specs = QVBoxLayout()
        specs.setSpacing(8)

        specs.addWidget(self._create_spec_row("Processor", self._get_cpu_display(), COLORS['accent_blue']))
        specs.addWidget(self._create_spec_row("Graphics", self._get_gpu_display(), COLORS['accent_green']))
        specs.addWidget(self._create_spec_row("Memory", self._get_ram_display(), COLORS['accent_purple']))
        specs.addWidget(self._create_spec_row("Storage", self._get_disk_display(), COLORS['accent_orange']))
        specs.addWidget(self._create_spec_row("OS", self._short_os(), COLORS['text_secondary']))

        layout.addLayout(specs)
        layout.addStretch()

        return card

    def _create_spec_row(self, label, value, color):
        """Single spec row."""
        row = QFrame()
        row.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(0)
        row.setLayout(layout)

        indicator = QFrame()
        indicator.setFixedSize(3, 22)
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        layout.addWidget(indicator)

        lbl = QLabel(label)
        lbl.setFont(S.font("Segoe UI", 11))
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding-left: 12px; background: transparent;")
        lbl.setMinimumWidth(80)
        layout.addWidget(lbl)

        val_lbl = QLabel(value)
        val_lbl.setFont(S.font("Segoe UI", 11))
        val_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(val_lbl, stretch=1)

        return row

    def _get_cpu_display(self):
        cpu = self._get_cpu_name()
        if not cpu:
            cpu = platform.processor()
        if not cpu:
            return "Unknown"
        if len(cpu) > 38:
            return cpu[:38] + "..."
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

    def _get_disk_display(self):
        try:
            disk = psutil.disk_partitions()[0].device
            return disk if disk else "Unknown"
        except:
            return "Unknown"

    def _create_storage_card(self):
        """Storage card."""
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        card.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Storage")
        title.setFont(S.font("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header.addWidget(title)

        header.addStretch()

        btn = QPushButton("View all →")
        btn.setFont(S.font("Segoe UI", 10))
        btn.setFixedHeight(26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._show_all_drives)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_orange']};
                color: white;
            }}
        """)
        header.addWidget(btn)
        layout.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Storage container
        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(8)
        layout.addLayout(self._storage_container)

        self._update_storage_display([])

        return card

    def _update_storage_display(self, partitions):
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not partitions:
            placeholder = QLabel("No drives detected")
            placeholder.setFont(S.font("Segoe UI", 12))
            placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
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
            free_gb = partition.get('free', 0) / (1024**3)
            pct = partition.get('percent', 0)

            row = QFrame()
            row.setStyleSheet("background-color: transparent;")
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 6, 0, 6)
            row_layout.setSpacing(12)
            row.setLayout(row_layout)

            # Drive badge
            badge = QLabel(drive_letter.replace("\\", "") if drive_letter else "?")
            badge.setFont(S.font("Segoe UI", 11, QFont.Bold))
            badge.setStyleSheet(f"""
                background-color: {COLORS['accent_orange']};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedWidth(32)
            row_layout.addWidget(badge)

            # Info
            info = QVBoxLayout()
            info.setSpacing(4)

            name_lbl = QLabel(mountpoint if mountpoint else drive_letter)
            name_lbl.setFont(S.font("Segoe UI", 11, QFont.Bold))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            info.addWidget(name_lbl)

            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_deeper']};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {self._get_storage_color(pct)};
                    border-radius: 3px;
                }}
            """)
            info.addWidget(bar)
            row_layout.addLayout(info, stretch=1)

            # Usage
            usage_lbl = QLabel(f"{used_gb:.0f}/{total_gb:.0f} GB")
            usage_lbl.setFont(S.font("Segoe UI", 10))
            usage_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            usage_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            usage_lbl.setMinimumWidth(70)
            row_layout.addWidget(usage_lbl)

            # Percentage
            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(S.font("Segoe UI", 11, QFont.Bold))
            pct_lbl.setStyleSheet(f"color: {self._get_storage_color(pct)}; background: transparent;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            pct_lbl.setMinimumWidth(40)
            row_layout.addWidget(pct_lbl)

            self._storage_container.addWidget(row)

    def _get_storage_color(self, pct):
        if pct > 90:
            return COLORS['accent_red']
        elif pct > 75:
            return COLORS['accent_orange']
        return COLORS['accent_green']

    def _show_all_drives(self):
        """Show all drives dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QProgressBar, QPushButton
        from PyQt6.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setMinimumSize(700, 450)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)

        drag_pos = None

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                nonlocal drag_pos
                drag_pos = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == Qt.MouseButton.LeftButton and drag_pos:
                dialog.move(event.globalPos() - drag_pos)
                event.accept()

        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                nonlocal drag_pos
                drag_pos = None
                event.accept()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        dialog.setLayout(main_layout)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 12, 12, 12)
        header.setLayout(header_layout)
        header.setCursor(Qt.CursorShape.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("Storage Drives")
        title.setFont(S.font("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFont(S.font("Segoe UI", 16))
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        header_layout.addWidget(close_btn)
        main_layout.addWidget(header)

        # Drives
        drives = QVBoxLayout()
        drives.setSpacing(14)

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

            drive_card = QFrame()
            drive_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
            drive_layout = QHBoxLayout()
            drive_layout.setSpacing(20)
            drive_layout.setContentsMargins(16, 16, 16, 16)
            drive_card.setLayout(drive_layout)

            # Drive letter
            letter = QLabel(drive_letter.replace("\\", ""))
            letter.setFont(S.font("Segoe UI", 20, QFont.Bold))
            letter.setStyleSheet(f"color: {COLORS['accent_orange']}; background: transparent;")
            letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter.setFixedSize(50, 50)
            drive_layout.addWidget(letter)

            # Info
            info = QVBoxLayout()
            info.setSpacing(8)

            name = QLabel(mountpoint if mountpoint else drive_letter)
            name.setFont(S.font("Segoe UI", 13, QFont.Bold))
            name.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            info.addWidget(name)

            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setFixedHeight(10)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_deeper']};
                    border: none;
                    border-radius: 5px;
                }}
                QProgressBar::chunk {{
                    background-color: {self._get_storage_color(pct)};
                    border-radius: 5px;
                }}
            """)
            info.addWidget(bar)

            stats = QHBoxLayout()
            used_lbl = QLabel(f"{used_gb:.1f} GB used")
            used_lbl.setFont(S.font("Segoe UI", 10))
            used_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
            stats.addWidget(used_lbl)
            stats.addStretch()
            free_lbl = QLabel(f"{free_gb:.1f} GB free")
            free_lbl.setFont(S.font("Segoe UI", 10))
            free_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            stats.addWidget(free_lbl)
            info.addLayout(stats)

            drive_layout.addLayout(info, stretch=1)

            # Percentage
            pct_box = QFrame()
            pct_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_deeper']};
                    border-radius: 10px;
                }}
            """)
            pct_layout = QVBoxLayout()
            pct_layout.setSpacing(2)
            pct_layout.setContentsMargins(16, 8, 16, 8)
            pct_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_box.setLayout(pct_layout)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(S.font("Segoe UI", 22, QFont.Bold))
            pct_lbl.setStyleSheet(f"color: {self._get_storage_color(pct)}; background: transparent;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(pct_lbl)

            used_lbl = QLabel("used")
            used_lbl.setFont(S.font("Segoe UI", 9))
            used_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
            used_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_layout.addWidget(used_lbl)

            drive_layout.addWidget(pct_box)
            drives.addWidget(drive_card)

        main_layout.addLayout(drives)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(S.font("Segoe UI", 11))
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 28px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    # ─── Data Update ───────────────────────────────────────────────────────────

    def update_data(self, data):
        """Called by MainWindow whenever new data arrives."""
        self._last_data = data

        # CPU
        if 'cpu' in data:
            cpu = data['cpu']
            pct = cpu.get('percent', 0)

            self._cpu_card.gauge.set_value(pct)
            self._cpu_history.append(pct)
            self._cpu_chart.sparkline.push(pct)

            freq = psutil.cpu_freq()
            clock = f"{freq.current / 1000:.2f} GHz" if freq else "--"
            temp = self._get_cpu_temp()
            power = self._estimate_cpu_power(pct)

            for i, val in enumerate([clock, temp, power]):
                self._cpu_card.stats[i].setText(val)

        # Memory
        if 'memory' in data:
            mem = data['memory']
            pct = mem.get('percent', 0)
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            avail_gb = mem.get('available', 0) / (1024**3)

            self._ram_card.gauge.set_value(pct)
            self._ram_history.append(used_gb)
            self._ram_chart.sparkline.push(used_gb)

            for i, val in enumerate([f"{used_gb:.1f} GB", f"{avail_gb:.1f} GB", self._get_ram_type()]):
                self._ram_card.stats[i].setText(val)

        # Disk
        if 'disk' in data:
            disk = data['disk']
            pct = disk.get('percent', 0)
            read_speed = disk.get('read_speed', 0)
            write_speed = disk.get('write_speed', 0)

            self._disk_card.gauge.set_value(pct)

            for i, val in enumerate([f"{read_speed:.0f} MB/s", f"{write_speed:.0f} MB/s", f"{pct:.0f}%"]):
                self._disk_card.stats[i].setText(val)

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

                self._net_down_lbl.setText(f"{self._net_down_mbps:.1f}")
                self._net_up_lbl.setText(f"{self._net_up_mbps:.1f}")

                self._net_sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])
                self._net_chart.sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

            self._last_net = (bytes_sent, bytes_recv)

        # GPU
        if 'gpu' in data:
            gpu = data['gpu']
            if gpu.get('available'):
                load = gpu.get('load')
                temp = gpu.get('temperature')
                fan = gpu.get('fan_speed')
                power = gpu.get('power')

                if load is not None:
                    self._gpu_card.gauge.set_value(load)
                    self._gpu_history.append(load)
                    self._gpu_chart.sparkline.push(load)

                temp_str = f"{temp:.0f} °C" if temp is not None else "-- °C"
                fan_str = f"{fan} RPM" if fan is not None else "-- RPM"
                power_str = f"{power:.0f} W" if power is not None else "-- W"

                for i, val in enumerate([temp_str, fan_str, power_str]):
                    self._gpu_card.stats[i].setText(val)

    def _get_cpu_temp(self):
        try:
            temps = psutil.cpu_temperature()
            if isinstance(temps, list):
                return f"{temps[0]:.0f} °C"
            return f"{temps:.0f} °C"
        except:
            try:
                import wmi
                w = wmi.WMI()
                temps = w.Win32_TemperatureProbe()
                if temps:
                    return f"{temps[0].CurrentReading / 10:.0f} °C"
            except:
                pass
        return "-- °C"

    def _estimate_cpu_power(self, pct):
        try:
            base_tdp = 65
            power = base_tdp * (0.3 + 0.7 * pct / 100)
            return f"{power:.0f} W"
        except:
            return "-- W"

    def _get_ram_type(self):
        try:
            import wmi
            w = wmi.WMI()
            for mem_obj in w.Win32_PhysicalMemory():
                if hasattr(mem_obj, 'MemoryType') and mem_obj.MemoryType:
                    mem_type = int(mem_obj.MemoryType)
                    type_map = {20: "DDR5", 21: "DDR4", 22: "DDR3", 24: "DDR2"}
                    return type_map.get(mem_type, "Unknown")
        except:
            pass
        return "DDR?"
