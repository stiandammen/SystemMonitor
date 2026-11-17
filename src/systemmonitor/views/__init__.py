"""
Views module - Application pages
"""
from .base import BaseView
from .gpu import GPUView
from .network import NetworkView
from .memory import MemoryView
from .settings import SettingsView

__all__ = [
    'BaseView', 'GPUView',
    'NetworkView', 'MemoryView', 'SettingsView'
]