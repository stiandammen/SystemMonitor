import pytest

from systemmonitor.i18n import tr, language_manager, SUPPORTED_LANGUAGES
from systemmonitor.i18n.strings_no import TRANSLATIONS_NO


@pytest.fixture(autouse=True)
def reset_language():
    """Always return to English so tests don't bleed into each other."""
    original = language_manager.current_language
    yield
    language_manager.set_language(original)
    language_manager.set_language('en')


def test_supported_languages_contains_english_and_norwegian():
    assert 'en' in SUPPORTED_LANGUAGES
    assert 'no' in SUPPORTED_LANGUAGES


def test_tr_returns_source_text_in_english():
    language_manager.set_language('en')
    assert tr("Settings") == "Settings"


def test_tr_translates_known_key_in_norwegian():
    language_manager.set_language('no')
    assert tr("Settings") == TRANSLATIONS_NO["Settings"]


def test_tr_falls_back_to_source_for_unknown_key():
    language_manager.set_language('no')
    assert tr("This string does not exist in any table") == "This string does not exist in any table"


def test_tr_is_idempotent_on_already_translated_text():
    language_manager.set_language('no')
    once = tr("Settings")
    twice = tr(once)
    assert once == twice


def test_tr_supports_format_args():
    language_manager.set_language('en')
    assert tr("Down / Up {0}").format("Mbps") == "Down / Up Mbps"


def test_tr_format_kwargs_falls_back_safely_on_mismatch():
    # No matching placeholder in the source string -> returns translated text untouched
    language_manager.set_language('en')
    assert tr("Settings", unused="x") == "Settings"


def test_set_language_ignores_unknown_codes():
    language_manager.set_language('en')
    language_manager.set_language('xx-not-a-language')
    assert language_manager.current_language == 'en'


def test_set_language_emits_signal_on_change(qapp):
    received = []
    language_manager.set_language('en')
    language_manager.language_changed.connect(received.append)
    try:
        language_manager.set_language('no')
        assert received == ['no']
        assert language_manager.current_language == 'no'
    finally:
        language_manager.language_changed.disconnect(received.append)


def test_set_language_no_signal_when_unchanged(qapp):
    received = []
    language_manager.set_language('en')
    language_manager.language_changed.connect(received.append)
    try:
        language_manager.set_language('en')
        assert received == []
    finally:
        language_manager.language_changed.disconnect(received.append)


def test_get_language_display_name():
    assert language_manager.get_language_display_name('no') == SUPPORTED_LANGUAGES['no']
    assert language_manager.get_language_display_name('zz') == 'zz'


def test_translation_table_has_no_empty_values():
    empty = [k for k, v in TRANSLATIONS_NO.items() if not v]
    assert empty == []
