# Computer Use ClaudeCode Protocol Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 把 OpenHarness agent 的 Computer Use 第 1 层“协议层”和第 2 层“桥接层”尽可能对齐 ClaudeCode 的可观察 computer use 行为，同时保留 Windows in-tree runtime 作为底层执行层。

**Architecture:** OpenHarness 不重写 Windows backend，而是在 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/` 增加 ClaudeCode-compatible facade：模型看到 ClaudeCode 风格工具、参数、权限、锁、display state 和结果 content blocks；facade 再把这些协议数据规范化给现有 Windows runtime 执行。`claudecode_bridge/` 负责模拟 ClaudeCode repo 内 `utils/computerUse` 的 wrapper/setup/mcpServer 行为，`windows_runtime/` 只做必要适配，不做推倒重写。

**Tech Stack:** Python 3.12, MCP stdio/JSON-RPC, OpenHarness agent runtime, Windows Win32/UIA/WGC/SendInput backend, unittest, CodeGraph, `start_oauth_agent.bat` visible-terminal acceptance.

---

## 1. 背景和边界

用户确认的目标是“除了外部 MCP 包和 macOS/Windows 系统不同之外，OpenHarness 的 computer use 尽可能完全对齐 ClaudeCode”。本计划只解决 ClaudeCode 可观察的协议层和桥接层差异，不把 macOS native executor 逐行搬到 Windows。

ClaudeCode repo 内可观察链路：

- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\setup.ts`：生成 `computer-use` MCP 配置和 allowed tools。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\mcpServer.ts`：创建 in-process MCP server，并给 `request_access` 动态注入已安装 app。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\wrapper.tsx`：绑定 session context、权限 UI、lock、Esc abort、cleanup、MCP result 到模型 block。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\toolRendering.tsx`：定义模型/终端可见的字段名和结果摘要。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\computerUseLock.ts`：定义 computer use 独占锁。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\cleanup.ts`：turn 结束释放锁、恢复隐藏 app、通知用户。
- `D:\ClaudeCode-main\ClaudeCode-main\components\permissions\ComputerUseApproval\ComputerUseApproval.tsx`：定义 app allowlist、grant flags、TCC/权限面板。

OpenHarness 当前链路：

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\inferred_ant_mcp\build_tools.py`：当前 24 个工具 schema。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\inferred_ant_mcp\runtime.py`：工具分发。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\inferred_ant_mcp\bind_session_context.py`：绑定 agent context。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\inferred_ant_mcp\legacy_ports.py`：把 v2 host 方法转到成熟 Windows session adapter。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\mcp_session_adapter.py`：把 MCP 原子工具映射到底层 Windows controller。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\claudecode_bridge\wrapper.py`：OpenHarness 侧 ClaudeCode wrapper 反推层。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tools\tool_scope.py`：控制 computer use operation/debug/source-development 模式下哪些工具暴露给模型。

## 2. 成功标准

- 模型看到的 OpenHarness tool name、tool schema、关键字段名和 ClaudeCode 可观察字段一致或兼容。
- OpenHarness 继续暴露 `computer-use` MCP server 和 `mcp__computer-use__*` allowed tools。
- 所有 ClaudeCode 风格输入字段都能被 OpenHarness 接受，例如 `coordinate`、`start_coordinate`、`region`、`direction`、`amount`、`duration`、`bundle_id`、`apps`。
- 旧 OpenHarness 字段仍可兼容，例如 `x`、`y`、`start_x`、`start_y`、`end_x`、`end_y`、`delta_y`、`app_name`、`applications`，避免破坏已有测试和历史 prompt。
- `request_access` 支持 app allowlist、grant flags、sentinel 风险类别和拒绝响应。
- `screenshot`、`zoom`、动作类工具返回更接近 MCP content blocks 的 text/image 数据，同时保留 artifact path 作为 Windows 调试证据。
- request/list 类工具只检查锁，不获取锁；动作/观察类工具按 ClaudeCode 语义获取 lock；turn 结束执行 cleanup。
- session context 具备 ClaudeCode 可观察的 display state：`selectedDisplayId`、`displayPinnedByModel`、`displayResolvedForApps`、`lastScreenshotDims`。
- `tools/list` 的 `request_access` 描述能动态加入 Windows 已安装应用提示。
- 自动化测试、probe 和真实可见终端验收全部通过后，才允许声明开发完成。

