"""Internationalization (i18n) package for SystemMonitor.

Usage::

    from systemmonitor.i18n import tr

    label = QLabel(tr("Settings"))

English is the source language used directly in the code; ``tr()`` looks
up a translation for the active language and falls back to the English
text when none exists. Connect to ``language_manager.language_changed`` (or
use ``I18nMixin``) to refresh widget text when the user switches language.
"""
from systemmonitor.i18n.manager import (
    SUPPORTED_LANGUAGES,
    LanguageManager,
    language_manager,
    tr,
)
from systemmonitor.i18n.mixin import I18nMixin

__all__ = [
    "tr",
    "language_manager",
    "LanguageManager",
    "SUPPORTED_LANGUAGES",
    "I18nMixin",
]
