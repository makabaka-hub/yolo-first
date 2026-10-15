"""定义桌面演示使用的配置、检测帧和界面调用接口。"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DemoModel:
    title: str
    weights: str
    note: str


@dataclass(frozen=True)
class DemoOptions:
    weights: str
    confidence: float = 0.35

    def __post_init__(self):
        if not 0 < self.confidence <= 1:
            raise ValueError("置信度阈值必须大于 0 且小于等于 1。")


@dataclass(frozen=True)
class Detection:
    name: str
    confidence: float
    box: tuple[float, float, float, float]


@dataclass(frozen=True)
class DemoFrame:
    annotated_jpeg: bytes
    original_jpeg: bytes
    detections: tuple[Detection, ...]
    width: int
    height: int
    inference_ms: float
    processing_fps: float
    source: str
    mode: str
    model: str
    confidence: float


class DemoPort(Protocol):
    def image(self, source: str, options: DemoOptions) -> None: ...
    def camera(self, index: int, options: DemoOptions) -> None: ...
    def configure(self, options: DemoOptions) -> None: ...
    def stop(self) -> None: ...
    def save(self, destination: str, frame: DemoFrame) -> None: ...
    def close(self) -> None: ...
