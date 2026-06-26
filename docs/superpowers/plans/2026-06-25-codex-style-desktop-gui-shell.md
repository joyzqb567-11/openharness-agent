# Codex-Style Desktop Shell V1: Bridge-First Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a V1 micro-Codex desktop vertical slice for OpenHarness: a visible desktop window can send one real prompt to the existing `learning_agent` backend, render the run lifecycle, show tool events, support cancel/retry/resume, surface backend-enforced permissions, and pass a real GUI prompt matrix before any later UI expansion.

**Architecture:** Keep `apps/desktop` as the desktop shell and `learning_agent` as the agent backend. The GUI talks to a local GUI bridge in `learning_agent/app/gui_bridge.py` over loopback HTTP plus event polling first, then upgrades to streaming only after the event protocol and lifecycle state machine are stable. The renderer is responsible for user experience only: thread display, composer, tool-call cards, permission intent UI, status panels, and project/session navigation.

**Tech Stack:** Electron + React + TypeScript + Vite for the desktop shell; Python standard-library HTTP server for the first GUI bridge; existing OpenHarness runtime stores for tasks, events, browser state, sessions, and harness runs.

---

## Scope And Non-Goals

This is a V1 vertical-slice implementation blueprint. It intentionally builds the smallest real Codex-like loop first so the project does not drift into a static desktop skin.

In scope:

- Desktop shell under `apps/desktop`.
- Local GUI bridge under `learning_agent/app/gui_bridge.py`.
- Chat view with tool-call visibility.
- Project and session sidebar.
- Status and task panels.
- Browser provider panel.
- Computer Use permission and safety surfaces.
- Event-driven UI updates.
- Packaging scripts and smoke tests.
- A real agent run lifecycle: start, running, needs permission, cancelling, completed, failed, cancelled, retry, and resume.
- A local bridge security model: loopback only, random token, strict origin policy, no raw memory reads, and structured errors.
- A true GUI prompt matrix that stresses the hard 5% cases, not only the happy path.

Out of scope:

- Replacing `learning_agent/core`.
- Rewriting MCP tool execution.
- Rewriting browser automation providers.
- Rewriting Computer Use runtime.
- Copying Codex private implementation details.
- Supporting cloud-hosted multi-user deployment in the first desktop shell.
- Building all Codex sidebar features before the first real prompt loop works.
- Claiming a mature shell before cancel/retry/resume, permission routing, and prompt-matrix acceptance pass.

## Maturity Ladder

This plan uses a maturity ladder so later workers do not confuse a good demo with a deployable shell.

- **V0 scaffold:** window opens and static layout renders.
- **V1 vertical slice:** one real prompt completes through backend bridge, events render, cancel/retry/resume work, permissions go through backend, and prompt matrix passes.
- **V2 working shell:** sessions, browser panel, task panel, search, plugins placeholder, automation placeholder, settings, and packaging are usable.
- **V3 mature shell:** streaming, richer traces, update flow, crash recovery, accessibility pass, signed packaging, and larger reliability matrix.

This document targets **V1 first**, then leaves hooks for V2.

## Success Criteria

- User can launch a desktop window from the repo.
- Left sidebar shows projects, sessions, search entry, plugin placeholder, automation placeholder, and settings entry.
- Main chat panel supports message input, user messages, assistant messages, final answers, and run status.
- GUI can send a prompt to the existing agent backend and receive a response.
- GUI can poll status events and render tool-call progress cards.
- GUI can cancel a running turn and show a `cancelled` terminal state.
- GUI can retry a failed or completed turn without duplicating unrelated events.
- GUI can resume the last session after the desktop window restarts.
- GUI can show current browser provider status from existing backend state.
- GUI can show long-task and background task status.
- GUI can surface permission requests as first-class UI state, but the backend remains the enforcement point.
- GUI bridge accepts only loopback requests that pass the startup token and allowed-origin checks.
- GUI never directly reads secrets, cookies, tokens, localStorage, sessionStorage, or private page text outside existing backend redaction rules.
- GUI has automated tests for bridge contracts and renderer state reducers.
- GUI has at least 20 real prompt-matrix scenarios covering happy path, tool progress, browser provider status, permission approval, permission refusal, cancel, retry, resume, backend busy, failed tool, long task, Chinese input, window restart, and safety refusal.
- Final GUI shell acceptance is the visible desktop GUI smoke run plus the visible GUI prompt matrix.
- The project-required `start_oauth_agent.bat` visible terminal gate is a conditional backend-agent gate, not the GUI visual acceptance gate.

## Acceptance Layers

Use these layers to avoid mixing GUI shell validation with backend agent validation.

### Layer A: Visible Desktop GUI Acceptance

This is the primary acceptance gate for the Codex-style desktop shell.

Required evidence:

- A real Electron desktop window opens on the user's machine.
- The window is not blank.
- Sidebar, thread panel, composer, tool/status area, browser panel, and permission surface are visible where applicable.
- Text does not overlap or clip in the supported window sizes.
- Composer supports Enter to send and Shift+Enter for newline.
- A real prompt can be entered from the GUI.
- Run state is visible: queued, running, needs permission, cancelling, completed, failed, or cancelled.
- Tool events render as visible cards or timeline rows.
- Cancel, retry, and resume actions are visible only when their backend endpoints are available.
- Permission approval and denial are visible GUI flows, while enforcement remains in the backend.
- The 20-scenario GUI prompt matrix in `apps/desktop/tests/gui-prompt-matrix.md` is checked against the visible desktop window.

Layer A does not use `learning_agent/start_oauth_agent.bat`. It validates the desktop GUI shell.

### Layer B: Automated Contract And Build Gate

This gate proves the bridge and renderer are mechanically consistent.

Required evidence:

- Python GUI bridge contract tests pass.
- Python GUI bridge security tests pass.
- Python lifecycle and permission tests pass.
- Frontend TypeScript lint passes.
- Frontend unit tests pass.
- Electron main/preload and renderer build outputs exist.

Layer B does not replace Layer A because automated tests cannot prove the visible desktop interface is usable.

### Layer C: Conditional Backend Agent Terminal Gate

This gate is only required when the implementation changes backend agent behavior.

Trigger Layer C when a task changes:

- Agent runtime execution.
- MCP routing or MCP tool execution.
- Model call behavior.
- Browser automation behavior.
- Computer Use behavior.
- Backend permission enforcement.
- `learning_agent/core`, `learning_agent/browser`, `learning_agent/runtime`, or equivalent runtime paths.

Layer C command:

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

Layer C requires a real prompt typed into the visible terminal and observed output. It is not a substitute for Layer A.

## Existing Backend Facts From CodeGraph

- `learning_agent/app/http_bridge.py` already exposes local HTTP endpoints for `/health`, `/status`, `/events`, `/browser/runs`, `/browser/events`, `/browser/providers`, `/sessions`, `/resume`, and `/run`.
- `learning_agent/runtime/status_events.py` provides `StatusEventStore` as the shared event stream.
- `learning_agent/runtime/status_snapshot.py` builds the unified status snapshot consumed by CLI, SDK, and HTTP bridge.
- `learning_agent/browser_automation_mcp_server.py` exposes browser MCP tools and browser provider status.
- `learning_agent/app/interactive.py` already renders terminal status, Chrome status, and Computer Use status.
- `apps/desktop` already exists as a GUI shell skeleton.

## Product Shape

The desktop shell should feel like Codex, but it should be OpenHarness-native.

Primary panes:

- Left rail: quick chat, search, plugins, automations, projects, settings.
- Project sidebar: current project, recent conversations, pinned sessions, background tasks.
- Main thread: messages, tool cards, status timeline, attachments, file links.
- Bottom composer: prompt input, permission mode indicator, model selector placeholder, send button.
- Right inspector: run details, status snapshot, browser provider, task list, selected tool-call evidence.

Initial visual direction:

- Light theme first.
- Quiet utility design.
- 8px or smaller radius.
- Dense but readable layout.
- No marketing hero page.
- No decorative gradient orbs.
- Use icons for actions and text for primary commands.

## File Structure

Create or modify these files during implementation:

```text
apps/desktop/package.json
apps/desktop/vite.config.ts
apps/desktop/tsconfig.json
apps/desktop/tsconfig.node.json
apps/desktop/index.html
apps/desktop/src/main/bridgeAuth.ts
apps/desktop/src/main/index.ts
apps/desktop/src/main/backendProcess.ts
apps/desktop/src/main/ipc.ts
apps/desktop/src/preload/index.ts
apps/desktop/src/renderer/App.tsx
apps/desktop/src/renderer/main.tsx
apps/desktop/src/components/AppShell.tsx
apps/desktop/src/components/Sidebar.tsx
apps/desktop/src/components/ThreadView.tsx
apps/desktop/src/components/Composer.tsx
apps/desktop/src/components/ToolCallCard.tsx
apps/desktop/src/components/StatusInspector.tsx
apps/desktop/src/api/guiClient.ts
apps/desktop/src/state/threadStore.ts
apps/desktop/src/state/statusStore.ts
apps/desktop/src/styles/theme.css
apps/desktop/src/styles/layout.css
apps/desktop/tests/guiClient.test.ts
apps/desktop/tests/statusStore.test.ts
apps/desktop/tests/threadStore.test.ts
learning_agent/app/gui_bridge.py
learning_agent/tests/test_gui_bridge_contract.py
learning_agent/tests/test_gui_bridge_events_contract.py
learning_agent/tests/test_gui_bridge_lifecycle_contract.py
learning_agent/tests/test_gui_bridge_permission_contract.py
learning_agent/tests/test_gui_bridge_security_contract.py
learning_agent/app/cli.py
docs/desktop_gui_shell_architecture.md
apps/desktop/tests/gui-prompt-matrix.md
learning_agent/test/desktop_gui_shell_YYYYMMDD/
```

