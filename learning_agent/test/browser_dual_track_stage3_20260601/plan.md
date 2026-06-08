# Browser Dual Track Stage 3 Tool Surface Plan Backup

来源：`docs/superpowers/plans/2026-06-01-browser-dual-track-stage3-tool-surface.md`

本备份用于防止长任务中断后偏离 Stage 3 范围。Stage 3 只做模型工具表面和防误选门禁，不做 Chrome 插件、native host、权限 UI 或 GIF 证据。

成功标准：
- 模型只看到统一 `browser_*` 动作工具。
- provider-specific open/click/type 等重复工具不会进入工具清单。
- 真实 Chrome 连接类工具被标记为 advanced/provider-control。
- skill/harness 明确“模型不选择 provider，底层由 BrowserProviderRouter 决定”。
- provider 决策事件可审计。
- 单测、全量测试、真实可见终端验收均通过。
