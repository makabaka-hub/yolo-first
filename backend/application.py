"""协调后端服务完成检查、训练或预测，向订阅者推送失败信息。"""

import traceback

from common.contracts import Command
from common.events import EventBus

from .data.preparation import DatasetService
from .inference.service import InferenceService
from .runtime.configuration import load_training_options, validate_device, validate_name
from .runtime.environment import RuntimeService
from .runtime.output import forward_library_output
from .runtime.paths import ProjectPaths
from .training.service import TrainingService


class Application:
    def __init__(
        self,
        paths: ProjectPaths,
        events: EventBus,
        runtime: RuntimeService,
        datasets: DatasetService,
        training: TrainingService,
        inference: InferenceService,
    ):
        self.paths = paths
        self.events = events
        self.runtime = runtime
        self.datasets = datasets
        self.training = training
        self.inference = inference

    def run(self, command: Command) -> int:
        try:
            with forward_library_output(self.events):
                self._execute(command)
            return 0
        except KeyboardInterrupt:
            self.events.publish("error", message="操作已取消。", detail="")
            return 130
        except Exception as error:
            self.events.publish("error", message=str(error), detail=traceback.format_exc())
            return 1

    def _execute(self, command: Command) -> None:
        if command.mode == "check":
            self.runtime.check()
        elif command.mode == "train":
            options = load_training_options(self.paths, command)
            self.runtime.initialize()
            self.runtime.require_device(options.device)
            dataset = self.datasets.prepare(options.data_config)
            result = self.training.train(options, dataset)
            if not command.skip_preview:
                self.inference.predict(
                    result.best_weights, dataset.validation_images, options.device, options.preview_name
                )
        elif command.mode == "predict":
            device = validate_device(command.device if command.device is not None else "0")
            name = validate_name(command.name if command.name is not None else "prediction")
            self.runtime.initialize()
            self.runtime.require_device(device)
            self.inference.predict(
                self.paths.resolve(command.weights), self.paths.resolve(command.source), device, name
            )
        else:
            raise ValueError(f"未知命令：{command.mode}")
