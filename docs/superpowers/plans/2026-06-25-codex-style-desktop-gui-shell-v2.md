# Codex-Style Desktop GUI Shell V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 V1 的 Electron GUI 外壳从“可见垂直切片”升级成接近 Codex 桌面体验的 V2 成熟外壳：真实流式对话、可靠恢复、工具轨迹、权限闭环、项目/会话管理、诊断、打包和可见 GUI 验收都成体系。

**Architecture:** 继续沿用 V1 的边界：`apps/desktop` 是 Electron/React 客户端，`learning_agent/app/gui_bridge.py` 是本地 loopback bridge，`learning_agent` 后端仍是运行事实源。V2 不让 renderer 直接读 `memory/` 或后端私有文件，而是通过 V2 协议、事件流、会话恢复接口和诊断接口读取状态。实现顺序采用“先协议和测试，再桥接真实 agent，再补 UI 面板和发布门禁”的方式，避免长任务跑偏。

**Tech Stack:** Electron 31、React 18、Vite 5、TypeScript 5、Vitest、Python 标准库 HTTP bridge、`unittest`、PowerShell release gate、现有 `learning_agent.runtime.status_events`、现有浏览器/Computer Use/权限/长任务 harness 能力。

---

## 1. 当前基线

V1 已经完成的内容：

- Electron 桌面窗口可以真实打开。
- GUI bridge 已有 token 保护、bootstrap、events 轮询、message、cancel、retry、resume、sessions、browser providers、permission decision。
- Renderer 已有 sidebar、thread panel、composer、status inspector、browser panel、permission banner/dialog、tool card。
- 可见 GUI 验收已经覆盖中文/英文 prompt、running、completed、failed、cancelled、retry、resume、permission approve/deny、tool card、browser provider panel。
- 自动化 release gate 已经覆盖 Python GUI bridge 合同测试、前端 lint、Vitest、production build。

V1 还没有达到 Codex 级成熟的关键差距：

- 回答仍以 V1 runner/轮询为主，不是完整真实 agent 流式输出。
- 没有稳定的 V2 协议 schema 分层，前后端类型仍容易一起膨胀。
- 错误、拒绝、安全提示还没有全部成为一等聊天消息。
- 多行中文输入和 Shift+Enter 还没有进入可见验收闭环。
- 工具轨迹只有基础卡片，没有完整 trace inspector、参数脱敏、stdout/stderr、重放线索。
- 项目、搜索、插件、自动化、设置、诊断、崩溃恢复、打包发布还只是 V1 外壳以外的能力。
- Layer A 可见 GUI 验收还没有被 release gate 自动要求。

## 2. V2 成熟定义

V2 只有同时满足下面条件，才可以说“接近 Codex 级成熟外壳”：

- 用户启动一个桌面入口后，能看到稳定的三栏或四区布局：项目/会话侧栏、对话主区、工具/状态检查区、设置/浏览器/诊断入口。
- 用户输入中文长 prompt 后，能看到 token 或 chunk 级流式输出，而不是只等最终答案。
- 用户可以取消、重试、恢复、查看历史 session；窗口重启、bridge 重启后仍能恢复最近会话。
- 工具调用、浏览器动作、Computer Use 权限请求、失败原因都以清晰 GUI 元素显示。
- 安全拒绝、token 错误、unknown route、bridge offline、backend busy 都以线程内消息或顶部诊断显示，不出现白屏或原始 traceback。
- 项目侧栏能展示当前 workspace、最近会话、搜索入口、基础设置入口。
- 所有新增后端接口都有 Python 合同测试；所有新增前端状态和组件行为都有 Vitest 覆盖。
- Layer A 可见 GUI 验收、Layer B 自动化验收、必要时 Layer C 真实终端 gate 的边界写清楚并执行。
- 发布门禁能一键运行，输出明确说明每一层验收结果。

## 3. 范围边界

V2 必须做：

- 复用 V1 的 `apps/desktop` 和 `learning_agent/app/gui_bridge.py`，不要新建一个脱节的桌面项目。
- 建立 V2 协议和事件流，让后续 UI、测试、真实 agent adapter 都围绕稳定合同演进。
- 补齐 V1 prompt matrix 中未完成的 GUI polish 项。
- 把 GUI 验收从“人工记录截图”升级成“有脚本、有矩阵、有可重复步骤”的门禁。
- 为后续自我开发 agent 项目保留可解释的 trace、session、权限、诊断数据结构。

V2 不强行做：

- 不在 V2 里承诺商业级代码签名证书，因为这依赖外部证书资产。
- 不默认开放高风险 Computer Use 自动操作，所有高风险动作仍走权限确认。
- 不把 renderer 变成后端文件读取器，避免 GUI 绕过 bridge 安全边界。
- 不在没有用户授权的情况下接管真实模型账号、浏览器账号或系统桌面权限。

## 4. 推荐方案

### 方案 A：在 V1 外壳上垂直升级，推荐

做法：

- 保留 `apps/desktop`。
- 保留 `learning_agent/app/gui_bridge.py`，但拆出协议、adapter、stream、diagnostics 等小模块。
- 先让 V2 协议和流式事件跑通，再扩展 UI。
- 每个模块完成后都进入 prompt matrix 和 release gate。

优点：

- 最少浪费 V1 代码。
- 风险小，用户能持续看到可运行 GUI。
- 适合长任务分阶段验收。

缺点：

