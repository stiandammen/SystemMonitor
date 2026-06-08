"""
Overview Page widgets - premium glass dashboard components
Extracted from views/overview_page.py to keep view files small and let these
premium components be reused elsewhere (e.g. a future "Dashboard" overlay).
"""
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from systemmonitor.widgets.sparkline import SparklineWidget
from systemmonitor.styles.theme import theme_manager
from systemmonitor.scaler import S
from systemmonitor.i18n import tr, I18nMixin


class GlassMetricCard(QFrame, I18nMixin):
    """Premium glass metric card - responsive with minimum sizes"""

    def __init__(self, title: str, icon: str, color: str | None = None, parent=None):
        super().__init__(parent)
        self._color = color or theme_manager.colors.ACCENT_GREEN
        self._title_key = title
        self._title = tr(title)
        self._icon = icon
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if hasattr(self, '_title_label'):
            self._title_label.setText(self._title)

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(S.px(120))
        self.setMinimumWidth(S.px(160))

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    background-color: {colors.BG_HOVER};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
                QFrame:hover {{
                    background-color: {colors.BG_HOVER};
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(6))
        self.setLayout(layout)

        header = QHBoxLayout()
        header.setSpacing(S.px(8))

        if self._icon:
            icon_label = QLabel()
            icon_label.setStyleSheet("background: transparent;")
            if '.' in self._icon and not self._icon.startswith('http'):
                try:
                    sz = S.px(20)
                    px = qta.icon(self._icon, color=self._color).pixmap(QSize(sz, sz))
                    icon_label.setPixmap(px)
                    icon_label.setFixedSize(sz, sz)
                except Exception:
                    icon_label.setText("•")
            else:
                icon_label.setText(self._icon)
                icon_label.setFont(QFont("Segoe UI", S.font_pt(14)))
                icon_label.setStyleSheet(f"color: {self._color}; background: transparent;")
            header.addWidget(icon_label)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        header.addWidget(self._title_label)
        header.addStretch()

        layout.addLayout(header)

        self._value_label = QLabel("--")
        self._value_label.setFont(QFont("Segoe UI", S.font_pt(24), QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._value_label)

        self._subtitle_label = QLabel("")
        self._subtitle_label.setFont(QFont("Segoe UI", S.font_pt(9)))
        self._subtitle_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._subtitle_label)

        self._sparkline = SparklineWidget(colors=[self._color])
        self._sparkline.setMinimumHeight(S.px(30))
        self._sparkline.setMaximumHeight(S.px(50))
        layout.addWidget(self._sparkline)

    def set_value(self, value: str, subtitle: str = ""):
        self._value_label.setText(value)
        self._subtitle_label.setText(subtitle)

    def set_color(self, color: str):
        self._color = color

    def push_sparkline(self, value: float):
        self._sparkline.push(value)


class GlassChartPanel(QFrame, I18nMixin):
    """Premium glass chart panel with title and sparkline - responsive"""

    def __init__(self, title: str, color: str | None = None, parent=None):
        super().__init__(parent)
        self._title_key = title
        self._title = tr(title)
        self._color = color or theme_manager.colors.ACCENT_GREEN
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if hasattr(self, '_title_label'):
            self._title_label.setText(self._title)

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(S.px(80))
        self.setMinimumWidth(S.px(140))

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    border-color: rgba(74, 108, 247, 0.5);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(14), S.px(10), S.px(14), S.px(10))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self._title_label)

        self._sparkline = SparklineWidget(colors=[self._color])
        self._sparkline.setMinimumHeight(S.px(50))
        self._sparkline.setMaximumHeight(S.px(90))
        layout.addWidget(self._sparkline, stretch=1)

    def push(self, value: float):
        self._sparkline.push(value)

    def push_multi(self, values: list):
        self._sparkline.push_multi(values)


