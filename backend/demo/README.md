# 演示计算服务

`catalog.py` 发现演示模型和示例，`detector.py` 负责模型预热与推理，`camera.py` 负责摄像头输入，`storage.py` 负责保存检测帧。`controller.py` 在独立线程中协调这些服务和用户命令。

仅用户点击打开摄像头时读取相机；停止、切换图片、异常或退出时释放。实时帧以 JPEG 字节和检测数据通过事件推送，不调用 Tk 控件。

在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 demo.py`。
