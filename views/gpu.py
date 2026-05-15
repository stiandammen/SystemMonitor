"""
GPU View - GPU monitoring with gauges, charts, and real-time data
Modern glassmorphism design with responsive layout
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient

from styles.theme import theme_manager
from scaler import S, ScaleMixin


# Color palette
COLORS = {
    'bg_primary': '#0a0e14',
    'bg_card': '#161f2a',
    'bg_deeper': '#0d1117',
    'bg_hover': '#1e2936',
    'border': '#2a3441',
    'border_card': '#1e2936',
    'text_primary': '#f0f4f8',
    'text_secondary': '#94a3b8',
    'text_muted': '#64748b',
    'accent_blue': '#3b82f6',
    'accent_green': '#10b981',
    'accent_purple': '#8b5cf6',
    'accent_orange': '#f59e0b',
    'accent_cyan': '#06b6d4',
    'accent_red': '#ef4444',
    'accent_yellow': '#ffd740',
}


def sync_colors():
    """Sync COLORS dict with theme_manager.colors"""
    try:
        c = theme_manager.colors
        COLORS.update({
            'bg_primary': c.BG_PRIMARY,
            'bg_card': c.BG_CARD,
            'bg_deeper': c.BG_HOVER,
            'bg_hover': c.BG_HOVER,
            'border': c.BORDER,
            'border_card': c.BORDER,
            'text_primary': c.TEXT_PRIMARY,
            'text_secondary': c.TEXT_SECONDARY,
            'text_muted': c.TEXT_MUTED,
            'accent_blue': c.ACCENT_BLUE,
            'accent_green': c.ACCENT_GREEN,
            'accent_purple': c.ACCENT_PURPLE,
            'accent_orange': c.ACCENT_ORANGE,
            'accent_cyan': c.ACCENT_CYAN,
            'accent_red': c.ACCENT_RED,
            'accent_yellow': c.ACCENT_YELLOW,
        })
    except Exception as e:
        print(f"sync_colors error: {e}")


class GlassCard(QFrame, ScaleMixin):
    """Glass-effect card - optimized without shadow for better performance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_connect()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_card']};
                border-radius: 12px;
            }}
        """)


class GPUGauge(QFrame, ScaleMixin):
    """
    Circular gauge with glow effect and pulse animation on value changes
    """
    def __init__(self, title: str = "", unit: str = "%",
                 min_val: float = 0.0, max_val: float = 100.0,
                 warn_threshold: float = 70.0, crit_threshold: float = 90.0,
                 size: int = 120, parent=None):
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._min_val = min_val
        self._max_val = max_val
        self._warn_threshold = warn_threshold
        self._crit_threshold = crit_threshold
        self._size = size
        self._display_value = 0.0
        self._target_value = 0.0
        self._pending_update = False
        self._subtitle = ""
        self._is_animating = False
        self._glow_intensity = 0.0
        self._last_color = COLORS.get('accent_green', '#0c997f')

        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: transparent; border: none;")

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

        # Animation timer for pulse effect
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_pulse)

        self.scale_connect()

    def on_scale_changed(self, factor: float):
        self.update()

    def _do_update(self):
        self._pending_update = False
        self.update()

    def _animate_pulse(self):
        """Animate the glow pulse effect"""
        if self._glow_intensity > 0:
            self._glow_intensity -= 0.05
            if self._glow_intensity <= 0:
                self._glow_intensity = 0
                self._anim_timer.stop()
        self.update()

    def set_value(self, value: float):
        """Update gauge value with throttling and trigger animation"""
        if value is None:
            value = 0
        old_target = self._target_value
        self._target_value = max(self._min_val, min(value, self._max_val))

        # Trigger pulse animation on significant change
        if abs(self._target_value - old_target) > 1.0 and not self._is_animating:
            self._glow_intensity = 0.8
            if not self._anim_timer.isActive():
                self._anim_timer.start(16)  # ~60fps

        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(16)  # ~60fps for smoother animation

    def set_max_value(self, max_val: float):
        self._max_val = max_val if max_val is not None else 100.0

    def set_subtitle(self, text: str):
        """Set subtitle text shown below the main value (e.g., '/ 16 GB')"""
        self._subtitle = text

    def _get_color_for_value(self, percentage: float) -> str:
        if percentage >= self._crit_threshold:
            return COLORS.get('accent_red', '#ef4444')
        elif percentage >= self._warn_threshold:
            return COLORS.get('accent_orange', '#f97316')
        return COLORS.get('accent_green', '#0c997f')

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = self._size
        center = size / 2

        # Smooth animation towards target
        diff = self._target_value - self._display_value
        if abs(diff) > 0.1:
            self._display_value += diff * 0.15
        else:
            self._display_value = self._target_value

        # Progress calculation
        range_val = self._max_val - self._min_val
        progress = (self._display_value - self._min_val) / range_val if range_val > 0 else 0
        progress = max(0.0, min(1.0, progress))
        current_color = self._get_color_for_value(progress * 100)

        pen_width = 8
        arc_rect = 14

        # Background track
        painter.setPen(QPen(QColor(COLORS['border']), pen_width, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(arc_rect, arc_rect, size - arc_rect * 2, size - arc_rect * 2,
                       135 * 16, -270 * 16)

        # Animated glow effect - enhanced during pulse
        glow_alpha = 40 + int(self._glow_intensity * 80)
        glow_color = QColor(current_color)
        glow_color.setAlpha(glow_alpha)
        glow_pen = QPen(glow_color, pen_width + 6 + int(self._glow_intensity * 8), Qt.PenStyle.SolidLine)
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawArc(arc_rect, arc_rect, size - arc_rect * 2, size - arc_rect * 2,
                       135 * 16, -270 * 16)

        # Progress arc with smooth color transition
        progress_color = QColor(current_color)
        progress_pen = QPen(progress_color, pen_width, Qt.PenStyle.SolidLine)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(arc_rect, arc_rect, size - arc_rect * 2, size - arc_rect * 2,
                       135 * 16, int(-270 * 16 * progress))

        # Outer ring pulse effect during animation
        if self._glow_intensity > 0:
            pulse_color = QColor(current_color)
            pulse_color.setAlpha(int(self._glow_intensity * 30))
            pulse_pen = QPen(pulse_color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pulse_pen)
            painter.drawArc(arc_rect - 4, arc_rect - 4, size - arc_rect * 2 + 8, size - arc_rect * 2 + 8,
                           135 * 16, -270 * 16)

        # Center value - for VRAM gauge show total memory (16) at center with GB below
        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Light))
        painter.setPen(QColor(COLORS['text_primary']))
        if self._title == "VRAM":
            max_val = self._max_val if self._max_val > 0 else 16
            value_text = f"{max_val:.0f}"
            fm = painter.fontMetrics()
            text_width = fm.width(value_text)
            painter.drawText(int(center - text_width / 2), int(center + 5), value_text)
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(COLORS['text_secondary']))
            gb_width = fm.width("GB")
            painter.drawText(int(center - gb_width / 2), int(center + 20), "GB")
        else:
            value_text = f"{self._display_value:.0f}{self._unit}"
            fm = painter.fontMetrics()
            text_width = fm.width(value_text)
            painter.drawText(int(center - text_width / 2), int(center + 5), value_text)

        # Title
        if self._title:
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(COLORS['text_muted']))
            title_width = fm.width(self._title)
            painter.drawText(int(center - title_width / 2), int(center + 35), self._title)

        painter.end()


class StatTile(QFrame, ScaleMixin):
    """Compact stat tile for info display"""
    def __init__(self, label: str = "", value: str = "--", color: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._color = color or COLORS['accent_cyan']
        self.scale_connect()
        self._setup_ui(label, value)

    def _setup_ui(self, label, value):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_deeper']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._value_lbl.setStyleSheet(f"color: {self._color}; background: transparent;")
        layout.addWidget(self._value_lbl)

        self._label_lbl = QLabel(label)
        self._label_lbl.setFont(QFont("Segoe UI", 9))
        self._label_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(self._label_lbl)

    def set_value(self, value: str):
        self._value_lbl.setText(value)

    def set_color(self, color: str):
        self._color = color
        self._value_lbl.setStyleSheet(f"color: {color}; background: transparent;")


class RealtimeGraph(QWidget, ScaleMixin):
    """Real-time line graph with gradient fill - optimized with throttled updates"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_data = []
        self._temp_data = []
        self._max_points = 60
        self._pending_update = False
        self.scale_connect()
        self.setMinimumHeight(160)

        # Throttle updates to ~30fps max
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update)

    def _do_update(self):
        self._pending_update = False
        self.update()

    def update_chart(self, load: float, temp: float):
        self._load_data.append(load if load is not None else 0)
        self._temp_data.append(temp if temp is not None else 0)
        if len(self._load_data) > self._max_points:
            self._load_data.pop(0)
            self._temp_data.pop(0)
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(33)  # ~30fps throttle

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.setBrush(QColor(COLORS['bg_card']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

        # Grid lines
        painter.setPen(QPen(QColor(COLORS['border']), 1, Qt.PenStyle.DotLine))
        for i in range(5):
            y = h * i / 4
            painter.drawLine(0, int(y), w, int(y))

        # Draw load area
        if len(self._load_data) > 1:
            step = w / (self._max_points - 1)
            valid_data = [(i, val) for i, val in enumerate(self._load_data) if val is not None]
            if valid_data:
                points = [(i * step, h - (val / 100.0 * h)) for i, val in valid_data]

                # Fill
                fill_pts = [(0, h)] + points + [(points[-1][0], h)]
                gradient = QLinearGradient(0, 0, 0, h)
                gradient.setColorAt(0, QColor(16, 185, 129, 100))
                gradient.setColorAt(1, QColor(16, 185, 129, 5))
                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)
                from PyQt6.QtCore import QPoint
                qpoints = [QPoint(int(x), int(y)) for x, y in fill_pts]
                if len(qpoints) >= 3:
                    painter.drawPolygon(*qpoints)

                # Load line
                painter.setPen(QPen(QColor(COLORS['accent_green']), 2))
                for i in range(len(points) - 1):
                    painter.drawLine(int(points[i][0]), int(points[i][1]),
                                   int(points[i + 1][0]), int(points[i + 1][1]))

            # Temp line
            temp_points = []
            for i, val in enumerate(self._temp_data):
                if val is not None:
                    x = i * step
                    y = h - (min(val, 100) / 100.0 * h)
                    temp_points.append((x, y))

            if temp_points and temp_points[-1][1] < h:
                painter.setPen(QPen(QColor(COLORS['accent_blue']), 2))
                for i in range(len(temp_points) - 1):
                    painter.drawLine(int(temp_points[i][0]), int(temp_points[i][1]),
                                   int(temp_points[i + 1][0]), int(temp_points[i + 1][1]))

        # Legend
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(COLORS['accent_green']))
        painter.drawText(12, 16, "● Load")
        painter.setPen(QColor(COLORS['accent_blue']))
        painter.drawText(80, 16, "● Temp")

        painter.end()


