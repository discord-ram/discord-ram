from __future__ import annotations

import typing
from collections.abc import Awaitable, Sequence

from ram.di.types import DependencyFactory

__all__: Sequence[str] = ("DependencyContainer",)

T = typing.TypeVar("T")


class DependencyContainer:
    def __init__(self) -> None:
        self._registry: dict[type[typing.Any], typing.Any | DependencyFactory[typing.Any]] = {}

    def register(self, key: type[T], value: T | DependencyFactory[T]) -> None:
        self._registry[key] = value

    def resolve(self, key: type[T]) -> T | Awaitable[T]:
        if key not in self._registry:
            raise KeyError(f"No dependency registered for {key}")
        value: T | DependencyFactory[T] = self._registry[key]
        if isinstance(value, DependencyFactory):
            return typing.cast(T | Awaitable[T], value())
        return value
