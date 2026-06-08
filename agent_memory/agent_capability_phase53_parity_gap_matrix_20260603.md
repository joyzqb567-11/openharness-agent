# Phase 53 Parity Gap Matrix

日期：2026-06-03

## 目标

- 把 ClaudeCode computer-use 源码成熟点与 learning_agent 当前 Windows Computer Use 的剩余差距固化成 Phase53-64 可执行矩阵。
- 明确 fake provider 不能替代真实 provider 验收。
- 暴露 `/computer parity` 终端入口，方便用户和外部 agent 在真实终端查看差距矩阵。

## 完成内容

- 新增 `learning_agent/computer_use/parity_gap_matrix.py`。
- 新增 `/computer parity` 终端命令。
- 新增测试 `learning_agent/tests/test_windows_computer_use_parity_gap_phase53.py`。
- 新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase53_parity_gap_matrix.json`。

## 验证

- TDD 红灯：`ModuleNotFoundError: No module named 'learning_agent.computer_use.parity_gap_matrix'`。
- 单元测试：`python -m unittest learning_agent.tests.test_windows_computer_use_parity_gap_phase53` 通过。
- 回归测试：Phase52 production matrix 测试通过。
- 编译：`python -m py_compile` 覆盖新增和修改文件，通过。
- JSON：`python -m json.tool learning_agent/acceptance_controller/scenarios/agent_capability_phase53_parity_gap_matrix.json` 通过。
- CLI：`python -m learning_agent.computer_use.parity_gap_matrix` 输出 `PHASE53_PARITY_GAP_MATRIX_OK`。
- 真实可见终端：`learning_agent/acceptance_controller/controller.ps1` 场景通过，证据在 `learning_agent/acceptance_controller/runs/agent_capability_phase53_parity_gap_matrix-20260603_163413/result.json`。

## 边界

- Phase53 只读，不点击、不移动鼠标、不扩大真实桌面动作面。
- Phase54-64 仍需逐项实现，不能因为 Phase53 matrix 通过而声明全部完成。