class GlassInfoPanel(QFrame, I18nMixin):
    """Premium glass info panel - responsive"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title_key = title
        self._title = tr(title)
        self._row_labels: list[tuple[QLabel, str]] = []  # (label_widget, label_key)
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        self._setup_ui()

    def retranslate_ui(self):
        self._title = tr(self._title_key)
        if hasattr(self, '_title_label'):
            self._title_label.setText(self._title)
        for label_widget, label_key in self._row_labels:
            label_widget.setText(tr(label_key))

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
                QFrame:hover {{
                    border-color: rgba(74, 108, 247, 0.5);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        self._title_label = QLabel(self._title)
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(self._title_label)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: transparent;")
        layout.addWidget(sep)

        self._content = QVBoxLayout()
        self._content.setSpacing(0)
        layout.addLayout(self._content)

    def add_info_row(self, label: str, value: str, color: str | None = None) -> QLabel:
        """Add a label/value row. Returns the value QLabel so callers can update it later."""
        row = QFrame()
        row.setStyleSheet("background: transparent;")

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, S.px(4), 0, S.px(4))
        row_layout.setSpacing(S.px(10))
        row.setLayout(row_layout)

        indicator = QFrame()
        indicator.setFixedSize(3, 16)
        accent_color = color or theme_manager.colors.ACCENT_GREEN
        indicator.setStyleSheet(f"background-color: {accent_color}; border-radius: 1px;")
        row_layout.addWidget(indicator)

        label_widget = QLabel(tr(label))
        label_widget.setFont(QFont("Segoe UI", S.font_pt(10)))
        label_widget.setMinimumWidth(80)
        label_widget.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; background: transparent;")
        row_layout.addWidget(label_widget)
        self._row_labels.append((label_widget, label))

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Segoe UI", S.font_pt(10)))
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_widget.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY}; background: transparent;")
        row_layout.addWidget(value_widget, stretch=1)

        self._content.addWidget(row)
        return value_widget


class AnimatedBar(QProgressBar):
    """Progress bar that smoothly fills to its target value via QPropertyAnimation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setMinimumHeight(S.px(8))
        self.setMaximumHeight(S.px(10))
        self._anim = QPropertyAnimation(self, b"value", self)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fill_from_zero(self, target: int):
        self._anim.stop()
        self._anim.setDuration(750)
        self._anim.setStartValue(0)
        self._anim.setEndValue(max(0, min(100, target)))
        self._anim.start()

    def update_value(self, target: int):
        self._anim.stop()
        self._anim.setDuration(300)
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(max(0, min(100, target)))
        self._anim.start()


