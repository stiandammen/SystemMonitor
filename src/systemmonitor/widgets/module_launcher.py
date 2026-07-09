"""
Module Launcher — glass-style start screen with clickable module tiles.
An alternative "home" view to the classic sidebar-first layout: a centered,
responsive grid of glass tiles (one per module) plus a minimal top row with
general Windows OS info. Selectable via Settings > Appearance > Home screen.
"""
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QGridLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager, css_color_to_hex
from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.i18n import tr, I18nMixin


def _get_windows_info() -> tuple[str, str]:
    """General OS name + version — intentionally no hardware/live metrics."""
    try:
        if platform.system() == "Windows":
            release = platform.win32_ver()[0] or ""
            edition = ""
            try:
                edition = platform.win32_edition() or ""
            except Exception:
                edition = ""
            os_name = f"Windows {release} {edition}".strip()
            version = platform.win32_ver()[1] or ""
            build = version.split(".")[-1] if version else ""
            version_display = f"Build {build}" if build else (version or "—")
            return os_name, version_display
    except Exception:
        pass
    return platform.system() or "Unknown OS", platform.release() or "—"


def _rgba(hex_or_css: str, alpha: int) -> str:
    """rgba(...) string for a theme color at the given alpha (0-255), accepting
    either a '#rrggbb' value or an existing 'rgba(...)' theme string."""
    hexcolor = css_color_to_hex(hex_or_css)
    color = QColor(hexcolor)
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha / 255:.3f})"


# Module tiles shown on the launcher — key matches MainWindow view names.
MODULE_TILES = [
    {"key": "overview", "label": "Dashboard", "icon": "mdi.view-dashboard",
     "desc": "Live system overview", "accent": "ACCENT_GREEN"},
    {"key": "cpu", "label": "Processor", "icon": "ph.cpu",
     "desc": "CPU load and temperature", "accent": "ACCENT_GREEN"},
    {"key": "gpu", "label": "Graphics", "icon": "ph.monitor",
     "desc": "GPU load and VRAM", "accent": "ACCENT_PURPLE"},
    {"key": "memory", "label": "Memory", "icon": "mdi.memory",
     "desc": "RAM usage and swap", "accent": "ACCENT_BLUE"},
    {"key": "network", "label": "Network", "icon": "ph.wifi-high",
     "desc": "Download and upload speed", "accent": "ACCENT_CYAN"},
    {"key": "storage", "label": "Storage", "icon": "ph.database",
     "desc": "Disk space and I/O", "accent": "ACCENT_ORANGE"},
    {"key": "settings", "label": "Settings", "icon": "ph.gear",
     "desc": "Theme, alerts and units", "accent": "TEXT_SECONDARY"},
]


