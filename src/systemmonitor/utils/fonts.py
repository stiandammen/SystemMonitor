"""Application font: Cutive Regular (bundled in assets/fonts).

``load_app_font`` registers the bundled TTF and makes it the default font for
the whole application. All widgets that name a family explicitly use
``UI_FONT_FAMILY`` ("Cutive"); if the file cannot be loaded, Qt is told to
substitute "Segoe UI" so the UI still renders normally.
"""
import os
import sys

UI_FONT_FAMILY = "Cutive"
_FONT_FILE = "Cutive-Regular.ttf"


def _font_path() -> str:
    base = getattr(sys, '_MEIPASS', None)
    if base:
        return os.path.join(base, 'systemmonitor', 'assets', 'fonts', _FONT_FILE)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets', 'fonts', _FONT_FILE)


def load_app_font(app) -> str:
    """Register the bundled font and set it as the application default.
    Returns the family name actually in use."""
    from PyQt6.QtGui import QFontDatabase, QFont
    family = UI_FONT_FAMILY
    path = _font_path()
    font_id = QFontDatabase.addApplicationFont(path) if os.path.exists(path) else -1
    if font_id >= 0:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            family = families[0]
    else:
        QFont.insertSubstitution(UI_FONT_FAMILY, "Segoe UI")
        family = "Segoe UI"
    app.setFont(QFont(family, app.font().pointSize()))
    return family
