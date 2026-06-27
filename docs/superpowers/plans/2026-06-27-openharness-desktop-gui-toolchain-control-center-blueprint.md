# OpenHarness Desktop GUI Toolchain Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 OpenHarness Desktop GUI 从“能聊天的 agent 壳”升级成接近 Codex 的成熟 agent GUI 产品，尽量复用现有 core、harness、browser、computer-use、MCP、planning、acceptance、memory 模块，减少重复代码和跑偏风险。

**Architecture:** 采用“薄 GUI adapter + 已有核心模块复用 + 事件流/状态快照优先”的架构。后端只新增少量 `learning_agent/app/gui_*` 适配模块，把现有 runtime 状态、工具目录、控制动作包装成稳定 HTTP/SSE contract；前端优先扩展已有 `StatusInspector`、`HarnessPanel`、`BrowserPanel`、`ComputerUsePanel` 和 `TracePanel`，只在确实需要产品化工作台时增加小组件。

**Tech Stack:** Python GUI bridge/runtime modules, OpenHarness `LearningAgent`, existing harness package, existing tool catalog/schema, existing browser automation MCP server, existing computer-use runtime, React/Electron desktop app, Vitest, PowerShell visible GUI smoke scripts, computer-use real GUI verification, systematic debugging.

---

## 0. 防跑偏总规则

这份蓝图是长任务执行时的“主链路”。每个实施者必须先读本节，再做任何代码修改。

**成功标准：**
- GUI 聊天主链路继续通过 `learning_agent/app/gui_harness_adapter.py` 和 `LearningAgent.run(...)` 使用真实核心 agent。
- 原有工具链路不重写，只做薄适配、状态展示、控制按钮、日志/证据可视化。
- 每一个新增 GUI 功能都必须能回答三个问题：复用了哪个已有模块、暴露了哪个稳定 contract、用户在真实 GUI 里能看到什么。
- 每一个阶段都必须有自动测试和肉眼可见真实 GUI 验收。
- 如果真实 GUI 验收发现 bug，必须使用 `superpowers:systematic-debugging` 找到根因、修复、重测，通过后才能进入下一任务。

**范围边界：**
- 本蓝图不改模型推理策略，不重写 `core/agent.py` 主循环。
- 本蓝图不重新实现 browser/computer-use/MCP/harness 的底层能力。
- 本蓝图不把所有工具都做成复杂专用页面；先用统一 toolchain control center 托住，再按高价值模块做专用面板。
- 本蓝图不为了“像 Codex”做视觉堆料；成熟度来自可控、可观测、可恢复、可验收。

**停止条件：**
- 发现现有模块 contract 与知识图谱判断不一致时，停止写代码，更新本蓝图的“事实差异”段落。
- 需要破坏现有 GUI 聊天主链路时，停止并汇报。
- 需要删除或替换大量已有 runtime 代码时，停止并汇报，因为这违背“尽量复用”原则。
- 真实 GUI 验收无法启动桌面应用时，停止功能推进，先按 systematic debugging 修启动链路。

**每个任务的固定执行循环：**
- [ ] 使用 CodeGraph 读取本任务涉及的符号和调用链。
- [ ] 确认可复用模块，不允许凭猜测新增平行实现。
- [ ] 写最小后端 contract 测试或前端组件测试。
- [ ] 实现薄 adapter 或薄 UI。
- [ ] 运行自动测试。
- [ ] 启动真实 Desktop GUI，用 computer-use 技能做肉眼可见验收。
- [ ] 如果发现 bug，使用 systematic debugging 修复并重测。
- [ ] 复制新写或修改代码到 `learning_agent/test/<task-name>/source_copies/`，满足项目学习归档规则。
- [ ] 更新 `agent_memory/progress.md`；如果发现风险，更新 `agent_memory/bugs.md`；如果形成可复用经验，更新 `agent_memory/experience.md`。
- [ ] 提交小粒度 commit。

---

## 1. 当前知识图谱结论

