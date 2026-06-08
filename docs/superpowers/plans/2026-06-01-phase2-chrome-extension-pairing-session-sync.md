# Phase 2 Chrome Extension Pairing Session Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development.

**Goal:** 让 Chrome extension/native host 保存非敏感配对信息，并能把浏览器侧 prompt 推入 `RuntimeCommandQueue`。

**Architecture:** 扩展 bridge state 继续作为连接状态中心；pairing store 负责脱敏持久化；browser prompt push 只写 durable queue，不直接绕过主循环。

**Tech Stack:** Python standard library, unittest, existing `ChromeExtensionBridgeState`, existing `RuntimeCommandQueue`.

---

## Tasks

- [ ] 写红灯测试：配对记录脱敏、session sync 状态、browser prompt 入 durable queue。
- [ ] 扩展 pairing store，新增 `save_pairing()` 和 `pairing_summary()`。
- [ ] 扩展 bridge state，新增 `record_pairing()`、`enqueue_browser_prompt()`、`session_sync_status_text()`。
- [ ] 扩展 host protocol，接受 `pair_device` 和 `browser_prompt`。
- [ ] 运行聚焦测试、相关扩展测试、py_compile。
- [ ] 备份新增/修改代码到 `learning_agent/test/agent_capability_completion_20260601/phase2/`。