class GPUView(QWidget, ScaleMixin):
    """GPU monitoring view with modern responsive design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_gpu_data = None
        self.scale_connect()
        sync_colors()  # Sync colors before setup
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self.update()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply styles when theme changes"""
        try:
            # Sync colors first
            sync_colors()
            # Full rebuild like overview_page does
            self._setup_ui()
            self.update()
        except Exception as e:
            print(f"GPU theme change error: {e}")
            import traceback
            traceback.print_exc()

    def _reapply_widget_styles(self):
        """Re-apply styles to widgets that use COLORS"""
        try:
            self._status_dot.setStyleSheet(f"color: {COLORS.get('accent_green', '#0c997f')}; font-size: 14px; background: transparent;")
            self._gpu_name_label.setStyleSheet(f"color: {COLORS.get('accent_cyan', '#22d3ee')}; background: transparent;")
        except Exception as e:
            print(f"GPU style reapply error: {e}")

    def _refresh_all_widgets(self):
        """Refresh all styled widgets"""
        try:
            if hasattr(self, '_header'):
                self._header.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS.get('bg_card', '#151d28')};
                        border-radius: 10px;
                        border: 1px solid {COLORS.get('border', '#2a3a4a')};
                    }}
                """)
        except Exception as e:
            print(f"Widget refresh error: {e}")

    def _setup_ui(self):
        """Setup GPU view UI"""
        # Main layout - no scroll area, fits in content area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Header bar
        header = self._create_header()
        main_layout.addWidget(header)

        # Main content area - responsive grid
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        content.setLayout(content_layout)

        # Gauges section
        gauges_section = self._create_gauges_section()
        content_layout.addWidget(gauges_section)

        # Info cards section
        info_section = self._create_info_section()
        content_layout.addWidget(info_section)

        # Chart section
        chart_section = self._create_chart_section()
        content_layout.addWidget(chart_section, stretch=1)

        main_layout.addWidget(content, stretch=1)

    def _create_header(self):
        """Header with title and GPU status"""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 10px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)
        header.setLayout(layout)

        # Status indicator
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px; background: transparent;")
        layout.addWidget(self._status_dot)

        # Title
        title = QLabel("GPU Monitor")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # GPU name
        self._gpu_name_label = QLabel("—")
        self._gpu_name_label.setFont(QFont("Segoe UI", 11))
        self._gpu_name_label.setStyleSheet(f"color: {COLORS['accent_cyan']}; background: transparent;")
        layout.addWidget(self._gpu_name_label)

        layout.addStretch()

        return header

    def _create_gauges_section(self):
        """Gauges in responsive grid"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        container.setLayout(layout)

        # Make gauges stretch to fill available space
        self._gauge_load = GPUGauge(title="GPU Load", unit="%", max_val=100,
                                   warn_threshold=50, crit_threshold=80, size=100)
        self._gauge_temp = GPUGauge(title="Temp", unit="°C", max_val=100,
                                   warn_threshold=60, crit_threshold=80, size=100)
        self._gauge_vram = GPUGauge(title="VRAM", unit="GB", max_val=16,
                                   warn_threshold=70, crit_threshold=90, size=100)
        self._gauge_power = GPUGauge(title="Power", unit="W", max_val=300,
                                    warn_threshold=200, crit_threshold=280, size=100)
        self._gauge_fan = GPUGauge(title="Fan", unit="%", max_val=100,
                                   warn_threshold=50, crit_threshold=80, size=100)

        for gauge in [self._gauge_load, self._gauge_temp, self._gauge_vram,
                      self._gauge_power, self._gauge_fan]:
            layout.addWidget(gauge, stretch=1)

        return container

    def _create_info_section(self):
        """Info tiles row"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        container.setLayout(layout)

        self._card_model = StatTile("GPU Model", "—", COLORS['accent_cyan'])
        self._card_driver = StatTile("Driver", "—", COLORS['text_secondary'])
        self._card_vram = StatTile("VRAM Used", "—", COLORS['accent_purple'])
        self._card_vram_total = StatTile("VRAM Total", "—", COLORS['accent_purple'])
        self._card_vendor = StatTile("Vendor", "—", COLORS['accent_green'])

        for card in [self._card_model, self._card_driver,
                     self._card_vram, self._card_vram_total, self._card_vendor]:
            layout.addWidget(card, stretch=1)

        return container

    def _create_chart_section(self):
        """Chart with legend"""
        chart_card = QFrame()
        chart_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 10px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        chart_card.setLayout(layout)

        chart_title = QLabel("Performance")
        chart_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        chart_title.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(chart_title)

        self._chart = RealtimeGraph()
        layout.addWidget(self._chart)

        return chart_card

    def update_data(self, data: dict):
        """Update view with GPU data - throttled"""
        if 'gpu' not in data:
            return
        self._pending_gpu_data = data
        if not getattr(self, '_update_scheduled', False):
            self._update_scheduled = True
            QTimer.singleShot(16, self._do_update)

    def _do_update(self):
        """Perform GPU update"""
        self._update_scheduled = False
        data = getattr(self, '_pending_gpu_data', None)
        if not data:
            return

        gpu = data['gpu']

        if not gpu.get('available', False):
            self._status_dot.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 14px; background: transparent;")
            return

        self._status_dot.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px; background: transparent;")

        # GPU info is embedded in the gpu dict itself (name, vendor, vram_mb, driver_version)
        gpu_name = gpu.get('name', '—')
        gpu_vendor = gpu.get('vendor', 'Unknown')
        gpu_vram = gpu.get('vram_mb', 0)
        gpu_driver = gpu.get('driver_version', 'N/A')

        self._gpu_name_label.setText(gpu_name)
        self._card_model.set_value(gpu_name[:35] if gpu_name else 'Unknown')
        self._card_driver.set_value(gpu_driver)
        self._card_vram.set_value(f"{gpu_vram / 1024:.1f} GB" if gpu_vram else "—")
        self._card_vendor.set_value(gpu_vendor)

        load = gpu.get('load', 0)
        mem_used = gpu.get('memory_used', 0)
        mem_total = gpu.get('memory_total', 1)
        temp = gpu.get('temperature', 0) or 0
        power = gpu.get('power', 0) or 0
        fan = gpu.get('fan_speed', 0) or 0

        self._gauge_load.set_value(load)
        self._gauge_temp.set_value(temp)
        self._gauge_vram.set_value(mem_used if mem_used else 0)
        self._gauge_vram.set_max_value(mem_total if mem_total else 16)

        # Set VRAM gauge to show total memory (16) at center with GB below
        if mem_total and mem_total > 0:
            self._gauge_vram.set_subtitle(f"/ {mem_total:.0f} GB")
        else:
            self._gauge_vram.set_subtitle("")

        # Update VRAM info cards
        if mem_total and mem_total > 0:
            self._card_vram.set_value(f"{mem_used:.1f} GB" if mem_used else "—")
            self._card_vram_total.set_value(f"{mem_total:.1f} GB")
        else:
            self._card_vram.set_value("—")
            self._card_vram_total.set_value("—")

        self._gauge_power.set_value(power)
        self._gauge_fan.set_value(fan)
        self._chart.update_chart(load, temp)
        self._last_gpu_data = gpu


from PyQt6.QtWidgets import QSizePolicy
