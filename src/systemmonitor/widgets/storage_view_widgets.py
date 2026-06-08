"""
Reusable header and KPI-tile widgets for the Storage view dashboard.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QResizeEvent, QPainter, QColor
)

import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.i18n import tr, I18nMixin


# ─────────────────────────────────────────────────────────────────────────────
# StorageHeader
# ─────────────────────────────────────────────────────────────────────────────
class StorageHeader(QWidget, ScaleMixin, I18nMixin):
    """Top header bar: pulsing LIVE dot · title · disk count chip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._live_state = True
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def retranslate_ui(self):
        self._setup_ui()
        self.set_live(self._live_state)

    def _setup_ui(self):
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = theme_manager.colors
        self.setFixedHeight(S.px(60))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"background-color: {colors.BG_CARD};"
            f"border-radius: {S.px(12)}px;"
        )

        row = QHBoxLayout()
        row.setContentsMargins(S.px(20), 0, S.px(20), 0)
        row.setSpacing(S.px(14))
        self.setLayout(row)

        # ── LIVE dot + label ──────────────────────────────────────────────
        live_row = QHBoxLayout()
        live_row.setSpacing(S.px(7))

        self._live_dot = QFrame()
        self._live_dot.setFixedSize(S.px(9), S.px(9))
        self._live_dot.setStyleSheet(
            f"background-color: {colors.ACCENT_GREEN};"
            f"border-radius: {S.px(4)}px;"
        )
        live_row.addWidget(self._live_dot)

        # Pulsing animation
        self._pulse_fx = QGraphicsOpacityEffect(self._live_dot)
        self._pulse_fx.setOpacity(1.0)
        self._live_dot.setGraphicsEffect(self._pulse_fx)

        fade_out = QPropertyAnimation(self._pulse_fx, b"opacity")
        fade_out.setDuration(850)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.25)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutSine)

        fade_in = QPropertyAnimation(self._pulse_fx, b"opacity")
        fade_in.setDuration(850)
        fade_in.setStartValue(0.25)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._pulse_anim = QSequentialAnimationGroup(self._live_dot)
        self._pulse_anim.addAnimation(fade_out)
        self._pulse_anim.addAnimation(fade_in)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

        live_lbl = QLabel(tr("LIVE"))
        live_lbl.setFont(QFont("Segoe UI", S.font_pt(9), QFont.Weight.Bold))
        live_lbl.setStyleSheet(f"color: {colors.ACCENT_GREEN}; background: transparent;")
        live_row.addWidget(live_lbl)
        row.addLayout(live_row)

        # Thin vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(S.px(28))
        sep.setStyleSheet(f"background-color: {colors.BORDER};")
        row.addWidget(sep)

        # ── Title ─────────────────────────────────────────────────────────
        title = QLabel(tr("Storage Monitor"))
        title.setFont(QFont("Segoe UI", S.font_pt(17), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        row.addWidget(title)
        row.addStretch()

        # ── Disk count chip ───────────────────────────────────────────────
        chip = QWidget()
        chip.setStyleSheet(
            f"background-color: {colors.BG_HOVER};"
            f"border-radius: {S.px(8)}px;"
        )
        chip_row = QHBoxLayout(chip)
        chip_row.setContentsMargins(S.px(10), S.px(4), S.px(10), S.px(4))
        chip_row.setSpacing(S.px(6))

        hdd_icon = QLabel()
        try:
            ico = qta.icon("fa5s.hdd", color=colors.ACCENT_BLUE)
            hdd_icon.setPixmap(ico.pixmap(S.px(14), S.px(14)))
        except Exception:
            hdd_icon.setText("")
        hdd_icon.setStyleSheet("background: transparent;")
        chip_row.addWidget(hdd_icon)

        self._disk_count_label = QLabel("--")
        self._disk_count_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Bold))
        self._disk_count_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        chip_row.addWidget(self._disk_count_label)

        unit = QLabel(tr("disks"))
        unit.setFont(QFont("Segoe UI", S.font_pt(9)))
        unit.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        chip_row.addWidget(unit)

        row.addWidget(chip)

    def set_disk_count(self, count: int):
        self._disk_count_label.setText(str(count))

    def set_live(self, live: bool):
        colors = theme_manager.colors
        self._live_state = live
        c = colors.ACCENT_GREEN if live else colors.TEXT_MUTED
        self._live_dot.setStyleSheet(
            f"background-color: {c}; border-radius: {S.px(4)}px;"
        )

    def _on_theme_changed(self, _):
        self._setup_ui()
        self.set_live(self._live_state)


