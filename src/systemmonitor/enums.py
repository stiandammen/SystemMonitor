"""Enum shim for SystemMonitor."""
import enum
from enum import *

# Export everything from the real enum module
globals().update({k: v for k, v in enum.__dict__.items() if not k.startswith('_')})
