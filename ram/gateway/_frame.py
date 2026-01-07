from typing import Any

from msgspec import Struct

from .op_code import OpCode


class GatewayFrame[T: Any](Struct):
    op: OpCode
    d: T
    s: int | None = None
    t: str | None = None
