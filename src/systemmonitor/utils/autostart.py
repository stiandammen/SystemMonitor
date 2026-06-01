"""Windows autostart management (stub).
Provides a minimal AutostartManager implementation that works on any platform.
The real implementation would manipulate the Windows registry, but for cross‑platform
usage we return False / no‑op.
"""
import os

class AutostartManager:
    """Stub manager for autostart handling.
    Returns False on non‑Windows platforms and does nothing otherwise.
    """

    REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "SystemMonitor"

    @staticmethod
    def is_enabled() -> bool:
        """Check if autostart is enabled (stub)."""
        return False

    @staticmethod
    def enable() -> bool:
        """Enable autostart (stub)."""
        return False

    @staticmethod
    def disable() -> bool:
        """Disable autostart (stub)."""
        return False

    @staticmethod
    def toggle() -> bool:
        """Toggle autostart state (stub)."""
        return False
