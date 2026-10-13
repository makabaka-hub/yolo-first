"""读取数据集配置，补齐数据并生成包含绝对路径的本机配置。"""

from pathlib import Path

from common.contracts import DatasetInfo
from common.events import EventBus

from backend.runtime.paths import ProjectPaths


class DatasetService:
    def __init__(self, paths: ProjectPaths, events: EventBus):
        self.paths = paths
        self.events = events

    def prepare(self, config_file: Path) -> DatasetInfo:
        import yaml
        from ultralytics.utils.downloads import download

        data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("数据集配置必须是 YAML 键值映射。")
        for key in ("path", "train", "val"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f"数据集配置 {key} 必须是非空路径。")
        dataset_dir = (self.paths.datasets / data["path"]).resolve()
        splits = {split: dataset_dir / data[split] for split in ("train", "val")}
        if not all(directory.is_dir() for directory in splits.values()):
            url = data.get("download")
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError("数据集目录不存在，配置需要提供 HTTPS download 地址。")
            self.events.publish("data_downloading", url=url)
            download(url, dir=self.paths.datasets, unzip=True)
        for split, directory in splits.items():
            if not directory.is_dir():
                raise FileNotFoundError(f"{split} 图片目录不存在：{directory}")
        data["path"] = str(dataset_dir)
        local_config = self.paths.config / f"{config_file.stem}.local.yaml"
        local_config.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        self.events.publish("data_ready", config=str(local_config), directory=str(dataset_dir))
        return DatasetInfo(local_config, splits["val"])
