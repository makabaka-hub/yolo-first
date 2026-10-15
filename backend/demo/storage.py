"""将用户选择的检测帧保存为图片和同名 JSON 检测明细。"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from common.demo import DemoFrame


def save_frame(destination: str, frame: DemoFrame) -> tuple[Path, Path]:
    import cv2
    import numpy as np

    path = Path(destination)
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        raise ValueError("保存格式请选择 .jpg 或 .png。")
    image = cv2.imdecode(np.frombuffer(frame.annotated_jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    success, encoded = cv2.imencode(path.suffix, image)
    if not success:
        raise RuntimeError("结果图片保存失败。")
    encoded.tofile(str(path))
    report = {
        "saved_at": datetime.now().astimezone().isoformat(), "source": frame.source,
        "model": frame.model, "confidence_threshold": frame.confidence,
        "image_size": [frame.width, frame.height], "inference_ms": frame.inference_ms,
        "detections": [asdict(detection) for detection in frame.detections],
    }
    report_path = path.with_suffix(".json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, report_path