class GlassStoragePanel(QFrame, I18nMixin):
    """Storage panel with animated bars and live drive info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_partitions = []
        self._drive_keys = []       # ordered list of device strings currently shown
        self._drive_refs = {}       # device -> {bar, pct_lbl, used_lbl, free_lbl, letter, name}
        self.i18n_connect()
        self._setup_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def retranslate_ui(self):
        self._title_label.setText(tr("Storage Drives"))
        if self._last_partitions:
            self._rebuild_drives(self._last_partitions, animate=False)

    def _on_theme_changed(self, theme_name: str):
        colors = theme_manager.colors
        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)
        self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        if self._last_partitions:
            self._rebuild_drives(self._last_partitions, animate=False)

    def _setup_ui(self):
        colors = theme_manager.colors
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        if theme_manager.current_theme == "heimdal":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 35, 64, 0.85);
                    border: none;
                    border-radius: {S.px(12)}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.BG_CARD};
                    border: none;
                    border-radius: {S.px(14)}px;
                }}
            """)

        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(16), S.px(12), S.px(16), S.px(12))
        layout.setSpacing(S.px(8))
        self.setLayout(layout)

        header = QHBoxLayout()
        self._title_label = QLabel(tr("Storage Drives"))
        self._title_label.setFont(QFont("Segoe UI", S.font_pt(12), QFont.Weight.Bold))
        self._title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(self._title_label)
        header.addStretch()
        layout.addLayout(header)

        self._storage_container = QVBoxLayout()
        self._storage_container.setSpacing(S.px(8))
        layout.addLayout(self._storage_container)

    def _clear_drives(self):
        while self._storage_container.count():
            item = self._storage_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._drive_keys = []
        self._drive_refs = {}

    def _pct_color(self, pct: float) -> str:
        colors = theme_manager.colors
        return (colors.ACCENT_GREEN if pct < 75
                else colors.ACCENT_ORANGE if pct < 90
                else colors.ACCENT_RED)

    def _add_drive_card(self, partition: dict, animate: bool):
        colors = theme_manager.colors
        device = partition.get('device', '')
        mountpoint = partition.get('mountpoint', '')
        total_gb = partition.get('total', 0) / (1024 ** 3)
        used_gb = partition.get('used', 0) / (1024 ** 3)
        free_gb = total_gb - used_gb
        pct = partition.get('percent', 0)
        pct_color = self._pct_color(pct)
        label_text = device.replace("\\", "") if device else "?"

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.BG_SECONDARY};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        row = QHBoxLayout()
        row.setContentsMargins(S.px(14), S.px(12), S.px(14), S.px(12))
        row.setSpacing(S.px(14))
        card.setLayout(row)

        # Drive letter badge
        letter_lbl = QLabel(label_text)
        letter_lbl.setFont(QFont("Segoe UI", S.font_pt(15), QFont.Weight.Bold))
        letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        letter_lbl.setFixedWidth(S.px(44))
        letter_lbl.setStyleSheet(
            f"color: {pct_color}; background: transparent;"
        )
        row.addWidget(letter_lbl)

        # Center: name + bar + stats
        info = QVBoxLayout()
        info.setSpacing(S.px(4))

        name_lbl = QLabel(mountpoint if mountpoint else device)
        name_lbl.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")
        info.addWidget(name_lbl)

        bar = AnimatedBar()
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-radius: {S.px(4)}px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: {S.px(4)}px;
            }}
        """)
        info.addWidget(bar)

        stats_row = QHBoxLayout()
        used_lbl = QLabel(tr("{0:.1f} GB used").format(used_gb))
        used_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        used_lbl.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        stats_row.addWidget(used_lbl)
        stats_row.addStretch()
        free_lbl = QLabel(tr("{0:.1f} GB free").format(free_gb))
        free_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        free_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        stats_row.addWidget(free_lbl)
        info.addLayout(stats_row)

        row.addLayout(info, stretch=1)

        # Right: percentage box
        pct_box = QFrame()
        pct_box.setStyleSheet(
            f"background-color: {colors.BG_PRIMARY}; border-radius: {S.px(8)}px;"
        )
        pct_col = QVBoxLayout()
        pct_col.setSpacing(1)
        pct_col.setContentsMargins(S.px(10), S.px(6), S.px(10), S.px(6))
        pct_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_box.setLayout(pct_col)

        pct_lbl = QLabel(f"{pct:.0f}%")
        pct_lbl.setFont(QFont("Segoe UI", S.font_pt(16), QFont.Weight.Bold))
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_lbl.setStyleSheet(f"color: {pct_color}; background: transparent;")
        pct_col.addWidget(pct_lbl)

        sub_lbl = QLabel(tr("used"))
        sub_lbl.setFont(QFont("Segoe UI", S.font_pt(8)))
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
        pct_col.addWidget(sub_lbl)

        row.addWidget(pct_box)
        self._storage_container.addWidget(card)

        # Animate or set directly
        if animate:
            bar.fill_from_zero(int(pct))
        else:
            bar.setValue(int(pct))

        self._drive_keys.append(device)
        self._drive_refs[device] = {
            'bar': bar, 'pct_lbl': pct_lbl,
            'used_lbl': used_lbl, 'free_lbl': free_lbl,
            'letter': letter_lbl, 'name': name_lbl,
        }

    def _update_drive_card(self, partition: dict):
        device = partition.get('device', '')
        refs = self._drive_refs.get(device)
        if not refs:
            return
        colors = theme_manager.colors
        total_gb = partition.get('total', 0) / (1024 ** 3)
        used_gb = partition.get('used', 0) / (1024 ** 3)
        free_gb = total_gb - used_gb
        pct = partition.get('percent', 0)
        pct_color = self._pct_color(pct)

        refs['bar'].update_value(int(pct))
        refs['bar'].setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors.BG_PRIMARY};
                border: none;
                border-radius: {S.px(4)}px;
            }}
            QProgressBar::chunk {{
                background-color: {pct_color};
                border-radius: {S.px(4)}px;
            }}
        """)
        refs['pct_lbl'].setText(f"{pct:.0f}%")
        refs['pct_lbl'].setStyleSheet(f"color: {pct_color}; background: transparent;")
        refs['used_lbl'].setText(tr("{0:.1f} GB used").format(used_gb))
        refs['free_lbl'].setText(tr("{0:.1f} GB free").format(free_gb))
        refs['letter'].setStyleSheet(f"color: {pct_color}; background: transparent;")

    def _rebuild_drives(self, partitions: list, animate: bool):
        self._clear_drives()
        colors = theme_manager.colors
        valid = [p for p in partitions if p.get('fstype')]
        if not valid:
            placeholder = QLabel(tr("No drives detected"))
            placeholder.setFont(QFont("Segoe UI", S.font_pt(11)))
            placeholder.setStyleSheet(f"color: {colors.TEXT_MUTED}; background: transparent;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._storage_container.addWidget(placeholder)
            return
        for partition in valid:
            self._add_drive_card(partition, animate=animate)

    def update_drives(self, partitions: list):
        self._last_partitions = partitions
        new_keys = [p.get('device', '') for p in partitions if p.get('fstype')]

        if new_keys != self._drive_keys:
            # Drive set changed – rebuild with entrance animation
            self._rebuild_drives(partitions, animate=True)
        else:
            # Same drives – update in place with smooth transition
            for partition in partitions:
                if partition.get('fstype'):
                    self._update_drive_card(partition)
