"""展示真实训练进度、曲线和日志，通过接口发起或停止训练。"""

import tkinter as tk
from tkinter import ttk

from common.training_view import TrainingSnapshot, TrainingViewPort

from . import theme as t
from .charts import LineChart


class TrainingWindow:
    def __init__(self, parent, port: TrainingViewPort, inbox):
        self.port, self.inbox = port, inbox
        self.closed, self.busy, self.fullscreen = False, False, False
        self.snapshot = None
        self.root = tk.Toplevel(parent)
        self.root.title("YOLO Vision · 训练过程")
        self.root.configure(bg=t.BG)
        width, height = min(1300, parent.winfo_screenwidth()-60), min(890, parent.winfo_screenheight()-70)
        self.root.geometry(f"{width}x{height}+50+45")
        self.root.minsize(1050, 750)
        header = tk.Frame(self.root, bg=t.BG)
        header.pack(fill="x", padx=24, pady=(20, 12))
        t.label(header, "训练过程", 23, bold=True).pack(side="left")
        self.phase_text = tk.StringVar(value="读取记录")
        tk.Label(header, textvariable=self.phase_text, bg=t.ACCENT_DARK, fg=t.ACCENT,
                 font=(t.FONT, 10), padx=13, pady=7).pack(side="left", padx=16)
        self.device_text = tk.StringVar(value="YOLO26n  /  COCO8")
        tk.Label(header, textvariable=self.device_text, bg=t.BG, fg=t.MUTED, font=(t.FONT, 10)).pack(side="right")
        t.label(self.root, "640 输入尺寸  ·  每批 4 张  ·  4 张训练图 + 4 张验证图  ·  小样本仅用于展示训练流程", 10, t.MUTED).pack(fill="x", padx=24, pady=(0, 14))
        toolbar = tk.Frame(self.root, bg=t.PANEL, padx=14, pady=10)
        toolbar.pack(fill="x", padx=24)
        t.label(toolbar, "本次训练轮数", 10).pack(side="left", padx=(0, 10))
        self.epochs = tk.StringVar(value="20")
        self.epoch_combo = ttk.Combobox(toolbar, textvariable=self.epochs, values=("5", "10", "20"),
                                       width=5, state="readonly", style="Demo.TCombobox", font=(t.FONT, 10))
        self.epoch_combo.pack(side="left", padx=(0, 15))
        self.start_button = t.button(toolbar, "开始实时训练", self.start, primary=True, small=True)
        self.start_button.pack(side="left", padx=(0, 10))
        self.stop_button = t.button(toolbar, "停止训练", self.stop, small=True)
        self.stop_button.pack(side="left")
        self.history_button = t.button(toolbar, "查看历史记录", self.port.history, small=True)
        self.history_button.pack(side="right")
        progress = tk.Frame(self.root, bg=t.BG)
        progress.pack(fill="x", padx=25, pady=(14, 12))
        self.progress_text = tk.StringVar(value="0 / 20 轮")
        tk.Label(progress, textvariable=self.progress_text, bg=t.BG, fg=t.TEXT,
                 font=(t.FONT, 12, "bold")).pack(side="left", padx=(0, 18))
        style = ttk.Style(self.root)
        style.configure("Demo.Horizontal.TProgressbar", troughcolor=t.PANEL, background=t.ACCENT, bordercolor=t.PANEL, lightcolor=t.ACCENT, darkcolor=t.ACCENT)
        self.progress = ttk.Progressbar(progress, maximum=20, style="Demo.Horizontal.TProgressbar")
        self.progress.pack(side="left", fill="x", expand=True)
        self.time_text = tk.StringVar(value="训练计时 —")
        tk.Label(progress, textvariable=self.time_text, bg=t.BG, fg=t.MUTED,
                 font=(t.FONT, 10)).pack(side="right", padx=(16, 0))
        cards = tk.Frame(self.root, bg=t.BG)
        cards.pack(fill="x", padx=20, pady=(0, 12))
        self.metric_values = []
        for index, caption in enumerate(("定位损失 / Box Loss", "分类损失 / Class Loss", "查准率 / Precision", "验证指标 / mAP50")):
            cards.columnconfigure(index, weight=1, uniform="metrics")
            card = tk.Frame(cards, bg=t.PANEL, padx=16, pady=9)
            card.grid(row=0, column=index, sticky="nsew", padx=5)
            t.label(card, caption, 9, t.MUTED).pack(anchor="w")
            value = tk.StringVar(value="—")
            tk.Label(card, textvariable=value, bg=t.PANEL, fg=t.ACCENT if index < 2 else t.TEXT,
                     font=(t.FONT, 23, "bold"), anchor="w").pack(fill="x")
            self.metric_values.append(value)
        plots = tk.Frame(self.root, bg=t.BG)
        plots.pack(fill="both", expand=True, padx=20)
        self.charts = []
        for index, title in enumerate(("训练损失   /   观察误差随轮数变化", "验证指标   /   在 4 张验证图上计算")):
            plots.columnconfigure(index, weight=1, uniform="charts")
            panel = tk.Frame(plots, bg=t.PANEL)
            panel.grid(row=0, column=index, sticky="nsew", padx=5)
            t.label(panel, title, 10, bold=True).pack(anchor="w", padx=15, pady=10)
            chart = LineChart(panel, fixed_max=1.0 if index else None)
            chart.pack(fill="both", expand=True, padx=7, pady=(0, 7))
            self.charts.append(chart)
        plots.rowconfigure(0, weight=1)
        log_frame = tk.Frame(self.root, bg=t.PANEL)
        log_frame.pack(fill="x", padx=24, pady=(12, 10))
        t.label(log_frame, "真实训练日志", 10, bold=True).pack(anchor="w", padx=12, pady=(8, 2))
        self.log = tk.Text(log_frame, height=4, bg=t.PANEL, fg=t.MUTED, relief="flat", bd=0,
                           font=(t.FONT, 9), wrap="word", padx=12, pady=4)
        self.log.pack(fill="x")
        self.log.configure(state="disabled")
        self.message = tk.StringVar(value="正在读取已有训练记录…")
        self.message_label = tk.Label(self.root, textvariable=self.message, bg=t.BG, fg=t.MUTED,
                                      font=(t.FONT, 9), anchor="w", wraplength=1180, justify="left")
        self.message_label.pack(fill="x", padx=24, pady=(0, 4))
        self.directory = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.directory, bg=t.BG, fg=t.MUTED, font=(t.FONT, 8),
                 anchor="w").pack(fill="x", padx=24, pady=(0, 12))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", lambda event: self.toggle_fullscreen() if self.fullscreen else None)
        self._controls()
        self.poll_job = self.root.after(80, self._poll)
        self.port.history()

    def _controls(self):
        self.start_button.configure(state="disabled" if self.busy else "normal")
        self.history_button.configure(state="disabled" if self.busy else "normal")
        self.epoch_combo.configure(state="disabled" if self.busy else "readonly")
        self.stop_button.configure(state="normal" if self.busy else "disabled")

    def start(self):
        if not self.busy:
            self.busy = True
            self.message.set("正在启动训练…")
            self._controls()
            self.port.start(int(self.epochs.get()))

    def stop(self):
        self.message.set("正在停止训练，请稍候…")
        self.port.stop()

    def _poll(self):
        if self.closed:
            return
        for event in self.inbox.drain():
            self.display(event.data["snapshot"])
        self.poll_job = self.root.after(100, self._poll)

    def display(self, snapshot: TrainingSnapshot):
        self.snapshot = snapshot
        self.busy = snapshot.phase in ("preparing", "running")
        titles = {"preparing": "准备训练", "running": "● 实时训练", "completed": "训练完成",
                  "history": "历史记录", "stopped": "训练已停止", "error": "训练失败"}
        self.phase_text.set(titles[snapshot.phase])
        self.device_text.set(f"YOLO26n  /  {snapshot.device}" if snapshot.device else "YOLO26n  /  COCO8")
        point = snapshot.points[-1] if snapshot.points else None
        current = point.epoch if point else 0
        self.progress_text.set(f"{current} / {snapshot.epochs} 轮")
        self.progress.configure(maximum=snapshot.epochs, value=current)
        self.time_text.set(f"训练计时 {point.seconds:.1f} 秒" if point else "训练计时 —")
        values = (f"{point.box_loss:.3f}", f"{point.cls_loss:.3f}", f"{point.precision:.1%}", f"{point.map50:.1%}") if point else ("—",) * 4
        for variable, value in zip(self.metric_values, values):
            variable.set(value)
        points = snapshot.points
        self.charts[0].update_series([
            ("定位损失", t.ACCENT, [(p.epoch, p.box_loss) for p in points]),
            ("分类损失", t.BLUE, [(p.epoch, p.cls_loss) for p in points]),
        ], snapshot.epochs)
        self.charts[1].update_series([
            ("mAP50", t.ACCENT, [(p.epoch, p.map50) for p in points]),
            ("Precision", t.BLUE, [(p.epoch, p.precision) for p in points]),
            ("Recall", "#f6ba70", [(p.epoch, p.recall) for p in points]),
        ], snapshot.epochs)
        self.message.set(snapshot.message)
        self.message_label.configure(fg=t.ERROR if snapshot.phase == "error" else t.MUTED)
        self.directory.set(f"记录目录：{snapshot.directory}" if snapshot.directory else "")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", snapshot.log or "选择开始实时训练后，这里显示训练进程的真实输出。")
        self.log.see("end")
        self.log.configure(state="disabled")
        self._controls()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.busy:
            self.port.stop()
        self.root.after_cancel(self.poll_job)
        self.root.destroy()
