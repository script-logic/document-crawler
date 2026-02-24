import logging
from enum import Enum, StrEnum


class LoggersToHijack(Enum):  # TODO
    SQLALCHEMY_ENGINE = ("sqlalchemy.engine", logging.WARNING)
    SQLALCHEMY_POOL = ("sqlalchemy.pool", logging.WARNING)
    URLLIB = ("urllib3", logging.WARNING)
    MATPLOTLIB = ("matplotlib", logging.WARNING)
    PIL = ("PIL", logging.WARNING)

    @property
    def logger_name(self) -> str:
        return self.value[0]

    @property
    def logger_level(self) -> int:
        return self.value[1]

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.logger_name)

    def set_level(self) -> None:
        self.logger.setLevel(self.logger_level)

    def hijack(self) -> None:
        logger = self.logger
        logger.handlers = []
        logger.propagate = True


class ProcessorNames(StrEnum):
    MERGE_CONTEXTVARS = "merge_contextvars"
    ADD_LOGGER_NAME = "add_logger_name"
    ADD_LOG_LEVEL = "add_log_level"
    POSITIONAL_ARGS = "positional_args_formatter"
    TIMESTAMP = "timestamp_stamper"
    STACK_INFO = "stack_info_renderer"
    EXC_INFO = "exc_info_formatter"

    CONTEXT_ADDER = "context_adder"
    MESSAGE_CLEANER = "message_cleaner"

    FORMATTER_WRAPPER = "formatter_wrapper"


class HandlerNames(StrEnum):
    FILE = "file"
    CONSOLE = "console"


class RendererNames(StrEnum):
    JSON = "json"
    CONSOLE = "console"
