"""统一主题管理 —— 精致现代风配色"""
import tkinter as tk
from tkinter import ttk

# 浅色主题
LIGHT = {
    "bg": "#f8f9fa",
    "surface": "#ffffff",
    "sidebar_bg": "#1e293b",
    "sidebar_fg": "#cbd5e1",
    "sidebar_active": "#3b82f6",
    "sidebar_hover": "#334155",
    "header_bg": "#ffffff",
    "header_fg": "#0f172a",
    "fg": "#1e293b",
    "fg_secondary": "#64748b",
    "fg_muted": "#94a3b8",
    "border": "#e2e8f0",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_fg": "#ffffff",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "info": "#3b82f6",
    "input_bg": "#ffffff",
    "input_border": "#cbd5e1",
    "input_focus": "#3b82f6",
    "card_bg": "#ffffff",
    "card_hover": "#f8fafc",
    "scrollbar_bg": "#f1f5f9",
    "scrollbar_fg": "#94a3b8",
    "log_bg": "#0f172a",
    "log_fg": "#e2e8f0",
}

# 暗色主题
DARK = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "sidebar_bg": "#0c1222",
    "sidebar_fg": "#94a3b8",
    "sidebar_active": "#3b82f6",
    "sidebar_hover": "#1e293b",
    "header_bg": "#1e293b",
    "header_fg": "#f1f5f9",
    "fg": "#e2e8f0",
    "fg_secondary": "#94a3b8",
    "fg_muted": "#64748b",
    "border": "#334155",
    "accent": "#3b82f6",
    "accent_hover": "#60a5fa",
    "accent_fg": "#ffffff",
    "success": "#34d399",
    "danger": "#f87171",
    "warning": "#fbbf24",
    "info": "#60a5fa",
    "input_bg": "#1e293b",
    "input_border": "#475569",
    "input_focus": "#3b82f6",
    "card_bg": "#1e293b",
    "card_hover": "#334155",
    "scrollbar_bg": "#1e293b",
    "scrollbar_fg": "#475569",
    "log_bg": "#0c1222",
    "log_fg": "#cbd5e1",
}

_current = "light"
_colors = dict(LIGHT)


def get(key: str) -> str:
    return _colors.get(key, "#000")


def toggle() -> str:
    global _current, _colors
    _current = "dark" if _current == "light" else "light"
    _colors = dict(DARK if _current == "dark" else LIGHT)
    return _current


def is_dark() -> bool:
    return _current == "dark"


def _setup_styles(style: ttk.Style):
    """配置 ttk 全局样式"""
    c = _colors
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # 根
    style.configure(".", background=c["bg"], foreground=c["fg"], font=("Microsoft YaHei UI", 10))

    # Frame
    style.configure("TFrame", background=c["bg"])
    style.configure("Surface.TFrame", background=c["surface"])
    style.configure("Card.TFrame", background=c["card_bg"], relief="solid", borderwidth=1)

    # Label
    style.configure("TLabel", background=c["bg"], foreground=c["fg"])
    style.configure("Secondary.TLabel", foreground=c["fg_secondary"], font=("TkDefaultFont", 9))
    style.configure("Muted.TLabel", foreground=c["fg_muted"], font=("TkDefaultFont", 9))
    style.configure("Title.TLabel", font=("TkDefaultFont", 14, "bold"), foreground=c["fg"])
    style.configure("Heading.TLabel", font=("TkDefaultFont", 11, "bold"), foreground=c["fg"])

    # LabelFrame (卡片)
    style.configure("Card.TLabelframe", background=c["card_bg"], bordercolor=c["border"],
                    relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=c["card_bg"], foreground=c["fg"],
                    font=("TkDefaultFont", 10, "bold"), borderwidth=0)

    # Button
    style.configure("TButton", background=c["card_bg"], foreground=c["fg"],
                    borderwidth=1, bordercolor=c["border"], padding=(12, 6),
                    relief="flat", font=("TkDefaultFont", 10))
    style.map("TButton",
              background=[("active", c["surface"]), ("disabled", c["bg"])],
              foreground=[("disabled", c["fg_muted"])])

    # Primary button
    style.configure("Primary.TButton", background=c["accent"], foreground=c["accent_fg"],
                    borderwidth=0, padding=(16, 8), font=("TkDefaultFont", 10, "bold"), relief="flat")
    style.map("Primary.TButton",
              background=[("active", c["accent_hover"]), ("disabled", c["fg_muted"])],
              foreground=[("disabled", c["fg_muted"])])

    # Danger outline button
    style.configure("Danger.TButton", background=c["card_bg"], foreground=c["danger"],
                    borderwidth=1, bordercolor=c["danger"], padding=(12, 6), relief="flat")
    style.map("Danger.TButton",
              background=[("active", "#fef2f2")],
              foreground=[("active", c["danger"])])

    # Small button
    style.configure("Small.TButton", padding=(8, 4), font=("TkDefaultFont", 9))

    # Entry
    style.configure("TEntry", fieldbackground=c["input_bg"], foreground=c["fg"],
                    borderwidth=1, bordercolor=c["input_border"], padding=6, relief="solid")
    style.map("TEntry", bordercolor=[("focus", c["input_focus"])])

    # Combobox
    style.configure("TCombobox", fieldbackground=c["input_bg"], foreground=c["fg"],
                    arrowcolor=c["fg"], borderwidth=1)
    style.map("TCombobox", fieldbackground=[("readonly", c["input_bg"])])

    # Progressbar
    style.configure("TProgressbar", background=c["accent"], troughcolor=c["border"],
                    borderwidth=0, thickness=8, relief="flat")

    # Checkbutton
    style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])
    style.map("TCheckbutton", background=[("active", c["bg"])])

    # Separator
    style.configure("TSeparator", background=c["border"])

    # Scrollbar
    style.configure("TScrollbar", background=c["scrollbar_bg"], troughcolor=c["bg"],
                    arrowcolor=c["fg_muted"], borderwidth=0)
    style.map("TScrollbar", background=[("active", c["scrollbar_fg"])])


def init(root: tk.Tk):
    _setup_styles(ttk.Style(root))
    root.configure(bg=_colors["bg"])
