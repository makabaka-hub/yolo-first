"""桌面演示组装入口：连接窗口、跨线程事件收件箱与后台服务。"""

from pathlib import Path

from backend.demo.catalog import demo_models, demo_samples
from backend.demo.controller import DemoController
from backend.runtime.environment import RuntimeService
from backend.runtime.paths import ProjectPaths
from common.demo import DemoOptions
from common.events import EventBus
from frontend.desktop.bridge import DesktopInbox
from frontend.desktop.window import DemoWindow


def build_demo():
    import tkinter as tk

    paths = ProjectPaths(Path(__file__).resolve().parent)
    models, samples = demo_models(paths), demo_samples(paths)
    events, inbox = EventBus(), DesktopInbox()
    events.subscribe(inbox.on_event)
    controller = DemoController(RuntimeService(paths, events), events, DemoOptions(models[0].weights), next(iter(samples.values())))
    root = tk.Tk()
    window = DemoWindow(root, controller, inbox, models, samples)
    return root, window, controller


def main():
    root, window, controller = build_demo()
    controller.start()
    try:
        root.mainloop()
    finally:
        controller.close()


if __name__ == "__main__":
    main()
