# 共享接口

`contracts.py` 定义命令、训练参数和结果；`events.py` 提供事件发布与订阅。

此目录只依赖 Python 标准库。前后端都可以使用它，彼此不互相导入。

事件在同一进程中同步派发，数据包含事件名和只读的字段映射。`subscribe()` 返回取消订阅函数；它不是网络推送接口。

常用事件：`environment_checked`、`training_progress`、`training_completed`、`prediction_completed`、`error`。服务方法的返回值用于后端流程衔接，事件用于通知界面。
