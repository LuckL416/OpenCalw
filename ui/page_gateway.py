"""Gateway 控制页面"""
import tkinter as tk
from tkinter import ttk
from ui.theme import get


class GatewayPage:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=get("bg"))

        # 标题
        h = tk.Frame(self.frame, bg=get("bg"))
        h.pack(fill="x", padx=30, pady=(25, 15))
        tk.Label(h, text="Gateway 控制台", font=("TkDefaultFont", 16, "bold"),
                 bg=get("bg"), fg=get("fg")).pack(side="left")

        # 状态卡片
        self._status_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                                     bd=1, highlightbackground=get("border"), highlightthickness=1)
        self._status_card.pack(fill="x", padx=30, pady=(0, 15))

        status_inner = tk.Frame(self._status_card, bg=get("card_bg"))
        status_inner.pack(fill="x", padx=25, pady=20)

        # 状态点 + 文字
        row1 = tk.Frame(status_inner, bg=get("card_bg"))
        row1.pack(fill="x")
        self._dot = tk.Canvas(row1, width=14, height=14, highlightthickness=0, bg=get("card_bg"))
        self._dot.pack(side="left", pady=3)
        self._dot_oval = self._dot.create_oval(2, 2, 12, 12, fill=get("fg_muted"), outline="")
        self._status_label = tk.Label(row1, text="已停止", font=("TkDefaultFont", 18, "bold"),
                                      bg=get("card_bg"), fg=get("fg_muted"))
        self._status_label.pack(side="left", padx=12)

        # 端口 + Dashboard
        row2 = tk.Frame(status_inner, bg=get("card_bg"))
        row2.pack(fill="x", pady=(12, 0))

        tk.Label(row2, text="端口", font=("TkDefaultFont", 9), bg=get("card_bg"),
                 fg=get("fg_secondary")).pack(side="left")
        self.port_var = tk.StringVar(value="18789")
        pe = tk.Entry(row2, textvariable=self.port_var, width=7, font=("TkDefaultFont", 12, "bold"),
                      bg=get("input_bg"), fg=get("fg"),
                      insertbackground=get("accent"), relief="solid", bd=1)
        pe.pack(side="left", padx=8)
        pe.bind("<Return>", lambda e: app.apply_port(self.port_var.get()))

        tk.Button(row2, text="应用", command=lambda: app.apply_port(self.port_var.get()),
                  bg=get("accent"), fg=get("accent_fg"), font=("TkDefaultFont", 9),
                  relief="flat", padx=12, pady=3, bd=0, cursor="hand2",
                  activebackground=get("accent_hover")).pack(side="left")

        tk.Label(row2, text="Dashboard", font=("TkDefaultFont", 9), bg=get("card_bg"),
                 fg=get("fg_secondary")).pack(side="left", padx=(30, 8))
        self._url_label = tk.Label(row2, text="—", font=("TkDefaultFont", 10),
                                   bg=get("card_bg"), fg=get("accent"), cursor="hand2")
        self._url_label.pack(side="left")
        self._url_label.bind("<Button-1>", lambda e: app.open_dashboard())

        tk.Button(row2, text="打开 →", command=app.open_dashboard,
                  bg=get("card_bg"), fg=get("accent"), font=("TkDefaultFont", 9),
                  relief="flat", padx=8, bd=0, cursor="hand2").pack(side="left", padx=6)

        # 按钮组
        btn_row = tk.Frame(status_inner, bg=get("card_bg"))
        btn_row.pack(fill="x", pady=(18, 0))

        self._start_btn = tk.Button(btn_row, text="▶  启动", command=app.start_gateway,
                                    bg=get("accent"), fg=get("accent_fg"), font=("TkDefaultFont", 10, "bold"),
                                    relief="flat", padx=20, pady=8, bd=0, cursor="hand2",
                                    activebackground=get("accent_hover"))
        self._start_btn.pack(side="left", padx=(0, 6))

        self._stop_btn = tk.Button(btn_row, text="■  停止", command=app.stop_gateway,
                                   bg=get("card_bg"), fg=get("danger"), font=("TkDefaultFont", 10),
                                   relief="solid", padx=20, pady=8, bd=1, cursor="hand2",
                                   activebackground="#fef2f2")
        self._stop_btn.pack(side="left", padx=6)
        self._stop_btn.config(state="disabled")

        self._restart_btn = tk.Button(btn_row, text="↻  重启", command=app.restart_gateway,
                                      bg=get("card_bg"), fg=get("fg"), font=("TkDefaultFont", 10),
                                      relief="solid", padx=20, pady=6, bd=1, cursor="hand2")
        self._restart_btn.pack(side="left", padx=6)
        self._restart_btn.config(state="disabled")

        # 分隔 + 其他操作
        tk.Frame(btn_row, bg=get("border"), width=1).pack(side="left", fill="y", padx=16, pady=4)

        btn_style = {"bg": get("card_bg"), "fg": get("fg"), "font": ("TkDefaultFont", 9),
                     "relief": "solid", "padx": 12, "pady": 4, "bd": 1, "cursor": "hand2"}

        tk.Button(btn_row, text="刷新状态", command=app._refresh_status, **btn_style).pack(side="left", padx=4)
        tk.Button(btn_row, text="所有配置", command=app._view_all_config, **btn_style).pack(side="left", padx=4)

        # ---- 版本卡片 ----
        ver_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                            bd=1, highlightbackground=get("border"), highlightthickness=1)
        ver_card.pack(fill="x", padx=30, pady=(0, 10))
        ver_inner = tk.Frame(ver_card, bg=get("card_bg"))
        ver_inner.pack(fill="x", padx=25, pady=15)

        tk.Label(ver_inner, text="版本管理", font=("TkDefaultFont", 10, "bold"),
                 bg=get("card_bg"), fg=get("fg")).pack(anchor="w")

        vrow = tk.Frame(ver_inner, bg=get("card_bg"))
        vrow.pack(fill="x", pady=(8, 0))
        self._cur_ver_label = tk.Label(vrow, text="当前：检测中...", font=("TkDefaultFont", 10),
                                       bg=get("card_bg"), fg=get("fg_secondary"))
        self._cur_ver_label.pack(side="left")

        self._update_status_label = tk.Label(vrow, text="", font=("TkDefaultFont", 10),
                                             bg=get("card_bg"), fg=get("success"))
        self._update_status_label.pack(side="left", padx=20)

        tk.Button(vrow, text="检查更新", command=app.check_update, **btn_style).pack(side="right", padx=4)
        self._update_btn = tk.Button(vrow, text="立即更新", command=app.do_update,
                                     bg=get("accent"), fg=get("accent_fg"), font=("TkDefaultFont", 9),
                                     relief="flat", padx=12, pady=3, bd=0, cursor="hand2",
                                     activebackground=get("accent_hover"))
        self._update_btn.pack(side="right", padx=4)
        self._update_btn.pack_forget()  # 默认隐藏

        self._update_progress = ttk.Progressbar(ver_inner, mode="indeterminate")
        self._update_progress.pack(fill="x", pady=(8, 0))
        self._update_progress.pack_forget()

    # ---- 公开方法 ----

    def set_running(self, running: bool):
        if running:
            self._status_label.config(text="运行中", fg=get("success"))
            self._dot.itemconfig(self._dot_oval, fill=get("success"))
            self._start_btn.config(state="disabled")
            self._stop_btn.config(state="normal")
            self._restart_btn.config(state="normal")
        else:
            self._status_label.config(text="已停止", fg=get("fg_muted"))
            self._dot.itemconfig(self._dot_oval, fill=get("fg_muted"))
            self._start_btn.config(state="normal")
            self._stop_btn.config(state="disabled")
            self._restart_btn.config(state="disabled")

    def set_busy(self, busy: bool):
        s = "disabled" if busy else "normal"
        self._start_btn.config(state=s)
        self._stop_btn.config(state=s)
        self._restart_btn.config(state=s)

    def set_url(self, url: str):
        self._url_label.config(text=url)

    def show_update_available(self, current: str, latest: str):
        self._cur_ver_label.config(text=f"当前：{current}  →  最新：{latest}")
        self._update_status_label.config(text="有新版本！", fg=get("warning"))
        self._update_btn.pack(side="right", padx=4, before=self._update_status_label.master.winfo_children()[0])
        self._update_btn.lift()

    def show_update_uptodate(self, current: str):
        self._cur_ver_label.config(text=f"当前：{current}")
        self._update_status_label.config(text="已是最新 ✓", fg=get("success"))
        self._update_btn.pack_forget()

    def show_update_done(self, version: str):
        self._cur_ver_label.config(text=f"当前：{version}")
        self._update_status_label.config(text="更新完成 ✓", fg=get("success"))
        self._update_btn.pack_forget()
        self.set_updating(False)

    def set_updating(self, active: bool):
        if active:
            self._update_progress.pack(fill="x", pady=(8, 0))
            self._update_progress.start()
            self._update_btn.config(state="disabled")
        else:
            self._update_progress.stop()
            self._update_progress.pack_forget()
            self._update_btn.config(state="normal")

    def on_theme_change(self):
        c = get
        self.frame.configure(bg=c("bg"))
        self._status_card.configure(bg=c("card_bg"), highlightbackground=c("border"))
        self._status_label.configure(bg=c("card_bg"))
        self._dot.configure(bg=c("card_bg"))
        self._url_label.configure(bg=c("card_bg"), fg=c("accent"))
        self._cur_ver_label.configure(bg=c("card_bg"), fg=c("fg_secondary"))
        self._update_status_label.configure(bg=c("card_bg"))
        # Re-render running state
        self.set_running(self.app.gateway_running)
