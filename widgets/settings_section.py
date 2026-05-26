"""
Settings Section Widget - Grouped settings with title
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from styles.theme import theme_manager
from scaler import S, ScaleMixin


class SettingsSection(QFrame, ScaleMixin):
    """A collapsible section for grouping related settings"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self.scale_connect()
        self._setup_ui()
        self._apply_style()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def on_scale_changed(self, factor: float):
        self._setup_ui()
        self._apply_style()
        self.update()

    def _on_theme_changed(self, theme_name: str):
        """Re-apply style when theme changes"""
        self._apply_style()
        # Re-style all child rows
        layout = self._content_layout
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, '_apply_style'):
                widget._apply_style()

    def _setup_ui(self):
        """Setup section UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(S.px(24), S.px(24), S.px(24), S.px(16))
        layout.setSpacing(S.px(20))
        self.setLayout(layout)

        # Section title
        self._title_label = QLabel(self._title)
        title_font = QFont("Segoe UI", S.font_pt(14))
        title_font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(title_font)
        layout.addWidget(self._title_label)

        # Content container
        self._content_widget = QFrame()
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, S.px(8), 0, S.px(8))
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch()
        self._content_widget.setLayout(self._content_layout)
        layout.addWidget(self._content_widget)

    def _apply_style(self):
        """Apply section styles with glassmorphism effect"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            SettingsSection {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(12)}px;
            }}
        """)
        self._title_label.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent; border: none;")
        self._content_widget.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)

    def add_widget(self, widget):
        """Add a widget to the section content"""
        # Insert before the stretch item
        self._content_layout.insertWidget(self._content_layout.count() - 1, widget)

    def get_content_layout(self):
        """Get the content layout for direct manipulation"""
        return self._content_layout