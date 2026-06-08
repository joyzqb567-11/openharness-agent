# Phase 54 Windows Native Reality Gate

日期：2026-06-03

## 目标

- 建立 Windows 原生依赖和权限的诚实门禁。
- 输出 `native_dependency_report.json`，明确哪些能力 ready、missing 或 blocked。
- 不安装依赖、不改注册表、不修改 Windows 设置。

## 完成内容

- 新增 `learning_agent/computer_use/native_reality_gate.py`。
- 新增 `/computer native-gate` 终端命令。
- 新增测试 `learning_agent/tests/test_windows_computer_use_native_reality_gate_phase54.py`。
- 新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase54_native_reality_gate.json`。

## 当前机器事实

- `dependency_count=9`。
- `uiautomation` 缺失。
- `comtypes` 缺失。
- `windows_graphics_capture_binding` 缺失。
- `win32_gdi_capture_api` 可用，但只能作为 fallback。
- `windows_sendinput_api` 可用，但真实输入仍未启用，仍需要 opt-in、allowlist、target guard 和审批。
- 没有执行依赖安装，没有修改系统设置。

## 验证

- TDD 红灯：`ModuleNotFoundError: No module named 'learning_agent.computer_use.native_reality_gate'`。
- 单元测试：`python -m unittest learning_agent.tests.test_windows_computer_use_native_reality_gate_phase54` 通过。
- 邻近回归：Phase53 和 Phase52 测试通过。
- 编译：`python -m py_compile` 覆盖新增和修改文件，通过。
- JSON：`python -m json.tool learning_agent/acceptance_controller/scenarios/agent_capability_phase54_native_reality_gate.json` 通过。
- CLI：`python -m learning_agent.computer_use.native_reality_gate` 输出 `PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK`。
- 真实可见终端：`learning_agent/acceptance_controller/controller.ps1` 场景通过，证据在 `learning_agent/acceptance_controller/runs/agent_capability_phase54_native_reality_gate-20260603_164301/result.json`。

## 边界

- Phase54 只读，不点击、不移动鼠标、不扩大真实桌面动作面。
- 缺失依赖不会被 fake provider 伪装为真实可用。
- 后续若要安装 `uiautomation`、`comtypes` 或 WGC 绑定，需要用户单独确认。
