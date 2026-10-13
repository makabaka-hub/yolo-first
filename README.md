# YOLO 第一次训练

使用 Ultralytics 的 YOLO26n 预训练模型和官方 COCO8 数据集，完成训练、保存权重，再重新加载权重识别图片。

COCO8 只有 4 张训练图片和 4 张验证图片，本项目用于检查流程，不能据此判断真实场景中的识别效果。

## 快速启动

在项目根目录打开 CMD、PowerShell 或 PyCharm 终端。首次安装：

```text
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

环境已安装时直接运行：

```text
.\.venv\Scripts\python.exe -X utf8 check_env.py
.\.venv\Scripts\python.exe -X utf8 train.py
```

训练默认使用第一个 NVIDIA GPU，运行 20 轮，然后用保存的最佳权重预测 4 张验证图片。首次运行会自动下载缺少的官方权重和数据。当前依赖针对 Windows、Python 3.13 和 CUDA 12.8；安装 PyTorch 需要下载较大的安装包。

## 独立预测

已经训练过时，可以直接用已有权重识别图片：

```text
.\.venv\Scripts\python.exe -X utf8 predict.py --weights runs/first_train/weights/best.pt --source datasets/coco8/images/val
```

将 `--source` 改为自己的图片或图片文件夹路径即可。相对路径以项目根目录为基准，也可传绝对路径。重复训练会生成 `first_train-2` 等新目录；使用新模型时，将 `--weights` 改为本次训练输出的权重路径。

## 调整参数

默认参数保存在 [config/training.yaml](config/training.yaml)。可以编辑配置，也可以只覆盖某次运行：

```text
.\.venv\Scripts\python.exe -X utf8 train.py --epochs 5 --name demo
.\.venv\Scripts\python.exe -X utf8 train.py --device cpu --skip-preview
```

`--skip-preview` 只执行训练。加 `--verbose` 可以显示第三方日志和错误堆栈。

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| epochs | 20 | 训练轮数 |
| imgsz | 640 | 输入图片的目标尺寸 |
| batch | 4 | 每批处理的图片数 |
| device | 0 | 第一个 NVIDIA GPU；也可指定 cpu |
| workers | 0 | 在主进程加载数据，适合 Windows 入门 |
| seed | 0 | 固定随机种子，便于比较结果 |

统一入口提供相同的命令：

```text
.\.venv\Scripts\python.exe -X utf8 main.py check
.\.venv\Scripts\python.exe -X utf8 main.py train
.\.venv\Scripts\python.exe -X utf8 main.py predict --weights runs/first_train/weights/best.pt --source datasets/coco8/images/val
```

## 代码组织

```text
yolo-first/
├── main.py                 模块组装：连接界面、事件与后端服务
├── train.py                保留训练入口
├── check_env.py            保留环境检查入口
├── predict.py              独立预测入口
├── config/                 数据集配置、训练参数
├── common/                 共享数据结构、事件发布与订阅
├── frontend/               参数解析、事件订阅、命令行展示
├── backend/
│   ├── application.py      协调检查、训练和预测流程
│   ├── runtime/            路径、配置读取、环境与日志适配
│   ├── data/               数据准备与本机配置生成
│   ├── training/           训练与逐轮进度通知
│   └── inference/          已有权重的图片推理
├── tests/                  结构与调用边界回归检查
├── examples/               首次训练的展示结果
├── logs/                   工程记录
└── licenses/               第三方许可文本
```

每个目录都有简短 README，自编 Python 文件顶部有职责注释。入口只负责组装或转交命令，训练流程由后端协调，各项计算由独立服务完成。

当前前端是命令行界面：它只解析输入、订阅事件和展示结果，不导入后端或计算库。后端不导入前端，通过共享事件接口推送进度与结果；第三方库的日志和直接输出也被转为事件，由界面决定是否展示。

事件在同一进程内同步派发。接入本机图形界面时可更换订阅者；远程网页界面还需要实现网络通信。当前项目没有网页或网络服务。

导入项目模块不会创建目录、修改环境变量或加载计算库。环境初始化在用户执行计算命令时才发生。YOLO 网络与训练算法由 Ultralytics、PyTorch 提供。

## 在 PyCharm 中运行

1. 打开本项目文件夹，选择 `.venv\Scripts\python.exe` 作为解释器。
2. 右键运行 `check_env.py`，检查 `gpu_available` 和显卡名称。
3. 右键运行 `train.py`，按控制台给出的路径查看权重、曲线和预测结果。
4. 需要预测自己的图片时，在终端运行上面的 `predict.py` 命令；也可在 PyCharm 的运行配置里填写脚本参数。

## 运行结果的位置

| 路径 | 内容 |
| --- | --- |
| models/yolo26n.pt | 官方预训练模型 |
| datasets/coco8/ | 图片及标注 |
| runs/first_train/weights/best.pt | 验证表现最佳的权重 |
| runs/first_train/weights/last.pt | 最后一轮的权重 |
| runs/first_train/results.csv | 逐轮训练指标 |
| runs/first_train/results.png | 训练曲线 |
| runs/preview/ | 训练结束后的图片预测 |
| runs/prediction/ | 独立预测结果 |
| .ultralytics/ | 当前项目的本机配置 |
| logs/environment.json | 环境检查报告 |

重复运行会创建带编号的新结果目录。数据集、本机配置、权重、虚拟环境和完整运行结果由 `.gitignore` 排除，GitHub 保存代码、配置、说明和精选示例。

## 训练结果展示

以下保留的是首次 20 轮训练的结果，后续运行不会自动覆盖这些示例。

![20 轮训练曲线](examples/training-curves.png)

![训练后的模型识别验证图片](examples/prediction.jpg)

逐轮指标见 [examples/results.csv](examples/results.csv)。示例图片来自官方 COCO8 验证集。

## 验证

```text
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

检查导入副作用、前后端依赖边界、事件订阅、第三方输出转发、独立预测与错误参数处理。实际训练和预测的验证记录见 [logs/progress.md](logs/progress.md)。

## AI 协助与参考

环境安装、代码、说明、训练运行和工程整改由 Codex 协助完成。可以按“界面输入 → 模块组装 → 后端协调 → 环境与数据 → 训练或推理 → 事件通知 → 界面展示”的顺序阅读代码。

- [Ultralytics 训练说明](https://docs.ultralytics.com/modes/train/)
- [Ultralytics 回调说明](https://docs.ultralytics.com/usage/callbacks/)
- [COCO8 数据集说明](https://docs.ultralytics.com/datasets/detect/coco8/)
- [PyTorch 安装版本](https://pytorch.org/get-started/previous-versions/)

`config/coco8.yaml` 改编自 Ultralytics 的配置，保留其 AGPL-3.0 许可说明，许可文本见 [licenses/ultralytics-AGPL-3.0.txt](licenses/ultralytics-AGPL-3.0.txt)。