## 3. 明确不做的事情

- 不把 `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\executor.ts` 的 macOS Swift/Input 实现照抄到 Windows。
- 不推倒重写 `windows_runtime` 的截图、坐标、SendInput、UIA、WGC 能力。
- 不删除现有 `learning_agent/computer_use_mcp_v2/windows_runtime/`，它是 Windows 执行层。
- 不把旧 raw 工具重新暴露给模型，例如 `computer_status`、`computer_observe`、`computer_action`、`computer_use`。
- 不绕过项目规则 17。凡是修改 agent computer use 功能，最终必须完成 `start_oauth_agent.bat` 真实可见终端交互验收。

## 4. 文件结构规划

Create:

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/claudecode_protocol.py`：集中放 ClaudeCode-compatible 字段常量、tool 参数规范、grant flags、sentinel app 分类和返回 block helpers。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/protocol_normalizer.py`：把 ClaudeCode 风格参数转换成 Windows runtime 内部参数，同时保留旧字段兼容。
- `learning_agent/tests/test_computer_use_mcp_v2_claudecode_protocol_manifest.py`：锁定工具清单、字段清单和 forbidden legacy 工具。
- `learning_agent/tests/test_computer_use_mcp_v2_protocol_normalizer.py`：锁定 `coordinate`、`region`、`bundle_id`、`apps` 等字段归一化。
- `learning_agent/tests/test_computer_use_mcp_v2_permission_grants.py`：锁定 app allowlist、grant flags、sentinel 风险分类。
- `learning_agent/tests/test_computer_use_mcp_v2_result_blocks.py`：锁定 text/image content blocks 与 artifact debug 数据并存。
- `learning_agent/tests/test_computer_use_mcp_v2_lock_lifecycle.py`：锁定 defers-lock 和 action-acquire-lock 语义。
- `learning_agent/tests/test_computer_use_mcp_v2_display_state.py`：锁定 display state 的读写和 cleanup。
- `learning_agent/tests/test_computer_use_mcp_v2_dynamic_tools_list.py`：锁定 `request_access` 动态 app 描述。

Modify:

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`：把 public schema 调整为 ClaudeCode-compatible schema，并保留旧字段兼容说明。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`：扩展 `ComputerUseMcpV2Context` 的 permissions、lock、display、result 状态。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`：所有工具分发前先走 protocol normalizer，再按 defers-lock 语义处理 lock。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`：改造 `request_access` 和 `list_granted_applications`。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py`：让 `screenshot` 和 `zoom` 返回 ClaudeCode-compatible image/text blocks。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py`：动作工具统一接受 ClaudeCode coordinate 参数。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/applications.py`：`open_application` 支持 `bundle_id` 优先，`app_name` 兼容。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/batch.py`：`computer_batch` 使用 `actions` 作为 ClaudeCode 主字段，兼容 `steps`。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/result_blocks.py`：补齐 MCP text/image content block 结构。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`：绑定 lock、display、grant flags、cleanup callbacks。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/legacy_ports.py`：只在必要处接收 normalized arguments，不改 Windows backend 核心。
- `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：只补参数别名和返回 block 适配，不重写 controller。
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`：`tools/list` 动态注入 Windows app inventory。
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py`：补齐 ClaudeCode wrapper 行为：session context、content block 映射、cleanup hook。
- `learning_agent/tools/tool_scope.py`：确认只暴露 MCP 工具，不暴露旧 raw 工具。
- `docs/computer_use_mcp_v2_architecture.md`：同步最新协议级对齐设计。
- `agent_memory/progress.md`：记录每个阶段结果和验证证据。
- `agent_memory/bugs.md`：记录发现但暂不修的风险。

## 5. Task 1: 建立 ClaudeCode 协议清单和红测

**Files:**