**已经接入或基本接入 GUI：**
- `learning_agent/app/gui_bridge.py` 已经提供 GUI HTTP/SSE 桥。
- `learning_agent/app/gui_harness_adapter.py` 已经通过 `LearningAgent.run(...)` 接入真实 agent 主循环。
- `apps/desktop/src/components/AppShell.tsx` 已经接入 sessions、events、runtime panels、provider settings、permission decision。
- `apps/desktop/src/components/TracePanel.tsx` 与 `ToolCallCard.tsx` 已能展示工具调用事件。
- `apps/desktop/src/components/HarnessPanel.tsx`、`BrowserPanel.tsx`、`ComputerUsePanel.tsx` 已存在，但目前更偏状态展示。
- Provider settings、OpenAI OAuth、自定义 provider、模型可见性和 test connection 已基本产品化。

**还没有充分产品化接入 GUI：**
- Harness 长任务真实控制：pause/resume/stop/create/checkpoint/restore/stage log。
- Computer Use 真实操作面：截图、观察、授权、目标应用、操作时间线、人工中止。
- Browser 自动化控制面：tabs、screenshot、console、network、downloads、replay、extension/CDP 配对。
- MCP 管理面：server list、resources、prompts、streams、tool schemas、health/errors。
- Planning/Todo/Subagent/Team：计划、任务、子 agent、peer message、worktree。
- Background command：命令列表、stdout/stderr tail、stop、exit code。
- Diagnostics/REPL/LSP：符号、定义、诊断、REPL output。
- Acceptance Controller：场景列表、运行、结果矩阵、截图/日志证据。
- Memory/Prompt/Token/Notebook：记忆、bugs/progress、prompt surface、token budget、notebook。

---

## 2. 文件结构策略

**后端优先复用：**
- Reuse: `learning_agent/app/gui_bridge.py`
- Reuse: `learning_agent/app/gui_harness_adapter.py`
- Reuse: `learning_agent/app/gui_protocol.py`
- Reuse: `learning_agent/app/gui_stream.py`
- Reuse: `learning_agent/harness/*.py`
- Reuse: `learning_agent/tools/catalog.py`
- Reuse: `learning_agent/tools/schemas.py`
- Reuse: `learning_agent/tools/tool_scope.py`
- Reuse: `learning_agent/browser_automation_mcp_server.py`
- Reuse: `learning_agent/computer_use_mcp_v2/windows_runtime/*.py`
- Reuse: `learning_agent/acceptance_controller/scenarios/*.json`

**后端建议新增薄模块：**
- Create: `learning_agent/app/gui_toolchain.py`
- Create: `learning_agent/app/gui_harness_controls.py`
- Create: `learning_agent/app/gui_computer_use.py`
- Create: `learning_agent/app/gui_browser_control.py`
- Create: `learning_agent/app/gui_mcp_control.py`
- Create: `learning_agent/app/gui_acceptance.py`
- Create: `learning_agent/app/gui_memory.py`

**前端优先复用：**
- Reuse: `apps/desktop/src/components/AppShell.tsx`
- Reuse: `apps/desktop/src/components/StatusInspector.tsx`
- Reuse: `apps/desktop/src/components/HarnessPanel.tsx`
- Reuse: `apps/desktop/src/components/BrowserPanel.tsx`
- Reuse: `apps/desktop/src/components/ComputerUsePanel.tsx`
- Reuse: `apps/desktop/src/components/TracePanel.tsx`
- Reuse: `apps/desktop/src/api/guiClient.ts`
- Reuse: `apps/desktop/src/api/guiTypes.ts`
- Reuse: `apps/desktop/src/styles/runtime-panels.css`

**前端建议新增薄组件：**
- Create: `apps/desktop/src/components/ToolchainPanel.tsx`
- Create: `apps/desktop/src/components/McpPanel.tsx`
- Create: `apps/desktop/src/components/CommandPanel.tsx`
- Create: `apps/desktop/src/components/PlanningPanel.tsx`
- Create: `apps/desktop/src/components/AcceptancePanel.tsx`
- Create: `apps/desktop/src/components/MemoryPanel.tsx`

