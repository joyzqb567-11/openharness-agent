# OpenHarness Desktop Real Model Latency V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 OpenHarness Desktop 的真实模型链路从“约 2 分钟空白等待 + fake streaming”升级为“2 秒内可见阶段、可取消、可诊断、可度量，并在经过验证的流式链路上显示真实 token”。

**Architecture:** 先把当前真实调用链路变成可观察系统：固化 baseline、定义有限状态机事件、让后端 adapter 在模型调用期间持续发 phase，再让前端显示这些 phase。随后按证据推进：先实现真实取消和 Codex CLI 可观测 runner，再做异步诊断、模型快速失败，最后把 Direct ChatGPT OAuth SSE 作为 gated fast path，而不是默认承诺。

**Tech Stack:** Python backend (`learning_agent/app`, `learning_agent/models`), pytest, Electron + React + TypeScript (`apps/desktop`), visible OpenHarness Desktop GUI acceptance, Codex CLI / ChatGPT OAuth diagnostics.

---

## Why This Plan Exists

当前慢点已经定位到真实模型调用阶段，而不是前端输入或 bridge 排队：

```text
gui_turn_queued -> turn_started: same second
turn_started -> first message_delta: about 122-128 seconds
```

已知事实：

- `CodexCliChatModel._run_codex_process()` 使用 `subprocess.run(...)`，会阻塞到 Codex CLI 子进程完整结束。
- `RealModelGuiAgentAdapter.run()` 等 `model.chat(...)` 完整返回后，才把最终文本拆成 chunk 发给 GUI。
- 当前 GUI 里的 streaming 是 fake streaming，不是真实 token streaming。
- `codex doctor` 显示 ChatGPT OAuth WebSocket handshake timeout，随后 HTTPS fallback。

V2 的核心不是“假装模型变快”，而是先消灭用户看见的空白等待：

```text
instrument -> visible status -> real cancellation -> observable CLI -> gated SSE fast path
```

## Scope

### In Scope

- 固化 baseline latency measurement，避免凭感觉判断是否变快。
- 新增统一 `ModelStreamEvent` 和有限 phase enum。
- 后端真实模型 adapter 支持可见 phase events。
- 前端 Composer / Status Inspector 显示模型调用阶段、耗时、模型、provider。
- 取消按钮必须真正停止后端工作，而不只是 UI 变成已取消。
- Codex CLI 先做 event shape discovery，再实现 observable runner。
- `codex doctor` / transport diagnostics 必须异步缓存，不能阻塞发送。
- Direct OAuth SSE 只作为 gated experimental fast path；probe 通过才实现真实 SSE streaming。
- 增加 secret redaction 自动门禁。
- 真实可见 GUI 验收必须记录 first status、first delta、completion、cancel 指标。

### Non-Goals

- 不绕过 OpenAI/ChatGPT 官方 OAuth 安全流程。
- 不复制 OpenCode client id 或私有 client secret 到 OpenHarness。
- 不把 OAuth token、authorization code、refresh token、cookie 写入日志、事件或截图证据。
- 不承诺 Codex CLI WebSocket timeout 时所有回答都能几秒完成。
- 不把未验证的 Codex CLI 配置项当作解决方案。
- 不再把 fake streaming 叫作真实 streaming。

## File Structure

```text
learning_agent/
  app/
    gui_agent_adapter.py
    gui_bridge.py
    gui_model_latency_diagnostics.py
  models/
    adapters.py
    streaming.py
    codex_cli_stream.py
  tests/
    test_gui_real_model_latency_baseline.py
    test_streaming_chat_model_protocol.py
    test_gui_real_model_latency_events.py
    test_codex_cli_event_shape_discovery.py
    test_codex_cli_streaming_model.py
    test_gui_model_latency_diagnostics.py
    test_codex_oauth_streaming_probe.py
    test_gui_model_latency_secret_redaction.py

apps/desktop/
  src/
    api/guiClient.ts
    api/guiProviderTypes.ts
    components/Composer.tsx
    components/ModelCallStatus.tsx
    components/StatusInspector.tsx
    state/providerSettingsStore.ts
    styles/layout.css
  tests/
    realModelLatencyEvents.test.ts
    modelCallStatus.test.tsx
    composer.test.ts

learning_agent/test/
  real_model_latency_v2_20260626/
    baseline/
      current_latency_events.json
      current_latency_summary.md
    codex_cli_discovery/
      sanitized_stdout.jsonl
      sanitized_stderr.txt
      event_shape.md
    visible_evidence/
      README.md
    implementation-notes.md
```

