"""管理隔离相机进程及有界帧队列，提供可超时、可取消的读取。"""

from queue import Empty
from time import monotonic

from .camera_worker import capture_worker


class CameraSession:
    def __init__(self, index: int, backend: str):
        import multiprocessing

        context = multiprocessing.get_context("spawn")
        self.frames = context.Queue(maxsize=2)
        self.stop = context.Event()
        self.process = context.Process(
            target=capture_worker, args=(index, backend, self.frames, self.stop),
            name="yolo-camera", daemon=True,
        )
        self.closed = False
        self.first_frame = None
        try:
            self.process.start()
        except Exception:
            self.frames.close()
            raise

    def _receive(self, timeout: float, cancel=None):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            if cancel is not None and cancel.is_set():
                raise InterruptedError("已取消打开摄像头。")
            try:
                name, value = self.frames.get(timeout=min(0.1, max(0.001, deadline - monotonic())))
            except Empty:
                if not self.process.is_alive():
                    raise RuntimeError("摄像头进程已退出，请检查设备占用或相机权限。")
                continue
            if name == "error":
                raise RuntimeError(value)
            return value
        raise TimeoutError("摄像头响应超时，已回收本次连接。")

    def wait_first(self, timeout: float, cancel=None) -> None:
        self.first_frame = self._receive(timeout, cancel)

    def read(self):
        if self.closed:
            return False, None
        if self.first_frame is not None:
            image, self.first_frame = self.first_frame, None
        else:
            image = self._receive(3.0)
        # 丢弃排队旧帧，保留已到达的最新画面。
        for _ in range(2):
            try:
                name, value = self.frames.get_nowait()
            except Empty:
                break
            if name == "frame":
                image = value
        return True, image

    def release(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.stop.set()
        self.process.join(0.4)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(1.0)
        self.frames.cancel_join_thread()
        self.frames.close()
        if not self.process.is_alive():
            self.process.close()
        self.first_frame = None
