# Phase 34 Windows OS Computer Use UIAutomation Text Provider

日期：2026-06-03

状态：已完成代码修改、自动化测试、真实可见终端验收、独立 verifier 复验和学习备份。

## 目标

Phase34 的目标是在 Phase33 provider diagnostics 基础上，接入一个可选的 UIAutomationClient 文本树 provider，让 Windows Computer Use 只读观察能优先读取控件树文本，缺依赖或读取失败时自动降级到 Win32 标题/子控件文本 fallback。

## 已完成改动

- 修改 `learning_agent/computer_use/native_helper.py`，新增 `WindowsUiautomationTextProvider`。
- 修改 `learning_agent/computer_use/native_helper.py`，新增 `FallbackNativeWindowTextProvider`。
- 修改 `WindowsNativeWindowObservationHelper` 默认文本 provider，从纯 `Win32WindowTextProvider` 改为 UIA 优先、Win32 fallback 的组合 provider。
- 修改 `learning_agent/computer_use/__init__.py`，导出 Phase34 两个 provider。
- 新增 `learning_agent/tests/test_windows_computer_use_uia_provider_phase34.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase34_windows_uia_text_provider.json`。
- 新增书面计划 `docs/superpowers/plans/2026-06-03-phase34-windows-uia-text-provider.md`。

## 当前边界

- Phase34 仍是只读文本观察增强。
- Phase34 没有扩大真实鼠标、键盘、点击、拖拽或窗口控制动作。
- `uiautomation` 依赖不是强制安装依赖；没有依赖时会降级到 Win32 文本 fallback。
- 验收和测试使用 fake UIA module，不读取用户真实桌面。
- UIA 文本进入现有 evidence store 后仍要经过敏感文本过滤。

## 已完成验证

- 红灯测试已确认生产代码缺少 `FallbackNativeWindowTextProvider` 和 `WindowsUiautomationTextProvider`。
- 实现后聚焦测试已通过：`python -m unittest learning_agent.tests.test_windows_computer_use_uia_provider_phase34`，6 tests OK。
- Phase32/33 兼容测试已通过：9 tests OK。
- Phase34 scenario JSON 格式检查已通过。
- Phase27-34 邻近回归已通过：44 tests OK。
- `py_compile` 已通过。
- 全量回归已通过：`python -m unittest discover -s learning_agent\tests`，650 tests OK，skipped=1。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/agent_capability_phase34_windows_uia_text_provider-20260603_090056/result.json`。
- 独立 verifier 复验已通过：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 最终 marker：`PHASE34_WINDOWS_UIA_TEXT_PROVIDER_READY PHASE34_WINDOWS_UIA_TEXT_PROVIDER_OK uia=true fallback=true raw_text_hidden=true actions_expanded=false`。

## 学习备份

- 备份目录：`learning_agent/test/agent_capability_phase34_windows_uia_text_provider_20260603/`。
