"""
Search Bar Widget
"""
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon

from styles.theme import theme_manager


class SearchBar(QLineEdit):
    """
    Search bar with debounced text changed signal
    """
    
    search_changed = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "Search...", debounce_ms: int = 300, parent=None):
        super().__init__(parent)
        self._debounce_ms = debounce_ms
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_search)
        
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(36)
        
        # Connect text changed
        self.textChanged.connect(self._on_text_changed)
        
        self._apply_style()
    
    def _apply_style(self):
        """Apply search bar styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            SearchBar {{
                background-color: {c.BG_INPUT};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: "Segoe UI";
                font-size: 13px;
            }}
            
            SearchBar:focus {{
                border-color: {c.ACCENT_GREEN};
            }}
            
            SearchBar::placeholder {{
                color: {c.TEXT_MUTED};
            }}
        """)
    
    def _on_text_changed(self, text: str):
        """Handle text change with debounce"""
        self._timer.stop()
        self._timer.start(self._debounce_ms)
    
    def _emit_search(self):
        """Emit search signal"""
        self.search_changed.emit(self.text())
    
    def clear_search(self):
        """Clear search text"""
        self.clear()
        self.search_changed.emit("")
