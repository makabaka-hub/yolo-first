"""订阅后端事件并显示进度、报告和结果，不进行模型计算。"""

import json
import logging
import re
import sys
from typing import TextIO

from common.events import Event


class ConsoleView:
    def __init__(self, verbose: bool = False, output: TextIO | None = None, error_output: TextIO | None = None):
        self.verbose = verbose
        # 固定界面输出流，避免后端转发第三方 stdout 时形成循环。
        self.output = output if output is not None else sys.stdout
        self.error_output = error_output if error_output is not None else sys.stderr

    def show(self, message: str, error: bool = False) -> None:
        print(message, file=self.error_output if error else self.output, flush=True)

    def on_event(self, event: Event) -> None:
        data = event.data
        match event.name:
            case "environment_checked":
                self.show(json.dumps(data["report"], ensure_ascii=False, indent=2))
                self.show(f"环境报告：{data['path']}")
            case "device_ready":
                self.show(f"计算设备：{data['device']}")
            case "data_downloading":
                self.show(f"正在下载数据集：{data['url']}")
            case "data_ready":
                self.show(f"数据已准备：{data['directory']}")
            case "model_loading":
                self.show(f"正在加载预训练模型（缺少时自动下载）：{data['weights']}")
            case "training_started":
                self.show(f"开始训练，共 {data['epochs']} 轮。")
            case "training_progress":
                self.show(f"训练进度：{data['epoch']}/{data['epochs']}")
            case "training_completed":
                self.show(f"训练完成，结果目录：{data['directory']}")
                self.show(f"训练后的模型：{data['weights']}")
            case "prediction_started":
                self.show(f"使用已有权重识别图片：{data['source']}")
            case "prediction_completed":
                self.show(f"已识别 {data['image_count']} 张图片，结果目录：{data['directory']}")
            case "library_log":
                if self.verbose or data["level"] >= logging.WARNING:
                    self.show(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", data["message"]))
            case "error":
                self.show(f"运行失败：{data['message']}", error=True)
                if self.verbose and data["detail"]:
                    self.show(data["detail"], error=True)
