from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import msgspec

from ram.gateway._event_decoder import convert
from ram.gateway._payloads import Identify, Resume, ShardInfo
from ram.gateway.events.ready_event import Ready
from ram.gateway.exceptions import GatewayShardStateConflict
from ram.gateway.gateway_event import GatewayEvent
from ram.gateway.gateway_transport import GatewayFrame, GatewayTransport
from ram.gateway.op_code import OpCode
from ram.intents import Intents


class GatewayShard:
    def __init__(
        self,
        *,
        token: str,
        gateway_url: str,
        intents: Intents,
        shard_id: int,
        shard_count: int,
    ) -> None:
        self._token = token
        self._gateway_url = gateway_url
        self._intents = intents
        self._shard_info: ShardInfo = ShardInfo(
            shard_id=shard_id, shard_count=shard_count
        )

        self._logger: logging.Logger = logging.getLogger(
            f"ram.gateway.{self._shard_info.shard_id}"
        )

        self._transport: GatewayTransport | None = None
        self._resume_gateway_url: str | None = None
        self._session_id: str | None = None
        self._seq: int | None = None
        self._is_closing: bool = False

        self._last_heartbeat_sent: float = float("-inf")
        self._last_heartbeat_ack_received: float = 0.0

    async def connect(self) -> tuple[asyncio.Task[None], asyncio.Task[None]] | None:
        if self._transport:
            raise GatewayShardStateConflict()
        self._transport = await GatewayTransport.open(
            self._resume_gateway_url or self._gateway_url
        )
        payload: GatewayFrame[dict[str, Any]] = await self._transport.receive()
        if payload.op == OpCode.INVALID_SESSION:
            if payload.d:
                return None
            else:
                return None
        elif payload.op == OpCode.RECONNECT:
            return None
        if payload.op != OpCode.HELLO:
            raise Exception()  # TODO(exceptions): protocol error maybe?
        heartbeat_interval: float = payload.d["heartbeat_interval"] / 1_000
        if self._resume_gateway_url and self._session_id:
            assert self._seq
            await self._transport.send(
                GatewayFrame(
                    op=OpCode.RESUME,
                    d=Resume(
                        token=self._token, session_id=self._session_id, seq=self._seq
                    ),
                )
            )
        else:
            await self._transport.send(
                GatewayFrame(
                    op=OpCode.IDENTIFY,
                    d=Identify(
                        token=self._token,
                        intents=self._intents,
                        shard=self._shard_info,
                    ),
                )
            )
        heartbeat_loop_task: asyncio.Task[None] = asyncio.create_task(
            self._heartbeat_loop(heartbeat_interval),
            name=f"shard {self._shard_info.shard_id}: heartbeat_loop",
        )
        event_loop_task: asyncio.Task[None] = asyncio.create_task(
            self._event_loop(), name=f"shard {self._shard_info.shard_id}: event_loop"
        )
        return (heartbeat_loop_task, event_loop_task)

    async def _send_heartbeat(self) -> None:
        assert self._transport
        await self._transport.send(GatewayFrame(op=OpCode.HEARTBEAT, d=self._seq))
        self._last_heartbeat_sent = time.time()

    async def _heartbeat_loop(self, heartbeat_interval: float) -> None:
        while not self._is_closing:
            if (
                self._last_heartbeat_sent - self._last_heartbeat_ack_received
                > heartbeat_interval
            ):
                return
            await self._send_heartbeat()
            await asyncio.sleep(heartbeat_interval)

    async def _event_loop(self) -> None:
        assert self._transport
        while not self._is_closing:
            payload: GatewayFrame[Any] = await self._transport.receive()
            if payload.op == OpCode.DISPATCH:
                try:
                    gateway_event: GatewayEvent[Any] = convert(payload)
                except msgspec.DecodeError as exc:
                    self._logger.error("Failed to decode event %s: %s", payload.t, exc, exc_info=exc)
                    continue
                self._seq = gateway_event.s
                if type(gateway_event) is Ready:
                    self._resume_gateway_url = gateway_event.d.resume_gateway_url
                    self._session_id = gateway_event.d.session_id
                    self._logger.info("ready [session:%s]", self._session_id)
                else:
                    self._logger.debug("dispatch: %r", gateway_event)
                    continue
            elif payload.op == OpCode.HEARTBEAT_ACK:
                self._last_heartbeat_ack_received = time.time()
            elif payload.op == OpCode.HEARTBEAT:
                await self._send_heartbeat()
