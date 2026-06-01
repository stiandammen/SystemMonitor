"""
Storage Widgets - Professional storage monitoring UI components
Enterprise-grade design with real-time graphs and metrics
"""
import math
from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin


def c():
    """Access theme colors - shorthand for cleaner code"""
    return theme_manager.colors


class LiveGraphWidget(QWidget):
    """
    Smooth live-updating line/area graph for read/write speeds.
    Professional gradient fills with glow effects.
    """
    def __init__(self, max_points: int = 60, parent=None):
        super().__init__(parent)
        self._max_points = max_points
        self._read_history: List[float] = []
        self._write_history: List[float] = []
        self._read_max = 100_000_000  # Normalize to 100 MB/s full scale
        self.setMinimumHeight(S.px(70))
        self.setMaximumHeight(S.px(90))
        theme_manager.theme_changed.connect(self.update)

    def set_speeds(self, read_bps: float, write_bps: float):
        """Add new speed data point"""
        self._read_history.append(max(0, read_bps))
        self._write_history.append(max(0, write_bps))

        if len(self._read_history) > self._max_points:
            self._read_history.pop(0)
        if len(self._write_history) > self._max_points:
            self._write_history.pop(0)

        current_max = max(
            max(self._read_history) if self._read_history else 1,
            max(self._write_history) if self._write_history else 1,
            1024 * 1024
        )
        if current_max > self._read_max * 1.2:
            self._read_max = current_max * 1.5
        elif len(self._read_history) > 10 and current_max < self._read_max * 0.5:
            self._read_max = max(current_max * 2, 100_000_000)

        self.update()

    def clear(self):
        """Clear all history"""
        self._read_history.clear()
        self._write_history.clear()
        self.update()

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to human readable"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            painter.end()
            return

        # Background
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 4, 4)

        if not self._read_history and not self._write_history:
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(colors.TEXT_MUTED))
            painter.drawText(w // 2 - 25, h // 2 + 4, "Waiting for data...")
            painter.end()
            return

        # Draw grid lines
        painter.setPen(QPen(QColor(colors.BORDER), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = h * i // 4
            painter.drawLine(0, y, w, y)

        step_w = w / self._max_points

        # Draw read line (green)
        if len(self._read_history) > 1:
            self._draw_graph(painter, self._read_history, step_w, h, colors.ACCENT_GREEN, True)

        # Draw write line (blue)
        if len(self._write_history) > 1:
            self._draw_graph(painter, self._write_history, step_w, h, colors.ACCENT_BLUE, False)

        # Current values in corner
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        read_text = f"↓ {self._format_speed(self._read_history[-1] if self._read_history else 0)}"
        write_text = f"↑ {self._format_speed(self._write_history[-1] if self._write_history else 0)}"

        painter.setPen(QColor(colors.ACCENT_GREEN))
        painter.drawText(8, 14, read_text)
        painter.setPen(QColor(colors.ACCENT_BLUE))
        painter.drawText(8, 28, write_text)

        painter.end()

    def _draw_graph(self, painter: QPainter, points: List[float], step_w: float, h: float, color: str, is_read: bool):
        """Draw a smooth graph line with proper gradient fill"""
        if len(points) < 2:
            return

        # Build path points
        path_points = []
        for i, val in enumerate(points):
            x = i * step_w
            y = h - (val / self._read_max) * (h - 8)
            y = max(4, min(h - 4, y))
            path_points.append((x, y))

        # Gradient fill
        fill_path = QPainterPath()
        fill_path.moveTo(0, h)
        for x, y in path_points:
            fill_path.lineTo(x, y)
        fill_path.lineTo((len(points) - 1) * step_w, h)
        fill_path.closeSubpath()

        fill_color = QColor(color)
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, fill_color.lighter(130))
        gradient.setColorAt(0.5, fill_color)
        gradient.setColorAt(1, fill_color)
        painter.setOpacity(0.25 if not is_read else 0.3)
        painter.fillPath(fill_path, QColor(color))
        painter.setOpacity(1.0)

        # Draw line
        line_path = QPainterPath()
        for i, (x, y) in enumerate(path_points):
            if i == 0:
                line_path.moveTo(x, y)
            else:
                line_path.lineTo(x, y)

        painter.setPen(QPen(QColor(color), 2))
        painter.drawPath(line_path)


class TemperatureGauge(QWidget):
    """
    Circular temperature gauge with color-coded status.
    Shows temperature with normal/warning/critical zones.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp: float = 0
        self.setFixedSize(S.px(64), S.px(64))
        theme_manager.theme_changed.connect(self.update)

    def set_temperature(self, temp_c: float):
        """Set temperature in Celsius"""
        self._temp = max(0, min(120, temp_c))
        self.update()

    def _get_status_color(self) -> QColor:
        colors = c()
        if self._temp >= 85:
            return QColor(colors.ACCENT_RED)
        elif self._temp >= 70:
            return QColor(colors.ACCENT_ORANGE)
        return QColor(colors.ACCENT_GREEN)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        size = min(self.width(), self.height())
        center = size / 2
        radius = size / 2 - 6

        # Background arc
        bg_rect = QRectF(center - radius, center - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor(colors.BG_HOVER), 5))
        painter.drawArc(bg_rect.toRect(), 135 * 16, 270 * 16)

        # Temperature arc
        if self._temp > 0:
            temp_angle = min(270, (self._temp / 100) * 270)
            status_color = self._get_status_color()
            painter.setPen(QPen(status_color, 5, cap=Qt.PenCapStyle.RoundCap))
            painter.drawArc(bg_rect.toRect(), 135 * 16, -int(temp_angle) * 16)

        # Temperature text
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        temp_text = f"{self._temp:.0f}°"
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(temp_text)
        painter.drawText(int(center - text_w / 2), int(center + 4), temp_text)

        painter.end()


class TemperatureBar(QWidget):
    """
    Linear temperature bar with color-coded status.
    Clean horizontal bar with gradient fill.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp: float = 0
        self.setFixedHeight(S.px(28))
        theme_manager.theme_changed.connect(self.update)

    def set_temperature(self, temp_c: float):
        """Set temperature in Celsius"""
        self._temp = max(0, min(120, temp_c))
        self.update()

    def _get_status_color(self) -> QColor:
        colors = c()
        if self._temp >= 85:
            return QColor(colors.ACCENT_RED)
        elif self._temp >= 70:
            return QColor(colors.ACCENT_ORANGE)
        return QColor(colors.ACCENT_GREEN)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = c()

        bar_h = 6
        bar_y = 11
        bar_w = self.width() - 50
        bar_x = 44

        # Background
        painter.setBrush(QColor(colors.BG_HOVER))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(bar_x), int(bar_y), int(bar_w), bar_h, 3, 3)

        # Fill
        fill_w = int((self._temp / 100) * bar_w)
        if fill_w > 0:
            status_color = self._get_status_color()
            painter.setBrush(status_color)
            painter.drawRoundedRect(int(bar_x), int(bar_y), fill_w, bar_h, 3, 3)

        # Label
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(colors.TEXT_PRIMARY))
        painter.drawText(0, int(bar_y + 14), f"{self._temp:.0f}°C")

        # Status dot
        icon_x = bar_x + bar_w + 8
        status_color = self._get_status_color()
        painter.setBrush(status_color)
        painter.drawEllipse(int(icon_x), int(bar_y), 8, 8)

        painter.end()


