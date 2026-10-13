# 项目配置

`training.yaml` 保存默认训练参数。`data` 相对于该配置文件所在目录；`model` 是 `models/` 内的权重文件名，缺少官方权重时自动下载。

`coco8.yaml` 保存数据路径、类别和下载地址，其 `path` 相对于项目 `datasets/` 目录。该文件保留原始许可说明。

可以复制训练配置后使用 `train.py --config config/你的配置.yaml`，或用 `--epochs`、`--device`、`--name` 覆盖单次运行参数。