- 需要小心拆分 V1 中已经变大的文件，不能一口气大改。

### 方案 B：新建 `apps/codex-shell-v2`

做法：

- 另建一个 Electron app，重新接 bridge。

优点：

- 可以从视觉和目录上完全重新整理。

缺点：

- V1 已完成的 tests、scripts、组件、验收证据会被绕开。
- 新旧外壳容易分叉，长期维护成本高。

### 方案 C：先做 Web UI，再封 Electron

做法：

- 先在浏览器里做 V2 UI，再接回桌面。

优点：

- 浏览器调试方便。

缺点：

- 用户最终目标是桌面外壳，Electron 的菜单、窗口、preload、token、可见验收仍要再做一次。

结论：采用方案 A。

## 5. V2 模块组成

V2 按 12 个模块推进，每个模块必须有独立测试和验收入口。

1. **协议模块**
   - 负责 V2 request/response/event schema、错误码、版本兼容。
   - 后端文件：`learning_agent/app/gui_protocol.py`
   - 前端文件：`apps/desktop/src/api/guiTypes.ts`

2. **事件流模块**
   - 负责 SSE 或长轮询 fallback、event id、heartbeat、断线重连。
   - 后端文件：`learning_agent/app/gui_stream.py`
   - 前端文件：`apps/desktop/src/api/streamClient.ts`

3. **真实 Agent Adapter 模块**
   - 负责把 GUI prompt 接到真实 agent/harness，而不是 V1 占位 runner。
   - 后端文件：`learning_agent/app/gui_agent_adapter.py`

4. **线程对话模块**
   - 负责流式 message parts、markdown/code/file links、失败和拒绝消息。
   - 前端文件：`apps/desktop/src/state/threadStore.ts`、`apps/desktop/src/components/ThreadView.tsx`

5. **Composer 输入模块**
   - 负责 Enter 发送、Shift+Enter 换行、中文多行持久化、附件入口。
   - 前端文件：`apps/desktop/src/components/Composer.tsx`

6. **工具轨迹模块**
   - 负责 tool call tree、参数脱敏、stdout/stderr、耗时、错误原因、复制诊断信息。
   - 前端文件：`apps/desktop/src/components/TracePanel.tsx`

7. **权限与安全模块**
   - 负责 permission request、approve/deny、临时授权、拒绝消息、安全策略说明。
   - 后端文件：`learning_agent/app/gui_permissions.py`
   - 前端文件：`apps/desktop/src/components/PermissionDialog.tsx`

8. **浏览器与 Computer Use 面板模块**
   - 负责 browser provider、visible Chromium、Chrome Extension、Computer Use lock/abort/status 的 GUI 展示。
   - 前端文件：`apps/desktop/src/components/BrowserPanel.tsx`、`apps/desktop/src/components/ComputerUsePanel.tsx`

9. **项目/会话/搜索模块**
   - 负责当前项目、最近会话、session rename、pin、archive、全文搜索入口。
   - 前端文件：`apps/desktop/src/components/Sidebar.tsx`、`apps/desktop/src/components/SearchPanel.tsx`

10. **长任务 Harness 模块**
    - 负责 goal、queue、checkpoint、pause/resume、status timeline、任务不跑偏提示。
    - 前端文件：`apps/desktop/src/components/HarnessPanel.tsx`

11. **设置与诊断模块**
    - 负责模型/provider、bridge 地址、token 状态、日志目录、版本、release gate 结果。
    - 前端文件：`apps/desktop/src/components/SettingsPanel.tsx`、`apps/desktop/src/components/DiagnosticsPanel.tsx`

12. **发布与验收模块**
    - 负责 Layer A/B/C 门禁、可见 GUI smoke、截图归档、release gate 汇总。
    - 脚本文件：`apps/desktop/scripts/release-gate.ps1`、`apps/desktop/scripts/visible-gui-smoke.ps1`

## 6. 数据流

```mermaid
flowchart LR
    User["用户在 Electron GUI 输入 prompt"]
    Composer["Composer 输入模块"]
    Renderer["React Renderer 状态机"]
    Client["guiClient / streamClient"]
    Bridge["Python GUI Bridge V2"]
    Adapter["真实 Agent Adapter"]
    Runtime["learning_agent Runtime / Harness / Tools"]
    Store["memory/gui_bridge + memory/status"]
    Panels["Thread / Trace / Permission / Browser / Diagnostics Panels"]

    User --> Composer
    Composer --> Renderer
    Renderer --> Client
    Client --> Bridge
    Bridge --> Adapter
    Adapter --> Runtime
    Runtime --> Store
    Store --> Bridge
    Bridge --> Client
    Client --> Renderer
    Renderer --> Panels
```

核心原则：

- 后端事实先落地，再通知前端。
- 前端可以显示 optimistic 状态，但必须被 bridge event 校正。
- 所有可恢复状态都有 session id、turn id、run id、event sequence。
- 所有用户可见错误都有 machine code 和 human message。

## 7. 文件结构规划

后端新增或调整：

- Modify: `learning_agent/app/gui_bridge.py`
  - 保留 HTTP server 和 routing，但把协议、事件流、adapter、权限、诊断逻辑拆出。
- Create: `learning_agent/app/gui_protocol.py`
  - 定义 schema version、错误码、event kind、message part、permission payload。
- Create: `learning_agent/app/gui_stream.py`
  - 定义 SSE/长轮询事件输出、heartbeat、reconnect cursor。
