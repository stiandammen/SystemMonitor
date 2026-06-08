import pytest

from systemmonitor.styles.theme import theme_manager


@pytest.fixture(autouse=True)
def reset_theme(qapp):
    """Restore the default theme so tests don't bleed into each other."""
    original = theme_manager.current_theme
    yield
    theme_manager.set_theme(original)
    theme_manager.set_theme('cyber-cyan')


def test_default_theme_is_cyber_cyan():
    theme_manager.set_theme('cyber-cyan')
    assert theme_manager.current_theme == 'cyber-cyan'


def test_get_available_themes_includes_known_themes():
    available = theme_manager.get_available_themes()
    for key in ('cyber-cyan', 'premium', 'cyberpunk', 'heimdal'):
        assert key in available


def test_set_theme_switches_current_theme_and_colors():
    theme_manager.set_theme('cyberpunk')
    assert theme_manager.current_theme == 'cyberpunk'
    assert theme_manager.colors.__class__.__name__ == 'CyberpunkTheme'


def test_set_theme_unknown_name_falls_back_to_cyber_cyan():
    theme_manager.set_theme('cyber-cyan')
    theme_manager.set_theme('does-not-exist')
    assert theme_manager.current_theme == 'cyber-cyan'


def test_set_theme_emits_signal_on_change():
    received = []
    theme_manager.set_theme('cyber-cyan')
    theme_manager.theme_changed.connect(received.append)
    try:
        theme_manager.set_theme('heimdal')
        assert received == ['heimdal']
    finally:
        theme_manager.theme_changed.disconnect(received.append)


def test_set_theme_no_signal_when_unchanged():
    received = []
    theme_manager.set_theme('premium')
    theme_manager.theme_changed.connect(received.append)
    try:
        theme_manager.set_theme('premium')
        assert received == []
    finally:
        theme_manager.theme_changed.disconnect(received.append)


def test_get_theme_display_name():
    assert theme_manager.get_theme_display_name('cyber-cyan') == 'Cyber Cyan'
    assert theme_manager.get_theme_display_name('made-up') == 'Made-Up'


def test_toggle_theme_switches_between_cyber_cyan_and_premium():
    theme_manager.set_theme('cyber-cyan')
    theme_manager.toggle_theme()
    assert theme_manager.current_theme == 'premium'
    theme_manager.toggle_theme()
    assert theme_manager.current_theme == 'cyber-cyan'


def test_get_stylesheet_returns_non_empty_string():
    theme_manager.set_theme('cyber-cyan')
    stylesheet = theme_manager.get_stylesheet()
    assert isinstance(stylesheet, str)
    assert len(stylesheet) > 0
