# 模型训练

`service.py` 加载预训练权重并调用 YOLO 训练，通过回调推送逐轮进度，返回结果目录和 `best.pt` 路径。

参数来自 `config/training.yaml`，本模块不负责命令解析、数据显示或预测。

启动命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 train.py`。

`records.py` 读取已写完的 CSV 行及原定轮数；`monitor.py` 为窗口启动独立训练进程，观察实际 CSV 与日志，通过事件推送快照。停止时回收本服务启动的进程树，不会只关闭 Windows 虚拟环境启动器。

历史展示优先选择完整训练记录，中断记录保留原定轮数。窗口实时训练使用新的 `runs/stage_train_*/` 目录，保留旧结果。