## Event Contract

Every backend model phase event must carry enough information to reject stale updates after cancellation.

```python
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Protocol

ModelStreamEventType = Literal["status", "delta", "error", "completed", "metrics"]
ModelStreamPhase = Literal[
    "queued",
    "started",
    "connecting",
    "auth_checking",
    "websocket_connecting",
    "websocket_timeout",
    "https_fallback",
    "streaming",
    "first_delta",
    "completed",
    "cancel_requested",
    "cancelled",
    "failed",
]

@dataclass(frozen=True)
class ModelStreamEvent:
    event_type: ModelStreamEventType
    phase: ModelStreamPhase
    message: str
    timestamp: float
    elapsed_ms: int
    sequence: int
    turn_id: str
    provider_id: str
    model_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

class StreamingChatModel(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        turn_id: str,
        provider_id: str,
        model_id: str,
    ) -> Iterable[ModelStreamEvent]:
        ...
```

Security rule:

```text
metadata may include phase, elapsed_ms, transport, provider_id, model_id, command_kind.
metadata must not include access_token, refresh_token, id_token, authorization_code, cookie, api_key, bearer, or raw callback URL.
```

## Success Metrics

- [x] `first_status_ms <= 2000` for every real-model turn.
- [x] `first_transport_warning_ms <= 30000` when WebSocket timeout occurs.
- [x] `first_delta_ms` is measured separately and never conflated with `first_status_ms`.
- [x] `cancel_visible_ms <= 500`.
- [x] `cancel_backend_stop_ms <= 3000` for Codex CLI child process under normal Windows process termination.
- [x] Stale delta from a cancelled turn never appears in a later turn.
- [x] Direct OAuth SSE only claims low-latency streaming after probe evidence confirms the endpoint and payload shape.
- [x] Secret redaction gate passes on all V2 evidence directories.
- [x] Real visible GUI acceptance passes using `computer-use:computer-use` to confirm and verify the visible OpenHarness Desktop window.

## Task 0: Baseline Latency Measurement

**Files:**

- Create: `learning_agent/tests/test_gui_real_model_latency_baseline.py`
- Create: `learning_agent/test/real_model_latency_v2_20260626/baseline/current_latency_summary.md`
- Create: `learning_agent/test/real_model_latency_v2_20260626/baseline/current_latency_events.json`

- [x] **Step 1: Write the baseline event parser test**

```python
def test_latency_summary_separates_queue_start_status_delta_and_completion():
    events = [
        {"type": "gui_turn_queued", "turn_id": "turn_a", "ts": "2026-06-26T13:30:31Z"},
        {"type": "turn_started", "turn_id": "turn_a", "ts": "2026-06-26T13:30:31Z"},
        {"type": "model_call_status", "turn_id": "turn_a", "phase": "connecting", "ts": "2026-06-26T13:30:32Z"},
        {"type": "message_delta", "turn_id": "turn_a", "ts": "2026-06-26T13:32:34Z"},
        {"type": "gui_turn_completed", "turn_id": "turn_a", "ts": "2026-06-26T13:32:35Z"},
    ]

    summary = summarize_latency_events(events)

    assert summary["queued_to_started_ms"] == 0
    assert summary["started_to_first_status_ms"] == 1000
    assert summary["started_to_first_delta_ms"] == 123000
    assert summary["started_to_completed_ms"] == 124000
```

- [x] **Step 2: Implement `summarize_latency_events()` inside the test file first**

```python
from datetime import datetime, timezone

def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def _ms(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() * 1000)

def summarize_latency_events(events: list[dict[str, object]]) -> dict[str, int]:
    by_type = {str(event["type"]): event for event in events}
    started = _parse_ts(str(by_type["turn_started"]["ts"]))
    queued = _parse_ts(str(by_type["gui_turn_queued"]["ts"]))
    status = _parse_ts(str(by_type["model_call_status"]["ts"]))
    delta = _parse_ts(str(by_type["message_delta"]["ts"]))
    completed = _parse_ts(str(by_type["gui_turn_completed"]["ts"]))
    return {
        "queued_to_started_ms": _ms(queued, started),
        "started_to_first_status_ms": _ms(started, status),
        "started_to_first_delta_ms": _ms(started, delta),
        "started_to_completed_ms": _ms(started, completed),
    }
```

