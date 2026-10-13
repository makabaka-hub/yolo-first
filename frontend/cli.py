"""解析命令行输入为共享命令对象，不调用计算服务。"""

import argparse
import sys

from common.contracts import Command


def parse_args(argv: list[str] | None = None) -> Command:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        arguments = ["train"]
    parser = argparse.ArgumentParser(description="YOLO 训练、环境检查和独立图片预测")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    check = subparsers.add_parser("check", help="检查 Python、计算库和 GPU")
    check.add_argument("--verbose", action="store_true", help="显示第三方日志和错误堆栈")
    train = subparsers.add_parser("train", help="训练模型并识别验证图片")
    train.add_argument("--config", default="config/training.yaml", help="训练 YAML 路径，相对于项目根目录")
    train.add_argument("--epochs", type=int, help="覆盖配置中的训练轮数")
    train.add_argument("--name", help="训练结果文件夹名称")
    train.add_argument("--device", help="GPU 编号，例如 0；也可指定 cpu")
    train.add_argument("--skip-preview", action="store_true", help="训练完成后跳过验证图片预测")
    train.add_argument("--verbose", action="store_true", help="显示第三方日志和错误堆栈")
    predict = subparsers.add_parser("predict", help="使用已有权重识别图片")
    predict.add_argument("--weights", default="runs/first_train/weights/best.pt", help="已有 .pt 权重路径")
    predict.add_argument("--source", default="datasets/coco8/images/val", help="图片或图片文件夹路径")
    predict.add_argument("--device", default="0", help="GPU 编号或 cpu")
    predict.add_argument("--name", default="prediction", help="预测结果文件夹名称")
    predict.add_argument("--verbose", action="store_true", help="显示第三方日志和错误堆栈")
    return Command(**vars(parser.parse_args(arguments)))
