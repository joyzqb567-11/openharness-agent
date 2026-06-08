# Browser Dual Track Stage 2 Provider Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有可见 Chromium / Playwright 能力和真实 Chrome CDP 能力迁入 provider adapter，同时保持模型表面只看到统一 `browser_*` 工具。

**Architecture:** Stage 2 不写 Chrome 插件，也不新增 provider-specific 工具名。`BrowserAutomationServer.call()` 在顶层浏览器工具调用时先通过 `BrowserProviderRouter` 做决策、写 `browser_provider_decision` 事件，再把已存在的工具 handler 委托给 `VisibleChromiumProvider` 或 `RealChromeCdpProvider` adapter；adapter 只包裹现有 server 方法，避免一次性重写浏览器执行逻辑。

**Tech Stack:** Python、unittest、BrowserRuntimeStore、BrowserProviderRouter、PowerShell acceptance controller、`learning_agent/start_oauth_agent.bat` 真实可见终端验收。

---

## 0. Stage 2 边界

Stage 2 只做这些事情：

1. 新增 provider 执行接口和 adapter。
2. 把 `browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_tabs`、`browser_console`、`browser_network`、`browser_upload_file`、`browser_downloads`、`browser_evaluate`、`browser_close`、`browser_recover_page`、`browser_visual_locate`、`browser_flow_run`、`browser_replay`、`browser_plugin_status`、`browser_site_grant` 等现有可见 Chromium / Playwright 工具委托给 `VisibleChromiumProvider`。
3. 把 `browser_connect_real_chrome`、`browser_disconnect_real_chrome`、`browser_profile_status` 委托给 `RealChromeCdpProvider`。
4. 每个顶层工具调用写入 `browser_provider_decision` 事件。
5. 工具名、schema、返回文本保持兼容。

Stage 2 不做这些事情：

1. 不新增 Chrome 插件。
2. 不安装 native host。
3. 不实现 `browser_tabs_context` 强制合同。
4. 不新增 `chrome_extension_open`、`real_chrome_cdp_open`、`visible_chromium_open` 这类重复工具。
5. 不改变真实 Chrome 高风险确认参数。

## 1. 文件结构

Create:

- `learning_agent/browser/providers/visible_chromium.py`
- `learning_agent/browser/providers/real_chrome_cdp.py`
- `learning_agent/tests/test_browser_provider_adapters.py`
- `learning_agent/acceptance_controller/scenarios/browser_provider_adapters_stage2_acceptance.json`
- `learning_agent/test/browser_dual_track_stage2_20260601/modified_snippets.md`

Modify:

- `learning_agent/browser/providers/protocol.py`
- `learning_agent/browser/providers/registry.py`
- `learning_agent/browser/providers/__init__.py`
- `learning_agent/browser_automation_mcp_server.py`
- `agent_memory/progress.md`
- `agent_memory/bugs.md`

## 2. 成功标准

Stage 2 完成后必须满足：

1. `VisibleChromiumProvider.kind` 返回 `visible_chromium`。
2. `RealChromeCdpProvider.kind` 返回 `real_chrome_cdp`。
3. provider adapter 能调用 server 现有 handler，保持原返回文本。
4. `BrowserAutomationServer.call("browser_open", ...)` 会通过 provider adapter 执行。
5. `BrowserAutomationServer.call("browser_connect_real_chrome", ...)` 会通过 CDP provider adapter 执行。
6. 顶层浏览器工具 run 的 event log 中存在 `browser_provider_decision`。
7. 现有 browser 单测和全量单测不退化。
8. `start_oauth_agent.bat` 真实可见终端验收通过。

## 3. Task 1：红灯测试

**Files:**

- Create: `learning_agent/tests/test_browser_provider_adapters.py`

- [ ] **Step 1: 写 provider adapter 测试**

测试必须覆盖：

1. `VisibleChromiumProvider` 委托 `browser_open`。
2. `RealChromeCdpProvider` 委托 `browser_connect_real_chrome`。
3. `BrowserProviderRegistry.register_provider()` 能从 provider 读取健康状态。
4. `BrowserAutomationServer.call()` 通过 provider adapter 执行 `browser_wait`。
5. `BrowserAutomationServer.call()` 写入 `browser_provider_decision` event。