**测试策略：**
- Frontend tests: `apps/desktop/tests/*.test.ts` and `apps/desktop/tests/*.test.tsx`
- Backend contract tests: implementation must first confirm the existing project test convention with `rg --files | rg '(^|[\\/])test'`; if no standard Python test directory exists, create focused tests under the current accepted project test location and mirror changed source into `learning_agent/test/<task-name>/source_copies/`.
- Visible GUI tests: `apps/desktop/scripts/visible-gui-smoke.ps1` plus computer-use skill observations.

---

## 3. 复用优先级矩阵

| 优先级 | 能力 | 已有模块 | GUI 缺口 | 最小接入方式 |
|---|---|---|---|---|
| P0 | Harness 控制 | `learning_agent/harness/*` | pause/resume unsupported | 新增 thin control adapter，扩展 `HarnessPanel` |
| P0 | Computer Use | `tool_scope.py`, `computer_use_mcp_v2` | 只有状态，无真实操作台 | 扩展 `ComputerUsePanel` 展示截图/授权/动作 |
| P1 | Browser | `browser_automation_mcp_server.py` | 只有 provider summary | 增加 tabs/console/network/replay 状态和基础动作 |
| P1 | MCP | MCP tools in `learning_agent/tools` | 无 server/resources/prompts 面 | 增加 MCP inventory/read-only explorer |
| P1 | Acceptance | `acceptance_controller` | 无 GUI dashboard | 场景列表 + run result + evidence viewer |
| P2 | Planning/Subagents | `todo_*`, `task_*`, `team_*` | 无计划/子 agent 面 | Toolchain panel 先展示，再做专用 panel |
| P2 | Background commands | `start/read/stop_background_command` | 无命令工作台 | 命令列表 + 输出 tail + stop |
| P2 | LSP/REPL | `lsp_*`, `repl` | 无代码诊断面 | 诊断列表 + REPL 输出 |
| P3 | Memory/Prompt/Token/Notebook | memory files, prompt/token tools, notebook tools | 无可视化 | 只读优先，编辑后置 |

---

## 4. Task 1: Toolchain Inventory Contract

**Purpose:** 先做统一工具链清单，防止每个面板各查各的、重复造数据结构。

**Files:**
- Create: `learning_agent/app/gui_toolchain.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/api/guiTypes.ts`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Create: `apps/desktop/src/components/ToolchainPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/styles/runtime-panels.css`
- Test: `apps/desktop/tests/toolchainPanel.test.tsx`
- Test: backend contract test path must be confirmed before implementation.

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "gui_bridge tool schemas builtin_tool_capability_pack StatusInspector runtime panels guiClient guiTypes"
```

Expected: output identifies `learning_agent/app/gui_bridge.py`, `learning_agent/tools/schemas.py`, `learning_agent/tools/catalog.py`, `apps/desktop/src/components/StatusInspector.tsx`, and existing runtime panel fetch flow.

- [ ] **Step 2: Define backend payload**

Add a read-only endpoint shaped like this:

```json
{
  "groups": [
    {
      "id": "computer_use",
      "label": "Computer Use",
      "status": "available",
      "tool_count": 20,
      "tools": [
        { "name": "screenshot", "category": "computer_use", "available": true }
      ]
    }
  ],
  "generated_at": "2026-06-27T00:00:00Z"
}
```

Expected: payload is generated from existing tool schema/catalog data, not hard-coded one tool at a time.

- [ ] **Step 3: Add frontend Toolchain tab**

Add a `tools` or `toolchain` view in `StatusInspector` that renders grouped tool names, availability, and “已复用模块” labels.

Expected: user can visually see which existing capabilities are connected and which are only available through agent calls.

- [ ] **Step 4: Run tests**

Run:

```powershell
npm --prefix apps/desktop run test -- toolchainPanel
npm --prefix apps/desktop run lint
```

Expected: Vitest passes and TypeScript lint passes.

- [ ] **Step 5: Visible GUI acceptance**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File apps/desktop/scripts/visible-gui-smoke.ps1
```

Then use computer-use skill to confirm the Desktop GUI shows the new Toolchain tab and grouped capabilities.

Expected: a real visible GUI window shows Toolchain inventory; no blank panel; text does not overlap.

