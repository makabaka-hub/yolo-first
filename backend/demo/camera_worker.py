"""在独立进程中读取相机，驱动阻塞时允许主程序终止并回收设备。"""

from queue import Full


def capture_worker(index, backend, frames, stop):
    import cv2

    capture = None
    # 主程序停止取帧时，不等待队列中的旧帧发送完毕。
    frames.cancel_join_thread()
    try:
        capture = cv2.VideoCapture(index, getattr(cv2, backend))
        if not capture.isOpened():
            raise RuntimeError("设备未能打开，可能被其他程序占用。")
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while not stop.is_set():
            success, image = capture.read()
            if not success or image is None:
                raise RuntimeError("相机未能返回有效画面。")
            try:
                frames.put_nowait(("frame", image))
            except Full:
                pass
    except Exception as error:
        try:
            frames.put_nowait(("error", str(error)))
        except Full:
            pass
    finally:
        if capture is not None:
            capture.release()