- [ ] **Step 2: 运行红灯测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_adapters
```

Expected:

```text
ModuleNotFoundError 或 AttributeError，指向 provider adapter 尚不存在
```

## 4. Task 2：扩展 Provider Protocol 和 Registry

**Files:**

- Modify: `learning_agent/browser/providers/protocol.py`
- Modify: `learning_agent/browser/providers/registry.py`

- [ ] **Step 1: 新增 `BrowserProvider` Protocol**

协议最小包含：

```python
class BrowserProvider(Protocol):
    @property
    def kind(self) -> BrowserProviderKind: ...
    def health(self) -> BrowserProviderHealth: ...
    def supports_tool(self, tool_name: str) -> bool: ...
    def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str: ...
```

- [ ] **Step 2: registry 支持 provider 注册和查找**

新增：

```python
register_provider(provider)
provider(kind)
all_providers()
```

要求：现有 `set_health()`、`health()`、`all_health()` 测试继续通过。

## 5. Task 3：实现两个 adapter

**Files:**

- Create: `learning_agent/browser/providers/visible_chromium.py`
- Create: `learning_agent/browser/providers/real_chrome_cdp.py`
- Modify: `learning_agent/browser/providers/__init__.py`

- [ ] **Step 1: 实现 `VisibleChromiumProvider`**

该 provider 只接收 server backend，并把现有工具名委托给同名 server 方法。

- [ ] **Step 2: 实现 `RealChromeCdpProvider`**

该 provider 只支持真实 Chrome CDP 相关工具：

```text
browser_connect_real_chrome
browser_disconnect_real_chrome
browser_profile_status
```

- [ ] **Step 3: 更新 provider 包导出**

从 `learning_agent.browser.providers` 导出两个 adapter。

## 6. Task 4：接入 BrowserAutomationServer

**Files:**

- Modify: `learning_agent/browser_automation_mcp_server.py`

- [ ] **Step 1: 初始化 provider registry 和 router**

在 `BrowserAutomationServer.__init__()` 中创建：

```python
self.browser_provider_router
self.browser_provider_registry
self.visible_chromium_provider
self.real_chrome_cdp_provider
```

并注册两个 provider。

- [ ] **Step 2: 顶层 call 写 provider decision**

新增 helper：

```python
_decide_browser_provider_for_tool(...)
_record_browser_provider_decision(...)
_provider_handler_for_tool(...)
```

要求：

1. 只在顶层 call 写一次 provider decision。
2. 嵌套 `browser_flow_run` 子调用不重复创建 provider decision run 根。
3. provider 不支持工具时回退原 dispatch，但要保留事件证据。

- [ ] **Step 3: 通过 provider adapter 执行 handler**

在 `execute_action(...)` 传入的 handler 使用 provider adapter 包装后的 handler。

## 7. Task 5：自动化验证

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters
```

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters
```

Run:

```powershell
python -m unittest discover -s learning_agent\tests
```

## 8. Task 6：真实可见终端验收

**Files:**

- Create: `learning_agent/acceptance_controller/scenarios/browser_provider_adapters_stage2_acceptance.json`

验收要求：

1. 真实终端里的 agent 调用 bash 检查 `BrowserAutomationServer.call("browser_wait", ...)`。
2. 检查 browser runtime event log 中包含 `browser_provider_decision`。
3. 最终回答包含固定标记：

```text
BROWSER_PROVIDER_ADAPTERS_STAGE2_READY
```

验收命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\browser_provider_adapters_stage2_acceptance.json
```

独立 verifier：

```powershell
python -m learning_agent.acceptance.verifier <run_dir> .\learning_agent\acceptance_controller\scenarios\browser_provider_adapters_stage2_acceptance.json
```

## 9. Task 7：备份和记录

**Files:**

- Create: `learning_agent/test/browser_dual_track_stage2_20260601/modified_snippets.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

记录内容：

1. 新增/修改文件。
2. 关键 provider adapter 行为。
3. 自动化测试结果。
4. 真实终端验收 run id。
5. Stage 2 剩余风险：只是迁入现有 Playwright/CDP，尚未实现插件 provider。
