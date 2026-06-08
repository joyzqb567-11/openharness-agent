# Stage 6：Chrome 插件写动作执行计划

日期：2026-06-01

项目根目录：`H:\codexworkplace\sofeware\OpenHarness-main`

## 阶段目标

在 Stage 5 只读插件底座之上，补齐 Chrome 插件 provider 的写动作能力。

本阶段坚持“双轨底层、单轨模型表面”：模型仍然只调用统一 `browser_*` 工具，不新增 `chrome_extension_click`、`chrome_extension_type` 这类重复工具名。

## 成功标准

1. `ChromeExtensionProvider` 支持 `browser_click`、`browser_type`、`browser_press_key`、`browser_open`、`browser_wait`、`browser_visual_locate` 这批插件写动作和辅助动作。
2. 插件侧 `background.js` 和 `content_script.js` 能表达 click、type、press_key、navigate、scroll、form_input、visual locate。
3. Native host 协议不再用 Stage 5 的只读拒绝处理写动作，而是把写动作命令和执行结果分开审计。
4. 每个插件写动作都通过 `BrowserActionExecutor.execute_action()`，不能绕过 action started/progress/completed/failed 生命周期。
5. 每个插件写动作都能记录 action/event/observation 证据，至少包含 command id、tool name、tab id、success/failure、visible text 或 locator 摘要。
6. 未连接插件时 provider 仍不可用，不能把写动作静默退到插件 provider。
7. 单元测试、相关回归、全量回归、真实可见终端验收和独立 verifier 都通过。

## 范围边界

本阶段先实现插件写动作协议和 provider 执行闭环，不做站点级权限授权 UI；站点权限放到 Stage 7。

本阶段不安装真实 Chrome 扩展，不写 Windows 注册表；真实安装 UX 与系统注册仍保持显式人工步骤。

本阶段不新增模型可见的 provider-specific 工具；所有写动作继续经 `browser_click`、`browser_type`、`browser_press_key`、`browser_open` 等统一工具入口。

## 执行步骤

1. 写红灯测试 `learning_agent/tests/test_chrome_extension_write_actions_stage6.py`，先证明当前 provider 不支持写动作、协议拒绝写动作、扩展脚本缺写动作命令。
2. 扩展 `message_protocol.py`，新增写动作命令和结果的安全 schema，同时保留敏感字段过滤。
3. 扩展 `bridge_server.py`，新增 pending command 队列、command result 记录、command status 文本和 observation 摘要。
4. 扩展 `ChromeExtensionProvider`，让统一写工具通过 bridge 命令队列执行，并在结果返回时输出稳定文本。
5. 扩展 `content_script.js` 和 `background.js`，让扩展可以执行 click/type/key/navigate/scroll/form_input/visual locate，并把结果回传 host。
6. 接入 `BrowserAutomationServer` provider 分发路径，确保插件写工具仍由 `BrowserActionExecutor.execute_action()` 包裹。
7. 新增 Stage 6 acceptance scenario，并把计划和修改备份到 `learning_agent/test/browser_dual_track_stage6_20260601/`。
8. 运行聚焦单测、相关回归、`py_compile`、全量 `unittest discover`、真实可见终端验收和独立 verifier。

## 停止条件

如果发现插件写动作绕过 `BrowserActionExecutor`，必须停止并修复。

如果发现插件脚本读取 cookie、storage、token、password 原文，必须停止并修复。

如果真实可见终端验收未通过，不能声明 Stage 6 完成。
