"""Typing shim for SystemMonitor.
Provides standard library ``typing`` symbols without conflicting with this module name.
"""
import os
import sys
import sysconfig
import importlib.util

# Locate the real stdlib typing module
_std_path = os.path.join(sysconfig.get_path('stdlib'), 'typing.py')
_spec = importlib.util.spec_from_file_location('typing_std', _std_path)
_std_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_std_mod)

# Explicit static assignments so Pylance can resolve common names
Any = _std_mod.Any
Dict = _std_mod.Dict
List = _std_mod.List
Set = _std_mod.Set
Tuple = _std_mod.Tuple
Optional = _std_mod.Optional
Union = _std_mod.Union
Callable = _std_mod.Callable
Type = _std_mod.Type
TypeVar = _std_mod.TypeVar
Generic = _std_mod.Generic
Protocol = _std_mod.Protocol
Literal = _std_mod.Literal
ClassVar = _std_mod.ClassVar
Final = _std_mod.Final
overload = _std_mod.overload
cast = _std_mod.cast
TYPE_CHECKING = _std_mod.TYPE_CHECKING
NamedTuple = _std_mod.NamedTuple
TypedDict = _std_mod.TypedDict

# Copy ALL remaining stdlib typing attributes so nothing is missing
_this = sys.modules[__name__]
for _attr in dir(_std_mod):
    if not hasattr(_this, _attr):
        setattr(_this, _attr, getattr(_std_mod, _attr))
