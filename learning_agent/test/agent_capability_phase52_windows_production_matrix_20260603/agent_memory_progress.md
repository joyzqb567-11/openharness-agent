# 当前任务进度

## 2026-06-03 Phase 38 Windows ComputerUseApproval Model
Status: code edits, focused tests, syntax check, scenario JSON check, CLI self-check, neighbor regression, backup, full regression, visible terminal acceptance, and independent verifier passed.
Completed:
- Added `learning_agent/computer_use/approval.py` with session app allowlist, grant flags, forbidden target classification, terminal status lines, and stable Phase38 CLI contract.
- Updated `learning_agent/computer_use/controller.py` with optional `approval_model` injection and pre-backend approval rejection.
- Updated `learning_agent/app/interactive.py` so `/computer status` shows `Computer Use Approval` lines.
- Updated `learning_agent/computer_use/__init__.py` to export Phase38 APIs.
- Added `learning_agent/tests/test_windows_computer_use_approval_phase38.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase38_windows_computer_approval.json`.
- Added phase record `agent_memory/agent_capability_phase38_windows_computer_approval_20260603.md`.
Verified:
- TDD red failed first with `ModuleNotFoundError: No module named 'learning_agent.computer_use.approval'`.
- Focused Phase38 tests: 6 tests OK.
- `py_compile`, scenario JSON, and CLI self-check passed.
- Phase30-38 neighbor regression: 45 tests OK.
- Full regression: `python -m unittest discover -s learning_agent\tests`, 670 tests OK, skipped=1.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase38_windows_computer_approval-20260603_105641`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
Boundary:
- Phase38 proves approval/session grant model, grant flags, forbidden target blocking, controller integration, and terminal status. It does not prove graphical approval UI or real low-level Windows SendInput/WGC/UIA maturity.

---

## 2026-06-03 Phase 37 Windows SendInput Action Executor Contract
Status: code edits, focused tests, syntax check, scenario JSON check, CLI self-check, neighbor regression, backup, full regression, visible terminal acceptance, and independent verifier passed.
Completed:
- Added `learning_agent/computer_use/sendinput_executor.py` with default-disabled `WindowsSendInputExecutor`, injectable low-level implementation, normalized action events, `type_text` redaction, stable CLI tokens, and Phase37 contract self-check.
- Updated `learning_agent/computer_use/controller.py` so `WindowsComputerUseBackend` accepts an `action_executor` and routes mouse/keyboard write actions through the SendInput executor contract instead of the old `SetCursorPos + mouse_event` path.
- Updated `learning_agent/computer_use/__init__.py` to export Phase37 APIs.
- Added `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase37_windows_sendinput_executor.json`.
- Added phase record `agent_memory/agent_capability_phase37_windows_sendinput_executor_20260603.md`.
Verified so far:
- TDD red: first Phase37 test run failed with `ModuleNotFoundError: No module named 'learning_agent.computer_use.sendinput_executor'`.
- Focused Phase37 tests: 5 tests OK.
- `py_compile` passed and Phase37 scenario JSON passed.
- CLI self-check printed `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK contract_ready=true real_input_default=false fake_impl_exercised=true raw_text_hidden=true actions_expanded=false marker=PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY`.
- Phase30-37 neighbor regression: 39 tests OK.
Final verification:
- Backup completed under `learning_agent/test/agent_capability_phase37_windows_sendinput_executor_20260603/`.
- Full regression passed: `python -m unittest discover -s learning_agent\tests`, 664 tests OK, skipped=1.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase37_windows_sendinput_executor-20260603_104221`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
Boundary:
- Phase37 proves SendInput executor contract, routing, and redaction. It does not prove a real low-level `ctypes.SendInput` implementation is already wired.

---

## 2026-06-03 Phase 36 Windows.Graphics.Capture Provider Contract
状态：已完成代码修改、自动化测试、学习备份和真实可见终端验收。

完成内容：
- 已新增 `learning_agent/computer_use/wgc_capture.py`，提供 `WindowsGraphicsCaptureProvider`、WGC 依赖诊断、截图结果合同转换和 CLI token。
- 已修改 `learning_agent/computer_use/native_diagnostics.py`，让 WGC 诊断项来自 Phase36 provider 合同。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase36 API。
- 已新增 `learning_agent/tests/test_windows_computer_use_wgc_provider_phase36.py`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase36_windows_wgc_provider.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase36_windows_wgc_provider_20260603.md`。
- 已备份到 `learning_agent/test/agent_capability_phase36_windows_wgc_provider_20260603/`。

验证：
- Phase36 聚焦测试：5 tests OK。
- Phase33-36 邻近回归：18 tests OK。
- `py_compile` 通过，Phase36 scenario JSON 校验通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，659 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase36_windows_wgc_provider-20260603_102321/result.json`，`completed=true`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE36_WINDOWS_WGC_PROVIDER_READY PHASE36_WINDOWS_WGC_PROVIDER_OK dependency_reported=true capture_contract_ready=true fallback_required=true actions_expanded=false`。

下一步：
- Phase37 补 SendInput executor；必须继续使用 safe action gate，不允许绕过 lock、abort、窗口目标和敏感窗口禁止规则。

---

## 2026-06-03 Phase 35 Windows Real UIA Safe-Window Smoke
状态：已完成代码修改、自动化测试、学习备份和真实可见终端验收。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_real_uia_smoke_phase35.py`，红灯确认缺少 `learning_agent.computer_use.real_uia_smoke`。
- 已新增 `learning_agent/computer_use/real_uia_smoke.py`，提供 `uiautomation` 依赖诊断、安全 Notepad 窗口目标、真实 UIA smoke 主入口和稳定 CLI token。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase35 smoke API。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase35_windows_real_uia_smoke.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase35_windows_real_uia_smoke_20260603.md`。
- 已备份到 `learning_agent/test/agent_capability_phase35_windows_real_uia_smoke_20260603/`。

验证：
- Phase35 聚焦测试：4 tests OK。
- Phase32-35 邻近回归：19 tests OK。
- `py_compile` 通过，Phase35 scenario JSON 校验通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，654 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase35_windows_real_uia_smoke-20260603_101422/result.json`，`completed=true`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE35_WINDOWS_REAL_UIA_SMOKE_READY PHASE35_WINDOWS_REAL_UIA_SMOKE_OK dependency_reported=true fake_provider_used=false actions_expanded=false safe_window_only=true`。

下一步：
- Phase36 补 Windows.Graphics.Capture provider 合同和诚实诊断；当前机器没有 `winrt/winsdk` WGC Python 绑定，不能声明 WGC 已可用。

---

## 2026-06-03 Phase 30 Windows OS Computer Use Safe Action Gate
状态：已完成代码修改、自动化测试、学习备份和真实可见终端验收。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_actions_phase30.py`，红灯确认缺少 `learning_agent.computer_use.lock`。
- 已新增 `learning_agent/computer_use/lock.py`，提供 durable lock、owner session、release、abort request、abort clear 和 status。
- 已新增 `learning_agent/computer_use/action_policy.py`，提供窗口相对坐标转换、文本脱敏、短哈希、目标窗口摘要和 action evidence envelope。
- 已修改 `learning_agent/computer_use/controller.py`：注入锁管理器时要求当前 session 持锁；abort flag 阻止后端动作；成功动作返回 `action_evidence`；生产默认 controller 可在无人持锁时自动获取当前 session 锁。
- 已修改 `MemoryComputerUseBackend` 和 `LearningAgent._computer_action()`，避免 `type_text` 原文进入日志、审计、权限提示和 evidence。
- 已修改 `learning_agent/computer_use/__init__.py` 导出 Phase 30 helper。
- 已修改 `learning_agent/tools/schemas.py`，说明提供 `window` 时 x/y 是窗口相对坐标。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase30_windows_action_gate.json`。

验证：
- Phase 30 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_actions_phase30`，5 tests OK。
- Phase 17/20/27/28/29 邻近回归：24 tests OK。
- `py_compile` 通过，Phase 30 scenario JSON 校验通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，630 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase30_windows_action_gate-20260603_065937/result.json`，`completed=true`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE30_WINDOWS_ACTION_GATE_READY PHASE30_WINDOWS_ACTION_GATE_OK no_lock_blocked=true coord=15,27 abort_blocked=true raw_text_hidden=true evidence=true`。

下一步：
- Phase 31 建议补动作前后 evidence chain、lock TTL/stale owner 恢复、abort 的终端命令入口和更完整的动作审计落盘。
- 仍不建议直接扩大真实鼠标键盘动作；真实动作前应继续补 native helper、DPI、多显示器、窗口遮挡和安全目标过滤。

---

## 2026-06-02 Phase 27 Windows OS Computer Use Protocol
状态：已完成代码修改、自动化测试、学习备份准备和真实可见终端验收。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_protocol_phase27.py`，红灯确认当前缺少 `computer_observe`、窗口目录和未知窗口拒绝。
- 已新增 `learning_agent/computer_use/models.py`，用 `ComputerUseWindowRef`、`build_window_ref()` 和 `window_ref_identity()` 固化窗口身份合同。
- 已扩展 `learning_agent/computer_use/controller.py`：新增 `OBSERVE_ACTIONS`、`observe()`、内存后端 `list_apps/list_windows/get_active_window/get_window_state`、动作前未知窗口拦截。
- 已扩展 `learning_agent/tools/schemas.py`：新增 `computer_observe` 只读工具，并给 `computer_action` 增加可选可信 `window` 目标。
- 已扩展 `learning_agent/tools/catalog.py`、`learning_agent/tools/executor.py` 和 `learning_agent/core/agent.py`，让 `computer_observe` 成为低风险只读工具并可真实分发。
- 已修复 `learning_agent/acceptance_controller/controller.ps1`：缺省 `event_payload_contains` 时不再生成 null 断言项。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase27_windows_computer_use_protocol.json`。

验证：
- Phase 27 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_protocol_phase27`，4 tests OK。
- Phase 17/20 回归：`python -m unittest learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_os_computer_use_phase20`，7 tests OK。
- 语法检查：`python -m py_compile ...` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，617 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase27_windows_computer_use_protocol-20260602_233224/result.json`，`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。

下一步：
- Phase 28 建议做 Windows 只读窗口枚举、窗口截图证据和 UI Automation 文本摘要。
- 不建议直接扩展真实鼠标键盘动作；必须先建立窗口发现、窗口相对坐标、权限、锁和证据链。

---

## 2026-06-02 Phase 26 Windows OS Computer Use Blueprint
状态：已完成书面蓝图；本阶段未修改运行时代码，未执行真实桌面动作。

完成内容：
- 已读取 Codex Computer Use 插件说明，提取 Windows 方向关键点：app/window 目标、UI Automation、SendInput、Windows.Graphics.Capture、窗口相对坐标和安全禁止项。
- 已对照现有 `learning_agent/computer_use/controller.py`、Phase 20 记录、Phase 14-23 蓝图和当前项目记忆。
- 已确认 Phase 25 编号已被真实 Chrome extension/native-host 连接后续占用，所以本轮 Windows OS Computer Use 蓝图使用 Phase 26。
- 新增正式蓝图：`docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`。
- 新增 phase memory：`agent_memory/agent_capability_phase26_windows_computer_use_blueprint_20260602.md`。
- 新增学习备份：`learning_agent/test/agent_capability_phase26_windows_computer_use_blueprint_20260602/phase26_blueprint.md`。
- 已同步根 `task_plan.md`、`findings.md`、`progress.md`。

下一步：
- 等用户确认后进入 Phase 27：typed Computer Use protocol and tests。
- Phase 27 只做协议和测试，不能直接跳到真实鼠标键盘动作。

验证：
- 本阶段是蓝图和记忆更新，未修改生产运行时代码。
- 因此未运行自动化测试，也未触发 `start_oauth_agent.bat` 真实可见终端验收。

---

## 2026-06-02 Phase 24 Real Chrome Extension E2E
状态：已完成 Phase 24 代码、自动化测试、备份和真实可见终端诊断验收；当前机器真实 Chrome 扩展仍未连接。
完成内容：
- 新增 `agent_memory/agent_capability_phase24_real_chrome_extension_e2e_20260602.md`，记录 Phase 24 成功标准、范围边界、停止条件和验收方式。
- 新增 `learning_agent/tests/test_real_chrome_extension_e2e_phase24.py`，覆盖 native host 工作区锁定、真实扩展证据判断、浏览器命令入队和 `/chrome` 菜单入口。
- 修改 `learning_agent/browser_extension_host/native_host.py`，让 Chrome 启动的 native host 不再依赖不稳定的当前目录。
- 修改 `learning_agent/browser_extension_host/manifest_installer.py`，让 native host launcher 写入 `OPENHARNESS_LEARNING_AGENT_WORKSPACE`，确保真实 Chrome 场景能回到 learning_agent 工作区。
- 修改 `learning_agent/app/interactive.py` 和 `learning_agent/app/chrome_status_renderer.py`，新增 `/chrome real-extension-e2e-check` 真实扩展闭环诊断入口。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase24_real_chrome_extension_e2e.json`，用于真实可见终端验收。
下一步：
- 若要让 `real_extension_e2e=true`，需要在 Chrome 里加载 `learning_agent/chrome_extension`，确认扩展 ID 后执行 `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`，再刷新扩展并重新运行 `/chrome real-extension-e2e-check`。
验证结果：
- `python -m unittest discover -s learning_agent\tests` 通过：611 tests OK，skipped=1。
- 真实可见终端 run `agent_capability_phase24_real_chrome_extension_e2e-20260602_221135` 通过 controller 和独立 verifier。
- 终端截图显示：`browser_prompt_queued=true`，`workspace_lock_ok=true`，`real_extension_connected=false`，`paired=false`，`real_extension_e2e=false`。

## 2026-06-01 Browser Dual Track Stage 12 真实可见终端总验收
状态：已完成 Stage 12 总验收、独立 verifier 复验、报告归档和备份。
完成内容：
- 新增 `learning_agent/acceptance_controller/scenarios/browser_dual_track_stage12_acceptance.json`，用于真实可见 Chromium 总验收。
- 新增 `docs/superpowers/reports/2026-06-01-browser-dual-track-stage12-acceptance-report.md`，记录自动化测试、真实终端 controller、verifier 和剩余边界。
- 已把 Stage 12 场景和报告备份到 `learning_agent/test/browser_dual_track_stage12_20260601/`。
验证结果：
- 自动化总回归已在 Stage 11 后执行：`python -m unittest discover -s learning_agent\tests`，Ran 546 tests OK，skipped=1。
- 旧 `browser_visible_runtime_acceptance.json` 曾因最终回答没有复制长验收行而失败；debug log 证明真实浏览器动作实际完成。
- 新 Stage 12 专用场景 `browser_dual_track_stage12_acceptance-20260601_193735`：controller 返回 `ACCEPTANCE_CONTROLLER_COMPLETED=True`。
- 独立 verifier 返回 `completed=true`、`assertion.passed=true`，debug log 确认 `browser_launch_visible`、`browser_open`、`browser_snapshot`、`browser_screenshot`、`browser_flow_run`、`browser_plugin_status` 均执行，最终回答包含 `BROWSER_DUAL_TRACK_STAGE12_READY STAGE12_VISIBLE_BROWSER_OK`。
下一步：
- 本轮蓝图任务已闭环，可向用户汇报完成；后续若继续提升，建议补 Chrome extension 写动作真实网站端到端验收和远程任务 UI/SDK 展示。

## 2026-06-01 Browser Dual Track Stage 11 Harness 接入
状态：已完成代码修改、自动化测试、全量回归、真实可见终端 controller 验收和独立 verifier 复验。
完成内容：
- 新增 `learning_agent/browser/harness_integration.py`，把 browser runtime run 同步成同 id 的 harness run/stage/verifier/event。
- 修改 `learning_agent/browser_automation_mcp_server.py`，在顶层浏览器工具创建 run、记录 provider decision、完成 run、同步 browser_flow_run report 时全部写入 harness。
- 修改 `learning_agent/runtime/status_snapshot.py`，让项目根和 `learning_agent` 包目录两种 workspace 都能读取 harness，并在 `browser.runs[*].harness` 与 `browser.harness.latest_verifier` 暴露验收结果。
- 新增 `learning_agent/tests/test_browser_harness_integration_stage11.py`，覆盖同 id harness run、provider decision 镜像、verifier 可见、flow checkpoint resume 不重跑。
- 新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/browser_harness_integration_stage11_acceptance.json`。
验证结果：
- `python -m py_compile learning_agent\browser\harness_integration.py learning_agent\browser_automation_mcp_server.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_browser_harness_integration_stage11.py` 通过。
- `python -m unittest learning_agent.tests.test_browser_harness_integration_stage11`：Ran 2 tests OK。
- Stage 8-11 相关回归：Ran 36 tests OK。
- 全量回归 `python -m unittest discover -s learning_agent\tests`：Ran 546 tests OK，skipped=1。
- 真实可见终端 controller：`browser_harness_integration_stage11_acceptance-20260601_193242`，`ACCEPTANCE_CONTROLLER_COMPLETED=True`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，最终回答包含 `BROWSER_HARNESS_STAGE11_READY STAGE11_BROWSER_HARNESS_OK`。
下一步：
- 进入 Stage 12，执行浏览器双轨架构总验收、全量证据整理和最终对齐报告。

## 2026-06-01 BrowserActionExecutor 执行层接管

状态：已完成代码修改、自动化测试、真实可见终端验收和独立 verifier 复验。

完成内容：
- 已新增并跑红 `learning_agent/tests/test_browser_action_executor.py` 的执行层测试，覆盖 `execute_action()` 重试、progress 事件、写工具串行锁、读工具不串行，以及 `BrowserAutomationServer.call()` 真实工具调用必须进入 executor。
- 已在 `learning_agent/browser/action_executor.py` 新增 `execute_action()` 和 `_execute_attempts()`，统一处理 action started、attempt progress、retry、success、failure、结果脱敏和 observation 回填。
- 已把 `learning_agent/browser_automation_mcp_server.py` 的公开 `call()` 接入 `BrowserActionExecutor.execute_action()`，不再让 server 直接旁路执行 handler 后手写 complete/fail。
- 已修复 `browser_flow_run` 嵌套工具调用死锁：`BrowserActionExecutor.write_lock` 改为 `threading.RLock()`，避免外层流程持锁后内层工具同线程再次加锁卡死。
- 已新增真实可见终端验收场景 `browser_action_executor_execute_layer_acceptance.json`，专门检查 started/progress/completed 三类 durable browser runtime event。

验证结果：
- 红灯已确认：新增测试首次因 `BrowserActionExecutor` 缺少 `execute_action` 失败，server 委托测试也证明旧路径没有进入 executor。
- 聚焦绿灯：`python -m unittest learning_agent.tests.test_browser_action_executor`，8 tests OK。
- 相关浏览器回归：`python -m unittest learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_action_executor`，28 tests OK。
- 编译检查：`python -m py_compile .\learning_agent\browser\action_executor.py .\learning_agent\browser_automation_mcp_server.py .\learning_agent\tests\test_browser_action_executor.py .\learning_agent\tests\test_browser_runtime_store.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，488 tests OK，skipped=1。
- 真实可见终端验收：`browser_action_executor_execute_layer_acceptance-20260601_124337/result.json` 显示 `completed=true`，最终回答包含 `ACTION_EXECUTOR_EXECUTE_LAYER_READY` 和 `started=True progress=True completed=True`。
- 独立 verifier：`python -m learning_agent.acceptance.verifier ...` 显示 `completed=true`、`assertion.passed=true`。

下一步：
- 如果继续增强浏览器执行层，建议补并发批处理/流式工具输出，而不是再在 `browser_automation_mcp_server.py` 内新增旁路生命周期逻辑。

## 2026-06-01 BrowserActionExecutor 批量并发与流式结果

状态：已完成 TDD 红绿、自动化测试、真实可见终端验收、独立 verifier 和学习备份。

完成内容：
- 已新增 `test_execute_action_streams_iterable_result_chunks_as_progress`，锁定 handler 返回分段结果时必须产生 `result_chunk` progress，并通过 `on_result_chunk` 回调给上层 UI/SDK。
- 已新增 `test_execute_batch_runs_concurrent_safe_read_actions_in_parallel`，锁定两个 `browser_snapshot` 只读动作在批量入口里必须真正并发执行，同时结果按输入顺序返回。
- 已在 `learning_agent/browser/action_executor.py` 增加 `_stream_result_text()`，普通字符串结果保持原样，非字符串可迭代结果按片段脱敏、落 progress、回调并合并。
- 已在 `learning_agent/browser/action_executor.py` 增加 `execute_batch()` 与 `_execute_batch_item()`，全只读批次使用 `ThreadPoolExecutor` 并发，包含写工具的批次保守串行。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/browser_action_batch_stream_acceptance.json`。

验证结果：
- 红灯已确认：新增测试首次因 `execute_action()` 不接受 `on_result_chunk`、`BrowserActionExecutor` 缺少 `execute_batch()` 失败。
- 聚焦绿灯：`python -m unittest learning_agent.tests.test_browser_action_executor`，10 tests OK。
- 相关浏览器回归：`python -m unittest learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_action_executor`，30 tests OK。
- 编译检查：`python -m py_compile .\learning_agent\browser\action_executor.py .\learning_agent\tests\test_browser_action_executor.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，490 tests OK，skipped=1。
- 真实可见终端验收：`browser_action_batch_stream_acceptance-20260601_125349/result.json` 显示 `completed=true`，最终回答包含 `ACTION_EXECUTOR_BATCH_STREAM_READY batch=true streaming=true tests=10 ok=true`。
- 独立 verifier：`python -m learning_agent.acceptance.verifier ...` 显示 `completed=true`、`assertion.passed=true`。

下一步：
- 如果继续对齐 ClaudeCode，建议把 `execute_batch()` 接入更上层的工具调度器，让模型一次产生的多个只读工具调用能由执行层自动批处理，而不仅是内部 API 可用。

## 2026-05-31 Long-Task Harness v1 执行记录

状态：核心代码、文档、学习备份、自动化验证和真实可见终端验收均已完成。

完成内容：
- 已按用户要求先生成 8 阶段任务文档：`task_plan.md`、`findings.md`、`progress.md`、`agent_memory/long_task_harness_plan.md`，并把计划备份到 `learning_agent/test/long_task_harness_20260531/task_plan.md`。
- 已新增 `learning_agent/tests/test_harness_long_task.py`，覆盖持久化 store、JSONL 事件、队列租约、heartbeat、完成/失败落盘、marker/artifact 阶段验收、可恢复失败重试、checkpoint resume、状态渲染和 CLI。
- 已完成独立 `learning_agent/harness/` 模块：`models.py`、`store.py`、`queue.py`、`verifier.py`、`recovery.py`、`runner.py`、`status.py`、`cli.py`、`__main__.py`、`__init__.py`。
- 已新增 `learning_agent/harness/README.md`，并更新 `learning_agent/README.md` 与 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，说明其他 agent 如何检查和接入长任务 harness。

当前验证：
- 红灯已确认：新增测试首次因 `learning_agent.harness` 不存在失败。
- 绿灯已确认：`python -m unittest learning_agent.tests.test_harness_long_task` 当前 5 tests OK。
- 完整回归已确认：`python -m unittest discover learning_agent` 当前 395 tests OK，skipped=1。
- 编译检查已确认：`python -m compileall learning_agent` 通过。
- MCP doctor 已确认：退出码 0，三个 MCP server 启动成功，模型可见 MCP 工具 30 个；当前真实 Chrome 正在运行导致 profile 诊断为 `needs_user_action`，但本轮 harness 验收不依赖真实 Chrome。
- 真实可见终端验收已确认：`learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/result.json` 显示 `completed=true`、`assertion.passed=true`，最终回答包含 `HarnessRun`、`HarnessQueue`、`StageVerifier`、`render_harness_status` 和 `LONG_TASK_HARNESS_READY`。
- 终端截图已目视确认：`learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/03_final.png` 中真实 Windows Terminal 显示了该回答。

下一步：
- 后续如果继续增强，可把 `LearningAgent.run_events()` 的长任务执行接入 `HarnessRunner`，并补 `enqueue/run` CLI。

## 2026-05-31 Harness CLI Agent Execution 执行记录

状态：已完成计划、TDD 红绿、CLI `enqueue/run`、`AgentStageExecutor`、文档同步、学习备份、自动化验证和真实可见终端验收。

完成内容：
- 已新增任务文档 `task_plan_harness_cli_agent_execution.md` 和进度文档 `progress_harness_cli_agent_execution.md`。
- 已扩展 `learning_agent/tests/test_harness_long_task.py`，新增 CLI enqueue、CLI run echo 和 `AgentStageExecutor` 三类回归测试。
- 已新增 `learning_agent/harness/agent_executor.py`，让 `HarnessRunner` 可以通过 `AgentStageExecutor` 调用真实 `LearningAgent.run(stage.prompt)`。
- 已扩展 `learning_agent/harness/cli.py`，新增 `enqueue` 和 `run` 子命令；`run` 支持 `--executor echo` 和 `--executor agent`。
- 已更新 `learning_agent/harness/README.md`、`learning_agent/README.md` 和 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`。

当前验证：
- 红灯已确认：新增测试首次因缺少 `learning_agent.harness.agent_executor` 失败。
- 绿灯已确认：`python -m unittest learning_agent.tests.test_harness_long_task` 当前 8 tests OK。
- 完整回归已确认：`python -m unittest discover learning_agent` 当前 398 tests OK，skipped=1。
- 编译检查已确认：`python -m compileall learning_agent` 通过。
- MCP doctor 已确认：退出码 0，三个 MCP server 启动成功，模型可见 MCP 工具 30 个；真实 Chrome 仍因本机 Chrome 正在运行显示 `needs_user_action`，但本轮 harness CLI 验收不依赖真实 Chrome。
- 真实可见终端验收已确认：`learning_agent/acceptance_controller/runs/harness_cli_echo_run-20260531_154459/result.json` 显示 `completed=true`、`assertion.passed=true`，最终回答包含 `HARNESS_CLI_AGENT_EXECUTION_OK`、`visible-cli`、`status=completed`、`acceptance=passed`、`VISIBLE_HARNESS_CLI_OK`、`AgentStageExecutor`。

下一步：
- 后续如果继续增强，可增加 JSON 计划文件输入、文件锁和把 `LearningAgent.run_events()` 的长期任务调度纳入 harness。

## 2026-05-31 断言验证器审计检查

状态：已完成代码阅读和聚焦验证；本轮没有修改生产代码。

检查结论：
- learning_agent 当前已经有可用的真实验收断言验证器，核心实现位于 `learning_agent/acceptance_controller/controller.ps1` 的 `Test-ScenarioAssertions` 函数。
- 该验证器会读取 `events.jsonl`、最终回答事件、最新 debug log 和权限响应计数，并生成 `state_checks`、`event_answer_checks`、`debug_log_checks`、`marker_passed`、`permission_count_passed`。
- 每轮验收会输出 `result.json`，保存 `completed`、`assertion`、事件序列、事件日志路径、启动截图、prompt 截图、最终截图、归档 debug log 和权限决策记录。
- 当前实现是“嵌在 PowerShell controller 里的场景断言器”，还不是独立 Python 包或独立 `verify-run` 命令。

验证结果：
- `python -m unittest learning_agent.tests.test_observability_acceptance`：9 tests OK。
- PowerShell `[scriptblock]::Create(...)` 解析 `learning_agent/acceptance_controller/controller.ps1`：通过。
- 场景统计确认 8 个 JSON 场景均配置了事件断言、最终回答断言和 debug log 证据断言；真实自然浏览器场景还配置了 `max_permission_sent_count=0`。

## 2026-05-31 H 盘路径二次清理与真实终端 smoke 验收

状态：已完成路径二次清理、自动化验证和真实可见终端 smoke 验收。

完成内容：
- 已清理当前 OpenHarness 项目相关的旧盘符残留，`rg` 搜索确认旧 OpenHarness 绝对路径和旧测试样例不再出现。
- 保留 `D:\ClaudeCode-main\ClaudeCode-main` 外部源码路径，因为本机实测该路径存在，而 `H:\ClaudeCode-main\ClaudeCode-main` 不存在；强行改为 H 盘会制造假路径。
- 已把 `learning_agent/tests/test_models_codex_oauth.py` 中无副作用示例路径改为 `H:/demo`。
- 已把 `learning_agent/README.md`、`learning_agent/change/oauth.txt` 和阶段 15H 备份 README 中的 opencode2-main 说明改为不写死盘符。
- 已修正 `learning_agent/acceptance_controller/scenarios/smoke.json`，让 smoke 场景按当前客户模式等待 `permission_auto_approved`，不再等待旧人工权限事件。
- 已按学习规则备份修改说明和关键文件到 `learning_agent/test/h_drive_cleanup_20260531/`。

验证结果：
- `python -m unittest learning_agent.tests.test_models_codex_oauth`：46 tests OK。
- `python -m compileall learning_agent`：通过。

## 2026-05-31 千问真实 Chrome 拟人操作测试

状态：用户目标已跑通，严格场景断言未通过。

测试目标：
- 由 `learning_agent` 通过 `browser_connect_real_chrome` 连接真实 Google Chrome。
- 打开 `https://www.qianwen.com/`。
- 拟人点击输入框、输入“请查询明天鄞州区的天气预报”、按 Enter 提交。
- 把真实浏览器上看到的千问回答告诉用户。

运行结果：
- 第一次 run：`learning_agent/acceptance_controller/runs/real_chrome_qianwen_yinzhou_weather-20260531_225006`。
- 第一次已连接真实 Chrome 并打开千问，但模型在输入框定位后遇到 Codex OAuth/API HTTP 503，中断于点击输入前。
- 第二次 run：`learning_agent/acceptance_controller/runs/real_chrome_qianwen_yinzhou_weather-20260531_225525`。
- 第二次日志确认 `browser_connect_real_chrome 成功`、`real_chrome_connected=true`、`browser_open 成功`、`browser_click 成功`、`browser_type 成功`、`browser_press_key 成功`、`browser_wait 成功`。
- 第二次真实 Chrome 页面可见千问回答：明天 6月1日 鄞州区天气晴，23℃～32℃，西北风 <3级，并提示防晒补水。

严格验收未通过原因：
- learning_agent 最终回答没有包含场景要求的固定标记和工具名清单。
- learning_agent 漏掉了场景要求的 `browser_screenshot` 工具调用。
- learning_agent 在已有 `browser_snapshot` 可见内容的情况下额外调用了 `browser_evaluate` 读取 `document.body.innerText`，这不符合真实 Chrome 默认隐私边界的最佳实践。

结论：
- 当前 agent 具备真实 Chrome 拟人点击、输入、提交并读取网页结果的能力。
- 但复杂真实浏览器任务的“严格按验收格式收尾”和“禁止 evaluate 的策略约束”还需要继续强化。
- `python -m unittest learning_agent.tests.test_observability_acceptance`：9 tests OK。
- `python -m unittest discover learning_agent`：387 tests OK，skipped=1。
- `python learning_agent\learning_agent.py mcp-doctor`：退出码 0，工作区和配置文件均为 H 盘，三个 MCP server 启动成功，模型可见 30 个 MCP 工具。
- 真实可见终端 smoke 验收第二次通过：`learning_agent/acceptance_controller/runs/smoke-20260531_140112/result.json` 显示 `completed=true`、`prompt_received=true`、`final_printed=true`，最终回答为 `ACCEPTANCE_HARNESS_OK`。
- 最终截图 `learning_agent/acceptance_controller/runs/smoke-20260531_140112/03_final.png` 已目视确认真实终端中显示 `Agent > ACCEPTANCE_HARNESS_OK`。

## 2026-05-31 H 盘运行路径修复

状态：已完成文件修改和主要验证。

证据：
- 用户确认当前实际运行目录是 `H:\codexworkplace\sofeware\OpenHarness-main`。
- 搜索确认 `learning_agent/mcp_servers.json` 曾把三个 MCP server 参数指向旧盘符下的 OpenHarness `learning_agent` 目录。
- 搜索确认 `AGENTS.md` 的学习备份路径和真实终端验收脚本路径曾指向旧盘符。
- 搜索确认 `agent_memory/context.md` 的项目根目录曾记录为旧盘符路径。

本次改动：
- 已把 `learning_agent/mcp_servers.json` 的 `browser_search`、`workspace_tools`、`browser_automation` 三组启动参数改为 H 盘当前项目路径。
- 已把 `AGENTS.md` 中学习备份目录和 `start_oauth_agent.bat` 强制验收路径改为 H 盘当前项目路径。
- 已把 `agent_memory/context.md` 当前项目根目录改为 H 盘当前项目路径。
- 历史 `debug_logs/` 和 `acceptance_controller/runs/` 中的历史盘符路径保留不改，因为它们是旧验收现场证据，不是当前运行配置。

验证结果：
- `learning_agent/mcp_servers.json` 已可被 PowerShell `ConvertFrom-Json` 正常解析，三个 MCP server 参数均显示为 H 盘路径。
- 三个 MCP server 文件路径均通过 `Test-Path`，说明 H 盘目标文件存在。
- 活跃运行配置与启动脚本范围内已搜不到旧盘符下的 OpenHarness 路径。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码为 0，工作区和配置文件均显示为 H 盘路径，`browser_search`、`workspace_tools`、`browser_automation` 三个 MCP server 启动成功，模型可见 30 个 MCP 工具。
- `python -m unittest learning_agent.tests.test_compat_cleanup` 通过，结果为 5 tests OK。

残留验证限制：
- `learning_agent.tests.test_mcp_registry` 全套测试在系统 Python 下剩余 2 个错误，错误原因是 `No module named 'playwright'`；这不是本次 D/H 路径修复导致。
- 沙盒内运行同一测试时，大量失败来自 `tempfile.TemporaryDirectory` 子目录写入被拒绝；沙盒外重跑后该类权限错误消失，只剩 Playwright 依赖缺失。

## 2026-05-30 阶段 13B 旧脚本入口收紧执行记录

状态：已完成代码改造、学习备份、自动化回归和 mcp-doctor；真实可见终端验收已启动但被 Codex OAuth/API HTTP 429 额度限制阻塞，尚不能声明开发完成。

完成内容：
- 扩展 `learning_agent/tests/test_compat_cleanup.py`，新增活跃测试/辅助脚本不再导入旧入口的扫描，以及 `learning_agent.py` 不再批量 re-export `core.agent` 的扫描。
- 红灯确认：新增保护测试最初失败，失败点分别是 `tests_support/legacy_learning_agent_suite.py` 仍导入旧入口、`learning_agent.py` 仍使用 `vars(agent_module).items()` 和 `globals()[exported_name]` 批量导出。
- 修改 `learning_agent/tests_support/legacy_learning_agent_suite.py`，把原来的旧入口大导入拆成 `app/core/models/mcp/tools` 分层导入。
- 修改 `learning_agent/fake_model_repl.py`，改为从 `core.agent` 和 `core.messages` 导入。
- 重写 `learning_agent/learning_agent.py`，仅保留路径兜底、`__path__` 脚本模式兜底、`app.cli.main` 导入和直接启动逻辑。
- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，补充阶段 13B 当前状态和后续导入导航。

