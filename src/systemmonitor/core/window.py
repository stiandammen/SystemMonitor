"""
Main Window - Application main window
Professional enterprise-grade design with responsive layout and overlay mode
"""
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QEvent, QTimer, QSize, QRectF
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QIcon, QCursor, QBrush

from systemmonitor.widgets.glass_sidebar import GlassSidebar
from systemmonitor.widgets.responsive import OverlayWidget
from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin, LayoutMode
from systemmonitor.config import settings
from systemmonitor.utils.logger import get_logger, LogCategory, log_info, log_debug
from systemmonitor.i18n import tr


def _cap(scaled: int, maximum: int) -> int:
    """Return scaled value capped at maximum — prevents oversized chrome on 5K."""
    return min(scaled, maximum)


class WinControlBtn(QWidget):
    """
    Window control button (minimize / maximize / restore / close) drawn
    entirely with QPainter — no Unicode glyphs, identical on every OS/font.
    """

    clicked = __import__('PyQt6.QtCore', fromlist=['pyqtSignal']).pyqtSignal()

    # kind: "min" | "max" | "restore" | "close"
    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self._kind = kind
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(_cap(S.px(34), 40), _cap(S.px(26), 30))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_kind(self, kind: str):
        self._kind = kind
        self.update()

    # ── events ────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
            event.accept()

    # ── painting ──────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = theme_manager.colors
        w, h = self.width(), self.height()
        r = S.px(6)

        # Background
        if self._hovered:
            bg = QColor(c.ACCENT_RED if self._kind == "close" else c.BG_HOVER)
            p.setBrush(QBrush(bg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, w, h, r, r)

        # Icon colour
        if self._hovered and self._kind == "close":
            icon_color = QColor("#ffffff")
        elif self._hovered:
            icon_color = QColor(c.TEXT_PRIMARY)
        else:
            icon_color = QColor(c.TEXT_MUTED)

        pen = QPen(icon_color)
        pen.setWidthF(_cap(S.px(2), 2))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = w / 2, h / 2
        sz = _cap(S.px(8), 9)    # icon bounding box half-size
        thin = _cap(S.px(7), 8)

        if self._kind == "min":
            # Horizontal line, centred, sitting at 65 % height
            y = cy + S.px(3)
            p.drawLine(int(cx - thin), int(y), int(cx + thin), int(y))

        elif self._kind == "max":
            # Rectangle outline
            rect = QRectF(cx - sz, cy - sz, sz * 2, sz * 2)
            p.drawRect(rect)

        elif self._kind == "restore":
            # Back rectangle (offset top-right)
            off = S.px(3)
            back = QRectF(cx - sz + off, cy - sz - off, sz * 2 - off, sz * 2 - off)
            p.drawRect(back)
            # Front rectangle (offset bottom-left), filled to hide back
            front_bg = QColor(c.ACCENT_RED if self._hovered else c.BG_CARD)
            p.setBrush(QBrush(front_bg))
            front = QRectF(cx - sz - off + S.px(1), cy - sz + off + S.px(1),
                           sz * 2 - off, sz * 2 - off)
            p.drawRect(front)
            p.setBrush(Qt.BrushStyle.NoBrush)

        elif self._kind == "close":
            # X
            p.drawLine(int(cx - sz), int(cy - sz), int(cx + sz), int(cy + sz))
            p.drawLine(int(cx + sz), int(cy - sz), int(cx - sz), int(cy + sz))

        p.end()


class TitleBar(QWidget, ScaleMixin):
    """Premium glass title bar with modern controls - responsive"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._maximized = False
        self._drag_position = None
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        if self._parent and self._parent._in_drag_resize:
            return
        self._setup_ui()
        self.update()

    def closeEvent(self, event):
        self.scale_disconnect()
        super().closeEvent(event)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setMinimumHeight(S.px(40))
        self.setMaximumHeight(S.px(48))

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                background-color: rgba(26, 30, 53, 0.85);
                border: none;
                border-bottom: 1px solid rgba(74, 108, 247, 0.2);
            """)
        else:
            self.setStyleSheet(f"""
                background-color: {colors.GLASS_BG};
                border: none;
                border-bottom: 1px solid {colors.GLASS_BORDER};
            """)

        # 1. Initialize layout if missing
        if self.layout() is None:
            layout = QHBoxLayout()
            self.setLayout(layout)
            
            self._title_label = QLabel("System Monitor")
            self._title_label.setCursor(Qt.CursorShape.SizeAllCursor)
            layout.addWidget(self._title_label)
            layout.addStretch()
            self._create_buttons(layout)
        
        # 2. Update properties
        layout = self.layout()
        layout.setContentsMargins(S.px(12), 0, S.px(8), 0)
        layout.setSpacing(S.px(6))
        
        if hasattr(self, '_title_label'):
            self._title_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))
            self._title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")

    def _create_buttons(self, layout):
        min_btn = WinControlBtn("min")
        min_btn.clicked.connect(self._minimize_window)
        layout.addWidget(min_btn)

        self._max_btn = WinControlBtn("max")
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        close_btn = WinControlBtn("close")
        close_btn.clicked.connect(self._close_window)
        layout.addWidget(close_btn)

    def _minimize_window(self):
        if self._parent:
            self._parent.showMinimized()

    def _toggle_maximize(self):
        if self._parent:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.set_kind("max")
                self._maximized = False
            else:
                self._parent.showMaximized()
                self._max_btn.set_kind("restore")
                self._maximized = True

    def _close_window(self):
        if self._parent:
            self._parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            self._parent._in_drag_resize = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.set_kind("max")
                self._maximized = False
                self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            self._parent.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            QTimer.singleShot(50, lambda: self._parent and setattr(self._parent, '_in_drag_resize', False))
            event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self._parent:
                if self._parent.isMaximized():
                    self._max_btn.set_kind("restore")
                    self._maximized = True
                else:
                    self._max_btn.set_kind("max")
                    self._maximized = False
        super().changeEvent(event)


