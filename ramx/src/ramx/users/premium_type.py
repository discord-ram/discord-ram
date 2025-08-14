from __future__ import annotations

import enum
import typing
from collections.abc import Sequence

__all__: Sequence[str] = ("PremiumType",)


@typing.final
class PremiumType(int, enum.Enum):
    NONE = 0
    NITRO_CLASSIC = 1
    NITRO = 2
    NITRO_BASIC = 3
