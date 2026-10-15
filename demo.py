"""桌面演示组装入口：连接窗口、跨线程事件收件箱与后台服务。"""

from pathlib import Path

from backend.demo.catalog import demo_models, demo_samples
from backend.demo.controller import DemoController
from backend.runtime.environment import RuntimeService
from backend.runtime.paths import ProjectPaths
from backend.training.monitor import TrainingMonitor
from common.demo import DemoOptions
from common.events import EventBus
from frontend.desktop.bridge import DesktopInbox, TrainingInbox
from frontend.desktop.window import DemoWindow
from frontend.desktop.instance import DesktopInstance, focus_existing_window
from frontend.desktop.launch import parse_launch_args


def build_demo():
    import tkinter as tk

    paths = ProjectPaths(Path(__file__).resolve().parent)
    models, samples = demo_models(paths), demo_samples(paths)
    events, inbox = EventBus(), DesktopInbox()
    events.subscribe(inbox.on_event)
    controller = DemoController(RuntimeService(paths, events), events, DemoOptions(models[0].weights), next(iter(samples.values())))
    training_inbox = TrainingInbox()
    events.subscribe(training_inbox.on_event)
    training = TrainingMonitor(paths, events, before_start=controller.stop)
    root = tk.Tk()
    window = DemoWindow(root, controller, inbox, models, samples, training, training_inbox)
    return root, window, controller


def main():
    launch = parse_launch_args()
    with DesktopInstance() as instance:
        if not instance.acquired:
            focus_existing_window()
            return
        root, window, controller = build_demo()
        controller.start()
        if launch.training:
            window.show_training()
        try:
            root.mainloop()
        finally:
            controller.close()
            window.training_port.close()


if __name__ == "__main__":
    from multiprocessing import freeze_support

    freeze_support()
    main()
