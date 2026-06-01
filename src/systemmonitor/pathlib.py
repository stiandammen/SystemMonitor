"""Pathlib shim for SystemMonitor.
Provides a thin wrapper around the standard library ``pathlib`` so that
imports like ``from systemmonitor.pathlib import Path`` work across the codebase.
"""
from pathlib import Path

__all__ = ["Path"]
