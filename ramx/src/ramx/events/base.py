from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

import msgspec

from ramx.gateway.api import ShardInfo
from ramx.users.partial_user import PartialUser

__all__: Sequence[str] = ("BaseEvent", "ReadyEvent")


class BaseEvent(msgspec.Struct, kw_only=True):
    __event_name__: ClassVar[str]


class ReadyEvent(BaseEvent):  # move to lifetime_events maybe
    __event_name__ = "READY"

    v: int
    user: PartialUser
    session_id: str
    resume_gateway_url: str
    shard: ShardInfo | None = None
