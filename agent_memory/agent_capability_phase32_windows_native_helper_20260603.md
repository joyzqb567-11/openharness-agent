# Phase 32 Windows OS Computer Use Native Observation Helper

## 目标

- 在 Phase31 的 lock/abort/evidence chain 之上，补一个只读 Windows native observation helper 桥接层。
- 本阶段只接截图/窗口文本观察，不扩大真实鼠标键盘动作范围。
- native helper 必须独立 opt-in，不能因为用户只开启窗口 inventory 就自动读取屏幕内容。

## 已完成

- 新增 `learning_agent/computer_use/native_helper.py`。
- 新增 `NativeWindowCaptureResult`、`NativeWindowTextResult` 和 `WindowsNativeWindowObservationHelper`。
- 新增 `Win32GdiWindowCaptureProvider`，在真实 Windows 上尝试使用 Win32 GDI `PrintWindow` / `BitBlt` 只读截图，返回 BMP artifact。
- 新增 `Win32WindowTextProvider`，在真实 Windows 上读取窗口标题和子控件文本作为 Phase32 fallback 文本摘要。
- 新增 `parse_hwnd_from_window()`，把 Phase28 标准 `window_id="hwnd:<id>"` 转成 Win32 hwnd。
- 修改 `learning_agent/computer_use/controller.py`，新增 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE` opt-in；只有显式设置该环境变量时，默认 Windows 后端才注入 native helper。
- 修改 `learning_agent/computer_use/__init__.py`，对外导出 Phase32 native helper 类型。
- 新增 `learning_agent/tests/test_windows_computer_use_native_helper_phase32.py`。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase32_windows_native_helper.json`。

## 最终验证

- 红灯：Phase32 首次失败于 `ImportError: cannot import name 'COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR'`，证明 native helper 生产入口缺失。
- 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_native_helper_phase32`，6 tests OK。
- 相邻回归：Phase17/20/27/28/29/30/31/32 Computer Use 相关 35 tests OK。
- 语法检查：`python -m py_compile learning_agent\computer_use\native_helper.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\tests\test_windows_computer_use_native_helper_phase32.py` 通过。
- 场景 JSON：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase32_windows_native_helper.json` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，641 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase32_windows_native_helper-20260603_081430/result.json`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE32_WINDOWS_NATIVE_HELPER_READY PHASE32_WINDOWS_NATIVE_HELPER_OK screenshot=true raw_text_hidden=true helper=windows_native_observation helper_available=true optin_guard=true parsed=true width=222`。
- 学习备份：`learning_agent/test/agent_capability_phase32_windows_native_helper_20260603/`。

## 安全边界

- Phase32 验收和测试使用 fake native provider，不读取真实桌面。
- 真实 Windows provider 只在用户显式设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE=1` 后才进入默认后端。
- 只开 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE=1` 仍只启用窗口 inventory，不读取截图或文本。
- `Win32WindowTextProvider` 是 Win32 标题/子控件文本 fallback，不是完整 UIAutomationClient 文本树。
- `Win32GdiWindowCaptureProvider` 是 GDI fallback，不是完整 Windows.Graphics.Capture 管线。
- 终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run 仍是禁止自动化目标。
