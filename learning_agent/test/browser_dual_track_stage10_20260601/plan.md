# Browser Dual Track Stage 10 Fallback Recovery Plan Backup

本文件是 `docs/superpowers/plans/2026-06-01-browser-dual-track-stage10-fallback-recovery.md` 的备份。

## 目标

把浏览器双轨架构的失败恢复和降级策略做实：

1. 当前 Chrome/登录态任务，插件不可用时不能静默降级。
2. 只有用户或上层明确传入 `allow_cdp_fallback=true`，才允许走 CDP。
3. provider 不可用时必须阻断真实 handler，不能只是记录日志。
4. tab context 失效时必须提示重新调用 `browser_tabs_context`。
5. 连续 3 次浏览器动作失败后必须停止并汇报。

## 验收

1. 新增 `learning_agent/tests/test_browser_fallback_recovery_stage10.py`。
2. 修改 `learning_agent/browser_automation_mcp_server.py` 和 `learning_agent/browser/runtime_events.py`。
3. 新增 controller 场景 `browser_fallback_recovery_stage10_acceptance.json`。
4. 通过 focused tests、相关回归、py_compile、完整单测、controller、verifier。

