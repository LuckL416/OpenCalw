"""安装向导页面"""
import tkinter as tk
from tkinter import ttk
from ui.theme import get


class InstallPage:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=get("bg"))

        # 标题
        tk.Label(self.frame, text="安装向导", font=("TkDefaultFont", 16, "bold"),
                 bg=get("bg"), fg=get("fg")).pack(anchor="w", padx=30, pady=(25, 15))

        # 步骤指示器
        steps_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                              bd=1, highlightbackground=get("border"), highlightthickness=1)
        steps_card.pack(fill="x", padx=30, pady=(0, 15))

        self._steps = ["许可声明", "环境检测", "安装 OpenClaw", "初始化配置", "部署完成"]
        stepper = tk.Frame(steps_card, bg=get("card_bg"))
        stepper.pack(padx=25, pady=20)

        self._step_widgets = []
        for i, name in enumerate(self._steps):
            w = tk.Frame(stepper, bg=get("card_bg"))
            w.pack(side="left", padx=4)

            circle = tk.Canvas(w, width=32, height=32, highlightthickness=0, bg=get("card_bg"))
            circle.create_oval(2, 2, 30, 30, fill=get("card_bg"), outline=get("border"), width=2)
            circle.create_text(16, 16, text=str(i + 1), fill=get("fg_muted"), font=("TkDefaultFont", 10, "bold"))
            circle.pack()
            self._step_widgets.append(circle)

            tk.Label(w, text=name, font=("TkDefaultFont", 8), bg=get("card_bg"),
                     fg=get("fg_muted")).pack(pady=(4, 0))

            if i < len(self._steps) - 1:
                tk.Label(stepper, text="─────", font=("TkDefaultFont", 6),
                         bg=get("card_bg"), fg=get("border")).pack(side="left", padx=2)

        # 进度条
        prog_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                             bd=1, highlightbackground=get("border"), highlightthickness=1)
        prog_card.pack(fill="x", padx=30, pady=(0, 15))
        prog_inner = tk.Frame(prog_card, bg=get("card_bg"))
        prog_inner.pack(fill="x", padx=25, pady=15)

        tk.Label(prog_inner, text="安装进度", font=("TkDefaultFont", 10, "bold"),
                 bg=get("card_bg"), fg=get("fg")).pack(anchor="w")
        pf = tk.Frame(prog_inner, bg=get("card_bg"))
        pf.pack(fill="x", pady=(8, 0))
        self._progress = ttk.Progressbar(pf, length=550, mode="determinate", value=0)
        self._progress.pack(side="left")
        self._progress_label = tk.Label(pf, text="  0%", font=("TkDefaultFont", 11, "bold"),
                                        bg=get("card_bg"), fg=get("accent"))
        self._progress_label.pack(side="left", padx=10)

        # 说明文字
        info_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                             bd=1, highlightbackground=get("border"), highlightthickness=1)
        info_card.pack(fill="x", padx=30, pady=(0, 15))
        tk.Label(info_card,
                 text="1. 自动检测 Node.js 环境   |   2. 配置淘宝镜像   |   3. 安装 OpenClaw   |   4. 初始化配置",
                 font=("TkDefaultFont", 9), bg=get("card_bg"), fg=get("fg_secondary"),
                 justify="left").pack(anchor="w", padx=20, pady=12)
        tk.Label(info_card,
                 text="⚠ 需要管理员权限   |   安装完成后请到「配置」页面设置 API 密钥",
                 font=("TkDefaultFont", 9), bg=get("card_bg"), fg=get("warning")).pack(anchor="w", padx=20, pady=(0, 12))

        # 按钮
        btn_row = tk.Frame(self.frame, bg=get("bg"))
        btn_row.pack(fill="x", padx=30)
        self._install_btn = tk.Button(btn_row, text="▶  开始安装", command=app.start_install,
                                      bg=get("accent"), fg=get("accent_fg"), font=("TkDefaultFont", 11, "bold"),
                                      relief="flat", padx=24, pady=10, bd=0, cursor="hand2",
                                      activebackground=get("accent_hover"))
        self._install_btn.pack(side="left", padx=(0, 8))

        bs = {"bg": get("card_bg"), "fg": get("fg"), "font": ("TkDefaultFont", 9),
              "relief": "solid", "bd": 1, "padx": 14, "pady": 6, "cursor": "hand2"}
        tk.Button(btn_row, text="彻底卸载", command=app.uninstall, **bs).pack(side="left", padx=4)
        tk.Button(btn_row, text="重置环境", command=app.reset_env, **bs).pack(side="left", padx=4)

    def set_progress(self, pct: int):
        self._progress.config(value=pct)
        self._progress_label.config(text=f"  {pct}%")

    def update_step(self, step: int):
        for i, c in enumerate(self._step_widgets):
            c.delete("all")
            if i == step:
                c.create_oval(2, 2, 30, 30, fill=get("accent"), outline=get("accent"), width=2)
                c.create_text(16, 16, text=str(i + 1), fill="#ffffff", font=("TkDefaultFont", 10, "bold"))
            elif i < step:
                c.create_oval(2, 2, 30, 30, fill=get("success"), outline=get("success"), width=2)
                c.create_text(16, 16, text="✓", fill="#ffffff", font=("TkDefaultFont", 10, "bold"))
            else:
                c.create_oval(2, 2, 30, 30, fill=get("card_bg"), outline=get("border"), width=2)
                c.create_text(16, 16, text=str(i + 1), fill=get("fg_muted"), font=("TkDefaultFont", 10, "bold"))

    def set_busy(self, busy: bool):
        self._install_btn.config(state="disabled" if busy else "normal")

    def reset(self):
        self.set_progress(0)
        self.update_step(0)

    def on_theme_change(self):
        pass
