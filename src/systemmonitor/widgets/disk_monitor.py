"""
DiskMonitor - Comprehensive disk monitoring widget
Shows disk space, read/write speed, and temperature with status indicators.
"""
import time
import platform
import psutil
from typing import Dict, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager


class SpeedGauge(QWidget):
    """
    Compact speed indicator showing read/write rates
    Draws a small arc gauge with speed value in center
    """
    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._read_speed = 0.0  # bytes/sec
        self._write_speed = 0.0
        theme_manager.theme_changed.connect(self.update)

    def set_speeds(self, read_bps: float, write_bps: float):
        """Update read/write speeds in bytes per second"""
        self._read_speed = max(0, read_bps)
        self._write_speed = max(0, write_bps)
        self.update()

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to human readable string"""
        if bps >= 1_073_741_824:  # GB/s
            return f"{bps / 1_073_741_824:.1f} GB/s"
        elif bps >= 1_048_576:  # MB/s
            return f"{bps / 1_048_576:.1f} MB/s"
        elif bps >= 1024:  # KB/s
            return f"{bps / 1024:.1f} KB/s"
        return f"{bps:.0f} B/s"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        center = self._size / 2

        # Read arc (top half, green)
        read_rect = QRectF(4, 4, self._size - 8, self._size - 8)
        read_angle = min(180, (self._read_speed / 200_000_000) * 180)  # 200MB/s = full
        painter.setPen(QPen(QColor(c.ACCENT_GREEN), 4, Qt.PenStyle.RoundCap))
        painter.drawArc(read_rect.toRect(), 180 * 16, -int(read_angle) * 16)

        # Write arc (bottom half, blue)
        write_rect = QRectF(4, 4, self._size - 8, self._size - 8)
        write_angle = min(180, (self._write_speed / 200_000_000) * 180)
        painter.setPen(QPen(QColor(c.ACCENT_BLUE), 4, Qt.PenStyle.RoundCap))
        painter.drawArc(write_rect.toRect(), 0 * 16, int(write_angle) * 16)

        # Center text - read speed
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(c.ACCENT_GREEN))
        read_text = self._format_speed(self._read_speed)
        painter.drawText(int(center - 28), int(center + 3), read_text)

        # Write speed below
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(c.ACCENT_BLUE))
        write_text = self._format_speed(self._write_speed)
        painter.drawText(int(center - 24), int(center + 14), write_text)

        painter.end()


class TemperatureIndicator(QWidget):
    """
    Temperature display with color-coded status
    Shows temperature value with indicator bar
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp = 0
        self.setFixedHeight(40)

    def set_temperature(self, temp_c: float):
        """Set temperature in Celsius"""
        self._temp = max(0, min(120, temp_c))  # Clamp 0-120°C
        self.update()

    def _get_status_color(self, temp: float) -> QColor:
        """Get color based on temperature thresholds"""
        c = theme_manager.colors
        if temp >= 85:  # Critical
            return QColor(c.ACCENT_RED)
        elif temp >= 70:  # Warning
            return QColor(c.ACCENT_ORANGE)
        return QColor(c.ACCENT_GREEN)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        # Temperature bar background
        bar_height = 6
        bar_y = 8
        bar_width = self.width() - 60
        bar_x = 50

        # Background
        painter.setBrush(QColor(c.BG_SECONDARY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_width), bar_height, 3, 3)

        # Temperature fill
        fill_width = (self._temp / 100) * bar_width
        status_color = self._get_status_color(self._temp)
        painter.setBrush(status_color)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(fill_width), bar_height, 3, 3)

        # Temperature label
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(c.TEXT_PRIMARY))
        painter.drawText(0, int(bar_y + 15), f"{self._temp:.0f}°C")

        # Status icon (circle indicator)
        icon_x = bar_x + bar_width + 10
        painter.setBrush(status_color)
        painter.drawEllipse(int(icon_x), int(bar_y), 10, 10)

        painter.end()


