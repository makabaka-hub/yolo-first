# 命令行界面

`cli.py` 解析输入，`console.py` 订阅事件并显示报告、训练进度、错误和结果位置。

界面只使用 Python 标准库和 `common`，不导入后端、PyTorch 或 Ultralytics。后端调用和模块组装由 `main.py` 完成。

当前 UI 是命令行界面。以后接入图形界面时，可以替换事件订阅者；远程界面需要另外实现网络通信。

查看命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 main.py --help`。
