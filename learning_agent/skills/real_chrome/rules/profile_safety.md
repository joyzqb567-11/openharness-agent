# Real Chrome Profile Safety Rule

使用场景：
- 用户明确要求真实 Chrome、桌面 Chrome、当前浏览器、可见浏览器或已登录状态。

规则：
- 不要用搜索、fetch_url 或独立 Chromium 替代真实 Chrome 请求。
- 先确认 browser_profile_status 是否可用，再考虑 browser_connect_real_chrome。
- 已读取 `real_chrome/SKILL.md` 后，connect 仍要等待 profile status workflow 完成；不要把“工具已准备”误当成“可以直接连接”。
- 连接真实 profile 前必须让用户理解风险，并包含 confirm_real_profile=true。
- 不主动读取 cookies、localStorage、sessionStorage、token、password 或 Authorization header。
- 若用户明确要求读取敏感数据，要重新说明风险和边界。

关键词：真实 Chrome、桌面 Chrome、当前浏览器、登录态、日常 Chrome profile、browser_profile_status、browser_connect_real_chrome、confirm_real_profile、cookies、localStorage、sessionStorage、token。
