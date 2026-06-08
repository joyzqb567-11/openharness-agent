# Browser Dual Track Stage 10 修改备份

> 本文件用于给用户学习和审计 Stage 10 改动；如果源文件后续变化，可以用这里快速理解本阶段新增了什么。

## learning_agent/browser/runtime_events.py

```python
BROWSER_RECOVERY_STOPPED = "browser_recovery_stopped"  # 新增代码+BrowserFallbackStage10: 表示连续浏览器失败已经触发停止；若没有这行代码，事件流无法审计为什么 agent 不再继续乱试。
BROWSER_RUNTIME_EVENT_TYPES = (..., BROWSER_GIF_EXPORTED, BROWSER_RECOVERY_STOPPED)  # 修改代码+BrowserFallbackStage10: 暴露全部稳定事件名并加入连续失败停止事件；若没有这行代码，CLI/API 无法确认停止保护属于正式浏览器 runtime。
```

## learning_agent/browser_automation_mcp_server.py

```python
from learning_agent.browser.providers import BrowserProviderDecision, BrowserProviderKind, ...
from learning_agent.browser.runtime_events import ..., BROWSER_RECOVERY_STOPPED
```

```python
self.browser_consecutive_failure_count = 0  # 新增代码+BrowserFallbackStage10: 记录连续顶层浏览器工具失败次数；若没有这行代码，agent 会在同类失败里一直重复尝试。
self.browser_consecutive_failure_limit = 3  # 新增代码+BrowserFallbackStage10: 设置连续失败最多三次后停止；若没有这行代码，真实浏览器卡死时可能无限消耗任务时间。
self.browser_recent_failures: list[dict[str, str | int]] = []  # 新增代码+BrowserFallbackStage10: 保存最近失败摘要给报错和审计使用；若没有这行代码，停止时用户看不到连续失败的上下文。
```

```python
allow_cdp_fallback = arguments.get("allow_cdp_fallback") is True  # 新增代码+BrowserFallbackStage10: 只有调用方显式传 true 才允许 CDP 兜底；若没有这行代码，登录态任务会被静默降级到 CDP。
router_arguments = dict(arguments)  # 新增代码+BrowserFallbackStage10: 复制参数再交给路由器判断意图；若没有这行代码，后续删除门禁字段会意外改动原工具参数。
router_arguments.pop("allow_cdp_fallback", None)  # 新增代码+BrowserFallbackStage10: 防止字段名里的 cdp 被路由器误判为用户明确要走 CDP；若没有这行代码，显式门禁会被字符串匹配绕过。
```

```python
if decision.provider == BrowserProviderKind.UNAVAILABLE:  # 新增代码+BrowserFallbackStage10: 路由明确不可用时直接阻断执行；若没有这行代码，server 会落回旧 handler 形成静默旁路。
    def unavailable_provider_handler(current_arguments: dict[str, Any]) -> str:  # 新增代码+BrowserFallbackStage10: 给执行器一个会明确失败的 handler；若没有这行代码，失败无法进入统一 action/event 记录。
        raise RuntimeError(...)  # 新增代码+BrowserFallbackStage10: 用中文说明已停止而不是降级；若没有这行代码，登录态动作可能悄悄走错轨道。
    return unavailable_provider_handler  # 新增代码+BrowserFallbackStage10: 返回阻断 handler 让统一执行器记录失败；若没有这行代码，后续仍会落入旧工具实现。
```

```python
unavailable_safe_fallback_tools = {"browser_tabs_context", "browser_tabs", "browser_provider_status", "browser_extension_status", "browser_plugin_status", "browser_profile_status"}  # 新增代码+BrowserFallbackStage10: 列出即使 provider 不可用也必须能查看的状态/上下文工具；若没有这行代码，agent 会连恢复前需要读取的状态都拿不到。
if decision.provider == BrowserProviderKind.UNAVAILABLE and tool_name in unavailable_safe_fallback_tools:  # 新增代码+BrowserFallbackStage10: 状态和上下文工具允许走旧只读实现；若没有这行代码，browser_tabs_context 会被兜底门禁误伤。
    return fallback_handler  # 新增代码+BrowserFallbackStage10: 返回安全只读 fallback handler；若没有这行代码，用户无法刷新标签页上下文来修复后续写动作。
```

```python
def _reset_browser_tool_failure_budget(self) -> None: ...
def _record_browser_tool_failure(self, tool_name: str, error: Exception | str) -> dict[str, Any]: ...
```

```python
failure_state = self._record_browser_tool_failure(name, error)  # 新增代码+BrowserFallbackStage10: 顶层失败时更新连续失败预算；若没有这行代码，连续失败三次不会停止。
if failure_state.get("stop_required"):  # 新增代码+BrowserFallbackStage10: 达到失败阈值时进入停止分支；若没有这行代码，agent 会继续重复同类浏览器失败。
    raise stop_error from error  # 新增代码+BrowserFallbackStage10: 保留原始异常链并停止继续；若没有这行代码，外部 agent 无法区分普通失败和连续失败停止。
self._reset_browser_tool_failure_budget()  # 新增代码+BrowserFallbackStage10: 顶层工具成功后清空连续失败预算；若没有这行代码，恢复成功后仍可能被旧失败熔断。
```

```python
raise RuntimeError("...请重新调用 browser_tabs_context 刷新标签页上下文，然后再执行写动作。")
```

## 新增测试与验收场景

```text
learning_agent/tests/test_browser_fallback_recovery_stage10.py
learning_agent/tests/test_browser_tabs_context_stage4.py
learning_agent/acceptance_controller/scenarios/browser_fallback_recovery_stage10_acceptance.json
```
