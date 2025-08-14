from __future__ import annotations

import asyncio
import logging
import typing
import zlib
from collections.abc import Sequence
from contextlib import AsyncExitStack

from aiohttp import WSMessage, WSMsgType
from aiohttp.client import ClientSession, ClientWebSocketResponse
from aiohttp.typedefs import StrOrURL
from msgspec import json

from ramx.gateway.api import ShardCloseCode
from ramx.gateway.entity_factory import EntityFactory
from ramx.gateway.exceptions import GatewayConnectionError, GatewayServerClosedConnectionError, GatewayTransportError

from ._payload import GatewayPayload

if typing.TYPE_CHECKING:
    from zlib import _Decompress as Decompress  # type: ignore

__all__: Sequence[str] = ("GatewayTransport",)

ZLIB_SUFFIX: typing.Final[bytes] = b"\x00\x00\xff\xff"

_RECONNECTABLE_SHARD_CLOSING_CODES: frozenset[ShardCloseCode] = frozenset(
    {
        ShardCloseCode.UNKNOWN_ERROR,
        ShardCloseCode.UNKNOWN_OPCODE,
        ShardCloseCode.DECODE_ERROR,
        ShardCloseCode.AUTHENTICATION_FAILED,
        ShardCloseCode.ALREADY_AUTHENTICATED,
        ShardCloseCode.AUTHENTICATION_FAILED,
        ShardCloseCode.ALREADY_AUTHENTICATED,
        ShardCloseCode.INVALID_SEQ,
        ShardCloseCode.RATE_LIMITED,
        ShardCloseCode.SESSION_TIMEOUT,
    }
)


@typing.final
class GatewayTransport:
    __slots__: Sequence[str] = (
        "_connection",
        "_entity_factory",
        "_compression",
        "_exit_stack",
        "_stop_event",
        "_decoder",
        "_encoder",
        "_inflator",
        "_buffer",
    )

    _logger: logging.Logger = logging.getLogger("ram.gateway.transport")

    @classmethod
    async def connect(
        cls, url: StrOrURL, *, entity_factory: EntityFactory, compression: bool = False
    ) -> GatewayTransport:
        exit_stack: AsyncExitStack = AsyncExitStack()
        client_session: ClientSession = ClientSession()
        await exit_stack.enter_async_context(client_session)
        try:
            connection = await exit_stack.enter_async_context(
                client_session.ws_connect(url, max_msg_size=0, autoclose=False)
            )
        except Exception as exception:
            raise GatewayConnectionError("Connection error") from exception
        return cls(connection, exit_stack, entity_factory=entity_factory, compression=compression)

    def __init__(
        self,
        connection: ClientWebSocketResponse,
        exit_stack: AsyncExitStack,
        *,
        entity_factory: EntityFactory,
        compression: bool,
    ) -> None:
        self._connection = connection
        self._exit_stack = exit_stack
        self._entity_factory = entity_factory
        self._compression = compression

        self._stop_event: asyncio.Event = asyncio.Event()

        self._decoder: json.Decoder[GatewayPayload] = self._entity_factory.json.get_decoder(GatewayPayload)
        self._encoder: json.Encoder = json.Encoder()

        self._inflator: Decompress | None = zlib.decompressobj() if self._compression else None
        self._buffer: bytearray | None = bytearray() if self._compression else None

    async def send(self, payload: GatewayPayload, *, compression: bool = False) -> None:
        await self._connection.send_bytes(data=memoryview(self._encoder.encode(payload)))

    async def close(self, code: int, extra: bytes = b"") -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        self._logger.debug("closing websocket connection with code %s", code)
        try:
            if not self._connection.closed:
                await asyncio.wait_for(self._connection.close(code=code, message=extra), timeout=5)
        except Exception as exc:
            self._logger.warning("exception during websocket close: %r", exc)
        finally:
            await self._exit_stack.aclose()

    async def receive_stream(self, data: bytes) -> GatewayPayload:
        assert self._inflator is not None
        assert self._buffer is not None
        self._buffer.extend(data)
        while not self._buffer.endswith(ZLIB_SUFFIX):
            data = await self._connection.receive_bytes()
            self._buffer.extend(data)
        data = self._inflator.decompress(self._buffer)
        payload = self._decoder.decode(data)
        self._buffer.clear()
        self._logger.debug("received [%r]", payload)
        return payload

    async def receive(self) -> GatewayPayload:
        message: WSMessage = await self._connection.receive()

        if message.type == WSMsgType.CLOSE:
            close_code = int(message.data)
            can_reconnect = close_code < 4_000 or close_code in _RECONNECTABLE_SHARD_CLOSING_CODES  # noqa: PLR2004  # TODO: replace magic value
            raise GatewayServerClosedConnectionError(
                message=message.extra or "", code=close_code, can_reconnect=can_reconnect
            )

        if message.type in {WSMsgType.CLOSING, WSMsgType.CLOSED}:
            raise GatewayConnectionError(message="Socket has closed")

        if message.type == WSMsgType.ERROR:
            raise GatewayConnectionError(message=f"WebSocket error: {self._connection.exception()}")

        if message.type == WSMsgType.BINARY:
            if self._compression:
                return await self.receive_stream(message.data)
            return self._decoder.decode(message.data)

        if message.type == WSMsgType.TEXT:
            if self._compression:
                raise GatewayTransportError(message="Received text data but compression is enabled")
            return self._decoder.decode(message.data)

        raise GatewayTransportError(message=f"Unexpected message type: {message.type}")
