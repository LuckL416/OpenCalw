# ====================== 前置配置与导入 ======================
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import queue
import time
import ctypes
import json
import webbrowser
import socket
import urllib.request
import tempfile
from typing import Optional, Dict, List, Tuple
import locale

# 禁用libpng警告
os.environ['PYTHONWARNINGS'] = 'ignore:libpng warning'
os.environ['PNG_WARNINGS'] = '0'

# 设置默认编码为UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
locale.setlocale(locale.LC_ALL, '')


# ====================== 工具函数（线程安全+权限检测） ======================
def is_admin():
    """检测是否管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_on_main_thread(func, *args, **kwargs):
    """线程安全执行UI操作"""
    if threading.current_thread() is threading.main_thread():
        func(*args, **kwargs)
    else:
        root = kwargs.pop('root', None) or tk._default_root
        if root:
            root.after(0, lambda: func(*args, **kwargs))


# ====================== 全局常量定义（适配2026.3.8） ======================
class AppConst:
    DEFAULT_PORT = "18789"  # OpenClaw默认Gateway端口
    DEFAULT_TIMEOUT = 15  # 命令执行超时时间
    LOG_MAX_LINES = 1000  # 日志最大行数
    GATEWAY_CHECK_INTERVAL = 5  # 状态刷新间隔
    GATEWAY_MAX_WAIT = 20  # Gateway启动等待时间

    # 安装向导步骤
    INSTALL_STEPS = [
        "📝 许可声明",
        "🔍 环境检测",
        "🚀 安装OpenClaw",
        "⚙️ 初始化配置",
        "✅ 部署完成"
    ]

    # Node.js LTS下载链接（npmmirror镜像）
    NODE_DOWNLOAD_URL = "https://npmmirror.com/mirrors/node/v18.20.4/node-v18.20.4-x64.msi"


# ====================== 主应用类（完整修复版） ======================
class OpenClawManager2026:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OpenClaw 管理工具（2026.3.8 路径修复+稳定版）")
        self.root.geometry("1300x900")
        self.root.resizable(True, True)
        self.root.minsize(1000, 700)  # 最小窗口尺寸，避免UI挤压

        # 全局状态变量
        self.node_path: Optional[str] = None
        self.npm_path: Optional[str] = None
        self.openclaw_path: Optional[str] = None
        self.config_file_path: Optional[str] = None  # 配置文件路径（绝对路径）
        self.is_installed: bool = False
        self.is_busy: bool = False
        self.output_queue = queue.Queue()
        self.log_data: List[Tuple[str, Optional[str]]] = []
        self.openclaw_version: str = "unknown"
        self.install_step: int = 0
        self.gateway_running: bool = False  # Gateway运行状态
        self.dashboard_url: str = ""  # Dashboard地址

        # 配置绑定变量（添加默认值保护）
        self.selected_provider = tk.StringVar(value="Moonshot AI（Kimi）")
        self.api_key = tk.StringVar(value="")
        self.selected_model = tk.StringVar(value="")
        self.temperature = tk.StringVar(value="0.7")
        self.max_tokens = tk.StringVar(value="4096")
        self.reasoning = tk.BooleanVar(value=True)
        self.timezone = tk.StringVar(value="Asia/Shanghai")
        self.language = tk.StringVar(value="zh-CN")
        self.verbose_mode = tk.BooleanVar(value=False)
        self.silent_mode = tk.BooleanVar(value=False)
        self.gateway_port = tk.StringVar(value=AppConst.DEFAULT_PORT)
        self.show_key_var = tk.BooleanVar(value=False)  # 独立管理，避免重复定义

        # 内置模型厂商配置
        self.model_providers = {
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

        # 初始化界面
        self.create_ui()
        self.process_queue()

        # 检查管理员权限
        if not is_admin():
            run_on_main_thread(messagebox.showwarning,
                               "权限提示",
                               "当前非管理员权限，部分操作（如安装Node.js/OpenClaw）可能失败！\n建议以管理员身份运行本程序。",
                               root=self.root)

        # 自动检测环境（线程安全）
        threading.Thread(target=self.auto_detect_environment, daemon=True).start()

    # ====================== 界面创建（优化：避免重复定义+UI稳定性） ======================
    def create_ui(self):
        # 配置ttk样式
        style = ttk.Style(self.root)
        style.configure("Accent.TButton", foreground="white", background="#2196F3", font=("", 10, "bold"))
        style.configure("Status.TLabel", font=("", 10))
        style.configure("Info.TLabel", font=("", 10), foreground="#666")

        # 顶部状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=20, pady=10)

        self.status_label = ttk.Label(status_frame, text="🔍 正在检测OpenClaw 2026.3.8环境...",
                                      font=("", 12, "bold"), style="Status.TLabel")
        self.status_label.pack(side="left")

        self.info_label = ttk.Label(status_frame,
                                    text=f"版本：未知 | 网关端口：{AppConst.DEFAULT_PORT} | 配置文件：未获取",
                                    style="Info.TLabel")
        self.info_label.pack(side="right", padx=20)

        # Tab控件（优化：避免重复添加）
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill="both", expand=True, padx=20, pady=5)

        # 1. Gateway控制Tab
        self.tab_gateway = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_gateway, text="🚀 Gateway控制")
        self.create_gateway_tab()

        # 2. 核心配置Tab
        self.tab_core = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_core, text="🎯 核心配置")
        self.create_core_config_tab()

        # 3. 高级设置Tab
        self.tab_advanced = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_advanced, text="⚙️ 高级设置")
        self.create_advanced_config_tab()

        # 4. 配置文件管理Tab（路径修复版）
        self.tab_config_file = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_config_file, text="📄 配置文件管理")
        self.create_config_file_tab()

        # 5. 安装向导Tab
        self.tab_install_wizard = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_install_wizard, text="🧰 安装向导")
        self.create_install_wizard_tab()

        # 日志显示区（优化：固定字体+滚动条）
        log_frame = ttk.LabelFrame(self.root, text="运行日志（路径修复+稳定版）")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled", font=("Consolas", 9), wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        # 日志标签颜色配置（优化：更友好的配色）
        self.log_text.tag_configure("success", foreground="#2E7D32")
        self.log_text.tag_configure("error", foreground="#D32F2F")
        self.log_text.tag_configure("info", foreground="#1976D2")
        self.log_text.tag_configure("warning", foreground="#FF8C00")
        self.log_text.tag_configure("gateway", foreground="#7B1FA2")
        self.log_text.tag_configure("config", foreground="#00796B")
        self.log_text.tag_configure("version", foreground="#006064")
        self.log_text.tag_configure("admin", foreground="#FF5722")

        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def create_gateway_tab(self):
        """Gateway控制界面（优化：按钮状态初始化+容错）"""
        main_frame = ttk.Frame(self.tab_gateway)
        main_frame.pack(fill="x", padx=30, pady=30)

        # Gateway运行状态面板
        status_panel = ttk.LabelFrame(main_frame, text="📊 Gateway运行状态", relief="groove", borderwidth=2)
        status_panel.pack(fill="x", pady=15)

        # 第一行：状态+Web地址
        row1 = ttk.Frame(status_panel)
        row1.pack(fill="x", padx=20, pady=10)

        ttk.Label(row1, text="当前状态：", font=("", 10, "bold")).pack(side="left")
        self.gateway_status_display = ttk.Label(row1, text="❌ 已停止", font=("", 10, "bold"), foreground="#D32F2F")
        self.gateway_status_display.pack(side="left", padx=10)

        ttk.Label(row1, text="Dashboard地址：", font=("", 10)).pack(side="left", padx=30)
        self.web_url_display = ttk.Label(row1, text="未获取", foreground="#1976D2", cursor="hand2")
        self.web_url_display.pack(side="left", padx=5)
        self.web_url_display.bind("<Button-1>", lambda e: self.manual_get_dashboard_url())
        ttk.Button(row1, text="🌐 手动打开", command=self.manual_open_dashboard, width=10).pack(side="left", padx=10)

        # 第二行：端口配置+状态刷新
        row2 = ttk.Frame(status_panel)
        row2.pack(fill="x", padx=20, pady=10)

        ttk.Label(row2, text="网关端口：", font=("", 10)).pack(side="left")
        port_entry = ttk.Entry(row2, textvariable=self.gateway_port, width=10, font=("", 10))
        port_entry.pack(side="left", padx=5)
        port_entry.bind("<Return>", lambda e: self.apply_port_config())  # 回车应用端口
        ttk.Button(row2, text="🔄 应用端口", command=self.apply_port_config, width=10).pack(side="left", padx=5)

        ttk.Button(row2, text="🔍 手动刷新状态", command=self.refresh_gateway_status, width=12).pack(side="left",
                                                                                                    padx=30)
        ttk.Button(row2, text="📄 打开配置文件", command=self.open_config_file, width=12).pack(side="left", padx=10)

        # Gateway控制按钮组（初始化禁用）
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=20)

        self.gateway_start_btn = ttk.Button(
            btn_frame, text="▶️ 启动Gateway", command=self.start_gateway, width=15, state="disabled",
            style="Accent.TButton"
        )
        self.gateway_start_btn.pack(side="left", padx=8)

        self.gateway_stop_btn = ttk.Button(
            btn_frame, text="⏹️ 停止Gateway", command=self.stop_gateway, width=15, state="disabled"
        )
        self.gateway_stop_btn.pack(side="left", padx=8)

        self.gateway_restart_btn = ttk.Button(
            btn_frame, text="🔄 重启Gateway", command=self.restart_gateway, width=15, state="disabled"
        )
        self.gateway_restart_btn.pack(side="left", padx=8)

        # 提取Token按钮
        ttk.Button(btn_frame, text="🔑 提取认证Token", command=self.extract_gateway_token, width=15).pack(side="left",
                                                                                                         padx=8)

        # 查看所有配置按钮
        ttk.Button(btn_frame, text="📋 查看所有配置", command=self.view_all_config, width=15).pack(side="left", padx=8)

    def create_core_config_tab(self):
        """核心配置界面（优化：避免重复定义show_key_var）"""
        main_frame = ttk.Frame(self.tab_core)
        main_frame.pack(fill="x", padx=30, pady=20)

        tip_label = ttk.Label(main_frame, text="📌 适配2026.3.8版本 | 先查看配置文件确认键名 | 保存后自动验证",
                              font=("", 10, "bold"), foreground="#D32F2F")
        tip_label.pack(anchor="w", pady=10)

        # 1. 厂商选择
        line1 = ttk.Frame(main_frame)
        line1.pack(fill="x", pady=8)
        ttk.Label(line1, text="大模型厂商：", width=15, font=("", 10)).pack(side="left")
        self.provider_combo = ttk.Combobox(
            line1, textvariable=self.selected_provider, values=list(self.model_providers.keys()),
            state="readonly", width=40, font=("", 10)
        )
        self.provider_combo.pack(side="left", padx=5)
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

        # 2. API密钥
        line2 = ttk.Frame(main_frame)
        line2.pack(fill="x", pady=8)
        ttk.Label(line2, text="API密钥：", width=15, font=("", 10)).pack(side="left")
        self.api_key_entry = ttk.Entry(
            line2, textvariable=self.api_key, width=50, show="*", font=("", 10)
        )
        self.api_key_entry.pack(side="left", padx=5)

        ttk.Checkbutton(
            line2, text="显示密钥", variable=self.show_key_var,
            command=lambda: self.api_key_entry.config(show="" if self.show_key_var.get() else "*")
        ).pack(side="left", padx=10)
        ttk.Button(
            line2, text="🔗 获取API密钥", command=self.open_api_key_url, width=12
        ).pack(side="left", padx=5)

        # 3. 模型选择
        line3 = ttk.Frame(main_frame)
        line3.pack(fill="x", pady=8)
        ttk.Label(line3, text="默认模型：", width=15, font=("", 10)).pack(side="left")
        self.model_combo = ttk.Combobox(
            line3, textvariable=self.selected_model, state="readonly", width=40, font=("", 10)
        )
        self.model_combo.pack(side="left", padx=5)
        self.on_provider_change(None)  # 初始化模型列表

        # 4. 核心参数（优化：输入验证）
        line4 = ttk.Frame(main_frame)
        line4.pack(fill="x", pady=8)
        ttk.Label(line4, text="温度（0-1）：", width=15, font=("", 10)).pack(side="left")
        temp_entry = ttk.Entry(line4, textvariable=self.temperature, width=10, font=("", 10))
        temp_entry.pack(side="left", padx=5)
        temp_entry.bind("<FocusOut>", lambda e: self.validate_temp_input())  # 失去焦点验证
        ttk.Label(line4, text="（默认0.7，越高越创意）", font=("", 9), foreground="#666").pack(side="left", padx=5)

        ttk.Label(line4, text="最大令牌：", width=12, font=("", 10)).pack(side="left", padx=20)
        tokens_entry = ttk.Entry(line4, textvariable=self.max_tokens, width=10, font=("", 10))
        tokens_entry.pack(side="left", padx=5)
        tokens_entry.bind("<FocusOut>", lambda e: self.validate_tokens_input())  # 失去焦点验证
        ttk.Label(line4, text="（默认4096）", font=("", 9), foreground="#666").pack(side="left", padx=5)

        # 5. 推理模式
        line5 = ttk.Frame(main_frame)
        line5.pack(fill="x", pady=8)
        ttk.Checkbutton(line5, text="启用推理模式（reasoning）", variable=self.reasoning).pack(side="left", padx=5)

        # 配置操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=20)
        ttk.Button(btn_frame, text="📖 读取配置", command=self.load_config, width=15).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_config, width=15, style="Accent.TButton").pack(
            side="left", padx=8)
        ttk.Button(btn_frame, text="✅ 验证配置", command=self.validate_config, width=15).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔄 重置配置", command=self.reset_config, width=15).pack(side="left", padx=8)

    def validate_temp_input(self):
        """验证温度输入（0-1之间）"""
        try:
            temp = float(self.temperature.get())
            if temp < 0 or temp > 1:
                raise ValueError
        except:
            self.temperature.set("0.7")
            run_on_main_thread(messagebox.showwarning, "输入验证", "温度值必须在0-1之间，已重置为默认值0.7",
                               root=self.root)

    def validate_tokens_input(self):
        """验证最大令牌输入（正整数）"""
        try:
            tokens = int(self.max_tokens.get())
            if tokens <= 0:
                raise ValueError
        except:
            self.max_tokens.set("4096")
            run_on_main_thread(messagebox.showwarning, "输入验证", "最大令牌必须为正整数，已重置为默认值4096",
                               root=self.root)

    def create_advanced_config_tab(self):
        """高级设置界面（无修改）"""
        main_frame = ttk.Frame(self.tab_advanced)
        main_frame.pack(fill="x", padx=30, pady=20)

        # 1. 时区与语言
        section1 = ttk.LabelFrame(main_frame, text="🌐 区域与语言", relief="groove")
        section1.pack(fill="x", pady=10, padx=5)

        line1 = ttk.Frame(section1)
        line1.pack(fill="x", pady=10, padx=20)
        ttk.Label(line1, text="时区：", width=10, font=("", 10)).pack(side="left")
        ttk.Entry(line1, textvariable=self.timezone, width=20, font=("", 10)).pack(side="left", padx=5)
        ttk.Label(line1, text="（默认 Asia/Shanghai）", font=("", 9), foreground="#666").pack(side="left", padx=5)

        line2 = ttk.Frame(section1)
        line2.pack(fill="x", pady=10, padx=20)
        ttk.Label(line2, text="语言：", width=10, font=("", 10)).pack(side="left")
        lang_combo = ttk.Combobox(line2, textvariable=self.language, values=["zh-CN", "en-US"], state="readonly",
                                  width=18, font=("", 10))
        lang_combo.pack(side="left", padx=5)

        # 2. 日志设置
        section2 = ttk.LabelFrame(main_frame, text="🎛️ 日志行为设置", relief="groove")
        section2.pack(fill="x", pady=10, padx=5)

        line3 = ttk.Frame(section2)
        line3.pack(fill="x", pady=10, padx=20)
        ttk.Checkbutton(line3, text="详细输出（verbose）", variable=self.verbose_mode).pack(side="left", padx=20)
        ttk.Checkbutton(line3, text="静默模式（silent）", variable=self.silent_mode).pack(side="left", padx=20)

        # 保存按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=20)
        ttk.Button(btn_frame, text="💾 保存所有高级设置", command=self.save_config, width=25,
                   style="Accent.TButton").pack(side="left", padx=8)

    def create_config_file_tab(self):
        """配置文件管理界面（路径修复版+容错优化）"""
        main_frame = ttk.Frame(self.tab_config_file)
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # 配置文件路径
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=10)
        ttk.Label(path_frame, text="配置文件路径：", font=("", 10, "bold")).pack(side="left")
        self.config_path_label = ttk.Label(path_frame, text="未获取", foreground="#1976D2")
        self.config_path_label.pack(side="left", padx=10)
        ttk.Button(path_frame, text="🔍 获取路径", command=self.get_config_file_path, width=10).pack(side="left",
                                                                                                    padx=10)
        ttk.Button(path_frame, text="📂 打开文件夹", command=self.open_config_folder, width=10).pack(side="left", padx=5)

        # 配置文件内容预览（优化：只读保护）
        preview_frame = ttk.LabelFrame(main_frame, text="配置文件内容预览")
        preview_frame.pack(fill="both", expand=True, pady=10)
        self.config_preview_text = scrolledtext.ScrolledText(preview_frame, font=("Consolas", 9), height=20,
                                                             state="disabled")
        self.config_preview_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="🔄 刷新预览", command=self.refresh_config_preview, width=15).pack(side="left",
                                                                                                     padx=8)
        ttk.Button(btn_frame, text="💾 备份配置文件", command=self.backup_config_file, width=15).pack(side="left",
                                                                                                     padx=8)
        ttk.Button(btn_frame, text="📥 还原配置文件", command=self.restore_config_file, width=15).pack(side="left",
                                                                                                      padx=8)
        ttk.Button(btn_frame, text="✏️ 手动编辑", command=self.edit_config_file, width=15).pack(side="left", padx=8)

    def create_install_wizard_tab(self):
        """安装向导界面（优化：进度条平滑+按钮状态）"""
        main_frame = ttk.Frame(self.tab_install_wizard)
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # 步骤指示器
        step_frame = ttk.Frame(main_frame)
        step_frame.pack(fill="x", pady=15)
        self.step_labels = []
        for idx, step_text in enumerate(AppConst.INSTALL_STEPS):
            step_label = ttk.Label(step_frame, text=step_text, font=("", 10), foreground="#666", relief="flat",
                                   borderwidth=2, padding=(15, 8))
            step_label.pack(side="left", padx=5)
            self.step_labels.append(step_label)
            if idx < len(AppConst.INSTALL_STEPS) - 1:
                ttk.Label(step_frame, text="→", font=("", 10)).pack(side="left")

        # 安装说明
        content_frame = ttk.LabelFrame(main_frame, text="安装说明（2026.3.8版本）", relief="groove")
        content_frame.pack(fill="both", expand=True, pady=15)

        desc_text = tk.Text(content_frame, height=8, font=("", 10), wrap="word", state="normal")
        desc_text.insert(tk.END, """
