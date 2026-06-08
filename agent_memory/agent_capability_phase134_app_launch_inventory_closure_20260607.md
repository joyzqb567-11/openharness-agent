# Phase134 App Launch Inventory Closure

时间：2026-06-07

本轮目标：把 `/computer use --full` 的普通应用发现能力从“只是不限制 50 个候选”推进到“发现层、resolver 层、真实启动后端层一起闭合”。

事实结论：
- `windows_app_inventory.py` 已接入 AppX/AUMID 枚举，并保留开始菜单 `.lnk` / `.appref-ms` 的 `shortcut` 启动身份。
- `windows_launch_resolver.py` 已把 `appx` 和 `shortcut` 标记为 Phase110 真实后端支持路线。
- `generic_launch_backend.py` 已存在 `launch_appx_aumid` 和 `launch_start_menu_shortcut` 后端，本轮 maturity 矩阵开始检查这些后端事实。
- `full_maturity_matrix.py` 新增 `appx_aumid_inventory_discovery_available`、`start_menu_shortcut_inventory_preserved`、`resolver_non_argv_backends_supported` 三个门禁字段。
- 自动化测试已覆盖新增闭环：`test_windows_computer_use_app_launch_inventory_closure_phase134` 和 full maturity 矩阵测试均通过。

边界说明：
- 这证明普通应用发现/解析/启动后端的源码链路已闭合，但不等于已经逐个真实启动了本机所有已安装普通应用。
- 高风险工具仍应继续排除；后续若要验证“所有普通应用真实可启动”，需要抽样或分批真实桌面验收，不能只靠静态矩阵。

本轮修改副本：`learning_agent/test/phase134_app_launch_inventory_closure_20260607/`
