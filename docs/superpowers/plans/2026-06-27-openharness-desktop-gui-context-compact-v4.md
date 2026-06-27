# OpenHarness Desktop GUI Context Compact V4.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the OpenHarness Desktop GUI message window send compact-aware multi-turn context to real ChatGPT OAuth Direct SSE calls, instead of sending only the latest prompt.

**Architecture:** Use `GuiSession.messages` as the GUI conversation source of truth. Add a focused text-only GUI context builder, feed its Responses `input` into Direct SSE, reuse the existing compact pipeline, and expose only privacy-safe budget/compact events. Reactive context overflow recovery is a two-attempt state machine: first request, optional one compact retry, then stop.

**Tech Stack:** Python stdlib HTTP bridge, existing `learning_agent.core.compact_pipeline`, existing `learning_agent.models.chatgpt_codex_sse.ChatGptCodexSseClient`, existing Electron/React Desktop GUI event stream, pytest, npm/Vitest if frontend rendering changes, Computer Use for real visible GUI acceptance.

---

## Review Upgrade Summary

This V4.1 plan incorporates:

- `docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4-karpathy-review.md`

Key upgrades:

- Add **Task 0 Evidence Lock** to prove the current latest-prompt-only bug before implementation.
- Deliver a minimum vertical slice first: text-only multi-turn context before compact, compact before reactive retry.
- Use current turn prompt as GUI compact goal so early greetings do not pollute `TaskState`.
- Add exact-once tests for current prompt.
- Add Direct SSE request body contract tests.
- Keep visible runtime events privacy-safe.
- Split visible GUI acceptance into data-layer evidence and model-behavior evidence.

---

## Current Evidence

- Existing compact modules:
  - `learning_agent/core/compact.py`
  - `learning_agent/core/compact_pipeline.py`
  - `learning_agent/core/reactive_compact.py`
  - `learning_agent/core/conversation_context.py`
- Current GUI Direct SSE path is latest-prompt-first:
  - `learning_agent/app/gui_agent_adapter.py::_direct_sse_messages()` builds input from `request.prompt`.
  - `learning_agent/app/gui_bridge.py::_run_adapter_turn()` builds `GuiAgentRunRequest(... prompt=turn.prompt ...)`.
- GUI history already exists:
  - `learning_agent/app/gui_bridge.py::start_message()` appends visible messages to `GuiSession.messages`.
- Direct SSE body contract:
  - `learning_agent/models/chatgpt_codex_sse.py::stream_responses()` sends caller-provided `messages` as body field `"input"`.

---

## File Map

### Create

- `learning_agent/app/gui_context.py`
  - Normalize GUI text history.
  - Enforce current prompt exact-once.
  - Build current-prompt-first `TaskState`.
  - Convert text-only history to Direct SSE Responses input.
  - Apply proactive compact.
  - Produce privacy-safe event payloads.
  - Convert Responses input back to compact messages for reactive retry.

- `learning_agent/tests/test_gui_context_builder.py`
  - Test exact-once prompt handling.
  - Test first-greeting does not become compact goal.
  - Test proactive compact preserves current prompt.
  - Test event payload excludes raw prompt/history/summary.

### Modify

- `learning_agent/app/gui_agent_adapter.py`
  - Add `messages` and `context_metadata` to `GuiAgentRunRequest`.
  - Prefer `request.messages` in `_direct_sse_messages()`.
  - Add two-attempt Direct SSE retry helpers.

- `learning_agent/app/gui_bridge.py`
  - Build GUI context before adapter execution.
  - Emit safe context events.
  - Pass prebuilt messages to adapter.

- `learning_agent/tests/test_gui_turn_payload_contract.py`
  - Add Evidence Lock and manager-level history/event tests.

- `learning_agent/tests/test_gui_direct_oauth_sse_adapter.py`
  - Add prebuilt message body and reactive retry tests.

- `learning_agent/tests/test_chatgpt_codex_sse_client.py`
  - Add body contract test if not already covered.

