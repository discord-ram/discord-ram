from __future__ import annotations

import abc
import asyncio
import inspect
import logging
import typing
import weakref
from collections import defaultdict
from collections.abc import Callable, Coroutine, Mapping, Sequence
from types import MethodType

from ramx.events.base import BaseEvent
from ramx.gateway.event_factory import EventFactory

__all__: Sequence[str] = ("BaseEventManager",)

Payload: typing.TypeAlias = Mapping[str, typing.Any]

T = typing.TypeVar("T")
T_Default = typing.TypeVar("T_Default")

T_Event = typing.TypeVar("T_Event", bound=BaseEvent)
T_Callback = typing.TypeVar("T_Callback", bound=Callable[..., Coroutine[typing.Any, typing.Any, typing.Any]])


class WeakReference(typing.Generic[T], abc.ABC):
    __slots__: Sequence[str] = ("_hash",)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if isinstance(other, WeakReference):
            return self._hash == other._hash  # type: ignore
        if callable(other):
            return self._hash == hash(other)
        return NotImplemented

    @abc.abstractmethod
    def unwrap(self) -> T: ...

    @abc.abstractmethod
    def unwrap_or(self, default: T_Default = None) -> T | T_Default: ...


class WeakFunc(typing.Generic[T], WeakReference[T]):
    __slots__ = ("_ref",)

    def __init__(self, func: T) -> None:
        if isinstance(func, MethodType):
            self._ref = weakref.WeakMethod(func)
        else:
            self._ref = weakref.ref(func)
        self._hash = hash(func)

    def unwrap(self) -> T:
        if obj := self._ref():
            return obj
        raise ReferenceError

    def unwrap_or(self, default: T_Default = None) -> T | T_Default:
        if obj := self._ref():
            return obj
        return default


class BaseEventManager(typing.Generic[T_Event, T_Callback]):
    def __init__(self, event_factory: EventFactory) -> None:
        self._logger: logging.Logger = logging.getLogger("ramx.event_manager")
        self._event_factory = event_factory

        self._listeners: defaultdict[type[T_Event], set[T_Callback | WeakReference[T_Callback]]] = defaultdict(set)
        self._event_map: dict[str, type[T_Event]] = {}

        self._dispatched_tasks: set[asyncio.Task[typing.Any]] = set()

    def subscribe(self, event_type: type[T_Event], callback: T_Callback, *, weak_ref: bool = True) -> None:
        func = WeakFunc(callback) if weak_ref else callback

        if hasattr(event_type, "__event_name__") and event_type.__event_name__ not in self._event_map:
            self._event_map[event_type.__event_name__] = event_type

        self._listeners[event_type].add(func)

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(
                "subscribed callback '%s%s' to event-type %s.%s",
                getattr(callback, "__name__", repr(callback)),
                inspect.signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )

    def unsubscribe(self, event_type: type[T_Event], callback: T_Callback) -> None:
        self._listeners[event_type].remove(callback)
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(
                "unsubscribed callback '%s%s' to event-type %s.%s",
                getattr(callback, "__name__", repr(callback)),
                inspect.signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )

    @typing.overload
    def dispatch(self, payload: Payload, *, event_name: str, return_tasks: typing.Literal[False]) -> None: ...

    @typing.overload
    def dispatch(
        self, payload: Payload, *, event_name: str, return_tasks: typing.Literal[True]
    ) -> Sequence[asyncio.Task[typing.Any]]: ...

    @typing.overload
    def dispatch(self, payload: Payload, *, event_type: type[T_Event], return_tasks: typing.Literal[False]) -> None: ...

    @typing.overload
    def dispatch(
        self, payload: Payload, *, event_type: type[T_Event], return_tasks: typing.Literal[True]
    ) -> Sequence[asyncio.Task[typing.Any]]: ...

    def dispatch(
        self,
        payload: Payload,
        *,
        event_type: type[T_Event] | None = None,
        event_name: str | None = None,
        return_tasks: bool = False,
    ) -> Sequence[asyncio.Task[typing.Any]] | None:
        dead_listeners: set[WeakReference[T_Callback]] = set()
        tasks: list[asyncio.Task[typing.Any]] | None = [] if return_tasks else None

        _event_type: type[T_Event] | None = event_type or (self._event_map.get(event_name) if event_name else None)
        if not _event_type:
            if not event_type and event_name is None:
                self._logger.warning("received dispatch without 'event_type' and 'event_name'")
            return

        event: T_Event = self._event_factory.convert_event(payload, _event_type)

        for listener in self._listeners[_event_type]:
            callback: T_Callback | None = None
            if isinstance(listener, WeakReference):
                func = typing.cast(T_Callback | None, listener.unwrap_or())
                if func is None:
                    dead_listeners.add(listener)  # type: ignore
                    continue
                callback = func
            else:
                callback = listener

            task: asyncio.Task[typing.Any] = asyncio.create_task(self._invoke_callback(event=event, callback=callback))
            if return_tasks:
                tasks.append(task)  # type: ignore
        self._listeners[_event_type] -= dead_listeners

        if return_tasks:
            return tasks

        return None

    @abc.abstractmethod
    async def _invoke_callback(self, *, event: T_Event, callback: T_Callback) -> None:
        await callback(event)
