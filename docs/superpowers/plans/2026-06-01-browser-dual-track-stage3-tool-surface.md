# Browser Dual Track Stage 3 Tool Surface Plan

## 目标

把 Stage 3 落成代码级门禁：模型只面对统一 `browser_*` 工具，不出现 `chrome_extension_open`、`real_chrome_cdp_click`、`visible_chromium_type` 这类 provider-specific 重复工具；底层 provider 选择必须由 `BrowserProviderRouter` 写入 event log。

## 范围

本阶段只处理“工具表面”和“防误选提示/测试”。不实现 Chrome 插件、不新增 native host、不改变真实浏览器动作能力。

## 成功标准

1. `browser_automation_mcp_server.TOOLS` 中只存在统一浏览器动作名。
2. MCP 工具 catalog 不会把 provider-specific 重复动作暴露给模型。
3. `browser_connect_real_chrome` 等高风险控制入口被标记为 advanced/provider-control，而不是普通 open/click/type 的替代工具。
4. `browser_automation` 与 `real_chrome` skill/harness 明确告诉模型：调用统一浏览器工具，不直接选择底层 provider。
5. 顶层浏览器工具调用后，browser runtime event log 能看到 `browser_provider_decision`。
6. 自动化测试、全量测试、真实可见终端验收全部通过。

## 任务分解

### Task 1：红灯测试

- 新增 `learning_agent/tests/test_browser_tool_surface_stage3.py`。
- 覆盖 server 工具清单中不存在 provider-specific 重复动作。
- 覆盖 MCP catalog 会给真实 Chrome 控制工具打上 advanced/provider-control 搜索提示。
- 覆盖 skill/harness 文本包含“模型不选择 provider/底层路线由 BrowserProviderRouter 决定”。

### Task 2：工具表面 helper

- 新增 `learning_agent/browser/providers/tool_surface.py`。
- 定义统一动作名集合、provider-specific 禁止前缀/后缀、provider-control 工具集合。
- 提供 `is_provider_specific_tool_name()`、`is_provider_control_tool_name()`、`browser_tool_surface_hint()`。

### Task 3：MCP catalog 标记

- 修改 `learning_agent/mcp/runtime.py`。
- 对 `browser_connect_real_chrome`、`browser_disconnect_real_chrome`、`browser_profile_status` 增加 advanced/provider-control 搜索提示。
- 对未来误接入的 provider-specific 重复工具保持 deferred 且不可作为普通统一动作入口。

### Task 4：提示词和 harness 对齐

- 修改 `learning_agent/skills/browser_automation/SKILL.md`。
- 修改 `learning_agent/skills/real_chrome/SKILL.md`。
- 修改 `learning_agent/browser/harness.py`。
- 明确模型只调用统一浏览器工具，底层 provider 由 `BrowserProviderRouter` 决定并写事件。

### Task 5：验证与备份

- 运行 Stage 3 单测、Stage 1-3 provider 相关单测、全量测试。
- 新增真实可见终端验收场景。
- 独立 verifier 验证 run。
- 备份修改摘要到 `learning_agent/test/browser_dual_track_stage3_20260601/modified_snippets.md`。
- 更新 `agent_memory/progress.md` 和 `agent_memory/bugs.md`。

## 停止条件

如果自动化测试或真实可见终端验收失败，不能声明 Stage 3 完成；必须记录失败 run、根因和下一步修复。