class DiskCard(QFrame):
    """
    Individual disk card showing all disk metrics
    Includes space usage, speed gauges, and temperature
    """
    # Signal emitted when disk is clicked (for future drill-down)
    disk_clicked = pyqtSignal(str)

    def __init__(self, drive_info: Dict, parent=None):
        super().__init__(parent)
        self._drive_info = drive_info
        self._temperature = None  # Will be set via update_temperature()
        self._read_speed = 0.0
        self._write_speed = 0.0
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Build the disk card layout"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: 1px solid {c.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        # Top row: Drive icon + name + letter
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Drive icon
        icon_label = QLabel()
        icon_label.setStyleSheet("background: transparent;")
        try:
            sz = S.px(28)
            icon_label.setPixmap(
                qta.icon("ph.hard-drive", color=theme_manager.colors.ACCENT_GREEN).pixmap(QSize(sz, sz))
            )
            icon_label.setFixedSize(sz, sz)
        except Exception:
            icon_label.setText("HDD")
            icon_label.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        top_row.addWidget(icon_label)

        # Drive name and mount point
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        drive_letter = self._drive_info.get('device', 'Unknown')[:2]
        name_label = QLabel(f"{drive_letter} {self._drive_info.get('mountpoint', '')}")
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c.TEXT_PRIMARY};")
        name_layout.addWidget(name_label)

        fs_label = QLabel(f"{self._drive_info.get('fstype', 'Unknown')} • {self._format_size(self._drive_info.get('total', 0))}")
        fs_label.setFont(QFont("Segoe UI", 10))
        fs_label.setStyleSheet(f"color: {c.TEXT_MUTED};")
        name_layout.addWidget(fs_label)

        top_row.addLayout(name_layout)
        top_row.addStretch()

        # Usage percentage (large)
        pct = self._drive_info.get('percent', 0)
        pct_label = QLabel(f"{pct:.0f}%")
        pct_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        pct_label.setStyleSheet(f"color: {self._get_usage_color(pct)};")
        top_row.addWidget(pct_label)

        main_layout.addLayout(top_row)

        # Progress bar for usage
        self._usage_bar = QProgressBar()
        self._usage_bar.setValue(int(pct))
        self._usage_bar.setFixedHeight(8)
        self._usage_bar.setTextVisible(False)
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_HOVER};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._get_usage_color(pct)};
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(self._usage_bar)

        # Space info row
        space_row = QHBoxLayout()
        used_gb = self._drive_info.get('used', 0) / (1024**3)
        free_gb = self._drive_info.get('free', 0) / (1024**3)
        total_gb = self._drive_info.get('total', 0) / (1024**3)

        used_label = QLabel(f"Used: {used_gb:.1f} GB")
        used_label.setFont(QFont("Segoe UI", 10))
        used_label.setStyleSheet(f"color: {c.TEXT_SECONDARY};")
        space_row.addWidget(used_label)

        space_row.addStretch()

        free_label = QLabel(f"Free: {free_gb:.1f} GB")
        free_label.setFont(QFont("Segoe UI", 10))
        free_label.setStyleSheet(f"color: {c.ACCENT_GREEN};")
        space_row.addWidget(free_label)

        main_layout.addLayout(space_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {c.BORDER}; max-height: 1px;")
        main_layout.addWidget(divider)

        # Bottom row: Speed + Temperature
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Speed section
        speed_label = QLabel("Speed")
        speed_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        speed_label.setStyleSheet(f"color: {c.TEXT_MUTED};")
        bottom_row.addWidget(speed_label)

        self._speed_gauge = SpeedGauge(size=60)
        bottom_row.addWidget(self._speed_gauge)

        # Read/Write labels
        speed_info = QVBoxLayout()
        speed_info.setSpacing(2)

        read_lbl = QLabel("R: -- MB/s")
        read_lbl.setFont(QFont("Segoe UI", 9))
        read_lbl.setStyleSheet(f"color: {c.ACCENT_GREEN};")
        read_lbl.setObjectName("read_speed_label")
        speed_info.addWidget(read_lbl)

        write_lbl = QLabel("W: -- MB/s")
        write_lbl.setFont(QFont("Segoe UI", 9))
        write_lbl.setStyleSheet(f"color: {c.ACCENT_BLUE};")
        write_lbl.setObjectName("write_speed_label")
        speed_info.addWidget(write_lbl)

        bottom_row.addLayout(speed_info)
        bottom_row.addStretch()

        # Temperature section
        temp_label = QLabel("Temp")
        temp_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        temp_label.setStyleSheet(f"color: {c.TEXT_MUTED};")
        bottom_row.addWidget(temp_label)

        self._temp_indicator = TemperatureIndicator()
        self._temp_indicator.setFixedWidth(120)
        bottom_row.addWidget(self._temp_indicator)

        main_layout.addLayout(bottom_row)

    def _get_usage_color(self, pct: float) -> str:
        """Get color for usage percentage"""
        c = theme_manager.colors
        if pct >= 90:
            return c.ACCENT_RED
        elif pct >= 75:
            return c.ACCENT_ORANGE
        return c.ACCENT_GREEN

    def _format_size(self, bytes_val: float) -> str:
        """Format bytes to human readable string"""
        tb = bytes_val / (1024**4)
        if tb >= 1:
            return f"{tb:.1f} TB"
        gb = bytes_val / (1024**3)
        if gb >= 1:
            return f"{gb:.1f} GB"
        return f"{bytes_val / (1024**2):.0f} MB"

    def update_space(self, used: float, free: float, total: float, percent: float):
        """Update disk space information"""
        self._drive_info.update({
            'used': used,
            'free': free,
            'total': total,
            'percent': percent
        })
        # Update UI elements
        self._usage_bar.setValue(int(percent))
        pct_label = self.findChild(QLabel, "")
        if pct_label:
            pct_label.setText(f"{percent:.0f}%")

    def update_speeds(self, read_bps: float, write_bps: float):
        """Update read/write speeds"""
        self._read_speed = read_bps
        self._write_speed = write_bps
        self._speed_gauge.set_speeds(read_bps, write_bps)

        # Update text labels
        read_lbl = self.findChild(QLabel, "read_speed_label")
        write_lbl = self.findChild(QLabel, "write_speed_label")
        if read_lbl:
            read_lbl.setText(f"R: {self._format_speed(read_bps)}")
        if write_lbl:
            write_lbl.setText(f"W: {self._format_speed(write_bps)}")

    def update_temperature(self, temp_c: float):
        """Update temperature display"""
        self._temperature = temp_c
        self._temp_indicator.set_temperature(temp_c)

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to MB/s or GB/s"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.1f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def _apply_theme(self):
        """Re-apply theme when theme changes"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: 1px solid {c.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)


class DiskMonitor(QWidget):
    """
    Main disk monitoring component
    Displays all disks with real-time updates
    Handles data collection and coordinates updates to child widgets
    """

    # Signal emitted when disk data is refreshed
    data_refreshed = pyqtSignal(list)

    def __init__(self, update_interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self._update_interval = update_interval_ms
        self._disk_collector = None
        self._disk_cards: Dict[str, DiskCard] = {}
        self._previous_io = None
        self._previous_time = None
        self._setup_ui()
        self._start_monitoring()

    def _setup_ui(self):
        """Initialize the UI layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Header
        header = QHBoxLayout()
        title = QLabel("Disk Monitor")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY};")
        header.addWidget(title)

        header.addStretch()

        # Refresh indicator
        self._status_label = QLabel("● Live")
        self._status_label.setFont(QFont("Segoe UI", 9))
        self._status_label.setStyleSheet(f"color: {theme_manager.colors.ACCENT_GREEN};")
        header.addWidget(self._status_label)

        main_layout.addLayout(header)

        # Container for disk cards
        self._cards_container = QVBoxLayout()
        self._cards_container.setSpacing(12)
        main_layout.addLayout(self._cards_container)

        # Initial scan
        self._update_disk_info()

    def _start_monitoring(self):
        """Start the periodic update timer"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_update_tick)
        self._timer.start(self._update_interval)

    def _on_update_tick(self):
        """Called every update interval - collect and display new data"""
        self._collect_io_stats()
        self._collect_temperature()
        self.data_refreshed.emit(list(self._disk_cards.keys()))

    def _collect_io_stats(self):
        """Collect read/write speed statistics"""
        try:
            current_io = psutil.disk_io_counters()
            current_time = time.time()

            if self._previous_io is None:
                self._previous_io = current_io
                self._previous_time = current_time
                return

            time_delta = current_time - self._previous_time
            if time_delta > 0:
                read_rate = (current_io.read_bytes - self._previous_io.read_bytes) / time_delta
                write_rate = (current_io.write_bytes - self._previous_io.write_bytes) / time_delta

                # Update all disk cards with new speeds
                for card in self._disk_cards.values():
                    card.update_speeds(read_rate, write_rate)

            self._previous_io = current_io
            self._previous_time = current_time

        except Exception as e:
            print(f"IO stats collection error: {e}")

    def _collect_temperature(self):
        """Collect disk temperature if available"""
        try:
            if platform.system() == 'Windows':
                try:
                    import wmi
                except ImportError:
                    return
                try:
                    w = wmi.WMI()
                    for disk in w.Win32_TemperatureProbe():
                        # Update first disk with this temperature (simplified)
                        for card in self._disk_cards.values():
                            if card._temperature is None:
                                card.update_temperature(disk.CurrentReading or 0)
                                break
                except (OSError, Exception):
                    # WMI query failed - temperature not available
                    pass
        except Exception:
            # Temperature not available - that's OK
            pass

    def _update_disk_info(self):
        """Scan and create/update disk cards"""
        try:
            partitions = psutil.disk_partitions(all=False)
            current_devices = set()

            for partition in partitions:
                if not partition.fstype:  # Skip CD-ROM etc
                    continue

                device = partition.device
                current_devices.add(device)

                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drive_info = {
                        'device': device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    }

                    if device in self._disk_cards:
                        # Update existing card
                        self._disk_cards[device].update_space(
                            usage.used, usage.free, usage.total, usage.percent
                        )
                    else:
                        # Create new card
                        card = DiskCard(drive_info)
                        self._disk_cards[device] = card
                        self._cards_container.addWidget(card)

                except PermissionError:
                    continue

            # Remove cards for drives that no longer exist
            removed = set(self._disk_cards.keys()) - current_devices
            for device in removed:
                card = self._disk_cards.pop(device)
                card.deleteLater()

        except Exception as e:
            print(f"Disk info update error: {e}")

    def set_update_interval(self, ms: int):
        """Change the update interval"""
        self._update_interval = ms
        if hasattr(self, '_timer'):
            self._timer.setInterval(ms)

    def stop(self):
        """Stop monitoring - call when widget is destroyed"""
        if hasattr(self, '_timer'):
            self._timer.stop()