class ModuleTile(QFrame, ScaleMixin):
    """Clickable glass tile representing one module/view."""

    clicked_with_name = pyqtSignal(str)

    def __init__(self, key: str, label: str, icon_name: str, desc: str,
                 accent: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._label_key = label
        self._icon_name = icon_name
        self._desc_key = desc
        self._accent_attr = accent
        self.setObjectName("ModuleTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scale_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setBlurRadius(S.px(26))
        shadow.setOffset(0, S.px(8))
        self.setGraphicsEffect(shadow)

    def _on_theme_changed(self, theme_name: str):
        self._apply_style()
        self._set_icon()

    def on_scale_changed(self, factor: float):
        self._setup_ui()

    def _accent_color(self) -> str:
        c = theme_manager.colors
        return getattr(c, self._accent_attr, c.ACCENT_GREEN)

    def _setup_ui(self):
        self.setMinimumSize(S.px(148), S.px(140))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        if self.layout() is None:
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setLayout(layout)

            self._badge = QFrame()
            self._badge.setObjectName("ModuleTileBadge")
            badge_layout = QVBoxLayout()
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._badge.setLayout(badge_layout)

            self._icon_label = QLabel()
            self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._icon_label.setStyleSheet("background: transparent; border: none;")
            badge_layout.addWidget(self._icon_label)

            badge_row = QHBoxLayout()
            badge_row.addStretch()
            badge_row.addWidget(self._badge)
            badge_row.addStretch()
            layout.addLayout(badge_row)

            self._title_label = QLabel()
            self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self._title_label)

            self._desc_label = QLabel()
            self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._desc_label.setWordWrap(True)
            layout.addWidget(self._desc_label)
        else:
            layout = self.layout()

        layout.setContentsMargins(S.px(14), S.px(18), S.px(14), S.px(18))
        layout.setSpacing(S.px(8))

        self._badge.setFixedSize(S.px(42), S.px(42))
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(11), QFont.Weight.DemiBold))
        self._desc_label.setFont(QFont("Segoe UI", S.font_pt(8)))

        self._title_label.setText(tr(self._label_key))
        self._desc_label.setText(tr(self._desc_key))

        self._set_icon()
        self._apply_style()

    def _set_icon(self):
        accent = self._accent_color()
        try:
            px = qta.icon(self._icon_name, color=accent).pixmap(QSize(S.px(18), S.px(18)))
            self._icon_label.setPixmap(px)
        except Exception:
            self._icon_label.setText("•")

    def _apply_style(self):
        c = theme_manager.colors
        accent = self._accent_color()

        glass_bg = _rgba(getattr(c, 'BG_CARD_SOLID', c.BG_CARD), 140)
        glass_bg_hover = _rgba(getattr(c, 'BG_CARD_SOLID', c.BG_CARD), 195)
        border = _rgba('#ffffff', 26)
        border_hover = _rgba(accent, 130)
        sheen = _rgba(accent, 115)
        badge_bg = _rgba(accent, 36)
        badge_border = _rgba(accent, 80)

        self.setStyleSheet(f"""
            ModuleTile, QFrame#ModuleTile {{
                background-color: {glass_bg};
                border: 1px solid {border};
                border-top: 1px solid {sheen};
                border-radius: {S.px(16)}px;
            }}
            ModuleTile:hover, QFrame#ModuleTile:hover {{
                background-color: {glass_bg_hover};
                border: 1px solid {border_hover};
                border-top: 1px solid {sheen};
            }}
        """)
        self._badge.setStyleSheet(f"""
            QFrame#ModuleTileBadge {{
                background-color: {badge_bg};
                border: 1px solid {badge_border};
                border-radius: {S.px(11)}px;
            }}
        """)
        self._title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        self._desc_label.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent; border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked_with_name.emit(self._key)
            event.accept()


