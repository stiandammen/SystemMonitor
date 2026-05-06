"""
Processes View - Professional Process Monitor
Clean, technician-focused interface with proper alignment
"""
import time
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QProgressBar, QScrollArea,
    QSizePolicy, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from styles.theme import theme_manager
from scaler import S, ScaleMixin


def c():
    """Get current theme colors"""
    return theme_manager.colors


# Status constants
STATUS_RUNNING = "running"
STATUS_SUSPENDED = "suspended"
STATUS_NOT_RESPONDING = "not responding"
STATUS_ERROR = "error"


STATUS_COLORS = {
    STATUS_RUNNING: "#10b981",
    STATUS_SUSPENDED: "#ffd740",
    STATUS_NOT_RESPONDING: "#f97316",
    STATUS_ERROR: "#ef4444",
}


class SummaryCard(QFrame):
    """Compact summary stat card"""

    def __init__(self, title: str, icon: str = "", accent: str = "#00ab84", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._setup_ui(title, icon)
        self._apply_style()

    def _setup_ui(self, title: str, icon: str):
        colors = c()
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(6)

        # Icon
        icon_lbl = QLabel()
        try:
            qicon = qta.icon(icon, color=self._accent)
            icon_lbl.setPixmap(qicon.pixmap(12, 12))
        except:
            pass
        header.addWidget(icon_lbl)

        # Title
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        title_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(title_lbl)
        header.addStretch()

        layout.addLayout(header)

        # Value
        self._value_lbl = QLabel("0")
        self._value_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._value_lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
        layout.addWidget(self._value_lbl)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setMaximumHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        layout.addWidget(self._progress)

    def _apply_style(self):
        colors = c()
        self.setStyleSheet(f"""
            SummaryCard {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 8px;
            }}
        """)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self._accent};
                border-radius: 2px;
            }}
        """)

    def set_value(self, value: str):
        self._value_lbl.setText(value)

    def set_progress(self, percent: float):
        self._progress.setValue(int(min(percent, 100)))


class ProcessesView(QWidget, ScaleMixin):
    """Professional Process Monitor with clean, aligned interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes = []
        self._system_data = {}
        self._cpu_baseline_done = False
        self._last_net_sent = 0
        self._last_net_recv = 0
        self._last_disk_read = 0
        self._last_disk_write = 0

        self.scale_connect()
        self._setup_ui()
        self._apply_theme()
        self._start_update_timer()

    def _setup_ui(self):
        """Setup main UI"""
        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Summary cards row
        summary_row = self._create_summary_row()
        main_layout.addWidget(summary_row)

        # Search bar
        search_frame = self._create_search_bar()
        main_layout.addWidget(search_frame)

        # Process table
        table_frame = self._create_table()
        main_layout.addWidget(table_frame, stretch=1)

    def _create_summary_row(self) -> QFrame:
        """Create summary statistics row"""
        colors = c()

        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet("background: transparent;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        frame.setLayout(layout)

        # CPU
        self._cpu_card = SummaryCard("CPU", "ph.cpu", colors.ACCENT_BLUE)
        self._cpu_card.set_value("0%")
        layout.addWidget(self._cpu_card, stretch=1)

        # Memory
        self._mem_card = SummaryCard("Memory", "mdi.memory", colors.ACCENT_PURPLE)
        self._mem_card.set_value("0 GB / 0 GB")
        self._mem_card.set_progress(0)
        layout.addWidget(self._mem_card, stretch=1)

        # Disk I/O
        self._disk_card = SummaryCard("Disk R/W", "fa5s.hdd", colors.ACCENT_ORANGE)
        self._disk_card.set_value("0 / 0 MB/s")
        layout.addWidget(self._disk_card, stretch=1)

        # Network
        self._net_card = SummaryCard("Network", "ph.wifi-high", colors.ACCENT_CYAN)
        self._net_card.set_value("0 / 0 Mbps")
        layout.addWidget(self._net_card, stretch=1)

        # Process count
        self._proc_card = SummaryCard("Processes", "ph.list", colors.TEXT_SECONDARY)
        self._proc_card.set_value("0")
        layout.addWidget(self._proc_card, stretch=1)

        return frame

    def _create_search_bar(self) -> QFrame:
        """Create search input"""
        colors = c()

        frame = QFrame()
        frame.setFixedHeight(44)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)
        frame.setLayout(layout)

        # Search icon
        search_icon = QLabel()
        try:
            icon = qta.icon("fa5s.search", color=colors.TEXT_MUTED)
            search_icon.setPixmap(icon.pixmap(14, 14))
        except:
            pass
        layout.addWidget(search_icon)

        # Input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by name or PID...")
        self._search_input.setFont(QFont("Segoe UI", 11))
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {colors.TEXT_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {colors.TEXT_MUTED};
            }}
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input, stretch=1)

        # Refresh button
        refresh_btn = QPushButton()
        try:
            icon = qta.icon("fa5s.sync", color=colors.TEXT_MUTED)
            refresh_btn.setIcon(icon)
        except:
            refresh_btn.setText("Refresh")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
            }}
        """)
        refresh_btn.clicked.connect(self._force_refresh)
        layout.addWidget(refresh_btn)

        return frame

    def _create_table(self) -> QFrame:
        """Create process table"""
        colors = c()

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        frame.setLayout(layout)

        # Table widget
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Name", "PID", "CPU %", "Memory MB", "User", "Threads", "Status"
        ])

        # Selection
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Header styling
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Column widths - adjusted for proper display
        self._table.setColumnWidth(0, 220)   # Name
        self._table.setColumnWidth(1, 80)     # PID
        self._table.setColumnWidth(2, 80)     # CPU
        self._table.setColumnWidth(3, 100)    # Memory
        self._table.setColumnWidth(4, 120)    # User
        self._table.setColumnWidth(5, 70)     # Threads
        self._table.setColumnWidth(6, 100)    # Status

        # Table styling
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors.BG_CARD};
                color: {colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                outline: none;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 8px 10px;
                border: none;
                border-bottom: 1px solid {colors.BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {colors.BG_HOVER};
            }}
            QTableWidget::item:alternate {{
                background-color: {colors.BG_SECONDARY};
            }}
            QHeaderView::section {{
                background-color: {colors.BG_SECONDARY};
                color: {colors.TEXT_SECONDARY};
                padding: 10px 10px;
                border: none;
                border-bottom: 2px solid {colors.BORDER};
                font-weight: 600;
                font-size: 11px;
            }}
            QHeaderView::section:hover {{
                background-color: {colors.BG_HOVER};
            }}
            QScrollBar:vertical {{
                background-color: {colors.BG_SECONDARY};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:hover {{
                background-color: {colors.TEXT_MUTED};
            }}
        """)

        # Set font
        self._table.setFont(QFont("Segoe UI", 11))

        layout.addWidget(self._table)

        return frame

    def _apply_theme(self):
        """Apply theme styles"""
        colors = c()
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")

    def _start_update_timer(self):
        """Start periodic update timer"""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._collect_data)
        self._update_timer.start(2000)

        # Initial CPU baseline and data collection
        QTimer.singleShot(100, self._init_baseline_and_collect)

    def _init_baseline_and_collect(self):
        """Initialize CPU baseline and collect data"""
        try:
            psutil.cpu_percent(percpu=True, interval=0.1)
            for proc in psutil.process_iter(['cpu_percent']):
                try:
                    proc.cpu_percent()
                except:
                    pass
            self._cpu_baseline_done = True
            self._collect_data()
        except Exception as e:
            print(f"Baseline error: {e}")
            self._cpu_baseline_done = True

    def _force_refresh(self):
        """Force data refresh"""
        self._cpu_baseline_done = False
        self._init_baseline_and_collect()

    def _on_search_changed(self, text: str):
        """Handle search filter"""
        if not text:
            self._update_table(self._processes)
        else:
            filtered = [
                p for p in self._processes
                if text.lower() in p.get('name', '').lower()
                or str(p.get('pid', '')) == text
            ]
            self._update_table(filtered)

    def _collect_data(self):
        """Collect process and system data"""
        try:
            if not self._cpu_baseline_done:
                return

            # Collect processes
            self._processes = self._collect_processes()

            # Collect system data
            self._collect_system_data()

            # Update UI
            self._update_table(self._processes)
            self._update_summary_cards()

        except Exception as e:
            print(f"Data collection error: {e}")

    def _collect_processes(self) -> List[Dict[str, Any]]:
        """Collect all running processes"""
        processes = []

        for proc in psutil.process_iter([
            'pid', 'name', 'cpu_percent', 'memory_info',
            'status', 'username', 'num_threads', 'num_handles', 'ppid'
        ]):
            try:
                if not proc.is_running():
                    continue

                info = proc.info
                pid = info.get('pid', 0)
                name = info.get('name', 'Unknown')

                # CPU percent
                cpu = 0.0
                try:
                    cpu = proc.cpu_percent(interval=None)
                except:
                    pass

                # Memory
                mem_info = info.get('memory_info', None)
                mem_mb = mem_info.rss / (1024 * 1024) if mem_info else 0

                # User
                username = info.get('username', None)
                if username:
                    username = str(username).split('@')[0] if '@' in str(username) else str(username)
                else:
                    username = 'N/A'

                # Status
                status = info.get('status', 'running')
                status = str(status).lower()
                if status in ('running', 'sleeping', 'idle'):
                    status_display = "Running"
                elif status == 'stopped':
                    status_display = "Stopped"
                elif status == 'zombie':
                    status_display = "Zombie"
                elif 'not responding' in status:
                    status_display = "Not Responding"
                else:
                    status_display = "Running"

                # Threads
                threads = info.get('num_threads', 0)

                # Handles
                handles = info.get('num_handles', 0)

                # PPID
                ppid = info.get('ppid', 0)

                processes.append({
                    'pid': pid,
                    'name': name,
                    'cpu': cpu,
                    'memory_mb': mem_mb,
                    'user': username or 'N/A',
                    'threads': threads,
                    'handles': handles,
                    'status': status_display,
                    'status_raw': status,
                    'ppid': ppid,
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by CPU descending
        processes.sort(key=lambda x: x.get('cpu') or 0, reverse=True)
        return processes[:150]  # Limit for performance

    def _collect_system_data(self):
        """Collect system-wide stats"""
        try:
            # Memory
            mem = psutil.virtual_memory()
            self._system_data['mem_used_gb'] = mem.used / (1024**3)
            self._system_data['mem_total_gb'] = mem.total / (1024**3)
            self._system_data['mem_percent'] = mem.percent

            # Network
            net = psutil.net_io_counters()
            self._system_data['bytes_sent'] = net.bytes_sent
            self._system_data['bytes_recv'] = net.bytes_recv

            # CPU
            self._system_data['cpu_percent'] = psutil.cpu_percent(interval=0.1)

            # Disk
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self._system_data['disk_read_mb'] = disk_io.read_bytes / (1024**2)
                    self._system_data['disk_write_mb'] = disk_io.write_bytes / (1024**2)
            except:
                pass

        except Exception as e:
            print(f"System data error: {e}")

    def _update_table(self, processes: List[Dict[str, Any]]):
        """Update table with process data"""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(processes))

        colors = c()

        for row, proc in enumerate(processes):
            # Name
            name_item = QTableWidgetItem(proc.get('name', ''))
            name_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            self._table.setItem(row, 0, name_item)

            # PID
            pid_item = QTableWidgetItem(str(proc.get('pid', '')))
            pid_item.setForeground(QColor(colors.TEXT_MUTED))
            self._table.setItem(row, 1, pid_item)

            # CPU %
            cpu_val = proc.get('cpu', 0)
            cpu_item = QTableWidgetItem(f"{cpu_val:.1f}")
            if cpu_val > 50:
                cpu_item.setForeground(QColor(colors.ACCENT_RED))
            elif cpu_val > 25:
                cpu_item.setForeground(QColor(colors.ACCENT_ORANGE))
            else:
                cpu_item.setForeground(QColor(colors.ACCENT_GREEN))
            cpu_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self._table.setItem(row, 2, cpu_item)

            # Memory
            mem_item = QTableWidgetItem(f"{proc.get('memory_mb', 0):.1f}")
            mem_item.setForeground(QColor(colors.ACCENT_CYAN))
            self._table.setItem(row, 3, mem_item)

            # User
            user_item = QTableWidgetItem(proc.get('user', 'N/A'))
            user_item.setForeground(QColor(colors.TEXT_SECONDARY))
            self._table.setItem(row, 4, user_item)

            # Threads
            threads_item = QTableWidgetItem(str(proc.get('threads', 0)))
            threads_item.setForeground(QColor(colors.TEXT_MUTED))
            self._table.setItem(row, 5, threads_item)

            # Status
            status = proc.get('status', 'Running')
            status_item = QTableWidgetItem(status)
            status_color = STATUS_COLORS.get(proc.get('status_raw', 'running'), STATUS_COLORS['running'])
            status_item.setForeground(QColor(status_color))
            self._table.setItem(row, 6, status_item)

        self._table.setSortingEnabled(True)

    def _update_summary_cards(self):
        """Update summary cards with system data"""
        data = self._system_data

        # CPU
        cpu = data.get('cpu_percent', 0)
        self._cpu_card.set_value(f"{cpu:.1f}%")
        self._cpu_card.set_progress(cpu)

        # Memory
        mem_used = data.get('mem_used_gb', 0)
        mem_total = data.get('mem_total_gb', 0)
        mem_pct = data.get('mem_percent', 0)
        self._mem_card.set_value(f"{mem_used:.1f} / {mem_total:.1f} GB")
        self._mem_card.set_progress(mem_pct)

        # Disk
        disk_read = data.get('disk_read_mb', 0)
        disk_write = data.get('disk_write_mb', 0)
        delta_read = disk_read - self._last_disk_read
        delta_write = disk_write - self._last_disk_write
        self._last_disk_read = disk_read
        self._last_disk_write = disk_write
        if delta_read < 0:
            delta_read = 0
        if delta_write < 0:
            delta_write = 0
        self._disk_card.set_value(f"{delta_read:.0f} / {delta_write:.0f} MB/s")

        # Network
        bytes_sent = data.get('bytes_sent', 0)
        bytes_recv = data.get('bytes_recv', 0)
        delta_sent = bytes_sent - self._last_net_sent
        delta_recv = bytes_recv - self._last_net_recv
        self._last_net_sent = bytes_sent
        self._last_net_recv = bytes_recv
        if delta_sent < 0:
            delta_sent = 0
        if delta_recv < 0:
            delta_recv = 0
        sent_mbps = (delta_sent * 8) / (1024 * 1024)
        recv_mbps = (delta_recv * 8) / (1024 * 1024)
        self._net_card.set_value(f"{recv_mbps:.1f} / {sent_mbps:.1f} Mbps")

        # Process count
        self._proc_card.set_value(str(len(self._processes)))

    def on_scale_changed(self, factor: float):
        """Handle DPI scale changes"""
        self._apply_theme()
        self.update()

    def update_data(self, data: dict):
        """Handle data updates from MainWindow"""
        # Integrate with main data collector
        if 'memory' in data:
            mem = data['memory']
            self._system_data['mem_used_gb'] = mem.get('used', 0) / (1024**3)
            self._system_data['mem_total_gb'] = mem.get('total', 0) / (1024**3)
            self._system_data['mem_percent'] = mem.get('percent', 0)

        if 'cpu' in data:
            self._system_data['cpu_percent'] = data['cpu'].get('percent', 0)

        if 'network' in data:
            net = data['network']
            self._system_data['bytes_sent'] = net.get('bytes_sent', 0)
            self._system_data['bytes_recv'] = net.get('bytes_recv', 0)

        self._update_summary_cards()

    def showEvent(self, a0):
        """Called when view is shown"""
        super().showEvent(a0)
        if not self._cpu_baseline_done:
            self._init_baseline_and_collect()

    def __del__(self):
        """Cleanup"""
        if hasattr(self, '_update_timer') and self._update_timer is not None:
            try:
                self._update_timer.stop()
            except RuntimeError:
                pass  # Timer was already deleted by C++
