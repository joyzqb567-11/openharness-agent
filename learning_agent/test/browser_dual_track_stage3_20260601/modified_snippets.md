# Browser Dual Track Stage 3 修改备份

日期：2026-06-01

## 本阶段目标

Stage 3 把“双轨底层、单轨模型表面”落成可测试门禁：模型只看到统一 `browser_*` 工具，provider-specific 重复动作不会进入模型 catalog，真实 Chrome 控制入口会标记为 `advanced provider-control`，底层 provider 选择由 `BrowserProviderRouter` 写入 event log。

## 新增文件

1. `learning_agent/browser/providers/tool_surface.py`
   - 新增 provider-specific 工具识别、provider-control 工具识别和工具表面提示 helper。
2. `learning_agent/tests/test_browser_tool_surface_stage3.py`
   - 覆盖统一工具清单、provider-specific 过滤、advanced/provider-control 标记、skill/harness 单轨提示、provider decision 事件。
3. `learning_agent/acceptance_controller/scenarios/browser_tool_surface_stage3_acceptance.json`
   - 新增真实可见终端验收场景。
4. `docs/superpowers/plans/2026-06-01-browser-dual-track-stage3-tool-surface.md`
   - 新增 Stage 3 书面计划。
5. `learning_agent/test/browser_dual_track_stage3_20260601/plan.md`
   - 备份 Stage 3 计划。

## 修改文件

1. `learning_agent/browser/providers/__init__.py`
   - 导出 `browser_tool_surface_hint`、`is_provider_control_tool_name`、`is_provider_specific_tool_name`、`normalized_browser_tool_name`。
2. `learning_agent/mcp/runtime.py`
   - `agent_tools()` 过滤 provider-specific 重复动作。
   - 真实 Chrome 控制工具的 `search_hint` 增加 `advanced provider-control`。
3. `learning_agent/skills/browser_automation/SKILL.md`
   - 明确模型不要直接选择 provider，只调用统一 `browser_*` 工具。
4. `learning_agent/skills/real_chrome/SKILL.md`
   - 明确真实 Chrome 路线也不让模型发明 provider-specific 工具。
5. `learning_agent/browser/harness.py`
   - 在真实 Chrome 和可见浏览器短 prompt harness 中加入 `BrowserProviderRouter` 单轨规则。
6. `agent_memory/bugs.md`
   - 记录 Stage 2 风险关闭和 Stage 3 后续关注。

## 红灯测试

首次运行：

```powershell
python -m unittest learning_agent.tests.test_browser_tool_surface_stage3
```

结果：

```text
FAILED (failures=2, errors=2)
ModuleNotFoundError: No module named 'learning_agent.browser.providers.tool_surface'
AssertionError: 'advanced' not found in ''
AssertionError: 'BrowserProviderRouter' not found in ...
```

## 自动化验证

```powershell
python -m unittest learning_agent.tests.test_browser_tool_surface_stage3
```

结果：

```text
Ran 6 tests in 0.064s
OK
```

```powershell
python -m py_compile .\learning_agent\browser\providers\tool_surface.py .\learning_agent\browser\providers\__init__.py .\learning_agent\mcp\runtime.py .\learning_agent\browser\harness.py .\learning_agent\tests\test_browser_tool_surface_stage3.py
```

结果：退出码 0。

```powershell
python -m unittest learning_agent.tests.test_browser_provider_router learning_agent.tests.test_browser_provider_adapters learning_agent.tests.test_browser_tool_surface_stage3 learning_agent.tests.test_tools_policy
```

结果：

```text
Ran 105 tests in 0.430s
OK
```

```powershell
python -m unittest discover -s learning_agent\tests
```

结果：

```text
Ran 513 tests in 20.571s
OK (skipped=1)
```

## 真实可见终端验收

验收场景：

```text
learning_agent/acceptance_controller/scenarios/browser_tool_surface_stage3_acceptance.json
```

controller run：

```text
learning_agent/acceptance_controller/runs/browser_tool_surface_stage3_acceptance-20260601_172518
```

结果：

```text
completed=true
assertion.passed=true
permission_sent_count=0
```

真实终端里的 agent 调用 bash 后输出：

```text
Ran 6 tests
OK
BROWSER_TOOL_SURFACE_STAGE3_READY STAGE3_TOOL_SURFACE_OK
```

独立 verifier 输出：

```text
schema_version=2
completed=true
assertion.passed=true
artifact_checks=true
```

## 剩余风险

1. Stage 3 只保证模型工具表面不分裂；`browser_tabs_context` 合同尚未实现。
2. Chrome 插件 provider、native host、站点权限和 GIF 证据仍在后续 Stage 5-9。
3. 未来如果外部 MCP server 暴露 provider-specific 动作，当前模型 catalog 会过滤，但内部 provider adapter 仍需在独立 provider 层接入。
