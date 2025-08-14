from __future__ import annotations

import datetime
import typing
from collections.abc import Sequence

__all__: Sequence[str] = ("Snowflake",)

DISCORD_EPOCH_MS = 1_420_070_400_000

TIMESTAMP_BITS = 42
WORKER_ID_BITS = 5
PROCESS_ID_BITS = 5
INCREMENT_BITS = 12

INCREMENT_SHIFT = 0
PROCESS_ID_SHIFT = INCREMENT_SHIFT + INCREMENT_BITS
WORKER_ID_SHIFT = PROCESS_ID_SHIFT + PROCESS_ID_BITS
TIMESTAMP_SHIFT = WORKER_ID_SHIFT + WORKER_ID_BITS


@typing.final
class Snowflake(int):
    __slots__: Sequence[str] = ()

    def __repr__(self) -> str:
        return f"Snowflake({int(self)})"

    def __hash__(self) -> int:
        return hash(self)

    @property
    def timestamp(self) -> float:
        return ((self >> TIMESTAMP_SHIFT) + DISCORD_EPOCH_MS) / 1_000

    @property
    def created_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp, tz=datetime.timezone.utc)

    @property
    def internal_worker(self) -> int:
        return (self >> WORKER_ID_SHIFT) & ((1 << WORKER_ID_BITS) - 1)

    @property
    def process_id(self) -> int:
        return (self >> PROCESS_ID_SHIFT) & ((1 << PROCESS_ID_BITS) - 1)

    @property
    def increment(self) -> int:
        return self & ((1 << INCREMENT_BITS) - 1)
