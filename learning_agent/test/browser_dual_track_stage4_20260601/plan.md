# Stage 4 学习备份：browser_tabs_context 合同执行计划

这是 `docs/superpowers/plans/2026-06-01-browser-dual-track-stage4-tabs-context.md` 的学习备份。

本阶段要补的是 ClaudeCode 类似 `tabs_context_mcp` 的能力：真实 Chrome / 登录态任务在点击、输入、按键、上传前，必须先读取当前标签页上下文。

验收重点不是只看有没有工具名，而是看真实 Chrome 写动作是否真的被 `browser_tabs_context` 卡住，以及关闭、切换、新建标签页后是否要求重新读取上下文。

最终必须通过自动化测试、全量回归、真实可见终端验收和独立 verifier。