- Create: `learning_agent/app/gui_agent_adapter.py`
  - 定义 GUI 到真实 agent/harness 的 adapter 接口和默认实现。
- Create: `learning_agent/app/gui_diagnostics.py`
  - 定义 bridge health、runtime snapshot degraded、日志摘要、release gate 状态。
- Create: `learning_agent/app/gui_permissions.py`
  - 定义 GUI 权限请求、决策、审计结构。
- Test: `learning_agent/tests/test_gui_protocol_contract.py`
- Test: `learning_agent/tests/test_gui_stream_contract.py`
- Test: `learning_agent/tests/test_gui_agent_adapter_contract.py`
- Test: `learning_agent/tests/test_gui_diagnostics_contract.py`
- Test: `learning_agent/tests/test_gui_permissions_v2_contract.py`

前端新增或调整：

- Modify: `apps/desktop/src/api/guiClient.ts`
  - 保留 V1 方法，新增 V2 方法，错误响应解析为结构化对象。
- Create: `apps/desktop/src/api/guiTypes.ts`
  - 集中 TypeScript 类型，避免类型散落在 client 和组件里。
- Create: `apps/desktop/src/api/streamClient.ts`
  - 负责 SSE/长轮询 fallback、reconnect、heartbeat timeout。
- Modify: `apps/desktop/src/state/threadStore.ts`
  - 支持 message parts、stream delta、安全拒绝、线程内错误。
- Create: `apps/desktop/src/state/eventReducer.ts`
  - 把后端 event 归一化为 UI state action。
- Create: `apps/desktop/src/state/settingsStore.ts`
  - 保存设置 panel 所需状态。
- Modify: `apps/desktop/src/components/AppShell.tsx`
  - 扩展 shell layout，增加右侧 inspector tabs 和底部诊断状态。
- Modify: `apps/desktop/src/components/ThreadView.tsx`
  - 支持流式 assistant message、markdown/code block、file link。
- Modify: `apps/desktop/src/components/Composer.tsx`
  - 支持 Shift+Enter、多行中文持久化、发送禁用原因。
- Create: `apps/desktop/src/components/TracePanel.tsx`
- Create: `apps/desktop/src/components/SearchPanel.tsx`
- Create: `apps/desktop/src/components/SettingsPanel.tsx`
- Create: `apps/desktop/src/components/DiagnosticsPanel.tsx`
- Create: `apps/desktop/src/components/ComputerUsePanel.tsx`
- Modify: `apps/desktop/src/styles/layout.css`
- Modify: `apps/desktop/src/styles/theme.css`
- Test: `apps/desktop/tests/guiClient.test.ts`
- Test: `apps/desktop/tests/streamClient.test.ts`
- Test: `apps/desktop/tests/threadStore.test.ts`
- Test: `apps/desktop/tests/eventReducer.test.ts`
- Test: `apps/desktop/tests/composer.test.ts`
- Test: `apps/desktop/tests/settingsStore.test.ts`
- Update: `apps/desktop/tests/gui-prompt-matrix.md`
- Update: `apps/desktop/tests/smoke.md`

脚本和文档：

- Modify: `apps/desktop/scripts/release-gate.ps1`
- Create: `apps/desktop/scripts/visible-gui-smoke.ps1`
- Update: `docs/desktop_gui_shell_architecture.md`
- Create: `docs/desktop_gui_shell_v2_acceptance.md`
- Update: `learning_agent/test/desktop_gui_shell_20260625/README.md` or create a V2 archive folder.
- Update: `agent_memory/progress.md`
- Update: `agent_memory/bugs.md` when a V2 risk becomes confirmed.

## 8. 验收分层

Layer A：可见桌面 GUI 验收。

- 必须启动真实 Electron 桌面窗口。
- 必须能输入真实用户 prompt。
- 必须观察 GUI 内的流式输出、工具卡片、权限弹窗、错误消息、恢复行为。
- V2 的“完成”必须有截图或可见 smoke 记录。

Layer B：自动化合同和构建验收。

- Python GUI bridge V2 tests 通过。
- Frontend Vitest 通过。
- TypeScript lint/build 通过。
- Production build 通过。
- release gate 汇总通过。

Layer C：真实可见终端 agent gate。

- 只有当任务修改 agent runtime、MCP routing、模型调用、浏览器自动化、Computer Use 执行或后端权限 enforcement 时触发。
- 如果只改 GUI shell、视觉、renderer 状态、文档和 release gate，Layer C 不触发。
- 一旦触发，必须按 `learning_agent/start_oauth_agent.bat` 的真实可见终端交互定义执行，不能用单元测试、stdin、HTTP bridge、自测脚本替代。

## 9. 实施任务

### Task 0: V2 基线冻结

**Files:**
- Read: `docs/desktop_gui_shell_architecture.md`
- Read: `apps/desktop/tests/gui-prompt-matrix.md`
- Read: `learning_agent/test/desktop_gui_shell_20260625/README.md`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: 确认工作树和分支**

Run:

```powershell
git -C H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1 status --short --branch
```

Expected:

```text
## codex/desktop-gui-shell-v1
```

- [ ] **Step 2: 记录 V2 开工范围**

Add a short entry to `agent_memory/progress.md`:

