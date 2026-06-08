# Stage 4：browser_tabs_context 合同执行计划

日期：2026-06-01

项目根目录：`H:\codexworkplace\sofeware\OpenHarness-main`

## 阶段目标

把 ClaudeCode `tabs_context_mcp` 的关键思想落到 learning_agent：真实 Chrome / 登录态任务在执行点击、输入、按键、上传等写动作前，必须先读取一次当前标签页上下文。

这里的 `browser_tabs_context` 不是普通的 `browser_tabs list` 别名。它要返回可审计的 session、provider、active tab、URL、title、page_id、tab_id，并作为后续真实 Chrome 写动作的上下文门禁。

## 成功标准

1. 工具清单公开 `browser_tabs_context`，模型只需要调用统一 `browser_*` 工具，不需要选择 provider。
2. `browser_tabs_context` 输出至少包含 `session_id`、`mode`、`provider`、`active_tab_id`、`tab_count`、`page_id`、`tab_id`、`URL`、`title`。
3. 当前 session 为真实 Chrome / CDP 时，`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_upload_file` 必须在有效 `browser_tabs_context` 后才能执行。
4. 如果标签页关闭、切换、新建、真实 Chrome 重连或断开导致 active tab 变化，旧 context 必须失效，后续写动作必须重新读取 `browser_tabs_context`。
5. tab id 必须继续由 `BrowserTabRegistry` 保证跨 session 不复用。
6. `VisibleChromiumProvider` 和 `RealChromeCdpProvider` 都要声明支持该统一工具，provider 决策事件仍进入 browser runtime event log。
7. skill/harness 文档必须告诉模型：真实 Chrome 写动作前先调用 `browser_tabs_context`，不要直接选择 provider。
8. 新增和修改内容必须备份到 `learning_agent/test/browser_dual_track_stage4_20260601/`。
9. 自动化测试通过后，还必须通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端验收和独立 verifier。

## 范围边界

本阶段只补 `browser_tabs_context` 合同，不实现 Chrome 插件、native host、GIF 录屏，也不改模型主循环。

本阶段可以修改 `browser_automation_mcp_server.py`、provider adapter、skills/harness、测试和验收场景。

## 执行步骤

1. 先写 Stage 4 红灯测试，覆盖工具清单、provider 支持、context 输出字段、真实 Chrome 写动作门禁、context 失效。
2. 运行 Stage 4 测试，确认失败点来自缺少 `browser_tabs_context` 或门禁逻辑。
3. 在 MCP server 中新增 `browser_tabs_context` 工具、分发入口、状态字段、context 标记和失效函数。
4. 在真实 Chrome/CDP 模式下，把写动作执行前的门禁放入统一 `call()` 路径，确保 provider/executor 之前就能阻断危险动作并写失败 run。
5. 在页面关闭、新建、切换、真实 Chrome 重连、断开等路径刷新或失效 context。
6. 更新 `VisibleChromiumProvider` 与 `RealChromeCdpProvider` 的支持工具集合。
7. 更新 browser skill 和 harness 提示，明确真实 Chrome 写动作前必须先读 `browser_tabs_context`。
8. 新增真实可见终端验收场景，要求 agent 在终端里检查 Stage 4 合同并输出固定成功标记。
9. 运行目标单测、相关回归、`py_compile`、全量 `unittest discover`。
10. 用 acceptance controller 启动 `start_oauth_agent.bat` 真实可见终端，执行 Stage 4 场景，并用 verifier 复验。

## 停止条件

如果自动化测试无法证明门禁生效，停止并修复。

如果真实可见终端验收没有通过，不能声明 Stage 4 完成。

