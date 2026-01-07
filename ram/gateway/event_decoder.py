from typing import Any

import msgspec

from ram.gateway.gateway_event import GatewayEvent
from ram.gateway.events.ready_event import Ready

EVENT_UNION: type[GatewayEvent[Any]] = Ready


def convert(data: dict[str, Any]) -> GatewayEvent[Any]:
    return msgspec.convert(data, type=EVENT_UNION)
