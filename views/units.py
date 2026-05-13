"""
NetworkSpy View - Professional Device Discovery & Monitoring System
Enterprise-grade network device scanner with live monitoring
"""
import sys
import os

if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTextEdit,
    QLineEdit, QComboBox, QGridLayout, QProgressBar, QStackedWidget,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPointF, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QLinearGradient, QBrush, QIcon,
    QPaintEvent, QMouseEvent, QPalette, QRadialGradient, QGradient
)
from functools import partial
import traceback

import qtawesome as qta
from typing import Dict, List, Optional, Tuple, Any

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from config import settings
from data.device_collector import DeviceCollector, DeviceMonitorWorker
from core.discovery.classification import DeviceClassifier, DeviceType


# ═══════════════════════════════════════════════════════
# DESIGN SYSTEM — CYBER TERMINAL
# ═══════════════════════════════════════════════════════
G = {
    "bg0": "#030609",
    "bg1": "#060D0F",
    "bg2": "#0A1512",
    "surface": "#0D1B1E",
    "panel": "#0F1F22",
    "border": "#0E3028",
    "border2": "#1A4A38",
    "green": "#00FF88",
    "green2": "#00CC6A",
    "green3": "#009950",
    "greenDim": "#003D20",
    "cyan": "#00FFE5",
    "cyanDim": "#004D45",
    "amber": "#FFB800",
    "amberDim": "#3D2C00",
    "red": "#FF3B5C",
    "redDim": "#3D0012",
    "blue": "#00AAFF",
    "blueDim": "#001F3D",
    "purple": "#CC44FF",
    "purpleDim": "#2A0040",
    "text": "#A8FFC8",
    "textDim": "#3D6B50",
    "mono": "'JetBrains Mono','Fira Code','Cascadia Code',monospace",
}


# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════
def ping_color(ms: int) -> str:
    if ms < 10:
        return G["green"]
    elif ms < 30:
        return G["amber"]
    else:
        return G["red"]


def mac_to_hex_display(mac: str) -> str:
    """Convert MAC address to hex display format"""
    if not mac or mac == "N/A":
        return "N/A"
    parts = mac.split(":")
    if len(parts) != 6:
        return mac
    return " ".join([f"0x{p}" for p in parts])


def get_current_time() -> str:
    """Get current time formatted for Norwegian locale"""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


# ═══════════════════════════════════════════════════════
# ICON BUTTON
# ═══════════════════════════════════════════════════════
class IconButton(QPushButton):
    """Minimal icon button with transparent background"""
    def __init__(self, icon_name: str, color: str = G["textDim"], size: int = 18, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._color = color
        self._size = size
        self.setFixedSize(size + 8, size + 8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_icon()

    def _setup_icon(self):
        try:
            icon = qta.icon(self._icon_name, color=self._color)
            self.setIcon(icon)
            self.setIconSize(QSize(self._size, self._size))
        except Exception:
            pass

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {G['border2']};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {G['surface']};
                border-color: {G['green']};
            }}
        """)


# ═══════════════════════════════════════════════════════
# SIGNAL BARS WIDGET
# ═══════════════════════════════════════════════════════
class SigBars(QWidget):
    """Signal strength bars indicator"""
    def __init__(self, ms: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._ms = ms
        self.setFixedSize(24, 20)

    def set_ping(self, ms: int):
        self._ms = ms
        self.update()

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        level = 5 if self._ms < 5 else 4 if self._ms < 15 else 3 if self._ms < 30 else 2 if self._ms < 60 else 1
        color = ping_color(self._ms)

        for i in range(5):
            bar_height = 3 + (i + 1) * 2.5
            x = i * 5
            y = 20 - bar_height

            if i < level:
                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.setBrush(QBrush(QColor(G["border2"])))
                painter.setPen(Qt.PenStyle.NoPen)

            painter.drawRoundedRect(x, int(y), 3, int(bar_height), 1, 1)


# ═══════════════════════════════════════════════════════
# GLOWING DOT
# ═══════════════════════════════════════════════════════
class GlowDot(QWidget):
    """Animated glowing status dot"""
    def __init__(self, color: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(10, 10)

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QRadialGradient(self.width() / 2, self.height() / 2, 8)
        c = QColor(self._color)
        gradient.setColorAt(0, c)
        gradient.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 6, 6)


# ═══════════════════════════════════════════════════════
# THREAT BADGE
# ═══════════════════════════════════════════════════════
class ThreatBadge(QFrame):
    """Threat level indicator badge"""
    def __init__(self, level: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._level = level
        self.setFixedHeight(20)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        self.setLayout(layout)

        if self._level == 0:
            label = QLabel("CLEAN")
            label.setFont(QFont("JetBrains Mono", 9))
            label.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
            layout.addWidget(label)
        elif self._level == 1:
            label = QLabel("WARN")
            label.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            label.setStyleSheet(f"color: {G['amber']}; background: transparent;")
            layout.addWidget(label)
        else:
            label = QLabel("FLAG")
            label.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
            label.setStyleSheet(f"color: {G['red']}; background: transparent;")
            layout.addWidget(label)

        if self._level > 0:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {G['redDim'] if self._level == 2 else G['amberDim']};
                    border: 1px solid {G['red'] if self._level == 2 else G['amber']};
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                }
            """)


