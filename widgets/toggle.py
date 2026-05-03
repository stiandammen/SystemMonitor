"""
Toggle Switch Widget - Professional iOS-style toggle with smooth animations
"""
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QBrush

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class ToggleSwitch(QCheckBox, ScaleMixin):
    """
    Professional iOS-style toggle switch with smooth sliding animation.
    Uses QPropertyAnimation for the handle position.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._handle_x = 4
        self._setup_animation()
        self.scale_connect()
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._apply_style()
        self.update()

    def _setup_animation(self):
        """Setup the handle position animation"""
        self._animation = QPropertyAnimation(self, b"handle_x")
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Linear)
        self._animation.valueChanged.connect(self.update)

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()

    def _get_handle_x(self) -> int:
        """Getter for animated handle position"""
        return self._handle_x

    def _set_handle_x(self, x: int):
        """Setter for animated handle position"""
        self._handle_x = x

    handle_x = pyqtProperty(int, _get_handle_x, _set_handle_x)

    def _apply_style(self):
        """Apply toggle switch styles"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(34)
        self.setMinimumWidth(60)
        self.setStyleSheet("""
            ToggleSwitch {
                spacing: 12px;
                background: transparent;
            }
        """)

    def _animate_to_checked(self, checked: bool):
        """Animate handle to checked/unchecked position"""
        self._animation.stop()
        self._animation.setStartValue(self._handle_x)
        self._animation.setEndValue(26 if checked else 4)
        self._animation.start()

    def mouseReleaseEvent(self, event):
        """Handle mouse release with animation"""
        super().mouseReleaseEvent(event)
        self._animate_to_checked(self.isChecked())

    def setChecked(self, checked: bool):
        """Set checked state"""
        super().setChecked(checked)
        self._handle_x = 26 if checked else 4
        self.update()

    def toggle(self):
        """Toggle with animation"""
        super().toggle()
        self._animate_to_checked(self.isChecked())

    def resizeEvent(self, event):
        """Resize the toggle"""
        super().resizeEvent(event)

    def paintEvent(self, event):
        """Custom paint for the toggle switch"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        c = theme_manager.colors

        # Track dimensions
        track_x = 4
        track_y = 4
        track_width = 42
        track_height = 18
        track_radius = 9

        # Draw track background
        track_color = QColor(c.ACCENT_GREEN) if self.isChecked() else QColor(c.BORDER)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_x, track_y, track_width, track_height, track_radius, track_radius)

        # Draw subtle highlight on track
        highlight_color = QColor(255, 255, 255, 25)
        highlight_rect = QRect(track_x + 2, track_y + 2, track_width - 4, track_height // 2 - 1)
        painter.setBrush(QBrush(highlight_color))
        painter.drawRoundedRect(highlight_rect, track_radius - 2, track_radius - 2)

        # Calculate handle position
        handle_rect = QRect(self._handle_x, 4, 22, 22)

        # Handle shadow
        shadow_color = QColor(0, 0, 0, 45)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        shadow_rect = QRect(handle_rect.x() + 1, handle_rect.y() + 2, handle_rect.width(), handle_rect.height())
        painter.drawEllipse(shadow_rect)

        # Handle background - white
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(handle_rect)

        # Handle highlight
        highlight_inner = QRect(handle_rect.x() + 3, handle_rect.y() + 3, handle_rect.width() - 6, handle_rect.height() // 2 - 2)
        highlight_inner_color = QColor(255, 255, 255, 140)
        painter.setBrush(QBrush(highlight_inner_color))
        painter.drawEllipse(highlight_inner)

        super().paintEvent(event)