```markdown
## 2026-06-25 Codex-style Desktop GUI Shell V2

- Status: planning approved, implementation not started.
- Scope: upgrade V1 Electron shell into V2 mature shell with streaming, real agent adapter, recovery, trace, permissions, search, settings, diagnostics, packaging, and layered GUI acceptance.
- Working tree: H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1
```

- [ ] **Step 3: Commit planning baseline**

Run:

```powershell
git add docs/superpowers/plans/2026-06-25-codex-style-desktop-gui-shell-v2.md agent_memory/progress.md
git commit -m "docs: add desktop gui shell v2 blueprint"
```

Expected:

```text
[codex/desktop-gui-shell-v1 ...] docs: add desktop gui shell v2 blueprint
```

### Task 1: V2 协议合同

**Files:**
- Create: `learning_agent/app/gui_protocol.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_protocol_contract.py`
- Create: `apps/desktop/src/api/guiTypes.ts`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/guiClient.test.ts`

- [ ] **Step 1: 写后端协议测试**

Create `learning_agent/tests/test_gui_protocol_contract.py` with tests for:

- `schema_version == 2`
- error response shape contains `ok: false`, `code`, `message`, `request_id`
- event shape contains `sequence`, `event_id`, `kind`, `created_at`, `run_id`, `turn_id`, `payload`
- message part shape supports `text_delta`, `final_text`, `refusal`, `tool_call`, `tool_result`, `error`

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_protocol_contract
```

Expected first run:

```text
FAILED
```

- [ ] **Step 2: 实现最小协议模块**

Create `learning_agent/app/gui_protocol.py` with:

```python
GUI_V2_SCHEMA_VERSION = 2
GUI_V2_TOKEN_HEADER = "X-OpenHarness-Desktop-Token"
GUI_V2_EVENT_KINDS = {
    "turn_started",
    "message_delta",
    "message_completed",
    "tool_started",
    "tool_finished",
    "permission_requested",
    "permission_answered",
    "safety_refusal",
    "turn_failed",
    "turn_cancelled",
    "heartbeat",
}
```

Also add helper functions:

- `make_error_response(code: str, message: str, request_id: str = "") -> dict[str, object]`
- `make_event(kind: str, sequence: int, payload: dict[str, object], run_id: str = "", turn_id: str = "") -> dict[str, object]`

- [ ] **Step 3: Run backend protocol test**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_protocol_contract
```

Expected:

```text
OK
```

- [ ] **Step 4: Add frontend V2 types**

Create `apps/desktop/src/api/guiTypes.ts` with TypeScript types mirroring the backend protocol:

```typescript
export type GuiV2EventKind =
  | "turn_started"
  | "message_delta"
  | "message_completed"
  | "tool_started"
  | "tool_finished"
  | "permission_requested"
  | "permission_answered"
  | "safety_refusal"
  | "turn_failed"
  | "turn_cancelled"
  | "heartbeat";
```

- [ ] **Step 5: Extend frontend client tests**

Update `apps/desktop/tests/guiClient.test.ts` to verify structured V2 errors are parsed without losing `code` and `message`.

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run guiClient.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit**

Run:

```powershell
git add learning_agent/app/gui_protocol.py learning_agent/tests/test_gui_protocol_contract.py apps/desktop/src/api/guiTypes.ts apps/desktop/src/api/guiClient.ts apps/desktop/tests/guiClient.test.ts
git commit -m "feat: add desktop gui v2 protocol contract"
```

### Task 2: V2 事件流和断线恢复

**Files:**
- Create: `learning_agent/app/gui_stream.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_stream_contract.py`
- Create: `apps/desktop/src/api/streamClient.ts`
- Create: `apps/desktop/tests/streamClient.test.ts`

- [ ] **Step 1: 写事件流合同测试**

Backend must support:

- `GET /v2/gui/events/stream?since_sequence=<n>`
- `GET /v2/gui/events?since_sequence=<n>&limit=<n>` fallback
- heartbeat event when no business event exists
- reconnect starts after last seen sequence

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_stream_contract
```

Expected first run:

```text
FAILED
```

- [ ] **Step 2: Implement stream module**

Create `learning_agent/app/gui_stream.py` with focused helpers:

- `format_sse_event(event: dict[str, object]) -> bytes`
- `format_sse_comment(text: str) -> bytes`
- `select_events_after(workspace: Path, since_sequence: int | None, limit: int) -> list[dict[str, object]]`

Implementation rule:

- Do not expose local filesystem paths in stream errors.
- Emit structured `heartbeat` events instead of keeping the UI silent forever.

- [ ] **Step 3: Wire bridge V2 stream routes**

Modify `learning_agent/app/gui_bridge.py`:

- Add `GET /v2/gui/events`.
- Add `GET /v2/gui/events/stream`.
- Keep all `/v1/gui/*` routes alive for compatibility.

- [ ] **Step 4: Add frontend stream client**

Create `apps/desktop/src/api/streamClient.ts`:

- Use `EventSource` when available and token can be passed safely through bridge-provided query token.
- Use long polling fallback when `EventSource` cannot carry the required header.
- Expose `connectGuiEventStream({ sinceSequence, onEvent, onError })`.

- [ ] **Step 5: Test reconnect behavior**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run streamClient.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 6: Commit**

Run:

```powershell
git add learning_agent/app/gui_stream.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_stream_contract.py apps/desktop/src/api/streamClient.ts apps/desktop/tests/streamClient.test.ts
git commit -m "feat: stream desktop gui v2 events"
```

### Task 3: 真实 Agent Adapter

