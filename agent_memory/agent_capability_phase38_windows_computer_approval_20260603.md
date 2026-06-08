# Phase 38 Windows ComputerUseApproval Model

## Status

Phase38 已完成代码实现、自动化测试、全量回归、学习备份、真实可见终端验收和独立 verifier 复核。

## What Changed

- 新增 `learning_agent/computer_use/approval.py`，提供 Windows Computer Use 会话审批模型、app allowlist、grant flags、禁止目标分类、CLI 合同自检和稳定验收 token。
- 修改 `learning_agent/computer_use/controller.py`，增加可注入 `approval_model`，在后端执行前拦截未授权 app、禁止目标和缺失危险 grant flag 的动作。
- 修改 `learning_agent/app/interactive.py`，让 `/computer status` 输出 `Computer Use Approval` 摘要，显示 approval 模型、授权 app 数、grant flags 和 `actions_expanded=false`。
- 修改 `learning_agent/computer_use/__init__.py`，导出 Phase38 approval API。
- 新增 `learning_agent/tests/test_windows_computer_use_approval_phase38.py`，覆盖 forbidden target、session grant、grant flags、controller 接入、CLI/场景 token、终端状态可见性。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase38_windows_computer_approval.json`。

## Verification

- TDD red: `python -m unittest learning_agent.tests.test_windows_computer_use_approval_phase38` 首次失败于 `ModuleNotFoundError: No module named 'learning_agent.computer_use.approval'`。
- Focused tests: `python -m unittest learning_agent.tests.test_windows_computer_use_approval_phase38`，6 tests OK。
- Syntax: `python -m py_compile learning_agent\computer_use\approval.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\app\interactive.py learning_agent\tests\test_windows_computer_use_approval_phase38.py` 通过。
- Scenario JSON: `python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase38_windows_computer_approval.json` 通过。
- CLI self-check: `PHASE38_WINDOWS_COMPUTER_APPROVAL_OK allowlist=true forbidden_blocked=true grant_flags=true terminal_status=true actions_expanded=false marker=PHASE38_WINDOWS_COMPUTER_APPROVAL_READY`。
- Neighbor regression: Phase30-38 共 45 tests OK。
- Full regression: `python -m unittest discover -s learning_agent\tests`，670 tests OK，skipped=1。
- Real visible terminal acceptance: `learning_agent/acceptance_controller/runs/agent_capability_phase38_windows_computer_approval-20260603_105641`，controller completed true。
- Independent verifier: completed true, assertion.passed true, permission_sent_count 0, all Phase38 token checks true。

## Proven

- 安全 app 可以通过 session grant 被允许，动作结果携带 `grant_id`。
- PowerShell/terminal 这类高风险窗口会被 `denied_forbidden_target` 拦截，且不会进入后端动作执行。
- `ctrl+alt+delete` 这类系统组合键在 `systemKeyCombos=false` 时被 `missing_grant_flags` 拒绝，显式授权后才允许。
- `/computer status` 可以在真实终端展示 Phase38 approval 摘要。
- Phase38 没有扩大真实动作面，验收 token 明确为 `actions_expanded=false`。

## Not Proven

- Phase38 不是图形化审批弹窗，只是终端安全状态和可注入审批模型。
- Phase38 不证明真实 `ctypes.SendInput`、真实 UIA、真实 WGC 已经成熟。
- Phase38 不允许自动化终端、Codex UI、安全设置、密码管理器、认证弹窗、验证码/OTP 或 Windows Run。

## Next

进入 Phase39：DPI、多显示器、逻辑/物理/窗口相对/显示器相对坐标模型。
