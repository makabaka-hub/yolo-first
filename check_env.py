"""检查项目使用的 Python、训练库和 GPU，并保存环境信息。"""

import json
import sys
from importlib.metadata import version
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent


def main():
    report = {
        "python_path": sys.executable,
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "torchvision_version": version("torchvision"),
        "ultralytics_version": version("ultralytics"),
        "cuda_version": torch.version.cuda,
        "gpu_available": torch.cuda.is_available(),
    }
    if report["gpu_available"]:
        report["gpu_name"] = torch.cuda.get_device_name(0)
        report["gpu_memory_gb"] = round(
            torch.cuda.get_device_properties(0).total_memory / 1024**3, 2
        )
        # 实际执行一次显卡计算，验证 CUDA 内核可以运行。
        values = torch.ones((32, 32), device="cuda")
        report["gpu_calculation_result"] = (values @ values).sum().item()

    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / "environment.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
