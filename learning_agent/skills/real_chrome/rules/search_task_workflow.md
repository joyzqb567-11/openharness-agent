# Real Chrome Search Task Workflow

当用户说“用真实浏览器查某个会议、酒店、航班、资料、天气、旅游攻略”等公开信息时，复用本流程。

1. 先读取 `learning_agent/skills/tool_list.md`，再读取 `learning_agent/skills/real_chrome/SKILL.md`。
2. 先调用 `browser_profile_status`，确认真实 Chrome profile 状态。
3. 再调用 `browser_connect_real_chrome`，参数必须包含 `confirm_real_profile=true`。
4. 连接成功后打开 `https://www.google.com/`，不要直接打开搜索结果 URL。
5. 用 `browser_snapshot` 找搜索框；若有同意弹窗，可只点击同意按钮继续。
6. 用 `browser_click` 点击搜索框，用 `browser_type` 输入从用户请求提炼出的搜索词，用 `browser_press_key` 按 Enter。
7. 用 `browser_wait` 等待结果加载，再用 `browser_screenshot` 保存视觉证据。
8. 用 `browser_snapshot` 读取结果页可见标题、摘要或页面信息，再整理回答。
9. 遇到 CAPTCHA 或异常流量验证时，不要绕过；截图后如实说明受阻。
10. 不要读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容、插件内容、network、console，也不要调用 `browser_evaluate`。

最终回答必须包含：`real_chrome_connected=true`、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`、搜索词、截图文件名或路径、可见来源摘要、任务结论和隐私边界说明。
