# Agent Capability Phase 11 - Chrome Uninstall Confirm

## 目标
- 给 Phase 10 的真实安装确认链路补齐对称回滚命令。
- 真实删除 Windows registry 必须经过显式确认 token，避免误删用户系统配置。

## 新增能力
- `/chrome uninstall-confirm I_UNDERSTAND_DELETE_REGISTRY`
  - 删除当前用户 HKCU 下 Chrome/Edge/Brave/Chromium 的 NativeMessagingHosts registry。
  - 输出 `dry_run=false`、删除前 registry 值和 registry 覆盖范围。
- `/chrome uninstall-confirm` 缺少 token 时会拒绝执行。
  - 输出固定 token 和用法。
  - 不删除 registry。

## 自动化验证
- 红灯：新增测试先因 `/chrome uninstall-confirm` 被识别为未知命令失败。
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`，Ran 8 tests OK。
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`，Ran 17 tests OK。
- 编译检查：`python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，Ran 579 tests OK，skipped=1。

## 真实终端验收
- 场景文件：`learning_agent/acceptance_controller/scenarios/agent_capability_phase11_chrome_uninstall_confirm_refusal.json`
- 验收策略：真实终端只测试“缺 token 拒绝执行”，避免本轮误删用户 registry。
- 真实终端 run：`learning_agent/acceptance_controller/runs/agent_capability_phase11_chrome_uninstall_confirm_refusal-20260601_225807`
- 结果：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 截图确认：终端输入 `/chrome uninstall-confirm` 后显示“已拒绝执行：需要显式确认 token”，并提示 `I_UNDERSTAND_DELETE_REGISTRY`。
- 独立 verifier 复验：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