已完成阶段性验证：
- 阶段 13B 保护测试通过：`python -m unittest learning_agent.tests.test_compat_cleanup`，4 tests OK。
- 语法检查通过：`learning_agent.py`、`fake_model_repl.py`、`tests_support/legacy_learning_agent_suite.py`、`tests/test_compat_cleanup.py`。
- 核心运行测试通过：`python -m unittest learning_agent.tests.test_core_run_loop`，40 tests OK。
- 假模型 REPL 自检通过：`python learning_agent\fake_model_repl.py --self-test` 退出码 0。
- 顶层 discovery 导入复现通过：在 `learning_agent` 目录执行 `python -c "import app"` 输出 `app import ok`。
- 完整回归通过：`python -m unittest discover learning_agent`，365 tests OK，skipped=1。
- MCP Doctor 通过：`python learning_agent\learning_agent.py mcp-doctor` 退出码 0，三个 MCP server 均启动成功，模型可见 30 个 MCP 工具。
- 真实可见终端验收已尝试：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_111154/result.json` 显示 `completed=false`、`permission_sent_count=0`、`marker_passed=true`，失败原因为模型首轮返回 HTTP 429 `usage_limit_reached`，未进入真实浏览器工具调用阶段。
- 继续尝试备用模型链路：本机 `codex.exe` 可用，版本为 `codex-cli 0.130.0-alpha.5`；但 `LEARNING_AGENT_MODEL_PROVIDER=codex` 的一次性 run 在 `codex exec` 90 秒超时，不能作为本轮验收替代。

## 2026-05-30 阶段 13 去兼容化第一刀执行记录

状态：阶段 13 第一刀已完成，并已通过自动化测试、mcp-doctor 和真实可见终端交互验收。

完成内容：
- 新增 `learning_agent/tools/schemas.py`，承载 `TOOL_SCHEMAS`、`KERNEL_TOOL_NAMES`、`DYNAMIC_SKILL_CAPABILITY_PACKS`、`BUILTIN_TOOL_CAPABILITY_PACKS`。
- 修改 `learning_agent/core/agent.py`，删除内置工具 schema 大块常量，改为从 `tools.schemas` 导入。
- 修改 `learning_agent/tools/catalog.py`，移除 `_main_entry_module()` 和 `_main_attr()` 旧入口回连。
- 修改 `learning_agent/mcp/runtime.py`，移除旧入口代理，直接依赖 `tools.catalog` 与 `tools.schemas`。
- 修改 `learning_agent/models/adapters.py`，默认输出 schema 改为读取 `DEFAULT_TOOL_SCHEMAS`。
- 修改 `learning_agent/app/cli.py` 和 `learning_agent/__init__.py`，让 app 层和包门面直接接新模块。
- 新增 `learning_agent/tests/test_compat_cleanup.py`，扫描生产模块禁止回流旧入口。
- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，补充阶段 13 当前状态和 `tools/schemas.py` 修 bug 索引。
- 已按用户学习备份规则，把本轮新增/修改文件复制到 `learning_agent/test/stage13_tool_schema_split_20260530/`。

已完成验证：
- `py_compile` 通过：`tools/schemas.py`、`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py`、`core/agent.py`、`__init__.py`、`tests/test_compat_cleanup.py`。
- 生产模块旧入口回流扫描通过：`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py`、`__init__.py` 中没有 `learning_agent.learning_agent` 导入。
- 新增回归通过：`python -m unittest learning_agent.tests.test_compat_cleanup`，2 tests OK。
- 工具层回归通过：`python -m unittest learning_agent.tests.test_tools_policy`，82 tests OK。
- MCP 层回归通过：`python -m unittest learning_agent.tests.test_mcp_registry`，108 tests OK。
- 模型层回归通过：`python -m unittest learning_agent.tests.test_models_codex_oauth`，46 tests OK。
- 聚焦组合回归通过：`python -m unittest learning_agent.tests.test_compat_cleanup learning_agent.tests.test_tools_policy learning_agent.tests.test_mcp_registry learning_agent.tests.test_models_codex_oauth`，238 tests OK。
- 完整回归通过：`python -m unittest discover learning_agent`，363 tests OK，skipped=1。
- MCP Doctor 通过：`python learning_agent\learning_agent.py mcp-doctor` 退出码 0，模型可见 30 个 MCP 工具，真实 Chrome profile 诊断为 available。
- 真实可见终端交互验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_104237/result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`，最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`、`real_chrome_connected=true`、`browser_click`、`browser_type`、`browser_press_key`、`browser_screenshot`。

## 2026-05-29 learning_agent 模块化重构阶段 11 测试拆分

状态：阶段 11 已完成；旧 `learning_agent/test_learning_agent.py` 已瘦身为兼容入口，新 `learning_agent/tests/` 包提供按领域运行的测试入口。

完成内容：
- 新增 `learning_agent/tests/` 包，包含 `test_core_run_loop.py`、`test_models_codex_oauth.py`、`test_mcp_registry.py`、`test_tools_policy.py`、`test_browser_intent.py`、`test_browser_harness.py`、`test_prompts_context.py`、`test_observability_acceptance.py`。
- 新增 `learning_agent/tests/_legacy_groups.py`，把遗留测试类按测试名关键字稳定分组，保证每条测试只有一个归属。
- 新增 `learning_agent/tests_support/legacy_learning_agent_suite.py`，承载原 112 万字节测试主体，并修复搬迁后的 `Path(__file__)` 资产定位。
- 修改 `learning_agent/test_learning_agent.py` 为旧入口兼容层；`python -m unittest learning_agent.test_learning_agent` 仍跑完整 359 条测试。
- 为 `python -m unittest discover learning_agent` 增加双导入兼容，避免目录 discovery 时 `learning_agent.py` 顶层模块遮蔽 `learning_agent` 包名。
- 已更新正式实施计划文档中阶段 11 的 Step 11.1-11.4 为完成。

验证记录：
- `py_compile` 覆盖新旧测试入口和 legacy suite，结果通过。
- 8 个分类入口分别通过：观测验收 9 条、浏览器意图 7 条、模型/OAuth 46 条、提示词上下文 36 条、工具策略 82 条、MCP registry 108 条、浏览器执行层 31 条（skipped=1）、核心兜底 40 条。
- 旧兼容入口通过：`Ran 359 tests in 25.301s OK (skipped=1)`。
- discovery 入口通过：`Ran 359 tests in 24.796s OK (skipped=1)`。

下一步：
- 进入阶段 12，删除 `learning_agent.py` 中已经委托到新模块后的不可达重复实现，把主文件收束成薄入口和兼容导出层。

## 2026-05-30 learning_agent 模块化重构阶段 12 瘦身入口

状态：阶段 12 已完成；代码瘦身、README/架构索引同步、自动化验收、MCP Doctor 和 `start_oauth_agent.bat` 真实可见终端验收均已通过，整体模块化改造阶段 0 到阶段 12 满足最终完成条件。

完成内容：
- `learning_agent/learning_agent.py` 已从约 1MB 巨型主文件收束为约 4.7KB 薄兼容入口，只负责脚本模式路径兜底、旧导入 re-export 和 `main()` 转发。
- `LearningAgent`、`ToolCallingFakeModel`、`TOOL_SCHEMAS`、工具循环、权限兼容入口和旧公开符号已经迁入 `learning_agent/core/agent.py`。
- `learning_agent/core/__init__.py` 已补充脚本模式 fallback，避免本地 MCP server 直接运行时因为 `learning_agent.py` 被当作顶层模块而导入失败。
- `core/agent.py` 的 packaged skill fallback 已改为从包根目录 `learning_agent/skills` 读取，避免迁移后误找 `learning_agent/core/skills`。
- `learning_agent/README.md` 已说明薄入口、`core/agent.py`、`app/`、`browser/`、`observability/` 和 `tests/` 的定位。
- `learning_agent/AGENT_ARCHITECTURE_INDEX.md` 已更新为当前落地架构地图，作为以后修 bug 的索引入口。
- 正式实施计划中 Step 12.1、12.2、12.3、12.4、12.5 已全部勾选完成。
- 本轮修复了真实 Chrome 环境探测误判：当 Windows 受限环境让 `Path.exists()` 或 `tasklist` 返回权限拒绝时，会用 PowerShell 只读 fallback 复查，避免误判 Chrome 正在运行或 User Data 缺失。

自动化验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\core\agent.py learning_agent\core\__init__.py learning_agent\browser_real_chrome.py` 退出码 0。
- `python -m unittest learning_agent.test_learning_agent` 结果为 `Ran 361 tests in 38.256s OK (skipped=1)`。
- `python -m unittest discover learning_agent` 结果为 `Ran 361 tests in 33.759s OK (skipped=1)`。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码 0，真实 Chrome profile 诊断为 `available`，Chrome 路径、User Data、进程状态和 9222 端口均识别正常；`browser_search`、`workspace_tools`、`browser_automation` 三个 MCP server 均启动成功，模型可见 MCP 工具 30 个。

真实可见终端验收记录：
- 命令：`powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\real_chrome_natural_weather_travel.json`。
- 结果文件：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_025500/result.json`。
- 验收结果：`completed=true`、`final_printed=true`、`prompt_sent=true`、`prompt_received=true`、`permission_sent_count=0`、`permission_count_passed=true`、`marker_passed=true`。
- 最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK` 和 `real_chrome_connected=true`。
- 动作链包含 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 截图证据：`learning_agent/browser_artifacts/real_chrome_chongqing_weather_travel_2026-05-31.png`。
- 阶段 12 修改文件和验收证据已备份到 `learning_agent/test/modular_refactor_stage12_20260529/`。

最终结论：
- 阶段 0 到阶段 12 的实施计划已完成，最终验收清单全部通过。

## 2026-05-27 Acceptance Harness 执行记录

状态：已完成最小验收协议模块、终端入口接入、自动化测试、MCP doctor、学习备份和真实可见终端 smoke 验收；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/acceptance_harness.py`，提供 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG`、`::learning-agent-acceptance ` 终端标记、JSONL 事件构造与写入。
- 已修改 `learning_agent/learning_agent.py`，让终端权限确认和交互主循环发出可观测状态事件。
- 已修改 `learning_agent/test_learning_agent.py`，新增 3 条回归测试覆盖默认静默、JSONL 写入和权限事件顺序。
- 已新增 `learning_agent/test/acceptance_harness_20260527/run_event_log_visible_terminal_smoke.ps1`，用于真实可见窗口 smoke 验收。
- 已把最终版 `acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`、计划文档和可见终端证据归档到 `learning_agent/test/acceptance_harness_20260527/`。

验证记录：
- 红灯验证：新增测试首次因 `ModuleNotFoundError: No module named 'learning_agent.acceptance_harness'` 失败；模块实现后权限事件测试又因事件文件不存在失败。
- 聚焦绿灯：3 条 Acceptance Harness 测试通过，输出 `Ran 3 tests in 0.030s OK`。
- 语法检查：`py_compile` 覆盖 `acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py` 通过。
- 完整回归：首次完整回归中浏览器下载测试出现一次空文件偶发失败；该单测单独复跑 1 次和连续 3 次均通过，随后完整回归重新通过：`Ran 335 tests in 22.247s OK (skipped=1)`。
- `mcp-doctor`：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 真实可见终端 smoke：通过 `start_oauth_agent.bat` 打开真实窗口，事件序列为 `permission_required -> permission_answered -> agent_ready_for_user_prompt -> user_prompt_received -> final_answer_printed -> agent_ready_for_user_prompt`，目标 agent 回复 `ACCEPTANCE_HARNESS_OK`。
- 最终版真实可见终端事件日志包含 `prompt_preview` 和 `answer_preview`，其中 `answer_preview` 为 `ACCEPTANCE_HARNESS_OK`。
- 可见终端结果文件：`learning_agent/test/acceptance_harness_20260527/event_log_visible_terminal_result.json` 显示 `completed=true`。

## 2026-05-27 重庆天气真实可见终端验收记录

状态：已完成 `start_oauth_agent.bat` 真实可见终端验收；目标 agent 成功调用浏览器自动化 MCP 查询重庆 2026-05-30 天气并生成旅游攻略；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/test/acceptance_harness_20260527/run_chongqing_weather_visible_terminal_acceptance.ps1`。
- 脚本会启动真实可见 `start_oauth_agent.bat` 窗口，设置 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG`，按事件日志等待权限、ready、prompt received 和 final answer。
- 脚本会自动同意启动 MCP server、`browser_open` 和 `browser_snapshot` 权限，并通过调试日志核验真实工具调用。
- 脚本会检查 `VISIBLE_WEATHER_ACCEPTANCE_OK`、`browser_open 成功`、`browser_snapshot 成功`、`2026-05-30`、`重庆`、`api.open-meteo.com`、`旅游攻略` 等证据。

验证记录：
- PowerShell 脚本解析检查通过，脚本已转换为 UTF-8 BOM 以兼容 Windows PowerShell 5.1。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- Acceptance Harness 聚焦测试通过：`Ran 3 tests in 0.041s OK`。
- 完整单元测试通过：`Ran 335 tests in 22.500s OK (skipped=1)`。
- `mcp-doctor` 通过：`browser_search`、`workspace_tools`、`browser_automation` 启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 真实可见终端天气验收通过：`CHONGQING_WEATHER_VISIBLE_TERMINAL_COMPLETED=True`，结果文件 `weather_visible_terminal_result.json` 显示 `completed=true`。
- 目标 agent 调用 `browser_open` 打开 Open-Meteo URL，并调用 `browser_snapshot` 读取 JSON。
- 本轮读取到的天气：重庆 2026-05-30 天气代码 51（毛毛雨），最高 28.3°C，最低 22.2°C，最大降水概率 25%，最大风速 4.0 km/h，紫外线指数 8.60。
- 目标 agent 最终生成了穿衣携带建议、重庆一日旅游攻略、下雨或高温备选方案和来源 URL。

## 2026-05-27 Acceptance Controller 执行记录

状态：已完成通用真实可见终端控制器、两个场景 JSON、结构回归测试、自动化回归、MCP doctor、真实可见终端 smoke 场景和重庆天气场景验收；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/acceptance_controller/controller.ps1`，统一处理真实窗口启动、事件等待、权限输入、prompt 重试、截图、事件日志、调试日志归档和 `result.json`。
- 已新增 `learning_agent/acceptance_controller/scenarios/smoke.json`，用于固定一行回答 smoke 验收。
- 已新增 `learning_agent/acceptance_controller/scenarios/chongqing_weather_browser.json`，用于重庆 2026-05-30 天气、浏览器 MCP 和旅游攻略验收。
- 已新增 `learning_agent/acceptance_controller/README.md`，说明运行方式和场景字段职责。
- 已修改 `learning_agent/test_learning_agent.py`，新增 2 条 Acceptance Controller 结构测试，锁定 controller 文件、场景 JSON 结构和通用事件协议关键字。
- 已将最终版 controller、场景、README、测试副本和本轮结果复制到 `learning_agent/test/acceptance_controller_20260527/`。

验证记录：
- 红灯验证：新增 controller 结构测试首次失败，失败点为缺少 `learning_agent/acceptance_controller/controller.ps1` 和相关场景文件。
- 聚焦绿灯：2 条 controller 结构测试通过；5 条 Acceptance 相关聚焦测试通过，输出 `Ran 5 tests in 0.041s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.048s OK (skipped=1)`。
- `mcp-doctor` 通过：`browser_search`、`workspace_tools`、`browser_automation` 启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 新 controller smoke 场景真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/smoke-20260527_230534/result.json` 显示 `completed=true`。
- 新 controller 重庆天气场景真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/chongqing_weather_browser-20260527_230607/result.json` 显示 `completed=true`。
- controller 版重庆天气日志确认 `browser_open 成功`、`browser_snapshot 成功`，读取到 `temperature_2m_max=28.3`、`temperature_2m_min=22.2`、`weather_code=51`。

## 2026-05-27 Real Chrome Profile Status 安全探针记录

状态：已完成真实 Chrome/profile 状态场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/test_learning_agent.py`，把 `real_chrome_profile_status.json` 纳入 Acceptance Controller 场景契约测试，并断言 prompt 必须包含 `real_chrome/SKILL.md`、`browser_profile_status` 和“不读取 cookies”的隐私边界。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_profile_status.json`，用于只读检查真实 Chrome/profile 状态，不连接真实 Chrome、不读取隐私网页内容。
- 已更新 `learning_agent/acceptance_controller/README.md`，补充 real Chrome profile status 场景运行命令。
- 已按学习备份规则复制 README、场景 JSON、测试副本和验收证据到 `learning_agent/test/real_chrome_profile_status_20260527/`。

验证记录：
- 红灯验证：`test_acceptance_controller_files_and_scenarios_are_valid` 先失败，失败点为缺少 `real_chrome_profile_status.json` 场景文件。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.011s OK`。
- Acceptance 聚焦回归：4 条相关测试通过，输出 `Ran 4 tests in 0.062s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 23.102s OK (skipped=1)`。
- `mcp-doctor` 通过：真实 Chrome profile 诊断为 `available`，Chrome 路径为 `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`，User Data 为 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data`，当前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_profile_status-20260527_232424/result.json` 显示 `completed=true`。
- 目标 agent 在真实终端中读取了 `learning_agent/skills/tool_list.md` 与 `learning_agent/skills/real_chrome/SKILL.md`，并调用 `mcp__browser_automation__browser_profile_status`。
- 状态工具返回：`mode=independent_chromium`、`real_chrome_connected=false`、`chrome_started_by_agent=false`、`endpoint=`、`profile=`、`pages=0`、最近安全拒绝为无；最终回答包含 `REAL_CHROME_PROFILE_STATUS_OK`。

## 2026-05-28 Real Chrome Connect Public Page 验收记录

状态：已完成场景级权限策略、真实 Chrome 连接公开页场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/acceptance_controller/controller.ps1`，新增 `permission_policy` 读取、大小写不敏感匹配、`Get-PermissionResponse` 决策函数，以及 `permission_policy_decisions` 结果审计。
- 已保持旧场景兼容：未配置 `permission_policy` 时默认继续输入 `y`，避免破坏 smoke、天气和 profile status 场景。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_connect_public_page.json`，默认拒绝未白名单权限，只允许启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 已修改 `learning_agent/acceptance_controller/README.md`，补充 connect 公开页场景运行命令和 `permission_policy` 字段说明。
- 已修改 `learning_agent/test_learning_agent.py`，新增场景结构和权限策略断言，锁定 connect 场景必须包含 `confirm_real_profile=true`、公开 URL、隐私边界、connect/open/snapshot 日志证据。
- 已按学习备份规则复制 controller、README、测试副本、场景 JSON 和验收证据到 `learning_agent/test/real_chrome_connect_public_page_20260528/`。

验证记录：
- 红灯验证：新增测试先失败，失败点为缺少 `real_chrome_connect_public_page.json` 和 controller 不包含 `permission_policy` / `Get-PermissionResponse` / `permission_policy_decisions`。
- 聚焦绿灯：2 条 Acceptance Controller 测试通过，输出 `Ran 2 tests in 0.047s OK`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.708s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，Chrome 路径和 User Data 均可识别，最终 Chrome 正在运行状态为 `false`，默认端口可用为 `true`。
- 第一次真实可见终端 connect 场景未通过：目标 agent 在 `browser_profile_status` 后的第 4 轮模型调用长时间无返回，未打印最终答案；失败证据位于 `runs/real_chrome_connect_public_page-20260528_053422/result.json`。
- 已基于失败根因收窄场景 prompt：减少第三个规则文件读取，并明确 status 后下一轮只调用 connect、connect 后只打开公开页、open 后只 snapshot。
- 第二次真实可见终端 connect 场景通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_connect_public_page-20260528_055137/result.json` 显示 `completed=true`。
- 真实终端事件序列包含 5 次权限请求并全部命中白名单：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 目标 agent 成功连接真实 Chrome：`browser_connect_real_chrome 成功`、`mode=real_chrome`、`real_chrome_connected=true`、`profile=Default`、`endpoint=http://127.0.0.1:9222`。
- 目标 agent 成功打开真实 Chrome 公开页：`browser_open 成功`，标题 `Example Domain`，URL `https://example.com/`。
- 目标 agent 成功读取公开页快照：`browser_snapshot 成功`，正文摘要包含 `Example Domain`。
- 最终回答包含 `REAL_CHROME_CONNECT_PUBLIC_PAGE_OK`，并声明未调用 `browser_evaluate`，未读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容或插件内容。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-28 Real Chrome Chongqing Weather Travel 验收记录

状态：已完成真实 Chrome 重庆天气攻略场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/test_learning_agent.py`，把 `real_chrome_chongqing_weather_travel.json` 纳入 Acceptance Controller 场景契约测试，并断言默认拒绝权限、真实 Chrome connect、Open-Meteo URL、2026-05-31、重庆、旅游攻略和隐私边界。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_chongqing_weather_travel.json`，只允许启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已更新 `learning_agent/acceptance_controller/README.md`，补充真实 Chrome 重庆天气攻略场景运行命令。
- 已按学习备份规则复制 README、测试副本、场景 JSON 和验收证据到 `learning_agent/test/real_chrome_chongqing_weather_travel_20260528/`。

验证记录：
- 红灯验证：`test_acceptance_controller_files_and_scenarios_are_valid` 先失败，失败点为缺少 `real_chrome_chongqing_weather_travel.json` 场景文件。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.012s OK`。
- Acceptance Controller 结构测试通过：`Ran 2 tests in 0.005s OK`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.140s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，验收前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_061032/result.json` 显示 `completed=true`。
- 真实终端事件序列包含 5 次权限请求并全部命中白名单：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 目标 agent 成功连接真实 Chrome：`browser_connect_real_chrome 成功`、`mode=real_chrome`、`real_chrome_connected=true`、`profile=Default`、`endpoint=http://127.0.0.1:9222`。
- 目标 agent 成功打开 Open-Meteo 公开天气 URL，并通过 `browser_snapshot` 读取重庆 2026-05-31 JSON。
- 本轮读取到的天气：重庆 2026-05-31 天气代码 51（毛毛雨），最高 31.0°C，最低 22.5°C，最大降水概率 39%，最大风速 6.4 km/h，紫外线指数 8.55。
- 目标 agent 最终输出 `REAL_CHROME_CHONGQING_WEATHER_TRAVEL_OK`，并生成穿衣携带建议、重庆一日旅游攻略、下雨或高温备选方案和来源 URL。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-28 Structured Permission Ledger 执行记录

状态：已完成结构化权限事件、controller 精确工具/URL 策略、TDD 红绿验证、完整回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，新增 `build_permission_event_payload()` 及辅助解析函数，把 MCP 工具权限文本解析为 `permission_kind`、`tool_name`、`arguments`、`risk_level`、`risk_summary`。
- 已修改 `ask_permission_from_terminal()`，让 `permission_required` 和 `permission_answered` 都写入结构化 payload，同时保留旧 `action` 字段兼容 controller 和历史日志。
- 已修改 `learning_agent/acceptance_controller/controller.ps1`，新增 `allow_tool_names`、`deny_tool_names`、`allow_url_prefixes` 读取和匹配逻辑。
- 已让 controller 的 `permission_policy_decisions` 写入 `tool_name`、`arguments`、`risk_level`、`risk_summary`、`url`，形成可审计 tool-call ledger。
- 已修改 `real_chrome_chongqing_weather_travel.json`，启动 MCP 仍用 `allow_contains`，真实 Chrome 和浏览器工具改用 `allow_tool_names`；`browser_open` 额外要求 URL 前缀 `https://api.open-meteo.com/v1/forecast`。
- 已更新 `learning_agent/acceptance_controller/README.md`，说明结构化权限策略字段。
- 已修改 `learning_agent/test_learning_agent.py`，新增结构化权限事件测试，并扩展 controller/场景契约测试。

验证记录：
- 红灯验证：新增测试先失败，失败点为 `permission_required` 缺少 `permission_kind`、天气场景缺少 `allow_tool_names`、controller 缺少 `allow_tool_names` / `allow_url_prefixes` / `payload.tool_name` / `payload.arguments`。
- 聚焦绿灯：同一组 3 条测试通过，输出 `Ran 3 tests in 0.094s OK`。
- Acceptance 聚焦回归：4 条相关测试通过，输出 `Ran 4 tests in 0.040s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- 完整单元测试通过：`Ran 338 tests in 22.214s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，验收前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_062749/result.json` 显示 `completed=true`。
- 本轮 `permission_policy_decisions` 记录了结构化字段；`browser_open` 的 `reason` 为 `allow_tool_name_and_url_prefix`，`matched_text` 为 `https://api.open-meteo.com/v1/forecast`。
- 目标 agent 成功连接真实 Chrome 并读取 Open-Meteo 重庆 2026-05-31 天气 JSON，最终输出 `REAL_CHROME_CHONGQING_WEATHER_TRAVEL_OK`。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-27 重庆天气浏览器自动化功能测试记录

状态：已完成 CLI 入口真实大模型浏览器工具链测试、日志核对、py_compile 和 MCP doctor；本轮未修改业务代码，未 stage，未 commit。当前 Codex 环境未完成用户本地可见 `start_oauth_agent.bat` 交互窗口验收，因此不能把本轮表述为开发验收完成。

完成内容：
- 已确认当前日期为 2026-05-27，3 天后为 2026-05-30。
- 已通过目标 `learning_agent` 的 `run --prompt --json` 入口执行重庆 2026-05-30 天气查询和旅游攻略生成任务。
- 已要求目标 agent 先读取 `learning_agent/skills/tool_list.md`，再读取 `learning_agent/skills/browser_automation/SKILL.md`，随后必须调用浏览器自动化 MCP 工具。
- 最新 `learning_agent/debug_logs/latest_run_readable.md` 确认目标 agent 调用了 `mcp__browser_automation__browser_open` 打开 Open-Meteo URL，并调用 `mcp__browser_automation__browser_snapshot` 读取页面正文 JSON。
- 测试输出已保存到 `learning_agent/test/chongqing_weather_browser_20260527/cli_run_output.txt`，本次摘要另存到 `learning_agent/test/chongqing_weather_browser_20260527/summary.md`。

验证记录：
- `py_compile`：`learning_agent.py`、`test_learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py` 编译通过。
- 完整单元测试：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 332 tests in 22.105s OK (skipped=1)`。
- `mcp-doctor`：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功；真实 Chrome profile 诊断为 `available`；模型可见 MCP 工具 30 个。
- 浏览器快照读取到 Open-Meteo JSON：重庆 2026-05-30 最高 28.9°C、最低 21.9°C、最大降水概率 29%、weather_code=3、最大风速 5.2 km/h、紫外线指数 8.50。
- 日志证据位置：`learning_agent/debug_logs/latest_run_readable.md` 中 `browser_open 成功`、`browser_snapshot 成功` 和最终中文攻略均可核对。

## 2026-05-27 learning_agent 项目水平分析记录

状态：已完成只读分析、源码抽样核对、测试验证和 MCP doctor 验证；未修改业务代码，未 stage，未 commit。

完成内容：
- 已读取 `agent_memory/context.md`、`progress.md`、`bugs.md`、`learning_agent/README.md`、`staticprompt/staticprompt.md`、`dynamicprompt/dynamicprompt.md`、`skills/tool_list.md`。
- 已抽查 `learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py`、启动脚本和 MCP 配置，确认文档中的四原子工具面、ToolPolicy、Prompt Architecture、MCP、浏览器、计划模式和任务管理等能力有源码落点。
- 已确认 `learning_agent/test_learning_agent.py` 当前包含 332 条 unittest 测试。
- 已用 Codex 自带 Python 执行语法检查，目标文件包括 `learning_agent.py`、`test_learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py`，结果通过。
- 已用 Codex 自带 Python 执行完整测试：`Ran 332 tests in 28.030s OK (skipped=1)`。
- 已执行 `learning_agent.py mcp-doctor`，确认 `browser_search`、`workspace_tools`、`browser_automation` 均启动成功，真实 Chrome profile 诊断为 `available`，模型可见 MCP 工具 30 个。

结论摘要：
- 当前 `learning_agent` 已达到“成熟 coding agent core 原型/教学版”的水平：核心架构、工具治理、提示词治理、MCP 接入、浏览器闭环和测试覆盖已经明显超过普通 demo。
- 当前仍不应宣称完整产品化或完全追平商业 Codex / Claude Code：真实可见终端交互验收不是本轮开发验收；真实 Chrome 登录态端到端、远程多用户安全、真实 git worktree、持久化定时任务和完整 UI 仍是边界。

## 2026-05-26 Prompt Files v3 执行记录

状态：实现已完成，聚焦测试和完整回归均已通过；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已将包内旧 `learning_agent/runtime_instructions.md` 重命名迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，旧文件路径不再保留。
- 已新增 `learning_agent/staticprompt/staticprompt.md`，承载每轮常驻的静态系统提示词，包含当前工作区占位符 `{{CURRENT_WORKSPACE}}`。
- 已修改 `learning_agent/learning_agent.py`，新增 `static_prompt_path` / `dynamic_prompt_path` 解析；`_build_initial_messages()` 改为读取 `staticprompt.md`，不再依赖 Python helper 拼系统提示词。
- 已删除源码中分散的静态系统提示词 helper，Python 只负责读取、占位符替换、兜底和动态规则发现。
- 已把 `dynamicprompt.md` 暴露为 `skill_load` 可读取的 `dynamicprompt` 伪 skill，保持动态规则按需加载。
- 已更新 `PromptRegistry`，把旧 `context.runtime_instructions` 元数据改为 `context.dynamic_prompt_index` 且标记为 `on_demand`。
- 已更新 `learning_agent/README.md` 和 `learning_agent/skills/prompt_architecture/SKILL.md`，说明新静态/动态提示词路径。
- 已新增/调整测试覆盖：静态提示词文件常驻加载、包内新文件存在、旧 runtime 文件删除、动态提示词不进首轮、动态提示词可通过 `skill_load` 按需加载。

验证记录：
- 红灯验证：新增聚焦测试先失败，失败点覆盖缺少 `static_prompt_path` / `dynamic_prompt_path`、默认提示词文件不存在。
- 聚焦绿灯：`Ran 6 tests in 0.100s OK`，覆盖本次文件化提示词迁移主路径。

## 2026-05-26 Lean System Prompt v2 执行记录

状态：已完成实现和完整回归验证，未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已将 `learning_agent/learning_agent.py` 的 `_build_core_identity_prompt()` 改为短核心身份，标题为 `Prompt Surface Architecture v2`。
- 已将 `_build_operating_principles_prompt()` 改为精简行为原则，保留工具可见文本、权限模式、Prompt Injection、Hooks、上下文压缩、先读代码、避免时间预估、失败诊断、安全和范围边界。
- 已将 `_build_context_policy_prompt()` 改为更明确的上下文优先级，纳入 `runtime_instructions.md`、`agent_memory` 三件套、`memory.md`、任务相关文件、工具 schema/MCP 说明和工具验证证据。
- 已从 `_build_initial_messages()` 的 `block_contents` 中移除 `prompt.policy.tool_boundary` 和 `prompt.policy.response`，避免每轮重复加载两块细节规则。
- 已重写 `learning_agent/runtime_instructions.md` 为短 Runtime Kernel，并把工具细节、skill router、capability pack、MCP/browser/real Chrome/delegation/diagnostics/cron/response policy 放入运行规则层。
- 已更新 `learning_agent/test_learning_agent.py` 的提示词回归测试，锁定新核心身份、精简 block 边界和 runtime skill router。
- 已把旧 `agent_memory/context.md`、`progress.md`、`bugs.md` 归档到 `agent_memory/archive/2026-05-26-lean-system-prompt/`，并将活跃三件套压缩为短摘要。

验证记录：
- 红灯验证：`test_system_prompt_uses_mature_coding_agent_identity` 首次失败，证明旧系统提示词仍在生效。
- 聚焦绿灯：`Ran 3 tests in 0.029s OK`，覆盖新系统身份、动态 compact 旧断言调整、短 runtime skill router。
- 完整回归首次只剩 1 个旧断言失败，原因是缺少 `知识与实时信息策略` 明确锚点。
- 已在 `runtime_instructions.md` 增加 `知识与实时信息策略` 小标题，保持核心系统提示词精简，同时满足实时信息策略锚点。
- 完整测试套件通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 313 tests in 21.527s OK (skipped=1)`。

下一步建议：
- 继续用 `prompt_surface_report` 和 `token_budget_report` 观察真实每轮提示词和工具池预算。
- 后续若再增长 runtime 关键词，应优先沉淀到 skill，而不是重新加回系统提示词。

## 2026-05-26 Dynamic Runtime Rules 执行记录

状态：已完成实现和完整回归验证，未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，让 `_build_initial_messages()` 不再把 `runtime_instructions.md` 作为 `context.runtime_instructions` 自动注入每轮 system prompt。
- 已把必要首轮底线上移到静态系统提示词：默认中文、证据边界、实时信息工具优先、动态规则加载路由、`skill_list`、`skill_load`、`tool_search`、`select_pack:<pack_name>`。
- 已修改 `skill_list` / `skill_load` 的发现范围，同时扫描工作区 `skills/` 和包内 `learning_agent/skills/`，让能力包规则可按需加载。
- 已把 `learning_agent/runtime_instructions.md` 改成动态运行规则索引，保留测试需要的工具关键词和规则入口，但不再作为每轮正文。
- 已更新 `learning_agent/skills/prompt_architecture/SKILL.md` 和 `learning_agent/README.md`，说明 runtime 现在是动态索引，不是常驻 prompt 正文。
- 已新增/调整测试覆盖 runtime 不再自动注入、静态 kernel 动态规则路由、包内 skills 可发现和可加载。

验证记录：
- 红灯验证：新增/调整的 5 条聚焦测试先失败，失败点覆盖 runtime 常驻注入、静态路由缺失、包内 skills 不可发现。
- 聚焦绿灯：同一组 5 条测试通过，输出 `Ran 5 tests in 0.064s OK`。
- 邻近 runtime/skill/prompt 回归通过，输出 `Ran 35 tests in 0.099s OK`。
- 完整测试套件通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 315 tests in 22.481s OK (skipped=1)`。
- 当时真实构造检查显示不包含 `context.runtime_instructions`；后续 Agent Memory Boundary 已进一步移除 `context.project_memory_index`。

## 2026-05-26 Prompt Files v3 最新状态

- 最新实现已把每轮静态系统提示词文件化到 `learning_agent/staticprompt/staticprompt.md`。
- 最新实现已把旧 runtime 文件迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，该文件只按需通过 `skill_load name=dynamicprompt` 或相关能力流程读取。
- 最新 `_build_initial_messages()` 加载块为：`prompt.kernel.identity`、`context.long_term_memory_index`。
- 本轮完整回归已通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 318 tests in 28.624s OK (skipped=1)`。
- 本轮学习备份已写入 `learning_agent/test/prompt_files_v3_20260526/`。

## 2026-05-26 Agent Memory Boundary 执行记录

状态：已完成实现、聚焦验证和完整回归；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已确认用户指出的问题成立：`agent_memory/context.md`、`progress.md`、`bugs.md` 是 Codex 开发本项目时的上下文，不应默认进入目标 `learning_agent` 的每轮 system prompt。
- 已修改 `learning_agent/learning_agent.py`，删除 `_read_project_agent_memory()` / `_find_project_agent_memory_dir()` 自动查找链路，并从 `_build_initial_messages()` 移除 `context.project_memory_index`。
- 已修改 `learning_agent/prompt_registry.py`，移除默认 `context.project_memory_index` prompt block。
- 已修改 `learning_agent/staticprompt/staticprompt.md`，删除 `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md` 的静态提示词关联。
- 已修改 `learning_agent/README.md`，说明目标 agent 每轮只默认读取 `staticprompt/staticprompt.md`、`memory.md` 和用户输入；`dynamicprompt.md` / skills 按需加载。

