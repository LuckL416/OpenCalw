# OpenClaw 管理器优化设计

## 目标

从代码结构、性能、健壮性、UI/UX 四个方面优化现有的 OpenClaw 管理器。

## 约束

- 保持 Tkinter 作为 UI 框架
- 同步更新所有 PyInstaller .spec 打包配置文件
- 不引入外部图标库
- 保持现有 `pack` 布局策略

---

## 一、模块结构重组

将 1533 行单文件 `openclaw.py` 拆分为以下目录结构：

```
openclaw/
├── openclaw.py                 # 主入口 (~30行)
├── app_const.py                # AppConst 常量类
├── i18n.py                     # 所有中文字符串字典
├── utils/
│   ├── __init__.py
│   ├── threading.py            # run_on_main_thread, is_admin
│   └── powershell.py           # run_powershell 封装
├── services/
│   ├── __init__.py
│   ├── environment.py          # 自动检测 Node.js/npm/OpenClaw
│   ├── gateway.py              # Gateway 启停重启 + 端口检测
│   ├── installer.py            # 安装向导完整流程
│   └── config_manager.py       # 配置读写、备份还原、验证
├── ui/
│   ├── __init__.py
│   ├── app.py                  # 主窗口框架 + Tab 容器
│   ├── gateway_tab.py          # Gateway 控制 Tab
│   ├── core_config_tab.py      # 核心配置 Tab
│   ├── advanced_tab.py         # 高级设置 Tab
│   ├── config_file_tab.py      # 配置文件管理 Tab
│   ├── install_wizard_tab.py   # 安装向导 Tab
│   └── widgets.py              # 通用组件（日志面板、设置行等）
```

### 职责分离

- `ui/*` — 只创建和布局 Tkinter 组件，不包含业务逻辑
- `services/*` — 处理所有系统交互和业务逻辑，不引用 tkinter
- `utils/*` — 无状态纯工具函数
- `openclaw.py` — 入口：创建 root → 初始化服务 → 启动 UI

### 通信模式

UI 层通过回调调用 Service 层，Service 层通过队列/回调回传结果：

```
UI (callback) → Service (background thread) → queue → UI (after poll)
```

---

## 二、性能优化

1. **去除硬阻塞**：`time.sleep(1/3/5)` 改为基于状态的轮询 + `root.after()`
2. **is_busy 加锁**：替换为 `threading.Lock()` 保护的属性
3. **log_data 加锁**：列表追加操作加 `threading.Lock` 保护
4. **路径解析缓存**：`config_file_path` 解析一次后缓存，避免重复 `os.path.expanduser`
5. **队列改为事件驱动**：`queue.get(block=True, timeout=1)` — 有消息才刷新 UI
6. **按钮状态联动**：`is_busy` 为 True 时批量禁用所有操作按钮

---

## 三、健壮性修复

1. **裸 except 替换**：3 处 `except:` 改为 `except Exception`，至少记录日志
2. **私有 API 替换**：`tk._default_root` 改为模块级保存的 root 引用
3. **messagebox 线程安全**：所有 `messagebox` 调用统一经 `run_on_main_thread`
4. **状态恢复保证**：所有设置 `is_busy = True` 的地方用 `try/finally` 确保恢复
5. **导入规范化**：函数内 `import shutil` 移至文件顶部
6. **网络重试**：npm install 等网络命令加最多 2 次重试
7. **UI 更新线程安全**：`step_labels` 遍历只在主线程执行

---

## 四、UI/UX 改进

### 视觉与主题

- 暗色/亮色主题切换（基于 `ttk.Style`，clam 主题）
- 顶部工具栏增加主题切换按钮
- 统一字号变量：标题 12、正文 10、辅助 9
- 窗口标题改为 "OpenClaw 管理器"

### 交互

- `is_busy` 时禁用所有操作按钮
- 键盘快捷键：`Ctrl+S` 保存、`Ctrl+R` 刷新、`F5` 刷新 Gateway
- 日志面板 `Ctrl+F` 搜索
- 状态栏显示 Gateway 运行时长
- 安装进度条支持取消
- 安装步骤用颜色区分状态

### 文案

- 所有硬编码字符串抽取至 `i18n.py`
- 按钮命名统一为动宾结构
- 错误提示使用友好语言

### 窗口管理

- 窗口位置/大小通过 `openclaw_gui_config.json` 持久化
- 关闭时有 Gateway 运行中的确认提示

---

## 五、打包配置同步

更新现有 .spec 文件，将单文件 `openclaw.py` 入口改为 package 模式：

- `openclaw.spec` — 核心版本
- `OpenClaw_Kimi启动器.spec` — Kimi 版本
- `OpenClaw全能版.spec` — 全能版本
- `OpenClaw全能管理工具.spec` — 管理工具版本
- `OpenClaw全能管理工具（保留服务版）.spec` — 保留服务版本
- `OpenClaw管理器.spec` — 管理器版本

---

## 六、测试策略

- 每个 `utils/*` 和 `services/*` 模块有对应的单元测试
- UI 模块做手动回归测试（Tkinter 不适合自动化 UI 测试）
- 重构前后功能对比：每个 Tab 的所有按钮功能
