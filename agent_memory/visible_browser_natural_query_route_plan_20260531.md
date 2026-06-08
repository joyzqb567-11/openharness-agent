# 2026-05-31 自然实时查询强制可见浏览器路由修复计划

## 背景

用户要求用真实可见方式重新测试精准 prompt：`帮我查询3天后武汉的天气，并帮我做一下旅游攻略。`

最新验收结果证明：agent 能回答武汉天气和旅游攻略，但只调用了 `browser_search.web_search` 和 `browser_search.fetch_url`，没有调用 `browser_launch_visible`、`browser_open`、`browser_snapshot` 等真实可见浏览器工具。

这说明当前缺口不是浏览器工具不能用，而是普通自然语言的实时查询没有进入可见浏览器工作流。

## 成功标准

1. 普通 prompt `帮我查询3天后武汉的天气，并帮我做一下旅游攻略。` 必须被识别为需要可见浏览器的公开实时查询。
2. 首轮模型可见工具中必须包含 `mcp__browser_automation__browser_launch_visible`，避免模型只能看到 `browser_profile_status` 或 `browser_search`。
3. 系统 harness 必须明确要求先启动可见独立 Chromium，再打开网页、读取页面快照和视觉证据。
4. 显式要求“真实 Chrome / 登录态 / 日常浏览器”的任务仍走 `browser_profile_status -> browser_connect_real_chrome`，不能被普通可见 Chromium 误替代。
5. 自动化测试必须覆盖意图识别、harness 注入、首轮工具池和显式真实 Chrome 回归保护。
6. 真实可见终端验收必须通过 `learning_agent/start_oauth_agent.bat`，并在日志里看到 `browser_launch_visible`、`visible_browser=true`、`headless=false`、`browser_open` 和 `browser_snapshot`。
7. 若真实可见终端验收无法完成，不能声明开发完成。

## 阶段计划

1. 证据固定：保留失败验收 run 路径和工具调用证据，写入 `agent_memory/bugs.md`。
2. 红灯测试：先新增失败测试，证明普通武汉天气/攻略 prompt 没有可见浏览器路由。
3. 意图分层：新增“自然公开实时查询需要可见浏览器”的检测函数，并保持“真实 Chrome 登录态”检测独立。
4. Harness 注入：新增可见浏览器任务 harness，要求 `browser_launch_visible(confirm_visible_browser=true)` 开始，不用 `web_search/fetch_url` 替代。
5. 工具池接入：在 `run_events()` 建初始 tools 前，若检测到自然可见浏览器查询，预加载 `browser_automation` 能力包，确保模型首轮能看见 `browser_launch_visible`。
6. 回归保护：确保显式“真实浏览器/登录态/日常 Chrome”仍触发真实 Chrome profile 流程，不走普通可见 Chromium。
7. 自动化验证：运行定向测试、py_compile、完整 `unittest discover learning_agent.tests`。
8. 真实验收：更新精准 prompt 场景并通过 controller 启动 `start_oauth_agent.bat`，观察真实终端和可见浏览器证据。
9. 备份归档：把本轮改动、测试、计划、验收结果复制到 `learning_agent/test/visible_browser_natural_query_route_20260531/`。

## 停止条件

只有同时满足“代码修改完成 + 自动化测试通过 + 精准 prompt 真实可见终端验收通过”，本轮才算完成。

如果精准 prompt 仍只调用 `browser_search` 或没有打开可见浏览器，必须继续修复，不能用回答质量代替真实可见浏览器验收。
