# Phase107 交互启动目标解析备份

本目录保存 Phase107 新增和修改过的代码副本，方便后续学习和对照。

- `interactive.py`：包含 `/computer launch <目标>` 接入 Phase107 解析器和 `phase107_main()` 验收入口。
- `interactive_launch_target.py`：包含 Phase107 目标解析器、普通应用别名和高风险拒绝规则。
- `test_windows_computer_use_interactive_launch_target_phase107.py`：包含 Phase107 红测和回归测试。
- `agent_capability_phase107_interactive_launch_target.json`：包含真实可见终端验收场景。

关键验收 token：

```text
PHASE107_INTERACTIVE_LAUNCH_TARGET_READY PHASE107_INTERACTIVE_LAUNCH_TARGET_OK calc_recognized_default_off=true high_risk_refused=true powershell_zero_side_effect=true real_desktop_touched=false uncontrolled_actions_expanded=false
```
