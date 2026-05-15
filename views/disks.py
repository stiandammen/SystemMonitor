"""
Disks View - Comprehensive disk monitoring with space, speed, and temperature
Shows all disk metrics with color-coded status indicators and real-time updates.
"""
import psutil
import platform
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class DiskIcon(QWidget):
    """Modern SSD/NVMe drive icon drawn with QPainter"""
    def __init__(self, size=48, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        theme_manager.theme_changed.connect(self.update)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w = self.width()
        h = self.height()
        pad = w * 0.08
        body_h = h * 0.72
        body_y = h * 0.12

        # Main body
        body_rect = QRectF(pad, body_y, w - pad * 2, body_h)
        body_grad = QLinearGradient(0, body_y, 0, body_y + body_h)
        body_grad.setColorAt(0, QColor(55, 65, 80))
        body_grad.setColorAt(1, QColor(30, 38, 52))
        painter.setBrush(body_grad)
        painter.setPen(QPen(QColor(20, 26, 36), 1.5))
        painter.drawRoundedRect(body_rect.toRect(), 3, 3)

        # Notch cut on right side (M.2 style)
        notch_w = w * 0.06
        notch_h = h * 0.22
        notch_x = w - pad - notch_w
        notch_y = body_y + body_h * 0.4
        painter.setBrush(QColor(c.BG_PRIMARY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(int(notch_x), int(notch_y), int(notch_w), int(notch_h))

        # Gold pins at bottom
        pin_area_h = h * 0.1
        pin_area_y = body_y + body_h
        pin_area_rect = QRectF(pad, pin_area_y, w - pad * 2, pin_area_h)
        pin_grad = QLinearGradient(0, pin_area_y, 0, pin_area_y + pin_area_h)
        pin_grad.setColorAt(0, QColor(200, 165, 90))
        pin_grad.setColorAt(1, QColor(160, 130, 60))
        painter.setBrush(pin_grad)
        painter.setPen(QPen(QColor(130, 100, 40), 1))
        painter.drawRect(pin_area_rect.toRect())

        # Horizontal pin dividers
        pin_count = 6
        pin_w_step = (w - pad * 2) / pin_count
        painter.setPen(QPen(QColor(130, 100, 40), 0.8))
        for i in range(1, pin_count):
            x = int(pad + i * pin_w_step)
            painter.drawLine(x, int(pin_area_y), x, int(pin_area_y + pin_area_h))

        # Label area
        label_pad = w * 0.12
        label_w = w - pad * 2 - label_pad * 2
        label_h = h * 0.18
        label_y = body_y + body_h * 0.18
        label_rect = QRectF(pad + label_pad, label_y, label_w, label_h)
        label_grad = QLinearGradient(0, label_y, 0, label_y + label_h)
        label_grad.setColorAt(0, QColor(80, 90, 110))
        label_grad.setColorAt(1, QColor(65, 75, 95))
        painter.setBrush(label_grad)
        painter.setPen(QPen(QColor(50, 60, 78), 1))
        painter.drawRoundedRect(label_rect.toRect(), 1, 1)

        # Small chip on body (flash chip)
        chip_w = w * 0.18
        chip_h = h * 0.14
        chip_x = w * 0.22
        chip_y = body_y + body_h * 0.52
        painter.setBrush(QColor(25, 30, 42))
        painter.setPen(QPen(QColor(40, 48, 65), 1))
        painter.drawRect(int(chip_x), int(chip_y), int(chip_w), int(chip_h))
        painter.setBrush(QColor(180, 140, 50))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(chip_x + 2), int(chip_y + 2), 3, 3)

        # Controller chip
        ctrl_size = w * 0.1
        ctrl_x = w * 0.58
        ctrl_y = body_y + body_h * 0.55
        painter.setBrush(QColor(20, 24, 35))
        painter.setPen(QPen(QColor(35, 42, 58), 1))
        painter.drawRect(int(ctrl_x), int(ctrl_y), int(ctrl_size), int(ctrl_size))

        painter.end()


class SpeedGaugeWidget(QWidget):
    """
    Compact speed gauge showing read/write speeds
    Draws arc indicators with MB/s values
    """
    def __init__(self, size=80, parent=None):
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
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        center = self._size / 2

        # Read arc (top half, green)
        read_rect = QRectF(4, 4, self._size - 8, self._size - 8)
        read_angle = min(180, (self._read_speed / 200_000_000) * 180)  # 200MB/s = full
        painter.setPen(QPen(QColor(c.ACCENT_GREEN), 5, cap=Qt.PenCapStyle.RoundCap))
        painter.drawArc(read_rect.toRect(), 180 * 16, -int(read_angle) * 16)

        # Write arc (bottom half, blue)
        write_rect = QRectF(4, 4, self._size - 8, self._size - 8)
        write_angle = min(180, (self._write_speed / 200_000_000) * 180)
        painter.setPen(QPen(QColor(c.ACCENT_BLUE), 5, cap=Qt.PenCapStyle.RoundCap))
        painter.drawArc(write_rect.toRect(), 0 * 16, int(write_angle) * 16)

        # Center text - read speed
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor(c.ACCENT_GREEN))
        read_text = self._format_speed(self._read_speed)
        fm = painter.fontMetrics()
        painter.drawText(int(center - fm.horizontalAdvance(read_text) / 2), int(center + 3), read_text)

        # Write speed below
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(c.ACCENT_BLUE))
        write_text = self._format_speed(self._write_speed)
        painter.drawText(int(center - fm.horizontalAdvance(write_text) / 2), int(center + 14), write_text)

        painter.end()


