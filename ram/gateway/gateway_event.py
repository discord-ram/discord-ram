from typing import Generic, TypeVar

import msgspec

EventT = TypeVar("EventT", bound=msgspec.Struct)


class GatewayEvent(msgspec.Struct, Generic[EventT], tag_field="t"):
    data: EventT = msgspec.field(name="d")
    seq: int = msgspec.field(name="s")
