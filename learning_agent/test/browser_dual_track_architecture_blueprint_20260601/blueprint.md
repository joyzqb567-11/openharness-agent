# learning_agent 双轨真实浏览器架构改造蓝图

日期：2026-06-01

状态：设计蓝图摘要备份，完整原文保存在 `docs/superpowers/specs/2026-06-01-browser-dual-track-architecture-blueprint.md`。

## 核心结论

learning_agent 应采用“底层双轨、模型表面单轨”的真实浏览器架构。

底层双轨：

1. Playwright / CDP / 可见 Chromium：用于公开网页、本地调试、自动化验收。
2. Chrome 插件 / Native Host / MCP Bridge：用于当前 Chrome、登录态、OAuth、复杂表单和站点权限。

模型表面单轨：

1. 模型只调用统一 `browser_*` 工具。
2. 模型不直接选择插件 provider 或 CDP provider。
3. `BrowserProviderRouter` 根据意图、权限、插件状态、登录态需求和用户显式要求选择底层 provider。

## 阶段摘要

1. Stage 0：蓝图确认与范围冻结。
2. Stage 1：Provider Protocol 和 Router 空实现。
3. Stage 2：现有 Playwright/CDP 能力迁入 Provider。
4. Stage 3：统一工具表面和模型防误选。
5. Stage 4：`browser_tabs_context` 合同。
6. Stage 5：Chrome 插件 MVP，只读能力。
7. Stage 6：Chrome 插件写动作。
8. Stage 7：插件站点权限。
9. Stage 8：状态 UI / CLI / API 生态。
10. Stage 9：GIF/录屏/视觉证据。
11. Stage 10：失败恢复和 fallback 策略。
12. Stage 11：长任务 harness 接入。
13. Stage 12：真实可见终端总验收。

## 完成门禁

只有同时满足以下条件，才能声明开发完成：

1. 代码修改完成。
2. 自动化测试通过。
3. 独立 verifier 通过。
4. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat` 真实可见终端交互验收通过。
5. 浏览器实际可见、可点、可输入、可读页面结果。

## 原文位置

完整蓝图保存在：

`H:\codexworkplace\sofeware\OpenHarness-main\docs\superpowers\specs\2026-06-01-browser-dual-track-architecture-blueprint.md`
