"""发现本机可用的演示模型，并给出内置示例图片位置。"""

from common.demo import DemoModel

from backend.runtime.paths import ProjectPaths


def demo_models(paths: ProjectPaths) -> tuple[DemoModel, ...]:
    models = [DemoModel(
        "通用识别 · YOLO26n", str(paths.models / "yolo26n.pt"),
        "官方预训练模型，识别人、车辆及日常物品等 80 类目标。",
    )]
    candidates = sorted(paths.runs.glob("*/weights/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if candidates:
        models.append(DemoModel(
            "本项目训练模型", str(candidates[0]),
            "COCO8 小样本训练结果，用于展示训练流程与模型切换。",
        ))
    return tuple(models)


def demo_samples(paths: ProjectPaths) -> dict[str, str]:
    return {
        "人物与领带": str(paths.root / "demo_assets" / "zidane.jpg"),
        "街景与车辆": str(paths.root / "demo_assets" / "bus.jpg"),
    }
