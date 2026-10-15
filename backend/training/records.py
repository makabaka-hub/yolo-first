"""读取训练 CSV 的完整行，过滤正在写入的半行和无效指标。"""

import csv
import io
import math
from pathlib import Path

from common.training_view import TrainingPoint


def read_training_points(source: Path) -> tuple[TrainingPoint, ...]:
    try:
        text = source.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return ()
    # 训练进程可能正在追加一行，只读取已写完的记录。
    if not text.endswith("\n"):
        text = text.rpartition("\n")[0] + "\n"
    points = []
    for original in csv.DictReader(io.StringIO(text)):
        row = {key.strip(): value for key, value in original.items() if key is not None}
        try:
            epoch = int(row["epoch"])
            values = [float(row[key]) for key in (
                "train/box_loss", "train/cls_loss", "metrics/precision(B)",
                "metrics/recall(B)", "metrics/mAP50(B)", "time",
            )]
            if epoch < 1 or not all(math.isfinite(value) for value in values):
                continue
            if points and epoch <= points[-1].epoch:
                continue
            points.append(TrainingPoint(epoch, *values))
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(points)


def expected_epochs(directory: Path, fallback: int) -> int:
    import yaml

    source = directory / "args.yaml"
    if not source.is_file():
        return fallback
    try:
        arguments = yaml.safe_load(source.read_text(encoding="utf-8"))
        value = arguments.get("epochs") if isinstance(arguments, dict) else None
        return max(value, fallback) if type(value) is int and value > 0 else fallback
    except (OSError, yaml.YAMLError):
        return fallback
