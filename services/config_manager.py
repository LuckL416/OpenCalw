"""配置文件管理：读写、备份还原"""
import os
import json
import shutil
from typing import Optional


GUI_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "openclaw_gui_config.json")


def read_config_file(path: str) -> str:
    """读取配置文件内容（容错编码）"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_config_file(path: str, content: dict):
    """写入配置文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)


def validate_json(content: str) -> bool:
    """验证是否为合法 JSON"""
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        return False


def create_default_config(path: str, default_port: int):
    """创建默认配置文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    default_config = {
        "gateway": {"port": default_port},
        "provider": {"default": "moonshot", "apiKey": ""}
    }
    write_config_file(path, default_config)


def save_gui_config(config_data: dict):
    """保存 GUI 配置到本地备份"""
    with open(GUI_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)


def load_gui_config() -> Optional[dict]:
    """从本地备份加载 GUI 配置"""
    if not os.path.exists(GUI_CONFIG_PATH):
        return None
    with open(GUI_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def backup_config_file(config_path: str, backup_path: str):
    """备份配置文件"""
    shutil.copy2(config_path, backup_path)


def restore_config_file(backup_path: str, config_path: str):
    """还原配置文件"""
    shutil.copy2(backup_path, config_path)


def delete_gui_config():
    """删除 GUI 配置备份"""
    if os.path.exists(GUI_CONFIG_PATH):
        os.remove(GUI_CONFIG_PATH)