- [x] **Step 3: Run the baseline parser test**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_latency_baseline.py -q
```

Expected:

```text
1 passed
```

- [x] **Step 4: Capture current GUI event evidence**

Use the existing GUI events endpoint or local event log to save a sanitized baseline sample:

```powershell
New-Item -ItemType Directory -Force -Path learning_agent/test/real_model_latency_v2_20260626/baseline
```

Expected:

```text
Directory exists: learning_agent/test/real_model_latency_v2_20260626/baseline
```

- [x] **Step 5: Write the current baseline summary**

`current_latency_summary.md` must contain:

```text
Prompt:
Selected provider:
Selected model:
queued_to_started_ms:
started_to_first_status_ms:
started_to_first_delta_ms:
started_to_completed_ms:
transport_warning_count:
Observed issue:
```

## Task 1: Streaming Event Contract

**Files:**

- Create: `learning_agent/models/streaming.py`
- Create: `learning_agent/tests/test_streaming_chat_model_protocol.py`

- [x] **Step 1: Write tests for phase, sequence, and redaction shape**

```python
from learning_agent.models.streaming import ModelStreamEvent

def test_model_stream_event_requires_phase_sequence_and_turn_context():
    event = ModelStreamEvent(
        event_type="status",
        phase="connecting",
        message="正在连接 GPT-5.5",
        timestamp=1.0,
        elapsed_ms=12,
        sequence=1,
        turn_id="turn_1",
        provider_id="openai",
        model_id="gpt-5.5",
        metadata={"transport": "codex_cli"},
    )

    assert event.phase == "connecting"
    assert event.sequence == 1
    assert event.turn_id == "turn_1"
```

- [x] **Step 2: Implement `ModelStreamEvent` and `StreamingChatModel`**

Use the exact Event Contract schema from the `Event Contract` section above.

- [x] **Step 3: Run tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_streaming_chat_model_protocol.py -q
```

Expected:

```text
1 passed
```

## Task 2: Backend Adapter Emits Real Phases

**Files:**

- Modify: `learning_agent/app/gui_agent_adapter.py`
- Test: `learning_agent/tests/test_gui_real_model_latency_events.py`

- [x] **Step 1: Add a fake streaming model test**

```python
class FakeStreamingModel:
    def stream_chat(self, messages, tools, *, turn_id, provider_id, model_id):
        yield ModelStreamEvent("status", "connecting", "正在连接测试模型", 1.0, 5, 1, turn_id, provider_id, model_id)
        yield ModelStreamEvent("delta", "streaming", "你好", 2.0, 15, 2, turn_id, provider_id, model_id)
        yield ModelStreamEvent("completed", "completed", "", 3.0, 20, 3, turn_id, provider_id, model_id)
```

Expected event order:

```text
turn_started
model_call_started
model_call_status phase=connecting
model_first_delta
message_delta
message_completed
model_call_completed
gui_turn_completed
```

- [x] **Step 2: Update `RealModelGuiAgentAdapter.run()`**

Required behavior:

```text
If model has stream_chat:
  emit model_call_started
  iterate stream events
  convert status -> model_call_status
  convert first delta -> model_first_delta + message_delta
  convert later delta -> message_delta
  convert completed -> message_completed + model_call_completed
  convert error -> model_call_failed + failed turn

If model only has chat:
  emit model_call_started
  emit model_call_status phase=connecting message="当前模型适配器仍是阻塞式调用"
  call chat()
  emit final text as compatibility delta
```

- [x] **Step 3: Reject stale events**

Adapter must ignore any stream event whose `turn_id` does not equal the active request turn id.

- [x] **Step 4: Run backend event tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_latency_events.py -q
```

Expected:

```text
All tests passed
```

## Task 3: Frontend Visible Model Status

**Files:**

- Modify: `apps/desktop/src/api/guiClient.ts`
- Modify: `apps/desktop/src/api/guiProviderTypes.ts`
- Modify: `apps/desktop/src/components/Composer.tsx`
- Create: `apps/desktop/src/components/ModelCallStatus.tsx`
- Modify: `apps/desktop/src/components/StatusInspector.tsx`
- Modify: `apps/desktop/src/styles/layout.css`
- Test: `apps/desktop/tests/realModelLatencyEvents.test.ts`
- Test: `apps/desktop/tests/modelCallStatus.test.tsx`

- [x] **Step 1: Add frontend event types**

The GUI client must recognize:

```ts
type ModelCallPhase =
  | "queued"
  | "started"
  | "connecting"
  | "auth_checking"
  | "websocket_connecting"
  | "websocket_timeout"
  | "https_fallback"
  | "streaming"
  | "first_delta"
  | "completed"
  | "cancel_requested"
  | "cancelled"
  | "failed";
