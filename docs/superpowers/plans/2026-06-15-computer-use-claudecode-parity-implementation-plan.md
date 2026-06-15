# Computer Use ClaudeCode Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐 OpenHarness computer use 与 ClaudeCode 观察到的工具表面和执行行为，新增 7 个 Windows 可执行工具，并对齐真实 clipboard、动态 tools/list、无 host 明确失败。

**Architecture:** `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/` 是反推 ClaudeCode 外部 `@ant/computer-use-mcp` 包的契约层，只放 MCP 工具名、schema、参数/返回语义和轻量 dispatch。真实 Windows API、SendInput、截图、剪贴板、窗口枚举、锁和审计全部留在 `learning_agent/computer_use_mcp_v2/windows_runtime/`，由 host/context/adapter 边界连接。

**Tech Stack:** Python 3, `unittest`, MCP JSON-RPC, Win32 `ctypes`, existing OpenHarness `ComputerUseController`, `WindowsSendInputExecutor`, `WindowsSendInputDispatcher`, `WindowsSendInputLowLevelSender`.

---

## Implementation Guardrails

- 本计划执行前先创建或切换到独立工作区，避免混入当前脏工作区里的历史变更。
- 每个任务遵循 TDD：先写失败测试，确认失败，再做最小实现，再运行目标测试。
- 所有新写和修改的代码行必须按项目规则加中文注释，并以 `新增代码+ClaudeCodeParity` 或 `修改代码+ClaudeCodeParity` 开头说明原因。
- `inferred_ant_mcp/` 只表达反推外部包契约，不直接调用 Windows API。
- `windows_runtime/` 承担真实 Windows 能力，不把平台细节写回契约层。
- 每个任务提交时只暂存该任务涉及文件，不暂存 `agent_memory/`、历史删除、运行产物或无关变更。

## File Map

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`  
  负责 24 个公开 MCP 工具的唯一 schema 来源和动态提示承载。
- Modify: `learning_agent/tools/tool_scope.py`  
  负责 `computer_use_operation` / `computer_use_debug` 下的工具可见性。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py`  
  负责无 host 明确失败和 host action 调用包装。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py`  
  负责反推包层 clipboard 契约，生产能力只通过 host 调用。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py`  
  负责把新增 7 个工具和 clipboard 方法桥接到 Windows session adapter。
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`  
  负责 MCP 原子工具到 controller/clipboard/backend 的真实映射。
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_executor.py`  
  负责新增动作转成规范输入事件。
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_dispatcher.py`  
  负责规范输入事件转成低层 SendInput 事件。
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py`  
  负责真实低层鼠标中键、按键释放、系统剪贴板 helper 复用边界。
- Create: `learning_agent/computer_use_mcp_v2/windows_runtime/clipboard_io.py`  
  负责真实 Windows 文本剪贴板读写，供 session adapter 使用。
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`  
  负责 `tools/list` 动态 hints 注入。
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/hostAdapter.py`  
  负责独立 stdio server 的动态 app hints 和 clipboard 降级说明。
- Test: `learning_agent/tests/test_computer_use_mcp_v2_contract.py`
- Test: `learning_agent/tests/test_computer_use_tool_scope.py`
- Test: `learning_agent/tests/test_computer_use_mcp_session_adapter.py`
- Test: `learning_agent/tests/test_windows_computer_use_sendinput_dispatcher_phase47.py`
- Test: `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`
- Test: create `learning_agent/tests/test_windows_computer_use_clipboard_io.py`
- Test: create `learning_agent/tests/test_computer_use_mcp_dynamic_tools_list.py`

---

### Task 1: Public MCP Tool Surface

**Files:**
- Modify: `learning_agent/tests/test_computer_use_mcp_v2_contract.py`
- Modify: `learning_agent/tests/test_computer_use_tool_scope.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`
- Modify: `learning_agent/tools/tool_scope.py`

- [ ] **Step 1: Write the failing contract tests**

In `learning_agent/tests/test_computer_use_mcp_v2_contract.py`, extend `EXPECTED_RAW_TOOL_NAMES` with the 7 parity tools and remove them from `FORBIDDEN_RAW_TOOL_NAMES`.

```python
EXPECTED_PARITY_RAW_TOOL_NAMES = {  # 新增代码+ClaudeCodeParity：集中列出本期补齐的 ClaudeCode 观察工具；如果没有这组常量，工具面扩展会散落在多个测试里。
    "zoom",  # 新增代码+ClaudeCodeParity：局部放大观察工具；如果没有这一项，ClaudeCode 视觉局部检查能力不对齐。
    "hold_key",  # 新增代码+ClaudeCodeParity：按住键盘修饰键工具；如果没有这一项，拖选和快捷组合动作无法表达。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：左键拖拽工具；如果没有这一项，绘图、拖放和选区任务不对齐。
    "middle_click",  # 新增代码+ClaudeCodeParity：鼠标中键工具；如果没有这一项，中键打开/滚轮点击场景不对齐。
    "triple_click",  # 新增代码+ClaudeCodeParity：三击工具；如果没有这一项，整段文本选择类桌面习惯不对齐。
    "left_mouse_down",  # 新增代码+ClaudeCodeParity：左键按下工具；如果没有这一项，分段拖拽无法表达。
    "left_mouse_up",  # 新增代码+ClaudeCodeParity：左键释放工具；如果没有这一项，分段拖拽无法安全闭合。
}
EXPECTED_RAW_TOOL_NAMES = EXPECTED_RAW_TOOL_NAMES | EXPECTED_PARITY_RAW_TOOL_NAMES  # 修改代码+ClaudeCodeParity：把新增工具纳入公开 MCP 合同；如果没有这一行，server selftest 仍只认 17 个工具。
FORBIDDEN_RAW_TOOL_NAMES = FORBIDDEN_RAW_TOOL_NAMES - EXPECTED_PARITY_RAW_TOOL_NAMES  # 修改代码+ClaudeCodeParity：新增工具不再按蓝图外工具拒绝；如果没有这一行，测试会自相矛盾。
```

In `learning_agent/tests/test_computer_use_tool_scope.py`, extend `OPERATION_RAW_TOOL_NAMES` with the same 7 tools and replace the old reserved `assertNotIn` checks with `assertIn` checks.

```python
OPERATION_RAW_TOOL_NAMES.update({  # 修改代码+ClaudeCodeParity：操作/debug 模式公开完整 ClaudeCode 观察工具面；如果没有这一段，模型仍看不到新增 7 个工具。
    "zoom",  # 新增代码+ClaudeCodeParity：让模型可在操作模式请求局部观察；如果没有这一项，zoom 只会存在于 schema 测试里。
    "hold_key",  # 新增代码+ClaudeCodeParity：让模型可按住修饰键；如果没有这一项，键盘保持动作不可见。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：让模型可直接拖拽；如果没有这一项，绘图和拖放仍依赖 batch 拼动作。
    "middle_click",  # 新增代码+ClaudeCodeParity：让模型可调用中键；如果没有这一项，中键工具即使实现也不可见。
    "triple_click",  # 新增代码+ClaudeCodeParity：让模型可调用三击；如果没有这一项，文本段落选择能力不完整。
    "left_mouse_down",  # 新增代码+ClaudeCodeParity：让模型可拆分鼠标按下；如果没有这一项，精细拖拽无法开始。
    "left_mouse_up",  # 新增代码+ClaudeCodeParity：让模型可拆分鼠标释放；如果没有这一项，精细拖拽无法结束。
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope
```

Expected: FAIL. The failure must mention missing `zoom`, `hold_key`, `left_click_drag`, `middle_click`, `triple_click`, `left_mouse_down`, or `left_mouse_up`.

- [ ] **Step 3: Implement the schema and scope changes**

