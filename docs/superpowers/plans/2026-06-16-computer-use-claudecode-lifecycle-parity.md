# Computer Use ClaudeCode Lifecycle Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 OpenHarness Computer Use 继续补齐到 ClaudeCode 的生命周期、工具发现和 display state 协议形态，覆盖 Esc 急停、turn cleanup、disabled tools/list、`displayResolvedForApps` 四个剩余对齐点。

**Architecture:** 不重写 Windows backend，也不模仿 macOS native package 的底层实现；只在 OpenHarness v2 MCP facade、ClaudeCode bridge、Windows session runtime 的连接处补齐 ClaudeCode 可观察协议。内部继续保留 Windows rich state 和审计证据，外部返回 ClaudeCode-compatible 字段，避免为“看起来一致”牺牲 Windows 诊断能力。

**Tech Stack:** Python 3.12, OpenHarness Computer Use MCP v2, unittest, CodeGraph, Windows runtime lock/cleanup/evidence modules, `start_oauth_agent.bat` visible-terminal acceptance.

---

## 1. 背景

用户确认这 4 项都值得对齐：

1. 把 Windows `GlobalEscapeAbortController` 接入 v2 acquire/cleanup。
2. 让 v2 wrapper cleanup 统一走完整 `run_turn_cleanup`，覆盖 hidden window/app restore。
3. 给 standalone `tools/list` 增加 mode disabled/context disabled 分支，对齐 ClaudeCode `adapter.isDisabled() ? { tools: [] } : { tools }`。
4. 为 `displayResolvedForApps` 写 ClaudeCode 观测用例，固定它在外部协议里是 key 字符串，内部仍可保留 OpenHarness rich list。

CodeGraph 已确认的 ClaudeCode 证据：

- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\wrapper.tsx`：
  - `acquireCuLock` fresh acquire 后调用 `registerEscHotkey`。
  - `onAppsHidden` 把隐藏 app id 累加到 `hiddenDuringTurn`。
  - `onDisplayResolvedForApps` 保存 string key。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\cleanup.ts`：
  - turn 结束先 unhide hidden apps。
  - 然后 `unregisterEscHotkey`。
  - 最后释放 computer use lock 并通知用户。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\mcpServer.ts`：
  - `tools/list` 返回 `adapter.isDisabled() ? { tools: [] } : { tools }`。
- `D:\ClaudeCode-main\ClaudeCode-main\state\AppStateStore.ts`：
  - `displayResolvedForApps?: string`，注释说明它是排序后逗号拼接的 bundle-id set。

CodeGraph 已确认的 OpenHarness 现状：

- `learning_agent/computer_use_mcp_v2/windows_runtime/global_escape_abort.py` 已有 `GlobalEscapeAbortController`，但主要被 `abort_streaming_hooks.py` 导入，未完全接入 v2 acquire 主链路。
- `learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py` 已有 `run_turn_cleanup`，但 CodeGraph 显示它只被本文件 manager 调用，未成为 v2 wrapper 的统一 cleanup 入口。
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py` 已实现动态 app inventory hint，但 `tools/list` 没有 disabled/context disabled 返回空工具清单的分支。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py` 当前外部 `displayResolvedForApps` 返回 rich list，和 ClaudeCode 的 string key 形态不一致。

## 2. 成功标准

- v2 acquire 成功后会注册全局 Escape 急停控制，注册过程幂等，重复工具调用不会重复堆叠 hook。
- 模型计划内发送 Escape 时不会触发用户急停；用户真实 Escape 会写入 durable abort 状态。
- turn cleanup 统一覆盖：hidden window/app restore、transient input release、Escape hook unregister、lock release、abort clear、owned resource cleanup。
- standalone `tools/list` 在 Computer Use disabled 或 context disabled 时返回 `{"tools": []}`，并记录可审计 trace。
- 外部 ClaudeCode-facing `displayState.displayResolvedForApps` 为稳定 string key，例如 `"Calculator,Notepad"` 或 `"com.app.a,com.app.b"`。
- OpenHarness 内部仍保留 rich records，例如 `displayResolvedForAppsRecords`，用于 Windows 多屏和窗口诊断。
- 旧测试不被静默删掉；需要更新旧断言时必须保留兼容字段或写明行为收窄原因。
- 自动化测试、py_compile、CodeGraph 同步和真实可见终端验收全部完成后，才允许声明开发完成。

## 3. 不做的事情

- 不把 ClaudeCode 的 macOS Swift executor 或 `@ant/computer-use-mcp` 外部包代码搬进 OpenHarness。
- 不新增未经授权的真实桌面动作能力。
- 不把 OpenHarness rich display records 删除。
- 不把旧 raw computer use 工具重新暴露给模型。
- 不用单元测试替代 `start_oauth_agent.bat` 真实可见终端验收。

## 4. 文件结构规划

Modify:

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
  - 增加 v2 context 的 disabled callbacks、Escape lifecycle callbacks、ClaudeCode display key 字段。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
  - 在 acquire 成功后触发 Escape hook 注册。
  - 在 cleanup helper 中继续清理 display pin，并依赖完整 cleanup callback。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
  - 从 `WindowsComputerUseSessionRuntime` 绑定 Escape register/mark/cleanup 能力。
  - 从 agent 恢复 display key 和 rich records。
  - 绑定 Computer Use disabled/context disabled 判断。
- `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`
  - 持有 `GlobalEscapeAbortController` 和 `ComputerUseSessionContextStore`。
  - acquire 后注册 Esc，cleanup 时走 `run_turn_cleanup`。
- `learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py`
  - 如有必要，扩展返回字段以覆盖 owned resource cleanup merge，但不扩大桌面动作面。
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`
  - `tools/list` 支持 disabled/context disabled 空工具清单。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py`
  - 外部 display state 输出 string key，并新增 rich records 字段。
- `learning_agent/computer_use_mcp_v2/windows_runtime/coordinates.py`
  - 增加或复用 helper，把 app records 转成 ClaudeCode string key。
- `docs/computer_use_mcp_v2_architecture.md`
  - 记录这 4 个生命周期和状态协议细节。
- `agent_memory/progress.md`
  - 记录每个任务完成证据。
- `agent_memory/bugs.md`
  - 记录未闭环风险或历史测试例外。

Create:

- `learning_agent/tests/test_computer_use_mcp_v2_escape_cleanup_parity.py`
  - 覆盖 Esc register、expected escape、cleanup unregister、hidden app restore。
- `learning_agent/tests/test_computer_use_mcp_v2_tools_list_disabled.py`
  - 覆盖 standalone tools/list disabled 返回空工具。
- `learning_agent/tests/test_computer_use_mcp_v2_display_resolved_key.py`
  - 覆盖 `displayResolvedForApps` string key 和 rich records 并存。
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal.json`
  - 真实可见终端验收场景。
- `learning_agent/test/computer_use_lifecycle_parity_20260616/`
  - 按 AGENTS 规则三备份本轮新写和修改的代码文件。

## 5. Task 1: 先写 Esc acquire/cleanup 红测

**Files:**

- Create: `learning_agent/tests/test_computer_use_mcp_v2_escape_cleanup_parity.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`

- [ ] **Step 1: 写失败测试，证明 acquire 后必须注册 Esc**

