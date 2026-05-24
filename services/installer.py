"""安装向导服务"""
import os
import time
import tempfile
import urllib.request
from utils.powershell import run_powershell
from services.environment import detect_node, detect_openclaw
from services.gateway import init_config
from app_const import AppConst


def install_node(log_callback) -> bool:
    """下载并安装 Node.js 18.x LTS"""
    log_callback("⚠️ 开始安装Node.js 18.x LTS...", "info")
    temp_dir = tempfile.gettempdir()
    node_installer = os.path.join(temp_dir, "node-v18.20.4-x64.msi")

    log_callback(f"📥 下载Node.js安装包...", "info")
    urllib.request.urlretrieve(AppConst.NODE_DOWNLOAD_URL, node_installer)
    log_callback(f"✅ Node.js安装包下载完成：{node_installer}", "success")

    success, _ = run_powershell(["msiexec", "/i", node_installer, "/qn"], "安装Node.js", log_callback)
    if success:
        log_callback("✅ Node.js安装成功", "success")
        return True
    else:
        log_callback("❌ Node.js安装失败", "error")
        return False


def install_openclaw(log_callback) -> bool:
    """通过 npm 全局安装 OpenClaw"""
    log_callback("🚀 开始安装OpenClaw...", "info")
    run_powershell(["npm", "config", "set", "registry", "https://registry.npmmirror.com"],
                   "设置npm淘宝镜像", log_callback)

    # 网络命令支持重试
    for attempt in range(3):
        success, output = run_powershell(
            ["npm", "install", "-g", "openclaw@latest"],
            f"全局安装OpenClaw (第{attempt + 1}次)",
            log_callback
        )
        if success:
            log_callback(f"✅ OpenClaw安装输出：{output}", "success")
            return True
        if attempt < 2:
            log_callback(f"⚠️ 安装失败，3秒后重试...", "warning")
            time.sleep(3)

    log_callback("❌ OpenClaw安装失败，已重试3次", "error")
    return False


def perform_install(log_callback) -> bool:
    """执行完整安装流程，返回是否成功"""
    log_callback("🚀 开始安装OpenClaw...", "success")

    # 步骤1：许可声明
    log_callback("📝 许可声明已确认", "info")
    time.sleep(1)

    # 步骤2：环境检测
    node_path = detect_node(log_callback)
    detect_openclaw(log_callback)

    if not node_path:
        if not install_node(log_callback):
            return False

    # 步骤3：安装 OpenClaw
    if not install_openclaw(log_callback):
        return False

    # 步骤4：初始化配置
    log_callback("⚙️ 初始化OpenClaw配置...", "info")
    success, _ = init_config("openclaw", log_callback)
    if success:
        log_callback("✅ OpenClaw配置初始化成功", "success")
    else:
        log_callback("⚠️ OpenClaw配置初始化失败，将手动创建", "warning")

    # 步骤5：完成
    log_callback("🎉 OpenClaw安装完成！", "success")
    return True


def uninstall_openclaw(log_callback) -> bool:
    """卸载 OpenClaw"""
    log_callback("🧹 开始卸载OpenClaw...", "info")
    success, _ = run_powershell(["npm", "uninstall", "-g", "openclaw"], "卸载OpenClaw", log_callback)
    if success:
        log_callback("✅ OpenClaw卸载成功", "success")
    else:
        log_callback("❌ OpenClaw卸载失败", "error")
    return success