## Data Contracts

The GUI bridge should use these stable JSON shapes.

### Bootstrap Response

```json
{
  "ok": true,
  "workspace": "H:\\codexworkplace\\sofeware\\OpenHarness-main",
  "app": {
    "name": "OpenHarness Desktop",
    "schema_version": 1
  },
  "snapshot": {},
  "feature_flags": {
    "chat_run": true,
    "event_polling": true,
    "browser_panel": true,
    "computer_use_panel": true,
    "streaming": false
  }
}
```

### Bridge Security

```json
{
  "host": "127.0.0.1",
  "token_header": "X-OpenHarness-Desktop-Token",
  "allowed_dev_origin": "http://127.0.0.1:5177",
  "allowed_prod_origin": "file://",
  "allowed_file_origin_header": "null",
  "health_endpoint_requires_token": false,
  "all_other_endpoints_require_token": true
}
```

The bridge token is generated when the bridge starts. The token is passed to the Electron renderer through the preload boundary or injected API client configuration. It is never written into source files.

### Send Message Request

```json
{
  "conversation_id": "default",
  "prompt": "请帮我分析当前项目",
  "max_turns": 12,
  "client_request_id": "client_20260625_001"
}
```

### Send Message Response

```json
{
  "ok": true,
  "conversation_id": "default",
  "turn_id": "turn_20260625_001",
  "run_id": "run_20260625_001",
  "status": "queued",
  "answer": "",
  "events_after_sequence": 123
}
```

### Turn Lifecycle

```json
{
  "states": [
    "queued",
    "running",
    "needs_permission",
    "cancelling",
    "completed",
    "failed",
    "cancelled"
  ],
  "terminal_states": ["completed", "failed", "cancelled"],
  "commands": [
    "POST /v1/gui/messages",
    "POST /v1/gui/turns/{turn_id}/cancel",
    "POST /v1/gui/turns/{turn_id}/retry",
    "POST /v1/gui/sessions/{session_id}/resume"
  ]
}
```

Required lifecycle events:

```text
gui_turn_queued
gui_turn_started
gui_turn_needs_permission
gui_turn_cancel_requested
gui_turn_cancelled
gui_turn_retried
gui_turn_resumed
gui_turn_completed
gui_turn_failed
```

### Permission Decision Request

```json
{
  "request_id": "permission_20260625_001",
  "turn_id": "turn_20260625_001",
  "decision": "approve",
  "reason": "用户在 GUI 中点击允许"
}
```

Allowed decisions are `approve` and `deny`. The GUI sends intent only. Backend permission machinery records and enforces the decision.

### Event Poll Response

```json
{
  "ok": true,
  "events": [
    {
      "schema_version": 2,
      "sequence": 124,
      "event_type": "tool_call_started",
      "session_id": "session_default",
      "run_id": "run_001",
      "turn_id": "turn_20260625_001",
      "payload": {
        "tool_name": "browser_provider_status",
        "summary": "checking provider status"
      }
    }
  ],
  "since_sequence": 123,
  "limit": 50
}
```

## Safety And Drift Guards

- Do not put GUI business logic inside `learning_agent/core`.
- Do not make the renderer call Python files directly.
- Do not let the renderer read `learning_agent/memory` raw files.
- Do not expose raw cookies, tokens, storage, password text, screenshot OCR text, or private page text.
- Do not bypass `StatusEventStore`, `build_status_snapshot`, `TaskRegistry`, or browser runtime stores.
- Do not hide tool failures behind generic UI messages.
- Do not ship localhost bridge endpoints without token and origin checks.
- Do not let the front end enforce permission decisions by itself.
- Do not create UI-only cancel/retry/resume buttons unless the backend endpoint and events exist first.
- Do not write TypeScript, TSX, CSS, Python, or PowerShell implementation code without the project-required Chinese line comments during actual implementation.
- Do not mark GUI work complete until automated tests and visible desktop smoke pass.
- Do not mark backend agent behavior changes complete until `start_oauth_agent.bat` visible terminal acceptance passes when Layer C is triggered.

## Task 1: Backend GUI Bridge Contract Tests

**Files:**

- Create: `learning_agent/tests/test_gui_bridge_contract.py`
- Create: `learning_agent/tests/test_gui_bridge_events_contract.py`
- Create: `learning_agent/app/gui_bridge.py`

- [ ] **Step 1: Write failing bridge bootstrap test**

Create `learning_agent/tests/test_gui_bridge_contract.py`:

```python
from pathlib import Path  # 新增代码+DesktopGUIBridgeTest: 使用 Path 构造临时工作区；如果没有这行代码，测试无法用统一路径对象。


def test_gui_bootstrap_payload_contains_snapshot_and_flags(tmp_path: Path) -> None:  # 新增代码+DesktopGUIBridgeTest: 验证 GUI 启动所需字段；如果没有这段测试，桌面壳可能拿不到状态和功能开关。
    from learning_agent.app.gui_bridge import build_gui_bootstrap_payload  # 新增代码+DesktopGUIBridgeTest: 导入计划新增的 bridge helper；如果没有这行代码，测试无法锁定后端合同。

    payload = build_gui_bootstrap_payload(tmp_path)  # 新增代码+DesktopGUIBridgeTest: 生成 GUI bootstrap 响应；如果没有这行代码，无法验证结构。

    assert payload["ok"] is True  # 新增代码+DesktopGUIBridgeTest: 确认 bridge 返回成功；如果没有这行断言，失败 payload 可能误过。
    assert payload["workspace"] == str(tmp_path)  # 新增代码+DesktopGUIBridgeTest: 确认工作区路径可展示；如果没有这行断言，GUI 可能显示错误项目。
    assert payload["app"]["schema_version"] == 1  # 新增代码+DesktopGUIBridgeTest: 锁定响应协议版本；如果没有这行断言，前端无法安全兼容。
    assert "snapshot" in payload  # 新增代码+DesktopGUIBridgeTest: 确认包含统一状态快照；如果没有这行断言，GUI 需要旁路读状态。
    assert payload["feature_flags"]["event_polling"] is True  # 新增代码+DesktopGUIBridgeTest: 确认事件轮询可用；如果没有这行断言，前端无法知道刷新方式。
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract
```

Expected: fail with `ModuleNotFoundError` or missing `build_gui_bootstrap_payload`.

- [ ] **Step 3: Write minimal bridge helper**

Create `learning_agent/app/gui_bridge.py`:

```python
"""Desktop GUI bridge for the OpenHarness local desktop shell."""  # 新增代码+DesktopGUIBridge: 说明本模块只服务桌面 GUI；如果没有这行代码，维护者容易把它和通用 HTTP bridge 混淆。
from __future__ import annotations  # 新增代码+DesktopGUIBridge: 延迟解析类型注解；如果没有这行代码，后续类型引用更容易受导入顺序影响。

from pathlib import Path  # 新增代码+DesktopGUIBridge: 使用 Path 规范化工作区；如果没有这行代码，字符串路径处理容易分裂。
from typing import Any  # 新增代码+DesktopGUIBridge: 描述 JSON payload 的通用值；如果没有这行代码，接口类型边界不清楚。

from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIBridge: 复用统一状态事实源；如果没有这行代码，GUI 会和 CLI/SDK 状态分裂。


GUI_SCHEMA_VERSION = 1  # 新增代码+DesktopGUIBridge: 固定 GUI bridge 协议版本；如果没有这行代码，前端无法判断响应兼容性。


def build_gui_bootstrap_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIBridge: 函数段开始，生成 GUI 启动首屏数据；如果没有这段函数，桌面壳需要调用多个后端端点拼状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 规范化工作区路径；如果没有这行代码，相对路径会导致前端项目身份不稳定。
    snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopGUIBridge: 读取统一状态快照；如果没有这行代码，GUI 没有 run/task/session/browser 数据。
    return {  # 新增代码+DesktopGUIBridge: 返回稳定 JSON 对象；如果没有这行代码，前端无法渲染启动页。
        "ok": True,  # 新增代码+DesktopGUIBridge: 标记请求成功；如果没有这行代码，前端要靠异常猜测状态。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIBridge: 返回当前项目路径；如果没有这行代码，侧栏无法显示项目身份。
        "app": {"name": "OpenHarness Desktop", "schema_version": GUI_SCHEMA_VERSION},  # 新增代码+DesktopGUIBridge: 返回应用名和协议版本；如果没有这行代码，前端无法做兼容判断。
        "snapshot": snapshot,  # 新增代码+DesktopGUIBridge: 返回统一状态快照；如果没有这行代码，首屏看不到任务和会话。
        "feature_flags": {  # 新增代码+DesktopGUIBridge: 返回能力开关；如果没有这行代码，前端无法按后端能力显示 UI。
            "chat_run": True,  # 新增代码+DesktopGUIBridge: 声明可发起聊天运行；如果没有这行代码，输入框无法判断是否可用。
            "event_polling": True,  # 新增代码+DesktopGUIBridge: 声明当前使用事件轮询；如果没有这行代码，前端无法启动 watcher。
            "browser_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示浏览器状态；如果没有这行代码，浏览器面板会误隐藏。
            "computer_use_panel": True,  # 新增代码+DesktopGUIBridge: 声明可显示 Computer Use 状态；如果没有这行代码，权限面板会误隐藏。
            "streaming": False,  # 新增代码+DesktopGUIBridge: 第一阶段不声明真实流式输出；如果没有这行代码，前端可能误等 SSE。
        },  # 新增代码+DesktopGUIBridge: feature_flags 对象结束；如果没有这行代码，Python 语法不完整。
    }  # 新增代码+DesktopGUIBridge: bootstrap payload 结束；如果没有这行代码，函数没有返回值。
# 新增代码+DesktopGUIBridge: 函数段结束，build_gui_bootstrap_payload 到此结束；如果没有这个边界说明，用户不容易看出它只负责首屏数据。
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_bridge_contract.py
git commit -m "feat: add desktop gui bridge bootstrap contract"
```

