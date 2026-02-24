import logging
from logging import Handler
from typing import Any

import structlog

from app.utils import Singleton

from .enums import LoggersToHijack
from .handlers import HandlerBuilder, HandlerFactory
from .interfaces import ILoggingConfig
from .processors import ProcessorBuilder, ProcessorFactory
from .renderers import RendererBuilder, RendererFactory


class LoggerManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.config: ILoggingConfig | None = None
        self.handler_builder: HandlerBuilder | None = None
        self.processor_builder: ProcessorBuilder | None = None
        self.renderer_builder: RendererBuilder | None = None
        self.is_configured = False

    def _configure_structlog(self) -> None:
        if (
            not self.processor_builder
            or not self.handler_builder
            or not self.renderer_builder
            or not self.config
        ):
            raise RuntimeError(
                "LoggerManager is not configured. "
                "Call 'setup_logging()' first."
            )

        shared_processors = self.processor_builder.build_shared_chain()
        formatter_wrapper = self.processor_builder.build_formatter_wrapper()

        structlog.configure(
            processors=shared_processors + [formatter_wrapper],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processor=self.renderer_builder.build_renderer(self.config.debug),
            foreign_pre_chain=shared_processors,
        )

        handlers: list[Handler] = self.handler_builder.build_handler_chain(
            self.config
        )
        for handler in handlers:
            handler.setFormatter(formatter)
            handler.setLevel(self.config.log_level)

        root_logger = logging.getLogger()
        root_logger.handlers = handlers
        root_logger.setLevel(self.config.log_level)

    def _configure_third_party_loggers(self):
        for logger_enum in LoggersToHijack:
            logger_enum.hijack()
            logger_enum.set_level()

    def _ensure_configured(self):
        if not self.is_configured:
            raise RuntimeError(
                "LoggerManager is not configured. "
                "Call 'setup_logging()' first."
            )

    def configure_logger_manager(
        self,
        config: ILoggingConfig,
        handler_builder: HandlerBuilder,
        processor_builder: ProcessorBuilder,
        renderer_builder: RendererBuilder,
    ) -> None:
        if self.is_configured:
            return

        self.config = config
        self.handler_builder = handler_builder
        self.processor_builder = processor_builder
        self.renderer_builder = renderer_builder

        self._configure_structlog()
        self._configure_third_party_loggers()

        self.is_configured = True

    def get_logger(self, name: str):
        self._ensure_configured()
        return structlog.get_logger(name)


def get_logger_manager() -> LoggerManager:
    return LoggerManager()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    logger_manager = get_logger_manager()
    return logger_manager.get_logger(name)


def bind_context(**kwargs: Any):
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context(*keys: Any):
    if keys:
        structlog.contextvars.unbind_contextvars(*keys)
    else:
        structlog.contextvars.clear_contextvars()


def setup_logging(config: ILoggingConfig):
    manager = LoggerManager()

    if manager.is_configured:
        return

    processor_factory = ProcessorFactory()
    renderer_factory = RendererFactory()
    handler_factory = HandlerFactory()

    renderer_builder = RendererBuilder(factory=renderer_factory)
    processor_builder = ProcessorBuilder(factory=processor_factory)
    handler_builder = HandlerBuilder(factory=handler_factory)

    manager.configure_logger_manager(
        config=config,
        handler_builder=handler_builder,
        processor_builder=processor_builder,
        renderer_builder=renderer_builder,
    )
