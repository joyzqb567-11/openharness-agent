# Browser Dual Track Stage 10 Fallback Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make browser provider fallback and repeated failure recovery auditable, conservative, and aligned with the dual-track blueprint.

**Architecture:** Stage 10 keeps the unified `browser_*` tool surface, but tightens the server-side routing gate so current Chrome/login-state tasks cannot silently fall back when the Chrome extension path is unavailable. Browser action failures gain a small consecutive-failure budget, and stale tab-context errors explicitly instruct the agent to refresh `browser_tabs_context`.

**Tech Stack:** Python standard library, `unittest`, existing `BrowserProviderRouter`, `BrowserAutomationServer`, `BrowserRuntimeStore`, and acceptance controller verifier.

---

## File Structure

- Modify: `learning_agent/browser_automation_mcp_server.py`
  - Stop hard-coded CDP fallback.
  - Block `BrowserProviderKind.UNAVAILABLE` before any fallback handler executes.
  - Track consecutive browser tool failures and stop after the configured budget.
  - Reset failure budget after a successful browser action.
  - Make stale `browser_tabs_context` errors explicitly request context refresh.
- Modify: `learning_agent/browser/runtime_events.py`
  - Add a stable browser recovery/fallback stop event name for future status watchers.
- Test: `learning_agent/tests/test_browser_fallback_recovery_stage10.py`
  - Cover no silent fallback, explicit CDP fallback, unavailable provider blocking, stale tab-context message, and consecutive failure budget.
- Create: `learning_agent/acceptance_controller/scenarios/browser_fallback_recovery_stage10_acceptance.json`
  - Run the Stage 10 unit test through the visible-terminal acceptance controller path.
- Backup: `learning_agent/test/browser_dual_track_stage10_20260601/plan.md`
  - Store this plan for later user review and learning.
- Backup: `learning_agent/test/browser_dual_track_stage10_20260601/modified_snippets.md`
  - Store the final modified-code summary after implementation.

---

### Task 1: Write Stage 10 Failing Tests

**Files:**
- Create: `learning_agent/tests/test_browser_fallback_recovery_stage10.py`

- [ ] **Step 1: Add tests for fallback and failure gates**

