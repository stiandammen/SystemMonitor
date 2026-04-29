"""
Disks View - Disk monitoring with detailed drive information
"""
import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QProgressBar, QPushButton, QDialog
)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient


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
    'accent_red': '#ef4444',
}


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


class DisksView(QWidget):
    """Disk monitoring view with per-drive breakdown"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_drives = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup view UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Page header
        header = self._create_header()
        main_layout.addWidget(header)

        # Scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_primary']};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)

        content = QWidget()
        content.setMaximumWidth(1200)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(24, 16, 24, 24)
        self._content_layout.setSpacing(16)
        content.setLayout(self._content_layout)

        self._scroll_area.setWidget(content)
        main_layout.addWidget(self._scroll_area, stretch=1)

        # Timer for storage refresh
        self._storage_timer = QTimer(self)
        self._storage_timer.timeout.connect(self._update_drives)
        self._storage_timer.start(5000)

    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: #111820; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 0, 24, 0)
        header.setLayout(layout)

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addStretch()

        title = QLabel("Disks")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        left.addWidget(title)

        subtitle = QLabel("Storage devices and drives")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']};")
        left.addWidget(subtitle)

        left.addStretch()
        layout.addLayout(left)
        layout.addStretch()

        return header

    def _get_storage_color(self, pct):
        if pct > 90:
            return COLORS['accent_red']
        elif pct > 75:
            return COLORS['accent_orange']
        return COLORS['accent_green']

    def _update_drives(self):
        """Update drive cards"""
        # Clear existing
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

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

            if vol_name:
                name_text = f"{vol_name} ({mountpoint})"
            else:
                name_text = mountpoint if mountpoint else drive_letter

            name_lbl = QLabel(name_text)
            name_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            info_layout.addWidget(name_lbl)

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

            # Right percentage box
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

            self._content_layout.addWidget(drive_card)

        self._content_layout.addStretch()

    def update_data(self, data):
        """Update view with new data"""
        self._update_drives()
