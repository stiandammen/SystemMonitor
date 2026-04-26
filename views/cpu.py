"""
CPU View - CPU monitoring dashboard with per-core graphs
Modern design matching GPU View
"""
import platform
import time
import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient
from PyQt5.QtWidgets import QSizePolicy

from styles.theme import theme_manager


# Use theme colors directly
def c():
    return theme_manager.colors


class CpuGraphWidget(QWidget):
    """Individual CPU core graph that adapts to container size - optimized with throttled repaints"""

    def __init__(self, core_index: int = 0, parent=None):
        super().__init__(parent)
        self._core_index = core_index
        self._history = []
        self._max_points = 50
        self._display_value = 0.0
        self._pending_update = False

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(100, 80)

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def set_value(self, value: float):
        """Set current CPU value with smooth animation"""
        self._display_value += (value - self._display_value) * 0.3

        if not self._history or len(self._history) > 0:
            self._history.append(value)
            if len(self._history) > self._max_points:
                self._history.pop(0)

        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)  # ~30fps throttle

    def paintEvent(self, event):
        """Paint the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        colors = c()
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            painter.end()
            return

        # Padding
        pad = 8
        graph_w = w - pad * 2
        graph_h = h - pad * 2 - 20  # Extra space for label

        # Background
        painter.setBrush(QColor(colors.BG_CARD))
        painter.setPen(QPen(QColor(colors.BORDER), 1))
        painter.drawRoundedRect(0, 0, int(w), int(h), 8, 8)

        if not self._history:
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignCenter, "Loading...")
            painter.end()
            return

        # Calculate points
        points = []
        step = graph_w / max(len(self._history) - 1, 1)
        for i, val in enumerate(self._history):
            x = pad + step * i
            y = pad + graph_h - (val / 100.0 * graph_h)
            points.append((x, y))

        # Color based on current value
        current = self._history[-1] if self._history else 0
        if current > 80:
            line_color = QColor(colors.ACCENT_RED)
        elif current > 60:
            line_color = QColor(colors.ACCENT_ORANGE)
        elif current > 40:
            line_color = QColor(colors.ACCENT_YELLOW)
        else:
            line_color = QColor(colors.ACCENT_BLUE)

        # Draw fill gradient
        if len(points) > 1:
            fill_pts = [(points[0][0], pad + graph_h)] + points + [(points[-1][0], pad + graph_h)]

            gradient = QLinearGradient(0, pad, 0, pad + graph_h)
            gradient.setColorAt(0, line_color.lighter(150))
            gradient.setColorAt(1, QColor(colors.BG_CARD))

            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)

            from PyQt5.QtCore import QPoint
            qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
            if len(qpoints) >= 3:
                painter.drawPolygon(*qpoints)

            # Draw line
            painter.setPen(QPen(line_color, 1.5, Qt.SolidLine))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))

        # Core label
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(colors.TEXT_SECONDARY))
        painter.drawText(pad + 4, pad + 12, f"Core {self._core_index}")

        # Value label
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(w - pad - 35, pad + 12, f"{current:.0f}%")

        painter.end()


class StatTile(QFrame):
    """Compact stat tile for info display"""
    def __init__(self, label: str = "", value: str = "--", color: str = None, parent=None):
        super().__init__(parent)
        colors = c()
        self._color = color or colors.ACCENT_BLUE

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._value_lbl.setStyleSheet(f"color: {self._color};")
        layout.addWidget(self._value_lbl)

        self._label_lbl = QLabel(label)
        self._label_lbl.setFont(QFont("Segoe UI", 9))
        self._label_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED};")
        layout.addWidget(self._label_lbl)

    def set_value(self, value: str):
        self._value_lbl.setText(value)

    def set_color(self, color: str):
        self._color = color
        self._value_lbl.setStyleSheet(f"color: {color};")


class CPUView(QWidget):
    """CPU monitoring dashboard with modern responsive design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._core_graphs = []
        self._cpu_info = {}
        self._boot_time = None
        self._logical_count = 1
        self._data_collector = None
        self._setup_ui()
        self._load_cpu_info()

    def set_data_collector(self, collector):
        """Set data collector and connect signals"""
        self._data_collector = collector
        if collector:
            collector.data_ready.connect(self._on_data_ready)
        self._start_update_timer()

    def _setup_ui(self):
        """Setup CPU view UI"""
        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Header bar
        header = self._create_header()
        main_layout.addWidget(header)

        # Stats row
        stats_row = self._create_stats_row()
        main_layout.addWidget(stats_row)

        # Core graphs section
        graphs_section = self._create_graphs_section()
        main_layout.addWidget(graphs_section, stretch=1)

        # Info panel
        info_panel = self._create_info_panel()
        main_layout.addWidget(info_panel)

        main_layout.addStretch()

    def _create_header(self):
        """Header with title and CPU info"""
        colors = c()

        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)
        header.setLayout(layout)

        # Title
        title = QLabel("CPU Monitor")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        # CPU name
        self._cpu_name_label = QLabel("—")
        self._cpu_name_label.setFont(QFont("Segoe UI", 11))
        self._cpu_name_label.setStyleSheet(f"color: {colors.ACCENT_BLUE};")
        layout.addWidget(self._cpu_name_label)

        layout.addStretch()

        # Overall usage indicator
        self._usage_indicator = QLabel("0%")
        self._usage_indicator.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self._usage_indicator.setStyleSheet(f"color: {colors.ACCENT_BLUE};")
        layout.addWidget(self._usage_indicator)

        return header

    def _create_stats_row(self):
        """Stats row with key metrics"""
        colors = c()

        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        container.setLayout(layout)

        self._stat_cores = StatTile("Physical Cores", "—", colors.ACCENT_GREEN)
        self._stat_threads = StatTile("Threads", "—", colors.ACCENT_CYAN)
        self._stat_freq = StatTile("Frequency", "—", colors.ACCENT_PURPLE)
        self._stat_uptime = StatTile("Uptime", "—", colors.TEXT_SECONDARY)

        for stat in [self._stat_cores, self._stat_threads, self._stat_freq, self._stat_uptime]:
            layout.addWidget(stat, stretch=1)

        return container

    def _create_info_panel(self):
        """Detailed CPU info panel with 3-column layout"""
        colors = c()

        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setSpacing(24)
        panel.setLayout(layout)

        # Left column - Basic info
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        left_title = QLabel("Basic Information")
        left_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        left_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY};")
        left_col.addWidget(left_title)

        self._info_name = self._create_info_row("CPU Name", "—", colors.ACCENT_BLUE)
        self._info_arch = self._create_info_row("Architecture", "x64", colors.ACCENT_GREEN)
        self._info_uptime = self._create_info_row("System Uptime", "—", colors.TEXT_SECONDARY)

        for row in [self._info_name, self._info_arch, self._info_uptime]:
            left_col.addWidget(row)
        left_col.addStretch()

        layout.addLayout(left_col, stretch=1)

        # Separator
        sep1 = QFrame()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet(f"background-color: {colors.BORDER};")
        layout.addWidget(sep1)

        # Center column - Specifications
        center_col = QVBoxLayout()
        center_col.setSpacing(12)

        center_title = QLabel("Specifications")
        center_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        center_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY};")
        center_col.addWidget(center_title)

        self._info_cores = self._create_info_row("Physical Cores", "—", colors.ACCENT_CYAN)
        self._info_threads = self._create_info_row("Logical Processors", "—", colors.ACCENT_PURPLE)
        self._info_freq = self._create_info_row("Base Frequency", "—", colors.ACCENT_ORANGE)
        self._info_cache = self._create_info_row("Cache", "L1/L2/L3", colors.TEXT_SECONDARY)

        for row in [self._info_cores, self._info_threads, self._info_freq, self._info_cache]:
            center_col.addWidget(row)
        center_col.addStretch()

        layout.addLayout(center_col, stretch=1)

        # Separator
        sep2 = QFrame()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet(f"background-color: {colors.BORDER};")
        layout.addWidget(sep2)

        # Right column - Usage stats
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        right_title = QLabel("Usage Statistics")
        right_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        right_title.setStyleSheet(f"color: {colors.TEXT_SECONDARY};")
        right_col.addWidget(right_title)

        self._info_usage = self._create_info_row("Current Usage", "0%", colors.ACCENT_BLUE)
        self._info_procs = self._create_info_row("Processes", "0", colors.TEXT_SECONDARY)
        self._info_threads_count = self._create_info_row("Total Threads", "0", colors.TEXT_SECONDARY)
        self._info_interrupts = self._create_info_row("Interrupts/sec", "0", colors.TEXT_SECONDARY)

        for row in [self._info_usage, self._info_procs, self._info_threads_count, self._info_interrupts]:
            right_col.addWidget(row)
        right_col.addStretch()

        layout.addLayout(right_col, stretch=1)

        return panel

    def _create_info_row(self, label: str, value: str, color: str = None):
        """Create a label-value info row"""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {c().BG_SECONDARY};
                border-radius: 6px;
                padding: 8px 12px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        row.setLayout(layout)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet(f"color: {c().TEXT_MUTED};")
        layout.addWidget(lbl)

        layout.addStretch()

        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 10, QFont.Bold))
        val.setStyleSheet(f"color: {color or c().TEXT_PRIMARY};")
        layout.addWidget(val)

        return row

    def _create_graphs_section(self):
        """Core graphs in responsive grid"""
        colors = c()

        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        section.setLayout(layout)

        # Title
        title = QLabel("Per-Core Usage")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_SECONDARY};")
        layout.addWidget(title)

        # Grid container
        grid_container = QWidget()
        self._graphs_grid = QGridLayout()
        self._graphs_grid.setSpacing(8)
        self._graphs_grid.setContentsMargins(0, 0, 0, 0)
        grid_container.setLayout(self._graphs_grid)

        layout.addWidget(grid_container, stretch=1)

        # Initialize graphs
        self._init_core_graphs()

        return section

    def _init_core_graphs(self):
        """Initialize graph widgets based on CPU count"""
        # Clear existing
        while self._graphs_grid.count():
            item = self._graphs_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._core_graphs.clear()

        try:
            self._logical_count = psutil.cpu_count(logical=True) or 1
        except Exception:
            self._logical_count = 1

        # Calculate columns based on available space
        # Each graph should be roughly 120-150px wide minimum
        cols = max(4, min(self._logical_count, 6))  # Between 4 and 6 columns
        rows = (self._logical_count + cols - 1) // cols

        for i in range(self._logical_count):
            row = i // cols
            col = i % cols

            graph = CpuGraphWidget(core_index=i)
            self._core_graphs.append(graph)
            self._graphs_grid.addWidget(graph, row, col)

    def _load_cpu_info(self):
        """Load static CPU info"""
        try:
            # Try WMI first for proper CPU name (most reliable on Windows)
            cpu_name = self._get_cpu_name_fallback()

            self._cpu_info['name'] = cpu_name
            self._cpu_info['architecture'] = platform.machine()

            try:
                self._boot_time = psutil.boot_time()
            except Exception:
                self._boot_time = None

            self._cpu_name_label.setText(cpu_name[:40] if len(cpu_name) > 40 else cpu_name)

            physical_cores = psutil.cpu_count(logical=False) or 1
            self._stat_cores.set_value(str(physical_cores))
            self._stat_threads.set_value(str(self._logical_count))

        except Exception as e:
            print(f"CPU info load error: {e}")
            self._cpu_info = {'name': 'Unknown CPU', 'architecture': 'x64'}

    def _get_cpu_name_fallback(self) -> str:
        """Get CPU name from registry or platform"""
        # Try WMI first (Windows) - gives proper full name like "12th Gen Intel Core i9-12900F"
        if platform.system() == 'Windows':
            try:
                import wmi
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                    if cpu.Name:
                        return cpu.Name.strip()
            except Exception:
                pass

        # Fallback to platform.processor()
        name = platform.processor()
        if name and name.strip():
            return name.strip()

        return "Unknown CPU"

    def _start_update_timer(self):
        """Start the real-time update timer"""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(500)  # Update display every 500ms

        # Initial update
        self._update_display()

    def _on_data_ready(self, data):
        """Handle data from background thread"""
        if 'cpu' in data:
            cpu = data['cpu']
            self._per_core = cpu.get('per_core', [])
            self._total_usage = cpu.get('percent', 0)

    def _update_display(self):
        """Update display with cached CPU data"""
        try:
            # Use cached data from collector if available
            per_core = getattr(self, '_per_core', None)
            total_usage = getattr(self, '_total_usage', None)

            if per_core is None or total_usage is None:
                per_core = psutil.cpu_percent(interval=None, percpu=True)
                total_usage = psutil.cpu_percent(interval=None)

            colors = c()

            # Update usage indicator color
            if total_usage > 80:
                usage_color = colors.ACCENT_RED
            elif total_usage > 60:
                usage_color = colors.ACCENT_ORANGE
            elif total_usage > 40:
                usage_color = colors.ACCENT_YELLOW
            else:
                usage_color = colors.ACCENT_BLUE

            self._usage_indicator.setStyleSheet(f"color: {usage_color}; font-size: 18px; font-weight: bold;")
            self._usage_indicator.setText(f"{total_usage:.0f}%")

            # Update frequency
            freq = psutil.cpu_freq()
            if freq:
                self._stat_freq.set_value(f"{freq.current:.0f} MHz")

            # Update uptime
            if self._boot_time:
                uptime_sec = int(time.time() - self._boot_time)
                days = uptime_sec // 86400
                hours = (uptime_sec % 86400) // 3600
                if days > 0:
                    self._stat_uptime.set_value(f"{days}d {hours}h")
                elif hours > 0:
                    self._stat_uptime.set_value(f"{hours}h")
                else:
                    mins = uptime_sec // 60
                    self._stat_uptime.set_value(f"{mins}m")

            # Update each core graph
            for i, usage in enumerate(per_core):
                if i < len(self._core_graphs):
                    self._core_graphs[i].set_value(usage)

            # Update info panel
            self._update_info_panel(total_usage, per_core)

        except Exception as e:
            print(f"CPU update error: {e}")

    def _update_info_panel(self, total_usage, per_core):
        """Update the info panel with current data"""
        colors = c()

        # Check if info panel widgets exist
        if not hasattr(self, '_info_name') or self._info_name is None:
            return

        try:
            # Basic info
            name_widget = self._info_name.layout().itemAt(1).widget()
            if name_widget:
                name_widget.setText(self._cpu_info.get('name', 'Unknown')[:45])

            arch_widget = self._info_arch.layout().itemAt(1).widget()
            if arch_widget:
                arch_widget.setText(self._cpu_info.get('architecture', 'x64'))

            # Uptime
            if self._boot_time:
                uptime_sec = int(time.time() - self._boot_time)
                days = uptime_sec // 86400
                hours = (uptime_sec % 86400) // 3600
                mins = (uptime_sec % 3600) // 60
                if days > 0:
                    uptime_str = f"{days}d {hours}h {mins}m"
                elif hours > 0:
                    uptime_str = f"{hours}h {mins}m"
                else:
                    uptime_str = f"{mins}m"
                uptime_widget = self._info_uptime.layout().itemAt(1).widget()
                if uptime_widget:
                    uptime_widget.setText(uptime_str)

            # Specs
            cores_widget = self._info_cores.layout().itemAt(1).widget()
            if cores_widget:
                cores_widget.setText(str(psutil.cpu_count(logical=False) or 1))

            threads_widget = self._info_threads.layout().itemAt(1).widget()
            if threads_widget:
                threads_widget.setText(str(self._logical_count))

            freq = psutil.cpu_freq()
            if freq:
                freq_widget = self._info_freq.layout().itemAt(1).widget()
                if freq_widget:
                    freq_widget.setText(f"{freq.current:.0f} MHz")

            # Usage
            if total_usage > 80:
                usage_color = colors.ACCENT_RED
            elif total_usage > 60:
                usage_color = colors.ACCENT_ORANGE
            elif total_usage > 40:
                usage_color = colors.ACCENT_YELLOW
            else:
                usage_color = colors.ACCENT_GREEN

            usage_lbl = self._info_usage.layout().itemAt(1).widget()
            if usage_lbl:
                usage_lbl.setText(f"{total_usage:.1f}%")
                usage_lbl.setStyleSheet(f"color: {usage_color}; font-weight: bold;")

            # Process count
            try:
                proc_count = len(psutil.pids())
            except Exception:
                proc_count = 0
            procs_widget = self._info_procs.layout().itemAt(1).widget()
            if procs_widget:
                procs_widget.setText(str(proc_count))

            # Interrupts
            try:
                stats = psutil.cpu_stats()
                interrupts = stats.interrupts if hasattr(stats, 'interrupts') else 0
            except Exception:
                interrupts = 0
            interrupts_widget = self._info_interrupts.layout().itemAt(1).widget()
            if interrupts_widget:
                interrupts_widget.setText(str(interrupts))
        except Exception as e:
            pass  # Silently ignore update errors

    def resizeEvent(self, event):
        """Handle resize to recalculate grid columns"""
        super().resizeEvent(event)
        # Grid auto-adjusts via size policy, no manual recalculation needed