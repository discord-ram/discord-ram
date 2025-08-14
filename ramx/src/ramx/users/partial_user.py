from __future__ import annotations

from collections.abc import Sequence

import msgspec

from ramx.locales import Locale
from ramx.unique import Unique
from ramx.users.premium_type import PremiumType
from ramx.users.user_flag import UserFlag

__all__: Sequence[str] = ("PartialUser",)


class PartialUser(Unique):
    username: str
    discriminator: str
    global_name: str | None = None
    is_bot: bool = msgspec.field(default=False, name="bot")
    is_system: bool = msgspec.field(default=False, name="system")
    accent_color: int | None = None
    locale: Locale | None = None
    flags: UserFlag = UserFlag.NONE
    premium_type: PremiumType = PremiumType.NONE

    @property
    def is_human(self) -> bool:
        return not (self.is_bot or self.is_system)
