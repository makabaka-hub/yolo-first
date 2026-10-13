"""重新加载指定权重，识别图片并推送结果保存位置。"""

from pathlib import Path

from common.contracts import PredictionResult
from common.events import EventBus

from backend.runtime.paths import ProjectPaths


class InferenceService:
    def __init__(self, paths: ProjectPaths, events: EventBus):
        self.paths = paths
        self.events = events

    def predict(self, weights: Path, source: Path, device: str, name: str) -> PredictionResult:
        if not weights.is_file():
            raise FileNotFoundError(f"权重文件不存在：{weights}。请先训练，或用 --weights 指定已有权重。")
        if not source.exists():
            raise FileNotFoundError(f"图片或图片文件夹不存在：{source}")
        from ultralytics import YOLO

        self.events.publish("prediction_started", weights=str(weights), source=str(source))
        model = YOLO(str(weights))
        results = model.predict(
            source=str(source),
            device=device,
            save=True,
            project=str(self.paths.runs),
            name=name,
            verbose=False,
            exist_ok=False,
        )
        if not results:
            raise RuntimeError("没有生成图片识别结果，请检查输入目录。")
        directory = Path(results[0].save_dir)
        self.events.publish("prediction_completed", directory=str(directory), image_count=len(results))
        return PredictionResult(directory, len(results))