【OpenClaw 2026.3.8 安装向导说明】
1. 自动检测Node.js环境（需18.x LTS版本）
2. 自动配置淘宝镜像，解决网络问题
3. 自动安装最新版OpenClaw 2026.3.8
4. 自动解析~路径为Windows真实路径，修复配置文件访问问题
5. 全程无需手动敲命令，严格遵循2026.3.8版本规范

⚠️ 安装过程需要管理员权限
⚠️ 安装完成后请先查看配置文件，确认配置键名
⚠️ 配置键名必须与配置文件一致，否则保存失败
""")
        desc_text.config(state="disabled")
        desc_text.pack(fill="x", padx=20, pady=10)

        # 进度条（优化：初始值0）
        progress_frame = ttk.Frame(content_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(progress_frame, text="安装进度：", font=("", 10)).pack(side="left")
        self.install_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate",
                                                value=0)
        self.install_progress.pack(side="left", padx=10)
        self.progress_label = ttk.Label(progress_frame, text="0%", font=("", 10))
        self.progress_label.pack(side="left", padx=10)

        # 安装控制按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        self.start_install_btn = ttk.Button(btn_frame, text="🚀 安装OpenClaw 2026.3.8", command=self.start_full_install,
                                            width=20, style="Accent.TButton")
        self.start_install_btn.pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🧹 彻底卸载", command=self.uninstall_openclaw, width=15).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🔄 重置环境", command=self.reset_install_env, width=15).pack(side="left", padx=10)

        self.update_install_step(0)

    # ====================== 核心功能实现（路径修复+鲁棒性优化版） ======================
    def log(self, msg: str, tag: Optional[str] = "info"):
        """日志输出（线程安全+长度限制）"""
        try:
            timestamp = time.strftime("[%H:%M:%S]")
            log_line = f"{timestamp} {msg}"
            self.log_data.append((log_line, tag))
            if len(self.log_data) > AppConst.LOG_MAX_LINES:
                self.log_data = self.log_data[-AppConst.LOG_MAX_LINES:]
            self.output_queue.put((log_line, tag))
        except Exception as e:
            print(f"日志记录失败：{e}")  # 降级输出到控制台

    def process_queue(self):
        """处理日志队列（线程安全+避免卡死）"""
        try:
            while True:
                try:
                    log_line, tag = self.output_queue.get(block=False, timeout=0.01)
                    self.log_text.config(state="normal")
                    # 避免重复换行
                    if self.log_text.get("end-2c", "end-1c") != "\n":
                        self.log_text.insert(tk.END, log_line + "\n", tag)
                    else:
                        self.log_text.insert(tk.END, log_line + "\n", tag)
                    self.log_text.see(tk.END)
                    self.log_text.config(state="disabled")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"日志处理失败：{e}")
        finally:
            self.root.after(100, self.process_queue)

    def run_powershell(self, cmd_list: List[str], desc: str) -> Tuple[bool, List[str]]:
        """执行PowerShell命令（优化：编码+超时+容错）"""
        try:
            if not cmd_list or (len(cmd_list) > 0 and cmd_list[0] is None):
                self.log(f"❌ {desc} 失败：命令为空或OpenClaw路径未找到", "error")
                return False, ["命令参数错误"]

            # 过滤空值参数+处理路径空格
            cmd_list = [item.strip() for item in cmd_list if item and item.strip()]
            if not cmd_list:
                self.log(f"❌ {desc} 失败：过滤后命令为空", "error")
                return False, ["过滤后命令为空"]

            # 构建安全命令
            cmd_parts = []
            for idx, item in enumerate(cmd_list):
                if idx == 0 and os.path.exists(item) and " " in item:
                    cmd_parts.append(f'& "{item}"')
                elif " " in item and not item.startswith('"') and not item.endswith('"'):
                    cmd_parts.append(f'"{item}"')
                else:
                    cmd_parts.append(item)
            cmd_str = " ".join(cmd_parts)

            # 执行命令（优化：编码+创建标志）
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-NoLogo", "-NonInteractive", "-Command", cmd_str],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=AppConst.DEFAULT_TIMEOUT,
                encoding='utf-8',
                errors='replace'  # 编码错误替换
            )

            # 处理输出
            output = [line.strip() for line in result.stdout.split("\n") if line.strip()]
            error = [line.strip() for line in result.stderr.split("\n") if line.strip()]

            if result.returncode == 0:
                self.log(f"✅ {desc} 成功", "success")
                return True, output
            else:
                error_msg = " | ".join(error) if error else "未知错误"
                if "Unrecognized key" in error_msg or "not found" in error_msg.lower():
                    self.log(f"⚠️ {desc}：配置键不被支持 - {error_msg}", "warning")
                    return False, error
                elif "missing required argument" in error_msg:
                    self.log(f"⚠️ {desc}：参数缺失 - {error_msg}", "warning")
                    return False, error
                else:
                    self.log(f"❌ {desc} 失败：{error_msg}", "error")
                    return False, error

        except subprocess.TimeoutExpired:
            self.log(f"❌ {desc} 失败：执行超时（{AppConst.DEFAULT_TIMEOUT}秒）", "error")
            return False, [f"执行超时（{AppConst.DEFAULT_TIMEOUT}秒）"]
        except Exception as e:
            self.log(f"❌ {desc} 异常：{str(e)}", "error")
            return False, [str(e)]

    def get_config_file_path(self):
        """获取配置文件路径（修复~路径解析+容错+线程安全）"""
        try:
            if not self.openclaw_path:
                self.log("❌ OpenClaw路径未找到", "error")
                run_on_main_thread(messagebox.showerror, "错误", "未检测到OpenClaw，请先安装", root=self.root)
                return None

            # 执行官方命令获取路径
            success, output = self.run_powershell([self.openclaw_path, "config", "file"], "获取配置文件路径")
            if success and output:
                raw_path = output[0].strip()
                # 核心修复：把~解析成Windows真实的用户家目录
                config_path = os.path.abspath(os.path.expanduser(raw_path))
                self.config_file_path = config_path

                # 线程安全更新UI
                run_on_main_thread(self.config_path_label.config, text=config_path, root=self.root)
                run_on_main_thread(self.info_label.config,
                                   text=f"版本：{self.openclaw_version} | 网关端口：{self.gateway_port.get()} | 配置文件：已获取",
                                   root=self.root)

                self.log(f"✅ 配置文件真实路径：{config_path}", "success")
                # 自动刷新预览
                self.refresh_config_preview()
                return config_path
            else:
                self.log("❌ 获取配置文件路径失败", "error")
                run_on_main_thread(messagebox.showerror, "错误",
                                   "获取配置文件路径失败，请手动执行 openclaw config file 命令", root=self.root)
                return None
        except Exception as e:
            self.log(f"❌ 获取配置文件路径异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "错误", f"获取配置文件路径异常：{str(e)}", root=self.root)
            return None

    def refresh_config_preview(self):
        """刷新配置文件预览（修复路径解析+JSON容错）"""
        try:
            # 先检查路径是否有效
            if not self.config_file_path:
                self.log("⚠️ 请先点击「获取路径」获取配置文件地址", "warning")
                return

            # 展开路径，确保是真实绝对路径
            config_path = os.path.abspath(os.path.expanduser(self.config_file_path))

            # 检查文件是否存在
            if not os.path.exists(config_path):
                self.log(f"⚠️ 配置文件不存在：{config_path}", "warning")
                # 清空预览并提示（线程安全）
                run_on_main_thread(self._update_config_preview,
                                   f"# 配置文件不存在：{config_path}\n# 请手动创建该文件，示例内容：\n{{\n  \"gateway\": {{\n    \"port\": 18789\n  }},\n  \"provider\": {{\n    \"default\": \"moonshot\",\n    \"apiKey\": \"你的API密钥\"\n  }}\n}}",
                                   root=self.root)
                return

            # 读取文件（容错编码）
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # 验证JSON格式
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.log(f"⚠️ 配置文件JSON格式错误：{str(e)}", "warning")
                content = f"# 配置文件JSON格式错误：{str(e)}\n# 原始内容：\n{content}"

            # 更新预览（线程安全）
            run_on_main_thread(self._update_config_preview, content, root=self.root)
            self.log("✅ 配置文件预览已刷新", "success")
        except Exception as e:
            self.log(f"❌ 读取配置文件失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "错误", f"读取配置文件失败：{str(e)}", root=self.root)

    def _update_config_preview(self, content: str):
        """内部方法：更新配置预览（线程安全）"""
        self.config_preview_text.config(state="normal")
        self.config_preview_text.delete(1.0, tk.END)
        self.config_preview_text.insert(tk.END, content)
        self.config_preview_text.config(state="disabled")

    def open_config_file(self):
        """打开配置文件（修复路径解析+容错+创建空文件）"""
        try:
            # 先获取/验证路径
            if not self.config_file_path:
                self.get_config_file_path()

            if not self.config_file_path:
                run_on_main_thread(messagebox.showerror, "错误", "未获取到配置文件路径，请先点击「获取路径」",
                                   root=self.root)
                return

            # 解析真实路径
            config_path = os.path.abspath(os.path.expanduser(self.config_file_path))

            # 检查文件是否存在，不存在则创建
            if not os.path.exists(config_path):
                try:
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    default_config = {
                        "gateway": {"port": int(AppConst.DEFAULT_PORT)},
                        "provider": {"default": "moonshot", "apiKey": ""}
                    }
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                    self.log(f"✅ 已创建默认配置文件：{config_path}", "success")
                except Exception as e:
                    self.log(f"❌ 创建配置文件失败：{str(e)}", "error")
                    run_on_main_thread(messagebox.showerror, "错误", f"创建配置文件失败：{str(e)}", root=self.root)
                    return

            # 打开文件（兼容不同系统）
            if os.name == 'nt':
                os.startfile(config_path)
            else:
                subprocess.run(['open', config_path])  # 兼容macOS/Linux
            self.log(f"📄 打开配置文件：{config_path}", "info")
        except Exception as e:
            self.log(f"❌ 打开配置文件失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"打开配置文件失败：{str(e)}", root=self.root)

    def open_config_folder(self):
        """打开配置文件所在文件夹（修复路径解析+容错）"""
        try:
            if not self.config_file_path:
                self.get_config_file_path()

            if not self.config_file_path:
                run_on_main_thread(messagebox.showerror, "错误", "未获取到配置文件路径", root=self.root)
                return

            config_path = os.path.abspath(os.path.expanduser(self.config_file_path))
            parent_dir = os.path.dirname(config_path)

            # 确保文件夹存在
            os.makedirs(parent_dir, exist_ok=True)

            if os.path.exists(parent_dir):
                if os.name == 'nt':
                    os.startfile(parent_dir)
                else:
                    subprocess.run(['open', parent_dir])
                self.log(f"📂 打开配置文件夹：{parent_dir}", "info")
            else:
                run_on_main_thread(messagebox.showerror, "错误", f"文件夹不存在：{parent_dir}", root=self.root)
        except Exception as e:
            self.log(f"❌ 打开配置文件夹失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "错误", f"打开配置文件夹失败：{str(e)}", root=self.root)

    def backup_config_file(self):
        """备份配置文件（修复路径解析+容错）"""
        try:
            if not self.config_file_path:
                run_on_main_thread(messagebox.showwarning, "提示", "请先获取配置文件路径", root=self.root)
                return

            # 解析真实路径
            config_path = os.path.abspath(os.path.expanduser(self.config_file_path))
            if not os.path.exists(config_path):
                run_on_main_thread(messagebox.showwarning, "提示", "配置文件不存在，无法备份", root=self.root)
                return

            # 选择备份路径
            backup_path = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(config_path)[1],
                filetypes=[("配置文件", f"*{os.path.splitext(config_path)[1]}"), ("所有文件", "*.*")],
                title="备份配置文件",
                initialfile=f"openclaw_config_backup_{time.strftime('%Y%m%d_%H%M%S')}{os.path.splitext(config_path)[1]}"
            )

            if backup_path:
                import shutil
                shutil.copy2(config_path, backup_path)
                self.log(f"✅ 配置文件已备份到：{backup_path}", "success")
                run_on_main_thread(messagebox.showinfo, "成功", f"配置文件已备份到：\n{backup_path}", root=self.root)
        except Exception as e:
            self.log(f"❌ 备份配置文件失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"备份失败：{str(e)}", root=self.root)

    def restore_config_file(self):
        """还原配置文件（修复路径解析+容错）"""
        try:
            if not self.config_file_path:
                run_on_main_thread(messagebox.showwarning, "提示", "请先获取配置文件路径", root=self.root)
                return

            # 选择备份文件
            restore_path = filedialog.askopenfilename(
                filetypes=[("配置文件", f"*{os.path.splitext(self.config_file_path)[1]}"), ("所有文件", "*.*")],
                title="选择配置备份文件"
            )

            if restore_path:
                # 解析真实路径
                config_path = os.path.abspath(os.path.expanduser(self.config_file_path))
                import shutil
                shutil.copy2(restore_path, config_path)
                self.log(f"✅ 配置文件已从 {restore_path} 还原", "success")
                self.refresh_config_preview()
                run_on_main_thread(messagebox.showinfo, "成功", "配置文件已还原！", root=self.root)
        except Exception as e:
            self.log(f"❌ 还原配置文件失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"还原失败：{str(e)}", root=self.root)

    def edit_config_file(self):
        """手动编辑配置文件（直接调用open_config_file）"""
        self.open_config_file()

    def load_config(self):
        """读取配置（仅读取本地GUI备份+容错）"""
        try:
            # 优先读取本地GUI备份
            gui_config_path = os.path.join(os.path.expanduser("~"), "openclaw_gui_config.json")
            if not os.path.exists(gui_config_path):
                run_on_main_thread(messagebox.showwarning, "提示",
                                   "未找到本地GUI配置备份\n建议先查看配置文件，手动编辑后保存", root=self.root)
                self.log("⚠️ 未找到本地GUI配置备份", "warning")
                return

            with open(gui_config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 线程安全还原到GUI界面
            run_on_main_thread(self._restore_gui_config, config_data, root=self.root)

            self.log(f"✅ 从本地加载GUI配置完成：{gui_config_path}", "success")
            run_on_main_thread(messagebox.showinfo, "成功", "已加载本地GUI配置！", root=self.root)
        except json.JSONDecodeError as e:
            self.log(f"❌ 加载配置失败：JSON格式错误 - {str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"加载配置失败：JSON格式错误\n{str(e)}", root=self.root)
        except Exception as e:
            self.log(f"❌ 加载配置失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"加载配置失败：{str(e)}", root=self.root)

    def _restore_gui_config(self, config_data: dict):
        """内部方法：还原GUI配置（线程安全）"""
        if "provider" in config_data:
            self.selected_provider.set(config_data["provider"])
            self.on_provider_change(None)
        if "model" in config_data:
            self.selected_model.set(config_data["model"])
        if "api_key" in config_data:
            self.api_key.set(config_data["api_key"])
        if "temperature" in config_data:
            self.temperature.set(config_data["temperature"])
        if "max_tokens" in config_data:
            self.max_tokens.set(config_data["max_tokens"])
        if "reasoning" in config_data:
            self.reasoning.set(config_data["reasoning"])
        if "port" in config_data:
            self.gateway_port.set(config_data["port"])
            self.apply_port_config()

    def save_config(self):
        """保存配置（仅保存本地GUI备份+验证）"""
        try:
            api_key = self.api_key.get().strip()
            if not api_key:
                run_on_main_thread(messagebox.showwarning, "提示", "请填写API密钥", root=self.root)
                return

            # 验证端口
            try:
                port = int(self.gateway_port.get())
                if port < 1 or port > 65535:
                    raise ValueError
            except:
                run_on_main_thread(messagebox.showwarning, "提示", "端口号必须是1-65535之间的整数", root=self.root)
                return

            # 仅保存到本地GUI备份
            config_data = {
                "provider": self.selected_provider.get(),
                "model": self.selected_model.get(),
                "api_key": api_key,
                "temperature": self.temperature.get(),
                "max_tokens": self.max_tokens.get(),
                "reasoning": self.reasoning.get(),
                "port": self.gateway_port.get()
            }

            gui_config_path = os.path.join(os.path.expanduser("~"), "openclaw_gui_config.json")
            with open(gui_config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.log(f"✅ GUI参数已备份到：{gui_config_path}", "success")
            self.log("ℹ️ 提示：请查看配置文件，手动编辑真实配置键", "info")
            run_on_main_thread(messagebox.showinfo, "成功",
                               f"GUI参数已备份到本地！\n请查看配置文件，手动编辑真实配置键\n路径：{gui_config_path}",
                               root=self.root)
        except Exception as e:
            self.log(f"❌ 备份参数失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"备份失败：{str(e)}", root=self.root)

    def validate_config(self):
        """验证配置（优化：容错）"""
        try:
            if not self.openclaw_path:
                run_on_main_thread(messagebox.showwarning, "提示", "请先安装OpenClaw", root=self.root)
                return

            # 执行官方验证命令
            success, output = self.run_powershell([self.openclaw_path, "config", "validate"], "验证配置")
            if success:
                run_on_main_thread(messagebox.showinfo, "成功", "配置验证通过！", root=self.root)
            else:
                run_on_main_thread(messagebox.showerror, "失败", "配置验证失败！\n请查看日志", root=self.root)
        except Exception as e:
            self.log(f"❌ 验证配置异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"验证配置异常：{str(e)}", root=self.root)

    def reset_config(self):
        """重置配置（线程安全）"""
        try:
            if not run_on_main_thread(messagebox.askyesno, "确认", "确定要重置所有配置吗？", root=self.root):
                return

            # 线程安全重置GUI变量
            run_on_main_thread(self._reset_gui_vars, root=self.root)

            self.log("✅ GUI配置已重置为默认值", "success")
            run_on_main_thread(messagebox.showinfo, "成功", "GUI配置已重置为默认值！", root=self.root)
        except Exception as e:
            self.log(f"❌ 重置配置失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"重置配置失败：{str(e)}", root=self.root)

    def _reset_gui_vars(self):
        """内部方法：重置GUI变量（线程安全）"""
        self.selected_provider.set("Moonshot AI（Kimi）")
        self.api_key.set("")
        self.temperature.set("0.7")
        self.max_tokens.set("4096")
        self.reasoning.set(True)
        self.timezone.set("Asia/Shanghai")
        self.language.set("zh-CN")
        self.verbose_mode.set(False)
        self.silent_mode.set(False)
        self.gateway_port.set(AppConst.DEFAULT_PORT)
        self.on_provider_change(None)
        self.api_key_entry.config(show="*")
        self.show_key_var.set(False)

    def view_all_config(self):
        """查看所有配置（优化：窗口大小+容错）"""
        try:
            if not self.openclaw_path:
                run_on_main_thread(messagebox.showwarning, "提示", "请先安装OpenClaw", root=self.root)
                return

            # 执行官方命令读取所有配置
            success, all_config = self.run_powershell([self.openclaw_path, "config", "get"], "读取所有配置")

            if success and all_config:
                config_text = "\n".join(all_config)
                # 创建新窗口（线程安全）
                run_on_main_thread(self._show_config_window, config_text, root=self.root)
                self.log("✅ 读取所有配置成功", "success")
            else:
                self.log("❌ 读取所有配置失败", "error")
                run_on_main_thread(messagebox.showerror, "失败", "读取所有配置失败，请查看日志", root=self.root)
        except Exception as e:
            self.log(f"❌ 查看所有配置异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"查看所有配置异常：{str(e)}", root=self.root)

    def _show_config_window(self, config_text: str):
        """内部方法：显示配置窗口（线程安全）"""
        config_window = tk.Toplevel(self.root)
        config_window.title("所有配置（2026.3.8）")
        config_window.geometry("800x600")
        config_window.minsize(600, 400)

        text_widget = scrolledtext.ScrolledText(config_window, font=("Consolas", 9))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, config_text)
        text_widget.config(state="disabled")

        # 添加复制按钮
        def copy_config():
            self.root.clipboard_clear()
            self.root.clipboard_append(config_text)
            messagebox.showinfo("成功", "配置内容已复制到剪贴板！")

        btn = ttk.Button(config_window, text="📋 复制所有配置", command=copy_config)
        btn.pack(pady=5)

    def on_provider_change(self, event=None):
        """切换厂商时更新模型列表（容错）"""
        try:
            provider = self.selected_provider.get()
            if provider in self.model_providers:
                models = self.model_providers[provider]["models"]
                self.model_combo["values"] = models
                if models:
                    self.model_combo.current(0)
                else:
                    self.model_combo.set("")
            else:
                self.model_combo["values"] = []
                self.model_combo.set("")
        except Exception as e:
            self.log(f"❌ 切换厂商异常：{str(e)}", "error")

    def open_api_key_url(self):
        """打开API密钥获取页面（容错）"""
        try:
            provider = self.selected_provider.get()
            if provider in self.model_providers:
                url = self.model_providers[provider]["api_key_url"]
                webbrowser.open(url)
                self.log(f"🌐 打开{provider} API密钥获取页面", "info")
            else:
                self.log(f"⚠️ 未找到{provider}的API密钥地址", "warning")
        except Exception as e:
            self.log(f"❌ 打开API密钥页面失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"打开页面失败：{str(e)}", root=self.root)

    def apply_port_config(self):
        """应用端口配置（优化：验证+线程安全）"""
        try:
            port = self.gateway_port.get().strip()
            if not port.isdigit() or int(port) < 1 or int(port) > 65535:
                run_on_main_thread(messagebox.showerror, "错误", "请输入有效的端口号（1-65535）", root=self.root)
                self.gateway_port.set(AppConst.DEFAULT_PORT)
                return

            # 线程安全更新UI
            run_on_main_thread(self.info_label.config,
                               text=f"版本：{self.openclaw_version} | 网关端口：{port} | 配置文件：{self.config_file_path if self.config_file_path else '未获取'}",
                               root=self.root)
            self.log(f"🔄 网关端口已更新为：{port}，重启Gateway后生效", "config")
        except Exception as e:
            self.log(f"❌ 应用端口配置失败：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "错误", f"应用端口配置失败：{str(e)}", root=self.root)

    def start_gateway(self):
        """启动Gateway（优化：状态检查+线程安全）"""
        try:
            if not self.is_installed or not self.openclaw_path:
                run_on_main_thread(messagebox.showwarning, "提示", "请先安装OpenClaw 2026.3.8", root=self.root)
                return
            if self.gateway_running:
                run_on_main_thread(messagebox.showinfo, "提示", "Gateway已在运行中！", root=self.root)
                return
            if self.is_busy:
                run_on_main_thread(messagebox.showwarning, "提示", "当前有操作正在进行，请稍后再试", root=self.root)
                return

            def start_task():
                try:
                    self.is_busy = True
                    self.log("🚀 执行Gateway启动命令（2026.3.8）...", "gateway")

                    port = self.gateway_port.get().strip()
                    if not port.isdigit() or int(port) < 1 or int(port) > 65535:
                        port = AppConst.DEFAULT_PORT
                        self.log(f"⚠️ 端口无效，使用默认端口：{port}", "warning")

                    cmd = [self.openclaw_path, "gateway", "start", "--port", port]
                    if self.verbose_mode.get():
                        cmd.append("--verbose")
                    if self.silent_mode.get():
                        cmd.append("--silent")

                    self.log(f"⚙️ 执行命令：{' '.join(cmd)}", "info")
                    success, output = self.run_powershell(cmd, "启动Gateway（2026.3.8）")

                    if success:
                        self.log("✅ Gateway启动命令执行成功，等待服务就绪...", "success")
                        time.sleep(5)
                        self.refresh_gateway_status()
                        if self.gateway_running:
                            self.log(f"✅ Gateway已成功运行，端口：{port}", "success")
                        else:
                            self.log("⚠️ 启动命令执行成功，但服务检测超时", "warning")
                    else:
                        self.log("❌ Gateway启动失败，请检查参数", "error")
                        run_on_main_thread(messagebox.showerror, "失败",
                                           "Gateway启动失败！\n请先执行 openclaw gateway start --help 查看支持的参数",
                                           root=self.root)
                finally:
                    self.is_busy = False

            threading.Thread(target=start_task, daemon=True).start()
        except Exception as e:
            self.log(f"❌ 启动Gateway异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"启动Gateway异常：{str(e)}", root=self.root)

    def stop_gateway(self):
        """停止Gateway（优化：状态检查+线程安全）"""
        try:
            if not self.gateway_running:
                run_on_main_thread(messagebox.showinfo, "提示", "Gateway未运行！", root=self.root)
                return
            if self.is_busy:
                run_on_main_thread(messagebox.showwarning, "提示", "当前有操作正在进行，请稍后再试", root=self.root)
                return

            self.log("⏹️ 执行Gateway停止命令（2026.3.8）...", "gateway")
            success, _ = self.run_powershell([self.openclaw_path, "gateway", "stop"], "停止Gateway（2026.3.8）")
            if success:
                self.log("✅ Gateway停止命令执行成功", "success")
                time.sleep(3)
                self.refresh_gateway_status()
            else:
                self.log("❌ Gateway停止失败", "error")
        except Exception as e:
            self.log(f"❌ 停止Gateway异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"停止Gateway异常：{str(e)}", root=self.root)

    def restart_gateway(self):
        """重启Gateway（优化：状态检查+线程安全）"""
        try:
            if not self.gateway_running:
                run_on_main_thread(messagebox.showinfo, "提示", "Gateway未运行！", root=self.root)
                return
            if self.is_busy:
                run_on_main_thread(messagebox.showwarning, "提示", "当前有操作正在进行，请稍后再试", root=self.root)
                return

            self.log("🔄 执行Gateway重启命令（2026.3.8）...", "gateway")
            port = self.gateway_port.get().strip()
            if not port.isdigit() or int(port) < 1 or int(port) > 65535:
                port = AppConst.DEFAULT_PORT

            cmd = [self.openclaw_path, "gateway", "restart", "--port", port]
            success, _ = self.run_powershell(cmd, "重启Gateway（2026.3.8）")
            if success:
                self.log("✅ Gateway重启命令执行成功", "success")
                time.sleep(5)
                self.refresh_gateway_status()
            else:
                self.log("❌ Gateway重启失败", "error")
        except Exception as e:
            self.log(f"❌ 重启Gateway异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"重启Gateway异常：{str(e)}", root=self.root)

    def refresh_gateway_status(self):
        """刷新Gateway状态（优化：双重检测+线程安全）"""
        try:
            if not self.openclaw_path:
                return

            self.log("🔍 手动刷新Gateway状态（2026.3.8）...", "info")
            port = self.gateway_port.get().strip()

            # 双重检测：端口监听 + 官方命令
            port_alive = self.check_port_listening(port)
            success, status_output = self.run_powershell([self.openclaw_path, "gateway", "status"],
                                                         "查看Gateway状态（2026.3.8）")

            # 确定最终状态
            self.gateway_running = port_alive or (success and any("running" in line.lower() for line in status_output))

            # 线程安全更新UI
            run_on_main_thread(self._update_gateway_status, self.gateway_running, port, root=self.root)

            if success and status_output:
                self.log(f"官方状态详情：\n" + "\n".join(status_output), "gateway")
        except Exception as e:
            self.log(f"❌ 刷新Gateway状态异常：{str(e)}", "error")

    def _update_gateway_status(self, is_running: bool, port: str):
        """内部方法：更新Gateway状态UI（线程安全）"""
        if is_running:
            self.gateway_status_display.config(text="✅ 运行中", foreground="#2E7D32")
            self.gateway_start_btn.config(state="disabled")
            self.gateway_stop_btn.config(state="normal")
            self.gateway_restart_btn.config(state="normal")
            self.log(f"📊 Gateway状态：运行中 | 端口：{port}", "gateway")
        else:
            self.gateway_status_display.config(text="❌ 已停止", foreground="#D32F2F")
            self.gateway_start_btn.config(state="normal")
            self.gateway_stop_btn.config(state="disabled")
            self.gateway_restart_btn.config(state="disabled")
            self.log(f"📊 Gateway状态：已停止", "gateway")

    def manual_get_dashboard_url(self):
        """手动获取Dashboard地址（优化：容错+兜底）"""
        try:
            if not self.openclaw_path or not self.gateway_running:
                run_on_main_thread(messagebox.showwarning, "提示", "请先启动Gateway", root=self.root)
                return

            self.log("🔍 手动获取Dashboard地址（2026.3.8）...", "info")
            success, output = self.run_powershell([self.openclaw_path, "dashboard"], "获取Dashboard地址（2026.3.8）")

            dashboard_url = None
            if success and output:
                for line in output:
                    line = line.strip()
                    if line.startswith("http://") or line.startswith("https://"):
                        dashboard_url = line
                        break

            # 兜底地址
            fallback_url = f"http://127.0.0.1:{self.gateway_port.get()}"
            if dashboard_url:
                self.dashboard_url = dashboard_url
                run_on_main_thread(self.web_url_display.config, text=dashboard_url, root=self.root)
                self.log(f"✅ 获取Dashboard地址成功：{dashboard_url}", "success")
            else:
                run_on_main_thread(self.web_url_display.config, text=f"获取失败，兜底地址：{fallback_url}",
                                   root=self.root)
                self.log(f"⚠️ 手动获取Dashboard地址失败，使用兜底地址：{fallback_url}", "warning")
        except Exception as e:
            self.log(f"❌ 获取Dashboard地址异常：{str(e)}", "error")
            fallback_url = f"http://127.0.0.1:{self.gateway_port.get()}"
            run_on_main_thread(self.web_url_display.config, text=f"获取失败，兜底地址：{fallback_url}", root=self.root)

    def manual_open_dashboard(self):
        """手动打开Dashboard（优化：容错+多尝试）"""
        try:
            if not self.openclaw_path:
                run_on_main_thread(messagebox.showwarning, "提示", "OpenClaw 2026.3.8未安装", root=self.root)
                return

            # 尝试1：使用已获取的地址
            if self.dashboard_url:
                try:
                    webbrowser.open(self.dashboard_url)
                    self.log(f"🌐 打开Dashboard：{self.dashboard_url}", "info")
                    return
                except Exception as e:
                    self.log(f"⚠️ 打开浏览器失败：{str(e)}", "warning")

            # 尝试2：重新获取地址
            self.manual_get_dashboard_url()
            if self.dashboard_url:
                try:
                    webbrowser.open(self.dashboard_url)
                    self.log(f"🌐 打开Dashboard：{self.dashboard_url}", "success")
                    return
                except Exception as e:
                    self.log(f"⚠️ 打开浏览器失败：{str(e)}", "warning")

            # 尝试3：使用兜底地址
            fallback_url = f"http://127.0.0.1:{self.gateway_port.get()}"
            try:
                webbrowser.open(fallback_url)
                self.log(f"🌐 打开Dashboard兜底地址：{fallback_url}", "info")
            except:
                run_on_main_thread(messagebox.showwarning, "提示", "无法打开Dashboard，请手动访问：\n" + fallback_url,
                                   root=self.root)
        except Exception as e:
            self.log(f"❌ 打开Dashboard异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showwarning, "提示",
                               "无法获取Dashboard地址，请手动执行 openclaw dashboard 命令", root=self.root)

    def extract_gateway_token(self):
        """提取Gateway认证Token（优化：容错）"""
        try:
            if not self.openclaw_path or not self.gateway_running:
                run_on_main_thread(messagebox.showwarning, "提示", "请先启动Gateway服务（2026.3.8）", root=self.root)
                return

            self.log("🔑 开始提取Gateway认证Token（2026.3.8）...", "info")

            # 执行官方token命令
            success, output = self.run_powershell([self.openclaw_path, "gateway", "token"], "提取Token（2026.3.8）")

            if success and output:
                token_info = None
                for line in output:
                    line = line.strip()
                    if line and not line.startswith("(") and not line.startswith("Warning"):
                        token_info = line
                        break

                if token_info:
                    self.log(f"✅ 成功提取Gateway Token：{token_info}", "success")
                    run_on_main_thread(messagebox.showinfo, "Gateway认证Token",
                                       f"✅ 提取到Token：\n{token_info}\n\n请复制此Token到Web界面认证框使用",
                                       root=self.root)
                else:
                    self.log("⚠️ 未️ 未在输出中找到Token", "warning")
                    run_on_main_thread(messagebox.showwarning, "提示", "未在输出中找到Token，请查看日志", root=self.root)
            else:
                self.log("❌ 提取Token失败", "error")
                run_on_main_thread(messagebox.showerror, "失败", "提取Token失败！\n请查看运行日志", root=self.root)
        except Exception as e:
            self.log(f"❌ 提取Token异常：{str(e)}", "error")
            run_on_main_thread(messagebox.showerror, "失败", f"提取Token异常：{str(e)}", root=self.root)

    def check_port_listening(self, port: str) -> bool:
        """检查端口是否被监听（优化：容错）"""
        try:
            port_int = int(port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', port_int))
                return result == 0
        except:
            return False

    def auto_detect_environment(self):
        """自动检测环境（优化：线程安全+容错）"""
        try:
            self.log("🔍 开始自动检测OpenClaw 2026.3.8环境...", "info")

            # 检测Node.js
            success, node_output = self.run_powershell(["node", "--version"], "检测Node.js版本")
            if success and node_output:
                self.node_path = "node"
                self.log(f"✅ 检测到Node.js：{node_output[0]}", "success")
            else:
                self.log("⚠️ 未检测到Node.js，请先安装Node.js 18.x LTS", "warning")

            # 检测npm
            success, npm_output = self.run_powershell(["npm", "--version"], "检测npm版本")
            if success and npm_output:
                self.npm_path = "npm"
                self.log(f"✅ 检测到npm：{npm_output[0]}", "success")
            else:
                self.log("⚠️ 未检测到npm", "warning")

            # 检测OpenClaw
            success, openclaw_output = self.run_powershell(["openclaw", "--version"], "检测OpenClaw版本")
            if success and openclaw_output:
                self.openclaw_path = "openclaw"
                self.openclaw_version = openclaw_output[0].strip() if openclaw_output else "unknown"
                self.is_installed = True
                self.log(f"✅ 检测到OpenClaw：{self.openclaw_version}", "version")

                # 自动获取配置文件路径
                self.get_config_file_path()
                # 刷新Gateway状态
                self.refresh_gateway_status()
            else:
                self.log("⚠️ 未检测到OpenClaw 2026.3.8，请先安装", "warning")
                self.is_installed = False

            # 线程安全更新状态栏
            run_on_main_thread(self.status_label.config,
                              text=f"✅ 环境检测完成 | OpenClaw：{'已安装' if self.is_installed else '未安装'}",
                              root=self.root)
            run_on_main_thread(self.info_label.config,
                              text=f"版本：{self.openclaw_version} | 网关端口：{self.gateway_port.get()} | 配置文件：{self.config_file_path if self.config_file_path else '未获取'}",
                              root=self.root)
        except Exception as e:
            self.log(f"❌ 环境检测异常：{str(e)}", "error")
            run_on_main_thread(self.status_label.config, text="❌ 环境检测失败", root=self.root)

    def start_full_install(self):
        """完整安装流程（优化：分步执行+进度条）"""
        if self.is_busy:
            messagebox.showwarning("提示", "当前有操作正在进行，请稍后再试")
            return

        def install_task():
            try:
                self.is_busy = True
                self.log("🚀 开始安装OpenClaw 2026.3.8...", "success")
                total_steps = len(AppConst.INSTALL_STEPS)

                # 步骤1：许可声明
                self.update_install_step(0)
                self.update_install_progress(10)
                time.sleep(1)

                # 步骤2：环境检测
                self.update_install_step(1)
                self.update_install_progress(20)
                self.auto_detect_environment()
                time.sleep(1)

                # 检查Node.js
                if not self.node_path:
                    self.log("⚠️ 开始安装Node.js 18.x LTS...", "info")
                    self.update_install_progress(30)
                    # 下载Node.js安装包
                    temp_dir = tempfile.gettempdir()
                    node_installer = os.path.join(temp_dir, "node-v18.20.4-x64.msi")
                    try:
                        urllib.request.urlretrieve(AppConst.NODE_DOWNLOAD_URL, node_installer)
                        self.log(f"✅ Node.js安装包下载完成：{node_installer}", "success")
                        # 执行安装
                        success, _ = self.run_powershell(["msiexec", "/i", node_installer, "/qn"], "安装Node.js")
                        if success:
                            self.log("✅ Node.js安装成功", "success")
                            self.node_path = "node"
                            self.npm_path = "npm"
                        else:
                            self.log("❌ Node.js安装失败", "error")
                            raise Exception("Node.js安装失败")
                    except Exception as e:
                        self.log(f"❌ Node.js下载/安装失败：{str(e)}", "error")
                        raise Exception(f"Node.js安装失败：{str(e)}")

                # 步骤3：安装OpenClaw
                self.update_install_step(2)
                self.update_install_progress(50)
                self.log("🚀 开始安装OpenClaw 2026.3.8...", "info")
                # 设置npm镜像
                self.run_powershell(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], "设置npm淘宝镜像")
                # 全局安装OpenClaw
                success, output = self.run_powershell(["npm", "install", "-g", "openclaw@latest"], "全局安装OpenClaw 2026.3.8")
                if not success:
                    self.log("❌ OpenClaw安装失败", "error")
                    raise Exception("OpenClaw安装失败")

                self.update_install_progress(70)
                self.log(f"✅ OpenClaw安装输出：{output}", "success")

                # 步骤4：初始化配置
                self.update_install_step(3)
                self.update_install_progress(85)
                self.log("⚙️ 初始化OpenClaw配置...", "info")
                # 初始化配置文件
                success, _ = self.run_powershell(["openclaw", "config", "init"], "初始化配置文件")
                if success:
                    self.log("✅ OpenClaw配置初始化成功", "success")
                    # 获取配置文件路径
                    self.get_config_file_path()
                else:
                    self.log("⚠️ OpenClaw配置初始化失败，将手动创建", "warning")

                # 步骤5：部署完成
                self.update_install_step(4)
                self.update_install_progress(100)
                self.log("🎉 OpenClaw 2026.3.8安装完成！", "success")
                self.is_installed = True
                self.openclaw_path = "openclaw"
                # 刷新环境信息
                self.auto_detect_environment()

                run_on_main_thread(messagebox.showinfo, "成功",
                                  "🎉 OpenClaw 2026.3.8安装完成！\n请切换到「核心配置」标签页配置API密钥。",
                                  root=self.root)
            except Exception as e:
                self.log(f"❌ 安装失败：{str(e)}", "error")
                run_on_main_thread(messagebox.showerror, "失败", f"安装失败：{str(e)}", root=self.root)
            finally:
                self.is_busy = False
                self.update_install_progress(100)

        threading.Thread(target=install_task, daemon=True).start()

    def update_install_step(self, step: int):
        """更新安装步骤（线程安全）"""
        try:
            self.install_step = step
            for idx, label in enumerate(self.step_labels):
                if idx == step:
                    label.config(foreground="#2196F3", font=("", 10, "bold"), relief="solid")
                elif idx < step:
                    label.config(foreground="#4CAF50", font=("", 10, "bold"))
                else:
                    label.config(foreground="#666", font=("", 10))
        except Exception as e:
            self.log(f"❌ 更新安装步骤失败：{str(e)}", "error")

    def update_install_progress(self, percent: int):
        """更新安装进度（线程安全）"""
        try:
            run_on_main_thread(self.install_progress.config, value=percent, root=self.root)
            run_on_main_thread(self.progress_label.config, text=f"{percent}%", root=self.root)
        except Exception as e:
            self.log(f"❌ 更新进度条失败：{str(e)}", "error")

    def uninstall_openclaw(self):
        """卸载OpenClaw（优化：容错）"""
        if not self.is_installed:
            messagebox.showwarning("提示", "未检测到OpenClaw，无需卸载")
            return

        if not messagebox.askyesno("确认", "确定要彻底卸载OpenClaw吗？\n此操作会删除全局安装的OpenClaw包"):
            return

        self.log("🧹 开始卸载OpenClaw...", "info")
        success, _ = self.run_powershell(["npm", "uninstall", "-g", "openclaw"], "卸载OpenClaw")
        if success:
            self.is_installed = False
            self.openclaw_path = None
            self.log("✅ OpenClaw卸载成功", "success")
            messagebox.showinfo("成功", "OpenClaw已成功卸载！")
            self.auto_detect_environment()
        else:
            self.log("❌ OpenClaw卸载失败", "error")
            messagebox.showerror("失败", "卸载失败，请查看日志")

    def reset_install_env(self):
        """重置安装环境（优化：容错）"""
        if not messagebox.askyesno("确认", "确定要重置安装环境吗？\n此操作会清除本地GUI配置备份"):
            return

        try:
            # 删除GUI配置备份
            gui_config_path = os.path.join(os.path.expanduser("~"), "openclaw_gui_config.json")
            if os.path.exists(gui_config_path):
                os.remove(gui_config_path)
                self.log(f"✅ 删除GUI配置备份：{gui_config_path}", "success")

            # 重置状态
            self.is_installed = False
            self.openclaw_path = None
            self.config_file_path = None
            self.gateway_running = False

            # 重置UI
            self._reset_gui_vars()
            self.update_install_step(0)
            self.update_install_progress(0)
            self.status_label.config(text="🔍 正在检测OpenClaw 2026.3.8环境...")
            self.info_label.config(text=f"版本：未知 | 网关端口：{AppConst.DEFAULT_PORT} | 配置文件：未获取")

            self.log("✅ 安装环境已重置", "success")
            messagebox.showinfo("成功", "安装环境已重置完成！")
        except Exception as e:
            self.log(f"❌ 重置环境失败：{str(e)}", "error")
            messagebox.showerror("失败", f"重置环境失败：{str(e)}")

    def on_window_close(self):
        """窗口关闭处理（优化：停止Gateway）"""
        try:
            if self.gateway_running:
                if messagebox.askyesno("确认", "Gateway仍在运行中，是否停止并退出？"):
                    self.stop_gateway()
            self.root.destroy()
        except:
            self.root.destroy()

# ====================== 程序入口 ======================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = OpenClawManager2026(root)
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败：{str(e)}")
        messagebox.showerror("启动失败", f"程序启动失败：{str(e)}")