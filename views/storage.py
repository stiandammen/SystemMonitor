"""
Storage View - Professional comprehensive storage monitoring
Enterprise-grade storage monitoring with live graphs, per-disk cards, and SMART status
"""
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import qtawesome as qta

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from utils.logger import get_logger, LogCategory, log_info, log_debug, log_error, log_exception
from data.storage import StorageCollector
from widgets.card import Card
from widgets.storage_widgets import (
    StorageDiskCard, StorageOverviewCard, StatTile, TemperatureBar
)


class StorageHeader(QWidget):
    """Header widget for storage view with live indicator and stats summary"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._live_state = True
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        """Build header layout"""
        colors = theme_manager.colors
        self.setFixedHeight(S.px(56))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"background-color: {colors.BG_CARD}; border: none; border-radius: {S.px(10)}px;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(S.px(20), 0, S.px(20), 0)
        main_layout.setSpacing(S.px(16))
        self.setLayout(main_layout)

        # Live indicator
        live_layout = QHBoxLayout()
        live_layout.setSpacing(S.px(8))

        self._live_dot = QFrame()
        self._live_dot.setFixedSize(S.px(8), S.px(8))
        self._live_dot.setStyleSheet(f"""
            background-color: {colors.ACCENT_GREEN};
            border-radius: {S.px(4)}px;
        """)
        live_layout.addWidget(self._live_dot)

        live_label = QLabel("LIVE")
        live_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        live_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_layout.addWidget(live_label)

        main_layout.addLayout(live_layout)

        # Title
        title = QLabel("Storage Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        main_layout.addWidget(title)

        main_layout.addStretch()

        # Disk count indicator
        disk_count_layout = QHBoxLayout()
        disk_count_layout.setSpacing(S.px(8))

        disk_icon = QLabel()
        try:
            icon = qta.icon('fa5s.hdd', color=colors.ACCENT_BLUE, scale=1.0)
            disk_icon.setPixmap(icon.pixmap(S.px(16), S.px(16)))
        except Exception:
            disk_icon.setText("")
        disk_icon.setStyleSheet("background: transparent;")
        disk_count_layout.addWidget(disk_icon)

        self._disk_count_label = QLabel("--")
        self._disk_count_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._disk_count_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        disk_count_layout.addWidget(self._disk_count_label)

        disks_text = QLabel("disks")
        disks_text.setFont(QFont("Segoe UI", S.font_pt(10)))
        disks_text.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        disk_count_layout.addWidget(disks_text)

        main_layout.addLayout(disk_count_layout)

    def set_disk_count(self, count: int):
        """Update disk count display"""
        self._disk_count_label.setText(str(count))

    def set_live(self, live: bool):
        """Set live indicator status"""
        colors = theme_manager.colors
        self._live_state = live
        if live:
            self._live_dot.setStyleSheet(f"background-color: {colors.ACCENT_GREEN}; border-radius: {S.px(4)}px;")
        else:
            self._live_dot.setStyleSheet(f"background-color: {colors.TEXT_MUTED}; border-radius: {S.px(4)}px;")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        self._setup_ui()
        self.set_live(self._live_state)


class StorageKpiCard(QFrame):
    """Premium KPI stat card for storage metrics"""
    def __init__(self, title: str, icon: str, accent: str, unit: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._accent = accent
        self._unit = unit
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(S.px(90))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        # Top row: icon + title
        top_row = QHBoxLayout()
        top_row.setSpacing(S.px(8))

        icon_label = QLabel()
        try:
            icon = qta.icon(self._icon, color=self._accent, scale=1.0)
            icon_label.setPixmap(icon.pixmap(S.px(16), S.px(16)))
        except Exception:
            icon_label.setText("")
        icon_label.setStyleSheet("background: transparent;")
        top_row.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        top_row.addWidget(title_label)
        top_row.addStretch()

        layout.addLayout(top_row)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(20), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        layout.addWidget(self._value_label)

        # Unit
        self._unit_label = QLabel(self._unit)
        self._unit_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._unit_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self._unit_label)

    def set_value(self, value: str, unit: str = ""):
        self._value_label.setText(value)
        if unit:
            self._unit_label.setText(unit)


class StorageView(QWidget, ScaleMixin):
    """
    Comprehensive storage monitoring view.
    Shows all disks with real-time metrics, graphs, and professional UI.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disk_cards: Dict[str, StorageDiskCard] = {}
        self._collector = None
        self._collector_started = False
        self._update_interval_ms = 1000

        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Build the storage monitoring UI"""
        colors = theme_manager.colors
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        main_layout.setSpacing(S.px(12))
        self.setLayout(main_layout)

        # ===== HEADER BAR =====
        self._header = StorageHeader()
        main_layout.addWidget(self._header)


        # ===== MAIN CONTENT (2 columns) =====
        content_container = QWidget()
        content_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(S.px(12))
        content_container.setLayout(content_layout)

        # LEFT COLUMN - Overview + usage bars
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(S.px(12))
        left_widget.setLayout(left_layout)

        # Overview card
        overview_card = Card(title="Storage Overview", icon="📊")
        self._overview_card = StorageOverviewCard()
        self._overview_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        overview_card.add_widget(self._overview_card)
        left_layout.addWidget(overview_card, stretch=1)

        # Top disks card
        disks_card = Card(title="Top Disks by Usage", icon="💾")
        self._top_disks_container = QVBoxLayout()
        self._top_disks_container.setSpacing(S.px(6))
        top_disks_widget = QWidget()
        top_disks_widget.setLayout(self._top_disks_container)
        disks_card.add_widget(top_disks_widget)
        left_layout.addWidget(disks_card, stretch=1)

        content_layout.addWidget(left_widget, stretch=2)

        # RIGHT COLUMN - Disk cards stacked
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(S.px(12))
        right_widget.setLayout(right_layout)

        # Physical disks header
        section_title = QLabel("Physical Disks")
        section_title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        section_title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        right_layout.addWidget(section_title)

        # Disk cards scroll container
        self._disk_cards_scroll = QWidget()
        self._disk_cards_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._disk_cards_inner = QVBoxLayout()
        self._disk_cards_inner.setSpacing(S.px(10))
        self._disk_cards_inner.setContentsMargins(0, 0, 0, 0)
        self._disk_cards_scroll.setLayout(self._disk_cards_inner)
        right_layout.addWidget(self._disk_cards_scroll, stretch=1)

        content_layout.addWidget(right_widget, stretch=1)

        main_layout.addWidget(content_container, stretch=1)

        # ===== BOTTOM STATUS BAR =====
        self._setup_status_bar(main_layout)

        # Start update timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update_tick)
        self._update_timer.start(self._update_interval_ms)

    def _setup_status_bar(self, parent_layout):
        """Setup bottom status bar"""
        colors = theme_manager.colors

        status_card = Card(title="Storage Health", icon="🛡️")
        status_layout = QHBoxLayout()
        status_layout.setSpacing(S.px(32))

        # Health indicator
        health_widget = QWidget()
        health_layout = QVBoxLayout()
        health_layout.setSpacing(4)
        health_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        health_icon = QLabel()
        try:
            icon = qta.icon("mdi.shield-check", color=colors.ACCENT_GREEN, scale=1.5)
            health_icon.setPixmap(icon.pixmap(S.px(28), S.px(28)))
        except Exception:
            health_icon.setText("✓")
        health_icon.setStyleSheet("background: transparent;")
        health_layout.addWidget(health_icon)

        self._health_label = QLabel("Healthy")
        self._health_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        self._health_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        health_layout.addWidget(self._health_label)

        health_widget.setLayout(health_layout)
        status_layout.addWidget(health_widget)

        # Total capacity
        cap_widget = QWidget()
        cap_layout = QVBoxLayout()
        cap_layout.setSpacing(2)
        cap_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cap_title = QLabel("Total Capacity")
        cap_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        cap_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        cap_layout.addWidget(cap_title)

        self._cap_label = QLabel("-- TB")
        self._cap_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._cap_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        cap_layout.addWidget(self._cap_label)

        cap_widget.setLayout(cap_layout)
        status_layout.addWidget(cap_widget)

        # Used space
        used_widget = QWidget()
        used_layout = QVBoxLayout()
        used_layout.setSpacing(2)
        used_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        used_title = QLabel("Used Space")
        used_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        used_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        used_layout.addWidget(used_title)

        self._used_label = QLabel("-- GB")
        self._used_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._used_label.setStyleSheet(f"color: {colors.ACCENT_BLUE}; background: transparent;")
        used_layout.addWidget(self._used_label)

        used_widget.setLayout(used_layout)
        status_layout.addWidget(used_widget)

        # Temperature
        temp_widget = QWidget()
        temp_layout = QVBoxLayout()
        temp_layout.setSpacing(2)
        temp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        temp_title = QLabel("Avg Temperature")
        temp_title.setFont(QFont("Segoe UI", S.font_pt(9)))
        temp_title.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        temp_layout.addWidget(temp_title)

        self._temp_label = QLabel("--°C")
        self._temp_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._temp_label.setStyleSheet(f"color: {colors.ACCENT_ORANGE}; background: transparent;")
        temp_layout.addWidget(self._temp_label)

        temp_widget.setLayout(temp_layout)
        status_layout.addWidget(temp_widget)

        status_layout.addStretch()

        status_card.add_layout(status_layout)
        parent_layout.addWidget(status_card)

    def start_collector(self):
        """Start the storage data collector"""
        if self._collector_started:
            return

        try:
            self._collector = StorageCollector()
            self._collector.data_updated.connect(self._on_collector_data)
            self._collector.start()
            self._collector_started = True
            log_info(LogCategory.DISK, "Storage collector started")
        except Exception as e:
            log_exception(LogCategory.DISK, "Failed to start storage collector", e)

    def _on_collector_data(self, data: dict):
        """Handle incoming data from collector"""
        self._update_from_data(data)

    def _on_update_tick(self):
        """Periodic update tick"""
        if not self._collector_started:
            self.start_collector()

    def _update_from_data(self, data: dict):
        """Update UI with new data"""
        colors = theme_manager.colors
        disks = data.get('disks', [])

        # Update header disk count
        self._header.set_disk_count(len(disks))

        # Track which disks we have
        current_devices = set()

        for disk in disks:
            device = disk.get('device', f'unknown_{id(disk)}')
            current_devices.add(device)

            # Update or create disk card
            if device not in self._disk_cards:
                card = StorageDiskCard(disk)
                self._disk_cards[device] = card
                self._disk_cards_inner.addWidget(card)
            else:
                self._disk_cards[device].update_disk_info(disk)

            # Update speeds
            read_rate = disk.get('read_rate', 0)
            write_rate = disk.get('write_rate', 0)
            self._disk_cards[device].update_speeds(read_rate, write_rate)

            # Update temperature
            temp = disk.get('temperature')
            if temp is not None:
                self._disk_cards[device].update_temperature(temp)

        # Remove old cards
        for device in list(self._disk_cards.keys()):
            if device not in current_devices:
                card = self._disk_cards.pop(device)
                card.deleteLater()

        # Update aggregate stats
        total_read = data.get('total_read_rate', 0)
        total_write = data.get('total_write_rate', 0)
        iops = data.get('iops', 0)
        latency = data.get('latency', 0)

        # Update overview card
        total_size = sum(d.get('total', 0) for d in disks)
        total_used = sum(d.get('used', 0) for d in disks)
        total_free = sum(d.get('free', 0) for d in disks)
        self._overview_card.set_storage_info(total_size, total_used, total_free, total_read, total_write)

        # Update status bar
        total_tb = total_size / (1024**4) if total_size > 0 else 0
        self._cap_label.setText(f"{total_tb:.1f} TB" if total_tb >= 1 else f"{total_size / (1024**3):.0f} GB")

        used_gb = total_used / (1024**3)
        self._used_label.setText(f"{used_gb:.0f} GB" if used_gb >= 1 else f"{used_gb:.1f} GB")

        # Calculate average temperature
        temps = [d.get('temperature', 0) for d in disks if d.get('temperature')]
        avg_temp = sum(temps) / len(temps) if temps else 0
        self._temp_label.setText(f"{avg_temp:.0f}°C")

        # Update top disks section
        self._update_top_disks(disks)

        self._header.set_live(True)

    def _update_top_disks(self, disks):
        """Update top disks by usage"""
        while self._top_disks_container.count():
            item = self._top_disks_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Sort by usage percentage
        sorted_disks = sorted(disks, key=lambda d: d.get('percent', 0), reverse=True)[:4]

        for disk in sorted_disks:
            device = disk.get('device', '')[:2]
            mountpoint = disk.get('mountpoint', 'N/A')
            percent = disk.get('percent', 0)
            total_gb = disk.get('total', 0) / (1024**3)
            used_gb = disk.get('used', 0) / (1024**3)

            pct_color = theme_manager.colors.ACCENT_GREEN if percent < 75 else theme_manager.colors.ACCENT_ORANGE if percent < 90 else theme_manager.colors.ACCENT_RED

            disk_row = QFrame()
            disk_row.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme_manager.colors.BG_HOVER};
                    border-radius: {S.px(8)}px;
                    padding: {S.px(8)}px;
                }}
            """)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(S.px(8), S.px(6), S.px(8), S.px(6))
            row_layout.setSpacing(S.px(12))
            disk_row.setLayout(row_layout)

            # Drive letter
            letter = QLabel(device)
            letter.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            letter.setStyleSheet(f"color: white; background: {pct_color}; padding: {S.px(2)}px {S.px(8)}px; border-radius: {S.px(4)}px;")
            letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter.setFixedWidth(S.px(32))
            row_layout.addWidget(letter)

            # Info
            info = QVBoxLayout()
            info.setSpacing(2)

            name = QLabel(f"{mountpoint}" if mountpoint else device)
            name.setFont(QFont("Segoe UI", S.font_pt(10)))
            name.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY}; background: transparent;")
            info.addWidget(name)

            bar = QProgressBar()
            bar.setValue(int(percent))
            bar.setFixedHeight(S.px(4))
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {theme_manager.colors.BG_PRIMARY};
                    border: none;
                    border-radius: {S.px(2)}px;
                }}
                QProgressBar::chunk {{
                    background-color: {pct_color};
                    border-radius: {S.px(2)}px;
                }}
            """)
            info.addWidget(bar)
            row_layout.addLayout(info, stretch=1)

            # Usage
            usage = QLabel(f"{used_gb:.0f}/{total_gb:.0f} GB")
            usage.setFont(QFont("Segoe UI", S.font_pt(9)))
            usage.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
            usage.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_layout.addWidget(usage)

            # Percentage
            pct = QLabel(f"{percent:.0f}%")
            pct.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            pct.setStyleSheet(f"color: {pct_color}; background: transparent;")
            pct.setAlignment(Qt.AlignmentFlag.AlignRight)
            pct.setMinimumWidth(S.px(30))
            row_layout.addWidget(pct)

            self._top_disks_container.addWidget(disk_row)

        self._top_disks_container.addStretch()

    def _set_live(self, live: bool):
        """Set live indicator"""
        if hasattr(self, '_header'):
            self._header.set_live(live)


    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        for card in self._disk_cards.values():
            card._on_theme_changed(theme_name)

    def update_data(self, data: dict):
        """Update view with data from main coordinator"""
        if 'disks' in data:
            self._update_from_data(data)

    def shutdown(self):
        """Cleanup when view is destroyed"""
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()
        if self._collector:
            self._collector.stop()
            if self._collector.isRunning():
                self._collector.requestInterruption()
                self._collector.wait(500)