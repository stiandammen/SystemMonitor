import pytest

from systemmonitor.config import AppConfig


# ── AppConfig.history_window ──────────────────────────────────────────────
def test_history_window_basic_span():
    points, stride = AppConfig.history_window(duration_seconds=60, interval_ms=1000)
    assert stride >= 1
    assert AppConfig.HISTORY_POINTS_MIN <= points <= AppConfig.HISTORY_POINTS_MAX


def test_history_window_long_span_uses_stride_to_cap_points():
    points, stride = AppConfig.history_window(
        duration_seconds=3600, interval_ms=500, target_points=300)
    assert stride > 1
    assert points <= 300


def test_history_window_invalid_inputs_fall_back_to_target():
    points, stride = AppConfig.history_window(
        duration_seconds="oops", interval_ms=500, target_points=120)
    assert stride == 1
    assert points == 120


# ── SettingsManager (isolated copy, never touches real config file) ──────
def test_settings_loads_defaults_when_no_file_exists(isolated_settings):
    assert isolated_settings.get('theme') == 'cyber-cyan'
    assert isolated_settings.get('language') == 'en'
    assert isolated_settings._config_path.exists()


def test_settings_get_returns_default_for_unknown_key(isolated_settings):
    assert isolated_settings.get('does_not_exist', 'fallback') == 'fallback'


def test_settings_set_persists_to_disk(isolated_settings):
    isolated_settings.set('theme', 'cyberpunk')
    assert isolated_settings.get('theme') == 'cyberpunk'

    import json
    with open(isolated_settings._config_path, 'r', encoding='utf-8') as f:
        on_disk = json.load(f)
    assert on_disk['theme'] == 'cyberpunk'


def test_settings_update_merges_multiple_keys(isolated_settings):
    isolated_settings.update({'ui_scale': 1.5, 'language': 'no'})
    assert isolated_settings.get('ui_scale') == 1.5
    assert isolated_settings.get('language') == 'no'


def test_settings_reset_to_defaults(isolated_settings):
    isolated_settings.set('theme', 'heimdal')
    isolated_settings.reset_to_defaults()
    assert isolated_settings.get('theme') == 'cyber-cyan'


def test_settings_get_all_returns_a_copy(isolated_settings):
    snapshot = isolated_settings.get_all()
    snapshot['theme'] = 'mutated'
    assert isolated_settings.get('theme') == 'cyber-cyan'


def test_settings_loads_existing_file_and_merges_with_defaults(tmp_path, monkeypatch):
    import json
    from systemmonitor.config import SettingsManager

    config_path = tmp_path / "settings.json"
    config_path.write_text(json.dumps({'theme': 'premium', 'custom_key': 'x'}), encoding='utf-8')
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)

    mgr = SettingsManager()
    assert mgr.get('theme') == 'premium'
    assert mgr.get('custom_key') == 'x'
    # Defaults not present in the file are still filled in
    assert mgr.get('language') == 'en'
