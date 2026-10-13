"""集中计算项目内的文件路径，导入时不创建目录。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    def resolve(self, value: str | Path) -> Path:
        return (self.root / value).resolve()

    @property
    def config(self) -> Path:
        return self.root / ".ultralytics"

    @property
    def datasets(self) -> Path:
        return self.root / "datasets"

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    @property
    def logs(self) -> Path:
        return self.root / "logs"
