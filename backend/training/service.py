"""封装 YOLO 训练调用，将训练回调转换为项目事件。"""

from pathlib import Path

from common.contracts import DatasetInfo, TrainingOptions, TrainingResult
from common.events import EventBus

from backend.runtime.paths import ProjectPaths


class TrainingService:
    def __init__(self, paths: ProjectPaths, events: EventBus):
        self.paths = paths
        self.events = events

    def train(self, options: TrainingOptions, dataset: DatasetInfo) -> TrainingResult:
        from ultralytics import YOLO

        model_path = self.paths.models / options.model
        self.events.publish("model_loading", weights=str(model_path))
        model = YOLO(str(model_path))

        def on_epoch_end(trainer):
            self.events.publish("training_progress", epoch=trainer.epoch + 1, epochs=trainer.epochs)

        model.add_callback("on_train_epoch_end", on_epoch_end)
        self.events.publish("training_started", epochs=options.epochs)
        model.train(
            data=str(dataset.config),
            epochs=options.epochs,
            imgsz=options.imgsz,
            batch=options.batch,
            device=options.device,
            workers=options.workers,
            seed=options.seed,
            project=str(self.paths.runs),
            name=options.name,
            plots=True,
            verbose=False,
            exist_ok=False,
        )
        directory = Path(model.trainer.save_dir)
        best_weights = directory / "weights" / "best.pt"
        if not best_weights.is_file():
            raise RuntimeError(f"训练结束后未找到最佳权重：{best_weights}")
        self.events.publish("training_completed", directory=str(directory), weights=str(best_weights))
        return TrainingResult(directory, best_weights)
