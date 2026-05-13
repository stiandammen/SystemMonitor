"""
Main Window - Application main window
Professional enterprise-grade design with clean window chrome
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QPoint, QEvent, QTimer
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QIcon

from widgets.sidebar import PremiumSidebar
from styles.theme import theme_manager
from scaler import S, ScaleMixin
from utils.logger import get_logger, LogCategory, log_info, log_debug


class TitleBar(QWidget, ScaleMixin):
    """Professional dark title bar with window controls"""

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
        """Setup title bar UI"""
        colors = theme_manager.colors
        self.setFixedHeight(38)
        self.setStyleSheet(f"background-color: {colors.BG_PRIMARY}; border: none; border-radius: 0px;")

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Draggable area label
        title = QLabel("System Monitor")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        title.setCursor(Qt.CursorShape.SizeAllCursor)
        layout.addWidget(title)

        layout.addStretch()

        # Window control buttons
        self._create_buttons(layout)

    def _create_buttons(self, layout):
        """Create minimize, maximize, close buttons"""
        colors = theme_manager.colors

        # Minimize button
        min_btn = QPushButton()
        min_btn.setFixedSize(36, 28)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.setIcon(QIcon.fromTheme("window-minimize"))
        min_btn.setText("─")
        min_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.TEXT_MUTED};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
            }}
        """)
        min_btn.clicked.connect(self._minimize_window)
        layout.addWidget(min_btn)

        # Maximize/Restore button
        max_btn = QPushButton()
        max_btn.setFixedSize(36, 28)
        max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        max_btn.setText("□")
        max_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        max_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.TEXT_MUTED};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.BG_HOVER};
                color: {colors.TEXT_PRIMARY};
            }}
        """)
        max_btn.clicked.connect(self._toggle_maximize)
        self._max_btn = max_btn
        layout.addWidget(max_btn)

        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(36, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setText("✕")
        close_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors.TEXT_MUTED};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.ACCENT_RED};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self._close_window)
        self._close_btn = close_btn
        layout.addWidget(close_btn)

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


class ResizeCorner(QWidget, ScaleMixin):
    """Custom resize grip in bottom-right corner"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.setFixedWidth(S.px(16))
        self.setMinimumHeight(S.px(16))
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


class MainWindow(QMainWindow, ScaleMixin):
    """Main application window - professional enterprise design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position = None
        self._in_drag_resize = False
        self._pending_scale_update = False
        self._view_cache = {}
        self._active_view = None
        self._resize_debounce_timer = QTimer()
        self._resize_debounce_timer.setSingleShot(True)
        self._resize_debounce_timer.timeout.connect(self._update_resize_corner)

        self.scale_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()
        self._preload_overview()

    def _preload_overview(self):
        """Preload the default overview view"""
        self._get_view("overview")

    def _get_view(self, view_name: str) -> QWidget:
        """Get or create a view lazily"""
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

    def _debounced_setup_ui(self):
        if not self._in_drag_resize:
            self._setup_ui()
            self.update()

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change - rebuild UI"""
        try:
            # Apply global stylesheet to update all widgets
            self.setStyleSheet(theme_manager.get_stylesheet())
            if hasattr(self, '_title_bar'):
                self._title_bar._setup_ui()
            if hasattr(self, '_sidebar'):
                self._sidebar._apply_theme()
                for item in self._sidebar._items.values():
                    item._apply_style()
            if hasattr(self, '_resize_corner'):
                self._resize_corner._on_theme_changed(theme_name)
            # Update all cached views so they repaint with new theme colors
            if hasattr(self, '_view_cache'):
                for view in self._view_cache.values():
                    view.update()
        except Exception as e:
            print(f"Theme change error: {e}")

    def _setup_ui(self):
        """Setup window UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(900, 600)

        colors = theme_manager.colors

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        # Title bar
        self._title_bar = TitleBar(self)
        main_layout.addWidget(self._title_bar)

        # Content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addLayout(content_layout)

        # Sidebar
        self._sidebar = self._create_sidebar()
        content_layout.addWidget(self._sidebar)

        # Content area
        self._content = QStackedWidget()
        content_layout.addWidget(self._content, stretch=1)

        # Load overview as default
        overview = self._get_view("overview")
        self._content.setCurrentWidget(overview)
        self._active_view = "overview"

        # Resize corner in bottom-right
        self._resize_corner = ResizeCorner(self)
        self._update_resize_corner_position()

    def _update_resize_corner_position(self):
        if hasattr(self, '_resize_corner'):
            self._resize_corner.move(self.width() - 16, self.height() - 16)

    def _create_sidebar(self):
        """Create sidebar navigation using premium sidebar widget"""
        sidebar = PremiumSidebar()
        sidebar.view_selected.connect(self._switch_view)
        return sidebar

    def _switch_view(self, view_name: str):
        """Switch to different view - lazy loading"""
        view = self._get_view(view_name)
        self._content.setCurrentWidget(view)
        self._active_view = view_name
        log_info(LogCategory.UI, f"Switched to view: {view_name}")

    def update_data(self, data: dict):
        """Update all active views with new data"""
        if self._active_view and self._active_view in self._view_cache:
            view = self._view_cache[self._active_view]
            if hasattr(view, 'update_data'):
                view.update_data(data)
        elif hasattr(self, '_overview_page'):
            self._overview_page.update_data(data)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.globalY() < self._title_bar.height():
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
            QTimer.singleShot(16, self._update_resize_corner)

    def _update_resize_corner(self):
        self._resize_debounce_active = False
        self._update_resize_corner_position()