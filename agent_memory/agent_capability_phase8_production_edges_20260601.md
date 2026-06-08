# Agent Capability Phase 8 Production Edges

## Goal

继续推进 ClaudeCode 浏览器能力差距收敛，不重复 Phase 1-7，而是补三个生产边缘缺口：

- native host manifest 指向可执行 launcher，而不是裸 Python 脚本。
- `/chrome` 不只是只读状态页，还要显示安全管理动作入口。
- Computer Use 默认安全关闭，但提供显式启用 Windows 后端的工厂入口。

## Success Criteria

- [x] `build_native_host_manifest(...)` 会生成 `.cmd` launcher，并把 manifest `path` 指向该 launcher。
- [x] `ChromeNativeHostInstaller.status()` 暴露 `registry_targets`，覆盖 Chrome、Edge、Brave、Chromium。
- [x] `/chrome` 输出包含 `Chrome Actions`、`/chrome install-preview`、`/chrome repair`、`/chrome uninstall-preview`。
- [x] `build_default_computer_use_backend(environ={})` 默认返回 `UnavailableComputerUseBackend`。
- [x] 只有显式设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE` 且平台为 Windows 时，才返回 `WindowsComputerUseBackend`。

## Verification

- `python -m unittest learning_agent.tests.test_agent_capability_phase8_production_edges`
  - Result: `Ran 3 tests ... OK`
- `python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_agent_capability_phase8_production_edges`
  - Result: `Ran 13 tests ... OK`
- `python -m py_compile learning_agent\browser_extension_host\manifest_installer.py learning_agent\app\chrome_status_renderer.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_agent_capability_phase8_production_edges.py`
  - Result: exit code `0`
- `python -m unittest discover -s learning_agent\tests`
  - Result: `Ran 571 tests ... OK (skipped=1)`
- `python -m py_compile learning_agent\browser_extension_host\manifest_installer.py learning_agent\app\chrome_status_renderer.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_agent_capability_phase8_production_edges.py learning_agent\tests\test_chrome_extension_readonly_stage5.py`
  - Result: exit code `0`

## Compatibility Update

- Updated `learning_agent/tests/test_chrome_extension_readonly_stage5.py` because its old assertion required manifest `path` to end with `native_host.py`.
- Phase 8 intentionally changes the production contract: manifest `path` now points to `.cmd` launcher, while the real script remains visible in `metadata.host_script`.

## Real Visible Terminal Acceptance

- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase8_chrome_actions.json`
- Controller run: `learning_agent/acceptance_controller/runs/agent_capability_phase8_chrome_actions-20260601_223016`
- Controller result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`
- Independent verifier: `completed=true`, `assertion.passed=true`
- Visual observation: final screenshot shows `/chrome` output with `Chrome Actions`, `/chrome install-preview`, `/chrome repair`, and `/chrome uninstall-preview`.