- [ ] **Step 6: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: expose desktop gui toolchain inventory"
```

Expected: one focused commit.

---

## 5. Task 2: Harness Real Controls

**Purpose:** 把已有 `HarnessPanel` 从状态面板升级为真实长任务控制台。

**Files:**
- Create: `learning_agent/app/gui_harness_controls.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/components/HarnessPanel.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/harnessPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "HarnessRunner HarnessQueue HarnessStore render_harness_status build_gui_harness_status_payload build_gui_harness_control_payload HarnessPanel"
```

Expected: output identifies existing harness status/control placeholders and runner/store/queue modules.

- [ ] **Step 2: Replace unsupported placeholder with real capability detection**

Backend `controls` must report:

```json
{
  "pause_supported": true,
  "resume_supported": true,
  "stop_supported": true,
  "checkpoint_supported": true,
  "restore_supported": false
}
```

Expected: false is allowed only when the existing harness module truly lacks that operation.

- [ ] **Step 3: Add control actions**

Expose minimal endpoints:

```text
POST /v2/gui/harness/pause
POST /v2/gui/harness/resume
POST /v2/gui/harness/stop
POST /v2/gui/harness/checkpoint
```

Expected: endpoints call existing harness queue/store/runner APIs or safe adapter functions; they must not spawn a parallel harness implementation.

- [ ] **Step 4: Extend `HarnessPanel`**

Show active goal, queue, checkpoints, pause/resume/stop/checkpoint buttons, and latest control result.

Expected: unsupported buttons are hidden or disabled with a clear reason.

- [ ] **Step 5: Run tests**

Run:

```powershell
npm --prefix apps/desktop run test -- harnessPanel
npm --prefix apps/desktop run lint
```

Expected: tests pass.

- [ ] **Step 6: Visible GUI acceptance**

Run visible GUI smoke and use computer-use to verify:
- Harness tab exists.
- Pause/resume/stop/checkpoint controls are visible when supported.
- Clicking a control changes the panel state or shows a safe backend message.

If any click fails or state is inconsistent, use `superpowers:systematic-debugging` before continuing.

- [ ] **Step 7: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: connect desktop harness controls"
```

Expected: one focused commit.

---

## 6. Task 3: Computer Use Workbench

**Purpose:** 把 Computer Use 从“状态摘要”升级成用户能看见、能授权、能中止、能验收的真实操作面。

**Files:**
- Create: `learning_agent/app/gui_computer_use.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/components/ComputerUsePanel.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/computerUsePanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "ComputerUsePanel build_gui_computer_use payload COMPUTER_USE_OPERATION_RAW_TOOL_NAMES ComputerUseModeSessionStore status read_last_observation read_last_action_result assert_last_action"
```

Expected: output shows existing computer-use status and raw operation tool names.

- [ ] **Step 2: Add read-only workbench payload**

Backend payload must include:

```json
{
  "mode": "off",
  "permission_mode": "manual",
  "allowed_action_classes": [],
  "last_observation": null,
  "last_action_result": null,
  "abort_available": true,
  "degraded": false,
  "safe_error": ""
}
```

Expected: payload reads existing computer-use runtime state and last observation/result when available.

- [ ] **Step 3: Add safe actions**

Expose minimal endpoints:

```text
POST /v2/gui/computer-use/request-access
POST /v2/gui/computer-use/abort
POST /v2/gui/computer-use/observe
```

Expected: endpoints reuse existing permission/runtime calls. They must not perform unsafe desktop actions without existing permission policy.

- [ ] **Step 4: Extend `ComputerUsePanel`**

Show mode, permission, target/app state, last observation summary, last action result, request access, observe, abort.

Expected: panel makes the real desktop-control state obvious to a non-expert user.

- [ ] **Step 5: Run tests**

Run:

```powershell
npm --prefix apps/desktop run test -- computerUsePanel
npm --prefix apps/desktop run lint
```

Expected: tests pass.

- [ ] **Step 6: Visible GUI acceptance**

Use computer-use skill to verify the real GUI:
- Computer Use tab is visible.
- Request/observe/abort controls render.
- Safe error/degraded state is readable.
- No action occurs without a visible permission path.

If behavior differs, use systematic debugging.