class TopHeader(QWidget, ScaleMixin):
    """Professional top header bar - responsive"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._maximized = False
        self._drag_position = None
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        if self._parent and self._parent._in_drag_resize:
            return
        self._apply_theme()
        self.update()

    def closeEvent(self, event):
        self.scale_disconnect()
        super().closeEvent(event)

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()

    def _setup_ui(self):
        self.setMinimumHeight(_cap(S.px(36), 40))
        self.setMaximumHeight(_cap(S.px(42), 46))

        if not self.layout():
            layout = QHBoxLayout()
            layout.setContentsMargins(_cap(S.px(14), 16), 0, _cap(S.px(6), 8), 0)
            layout.setSpacing(_cap(S.px(8), 10))
            self.setLayout(layout)
            self._build_contents(layout)

        self._apply_theme()

    def _build_contents(self, layout):
        icon_sz = _cap(S.px(26), 30)
        self._icon_container = QFrame()
        self._icon_container.setFixedSize(icon_sz, icon_sz)
        self._icon_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_container.setLayout(icon_layout)

        icon_label = QLabel("SM")
        icon_label.setFont(QFont("Segoe UI", _cap(S.font_pt(9), 10), QFont.Weight.Bold))
        icon_label.setStyleSheet("color: white;")
        icon_layout.addWidget(icon_label)
        layout.addWidget(self._icon_container)

        self._title_label = QLabel("System Monitor")
        self._title_label.setFont(QFont("Segoe UI", _cap(S.font_pt(10), 11), QFont.Weight.Medium))
        self._title_label.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(self._title_label)

        spacer = QWidget()
        spacer.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(spacer, stretch=1)

        self._min_btn = WinControlBtn("min")
        self._min_btn.clicked.connect(self._minimize_window)
        layout.addWidget(self._min_btn)

        self._max_btn = WinControlBtn("max")
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        self._close_btn = WinControlBtn("close")
        self._close_btn.clicked.connect(self._close_window)
        layout.addWidget(self._close_btn)

    def _apply_theme(self):
        colors = theme_manager.colors
        is_heimdal = theme_manager.current_theme == "heimdal"

        if is_heimdal:
            self.setStyleSheet("""
                background-color: #12152A;
                border: none;
                border-bottom: 1px solid rgba(74, 108, 247, 0.2);
            """)
        else:
            self.setStyleSheet(f"""
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-bottom: 1px solid {colors.BORDER};
            """)

        if hasattr(self, '_title_label'):
            self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")

        if hasattr(self, '_icon_container'):
            self._icon_container.setStyleSheet(f"""
                background-color: {colors.ACCENT_GREEN};
                border-radius: {_cap(S.px(6), 7)}px;
            """)

        # WinControlBtn reads theme_manager.colors directly in paintEvent — just repaint
        for btn in [getattr(self, '_min_btn', None),
                    getattr(self, '_max_btn', None),
                    getattr(self, '_close_btn', None)]:
            if btn is not None:
                btn.update()

    def _minimize_window(self):
        if self._parent:
            self._parent.showMinimized()

    def _toggle_maximize(self):
        if self._parent:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.set_kind("max")
                self._maximized = False
            else:
                self._parent.showMaximized()
                self._max_btn.set_kind("restore")
                self._maximized = True

    def _close_window(self):
        if self._parent:
            self._parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            self._parent._in_drag_resize = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.set_kind("max")
                self._maximized = False
                self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            self._parent.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            QTimer.singleShot(50, lambda: self._parent and setattr(self._parent, '_in_drag_resize', False))
            event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self._parent:
                if self._parent.isMaximized():
                    self._max_btn.set_kind("restore")
                    self._maximized = True
                else:
                    self._max_btn.set_kind("max")
                    self._maximized = False
        super().changeEvent(event)


class MainWindow(QMainWindow, ScaleMixin):
    """Main application window - responsive enterprise design with overlay support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position = None
        self._in_drag_resize = False
        self._pending_scale_update = False
        self._view_cache = {}
        self._active_view = None
        self._overlay_mode = False
        self._overlay_widget = None
        self._alert_toast = None
        self._resize_debounce_timer = QTimer()
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_debounce_timer.timeout.connect(self._on_debounced_resize)

        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self._preload_overview()

        # Check for updates in background on startup (if enabled)
        from systemmonitor.config import settings as app_settings
        if app_settings.get('check_for_updates', True):
            QTimer.singleShot(5000, self._check_for_updates_startup)

    def _preload_overview(self):
        self._get_view("overview")

    def _check_for_updates_startup(self):
        from systemmonitor.utils.updater import UpdateCheckerThread
        self._startup_updater = UpdateCheckerThread(self)
        self._startup_updater.check_finished.connect(self._on_startup_update_check_finished)
        self._startup_updater.start()

    def _on_startup_update_check_finished(self, available: bool, info: dict):
        if available and not self.isMinimized() and self.isVisible():
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, tr("Update Available"),
                tr("A new version ({0}) of System Monitor is available.\n\nRelease notes:\n{1}\n\nDo you want to download and install it now?").format(info["version"], info["release_notes"]),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._switch_view("settings")
                settings_view = self._get_view("settings")
                if hasattr(settings_view, "start_update_download"):
                    settings_view.start_update_download(info)

    def closeEvent(self, event):
        """Hide to the system tray instead of quitting — a monitoring tool
        should keep collecting in the background when the window is closed."""
        from systemmonitor.config import settings as app_settings
        from PyQt6.QtWidgets import QSystemTrayIcon

        if app_settings.get('show_system_tray', True) and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
        else:
            super().closeEvent(event)

    def _get_view(self, view_name: str) -> QWidget:
        if view_name not in self._view_cache:
            from systemmonitor.views.overview_page import OverviewPage
            from systemmonitor.views.cpu import CPUView
            from systemmonitor.views.gpu import GPUView
            from systemmonitor.views.network import NetworkView
            from systemmonitor.views.memory import MemoryView
            from systemmonitor.views.storage import StorageView
            from systemmonitor.views.logs import LogView
            from systemmonitor.views.settings import SettingsView
            from systemmonitor.widgets.module_launcher import ModuleLauncherPage

            view_classes = {
                "overview": OverviewPage,
                "cpu": CPUView,
                "gpu": GPUView,
                "network": NetworkView,
                "memory": MemoryView,
                "storage": StorageView,
                "logs": LogView,
                "settings": SettingsView,
                "home": ModuleLauncherPage,
            }

            if view_name in view_classes:
                view = view_classes[view_name]()
                self._view_cache[view_name] = view
                self._content.addWidget(view)
                if view_name == 'settings' and hasattr(view, 'signals_changed'):
                    view.signals_changed.connect(self._on_settings_changed)
                if view_name == 'home' and hasattr(view, 'module_selected'):
                    view.module_selected.connect(self._switch_view)

        return self._view_cache[view_name]

    def _on_settings_changed(self, key: str, value):
        if key == 'ui_scale':
            from systemmonitor.scaler import S
            S.set_user_scale(float(value))
        elif key == 'hidden_views':
            hidden = set(value or [])
            if hasattr(self, '_sidebar'):
                self._sidebar.set_hidden_views(hidden)
            if self._active_view in hidden:
                self._sidebar.set_active_view('overview')
                self._switch_view('overview')
        elif key == 'home_screen_style':
            if hasattr(self, '_sidebar'):
                self._sidebar.set_home_screen_enabled(value == 'launcher')

    def show_alert_toast(self, message: str, level: str = 'warning'):
        """Show an in-app banner for a triggered alert (the 'In-app Visuals'
        notification method, as an alternative to system tray popups)."""
        if self._alert_toast is None:
            from systemmonitor.widgets.alert_toast import AlertToast
            self._alert_toast = AlertToast(self)
        self._alert_toast.show_alert(message, level)

    def on_scale_changed(self, factor: float):
        if self._in_drag_resize:
            self._pending_scale_update = True
            return
        self._pending_scale_update = False
        log_debug(LogCategory.WINDOW, f"Scale changed: {factor}")
        self._apply_scale_to_frame()

    def on_layout_mode_changed(self, mode):
        if self._in_drag_resize:
            return
        if mode == LayoutMode.COMPACT:
            if hasattr(self, '_sidebar') and not self._sidebar._collapsed:
                self._sidebar._toggle_collapse()
        else:
            if hasattr(self, '_sidebar') and self._sidebar._collapsed:
                self._sidebar._toggle_collapse()

    def _apply_scale_to_frame(self):
        """Update only the window frame elements — views rebuild themselves via ScaleMixin."""
        self.setMinimumSize(S.px(700), S.px(500))
        if hasattr(self, '_top_header'):
            self._top_header._setup_ui()
        if hasattr(self, '_resize_corner'):
            self._resize_corner.setMinimumSize(S.px(16), S.px(16))
            self._resize_corner.setMaximumSize(S.px(24), S.px(24))
            self._update_resize_corner_position()

    def _on_theme_changed(self, theme_name: str):
        try:
            QApplication.instance().setStyleSheet(theme_manager.get_stylesheet())
            c = theme_manager.colors

            if hasattr(self, '_top_header'):
                self._top_header._apply_theme()

            if hasattr(self, '_content'):
                if theme_name == "heimdal":
                    self._content.setStyleSheet(f"""
                        QStackedWidget {{
                            background-color: {c.BG_PRIMARY};
                            border-left: 1px solid rgba(74, 108, 247, 0.2);
                        }}
                    """)
                else:
                    self._content.setStyleSheet(f"""
                        QStackedWidget {{
                            background-color: {c.BG_PRIMARY};
                        }}
                    """)

            if hasattr(self, '_sidebar'):
                self._sidebar._apply_theme()
                for item in self._sidebar._items.values():
                    item._on_theme_changed(theme_name)

            if hasattr(self, '_resize_corner'):
                self._resize_corner._on_theme_changed(theme_name)

            if hasattr(self, '_view_cache'):
                for view in self._view_cache.values():
                    view.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Theme change error: {e}")

    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("System Monitor")
        try:
            import sys
            import os
            from PyQt6.QtGui import QIcon
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(base_dir, "assets", "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        screen = self.screen()
        if screen:
            geom = screen.availableGeometry()
            w = int(geom.width() * 0.85)
            h = int(geom.height() * 0.85)
            x = geom.x() + (geom.width() - w) // 2
            y = geom.y() + (geom.height() - h) // 2
            self.setGeometry(x, y, w, h)
        else:
            self.setGeometry(100, 100, 1400, 900)

        self.setMinimumSize(S.px(700), S.px(500))

        colors = theme_manager.colors

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        self._top_header = TopHeader(self)
        main_layout.addWidget(self._top_header)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addLayout(content_layout)

        self._sidebar = self._create_sidebar()
        content_layout.addWidget(self._sidebar)

        self._content = QStackedWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if theme_manager.current_theme == "heimdal":
            self._content.setStyleSheet(f"""
                QStackedWidget {{
                    background-color: {colors.BG_PRIMARY};
                    border-left: 1px solid rgba(74, 108, 247, 0.2);
                }}
            """)
        else:
            self._content.setStyleSheet(f"""
                QStackedWidget {{
                    background-color: {colors.BG_PRIMARY};
                }}
            """)
        content_layout.addWidget(self._content, stretch=1)

        initial_view = "home" if settings.get('home_screen_style', 'sidebar') == 'launcher' else "overview"
        initial_widget = self._get_view(initial_view)
        self._content.setCurrentWidget(initial_widget)
        self._active_view = initial_view
        if hasattr(self, '_sidebar'):
            self._sidebar.set_active_view(initial_view)
            self._sidebar.setVisible(initial_view != 'home')

        self._resize_corner = ResizeCorner(self)
        self._update_resize_corner_position()

    def _update_resize_corner_position(self):
        if hasattr(self, '_resize_corner'):
            self._resize_corner.move(self.width() - 16, self.height() - 16)

    def _create_sidebar(self):
        sidebar = GlassSidebar()
        sidebar.view_selected.connect(self._switch_view)
        sidebar.set_hidden_views(settings.get('hidden_views', []))
        if S.is_compact():
            sidebar._collapsed = True
            sidebar.setFixedWidth(S.px(64))
        return sidebar

    def _switch_view(self, view_name: str):
        view = self._get_view(view_name)
        self._content.setCurrentWidget(view)
        self._active_view = view_name
        if hasattr(self, '_sidebar'):
            self._sidebar.set_active_view(view_name)
            self._sidebar.setVisible(view_name != 'home')
        log_info(LogCategory.UI, f"Switched to view: {view_name}")

    def update_data(self, data: dict):
        if self._overlay_mode and self._overlay_widget:
            self._overlay_widget.update_data(data)
            return

        if self._active_view and self._active_view in self._view_cache:
            view = self._view_cache[self._active_view]
            if hasattr(view, 'update_data'):
                view.update_data(data)

    def toggle_overlay_mode(self):
        if self._overlay_mode:
            self._exit_overlay_mode()
        else:
            self._enter_overlay_mode()

    def _enter_overlay_mode(self):
        self._overlay_mode = True
        self._overlay_widget = OverlayWidget()
        self._overlay_widget.show()
        self.hide()

    def _exit_overlay_mode(self):
        self._overlay_mode = False
        if self._overlay_widget:
            self._overlay_widget.close()
            self._overlay_widget = None
        self.showNormal()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.globalY() < self._top_header.height():
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self._in_drag_resize = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            was_resizing = self._in_drag_resize
            self._in_drag_resize = False
            if self._pending_scale_update:
                self._pending_scale_update = False
                self._apply_scale_to_frame()
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, '_resize_debounce_active', False):
            self._resize_debounce_active = True
            QTimer.singleShot(16, self._on_debounced_resize)

    def _on_debounced_resize(self):
        self._resize_debounce_active = False
        self._update_resize_corner_position()
        if self._alert_toast is not None:
            self._alert_toast.reposition()


class ResizeCorner(QWidget, ScaleMixin):
    """Custom resize grip in bottom-right corner"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.setMinimumSize(S.px(16), S.px(16))
        self.setMaximumSize(S.px(24), S.px(24))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._start_geometry = None
        self._start_pos = None
        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self.update()

    def _on_theme_changed(self, theme_name: str):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = theme_manager.colors
        painter.setPen(QPen(QColor(colors.BORDER), 1))
        h = self.height()
        w = self.width()
        for i in range(2):
            painter.drawLine(w - 4 - i * 4, h, w, h - 4 - i * 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_geometry = self._parent.geometry()
            self._start_pos = event.globalPos()
            self._parent._in_drag_resize = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._start_geometry:
            delta = event.globalPos() - self._start_pos
            new_width = max(self._parent.minimumWidth(), self._start_geometry.width() + delta.x())
            new_height = max(self._parent.minimumHeight(), self._start_geometry.height() + delta.y())
            self._parent.resize(int(new_width), int(new_height))
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_geometry = None
            self._start_pos = None
            self._parent._in_drag_resize = False
            event.accept()
