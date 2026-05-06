"""
Network View - Advanced Network Monitoring Dashboard
Professional enterprise-grade network monitoring with real-time data
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QGridLayout, QProgressBar, QTabWidget, QTabBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPointF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QBrush, QIcon, QPolygonF, QPaintEvent

import psutil
import socket
import platform
import time
from collections import deque
from typing import Dict, List, Optional, Tuple
import qtawesome as qta

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from core.signals import signal_bus
from widgets.card import Card


class MiniSparkline(QWidget):
    """Mini sparkline graph for KPI cards"""
    def __init__(self, color="#10b981", parent=None):
        super().__init__(parent)
        self._color = color
        self._history = deque(maxlen=30)
        self._pending_update = False

        self.setFixedHeight(40)
        self.setMinimumWidth(80)

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def add_point(self, value: float):
        self._history.append(value)
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def paintEvent(self, a0):
        if not self._history:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w = self.width()
        h = self.height()

        # Draw line
        points = []
        step_x = w / (len(self._history) - 1) if len(self._history) > 1 else 0
        max_val = max(self._history) if max(self._history) > 0 else 1

        for i, val in enumerate(self._history):
            x = step_x * i
            y = h - (val / max_val * h * 0.9) - 2
            points.append((x, y))

        if len(points) > 1:
            # Fill
            fill_path = points + [(w, h), (0, h)]
            gradient = QLinearGradient(0, 0, 0, h)
            gradient.setColorAt(0, QColor(self._color))
            gradient.setColorAt(1, QColor(c.BG_PRIMARY))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)

            qpoints = [QPointF(int(x), int(y)) for x, y in fill_path]
            painter.drawPolygon(*qpoints)

            # Line
            painter.setPen(QPen(QColor(self._color), 1.5))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i+1][0]), int(points[i+1][1]))

        painter.end()


class KpiCard(QFrame):
    """Premium KPI stat card with mini graph"""
    def __init__(self, title: str, icon: str, accent: str, unit: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._accent = accent
        self._unit = unit
        self._value = "0"
        self._sub_text = ""

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        layout.setSpacing(S.px(10))
        self.setLayout(layout)

        # Top row: icon + title
        top_row = QHBoxLayout()
        top_row.setSpacing(S.px(10))

        icon_label = QLabel()
        try:
            icon = qta.icon(self._icon, color=self._accent, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(20), S.px(20)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        top_row.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(11)))
        title_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        top_row.addWidget(title_label)
        top_row.addStretch()

        layout.addLayout(top_row)

        # Value + sparkline
        value_row = QHBoxLayout()
        value_row.setSpacing(S.px(12))

        self._value_label = QLabel("0")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(28), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        value_row.addWidget(self._value_label)

        self._unit_label = QLabel(self._unit)
        self._unit_label.setFont(QFont("Segoe UI", S.font_pt(12)))
        self._unit_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        value_row.addWidget(self._unit_label)

        value_row.addStretch()

        self._sparkline = MiniSparkline(color=self._accent)
        self._sparkline.setFixedWidth(S.px(80))
        value_row.addWidget(self._sparkline)

        layout.addLayout(value_row)

        # Sub text
        self._sub_label = QLabel("")
        self._sub_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._sub_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self._sub_label)

    def _apply_theme(self):
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

    def set_value(self, value: str, sub_text: str = ""):
        self._value = value
        self._value_label.setText(value)
        self._sub_label.setText(sub_text)
        self._sparkline.add_point(float(value) if value.replace(".", "").replace(",", "").isdigit() else 0)


class NetworkTrafficGraph(QWidget):
    """Main real-time network traffic graph"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._upload_history = deque(maxlen=60)
        self._download_history = deque(maxlen=60)
        self._pending_update = False
        self._max_value = 100.0

        self.setMinimumHeight(200)

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def add_data(self, upload: float, download: float):
        self._upload_history.append(upload)
        self._download_history.append(download)

        # Auto-scale max
        max_val = max(max(self._upload_history) if self._upload_history else 1,
                     max(self._download_history) if self._download_history else 1)
        self._max_value = max(100, max_val * 1.2)

        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w = self.width()
        h = self.height()

        # Fill background
        painter.fillRect(self.rect(), QColor(c.BG_CARD))

        # Margins
        ml, mr, mt, mb = 50, 20, 20, 30
        graph_w = w - ml - mr
        graph_h = h - mt - mb

        # Draw grid
        painter.setPen(QPen(QColor(c.BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = mt + graph_h * i / 4
            painter.drawLine(int(ml), int(y), int(w - mr), int(y))

        # Y-axis labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(c.TEXT_MUTED))
        for i in range(5):
            val = self._max_value * (4 - i) / 4
            y = mt + graph_h * i / 4
            label = self._format_value(val)
            fm = painter.fontMetrics()
            painter.drawText(int(ml - fm.horizontalAdvance(label) - 5), int(y + 4), label)

        # Draw data
        def draw_series(history, color):
            if len(history) < 2:
                return
            points = []
            step_x = graph_w / (len(history) - 1)
            for i, val in enumerate(history):
                x = ml + step_x * i
                y = mt + graph_h - (val / self._max_value * graph_h)
                points.append((x, y))

            # Fill
            fill_points = points + [(points[-1][0], mt + graph_h), (points[0][0], mt + graph_h)]
            gradient = QLinearGradient(0, mt, 0, mt + graph_h)
            gradient.setColorAt(0, QColor(color))
            gradient.setColorAt(1, QColor(c.BG_PRIMARY))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            qpoints = [QPointF(int(x), int(y)) for x, y in fill_points]
            painter.drawPolygon(*qpoints)

            # Line
            painter.setPen(QPen(QColor(color), 2))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i+1][0]), int(points[i+1][1]))

        if len(self._download_history) > 1:
            draw_series(self._download_history, c.ACCENT_CYAN)
        if len(self._upload_history) > 1:
            draw_series(self._upload_history, c.ACCENT_PURPLE)

        # Legend (positioned above bottom edge to avoid truncation)
        legend_y = h - 20
        painter.setFont(QFont("Segoe UI", 9))

        # Download
        painter.setPen(QColor(c.ACCENT_CYAN))
        painter.drawText(int(w / 2 - 60), legend_y, "▼ Download")
        # Upload
        painter.setPen(QColor(c.ACCENT_PURPLE))
        painter.drawText(int(w / 2 + 20), legend_y, "▲ Upload")

        painter.end()

    def _format_value(self, val: float) -> str:
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"{val/1_000:.1f}K"
        return f"{val:.0f}"


