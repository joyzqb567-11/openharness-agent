# Browser Dual Track Stage 2 学习备份

本文件是 Stage 2 书面计划的学习备份，正式计划位于：

```text
docs/superpowers/plans/2026-06-01-browser-dual-track-stage2-provider-adapters.md
```

Stage 2 目标：

1. 新增 `VisibleChromiumProvider`。
2. 新增 `RealChromeCdpProvider`。
3. 让 `BrowserAutomationServer.call()` 顶层调用先写 `browser_provider_decision`。
4. 通过 provider adapter 调用现有 server 工具 handler。
5. 保持模型只看到统一 `browser_*` 工具。

Stage 2 不做：

1. 不写 Chrome 插件。
2. 不安装 native host。
3. 不实现 tabs context 强制合同。
4. 不新增 provider-specific 工具名。

验收要求：

1. provider adapter 单测通过。
2. 浏览器相关回归测试通过。
3. 全量测试通过。
4. `start_oauth_agent.bat` 真实可见终端验收通过。