class TemperatureWidget(QWidget):
    """
    Temperature display with color-coded status bar
    Shows temperature value with gradient indicator
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp = 0
        self.setFixedHeight(36)

    def set_temperature(self, temp_c: float):
        """Set temperature in Celsius"""
        self._temp = max(0, min(120, temp_c))  # Clamp 0-120°C
        self.update()

    def _get_status_color(self) -> QColor:
        """Get color based on temperature thresholds"""
        c = theme_manager.colors
        if self._temp >= 85:
            return QColor(c.ACCENT_RED)
        elif self._temp >= 70:
            return QColor(c.ACCENT_ORANGE)
        return QColor(c.ACCENT_GREEN)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        # Background bar
        bar_height = 6
        bar_y = 6
        bar_width = self.width() - 50
        bar_x = 40

        painter.setBrush(QColor(c.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_width), bar_height, 3, 3)

        # Temperature fill
        fill_width = (self._temp / 100) * bar_width
        status_color = self._get_status_color()
        painter.setBrush(status_color)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(fill_width), bar_height, 3, 3)

        # Temperature label
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(c.TEXT_PRIMARY))
        painter.drawText(0, int(bar_y + 14), f"{self._temp:.0f}°C")

        # Status indicator circle
        icon_x = bar_x + bar_width + 8
        painter.setBrush(status_color)
        painter.drawEllipse(int(icon_x), int(bar_y), 10, 10)

        painter.end()


class DiskCard(QFrame):
    """
    Individual disk card showing all disk metrics
    Includes space usage, speed gauges, and temperature
    """
    def __init__(self, drive_info: dict, parent=None):
        super().__init__(parent)
        self._drive_info = drive_info
        self._temperature = 0
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

        # Top row: Drive icon + name + letter + percentage
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Drive icon
        icon_label = QLabel("💾")
        icon_label.setFont(QFont("Segoe UI", 24))
        top_row.addWidget(icon_label)

        # Drive name and mount point
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        drive_letter = self._drive_info.get('device', 'Unknown')[:2]
        fs_type = self._drive_info.get('fstype', 'Unknown')
        mountpoint = self._drive_info.get('mountpoint', '')

        name_label = QLabel(f"{drive_letter} {mountpoint}" if mountpoint else drive_letter)
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        name_layout.addWidget(name_label)

        fs_label = QLabel(f"{fs_type} • {self._format_size(self._drive_info.get('total', 0))}")
        fs_label.setFont(QFont("Segoe UI", 10))
        fs_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        name_layout.addWidget(fs_label)

        top_row.addLayout(name_layout)
        top_row.addStretch()

        # Usage percentage (large)
        pct = self._drive_info.get('percent', 0)
        self._pct_label = QLabel(f"{pct:.0f}%")
        self._pct_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._pct_label.setObjectName("pct_label")
        self._pct_label.setStyleSheet(f"color: {self._get_usage_color(pct)}; background: transparent;")
        top_row.addWidget(self._pct_label)

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

        used_label = QLabel(f"Used: {used_gb:.1f} GB")
        used_label.setFont(QFont("Segoe UI", 10))
        used_label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        space_row.addWidget(used_label)

        space_row.addStretch()

        free_label = QLabel(f"Free: {free_gb:.1f} GB")
        free_label.setFont(QFont("Segoe UI", 10))
        free_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        space_row.addWidget(free_label)

        main_layout.addLayout(space_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {c.BORDER}; max-height: 1px;")
        main_layout.addWidget(divider)

        # Bottom row: Speed + Temperature sections
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        # Speed section
        speed_section = QVBoxLayout()
        speed_section.setSpacing(4)

        speed_header = QLabel("Speed")
        speed_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        speed_header.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        speed_section.addWidget(speed_header)

        speed_content = QHBoxLayout()
        speed_content.setSpacing(8)

        self._speed_gauge = SpeedGaugeWidget(size=60)
        speed_content.addWidget(self._speed_gauge)

        speed_labels = QVBoxLayout()
        speed_labels.setSpacing(2)

        self._read_label = QLabel("R: -- MB/s")
        self._read_label.setFont(QFont("Segoe UI", 9))
        self._read_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        speed_labels.addWidget(self._read_label)

        self._write_label = QLabel("W: -- MB/s")
        self._write_label.setFont(QFont("Segoe UI", 9))
        self._write_label.setStyleSheet(f"color: {c.ACCENT_BLUE}; background: transparent;")
        speed_labels.addWidget(self._write_label)

        speed_content.addLayout(speed_labels)
        speed_section.addLayout(speed_content)
        bottom_row.addLayout(speed_section)

        bottom_row.addStretch()

        # Temperature section
        temp_section = QVBoxLayout()
        temp_section.setSpacing(4)

        temp_header = QLabel("Temperature")
        temp_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        temp_header.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        temp_section.addWidget(temp_header)

        self._temp_widget = TemperatureWidget()
        self._temp_widget.setFixedWidth(140)
        temp_section.addWidget(self._temp_widget)

        bottom_row.addLayout(temp_section)

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

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to MB/s or GB/s"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.1f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def update_space(self, used: float, free: float, total: float, percent: float):
        """Update disk space information"""
        self._drive_info.update({
            'used': used,
            'free': free,
            'total': total,
            'percent': percent
        })
        self._usage_bar.setValue(int(percent))
        self._pct_label.setText(f"{percent:.0f}%")
        self._pct_label.setStyleSheet(f"color: {self._get_usage_color(percent)}; background: transparent;")
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme_manager.colors.BG_HOVER};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._get_usage_color(percent)};
                border-radius: 4px;
            }}
        """)

    def update_speeds(self, read_bps: float, write_bps: float):
        """Update read/write speeds"""
        self._read_speed = read_bps
        self._write_speed = write_bps
        self._speed_gauge.set_speeds(read_bps, write_bps)
        self._read_label.setText(f"R: {self._format_speed(read_bps)}")
        self._write_label.setText(f"W: {self._format_speed(write_bps)}")

    def update_temperature(self, temp_c: float):
        """Update temperature display"""
        self._temperature = temp_c
        self._temp_widget.set_temperature(temp_c)

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


