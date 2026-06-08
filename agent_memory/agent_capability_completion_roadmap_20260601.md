# Agent Capability Completion Roadmap 2026-06-01

## Goal

本轮计划目标是补齐 `learning_agent` 与 ClaudeCode 类成熟 agent 的关键差距：生产级 Chrome extension/native host 生态、配对和 session sync、高层浏览器工具、全局 StreamingToolExecutor、Windows OS 级 Computer Use、类似 `/chrome` 的终端状态 UI、真实端到端验收。

## Scope

只先生成主控书面计划，不直接改运行时代码。后续每个阶段都必须单独写 TDD 子计划，再进入实现。

## Plan File

- `docs/superpowers/plans/2026-06-01-agent-capability-completion-roadmap.md`

## Learning Copy

- `learning_agent/test/agent_capability_completion_20260601/plan.md`

## Required Execution Order

1. Chrome extension installer/native host registry.
2. Pairing and session sync.
3. High-level browser tools.
4. Global StreamingToolExecutor.
5. Windows Computer Use.
6. `/chrome` terminal status UI.
7. Real end-to-end acceptance matrix.

## Non-Negotiable Gates

- 不保存明文密码。
- 不静默写注册表。
- 不静默降级真实 Chrome provider。
- 不把 CLI/selftest/stdin 当作真实可见终端验收。
- 每阶段完成都必须自动化测试、学习备份、agent_memory 记录、真实可见终端验收和独立 verifier 复验。

