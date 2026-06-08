# Browser Dual Track Stage 2 修改备份

日期：2026-06-01

## 本阶段目标

Stage 2 把现有 Playwright / 可见 Chromium 能力和真实 Chrome CDP 能力迁入 provider adapter，同时保持模型表面只看到统一 `browser_*` 工具。

## 新增文件

1. `learning_agent/browser/providers/visible_chromium.py`
   - 新增 `VisibleChromiumProvider`，把 `browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_wait` 等现有工具委托给旧 `BrowserAutomationServer` handler。
2. `learning_agent/browser/providers/real_chrome_cdp.py`
   - 新增 `RealChromeCdpProvider`，把 `browser_connect_real_chrome`、`browser_disconnect_real_chrome`、`browser_profile_status` 委托给旧真实 Chrome/CDP handler。
3. `learning_agent/tests/test_browser_provider_adapters.py`
   - 覆盖 provider adapter 委托、registry provider 注册、server 顶层 provider handler、provider decision 事件写入。
4. `learning_agent/acceptance_controller/scenarios/browser_provider_adapters_stage2_acceptance.json`
   - 新增真实可见终端验收场景。

## 修改文件

1. `learning_agent/browser/providers/protocol.py`
   - 新增 `BrowserProvider` Protocol，定义 `kind`、`health()`、`supports_tool()`、`execute_tool()`。
2. `learning_agent/browser/providers/registry.py`
   - 新增 `register_provider()`、`provider()`、`all_providers()`，同时保持原有 health API。
3. `learning_agent/browser/providers/__init__.py`
   - 导出 `BrowserProvider`、`VisibleChromiumProvider`、`RealChromeCdpProvider`。
4. `learning_agent/browser_automation_mcp_server.py`
   - 初始化 provider router、provider registry 和两个 adapter。
   - 顶层 `call()` 新增 provider decision。
   - 顶层 `call()` 把执行 handler 包给 provider adapter。
   - 当前嵌套 flow 子调用不重复写 provider decision。
5. `learning_agent/tests/test_browser_runtime_store.py`
   - 更新事件序列断言，加入 `browser_provider_decision`。
6. `agent_memory/progress.md`
   - 记录 Stage 2 计划、实现和验收。
7. `agent_memory/bugs.md`
   - 记录 Stage 2 剩余风险。

## 红灯测试

首次运行：

```powershell
python -m unittest learning_agent.tests.test_browser_provider_adapters
```

结果：

```text
FAILED (errors=5)
ModuleNotFoundError: No module named 'learning_agent.browser.providers.real_chrome_cdp'
ModuleNotFoundError: No module named 'learning_agent.browser.providers.visible_chromium'
AttributeError: 'BrowserProviderRegistry' object has no attribute 'register_provider'
```

## 自动化验证

```powershell
python -m unittest learning_agent.tests.test_browser_provider_adapters
```

结果：

```text
Ran 5 tests in 0.101s
OK
```

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters
```

结果：

```text
Ran 17 tests in 0.078s
OK
```

```powershell
python -m py_compile .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\visible_chromium.py .\learning_agent\browser\providers\real_chrome_cdp.py .\learning_agent\browser\providers\__init__.py .\learning_agent\browser_automation_mcp_server.py .\learning_agent\tests\test_browser_provider_adapters.py
```

结果：退出码 0。

```powershell
python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters
```

结果：

```text
Ran 38 tests in 0.214s
OK
```

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：

```text
Ran 507 tests in 18.846s
OK (skipped=1)
```

## 真实可见终端验收

验收场景：

```text
learning_agent/acceptance_controller/scenarios/browser_provider_adapters_stage2_acceptance.json
```

controller run：

```text
learning_agent/acceptance_controller/runs/browser_provider_adapters_stage2_acceptance-20260601_171446
```

结果：

```text
completed=true
assertion.passed=true
prompt_sent=true
prompt_received=true
final_printed=true
permission_sent_count=0
```

真实终端里的 agent 调用 bash 后输出：

```text
PROVIDER_ADAPTERS_STAGE2_OK provider=visible_chromium decision_event=True result_has_wait=True
```

独立 verifier 输出：

```text
schema_version=2
completed=true
assertion.passed=true
artifact_checks=true
```

## 剩余风险

1. Stage 2 只是把现有 Playwright/CDP 执行能力包进 provider adapter，还没有 Chrome 插件 provider。
2. `browser_tabs_context` 合同尚未实现，应进入 Stage 4 前单独处理。
3. 当前 provider adapter 仍委托旧 server 方法，后续阶段需要继续把权限、tabs context、插件状态、录屏证据纳入 provider 生态。
