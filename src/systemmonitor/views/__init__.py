"""
Views module - Application pages
"""
from .base import BaseView
from .cpu import CPUView
from .gpu import GPUView
from .network import NetworkView
from .memory import MemoryView
from .settings import SettingsView

__all__ = [
    'BaseView', 'CPUView', 'GPUView',
    'NetworkView', 'MemoryView', 'SettingsView'
]