**Files:**
- Create: `learning_agent/app/gui_agent_adapter.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_agent_adapter_contract.py`

- [ ] **Step 1: 写 adapter 合同测试**

Test cases:

- GUI prompt creates a run with `session_id`, `turn_id`, `run_id`, `prompt`.
- Adapter emits `turn_started`, at least one `message_delta`, and `message_completed`.
- Adapter propagates cancellation to the running turn.
- Adapter converts backend exceptions into `turn_failed` event.
- Adapter can run in deterministic fake mode for frontend tests.

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_agent_adapter_contract
```

Expected first run:

```text
FAILED
```

- [ ] **Step 2: Create adapter interface**

Create `learning_agent/app/gui_agent_adapter.py` with:

- `GuiAgentRunRequest`
- `GuiAgentRunResult`
- `GuiAgentAdapter`
- `FakeStreamingGuiAgentAdapter`
- `DefaultHarnessGuiAgentAdapter`

The default adapter should use existing harness/runtime entry points available in this repository. If an exact stable entry point is not available, keep the default adapter behind a feature flag and fail with a structured `adapter_unavailable` event, not a traceback.

- [ ] **Step 3: Wire bridge run manager to adapter**

Modify `GuiRunManager` in `learning_agent/app/gui_bridge.py`:

- Accept `agent_adapter`.
- Use adapter for V2 turns.
- Keep V1 answer runner path for compatibility tests.

- [ ] **Step 4: Run backend adapter tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_agent_adapter_contract
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app/gui_agent_adapter.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_agent_adapter_contract.py
git commit -m "feat: connect desktop gui to agent adapter"
```

### Task 4: Thread 流式渲染和一等消息

**Files:**
- Modify: `apps/desktop/src/state/threadStore.ts`
- Create: `apps/desktop/src/state/eventReducer.ts`
- Modify: `apps/desktop/src/components/ThreadView.tsx`
- Test: `apps/desktop/tests/threadStore.test.ts`
- Create: `apps/desktop/tests/eventReducer.test.ts`

- [ ] **Step 1: Write frontend reducer tests**

Cover:

- `message_delta` appends text to active assistant message.
- `message_completed` finalizes text.
- `safety_refusal` creates an assistant-visible refusal message.
- `turn_failed` creates a visible error message.
- unknown event kind is ignored with diagnostics instead of crashing.

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run threadStore.test.ts eventReducer.test.ts
```

Expected first run:

```text
FAIL
```

- [ ] **Step 2: Implement event reducer**

Create `apps/desktop/src/state/eventReducer.ts`:

- Convert backend V2 events into existing `ThreadAction`.
- Keep reducer pure and deterministic.
- Use existing `ThreadMessage` shape until a message-part split is needed.

- [ ] **Step 3: Update ThreadView**

Modify `ThreadView.tsx`:

- Render streaming assistant message without layout jumps.
- Render refusal with normal assistant message chrome and a clear safety label.
- Render in-thread error with retry action when a turn id exists.
- Render code blocks using `<pre><code>` with horizontal scroll.

- [ ] **Step 4: Run frontend tests**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run threadStore.test.ts eventReducer.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add apps/desktop/src/state/threadStore.ts apps/desktop/src/state/eventReducer.ts apps/desktop/src/components/ThreadView.tsx apps/desktop/tests/threadStore.test.ts apps/desktop/tests/eventReducer.test.ts
git commit -m "feat: render streaming desktop gui messages"
```

### Task 5: Composer 多行中文和发送体验

**Files:**
- Modify: `apps/desktop/src/components/Composer.tsx`
- Create: `apps/desktop/tests/composer.test.ts`
- Update: `apps/desktop/tests/gui-prompt-matrix.md`

- [ ] **Step 1: Write Composer tests**

Cover:

- Enter sends non-empty prompt.
- Shift+Enter inserts newline.
- Chinese multiline text is passed to `sendMessage` with newline preserved.
- Empty or whitespace-only prompt cannot be sent.
- Running turn disables send and shows concise reason through button state.

- [ ] **Step 2: Implement Composer behavior**

Modify `Composer.tsx`:

- Use a controlled textarea.
- Keep caret behavior stable after Shift+Enter.
- Clear input only after `sendMessage` accepts the prompt.
- Preserve Chinese punctuation and newline exactly.

- [ ] **Step 3: Run tests**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run composer.test.ts
```

Expected:

```text
PASS
```

- [ ] **Step 4: Commit**

Run:

```powershell
git add apps/desktop/src/components/Composer.tsx apps/desktop/tests/composer.test.ts apps/desktop/tests/gui-prompt-matrix.md
git commit -m "feat: polish desktop gui composer input"
```

### Task 6: 权限与安全 V2

**Files:**
- Create: `learning_agent/app/gui_permissions.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_permissions_v2_contract.py`
- Modify: `apps/desktop/src/components/PermissionDialog.tsx`
- Modify: `apps/desktop/src/components/PermissionBanner.tsx`

- [ ] **Step 1: Write permission V2 contract tests**

Cover:

- permission request has `request_id`, `turn_id`, `run_id`, `tool_name`, `reason`, `risk_summary`, `created_at`.
- approve/deny is idempotent.
- repeated decision returns structured `permission_already_answered`.
- denied permission emits visible event for thread and trace panel.

- [ ] **Step 2: Implement backend permission helpers**

Create `gui_permissions.py`:

- Normalize permission request payloads.
- Normalize decisions.
- Redact dangerous local paths or secrets from user-facing messages.
- Preserve audit fields for trace panel.

- [ ] **Step 3: Update GUI permission components**

Modify dialog/banner:

- Show tool/app name, action summary, risk summary, and decision buttons.
- Keep approve and deny visually distinct.
- Disable buttons after decision until backend confirms state.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_permissions_v2_contract
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run
```

