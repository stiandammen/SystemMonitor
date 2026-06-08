import pytest

from systemmonitor.utils import helpers


# ── format_bytes ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("value, expected", [
    (0, "0 B"),
    (None, "0 B"),
    (512, "512.00 B"),
    (1024, "1.00 KB"),
    (1536, "1.50 KB"),
    (1024 ** 3, "1.00 GB"),
    (1024 ** 4, "1.00 TB"),
])
def test_format_bytes(value, expected):
    assert helpers.format_bytes(value) == expected


def test_format_bytes_precision():
    assert helpers.format_bytes(1536, precision=0) == "2 KB"


def test_format_bytes_per_second():
    assert helpers.format_bytes_per_second(1024) == "1.00 KB/s"


# ── format_uptime ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("seconds, expected", [
    (None, "N/A"),
    (-5, "N/A"),
    (45, "0m"),
    (90, "1m"),
    (3661, "1h 1m"),
    (90061, "1d 1h 1m"),
])
def test_format_uptime(seconds, expected):
    assert helpers.format_uptime(seconds) == expected


# ── temperature conversion ────────────────────────────────────────────────
def test_convert_temperature_none():
    assert helpers.convert_temperature(None) is None


def test_convert_temperature_celsius_passthrough():
    assert helpers.convert_temperature(20.0, 'celsius') == 20.0


def test_convert_temperature_to_fahrenheit():
    assert helpers.convert_temperature(0.0, 'fahrenheit') == 32.0
    assert helpers.convert_temperature(100.0, 'fahrenheit') == 212.0


def test_temperature_unit_suffix():
    assert helpers.temperature_unit_suffix('celsius') == '°C'
    assert helpers.temperature_unit_suffix('fahrenheit') == '°F'


def test_format_temperature_none():
    assert helpers.format_temperature(None) == "N/A"


def test_format_temperature_uses_explicit_unit_and_precision(monkeypatch):
    from systemmonitor.config import settings
    monkeypatch.setattr(settings, 'get', lambda key, default=None:
                        {'temperature_unit': 'fahrenheit', 'decimal_places': 2}.get(key, default))
    assert helpers.format_temperature(0.0) == "32.00°F"


def test_format_temperature_parts(monkeypatch):
    from systemmonitor.config import settings
    monkeypatch.setattr(settings, 'get', lambda key, default=None:
                        {'temperature_unit': 'celsius', 'decimal_places': 1}.get(key, default))
    value, unit = helpers.format_temperature_parts(36.6)
    assert value == "36.6"
    assert unit == "°C"


def test_format_temperature_parts_none():
    assert helpers.format_temperature_parts(None) == ("N/A", "")


# ── network speed ─────────────────────────────────────────────────────────
def test_network_speed_value_mbps():
    value, label = helpers.network_speed_value(1_000_000, unit='mbps')
    assert label == 'Mbps'
    assert value == pytest.approx(8.0)


def test_network_speed_value_mbytes():
    value, label = helpers.network_speed_value(1_048_576, unit='mbytes')
    assert label == 'MB/s'
    assert value == pytest.approx(1.0)


def test_network_speed_value_handles_none():
    value, label = helpers.network_speed_value(None, unit='mbps')
    assert value == 0.0
    assert label == 'Mbps'


def test_format_network_speed(monkeypatch):
    from systemmonitor.config import settings
    monkeypatch.setattr(settings, 'get', lambda key, default=None:
                        {'network_speed_unit': 'mbytes', 'decimal_places': 2}.get(key, default))
    assert helpers.format_network_speed(1_048_576) == "1.00 MB/s"


# ── misc formatting ───────────────────────────────────────────────────────
@pytest.mark.parametrize("hz, expected", [
    (0, "0 MHz"),
    (None, "0 MHz"),
    (800, "800 Hz"),
    (2_500_000, "2 MHz"),
    (3_400_000_000, "3.40 GHz"),
])
def test_format_frequency(hz, expected):
    assert helpers.format_frequency(hz) == expected


@pytest.mark.parametrize("value, expected", [
    (None, "N/A"),
    (12.345, "12.3%"),
])
def test_format_percentage(value, expected):
    assert helpers.format_percentage(value) == expected


def test_format_number_int_uses_thousands_separator():
    assert helpers.format_number(1_234_567) == "1,234,567"


def test_format_number_float_uses_precision():
    assert helpers.format_number(1234.5678, precision=1) == "1,234.6"


def test_format_number_none():
    assert helpers.format_number(None) == "N/A"


def test_truncate_string():
    assert helpers.truncate_string("hello world", 8) == "hello..."
    assert helpers.truncate_string("short", 10) == "short"
    assert helpers.truncate_string(None, 5) == ""


# ── numeric helpers ───────────────────────────────────────────────────────
def test_clamp():
    assert helpers.clamp(5, 0, 10) == 5
    assert helpers.clamp(-1, 0, 10) == 0
    assert helpers.clamp(11, 0, 10) == 10


def test_lerp():
    assert helpers.lerp(0.0, 10.0, 0.5) == 5.0
    assert helpers.lerp(0.0, 10.0, -1.0) == 0.0
    assert helpers.lerp(0.0, 10.0, 2.0) == 10.0


def test_smoothstep():
    assert helpers.smoothstep(0.0, 1.0, -1.0) == 0.0
    assert helpers.smoothstep(0.0, 1.0, 2.0) == 1.0
    assert helpers.smoothstep(0.0, 1.0, 0.5) == pytest.approx(0.5)
