import enum
import logging
from typing import Any

from aiohttp import ClientWebSocketResponse, WSMessage, WSMsgType
from msgspec.json import Encoder, Decoder

from ram.gateway.exceptions import GatewayTransportClosed
from ram.gateway.gateway_payload import GatewayPayload
from ram.ws.transport import WebsocketTransport


class CompressionStrategy(enum.Enum):
    ZLIB = "zlib-stream"


class GatewayTransport(WebsocketTransport):
    __slots__: tuple[str, ...] = ("_compression", "_logger", "_encoder", "_decoder")

    def __init__(
        self,
        connection: ClientWebSocketResponse,
        compression: CompressionStrategy | None = None,
    ) -> None:
        super().__init__(connection)
        self._compression = compression

        self._logger: logging.Logger = logging.getLogger("ram.transport")

        self._encoder: Encoder = Encoder()
        self._decoder: Decoder[dict[str, Any]] = Decoder(dict[str, Any])

    async def receive(self) -> dict[str, Any]:
        message: WSMessage = await self.connection.receive()
        if message.type in {WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSED}:
            raise GatewayTransportClosed(code=message.data, extra=message.extra)
        else:
            return self._decoder.decode(message.data)

    async def send(self, payload: GatewayPayload) -> None:
        data: bytes = self._encoder.encode(payload)
        await self.connection.send_bytes(data)