- Create: `learning_agent/tests/test_computer_use_mcp_v2_claudecode_protocol_manifest.py`
- Create: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/claudecode_protocol.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`

- [x] **Step 1: 写协议清单红测**

测试必须验证 OpenHarness 暴露的工具名覆盖当前 24 个工具，并且 forbidden legacy raw names 不会出现在 schema 中。

```python
import unittest

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import (
    FORBIDDEN_LEGACY_RAW_TOOL_NAMES,
    computer_use_mcp_tools,
)


class ComputerUseMcpV2ClaudeCodeProtocolManifestTests(unittest.TestCase):
    def test_public_tool_names_match_claudecode_compatible_surface(self) -> None:
        tools = computer_use_mcp_tools()
        names = {tool["name"] for tool in tools}
        expected_names = {
            "request_access",
            "observe",
            "screenshot",
            "cursor_position",
            "mouse_move",
            "left_click",
            "double_click",
            "right_click",
            "middle_click",
            "triple_click",
            "left_mouse_down",
            "left_mouse_up",
            "type",
            "key",
            "hold_key",
            "scroll",
            "left_click_drag",
            "zoom",
            "wait",
            "read_clipboard",
            "write_clipboard",
            "open_application",
            "list_granted_applications",
            "computer_batch",
        }
        self.assertEqual(names, expected_names)

    def test_legacy_raw_tools_are_not_public(self) -> None:
        names = {tool["name"] for tool in computer_use_mcp_tools()}
        self.assertFalse(names.intersection(FORBIDDEN_LEGACY_RAW_TOOL_NAMES))
```

- [x] **Step 2: 运行红测确认当前协议差异**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest
```

Expected: 至少 schema 字段 parity 测试失败，因为 `coordinate`、`region`、`bundle_id`、`apps` 还没有作为主字段完整暴露。

- [x] **Step 3: 在 `claudecode_protocol.py` 定义协议常量**

实现时每一行新代码都要按 AGENTS.md 规则添加中文注释，注释前缀使用 `新增代码+ClaudeCodeProtocolParity`。

```python
from __future__ import annotations

CLAUDECODE_COORDINATE_FIELD = "coordinate"
CLAUDECODE_START_COORDINATE_FIELD = "start_coordinate"
CLAUDECODE_REGION_FIELD = "region"
CLAUDECODE_BUNDLE_ID_FIELD = "bundle_id"
CLAUDECODE_APPS_FIELD = "apps"
CLAUDECODE_ACTIONS_FIELD = "actions"

CLAUDECODE_GRANT_FLAGS = {
    "clipboardRead": False,
    "clipboardWrite": False,
    "systemKeyCombos": False,
}

CLAUDECODE_DEFERS_LOCK_TOOLS = {
    "request_access",
    "list_granted_applications",
}
```

- [x] **Step 4: 提交 Task 1**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/claudecode_protocol.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/tests/test_computer_use_mcp_v2_claudecode_protocol_manifest.py
git commit -m "test: lock computer use claudecode protocol manifest"
```

## 6. Task 2: 协议参数 normalizer

**Files:**

- Create: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/protocol_normalizer.py`
- Test: `learning_agent/tests/test_computer_use_mcp_v2_protocol_normalizer.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`

- [x] **Step 1: 写 coordinate/region/bundle/apps 红测**