- `agent_memory/progress.md`
- `agent_memory/bugs.md`

### Optional

- `apps/desktop/src/state/eventReducer.ts`
  - Modify only if current event list hides context events.

---

## Success Criteria

- Evidence Lock test fails before implementation and passes after implementation.
- Direct SSE request body includes prior completed user/assistant text plus current prompt.
- Current prompt appears exactly once.
- GUI compact `TaskState` uses current prompt as current goal and original request for compact purposes.
- Proactive compact keeps current prompt and important earlier facts.
- Visible GUI runtime events show safe metadata only.
- Reactive retry makes at most two Direct SSE attempts and never retries after visible text has streamed.
- Real GUI acceptance proves both:
  - Data layer: Direct SSE request or sanitized debug evidence contains `ALPHA_CONTEXT_927` or a compact summary preserving it.
  - Behavior layer: real model replies with `ALPHA_CONTEXT_927`.

---

## Invariants

- Follow all `AGENTS.md` Chinese comment rules for actual source edits.
- Copy modified source/tests to `learning_agent/test/gui_context_compact_v4/`.
- Keep Direct SSE on `runtime=direct_sse`, `websocket_enabled=false`, `codex_cli_used=false`.
- V4.1 is text-only: exclude or summarize images, tool calls, reasoning items, and native function-call items.
- Exclude current assistant placeholder.
- Exclude empty, queued, failed, or cancelled assistant messages.
- Do not put raw OAuth tokens, raw compact summaries, raw prompt bodies, access tokens, refresh tokens, or API keys in visible event payloads.

## Mandatory Real GUI Verification And Debugging Rule

- 真实 GUI 窗口验证必须使用 `computer-use` skill 操作和观察 OpenHarness Desktop GUI。
- 当真实 GUI 窗口验证时出现 bug、异常状态、加载失败、模型无回复、上下文未生效、事件面板证据缺失，或任何肉眼可见问题时，必须先使用 `superpowers:systematic-debugging` skill 查询和定位 root cause。
- 在 root cause 没有查清前，不允许直接猜测式修复。
- 修复后必须重新运行相关自动化测试，并重新执行同一个真实 GUI 窗口验证。
- 只有当前任务的自动化验证和真实 GUI 窗口验证都通过后，才允许继续执行蓝图里的下一个任务。

---

### Task 0: Evidence Lock

**Files:**
- Modify: `learning_agent/tests/test_gui_turn_payload_contract.py`

- [ ] **Step 1: Add failing test**

Add a test named:

```python
def test_gui_manager_does_not_send_only_latest_prompt_to_adapter(self) -> None:
    ...
```

Required test setup:

- Use `GuiRunManager` with a `SpyAdapter`.
- Send first GUI message: `请记住测试代号 ALPHA_CONTEXT_927`.
- Send second GUI message: `刚才的测试代号是什么？`.
- Inspect the second captured `GuiAgentRunRequest`.

Required assertions:

```python
assert hasattr(second_request, "messages")
assert "ALPHA_CONTEXT_927" in joined_request_text
assert "刚才的测试代号是什么？" in joined_request_text
```

- [ ] **Step 2: Run and verify red**

```powershell
python -m pytest learning_agent\tests\test_gui_turn_payload_contract.py::GuiTurnPayloadContractTests::test_gui_manager_does_not_send_only_latest_prompt_to_adapter -q
```

Expected:

```text
FAIL
```

---

### Task 1: GUI Text Context Builder

**Files:**
- Create: `learning_agent/app/gui_context.py`
- Create: `learning_agent/tests/test_gui_context_builder.py`

- [ ] **Step 1: Add context builder tests**

Create tests with these names:

```python
def test_current_prompt_appears_once_when_current_user_message_exists(tmp_path) -> None: ...
def test_current_prompt_is_appended_once_when_missing_from_session_messages(tmp_path) -> None: ...
def test_task_state_goal_prefers_current_prompt_over_first_greeting(tmp_path) -> None: ...
def test_gui_context_compacts_long_history_and_keeps_current_prompt(tmp_path) -> None: ...
def test_gui_context_event_payload_excludes_raw_text(tmp_path) -> None: ...
def test_gui_context_limits_from_env_respects_small_visual_qa_thresholds(monkeypatch) -> None: ...
```

