"""
Disks View - Modern glassmorphism disk monitoring
Glass effect cards with subtle glow and frosted appearance.
"""
import psutil
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import pyqtSignal

from styles.theme import theme_manager, css_color_to_hex
from scaler import S, ScaleMixin


class GlassCard(QFrame):
    """
    Modern glassmorphism card with frosted glass effect
    Features:
    - Semi-transparent background with subtle gradient
    - Soft outer glow (ambient light effect)
    - Inner highlight for depth
    - Clean rounded corners
    """
    def __init__(self, glow_color=None, intensity=0.5, parent=None):
        super().__init__(parent)
        self._glow_color = glow_color or QColor(59, 130, 246)  # accent blue
        self._intensity = intensity
        self._corner_radius = 16
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def set_glow_color(self, color: QColor):
        self._glow_color = color
        self.update()

    def set_intensity(self, intensity: float):
        self._intensity = max(0.1, min(1.0, intensity))
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.RenderHint.SmoothPixmap)
        c = theme_manager.colors

        rect = self.rect()
        inner_rect = rect.adjusted(1, 1, -1, -1)

        # --- Outer ambient glow (soft, diffused) ---
        glow_alpha = int(25 * self._intensity)
        glow_rect = inner_rect.adjusted(-8, -8, 8, 8)
        glow = QColor(self._glow_color.red(), self._glow_color.green(), self._glow_color.blue(), glow_alpha)
        painter.setPen(QPen(glow, 16))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(glow_rect, self._corner_radius + 4, self._corner_radius + 4)

        # --- Middle glow ring ---
        mid_alpha = int(40 * self._intensity)
        mid_glow = QColor(self._glow_color.red(), self._glow_color.green(), self._glow_color.blue(), mid_alpha)
        mid_rect = inner_rect.adjusted(-3, -3, 3, 3)
        painter.setPen(QPen(mid_glow, 4))
        painter.drawRoundedRect(mid_rect, self._corner_radius + 1, self._corner_radius + 1)

        # --- Card background with glass gradient ---
        bg_alpha = int(180 * self._intensity)
        glass_gradient = QLinearGradient(0, 0, 0, rect.height())
        glass_gradient.setColorAt(0, QColor(255, 255, 255, int(18 * self._intensity)))  # Top highlight
        glass_gradient.setColorAt(0.3, QColor(255, 255, 255, int(8 * self._intensity)))
        glass_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(glass_gradient)
        painter.setPen(QPen(QColor(css_color_to_hex(c.BORDER)), 0))
        painter.drawRoundedRect(inner_rect, self._corner_radius, self._corner_radius)

        # --- Subtle inner border highlight (top-left light catch) ---
        highlight_alpha = int(30 * self._intensity)
        highlight_rect = inner_rect.adjusted(1, 1, -1, -1)
        highlight_color = QColor(255, 255, 255, highlight_alpha)
        painter.setPen(QPen(highlight_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(highlight_rect, self._corner_radius - 1, self._corner_radius - 1)

        # --- Bottom shadow edge ---
        shadow_gradient = QLinearGradient(0, rect.height() - 20, 0, rect.height())
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, int(15 * self._intensity)))
        painter.setBrush(shadow_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(inner_rect, self._corner_radius, self._corner_radius)

        painter.end()


class SpeedGauge(QWidget):
    """
    Circular speed gauge with read/write arcs
    Modern minimal design with glowing arcs
    """
    def __init__(self, size=70, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._read_speed = 0.0
        self._write_speed = 0.0
        theme_manager.theme_changed.connect(self.update)

    def set_speeds(self, read_bps: float, write_bps: float):
        self._read_speed = max(0, read_bps)
        self._write_speed = max(0, write_bps)
        self.update()

    def _format_speed(self, bps: float) -> str:
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.1f}"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f}"
        elif bps >= 1024:
            return f"{bps / 1024:.0f}"
        return "0"

    def _get_speed_unit(self, bps: float) -> str:
        if bps >= 1_073_741_824:
            return "GB/s"
        elif bps >= 1_048_576:
            return "MB/s"
        return "KB/s"

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        center = self._size / 2
        radius = (self._size - 12) / 2

        # Background track
        bg_rect = QRectF(6, 6, self._size - 12, self._size - 12)
        painter.setPen(QPen(QColor(c.BG_HOVER), 6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(bg_rect.toRect(), 0 * 16, 360 * 16)

        # Read arc (top, green) - 180° to 0°
        read_fraction = min(1.0, self._read_speed / 250_000_000)  # 250MB/s = full
        read_angle = int(read_fraction * 180)
        if read_angle > 0:
            read_color = QColor(c.ACCENT_GREEN)
            painter.setPen(QPen(read_color, 5, cap=Qt.PenCapStyle.RoundCap))
            painter.drawArc(bg_rect.toRect(), 180 * 16, -read_angle * 16)

        # Write arc (bottom, blue) - 0° to 180°
        write_fraction = min(1.0, self._write_speed / 250_000_000)
        write_angle = int(write_fraction * 180)
        if write_angle > 0:
            write_color = QColor(c.ACCENT_BLUE)
            painter.setPen(QPen(write_color, 5, cap=Qt.PenCapStyle.RoundCap))
            painter.drawArc(bg_rect.toRect(), 0 * 16, write_angle * 16)

        # Center: Read speed
        read_text = self._format_speed(self._read_speed)
        read_unit = self._get_speed_unit(self._read_speed)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(c.ACCENT_GREEN))
        fm = painter.fontMetrics()
        painter.drawText(int(center - fm.horizontalAdvance(read_text) / 2), int(center - 2), read_text)

        # Center: Write speed (smaller, below)
        write_text = self._format_speed(self._write_speed)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(c.ACCENT_BLUE))
        painter.drawText(int(center - fm.horizontalAdvance(write_text) / 2), int(center + 12), write_text)

        painter.end()


class TemperatureBar(QWidget):
    """
    Temperature indicator with color-coded bar
    Minimal design with gradient fill
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp = 0
        self.setFixedHeight(28)

    def set_temperature(self, temp_c: float):
        self._temp = max(0, min(120, temp_c))
        self.update()

    def _get_temp_color(self) -> QColor:
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

        bar_height = 6
        bar_y = 10
        bar_width = self.width() - 80
        bar_x = 50

        # Background track
        painter.setBrush(QColor(c.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_width), bar_height, 3, 3)

        # Temperature fill with gradient
        fill_width = (self._temp / 100) * bar_width
        temp_color = self._get_temp_color()

        # Gradient fill for better look
        fill_gradient = QLinearGradient(bar_x, 0, bar_x + fill_width, 0)
        fill_gradient.setColorAt(0, temp_color)
        fill_gradient.setColorAt(1, QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 180))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(fill_width), bar_height, 3, 3)

        # Temperature label
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor(c.TEXT_PRIMARY))
        painter.drawText(0, int(bar_y + 13), f"{self._temp:.0f}°C")

        # Status dot
        dot_x = bar_x + bar_width + 10
        glow_color = QColor(temp_color.red(), temp_color.green(), temp_color.blue(), 100)
        painter.setBrush(glow_color)
        painter.drawEllipse(int(dot_x), int(bar_y - 1), 12, 12)
        painter.setBrush(temp_color)
        painter.drawEllipse(int(dot_x + 1), int(bar_y), 10, 10)

        painter.end()


class DiskCard(GlassCard):
    """
    Individual disk card with modern glassmorphism design
    Shows: name, usage percentage, space, speed, temperature
    """
    def __init__(self, drive_info: dict, parent=None):
        super().__init__(parent=parent)
        self._drive_info = drive_info
        self._temperature = 0
        self._read_speed = 0.0
        self._write_speed = 0.0
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        c = theme_manager.colors

        # Base style for glass card
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        # Determine glow color based on usage
        usage_pct = self._drive_info.get('percent', 0)
        if usage_pct >= 90:
            glow = QColor(c.ACCENT_RED)
        elif usage_pct >= 75:
            glow = QColor(c.ACCENT_ORANGE)
        else:
            glow = QColor(c.ACCENT_BLUE)
        self.set_glow_color(glow)
        self.set_intensity(0.6)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(14)
        self.setLayout(main_layout)

        # === TOP ROW: Icon + Info + Percentage ===
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Drive icon (custom painted)
        icon_widget = QWidget()
        icon_widget.setFixedSize(44, 44)
        icon_layout = QVBoxLayout(icon_widget)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label = QLabel("💾")
        icon_label.setFont(QFont("Segoe UI", 22))
        icon_layout.addWidget(icon_label)
        top_row.addWidget(icon_widget)

        # Drive info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        drive_letter = self._drive_info.get('device', 'Unknown')[:2]
        mountpoint = self._drive_info.get('mountpoint', '')
        fs_type = self._drive_info.get('fstype', 'Unknown')

        name_label = QLabel(f"{drive_letter} {mountpoint}" if mountpoint else drive_letter)
        name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        info_layout.addWidget(name_label)

        fs_label = QLabel(f"{fs_type} • {self._format_size(self._drive_info.get('total', 0))}")
        fs_label.setFont(QFont("Segoe UI", 10))
        fs_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        info_layout.addWidget(fs_label)

        top_row.addLayout(info_layout)
        top_row.addStretch()

        # Usage percentage (large, bold)
        self._pct_label = QLabel(f"{usage_pct:.0f}%")
        self._pct_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self._pct_label.setStyleSheet(f"color: {self._get_usage_color(usage_pct)}; background: transparent;")
        top_row.addWidget(self._pct_label)

        main_layout.addLayout(top_row)

        # === USAGE BAR ===
        self._usage_bar = QProgressBar()
        self._usage_bar.setValue(int(usage_pct))
        self._usage_bar.setFixedHeight(6)
        self._usage_bar.setTextVisible(False)
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {c.BG_HOVER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {self._get_usage_color(usage_pct)};
                border-radius: 3px;
            }}
        """)
        main_layout.addWidget(self._usage_bar)

        # === SPACE INFO ===
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

        # === BOTTOM ROW: Speed + Temperature ===
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)

        # Speed section
        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(6)

        speed_header = QLabel("SPEED")
        speed_header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        speed_header.setStyleSheet(f"color: {c.TEXT_MUTED}; letter-spacing: 1px; background: transparent;")
        speed_layout.addWidget(speed_header)

        speed_content = QHBoxLayout()
        speed_content.setSpacing(12)

        self._speed_gauge = SpeedGauge(size=56)
        speed_content.addWidget(self._speed_gauge)

        speed_labels = QVBoxLayout()
        speed_labels.setSpacing(4)

        self._read_label = QLabel("R: -- MB/s")
        self._read_label.setFont(QFont("Segoe UI", 9))
        self._read_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; background: transparent;")
        speed_labels.addWidget(self._read_label)

        self._write_label = QLabel("W: -- MB/s")
        self._write_label.setFont(QFont("Segoe UI", 9))
        self._write_label.setStyleSheet(f"color: {c.ACCENT_BLUE}; background: transparent;")
        speed_labels.addWidget(self._write_label)

        speed_content.addLayout(speed_labels)
        speed_layout.addLayout(speed_content)
        bottom_row.addLayout(speed_layout)

        bottom_row.addStretch()

        # Temperature section
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(6)

        temp_header = QLabel("TEMP")
        temp_header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        temp_header.setStyleSheet(f"color: {c.TEXT_MUTED}; letter-spacing: 1px; background: transparent;")
        temp_layout.addWidget(temp_header)

        self._temp_widget = TemperatureBar()
        self._temp_widget.setFixedWidth(130)
        temp_layout.addWidget(self._temp_widget)

        bottom_row.addLayout(temp_layout)

        main_layout.addLayout(bottom_row)

    def _get_usage_color(self, pct: float) -> str:
        c = theme_manager.colors
        if pct >= 90:
            return c.ACCENT_RED
        elif pct >= 75:
            return c.ACCENT_ORANGE
        return c.ACCENT_GREEN

    def _format_size(self, bytes_val: float) -> str:
        tb = bytes_val / (1024**4)
        if tb >= 1:
            return f"{tb:.1f} TB"
        gb = bytes_val / (1024**3)
        if gb >= 1:
            return f"{gb:.1f} GB"
        return f"{bytes_val / (1024**2):.0f} MB"

    def _format_speed(self, bps: float) -> str:
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.1f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def update_space(self, used: float, free: float, total: float, percent: float):
        self._drive_info.update({'used': used, 'free': free, 'total': total, 'percent': percent})

        self._usage_bar.setValue(int(percent))
        self._pct_label.setText(f"{percent:.0f}%")
        self._pct_label.setStyleSheet(f"color: {self._get_usage_color(percent)}; background: transparent;")
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme_manager.colors.BG_HOVER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {self._get_usage_color(percent)};
                border-radius: 3px;
            }}
        """)

        # Update glow color based on usage
        if percent >= 90:
            self.set_glow_color(QColor(theme_manager.colors.ACCENT_RED))
        elif percent >= 75:
            self.set_glow_color(QColor(theme_manager.colors.ACCENT_ORANGE))
        else:
            self.set_glow_color(QColor(theme_manager.colors.ACCENT_BLUE))

    def update_speeds(self, read_bps: float, write_bps: float):
        self._read_speed = read_bps
        self._write_speed = write_bps
        self._speed_gauge.set_speeds(read_bps, write_bps)
        self._read_label.setText(f"R: {self._format_speed(read_bps)}")
        self._write_label.setText(f"W: {self._format_speed(write_bps)}")

    def update_temperature(self, temp_c: float):
        self._temperature = temp_c
        self._temp_widget.set_temperature(temp_c)

    def _apply_theme(self):
        pass  # GlassCard handles paintEvent


class DisksView(QWidget, ScaleMixin):
    """
    Disk monitoring view with modern glassmorphism cards
    Real-time updates via data collector
    """
    disk_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disk_cards = {}
        self._temps = {}
        self._data_collector = None
        self._pending_update = False
        self._cards_layout = None
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._on_update)
        self._update_timer.start(2000)  # 2 second interval
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        c = theme_manager.colors
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(S.px(20))
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self.setLayout(main_layout)

        # Header
        header = QLabel("Disks")
        header.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        header.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(header)

        # Cards container widget (no scroll area)
        cards_widget = QWidget()
        cards_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cards_widget.setStyleSheet("background: transparent;")

        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(S.px(16))
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_widget.setLayout(self._cards_layout)

        main_layout.addWidget(cards_widget, stretch=1)

        self._scan_disks()

    def set_data_collector(self, collector):
        self._data_collector = collector
        if collector:
            collector.data_ready.connect(self._on_data_ready)

    def _on_data_ready(self, data: dict):
        if 'disk' not in data:
            return
        disk_data = data['disk']

        partitions = disk_data.get('partitions', [])
        partition_io = disk_data.get('partition_io', {})

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
                card.update_space(
                    part.get('used', 0),
                    part.get('free', 0),
                    part.get('total', 0),
                    part.get('percent', 0)
                )
                if mountpoint and mountpoint in io_by_mountpoint:
                    io = io_by_mountpoint[mountpoint]
                    card.update_speeds(io.get('read_rate', 0), io.get('write_rate', 0))
                else:
                    card.update_speeds(disk_data.get('read_rate', 0), disk_data.get('write_rate', 0))

        self._collect_temperature()

    def _on_update(self):
        self._collect_temperature()

    def _collect_temperature(self):
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
                            for card in self._disk_cards.values():
                                if card._temperature == 0:
                                    card.update_temperature(temp)
                                    break
                except (OSError, RuntimeError):
                    pass
        except Exception:
            pass

    def _scan_disks(self):
        try:
            partitions = psutil.disk_partitions(all=False)
            current_devices = set()

            for partition in partitions:
                if not partition.fstype or partition.fstype == '':
                    continue

                if platform.system() == 'Windows':
                    if partition.opts and 'cdrom' in partition.opts.lower():
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
                        self._disk_cards[device].update_space(
                            usage.used, usage.free, usage.total, usage.percent
                        )
                    else:
                        card = DiskCard(drive_info)
                        self._disk_cards[device] = card
                        self._cards_layout.addWidget(card)

                except (PermissionError, OSError):
                    continue

            removed = set(self._disk_cards.keys()) - current_devices
            for device in removed:
                card = self._disk_cards.pop(device)
                card.deleteLater()

        except Exception as e:
            print(f"Disk scan error: {e}")

    def _on_theme_changed(self, theme_name: str):
        self._scan_disks()

    def on_scale_changed(self, factor: float):
        self.update()

    def update_data(self, data):
        self._on_data_ready(data)