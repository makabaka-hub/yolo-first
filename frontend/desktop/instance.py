"""保持单个 Windows 演示窗口，重复启动时唤起已有窗口。"""

import os


class DesktopInstance:
    def __init__(self, name="Local\\YOLOVisionDesktop"):
        self.name = name
        self.handle = None
        self.acquired = True

    def __enter__(self):
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
            self.kernel.CreateMutexW.restype = wintypes.HANDLE
            self.kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
            self.handle = self.kernel.CreateMutexW(None, False, self.name)
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.acquired = ctypes.get_last_error() != 183
        return self

    def __exit__(self, *args):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def focus_existing_window():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        user = ctypes.WinDLL("user32", use_last_error=True)
        user.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
        user.FindWindowW.restype = wintypes.HWND
        user.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
        user.SetForegroundWindow.argtypes = (wintypes.HWND,)
        handle = user.FindWindowW(None, "YOLO Vision · 目标检测演示")
        if handle:
            user.ShowWindow(handle, 9)
            user.SetForegroundWindow(handle)
