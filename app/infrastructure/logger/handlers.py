import sys
from logging import Handler, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Literal, overload

from app.utils import Singleton

from .decorators import register_in
from .enums import HandlerNames
from .interfaces import BaseLoggerFactory, IHandler, ILoggingConfig


class HandlerFactory(BaseLoggerFactory[IHandler], metaclass=Singleton):
    @overload
    def create(
        self,
        name: Literal[HandlerNames.FILE],
        *,
        logging_config: ILoggingConfig,
    ) -> IHandler: ...

    @overload
    def create(
        self,
        name: Literal[HandlerNames.CONSOLE],
    ) -> IHandler: ...

    def create(self, name: str, **kwargs: Any) -> IHandler:
        processor_cls = self.get_blueprint(name)

        return processor_cls(**kwargs)


class HandlerBuilder:
    def __init__(self, factory: HandlerFactory) -> None:
        self.factory = factory

    def build_console_handler(self) -> Handler:
        strategy = self.factory.create(HandlerNames.CONSOLE)
        return strategy()

    def build_file_handler(self, logging_config: ILoggingConfig) -> Handler:
        log_path = Path(logging_config.logs_dir)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        strategy = self.factory.create(
            HandlerNames.FILE, logging_config=logging_config
        )
        return strategy()

    def build_handler_chain(
        self,
        logging_config: ILoggingConfig,
    ) -> list[Handler]:
        result: list[Handler] = []
        result.append(self.build_console_handler())
        if logging_config.enable_file_logging:
            result.append(self.build_file_handler(logging_config))
        return result


@register_in(HandlerFactory, HandlerNames.CONSOLE)
class ConsoleHandlerStrategy:
    def __call__(self) -> Handler:
        return StreamHandler(sys.stdout)


@register_in(HandlerFactory, HandlerNames.FILE)
class FileHandlerStrategy:
    def __init__(self, logging_config: ILoggingConfig) -> None:
        self.logging_config = logging_config

    def __call__(self) -> Handler:
        return RotatingFileHandler(
            filename=str(
                self.logging_config.logs_dir
                / self.logging_config.logs_file_name
            ),
            maxBytes=self.logging_config.max_file_size_mb * 1024 * 1024,
            backupCount=self.logging_config.backup_count,
            encoding="utf-8",
        )
