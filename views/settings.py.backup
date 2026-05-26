"""
Settings View - Professional application settings
Clean enterprise-grade settings interface
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QFileDialog, QMessageBox, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QPainter, QColor

from config import settings
from utils.autostart import AutostartManager
from scaler import S, ScaleMixin
from styles.theme import theme_manager
from widgets.settings_section import SettingsSection
from widgets.settings_row import SettingsRow


class ToggleWidget(QWidget, ScaleMixin):
    """Toggle switch widget with green active state"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(50, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_manager.theme_changed.connect(lambda _: self.update())

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
        c = theme_manager.colors

        # Track color
        if self._checked:
            track_color = QColor(c.ACCENT_GREEN)
        else:
            track_color = QColor(c.BORDER)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, 50, 26, 13, 13)

        # Handle
        handle_x = 26 if self._checked else 4
        handle_rect = QRect(handle_x, 4, 22, 22)

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(handle_rect)


class SettingsView(QWidget, ScaleMixin):
    """Settings view with organized sections"""

    settings_changed = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()

    def _on_theme_changed(self, theme_name: str):
        """Rebuild UI when theme changes"""
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
        # Clear existing layout
        while self.layout():
            old_layout = self.layout()
            while old_layout.count():
                old_layout.takeAt(0).widget().setParent(None)
            old_layout.setParent(None)

        c = theme_manager.colors
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout (no scroll area - fits in window)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(S.px(32), S.px(32), S.px(32), S.px(32))
        main_layout.setSpacing(S.px(24))
        self.setLayout(main_layout)

        # Content container with max width for readability
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content.setMaximumWidth(S.px(900))
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(S.px(24))
        content.setLayout(content_layout)
        main_layout.addWidget(content, stretch=1)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
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
        section = SettingsSection(title)
        parent_layout.addWidget(section)
        return section.get_content_layout()

    def _add_row(self, layout, label_text, control):
        """Add a row to a section layout"""
        row = SettingsRow(label_text)
        row.set_control(control)
        layout.addWidget(row)

    def _create_styled_combo(self, items, current_index=0):
        """Create a styled combo box"""
        c = theme_manager.colors
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(current_index)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {c.BG_INPUT};
                color: {c.TEXT_PRIMARY};
                border: 0px solid {c.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 100px;
            }}
            QComboBox::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {c.TEXT_MUTED};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 0px solid {c.BORDER};
                border-radius: 6px;
            }}
        """)
        return combo

    def _add_appearance_section(self, layout):
        # Get available themes with display names
        available_themes = theme_manager.get_available_themes()
        theme_display_names = [theme_manager.get_theme_display_name(t) for t in available_themes]

        combo = self._create_styled_combo(theme_display_names)
        current_theme = settings.get('theme', 'midnight')
        try:
            current_index = available_themes.index(current_theme)
        except ValueError:
            current_index = 0  # Default to 'midnight' (index 0)
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(lambda idx: self._on_theme_changed(available_themes[idx]))
        self._add_row(layout, "Theme", combo)

        # Reset to default button (for custom theme)
        c = theme_manager.colors
        reset_btn = QPushButton("Reset Custom to Default")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_GREEN};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.ACCENT_GREEN_BRIGHT};
            }}
        """)
        reset_btn.clicked.connect(self._on_reset_custom_theme)
        self._add_row(layout, "Reset Custom Theme", reset_btn)

    def _on_reset_custom_theme(self):
        """Reset custom theme to default colors"""
        from styles.theme import DEFAULT_COLORS
        settings.set('custom_theme_colors', DEFAULT_COLORS.copy())
        theme_manager.reset_to_default()

    def _on_theme_changed(self, theme_name: str):
        settings.set('theme', theme_name)
        if theme_name == 'custom':
            custom_colors = settings.get('custom_theme_colors', {})
            if custom_colors:
                theme_manager.load_custom_theme(custom_colors)
        theme_manager.set_theme(theme_name)
        self.settings_changed.emit('theme', theme_name)

    def _add_performance_section(self, layout):
        combo = self._create_styled_combo(["250ms", "500ms", "1000ms", "2000ms"])
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
        c = theme_manager.colors
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background-color: {c.BORDER};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background-color: {c.ACCENT_GREEN};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background-color: {c.TEXT_PRIMARY};
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }}
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
        combo = self._create_styled_combo(["CSV", "JSON"])
        combo.setCurrentText(settings.get('export_format', 'csv').upper())
        combo.currentIndexChanged.connect(lambda idx: self._on_setting_changed('export_format', combo.currentText().lower()))
        self._add_row(layout, "Export Format", combo)

        c = theme_manager.colors
        btn = QPushButton("Browse...")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_GREEN};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.ACCENT_GREEN_BRIGHT};
            }}
        """)
        btn.clicked.connect(self._on_browse_export_directory)
        self._add_row(layout, "Export Directory", btn)

    def _add_reset_section(self, layout):
        c = theme_manager.colors
        btn = QPushButton("Reset to Defaults")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_RED};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.STATUS_RED};
            }}
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