"""配置页面 —— 模型配置 + 高级设置"""
import tkinter as tk
from tkinter import ttk
import webbrowser
from ui.theme import get

PROVIDERS = {
    "OpenAI": {
        "id": "openai",
        "url": "https://platform.openai.com/api-keys",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini", "o1"]
    },
    "Anthropic（Claude）": {
        "id": "anthropic",
        "url": "https://console.anthropic.com/settings/keys",
        "models": ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5"]
    },
    "Moonshot AI（Kimi）": {
        "id": "moonshot",
        "url": "https://platform.moonshot.cn/console/api-keys",
        "models": ["moonshot/kimi-k2.5", "moonshot/kimi-k2.5-coding",
                   "moonshot/moonshot-v1-8k", "moonshot/moonshot-v1-32k",
                   "moonshot/moonshot-v1-128k"]
    },
    "DeepSeek（深度求索）": {
        "id": "deepseek",
        "url": "https://platform.deepseek.com/api_keys",
        "models": ["deepseek/deepseek-chat", "deepseek/deepseek-coder",
                   "deepseek/deepseek-reasoner"]
    },
    "通义千问（阿里云）": {
        "id": "qwen",
        "url": "https://dashscope.console.aliyun.com/apiKey",
        "models": ["qwen/qwen-max", "qwen/qwen-plus", "qwen/qwen-turbo",
                   "qwen/qwen-max-latest"]
    },
    "Google（Gemini）": {
        "id": "google",
        "url": "https://aistudio.google.com/app/apikey",
        "models": ["google/gemini-2.5-flash", "google/gemini-2.5-pro"]
    },
    "Groq": {
        "id": "groq",
        "url": "https://console.groq.com/keys",
        "models": ["groq/llama-3.3-70b", "groq/llama-3.1-8b", "groq/mixtral-8x7b"]
    },
    "Ollama（本地）": {
        "id": "ollama",
        "url": "",
        "models": ["ollama/llama3", "ollama/qwen2.5", "ollama/deepseek-r1"]
    },
}


