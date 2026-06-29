"""Pathlib shim for SystemMonitor."""
import pathlib
from pathlib import *

# Export everything from the real pathlib module
globals().update({k: v for k, v in pathlib.__dict__.items() if not k.startswith('_')})