Required fixtures:

```python
@dataclass
class MessageStub:
    role: str
    text: str
    turn_id: str = ""
    status: str = "completed"
```

Required assertions:

```python
assert joined_text.count(current_prompt) == 1
assert "ALPHA_CONTEXT_927" in joined_text
assert result.task_state_summary["current_goal"] == current_prompt
assert result.task_state_summary["original_user_request"] == current_prompt
assert result.compacted is True
assert raw_history_text not in json.dumps(result.event_payload, ensure_ascii=False)
```

- [ ] **Step 2: Run and verify red**

```powershell
python -m pytest learning_agent\tests\test_gui_context_builder.py -q
```

Expected:

```text
FAIL
ModuleNotFoundError
```

- [ ] **Step 3: Implement public API**

`learning_agent/app/gui_context.py` must expose:

```python
@dataclass
class GuiContextBuildResult:
    messages: list[dict[str, object]]
    compacted: bool
    event_payload: dict[str, object]
    task_state_summary: dict[str, str]


def build_gui_context_for_turn(...) -> GuiContextBuildResult: ...
def responses_input_to_compact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
def gui_context_limits_from_env(env: Mapping[str, str] | None = None) -> dict[str, int]: ...
```

Required behavior:

- Accept dataclass-style and dict-style GUI messages.
- Keep only user/assistant text.
- Keep completed assistant messages only.
- Drop current assistant placeholder.
- Append current prompt only if missing.
- Use current prompt as `TaskState` original request/current goal for GUI compact.
- Build text-only Responses input:

```python
{"role": "user" | "assistant", "content": [{"type": "input_text", "text": text}]}
```

- Event payload may include counts, char estimates, reason, generation, and relative artifact path only.

- [ ] **Step 4: Run and verify green**

```powershell
python -m pytest learning_agent\tests\test_gui_context_builder.py -q
```

Expected:

```text
all selected tests passed
```

---

### Task 2: Direct SSE Body Contract

**Files:**
- Modify: `learning_agent/app/gui_agent_adapter.py`
- Modify: `learning_agent/tests/test_chatgpt_codex_sse_client.py`
- Modify: `learning_agent/tests/test_gui_direct_oauth_sse_adapter.py`

- [ ] **Step 1: Add body contract tests**

Add tests named:

```python
def test_stream_responses_preserves_text_only_message_input_body() -> None: ...
def test_direct_sse_adapter_uses_request_messages_when_present(tmp_path, monkeypatch) -> None: ...
```

Required assertions:

```python
assert captured["body"]["input"] == messages
assert captured["body"]["input"] == request.messages
```

- [ ] **Step 2: Run and verify red where adapter lacks fields**

```powershell
python -m pytest learning_agent\tests\test_chatgpt_codex_sse_client.py::test_stream_responses_preserves_text_only_message_input_body learning_agent\tests\test_gui_direct_oauth_sse_adapter.py::test_direct_sse_adapter_uses_request_messages_when_present -q
```

Expected:

```text
client test may pass; adapter test fails until request.messages exists
```

- [ ] **Step 3: Implement adapter request fields**

Add to `GuiAgentRunRequest`:

```python
messages: list[dict[str, object]] = field(default_factory=list)
context_metadata: dict[str, object] = field(default_factory=dict)
```

Update `_direct_sse_messages()`:

```python
if request.messages:
    return request.messages
return [{"role": "user", "content": [{"type": "input_text", "text": request.prompt}]}]
```

- [ ] **Step 4: Run adapter/client tests**

```powershell
python -m pytest learning_agent\tests\test_chatgpt_codex_sse_client.py learning_agent\tests\test_gui_direct_oauth_sse_adapter.py -q
```

Expected:

