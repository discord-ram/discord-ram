import enum
import logging
from typing import Any

from aiohttp import ClientWebSocketResponse, WSMessage, WSMsgType
from msgspec.json import Decoder, Encoder

from ram.gateway._frame import GatewayFrame
from ram.gateway.exceptions import GatewayTransportClosed
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
        self._decoder: Decoder[GatewayFrame[Any]] = Decoder(GatewayFrame)

    async def receive(self) -> GatewayFrame[Any]:
        message: WSMessage = await self.connection.receive()
        #self._logger.debug("received: %r", message)
        if message.type in {WSMsgType.ERROR, WSMsgType.CLOSE, WSMsgType.CLOSED}:
            raise GatewayTransportClosed(code=message.data, extra=message.extra)
        else:
            return self._decoder.decode(message.data)

    async def send(self, payload: GatewayFrame[Any]) -> None:
        data: bytes = self._encoder.encode(payload)
        await self.connection.send_bytes(data)
        #self._logger.debug("send: %r", payload)
