"""
Theme Manager - Handles application theming
"""
from PyQt6.QtCore import QObject, pyqtSignal


class ThemeManager(QObject):
    """Manages application theme"""
    
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = "dark"
    
    @property
    def current_theme(self):
        return self._current_theme
    
    def set_theme(self, theme_name):
        """Set application theme"""
        if theme_name != self._current_theme:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
    
    def get_stylesheet(self):
        """Get stylesheet for current theme"""
        if self._current_theme == "dark":
            return self._get_dark_stylesheet()
        else:
            return self._get_light_stylesheet()
    
    def _get_dark_stylesheet(self):
        """Dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #0a0e14;
                color: #f0f4f8;
            }
            QWidget {
                background-color: #0a0e14;
                color: #f0f4f8;
            }
            QFrame {
                background-color: #161f2a;
                border: 1px solid #2a3441;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
                color: #f0f4f8;
            }
            QPushButton {
                background-color: #1c2128;
                color: #f0f4f8;
                border: 1px solid #2a3441;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2a3441;
                border-color: #10b981;
            }
        """
    
    def _get_light_stylesheet(self):
        """Light theme stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f7fb;
                color: #0f172a;
            }
            QWidget {
                background-color: #f5f7fb;
                color: #0f172a;
            }
            QFrame {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
            QLabel {
                background-color: transparent;
                color: #0f172a;
            }
            QPushButton {
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #059669;
            }
        """
