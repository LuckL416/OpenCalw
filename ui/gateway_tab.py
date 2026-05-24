"""Gateway 控制 Tab"""
import tkinter as tk
from tkinter import ttk
from ui.theme import get


class GatewayTab:
    def __init__(self, parent, callbacks: dict):
        self.cb = callbacks
        self.frame = parent
        self._running = False

        outer = ttk.Frame(self.frame)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # ---- 状态卡片 ----
        card = ttk.LabelFrame(outer, text="Gateway 运行状态", style="Card.TLabelframe")
        card.pack(fill="x", pady=(0, 12))
        inner = ttk.Frame(card, style="Card.TFrame")
        inner.pack(fill="x", padx=20, pady=15)

        # 状态指示器（大号）
        status_row = ttk.Frame(inner, style="Card.TFrame")
        status_row.pack(fill="x")

        self.status_canvas = tk.Canvas(status_row, width=18, height=18, highlightthickness=0, bg=get("card_bg"))
        self.status_canvas.pack(side="left")
        self._status_dot = self.status_canvas.create_oval(2, 2, 16, 16, fill="#D32F2F", outline="")

        self.status_display = ttk.Label(status_row, text="已停止", font=("", 14, "bold"))
        self.status_display.pack(side="left", padx=10)

        # 端口和 URL
        info_row = ttk.Frame(inner, style="Card.TFrame")
        info_row.pack(fill="x", pady=(8, 0))

        ttk.Label(info_row, text="端口", font=("", 9), style="Muted.TLabel").pack(side="left")
        self.port_var = tk.StringVar(value="18789")
        port_entry = ttk.Entry(info_row, textvariable=self.port_var, width=8, font=("", 12, "bold"))
        port_entry.pack(side="left", padx=5)
        port_entry.bind("<Return>", lambda e: self._apply_port())

        ttk.Button(info_row, text="应用", command=self._apply_port, width=5).pack(side="left", padx=2)

        ttk.Label(info_row, text="Dashboard", font=("", 9), style="Muted.TLabel").pack(side="left", padx=(30, 5))
        self.url_display = ttk.Label(info_row, text="未获取", foreground=get("accent"), cursor="hand2",
                                     font=("", 10))
        self.url_display.pack(side="left", padx=5)
        self.url_display.bind("<Button-1>", lambda e: self.cb.get("get_dashboard_url", lambda: None)())

        ttk.Button(info_row, text="打开 ▸", command=lambda: self.cb.get("open_dashboard", lambda: None)(),
                   width=7).pack(side="left", padx=5)

        # ---- 控制按钮组 ----
        btn_card = ttk.LabelFrame(outer, text="操作", style="Card.TLabelframe")
        btn_card.pack(fill="x", pady=(0, 12))
        btn_row = ttk.Frame(btn_card, style="Card.TFrame")
        btn_row.pack(fill="x", padx=20, pady=15)

        self.start_btn = ttk.Button(btn_row, text="▶  启动",
                                     command=lambda: self.cb.get("start", lambda: None)(),
                                     style="Accent.TButton", state="disabled")
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = ttk.Button(btn_row, text="■  停止",
                                    command=lambda: self.cb.get("stop", lambda: None)(),
                                    style="Danger.TButton", state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.restart_btn = ttk.Button(btn_row, text="↻  重启",
                                       command=lambda: self.cb.get("restart", lambda: None)(),
                                       state="disabled")
        self.restart_btn.pack(side="left", padx=4)

        ttk.Separator(btn_row, orient="vertical").pack(side="left", padx=12, fill="y")

        ttk.Button(btn_row, text="刷新状态",
                   command=lambda: self.cb.get("refresh", lambda: None)()).pack(side="left", padx=4)
        ttk.Button(btn_row, text="提取 Token",
                   command=lambda: self.cb.get("extract_token", lambda: None)()).pack(side="left", padx=4)
        ttk.Button(btn_row, text="所有配置",
                   command=lambda: self.cb.get("view_all_config", lambda: None)()).pack(side="left", padx=4)
        ttk.Button(btn_row, text="打开配置文件",
                   command=lambda: self.cb.get("open_config", lambda: None)()).pack(side="left", padx=4)

        self._update_buttons(False)

    def set_status(self, running: bool, port: str = ""):
        self._running = running
        self._update_buttons(running)
        if running:
            self.status_display.config(text="运行中", foreground=get("success"))
            self.status_canvas.itemconfig(self._status_dot, fill=get("success"))
        else:
            self.status_display.config(text="已停止", foreground=get("danger"))
            self.status_canvas.itemconfig(self._status_dot, fill=get("danger"))

    def set_url(self, url: str):
        self.url_display.config(text=url)

    def set_port(self, port: str):
        self.port_var.set(port)

    def get_port(self) -> str:
        return self.port_var.get().strip()

    def set_busy(self, busy: bool):
        if busy:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.restart_btn.config(state="disabled")
        else:
            self._update_buttons(self._running)

    def _apply_port(self):
        port = self.port_var.get().strip()
        self.cb.get("apply_port", lambda p: None)(port)

    def _update_buttons(self, running: bool):
        if running:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.restart_btn.config(state="normal")
        else:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.restart_btn.config(state="disabled")