```python
"""Stage 10 fallback and recovery tests for browser dual-track runtime."""  # 新增代码+BrowserFallbackStage10: 说明本文件锁定浏览器降级和失败停止策略；若没有这行代码，测试文件职责不清楚。

from __future__ import annotations  # 新增代码+BrowserFallbackStage10: 延迟解析类型注解；若没有这行代码，旧 Python 解析前向类型时更容易出错。

import tempfile  # 新增代码+BrowserFallbackStage10: 创建隔离工作区；若没有这行代码，测试会污染真实项目目录。
import unittest  # 新增代码+BrowserFallbackStage10: 使用项目现有 unittest 风格；若没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+BrowserFallbackStage10: 处理临时工作区路径；若没有这行代码，路径拼接会变成脆弱字符串。

from learning_agent.browser.providers import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserFallbackStage10: 导入 provider 决策模型；若没有这行代码，测试无法构造路由和阻断场景。
from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserFallbackStage10: 导入真实 server；若没有这行代码，只能测 router，不能证明工具入口已接管。


class BrowserFallbackRecoveryStage10Tests(unittest.TestCase):  # 新增代码+BrowserFallbackStage10: 定义 Stage 10 测试集合；若没有这个类，unittest 无法发现测试。
    def make_server(self) -> BrowserAutomationServer:  # 新增代码+BrowserFallbackStage10: 创建隔离 server；若没有这行代码，每个测试都要重复搭建工作区。
        temp_dir = tempfile.TemporaryDirectory()  # 新增代码+BrowserFallbackStage10: 创建临时目录对象；若没有这行代码，测试会写入真实工作区。
        self.addCleanup(temp_dir.cleanup)  # 新增代码+BrowserFallbackStage10: 测试结束自动清理目录；若没有这行代码，临时文件会残留。
        return BrowserAutomationServer(Path(temp_dir.name))  # 新增代码+BrowserFallbackStage10: 返回使用临时工作区的 server；若没有这行代码，测试拿不到被测对象。

    def install_health(self, server: BrowserAutomationServer) -> None:  # 新增代码+BrowserFallbackStage10: 注入稳定 provider 健康状态；若没有这行代码，测试会依赖本机浏览器真实状态。
        server.browser_provider_registry.all_health = lambda: {  # 新增代码+BrowserFallbackStage10: 用 lambda 覆盖健康读取；若没有这行代码，测试无法稳定模拟插件断开。
            BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_disconnected"),  # 新增代码+BrowserFallbackStage10: 模拟插件不可用；若没有这行代码，降级规则不会触发。
            BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP, "cdp_ready"),  # 新增代码+BrowserFallbackStage10: 模拟 CDP 可作为候选；若没有这行代码，无法区分候选和不可用。
            BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM, "visible_ready"),  # 新增代码+BrowserFallbackStage10: 模拟公开网页轨道可用；若没有这行代码，默认公开网页路由不稳定。
        }  # 新增代码+BrowserFallbackStage10: 结束健康状态字典；若没有这行代码，Python 语法不完整。

    def test_current_chrome_task_does_not_silently_allow_cdp_fallback(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证真实 Chrome 场景不会静默降级；若没有这行代码，server 可能继续把 allow_cdp_fallback 写死为 True。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        self.install_health(server)  # 新增代码+BrowserFallbackStage10: 注入插件断开但 CDP 可用状态；若没有这行代码，测试不稳定。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制模拟当前 Chrome/登录态任务；若没有这行代码，router 会按公开网页处理。
        decision = server._decide_browser_provider_for_tool("browser_click", {"selector": "#login"})  # 新增代码+BrowserFallbackStage10: 调用真实 server 路由入口；若没有这行代码，无法发现工具入口硬编码降级。
        self.assertEqual(decision.provider, BrowserProviderKind.UNAVAILABLE)  # 新增代码+BrowserFallbackStage10: 断言未确认时不可执行；若没有这行代码，静默 CDP 降级会漏网。
        self.assertEqual(decision.fallback_provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserFallbackStage10: 断言 CDP 只是候选；若没有这行代码，用户不知道可选修复路径。
        self.assertTrue(decision.requires_user_confirmation)  # 新增代码+BrowserFallbackStage10: 断言必须用户确认；若没有这行代码，高风险降级门禁不成立。

    def test_current_chrome_task_allows_cdp_only_when_explicitly_confirmed(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证显式允许时才走 CDP；若没有这行代码，确认开关可能失效。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        self.install_health(server)  # 新增代码+BrowserFallbackStage10: 注入稳定 provider 健康状态；若没有这行代码，测试依赖真实环境。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制模拟登录态任务；若没有这行代码，降级规则不会进入插件分支。
        decision = server._decide_browser_provider_for_tool("browser_click", {"selector": "#login", "allow_cdp_fallback": True})  # 新增代码+BrowserFallbackStage10: 带显式降级确认调用路由；若没有这行代码，授权分支没有覆盖。
        self.assertEqual(decision.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserFallbackStage10: 断言确认后才选择 CDP；若没有这行代码，授权降级结果不明确。
        self.assertEqual(decision.reason_code, "extension_unavailable_cdp_fallback_allowed")  # 新增代码+BrowserFallbackStage10: 断言原因码稳定；若没有这行代码，外部 agent 难以审计。

    def test_unavailable_provider_blocks_fallback_handler(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证 unavailable 决策不会继续执行旧 handler；若没有这行代码，路由阻断只是纸面结果。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        decision = BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason="插件不可用，需要用户确认", tool_name="browser_click", fallback_provider=BrowserProviderKind.REAL_CHROME_CDP, requires_user_confirmation=True)  # 新增代码+BrowserFallbackStage10: 构造不可用决策；若没有这行代码，阻断分支没有输入。
        handler = server._provider_handler_for_tool(decision, "browser_click", lambda _arguments: "should not run")  # 新增代码+BrowserFallbackStage10: 请求 server 包装 handler；若没有这行代码，无法验证实际执行入口。
        with self.assertRaises(RuntimeError) as caught:  # 新增代码+BrowserFallbackStage10: 捕获预期阻断异常；若没有这行代码，测试无法检查错误内容。
            handler({})  # 新增代码+BrowserFallbackStage10: 执行包装后 handler；若没有这行代码，阻断逻辑不会运行。
        self.assertIn("插件不可用", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言错误说明原始原因；若没有这行代码，用户可能只看到泛化失败。
        self.assertIn("allow_cdp_fallback=true", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言提示显式确认参数；若没有这行代码，用户不知道如何安全降级。

    def test_tabs_context_contract_requests_refresh_when_stale(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证旧 tab context 会要求刷新；若没有这行代码，模型可能继续复用失效 context。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制进入真实 Chrome context 门禁；若没有这行代码，写动作不会被检查。
        server._tabs_context_is_valid = lambda: False  # 新增代码+BrowserFallbackStage10: 模拟 context 已失效；若没有这行代码，测试无法稳定触发错误。
        server.tabs_context_last_reason = "active tab 已变化"  # 新增代码+BrowserFallbackStage10: 设置失效原因；若没有这行代码，错误文案没有可断言内容。
        with self.assertRaises(RuntimeError) as caught:  # 新增代码+BrowserFallbackStage10: 捕获预期门禁异常；若没有这行代码，测试无法检查提示。
            server._enforce_tabs_context_contract("browser_click")  # 新增代码+BrowserFallbackStage10: 执行写动作门禁；若没有这行代码，刷新提示不会生成。
        self.assertIn("重新调用 browser_tabs_context", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言明确要求重读 context；若没有这行代码，模型下一步可能猜错。

    def test_consecutive_failure_budget_stops_after_three_failures(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证连续失败刹车；若没有这行代码，浏览器任务可能在坏页面上反复乱试。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        first = server._record_browser_tool_failure("browser_click", RuntimeError("fail-1"))  # 新增代码+BrowserFallbackStage10: 记录第一次失败；若没有这行代码，预算不会推进。
        second = server._record_browser_tool_failure("browser_click", RuntimeError("fail-2"))  # 新增代码+BrowserFallbackStage10: 记录第二次失败；若没有这行代码，无法验证临界前状态。
        third = server._record_browser_tool_failure("browser_click", RuntimeError("fail-3"))  # 新增代码+BrowserFallbackStage10: 记录第三次失败；若没有这行代码，停止条件不会触发。
        self.assertFalse(first["stop_required"])  # 新增代码+BrowserFallbackStage10: 第一次失败不立刻停止；若没有这行代码，恢复策略会过早中断。
        self.assertFalse(second["stop_required"])  # 新增代码+BrowserFallbackStage10: 第二次失败仍允许上层恢复；若没有这行代码，2-3 次预算语义不清。
        self.assertTrue(third["stop_required"])  # 新增代码+BrowserFallbackStage10: 第三次失败必须停止；若没有这行代码，连续失败刹车没有被锁定。
        server._reset_browser_tool_failure_budget()  # 新增代码+BrowserFallbackStage10: 模拟成功动作后复位预算；若没有这行代码，恢复后仍会误报连续失败。
        self.assertEqual(server.browser_consecutive_failure_count, 0)  # 新增代码+BrowserFallbackStage10: 断言复位成功；若没有这行代码，成功动作后仍可能被旧失败状态拖累。


if __name__ == "__main__":  # 新增代码+BrowserFallbackStage10: 支持直接运行测试文件；若没有这行代码，人工调试需要额外命令格式。
    unittest.main()  # 新增代码+BrowserFallbackStage10: 启动 unittest；若没有这行代码，直接运行文件不会执行测试。
```

