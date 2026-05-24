"""PowerShell 命令执行封装"""
import subprocess
from typing import List, Tuple, Optional, Callable

from app_const import AppConst

DEFAULT_TIMEOUT = AppConst.DEFAULT_TIMEOUT


def run_powershell(
    cmd_list: List[str],
    desc: str,
    log_callback: Optional[Callable] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[bool, List[str]]:
    """执行PowerShell命令（编码+超时+容错）"""
    try:
        if not cmd_list or (len(cmd_list) > 0 and cmd_list[0] is None):
            _log(log_callback, f"❌ {desc} 失败：命令为空或路径未找到", "error")
            return False, ["命令参数错误"]

        cmd_list = [item.strip() for item in cmd_list if item and item.strip()]
        if not cmd_list:
            _log(log_callback, f"❌ {desc} 失败：过滤后命令为空", "error")
            return False, ["过滤后命令为空"]

        cmd_parts = []
        for idx, item in enumerate(cmd_list):
            if idx == 0 and " " in item:
                cmd_parts.append(f'& "{item}"')
            elif " " in item and not item.startswith('"') and not item.endswith('"'):
                cmd_parts.append(f'"{item}"')
            else:
                cmd_parts.append(item)
        cmd_str = " ".join(cmd_parts)

        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-NoLogo", "-NonInteractive", "-Command", cmd_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )

        output = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        error = [line.strip() for line in result.stderr.split("\n") if line.strip()]

        if result.returncode == 0:
            _log(log_callback, f"✅ {desc} 成功", "success")
            return True, output
        else:
            error_msg = " | ".join(error) if error else "未知错误"
            if "Unrecognized key" in error_msg or "not found" in error_msg.lower():
                _log(log_callback, f"⚠️ {desc}：配置键不被支持 - {error_msg}", "warning")
            elif "missing required argument" in error_msg:
                _log(log_callback, f"⚠️ {desc}：参数缺失 - {error_msg}", "warning")
            else:
                _log(log_callback, f"❌ {desc} 失败：{error_msg}", "error")
            return False, error

    except subprocess.TimeoutExpired:
        _log(log_callback, f"❌ {desc} 失败：执行超时（{timeout}秒）", "error")
        return False, [f"执行超时（{timeout}秒）"]
    except Exception as e:
        _log(log_callback, f"❌ {desc} 异常：{str(e)}", "error")
        return False, [str(e)]


def _log(callback, msg, tag):
    if callback:
        callback(msg, tag)
