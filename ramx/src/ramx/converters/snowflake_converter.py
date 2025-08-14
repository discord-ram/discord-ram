from __future__ import annotations

import typing
from collections.abc import Sequence

from ramx.converters.base import converter
from ramx.snowflakes import Snowflake

__all__: Sequence[str] = ("snowflake_converter",)


@converter(Snowflake)
def snowflake_converter(value: typing.Any) -> Snowflake:  # noqa: ANN401
    return Snowflake(value)
