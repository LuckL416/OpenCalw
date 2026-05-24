"""安装向导 Tab"""
import tkinter as tk
from tkinter import ttk
from ui.theme import get


class InstallWizardTab:
    def __init__(self, parent, callbacks: dict):
        self.cb = callbacks
        self.frame = parent

        outer = ttk.Frame(self.frame)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # 编号步骤指示器
        self._steps = ["许可声明", "环境检测", "安装 OpenClaw", "初始化配置", "部署完成"]
        stepper_card = ttk.LabelFrame(outer, text="安装进度", style="Card.TLabelframe")
        stepper_card.pack(fill="x", pady=(0, 12))

        stepper = ttk.Frame(stepper_card, style="Card.TFrame")
        stepper.pack(fill="x", padx=20, pady=15)

        self._step_widgets = []
        for idx, name in enumerate(self._steps):
            wrapper = ttk.Frame(stepper, style="Card.TFrame")
            wrapper.pack(side="left", padx=3)

            num_label = tk.Label(wrapper, text=str(idx + 1), font=("", 10, "bold"),
                                 width=3, height=1, relief="solid", bd=2,
                                 bg=get("card_bg"), fg=get("muted"))
            num_label.pack()
            name_label = ttk.Label(wrapper, text=name, font=("", 8))
            name_label.pack(pady=(2, 0))
            self._step_widgets.append((num_label, name_label))

            if idx < len(self._steps) - 1:
                sep = ttk.Label(stepper, text="────", font=("", 5), foreground=get("muted"))
                sep.pack(side="left", padx=1)

        # 说明 + 进度
        content = ttk.LabelFrame(outer, text="安装说明", style="Card.TLabelframe")
        content.pack(fill="both", expand=True, pady=(0, 12))

        desc = tk.Text(content, height=8, font=("", 10), wrap="word", state="disabled",
                       bg=get("card_bg"), fg=get("fg"), relief="flat", borderwidth=0)
        desc.insert(tk.END, """【OpenClaw 安装向导说明】
1. 自动检测 Node.js 环境（需 18.x LTS 版本）
2. 自动配置淘宝镜像，解决网络问题
3. 自动安装最新版 OpenClaw
4. 自动解析 ~ 路径为 Windows 真实路径
5. 全程无需手动敲命令

⚠️ 安装需要管理员权限 | 完成后请先查看配置文件确认键名""")
        desc.pack(fill="x", padx=15, pady=10)

        # 进度条
        prog_frame = ttk.Frame(content, style="Card.TFrame")
        prog_frame.pack(fill="x", padx=15, pady=(0, 10))
        ttk.Label(prog_frame, text="进度", font=("", 9)).pack(side="left")
        self.progress_bar = ttk.Progressbar(prog_frame, orient="horizontal", length=500,
                                            mode="determinate", value=0)
        self.progress_bar.pack(side="left", padx=10)
        self.progress_label = ttk.Label(prog_frame, text="0%", font=("", 10, "bold"))
        self.progress_label.pack(side="left", padx=5)

        # 按钮
        btn_row = ttk.Frame(outer)
        btn_row.pack(fill="x")
        self.start_btn = ttk.Button(btn_row, text="▶  安装 OpenClaw",
                                     command=lambda: self.cb.get("start_install", lambda: None)(),
                                     style="Accent.TButton")
        self.start_btn.pack(side="left", padx=3)
        ttk.Button(btn_row, text="彻底卸载", command=lambda: self.cb.get("uninstall", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(btn_row, text="重置环境", command=lambda: self.cb.get("reset_env", lambda: None)()).pack(
            side="left", padx=3)

        self.update_step(0)

    def set_progress(self, percent: int):
        self.progress_bar.config(value=percent)
        self.progress_label.config(text=f"{percent}%")

    def update_step(self, step: int):
        for idx, (num_label, name_label) in enumerate(self._step_widgets):
            if idx == step:
                num_label.config(bg=get("accent"), fg=get("accent_fg"), relief="solid")
                name_label.config(foreground=get("accent"))
            elif idx < step:
                num_label.config(bg=get("success"), fg="white", relief="solid")
                name_label.config(foreground=get("success"))
            else:
                num_label.config(bg=get("card_bg"), fg=get("muted"), relief="ridge")
                name_label.config(foreground=get("muted"))

    def set_busy(self, busy: bool):
        self.start_btn.config(state="disabled" if busy else "normal")

    def reset(self):
        self.update_step(0)
        self.set_progress(0)
