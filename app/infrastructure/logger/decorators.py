from typing import Any, Callable, Type, TypeVar

from .interfaces import BaseLoggerFactory


T = TypeVar("T", bound=Type[Any])


def register_in(
    registry: Type[BaseLoggerFactory[Any]], name: str
) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        registry().register(name, cls)
        return cls

    return decorator
