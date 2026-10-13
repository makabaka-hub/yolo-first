"""定义命令、训练配置和服务结果，供前后端交换数据。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Command:
    mode: str
    config: str = "config/training.yaml"
    epochs: int | None = None
    name: str | None = None
    device: str | None = None
    skip_preview: bool = False
    weights: str = "runs/first_train/weights/best.pt"
    source: str = "datasets/coco8/images/val"
    verbose: bool = False


@dataclass(frozen=True)
class TrainingOptions:
    data_config: Path
    model: str
    epochs: int
    imgsz: int
    batch: int
    device: str
    workers: int
    seed: int
    name: str
    preview_name: str


@dataclass(frozen=True)
class DatasetInfo:
    config: Path
    validation_images: Path


@dataclass(frozen=True)
class TrainingResult:
    directory: Path
    best_weights: Path


@dataclass(frozen=True)
class PredictionResult:
    directory: Path
    image_count: int
