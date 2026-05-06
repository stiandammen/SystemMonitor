"""
Views module - Application pages
"""
from .base import BaseView
from .overview import OverviewView
from .cpu import CPUView
from .gpu import GPUView
from .network import NetworkView
from .memory import MemoryView
from .disks import DisksView
from .settings import SettingsView

__all__ = [
    'BaseView', 'OverviewView', 'CPUView', 'GPUView',
    'NetworkView', 'MemoryView', 'DisksView', 'SettingsView'
]