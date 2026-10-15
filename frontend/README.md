# 展示界面

`cli.py` 解析输入，`console.py` 订阅事件并显示报告、训练进度、错误和结果位置。

命令行界面使用 Python 标准库和 `common`，由 `main.py` 组装。

`desktop/` 提供 Tk 本机窗口，使用 Pillow 渲染 JPEG 画面，由 `demo.py` 组装。两种界面都不导入后端、PyTorch、Ultralytics 或 OpenCV，计算通过共享接口提交，结果通过事件接收。

查看命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 main.py --help`。
