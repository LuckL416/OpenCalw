"""线程安全工具函数"""
import threading
import ctypes

_root_ref = None


def set_root(root):
    """保存主窗口引用，避免依赖 tk._default_root"""
    global _root_ref
    _root_ref = root


def get_root():
    return _root_ref


def is_admin():
    """检测是否管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_on_main_thread(func, *args, **kwargs):
    """线程安全执行UI操作"""
    if threading.current_thread() is threading.main_thread():
        func(*args, **kwargs)
    else:
        root = get_root()
        if root:
            root.after(0, lambda: func(*args, **kwargs))
