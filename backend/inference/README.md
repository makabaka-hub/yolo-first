# 图片推理

`service.py` 重新加载已有权重，识别指定图片或图片文件夹，保存带检测框的图片，并推送结果位置和图片数量。

此服务不调用训练服务。训练结束后的演示与独立预测命令复用同一个服务。

启动命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 predict.py --weights runs/first_train/weights/best.pt --source datasets/coco8/images/val`。
