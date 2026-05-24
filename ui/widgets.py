"""通用 UI 组件"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from ui.theme import get


class Sidebar:
    """垂直侧边栏导航"""

    def __init__(self, parent, on_select):
        self.parent = parent
        self.on_select = on_select
        self._buttons = []
        self._active_idx = 0

        self.frame = tk.Frame(parent, bg=get("sidebar_bg"), width=200)
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.frame, bg=get("sidebar_bg"))
        logo_frame.pack(fill="x", pady=(20, 10))
        tk.Label(logo_frame, text="🦀", font=("TkDefaultFont", 24), bg=get("sidebar_bg"),
                 fg=get("sidebar_active")).pack()
        tk.Label(logo_frame, text="OpenClaw", font=("TkDefaultFont", 10, "bold"),
                 bg=get("sidebar_bg"), fg=get("sidebar_fg")).pack(pady=(2, 0))

        # 分隔线
        tk.Frame(self.frame, bg=get("sidebar_hover"), height=1).pack(fill="x", padx=20)

        # 导航按钮容器
        self._nav_frame = tk.Frame(self.frame, bg=get("sidebar_bg"))
        self._nav_frame.pack(fill="both", expand=True, pady=10)

        # 底部版本信息
        self.version_label = tk.Label(self.frame, text="v---", font=("TkDefaultFont", 8),
                                      bg=get("sidebar_bg"), fg=get("fg_muted"))
        self.version_label.pack(side="bottom", pady=10)

    def add(self, icon: str, label: str) -> int:
        """添加导航项，返回索引"""
        idx = len(self._buttons)
        btn = tk.Frame(self._nav_frame, bg=get("sidebar_bg"), cursor="hand2", padx=20)
        btn.pack(fill="x")

        inner = tk.Frame(btn, bg=get("sidebar_bg"))
        inner.pack(fill="x", padx=5, pady=3)

        # 选中指示条
        bar = tk.Frame(inner, bg=get("sidebar_bg"), width=3)
        bar.pack(side="left", fill="y", padx=(0, 8))

        icon_label = tk.Label(inner, text=icon, font=("TkDefaultFont", 14), bg=get("sidebar_bg"),
                              fg=get("sidebar_fg"))
        icon_label.pack(side="left")

        text_label = tk.Label(inner, text=label, font=("TkDefaultFont", 10), bg=get("sidebar_bg"),
                              fg=get("sidebar_fg"), anchor="w")
        text_label.pack(side="left", padx=8)

        def on_enter(e, b=btn, ib=inner, bl=bar, ic=icon_label, tx=text_label):
            if idx != self._active_idx:
                b.configure(bg=get("sidebar_hover"))
                ib.configure(bg=get("sidebar_hover"))
                ic.configure(bg=get("sidebar_hover"))
                tx.configure(bg=get("sidebar_hover"))

        def on_leave(e, b=btn, ib=inner, bl=bar, ic=icon_label, tx=text_label):
            if idx != self._active_idx:
                b.configure(bg=get("sidebar_bg"))
                ib.configure(bg=get("sidebar_bg"))
                ic.configure(bg=get("sidebar_bg"))
                tx.configure(bg=get("sidebar_bg"))

        def on_click(e, i=idx):
            self.select(i)
            self.on_select(i)

        for w in [btn, inner, bar, icon_label, text_label]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        self._buttons.append((btn, inner, bar, icon_label, text_label))
        return idx

    def select(self, idx: int):
        """高亮指定导航项"""
        for i, (btn, inner, bar, icon, text) in enumerate(self._buttons):
            if i == idx:
                active = get("sidebar_active")
                btn.configure(bg=active)
                inner.configure(bg=active)
                bar.configure(bg=active)
                icon.configure(bg=active, fg="#ffffff")
                text.configure(bg=active, fg="#ffffff")
            else:
                bg = get("sidebar_bg")
                btn.configure(bg=bg)
                inner.configure(bg=bg)
                bar.configure(bg=bg)
                icon.configure(bg=bg, fg=get("sidebar_fg"))
                text.configure(bg=bg, fg=get("sidebar_fg"))
        self._active_idx = idx

    def set_version(self, version: str):
        self.version_label.config(text=f"v{version}")


class LogPanel:
    """可折叠日志面板"""

    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=get("log_bg"))
        self._count = 0
        self._expanded = True

        # 工具栏
        bar = tk.Frame(self.frame, bg=get("log_bg"))
        bar.pack(fill="x")

        self._count_label = tk.Label(bar, text="0 条", font=("Consolas", 8),
                                     bg=get("log_bg"), fg=get("fg_muted"))
        self._count_label.pack(side="left", padx=10, pady=2)

        toggle_text = "▾ 收起" if self._expanded else "▸ 展开"
        self._toggle_btn = tk.Label(bar, text=toggle_text, font=("TkDefaultFont", 9),
                                    bg=get("log_bg"), fg=get("accent"), cursor="hand2")
        self._toggle_btn.pack(side="right", padx=10, pady=2)
        self._toggle_btn.bind("<Button-1>", lambda e: self._toggle())

        clear_btn = tk.Label(bar, text="清空", font=("TkDefaultFont", 9),
                             bg=get("log_bg"), fg=get("accent"), cursor="hand2")
        clear_btn.pack(side="right", padx=5)
        clear_btn.bind("<Button-1>", lambda e: self.clear())

        # 文本区域
        self.text = scrolledtext.ScrolledText(
            self.frame, font=("Consolas", 9), wrap="word",
            bg=get("log_bg"), fg=get("log_fg"),
            insertbackground=get("accent"),
            selectbackground=get("sidebar_hover"),
            relief="flat", borderwidth=0, height=5,
            padx=10, pady=5
        )
        self.text.pack(fill="both", expand=True)

        _configure_log_tags(self.text)

    def append(self, line: str, tag: str = "info"):
        self.text.config(state="normal")
        self.text.insert(tk.END, line + "\n", tag)
        self.text.see(tk.END)
        self.text.config(state="disabled")
        self._count += 1
        self._count_label.config(text=f"{self._count} 条")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete(1.0, tk.END)
        self.text.config(state="disabled")
        self._count = 0
        self._count_label.config(text="0 条")

    def pack(self, **kw):
        self.frame.pack(**kw)

    def update_theme(self):
        self.frame.configure(bg=get("log_bg"))
        self._count_label.configure(bg=get("log_bg"), fg=get("fg_muted"))
        self._toggle_btn.configure(bg=get("log_bg"), fg=get("accent"))
        self.text.configure(bg=get("log_bg"), fg=get("log_fg"),
                            insertbackground=get("accent"))

    def _toggle(self):
        if self._expanded:
            self.text.pack_forget()
            self._toggle_btn.config(text="▸ 展开")
        else:
            self.text.pack(fill="both", expand=True)
            self._toggle_btn.config(text="▾ 收起")
        self._expanded = not self._expanded


def _configure_log_tags(text_widget):
    text_widget.tag_configure("success", foreground=get("success"))
    text_widget.tag_configure("error", foreground=get("danger"))
    text_widget.tag_configure("info", foreground=get("info"))
    text_widget.tag_configure("warning", foreground=get("warning"))
    text_widget.tag_configure("gateway", foreground="#a78bfa")
    text_widget.tag_configure("config", foreground="#2dd4bf")
    text_widget.tag_configure("version", foreground="#38bdf8")
    text_widget.tag_configure("admin", foreground="#fb923c")
