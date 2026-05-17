"""
Responsive layout utilities for SystemMonitor
Provides CollapsiblePanel, OverlayWidget, and responsive layout helpers.
"""
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty,
    QTimer, QSize
)
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient

from styles.theme import theme_manager
from scaler import S, ScaleMixin, LayoutMode


class CollapsiblePanel(QFrame, ScaleMixin):
    """Collapsible panel that can expand/collapse with smooth animation.
    In compact mode it starts collapsed, in expanded mode it starts expanded."""

    def __init__(self, title: str = "", icon: str = "", accent: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._accent: str = accent or theme_manager.colors.ACCENT_GREEN
        self._is_expanded = not S.is_compact()
        self._content_visible = self._is_expanded
        self._animation_duration = 200
        self._hovered = False
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def _on_theme_changed(self, theme_name: str):
        self._apply_styles()
        self.update()

    def on_scale_changed(self, factor: float):
        self._apply_styles()

    def on_layout_mode_changed(self, mode):
        if mode == LayoutMode.COMPACT:
            self.collapse()
        else:
            self.expand()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._apply_styles()

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setLayout(self._main_layout)

        self._header = self._create_header()
        self._main_layout.addWidget(self._header)

        self._content_area = QWidget()
        self._content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(S.px(16), S.px(8), S.px(16), S.px(16))
        self._content_layout.setSpacing(S.px(8))
        self._content_area.setLayout(self._content_layout)
        self._main_layout.addWidget(self._content_area)

        if not self._is_expanded:
            self._content_area.setVisible(False)

    def _create_header(self):
        colors = theme_manager.colors
        header = QFrame()
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.setMinimumHeight(S.px(44))
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(S.px(16), S.px(10), S.px(16), S.px(10))
        header_layout.setSpacing(S.px(10))
        header.setLayout(header_layout)

        if self._icon:
            icon_label = QLabel(self._icon)
            icon_label.setFont(QFont("Segoe UI", S.font_pt(14)))
            icon_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
            header_layout.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._toggle_icon = QLabel("▼" if self._is_expanded else "▶")
        self._toggle_icon.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._toggle_icon.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header_layout.addWidget(self._toggle_icon)

        header.mousePressEvent = lambda e: self.toggle_expand()
        self._header_widget = header
        return header

    def _apply_styles(self):
        border_color = "rgba(74, 108, 247, 0.25)"

        self.setStyleSheet(f"""
            CollapsiblePanel {{
                background-color: rgba(30, 35, 64, 0.85);
                border: 1px solid {border_color};
                border-radius: {S.px(12)}px;
            }}
            CollapsiblePanel:hover {{
                border-color: rgba(74, 108, 247, 0.5);
            }}
        """)

    def toggle_expand(self):
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        if self._is_expanded:
            return
        self._is_expanded = True
        self._content_visible = True
        self._content_area.setVisible(True)
        self._toggle_icon.setText("▼")
        self._animate_content_height(max_height=500)

    def collapse(self):
        if not self._is_expanded:
            return
        self._is_expanded = False
        self._toggle_icon.setText("▶")
        self._animate_content_height(max_height=0, on_done=lambda: self._content_area.setVisible(False))

    def _animate_content_height(self, max_height: int, on_done=None):
        if on_done:
            QTimer.singleShot(self._animation_duration, on_done)
        self._content_area.setMaximumHeight(max_height if max_height > 0 else 16777215)
        self.updateGeometry()

    def add_widget(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_expanded(self, expanded: bool):
        if expanded:
            self.expand()
        else:
            self.collapse()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        glow_pen = QPen(QColor(74, 108, 247, 25))
        glow_pen.setWidthF(1.5)
        painter.setPen(glow_pen)
        painter.drawRoundedRect(rect, S.px(12), S.px(12))
        painter.end()


class OverlayWidget(QFrame):
    """Transparent desktop overlay widget mode.
    Shows a compact monitoring strip that floats above the desktop."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position = None
        self._pinned = False
        self._setup_overlay()

    def _setup_overlay(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMinimumWidth(S.px(280))
        self.setMinimumHeight(S.px(60))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(S.px(8), S.px(8), S.px(8), S.px(8))
        self._main_layout.setSpacing(S.px(4))
        self.setLayout(self._main_layout)

        self._metrics_row = QHBoxLayout()
        self._metrics_row.setSpacing(S.px(8))
        self._main_layout.addLayout(self._metrics_row)

        self._metric_labels = {}
        for key, icon, color in [
            ("cpu", "CPU", theme_manager.colors.ACCENT_GREEN),
            ("gpu", "GPU", theme_manager.colors.ACCENT_PURPLE),
            ("ram", "RAM", theme_manager.colors.ACCENT_BLUE),
            ("temp", "TMP", theme_manager.colors.ACCENT_RED),
        ]:
            container = QFrame()
            container.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(18, 21, 42, 0.92);
                    border: 1px solid rgba(74, 108, 247, 0.3);
                    border-radius: {S.px(8)}px;
                    padding: {S.px(4)}px;
                }}
            """)
            cl = QVBoxLayout()
            cl.setContentsMargins(S.px(8), S.px(4), S.px(8), S.px(4))
            cl.setSpacing(0)
            container.setLayout(cl)

            lbl_title = QLabel(icon)
            lbl_title.setFont(QFont("Segoe UI", S.font_pt(8), QFont.Weight.Bold))
            lbl_title.setStyleSheet(f"color: {color}; background: transparent;")
            cl.addWidget(lbl_title)

            lbl_value = QLabel("--")
            lbl_value.setFont(QFont("Segoe UI", S.font_pt(14), QFont.Weight.Bold))
            lbl_value.setStyleSheet("color: #E8ECFF; background: transparent;")
            cl.addWidget(lbl_value)

            self._metrics_row.addWidget(container)
            self._metric_labels[key] = lbl_value

    def update_data(self, data: dict):
        if 'cpu' in data:
            pct = data['cpu'].get('percent', 0)
            self._metric_labels['cpu'].setText(f"{pct:.0f}%")

        if 'gpu' in data and data['gpu'].get('available'):
            load = data['gpu'].get('load')
            if load is not None:
                self._metric_labels['gpu'].setText(f"{load:.0f}%")

        if 'memory' in data:
            pct = data['memory'].get('percent', 0)
            self._metric_labels['ram'].setText(f"{pct:.0f}%")

        if 'gpu' in data:
            temp = data['gpu'].get('temperature')
            if temp is not None:
                self._metric_labels['temp'].setText(f"{temp:.0f}°")

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        bg_rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setPen(QPen(QColor(74, 108, 247, 60), 1.5))
        painter.setBrush(QColor(12, 15, 26, 235))
        painter.drawRoundedRect(bg_rect, S.px(12), S.px(12))

        glow_pen = QPen(QColor(74, 108, 247, 40))
        glow_pen.setWidthF(2.0)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bg_rect.adjusted(-1, -1, 1, 1), S.px(13), S.px(13))
        painter.end()

    def mousePressEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self._drag_position = a0.globalPos() - self.frameGeometry().topLeft()
            a0.accept()

    def mouseMoveEvent(self, a0):
        if a0.buttons() == Qt.MouseButton.LeftButton and self._drag_position:
            self.move(a0.globalPos() - self._drag_position)
            a0.accept()

    def mouseReleaseEvent(self, a0):
        self._drag_position = None
        a0.accept()

    def mouseDoubleClickEvent(self, a0):
        from core.window import MainWindow
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                widget.showNormal()
                widget.activateWindow()
                widget.raise_()
                break


