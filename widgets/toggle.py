"""
Toggle Switch Widget - iOS-style toggle
"""
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import Qt

from styles.theme import theme_manager


class ToggleSwitch(QCheckBox):
    """
    iOS-style toggle switch
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
    
    def _apply_style(self):
        """Apply toggle switch styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            ToggleSwitch {{
                spacing: 8px;
            }}
            
            ToggleSwitch::indicator {{
                width: 50px;
                height: 26px;
                border-radius: 13px;
                background-color: {c.BORDER};
            }}
            
            ToggleSwitch::indicator:checked {{
                background-color: {c.ACCENT_GREEN};
            }}
            
            ToggleSwitch::indicator::handle {{
                width: 22px;
                height: 22px;
                border-radius: 11px;
                background-color: white;
                margin: 2px;
            }}
            
            ToggleSwitch::indicator:checked::handle {{
                margin-left: 26px;
            }}
        """)