class SMARTStatusWidget(QWidget):
    """
    Widget displaying SMART status information.
    Shows health, wear level, and other SMART attributes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._smart_data: Optional[Dict] = None
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build SMART status widget layout"""
        colors = c()

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Title
        title = QLabel("SMART Health")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        main_layout.addWidget(title)

        # Health status
        self._health_label = QLabel("Unknown")
        self._health_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        main_layout.addWidget(self._health_label)

        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)
        main_layout.addLayout(stats_layout)

        self._create_stat_item("Power On", "h", "power_on_hours", stats_layout)
        self._create_stat_item("Cycles", "", "power_cycle_count", stats_layout)
        self._create_stat_item("Bad Sectors", "", "bad_sectors", stats_layout)
        self._create_stat_item("Wear Level", "%", "wear_level", stats_layout)

    def _create_stat_item(self, label: str, unit: str, key: str, layout: QGridLayout):
        """Create a stat display item"""
        colors = c()

        label_w = QLabel(label)
        label_w.setFont(QFont("Segoe UI", 8))
        label_w.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")

        value_w = QLabel("--" if unit else "")
        value_w.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        value_w.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        value_w.setObjectName(f"smart_{key}")

        row = layout.rowCount()
        layout.addWidget(label_w, row, 0)
        layout.addWidget(value_w, row, 1)

    def set_smart_data(self, smart_data: Optional[Dict]):
        """Update SMART data"""
        self._smart_data = smart_data
        self._update_display()

    def _update_display(self):
        """Update SMART data display"""
        colors = c()

        if not self._smart_data:
            self._health_label.setText("N/A")
            self._health_label.setStyleSheet(f"color: {colors.TEXT_MUTED};")
            return

        health = self._smart_data.get('health', 'Unknown')
        self._health_label.setText(health)

        if health in ['OK', 'Healthy', 'Good']:
            health_color = colors.ACCENT_GREEN
        elif health in ['Warning', 'Caution']:
            health_color = colors.ACCENT_ORANGE
        else:
            health_color = colors.TEXT_SECONDARY

        self._health_label.setStyleSheet(f"color: {health_color};")

        stat_mappings = [
            ('power_on_hours', 'h'),
            ('power_cycle_count', ''),
            ('bad_sectors', ''),
            ('wear_level', '%'),
        ]

        for key, unit in stat_mappings:
            value = self._smart_data.get(key)
            label = self.findChild(QLabel, f"smart_{key}")
            if label:
                if value is not None:
                    label.setText(f"{value}{unit}")
                else:
                    label.setText("--")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        self._setup_ui()
        self._update_display()


