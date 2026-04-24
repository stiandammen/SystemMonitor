"""
CPU View - CPU monitoring
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class CPUView(QWidget):
    """CPU monitoring view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup view UI"""
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_widget.setMaximumWidth(1200)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(20, 20, 20, 20)
        self._content_layout.setSpacing(20)
        content_widget.setLayout(self._content_layout)

        self._scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._scroll_area)
        self.setLayout(main_layout)

        title = QLabel("CPU Monitoring")
        font = QFont("Segoe UI", 24)
        font.setBold(True)
        title.setFont(font)
        self._content_layout.addWidget(title)

        self._info_label = QLabel("Loading...")
        self._content_layout.addWidget(self._info_label)

        self._content_layout.addStretch()
    
    def update_data(self, data):
        """Update view with new data"""
        if 'cpu' in data:
            cpu = data['cpu']
            self._info_label.setText(f"CPU Usage: {cpu['percent']:.1f}%")
