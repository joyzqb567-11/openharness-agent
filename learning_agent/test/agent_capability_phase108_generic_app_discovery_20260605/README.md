# Phase108 Generic App Discovery 学习备份

本目录保存 Phase108 本轮新增和修改的关键文件，方便逐行学习。

## 本轮目标

- 把 `/computer launch <app>` 从“每个应用都要硬编码别名”的路线，升级为“通用应用发现 + 风险分类 + 默认不真实启动”的路线。
- 普通应用不再要求逐个加入白名单或逐个写补丁。
- 高风险应用仍然拒绝，例如 PowerShell、CMD、注册表、系统设置、安全工具等。
- 默认路径不打开真实应用，只生成可审计的安全启动计划。

## 关键文件

- `generic_app_discovery.py`：Phase108 通用发现内核。
- `interactive.py`：接入 `/computer launch <app>` 的交互命令路径。
- `test_windows_computer_use_generic_app_discovery_phase108.py`：Phase108 红绿测试。
- `agent_capability_phase108_generic_app_discovery.json`：真实可见终端验收场景。
- `visible_terminal_result.json`：真实可见终端验收结果。
- `visible_terminal_latest_run_readable.md`：真实终端运行日志。

## 验收结论

最终真实终端 token：

```text
PHASE108_GENERIC_APP_DISCOVERY_READY PHASE108_GENERIC_APP_DISCOVERY_OK dynamic_discovery_used=true hardcoded_app_whitelist_required=false per_app_patch_required=false generic_target_default_off=true high_risk_refused=true real_desktop_touched=false uncontrolled_actions_expanded=false
```

## 当前边界

Phase108 不是无限制控制本地电脑。它证明的是：普通应用目标可以进入通用发现和安全计划，不再需要每个应用单独白名单；真实打开应用仍保持默认关闭，高风险目标仍被拒绝。
