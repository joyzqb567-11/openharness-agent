# Phase 6：`/chrome` 终端状态 UI 书面计划

## 目标
- 在真实交互终端中新增 `/chrome` 命令，提供聚焦浏览器生态的状态视图。
- 状态视图覆盖 provider、Chrome extension、native host、active tab、权限事件、最近浏览器 run 和录制证据。
- 复用 `build_status_snapshot()` 统一事实源，避免终端 UI 与 SDK/API 状态分裂。

## 范围
- 新增专用渲染器 `learning_agent/app/chrome_status_renderer.py`。
- 扩展 `learning_agent/app/interactive.py`，识别 `/chrome` 和 `chrome`。
- 新增自动化测试锁定渲染文本和命令入口可导入。

## 不做
- 不在本阶段启动真实 Chrome。
- 不改变已有 `/status` 大状态页。

## 成功标准
- `/chrome` 能输出 `Chrome Status`、provider 可用性、extension/native host、active tab、权限计数、最近 run、录制路径。
- 空状态也能输出清楚的空态，而不是报错。
- 终端命令会写入验收事件 `chrome_status_printed`。

## 验证
- 先写失败测试：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18`
- 实现后运行相关状态生态回归和 py_compile。
