# learning_agent 真实可见浏览器验收补齐计划

日期：2026-05-31

## 背景

上一轮已经补齐了页面失败恢复、视觉定位、坐标点击、复杂流程、登录态安全、插件兼容状态、异常重试和任务回放等浏览器运行层能力。

但上一轮真实终端验收主要证明这些工具在 agent 会话里可见、可调用、状态正确，没有强制把独立浏览器从 headless 模式切到肉眼可见窗口，也没有在可见浏览器窗口中跑一条完整操作链路。

## 本轮目标

新增一个明确的可见浏览器启动能力，让 agent 可以在普通独立 Chromium 场景下启动肉眼可见的浏览器窗口，然后用真实可见终端验收场景完成以下动作：

1. 启动可见浏览器。
2. 打开公开网页。
3. 读取页面快照。
4. 进行视觉定位。
5. 用坐标点击或阶段流程执行页面动作。
6. 执行页面恢复。
7. 查看任务回放 dry-run。
8. 查看浏览器插件兼容状态。
9. 最终回答包含验收标记和关键工具名。

## 实现阶段

阶段 1：补测试
- 新增或扩展 `test_browser_runtime_alignment.py`。
- 验证工具清单包含 `browser_launch_visible`。
- 验证缺少 `confirm_visible_browser=true` 时拒绝启动。
- 验证确认后会切换 `launch_headless=false` 并调用浏览器启动流程。

阶段 2：补运行层
- 在 `browser_automation_mcp_server.py` 中新增 `browser_launch_visible`。
- 增加 `launch_headless` 状态。
- `ensure_browser()` 根据 `launch_headless` 决定 Playwright 是否 headless。
- `browser_profile_status` 和 `browser_plugin_status` 输出可见浏览器状态。

阶段 3：更新 skill
- `browser_automation/SKILL.md` 说明肉眼可见浏览器验收先调用 `browser_launch_visible`。
- `real_chrome/SKILL.md` 保持真实 Chrome 登录态边界，不把可见独立 Chromium 误称为用户真实 profile。

阶段 4：真实可见终端验收
- 新增 `browser_visible_runtime_acceptance.json`。
- 必须通过 `start_oauth_agent.bat` 由 controller 打开真实可见终端。
- 场景要求 agent 调用 `browser_launch_visible`、`browser_open`、`browser_snapshot`、`browser_visual_locate`、`browser_recover_page`、`browser_replay`、`browser_plugin_status`。
- 结果必须 `completed=true` 且 `assertion.passed=true`。

## 验收标准

1. 自动化测试通过。
2. 完整测试发现集通过。
3. 真实可见终端验收通过。
4. 验收 evidence 中必须出现 `browser_launch_visible`、`visible_browser=true`、`headless=false`、`browser_open`、`browser_snapshot`、`browser_visual_locate`、`browser_recover_page`、`browser_replay`、`browser_plugin_status`。
5. 如果真实可见浏览器窗口无法由当前环境打开、观察或截图证明，则不能声明任务完成。
