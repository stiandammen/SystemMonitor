"""Retranslation mixin for widgets/views — mirrors ``ScaleMixin`` in
``systemmonitor.scaler``. Subclasses connect once and override
``retranslate_ui`` to refresh any text drawn from ``tr()``.
"""
from systemmonitor.i18n.manager import language_manager


class I18nMixin:
    """Mixin that wires a widget up to language-change notifications."""

    def i18n_connect(self):
        language_manager.language_changed.connect(self._handle_language_changed)

    def i18n_disconnect(self):
        try:
            language_manager.language_changed.disconnect(self._handle_language_changed)
        except (TypeError, RuntimeError):
            pass

    def _handle_language_changed(self, language: str):
        self.retranslate_ui()

    def retranslate_ui(self):
        """Override in subclasses to refresh displayed text."""
        pass
