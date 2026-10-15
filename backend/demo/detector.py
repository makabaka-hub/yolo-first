"""封装演示推理，将 YOLO 检测框、标注图片和耗时转为共享数据。"""

from pathlib import Path
from time import perf_counter

from common.demo import DemoFrame, DemoOptions, Detection


class DemoDetector:
    def __init__(self):
        self.model = None
        self.weights = None
        self.device = "cpu"

    def initialize(self) -> str:
        import torch

        if torch.cuda.is_available():
            self.device = "0"
            return torch.cuda.get_device_name(0)
        return "CPU"

    def load(self, options: DemoOptions) -> None:
        if self.weights == options.weights:
            return
        import numpy as np
        from ultralytics import YOLO

        path = Path(options.weights)
        if not path.is_file() and path.name != "yolo26n.pt":
            raise FileNotFoundError(f"模型权重不存在：{path}")
        model = YOLO(str(path))
        # 加载时完成预热，避免按下演示按钮后才初始化 CUDA。
        model.predict(np.zeros((640, 640, 3), dtype=np.uint8), device=self.device, verbose=False)
        self.model, self.weights = model, options.weights

    def read_image(self, source: str):
        import cv2
        import numpy as np

        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"图片不存在：{source}")
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法读取这张图片，请选择 JPG、PNG、BMP 或 WebP 图片。")
        return image

    def detect(self, image, options: DemoOptions, source: str, mode: str, started: float | None = None) -> DemoFrame:
        import cv2

        started = perf_counter() if started is None else started
        result = self.model.predict(
            image, conf=options.confidence, imgsz=640, device=self.device,
            verbose=False, save=False,
        )[0]
        rows = result.boxes.data.cpu().tolist() if result.boxes is not None else []
        detections = tuple(sorted((
            Detection(result.names[int(row[-1])], float(row[-2]), tuple(float(value) for value in row[:4]))
            for row in rows
        ), key=lambda detection: detection.confidence, reverse=True))
        annotated = result.plot(line_width=2, font_size=16)
        success, output = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 91])
        original_success, original = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 91])
        if not success or not original_success:
            raise RuntimeError("图片编码失败。")
        elapsed = max(perf_counter() - started, 0.000001)
        return DemoFrame(
            output.tobytes(), original.tobytes(), detections, image.shape[1], image.shape[0],
            float(result.speed.get("inference", 0)), 1 / elapsed if mode == "camera" else 0,
            source, mode, Path(options.weights).stem, options.confidence,
        )
