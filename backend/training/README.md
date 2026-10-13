# 模型训练

`service.py` 加载预训练权重并调用 YOLO 训练，通过回调推送逐轮进度，返回结果目录和 `best.pt` 路径。

参数来自 `config/training.yaml`，本模块不负责命令解析、数据显示或预测。

启动命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 train.py`。
