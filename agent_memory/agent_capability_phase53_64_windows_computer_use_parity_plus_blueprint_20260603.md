# Phase 53-64 Windows Computer Use Parity Plus Blueprint Memory

## 目的

用户要求制定书面升级蓝图，把 learning_agent 当前相对 ClaudeCode Computer Use 剩余约 20% 差距全部补齐，并争取在 Windows Computer Use、外部 agent 接管调试、真实验收矩阵上超过 ClaudeCode。

## 蓝图文件

- 正式蓝图：`docs/superpowers/plans/2026-06-03-phase53-64-windows-computer-use-parity-plus.md`
- 学习备份：`learning_agent/test/agent_capability_phase53_64_windows_computer_use_parity_plus_20260603/phase53_64_blueprint.md`

## 阶段范围

- Phase 53：Parity gap lock and non-fake acceptance contract。
- Phase 54：Windows native dependency and permission reality gate。
- Phase 55：Out-of-process Windows native helper v2。
- Phase 56：Real Windows screenshot pipeline with pixel guard。
- Phase 57：Real UIA control tree and semantic locator。
- Phase 58：Real SendInput action path with target guard。
- Phase 59：ClaudeCode-style session context and AppState。
- Phase 60：Approval UX and persistent grants。
- Phase 61：Global abort, hotkey, cleanup, and streaming hooks。
- Phase 62：High-level Computer Tool API and streaming integration。
- Phase 63：External agent controller takeover and debug surface。
- Phase 64：Final parity plus production matrix。

## 核心边界

- 本轮只创建书面蓝图，不修改运行时代码。
- 后续执行必须由用户确认后开始。
- 未经用户明确确认，不安装系统依赖、不写注册表、不改 Windows 安全设置。
- fake provider 验收只能声明 contract passed，不能声明 real native passed。
- 每个运行时代码阶段最终必须通过自动化测试和 `start_oauth_agent.bat` 真实可见终端交互验收。

## 设计意图

Phase 53-64 不只是补齐 ClaudeCode 架构差距，还要把 learning_agent 做成 Windows-first 的 OS Computer Use：真实安全窗口截图、真实 UIA 控件树、受控 SendInput、强 action evidence、全局 cleanup、外部 agent controller 接管、最终可复验 production matrix。
