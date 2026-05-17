"""
Main Window - Application main window
Professional enterprise-grade design with responsive layout and overlay mode
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QEvent, QTimer, QSize
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QIcon, QCursor

from widgets.glass_sidebar import GlassSidebar
from widgets.responsive import OverlayWidget
from styles.theme import theme_manager
from scaler import S, ScaleMixin, LayoutMode
from utils.logger import get_logger, LogCategory, log_info, log_debug


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

        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(12), 0, S.px(8), 0)
        layout.setSpacing(S.px(6))
        self.setLayout(layout)

        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))
        title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        title.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(title)

        layout.addStretch()
        self._create_buttons(layout)

    def _create_buttons(self, layout):
        colors = theme_manager.colors

        for text, slot, style_key in [
            ("─", self._minimize_window, "min"),
            ("□", self._toggle_maximize, "max"),
            ("✕", self._close_window, "close"),
        ]:
            btn = QPushButton()
            btn.setFixedSize(S.px(36), S.px(28))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setText(text)
            btn.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))

            if style_key == "close":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.TEXT_MUTED};
                        border: none;
                        border-radius: {S.px(6)}px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.ACCENT_RED};
                        color: white;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.TEXT_MUTED};
                        border: none;
                        border-radius: {S.px(6)}px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.BG_HOVER};
                        color: {colors.TEXT_PRIMARY};
                    }}
                """)

            btn.clicked.connect(slot)
            layout.addWidget(btn)
            if style_key == "max":
                self._max_btn = btn

    def _minimize_window(self):
        if self._parent:
            self._parent.showMinimized()

    def _toggle_maximize(self):
        if self._parent:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.setText("□")
                self._maximized = False
            else:
                self._parent.showMaximized()
                self._max_btn.setText("❐")
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
                self._max_btn.setText("□")
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
                    self._max_btn.setText("❐")
                    self._maximized = True
                else:
                    self._max_btn.setText("□")
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
        self._setup_ui()
        self.update()

    def closeEvent(self, event):
        self.scale_disconnect()
        super().closeEvent(event)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setMinimumHeight(S.px(48))
        self.setMaximumHeight(S.px(60))

        if theme_manager.current_theme == "heimdal":
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

        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(16), 0, S.px(8), 0)
        layout.setSpacing(S.px(12))
        self.setLayout(layout)

        self._create_icon(layout)

        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", S.font_pt(13), QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        title.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(title)

        spacer = QWidget()
        spacer.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(spacer, stretch=1)

        self._create_window_controls(layout)

    def _create_icon(self, layout):
        icon_container = QFrame()
        icon_container.setMinimumSize(S.px(32), S.px(32))
        icon_container.setMaximumSize(S.px(40), S.px(40))
        icon_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        accent = theme_manager.colors.ACCENT_GREEN
        icon_container.setStyleSheet(f"""
            background-color: {accent};
            border-radius: {S.px(8)}px;
        """)

        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setLayout(icon_layout)

        icon_label = QLabel("SM")
        icon_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        icon_label.setStyleSheet("color: white;")
        icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container)

    def _create_window_controls(self, layout):
        colors = theme_manager.colors
        is_heimdal = theme_manager.current_theme == "heimdal"

        for text, slot, is_close in [
            ("─", self._minimize_window, False),
            ("□", self._toggle_maximize, False),
            ("✕", self._close_window, True),
        ]:
            btn = QPushButton()
            btn.setFixedSize(S.px(36), S.px(28))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setText(text)
            btn.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))

            if is_close:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #8A92B2;
                        border: none;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #FF4757;
                        color: white;
                    }
                """)
            elif is_heimdal:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #8A92B2;
                        border: none;
                        border-radius: 6px;
                    }
                    QPushButton:hover {
                        background-color: #252A47;
                        color: #E8ECFF;
                    }
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {colors.TEXT_MUTED};
                        border: none;
                        border-radius: {S.px(6)}px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.BG_HOVER};
                        color: {colors.TEXT_PRIMARY};
                    }}
                """)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
            if "□" in text or "❐" in text:
                self._max_btn = btn

    def _minimize_window(self):
        if self._parent:
            self._parent.showMinimized()

    def _toggle_maximize(self):
        if self._parent:
            if self._maximized:
                self._parent.showNormal()
                self._max_btn.setText("□")
                self._maximized = False
            else:
                self._parent.showMaximized()
                self._max_btn.setText("❐")
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
                self._max_btn.setText("□")
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
                    self._max_btn.setText("❐")
                    self._maximized = True
                else:
                    self._max_btn.setText("□")
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
        self._resize_debounce_timer = QTimer()
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_debounce_timer.timeout.connect(self._on_debounced_resize)

        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self._preload_overview()

    def _preload_overview(self):
        self._get_view("overview")

    def _get_view(self, view_name: str) -> QWidget:
        if view_name not in self._view_cache:
            from views.overview_page import OverviewPage
            from views.cpu import CPUView
            from views.gpu import GPUView
            from views.network import NetworkView
            from views.memory import MemoryView
            from views.storage import StorageView
            from views.settings import SettingsView

            view_classes = {
                "overview": OverviewPage,
                "cpu": CPUView,
                "gpu": GPUView,
                "network": NetworkView,
                "memory": MemoryView,
                "storage": StorageView,
                "settings": SettingsView,
            }

            if view_name in view_classes:
                self._view_cache[view_name] = view_classes[view_name]()
                self._content.addWidget(self._view_cache[view_name])

        return self._view_cache[view_name]

    def on_scale_changed(self, factor: float):
        if self._in_drag_resize:
            self._pending_scale_update = True
            return
        log_debug(LogCategory.WINDOW, f"Scale changed: {factor}")
        self._pending_scale_update = True
        QTimer.singleShot(100, self._debounced_setup_ui)

    def on_layout_mode_changed(self, mode):
        if self._in_drag_resize:
            return
        if mode == LayoutMode.COMPACT:
            if hasattr(self, '_sidebar') and not self._sidebar._collapsed:
                self._sidebar._toggle_collapse()
        else:
            if hasattr(self, '_sidebar') and self._sidebar._collapsed:
                self._sidebar._toggle_collapse()
        self._debounced_setup_ui()

    def _debounced_setup_ui(self):
        if not self._in_drag_resize:
            self._setup_ui()
            self.update()

    def _on_theme_changed(self, theme_name: str):
        try:
            self.setStyleSheet(theme_manager.get_stylesheet())
            if hasattr(self, '_top_header'):
                self._top_header._setup_ui()
            if hasattr(self, '_sidebar'):
                self._sidebar._apply_theme()
                for item in self._sidebar._items.values():
                    item._apply_style()
            if hasattr(self, '_resize_corner'):
                self._resize_corner._on_theme_changed(theme_name)
            if hasattr(self, '_view_cache'):
                for view in self._view_cache.values():
                    view.update()
        except Exception as e:
            print(f"Theme change error: {e}")

    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("System Monitor")

        screen = self.screen()
        if screen:
            geom = screen.availableGeometry()
            self.setGeometry(geom.x() + 50, geom.y() + 50,
                           min(1400, geom.width() - 100),
                           min(900, geom.height() - 100))
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
        self._content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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

        overview = self._get_view("overview")
        self._content.setCurrentWidget(overview)
        self._active_view = "overview"

        self._resize_corner = ResizeCorner(self)
        self._update_resize_corner_position()

    def _update_resize_corner_position(self):
        if hasattr(self, '_resize_corner'):
            self._resize_corner.move(self.width() - 16, self.height() - 16)

    def _create_sidebar(self):
        sidebar = GlassSidebar()
        sidebar.view_selected.connect(self._switch_view)
        if S.is_compact():
            sidebar._collapsed = True
            sidebar.setFixedWidth(S.px(64))
        return sidebar

    def _switch_view(self, view_name: str):
        view = self._get_view(view_name)
        self._content.setCurrentWidget(view)
        self._active_view = view_name
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
            if hasattr(self, '_pending_scale_update') and self._pending_scale_update:
                self._pending_scale_update = False
                self._setup_ui()
                self.update()
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, '_resize_debounce_active', False):
            self._resize_debounce_active = True
            QTimer.singleShot(16, self._on_debounced_resize)

    def _on_debounced_resize(self):
        self._resize_debounce_active = False
        self._update_resize_corner_position()


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