Add this test file:

```python
"""ClaudeCode-style Escape lifecycle tests for Computer Use MCP v2."""  # 新增代码+ClaudeCodeLifecycleParity：说明本测试文件专门验证 Esc 急停生命周期；如果没有这行代码，后续读者不知道这些测试为什么不放在普通 lock 测试里。
from __future__ import annotations  # 新增代码+ClaudeCodeLifecycleParity：启用延迟类型解析；如果没有这行代码，测试里的类型注解在旧解释顺序下更容易出错。

import unittest  # 新增代码+ClaudeCodeLifecycleParity：导入 unittest；如果没有这行代码，本文件无法被现有测试命令发现和执行。
from typing import Any  # 新增代码+ClaudeCodeLifecycleParity：导入 Any 描述 fake 回调参数；如果没有这行代码，测试 fake 的接口边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+ClaudeCodeLifecycleParity：导入 v2 分发入口；如果没有这行代码，测试无法证明真实主链路会触发 Esc 注册。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+ClaudeCodeLifecycleParity：导入 v2 context；如果没有这行代码，测试无法注入锁和 Esc 回调。


class _ObserveHost:  # 新增代码+ClaudeCodeLifecycleParity：类段开始，提供最小 observe host；如果没有这个 fake，测试会依赖真实 Windows 桌面。
    def observe(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟 host observe；如果没有这段函数，observe 工具会因为没有 host 失败。
        return {"ok": True, "text": "visible desktop", "payload": {"desktop_action_performed": False}}  # 新增代码+ClaudeCodeLifecycleParity：返回只读观察结果；如果没有这行代码，测试无法走到工具成功路径。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，_ObserveHost.observe 到此结束；如果没有这个边界说明，用户不容易看出 fake host 行为范围。
# 新增代码+ClaudeCodeLifecycleParity：类段结束，_ObserveHost 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class ComputerUseMcpV2EscapeCleanupParityTests(unittest.TestCase):  # 新增代码+ClaudeCodeLifecycleParity：类段开始，验证 ClaudeCode Esc acquire/cleanup 对齐；如果没有这个测试类，生命周期缺口会继续靠人工记忆。
    def test_acquire_registers_escape_abort_once(self) -> None:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，验证 acquire 成功后注册 Esc；如果没有这段测试，OpenHarness 可能只拿锁不启用急停。
        events: list[tuple[str, str]] = []  # 新增代码+ClaudeCodeLifecycleParity：保存注册事件；如果没有这行代码，测试无法断言注册次数。

        def acquire_lock(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟成功取锁；如果没有这段 fake，分发入口不会进入 acquire 成功分支。
            return {"acquired": True, "lock_backend": "fake", "tool_name": tool_name}  # 新增代码+ClaudeCodeLifecycleParity：返回成功 acquire；如果没有这行代码，runtime 会把工具拦在锁失败路径。
        # 新增代码+ClaudeCodeLifecycleParity：函数段结束，acquire_lock 到此结束；如果没有这个边界说明，用户不容易看出 fake 锁范围。

        def register_escape(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟注册全局 Esc；如果没有这段 fake，测试无法观察 register 是否被调用。
            events.append(("register", tool_name))  # 新增代码+ClaudeCodeLifecycleParity：记录注册事件；如果没有这行代码，断言没有数据来源。
            return {"global_hotkey_registered": True, "idempotent": len(events) > 1}  # 新增代码+ClaudeCodeLifecycleParity：返回注册结果；如果没有这行代码，runtime debug 无法合并注册报告。
        # 新增代码+ClaudeCodeLifecycleParity：函数段结束，register_escape 到此结束；如果没有这个边界说明，用户不容易看出 Esc fake 范围。

        context = ComputerUseMcpV2Context(host=_ObserveHost(), acquire_computer_use_lock=acquire_lock, register_global_escape_abort=register_escape)  # 新增代码+ClaudeCodeLifecycleParity：构造带锁和 Esc 回调的 context；如果没有这行代码，工具分发不会走本测试路径。
        result = dispatch_computer_use_mcp_v2_tool("observe", {}, context)  # 新增代码+ClaudeCodeLifecycleParity：调用只读观察工具；如果没有这行代码，测试没有实际行为。

        self.assertTrue(result["ok"])  # 新增代码+ClaudeCodeLifecycleParity：确认工具成功；如果没有这行代码，注册断言可能建立在失败路径上。
        self.assertEqual(events, [("register", "observe")])  # 新增代码+ClaudeCodeLifecycleParity：确认 acquire 成功后只注册一次；如果没有这行代码，重复 hook 或漏注册都不会被发现。
        self.assertTrue(result["debug"]["escape_abort"]["global_hotkey_registered"])  # 新增代码+ClaudeCodeLifecycleParity：确认注册结果进入 debug；如果没有这行代码，真实排查时看不到 Esc 生命周期。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，test_acquire_registers_escape_abort_once 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
# 新增代码+ClaudeCodeLifecycleParity：类段结束，ComputerUseMcpV2EscapeCleanupParityTests 到此结束；如果没有这个边界说明，用户不容易看出本测试文件范围。
```

- [ ] **Step 2: 运行红测并确认失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity.ComputerUseMcpV2EscapeCleanupParityTests.test_acquire_registers_escape_abort_once
```

Expected:

```text
AttributeError: ComputerUseMcpV2Context.__init__() got an unexpected keyword argument 'register_global_escape_abort'
```

If the failure is not about missing `register_global_escape_abort`, stop and inspect why the test did not exercise the intended missing seam.

## 6. Task 2: 实现 Esc acquire lifecycle

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`
- Test: `learning_agent/tests/test_computer_use_mcp_v2_escape_cleanup_parity.py`

- [ ] **Step 1: 在 `ComputerUseMcpV2Context` 增加 Esc 回调字段**

Add fields to `ComputerUseMcpV2Context` after `is_lock_held_locally`:

```python
    register_global_escape_abort: Callable[[str], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLifecycleParity：保存 acquire 成功后注册全局 Escape 急停的回调；如果没有这一行，v2 工具拿到锁后仍缺少 ClaudeCode 风格 Esc 急停。
    mark_expected_escape: Callable[[str, int], dict[str, Any]] | None = None  # 新增代码+ClaudeCodeLifecycleParity：保存模型计划内 Escape 的声明回调；如果没有这一行，模型自己发 Esc 可能被误判成用户急停。
```

- [ ] **Step 2: 在 runtime acquire 成功后注册 Esc**

Modify `_prepare_computer_use_lock` in `runtime.py` after `lock_held_locally` is written:

```python
    if lock_mode == "acquire" and callable(context.register_global_escape_abort):  # 新增代码+ClaudeCodeLifecycleParity：动作或观察工具拿到锁后注册全局 Esc；如果没有这一行，用户无法用 Esc 可靠中止 Computer Use。
        try:  # 新增代码+ClaudeCodeLifecycleParity：保护 Esc 注册后端；如果没有这一行，热键注册异常会让普通 observe/click 崩溃。
            escape_report = _dict_result(context.register_global_escape_abort(tool_name))  # 新增代码+ClaudeCodeLifecycleParity：调用绑定到 Windows runtime 的注册回调；如果没有这一行，Esc 控制器不会进入主链路。
        except Exception as error:  # 新增代码+ClaudeCodeLifecycleParity：把异常转成 debug 报告；如果没有这一行，真实后端错误无法审计。
            escape_report = {"global_hotkey_registered": False, "reason": str(error), "error_class": type(error).__name__}  # 新增代码+ClaudeCodeLifecycleParity：记录失败但不扩大副作用；如果没有这一行，用户不知道 Esc 为什么不可用。
        lock_debug["escape_abort"] = escape_report  # 新增代码+ClaudeCodeLifecycleParity：把 Esc 注册结果写入工具 debug；如果没有这一行，验收无法证明 register 发生过。
```

- [ ] **Step 3: 在 `WindowsComputerUseSessionRuntime` 增加 controller 和注册方法**

Add lazy import helper inside `session_runtime.py` near imports:

```python
def _default_escape_abort_controller(lock_manager: ComputerUseLockManager, session_id: str) -> Any:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，创建默认 Esc 急停控制器；如果没有这段函数，session runtime 需要在导入期加载热键模块并增加循环导入风险。
    try:  # 新增代码+ClaudeCodeLifecycleParity：优先包路径导入；如果没有这一行，普通模块运行无法加载控制器。
        from learning_agent.computer_use_mcp_v2.windows_runtime.global_escape_abort import GlobalEscapeAbortController  # 新增代码+ClaudeCodeLifecycleParity：导入全局 Esc 控制器；如果没有这一行，runtime 无法生成默认控制器。
    except ModuleNotFoundError as error:  # 新增代码+ClaudeCodeLifecycleParity：兼容 bat 脚本路径；如果没有这一行，真实可见终端可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.global_escape_abort"}:  # 新增代码+ClaudeCodeLifecycleParity：只允许包名前缀差异 fallback；如果没有这一行，真实 bug 会被误吞。
            raise  # 新增代码+ClaudeCodeLifecycleParity：重新抛出非路径错误；如果没有这一行，内部错误会被隐藏。
        from computer_use_mcp_v2.windows_runtime.global_escape_abort import GlobalEscapeAbortController  # type: ignore  # 新增代码+ClaudeCodeLifecycleParity：脚本模式导入控制器；如果没有这一行，start_oauth_agent.bat 路径下无法注册 Esc。
    return GlobalEscapeAbortController(lock_manager=lock_manager, session_id=session_id)  # 新增代码+ClaudeCodeLifecycleParity：返回和本 runtime 共用 lock manager 的控制器；如果没有这一行，Esc abort 会写到另一套事实源。
# 新增代码+ClaudeCodeLifecycleParity：函数段结束，_default_escape_abort_controller 到此结束；如果没有这个边界说明，用户不容易看出默认控制器创建范围。
```

Extend `__init__` signature and body:

```python
    def __init__(self, lock_manager: ComputerUseLockManager | None = None, session_id: str = PHASE40_DEFAULT_SESSION_ID, notification_limit: int = 20, audit_store: ComputerUseAuditStore | None = None, owned_resource_registry: OwnedResourceRegistry | None = None, escape_abort_controller: Any | None = None) -> None:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，初始化锁、会话、通知、审计、自有资源和 Esc 控制器；如果没有新增参数，测试和生产无法把 Esc 生命周期接入同一个 runtime。
        ...
        self.escape_abort_controller = escape_abort_controller if escape_abort_controller is not None else _default_escape_abort_controller(self.lock_manager, self.session_id)  # 新增代码+ClaudeCodeLifecycleParity：保存或创建全局 Esc 控制器；如果没有这一行，acquire 后无法注册用户急停热键。
```

Add methods:

```python
    def register_global_escape_abort(self, tool_name: str = "") -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，注册 ClaudeCode 风格全局 Esc 急停；如果没有这段函数，v2 context 无法在 acquire 成功后启用 Esc。
        report = dict(self.escape_abort_controller.register() or {})  # 新增代码+ClaudeCodeLifecycleParity：调用控制器注册方法；如果没有这一行，真实热键不会被注册。
        report.update({"tool_name": str(tool_name), "session_id": self.session_id, "escape_backend": "windows_runtime"})  # 新增代码+ClaudeCodeLifecycleParity：补充工具名和会话；如果没有这一行，debug 无法说明哪次工具触发注册。
        return report  # 新增代码+ClaudeCodeLifecycleParity：返回注册报告；如果没有这一行，runtime 无法把结果写入 debug。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，register_global_escape_abort 到此结束；如果没有这个边界说明，用户不容易看出注册范围。

    def mark_expected_escape(self, reason: str = "model_sent_escape", count: int = 1) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，声明模型计划内 Escape；如果没有这段函数，模型关闭菜单时可能触发用户急停。
        return dict(self.escape_abort_controller.mark_expected_escape(reason=reason, count=count) or {})  # 新增代码+ClaudeCodeLifecycleParity：委托控制器处理计划内 Escape；如果没有这一行，expected escape 计数不会生效。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，mark_expected_escape 到此结束；如果没有这个边界说明，用户不容易看出计划内 Escape 范围。
```

- [ ] **Step 4: 在 `bind_session_context.py` 绑定 Esc 回调**

Inside `_lock_callbacks_from_runtime`, add helper functions before return:

```python
    def register_global_escape_abort(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，把 runtime Esc 注册方法绑定进 context；如果没有这段函数，runtime.py 无法调用真实注册逻辑。
        method = getattr(runtime, "register_global_escape_abort", None)  # 新增代码+ClaudeCodeLifecycleParity：读取 runtime 注册方法；如果没有这一行，非标准 runtime 会直接崩溃。
        return dict(method(tool_name) or {}) if callable(method) else {"global_hotkey_registered": False, "reason": "register_global_escape_abort_missing"}  # 新增代码+ClaudeCodeLifecycleParity：调用方法或返回稳定缺失报告；如果没有这一行，debug 字段不稳定。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，register_global_escape_abort 到此结束；如果没有这个边界说明，用户不容易看出绑定范围。

    def mark_expected_escape(reason: str, count: int) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，绑定计划内 Escape 声明；如果没有这段函数，动作层未来无法声明模型发出的 Esc。
        method = getattr(runtime, "mark_expected_escape", None)  # 新增代码+ClaudeCodeLifecycleParity：读取 runtime 计划内 Escape 方法；如果没有这一行，非标准 runtime 会崩溃。
        return dict(method(reason=reason, count=count) or {}) if callable(method) else {"expected_escape_count": 0, "reason": "mark_expected_escape_missing"}  # 新增代码+ClaudeCodeLifecycleParity：调用方法或返回稳定缺失报告；如果没有这一行，调用方无法审计该能力是否存在。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，mark_expected_escape 到此结束；如果没有这个边界说明，用户不容易看出绑定范围。
```

Add them to the returned dict:

```python
"register_global_escape_abort": register_global_escape_abort,  # 新增代码+ClaudeCodeLifecycleParity：把 Esc 注册回调交给 context；如果没有这一项，runtime acquire 成功后仍无法注册 Esc。
"mark_expected_escape": mark_expected_escape,  # 新增代码+ClaudeCodeLifecycleParity：把计划内 Escape 回调交给 context；如果没有这一项，未来 Escape 动作无法区分用户急停和模型动作。
```