```python
import unittest

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.protocol_normalizer import (
    normalize_computer_use_arguments,
)


class ComputerUseMcpV2ProtocolNormalizerTests(unittest.TestCase):
    def test_coordinate_array_becomes_xy_for_windows_runtime(self) -> None:
        normalized = normalize_computer_use_arguments("left_click", {"coordinate": [12, 34]})
        self.assertEqual(normalized["x"], 12)
        self.assertEqual(normalized["y"], 34)
        self.assertEqual(normalized["coordinate"], [12, 34])

    def test_drag_start_coordinate_and_coordinate_become_start_end_xy(self) -> None:
        normalized = normalize_computer_use_arguments(
            "left_click_drag",
            {"start_coordinate": [1, 2], "coordinate": [30, 40]},
        )
        self.assertEqual(normalized["start_x"], 1)
        self.assertEqual(normalized["start_y"], 2)
        self.assertEqual(normalized["end_x"], 30)
        self.assertEqual(normalized["end_y"], 40)

    def test_region_array_becomes_xy_width_height(self) -> None:
        normalized = normalize_computer_use_arguments("zoom", {"region": [10, 20, 300, 200]})
        self.assertEqual(normalized["x"], 10)
        self.assertEqual(normalized["y"], 20)
        self.assertEqual(normalized["width"], 300)
        self.assertEqual(normalized["height"], 200)

    def test_bundle_id_is_preserved_and_mirrored_to_app_name_for_legacy_runtime(self) -> None:
        normalized = normalize_computer_use_arguments("open_application", {"bundle_id": "notepad.exe"})
        self.assertEqual(normalized["bundle_id"], "notepad.exe")
        self.assertEqual(normalized["app_name"], "notepad.exe")
```

- [x] **Step 2: 实现 normalizer**

实现要求：

- `coordinate: [x, y]` 映射为 `x`、`y`。
- `start_coordinate: [x, y]` 映射为 `start_x`、`start_y`。
- `coordinate` 在 drag 工具里同时作为终点，映射为 `end_x`、`end_y`。
- `region: [x, y, width, height]` 映射为 `x`、`y`、`width`、`height`。
- `duration` 映射为 `duration_seconds`。
- `direction` 和 `amount` 映射为 Windows runtime 可执行的滚动 delta，同时保留原字段。
- `bundle_id` 映射为 `app_name`，同时保留 `bundle_id`。
- `apps` 映射为 `applications`，同时保留 `apps`。
- `actions` 映射为 `steps`，同时保留 `actions`。

- [x] **Step 3: 在 runtime 分发入口使用 normalizer**

`dispatch_computer_use_mcp_v2_tool` 必须在任何权限、观察、动作、batch 分支之前调用 normalizer。这样所有后续模块只需要处理 normalized arguments。

- [x] **Step 4: 运行 normalizer 测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer
```

Expected: PASS.

- [x] **Step 5: 提交 Task 2**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/protocol_normalizer.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/tests/test_computer_use_mcp_v2_protocol_normalizer.py
git commit -m "feat: normalize claudecode computer use protocol arguments"
```

## 7. Task 3: Public tool schema 改为 ClaudeCode-compatible 主字段

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`
- Test: `learning_agent/tests/test_computer_use_mcp_v2_claudecode_protocol_manifest.py`

- [x] **Step 1: 扩展 manifest 测试**

检查 `left_click`、`mouse_move`、`zoom`、`open_application`、`request_access`、`computer_batch` 的 schema 主字段。

Expected schema fields:

- `left_click`: `coordinate`
- `mouse_move`: `coordinate`
- `left_click_drag`: `start_coordinate`, `coordinate`
- `zoom`: `region`
- `scroll`: `direction`, `amount`, optional `coordinate`
- `hold_key`: `text`, `duration`
- `open_application`: `bundle_id`
- `request_access`: `apps`, `reason`
- `computer_batch`: `actions`

- [x] **Step 2: 修改 `build_tools.py`**

保留旧字段兼容但不要把旧字段作为主描述。schema 描述里必须明确 ClaudeCode 风格字段是推荐字段。

- [x] **Step 3: 确认 `tool_scope.py` 未暴露旧 raw 工具**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_tool_scope
```

Expected: PASS.

- [x] **Step 4: 提交 Task 3**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/tests/test_computer_use_mcp_v2_claudecode_protocol_manifest.py
git commit -m "feat: expose claudecode-compatible computer use schemas"
```

## 8. Task 4: 权限模型 parity

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_permission_grants.py`

- [x] **Step 1: 写 app allowlist 和 grant flags 测试**

测试输入：

```python
{
    "apps": [
        {"displayName": "Notepad", "bundleId": "notepad.exe"},
        {"displayName": "PowerShell", "bundleId": "powershell.exe"}
    ],
    "grantFlags": {
        "clipboardRead": True,
        "clipboardWrite": True,
        "systemKeyCombos": False
    },
    "reason": "需要在记事本中输入测试文本"
}
```