# ─────────────────────────────────────────────────────────────────────────────
# StorageKpiCard — individual metric tile with animated top accent bar
# ─────────────────────────────────────────────────────────────────────────────
class StorageKpiCard(QFrame, ScaleMixin, I18nMixin):
    """
    Metric tile: top colored accent line, responsive font scaling, icon + value + unit.
    """
    _ACCENT_H = 3  # px of top accent line (scaled)

    def __init__(self, title: str, icon_name: str, accent: str,
                 unit: str = "", parent=None):
        super().__init__(parent)
        self._title_key = title
        self._title = tr(title)
        self._icon_name = icon_name
        self._accent = accent
        self._unit = unit
        self._value_label: QLabel | None = None
        self._unit_label: QLabel | None = None
        self._title_label: QLabel | None = None
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _):
        self._setup_ui()

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if self._title_label:
            self._title_label.setText(self._title)

    def _setup_ui(self):
        if self.layout() is not None:
            for child in self.findChildren(QWidget):
                child.deleteLater()
            tmp = QWidget()
            tmp.setLayout(self.layout())
            tmp.deleteLater()

        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(S.px(82))
        self.setMinimumWidth(S.px(90))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)

        lay = QVBoxLayout()
        ah = S.px(self._ACCENT_H)
        lay.setContentsMargins(S.px(14), ah + S.px(10), S.px(14), S.px(10))
        lay.setSpacing(S.px(3))
        self.setLayout(lay)

        # Icon + title row
        top = QHBoxLayout()
        top.setSpacing(S.px(6))

        icon_lbl = QLabel()
        try:
            ico = qta.icon(self._icon_name, color=self._accent)
            icon_lbl.setPixmap(ico.pixmap(S.px(14), S.px(14)))
        except Exception:
            icon_lbl.setText("")
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        top.addWidget(icon_lbl)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._title_label.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        top.addWidget(self._title_label, stretch=1)
        lay.addLayout(top)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
        self._value_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        lay.addWidget(self._value_label)

        # Unit
        self._unit_label = QLabel(self._unit)
        self._unit_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._unit_label.setStyleSheet(
            f"color: {colors.TEXT_MUTED}; background: transparent;"
        )
        lay.addWidget(self._unit_label)
        lay.addStretch()

    # ── top accent line drawn in paintEvent ──────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        r = S.px(12)
        ah = S.px(self._ACCENT_H)
        painter.save()
        painter.setClipRect(0, 0, self.width(), ah)
        painter.setBrush(QColor(self._accent))
        painter.drawRoundedRect(0, 0, self.width(), r * 2, r, r)
        painter.restore()
        painter.end()

    # ── adaptive font scaling ─────────────────────────────────────────────
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        w = event.size().width()
        if w < 10:
            return
        for lbl, lo, hi, div in [
            (self._value_label,  11, 22, 9),
            (self._title_label,   8, 11, 16),
            (self._unit_label,    7, 10, 18),
        ]:
            if lbl is None:
                continue
            pt = max(lo, min(hi, w // div))
            f = lbl.font()
            if f.pointSize() != pt:
                f.setPointSize(pt)
                lbl.setFont(f)

    def set_value(self, value: str, unit: str = ""):
        if self._value_label:
            self._value_label.setText(value)
        if unit and self._unit_label:
            self._unit_label.setText(unit)
