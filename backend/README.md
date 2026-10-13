# 后端服务

`application.py` 协调环境检查、训练和独立预测。具体计算分别放在 `runtime/`、`data/`、`training/`、`inference/`。

后端不导入 `frontend`，不直接打印界面内容，进度和结果通过 `EventBus` 推送。更换界面不需要修改计算服务。

服务由根目录 `main.py` 组装；本目录不作为脚本直接运行。
