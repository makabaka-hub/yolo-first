"""显式初始化计算环境，检查 GPU，并将第三方日志转为事件。"""

import io
import json
import logging
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import version

from common.events import EventBus

from .paths import ProjectPaths


class EventLogHandler(logging.Handler):
    def __init__(self, events: EventBus):
        super().__init__()
        self.events = events

    def emit(self, record: logging.LogRecord) -> None:
        self.events.publish("library_log", message=self.format(record), level=record.levelno)


class RuntimeService:
    def __init__(self, paths: ProjectPaths, events: EventBus):
        self.paths = paths
        self.events = events

    def initialize(self) -> None:
        """在导入 Ultralytics 前设置路径，副作用只在显式调用时发生。"""
        for directory in (self.paths.config, self.paths.datasets, self.paths.models, self.paths.runs):
            directory.mkdir(parents=True, exist_ok=True)
        os.environ["YOLO_CONFIG_DIR"] = str(self.paths.config)
        os.environ["MPLCONFIGDIR"] = str(self.paths.root / ".cache" / "matplotlib")
        os.environ["TORCH_HOME"] = str(self.paths.root / ".cache" / "torch")
        os.environ["YOLO_VERBOSE"] = "False"

        # 第三方首次导入可能输出配置提示，将其一并交给订阅者展示。
        startup_messages = io.StringIO()
        with redirect_stdout(startup_messages), redirect_stderr(startup_messages):
            from ultralytics import settings, utils
            from ultralytics.utils import LOGGER

            settings.update({
                "datasets_dir": str(self.paths.datasets),
                "weights_dir": str(self.paths.models),
                "runs_dir": str(self.paths.runs),
                "sync": False,
            })
            # 8.4 版本还保留导入时的目录快照，需在加载模型前同步。
            utils.DATASETS_DIR = self.paths.datasets
            utils.WEIGHTS_DIR = self.paths.models
            utils.RUNS_DIR = self.paths.runs
        for handler in tuple(LOGGER.handlers):
            LOGGER.removeHandler(handler)
            handler.close()
        LOGGER.addHandler(EventLogHandler(self.events))
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False
        if message := startup_messages.getvalue().strip():
            self.events.publish("library_log", message=message, level=logging.INFO)

    def require_device(self, device: str) -> None:
        import torch

        if device == "cpu":
            self.events.publish("device_ready", device="CPU")
            return
        if not torch.cuda.is_available():
            raise RuntimeError("未检测到可用 NVIDIA GPU。请运行 check_env.py 检查，或使用 --device cpu。")
        index = int(device)
        if index >= torch.cuda.device_count():
            raise ValueError(f"GPU 编号 {index} 不存在。")
        self.events.publish("device_ready", device=torch.cuda.get_device_name(index))

    def check(self) -> dict:
        import torch

        report = {
            "python_path": sys.executable,
            "python_version": sys.version.split()[0],
            "torch_version": torch.__version__,
            "torchvision_version": version("torchvision"),
            "ultralytics_version": version("ultralytics"),
            "cuda_version": torch.version.cuda,
            "gpu_available": torch.cuda.is_available(),
        }
        if report["gpu_available"]:
            report["gpu_name"] = torch.cuda.get_device_name(0)
            report["gpu_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1024**3, 2
            )
            values = torch.ones((32, 32), device="cuda")
            report["gpu_calculation_result"] = (values @ values).sum().item()
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        report_path = self.paths.logs / "environment.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.events.publish("environment_checked", report=report, path=str(report_path))
        return report
