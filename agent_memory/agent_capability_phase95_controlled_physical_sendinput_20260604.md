# 2026-06-04 Agent Capability Phase 95 Controlled Physical SendInput

## 目标

- 在 Phase94 “已授权真实派发候选”之后，补齐一个受控的物理 SendInput sender adapter。
- 默认仍然不触碰真实桌面；只有显式启用 `LEARNING_AGENT_PHASE95_ENABLE_REAL_SENDINPUT=1` 或注入启用参数时才允许进入物理派发路径。
- 继续拒绝终端、PowerShell、Codex UI、系统/安全/认证类高风险窗口。
- 继续拒绝未知低层事件和原始文本事件，报告中只保留脱敏摘要。

## 修改文件

- `learning_agent/computer_use/controlled_physical_sendinput.py`
- `learning_agent/tests/test_windows_computer_use_controlled_physical_sendinput_phase95.py`
- `learning_agent/computer_use/__init__.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase95_controlled_physical_sendinput.json`
- `learning_agent/runtime/files.py`
- `learning_agent/tests/test_runtime_files.py`

## 验证

- Runtime tests：3 OK。
- Phase95 focused tests：5 OK。
- Phase95 CLI self-check 输出 `PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_READY PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK`。
- Phase94+95 adjacent regression：9 OK。
- Phase90 family regression：25 OK。
- Computer Use focused suite：230 OK。
- Compile check：exit 0。
- Full unittest discover：845 OK，skipped=1。

## 边界

- Phase95 证明“授权候选低层事件可以到达受控物理 sender adapter”，但默认仍不触碰真实桌面。
- Phase95 没有扩大无限制控制范围，真实物理派发仍受 env gate、目标窗口校验、事件类型白名单和 raw text 拒绝约束。
- 当前还需要真实可见终端 controller 场景通过，才能按项目规则声明完整开发完成。
