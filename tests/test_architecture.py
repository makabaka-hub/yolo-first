"""验证导入副作用、前后端依赖边界和独立预测流程。"""

import ast
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from backend.application import Application
from backend.data.preparation import DatasetService
from backend.inference.service import InferenceService
from backend.runtime.environment import RuntimeService
from backend.runtime.paths import ProjectPaths
from backend.runtime.output import forward_library_output
from backend.training.service import TrainingService
from common.contracts import Command
from common.events import EventBus
from frontend.console import ConsoleView


ROOT = Path(__file__).resolve().parents[1]


class ArchitectureTests(unittest.TestCase):
    def test_imports_do_not_write_files_change_environment_or_load_compute_libraries(self):
        # 放到全新目录检查，避免本机已有的配置文件掩盖导入副作用。
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("backend", "common", "frontend"):
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns("__pycache__"))
            for name in ("main.py", "train.py", "predict.py", "check_env.py", "demo.py"):
                shutil.copyfile(ROOT / name, root / name)
            probe = """
import importlib
import os
import sys
from pathlib import Path
root = Path.cwd()
files_before = {str(path.relative_to(root)) for path in root.rglob('*')}
environment_before = dict(os.environ)
for source in sorted(root.rglob('*.py')):
    parts = list(source.relative_to(root).with_suffix('').parts)
    if parts[-1] == '__init__':
        parts.pop()
    importlib.import_module('.'.join(parts))
assert dict(os.environ) == environment_before, '导入改变了环境变量'
assert {str(path.relative_to(root)) for path in root.rglob('*')} == files_before, '导入写入了文件'
assert 'torch' not in sys.modules, '导入时加载了 PyTorch'
assert 'ultralytics' not in sys.modules, '导入时加载了 Ultralytics'
"""
            result = subprocess.run(
                [sys.executable, "-B", "-X", "utf8", "-c", probe],
                cwd=root, capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout + result.stderr, "")

    def test_frontend_and_backend_only_share_contracts(self):
        forbidden = {
            "backend": {"frontend"},
            "frontend": {"backend", "torch", "ultralytics", "yaml", "cv2", "numpy"},
            "common": {"backend", "frontend", "torch", "ultralytics", "yaml", "cv2", "numpy"},
        }
        for directory, banned in forbidden.items():
            for source in (ROOT / directory).rglob("*.py"):
                tree = ast.parse(source.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        names = [node.module]
                    for name in names:
                        self.assertNotIn(name.split(".")[0], banned, str(source))

    def test_events_reach_multiple_subscribers_and_can_be_unsubscribed(self):
        events = EventBus()
        first, second = [], []
        unsubscribe = events.subscribe(first.append)
        events.subscribe(second.append)
        events.publish("training_progress", epoch=1, epochs=20)
        unsubscribe()
        unsubscribe()  # 重复取消不会影响其他订阅者。
        events.publish("training_progress", epoch=2, epochs=20)
        self.assertEqual([event.data["epoch"] for event in first], [1])
        self.assertEqual([event.data["epoch"] for event in second], [1, 2])
        with self.assertRaises(TypeError):
            first[0].data["epoch"] = 99

    def build_application(self, root):
        events = EventBus()
        received = []
        events.subscribe(received.append)
        runtime = Mock(spec=RuntimeService)
        datasets = Mock(spec=DatasetService)
        training = Mock(spec=TrainingService)
        inference = Mock(spec=InferenceService)
        application = Application(ProjectPaths(root), events, runtime, datasets, training, inference)
        return application, runtime, datasets, training, inference, received

    def test_library_output_is_forwarded_without_delaying_ui_progress(self):
        events = EventBus()
        received = []
        events.subscribe(received.append)
        output = io.StringIO()
        view = ConsoleView(output=output)
        events.subscribe(view.on_event)
        with forward_library_output(events):
            print("第三方下载进度")
            events.publish("training_progress", epoch=1, epochs=20)
            self.assertIn("训练进度：1/20", output.getvalue())
        self.assertNotIn("第三方下载进度", output.getvalue())
        self.assertEqual(received[0].name, "library_log")
        self.assertEqual(received[0].data["message"], "第三方下载进度")

    def test_predict_uses_existing_weights_without_preparing_data_or_training(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            application, runtime, datasets, training, inference, received = self.build_application(root)
            command = Command("predict", weights="saved.pt", source="image.jpg", device="cpu", name="demo")
            self.assertEqual(application.run(command), 0)
            runtime.require_device.assert_called_once_with("cpu")
            inference.predict.assert_called_once_with(root / "saved.pt", root / "image.jpg", "cpu", "demo")
            datasets.prepare.assert_not_called()
            training.train.assert_not_called()
            self.assertFalse(received)

    def test_invalid_epochs_fail_before_initializing_compute_runtime(self):
        application, runtime, datasets, training, inference, received = self.build_application(ROOT)
        self.assertEqual(application.run(Command("train", epochs=0)), 1)
        runtime.initialize.assert_not_called()
        datasets.prepare.assert_not_called()
        training.train.assert_not_called()
        inference.predict.assert_not_called()
        self.assertEqual(received[-1].name, "error")
        self.assertIn("epochs", received[-1].data["message"])


if __name__ == "__main__":
    unittest.main()
