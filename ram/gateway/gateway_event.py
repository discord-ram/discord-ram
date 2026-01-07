from msgspec import Struct


class GatewayEvent[EventT: Struct](Struct, tag_field="t"):
    d: EventT
    s: int
