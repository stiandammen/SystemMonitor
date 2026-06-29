"""Datetime shim for SystemMonitor."""
import datetime
from datetime import *

# Export everything from the real datetime module
globals().update({k: v for k, v in datetime.__dict__.items() if not k.startswith('_')})