- [ ] **Step 7: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop computer use workbench"
```

Expected: one focused commit.

---

## 7. Task 4: Browser Automation Workbench

**Purpose:** 把 browser automation 从 provider 状态变成可观察、可排查的浏览器工作台。

**Files:**
- Create: `learning_agent/app/gui_browser_control.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/components/BrowserPanel.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/browserPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "BrowserPanel browser_automation_mcp_server browser_open browser_tabs browser_console browser_network browser_downloads browser_replay build_gui_browser_providers_payload"
```

Expected: output identifies provider status and browser MCP tools.

- [ ] **Step 2: Add browser workbench payload**

Payload must include provider status, tabs summary, latest console/network summary, downloads summary, replay availability, and safe error.

Expected: data comes from existing browser automation server/provider router where available.

- [ ] **Step 3: Add minimal safe actions**

Expose:

```text
POST /v2/gui/browser/open
POST /v2/gui/browser/refresh-status
GET  /v2/gui/browser/tabs
GET  /v2/gui/browser/console
GET  /v2/gui/browser/network
```

Expected: write actions are limited and respect existing browser permission policy.

- [ ] **Step 4: Extend `BrowserPanel`**

Show providers, active tab, tab count, console errors, network errors, replay/download summaries.

Expected: user can diagnose “browser tool链路为什么没动” without opening logs.

- [ ] **Step 5: Run tests**

Run:

```powershell
npm --prefix apps/desktop run test -- browserPanel
npm --prefix apps/desktop run lint
```

Expected: tests pass.

- [ ] **Step 6: Visible GUI acceptance**

Use real GUI and computer-use to confirm Browser tab renders provider status and workbench sections.

If browser provider is unavailable, panel must show unavailable reason instead of crashing.

- [ ] **Step 7: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop browser automation workbench"
```

Expected: one focused commit.

---

## 8. Task 5: MCP Management Panel

**Purpose:** 让 GUI 能看见 MCP server、resource、prompt、stream 的接入状态。

**Files:**
- Create: `learning_agent/app/gui_mcp_control.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `apps/desktop/src/components/McpPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/mcpPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "MCP list_mcp_resources read_mcp_resource list_mcp_prompts read_mcp_prompt listen_mcp_stream load_mcp_server_configs McpToolRegistry"
```

Expected: output identifies existing MCP config/registry/tools.

- [ ] **Step 2: Add read-only MCP inventory**

Expose:

```text
GET /v2/gui/mcp/servers
GET /v2/gui/mcp/resources
GET /v2/gui/mcp/prompts
```

Expected: endpoints never leak secrets and return safe errors per server.

- [ ] **Step 3: Add `McpPanel`**

Show server name, status, resource count, prompt count, last error.

Expected: user can see whether MCP is configured and which servers are failing.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- mcpPanel
npm --prefix apps/desktop run lint
```

Then verify in real GUI.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop mcp management panel"
```

Expected: one focused commit.

---

## 9. Task 6: Planning, Todo, Subagent, Team Panel

**Purpose:** 把 core 里的计划和多 agent 协作能力露出给 GUI，而不是只靠聊天文本。

**Files:**
- Modify: `learning_agent/app/gui_toolchain.py`
- Create: `apps/desktop/src/components/PlanningPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/planningPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "todo_read todo_write task_list task_get task_update team_create team_start_task send_message list_peers read_peer_messages enter_plan_mode exit_plan_mode verify_plan_execution"
```

Expected: output identifies existing planning/delegation tools.

- [ ] **Step 2: Add planning inventory payload**

Payload must show which planning/delegation tools are available, current todo count if readable, active task count if readable, and safe unavailable reasons.

Expected: read-only first; mutation buttons are added only after read path is stable.

- [ ] **Step 3: Add `PlanningPanel`**

Show todos, tasks, teams, peer messages as sections. Empty states must explain “暂无数据” rather than implying broken runtime.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- planningPanel
npm --prefix apps/desktop run lint
```

Then verify in real GUI.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: surface planning and subagent state in desktop gui"
```

Expected: one focused commit.

---

## 10. Task 7: Background Command Console

**Purpose:** 让 GUI 能看见后台命令，尤其是长任务执行时的终端输出和停止控制。

**Files:**
- Create: `learning_agent/app/gui_execution.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `apps/desktop/src/components/CommandPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/commandPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "start_background_command read_background_command stop_background_command event_tail run_status task_status"
```

