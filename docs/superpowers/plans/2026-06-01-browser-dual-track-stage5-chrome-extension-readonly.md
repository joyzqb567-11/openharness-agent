# Stage 5：Chrome 插件 MVP 只读能力执行计划

日期：2026-06-01

项目根目录：`H:\codexworkplace\sofeware\OpenHarness-main`

## 阶段目标

补齐 Chrome 插件路线的最小只读闭环，让 learning_agent 具备对齐 ClaudeCode `claude-in-chrome` 接入层的基础结构：Chrome extension、Native Host、消息协议、连接状态、当前标签页上下文和页面可见文本读取。

本阶段只做只读能力，不做点击、输入、按键、上传、提交等写动作。

## 成功标准

1. 新增 `learning_agent/chrome_extension/`，包含 Manifest V3 扩展文件。
2. 新增 `learning_agent/browser_extension_host/`，包含 native host、bridge state、message protocol、pairing store、manifest installer。
3. 消息协议只允许 `tabs_context`、`read_page`、`status` 这类只读动作。
4. 消息协议明确拒绝 `click`、`type`、`press_key`、`navigate`、`upload`、`submit` 等写动作。
5. 插件脚本不得调用 `chrome.cookies`、`document.cookie`、`localStorage`、`sessionStorage`。
6. 新增 `ChromeExtensionProvider`，默认未连接时健康状态为不可用，连接后能提供 `browser_tabs_context`、`browser_snapshot`、`browser_extension_status` 的只读结果。
7. `BrowserAutomationServer` 注册 `ChromeExtensionProvider`，并暴露 `browser_extension_status` 状态工具。
8. Router 仍保持模型单轨表面：模型不直接调用 `chrome_extension_open` 等 provider-specific 工具。
9. 新增 Stage 5 单元测试、备份文档、真实可见终端验收场景。
10. 全量测试和真实可见终端验收通过后，才能标记 Stage 5 完成。

## 范围边界

本阶段不安装真实 Chrome 插件到用户浏览器，不写 Windows 注册表，也不执行页面点击输入。

本阶段只提供可安装文件、native host manifest 生成器、只读消息协议和 provider 接入点。真实写动作、站点权限和安装 UX 放到 Stage 6、Stage 7、Stage 8。

## 执行步骤

1. 写红灯测试，验证扩展文件、只读协议、敏感 API 禁止、provider 默认不可用和连接后可读。
2. 新建 Chrome extension 文件：`manifest.json`、`background.js`、`content_script.js`、`page_bridge.js`、`options.html`、`options.js`。
3. 新建 host 模块：`message_protocol.py`、`pairing_store.py`、`bridge_server.py`、`manifest_installer.py`、`native_host.py`。
4. 新增 `ChromeExtensionProvider`，只支持 `browser_tabs_context`、`browser_snapshot`、`browser_extension_status`。
5. 接入 `BrowserAutomationServer` 的 provider registry 和工具清单。
6. 新增 acceptance scenario，并把修改备份到 `learning_agent/test/browser_dual_track_stage5_20260601/`。
7. 运行目标单测、相关回归、`py_compile`、全量 `unittest discover`。
8. 通过 `start_oauth_agent.bat` 真实可见终端验收和独立 verifier。

## 停止条件

如果测试发现插件或 host 读取 cookies、storage、token、password 原文，立即停止并修复。

如果 `ChromeExtensionProvider` 在未连接时被 Router 当作可用，立即停止并修复。

如果真实可见终端验收未通过，不能声明 Stage 5 完成。