```

- [x] **Step 2: Add `ModelCallStatus`**

The component must show compact, non-marketing status text:

```text
正在连接 GPT-5.5
WebSocket 超时，正在切换 HTTPS
已收到首个响应
已取消
调用失败：当前模型不可用
```

- [x] **Step 3: Keep composer stable**

The status row must not resize the composer or push the send button. Use a fixed-height status line and ellipsis for long text.

- [x] **Step 4: Run frontend tests**

Run:

```powershell
npm --prefix apps/desktop test -- realModelLatencyEvents.test.ts modelCallStatus.test.tsx
```

Expected:

```text
Test Files 2 passed
```

## Task 4: Real Cancellation

**Files:**

- Modify: `learning_agent/app/gui_agent_adapter.py`
- Modify: `learning_agent/models/codex_cli_stream.py`
- Modify: `apps/desktop/src/components/Composer.tsx`
- Test: `learning_agent/tests/test_gui_real_model_latency_events.py`
- Test: `learning_agent/tests/test_codex_cli_streaming_model.py`
- Test: `apps/desktop/tests/realModelLatencyEvents.test.ts`

- [x] **Step 1: Add cancellation race tests**

Tests must cover:

```text
turn A cancelled -> late delta from turn A ignored
turn A cancelled -> turn B can stream normally
cancel called twice -> no crash
process already exited -> cancel no-op succeeds
frontend cancel -> visible cancelled state within 500ms
```

- [x] **Step 2: Define Windows process behavior**

Codex CLI runner must:

```text
start child process with its own process group when supported
on cancel: emit cancel_requested
try soft terminate
wait up to 3 seconds
kill process if still alive
drain stdout/stderr queues
emit cancelled
ignore late stdout/stderr lines after cancelled
```

- [x] **Step 3: Wire frontend cancel to backend cancel**

The Composer cancel button must send the existing turn id to the backend cancel endpoint and optimistically display `cancel_requested`.

- [x] **Step 4: Run cancellation tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_latency_events.py learning_agent/tests/test_codex_cli_streaming_model.py -q
npm --prefix apps/desktop test -- realModelLatencyEvents.test.ts
```

Expected:

```text
All selected tests passed
```

## Task 5: Codex CLI Event Shape Discovery

**Files:**

- Create: `learning_agent/tests/test_codex_cli_event_shape_discovery.py`
- Create: `learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/sanitized_stdout.jsonl`
- Create: `learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/sanitized_stderr.txt`
- Create: `learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/event_shape.md`

- [x] **Step 1: Run a minimal real discovery command**

Command:

```powershell
codex exec --json --skip-git-repo-check --sandbox read-only --model gpt-5.5 "请只回复：pong"
```

Save sanitized stdout/stderr. Remove tokens, callback URLs, cookies, email addresses, and absolute temp token paths.

- [x] **Step 2: Write `event_shape.md`**

The file must answer:

```text
Does stdout contain JSONL?
Does stdout contain token deltas?
Does stderr contain transport warnings?
Where does final answer appear?
Can OpenHarness show real token streaming from Codex CLI?
Can OpenHarness at least show transport status from Codex CLI?
```

- [x] **Step 3: Add test that event shape document exists and is explicit**

```python
from pathlib import Path

def test_codex_cli_event_shape_document_records_delta_capability():
    text = Path("learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/event_shape.md").read_text(encoding="utf-8")
    assert "Does stdout contain token deltas:" in text
    assert "Can OpenHarness show real token streaming from Codex CLI:" in text
```

- [x] **Step 4: Run discovery documentation test**

Run:

```powershell
python -m pytest learning_agent/tests/test_codex_cli_event_shape_discovery.py -q
```

Expected:

```text
1 passed
```

## Task 6: Observable Codex CLI Runner

**Files:**

- Modify: `learning_agent/models/adapters.py`
- Create: `learning_agent/models/codex_cli_stream.py`
- Test: `learning_agent/tests/test_codex_cli_streaming_model.py`

- [x] **Step 1: Write fake process tests**

Required fake cases:

```text
stderr "Responses WebSocket timed out" -> phase websocket_timeout
stderr "Falling back from WebSockets to HTTPS transport" -> phase https_fallback
stdout JSONL delta if discovery says deltas exist -> event_type delta
stdout no delta if discovery says no deltas -> final output file still parsed
non-zero exit -> error event
cancel -> process terminated and cancelled event emitted
```

- [x] **Step 2: Implement `CodexCliStreamingRunner`**

Runner must use `subprocess.Popen`, not `subprocess.run`, and must never block waiting for final completion before emitting status events.

- [x] **Step 3: Keep `CodexCliChatModel.chat()` compatible**

Existing `chat()` callers must still work by collecting `stream_chat()` output into a final `ModelMessage`.

- [x] **Step 4: Run tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_codex_cli_streaming_model.py -q
```

Expected:

```text
All tests passed
```

## Task 7: Async Transport Diagnostics Cache

**Files:**

- Create: `learning_agent/app/gui_model_latency_diagnostics.py`
- Test: `learning_agent/tests/test_gui_model_latency_diagnostics.py`

- [x] **Step 1: Add diagnostics parser tests**

Inputs:

```text
Responses WebSocket timed out
HTTPS fallback may still work
https://chatgpt.com/backend-api/ reachable
```

Expected parsed result:

```python
{
    "websocket_ok": False,
    "http_reachable": True,
    "expected_slow_fallback": True,
}
```

- [x] **Step 2: Implement async cache behavior**

Rules:

```text
diagnostics never run synchronously inside send-message request
cache TTL is 5 minutes
expired cache returns last known value and starts background refresh
no cache returns unknown status and starts background refresh
doctor timeout is recorded as diagnostic_unknown, not user turn failure
```

- [x] **Step 3: Run diagnostics tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_model_latency_diagnostics.py -q
```

Expected:

```text
All tests passed
```

## Task 8: Honest Model Gating And Fast Failure

**Files:**

- Modify: `learning_agent/app/gui_agent_adapter.py`
- Modify: `learning_agent/app/gui_provider_settings.py`
- Modify: `apps/desktop/src/components/Composer.tsx`
- Modify: `apps/desktop/src/state/providerSettingsStore.ts`
- Test: `learning_agent/tests/test_gui_real_model_latency_events.py`
- Test: `apps/desktop/tests/composer.test.ts`

- [x] **Step 1: Fast-fail disconnected provider**

If user selects real OpenAI model but provider is disconnected:

```text
show "请先连接 OpenAI"
do not start long backend model call
do not spawn codex.exe
```

- [x] **Step 2: Cache unsupported model failures**

If ChatGPT OAuth rejects a model:

```text
record provider_id + model_id + error_kind=model_unsupported
show readable error
mark model in dropdown as recently failed
clear failure after reconnect or model catalog refresh
```

- [x] **Step 3: Run gating tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_latency_events.py -q
npm --prefix apps/desktop test -- composer.test.ts
```

Expected:

```text
All selected tests passed
```

## Task 9: Probe And Gate Direct ChatGPT OAuth SSE Fast Path

**Files:**

- Modify: `learning_agent/models/adapters.py`
- Test: `learning_agent/tests/test_codex_oauth_streaming_probe.py`
- Evidence: `learning_agent/test/real_model_latency_v2_20260626/direct_oauth_sse_probe.md`

- [x] **Step 1: Add capability probe contract**

Probe result must be one of:

```text
available
unavailable_unauthorized
unavailable_forbidden
unavailable_unknown_payload
not_configured
```

- [x] **Step 2: Run probe only when direct OAuth is explicitly configured**

Required environment:

```text
OPENHARNESS_OPENAI_AUTH_MODE=direct_oauth
OPENHARNESS_OPENAI_EXPERIMENTAL=1
OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted
OPENHARNESS_OPENAI_CLIENT_ID=<explicit user-provided client id>
```

- [x] **Step 3: Do not claim streaming if probe fails**

If probe result is not `available`, GUI may show connected/authenticated status but must not claim low-latency SSE streaming.

- [x] **Step 4: Implement SSE stream only after available probe**

When available:

```text
use Authorization header only
do not log token
parse SSE chunks into delta events
emit first_delta exactly once
close stream on cancellation
```

- [x] **Step 5: Run probe tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_codex_oauth_streaming_probe.py -q
```

Expected:

```text
All tests passed
```

## Task 10: Secret Redaction Gate

**Files:**

- Create: `learning_agent/tests/test_gui_model_latency_secret_redaction.py`
- Reuse: `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`

- [x] **Step 1: Add redaction unit test**

