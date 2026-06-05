# /computer use --full 通用启动后端成熟记录

日期：2026-06-05

目标：实现蓝图 Task 2，把 Phase109 的记录型“启动候选”推进为独立的通用启动后端。

本轮结论：
- 默认路径仍不启动真实应用，后端调用次数为 0。
- 授权路径使用 `argv` 数组，不使用 shell 字符串。
- 危险计划在进入后端前拒绝，保证零桌面副作用。
- 启动后会登记本 agent 自有进程，后续 cleanup 能区分用户原有进程和 agent 新启动进程。
- 启动失败会返回结构化 `failure_reason`，不再沉默失败。
- Phase109 默认启动后端已切换到 `Phase110RecordingGenericLaunchBackend`，新后端不再孤立。

新增代码：
- `learning_agent/computer_use/generic_launch_backend.py`
- `learning_agent/tests/test_windows_computer_use_generic_launch_backend_maturity.py`

修改代码：
- `learning_agent/computer_use/generic_real_launch_candidate.py`

红测证据：
- 先运行 `python -m unittest learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`
- 结果为 `ModuleNotFoundError: No module named 'learning_agent.computer_use.generic_launch_backend'`
- 这证明测试先于实现，缺口是真实存在的。

通过验证：
- `python -m py_compile learning_agent\computer_use\generic_launch_backend.py learning_agent\computer_use\generic_real_launch_candidate.py learning_agent\tests\test_windows_computer_use_generic_launch_backend_maturity.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_real_launch_candidate_phase109`
- `python -m learning_agent.computer_use.generic_launch_backend`

固定 token：
- `PHASE110_GENERIC_LAUNCH_BACKEND_READY`
- `PHASE110_GENERIC_LAUNCH_BACKEND_OK`

后续约束：
- Task 3 的窗口身份绑定必须消费 Phase110 输出的 `process_id`、`process_executable`、`argv` 和 `owned_process_registered`。
- Task 4 的资源清理登记可以升级当前 `Phase110OwnedProcessRegistry`，但不能改成逐应用清理器。
