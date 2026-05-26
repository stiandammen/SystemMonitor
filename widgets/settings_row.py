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
        self.setMinimumHeight(S.px(56))
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(20), S.px(14), S.px(20), S.px(14))
        layout.setSpacing(S.px(24))
        self.setLayout(layout)

        # Left side - label and description
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(S.px(4))
        left_widget.setLayout(left_layout)
        layout.addWidget(left_widget, 1)

        self._label = QLabel(self._label_text)
        label_font = QFont("Segoe UI", S.font_pt(13))
        label_font.setWeight(QFont.Weight.Medium)
        self._label.setFont(label_font)
        left_layout.addWidget(self._label)

        if self._description_text:
            self._description = QLabel(self._description_text)
            desc_font = QFont("Segoe UI", S.font_pt(11))
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
        """Apply row styles with enhanced visual feedback"""
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


class ToggleWidget(QWidget, ScaleMixin):
    """Toggle switch widget with green active state"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(S.px(50), S.px(26))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_manager.theme_changed.connect(lambda _: self.update())

    def setChecked(self, checked: bool):
        self._checked = checked
        self.toggled.emit(checked)
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def mouseReleaseEvent(self, a0):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()
        super().mouseReleaseEvent(a0)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = theme_manager.colors

        # Track color
        if self._checked:
            track_color = QColor(c.ACCENT_GREEN)
        else:
            track_color = QColor(c.BORDER)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 0, S.px(50), S.px(26), S.px(13), S.px(13))

        # Handle
        handle_x = S.px(26) if self._checked else S.px(4)
        handle_rect = QRect(handle_x, S.px(4), S.px(22), S.px(22))

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(handle_rect)


class SettingsButton(QPushButton):
    """Styled settings button with modern appearance"""

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
                color: white;
                border: none;
                border-radius: {S.px(6)}px;
                padding: {S.px(8)}px {S.px(16)}px;
                font-family: "Segoe UI", sans-serif;
                font-size: {S.font_pt(13)}pt;
                font-weight: 600;
                min-width: {S.px(80)}px;
            }}
            QPushButton:hover {{
                background-color: {c.ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {c.ACCENT_GREEN};
            }}
        """)


class DangerButton(QPushButton):
    """Danger button for destructive actions with modern appearance"""

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
                color: white;
                border: none;
                border-radius: {S.px(6)}px;
                padding: {S.px(8)}px {S.px(16)}px;
                font-family: "Segoe UI", sans-serif;
                font-size: {S.font_pt(13)}pt;
                font-weight: 600;
                min-width: {S.px(80)}px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton:pressed {{
                background-color: {c.ACCENT_RED};
            }}
        """)


class SettingsComboBox(QComboBox):
    """Styled settings dropdown with modern appearance"""

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
                border: none;
                border-radius: S.px(6)px;
                padding: S.px(8)px S.px(12)px;
                font-family: "Segoe UI", "Segoe UI Variable", sans-serif;
                font-size: S.px(13)px;
                min-width: S.px(120)px;
            }}
            QComboBox:hover {{
                background-color: {c.BG_HOVER};
            }}
            QComboBox:focus {{
                border: 1px solid {c.ACCENT_GREEN};
            }}
            QComboBox::drop-down {{
                border: none;
                width: S.px(24)px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: S.px(4)px solid transparent;
                border-right: S.px(4)px solid transparent;
                border-top: S.px(5)px solid {c.TEXT_MUTED};
                margin-right: S.px(8)px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: none;
                border-radius: S.px(6)px;
                selection-background-color: {c.BG_HOVER};
                padding: S.px(4)px;
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
        font = QFont("Segoe UI", S.font_pt(11))
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
            QSlider {{
                min-height: S.px(36)px;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: S.px(6)px;
                background-color: {c.BORDER};
                border-radius: S.px(3)px;
                margin: S.px(15)px S.px(8)px;
            }}
            QSlider::sub-page:horizontal {{
                background-color: {c.ACCENT_GREEN};
                border-radius: S.px(3)px;
                height: S.px(6)px;
            }}
            QSlider::handle:horizontal {{
                background-color: {c.TEXT_PRIMARY};
                width: S.px(20)px;
                height: S.px(20)px;
                border-radius: S.px(10)px;
                margin: S.px(-7)px 0;
                border: S.px(2)px solid {c.ACCENT_GREEN};
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {c.TEXT_PRIMARY};
                border: S.px(2)px solid {c.ACCENT_GREEN};
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
                border: S.px(1)px solid {c.ACCENT_GREEN};
                border-radius: S.px(6)px;
                padding: S.px(4)px S.px(10)px;
                font-weight: bold;
            }}
        """)

    def _update_value_label_position(self):
        """Position the value label above the handle"""
        if self._value_label:
            handle_width = S.px(20)
            available_width = self.width() - handle_width
            if available_width > 0:
                ratio = (self.value() - self.minimum()) / max(1, self.maximum() - self.minimum())
                x = int(ratio * available_width) + handle_width // 2 - self._value_label.width() // 2
                y = -self._value_label.height() - S.px(8)
                self._value_label.move(x, y)

    def setValue(self, a0):
        """Set slider value and update label"""
        super().setValue(a0)
        self._current_value = a0
        if self._value_label:
            self._value_label.setText(str(a0))
            self._update_value_label_position()

    def resizeEvent(self, a0):
        """Handle resize to reposition label"""
        super().resizeEvent(a0)
        self._update_value_label_position()

    def showEvent(self, a0):
        """Show label when slider appears"""
        super().showEvent(a0)
        self._value_label.setText(str(self.value()))
        self._update_value_label_position()
        self._value_label.show()

    def hideEvent(self, a0):
        """Hide label when slider disappears"""
        super().hideEvent(a0)
        self._value_label.hide()

    def sliderChange(self, change):
        """Update label position when slider changes"""
        super().sliderChange(change)
        if change == QSlider.ChangePolicy.SliderValueChange:
            self._current_value = self.value()
            if self._value_label:
                self._value_label.setText(str(self.value()))
                self._update_value_label_position()