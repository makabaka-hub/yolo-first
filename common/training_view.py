"""定义训练展示的数据快照与界面调用接口，不依赖训练库。"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TrainingPoint:
    epoch: int
    box_loss: float
    cls_loss: float
    precision: float
    recall: float
    map50: float
    seconds: float


@dataclass(frozen=True)
class TrainingSnapshot:
    phase: str
    message: str
    epochs: int
    points: tuple[TrainingPoint, ...] = ()
    directory: str = ""
    device: str = ""
    log: str = ""


class TrainingViewPort(Protocol):
    def start(self, epochs: int) -> None: ...
    def stop(self) -> None: ...
    def history(self) -> None: ...
    def close(self) -> None: ...
