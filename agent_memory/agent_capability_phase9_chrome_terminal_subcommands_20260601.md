# Agent Capability Phase 9 - Chrome Terminal Subcommands

## 目标
- 把 `/chrome` 面板中展示的 Chrome 动作提示推进为真实终端可执行子命令。
- 默认保持安全预览，不写 Windows registry，不删除 registry。

## 本阶段新增能力
- `/chrome install-preview [extension_id]`
  - 生成 native host manifest。
  - 生成 `.cmd` launcher。
  - 输出 `dry_run=true`、manifest 路径、launcher 路径和 registry 覆盖范围。
  - 同时兼容 repo 根目录和 `learning_agent` 目录作为 workspace，避免真实 bat 入口出现双层 `learning_agent\learning_agent` 路径。
- `/chrome repair`
  - 输出 native host 当前状态对应的中文修复建议。
- `/chrome uninstall-preview`
  - 输出将要清理的 registry key 列表。
  - 默认 `dry_run=true`，不删除真实 registry。

## 自动化验证
- `python -m unittest learning_agent.tests.test_chrome_terminal_subcommands_phase9`
- `python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_agent_capability_phase8_production_edges`
- `python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_terminal_subcommands_phase9.py`
- `python -m unittest discover -s learning_agent\tests`

## 风险边界
- Phase 9 只实现 preview/repair/uninstall-preview，不开放真实 registry 写入命令。
- 真实安装仍应由后续明确确认型命令或工具执行，避免小白用户误改系统。

## 真实终端验收
- 场景文件：`learning_agent/acceptance_controller/scenarios/agent_capability_phase9_chrome_install_preview.json`
- 第一次真实终端验收发现 workspace 路径双层嵌套，已补回归测试并修复。
- 第二次真实终端验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase9_chrome_install_preview-20260601_224229`
- 结果：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 截图确认：终端中 `/chrome install-preview` 输出 `dry_run=true`，manifest 和 launcher 路径均为 `learning_agent\memory\chrome_native_host\...`。
- 独立 verifier 复验：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
