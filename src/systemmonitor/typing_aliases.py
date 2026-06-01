"""Utility typing definitions for the SystemMonitor package.
Provides shortcuts for common typing aliases used across the codebase.
"""
from __future__ import annotations
import importlib
_std_typing = importlib.import_module('typing')

Any = _std_typing.Any
Callable = _std_typing.Callable
Dict = _std_typing.Dict
Iterable = _std_typing.Iterable
List = _std_typing.List
Literal = _std_typing.Literal
Mapping = _std_typing.Mapping
MutableMapping = _std_typing.MutableMapping
Optional = _std_typing.Optional
Sequence = _std_typing.Sequence
Tuple = _std_typing.Tuple
Union = _std_typing.Union

__all__ = [
    "Any","Callable","Dict","Iterable","List","Literal","Mapping",
    "MutableMapping","Optional","Sequence","Tuple","Union",
]
