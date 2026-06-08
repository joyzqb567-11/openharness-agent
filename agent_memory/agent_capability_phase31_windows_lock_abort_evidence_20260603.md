# Phase 31 Windows OS Computer Use Lock, Abort, And Evidence Chain

## 目标

- 在 Phase 30 安全动作门禁基础上，补齐 stale lock 恢复、动作前后窗口状态证据、磁盘审计链和真实终端 `/computer` abort/status UI。
- 本阶段仍不扩大真实鼠标键盘动作范围，不声明真实 SendInput、Windows.Graphics.Capture 或 UIAutomationClient native helper 已完成。

## 已完成

- 新增 `learning_agent/computer_use/audit.py`：提供 Computer Use 审计事件 JSONL、动作证据链 JSON、递归脱敏和状态输出。
- 修改 `learning_agent/computer_use/lock.py`：增加 stale lock TTL、陈旧 owner 恢复证据、UTC 时间解析修复，并保持 abort flag 门禁。
- 修改 `learning_agent/computer_use/controller.py`：支持注入 `ComputerUseAuditStore`，动作执行前后通过只读 `get_window_state` 采集 before/after evidence，并把同一 `audit_id` 写入结果、事件和 chain 文件。
- 修改 `learning_agent/app/interactive.py`：新增 `/computer`、`/computer status`、`/computer abort <reason>`、`/computer clear-abort`、`/computer release [session_id]` 真实终端命令入口，并写 `computer_status_printed` 验收事件。
- 修改 `learning_agent/computer_use/__init__.py`：对外导出 `ComputerUseAuditStore`。
- 新增 `learning_agent/tests/test_windows_computer_use_lock_abort_phase31.py`：覆盖 stale lock 恢复、before/after evidence、磁盘脱敏、`/computer` abort/clear 和场景文件。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase31_windows_lock_abort_evidence.json`：真实可见终端验收场景，验证 lock、abort、evidence chain、磁盘脱敏和 `/computer` 命令入口。

## 最终验证

- 红灯：Phase31 首次失败于 `ImportError: cannot import name 'run_computer_terminal_command'`，证明 `/computer` 终端入口缺失。
- 聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_lock_abort_phase31`，5 tests OK。
- 相邻回归：Phase 17/20/27/28/29/30 Computer Use 相关 24 tests OK。
- 语法检查：`python -m py_compile learning_agent\computer_use\audit.py learning_agent\computer_use\lock.py learning_agent\computer_use\controller.py learning_agent\computer_use\__init__.py learning_agent\app\interactive.py learning_agent\tests\test_windows_computer_use_lock_abort_phase31.py` 通过。
- 场景 JSON：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase31_windows_lock_abort_evidence.json` 通过。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，635 tests OK，skipped=1。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase31_windows_lock_abort_evidence-20260603_075659/result.json`。
- 独立 verifier：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 最终 marker：`PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_READY PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_OK recovered=true chain=true before=true after=true abort_blocked=true raw_text_hidden=true terminal_abort=true terminal_clear=true coord=34,48`。
- 学习备份：`learning_agent/test/agent_capability_phase31_windows_lock_abort_evidence_20260603/`。

## 已修复风险

- 修复 `parse_lock_timestamp` 使用本地时区解析 UTC 的问题；否则东八区会把刚创建的锁误判为 8 小时前的陈旧锁。
- 成功动作现在有 `before_evidence` 和 `after_evidence`，并且二者都绑定同一个 `audit_id`。
- 磁盘审计只保存 `text_sha256_16` 等脱敏摘要，不保存原始 `type_text` 文本。
- 用户可以在真实终端通过 `/computer abort <reason>` 阻断下一次桌面动作，通过 `/computer clear-abort` 恢复。

## 边界

- Phase31 使用安全内存后端和临时锁/审计目录完成自动化验证，不触碰真实桌面鼠标键盘。
- 真实 Windows native helper、真实截图、UI Automation 文本树、DPI/多显示器/窗口遮挡处理仍属于后续 Phase32+。
- 终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run 仍是禁止自动化目标。
