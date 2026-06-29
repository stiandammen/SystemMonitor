"""Typing shim for SystemMonitor."""
import typing
from typing import *

# Export everything from the real typing module
globals().update({k: v for k, v in typing.__dict__.items() if not k.startswith('_')})
