# Phase36 Windows.Graphics.Capture Provider Contract 记录

更新时间：2026-06-03

## 本阶段目标

Phase36 的目标不是安装 WGC 依赖，也不是直接声明本机 WGC 截图已跑通，而是先建立可测试、可诊断、可回退的 Windows.Graphics.Capture provider 合同：

- provider 名称固定为 `windows_graphics_capture`。
- 合同版本固定为 `phase36_windows_graphics_capture_provider`。
- 默认诚实报告 `winrt.windows.graphics.capture` / `winsdk.windows.graphics.capture` 依赖状态。
- 当前缺少依赖或真实实现时返回 `fallback_required=true`。
- 不扩大鼠标、键盘、窗口动作。
- 不用 fake screenshot 冒充真实 WGC。

## 已实现内容

- 新增 `learning_agent/computer_use/wgc_capture.py`。
- 新增 `WindowsGraphicsCaptureProvider`。
- 新增 `phase36_dependency_status()`。
- 新增 `run_phase36_wgc_provider_contract()` 和 CLI token 输出。
- 修改 `learning_agent/computer_use/native_diagnostics.py`，让 WGC 诊断项来自 Phase36 provider 合同。
- 修改 `learning_agent/computer_use/__init__.py`，导出 Phase36 API。
- 新增测试 `learning_agent/tests/test_windows_computer_use_wgc_provider_phase36.py`。
- 新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase36_windows_wgc_provider.json`。

## 当前环境事实

当前环境没有可发现的 WGC Python 绑定，因此 Phase36 输出：

- `dependency_reported=true`
- `dependency_available=false`
- `capture_contract_ready=true`
- `fallback_required=true`
- `actions_expanded=false`

这是本阶段的正确诚实结果。

## 后续建议

- Phase37 继续补 SendInput executor，但必须继续受 lock、abort、target window、approval 和 evidence gate 约束。
- 若未来要让 WGC 真正截图，需要用户明确确认安装/接入 Windows helper，不应由当前阶段自动安装依赖。
