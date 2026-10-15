"""组织桌面演示界面，在 Tk 主线程消费事件并渲染后端结果。"""

import io
import tkinter as tk
from collections import Counter
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageOps, ImageTk

from common.demo import DemoFrame, DemoModel, DemoOptions, DemoPort
from common.labels import display_label

from . import theme as t
from .bridge import DesktopInbox


class DemoWindow:
    def __init__(self, root, port: DemoPort, inbox: DesktopInbox, models: tuple[DemoModel, ...], samples: dict[str, str]):
        self.root, self.port, self.inbox = root, port, inbox
        self.models, self.samples = models, samples
        self.frame: DemoFrame | None = None
        self.current_image = None
        self.photo = None
        self.ready = False
        self.busy = True
        self.streaming = False
        self.opening_camera = False
        self.closed = False
        self.fullscreen = False
        self.show_original = False
        self.threshold_job = None
        self.resize_job = None
        root.title("YOLO Vision · 目标检测演示")
        icon = Path(__file__).resolve().parents[2] / "demo_assets" / "icon.ico"
        if icon.is_file():
            root.iconbitmap(str(icon))
        root.configure(bg=t.BG)
        width, height = min(1500, root.winfo_screenwidth() - 70), min(940, root.winfo_screenheight() - 90)
        root.geometry(f"{width}x{height}+{max(0, (root.winfo_screenwidth()-width)//2)}+{max(0, (root.winfo_screenheight()-height)//2)}")
        root.minsize(1120, 790)
        t.configure_ttk(root)
        self._header()
        self._footer()
        body = tk.Frame(root, bg=t.BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        self._sidebar(body)
        self._viewer(body)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<F11>", lambda event: self.toggle_fullscreen())
        root.bind("<Escape>", self.escape)
        root.bind("<Control-o>", lambda event: self.choose_image())
        root.bind("<Control-s>", lambda event: self.save())
        self.poll_job = root.after(35, self._poll)

    def _header(self):
        header = tk.Frame(self.root, bg=t.BG)
        header.pack(fill="x", padx=26, pady=(21, 18))
        identity = tk.Frame(header, bg=t.BG)
        identity.pack(side="left")
        title = tk.Frame(identity, bg=t.BG)
        title.pack(anchor="w")
        t.label(title, "[  ]", 22, t.ACCENT, True).pack(side="left", padx=(0, 12))
        t.label(title, "YOLO", 25, t.TEXT, True).pack(side="left")
        t.label(title, "  VISION", 25, t.MUTED).pack(side="left")
        t.label(identity, "目标检测演示   /   图片识别与实时视觉", 10, t.MUTED).pack(anchor="w", pady=(3, 0))
        t.button(header, "全屏演示  F11", self.toggle_fullscreen, small=True).pack(side="right", padx=(14, 0))
        self.device_text = tk.StringVar(value="●  正在准备模型")
        tk.Label(header, textvariable=self.device_text, bg=t.ACCENT_DARK, fg=t.ACCENT,
                 font=(t.FONT, 10), padx=14, pady=9).pack(side="right")

    def _footer(self):
        footer = tk.Frame(self.root, bg=t.BG, height=45)
        footer.pack(side="bottom", fill="x", padx=26, pady=(0, 10))
        self.status_text = tk.StringVar(value="正在准备模型，首次加载需要几秒钟…")
        self.status_label = tk.Label(footer, textvariable=self.status_text, bg=t.BG, fg=t.MUTED,
                                     font=(t.FONT, 9), anchor="w", wraplength=970, justify="left")
        self.status_label.pack(side="left", fill="x", expand=True)
        t.label(footer, "Ctrl+O 选图  ·  F11 全屏  ·  Esc 停止", 9, t.MUTED).pack(side="right", padx=(10, 0))

    def _sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=t.PANEL, width=292, highlightbackground=t.BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)
        content = tk.Frame(sidebar, bg=t.PANEL)
        content.pack(fill="both", expand=True, padx=19, pady=18)
        t.label(content, "演示控制", 14, bold=True).pack(anchor="w", pady=(0, 14))
        self.image_button = t.button(content, "选择图片", self.choose_image, primary=True)
        self.image_button.pack(fill="x")
        camera_row = tk.Frame(content, bg=t.PANEL)
        camera_row.pack(fill="x", pady=(8, 8))
        self.camera_button = t.button(camera_row, "打开摄像头", self.start_camera)
        self.camera_button.pack(side="left", fill="x", expand=True)
        self.camera_index = tk.StringVar(value="0")
        self.camera_combo = ttk.Combobox(camera_row, textvariable=self.camera_index, values=("0", "1", "2"),
                                          width=2, state="readonly", style="Demo.TCombobox", font=(t.FONT, 10))
        self.camera_combo.pack(side="left", padx=(7, 0), ipady=4)
        action_row = tk.Frame(content, bg=t.PANEL)
        action_row.pack(fill="x")
        self.stop_button = t.button(action_row, "停止", self.stop, small=True)
        self.stop_button.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.save_button = t.button(action_row, "保存结果", self.save, small=True)
        self.save_button.pack(side="left", fill="x", expand=True)
        self._divider(content)
        t.label(content, "识别模型", 9, t.MUTED).pack(anchor="w", pady=(0, 4))
        self.model_index = tk.StringVar(value=self.models[0].title)
        self.model_combo = ttk.Combobox(content, textvariable=self.model_index,
                                         values=[model.title for model in self.models], state="readonly",
                                         style="Demo.TCombobox", font=(t.FONT, 10))
        self.model_combo.pack(fill="x")
        self.model_combo.bind("<<ComboboxSelected>>", self.change_model)
        self.model_note = tk.StringVar(value=self.models[0].note)
        tk.Label(content, textvariable=self.model_note, bg=t.PANEL, fg=t.MUTED, font=(t.FONT, 9),
                 wraplength=244, justify="left", anchor="w").pack(fill="x", pady=(7, 11))
        threshold_row = tk.Frame(content, bg=t.PANEL)
        threshold_row.pack(fill="x")
        t.label(threshold_row, "置信度阈值", 10).pack(side="left")
        self.threshold_text = tk.StringVar(value="35%")
        tk.Label(threshold_row, textvariable=self.threshold_text, bg=t.PANEL, fg=t.ACCENT,
                 font=(t.FONT, 12, "bold")).pack(side="right")
        self.threshold = tk.DoubleVar(value=0.35)
        self.threshold.trace_add("write", self.change_threshold)
        self.scale = ttk.Scale(content, variable=self.threshold, from_=0.1, to=0.9,
                               orient="horizontal", style="Demo.Horizontal.TScale")
        self.scale.pack(fill="x", pady=(8, 4))
        t.label(content, "阈值越高，筛选越严格", 9, t.MUTED).pack(anchor="w", pady=(0, 13))
        t.label(content, "内置演示图", 9, t.MUTED).pack(anchor="w", pady=(0, 6))
        sample_row = tk.Frame(content, bg=t.PANEL)
        sample_row.pack(fill="x")
        self.sample_buttons = []
        for index, (name, source) in enumerate(self.samples.items()):
            widget = t.button(sample_row, name, lambda path=source: self.select_image(path), small=True)
            widget.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 6, 0))
            self.sample_buttons.append(widget)
        self._divider(content)
        t.label(content, "识别明细", 11, bold=True).pack(anchor="w", pady=(0, 8))
        table_frame = tk.Frame(content, bg=t.PANEL)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_frame, columns=("name", "confidence"), show="headings", height=3, style="Demo.Treeview")
        self.table.heading("name", text="目标")
        self.table.heading("confidence", text="置信度")
        self.table.column("name", width=137, minwidth=80, anchor="w")
        self.table.column("confidence", width=73, minwidth=65, anchor="e")
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview, style="Demo.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)
        self._set_controls()

    def _divider(self, parent):
        tk.Frame(parent, bg=t.BORDER, height=1).pack(fill="x", pady=(15, 13))

    def _viewer(self, parent):
        right = tk.Frame(parent, bg=t.BG)
        right.pack(side="left", fill="both", expand=True)
        metrics = tk.Frame(right, bg=t.BG)
        metrics.pack(side="bottom", fill="x", pady=(14, 0))
        self.metric_values = []
        for index, (title, value) in enumerate((("检测目标", "—"), ("目标类别", "—"), ("推理耗时 / ms", "—"), ("处理帧率 / FPS", "—"))):
            metrics.columnconfigure(index, weight=1, uniform="statistics")
            card = tk.Frame(metrics, bg=t.PANEL, highlightbackground=t.BORDER, highlightthickness=1)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 10, 0))
            t.label(card, title, 9, t.MUTED).pack(anchor="w", padx=18, pady=(12, 0))
            variable = tk.StringVar(value=value)
            tk.Label(card, textvariable=variable, bg=t.PANEL, fg=t.ACCENT if index == 0 else t.TEXT,
                     font=(t.FONT, 25, "bold"), anchor="w").pack(fill="x", padx=18, pady=(0, 10))
            self.metric_values.append(variable)
        panel = tk.Frame(right, bg=t.PANEL, highlightbackground=t.BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True)
        heading = tk.Frame(panel, bg=t.PANEL)
        heading.pack(fill="x", padx=18, pady=12)
        t.label(heading, "检测画面", 12, bold=True).pack(side="left")
        self.mode_text = tk.StringVar(value="准备中")
        tk.Label(heading, textvariable=self.mode_text, bg=t.ACCENT_DARK, fg=t.ACCENT,
                 font=(t.FONT, 9), padx=9, pady=3).pack(side="left", padx=12)
        self.original_button = t.button(heading, "查看原图", self.toggle_original, small=True)
        self.original_button.pack(side="right")
        self.canvas = tk.Canvas(panel, bg=t.CANVAS, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=12)
        self.canvas.bind("<Configure>", self._schedule_redraw)
        caption = tk.Frame(panel, bg=t.PANEL)
        caption.pack(fill="x", padx=18, pady=10)
        self.source_text = tk.StringVar(value="本地模型加载中，即将显示内置演示图")
        tk.Label(caption, textvariable=self.source_text, bg=t.PANEL, fg=t.MUTED,
                 font=(t.FONT, 9), anchor="w").pack(side="left", fill="x", expand=True)
        t.label(caption, "LOCAL INFERENCE", 9, t.MUTED).pack(side="right")

    def options(self):
        selected = next(model for model in self.models if model.title == self.model_index.get())
        return DemoOptions(selected.weights, round(self.threshold.get(), 2))

    def _set_controls(self):
        available = self.ready and not self.busy
        for widget in (self.image_button, self.camera_button, *self.sample_buttons):
            widget.configure(state="normal" if available else "disabled")
        self.model_combo.configure(state="readonly" if available else "disabled")
        self.scale.configure(state="normal" if available else "disabled")
        self.camera_combo.configure(state="readonly" if available and not self.streaming else "disabled")
        self.stop_button.configure(state="normal" if self.streaming or self.opening_camera else "disabled")
        self.save_button.configure(state="normal" if self.frame is not None else "disabled")

    def choose_image(self):
        if not self.ready or self.busy:
            return
        source = filedialog.askopenfilename(parent=self.root, title="选择要识别的图片", filetypes=[
            ("图片", "*.jpg *.jpeg *.png *.bmp *.webp"), ("所有文件", "*.*"),
        ])
        if source:
            self.select_image(source)

    def select_image(self, source):
        if self.ready and not self.busy:
            self.busy = True
            self._set_controls()
            self.port.image(source, self.options())

    def start_camera(self):
        if self.ready and not self.busy:
            self.opening_camera = True
            self.busy = True
            self._set_controls()
            self.port.camera(int(self.camera_index.get()), self.options())

    def stop(self):
        self.port.stop()

    def change_model(self, event=None):
        selected = next(model for model in self.models if model.title == self.model_index.get())
        self.model_note.set(selected.note)
        self._configure()

    def change_threshold(self, *args):
        self.threshold_text.set(f"{self.threshold.get():.0%}")
        if self.threshold_job is not None:
            self.root.after_cancel(self.threshold_job)
        self.threshold_job = self.root.after(260, self._configure)

    def _configure(self):
        self.threshold_job = None
        if self.ready and not self.busy:
            self.busy = True
            self._set_controls()
            self.port.configure(self.options())

    def save(self):
        if self.frame is None:
            return
        snapshot = self.frame
        destination = filedialog.asksaveasfilename(
            parent=self.root, title="保存识别画面与检测明细", defaultextension=".jpg",
            initialfile=f"YOLO_{datetime.now():%Y%m%d_%H%M%S}.jpg",
            filetypes=[("JPEG 图片", "*.jpg"), ("PNG 图片", "*.png")],
        )
        if destination:
            self.port.save(destination, snapshot)

    def toggle_original(self):
        self.show_original = not self.show_original
        self.original_button.configure(text="查看识别" if self.show_original else "查看原图")
        if self.frame is not None:
            self._decode_frame()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def escape(self, event=None):
        if self.fullscreen:
            self.toggle_fullscreen()
        elif self.streaming or self.opening_camera:
            self.stop()

    def _poll(self):
        if self.closed:
            return
        for event in self.inbox.drain():
            data = event.data
            if event.name == "demo_ready":
                self.ready = True
                device = data["device"].replace("NVIDIA GeForce ", "")
                self.device_text.set(f"●  {device}")
            elif event.name == "demo_state":
                self.busy = data["phase"] in ("loading", "working")
                self.streaming = data["phase"] == "streaming"
                if data["phase"] in ("idle", "streaming"):
                    self.opening_camera = False
                self.status_text.set(data["message"])
                self.status_label.configure(fg=t.MUTED)
                if data["phase"] == "loading":
                    self.mode_text.set("模型加载中")
                elif self.streaming:
                    self.mode_text.set("● 实时识别")
                elif data["phase"] == "idle" and self.frame is not None and self.frame.mode == "camera":
                    self.mode_text.set("画面已暂停")
                    self.metric_values[3].set("—")
            elif event.name == "demo_frame":
                self._on_frame(data["frame"])
            elif event.name == "demo_error":
                self.busy, self.streaming = False, False
                self.opening_camera = False
                self.status_text.set(data["message"])
                self.status_label.configure(fg=t.ERROR)
                self.mode_text.set("请检查输入")
            elif event.name == "demo_saved":
                self.status_text.set(f"已保存图片及同名 JSON 明细：{data['path']}")
                self.status_label.configure(fg=t.ACCENT)
        self._set_controls()
        self.poll_job = self.root.after(35, self._poll)

    def _on_frame(self, frame: DemoFrame):
        self.frame = frame
        self.mode_text.set(("● 实时识别" if self.streaming else "画面已暂停") if frame.mode == "camera" else "图片识别")
        self.source_text.set(f"{frame.source}   ·   {frame.width} × {frame.height}   ·   {frame.model}")
        values = (
            str(len(frame.detections)), str(len({detection.name for detection in frame.detections})),
            f"{frame.inference_ms:.1f}", f"{frame.processing_fps:.1f}" if frame.mode == "camera" and self.streaming else "—",
        )
        for variable, value in zip(self.metric_values, values):
            variable.set(value)
        self.table.delete(*self.table.get_children())
        for detection in frame.detections:
            self.table.insert("", "end", values=(display_label(detection.name), f"{detection.confidence:.1%}"))
        if not frame.detections:
            self.table.insert("", "end", values=("暂无目标", "—"))
        self._decode_frame()

    def _decode_frame(self):
        payload = self.frame.original_jpeg if self.show_original else self.frame.annotated_jpeg
        with Image.open(io.BytesIO(payload)) as image:
            self.current_image = image.convert("RGB")
        self._redraw()

    def _schedule_redraw(self, event=None):
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(60, self._redraw)

    def _redraw(self):
        self.resize_job = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 30 or height < 30:
            return
        self.canvas.delete("all")
        if self.current_image is not None:
            filter_mode = Image.Resampling.BILINEAR if self.streaming else Image.Resampling.LANCZOS
            image = ImageOps.contain(self.current_image, (width - 28, height - 28), method=filter_mode)
            self.photo = ImageTk.PhotoImage(image, master=self.root)
            self.canvas.create_image(width // 2, height // 2, image=self.photo, anchor="center")
        else:
            for x in range(0, width, 48):
                self.canvas.create_line(x, 0, x, height, fill="#101d2c")
            for y in range(0, height, 48):
                self.canvas.create_line(0, y, width, y, fill="#101d2c")
            self.canvas.create_text(width // 2, height // 2 - 20, text="视觉引擎准备中", fill=t.TEXT, font=(t.FONT, 22, "bold"))
            self.canvas.create_text(width // 2, height // 2 + 25, text="即将载入内置图片，摄像头由你手动开启", fill=t.MUTED, font=(t.FONT, 11))
        for x, y, dx, dy in ((9, 9, 1, 1), (width-9, 9, -1, 1), (9, height-9, 1, -1), (width-9, height-9, -1, -1)):
            self.canvas.create_line(x, y+dy*18, x, y, x+dx*18, y, fill=t.ACCENT, width=2)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.port.close()
        for job in (self.poll_job, self.threshold_job, self.resize_job):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()
