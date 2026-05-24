# ====================== 前置配置 ======================
import os
import sys
import locale

# 确保项目根目录在 sys.path 中
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

os.environ['PYTHONWARNINGS'] = 'ignore:libpng warning'
os.environ['PNG_WARNINGS'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'
locale.setlocale(locale.LC_ALL, '')

# ====================== 程序入口 ======================
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import messagebox
    from ui.app import OpenClawApp

    try:
        root = tk.Tk()
        app = OpenClawApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("启动失败", f"程序启动失败：\n{e}")
