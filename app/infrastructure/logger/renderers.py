from typing import Any, Callable, Literal, overload

import orjson
import structlog
from structlog.types import EventDict, Processor, WrappedLogger
from structlog.typing import ProcessorReturnValue

from app.utils import Singleton

from .decorators import register_in
from .enums import RendererNames
from .interfaces import BaseLoggerFactory, ILogProcessor


class RendererFactory(BaseLoggerFactory[ILogProcessor], metaclass=Singleton):
    @overload
    def create(
        self,
        name: Literal[RendererNames.CONSOLE],
        *,
        colors: bool = ...,
        pad_event_to: int = ...
    ) -> ILogProcessor: ...

    @overload
    def create(
        self,
        name: Literal[RendererNames.JSON],
    ) -> ILogProcessor: ...

    def create(self, name: str, **kwargs: Any) -> ILogProcessor:
        processor_cls = self.get_blueprint(name)

        return processor_cls(**kwargs)


class RendererBuilder:
    def __init__(self, factory: RendererFactory) -> None:
        self.factory = factory

    def build_renderer(self, debug: bool) -> ILogProcessor:
        if not debug:
            return self.factory.create(RendererNames.JSON)
        else:
            return self.factory.create(
                RendererNames.CONSOLE, colors=True, pad_event_to=20
            )


@register_in(RendererFactory, RendererNames.JSON)
class JsonRenderStrategy:
    def __init__(self) -> None:
        self.renderer: Processor = structlog.processors.JSONRenderer(
            serializer=self._serializer
        )

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> ProcessorReturnValue:
        return self.renderer(logger, method_name, event_dict)

    def _serializer(
        self,
        data: Any,
        default: Callable[[Any], Any] | None = None,
        option: int | None = None,
    ) -> str:
        return orjson.dumps(data, default=default, option=option).decode(
            "utf-8"
        )


@register_in(RendererFactory, RendererNames.CONSOLE)
class ConsoleRenderStrategy:
    def __init__(self, colors: bool = True, pad_event_to: int = 20) -> None:
        self.renderer: Processor = structlog.dev.ConsoleRenderer(
            colors=colors,
            pad_event_to=pad_event_to,
        )

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> ProcessorReturnValue:
        return self.renderer(logger, method_name, event_dict)
