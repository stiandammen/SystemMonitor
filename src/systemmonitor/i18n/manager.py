"""Translation manager for SystemMonitor.

Mirrors the singleton + Qt-signal pattern used by ``ThemeManager``
(``systemmonitor.styles.theme``): English is the source language (the
strings written directly in the UI code), and other languages are looked
up from a flat ``{english_text: translated_text}`` dictionary. Strings with
no translation fall back to the English source text, so the UI never shows
a raw key.
"""
from PyQt6.QtCore import QObject, pyqtSignal

from systemmonitor.config import settings
from systemmonitor.i18n.strings_no import TRANSLATIONS_NO

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'no': 'Norsk (bokmål)',
}

_TRANSLATIONS = {
    'no': TRANSLATIONS_NO,
}


class LanguageManager(QObject):
    """Manages the application's display language (singleton)."""

    language_changed = pyqtSignal(str)  # Emits the new language code

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._current_language = settings.get('language', 'en')
        if self._current_language not in SUPPORTED_LANGUAGES:
            self._current_language = 'en'

    @property
    def current_language(self) -> str:
        return self._current_language

    def get_language_display_name(self, code: str) -> str:
        return SUPPORTED_LANGUAGES.get(code, code)

    def set_language(self, language: str):
        if language not in SUPPORTED_LANGUAGES:
            return
        if language == self._current_language:
            return
        self._current_language = language
        settings.set('language', language)
        self.language_changed.emit(language)

    def tr(self, text: str, *args, **kwargs) -> str:
        """Translate ``text`` (the English source string) into the current
        language. Falls back to the English text — optionally formatted with
        ``*args``/``**kwargs`` — when no translation is available."""
        table = _TRANSLATIONS.get(self._current_language)
        translated = table.get(text, text) if table else text
        if args or kwargs:
            try:
                return translated.format(*args, **kwargs)
            except (IndexError, KeyError, ValueError):
                return translated
        return translated


# Global singleton instance — mirrors `theme_manager`
language_manager = LanguageManager()


def tr(text: str, *args, **kwargs) -> str:
    """Module-level convenience wrapper around ``language_manager.tr``."""
    return language_manager.tr(text, *args, **kwargs)