class ResponsiveGridLayout:
    """Helper that calculates optimal column count based on available width."""

    @staticmethod
    def columns_for_width(width: int, item_min_width: int = 280) -> int:
        cols = max(1, int(width // (item_min_width * S.scale_factor)))
        return min(cols, 4)

    @staticmethod
    def arrange_widgets(container: QWidget, widgets: list, item_min_width: int = 280):
        layout = container.layout()
        if layout is None:
            layout = QVBoxLayout(container)
            container.setLayout(layout)

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().setParent(None)

        cols = ResponsiveGridLayout.columns_for_width(container.width(), item_min_width)
        row_layout = None
        for i, widget in enumerate(widgets):
            if i % cols == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(S.px(16))
                layout.addLayout(row_layout)
            widget.setParent(container)
            row_layout.addWidget(widget, stretch=1)

        if row_layout:
            for _ in range(cols - (len(widgets) % cols)):
                if len(widgets) % cols != 0:
                    spacer = QWidget()
                    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    row_layout.addWidget(spacer, stretch=1)
                    break


class SmoothProgressBar(QFrame):
    """Premium progress bar with smooth animation and glow effect."""

    def __init__(self, value: int = 0, color: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._value = value
        self._target_value = value
        self._color: str = color or theme_manager.colors.ACCENT_GREEN
        self._animation = QPropertyAnimation(self, b"progress_value")
        self._animation.setDuration(400)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.setMinimumHeight(S.px(8))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def get_progress_value(self) -> int:
        return int(self._value)

    def set_progress_value(self, val: int):
        self._value = val
        self.update()

    progress_value = pyqtProperty(int, get_progress_value, set_progress_value)

    def set_value(self, value: int, animate: bool = True):
        self._target_value = max(0, min(100, value))
        if animate and self._value != self._target_value:
            self._animation.stop()
            self._animation.setStartValue(int(self._value))
            self._animation.setEndValue(self._target_value)
            self._animation.start()
        else:
            self._value = self._target_value
            self.update()

    def set_color(self, color: str):
        self._color = color
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        bg_rect = rect.adjusted(0, 0, 0, 0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 35, 64, 180))
        painter.drawRoundedRect(bg_rect, S.px(4), S.px(4))

        fill_width = int(rect.width() * (self._value / 100.0))
        if fill_width > 0:
            fill_rect = QRectF(0, 0, fill_width, rect.height())
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            color = QColor(self._color)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)
            painter.setBrush(gradient)
            painter.drawRoundedRect(fill_rect.toRect(), S.px(4), S.px(4))

        painter.end()


class GlowLabel(QLabel):
    """Label with optional glow effect for premium metrics."""

    def __init__(self, text: str = "", glow_color: Optional[str] = None, parent=None):
        super().__init__(text, parent)
        self._glow_color: Optional[str] = glow_color

    def set_glow_color(self, color: str):
        self._glow_color = color
        self.update()

    def paintEvent(self, a0):
        if self._glow_color:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            glow_color = QColor(self._glow_color)
            for i in range(3, 0, -1):
                alpha = int(15 / i)
                glow_color.setAlpha(alpha)
                painter.setPen(QPen(glow_color, i * 2))
                rect = self.rect().adjusted(-i*2, -i*2, i*2, i*2)
                painter.drawRect(rect)
            painter.end()
        super().paintEvent(a0)