class DonutChart(QWidget):
    """Donut chart for protocol distribution"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Dict[str, float] = {}
        self._colors = ["#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]

        self.setFixedSize(140, 140)

    def set_data(self, data: Dict[str, float]):
        self._data = data
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w = self.width()
        h = self.height()
        size = min(w, h)

        # Background
        painter.fillRect(self.rect(), QColor(c.BG_CARD))

        cx, cy = w / 2, h / 2
        outer_r = size / 2 - 10
        inner_r = outer_r * 0.6

        total = sum(self._data.values()) if self._data else 1
        start_angle = 90

        for i, (label, value) in enumerate(self._data.items()):
            if value <= 0:
                continue
            angle = (value / total) * 360

            painter.setBrush(QBrush(QColor(self._colors[i % len(self._colors)])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(int(cx - outer_r), int(cy - outer_r), int(outer_r * 2), int(outer_r * 2),
                          int(start_angle * 16), int(-angle * 16))

            start_angle += angle

        # Center circle (hole)
        painter.setBrush(QBrush(QColor(c.BG_CARD)))
        painter.drawEllipse(int(cx - inner_r), int(cy - inner_r), int(inner_r * 2), int(inner_r * 2))

        painter.end()


class AlertCard(QFrame):
    """Premium alert notification card"""
    def __init__(self, severity: str, message: str, timestamp: str, parent=None):
        super().__init__(parent)
        self._severity = severity
        self._message = message
        self._timestamp = timestamp
        self._setup_ui()

    def _setup_ui(self):
        c = theme_manager.colors

        # Severity color
        severity_colors = {
            "critical": c.ACCENT_RED,
            "warning": c.ACCENT_ORANGE,
            "info": c.ACCENT_BLUE,
        }
        accent = severity_colors.get(self._severity, c.ACCENT_BLUE)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_HOVER};
                border: none;
                border-left: 3px solid {accent};
                border-radius: {S.px(6)}px;
                padding: {S.px(8)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
        layout.setSpacing(2)
        self.setLayout(layout)

        msg_label = QLabel(self._message)
        msg_label.setFont(QFont("Segoe UI", S.font_pt(11)))
        msg_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(msg_label)

        time_label = QLabel("just now")
        time_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        time_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        layout.addWidget(time_label)


class InterfaceStatusCard(QFrame):
    """Network interface status card"""
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._setup_ui()

    def _setup_ui(self):
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_HOVER};
                border: none;
                border-radius: {S.px(8)}px;
                padding: {S.px(12)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        # Header
        header = QHBoxLayout()
        header.setSpacing(S.px(8))

        status_dot = QFrame()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet(f"""
            background-color: {c.ACCENT_GREEN};
            border-radius: 4px;
        """)
        header.addWidget(status_dot)

        name_label = QLabel(self._name)
        name_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(name_label)

        header.addStretch()

        layout.addLayout(header)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_SECONDARY};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {c.ACCENT_CYAN};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self._progress)

        # Stats
        stats = QHBoxLayout()
        stats.setSpacing(S.px(16))

        self._speed_label = QLabel("0 Mbps")
        self._speed_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._speed_label.setStyleSheet(f"color: {c.ACCENT_CYAN}; background: transparent;")
        stats.addWidget(self._speed_label)

        self._usage_label = QLabel("0% used")
        self._usage_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._usage_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        stats.addWidget(self._usage_label)

        stats.addStretch()

        layout.addLayout(stats)

    def update_status(self, speed: str, usage: float):
        self._speed_label.setText(speed)
        self._usage_label.setText(f"{usage:.1f}% used")
        self._progress.setValue(int(usage))


class DeviceRow(QFrame):
    """Top device by traffic row with animated bar"""
    def __init__(self, rank: int, ip: str, hostname: str, traffic: str, percentage: float, parent=None):
        super().__init__(parent)
        self._setup_ui(rank, ip, hostname, traffic, percentage)

    def _setup_ui(self, rank: int, ip: str, hostname: str, traffic: str, percentage: float):
        c = theme_manager.colors

        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                padding: {S.px(4)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(S.px(4))
        self.setLayout(layout)

        # Top row
        row = QHBoxLayout()
        row.setSpacing(S.px(12))

        rank_label = QLabel(f"#{rank}")
        rank_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        rank_label.setFixedWidth(24)
        rank_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        row.addWidget(rank_label)

        ip_label = QLabel(ip)
        ip_label.setFont(QFont("Segoe UI", S.font_pt(11)))
        ip_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        row.addWidget(ip_label)

        hostname_label = QLabel(hostname)
        hostname_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        hostname_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        hostname_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(hostname_label, stretch=1)

        traffic_label = QLabel(traffic)
        traffic_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        traffic_label.setStyleSheet(f"color: {c.ACCENT_CYAN}; background: transparent;")
        traffic_label.setFixedWidth(70)
        traffic_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(traffic_label)

        layout.addLayout(row)

        # Progress bar
        bar = QProgressBar()
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_SECONDARY};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {c.ACCENT_CYAN};
                border-radius: 2px;
            }}
        """)
        bar.setValue(int(percentage))
        layout.addWidget(bar)