Expected:

```text
OK
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app/gui_permissions.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_permissions_v2_contract.py apps/desktop/src/components/PermissionDialog.tsx apps/desktop/src/components/PermissionBanner.tsx
git commit -m "feat: add desktop gui permission v2 flow"
```

### Task 7: Trace Inspector

**Files:**
- Create: `apps/desktop/src/components/TracePanel.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/styles/layout.css`
- Test: `apps/desktop/tests/eventReducer.test.ts`

- [ ] **Step 1: Extend event tests for tools**

Cover:

- `tool_started` creates a trace row.
- `tool_finished` updates duration and output summary.
- failed tool shows error code and readable message.
- sensitive fields are displayed as `[redacted]`.

- [ ] **Step 2: Create TracePanel**

TracePanel should show:

- run id and turn id.
- ordered event list.
- tool name.
- status.
- duration.
- redacted args preview.
- result summary.
- copy diagnostic button.

- [ ] **Step 3: Wire inspector tabs**

Modify `AppShell.tsx`:

- Right panel tabs: `状态`, `工具`, `浏览器`, `设置`, `诊断`.
- Keep cards at 8px radius or less.
- Use lucide icons for compact tab buttons.

- [ ] **Step 4: Run frontend tests and lint**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run
npm run lint
```

Expected:

```text
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add apps/desktop/src/components/TracePanel.tsx apps/desktop/src/components/AppShell.tsx apps/desktop/src/components/StatusInspector.tsx apps/desktop/src/styles/layout.css apps/desktop/tests/eventReducer.test.ts
git commit -m "feat: add desktop gui trace inspector"
```

### Task 8: 项目、会话和搜索入口

**Files:**
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_sessions_search_contract.py`
- Modify: `apps/desktop/src/components/Sidebar.tsx`
- Create: `apps/desktop/src/components/SearchPanel.tsx`

- [ ] **Step 1: Write sessions/search backend tests**

Cover:

- sessions list returns stable id, title, last message preview, updated_at.
- rename session changes title.
- archive session hides it from default list and keeps it recoverable through archived filter.
- search query returns matching session ids and message snippets.

- [ ] **Step 2: Add backend routes**

Add routes:

- `GET /v2/gui/sessions`
- `POST /v2/gui/sessions/{session_id}/rename`
- `POST /v2/gui/sessions/{session_id}/archive`
- `GET /v2/gui/search?q=<query>`

- [ ] **Step 3: Update Sidebar**

Sidebar should show:

- current workspace.
- new conversation action.
- recent sessions.
- pinned or active session state.
- search button.
- archived filter entry.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_sessions_search_contract
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run
```

Expected:

```text
OK
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_sessions_search_contract.py apps/desktop/src/components/Sidebar.tsx apps/desktop/src/components/SearchPanel.tsx
git commit -m "feat: add desktop gui session search"
```

### Task 9: 浏览器和 Computer Use 成熟面板

**Files:**
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_browser_computer_panel_contract.py`
- Modify: `apps/desktop/src/components/BrowserPanel.tsx`
- Create: `apps/desktop/src/components/ComputerUsePanel.tsx`

- [ ] **Step 1: Write backend panel data tests**

Cover:

- browser provider status degrades without path leakage.
- visible Chromium status is represented when available.
- extension host status is represented when available.
- Computer Use lock/abort status appears with safe fields.

- [ ] **Step 2: Add V2 panel payload**

Add `GET /v2/gui/runtime/panels` returning:

- `browser`
- `computer_use`
- `permissions`
- `status_degraded`
- `safe_error`

- [ ] **Step 3: Update panels**

BrowserPanel:

- provider chips.
- active target summary.
- degraded banner.

ComputerUsePanel:

- lock owner summary.
- abort state.
- permission mode.
- safe disabled state when unavailable.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_browser_computer_panel_contract
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run
```

Expected:

```text
OK
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_browser_computer_panel_contract.py apps/desktop/src/components/BrowserPanel.tsx apps/desktop/src/components/ComputerUsePanel.tsx
git commit -m "feat: surface browser and computer use status in gui"
```

### Task 10: 长任务 Harness GUI

**Files:**
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `learning_agent/tests/test_gui_harness_panel_contract.py`
- Create: `apps/desktop/src/components/HarnessPanel.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`

- [ ] **Step 1: Write harness panel tests**

Cover:

- current goal status appears if a goal is active.
- queue entries appear with status.
- checkpoint events appear in order.
- pause/resume request returns structured response.

- [ ] **Step 2: Add harness summary endpoint**

Add `GET /v2/gui/harness/status`.

Payload fields:

- `active_goal`
- `queue`
- `checkpoints`
- `last_progress`
- `blocked_reason`
- `safe_error`

- [ ] **Step 3: Create HarnessPanel**

Panel should show:

- active goal.
- running step.
- checkpoints.
- blocked warning.
- pause/resume controls only when backend supports them.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_harness_panel_contract
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run
```

Expected:

