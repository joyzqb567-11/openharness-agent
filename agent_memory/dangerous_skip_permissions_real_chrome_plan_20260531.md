# Dangerous Skip Permissions + Real Chrome Test Plan

## 目标

让 `start_oauth_agent.bat` 启动的真实 learning_agent 默认进入本地调试危险模式，效果接近 ClaudeCode 的 `--dangerously-skip-permissions`：权限确认不再弹 `y/N`，而是自动允许并留下审计记录。

## 范围

1. 新增 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS` 环境变量识别。
2. `start_oauth_agent.ps1` 默认设置该环境变量为 `1`，但允许用户提前设置为 `0/false/off/no` 关闭。
3. 终端权限入口自动通过所有权限请求，并写入 `permission_auto_approved`。
4. MCP 工具权限入口自动通过所有 MCP 工具调用，并写入 MCP progress 的 `permission_auto_approved`。
5. 保留工具自身的必要参数校验，例如 `browser_connect_real_chrome` 仍需要 `confirm_real_profile=true`。
6. 新增真实 Chrome 调试验收场景，要求使用 `browser_connect_real_chrome` 打开 `https://example.com`。

## 验收标准

1. 单元测试证明危险模式不会调用 `input()`。
2. 单元测试证明危险模式会给任意 MCP 工具返回自动授权原因。
3. 单元测试证明 `start_oauth_agent.ps1` 默认启用危险模式。
4. `python -m unittest discover learning_agent.tests` 通过。
5. 通过 `start_oauth_agent.bat` 真实可见终端验收，最终输出包含 `browser_connect_real_chrome` 和 `real_chrome_connected=true`。
