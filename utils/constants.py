"""
Constants and Enums for System Monitor
"""
from enum import Enum, auto


class ViewName(Enum):
    """Navigation view names"""
    OVERVIEW = "overview"
    CPU = "cpu"
    GPU = "gpu"
    NETWORK = "network"
    MEMORY = "memory"
    DISKS = "disks"
    PROCESSES = "processes"
    CMD = "cmd"
    SETTINGS = "settings"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ExportFormat(Enum):
    """Data export formats"""
    CSV = "csv"
    JSON = "json"
    TXT = "txt"


class ThemeMode(Enum):
    """Application theme modes"""
    DARK = "dark"
    LIGHT = "light"


class UpdateInterval(Enum):
    """Data update intervals in milliseconds"""
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
    ViewName.PROCESSES: "Processes",
    ViewName.CMD: "CMD",
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
    ViewName.PROCESSES: "fa5s.tools",
    ViewName.CMD: "fa5s.terminal",
    ViewName.SETTINGS: "fa5s.cog",
}

# View icon images (PNG paths - takes precedence over VIEW_ICONS)
VIEW_ICON_IMAGES = {
    ViewName.DISKS: "C:/Users/RSman/Desktop/backup script/SystemMonitor/ssd3.png",
}