```text
all selected tests passed
```

---

### Task 3: Bridge Context Into GUI Turns

**Files:**
- Modify: `learning_agent/app/gui_bridge.py`
- Modify: `learning_agent/tests/test_gui_turn_payload_contract.py`

- [ ] **Step 1: Build context in `_run_adapter_turn()`**

Required flow:

```python
context_limits = gui_context_limits_from_env()
context_result = build_gui_context_for_turn(
    session_messages=session.messages,
    current_turn_id=turn.turn_id,
    current_prompt=turn.prompt,
    session_id=turn.session_id,
    run_id=turn.run_id,
    turn_id=turn.turn_id,
    workspace=self.workspace,
    max_messages=context_limits["max_messages"],
    max_chars=context_limits["max_chars"],
)
```

Required request fields:

```python
messages=context_result.messages
context_metadata=context_result.event_payload
```

Preserve existing provider/model fields:

```python
provider_id=turn.provider_id
model_id=turn.model_id
reasoning_effort=turn.reasoning_effort
permission_mode=turn.permission_mode
workspace=str(self.workspace)
```

- [ ] **Step 2: Emit safe runtime events**

Required events:

```text
context_budget
compact_completed, only if compacted
compact_skipped, only if no compact and existing event conventions support it
```

Payload must be `context_result.event_payload`.

- [ ] **Step 3: Run Evidence Lock again and verify green**

```powershell
python -m pytest learning_agent\tests\test_gui_turn_payload_contract.py::GuiTurnPayloadContractTests::test_gui_manager_does_not_send_only_latest_prompt_to_adapter -q
```

Expected:

```text
1 passed
```

- [ ] **Step 4: Add manager event test**

Add:

```python
def test_gui_manager_records_privacy_safe_context_budget_event(self) -> None: ...
```

Required assertions:

```python
assert "estimated_chars_before" in payload
assert "estimated_chars_after" in payload
assert "ALPHA_CONTEXT_927" not in json.dumps(payload, ensure_ascii=False)
```

- [ ] **Step 5: Run manager contract tests**

```powershell
python -m pytest learning_agent\tests\test_gui_turn_payload_contract.py -q
```

Expected:

```text
all selected tests passed
```

---

### Task 4: Reactive Context Overflow Retry

**Files:**
- Modify: `learning_agent/app/gui_agent_adapter.py`
- Modify: `learning_agent/app/gui_context.py`
- Modify: `learning_agent/tests/test_gui_direct_oauth_sse_adapter.py`

- [ ] **Step 1: Add retry tests**

Add tests named:

```python
def test_direct_sse_adapter_retries_once_after_context_overflow_before_visible_delta(tmp_path, monkeypatch) -> None: ...
def test_direct_sse_adapter_does_not_retry_context_error_after_visible_delta(tmp_path, monkeypatch) -> None: ...
```

Required assertions:

```python
assert len(calls) == 2
assert any(event["kind"] == "reactive_compact_completed" for event in events)
assert len(calls_after_visible_delta) == 1
```

- [ ] **Step 2: Implement state-machine helpers**

Required helper shape:

```python
@dataclass
class DirectSseAttemptResult:
    status: str
    final_text: str
    error: str
    visible_delta_emitted: bool


def _run_direct_sse_once(...) -> DirectSseAttemptResult: ...
def _should_retry_after_context_overflow(result: DirectSseAttemptResult, attempted: bool) -> bool: ...
```

Allowed retry flow:

1. Run first attempt.
2. Retry only if error is context overflow, no retry attempted, and no visible delta emitted.
3. Call `recover_from_context_overflow(...)`.
4. Emit `reactive_compact_completed` with safe payload.
5. Run second attempt.
6. Do not run a third attempt.

- [ ] **Step 3: Run retry tests**

```powershell
python -m pytest learning_agent\tests\test_gui_direct_oauth_sse_adapter.py::test_direct_sse_adapter_retries_once_after_context_overflow_before_visible_delta learning_agent\tests\test_gui_direct_oauth_sse_adapter.py::test_direct_sse_adapter_does_not_retry_context_error_after_visible_delta -q
```

