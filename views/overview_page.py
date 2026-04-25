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
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

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


class DiskIcon(QWidget):
    """Modern SSD/NVMe drive icon drawn with QPainter"""
    def __init__(self, size=48, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)

        w = self.width()
        h = self.height()
        pad = w * 0.08
        body_h = h * 0.72
        body_y = h * 0.12

        # Main body (dark PCB-like)
        body_rect = QRect(int(pad), int(body_y), int(w - pad * 2), int(body_h))
        body_grad = QLinearGradient(0, body_y, 0, body_y + body_h)
        body_grad.setColorAt(0, QColor(55, 65, 80))
        body_grad.setColorAt(1, QColor(30, 38, 52))
        painter.setBrush(body_grad)
        painter.setPen(QPen(QColor(20, 26, 36), 1.5))
        painter.drawRoundedRect(body_rect, 3, 3)

        # Notch cut on right side (M.2 style)
        notch_w = w * 0.06
        notch_h = h * 0.22
        notch_x = w - pad - notch_w
        notch_y = body_y + body_h * 0.4
        painter.setBrush(QColor(COLORS['bg_primary']))
        painter.setPen(Qt.NoPen)
        painter.drawRect(int(notch_x), int(notch_y), int(notch_w), int(notch_h))

        # Gold pins at bottom
        pin_area_h = h * 0.1
        pin_area_y = body_y + body_h
        pin_area_rect = QRect(int(pad), int(pin_area_y), int(w - pad * 2), int(pin_area_h))
        pin_grad = QLinearGradient(0, pin_area_y, 0, pin_area_y + pin_area_h)
        pin_grad.setColorAt(0, QColor(200, 165, 90))
        pin_grad.setColorAt(1, QColor(160, 130, 60))
        painter.setBrush(pin_grad)
        painter.setPen(QPen(QColor(130, 100, 40), 1))
        painter.drawRect(pin_area_rect)

        # Horizontal pin dividers
        pin_count = 6
        pin_w_step = (w - pad * 2) / pin_count
        painter.setPen(QPen(QColor(130, 100, 40), 0.8))
        for i in range(1, pin_count):
            x = int(pad + i * pin_w_step)
            painter.drawLine(x, int(pin_area_y), x, int(pin_area_y + pin_area_h))

        # Label area (small rectangle on body)
        label_pad = w * 0.12
        label_w = w - pad * 2 - label_pad * 2
        label_h = h * 0.18
        label_y = body_y + body_h * 0.18
        label_rect = QRect(int(pad + label_pad), int(label_y), int(label_w), int(label_h))
        label_grad = QLinearGradient(0, label_y, 0, label_y + label_h)
        label_grad.setColorAt(0, QColor(80, 90, 110))
        label_grad.setColorAt(1, QColor(65, 75, 95))
        painter.setBrush(label_grad)
        painter.setPen(QPen(QColor(50, 60, 78), 1))
        painter.drawRoundedRect(label_rect, 1, 1)

        # Small chip on body (flash chip)
        chip_w = w * 0.18
        chip_h = h * 0.14
        chip_x = w * 0.22
        chip_y = body_y + body_h * 0.52
        painter.setBrush(QColor(25, 30, 42))
        painter.setPen(QPen(QColor(40, 48, 65), 1))
        painter.drawRect(int(chip_x), int(chip_y), int(chip_w), int(chip_h))
        # Tiny dot on chip (origin marker)
        painter.setBrush(QColor(180, 140, 50))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(chip_x + 2), int(chip_y + 2), 3, 3)

        # Controller chip (small square)
        ctrl_size = w * 0.1
        ctrl_x = w * 0.58
        ctrl_y = body_y + body_h * 0.55
        painter.setBrush(QColor(20, 24, 35))
        painter.setPen(QPen(QColor(35, 42, 58), 1))
        painter.drawRect(int(ctrl_x), int(ctrl_y), int(ctrl_size), int(ctrl_size))

        painter.end()


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
        header.setStyleSheet(f"background-color: {COLORS['bg_primary']}; border: none;")
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

        # Store CPU info label ref for timer updates
        self._cpu_val_label = info_layout.itemAt(4).widget().layout().itemAt(1).widget()
        self._gpu_val_label = info_layout.itemAt(6).widget().layout().itemAt(1).widget()

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
        cpu = self._get_cpu_name()
        if not cpu:
            cpu = platform.processor()
        if not cpu:
            return "Unknown"
        # Shorten only very long names
        if len(cpu) > 35:
            return cpu[:35] + "..."
        return cpu

    def _get_cpu_name(self):
        """Get CPU name via WMI"""
        try:
            import wmi
            w = wmi.WMI()
            for cpu in w.Win32_Processor():
                return cpu.Name
        except:
            return None

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
        val.setFont(QFont("Segoe UI", 10))
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

        self._system_info_timer = QTimer(self)
        self._system_info_timer.timeout.connect(self._update_system_info)
        self._system_info_timer.start(10000)

    def _update_uptime(self):
        self._uptime_seconds = int(time.time() - self._start_time)
        self._uptime_val_label.setText(self._format_uptime(self._uptime_seconds))

    def _update_system_info(self):
        """Update CPU and GPU info in header periodically"""
        self._cpu_val_label.setText(self._short_cpu())
        self._gpu_val_label.setText(self._short_gpu())

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
        card.setMinimumHeight(200)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(12)
        card.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_lbl = QLabel("🖥️")
        icon_lbl.setFont(QFont("Segoe UI", 14))
        header.addWidget(icon_lbl)

        title = QLabel("System Info")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.addWidget(title)

        header.addStretch()
        layout.addLayout(header)

        # System info rows container
        sys_container = QVBoxLayout()
        sys_container.setSpacing(8)
        layout.addLayout(sys_container)

        # System info data
        sys_info = [
            ("Motherboard", self._get_motherboard(), "🖧"),
            ("CPU", (platform.processor() or "Unknown")[:40], "⚙️"),
            ("GPU", self._short_gpu(), "🎮"),
            ("RAM", self._get_ram_info(), "💾"),
            ("Storage", self._get_primary_disk(), "🖴"),
            ("OS", self._short_os(), "🖥️"),
        ]

        for label, value, icon in sys_info:
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_deeper']};
                    border-radius: 8px;
                    padding: 10px 12px;
                }}
            """)
            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)
            row_layout.setContentsMargins(6, 6, 6, 6)
            row.setLayout(row_layout)

            # Icon box
            icon_box = QFrame()
            icon_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border-radius: 8px;
                    padding: 6px;
                }}
            """)
            icon_box_layout = QVBoxLayout()
            icon_box_layout.setContentsMargins(0, 0, 0, 0)
            icon_box_layout.setSpacing(0)
            icon_box.setLayout(icon_box_layout)

            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI", 16))
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_box_layout.addWidget(icon_lbl)

            row_layout.addWidget(icon_box)

            # Label
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row_layout.addWidget(lbl)

            row_layout.addStretch()

            # Value
            val_lbl = QLabel(value)
            val_lbl.setFont(QFont("Segoe UI", 10))
            val_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(val_lbl)

            sys_container.addWidget(row)

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
        card.setMinimumHeight(200)
        card.setStyleSheet(card_stylesheet())
        layout = QVBoxLayout()
        layout.setSpacing(12)
        card.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_lbl = QLabel("💾")
        icon_lbl.setFont(QFont("Segoe UI", 14))
        header.addWidget(icon_lbl)

        title = QLabel("Storage")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.addWidget(title)

        header.addStretch()

        # View all button
        btn = QPushButton("View all →")
        btn.setFont(QFont("Segoe UI", 9))
        btn.setFixedHeight(26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._show_all_drives())
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_deeper']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_orange']};
            }}
        """)
        header.addWidget(btn)
        layout.addLayout(header)

        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(8)
        layout.addLayout(self._storage_container)

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

            # Get drive letter and label
            drive_letter = partition.device
            mountpoint = partition.mountpoint

            # Try to get a friendly name
            try:
                import wmi
                w = wmi.WMI()
                for disk in w.Win32_LogicalDisk():
                    if disk.DeviceID == drive_letter:
                        vol_name = disk.VolumeName
                        break
                else:
                    vol_name = ""
            except:
                vol_name = ""

            # Calculate values
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            pct = usage.percent

            # Create storage row
            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_deeper']};
                    border-radius: 8px;
                    padding: 10px 12px;
                }}
            """)
            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row.setLayout(row_layout)

            # Disk icon + drive letter
            icon_col = QVBoxLayout()
            icon_col.setSpacing(3)
            icon_col.setAlignment(Qt.AlignCenter)
            icon_label = DiskIcon(size=44)
            icon_col.addWidget(icon_label)
            drive_lbl = QLabel(drive_letter.replace("\\", ""))
            drive_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            drive_lbl.setStyleSheet(f"color: {COLORS['accent_orange']};")
            drive_lbl.setAlignment(Qt.AlignCenter)
            icon_col.addWidget(drive_lbl)

            row_layout.addLayout(icon_col)

            # Drive info
            info_box = QVBoxLayout()
            info_box.setSpacing(2)

            # Name/location
            if vol_name:
                name_text = f"{vol_name} ({mountpoint})"
            else:
                name_text = mountpoint if mountpoint else drive_letter

            name_lbl = QLabel(name_text)
            name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            info_box.addWidget(name_lbl)

            # Progress bar
            bar = QProgressBar()
            bar.setValue(int(pct))
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_card']};
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background-color: {self._get_storage_color(pct)};
                    border-radius: 3px;
                }}
            """)
            info_box.addWidget(bar)

            row_layout.addLayout(info_box, stretch=1)

            # Size info
            size_box = QVBoxLayout()
            size_box.setSpacing(0)
            size_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            used_lbl = QLabel(f"{used_gb:.0f} GB used")
            used_lbl.setFont(QFont("Segoe UI", 9))
            used_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            used_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_box.addWidget(used_lbl)

            free_lbl = QLabel(f"{free_gb:.0f} GB free")
            free_lbl.setFont(QFont("Segoe UI", 8))
            free_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            free_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_box.addWidget(free_lbl)

            row_layout.addLayout(size_box)

            # Percentage badge
            pct_box = QVBoxLayout()
            pct_box.setSpacing(0)
            pct_box.setAlignment(Qt.AlignCenter)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            pct_lbl.setStyleSheet(f"color: {self._get_storage_color(pct)};")
            pct_lbl.setAlignment(Qt.AlignCenter)
            pct_box.addWidget(pct_lbl)

            row_layout.addLayout(pct_box)

            self._storage_container.addWidget(row)

    def _get_storage_color(self, pct):
        """Get color based on usage percentage"""
        if pct > 90:
            return COLORS['accent_red']
        elif pct > 75:
            return COLORS['accent_orange']
        return COLORS['accent_green']

    def _show_all_drives(self):
        """Show all drives in a dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QProgressBar, QPushButton

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setMinimumSize(750, 450)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)

        # Drag state
        _drag_pos = None

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                nonlocal _drag_pos
                _drag_pos = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == Qt.LeftButton and _drag_pos:
                dialog.move(event.globalPos() - _drag_pos)
                event.accept()

        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                _drag_pos = None
                event.accept()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        dialog.setLayout(main_layout)

        # Header with drag handle
        header = QFrame()
        header.setStyleSheet(f"background-color: {COLORS['bg_card']}; border-radius: 8px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 12, 12, 12)
        header.setLayout(header_layout)
        header.setCursor(Qt.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("Storage Drives")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        header_layout.addStretch()

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

        main_layout.addWidget(header)

        # Drives container
        drives_container = QVBoxLayout()
        drives_container.setSpacing(14)
        main_layout.addLayout(drives_container)

        for partition in psutil.disk_partitions():
            if not partition.fstype:
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue

            drive_letter = partition.device
            mountpoint = partition.mountpoint

            try:
                import wmi
                w = wmi.WMI()
                vol_name = ""
                for disk in w.Win32_LogicalDisk():
                    if disk.DeviceID == drive_letter:
                        vol_name = disk.VolumeName or ""
                        break
            except:
                vol_name = ""

            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            pct = usage.percent

            # Drive card
            drive_card = QFrame()
            drive_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                    padding: 16px;
                }}
            """)
            drive_layout = QHBoxLayout()
            drive_layout.setSpacing(20)
            drive_card.setLayout(drive_layout)

            # Left icon + drive letter (no frame, just icon column)
            icon_col = QVBoxLayout()
            icon_col.setSpacing(3)
            icon_col.setAlignment(Qt.AlignCenter)
            disk_icon = DiskIcon(size=56)
            icon_col.addWidget(disk_icon)
            drive_lbl = QLabel(drive_letter.replace("\\", ""))
            drive_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
            drive_lbl.setStyleSheet(f"color: {COLORS['accent_orange']};")
            drive_lbl.setAlignment(Qt.AlignCenter)
            icon_col.addWidget(drive_lbl)

            drive_layout.addLayout(icon_col)

            # Center info
            info_layout = QVBoxLayout()
            info_layout.setSpacing(8)

            # Drive name
            if vol_name:
                name_text = f"{vol_name} ({mountpoint})"
            else:
                name_text = mountpoint if mountpoint else drive_letter

            name_lbl = QLabel(name_text)
            name_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            info_layout.addWidget(name_lbl)

            # Progress bar
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
            info_layout.addWidget(bar)

            # Stats row
            stats_row = QHBoxLayout()
            stats_row.setSpacing(16)

            used_lbl = QLabel(f"{used_gb:.1f} GB used")
            used_lbl.setFont(QFont("Segoe UI", 10))
            used_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            stats_row.addWidget(used_lbl)

            stats_row.addStretch()

            free_lbl = QLabel(f"{free_gb:.1f} GB free")
            free_lbl.setFont(QFont("Segoe UI", 10))
            free_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            stats_row.addWidget(free_lbl)

            total_lbl = QLabel(f"of {total_gb:.1f} GB total")
            total_lbl.setFont(QFont("Segoe UI", 10))
            total_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            stats_row.addWidget(total_lbl)

            info_layout.addLayout(stats_row)

            drive_layout.addLayout(info_layout, stretch=1)

            # Right percentage badge
            pct_box = QFrame()
            pct_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_deeper']};
                    border-radius: 10px;
                    padding: 12px 16px;
                }}
            """)
            pct_box_layout = QVBoxLayout()
            pct_box_layout.setSpacing(2)
            pct_box_layout.setContentsMargins(8, 8, 8, 8)
            pct_box_layout.setAlignment(Qt.AlignCenter)
            pct_box.setLayout(pct_box_layout)

            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
            pct_lbl.setStyleSheet(f"color: {self._get_storage_color(pct)};")
            pct_lbl.setAlignment(Qt.AlignCenter)
            pct_box_layout.addWidget(pct_lbl)

            used_of = QLabel("used")
            used_of.setFont(QFont("Segoe UI", 9))
            used_of.setStyleSheet(f"color: {COLORS['text_muted']};")
            used_of.setAlignment(Qt.AlignCenter)
            pct_box_layout.addWidget(used_of)

            drive_layout.addWidget(pct_box)

            drives_container.addWidget(drive_card)

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
                border-radius: 8px;
                padding: 6px 28px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        close_btn.clicked.connect(dialog.close)
        main_layout.addWidget(close_btn, 0, Qt.AlignRight)

        dialog.exec_()

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
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_blue']};
            }}
        """)
        btn.clicked.connect(self._show_all_alerts)
        layout.addWidget(btn)

        self._update_alerts([])

        return card

    def _get_alert_color(self, level):
        """Get color based on alert level"""
        if level == "red":
            return COLORS['accent_red']
        elif level == "yellow":
            return COLORS['accent_orange']
        return COLORS['accent_green']

    def _show_all_alerts(self):
        """Show all alerts in a dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setMinimumSize(750, 500)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)

        _drag_pos = None

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                nonlocal _drag_pos
                _drag_pos = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == Qt.LeftButton and _drag_pos:
                dialog.move(event.globalPos() - _drag_pos)
                event.accept()

        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                _drag_pos = None
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
        header.setCursor(Qt.SizeAllCursor)
        header.mousePressEvent = mousePressEvent
        header.mouseMoveEvent = mouseMoveEvent
        header.mouseReleaseEvent = mouseReleaseEvent

        title = QLabel("All Alerts")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        header_layout.addStretch()

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

        main_layout.addWidget(header)

        # Alerts container
        alerts_container = QVBoxLayout()
        alerts_container.setSpacing(14)
        main_layout.addLayout(alerts_container)

        # Generate current alerts
        alerts = []
        if hasattr(self, '_last_data'):
            alerts = self._generate_alerts(self._last_data)

        if not alerts:
            alerts = [{"level": "green", "title": "All systems normal", "desc": "No issues detected"}]

        for alert in alerts:
            level = alert.get("level", "green")
            title_text = alert.get("title", "")
            desc = alert.get("desc", "")
            color = self._get_alert_color(level)

            alert_card = QFrame()
            alert_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['accent_green']};
                    border-radius: 10px;
                    padding: 16px;
                }}
            """)
            alert_layout = QHBoxLayout()
            alert_layout.setSpacing(20)
            alert_card.setLayout(alert_layout)

            # Left color bar
            color_bar = QFrame()
            color_bar.setFixedWidth(4)
            color_bar.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            alert_layout.addWidget(color_bar)

            # Icon column
            icon_col = QVBoxLayout()
            icon_col.setAlignment(Qt.AlignCenter)
            icon_lbl = QLabel("●")
            icon_lbl.setFont(QFont("Segoe UI", 24))
            icon_lbl.setStyleSheet(f"color: {color};")
            icon_col.addWidget(icon_lbl)
            alert_layout.addLayout(icon_col)

            # Center info
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)

            title_lbl = QLabel(title_text)
            title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
            title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            info_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Segoe UI", 10))
            desc_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            info_layout.addWidget(desc_lbl)

            alert_layout.addLayout(info_layout, stretch=1)

            alerts_container.addWidget(alert_card)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 11))
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_blue']};
            }}
        """)
        close_btn.clicked.connect(dialog.close)
        main_layout.addWidget(close_btn, 0, Qt.AlignRight)

        dialog.exec_()

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
            color = self._get_alert_color(level)

            item = QFrame()
            item.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_deeper']};
                    border: 1px solid {COLORS['accent_green']};
                    border-radius: 8px;
                    padding: 10px 12px;
                }}
            """)
            item_layout = QHBoxLayout()
            item_layout.setSpacing(10)
            item_layout.setContentsMargins(8, 8, 8, 8)
            item.setLayout(item_layout)

            # Text
            txt_vbox = QVBoxLayout()
            txt_vbox.setSpacing(1)
            t = QLabel(title)
            t.setFont(QFont("Segoe UI", 11, QFont.Bold))
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

        # GPU
        if 'gpu' in data:
            gpu = data['gpu']
            if gpu.get('available'):
                load = gpu.get('load')
                temp = gpu.get('temperature')
                fan = gpu.get('fan_speed')
                power = gpu.get('power')

                # Update gauge with load percentage
                if load is not None:
                    self._gpu_card.gauge.set_value(load)
                    self._gpu_card.sparkline.push(load)
                    self._gpu_history.append(load)
                    # Update GPU detail chart
                    self._gpu_detail_chart.sparkline.push(load)

                # Update stats: Temp, Fan, Power
                temp_str = f"{temp:.0f} °C" if temp is not None else "-- °C"
                fan_str = f"{fan} RPM" if fan is not None else "-- RPM"
                power_str = f"{power:.0f} W" if power is not None else "-- W"

                for i, val in enumerate([temp_str, fan_str, power_str]):
                    self._gpu_card.stats[i].setText(val)

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

        # Size grip for resizing
        size_grip = QSizeGrip(dialog)
        size_grip.setFixedSize(16, 16)

        main_layout.addLayout(btn_layout)

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
