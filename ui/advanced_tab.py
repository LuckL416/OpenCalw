"""高级设置 Tab"""
import tkinter as tk
from tkinter import ttk
from ui.widgets import SettingsRow


class AdvancedTab:
    def __init__(self, parent, callbacks: dict):
        self.cb = callbacks
        self.frame = parent

        outer = ttk.Frame(self.frame)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # 区域与语言
        section1 = ttk.LabelFrame(outer, text="区域与语言", style="Card.TLabelframe")
        section1.pack(fill="x", pady=(0, 12))
        grid1 = ttk.Frame(section1, style="Card.TFrame")
        grid1.pack(fill="x", padx=15, pady=10)

        r = 0
        self.timezone_var = tk.StringVar(value="Asia/Shanghai")
        r = SettingsRow.grid(grid1, r, "时区", ttk.Entry(grid1, textvariable=self.timezone_var, width=24, font=("", 10)),
                            extra=[ttk.Label(grid1, text="默认 Asia/Shanghai", style="Muted.TLabel")])

        self.lang_var = tk.StringVar(value="zh-CN")
        r = SettingsRow.grid(grid1, r, "语言",
                            ttk.Combobox(grid1, textvariable=self.lang_var, values=["zh-CN", "en-US"],
                                         state="readonly", width=22, font=("", 10)))

        # 日志行为
        section2 = ttk.LabelFrame(outer, text="日志行为", style="Card.TLabelframe")
        section2.pack(fill="x", pady=(0, 12))
        grid2 = ttk.Frame(section2, style="Card.TFrame")
        grid2.pack(fill="x", padx=15, pady=10)

        self.verbose_var = tk.BooleanVar(value=False)
        self.silent_var = tk.BooleanVar(value=False)
        r2 = 0
        r2 = SettingsRow.grid(grid2, r2, "详细输出", ttk.Checkbutton(grid2, text="启用 verbose 模式",
                              variable=self.verbose_var))
        r2 = SettingsRow.grid(grid2, r2, "静默模式", ttk.Checkbutton(grid2, text="启用 silent 模式",
                              variable=self.silent_var))

        # 保存
        ttk.Button(outer, text="保存所有高级设置", command=lambda: self.cb.get("save", lambda: None)(),
                   style="Accent.TButton").pack(anchor="w", pady=(0, 10))

    def get_values(self) -> dict:
        return {
            "timezone": self.timezone_var.get(),
            "language": self.lang_var.get(),
            "verbose": self.verbose_var.get(),
            "silent": self.silent_var.get()
        }

    def reset(self):
        self.timezone_var.set("Asia/Shanghai")
        self.lang_var.set("zh-CN")
        self.verbose_var.set(False)
        self.silent_var.set(False)
