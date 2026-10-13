"""读取训练 YAML，应用命令行覆盖，并校验参数。"""

from pathlib import Path

from common.contracts import Command, TrainingOptions

from .paths import ProjectPaths


def validate_device(value: object) -> str:
    device = str(value)
    if device != "cpu" and not device.isdecimal():
        raise ValueError("device 必须是 cpu 或单个 GPU 编号，例如 0。")
    return device


def validate_name(value: object, field: str = "name") -> str:
    if not isinstance(value, str) or not value.strip() or value in (".", ".."):
        raise ValueError(f"{field} 必须是非空的结果文件夹名称。")
    if any(character in value for character in '/\\:*?"<>|'):
        raise ValueError(f"{field} 不能包含路径分隔符或 Windows 文件名禁用字符。")
    return value


def load_training_options(paths: ProjectPaths, command: Command) -> TrainingOptions:
    import yaml

    config_file = paths.resolve(command.config)
    settings = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("训练配置必须是 YAML 键值映射。")
    required = {
        "data", "model", "epochs", "imgsz", "batch", "device", "workers",
        "seed", "name", "preview_name",
    }
    missing = required - settings.keys()
    unknown = settings.keys() - required
    if missing or unknown:
        raise ValueError(f"训练配置字段错误，缺少：{sorted(missing)}，未知：{sorted(unknown)}。")
    for key in ("epochs", "name", "device"):
        override = getattr(command, key)
        if override is not None:
            settings[key] = override
    for key in ("epochs", "imgsz", "batch", "workers", "seed"):
        value = settings[key]
        minimum = 0 if key in ("workers", "seed") else 1
        if type(value) is not int or value < minimum:
            raise ValueError(f"{key} 必须是大于等于 {minimum} 的整数。")
    if not isinstance(settings["data"], str) or not settings["data"].strip():
        raise ValueError("data 必须是数据集配置文件路径。")
    # 仅使用项目 models 目录下的 .pt 文件，路径不依赖启动位置。
    model = settings["model"]
    if not isinstance(model, str) or Path(model).name != model or not model.endswith(".pt"):
        raise ValueError("model 必须是 .pt 权重文件名，例如 yolo26n.pt。")
    return TrainingOptions(
        data_config=(config_file.parent / settings["data"]).resolve(),
        model=model,
        epochs=settings["epochs"],
        imgsz=settings["imgsz"],
        batch=settings["batch"],
        device=validate_device(settings["device"]),
        workers=settings["workers"],
        seed=settings["seed"],
        name=validate_name(settings["name"]),
        preview_name=validate_name(settings["preview_name"], "preview_name"),
    )
