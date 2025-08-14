from __future__ import annotations

from collections.abc import Sequence

import attrs

from ramx.exceptions import BaseException

__all__: Sequence[str] = (
    "GatewayException",
    "GatewayConnectionError",
    "GatewayServerClosedConnectionError",
    "GatewayTransportError",
    "GatewayTransportationError",
)


@attrs.define(auto_exc=True, slots=True, frozen=True)
class GatewayException(BaseException): ...


class GatewayConnectionError(GatewayException): ...


@attrs.define(auto_exc=True, slots=True, frozen=True, kw_only=True)
class GatewayServerClosedConnectionError(GatewayConnectionError):
    code: int
    message: str
    can_reconnect: bool


class GatewayTransportError(GatewayException): ...


@attrs.define(auto_exc=True, slots=True, frozen=True, kw_only=True)
class GatewayTransportationError(GatewayTransportError):
    code: int
    message: str
