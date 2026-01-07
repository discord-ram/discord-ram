from ram.events.ready_event import ReadyEvent
from ram.gateway.gateway_event import GatewayEvent


class Ready(GatewayEvent[ReadyEvent], tag="READY"): ...
