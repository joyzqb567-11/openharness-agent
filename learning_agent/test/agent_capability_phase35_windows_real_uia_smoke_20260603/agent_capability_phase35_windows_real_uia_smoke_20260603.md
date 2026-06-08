# Phase35 Windows Real UIA Safe-Window Smoke 记录

更新时间：2026-06-03

## 本阶段目标

Phase35 的目标是把 Windows Computer Use 从“fake/provider 合同测试”推进到“真实安全窗口 smoke harness”：

- 默认先检查 `uiautomation` 依赖是否存在。
- 依赖缺失时诚实报告，不使用 fake provider 冒充真实 UIA。
- 依赖存在时只启动自己创建的安全 Notepad 临时文件窗口。
- 只读取该安全窗口的 UIA 文本，不移动鼠标，不点击桌面，不扩展键盘鼠标动作。
- 输出稳定验收标记 `PHASE35_WINDOWS_REAL_UIA_SMOKE_READY`。

## 已实现内容

- 新增 `learning_agent/computer_use/real_uia_smoke.py`。
- 新增 `Phase35SafeWindowTarget`、`Phase35RealUiaSmokeResult`。
- 新增 `run_phase35_real_uia_smoke()`。
- 新增 `python -m learning_agent.computer_use.real_uia_smoke` CLI 输出。
- 修改 `learning_agent/computer_use/__init__.py` 暴露 Phase35 API。
- 新增单元测试 `learning_agent/tests/test_windows_computer_use_real_uia_smoke_phase35.py`。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase35_windows_real_uia_smoke.json`。

## 当前环境事实

本机当前 Python 环境未安装 `uiautomation`，因此 Phase35 在当前环境下会输出：

- `dependency_reported=true`
- `dependency_available=false`
- `real_uia_attempted=false`
- `real_uia_verified=false`
- `fake_provider_used=false`
- `actions_expanded=false`

这不是失败，而是 Phase35 设计要求的诚实诊断结果。

## 风险与后续

- Phase35 还不是完整 OS 级输入执行器。
- Phase35 不新增真实鼠标/键盘动作。
- Phase36 应继续补 Windows.Graphics.Capture provider 合同。
- Phase37 应补 SendInput executor，并继续保持安全门禁。
