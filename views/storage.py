"""
Storage View - Professional comprehensive storage monitoring
Enterprise-grade storage monitoring with live graphs, per-disk cards, and SMART status
"""
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import qtawesome as qta

from styles.theme import theme_manager
from scaler import S, ScaleMixin
from utils.logger import get_logger, LogCategory, log_info, log_debug, log_error, log_exception
from data.storage import StorageCollector
from widgets.storage_widgets import (
    StorageDiskCard, StorageOverviewCard, StatTile
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
        self.setFixedHeight(S.px(72))
        self.setStyleSheet(f"background-color: {colors.BG_SECONDARY}; border: none;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(S.px(24), 0, S.px(24), 0)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Storage")
        title.setFont(QFont("Segoe UI", S.font_pt(22), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(title)

        subtitle = QLabel("Comprehensive disk monitoring with real-time performance")
        subtitle.setFont(QFont("Segoe UI", S.font_pt(10)))
        subtitle.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        title_layout.addWidget(subtitle)

        main_layout.addLayout(title_layout)
        main_layout.addStretch()

        # Live indicator
        live_layout = QHBoxLayout()
        live_layout.setSpacing(8)

        self._live_dot = QFrame()
        self._live_dot.setFixedSize(S.px(8), S.px(8))
        self._live_dot.setStyleSheet(f"""
            background-color: {colors.ACCENT_GREEN};
            border-radius: {S.px(4)}px;
        """)
        live_layout.addWidget(self._live_dot)

        self._live_label = QLabel("Live")
        self._live_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._live_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_layout.addWidget(self._live_label)

        main_layout.addLayout(live_layout)

        # Disk count indicator
        disk_count_layout = QHBoxLayout()
        disk_count_layout.setSpacing(8)

        disk_icon = QLabel()
        try:
            icon = qta.icon('fa5s.hdd', color=colors.ACCENT_BLUE, scale=1.0)
            disk_icon.setPixmap(icon.pixmap(S.px(16), S.px(16)))
        except Exception:
            disk_icon.setText("")
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
            self._live_label.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        else:
            self._live_dot.setStyleSheet(f"background-color: {colors.TEXT_MUTED}; border-radius: {S.px(4)}px;")
            self._live_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        self._setup_ui()
        self.set_live(self._live_state)


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

    def _setup_ui(self):
        """Build the storage monitoring UI"""
        colors = theme_manager.colors

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Header
        self._header = StorageHeader()
        main_layout.addWidget(self._header)

        # Scroll area for content
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {colors.BG_PRIMARY};
                border: none;
            }}
            QScrollArea > QWidget {{
                background-color: {colors.BG_PRIMARY};
            }}
        """)

        # Content widget
        self._content_widget = QWidget()
        self._content_widget.setMaximumWidth(S.px(1400))

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(S.px(24), S.px(16), S.px(24), S.px(24))
        content_layout.setSpacing(S.px(16))
        self._content_widget.setLayout(content_layout)

        self._scroll_area.setWidget(self._content_widget)
        main_layout.addWidget(self._scroll_area, stretch=1)

        # Overview section
        self._overview_card = StorageOverviewCard()
        self._overview_card.set_storage_info(0, 0, 0, 0, 0)
        content_layout.addWidget(self._overview_card)

        # Stats summary grid
        self._stats_section(content_layout)

        # Disk cards section
        self._disk_cards_section(content_layout)

        # Start update timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update_tick)
        self._update_timer.start(self._update_interval_ms)

    def _stats_section(self, parent_layout):
        """Create stats summary grid"""
        colors = theme_manager.colors

        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: transparent; border: none;")

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)
        stats_frame.setLayout(stats_layout)

        stats_title = QLabel("Performance Summary")
        stats_title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        stats_title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        stats_layout.addWidget(stats_title)

        # Stats grid
        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(S.px(12))

        self._read_speed_tile = StatTile("Read Speed", "-- MB/s", colors.ACCENT_GREEN)
        self._write_speed_tile = StatTile("Write Speed", "-- MB/s", colors.ACCENT_BLUE)
        self._iops_tile = StatTile("IOPS", "--", colors.ACCENT_PURPLE)
        self._latency_tile = StatTile("Latency", "-- ms", colors.ACCENT_ORANGE)

        self._stats_grid.addWidget(self._read_speed_tile, 0, 0)
        self._stats_grid.addWidget(self._write_speed_tile, 0, 1)
        self._stats_grid.addWidget(self._iops_tile, 0, 2)
        self._stats_grid.addWidget(self._latency_tile, 0, 3)

        stats_layout.addLayout(self._stats_grid)
        parent_layout.addWidget(stats_frame)

    def _disk_cards_section(self, parent_layout):
        """Create disk cards section"""
        colors = theme_manager.colors

        self._disk_cards_container = QVBoxLayout()
        self._disk_cards_container.setSpacing(S.px(12))

        section_title = QLabel("Physical Disks")
        section_title.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        section_title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        self._disk_cards_container.addWidget(section_title)

        self._disk_cards_inner = QVBoxLayout()
        self._disk_cards_inner.setSpacing(S.px(12))
        self._disk_cards_container.addLayout(self._disk_cards_inner)

        parent_layout.addLayout(self._disk_cards_container)

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
            log_exception(LogCategory.DISK, f"Failed to start storage collector: {e}")

    def _on_collector_data(self, data: dict):
        """Handle incoming data from collector"""
        self._update_from_data(data)

    def _on_update_tick(self):
        """Periodic update tick"""
        if not self._collector_started:
            self.start_collector()

    def _update_from_data(self, data: dict):
        """Update UI with new data"""
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

        # Update aggregate stats
        total_read = data.get('total_read_rate', 0)
        total_write = data.get('total_write_rate', 0)

        # Update stats tiles
        self._read_speed_tile.set_value(self._format_speed(total_read))
        self._write_speed_tile.set_value(self._format_speed(total_write))

        # Remove old cards
        for device in list(self._disk_cards.keys()):
            if device not in current_devices:
                card = self._disk_cards.pop(device)
                card.deleteLater()

        # Update overview
        total_size = sum(d.get('total', 0) for d in disks)
        total_used = sum(d.get('used', 0) for d in disks)
        total_free = sum(d.get('free', 0) for d in disks)
        self._overview_card.set_storage_info(total_size, total_used, total_free, total_read, total_write)

        self._header.set_live(True)

    def _set_live(self, live: bool):
        """Set live indicator"""
        if hasattr(self, '_header'):
            self._header.set_live(live)

    def _format_speed(self, bps: float) -> str:
        """Format bytes/sec to human readable string"""
        if bps >= 1_073_741_824:
            return f"{bps / 1_073_741_824:.2f} GB/s"
        elif bps >= 1_048_576:
            return f"{bps / 1_048_576:.0f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        return f"{bps:.0f} B/s"

    def _on_theme_changed(self, theme_name: str):
        """Handle theme changes"""
        for card in self._disk_cards.values():
            card._on_theme_changed(theme_name)

    def on_scale_changed(self, factor: float):
        """Handle DPI scale changes"""
        self.update()

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