Expected:

```text
2 passed
```

---

### Task 5: Automated Verification

**Files:**
- No new source files.

- [ ] **Step 1: Run targeted Python tests**

```powershell
python -m pytest learning_agent\tests\test_gui_context_builder.py learning_agent\tests\test_gui_direct_oauth_sse_adapter.py learning_agent\tests\test_gui_turn_payload_contract.py learning_agent\tests\test_chatgpt_codex_sse_client.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: Compile changed Python files**

```powershell
python -m py_compile learning_agent\app\gui_context.py learning_agent\app\gui_agent_adapter.py learning_agent\app\gui_bridge.py learning_agent\models\chatgpt_codex_sse.py
```

Expected:

```text
command exits with code 0
```

- [ ] **Step 3: Run provider/model regression tests**

```powershell
python -m pytest learning_agent\tests\test_gui_provider_openai_real_oauth_attempts.py learning_agent\tests\test_gui_provider_oauth_disconnect.py learning_agent\tests\test_openai_model_registry.py learning_agent\tests\test_openai_provider_runtime_state.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 4: Run frontend tests if frontend changed**

```powershell
npm --prefix apps/desktop test -- --run
npm --prefix apps/desktop run lint
```

Expected:

```text
Vitest and lint pass
```

- [ ] **Step 5: Run secret scan**

```powershell
python learning_agent\scripts\assert_no_real_provider_secret_leaks.py
```

Expected:

```text
Provider secret leak scan passed.
```

---

### Task 6: Real Visible GUI Acceptance

**Files:**
- Evidence directory: `learning_agent/test/gui_context_compact_v4/`

- [ ] **Step 1: Start GUI with forced compact thresholds**

Use:

```powershell
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse"
$env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted"
$env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1"
$env:OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES = "5"
$env:OPENHARNESS_GUI_CONTEXT_MAX_CHARS = "900"
```

Expected visible state:

- OpenHarness Desktop opens.
- GUI bridge is online.
- OpenAI provider is connected through OAuth.
- Composer model menu shows an OpenAI/ChatGPT OAuth model.

- [ ] **Step 2: Verify no-compact recall**

Use Computer Use to send:

```text
请记住这个测试代号：ALPHA_CONTEXT_927。只回复：已记住。
```

Then send:

```text
刚才的测试代号是什么？只输出代号。
```

Expected:

- Data layer: sanitized request/debug evidence includes `ALPHA_CONTEXT_927`.
- Behavior layer: visible assistant answer contains `ALPHA_CONTEXT_927`.
- Runtime event shows `runtime=direct_sse`, `websocket_enabled=false`, `codex_cli_used=false`.

- [ ] **Step 3: Verify forced compact recall**

Send five filler turns:

```text
补充上下文 1：这是一段用于触发压缩的测试文本。
补充上下文 2：这是一段用于触发压缩的测试文本。
补充上下文 3：这是一段用于触发压缩的测试文本。
补充上下文 4：这是一段用于触发压缩的测试文本。
补充上下文 5：这是一段用于触发压缩的测试文本。
```

Then send:

```text
刚才我让你记住的测试代号是什么？只输出代号。
```

Expected:

- Right runtime panel shows `context_budget`.
- Right runtime panel shows `compact_completed`.
- Visible assistant answer is `ALPHA_CONTEXT_927` or contains `ALPHA_CONTEXT_927`.
- Visible event payloads do not expose raw compact summary or secrets.

- [ ] **Step 4: Debug before changing code if GUI acceptance fails**

Use `superpowers:systematic-debugging` and collect:

- GUI runtime event tail.
- Provider runtime state.
- Sanitized Direct SSE body evidence.
- Screenshot of visible GUI state.

Classify failure as one of:

```text
context construction
compact pipeline
Direct SSE protocol
model behavior
GUI rendering
```

Then fix root cause and rerun from Step 1.

