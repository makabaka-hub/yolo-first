# 运行环境

- `paths.py`：集中管理项目路径，相对路径以项目根目录为基准。
- `configuration.py`：读取训练 YAML、应用参数覆盖并检查参数。
- `environment.py`：显式初始化计算库，检查 GPU，将第三方日志转为事件。
- `output.py`：将第三方直接输出的内容转为事件，供界面选择是否显示。

导入模块不会创建目录、修改环境变量或加载 PyTorch、Ultralytics。上述操作只在服务方法被调用时执行。

检查命令：在项目根目录运行 `.\.venv\Scripts\python.exe -X utf8 check_env.py`。
