"""
Stat Chip Widget - Compact stat display
"""
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class StatChip(QFrame, ScaleMixin):
    """
    Compact chip showing label and value
    """

    def __init__(self, label: str = "", value: str = "", trend: str = "", parent=None):
        super().__init__(parent)
        self._label_text = label
        self._value_text = value
        self._trend_text = trend
        self.scale_connect()
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Setup chip UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Label
        self._label = QLabel(self._label_text)
        label_font = QFont("Segoe UI", 10)
        self._label.setFont(label_font)
        layout.addWidget(self._label)

        # Value
        self._value = QLabel(self._value_text)
        value_font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self._value.setFont(value_font)
        layout.addWidget(self._value)

        # Trend (optional)
        if self._trend_text:
            self._trend = QLabel(self._trend_text)
            trend_font = QFont("Segoe UI", 9)
            self._trend.setFont(trend_font)
            layout.addWidget(self._trend)

        layout.addStretch()

    def _apply_style(self):
        """Apply chip styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            StatChip {{
                background-color: {c.BG_CARD};
                border: 1px solid {c.BORDER};
                border-radius: 6px;
            }}
        """)

        self._label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent;")
        self._value.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")

    def set_value(self, value: str):
        """Update value text"""
        self._value_text = value
        self._value.setText(value)

    def set_label(self, label: str):
        """Update label text"""
        self._label_text = label
        self._label.setText(label)


class StatusChip(QFrame, ScaleMixin):
    """Status chip with color-coded badge for health indicators"""

    def __init__(self, status: str = "normal", label: str = "", parent=None):
        super().__init__(parent)
        self._status = status
        self._label_text = label
        self.scale_connect()
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Setup chip UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)
        self.setLayout(layout)

        # Status indicator dot
        self._indicator = QFrame()
        self._indicator.setFixedSize(8, 8)
        layout.addWidget(self._indicator)

        # Label
        if self._label_text:
            self._label = QLabel(self._label_text)
            label_font = QFont("Segoe UI", 10)
            self._label.setFont(label_font)
            layout.addWidget(self._label)

    def _apply_style(self):
        """Apply status-specific styles"""
        c = theme_manager.colors

        if theme_manager.current_theme == "heimdal":
            # Heimdal status colors
            if self._status == "critical":
                bg = "rgba(255, 71, 87, 0.15)"
                color = "#FF4757"
                indicator_color = "#FF4757"
            elif self._status == "warning":
                bg = "rgba(255, 107, 53, 0.15)"
                color = "#FF6B35"
                indicator_color = "#FF6B35"
            elif self._status == "ok":
                bg = "rgba(0, 224, 150, 0.15)"
                color = "#00E096"
                indicator_color = "#00E096"
            else:  # info
                bg = "rgba(74, 108, 247, 0.15)"
                color = "#4A6CF7"
                indicator_color = "#4A6CF7"
        else:
            # Original theme colors
            if self._status == "critical":
                bg = c.ERROR_BG
                color = c.STATUS_RED
                indicator_color = c.STATUS_RED
            elif self._status == "warning":
                bg = c.WARNING_BG
                color = c.STATUS_ORANGE
                indicator_color = c.STATUS_ORANGE
            elif self._status == "ok":
                bg = c.SUCCESS_BG
                color = c.STATUS_GREEN
                indicator_color = c.STATUS_GREEN
            else:  # info
                bg = c.INFO_BG
                color = c.ACCENT_BLUE
                indicator_color = c.ACCENT_BLUE

        self.setStyleSheet(f"""
            StatusChip {{
                background-color: {bg};
                border: none;
                border-radius: 12px;
            }}
        """)

        self._indicator.setStyleSheet(f"background-color: {indicator_color}; border-radius: 4px;")
        if hasattr(self, '_label'):
            self._label.setStyleSheet(f"color: {color}; background: transparent;")

    def set_status(self, status: str):
        """Update status type: critical, warning, ok, info"""
        self._status = status
        self._apply_style()

    def set_label(self, label: str):
        """Update label text"""
        self._label_text = label
        if hasattr(self, '_label'):
            self._label.setText(label)
