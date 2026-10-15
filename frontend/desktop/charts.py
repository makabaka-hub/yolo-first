"""用 Tk Canvas 绘制训练指标，坐标换算仅用于界面显示。"""

import tkinter as tk

from . import theme as t


class LineChart(tk.Canvas):
    def __init__(self, parent, fixed_max=None):
        super().__init__(parent, bg=t.CANVAS, highlightthickness=0)
        self.series = []
        self.epochs = 20
        self.fixed_max = fixed_max
        self.bind("<Configure>", lambda event: self.redraw())

    def update_series(self, series, epochs):
        self.series, self.epochs = series, max(1, epochs)
        self.redraw()

    def redraw(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 100 or height < 100:
            return
        left, top, right, bottom = 54, 25, width - 24, height - 65
        values = [value for _, _, points in self.series for _, value in points]
        maximum = self.fixed_max if self.fixed_max is not None else max(values + [1.0]) * 1.12
        for tick in range(5):
            y = bottom - (bottom - top) * tick / 4
            self.create_line(left, y, right, y, fill="#233247")
            self.create_text(left - 10, y, text=f"{maximum*tick/4:.2f}", anchor="e", fill=t.MUTED, font=(t.FONT, 9))
            x = left + (right - left) * tick / 4
            self.create_text(x, bottom + 18, text=str(round(self.epochs*tick/4)), fill=t.MUTED, font=(t.FONT, 9))
        self.create_text(right, bottom + 36, text="训练轮数 / epoch", fill=t.MUTED, font=(t.FONT, 9), anchor="e")
        for index, (name, color, points) in enumerate(self.series):
            coordinates = []
            for epoch, value in points:
                x = left + (right - left) * epoch / self.epochs
                y = bottom - (bottom - top) * value / maximum
                coordinates.extend((x, y))
            if len(coordinates) >= 4:
                self.create_line(*coordinates, fill=color, width=2)
            for offset in range(0, len(coordinates), 2):
                x, y = coordinates[offset:offset+2]
                self.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color)
            x = left + index * 145
            self.create_line(x, height-15, x+18, height-15, fill=color, width=3)
            self.create_text(x+25, height-15, text=name, fill=t.MUTED, font=(t.FONT, 9), anchor="w")
        if not values:
            self.create_text((left+right)//2, (top+bottom)//2, text="等待第一轮真实训练结果…", fill=t.MUTED, font=(t.FONT, 12))
