"""项目组装入口：连接界面、事件总线和后端服务。"""

from pathlib import Path

from backend.application import Application
from backend.data.preparation import DatasetService
from backend.inference.service import InferenceService
from backend.runtime.environment import RuntimeService
from backend.runtime.paths import ProjectPaths
from backend.training.service import TrainingService
from common.events import EventBus
from frontend.cli import parse_args
from frontend.console import ConsoleView


def main(argv: list[str] | None = None) -> int:
    command = parse_args(argv)
    paths = ProjectPaths(Path(__file__).resolve().parent)
    events = EventBus()
    view = ConsoleView(command.verbose)
    events.subscribe(view.on_event)
    application = Application(
        paths, events,
        RuntimeService(paths, events),
        DatasetService(paths, events),
        TrainingService(paths, events),
        InferenceService(paths, events),
    )
    return application.run(command)


if __name__ == "__main__":
    raise SystemExit(main())
