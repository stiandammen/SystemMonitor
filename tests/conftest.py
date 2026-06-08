import pytest


@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication instance — required before constructing any QObject
    that uses Qt signals (PyQt6 raises if no QCoreApplication exists)."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Give SettingsManager a throwaway config file so tests never touch the
    user's real %APPDATA%/SystemMonitor/settings.json."""
    from systemmonitor.config import SettingsManager

    config_path = tmp_path / "settings.json"
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager()
