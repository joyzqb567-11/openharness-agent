# Browser Dual Track Stage 1 修改备份

日期：2026-06-01

## 本阶段目标

Stage 1 只建立 Provider Protocol、Router、Registry 和 provider decision 事件，不改变现有浏览器执行路径。

## 新增文件

1. `learning_agent/browser/providers/__init__.py`
   - 导出 `BrowserProviderDecision`、`BrowserProviderHealth`、`BrowserProviderKind`、`BrowserProviderRegistry`、`BrowserProviderRouter`。
2. `learning_agent/browser/providers/protocol.py`
   - 定义 provider 类型、健康状态和路由决策对象。
3. `learning_agent/browser/providers/router.py`
   - 定义 `BrowserProviderRouter.decide_provider(...)`，实现公开网页、当前 Chrome 登录态、CDP 调试、本地开发和插件不可用降级规则。
4. `learning_agent/browser/providers/registry.py`
   - 定义 `BrowserProviderRegistry`，未注册 provider 默认返回不可用。
5. `learning_agent/browser/providers/provider_events.py`
   - 定义 provider decision 事件 payload helper。
6. `learning_agent/tests/test_browser_provider_router.py`
   - 覆盖 Stage 1 路由规则、事件注册和 registry 缺省不可用行为。
7. `learning_agent/acceptance_controller/scenarios/browser_provider_router_stage1_acceptance.json`
   - 新增真实可见终端验收场景，要求终端里的 agent 调用 bash 执行 Python 命令，验证 provider router 协议层和 event payload。

## 修改文件

1. `learning_agent/browser/runtime_events.py`
   - 新增 `BROWSER_PROVIDER_DECISION = "browser_provider_decision"`。
   - 将 `BROWSER_PROVIDER_DECISION` 加入 `BROWSER_RUNTIME_EVENT_TYPES`。
2. `learning_agent/browser/__init__.py`
   - 从 browser 包入口导出 provider 路由协议、注册表和路由器。

## 关键规则

1. 公开网页和普通查询默认选择 `visible_chromium`。
2. 当前 Chrome、登录态、现有标签页、OAuth 任务优先选择 `chrome_extension`。
3. 插件不可用时，如果没有明确允许降级，返回 `unavailable`，并把 `real_chrome_cdp` 作为候选 fallback。
4. 显式 CDP、调试端口、`browser_connect_real_chrome` 请求选择 `real_chrome_cdp`。
5. 本地开发、localhost、127.0.0.1、file 页面选择 `visible_chromium`。
6. 模型仍然只面对统一 `browser_*` 工具，不新增 `chrome_extension_open` 或 `cdp_real_chrome_open`。

## 自动化测试

代码质量评审后补充修复：

1. `BrowserProviderRouter` 复用 `learning_agent/browser/intent.py` 的真实浏览器关键词，并补齐当前浏览器、真实浏览器、真实 Chrome、current browser、login state 等触发词。
2. `BrowserProviderDecision.to_event_payload()` 新增 `schema_version=1`、稳定 `reason_code` 和 JSON 安全 `metadata`。
3. 插件不可用且允许 CDP fallback 时，事件记录 `fallback_from=chrome_extension`；未允许 fallback 时，仍返回 `unavailable` 并要求确认。
4. `provider_events.build_provider_decision_event()`、`BrowserProviderRegistry.set_health()` 和 `BrowserProviderRegistry.all_health()` 已补测试。

评审修复后 fresh 运行：

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

结果：

```text
Ran 12 tests in 0.000s
OK
```

评审修复后 fresh 运行：

```powershell
python -m py_compile .\learning_agent\browser\providers\__init__.py .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\router.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\provider_events.py .\learning_agent\browser\runtime_events.py .\learning_agent\browser\__init__.py .\learning_agent\tests\test_browser_provider_router.py
```

结果：退出码 0。

评审修复后 fresh 运行：

```powershell
python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router
```

结果：

```text
Ran 33 tests in 0.194s
OK
```

评审修复后 fresh 运行：

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：

```text
Ran 502 tests in 18.236s
OK (skipped=1)
```

已运行：

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

结果：

```text
Ran 7 tests in 0.000s
OK
```

已运行：

```powershell
python -m py_compile .\learning_agent\browser\providers\__init__.py .\learning_agent\browser\providers\protocol.py .\learning_agent\browser\providers\router.py .\learning_agent\browser\providers\registry.py .\learning_agent\browser\providers\provider_events.py .\learning_agent\browser\runtime_events.py .\learning_agent\browser\__init__.py .\learning_agent\tests\test_browser_provider_router.py
```

结果：退出码 0。

已运行：

```powershell
python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_provider_router
```

结果：

```text
Ran 28 tests in 0.220s
OK
```

已运行：

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：

```text
Ran 497 tests in 20.571s
OK (skipped=1)
```

## 真实可见终端验收

已完成 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收。

验收场景：

```text
learning_agent/acceptance_controller/scenarios/browser_provider_router_stage1_acceptance.json
```

controller run：

```text
learning_agent/acceptance_controller/runs/browser_provider_router_stage1_acceptance-20260601_165755
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
PROVIDER_ROUTER_STAGE1_OK provider=real_chrome_cdp reason_code=extension_unavailable_cdp_fallback_allowed schema_version=1 fallback_from=chrome_extension
```

独立 verifier 复验：

```powershell
python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_provider_router_stage1_acceptance-20260601_165755 .\learning_agent\acceptance_controller\scenarios\browser_provider_router_stage1_acceptance.json
```

结果：

```text
schema_version=2
completed=true
assertion.passed=true
artifact_checks=true
```

按照项目门禁，Stage 1 已满足“代码修改完成 + 自动化测试通过 + start_oauth_agent.bat 可见终端交互测试通过”。

## 最终收口记录

最终 fresh 自动化验证：

```powershell
python -m json.tool .\learning_agent\acceptance_controller\scenarios\browser_provider_router_stage1_acceptance.json > $null
```

结果：通过。

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router
```

结果：

```text
Ran 12 tests in 0.001s
OK
```

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：

```text
Ran 502 tests in 21.123s
OK (skipped=1)
```

代码质量复审结论：通过。

复审确认：

1. `BrowserProviderRouter` 已复用 `REAL_CHROME_INTENT_KEYWORDS`，并排除普通可见浏览器表达，降低误选插件路线风险。
2. CDP fallback 只在 `allow_cdp_fallback=True` 时执行，并记录 `metadata.fallback_from=chrome_extension`。
3. event payload 已包含 `schema_version=1`、`reason_code` 和 JSON 安全 `metadata`。
4. `provider_events` helper 和 registry 写入/快照路径均已有测试覆盖。