# ═══════════════════════════════════════════════════════
# TYPE CONFIGURATION
# ═══════════════════════════════════════════════════════
TYPE_ICONS = {
    "nas": "fa5s.server",
    "server": "fa5s.server",
    "computer": "fa5s.desktop",
    "laptop": "fa5s.laptop",
    "phone": "fa5s.mobile",
    "tablet": "fa5s.tablet",
    "printer": "fa5s.print",
    "router": "fa5s.wifi",
    "switch": "fa5s.projectdiagram",
    "access_point": "fa5s.wifi",
    "iot": "ph.devices",
    "smart": "ph.lightbulb",
    "webcam": "fa5s.camera",
    "speaker": "fa5s.volume-up",
    "headset": "fa5s.headphones",
    "keyboard": "fa5s.keyboard",
    "mouse": "fa5s.mouse-pointer",
    "game_controller": "fa5s.gamepad",
    "usb_dongle": "fa5s.plug",
    "audio_interface": "fa5s.volume-up",
    "storage": "fa5s.hdd",
    "network_adapter": "fa5s.ethernet",
    "bluetooth": "fa5s.bluetooth-b",
    "ethernet": "fa5s.ethernet",
    "wifi": "fa5s.wifi",
    "unknown": "fa5s.question",
}


# ═══════════════════════════════════════════════════════
# DEVICE ROW (List item for device list)
# ═══════════════════════════════════════════════════════
class DeviceRow(QFrame):
    """Device list item row with cyber terminal styling"""
    clicked = pyqtSignal(dict)

    def __init__(self, device: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._device = device
        self._setup_ui()

    def update_device(self, device: dict):
        """Update the device data"""
        self._device = device
        self._update_display()

    def _setup_ui(self):
        self.setFixedHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Get device type config
        dev_type = self._device.get("type", "unknown")
        cfg = DeviceClassifier.get_type_config(DeviceType(dev_type) if dev_type in [e.value for e in DeviceType] else DeviceType.UNKNOWN)
        color = cfg.color

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        self.setLayout(layout)

        # Status indicator
        status = self._device.get("status", "offline")
        dot_color = G["green"] if status == "online" else (G["amber"] if status in ["paired", "connected"] else G["textDim"])
        dot = GlowDot(dot_color)
        layout.addWidget(dot)

        # Device icon
        icon_name = TYPE_ICONS.get(dev_type, "fa5s.question")
        try:
            icon = qta.icon(icon_name, color=color)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(20, 20))
            icon_label.setStyleSheet("background: transparent;")
            layout.addWidget(icon_label)
        except Exception:
            pass

        # Device info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name = self._device.get("name", "Unknown Device")
        name_label = QLabel(name[:30] + ("..." if len(name) > 30 else ""))
        name_label.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {G['green']}; background: transparent;")
        info_layout.addWidget(name_label)

        ip = self._device.get("ip", "N/A")
        ip_label = QLabel(str(ip))
        ip_label.setFont(QFont("JetBrains Mono", 9))
        ip_label.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
        info_layout.addWidget(ip_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Ping indicator
        ping = self._device.get("ping", 0)
        ping_label = QLabel(f"{ping}ms")
        ping_label.setFont(QFont("JetBrains Mono", 10))
        ping_label.setStyleSheet(f"color: {ping_color(ping)}; background: transparent;")
        layout.addWidget(ping_label)

        # Source indicator
        source = self._device.get("source", "")
        if source:
            source_label = QLabel(f"[{source[:3].upper()}]")
            source_label.setFont(QFont("JetBrains Mono", 8))
            source_label.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
            layout.addWidget(source_label)

        self._update_style()

    def _update_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {G['bg1']};
                border: 1px solid {G['border']};
                border-radius: 4px;
            }}
            QFrame:hover {{
                background-color: {G['surface']};
                border-color: {G['border2']};
            }}
        """)

    def _update_display(self):
        """Update display with new device data"""
        # This could be enhanced to update individual elements
        # For now, we rebuild on major changes
        self._setup_ui()

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.clicked.emit(self._device)


# ═══════════════════════════════════════════════════════
# DETAIL PANEL
# ═══════════════════════════════════════════════════════
class DetailPanel(QFrame):
    """Detailed device information panel"""
    back_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._device: Optional[dict] = None
        self.setFixedWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI"""
        self._rebuild_ui()

    def set_device(self, device: dict):
        """Set the device to display"""
        self._device = device
        self._rebuild_ui()

    def clear_device(self):
        """Clear the current device"""
        self._device = None
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Rebuild the entire UI"""
        while self.layout():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self._device is None:
            self._setup_empty_state()
            return

        self._setup_content()

    def _setup_empty_state(self):
        """Setup empty state when no device is selected"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Placeholder
        placeholder = QFrame()
        placeholder.setStyleSheet(f"background-color: {G['bg1']};")
        placeholder_layout = QVBoxLayout()
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.setSpacing(20)
        placeholder.setLayout(placeholder_layout)

        # Icon
        try:
            icon = qta.icon("fa5s.server", color=G["textDim"], scale=2)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(64, 64))
            icon_label.setStyleSheet("background: transparent;")
            placeholder_layout.addWidget(icon_label)
        except Exception:
            pass

        # Text
        text = QLabel("Select a device to view details")
        text.setFont(QFont("JetBrains Mono", 12))
        text.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
        placeholder_layout.addWidget(text)

        layout.addWidget(placeholder)

    def _setup_content(self):
        """Setup the detail content"""
        device = self._device
        dev_type = device.get("type", "unknown")

        # Get type config
        try:
            cfg = DeviceClassifier.get_type_config(DeviceType(dev_type) if dev_type in [e.value for e in DeviceType] else DeviceType.UNKNOWN)
        except Exception:
            cfg = DeviceClassifier.get_type_config(DeviceType.UNKNOWN)

        color = cfg.color
        pc = ping_color(device.get("ping", 0))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Top accent line
        accent_line = QFrame()
        accent_line.setFixedHeight(2)
        accent_line.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:0.5 {G['cyan']}, stop:1 {color});
            }}
        """)
        layout.addWidget(accent_line)

        # Header with back button
        header = QFrame()
        header.setFixedHeight(90)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(18, 16, 18, 14)
        header_layout.setSpacing(12)
        header.setLayout(header_layout)

        # Back button
        back_btn = QPushButton()
        back_btn.setFixedSize(36, 36)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        try:
            back_icon = qta.icon("fa5s.arrow-left", color=G["text"])
            back_btn.setIcon(back_icon)
        except Exception:
            back_btn.setText("<")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {G['surface']};
                border: 1px solid {G['border2']};
                border-radius: 4px;
                color: {G['text']};
            }}
            QPushButton:hover {{
                background-color: {G['panel']};
                border-color: {G['green']};
            }}
        """)
        header_layout.addWidget(back_btn)

        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg.dim};
                border: 1px solid {color}44;
                border-radius: 4px;
            }}
        """)
        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        icon_name = TYPE_ICONS.get(dev_type, "fa5s.question")
        try:
            icon = qta.icon(icon_name, color=color)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(22, 22))
            icon_label.setStyleSheet("background: transparent;")
            icon_layout.addWidget(icon_label)
        except Exception:
            pass

        header_layout.addWidget(icon_container)

        # Device name and type
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name_label = QLabel(device.get("name", "Unknown Device"))
        name_label.setFont(QFont("JetBrains Mono", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {G['green']}; background: transparent;")
        name_label.setMaximumWidth(220)
        info_layout.addWidget(name_label)

        type_label = QLabel(f"{cfg.glyph} {cfg.label}")
        type_label.setFont(QFont("JetBrains Mono", 9))
        type_label.setStyleSheet(f"color: {color}; background: transparent;")
        info_layout.addWidget(type_label)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)

        status = device.get("status", "offline")
        dot = GlowDot(G["green"] if status == "online" else G["amber"])
        status_layout.addWidget(dot)

        status_label = QLabel(status.upper())
        status_label.setFont(QFont("JetBrains Mono", 9))
        status_label.setStyleSheet(f"color: {G['green'] if status == 'online' else G['amber']}; background: transparent;")
        status_layout.addWidget(status_label)
        status_layout.addStretch()

        info_layout.addLayout(status_layout)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {G['bg1']};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {G['bg1']};
            }}
        """)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(18, 14, 18, 14)
        content_layout.setSpacing(16)
        content.setLayout(content_layout)

        # NETWORK INFO section
        section_label = QLabel("── NETWORK INFO ──────────────────────")
        section_label.setFont(QFont("JetBrains Mono", 8))
        section_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 2px; background: transparent;")
        content_layout.addWidget(section_label)

        net_fields = [
            ("IPv4", device.get("ip", "N/A"), color),
            ("MAC", device.get("mac", "N/A"), G["green"]),
            ("OUI", mac_to_hex_display(device.get("mac", "00:00:00:00:00:00"))[:14] + "...", G["textDim"]),
            ("VENDOR", device.get("vendor", "Unknown"), G["text"]),
        ]

        # Add speed for adapters
        if device.get("speed"):
            net_fields.append(("SPEED", device["speed"], G["cyan"]))

        net_fields.extend([
            ("OS", device.get("os", "N/A"), G["text"]),
            ("LAST-SEEN", device.get("last_seen", "just now"), G["textDim"]),
            ("SOURCE", device.get("source", "unknown").upper(), G["textDim"]),
        ])

        for field in net_fields:
            field_layout = QHBoxLayout()
            field_layout.setContentsMargins(0, 6, 0, 6)
            field_layout.setSpacing(12)

            key_label = QLabel(field[0])
            key_label.setFont(QFont("JetBrains Mono", 9))
            key_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 1px; background: transparent;")
            key_label.setFixedWidth(80)
            field_layout.addWidget(key_label)

            value_label = QLabel(str(field[1]))
            value_label.setFont(QFont("JetBrains Mono", 10))
            value_label.setStyleSheet(f"color: {field[2]}; background: transparent;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            field_layout.addWidget(value_label)

            content_layout.addLayout(field_layout)

            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {G['border']};")
            content_layout.addWidget(sep)

        # LATENCY section
        latency_frame = QFrame()
        latency_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {G['surface']};
                border: 1px solid {G['border2']};
                border-radius: 4px;
            }}
        """)
        latency_layout = QHBoxLayout()
        latency_layout.setContentsMargins(14, 14, 14, 14)
        latency_layout.setSpacing(12)
        latency_frame.setLayout(latency_layout)

        latency_info = QVBoxLayout()
        latency_info.setSpacing(4)

        latency_title = QLabel("RTT / LATENCY")
        latency_title.setFont(QFont("JetBrains Mono", 8))
        latency_title.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 2px; background: transparent;")
        latency_info.addWidget(latency_title)

        latency_value_layout = QHBoxLayout()
        latency_value_layout.setSpacing(4)

        ping = device.get("ping", 0)
        latency_value = QLabel(str(ping))
        latency_value.setFont(QFont("JetBrains Mono", 28, QFont.Weight.Bold))
        latency_value.setStyleSheet(f"color: {pc}; text-shadow: 0 0 20px {pc}; background: transparent;")
        latency_value_layout.addWidget(latency_value)

        latency_unit = QLabel("ms")
        latency_unit.setFont(QFont("JetBrains Mono", 10))
        latency_unit.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
        latency_value_layout.addWidget(latency_unit)

        latency_info.addLayout(latency_value_layout)

        latency_status = QLabel("EXCELLENT" if ping < 10 else "GOOD" if ping < 30 else "HIGH-LATENCY")
        latency_status.setFont(QFont("JetBrains Mono", 8))
        latency_status.setStyleSheet(f"color: {pc}; letter-spacing: 1px; background: transparent;")
        latency_info.addWidget(latency_status)

        latency_layout.addLayout(latency_info)
        latency_layout.addWidget(SigBars(ping))

        content_layout.addWidget(latency_frame)

        # Services/Ports section
        services = device.get("services", {})
        ports = device.get("ports", [])

        if ports or services:
            ports_label = QLabel("── OPEN PORTS ────────────────────────")
            ports_label.setFont(QFont("JetBrains Mono", 8))
            ports_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 2px; background: transparent;")
            content_layout.addWidget(ports_label)

            if ports:
                ports_layout = QHBoxLayout()
                ports_layout.setSpacing(6)

                for port in ports[:10]:  # Limit to 10 ports
                    port_frame = QFrame()
                    port_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {G['surface']};
                            border: 1px solid {G['border2']};
                            border-radius: 3px;
                            padding: 4px 10px;
                        }}
                    """)
                    port_layout = QHBoxLayout()
                    port_layout.setContentsMargins(0, 4, 0, 4)
                    port_layout.setSpacing(4)
                    port_frame.setLayout(port_layout)

                    port_num = QLabel(str(port))
                    port_num.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
                    port_num.setStyleSheet(f"color: {G['green']}; background: transparent;")
                    port_layout.addWidget(port_num)

                    service_name = services.get(port, "")
                    if service_name:
                        port_svc = QLabel(f"/{service_name[:8]}")
                        port_svc.setFont(QFont("JetBrains Mono", 9))
                        port_svc.setStyleSheet(f"color: {G['textDim']}; background: transparent;")
                        port_layout.addWidget(port_svc)

                    ports_layout.addWidget(port_frame)

                content_layout.addLayout(ports_layout)

        # USB info
        if device.get("vid") or device.get("device_id"):
            usb_label = QLabel("── USB INFO ───────────────────────────")
            usb_label.setFont(QFont("JetBrains Mono", 8))
            usb_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 2px; background: transparent;")
            content_layout.addWidget(usb_label)

            usb_fields = []
            if device.get("vid"):
                usb_fields.append(("VID", f"0x{device['vid']}", G["cyan"]))
            if device.get("pid"):
                usb_fields.append(("PID", f"0x{device['pid']}", G["cyan"]))
            if device.get("device_id"):
                usb_fields.append(("ID", device["device_id"][:25] + "...", G["textDim"]))

            for field in usb_fields:
                field_layout = QHBoxLayout()
                field_layout.setContentsMargins(0, 6, 0, 6)
                field_layout.setSpacing(12)

                key_label = QLabel(field[0])
                key_label.setFont(QFont("JetBrains Mono", 9))
                key_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 1px; background: transparent;")
                key_label.setFixedWidth(80)
                field_layout.addWidget(key_label)

                value_label = QLabel(str(field[1]))
                value_label.setFont(QFont("JetBrains Mono", 10))
                value_label.setStyleSheet(f"color: {field[2]}; background: transparent;")
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                field_layout.addWidget(value_label)

                content_layout.addLayout(field_layout)

        # Driver info for audio
        if device.get("driver"):
            audio_label = QLabel("── DRIVER ─────────────────────────────")
            audio_label.setFont(QFont("JetBrains Mono", 8))
            audio_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 2px; background: transparent;")
            content_layout.addWidget(audio_label)

            field_layout = QHBoxLayout()
            field_layout.setContentsMargins(0, 6, 0, 6)
            field_layout.setSpacing(12)

            key_label = QLabel("DRIVER")
            key_label.setFont(QFont("JetBrains Mono", 9))
            key_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 1px; background: transparent;")
            key_label.setFixedWidth(80)
            field_layout.addWidget(key_label)

            value_label = QLabel(str(device["driver"])[:30])
            value_label.setFont(QFont("JetBrains Mono", 10))
            value_label.setStyleSheet(f"color: {G['cyan']}; background: transparent;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            field_layout.addWidget(value_label)

            content_layout.addLayout(field_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)


# ═══════════════════════════════════════════════════════
# DEVICE LIST PANEL
# ═══════════════════════════════════════════════════════
class DeviceListPanel(QFrame):
    """Left panel with device list"""
    device_selected = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._devices: List[dict] = []
        self._device_rows: Dict[str, DeviceRow] = {}
        self._selected_id: Optional[str] = None
        self._scanning = False
        self._setup_ui()

    def set_devices(self, devices: List[dict]):
        """Update device list from external source"""
        self._devices = devices
        self._rebuild_list()

    def update_device(self, device: dict):
        """Update a single device in the list"""
        device_id = device.get("id", "")
        if device_id in self._device_rows:
            self._device_rows[device_id].update_device(device)

            # Update stats
            self._update_stats()

            # If this is the selected device, update the detail panel
            if device_id == self._selected_id:
                self.device_selected.emit(device)

    def _rebuild_list(self):
        """Rebuild device rows from current _devices list"""
        scroll = self.findChild(QScrollArea)
        if not scroll:
            return
        list_widget = scroll.widget()
        if not list_widget:
            return
        list_layout = list_widget.layout()
        if not list_layout:
            return

        # Remove existing rows
        while list_layout.count():
            item = list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._device_rows.clear()

        # Add device rows
        for device in self._devices:
            row = DeviceRow(device)
            row.clicked.connect(self._on_device_clicked)
            list_layout.addWidget(row)
            self._device_rows[device.get("id", "")] = row

        list_layout.addStretch()

        # Update stats
        self._update_stats()

    def _update_stats(self):
        """Update the stats label"""
        online_count = sum(1 for d in self._devices if d.get("status") == "online")
        total_count = len(self._devices)
        self._stats_label.setText(f"{online_count} ONLINE / {total_count} TOTAL")

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {G['bg1']};
                border-right: 1px solid {G['border2']};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Search bar
        search_frame = QFrame()
        search_frame.setFixedHeight(50)
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {G['bg1']};
                border-bottom: 1px solid {G['border']};
            }}
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(8)
        search_frame.setLayout(search_layout)

        try:
            search_icon = qta.icon("fa5s.search", color=G["textDim"])
            search_icon_label = QLabel()
            search_icon_label.setPixmap(search_icon.pixmap(14, 14))
            search_icon_label.setStyleSheet("background: transparent;")
            search_layout.addWidget(search_icon_label)
        except Exception:
            pass

        self._search_input = QLineEdit()
        self._search_input.setFont(QFont("JetBrains Mono", 10))
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {G['surface']};
                color: {G['text']};
                border: 1px solid {G['border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border-color: {G['green']};
            }}
        """)
        self._search_input.setPlaceholderText("Search devices...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)

        # Refresh button
        self._refresh_btn = QPushButton()
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            refresh_icon = qta.icon("fa5s.sync-alt", color=G["green"])
            self._refresh_btn.setIcon(refresh_icon)
            self._refresh_btn.setIconSize(QSize(14, 14))
        except Exception:
            self._refresh_btn.setText("Refresh")
        self._refresh_btn.setFixedSize(36, 32)
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {G['surface']};
                border: 1px solid {G['border2']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {G['panel']};
                border-color: {G['green']};
            }}
        """)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        search_layout.addWidget(self._refresh_btn)

        layout.addWidget(search_frame)

        # Stats row
        stats_frame = QFrame()
        stats_frame.setFixedHeight(50)
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(12, 8, 12, 8)
        stats_layout.setSpacing(8)
        stats_frame.setLayout(stats_layout)

        self._stats_label = QLabel("0 ONLINE / 0 TOTAL")
        self._stats_label.setFont(QFont("JetBrains Mono", 8))
        self._stats_label.setStyleSheet(f"color: {G['textDim']}; letter-spacing: 1px; background: transparent;")
        stats_layout.addWidget(self._stats_label)

        self._scan_indicator = QLabel("")
        self._scan_indicator.setFont(QFont("JetBrains Mono", 8))
        self._scan_indicator.setStyleSheet(f"color: {G['green']}; background: transparent;")
        stats_layout.addWidget(self._scan_indicator)

        stats_layout.addStretch()

        layout.addWidget(stats_frame)

        # Device list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {G['bg1']};
                border: none;
            }}
        """)

        list_widget = QWidget()
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(12, 8, 12, 8)
        list_layout.setSpacing(6)
        list_widget.setLayout(list_layout)

        scroll.setWidget(list_widget)
        layout.addWidget(scroll, stretch=1)

    def _on_search_changed(self, text: str):
        """Filter devices by search text"""
        filter_text = text.lower()
        for device_id, row in self._device_rows.items():
            device = row._device
            visible = (
                filter_text in device.get("name", "").lower() or
                filter_text in device.get("ip", "").lower() or
                filter_text in device.get("vendor", "").lower() or
                filter_text in device.get("mac", "").lower() or
                filter_text in device.get("type", "").lower() or
                filter_text in device.get("status", "").lower()
            )
            row.setVisible(visible)

    def _on_device_clicked(self, device: dict):
        """Handle device row click"""
        self._selected_id = device.get("id")
        self.device_selected.emit(device)

    def _on_refresh_clicked(self):
        """Trigger refresh scan"""
        self._set_scanning(True)
        # Emit signal to trigger refresh
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._set_scanning(False))

    def _set_scanning(self, scanning: bool):
        """Set scanning state"""
        self._scanning = scanning
        if scanning:
            self._scan_indicator.setText("[SCANNING...]")
            try:
                spin_icon = qta.icon("fa5s.spinner", color=G["green"])
                self._refresh_btn.setIcon(spin_icon)
            except Exception:
                pass
        else:
            self._scan_indicator.setText("")
            try:
                refresh_icon = qta.icon("fa5s.sync-alt", color=G["green"])
                self._refresh_btn.setIcon(refresh_icon)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════
# MAIN VIEW
# ═══════════════════════════════════════════════════════
class UnitsView(QWidget, ScaleMixin):
    """NetworkSpy - Professional Device Discovery & Monitoring View"""

    settings_changed = pyqtSignal(str, object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        # Device state
        self._devices: List[dict] = []
        self._selected_device: Optional[dict] = None

        # Setup collector
        self._collector = DeviceCollector()
        self._collector.start()

        # Setup worker
        self._worker = DeviceMonitorWorker(self._collector)
        self._worker.devices_changed.connect(self._on_devices_changed)
        self._worker.device_changed.connect(self._on_device_changed)
        self._worker.start()

        # Setup UI
        self._setup_ui()

        # Initial scan
        QTimer.singleShot(500, self._do_initial_scan)

    def _do_initial_scan(self):
        """Trigger initial device scan"""
        self._collector.force_refresh()

    def _on_devices_changed(self, devices: List[dict]):
        """Handle devices list update from collector"""
        self._devices = devices
        self._device_list.set_devices(devices)

        # Update selected device if it changed
        if self._selected_device:
            device_id = self._selected_device.get("id")
            updated = next((d for d in devices if d.get("id") == device_id), None)
            if updated:
                self._selected_device = updated
                # Don't update detail panel here - it would reset navigation

    def _on_device_changed(self, device: dict):
        """Handle single device update"""
        self._device_list.update_device(device)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _handle_scale_changed(self, factor: float):
        self.on_scale_changed(factor)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup the main UI"""
        # Clear existing layout
        while self.layout():
            old_layout = self.layout()
            while old_layout.count():
                old_layout.takeAt(0).widget().setParent(None)
            old_layout.setParent(None)

        self.setStyleSheet(f"background-color: {G['bg0']};")

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Left panel - Device list
        self._device_list = DeviceListPanel()
        self._device_list.device_selected.connect(self._on_device_selected)
        main_layout.addWidget(self._device_list, stretch=1)

        # Right panel - Detail (stacked for navigation)
        self._detail_stack = QStackedWidget()
        main_layout.addWidget(self._detail_stack)

        # Detail view widget
        self._detail_view = QWidget()
        detail_layout = QHBoxLayout()
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(0)
        detail_layout.addWidget(DetailPanel())
        self._detail_view.setLayout(detail_layout)
        self._detail_stack.addWidget(self._detail_view)

    def _on_device_selected(self, device: dict):
        """Handle device selection from list"""
        self._selected_device = device

        # Find or create detail panel
        detail_panel = self._detail_view.findChild(DetailPanel)
        if detail_panel:
            detail_panel.set_device(device)
            detail_panel.back_clicked.connect(self._on_back_to_list)

        # Show detail view
        self._detail_stack.setCurrentWidget(self._detail_view)

    def _on_back_to_list(self):
        """Handle back navigation to device list"""
        self._detail_stack.setCurrentIndex(0)

    def update_data(self, data):
        """Handle data update from coordinator - not used for devices"""
        pass

    def cleanup(self):
        """Cleanup when view is destroyed"""
        if self._worker:
            self._worker.stop()
        if self._collector:
            self._collector.stop()


# Standalone test
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = UnitsView()
    view.setWindowTitle("Device Discovery")
    view.resize(1200, 800)
    view.show()
    sys.exit(app.exec())
