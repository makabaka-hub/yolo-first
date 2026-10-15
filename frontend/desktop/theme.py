"""定义桌面窗口的颜色、字体和基础控件样式。"""

import tkinter as tk
from tkinter import ttk


BG = "#0b111b"
PANEL = "#121d2b"
CANVAS = "#080f19"
BORDER = "#263548"
TEXT = "#edf4ff"
MUTED = "#90a2bb"
ACCENT = "#58e0c4"
ACCENT_DARK = "#123f3b"
BLUE = "#79adff"
ERROR = "#ff8f99"
FONT = "Microsoft YaHei UI"


def label(parent, text="", size=10, color=TEXT, bold=False, **kwargs):
    return tk.Label(
        parent, text=text, bg=parent.cget("bg"), fg=color,
        font=(FONT, size, "bold" if bold else "normal"), anchor="w", **kwargs,
    )


def button(parent, text, command, primary=False, small=False):
    background = ACCENT if primary else "#1c2c40"
    foreground = BG if primary else TEXT
    widget = tk.Button(
        parent, text=text, command=command, bg=background, fg=foreground,
        activebackground="#87edda" if primary else "#2a405b", activeforeground=foreground,
        disabledforeground="#62758e", relief="flat", bd=0, cursor="hand2",
        font=(FONT, 9 if small else 10, "bold"), padx=10, pady=7 if small else 9,
        highlightthickness=0, takefocus=True,
    )
    return widget


def configure_ttk(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Demo.TCombobox", fieldbackground="#1c2c40", background=BORDER, foreground=TEXT,
                    arrowcolor=ACCENT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=6)
    style.map("Demo.TCombobox", fieldbackground=[("readonly", "#1c2c40"), ("disabled", PANEL)],
              foreground=[("readonly", TEXT), ("disabled", MUTED)], selectbackground=[("readonly", "#1c2c40")],
              selectforeground=[("readonly", TEXT)])
    style.configure("Demo.Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    borderwidth=0, bordercolor=PANEL, lightcolor=PANEL, darkcolor=PANEL,
                    rowheight=26, font=(FONT, 10))
    style.configure("Demo.Treeview.Heading", background="#1a2a3d", foreground=MUTED,
                    font=(FONT, 9), relief="flat", padding=5)
    style.map("Demo.Treeview", background=[("selected", ACCENT_DARK)], foreground=[("selected", ACCENT)])
    style.configure("Demo.Vertical.TScrollbar", background="#2b4158", troughcolor=PANEL,
                    bordercolor=PANEL, lightcolor=PANEL, darkcolor=PANEL, arrowcolor=MUTED, arrowsize=11)
    style.map("Demo.Vertical.TScrollbar", background=[("active", "#416078")])
    style.configure("Demo.Horizontal.TScale", background=ACCENT, troughcolor="#263b50",
                    bordercolor=PANEL, lightcolor=ACCENT, darkcolor=ACCENT, sliderlength=18)
    root.option_add("*TCombobox*Listbox.background", "#1c2c40")
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT_DARK)