验证记录：
- 红灯验证：4 条聚焦测试先失败，失败点包含 `Project Memory Index` 仍进入 system prompt、静态提示词仍出现 `agent_memory/context.md`。
- 聚焦绿灯：同一组 4 条测试通过，输出 `Ran 4 tests in 0.032s OK`。
- 邻近回归：10 条 prompt/registry/预算测试通过，输出 `Ran 10 tests in 0.077s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 318 tests in 23.232s OK (skipped=1)`。
- 真实加载确认：`loaded_blocks=prompt.kernel.identity,context.long_term_memory_index`，`HAS_AGENT_MEMORY=False`，`HAS_MEMORY_INDEX=True`。

## 2026-05-26 Four Atom Tool Surface 执行记录

状态：已完成实现、README 同步、完整回归和语法检查；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，新增首轮模型可见的 `read`、`write`、`edit`、`bash` 四个原子工具 schema。
- 已将 `KERNEL_TOOL_NAMES` 收敛为四原子工具；`tool_search`、`skill_load`、MCP 工具和其他内置工具继续保留在内部 catalog，但默认 deferred，不再进入首轮 Tool Pool。
- 已新增 `_read_atom()`、`_write_atom()`、`_edit_atom()`、`_bash_atom()` 执行路径，并在 `_execute_tool()` 中分发这四个原子工具。
- 已新增 `learning_agent/skills/tool_list.md`，作为模型通过 `read` 发现能力和 skill 文件路径的入口。
- 已更新 `learning_agent/staticprompt/staticprompt.md`、`learning_agent/dynamicprompt/dynamicprompt.md`、`learning_agent/README.md`，统一说明 read-based skill discovery 和四原子工具面。
- 已更新 `learning_agent/test_learning_agent.py`，把旧首轮 `tool_search` / `skill_load` / `select_pack` 预期改为 `read / write / edit / bash` 与 `tool_list.md`。
- 已修正 static prompt 兜底文案，避免静态提示词文件损坏时重新提示旧工具搜索和能力包语法。

验证记录：
- 红灯验证：新增四原子聚焦测试先失败，失败点覆盖旧 kernel 工具仍首轮可见、`tool_list.md` 不存在、dynamicprompt 仍旧路由。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 321 tests in 22.497s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。

## 2026-05-26 CLI / HTTP Command Bridge 执行记录

状态：已完成实现、README 同步、完整回归和语法检查；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已扩展 `MainArgs` 和 `parse_main_args()`，新增 `run` 命令、`--prompt`、`--json`、`bridge` 命令、`--bridge-host`、`--bridge-port`、`--bridge-token`。
- 已新增 `format_cli_run_response()`，让 CLI 一次性运行可以输出 Codex 易解析的 JSON。
- 已新增 `LearningAgentCommandBridgeServer`、`LearningAgentCommandBridgeHandler` 和 `create_command_bridge_server()`。
- HTTP bridge 支持 `GET /health` / `/v1/health`，返回 `ok`、`agent`、`workspace` 和 `visible_tools`。
- HTTP bridge 支持 `POST /run` / `/command` / `/v1/run` / `/v1/command`，接收 JSON `prompt` 和可选 `max_turns`，返回 JSON `answer`、`workspace`、`visible_tools` 和 `max_turns`。
- 已在 `main()` 中接入一次性 CLI run 和 bridge serve 模式，同时保持原交互模式和 `doctor/mcp-doctor` 兼容。
- 已更新 `learning_agent/README.md`，补充 CLI run 和 HTTP command bridge 的启动命令、认证方式和请求示例。

