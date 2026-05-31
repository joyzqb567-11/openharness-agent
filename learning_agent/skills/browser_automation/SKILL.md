---
name: browser_automation
description: Use when ordinary independent browser automation is needed and the user did not require real Chrome or login state.
---

# Browser Automation

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入普通浏览器自动化能力。需要操作细节时，再读取：

- `learning_agent/skills/browser_automation/rules/ordinary_browser.md`

读取本文件成功后，运行时会按需把 `browser_automation` MCP 工具加入当前工具池；如果工具仍不可见，优先检查 MCP 是否启用或 browser_automation server 是否启动成功。

边界：
- 普通网页、localhost、截图、点击、输入、等待和页面检查走本 skill。
- 用户明确要求真实 Chrome、桌面 Chrome、当前浏览器或登录态时，改读 `learning_agent/skills/real_chrome/SKILL.md`。
- 实际执行优先使用解锁后的 `browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_wait`、`browser_screenshot`、`browser_evaluate` 等浏览器工具。
