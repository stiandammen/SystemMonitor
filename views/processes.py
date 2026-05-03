"""
Processes View - Professional Process Monitoring
Enterprise-grade process management with real-time monitoring
"""
import time
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
    QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QProgressBar, QTabWidget, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QDialog, QPushButton,
    QTextEdit, QCheckBox, QGroupBox, QSpinBox, QTableView
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QSortFilterProxyModel,
    QModelIndex, QAbstractTableModel, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QAction, QIcon, QPalette, QCursor, QPainterPath
)
import qtawesome as qta

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from core.signals import signal_bus
from data.collector import DataCollector


def c():
    """Get current theme colors"""
    return theme_manager.colors


# Status constants
STATUS_RUNNING = "running"
STATUS_SUSPENDED = "suspended"
STATUS_NOT_RESPONDING = "not responding"
STATUS_CRITICAL = "critical"
STATUS_ERROR = "error"


STATUS_COLORS = {
    STATUS_RUNNING: "#10b981",       # Green
    STATUS_SUSPENDED: "#ffd740",     # Yellow
    STATUS_NOT_RESPONDING: "#f97316", # Orange
    STATUS_CRITICAL: "#f97316",      # Orange
    STATUS_ERROR: "#ef4444",        # Red
}


class ProcessWorker(QThread):
    """Background worker for collecting process data"""

    data_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._interval = 2.0  # seconds
        self._last_net_sent = 0
        self._last_net_recv = 0
        self._last_net_time = 0

    def run(self):
        """Collect process data in background"""
        self._running = True

        while self._running:
            try:
                processes = self._collect_processes()
                self.data_ready.emit(processes)
            except Exception as e:
                self.error.emit(str(e))

            time.sleep(self._interval)

    def stop(self):
        """Stop the worker"""
        self._running = False

    def _collect_processes(self) -> List[Dict[str, Any]]:
        """Collect all process information"""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info',
                                         'create_time', 'status', 'username', 'num_threads',
                                         'num_handles', 'nice', 'ppid']):
            try:
                if not proc.is_running():
                    continue

                info = proc.info
                pid = info.get('pid', 0)
                name = info.get('name', 'Unknown')
                cpu = info.get('cpu_percent', 0) or 0
                mem_info = info.get('memory_info', None)
                mem_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
                mem_vms = mem_info.vms / (1024 * 1024) if mem_info else 0

                username = info.get('username', None)
                if username:
                    if '@' in str(username):
                        username = str(username).split('@')[0]
                    else:
                        username = str(username)

                status = info.get('status', 'unknown')
                status_display = self._map_status(status)
                path = self._get_process_path(proc)

                try:
                    children = proc.children(recursive=False)
                    child_count = len(children)
                except:
                    child_count = 0

                try:
                    open_files = len(proc.open_files())
                except:
                    open_files = 0

                threads = info.get('num_threads', 0)
                handles = info.get('num_handles', 0)
                nice = info.get('nice', 0)
                priority = self._map_nice_to_priority(nice)

                create_time = info.get('create_time', 0)
                start_time = datetime.fromtimestamp(create_time) if create_time else None
                ppid = info.get('ppid', 0)
                arch = self._get_process_arch(proc)

                processes.append({
                    'pid': pid,
                    'name': name,
                    'cpu': cpu,
                    'memory_mb': mem_mb,
                    'memory_vms_mb': mem_vms,
                    'status': status_display,
                    'status_raw': status,
                    'user': username or 'N/A',
                    'path': path or 'N/A',
                    'threads': threads,
                    'handles': handles,
                    'priority': priority,
                    'nice': nice,
                    'start_time': start_time,
                    'ppid': ppid,
                    'child_count': child_count,
                    'open_files': open_files,
                    'arch': arch,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        processes.sort(key=lambda x: x.get('cpu') or 0, reverse=True)
        return processes[:200]

    def _map_status(self, status: str) -> str:
        """Map psutil status to display status"""
        status = str(status).lower()
        if status == 'running':
            return STATUS_RUNNING
        elif status in ('sleeping', 'idle'):
            return STATUS_RUNNING
        elif status == 'stopped':
            return STATUS_SUSPENDED
        elif status == 'zombie':
            return STATUS_ERROR
        elif 'not responding' in status or 'hung' in status:
            return STATUS_NOT_RESPONDING
        else:
            return STATUS_RUNNING

    def _map_nice_to_priority(self, nice: int) -> str:
        """Map nice value to priority name"""
        if nice < -7:
            return "Realtime"
        elif nice < -3:
            return "High"
        elif nice < 0:
            return "Above Normal"
        elif nice == 0:
            return "Normal"
        elif nice < 4:
            return "Below Normal"
        else:
            return "Low"

    def _get_process_path(self, proc) -> Optional[str]:
        """Get process executable path"""
        try:
            return proc.exe()
        except:
            return None

    def _get_process_arch(self, proc) -> str:
        """Get process architecture"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                PROCESSOR_ARCHITECTURE_x64 = 9
                PROCESSOR_ARCHITECTURE_x86 = 5

                kernel32 = ctypes.windll.kernel32
                IsWow64Process = kernel32.IsWow64Process
                IsWow64Process.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
                IsWow64Process.restype = ctypes.c_int

                wow64 = ctypes.c_int(0)
                if IsWow64Process(proc.pid, ctypes.byref(wow64)):
                    return "x64" if wow64.value == 0 else "x86"
            return "x64"
        except:
            return "x64"


class MiniSparkline(QWidget):
    """Mini sparkline graph widget for trend display"""

    def __init__(self, parent=None, max_points: int = 30, color: str = "#00ab84"):
        super().__init__(parent)
        self._history = []
        self._max_points = max_points
        self._color = QColor(color)
        self._fill_color = QColor(color + "33")  # 20% alpha
        self.setMinimumHeight(24)
        self.setMinimumWidth(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_value(self, value: float):
        """Add a new value to the sparkline"""
        self._history.append(value)
        if len(self._history) > self._max_points:
            self._history.pop(0)
        self.update()

    def clear(self):
        """Clear the sparkline data"""
        self._history = []
        self.update()

    def paintEvent(self, a0):
        """Paint the sparkline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._history or self.width() <= 0 or self.height() <= 0:
            painter.end()
            return

        w = self.width()
        h = self.height()
        pad = 2

        graph_w = w - pad * 2
        graph_h = h - pad * 2

        # Calculate points
        points = []
        step = graph_w / max(len(self._history) - 1, 1)
        max_val = max(max(self._history) if self._history else 1, 1)

        for i, val in enumerate(self._history):
            x = pad + step * i
            y = pad + graph_h - (val / max_val * graph_h)
            points.append(QPoint(int(x), int(y)))

        if len(points) < 2:
            painter.end()
            return

        # Draw fill
        fill_pts = [QPoint(points[0].x(), pad + graph_h)] + points + [QPoint(points[-1].x(), pad + graph_h)]

        gradient = QLinearGradient(0, pad, 0, pad + graph_h)
        gradient.setColorAt(0, self._fill_color.lighter(150))
        gradient.setColorAt(1, self._fill_color)

        path = QPainterPath()
        path.moveTo(fill_pts[0])
        for pt in fill_pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()

        painter.fillPath(path, gradient)

        # Draw line
        pen = QPen(self._color, 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawPolyline(points)

        painter.end()


class SummaryCard(QFrame):
    """Premium summary card with sparkline and progress"""

    def __init__(self, title: str, icon: str = "", accent: str = "#00ab84", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._title = title
        self._value = "0"
        self._subtitle = ""
        self._max_value = 100
        self._sparkline = None
        self._sparkline_history = []

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(8)

        # Icon
        self._icon_label = QLabel()
        try:
            qicon = qta.icon(icon, color=self._accent)
            self._icon_label.setPixmap(qicon.pixmap(16, 16))
        except Exception:
            self._icon_label.setText("")
        header.addWidget(self._icon_label)

        # Title
        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", 10))
        self._title_label.setStyleSheet("background: transparent;")
        header.addWidget(self._title_label)

        header.addStretch()

        # Sparkline
        self._sparkline = MiniSparkline(color=self._accent)
        self._sparkline.setFixedWidth(80)
        header.addWidget(self._sparkline)

        layout.addLayout(header)

        # Value
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._value_label.setStyleSheet("background: transparent;")
        layout.addWidget(self._value_label)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setMaximumHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        layout.addWidget(self._progress)

    def _apply_style(self):
        """Apply theme styles"""
        colors = c()
        self.setStyleSheet(f"""
            SummaryCard {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)

        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")

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

    def set_value(self, value: str, subtitle: str = ""):
        """Update the card value"""
        self._value = value
        self._subtitle = subtitle
        self._value_label.setText(value)

    def set_progress(self, percent: float):
        """Update progress bar"""
        self._progress.setValue(int(min(percent, 100)))

    def add_sparkline_value(self, value: float):
        """Add value to sparkline"""
        self._sparkline_history.append(value)
        if len(self._sparkline_history) > 30:
            self._sparkline_history.pop(0)
        self._sparkline.add_value(value)


class ProcessTableModel(QAbstractTableModel):
    """High-performance table model for processes"""

    COLUMNS = [
        {'key': 'status', 'title': 'Status', 'width': 60},
        {'key': 'name', 'title': 'Process Name', 'width': 200},
        {'key': 'pid', 'title': 'PID', 'width': 70},
        {'key': 'cpu', 'title': 'CPU %', 'width': 70},
        {'key': 'memory_mb', 'title': 'Memory', 'width': 90},
        {'key': 'user', 'title': 'User', 'width': 100},
        {'key': 'threads', 'title': 'Threads', 'width': 60},
        {'key': 'handles', 'title': 'Handles', 'width': 70},
        {'key': 'priority', 'title': 'Priority', 'width': 90},
        {'key': 'start_time', 'title': 'Start Time', 'width': 100},
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._filtered_data: List[Dict[str, Any]] = []
        self._sort_column = 3  # CPU %
        self._sort_order = Qt.SortOrder.DescendingOrder
        self._filter_text = ""

    def rowCount(self, parent=None):
        return len(self._filtered_data)

    def columnCount(self, parent=None):
        return len(self.COLUMNS)

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._filtered_data):
            return None

        process = self._filtered_data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            key = self.COLUMNS[col]['key']
            value = process.get(key, '')

            if key == 'cpu':
                return f"{value:.1f}%"
            elif key == 'memory_mb':
                return f"{value:.1f} MB"
            elif key == 'start_time' and value:
                return value.strftime("%H:%M:%S")
            elif key == 'status':
                return ""
            return str(value) if value is not None else ""
        elif role == Qt.ItemDataRole.BackgroundRole:
            status = process.get('status', STATUS_RUNNING)
            color = QColor(STATUS_COLORS.get(status, STATUS_COLORS[STATUS_RUNNING]))
            return color.lighter(190)
        elif role == Qt.ItemDataRole.ForegroundRole:
            return QPalette().color(QPalette.ColorRole.Text)
        elif role == Qt.ItemDataRole.UserRole:
            return process

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]['title']
        elif role == Qt.ItemDataRole.SizeHintRole:
            return QSize(self.COLUMNS[section]['width'], 32)
        return None

    def setProcessData(self, data: List[Dict[str, Any]]):
        """Update the model data"""
        self._data = data
        self._apply_filter_and_sort()

    def setFilterFixedString(self, filter_text: str):
        """Set filter text"""
        self._filter_text = filter_text.lower()
        self._apply_filter_and_sort()

    def _apply_filter_and_sort(self):
        """Apply filter and sort to data"""
        # Filter data
        if self._filter_text:
            self._filtered_data = [
                p for p in self._data
                if self._matches_filter(p)
            ]
        else:
            self._filtered_data = self._data.copy()

        # Sort data
        col = self.COLUMNS[self._sort_column]['key']
        reverse = self._sort_order == Qt.SortOrder.DescendingOrder

        def get_sort_key(p):
            val = p.get(col, 0)
            if val is None:
                val = 0
            if isinstance(val, str):
                return val.lower()
            return val

        self._filtered_data.sort(key=get_sort_key, reverse=reverse)
        self.modelReset.emit()

    def _matches_filter(self, process: Dict[str, Any]) -> bool:
        """Check if process matches filter"""
        if not self._filter_text:
            return True

        text = self._filter_text

        # Check if it's a special filter
        if text.startswith('high cpu'):
            try:
                threshold = float(text.split()[-1].replace('%', '')) if len(text.split()) > 1 else 50
                return process.get('cpu', 0) > threshold
            except:
                pass
        elif text.startswith('memory >'):
            try:
                threshold = float(text.split()[-1].replace('mb', '').strip())
                return process.get('memory_mb', 0) > threshold
            except:
                pass
        elif text.startswith('memory <'):
            try:
                threshold = float(text.split()[-1].replace('mb', '').strip())
                return process.get('memory_mb', 0) < threshold
            except:
                pass

        # Check process name, PID, user
        name = process.get('name', '').lower()
        pid = str(process.get('pid', ''))
        user = process.get('user', '').lower()

        return (text in name or text in pid or text in user)

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """Sort the model"""
        self._sort_column = column
        self._sort_order = order
        self._apply_filter_and_sort()

    def get_process_at_row(self, row: int) -> Optional[Dict[str, Any]]:
        """Get process data at row"""
        if 0 <= row < len(self._filtered_data):
            return self._filtered_data[row]
        return None


class ProcessTableView(QTableView):
    """Custom table view for processes"""

    process_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup table view"""
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Style
        colors = c()
        self.setStyleSheet(f"""
            QTableView {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 8px;
                outline: none;
            }}
            QTableView::item {{
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid {colors.BORDER};
            }}
            QTableView::item:selected {{
                background-color: {colors.BG_HOVER};
            }}
            QHeaderView {{
                background-color: {colors.BG_SECONDARY};
            }}
            QHeaderView::section {{
                background-color: {colors.BG_SECONDARY};
                color: {colors.TEXT_SECONDARY};
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid {colors.BORDER};
                font-weight: 600;
            }}
            QHeaderView::section:hover {{
                background-color: {colors.BG_HOVER};
            }}
            QScrollBar:vertical {{
                background-color: {colors.BG_SECONDARY};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.BORDER};
                border-radius: 5px;
                min-height: 20px;
            }}
        """)

    def selectionChanged(self, selected, deselected):
        """Handle selection change"""
        super().selectionChanged(selected, deselected)
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            model = self.model()
            if model:
                proc = model.get_process_at_row(row)
                if proc:
                    self.process_selected.emit(proc)


class DetailsPanel(QFrame):
    """Right-side details panel for selected process"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Setup UI"""
        colors = c()

        self.setFixedWidth(340)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.BG_SECONDARY};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {colors.BG_SECONDARY};
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        content.setLayout(content_layout)

        # Header
        header = QLabel("Process Details")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("background: transparent;")
        content_layout.addWidget(header)

        # Placeholder
        self._placeholder = QLabel("Select a process to view details")
        self._placeholder.setFont(QFont("Segoe UI", 10))
        self._placeholder.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self._placeholder)

        # Details container (hidden initially)
        self._details_container = QWidget()
        self._details_container.setVisible(False)
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(16)
        self._details_container.setLayout(details_layout)

        # Process Name Header
        self._process_name_label = QLabel("Process Name")
        self._process_name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        details_layout.addWidget(self._process_name_label)

        self._process_path_label = QLabel("")
        self._process_path_label.setFont(QFont("Segoe UI", 9))
        self._process_path_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._process_path_label.setWordWrap(True)
        details_layout.addWidget(self._process_path_label)

        # Status badge
        self._status_badge = QLabel()
        self._status_badge.setFixedHeight(24)
        self._status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        details_layout.addWidget(self._status_badge)

        # General Info Section
        general_section, self._general_info_layout = self._create_info_section("General Information")
        details_layout.addWidget(general_section)

        # Resource Usage Section
        resource_section = self._create_resource_section()
        details_layout.addWidget(resource_section)

        # Action Buttons Section
        actions_section = self._create_actions_section()
        details_layout.addWidget(actions_section)

        content_layout.addWidget(self._details_container)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_info_section(self, title: str) -> tuple:
        """Create general info section with content widget"""
        colors = c()
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)
        frame.setLayout(main_layout)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        main_layout.addWidget(title_label)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 4, 0, 0)
        content_layout.setSpacing(6)
        content.setLayout(content_layout)
        main_layout.addWidget(content)

        return frame, content_layout

    def _create_resource_section(self) -> QFrame:
        """Create resource usage section"""
        colors = c()
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)
        frame.setLayout(main_layout)

        title_label = QLabel("Resource Usage")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        main_layout.addWidget(title_label)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 4, 0, 0)
        content_layout.setSpacing(10)
        content.setLayout(content_layout)
        main_layout.addWidget(content)

        # CPU bar
        cpu_row = self._create_progress_row("CPU", colors.ACCENT_BLUE)
        self._cpu_bar = cpu_row['bar']
        self._cpu_value = cpu_row['value']
        content_layout.addWidget(cpu_row['widget'])

        # Memory bar
        mem_row = self._create_progress_row("Memory", colors.ACCENT_PURPLE)
        self._mem_bar = mem_row['bar']
        self._mem_value = mem_row['value']
        content_layout.addWidget(mem_row['widget'])

        # Threads count
        threads_widget = QWidget()
        threads_layout = QHBoxLayout()
        threads_layout.setContentsMargins(0, 0, 0, 0)
        threads_layout.setSpacing(8)
        threads_widget.setLayout(threads_layout)
        self._threads_label = QLabel("Threads")
        self._threads_label.setFont(QFont("Segoe UI", 10))
        self._threads_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._threads_value = QLabel("0")
        self._threads_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        threads_layout.addWidget(self._threads_label)
        threads_layout.addStretch()
        threads_layout.addWidget(self._threads_value)
        content_layout.addWidget(threads_widget)

        # Handles count
        handles_widget = QWidget()
        handles_layout = QHBoxLayout()
        handles_layout.setContentsMargins(0, 0, 0, 0)
        handles_layout.setSpacing(8)
        handles_widget.setLayout(handles_layout)
        self._handles_label = QLabel("Handles")
        self._handles_label.setFont(QFont("Segoe UI", 10))
        self._handles_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._handles_value = QLabel("0")
        self._handles_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        handles_layout.addWidget(self._handles_label)
        handles_layout.addStretch()
        handles_layout.addWidget(self._handles_value)
        content_layout.addWidget(handles_widget)

        return frame

    def _create_progress_row(self, label: str, color: str) -> dict:
        """Create a label + progress bar row"""
        colors = c()
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        widget.setLayout(layout)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 10))
        label_widget.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")

        value_widget = QLabel("0%")
        value_widget.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        value_widget.setStyleSheet(f"color: {color}; background: transparent;")

        header_layout.addWidget(label_widget)
        header_layout.addStretch()
        header_layout.addWidget(value_widget)
        layout.addLayout(header_layout)

        bar = QProgressBar()
        bar.setMaximumHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(bar)

        return {'widget': widget, 'bar': bar, 'value': value_widget, 'label': label_widget}

    def _create_actions_section(self) -> QFrame:
        """Create action buttons section"""
        colors = c()
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)
        frame.setLayout(main_layout)

        title_label = QLabel("Actions")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        main_layout.addWidget(title_label)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 4, 0, 0)
        content_layout.setSpacing(8)
        content.setLayout(content_layout)
        main_layout.addWidget(content)

        # Safe actions row 1
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._btn_open_location = self._create_action_button("Open Location", "fa5s.folder-open", colors.ACCENT_BLUE)
        self._btn_copy_pid = self._create_action_button("Copy PID", "fa5s.copy", colors.TEXT_SECONDARY)
        self._btn_refresh = self._create_action_button("Refresh", "fa5s.sync", colors.ACCENT_GREEN)

        row1.addWidget(self._btn_open_location)
        row1.addWidget(self._btn_copy_pid)
        row1.addWidget(self._btn_refresh)
        content_layout.addLayout(row1)

        # Danger zone
        danger_label = QLabel("Danger Zone")
        danger_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        danger_label.setStyleSheet(f"color: {colors.ACCENT_RED}; background: transparent;")
        content_layout.addWidget(danger_label)

        self._btn_terminate = self._create_action_button("End Process", "fa5s.times-circle", colors.ACCENT_RED)
        self._btn_terminate.clicked.connect(self._on_terminate_clicked)
        content_layout.addWidget(self._btn_terminate)

        self._btn_kill_tree = self._create_action_button("Kill Process Tree", "fa5s.tree", colors.ACCENT_RED)
        content_layout.addWidget(self._btn_kill_tree)

        return frame

    def _create_action_button(self, text: str, icon: str, color: str) -> QPushButton:
        """Create a styled action button"""
        btn = QPushButton()
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setText(f"  {text}")

        try:
            qicon = qta.icon(icon, color=color)
            btn.setIcon(qicon)
            btn.setIconSize(QSize(14, 14))
        except:
            pass

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c().BG_SECONDARY};
                color: {color};
                border: none;
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {c().BG_HOVER};
            }}
        """)

        return btn

    def _apply_style(self):
        """Apply theme styles"""
        colors = c()
        self.setStyleSheet(f"""
            DetailsPanel {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-left: 1px solid {colors.BORDER};
            }}
        """)

    def set_process(self, process: Optional[Dict[str, Any]]):
        """Set the process to display"""
        self._process = process

        if process is None:
            self._placeholder.setVisible(True)
            self._details_container.setVisible(False)
            return

        self._placeholder.setVisible(False)
        self._details_container.setVisible(True)

        self._update_details()

    def _update_details(self):
        """Update details display"""
        if self._process is None:
            return

        proc = self._process
        colors = c()

        # Process name
        self._process_name_label.setText(proc.get('name', 'Unknown'))
        self._process_name_label.setStyleSheet("background: transparent;")

        # Path
        path = proc.get('path', 'N/A')
        self._process_path_label.setText(path)

        # Status badge
        status = proc.get('status', STATUS_RUNNING)
        status_color = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_RUNNING])
        self._status_badge.setText(f"  {status.upper()}  ")
        self._status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color}33;
                color: {status_color};
                border: 1px solid {status_color};
                border-radius: 12px;
                font-weight: bold;
            }}
        """)

        # Clear general info
        while self._general_info_layout.count():
            item = self._general_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add general info rows
        self._add_info_row("PID", str(proc.get('pid', 'N/A')))
        self._add_info_row("User", proc.get('user', 'N/A'))
        self._add_info_row("Priority", proc.get('priority', 'Normal'))
        self._add_info_row("Architecture", proc.get('arch', 'x64'))

        start_time = proc.get('start_time')
        if start_time:
            time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            self._add_info_row("Started", time_str)
        else:
            self._add_info_row("Started", "N/A")

        self._add_info_row("Parent PID", str(proc.get('ppid', 'N/A')))
        self._add_info_row("Threads", str(proc.get('threads', 0)))
        self._add_info_row("Handles", str(proc.get('handles', 0)))

        # Update resource usage
        cpu = proc.get('cpu', 0)
        self._cpu_bar.setValue(int(min(cpu, 100)))
        self._cpu_value.setText(f"{cpu:.1f}%")

        mem_mb = proc.get('memory_mb', 0)
        try:
            sys_mem = psutil.virtual_memory()
            mem_percent = (mem_mb * 1024 * 1024) / sys_mem.total * 100 if sys_mem.total > 0 else 0
        except:
            mem_percent = 0
        self._mem_bar.setValue(int(min(mem_percent, 100)))
        self._mem_value.setText(f"{mem_mb:.1f} MB")

        self._threads_value.setText(str(proc.get('threads', 0)))
        self._handles_value.setText(str(proc.get('handles', 0)))

    def _add_info_row(self, label: str, value: str):
        """Add an info row to the general info layout"""
        colors = c()
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)
        row.setLayout(layout)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(lbl)

        layout.addStretch()

        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        val.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(val)

        self._general_info_layout.addWidget(row)

    def _on_terminate_clicked(self):
        """Handle terminate process button click"""
        if self._process:
            pid = self._process.get('pid')
            name = self._process.get('name', 'Unknown')
            dialog = ConfirmationDialog(
                "Terminate Process",
                f"Are you sure you want to terminate '{name}' (PID: {pid})?\n\nThis action cannot be undone.",
                self
            )
            if dialog.exec():
                try:
                    psutil.Process(pid).terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass


