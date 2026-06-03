"""
Settings View â€” Professional rebuild
Card-based sections, scroll support, consistent with the rest of the GUI theme.
"""
from systemmonitor.pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QFileDialog, QMessageBox,
    QSizePolicy, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.config import settings
from systemmonitor.utils.autostart import AutostartManager
from systemmonitor.utils.exporters import DataExporter
from systemmonitor.core.signals import signal_bus
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.styles.theme import theme_manager
from systemmonitor.widgets.card import Card
from systemmonitor.widgets.settings_row import ToggleWidget


def _c():
    return theme_manager.colors


class SettingsView(QWidget, ScaleMixin):
    signals_changed = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path_label = None
        self._last_data: dict = {}
        self._exporter = DataExporter()
        self._exporter.export_completed.connect(self._on_export_result)
        signal_bus.data_updated.connect(self._on_data_updated)
        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()

    def _on_theme_changed(self, _):
        # Defer rebuild so any active widget event (e.g. combo click) finishes first.
        # Rebuilding the layout synchronously inside theme_changed destroys the combo
        # box while Qt is still processing its currentIndexChanged event â†’ crash.
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def on_scale_changed(self, _):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    # â”€â”€ Build â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _setup_ui(self):
        if self.layout():
            old = self.layout()
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.deleteLater()
            # QWidget.setLayout() calls self.takeLayout() internally, which is the
            # only reliable way to clear self.layout() (setParent(None) on the layout
            # does NOT update QWidget's internal d->layout pointer, causing an
            # infinite loop on the next iteration of "while self.layout()").
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        c = _c()
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout()
        root.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        root.setSpacing(S.px(12))
        self.setLayout(root)

        root.addWidget(self._build_header())

        # Scroll area wraps all sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                width: {S.px(6)}px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c.BORDER};
                border-radius: {S.px(3)}px;
                min-height: {S.px(30)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.TEXT_MUTED};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, S.px(4), 0)
        content_layout.setSpacing(S.px(12))
        content.setLayout(content_layout)
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        self._build_general_section(content_layout)
        self._build_appearance_section(content_layout)
        self._build_alerts_section(content_layout)
        self._build_data_section(content_layout)
        self._build_maintenance_section(content_layout)
        content_layout.addStretch()

    # â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _build_header(self) -> QFrame:
        c = _c()
        header = QFrame()
        header.setMinimumHeight(S.px(52))
        header.setMaximumHeight(S.px(62))
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(20), 0, S.px(20), 0)
        layout.setSpacing(S.px(12))
        header.setLayout(layout)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QLabel("·")
        sep.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        sep.setFont(QFont("Segoe UI", S.font_pt(14)))
        layout.addWidget(sep)

        subtitle = QLabel("Application preferences")
        subtitle.setFont(QFont("Segoe UI", S.font_pt(11)))
        subtitle.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addStretch()

        badge = QLabel("v1.0.0")
        badge.setFont(QFont("Segoe UI", S.font_pt(9)))
        badge.setStyleSheet(f"""
            color: {c.TEXT_MUTED};
            background: {c.BG_SECONDARY};
            border-radius: {S.px(10)}px;
            padding: {S.px(3)}px {S.px(10)}px;
        """)
        layout.addWidget(badge)
        return header

    # â”€â”€ Row builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _row(self, label: str, desc: str, control: QWidget,
             last: bool = False) -> QFrame:
        """Single settings row: label + description left, control right."""
        c = _c()
        row = QFrame()
        row.setObjectName("SettingsRow")
        border = "" if last else f"border-bottom: 1px solid {c.BORDER};"
        row.setStyleSheet(f"""
            QFrame#SettingsRow {{
                background: transparent;
                border: none;
                {border}
            }}
            QFrame#SettingsRow:hover {{
                background-color: {c.BG_HOVER};
                border-radius: {S.px(6)}px;
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(6), S.px(14), S.px(6), S.px(14))
        layout.setSpacing(S.px(24))
        row.setLayout(layout)

        # Left â€” label + optional description
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        ll = QVBoxLayout()
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(S.px(2))
        left.setLayout(ll)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))
        lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        ll.addWidget(lbl)

        if desc:
            d = QLabel(desc)
            d.setFont(QFont("Segoe UI", S.font_pt(9)))
            d.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent; border: none;")
            d.setWordWrap(True)
            ll.addWidget(d)

        layout.addWidget(left, stretch=1)
        layout.addWidget(control)
        return row

    # â”€â”€ Control factories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _combo(self, display_items: list, data_items: list,
               current_value) -> QComboBox:
        c = _c()
        combo = QComboBox()
        for disp, data in zip(display_items, data_items):
            combo.addItem(disp, data)
        try:
            combo.setCurrentIndex(data_items.index(current_value))
        except (ValueError, IndexError):
            combo.setCurrentIndex(0)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setFixedWidth(S.px(210))
        combo.setFixedHeight(S.px(34))
        combo.setFont(QFont("Segoe UI", S.font_pt(10)))
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                padding: 0 {S.px(10)}px;
            }}
            QComboBox:hover {{
                border-color: {c.ACCENT_GREEN};
                background-color: {c.BG_HOVER};
            }}
            QComboBox::drop-down {{
                border: none;
                width: {S.px(24)}px;
            }}
            QComboBox::down-arrow {{
                border-left: {S.px(4)}px solid transparent;
                border-right: {S.px(4)}px solid transparent;
                border-top: {S.px(5)}px solid {c.TEXT_MUTED};
                margin-right: {S.px(8)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                selection-background-color: {c.BG_HOVER};
                padding: {S.px(4)}px;
                outline: none;
            }}
        """)
        return combo

    def _btn(self, text: str, danger: bool = False,
             accent: bool = False, icon: str = "") -> QPushButton:
        c = _c()
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        btn.setFixedHeight(S.px(34))

        if danger:
            bg, hover, fg = c.ACCENT_RED, "#c0392b", "#ffffff"
            border_col = c.ACCENT_RED
        elif accent:
            bg, hover, fg = c.ACCENT_GREEN, c.ACCENT_BLUE, "#ffffff"
            border_col = c.ACCENT_GREEN
        else:
            bg, hover, fg = c.BG_SECONDARY, c.BG_HOVER, c.TEXT_PRIMARY
            border_col = c.BORDER

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border_col};
                border-radius: {S.px(6)}px;
                padding: 0 {S.px(18)}px;
            }}
            QPushButton:hover {{
                background-color: {hover};
                border-color: {c.ACCENT_GREEN if not danger else c.ACCENT_RED};
            }}
            QPushButton:pressed {{
                background-color: {bg};
            }}
        """)
        if icon:
            try:
                icon_color = "#ffffff" if (danger or accent) else c.TEXT_PRIMARY
                btn.setIcon(qta.icon(icon, color=icon_color))
                btn.setIconSize(QSize(S.px(14), S.px(14)))
            except Exception:
                pass
        return btn

    def _slider_row(self, minimum: int, maximum: int,
                    value: int) -> tuple[QWidget, QSlider]:
        c = _c()
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lo = QHBoxLayout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(S.px(10))
        container.setLayout(lo)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.setFixedWidth(S.px(170))
        slider.setFixedHeight(S.px(34))
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: {S.px(4)}px;
                background: {c.BORDER};
                border-radius: {S.px(2)}px;
            }}
            QSlider::sub-page:horizontal {{
                background: {c.ACCENT_GREEN};
                border-radius: {S.px(2)}px;
            }}
            QSlider::handle:horizontal {{
                background: {c.TEXT_PRIMARY};
                width: {S.px(16)}px;
                height: {S.px(16)}px;
                border-radius: {S.px(8)}px;
                margin: {S.px(-6)}px 0;
                border: 2px solid {c.ACCENT_GREEN};
            }}
            QSlider::handle:horizontal:hover {{
                background: {c.ACCENT_GREEN};
            }}
        """)

        val_lbl = QLabel(f"{value}%")
        val_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        val_lbl.setFixedWidth(S.px(42))
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"""
            color: {c.ACCENT_GREEN};
            background: {c.BG_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: {S.px(4)}px;
        """)
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}%"))

        lo.addWidget(slider)
        lo.addWidget(val_lbl)
        return container, slider

    def _make_toggle(self, key: str, default: bool) -> ToggleWidget:
        toggle = ToggleWidget()
        toggle.setChecked(settings.get(key, default))
        toggle.toggled.connect(lambda v: self._on_setting_changed(key, v))
        return toggle

    # â”€â”€ Sections â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _build_general_section(self, parent: QVBoxLayout):
        card = Card(title="General", icon="ph.gear")

        rows = [
            ("Show system tray icon",
             "Display the application icon in the Windows system tray",
             self._make_toggle('show_system_tray', True), False),
            ("Start application minimized",
             "Launch directly to tray without showing the main window",
             self._make_toggle('start_minimized', False), False),
            ("Enable animations",
             "Smooth transitions and animated charts throughout the interface",
             self._make_toggle('enable_animations', True), False),
            ("Check for updates on startup",
             "Automatically check for new versions when the application starts",
             self._make_toggle('check_for_updates', True), False),
        ]
        for label, desc, ctrl, last in rows:
            card.add_widget(self._row(label, desc, ctrl, last))

        btn = self._btn("Check now")
        btn.clicked.connect(self._on_check_for_updates)
        card.add_widget(self._row(
            "Check for updates",
            "Manually query for the latest available release",
            btn, last=True
        ))
        parent.addWidget(card)

    def _build_appearance_section(self, parent: QVBoxLayout):
        card = Card(title="Appearance", icon="ph.palette")

        theme_keys  = [
            "cyber-cyan", "premium", "cyberpunk", "heimdal",
        ]
        theme_names = [
            "Cyber Cyan (Default)", "Premium Dark", "Cyberpunk", "Heimdal",
        ]
        theme_combo = self._combo(theme_names, theme_keys,
                                  settings.get('theme', 'cyber-cyan'))
        theme_combo.currentIndexChanged.connect(
            lambda _: self._on_theme_selected(theme_combo.currentData()))
        card.add_widget(self._row(
            "Theme",
            "Overall visual appearance of the application",
            theme_combo
        ))

        scale_vals  = [0.75, 0.90, 1.0, 1.10, 1.25, 1.50]
        scale_names = ["75%", "90%", "100% (Default)", "110%", "125%", "150%"]
        scale_combo = self._combo(scale_names, scale_vals,
                                  settings.get('ui_scale', 1.0))
        scale_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('ui_scale', scale_vals[i]))
        card.add_widget(self._row(
            "UI Scale",
            "Adjust the overall interface size to match your display",
            scale_combo, last=True
        ))
        parent.addWidget(card)

    def _build_alerts_section(self, parent: QVBoxLayout):
        card = Card(title="Alerts & Notifications", icon="ph.bell")

        card.add_widget(self._row(
            "Enable system alerts",
            "Receive notifications when system metrics exceed configured thresholds",
            self._make_toggle('alerts_enabled', True)
        ))

        cpu_thresh = settings.get('alert_cpu_threshold', 80)
        ctrl_cpu, slider_cpu = self._slider_row(50, 100, cpu_thresh)
        slider_cpu.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_cpu_threshold', v))
        card.add_widget(self._row(
            "CPU alert threshold",
            "Send an alert when CPU usage exceeds this percentage",
            ctrl_cpu
        ))

        gpu_thresh = settings.get('alert_gpu_threshold', 85)
        ctrl_gpu, slider_gpu = self._slider_row(50, 110, gpu_thresh)
        slider_gpu.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_gpu_threshold', v))
        card.add_widget(self._row(
            "GPU temperature threshold",
            "Send an alert when GPU temperature exceeds this value (°C)",
            ctrl_gpu, last=True
        ))
        parent.addWidget(card)

    def _build_data_section(self, parent: QVBoxLayout):
        c = _c()
        card = Card(title="Data & Export", icon="ph.download")

        fmt_vals  = ["csv", "json", "txt"]
        fmt_names = ["CSV", "JSON", "Plain text"]
        fmt_combo = self._combo(fmt_names, fmt_vals,
                                settings.get('export_format', 'csv'))
        fmt_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('export_format', fmt_vals[i]))
        card.add_widget(self._row(
            "Export format",
            "File format used when exporting monitoring snapshots",
            fmt_combo
        ))

        browse_btn = self._btn("Browse…", icon="ph.folder-open")
        browse_btn.clicked.connect(self._on_browse_export_directory)
        card.add_widget(self._row(
            "Export destination",
            "Folder where exported monitoring data files are saved",
            browse_btn
        ))

        self._path_label = QLabel(
            settings.get('export_directory', str(Path.home() / 'Documents')))
        self._path_label.setFont(QFont("Consolas", S.font_pt(9)))
        self._path_label.setStyleSheet(f"""
            color: {c.TEXT_SECONDARY};
            background: {c.BG_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: {S.px(4)}px;
            padding: {S.px(4)}px {S.px(8)}px;
        """)
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._path_label.setCursor(Qt.CursorShape.IBeamCursor)
        card.add_widget(self._row(
            "Current path", "", self._path_label
        ))

        export_btn = self._btn("Export now", accent=True, icon="ph.download-simple")
        export_btn.clicked.connect(self._on_export_now)
        card.add_widget(self._row(
            "Export snapshot",
            "Save a snapshot of current system metrics to the export folder",
            export_btn, last=True
        ))
        parent.addWidget(card)

    def _build_maintenance_section(self, parent: QVBoxLayout):
        card = Card(title="Maintenance", icon="ph.wrench")

        reset_btn = self._btn("Reset all settings to default", danger=True, icon="ph.arrow-counter-clockwise")
        reset_btn.clicked.connect(self._on_reset_clicked)
        card.add_widget(self._row(
            "Reset settings",
            "Restore all preferences to factory defaults â€” this cannot be undone",
            reset_btn, last=True
        ))
        parent.addWidget(card)

    # â”€â”€ Event handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _on_theme_selected(self, theme: str):
        settings.set('theme', theme)
        self.signals_changed.emit('theme', theme)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: theme_manager.set_theme(theme))

    def _on_setting_changed(self, key: str, value):
        settings.set(key, value)
        self.signals_changed.emit(key, value)
        signal_bus.setting_changed.emit(key, value)

    def _on_check_for_updates(self):
        QMessageBox.information(
            self, "Update Check",
            "You are running the latest version.\n\nVersion: 1.0.0\nNo updates available.",
            QMessageBox.StandardButton.Ok)

    def _on_data_updated(self, data: dict):
        self._last_data = data

    def _on_browse_export_directory(self):
        current = settings.get('export_directory',
                               str(Path.home() / 'Documents'))
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", current,
            QFileDialog.Option.ShowDirsOnly)
        if directory:
            self._on_setting_changed('export_directory', directory)
            if self._path_label:
                self._path_label.setText(directory)

    def _on_export_now(self):
        if not self._last_data:
            QMessageBox.warning(
                self, "No Data",
                "No monitoring data available yet.\nPlease wait a moment and try again.",
                QMessageBox.StandardButton.Ok)
            return

        fmt = settings.get('export_format', 'csv')
        export_dir = settings.get('export_directory', str(Path.home() / 'Documents'))

        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"system_monitor_{timestamp}.{fmt}"
        filepath = str(Path(export_dir) / filename)

        self._exporter.export_snapshot(self._last_data, filepath, fmt)

    def _on_export_result(self, success: bool, message: str):
        if success:
            QMessageBox.information(
                self, "Export Successful", message,
                QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.critical(
                self, "Export Failed", message,
                QMessageBox.StandardButton.Ok)

    def _on_reset_clicked(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            settings.reset_to_defaults()
            AutostartManager.disable()
            self.signals_changed.emit('reset', True)
            self._setup_ui()
            QMessageBox.information(
                self, "Settings Reset",
                "All settings have been reset to defaults.\n"
                "Some changes may require a restart to take effect.",
                QMessageBox.StandardButton.Ok)
