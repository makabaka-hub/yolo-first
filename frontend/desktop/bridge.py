"""跨线程接收事件；检测画面只保留最新一帧，避免界面延迟堆积。"""

from queue import Empty, SimpleQueue
from threading import Lock

from common.events import Event


class DesktopInbox:
    def __init__(self):
        self.controls = SimpleQueue()
        self.lock = Lock()
        self.latest_frame = None

    def on_event(self, event: Event) -> None:
        if event.name == "demo_frame":
            with self.lock:
                self.latest_frame = event
        elif event.name.startswith("demo_"):
            self.controls.put(event)

    def drain(self) -> list[Event]:
        events = []
        while True:
            try:
                events.append(self.controls.get_nowait())
            except Empty:
                break
        with self.lock:
            frame, self.latest_frame = self.latest_frame, None
        if frame is not None:
            events.append(frame)
        return events
