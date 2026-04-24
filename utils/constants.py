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
    ViewName.SETTINGS: "Settings",
}

# View icons (Unicode)
VIEW_ICONS = {
    ViewName.OVERVIEW: "📊",
    ViewName.CPU: "🔲",
    ViewName.GPU: "🎮",
    ViewName.NETWORK: "🌐",
    ViewName.MEMORY: "💾",
    ViewName.DISKS: "💿",
    ViewName.PROCESSES: "⚙️",
    ViewName.SETTINGS: "🔧",
}
