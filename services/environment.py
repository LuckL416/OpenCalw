"""环境检测服务：Node.js / npm / OpenClaw"""
from typing import Optional
from utils.powershell import run_powershell


def detect_node(log_callback) -> Optional[str]:
    """检测 Node.js，返回路径或 None"""
    success, output = run_powershell(["node", "--version"], "检测Node.js版本", log_callback)
    if success and output:
        log_callback(f"✅ 检测到Node.js：{output[0]}", "success")
        return "node"
    log_callback("⚠️ 未检测到Node.js，请先安装Node.js 18.x LTS", "warning")
    return None


def detect_npm(log_callback) -> Optional[str]:
    """检测 npm，返回路径或 None"""
    success, output = run_powershell(["npm", "--version"], "检测npm版本", log_callback)
    if success and output:
        log_callback(f"✅ 检测到npm：{output[0]}", "success")
        return "npm"
    log_callback("⚠️ 未检测到npm", "warning")
    return None


def detect_openclaw(log_callback) -> tuple:
    """检测 OpenClaw，返回 (path, version, is_installed)"""
    success, output = run_powershell(["openclaw", "--version"], "检测OpenClaw版本", log_callback)
    if success and output:
        version = output[0].strip() if output else "unknown"
        log_callback(f"✅ 检测到OpenClaw：{version}", "version")
        return "openclaw", version, True
    log_callback("⚠️ 未检测到OpenClaw，请先安装", "warning")
    return None, "unknown", False
