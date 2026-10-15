"""启动独立训练进程，观察真实 CSV 与日志，通过事件推送训练快照。"""

import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from threading import Event, Lock, Thread

from common.events import EventBus
from common.training_view import TrainingSnapshot

from backend.runtime.paths import ProjectPaths

from .records import expected_epochs, read_training_points


def terminate_training(process) -> None:
    """停止本服务创建的进程树，包含 Windows 虚拟环境启动器的子进程。"""
    if process.poll() is not None:
        return
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=8,
        )
        if result.returncode and process.poll() is None:
            raise RuntimeError("未能停止训练进程，请保留窗口并重试停止。")
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


class TrainingMonitor:
    def __init__(self, paths: ProjectPaths, events: EventBus, before_start):
        self.paths, self.events, self.before_start = paths, events, before_start
        self.lock = Lock()
        self.cancel = Event()
        self.active = False
        self.process = None
        self.worker = None
        self.last_snapshot = None

    def _publish(self, snapshot: TrainingSnapshot):
        if snapshot != self.last_snapshot:
            self.last_snapshot = snapshot
            self.events.publish("training_view", snapshot=snapshot)

    def start(self, epochs: int) -> None:
        if type(epochs) is not int or not 1 <= epochs <= 100:
            self._publish(TrainingSnapshot("error", "训练轮数必须是 1 到 100 的整数。", 20))
            return
        with self.lock:
            if self.active:
                return
            self.active = True
            self.cancel.clear()
        self.worker = Thread(target=self._run, args=(epochs,), name="yolo-training-monitor", daemon=True)
        self.worker.start()

    def stop(self) -> None:
        self.cancel.set()

    def close(self) -> None:
        self.stop()
        if self.worker is not None and self.worker.is_alive():
            self.worker.join(20)

    def history(self) -> None:
        with self.lock:
            if self.active:
                if self.last_snapshot is not None:
                    self.events.publish("training_view", snapshot=self.last_snapshot)
                return
        Thread(target=self._history, name="yolo-training-history", daemon=True).start()

    def _history(self):
        try:
            candidates = sorted(self.paths.runs.glob("*/results.csv"), key=lambda file: file.stat().st_mtime, reverse=True)
            candidates.append(self.paths.root / "examples" / "results.csv")
            selection = None
            for source in candidates:
                points = read_training_points(source)
                if points:
                    epochs = expected_epochs(source.parent, points[-1].epoch)
                    if selection is None:
                        selection = source, points, epochs
                    if points[-1].epoch >= epochs:
                        selection = source, points, epochs
                        break
            if selection is not None:
                source, points, epochs = selection
                suffix = "" if points[-1].epoch >= epochs else "（未完成全部轮次）"
                with self.lock:
                    if self.active:
                        return
                    self._publish(TrainingSnapshot(
                        "history", f"历史记录：已记录 {points[-1].epoch}/{epochs} 轮{suffix}，可开始新的实时训练。",
                        epochs, points, str(source.parent), "历史记录",
                    ))
                return
            self._publish(TrainingSnapshot("history", "尚无训练记录，点击开始即可生成实时曲线。", 20))
        except Exception as error:
            self._publish(TrainingSnapshot("error", f"读取历史记录失败：{error}", 20))

    def _run(self, epochs: int):
        name = "stage_train_" + uuid.uuid4().hex[:10]
        directory = self.paths.runs / name
        points, device, tail = (), "准备中", ""
        final_snapshot = None
        try:
            self._publish(TrainingSnapshot("preparing", "正在准备独立训练进程…", epochs, directory=str(directory)))
            self.before_start()
            import torch

            device_arg = "0" if torch.cuda.is_available() else "cpu"
            device = torch.cuda.get_device_name(0) if device_arg == "0" else "CPU"
            if self.cancel.is_set():
                final_snapshot = TrainingSnapshot("stopped", "已取消训练。", epochs, directory=str(directory), device=device)
                return
            self.paths.logs.mkdir(parents=True, exist_ok=True)
            log_path = self.paths.logs / f"{name}.log"
            executable = str(Path(sys.executable).with_name("python.exe")) if os.name == "nt" else sys.executable
            arguments = [
                executable, "-u", "-X", "utf8", str(self.paths.root / "train.py"),
                "--epochs", str(epochs), "--name", name, "--device", device_arg, "--skip-preview",
            ]
            environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
            with log_path.open("w", encoding="utf-8") as log:
                self.process = subprocess.Popen(
                    arguments, cwd=self.paths.root, env=environment, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                while True:
                    points = read_training_points(directory / "results.csv")
                    text = log_path.read_text(encoding="utf-8", errors="replace")
                    tail = "\n".join(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).splitlines()[-8:])
                    self._publish(TrainingSnapshot(
                        "running", "正在真实训练，每轮验证完成后更新曲线。", epochs, points, str(directory), device, tail,
                    ))
                    if self.process.poll() is not None:
                        break
                    if self.cancel.wait(0.2):
                        terminate_training(self.process)
                        final_snapshot = TrainingSnapshot(
                            "stopped", "训练已停止，已写入的记录保留在结果目录。", epochs,
                            read_training_points(directory / "results.csv"), str(directory), device, tail,
                        )
                        return
                points = read_training_points(directory / "results.csv")
                if self.process.returncode != 0:
                    raise RuntimeError(f"训练进程退出（代码 {self.process.returncode}），请查看下方日志。")
                if not points or points[-1].epoch != epochs or not (directory / "weights" / "best.pt").is_file():
                    raise RuntimeError("训练结果不完整，请查看日志及结果目录。")
                final_snapshot = TrainingSnapshot("completed", "训练完成，最佳权重和训练曲线已保存。", epochs, points, str(directory), device, tail)
        except Exception as error:
            if self.process is not None and self.process.poll() is None:
                try:
                    terminate_training(self.process)
                except Exception as stop_error:
                    error = RuntimeError(f"{error}；{stop_error}")
            final_snapshot = TrainingSnapshot("error", str(error), epochs, points, str(directory), device, tail)
        finally:
            with self.lock:
                self.active = False
            if final_snapshot is not None:
                self._publish(final_snapshot)
