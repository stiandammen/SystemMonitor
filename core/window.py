"""
Main Window - Application main window
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QFont, QMouseEvent


COLORS = {
    'bg_primary': '#0a0e14',
    'bg_card': '#161f2a',
    'bg_hover': '#1e2936',
    'text_primary': '#f0f4f8',
    'text_muted': '#64748b',
    'border': '#2a3441',
    'accent_green': '#10b981',
    'accent_red': '#ef4444',
    'accent_blue': '#3b82f6',
}


class TitleBar(QWidget):
    """Custom dark title bar with window controls"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._maximized = False
        self._drag_position = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup title bar UI"""
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']}; border: none;")

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)
        self.setLayout(layout)

        # App title
        title = QLabel("⚙ System Monitor")
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        layout.addStretch()

        # Window control buttons
        self._create_buttons(layout)

    def _create_buttons(self, layout):
        """Create minimize, maximize, close buttons"""
        # Minimize button
        min_btn = QPushButton()
        min_btn.setFixedSize(40, 32)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.2);
            }}
            QPushButton:pressed {{
                background-color: rgba(59, 130, 246, 0.3);
            }}
        """)
        min_btn.setText("─")
        min_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        min_btn.setStyleSheet(f"""
            color: {COLORS['text_muted']};
        """ + f"""
            QPushButton:hover {{
                color: {COLORS['accent_blue']};
            }}
        """)
        min_btn.clicked.connect(self._minimize_window)
        layout.addWidget(min_btn)

        # Maximize/Restore button
        self._max_btn = QPushButton()
        self._max_btn.setFixedSize(40, 32)
        self._max_btn.setCursor(Qt.PointingHandCursor)
        self._max_btn.setText("□")
        self._max_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._max_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(16, 185, 129, 0.2);
                color: {COLORS['accent_green']};
            }}
            QPushButton:pressed {{
                background-color: rgba(16, 185, 129, 0.3);
            }}
        """)
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(40, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setText("✕")
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.2);
                color: {COLORS['accent_red']};
            }}
            QPushButton:pressed {{
                background-color: rgba(239, 68, 68, 0.3);
            }}
        """)
        close_btn.clicked.connect(self._close_window)
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
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position:
            if self._maximized:
                # If maximized, restore first then move
                self._parent.showNormal()
                self._max_btn.setText("□")
                self._maximized = False
                self._drag_position = event.globalPos() - self._parent.frameGeometry().topLeft()
            self._parent.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = None
            event.accept()

    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == QEvent.WindowStateChange:
            if self._parent:
                if self._parent.isMaximized():
                    self._max_btn.setText("❐")
                    self._maximized = True
                else:
                    self._max_btn.setText("□")
                    self._maximized = False
        super().changeEvent(event)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup window UI"""
        # Frameless window for custom title bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Window properties
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 2870, 1721)
        self.setMinimumSize(1400, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout (vertical: title bar + content)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        # Custom title bar
        self._title_bar = TitleBar(self)
        main_layout.addWidget(self._title_bar)

        # Content area layout (horizontal: sidebar + content)
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

        # Create views
        self._create_views()

    def _create_sidebar(self):
        """Create sidebar navigation"""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(6)
        sidebar.setLayout(layout)

        # Title
        title = QLabel("⚙ System Monitor")
        font = QFont("Segoe UI", 15, QFont.Bold)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        layout.addSpacing(24)

        # Navigation buttons with icons
        nav_items = [
            ("Overview", "◉", "overview"),
            ("CPU", "◇", "cpu"),
            ("GPU", "◈", "gpu"),
            ("Network", "⬡", "network"),
            ("Memory", "◐", "memory"),
            ("Disks", "⬟", "disks"),
            ("Processes", "◎", "processes"),
        ]

        for view_name, icon, view_key in nav_items:
            btn = QPushButton(f"  {icon}  {view_name}")
            btn.setMinimumHeight(44)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['border']};
                }}
            """)
            btn.clicked.connect(lambda checked, key=view_key: self._switch_view(key))
            layout.addWidget(btn)

        layout.addStretch()

        # Settings button at bottom with distinct style
        settings_btn = QPushButton("  ⚙  Settings")
        settings_btn.setMinimumHeight(44)
        settings_btn.setFont(QFont("Segoe UI", 11))
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                text-align: left;
                padding-left: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['accent_blue']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)
        settings_btn.clicked.connect(lambda checked: self._switch_view("settings"))
        layout.addWidget(settings_btn)

        return sidebar

    def _create_views(self):
        """Create all views"""
        from views.overview_page import OverviewPage
        from views.cpu import CPUView
        from views.gpu import GPUView
        from views.network import NetworkView
        from views.memory import MemoryView
        from views.disks import DisksView
        from views.processes import ProcessesView
        from views.settings import SettingsView

        self._views = {
            "overview": OverviewPage(),
            "cpu": CPUView(),
            "gpu": GPUView(),
            "network": NetworkView(),
            "memory": MemoryView(),
            "disks": DisksView(),
            "processes": ProcessesView(),
            "settings": SettingsView(),
        }

        for name, view in self._views.items():
            self._content.addWidget(view)

        # Set initial view
        self._content.setCurrentWidget(self._views["overview"])

    def _switch_view(self, view_name):
        """Switch to different view"""
        if view_name in self._views:
            self._content.setCurrentWidget(self._views[view_name])

    def update_data(self, data):
        """Update all views with new data"""
        for view in self._views.values():
            if hasattr(view, 'update_data'):
                view.update_data(data)

    def mousePressEvent(self, event):
        """Handle window drag from content area"""
        if event.button() == Qt.LeftButton and event.globalY() < self._title_bar.height():
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle window move from content area"""
        if event.buttons() == Qt.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._drag_position = None
            event.accept()
