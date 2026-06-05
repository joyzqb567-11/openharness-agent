# /computer launch 通用后端交互接线成熟记录

日期：2026-06-05

本任务对应蓝图 Task 5：把 `/computer launch <app>` 从“只展示 Phase109 通用真实启动候选”推进到“交互入口实际接到 Phase110 通用启动后端编排”。

完成内容：
- 新增 `learning_agent/tests/test_windows_computer_use_interactive_generic_launch_maturity.py`，覆盖 Obsidian 默认关闭接通后端、显式真实门到达 production 后端形状、PowerShell 高风险拒绝、`/computer stop` 上浮自有资源清理结果。
- 修改 `learning_agent/computer_use/universal_live_execution.py`，新增 Phase113 交互通用启动桥 `run_phase113_interactive_generic_launch_bridge` 和 `phase113_cli_line`。
- 修改 `learning_agent/app/interactive.py`，让 `/computer launch obsidian` 输出 Phase113 token，并让 `/computer stop` 输出 `owned_resource_cleanup_completed` 与 `residual_owned_process`。

安全边界：
- 默认路径仍然 `real_full_launch_attempted=false`。
- 默认路径仍然 `backend_launch_performed=false`。
- 显式真实启动只通过 `LEARNING_AGENT_ENABLE_GENERIC_REAL_LAUNCH_SMOKE=1` 或测试显式参数启用。
- 高风险目标 PowerShell 仍然在进入通用后端前拒绝。

验证记录：
- `python -m py_compile learning_agent\computer_use\universal_live_execution.py learning_agent\app\interactive.py learning_agent\tests\test_windows_computer_use_interactive_generic_launch_maturity.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_interactive_generic_launch_maturity`
- `python -m unittest learning_agent.tests.test_windows_computer_use_interactive_full_launch_phase106 learning_agent.tests.test_windows_computer_use_interactive_launch_target_phase107`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_app_discovery_phase108 learning_agent.tests.test_windows_computer_use_generic_real_launch_candidate_phase109 learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`
- `python -m unittest learning_agent.tests.test_windows_computer_use_mode_commands_phase98 learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity`

结果：自动化验证通过。真实可见终端验收仍需在蓝图 Task 8 统一执行，当前不能声明最终开发完成。
