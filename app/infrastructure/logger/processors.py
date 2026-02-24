from typing import Any, Literal, overload

import structlog
from structlog.types import EventDict, Processor

from app.utils import Singleton

from .decorators import register_in
from .enums import ProcessorNames
from .interfaces import (
    BaseLoggerFactory,
    BaseProcessorStrategy,
    ILoggingConfig,
    ILogProcessor,
)


class ProcessorFactory(BaseLoggerFactory[ILogProcessor], metaclass=Singleton):
    @overload
    def create(
        self,
        name: Literal[ProcessorNames.CONTEXT_ADDER],
        *,
        logging_config: ILoggingConfig
    ) -> ILogProcessor: ...

    @overload
    def create(
        self, name: Literal[ProcessorNames.TIMESTAMP], *, fmt: str | None = ...
    ) -> ILogProcessor: ...

    @overload
    def create(
        self,
        name: Literal[
            ProcessorNames.MERGE_CONTEXTVARS,
            ProcessorNames.ADD_LOGGER_NAME,
            ProcessorNames.ADD_LOG_LEVEL,
            ProcessorNames.POSITIONAL_ARGS,
            ProcessorNames.STACK_INFO,
            ProcessorNames.EXC_INFO,
            ProcessorNames.MESSAGE_CLEANER,
            ProcessorNames.FORMATTER_WRAPPER,
        ],
    ) -> ILogProcessor: ...

    def create(self, name: str, **kwargs: Any) -> ILogProcessor:
        processor_cls = self.get_blueprint(name)

        return processor_cls(**kwargs)


class ProcessorBuilder:
    def __init__(
        self,
        factory: ProcessorFactory,
        additional_processors: list[ILogProcessor] | None = None,
    ) -> None:
        self.factory = factory
        self.additional_processors = additional_processors or []

    def build_base_chain(self) -> list[ILogProcessor]:
        return [
            self.factory.create(ProcessorNames.MERGE_CONTEXTVARS),
            self.factory.create(ProcessorNames.ADD_LOGGER_NAME),
            self.factory.create(ProcessorNames.ADD_LOG_LEVEL),
            self.factory.create(ProcessorNames.POSITIONAL_ARGS),
            self.factory.create(ProcessorNames.TIMESTAMP),
            self.factory.create(ProcessorNames.STACK_INFO),
            self.factory.create(ProcessorNames.EXC_INFO),
        ]

    def build_shared_chain(self) -> list[ILogProcessor]:
        chain = self.build_base_chain()
        chain.append(self.factory.create(ProcessorNames.MESSAGE_CLEANER))
        chain.extend(self.additional_processors)
        return chain

    def build_formatter_wrapper(self) -> ILogProcessor:
        return self.factory.create(ProcessorNames.FORMATTER_WRAPPER)


class LogMessageCleaner:
    def __call__(
        self, logger: Any, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """
        Clean up log messages for better readability in console output.
        Removes extra whitespace.

        Args:
            logger: The logger instance
            method_name: The log method name
            event_dict: The event dictionary to process
        """
        if "event" in event_dict:
            event_dict["event"] = event_dict["event"].strip()
        return event_dict


class AppContextAdder:
    def __init__(self, app_name: str, debug: bool) -> None:
        self.app_name = app_name
        self.debug = debug

    def __call__(
        self, logger: Any, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """
        Add application-wide context to all log entries.

        Args:
            logger: The logger instance
            method_name: The log method name
            event_dict: The event dictionary to process
        """
        event_dict.setdefault("app", self.app_name)
        event_dict.setdefault("debug", self.debug)
        return event_dict


@register_in(ProcessorFactory, ProcessorNames.MERGE_CONTEXTVARS)
class MergeContextvarsStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = structlog.contextvars.merge_contextvars


@register_in(ProcessorFactory, ProcessorNames.ADD_LOGGER_NAME)
class AddLoggerNameStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = structlog.stdlib.add_logger_name


@register_in(ProcessorFactory, ProcessorNames.ADD_LOG_LEVEL)
class AddLogLevelStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = structlog.stdlib.add_log_level


@register_in(ProcessorFactory, ProcessorNames.POSITIONAL_ARGS)
class PositionalArgsFormatterStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = (
            structlog.stdlib.PositionalArgumentsFormatter()
        )


@register_in(ProcessorFactory, ProcessorNames.TIMESTAMP)
class TimestampStamperStrategy(BaseProcessorStrategy):
    def __init__(self, fmt: str | None = "%Y-%m-%d %H:%M:%S") -> None:
        self.processor: Processor = structlog.processors.TimeStamper(fmt=fmt)


@register_in(ProcessorFactory, ProcessorNames.STACK_INFO)
class StackInfoRendererStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = structlog.processors.StackInfoRenderer()


@register_in(ProcessorFactory, ProcessorNames.EXC_INFO)
class ExcInfoFormatterStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = structlog.processors.format_exc_info


@register_in(ProcessorFactory, ProcessorNames.CONTEXT_ADDER)
class AppContextAdderStrategy(BaseProcessorStrategy):
    def __init__(self, logging_config: ILoggingConfig) -> None:
        self.processor: Processor = AppContextAdder(
            app_name=logging_config.app_name,
            debug=logging_config.debug,
        )


@register_in(ProcessorFactory, ProcessorNames.MESSAGE_CLEANER)
class LogMessageCleanerStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = LogMessageCleaner()


@register_in(ProcessorFactory, ProcessorNames.FORMATTER_WRAPPER)
class FormatterWrapperStrategy(BaseProcessorStrategy):
    def __init__(self) -> None:
        self.processor: Processor = (
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        )