Expected: output identifies existing background command tools and status/reporting tools.

- [ ] **Step 2: Add command inventory**

Expose:

```text
GET  /v2/gui/commands
GET  /v2/gui/commands/{id}/tail
POST /v2/gui/commands/{id}/stop
```

Expected: endpoints map to existing background command state where available.

- [ ] **Step 3: Add `CommandPanel`**

Show command id, command text, status, last output lines, exit code, stop button.

Expected: user can tell whether a long-running command is still alive.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- commandPanel
npm --prefix apps/desktop run lint
```

Then verify in real GUI.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop background command console"
```

Expected: one focused commit.

---

## 11. Task 8: Acceptance Controller Dashboard

**Purpose:** 把已有验收场景变成 GUI 内可运行、可看证据的 dashboard，支撑“真实 GUI 验收强制门禁”。

**Files:**
- Create: `learning_agent/app/gui_acceptance.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `apps/desktop/src/components/AcceptancePanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/acceptancePanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "acceptance_controller scenarios controller.ps1 result.json events.jsonl visible terminal final_acceptance_matrix"
```

Expected: output identifies scenario files, run artifacts, and controller entry points.

- [ ] **Step 2: Add scenario inventory**

Expose:

```text
GET  /v2/gui/acceptance/scenarios
GET  /v2/gui/acceptance/runs
POST /v2/gui/acceptance/run
```

Expected: scenario list is read from `learning_agent/acceptance_controller/scenarios`.

- [ ] **Step 3: Add `AcceptancePanel`**

Show scenario name, category, last result, last run time, evidence links, run button.

Expected: a non-expert user can see what has been tested and what failed.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- acceptancePanel
npm --prefix apps/desktop run lint
```

Then use computer-use to verify real GUI dashboard and at least one safe smoke scenario listing.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop acceptance dashboard"
```

Expected: one focused commit.

---

## 12. Task 9: Diagnostics, LSP, REPL Panel

**Purpose:** 让 GUI 具备 Codex 类产品必须有的开发者可观测性。

**Files:**
- Modify: `learning_agent/app/gui_diagnostics.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `apps/desktop/src/components/DiagnosticsPanel.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/diagnosticsPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "gui_diagnostics DiagnosticsPanel lsp_symbols lsp_definition lsp_diagnostics repl health_status read_trace compact_status resume_report"
```

Expected: output identifies existing diagnostics and LSP/REPL tools.

- [ ] **Step 2: Add diagnostics payload**

Payload must include health, trace summary, compact status, resume report summary, LSP diagnostics summary, and REPL availability.

Expected: no secrets, no huge log blobs; use summaries and links/ids.

- [ ] **Step 3: Extend `DiagnosticsPanel`**

Show health, traces, LSP diagnostics, REPL status, compact/resume state.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- diagnosticsPanel
npm --prefix apps/desktop run lint
```

Then verify in real GUI.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: expand desktop diagnostics panel"
```

Expected: one focused commit.

---

## 13. Task 10: Memory, Prompt, Token, Notebook Panel

**Purpose:** 把长期任务不跑偏所需的上下文、进度、风险、token 状态放到 GUI 可见位置。

**Files:**
- Create: `learning_agent/app/gui_memory.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Create: `apps/desktop/src/components/MemoryPanel.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Test: `apps/desktop/tests/memoryPanel.test.tsx`

- [ ] **Step 1: CodeGraph exploration**

Run:

```powershell
codegraph explore "append_memory prompt_surface_report token_budget_report notebook_read notebook_edit agent_memory context progress bugs"
```

Expected: output identifies memory/prompt/token/notebook tool surfaces and project memory files.

- [ ] **Step 2: Add read-only memory payload**

Expose:

```text
GET /v2/gui/memory/summary
GET /v2/gui/prompt/status
GET /v2/gui/notebook/status
```

Expected: read-only first. Editing memory or notebook is not part of the first pass.

- [ ] **Step 3: Add `MemoryPanel`**

Show context/progress/bugs summaries, prompt surface status, token budget status, notebook availability.