---

### Task 7: Learning Copy And Memory Update

**Files:**
- Create directory: `learning_agent/test/gui_context_compact_v4/`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: Copy source and tests**

```powershell
New-Item -ItemType Directory -Force learning_agent\test\gui_context_compact_v4
Copy-Item learning_agent\app\gui_context.py learning_agent\test\gui_context_compact_v4\gui_context.py
Copy-Item learning_agent\app\gui_agent_adapter.py learning_agent\test\gui_context_compact_v4\gui_agent_adapter.py
Copy-Item learning_agent\app\gui_bridge.py learning_agent\test\gui_context_compact_v4\gui_bridge.py
Copy-Item learning_agent\tests\test_gui_context_builder.py learning_agent\test\gui_context_compact_v4\test_gui_context_builder.py
Copy-Item learning_agent\tests\test_gui_direct_oauth_sse_adapter.py learning_agent\test\gui_context_compact_v4\test_gui_direct_oauth_sse_adapter.py
Copy-Item learning_agent\tests\test_gui_turn_payload_contract.py learning_agent\test\gui_context_compact_v4\test_gui_turn_payload_contract.py
Copy-Item learning_agent\tests\test_chatgpt_codex_sse_client.py learning_agent\test\gui_context_compact_v4\test_chatgpt_codex_sse_client.py
```

- [ ] **Step 2: Update memory**

Append to `agent_memory/progress.md`:

```markdown
## 2026-06-27 OpenHarness Desktop GUI Context Compact V4.1

- GUI message window now sends text-only compact-aware multi-turn context to ChatGPT OAuth Direct SSE.
- Current prompt exact-once behavior is covered by tests.
- GUI compact TaskState uses current turn prompt as the goal, avoiding first-greeting goal pollution.
- Visible GUI acceptance verified `ALPHA_CONTEXT_927` recall without compact and with forced compact.
```

Append to `agent_memory/bugs.md`:

```markdown
## 2026-06-27 GUI Direct SSE Latest-Prompt-Only Context Bug

- Root cause: Desktop GUI Direct SSE adapter previously received only the latest prompt, so follow-up prompts could not reliably use earlier GUI conversation messages.
- Fix: GUI bridge now builds a text-only session context from `GuiSession.messages`, applies compact when needed, and passes prebuilt Responses input into Direct SSE.
- Guardrails: current prompt exact-once tests, Direct SSE body contract tests, privacy-safe context events, and real visible GUI acceptance.
```

---

## Final Release Gate

Before saying the feature is complete, all must be true:

- Evidence Lock test red before implementation, green after implementation.
- Targeted pytest passes.
- `py_compile` passes.
- Provider/model regression tests pass.
- Secret scan passes.
- OpenHarness Desktop GUI visibly opens.
- Computer Use sends real GUI messages.
- Every GUI-affecting task has been verified in the real visible GUI window with `computer-use`; if any issue was found, `superpowers:systematic-debugging` was used to find root cause, fix it, and retest before continuing to the next task.
- Data-layer evidence proves Direct SSE receives prior context.
- Behavior-layer evidence proves real model recalls `ALPHA_CONTEXT_927`.
- Runtime panel shows `context_budget` and forced-threshold `compact_completed`.

If visible GUI acceptance cannot be completed, final response must say:

```text
真实可见 GUI 上下文压缩验收未完成，不能声明开发完成。
```

---

## Self-Review

- Spec coverage: Covers evidence lock, text-only multi-turn context, proactive compact, reactive retry, event privacy, automated tests, secret safety, and real visible GUI acceptance.
- Review coverage: Incorporates every must-upgrade item from the Karpathy review.
- Placeholder scan: No unfinished placeholder markers are used.
- Type consistency: `GuiContextBuildResult.messages`, `GuiAgentRunRequest.messages`, and Direct SSE `body["input"]` all mean the same text-only Responses input format.
- Scope check: Does not change OAuth, provider settings, or frontend layout unless event rendering proves insufficient.