Expected:

- `request_access` 返回 `granted: True`。
- context 保存 `allowedApps`。
- context 保存 `grantFlags`。
- `PowerShell` 被标记为 shell sentinel 风险应用。
- `list_granted_applications` 返回 ClaudeCode-compatible 结构。

- [x] **Step 2: 实现 grant state**

`ComputerUseMcpV2Context` 增加字段：

- `allowed_apps`
- `grant_flags`
- `sentinel_warnings`
- `denied_apps`

默认 `grant_flags` 使用 `clipboardRead=False`、`clipboardWrite=False`、`systemKeyCombos=False`。

- [x] **Step 3: 实现 sentinel 分类**

Windows 风险类别：

- `shell`: `cmd.exe`, `powershell.exe`, `pwsh.exe`, `Windows Terminal`
- `filesystem`: `explorer.exe`, `notepad.exe` only when file path target is present
- `system_settings`: `control.exe`, `SystemSettings.exe`, `regedit.exe`

sentinel 只影响提示和审计，不直接替代用户授权。

- [x] **Step 4: 运行权限测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_permission_grants
```

Expected: PASS.

- [x] **Step 5: 提交 Task 4**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py learning_agent/tests/test_computer_use_mcp_v2_permission_grants.py
git commit -m "feat: align computer use permission grants with claudecode"
```

## 9. Task 5: 结果 content blocks parity

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/result_blocks.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_result_blocks.py`

- [x] **Step 1: 写结果 block 测试**

Expected result shape:

```python
{
    "ok": True,
    "tool": "screenshot",
    "content": [
        {"type": "text", "text": "Captured screenshot."},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "base64-data"
            }
        }
    ],
    "debug": {
        "artifact_path": "path-visible-for-windows-debugging"
    }
}
```

- [x] **Step 2: 实现 text/image block helpers**

`result_blocks.py` 增加：

- `text_content_block(text: str) -> dict[str, Any]`
- `image_content_block(data: str, media_type: str) -> dict[str, Any]`
- `success_result(..., content: list[dict[str, Any]] | None = None, debug: dict[str, Any] | None = None)`

- [x] **Step 3: 适配 screenshot 和 zoom**

`screenshot` 和 `zoom` 必须优先返回 content blocks。Windows artifact path 放进 `debug.artifact_path`，不要让模型只能通过文件路径理解截图。

- [x] **Step 4: 运行结果测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_result_blocks
```

Expected: PASS.

- [x] **Step 5: 提交 Task 5**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/result_blocks.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py learning_agent/tests/test_computer_use_mcp_v2_result_blocks.py
git commit -m "feat: return claudecode-style computer use content blocks"
```

## 10. Task 6: Lock lifecycle 和 cleanup parity

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_lock_lifecycle.py`

- [x] **Step 1: 写 defers-lock 测试**

Expected:

- `request_access` 不 acquire lock，只调用 `check_lock`。
- `list_granted_applications` 不 acquire lock，只调用 `check_lock`。
- `screenshot` acquire lock。
- `left_click` acquire lock。
- turn cleanup release lock。

- [x] **Step 2: 扩展 context callbacks**

`ComputerUseMcpV2Context` 增加：

- `check_computer_use_lock`
- `acquire_computer_use_lock`
- `release_computer_use_lock`
- `cleanup_after_turn`
- `is_lock_held_locally`

没有 agent callback 时使用安全 no-op，并在结果 debug 中记录 `lock_backend: "unavailable"`。

- [x] **Step 3: 在 runtime 中执行 lock 语义**

分发前判断工具名：

- `request_access` 和 `list_granted_applications` 只检查锁。
- 其他 computer use 工具先 acquire lock。
- acquire 失败时返回 `computer_use_lock_unavailable`，不要继续执行鼠标键盘。

