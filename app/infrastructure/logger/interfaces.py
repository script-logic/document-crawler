from abc import ABC, abstractmethod
from logging import Handler
from pathlib import Path
from typing import Any, Generic, Protocol, Type, TypeVar

from structlog.types import EventDict, Processor, WrappedLogger
from structlog.typing import ProcessorReturnValue

T = TypeVar("T")


class ILoggingConfig(Protocol):
    debug: bool
    app_name: str
    log_level: str
    enable_file_logging: bool
    logs_dir: Path
    logs_file_name: str
    max_file_size_mb: int
    backup_count: int


class IHandler(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Handler: ...


class ILogProcessor(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> ProcessorReturnValue: ...


class BaseProcessorStrategy(ABC):
    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        self.processor: Processor

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> ProcessorReturnValue:
        return self.processor(logger, method_name, event_dict)


class BaseLoggerFactory(ABC, Generic[T]):
    def __init__(self) -> None:
        self._blueprints: dict[str, Type[T]] = {}

    def register(self, name: str, item_blueprint: Type[T]):
        if name in self._blueprints:
            raise ValueError(f"Blueprint '{name}' is already registered")
        self._blueprints[name] = item_blueprint

    def get_blueprint(self, name: str) -> Type[T]:
        if name not in self._blueprints:
            raise ValueError(f"Blueprint '{name}' not registered")
        return self._blueprints[name]

    def get_available_products(self) -> list[str]:
        return list(self._blueprints)
