"""Constants and Enums for SystemMonitor.
Provides resource path helper and several Enum definitions used across the project.
"""
import os
import sys
from systemmonitor.enum import Enum, auto

def get_resource_path(relative_path: str) -> str:
    """Return absolute path to a resource file.
    Works for development (relative to project root) and for PyInstaller builds.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
    else:
        # Project root is one level up from utils package
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class ViewName(Enum):
    """Navigation view names."""
    OVERVIEW = "overview"
    CPU = "cpu"
    GPU = "gpu"
    NETWORK = "network"
    MEMORY = "memory"
    DISKS = "disks"
    SETTINGS = "settings"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ExportFormat(Enum):
    """Data export formats."""
    CSV = "csv"
    JSON = "json"
    TXT = "txt"

class ThemeMode(Enum):
    """Application theme modes."""
    DARK = "dark"
    LIGHT = "light"

class UpdateInterval(Enum):
    """Data update intervals in milliseconds."""
    FAST = 250      # CPU, GPU, RAM, Network
    MEDIUM = 1000   # Processes
    SLOW = 5000     # Metadata, topology

# View display names
VIEW_TITLES = {
    ViewName.OVERVIEW: "Overview",
    ViewName.CPU: "CPU",
    ViewName.GPU: "GPU",
    ViewName.NETWORK: "Network",
    ViewName.MEMORY: "Memory",
    ViewName.DISKS: "Disks",
    ViewName.SETTINGS: "Settings",
}

# View icons (qtawesome icon names)
VIEW_ICONS = {
    ViewName.OVERVIEW: "ph.gauge",
    ViewName.CPU: "mdi.cpu-64-bit",
    ViewName.GPU: "fa5s.desktop",
    ViewName.NETWORK: "mdi.network",
    ViewName.MEMORY: "mdi.memory",
    ViewName.DISKS: "fa5s.server",
    ViewName.SETTINGS: "fa5s.cog",
}

# View icon images (PNG paths - takes precedence over VIEW_ICONS)
VIEW_ICON_IMAGES = {
    ViewName.DISKS: get_resource_path("assets/ssd3.png"),
}
