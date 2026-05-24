"""配置文件管理页面"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from ui.theme import get


class FilesPage:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=get("bg"))

        # 标题
        tk.Label(self.frame, text="配置文件管理", font=("TkDefaultFont", 16, "bold"),
                 bg=get("bg"), fg=get("fg")).pack(anchor="w", padx=30, pady=(25, 15))

        # 路径卡片
        path_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                             bd=1, highlightbackground=get("border"), highlightthickness=1)
        path_card.pack(fill="x", padx=30, pady=(0, 12))
        path_inner = tk.Frame(path_card, bg=get("card_bg"))
        path_inner.pack(fill="x", padx=20, pady=12)

        tk.Label(path_inner, text="路径", font=("TkDefaultFont", 9), bg=get("card_bg"),
                 fg=get("fg_secondary")).pack(side="left")
        self._path_label = tk.Label(path_inner, text="未获取", font=("TkDefaultFont", 10),
                                    bg=get("card_bg"), fg=get("accent"))
        self._path_label.pack(side="left", padx=10)

        bs = {"bg": get("card_bg"), "fg": get("fg"), "font": ("TkDefaultFont", 9),
              "relief": "solid", "bd": 1, "padx": 10, "pady": 3, "cursor": "hand2"}
        tk.Button(path_inner, text="获取路径", command=app.get_config_path, **bs).pack(side="right", padx=3)
        tk.Button(path_inner, text="打开文件", command=app.open_config_file, **bs).pack(side="right", padx=3)
        tk.Button(path_inner, text="打开文件夹", command=app.open_config_folder, **bs).pack(side="right", padx=3)

        # 预览
        pre_card = tk.Frame(self.frame, bg=get("card_bg"), relief="solid",
                            bd=1, highlightbackground=get("border"), highlightthickness=1)
        pre_card.pack(fill="both", expand=True, padx=30, pady=(0, 12))

        tk.Label(pre_card, text="内容预览", font=("TkDefaultFont", 9), bg=get("card_bg"),
                 fg=get("fg_secondary")).pack(anchor="w", padx=20, pady=(10, 0))

        self._preview = scrolledtext.ScrolledText(
            pre_card, font=("Consolas", 9), state="disabled",
            bg=get("log_bg"), fg=get("log_fg"),
            insertbackground=get("accent"), relief="flat", borderwidth=0,
            padx=15, pady=10
        )
        self._preview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # 操作按钮
        btn_row = tk.Frame(self.frame, bg=get("bg"))
        btn_row.pack(fill="x", padx=30)
        tk.Button(btn_row, text="🔄 刷新", command=lambda: app._refresh_preview() if app.config_file_path else None,
                  **bs).pack(side="left", padx=3)
        tk.Button(btn_row, text="💾 备份", command=app.backup_config,
                  bg=get("accent"), fg=get("accent_fg"), font=("TkDefaultFont", 9),
                  relief="flat", padx=12, pady=4, bd=0, cursor="hand2").pack(side="left", padx=3)
        tk.Button(btn_row, text="📥 还原", command=app.restore_config, **bs).pack(side="left", padx=3)

    def set_path(self, path: str):
        self._path_label.config(text=path)

    def set_preview(self, content: str):
        self._preview.config(state="normal")
        self._preview.delete(1.0, tk.END)
        self._preview.insert(tk.END, content)
        self._preview.config(state="disabled")

    def on_theme_change(self):
        self._preview.configure(bg=get("log_bg"), fg=get("log_fg"))