- [ ] **Step 5: 跑测试确认通过**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity
```

Expected:

```text
Ran 1 test
OK
```

## 7. Task 3: 统一 cleanup 到 `run_turn_cleanup`

**Files:**

- Modify: `learning_agent/tests/test_computer_use_mcp_v2_escape_cleanup_parity.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py` only if return merge fields are insufficient.

- [ ] **Step 1: 写 cleanup 覆盖 hidden restore 和 Esc unregister 的红测**

Append this test:

```python
    def test_session_cleanup_uses_turn_cleanup_and_unregisters_escape(self) -> None:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，验证 session cleanup 统一覆盖 hidden restore 和 Esc 注销；如果没有这段测试，cleanup 可能只释放锁却漏掉窗口恢复或热键注销。
        from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+ClaudeCodeLifecycleParity：导入 lock manager；如果没有这行代码，测试无法创建隔离锁状态。
        from learning_agent.computer_use_mcp_v2.windows_runtime.session_context import ComputerUseSessionContextStore  # 新增代码+ClaudeCodeLifecycleParity：导入 session context store；如果没有这行代码，测试无法模拟 hiddenDuringTurn 状态。
        from learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # 新增代码+ClaudeCodeLifecycleParity：导入 session runtime；如果没有这行代码，测试无法覆盖真实 cleanup 入口。
        from tempfile import TemporaryDirectory  # 新增代码+ClaudeCodeLifecycleParity：导入临时目录；如果没有这行代码，测试会污染真实用户状态。

        class FakeEscapeController:  # 新增代码+ClaudeCodeLifecycleParity：类段开始，模拟 Esc 控制器；如果没有这个 fake，测试会尝试注册真实系统热键。
            def __init__(self) -> None:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，初始化调用计数；如果没有这段函数，测试无法断言 cleanup 是否调用。
                self.cleaned = 0  # 新增代码+ClaudeCodeLifecycleParity：记录 cleanup 次数；如果没有这行代码，测试看不到 Esc 是否注销。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，FakeEscapeController.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 状态范围。
            def register(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟注册；如果没有这段函数，runtime 构造后不能复用同一 fake。
                return {"global_hotkey_registered": True}  # 新增代码+ClaudeCodeLifecycleParity：返回注册成功；如果没有这行代码，注册路径没有稳定输出。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，FakeEscapeController.register 到此结束；如果没有这个边界说明，用户不容易看出 fake 注册范围。
            def cleanup(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟注销；如果没有这段函数，run_turn_cleanup 无法清理 Esc。
                self.cleaned += 1  # 新增代码+ClaudeCodeLifecycleParity：累计 cleanup；如果没有这行代码，断言没有事实来源。
                return {"escape_hook_unregistered": True, "global_hotkey_registered": False}  # 新增代码+ClaudeCodeLifecycleParity：返回注销成功；如果没有这行代码，cleanup report 无法汇总成功。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，FakeEscapeController.cleanup 到此结束；如果没有这个边界说明，用户不容易看出 fake 注销范围。
        # 新增代码+ClaudeCodeLifecycleParity：类段结束，FakeEscapeController 到此结束；如果没有这个边界说明，用户不容易看出 fake 控制器范围。

        class FakeHostBackend:  # 新增代码+ClaudeCodeLifecycleParity：类段开始，模拟 host hide/unhide 后端；如果没有这个 fake，测试无法证明 hidden restore 被调用。
            def __init__(self) -> None:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，初始化恢复记录；如果没有这段函数，测试无法检查 unhide 参数。
                self.unhidden: list[list[dict[str, Any]]] = []  # 新增代码+ClaudeCodeLifecycleParity：保存每次恢复窗口列表；如果没有这行代码，断言没有数据来源。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，FakeHostBackend.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 状态范围。
            def release_transient_inputs(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟释放临时输入；如果没有这段函数，cleanup report 会走兜底而无法证明调用。
                return {"transient_inputs_released": True}  # 新增代码+ClaudeCodeLifecycleParity：返回释放成功；如果没有这行代码，cleanup_completed 可能为假。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，release_transient_inputs 到此结束；如果没有这个边界说明，用户不容易看出 fake 输入释放范围。
            def unhide_host_windows(self, windows: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，模拟恢复隐藏窗口；如果没有这段函数，cleanup 无法证明 hidden window 被恢复。
                self.unhidden.append([dict(item) for item in windows])  # 新增代码+ClaudeCodeLifecycleParity：记录恢复目标；如果没有这行代码，测试无法断言恢复了哪个窗口。
                return {"host_windows_restored": True, "unhidden_window_count": len(windows)}  # 新增代码+ClaudeCodeLifecycleParity：返回恢复成功；如果没有这行代码，cleanup report 无法汇总。
            # 新增代码+ClaudeCodeLifecycleParity：函数段结束，unhide_host_windows 到此结束；如果没有这个边界说明，用户不容易看出 fake unhide 范围。
        # 新增代码+ClaudeCodeLifecycleParity：类段结束，FakeHostBackend 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。

        with TemporaryDirectory() as temp_dir:  # 新增代码+ClaudeCodeLifecycleParity：创建隔离状态目录；如果没有这行代码，测试会污染真实 lock/context 文件。
            lock_manager = ComputerUseLockManager(base_dir=temp_dir)  # 新增代码+ClaudeCodeLifecycleParity：创建隔离锁管理器；如果没有这行代码，cleanup 无法释放测试锁。
            context_store = ComputerUseSessionContextStore(base_dir=temp_dir)  # 新增代码+ClaudeCodeLifecycleParity：创建隔离 context store；如果没有这行代码，hidden windows 无处保存。
            fake_host = FakeHostBackend()  # 新增代码+ClaudeCodeLifecycleParity：创建 fake host；如果没有这行代码，cleanup 无法记录 unhide。
            fake_escape = FakeEscapeController()  # 新增代码+ClaudeCodeLifecycleParity：创建 fake Esc 控制器；如果没有这行代码，cleanup 无法记录注销。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="test-session", context_store=context_store, host_cleanup_backend=fake_host, escape_abort_controller=fake_escape)  # 新增代码+ClaudeCodeLifecycleParity：构造带完整 cleanup 依赖的 runtime；如果没有这行代码，测试无法覆盖新主链路。
            lock_manager.acquire("test-session", owner_label="unit-test")  # 新增代码+ClaudeCodeLifecycleParity：让本 session 持锁；如果没有这行代码，cleanup 释放锁路径无法被覆盖。
            context_store.bind_context("test-session", hidden_windows=[{"id": "window-1"}], host_windows_hidden=True)  # 新增代码+ClaudeCodeLifecycleParity：模拟本轮隐藏过窗口；如果没有这行代码，unhide 分支不会执行。

            report = runtime.cleanup_turn(reason="unit-test cleanup")  # 新增代码+ClaudeCodeLifecycleParity：执行真实 cleanup 入口；如果没有这行代码，测试没有行为。

        self.assertTrue(report["cleanup_completed"])  # 新增代码+ClaudeCodeLifecycleParity：确认完整 cleanup 成功；如果没有这行代码，失败报告也可能漏过。
        self.assertEqual(fake_host.unhidden, [[{"id": "window-1"}]])  # 新增代码+ClaudeCodeLifecycleParity：确认隐藏窗口被恢复；如果没有这行代码，hidden restore 缺口不会暴露。
        self.assertEqual(fake_escape.cleaned, 1)  # 新增代码+ClaudeCodeLifecycleParity：确认 Esc hook 被注销一次；如果没有这行代码，热键残留不会被发现。
        self.assertTrue(report["escape_hook_unregistered"])  # 新增代码+ClaudeCodeLifecycleParity：确认报告上浮 Esc 注销字段；如果没有这行代码，真实验收无法读出 cleanup 细节。
        self.assertTrue(report["lock_released"])  # 新增代码+ClaudeCodeLifecycleParity：确认锁被释放；如果没有这行代码，cleanup 可能恢复窗口但留下锁。
    # 新增代码+ClaudeCodeLifecycleParity：函数段结束，test_session_cleanup_uses_turn_cleanup_and_unregisters_escape 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
```

- [ ] **Step 2: 运行红测并确认失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity.ComputerUseMcpV2EscapeCleanupParityTests.test_session_cleanup_uses_turn_cleanup_and_unregisters_escape
```

Expected:

```text
TypeError: WindowsComputerUseSessionRuntime.__init__() got an unexpected keyword argument 'context_store'
```

- [ ] **Step 3: 让 session runtime 使用 `run_turn_cleanup`**

Modify `WindowsComputerUseSessionRuntime.__init__` to accept and save:

```python
context_store: ComputerUseSessionContextStore | None = None  # 新增代码+ClaudeCodeLifecycleParity：允许测试和生产注入 session context store；如果没有这个参数，cleanup 找不到 hidden windows 的统一事实源。
host_cleanup_backend: Any | None = None  # 新增代码+ClaudeCodeLifecycleParity：允许注入隐藏窗口恢复后端；如果没有这个参数，run_turn_cleanup 无法真正恢复 host/app。
```

Inside `__init__`:

```python
        self.context_store = context_store if context_store is not None else ComputerUseSessionContextStore(base_dir=Path(self.lock_manager.base_dir).parent / "session_context")  # 新增代码+ClaudeCodeLifecycleParity：保存或创建 cleanup context store；如果没有这一行，hidden windows 状态无法跨函数读取。
        self.host_cleanup_backend = host_cleanup_backend  # 新增代码+ClaudeCodeLifecycleParity：保存 host cleanup 后端；如果没有这一行，cleanup 无法调用 unhide/release_transient_inputs。
```

Modify `cleanup_turn` so lock/abort/hidden/Esc cleanup is delegated:

```python
        turn_cleanup = run_turn_cleanup(self.context_store, target_session_id, host_backend=self.host_cleanup_backend, lock_manager=self.lock_manager, escape_controller=self.escape_abort_controller, reason=reason)  # 新增代码+ClaudeCodeLifecycleParity：用统一 turn cleanup 处理 hidden restore、Esc 注销、锁释放和 abort 清理；如果没有这一行，各路径会继续分散清理并容易漏项。
```

Then merge existing owned resource cleanup and notification fields into the returned report instead of separately releasing lock again.

- [ ] **Step 4: 确认 cleanup 测试通过**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity
```

Expected:

```text
Ran 2 tests
OK
```

## 8. Task 4: standalone tools/list disabled 分支

**Files:**

- Create: `learning_agent/tests/test_computer_use_mcp_v2_tools_list_disabled.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`

- [ ] **Step 1: 写 disabled tools/list 红测**

Create test:

```python
"""Tests for ClaudeCode-style disabled tools/list behavior."""  # 新增代码+ClaudeCodeToolsListDisabled：说明本测试文件验证 tools/list 禁用分支；如果没有这行代码，读者不容易知道为什么返回空工具是正确行为。
from __future__ import annotations  # 新增代码+ClaudeCodeToolsListDisabled：启用延迟类型解析；如果没有这行代码，类型注解可能提前求值。

import unittest  # 新增代码+ClaudeCodeToolsListDisabled：导入 unittest；如果没有这行代码，测试无法运行。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import handle_json_rpc_message  # 新增代码+ClaudeCodeToolsListDisabled：导入 standalone JSON-RPC handler；如果没有这行代码，测试无法覆盖 tools/list 主入口。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+ClaudeCodeToolsListDisabled：导入 v2 context；如果没有这行代码，测试无法注入禁用回调。


class ComputerUseMcpV2ToolsListDisabledTests(unittest.TestCase):  # 新增代码+ClaudeCodeToolsListDisabled：类段开始，验证 disabled 时隐藏工具；如果没有这个测试类，模型可能在禁用模式仍看到 Computer Use 工具。
    def test_tools_list_returns_empty_when_computer_use_disabled(self) -> None:  # 新增代码+ClaudeCodeToolsListDisabled：函数段开始，验证全局 disabled；如果没有这段测试，adapter.isDisabled parity 会缺失。
        context = ComputerUseMcpV2Context(is_computer_use_disabled=lambda: True)  # 新增代码+ClaudeCodeToolsListDisabled：构造禁用 context；如果没有这行代码，handler 会按默认启用返回工具。
        response = handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, context)  # 新增代码+ClaudeCodeToolsListDisabled：调用 tools/list；如果没有这行代码，测试没有行为。
        self.assertEqual(response["result"]["tools"], [])  # 新增代码+ClaudeCodeToolsListDisabled：确认禁用时返回空工具；如果没有这行代码，ClaudeCode adapter.isDisabled 语义无法锁定。
    # 新增代码+ClaudeCodeToolsListDisabled：函数段结束，test_tools_list_returns_empty_when_computer_use_disabled 到此结束；如果没有这个边界说明，用户不容易看出测试范围。

    def test_tools_list_returns_empty_when_context_disabled(self) -> None:  # 新增代码+ClaudeCodeToolsListDisabled：函数段开始，验证上下文 disabled；如果没有这段测试，非交互或禁用上下文仍可能暴露工具。
        context = ComputerUseMcpV2Context(is_computer_use_context_disabled=lambda: True)  # 新增代码+ClaudeCodeToolsListDisabled：构造上下文禁用 context；如果没有这行代码，handler 无法覆盖 context disabled。
        response = handle_json_rpc_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, context)  # 新增代码+ClaudeCodeToolsListDisabled：调用 tools/list；如果没有这行代码，测试没有行为。
        self.assertEqual(response["result"]["tools"], [])  # 新增代码+ClaudeCodeToolsListDisabled：确认上下文禁用时返回空工具；如果没有这行代码，禁用策略不可观测。
    # 新增代码+ClaudeCodeToolsListDisabled：函数段结束，test_tools_list_returns_empty_when_context_disabled 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
# 新增代码+ClaudeCodeToolsListDisabled：类段结束，ComputerUseMcpV2ToolsListDisabledTests 到此结束；如果没有这个边界说明，用户不容易看出本测试文件范围。
```

- [ ] **Step 2: 运行红测并确认失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled
```

Expected:

```text
TypeError: ComputerUseMcpV2Context.__init__() got an unexpected keyword argument 'is_computer_use_disabled'
```

- [ ] **Step 3: 实现 context disabled callbacks**

Add fields to `ComputerUseMcpV2Context`:

```python
    is_computer_use_disabled: Callable[[], bool] | None = None  # 新增代码+ClaudeCodeToolsListDisabled：保存全局 Computer Use disabled 判断；如果没有这一行，standalone tools/list 无法对齐 ClaudeCode adapter.isDisabled。
    is_computer_use_context_disabled: Callable[[], bool] | None = None  # 新增代码+ClaudeCodeToolsListDisabled：保存当前上下文 disabled 判断；如果没有这一行，非交互或禁用上下文仍可能暴露工具。
```

- [ ] **Step 4: 在 `mcpServer.py` 增加 disabled 分支**

Add helper:

```python
def _computer_use_tools_list_disabled(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ClaudeCodeToolsListDisabled：函数段开始，判断 tools/list 是否应该返回空工具；如果没有这段函数，禁用逻辑会散落在 handler 中。
    disabled = bool(context.is_computer_use_disabled() if callable(context.is_computer_use_disabled) else False)  # 新增代码+ClaudeCodeToolsListDisabled：读取全局 disabled；如果没有这一行，adapter.isDisabled 语义不会生效。
    context_disabled = bool(context.is_computer_use_context_disabled() if callable(context.is_computer_use_context_disabled) else False)  # 新增代码+ClaudeCodeToolsListDisabled：读取上下文 disabled；如果没有这一行，非交互上下文仍会暴露工具。
    return {"disabled": disabled, "context_disabled": context_disabled, "tools_hidden": bool(disabled or context_disabled)}  # 新增代码+ClaudeCodeToolsListDisabled：返回结构化判断；如果没有这一行，trace 和 handler 无法复用同一结果。
# 新增代码+ClaudeCodeToolsListDisabled：函数段结束，_computer_use_tools_list_disabled 到此结束；如果没有这个边界说明，用户不容易看出 disabled 判断范围。
```

Inside `handle_json_rpc_message`, before app inventory loading:

```python
        disabled_state = _computer_use_tools_list_disabled(context)  # 新增代码+ClaudeCodeToolsListDisabled：先判断 Computer Use 是否禁用；如果没有这一行，禁用场景仍会枚举 app 并返回工具。
        if disabled_state["tools_hidden"]:  # 新增代码+ClaudeCodeToolsListDisabled：禁用时直接返回空工具；如果没有这一行，模型会在禁用状态看到可调用 Computer Use 工具。
            _record_tools_list_inventory_trace(context, {"status": "disabled", **disabled_state})  # 新增代码+ClaudeCodeToolsListDisabled：记录禁用原因；如果没有这一行，排查时不知道为什么工具列表为空。
            return _response(request_id, {"tools": []})  # 新增代码+ClaudeCodeToolsListDisabled：对齐 ClaudeCode adapter.isDisabled 返回形态；如果没有这一行，协议级 tools/list 不一致。
```

- [ ] **Step 5: 跑测试确认通过**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list
```

Expected:

```text
OK
```

## 9. Task 5: `displayResolvedForApps` 外部 string key 与内部 rich records 并存

**Files:**

- Create: `learning_agent/tests/test_computer_use_mcp_v2_display_resolved_key.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/coordinates.py`
- Modify existing tests if needed: `learning_agent/tests/test_computer_use_mcp_v2_display_state.py`

- [ ] **Step 1: 写 display key 红测**

Create test:

```python
"""Tests for ClaudeCode displayResolvedForApps string key parity."""  # 新增代码+ClaudeCodeDisplayKeyParity：说明本测试文件验证 displayResolvedForApps 外部形态；如果没有这行代码，读者不知道 rich list 和 string key 为什么同时存在。
from __future__ import annotations  # 新增代码+ClaudeCodeDisplayKeyParity：启用延迟类型解析；如果没有这行代码，类型注解可能提前求值。

import unittest  # 新增代码+ClaudeCodeDisplayKeyParity：导入 unittest；如果没有这行代码，测试无法运行。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.observation import _display_state_payload  # 新增代码+ClaudeCodeDisplayKeyParity：导入 display state 输出 helper；如果没有这行代码，测试无法锁定模型可见字段。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+ClaudeCodeDisplayKeyParity：导入 context；如果没有这行代码，测试无法构造显示器状态。


class ComputerUseMcpV2DisplayResolvedKeyTests(unittest.TestCase):  # 新增代码+ClaudeCodeDisplayKeyParity：类段开始，验证 displayResolvedForApps key；如果没有这个测试类，外部协议形态可能再次漂移。
    def test_display_resolved_for_apps_is_claudecode_string_key(self) -> None:  # 新增代码+ClaudeCodeDisplayKeyParity：函数段开始，验证外部字段是字符串；如果没有这段测试，OpenHarness rich list 会继续占用 ClaudeCode 字段名。
        context = ComputerUseMcpV2Context()  # 新增代码+ClaudeCodeDisplayKeyParity：创建 context；如果没有这行代码，display helper 没有输入。
        context.display_resolved_for_apps = [  # 新增代码+ClaudeCodeDisplayKeyParity：设置内部 rich records；如果没有这行代码，测试无法验证 key 从 records 生成。
            {"appId": "Notepad", "displayId": "1", "windowId": "w1"},  # 新增代码+ClaudeCodeDisplayKeyParity：加入 Notepad 记录；如果没有这行代码，排序和去重没有代表数据。
            {"appId": "Calculator", "displayId": "1", "windowId": "w2"},  # 新增代码+ClaudeCodeDisplayKeyParity：加入 Calculator 记录；如果没有这行代码，key 无法证明按 app id 排序。
        ]  # 新增代码+ClaudeCodeDisplayKeyParity：结束 rich records 列表；如果没有这行代码，Python 语法不完整。

        payload = _display_state_payload(context)  # 新增代码+ClaudeCodeDisplayKeyParity：生成模型可见 display state；如果没有这行代码，测试没有行为。

        self.assertEqual(payload["displayResolvedForApps"], "Calculator,Notepad")  # 新增代码+ClaudeCodeDisplayKeyParity：确认 ClaudeCode-facing 字段是排序后的 string key；如果没有这行代码，协议形态无法锁定。
        self.assertEqual(len(payload["displayResolvedForAppsRecords"]), 2)  # 新增代码+ClaudeCodeDisplayKeyParity：确认 OpenHarness 内部 rich records 仍上浮到新字段；如果没有这行代码，Windows 诊断信息可能被删掉。
    # 新增代码+ClaudeCodeDisplayKeyParity：函数段结束，test_display_resolved_for_apps_is_claudecode_string_key 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
# 新增代码+ClaudeCodeDisplayKeyParity：类段结束，ComputerUseMcpV2DisplayResolvedKeyTests 到此结束；如果没有这个边界说明，用户不容易看出本测试文件范围。
```

- [ ] **Step 2: 运行红测并确认失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_display_resolved_key
```

Expected:

```text
AssertionError: [{'appId': ...}] != 'Calculator,Notepad'
```

- [ ] **Step 3: 增加 string key helper**

Add to `coordinates.py` or `observation.py`:

```python
def claudecode_display_resolved_for_apps_key(records: Any) -> str:  # 新增代码+ClaudeCodeDisplayKeyParity：函数段开始，把 OpenHarness rich records 转成 ClaudeCode string key；如果没有这段函数，外部协议会继续返回数组而不是 ClaudeCode 的 app-set key。
    safe_records = [dict(item) for item in records if isinstance(item, dict)] if isinstance(records, list) else []  # 新增代码+ClaudeCodeDisplayKeyParity：只接受 dict 列表；如果没有这一行，坏数据会污染 key 生成。
    app_ids = sorted({str(item.get("appId", item.get("bundleId", item.get("bundle_id", ""))) or "").strip() for item in safe_records if str(item.get("appId", item.get("bundleId", item.get("bundle_id", ""))) or "").strip()})  # 新增代码+ClaudeCodeDisplayKeyParity：提取、去重并排序 app id；如果没有这一行，同一 app 多窗口会让 key 不稳定。
    return ",".join(app_ids)  # 新增代码+ClaudeCodeDisplayKeyParity：返回 ClaudeCode 风格逗号拼接 key；如果没有这一行，外部字段无法稳定比较 allowed app set。
# 新增代码+ClaudeCodeDisplayKeyParity：函数段结束，claudecode_display_resolved_for_apps_key 到此结束；如果没有这个边界说明，用户不容易看出 key 生成范围。
```

- [ ] **Step 4: 修改 `_display_state_payload`**

Replace current `displayResolvedForApps` list output:

```python
    records = [dict(item) for item in context.display_resolved_for_apps]  # 新增代码+ClaudeCodeDisplayKeyParity：复制内部 rich records；如果没有这一行，返回值可能共享可变列表。
    resolved_key = context.display_resolved_for_apps_key or claudecode_display_resolved_for_apps_key(records)  # 新增代码+ClaudeCodeDisplayKeyParity：优先使用已保存 key，否则从 records 生成；如果没有这一行，外部 ClaudeCode key 会为空或不稳定。
    return {"selectedDisplayId": context.selected_display_id, "displayPinnedByModel": bool(context.display_pinned_by_model), "displayResolvedForApps": resolved_key, "displayResolvedForAppsRecords": records, "lastScreenshotDims": dict(context.last_screenshot_dims)}  # 修改代码+ClaudeCodeDisplayKeyParity：外部字段返回 string key，同时保留 records；如果没有这一行，ClaudeCode 协议和 Windows 诊断无法同时满足。
```

- [ ] **Step 5: 更新 context 和 bind_session_context**

Add field:

```python
    display_resolved_for_apps_key: str = ""  # 新增代码+ClaudeCodeDisplayKeyParity：保存 ClaudeCode 风格 app-set key；如果没有这一行，context 只能保存 rich records，无法保持外部协议一致。
```

Update `_display_state_from_agent` to read both:

```python
    resolved_for_apps_key = str(getattr(agent, "computer_use_display_resolved_for_apps_key", "") or "")  # 新增代码+ClaudeCodeDisplayKeyParity：读取 agent 保存的 ClaudeCode key；如果没有这一行，跨轮 context 会丢失 app-set key。
```

Return it in the dict:

```python
"display_resolved_for_apps_key": resolved_for_apps_key,  # 新增代码+ClaudeCodeDisplayKeyParity：把 key 带入 context；如果没有这一项，新 context 只能重新从 records 推断。
```

- [ ] **Step 6: 跑 display 测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_display_resolved_key learning_agent.tests.test_computer_use_mcp_v2_display_state
```

Expected:

```text
OK
```

## 10. Task 6: 真实主链路和 wrapper cleanup 回归

**Files:**

- Modify: `learning_agent/tests/test_computer_use_mcp_v2_bridge_wrapper.py`
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py` only if cleanup is not invoking `cleanup_computer_use_mcp_v2_turn`.
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py` only if wrapper cleanup cannot reach complete runtime cleanup.

- [ ] **Step 1: 写 wrapper cleanup 使用完整 cleanup 的测试**

Add to bridge wrapper tests:

```python
def test_wrapper_cleanup_calls_complete_turn_cleanup(self) -> None:
    # 新增代码+ClaudeCodeLifecycleParity：测试说明，wrapper 异常或完成后必须调用完整 cleanup；如果没有这个测试，bridge 层可能绕开 hidden restore 和 Esc 注销。
    cleanup_events = []  # 新增代码+ClaudeCodeLifecycleParity：保存 cleanup 调用；如果没有这行代码，断言没有事实来源。

    class FakeAgent:
        # 新增代码+ClaudeCodeLifecycleParity：fake agent 段开始，提供 wrapper 所需最小字段；如果没有这个 fake，测试会依赖真实 agent。
        def __init__(self) -> None:
            # 新增代码+ClaudeCodeLifecycleParity：初始化 fake agent；如果没有这段函数，context 字段不存在。
            self.computer_use_mcp_v2_host = object()  # 新增代码+ClaudeCodeLifecycleParity：设置显式 host 避免 legacy host 构造；如果没有这行代码，测试会进入不相关 adapter。
        def _computer_use_cleanup_runtime(self):
            # 新增代码+ClaudeCodeLifecycleParity：提供 cleanup runtime 工厂；如果没有这段函数，bind_session_context 无法绑定 cleanup。
            class Runtime:
                # 新增代码+ClaudeCodeLifecycleParity：fake runtime 段开始，提供 cleanup_turn；如果没有这个类，wrapper 无法证明调用完整 cleanup。
                session_id = "wrapper-test"
                lock_manager = object()
                def cleanup_turn(self, reason: str = "turn cleanup"):
                    # 新增代码+ClaudeCodeLifecycleParity：记录 cleanup；如果没有这段函数，测试无法观察 wrapper cleanup。
                    cleanup_events.append(reason)
                    return {"cleanup_completed": True, "reason": reason}
            return Runtime()
    # 新增代码+ClaudeCodeLifecycleParity：fake agent 段结束；如果没有这个边界说明，用户不容易看出 fake 范围。

    # 新增代码+ClaudeCodeLifecycleParity：执行 wrapper 调用并断言 cleanup_events；实际代码应复用现有 wrapper 测试里的 call helper，避免新建不必要框架。
```

The exact call helper must follow the existing `test_computer_use_mcp_v2_bridge_wrapper.py` pattern. Do not create a second wrapper entrypoint.

- [ ] **Step 2: Run wrapper tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper
```

Expected:

```text
OK
```

## 11. Task 7: 文档、学习备份和项目记忆

**Files:**

- Modify: `docs/computer_use_mcp_v2_architecture.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create or update: `learning_agent/test/computer_use_lifecycle_parity_20260616/`

- [ ] **Step 1: 更新架构文档**

Add a section named:

```markdown
## ClaudeCode Lifecycle Parity: Esc, Cleanup, Disabled Tools, Display Key
```

Include these facts:

- Esc register happens only after v2 acquire succeeds.
- Esc cleanup happens through turn cleanup before or together with lock release.
- `tools/list` returns `tools: []` when disabled.
- `displayResolvedForApps` is a ClaudeCode-facing string key.
- `displayResolvedForAppsRecords` keeps OpenHarness Windows rich diagnostic records.

- [ ] **Step 2: 复制修改代码到学习目录**

Create directory:

```powershell
New-Item -ItemType Directory -Force "learning_agent\test\computer_use_lifecycle_parity_20260616"
```

Copy every modified Python source and test file into that directory with flattened names. Example:

```powershell
Copy-Item "learning_agent\computer_use_mcp_v2\inferred_ant_mcp\runtime.py" "learning_agent\test\computer_use_lifecycle_parity_20260616\learning_agent__computer_use_mcp_v2__inferred_ant_mcp__runtime.py"
```

After copying, verify hashes match:

```powershell
python - <<'PY'
from pathlib import Path
import hashlib
pairs = [
    (Path("learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py"), Path("learning_agent/test/computer_use_lifecycle_parity_20260616/learning_agent__computer_use_mcp_v2__inferred_ant_mcp__runtime.py")),
]
for src, dst in pairs:
    print(src, hashlib.sha256(src.read_bytes()).hexdigest() == hashlib.sha256(dst.read_bytes()).hexdigest())
PY
```

Expected:

```text
learning_agent\computer_use_mcp_v2\inferred_ant_mcp\runtime.py True
```

- [ ] **Step 3: 更新 agent memory**

Append to `agent_memory/progress.md`:

```markdown
## 2026-06-16 Computer Use ClaudeCode Lifecycle Parity

- 已补齐 Esc acquire/register 和 turn cleanup/unregister 生命周期。
- 已补齐 standalone tools/list disabled 返回空工具清单。
- 已将外部 displayResolvedForApps 固定为 ClaudeCode string key，同时保留 displayResolvedForAppsRecords 作为 OpenHarness Windows rich state。
- 自动化测试、py_compile、CodeGraph 和真实可见终端验收结果记录在本节后续条目。
```

Append or update `agent_memory/bugs.md` with any failures that remain. If no new unresolved risk exists, add:

```markdown
- 2026-06-16 本轮 ClaudeCode lifecycle parity 未留下新的未解决功能风险；历史全量 discover 旧接口失败仍不作为本轮验收口径。
```

## 12. Task 8: 验证和真实可见终端验收

**Files:**

- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal.json`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: 运行聚焦测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled learning_agent.tests.test_computer_use_mcp_v2_display_resolved_key learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper
```

Expected:

```text
OK
```

- [ ] **Step 2: 运行完整 v2 computer use 回归矩阵**

Run the same matrix currently used by the project, and add the three new test files:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_agent_side_binding learning_agent.tests.test_computer_use_mcp_batch_safety learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper learning_agent.tests.test_windows_computer_use_image_results_phase41 learning_agent.tests.test_windows_computer_use_real_screenshot_phase56 learning_agent.tests.test_computer_use_mcp_v2_sendinput_parity_task4 learning_agent.tests.test_computer_use_mcp_v2_primary_paths learning_agent.tests.test_computer_use_mcp_v2_internal_adapter_fence learning_agent.tests.test_computer_use_mcp_v2_architecture_docs learning_agent.tests.test_computer_use_mcp_v2_state_observe_action_loop learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled learning_agent.tests.test_computer_use_mcp_v2_display_resolved_key
```

Expected:

```text
OK
```

- [ ] **Step 3: py_compile**

Run:

```powershell
python -m py_compile learning_agent\computer_use_mcp_v2\inferred_ant_mcp\types.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\runtime.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\bind_session_context.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\observation.py learning_agent\computer_use_mcp_v2\windows_runtime\session_runtime.py learning_agent\computer_use_mcp_v2\windows_runtime\turn_cleanup.py learning_agent\computer_use_mcp_v2\windows_runtime\coordinates.py learning_agent\computer_use_mcp_v2\claudecode_bridge\mcpServer.py learning_agent\tests\test_computer_use_mcp_v2_escape_cleanup_parity.py learning_agent\tests\test_computer_use_mcp_v2_tools_list_disabled.py learning_agent\tests\test_computer_use_mcp_v2_display_resolved_key.py
```

Expected: command exits with code 0.

- [ ] **Step 4: 创建真实终端验收场景**

Create JSON scenario:

```json
{
  "name": "agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal",
  "start_bat": "H:\\codexworkplace\\sofeware\\OpenHarness-main\\learning_agent\\start_oauth_agent.bat",
  "prompts": [
    "/computer use --full",
    "请只使用 Computer Use MCP v2 的只读能力检查当前桌面状态，然后回答 COMPUTER_USE_MCP_V2_LIFECYCLE_PARITY_OK。不要点击鼠标，不要输入键盘，不要读写剪贴板，不要打开应用。"
  ],
  "expected_markers": [
    "Computer Use Mode",
    "full_mode=true",
    "mcp__computer-use__observe",
    "COMPUTER_USE_MCP_V2_LIFECYCLE_PARITY_OK"
  ],
  "forbidden_markers": [
    "low_level_event_count=1",
    "real_desktop_touched=true"
  ]
}
```

If the existing acceptance controller schema uses different keys, copy the exact shape from the latest passing scenario `agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal.json` and only change name, prompt, marker, and assertions.

- [ ] **Step 5: 执行真实可见终端验收**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "learning_agent\acceptance_controller\controller.ps1" -ScenarioPath "scenarios\agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal.json"
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
```

The result JSON must show:

- `completed=true`
- `assertion.passed=true`
- `computer_use_mcp_v2_tool=true`
- tool call includes `mcp__computer-use__observe`
- final marker includes `COMPUTER_USE_MCP_V2_LIFECYCLE_PARITY_OK`
- `permission_sent_count=0`
- `real_desktop_touched=false`
- `low_level_event_count=0`

If the Codex environment cannot open, observe, and interact with the visible terminal, stop and report:

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

- [ ] **Step 6: 同步 CodeGraph**

Run:

```powershell
codegraph sync .
codegraph status .
codegraph query register_global_escape_abort
codegraph query claudecode_display_resolved_for_apps_key
```

Expected:

- `codegraph status .` reports `[OK] Index is up to date`
- queries find the new symbols in source and backup files

## 13. 停止条件

Stop and ask the user before continuing if any of these happen:

- `run_turn_cleanup` integration would require deleting existing owned resource cleanup or notification behavior.
- Esc registration requires a real global Windows hook that cannot be safely faked in tests.
- `tools/list` disabled behavior conflicts with an existing OpenHarness mode policy.
- `displayResolvedForApps` string key would require removing rich records instead of adding a companion records field.
- Visible terminal acceptance cannot be completed from Codex.
- CodeGraph cannot be synced or reports stale index after repeated sync attempts.

## 14. Self-Review

- Spec coverage: all 4 requested items are covered by Tasks 1-5 and verified in Task 8.
- Placeholder scan: this plan does not contain deferred implementation placeholders. Each code-changing task includes file names, test names, code snippets, and expected commands.
- Type consistency: `register_global_escape_abort`, `mark_expected_escape`, `is_computer_use_disabled`, `is_computer_use_context_disabled`, and `display_resolved_for_apps_key` are introduced before later tasks reference them.
- Safety: no task expands uncontrolled desktop actions; real terminal acceptance uses observe-only prompt.
- AGENTS compliance: implementation tasks explicitly require Chinese per-line comments in code snippets, learning backup copy, agent memory update, CodeGraph sync, and visible-terminal acceptance.