```text
OK
PASS
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_harness_panel_contract.py apps/desktop/src/components/HarnessPanel.tsx apps/desktop/src/components/AppShell.tsx
git commit -m "feat: add desktop gui long task harness panel"
```

### Task 11: 设置、诊断和崩溃恢复

**Files:**
- Create: `learning_agent/app/gui_diagnostics.py`
- Create: `learning_agent/tests/test_gui_diagnostics_contract.py`
- Create: `apps/desktop/src/components/SettingsPanel.tsx`
- Create: `apps/desktop/src/components/DiagnosticsPanel.tsx`
- Create: `apps/desktop/src/state/settingsStore.ts`
- Test: `apps/desktop/tests/settingsStore.test.ts`

- [ ] **Step 1: Write diagnostics backend tests**

Cover:

- bridge health returns schema version, uptime, workspace, feature flags.
- diagnostics redacts token and local secret paths.
- degraded snapshot includes safe message.
- last release gate result can be read when present.

- [ ] **Step 2: Implement diagnostics module**

Create `gui_diagnostics.py`:

- `build_gui_health_payload`
- `build_gui_diagnostics_payload`
- `redact_diagnostic_text`

- [ ] **Step 3: Add settings UI**

SettingsPanel should show:

- model/provider display.
- bridge URL host and port without token.
- feature flags.
- theme choice.
- log and evidence folder path with copy button.

- [ ] **Step 4: Add diagnostics UI**

DiagnosticsPanel should show:

