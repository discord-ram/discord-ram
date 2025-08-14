from __future__ import annotations

import abc
import inspect
import typing
from collections.abc import Sequence

if typing.TYPE_CHECKING:
    from ram.di.container import DependencyContainer

__all__: Sequence[str] = ("DependencyFactory", "Inject", "LazyInjected")

T = typing.TypeVar("T")
P = typing.ParamSpec("P")
T_co = typing.TypeVar("T_co", covariant=True)


@typing.runtime_checkable
class DependencyFactory(typing.Generic[T_co], typing.Protocol):
    @abc.abstractmethod
    @typing.overload
    def __call__(self) -> T_co: ...

    @abc.abstractmethod
    @typing.overload
    async def __call__(self) -> T_co: ...


class Inject(typing.Generic[T]):
    def __init__(self, type: T) -> None:
        self.injection_type: T = type


class LazyInjected(typing.Generic[P, T]):
    def __init__(
        self,
        func: typing.Callable[P, typing.Awaitable[T]],
        container: DependencyContainer,
        dependencies: dict[str, type[typing.Any]],
    ) -> None:
        self._func = func
        self._container = container
        self._dependencies = dependencies

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> typing.Awaitable[T]:
        return self._async_wrapper(*args, **kwargs)

    async def _async_wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
        for key, dependency_type in self._dependencies.items():
            dependency = self._container.resolve(dependency_type)
            if inspect.isawaitable(dependency):
                dependency = await dependency
            kwargs[key] = dependency
        return await self._func(*args, **kwargs)
