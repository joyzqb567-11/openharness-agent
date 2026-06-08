# Phase 27 Windows OS Computer Use Protocol

## Goal

把 Phase 20 的松散 `computer_action` 安全壳升级为 Windows OS Computer Use 的 typed 协议层：先有只读 `computer_observe`，再让高风险 `computer_action` 能绑定可信窗口目标。

## Completed

- 新增 `learning_agent/computer_use/models.py`，定义 `ComputerUseWindowRef`、窗口文本清理、窗口引用构造和窗口身份键。
- 扩展 `learning_agent/computer_use/controller.py`：
  - 新增 `OBSERVE_ACTIONS` 和 `observe()`。
  - 内存后端支持 `list_apps`、`list_windows`、`get_active_window`、`get_window_state`。
  - 动作参数如果带 `window`，会先验证窗口是否来自可信目录。
  - 旧的无 `window` confirmed 动作保持兼容。
- 新增 `computer_observe` 工具 schema，并归入 `computer_use` capability pack。
- `computer_observe` 在 catalog 中是低风险、只读、并发安全。
- executor 和 `LearningAgent` 已能真实分发 `computer_observe`。
- `computer_action` schema 新增可选 `window` 目标。
- 修复 acceptance controller 对缺省 `event_payload_contains` 的 null 断言项崩溃。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase27_windows_computer_use_protocol.json`。

## Verification

- Red test observed:
  - `computer_observe` schema/catalog 缺失。
  - `MemoryComputerUseBackend(windows=...)` 不存在。
  - `ComputerUseController.observe()` 不存在。
- Focused green:
  - `python -m unittest learning_agent.tests.test_windows_computer_use_protocol_phase27`
  - Result: 4 tests OK.
- Regression:
  - `python -m unittest learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_os_computer_use_phase20`
  - Result: 7 tests OK.
- Syntax:
  - `python -m py_compile learning_agent\computer_use\models.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tools\schemas.py learning_agent\tools\catalog.py learning_agent\tools\executor.py learning_agent\core\agent.py learning_agent\tests\test_windows_computer_use_protocol_phase27.py`
  - Result: OK.
- Full regression:
  - `python -m unittest discover -s learning_agent\tests`
  - Result: 617 tests OK, skipped=1.
- Real visible terminal acceptance:
  - Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase27_windows_computer_use_protocol.json`
  - Run: `learning_agent/acceptance_controller/runs/agent_capability_phase27_windows_computer_use_protocol-20260602_233224`
  - Result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
  - Marker: `PHASE27_COMPUTER_PROTOCOL_READY PHASE27_COMPUTER_PROTOCOL_OK observe=true reject_unknown=true backend_actions=0`.

## Boundary

Phase 27 does not implement real Windows window enumeration, real screenshot capture, UI Automation text tree extraction, or new SendInput actions. Those belong to Phase 28+.

## Recommended Next Phase

Phase 28 should implement read-only Windows window inventory and observation:

- Enumerate visible top-level windows.
- Return stable `app_id/window_id/title_preview`.
- Capture window-relative screenshot metadata.
- Add first UI Automation text summary.
- Keep all write actions unchanged until read-only observation is proven in real terminal acceptance.
