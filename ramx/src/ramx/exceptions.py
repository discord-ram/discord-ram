from __future__ import annotations

from collections.abc import Sequence

import attrs
import typing_extensions

__all__: Sequence[str] = ("BaseException",)


@attrs.define(auto_exc=True, slots=True, frozen=True)
class BaseException(Exception):
    message: str

    @typing_extensions.override
    def __str__(self) -> str:
        return self.message
