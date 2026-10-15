"""带超时和取消地打开相机，验证首帧后交付连接，并读取镜像画面。"""

from .camera_session import CameraSession


def open_camera(index: int, cancel=None, timeout: float = 4.0):
    errors = []
    for backend in ("CAP_MSMF", "CAP_DSHOW"):
        if cancel is not None and cancel.is_set():
            raise InterruptedError("已取消打开摄像头。")
        capture = CameraSession(index, backend)
        try:
            capture.wait_first(timeout, cancel)
            return capture
        except InterruptedError:
            capture.release()
            raise
        except (RuntimeError, TimeoutError) as error:
            capture.release()
            errors.append(str(error))
    detail = "响应超时" if any("超时" in error for error in errors) else "无法读取画面"
    raise RuntimeError(f"摄像头{detail}。请关闭占用相机的软件，确认编号和 Windows 相机权限后重试。")


def read_camera(capture):
    import cv2

    success, image = capture.read()
    if not success:
        raise RuntimeError("摄像头画面读取中断，请停止后重试；也可使用内置图片继续演示。")
    return cv2.flip(image, 1)
