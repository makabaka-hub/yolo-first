"""解析桌面启动选项，仅决定初始显示的界面。"""

import argparse


def parse_launch_args():
    parser = argparse.ArgumentParser(description="YOLO 本机识别与训练过程展示")
    parser.add_argument("--training", action="store_true", help="启动时打开训练过程窗口")
    return parser.parse_args()
