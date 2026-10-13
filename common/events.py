"""提供进程内事件发布与订阅，计算服务不直接调用界面。"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class Event:
    name: str
    data: Mapping[str, Any]


class EventBus:
    def __init__(self):
        self._subscribers: list[Callable[[Event], None]] = []

    def subscribe(self, callback: Callable[[Event], None]) -> Callable[[], None]:
        """注册订阅者，返回取消订阅函数。"""
        self._subscribers.append(callback)

        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    def publish(self, name: str, **data: Any) -> None:
        event = Event(name, MappingProxyType(data))
        for callback in tuple(self._subscribers):
            callback(event)
