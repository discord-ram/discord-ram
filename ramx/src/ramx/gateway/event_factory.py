from __future__ import annotations

import typing
from collections.abc import Mapping, Sequence

from ramx.gateway.entity_factory import EntityFactory

__all__: Sequence[str] = ("EventFactory",)

T_Event = typing.TypeVar("T_Event")


class EventFactory:
    def __init__(self, entity_factory: EntityFactory) -> None:
        self.entity_factory: EntityFactory = entity_factory

    def convert_event(self, obj: Mapping[str, typing.Any], event: type[T_Event]) -> T_Event:
        return self.entity_factory.convert(obj, type=event)
