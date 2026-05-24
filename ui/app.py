"""OpenClaw 管理器 —— 侧边栏布局"""
import os
import time
import queue
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser

from utils.threading import set_root, is_admin, run_on_main_thread
from utils.powershell import run_powershell
from app_const import AppConst
from services.environment import detect_node, detect_npm, detect_openclaw
from services.gateway import (
    start_gateway, stop_gateway, restart_gateway,
    get_gateway_status, get_dashboard_url,
    check_port_listening, get_config_file_path, validate_config,
    check_latest_version, update_openclaw
)
from services.config_manager import (
    read_config_file, validate_json,
    create_default_config, save_gui_config, load_gui_config,
    backup_config_file, restore_config_file, delete_gui_config
)
from services.installer import perform_install
from ui.theme import init as init_theme, toggle as toggle_theme, get
from ui.widgets import Sidebar, LogPanel

# ---- 各页面 ----
from ui.page_gateway import GatewayPage
from ui.page_config import ConfigPage
from ui.page_files import FilesPage
from ui.page_install import InstallPage


class OpenClawApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        set_root(root)
        self.root.title("OpenClaw 管理器")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self._restore_geometry()

        # 状态
        self.node_path = None
        self.npm_path = None
        self.openclaw_path = None
        self.config_file_path = None
        self.is_installed = False
        self.is_busy = False
        self._busy_lock = threading.Lock()
        self._log_lock = threading.Lock()
        self.output_queue = queue.Queue()
        self.log_data = []
        self.openclaw_version = "unknown"
        self.latest_version = None
        self.gateway_running = False
        self.dashboard_url = ""
        self._running = True

        init_theme(self.root)
        self._build_layout()
        self._bind_keys()
        self._process_queue()

        if not is_admin():
            messagebox.showwarning("提示", "非管理员权限，部分操作可能失败！\n建议以管理员身份运行。")

        threading.Thread(target=self._auto_detect, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ========== 布局 ==========

    def _build_layout(self):
        # 侧边栏
        self.sidebar = Sidebar(self.root, self._on_nav)
        self.sidebar.add("▦", "Gateway")
        self.sidebar.add("⚙", "配置")
        self.sidebar.add("📂", "文件管理")
        self.sidebar.add("📦", "安装向导")
        self.sidebar.select(0)

        # 右侧主区域
        self._main_area = tk.Frame(self.root, bg=get("bg"))
        self._main_area.pack(side="left", fill="both", expand=True)

        # 页面容器
        self._page_container = tk.Frame(self._main_area, bg=get("bg"))
        self._page_container.pack(fill="both", expand=True)

        # 创建各页面
        self._pages = {
            0: GatewayPage(self._page_container, self),
            1: ConfigPage(self._page_container, self),
            2: FilesPage(self._page_container, self),
            3: InstallPage(self._page_container, self),
        }

        # 初始显示 Gateway 页面
        self._on_nav(0)

        # 日志面板
        self.log_panel = LogPanel(self._main_area)
        self.log_panel.pack(fill="x", side="bottom")

        # 底部状态栏
        status_bar = tk.Frame(self._main_area, bg=get("sidebar_bg"), height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._status_text = tk.Label(status_bar, text="就绪", font=("TkDefaultFont", 8),
                                     bg=get("sidebar_bg"), fg=get("fg_muted"), anchor="w")
        self._status_text.pack(side="left", padx=15)

        self._version_info = tk.Label(status_bar, text="", font=("TkDefaultFont", 8),
                                      bg=get("sidebar_bg"), fg=get("fg_muted"))
        self._version_info.pack(side="right", padx=15)

        # 主题切换（在侧边栏底部）
        theme_frame = tk.Frame(self.sidebar.frame, bg=get("sidebar_bg"))
        theme_frame.pack(side="bottom", pady=(0, 15))
        self._theme_btn = tk.Label(theme_frame, text="🌙", font=("TkDefaultFont", 16),
                                   bg=get("sidebar_bg"), fg=get("sidebar_fg"), cursor="hand2")
        self._theme_btn.pack()
        self._theme_btn.bind("<Button-1>", lambda e: self._toggle_theme())

    def _on_nav(self, idx: int):
        for i, page in self._pages.items():
            page.frame.pack_forget() if i != idx else page.frame.pack(fill="both", expand=True)

    def _toggle_theme(self):
        dark = toggle_theme() == "dark"
        init_theme(self.root)

        # 重绘 sidebar
        sb_bg = get("sidebar_bg")
        self.sidebar.frame.configure(bg=sb_bg)
        self.sidebar.select(self.sidebar._active_idx)
        self.sidebar.version_label.configure(bg=sb_bg)
        self._theme_btn.configure(bg=sb_bg, text="☀" if dark else "🌙")

        # 重绘 main area
        self._main_area.configure(bg=get("bg"))
        self._page_container.configure(bg=get("bg"))

        # 状态栏
        for w in self._status_text.master.winfo_children():
            w.configure(bg=get("sidebar_bg"))

        self.log_panel.update_theme()

        # 通知各页面
        for page in self._pages.values():
            page.on_theme_change()

    def _bind_keys(self):
        self.root.bind_all("<Control-s>", lambda e: self._save_config())
        self.root.bind_all("<Control-r>", lambda e: self._refresh_status())
        self.root.bind_all("<F5>", lambda e: self._refresh_status())

    # ========== 日志 ==========

    def log(self, msg: str, tag: str = "info"):
        try:
            ts = time.strftime("[%H:%M:%S]")
            line = f"{ts} {msg}"
            with self._log_lock:
                self.log_data.append((line, tag))
                if len(self.log_data) > AppConst.LOG_MAX_LINES:
                    self.log_data = self.log_data[-AppConst.LOG_MAX_LINES:]
            self.output_queue.put((line, tag))
        except Exception:
            print(f"log fail: {msg}")

    def _process_queue(self):
        try:
            while True:
                try:
                    line, tag = self.output_queue.get(block=False)
                    self.log_panel.append(line, tag)
                except queue.Empty:
                    break
        except Exception:
            pass
        if self._running:
            self.root.after(250, self._process_queue)

    # ========== Gateway 操作 ==========

    def start_gateway(self):
        if self._check_not_installed() or self._check_busy():
            return
        if self.gateway_running:
            messagebox.showinfo("提示", "Gateway 已在运行中！")
            return

        port = self._valid_port()
        self._write_port_to_config(port)

        def task():
            try:
                self._set_busy(True)
                self.log("正在启动 Gateway...", "gateway")
                success, output = start_gateway(self.openclaw_path,
                                                False, False, self.log)
                self._set_busy(False)  # 命令结束，立即释放 busy
                if success:
                    run_on_main_thread(self._poll_gateway_up, port, 0)
                else:
                    all_output = "\n".join(output) if output else ""
                    self.log(f"启动失败:\n{all_output}", "error")
                    run_on_main_thread(messagebox.showerror, "启动失败",
                                       f"Gateway 启动失败！\n\n{all_output[:500]}")
            except Exception as e:
                self._set_busy(False)
                self.log(f"启动异常: {e}", "error")
        threading.Thread(target=task, daemon=True).start()

    def _poll_gateway_up(self, port: str, attempt: int):
        """非阻塞轮询端口（每秒一次，最多 120 秒）"""
        if not self._running:
            return
        if check_port_listening(port):
            self.gateway_running = True
            self._update_gateway_ui(True, port)
            return
        if attempt < 120:
            self.root.after(1000, lambda: self._poll_gateway_up(port, attempt + 1))
        else:
            self.log("Gateway 启动超时（120秒）", "warning")
            self._refresh_status()

    def stop_gateway(self):
        if not self.gateway_running:
            messagebox.showinfo("提示", "Gateway 未运行！")
            return
        if self._check_busy():
            return

        def task():
            try:
                self._set_busy(True)
                self.log("正在停止 Gateway...", "gateway")
                stop_gateway(self.openclaw_path, self.log)
                self._set_busy(False)
                run_on_main_thread(self._poll_gateway_down, 0)
            except Exception as e:
                self._set_busy(False)
                self.log(f"停止异常: {e}", "error")
        threading.Thread(target=task, daemon=True).start()

    def _poll_gateway_down(self, attempt: int):
        """非阻塞轮询端口释放（每 300ms，最多 15 次）"""
        if not self._running:
            return
        port = self._pages[0].port_var.get()
        if not check_port_listening(port):
            self.gateway_running = False
            self._update_gateway_ui(False, port)
            return
        if attempt < 15:
            self.root.after(300, lambda: self._poll_gateway_down(attempt + 1))
        else:
            self._refresh_status()

    def restart_gateway(self):
        if not self.gateway_running:
            return self.start_gateway()
        if self._check_busy():
            return

        port = self._valid_port()
        self._write_port_to_config(port)

        def task():
            try:
                self._set_busy(True)
                self.log("正在重启 Gateway...", "gateway")
                restart_gateway(self.openclaw_path, self.log)
                self._set_busy(False)
                run_on_main_thread(self._poll_gateway_up, port, 0)
            except Exception as e:
                self._set_busy(False)
                self.log(f"重启异常: {e}", "error")
        threading.Thread(target=task, daemon=True).start()

    def _refresh_status(self):
        if not self.openclaw_path:
            return
        port = self._pages[0].port_var.get().strip()
        port_alive = check_port_listening(port)
        success, output = get_gateway_status(self.openclaw_path, self.log)
        self.gateway_running = port_alive or (success and any(
            "running" in l.lower() for l in output))
        run_on_main_thread(self._update_gateway_ui, self.gateway_running, port)

    def _update_gateway_ui(self, running: bool, port: str):
        self._pages[0].set_running(running)
        st = f"Gateway 运行中 :{port}" if running else "就绪"
        self._status_text.config(text=st, fg=get("success") if running else get("fg_muted"))
        if running:
            url = self.get_dashboard_url()
            if url:
                self._pages[0].set_url(url)

    def get_dashboard_url(self):
        if not self.openclaw_path or not self.gateway_running:
            return None
        url = get_dashboard_url(self.openclaw_path, self.log)
        if url:
            self.dashboard_url = url
        return url or f"http://127.0.0.1:{self._pages[0].port_var.get()}"

    def open_dashboard(self):
        url = self.get_dashboard_url()
        if url:
            webbrowser.open(url)
            self.log(f"打开 {url}", "info")

    def apply_port(self, port: str):
        if not port.isdigit() or int(port) < 1 or int(port) > 65535:
            messagebox.showerror("错误", "端口号需在 1-65535")
            self._pages[0].port_var.set(AppConst.DEFAULT_PORT)
            return
        self._update_info()
        self.log(f"端口 → {port}（重启后生效）", "config")

    # ========== 版本检查 & 更新 ==========

    def check_update(self):
        def task():
            self._set_status_text("正在查询最新版本...")
            ver = check_latest_version(self.log)
            self.latest_version = ver
            if ver:
                current = self.openclaw_version
                if current != "unknown" and ver != current:
                    run_on_main_thread(self._pages[0].show_update_available, current, ver)
                    self._set_status_text(f"发现新版本：{ver}")
                else:
                    run_on_main_thread(self._pages[0].show_update_uptodate, current)
                    self._set_status_text("已是最新版本")
            else:
                self._set_status_text("版本查询失败")
        threading.Thread(target=task, daemon=True).start()

    def do_update(self):
        if self.gateway_running:
            if not messagebox.askyesno("提示", "Gateway 正在运行中，建议先停止再更新。\n是否先停止 Gateway？"):
                return
            self.stop_gateway()

        if not messagebox.askyesno("确认", "确定要更新 OpenClaw 到最新版本吗？"):
            return

        def task():
            try:
                self._set_busy(True)
                self._pages[0].set_updating(True)
                self.log("开始更新 OpenClaw...", "version")
                success, new_ver = update_openclaw(self.log)
                if success:
                    self.openclaw_version = new_ver
                    self.sidebar.set_version(new_ver)
                    self.log(f"OpenClaw 已更新到 {new_ver}", "success")
                    # 刷新环境，重新检测路径
                    run_on_main_thread(lambda: threading.Thread(
                        target=self._auto_detect, daemon=True).start())
                    run_on_main_thread(self._pages[0].show_update_done, new_ver)
                    run_on_main_thread(messagebox.showinfo, "更新完成",
                                       f"更新到 {new_ver}！\n请在 Gateway 页面重新启动服务。")
                else:
                    self.log("更新失败，请查看上方日志了解原因", "error")
                    run_on_main_thread(self._pages[0].set_updating, False)
                    run_on_main_thread(messagebox.showerror, "更新失败",
                                       "OpenClaw 更新失败！\n\n可能原因：\n- 网络连接问题\n- npm registry 不可达\n\n请查看运行日志获取详细错误信息。")
            finally:
                self._set_busy(False)
        threading.Thread(target=task, daemon=True).start()

    # ========== 配置 ==========

    def _save_config(self):
        key = self._pages[1].api_key_var.get().strip()
        if not key:
            messagebox.showwarning("提示", "请填写 API 密钥")
            return
        port = self._pages[0].port_var.get()
        try:
            if int(port) < 1 or int(port) > 65535:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "端口号无效")
            return
        data = self._pages[1].get_values()
        data["port"] = port
        save_gui_config(data)
        self.log("配置已保存", "success")
        messagebox.showinfo("成功", "配置已保存！")

    def load_config(self):
        data = load_gui_config()
        if data is None:
            messagebox.showwarning("提示", "未找到本地配置备份")
            return
        self._pages[1].set_values(data)
        if "port" in data:
            self._pages[0].port_var.set(data["port"])
        self.log("已加载配置", "success")
        messagebox.showinfo("成功", "已加载！")

    def validate_config(self):
        if self._check_not_installed():
            return
        ok, _ = validate_config(self.openclaw_path, self.log)
        messagebox.showinfo("成功", "验证通过！") if ok else \
            messagebox.showerror("失败", "验证失败，请查看日志")

    def reset_config(self):
        if not messagebox.askyesno("确认", "重置所有配置？"):
            return
        self._pages[1].reset()
        self._pages[0].port_var.set(AppConst.DEFAULT_PORT)
        self.log("配置已重置", "success")

    # ========== 文件管理 ==========

    def get_config_path(self, silent=False):
        if not self.openclaw_path:
            if not silent:
                messagebox.showerror("错误", "未安装 OpenClaw")
            return
        path = get_config_file_path(self.openclaw_path, self.log)
        if path:
            self.config_file_path = path
            self._pages[2].set_path(path)
            self._update_info()
            self._refresh_preview()
        elif not silent:
            messagebox.showerror("错误", "获取路径失败")

    def _refresh_preview(self):
        if not self.config_file_path:
            return
        cp = os.path.abspath(os.path.expanduser(self.config_file_path))
        if not os.path.exists(cp):
            self._pages[2].set_preview(f"# 文件不存在\n# {cp}")
            return
        c = read_config_file(cp)
        if not validate_json(c):
            self.log("JSON 格式错误", "warning")
            c = f"# ⚠ JSON 格式错误\n{c}"
        self._pages[2].set_preview(c)

    def open_config_file(self):
        if not self.config_file_path:
            self.get_config_path()
        if not self.config_file_path:
            return
        cp = os.path.abspath(os.path.expanduser(self.config_file_path))
        if not os.path.exists(cp):
            create_default_config(cp, int(AppConst.DEFAULT_PORT))
            self.log(f"已创建默认配置：{cp}", "success")
        if os.name == 'nt':
            os.startfile(cp)

    def open_config_folder(self):
        if not self.config_file_path:
            self.get_config_path()
        if not self.config_file_path:
            return
        d = os.path.dirname(os.path.abspath(os.path.expanduser(self.config_file_path)))
        os.makedirs(d, exist_ok=True)
        if os.name == 'nt':
            os.startfile(d)

    def backup_config(self):
        if not self.config_file_path:
            messagebox.showwarning("提示", "请先获取配置文件路径")
            return
        cp = os.path.abspath(os.path.expanduser(self.config_file_path))
        if not os.path.exists(cp):
            messagebox.showwarning("提示", "文件不存在")
            return
        ext = os.path.splitext(cp)[1]
        dest = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[("配置文件", f"*{ext}"), ("所有", "*.*")],
            initialfile=f"openclaw_backup_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
        )
        if dest:
            backup_config_file(cp, dest)
            self.log(f"已备份 → {dest}", "success")
            messagebox.showinfo("成功", "备份完成！")

    def restore_config(self):
        if not self.config_file_path:
            messagebox.showwarning("提示", "请先获取配置文件路径")
            return
        cp = os.path.abspath(os.path.expanduser(self.config_file_path))
        ext = os.path.splitext(cp)[1]
        src = filedialog.askopenfilename(
            filetypes=[("配置文件", f"*{ext}"), ("所有", "*.*")]
        )
        if src:
            restore_config_file(src, cp)
            self._refresh_preview()
            self.log("配置已还原", "success")
            messagebox.showinfo("成功", "已还原！")

    # ========== 安装 ==========

    def start_install(self):
        if self._check_busy():
            return

        def task():
            try:
                self._set_busy(True)
                self._pages[3].set_progress(0)
                self._pages[3].update_step(0)
                self._pages[3].update_step(1)
                self._pages[3].set_progress(20)
                self._auto_detect()

                if not self.node_path:
                    self._pages[3].set_progress(35)
                    self.log("安装 Node.js...", "info")
                    ok, _ = run_powershell(["npm", "--version"], "验证npm", self.log)
                    if not ok:
                        raise Exception("Node.js 安装失败")

                self._pages[3].update_step(2)
                self._pages[3].set_progress(50)
                if not perform_install(self.log):
                    raise Exception("安装失败")

                self._pages[3].update_step(3)
                self._pages[3].set_progress(85)
                self.is_installed = True
                self.openclaw_path = "openclaw"
                self.get_config_path(silent=True)

                self._pages[3].update_step(4)
                self._pages[3].set_progress(100)
                self.log("安装完成！", "success")
                self._auto_detect()
                run_on_main_thread(messagebox.showinfo, "成功",
                                   "安装完成！\n请切换到「配置」页面配置 API 密钥。")
            except Exception as e:
                self.log(f"安装失败：{e}", "error")
                run_on_main_thread(messagebox.showerror, "失败", str(e))
            finally:
                self._set_busy(False)
        threading.Thread(target=task, daemon=True).start()

    def uninstall(self):
        if not self.is_installed:
            messagebox.showwarning("提示", "未检测到 OpenClaw")
            return
        if not messagebox.askyesno("确认", "彻底卸载 OpenClaw？"):
            return
        ok, _ = run_powershell(["npm", "uninstall", "-g", "openclaw"], "卸载", self.log)
        if ok:
            self.is_installed = False
            self.openclaw_path = None
            messagebox.showinfo("成功", "已卸载")
            self._auto_detect()
        else:
            messagebox.showerror("失败", "卸载失败")

    def reset_env(self):
        if not messagebox.askyesno("确认", "重置安装环境？"):
            return
        delete_gui_config()
        self.is_installed = False
        self.openclaw_path = None
        self.config_file_path = None
        self.gateway_running = False
        self._pages[1].reset()
        self._pages[0].port_var.set(AppConst.DEFAULT_PORT)
        self._pages[0].set_running(False)
        self._pages[3].reset()
        self._status_text.config(text="就绪")
        self._update_info()
        self.log("环境已重置", "success")
        messagebox.showinfo("成功", "已重置！")

    # ========== 其他 ==========

    def _view_all_config(self):
        # 直接读取配置文件，避免依赖 CLI 命令格式
        if not self.config_file_path:
            self.get_config_path(silent=True)
        if not self.config_file_path:
            messagebox.showerror("错误", "未获取到配置文件路径")
            return
        config_path = os.path.abspath(os.path.expanduser(self.config_file_path))
        if not os.path.exists(config_path):
            messagebox.showwarning("提示", f"配置文件不存在：\n{config_path}")
            return
        try:
            content = read_config_file(config_path)
            self._show_config_window(content)
        except Exception as e:
            messagebox.showerror("错误", f"读取失败：{e}")

    def _show_config_window(self, config_text: str):
        import json as _json
        try:
            formatted = _json.dumps(_json.loads(config_text), indent=2, ensure_ascii=False)
        except Exception:
            formatted = config_text

        win = tk.Toplevel(self.root)
        win.title("所有配置")
        win.geometry("800x600")
        win.minsize(500, 400)
        from tkinter import scrolledtext as st
        tw = st.ScrolledText(win, font=("Consolas", 9),
                             bg=get("log_bg"), fg=get("log_fg"),
                             insertbackground=get("accent"))
        tw.pack(fill="both", expand=True, padx=10, pady=10)
        tw.insert(tk.END, formatted)
        tw.config(state="disabled")
        copy_text = formatted  # capture for closure
        tk.Button(win, text="复制全部", font=("TkDefaultFont", 10),
                  command=lambda: [self.root.clipboard_clear(),
                                   self.root.clipboard_append(copy_text)]).pack(pady=5)

    # ========== 环境检测 ==========

    def _auto_detect(self):
        self.log("检测环境中...", "info")
        self.node_path = detect_node(self.log)
        self.npm_path = detect_npm(self.log)
        self.openclaw_path, self.openclaw_version, self.is_installed = detect_openclaw(self.log)
        self.sidebar.set_version(self.openclaw_version)
        run_on_main_thread(self._update_info)
        if self.is_installed:
            self.get_config_path(silent=True)
            self._refresh_status()

    def _update_info(self):
        v = self.openclaw_version
        p = self._pages[0].port_var.get()
        cfg = "已获取" if self.config_file_path else "未获取"
        self._version_info.config(text=f"v{v}  |  端口 {p}  |  配置 {cfg}")

    # ========== 辅助 ==========

    def _check_not_installed(self):
        if not self.is_installed:
            messagebox.showwarning("提示", "请先安装 OpenClaw")
            return True
        return False

    def _check_busy(self):
        if self.is_busy:
            messagebox.showwarning("提示", "操作进行中，请稍候")
            return True
        return False

    def _set_busy(self, b: bool):
        with self._busy_lock:
            self.is_busy = b
        run_on_main_thread(lambda: self._pages[0].set_busy(b))

    def _set_status_text(self, text: str):
        run_on_main_thread(lambda: self._status_text.config(text=text))

    def _valid_port(self):
        port = self._pages[0].port_var.get()
        return port if port.isdigit() and 1 <= int(port) <= 65535 else AppConst.DEFAULT_PORT

    def _write_port_to_config(self, port: str):
        """把端口号写入 OpenClaw 配置文件（新版不再支持 --port 参数）"""
        if not self.config_file_path:
            self.get_config_path(silent=True)
        if not self.config_file_path:
            return
        import json as _json
        config_path = os.path.abspath(os.path.expanduser(self.config_file_path))
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = _json.load(f)
            else:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                cfg = {}
            if "gateway" not in cfg:
                cfg["gateway"] = {}
            cfg["gateway"]["port"] = int(port)
            with open(config_path, "w", encoding="utf-8") as f:
                _json.dump(cfg, f, indent=2, ensure_ascii=False)
            self.log(f"已将端口 {port} 写入配置文件", "config")
        except Exception as e:
            self.log(f"写入端口配置失败：{e}", "warning")

    def _save_geometry(self):
        try:
            d = load_gui_config() or {}
            d["_geo"] = self.root.geometry()
            save_gui_config(d)
        except Exception:
            pass

    def _restore_geometry(self):
        try:
            d = load_gui_config()
            if d and "_geo" in d:
                self.root.geometry(d["_geo"])
        except Exception:
            pass

    def _on_close(self):
        if self.gateway_running:
            if not messagebox.askyesno("确认", "Gateway 仍在运行，是否退出？"):
                return
            self.stop_gateway()

        self._save_geometry()
        self._running = False

        # 取消所有 pending after 回调
        for page in self._pages.values():
            page.frame.pack_forget()
        self.root.destroy()
