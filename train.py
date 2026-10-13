"""运行一次 YOLO 目标检测训练，并保存验证图片的识别结果。"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / ".ultralytics"
CONFIG_DIR.mkdir(exist_ok=True)
os.environ["YOLO_CONFIG_DIR"] = str(CONFIG_DIR)
os.environ["MPLCONFIGDIR"] = str(ROOT / ".cache" / "matplotlib")
os.environ["TORCH_HOME"] = str(ROOT / ".cache" / "torch")

import torch
import yaml
from ultralytics import YOLO, settings
from ultralytics.utils.downloads import download


def prepare_data():
    """解析相对数据路径，缺少 COCO8 时下载，并生成本机配置。"""
    data = yaml.safe_load((ROOT / "coco8.yaml").read_text(encoding="utf-8"))
    dataset_dir = (ROOT / "datasets" / data["path"]).resolve()
    if not all((dataset_dir / data[split]).is_dir() for split in ("train", "val")):
        download(data["download"], dir=ROOT / "datasets", unzip=True)
    data["path"] = str(dataset_dir)
    local_config = CONFIG_DIR / "coco8.local.yaml"
    local_config.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return local_config


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("未检测到可用的 NVIDIA GPU，请先运行 check_env.py 检查环境。")

    # 将数据、模型和训练结果放在项目内，便于在 PyCharm 中查看。
    settings.update({
        "datasets_dir": str(ROOT / "datasets"),
        "weights_dir": str(ROOT / "models"),
        "runs_dir": str(ROOT / "runs"),
        "sync": False,
    })
    (ROOT / "models").mkdir(exist_ok=True)
    model = YOLO(str(ROOT / "models" / "yolo26n.pt"))
    data_config = prepare_data()

    # 在预训练模型的基础上，用 COCO8 小数据集训练 20 轮。
    model.train(
        data=str(data_config),
        epochs=20,
        imgsz=640,
        batch=4,
        device=0,
        workers=0,
        project=str(ROOT / "runs"),
        name="first_train",
        plots=True,
        seed=0,
    )

    run_dir = Path(model.trainer.save_dir)
    best_weights = run_dir / "weights" / "best.pt"
    print(f"\n训练完成，结果目录：{run_dir}")
    print(f"训练后的模型：{best_weights}")

    # 重新加载训练后的权重，检查它能否识别验证图片。
    trained_model = YOLO(str(best_weights))
    previews = trained_model.predict(
        source=str(ROOT / "datasets" / "coco8" / "images" / "val"),
        device=0,
        save=True,
        project=str(ROOT / "runs"),
        name="preview",
    )
    print(f"识别示例目录：{previews[0].save_dir}")


# Windows 下将训练入口放在这里，避免子进程重复执行脚本。
if __name__ == "__main__":
    main()
