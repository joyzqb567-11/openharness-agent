# 双轨真实浏览器实施计划摘要

日期：2026-06-01

完整计划位置：

`H:\codexworkplace\sofeware\OpenHarness-main\docs\superpowers\plans\2026-06-01-browser-dual-track-architecture-implementation.md`

## 核心执行原则

1. 先执行 Stage 1：Provider Protocol 和 BrowserProviderRouter。
2. Stage 1 不改变现有真实浏览器工具行为。
3. 模型表面只保留统一 `browser_*` 工具。
4. provider 选择只能由代码层 Router 决定。
5. 每个阶段必须单独验收，不能跳到插件大改。

## Stage 1 必须新增

1. `learning_agent/browser/providers/__init__.py`
2. `learning_agent/browser/providers/protocol.py`
3. `learning_agent/browser/providers/router.py`
4. `learning_agent/browser/providers/registry.py`
5. `learning_agent/browser/providers/provider_events.py`
6. `learning_agent/tests/test_browser_provider_router.py`

## Stage 1 验收

1. `python -m unittest learning_agent.tests.test_browser_provider_router`
2. `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router`
3. `python -m unittest discover -s learning_agent\tests`
4. `learning_agent/start_oauth_agent.bat` 真实可见终端验收。
