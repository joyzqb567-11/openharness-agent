# learning_agent 真实浏览器能力对齐 ClaudeCode 汇报

日期：2026-05-31

## 源码对比结论

ClaudeCode 源码中可确认的浏览器能力不是一个单独 Playwright 脚本，而是一组协同能力：

1. `commands/chrome/chrome.tsx`
   - 有 Chrome 扩展入口、安装状态、站点级权限管理和 `--chrome` / `--no-chrome` 模式。
2. `skills/bundled/claudeInChrome.ts`
   - 有 Claude in Chrome skill，要求先读取当前 tab 上下文，再使用 Chrome 浏览器 MCP 工具。
3. `hooks/usePromptsFromClaudeInChrome.tsx`
   - 可从 Chrome 扩展接收 prompt、图片和 tabId，并进入主消息队列。
4. `utils/computerUse/mcpServer.ts`
   - 有 computer-use MCP，能支撑坐标和桌面级交互。
5. `components/permissions/ComputerUseApproval/ComputerUseApproval.tsx`
   - 有面向用户的 computer-use 权限审批、系统权限缺失提示和 retry 入口。
6. `services/tools/StreamingToolExecutor.ts` 和 `services/tools/toolExecution.ts`
   - 工具执行支持流式、并发安全、权限决策、hook、失败处理。
7. `utils/conversationRecovery.ts`
   - 支持会话恢复、未完成工具调用清理、技能和 hook 恢复。
8. `plugins/builtinPlugins.ts`
   - 有插件启用、工具允许、hooks 和 MCP server 配置生态。

learning_agent 原来已有真实 Chrome 连接、Playwright 页面工具、敏感脚本阻断、审计日志和公开搜索 harness，但缺少浏览器运行层的恢复、视觉、流程、回放和站点授权能力。

## 本次已补齐能力

1. 页面失败恢复
   - 新增 `browser_recover_page`。
   - 支持 `reload`、`back`、`forward`、`new`、`reopen`。
   - 恢复结果会进入 `browser_profile_status` 的最近恢复摘要。

2. 视觉定位
   - `browser_snapshot` 现在返回 `box`、`center_x`、`center_y`。
   - 新增 `browser_visual_locate`，可按 text、selector、element_id 返回视觉候选。
   - `browser_click` 新增 x/y 坐标点击。

3. 复杂网站流程
   - 新增 `browser_flow_run`。
   - 支持 stages，每个阶段有 name、tool、arguments。
   - 每阶段输出 success/error，失败时能定位具体阶段。

4. 登录态安全
   - 新增 `browser_site_grant`。
   - 支持 `grant`、`revoke`、`list`、`enable_strict`、`disable_strict`。
   - 真实 Chrome 严格模式下，`browser_open` 会检查 origin 是否已授权。
   - 真实 Chrome 下动作默认只审计，不允许自动执行回放。

5. 插件兼容状态
   - 新增 `browser_plugin_status`。
   - 输出恢复、视觉定位、坐标点击、流程、动作日志、回放、站点授权和重试能力状态。

6. 异常重试
   - `call()` 统一进入 `_run_browser_tool_with_retries()`。
   - 对常见临时错误如 timeout、page closed、context closed、navigation failed 做短重试。
   - 失败和成功都会写入动作日志。

7. 任务回放
   - 新增 `browser_action_log.jsonl`。
   - 新增 `browser_replay`。
   - 默认 dry-run 只列计划。
   - 只有 `confirm_replay=true` 且 `dry_run=false` 时才执行安全动作。
   - 输入、上传、脚本、真实 Chrome 连接和站点授权不会被自动回放。

## 本次修改的关键文件

1. `learning_agent/browser_automation_mcp_server.py`
   - 新增真实浏览器运行层工具、统一重试、动作日志、回放、视觉定位、站点授权。
2. `learning_agent/tests/test_browser_runtime_alignment.py`
   - 新增 7 个测试，覆盖新增能力。
3. `learning_agent/skills/browser_automation/SKILL.md`
   - 告诉模型普通浏览器任务如何使用恢复、视觉、流程、回放和状态工具。
4. `learning_agent/skills/real_chrome/SKILL.md`
   - 告诉模型真实 Chrome 下如何使用站点授权、恢复、视觉定位和安全回放边界。

## 自动化验证

1. `python -m py_compile learning_agent/browser_automation_mcp_server.py learning_agent/tests/test_browser_runtime_alignment.py`
   - 通过。
2. `python -m unittest learning_agent.tests.test_browser_runtime_alignment`
   - 7 个测试通过。
3. `python -m unittest learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_harness learning_agent.tests.test_browser_intent`
   - 49 个测试通过，1 个真实 Chrome 手动测试按环境变量跳过。
4. `python -m unittest discover learning_agent.tests`
   - 433 个测试通过，1 个真实 Chrome 手动测试按环境变量跳过。
5. `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\browser_runtime_alignment.json`
   - 真实可见终端验收通过。
   - 结果文件：`learning_agent/acceptance_controller/runs/browser_runtime_alignment-20260531_204032/result.json`
   - `completed=true`，`assertion.passed=true`。
   - 最终可见回答包含 `BROWSER_RUNTIME_ALIGNMENT_READY`、`browser_profile_status`、`browser_plugin_status`、`page_recovery`、`visual_locate`、`coordinate_click`、`flow_run`、`action_log`、`replay`、`site_grant`、`retry`。
6. `python -m learning_agent.acceptance.verifier ...browser_runtime_alignment-20260531_204032 ...browser_runtime_alignment.json`
   - 离线复验通过。
   - `completed=true`，`assertion.passed=true`，截图、事件、调试日志证据均存在。

## 验收中发现并修复的问题

第一次真实终端验收失败，原因是 `browser_flow_run` 的工具 schema 里 `stages` 是 array 但缺少 `items`，OpenAI response_format 返回 `invalid_json_schema`。

已修复：

1. 为 `browser_flow_run.inputSchema.properties.stages` 补充 `items`。
2. 在 `learning_agent/tests/test_browser_runtime_alignment.py` 中新增 schema 断言，防止回归。
3. 修复后重新运行完整测试和真实可见终端验收，均通过。

## 仍未等同 ClaudeCode 的部分

1. ClaudeCode 有 Chrome 扩展入口和浏览器侧 prompt/tabId/image 进入主消息队列；learning_agent 目前是 MCP 工具侧增强，还没有浏览器扩展。
2. ClaudeCode 有终端 UI 权限面板和 computer-use 系统权限恢复提示；learning_agent 目前是工具返回文本和状态字段。
3. ClaudeCode 的插件系统有 marketplace、依赖解析、启停和 hooks 配置；learning_agent 目前新增的是浏览器插件兼容状态报告，不是完整插件市场。
4. ClaudeCode 的流式工具执行和浏览器扩展内部实现更成熟；learning_agent 本次补的是浏览器工具运行层，不等于完整复制 ClaudeCode 生态。

## 备份

本次修改已备份到：

`learning_agent/test/browser_runtime_alignment_20260531/`
