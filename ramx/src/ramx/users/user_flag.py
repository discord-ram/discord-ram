from __future__ import annotations

import enum
import typing
from collections.abc import Sequence

__all__: Sequence[str] = ("UserFlag",)


@typing.final
class UserFlag(enum.Flag):
    NONE = 0
    DISCORD_EMPLOYEE = 1 << 0
    PARTNERED_SERVER_OWNER = 1 << 1
    HYPESQUAD_EVENTS = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    HYPESQUAD_BRAVERY = 1 << 6
    HYPESQUAD_BRILLIANCE = 1 << 7
    HYPESQUAD_BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    TEAM_USER = 1 << 10
    BUG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT = 1 << 16
    EARLY_VERIFIED_DEVELOPER = 1 << 17
    DISCORD_CERTIFIED_MODERATOR = 1 << 18
    BOT_HTTP_INTERACTIONS = 1 << 19
    SPAMMER = 1 << 20
    ACTIVE_DEVELOPER = 1 << 22
    PROVISIONAL_ACCOUNT = 1 << 23
    QUARANTINED = 1 << 44
    COLLABORATOR = 1 << 50
    RESTRICTED_COLLABORATOR = 1 << 51