## Task 2: GUI Bridge HTTP Server And CLI Entry

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `learning_agent/app/cli.py`
- Test: `learning_agent/tests/test_gui_bridge_contract.py`
- Create: `learning_agent/tests/test_gui_bridge_security_contract.py`

- [ ] **Step 1: Add failing HTTP route test**

Append to `learning_agent/tests/test_gui_bridge_contract.py`:

```python
import json  # 新增代码+DesktopGUIBridgeTest: 解析 HTTP 响应 JSON；如果没有这行代码，测试只能比较原始字符串。
import urllib.request  # 新增代码+DesktopGUIBridgeTest: 使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。


def test_gui_bridge_http_bootstrap_route(tmp_path: Path) -> None:  # 新增代码+DesktopGUIBridgeTest: 验证 GUI bridge HTTP 端点；如果没有这段测试，Electron 无法可靠启动首屏。
    from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIBridgeTest: 导入计划新增的 HTTP server 构造器；如果没有这行代码，测试无法启动 bridge。

    server = create_gui_bridge_server(workspace=tmp_path, host="127.0.0.1", port=0, token="")  # 新增代码+DesktopGUIBridgeTest: 使用随机端口启动 server 对象；如果没有这行代码，测试可能端口冲突。
    try:  # 新增代码+DesktopGUIBridgeTest: 保护 server 清理；如果没有这行代码，测试失败会泄漏监听端口。
        import threading  # 新增代码+DesktopGUIBridgeTest: 后台运行标准库 HTTP server；如果没有这行代码，请求会阻塞。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIBridgeTest: 创建 daemon 线程；如果没有这行代码，测试无法同时请求 server。
        thread.start()  # 新增代码+DesktopGUIBridgeTest: 启动 HTTP server；如果没有这行代码，urllib 会连接失败。
        host, port = server.server_address  # 新增代码+DesktopGUIBridgeTest: 读取真实随机端口；如果没有这行代码，请求不知道地址。
        with urllib.request.urlopen(f"http://{host}:{port}/v1/gui/bootstrap", timeout=5) as response:  # 新增代码+DesktopGUIBridgeTest: 请求 bootstrap 端点；如果没有这行代码，无法验证 HTTP 路由。
            payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIBridgeTest: 解析响应 JSON；如果没有这行代码，无法断言字段。
        assert payload["ok"] is True  # 新增代码+DesktopGUIBridgeTest: 确认 HTTP 返回成功；如果没有这行断言，坏响应可能误过。
        assert payload["app"]["name"] == "OpenHarness Desktop"  # 新增代码+DesktopGUIBridgeTest: 确认返回 GUI 应用名；如果没有这行断言，前端首屏品牌可能丢失。
    finally:  # 新增代码+DesktopGUIBridgeTest: 无论断言是否失败都关闭 server；如果没有这行代码，测试环境会残留端口。
        server.shutdown()  # 新增代码+DesktopGUIBridgeTest: 请求 server 退出；如果没有这行代码，后台线程可能继续运行。
        server.server_close()  # 新增代码+DesktopGUIBridgeTest: 释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract
```

Expected: fail with missing `create_gui_bridge_server`.

- [ ] **Step 3: Add HTTP server implementation**

Append to `learning_agent/app/gui_bridge.py`:

```python
import http.server  # 新增代码+DesktopGUIBridge: 使用标准库 HTTP server；如果没有这行代码，GUI bridge 需要引入新依赖。
import json  # 新增代码+DesktopGUIBridge: 序列化 HTTP JSON 响应；如果没有这行代码，前端无法解析结构化数据。
import urllib.parse  # 新增代码+DesktopGUIBridge: 解析 URL path 和 query；如果没有这行代码，事件轮询参数无法读取。


class DesktopGuiBridgeServer(http.server.ThreadingHTTPServer):  # 新增代码+DesktopGUIBridge: 类段开始，保存 GUI bridge 工作区和 token；如果没有这个类，handler 无法访问项目状态。
    def __init__(self, server_address: tuple[str, int], workspace: str | Path, token: str = "") -> None:  # 新增代码+DesktopGUIBridge: 初始化 server；如果没有这段函数，外部无法注入工作区。
        super().__init__(server_address, DesktopGuiBridgeHandler)  # 新增代码+DesktopGUIBridge: 绑定 handler；如果没有这行代码，server 不会处理 GUI 路由。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 保存规范化工作区；如果没有这行代码，所有端点都不知道项目位置。
        self.token = str(token or "")  # 新增代码+DesktopGUIBridge: 保存可选 token；如果没有这行代码，本地请求无法启用保护。
    # 新增代码+DesktopGUIBridge: 函数段结束，DesktopGuiBridgeServer.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 server 只保存共享状态。


class DesktopGuiBridgeHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+DesktopGUIBridge: 类段开始，处理 GUI bridge HTTP 请求；如果没有这个类，Electron 前端没有后端入口。
    server: DesktopGuiBridgeServer  # 新增代码+DesktopGUIBridge: 标注 server 类型；如果没有这行代码，编辑器看不懂 workspace/token 字段。

    def log_message(self, format: str, *args: Any) -> None:  # 新增代码+DesktopGUIBridge: 关闭默认访问日志；如果没有这段函数，控制台会被轮询请求刷屏。
        return  # 新增代码+DesktopGUIBridge: 明确不输出标准库日志；如果没有这行代码，函数没有行为。
    # 新增代码+DesktopGUIBridge: 函数段结束，log_message 到此结束；如果没有这个边界说明，用户不容易看出它只负责降噪。

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:  # 新增代码+DesktopGUIBridge: 统一返回 JSON；如果没有这段函数，每个端点会重复 header 逻辑。
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+DesktopGUIBridge: 编码 UTF-8 JSON；如果没有这行代码，中文状态会乱码。
        self.send_response(status)  # 新增代码+DesktopGUIBridge: 写 HTTP 状态码；如果没有这行代码，前端无法判断成功失败。
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 新增代码+DesktopGUIBridge: 声明 JSON 类型；如果没有这行代码，前端可能按文本处理。
        self.send_header("Content-Length", str(len(raw_body)))  # 新增代码+DesktopGUIBridge: 声明响应长度；如果没有这行代码，客户端可能等待连接关闭。
        self.send_header("Cache-Control", "no-store")  # 新增代码+DesktopGUIBridge: 禁止缓存状态响应；如果没有这行代码，GUI 可能显示旧状态。
        self.end_headers()  # 新增代码+DesktopGUIBridge: 结束响应头；如果没有这行代码，响应体不会正确发送。
        self.wfile.write(raw_body)  # 新增代码+DesktopGUIBridge: 写出响应体；如果没有这行代码，前端收不到数据。
    # 新增代码+DesktopGUIBridge: 函数段结束，_send_json 到此结束；如果没有这个边界说明，用户不容易看出它只负责响应包装。

    def do_GET(self) -> None:  # 新增代码+DesktopGUIBridge: 处理 GET 请求；如果没有这段函数，GUI 无法读取 bootstrap 和事件。
        path = urllib.parse.urlparse(self.path).path  # 新增代码+DesktopGUIBridge: 提取路径；如果没有这行代码，带 query 的请求无法路由。
        if path in {"/v1/gui/bootstrap", "/gui/bootstrap"}:  # 新增代码+DesktopGUIBridge: 识别 bootstrap 端点；如果没有这行代码，前端首屏请求会 404。
            self._send_json(200, build_gui_bootstrap_payload(self.server.workspace))  # 新增代码+DesktopGUIBridge: 返回首屏 payload；如果没有这行代码，GUI 不能启动。
            return  # 新增代码+DesktopGUIBridge: 响应完成后退出；如果没有这行代码，handler 可能继续发送第二个响应。
        self._send_json(404, {"ok": False, "error": "未知 GUI bridge GET 路径。"})  # 新增代码+DesktopGUIBridge: 返回结构化 404；如果没有这行代码，前端会收到 HTML 错误页。
    # 新增代码+DesktopGUIBridge: 函数段结束，do_GET 到此结束；如果没有这个边界说明，用户不容易看出当前只开放只读端点。
# 新增代码+DesktopGUIBridge: 类段结束，DesktopGuiBridgeHandler 到此结束；如果没有这个边界说明，用户不容易看出 HTTP handler 范围。


def create_gui_bridge_server(workspace: str | Path, host: str = "127.0.0.1", port: int = 8776, token: str = "") -> DesktopGuiBridgeServer:  # 新增代码+DesktopGUIBridge: 函数段开始，创建 GUI bridge server；如果没有这段函数，CLI 和测试会重复构造逻辑。
    return DesktopGuiBridgeServer((host, port), workspace=workspace, token=token)  # 新增代码+DesktopGUIBridge: 返回绑定 server；如果没有这行代码，调用方拿不到可启动对象。
# 新增代码+DesktopGUIBridge: 函数段结束，create_gui_bridge_server 到此结束；如果没有这个边界说明，用户不容易看出它只负责创建 server。
```

