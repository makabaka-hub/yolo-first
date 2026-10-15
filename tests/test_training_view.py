"""验证实时 CSV 读取、历史记录选择和训练完成状态的生命周期。"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.runtime.paths import ProjectPaths
from backend.demo.catalog import demo_models
from backend.training.monitor import TrainingMonitor
from backend.training.records import expected_epochs, read_training_points
from common.events import EventBus


HEADER = "epoch,train/box_loss,train/cls_loss,metrics/precision(B),metrics/recall(B),metrics/mAP50(B),time\n"
ROW = "1,1.2,2.3,0.8,0.7,0.75,5\n"


class TrainingViewTests(unittest.TestCase):
    def test_reader_ignores_partial_row_during_append(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "results.csv"
            source.write_text(HEADER + ROW + "2,1.1,2.1,0.85,0.75,0.8,", encoding="utf-8")
            points = read_training_points(source)
            self.assertEqual([point.epoch for point in points], [1])
            with source.open("a", encoding="utf-8") as stream:
                stream.write("10\n")
            self.assertEqual([point.epoch for point in read_training_points(source)], [1, 2])

    def test_reader_skips_nonfinite_and_duplicate_epochs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "results.csv"
            source.write_text(HEADER + ROW + ROW + "2,nan,2.3,0.8,0.7,0.75,10\n", encoding="utf-8")
            self.assertEqual(len(read_training_points(source)), 1)

    def test_history_retains_planned_epoch_count_for_stopped_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "runs" / "partial"
            run.mkdir(parents=True)
            (run / "results.csv").write_text(HEADER + ROW, encoding="utf-8")
            (run / "args.yaml").write_text("epochs: 20\n", encoding="utf-8")
            monitor = TrainingMonitor(ProjectPaths(root), EventBus(), lambda: None)
            monitor._history()
            self.assertEqual(monitor.last_snapshot.epochs, 20)
            self.assertEqual(len(monitor.last_snapshot.points), 1)
            self.assertIn("未完成", monitor.last_snapshot.message)
            self.assertEqual(expected_epochs(run, 1), 20)

    def test_terminal_event_is_published_after_monitor_becomes_idle(self):
        with tempfile.TemporaryDirectory() as directory:
            events = EventBus()
            monitor = TrainingMonitor(ProjectPaths(Path(directory)), events, lambda: None)
            observed = []
            events.subscribe(lambda event: observed.append((event.data["snapshot"].phase, monitor.active)))
            monitor.active = True
            monitor.cancel.set()
            with patch.dict("sys.modules", {"torch": Mock()}):
                monitor._run(20)
            self.assertEqual(observed[-1], ("stopped", False))

    def test_demo_model_menu_skips_weights_from_interrupted_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "runs" / "partial"
            (run / "weights").mkdir(parents=True)
            (run / "weights/best.pt").write_bytes(b"test placeholder")
            (run / "results.csv").write_text(HEADER + ROW, encoding="utf-8")
            (run / "args.yaml").write_text("epochs: 20\n", encoding="utf-8")
            self.assertEqual(len(demo_models(ProjectPaths(root))), 1)


if __name__ == "__main__":
    unittest.main()
