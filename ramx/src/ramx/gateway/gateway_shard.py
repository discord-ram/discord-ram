from __future__ import annotations

import asyncio
import contextlib
import logging
import platform
import sys
import time
import typing
from collections.abc import Sequence
from typing import Final

import msgspec

from ramx.gateway._payload import GatewayPayload, OpCode
from ramx.gateway._transport import GatewayTransport
from ramx.gateway.api import ShardCloseCode, ShardInfo
from ramx.gateway.base_event_manager import BaseEventManager
from ramx.gateway.entity_factory import EntityFactory
from ramx.gateway.exceptions import GatewayServerClosedConnectionError
from ramx.intents import Intents

__all__: Sequence[str] = ("ConnectionProperties", "GatewayShard")

_LIBRARY_NAME: Final[str] = "discord-ram"
_READY: Final[str] = sys.intern("READY")
_RESUMED: Final[str] = sys.intern("RESUMED")


class ConnectionProperties(msgspec.Struct):
    os: str = platform.platform()
    browser: str = _LIBRARY_NAME
    device: str = _LIBRARY_NAME


class Identify(msgspec.Struct, omit_defaults=True):
    token: str
    intents: Intents
    properties: ConnectionProperties = msgspec.field(default_factory=ConnectionProperties)
    compress: bool = False
    large_threshold: int | None = None
    shard: ShardInfo | None = None


class Resume(msgspec.Struct):
    token: str
    session_id: str
    seq: int


class GatewayShard:
    def __init__(
        self,
        *,
        token: str,
        url: str,
        intents: Intents,
        shard_id: int | None = None,
        shard_count: int | None = None,
        entity_factory: EntityFactory,
        event_manager: BaseEventManager[typing.Any, typing.Any],
    ) -> None:
        self._logger: logging.Logger = logging.getLogger("ramx.gateway")

        self._token = token
        self._gateway_url = url

        self._intents = intents

        self._shard_id = shard_id
        self._shard_count = shard_count

        self._entity_factory = entity_factory
        self._event_manager = event_manager

        self._ws: GatewayTransport | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._heartbeat_latency: float = float("nan")
        self._last_heartbeat_ack_received: float = float("nan")
        self._last_heartbeat_sent: float = float("nan")

        self._resume_gateway_url: str | None = None
        self._session_id: str | None = None
        self._seq: int | None = None

        self._is_closing: bool = False

    async def start(self) -> None:
        if self._keep_alive_task:
            raise RuntimeError
        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    async def join(self) -> None:
        if not self._keep_alive_task:
            raise RuntimeError
        await asyncio.wait_for(asyncio.shield(self._keep_alive_task), timeout=None)

    async def close(self) -> None:
        if not self._keep_alive_task:
            raise RuntimeError

        if self._is_closing:
            await self.join()
            return

        self._logger.info("shard has been requested to shutdown")
        self._is_closing = True

        self._keep_alive_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._keep_alive_task

        self._keep_alive_task = None
        self._is_closing = False
        self._logger.info("shard shutdown successfully")

    async def connect(self) -> Sequence[asyncio.Task[None]] | None:
        self._ws = await GatewayTransport.connect(
            self._resume_gateway_url or self._gateway_url, entity_factory=self._entity_factory
        )

        initial_payload = await self._ws.receive()

        if initial_payload.op == OpCode.INVALID_SESSION and initial_payload.d is False:
            self._is_closing = True
            return

        if initial_payload.op == OpCode.RECONNECT:
            await self._ws.close(code=ShardCloseCode.GOING_AWAY, extra=b"reconnecting")
            return

        if initial_payload.op != OpCode.HELLO:
            raise RuntimeError  # Unexcepted API behaviour

        assert initial_payload.d
        heartbeat_interval = initial_payload.d["heartbeat_interval"] / 1_000
        self._logger.debug("received HELLO payload, heartbeat interval is %ss", heartbeat_interval)
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        self._heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval))

        await self._send_identify()
        return (self._heartbeat_task, asyncio.create_task(self._poll_events()))

    async def _send_heartbeat(self) -> None:
        assert self._ws
        self._logger.debug("sending heartbeat")
        await self._ws.send(GatewayPayload(op=OpCode.HEARTBEAT))
        self._last_heartbeat_sent = time.time()

    async def _send_identify(self) -> None:
        assert self._ws
        if self._session_id and self._seq:
            self._logger.debug("resuming session %s [seq:%s]", self._session_id, self._seq)
            await self._ws.send(
                GatewayPayload(
                    op=OpCode.RESUME, d=Resume(token=self._token, session_id=self._session_id, seq=self._seq)
                )
            )
        else:
            self._logger.debug("identifying new session")
            await self._ws.send(
                GatewayPayload(op=OpCode.IDENTIFY, d=Identify(token=self._token, intents=self._intents))
            )

    async def _heartbeat(self, heartbeat_interval: float) -> None:
        while not self._is_closing:
            await self._send_heartbeat()
            await asyncio.sleep(heartbeat_interval)

    async def _poll_events(self) -> None:
        assert self._ws
        while not self._is_closing:
            payload = await self._ws.receive()

            if payload.op == OpCode.DISPATCH:
                self._seq = payload.s
                self._logger.debug("received dispatch: %s [seq:%s]", payload.t, payload.s)

                if payload.t == _READY:
                    assert payload.d
                    self._session_id = payload.d["session_id"]
                    self._resume_gateway_url = payload.d["resume_gateway_url"]
                    self._logger.info(
                        "ready: %s#%s (ID: %s), %s guild(s)%ssession: '%s'",
                        payload.d["user"]["username"],
                        payload.d["user"]["discriminator"],
                        payload.d["user"]["id"],
                        len(payload.d["guilds"]),
                        (
                            f", shard ({'/'.join(map(str, shard_info))}), "
                            if (shard_info := payload.d.get("shard"))
                            else ", "
                        ),
                        self._session_id,
                    )

                elif payload.t == _RESUMED:
                    self._logger.info("resumed session: '%s'", self._session_id)

                assert payload.d
                assert payload.t
                self._event_manager.dispatch(payload=payload.d, event_name=payload.t)  # type: ignore

            elif payload.op == OpCode.RECONNECT:
                self._logger.info("received reconnect payload")
                break

            elif payload.op == OpCode.HEARTBEAT:
                self._logger.debug("received heartbeat request")
                await self._send_heartbeat()

            elif payload.op == OpCode.HEARTBEAT_ACK:
                self._last_heartbeat_ack_received = time.time()
                self._heartbeat_latency = self._last_heartbeat_ack_received - self._last_heartbeat_sent
                self._logger.debug("received heartbeat ack")

            elif payload.op == OpCode.INVALID_SESSION:
                assert payload.d
                can_reconnect: bool = payload.d
                if not can_reconnect:
                    self._seq = None
                    self._resume_gateway_url = None
                    self._session_id = None
                break

            else:
                self._logger.warning("received unknown op %s [%r]", payload.op, payload)

    async def _keep_alive(self) -> None:
        lifetime_tasks: Sequence[asyncio.Task[None]] | None = None

        while not self._is_closing:
            try:
                lifetime_tasks = await self.connect()
                if not lifetime_tasks:
                    raise RuntimeError
                await asyncio.wait(lifetime_tasks, return_when=asyncio.FIRST_COMPLETED)
            except GatewayServerClosedConnectionError as exception:
                if not exception.can_reconnect:
                    break
                self._logger.error("gateway server closed connection: [%s] %s", exception.code, exception.message)
            except Exception as exception:
                raise exception
