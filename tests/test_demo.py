"""验证桌面帧背压、后台错误恢复、参数校验和摄像头异常释放。"""

import sys
import unittest
from dataclasses import replace
from queue import Queue
from unittest.mock import Mock, patch

from backend.demo.camera import open_camera
from backend.demo.controller import DemoController
from common.demo import DemoFrame, DemoOptions
from common.events import EventBus
from frontend.desktop.bridge import DesktopInbox


class FakeDetector:
    def __init__(self):
        self.weights = None

    def initialize(self):
        return "CPU test"

    def load(self, options):
        self.weights = options.weights

    def read_image(self, source):
        if source == "bad.jpg":
            raise ValueError("测试损坏图片")
        return b"decoded image"

    def detect(self, image, options, source, mode, started=None):
        return DemoFrame(b"annotated", b"original", (), 640, 480, 10, 0, source, mode, "test", options.confidence)


class DemoTests(unittest.TestCase):
    def test_inbox_keeps_latest_frame_without_dropping_control_events(self):
        events, inbox = EventBus(), DesktopInbox()
        events.subscribe(inbox.on_event)
        events.publish("demo_state", phase="streaming", message="ready")
        for number in range(300):
            events.publish("demo_frame", frame=number)
        events.publish("demo_saved", path="snapshot.jpg")
        events.publish("library_log", message="not a UI event")
        received = inbox.drain()
        self.assertEqual([event.name for event in received], ["demo_state", "demo_saved", "demo_frame"])
        self.assertEqual(received[-1].data["frame"], 299)
        self.assertEqual(inbox.drain(), [])

    def test_invalid_confidence_is_rejected(self):
        for value in (0, -0.5, 1.1, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                DemoOptions("model.pt", value)

    def test_worker_recovers_from_bad_image_and_stops(self):
        events, received = EventBus(), Queue()
        events.subscribe(received.put)
        options = DemoOptions("model.pt")
        controller = DemoController(Mock(), events, options, "initial.jpg")
        controller.detector = FakeDetector()

        def wait_for(name):
            for _ in range(20):
                event = received.get(timeout=3)
                if event.name == name:
                    return event
            self.fail(f"没有收到事件 {name}")

        controller.start()
        try:
            self.assertEqual(wait_for("demo_frame").data["frame"].source, "initial.jpg")
            controller.image("bad.jpg", options)
            self.assertIn("损坏图片", wait_for("demo_error").data["message"])
            controller.image("valid.jpg", options)
            self.assertEqual(wait_for("demo_frame").data["frame"].source, "valid.jpg")
            controller.configure(replace(options, confidence=0.75))
            self.assertEqual(wait_for("demo_frame").data["frame"].confidence, 0.75)
        finally:
            controller.close()
            controller.worker.join(3)
        self.assertFalse(controller.worker.is_alive())
        self.assertEqual(wait_for("demo_closed").name, "demo_closed")

    def test_camera_releases_both_failed_capture_backends(self):
        module = Mock()
        primary, fallback = Mock(), Mock()
        primary.isOpened.return_value = fallback.isOpened.return_value = False
        module.VideoCapture.side_effect = [primary, fallback]
        with patch.dict(sys.modules, {"cv2": module}), self.assertRaisesRegex(RuntimeError, "摄像头无法打开"):
            open_camera(0)
        primary.release.assert_called_once()
        fallback.release.assert_called_once()


if __name__ == "__main__":
    unittest.main()
