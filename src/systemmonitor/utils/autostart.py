"""Windows autostart management.

Adds/removes a value under HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
so the app can launch automatically when the user signs in. The Run key lives in
HKEY_CURRENT_USER, so no elevation is required. On non-Windows platforms `winreg`
is unavailable and every operation is a safe no-op that returns False.
"""
import os
import sys

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows platforms
    winreg = None


class AutostartManager:
    """Manages whether SystemMonitor launches automatically at sign-in."""

    REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "SystemMonitor"

    @classmethod
    def _command(cls) -> str:
        """Command line written to the registry to relaunch the app.

        Frozen (PyInstaller) builds run directly from their executable; otherwise
        the interpreter and entry script must both be quoted and passed along.
        """
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}"'
        script = os.path.abspath(sys.argv[0])
        return f'"{sys.executable}" "{script}"'

    @classmethod
    def is_enabled(cls) -> bool:
        """Check whether the Run key currently points at this app."""
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REGISTRY_KEY, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, cls.APP_NAME)
                return bool(value)
        except OSError:
            return False

    @classmethod
    def enable(cls) -> bool:
        """Add (or refresh) the Run key entry so the app starts at sign-in."""
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, cls._command())
            return True
        except OSError:
            return False

    @classmethod
    def disable(cls) -> bool:
        """Remove the Run key entry so the app no longer starts at sign-in."""
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REGISTRY_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, cls.APP_NAME)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False

    @classmethod
    def toggle(cls) -> bool:
        """Flip the current autostart state and return the resulting state."""
        if cls.is_enabled():
            cls.disable()
            return False
        cls.enable()
        return True
