from abc import ABCMeta
from threading import Lock
from typing import Any, Optional, ClassVar, Dict, Type, cast


class Singleton(ABCMeta):
    __instances: ClassVar[Dict[Type[Any], object]] = {}
    __lock: ClassVar[Lock] = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        cls_type = cast(Type[Any], cls)

        if cls_type not in cls.__instances:
            with cls.__lock:
                if cls_type not in cls.__instances:
                    cls.__instances[cls_type] = super().__call__(
                        *args, **kwargs
                    )
        return cls.__instances[cls_type]

    @classmethod
    def clear_singleton(cls, target_class: Optional[Type[Any]] = None) -> None:
        if target_class is None:
            cls.__instances.clear()
        else:
            cls.__instances.pop(target_class, None)
