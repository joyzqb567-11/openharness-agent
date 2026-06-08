# Browser Dual Track Stage 4 修改备份

日期：2026-06-01

## 本阶段目标

Stage 4 把 `browser_tabs_context` 做成真实 Chrome / 登录态任务的强制上下文合同：模型执行点击、输入、按键、上传前，必须先读取当前 session、active tab、URL、标题、provider 和 page_id。

## 新增文件

1. `docs/superpowers/plans/2026-06-01-browser-dual-track-stage4-tabs-context.md`
   - 新增 Stage 4 书面计划、成功标准、范围边界、执行步骤和停止条件。
2. `learning_agent/test/browser_dual_track_stage4_20260601/plan.md`
   - 备份 Stage 4 计划，方便用户后续学习和对齐。
3. `learning_agent/tests/test_browser_tabs_context_stage4.py`
   - 新增红灯/绿灯测试，覆盖工具清单、provider 支持、context 输出字段、真实 Chrome 写动作门禁、active tab 变化失效。
4. `learning_agent/acceptance_controller/scenarios/browser_tabs_context_stage4_acceptance.json`
   - 新增真实可见终端验收场景。

## 修改文件

1. `learning_agent/browser_automation_mcp_server.py`
   - 新增 `browser_tabs_context` 工具清单和 dispatch。
   - 新增 `BROWSER_TABS_CONTEXT_REQUIRED_WRITE_TOOLS`。
   - 新增 tabs context 读取状态、失效原因和门禁 helper。
   - 真实 Chrome 模式下，`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_upload_file` 执行前必须先通过 `browser_tabs_context`。
   - 页面关闭、导航、新建标签页、切换标签页、真实 Chrome 重连、断开和 close_all 后会让旧 context 失效。
   - `browser_tabs_context` 输出 `session_id`、`mode`、`provider`、`connected`、`visible`、`headless`、`active_tab_id`、`tab_count`、`tab_id`、`page_id`、`title`、`URL`。
2. `learning_agent/browser/providers/visible_chromium.py`
   - `VISIBLE_CHROMIUM_TOOLS` 增加 `browser_tabs_context`。
3. `learning_agent/browser/providers/real_chrome_cdp.py`
   - `REAL_CHROME_CDP_TOOLS` 增加 `browser_tabs_context`。
4. `learning_agent/browser/harness.py`
   - 真实 Chrome harness 明确写动作前必须调用 `browser_tabs_context`。
   - 可见浏览器 harness 说明 `browser_tabs_context` 可用于查看 session 和标签页状态。
5. `learning_agent/skills/real_chrome/SKILL.md`
   - 真实 Chrome skill 明确点击、输入、按键、上传前必须先读 `browser_tabs_context`。
6. `learning_agent/skills/browser_automation/SKILL.md`
   - 普通浏览器 skill 补充 `browser_tabs_context` 的状态查看用途。
7. `agent_memory/progress.md`
   - 记录 Stage 4 计划启动和后续执行状态。

## 红灯测试

首次运行：

```powershell
python -m unittest learning_agent.tests.test_browser_tabs_context_stage4
```

结果：

```text
FAILED (failures=1, errors=4)
RuntimeError: 未知工具：browser_tabs_context
AssertionError: 'browser_tabs_context' not found in [...]
AttributeError: 'FakeTabsContextPage' object has no attribute 'locator'
```

这些失败证明当时确实缺少工具、provider 支持和真实 Chrome 写动作门禁。

## 当前自动化验证

```powershell
python -m unittest learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tool_surface_stage3 learning_agent.tests.test_browser_session_manager
```

结果：

```text
Ran 20 tests in 0.196s
OK
```

```powershell
python -m py_compile .\learning_agent\browser_automation_mcp_server.py .\learning_agent\browser\providers\visible_chromium.py .\learning_agent\browser\providers\real_chrome_cdp.py .\learning_agent\browser\harness.py .\learning_agent\tests\test_browser_tabs_context_stage4.py
```

结果：退出码 0。

## 待完成门禁

还需要运行全量测试和 `start_oauth_agent.bat` 真实可见终端验收，未完成前不能声明 Stage 4 完成。

