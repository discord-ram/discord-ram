from __future__ import annotations

import typing
from collections.abc import Sequence

import msgspec
from typing_extensions import Buffer

from ramx.converters.base import Converter, ConverterMapping

__all__: Sequence[str] = ("EntityFactory", "JsonEntityFactory", "ConverterFactory")

T = typing.TypeVar("T")


@typing.final
class JsonEntityFactory:
    global_dec_hook: Converter[typing.Any] | ConverterMapping

    def __init__(self, global_dec_hook: Converter[typing.Any] | ConverterMapping) -> None:
        self.global_dec_hook = global_dec_hook

    def get_decoder(self, type: type[T], *, strict: bool = True) -> msgspec.json.Decoder[T]:
        return msgspec.json.Decoder(type=type, strict=strict, dec_hook=self.global_dec_hook)

    def decode(self, buf: Buffer, type: type[T], *, strict: bool = True) -> T:
        return msgspec.json.decode(buf, type=type, dec_hook=self.global_dec_hook, strict=strict)


@typing.final
class ConverterFactory:
    global_dec_hook: Converter[typing.Any] | ConverterMapping

    def __init__(self, global_dec_hook: Converter[typing.Any] | ConverterMapping) -> None:
        self.global_dec_hook = global_dec_hook

    def convert(self, obj: typing.Any, type: type[T], *, strict: bool = True) -> T:  # noqa: ANN401
        return msgspec.convert(obj, type=type, dec_hook=self.global_dec_hook, strict=strict)


class EntityFactory:
    def __init__(self, global_dec_hook: Converter[typing.Any] | ConverterMapping) -> None:
        self.json: JsonEntityFactory = JsonEntityFactory(global_dec_hook)
        self.converter: ConverterFactory = ConverterFactory(global_dec_hook)

    def convert(self, obj: typing.Any, type: type[T], *, strict: bool = True) -> T:  # noqa: ANN401
        return self.converter.convert(obj, type, strict=strict)