Patterns that must fail if found in model latency evidence:

```text
access_token
refresh_token
id_token
authorization_code
Bearer 
sk-
cookie
oauth/authorize?response_type=code
localhost:1455/auth/callback?code=
```

- [x] **Step 2: Run redaction test**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_model_latency_secret_redaction.py -q
```

Expected:

```text
All tests passed
```

- [x] **Step 3: Run evidence directory leak scan**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1 learning_agent/test/real_model_latency_v2_20260626
```

Expected:

```text
No provider secret leaks detected
```

## Task 11: Visible GUI Acceptance And Documentation

**Files:**

- Create/modify: `learning_agent/test/real_model_latency_v2_20260626/visible_evidence/README.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Modify: `agent_memory/experience.md`

- [x] **Step 1: Start real visible GUI**

Open the real OpenHarness Desktop window. Use computer-use when available.

- [x] **Step 2: Run real prompt**

Select:

```text
Provider: OpenAI / ChatGPT OAuth connected source
Model: GPT-5.5 or currently visible supported ChatGPT OAuth model
Reasoning: current composer selection
Prompt: 请用一句中文回答：你现在是真实模型连接还是模拟回复？
```

- [x] **Step 3: Record metrics**

`visible_evidence/README.md` must contain:

```text
Prompt:
Selected provider:
Selected model:
first_status_ms:
first_transport_warning_ms:
first_delta_ms:
completion_ms:
cancel_visible_ms:
cancel_backend_stop_ms:
Observed transport:
Screenshot files:
Result:
```

- [x] **Step 4: Apply visible GUI acceptance and bug rule**

验收需要使用肉眼可见的真实 GUI 界面进行验收，使用 `computer-use:computer-use` 技能确认和验证。如果验收时出现 bug 或发现 bug 时，必须使用 `superpowers:systematic-debugging` 技能，修复 bug，并重新测试，测试通过后继续执行下一个任务。

- [x] **Step 5: Run final regression commands**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_real_model_latency_baseline.py learning_agent/tests/test_streaming_chat_model_protocol.py learning_agent/tests/test_gui_real_model_latency_events.py learning_agent/tests/test_codex_cli_event_shape_discovery.py learning_agent/tests/test_codex_cli_streaming_model.py learning_agent/tests/test_gui_model_latency_diagnostics.py learning_agent/tests/test_codex_oauth_streaming_probe.py learning_agent/tests/test_gui_model_latency_secret_redaction.py -q
npm --prefix apps/desktop test -- realModelLatencyEvents.test.ts modelCallStatus.test.tsx composer.test.ts
powershell -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1 learning_agent/test/real_model_latency_v2_20260626
```

Expected:

```text
All selected Python tests passed
All selected Desktop tests passed
No provider secret leaks detected
Visible GUI acceptance passed
```

## Stop Conditions

Stop and report instead of pushing forward when:

- Direct OAuth SSE endpoint or payload shape cannot be verified without exposing private token.
- Codex CLI discovery proves there are no token deltas; in that case implement status/fallback observability but do not claim Codex CLI true token streaming.
- The user’s ChatGPT OAuth account rejects all visible models.
- The visible GUI cannot be opened or observed from the current environment.
- Fixing latency would require copying OpenCode private client ids, client secrets, or user tokens into OpenHarness.
- Cancellation cannot reliably stop the Windows process tree; report the exact child process behavior and keep the UI honest.

## Implementation Order

1. Task 0: Baseline Latency Measurement.
2. Task 1: Streaming Event Contract.
3. Task 2: Backend Adapter Emits Real Phases.
4. Task 3: Frontend Visible Model Status.
5. Task 4: Real Cancellation.
6. Task 5: Codex CLI Event Shape Discovery.
7. Task 6: Observable Codex CLI Runner.
8. Task 7: Async Transport Diagnostics Cache.
9. Task 8: Honest Model Gating And Fast Failure.
10. Task 9: Probe And Gate Direct ChatGPT OAuth SSE Fast Path.
11. Task 10: Secret Redaction Gate.
12. Task 11: Visible GUI Acceptance And Documentation.

## Expected User-Facing Result

After V2 lands, the user should not stare at a silent waiting state for 2 minutes. In the worst Codex CLI WebSocket timeout case, the Desktop shell shows what is happening, stays cancellable, and records honest latency metrics. In the best verified Direct OAuth SSE case, the selected ChatGPT OAuth model streams visible output as soon as real deltas arrive.
