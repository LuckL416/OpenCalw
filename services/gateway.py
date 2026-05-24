"""Gateway 管理服务：启停、状态检测、端口检查"""
import socket
from typing import Optional, Tuple
from utils.powershell import run_powershell


GATEWAY_START_TIMEOUT = 120  # 启动需要加载模型，可能很久
GATEWAY_CMD_TIMEOUT = 30     # 普通命令超时


def start_gateway(openclaw_path: str, verbose: bool, silent: bool,
                  log_callback) -> Tuple[bool, list]:
    """启动 Gateway（端口通过配置文件设置，不作为命令行参数）"""
    cmd = [openclaw_path, "gateway", "start"]
    if verbose:
        cmd.append("--verbose")
    if silent:
        cmd.append("--silent")

    log_callback(f"执行: {' '.join(cmd)}", "info")
    return run_powershell(cmd, "启动Gateway", log_callback, timeout=GATEWAY_START_TIMEOUT)


def stop_gateway(openclaw_path: str, log_callback) -> Tuple[bool, list]:
    """停止 Gateway"""
    return run_powershell([openclaw_path, "gateway", "stop"], "停止Gateway", log_callback,
                          timeout=GATEWAY_CMD_TIMEOUT)


def restart_gateway(openclaw_path: str, log_callback) -> Tuple[bool, list]:
    """重启 Gateway（端口通过配置文件设置）"""
    cmd = [openclaw_path, "gateway", "restart"]
    return run_powershell(cmd, "重启Gateway", log_callback, timeout=GATEWAY_START_TIMEOUT)


def get_gateway_status(openclaw_path: str, log_callback) -> Tuple[bool, list]:
    """获取 Gateway 官方状态"""
    return run_powershell([openclaw_path, "gateway", "status"], "查看Gateway状态", log_callback,
                          timeout=10)


def get_dashboard_url(openclaw_path: str, log_callback) -> Optional[str]:
    """获取 Dashboard 地址"""
    success, output = run_powershell([openclaw_path, "dashboard"], "获取Dashboard地址", log_callback,
                                     timeout=10)
    if success and output:
        for line in output:
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                return line
    return None


def extract_token(openclaw_path: str, log_callback) -> Optional[str]:
    """提取 Gateway 认证 Token"""
    success, output = run_powershell([openclaw_path, "gateway", "token"], "提取Token", log_callback)
    if success and output:
        for line in output:
            line = line.strip()
            if line and not line.startswith("(") and not line.startswith("Warning"):
                return line
    return None


def check_port_listening(port: str) -> bool:
    """检查端口是否被监听"""
    try:
        port_int = int(port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            result = s.connect_ex(('127.0.0.1', port_int))
            return result == 0
    except Exception:
        return False


def get_config_file_path(openclaw_path: str, log_callback) -> Optional[str]:
    """获取配置文件路径（解析 ~ 为真实路径）"""
    import os
    success, output = run_powershell([openclaw_path, "config", "file"], "获取配置文件路径", log_callback)
    if success and output:
        raw_path = output[0].strip()
        return os.path.abspath(os.path.expanduser(raw_path))
    return None


def validate_config(openclaw_path: str, log_callback) -> Tuple[bool, list]:
    """执行官方配置验证"""
    return run_powershell([openclaw_path, "config", "validate"], "验证配置", log_callback)


def init_config(openclaw_path: str, log_callback) -> Tuple[bool, list]:
    """初始化配置文件"""
    return run_powershell([openclaw_path, "config", "init"], "初始化配置文件", log_callback)


def check_latest_version(log_callback) -> Optional[str]:
    """查询 npm registry 上 OpenClaw 的最新版本"""
    success, output = run_powershell(
        ["npm", "view", "openclaw", "version"],
        "查询OpenClaw最新版本", log_callback, timeout=20
    )
    if success and output:
        return output[0].strip()
    return None


def update_openclaw(log_callback) -> Tuple[bool, str]:
    """通过 npm 更新 OpenClaw 到最新版本，返回 (成功, 版本号)"""
    # 先设置 npm 镜像（容错）
    run_powershell(
        ["npm", "config", "set", "registry", "https://registry.npmmirror.com"],
        "设置npm镜像", log_callback, timeout=10
    )

    # 重试最多 2 次
    for attempt in range(2):
        success, output = run_powershell(
            ["npm", "install", "-g", "openclaw@latest"],
            f"更新OpenClaw (第{attempt + 1}次)", log_callback, timeout=120
        )
        if success:
            break
        if attempt < 1:
            import time
            time.sleep(2)

    if success:
        # 确认新版本
        ver_success, ver_output = run_powershell(
            ["openclaw", "--version"], "确认新版本", log_callback
        )
        if ver_success and ver_output:
            return True, ver_output[0].strip()
        return True, "latest"

    # 失败时记录详细错误
    if output:
        for line in output[-10:]:
            log_callback(f"  {line}", "error")
    return False, ""
