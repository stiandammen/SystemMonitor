"""Enum shim for SystemMonitor.
Provides the standard library ``enum`` functionality without conflicting with this module name.
"""
import os
import sys
import sysconfig
import importlib.util

# Locate the real stdlib enum module
this_dir = os.path.dirname(os.path.abspath(__file__))
saved_path = sys.path.copy()
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(this_dir)]
had_enum = 'enum' in sys.modules
old_enum = sys.modules.pop('enum', None)
try:
    import enum as _std_mod
finally:
    sys.path = saved_path
    if had_enum:
        sys.modules['enum'] = old_enum

# Explicit static assignments so Pylance can resolve common names
Enum = _std_mod.Enum
IntEnum = _std_mod.IntEnum
Flag = _std_mod.Flag
IntFlag = _std_mod.IntFlag
StrEnum = getattr(_std_mod, 'StrEnum', _std_mod.Enum)
auto = _std_mod.auto
unique = _std_mod.unique
EnumMeta = _std_mod.EnumMeta
EnumType = getattr(_std_mod, 'EnumType', _std_mod.EnumMeta)

# Copy ALL remaining stdlib enum attributes so nothing is missing (e.g. global_enum, member, nonmember)
_this = sys.modules[__name__]
for _attr in dir(_std_mod):
    if not hasattr(_this, _attr):
        setattr(_this, _attr, getattr(_std_mod, _attr))