class ModuleLauncherPage(QWidget, ScaleMixin, I18nMixin):
    """Centered, glass module-grid start screen — alternative entry point
    to the classic sidebar-first layout. Toggled in Settings > Appearance."""

    module_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tiles: list = []
        self._current_cols = -1
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def retranslate_ui(self):
        self._setup_ui()

    def on_scale_changed(self, factor: float):
        self._setup_ui()

    def _setup_ui(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        c = theme_manager.colors
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setLayout(root)

        root.addWidget(self._create_top_row())
        root.addStretch(1)
        root.addWidget(self._create_hero())
        root.addWidget(self._create_grid_wrapper())
        root.addStretch(1)
        root.addWidget(self._create_footer())

        self._current_cols = -1
        self._recompute_grid()

    def _create_top_row(self):
        c = theme_manager.colors
        row = QFrame()
        row.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(24), S.px(16), S.px(24), S.px(4))
        layout.setSpacing(S.px(8))
        row.setLayout(layout)

        layout.addStretch()

        os_name, os_version = _get_windows_info()
        layout.addWidget(self._info_pill(os_name, tr("Operating system")))
        layout.addWidget(self._info_pill(os_version, tr("Version")))

        settings_btn = QFrame()
        settings_btn.setFixedSize(S.px(26), S.px(26))
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(f"""
            background-color: {_rgba('#ffffff', 13)};
            border: 1px solid {_rgba('#ffffff', 18)};
            border-radius: {S.px(7)}px;
        """)
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_btn.setLayout(btn_layout)
        gear = QLabel()
        gear.setStyleSheet("background: transparent; border: none;")
        gear.setPixmap(qta.icon('ph.gear', color=c.TEXT_SECONDARY).pixmap(QSize(S.px(13), S.px(13))))
        btn_layout.addWidget(gear)

        def _open_settings(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.module_selected.emit('settings')

        settings_btn.mouseReleaseEvent = _open_settings
        layout.addWidget(settings_btn)

        return row

    def _info_pill(self, value: str, caption: str) -> QFrame:
        c = theme_manager.colors
        pill = QFrame()
        pill.setStyleSheet(f"""
            background-color: {_rgba('#ffffff', 13)};
            border: 1px solid {_rgba('#ffffff', 18)};
            border-radius: {S.px(8)}px;
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(12), S.px(5), S.px(12), S.px(5))
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setLayout(layout)

        val = QLabel(value)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.DemiBold))
        val.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(val)

        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap.setFont(QFont("Segoe UI", S.font_pt(8)))
        cap.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent; border: none;")
        layout.addWidget(cap)

        return pill

    def _create_hero(self):
        c = theme_manager.colors
        wrap = QFrame()
        wrap.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(24), S.px(20), S.px(24), S.px(22))
        layout.setSpacing(S.px(4))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrap.setLayout(layout)

        title = QLabel(tr("Select a module"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(title)

        subtitle = QLabel(tr("Click a module to open detailed monitoring"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", S.font_pt(10)))
        subtitle.setStyleSheet(f"color: {c.TEXT_SECONDARY}; background: transparent; border: none;")
        layout.addWidget(subtitle)

        return wrap

    def _create_grid_wrapper(self):
        outer = QFrame()
        outer.setStyleSheet("background: transparent; border: none;")
        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(S.px(24), 0, S.px(24), 0)
        outer.setLayout(outer_layout)

        outer_layout.addStretch(1)

        grid_container = QFrame()
        grid_container.setStyleSheet("background: transparent; border: none;")
        grid_container.setMaximumWidth(S.px(4 * 150 + 3 * 14))
        self._grid_layout = QGridLayout()
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(S.px(14))
        grid_container.setLayout(self._grid_layout)

        self._tiles = []
        for item in MODULE_TILES:
            tile = ModuleTile(item["key"], item["label"], item["icon"],
                               item["desc"], item["accent"])
            tile.clicked_with_name.connect(self.module_selected.emit)
            self._tiles.append(tile)

        self._arrange_grid(4)
        outer_layout.addWidget(grid_container)
        outer_layout.addStretch(1)
        self._grid_container = grid_container
        return outer

    def _arrange_grid(self, cols: int):
        while self._grid_layout.count():
            self._grid_layout.takeAt(0)
        for i, tile in enumerate(self._tiles):
            self._grid_layout.addWidget(tile, i // cols, i % cols)
        self._current_cols = cols

    def _recompute_grid(self):
        if not self._tiles:
            return
        cols = max(2, min(4, S.grid_columns_for(self.width(), max_cols=4)))
        if cols != self._current_cols:
            self._arrange_grid(cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recompute_grid()

    def _create_footer(self):
        c = theme_manager.colors
        footer = QFrame()
        footer.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(24), S.px(12), S.px(24), S.px(16))
        layout.setSpacing(S.px(6))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setLayout(layout)

        dot = QFrame()
        dot.setFixedSize(S.px(6), S.px(6))
        dot.setStyleSheet(f"background-color: {c.STATUS_GREEN}; border-radius: {S.px(3)}px;")
        layout.addWidget(dot)

        text = QLabel(tr("All systems operational"))
        text.setFont(QFont("Segoe UI", S.font_pt(8)))
        text.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent; border: none;")
        layout.addWidget(text)

        return footer