- [ ] **Step 4: Add CLI command**

Modify `learning_agent/app/cli.py` by adding a `desktop-bridge` command that calls `create_gui_bridge_server`.

Required behavior:

```text
python -m learning_agent.app.cli desktop-bridge --workspace H:\codexworkplace\sofeware\OpenHarness-main --port 8776
```

Expected console output:

```text
Desktop GUI bridge 已启动：http://127.0.0.1:8776
接口：GET /v1/gui/bootstrap
```

- [ ] **Step 5: Add bridge security contract**

Create `learning_agent/tests/test_gui_bridge_security_contract.py`.

Required assertions:

- `/health` can return without a token.
- `/v1/gui/bootstrap` rejects requests without `X-OpenHarness-Desktop-Token`.
- `/v1/gui/bootstrap` rejects requests with a wrong token.
- `/v1/gui/bootstrap` accepts requests with the startup token.
- Requests with an unexpected `Origin` are rejected.
- Error responses are JSON and do not expose filesystem paths.

Required implementation behavior in `gui_bridge.py`:

```text
host defaults to 127.0.0.1
token is generated if the caller does not provide one
token is checked on every endpoint except /health
 Origin is allowed only when absent, null, file://, or http://127.0.0.1:5177 in dev
all errors return {"ok": false, "error": "...", "code": "..."}
```

Required CLI behavior:

```text
python -m learning_agent.app.cli desktop-bridge --workspace H:\codexworkplace\sofeware\OpenHarness-main --port 8776
```

Expected console output includes the URL and a one-line token handoff message for the Electron app. Do not print secrets in normal verbose logs after startup.

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_security_contract
```

Expected: `OK`.

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/app/cli.py learning_agent/tests/test_gui_bridge_contract.py learning_agent/tests/test_gui_bridge_security_contract.py
git commit -m "feat: expose desktop gui bridge server"
```

## Task 3: Event Polling Contract

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `learning_agent/tests/test_gui_bridge_events_contract.py`

- [ ] **Step 1: Write failing event endpoint test**

Create `learning_agent/tests/test_gui_bridge_events_contract.py`:

```python
from pathlib import Path  # 新增代码+DesktopGUIEventsTest: 使用 Path 构造临时工作区；如果没有这行代码，测试无法创建状态目录。


def test_gui_events_payload_uses_status_event_store(tmp_path: Path) -> None:  # 新增代码+DesktopGUIEventsTest: 验证 GUI 事件来自统一事件源；如果没有这段测试，前端可能读取旁路日志。
    from learning_agent.app.gui_bridge import build_gui_events_payload  # 新增代码+DesktopGUIEventsTest: 导入计划新增事件 helper；如果没有这行代码，测试无法锁定接口。
    from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIEventsTest: 使用真实状态事件 store；如果没有这行代码，测试不能证明复用事实源。

    store = StatusEventStore(tmp_path / "memory" / "status")  # 新增代码+DesktopGUIEventsTest: 创建临时事件 store；如果没有这行代码，事件没有落盘位置。
    store.append("status_probe", {"message": "hello"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+DesktopGUIEventsTest: 写入一条真实事件；如果没有这行代码，payload 只能返回空列表。

    payload = build_gui_events_payload(tmp_path, since_sequence=0, limit=10)  # 新增代码+DesktopGUIEventsTest: 读取 GUI 事件 payload；如果没有这行代码，无法验证事件接口。

    assert payload["ok"] is True  # 新增代码+DesktopGUIEventsTest: 确认响应成功；如果没有这行断言，失败响应可能误过。
    assert len(payload["events"]) == 1  # 新增代码+DesktopGUIEventsTest: 确认读到真实事件；如果没有这行断言，GUI 可能永远无进度。
    assert payload["events"][0]["event_type"] == "status_probe"  # 新增代码+DesktopGUIEventsTest: 确认事件类型保留；如果没有这行断言，前端无法分类渲染。
    assert payload["events"][0]["turn_id"] == "turn_a"  # 新增代码+DesktopGUIEventsTest: 确认 turn_id 顶层可见；如果没有这行断言，消息和事件无法关联。
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_events_contract
```

Expected: fail with missing `build_gui_events_payload`.

- [ ] **Step 3: Implement event payload helper**

Append to `learning_agent/app/gui_bridge.py`:

```python
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIBridge: 读取统一事件流；如果没有这行代码，GUI 事件会和 CLI/SDK 分裂。


def build_gui_events_payload(workspace: str | Path, since_sequence: int | None = None, limit: int = 50) -> dict[str, Any]:  # 新增代码+DesktopGUIBridge: 函数段开始，生成 GUI 事件轮询 payload；如果没有这段函数，前端无法增量刷新工具和任务状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBridge: 规范化工作区；如果没有这行代码，事件路径会不稳定。
    safe_limit = max(1, min(200, int(limit)))  # 新增代码+DesktopGUIBridge: 限制事件数量；如果没有这行代码，大量事件会拖慢 UI。
    store = StatusEventStore(workspace_path / "memory" / "status")  # 新增代码+DesktopGUIBridge: 打开统一状态事件 store；如果没有这行代码，payload 没有事件源。
    events = [event.to_dict() for event in store.list_events(since_sequence=since_sequence, limit=safe_limit)]  # 新增代码+DesktopGUIBridge: 读取并序列化事件；如果没有这行代码，前端收不到事件列表。
    return {"ok": True, "events": events, "since_sequence": since_sequence, "limit": safe_limit}  # 新增代码+DesktopGUIBridge: 返回稳定事件 payload；如果没有这行代码，前端无法记录游标。
# 新增代码+DesktopGUIBridge: 函数段结束，build_gui_events_payload 到此结束；如果没有这个边界说明，用户不容易看出它只负责事件轮询。
```

- [ ] **Step 4: Extend HTTP GET route**

Modify `DesktopGuiBridgeHandler.do_GET` so `/v1/gui/events` reads `since_sequence` and `limit` query parameters and returns `build_gui_events_payload`.

Exact route behavior:

```text
GET /v1/gui/events?since_sequence=10&limit=50
```

Expected JSON:

```json
{
  "ok": true,
  "events": [],
  "since_sequence": 10,
  "limit": 50
}
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_bridge_events_contract.py
git commit -m "feat: add desktop gui event polling contract"
```

## Task 4: Desktop App Bootstrap

**Files:**

- Create: `apps/desktop/package.json`
- Create: `apps/desktop/vite.config.ts`
- Create: `apps/desktop/tsconfig.json`
- Create: `apps/desktop/tsconfig.node.json`
- Create: `apps/desktop/index.html`
- Create: `apps/desktop/src/main/bridgeAuth.ts`
- Create: `apps/desktop/src/main/index.ts`
- Create: `apps/desktop/src/preload/index.ts`
- Create: `apps/desktop/src/renderer/main.tsx`
- Create: `apps/desktop/src/renderer/App.tsx`

- [ ] **Step 1: Create package file**

Create `apps/desktop/package.json`:

```json
{
  "name": "openharness-desktop",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "dist/main/index.js",
  "scripts": {
    "dev:renderer": "vite --host 127.0.0.1 --port 5177",
    "build:main": "tsc -p tsconfig.node.json",
    "build:renderer": "vite build",
    "build": "npm run build:main && npm run build:renderer",
    "test": "vitest run",
    "lint": "tsc -p tsconfig.json --noEmit && tsc -p tsconfig.node.json --noEmit",
    "start": "electron ."
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "electron": "^31.0.0",
    "lucide-react": "^0.468.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "vite": "^5.4.0"
  },
  "devDependencies": {
    "@types/node": "^20.14.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create TypeScript configs**

Create `apps/desktop/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src", "tests", "vite.config.ts"]
}
```

Create `apps/desktop/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "skipLibCheck": true,
    "types": ["node"],
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src/main", "src/preload", "vite.config.ts"]
}
```

- [ ] **Step 3: Create Vite config**

Create `apps/desktop/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: ".",
  server: {
    host: "127.0.0.1",
    port: 5177,
  },
  build: {
    outDir: "dist/renderer",
    emptyOutDir: true,
  },
});
```

- [ ] **Step 4: Create renderer HTML**

Create `apps/desktop/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OpenHarness Desktop</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/renderer/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create first React app**

Create `apps/desktop/src/renderer/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "../styles/theme.css";
import "../styles/layout.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `apps/desktop/src/renderer/App.tsx`:

```tsx
export function App() {
  return (
    <main className="app-shell">
      <aside className="left-rail">OpenHarness</aside>
      <section className="thread-panel">
        <header className="thread-header">快速对话</header>
        <div className="thread-body">桌面 GUI 外壳已启动。</div>
        <footer className="composer">要求后续变更</footer>
      </section>
    </main>
  );
}
```

- [ ] **Step 6: Create Electron shell**

Create `apps/desktop/src/main/bridgeAuth.ts`:

```ts
import crypto from "node:crypto";

export type BridgeAuth = {
  token: string;
  headers: Record<string, string>;
};

