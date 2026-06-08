# Phase 1 Chrome Extension Installer Native Host Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development.

**Goal:** 给 `learning_agent` 增加生产级 Chrome native host 安装状态、dry-run 注册表适配器、可回滚安装/卸载入口和清晰修复建议。

**Architecture:** 先在 `manifest_installer.py` 内补齐安全抽象，不默认写真实注册表；测试使用 fake registry adapter。后续真实写注册表必须由调用方显式传入 `dry_run=False`，并且会返回 audit record。

**Tech Stack:** Python standard library, unittest, Windows registry path conventions, existing Chrome extension host files.

---

## Tasks

- [ ] 写红灯测试：证明当前缺少 install/status/uninstall/dry-run registry lifecycle。
- [ ] 实现 `NativeHostRegistryAdapter`、`MemoryNativeHostRegistryAdapter`、`WindowsNativeHostRegistryAdapter`。
- [ ] 实现 `ChromeNativeHostInstaller`，支持 `status()`、`install()`、`uninstall()`、`repair_hint()`。
- [ ] 保持 `build_native_host_manifest()` 兼容旧调用。
- [ ] 运行聚焦测试、相关扩展测试、py_compile。
- [ ] 备份新增/修改代码到 `learning_agent/test/agent_capability_completion_20260601/phase1/`。

