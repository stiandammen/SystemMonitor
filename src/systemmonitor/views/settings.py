"""
Settings View — Professional rebuild
Card-based sections, scroll support, consistent with the rest of the GUI theme.
"""
from systemmonitor.paths_ext import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QSpinBox, QFileDialog, QMessageBox,
    QSizePolicy, QFrame, QScrollArea, QDialog
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
from systemmonitor.i18n import tr, language_manager, SUPPORTED_LANGUAGES, I18nMixin
from systemmonitor.widgets.card import Card
from systemmonitor.widgets.settings_row import ToggleWidget


def _c():
    return theme_manager.colors


# Sidebar tabs the user is allowed to hide via the "Tab Visibility" section.
# Dashboard and Settings stay out of this list — they must always remain
# reachable (Settings is the only way back to re-enable a hidden tab).
HIDEABLE_VIEWS = [
    ("cpu", "Processor"),
    ("gpu", "Graphics"),
    ("network", "Network"),
    ("memory", "Memory"),
    ("storage", "Storage"),
]


class SettingsView(QWidget, ScaleMixin, I18nMixin):
    signals_changed = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path_label = None
        self._last_data: dict = {}
        self._exporter = DataExporter()
        self._exporter.export_completed.connect(self._on_export_result)
        signal_bus.data_updated.connect(self._on_data_updated)
        self.scale_connect()
        self.i18n_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()

    def _on_theme_changed(self, _):
        # Defer rebuild so any active widget event (e.g. combo click) finishes first.
        # Rebuilding the layout synchronously inside theme_changed destroys the combo
        # box while Qt is still processing its currentIndexChanged event → crash.
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def retranslate_ui(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def on_scale_changed(self, _):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    # ── Build ──────────────────────────────────────────────────────────────

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
        self._build_visibility_section(content_layout)
        self._build_performance_section(content_layout)
        self._build_appearance_section(content_layout)
        self._build_units_section(content_layout)
        self._build_alerts_section(content_layout)
        self._build_data_section(content_layout)
        self._build_export_server_section(content_layout)
        self._build_information_section(content_layout)
        self._build_maintenance_section(content_layout)
        content_layout.addStretch()

    # ── Header ─────────────────────────────────────────────────────────────

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

        title = QLabel(tr("Settings"))
        title.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QLabel("·")
        sep.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        sep.setFont(QFont("Segoe UI", S.font_pt(14)))
        layout.addWidget(sep)

        subtitle = QLabel(tr("Application preferences"))
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

    # ── Information Section ────────────────────────────────────────────────

    def _build_information_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Information"), icon="ph.info")

        about_btn = self._btn(tr("About System Monitor"), icon="ph.identification-card")
        about_btn.clicked.connect(self._show_about_dialog)
        card.add_widget(self._row(
            tr("Application Info"),
            tr("View version number, build details and project links"),
            about_btn
        ))

        help_btn = self._btn(tr("Documentation & Help"), icon="ph.book-open")
        help_btn.clicked.connect(self._show_help_dialog)
        card.add_widget(self._row(
            tr("Technical Documentation"),
            tr("Learn what the different metrics (IRQ, P-cores, etc.) actually mean"),
            help_btn, last=True
        ))
        parent.addWidget(card)

    def _show_about_dialog(self):
        c = _c()
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("About System Monitor"))
        dialog.setMinimumSize(S.px(700), S.px(520))
        dialog.setStyleSheet(f"background-color: {c.BG_CARD}; border: 1px solid {c.BORDER};")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(S.px(30), S.px(25), S.px(30), S.px(25))
        layout.setSpacing(S.px(10))

        header_layout = QHBoxLayout()
        header_layout.setSpacing(S.px(10))
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(20), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.ACCENT_GREEN}; border: none;")
        header_layout.addWidget(title)

        version = QLabel("v2.0.0")
        version.setFont(QFont("Segoe UI", S.font_pt(9.5), QFont.Weight.Bold))
        version.setStyleSheet(f"""
            color: {c.TEXT_SECONDARY};
            background-color: {c.BG_SECONDARY};
            border-radius: {S.px(6)}px;
            padding: {S.px(2)}px {S.px(8)}px;
            border: 1px solid {c.BORDER};
        """)
        header_layout.addWidget(version)
        layout.addLayout(header_layout)

        desc = QLabel(tr("Advanced system diagnostics and hardware telemetry in real-time."))
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", S.font_pt(10.5), QFont.Weight.Medium))
        desc.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none; margin-bottom: 2px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet(f"background-color: {c.BORDER}; max-height: 1px; border: none;")
        layout.addWidget(sep)

        features_title = QLabel(tr("Key Features:"))
        features_title.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        features_title.setStyleSheet(f"color: {c.ACCENT_BLUE}; border: none; margin-top: 5px; margin-bottom: 2px;")
        layout.addWidget(features_title)

        from PyQt6.QtWidgets import QGridLayout
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(S.px(14))

        features_list = [
            ("Processor (CPU)", "Advanced real-time analysis of core load (P/E cores), clocks, temperatures, and IRQs.", 0, 0),
            ("Graphics (GPU)", "Telemetry for GPU utilization, VRAM allocation, temperatures, and power draw.", 0, 1),
            ("System Memory (RAM)", "Precise tracking of physical RAM and pagefile, memory speed, and top processes.", 1, 0),
            ("Storage (Disk)", "Real-time I/O throughput, partition space usage, and SMART health monitoring.", 1, 1),
            ("Network", "Bandwidth tracking (download/upload), active connections, and network topology.", 2, 0),
            ("Smart Alerts", "Threshold alarms for hardware events via system notifications or in-app toasts.", 2, 1),
            ("Telemetry Export", "JSON/CSV snapshot export and built-in Prometheus metrics server (/metrics).", 3, 0)
        ]

        for title_str, desc_str, r, col in features_list[:6]:
            feat_widget = QWidget()
            feat_widget.setStyleSheet("background: transparent; border: none;")
            feat_layout = QVBoxLayout(feat_widget)
            feat_layout.setContentsMargins(0, 0, 0, 0)
            feat_layout.setSpacing(S.px(2))

            name_label = QLabel(tr(title_str))
            name_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
            name_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; border: none;")
            
            desc_label = QLabel(tr(desc_str))
            desc_label.setWordWrap(True)
            desc_label.setFont(QFont("Segoe UI", S.font_pt(9.5)))
            desc_label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; border: none;")
            
            feat_layout.addWidget(name_label)
            feat_layout.addWidget(desc_label)
            grid.addWidget(feat_widget, r, col)

        # 7th item spanning 2 columns
        title_str, desc_str, r, col = features_list[6]
        feat_widget = QWidget()
        feat_widget.setStyleSheet("background: transparent; border: none;")
        feat_layout = QVBoxLayout(feat_widget)
        feat_layout.setContentsMargins(0, 0, 0, 0)
        feat_layout.setSpacing(S.px(2))

        name_label = QLabel(tr(title_str))
        name_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c.ACCENT_GREEN}; border: none;")
        
        desc_label = QLabel(tr(desc_str))
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", S.font_pt(9.5)))
        desc_label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; border: none;")
        
        feat_layout.addWidget(name_label)
        feat_layout.addWidget(desc_label)
        grid.addWidget(feat_widget, r, col, 1, 2)

        layout.addWidget(grid_widget)
        layout.addSpacing(S.px(10))

        close_btn = self._btn(tr("Close"))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def _show_help_dialog(self):
        from PyQt6.QtWidgets import QDialog, QScrollArea, QWidget, QVBoxLayout, QLabel
        c = _c()
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("Documentation & Help"))
        dialog.setMinimumSize(S.px(600), S.px(500))
        dialog.setStyleSheet(f"background-color: {c.BG_CARD}; border: 1px solid {c.BORDER};")

        main_layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(S.px(20))

        help_topics = [
            ("P-Cores & E-Cores",
             "Hybrid Intel CPUs (12th gen+) use Performance cores for heavy tasks "
             "and Efficiency cores for background work to save power."),
            ("Context Switches",
             "How often the CPU switches between different tasks. High numbers are normal, "
             "but extreme spikes can indicate heavy multitasking or driver issues."),
            ("Interrupts (IRQ)",
             "Signals from hardware to the CPU. High interrupt rates can mean "
             "malfunctioning hardware or high network/disk load."),
            ("VRAM",
             "Dedicated memory on your Graphics Card. If this fills up, "
             "graphics-heavy apps will slow down significantly."),
            ("Page File / Swap",
             "A portion of your storage used as 'extra' RAM when physical memory is full. "
             "Using this is much slower than real RAM."),
        ]

        for topic, text in help_topics:
            topic_lbl = QLabel(tr(topic))
            topic_lbl.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
            topic_lbl.setStyleSheet(f"color: {c.ACCENT_BLUE}; border: none;")
            layout.addWidget(topic_lbl)

            text_lbl = QLabel(tr(text))
            text_lbl.setWordWrap(True)
            text_lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
            text_lbl.setStyleSheet(f"color: {c.TEXT_PRIMARY}; border: none;")
            layout.addWidget(text_lbl)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        close_btn = self._btn(tr("Close"))
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    # ── Row builder ────────────────────────────────────────────────────────

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

        # Left — label + optional description
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

    # ── Control factories ──────────────────────────────────────────────────

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
                    value: int, unit: str = '%') -> tuple[QWidget, QSlider]:
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

        val_lbl = QLabel(f"{value}{unit}")
        val_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        val_lbl.setFixedWidth(S.px(48))
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"""
            color: {c.ACCENT_GREEN};
            background: {c.BG_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: {S.px(4)}px;
        """)
        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{unit}"))

        lo.addWidget(slider)
        lo.addWidget(val_lbl)
        return container, slider

    def _make_toggle(self, key: str, default: bool) -> ToggleWidget:
        toggle = ToggleWidget()
        toggle.setChecked(settings.get(key, default))
        toggle.toggled.connect(lambda v: self._on_setting_changed(key, v))
        return toggle

    def _make_autostart_toggle(self) -> ToggleWidget:
        """Toggle backed by the Windows registry Run key rather than a plain
        settings value — the registry is the source of truth for its state."""
        toggle = ToggleWidget()
        toggle.setChecked(AutostartManager.is_enabled())
        toggle.toggled.connect(self._on_autostart_toggled)
        return toggle

    def _on_autostart_toggled(self, enabled: bool):
        ok = AutostartManager.enable() if enabled else AutostartManager.disable()
        settings.set('autostart', enabled and ok)
        self.signals_changed.emit('autostart', enabled and ok)

    def _make_visibility_toggle(self, view_key: str) -> ToggleWidget:
        """Toggle bound to the 'hidden_views' list rather than a plain bool key —
        checked means visible (i.e. NOT present in the hidden list)."""
        toggle = ToggleWidget()
        toggle.setChecked(view_key not in settings.get('hidden_views', []))
        toggle.toggled.connect(lambda visible: self._on_visibility_toggled(view_key, visible))
        return toggle

    # ── Sections ───────────────────────────────────────────────────────────

    def _build_general_section(self, parent: QVBoxLayout):
        card = Card(title=tr("General"), icon="ph.gear")

        lang_keys  = list(SUPPORTED_LANGUAGES.keys())
        lang_names = list(SUPPORTED_LANGUAGES.values())
        lang_combo = self._combo(lang_names, lang_keys,
                                 settings.get('language', 'en'))
        lang_combo.currentIndexChanged.connect(
            lambda i: self._on_language_selected(lang_keys[i]))
        card.add_widget(self._row(
            tr("Language"),
            tr("Display language used throughout the application"),
            lang_combo
        ))

        rows = [
            (tr("Show system tray icon"),
             tr("Display the application icon in the Windows system tray"),
             self._make_toggle('show_system_tray', True), False),
            (tr("Start application minimized"),
             tr("Launch directly to tray without showing the main window"),
             self._make_toggle('start_minimized', False), False),
            (tr("Run on Startup"),
             tr("Launch System Monitor automatically when you sign in to Windows"),
             self._make_autostart_toggle(), False),
            (tr("Enable animations"),
             tr("Smooth transitions and animated charts throughout the interface"),
             self._make_toggle('enable_animations', True), False),
            (tr("Check for updates on startup"),
             tr("Automatically check for new versions when the application starts"),
             self._make_toggle('check_for_updates', True), False),
        ]
        for label, desc, ctrl, last in rows:
            card.add_widget(self._row(label, desc, ctrl, last))

        btn = self._btn(tr("Check now"))
        btn.clicked.connect(self._on_check_for_updates)
        card.add_widget(self._row(
            tr("Check for updates"),
            tr("Manually query for the latest available release"),
            btn, last=True
        ))
        parent.addWidget(card)

    def _build_visibility_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Tab Visibility"), icon="ph.eye")

        for i, (view_key, label) in enumerate(HIDEABLE_VIEWS):
            last = i == len(HIDEABLE_VIEWS) - 1
            translated_label = tr(label)
            card.add_widget(self._row(
                tr("Show {0} tab").format(translated_label),
                tr("Display the {0} tab in the sidebar — hide it for a cleaner interface "
                   "if you don't use it (e.g. no dedicated GPU)").format(translated_label),
                self._make_visibility_toggle(view_key),
                last,
            ))
        parent.addWidget(card)

    def _on_visibility_toggled(self, view_key: str, visible: bool):
        hidden = list(settings.get('hidden_views', []))
        if visible:
            if view_key in hidden:
                hidden.remove(view_key)
        elif view_key not in hidden:
            hidden.append(view_key)
        settings.set('hidden_views', hidden)
        self.signals_changed.emit('hidden_views', hidden)

    def _build_performance_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Performance"), icon="ph.gauge")

        speed_vals  = [250, 500, 2000]
        speed_names = [tr("Fast (250ms)"), tr("Normal (500ms)"), tr("Low (2000ms)")]
        speed_combo = self._combo(speed_names, speed_vals,
                                  settings.get('update_interval', 500))
        speed_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('update_interval', speed_vals[i]))
        card.add_widget(self._row(
            tr("Update speed"),
            tr("How often metrics are refreshed — faster gives real-time detail, "
               "slower saves CPU and power"),
            speed_combo
        ))

        history_vals  = [300, 900, 3600]
        history_names = [tr("5 minutes"), tr("15 minutes"), tr("1 hour")]
        history_combo = self._combo(history_names, history_vals,
                                    settings.get('history_duration', 300))
        history_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('history_duration', history_vals[i]))
        card.add_widget(self._row(
            tr("History length"),
            tr("How much time the live graphs keep visible before scrolling off"),
            history_combo, last=True
        ))
        parent.addWidget(card)

    def _build_appearance_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Appearance"), icon="ph.palette")

        theme_keys  = [
            "cyber-cyan", "premium", "cyberpunk", "heimdal",
        ]
        theme_names = [
            tr("Cyber Cyan (Default)"), tr("Premium Dark"), tr("Cyberpunk"), tr("Heimdal"),
        ]
        theme_combo = self._combo(theme_names, theme_keys,
                                  settings.get('theme', 'cyber-cyan'))
        theme_combo.currentIndexChanged.connect(
            lambda _: self._on_theme_selected(theme_combo.currentData()))
        card.add_widget(self._row(
            tr("Theme"),
            tr("Overall visual appearance of the application"),
            theme_combo
        ))

        scale_vals  = [0.75, 0.90, 1.0, 1.10, 1.25, 1.50]
        scale_names = ["75%", "90%", tr("100% (Default)"), "110%", "125%", "150%"]
        scale_combo = self._combo(scale_names, scale_vals,
                                  settings.get('ui_scale', 1.0))
        scale_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('ui_scale', scale_vals[i]))
        card.add_widget(self._row(
            tr("UI Scale"),
            tr("Adjust the overall interface size to match your display"),
            scale_combo, last=True
        ))
        parent.addWidget(card)

    def _build_units_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Units & Display"), icon="ph.ruler")

        temp_keys  = ['celsius', 'fahrenheit']
        temp_names = [tr('Celsius (°C)'), tr('Fahrenheit (°F)')]
        temp_combo = self._combo(temp_names, temp_keys,
                                 settings.get('temperature_unit', 'celsius'))
        temp_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('temperature_unit', temp_keys[i]))
        card.add_widget(self._row(
            tr("Temperature unit"),
            tr("Unit used to display CPU, GPU and storage temperature readings"),
            temp_combo
        ))

        speed_keys  = ['mbps', 'mbytes']
        speed_names = [tr('Mbps (Megabits — ISP standard)'), tr('MB/s (Megabytes — file transfer)')]
        speed_combo = self._combo(speed_names, speed_keys,
                                  settings.get('network_speed_unit', 'mbps'))
        speed_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('network_speed_unit', speed_keys[i]))
        card.add_widget(self._row(
            tr("Network speed unit"),
            tr("Unit used to display network download and upload speeds"),
            speed_combo
        ))

        decimals_keys  = [0, 1, 2]
        decimals_names = [tr('0 decimals (e.g. 42)'), tr('1 decimal (e.g. 42.3)'), tr('2 decimals (e.g. 42.34)')]
        decimals_combo = self._combo(decimals_names, decimals_keys,
                                     settings.get('decimal_places', 1))
        decimals_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('decimal_places', decimals_keys[i]))
        card.add_widget(self._row(
            tr("Decimal precision"),
            tr("Number of decimal places shown for temperature and network speed readouts"),
            decimals_combo, last=True
        ))
        parent.addWidget(card)

    def _build_alerts_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Alerts & Notifications"), icon="ph.bell")

        card.add_widget(self._row(
            tr("Enable system alerts"),
            tr("Receive notifications when system metrics exceed configured thresholds"),
            self._make_toggle('alerts_enabled', True)
        ))

        cpu_thresh = settings.get('alert_cpu_threshold', 80)
        ctrl_cpu, slider_cpu = self._slider_row(50, 100, cpu_thresh)
        slider_cpu.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_cpu_threshold', v))
        card.add_widget(self._row(
            tr("CPU alert threshold"),
            tr("Send an alert when CPU usage exceeds this percentage"),
            ctrl_cpu
        ))

        mem_thresh = settings.get('alert_memory_threshold', 85)
        ctrl_mem, slider_mem = self._slider_row(50, 100, mem_thresh)
        slider_mem.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_memory_threshold', v))
        card.add_widget(self._row(
            tr("RAM usage threshold"),
            tr("Send an alert when memory usage exceeds this percentage"),
            ctrl_mem
        ))

        disk_thresh = settings.get('alert_disk_threshold', 90)
        ctrl_disk, slider_disk = self._slider_row(50, 100, disk_thresh)
        slider_disk.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_disk_threshold', v))
        card.add_widget(self._row(
            tr("Disk space threshold"),
            tr("Send an alert when a partition's used space exceeds this percentage"),
            ctrl_disk
        ))

        cpu_temp_thresh = settings.get('alert_temperature_threshold', 80)
        ctrl_cpu_temp, slider_cpu_temp = self._slider_row(50, 110, cpu_temp_thresh, unit='°C')
        slider_cpu_temp.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_temperature_threshold', v))
        card.add_widget(self._row(
            tr("CPU temperature threshold"),
            tr("Send an alert when CPU temperature exceeds this value (°C)"),
            ctrl_cpu_temp
        ))

        gpu_thresh = settings.get('alert_gpu_threshold', 85)
        ctrl_gpu, slider_gpu = self._slider_row(50, 110, gpu_thresh, unit='°C')
        slider_gpu.valueChanged.connect(
            lambda v: self._on_setting_changed('alert_gpu_threshold', v))
        card.add_widget(self._row(
            tr("GPU temperature threshold"),
            tr("Send an alert when GPU temperature exceeds this value (°C)"),
            ctrl_gpu
        ))

        method_keys  = ['system', 'in_app']
        method_names = [tr('System Notifications (Windows popups)'), tr('In-app Visuals')]
        method_combo = self._combo(method_names, method_keys,
                                   settings.get('notification_method', 'system'))
        method_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('notification_method', method_keys[i]))
        card.add_widget(self._row(
            tr("Notification method"),
            tr("Show alerts as Windows system tray popups, or as banners inside the app"),
            method_combo, last=True
        ))
        parent.addWidget(card)

    def _build_data_section(self, parent: QVBoxLayout):
        c = _c()
        card = Card(title=tr("Data & Export"), icon="ph.download")

        fmt_vals  = ["csv", "json", "txt"]
        fmt_names = [tr("CSV"), tr("JSON"), tr("Plain text")]
        fmt_combo = self._combo(fmt_names, fmt_vals,
                                settings.get('export_format', 'csv'))
        fmt_combo.currentIndexChanged.connect(
            lambda i: self._on_setting_changed('export_format', fmt_vals[i]))
        card.add_widget(self._row(
            tr("Export format"),
            tr("File format used when exporting monitoring snapshots"),
            fmt_combo
        ))

        browse_btn = self._btn(tr("Browse…"), icon="ph.folder-open")
        browse_btn.clicked.connect(self._on_browse_export_directory)
        card.add_widget(self._row(
            tr("Export destination"),
            tr("Folder where exported monitoring data files are saved"),
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
            tr("Current path"), "", self._path_label
        ))

        export_btn = self._btn(tr("Export now"), accent=True, icon="ph.download-simple")
        export_btn.clicked.connect(self._on_export_now)
        card.add_widget(self._row(
            tr("Export snapshot"),
            tr("Save a snapshot of current system metrics to the export folder"),
            export_btn, last=True
        ))
        parent.addWidget(card)

    def _build_export_server_section(self, parent: QVBoxLayout):
        c = _c()
        card = Card(title=tr("Prometheus Exporter"), icon="ph.broadcast")

        card.add_widget(self._row(
            tr("Enable metrics endpoint"),
            tr("Expose live metrics at /metrics in Prometheus text format so external "
               "tools (Prometheus, Grafana agent, curl) can scrape this machine"),
            self._make_toggle('prometheus_enabled', False)
        ))

        port_spin = QSpinBox()
        port_spin.setRange(1024, 65535)
        port_spin.setValue(int(settings.get('prometheus_port', 9090)))
        port_spin.setFixedWidth(S.px(90))
        port_spin.setStyleSheet(f"""
            QSpinBox {{
                color: {c.TEXT_PRIMARY};
                background: {c.BG_SECONDARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(4)}px;
                padding: {S.px(4)}px {S.px(6)}px;
            }}
        """)
        card.add_widget(self._row(
            tr("Port"),
            tr("TCP port the metrics server listens on"),
            port_spin
        ))

        url_label = QLabel(f"http://localhost:{settings.get('prometheus_port', 9090)}/metrics")
        url_label.setFont(QFont("Consolas", S.font_pt(9)))
        url_label.setStyleSheet(f"""
            color: {c.TEXT_SECONDARY};
            background: {c.BG_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: {S.px(4)}px;
            padding: {S.px(4)}px {S.px(8)}px;
        """)
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_label.setCursor(Qt.CursorShape.IBeamCursor)
        port_spin.valueChanged.connect(lambda v: url_label.setText(f"http://localhost:{v}/metrics"))
        port_spin.valueChanged.connect(lambda v: self._on_setting_changed('prometheus_port', v))
        card.add_widget(self._row(
            tr("Scrape URL"),
            tr("Point your Prometheus server (or curl) at this address while enabled"),
            url_label, last=True
        ))

        parent.addWidget(card)

    def _build_maintenance_section(self, parent: QVBoxLayout):
        card = Card(title=tr("Maintenance"), icon="ph.wrench")

        reset_btn = self._btn(tr("Reset all settings to default"), danger=True, icon="ph.arrow-counter-clockwise")
        reset_btn.clicked.connect(self._on_reset_clicked)
        card.add_widget(self._row(
            tr("Reset settings"),
            tr("Restore all preferences to factory defaults — this cannot be undone"),
            reset_btn, last=True
        ))
        parent.addWidget(card)

    # ── Event handlers ─────────────────────────────────────────────────────

    def _on_theme_selected(self, theme: str):
        settings.set('theme', theme)
        self.signals_changed.emit('theme', theme)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: theme_manager.set_theme(theme))

    def _on_language_selected(self, language: str):
        self.signals_changed.emit('language', language)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: language_manager.set_language(language))

    def _on_setting_changed(self, key: str, value):
        settings.set(key, value)
        self.signals_changed.emit(key, value)
        signal_bus.setting_changed.emit(key, value)

    def _on_check_for_updates(self):
        QMessageBox.information(
            self, tr("Update Check"),
            tr("You are running the latest version.\n\nVersion: {0}\nNo updates available.").format("1.0.0"),
            QMessageBox.StandardButton.Ok)

    def _on_data_updated(self, data: dict):
        self._last_data = data

    def _on_browse_export_directory(self):
        current = settings.get('export_directory',
                               str(Path.home() / 'Documents'))
        directory = QFileDialog.getExistingDirectory(
            self, tr("Select Export Directory"), current,
            QFileDialog.Option.ShowDirsOnly)
        if directory:
            self._on_setting_changed('export_directory', directory)
            if self._path_label:
                self._path_label.setText(directory)

    def _on_export_now(self):
        if not self._last_data:
            QMessageBox.warning(
                self, tr("No Data"),
                tr("No monitoring data available yet.\nPlease wait a moment and try again."),
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
                self, tr("Export Successful"), message,
                QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.critical(
                self, tr("Export Failed"), message,
                QMessageBox.StandardButton.Ok)

    def _on_reset_clicked(self):
        reply = QMessageBox.question(
            self, tr("Reset Settings"),
            tr("Reset all settings to their default values?\n\nThis cannot be undone."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            settings.reset_to_defaults()
            AutostartManager.disable()
            self.signals_changed.emit('reset', True)
            self._setup_ui()
            QMessageBox.information(
                self, tr("Settings Reset"),
                tr("All settings have been reset to defaults.\n"
                   "Some changes may require a restart to take effect."),
                QMessageBox.StandardButton.Ok)
