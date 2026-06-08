# Phase 28 Windows OS Computer Use Read-Only Inventory

## Goal

在不扩大真实鼠标键盘动作的前提下，为 Windows OS Computer Use 增加只读 app/window inventory：能列出安全窗口、按 app 分组、读取窗口几何状态，并清楚说明 native helper 仍未接入。

## Completed

- 新增 `learning_agent/computer_use/windows_backend.py`。
- 新增 `StaticWindowsWindowInventory`，用于测试和真实终端验收中的安全静态窗口数据。
- 新增 `WindowsWindowInventoryProbe`，使用 Win32 ctypes 做可选真实顶层窗口枚举。
- 新增窗口归一化和过滤：
  - 空标题窗口被过滤。
  - 终端、Codex、安全/密码/认证相关标题被过滤。
  - 返回 `filtered_count` 解释过滤数量。
- `WindowsComputerUseBackend` 支持注入 inventory，并区分：
  - `real_actions_enabled=True`：动作开关模式。
  - `real_actions_enabled=False`：只读 inventory 模式。
- 新增 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE` 只读观察环境变量。
- 默认 unavailable 状态现在同时提示动作开关和只读观察开关。
- `get_window_state` 返回窗口几何和 Phase 29 UIA/screenshot 占位字段。
- 高风险动作在只读 Windows 后端中会被拒绝，不会移动鼠标或点击。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`。

## Verification

- Red test observed:
  - `learning_agent.computer_use.windows_backend` 不存在。
  - 默认状态没有 `observe_opt_in_env_var`。
- Focused green:
  - `python -m unittest learning_agent.tests.test_windows_computer_use_inventory_phase28`
  - Result: 5 tests OK.
- Regression:
  - `python -m unittest learning_agent.tests.test_windows_computer_use_inventory_phase28 learning_agent.tests.test_windows_computer_use_protocol_phase27 learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_os_computer_use_phase20`
  - Result: 16 tests OK.
- Syntax:
  - `python -m py_compile learning_agent\computer_use\windows_backend.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_windows_computer_use_inventory_phase28.py`
  - Result: OK.
- Full regression:
  - `python -m unittest discover -s learning_agent\tests`
  - Result: 622 tests OK, skipped=1.
- Real visible terminal acceptance:
  - Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`
  - Run: `learning_agent/acceptance_controller/runs/agent_capability_phase28_windows_inventory-20260602_234801`
  - Result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
  - Marker: `PHASE28_WINDOWS_INVENTORY_READY PHASE28_WINDOWS_INVENTORY_OK windows=1 filtered=1 apps=1 width=300 actions_blocked=true`.
- Independent verifier:
  - `python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\agent_capability_phase28_windows_inventory-20260602_234801 .\learning_agent\acceptance_controller\scenarios\agent_capability_phase28_windows_inventory.json`
  - Result: `completed=true`, `assertion.passed=true`.

## Boundary

Phase 28 does not save real screenshots and does not extract UI Automation text trees. It returns geometry and explicit placeholders so Phase 29 can add screenshot evidence and bounded UIA summaries without changing the public contract.

## Recommended Next Phase

Phase 29 should implement evidence artifacts:

- Save window observation artifacts under `learning_agent/memory/computer_use/evidence/`.
- Add screenshot evidence metadata without dumping large images into tool text.
- Add bounded UI Automation excerpts.
- Keep write actions unchanged until evidence quality is proven.
