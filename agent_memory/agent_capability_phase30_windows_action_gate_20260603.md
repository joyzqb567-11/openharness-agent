# Phase 30 Windows OS Computer Use Safe Action Gate

## 目标

- 在继续扩大真实 Windows OS Computer Use 动作前，先补齐 durable lock、abort flag、窗口相对坐标转换、敏感文本脱敏和 action evidence envelope。
- 本阶段不扩大真实鼠标键盘范围，不声明真实 SendInput、Windows.Graphics.Capture 或 UIAutomationClient native helper 已完成。

## 已完成

- 新增 `learning_agent/computer_use/lock.py`：提供 durable desktop control lock、owner session、release、abort request、abort clear 和 status。
- 新增 `learning_agent/computer_use/action_policy.py`：提供窗口相对坐标转换、文本脱敏短哈希、目标窗口摘要和 action evidence envelope。
- 修改 `learning_agent/computer_use/controller.py`：注入锁管理器时要求当前 session 持锁；abort flag 在后端执行前拦截；动作结果携带 `action_evidence`；生产默认 controller 可自动获取无人持有的当前 session 锁。
- 修改 `MemoryComputerUseBackend`：动作日志保存脱敏参数，避免保存原始 `type_text` 文本。
- 修改 `LearningAgent._computer_action()`：权限提示和拒绝观察记录使用脱敏摘要。
- 修改 `learning_agent/tools/schemas.py`：说明提供 `window` 时 x/y 是窗口相对坐标。
- 新增 `learning_agent/tests/test_windows_computer_use_actions_phase30.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase30_windows_action_gate.json`。
- 学习备份：`learning_agent/test/agent_capability_phase30_windows_action_gate_20260603/`。

## 验证

- 红灯：`python -m unittest learning_agent.tests.test_windows_computer_use_actions_phase30` 首次失败于 `ModuleNotFoundError: No module named 'learning_agent.computer_use.lock'`。
- 聚焦测试：Phase 30 5 tests OK。
- 邻近回归：Phase 17/20/27/28/29 共 24 tests OK。
- 语法和配置：`py_compile` OK，Phase 30 scenario JSON OK。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，630 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase30_windows_action_gate-20260603_065937/result.json`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE30_WINDOWS_ACTION_GATE_READY PHASE30_WINDOWS_ACTION_GATE_OK no_lock_blocked=true coord=15,27 abort_blocked=true raw_text_hidden=true evidence=true`。

## 边界

- Phase 30 使用安全内存后端和临时锁目录完成验收，不触碰真实桌面鼠标键盘。
- 真实动作前仍需要 Phase 31+ 补动作前后截图/状态 evidence chain、锁 TTL/stale owner 恢复、abort 的用户入口、native helper、DPI/多显示器/窗口遮挡处理。
- 终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run 仍是禁止自动化目标。