export function createBridgeAuth(): BridgeAuth {
  const token = crypto.randomBytes(32).toString("hex");
  return {
    token,
    headers: {
      "X-OpenHarness-Desktop-Token": token,
    },
  };
}
```

Create `apps/desktop/src/main/index.ts`:

```ts
import { app, BrowserWindow } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentFile = fileURLToPath(import.meta.url);
const currentDir = path.dirname(currentFile);

function createWindow() {
  const window = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 980,
    minHeight: 640,
    title: "OpenHarness Desktop",
    webPreferences: {
      preload: path.join(currentDir, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const devServerUrl = process.env.OPENHARNESS_DESKTOP_DEV_URL;
  if (devServerUrl) {
    void window.loadURL(devServerUrl);
    return;
  }

  void window.loadFile(path.join(currentDir, "../renderer/index.html"));
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
```

Create `apps/desktop/src/preload/index.ts`:

```ts
import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("openHarnessDesktop", {
  version: "0.1.0",
});
```

- [ ] **Step 7: Create base styles**

Create `apps/desktop/src/styles/theme.css`:

```css
:root {
  color-scheme: light;
  font-family: "Inter", "Segoe UI", system-ui, sans-serif;
  color: #1f2328;
  background: #f6f8fb;
}

body {
  margin: 0;
  min-width: 980px;
  min-height: 640px;
}

button,
input,
textarea {
  font: inherit;
}
```

Create `apps/desktop/src/styles/layout.css`:

```css
.app-shell {
  display: grid;
  grid-template-columns: 304px minmax(0, 1fr);
  min-height: 100vh;
}

.left-rail {
  border-right: 1px solid #d8dee8;
  background: #eef2f7;
  padding: 16px;
}

.thread-panel {
  display: grid;
  grid-template-rows: 56px minmax(0, 1fr) 96px;
  background: #ffffff;
}

.thread-header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e5e9f0;
  padding: 0 20px;
  font-weight: 600;
}

.thread-body {
  padding: 24px;
  overflow: auto;
}

.composer {
  border-top: 1px solid #e5e9f0;
  padding: 20px;
}
```

- [ ] **Step 8: Run type check**

Run:

```powershell
cd apps\desktop
npm install
npm run lint
npm run build
```

Expected: TypeScript and renderer build exit with code `0`, and `dist/main/index.js`, `dist/preload/index.js`, and `dist/renderer/index.html` exist.

- [ ] **Step 9: Commit**

```powershell
git add apps/desktop/package.json apps/desktop/vite.config.ts apps/desktop/tsconfig.json apps/desktop/tsconfig.node.json apps/desktop/index.html apps/desktop/src
git commit -m "feat: bootstrap desktop gui shell"
```

## Task 5: GUI API Client

**Files:**

- Create: `apps/desktop/src/api/guiClient.ts`
- Create: `apps/desktop/tests/guiClient.test.ts`

- [ ] **Step 1: Write API client test**

Create `apps/desktop/tests/guiClient.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";
import { createGuiClient } from "../src/api/guiClient";

describe("createGuiClient", () => {
  it("loads bootstrap payload from the GUI bridge", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        ok: true,
        workspace: "H:/repo",
        app: { name: "OpenHarness Desktop", schema_version: 1 },
        snapshot: {},
        feature_flags: { event_polling: true },
      }),
    })) as unknown as typeof fetch;

    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock);
    const payload = await client.bootstrap();

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/bootstrap", {
      headers: { "X-OpenHarness-Desktop-Token": "test-token" },
    });
    expect(payload.workspace).toBe("H:/repo");
  });
});
```

- [ ] **Step 2: Implement API client**

Create `apps/desktop/src/api/guiClient.ts`:

```ts
export type GuiBootstrapPayload = {
  ok: true;
  workspace: string;
  app: {
    name: string;
    schema_version: number;
  };
  snapshot: Record<string, unknown>;
  feature_flags: Record<string, boolean>;
};

export type GuiEventPayload = {
  ok: true;
  events: Array<Record<string, unknown>>;
  since_sequence: number | null;
  limit: number;
};

type FetchLike = typeof fetch;

