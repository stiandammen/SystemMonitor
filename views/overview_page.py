"""
Overview Page - Main dashboard with system overview
"""
import platform
import time
import psutil
from collections import deque
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QPushButton,
    QFormLayout, QProgressBar, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from widgets.card import Card
from widgets.donut_gauge import DonutGauge
from widgets.sparkline import SparklineWidget


# Color palette matching the app theme
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
    'accent_yellow': '#ffd740',
}


def card_stylesheet():
    return f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 16px;
        }}
    """


def label_stylesheet(color=None, size=None, bold=False):
    style = ""
    if color:
        style += f"color: {color};"
    if size:
        style += f"font-size: {size}px;"
    if bold:
        style += "font-weight: bold;"
    return style


class OverviewPage(QWidget):
    """
    Main overview dashboard page
    Shows real-time system performance with gauges, graphs, and info panels
    """

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0

        # Network speed tracking (bytes/sec)
        self._last_net = None
        self._net_down_mbps = 0.0
        self._net_up_mbps = 0.0

        # Data buffers for sparklines
        self._cpu_history = deque(maxlen=60)
        self._gpu_history = deque(maxlen=60)
        self._ram_history = deque(maxlen=60)
        self._net_down_history = deque(maxlen=60)
        self._net_up_history = deque(maxlen=60)

        self._setup_ui()
        self._start_timers()

    def _setup_ui(self):
        """Setup main layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Page header
        header = self._create_page_header()
        layout.addWidget(header)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_primary']};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 16, 24, 24)
        content_layout.setSpacing(20)
        content.setLayout(content_layout)

        # Row 1: Resource cards
        resource_row = self._create_resource_cards_row()
        content_layout.addWidget(resource_row)

        # Row 2: Detail charts
        chart_row = self._create_detail_charts_row()
        content_layout.addWidget(chart_row)

        # Row 3: Info panels
        info_row = self._create_info_panels_row()
        content_layout.addWidget(info_row)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    # ─── Page Header ─────────────────────────────────────────────────────────

    def _create_page_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: #111820; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 0, 24, 0)
        header.setLayout(layout)

        # Left: Title + subtitle
        left = QVBoxLayout()
        left.setSpacing(2)
        left.addStretch()

        title = QLabel("Overview")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        left.addWidget(title)

        subtitle = QLabel("Real-time system performance")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']};")
        left.addWidget(subtitle)

        left.addStretch()
        layout.addLayout(left)

        # Spacer
        layout.addStretch()

        # Right: Info blocks
        info_layout = QHBoxLayout()
        info_layout.setSpacing(0)
        info_layout.addWidget(self._create_info_block("Uptime", self._format_uptime(0)))
        info_layout.addWidget(self._create_separator())
        info_layout.addWidget(self._create_info_block("OS", self._short_os()))
        info_layout.addWidget(self._create_separator())
        info_layout.addWidget(self._create_info_block("CPU", self._short_cpu()))
        info_layout.addWidget(self._create_separator())
        info_layout.addWidget(self._create_info_block("GPU", self._short_gpu()))

        # Store uptime label ref for timer updates
        self._uptime_val_label = info_layout.itemAt(0).widget().layout().itemAt(1).widget()

        layout.addLayout(info_layout)

        return header

    def _short_os(self):
        """Short OS string"""
        p = platform.platform()
        if "Windows" in p:
            return "Windows " + platform.win32_ver()[0]
        return p

    def _short_cpu(self):
        """Short CPU string"""
        cpu = platform.processor()
        if not cpu:
            return "Unknown"
        # Shorten common long names
        if len(cpu) > 30:
            return cpu[:30] + "..."
        return cpu

    def _short_gpu(self):
        """Get GPU name"""
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

    def _create_info_block(self, label, value):
        block = QFrame()
        block.setContentsMargins(16, 0, 16, 0)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        block.setLayout(layout)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 12))
        val.setStyleSheet(f"color: {COLORS['text_primary']};")
        val.setWordWrap(False)
        layout.addWidget(val)

        return block

    def _create_separator(self):
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        return sep

    def _format_uptime(self, seconds):
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"

    def _start_timers(self):
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)
        self._uptime_timer.start(1000)

        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._refresh_processes)
        self._process_timer.start(3000)

        self._storage_timer = QTimer(self)
        self._storage_timer.timeout.connect(self._update_storage)
        self._storage_timer.start(5000)

    def _update_uptime(self):
        self._uptime_seconds = int(time.time() - self._start_time)
        self._uptime_val_label.setText(self._format_uptime(self._uptime_seconds))

    # ─── Row 1: Resource Cards ───────────────────────────────────────────────

    def _create_resource_cards_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        self._cpu_card = self._create_resource_card("CPU", COLORS['accent_blue'], "Clock", "Temp", "Power")
        self._gpu_card = self._create_resource_card("GPU", COLORS['accent_green'], "Temp", "Fan", "Power")
        self._ram_card = self._create_resource_card("RAM", COLORS['accent_purple'], "Speed", "Used", "Available")
        self._disk_card = self._create_resource_card("Disk", COLORS['accent_orange'], "Read", "Write", "Temp")
        self._network_card = self._create_network_card()

        layout.addWidget(self._cpu_card, stretch=1)
        layout.addWidget(self._gpu_card, stretch=1)
        layout.addWidget(self._ram_card, stretch=1)
        layout.addWidget(self._disk_card, stretch=1)
        layout.addWidget(self._network_card, stretch=1)

        return row

    def _create_resource_card(self, title, color, *labels):
        card = QFrame()
        card.setMinimumHeight(200)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_lbl)

        # Gauge + Stats row
        content = QHBoxLayout()
        content.setSpacing(14)

        gauge = DonutGauge(color=color, size=90)
        content.addWidget(gauge)

        # Stats
        stats_vbox = QVBoxLayout()
        stats_vbox.setSpacing(8)

        stat_widgets = []
        for lbl in labels:
            stat_row = QHBoxLayout()
            stat_row.setSpacing(4)

            name_lbl = QLabel(lbl + ":")
            name_lbl.setFont(QFont("Segoe UI", 11))
            name_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            stat_row.addWidget(name_lbl)

            val_lbl = QLabel("--")
            val_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            val_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            stat_row.addWidget(val_lbl)

            stat_row.addStretch()
            stats_vbox.addLayout(stat_row)
            stat_widgets.append(val_lbl)

        stats_vbox.addStretch()
        content.addLayout(stats_vbox)
        layout.addLayout(content)

        # Sparkline
        sparkline = SparklineWidget(colors=[color])
        sparkline.setFixedHeight(50)
        layout.addWidget(sparkline)

        card.gauge = gauge
        card.sparkline = sparkline
        card.stats = stat_widgets

        return card

    def _create_network_card(self):
        card = QFrame()
        card.setMinimumHeight(200)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        # Title
        title_lbl = QLabel("Network")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_lbl)

        # Up/Down
        content = QHBoxLayout()
        content.setSpacing(24)

        # Upload
        up_vbox = QVBoxLayout()
        up_vbox.setSpacing(2)
        up_icon = QLabel("▲")
        up_icon.setFont(QFont("Segoe UI", 14))
        up_icon.setStyleSheet(f"color: {COLORS['accent_cyan']};")
        up_vbox.addWidget(up_icon)
        self._net_up_lbl = QLabel("0.0")
        self._net_up_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self._net_up_lbl.setStyleSheet(f"color: {COLORS['accent_cyan']};")
        up_vbox.addWidget(self._net_up_lbl)
        up_unit = QLabel("Mbps up")
        up_unit.setFont(QFont("Segoe UI", 10))
        up_unit.setStyleSheet(f"color: {COLORS['text_muted']};")
        up_vbox.addWidget(up_unit)
        up_vbox.addStretch()
        content.addLayout(up_vbox)

        # Download
        down_vbox = QVBoxLayout()
        down_vbox.setSpacing(2)
        down_icon = QLabel("▼")
        down_icon.setFont(QFont("Segoe UI", 14))
        down_icon.setStyleSheet(f"color: {COLORS['accent_blue']};")
        down_vbox.addWidget(down_icon)
        self._net_down_lbl = QLabel("0.0")
        self._net_down_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self._net_down_lbl.setStyleSheet(f"color: {COLORS['accent_blue']};")
        down_vbox.addWidget(self._net_down_lbl)
        down_unit = QLabel("Mbps down")
        down_unit.setFont(QFont("Segoe UI", 10))
        down_unit.setStyleSheet(f"color: {COLORS['text_muted']};")
        down_vbox.addWidget(down_unit)
        down_vbox.addStretch()
        content.addLayout(down_vbox)

        content.addStretch()
        layout.addLayout(content)

        # Sparklines (dual)
        self._net_sparkline = SparklineWidget(colors=[COLORS['accent_cyan'], COLORS['accent_blue']])
        self._net_sparkline.setFixedHeight(50)
        layout.addWidget(self._net_sparkline)

        return card

    # ─── Row 2: Detail Charts ──────────────────────────────────────────────────

    def _create_detail_charts_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        self._cpu_detail_chart = self._create_detail_chart("CPU Usage", "Total · Core 1-8", COLORS['accent_blue'])
        self._gpu_detail_chart = self._create_detail_chart("GPU Usage", "Load %", COLORS['accent_green'])
        self._ram_detail_chart = self._create_detail_chart("RAM Usage", "Used GB", COLORS['accent_purple'])
        self._net_detail_chart = self._create_detail_chart("Network Activity", "Down · Up", COLORS['accent_cyan'])
        self._net_detail_chart.sparkline._colors = [COLORS['accent_blue'], COLORS['accent_cyan']]
        self._net_detail_chart.sparkline._data = [deque(maxlen=60), deque(maxlen=60)]

        layout.addWidget(self._cpu_detail_chart, stretch=1)
        layout.addWidget(self._gpu_detail_chart, stretch=1)
        layout.addWidget(self._ram_detail_chart, stretch=1)
        layout.addWidget(self._net_detail_chart, stretch=1)

        return row

    def _create_detail_chart(self, title, legend, color):
        card = QFrame()
        card.setMinimumHeight(160)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header_lbl = QLabel(title)
        header_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.addWidget(header_lbl)
        header.addStretch()

        legend_lbl = QLabel(legend)
        legend_lbl.setFont(QFont("Segoe UI", 10))
        legend_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        header.addWidget(legend_lbl)
        layout.addLayout(header)

        # Sparkline chart
        sparkline = SparklineWidget(colors=[color])
        sparkline.setFixedHeight(90)
        layout.addWidget(sparkline)

        card.sparkline = sparkline
        return card

    # ─── Row 3: Info Panels ───────────────────────────────────────────────────

    def _create_info_panels_row(self):
        row = QFrame()
        layout = QHBoxLayout()
        layout.setSpacing(14)
        row.setLayout(layout)

        process_card = self._create_process_card()
        sysinfo_card = self._create_system_info_card()
        storage_card = self._create_storage_card()
        alerts_card = self._create_alerts_card()

        layout.addWidget(process_card, stretch=1)
        layout.addWidget(sysinfo_card, stretch=1)
        layout.addWidget(storage_card, stretch=1)
        layout.addWidget(alerts_card, stretch=1)

        return row

    # ── Process Table Card ──────────────────────────────────────────────────

    def _create_process_card(self):
        card = QFrame()
        card.setMinimumHeight(280)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        card.setLayout(layout)

        # Title
        title = QLabel("Top Processes")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Process", "PID", "CPU %", "RAM %", "GPU"])
        table.setRowCount(6)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFont(QFont("Segoe UI", 10))
        table.horizontalHeader().setFont(QFont("Segoe UI", 9, QFont.Bold))
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(32)
        table.setFocusPolicy(Qt.NoFocus)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_muted']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                padding: 8px 8px;
                font-weight: bold;
            }}
            QHeaderView {{
                border: none;
            }}
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        table.setColumnWidth(1, 50)
        table.setColumnWidth(2, 55)
        table.setColumnWidth(3, 55)
        table.setColumnWidth(4, 45)

        layout.addWidget(table)
        self._process_table = table

        # View all button
        btn = QPushButton("View all →")
        btn.setFont(QFont("Segoe UI", 9))
        btn.setFixedHeight(26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._show_all_processes)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_blue']};
            }}
        """)
        layout.addWidget(btn)

        return card

    # ── System Info Card ───────────────────────────────────────────────────

    def _create_system_info_card(self):
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        title = QLabel("System Info")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)

        def make_val(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            return lbl

        def make_row(label, value):
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            return (lbl, make_val(value))

        rows = [
            ("Motherboard", self._get_motherboard()),
            ("CPU", (platform.processor() or "Unknown")[:40]),
            ("GPU", self._short_gpu()),
            ("RAM", self._get_ram_info()),
            ("Storage", self._get_primary_disk()),
            ("OS", self._short_os()),
        ]

        for label, value in rows:
            lbl, val_lbl = make_row(label, value)
            form.addRow(lbl, val_lbl)

        layout.addLayout(form)

        return card

    def _get_motherboard(self):
        try:
            import wmi
            w = wmi.WMI()
            return w.Win32_BaseBoard()[0].Product
        except:
            return "Unknown"

    def _get_primary_disk(self):
        try:
            return psutil.disk_partitions()[0].device
        except:
            return "Unknown"

    def _get_ram_info(self):
        """Get RAM info: size and type"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3))

            # Try WMI for RAM type via multiple methods
            ram_type = "Unknown"
            speed = 0

            try:
                import wmi
                w = wmi.WMI()
                for mem_obj in w.Win32_PhysicalMemory():
                    # Get speed first
                    if hasattr(mem_obj, 'Speed') and mem_obj.Speed:
                        speed = int(mem_obj.Speed)

                    # Check MemoryType property
                    if hasattr(mem_obj, 'MemoryType') and mem_obj.MemoryType:
                        mem_type = int(mem_obj.MemoryType)
                        # MemoryType values: 0=Unknown, 20=DDR5, 21=DDR4, 22=DDR3, 24=DDR2
                        type_map = {
                            20: "DDR5",
                            21: "DDR4",
                            22: "DDR3",
                            24: "DDR2",
                        }
                        ram_type = type_map.get(mem_type, "Unknown")
                        if ram_type != "Unknown":
                            break

                # Fallback: detect by speed if MemoryType didn't work
                if ram_type == "Unknown" and speed > 0:
                    if speed >= 6400:
                        ram_type = "DDR5"
                    elif speed >= 3200:
                        ram_type = "DDR4"
                    elif speed >= 2133:
                        ram_type = "DDR3"
                    else:
                        ram_type = "DDR"

            except Exception as e:
                print(f"WMI RAM detection error: {e}")

            if ram_type != "Unknown":
                return f"{total_gb} GB {ram_type}"
            else:
                return f"{total_gb} GB"
        except Exception as e:
            print(f"RAM info error: {e}")
            return "Unknown"

    # ── Storage Card ─────────────────────────────────────────────────────────

    def _create_storage_card(self):
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        title = QLabel("Storage")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(10)
        layout.addLayout(self._storage_container)

        # View all button
        btn = QPushButton("View all drives →")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setFixedHeight(30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #1e2936;
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_orange']};
            }}
        """)
        layout.addWidget(btn)

        self._update_storage()

        return card

    def _update_storage(self):
        """Repopulate storage card with current partitions"""
        # Clear existing
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for partition in psutil.disk_partitions():
            if not partition.fstype:
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue

            row = QFrame()
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_layout)

            # Drive label
            name_lbl = QLabel(partition.device)
            name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            name_lbl.setFixedWidth(48)
            row_layout.addWidget(name_lbl)

            # Progress bar
            bar = QProgressBar()
            bar.setValue(int(usage.percent))
            bar.setFixedHeight(10)
            bar.setTextVisible(False)
            # Color based on usage
            if usage.percent > 90:
                chunk_color = COLORS['accent_red']
            elif usage.percent > 75:
                chunk_color = COLORS['accent_orange']
            else:
                chunk_color = COLORS['accent_green']
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_deeper']};
                    border: none;
                    border-radius: 5px;
                }}
                QProgressBar::chunk {{
                    background-color: {chunk_color};
                    border-radius: 5px;
                }}
            """)
            row_layout.addWidget(bar, stretch=1)

            # Percent + size
            pct_lbl = QLabel(f"{usage.percent:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", 10))
            pct_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            pct_lbl.setFixedWidth(38)
            row_layout.addWidget(pct_lbl)

            self._storage_container.addWidget(row)

    # ── Alerts Card ──────────────────────────────────────────────────────────

    def _create_alerts_card(self):
        card = QFrame()
        card.setMinimumHeight(260)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(10)
        card.setLayout(layout)

        title = QLabel("Alerts")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        self._alerts_vbox = QVBoxLayout()
        self._alerts_vbox.setSpacing(10)
        layout.addLayout(self._alerts_vbox)

        # View all button
        btn = QPushButton("View all alerts →")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setFixedHeight(30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #1e2936;
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_red']};
            }}
        """)
        layout.addWidget(btn)

        self._update_alerts([])

        return card

    def _update_alerts(self, alerts=None):
        """Repaint alerts list"""
        while self._alerts_vbox.count():
            item = self._alerts_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if alerts is None:
            if hasattr(self, '_last_data'):
                alerts = self._generate_alerts(self._last_data)
            else:
                alerts = []

        if not alerts:
            alerts = [{"level": "green", "title": "All systems normal", "desc": "No issues detected"}]

        for alert in alerts:
            level = alert.get("level", "green")
            title = alert.get("title", "")
            desc = alert.get("desc", "")

            item = QFrame()
            item_layout = QHBoxLayout()
            item_layout.setSpacing(10)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item.setLayout(item_layout)

            # Dot indicator
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 12))
            if level == "red":
                dot.setStyleSheet(f"color: {COLORS['accent_red']};")
            elif level == "yellow":
                dot.setStyleSheet(f"color: {COLORS['accent_yellow']};")
            else:
                dot.setStyleSheet(f"color: {COLORS['accent_green']};")
            item_layout.addWidget(dot)

            # Text
            txt_vbox = QVBoxLayout()
            txt_vbox.setSpacing(1)
            t = QLabel(title)
            t.setFont(QFont("Segoe UI", 11))
            t.setStyleSheet(f"color: {COLORS['text_primary']};")
            txt_vbox.addWidget(t)
            d = QLabel(desc)
            d.setFont(QFont("Segoe UI", 10))
            d.setStyleSheet(f"color: {COLORS['text_muted']};")
            txt_vbox.addWidget(d)
            item_layout.addLayout(txt_vbox)

            self._alerts_vbox.addWidget(item)

    def _generate_alerts(self, data):
        """Generate alert list from data"""
        alerts = []

        if 'cpu' in data:
            pct = data['cpu'].get('percent', 0)
            if pct > 95:
                alerts.append({"level": "red", "title": "Critical CPU Usage", "desc": f"CPU at {pct:.0f}%"})
            elif pct > 80:
                alerts.append({"level": "yellow", "title": "High CPU Usage", "desc": f"CPU at {pct:.0f}%"})

        if 'memory' in data:
            pct = data['memory'].get('percent', 0)
            if pct > 90:
                alerts.append({"level": "yellow", "title": "High Memory Usage", "desc": f"RAM at {pct:.0f}%"})

        if 'disk' in data:
            pct = data['disk'].get('percent', 0)
            if pct > 90:
                alerts.append({"level": "yellow", "title": "Low Disk Space", "desc": f"Disk at {pct:.0f}%"})

        return alerts

    # ─── Data Update ───────────────────────────────────────────────────────────

    def update_data(self, data):
        """Called by MainWindow whenever new data arrives"""
        self._last_data = data

        # CPU
        if 'cpu' in data:
            cpu = data['cpu']
            pct = cpu.get('percent', 0)
            per_core = cpu.get('per_core', [])

            self._cpu_card.gauge.set_value(pct)
            self._cpu_card.sparkline.push(pct)

            # Stats
            freq = psutil.cpu_freq()
            clock = f"{freq.current / 1000:.2f} GHz" if freq else "--"
            temp = self._get_cpu_temp()
            power = self._estimate_cpu_power(pct)

            for i, val in enumerate([clock, temp, power]):
                self._cpu_card.stats[i].setText(val)

            self._cpu_history.append(pct)

            # Update CPU detail chart
            self._cpu_detail_chart.sparkline.push(pct)

        # Memory
        if 'memory' in data:
            mem = data['memory']
            pct = mem.get('percent', 0)
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            avail_gb = mem.get('available', 0) / (1024**3)

            self._ram_card.gauge.set_value(pct)
            self._ram_card.sparkline.push(pct)

            for i, val in enumerate([f"{psutil.virtual_memory().speed} MHz" if hasattr(psutil.virtual_memory(), 'speed') else "-- MHz", f"{used_gb:.1f} GB", f"{avail_gb:.1f} GB"]):
                self._ram_card.stats[i].setText(val)

            self._ram_history.append(used_gb)
            self._ram_detail_chart.sparkline.push(used_gb)

        # Disk
        if 'disk' in data:
            disk = data['disk']
            pct = disk.get('percent', 0)
            used_gb = disk.get('used', 0) / (1024**3)
            total_gb = disk.get('total', 0) / (1024**3)

            self._disk_card.gauge.set_value(pct)
            self._disk_card.sparkline.push(pct)

            for i, val in enumerate([f"{used_gb:.0f} MB/s", f"{used_gb:.0f} MB/s", "-- °C"]):
                self._disk_card.stats[i].setText(val)

        # Network
        if 'network' in data:
            net = data['network']
            bytes_sent = net.get('bytes_sent', 0)
            bytes_recv = net.get('bytes_recv', 0)

            if self._last_net:
                dt = 1.0  # seconds since last update
                down_speed = (bytes_recv - self._last_net[0]) / dt / 1e6  # Mbps
                up_speed = (bytes_sent - self._last_net[1]) / dt / 1e6

                self._net_down_mbps = max(0, down_speed)
                self._net_up_mbps = max(0, up_speed)

                self._net_down_lbl.setText(f"{self._net_down_mbps:.1f}")
                self._net_up_lbl.setText(f"{self._net_up_mbps:.1f}")

                self._net_sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

                self._net_down_history.append(self._net_down_mbps)
                self._net_up_history.append(self._net_up_mbps)

                self._net_detail_chart.sparkline.push_multi([self._net_down_mbps, self._net_up_mbps])

            self._last_net = (bytes_sent, bytes_recv)

        # Alerts
        self._update_alerts()

    def _get_cpu_temp(self):
        """Get CPU temperature"""
        try:
            temps = psutil.cpu_temperature()
            if isinstance(temps, list):
                return f"{temps[0]:.0f} °C"
            return f"{temps:.0f} °C"
        except:
            # Try wmi
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
        """Rough CPU power estimate in watts"""
        try:
            # Base TDP ~65W, scale with usage
            base_tdp = 65
            power = base_tdp * (0.3 + 0.7 * pct / 100)
            return f"{power:.0f} W"
        except:
            return "-- W"

    # ─── Process Refresh ───────────────────────────────────────────────────────

    def _refresh_processes(self):
        """Refresh process table every 3 seconds"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if proc.is_running():
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)

            text_color = QColor(COLORS['text_primary'])

            for i in range(6):
                if i < len(processes):
                    proc = processes[i]
                    name_item = QTableWidgetItem((proc.get('name') or 'Unknown')[:25])
                    name_item.setForeground(text_color)
                    self._process_table.setItem(i, 0, name_item)

                    pid_item = QTableWidgetItem(str(proc.get('pid', '--')))
                    pid_item.setForeground(text_color)
                    self._process_table.setItem(i, 1, pid_item)

                    cpu_val = proc.get('cpu_percent')
                    cpu_item = QTableWidgetItem(f"{cpu_val:.1f}" if cpu_val is not None else "--")
                    cpu_item.setForeground(text_color)
                    self._process_table.setItem(i, 2, cpu_item)

                    mem_info = proc.get('memory_info')
                    if mem_info and hasattr(mem_info, 'rss'):
                        mem_pct = (mem_info.rss / psutil.virtual_memory().total) * 100
                        mem_item = QTableWidgetItem(f"{mem_pct:.1f}")
                        mem_item.setForeground(text_color)
                        self._process_table.setItem(i, 3, mem_item)
                    else:
                        mem_item = QTableWidgetItem("--")
                        mem_item.setForeground(text_color)
                        self._process_table.setItem(i, 3, mem_item)

                    gpu_item = QTableWidgetItem("--")
                    gpu_item.setForeground(text_color)
                    self._process_table.setItem(i, 4, gpu_item)
                else:
                    for col in range(5):
                        item = QTableWidgetItem("")
                        item.setForeground(text_color)
                        self._process_table.setItem(i, col, item)
        except Exception as e:
            print(f"Process refresh error: {e}")

    def _show_all_processes(self):
        """Show dialog with all running processes"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame, QSizeGrip
        from PyQt5.QtCore import Qt, QPoint

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setSizeGripEnabled(True)
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 650)

        # Mouse drag position
        self._drag_position = None

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self._drag_position = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == Qt.LeftButton and self._drag_position:
                dialog.move(event.globalPos() - self._drag_position)
                event.accept()

        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                self._drag_position = None
                event.accept()

        # Install event filter on header for dragging
        header_frame = None
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        dialog.setLayout(main_layout)

        # Header with title and stats
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 12, 12, 12)
        header_frame.setLayout(header_layout)

        # Enable dragging on header
        header_frame.mousePressEvent = mousePressEvent
        header_frame.mouseMoveEvent = mouseMoveEvent
        header_frame.mouseReleaseEvent = mouseReleaseEvent
        header_frame.setCursor(Qt.SizeAllCursor)

        title = QLabel("Running Processes")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Stats badge
        self._process_count_label = QLabel("0 processes")
        self._process_count_label.setFont(QFont("Segoe UI", 11))
        self._process_count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background-color: {COLORS['bg_deeper']}; padding: 6px 14px; border-radius: 12px;")
        header_layout.addWidget(self._process_count_label)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFont(QFont("Segoe UI", 16))
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
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
        close_btn.clicked.connect(dialog.close)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header_frame)

        # Table container
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        table_container.setLayout(table_layout)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Process Name", "PID", "CPU %", "RAM MB", "Status"])
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFont(QFont("Segoe UI", 11))
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 12px 16px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:alternate {{
                background-color: {COLORS['bg_deeper']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['bg_hover']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: none;
                border-bottom: 2px solid {COLORS['border']};
                padding: 14px 16px;
                font-weight: bold;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QHeaderView {{
                border: none;
            }}
            QHeaderView::downArrow {{
                width: 10px;
            }}
        """)

        # Make table stretch to fill container
        table_layout.addWidget(table)
        table_container_layout = table_layout
        table_container_layout.addWidget(table)

        main_layout.addWidget(table_container, stretch=1)

        # Set column resizing behavior - Process Name fixed, others stretch
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        table.setColumnWidth(0, 180)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 90)
        table.setColumnWidth(4, 90)

        # Populate table
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

        # Update process count
        self._process_count_label.setText(f"{len(processes)} processes")

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # Refresh button
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 11))
        refresh_btn.setFixedHeight(38)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(lambda: self._refresh_process_dialog(table, self._process_count_label))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_blue']};
            }}
        """)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 11))
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.PointingHandCursor)
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
        close_btn.clicked.connect(dialog.close)

        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)

        # Size grip layout row with visible resize indicator
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 6, 6)
        grip_row.addStretch()

        resize_indicator = QLabel("⤡")
        resize_indicator.setFont(QFont("Segoe UI", 12))
        resize_indicator.setStyleSheet(f"color: {COLORS['text_muted']};")
        resize_indicator.setToolTip("Drag to resize")
        resize_indicator.setCursor(Qt.SizeBDiagCursor)
        grip_row.addWidget(resize_indicator, 0, Qt.AlignRight | Qt.AlignBottom)

        # Create a size grip for actual resizing
        size_grip = QSizeGrip(dialog)
        size_grip.setFixedSize(16, 16)
        grip_row.addWidget(size_grip, 0, Qt.AlignRight | Qt.AlignBottom)

        main_layout.addLayout(btn_layout)
        main_layout.addLayout(grip_row)

        dialog.exec_()

    def _refresh_process_dialog(self, table, count_label):
        """Refresh the process dialog table"""
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
        count_label.setText(f"{len(processes)} processes")

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
