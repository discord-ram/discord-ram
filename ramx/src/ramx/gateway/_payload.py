from __future__ import annotations

import typing
from collections.abc import Sequence

import msgspec

from ramx.gateway.api import OpCode

__all__: Sequence[str] = ("GatewayPayload",)


class GatewayPayload(msgspec.Struct):
    op: OpCode
    d: typing.Any | None = None
    s: int | None = None
    t: str | None = None
