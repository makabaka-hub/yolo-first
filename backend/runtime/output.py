"""将第三方直接写入终端的内容转为事件，界面决定如何显示。"""

import io
import logging
from contextlib import contextmanager, redirect_stderr, redirect_stdout

from common.events import EventBus


class EventStream(io.TextIOBase):
    def __init__(self, events: EventBus):
        super().__init__()
        self.events = events
        self._pending = ""

    @property
    def encoding(self):
        return "utf-8"

    def write(self, text: str) -> int:
        self._pending += text.replace("\r", "\n")
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            if line.strip():
                self.events.publish("library_log", message=line, level=logging.INFO)
        return len(text)

    def flush(self) -> None:
        if self._pending.strip():
            line, self._pending = self._pending, ""
            self.events.publish("library_log", message=line, level=logging.INFO)


@contextmanager
def forward_library_output(events: EventBus):
    """适配单进程命令行任务；订阅者应写入其自己的界面输出流。"""
    output = EventStream(events)
    with redirect_stdout(output), redirect_stderr(output):
        try:
            yield
        finally:
            output.flush()