Expected: user can see why the agent is making current decisions and whether context is close to compaction.

- [ ] **Step 4: Run tests and visible GUI acceptance**

Run:

```powershell
npm --prefix apps/desktop run test -- memoryPanel
npm --prefix apps/desktop run lint
```

Then verify in real GUI.

- [ ] **Step 5: Commit**

Run:

```powershell
git add learning_agent/app apps/desktop/src apps/desktop/tests learning_agent/test agent_memory
git commit -m "feat: add desktop memory and token status panel"
```

Expected: one focused commit.

---

## 14. Final Integration Gate

**Purpose:** 所有面板接入后，做一次类似 Codex 产品级的总验收。

- [ ] **Step 1: Run frontend unit and type gates**

Run:

```powershell
npm --prefix apps/desktop run test
npm --prefix apps/desktop run lint
npm --prefix apps/desktop run build
```

Expected: all pass.

- [ ] **Step 2: Run backend contract gates**

Run the backend contract tests selected by the implementation tasks.

Expected: all GUI adapter payload tests pass.

- [ ] **Step 3: Run visible GUI smoke**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File apps/desktop/scripts/visible-gui-smoke.ps1
```

Expected: desktop app opens and major tabs render.

- [ ] **Step 4: Computer-use visual verification**

Use computer-use skill to inspect the real Desktop GUI and confirm:
- Chat still works.
- Toolchain inventory is visible.
- Harness controls are visible and safe.
- Computer Use workbench is visible.
- Browser workbench is visible.
- MCP panel is visible.
- Acceptance panel is visible.
- Diagnostics and Memory panels are visible.
- No major text overlap or blank panel.

- [ ] **Step 5: Systematic debugging gate**

If any final gate fails, use `superpowers:systematic-debugging`.

Required debugging rule:
- Reproduce the failure.
- Collect evidence.
- Identify root cause.
- Fix the smallest responsible code path.
- Re-run the failed automatic test.
- Re-run visible GUI acceptance.
- Only then mark the task complete.

- [ ] **Step 6: Final commit**

Run:

```powershell
git status --short
git add learning_agent apps/desktop docs/superpowers/plans agent_memory
git commit -m "feat: mature desktop gui toolchain control center"
```

Expected: final integration commit only if previous task commits were not already sufficient.

---

## 15. Recommended Execution Order

执行顺序必须保持：

1. Toolchain Inventory Contract
2. Harness Real Controls
3. Computer Use Workbench
4. Browser Automation Workbench
5. MCP Management Panel
6. Planning/Todo/Subagent/Team Panel
7. Background Command Console
8. Acceptance Controller Dashboard
9. Diagnostics/LSP/REPL Panel
10. Memory/Prompt/Token/Notebook Panel
11. Final Integration Gate

理由：
- Toolchain inventory 是全局地图，先做能减少后续重复代码。
- Harness 是长任务骨架，必须先补控制能力。
- Computer Use 和 Browser 是用户肉眼可见的“手”和“眼”。
- MCP、Planning、Command、Acceptance 是成熟 agent 的工具链管理层。
- Diagnostics 和 Memory 是长任务不跑偏的可观测性层。

---

## 16. Self-Review Checklist

**Spec coverage:**
- 已覆盖用户要求的“根据知识图谱识别未接 GUI 的模块”。
- 已覆盖“尽量复用原来文件或代码，减少代码量”。
- 已覆盖“最终目标是 Codex 一样成熟的 GUI 产品”。
- 已覆盖“防止长任务跑偏”的成功标准、范围边界、停止条件和验收方式。
- 已覆盖“真实 GUI 肉眼验收 + computer-use + systematic debugging”的强制门禁。

**Placeholder scan:**
- 本蓝图没有使用会让执行者停下猜测的占位说明。
- 每个任务都有明确文件、命令、验收预期和 commit 建议。

**Type and contract consistency:**
- 后端统一使用 `/v2/gui/*` 命名，延续当前 GUI bridge 风格。
- 前端统一从 `guiClient.ts` 和 `guiTypes.ts` 增加 contract，避免组件直接散落 fetch。
- 面板统一挂到 `StatusInspector.tsx`，保持现有右侧工作台结构。