- [x] **Step 4: 运行 lock 测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle
```

Expected: PASS.

- [x] **Step 5: 提交 Task 6**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py learning_agent/tests/test_computer_use_mcp_v2_lock_lifecycle.py
git commit -m "feat: align computer use lock lifecycle with claudecode"
```

## 11. Task 7: Display state parity

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py`
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/coordinates.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_display_state.py`

- [x] **Step 1: 写 display state 测试**

Expected fields:

- `selectedDisplayId`
- `displayPinnedByModel`
- `displayResolvedForApps`
- `lastScreenshotDims`

Expected behavior:

- screenshot 后写入 `lastScreenshotDims`。
- display resolve 后写入 `displayResolvedForApps`。
- cleanup 不清空 `lastScreenshotDims`，但清理临时 pinned state。

- [x] **Step 2: 实现 context 字段和 callbacks**

OpenHarness 字段使用 Python snake_case 保存，返回给模型时使用 ClaudeCode camelCase。

- [x] **Step 3: 连接 Windows 坐标系统**

`coordinates.py` 只暴露必要转换，不改变现有 DPI 和截图映射核心逻辑。

- [x] **Step 4: 运行 display 测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_display_state
```

Expected: PASS.

- [x] **Step 5: 提交 Task 7**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py learning_agent/computer_use_mcp_v2/windows_runtime/coordinates.py learning_agent/tests/test_computer_use_mcp_v2_display_state.py
git commit -m "feat: add claudecode-style computer use display state"
```

## 12. Task 8: Dynamic tools/list app inventory

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_dynamic_tools_list.py`

- [x] **Step 1: 写 tools/list 测试**

Expected:

- `tools/list` 返回 `request_access`。
- `request_access.description` 包含 Windows app inventory 返回的安全应用名。
- app inventory 超时时，`tools/list` 仍返回静态 schema，不崩溃。

- [x] **Step 2: 实现动态 description 注入**

`mcpServer.py` 在 `tools/list` 时调用 Windows app inventory，最多等待 1 秒。失败时记录 debug trace，返回静态描述。

- [x] **Step 3: 运行 dynamic tools/list 测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list
```

Expected: PASS.

- [x] **Step 4: 提交 Task 8**

```powershell
git add learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/tests/test_computer_use_mcp_v2_dynamic_tools_list.py
git commit -m "feat: inject windows app inventory into computer use tools list"
```

## 13. Task 9: Bridge wrapper parity

**Files:**

- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py`
- Modify: `learning_agent/computer_use_mcp_v2/claudecode_bridge/toolRendering.py`
- Modify: `learning_agent/mcp/agent_adapter.py`
- Test: existing MCP server and adapter tests

- [x] **Step 1: 复核 wrapper 行为**

Wrapper 必须负责：

- 绑定同一个 session context。
- 每次工具调用写入 current tool use context。
- 调用 runtime。
- 把 MCP content blocks 映射成 agent 模型可读 block。
- 在 abort 或 turn end 时走 cleanup hook。

- [x] **Step 2: 补 tool rendering 字段名**

`toolRendering.py` 使用 ClaudeCode 字段名展示：

- coordinate
- start_coordinate
- region
- direction
- amount
- text
- duration
- bundle_id
- apps
- actions

- [x] **Step 3: 运行 adapter 测试**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_session_adapter
```

Expected: PASS.

- [x] **Step 4: 提交 Task 9**

```powershell
git add learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py learning_agent/computer_use_mcp_v2/claudecode_bridge/toolRendering.py learning_agent/mcp/agent_adapter.py
git commit -m "feat: align computer use bridge wrapper with claudecode"
```

## 14. Task 10: 总验证和真实终端验收

**Files:**

- Modify: `docs/computer_use_mcp_v2_architecture.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md` only if new risks are found

- [x] **Step 1: 运行 py_compile**

```powershell
python -m py_compile learning_agent/computer_use_mcp_v2/inferred_ant_mcp/claudecode_protocol.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/protocol_normalizer.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/observation.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/actions.py learning_agent/computer_use_mcp_v2/claudecode_bridge/wrapper.py learning_agent/computer_use_mcp_v2/claudecode_bridge/mcpServer.py
```

