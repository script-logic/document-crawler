from collections.abc import Callable
from typing import Any, TypeVar

from .interfaces import BaseLoggerFactory

T = TypeVar("T", bound=type[Any])


def register_in(
    registry: type[BaseLoggerFactory[Any]], name: str
) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        registry().register(name, cls)
        return cls

    return decorator
