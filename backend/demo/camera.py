"""打开 Windows 摄像头、读取镜像画面，并处理初始化失败时的释放。"""


def open_camera(index: int):
    import cv2

    capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not capture.isOpened():
        capture.release()
        capture = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError("摄像头无法打开。请尝试编号 1，或检查 Windows 相机权限及其他程序占用。")
    try:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return capture
    except Exception:
        capture.release()
        raise


def read_camera(capture):
    import cv2

    success, image = capture.read()
    if not success:
        raise RuntimeError("摄像头画面读取中断，请停止后重试；也可使用内置图片继续演示。")
    return cv2.flip(image, 1)