Expected: command exits 0.

- [x] **Step 2: 运行 computer use 单测矩阵**

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_tool_scope
```

Expected: all tests PASS.

- [x] **Step 3: 运行独立 MCP probe**

```powershell
python learning_agent\acceptance_controller\probes\computer_use_independent_mcp_server_probe.py
```

Expected:

```text
COMPUTER_USE_MCP_V2_READY
```

- [x] **Step 4: 执行真实可见终端验收**

必须启动：

```powershell
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

必须在用户本地可见真实终端窗口中的 agent 交互提示符输入真实用户风格 prompt：

```text
请使用 computer use 查询当前已授权的应用列表，然后截图观察当前桌面，不要点击或输入任何内容。
```

Expected:

- agent 调用 `mcp__computer-use__list_granted_applications`。
- agent 调用 `mcp__computer-use__screenshot` 或 `mcp__computer-use__observe`。
- 输出中没有 legacy raw tool。
- 输出中能看到 ClaudeCode-compatible 字段或结果摘要。
- 若截图成功，结果包含模型可见 image content block 或对应 image message。

- [x] **Step 5: 更新文档和记忆**

`docs/computer_use_mcp_v2_architecture.md` 记录最终协议链路。`agent_memory/progress.md` 记录通过的测试命令和真实终端 run 路径。若有无法本轮解决的风险，写入 `agent_memory/bugs.md`。

- [x] **Step 6: 提交 Task 10**

```powershell
git add docs/computer_use_mcp_v2_architecture.md agent_memory/progress.md agent_memory/bugs.md
git commit -m "docs: record claudecode protocol parity acceptance"
```

## 15. CodeGraph 使用要求

每个 task 开始前先运行 CodeGraph，确认当前知识图谱里的文件关系没有漂移。

OpenHarness 查询命令：

```powershell
codegraph status .
codegraph explore "computer use mcp v2 claudecode protocol runtime wrapper schema permission lock display result blocks"
```

ClaudeCode 对照查询命令：

```powershell
codegraph status .
codegraph explore "utils/computerUse setup wrapper mcpServer toolRendering permissions lock cleanup display coordinate region bundle_id apps"
```

如果 CodeGraph MCP transport 关闭，使用 CLI 版本；这仍然读取 `.codegraph/` 索引。

## 16. 风险和停止条件

- 如果发现 ClaudeCode repo 里缺少 `@ant/computer-use-mcp` 外部包源码，不要声称包内部已逐行对齐，只能声称“repo 可观察协议对齐”。
- 如果 schema parity 导致现有 Windows runtime 测试失败，优先修 normalizer，不要改底层 SendInput 或截图 controller。
- 如果 lock lifecycle 影响真实鼠标键盘安全，停止实现并把风险写入 `agent_memory/bugs.md`。
- 如果当前 Codex 环境无法打开、观察或向用户本地可见终端窗口输入内容，最终必须明确说明：“真实可见终端交互验收未完成，不能声明开发完成。”
- 只有“代码修改完成 + 自动化测试通过 + start_oauth_agent.bat 可见终端交互测试通过”同时满足，才可以声明开发完成。

## 17. 推荐执行方式

优先使用 Subagent-Driven：

- 每个 Task 派一个新 subagent。
- 主 agent 每个 Task 后做代码审查和测试复核。
- 每个 Task 单独 commit，避免长任务上下文压缩后无法回滚。

如果用户希望当前会话直接执行，使用 Inline Execution：

- 每完成两个 Task 停下来汇报一次。
- 不跨过失败测试。
- 不在真实终端验收前声明完成。

## 18. 自检结果

- Spec coverage：本计划覆盖协议 schema、normalizer、权限、结果 block、lock、display、dynamic tools/list、wrapper、测试和真实终端验收。
- 占位表达扫描：本文没有保留空洞任务，每个阶段都有目标文件、测试命令、预期结果和停止条件。
- Type consistency：计划内统一使用 ClaudeCode-facing camelCase 字段和 OpenHarness-internal snake_case 字段，normalizer 是两者唯一转换边界。
