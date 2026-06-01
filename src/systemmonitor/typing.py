"""Shim module that re‑exports the standard library ``typing`` symbols."""
from typing import (
    Any, Dict, List, Set, Tuple, FrozenSet, Sequence, Mapping,
    MutableMapping, MutableSequence, Iterable, Iterator, Generator,
    Callable, Awaitable, Coroutine, AsyncGenerator, AsyncIterable,
    AsyncIterator, Type, ClassVar, Final, Literal, TypeVar, Generic,
    Protocol, Union, Optional, overload, cast, no_type_check,
    NamedTuple, TypedDict, IO, TextIO, BinaryIO,
    TYPE_CHECKING, get_type_hints, get_args, get_origin,
    ForwardRef, NewType, runtime_checkable,
)

__all__ = [
    "Any", "Dict", "List", "Set", "Tuple", "FrozenSet", "Sequence",
    "Mapping", "MutableMapping", "MutableSequence", "Iterable", "Iterator",
    "Generator", "Callable", "Awaitable", "Coroutine", "AsyncGenerator",
    "AsyncIterable", "AsyncIterator", "Type", "ClassVar", "Final",
    "Literal", "TypeVar", "Generic", "Protocol", "Union", "Optional",
    "overload", "cast", "no_type_check", "NamedTuple", "TypedDict",
    "IO", "TextIO", "BinaryIO", "TYPE_CHECKING", "get_type_hints",
    "get_args", "get_origin", "ForwardRef", "NewType", "runtime_checkable",
]