class NetworkTopologyWidget(QWidget):
    """Network topology map visualization"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w = self.width()
        h = self.height()

        painter.fillRect(self.rect(), QColor(c.BG_CARD))

        # Draw network nodes
        nodes = [
            ("Internet", w/2, 30, c.ACCENT_BLUE),
            ("Router", w/2, 80, c.ACCENT_GREEN),
            ("Server", w/3, 130, c.ACCENT_ORANGE),
            ("NAS", w*2/3, 130, c.ACCENT_PURPLE),
            ("PC 1", w/4, 170, c.TEXT_SECONDARY),
            ("PC 2", w/2, 170, c.TEXT_SECONDARY),
            ("Camera", w*3/4, 170, c.TEXT_SECONDARY),
        ]

        def draw_node(label, x, y, color):
            # Node circle
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - 12), int(y - 12), 24, 24)

            # Glow effect
            glow = QLinearGradient(x - 20, y, x + 20, y)
            glow.setColorAt(0, QColor(color))
            glow.setColorAt(1, QColor(color))
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setOpacity(0.3)
            painter.drawEllipse(int(x - 16), int(y - 16), 32, 32)
            painter.setOpacity(1.0)

            # Label
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(c.TEXT_PRIMARY))
            fm = painter.fontMetrics()
            label_w = fm.horizontalAdvance(label)
            painter.drawText(int(x - label_w/2), int(y + 22), label)

        # Draw connections
        painter.setPen(QPen(QColor(c.BORDER), 1, Qt.PenStyle.DashLine))
        connections = [
            (w/2, 18, w/2, 68),
            (w/2, 68, w/3, 118),
            (w/2, 68, w*2/3, 118),
            (w/3, 118, w/4, 158),
            (w/3, 118, w/2, 158),
            (w*2/3, 118, w*3/4, 158),
        ]
        for x1, y1, x2, y2 in connections:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw nodes
        for label, x, y, color in nodes:
            draw_node(label, x, y, color)

        painter.end()


class ConnectionsTable(QTableWidget):
    """Active network connections table"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        c = theme_manager.colors

        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(["Local IP", "Local Port", "Remote", "Remote Port", "Protocol", "State", "Duration"])

        header = self.horizontalHeader()
        header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.setFont(QFont("Segoe UI", 10))
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: none;
                border-radius: {S.px(8)}px;
                gridline-color: {c.BORDER};
            }}
            QTableWidget::item {{
                padding: {S.px(8)}px;
                border-bottom: 1px solid {c.BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {c.BG_HOVER};
            }}
            QHeaderView::section {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_SECONDARY};
                padding: {S.px(10)}px;
                border: none;
                border-bottom: 2px solid {c.BORDER};
                font-weight: bold;
            }}
        """)

    def update_connections(self, connections: List[Dict]):
        self.setRowCount(0)
        for conn in connections[:50]:  # Limit to 50
            row = self.rowCount()
            self.insertRow(row)

            items = [
                conn.get("local_ip", "-"),
                str(conn.get("local_port", "-")),
                conn.get("remote", "-"),
                str(conn.get("remote_port", "-")),
                conn.get("protocol", "-"),
                conn.get("state", "-"),
                conn.get("duration", "-"),
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setFont(QFont("Segoe UI", 9))
                self.setItem(row, col, item)


class NetworkView(QWidget, ScaleMixin):
    """Advanced Network Monitoring Dashboard"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self._last_bytes_sent = 0
        self._last_bytes_recv = 0
        self._last_check = time.time()
        self._connections: List[Dict] = []

        self._setup_ui()
        self._connect_signals()
        self._start_timers()

    def _setup_ui(self):
        """Setup network monitoring dashboard UI"""
        # Main scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_widget.setMaximumWidth(1400)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(20), S.px(20), S.px(20), S.px(20))
        main_layout.setSpacing(S.px(20))
        content_widget.setLayout(main_layout)

        self._scroll_area.setWidget(content_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll_area)
        self.setLayout(layout)

        # ===== TOP BAR =====
        self._setup_top_bar(main_layout)

        # ===== KPI CARDS =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(S.px(16))

        self._traffic_card = KpiCard("Total Traffic", "mdi.network", "#06b6d4", "Mbps")
        kpi_layout.addWidget(self._traffic_card, stretch=1)

        self._connections_card = KpiCard("Active Connections", "mdi.link", "#10b981", "")
        kpi_layout.addWidget(self._connections_card, stretch=1)

        self._devices_card = KpiCard("Online Devices", "mdi.lan", "#3b82f6", "")
        kpi_layout.addWidget(self._devices_card, stretch=1)

        self._ping_card = KpiCard("Average Ping", "mdi.access-point", "#f59e0b", "ms")
        kpi_layout.addWidget(self._ping_card, stretch=1)

        main_layout.addLayout(kpi_layout)

        # ===== MAIN CONTENT GRID =====
        content_grid = QGridLayout()
        content_grid.setSpacing(S.px(16))

        # Left column (wider)
        left_col = QVBoxLayout()
        left_col.setSpacing(S.px(16))

        # Main traffic graph
        traffic_card = Card(title="Network Traffic", icon="📊")
        self._traffic_graph = NetworkTrafficGraph()
        traffic_card.add_widget(self._traffic_graph)
        left_col.addWidget(traffic_card)

        # Connections table
        conn_card = Card(title="Active Connections", icon="🔗")
        self._connections_table = ConnectionsTable()
        conn_card.add_widget(self._connections_table)
        left_col.addWidget(conn_card)

        content_grid.addLayout(left_col, 0, 0, 2, 1)

        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(S.px(16))

        # Alerts panel
        alerts_card = Card(title="Active Alerts", icon="⚠️")
        self._alerts_container = QVBoxLayout()
        self._alerts_container.setSpacing(S.px(8))
        alerts_widget = QWidget()
        alerts_widget.setLayout(self._alerts_container)
        alerts_card.add_widget(alerts_widget)
        right_col.addWidget(alerts_card)

        # Interface status
        interfaces_card = Card(title="Interface Status", icon="🌐")
        self._interfaces_container = QVBoxLayout()
        self._interfaces_container.setSpacing(S.px(8))
        interfaces_widget = QWidget()
        interfaces_widget.setLayout(self._interfaces_container)
        interfaces_card.add_widget(interfaces_widget)
        right_col.addWidget(interfaces_card)

        content_grid.addLayout(right_col, 0, 1, 1, 1)

        # Middle panels row
        middle_row = QHBoxLayout()
        middle_row.setSpacing(S.px(16))

        # Traffic distribution
        dist_card = Card(title="Traffic Distribution", icon="🥧")
        dist_content = QHBoxLayout()
        dist_content.setSpacing(S.px(20))

        self._donut_chart = DonutChart()
        self._donut_chart.setFixedSize(120, 120)
        dist_content.addWidget(self._donut_chart)

        self._protocol_legend = QVBoxLayout()
        self._protocol_legend.setSpacing(S.px(6))
        legend_widget = QWidget()
        legend_widget.setLayout(self._protocol_legend)
        dist_content.addWidget(legend_widget)

        dist_widget = QWidget()
        dist_widget.setLayout(dist_content)
        dist_card.add_widget(dist_widget)
        middle_row.addWidget(dist_card, stretch=1)

        # Top devices
        devices_card = Card(title="Top Devices by Traffic", icon="📱")
        self._devices_list = QVBoxLayout()
        self._devices_list.setSpacing(S.px(4))
        devices_widget = QWidget()
        devices_widget.setLayout(self._devices_list)
        devices_card.add_widget(devices_widget)
        middle_row.addWidget(devices_card, stretch=1)

        # Network topology
        topology_card = Card(title="Network Map", icon="🗺️")
        topology_card.add_widget(NetworkTopologyWidget())
        middle_row.addWidget(topology_card, stretch=1)

        content_grid.addLayout(middle_row, 1, 1, 1, 1)

        main_layout.addLayout(content_grid)

        # System status
        self._setup_system_status(main_layout)

        main_layout.addStretch()

    def _setup_top_bar(self, parent_layout):
        """Setup top navigation bar"""
        c = theme_manager.colors

        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
                padding: {S.px(12)}px {S.px(16)}px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setSpacing(S.px(16))
        layout.setContentsMargins(S.px(16), S.px(8), S.px(16), S.px(8))
        top_bar.setLayout(layout)

        # Live indicator
        live_layout = QHBoxLayout()
        live_layout.setSpacing(S.px(8))

        live_dot = QFrame()
        live_dot.setFixedSize(10, 10)
        live_dot.setStyleSheet(f"""
            background-color: {c.ACCENT_GREEN};
            border-radius: 5px;
        """)
        live_layout.addWidget(live_dot)

        live_label = QLabel("LIVE")
        live_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        live_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        live_layout.addWidget(live_label)

        layout.addLayout(live_layout)

        # Time range dropdown
        self._time_dropdown = QComboBox()
        self._time_dropdown.addItems(["Last 1 hour", "Last 24 hours", "Last 7 days", "Last 30 days"])
        self._time_dropdown.setFixedWidth(120)
        layout.addWidget(self._time_dropdown)

        # Refresh dropdown
        self._refresh_dropdown = QComboBox()
        self._refresh_dropdown.addItems(["5s", "10s", "30s", "60s"])
        self._refresh_dropdown.setFixedWidth(70)
        self._refresh_dropdown.setCurrentText("5s")
        layout.addWidget(self._refresh_dropdown)

        layout.addStretch()

        # Icons
        icons_layout = QHBoxLayout()
        icons_layout.setSpacing(S.px(16))

        for icon_name in ["fa5s.search", "fa5s.bell", "fa5s.cog", "fa5s.expand"]:
            try:
                icon = qta.icon(icon_name, color=c.TEXT_MUTED)
                icon_btn = QPushButton()
                icon_btn.setIcon(icon)
                icon_btn.setFixedSize(36, 36)
                icon_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border: none;
                        border-radius: {S.px(8)}px;
                    }}
                    QPushButton:hover {{
                        background-color: {c.BG_HOVER};
                    }}
                """)
                icons_layout.addWidget(icon_btn)
            except Exception:
                pass

        layout.addLayout(icons_layout)

        parent_layout.addWidget(top_bar)

    def _setup_system_status(self, parent_layout):
        """Setup system status panel"""
        c = theme_manager.colors

        status_card = Card(title="System Status", icon="🛡️")

        status_layout = QHBoxLayout()
        status_layout.setSpacing(S.px(32))

        # Health
        health_widget = QWidget()
        health_layout = QVBoxLayout()
        health_layout.setSpacing(4)
        health_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        health_icon = QLabel()
        try:
            icon = qta.icon("mdi.shield-check", color=c.ACCENT_GREEN, scale=1.5)
            health_icon.setPixmap(icon.pixmap(32, 32))
        except Exception:
            health_icon.setText("✓")
        health_icon.setStyleSheet("background: transparent;")
        health_layout.addWidget(health_icon)

        health_label = QLabel("Healthy")
        health_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        health_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        health_layout.addWidget(health_label)

        health_widget.setLayout(health_layout)
        status_layout.addWidget(health_widget)

        # Uptime
        uptime_widget = QWidget()
        uptime_layout = QVBoxLayout()
        uptime_layout.setSpacing(2)
        uptime_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        uptime_title = QLabel("Uptime")
        uptime_title.setFont(QFont("Segoe UI", 9))
        uptime_title.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        uptime_layout.addWidget(uptime_title)

        self._uptime_label = QLabel("0d 0h 0m")
        self._uptime_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._uptime_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        uptime_layout.addWidget(self._uptime_label)

        uptime_widget.setLayout(uptime_layout)
        status_layout.addWidget(uptime_widget)

        # Start time
        start_widget = QWidget()
        start_layout = QVBoxLayout()
        start_layout.setSpacing(2)
        start_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_title = QLabel("Started")
        start_title.setFont(QFont("Segoe UI", 9))
        start_title.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        start_layout.addWidget(start_title)

        self._start_label = QLabel("--:--")
        self._start_label.setFont(QFont("Segoe UI", 12))
        self._start_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        start_layout.addWidget(self._start_label)

        start_widget.setLayout(start_layout)
        status_layout.addWidget(start_widget)

        # Active monitors
        monitors_widget = QWidget()
        monitors_layout = QVBoxLayout()
        monitors_layout.setSpacing(2)
        monitors_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        monitors_title = QLabel("Monitoring")
        monitors_title.setFont(QFont("Segoe UI", 9))
        monitors_title.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        monitors_layout.addWidget(monitors_title)

        monitors_value = QLabel("7 services")
        monitors_value.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        monitors_value.setStyleSheet(f"color: {c.ACCENT_BLUE}; background: transparent;")
        monitors_layout.addWidget(monitors_value)

        monitors_widget.setLayout(monitors_layout)
        status_layout.addWidget(monitors_widget)

        status_layout.addStretch()

        status_card.add_layout(status_layout)
        parent_layout.addWidget(status_card)

    def _connect_signals(self):
        """Connect to signal bus"""
        signal_bus.data_updated.connect(self._on_data_updated)
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _start_timers(self):
        """Start update timers"""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._collect_connections)
        self._refresh_timer.start(5000)  # 5 seconds

        # Initial connection collection
        QTimer.singleShot(500, self._collect_connections)

        # Start time tracker
        self._start_time = time.time()

    def _on_data_updated(self, data: dict):
        """Handle data update from signal bus"""
        if 'network' not in data:
            return

        net = data['network']

        # Calculate traffic speed
        current_time = time.time()
        bytes_sent = net.get('bytes_sent', 0)
        bytes_recv = net.get('bytes_recv', 0)

        time_delta = max(current_time - self._last_check, 0.001)

        upload_speed = (bytes_sent - self._last_bytes_sent) / time_delta / 1024 / 1024  # MB/s
        download_speed = (bytes_recv - self._last_bytes_recv) / time_delta / 1024 / 1024  # MB/s

        self._last_bytes_sent = bytes_sent
        self._last_bytes_recv = bytes_recv
        self._last_check = current_time

        # Convert to Mbps for display
        upload_mbps = upload_speed * 8
        download_mbps = download_speed * 8

        # Update KPI cards
        total_speed = upload_mbps + download_mbps
        self._traffic_card.set_value(
            f"{total_speed:.2f}",
            f"↓ {download_mbps:.1f} / ↑ {upload_mbps:.1f}"
        )

        # Update traffic graph
        self._traffic_graph.add_data(upload_mbps, download_mbps)

        # Update connection count
        conn_count = len(self._connections)
        self._connections_card.set_value(str(conn_count), "TCP / UDP connections")

        # Update ping card (simulated)
        ping_value = self._simulate_ping()
        self._ping_card.set_value(str(ping_value), "min: 1ms / max: 45ms")

    def _simulate_ping(self):
        """Simulate ping value for demo"""
        import random
        return round(random.uniform(5, 25), 1)

    def _collect_connections(self):
        """Collect active network connections"""
        try:
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if conn.status:
                        local_addr = conn.laddr.ip if conn.laddr else "-"
                        local_port = conn.laddr.port if conn.laddr else "-"
                        remote_addr = conn.raddr.ip if conn.raddr else "-"
                        remote_port = conn.raddr.port if conn.raddr else "-"

                        protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"

                        connections.append({
                            "local_ip": local_addr,
                            "local_port": local_port,
                            "remote": remote_addr,
                            "remote_port": remote_port,
                            "protocol": protocol,
                            "state": conn.status or "-",
                            "duration": "-",
                        })
                except (ValueError, OSError):
                    pass

            self._connections = connections
            self._connections_table.update_connections(connections)

            # Update devices card
            self._devices_card.set_value(str(len(connections)), "Established connections")

            # Update protocol distribution
            self._update_protocol_distribution()

            # Update top devices
            self._update_top_devices()

            # Update alerts
            self._update_alerts()

            # Update interfaces
            self._update_interfaces()

        except Exception as e:
            pass

    def _update_protocol_distribution(self):
        """Update donut chart with protocol distribution"""
        tcp_count = sum(1 for c in self._connections if c.get("protocol") == "TCP")
        udp_count = sum(1 for c in self._connections if c.get("protocol") == "UDP")
        other = max(len(self._connections) - tcp_count - udp_count, 0)

        self._donut_chart.set_data({
            "TCP": tcp_count,
            "UDP": udp_count,
            "Other": other,
        })

        # Update legend
        while self._protocol_legend.count():
            item = self._protocol_legend.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = theme_manager.colors
        legend_items = [
            ("TCP", tcp_count, "#3b82f6"),
            ("UDP", udp_count, "#10b981"),
            ("Other", other, "#8b5cf6"),
        ]

        for label, count, color in legend_items:
            row = QHBoxLayout()
            row.setSpacing(8)

            color_dot = QFrame()
            color_dot.setFixedSize(10, 10)
            color_dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
            row.addWidget(color_dot)

            label_widget = QLabel(f"{label}: {count}")
            label_widget.setFont(QFont("Segoe UI", 10))
            label_widget.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
            row.addWidget(label_widget)

            row.addStretch()

            legend_widget = QWidget()
            legend_widget.setLayout(row)
            self._protocol_legend.addWidget(legend_widget)

    def _update_top_devices(self):
        """Update top devices list"""
        while self._devices_list.count():
            item = self._devices_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Simulated top devices
        devices = [
            (1, "192.168.1.1", "Router", "245.8 MB", 85),
            (2, "192.168.1.100", "DESKTOP-PC", "128.4 MB", 52),
            (3, "192.168.1.101", "LAPTOP", "89.2 MB", 36),
            (4, "192.168.1.102", "PHONE", "34.1 MB", 14),
            (5, "192.168.1.103", "TV", "12.3 MB", 5),
        ]

        for rank, ip, hostname, traffic, percentage in devices:
            row = DeviceRow(rank, ip, hostname, traffic, percentage)
            self._devices_list.addWidget(row)

    def _update_alerts(self):
        """Update alerts panel"""
        while self._alerts_container.count():
            item = self._alerts_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = theme_manager.colors

        # Simulated alerts
        alerts = [
            ("warning", "High ping to 8.8.8.8", "2 min ago"),
            ("info", "New device connected: PHONE", "5 min ago"),
        ]

        if not alerts:
            no_alerts = QLabel("No active alerts")
            no_alerts.setFont(QFont("Segoe UI", 11))
            no_alerts.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
            self._alerts_container.addWidget(no_alerts)
        else:
            for severity, message, time_ in alerts:
                alert = AlertCard(severity, message, time_)
                self._alerts_container.addWidget(alert)

        self._alerts_container.addStretch()

    def _update_interfaces(self):
        """Update network interfaces status"""
        while self._interfaces_container.count():
            item = self._interfaces_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = theme_manager.colors

        # Get real interfaces
        interfaces = []
        try:
            stats = psutil.net_io_counters(pernic=True)
            for iface, data in stats.items():
                interfaces.append({
                    "name": iface,
                    "bytes_sent": data.bytes_sent,
                    "bytes_recv": data.bytes_recv,
                })
        except Exception:
            pass

        # Add simulated interfaces if none found
        if not interfaces:
            interfaces = [
                {"name": "Ethernet", "bytes_sent": 0, "bytes_recv": 0},
                {"name": "Wi-Fi", "bytes_sent": 0, "bytes_recv": 0},
            ]

        # Create interface cards
        row = None
        for i, iface in enumerate(interfaces[:4]):  # Max 4 interfaces
            if i % 2 == 0:
                row = QHBoxLayout()
                row.setSpacing(S.px(12))
                self._interfaces_container.addLayout(row)

            card = InterfaceStatusCard(iface["name"])
            card.update_status("100 Mbps", 45.0)  # Simulated values
            row.addWidget(card, stretch=1)

        self._interfaces_container.addStretch()

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self._setup_ui()
        self.update()

    def on_scale_changed(self, factor: float):
        """Handle DPI scale change"""
        self._setup_ui()
        self.update()

    def update_data(self, data: dict):
        """Public method to update data - called from outside"""
        self._on_data_updated(data)