In `build_tools.py`, add the 7 names to `COMPUTER_USE_MCP_TOOL_NAMES`, remove them from `FORBIDDEN_LEGACY_RAW_TOOL_NAMES`, and add schema entries near related mouse/keyboard tools.

```python
    "zoom",  # 新增代码+ClaudeCodeParity：公开局部放大观察工具；如果没有这一项，OpenHarness 工具表面少于 ClaudeCode 观察结果。
    "hold_key",  # 新增代码+ClaudeCodeParity：公开按住键盘工具；如果没有这一项，模型无法表达按住 Shift/Ctrl 的动作。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：公开左键拖拽工具；如果没有这一项，拖拽只能靠 batch 临时拼接。
    "middle_click",  # 新增代码+ClaudeCodeParity：公开中键点击工具；如果没有这一项，鼠标中键场景无法对齐。
    "triple_click",  # 新增代码+ClaudeCodeParity：公开三击工具；如果没有这一项，整段选择类场景无法对齐。
    "left_mouse_down",  # 新增代码+ClaudeCodeParity：公开左键按下工具；如果没有这一项，分段拖拽没有开始动作。
    "left_mouse_up",  # 新增代码+ClaudeCodeParity：公开左键释放工具；如果没有这一项，分段拖拽没有闭合动作。
```

Add tool schema entries:

```python
        _tool("zoom", "放大观察指定屏幕区域并返回局部截图。", {"x": point["x"], "y": point["y"], "width": {"type": "integer"}, "height": {"type": "integer"}, "reason": {"type": "string"}}, ["x", "y", "width", "height"], read_only=True),  # 新增代码+ClaudeCodeParity：定义 zoom 区域参数；如果没有这一行，模型不知道如何传局部观察区域。
        _tool("hold_key", "按住一个键一小段时间后释放。", {"key": {"type": "string"}, "duration_seconds": {"type": "number"}, "reason": {"type": "string"}}, ["key"]),  # 新增代码+ClaudeCodeParity：定义按住键工具；如果没有这一行，修饰键保持动作没有 schema。
        _tool("left_click_drag", "按住左键从起点拖拽到终点。", {"start_x": point["x"], "start_y": point["y"], "end_x": point["x"], "end_y": point["y"], "duration_seconds": {"type": "number"}, "reason": {"type": "string"}}, ["start_x", "start_y", "end_x", "end_y"]),  # 新增代码+ClaudeCodeParity：定义拖拽起终点；如果没有这一行，绘图和拖放工具无法调用。
        _tool("middle_click", "在指定坐标执行鼠标中键点击。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ClaudeCodeParity：定义中键点击；如果没有这一行，中键工具无法进入 tools/list。
        _tool("triple_click", "在指定坐标执行左键三击。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ClaudeCodeParity：定义三击；如果没有这一行，三击工具无法进入 tools/list。
        _tool("left_mouse_down", "在指定坐标按下左键但不立刻释放。", {**point, "reason": {"type": "string"}}, ["x", "y"]),  # 新增代码+ClaudeCodeParity：定义左键按下；如果没有这一行，分段拖拽无法开始。
        _tool("left_mouse_up", "释放当前按下的左键。", {"reason": {"type": "string"}}, []),  # 新增代码+ClaudeCodeParity：定义左键释放；如果没有这一行，分段拖拽无法安全结束。
```

