# YOLO 第一次训练

用 Ultralytics 完成一次目标检测训练，并保存模型权重、训练曲线和图片识别示例。

使用 YOLO26n 预训练模型和官方 COCO8 数据集。COCO8 只有 4 张训练图片和 4 张验证图片，本项目用于检查训练流程，不能据此判断模型在真实场景中的效果。

## 安装与运行

下载本仓库，在项目根目录打开 CMD、PowerShell 或 PyCharm 的终端，依次执行：

```text
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 check_env.py
.\.venv\Scripts\python.exe -X utf8 train.py
```

已有 `.venv` 环境时，可直接执行后两条命令。首次运行会在需要时下载官方预训练模型和 COCO8 数据集，数据、模型和结果保存在项目内。PyTorch 安装包较大，第一次安装需要等待下载完成。

当前依赖版本针对 Windows、Python 3.13 和支持 CUDA 12.8 的 NVIDIA GPU，运行前需要可用的 NVIDIA 驱动。

## 训练结果展示

![20 轮训练曲线](examples/training-curves.png)

![训练后模型识别验证图片](examples/prediction.jpg)

逐轮指标见 [examples/results.csv](examples/results.csv)。识别示例使用官方 COCO8 的验证图片。

## 在 PyCharm 中运行

1. 使用“打开 / Open”打开本项目文件夹。
2. 在 Python 解释器设置中，选择项目内已有的 `.venv\Scripts\python.exe`；若环境尚未创建，先按上面的步骤安装。
3. 右键运行 `check_env.py`。确认输出中的 `gpu_available` 为 `true`，并显示实际使用的显卡名称。
4. 右键运行 `train.py`。它会训练 20 轮，再重新加载训练后的模型识别 4 张验证图片。

## 从终端运行

在项目文件夹中执行以下命令，CMD 和 PowerShell 均可使用：

```text
.\.venv\Scripts\python.exe -X utf8 check_env.py
.\.venv\Scripts\python.exe -X utf8 train.py
```

## 文件位置

- `train.py`：训练入口，准备数据、配置训练参数，并检查训练后模型的图片识别。
- `check_env.py`：检查 Python、训练库和 GPU。
- `coco8.yaml`：数据集配置，记录类别名称和数据路径。
- `models/yolo26n.pt`：官方预训练模型。
- `datasets/coco8/`：图片和对应的标注文件。
- `runs/first_train/weights/best.pt`：训练期间根据验证表现选出的模型。
- `runs/first_train/weights/last.pt`：最后一轮保存的模型。
- `runs/first_train/results.csv`：各轮训练的指标。
- `runs/first_train/results.png`：训练曲线。
- `runs/preview/`：训练后模型识别验证图片的结果。
- `logs/`：环境信息、素材来源和首次训练日志。
- `examples/`：精选训练曲线、识别图片和逐轮指标，用于在 GitHub 中展示。

YOLO 网络结构和训练算法由 Ultralytics、PyTorch 提供，本项目的代码负责组织训练流程。完整数据集、模型权重、运行目录和本机环境信息由 `.gitignore` 排除，仓库保存代码、配置、文档和精选展示结果。

再次运行时，Ultralytics 通常会创建带编号的新结果文件夹，保留前一次训练结果。

## 训练参数

| 参数 | 本次设置 | 含义 |
| --- | --- | --- |
| epochs | 20 | 训练 20 轮 |
| imgsz | 640 | 输入图片的目标尺寸 |
| batch | 4 | 每批处理 4 张图片 |
| device | 0 | 使用第一个 NVIDIA GPU |
| workers | 0 | 在主进程中加载数据 |
| seed | 0 | 固定随机种子，便于比较运行结果 |

## 重新安装环境

现有项目已经创建了 `.venv`，无需重复创建。迁移到其他电脑时，可以在项目文件夹中创建新的环境：

```text
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`coco8.yaml` 使用相对数据路径。`train.py` 根据当前项目位置生成本机配置，移动或下载项目到不同目录时，无需手动填写原电脑的数据路径。

## AI 协助情况

环境安装、训练脚本、项目说明、首次训练和仓库整理由 Codex 协助完成。阅读代码时，可以按“检查环境 → 准备数据 → 读取预训练模型 → 训练 → 保存权重 → 加载训练后的权重 → 识别图片”的顺序理解。

## 参考

- [Ultralytics 训练说明](https://docs.ultralytics.com/modes/train/)
- [COCO8 数据集说明](https://docs.ultralytics.com/datasets/detect/coco8/)
- [PyTorch 官方安装版本](https://pytorch.org/get-started/previous-versions/)

`coco8.yaml` 改编自 Ultralytics 提供的配置，保留其 AGPL-3.0 许可说明；对应的许可文本见 [licenses/ultralytics-AGPL-3.0.txt](licenses/ultralytics-AGPL-3.0.txt)。

## 首次训练结果

2026-10-13 已完成 20 轮 GPU 训练，生成 best.pt、last.pt、results.csv 和 results.png。训练后的模型已重新加载，并保存了 4 张验证图片的识别结果。环境检查与依赖检查均通过。工程记录见 [logs/progress.md](logs/progress.md)，完整环境与训练记录保存在本机的 logs/training_summary.json。