验证记录：
- 红灯验证：新增 3 条聚焦测试先失败，失败点为无法导入 `create_command_bridge_server`。
- 聚焦绿灯：同一组 3 条测试通过，输出 `Ran 3 tests in 0.540s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 324 tests in 26.883s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。

## 2026-05-26 Dynamic Prompt Tree 执行记录

状态：已完成实现、README 同步、完整回归、语法检查和 CLI 真实入口验证；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已把 `learning_agent/skills/*/SKILL.md` 改成第二层轻入口，只保留能力判断、边界和 `rules/*.md` 子规则索引。
- 已新增 `learning_agent/skills/*/rules/*.md` 第三层子规则，承载 MCP、浏览器、真实 Chrome、文件、执行、计划、诊断、记忆、Notebook、委派和长期任务细节。
- 已从包内 skills 清理 `tool_search` / `select_pack` 旧路由文案，避免动态规则把模型拉回旧工具搜索架构。
- 已修改 `learning_agent/learning_agent.py`，让 `read` 记录已读取的动态提示词层级，并阻止模型跳过 `tool_list.md` 和父 `SKILL.md` 直接读取 `rules/*.md`。
- 已更新 `learning_agent/staticprompt/staticprompt.md`、`dynamicprompt/dynamicprompt.md`、`skills/tool_list.md` 和 README，统一描述 `tool_list.md -> SKILL.md -> rules/*.md` 三级加载顺序。
- 已更新 `learning_agent/test_learning_agent.py`，新增三级动态规则树和 read 层级门控回归测试，并调整旧 MCP skill 断言。

验证记录：
- 红灯验证：新增 2 条聚焦测试先失败，失败点覆盖所有旧 SKILL 缺少三级结构、`read` 可直接读取子规则。
- 聚焦绿灯：同一组 2 条测试通过，输出 `Ran 2 tests in 0.040s OK`。
- 相关回归：动态 prompt、skill、首轮工具池和 HTTP bridge 相关测试通过，输出 `Ran 4 tests in 0.604s OK` 与 `Ran 6 tests in 0.041s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 326 tests in 28.877s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- CLI 真实入口验证：通过 `LEARNING_AGENT_MODEL_PROVIDER=codex-cli` 执行 `learning_agent.py --max-turns 1 --prompt ... --json run`，返回 `ok=true`，回答确认采用 `tool_list.md -> SKILL.md -> rules/*.md` 分层，当前可见工具为 `read/write/edit/bash`。

## 2026-05-26 Current Date Prompt 执行记录

状态：已完成实现、单测回归、语法检查、CLI 真实入口验证和学习备份；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已新增 `learning_agent/learning_agent.py` 的 `get_local_iso_date()`，用本地日期生成 `YYYY-MM-DD`，作为系统提示词日期来源。
- 已修改 `_read_static_prompt()`，每轮读取 staticprompt 时替换 `{{CURRENT_DATE}}`，让 agent 每轮都能看到当天真实日期。
- 已修改 fallback static prompt，在静态提示词文件缺失、为空或路径异常时仍写入当前日期。
- 已修改 `learning_agent/staticprompt/staticprompt.md`，新增 `当前日期：{{CURRENT_DATE}}`，保持静态文件不写死日期。
- 已新增 `learning_agent/test_learning_agent.py` 聚焦测试，验证第一轮和第二轮 system prompt 都包含当天日期且不泄漏 `{{CURRENT_DATE}}`。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/current_date_prompt_20260526/`。

验证记录：
- 红灯验证：`python -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_static_prompt_renders_current_date_each_turn` 先失败，失败点为 system prompt 仍包含 `{{CURRENT_DATE}}` 而非 `2026-05-26`。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.011s OK`。
- 相关回归：`test_static_prompt_file_is_loaded_into_system_prompt`、`test_static_prompt_renders_current_date_each_turn`、`test_system_prompt_contains_current_info_policy` 三条通过，输出 `Ran 3 tests in 0.048s OK`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最终单独重跑输出 `Ran 329 tests in 23.137s OK (skipped=1)`。
- CLI 真实入口验证：通过 `LEARNING_AGENT_MODEL_PROVIDER=codex-cli` 执行 `learning_agent.py run --max-turns 1 --prompt "请只回答你在系统提示词中看到的当前日期..." --json`，返回 `ok=true` 且 `answer` 为 `2026-05-26`。

## 2026-05-26 Browser Automation 执行记录

状态：已完成实现、动态提示词同步、单测回归、完整回归、MCP doctor、HTTP command bridge 真实浏览器闭环和学习备份；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已新增 read-based dynamic skill unlock：读取 `browser_automation/SKILL.md` 后自动加载 `browser_automation` MCP 工具包。
- 已新增 real Chrome read-based 准备逻辑：读取 `real_chrome/SKILL.md` 后准备 `real_chrome` 和后续页面操作工具，但 connect 仍受 `browser_profile_status` workflow gate 保护。
- 已让读取 `real_chrome/SKILL.md` 自动设置 `real_chrome_requested=True`，防止真实 Chrome 路线在连接前误走独立 Chromium。
- 已让 `_resolve_workspace_path()` 兼容 CLI 默认 `learning_agent` 工作区下的 `learning_agent/skills/...` 项目根风格路径。
- 已同步更新 `browser_automation`、`real_chrome` 两个 SKILL.md 和子规则，说明读取 skill 后工具解锁与 profile status 前置边界。
- 已新增 3 条回归测试，覆盖 browser skill 解锁、real Chrome workflow 解锁、CLI 包目录路径兼容。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/browser_automation_20260526/`。

验证记录：
- 红灯验证：新增 2 条浏览器聚焦测试先失败，失败点为读取 skill 后 `browser_open` / `browser_connect_real_chrome` 仍未进入 Tool Pool。
- 聚焦绿灯：新增浏览器与路径兼容测试通过，输出 `Ran 3 tests in 0.030s OK`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 330 tests in 21.752s OK (skipped=1)`。
- MCP doctor：`learning_agent.py mcp-doctor` 显示 browser_search、workspace_tools、browser_automation 均启动成功，真实 Chrome profile 诊断为 `available`。
- HTTP command bridge 真实闭环：通过本地 bridge POST `/run` 下发真实 prompt，agent 读取 browser skill 后调用真实 MCP `browser_open` 和 `browser_snapshot`，返回 `ok=true`。

## 2026-05-26 Browser Weather Travel 真实验收执行记录

状态：已完成真实大模型端到端验收、CLI 入口验收、完整回归和启动脚本 selftest；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已按用户要求让目标 agent 查询 2026-05-29 北京天气并生成旅游攻略；该日期是当前日期 2026-05-26 的 3 天后。
- 已修复 `real browser automation` 被 `_detect_real_chrome_intent()` 误判为真实 Chrome/profile 请求的问题，避免普通 Playwright browser task 隐藏 `browser_open`。
- 已补齐 `_final_answer_retry_message()`，修复 HTTP bridge 在最终回答阶段因缺失方法返回 500 的问题。
- 已通过 HTTP command bridge 让真实 `CodexCliChatModel` 驱动目标 agent：先读取 `learning_agent/skills/tool_list.md`，再读取 `learning_agent/skills/browser_automation/SKILL.md`，随后调用 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- 已通过 CLI `learning_agent.py run --prompt ... --json` 再跑一次真实浏览器任务，权限输入自动喂 `y`，最新调试日志确认同样完成 `browser_open` 和 `browser_snapshot`。
- 已运行 `cmd /c learning_agent\start_oauth_agent.bat selftest`，验证用户指定启动脚本的自检路径可用。

验证记录：
- 聚焦回归：真实浏览器误判、browser skill 解锁、real Chrome workflow、Codex adapter 指令测试通过，输出 `Ran 6 tests in 0.665s OK`。
- 缺失方法修复回归：`test_run_retries_final_answer_when_required_markdown_headings_are_missing` 等 4 条通过，输出 `Ran 4 tests in 0.040s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 332 tests in 22.082s OK (skipped=1)`。
- 启动脚本 selftest：`cmd /c learning_agent\start_oauth_agent.bat selftest` 输出 `Ran 332 tests in 21.613s OK (skipped=1)`。
- HTTP bridge 真实验收结果保存到 `learning_agent/test/browser_weather_travel_20260526/result.json`，其中 `completed_browser_calls` 为 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- CLI 真实验收输出保存到 `learning_agent/test/browser_weather_travel_20260526/cli_run_output.txt`；该文件因 Windows 管道编码显示中文乱码，但 `learning_agent/debug_logs/latest_run_readable.md` 保留了可读中文调试证据。
- 最新浏览器快照读取到 Open-Meteo JSON：最高 30.5°C、最低 17.0°C、最大降水概率 0%、weather_code=1、最大风速 14.6 km/h。

## 2026-05-28 Real Chrome Google Human Visible 执行记录

状态：已完成实现、红绿灯回归、完整单测、MCP Doctor、真实可见终端交互验收和截图验证；未 stage，未 commit。

完成内容：
- 新增 `real_chrome_google_human_search.json` 场景，用于验证真实桌面 Chrome 打开 Google 后执行点击、输入、回车、等待、截图和快照读取。
- 修改 `controller.ps1`，新增 `post_success_wait_seconds`，场景成功后可保留真实窗口 20 秒让用户肉眼观察。
- 修改 `learning_agent.py`，让 `final_answer_printed` 事件保留 `answer_text` 完整回答，同时继续保留 `answer_preview`。
- 修改 `controller.ps1`，事件回答断言优先检查完整 `answer_text`，旧事件没有该字段时再退回 `answer_preview`。
- 新增/更新 `test_learning_agent.py` 回归测试，锁定 Google 拟人场景、成功后停留字段、完整回答事件字段和 controller 完整回答断言。

验证记录：
- 红灯验证：`test_acceptance_controller_script_uses_generic_event_protocol` 与 `test_interactive_acceptance_event_includes_full_final_answer_text` 先失败，证明旧 controller 不认识 `answer_text`，旧交互事件只写 `answer_preview`。
- 聚焦绿灯：同两条测试通过，输出 `Ran 2 tests in 0.037s OK`。
- 语法检查：`python -m py_compile learning_agent\acceptance_harness.py learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- PowerShell 解析：`[scriptblock]::Create($text)` 检查 `controller.ps1` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 339 tests in 21.962s OK (skipped=1)`。
- MCP Doctor：`learning_agent.py mcp-doctor` 显示 browser_search、workspace_tools、browser_automation 均启动成功，真实 Chrome profile `available`，运行前 Chrome 正在运行为 `false`。
- 第一次真实可见终端验收实际完成了 Google 点击输入截图，但因为 `answer_preview` 截断在 `- br`，`event_answer_checks.browser_screenshot=false`，控制器误判失败；该根因已修复。
- 第二次真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_google_human_search-20260528_064903/result.json` 显示 `completed=true`。
- Google 搜索结果页截图已目视验证非空，路径为 `learning_agent/browser_artifacts/real_chrome_google_human_search_20260528.png`。

## 2026-05-28 Real Browser Task Harness 执行记录

状态：已完成通用真实浏览器查询 harness、自然短 prompt 验收场景、红绿灯回归、完整单测、MCP Doctor、真实可见终端交互验收、截图验证、Chrome 清理；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`：补充 `真实浏览器` 触发词，新增 `_detect_real_browser_information_task()` 和 `_build_real_browser_task_harness_message()`，并在 `_build_initial_messages()` 中按需拼接 `Real Browser Task Harness`。
- 已修改 `learning_agent/skills/real_chrome/SKILL.md`：新增 `search_task_workflow.md` 子规则索引。
- 已新增 `learning_agent/skills/real_chrome/rules/search_task_workflow.md`：沉淀会议、酒店、航班、资料、天气、旅游攻略等公开查询的通用真实 Chrome Google 搜索流程。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_weather_travel.json`：使用自然短 prompt 触发真实浏览器查询，不把 `browser_click` / `browser_type` 等工具步骤写进用户 prompt。
- 已修改 `learning_agent/acceptance_controller/README.md`：补充自然短 prompt 真实浏览器验收场景运行命令。
- 已修改 `learning_agent/test_learning_agent.py`：新增短语识别、harness 注入、real_chrome 通用规则、自然短 prompt 场景契约回归测试。

验证记录：
- 红灯验证：4 条新增测试先失败，失败点分别为“真实浏览器”短语漏判、首轮没有 `Real Browser Task Harness`、`real_chrome` skill 未索引 `search_task_workflow.md`、自然短 prompt 场景文件不存在。
- 聚焦绿灯：同 4 条测试转绿，输出 `Ran 4 tests in 0.044s OK`。
- 第一次真实可见终端验收实际完成了真实 Chrome Google 搜索、点击、输入、回车、截图和攻略回答，但最终回答缺少机器可读 `real_chrome_connected=true` / `browser_click` 等工具名，导致 `event_answer_checks` 失败。
- 根因修复：harness 和 `search_task_workflow.md` 已要求最终回答包含 `real_chrome_connected=true` 和关键工具名；新增聚焦断言先失败再转绿。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\acceptance_harness.py`。
- PowerShell 解析通过：`[scriptblock]::Create($text)` 检查 `controller.ps1` 成功。
- 完整单测通过：`Ran 342 tests in 25.124s OK (skipped=1)`。
- MCP Doctor 通过：browser_search、workspace_tools、browser_automation 均启动成功；真实 Chrome profile `available`；最终清理后 Chrome 正在运行状态为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260528_073250/result.json` 显示 `completed=true`。
- 验收结果确认：权限策略默认拒绝，实际放行 11 次；日志断言和最终回答断言全部为 true；最终回答含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`、`real_chrome_connected=true`、关键工具名和截图路径。
- 截图目视确认：`learning_agent/browser_artifacts/real_chrome_chongqing_weather_travel_20260531.png` 是 Google 搜索结果页，搜索词为“重庆 2026年5月31日 天气 旅游攻略”。

## 2026-05-28 Real Browser Customer Mode 执行记录

状态：已完成红灯测试、实现、聚焦回归、完整单测、MCP Doctor、真实可见终端交互验收、截图验证和 Chrome 清理；未 stage，未 commit。

完成内容：
- 已新增 `ask_permission_from_terminal_customer_mode()`，项目内置 MCP 启动默认自动允许并发送 `permission_auto_approved` 事件，不再调用 `input()`。
- 已修改 `main()` 使用客户模式权限入口；JSON 一次性运行时会关闭启动进度文本，避免污染机器可读输出。
- 已新增 `real_browser_information_task_requested`，只在真实浏览器公开信息查询任务中启用自动授权。
- 已新增真实浏览器工具自动授权白名单和进度提示，用户会看到 `Agent > 正在检查真实 Chrome 状态...`、`Agent > 正在输入搜索词...` 等操作说明。
- 已更新 `controller.ps1`，支持 `max_permission_sent_count` 与 `permission_count_passed`，可自动证明客户模式没有 y/N 权限输入。
- 已更新自然短 prompt 真实浏览器验收场景，要求 `max_permission_sent_count` 为 0，并移除 `permission_required` / `permission_answered` 必需事件。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/real_browser_customer_mode_20260528/`。

验证记录：
- 红灯验证：新增测试最初因 `ask_permission_from_terminal_customer_mode` 不存在而失败，证明旧实现没有客户模式权限入口。
- 聚焦绿灯：客户模式 MCP 启动、白名单浏览器工具自动授权、敏感 `browser_evaluate` 不自动授权、验收场景和 controller 协议 5 条测试通过，输出 `Ran 5 tests in 0.066s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\acceptance_harness.py`；PowerShell `[scriptblock]::Create($text)` 解析 `controller.ps1` 通过。
- 完整单测通过：`Ran 345 tests in 27.780s OK (skipped=1)`。
- MCP Doctor 初次发现 9222 调试 Chrome 残留；已确认根进程命令行含 `--remote-debugging-port=9222 about:blank`，仅清理该自动化 Chrome 根进程。
- 清理后 MCP Doctor 通过：真实 Chrome profile `available`，Chrome 正在运行 `false`，默认端口可用 `true`，browser_search/workspace_tools/browser_automation 均启动成功。
- 真实可见终端交互验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260528_082044/result.json` 显示 `completed=true`。
- 无 y 验收关键结果：`permission_sent_count=0`、`max_permission_sent_count=0`、`permission_count_passed=true`；事件序列只有 `permission_auto_approved`、`agent_ready_for_user_prompt`、`user_prompt_received`、`final_answer_printed`、`agent_ready_for_user_prompt`，没有 `permission_required` 或 `permission_answered`。
- 真实浏览器截图已目视确认：`learning_agent/browser_artifacts/chongqing_weather_travel_2026-05-31.png` 为 Google 搜索结果页，搜索词是“重庆 2026年5月31日 天气 旅…”。
- 验收后已清理本次调试 Chrome 根进程，再次 MCP Doctor 确认 Chrome 未运行且 9222 端口可用。

## 2026-05-28 Real Browser YouTube Customer Mode 执行记录

状态：已完成根因确认、红灯测试、实现、聚焦回归、真实可见终端验收、截图验证、Chrome 清理和 MCP Doctor 复查；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`：把 YouTube/视频/评论/排行/有哪些等自然公开查询表达纳入 `_detect_real_browser_information_task()`。
- 已修改 `learning_agent/test_learning_agent.py`：新增 YouTube 自然短 prompt 识别测试，并把 YouTube 真实终端场景加入场景有效性检查列表。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_youtube_video_comments.json`：复现用户截图 prompt，要求真实终端验收中 `permission_sent_count=0`。
- 已清理用户截图旧会话残留的自动化 Chrome/MCP 子进程，用于释放 9222 端口；未杀掉用户可见终端主进程，但旧终端不会热加载新代码，需要重启 `start_oauth_agent.bat`。

验证记录：
- 红灯验证：`test_real_browser_youtube_video_question_is_customer_information_task` 先失败，失败点为 `_detect_real_browser_information_task(youtube_prompt)` 返回 `False`。
- 聚焦绿灯：YouTube 识别、客户模式自动授权、敏感工具拒绝、场景结构 4 条测试通过，输出 `Ran 4 tests in 0.041s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py`。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_youtube_video_comments-20260528_091026/result.json` 显示 `completed=true`。
- 无 y 验收关键结果：`permission_sent_count=0`、`max_permission_sent_count=0`、`permission_count_passed=true`；事件序列没有 `permission_required` 或 `permission_answered`。
- 验收日志确认真实浏览器动作：`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot` 全部命中断言。
- 真实终端截图已目视确认：`learning_agent/acceptance_controller/runs/real_chrome_natural_youtube_video_comments-20260528_091026/03_final.png` 展示最终回答和验收事件。
- 验收后已清理本次调试 Chrome 根进程，再次 MCP Doctor 确认 Chrome 正在运行 `false`，默认端口可用 `true`，3 个 MCP server 均启动成功。

## 2026-05-29 learning_agent 模块化重构实施计划记录

状态：已完成完整蓝图固化为正式实施计划文档；本轮未开始拆代码，未修改业务逻辑，未运行单元测试或真实终端功能验收。

完成内容：
- 已新增正式计划文档 `docs/superpowers/plans/2026-05-29-learning-agent-modular-refactor.md`。
- 计划覆盖阶段 0 到阶段 12：锁定基线、建立目录骨架、拆 core、拆 models、拆 mcp、拆 tools、拆 prompts、拆 browser、拆 tasks、拆 observability、整理 app、拆测试文件、瘦身 `learning_agent.py`。
- 已在计划中明确最终完成定义：阶段 12 完成后，必须同时满足结构完成、功能未回退、完整 unittest 通过、`mcp-doctor` 通过、真实可见终端验收通过、真实 Chrome 客户模式 `permission_sent_count=0`、文档同步完成，才算整体改造完成。
- 已新增学习备份 `learning_agent/test/modular_refactor_plan_20260529/IMPLEMENTATION_PLAN_BACKUP.md`。

下一步：
- 从阶段 0 开始执行，不直接跳到拆代码。
- 每阶段先读相关文件，再做聚焦迁移。
- 每阶段修改代码都需要逐行中文注释，并备份到 `learning_agent/test/<阶段名_日期>/`。
- 涉及 agent 行为变化的阶段必须完成真实可见终端 `start_oauth_agent.bat` 验收后，才能声明该阶段完成。

## 2026-05-29 learning_agent 模块化重构阶段 0 基线

状态：阶段 0 已完成；本阶段只做基线读取和验证，没有修改业务代码。

完成内容：
- 已记录 `learning_agent.py` 当前大小为 1056623 bytes。
- 已记录 `test_learning_agent.py` 当前大小为 1102954 bytes。
- 已创建基线文件 `learning_agent/test/modular_refactor_baseline_20260529/baseline.md`。
- 已把正式计划文档中的阶段 0 复选框标记为完成。

验证记录：
- 完整单元测试通过：`Ran 346 tests in 26.337s OK (skipped=1)`。
- MCP Doctor 通过：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。
- 真实 Chrome profile 诊断为 `available`，Chrome 正在运行 `false`，默认端口可用 `true`。
- 历史真实 Chrome 天气旅游验收记录确认：`completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。
- 历史真实 Chrome YouTube 查询验收记录确认：`completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。

下一步：
- 进入阶段 1：建立目录骨架和兼容导出。

## 2026-05-29 learning_agent 模块化重构阶段 1 目录骨架

状态：阶段 1 已完成；本阶段只新增目标目录和 `__init__.py`，没有迁移业务逻辑。

完成内容：
- 已新增 `learning_agent/app/__init__.py`。
- 已新增 `learning_agent/core/__init__.py`。
- 已新增 `learning_agent/models/__init__.py`。
- 已新增 `learning_agent/tools/__init__.py`。
- 已新增 `learning_agent/mcp/__init__.py`。
- 已新增 `learning_agent/browser/__init__.py`。
- 已新增 `learning_agent/prompts/__init__.py`。
- 已新增 `learning_agent/memory/__init__.py`。
- 已新增 `learning_agent/tasks/__init__.py`。
- 已新增 `learning_agent/observability/__init__.py`。
- 已新增 `learning_agent/tests_support/__init__.py`。
- 已新增学习备份说明 `learning_agent/test/modular_refactor_stage1_20260529/README.md`。
- 已把正式计划文档中的阶段 1 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整单元测试通过：`Ran 346 tests in 22.125s OK (skipped=1)`。

下一步：
- 进入阶段 2：拆 `core/messages.py` 和 `core/config.py`。

## 2026-05-29 learning_agent 模块化重构阶段 2 core 拆分

状态：阶段 2 已完成；已把基础配置解析与模型消息结构迁移到 `learning_agent/core/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/core/messages.py`，承载 `ToolCall` 和 `ModelMessage`。
- 已新增 `learning_agent/core/config.py`，承载运行配置、CLI 参数解析、轮次策略、prompt 软预算和本地日期函数。
- 已修改 `learning_agent/learning_agent.py`：从 `core.config` 和 `core.messages` 导入上述对象，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_core_messages_exports_tool_call_and_model_message`、`test_core_config_exports_runtime_parsers`。
- 已新增/更新学习备份目录 `learning_agent/test/modular_refactor_stage2_20260529/`。
- 已把正式计划文档中的阶段 2 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\core\messages.py learning_agent\core\config.py learning_agent\test_learning_agent.py` 通过。
- 聚焦测试通过：`python -m unittest learning_agent.test_learning_agent -k core` 输出 `Ran 2 tests in 0.001s OK`。
- 完整单元测试通过：`Ran 349 tests in 22.847s OK (skipped=1)`。

验证中发现并处理的问题：
- `mcp-doctor` 访问真实 Chrome User Data 目录时，如果 Windows 返回 `PermissionError`，会直接崩溃；已修改 `browser_real_chrome.py` 让不可访问候选路径被跳过并继续生成诊断报告。
- 后台命令在 Windows sandbox 下 `taskkill` 可能返回 `Access denied`，导致子进程继续占用临时工作目录；已让后台命令在 Windows 使用独立进程组，并优先用 `CTRL_BREAK_EVENT` 收束进程组，同时关闭管道并等待 reader 线程退出。

下一步：
- 进入阶段 3：拆 `models/`。

## 2026-05-29 learning_agent 模块化重构阶段 3 models 拆分

状态：阶段 3 已完成；已把模型接口、OpenAI-compatible 模型、Codex CLI 模型、Codex OAuth/API 模型和 OAuth token 逻辑迁移到 `learning_agent/models/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/models/base.py`，承载 `ChatModel` 模型接口。
- 已新增 `learning_agent/models/adapters.py`，承载 `OpenAIChatModel`、`CodexCliChatModel`、`CodexOAuthTokens`、`CodexOAuthTokenStore`、`CodexOAuthChatModel`。
- 已新增 `learning_agent/models/openai_chat.py`、`codex_cli.py`、`oauth_tokens.py`、`codex_oauth.py` 作为稳定导入入口。
- 已修改 `learning_agent/learning_agent.py`：从 `models/` 导入模型类和回调类型，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_models_package_exports_chat_model_adapters`，锁定新模块导出和旧入口兼容。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage3_20260529/`。
- 已把正式计划文档中的阶段 3 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\models\base.py learning_agent\models\adapters.py learning_agent\models\openai_chat.py learning_agent\models\codex_cli.py learning_agent\models\oauth_tokens.py learning_agent\models\codex_oauth.py learning_agent\test_learning_agent.py` 通过。
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.models.base'`。
- 模型导入测试迁移后通过：`Ran 1 test in 0.000s OK`。
- 聚焦测试通过：`-k models` 输出 `Ran 1 test in 0.000s OK`。
- 聚焦测试通过：`-k oauth` 输出 `Ran 12 tests in 0.006s OK`。
- 聚焦测试通过：`-k codex_cli` 输出 `Ran 3 tests in 0.014s OK`。
- 完整单元测试通过：`Ran 350 tests in 21.976s OK (skipped=1)`。

验证中观察：
- 按计划没有改变模型请求 body、OAuth 刷新、重登录或远端断连判断，只改变代码所在文件。
- 完整测试第一次运行时，浏览器上传下载测试偶发读到空下载文件；随后单独复现通过，完整测试重跑通过。当前判断为浏览器下载异步落盘时序观察，已记录到 `agent_memory/bugs.md`，阶段 3 不修改该浏览器模块。

下一步：
- 进入阶段 4：拆 `mcp/`。

## 2026-05-29 learning_agent 模块化重构阶段 4 MCP 拆分

状态：阶段 4 已完成；已把 MCP 配置、客户端、registry、auth challenge 和 doctor 迁移到 `learning_agent/mcp/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/mcp/runtime.py`，承载 MCP 运行时主实现。
- 已新增 `learning_agent/mcp/config.py`、`auth.py`、`stdio_client.py`、`http_client.py`、`sse_client.py`、`registry.py`、`doctor.py`、`tool_adapter.py` 作为稳定导入入口。
- 已修改 `learning_agent/mcp/__init__.py`：统一 re-export MCP 公开对象。
- 已修改 `learning_agent/learning_agent.py`：从 `mcp/` 导入 MCP 对象，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_mcp_package_exports_config_and_registry`，锁定新模块导出和旧入口兼容。
- 已处理阶段 4 暴露的 doctor monkeypatch 兼容问题：`run_mcp_doctor()` 通过兼容层优先读取旧主入口诊断替身，再回退真实诊断。
- 已处理重复出现的浏览器下载落盘时序问题：上传下载测试现在等待两个下载文件内容都包含 `hello-download` 后才判定完成。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage4_20260529/`。
- 已把正式计划文档中的阶段 4 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\mcp\runtime.py learning_agent\test_learning_agent.py` 通过。
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.mcp.config'`。
- MCP 导入测试迁移后通过：`Ran 1 test in 0.000s OK`。
- 聚焦 doctor 测试通过：`Ran 1 test in 0.007s OK`。
- 浏览器上传下载聚焦测试通过：`Ran 1 test in 3.124s OK`。
- MCP 全组测试通过：`Ran 105 tests in 16.259s OK`。
- `learning_agent\learning_agent.py mcp-doctor` 退出码为 0，并列出 30 个 MCP 工具。
- 完整单元测试通过：`Ran 351 tests in 22.502s OK (skipped=1)`。

下一步：
- 进入阶段 5：拆 `tools/`。

## 2026-05-29 learning_agent 模块化重构阶段 5 tools 拆分

状态：阶段 5 已完成；已把工具元数据、catalog、工具池过滤、执行分发、策略兼容入口、四原子轻量 helper 和长结果存储 helper 迁移到 `learning_agent/tools/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/tools/types.py`，承载 `AgentTool`。
- 已新增 `learning_agent/tools/catalog.py`，承载 `agent_tool_from_schema`、`builtin_tool_capability_pack`、`build_builtin_tool_catalog`。
- 已新增 `learning_agent/tools/pool.py`，承载当前工具池、allowed_tools 过滤、工具名提取和策略决策 helper。
- 已新增 `learning_agent/tools/executor.py`，承载 `_execute_tool` 的执行守卫和分发表。
- 已新增 `learning_agent/tools/policy.py`，作为 `ToolPolicy` 新命名空间兼容入口。
- 已新增 `learning_agent/tools/atom_tools.py`，承载四原子工具轻量 helper。
- 已新增 `learning_agent/tools/result_storage.py`，承载长工具结果文件名、inline limit 和摘要 helper。
- 已修改 `learning_agent/learning_agent.py`：删除本地 `AgentTool` 和 catalog builder 实现；`_execute_tool` 改为委托 `tools.executor`；工具池、结果存储和原子工具轻量逻辑改为委托 `tools/`。
- 已修改 `learning_agent/test_learning_agent.py`：新增/扩展工具层导入测试，覆盖 `types`、`catalog`、`pool` 和 `policy` 新入口。
- 已把正式计划文档中的阶段 5 复选框标记为完成。

验证记录：
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.tools.catalog'`。
- `py_compile learning_agent\learning_agent.py learning_agent\tools\*.py learning_agent\test_learning_agent.py` 通过。
- 工具层新导入测试通过：`Ran 1 test in 0.009s OK`。
- 工具 catalog 聚焦测试通过：`Ran 2 tests in 0.013s OK`。
- 原子工具聚焦测试通过：`Ran 3 tests in 0.035s OK`。
- 长结果落盘聚焦测试通过：`Ran 1 test in 0.027s OK`。
- 权限测试通过：`Ran 20 tests in 0.251s OK`。
- 工具全组测试通过：`Ran 134 tests in 5.156s OK`。
- `learning_agent\learning_agent.py mcp-doctor` 退出码为 0，并列出 30 个 MCP 工具。
- 完整单元测试通过：`Ran 352 tests in 22.522s OK (skipped=1)`。

当前结构说明：
- `learning_agent.py` 仍保留大量具体工具实现方法，这是为了避免一次性搬动文件、后台命令、task、team、plan、lsp、cron 等多类副作用逻辑。
- 阶段 5 已完成“工具层边界”和“执行入口分发表”拆分；后续阶段 6-8 可以继续把 prompts/browser/app/session 相关具体实现迁出。

下一步：
- 进入阶段 6：拆 `prompts/`。

## 2026-05-29 learning_agent 模块化重构阶段 6 prompts 拆分

状态：阶段 6 已完成；已把静态提示词、动态提示词、提示词注册表、上下文装配、token 预算和提示词表面报告入口收拢到 `learning_agent/prompts/`，旧入口仍保持兼容。

完成内容：
- 已新增 `learning_agent/prompts/static_prompt.py`，承载 `staticprompt.md` 路径解析、读取、`{{CURRENT_WORKSPACE}}` 与 `{{CURRENT_DATE}}` 渲染、空文件/缺失文件/目录路径兜底。
- 已新增 `learning_agent/prompts/dynamic_prompt.py`，承载 `dynamicprompt.md` 路径解析和伪 skill 元信息生成，保持 dynamicprompt 按需读取，不进入常驻 system prompt。
- 已新增 `learning_agent/prompts/registry.py`，作为 `PromptRegistry`、`PromptBlock` 和 `build_default_prompt_registry` 的新命名空间兼容入口。
- 已新增 `learning_agent/prompts/context_assembler.py`，作为 `ContextAssembler`、`PromptSurfaceReport`、`build_long_term_memory_index` 等上下文装配对象的新命名空间兼容入口。
- 已新增 `learning_agent/prompts/token_budget.py` 和 `learning_agent/prompts/surface_report.py`，为后续预算和报告继续瘦身提供稳定入口。
- 已修改 `learning_agent/prompts/__init__.py`，统一 re-export prompts 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 prompts 层导入 prompt/context 对象，并把 `_read_static_prompt()`、`_fallback_static_prompt()`、`_resolve_static_prompt_path()`、`_resolve_dynamic_prompt_path()`、`_dynamic_prompt_skill_metadata()` 改成委托新模块。
- 已修改 `learning_agent/test_learning_agent.py`，新增 `test_prompts_package_exports_static_prompt_loader`，锁定新 prompts 包入口。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage6_20260529/`，保存阶段 6 修改后的主文件、测试文件、prompts 模块和实施计划快照。
- 已把正式实施计划文档中的阶段 6 四个步骤全部勾选完成。

验证记录：
- 红灯验证：新增 prompts 导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.prompts.static_prompt'`。
- 语法检查通过：`py_compile learning_agent.py prompts/*.py test_learning_agent.py`。
- 新增导入测试通过：`Ran 1 test in 0.000s OK`。
- prompt 专项回归通过：`python -m unittest learning_agent.test_learning_agent -k prompt` 输出 `Ran 46 tests in 1.012s OK`。
- context 专项回归通过：`python -m unittest learning_agent.test_learning_agent -k context` 输出 `Ran 7 tests in 0.017s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 353 tests in 27.346s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个；当前真实 Chrome 诊断为 `blocked`，原因为本机已有 Chrome 正在运行且未找到可用 User Data 路径，本阶段未触碰真实 Chrome 功能。

当前结构说明：
- `learning_agent.py` 仍保留提示词构建的编排职责，但文件化 prompt 的细节已经移入 `prompts/`。
- `prompt_registry.py` 和 `context_assembler.py` 目前作为旧兼容实现继续存在，`prompts/registry.py` 与 `prompts/context_assembler.py` 先作为稳定新入口重导出，避免一次性移动大段已测试代码造成风险。

下一步：
- 进入阶段 7：拆 `browser/`，重点迁移真实浏览器意图识别、真实 Chrome harness、客户模式授权白名单和搜索工作流。

## 2026-05-29 learning_agent 模块化重构阶段 7 browser 拆分

状态：阶段 7 已完成；已把真实浏览器意图识别、真实浏览器任务 harness、客户模式自动授权、Google 搜索流程常量和浏览器产物路径安全 helper 收拢到 `learning_agent/browser/`，旧入口仍保持兼容。

完成内容：
- 已新增 `learning_agent/browser/intent.py`，承载真实 Chrome 意图、真实浏览器公开信息查询意图、独立浏览器工具集合和真实 Chrome 前置阻断判断。
- 已新增 `learning_agent/browser/harness.py`，承载自然短 prompt 的真实浏览器查询任务约束文本。
- 已新增 `learning_agent/browser/permissions.py`，承载真实浏览器客户模式是否激活、MCP 工具自动授权原因、终端 MCP 启动自动授权和客户可见进度文案。
- 已新增 `learning_agent/browser/search_workflow.py`，承载 Google URL 白名单、客户模式固定工具白名单和最终回答动作名清单。
- 已新增 `learning_agent/browser/artifacts.py`，承载浏览器截图/下载产物文件名清洗和安全路径生成。
- 已修改 `learning_agent/browser/__init__.py`，统一 re-export browser 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 browser 层导入上述 helper，并让旧方法入口委托新模块。
- 已修改 `learning_agent/browser_automation_mcp_server.py`，让 `safe_artifact_path()` 先委托 `browser.artifacts.safe_browser_artifact_path()`。
- 已修改 `learning_agent/test_learning_agent.py`，新增真实浏览器意图、客户模式权限和产物路径 helper 的模块入口测试。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage7_20260529/`，保存阶段 7 修改后的主文件、测试文件、browser 模块、MCP server 和实施计划快照。
- 已把正式实施计划文档中的阶段 7 六个步骤全部勾选完成。

验证记录：
- 红灯验证：新增浏览器意图导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.browser.intent'`。
- 语法检查通过：`py_compile learning_agent.py browser/*.py browser_automation_mcp_server.py test_learning_agent.py`。
- 新增浏览器层导入/权限/产物路径测试通过：3 条测试均 OK。
- 浏览器专项回归通过：`-k real_browser` 输出 `Ran 7 tests in 0.042s OK`。
- 真实 Chrome 专项回归通过：`-k real_chrome` 输出 `Ran 36 tests in 3.862s OK (skipped=1)`。
- YouTube 客户模式专项回归通过：`-k youtube` 输出 `Ran 1 test in 0.003s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 356 tests in 22.521s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260529_105333/result.json` 显示 `completed=true`、`permission_sent_count=0`、`permission_count_passed=true`，最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`。

当前结构说明：
- browser 层已经成为真实浏览器意图、客户模式授权和产物路径安全的稳定入口。
- `learning_agent.py` 目前仍保留部分旧浏览器方法体作为兼容过渡，但执行路径已优先委托到 `learning_agent/browser/`；阶段 12 瘦身时应删除这些重复业务实现。
- `browser_real_chrome.py` 本阶段未做新改动；真实 Chrome profile 诊断仍属于独立 helper 文件职责。

下一步：
- 进入阶段 8：拆 `tasks/`，重点迁移后台命令、子任务、多 agent 教学版、cron/monitor 等长任务记录类和 helper。

## 2026-05-29 learning_agent 模块化重构阶段 8 tasks 拆分

状态：阶段 8 已完成；已把后台命令、task 子 agent、team 通信、cron 和 monitor 的记录类与纯 helper 迁移到 `learning_agent/tasks/`，旧工具输出和教学版边界保持兼容。

完成内容：
- 已新增 `learning_agent/tasks/background.py`，承载 `BackgroundCommand`、后台输出队列读取 helper 和后台命令状态格式化 helper。
- 已新增 `learning_agent/tasks/task_runs.py`，承载 `TaskRun`、禁止子 agent 继承的任务工具集合、`background` 参数解析和子 agent prompt 构造 helper。
- 已新增 `learning_agent/tasks/team.py`，承载 `TeamMessage`、`TeamPeer` 和根据待确认消息数计算 peer 状态的 helper。
- 已新增 `learning_agent/tasks/cron_monitor.py`，承载 `CronRecord`、`MonitorRecord`、cron/monitor 状态解析、结果数解析、monitor 结果状态解析和记录格式化 helper。
- 已修改 `learning_agent/tasks/__init__.py`，统一 re-export tasks 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 tasks 层导入记录类和 helper，并让相关旧方法入口委托新模块。
- 已修改 `learning_agent/test_learning_agent.py`，新增 `test_tasks_package_exports_background_and_task_records`，锁定 tasks 包入口。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage8_20260529/`，保存阶段 8 修改后的主文件、测试文件、tasks 模块和实施计划快照。
- 已把正式实施计划文档中的阶段 8 三个步骤全部勾选完成。

验证记录：
- 红灯验证：新增 tasks 导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.tasks.background'`。
- 语法检查通过：`py_compile learning_agent.py tasks/*.py test_learning_agent.py`。
- 新增导入测试通过：`Ran 1 test in 0.000s OK`。
- task 专项回归通过：`-k task` 输出 `Ran 24 tests in 0.315s OK`。
- background 专项回归通过：`-k background` 输出 `Ran 8 tests in 0.243s OK`。
- cron 专项回归通过：`-k cron` 输出 `Ran 4 tests in 0.019s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 357 tests in 28.619s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。

当前结构说明：
- tasks 层现在是长期任务记录类和纯 helper 的稳定入口。
- 实际副作用编排仍留在 `learning_agent.py`：例如创建子 agent、启动后台进程、权限确认、team 绑定 task、cron/monitor 工具输出编排；这是为了保持教学版行为兼容并避免一次性搬动高风险运行时逻辑。
- 本阶段未升级为产品级队列、真实系统定时器、持久化后台调度或真实通知系统。

下一步：
- 进入阶段 9：拆 `observability/`，重点迁移 debug log、验收事件、权限事件和 run record 的观测层入口。
## 2026-05-29 learning_agent 模块化重构阶段 10 app 拆分

状态：阶段 10 已完成；CLI、doctor、HTTP bridge 和交互式终端入口已经迁入 `learning_agent/app/`，`learning_agent.py` 保留兼容转发。

完成内容：
- 新增 `learning_agent/app/cli.py`：承载 `main()`、`build_model_from_env()`、`format_cli_run_response()`，并通过依赖注入避免直接循环导入 `LearningAgent`。
- 新增 `learning_agent/app/doctor.py`：承载 app 层 `run_mcp_doctor()`，委托 MCP 层真实诊断。
- 新增 `learning_agent/app/http_bridge.py`：承载 `LearningAgentCommandBridgeServer`、`LearningAgentCommandBridgeHandler`、`create_command_bridge_server()` 和 `serve_command_bridge()`。
- 新增 `learning_agent/app/interactive.py`：承载真实用户可见交互式终端循环和验收事件写入。
- 修改 `learning_agent/app/__init__.py`：导出 `main` 和 `run_mcp_doctor`。
- 修改 `learning_agent/learning_agent.py`：原 `main()` 现在转发到 `app.cli.main(agent_cls=LearningAgent, permission_callback=ask_permission_from_terminal_customer_mode)`；旧 `build_model_from_env()`、`format_cli_run_response()`、`create_command_bridge_server()` 保留兼容包装并委托 app 层。
- 修改 `learning_agent/test_learning_agent.py`：新增 `test_app_package_exports_main_entrypoints`。
- 已备份到 `learning_agent/test/modular_refactor_stage10_20260529/`。
- 已把正式实施计划文档中阶段 10 的 Step 10.1-10.4 勾选完成。

验证记录：
- app 入口红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.app.cli'`。
- `py_compile learning_agent.py app/*.py test_learning_agent.py` 通过。
- `python -m unittest learning_agent.test_learning_agent -k app_package` 通过。
- `python -m unittest learning_agent.test_learning_agent -k command_bridge` 通过。
- `python learning_agent\learning_agent.py --help` 通过。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码 0，三个 MCP server 均启动成功，模型可见 MCP 工具 30 个。
- `python learning_agent\learning_agent.py run --prompt "ping" --json --max-turns 1` 输出干净 JSON；当前无 `OPENAI_API_KEY` 时返回结构化模型错误，符合预期。
- 完整单元测试通过：`Ran 359 tests in 25.939s OK (skipped=1)`。

当前结构说明：
- app 层已经成为启动入口层，主文件不再需要直接承载完整 CLI/bridge/interactive 编排。
- `learning_agent.py` 中仍保留了旧 app 入口实现的不可达兼容代码，阶段 12 瘦身时需要删除。
- 下一步进入阶段 11：拆分 `test_learning_agent.py`，让测试按模块路径定位。
## 2026-05-30 Stage 13C progress: existing CDP attach for visible Chrome

Status: completed for Stage 13C; code, automated regression, MCP doctor, and visible-terminal acceptance all passed.

What changed:
- Updated `learning_agent/browser_automation_mcp_server.py` so `browser_connect_real_chrome()` checks the requested local CDP port when Chrome is already running.
- Added attach mode to `_connect_real_chrome_after_checks()` through `attach_existing_cdp` and `existing_debug_port`.
- In attach mode, the server does not launch a new Chrome process and keeps `chrome_process=None`, preserving the safety rule that disconnecting should not close the user’s already-open Chrome.
- Updated `learning_agent/browser_real_chrome.py` so `diagnose_real_chrome_environment()` reports `available` when 9222 is occupied by trusted Chrome CDP, preventing `mcp-doctor` and the model from treating an attachable Chrome as a blocker.
- Updated `learning_agent/tests_support/legacy_learning_agent_suite.py` with two RealChrome branch tests: allow attach when existing CDP is live, block when Chrome is running without trusted CDP.
- Updated `learning_agent/AGENT_ARCHITECTURE_INDEX.md` with Stage 13C notes so future agents can find this boundary quickly.

Red/green record:
- Red: `python -m unittest learning_agent.tests_support.legacy_learning_agent_suite.LearningAgentTests.test_browser_connect_real_chrome_attaches_when_running_chrome_has_cdp` failed under old code with the exact running-Chrome refusal.
- Green: the same test passed after the attach-mode implementation.
- Guard: `test_browser_connect_real_chrome_blocks_when_chrome_is_running_without_cdp` passed, proving the profile-lock protection is still present when no trusted CDP exists.
- Diagnostic red/green: `test_real_chrome_diagnostic_reports_available_when_running_chrome_has_cdp` first failed with `needs_user_action != available`, then passed after the diagnosis semantics were updated.

Verification completed so far:
- `python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\tests_support\legacy_learning_agent_suite.py` passed.
- `python -m unittest learning_agent.tests_support.legacy_learning_agent_suite -k real_chrome` passed: 40 tests OK, skipped=1.
- `python -m unittest learning_agent.tests.test_compat_cleanup` passed: 4 tests OK.
- `python -m unittest discover learning_agent` passed: 367 tests OK, skipped=1.
- `python learning_agent\learning_agent.py mcp-doctor` now reports real Chrome profile status as `available` on this machine because 9222 is trusted Chrome CDP.

Visible terminal acceptance:
- Command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\real_chrome_natural_weather_travel.json`.
- Result: `learning_agent\acceptance_controller\runs\real_chrome_natural_weather_travel-20260530_144214\result.json`.
- Outcome: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, `marker_passed=true`, `permission_count_passed=true`.
- Evidence: final answer included `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK` and `real_chrome_connected=true`; debug checks confirmed `browser_connect_real_chrome 成功`, `browser_open 成功`, `browser_click 成功`, `browser_type 成功`, `browser_press_key 成功`, `browser_wait 成功`, `browser_screenshot 成功`, and `browser_snapshot 成功`.

## 2026-05-30 Stage 14 hard cleanup progress

Status: completed for code cleanup, documentation cleanup, automated tests, and visible-terminal acceptance.

What changed:
- Split the old large legacy test suite into real modules under `learning_agent/tests/`.
- Deleted the old test aggregator files and old acceptance forwarding entry.
- Removed same-block unreachable old implementations from `learning_agent/core/agent.py`.
- Updated `start_oauth_agent.ps1`, `start_codex_agent.ps1`, `README.md`, and `AGENT_ARCHITECTURE_INDEX.md` so user-visible docs and scripts point to the new architecture.
- Deleted source-tree historical artifact directories: `learning_agent/test/`, `learning_agent/debug_logs/`, `learning_agent/browser_artifacts/`, and `learning_agent/tests_support/`.
- Archived the fresh real-browser evidence from the acceptance run into `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/`.

Verification:
- `python -m compileall learning_agent` passed through bundled Codex Python.
- AST unreachable scan returned `NO_UNREACHABLE_SAME_BLOCK_CODE`.
- `python -m unittest learning_agent.tests.test_compat_cleanup` passed: 5 tests OK.
- `python -m unittest discover learning_agent` passed: 368 tests OK, skipped=1.
- Visible terminal acceptance passed at `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/result.json`: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.

## 2026-05-31 ClaudeCode gap baseline documentation

Status: completed for documentation only; no runtime code changed.

What changed:
- Added `agent_memory/claude_code_gap_baseline.md` as the agent-readable baseline for comparing learning_agent with `D:\ClaudeCode-main\ClaudeCode-main`.
- Added `learning_agent/claude_code_gap_baseline_backup_20260531.md` as a stable markdown backup for later alignment.
- The baseline records the current estimate: learning_agent is about 55%-65% aligned with reproducible core agent ideas, about 50%-60% aligned with the local long-running self-development goal, and about 25%-35% aligned with ClaudeCode product-level completeness.

Important next direction:
- The recommended next engineering phase is `Stage 15: Event Stream Runtime and Tool Executor v2`.
- Main focus should be streaming agent loop, richer tool protocol, concurrent read-only tool execution, transcript/session persistence, permission hooks, and durable task/subagent runtime.

Verification:
- Documentation-only change; no automated tests or visible terminal acceptance were required.

## 2026-05-31 Stage 15 event runtime written plan

Status: completed for planning only; no runtime code changed.

What changed:
- Added `agent_memory/stage15_event_runtime_plan.md` as the detailed 8-stage plan for adding event-stream runtime, richer tool protocol, Tool Executor v2, permission hooks, safe concurrency, and session resume/compact.
- Added `learning_agent/stage15_event_runtime_plan_backup_20260531.md` as a stable backup copy.

Plan summary:
- Stage 15A: event types and transcript foundation.
- Stage 15B: streaming model interface.
- Stage 15C: `LearningAgent.run_events()` with old `run()` compatibility.
- Stage 15D: Tool Protocol v3 metadata.
- Stage 15E: Tool Executor v2 and permission hooks.
- Stage 15F: safe concurrent read-only tool batching.
- Stage 15G: session save/resume and minimal compact.
- Stage 15H: integration validation, docs, and real visible terminal acceptance.

Verification:
- Documentation-only change; no automated tests or visible terminal acceptance were required.

## 2026-05-31 Stage 15A event runtime foundation

Status: completed for Stage 15A foundation in isolated worktree `stage15a-event-runtime`.

Baseline setup:
- Created initial git baseline commit on `main`: `3c657e5 chore: establish learning agent baseline`.
- Created isolated worktree: `.worktrees/stage15a-event-runtime`.
- Installed missing local Python test dependency with `python -m pip install playwright`.
- Installed Playwright Chromium with `python -m playwright install chromium`.
- Restored baseline test fixtures required by existing tests:
  - `.gitignore` now includes `learning_agent/browser_profiles.json`.
  - `.gitignore` now includes `learning_agent/browser_artifacts/real_chrome_audit.jsonl`.
  - Added `docs/superpowers/specs/claudecode_parity_checklist.md`.

TDD record:
- Red: `python -m unittest learning_agent.tests.test_runtime_events` failed with `ModuleNotFoundError: No module named 'learning_agent.core.events'`.
- Green: after adding `learning_agent/core/events.py` and `learning_agent/observability/transcript.py`, the same command passed with 2 tests OK.

Implemented:
- Added `learning_agent/core/events.py` with immutable `AgentEvent`, UTC timestamp helper, event factory, and JSONL serializer.
- Added `learning_agent/observability/transcript.py` with `TranscriptWriter` that appends events to `<base_dir>/<session_id>/events.jsonl`.
- Added `learning_agent/tests/test_runtime_events.py` covering stable JSON event serialization and session-directory JSONL transcript writes.
- Backed up new Stage 15A code into `learning_agent/test/stage15a_event_runtime_20260531/`.

Verification:
- Focused baseline repair tests passed: `python -m unittest learning_agent.tests.test_browser_harness.BrowserHarnessTests.test_gitignore_ignores_real_chrome_local_files learning_agent.tests.test_core_run_loop.CoreRunLoopTests.test_claudecode_parity_checklist_records_phase_7_status`.
- Full baseline unittest passed after dependency and fixture repair: `python -m unittest discover learning_agent` -> 368 tests OK, skipped=1.
- Focused Stage 15A test passed: `python -m unittest learning_agent.tests.test_runtime_events` -> 2 tests OK.
- Final Stage 15A compile verification passed: `python -m compileall learning_agent`.
- Final Stage 15A full unittest passed: `python -m unittest discover learning_agent` -> 370 tests OK, skipped=1.

Acceptance note:
- Real visible terminal acceptance was not run for Stage 15A because this stage only adds standalone event/transcript primitives and does not integrate runtime behavior into `LearningAgent.run()`.
- Future stages that change the interactive run loop, tool execution behavior, or user-visible agent behavior must run `start_oauth_agent.bat` visible-terminal acceptance before claiming development complete.

## 2026-05-31 Stage 15B-15G event runtime implementation progress

Status: code implementation and automated regression completed through Stage 15G in worktree `stage15a-event-runtime`.

Completed:
- Stage 15B streaming model compatibility in `models/base.py`.
- Stage 15C `run_events()` event stream and transcript integration in `core/agent.py`.
- Stage 15D Tool Protocol v3 metadata in `tools/types.py` and `tools/catalog.py`.
- Stage 15E Tool Executor v2, permission decision object, hook manager, and executor observations.
- Stage 15F safe concurrent read-only tool orchestration and integration into `run()` / `run_events()`.
- Stage 15G transcript reading, session summary store, and minimal compact helper.

Focused verification passed:
- `python -m unittest learning_agent.tests.test_models_streaming`
- `python -m unittest learning_agent.tests.test_runtime_events`
- `python -m unittest learning_agent.tests.test_tool_protocol`
- `python -m unittest learning_agent.tests.test_tool_executor_v2`
- `python -m unittest learning_agent.tests.test_tool_orchestrator`
- `python -m unittest learning_agent.tests.test_sessions`

Full regression evidence during implementation:
- Stage 15D full discovery: 377 tests OK, skipped=1.
- Stage 15E full discovery: 381 tests OK, skipped=1.
- Stage 15F full discovery: 384 tests OK, skipped=1.
- Stage 15G full discovery: 387 tests OK, skipped=1.

Remaining Stage 15H gate:
- Run fresh final `compileall`, full unittest discovery, `--help`, and `mcp-doctor`.
- Perform or request real visible terminal interaction through `learning_agent/start_oauth_agent.bat`.

## 2026-05-31 独立验收 verifier 与终端焦点门禁

Status: completed for code, docs, backup, automated regression, independent verifier replay, and real visible terminal smoke acceptance.

What changed:
- Added `learning_agent/acceptance/__init__.py` and `learning_agent/acceptance/verifier.py`.
- Added `learning_agent/tests/test_acceptance_verifier.py`.
- Updated `learning_agent/acceptance_controller/README.md` with offline replay verification usage.
- Hardened `learning_agent/acceptance_controller/controller.ps1` so it verifies the foreground window belongs to the target terminal before pasting prompts.
- Updated `learning_agent/tests/test_observability_acceptance.py` to guard the new foreground-window validation requirements.
- Backed up changed files under `learning_agent/test/acceptance_verifier_20260531/`.

Verification:
- Red test first: verifier import test failed before `learning_agent.acceptance` existed.
- Focused verifier tests: `python -m unittest learning_agent.tests.test_acceptance_verifier` passed with 3 tests OK.
- Controller protocol guard: `python -m unittest learning_agent.tests.test_observability_acceptance.ObservabilityAcceptanceTests.test_acceptance_controller_script_uses_generic_event_protocol` passed.
- PowerShell parse check for `controller.ps1` passed.
- Full regression: `python -m unittest discover learning_agent` passed with 390 tests OK, skipped=1.
- Compile check: `python -m compileall learning_agent` passed.
- MCP doctor: `python learning_agent\learning_agent.py mcp-doctor` exited 0 and reported 30 visible MCP tools.

Real visible terminal acceptance:
- Successful run: `learning_agent/acceptance_controller/runs/smoke-20260531_143929/result.json`.
- Result: `completed=true`, `prompt_received=true`, `final_printed=true`, `prompt_send_attempts=1`, final answer `ACCEPTANCE_HARNESS_OK`.
- Independent replay: `python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\smoke-20260531_143929 learning_agent\acceptance_controller\scenarios\smoke.json` returned `completed=true` and `assertion.passed=true`.

## 2026-05-31 long-task harness source review

Status: analysis only; no runtime code changed.

Findings:
- `learning_agent` currently has acceptance/controller harness pieces, `run_events()` transcript/session primitives, and in-process task/background/cron/monitor records.
- It does not yet have an independent durable long-task harness module with endpoint recovery, persistent task queue, staged acceptance gates, automatic continuation after failure, durable task state, or task-state visualization.
- ClaudeCode source review confirms a mature harness is spread across `QueryEngine.ts`, `utils/sessionStorage.ts`, `tasks/*`, `utils/messageQueueManager.ts`, `services/compact/*`, `services/tools/*`, and `components/tasks/*`.
- Recommended direction: add `learning_agent/harness/` as a dedicated package with durable run/task/stage schemas, append-only event log, persistent queue leases, checkpoint/resume, retry policy, verifier gates, and a status API/UI bridge.

## 2026-05-31 harness 对齐 ClaudeCode 方案确认

Status: planning only; no runtime code changed.

Confirmed from source:
- `learning_agent/harness/` already provides durable run/stage/attempt models, JSON/JSONL store, lease queue, runner, verifier, CLI, and `AgentStageExecutor`.
- `learning_agent/core/agent.py` already has `run_events()`, transcript writing, session summary, streaming model event consumption, and orchestrated tool execution.
- Runtime entrypoint tracing shows `learning_agent/learning_agent.py` delegates to `learning_agent/app/cli.py`, interactive mode delegates to `learning_agent/app/interactive.py`, and that path calls `agent.run(...)` without importing or invoking `learning_agent.harness`; therefore the real terminal main loop is not yet harness-driven.
- ClaudeCode's comparable long-task capability is distributed across `QueryEngine.ts`, `cli/print.ts`, `utils/messageQueueManager.ts`, `tasks/LocalAgentTask`, `tasks/RemoteAgentTask`, `tasks/LocalShellTask`, `utils/task/framework.ts`, `utils/task/TaskOutput.ts`, and `utils/sessionStorage.ts`.

Output:
- Created `agent_memory/harness_claudecode_alignment_plan_20260531.md`.
- The plan defines 12 stages: source baseline tests, runtime command queue, session runtime integration, interrupted-turn resume, durable task registry, task notification feedback, poller/watchdog, task output management, file locks/atomic writes, CLI/API status, verifier upgrades, and real visible terminal acceptance.

Next recommended action:
- Start with Stage 1 from `agent_memory/harness_claudecode_alignment_plan_20260531.md`: write failing alignment tests that prove which ClaudeCode-equivalent behaviors are still missing before implementation.

## 2026-05-31 source-only evidence correction

Status: planning evidence corrected; no runtime code changed.

Correction:
- README files must not be treated as key evidence for harness capability conclusions.
- Updated `agent_memory/harness_claudecode_alignment_plan_20260531.md` and this progress entry so the key conclusion uses source entrypoint tracing and symbol-reference scans instead of README statements.

## 2026-05-31 ClaudeCode-aligned harness runtime implementation

Status: implementation in progress; final real visible terminal acceptance still pending.

Implemented:
- Added `learning_agent/tests/test_harness_runtime_alignment.py` as the source-behavior alignment suite.
- Added `learning_agent/runtime/` with durable command queue, atomic/locked file helpers, session runtime, interrupted run resumer, durable task registry, task output store, and task poller.
- Updated `LearningAgent.run()` to keep the old text-returning API while internally using `run_events()` and mirroring the real run into durable harness state.
- Updated task and background command paths so task records/output persist under `memory/tasks` and can generate task notifications.
- Upgraded `HarnessStore`/`HarnessQueue` to use atomic writes, queue locks, and corrupt JSON quarantine.
- Upgraded `StageVerifier`/`HarnessStage` for marker, artifact, artifact content, JSON required fields, command exit codes, event sequence, and acceptance result checks.
- Upgraded harness CLI with `queue`, `tasks`, `events`, `resume`, and `poll`.

Verification so far:
- Red test confirmed first: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` failed because `learning_agent.runtime` did not exist.
- Green focused suite: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` -> 9 tests OK.
- Regression checks: `python -m unittest learning_agent.tests.test_core_run_loop` -> 40 tests OK; `python -m unittest learning_agent.tests.test_runtime_events` -> 4 tests OK; `python -m unittest learning_agent.tests.test_harness_long_task` -> 8 tests OK.
- Full regression: `python -m unittest discover learning_agent` -> 407 tests OK, skipped=1.
- Compile check: `python -m compileall learning_agent` -> exit 0.
- MCP doctor: `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools; Chrome real-profile status needs user action because Chrome was already running.
- Backup: copied changed runtime/core/harness/test/planning files to `learning_agent/test/harness_claudecode_alignment_20260531/`.

Remaining gate:
- Completed: real visible terminal acceptance through `learning_agent/start_oauth_agent.bat` passed for `learning_agent/acceptance_controller/runs/harness_runtime_alignment_status-20260531_165630/result.json`.
- Completed: independent replay passed with `python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\harness_runtime_alignment_status-20260531_165630 learning_agent\acceptance_controller\scenarios\harness_runtime_alignment_status.json`.
- Completed: latest durable run evidence in `learning_agent/memory/harness/runs/runtime_275e3c33ad6ec332.json` shows top-level `status=completed`, `stages[0].status=completed`, and `stages[0].acceptance.passed=true`.
- Completed: runtime command evidence in `learning_agent/memory/runtime/events.jsonl` shows the real prompt command was queued and completed.

Bug found and fixed during real acceptance:
- Real terminal acceptance initially exposed a false-complete state where the top-level run was completed but the copied stage stayed pending.
- Added regression checks in `learning_agent/tests/test_harness_runtime_alignment.py`.
- Fixed `learning_agent/runtime/session_runtime.py` to update `run.stages[0]` after `HarnessRun.create(...)`, because `HarnessRun.create()` deep-copies stages.
- Re-ran full verification after the fix: `python -m unittest discover learning_agent` -> 407 tests OK, skipped=1; `python -m compileall learning_agent` -> exit 0; `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools.

## 2026-05-31 Harness ClaudeCode alignment status correction

Status: previous completion claim downgraded to incomplete after source-only comparison.

Correction:
- The existing implementation created durable harness files, runtime queue files, task registry files, verifier upgrades, CLI status commands, and a real visible terminal smoke acceptance.
- That is not enough to claim ClaudeCode core harness alignment.
- The hard gate from `agent_memory/harness_claudecode_alignment_plan_20260531.md` requires the real main loop to be harness-driven and to consume queued prompt/task-notification/resume commands as model-visible context.
- Current source review shows `LearningAgent.run()` records a prompt into `RuntimeCommandQueue`, but then directly calls `agent.run_events(user_input, ...)` in `learning_agent/runtime/session_runtime.py`; it does not drain `RuntimeCommandQueue` into the model loop the way ClaudeCode drains queued commands in `query.ts`.
- Therefore the current alignment estimate must be treated as partial foundation only, not task completion.

Updated remaining hard gates:
- Add failing tests proving task notifications are automatically injected into the next real model turn without manual `task_output`.
- Add failing tests proving `resume_interrupted` commands are consumed by the real run loop, not merely enqueued.
- Refactor the real run path so queued runtime commands become model-visible context and are marked consumed only after they are attached to the turn.
- Add real visible terminal scenarios for task notification feedback and interrupted resume before any future completion claim.

## 2026-05-31 Harness alignment execution plan rewrite

Status: planning completed for corrected execution scope; implementation not started in this entry.

What changed:
- Added `agent_memory/harness_claudecode_alignment_execution_plan_20260531.md`.
- The new plan turns the previous loose "next step" into ten phases with hard gates.
- The plan centers on the missing core behavior: real `LearningAgent.run()` must drain durable runtime commands into model-visible context.
- The plan explicitly blocks completion claims until task notification feedback, interrupted resume consumption, durable task truth source, CLI/status visibility, automated regression, and real visible terminal acceptance all pass.

Critical correction:
- The old implementation remains a partial foundation.
- The next implementation pass must start with red tests for queue-drain-to-model behavior before modifying production code.

## 2026-05-31 Harness ClaudeCode alignment completion pass

Status: implementation and verification completed.

Implemented after corrected plan:
- Added red/green tests proving real queue drain, task notification feedback, interrupted resume consumption, and background command auto-notification.
- Fixed background shell completion so it updates durable task registry and enqueues notifications without `read_background_command`.
- Extended harness CLI/status output so run/stage/task/event/output/verifier evidence is visible.
- Fixed dynamic skill capability loading so reading `long_running_work/SKILL.md` exposes the real execution and long-running-work tools in the next model turn.
- Added visible terminal scenarios for task notification seed, notification feedback, resume, background shell watchdog, and background shell notification.

Verification:
- Red test confirmed before fix: `test_reading_long_running_skill_loads_background_command_tools` failed because `start_background_command` was not visible after reading `long_running_work/SKILL.md`.
- Focused green tests passed: `learning_agent.tests.test_mcp_registry`, `learning_agent.tests.test_tools_policy`, `learning_agent.tests.test_harness_runtime_alignment`, and the background auto-notify core-run-loop test.
- Full regression passed: `python -m unittest discover learning_agent` -> 414 tests OK, skipped=1.
- Compile check passed: `python -m compileall learning_agent` -> exit 0.
- MCP doctor passed: `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools; Chrome profile diagnostic still reports `needs_user_action` only because Chrome is currently running.

Real visible terminal acceptance:
- `harness_task_notification_seed-20260531_175937/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_task_notification-20260531_180044/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_runtime_resume-20260531_180202/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_background_shell_watchdog-20260531_180225/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_background_shell_notification-20260531_180359/result.json` -> `completed=true`, `assertion.passed=true`.
- Independent replay verifier also passed for all five run directories with `python -m learning_agent.acceptance.verifier <run_dir> <scenario.json>`.
- Final runtime queue check returned `NO_QUEUED_COMMANDS`.

Conclusion:
- The previous false-completion risk is resolved for the planned ClaudeCode core harness subset: real terminal prompt creates a durable run, queued notifications/resume commands enter the real model context, background tasks persist and notify, status/CLI surfaces evidence, and the feature passed real visible terminal acceptance.

## 2026-05-31 run() unreachable legacy cleanup

Status: source cleanup and verification completed.

What changed:
- Removed the unreachable legacy `LearningAgent.run()` loop after `return run_agent_with_harness_session(...)`.
- Kept `run_events()` unchanged as the real event-stream implementation.
- Added learning backup at `learning_agent/test/run_unreachable_cleanup_20260531/modified_snippets.md`.

Why:
- The leftover code could not execute, but it made the project look like it still had two competing main loops.
- Cleaning it makes the source match the intended architecture: `run()` is a thin compatibility wrapper and `run_events()` is the real event runtime.

Verification:
- `python -m py_compile learning_agent\core\agent.py` passed.
- `python -m unittest learning_agent.tests.test_harness_runtime_alignment learning_agent.tests.test_core_run_loop` passed: 55 tests OK.
- `python -m unittest discover learning_agent` passed: 414 tests OK, skipped=1.
- Real visible terminal smoke acceptance passed via `learning_agent/acceptance_controller/controller.ps1` with run directory `learning_agent/acceptance_controller/runs/smoke-20260531_182223`.
- Independent verifier passed for `smoke-20260531_182223`: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.

## 2026-05-31 Compact/Resume and UI/SDK status ecosystem plan

Status: planning completed; no production code changed for this plan.

Created:
- `agent_memory/compact_resume_status_ecosystem_alignment_plan_20260531.md`.
- `learning_agent/test/compact_resume_status_ecosystem_plan_20260531/plan.md`.

Scope:
- Align compact/resume complexity with ClaudeCode using append-only transcript, compact boundary, turn ledger, resume loader, consistency checks, and real main-loop integration.
- Align UI/SDK status ecosystem with ClaudeCode using terminal status renderer, status event protocol, status snapshot, CLI/API/SDK access, and model-callable status tools.
- Explicitly excludes remote tasks and streaming tool execution from this plan so the task stays focused.

## 2026-05-31 Compact/Resume and UI/SDK status ecosystem execution

Status: implementation completed and fully verified.

Implemented:
- Added transcript v2, turn ledger, compact boundary, resume loader, status event store, status snapshot, terminal renderer, SDK status helpers, HTTP `/status` and `/events`, harness CLI `snapshot`, interactive `/status`, and model-callable status tools.
- Integrated transcript v2, turn ledger, compact boundary, and status events into the real `LearningAgent.run_events()` path so they are no longer standalone side systems.
- Added tool schema/catalog/executor routes for `status_snapshot`, `task_status`, `session_list`, `session_resume`, `compact_status`, and `event_tail`.
- Added acceptance scenario `learning_agent/acceptance_controller/scenarios/compact_resume_status_ecosystem.json`.

Verification so far:
- Red HTTP test failed first with `/status` returning 404.
- Focused HTTP status/event test now passes.
- Red CLI module-entry test failed first because `python -m learning_agent.harness.cli snapshot` printed no status output.
- Full compact/resume/status ecosystem test file passes: 6 tests OK.
- Related regression passed: 258 tests OK.
- Full regression passed: 420 tests OK, skipped=1.
- Compile checks passed for changed modules and `python -m compileall learning_agent`.
- Real visible terminal acceptance passed for `compact_resume_status_ecosystem-20260531_185954`, and independent verifier passed.
- Real latest session evidence after visible terminal run: `memory/sessions/session_20260531_190000_e71f387a` contains `events.jsonl`, `summary.json`, `transcript_v2.jsonl` with 35 lines, and `turns.json`; `memory/status/events.jsonl` has 34 status events.
- After the CLI entrypoint fix, real visible terminal acceptance was rerun and passed for `compact_resume_status_ecosystem-20260531_190357`; independent verifier passed.
- Final latest session evidence after rerun: `memory/sessions/session_20260531_190403_57d4274a` contains `events.jsonl`, `summary.json`, `transcript_v2.jsonl` with 35 lines, and `turns.json`; `memory/status/events.jsonl` has 68 status events.

Backup:
- Refreshed under `learning_agent/test/compact_resume_status_ecosystem_20260531/`.

## 2026-05-31 Deep ClaudeCode compact/resume and status ecosystem alignment plan

Status: planning completed; waiting for user confirmation before implementation.

Why this plan exists:
- The previous compact/resume and status ecosystem task produced a working foundation, but it did not fully match ClaudeCode's deeper compact/resume complexity.
- Source comparison showed ClaudeCode has layered snip/microcompact/context-collapse/autocompact/reactive-compact behavior, richer resume cleanup, tombstones, tool summaries, session metadata restoration, and tighter SDK/UI event integration.

Created:
- `agent_memory/compact_resume_status_claudecode_deep_alignment_plan_20260531.md`
- `learning_agent/test/compact_resume_status_claudecode_deep_alignment_plan_20260531/plan.md`

Scope:
- Plan only. No production runtime code changed in this step.
- Implementation must wait for explicit user confirmation.
- Final implementation will require automated tests, compile checks, real visible `start_oauth_agent.bat` terminal acceptance, and independent verifier replay before any completion claim.

## 2026-05-31 Deep ClaudeCode compact/resume and status ecosystem alignment execution

Status: implementation completed and verified with automated tests plus real visible terminal acceptance.

Implemented:
- Status event protocol v2 now has stable `schema_version`, `session_id`, `run_id`, and `turn_id` fields, plus lifecycle event names for model, tools, compact, resume, verifier, and status.
- Multi-layer compact now records `tool_output_snip`, `microcompact`, `context_collapse`, `autocompact`, artifact paths, archived ranges, character estimates, and collapse commit ids.
- Reactive compact now detects prompt-too-long/media-too-large style failures and retries once with a tighter compacted context.
- ResumeLoader v2 now reports bad transcript lines, missing tool results, orphan tool results, interrupted turns, tombstones, warnings, and `resume_safe`/`resume_needs_review`.
- `LearningAgent.run_events()` now emits v2 status events for accepted turns, model responses, tool use/result, proactive compact, and reactive compact retry.
- HTTP bridge now exposes `/runs`, `/sessions`, `/resume?session_id=...`, `/health`, and type-filtered `/events`, alongside existing `/status`.
- SDK status now exposes `get_runs`, `get_sessions`, `get_health`, and `load_resume_report`, and event watch/list support event type filtering.
- Terminal UI now supports `/status`, `/events`, `/sessions`, `/resume <session_id>`, and `/compact`.
- Model-callable status tools now include `resume_report`, `run_status`, and `health_status` in addition to the previous status tools.
- Compatibility tests prove legacy status events and legacy compact boundaries remain readable by the new snapshot/resume path.

Automated verification:
- `python -m unittest learning_agent.tests.test_compact_deep_alignment learning_agent.tests.test_resume_deep_alignment learning_agent.tests.test_status_ecosystem_deep_alignment learning_agent.tests.test_compact_resume_status_ecosystem learning_agent.tests.test_runtime_events` passed: 16 tests OK.
- `python -m compileall -q learning_agent` passed.
- `python -m unittest discover learning_agent.tests` passed: 426 tests OK, skipped=1.

Backup:
- Source backup for this execution is being refreshed under `learning_agent/test/compact_resume_status_claudecode_deep_alignment_20260531/`.

Real visible terminal verification:
- Scenario file: `learning_agent/acceptance_controller/scenarios/compact_resume_status_deep_alignment.json`.
- Controller run directory: `learning_agent/acceptance_controller/runs/compact_resume_status_deep_alignment-20260531_200122`.
- Controller result: `ACCEPTANCE_CONTROLLER_COMPLETED=True`.
- Independent verifier result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Verifier confirmed final answer contained `COMPACT_RESUME_STATUS_DEEP_READY`, `tool_output_snip`, `microcompact`, `context_collapse`, `reactive_compact_retry`, `ResumeRepairReport`, `resume_needs_review`, `STATUS_SCHEMA_VERSION`, `get_health`, `load_resume_report`, `resume_report`, `run_status`, `health_status`, `/events`, `/sessions`, and `/compact`.
# 2026-05-31 真实浏览器能力对齐 ClaudeCode

## 当前任务

用户要求继续增强 `learning_agent` 的真实浏览器能力，重点补齐页面失败恢复、视觉定位、复杂网站流程、登录态安全、插件兼容、异常重试和任务回放，并且要求再次阅读 `D:\ClaudeCode-main\ClaudeCode-main` 源码作为对照证据。

## 已完成

1. 已确认本轮不是只做报告，而是要补代码能力。
2. 已初步读取 `learning_agent` 的浏览器 MCP、真实 Chrome、安全策略、harness、权限和测试文件。
3. 已初步读取 ClaudeCode 的 Chrome 扩展入口、Claude in Chrome skill、Chrome prompt hook、computer-use MCP、权限 UI、流式工具执行、消息队列、会话恢复和插件系统源码。
4. 已创建书面计划：`agent_memory/browser_claudecode_alignment_plan_20260531.md`。

## 下一步

1. 已写新增浏览器运行层测试：`learning_agent/tests/test_browser_runtime_alignment.py`。
2. 已实现动作轨迹、回放、重试、恢复、视觉定位、复杂流程、安全边界和插件兼容状态。
3. 已备份修改到 `learning_agent/test/browser_runtime_alignment_20260531/`。
4. 已通过 `python -m unittest discover learning_agent.tests`，结果为 433 个测试通过，1 个手动真实 Chrome 测试跳过。
5. 第一次真实终端验收发现 `browser_flow_run` 的 array schema 缺少 items，导致 OpenAI response_format invalid_json_schema；已补 schema 并加测试。
6. 第二次真实终端验收通过：`learning_agent/acceptance_controller/runs/browser_runtime_alignment-20260531_204032/result.json` 中 `completed=true`，`assertion.passed=true`。

## 本次新增能力文件

1. `learning_agent/browser_automation_mcp_server.py`
2. `learning_agent/tests/test_browser_runtime_alignment.py`
3. `learning_agent/skills/browser_automation/SKILL.md`
4. `learning_agent/skills/real_chrome/SKILL.md`
5. `agent_memory/browser_claudecode_alignment_report_20260531.md`
6. `learning_agent/acceptance_controller/scenarios/browser_runtime_alignment.json`

# 2026-05-31 真实可见浏览器验收补齐

## 当前任务

用户要求所有真实浏览器新增能力必须经过肉眼可见的真实浏览器测试验收通过，才能算完成。

## 当前判断

上一轮已补核心浏览器工具能力，并通过真实终端状态验收；但独立 Chromium 默认还是 headless，缺少明确的“可见浏览器启动 + 可见浏览器完整链路验收”。

## 本轮计划

1. 新增 `browser_launch_visible` 工具。
2. 让 `ensure_browser()` 支持 `headless=false`。
3. 让状态工具输出 `visible_browser` 和 `headless` 状态。
4. 新增真实可见浏览器验收场景。
5. 跑自动化测试、完整测试和真实可见终端验收。

## 本轮完成

1. 已新增 `browser_launch_visible`，需要 `confirm_visible_browser=true` 才会启动可见独立 Chromium。
2. 已让 `browser_open`、`browser_snapshot`、`browser_visual_locate`、`browser_flow_run`、`browser_recover_page`、`browser_replay`、`browser_plugin_status` 在可见浏览器 workflow 中连贯可用。
3. 已修复 Windows 状态文件 `os.replace` 短暂拒绝访问问题：`atomic_write_text()` 现在会短退避重试并清理失败临时文件。
4. 已修复 `browser_visual_locate`：现在能定位不可点击的标题/正文文本块，并支持 `selector="h1"` 这类简写。
5. 已修复 `browser_flow_run`：阶段里的空 `browser_wait` 会自动补 `milliseconds=250`，避免模型小参数遗漏导致流程失败。
6. 已更新可见浏览器验收场景：`learning_agent/acceptance_controller/scenarios/browser_visible_runtime_acceptance.json`。

## 验证结果

1. `python -m unittest learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_intent learning_agent.tests.test_browser_harness learning_agent.tests.test_runtime_files` 通过：55 个测试 OK，1 个跳过。
2. `python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\runtime\files.py learning_agent\browser\intent.py learning_agent\core\agent.py learning_agent\tests\test_runtime_files.py learning_agent\tests\test_browser_runtime_alignment.py` 通过。
3. `python -m unittest discover learning_agent.tests` 通过：439 个测试 OK，1 个跳过。
4. 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260531_211805/result.json` 中 `completed=true`、`assertion.passed=true`。
5. 真实验收日志确认：`browser_launch_visible 成功`、`visible_browser=true`、`headless=false`、`browser_open`、`browser_snapshot`、`browser_visual_locate 成功`、`browser_flow_run 完成`、`browser_recover_page 成功`、`browser_replay 计划`、`browser_plugin_status compatible=true`。
6. 独立验收复核通过：`python -m learning_agent.acceptance.verifier ...browser_visible_runtime_acceptance-20260531_211805 ...browser_visible_runtime_acceptance.json` 输出 `completed=true`、`assertion.passed=true`。

# 2026-05-31 自然实时查询可见浏览器路由修复

## 当前任务

用户指出本地桌面没有看到真实浏览器，要求重新测试精准 prompt：`帮我查询3天后武汉的天气，并帮我做一下旅游攻略。`

## 已确认

1. 精准 prompt 场景已经跑过一次：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_212955/result.json`。
2. 该 run 的最终回答已打印，但工具调用只有 `browser_search.web_search` 和 `browser_search.fetch_url`。
3. 没有看到 `browser_launch_visible`、`browser_open`、`browser_snapshot`，所以真实可见浏览器验收不成立。
4. 代码证据显示当前 `detect_real_browser_information_task()` 要求先命中“真实浏览器”等关键词，普通天气/攻略查询不会进入浏览器 harness。

## 本轮计划文件

已创建：`agent_memory/visible_browser_natural_query_route_plan_20260531.md`。

## 下一步

1. 写红灯测试锁定普通武汉天气/攻略 prompt 必须进入可见浏览器路由。
2. 实现自然实时查询意图、可见浏览器 harness 和首轮 `browser_launch_visible` 工具暴露。
3. 跑自动化测试和真实可见终端验收。

## 本轮完成

1. 已新增普通自然实时查询识别函数：`detect_visible_browser_information_task()`。
2. 已新增 `Visible Browser Task Harness`，精准 prompt 会要求可见独立 Chromium，而不是后台 `web_search/fetch_url`。
3. `LearningAgent.run_events()` 已在首轮工具池构造前预加载可见浏览器公开查询所需工具。
4. 已新增普通可见浏览器公开查询自动授权白名单，范围只包含独立 Chromium 的公开网页动作；`browser_evaluate`、`file://`、缺确认参数启动仍不自动放行。
5. 自动化测试通过：`python -m unittest discover learning_agent.tests`，444 tests OK，skipped=1。
6. 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_215353/result.json`。
7. 独立 verifier 通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
8. 最终回答包含 `browser_launch_visible`、`visible_browser=true`、`headless=false`，并给出武汉天气和旅游攻略。
## 2026-05-31 危险调试权限 + browser_connect_real_chrome 验收执行记录

状态：已完成。

已完成：
- 已确认权限拦截点位于 `learning_agent/browser/permissions.py`、`learning_agent/core/agent.py` 和 `learning_agent/start_oauth_agent.ps1`。
- 已新增 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS` 开关，危险模式下终端权限和 MCP 工具权限会自动写入 `permission_auto_approved` 并放行。
- 已让 `start_oauth_agent.ps1` 普通启动默认设置危险调试权限，并在终端打印清楚提示。
- 已新增单元测试覆盖任意 MCP 工具危险自动授权、终端权限不调用 input、启动脚本默认设置危险开关。
- 已新增真实可见终端验收场景 `real_chrome_dangerous_skip_connect_public_page.json`，要求调用 `browser_connect_real_chrome(confirm_real_profile=true)` 并打开 `https://example.com`。
- 首次真实可见终端验收已证明权限层通过，但 `browser_connect_real_chrome` 被工具自身的“日常 Chrome 正在运行且无 CDP”安全检查阻断。
- 已补充危险调试模式下的隔离 debug profile 兜底：不关闭用户 Chrome，不读取登录态，而是用真实 Google Chrome + `browser_artifacts/real_chrome_debug_profile` 完成可见浏览器连接测试。
- 已新增单元测试 `test_browser_connect_real_chrome_uses_debug_profile_fallback_in_dangerous_mode` 锁定上述兜底。

最终验收：
- 已更新学习备份到 `learning_agent/test/dangerous_skip_permissions_real_chrome_20260531/`。
- 已重新通过 `start_oauth_agent.bat` 的真实可见终端执行 controller 场景，确认 `browser_connect_real_chrome` 真实可见验收通过。
- 验收 run：`learning_agent/acceptance_controller/runs/real_chrome_dangerous_skip_connect_public_page-20260531_223149`。
- `result.json` 中 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`、`permission_auto_approved=true`。
- 最终截图 `03_final.png` 可见真实 Google Chrome 打开 `https://example.com`，并且终端输出包含 `REAL_CHROME_DANGEROUS_SKIP_CONNECT_OK`、`real_chrome_connected=true`、`real_chrome_profile_scope=debug_profile_fallback`。

当前验证：
- `python -m unittest learning_agent.tests.test_browser_harness learning_agent.tests.test_browser_intent learning_agent.tests.test_mcp_registry`：160 tests OK，skipped=1。
- `python -m unittest discover learning_agent.tests`：448 tests OK，skipped=1。
- `python -m compileall learning_agent`：通过。

## 2026-06-01 雷神 H5 登录真实 Chrome 拟人验收完成记录

任务目标：
- 用户要求由 `learning_agent` 通过 `browser_connect_real_chrome` 控制真实 Google Chrome，打开指定 H5 页面，输入已提供账号和密码，提交登录，并把登录后页面可见内容反馈给用户。
- 因为该任务涉及真实登录态和敏感输入，本轮实现和验收必须使用 `browser_type_secret` 从环境变量读取密钥，并在事件、日志、最终回答中脱敏。

本轮修复：
- 已补齐真实 Chrome 登录流的密钥输入能力：`browser_type_secret` 只从环境变量取值，不把明文密码写进 agent 最终回答或调试日志。
- 已让 `browser_flow_run` 支持从 workspace 内的 Markdown/JSON 阶段文件读取流程，避免长流程参数被模型写乱。
- 已修复 OAuth/API 模型结构化输出偶发损坏的问题：当模型返回不可解析 JSON 时，`CodexCliChatModel` 和 `CodexOAuthChatModel` 会追加一次“只修复 JSON”的重试提示，并只在修复后结构合法时继续执行工具。

自动化验证：
- `python -m unittest learning_agent.tests.test_models_codex_oauth`：47 tests OK。
- `python -m unittest learning_agent.tests.test_browser_runtime_alignment`：16 tests OK。
- `python -m py_compile learning_agent\models\adapters.py learning_agent\tests\test_models_codex_oauth.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_browser_runtime_alignment.py`：通过。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端执行 controller 场景。
- 验收 run：`learning_agent/acceptance_controller/runs/real_chrome_leishen_login_content-20260601_075721`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已通过：`python -m learning_agent.acceptance.verifier ...real_chrome_leishen_login_content-20260601_075721 ...real_chrome_leishen_login_content.json` 输出 `completed=true`、`assertion.passed=true`。
- 调试日志确认真实工具链：`browser_connect_real_chrome 成功`、`real_chrome_connected=true`、`browser_open 成功`、`browser_flow_run 完成`、`browser_type_secret 成功`、`browser_click 成功`、`browser_wait 成功`、`browser_screenshot 成功`、`browser_snapshot 成功`。
- 页面可见结果：登录成功，页面标题为 `皇上快点`，可见内容包含 `欢迎回来`、用户信息（已脱敏）和 `修改密码`。
- 页面截图证据：`learning_agent/browser_artifacts/leishen_after_account_login_v8.png`。

## 2026-06-01 Browser Runtime ClaudeCode 对齐升级计划

当前任务：
- 用户要求结合并参考 ClaudeCode 源码，先制定 `learning_agent` 真实浏览器能力的升级计划，不直接改运行时代码。

已完成：
- 已重新按源码证据归纳 ClaudeCode 可确认能力：`claude-in-chrome` MCP/Chrome 扩展桥接、skill 激活、tabs context、站点级权限、MCP progress、流式工具执行、并发安全、Chrome 状态 UI。
- 已把 learning_agent 当前能力边界写入计划：已有真实 Chrome/可见 Chromium/浏览器 MCP 工具/回放雏形/acceptance verifier，但缺少独立 Browser Runtime、状态机、locator、恢复策略、浏览器专用状态生态和 verifier 2.0 闭环。
- 已创建正式计划：`agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`。
- 已创建实施计划副本：`docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`。
- 已创建学习备份：`learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`。

下一步：
- 等用户确认后，从阶段 1 开始执行：先做 Browser Runtime 协议层和 Browser Runtime Store，不先堆更多零散浏览器工具。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 1-2

状态：部分完成，已完成底层协议层、持久化 store、浏览器 MCP server 工具执行入口接入、agent/status 状态镜像；整套 12 阶段任务尚未完成，真实可见终端验收尚未执行。

已完成：
- Stage 1：新增 `learning_agent/browser/runtime_models.py`，定义 `BrowserRun`、`BrowserSession`、`BrowserTab`、`BrowserAction`、`BrowserObservation`、`BrowserLocator`、`BrowserRecoveryAttempt`、`BrowserAssertion`、`BrowserCapabilityReport`。
- Stage 1：新增 `learning_agent/tests/test_browser_runtime_models.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.runtime_models'`，再实现协议层并通过测试。
- Stage 2：新增 `learning_agent/browser/runtime_events.py`，集中定义 `browser_run_created`、`browser_action_started`、`browser_action_completed`、`browser_observation_recorded` 等事件名。
- Stage 2：新增 `learning_agent/browser/runtime_store.py`，把 browser run/action/observation/event 持久化到调用方指定目录下的 `runs/`、`actions/`、`observations/`、`events/`。
- Stage 2：新增 `learning_agent/tests/test_browser_runtime_store.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.runtime_store'`，再实现 store 并通过测试。
- Stage 2：新增红灯测试锁定真实 `BrowserAutomationServer.call()` 必须自动创建 durable browser run 和 `browser_action_started/completed` 事件；红灯为 run 列表为空。
- Stage 2：已修改 `learning_agent/browser_automation_mcp_server.py` 的统一 `call()` 包装层，顶层工具调用会创建 browser run，嵌套 flow 阶段共享同一个 run，每个工具动作写 started/completed/failed。
- Stage 2：新增红灯测试锁定 `LearningAgent._execute_tool()` 调用 browser_automation MCP 工具后必须把 latest browser run 镜像到统一 status 事件；红灯为 `browser_runtime_event` 缺失。
- Stage 2：已修改 `learning_agent/core/agent.py`，浏览器 MCP 工具完成或失败后会扫描 `<workspace>/learning_agent/memory/browser_runtime/` 最新 run，写入 observation 和 `StatusEventStore(...).append("browser_runtime_event", ...)`。
- Stage 2：已修改 `learning_agent/runtime/status_schema.py`，把 `browser_runtime_event` 加入 v2 状态事件类型。
- 已把 Stage 1 代码备份到 `learning_agent/test/browser_runtime_claudecode_stage1_20260601/`。
- 已把 Stage 2 代码和 server 接入修改备份到 `learning_agent/test/browser_runtime_claudecode_stage2_20260601/`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：67 tests OK。
- `python -m py_compile learning_agent\core\agent.py learning_agent\runtime\status_schema.py learning_agent\browser_automation_mcp_server.py learning_agent\browser\runtime_models.py learning_agent\browser\runtime_events.py learning_agent\browser\runtime_store.py learning_agent\tests\test_browser_runtime_store.py`：通过。

未完成：
- browser runtime 事件已经镜像到统一 status event，但还没有在 status snapshot/CLI/API 中形成专门的 browser section。
- browser run id 还没有进入每一轮模型上下文的专用摘要，也没有和 verifier 2.0/acceptance scenario 完整闭环。
- 尚未完成 Stage 3-12。
- 尚未执行 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收；因此不能声明整套浏览器 runtime 对齐开发完成。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 3

状态：Stage 3 已完成自动化测试和真实可见终端交互验收；整套 12 阶段任务仍未完成。

已完成：
- Stage 3：新增 `learning_agent/browser/tab_registry.py`，提供稳定 tab id、page_key 映射、active tab 切换、关闭清理和健康报告。
- Stage 3：新增 `learning_agent/browser/session_manager.py`，统一表示 `independent_chromium`、`visible_chromium`、`real_chrome_cdp` 三类浏览器 session。
- Stage 3：新增 `learning_agent/tests/test_browser_session_manager.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.session_manager'` 和 `BrowserAutomationServer` 缺少 `session_manager`，再实现通过。
- Stage 3：修改 `learning_agent/browser_automation_mcp_server.py`，在独立 Chromium 启动、可见 Chromium 启动、真实 Chrome CDP 连接、页面登记、页面关闭、标签切换、`browser_plugin_status`、`browser_profile_status` 中接入 `BrowserSessionManager`。
- Stage 3：真实 Chrome profile 状态只记录 `Default (scope)` 这类脱敏摘要，不保存完整 `User Data` 路径。
- Stage 3：已把本阶段代码备份到 `learning_agent/test/browser_runtime_claudecode_stage3_20260601/`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_session_manager`：4 tests OK。
- `python -m unittest learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：68 tests OK。
- `python -m unittest learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_intent learning_agent.tests.test_browser_harness learning_agent.tests.test_compact_resume_status_ecosystem learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：126 tests OK，skipped=1。
- `python -m py_compile learning_agent\browser\tab_registry.py learning_agent\browser\session_manager.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_browser_session_manager.py`：通过。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端执行 controller 场景。
- 验收 run：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_105840`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已通过：`python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_visible_runtime_acceptance-20260601_105840 .\learning_agent\acceptance_controller\scenarios\browser_visible_runtime_acceptance.json`。
- 调试日志确认本次 Stage 3 新字段：`session_mode=visible_chromium`、`connected=true`、`visible=true`、`tab_count=1`、`active_tab_id=browser_session_1_fa131c86-tab-1`。

未完成：
- Stage 4-12 仍未完成，下一步应进入 Observation Engine / Locator Engine，而不是继续在 server 单体里堆零散工具。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 4-12

状态：Stage 4-11 已完成代码实现、真实 server 接入、状态生态接入和全量自动化测试；Stage 12 仍剩真实可见终端交互验收。

已完成：
- Stage 4：新增 `learning_agent/browser/observation.py` 和 `learning_agent/browser/screenshot_index.py`，把页面文本、元素、console、network、截图路径统一成 `BrowserObservation`，长页面正文会落盘到 artifact。
- Stage 4：修改 `BrowserObservation` 协议，新增 `artifact_paths` 字段；修改 `browser_snapshot` 和 `browser_screenshot`，真实工具成功后会保存 observation 并把 action 关联到 observation_id。
- Stage 5：新增 `learning_agent/browser/locator.py`，支持 selector/text/role/label/placeholder/element_id/coordinate/visual_query 候选评分和解释。
- Stage 6：新增 `learning_agent/browser/action_policy.py` 和 `learning_agent/browser/action_executor.py`，区分只读并发工具和写操作串行工具，并提供 started/progress/completed/failed/interrupted 生命周期事件。
- Stage 7：新增 `learning_agent/browser/recovery.py`，把 page_closed、context_closed、navigation_timeout、network_idle_timeout、locator_not_found、click_intercepted、stale_element、download_failed、chrome_disconnected、permission_denied 归一化，并提供重试预算。
- Stage 8：新增 `learning_agent/browser/flow_schema.py` 和 `learning_agent/browser/flow_runtime.py`；`browser_flow_run` 现在通过 checkpoint runtime 执行阶段，已完成阶段可跳过，不再只能从头重跑。
- Stage 9：新增 `learning_agent/browser/secret_vault.py` 和 `learning_agent/browser/site_permissions.py`，提供 secret ref、输出脱敏和 origin 授权模型。
- Stage 10：新增 `learning_agent/browser/assertions.py` 和 `learning_agent/browser/replay.py`；`acceptance/verifier.py` 升级到 schema_version=2，可读取 `browser_observation_path` 并执行 `browser_assertions`。
- Stage 11：`build_status_snapshot()` 新增 `browser` 区块，包含 browser runs/actions/observations/events/counts/store/latest_run。
- Stage 11：`learning_agent/sdk/status.py` 新增 `get_browser_runs()` 和 `get_browser_events()`。
- Stage 11：HTTP bridge 新增 `GET /browser/runs`、`GET /browser/events`、`GET /v1/browser/runs`、`GET /v1/browser/events`。
- Stage 11：harness CLI 新增 `browser-runs` 和 `browser-events` 子命令。
- Stage 11：终端状态渲染器新增 `Browser Runtime` 区块，显示 browser run/action/observation/event 计数、latest_run 和 store。
- 已把本阶段所有新增/修改代码备份到 `learning_agent/test/browser_runtime_stage4_12_20260601/`。

自动化验证：
- 先观察红灯：新增 Stage 4-11 测试首次运行出现 `ModuleNotFoundError` 和 `get_browser_events` 导入失败。
- `python -m unittest learning_agent.tests.test_browser_observation learning_agent.tests.test_browser_locator learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_recovery learning_agent.tests.test_browser_flow_runtime learning_agent.tests.test_browser_secret_permissions learning_agent.tests.test_browser_replay_assertions learning_agent.tests.test_browser_status_ecosystem`：19 tests OK。
- `python -m py_compile` 覆盖 browser runtime 新模块、`browser_automation_mcp_server.py`、`status_snapshot.py`、SDK、HTTP bridge、CLI、verifier：通过。
- `python -m unittest discover -s learning_agent\tests -p "test_browser*.py"`：95 tests OK，skipped=1。
- `python -m unittest discover -s learning_agent\tests -p "test_*status*.py"`：10 tests OK。
- `python -m unittest discover -s learning_agent\tests -p "test_*acceptance*.py"`：12 tests OK。
- `python -m unittest discover -s learning_agent\tests`：483 tests OK，skipped=1。

未完成：
- 仍需执行 `learning_agent/start_oauth_agent.bat` 的真实可见终端交互验收，并用独立 verifier 复验 run；未完成前不能声明整套 Stage 4-12 开发完成。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 12 验收完成

状态：Stage 4-12 已完成代码实现、自动化测试、学习备份、真实可见终端交互验收和独立 verifier 复验。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 启动真实可见终端窗口，并由 controller 输入验收 prompt。
- 验收 run：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_114746`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`final_printed=true`、`permission_sent_count=0`。
- debug log 确认工具链包含 `browser_launch_visible`、`browser_open`、`browser_snapshot`、`browser_screenshot`、`browser_flow_run`、`browser_plugin_status`。
- debug log 确认关键状态包含 `visible_browser=true`、`headless=false`、`observation_id=`、`flow_checkpoint`、`status_browser_runtime`、`browser_runtime_store=`、`compatible=true`。

独立验收复核：
- 已运行 `python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_visible_runtime_acceptance-20260601_114746 .\learning_agent\acceptance_controller\scenarios\browser_visible_runtime_acceptance.json`。
- verifier 输出 `schema_version=2`、`completed=true`，并且 `assertion.passed=true`。
- verifier artifact 检查确认 `result_json`、`event_log`、`debug_log`、`startup_screenshot`、`prompt_screenshot`、`final_screenshot` 都存在。

最终自动化测试证据：
- `python -m unittest discover -s learning_agent\tests` 通过：483 tests OK，skipped=1。
- Stage 4-12 学习备份目录：`learning_agent/test/browser_runtime_stage4_12_20260601/`。

## 2026-06-01 BrowserActionExecutor 接管 server 生命周期

状态：代码实现、自动化测试、真实可见终端验收和独立 verifier 复验已完成。

本次目标：
- 延续 Stage 4-12 后的下一步，把 `browser_automation_mcp_server.py` 里旧的 action started/completed/failed 手写逻辑收敛到 `BrowserActionExecutor`。
- 保留原有稳定 action id 规则：`<browser_run_id>-action-<序号>`，避免 run/action/observation 证据断链。

已完成：
- 新增红灯测试 `test_executor_accepts_stable_action_id_from_runtime_store`，首次运行报错：`BrowserActionExecutor.begin_action() got an unexpected keyword argument 'action_id'`。
- 新增红灯测试 `test_browser_server_delegates_action_lifecycle_to_executor`，首次运行失败：spy executor 没有收到 `begin` 和 `complete` 调用。
- 修改 `learning_agent/browser/action_executor.py`，让 `begin_action(...)` 支持调用方传入稳定 `action_id`。
- 修改 `learning_agent/browser_automation_mcp_server.py`，新增 `self.browser_action_executor = BrowserActionExecutor(store=self.browser_runtime_store)`。
- 修改 `_start_browser_runtime_action()`，委托 `browser_action_executor.begin_action(...)` 创建并保存 started action。
- 修改 `_complete_browser_runtime_action()`，委托 `browser_action_executor.complete_action(...)` 完成 action 并关联 observation。
- 修改 `_fail_browser_runtime_action()`，委托 `browser_action_executor.fail_action(...)` 写入标准失败分类和失败事件。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_action_executor` 通过：5 tests OK。
- `python -m unittest learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_action_executor` 通过：25 tests OK。
- `python -m py_compile .\learning_agent\browser\action_executor.py .\learning_agent\browser_automation_mcp_server.py .\learning_agent\tests\test_browser_action_executor.py` 通过。
- `python -m unittest discover -s learning_agent\tests` 通过：485 tests OK，skipped=1。

真实可见终端验收：
- 先使用旧的 `browser_visible_runtime_acceptance.json` 重跑两次，浏览器工具链已执行到 visible/open/snapshot/screenshot/flow_run，但模型提前最终回答，未调用 `browser_plugin_status`，因此旧大场景失败；该失败不是本次 executor 代码异常。
- 为本次改动新增聚焦场景 `learning_agent/acceptance_controller/scenarios/browser_action_executor_delegation_acceptance.json`。
- 聚焦场景通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端窗口运行，run 为 `learning_agent/acceptance_controller/runs/browser_action_executor_delegation_acceptance-20260601_122229`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 真实终端里的 agent 调用 bash 检查 browser runtime event log，输出 `ACTION_EXECUTOR_STORE_OK started=True completed=True`，证明 action started/completed 已落入 durable browser runtime。
- 独立 verifier 已通过：`schema_version=2`、`completed=true`、`assertion.passed=true`。

备份：
- 本轮学习备份目录：`learning_agent/test/browser_action_executor_delegation_20260601/`。

## 2026-06-01 ClaudeCode 真实浏览器源码对比分析

状态：只读源码分析进行中，未修改运行代码。

本次目标：
- 阅读 ClaudeCode 中 Claude in Chrome / native host / MCP / skill / UI 接入源码。
- 对照 learning_agent 当前 `browser_automation`、真实 Chrome CDP、可见浏览器、运行时持久化和回放实现。

已确认的关键事实：
- ClaudeCode 当前源码树引用 `@ant/claude-for-chrome-mcp`，但该包源码不在本地 `node_modules` 中，因此只能确认 CLI/MCP/native host/skill/UI 接入层源码，不能把隐藏包内部实现当作已读证据。
- learning_agent 已有真实 Chrome/CDP 连接、可见 Chromium、页面恢复、视觉定位、复杂流程、任务回放、站点授权、动作执行器、事件持久化和状态输出。

## 2026-06-01 双轨真实浏览器架构蓝图

状态：书面蓝图已完成，未进入代码实现。

本次目标：
- 防止后续长任务跑偏，先把 learning_agent 双轨真实浏览器改造拆成可验收阶段。
- 固定核心原则：底层支持 `visible_chromium`、`real_chrome_cdp`、`chrome_extension`，但模型表面只暴露统一 `browser_*` 工具，由 `BrowserProviderRouter` 在代码层选择 provider。

已完成：
- 新增蓝图文档：`docs/superpowers/specs/2026-06-01-browser-dual-track-architecture-blueprint.md`。
- 新增摘要备份：`learning_agent/test/browser_dual_track_architecture_blueprint_20260601/blueprint.md`。
- 蓝图明确 12 个实施阶段、路由规则、成功标准、停止条件、fallback 策略、真实可见终端总验收门禁。

重要约束：
- 不让模型同时看到插件版和 CDP 版重复工具。
- 当前 Chrome、登录态、OAuth、现有标签页优先走 Chrome 插件 provider。
- 公开网页、本地开发、普通可见验收优先走可见 Chromium / Playwright。
- 插件不可用时不能静默降级到 CDP，除非用户或策略明确允许。

## 2026-06-01 双轨真实浏览器实施计划

状态：实施计划已完成，尚未进入 Stage 1 代码实现。

已完成：
- 新增主实施计划：`docs/superpowers/plans/2026-06-01-browser-dual-track-architecture-implementation.md`。
- 新增计划摘要备份：`learning_agent/test/browser_dual_track_architecture_blueprint_20260601/implementation_plan_summary.md`。
- 主计划明确 Stage 1 只做 Provider Protocol、Router、Registry、provider decision 事件和测试，不改现有真实浏览器执行路径。
- 主计划明确 Stage 2 到 Stage 12 必须逐阶段单独生成计划，不允许直接跳到 Chrome 插件/native host 大改。

自检结果：
- 占位词检查通过：未发现 `TODO`、`TBD`、`待定`、`占位`。
- Provider 防误选检查通过：计划中没有设计 `chrome_extension_open`、`cdp_real_chrome_open`、`visible_chromium_open` 这类会让模型直接选轨道的重复工具名。

下一步建议：
- 等用户确认后，按主实施计划进入 Stage 1：先写红灯测试 `learning_agent/tests/test_browser_provider_router.py`，再实现 `learning_agent/browser/providers/` 协议和 Router。

## 2026-06-01 双轨真实浏览器 Stage 1 执行

状态：代码实现和自动化测试已完成；真实可见终端验收尚未完成，因此不能声明 Stage 1 开发完成。

本阶段范围：
- 新增 Provider Protocol、Router、Registry 和 provider decision 事件。
- 不接管现有 `browser_automation_mcp_server.py` 执行路径。
- 不新增插件版和 CDP 版重复工具名，继续保持模型表面单轨。

已完成：
- 新增 `learning_agent/tests/test_browser_provider_router.py`。
- 新增 `learning_agent/browser/providers/__init__.py`。
- 新增 `learning_agent/browser/providers/protocol.py`。
- 新增 `learning_agent/browser/providers/router.py`。
- 新增 `learning_agent/browser/providers/registry.py`。
- 新增 `learning_agent/browser/providers/provider_events.py`。
- 修改 `learning_agent/browser/runtime_events.py`，加入 `BROWSER_PROVIDER_DECISION`。
- 修改 `learning_agent/browser/__init__.py`，导出 provider 相关公开 API。
- 新增备份文件 `learning_agent/test/browser_dual_track_stage1_20260601/modified_snippets.md`。

红灯测试：
- `python -m unittest learning_agent.tests.test_browser_provider_router` 首次运行失败，错误为 `ModuleNotFoundError: No module named 'learning_agent.browser.providers'` 和缺少 `BROWSER_PROVIDER_DECISION`，符合预期。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_provider_router` 通过：7 tests OK。
- `python -m py_compile .\learning_agent\browser\providers\__init__.py .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\router.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\provider_events.py .\learning_agent\browser\runtime_events.py .\learning_agent\browser\__init__.py .\learning_agent\tests\test_browser_provider_router.py` 通过：退出码 0。
- `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router` 通过：28 tests OK。
- `python -m unittest discover -s learning_agent\tests` 通过：497 tests OK，skipped=1。

子代理审查：
- 已派发 Stage 1 规格符合性只读审查。
- 已派发 Stage 1 代码质量只读审查。
- 截至本记录，子代理尚未返回最终审查结果。

真实可见终端验收：
- 尚未完成。
- 按 AGENTS 规则，真实可见终端交互验收未完成，不能声明开发完成。

## 2026-06-01 双轨真实浏览器 Stage 1 评审修复复测

状态：代码质量评审指出的问题已修复并完成 fresh 自动化复测；真实可见终端交互验收仍未完成，因此仍不能声明 Stage 1 开发完成。

本轮修复点：
- `BrowserProviderRouter` 复用 `learning_agent/browser/intent.py` 里的真实浏览器关键词，补齐“当前浏览器、真实浏览器、真实 Chrome、current browser、login state”等场景，避免 router 和 intent 关键词漂移。
- `BrowserProviderDecision` 新增稳定 `schema_version=1`、`reason_code` 和 JSON 安全 `metadata`，避免 event log 被不可序列化对象破坏。
- 插件不可用时，如果没有明确允许 CDP fallback，继续返回 `unavailable` 并要求用户确认；如果明确允许 fallback，则记录 `fallback_from=chrome_extension`，不再把 fallback_provider 伪装成同一个已选 provider。
- `_available_or_unavailable()` 在 provider 不可用时不再把失败 provider 写成 fallback，避免状态语义误导后续 agent。
- `provider_events.build_provider_decision_event()` 和 `BrowserProviderRegistry.set_health()/all_health()` 已补测试覆盖。

fresh 自动化验证：
- `python -m unittest learning_agent.tests.test_browser_provider_router` 通过：12 tests OK。
- `python -m py_compile .\learning_agent\browser\providers\__init__.py .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\router.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\provider_events.py .\learning_agent\browser\runtime_events.py .\learning_agent\browser\__init__.py .\learning_agent\tests\test_browser_provider_router.py` 通过：退出码 0。
- `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router` 通过：33 tests OK。
- `python -m unittest discover -s learning_agent\tests` 通过：502 tests OK，skipped=1。

仍未完成：
- 仍需要运行 `learning_agent/start_oauth_agent.bat` 的真实可见终端交互验收。按 AGENTS 规则，该门禁未完成前，不能说 Stage 1 开发完成或验收通过。

## 2026-06-01 双轨真实浏览器 Stage 1 真实终端验收

状态：Stage 1 的代码实现、自动化测试、学习备份、真实可见终端交互验收和独立 verifier 复验均已完成。

新增验收场景：
- `learning_agent/acceptance_controller/scenarios/browser_provider_router_stage1_acceptance.json`。
- 场景要求真实终端里的 agent 调用 `bash` 执行 Python 命令，导入 `BrowserProviderRouter`、`BrowserProviderHealth`、`BrowserProviderKind` 和 `build_provider_decision_event`。
- 场景验证插件不可用但明确允许 CDP fallback 时，结果为 `provider=real_chrome_cdp`、`reason_code=extension_unavailable_cdp_fallback_allowed`、`schema_version=1`、`fallback_from=chrome_extension`。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 启动真实可见终端窗口。
- controller run：`learning_agent/acceptance_controller/runs/browser_provider_router_stage1_acceptance-20260601_165755`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`。
- 真实终端里的 agent 调用 `bash` 成功输出：`PROVIDER_ROUTER_STAGE1_OK provider=real_chrome_cdp reason_code=extension_unavailable_cdp_fallback_allowed schema_version=1 fallback_from=chrome_extension`。

独立 verifier：
- 已运行 `python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_provider_router_stage1_acceptance-20260601_165755 .\learning_agent\acceptance_controller\scenarios\browser_provider_router_stage1_acceptance.json`。
- verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- artifact checks 确认 `result_json`、`event_log`、`debug_log`、`startup_screenshot`、`prompt_screenshot`、`final_screenshot` 均存在。

结论：
- Stage 1 可以标记为已完成；下一步应进入 Stage 2 的独立详细计划，而不是直接改 Chrome 插件或 native host。

## 2026-06-01 双轨真实浏览器 Stage 1 最终收口

状态：Stage 1 已收口。

最终自动化验证：
- `python -m json.tool .\learning_agent\acceptance_controller\scenarios\browser_provider_router_stage1_acceptance.json > $null` 通过。
- `python -m unittest learning_agent.tests.test_browser_provider_router` 通过：12 tests OK。
- `python -m unittest discover -s learning_agent\tests` 通过：502 tests OK，skipped=1。

代码质量复审：
- 子代理代码质量复审返回：通过。
- 复审确认 `router.py` 已复用 `REAL_CHROME_INTENT_KEYWORDS`，并排除“可见浏览器 / 真实可见浏览器 / visible browser”，避免普通可见 Chromium 请求误判为插件路线。
- 复审确认 CDP fallback 只有 `allow_cdp_fallback=True` 时才执行，且 metadata 记录 `fallback_from` 和 `unavailable_reason`。
- 复审确认 payload 已包含 `schema_version=1`、`reason_code` 和 JSON 安全 metadata。
- 复审确认 `provider_events` helper、registry 写入和 registry 快照副本均有测试覆盖。

下一步：
- 进入 Stage 2 前必须先写独立详细计划；Stage 2 不应直接大改 Chrome 插件或 native host。

## 2026-06-01 双轨真实浏览器 Stage 2 计划启动

状态：Stage 2 独立详细计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage2-provider-adapters.md`。

学习备份：
- `learning_agent/test/browser_dual_track_stage2_20260601/plan.md`。

Stage 2 边界：
- 只迁入现有 Playwright / 可见 Chromium 和真实 Chrome CDP 能力到 provider adapter。
- 保持模型表面统一 `browser_*` 工具。
- 顶层浏览器工具调用要写 `browser_provider_decision` 事件。
- 不写 Chrome 插件，不安装 native host，不实现 `browser_tabs_context` 强制合同。

## 2026-06-01 双轨真实浏览器 Stage 2 完成

状态：Stage 2 已完成代码实现、自动化测试、学习备份、真实可见终端验收和独立 verifier 复验。

新增与修改：
- 新增 `learning_agent/browser/providers/visible_chromium.py`，提供 `VisibleChromiumProvider`。
- 新增 `learning_agent/browser/providers/real_chrome_cdp.py`，提供 `RealChromeCdpProvider`。
- 修改 `learning_agent/browser/providers/protocol.py`，新增 `BrowserProvider` Protocol。
- 修改 `learning_agent/browser/providers/registry.py`，新增 provider 注册和查询能力。
- 修改 `learning_agent/browser/providers/__init__.py`，导出 Stage 2 provider adapter。
- 修改 `learning_agent/browser_automation_mcp_server.py`，顶层工具调用先写 `browser_provider_decision`，再通过 provider adapter handler 进入 `BrowserActionExecutor`。
- 新增 `learning_agent/tests/test_browser_provider_adapters.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/browser_provider_adapters_stage2_acceptance.json`。
- 新增学习备份 `learning_agent/test/browser_dual_track_stage2_20260601/modified_snippets.md`。

红灯测试：
- `python -m unittest learning_agent.tests.test_browser_provider_adapters` 首次失败，错误包括缺少 `real_chrome_cdp`、`visible_chromium` 模块，以及 registry 缺少 `register_provider()`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_provider_adapters` 通过：5 tests OK。
- `python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters` 通过：17 tests OK。
- `python -m py_compile .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\visible_chromium.py .\learning_agent\browser\providers\real_chrome_cdp.py .\learning_agent\browser\providers\__init__.py .\learning_agent\browser_automation_mcp_server.py .\learning_agent\tests\test_browser_provider_adapters.py` 通过：退出码 0。
- `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters` 通过：38 tests OK。
- `python -m unittest discover -s learning_agent\tests` 通过：507 tests OK，skipped=1。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 启动真实可见终端窗口。
- controller run：`learning_agent/acceptance_controller/runs/browser_provider_adapters_stage2_acceptance-20260601_171446`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`。
- 真实终端里的 agent 调用 `bash` 成功输出：`PROVIDER_ADAPTERS_STAGE2_OK provider=visible_chromium decision_event=True result_has_wait=True`。

独立 verifier：
- 已运行 `python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_provider_adapters_stage2_acceptance-20260601_171446 .\learning_agent\acceptance_controller\scenarios\browser_provider_adapters_stage2_acceptance.json`。
- verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- artifact checks 确认 `result_json`、`event_log`、`debug_log`、`startup_screenshot`、`prompt_screenshot`、`final_screenshot` 均存在。

下一步：
- 进入 Stage 3 前必须先创建独立详细计划，目标是统一工具表面和模型防误选。
## 2026-06-01 双轨真实浏览器 Stage 3 完成

阶段目标：
- 按 `docs/superpowers/plans/2026-06-01-browser-dual-track-stage3-tool-surface.md` 执行 Stage 3，确保模型只看到统一 `browser_*` 工具，不直接选择 provider。

已完成：
- 新增 `learning_agent/browser/providers/tool_surface.py`，定义 provider-specific 重复动作识别、provider-control 控制工具识别和工具表面提示。
- 修改 `learning_agent/mcp/runtime.py`，让模型 catalog 过滤 `chrome_extension_open`、`real_chrome_cdp_click` 等 provider-specific 重复动作。
- 修改 `learning_agent/mcp/runtime.py`，让 `browser_connect_real_chrome` 等真实 Chrome 控制工具带 `advanced provider-control` 搜索提示。
- 修改 `learning_agent/skills/browser_automation/SKILL.md`、`learning_agent/skills/real_chrome/SKILL.md` 和 `learning_agent/browser/harness.py`，明确“不要直接选择 provider；只调用统一 browser_*；底层由 BrowserProviderRouter 决定并写 event log”。
- 新增 `learning_agent/tests/test_browser_tool_surface_stage3.py`，覆盖 6 个 Stage 3 门禁。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/browser_tool_surface_stage3_acceptance.json`。
- 已把本阶段计划和修改备份到 `learning_agent/test/browser_dual_track_stage3_20260601/`。

验证结果：
- 红灯测试先失败，失败点为缺少 `tool_surface.py`、缺少 `advanced provider-control` 标记、skill/harness 未包含 `BrowserProviderRouter` 单轨规则。
- `python -m unittest learning_agent.tests.test_browser_tool_surface_stage3`：6 tests OK。
- `python -m py_compile .\learning_agent\browser\providers\tool_surface.py .\learning_agent\browser\providers\__init__.py .\learning_agent\mcp\runtime.py .\learning_agent\browser\harness.py .\learning_agent\tests\test_browser_tool_surface_stage3.py`：通过。
- `python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tool_surface_stage3 learning_agent.tests.test_tools_policy`：105 tests OK。
- `python -m unittest discover -s learning_agent\tests`：513 tests OK，skipped=1。
- 真实可见终端验收 run：`learning_agent/acceptance_controller/runs/browser_tool_surface_stage3_acceptance-20260601_172518`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。

下一步：
- 进入 Stage 4：实现 `browser_tabs_context` 合同，让当前 Chrome/登录态任务在 click/type 前必须先读取 tab context，并防止 tab id 跨 session 复用。
## 2026-06-01 双轨真实浏览器 Stage 4 计划启动

状态：Stage 4 独立计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage4-tabs-context.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage4_20260601/plan.md`

本阶段边界：
- 新增统一 `browser_tabs_context` 工具。
- 真实 Chrome / 登录态写动作前必须先读取有效 tab context。
- 标签页关闭、切换、新建、真实 Chrome 重连或断开后旧 context 必须失效。
- 不做 Chrome 插件和 native host 实现；这些留到后续阶段。
## 2026-06-01 双轨真实浏览器 Stage 4 自动化实现完成

状态：Stage 4 代码实现、红灯测试、目标单测和相关回归已完成；真实可见终端验收尚未执行。

已完成：
- 新增 `browser_tabs_context` 工具。
- 真实 Chrome / 登录态写动作前强制要求先读取 `browser_tabs_context`。
- active tab 变化、标签页关闭、导航、真实 Chrome 重连/断开后旧 context 会失效。
- provider adapter 已声明支持 `browser_tabs_context`。
- skill 和 harness 已补充 tabs context 使用规则。
- 学习备份已写入 `learning_agent/test/browser_dual_track_stage4_20260601/modified_snippets.md`。

当前验证：
- 红灯测试首次失败点为未知工具、缺 provider 支持和写动作未被 context 拦截。
- `python -m unittest learning_agent.tests.test_browser_tabs_context_stage4` 已通过，5 tests OK。
- 相关回归 `test_browser_tabs_context_stage4/test_browser_provider_adapters/test_browser_tool_surface_stage3/test_browser_session_manager` 已通过，20 tests OK。
- Stage 4 修改文件 `py_compile` 已通过。

下一步：
- 运行全量 `python -m unittest discover -s learning_agent\tests`。
- 通过 `learning_agent/start_oauth_agent.bat` 执行 `browser_tabs_context_stage4_acceptance.json` 真实可见终端验收。
## 2026-06-01 双轨真实浏览器 Stage 4 完成

状态：Stage 4 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

最终自动化验证：
- `python -m unittest learning_agent.tests.test_browser_tabs_context_stage4`：5 tests OK。
- `python -m unittest learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tool_surface_stage3 learning_agent.tests.test_browser_session_manager`：20 tests OK。
- `python -m unittest discover -s learning_agent\tests`：518 tests OK，skipped=1。
- `python -m py_compile .\learning_agent\browser_automation_mcp_server.py .\learning_agent\browser\providers\visible_chromium.py .\learning_agent\browser\providers\real_chrome_cdp.py .\learning_agent\browser\harness.py .\learning_agent\tests\test_browser_tabs_context_stage4.py`：退出码 0。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/browser_tabs_context_stage4_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/browser_tabs_context_stage4_acceptance-20260601_174203`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已通过，最终回答包含 `BROWSER_TABS_CONTEXT_STAGE4_READY STAGE4_TABS_CONTEXT_OK`。

结论：
- 当前 Chrome / 登录态写动作已经被 `browser_tabs_context` 合同卡住。
- Stage 5 应进入 Chrome 插件 MVP 只读能力，不应跳到写动作或权限系统。
## 2026-06-01 双轨真实浏览器 Stage 5 计划启动

状态：Stage 5 独立计划已创建，准备进入红灯测试和只读插件基础设施实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage5-chrome-extension-readonly.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage5_20260601/plan.md`

本阶段边界：
- 只做 Chrome extension / native host / provider 的只读闭环。
- 只允许 tabs context、read page、status。
- 不实现点击、输入、按键、上传、提交等写动作。
- 不安装真实插件，不写 Windows 注册表。
## 2026-06-01 双轨真实浏览器 Stage 5 完成

状态：Stage 5 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

已完成：
- 新增 `learning_agent/chrome_extension/`，包含 Manifest V3 扩展文件、background、content script、page bridge 和 options 页面。
- 新增 `learning_agent/browser_extension_host/`，包含只读消息协议、bridge state、pairing store、native host 和 manifest 生成器。
- 新增 `ChromeExtensionProvider`，默认未连接不可用，连接后只支持 `browser_tabs_context`、`browser_snapshot`、`browser_extension_status`。
- `BrowserAutomationServer` 已注册 Chrome extension provider，并公开 `browser_extension_status` 统一状态工具。
- Stage 5 明确不开放点击、输入、按键、上传、提交等写动作，也不安装真实插件或写 Windows 注册表。
- 学习备份已写入 `learning_agent/test/browser_dual_track_stage5_20260601/modified_snippets.md`。

自动化验证：
- 红灯测试首次失败点为缺插件文件、缺 host 包、缺 provider 和缺 `browser_extension_status`。
- `python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5`：5 tests OK。
- `python -m unittest learning_agent.tests.test_chrome_extension_readonly_stage5 learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_tool_surface_stage3`：33 tests OK。
- `python -m unittest discover -s learning_agent\tests`：523 tests OK，skipped=1。
- Stage 5 修改文件 `py_compile`：退出码 0。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/chrome_extension_readonly_stage5_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/chrome_extension_readonly_stage5_acceptance-20260601_175710`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- 最终回答包含 `CHROME_EXTENSION_STAGE5_READY STAGE5_CHROME_EXTENSION_READONLY_OK`。

结论：
- Chrome 插件路线现在有了可审计的只读 MVP 底座。
- Stage 6 应进入 Chrome 插件写动作，但必须继续保持统一 `browser_*` 工具表面、权限门禁和真实终端验收。
## 2026-06-01 双轨真实浏览器 Stage 6 计划启动

状态：Stage 6 独立计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage6-chrome-extension-write-actions.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage6_20260601/plan.md`

本阶段边界：
- 让 Chrome 插件 provider 支持统一 `browser_click`、`browser_type`、`browser_press_key`、`browser_open`、`browser_wait`、`browser_visual_locate` 等写动作和辅助动作。
- 不新增模型可见 provider-specific 重复工具。
- 不安装真实 Chrome 扩展，不写 Windows 注册表。
- 站点级权限系统放到 Stage 7。
## 2026-06-01 双轨真实浏览器 Stage 6 完成

状态：Stage 6 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

已完成：
- `message_protocol.py` 新增 `build_write_command()` 和 `action_result` 脱敏响应。
- `ChromeExtensionBridgeState` 新增 pending command 队列、结果记录、结果等待和命令状态文本。
- `native_host.py` 支持 `poll_commands` 和 `action_result`，让扩展可以拉取命令并回传执行结果。
- `ChromeExtensionProvider` 支持 `browser_click`、`browser_type`、`browser_press_key`、`browser_open`、`browser_wait`、`browser_visual_locate`。
- `background.js` 支持命令轮询、执行命令和回传结果。
- `content_script.js` 支持页面侧 click、type、press_key、wait、scroll、visual_locate。
- 生产 `BrowserAutomationServer.call()` 的插件写动作仍进入 `BrowserActionExecutor.execute_action()`。

自动化验证：
- 红灯测试首次失败点为缺 `build_write_command`、缺 bridge 队列、provider 不支持命令超时、server 写动作回退旧 handler。
- `python -m unittest learning_agent.tests.test_chrome_extension_write_actions_stage6`：5 tests OK。
- Stage 5/6 与 provider 相关回归：38 tests OK。
- `python -m unittest discover -s learning_agent\tests`：528 tests OK，skipped=1。
- Stage 6 修改文件 `py_compile`：退出码 0。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/chrome_extension_write_actions_stage6_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/chrome_extension_write_actions_stage6_acceptance-20260601_181238`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- 最终回答包含 `CHROME_EXTENSION_STAGE6_READY STAGE6_CHROME_EXTENSION_WRITE_ACTIONS_OK`。

结论：
- 插件 provider 已具备受控写动作命令队列和执行器接入。
- Stage 7 应进入插件站点权限，避免写动作在未授权 origin 上默认放开。
## 2026-06-01 双轨真实浏览器 Stage 7 计划启动

状态：Stage 7 独立计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage7-extension-site-permissions.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage7_20260601/plan.md`

本阶段边界：
- 给 Chrome extension provider 增加 origin 级权限。
- `read`、`click`、`type`、`submit`、`upload`、`console`、`network` 分开授权。
- 继续保持统一 `browser_site_grant` 和统一 `browser_*` 工具表面。
- 不做图形化授权 UI，不安装真实扩展。
## 2026-06-01 双轨真实浏览器 Stage 7 完成

状态：Stage 7 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

已完成：
- `BrowserSitePermissions` 支持 origin + action 级权限：`read`、`click`、`type`、`submit`、`upload`、`console`、`network`。
- `ChromeExtensionProvider` 在读写工具前检查 origin 权限，未授权时抛 `PermissionError`。
- `ChromeExtensionBridgeState` 可提供 active tab URL、page_id 对应 URL，并记录 permission event。
- `browser_site_grant` schema 新增 `permissions` 参数，并同步到 `ChromeExtensionProvider.site_permissions`。
- `browser_site_grant list` 会显示 Chrome extension provider 的动作级权限 JSON。

自动化验证：
- 红灯测试首次失败点为 `grant(permissions=...)` 不支持、provider 不接受 `site_permissions`、未授权 click 进入命令队列超时。
- `python -m unittest learning_agent.tests.test_chrome_extension_site_permissions_stage7`：4 tests OK。
- Stage 5/6/7 与权限相关回归：44 tests OK。
- `python -m unittest discover -s learning_agent\tests`：532 tests OK，skipped=1。
- Stage 7 修改文件 `py_compile`：退出码 0。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/chrome_extension_site_permissions_stage7_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/chrome_extension_site_permissions_stage7_acceptance-20260601_182242`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- 最终回答包含 `CHROME_EXTENSION_STAGE7_READY STAGE7_CHROME_EXTENSION_SITE_PERMISSIONS_OK`。

结论：
- 插件读写动作已具备 origin + action 级权限边界。
- Stage 8 应进入状态 UI / CLI / API 生态，把 provider、native host、tab、permission、run、action、observation 统一展示给其他 agent。

## 2026-06-01 双轨真实浏览器 Stage 8 计划启动

状态：Stage 8 独立计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage8-status-ui-cli-api.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage8_20260601/plan.md`

本阶段边界：
- 把 provider、Chrome 插件连接、native host 状态、tab、权限、最近动作、observation 接入统一 status snapshot。
- 扩展终端状态渲染、SDK、HTTP API、CLI 和 `browser_provider_status` 工具。
- 不新增 provider-specific 模型可见动作工具，不做真实扩展安装，不做 GIF/录屏。

## 2026-06-01 双轨真实浏览器 Stage 8 完成

状态：Stage 8 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

已完成：
- `learning_agent/runtime/status_snapshot.py` 新增 `browser.provider_status`，统一聚合 provider、Chrome 插件、native host、tabs、permissions、recent actions、recent observations。
- `learning_agent/app/status_renderer.py` 新增 `Browser Providers` 区块，终端状态能看到 provider 可用性、插件连接、pending command、权限事件和 active tab URL。
- `learning_agent/sdk/status.py` 新增 `get_browser_provider_status(workspace)`，让其他 agent 直接读取 provider 状态。
- `learning_agent/browser_automation_mcp_server.py` 新增 `browser_provider_status` 工具，并补脚本模式导入 fallback。
- `learning_agent/app/http_bridge.py` 新增 `/browser/providers` 和 `/v1/browser/providers`。
- `learning_agent/harness/cli.py` 新增 `provider-status --workspace`。
- 新增 `learning_agent/tests/test_chrome_extension_status_ecosystem_stage8.py`。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/chrome_extension_status_ecosystem_stage8_acceptance.json`。
- 学习备份已写入 `learning_agent/test/browser_dual_track_stage8_20260601/modified_snippets.md`。

自动化验证：
- `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`：3 tests OK。
- `python -m py_compile learning_agent\runtime\status_snapshot.py learning_agent\app\status_renderer.py learning_agent\sdk\status.py learning_agent\browser_automation_mcp_server.py learning_agent\app\http_bridge.py learning_agent\harness\cli.py learning_agent\tests\test_chrome_extension_status_ecosystem_stage8.py`：退出码 0。
- Stage 5/6/7/8 与状态生态相关回归：47 tests OK。
- `python -m unittest discover -s learning_agent\tests`：535 tests OK，skipped=1。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/chrome_extension_status_ecosystem_stage8_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/chrome_extension_status_ecosystem_stage8_acceptance-20260601_184110`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`。
- 真实终端中的 agent 执行 `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`，结果 `Ran 3 tests`、`OK`。
- 最终标记：`CHROME_EXTENSION_STAGE8_READY STAGE8_STATUS_ECOSYSTEM_OK`。

独立 verifier：
- verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- artifact checks 确认 `result_json`、`event_log`、`debug_log`、`startup_screenshot`、`prompt_screenshot`、`final_screenshot` 均存在。

结论：
- Stage 8 可以标记完成。
- 下一阶段进入 Stage 9：GIF/录屏/视觉证据，把多步真实浏览器任务的过程证据从“单张截图/日志”升级为可回放的帧序列或 GIF。

## 2026-06-01 双轨真实浏览器 Stage 9 计划启动

状态：Stage 9 独立计划已创建，准备进入红灯测试和实现。

计划文件：
- `docs/superpowers/plans/2026-06-01-browser-dual-track-stage9-visual-evidence.md`

学习备份：
- `learning_agent/test/browser_dual_track_stage9_20260601/plan.md`

本阶段边界：
- 新增统一 `browser_record_start`、`browser_record_stop`、`browser_gif_export` 工具。
- 浏览器动作成功后自动保存帧，不要求模型每一步手动截图。
- 使用 Pillow 生成 GIF，不引入新依赖。
- 状态快照和终端渲染必须能看到最近录制、帧数和 GIF 路径。
- 独立 verifier 必须能通过 `required_artifact_globs` 检查帧序列和 GIF 产物真实存在。

## 2026-06-01 双轨真实浏览器 Stage 9 完成

状态：Stage 9 已通过代码实现、自动化测试、全量回归、真实可见终端验收和独立 verifier。

已完成：
- 新增 `learning_agent/browser/recording.py`，包含 `BrowserRecordingStore`、PNG 帧 manifest、GIF 导出和 selftest 入口。
- 新增 `browser_record_start`、`browser_record_stop`、`browser_gif_export` 三个统一浏览器工具。
- 成功浏览器动作会自动调用 `_capture_recording_frame()`，把当前页面画面保存为 PNG 帧。
- 录制开始、录帧、停止和 GIF 导出写入 browser runtime event log。
- `status_snapshot.py` 新增 `browser.recordings` 区块。
- `status_renderer.py` 新增 `Browser Recordings` 终端区块。
- `acceptance/verifier.py` 新增 `required_artifact_globs`，支持 `{project_root}` 和 `{run_dir}`，可独立检查帧序列和 GIF 真实存在。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/browser_visual_evidence_stage9_acceptance.json`。
- 学习备份已写入 `learning_agent/test/browser_dual_track_stage9_20260601/modified_snippets.md`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_acceptance_verifier`：7 tests OK。
- `python -m py_compile learning_agent\browser\recording.py learning_agent\browser\runtime_events.py learning_agent\browser_automation_mcp_server.py learning_agent\runtime\status_snapshot.py learning_agent\app\status_renderer.py learning_agent\acceptance\verifier.py learning_agent\tests\test_browser_recording_stage9.py learning_agent\tests\test_acceptance_verifier.py`：退出码 0。
- `python -m learning_agent.browser.recording --selftest --workspace H:\codexworkplace\sofeware\OpenHarness-main`：输出 `STAGE9_RECORDING_SELFTEST_OK`，生成 3 帧和 GIF。
- Stage 8/9 状态相关回归：11 tests OK。
- `python -m unittest discover -s learning_agent\tests`：539 tests OK，skipped=1。

真实可见终端验收：
- controller 场景：`learning_agent/acceptance_controller/scenarios/browser_visual_evidence_stage9_acceptance.json`。
- run 目录：`learning_agent/acceptance_controller/runs/browser_visual_evidence_stage9_acceptance-20260601_185914`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`。
- 真实终端中的 agent 执行 `python -m unittest learning_agent.tests.test_browser_recording_stage9`，结果 `Ran 3 tests`、`OK`。
- 真实终端中的 agent 执行 `python -m learning_agent.browser.recording --selftest --workspace H:\codexworkplace\sofeware\OpenHarness-main`，输出 `STAGE9_RECORDING_SELFTEST_OK`。
- 最终标记：`BROWSER_VISUAL_EVIDENCE_STAGE9_READY STAGE9_VISUAL_EVIDENCE_OK`。

独立 verifier：
- verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`。
- `required_artifact_glob_checks` 三项均为 true：
  - `recording_manifest.json`
  - `frames/*.png`
  - `stage9_selftest.gif`

结论：
- Stage 9 可以标记完成。
- 下一阶段进入 Stage 10：失败恢复和 fallback 策略，重点是插件不可用、tab 丢失、权限不足、页面卡死时不乱降级、不乱重跑。
- 2026-06-01 Stage 10 开始执行：已新增书面计划 `docs/superpowers/plans/2026-06-01-browser-dual-track-stage10-fallback-recovery.md`，并备份到 `learning_agent/test/browser_dual_track_stage10_20260601/plan.md`；本阶段范围锁定为不静默降级、显式 CDP fallback、不可用 provider 阻断、tab context 刷新提示、连续失败停止。
## 2026-06-01 双轨真实浏览器 Stage 10 完成

状态：Stage 10 已通过代码实现、聚焦单测、相关回归、全量测试、真实可见终端验收和独立 verifier。

完成内容：
- `browser_automation_mcp_server.py` 不再默认允许 CDP fallback；只有参数 `allow_cdp_fallback=true` 才允许从 Chrome 插件不可用场景退到 RealChromeCdpProvider。
- `allow_cdp_fallback` 参数在进入 router 文本意图匹配前会被剥离，避免字段名里的 `cdp` 被误判为用户主动请求 CDP。
- provider 决策为 `UNAVAILABLE` 时，点击/输入等写动作会明确阻断，不会落回旧 handler 静默执行。
- `browser_tabs_context`、`browser_tabs`、provider/status 类只读恢复工具在 provider 不可用时仍可执行，避免用户连恢复前的状态都看不到。
- 新增连续浏览器失败预算：顶层浏览器工具连续失败 3 次后停止，写入 `browser_recovery_stopped` 事件，并提示查看 provider status、tabs context 或 recover page。
- tab context 失效报错已明确要求“重新调用 browser_tabs_context 刷新标签页上下文”。

验证记录：
- `python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10`：5 tests OK。
- `python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_recovery learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`：30 tests OK。
- `python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\browser\runtime_events.py learning_agent\tests\test_browser_fallback_recovery_stage10.py learning_agent\tests\test_browser_tabs_context_stage4.py`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：544 tests OK，skipped=1。
- 真实可见终端验收场景：`learning_agent/acceptance_controller/scenarios/browser_fallback_recovery_stage10_acceptance.json`。
- controller run：`learning_agent/acceptance_controller/runs/browser_fallback_recovery_stage10_acceptance-20260601_191529`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- verifier 输出 `schema_version=2`、`completed=true`、`assertion.passed=true`，最终回答包含 `BROWSER_FALLBACK_RECOVERY_STAGE10_READY STAGE10_FALLBACK_RECOVERY_OK`。

学习备份：
- `learning_agent/test/browser_dual_track_stage10_20260601/`

下一步：
- 进入 Stage 11：长任务 harness 接入，确保浏览器 provider 决策、stage、queue、event log、action executor、observation、replay、verifier、resume/checkpoint 不再是旁路系统。
## 2026-06-01 ClaudeCode 本地真实浏览器能力源码对比

状态：已完成源码阅读和能力差距评估，本次没有修改产品代码。

本次只用源码作为证据，没有把 README 当关键证据。已阅读 ClaudeCode 的 `entrypoints/cli.tsx`、`utils/claudeInChrome/*`、`skills/bundled/claudeInChrome.ts`、`commands/chrome/chrome.tsx`、`utils/computerUse/*`、`services/tools/StreamingToolExecutor.ts`、`services/tools/toolExecution.ts`、`services/mcp/client.ts`、`services/mcp/config.ts` 等真实浏览器、Computer Use、MCP、权限和工具执行相关源码。

已阅读 learning_agent 的 `browser_automation_mcp_server.py`、`browser/providers/*`、`browser_extension_host/*`、`chrome_extension/*`、`browser/session_manager.py`、`browser/action_executor.py`、`browser/flow_runtime.py`、`browser/harness_integration.py`、`browser/observation.py`、`browser/locator.py`、`browser/recovery.py`、`browser/replay.py`、`runtime/status_snapshot.py` 等真实浏览器双轨架构源码。

结论：按“本地真实浏览器能力”口径，learning_agent 当前大约达到 ClaudeCode 的 70% 到 78%，中位估算约 72%。如果只按 Windows 上可验证的真实 Chrome/可见浏览器任务比较，可接近 75% 到 80%；如果把 ClaudeCode 的 Chrome 扩展生产安装、native host 配对、外部 `@ant/claude-for-chrome-mcp` 能力、macOS computer-use、终端 UI 和成熟工具执行器都算进去，则约 65% 到 70%。

主要差距集中在：生产级 Chrome 扩展/native host 安装与配对、浏览器发起 prompt/session sync、专门的 `form_input`/`computer`/`shortcuts` 类工具、OS 级鼠标键盘和显示器控制、StreamingToolExecutor 级别的并发流式工具执行、插件生态和 ToolSearch/skill 路由、`/chrome` 状态菜单/View Tab/权限面板等终端 UI 生态。

## 2026-06-01 Agent Capability Completion Roadmap Planning

- 用户要求按建议补齐七大方向，并先生成书面计划防止复杂任务跑偏。
- 已读取 `learning_agent/zqbcontext.md`、根 `task_plan.md`、`findings.md`、根 `progress.md` 和 `agent_memory/progress.md`，确认当前 baseline。
- 已生成主控计划：`docs/superpowers/plans/2026-06-01-agent-capability-completion-roadmap.md`。
- 已生成 agent_memory 记录：`agent_memory/agent_capability_completion_roadmap_20260601.md`。
- 已生成学习备份：`learning_agent/test/agent_capability_completion_20260601/plan.md`。
- 已更新根 `task_plan.md`，把当前 active plan 切换为 Agent Capability Completion Roadmap。
- 当前阶段：只完成书面计划，尚未修改运行时代码，尚未开始 Phase 1 实现。

## 2026-06-01 Agent Capability Completion Phase 1

- 已创建 Phase 1 子计划：`docs/superpowers/plans/2026-06-01-phase1-chrome-extension-installer-native-host.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_chrome_extension_installer_stage13.py`，红灯证明缺少 `ChromeNativeHostInstaller` 和 `MemoryNativeHostRegistryAdapter`。
- 已实现 `learning_agent/browser_extension_host/manifest_installer.py`：新增 native host 名称常量、Windows registry 路径常量、registry adapter 协议、内存 fake adapter、真实 Windows HKCU adapter、`ChromeNativeHostInstaller.status/install/uninstall/repair_hint`。
- 已扩展 `learning_agent/browser_automation_mcp_server.py`：新增 `browser_extension_install`、`browser_extension_uninstall`、`browser_extension_repair_hint` 工具，并把 installer 状态并入 `browser_extension_status`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13`，Ran 4 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_chrome_extension_readonly_stage5 learning_agent.tests.test_chrome_extension_write_actions_stage6 learning_agent.tests.test_chrome_extension_site_permissions_stage7 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`，Ran 21 tests OK。
- 已验证：`python -m py_compile learning_agent\browser_extension_host\manifest_installer.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_chrome_extension_installer_stage13.py`，退出码 0。
- 已备份 Phase 1 修改到 `learning_agent/test/agent_capability_completion_20260601/phase1/`。
- 当前阶段：Phase 1 自动化验证完成；真实可见终端总验收将在 Phase 7 统一执行。

## 2026-06-01 Agent Capability Completion Phase 2

- 已创建 Phase 2 子计划：`docs/superpowers/plans/2026-06-01-phase2-chrome-extension-pairing-session-sync.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_chrome_extension_pairing_stage14.py`，红灯证明 `ChromeExtensionBridgeState` 缺少 `record_pairing` 和 `enqueue_browser_prompt`。
- 已扩展 `learning_agent/browser_extension_host/pairing_store.py`：新增递归敏感字段过滤、`save_pairing()` 和 `pairing_summary()`。
- 已扩展 `learning_agent/browser_extension_host/bridge_server.py`：新增 `record_pairing()`、`pairing_summary()`、`session_sync_status_text()`、`enqueue_browser_prompt()`，并把 paired/device/session/last_browser_prompt_id 接入状态。
- 已扩展 `learning_agent/browser_extension_host/native_host.py`：新增 `pair_device` 和 `browser_prompt` 消息分支，browser prompt 写入 `RuntimeCommandQueue`。
- 已扩展 `learning_agent/chrome_extension/background.js`：连接 native host 后发送配对摘要，并支持 `browser_prompt` 消息推送。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_extension_pairing_stage14 ... test_chrome_extension_status_ecosystem_stage8`，Ran 23 tests OK。
- 已验证：`python -m py_compile learning_agent\browser_extension_host\pairing_store.py learning_agent\browser_extension_host\bridge_server.py learning_agent\browser_extension_host\native_host.py learning_agent\tests\test_chrome_extension_pairing_stage14.py`，退出码 0。
- 已验证：`node --check learning_agent\chrome_extension\background.js`，退出码 0。
- 已备份 Phase 2 修改到 `learning_agent/test/agent_capability_completion_20260601/phase2/`。
- 当前阶段：Phase 2 自动化验证完成；真实可见终端总验收将在 Phase 7 统一执行。

## 2026-06-01 Agent Capability Completion Phase 3

- 已创建 Phase 3 子计划：`docs/superpowers/plans/2026-06-01-phase3-high-level-browser-tools.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_browser_high_level_tools_stage15.py`，红灯证明缺少高层 helper、工具 schema 和 server 分发。
- 已新增 `learning_agent/browser/high_level_tools.py`：提供 `browser_form_input` 的底层计划构建、快捷键别名映射和快捷键清单格式化。
- 已扩展 `learning_agent/browser_automation_mcp_server.py`：新增 `browser_form_input`、`browser_shortcuts_list`、`browser_shortcuts_execute`，并接入重试、回放阻断、真实 Chrome tabs context 写动作门禁。
- 已验证：`python -m unittest learning_agent.tests.test_browser_high_level_tools_stage15`，Ran 4 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_browser_high_level_tools_stage15 learning_agent.tests.test_browser_tool_surface_stage3 learning_agent.tests.test_browser_locator learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_extension_installer_stage13`，Ran 19 tests OK。
- 已验证：`python -m py_compile learning_agent\browser\high_level_tools.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_browser_high_level_tools_stage15.py`，退出码 0。
- 已备份 Phase 3 修改到 `learning_agent/test/agent_capability_completion_20260601/phase3/`。
- 当前阶段：Phase 3 自动化验证完成；真实可见终端总验收将在 Phase 7 统一执行。

## 2026-06-01 Agent Capability Completion Phase 4

- 已创建 Phase 4 子计划：`docs/superpowers/plans/2026-06-01-phase4-global-streaming-tool-executor.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_streaming_tool_executor_stage16.py`，红灯证明缺少全局 streaming executor，且 orchestrator 会原样返回 generator。
- 已新增 `learning_agent/tools/streaming_executor.py`：统一 `tool_started`、`tool_result_chunk`、`tool_completed`、`tool_failed` 事件和分段结果拼接。
- 已扩展 `learning_agent/tools/orchestrator.py`：所有单工具执行路径改为通过全局 streaming executor，并将事件写入 `streaming_tool_executor` observation。
- 已验证：`python -m unittest learning_agent.tests.test_streaming_tool_executor_stage16`，Ran 3 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_streaming_tool_executor_stage16 learning_agent.tests.test_tool_orchestrator learning_agent.tests.test_tool_executor_v2 learning_agent.tests.test_tool_protocol learning_agent.tests.test_mcp_registry`，Ran 124 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_high_level_tools_stage15`，Ran 14 tests OK。
- 已验证：`python -m py_compile learning_agent\tools\streaming_executor.py learning_agent\tools\orchestrator.py learning_agent\tests\test_streaming_tool_executor_stage16.py`，退出码 0。
- 已备份 Phase 4 修改到 `learning_agent/test/agent_capability_completion_20260601/phase4/`。
- 当前阶段：Phase 4 自动化验证完成；真实可见终端总验收将在 Phase 7 统一执行。

## 2026-06-01 Agent Capability Completion Phase 5

- 已创建 Phase 5 子计划：`docs/superpowers/plans/2026-06-01-phase5-os-computer-use.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_os_computer_use_stage17.py`，红灯证明项目缺少 `learning_agent.computer_use` 模块。
- 已新增 `learning_agent/computer_use/controller.py` 和 `learning_agent/computer_use/__init__.py`：提供默认安全关闭后端、测试内存后端、动作结果对象和统一控制器。
- 已扩展 `learning_agent/tools/schemas.py`：新增 `computer_status` 和 `computer_action` 工具 schema，并归入 `computer_use` 能力包。
- 已扩展 `learning_agent/tools/catalog.py`：`computer_status` 标记为只读并发安全，`computer_action` 标记为高风险、需用户交互、禁止并发。
- 已扩展 `learning_agent/tools/executor.py` 和 `learning_agent/core/agent.py`：接入 `computer_status`、`computer_action` 分发，桌面动作会先走 `ask_permission`，再走 `confirm_desktop_control` 安全门。
- 已验证：`python -m unittest learning_agent.tests.test_os_computer_use_stage17`，Ran 4 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_streaming_tool_executor_stage16 learning_agent.tests.test_tool_orchestrator learning_agent.tests.test_tool_executor_v2 learning_agent.tests.test_tool_protocol learning_agent.tests.test_mcp_registry`，Ran 128 tests OK。
- 已验证：`python -m py_compile learning_agent\computer_use\__init__.py learning_agent\computer_use\controller.py learning_agent\tools\schemas.py learning_agent\tools\catalog.py learning_agent\tools\executor.py learning_agent\core\agent.py`，退出码 0。
- 已备份 Phase 5 修改到 `learning_agent/test/agent_capability_completion_20260601/phase5/`。
- 当前阶段：Phase 5 自动化验证完成；真实可见终端总验收将在 Phase 7 统一执行。

## 2026-06-01 Agent Capability Completion Phase 6

- 已创建 Phase 6 子计划：`docs/superpowers/plans/2026-06-01-phase6-chrome-terminal-status-ui.md`。
- 已按 TDD 写红灯测试：`learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`，红灯证明缺少 `learning_agent.app.chrome_status_renderer`。
- 已新增 `learning_agent/app/chrome_status_renderer.py`：提供 `/chrome` 聚焦状态页，覆盖 provider、extension、native host、active tab、权限事件、最近 run 和录制证据。
- 已扩展 `learning_agent/app/interactive.py`：新增 `/chrome` 和 `chrome` 命令，复用 `build_status_snapshot()` 并写入 `chrome_status_printed` 验收事件。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_browser_status_ecosystem learning_agent.tests.test_chrome_extension_status_ecosystem_stage8 learning_agent.tests.test_status_ecosystem_deep_alignment`，Ran 9 tests OK。
- 已验证：`python -m py_compile learning_agent\app\chrome_status_renderer.py learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py`，退出码 0。
- 已备份 Phase 6 修改到 `learning_agent/test/agent_capability_completion_20260601/phase6/`。
- 当前阶段：Phase 6 自动化验证完成；下一步进入 Phase 7 真实端到端验收矩阵。

## 2026-06-01 Agent Capability Completion Phase 7

- 已创建 Phase 7 子计划：`docs/superpowers/plans/2026-06-01-phase7-real-e2e-acceptance-matrix.md`。
- 已新增验收矩阵：`learning_agent/acceptance_controller/scenarios/agent_capability_completion_phase7_matrix.json`，覆盖 Phase 1-7 的自动化测试、备份目录和真实终端场景。
- 已新增真实终端 `/chrome` 场景：`learning_agent/acceptance_controller/scenarios/agent_capability_completion_phase7_chrome_status.json`。
- 已新增矩阵测试：`learning_agent/tests/test_agent_capability_acceptance_matrix_stage19.py`。
- 已扩展 `learning_agent/acceptance_controller/controller.ps1`：支持事件型终端命令验收，`/chrome` 可在 `chrome_status_printed` 出现后完成，不再强等 `final_answer_printed`。
- 已扩展 `learning_agent/acceptance/verifier.py`：无模型最终回答、无 debug 断言的事件型场景允许没有 `latest_run_readable.md`，但仍强制检查 result/events/screenshots。
- 已验证：`python -m unittest learning_agent.tests.test_agent_capability_acceptance_matrix_stage19`，Ran 3 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_browser_high_level_tools_stage15 learning_agent.tests.test_streaming_tool_executor_stage16 learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_agent_capability_acceptance_matrix_stage19`，Ran 22 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_agent_capability_acceptance_matrix_stage19 learning_agent.tests.test_acceptance_verifier learning_agent.tests.test_chrome_terminal_status_ui_stage18`，Ran 9 tests OK。
- 已验证：`python -m py_compile learning_agent\acceptance\verifier.py learning_agent\tests\test_agent_capability_acceptance_matrix_stage19.py`，退出码 0。
- 已验证 PowerShell 解析：`[scriptblock]::Create(controller.ps1)`，输出 `POWERSHELL_PARSE_OK`。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_completion_phase7_chrome_status-20260601_221208`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 已备份 Phase 7 修改和真实验收结果到 `learning_agent/test/agent_capability_completion_20260601/phase7/`。
- 当前阶段：Phase 1-7 已全部完成自动化验证和真实可见终端验收。

## 2026-06-01 Agent Capability Phase 9 Chrome Terminal Subcommands

- 已按 TDD 写红灯测试：`learning_agent/tests/test_chrome_terminal_subcommands_phase9.py`，红灯证明 `learning_agent.app.interactive` 缺少可测试的 `/chrome` 子命令入口。
- 已扩展 `learning_agent/app/interactive.py`：新增 `run_chrome_terminal_command()`，支持 `/chrome install-preview`、`/chrome repair`、`/chrome uninstall-preview`，并让真实交互循环识别 `/chrome ...` 子命令。
- `/chrome install-preview` 默认生成 native host manifest 和 `.cmd` launcher，只输出 `dry_run=true` 审计信息，不写 Windows registry。
- 已根据真实终端截图修正 workspace 路径兼容：repo 根目录和 `learning_agent` 目录都能生成正确路径，避免 `learning_agent\learning_agent` 双层嵌套。
- `/chrome repair` 复用 `ChromeNativeHostInstaller.repair_hint()` 输出中文修复建议。
- `/chrome uninstall-preview` 默认只输出将影响的 registry key，`dry_run=true`，不删除 registry。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase9_chrome_install_preview.json`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`，Ran 4 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`，Ran 13 tests OK。
- 已验证：`python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`，退出码 0。
- 已验证：`python -m unittest discover -s learning_agent\tests`，Ran 575 tests OK，skipped=1。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome install-preview`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase9_chrome_install_preview-20260601_224229`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 已查看最终截图 `03_final.png`：终端显示 `Chrome Action`、`action=browser_extension_install`、`dry_run=true`、manifest/launcher 路径，并确认路径为 `learning_agent\memory\chrome_native_host`，不再出现双层 `learning_agent\learning_agent`。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 当前阶段：Phase 9 自动化验证和真实可见终端验收完成。

## 2026-06-01 Agent Capability Phase 10 Chrome Install Confirm

- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_subcommands_phase9.py`，新增两个确认安装测试。
- 红灯已确认：新增测试首次因 `run_chrome_terminal_command()` 不支持 `registry_adapter` 且缺少 `/chrome install-confirm` 失败。
- 已扩展 `learning_agent/app/interactive.py`：新增 `CHROME_INSTALL_CONFIRM_TOKEN = "I_UNDERSTAND_WRITE_REGISTRY"`，并支持 `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。
- 缺少 extension_id 或确认 token 时，`/chrome install-confirm` 会输出拒绝原因和用法，不写 registry。
- 带确认 token 时，`/chrome install-confirm` 调用 `ChromeNativeHostInstaller.install(..., dry_run=False)`，写入 HKCU 下 Chrome/Edge/Brave/Chromium NativeMessagingHosts registry；自动化测试使用 `MemoryNativeHostRegistryAdapter` 验证，不碰真实系统。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase10_chrome_install_confirm_refusal.json`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`，Ran 6 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`，Ran 15 tests OK。
- 已验证：`python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`，退出码 0。
- 已验证：`python -m unittest discover -s learning_agent\tests`，Ran 577 tests OK，skipped=1。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome install-confirm abcdefghijklmnopabcdefghijklmnop`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase10_chrome_install_confirm_refusal-20260601_225316`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 已查看最终截图 `03_final.png`：终端显示 `Chrome Action`、`action=browser_extension_install_confirm`、`已拒绝执行：需要显式确认 token`，并提示 `I_UNDERSTAND_WRITE_REGISTRY`。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 当前阶段：Phase 10 自动化验证和真实可见终端拒绝验收完成。

## 2026-06-01 Agent Capability Phase 11 Chrome Uninstall Confirm

- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_subcommands_phase9.py`，新增两个确认卸载测试。
- 红灯已确认：新增测试首次因 `/chrome uninstall-confirm` 被识别为未知命令失败。
- 已扩展 `learning_agent/app/interactive.py`：新增 `CHROME_UNINSTALL_CONFIRM_TOKEN = "I_UNDERSTAND_DELETE_REGISTRY"`，并支持 `/chrome uninstall-confirm I_UNDERSTAND_DELETE_REGISTRY`。
- 缺少确认 token 时，`/chrome uninstall-confirm` 会输出拒绝原因和用法，不删 registry。
- 带确认 token 时，`/chrome uninstall-confirm` 调用 `ChromeNativeHostInstaller.uninstall(dry_run=False)`，删除 HKCU 下 Chrome/Edge/Brave/Chromium NativeMessagingHosts registry；自动化测试使用 `MemoryNativeHostRegistryAdapter` 验证，不碰真实系统。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase11_chrome_uninstall_confirm_refusal.json`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`，Ran 8 tests OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`，Ran 17 tests OK。
- 已验证：`python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`，退出码 0。
- 已验证：`python -m unittest discover -s learning_agent\tests`，Ran 579 tests OK，skipped=1。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome uninstall-confirm`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase11_chrome_uninstall_confirm_refusal-20260601_225807`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 已查看最终截图 `03_final.png`：终端显示 `Chrome Action`、`action=browser_extension_uninstall_confirm`、`已拒绝执行：需要显式确认 token`，并提示 `I_UNDERSTAND_DELETE_REGISTRY`。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 当前阶段：Phase 11 自动化验证和真实可见终端拒绝验收完成。

## 2026-06-01 Agent Capability Phase 12 Chrome Status Guide

- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`，新增 `/chrome` 向导渲染测试。
- 已按 TDD 新增 `learning_agent/tests/test_chrome_status_snapshot_phase12.py`，验证真实状态快照包含 native host installer 状态。
- 红灯已确认：渲染器缺少 `Chrome Guide`，快照缺少 `installer_state`。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：新增 `Chrome Guide` 区块，按 `installer_state` 给出下一条建议命令。
- 已扩展 `learning_agent/runtime/status_snapshot.py`：把 `ChromeNativeHostInstaller.status()` 合并进 `browser.provider_status.native_host`，包含 `installer_state`、`manifest_path`、`registry_targets` 等字段。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase12_chrome_status_guide.json`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18.ChromeTerminalStatusUiStage18Tests.test_render_chrome_status_guides_next_command_for_installer_states`，Ran 1 test OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_status_snapshot_phase12`，Ran 1 test OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8 learning_agent.tests.test_status_ecosystem_deep_alignment`，Ran 18 tests OK。
- 已验证：`python -m py_compile learning_agent\app\chrome_status_renderer.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py learning_agent\tests\test_chrome_status_snapshot_phase12.py`，退出码 0。
- 已验证：`python -m unittest discover -s learning_agent\tests`，Ran 581 tests OK，skipped=1。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase12_chrome_status_guide-20260601_230542`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 已查看最终截图 `03_final.png`：终端显示 `installer_state=manifest_created`、`Chrome Guide`、`next=/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 当前阶段：Phase 12 自动化验证和真实可见终端 `/chrome` 向导验收完成。

## 2026-06-02 Agent Capability Phase 13 Chrome Pairing Status

- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`，新增 `/chrome` pairing/session sync 渲染测试。
- 已按 TDD 扩展 `learning_agent/tests/test_chrome_status_snapshot_phase12.py`，新增真实 bridge pairing 状态快照测试。
- 红灯已确认：渲染器缺少 `paired=true/session_id`，快照缺少 `paired`。
- 已扩展 `learning_agent/runtime/status_snapshot.py`：从 `chrome_extension_bridge.json` 的 `pairing` 字段读取脱敏 `device_id`、`session_id`、`allowed_origins`，并合并进 `browser.provider_status.chrome_extension`。
- 已修正 `learning_agent` 工作区下 bridge 状态路径选择，避免读取 `learning_agent\learning_agent\memory\chrome_extension_bridge.json`。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：新增 `paired/device_id/session_id/allowed_origin_count/last_seen_at` 输出，并在已注册且已配对时提示 `session sync 已连接`。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase13_chrome_pairing_status.json`。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18.ChromeTerminalStatusUiStage18Tests.test_render_chrome_status_shows_pairing_and_session_sync`，Ran 1 test OK。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_status_snapshot_phase12.ChromeStatusSnapshotPhase12Tests.test_status_snapshot_includes_extension_pairing_and_session_sync`，Ran 1 test OK。
- 第一次真实终端验收失败：controller 把输入粘连为 `/chrome/chrome`，交互循环未识别该命令，导致进入模型调用并触发 API schema 错误。
- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_subcommands_phase9.py`：新增 `is_chrome_terminal_command()` 识别测试和 `/chrome/chrome` 重复粘连状态测试。
- 已扩展 `learning_agent/app/interactive.py`：新增 `is_chrome_terminal_command()`，真实交互循环现在会拦截 `/chrome/chrome` 并按 `/chrome` 状态命令处理。
- 已验证：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`，Ran 21 tests OK。
- 已验证：`python -m py_compile learning_agent\app\interactive.py learning_agent\app\chrome_status_renderer.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py learning_agent\tests\test_chrome_status_snapshot_phase12.py`，退出码 0。
- 已验证：`python -m unittest discover -s learning_agent\tests`，Ran 585 tests OK，skipped=1。
- 已完成真实可见终端交互验收：controller 启动 `learning_agent/start_oauth_agent.bat` 可见终端窗口，输入 `/chrome`，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase13_chrome_pairing_status-20260602_194601`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`state_checks.agent_ready_for_user_prompt=true`、`state_checks.chrome_status_printed=true`、`permission_sent_count=0`。
- 已查看最终截图 `03_final.png`：终端显示 `paired=false device_id= session_id= allowed_origin_count=0`，说明本机当前尚未完成扩展配对，但 `/chrome` 已能展示配对/session sync 缺失项。
- 独立 verifier 复验同一 run：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
- 当前阶段：Phase 13 自动化验证和真实可见终端 `/chrome` pairing 状态验收完成。

## 2026-06-02 Phase 14-23 Chrome/Browser/Harness Blueprint

- 用户要求：从 Phase 14 到 Phase 23 先做书面蓝图计划，用户确认后再执行。
- 已使用 writing-plans / planning-with-files 思路整理后续蓝图。
- 已创建蓝图文件：`docs/superpowers/plans/2026-06-02-phase14-23-chrome-browser-harness-blueprint.md`。
- 蓝图覆盖：
  - Phase 14 `/chrome pairing-diagnose`
  - Phase 15 Chrome extension 配对触发链路
  - Phase 16 session sync 真实闭环
  - Phase 17 `/chrome` 可操作向导增强
  - Phase 18 真实 Chrome extension 端到端验收
  - Phase 19 browser tool routing 强化
  - Phase 20 OS Computer Use 生产化
  - Phase 21 ClaudeCode-style terminal status UI
  - Phase 22 长任务 harness 与浏览器任务融合
  - Phase 23 最终端到端验收矩阵升级
- 当前状态：仅完成书面蓝图，尚未执行任何 Phase 14-23 代码实现；等待用户确认。
## 2026-06-02 Agent Capability Phase 14 Chrome Pairing Diagnose

- 已按 TDD 新增并通过 `learning_agent/tests/test_chrome_pairing_diagnose_phase14.py`，覆盖无 bridge 文件和半配对缺 session 字段两类场景。
- 已扩展 `learning_agent/app/interactive.py`，新增 `/chrome pairing-diagnose` 只读诊断命令，输出 `pairing_diagnose`、installer/bridge/extension/session 字段、`reason=...` 分类和 `next=...` 下一步建议。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase14_chrome_pairing_diagnose.json`。
- 自动化验证：Phase 14 聚焦测试 2 tests OK，相关回归 18 tests OK，`py_compile` 退出码 0，全量 `python -m unittest discover -s learning_agent\tests` 为 587 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome pairing-diagnose`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase14_chrome_pairing_diagnose-20260602_200019`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`chrome_status_printed=true`、`permission_sent_count=0`；独立 verifier 同样通过。
- 截图确认终端输出包含 `pairing_diagnose`、`paired=false`、多个 `reason=...` 和下一步命令。
- 学习备份目录：`learning_agent/test/agent_capability_phase14_chrome_pairing_diagnose_20260602/`。
- 当前状态：Phase 14 完成；下一步进入 Phase 15 Chrome extension 配对触发链路。
## 2026-06-02 Agent Capability Phase 15 Chrome Pairing Trigger

- 已按 TDD 新增并通过 `learning_agent/tests/test_chrome_pairing_trigger_phase15.py`，覆盖 pairing preview 只读、pairing-start-confirm 写 pending、bridge 完成态、扩展脚本响应 `pairing_request`。
- 已扩展 `learning_agent/browser_extension_host/bridge_server.py`：新增 `start_pairing_request()`、`pairing_request_summary()`、`pending_pairing_request()`，并在 `record_pairing()` 匹配 request 后标记 completed。
- 已扩展 `learning_agent/browser_extension_host/native_host.py`：`poll_commands` 响应会附带 `pairing_request`，让真实扩展能消费终端触发。
- 已扩展 `learning_agent/chrome_extension/background.js`：扩展收到 `pairing_request` 后回传 `pair_device`，并携带 `request_id` 和 `request_nonce`。
- 已扩展 `learning_agent/app/interactive.py`：新增 `/chrome pairing-preview` 和 `/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME`。
- 已扩展 `learning_agent/runtime/status_snapshot.py` 和 `learning_agent/app/chrome_status_renderer.py`：`/chrome` 可见 `pending_pairing_request_status`、`pending_pairing_request_id`、`pending_pairing_request_created_at`。
- 自动化验证：Phase 15 聚焦测试 4 tests OK，相关回归 24 tests OK，Python `py_compile` 退出码 0，`node --check background.js` 退出码 0，全量 `python -m unittest discover -s learning_agent\tests` 为 591 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase15_chrome_pairing_trigger-20260602_201148`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`chrome_status_printed=true`、`permission_sent_count=0`；独立 verifier 同样通过。
- 截图确认终端输出包含 `chrome_pairing_start_confirm`、`dry_run=false`、`pending_pairing_request_status=pending` 和下一步说明。
- 学习备份目录：`learning_agent/test/agent_capability_phase15_chrome_pairing_trigger_20260602/`。
- 当前状态：Phase 15 完成；下一步进入 Phase 16 session sync 真实闭环。
## 2026-06-02 Agent Capability Phase 16 Session Sync Real Closure

- 已按 TDD 新增并通过 `learning_agent/tests/test_chrome_session_sync_phase16.py`，覆盖结构化 durable command、`/chrome` last browser prompt 证据、真实终端自检命令路径。
- 已扩展 `learning_agent/browser_extension_host/bridge_server.py`：`enqueue_browser_prompt()` 仍创建 `mode=prompt`，但 payload 增加结构化 `browser_prompt`，包含 prompt、URL、title、tab_id、selected_text、source。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：`/chrome` 显示 `last_browser_prompt_id` 和 `last_browser_prompt_url`。
- 已扩展 `learning_agent/app/interactive.py`：新增 `/chrome session-sync-selftest`，模拟浏览器侧 prompt 入队并输出 `queue_command_exists=true`。
- 自动化验证：Phase 16 聚焦测试 3 tests OK，相关回归 27 tests OK，`py_compile` 退出码 0，全量 `python -m unittest discover -s learning_agent\tests` 为 594 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome session-sync-selftest`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase16_session_sync-20260602_201954`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`chrome_status_printed=true`、`permission_sent_count=0`；独立 verifier 同样通过。
- 截图确认终端输出包含 `chrome_session_sync_selftest`、`last_browser_prompt_url=https://session-sync.local/selftest`、`queue_command_exists=true`。
- 学习备份目录：`learning_agent/test/agent_capability_phase16_session_sync_20260602/`。
- 当前状态：Phase 16 完成；下一步进入 Phase 17 `/chrome` 可操作向导增强。

## 2026-06-02 Agent Capability Phase 17 Chrome Operable Guide

- 已按 TDD 扩展 `learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`，新增 `/chrome` 可操作向导测试，覆盖 `Chrome Current`、`state=registered_unpaired`、风险等级、确认 token 要求和终端单行长度。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：新增 `_chrome_current_state()`，并让 `/chrome` 输出 `Chrome Current`、更清楚的 `Chrome Guide` 和带 `risk=`/`confirm=` 的 `Chrome Actions`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase17_chrome_operable_guide.json`，验收 prompt 为 `/chrome`。
- 自动化验证：Phase 17 聚焦测试 1 test OK；Phase 14-17 相关回归 14 tests OK；`py_compile` 退出码 0；全量 `python -m unittest discover -s learning_agent\tests` 为 595 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase17_chrome_operable_guide-20260602_202526`。
- 验收结果：`result.json completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`；独立 verifier 同样通过。
- 截图确认终端输出包含 `Chrome Current`、`Chrome Guide`、`Chrome Actions`，并清楚显示 `risk=low/high/medium` 与 `confirm=no/yes`。
- 学习备份目录：`learning_agent/test/agent_capability_phase17_chrome_operable_guide_20260602/`。
- 当前状态：Phase 17 完成；下一步进入 Phase 18 真实 Chrome extension 端到端验收。

## 2026-06-02 Agent Capability Phase 18 Chrome Extension E2E

- 已按 TDD 新增 `learning_agent/tests/test_chrome_extension_e2e_matrix_phase18.py`，红灯确认 `/chrome extension-e2e-check` 初始为未知命令。
- 已扩展 `learning_agent/app/interactive.py`：新增 `/chrome extension-e2e-check`，输出 `manifest_ok`、`launcher_ok`、`pairing_completed`、`browser_prompt_queued`、`real_extension_connected`、`real_extension_e2e` 和 `e2e_level`。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：`Chrome Actions` 新增低风险无确认命令 `/chrome extension-e2e-check`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase18_chrome_extension_e2e.json`。
- 自动化验证：Phase 18 聚焦测试 2 tests OK；Phase 14-18 相关回归 22 tests OK；`py_compile` 退出码 0；`node --check background.js` 退出码 0；全量 `python -m unittest discover -s learning_agent\tests` 为 597 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome extension-e2e-check`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase18_chrome_extension_e2e-20260602_203303`。
- 验收结果：`result.json completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`；独立 verifier 同样通过。
- 截图确认终端输出包含 `manifest_ok=true`、`launcher_ok=true`、`pairing_completed=true`、`browser_prompt_queued=true`，同时明确 `real_extension_connected=false`、`real_extension_e2e=false`。
- 学习备份目录：`learning_agent/test/agent_capability_phase18_chrome_extension_e2e_20260602/`。
- 当前状态：Phase 18 完成本地协议端到端证据链和真实扩展连接边界暴露；下一步进入 Phase 19 Browser Tool Routing 强化。

## 2026-06-02 Agent Capability Phase 19 Browser Tool Routing

- 已按 TDD 新增 `learning_agent/tests/test_browser_routing_phase19.py`，覆盖 extension health 配对门禁、extension 工具支持优先、CDP fallback、visible Chromium fallback。
- 红灯已确认：初次运行 Phase 19 测试失败，暴露 `BrowserProviderHealth.available()` 不支持 metadata，以及 extension health 只看连接不看配对。
- 已扩展 `learning_agent/browser/providers/protocol.py`：`BrowserProviderHealth` 新增 `metadata`，`available()` / `unavailable()` 支持携带审计字段。
- 已升级 `learning_agent/browser/providers/chrome_extension.py`：Chrome extension provider 必须连接且完成 `extension_id/device_id/session_id` 配对后才可用，并暴露 `supported_tools`。
- 已重写并强化 `learning_agent/browser/providers/router.py`：当前 Chrome/登录态任务会先选已配对且支持工具的 extension；extension 不支持工具时优先走真实 Chrome CDP；CDP 不可用时退到隔离可见 Chromium；extension 不可用仍保留需要确认的安全门禁。
- 已更新旧测试 `learning_agent/tests/test_chrome_extension_readonly_stage5.py`：连接但未配对不可用，完成配对后才可用。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase19_browser_routing.json`。
- 自动化验证：Phase 19 聚焦测试 3 tests OK；相关 provider/extension 回归 50 tests OK；`py_compile` 退出码 0；场景 JSON 解析退出码 0。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，600 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 Phase 19 路由验收 prompt，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase19_browser_routing-20260602_204739`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，event/debug 均包含 `PHASE19_ROUTING_OK`、`extension=chrome_extension`、`cdp=real_chrome_cdp`、`visible=visible_chromium`。
- 独立 verifier 复验通过，截图 `03_final.png` 确认真实 Windows 终端内显示 Phase 19 路由成功标记。
- 学习备份目录：`learning_agent/test/agent_capability_phase19_browser_routing_20260602/`。
- 当前状态：Phase 19 完成；下一步进入 Phase 20 OS 级 Computer Use 生产化。

## 2026-06-02 Agent Capability Phase 20 OS Computer Use

- 已按 TDD 新增 `learning_agent/tests/test_os_computer_use_phase20.py`，覆盖默认真实动作关闭说明、拒绝动作审计、内存截图证据。
- 红灯已确认：初次运行 Phase 20 测试失败，暴露默认状态缺少 `real_actions_enabled`，动作结果缺少 `audit_id` 和 `evidence`。
- 已扩展 `learning_agent/computer_use/controller.py`：默认后端和内存后端都会输出真实动作启用边界、环境变量开关和平台信息。
- 已增强 `MemoryComputerUseBackend` 和 `WindowsComputerUseBackend` 的 `screenshot` 返回：结果包含 `evidence.kind=screenshot`，并明确证据边界。
- 已增强 `ComputerUseController`：新增审计日志摘要，被拒绝动作和成功动作都会记录 `audit_id`、动作、允许状态、原因、后端和安全元数据。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase20_os_computer_use.json`，验收时只做只读状态检查，不调用 `computer_action`。
- 自动化验证：Phase 20 聚焦加 Stage 17 回归 7 tests OK；正确相关回归 99 tests OK；场景 JSON 解析通过；`py_compile` 退出码 0。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，603 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 Phase 20 只读状态验收 prompt，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase20_os_computer_use-20260602_205824`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，event/debug 均包含 `PHASE20_COMPUTER_STATUS_OK`、`real_actions_enabled=false`、`opt_in_env_var=LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`、`audit_count=0`。
- 独立 verifier 复验通过，截图 `03_final.png` 确认真实 Windows 终端内显示 Phase 20 状态验收成功标记。
- 学习备份目录：`learning_agent/test/agent_capability_phase20_os_computer_use_20260602/`。
- 当前状态：Phase 20 完成；下一步进入 Phase 21 类似 `/chrome` 的终端状态 UI。

## 2026-06-02 Agent Capability Phase 21 Terminal Status UI

- 已按 TDD 新增 `learning_agent/tests/test_terminal_status_ui_phase21.py`，覆盖 `/status` 和 `/chrome` 的紧凑摘要、下一步命令、最近问题和终端单行长度。
- 红灯已确认：初次运行 Phase 21 测试失败，暴露旧 UI 缺少 `Status Summary` 和 `Chrome Summary`。
- 已扩展 `learning_agent/app/status_renderer.py`：新增 `Status Summary`，显示 connection、next 和 recent_error，让 `/status` 第一屏更可操作。
- 已扩展 `learning_agent/app/chrome_status_renderer.py`：新增 `Chrome Summary`，显示 connection、next 和 recent_issue，让 `/chrome` 第一屏更接近成熟终端状态面板。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase21_terminal_status_ui.json`，用只读渲染器命令同时验证 `/status` 和 `/chrome` 输出。
- 自动化验证：Phase 21 聚焦测试 2 tests OK；相关状态 UI 回归 26 tests OK；场景 JSON 解析通过；`py_compile` 退出码 0。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，605 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 Phase 21 状态 UI 验收 prompt，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase21_terminal_status_ui-20260602_210605`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，event/debug 均包含 `PHASE21_STATUS_UI_OK`、`status_summary=true`、`chrome_summary=true`、`next=/chrome_pairing_diagnose`、`max_line_ok=true`。
- 独立 verifier 复验通过，截图 `03_final.png` 确认真实 Windows 终端内显示 Phase 21 状态 UI 成功标记。
- 学习备份目录：`learning_agent/test/agent_capability_phase21_terminal_status_ui_20260602/`。
- 当前状态：Phase 21 完成；下一步进入 Phase 22 Long-Task Harness and Browser Task Fusion。

## 2026-06-02 Agent Capability Phase 22 Browser Harness Fusion

- 已按 TDD 新增 `learning_agent/tests/test_browser_harness_fusion_phase22.py`，覆盖浏览器 action 证据进入 harness、同 action 去重、`/status` 和 `/chrome` 暴露 harness 链接。
- 红灯已确认：初次运行 Phase 22 测试失败，暴露 `BrowserHarnessMirror` 缺少 `append_action_evidence()`。
- 已扩展 `learning_agent/browser/harness_integration.py`：新增 `append_action_evidence()`，将 `BrowserAction` 转成 verifier 友好的 `browser_action_evidence` harness event，并按 `action_id` 去重。
- 已扩展 `learning_agent/browser_automation_mcp_server.py`：真实 browser action 结束时同步 action evidence 到 harness。
- 已扩展 `learning_agent/runtime/status_snapshot.py`：`browser.runs[*].harness` 新增 `action_evidence_count` 和 `latest_action_evidence`。
- 已扩展 `learning_agent/app/status_renderer.py` 和 `learning_agent/app/chrome_status_renderer.py`：状态 UI 直接显示 `harness_run_id`、`harness_verifier_passed`、`harness_action_evidence_count`、`harness_latest_action`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase22_browser_harness_fusion.json`。
- 自动化验证：Phase 22 聚焦测试 1 test OK；相关 browser/harness/status 回归 16 tests OK；场景 JSON 解析通过；`py_compile` 退出码 0。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，606 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 Phase 22 browser harness 融合验收 prompt，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase22_browser_harness_fusion-20260602_211420`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，event/debug 均包含 `PHASE22_BROWSER_HARNESS_OK`、`harness_run_id=phase22_visible_browser_run`、`verifier_passed=true`、`action_evidence_count=1`、`dedupe_ok=true`。
- 独立 verifier 复验通过，截图 `03_final.png` 确认真实 Windows 终端内显示 Phase 22 浏览器 harness 融合成功标记。
- 学习备份目录：`learning_agent/test/agent_capability_phase22_browser_harness_fusion_20260602/`。
- 当前状态：Phase 22 完成；下一步进入 Phase 23 Final End-to-End Acceptance Matrix Upgrade。

## 2026-06-02 Agent Capability Phase 23 Final Acceptance Matrix

- 已新增最终验收矩阵 `learning_agent/acceptance_controller/final_acceptance_matrix_phase23.json`，覆盖 Phase 14-22 共 9 个阶段。
- 矩阵逐项记录每个阶段的测试模块、真实终端验收 scenario、acceptance run、学习备份目录、阶段报告和期望验收结果。
- 已新增 `learning_agent/tests/test_final_acceptance_matrix_phase23.py`，机器验证矩阵阶段完整、测试模块可导入、scenario JSON 可解析、报告/备份/run/截图存在、`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase23_final_acceptance_matrix.json`。
- 自动化验证：Phase 23 矩阵测试 1 test OK；Phase 14-23 聚焦集合 21 tests OK；矩阵和场景 JSON 解析通过；`py_compile` 退出码 0。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，607 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 Phase 23 最终矩阵验收 prompt，生成 run `learning_agent/acceptance_controller/runs/agent_capability_phase23_final_acceptance_matrix-20260602_212302`。
- 真实验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，event/debug 均包含 `PHASE23_MATRIX_OK`、`phases=9`、`first_phase=14`、`last_phase=22`、`final_acceptance_matrix_phase23.json`。
- 独立 verifier 复验通过，截图 `03_final.png` 确认真实 Windows 终端内显示 Phase 23 最终验收矩阵成功标记。
- 学习备份目录：`learning_agent/test/agent_capability_phase23_final_acceptance_matrix_20260602/`。
- 当前状态：Phase 14-23 蓝图任务全部完成。

## 2026-06-03 Phase 32 Windows OS Computer Use Native Observation Helper
状态：已完成代码修改、自动化测试、全量回归、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_native_helper_phase32.py`，红灯确认 native helper 生产入口缺失。
- 已新增 `learning_agent/computer_use/native_helper.py`，包含 `WindowsNativeWindowObservationHelper`、Win32 GDI 截图 fallback、Win32 文本 fallback 和可注入 provider 合同。
- 已修改 `learning_agent/computer_use/controller.py`，新增 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE`，只有显式 opt-in 才会在默认 Windows 后端挂载 native helper。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase32 native helper 类型。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase32_windows_native_helper.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase32_windows_native_helper_20260603.md`。
- 已按学习规则把新增/修改文件备份到 `learning_agent/test/agent_capability_phase32_windows_native_helper_20260603/`。

验证：
- Phase32 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_native_helper_phase32`，6 tests OK。
- Computer Use 相邻回归：Phase17/20/27/28/29/30/31/32 共 35 tests OK。
- 语法检查：`py_compile` 通过。
- 场景 JSON：`python -m json.tool` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，641 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase32_windows_native_helper-20260603_081430/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过，最终 marker 为 `PHASE32_WINDOWS_NATIVE_HELPER_READY PHASE32_WINDOWS_NATIVE_HELPER_OK screenshot=true raw_text_hidden=true helper=windows_native_observation helper_available=true optin_guard=true parsed=true width=222`。

下一步：
- 建议 Phase33 继续做真实 Windows.Graphics.Capture 或 UIAutomationClient 专项，而不是扩大鼠标键盘动作。
- Phase33 应优先补 native helper 权限诊断、DPI/多显示器、遮挡/最小化窗口处理，以及禁止目标二次过滤。

---

## 2026-06-03 Phase 31 Windows OS Computer Use Lock, Abort, Evidence Chain
状态：已完成代码修改、自动化测试、全量回归、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_lock_abort_phase31.py`，红灯确认缺少 `/computer` 终端入口。
- 已新增 `learning_agent/computer_use/audit.py`，用于保存 Computer Use 审计事件和动作证据链，并递归脱敏。
- 已修改 `learning_agent/computer_use/lock.py`，补 stale lock TTL、陈旧 owner 恢复状态和 UTC 时间解析修复。
- 已修改 `learning_agent/computer_use/controller.py`，让成功动作携带 `before_evidence`、`after_evidence`、`chain_path`，并把审计事件落盘。
- 已修改 `learning_agent/app/interactive.py`，新增 `/computer status`、`/computer abort <reason>`、`/computer clear-abort`、`/computer release [session_id]`。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 `ComputerUseAuditStore`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase31_windows_lock_abort_evidence.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase31_windows_lock_abort_evidence_20260603.md`。
- 已按学习规则把新增/修改文件备份到 `learning_agent/test/agent_capability_phase31_windows_lock_abort_evidence_20260603/`。

验证：
- Phase 31 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_lock_abort_phase31`，5 tests OK。
- Computer Use 相邻回归：Phase 17/20/27/28/29/30 共 24 tests OK。
- 语法检查：`py_compile` 通过。
- 场景 JSON：`python -m json.tool` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，635 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase31_windows_lock_abort_evidence-20260603_075659/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过，最终 marker 为 `PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_READY PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_OK recovered=true chain=true before=true after=true abort_blocked=true raw_text_hidden=true terminal_abort=true terminal_clear=true coord=34,48`。

下一步：
- 建议 Phase 32 继续做真实 Windows native helper 的安全只读桥接：先接 Windows.Graphics.Capture/截图和 UIAutomationClient 文本树，再考虑更窄的 SendInput 动作。
- 真实动作范围仍不能扩大到终端、Codex UI、安全设置、密码管理器、认证弹窗或 Windows Run。

---

## 2026-06-02 Agent Capability Phase 24/25 Real Chrome Extension Native E2E

- 延续 Phase 24 诊断结果，执行真实本地 Chromium extension/native messaging host 闭环验证。
- Computer Use native pipe 当前不可用，未能用桌面自动化直接操作 Google Chrome UI；已如实记录边界。
- Google Chrome stable 在当前环境忽略命令行本地扩展加载参数，因此使用本地可见 Playwright Chromium 加载 `learning_agent/chrome_extension`。
- 真实扩展 service worker 已加载：`chrome-extension://lepnefooepbnjbcnhooiccpnafalfbdk/background.js`。
- 真实扩展 id：`lepnefooepbnjbcnhooiccpnafalfbdk`。
- 已通过真实可见终端运行 `/chrome install-confirm lepnefooepbnjbcnhooiccpnafalfbdk I_UNDERSTAND_WRITE_REGISTRY`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase25_install_real_extension_native_host-20260602_222940`。
- 已确认 native host launcher 原始失败根因：Chrome 启动 `.cmd` 时缺少仓库根目录 `PYTHONPATH`，导致 `ModuleNotFoundError: No module named 'learning_agent'`。
- 已修复 `learning_agent/browser_extension_host/manifest_installer.py`，launcher 现在设置 `OPENHARNESS_LEARNING_AGENT_WORKSPACE` 和 `PYTHONPATH`。
- 已补强真实终端验收门禁：`chrome_status_printed` 事件携带 `/chrome` 输出文本，controller 和独立 verifier 均支持 `event_payload_contains`。
- 已修复 `BrowserAutomationServer` 单测隔离问题：可注入 `MemoryNativeHostRegistryAdapter`，避免真实 HKCU registry 污染临时 workspace 测试。
- 严格真实可见终端验收已通过，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase24_real_chrome_extension_e2e-20260602_224404`。
- 最新验收 result：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最新验收 payload checks 全部为 true：`real_extension_connected=true`、`paired=true`、`browser_prompt_queued=true`、`workspace_lock_ok=true`、`real_extension_e2e=true`。
- 独立 verifier 复验同一 run 通过，并显示五个 `event_payload_checks=true`。
- 自动化验证：Phase 24 测试 5 OK；acceptance verifier 测试 5 OK；Phase24+observability 14 OK；Stage13+Phase9 14 OK。
- 全量验证：`python -m unittest discover -s learning_agent\tests`，613 tests OK，skipped=1。
- 编译与静态检查：`py_compile`、两个 scenario JSON、`node --check learning_agent\chrome_extension\background.js` 均通过。
- 学习备份目录已刷新：`learning_agent/test/agent_capability_phase24_real_chrome_extension_e2e_20260602/`。
- 当前边界：验收期间是真实连接；holder 脚本退出后 bridge 可回到 `connected=false`，这是 native host EOF 的预期结果。若以后手动加载 Google Chrome stable 且扩展 id 不同，需要重新执行 `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。
- 当前状态：Phase 24 真实扩展 E2E 和 Phase 25 native host 真实连接闭环完成。
## 2026-06-03 Phase 29 Windows OS Computer Use 窗口观察证据链
状态：已完成代码修改、自动化测试、真实可见终端验收和学习备份。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_observe_phase29.py`，红灯确认缺少 `learning_agent.computer_use.evidence`。
- 已新增 `learning_agent/computer_use/evidence.py`，用于保存窗口状态 metadata、截图 artifact、过滤后的 UIA 摘要和 helper 状态。
- 已新增 `learning_agent/computer_use/helper_client.py`，提供 `WindowObservationPayload`、`StaticWindowObservationHelper` 和 `NullWindowObservationHelper`。
- 已修改 `learning_agent/computer_use/controller.py`，让 `WindowsComputerUseBackend.get_window_state` 返回 `screenshot_id`、`screenshot_path`、`evidence_path`、`accessibility_excerpt`、过滤统计和 helper 状态。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase 29 evidence/helper 类型。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase29_windows_observe_evidence.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase29_windows_observe_evidence_20260603.md`。
- 已按学习规则把新增/修改文件备份到 `learning_agent/test/agent_capability_phase29_windows_observe_evidence_20260603/`。

验证：
- Phase 29 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_observe_phase29`，3 tests OK。
- Phase 28/29 聚焦测试：8 tests OK。
- Phase 29/28/27/20 回归：15 tests OK。
- 语法检查：`py_compile` 通过。
- 场景 JSON：`python -m json.tool` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，625 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase29_windows_observe_evidence-20260603_062659/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过，最终 marker 为 `PHASE29_WINDOWS_OBSERVE_READY PHASE29_WINDOWS_OBSERVE_OK screenshot=true metadata=true width=123 filtered=1 truncated=true password_hidden=true`。
- evidence 文件检查通过：`learning_agent/memory/computer_use/evidence_phase29_acceptance/` 下生成了 metadata 和截图文件，metadata 中 `contains_password=False`。

下一步：
- 建议 Phase 30 先补 durable computer-use lock、abort flag 和 action evidence envelope。
- 不建议直接扩大真实鼠标键盘动作；应先把锁、撤销/中断、动作前后证据链做好。

---

## 2026-06-03 Phase 33 Windows OS Computer Use native provider diagnostics
状态：已完成代码修改、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已新增 `learning_agent/computer_use/native_diagnostics.py`，用于输出 Windows.Graphics.Capture、GDI fallback、UIAutomationClient、Win32 文本 fallback 的 provider 诊断。
- 已修改 `learning_agent/computer_use/native_helper.py`，让 helper 状态包含 `diagnostics`。
- 已修改 `learning_agent/computer_use/controller.py`，让 Windows 后端状态包含 `native_observation_diagnostics`。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 `WindowsNativeObservationDiagnostics`。
- 已新增 `learning_agent/tests/test_windows_computer_use_native_diagnostics_phase33.py`，按 TDD 先确认缺少 diagnostics 字段。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase33_windows_native_diagnostics.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase33_windows_native_diagnostics_20260603.md`。

当前验证：
- 红灯测试失败点正确：缺少 `diagnostics` 和 `native_observation_diagnostics`。
- 绿灯聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_native_diagnostics_phase33`，3 tests OK。
- Phase27-33 邻近回归：38 tests OK。
- `py_compile` 与 scenario JSON 检查均通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，644 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase33_windows_native_diagnostics-20260603_082834/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过，最终 marker 为 `PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_READY PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_OK phase=phase33_windows_native_diagnostics wgc_known=true uia_known=true active_capture=visible_fake_capture active_text=visible_fake_text safe=true actions_expanded=false`。
- 学习备份目录已刷新：`learning_agent/test/agent_capability_phase33_windows_native_diagnostics_20260603/`。

---

## 2026-06-03 Phase 34 Windows OS Computer Use UIAutomation text provider
状态：已完成代码修改、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已新增 `WindowsUiautomationTextProvider`，支持注入 fake/真实 `uiautomation` 模块并有界遍历控件树。
- 已新增 `FallbackNativeWindowTextProvider`，支持 UIA 失败时自动降级到 Win32 文本 fallback。
- 已修改 `WindowsNativeWindowObservationHelper` 默认文本 provider 为 UIA 优先组合 provider。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase34 provider。
- 已新增 `learning_agent/tests/test_windows_computer_use_uia_provider_phase34.py`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase34_windows_uia_text_provider.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase34_windows_uia_text_provider_20260603.md`。

当前验证：
- 红灯测试失败点正确：缺少 `FallbackNativeWindowTextProvider`。
- 绿灯聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_uia_provider_phase34`，6 tests OK。
- Phase32/33 兼容测试：9 tests OK。
- Phase34 scenario JSON 格式检查通过。
- Phase27-34 邻近回归：44 tests OK。
- `py_compile` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，650 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase34_windows_uia_text_provider-20260603_090056/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过，最终 marker 为 `PHASE34_WINDOWS_UIA_TEXT_PROVIDER_READY PHASE34_WINDOWS_UIA_TEXT_PROVIDER_OK uia=true fallback=true raw_text_hidden=true actions_expanded=false`。
- 学习备份目录已刷新：`learning_agent/test/agent_capability_phase34_windows_uia_text_provider_20260603/`。

---

## 2026-06-02 Phase 28 Windows OS Computer Use 只读窗口枚举
状态：已完成代码修改、自动化测试、真实可见终端验收和学习备份。

完成内容：
- 已按 TDD 新增 `learning_agent/tests/test_windows_computer_use_inventory_phase28.py`，先确认缺少 `windows_backend.py` 和 observe opt-in 字段两个红灯。
- 已新增 `learning_agent/computer_use/windows_backend.py`，实现静态 inventory、Win32 ctypes 只读枚举、安全标题过滤、窗口矩形归一化、app 聚合和进程路径哈希。
- 已修改 `learning_agent/computer_use/controller.py`，让 `WindowsComputerUseBackend` 支持 `list_windows`、`list_apps`、`get_active_window`、`get_window_state`。
- 已新增只读观察开关 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE`，并保持真实动作开关 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE` 独立。
- 已修改 `learning_agent/computer_use/__init__.py`，导出 Phase 28 inventory helper，方便后续 Phase 29 复用。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`。
- 已新增阶段记录 `agent_memory/agent_capability_phase28_windows_inventory_20260602.md`。
- 已按学习规则把新增/修改文件备份到 `learning_agent/test/agent_capability_phase28_windows_inventory_20260602/`。

验证：
- Phase 28 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_inventory_phase28`，5 tests OK。
- Phase 27/17/20 回归：`python -m unittest learning_agent.tests.test_windows_computer_use_inventory_phase28 learning_agent.tests.test_windows_computer_use_protocol_phase27 learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_os_computer_use_phase20`，16 tests OK。
- 语法检查：`python -m py_compile learning_agent\computer_use\windows_backend.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_windows_computer_use_inventory_phase28.py` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，622 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase28_windows_inventory-20260602_234801/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier 复验通过：最终 marker 为 `PHASE28_WINDOWS_INVENTORY_READY PHASE28_WINDOWS_INVENTORY_OK windows=1 filtered=1 apps=1 width=300 actions_blocked=true`。

下一步：
- 建议进入 Phase 29：真实截图证据 artifact 和 UI Automation 文本摘要。
- Phase 29 仍应保持只读优先，先补 evidence chain，再考虑窗口相对坐标动作。

---
## 2026-06-03 Phase 35-42 Windows Computer Use ClaudeCode alignment blueprint

- 已按用户要求把后续 Windows Computer Use 对齐任务制作成升级蓝图。
- 新增正式蓝图：`docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`。
- 新增 agent_memory 记录：`agent_memory/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603.md`。
- 新增学习备份：`learning_agent/test/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603/phase35_42_blueprint.md`。
- 已更新根 `task_plan.md`，当前 active plan 变更为 Phase 35-42。
- 本机依赖探测结果：`uiautomation=False`、`comtypes=False`、WGC Python bindings unavailable、`platform=win32`。
- 发现并记录两个工具使用错误：PowerShell 不支持 Bash heredoc，当前 `New-Item` 不支持 `-LiteralPath` 参数。
- 下一步：按 TDD 启动 Phase 35 真实安全窗口 UIA smoke harness。

---
---

## 2026-06-03 Phase 39 Windows OS Computer Use DPI And Multi-Monitor Coordinates

- Added `learning_agent/computer_use/coordinates.py` as the Phase39 coordinate model.
- Updated `learning_agent/computer_use/action_policy.py` so window-relative actions are converted through logical screen, display-relative logical, and physical screen coordinates before backend execution.
- Updated `learning_agent/computer_use/windows_backend.py` and `learning_agent/computer_use/controller.py` so window state can carry display metadata, DPI scale, and a reusable coordinate context.
- Added Phase39 focused tests and a real visible terminal acceptance scenario.
- Red test failed for the expected missing `learning_agent.computer_use.coordinates` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_coordinates_phase39`, 5 tests OK.
- Phase30-39 regression passed: 50 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 675 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase39_windows_coordinates-20260603_111521`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE39_WINDOWS_COORDINATES_READY PHASE39_WINDOWS_COORDINATES_OK dpi=true multi_monitor=true action_policy=true window_state=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase39_windows_coordinates_20260603/`.
- Current boundary: Phase39 normalizes coordinates and preserves display metadata; it does not expand the real action surface, and `actions_expanded=false` remains intentional.
---

## 2026-06-03 Phase 40 Windows OS Computer Use Abort, Cleanup, And Notifications

- Added `learning_agent/computer_use/session_runtime.py` for Phase40 session runtime semantics.
- Added durable runtime notifications for global abort and turn cleanup.
- Updated `/computer status` to include a `Computer Runtime` section with runtime model, marker, notification count, cleanup count, last notification, and `actions_expanded=false`.
- Updated `/computer abort <reason>` so it writes the durable abort flag and records a `computer_use_abort_requested` notification.
- Added `/computer cleanup [session_id]` and `/computer notifications`.
- Added Phase40 focused tests and a real visible terminal acceptance scenario.
- Red test failed for the expected missing `learning_agent.computer_use.session_runtime` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_session_runtime_phase40`, 4 tests OK.
- Phase30-40 regression passed: 54 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 679 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase40_windows_abort_cleanup-20260603_112730`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE40_WINDOWS_ABORT_CLEANUP_READY PHASE40_WINDOWS_ABORT_CLEANUP_OK abort=true cleanup=true notifications=true terminal_status=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase40_windows_abort_cleanup_20260603/`.
- Current boundary: Phase40 adds runtime safety semantics only; it does not expand real desktop actions.

---

## 2026-06-03 Phase 41 Windows OS Computer Use Image Results

状态：已完成代码实现、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已新增 Phase41 图片结果协议：`PHASE41_WINDOWS_IMAGE_RESULTS_READY`、`PHASE41_WINDOWS_IMAGE_RESULTS_OK`、`phase41_model_visible_image_results`。
- `learning_agent/computer_use/evidence.py` 现在会从截图 evidence 生成 `image_result` block，字段包括 artifact 路径、MIME、尺寸、截图 id、metadata 路径和 `sensitive_text_included=false`。
- `ComputerUseEvidenceStore.save_window_state(...)` 现在返回并保存 `image_results` 与 `image_result_count`。
- `ComputerUseActionResult.to_text(...)` 现在追加 `Computer Use Image Results` 文本区，避免模型从巨大 dict 中猜截图路径。
- `WindowsComputerUseBackend.get_window_state` 在顶层和 `state` 内同步 image result 字段。
- `LearningAgent` 在 `computer_observe` 和 `computer_action` 后把截图 artifact 登记进 `active_artifacts`，并写 `computer_use_image_result` observation。
- 已新增 `learning_agent/tests/test_windows_computer_use_image_results_phase41.py`。
- 已新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase41_windows_image_results.json`。

验证：
- 红灯：初次 Phase41 focused 测试因缺少 `PHASE41_IMAGE_RESULT_MODEL` 等 evidence 合同入口失败。
- focused：`python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41`，4 tests OK。
- 语法：Phase41 touched Python files `py_compile` 通过。
- CLI selftest：`PHASE41_WINDOWS_IMAGE_RESULTS_READY PHASE41_WINDOWS_IMAGE_RESULTS_OK artifact=true image_block=true agent_artifact=true sensitive_text_hidden=true actions_expanded=false`。
- Windows Computer Use 回归：`python -m unittest discover -s .\learning_agent\tests -p "test_windows_computer_use_*.py"`，70 tests OK。
- 全量：`python -m unittest discover -s .\learning_agent\tests`，683 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase41_windows_image_results-20260603_114516/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier：同一 run 复验通过。

边界：
- Phase41 不扩大真实桌面动作；`actions_expanded=false` 保持为验收 token。
- image_result block 不包含原始 UIA 文本，只提供本地 artifact 引用和尺寸/MIME 元数据。
- 下一步进入 Phase42 最终 Windows Computer Use E2E 矩阵。

---

## 2026-06-03 Phase 42 Windows OS Computer Use Final Matrix

状态：已完成代码实现、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

完成内容：
- 已新增 `learning_agent/computer_use/final_matrix.py`，作为 Phase35-41 安全合同总验收入口。
- 已新增最终矩阵 JSON：`learning_agent/acceptance_controller/final_acceptance_matrix_phase42_windows_computer_use.json`。
- 已新增 Phase42 focused 测试：`learning_agent/tests/test_windows_computer_use_final_matrix_phase42.py`。
- 已新增真实可见终端场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase42_windows_computer_use_final_matrix.json`。
- 已从 `learning_agent/computer_use/__init__.py` 导出 Phase42 API。
- 已更新 Phase35-42 蓝图和根 `task_plan.md`，Phase42 已勾选完成。

覆盖矩阵：
- Phase35：UIA 依赖诊断和安全窗口边界。
- Phase36：WGC provider 合同和 fallback 边界。
- Phase37：SendInput 合同、安全 fake action、真实输入默认关闭、raw text hidden。
- Phase38：approval allowlist、forbidden target、grant flags。
- Phase39：observe、coordinate context、window state。
- Phase40：abort、cleanup、notifications。
- Phase41：evidence、image block、agent active_artifacts、sensitive text hidden。

验证：
- 红灯：初次 Phase42 focused 测试因缺少 `learning_agent.computer_use.final_matrix` 失败。
- focused：`python -m unittest learning_agent.tests.test_windows_computer_use_final_matrix_phase42`，3 tests OK。
- 语法：Phase42 touched Python files `py_compile` 通过。
- CLI selftest：`PHASE42_WINDOWS_COMPUTER_USE_FINAL_READY PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK phase_count=7 matrix=true observe=true evidence=true approval=true gated_refusal=true safe_action=true abort_cleanup=true artifact_visibility=true actions_expanded=false`。
- JSON：最终矩阵和场景均通过 `python -m json.tool`。
- Windows Computer Use 回归：`python -m unittest discover -s .\learning_agent\tests -p "test_windows_computer_use_*.py"`，73 tests OK。
- 全量：`python -m unittest discover -s .\learning_agent\tests`，686 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase42_windows_computer_use_final_matrix-20260603_115600/result.json`，`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 独立 verifier：同一 run 复验通过。

边界：
- Phase42 不点击真实桌面、不移动鼠标、不向真实窗口输入文本。
- Phase42 不扩大真实桌面动作；`actions_expanded=false` 保持为最终 token。
- Phase35-42 Windows Computer Use ClaudeCode-alignment 蓝图任务已完成。
---

## 2026-06-03 Phase 43 Windows Native Capability Matrix

- Added a normalized Windows native capability matrix for Computer Use.
- Connected the matrix to `WindowsComputerUseBackend.status()` and `/computer status`.
- Added tests and acceptance scenario for Phase43.
- Verification passed: focused Phase43 tests 4 OK, Phase33/42/43 regression 10 OK, py_compile OK, CLI selftest OK.
- Boundary: diagnostics/status only; real desktop actions remain gated and not expanded.

---

## 2026-06-03 Phase 44 Windows Native Host / Helper Architecture

- Added an in-process Windows native host/client contract in `learning_agent/computer_use/native_host.py`.
- Covered `status`, `observe`, `capture`, `action`, and `cleanup` messages with deterministic tests.
- Verified that raw screenshot bytes are not included in host JSON responses.
- Verified that action messages are refused by default with `real_action_refused_by_native_host`.
- Added acceptance scenario `agent_capability_phase44_windows_native_host.json`.
- Verification passed: focused Phase44 tests 4 OK, Phase32/43/44 regression 14 OK, py_compile OK, CLI selftest OK.
- Boundary: architecture only; real OS actions are still gated and not expanded.

---

## 2026-06-03 Phase 45 Windows Screenshot Runtime

- Added `learning_agent/computer_use/screenshot_runtime.py` with WGC-first/GDI-fallback provider orchestration, evidence artifact writing, provider attempt audit, and stable Phase45 CLI tokens.
- Updated `learning_agent/computer_use/native_host.py` so injected screenshot runtimes can serve `capture` messages without returning raw bytes.
- Added `learning_agent/tests/test_windows_computer_use_screenshot_runtime_phase45.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase45_windows_screenshot_runtime.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.screenshot_runtime'`.
- Verification passed: focused Phase45 tests 4 OK; `py_compile` OK; Phase32/36/44/45 regression 19 OK; CLI self-check emitted `PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase45_windows_screenshot_runtime_20260603/`.
- Boundary: Phase45 expands screenshot runtime architecture only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 46 Windows UIA Control Tree Runtime

- Added `learning_agent/computer_use/uia_tree.py` with structured UIA tree observation, bounds, clickable/editable hints, node/depth limits, and sensitive text redaction.
- Updated `learning_agent/computer_use/native_host.py` so injected UIA tree runtimes can serve `observe` messages.
- Added `learning_agent/tests/test_windows_computer_use_uia_tree_phase46.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase46_windows_uia_tree.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.uia_tree'`.
- Verification passed: focused Phase46 tests 4 OK; `py_compile` OK; Phase34/44/45/46 regression 18 OK; CLI self-check emitted `PHASE46_WINDOWS_UIA_TREE_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase46_windows_uia_tree_20260603/`.
- Boundary: Phase46 expands read-only structured UIA observation only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 47 Windows SendInput Dispatcher

- Added `learning_agent/computer_use/sendinput_dispatcher.py` with low-level event expansion, target-before-send verification, recording sender, and Phase47 CLI tokens.
- Updated `learning_agent/computer_use/native_host.py` so injected action executors can serve `action` messages only when real actions are explicitly enabled.
- Added `learning_agent/tests/test_windows_computer_use_sendinput_dispatcher_phase47.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase47_windows_sendinput_dispatcher.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.sendinput_dispatcher'`.
- Verification passed: focused Phase47 tests 4 OK; `py_compile` OK; Phase37/44/47 regression 13 OK; CLI self-check emitted `PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase47_windows_sendinput_dispatcher_20260603/`.
- Boundary: Phase47 expands the dispatcher surface but still relies on upstream opt-in, allowlist, lock, abort, approval, target verification, and evidence before real desktop use.

---

## 2026-06-03 Phase 48 Windows Security Policy

- Added `learning_agent/computer_use/security_policy.py` with observe/action/system_key/clipboard grant classes, high-risk default refusal, readable refusal text, and Phase48 CLI tokens.
- Updated `learning_agent/computer_use/approval.py` to accept an optional injected Phase48 policy while leaving the default Phase38 behavior compatible.
- Updated `/computer status` so the real terminal status panel shows `security_policy=phase48_windows_security_policy` and the stable grant class list.
- Added `learning_agent/tests/test_windows_computer_use_security_policy_phase48.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase48_windows_security_policy.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.security_policy'`.
- Verification passed: focused Phase48 tests 4 OK; Phase38/48 regression 10 OK; `py_compile` OK; CLI self-check emitted `PHASE48_WINDOWS_SECURITY_POLICY_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase48_windows_security_policy_20260603/`.
- Boundary: Phase48 upgrades policy clarity and status visibility only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 49 Computer Use Tool Surface Compatibility

- Added `learning_agent/computer_use/tool_surface.py` with stable compatibility contract `phase49_computer_use_compat_tool_surface`.
- Updated `learning_agent/tools/schemas.py`, `learning_agent/tools/catalog.py`, `learning_agent/tools/executor.py`, and `learning_agent/core/agent.py` so `computer_use` and `computer-use` are visible, high-risk, package-gated, and routed through the same existing controller chain.
- Added `learning_agent/tests/test_windows_computer_use_tool_surface_phase49.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase49_windows_tool_surface.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.tool_surface'`.
- Verification passed: focused Phase49 tests 4 OK; Phase27/48/49 regression 12 OK; `py_compile` OK; CLI self-check emitted `PHASE49_COMPUTER_USE_TOOL_SURFACE_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase49_windows_tool_surface_20260603/`.
- Boundary: Phase49 adds compatibility aliases only; it does not expand real desktop action capability.

---

## 2026-06-03 Phase 50 Windows Recovery Runtime

- Upgraded `WindowsComputerUseSessionRuntime` with Phase50 recovery model `phase50_windows_recovery_runtime`.
- Added explicit stale lock recovery, cleanup abort clearing, and action journal replay against the existing audit store.
- Updated `/computer recover`, `/computer journal`, and `/computer cleanup` terminal output.
- Added `learning_agent/tests/test_windows_computer_use_recovery_phase50.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase50_windows_recovery_runtime.json`.
- TDD red confirmed first: `ImportError: cannot import name 'PHASE50_WINDOWS_RECOVERY_MARKER'`.
- Verification passed: focused Phase50 tests 5 OK; Phase31/40/50 regression 14 OK; `py_compile` OK; CLI self-check emitted `PHASE50_WINDOWS_RECOVERY_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase50_windows_recovery_runtime_20260603/`.
- Boundary: Phase50 improves recovery and observability only; it does not expand real desktop action capability.

---

## 2026-06-03 Phase 51 Computer Status UI

- Added compact `/computer` status renderer with `Computer Summary`, `next=/computer observe`, recent action, grant state, runtime, native capability, and command list.
- Added terminal grant/revoke draft store with explicit `terminal_ui_only` scope.
- Updated `/computer status`, `/computer observe`, `/computer grant`, and `/computer revoke` in `learning_agent/app/interactive.py`.
- Added `learning_agent/tests/test_windows_computer_use_terminal_ui_phase51.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase51_computer_status_ui.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.app.computer_status_renderer'`.
- Verification passed: focused Phase51 tests 4 OK; Phase21/38/48/50/51 regression 21 OK; `py_compile` OK; CLI self-check emitted `PHASE51_COMPUTER_STATUS_UI_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase51_computer_status_ui_20260603/`.
- Boundary: Phase51 improves terminal visibility only; terminal grant state is not a bypass for controller approval.

---

## 2026-06-03 Phase 52 Windows Production Matrix

- Added `learning_agent/computer_use/production_matrix.py` as the Phase43-51 production aggregate contract.
- Added focused Phase52 tests and visible-terminal scenario `agent_capability_phase52_windows_production_matrix.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.production_matrix'`.
- Fixed a Phase43/Phase51 compatibility regression in `learning_agent/app/computer_status_renderer.py`: `/computer status` now keeps `Computer Native Capability Matrix`, the Phase43 marker, and `windows_sendinput` visible while preserving the compact Phase51 panel.
- Verification passed: Phase52 focused tests 2 OK; Phase43-52 regression 39 OK; `py_compile` OK; CLI self-check emitted `PHASE52_WINDOWS_PRODUCTION_MATRIX_OK phase_count=9 native_capability=true native_host=true screenshot_runtime=true uia_tree=true sendinput_dispatcher=true security_policy=true tool_surface=true recovery_runtime=true status_ui=true dispatcher_actions_expanded=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase52_windows_production_matrix_20260603/`.
- Visible terminal launch attempt made with `learning_agent/start_oauth_agent.bat`; process check showed `cmd`/`powershell`/`WindowsTerminal` processes present.
- Real visible terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/result.json` recorded `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, and all Phase52 answer/log token checks passed.
