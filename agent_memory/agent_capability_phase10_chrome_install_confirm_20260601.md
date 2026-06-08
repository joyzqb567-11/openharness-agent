# Agent Capability Phase 10 - Chrome Install Confirm

## 目标
- 在 `/chrome install-preview` 后补齐真实安装确认链路。
- 真实写 Windows registry 必须经过显式确认 token，避免误操作。

## 新增能力
- `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`
  - 生成 native host manifest。
  - 生成 `.cmd` launcher。
  - 写入当前用户 HKCU 下 Chrome/Edge/Brave/Chromium 的 NativeMessagingHosts registry。
  - 输出 `dry_run=false`、manifest 路径、launcher 路径和 registry 覆盖范围。
- `/chrome install-confirm <extension_id>` 缺少 token 时会拒绝执行。
  - 输出固定 token 和用法。
  - 不写 registry。

## 自动化验证
- 红灯：新增测试先因 `run_chrome_terminal_command()` 不支持 `registry_adapter` 且缺少 `install-confirm` 失败。
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`，Ran 6 tests OK。
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`，Ran 15 tests OK。
- 编译检查：`python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，Ran 577 tests OK，skipped=1。

## 真实终端验收
- 场景文件：`learning_agent/acceptance_controller/scenarios/agent_capability_phase10_chrome_install_confirm_refusal.json`
- 验收策略：真实终端只测试“缺 token 拒绝执行”，避免本轮误写用户 registry。
- 真实终端 run：`learning_agent/acceptance_controller/runs/agent_capability_phase10_chrome_install_confirm_refusal-20260601_225316`
- 结果：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 截图确认：终端输入 `/chrome install-confirm abcdefghijklmnopabcdefghijklmnop` 后显示“已拒绝执行：需要显式确认 token”，并提示 `I_UNDERSTAND_WRITE_REGISTRY`。
- 独立 verifier 复验：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
