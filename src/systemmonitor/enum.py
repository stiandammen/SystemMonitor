"""Enum shim for SystemMonitor.
Provides the standard library ``enum`` functionality without conflicting with this module name.
"""
import os
import sys
import sysconfig
import importlib.util

# Locate the real stdlib enum module file
_std_path = os.path.join(sysconfig.get_path('stdlib'), 'enum.py')
_spec = importlib.util.spec_from_file_location('enum_std', _std_path)
_std_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_std_mod)

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
