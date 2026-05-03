"""
Settings Row Widget - Label + control row
"""
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QWidget, QBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect, QPoint
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class SettingsRow(QFrame, ScaleMixin):
    """A row with label and control (toggle, slider, button, etc.)"""

    clicked = pyqtSignal()

    def __init__(self, label: str = "", description: str = "", parent=None):
        super().__init__(parent)
        self._label_text = label
        self._description_text = description
        self._control_widget = None
        self.scale_connect()
        self._setup_ui()
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self._apply_style()
        self.update()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def _setup_ui(self):
        """Setup row UI"""
        self.setMinimumHeight(56)
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(24)
        self.setLayout(layout)

        # Left side - label and description
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget, 1)

        self._label = QLabel(self._label_text)
        label_font = QFont("Segoe UI", 13)
        label_font.setWeight(QFont.Weight.Medium)
        self._label.setFont(label_font)
        left_layout.addWidget(self._label)

        if self._description_text:
            self._description = QLabel(self._description_text)
            desc_font = QFont("Segoe UI", 11)
            self._description.setFont(desc_font)
            left_layout.addWidget(self._description)

        # Right side - control
        self._control_container = QFrame()
        self._control_layout = QHBoxLayout()
        self._control_layout.setContentsMargins(0, 0, 0, 0)
        self._control_layout.setSpacing(0)
        self._control_container.setLayout(self._control_layout)
        layout.addWidget(self._control_container)

    def _apply_style(self):
        """Apply row styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            SettingsRow {{
                background-color: transparent;
                border: none;
                border-bottom: 1px solid {c.BORDER};
            }}
            SettingsRow:hover {{
                background-color: {c.BG_HOVER};
            }}
        """)
        self._label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        if hasattr(self, '_description'):
            self._description.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent; border: none;")

    def set_control(self, widget):
        """Set the control widget on the right side"""
        self._control_widget = widget
        self._control_layout.addWidget(widget)

    def get_control(self):
        """Get the control widget"""
        return self._control_widget


class SettingsButton(QPushButton):
    """Styled settings button"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def _apply_style(self):
        """Apply button styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_GREEN};
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.ACCENT_GREEN};
                opacity: 0.85;
            }}
            QPushButton:pressed {{
                background-color: {c.ACCENT_GREEN};
                opacity: 0.7;
            }}
        """)


class DangerButton(QPushButton):
    """Danger button for destructive actions"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def _apply_style(self):
        """Apply danger button styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_RED};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c.ACCENT_RED};
                opacity: 0.85;
            }}
            QPushButton:pressed {{
                background-color: {c.ACCENT_RED};
                opacity: 0.7;
            }}
        """)


class SettingsComboBox(QComboBox):
    """Styled settings dropdown"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def _apply_style(self):
        """Apply dropdown styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {c.BG_INPUT};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {c.BORDER_FOCUS};
            }}
            QComboBox:focus {{
                border-color: {c.ACCENT_GREEN};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 32px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {c.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 8px;
                selection-background-color: {c.BG_HOVER};
                padding: 4px;
            }}
        """)


class SettingsSlider(QSlider):
    """Professional slider with value indicator and smooth animations"""

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._value_label = None
        self._track_animation = None
        self._current_value = 0
        self._setup_value_label()
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_value_label(self):
        """Create floating value label"""
        self._value_label = QLabel(self)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.Weight.DemiBold)
        self._value_label.setFont(font)
        self._update_value_label_position()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()
        self._update_value_label_style()

    def _apply_style(self):
        """Apply slider styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            SettingsSlider {{
                min-height: 36px;
            }}
            SettingsSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background-color: {c.BORDER};
                border-radius: 3px;
                margin: 15px 8px;
            }}
            SettingsSlider::sub-page:horizontal {{
                background-color: {c.ACCENT_GREEN};
                border-radius: 3px;
                height: 6px;
            }}
            SettingsSlider::handle:horizontal {{
                background-color: {c.TEXT_PRIMARY};
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -7px 0;
                border: 2px solid {c.ACCENT_GREEN};
            }}
            SettingsSlider::handle:horizontal:hover {{
                background-color: {c.TEXT_PRIMARY};
                border: 2px solid {c.ACCENT_GREEN};
            }}
        """)
        self._update_value_label_style()

    def _update_value_label_style(self):
        """Update value label appearance"""
        c = theme_manager.colors
        self._value_label.setStyleSheet(f"""
            QLabel {{
                color: {c.TEXT_PRIMARY};
                background-color: {c.BG_HOVER};
                border: 1px solid {c.ACCENT_GREEN};
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
            }}
        """)

    def _update_value_label_position(self):
        """Position the value label above the handle"""
        if self._value_label:
            handle_width = 20
            available_width = self.width() - handle_width
            if available_width > 0:
                ratio = (self.value() - self.minimum()) / max(1, self.maximum() - self.minimum())
                x = int(ratio * available_width) + handle_width // 2 - self._value_label.width() // 2
                y = -self._value_label.height() - 8
                self._value_label.move(x, y)

    def setValue(self, value):
        """Set slider value and update label"""
        super().setValue(value)
        self._current_value = value
        if self._value_label:
            self._value_label.setText(str(value))
            self._update_value_label_position()

    def resizeEvent(self, event):
        """Handle resize to reposition label"""
        super().resizeEvent(event)
        self._update_value_label_position()

    def showEvent(self, event):
        """Show label when slider appears"""
        super().showEvent(event)
        self._value_label.setText(str(self.value()))
        self._update_value_label_position()
        self._value_label.show()

    def hideEvent(self, event):
        """Hide label when slider disappears"""
        super().hideEvent(event)
        self._value_label.hide()

    def sliderChange(self, change):
        """Update label position when slider changes"""
        super().sliderChange(change)
        if change == QSlider.ChangePolicy.SliderValueChange:
            self._current_value = self.value()
            if self._value_label:
                self._value_label.setText(str(self.value()))
                self._update_value_label_position()