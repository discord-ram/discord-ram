from __future__ import annotations

import enum
import typing
from collections.abc import Sequence

import msgspec

__all__: Sequence[str] = ("OpCode", "ShardCloseCode", "ShardInfo")


@typing.final
class OpCode(int, enum.Enum):
    """https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway-gateway-opcodes"""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


@typing.final
class ShardCloseCode(int, enum.Enum):
    NORMAL_CLOSURE = 1_000
    GOING_AWAY = 1_001

    UNKNOWN_ERROR = 4_000
    UNKNOWN_OPCODE = 4_001
    DECODE_ERROR = 4_002
    NOT_AUTHENTICATED = 4_003
    AUTHENTICATION_FAILED = 4_004
    ALREADY_AUTHENTICATED = 4_005
    INVALID_SEQ = 4_007
    RATE_LIMITED = 4_008
    SESSION_TIMEOUT = 4_009
    INVALID_SHARD = 4_010
    SHARDING_REQUIRED = 4_011
    INVALID_VERSION = 4_012
    INVALID_INTENT = 4_013
    DISALLOWED_INTENT = 4_014


class ShardInfo(msgspec.Struct, array_like=True):
    shard_id: int
    shard_count: int
