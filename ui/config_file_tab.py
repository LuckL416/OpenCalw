"""配置文件管理 Tab"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from ui.theme import get, is_dark

_LOG_BG_LIGHT = "#263238"
_LOG_BG_DARK = "#0d1117"


class ConfigFileTab:
    def __init__(self, parent, callbacks: dict):
        self.cb = callbacks
        self.frame = parent

        outer = ttk.Frame(self.frame)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # 路径栏
        path_card = ttk.LabelFrame(outer, text="配置文件", style="Card.TLabelframe")
        path_card.pack(fill="x", pady=(0, 12))
        path_row = ttk.Frame(path_card, style="Card.TFrame")
        path_row.pack(fill="x", padx=15, pady=10)

        self.path_label = ttk.Label(path_row, text="未获取", foreground=get("accent"), font=("", 10))
        self.path_label.pack(side="left", padx=5)
        ttk.Button(path_row, text="获取路径", command=lambda: self.cb.get("get_path", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(path_row, text="打开文件", command=lambda: self.cb.get("edit", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(path_row, text="打开文件夹", command=lambda: self.cb.get("open_folder", lambda: None)()).pack(
            side="left", padx=3)

        # 预览
        preview_card = ttk.LabelFrame(outer, text="内容预览", style="Card.TLabelframe")
        preview_card.pack(fill="both", expand=True, pady=(0, 12))

        bg = _LOG_BG_DARK if is_dark() else _LOG_BG_LIGHT
        fg = "#e6edf3" if is_dark() else "#eceff1"
        self.preview_text = scrolledtext.ScrolledText(preview_card, font=("Consolas", 9),
                                                       state="disabled", bg=bg, fg=fg,
                                                       insertbackground=get("accent"))
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 操作按钮
        btn_row = ttk.Frame(outer)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="刷新预览", command=lambda: self.cb.get("refresh_preview", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(btn_row, text="备份", command=lambda: self.cb.get("backup", lambda: None)(),
                   style="Accent.TButton").pack(side="left", padx=3)
        ttk.Button(btn_row, text="还原", command=lambda: self.cb.get("restore", lambda: None)()).pack(
            side="left", padx=3)

    def set_path(self, path: str):
        self.path_label.config(text=path)

    def set_preview(self, content: str):
        self.preview_text.config(state="normal")
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, content)
        self.preview_text.config(state="disabled")

    def apply_theme(self, dark: bool):
        bg = _LOG_BG_DARK if dark else _LOG_BG_LIGHT
        fg = "#e6edf3" if dark else "#eceff1"
        self.preview_text.configure(bg=bg, fg=fg)
