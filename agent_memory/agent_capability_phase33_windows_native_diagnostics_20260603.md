# Phase 33 Windows OS Computer Use Native Diagnostics

日期：2026-06-03

状态：已完成代码修改、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

## 目标

Phase33 的目标是在 Phase32 只读 native helper 基础上，补齐 Windows native observation 的能力诊断层，让 agent 能清楚回答：

- 当前截图 provider 是谁。
- 当前文本 provider 是谁。
- Windows.Graphics.Capture 是否被纳入首选路线。
- UIAutomationClient 是否被纳入首选路线。
- 当前为什么仍使用 GDI/Win32 fallback。
- 是否扩大了真实鼠标键盘动作能力。
- 启用 native 观察需要哪个 opt-in 开关。

## 已完成改动

- 新增 `learning_agent/computer_use/native_diagnostics.py`。
- 修改 `learning_agent/computer_use/native_helper.py`，让 `WindowsNativeWindowObservationHelper.status()` 返回 `diagnostics`。
- 修改 `learning_agent/computer_use/controller.py`，让 `WindowsComputerUseBackend.status()` 返回 `native_observation_diagnostics`。
- 修改 `learning_agent/computer_use/__init__.py`，导出 `WindowsNativeObservationDiagnostics`。
- 新增 `learning_agent/tests/test_windows_computer_use_native_diagnostics_phase33.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase33_windows_native_diagnostics.json`。
- 新增书面计划 `docs/superpowers/plans/2026-06-03-phase33-windows-native-diagnostics.md`。

## 当前边界

- Phase33 仍是只读诊断增强。
- Phase33 没有扩大真实鼠标、键盘、点击、拖拽或窗口控制动作。
- Phase33 没有声称完整 Windows.Graphics.Capture 已接管截图。
- Phase33 没有声称完整 UIAutomationClient 控件树已接管文本读取。
- 当前 WGC/UIA 是明确进入 provider roadmap 和状态诊断的首选能力；实际观察仍由 Phase32 的 GDI/Win32 fallback 或注入 provider 完成。

## 已完成验证

- 红灯测试已确认生产代码缺少 `diagnostics` 和 `native_observation_diagnostics`。
- 实现后聚焦测试已通过：`python -m unittest learning_agent.tests.test_windows_computer_use_native_diagnostics_phase33`，3 tests OK。
- Phase27-33 邻近回归已通过：38 tests OK。
- `py_compile` 已通过。
- 场景 JSON 格式检查已通过。
- 全量回归已通过：`python -m unittest discover -s learning_agent\tests`，644 tests OK，skipped=1。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/agent_capability_phase33_windows_native_diagnostics-20260603_082834/result.json`。
- 独立 verifier 复验已通过：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 最终 marker：`PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_READY PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_OK phase=phase33_windows_native_diagnostics wgc_known=true uia_known=true active_capture=visible_fake_capture active_text=visible_fake_text safe=true actions_expanded=false`。

## 学习备份

- 备份目录：`learning_agent/test/agent_capability_phase33_windows_native_diagnostics_20260603/`。
