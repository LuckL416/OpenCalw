"""所有硬编码中文字符串"""

# 窗口
WINDOW_TITLE = "OpenClaw 管理器"
WINDOW_GEOMETRY = "1300x900"
WINDOW_MIN_SIZE = (1000, 700)

# 状态栏
STATUS_DETECTING = "正在检测 OpenClaw 环境..."
STATUS_DETECTED = "环境检测完成 | OpenClaw：{status}"
STATUS_DETECT_FAILED = "环境检测失败"

# Gateway 状态
GATEWAY_RUNNING = "运行中"
GATEWAY_STOPPED = "已停止"
GATEWAY_URL_UNKNOWN = "未获取"

# 按钮文案
BTN_START_GATEWAY = "启动 Gateway"
BTN_STOP_GATEWAY = "停止 Gateway"
BTN_RESTART_GATEWAY = "重启 Gateway"
BTN_EXTRACT_TOKEN = "提取认证 Token"
BTN_VIEW_ALL_CONFIG = "查看所有配置"
BTN_REFRESH_STATUS = "手动刷新状态"
BTN_OPEN_CONFIG = "打开配置文件"
BTN_APPLY_PORT = "应用端口"
BTN_OPEN_DASHBOARD = "手动打开"
BTN_READ_CONFIG = "读取配置"
BTN_SAVE_CONFIG = "保存配置"
BTN_VALIDATE_CONFIG = "验证配置"
BTN_RESET_CONFIG = "重置配置"
BTN_BACKUP_CONFIG = "备份配置文件"
BTN_RESTORE_CONFIG = "还原配置文件"
BTN_EDIT_CONFIG = "手动编辑"
BTN_REFRESH_PREVIEW = "刷新预览"
BTN_GET_PATH = "获取路径"
BTN_OPEN_FOLDER = "打开文件夹"
BTN_START_INSTALL = "安装 OpenClaw"
BTN_UNINSTALL = "彻底卸载"
BTN_RESET_ENV = "重置环境"
BTN_GET_API_KEY = "获取API密钥"

# 标签
LBL_GATEWAY_STATUS = "当前状态："
LBL_DASHBOARD_URL = "Dashboard地址："
LBL_GATEWAY_PORT = "网关端口："
LBL_CONFIG_PATH = "配置文件路径："

# 提示消息
MSG_ADMIN_WARNING = "当前非管理员权限，部分操作（如安装Node.js/OpenClaw）可能失败！\n建议以管理员身份运行本程序。"
MSG_INSTALL_SUCCESS = "OpenClaw 安装完成！\n请切换到「核心配置」标签页配置API密钥。"
MSG_INSTALL_FAILED = "安装失败：{error}"
MSG_UNINSTALL_CONFIRM = "确定要彻底卸载 OpenClaw 吗？\n此操作会删除全局安装的 OpenClaw 包"
MSG_UNINSTALL_SUCCESS = "OpenClaw 已成功卸载！"
MSG_UNINSTALL_FAILED = "卸载失败，请查看日志"
MSG_NOT_INSTALLED = "未检测到 OpenClaw，无需卸载"
MSG_NOT_DETECTED = "未检测到 OpenClaw，请先安装"
MSG_GATEWAY_ALREADY_RUNNING = "Gateway 已在运行中！"
MSG_GATEWAY_NOT_RUNNING = "Gateway 未运行！"
MSG_BUSY = "当前有操作正在进行，请稍后再试"
MSG_PORT_INVALID = "请输入有效的端口号（1-65535）"
MSG_API_KEY_EMPTY = "请填写API密钥"
MSG_CONFIG_SAVED = "GUI参数已备份到本地！\n请查看配置文件，手动编辑真实配置键"
MSG_CONFIG_LOADED = "已加载本地GUI配置！"
MSG_CONFIG_RESET = "GUI配置已重置为默认值！"
MSG_CONFIG_VALIDATED = "配置验证通过！"
MSG_CONFIG_VALIDATE_FAILED = "配置验证失败！\n请查看日志"
MSG_RESET_CONFIRM = "确定要重置所有配置吗？"
MSG_RESET_ENV_CONFIRM = "确定要重置安装环境吗？\n此操作会清除本地GUI配置备份"
MSG_RESET_ENV_SUCCESS = "安装环境已重置完成！"
MSG_CLOSE_CONFIRM = "Gateway 仍在运行中，是否停止并退出？"
MSG_STARTUP_FAILED = "程序启动失败：{error}"
MSG_NO_GUI_BACKUP = "未找到本地GUI配置备份\n建议先查看配置文件，手动编辑后保存"

# Tab 名称
TAB_GATEWAY = "Gateway 控制"
TAB_CORE_CONFIG = "核心配置"
TAB_ADVANCED = "高级设置"
TAB_CONFIG_FILE = "配置文件管理"
TAB_INSTALL_WIZARD = "安装向导"

# 配置提示
TIP_ADAPT_VERSION = "适配 2026.3.8 版本 | 先查看配置文件确认键名 | 保存后自动验证"

# 安装说明
INSTALL_DESC = """
【OpenClaw 安装向导说明】
1. 自动检测 Node.js 环境（需 18.x LTS 版本）
2. 自动配置淘宝镜像，解决网络问题
3. 自动安装最新版 OpenClaw
4. 自动解析 ~ 路径为 Windows 真实路径，修复配置文件访问问题
5. 全程无需手动敲命令，严格遵循版本规范

⚠️ 安装过程需要管理员权限
⚠️ 安装完成后请先查看配置文件，确认配置键名
⚠️ 配置键名必须与配置文件一致，否则保存失败
"""

# 日志框架
LOG_FRAME_TITLE = "运行日志"
