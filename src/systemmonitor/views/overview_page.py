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
    QScrollArea, QGridLayout, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.widgets.donut_gauge import DonutGauge
from systemmonitor.widgets.sparkline import SparklineWidget
from systemmonitor.widgets.responsive import CollapsiblePanel, ResponsiveGridLayout
from systemmonitor.widgets.overview_widgets import (
    GlassMetricCard, GlassChartPanel, GlassInfoPanel, GlassStoragePanel
)
from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin, LayoutMode
from systemmonitor.config import settings
from systemmonitor.utils.helpers import format_temperature, temperature_unit_suffix, network_speed_value


class OverviewPage(QWidget, ScaleMixin, I18nMixin):
    """Premium glass overview dashboard - responsive with adaptive grid"""

    def __init__(self, data_collector=None, parent=None):
        super().__init__(parent)
        self._data_collector = data_collector
        self._start_time = time.time()
        self._uptime_seconds = 0
        self._last_net = None
        self._net_down_speed = 0.0
        self._net_up_speed = 0.0
        self._last_data = {}
        self._system_info_cache = {}
        self._system_info_cache_time = 0
        self._system_info_cache_ttl = 30
        self._battery_row_value = None
        self._battery_block = None
        self._battery_val_label = None
        self._battery_icon_label = None
        self._has_battery = self._detect_battery()

        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        self._start_timers()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_data_collector(self, collector):
        self._data_collector = collector

    def _on_theme_changed(self, theme_name: str):
        QTimer.singleShot(0, self._rebuild_and_restore)

    def retranslate_ui(self):
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
        self._is_rebuilding = True
        try:
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
        except Exception:
            # Ignore errors during cleanup
            pass

        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        title = QLabel(tr("Dashboard"))
        title.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_section.addWidget(title)

        subtitle = QLabel(tr("System performance overview"))
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

        uptime_lbl = QLabel(tr("Uptime"))
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

        os_lbl = QLabel(tr("OS"))
        os_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        os_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        os_layout.addWidget(os_lbl)
        status_layout.addWidget(os_block)

        if self._has_battery:
            sep2 = QFrame()
            sep2.setFixedWidth(1)
            sep2.setMinimumHeight(S.px(28))
            sep2.setMaximumHeight(S.px(36))
            sep2.setStyleSheet("background-color: transparent;")
            status_layout.addWidget(sep2)

            battery_block = QFrame()
            battery_block.setStyleSheet(f"""
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(8)}px;
            """)
            battery_layout = QHBoxLayout()
            battery_layout.setSpacing(S.px(6))
            battery_layout.setContentsMargins(S.px(12), S.px(6), S.px(12), S.px(6))
            battery_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            battery_block.setLayout(battery_layout)

            battery_icon = QLabel()
            battery_icon.setPixmap(qta.icon('ph.battery-charging', color=colors.ACCENT_GREEN).pixmap(S.px(16), S.px(16)))
            battery_layout.addWidget(battery_icon)
            self._battery_icon_label = battery_icon

            battery_text_layout = QVBoxLayout()
            battery_text_layout.setSpacing(0)
            battery_text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self._battery_val_label = QLabel("--%")
            self._battery_val_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
            self._battery_val_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
            battery_text_layout.addWidget(self._battery_val_label)

            battery_lbl = QLabel(tr("Battery"))
            battery_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
            battery_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            battery_text_layout.addWidget(battery_lbl)

            battery_layout.addLayout(battery_text_layout)
            status_layout.addWidget(battery_block)
            self._battery_block = battery_block
        else:
            self._battery_block = None
            self._battery_val_label = None
            self._battery_icon_label = None

        layout.addLayout(status_layout)
        return header

    def _create_metrics_row(self):
        colors = theme_manager.colors
        row = QFrame()
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QGridLayout()
        layout.setSpacing(S.px(12))
        layout.setContentsMargins(0, 0, 0, 0)
        row.setLayout(layout)

        cpu_card = GlassMetricCard("CPU Load", "ph.cpu", colors.ACCENT_GREEN)
        cpu_card.set_value("--", tr("Loading..."))
        self._cpu_card = cpu_card

        gpu_card = GlassMetricCard("GPU Load", "ph.monitor", colors.ACCENT_PURPLE)
        gpu_card.set_value("--", tr("Loading..."))
        self._gpu_card = gpu_card

        ram_card = GlassMetricCard("Memory", "ph.hard-drive", colors.ACCENT_BLUE)
        ram_card.set_value("--", tr("Loading..."))
        self._ram_card = ram_card

        net_card = GlassMetricCard("Network", "ph.wifi-high", colors.ACCENT_CYAN)
        _, _net_unit = network_speed_value(0)
        net_card.set_value("0.0 / 0.0", tr("Down / Up {0}").format(_net_unit))
        self._net_card = net_card

        disk_card = GlassMetricCard("Disk Activity", "mdi.harddisk", colors.ACCENT_ORANGE)
        disk_card.set_value("-- / --", tr("R/W MB/s"))
        self._disk_card = disk_card

        temp_card = GlassMetricCard("Temperature", "ph.thermometer", colors.ACCENT_RED)
        temp_card.set_value(f"--{temperature_unit_suffix()}", tr("GPU temp"))
        self._temp_card = temp_card

        self._metric_cards = [cpu_card, gpu_card, ram_card, net_card, disk_card, temp_card]
        self._current_metric_cols = S.grid_columns_for(max(self.width(), 100))
        self._arrange_metric_grid(layout, self._current_metric_cols)

        return row

    def _arrange_metric_grid(self, layout: QGridLayout, cols: int):
        while layout.count():
            layout.takeAt(0)
        for i, card in enumerate(self._metric_cards):
            layout.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_cols = S.grid_columns_for(self.width())
        if new_cols != getattr(self, '_current_metric_cols', -1):
            self._current_metric_cols = new_cols
            if hasattr(self, '_metrics_row') and hasattr(self, '_metric_cards'):
                layout = self._metrics_row.layout()
                if isinstance(layout, QGridLayout):
                    self._arrange_metric_grid(layout, new_cols)

    def _create_charts_section(self):
        colors = theme_manager.colors
        section = QFrame()
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        row.setLayout(layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(S.px(8))
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")

        sysinfo_panel = self._create_sysinfo_panel()
        sysinfo_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        splitter.addWidget(sysinfo_panel)

        storage_panel = GlassStoragePanel()
        self._storage_panel = storage_panel
        storage_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        splitter.addWidget(storage_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        return row

    def _create_sysinfo_panel(self):
        colors = theme_manager.colors
        panel = GlassInfoPanel("System Information")

        panel.add_info_row("Processor", self._get_cpu_display(), colors.ACCENT_BLUE)
        panel.add_info_row("Graphics", self._get_gpu_display(), colors.ACCENT_PURPLE)
        panel.add_info_row("Memory", self._get_ram_display(), colors.ACCENT_GREEN)
        panel.add_info_row("Operating System", self._short_os(), colors.TEXT_SECONDARY)
        panel.add_info_row("Architecture", platform.machine(), colors.TEXT_MUTED)

        if self._has_battery:
            self._battery_row_value = panel.add_info_row("Battery", "—", colors.ACCENT_GREEN)
        else:
            self._battery_row_value = None

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

    def _detect_battery(self) -> bool:
        try:
            from systemmonitor.data.hardware.battery_manager import BatteryManager
            return BatteryManager().has_battery()
        except Exception:
            return False

    def _format_battery_display(self, battery: dict) -> tuple[str, str]:
        """Returns (display_text, accent_color) for a battery info dict."""
        colors = theme_manager.colors
        percent = battery.get('percent', 0)
        status = battery.get('status_text', 'Unknown')
        secs_left = battery.get('secs_left')

        text = f"{percent:.0f}% • {status}"
        if status == "On battery":
            from systemmonitor.data.hardware.battery_manager import BatteryManager
            remaining = BatteryManager.format_time_remaining(secs_left)
            if remaining != "—":
                text += f" • {remaining}"

        if status == "On battery" and percent <= 20:
            color = colors.ACCENT_RED
        elif status == "On battery" and percent <= 40:
            color = colors.ACCENT_ORANGE
        elif battery.get('power_plugged'):
            color = colors.ACCENT_GREEN
        else:
            color = colors.TEXT_PRIMARY

        return text, color

    def _short_os(self):
        p = platform.platform()
        if "Windows" in p:
            return "Windows " + platform.win32_ver()[0]
        return p

    def _short_cpu(self):
        cpu = platform.processor()
        if not cpu:
            return tr("Unknown")
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
            return tr("Unknown")
        if len(cpu) > 40:
            return cpu[:40] + "..."
        return cpu

    def _get_gpu_display(self):
        gpu = self._short_gpu()
        if not gpu or gpu == "N/A":
            return tr("Not detected")
        return gpu

    def _get_ram_display(self):
        now = time.time()
        if now - self._system_info_cache_time < self._system_info_cache_ttl and 'ram_info' in self._system_info_cache:
            return self._system_info_cache['ram_info']
        try:
            mem = psutil.virtual_memory()
            total_gb = round(mem.total / (1024**3))
            from systemmonitor.data.memory import get_ram_type
            ram_type = get_ram_type()
            result = f"{total_gb} GB {ram_type}" if ram_type else f"{total_gb} GB"
            self._system_info_cache['ram_info'] = result
            self._system_info_cache_time = now
            return result
        except Exception:
            return tr("Unknown")

    def update_data(self, data):
        """Called by MainWindow whenever new data arrives"""
        self._last_data = data

        if 'cpu' in data:
            cpu = data['cpu']
            pct = cpu.get('percent', 0)
            self._cpu_card.set_value(f"{pct:.0f}%", tr("{0:.1f}% utilization").format(pct))
            self._cpu_card.push_sparkline(pct)
            self._cpu_sparkline.push(pct)

        if 'gpu' in data:
            gpu = data['gpu']
            if gpu.get('available'):
                load = gpu.get('load')
                if load is not None:
                    self._gpu_card.set_value(f"{load:.0f}%", tr("GPU load"))
                    self._gpu_card.push_sparkline(load)
                    self._gpu_sparkline.push(load)

        if 'memory' in data:
            mem = data['memory']
            pct = mem.get('percent', 0)
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            self._ram_card.set_value(f"{used_gb:.1f} GB", tr("{0:.0f}% of {1:.0f} GB").format(pct, total_gb))
            self._ram_card.push_sparkline(pct)
            self._ram_sparkline.push(pct)

        if 'network' in data:
            net = data['network']
            bytes_sent = net.get('bytes_sent', 0)
            bytes_recv = net.get('bytes_recv', 0)

            if self._last_net:
                dt = 1.0
                down_bps = max(0.0, (bytes_recv - self._last_net[0]) / dt)
                up_bps = max(0.0, (bytes_sent - self._last_net[1]) / dt)

                down_speed, speed_unit = network_speed_value(down_bps)
                up_speed, _ = network_speed_value(up_bps)
                precision = settings.get('decimal_places', 1)

                self._net_down_speed = down_speed
                self._net_up_speed = up_speed

                self._net_card.set_value(
                    f"{down_speed:.{precision}f} / {up_speed:.{precision}f}",
                    tr("Down / Up {0}").format(speed_unit)
                )
                self._net_sparkline.push_multi([down_speed, up_speed])

            self._last_net = (bytes_sent, bytes_recv)

        if 'disk' in data:
            disk = data['disk']
            read_speed = disk.get('read_speed', 0)
            write_speed = disk.get('write_speed', 0)
            self._disk_card.set_value(
                f"{read_speed:.0f} / {write_speed:.0f}",
                tr("R/W MB/s")
            )

        if 'gpu' in data:
            gpu = data['gpu']
            temp = gpu.get('temperature')
            
            # Fallback: Search all GPUs in the list if primary temp is missing
            if temp is None and 'gpus' in gpu:
                for g in gpu['gpus']:
                    g_temp = g.get('temperature_celsius')
                    if g_temp is not None and g_temp > 0:
                        temp = g_temp
                        break
            
            if temp is not None:
                self._temp_card.set_value(format_temperature(temp), tr("GPU temp"))
                self._temp_card.push_sparkline(temp)
            else:
                # If still no temp, try to see if cpu temp is available as a system-wide fallback
                cpu_temp = data.get('cpu', {}).get('temperature')
                if cpu_temp:
                    self._temp_card.set_value(format_temperature(cpu_temp), tr("System temp"))
                    self._temp_card.push_sparkline(cpu_temp)

        if 'disk' in data:
            partitions = data['disk'].get('partitions', [])
            if partitions:
                self._storage_panel.update_drives(partitions)

        if self._has_battery and 'system_info' in data:
            battery = data['system_info'].get('battery')
            if battery:
                self._update_battery_display(battery)

    def _update_battery_display(self, battery: dict):
        text, color = self._format_battery_display(battery)
        percent = battery.get('percent', 0)
        plugged = battery.get('power_plugged')

        if self._battery_row_value is not None:
            self._battery_row_value.setText(text)
            self._battery_row_value.setStyleSheet(f"color: {color}; background: transparent;")

        if self._battery_val_label is not None:
            self._battery_val_label.setText(f"{percent:.0f}%")
            self._battery_val_label.setStyleSheet(f"color: {color}; background: transparent;")

        if self._battery_icon_label is not None:
            if plugged:
                icon_name = 'ph.battery-charging'
            elif percent <= 15:
                icon_name = 'ph.battery-warning'
            elif percent <= 40:
                icon_name = 'ph.battery-low'
            elif percent <= 75:
                icon_name = 'ph.battery-medium'
            else:
                icon_name = 'ph.battery-full'
            self._battery_icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(S.px(16), S.px(16)))
