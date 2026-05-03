"""
Settings View - Professional application settings
Simple and stable implementation
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QComboBox, QSlider, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QPainter, QColor

from config import settings
from utils.autostart import AutostartManager
from scaler import S, ScaleMixin


class ToggleWidget(QWidget, ScaleMixin):
    """Toggle switch widget with green/off colors"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(50, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setChecked(self, checked: bool):
        self._checked = checked
        self.toggled.emit(checked)
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def mouseReleaseEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Green track when on, gray when off
        if self._checked:
            track_color = QColor(16, 185, 129)  # Green
        else:
            track_color = QColor(42, 52, 65)   # Gray

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, 50, 26, 13, 13)

        # Handle
        handle_x = 26 if self._checked else 4
        handle_rect = QRect(handle_x, 4, 22, 22)

        # Shadow
        painter.setBrush(QColor(0, 0, 0, 40))
        painter.drawEllipse(handle_rect.adjusted(0, 2, 0, 2))

        # White handle
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(handle_rect)


class SettingsView(QWidget, ScaleMixin):
    """Settings view with organized sections"""

    settings_changed = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self._setup_ui()

    def scale_disconnect(self):
        try:
            from scaler import _signals
            _signals.scale_changed.disconnect(self._handle_scale_changed)
        except Exception:
            pass

    def _handle_scale_changed(self, factor: float):
        self.on_scale_changed(factor)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        # Dark background
        self.setStyleSheet("background-color: #0a0e14;")

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content container
        content = QWidget()
        content.setMaximumWidth(900)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        content.setLayout(main_layout)

        scroll.setWidget(content)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(scroll)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #f0f4f8;")
        main_layout.addWidget(title)

        # Appearance section
        section = self._create_section("Appearance", main_layout)
        self._add_appearance_section(section)

        # Performance section
        section = self._create_section("Performance", main_layout)
        self._add_performance_section(section)

        # Alerts section
        section = self._create_section("Alerts", main_layout)
        self._add_alerts_section(section)

        # Features section
        section = self._create_section("Features", main_layout)
        self._add_features_section(section)

        # System section
        section = self._create_section("System", main_layout)
        self._add_system_section(section)

        # Export section
        section = self._create_section("Export", main_layout)
        self._add_export_section(section)

        # Reset section
        section = self._create_section("Reset", main_layout)
        self._add_reset_section(section)

        main_layout.addStretch()

    def _create_section(self, title: str, parent_layout):
        """Create a settings section"""
        section = QWidget()
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(8)
        section.setLayout(section_layout)

        # Section title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #f0f4f8;")
        section_layout.addWidget(title_label)

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 8, 0, 0)
        content_layout.setSpacing(0)
        content_widget.setLayout(content_layout)
        section_layout.addWidget(content_widget)

        parent_layout.addWidget(section)
        return content_layout

    def _add_row(self, layout, label_text, control):
        """Add a row to a section layout"""
        row = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 12, 0, 12)
        row_layout.setSpacing(16)
        row.setLayout(row_layout)

        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 13))
        label.setStyleSheet("color: #f0f4f8;")
        row_layout.addWidget(label, 1)

        row_layout.addWidget(control)
        layout.addWidget(row)

    def _create_combo(self, items, current_index=0):
        """Create a styled combo box"""
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(current_index)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #0d1117;
                color: #f0f4f8;
                border: 1px solid #2a3441;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 100px;
            }
            QComboBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #94a3b8;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #161f2a;
                color: #f0f4f8;
                border: 1px solid #2a3441;
                border-radius: 6px;
            }
        """)
        return combo

    def _add_appearance_section(self, layout):
        combo = self._create_combo(["Dark", "Light"])
        combo.setCurrentText(settings.get('theme', 'dark').title())
        combo.currentIndexChanged.connect(lambda idx: self._on_setting_changed('theme', combo.currentText().lower()))
        self._add_row(layout, "Theme", combo)

    def _add_performance_section(self, layout):
        combo = self._create_combo(["250ms", "500ms", "1000ms", "2000ms"])
        intervals = {250: 0, 500: 1, 1000: 2, 2000: 3}
        combo.setCurrentIndex(intervals.get(settings.get('update_interval', 500), 1))
        combo.currentIndexChanged.connect(lambda idx: self._on_setting_changed('update_interval', list(intervals.keys())[idx]))
        self._add_row(layout, "Update Interval", combo)

    def _add_alerts_section(self, layout):
        toggle = ToggleWidget()
        toggle.setChecked(settings.get('alerts_enabled', True))
        toggle.toggled.connect(lambda checked: self._on_setting_changed('alerts_enabled', checked))
        self._add_row(layout, "Enable Alerts", toggle)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(50, 100)
        slider.setValue(settings.get('alert_cpu_threshold', 80))
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background-color: #2a3441;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background-color: #10b981;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #f0f4f8;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
        """)
        slider.valueChanged.connect(lambda v: self._on_setting_changed('alert_cpu_threshold', v))
        self._add_row(layout, "CPU Alert Threshold", slider)

    def _add_features_section(self, layout):
        toggle = ToggleWidget()
        toggle.setChecked(settings.get('show_gpu', True))
        toggle.toggled.connect(lambda checked: self._on_setting_changed('show_gpu', checked))
        self._add_row(layout, "Show GPU", toggle)

        toggle = ToggleWidget()
        toggle.setChecked(settings.get('show_network', True))
        toggle.toggled.connect(lambda checked: self._on_setting_changed('show_network', checked))
        self._add_row(layout, "Show Network", toggle)

    def _add_system_section(self, layout):
        toggle = ToggleWidget()
        toggle.setChecked(settings.get('autostart', False))
        toggle.toggled.connect(self._on_autostart_toggled)
        self._add_row(layout, "Start with Windows", toggle)

        toggle = ToggleWidget()
        toggle.setChecked(settings.get('minimize_to_tray', False))
        toggle.toggled.connect(lambda checked: self._on_setting_changed('minimize_to_tray', checked))
        self._add_row(layout, "Minimize to Tray", toggle)

        toggle = ToggleWidget()
        toggle.setChecked(settings.get('start_minimized', False))
        toggle.toggled.connect(lambda checked: self._on_setting_changed('start_minimized', checked))
        self._add_row(layout, "Start Minimized", toggle)

    def _add_export_section(self, layout):
        combo = self._create_combo(["CSV", "JSON"])
        combo.setCurrentText(settings.get('export_format', 'csv').upper())
        combo.currentIndexChanged.connect(lambda idx: self._on_setting_changed('export_format', combo.currentText().lower()))
        self._add_row(layout, "Export Format", combo)

        btn = QPushButton("Browse...")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        btn.clicked.connect(self._on_browse_export_directory)
        self._add_row(layout, "Export Directory", btn)

    def _add_reset_section(self, layout):
        btn = QPushButton("Reset to Defaults")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        btn.clicked.connect(self._on_reset_clicked)
        self._add_row(layout, "Reset All Settings", btn)

    def _on_autostart_toggled(self, checked: bool):
        settings.set('autostart', checked)
        if checked:
            AutostartManager.enable()
        else:
            AutostartManager.disable()
        self.settings_changed.emit('autostart', checked)

    def _on_setting_changed(self, key: str, value):
        settings.set(key, value)
        self.settings_changed.emit(key, value)

    def _on_browse_export_directory(self):
        current = settings.get('export_directory', str(Path.home() / 'Documents'))
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory", current)
        if directory:
            self._on_setting_changed('export_directory', directory)

    def _on_reset_clicked(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            settings.reset_to_defaults()
            AutostartManager.disable()

    def update_data(self, data):
        pass