class ConfigPage:
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=get("bg"))

        canvas = tk.Canvas(self.frame, bg=get("bg"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        self._scroll = tk.Frame(canvas, bg=get("bg"))
        self._scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll, anchor="nw", tags="inner")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
        def _on_mousewheel(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self._build_ui()

    # ========== UI 构建 ==========

    def _build_ui(self):
        tk.Label(self._scroll, text="模型配置", font=("TkDefaultFont", 18, "bold"),
                 bg=get("bg"), fg=get("fg")).pack(anchor="w", padx=40, pady=(30, 20))

        self._build_model_section()
        self._build_advanced_section()

    def _build_model_section(self):
        card = self._card_frame("大模型配置")
        grid = tk.Frame(card, bg=get("card_bg"))
        grid.pack(fill="x", padx=30, pady=(5, 20))

        r = 0

        # ---- 厂商选择 ----
        self.provider_var = tk.StringVar(value=list(PROVIDERS.keys())[0])
        r = self._grid_row(grid, r, "厂商",
                           self._cbb(grid, self.provider_var, list(PROVIDERS.keys()), 34,
                                     self._on_provider_change))

        # ---- API 密钥 ----
        self.api_key_var = tk.StringVar()
        key_row = tk.Frame(grid, bg=get("card_bg"))
        self._key_entry = tk.Entry(key_row, textvariable=self.api_key_var, show="*",
                                   font=("Consolas", 10), width=36,
                                   bg=get("input_bg"), fg=get("fg"),
                                   insertbackground=get("accent"), relief="solid", bd=1)
        self._key_entry.pack(side="left")
        self._show_key_var = tk.BooleanVar()
        eye_btn = tk.Button(key_row, text="👁", font=("TkDefaultFont", 9),
                            relief="flat", bd=0, cursor="hand2",
                            bg=get("card_bg"), fg=get("fg_secondary"),
                            command=self._toggle_key_visibility)
        eye_btn.pack(side="left", padx=4)
        r = self._grid_row(grid, r, "API 密钥", key_row)

        # 获取密钥链接
        self._key_url_label = tk.Label(grid, text="获取密钥 →", font=("TkDefaultFont", 9),
                                       bg=get("card_bg"), fg=get("accent"), cursor="hand2")
        self._key_url_label.grid(row=r - 1, column=2, sticky="w", padx=10)
        self._key_url_label.bind("<Button-1>", lambda e: self._open_key_url())
        self._update_key_url()

        # ---- 模型选择 ----
        model_row = tk.Frame(grid, bg=get("card_bg"))
        self.model_var = tk.StringVar()
        self._model_cb = ttk.Combobox(model_row, textvariable=self.model_var, width=28)
        self._model_cb.pack(side="left")
        self._model_cb.bind("<<ComboboxSelected>>", lambda e: self._on_model_selected())

        refresh_btn = tk.Button(model_row, text="🔄 刷新", font=("TkDefaultFont", 9),
                                relief="solid", bd=1, padx=10, cursor="hand2",
                                bg=get("card_bg"), fg=get("fg"),
                                command=self._refresh_models)
        refresh_btn.pack(side="left", padx=6)
        r = self._grid_row(grid, r, "模型", model_row)

        self._model_status = tk.Label(grid, text="", font=("TkDefaultFont", 8),
                                      bg=get("card_bg"), fg=get("fg_muted"))
        self._model_status.grid(row=r - 1, column=2, sticky="w", padx=10)
        self._on_provider_change()

        # ---- 分隔 ----
        tk.Frame(grid, bg=get("border"), height=1).grid(
            row=r, column=0, columnspan=3, sticky="ew", pady=12)
        r += 1

        # ---- 参数区 ----
        param_label = tk.Label(grid, text="请求参数", font=("TkDefaultFont", 10, "bold"),
                               bg=get("card_bg"), fg=get("fg"))
        param_label.grid(row=r, column=0, columnspan=3, sticky="w", pady=(0, 8))
        r += 1

        # 温度
        self.temp_var = tk.StringVar(value="0.7")
        temp_row = tk.Frame(grid, bg=get("card_bg"))
        self._temp_entry = tk.Entry(temp_row, textvariable=self.temp_var, width=8,
                                    font=("TkDefaultFont", 10),
                                    bg=get("input_bg"), fg=get("fg"), relief="solid", bd=1)
        self._temp_entry.pack(side="left")
        self._temp_entry.bind("<FocusOut>", lambda e: self._validate_temp())
        self._temp_scale = ttk.Scale(temp_row, from_=0, to=1, value=0.7,
                                     command=self._on_temp_scale, length=100)
        self._temp_scale.pack(side="left", padx=8)
        self._temp_hint = tk.Label(temp_row, text="0.7", font=("TkDefaultFont", 9),
                                   bg=get("card_bg"), fg=get("accent"), width=4)
        self._temp_hint.pack(side="left")
        r = self._grid_row(grid, r, "温度", temp_row)

        # 最大令牌
        self.tokens_var = tk.StringVar(value="4096")
        r = self._grid_row(grid, r, "最大令牌",
                           self._entry(grid, self.tokens_var, 9),
                           tk.Label(grid, text="默认 4096", font=("TkDefaultFont", 9),
                                    bg=get("card_bg"), fg=get("fg_muted")))

        # 推理模式
        self.reasoning_var = tk.BooleanVar(value=True)
        r = self._grid_row(grid, r, "推理模式",
                           tk.Checkbutton(grid, text="启用 reasoning（深度思考）",
                                          variable=self.reasoning_var,
                                          bg=get("card_bg"), fg=get("fg"),
                                          selectcolor=get("card_bg"),
                                          activebackground=get("card_bg"),
                                          font=("TkDefaultFont", 10)))

        # ---- 操作按钮 ----
        btn_row = tk.Frame(grid, bg=get("card_bg"))
        btn_row.grid(row=r + 1, column=0, columnspan=3, sticky="w", pady=(15, 0))
        r += 2

        bs = {"relief": "flat", "padx": 16, "pady": 8, "bd": 0, "cursor": "hand2",
              "font": ("TkDefaultFont", 10)}
        tk.Button(btn_row, text="读取配置", command=self.app.load_config,
                  bg=get("card_bg"), fg=get("fg"), **bs).pack(side="left", padx=3)
        tk.Button(btn_row, text="💾 保存配置", command=self.app._save_config,
                  bg=get("accent"), fg=get("accent_fg"), **bs).pack(side="left", padx=3)
        tk.Button(btn_row, text="✅ 验证", command=self.app.validate_config,
                  bg=get("card_bg"), fg=get("fg"), **bs).pack(side="left", padx=3)
        tk.Button(btn_row, text="重置", command=self.app.reset_config,
                  bg=get("card_bg"), fg=get("fg"), **bs).pack(side="left", padx=3)

    def _build_advanced_section(self):
        card = self._card_frame("高级设置")
        grid = tk.Frame(card, bg=get("card_bg"))
        grid.pack(fill="x", padx=30, pady=(5, 20))
        r = 0

        self.timezone_var = tk.StringVar(value="Asia/Shanghai")
        r = self._grid_row(grid, r, "时区",
                           self._entry(grid, self.timezone_var, 20),
                           tk.Label(grid, text="默认 Asia/Shanghai", font=("TkDefaultFont", 9),
                                    bg=get("card_bg"), fg=get("fg_muted")))

        self.lang_var = tk.StringVar(value="zh-CN")
        r = self._grid_row(grid, r, "语言",
                           self._cbb(grid, self.lang_var, ["zh-CN", "en-US"], 18))

        self.verbose_var = tk.BooleanVar()
        self.silent_var = tk.BooleanVar()
        vf = tk.Frame(grid, bg=get("card_bg"))
        tk.Checkbutton(vf, text="Verbose 详细输出", variable=self.verbose_var,
                       bg=get("card_bg"), fg=get("fg"), selectcolor=get("card_bg"),
                       activebackground=get("card_bg"), font=("TkDefaultFont", 10)).pack(anchor="w")
        tk.Checkbutton(vf, text="Silent 静默模式", variable=self.silent_var,
                       bg=get("card_bg"), fg=get("fg"), selectcolor=get("card_bg"),
                       activebackground=get("card_bg"), font=("TkDefaultFont", 10)).pack(anchor="w")
        r = self._grid_row(grid, r, "日志模式", vf)

    # ========== 辅助控件创建 ==========

    def _card_frame(self, title):
        f = tk.Frame(self._scroll, bg=get("card_bg"), relief="solid",
                     bd=1, highlightbackground=get("border"), highlightthickness=1)
        f.pack(fill="x", padx=40, pady=(0, 18))
        tk.Label(f, text=title, font=("TkDefaultFont", 11, "bold"),
                 bg=get("card_bg"), fg=get("fg")).pack(anchor="w", padx=30, pady=(18, 5))
        return f

    def _grid_row(self, parent, row, label, widget, extra=None):
        """统一的网格行：标签 | 控件 | 额外信息"""
        lbl = tk.Label(parent, text=label, font=("TkDefaultFont", 10),
                       bg=get("card_bg"), fg=get("fg_secondary"))
        lbl.grid(row=row, column=0, sticky="e", padx=(0, 12), pady=8)
        widget.grid(row=row, column=1, sticky="w", pady=8)
        if extra:
            extra.grid(row=row, column=2, sticky="w", padx=12, pady=8)
        return row + 1

    def _entry(self, parent, var, width):
        return tk.Entry(parent, textvariable=var, width=width, font=("TkDefaultFont", 10),
                        bg=get("input_bg"), fg=get("fg"), relief="solid", bd=1,
                        insertbackground=get("accent"))

    def _cbb(self, parent, var, values, width, on_change=None):
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=width, font=("TkDefaultFont", 10))
        if on_change:
            cb.bind("<<ComboboxSelected>>", on_change)
        return cb

    # ========== 模型刷新 ==========

    def _refresh_models(self):
        """重置为内置模型列表"""
        provider = self.provider_var.get()
        models = PROVIDERS.get(provider, {}).get("models", [])
        self._model_cb["values"] = models
        if models:
            self._model_cb.current(0)
        self._model_status.config(text=f"内置 {len(models)} 个", fg=get("fg_muted"))

    def _update_model_list(self, models):
        self._model_cb["values"] = models
        if models:
            self._model_cb.current(0)
        self._model_status.config(text=f"共 {len(models)} 个", fg=get("success"))

    # ========== 事件处理 ==========

    def _on_provider_change(self, e=None):
        provider = self.provider_var.get()
        if provider in PROVIDERS:
            models = PROVIDERS[provider]["models"]
            self._model_cb["values"] = models
            if models:
                self._model_cb.current(0)
                self._on_model_selected()
            self._model_status.config(text=f"内置 {len(models)} 个", fg=get("fg_muted"))
        self._update_key_url()

    def _on_model_selected(self):
        pass  # 预留：选中模型后的操作

    def _on_temp_scale(self, val):
        v = round(float(val), 2)
        self.temp_var.set(str(v))
        self._temp_hint.config(text=str(v))

    def _toggle_key_visibility(self):
        self._show_key_var.set(not self._show_key_var.get())
        self._key_entry.config(show="" if self._show_key_var.get() else "*")

    def _update_key_url(self):
        provider = self.provider_var.get()
        url = PROVIDERS.get(provider, {}).get("url", "")
        if url:
            self._key_url_label.config(text="获取密钥 →", cursor="hand2")
        else:
            self._key_url_label.config(text="", cursor="")

    def _open_key_url(self):
        provider = self.provider_var.get()
        url = PROVIDERS.get(provider, {}).get("url", "")
        if url:
            webbrowser.open(url)

    # ========== 数据操作 ==========

    def get_values(self):
        return {
            "provider": self.provider_var.get(),
            "model": self.model_var.get(),
            "api_key": self.api_key_var.get().strip(),
            "temperature": self.temp_var.get(),
            "max_tokens": self.tokens_var.get(),
            "reasoning": self.reasoning_var.get(),
            "timezone": self.timezone_var.get(),
            "language": self.lang_var.get(),
            "verbose": self.verbose_var.get(),
            "silent": self.silent_var.get(),
        }

    def set_values(self, d):
        for k in ["provider", "model", "api_key", "temperature", "max_tokens",
                   "timezone", "language"]:
            if k in d:
                var_name = f"{k}_var"
                if hasattr(self, var_name):
                    getattr(self, var_name).set(str(d[k]))
        for k in ["reasoning", "verbose", "silent"]:
            if k in d:
                var_name = f"{k}_var"
                if hasattr(self, var_name):
                    getattr(self, var_name).set(bool(d[k]))
        if "provider" in d:
            self._on_provider_change()

    def reset(self):
        self.provider_var.set(list(PROVIDERS.keys())[0])
        self.api_key_var.set("")
        self.temp_var.set("0.7")
        self._temp_scale.set(0.7)
        self._temp_hint.config(text="0.7")
        self.tokens_var.set("4096")
        self.reasoning_var.set(True)
        self.timezone_var.set("Asia/Shanghai")
        self.lang_var.set("zh-CN")
        self.verbose_var.set(False)
        self.silent_var.set(False)
        self._key_entry.config(show="*")
        self._show_key_var.set(False)
        self._on_provider_change()

    def on_theme_change(self):
        pass

    # ========== 验证 ==========

    def _validate_temp(self):
        try:
            v = float(self.temp_var.get())
            if not 0 <= v <= 1:
                raise ValueError
            self._temp_scale.set(v)
            self._temp_hint.config(text=str(v))
        except Exception:
            self.temp_var.set("0.7")
            self._temp_scale.set(0.7)
            self._temp_hint.config(text="0.7")

    def _validate_tokens(self):
        try:
            if int(self.tokens_var.get()) <= 0:
                raise ValueError
        except Exception:
            self.tokens_var.set("4096")