- [ ] **Step 2: Run tests and confirm they fail before implementation**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10
```

Expected: FAIL because `_decide_browser_provider_for_tool` still hard-codes CDP fallback, unavailable provider decisions still fall through to fallback handlers, and failure-budget helpers do not exist.

---

### Task 2: Implement Conservative Fallback Gate

**Files:**
- Modify: `learning_agent/browser_automation_mcp_server.py`

- [ ] **Step 1: Change `_decide_browser_provider_for_tool`**

Implementation rule:
- Read `allow_cdp_fallback` only when the tool arguments contain boolean `True`.
- Keep current Chrome/login-state intent when `tabs_context` contract applies.
- Do not allow string `"true"` to bypass the gate.

Expected core change:

```python
allow_cdp_fallback = arguments.get("allow_cdp_fallback") is True  # 修改代码+BrowserFallbackStage10: 只有布尔 True 才允许登录态任务降级到 CDP；若没有这行代码，插件不可用时会继续静默走 CDP。
return self.browser_provider_router.decide_provider(user_input=router_input, tool_name=tool_name, arguments=arguments, provider_health=self.browser_provider_registry.all_health(), allow_cdp_fallback=allow_cdp_fallback)  # 修改代码+BrowserFallbackStage10: 把显式确认传给 router；若没有这行代码，server 入口会覆盖 router 的安全默认值。
```

- [ ] **Step 2: Change `_provider_handler_for_tool`**

Implementation rule:
- If decision provider is `UNAVAILABLE`, return a handler that raises a user-readable `RuntimeError`.
- Include original reason, optional fallback provider, and exact confirmation hint.
- Do not call `fallback_handler` in this branch.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10
```