class ConfirmationDialog(QDialog):
    """Confirmation dialog for dangerous actions"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self._setup_ui(title, message)

    def _setup_ui(self, title: str, message: str):
        """Setup dialog UI"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        colors = c()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors.BG_PRIMARY};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        self.setLayout(layout)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(msg_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.ACCENT_RED};
                color: white;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)


class ProcessesView(QWidget, ScaleMixin):
    """Professional Process Monitor View"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes = []
        self._selected_process = None
        self._worker = None
        self._last_update = 0
        self._update_interval = 2000  # ms
        self._is_visible = False

        self.scale_connect()
        self._setup_ui()
        self._apply_theme()
        self._start_worker()
        self._start_update_timer()

    def _setup_ui(self):
        """Setup the main UI"""
        colors = c()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Left content area
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        content_widget.setLayout(content_layout)

        # Top navigation tabs
        tabs = self._create_tabs()
        content_layout.addWidget(tabs)

        # Summary cards
        summary = self._create_summary_cards()
        content_layout.addWidget(summary)

        # Search bar
        search = self._create_search_bar()
        content_layout.addWidget(search)

        # Process table
        table = self._create_process_table()
        content_layout.addWidget(table, stretch=1)

        main_layout.addWidget(content_widget, stretch=1)

        # Right details panel
        self._details_panel = DetailsPanel()
        main_layout.addWidget(self._details_panel)

    def _create_tabs(self) -> QFrame:
        """Create top navigation tabs"""
        colors = c()

        tabs_frame = QFrame()
        tabs_frame.setFixedHeight(44)
        tabs_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        tabs_frame.setLayout(layout)

        self._nav_tabs = []
        tabs_data = [
            ("Processes", "ph.list", True),
            ("Performance", "mdi.gauge", False),
            ("Resources", "fa5s.chart-pie", False),
            ("Services", "fa5s.cogs", False),
            ("Startup Apps", "fa5s.rocket", False),
            ("Users", "fa5s.users", False),
        ]

        for label, icon, active in tabs_data:
            btn = QPushButton()
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            try:
                icon_color = colors.ACCENT_GREEN if active else colors.TEXT_MUTED
                qicon = qta.icon(icon, color=icon_color)
                btn.setIcon(qicon)
                btn.setIconSize(QSize(16, 16))
            except:
                pass

            btn.setText(f"  {label}")
            btn.setFont(QFont("Segoe UI", 11))

            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors.BG_HOVER};
                        color: {colors.ACCENT_GREEN};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 14px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.TEXT_SECONDARY};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 14px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.BG_HOVER};
                        color: {colors.TEXT_PRIMARY};
                    }}
                """)

            self._nav_tabs.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        return tabs_frame

    def _create_summary_cards(self) -> QFrame:
        """Create summary cards row"""
        colors = c()

        cards_frame = QFrame()
        cards_frame.setFixedHeight(90)
        cards_frame.setStyleSheet("background: transparent;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        cards_frame.setLayout(layout)

        # CPU Card
        self._cpu_card = SummaryCard("CPU", "ph.cpu", colors.ACCENT_BLUE)
        self._cpu_card.set_value("0%")
        layout.addWidget(self._cpu_card, stretch=1)

        # Memory Card
        self._mem_card = SummaryCard("Memory", "mdi.memory", colors.ACCENT_PURPLE)
        self._mem_card.set_value("0 / 0 GB")
        layout.addWidget(self._mem_card, stretch=1)

        # Disk Card
        self._disk_card = SummaryCard("Disk", "fa5s.database", colors.ACCENT_ORANGE)
        self._disk_card.set_value("0 MB/s")
        layout.addWidget(self._disk_card, stretch=1)

        # Network Card
        self._net_card = SummaryCard("Network", "ph.wifi-high", colors.ACCENT_CYAN)
        self._net_card.set_value("0 / 0 Mbps")
        layout.addWidget(self._net_card, stretch=1)

        return cards_frame

    def _create_search_bar(self) -> QFrame:
        """Create search bar"""
        colors = c()

        search_frame = QFrame()
        search_frame.setFixedHeight(48)
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)
        search_frame.setLayout(layout)

        # Search icon
        search_icon = QLabel()
        try:
            icon = qta.icon("fa5s.search", color=colors.TEXT_MUTED)
            search_icon.setPixmap(icon.pixmap(16, 16))
        except:
            pass
        layout.addWidget(search_icon)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search processes (Ctrl+K) - supports: name, PID, user, high cpu, memory > 500MB")
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

        # Filter button
        filter_btn = QPushButton()
        try:
            icon = qta.icon("fa5s.filter", color=colors.TEXT_MUTED)
            filter_btn.setIcon(icon)
        except:
            filter_btn.setText("Filter")
        filter_btn.setFixedSize(36, 36)
        filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
            }}
        """)
        layout.addWidget(filter_btn)

        # Refresh button
        refresh_btn = QPushButton()
        try:
            icon = qta.icon("fa5s.sync", color=colors.TEXT_MUTED)
            refresh_btn.setIcon(icon)
        except:
            refresh_btn.setText("Refresh")
        refresh_btn.setFixedSize(36, 36)
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

        return search_frame

    def _create_process_table(self) -> QFrame:
        """Create the process table"""
        colors = c()

        table_frame = QFrame()
        table_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        table_frame.setLayout(layout)

        # Table
        self._table_model = ProcessTableModel()
        self._table_view = ProcessTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.process_selected.connect(self._on_process_selected)

        # Column widths
        for i, col in enumerate(ProcessTableModel.COLUMNS):
            width = col.get('width', 100)
            self._table_view.setColumnWidth(i, width)

        # Header
        header = self._table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self._table_view)

        return table_frame

    def _apply_theme(self):
        """Apply theme styles"""
        colors = c()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.BG_PRIMARY};
            }}
        """)

    def _start_worker(self):
        """Start the background worker"""
        self._worker = ProcessWorker()
        self._worker.data_ready.connect(self._on_processes_updated)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _start_update_timer(self):
        """Start the display update timer"""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(500)  # 500ms for smooth UI

    def _force_refresh(self):
        """Force an immediate refresh"""
        if self._worker:
            self._worker.stop()
            self._worker.wait(1000)
            self._worker.start()

    def _on_processes_updated(self, processes: List[Dict[str, Any]]):
        """Handle processes data update"""
        self._processes = processes
        self._last_update = time.time()

        # Update table model
        self._table_model.setProcessData(processes)

        # Update summary cards
        self._update_summary_cards()

    def _on_worker_error(self, error: str):
        """Handle worker error"""
        print(f"Process worker error: {error}")

    def _on_process_selected(self, process: Dict[str, Any]):
        """Handle process selection"""
        self._selected_process = process
        self._details_panel.set_process(process)

    def _on_search_changed(self, text: str):
        """Handle search text change"""
        self._table_model.setFilterFixedString(text)

    def _update_display(self):
        """Update display with latest data"""
        # Update is handled by model signals
        pass

    def _update_summary_cards(self):
        """Update summary cards with aggregate data"""
        if not self._processes:
            return

        colors = c()

        # Calculate aggregates
        total_cpu = sum(p.get('cpu', 0) for p in self._processes)
        total_mem = sum(p.get('memory_mb', 0) for p in self._processes)
        total_threads = sum(p.get('threads', 0) for p in self._processes)

        # Update CPU card
        avg_cpu = total_cpu / len(self._processes) if self._processes else 0
        self._cpu_card.set_value(f"{avg_cpu:.1f}%")
        self._cpu_card.set_progress(avg_cpu)
        self._cpu_card.add_sparkline_value(avg_cpu)

        # Update Memory card
        try:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            self._mem_card.set_value(f"{used_gb:.1f} / {total_gb:.1f} GB")
            self._mem_card.set_progress(mem.percent)
            self._mem_card.add_sparkline_value(mem.percent)
        except:
            pass

        # Update Disk card (activity)
        disk_activity = 0
        for p in self._processes[:10]:  # Top processes
            disk_activity += p.get('disk_mbps', 0)
        self._disk_card.set_value(f"{disk_activity:.1f} MB/s")
        self._disk_card.add_sparkline_value(disk_activity)

        # Update Network card
        try:
            net = psutil.net_io_counters()
            sent_mbps = (net.bytes_sent - getattr(self, '_last_sent', net.bytes_sent)) / (1024 * 1024)
            recv_mbps = (net.bytes_recv - getattr(self, '_last_recv', net.bytes_recv)) / (1024 * 1024)
            self._last_sent = net.bytes_sent
            self._last_recv = net.bytes_recv
            self._net_card.set_value(f"{recv_mbps:.1f} / {sent_mbps:.1f} Mbps")
            self._net_card.add_sparkline_value(recv_mbps + sent_mbps)
        except:
            pass

    def enterEvent(self, event):
        """Called when view enters"""
        super().enterEvent(event)
        self._is_visible = True

    def leaveEvent(self, a0):
        """Called when view leaves"""
        super().leaveEvent(a0)
        self._is_visible = False

    def showEvent(self, a0):
        """Called when view is shown"""
        super().showEvent(a0)
        self._is_visible = True

    def hideEvent(self, a0):
        """Called when view is hidden"""
        super().hideEvent(a0)
        self._is_visible = False

    def on_scale_changed(self, factor: float):
        """Handle scale changes"""
        self._apply_theme()
        self.update()

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self._apply_theme()
        self._table_view._setup_ui()

    def __del__(self):
        """Cleanup"""
        if self._worker:
            self._worker.stop()
            self._worker.wait(2000)