export function createGuiClient(baseUrl: string, bridgeToken: string, fetcher: FetchLike = fetch) {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, "");
  const headers = { "X-OpenHarness-Desktop-Token": bridgeToken };

  async function requestJson<T>(path: string): Promise<T> {
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { headers });
    if (!response.ok) {
      throw new Error(`GUI bridge request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  }

  return {
    bootstrap(): Promise<GuiBootstrapPayload> {
      return requestJson<GuiBootstrapPayload>("/v1/gui/bootstrap");
    },
    events(sinceSequence: number | null, limit = 50): Promise<GuiEventPayload> {
      const query = sinceSequence === null ? `limit=${limit}` : `since_sequence=${sinceSequence}&limit=${limit}`;
      return requestJson<GuiEventPayload>(`/v1/gui/events?${query}`);
    },
  };
}
```

- [ ] **Step 3: Run frontend tests**

Run:

```powershell
cd apps\desktop
npm test
```

Expected: `guiClient.test.ts` passes.

- [ ] **Step 4: Commit**

```powershell
git add apps/desktop/src/api/guiClient.ts apps/desktop/tests/guiClient.test.ts
git commit -m "feat: add desktop gui api client"
```

## Task 6: App Shell Layout

**Files:**

- Create: `apps/desktop/src/components/AppShell.tsx`
- Create: `apps/desktop/src/components/Sidebar.tsx`
- Create: `apps/desktop/src/components/ThreadView.tsx`
- Create: `apps/desktop/src/components/Composer.tsx`
- Modify: `apps/desktop/src/renderer/App.tsx`
- Modify: `apps/desktop/src/styles/layout.css`

- [ ] **Step 1: Create AppShell component**

Create `apps/desktop/src/components/AppShell.tsx`:

```tsx
import { Sidebar } from "./Sidebar";
import { ThreadView } from "./ThreadView";
import { Composer } from "./Composer";

export function AppShell() {
  return (
    <main className="app-shell">
      <Sidebar />
      <section className="thread-panel" aria-label="当前对话">
        <header className="thread-header">快速对话</header>
        <ThreadView />
        <Composer />
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Create Sidebar component**

Create `apps/desktop/src/components/Sidebar.tsx`:

```tsx
import { Bot, Folder, Plug, Search, Settings, Zap } from "lucide-react";

const primaryItems = [
  { label: "快速对话", icon: Bot },
  { label: "搜索", icon: Search },
  { label: "插件", icon: Plug },
  { label: "自动化", icon: Zap },
];

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="项目和导航">
      <nav className="sidebar-section">
        {primaryItems.map((item) => {
          const Icon = item.icon;
          return (
            <button className="sidebar-item" key={item.label} type="button">
              <Icon aria-hidden="true" size={16} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <section className="sidebar-section" aria-label="项目">
        <div className="sidebar-heading">项目</div>
        <button className="sidebar-item" type="button">
          <Folder aria-hidden="true" size={16} />
          <span>OpenHarness-main</span>
        </button>
      </section>
      <button className="sidebar-item sidebar-settings" type="button">
        <Settings aria-hidden="true" size={16} />
        <span>设置</span>
      </button>
    </aside>
  );
}
```

- [ ] **Step 3: Create ThreadView and Composer**

Create `apps/desktop/src/components/ThreadView.tsx`:

```tsx
export function ThreadView() {
  return (
    <div className="thread-body">
      <article className="message assistant-message">
        <p>桌面 GUI 外壳已连接到 OpenHarness 后端蓝图。</p>
      </article>
    </div>
  );
}
```

Create `apps/desktop/src/components/Composer.tsx`:

```tsx
import { ArrowUp, Paperclip } from "lucide-react";

export function Composer() {
  return (
    <footer className="composer">
      <button className="icon-button" type="button" aria-label="添加附件">
        <Paperclip aria-hidden="true" size={18} />
      </button>
      <textarea className="composer-input" rows={1} placeholder="要求后续变更" />
      <button className="send-button" type="button" aria-label="发送">
        <ArrowUp aria-hidden="true" size={18} />
      </button>
    </footer>
  );
}
```

- [ ] **Step 4: Wire AppShell**

Replace `apps/desktop/src/renderer/App.tsx`:

```tsx
import { AppShell } from "../components/AppShell";

export function App() {
  return <AppShell />;
}
```

- [ ] **Step 5: Update layout CSS**

Append to `apps/desktop/src/styles/layout.css`:

```css
.sidebar {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 20px;
  border-right: 1px solid #d8dee8;
  background: #eef2f7;
  padding: 12px 8px;
}

.sidebar-section {
  display: grid;
  gap: 6px;
}

.sidebar-heading {
  padding: 10px 10px 4px;
  color: #6b7280;
  font-size: 12px;
}

.sidebar-item {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 36px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #30363d;
  padding: 0 10px;
  text-align: left;
}

.sidebar-item:hover {
  background: #dfe5ee;
}

.message {
  max-width: 760px;
  line-height: 1.6;
}

.composer {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) 40px;
  align-items: end;
  gap: 10px;
}

.composer-input {
  min-height: 44px;
  max-height: 160px;
  resize: vertical;
  border: 1px solid #d8dee8;
  border-radius: 8px;
  padding: 12px;
}

.icon-button,
.send-button {
  width: 40px;
  height: 40px;
  border: 1px solid #d8dee8;
  border-radius: 8px;
  background: #ffffff;
}

.send-button {
  background: #30363d;
  color: #ffffff;
}
```

- [ ] **Step 6: Run frontend checks**

Run:

```powershell
cd apps\desktop
npm run lint
npm test
```

Expected: both commands exit `0`.

- [ ] **Step 7: Commit**

```powershell
git add apps/desktop/src/components apps/desktop/src/renderer/App.tsx apps/desktop/src/styles/layout.css
git commit -m "feat: add codex-style desktop shell layout"
```

## Task 7: Thread State And Message Rendering

**Files:**

- Create: `apps/desktop/src/state/threadStore.ts`
- Create: `apps/desktop/tests/threadStore.test.ts`
- Modify: `apps/desktop/src/components/ThreadView.tsx`
- Modify: `apps/desktop/src/components/Composer.tsx`

- [ ] **Step 1: Write reducer test**

Create `apps/desktop/tests/threadStore.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { threadReducer } from "../src/state/threadStore";

describe("threadReducer", () => {
  it("adds user and assistant messages", () => {
    const afterUser = threadReducer(undefined, {
      type: "message_added",
      message: { id: "m1", role: "user", text: "你好" },
    });

    const afterAssistant = threadReducer(afterUser, {
      type: "message_added",
      message: { id: "m2", role: "assistant", text: "你好，我在。" },
    });

    expect(afterAssistant.messages).toHaveLength(2);
    expect(afterAssistant.messages[0].role).toBe("user");
    expect(afterAssistant.messages[1].text).toBe("你好，我在。");
  });
});
```

- [ ] **Step 2: Implement reducer**

Create `apps/desktop/src/state/threadStore.ts`:

```ts
export type ThreadMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
};

export type ThreadState = {
  messages: ThreadMessage[];
  activeTurnId: string | null;
  isRunning: boolean;
};

export type ThreadAction =
  | { type: "message_added"; message: ThreadMessage }
  | { type: "turn_started"; turnId: string }
  | { type: "turn_finished" };

const initialState: ThreadState = {
  messages: [],
  activeTurnId: null,
  isRunning: false,
};

export function threadReducer(state: ThreadState = initialState, action: ThreadAction): ThreadState {
  if (action.type === "message_added") {
    return { ...state, messages: [...state.messages, action.message] };
  }

  if (action.type === "turn_started") {
    return { ...state, activeTurnId: action.turnId, isRunning: true };
  }

  if (action.type === "turn_finished") {
    return { ...state, isRunning: false };
  }

  return state;
}
```

- [ ] **Step 3: Run reducer test**

Run:

```powershell
cd apps\desktop
npm test
```

Expected: reducer test passes.

- [ ] **Step 4: Commit**

```powershell
git add apps/desktop/src/state/threadStore.ts apps/desktop/tests/threadStore.test.ts
git commit -m "feat: add desktop thread state reducer"
```

## Task 8: Chat Run Lifecycle

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `learning_agent/tests/test_gui_bridge_contract.py`
- Create: `learning_agent/tests/test_gui_bridge_lifecycle_contract.py`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Modify: `apps/desktop/src/components/Composer.tsx`
- Modify: `apps/desktop/src/state/threadStore.ts`

- [ ] **Step 1: Backend lifecycle contract**

Create `learning_agent/tests/test_gui_bridge_lifecycle_contract.py`.

Required tests:

- `POST /v1/gui/messages` accepts `prompt`, creates a `turn_id`, creates a `run_id`, and returns `status=queued`.
- A second `POST /v1/gui/messages` while a turn is running returns HTTP `409` with `code=agent_busy`.
- `POST /v1/gui/turns/{turn_id}/cancel` records `gui_turn_cancel_requested`.
- A cancelled turn reaches `status=cancelled` and writes `gui_turn_cancelled`.
- `POST /v1/gui/turns/{turn_id}/retry` creates a new turn linked to the old turn.
- `POST /v1/gui/sessions/{session_id}/resume` returns the last known messages and event cursor.
- All lifecycle responses include `events_after_sequence`.

First message response:

Expected JSON:

```json
{
  "ok": true,
  "conversation_id": "default",
  "turn_id": "turn_...",
  "run_id": "run_...",
  "status": "queued",
  "events_after_sequence": 0
}
```

- [ ] **Step 2: Backend state machine**

Implement message submission in `gui_bridge.py` using a background worker and a single-agent lock.

Required state transitions:

```text
queued -> running -> completed
queued -> running -> failed
queued -> running -> needs_permission -> running -> completed
queued -> running -> needs_permission -> failed
queued -> running -> cancelling -> cancelled
```

Required event types:

```text
gui_turn_queued
gui_turn_started
gui_turn_needs_permission
gui_turn_cancel_requested
gui_turn_cancelled
gui_turn_retried
gui_turn_resumed
gui_turn_completed
gui_turn_failed
```

Required backend behavior:

- Use one active-turn lock for V1.
- Return `409 agent_busy` instead of silently queueing unlimited turns.
- Persist enough metadata to resume the latest session after desktop restart.
- Never mark the turn completed until the backend has produced a final answer or a terminal failure event.
- Never hide backend/tool failures behind a generic GUI-only message.

- [ ] **Step 3: Frontend API**

Extend `guiClient.ts`:

```ts
export type SendMessageResponse = {
  ok: true;
  conversation_id: string;
  turn_id: string;
  run_id: string;
  status: "queued";
  answer: string;
  events_after_sequence: number;
};

sendMessage(prompt: string, conversationId = "default"): Promise<SendMessageResponse> {
  return postJson<SendMessageResponse>("/v1/gui/messages", {
    conversation_id: conversationId,
    prompt,
  });
}

cancelTurn(turnId: string): Promise<{ ok: true; turn_id: string; status: "cancelling" }> {
  return postJson(`/v1/gui/turns/${turnId}/cancel`, {});
}

retryTurn(turnId: string): Promise<SendMessageResponse> {
  return postJson(`/v1/gui/turns/${turnId}/retry`, {});
}

resumeSession(sessionId: string): Promise<{ ok: true; session_id: string; messages: unknown[]; events_after_sequence: number }> {
  return postJson(`/v1/gui/sessions/${sessionId}/resume`, {});
}
```

- [ ] **Step 4: UI behavior**

Composer rules:

- Enter sends message.
- Shift+Enter inserts newline.
- Empty prompt keeps send button disabled.
- While turn is running, input remains editable but send button is disabled.
- User message appears immediately.
- Assistant placeholder appears with running status.
- Cancel button appears while the active turn is `queued`, `running`, or `needs_permission`.
- Retry button appears when the selected turn is `failed`, `cancelled`, or `completed`.
- Resume action appears after app restart when the bridge reports a resumable session.
- Busy backend response shows a clear message and does not duplicate the user prompt.

- [ ] **Step 5: Verification**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_lifecycle_contract
cd apps\desktop
npm run lint
npm test
```

Expected: all commands exit `0`.

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_bridge_contract.py learning_agent/tests/test_gui_bridge_lifecycle_contract.py apps/desktop/src/api/guiClient.ts apps/desktop/src/components/Composer.tsx apps/desktop/src/state/threadStore.ts
git commit -m "feat: add desktop chat run lifecycle"
```

## Task 9: Tool Call Cards And Status Timeline

**Files:**

- Create: `apps/desktop/src/components/ToolCallCard.tsx`
- Create: `apps/desktop/src/components/StatusInspector.tsx`
- Create: `apps/desktop/src/state/statusStore.ts`
- Modify: `apps/desktop/src/components/ThreadView.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`

- [ ] **Step 1: Define status store**

Create `apps/desktop/src/state/statusStore.ts`:

```ts
export type StatusEvent = {
  sequence: number;
  event_type: string;
  session_id: string;
  run_id: string;
  turn_id: string;
  payload: Record<string, unknown>;
};

export type StatusState = {
  lastSequence: number;
  events: StatusEvent[];
};

export function appendStatusEvents(state: StatusState, events: StatusEvent[]): StatusState {
  const lastSequence = events.reduce((current, event) => Math.max(current, event.sequence), state.lastSequence);
  return {
    lastSequence,
    events: [...state.events, ...events].slice(-300),
  };
}
```

- [ ] **Step 2: ToolCallCard**

Create `apps/desktop/src/components/ToolCallCard.tsx`:

```tsx
type ToolCallCardProps = {
  eventType: string;
  toolName: string;
  summary: string;
};

export function ToolCallCard({ eventType, toolName, summary }: ToolCallCardProps) {
  return (
    <article className="tool-card">
      <div className="tool-card-title">{toolName}</div>
      <div className="tool-card-meta">{eventType}</div>
      <p>{summary}</p>
    </article>
  );
}
```

- [ ] **Step 3: StatusInspector**

Create `apps/desktop/src/components/StatusInspector.tsx`:

```tsx
import type { StatusEvent } from "../state/statusStore";

type StatusInspectorProps = {
  events: StatusEvent[];
};

export function StatusInspector({ events }: StatusInspectorProps) {
  return (
    <aside className="status-inspector" aria-label="运行状态">
      <h2>运行状态</h2>
      {events.slice(-20).map((event) => (
        <div className="status-event" key={event.sequence}>
          <span>#{event.sequence}</span>
          <strong>{event.event_type}</strong>
        </div>
      ))}
    </aside>
  );
}
```

- [ ] **Step 4: Poll events**

In `App.tsx`, start a `setInterval` that calls `client.events(lastSequence, 50)` every 1500 ms while app is open. Clear the interval on unmount.

- [ ] **Step 5: Verification**

Run:

```powershell
cd apps\desktop
npm run lint
npm test
```

Expected: all frontend checks pass.

- [ ] **Step 6: Commit**

```powershell
git add apps/desktop/src/components/ToolCallCard.tsx apps/desktop/src/components/StatusInspector.tsx apps/desktop/src/state/statusStore.ts apps/desktop/src/components/ThreadView.tsx apps/desktop/src/api/guiClient.ts
git commit -m "feat: render desktop tool call timeline"
```

## Task 10: Project And Session Sidebar

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Modify: `apps/desktop/src/components/Sidebar.tsx`

- [ ] **Step 1: Backend sessions endpoint**

Expose `GET /v1/gui/sessions` from `gui_bridge.py`, using `build_status_snapshot(workspace).get("sessions", [])`.

Expected JSON:

```json
{
  "ok": true,
  "sessions": [],
  "resume": {}
}
```

- [ ] **Step 2: Frontend client**

Add:

```ts
sessions(): Promise<{ ok: true; sessions: Array<Record<string, unknown>>; resume: Record<string, unknown> }> {
  return requestJson("/v1/gui/sessions");
}
```

- [ ] **Step 3: Sidebar rendering**

Sidebar should show:

- Quick chat.
- Search.
- Plugins.
- Automations.
- Project name.
- Recent sessions.
- Settings.

- [ ] **Step 4: Verification**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract
cd apps\desktop
npm run lint
```

Expected: both commands exit `0`.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/app/gui_bridge.py apps/desktop/src/api/guiClient.ts apps/desktop/src/components/Sidebar.tsx
git commit -m "feat: add desktop project and session sidebar"
```

## Task 11: Browser Provider Panel

**Files:**

- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Create: `apps/desktop/src/components/BrowserPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`

- [ ] **Step 1: Backend browser endpoint**

Expose `GET /v1/gui/browser/providers` by reading `snapshot["browser"]["provider_status"]`.

Expected JSON:

```json
{
  "ok": true,
  "provider_status": {},
  "browser": {}
}
```

- [ ] **Step 2: BrowserPanel component**

Create `apps/desktop/src/components/BrowserPanel.tsx`:

```tsx
type BrowserPanelProps = {
  providerStatus: Record<string, unknown>;
};

export function BrowserPanel({ providerStatus }: BrowserPanelProps) {
  const providerNames = Object.keys((providerStatus.providers as Record<string, unknown> | undefined) ?? {});

  return (
    <section className="browser-panel" aria-label="浏览器状态">
      <h2>浏览器</h2>
      {providerNames.length === 0 ? (
        <p>暂无 provider 状态。</p>
      ) : (
        providerNames.map((name) => <div key={name}>{name}</div>)
      )}
    </section>
  );
}
```

- [ ] **Step 3: Verification**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract
cd apps\desktop
npm run lint
```

Expected: both commands exit `0`.

- [ ] **Step 4: Commit**

```powershell
git add learning_agent/app/gui_bridge.py apps/desktop/src/api/guiClient.ts apps/desktop/src/components/BrowserPanel.tsx apps/desktop/src/components/StatusInspector.tsx
git commit -m "feat: show browser provider status in desktop shell"
```

## Task 12: Permission And Safety UX

**Files:**

- Create: `apps/desktop/src/components/PermissionBanner.tsx`
- Create: `apps/desktop/src/components/PermissionDialog.tsx`
- Modify: `apps/desktop/src/state/statusStore.ts`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_bridge_permission_contract.py`

- [ ] **Step 1: Backend permission contract**

Create `learning_agent/tests/test_gui_bridge_permission_contract.py`.

Required tests:

- Bridge converts backend permission-required events into `gui_turn_needs_permission`.
- `POST /v1/gui/permissions/{request_id}/decision` accepts `approve`.
- `POST /v1/gui/permissions/{request_id}/decision` accepts `deny`.
- Unknown `request_id` returns structured `404 permission_not_found`.
- Duplicate decision returns structured `409 permission_already_answered`.
- Every permission decision writes an audit event through `StatusEventStore`.

Required endpoint:

```text
POST /v1/gui/permissions/{request_id}/decision
```

Request JSON:

```json
{
  "turn_id": "turn_20260625_001",
  "decision": "approve",
  "reason": "用户在 GUI 中点击允许"
}
```

Allowed decisions:

```text
approve
deny
```

- [ ] **Step 2: Permission event parser**

Add to `statusStore.ts`:

```ts
export function latestPermissionEvent(events: StatusEvent[]): StatusEvent | null {
  const permissionEvents = events.filter((event) =>
    ["permission_required", "permission_answered", "computer_use_permission_required"].includes(event.event_type),
  );

  return permissionEvents.at(-1) ?? null;
}
```

- [ ] **Step 3: PermissionBanner**

Create `apps/desktop/src/components/PermissionBanner.tsx`:

```tsx
type PermissionBannerProps = {
  title: string;
  detail: string;
};

export function PermissionBanner({ title, detail }: PermissionBannerProps) {
  return (
    <section className="permission-banner" role="status">
      <strong>{title}</strong>
      <span>{detail}</span>
    </section>
  );
}
```

- [ ] **Step 4: PermissionDialog**

Create `apps/desktop/src/components/PermissionDialog.tsx`:

```tsx
type PermissionDialogProps = {
  open: boolean;
  appName: string;
  reason: string;
  onApprove: () => void;
  onDeny: () => void;
};

export function PermissionDialog({ open, appName, reason, onApprove, onDeny }: PermissionDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="permission-dialog-backdrop">
      <section className="permission-dialog" role="dialog" aria-modal="true" aria-label="权限请求">
        <h2>权限请求</h2>
        <p>{appName}</p>
        <p>{reason}</p>
        <div className="permission-dialog-actions">
          <button type="button" onClick={onDeny}>拒绝</button>
          <button type="button" onClick={onApprove}>允许</button>
        </div>
      </section>
    </div>
  );
}
```

- [ ] **Step 5: Safety rules**

The GUI may show approve/deny controls, but the actual permission decision must still go through backend permission machinery. The front end sends intent only; the backend records and enforces policy.

Additional required behavior:

- Permission dialog shows the backend `request_id`, app/tool name, reason, and risk summary.
- Permission dialog never exposes raw secrets or hidden page text.
- Permission approval and denial are both visible in the status timeline.
- Permission requests time out into a visible `failed` or `cancelled` state instead of hanging forever.

- [ ] **Step 6: Verification**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_permission_contract
cd apps\desktop
npm run lint
npm test
```

Expected: backend permission contract and frontend checks pass.

- [ ] **Step 7: Commit**

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_bridge_permission_contract.py apps/desktop/src/components/PermissionBanner.tsx apps/desktop/src/components/PermissionDialog.tsx apps/desktop/src/state/statusStore.ts apps/desktop/src/components/AppShell.tsx
git commit -m "feat: add desktop permission surfaces"
```

## Task 13: Desktop Launch Scripts

**Files:**

- Modify: `apps/desktop/package.json`
- Create: `apps/desktop/scripts/start-backend.ps1`
- Create: `apps/desktop/scripts/start-desktop-dev.ps1`
- Modify: `README.md`

- [ ] **Step 1: Backend launch script**

Create `apps/desktop/scripts/start-backend.ps1`:

```powershell
param(
  [string]$Workspace = (Resolve-Path ..\..).Path,
  [int]$Port = 8776
)

python -m learning_agent.app.cli desktop-bridge --workspace $Workspace --port $Port
```

- [ ] **Step 2: Desktop dev script**

Create `apps/desktop/scripts/start-desktop-dev.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$DesktopRoot = Split-Path -Parent $PSScriptRoot
Set-Location $DesktopRoot

npm install
npm run build:main

$env:OPENHARNESS_DESKTOP_DEV_URL = "http://127.0.0.1:5177"
$renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer" -WindowStyle Hidden -PassThru
try {
  Start-Sleep -Seconds 3
  npm run start
}
finally {
  if ($renderer -and -not $renderer.HasExited) {
    Stop-Process -Id $renderer.Id -Force
  }
}
```

- [ ] **Step 3: package.json scripts**

Add:

```json
{
  "scripts": {
    "backend": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-backend.ps1",
    "desktop:dev": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-desktop-dev.ps1"
  }
}
```

- [ ] **Step 4: Verification**

Run:

```powershell
cd apps\desktop
npm run lint
npm run build
```

Expected: TypeScript and build exit `0`.

- [ ] **Step 5: Commit**

```powershell
git add apps/desktop/package.json apps/desktop/scripts README.md
git commit -m "feat: add desktop gui launch scripts"
```

## Task 14: Visible Desktop GUI Smoke And Acceptance

**Files:**

- Create: `apps/desktop/tests/smoke.md`
- Create: `apps/desktop/tests/gui-prompt-matrix.md`
- Create: `docs/desktop_gui_shell_architecture.md`
- Create: `learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md`

- [ ] **Step 1: Write smoke checklist**

Create `apps/desktop/tests/smoke.md`:

```markdown
# Desktop GUI Smoke Checklist

This checklist is Layer A visible desktop GUI acceptance. It validates the Electron shell, not the terminal agent.

- Start GUI bridge on localhost.
- Start desktop renderer and Electron shell.
- Confirm a real desktop window opens on the user's machine.
- Confirm the window is not blank.
- Confirm sidebar renders.
- Confirm thread panel renders.
- Confirm composer accepts text.
- Confirm bootstrap payload loads.
- Confirm event polling returns without error.
- Confirm browser provider panel handles empty provider state.
- Confirm permission banner can render from a synthetic event.
- Confirm cancel button changes a running turn into a visible cancelling/cancelled state.
- Confirm retry creates a new linked turn.
- Confirm resume restores the last session after window restart.
```

- [ ] **Step 2: Write GUI prompt matrix**

Create `apps/desktop/tests/gui-prompt-matrix.md`:

```markdown
# Desktop GUI Prompt Matrix

This matrix is Layer A visible desktop GUI acceptance. The V1 shell is not accepted until every scenario below has visible GUI evidence in the Electron window.

- Basic Chinese project-analysis prompt completes with a final answer.
- Basic English project-analysis prompt completes with a final answer.
- Long task prompt shows running state and tool/status events.
- Tool progress appears as at least one tool card.
- Browser provider status appears without renderer reading backend memory files.
- Permission approval request appears and approve intent reaches backend.
- Permission denial request appears and deny intent reaches backend.
- Cancel during running turn reaches visible cancelled state.
- Retry after failed turn creates a new linked turn.
- Retry after completed turn creates a new linked turn.
- Window restart resumes the latest session.
- Backend busy response does not duplicate the prompt.
- Failed tool event appears with readable error details.
- Safety refusal appears as an assistant message and terminal event.
- Chinese multiline input preserves newlines.
- Shift+Enter inserts newline.
- Enter sends prompt.
- Empty prompt cannot be sent.
- Bridge token rejection shows structured error.
- Unknown route shows structured JSON error.
```

- [ ] **Step 3: Write architecture doc**

Create `docs/desktop_gui_shell_architecture.md`:

```markdown
# Desktop GUI Shell Architecture

The OpenHarness desktop shell lives in `apps/desktop`.

The backend remains in `learning_agent`.

The bridge boundary is `learning_agent/app/gui_bridge.py`.

The renderer never reads backend memory files directly.

The renderer uses bridge endpoints and event polling to update UI state.

V1 readiness means the GUI prompt matrix passes, not only that the window opens.

`learning_agent/start_oauth_agent.bat` is the conditional backend-agent terminal gate. It is not the visible desktop GUI acceptance gate.
```

- [ ] **Step 4: Copy learning archive**

Create `learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md` and include:

```markdown
# Desktop GUI Shell Learning Archive

This archive records the files, tests, smoke evidence, and acceptance notes for the Codex-style desktop GUI shell.
```

- [ ] **Step 5: Automated verification**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_bridge_permission_contract
cd apps\desktop
npm run lint
npm test
npm run build
```

Expected: every command exits `0`.

- [ ] **Step 6: Visible desktop smoke**

Run:

```powershell
cd apps\desktop
npm run desktop:dev
```

Expected:

- A visible desktop window opens.
- Sidebar is visible.
- Chat panel is visible.
- Composer is visible.
- No text overlaps.
- No blank window.
- `apps/desktop/tests/gui-prompt-matrix.md` scenarios are checked against visible GUI behavior.
- Evidence is captured as screenshots, screen recording, or explicit manual notes in `learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md`.

- [ ] **Step 7: Conditional backend agent terminal gate**

This step is not the GUI visual acceptance gate. Run it only if the implementation changes agent runtime behavior, browser automation, Computer Use, MCP routing, model calls, or backend permission enforcement.

Conditional command:

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

Then enter a realistic prompt in the visible terminal and confirm the output. If Layer C is triggered but cannot be performed by the agent environment, state:

```text
真实可见终端交互验收未完成，不能声明后端 agent 行为变更完成。
```

If the task only changes the desktop renderer layout, visual styling, GUI-only state rendering, or GUI documentation, record this step as:

```text
未触发：本次只改 GUI 视觉/交互层，没有修改后端 agent 行为。
```

- [ ] **Step 8: Commit**

```powershell
git add apps/desktop/tests/smoke.md apps/desktop/tests/gui-prompt-matrix.md docs/desktop_gui_shell_architecture.md learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md
git commit -m "docs: add desktop gui smoke and architecture evidence"
```

## Task 15: Release Gate

**Files:**

- Create: `apps/desktop/scripts/release-gate.ps1`
- Modify: `docs/desktop_gui_shell_architecture.md`

- [ ] **Step 1: Create release gate script**

Create `apps/desktop/scripts/release-gate.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$DesktopRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $DesktopRoot "..\..")

Set-Location $RepoRoot
python -m unittest `
  learning_agent.tests.test_gui_bridge_contract `
  learning_agent.tests.test_gui_bridge_events_contract `
  learning_agent.tests.test_gui_bridge_security_contract `
  learning_agent.tests.test_gui_bridge_lifecycle_contract `
  learning_agent.tests.test_gui_bridge_permission_contract

Set-Location $DesktopRoot
npm run lint
npm test
npm run build
```

- [ ] **Step 2: Document release gate**

Append to `docs/desktop_gui_shell_architecture.md`:

```markdown
## Release Gate

Before claiming desktop GUI shell readiness, complete all required Layer A and Layer B checks.

Layer B automated gate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File apps/desktop/scripts/release-gate.ps1
```

Layer A visible desktop GUI gate:

- Run `cd apps\desktop`.
- Run `npm run desktop:dev`.
- Verify a real Electron window opens.
- Verify `apps/desktop/tests/smoke.md`.
- Verify `apps/desktop/tests/gui-prompt-matrix.md`.
- Save screenshots, screen recording, or manual notes in `learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md`.

Layer C conditional backend-agent terminal gate:

- Only required when a task changes agent runtime, MCP routing, model calls, browser automation, Computer Use, or backend permission enforcement.
- When required, run `learning_agent/start_oauth_agent.bat` in a visible terminal and type a realistic prompt.
- Layer C is not a replacement for Layer A.
```

- [ ] **Step 3: Run release gate**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File apps\desktop\scripts\release-gate.ps1
```

Expected: all checks exit `0`.

- [ ] **Step 4: Commit**

```powershell
git add apps/desktop/scripts/release-gate.ps1 docs/desktop_gui_shell_architecture.md
git commit -m "chore: add desktop gui release gate"
```

## Implementation Order

Use this order:

1. Backend bootstrap bridge.
2. Bridge security contract.
3. Event polling bridge.
4. Chat run lifecycle with cancel/retry/resume.
5. Backend permission decision contract.
6. Electron + React build chain.
7. API client.
8. Layout.
9. Thread state.
10. Tool timeline.
11. Sidebar sessions.
12. Browser provider panel.
13. Permission surfaces.
14. Launch scripts.
15. Smoke, prompt matrix, and release gate.

Stop after each task, run the listed checks, then commit.

## Drift Control Checklist

Before starting each task:

- Read this task only plus the file structure section.
- Confirm the files listed for the task are the only intended files.
- Run the failing test first when the task includes a backend or state contract.
- Keep GUI logic in `apps/desktop`.
- Keep backend bridge logic in `learning_agent/app/gui_bridge.py`.
- Keep existing agent logic in place.
- Keep V1 focused on one real prompt loop before adding broad sidebar features.
- Confirm every new UI action has a backend endpoint and event before rendering it as enabled.
- Update `agent_memory/progress.md` after completing a task.
- Add learning backup under `learning_agent/test/desktop_gui_shell_YYYYMMDD/` for changed code and docs.

Before claiming completion:

- Run the release gate.
- Run visible desktop smoke.
- Run the visible GUI prompt matrix.
- Run `start_oauth_agent.bat` visible terminal gate only if agent runtime behavior changed.
- Do not use `start_oauth_agent.bat` as proof that the desktop GUI visual shell works.
- Report any skipped verification honestly.

## Self-Review

Spec coverage:

- V1 micro-Codex vertical slice: covered by Tasks 1, 2, 3, 4, 5, 8, 12, 14, 15.
- Later mature Codex-like shell surface: covered by Tasks 6, 7, 9, 10, 11, 12, 13.
- Backend reuse: covered by Tasks 1, 2, 3, 8.
- Agent lifecycle reliability: covered by Task 8 and the prompt matrix in Task 14.
- Bridge security: covered by Task 2 and Task 15.
- Backend-enforced permissions: covered by Task 12.
- Long-task drift control: covered by maturity ladder, drift checklist, task ordering, release gate, and memory update rule.
- Browser/Computer Use visibility: covered by Tasks 11 and 12.
- Visible desktop GUI acceptance: covered by Task 14 Layer A.
- Automated contract/build acceptance: covered by Task 15 Layer B.
- Conditional backend-agent terminal acceptance: covered by Task 14 Layer C and Task 15 Layer C.

Placeholder scan:

- This plan avoids placeholder markers, vague "handle edge cases", and unbounded "write tests" instructions.

Type consistency:

- Backend functions use `build_gui_bootstrap_payload`, `build_gui_events_payload`, and `create_gui_bridge_server`.
- Frontend client uses `createGuiClient`, `bootstrap`, `events`, `sendMessage`, `cancelTurn`, `retryTurn`, and `resumeSession`.
- Event fields use existing `StatusEventStore` top-level `sequence`, `event_type`, `session_id`, `run_id`, and `turn_id`.
- Turn states use `queued`, `running`, `needs_permission`, `cancelling`, `completed`, `failed`, and `cancelled`.
