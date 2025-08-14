from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Generic, TypeVar, cast

__all__: Sequence[str] = ("Converter", "ConverterMapping", "converter")

T = TypeVar("T")
V = TypeVar("V")


class Converter(Generic[T]):
    def __init__(self, type_: type[T], callback: Callable[[Any], T]) -> None:
        self.type_: type[T] = type_
        self.callback: Callable[[Any], T] = callback

    def __call__(self, _: type[T], value: Any) -> T:  # noqa: ANN401
        return self.callback(value)

    def __or__(self, other: Converter[Any]) -> ConverterMapping:
        mapping = ConverterMapping()
        mapping[self.type_] = self
        mapping[other.type_] = other
        return mapping


class ConverterMapping:
    def __init__(self) -> None:
        self._mapping: dict[type[Any], Converter[type[Any]]] = {}

    def __setitem__(self, key: type, value: Converter[Any]) -> None:
        self._mapping[key] = value

    def __getitem__(self, key: type[T]) -> Converter[T]:
        return cast(Converter[T], self._mapping[key])

    def __call__(self, type_: type[T], value: V) -> T | V:
        if converter := self._mapping.get(type_):
            return cast(T, converter(type, value))
        return value

    def __ior__(self, other: ConverterMapping) -> ConverterMapping:
        self._mapping.update(other._mapping)
        return self

    def __or__(self, other: Converter[type[Any]] | ConverterMapping) -> ConverterMapping:
        if isinstance(other, Converter):
            self[other.type_] = other
        else:
            self |= other
        return self


def converter(type_: type[T]) -> Callable[[Callable[[Any], T]], Converter[T]]:
    def inner(func: Callable[[Any], T]) -> Converter[T]:
        return Converter(type_, func)

    return inner
