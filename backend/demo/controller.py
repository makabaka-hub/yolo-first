"""用单个后台线程执行演示任务，向订阅者推送状态和最新检测帧。"""

from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from time import perf_counter

from common.demo import DemoFrame, DemoOptions
from common.events import EventBus

from backend.runtime.environment import RuntimeService
from backend.runtime.output import forward_library_output

from .detector import DemoDetector
from .camera import open_camera, read_camera
from .storage import save_frame


class DemoController:
    def __init__(self, runtime: RuntimeService, events: EventBus, options: DemoOptions, initial_image: str):
        self.runtime, self.events, self.options = runtime, events, options
        self.initial_image = initial_image
        self.detector = DemoDetector()
        self.commands = Queue()
        self.shutdown = Event()
        self.stop_capture = Event()
        self.worker = Thread(target=self._run, name="yolo-demo-worker", daemon=True)
        self.capture = None
        self.last_image = None
        self.last_source = ""

    def start(self) -> None:
        self.worker.start()

    def image(self, source: str, options: DemoOptions) -> None:
        self.stop_capture.set()
        self.commands.put(("image", (source, options)))

    def camera(self, index: int, options: DemoOptions) -> None:
        self.commands.put(("camera", (index, options)))

    def configure(self, options: DemoOptions) -> None:
        self.commands.put(("configure", options))

    def stop(self) -> None:
        self.stop_capture.set()
        self.commands.put(("stop", None))

    def save(self, destination: str, frame: DemoFrame) -> None:
        self.commands.put(("save", (destination, frame)))

    def close(self) -> None:
        self.shutdown.set()
        self.stop_capture.set()
        self.commands.put(("close", None))

    def _state(self, phase: str, message: str) -> None:
        self.events.publish("demo_state", phase=phase, message=message)

    def _load(self, options: DemoOptions) -> None:
        if self.detector.weights != options.weights:
            self._state("loading", "正在加载模型并预热，请稍候…")
            with forward_library_output(self.events):
                self.detector.load(options)
        self.options = options

    def _release_camera(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def _image(self, source: str, options: DemoOptions) -> None:
        self._release_camera()
        self._load(options)
        self._state("working", "正在识别图片…")
        image = self.detector.read_image(source)
        frame = self.detector.detect(image, options, Path(source).name, "image")
        self.last_image, self.last_source = image, Path(source).name
        self.events.publish("demo_frame", frame=frame)
        self._state("idle", "图片识别完成。可以调节阈值、切换模型或保存结果。")

    def _camera(self, index: int, options: DemoOptions) -> None:
        self._release_camera()
        self._load(options)
        self._state("working", f"正在打开摄像头 {index}…")
        self.capture = open_camera(index)
        self.stop_capture.clear()
        self._state("streaming", "摄像头实时识别中。点击停止可释放摄像头；保存结果可保留当前画面。")

    def _configure(self, options: DemoOptions) -> None:
        self._load(options)
        if self.capture is None and self.last_image is not None:
            self._state("working", "正在应用新的识别设置…")
            frame = self.detector.detect(self.last_image, options, self.last_source, "image")
            self.events.publish("demo_frame", frame=frame)
            self._state("idle", "设置已应用。可以继续调节阈值或切换输入。")
        elif self.capture is not None:
            self._state("streaming", "新设置已应用，摄像头实时识别中。")
        else:
            self._state("idle", "模型已就绪，请选择图片或打开摄像头。")

    def _save(self, destination: str, frame: DemoFrame) -> None:
        path, report_path = save_frame(destination, frame)
        self.events.publish("demo_saved", path=str(path), report=str(report_path))

    def _handle(self, name, data):
        if name == "image":
            self._image(*data)
        elif name == "camera":
            self._camera(*data)
        elif name == "configure":
            self._configure(data)
        elif name == "save":
            self._save(*data)
        elif name == "stop":
            self._release_camera()
            self._state("idle", "已停止，保留最后一帧。可保存结果或切换到图片演示。")

    def _run(self):
        try:
            self._state("loading", "正在初始化本地计算环境…")
            with forward_library_output(self.events):
                self.runtime.initialize()
                device = self.detector.initialize()
                self._load(self.options)
            self.events.publish("demo_ready", device=device)
            if not self.shutdown.is_set():
                self._image(self.initial_image, self.options)
        except Exception as error:
            self.events.publish("demo_error", message=str(error))
        try:
            while not self.shutdown.is_set():
                try:
                    if self.capture is not None and self.stop_capture.is_set():
                        self._release_camera()
                    try:
                        name, data = self.commands.get(timeout=0 if self.capture is not None else 0.1)
                    except Empty:
                        name = None
                    if name == "close":
                        break
                    if name:
                        self._handle(name, data)
                    elif self.capture is not None:
                        started = perf_counter()
                        image = read_camera(self.capture)
                        if self.stop_capture.is_set() or self.shutdown.is_set():
                            continue
                        frame = self.detector.detect(image, self.options, "摄像头 · 镜像", "camera", started)
                        self.last_image, self.last_source = image, "摄像头截图"
                        self.events.publish("demo_frame", frame=frame)
                except Exception as error:
                    self._release_camera()
                    self.events.publish("demo_error", message=str(error))
        finally:
            self._release_camera()
            self.events.publish("demo_closed")
