"""验证桌面帧背压、后台错误恢复、参数校验和摄像头异常释放。"""

import sys
import os
import time
import unittest
import uuid
from dataclasses import replace
from queue import Queue
from threading import Event
from unittest.mock import Mock, patch

from backend.demo.camera import open_camera
from backend.demo.controller import DemoController
from backend.demo.camera_session import CameraSession
from common.demo import DemoFrame, DemoOptions
from common.events import EventBus
from frontend.desktop.bridge import DesktopInbox
from frontend.desktop.instance import DesktopInstance


def stalled_camera_worker(index, backend, frames, stop):
    """模拟卡在不可取消原生调用中的驱动。"""
    time.sleep(60)


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
        primary, fallback = Mock(), Mock()
        primary.wait_first.side_effect = RuntimeError("设备占用")
        fallback.wait_first.side_effect = RuntimeError("设备占用")
        with patch("backend.demo.camera.CameraSession", side_effect=[primary, fallback]), self.assertRaisesRegex(RuntimeError, "摄像头"):
            open_camera(0)
        primary.release.assert_called_once()
        fallback.release.assert_called_once()

    def test_camera_timeout_releases_first_backend_before_fallback(self):
        primary, fallback = Mock(), Mock()
        primary.wait_first.side_effect = TimeoutError("响应超时")
        with patch("backend.demo.camera.CameraSession", side_effect=[primary, fallback]):
            self.assertIs(open_camera(0), fallback)
        primary.release.assert_called_once()
        fallback.wait_first.assert_called_once()
        fallback.release.assert_not_called()

    def test_cancel_does_not_open_a_camera(self):
        cancel = Event()
        cancel.set()
        with patch("backend.demo.camera.CameraSession") as session, self.assertRaises(InterruptedError):
            open_camera(0, cancel=cancel)
        session.assert_not_called()

    def test_stalled_driver_process_can_be_timed_out_and_reclaimed(self):
        import multiprocessing

        with patch("backend.demo.camera_session.capture_worker", stalled_camera_worker):
            capture = CameraSession(0, "CAP_MSMF")
        process_id = capture.process.pid
        try:
            with self.assertRaises(TimeoutError):
                capture.wait_first(0.2)
        finally:
            started = time.monotonic()
            capture.release()
        self.assertLess(time.monotonic() - started, 3)
        self.assertNotIn(process_id, [child.pid for child in multiprocessing.active_children()])

    @unittest.skipUnless(os.name == "nt", "Windows 单实例互斥量")
    def test_duplicate_launch_reuses_instance_until_first_window_exits(self):
        name = "Local\\YOLOTest-" + uuid.uuid4().hex
        with DesktopInstance(name) as first:
            self.assertTrue(first.acquired)
            with DesktopInstance(name) as second:
                self.assertFalse(second.acquired)
        with DesktopInstance(name) as next_instance:
            self.assertTrue(next_instance.acquired)


if __name__ == "__main__":
    unittest.main()
