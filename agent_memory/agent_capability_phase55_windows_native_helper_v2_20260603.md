# Phase 55 Windows Native Helper V2

## 目标

把 Windows Computer Use 从进程内 native host 合同推进到真实 out-of-process helper v2：主 agent 通过 JSONL stdio 调用子进程，能够在 helper 卡死、崩溃或拒绝真实动作时保持稳定恢复。

## 已完成

- 新增 `learning_agent/computer_use/native_helper_v2.py`。
- 新增 `learning_agent/tests/test_windows_computer_use_native_helper_v2_phase55.py`。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase55_windows_native_helper_v2.json`。
- helper v2 支持 `status`、`list_windows`、`capture_window`、`read_uia_tree`、`send_input`、`hotkey`、`cleanup` 协议。
- `send_input` 默认拒绝，不触碰真实鼠标键盘。
- 协议响应不包含截图原始 bytes、UIA 原始文本、输入原始文本。
- Windows 子进程 stdio 固定 UTF-8，避免中文协议在 Windows 控制台下解码失败。
- helper 超时和崩溃都会返回结构化错误，不拖垮主 agent。

## 验证

- TDD 红灯：`ModuleNotFoundError: No module named 'learning_agent.computer_use.native_helper_v2'`。
- Phase55 focused tests：3 OK。
- `py_compile`：通过。
- Phase55 scenario JSON：通过。
- CLI 自检：`PHASE55_WINDOWS_NATIVE_HELPER_V2_OK process_started=true health=true messages=true timeout_handled=true crash_handled=true send_input_refused=true raw_text_hidden=true actions_expanded=false marker=PHASE55_WINDOWS_NATIVE_HELPER_V2_READY`。
- Phase44/52/53/54/55 回归：13 OK。
- 真实可见终端验收：`learning_agent/acceptance_controller/runs/agent_capability_phase55_windows_native_helper_v2-20260603_165500/result.json`，`completed=true`，`prompt_sent=true`，`prompt_received=true`，`final_printed=true`。

## 边界

- Phase55 只证明 helper 进程边界、协议、超时、崩溃、cleanup 和安全默认拒绝。
- Phase55 不声明真实截图、真实 UIA、真实 SendInput 已完成。
- Phase56-58 继续分别补真实截图、真实 UIA、真实动作执行。
