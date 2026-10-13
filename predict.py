"""独立图片预测入口，将参数交给统一组装入口。"""

import sys

from main import main


if __name__ == "__main__":
    raise SystemExit(main(["predict", *sys.argv[1:]]))
