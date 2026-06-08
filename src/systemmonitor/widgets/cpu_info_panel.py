"""
CpuInfoPanel - CPU information display panel
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin


class CpuInfoPanel(QWidget, ScaleMixin, I18nMixin):
    """
    CPU information panel with 3-column layout:
    - Left: CPU name, architecture, uptime
    - Center: Base clock, cores, threads, cache
    - Right: Usage %, processes, threads, interrupts/sec
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._info = {}
        self._uptime_seconds = 0
        self._label_widgets: list = []
        self.scale_connect()
        self.i18n_connect()
        self._setup_ui()

    def retranslate_ui(self):
        for lbl, source_text in self._label_widgets:
            lbl.setText(tr(source_text))

    def _setup_ui(self):
        """Setup the UI"""
        c = theme_manager.colors

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        self.setLayout(main_layout)

        # Title
        title = QLabel(tr("CPU Information"))
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Content card
        self._card = QFrame()
        self._card.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: 1px solid {c.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        main_layout.addWidget(self._card)

        # 3-column grid
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(24)
        self._card.setLayout(grid_layout)

        # Left column - Basic info
        self._left_col = self._create_info_column()
        grid_layout.addWidget(self._left_col, stretch=1)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"border: 1px solid {c.BORDER};")
        separator.setFixedWidth(1)
        grid_layout.addWidget(separator)

        # Center column - Specs
        self._center_col = self._create_specs_column()
        grid_layout.addWidget(self._center_col, stretch=1)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet(f"border: 1px solid {c.BORDER};")
        separator2.setFixedWidth(1)
        grid_layout.addWidget(separator2)

        # Right column - Usage
        self._right_col = self._create_usage_column()
        grid_layout.addWidget(self._right_col, stretch=1)

    def _create_info_column(self) -> QWidget:
        """Create left info column"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        widget.setLayout(layout)

        # CPU Name
        name_widget = self._create_info_item("CPU", "Unknown")
        self._cpu_name_label = name_widget.item_at(1)
        layout.addWidget(name_widget.widget)

        # Architecture
        arch_widget = self._create_info_item("Architecture", "x64")
        self._arch_label = arch_widget.item_at(1)
        layout.addWidget(arch_widget.widget)

        # Uptime
        uptime_widget = self._create_info_item("Uptime", "0s")
        self._uptime_label = uptime_widget.item_at(1)
        layout.addWidget(uptime_widget.widget)

        layout.addStretch()
        return widget

    def _create_specs_column(self) -> QWidget:
        """Create center specs column"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        widget.setLayout(layout)

        # Base Clock
        clock_widget = self._create_info_item("Base Clock", "0 MHz")
        self._clock_label = clock_widget.item_at(1)
        layout.addWidget(clock_widget.widget)

        # Physical Cores
        cores_widget = self._create_info_item("Physical Cores", "0")
        self._cores_label = cores_widget.item_at(1)
        layout.addWidget(cores_widget.widget)

        # Logical Processors
        threads_widget = self._create_info_item("Logical Processors", "0")
        self._threads_label = threads_widget.item_at(1)
        layout.addWidget(threads_widget.widget)

        # Cache info
        cache_widget = self._create_info_item("Cache", "N/A")
        self._cache_label = cache_widget.item_at(1)
        layout.addWidget(cache_widget.widget)

        layout.addStretch()
        return widget

    def _create_usage_column(self) -> QWidget:
        """Create right usage column"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        widget.setLayout(layout)

        # Current Usage
        usage_widget = self._create_info_item("Current Usage", "0%")
        self._usage_label = usage_widget.item_at(1)
        layout.addWidget(usage_widget.widget)

        # Interrupts/sec
        int_widget = self._create_info_item("Interrupts/sec", "0")
        self._interrupts_label = int_widget.item_at(1)
        layout.addWidget(int_widget.widget)

        layout.addStretch()
        return widget

    def _create_info_item(self, label: str, value: str) -> tuple:
        """Create a label-value pair widget"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        container.setLayout(layout)

        lbl = QLabel(tr(label))
        lbl.setStyleSheet(f"color: {theme_manager.colors.TEXT_MUTED}; font-size: 11px; background: transparent;")
        layout.addWidget(lbl)
        self._label_widgets.append((lbl, label))

        val = QLabel(value)
        val.setStyleSheet(f"color: {theme_manager.colors.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; background: transparent;")
        layout.addWidget(val)

        class Item:
            widget = container
            def item_at(self, index): return layout.itemAt(index).widget()
            def label(self): return lbl
            def value_label(self): return val

        return Item()

    def update_info(self, data: dict):
        """Update panel with CPU data"""
        if 'info' in data:
            info = data['info']
            self._cpu_name_label.setText(info.get('name', tr('Unknown'))[:50])
            self._arch_label.setText(info.get('architecture', 'x64'))

        if 'uptime' in data:
            uptime = data['uptime']
            self._uptime_label.setText(self._format_uptime(uptime))

        if 'specs' in data:
            specs = data['specs']
            if 'frequency' in specs:
                freq = specs['frequency']
                self._clock_label.setText(f"{freq:.0f} MHz")
            self._cores_label.setText(str(specs.get('cores', 0)))
            self._threads_label.setText(str(specs.get('threads', 0)))
            if 'cache' in specs:
                self._cache_label.setText(specs['cache'])

        if 'usage' in data:
            usage = data['usage']
            self._usage_label.setText(f"{usage.get('percent', 0):.1f}%")
            self._interrupts_label.setText(str(usage.get('interrupts', 0)))

            # Color code based on usage
            percent = usage.get('percent', 0)
            if percent > 80:
                color = theme_manager.colors.ACCENT_RED
            elif percent > 60:
                color = theme_manager.colors.ACCENT_ORANGE
            elif percent > 40:
                color = theme_manager.colors.ACCENT_YELLOW
            else:
                color = theme_manager.colors.ACCENT_GREEN
            self._usage_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;")

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human-readable format"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"