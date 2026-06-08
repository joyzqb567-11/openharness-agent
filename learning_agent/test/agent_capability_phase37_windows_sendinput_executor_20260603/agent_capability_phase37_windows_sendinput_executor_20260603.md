# Phase 37 Windows SendInput Action Executor

## 目标

把 `learning_agent` 的 Windows Computer Use 写动作层从旧的 `SetCursorPos + mouse_event` 占位路径推进到 Phase37 SendInput 执行器合同，并保持 Phase30/31 已建立的确认、可信窗口、持锁、abort、证据链和脱敏门禁。

## 已完成

- 新增 `learning_agent/computer_use/sendinput_executor.py`。
- 新增 `WindowsSendInputExecutor` 和 `WindowsSendInputActionResult`。
- 新增稳定验收标记 `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY` 和 `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK`。
- 支持合同动作：`click`、`double_click`、`move_mouse`、`press_key`、`type_text`、`scroll`。
- 默认 `real_input_enabled=false`，只有 Windows 平台、显式启用、并注入底层实现时才允许执行。
- `type_text` 不把原始文本写入可见事件、结果、dispatch 摘要或验收输出，只保留 `text_length`、`text_sha256_16`、`text_redacted=true`。
- 修改 `learning_agent/computer_use/controller.py`，让 `WindowsComputerUseBackend` 可注入 `action_executor`，真实写动作统一路由到 SendInput 执行器合同。
- 保留 `screenshot` 的旧屏幕尺寸占位读取，未把它混入鼠标键盘动作执行器。
- 修改 `learning_agent/computer_use/__init__.py`，导出 Phase37 API。
- 新增 `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase37_windows_sendinput_executor.json`。

## 已验证

- TDD 红灯已确认：首次运行 Phase37 测试因 `ModuleNotFoundError: No module named 'learning_agent.computer_use.sendinput_executor'` 失败。
- Phase37 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_sendinput_phase37`，5 tests OK。
- 编译检查：`python -m py_compile learning_agent\computer_use\sendinput_executor.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_windows_computer_use_sendinput_phase37.py` 通过。
- 场景 JSON 校验通过，success marker 为 `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY`。
- Phase37 CLI 自检通过，输出 `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK contract_ready=true real_input_default=false fake_impl_exercised=true raw_text_hidden=true actions_expanded=false marker=PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY`。
- 相邻 Computer Use 回归通过：Phase30-37 共 39 tests OK。
- 学习备份已完成：`learning_agent/test/agent_capability_phase37_windows_sendinput_executor_20260603/`。
- 全量回归通过：`python -m unittest discover -s learning_agent\tests`，664 tests OK，skipped=1。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase37_windows_sendinput_executor-20260603_104221/result.json`。
- 独立 verifier 通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK contract_ready=true real_input_default=false fake_impl_exercised=true raw_text_hidden=true actions_expanded=false`。

## 边界

- Phase37 证明的是 SendInput 执行器合同和后端路由，不证明本机已经完成真实底层 `ctypes.SendInput` 实现。
- 单元测试和验收只使用 fake/injected implementation，不移动鼠标、不点击真实桌面、不向真实窗口输入文本。
- 当前真实动作默认仍不会执行，因为默认没有注入底层 SendInput implementation。
- 任何未来真实实现仍必须经过 Phase30/31 的 confirm、trusted window、lock、abort、before/after evidence 和敏感目标过滤。

## 下一步

进入 Phase38：补 Windows ComputerUseApproval 模型，把 ClaudeCode 风格的 session grant、app/window allowlist、终端安全状态提示和拒绝原因接到现有 controller/interactive 链路中。
