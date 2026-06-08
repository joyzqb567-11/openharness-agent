# 2026-06-07 Phase136 WeChat full-mode launch acceptance

## Context
- 本轮处理的问题是：`/computer use --full` 开启后，用户输入“请帮我打开本机电脑微信”时，agent 不应把微信排除在普通应用之外，也不应只停在 discover 或乱传脏 app_name。
- 源码事实确认：当前主循环应用发现入口是 `learning_agent/core/agent.py::_computer_discover -> learning_agent/computer_use/windows_app_inventory.py`，启动入口是模型主循环调用 `computer_action action=launch_app`，不是旧 `generic_app_discovery.py`。
- 根因链路：微信在开始菜单可发现，但英文别名 `wechat/weixin` 没有合并到主候选；中文自然语言“本机电脑微信”缺少“软件/应用”泛词时，桌面任务 router 没有稳定进入 full harness；微信启动后真实窗口可能由代理/子进程承载，旧窗口绑定只看启动 pid，导致 `visible_window_verified=false`。

## Fix
- `windows_app_inventory.py` 合并同一应用的别名和启动身份，让中文微信候选同时能被 `微信/wechat/weixin` 命中。
- `desktop_task_router.py` 增加通用中文本地应用名抽取，支持“本机电脑微信”“本机电脑QQ软件”等真实用户说法进入桌面 GUI 路线。
- `core/agent.py` 强化 full harness：discover 若只有唯一高置信候选，下一轮必须用候选原始 `app_name` 调用 `computer_action launch_app`，避免再次出现 `微信.pdf???` 这类脏目标。
- `universal_target_session.py` 增加代理/多进程窗口绑定：先尝试 pid 精确绑定，失败后根据目标标题/进程/AppID 匹配可见窗口，并保留 `actual_window_process_id`、`proxy_owner_process_id`、`agent_owned_proxy_window` 作为审计字段。
- 新增真实验收场景 `learning_agent/acceptance_controller/scenarios/computer_use_full_open_wechat_probe.json`，要求真实启动微信、可见窗口验证、开始菜单 shortcut 后端和微信显示名都命中。

## Verification
- 自动化回归通过：`python -m unittest learning_agent.tests.test_windows_computer_use_universal_target_session learning_agent.tests.test_windows_computer_use_full_desktop_task_router learning_agent.tests.test_windows_computer_use_wechat_app_inventory_phase136 learning_agent.tests.test_windows_computer_use_windows_app_inventory_phase122 learning_agent.tests.test_windows_computer_use_launch_resolver_phase124 learning_agent.tests.test_core_run_loop`，共 113 个测试 OK。
- 语法检查通过：`python -m py_compile` 覆盖本轮修改的 computer_use、core agent 和测试文件。
- 真实可见终端验收通过：acceptance controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/computer use --full`，再输入“请帮我打开本机电脑微信。看到微信窗口后就结束，不要登录，不要输入账号密码。”，结果目录 `learning_agent/acceptance_controller/runs/computer_use_full_open_wechat_probe-20260607_155536/`。
- 验收硬证据：`result.json` 显示 `completed=true`、`assertion.passed=true`，debug log 命中 `real_launch_performed': True`、`visible_window_verified': True`、`launch_backend': 'start_menu_shortcut'`、`display_name': '微信'`。

## Boundary
- 本轮能确认：微信属于普通应用路径，当前 `/computer use --full` 已能通过模型主循环真实启动并观察到微信窗口。
- 本轮不能无限外推为“所有普通应用、所有登录/输入/复杂 UI 工作流 100% 成熟”；它修复的是普通应用发现、中文目标路由、启动决策和代理窗口绑定这条基础链路。
