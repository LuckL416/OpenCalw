"""核心配置 Tab"""
import tkinter as tk
from tkinter import ttk
from ui.widgets import SettingsRow

MODEL_PROVIDERS = {
    "Moonshot AI（Kimi）": {
        "provider_id": "moonshot",
        "api_key_url": "https://platform.moonshot.cn/console/api-keys",
        "models": [
            "moonshot/kimi-k2.5 - Kimi K2.5 旗舰版",
            "moonshot/kimi-k2.5-coding - Kimi K2.5 代码版",
            "moonshot/moonshot-v1-8k - 旧版 8k 日常聊天",
            "moonshot/moonshot-v1-32k - 旧版 32k 长文本"
        ]
    },
    "DeepSeek（深度求索）": {
        "provider_id": "deepseek",
        "api_key_url": "https://platform.deepseek.com/api_keys",
        "models": [
            "deepseek/deepseek-chat - 通用对话",
            "deepseek/deepseek-coder - 代码专用"
        ]
    },
    "通义千问（阿里云）": {
        "provider_id": "qwen",
        "api_key_url": "https://dashscope.console.aliyun.com/apiKey",
        "models": [
            "qwen/qwen-max - 旗舰版",
            "qwen/qwen-turbo - 极速版"
        ]
    }
}


class CoreConfigTab:
    def __init__(self, parent, callbacks: dict):
        self.cb = callbacks
        self.frame = parent

        outer = ttk.Frame(self.frame)
        outer.pack(fill="both", expand=True, padx=20, pady=15)

        # 提示横幅
        banner = ttk.Label(outer, text="配置前请先查看配置文件确认键名", font=("", 9),
                           foreground="#E65100", background="#FFF3E0", padding=(10, 4))
        banner.pack(fill="x", pady=(0, 12))

        # 主配置表单
        form = ttk.LabelFrame(outer, text="模型配置", style="Card.TLabelframe")
        form.pack(fill="x")
        grid = ttk.Frame(form, style="Card.TFrame")
        grid.pack(fill="x", padx=15, pady=10)

        r = 0
        # 厂商选择
        self.provider_var = tk.StringVar(value="Moonshot AI（Kimi）")
        self.provider_combo = ttk.Combobox(
            grid, textvariable=self.provider_var, values=list(MODEL_PROVIDERS.keys()),
            state="readonly", width=48, font=("", 10))
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_change)
        r = SettingsRow.grid(grid, r, "大模型厂商", self.provider_combo)

        # API密钥
        self.api_key_var = tk.StringVar()
        self.show_key_var = tk.BooleanVar(value=False)

        key_widget = ttk.Frame(grid)
        self.api_key_entry = ttk.Entry(key_widget, textvariable=self.api_key_var, width=42, show="*", font=("", 10))
        self.api_key_entry.pack(side="left")
        show_cb = ttk.Checkbutton(key_widget, text="显示", variable=self.show_key_var,
                                  command=self._toggle_key_visibility)
        show_cb.pack(side="left", padx=5)
        get_btn = ttk.Button(key_widget, text="获取密钥 ▸", command=self._open_api_key)
        get_btn.pack(side="left", padx=5)
        r = SettingsRow.grid(grid, r, "API 密钥", key_widget)

        # 模型选择
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            grid, textvariable=self.model_var, state="readonly", width=48, font=("", 10))
        r = SettingsRow.grid(grid, r, "默认模型", self.model_combo)
        self._on_provider_change(None)

        # 温度
        self.temp_var = tk.StringVar(value="0.7")
        temp_widget = ttk.Frame(grid)
        temp_entry = ttk.Entry(temp_widget, textvariable=self.temp_var, width=8, font=("", 10))
        temp_entry.pack(side="left")
        temp_entry.bind("<FocusOut>", lambda e: self._validate_temp())
        ttk.Label(temp_widget, text="范围 0-1，默认 0.7", style="Muted.TLabel").pack(side="left", padx=8)
        r = SettingsRow.grid(grid, r, "温度", temp_widget)

        # 最大令牌
        self.tokens_var = tk.StringVar(value="4096")
        tokens_widget = ttk.Frame(grid)
        tokens_entry = ttk.Entry(tokens_widget, textvariable=self.tokens_var, width=8, font=("", 10))
        tokens_entry.pack(side="left")
        tokens_entry.bind("<FocusOut>", lambda e: self._validate_tokens())
        ttk.Label(tokens_widget, text="默认 4096", style="Muted.TLabel").pack(side="left", padx=8)
        r = SettingsRow.grid(grid, r, "最大令牌数", tokens_widget)

        # 推理模式
        self.reasoning_var = tk.BooleanVar(value=True)
        r = SettingsRow.grid(grid, r, "推理模式", ttk.Checkbutton(grid, text="启用 reasoning",
                             variable=self.reasoning_var))

        # 操作按钮
        btn_row = ttk.Frame(outer)
        btn_row.pack(fill="x", pady=(12, 0))
        ttk.Button(btn_row, text="读取配置", command=lambda: self.cb.get("load", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(btn_row, text="保存配置", command=lambda: self.cb.get("save", lambda: None)(),
                   style="Accent.TButton").pack(side="left", padx=3)
        ttk.Button(btn_row, text="验证配置", command=lambda: self.cb.get("validate", lambda: None)()).pack(
            side="left", padx=3)
        ttk.Button(btn_row, text="重置", command=lambda: self.cb.get("reset", lambda: None)()).pack(
            side="left", padx=3)

    def get_values(self) -> dict:
        return {
            "provider": self.provider_var.get(),
            "model": self.model_var.get(),
            "api_key": self.api_key_var.get().strip(),
            "temperature": self.temp_var.get(),
            "max_tokens": self.tokens_var.get(),
            "reasoning": self.reasoning_var.get()
        }

    def set_values(self, data: dict):
        if "provider" in data:
            self.provider_var.set(data["provider"])
            self._on_provider_change(None)
        if "model" in data:
            self.model_var.set(data["model"])
        if "api_key" in data:
            self.api_key_var.set(data["api_key"])
        if "temperature" in data:
            self.temp_var.set(data["temperature"])
        if "max_tokens" in data:
            self.tokens_var.set(data["max_tokens"])
        if "reasoning" in data:
            self.reasoning_var.set(data["reasoning"])

    def reset(self):
        self.provider_var.set("Moonshot AI（Kimi）")
        self.api_key_var.set("")
        self.temp_var.set("0.7")
        self.tokens_var.set("4096")
        self.reasoning_var.set(True)
        self.api_key_entry.config(show="*")
        self.show_key_var.set(False)
        self._on_provider_change(None)

    def _toggle_key_visibility(self):
        self.api_key_entry.config(show="" if self.show_key_var.get() else "*")

    def _on_provider_change(self, event=None):
        provider = self.provider_var.get()
        if provider in MODEL_PROVIDERS:
            models = MODEL_PROVIDERS[provider]["models"]
            self.model_combo["values"] = models
            if models:
                self.model_combo.current(0)
        else:
            self.model_combo["values"] = []
            self.model_combo.set("")

    def _open_api_key(self):
        provider = self.provider_var.get()
        if provider in MODEL_PROVIDERS:
            self.cb.get("open_api_key_url", lambda u: None)(MODEL_PROVIDERS[provider]["api_key_url"])

    def _validate_temp(self):
        try:
            v = float(self.temp_var.get())
            if v < 0 or v > 1:
                raise ValueError
        except (ValueError, TypeError):
            self.temp_var.set("0.7")

    def _validate_tokens(self):
        try:
            v = int(self.tokens_var.get())
            if v <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self.tokens_var.set("4096")