Expected: some tests still fail until failure budget is implemented.

---

### Task 3: Implement Consecutive Failure Budget

**Files:**
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Modify: `learning_agent/browser/runtime_events.py`

- [ ] **Step 1: Add failure-budget fields in `BrowserAutomationServer.__init__`**

Add:
- `browser_consecutive_failure_count = 0`
- `browser_consecutive_failure_limit = 3`
- `browser_recent_failures = []`

- [ ] **Step 2: Add helper methods**

Add:
- `_record_browser_tool_failure(tool_name, error)`
- `_reset_browser_tool_failure_budget()`
- `_raise_if_browser_failure_budget_exhausted(tool_name, error_text)`

Behavior:
- Every failed top-level browser tool increments the counter.
- Successful top-level browser tool resets it.
- At limit, raise a clearer `RuntimeError` telling the agent to stop, inspect status/logs, and refresh/recover manually.

- [ ] **Step 3: Wire helpers into `call()`**

Implementation rule:
- Reset after successful `execute_action`.
- Record and maybe stop in the exception path around `execute_action`.
- Keep the original exception as `from error` so debugging keeps the root cause.

- [ ] **Step 4: Add runtime event constant**

Add `BROWSER_RECOVERY_STOPPED = "browser_recovery_stopped"` to `learning_agent/browser/runtime_events.py` and include it in `BROWSER_RUNTIME_EVENT_TYPES`.

---

### Task 4: Improve Tab Context Refresh Messaging

**Files:**
- Modify: `learning_agent/browser_automation_mcp_server.py`

- [ ] **Step 1: Update `_enforce_tabs_context_contract` error**

The error must include:
- `重新调用 browser_tabs_context`
- stale reason
- avoid continuing click/type/key/upload until refreshed

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10
```

Expected: all Stage 10 tests pass.

---

### Task 5: Add Acceptance Scenario and Backups

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/browser_fallback_recovery_stage10_acceptance.json`
- Create: `learning_agent/test/browser_dual_track_stage10_20260601/modified_snippets.md`

- [ ] **Step 1: Create acceptance scenario**

The scenario must run:

```powershell
python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10
```

The final answer marker must include:

```text
BROWSER_FALLBACK_RECOVERY_STAGE10_READY STAGE10_FALLBACK_RECOVERY_OK
```

- [ ] **Step 2: Back up changed snippets**

The backup must list:
- modified server fallback gate
- failure-budget helpers
- runtime event constant
- test file
- acceptance scenario

---

### Task 6: Verification

- [ ] **Step 1: Run focused tests**

```powershell
python -m unittest learning_agent.tests.test_browser_fallback_recovery_stage10
```

- [ ] **Step 2: Run related regression tests**

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tabs_context_stage4 learning_agent.tests.test_browser_recovery learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8
```

- [ ] **Step 3: Run py_compile**

```powershell
python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\browser\runtime_events.py learning_agent\tests\test_browser_fallback_recovery_stage10.py
```

- [ ] **Step 4: Run full unit suite**

```powershell
python -m unittest discover -s learning_agent\tests
```

- [ ] **Step 5: Run acceptance controller scenario**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\browser_fallback_recovery_stage10_acceptance.json'
```

- [ ] **Step 6: Run acceptance verifier**

```powershell
python -m learning_agent.acceptance.verifier '<run_dir>' 'H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\browser_fallback_recovery_stage10_acceptance.json'
```

Expected:
- Unit tests pass.
- Related regression tests pass.
- Full suite passes.
- Controller reports `ACCEPTANCE_CONTROLLER_COMPLETED=True`.
- Verifier reports `completed=true` and `assertion.passed=true`.

---

## Success Criteria

1. Current Chrome/login-state browser write tasks do not silently fall back to CDP.
2. CDP fallback works only when `allow_cdp_fallback` is boolean `True`.
3. `UNAVAILABLE` provider decisions block the actual tool handler.
4. Stale tabs context tells the agent to call `browser_tabs_context` again.
5. Three consecutive browser tool failures stop with a clear recovery message.
6. Stage 10 unit tests, related regressions, full tests, controller, and verifier all pass.

