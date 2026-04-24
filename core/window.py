"""
Main Window - Application main window
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QMouseEvent


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup window UI"""
        # Window properties
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central.setLayout(layout)
        
        # Sidebar
        self._sidebar = self._create_sidebar()
        layout.addWidget(self._sidebar)
        
        # Content area
        self._content = QStackedWidget()
        layout.addWidget(self._content, stretch=1)
        
        # Create views
        self._create_views()
    
    def _create_sidebar(self):
        """Create sidebar navigation"""
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #111820;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        sidebar.setLayout(layout)
        
        # Title
        title = QLabel("⚙ SYSTEM MONITOR")
        font = QFont("Segoe UI", 14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Navigation buttons
        views = ["Overview", "CPU", "GPU", "Network", "Memory", "Disks", "Processes", "Settings"]
        for view_name in views:
            btn = QPushButton(view_name)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, name=view_name.lower(): self._switch_view(name))
            layout.addWidget(btn)
        
        layout.addStretch()
        
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