In `tool_scope.py`, add the 7 raw names to `COMPUTER_USE_OPERATION_RAW_TOOL_NAMES` and remove `middle_click`, `triple_click`, `left_mouse_down`, `left_mouse_up` from `COMPUTER_USE_RESERVED_RAW_TOOL_NAMES`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/tests/test_computer_use_mcp_v2_contract.py learning_agent/tests/test_computer_use_tool_scope.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/tools/tool_scope.py
git commit -m "feat: expose ClaudeCode computer use parity tools"
```

---

### Task 2: No-Host Failure and Host Bridge Methods

**Files:**
- Modify: `learning_agent/tests/test_computer_use_mcp_v2_contract.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py`

- [ ] **Step 1: Write failing no-host and host bridge tests**

Add tests to `test_computer_use_mcp_v2_contract.py`.

```python
    def test_mutating_actions_fail_without_host(self) -> None:  # 新增代码+ClaudeCodeParity：验证无 host 时真实桌面动作不能假成功；如果没有这个测试，no-op 成功会继续误导模型。
        result = dispatch_computer_use_mcp_v2_tool("mcp__computer-use__left_click", {"x": 1, "y": 2}, ComputerUseMcpV2Context())  # 新增代码+ClaudeCodeParity：构造没有 host 的点击调用；如果没有这一行，测试无法复现假成功路径。
        self.assertFalse(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言点击失败；如果没有这一行，no-host 成功不会被拦住。
        self.assertEqual("host_required", result["error_class"])  # 新增代码+ClaudeCodeParity：断言失败类别稳定；如果没有这一行，模型无法按错误恢复。
        self.assertFalse(result["payload"]["desktop_action_performed"])  # 新增代码+ClaudeCodeParity：断言真实桌面未触碰；如果没有这一行，失败结果缺少安全证据。

    def test_new_parity_tools_dispatch_to_host_methods(self) -> None:  # 新增代码+ClaudeCodeParity：验证新增工具会优先调用 host；如果没有这个测试，schema 可见但执行可能断开。
        host = _FakeParityHost()  # 新增代码+ClaudeCodeParity：创建记录型 host；如果没有这一行，无法断言调用了哪个方法。
        context = ComputerUseMcpV2Context(host=host)  # 新增代码+ClaudeCodeParity：把 host 注入 v2 context；如果没有这一行，runtime 会走 no-host 失败。
        for name in ("zoom", "hold_key", "left_click_drag", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up"):  # 新增代码+ClaudeCodeParity：覆盖 7 个新增工具；如果没有这一行，可能漏掉某个工具。
            result = dispatch_computer_use_mcp_v2_tool(f"mcp__computer-use__{name}", {"x": 1, "y": 2, "key": "shift", "start_x": 1, "start_y": 2, "end_x": 3, "end_y": 4, "width": 20, "height": 10}, context)  # 新增代码+ClaudeCodeParity：用宽松参数调用工具；如果没有这一行，host 方法不会被触发。
            self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言 host 结果被包装为成功；如果没有这一行，新增工具执行路径可能失败。
        self.assertEqual(["zoom", "hold_key", "left_click_drag", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up"], host.calls)  # 新增代码+ClaudeCodeParity：断言所有工具均命中同名 host 方法；如果没有这一行，host bridge 漏方法不会暴露。
```

Add fake host:

```python
class _FakeParityHost(_FakeV2Host):  # 新增代码+ClaudeCodeParity：扩展现有 fake host 覆盖新增工具；如果没有这个类，新增工具 dispatch 测试会依赖真实桌面。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeParity：初始化调用记录；如果没有这一行，测试无法断言调用顺序。
        self.calls: list[str] = []  # 新增代码+ClaudeCodeParity：保存被调用工具名；如果没有这一行，host bridge 是否命中不可见。

    def _ok(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：统一返回 fake 成功；如果没有这个 helper，每个方法都要重复包装。
        self.calls.append(name)  # 新增代码+ClaudeCodeParity：记录工具名；如果没有这一行，测试无法判断 dispatch 目标。
        return {"ok": True, "tool_name": name, "arguments": dict(arguments)}  # 新增代码+ClaudeCodeParity：返回结构化 fake payload；如果没有这一行，runtime 没有可包装结果。

    def zoom(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("zoom", arguments)  # 新增代码+ClaudeCodeParity：fake zoom 方法；如果没有这一行，zoom 会走失败路径。
    def hold_key(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("hold_key", arguments)  # 新增代码+ClaudeCodeParity：fake hold_key 方法；如果没有这一行，hold_key 会走失败路径。
    def left_click_drag(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("left_click_drag", arguments)  # 新增代码+ClaudeCodeParity：fake drag 方法；如果没有这一行，拖拽会走失败路径。
    def middle_click(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("middle_click", arguments)  # 新增代码+ClaudeCodeParity：fake 中键方法；如果没有这一行，中键会走失败路径。
    def triple_click(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("triple_click", arguments)  # 新增代码+ClaudeCodeParity：fake 三击方法；如果没有这一行，三击会走失败路径。
    def left_mouse_down(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("left_mouse_down", arguments)  # 新增代码+ClaudeCodeParity：fake 左键按下方法；如果没有这一行，按下会走失败路径。
    def left_mouse_up(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._ok("left_mouse_up", arguments)  # 新增代码+ClaudeCodeParity：fake 左键释放方法；如果没有这一行，释放会走失败路径。
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract
```

Expected: FAIL. The first failure should show no-host action still returns success or new tools return `unknown_tool`.

- [ ] **Step 3: Implement action failure and bridge methods**

In `actions.py`, add a mutating tool set and no-host failure helper.

```python
MUTATING_DESKTOP_TOOL_NAMES = {"mouse_move", "left_click", "double_click", "right_click", "type", "key", "scroll", "hold_key", "left_click_drag", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up"}  # 新增代码+ClaudeCodeParity：集中列出会改变桌面的工具；如果没有这行代码，无 host 失败规则会散落。

def _host_required_failure(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，返回无 host 明确失败；如果没有这段函数，动作会继续假成功。
    return error_result(tool_name, f"host_required_for_desktop_action:{tool_name}", error_class="host_required", payload={"requires_host": True, "desktop_action_performed": False})  # 新增代码+ClaudeCodeParity：返回机器可读失败；如果没有这一行，模型不知道动作没有发生。
```

Replace no-op branches in `perform_action()` with:

```python
    if tool_name in MUTATING_DESKTOP_TOOL_NAMES:  # 修改代码+ClaudeCodeParity：无 host 的桌面动作必须失败；如果没有这一行，模型会误以为真实点击已发生。
        return _host_required_failure(tool_name)  # 修改代码+ClaudeCodeParity：返回明确失败；如果没有这一行，no-op 成功问题会继续存在。
```

In `legacy_ports.py`, add methods to `ComputerUseMcpV2LegacyHostAdapter`:

```python
    def zoom(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("zoom", arguments)  # 新增代码+ClaudeCodeParity：把 zoom 接到旧 session adapter；如果没有这一行，生产 host 无法执行 zoom。
    def hold_key(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("hold_key", arguments)  # 新增代码+ClaudeCodeParity：把 hold_key 接到旧 session adapter；如果没有这一行，生产 host 无法执行按住键。
    def left_click_drag(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("left_click_drag", arguments)  # 新增代码+ClaudeCodeParity：把拖拽接到旧 session adapter；如果没有这一行，生产 host 无法执行拖拽。
    def middle_click(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("middle_click", arguments)  # 新增代码+ClaudeCodeParity：把中键接到旧 session adapter；如果没有这一行，生产 host 无法执行中键。
    def triple_click(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("triple_click", arguments)  # 新增代码+ClaudeCodeParity：把三击接到旧 session adapter；如果没有这一行，生产 host 无法执行三击。
    def left_mouse_down(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("left_mouse_down", arguments)  # 新增代码+ClaudeCodeParity：把左键按下接到旧 session adapter；如果没有这一行，分段拖拽无法开始。
    def left_mouse_up(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("left_mouse_up", arguments)  # 新增代码+ClaudeCodeParity：把左键释放接到旧 session adapter；如果没有这一行，分段拖拽无法结束。
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/tests/test_computer_use_mcp_v2_contract.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py
git commit -m "fix: fail computer use desktop actions without host"
```

---

### Task 3: Session Adapter Mappings for New Tools

**Files:**
- Modify: `learning_agent/tests/test_computer_use_mcp_session_adapter.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`

- [ ] **Step 1: Write failing adapter mapping tests**

Add tests:

```python
    def test_left_click_drag_maps_to_drag_path(self) -> None:  # 新增代码+ClaudeCodeParity：验证 ClaudeCode 拖拽工具映射到 Windows drag_path；如果没有这个测试，拖拽可能只暴露不执行。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+ClaudeCodeParity：创建 fake adapter；如果没有这一行，测试会误碰真实桌面。
        adapter.state.last_observed_window = {"app_id": "fake-app.exe", "window_id": "hwnd:100"}  # 新增代码+ClaudeCodeParity：模拟已观察窗口；如果没有这一行，动作会被缺目标门禁挡住。
        result = adapter.call_atomic_tool("left_click_drag", {"start_x": 1, "start_y": 2, "end_x": 9, "end_y": 10, "duration_seconds": 0.2})  # 新增代码+ClaudeCodeParity：调用拖拽工具；如果没有这一行，映射不会被覆盖。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言 fake controller 成功；如果没有这一行，失败路径可能被忽略。
        self.assertEqual("drag_path", controller.executed[0]["action"])  # 新增代码+ClaudeCodeParity：断言动作映射为 drag_path；如果没有这一行，拖拽语义可能漂移。
        self.assertEqual([{"x": 1, "y": 2}, {"x": 9, "y": 10}], controller.executed[0]["points"])  # 新增代码+ClaudeCodeParity：断言起终点正确；如果没有这一行，拖拽路径可能反向或缺点。

    def test_new_mouse_tools_map_to_controller_actions(self) -> None:  # 新增代码+ClaudeCodeParity：验证中键、三击、鼠标按下释放映射；如果没有这个测试，新增工具可能继续 unsupported。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+ClaudeCodeParity：创建 fake adapter；如果没有这一行，测试无法运行。
        adapter.state.last_observed_window = {"app_id": "fake-app.exe", "window_id": "hwnd:100"}  # 新增代码+ClaudeCodeParity：模拟可复用窗口；如果没有这一行，高风险动作缺目标。
        for tool_name in ("middle_click", "triple_click", "left_mouse_down", "left_mouse_up", "hold_key"):  # 新增代码+ClaudeCodeParity：覆盖剩余新增动作；如果没有这一行，可能漏掉工具。
            adapter.call_atomic_tool(tool_name, {"x": 3, "y": 4, "key": "shift", "duration_seconds": 0.1})  # 新增代码+ClaudeCodeParity：调用工具；如果没有这一行，映射不会触发。
        self.assertEqual(["click", "triple_click", "mouse_down", "mouse_up", "hold_key"], [item["action"] for item in controller.executed])  # 新增代码+ClaudeCodeParity：断言映射到 controller action；如果没有这一行，真实执行层无法对齐。
        self.assertEqual("middle", controller.executed[0]["button"])  # 新增代码+ClaudeCodeParity：断言 middle_click 使用中键；如果没有这一行，中键可能误当左键。
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_session_adapter
```

Expected: FAIL. `triple_click`, `left_mouse_down`, or `left_mouse_up` should still report `unsupported_computer_use_tool`.

- [ ] **Step 3: Implement adapter mapping**

In `ComputerUseMcpSessionState`, add pressed mouse state.

```python
    pressed_mouse_buttons: set[str] = field(default_factory=set)  # 新增代码+ClaudeCodeParity：记录跨工具保持按下的鼠标按钮；如果没有这一行，cleanup 和 left_mouse_up 不知道当前状态。
```

In `_action_can_reuse_observed_window()`, include:

```python
    reusable_actions = {"click", "double_click", "move_mouse", "type_text", "press_key", "scroll", "drag_path", "triple_click", "mouse_down", "mouse_up", "hold_key"}  # 修改代码+ClaudeCodeParity：新增工具也复用最近观察窗口；如果没有这一行，observe 后新增动作仍会缺 window。
```

In `call_atomic_tool()`, remove the unsupported branch for `triple_click`, `left_mouse_down`, `left_mouse_up`.

In `_controller_arguments_for_tool()`, add:

```python
    if tool_name == "triple_click":  # 新增代码+ClaudeCodeParity：支持 ClaudeCode 三击工具；如果没有这一行，三击会落入未知动作。
        return {"action": "triple_click", "x": arguments.get("x"), "y": arguments.get("y"), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity：返回三击 controller 参数；如果没有这一行，底层执行器无法生成三次点击。
    if tool_name == "left_mouse_down":  # 新增代码+ClaudeCodeParity：支持分段左键按下；如果没有这一行，精细拖拽无法开始。
        return {"action": "mouse_down", "x": arguments.get("x"), "y": arguments.get("y"), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity：返回按下参数；如果没有这一行，controller 不知道要保持鼠标状态。
    if tool_name == "left_mouse_up":  # 新增代码+ClaudeCodeParity：支持分段左键释放；如果没有这一行，精细拖拽无法结束。
        return {"action": "mouse_up", "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity：返回释放参数；如果没有这一行，controller 不知道要释放左键。
    if tool_name == "hold_key":  # 新增代码+ClaudeCodeParity：支持按住键盘工具；如果没有这一行，修饰键保持动作无法执行。
        return {"action": "hold_key", "key": arguments.get("key", ""), "duration_seconds": arguments.get("duration_seconds", 0.1), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity：返回按住键参数；如果没有这一行，底层无法生成 key_down/pause/key_up。
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_session_adapter
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/tests/test_computer_use_mcp_session_adapter.py learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py
git commit -m "feat: map ClaudeCode parity tools to Windows session actions"
```

---

### Task 4: SendInput Executor and Dispatcher Support

**Files:**
- Modify: `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`
- Modify: `learning_agent/tests/test_windows_computer_use_sendinput_dispatcher_phase47.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_executor.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_dispatcher.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py`

- [ ] **Step 1: Write failing SendInput tests**

In `test_windows_computer_use_sendinput_dispatcher_phase47.py`, add:

```python
    def test_dispatcher_expands_parity_mouse_and_hold_key_actions(self) -> None:  # 新增代码+ClaudeCodeParity：验证新增鼠标和按键保持动作能展开到底层事件；如果没有这个测试，工具可能只到 controller 不到 SendInput。
        verifier = Phase47TargetVerifier(ok=True)  # 新增代码+ClaudeCodeParity：创建稳定目标校验器；如果没有这一行，发送会被目标门禁挡住。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+ClaudeCodeParity：创建记录 sender；如果没有这一行，测试会触碰真实鼠标键盘。
        executor = self._executor(verifier, sender)  # 新增代码+ClaudeCodeParity：创建 executor-dispatcher 链；如果没有这一行，动作无法进入 dispatcher。
        self.assertTrue(executor.execute("triple_click", {"x": 10, "y": 20}).ok)  # 新增代码+ClaudeCodeParity：验证三击；如果没有这一行，triple_click 展开不会被覆盖。
        self.assertTrue(executor.execute("mouse_down", {"x": 10, "y": 20, "button": "left"}).ok)  # 新增代码+ClaudeCodeParity：验证鼠标按下；如果没有这一行，分段拖拽起点不被覆盖。
        self.assertTrue(executor.execute("mouse_up", {"button": "left"}).ok)  # 新增代码+ClaudeCodeParity：验证鼠标释放；如果没有这一行，分段拖拽闭合不被覆盖。
        self.assertTrue(executor.execute("hold_key", {"key": "shift", "duration_seconds": 0.01}).ok)  # 新增代码+ClaudeCodeParity：验证按住键；如果没有这一行，key_down/pause/key_up 不被覆盖。
        event_types = [event["type"] for event in sender.low_level_events]  # 新增代码+ClaudeCodeParity：收集低层事件类型；如果没有这一行，无法断言展开结果。
        self.assertGreaterEqual(event_types.count("mouse_down"), 5)  # 新增代码+ClaudeCodeParity：三击加显式按下至少产生多次 mouse_down；如果没有这一行，三击可能只点一次。
        self.assertGreaterEqual(event_types.count("mouse_up"), 5)  # 新增代码+ClaudeCodeParity：三击加显式释放至少产生多次 mouse_up；如果没有这一行，鼠标可能卡住。
        self.assertIn("key_down", event_types)  # 新增代码+ClaudeCodeParity：断言按键按下存在；如果没有这一行，hold_key 只有等待没有按键。
        self.assertIn("key_up", event_types)  # 新增代码+ClaudeCodeParity：断言按键释放存在；如果没有这一行，hold_key 可能造成卡键。
        self.assertIn("pause", event_types)  # 新增代码+ClaudeCodeParity：断言按住期间有受控暂停；如果没有这一行，hold_key 退化成普通 key。
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_sendinput_dispatcher_phase47
```

Expected: FAIL. `SendInput 执行器不支持动作：triple_click` or empty low-level event expansion should appear.

- [ ] **Step 3: Implement executor actions**

In `sendinput_executor.py`, extend supported actions:

```python
PHASE37_SUPPORTED_ACTIONS = ("click", "double_click", "drag_path", "move_mouse", "press_key", "scroll", "type_text", "triple_click", "mouse_down", "mouse_up", "hold_key")  # 修改代码+ClaudeCodeParity：声明新增 ClaudeCode parity 动作；如果没有这一行，执行器会在入口拒绝新增工具。
```

Add `_events_for_action()` branches:

```python
        if action == "triple_click":  # 新增代码+ClaudeCodeParity：生成三击规范事件；如果没有这一行，三击无法进入 dispatcher。
            event = {"type": "triple_click", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y")), "button": "left"}  # 新增代码+ClaudeCodeParity：固定三击为左键；如果没有这一行，底层不知道点击位置。
            return [event], {}, None  # 新增代码+ClaudeCodeParity：返回三击事件；如果没有这一行，execute 无法继续分发。
        if action == "mouse_down":  # 新增代码+ClaudeCodeParity：生成鼠标按下规范事件；如果没有这一行，分段拖拽无法开始。
            event = {"type": "mouse_down", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y")), "button": str(arguments.get("button", "left"))}  # 新增代码+ClaudeCodeParity：保留坐标和按钮；如果没有这一行，底层无法按下指定按钮。
            return [event], {"button": event["button"]}, None  # 新增代码+ClaudeCodeParity：返回按下事件；如果没有这一行，execute 无法继续分发。
        if action == "mouse_up":  # 新增代码+ClaudeCodeParity：生成鼠标释放规范事件；如果没有这一行，分段拖拽无法闭合。
            event = {"type": "mouse_up", "button": str(arguments.get("button", "left"))}  # 新增代码+ClaudeCodeParity：保留释放按钮；如果没有这一行，底层无法释放指定按钮。
            return [event], {"button": event["button"]}, None  # 新增代码+ClaudeCodeParity：返回释放事件；如果没有这一行，execute 无法继续分发。
        if action == "hold_key":  # 新增代码+ClaudeCodeParity：生成按住键规范事件；如果没有这一行，hold_key 无法进入 dispatcher。
            key = str(arguments.get("key", "")).strip()[:80]  # 新增代码+ClaudeCodeParity：读取并限制键名；如果没有这一行，坏键名可能污染日志。
            if not key:  # 新增代码+ClaudeCodeParity：拒绝空键；如果没有这一行，底层可能收到无意义按键。
                return [], {}, self._refusal(action, "hold_key 缺少 key 参数，未调用 SendInput。", {"missing": "key"})  # 新增代码+ClaudeCodeParity：返回缺参失败；如果没有这一行，模型不知道如何修正。
            event = {"type": "hold_key", "key": key, "duration_seconds": max(0.0, min(float(arguments.get("duration_seconds", 0.1) or 0.1), 5.0))}  # 新增代码+ClaudeCodeParity：限制按住时间；如果没有这一行，模型可能让按键长期保持。
            return [event], {"key": key}, None  # 新增代码+ClaudeCodeParity：返回按住键事件；如果没有这一行，execute 无法继续分发。
```

- [ ] **Step 4: Implement dispatcher expansion**

In `sendinput_dispatcher.py`, add `_expand_event()` branches:

```python
        if event_type == "triple_click":  # 新增代码+ClaudeCodeParity：展开三击；如果没有这一行，triple_click 不会产生鼠标事件。
            button = str(event.get("button", "left"))  # 新增代码+ClaudeCodeParity：读取按钮；如果没有这一行，三击按钮不稳定。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}, {"type": "mouse_down", "button": button}, {"type": "mouse_up", "button": button}, {"type": "mouse_down", "button": button}, {"type": "mouse_up", "button": button}, {"type": "mouse_down", "button": button}, {"type": "mouse_up", "button": button}], target)  # 新增代码+ClaudeCodeParity：返回三次按下抬起；如果没有这一行，三击会退化成单击。
        if event_type == "mouse_down":  # 新增代码+ClaudeCodeParity：展开显式鼠标按下；如果没有这一行，left_mouse_down 不会触发。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}, {"type": "mouse_down", "button": str(event.get("button", "left"))}], target)  # 新增代码+ClaudeCodeParity：先移动再按下；如果没有这一行，按下位置不可靠。
        if event_type == "mouse_up":  # 新增代码+ClaudeCodeParity：展开显式鼠标释放；如果没有这一行，left_mouse_up 不会触发。
            return _phase47_attach_target([{"type": "mouse_up", "button": str(event.get("button", "left"))}], target)  # 新增代码+ClaudeCodeParity：释放指定按钮；如果没有这一行，鼠标可能卡住。
        if event_type == "hold_key":  # 新增代码+ClaudeCodeParity：展开按住键；如果没有这一行，hold_key 无法保持按下状态。
            key = str(event.get("key", "")).strip()  # 新增代码+ClaudeCodeParity：读取键名；如果没有这一行，低层事件没有目标键。
            seconds = max(0.0, min(float(event.get("duration_seconds", 0.1) or 0.1), 5.0))  # 新增代码+ClaudeCodeParity：限制保持时间；如果没有这一行，按键可能被保持太久。
            return _phase47_attach_target([{"type": "key_down", "key": key}, {"type": "pause", "seconds": seconds}, {"type": "key_up", "key": key}], target) if key else []  # 新增代码+ClaudeCodeParity：确保 finally 语义由事件序列释放；如果没有这一行，hold_key 会卡键。
```

- [ ] **Step 5: Add middle mouse support to the low-level sender**

In `real_sendinput_guard.py`, update `_send_mouse_button()` flag selection:

```python
        button_name = button.lower()  # 修改代码+ClaudeCodeParity：规范按钮名称；如果没有这一行，中键大小写会导致错误分支。
        flag = 0x0002 if button_name == "left" and down else 0x0004 if button_name == "left" else 0x0008 if button_name == "right" and down else 0x0010 if button_name == "right" else 0x0020 if button_name == "middle" and down else 0x0040 if button_name == "middle" else 0  # 修改代码+ClaudeCodeParity：支持左/右/中键按下抬起；如果没有这一行，middle_click 会被当成右键或空事件。
        if flag == 0:  # 新增代码+ClaudeCodeParity：拒绝未知按钮；如果没有这一行，坏按钮可能构造无意义 SendInput。
            return False  # 新增代码+ClaudeCodeParity：未知按钮不发送；如果没有这一行，调用方无法知道动作失败。
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_sendinput_phase37 learning_agent.tests.test_windows_computer_use_sendinput_dispatcher_phase47
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/tests/test_windows_computer_use_sendinput_phase37.py learning_agent/tests/test_windows_computer_use_sendinput_dispatcher_phase47.py learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_executor.py learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_dispatcher.py learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py
git commit -m "feat: execute ClaudeCode parity mouse and keyboard actions"
```

---

### Task 5: Real Windows Clipboard

**Files:**
- Create: `learning_agent/computer_use_mcp_v2/windows_runtime/clipboard_io.py`
- Create: `learning_agent/tests/test_windows_computer_use_clipboard_io.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py`

- [ ] **Step 1: Write failing clipboard tests**

Create `test_windows_computer_use_clipboard_io.py`.

```python
from __future__ import annotations  # 新增代码+ClaudeCodeParity：延迟类型解析；如果没有这一行，测试导入更脆弱。

import unittest  # 新增代码+ClaudeCodeParity：使用 unittest；如果没有这一行，测试不会被发现。

from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionState  # 新增代码+ClaudeCodeParity：导入 session adapter；如果没有这一行，测试无法覆盖生产 clipboard 路径。


class _FakeClipboardBackend:  # 新增代码+ClaudeCodeParity：定义 fake 系统剪贴板；如果没有这个类，单测会改用户真实剪贴板。
    def __init__(self) -> None: self.text = ""  # 新增代码+ClaudeCodeParity：保存 fake 文本；如果没有这一行，读写没有状态。
    def read_text(self) -> dict[str, object]: return {"ok": True, "text": self.text, "backend": "fake_system_clipboard"}  # 新增代码+ClaudeCodeParity：模拟读取；如果没有这一行，read_clipboard 无法测试。
    def write_text(self, text: str) -> dict[str, object]: self.text = str(text); return {"ok": True, "text_length": len(self.text), "backend": "fake_system_clipboard"}  # 新增代码+ClaudeCodeParity：模拟写入；如果没有这一行，write_clipboard 无法测试。


class WindowsComputerUseClipboardIoTests(unittest.TestCase):  # 新增代码+ClaudeCodeParity：测试真实 clipboard adapter 边界；如果没有这个类，clipboard 对齐没有保护。
    def test_session_adapter_uses_system_clipboard_backend(self) -> None:  # 新增代码+ClaudeCodeParity：验证 session adapter 不再只写内存 clipboard；如果没有这个测试，旧 session clipboard 会回归。
        backend = _FakeClipboardBackend()  # 新增代码+ClaudeCodeParity：创建 fake backend；如果没有这一行，测试会触碰系统剪贴板。
        state = ComputerUseMcpSessionState()  # 新增代码+ClaudeCodeParity：创建 session 状态；如果没有这一行，adapter 无法构造。
        state.clipboard_backend = backend  # 新增代码+ClaudeCodeParity：注入 fake 系统剪贴板；如果没有这一行，adapter 会使用默认后端。
        adapter = ComputerUseMcpSessionAdapter(controller=object(), state=state)  # 新增代码+ClaudeCodeParity：创建 adapter；如果没有这一行，测试没有执行主体。
        write_result = adapter.call_atomic_tool("write_clipboard", {"text": "hello"})  # 新增代码+ClaudeCodeParity：执行写入；如果没有这一行，backend 不会被调用。
        read_result = adapter.call_atomic_tool("read_clipboard", {})  # 新增代码+ClaudeCodeParity：执行读取；如果没有这一行，无法验证写入结果。
        self.assertTrue(write_result["ok"], write_result)  # 新增代码+ClaudeCodeParity：断言写入成功；如果没有这一行，失败会被忽略。
        self.assertEqual("hello", read_result["payload"]["text"])  # 新增代码+ClaudeCodeParity：断言读取来自 backend；如果没有这一行，旧内存路径可能冒充成功。
        self.assertEqual("fake_system_clipboard", read_result["payload"]["backend"])  # 新增代码+ClaudeCodeParity：断言后端来源；如果没有这一行，无法区分系统和内存。


if __name__ == "__main__":  # 新增代码+ClaudeCodeParity：允许单文件运行；如果没有这一行，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeParity：启动 unittest；如果没有这一行，直接运行没有测试。
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_clipboard_io
```

Expected: FAIL because `ComputerUseMcpSessionState` has no `clipboard_backend` or adapter still reports `agent_session_memory_clipboard`.

- [ ] **Step 3: Create Windows clipboard helper**

Create `clipboard_io.py`:

```python
"""Windows 文本剪贴板读写 helper。"""  # 新增代码+ClaudeCodeParity：说明本文件只负责真实系统剪贴板；如果没有这行代码，读者容易把它和反推契约层混淆。
from __future__ import annotations  # 新增代码+ClaudeCodeParity：延迟类型解析；如果没有这行代码，导入顺序更脆弱。

from typing import Any  # 新增代码+ClaudeCodeParity：标注 JSON 结果；如果没有这行代码，返回边界不清楚。


class WindowsClipboardTextIO:  # 新增代码+ClaudeCodeParity：类段开始，封装 Win32 文本剪贴板；如果没有这个类，adapter 会直接写 ctypes 平台细节。
    def read_text(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，读取 Unicode 文本；如果没有这段函数，read_clipboard 不能读系统剪贴板。
        from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+ClaudeCodeParity：复用既有 Win32 剪贴板读取实现；如果没有这一行，会重复低层 API 代码。
        text = WindowsSendInputLowLevelSender()._clipboard_text()  # 新增代码+ClaudeCodeParity：读取系统剪贴板文本；如果没有这一行，工具拿不到真实剪贴板。
        if text is None:  # 新增代码+ClaudeCodeParity：处理无文本或读取失败；如果没有这一行，None 会被当成字符串。
            return {"ok": False, "reason": "system_clipboard_text_unavailable", "backend": "windows_system_clipboard"}  # 新增代码+ClaudeCodeParity：返回可恢复失败；如果没有这一行，模型不知道剪贴板不可读。
        return {"ok": True, "text": text, "text_length": len(text), "backend": "windows_system_clipboard"}  # 新增代码+ClaudeCodeParity：返回真实文本和长度；如果没有这一行，模型无法读取剪贴板内容。

    def write_text(self, text: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，写入 Unicode 文本；如果没有这段函数，write_clipboard 不能写系统剪贴板。
        from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+ClaudeCodeParity：复用既有 Win32 剪贴板写入实现；如果没有这一行，会重复低层 API 代码。
        ok = WindowsSendInputLowLevelSender()._set_clipboard_text(str(text))  # 新增代码+ClaudeCodeParity：写入系统剪贴板；如果没有这一行，系统剪贴板不会变化。
        return {"ok": bool(ok), "text_length": len(str(text)), "backend": "windows_system_clipboard", "reason": "" if ok else "system_clipboard_write_failed"}  # 新增代码+ClaudeCodeParity：返回写入摘要；如果没有这一行，模型无法判断写入是否成功。
```

- [ ] **Step 4: Wire clipboard through session adapter and host bridge**

In `ComputerUseMcpSessionState`, add:

```python
    clipboard_backend: Any | None = None  # 新增代码+ClaudeCodeParity：保存可注入系统剪贴板后端；如果没有这一行，单测只能触碰真实剪贴板。
```

In `_call_clipboard()`, replace session-memory read/write with backend calls:

```python
        backend = self.state.clipboard_backend  # 新增代码+ClaudeCodeParity：读取注入后端；如果没有这一行，测试无法隔离系统剪贴板。
        if backend is None:  # 新增代码+ClaudeCodeParity：缺省创建真实 Windows 后端；如果没有这一行，生产 clipboard 没有系统能力。
            from learning_agent.computer_use_mcp_v2.windows_runtime.clipboard_io import WindowsClipboardTextIO  # 新增代码+ClaudeCodeParity：延迟导入平台实现；如果没有这一行，contract 层会被平台导入污染。
            backend = WindowsClipboardTextIO()  # 新增代码+ClaudeCodeParity：创建真实剪贴板后端；如果没有这一行，read/write 仍是内存状态。
            self.state.clipboard_backend = backend  # 新增代码+ClaudeCodeParity：缓存后端供本会话复用；如果没有这一行，多次调用无法共享注入后端。
```

Wrap backend read/write results with the existing `_json_result()` helper so failures remain machine-readable:

```python
        if tool_name == "read_clipboard":  # 修改代码+ClaudeCodeParity：读剪贴板必须走后端；如果没有这一行，read_clipboard 会继续读会话内存。
            payload = dict(backend.read_text())  # 新增代码+ClaudeCodeParity：读取真实或注入剪贴板后端；如果没有这一行，工具无法得到系统剪贴板内容。
            return _json_result(tool_name, bool(payload.get("ok")), payload, error_class=None if payload.get("ok") else "clipboard_unavailable")  # 修改代码+ClaudeCodeParity：把后端结果包装成 MCP JSON；如果没有这一行，失败原因无法稳定传给模型。
        if tool_name == "write_clipboard":  # 修改代码+ClaudeCodeParity：写剪贴板必须走后端；如果没有这一行，write_clipboard 会继续只改会话状态。
            payload = dict(backend.write_text(str(arguments.get("text", ""))))  # 新增代码+ClaudeCodeParity：把文本写入真实或注入剪贴板后端；如果没有这一行，系统剪贴板不会变化。
            return _json_result(tool_name, bool(payload.get("ok")), payload, error_class=None if payload.get("ok") else "clipboard_unavailable")  # 修改代码+ClaudeCodeParity：把写入结果包装成 MCP JSON；如果没有这一行，模型无法判断写入是否成功。
```

In `legacy_ports.py`, add:

```python
    def read_clipboard(self, arguments: dict[str, Any] | None = None) -> dict[str, Any]: return self._call("read_clipboard", arguments or {})  # 新增代码+ClaudeCodeParity：把 read_clipboard 接到 session adapter；如果没有这一行，契约层读剪贴板无法走系统后端。
    def write_clipboard(self, arguments: dict[str, Any]) -> dict[str, Any]: return self._call("write_clipboard", arguments)  # 新增代码+ClaudeCodeParity：把 write_clipboard 接到 session adapter；如果没有这一行，契约层写剪贴板无法走系统后端。
```

In `inferred_ant_mcp/clipboard.py`, use host methods first and fail if no host:

```python
    method = getattr(context.host, "read_clipboard", None) if context.host is not None else None  # 新增代码+ClaudeCodeParity：读取 host 剪贴板方法；如果没有这一行，契约层无法接生产系统 clipboard。
```

- [ ] **Step 5: Run clipboard tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_clipboard_io learning_agent.tests.test_computer_use_mcp_session_adapter
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/tests/test_windows_computer_use_clipboard_io.py learning_agent/computer_use_mcp_v2/windows_runtime/clipboard_io.py learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py
git commit -m "feat: use real Windows clipboard for computer use"
```

---

### Task 6: Dynamic tools/list App Hints

**Files:**
- Create: `learning_agent/tests/test_computer_use_mcp_dynamic_tools_list.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/hostAdapter.py`

- [ ] **Step 1: Write failing dynamic tools/list tests**

Create `test_computer_use_mcp_dynamic_tools_list.py`.

```python
from __future__ import annotations  # 新增代码+ClaudeCodeParity：延迟类型解析；如果没有这一行，测试导入更脆弱。

import unittest  # 新增代码+ClaudeCodeParity：使用 unittest；如果没有这一行，测试不会被发现。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import handle_json_rpc_message  # 新增代码+ClaudeCodeParity：导入 JSON-RPC tools/list 入口；如果没有这一行，测试不能覆盖 MCP server。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context  # 新增代码+ClaudeCodeParity：导入上下文；如果没有这一行，无法注入 fake host。


class _HintHost:  # 新增代码+ClaudeCodeParity：定义动态提示 fake host；如果没有这个类，测试会依赖真实 Windows app inventory。
    def dynamic_tool_hints(self) -> dict[str, object]:  # 新增代码+ClaudeCodeParity：返回动态工具提示；如果没有这一行，tools/list 无动态来源。
        return {"available_applications": ["Notepad", "Paint"], "granted_applications": ["Notepad"], "recent_safe_windows": ["Untitled - Notepad"]}  # 新增代码+ClaudeCodeParity：提供 app/grant/window 摘要；如果没有这一行，无法断言 description/_meta 增强。


class ComputerUseMcpDynamicToolsListTests(unittest.TestCase):  # 新增代码+ClaudeCodeParity：测试 tools/list 动态提示；如果没有这个类，ClaudeCode app hints 体验没有保护。
    def test_tools_list_includes_dynamic_application_hints(self) -> None:  # 新增代码+ClaudeCodeParity：验证 tools/list 带应用提示；如果没有这个测试，schema 会一直是静态描述。
        response = handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, ComputerUseMcpV2Context(host=_HintHost()))  # 新增代码+ClaudeCodeParity：调用 tools/list 并注入 fake hints；如果没有这一行，MCP server 不会被覆盖。
        tools = response["result"]["tools"]  # 新增代码+ClaudeCodeParity：读取工具列表；如果没有这一行，后续无法断言。
        open_app = next(tool for tool in tools if tool["name"] == "open_application")  # 新增代码+ClaudeCodeParity：定位打开应用工具；如果没有这一行，断言目标不清楚。
        self.assertIn("Notepad", open_app["description"])  # 新增代码+ClaudeCodeParity：断言可用应用出现在描述；如果没有这一行，模型仍看不到动态 app hint。
        self.assertIn("dynamic_hints", open_app["_meta"])  # 新增代码+ClaudeCodeParity：断言 meta 标记动态来源；如果没有这一行，调试无法确认 hints 生效。


if __name__ == "__main__":  # 新增代码+ClaudeCodeParity：允许单文件运行；如果没有这一行，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeParity：启动测试；如果没有这一行，直接运行无测试。
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_dynamic_tools_list
```

Expected: FAIL because `open_application` description does not include `Notepad`.

- [ ] **Step 3: Implement dynamic hints without putting Windows logic in inferred_ant_mcp**

In `build_tools.py`, change signature:

```python
def computer_use_mcp_tools(dynamic_hints: dict[str, Any] | None = None) -> list[dict[str, Any]]:  # 修改代码+ClaudeCodeParity：允许外层注入动态 app/grant/window 提示；如果没有这一行，tools/list 只能返回静态 schema。
```

After building `tools`, apply hints:

```python
    hints = dict(dynamic_hints or {})  # 新增代码+ClaudeCodeParity：复制动态提示避免污染调用方；如果没有这一行，schema helper 可能修改外部对象。
    app_names = [str(item) for item in hints.get("available_applications", []) if str(item).strip()]  # 新增代码+ClaudeCodeParity：读取可用应用名；如果没有这一行，open_application 无法增强描述。
    if app_names:  # 新增代码+ClaudeCodeParity：只有有动态应用时才增强；如果没有这一行，空提示会制造噪声。
        for tool in tools:  # 新增代码+ClaudeCodeParity：遍历工具 schema；如果没有这一行，无法找到 open_application。
            if tool.get("name") == "open_application":  # 新增代码+ClaudeCodeParity：只增强打开应用工具；如果没有这一行，所有工具描述会变吵。
                tool["description"] = f"{tool['description']} 当前可用应用示例：{', '.join(app_names[:12])}。"  # 新增代码+ClaudeCodeParity：注入 ClaudeCode 风格 app hints；如果没有这一行，模型不知道可打开什么应用。
                tool["_meta"]["dynamic_hints"] = {"available_applications": app_names[:12]}  # 新增代码+ClaudeCodeParity：写入机器可读动态提示；如果没有这一行，调试无法确认提示来源。
```

In `mcpServer.py`, add helper:

```python
def _dynamic_tool_hints(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，从 host 读取动态 tools/list 提示；如果没有这段函数，MCP server 会直接依赖静态 schema。
    method = getattr(context.host, "dynamic_tool_hints", None) if context.host is not None else None  # 新增代码+ClaudeCodeParity：读取 host hints 方法；如果没有这一行，server 无法接入 Windows inventory。
    if not callable(method):  # 新增代码+ClaudeCodeParity：host 不支持时返回空提示；如果没有这一行，独立 selftest 会失败。
        return {}  # 新增代码+ClaudeCodeParity：无动态信息时保持静态 schema；如果没有这一行，tools/list 可能崩溃。
    try:  # 新增代码+ClaudeCodeParity：保护动态 inventory 失败；如果没有这一行，tools/list 会被慢或坏 inventory 拖垮。
        result = method()  # 新增代码+ClaudeCodeParity：调用 host 动态提示；如果没有这一行，app hints 不会出现。
    except Exception as error:  # 新增代码+ClaudeCodeParity：捕获 host 异常；如果没有这一行，MCP 初始化可能失败。
        return {"dynamic_hints_error": type(error).__name__}  # 新增代码+ClaudeCodeParity：返回错误摘要；如果没有这一行，调试不知道动态信息为何缺失。
    return dict(result) if isinstance(result, dict) else {}  # 新增代码+ClaudeCodeParity：只接受 dict hints；如果没有这一行，坏返回值会污染 schema。
```

Change tools/list branch:

```python
        return _response(request_id, {"tools": computer_use_mcp_tools(_dynamic_tool_hints(context))})  # 修改代码+ClaudeCodeParity：把 host 动态提示注入工具列表；如果没有这一行，tools/list 仍是静态描述。
```

In `hostAdapter.py`, add a safe default:

```python
    def dynamic_tool_hints(self) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，提供独立 stdio server 的动态提示；如果没有这段函数，tools/list 无法显示 Windows 应用线索。
        try:  # 新增代码+ClaudeCodeParity：保护 app inventory 失败；如果没有这一行，tools/list 可能因本机环境问题失败。
            from learning_agent.computer_use_mcp_v2.windows_runtime.windows_app_inventory import query_windows_app_inventory  # 新增代码+ClaudeCodeParity：延迟导入 Windows app inventory；如果没有这一行，host adapter 无法发现应用。
            inventory = query_windows_app_inventory({})  # 新增代码+ClaudeCodeParity：读取应用库存；如果没有这一行，动态 app hints 没有数据来源。
            return {"available_applications": [str(item.get("name", "")) for item in inventory.get("applications", [])[:12] if isinstance(item, dict)]}  # 新增代码+ClaudeCodeParity：返回简短应用名列表；如果没有这一行，模型仍不知道可用应用。
        except Exception as error:  # 新增代码+ClaudeCodeParity：捕获 inventory 异常；如果没有这一行，tools/list 可能失败。
            return {"dynamic_hints_error": type(error).__name__}  # 新增代码+ClaudeCodeParity：返回错误摘要；如果没有这一行，缺提示原因不可见。
```

- [ ] **Step 4: Run dynamic list tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_v2_contract
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/tests/test_computer_use_mcp_dynamic_tools_list.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py learning_agent/computer_use_mcp_v2/claudecode_bridge/hostAdapter.py
git commit -m "feat: add dynamic app hints to computer use tools list"
```

---

### Task 7: Zoom Image Result and Batch Safety

**Files:**
- Modify: `learning_agent/tests/test_computer_use_mcp_session_adapter.py`
- Modify: `learning_agent/tests/test_computer_use_mcp_batch_safety.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py`

- [ ] **Step 1: Write failing zoom and batch tests**

In `test_computer_use_mcp_session_adapter.py`, add:

```python
    def test_zoom_maps_to_window_state_with_region(self) -> None:  # 新增代码+ClaudeCodeParity：验证 zoom 不是普通 observe，而是带区域的局部观察；如果没有这个测试，zoom 可能只返回整屏截图。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+ClaudeCodeParity：创建 fake adapter；如果没有这一行，测试无法运行。
        result = adapter.call_atomic_tool("zoom", {"x": 10, "y": 20, "width": 100, "height": 80, "reason": "unit zoom"})  # 新增代码+ClaudeCodeParity：调用 zoom；如果没有这一行，区域映射不会触发。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeParity：断言 fake observe 成功；如果没有这一行，后续断言可能读失败数据。
        self.assertEqual("get_window_state", controller.observed[1]["action"])  # 新增代码+ClaudeCodeParity：断言 zoom 仍走安全窗口观察；如果没有这一行，zoom 可能绕过目标窗口。
        self.assertEqual({"x": 10, "y": 20, "width": 100, "height": 80}, controller.observed[1]["region"])  # 新增代码+ClaudeCodeParity：断言区域传到 controller；如果没有这一行，局部观察无法实现。
```

In batch safety tests, add a case that `computer_batch` accepts new parity tools but still rejects `powershell` and `command`.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_batch_safety
```

Expected: FAIL if zoom does not include `region` or batch rejects the newly allowed tools.

- [ ] **Step 3: Implement zoom region mapping**

In `_controller_arguments_for_tool()`:

```python
    if tool_name == "zoom":  # 新增代码+ClaudeCodeParity：支持局部放大观察；如果没有这一行，zoom 会退化成普通 observe。
        region = {"x": arguments.get("x"), "y": arguments.get("y"), "width": arguments.get("width"), "height": arguments.get("height")}  # 新增代码+ClaudeCodeParity：保留局部区域；如果没有这一行，截图后无法裁剪。
        return {"action": "get_window_state", "region": region, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity：把 zoom 映射为带区域观察；如果没有这一行，controller 收不到局部观察意图。
```

In `image_messages.py`, preserve zoom region metadata alongside the screenshot message:

```python
    region = _nested_value(payload, ("payload", "legacy_payload", "region")) or _nested_value(payload, ("legacy_payload", "region"))  # 新增代码+ClaudeCodeParity：从 controller payload 里取出 zoom 区域；如果没有这一行，模型只能看到图片却不知道局部截图坐标。
    if isinstance(region, dict):  # 新增代码+ClaudeCodeParity：只接受字典区域，避免坏 payload 污染消息；如果没有这一行，异常格式可能破坏图片消息。
        text_parts.append(f"zoom_region={json.dumps(region, ensure_ascii=False, sort_keys=True)}")  # 新增代码+ClaudeCodeParity：把区域元数据写进模型可读文本；如果没有这一行，zoom 的局部观察语义会丢失。
```

Keep image cropping or screenshot capture in `windows_runtime/`; do not add image manipulation code to `inferred_ant_mcp/`.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_batch_safety
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/tests/test_computer_use_mcp_session_adapter.py learning_agent/tests/test_computer_use_mcp_batch_safety.py learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py
git commit -m "feat: support zoom region observations in computer use"
```

---

### Task 8: Final Verification and Visible Terminal Acceptance

**Files:**
- Modify: `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_tool_surface_visible_terminal.json`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: Run focused automated tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_batch_safety learning_agent.tests.test_windows_computer_use_sendinput_phase37 learning_agent.tests.test_windows_computer_use_sendinput_dispatcher_phase47 learning_agent.tests.test_windows_computer_use_clipboard_io learning_agent.tests.test_computer_use_mcp_dynamic_tools_list
```

Expected: PASS.

- [ ] **Step 2: Run py_compile on changed runtime files**

Run:

```powershell
python -m py_compile learning_agent\computer_use_mcp_v2\inferred_ant_mcp\build_tools.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\actions.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\clipboard.py learning_agent\computer_use_mcp_v2\inferred_ant_mcp\legacy_ports.py learning_agent\computer_use_mcp_v2\windows_runtime\mcp_session_adapter.py learning_agent\computer_use_mcp_v2\windows_runtime\sendinput_executor.py learning_agent\computer_use_mcp_v2\windows_runtime\sendinput_dispatcher.py learning_agent\computer_use_mcp_v2\windows_runtime\real_sendinput_guard.py learning_agent\computer_use_mcp_v2\windows_runtime\clipboard_io.py learning_agent\computer_use_mcp_v2\claudecode_bridge\mcpServer.py learning_agent\computer_use_mcp_v2\claudecode_bridge\hostAdapter.py learning_agent\tools\tool_scope.py
```

Expected: command exits 0.

- [ ] **Step 3: Run MCP server selftest**

Run:

```powershell
python learning_agent\mcp\servers\computer_use_server.py --selftest
```

Expected: output contains `COMPUTER_USE_MCP_V2_READY`, `tool_count` is `24`, and no shell surface is reported.

- [ ] **Step 4: Run CodeGraph sync**

Run:

```powershell
codegraph sync
codegraph status
```

Expected: sync completes and status does not report modified source files left out of the index.

- [ ] **Step 5: Perform real visible terminal acceptance**

Start:

```powershell
Start-Process -FilePath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat"
```

In the visible terminal, enter a realistic prompt:

```text
/computer use --full
请打开记事本，输入一行“Computer Use ClaudeCode parity test”，把这行文字复制到真实系统剪贴板，再读取剪贴板确认内容；随后打开画图，用 left_click_drag 画一条短线，使用 zoom 观察局部画布，最后停止 computer use。
```

Required observations:

- The agent sees `mcp__computer-use__zoom`, `mcp__computer-use__hold_key`, `mcp__computer-use__left_click_drag`, `mcp__computer-use__middle_click`, `mcp__computer-use__triple_click`, `mcp__computer-use__left_mouse_down`, `mcp__computer-use__left_mouse_up`.
- Notepad receives text through real desktop control.
- `write_clipboard` and `read_clipboard` operate on the Windows system clipboard.
- Paint receives a visible drag line from `left_click_drag`.
- `zoom` returns a local observation or screenshot artifact.
- Cleanup releases pressed keys and mouse buttons.

If this visible terminal acceptance cannot be performed from the current Codex environment, do not claim development complete. Report: `真实可见终端交互验收未完成，不能声明开发完成。`

- [ ] **Step 6: Update progress memory**

Append a short entry to `agent_memory/progress.md` with:

- completed commit hashes
- automated tests run
- MCP selftest result
- visible terminal acceptance result
- any remaining risks

- [ ] **Step 7: Final commit for acceptance updates**

Commit the progress-memory acceptance entry separately from runtime code:

```powershell
git add agent_memory/progress.md
git commit -m "docs: record computer use parity acceptance"
```

---

## Self-Review

- Spec coverage: the plan covers 7 new tools, true clipboard, dynamic tools/list, no-host failure, tests, and real visible terminal acceptance.
- Directory boundary: the plan keeps `inferred_ant_mcp/` as a reverse-engineered MCP contract layer and keeps Windows implementation in `windows_runtime/`.
- Type consistency: tool names are consistently `zoom`, `hold_key`, `left_click_drag`, `middle_click`, `triple_click`, `left_mouse_down`, `left_mouse_up`.
- Safety consistency: mutating actions require host/controller/SendInput path and no-host failure returns `desktop_action_performed=false`.
- Verification consistency: automated tests are listed before visible terminal acceptance, and automated tests are not treated as a substitute for visible terminal acceptance.
