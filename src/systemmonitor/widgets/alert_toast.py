"""
Alert Toast - lightweight in-app notification banner shown over the main
window when a system metric crosses an alert threshold (the "In-app Visuals"
notification method, as an alternative to Windows system tray popups).
"""
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S


class AlertToast(QWidget):
    """Floating banner anchored to the top-right corner of its parent.

    A single instance is reused: a new alert arriving while the toast is
    already visible simply replaces the message and restarts the auto-dismiss
    timer, rather than stacking multiple banners.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AlertToast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setVisible(False)
        self.setFixedWidth(S.px(320))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        self._label.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(self._label)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.hide)

    def show_alert(self, message: str, level: str = 'warning'):
        """Display (or refresh) the banner with the given message and level."""
        colors = theme_manager.colors
        bg = colors.ACCENT_RED if level in ('critical', 'CRITICAL') else colors.ACCENT_ORANGE
        self.setStyleSheet(f"""
            #AlertToast {{
                background-color: {bg};
                border-radius: {S.px(10)}px;
            }}
        """)
        self._label.setText(message)
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._dismiss_timer.start(6000)

    def reposition(self):
        """Re-anchor to the parent's top-right corner (e.g. on window resize)."""
        if self.isVisible():
            self._reposition()

    def _reposition(self):
        parent = self.parentWidget()
        if parent is None:
            return
        margin = S.px(20)
        x = parent.width() - self.width() - margin
        y = S.px(60)
        self.move(max(0, x), y)
