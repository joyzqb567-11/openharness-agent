# Agent Capability Phase 12 - Chrome Status Guide

## 目标
- 把 `/chrome` 状态页升级为向导式状态页。
- 用户看到 Chrome/native host 状态后，可以直接知道下一条应该执行的命令。

## 新增能力
- `/chrome` 新增 `installer_state` 和 `manifest_path` 展示。
- `/chrome` 新增 `Chrome Guide` 区块。
- 未安装或未知状态时提示 `/chrome install-preview`。
- 已生成 manifest 但未注册时提示 `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。
- 已注册时提示进入 `extension pairing / session sync`。
- registry 不匹配或异常时提示 `/chrome repair`。
- `build_status_snapshot()` 现在会把 `ChromeNativeHostInstaller.status()` 合并进 `browser.provider_status.native_host`。

## 自动化验证
- 红灯：渲染器缺少 `Chrome Guide`，快照缺少 `installer_state`。
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18.ChromeTerminalStatusUiStage18Tests.test_render_chrome_status_guides_next_command_for_installer_states`
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_status_snapshot_phase12`
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8 learning_agent.tests.test_status_ecosystem_deep_alignment`，Ran 18 tests OK。
- 编译检查：`python -m py_compile learning_agent\app\chrome_status_renderer.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py learning_agent\tests\test_chrome_status_snapshot_phase12.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，Ran 581 tests OK，skipped=1。

## 真实终端验收
- 场景文件：`learning_agent/acceptance_controller/scenarios/agent_capability_phase12_chrome_status_guide.json`
- 验收策略：真实终端输入 `/chrome`，截图确认出现 `Chrome Guide` 和 `next=/chrome ...`。
- 真实终端 run：`learning_agent/acceptance_controller/runs/agent_capability_phase12_chrome_status_guide-20260601_230542`
- 结果：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 截图确认：终端显示 `installer_state=manifest_created`、`Chrome Guide`、`next=/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。
- 独立 verifier 复验：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
