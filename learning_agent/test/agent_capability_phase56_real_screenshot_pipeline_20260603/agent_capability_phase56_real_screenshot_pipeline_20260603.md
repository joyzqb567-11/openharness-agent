# Phase 56 Windows Real Screenshot Pipeline

## 目标

把 Windows Computer Use 截图从 provider/evidence 合同推进到真实安全窗口截图验收：优先 WGC，缺依赖时 fallback 到 GDI，并用 pixel guard 阻止黑屏、空白图、坏尺寸和无标题区域截图误过。

## 已完成

- 新增 `learning_agent/computer_use/real_screenshot_pipeline.py`。
- 修改 `learning_agent/computer_use/native_helper_v2.py`，让 `capture_window` 接入 Phase56 pipeline。
- 修改 `learning_agent/computer_use/__init__.py`，导出 Phase56 API。
- 新增 `learning_agent/tests/test_windows_computer_use_real_screenshot_phase56.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase56_real_screenshot_pipeline.json`。
- Pixel guard 支持 BMP 头、尺寸、位深、像素采样、全黑/全白、颜色多样性、标题区域可见性检查。
- CLI 和真实终端验收会启动自有 Notepad 安全窗口，截图后清理，不操作用户其他窗口。

## 验证

- TDD 红灯：`ModuleNotFoundError: No module named 'learning_agent.computer_use.real_screenshot_pipeline'`。
- Phase56 focused tests：5 OK。
- Phase45/52/54/55/56 相邻回归：16 OK。
- `py_compile`：通过。
- Phase56 scenario JSON：通过。
- CLI 真实截图自检：`PHASE56_WINDOWS_REAL_SCREENSHOT_OK pixel_guard=true artifact=true helper_v2_capture=true real_smoke=true raw_bytes_hidden=true actions_expanded=false marker=PHASE56_WINDOWS_REAL_SCREENSHOT_READY`。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase56_real_screenshot_pipeline-20260603_170920/result.json`，`completed=true`，`prompt_sent=true`，`prompt_received=true`，`final_printed=true`。
- 真实终端截图 artifact：`learning_agent/memory/computer_use/evidence/computer-window-20260603T090932Z-17657b0b.bmp`。

## 边界

- 本阶段只读截图，不移动鼠标，不点击，不键盘输入，不改系统设置。
- WGC 仍缺 Python 绑定，本机真实验收使用 `win32_gdi_printwindow` fallback。
- Phase57 继续补真实 UIA 控件树和语义 locator。
