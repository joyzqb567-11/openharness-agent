# Ordinary Browser Rule

使用场景：
- 打开普通网页、localhost、file 页面或测试页面交互。
- 需要截图、页面快照、点击、输入、等待、上传、控制台或网络检查。

规则：
- 用户没有要求真实 Chrome 登录态时，默认普通独立浏览器足够。
- 已读取 `browser_automation/SKILL.md` 后，优先使用当前工具池里的浏览器 MCP 工具执行打开、点击、输入、等待、截图和页面检查。
- 简单网页正文或搜索优先走搜索/读取能力，不要为了静态文本强行打开浏览器。
- 执行页面脚本前说明目的，避免主动读取 cookie、localStorage、sessionStorage、token 或授权头。
- 截图、下载和页面产物应保存到可审计位置，例如 browser_artifacts。

关键词：mcp__browser_automation__browser_open、browser_snapshot、browser_click、browser_type、browser_wait、browser_screenshot、browser_evaluate、mcp__browser_search__web_search、mcp__browser_search__fetch_url、真实 Chrome。
