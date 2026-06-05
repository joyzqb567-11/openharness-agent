# Computer Use Full Maturity Blueprint - 2026-06-05

## Context

用户指出 `/computer use --full` 如果继续无止境 Phase，就永远无法判断是否成熟。

本次工作不是继续实现一个功能 Phase，而是冻结成熟定义和最终停止条件。

## Blueprint

书面蓝图已保存到：

`docs/superpowers/plans/2026-06-05-computer-use-full-maturity-blueprint.md`

## Core Decision

`/computer use --full` 成熟必须同时满足 M0-M7：

- M0 产品语义成熟
- M1 普通应用通用发现成熟
- M2 通用真实启动成熟
- M3 窗口身份绑定成熟
- M4 通用操作闭环成熟
- M5 清理和恢复成熟
- M6 安全成熟
- M7 真实可见终端成熟验收

## Final Stop Rule

当最终矩阵通过并且真实可见终端 scenario 输出 `COMPUTER_USE_FULL_MATURE_OK` 后，停止新增“成熟能力 Phase”。

后续只允许：

- bugfix
- compatibility
- representative sample

不能再用新 Phase 逃避成熟定义。

## Final Token

`COMPUTER_USE_FULL_MATURE_READY COMPUTER_USE_FULL_MATURE_OK generic_discovery=true generic_real_launch=true verified_window_actions=true cleanup_recovery=true high_risk_refused=true visible_terminal_acceptance=true hardcoded_app_whitelist_required=false per_app_patch_required=false uncontrolled_actions_expanded=false`
