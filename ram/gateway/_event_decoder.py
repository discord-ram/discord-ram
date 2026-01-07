from typing import Any

import msgspec

from ram.gateway._frame import GatewayFrame
from ram.gateway.events.ready_event import Ready
from ram.gateway.gateway_event import GatewayEvent

EVENT_UNION: type[GatewayEvent[Any]] = Ready


def convert(data: GatewayFrame[Any]) -> GatewayEvent[Any]:
    return msgspec.convert(data, type=EVENT_UNION, from_attributes=True)
