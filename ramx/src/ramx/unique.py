from __future__ import annotations

import datetime
import typing
from collections.abc import Sequence

import msgspec
import typing_extensions

from ramx.snowflakes import Snowflake

__all__: Sequence[str] = ("Unique",)


class Unique(msgspec.Struct):
    id: Snowflake

    @property
    def created_at(self) -> datetime.datetime:
        return self.id.created_at

    @typing.final
    def __index__(self) -> int:
        return int(self.id)

    @typing.final
    def __int__(self) -> int:
        return int(self.id)

    @typing_extensions.override
    def __hash__(self) -> int:
        return hash(self.id)

    @typing_extensions.override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self.id == other.id
        return False
