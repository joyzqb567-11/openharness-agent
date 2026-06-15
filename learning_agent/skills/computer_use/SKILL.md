---
name: computer_use
description: Use when a task needs real Windows desktop observation, application launch, mouse, keyboard, clipboard, or ClaudeCode-style computer-use MCP tools.
---

# Computer Use

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

## 能力边界

- Computer Use 现在优先通过独立 `computer-use` MCP server 进入，对外工具名前缀是 `mcp__computer-use__`。
- 常用入口是 `mcp__computer-use__request_access`、`mcp__computer-use__open_application`、`mcp__computer-use__screenshot`、`mcp__computer-use__mouse_move`、`mcp__computer-use__left_click`、`mcp__computer-use__type`、`mcp__computer-use__key`、`mcp__computer-use__scroll`、`mcp__computer-use__computer_batch`。
- `bash`、`powershell`、`command`、`script` 不属于 Computer Use MCP；桌面任务不要用 shell 伪装点击、输入、启动应用或读取屏幕。
- 高风险目标、登录、验证码、会员、付费、风控和隐私页面必须停止并说明原因，不要绕过限制。

## 推荐流程

1. 先请求授权：调用 `mcp__computer-use__request_access`，说明应用、原因、权限范围和时长。
2. 再打开或绑定应用：调用 `mcp__computer-use__open_application`，优先使用用户明确点名的本地软件。
3. 然后观察：调用 `mcp__computer-use__screenshot` 或只读观察工具确认当前窗口。
4. 最后小步执行：鼠标、键盘、滚动、剪贴板和批处理都要小步验证，失败时记录阻塞原因。

## 成功判据

- 模型可见工具中出现 `mcp__computer-use__request_access` 这类 ClaudeCode 风格名称。
- `computer-use` MCP 的 `tools/list` 不包含 `bash`、`powershell`、`command`、`script`。
- `/computer use --full` 成功后，模型主循环应加载 `computer_use` 能力包，而不是把桌面任务交给命令行。
