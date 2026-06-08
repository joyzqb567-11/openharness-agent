# Phase 39 Windows Computer Use DPI / Multi-Monitor Coordinates Report

## Status

Phase 39 已完成代码修改、自动化验证、真实可见终端验收、独立 verifier 复验和学习备份。

## What Changed

- 新增 `learning_agent/computer_use/coordinates.py`，提供 `build_coordinate_context()`、CLI 自检和稳定验收 marker。
- 修改 `learning_agent/computer_use/action_policy.py`，窗口相对坐标现在会通过 Phase39 坐标模型换算成物理屏幕坐标，同时保留 Phase30 兼容字段。
- 修改 `learning_agent/computer_use/windows_backend.py`，静态/上游窗口记录会保留 `app_id`、`display` 和 `displays` 元数据，避免 DPI 信息在 inventory 归一化时丢失。
- 修改 `learning_agent/computer_use/controller.py`，`get_window_state` 返回 `coordinate_context`、`coordinate_model`、`dpi_scale`、`window_logical_rect` 和 `window_physical_rect`。
- 修改 `learning_agent/computer_use/__init__.py`，公开导出 Phase39 坐标 API。
- 新增 `learning_agent/tests/test_windows_computer_use_coordinates_phase39.py`。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase39_windows_coordinates.json`。

## Verified

- 红灯：`python -m unittest learning_agent.tests.test_windows_computer_use_coordinates_phase39` 初次失败于 `ModuleNotFoundError: No module named 'learning_agent.computer_use.coordinates'`。
- 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_coordinates_phase39`，5 tests OK。
- 语法检查：`python -m py_compile ...`，exit code 0。
- 场景 JSON：`python -m json.tool ...agent_capability_phase39_windows_coordinates.json`，exit code 0。
- CLI 自检：`PHASE39_WINDOWS_COORDINATES_OK dpi=true multi_monitor=true action_policy=true window_state=true actions_expanded=false marker=PHASE39_WINDOWS_COORDINATES_READY`。
- 相邻回归：Phase30 + Phase39，10 tests OK。
- Phase30-39 回归：50 tests OK。
- 全量回归：`python -m unittest discover -s .\learning_agent\tests`，675 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase39_windows_coordinates-20260603_111521/result.json`，completed=true。
- 独立 verifier：completed=true，assertion.passed=true，permission_sent_count=0。

## Boundaries

- Phase39 只补坐标模型和审计解释，不扩大真实动作范围，`actions_expanded=false`。
- 当前 WGC/UIA 依赖事实不变：本机仍缺少 `uiautomation`、`comtypes`、`winrt/winsdk Windows.Graphics.Capture`。
- 终端、Codex UI、安全设置、密码管理器、认证/验证码窗口仍是禁止自动化目标。