class DisksView(QWidget, ScaleMixin):
    """
    Disk monitoring view with comprehensive metrics
    Shows all disks with space usage, read/write speeds, and temperature
    Real-time updates via data collector
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disk_cards = {}  # device -> DiskCard
        self._temps = {}  # device -> temperature
        self._data_collector = None
        self._pending_update = False
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def set_data_collector(self, collector):
        """Set data collector for receiving updates"""
        self._data_collector = collector
        if collector:
            collector.data_ready.connect(self._on_data_ready)

    def _on_data_ready(self, data: dict):
        """Handle data from collector"""
        if 'disk' not in data:
            return
        disk_data = data['disk']

        # Update partition space info and IO rates
        partitions = disk_data.get('partitions', [])
        partition_io = disk_data.get('partition_io', {})

        # Build lookup by mountpoint
        io_by_mountpoint = {}
        for part in partitions:
            mountpoint = part.get('mountpoint')
            if mountpoint in partition_io:
                io_by_mountpoint[mountpoint] = partition_io[mountpoint]

        for part in partitions:
            device = part.get('device')
            mountpoint = part.get('mountpoint')

            if device in self._disk_cards:
                card = self._disk_cards[device]
                # Update space
                card.update_space(
                    part.get('used', 0),
                    part.get('free', 0),
                    part.get('total', 0),
                    part.get('percent', 0)
                )
                # Update IO rates - use mountpoint-based lookup if available
                if mountpoint and mountpoint in io_by_mountpoint:
                    io = io_by_mountpoint[mountpoint]
                    card.update_speeds(
                        io.get('read_rate', 0),
                        io.get('write_rate', 0)
                    )
                else:
                    # Fallback to total IO rates
                    total_read = disk_data.get('read_rate', 0)
                    total_write = disk_data.get('write_rate', 0)
                    card.update_speeds(total_read, total_write)

        # Temperature is collected separately via timer
        self._collect_temperature()

    def _on_update(self):
        """Periodic update - collect temperature only (IO comes via collector)"""
        self._collect_temperature()

    def _collect_temperature(self):
        """Collect disk temperature using WMI on Windows"""
        try:
            if platform.system() == 'Windows':
                try:
                    import wmi
                except ImportError:
                    return
                try:
                    w = wmi.WMI()
                    for disk in w.Win32_TemperatureProbe():
                        temp = disk.CurrentReading
                        if temp and temp > 0:
                            # Apply to first disk that doesn't have temp set
                            for card in self._disk_cards.values():
                                if card._temperature == 0:
                                    card.update_temperature(temp)
                                    break
                except (OSError, RuntimeError):
                    # WMI query failed - temperature not available
                    pass
        except Exception:
            pass  # Temperature not available

    def _scan_disks(self):
        """Scan for disk partitions and create/update cards"""
        try:
            partitions = psutil.disk_partitions(all=False)
            current_devices = set()

            for partition in partitions:
                if not partition.fstype:
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
                        self._cards_layout.addWidget(card)

                except PermissionError:
                    continue

            # Remove cards for drives that no longer exist
            removed = set(self._disk_cards.keys()) - current_devices
            for device in removed:
                card = self._disk_cards.pop(device)
                card.deleteLater()

        except Exception as e:
            print(f"Disk scan error: {e}")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self._scan_disks()

    def on_scale_changed(self, factor: float):
        self.update()

    def update_data(self, data):
        """Update view with new data from data collector"""
        self._on_data_ready(data)