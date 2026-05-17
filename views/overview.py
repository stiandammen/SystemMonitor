"""
Overview View - Main dashboard
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scaler import S, ScaleMixin


class OverviewView(QWidget, ScaleMixin):
    """Overview dashboard view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self._setup_ui()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup view UI"""
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_widget.setMaximumWidth(1200)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        content_widget.setLayout(layout)

        self._scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._scroll_area)
        self.setLayout(main_layout)

        # Title
        title = QLabel("System Overview")
        font = QFont("Segoe UI", 24)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Stats grid
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        # CPU Card
        self._cpu_card = self._create_stat_card("CPU", "0%")
        stats_layout.addWidget(self._cpu_card, stretch=1)

        # Memory Card
        self._memory_card = self._create_stat_card("Memory", "0%")
        stats_layout.addWidget(self._memory_card, stretch=1)

        # Disk Card
        self._disk_card = self._create_stat_card("Disk", "0%")
        stats_layout.addWidget(self._disk_card, stretch=1)

        layout.addLayout(stats_layout)
        layout.addStretch()
    
    def _create_stat_card(self, title, value):
        """Create a stat card"""
        card = QFrame()
        card.setMinimumHeight(100)
        card.setStyleSheet("""
            QFrame {
                background-color: #161f2a;
                border: none;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout()
        card.setLayout(layout)
        
        title_label = QLabel(title)
        title_font = QFont("Segoe UI", 12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_font = QFont("Segoe UI", 32)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #10b981; background: transparent;")
        layout.addWidget(value_label)
        
        # Store reference for updates
        card.value_label = value_label
        
        return card
    
    def update_data(self, data):
        """Update view with new data"""
        if 'cpu' in data:
            self._cpu_card.value_label.setText(f"{data['cpu']['percent']:.1f}%")
        
        if 'memory' in data:
            self._memory_card.value_label.setText(f"{data['memory']['percent']:.1f}%")
        
        if 'disk' in data:
            self._disk_card.value_label.setText(f"{data['disk']['percent']:.1f}%")
