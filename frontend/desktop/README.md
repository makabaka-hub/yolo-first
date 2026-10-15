# 本机演示界面

`window.py` 组织窗口与展示事件，`theme.py` 定义样式，`bridge.py` 将后台事件交给 Tk 主线程。实时画面只保留最新一帧，避免排队造成画面延迟。

`instance.py` 使用 Windows 命名互斥量避免重复启动；再次启动时唤起已有演示窗口，减少多个窗口争用摄像头。

前端不导入后端或计算库，只通过 `common/demo.py` 的接口提交操作，通过事件接收结果。图片缩放和解码仅用于 UI 渲染。

启动：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 demo.py`，或双击根目录的 `启动演示.bat`。
