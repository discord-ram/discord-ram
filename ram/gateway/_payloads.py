import platform
import typing

import msgspec

from ram.intents import Intents

LIBRARY_NAME: typing.Final[str] = "discord-ram"


class ConnectionProperties(msgspec.Struct):
    os: str = platform.platform()
    browser: str = LIBRARY_NAME
    device: str = LIBRARY_NAME


class ShardInfo(msgspec.Struct, array_like=True):
    shard_id: int
    shard_count: int


class Identify(msgspec.Struct, omit_defaults=True):
    token: str
    intents: Intents
    properties: ConnectionProperties = msgspec.field(
        default_factory=ConnectionProperties
    )
    compress: bool = False
    large_threshold: int | None = None
    shard: ShardInfo | None = None


class Resume(msgspec.Struct):
    token: str
    session_id: str
    seq: int
