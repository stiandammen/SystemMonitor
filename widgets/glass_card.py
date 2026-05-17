"""
Premium Glass Card Widget - Glassmorphism container with green glow
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QGradient
from typing import Optional

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class GlassCard(QFrame, ScaleMixin):
    """
    Premium glass card with transparency, rounded corners, and subtle green glow
    Modern enterprise-grade container for dashboard elements
    """

    def __init__(self, title: str = "", icon: str = "", glow_color: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._glow_color = glow_color
        self._isHovered = False
        self._hover_animation_value = 0.0
        self.scale_connect()
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()
        self.update()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup card UI"""
        self.setMinimumHeight(S.px(120))

        # Enable hover tracking
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Main layout
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(S.px(20), S.px(16), S.px(20), S.px(16))
        self._layout.setSpacing(S.px(12))
        self.setLayout(self._layout)

        # Header (title + icon)
        if self._title or self._icon:
            self._header = QHBoxLayout()
            self._header.setSpacing(S.px(10))

            # Icon
            if self._icon:
                self._icon_label = QLabel(self._icon)
                self._icon_label.setStyleSheet("font-size: 18px; background: transparent;")
                self._header.addWidget(self._icon_label)

            # Title
            if self._title:
                self._title_label = QLabel(self._title)
                font = QFont("Segoe UI", S.font_pt(13), QFont.Weight.DemiBold)
                self._title_label.setFont(font)
                self._header.addWidget(self._title_label)

            self._header.addStretch()
            self._layout.addLayout(self._header)

        # Content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_widget.setLayout(self._content_layout)
        self._layout.addWidget(self._content_widget, stretch=1)

    def _apply_theme(self):
        """Apply current theme styles with glassmorphism"""
        c = theme_manager.colors
        glow = self._glow_color or c.ACCENT_GREEN

        # Base stylesheet for the frame
        self.setStyleSheet(f"""
            GlassCard, QFrame#GlassCard {{
                background-color: rgba(30, 35, 64, 0.85);
                border: 1px solid rgba(74, 108, 247, 0.25);
                border-radius: {S.px(12)}px;
            }}
            GlassCard:hover, QFrame#GlassCard:hover {{
                border-color: rgba(74, 108, 247, 0.5);
            }}
        """)

    def set_content(self, widget: QWidget):
        """Set the content widget"""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        self._content_layout.addWidget(widget)

    def add_widget(self, widget: QWidget):
        """Add a widget to content area"""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to content area"""
        self._content_layout.addLayout(layout)

    def set_title(self, title: str):
        """Update card title"""
        self._title = title
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)

    def set_icon(self, icon: str):
        """Update card icon"""
        self._icon = icon
        if hasattr(self, '_icon_label'):
            self._icon_label.setText(icon)

    def paintEvent(self, a0):
        """Custom paint for glow effect"""
        super().paintEvent(a0)

        if not hasattr(theme_manager, 'colors'):
            return

        c = theme_manager.colors
        glow = self._glow_color or c.ACCENT_GREEN

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw subtle blue glow border for Heimdal style
        rect = self.rect()
        glow_rect = rect.adjusted(1, 1, -1, -1)

        # Create subtle blue glow pen
        glow_color = QColor(74, 108, 247, 30)
        glow_pen = QPen(glow_color)
        glow_pen.setWidthF(1.5)

        # Draw rounded rect outline with subtle glow
        painter.setPen(glow_pen)
        painter.drawRoundedRect(glow_rect, S.px(12), S.px(12))

        painter.end()


class PremiumMetricCard(QFrame, ScaleMixin):
    """
    Premium metric card with icon, value, sparkline, and green glow accent
    Used for displaying key metrics like CPU, Memory, Network, etc.
    """

    def __init__(self, title: str, icon: str = "", accent: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._accent = accent or theme_manager.colors.ACCENT_GREEN
        self._value = "--"
        self._subtitle = ""
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._apply_styles()
        self.update()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup card UI"""
        self.setMinimumHeight(S.px(140))
        self.setMinimumWidth(S.px(200))
        self._apply_styles()

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(20), S.px(16), S.px(20), S.px(16))
        layout.setSpacing(S.px(10))
        self.setLayout(layout)

        # Header with icon and title
        header = QHBoxLayout()
        header.setSpacing(S.px(10))

        if self._icon:
            icon_label = QLabel(self._icon)
            icon_label.setFont(QFont("Segoe UI", S.font_pt(16)))
            icon_label.setStyleSheet(f"color: {self._accent}; background: transparent;")
            header.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Value display
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(28), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._value_label)

        # Subtitle
        self._subtitle_label = QLabel(self._subtitle)
        self._subtitle_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._subtitle_label.setStyleSheet(f"color: {theme_manager.colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._subtitle_label)

        layout.addStretch()

    def _apply_styles(self):
        """Apply premium glass styles"""
        c = theme_manager.colors

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 35, 64, 0.85);
                border: 1px solid rgba(74, 108, 247, 0.25);
                border-radius: {S.px(12)}px;
            }}
            QFrame:hover {{
                border-color: rgba(74, 108, 247, 0.5);
            }}
        """)

    def set_value(self, value: str, subtitle: str = "", trend: Optional[float] = None):
        """Update the displayed value with optional trend indicator"""
        self._value = value
        self._subtitle = subtitle
        self._trend = trend

        if hasattr(self, '_value_label'):
            self._value_label.setText(value)
        if hasattr(self, '_subtitle_label'):
            self._subtitle_label.setText(subtitle)

        # Update trend indicator
        if hasattr(self, '_trend_label') and trend is not None:
            self._trend_label.setVisible(True)
            if trend > 0:
                self._trend_label.setText(f"↑ {trend:.1f}%")
                self._trend_label.setStyleSheet("color: #00E096; background: transparent;")
            elif trend < 0:
                self._trend_label.setText(f"↓ {abs(trend):.1f}%")
                self._trend_label.setStyleSheet("color: #FF4757; background: transparent;")
            else:
                self._trend_label.setText("→ 0%")
                self._trend_label.setStyleSheet("color: #8A92B2; background: transparent;")
        else:
            if hasattr(self, '_trend_label'):
                self._trend_label.setVisible(False)

    def set_accent(self, accent: str):
        """Update accent color"""
        self._color = accent
        self._setup_ui()
        self.update()

    def push_sparkline(self, value: float):
        """Push a value to the sparkline"""
        if hasattr(self, '_sparkline') and self._sparkline:
            self._sparkline.push(value)


class MetricCard(QFrame, ScaleMixin):
    """
    Professional metric card with trend indicator
    Used for displaying key metrics like CPU, Memory, Network, etc.
    Features: icon, title, large value, sparkline, subtitle with trend
    """

    def __init__(self, title: str, icon: str = "", color: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._color = color or theme_manager.colors.ACCENT_GREEN
        self._value = "--"
        self._subtitle = ""
        self._trend = None
        self._trend_history = []
        self._max_history = 30
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        # Enable hover tracking
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()
        self.update()

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _setup_ui(self):
        """Setup card UI"""
        colors = theme_manager.colors
        self.setMinimumHeight(S.px(150))
        self.setMinimumWidth(S.px(200))
        self._apply_styles()

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(14), S.px(16), S.px(14))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        # Header row: icon + title
        header = QHBoxLayout()
        header.setSpacing(S.px(8))

        if self._icon:
            self._icon_label = QLabel(self._icon)
            self._icon_label.setFont(QFont("Segoe UI", S.font_pt(16)))
            self._icon_label.setStyleSheet(f"color: {self._color}; background: transparent;")
            header.addWidget(self._icon_label)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.Medium))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(self._title_label)
        header.addStretch()

        # Trend indicator (hidden by default)
        self._trend_label = QLabel("")
        self._trend_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        self._trend_label.setStyleSheet("background: transparent;")
        self._trend_label.setVisible(False)
        header.addWidget(self._trend_label)

        layout.addLayout(header)

        # Value display
        self._value_label = QLabel(self._value)
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(26), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._value_label)

        # Subtitle / status
        self._subtitle_label = QLabel(self._subtitle)
        self._subtitle_label.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._subtitle_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._subtitle_label)

        # Sparkline widget
        from widgets.sparkline import SparklineWidget
        self._sparkline = SparklineWidget(colors=[self._color])
        self._sparkline.setFixedHeight(40)
        layout.addWidget(self._sparkline)

    def _apply_styles(self):
        """Apply card styles with hover effect"""
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: rgba(30, 35, 64, 0.85);
                border: 1px solid rgba(74, 108, 247, 0.25);
                border-radius: {S.px(12)}px;
            }}
            MetricCard:hover {{
                border-color: rgba(74, 108, 247, 0.5);
                background-color: rgba(35, 40, 70, 0.9);
            }}
        """)