class StorageDiskCard(QFrame):
    """
    Professional individual disk card showing all disk metrics.
    Features: space usage, speed gauges, temperature, and SMART data.
    """
    disk_selected = pyqtSignal(str)

    def __init__(self, disk_info: Dict, parent=None):
        super().__init__(parent)
        self._disk_info = disk_info
        self._temperature = 0
        self._read_speed = 0.0
        self._write_speed = 0.0
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build the disk card layout"""
        colors = c()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(S.px(12))
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self.setLayout(main_layout)

        # Header row: Disk icon + name + type badge + usage %
        header_row = QHBoxLayout()
        header_row.setSpacing(S.px(12))

        # Disk type icon with qtawesome
        icon_label = QLabel()
        icon_name = self._get_disk_icon_name()
        try:
            icon_color = self._get_type_color()
            icon = qta.icon(icon_name, color=icon_color, scale=1.2)
            icon_label.setPixmap(icon.pixmap(S.px(28), S.px(28)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        header_row.addWidget(icon_label)

        # Name and details
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        name_label = QLabel(self._get_disk_title())
        name_label.setFont(QFont("Segoe UI", S.font_pt(13), QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        name_label.setObjectName("disk_name_label")
        name_layout.addWidget(name_label)

        # Model row
        model_row = QHBoxLayout()
        model_row.setSpacing(S.px(8))

        type_badge = QLabel(self._disk_info.get('disk_type', 'Unknown'))
        type_badge.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
        type_color = self._get_type_color()
        type_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {type_color};
                color: white;
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        model_row.addWidget(type_badge)

        model_label = QLabel(self._disk_info.get('model', 'Unknown Model'))
        model_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        model_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        model_label.setObjectName("model_label")
        model_row.addWidget(model_label)

        model_row.addStretch()
        name_layout.addLayout(model_row)

        header_row.addLayout(name_layout, stretch=1)
        header_row.addStretch()

        # Usage percentage (large)
        self._pct_label = QLabel(f"{self._get_usage_percent():.0f}%")
        self._pct_label.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        self._pct_label.setStyleSheet(f"color: {self._get_usage_color()}; background: transparent;")
        self._pct_label.setObjectName("pct_label")
        self._pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(self._pct_label)

        main_layout.addLayout(header_row)

        # Progress bar for usage
        self._usage_bar = QProgressBar()
        self._usage_bar.setValue(int(self._get_usage_percent()))
        self._usage_bar.setFixedHeight(S.px(6))
        self._usage_bar.setTextVisible(False)
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_HOVER};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self._get_usage_color()};
                border-radius: 3px;
            }}
        """)
        self._usage_bar.setObjectName("usage_bar")
        main_layout.addWidget(self._usage_bar)

        # Space info row
        space_row = QHBoxLayout()
        used_gb = self._disk_info.get('used', 0) / (1024**3)
        free_gb = self._disk_info.get('free', 0) / (1024**3)
        total_tb = self._disk_info.get('total', 0) / (1024**4)

        if total_tb >= 1:
            total_label_text = f"of {total_tb:.1f} TB"
        else:
            total_label_text = f"of {self._disk_info.get('total', 0) / (1024**3):.0f} GB"

        used_label = QLabel(f"Used: {used_gb:.1f} GB {total_label_text}")
        used_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        used_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        space_row.addWidget(used_label)

        space_row.addStretch()

        free_label = QLabel(f"Free: {free_gb:.1f} GB")
        free_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        free_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        space_row.addWidget(free_label)

        main_layout.addLayout(space_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {colors.BORDER}; max-height: 1px;")
        main_layout.addWidget(divider)

        # Speed + Temperature row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(S.px(16))

        # Read/Write speed section
        speed_section = QVBoxLayout()
        speed_section.setSpacing(4)

        speed_header = QLabel("Transfer Speed")
        speed_header.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        speed_header.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        speed_section.addWidget(speed_header)

        self._read_label = QLabel("↓ -- MB/s")
        self._read_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._read_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        speed_section.addWidget(self._read_label)

        self._write_label = QLabel("↑ -- MB/s")
        self._write_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._write_label.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        speed_section.addWidget(self._write_label)

        metrics_row.addLayout(speed_section)

        metrics_row.addStretch()

        # Temperature section
        temp_section = QVBoxLayout()
        temp_section.setSpacing(4)

        temp_header = QLabel("Temperature")
        temp_header.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        temp_header.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        temp_section.addWidget(temp_header)

        self._temp_bar = TemperatureBar()
        temp_section.addWidget(self._temp_bar)

        metrics_row.addLayout(temp_section)

        main_layout.addLayout(metrics_row)

        # Bottom stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(S.px(16))

        # Mount point
        mount_text = self._disk_info.get('mountpoint', 'N/A')
        mount_label = QLabel(f"Mount: {mount_text}")
        mount_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        mount_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        stats_row.addWidget(mount_label)

        stats_row.addStretch()

        # File system
        fs_label = QLabel(f"FS: {self._disk_info.get('fstype', 'Unknown')}")
        fs_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        fs_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        stats_row.addWidget(fs_label)

        main_layout.addLayout(stats_row)

    def _get_disk_icon_name(self) -> str:
        """Get qtawesome icon name for disk type"""
        disk_type = self._disk_info.get('disk_type', 'Unknown')
        if disk_type == 'NVMe':
            return 'mdi.expansion'
        elif disk_type == 'SSD':
            return 'mdi.thumb-up'
        return 'mdi.harddisk'

    def _get_disk_title(self) -> str:
        """Get disk display title"""
        device = self._disk_info.get('device', 'Unknown')
        name = self._disk_info.get('name', device)
        if name and name != device:
            return name
        if device:
            return f"Disk {device[:2]}"
        return "Unknown Disk"

    def _get_type_color(self) -> str:
        """Get color for disk type badge"""
        colors = c()
        disk_type = self._disk_info.get('disk_type', 'Unknown')
        if disk_type == 'NVMe':
            return colors.ACCENT_PURPLE
        elif disk_type == 'SSD':
            return colors.ACCENT_BLUE
        elif disk_type == 'HDD':
            return colors.ACCENT_ORANGE
        return colors.TEXT_MUTED

    def _get_usage_percent(self) -> float:
        """Get usage percentage"""
        return self._disk_info.get('percent', 0)

    def _get_usage_color(self) -> str:
        """Get color for usage percentage"""
        colors = c()
        pct = self._get_usage_percent()
        if pct >= 90:
            return colors.ACCENT_RED
        elif pct >= 75:
            return colors.ACCENT_ORANGE
        return colors.ACCENT_GREEN

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to MB/s or GB/s"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def update_disk_info(self, disk_info: Dict):
        """Update all disk information"""
        self._disk_info = disk_info
        self.update()

    def update_speeds(self, read_bps: float, write_bps: float):
        """Update read/write speeds"""
        self._read_speed = read_bps
        self._write_speed = write_bps
        self._read_label.setText(f"↓ {self._format_speed(read_bps)}")
        self._write_label.setText(f"↑ {self._format_speed(write_bps)}")

    def update_temperature(self, temp_c: float):
        """Update temperature display"""
        self._temperature = temp_c
        self._temp_bar.set_temperature(temp_c)

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        self._setup_ui()


class StorageOverviewCard(QFrame):
    """
    Compact storage overview card for dashboard.
    Shows total usage and aggregate speeds with professional styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._total_used = 0
        self._total_free = 0
        self._total_size = 0
        self._read_speed = 0.0
        self._write_speed = 0.0
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build overview card layout"""
        colors = c()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: 12px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(S.px(10))
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        self.setLayout(main_layout)

        # Title row with icon
        title_row = QHBoxLayout()
        title_row.setSpacing(S.px(8))

        # Storage icon
        icon_label = QLabel()
        try:
            icon = qta.icon('mdi.database', color=colors.ACCENT_BLUE, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(18), S.px(18)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        title_row.addWidget(icon_label)

        title = QLabel("Storage Overview")
        title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_row.addWidget(title)

        title_row.addStretch()
        main_layout.addLayout(title_row)

        # Usage bar
        self._usage_bar = QProgressBar()
        self._usage_bar.setFixedHeight(S.px(10))
        self._usage_bar.setTextVisible(False)
        self._usage_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_HOVER};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {colors.ACCENT_BLUE};
                border-radius: 5px;
            }}
        """)
        main_layout.addWidget(self._usage_bar)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(S.px(16))

        self._used_label = QLabel("Used: -- GB")
        self._used_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._used_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        stats_row.addWidget(self._used_label)

        stats_row.addStretch()

        self._free_label = QLabel("Free: -- GB")
        self._free_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._free_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        stats_row.addWidget(self._free_label)

        main_layout.addLayout(stats_row)

        # Speed row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(S.px(16))

        self._read_label = QLabel("↓ -- MB/s")
        self._read_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._read_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        speed_row.addWidget(self._read_label)

        self._write_label = QLabel("↑ -- MB/s")
        self._write_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._write_label.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        speed_row.addWidget(self._write_label)

        speed_row.addStretch()
        main_layout.addLayout(speed_row)

    def set_storage_info(self, total_size: float, total_used: float, total_free: float,
                         read_speed: float, write_speed: float):
        """Update storage overview"""
        self._total_size = total_size
        self._total_used = total_used
        self._total_free = total_free
        self._read_speed = read_speed
        self._write_speed = write_speed

        # Update progress bar
        if total_size > 0:
            percent = (total_used / total_size) * 100
            self._usage_bar.setValue(int(percent))

        # Update labels
        used_gb = total_used / (1024**3)
        free_gb = total_free / (1024**3)

        self._used_label.setText(f"Used: {used_gb:.1f} GB")
        self._free_label.setText(f"Free: {free_gb:.1f} GB")
        self._read_label.setText(f"↓ {self._format_speed(read_speed)}")
        self._write_label.setText(f"↑ {self._format_speed(write_speed)}")

    def _format_speed(self, bps: float) -> str:
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def _on_theme_changed(self, theme_name: str):
        """Re-apply theme"""
        self._setup_ui()
        self.set_storage_info(self._total_size, self._total_used, self._total_free,
                             self._read_speed, self._write_speed)


class StatTile(QFrame):
    """
    Compact statistic tile for displaying key metrics.
    Professional glassmorphism style with icon and value.
    """
    def __init__(self, label: str, value: str = "--", accent: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = value
        colors = c()
        self._accent = accent or colors.ACCENT_BLUE
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build stat tile layout"""
        colors = c()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: 1px solid {colors.BORDER};
                border-radius: 10px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(S.px(12), S.px(10), S.px(12), S.px(10))
        self.setLayout(main_layout)

        # Value with accent color
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        self._value_label.setObjectName("value_label")
        main_layout.addWidget(self._value_label)

        # Label
        label_text = QLabel(self._label)
        label_text.setFont(QFont("Segoe UI", S.font_pt(9)))
        label_text.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        main_layout.addWidget(label_text)

    def set_value(self, value: str):
        """Update the displayed value"""
        self._value = value
        label = self.findChild(QLabel, "value_label")
        if label:
            label.setText(value)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply theme"""
        self._setup_ui()
        self.set_value(self._value)
