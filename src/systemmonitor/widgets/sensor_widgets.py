"""
Sensor Widgets - Extended sensor readout (fan RPM & voltage rails)
Used by the CPU view (OPPGAVE-11). Many consumer Windows machines only expose
these through vendor tools (HWiNFO/LibreHardwareMonitor), so the panel shows a
plain-language explanation instead of fabricating numbers when nothing is found.
"""
from typing import List, Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin


def c():
    return theme_manager.colors


class _SensorColumn(QFrame):
    """One labeled column of sensor rows with an empty-state message."""

    def __init__(self, title: str, icon: str, empty_message: str, parent=None):
        super().__init__(parent)
        self._empty_message = empty_message
        colors = c()

        self.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(S.px(6))

        head = QHBoxLayout()
        head.setSpacing(S.px(6))
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color=colors.TEXT_SECONDARY).pixmap(S.px(14), S.px(14)))
        head.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        head.addWidget(title_label)
        head.addStretch()
        outer.addLayout(head)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(S.px(4))
        self._rows_layout.setContentsMargins(S.px(20), 0, 0, 0)
        outer.addLayout(self._rows_layout)
        outer.addStretch()

        self._empty_label = QLabel(empty_message)
        self._empty_label.setWordWrap(True)
        self._empty_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._empty_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        self._rows_layout.addWidget(self._empty_label)

    def set_readings(self, readings: List[tuple]):
        """readings: list of (label, value_text) tuples. Empty -> show placeholder."""
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        colors = c()
        if not readings:
            empty = QLabel(self._empty_message)
            empty.setWordWrap(True)
            empty.setFont(QFont("Segoe UI", S.font_pt(9)))
            empty.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            self._rows_layout.addWidget(empty)
            return

        for label, value in readings:
            row = QHBoxLayout()
            row.setSpacing(S.px(8))

            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
            lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
            row.addWidget(lbl, stretch=1)

            val = QLabel(value)
            val.setFont(QFont("Consolas", S.font_pt(10), QFont.Weight.Bold))
            val.setStyleSheet(f"color: {colors.ACCENT_CYAN}; background: transparent;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(val)

            wrapper = QFrame()
            wrapper.setLayout(row)
            self._rows_layout.addWidget(wrapper)


class SensorsPanel(QFrame, ScaleMixin, I18nMixin):
    """Two-column panel showing fan RPM and voltage rail readings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_fans: List[tuple] = []
        self._last_voltages: List[tuple] = []
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()

    def retranslate_ui(self):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def _setup_ui(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QFrame().setLayout(old)

        colors = c()
        self.setStyleSheet(f"""
            QFrame#sensors_panel {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        self.setObjectName("sensors_panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(S.px(16), S.px(14), S.px(16), S.px(14))
        layout.setSpacing(S.px(28))

        self._fans_col = _SensorColumn(
            tr("Fan Speeds (RPM)"), "mdi.fan",
            tr("No fan sensors exposed by this system. Most consumer PCs only "
               "report fan RPM through vendor tools like HWiNFO."))
        layout.addWidget(self._fans_col, stretch=1)

        self._voltages_col = _SensorColumn(
            tr("Voltage Rails"), "mdi.flash-outline",
            tr("No voltage sensors exposed by this system's firmware/WMI interface."))
        layout.addWidget(self._voltages_col, stretch=1)

        self._fans_col.set_readings(self._last_fans)
        self._voltages_col.set_readings(self._last_voltages)

    def on_scale_changed(self, factor: float):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._setup_ui)

    def update_sensors(self, fans: List[tuple], voltages: List[tuple]):
        self._last_fans = fans or []
        self._last_voltages = voltages or []
        self._fans_col.set_readings(self._last_fans)
        self._voltages_col.set_readings(self._last_voltages)
