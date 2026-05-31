---
name: real_chrome
description: Use when the user explicitly requires real Chrome, desktop Chrome, current browser, visible browser, or login state.
---

# Real Chrome

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入真实 Chrome 高风险能力。需要细节时，再读取：

- `learning_agent/skills/real_chrome/rules/profile_safety.md`
- `learning_agent/skills/real_chrome/rules/search_task_workflow.md`

读取本文件成功后，运行时会准备 `real_chrome` 和后续页面操作所需的 `browser_automation` MCP 工具；真实连接仍必须先执行 `browser_profile_status`，状态检查完成后才可调用 `browser_connect_real_chrome`。

边界：
- 不要用搜索、fetch、普通独立 Chromium 替代用户明确要求的真实 Chrome。
- 真实 profile 可能包含 cookies、localStorage、sessionStorage、token 和账号状态。
- 连接真实 Chrome 后，继续使用解锁后的浏览器打开、点击、输入、截图和页面检查工具操作同一个真实浏览器会话。