- backend online/offline.
- schema version.
- degraded state.
- last error.
- release gate status.
- copy diagnostic bundle button.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_gui_diagnostics_contract
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm test -- --run settingsStore.test.ts
npm run lint
```

Expected:

```text
OK
PASS
```

- [ ] **Step 6: Commit**

Run:

```powershell
git add learning_agent/app/gui_diagnostics.py learning_agent/tests/test_gui_diagnostics_contract.py apps/desktop/src/components/SettingsPanel.tsx apps/desktop/src/components/DiagnosticsPanel.tsx apps/desktop/src/state/settingsStore.ts apps/desktop/tests/settingsStore.test.ts
git commit -m "feat: add desktop gui settings and diagnostics"
```

### Task 12: 视觉成熟度和可访问性

**Files:**
- Modify: `apps/desktop/src/styles/layout.css`
- Modify: `apps/desktop/src/styles/theme.css`
- Modify: `apps/desktop/src/components/*.tsx`
- Update: `apps/desktop/tests/smoke.md`

- [ ] **Step 1: Define visual acceptance checklist**

Update `apps/desktop/tests/smoke.md` with checks:

- 1280x800 desktop window has no text overlap.
- 1024x720 compact window remains usable.
- buttons have icon labels or accessible labels.
- right inspector tabs remain visible.
- composer keeps stable height within min/max.
- tool cards do not resize layout unexpectedly.

- [ ] **Step 2: Polish layout**

Rules:

- No nested cards.
- Cards use 8px radius or less.
- Operational SaaS-style shell: quiet, dense, scannable.
- Avoid one-note palette.
- Use lucide icons where suitable.
- Keep text readable at Windows default scaling.

- [ ] **Step 3: Manual visible GUI pass**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-desktop-dev.ps1
```

Expected:

```text
Electron window opens, thread/composer/sidebar/inspector are visible, no blank panel, no obvious overlap.
```

- [ ] **Step 4: Commit**

Run:

```powershell
git add apps/desktop/src/styles/layout.css apps/desktop/src/styles/theme.css apps/desktop/src/components apps/desktop/tests/smoke.md
git commit -m "feat: polish desktop gui visual shell"
```

### Task 13: 打包和启动体验

**Files:**
- Modify: `apps/desktop/package.json`
- Create: `apps/desktop/scripts/package-windows.ps1`
- Modify: `apps/desktop/scripts/start-backend.ps1`
- Modify: `apps/desktop/scripts/start-desktop-dev.ps1`
- Update: `docs/desktop_gui_shell_architecture.md`

- [ ] **Step 1: Add packaging script test by dry run**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm run build
```

Expected:

```text
build completes without TypeScript or Vite errors.
```

- [ ] **Step 2: Add Windows packaging script**

Create `apps/desktop/scripts/package-windows.ps1`:

- Runs `npm ci` if `node_modules` is absent.
- Runs `npm run build`.
- Produces a local unpacked Electron app or clear package artifact.
- Writes package summary to `learning_agent/test/desktop_gui_shell_v2/package_summary.txt`.

- [ ] **Step 3: Improve startup diagnostics**

Update startup scripts:

- Print bridge URL.
- Print renderer URL.
- Print evidence folder.
- Print clear error if port is occupied.

- [ ] **Step 4: Run package script**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\package-windows.ps1
```

Expected:

```text
Desktop package artifact created.
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add apps/desktop/package.json apps/desktop/scripts/package-windows.ps1 apps/desktop/scripts/start-backend.ps1 apps/desktop/scripts/start-desktop-dev.ps1 docs/desktop_gui_shell_architecture.md
git commit -m "feat: add desktop gui packaging flow"
```

### Task 14: Release gate V2

**Files:**
- Modify: `apps/desktop/scripts/release-gate.ps1`
- Create: `apps/desktop/scripts/visible-gui-smoke.ps1`
- Update: `apps/desktop/tests/gui-prompt-matrix.md`
- Create: `docs/desktop_gui_shell_v2_acceptance.md`

- [ ] **Step 1: Extend prompt matrix**

Add V2 visible GUI rows:

- streaming Chinese answer.
- streaming English answer.
- safety refusal as assistant message.
- multiline Chinese persistence.
- Shift+Enter newline.
- structured token rejection GUI error.
- structured unknown route GUI error.
- bridge offline banner.
- tool trace row.
- permission approve/deny.
- browser panel degraded state.
- Computer Use panel safe unavailable state.
- settings panel opens.
- diagnostics panel copies safe diagnostic bundle.
- window restart restores latest V2 session.

- [ ] **Step 2: Add visible smoke script**

Create `visible-gui-smoke.ps1`:

- Starts backend.
- Starts desktop dev shell.
- Writes operator instructions for each visible check.
- Saves smoke log path.
- Does not claim pass automatically without visible confirmation.

- [ ] **Step 3: Update release gate**

`release-gate.ps1` must run:

- Python GUI V1 and V2 tests.
- Frontend lint.
- Frontend Vitest.
- Frontend production build.
- Visible GUI smoke preflight.
- Print Layer C trigger decision.

- [ ] **Step 4: Run release gate**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

Expected:

```text
Python GUI tests OK.
Frontend lint passed.
Frontend unit tests passed.
Frontend production build passed.
Layer A visible GUI smoke instructions generated.
Layer C trigger decision printed.
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add apps/desktop/scripts/release-gate.ps1 apps/desktop/scripts/visible-gui-smoke.ps1 apps/desktop/tests/gui-prompt-matrix.md docs/desktop_gui_shell_v2_acceptance.md
git commit -m "feat: add desktop gui v2 release gate"
```

### Task 15: V2 最终验收和归档

**Files:**
- Update: `learning_agent/test/desktop_gui_shell_v2/README.md`
- Update: `docs/desktop_gui_shell_architecture.md`
- Update: `agent_memory/progress.md`
- Update: `agent_memory/bugs.md`

- [ ] **Step 1: Run full Layer B**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

Expected:

```text
All automated V2 checks pass.
```

- [ ] **Step 2: Run full Layer A visible GUI acceptance**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-desktop-dev.ps1
```

Visible prompts:

```text
请分析当前项目是什么项目，并列出模块组成。
```

```text
请用三行中文说明这个 GUI 外壳现在能做什么。
第二行必须保留换行。
第三行说明如何重试。
```

```text
请执行一个需要权限确认的模拟工具动作，并让我在 GUI 里批准或拒绝。
```

```text
请开始一个较长任务，我会中途点击取消，然后再点击重试。
```

Expected:

```text
Visible Electron GUI shows streaming answer, multiline persistence, tool trace, permission flow, cancel, retry, diagnostics, and session resume.
```

- [ ] **Step 3: Decide Layer C trigger**

If any implementation task changed agent runtime, MCP routing, model call path, browser automation execution, Computer Use execution, or backend permission enforcement, run:

```powershell
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

Then type a realistic user prompt into the visible terminal and observe output.

If no such backend runtime behavior changed, record:

```text
Layer C not triggered: this V2 change modified GUI shell, bridge display contracts, diagnostics, release gate, or visual acceptance only.
```

- [ ] **Step 4: Archive evidence**

Create `learning_agent/test/desktop_gui_shell_v2/README.md` with:

- branch name.
- commit range.
- commands run.
- visible screenshot names.
- prompt matrix results.
- known limitations.
- Layer C trigger decision.

- [ ] **Step 5: Final commit**

Run:

```powershell
git add learning_agent/test/desktop_gui_shell_v2/README.md docs/desktop_gui_shell_architecture.md agent_memory/progress.md agent_memory/bugs.md
git commit -m "docs: record desktop gui v2 acceptance evidence"
```

## 10. 成功标准

V2 can be declared complete only when:

- All checked tasks in this plan are completed.
- `apps/desktop/tests/gui-prompt-matrix.md` has V2 rows checked with evidence links.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1` passes.
- Visible Electron GUI acceptance has been performed and archived.
- Layer C decision is explicitly recorded.
- No raw traceback, local secret path, or token appears in GUI error surfaces.
- There is no known failing test related to V2 scope.

## 11. Stop Conditions

Stop and report to the user before continuing if:

- The real agent adapter entry point cannot be identified from code after focused investigation.
- A V2 task requires modifying model account/OAuth behavior or using real credentials.
- Browser or Computer Use changes would perform real high-risk desktop actions without a visible permission gate.
- Electron cannot open a visible window in the current environment.
- Release gate failure points to an unrelated pre-existing broken area outside V2 scope.
- A design decision would force replacing V1 instead of evolving it.

## 12. Recommended Execution Mode

Use `superpowers:subagent-driven-development` for implementation because tasks are separable:

- One subagent per backend protocol/stream/adapter task.
- One subagent per frontend state/UI task.
- One review pass between backend and frontend integration.
- Main agent owns release gate, visible GUI acceptance, and final evidence archive.

Use inline execution only for small follow-up fixes or if subagents are unavailable.

## 13. First Three Commits To Make

1. `docs: add desktop gui shell v2 blueprint`
2. `feat: add desktop gui v2 protocol contract`
3. `feat: stream desktop gui v2 events`

This order gives the project a stable written target, a stable protocol, then a real-time event backbone. After that, the rest of the Codex-like shell becomes a set of visible panels and acceptance slices instead of a vague long task.
