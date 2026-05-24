"""全局常量（适配2026.3.8）"""


class AppConst:
    DEFAULT_PORT = "18789"
    DEFAULT_TIMEOUT = 15
    LOG_MAX_LINES = 1000
    GATEWAY_CHECK_INTERVAL = 5
    GATEWAY_MAX_WAIT = 20

    INSTALL_STEPS = [
        "许可声明",
        "环境检测",
        "安装OpenClaw",
        "初始化配置",
        "部署完成"
    ]

    NODE_DOWNLOAD_URL = "https://npmmirror.com/mirrors/node/v18.20.4/node-v18.20.4-x64.msi"
