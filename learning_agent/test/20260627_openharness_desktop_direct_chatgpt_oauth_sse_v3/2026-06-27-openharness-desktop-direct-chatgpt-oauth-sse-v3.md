# OpenHarness Desktop Direct ChatGPT OAuth SSE V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` for parallel review where the environment supports subagents, otherwise use `superpowers:executing-plans` and execute this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build an experimental OpenHarness Desktop real-model runtime that uses ChatGPT OAuth + direct HTTPS/SSE for selected OpenAI OAuth models, without silently falling back to the slow Codex CLI WebSocket retry path.

**Architecture:** Implement V3 as a set of thin vertical slices: first prove selected-model GUI payloads against a fake SSE server, then add OS-encrypted token storage, real browser OAuth, account discovery, model probing, direct SSE streaming, cancellation, diagnostics, and visible GUI acceptance. The direct endpoint is an explicitly gated experimental runtime, not a stable OpenHarness product contract.

**Tech Stack:** Python stdlib HTTP server and `urllib`, Windows DPAPI CurrentUser encryption, existing `learning_agent.models.base.ModelStreamEvent`, existing OpenHarness GUI bridge, Electron/React desktop UI, Pytest, Vitest, structured secret scanning, and computer-use visible GUI acceptance.

---

## 1. Review-Driven Upgrade Summary

This upgraded plan incorporates the Karpathy review findings:

1. The OpenCode OAuth client id is treated as a research observation, not a product default.
2. The direct ChatGPT Codex endpoint is gated behind `OPENHARNESS_OPENAI_EXPERIMENTAL=1` and `OPENHARNESS_OPENAI_RUNTIME=direct_sse`.
3. SSE parsing is driven by sanitized golden fixtures, not imagined event shapes only.
4. Secret scanning uses a structured scanner that distinguishes safe key names from real secret values.
5. Model availability is static + probe + last-known-good, not a fixed hardcoded allow-list.
6. Account discovery and account-required errors are first-class runtime states.
7. Stream cancellation, timeout classes, retry rules, and endpoint drift are explicit.
8. Existing `CodexOAuthChatModel` logic receives a migration plan so two OAuth stacks do not silently diverge.
9. Execution is reordered around thin vertical slices so every phase has visible evidence.
10. GUI acceptance verifies real direct SSE behavior instead of depending on exact model wording.

---

## 2. Evidence And Current Code Facts

### OpenCode evidence already confirmed

- `D:\opencode\packages\opencode\src\plugin\openai\codex.ts`
  - Uses OpenAI issuer `https://auth.openai.com`.
  - Uses PKCE OAuth authorize flow with `codex_cli_simplified_flow=true`.
  - Exchanges callback code for OAuth tokens.
  - Refreshes access tokens before use.
  - Rewrites response calls to `https://chatgpt.com/backend-api/codex/responses`.
  - Sends `Authorization: Bearer access_token_value` and `ChatGPT-Account-Id` when available.

- `D:\opencode\packages\opencode\src\plugin\openai\ws-pool.ts`
  - WebSocket transport is experimental.
  - Fallback is intentionally fast.
  - OpenCode does not make users wait through five Codex CLI WebSocket retries.

- `D:\opencode\packages\llm\src\protocols\openai-responses.ts`
  - Default OpenAI Responses transport is HTTP SSE.
  - WebSocket is a separate route.

### Current OpenHarness facts verified by CodeGraph

- `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\Composer.tsx`
  - `ComposerSubmitHandler` currently submits only a prompt string.

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_auth_attempts.py`
  - OpenAI browser/headless auth attempts are still mock attempts.

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_secret_store.py`
  - Current secret interface is `set_secret(secret_ref, value)`, `get_secret(secret_ref)`, `delete_secret(secret_ref)`, and `mask_secret(secret_ref)`.
  - Current implementation is `DevJsonSecretStore`, which writes development JSON.

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_settings.py`
  - `disconnect_provider` currently deletes one API-key-style `secret_ref`; it does not yet clear OAuth token ref groups.

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\adapters.py`
  - `CodexOAuthChatModel` contains useful OAuth/SSE pieces but buffers SSE internally and should be migrated into focused modules.

---

## 3. Non-Negotiable Product Contract

### Direct SSE is experimental

Direct ChatGPT OAuth SSE may be the default runtime only inside explicitly enabled experimental ChatGPT OAuth mode:

```powershell
$env:OPENHARNESS_OPENAI_AUTH_MODE = "real_browser"
$env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1"
$env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted"
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse"
if (-not $env:OPENHARNESS_OPENAI_CLIENT_ID) { throw "OPENHARNESS_OPENAI_CLIENT_ID must be set explicitly by the operator." }
```

Research note:

- The currently observed OpenCode OAuth client id is `app_EMoamEEZ73f0CkXaXp7hrann`.
- This value may be used for local compatibility experiments only.
- OpenHarness must not treat it as an owned stable product default.
- When this observed value is used, diagnostics must show `oauth_client_source=observed_opencode_reference`.

### No silent fallback

When `OPENHARNESS_OPENAI_RUNTIME=direct_sse`, failure must produce visible state:

- `direct_route_unavailable`
- `provider_needs_reconnect`
- `account_selection_required`
- `model_not_available`
- `stream_timeout`
- `endpoint_drift_detected`

The code must not silently call Codex CLI in direct mode.

### WebSocket is disabled for V3 direct SSE

Direct SSE must emit:

```json
{
  "runtime": "direct_sse",
  "transport": "https_sse",
  "websocket_enabled": false,
  "codex_cli_used": false
}
```

---

## 4. File Structure Map

### Backend runtime files

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_openai_oauth.py`
  - Owns PKCE, browser auth attempt lifecycle, localhost callback, token exchange, account discovery, and OAuth attempt cleanup.

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_openai_state.py`
  - Defines `OpenAIProviderRuntimeState`, `OpenAIAccountSummary`, `OpenAIModelAvailability`, and safe serialization helpers.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_secret_store.py`
  - Adds `OsEncryptedSecretStore` and `make_provider_secret_store`.
  - Keeps `DevJsonSecretStore` for API-key development mode only.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_auth_attempts.py`
  - Routes OpenAI browser real mode to `OpenAIChatGptOAuthService`.
  - Keeps mock attempts for stable visual provider UI tests.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_settings.py`
  - Uses `make_provider_secret_store`.
  - Supports OAuth secret ref groups.
  - Clears selected model/account on disconnect.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_bridge.py`
  - Accepts selected provider/model/reasoning/permission fields.
  - Emits runtime diagnostics.
  - Exposes auth attempt, model probe, and cancellation state.

### Model runtime files

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\chatgpt_codex_sse.py`
  - Focused direct HTTPS/SSE client and parser.

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\chatgpt_oauth_tokens.py`
  - Resolves encrypted OAuth token refs, refreshes tokens, and returns in-memory token objects only.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\adapters.py`
  - Marks `CodexOAuthChatModel` as a legacy compatibility wrapper or migrates its useful pieces into the new focused modules.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_agent_adapter.py`
  - Adds the real direct OpenAI GUI adapter path.
  - Converts `ModelStreamEvent` to GUI events.
  - Handles cancellation and timeout lifecycle.

### Frontend files

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\Composer.tsx`
  - Submits structured payload instead of only prompt string.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\AppShell.tsx`
  - Owns selected provider/model/reasoning/permission state and passes it into Composer.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\api\guiClient.ts`
  - Sends new GUI turn payload fields.
  - Adds model probe and cancellation request helpers if absent.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\api\guiProviderTypes.ts`
  - Adds runtime, account, model availability, probe, and diagnostics types.

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\state\providerSettingsStore.ts`
  - Resets selected model on disconnect.
  - Redacts nested secret refs and token-like values before logging.

### Tests and fixtures

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\response_stream_basic.sse`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\response_stream_tool_call.sse`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\response_stream_error_model_not_supported.sse`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\oauth_token_response.example.json`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\scripts\assert_no_real_provider_secret_leaks.py`

---

## 5. Success Criteria

1. Fake token + fake SSE vertical slice proves GUI sends selected provider/model before real OAuth is added.
2. Real OAuth tokens are stored only in OS-encrypted storage when real mode is enabled.
3. OpenAI browser OAuth works through a visible browser flow and a localhost callback.
4. Account discovery stores a safe account summary and surfaces account-required errors.
5. Model dropdown is driven by static known models, probe results, and last-known-good cache.
6. Direct SSE streams at least one visible delta before completion.
7. Cancel closes an active SSE request and emits a visible cancelled event.
8. Direct runtime emits `codex_cli_used=false` and `websocket_enabled=false`.
9. Structured secret scanner passes without deleting useful field names.
10. Visible GUI acceptance proves connect, model selection, direct streaming, cancel, disconnect, and reconnect.

---

## 6. Stop Conditions

Stop and report before continuing if any condition is hit:

1. OAuth cannot complete without copying private secrets.
2. The configured OAuth client id is rejected and no user-approved experimental value is available.
3. The direct endpoint rejects all authenticated probes with no actionable account/model reason.
4. Windows DPAPI CurrentUser encryption fails on the target machine.
5. Real tokens appear in logs, UI, state files, diagnostics, or test fixtures.
6. The only working path is Codex CLI WebSocket retry fallback.
7. computer-use cannot safely complete a required human browser login step.

---

## 7. Runtime Data Contracts

### OpenAIProviderRuntimeState

```python
@dataclass(frozen=True)
class OpenAIProviderRuntimeState:
    provider_id: str
    auth_type: str
    runtime: str
    direct_route_status: str
    account_id: str | None
    account_label: str
    selected_model_id: str | None
    available_models: list[str]
    last_known_good_models: list[str]
    oauth_client_source: str
    needs_reconnect: bool
    updated_at: str
```

Allowed `direct_route_status` values:

- `not_connected`
- `not_probed`
- `healthy`
- `account_selection_required`
- `model_not_available`
- `auth_failed`
- `direct_route_unavailable`
- `endpoint_drift_detected`

### GUI turn payload

```ts
type GuiTurnSubmitPayload = {
  prompt: string;
  providerId: string | null;
  modelId: string | null;
  reasoningEffort: "low" | "medium" | "high" | "ultra";
  permissionMode: "read_only" | "workspace_write" | "full_access";
};
```

Backward compatibility:

- If an older frontend sends only `prompt`, backend defaults `providerId=null`, `modelId=null`, `reasoningEffort="high"`, and `permissionMode="full_access"`.
- In this fallback case the backend emits `runtime_path=legacy_prompt_only`.

### Timeout contract

- Connect timeout: 20 seconds.
- First byte timeout: 30 seconds.
- Idle stream timeout: 60 seconds.
- Total turn timeout: 120 seconds.
- A 401 response triggers one token refresh and one retry.
- A 429 response surfaces `rate_limited` without automatic rapid retries.
- A 5xx response surfaces `direct_route_unavailable`.
- An unrecognized event envelope surfaces `endpoint_drift_detected`.

---

## 8. Implementation Tasks

### Task 0: Golden Fixtures And Structured Secret Scanner

**Files:**

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\response_stream_basic.sse`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\response_stream_error_model_not_supported.sse`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\fixtures\chatgpt_codex_sse\oauth_token_response.example.json`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\scripts\assert_no_real_provider_secret_leaks.py`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_provider_secret_leak_scanner.py`

- [ ] **Step 0.1: Add sanitized SSE fixtures**

`response_stream_basic.sse` must contain real-shaped but fake-safe SSE data:

```text
event: response.created
data: {"type":"response.created","response":{"id":"resp_test_001","model":"gpt-5.5"}}

event: response.output_text.delta
data: {"type":"response.output_text.delta","delta":"OPENHARNESS_"}

event: response.output_text.delta
data: {"type":"response.output_text.delta","delta":"OK"}

event: response.output_text.done
data: {"type":"response.output_text.done","text":"OPENHARNESS_OK"}

event: response.completed
data: {"type":"response.completed","response":{"id":"resp_test_001","status":"completed"}}

data: [DONE]
```

- [ ] **Step 0.2: Add model-not-supported fixture**

`response_stream_error_model_not_supported.sse`:

```text
event: error
data: {"error":{"code":"model_not_supported","message":"The requested test model is not supported for this account."}}
```

- [ ] **Step 0.3: Add fake OAuth token fixture**

`oauth_token_response.example.json`:

```json
{
  "access_token": "test_access_token_value",
  "refresh_token": "test_refresh_token_value",
  "id_token": "test_id_token_value",
  "expires_in": 3600,
  "token_type": "Bearer",
  "account_id": "acct_test_001"
}
```

- [ ] **Step 0.4: Implement structured scanner**

Scanner rules:

- Allow safe field names such as `access_token`, `refresh_token`, and `secret_ref`.
- Fail on `Bearer ` followed by 32 or more token-like characters.
- Fail on `sk-` followed by 20 or more token-like characters.
- Fail on JWT-like three-part token values outside test fixtures.
- Fail on non-redacted email addresses inside `memory`, `agent_memory`, app logs, or diagnostics captures.
- Allow fake values beginning with `test_`.

Run:

```powershell
python learning_agent/scripts/assert_no_real_provider_secret_leaks.py
pytest learning_agent/tests/test_provider_secret_leak_scanner.py -q
```

Expected:

```text
Provider secret leak scan passed.
```

---

### Task 1: V3A Thin Vertical Slice With Fake Token And Fake SSE

**Files:**

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\Composer.tsx`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\AppShell.tsx`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\api\guiClient.ts`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_bridge.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_agent_adapter.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_turn_payload_contract.py`

- [ ] **Step 1.1: Extend GUI turn request with backward compatibility**

Backend request defaults:

```python
provider_id = body.get("providerId") if isinstance(body.get("providerId"), str) else None
model_id = body.get("modelId") if isinstance(body.get("modelId"), str) else None
reasoning_effort = body.get("reasoningEffort") if body.get("reasoningEffort") in {"low", "medium", "high", "ultra"} else "high"
permission_mode = body.get("permissionMode") if body.get("permissionMode") in {"read_only", "workspace_write", "full_access"} else "full_access"
```

- [ ] **Step 1.2: Add a fixture SSE adapter path**

When `OPENHARNESS_OPENAI_RUNTIME=direct_sse_fixture`, the GUI adapter reads `response_stream_basic.sse` and emits streaming GUI deltas. This proves the desktop pipeline before real OAuth.

- [ ] **Step 1.3: Verify selected model reaches backend**

Run:

```powershell
pytest learning_agent/tests/test_gui_turn_payload_contract.py -q
cd apps/desktop
npm test -- --run
```

Expected:

```text
selected provider and model are present in backend request
fixture SSE produces OPENHARNESS_OK through GUI event stream
```

---

### Task 2: V3B OS-Encrypted Secret Store And Real Disconnect Semantics

**Files:**

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_secret_store.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_settings.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_provider_os_secret_store.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_provider_oauth_disconnect.py`

- [ ] **Step 2.1: Add `OsEncryptedSecretStore` with current interface**

Use the existing `GuiProviderSecretStore` interface:

```python
class OsEncryptedSecretStore(GuiProviderSecretStore):
    kind = "os_encrypted"

    def set_secret(self, secret_ref: str, value: str) -> str:
        return self._set_dpapi_current_user_secret(secret_ref, value)

    def get_secret(self, secret_ref: str) -> str:
        return self._get_dpapi_current_user_secret(secret_ref)

    def delete_secret(self, secret_ref: str) -> None:
        self._delete_dpapi_current_user_secret(secret_ref)

    def mask_secret(self, secret_ref: str) -> str:
        return mask_secret_value(self.get_secret(secret_ref))
```

- [ ] **Step 2.2: Add `make_provider_secret_store`**

Factory behavior:

- `OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted` returns `OsEncryptedSecretStore`.
- Empty or `dev_json` returns `DevJsonSecretStore`.
- Real OAuth mode must reject anything except `os_encrypted`.

- [ ] **Step 2.3: Upgrade disconnect to delete OAuth secret ref groups**

Disconnect must delete every ref in:

```json
{
  "secret_refs": {
    "access_token": "provider:openai:access_token",
    "refresh_token": "provider:openai:refresh_token",
    "id_token": "provider:openai:id_token"
  }
}
```

It must also clear selected OpenAI account and selected OpenAI model.

Run:

```powershell
pytest learning_agent/tests/test_gui_provider_os_secret_store.py learning_agent/tests/test_gui_provider_oauth_disconnect.py -q
```

Expected:

```text
plaintext token value is absent from secrets.os.json
disconnect deletes all OAuth token refs
```

---

### Task 3: V3C Real Browser OAuth And Account Discovery

**Files:**

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_openai_oauth.py`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_openai_state.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_auth_attempts.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_settings.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_provider_openai_real_oauth_attempts.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_openai_provider_runtime_state.py`

- [ ] **Step 3.1: Build real browser authorization URL from explicit config**

Required query parameters:

- `response_type=code`
- `client_id` from `OPENHARNESS_OPENAI_CLIENT_ID`
- `redirect_uri` from actual localhost callback port
- `scope=openid profile email offline_access`
- `code_challenge`
- `code_challenge_method=S256`
- `id_token_add_organizations=true`
- `codex_cli_simplified_flow=true`
- `originator=openharness`
- random `state`

- [ ] **Step 3.2: Detect client source**

If configured client id is `app_EMoamEEZ73f0CkXaXp7hrann`, store:

```json
{
  "oauth_client_source": "observed_opencode_reference"
}
```

Otherwise store:

```json
{
  "oauth_client_source": "operator_configured"
}
```

- [ ] **Step 3.3: Add account discovery**

After token exchange:

- Parse safe account id if present.
- Store `account_label` as a redacted label.
- If multiple accounts are discovered, choose the first usable account and store `account_selection_status=auto_selected_first`.
- If endpoint reports account required later, surface `account_selection_required`.

Run:

```powershell
pytest learning_agent/tests/test_gui_provider_openai_real_oauth_attempts.py learning_agent/tests/test_openai_provider_runtime_state.py -q
```

Expected:

```text
wrong OAuth state fails
correct OAuth state stores encrypted refs only
runtime state serializes without token values
```

---

### Task 4: V3D Model Registry, Probe, And Last-Known-Good Cache

**Files:**

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_openai_models.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_provider_settings.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_bridge.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_openai_model_registry.py`

- [ ] **Step 4.1: Add three-layer model source**

Model registry order:

1. `static_known_models`: local display candidates.
2. `probe_available_models`: direct SSE probe results for current account.
3. `last_known_good_models`: cached models that completed at least one real call.

Static candidates:

```python
("gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex-spark")
```

- [ ] **Step 4.2: Add probe result states**

Allowed model states:

- `unknown`
- `available`
- `not_supported_for_account`
- `auth_failed`
- `rate_limited`
- `probe_failed`

- [ ] **Step 4.3: Persist last-known-good models**

Store safe cache under:

```text
memory/gui_provider_settings/openai_model_registry.json
```

The file must not contain token or email values.

Run:

```powershell
pytest learning_agent/tests/test_openai_model_registry.py -q
python learning_agent/scripts/assert_no_real_provider_secret_leaks.py
```

Expected:

```text
model dropdown uses probed models when available
unsupported model shows visible account/model error
```

---

### Task 5: V3E Direct SSE Client And `CodexOAuthChatModel` Migration

**Files:**

- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\chatgpt_codex_sse.py`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\chatgpt_oauth_tokens.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\adapters.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_chatgpt_codex_sse_client.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_codex_oauth_legacy_wrapper.py`

- [ ] **Step 5.1: Move useful SSE parsing concepts into focused client**

`ChatGptCodexSseClient.stream_responses` must:

- POST to `https://chatgpt.com/backend-api/codex/responses`.
- Send `Accept: text/event-stream`.
- Send `Authorization: Bearer access_token_value`.
- Send `ChatGPT-Account-Id` when available.
- Yield `ModelStreamEvent` per text delta.
- Stop on `[DONE]`, `response.output_text.done`, or `response.completed`.
- Surface `endpoint_drift_detected` on unknown envelope shapes.

- [ ] **Step 5.2: Use sanitized fixtures as parser tests**

Run:

```powershell
pytest learning_agent/tests/test_chatgpt_codex_sse_client.py -q
```

Expected:

```text
fixture response_stream_basic.sse yields OPENHARNESS_ then OK before completion
model-not-supported fixture yields model_not_available error
```

- [ ] **Step 5.3: Define legacy wrapper strategy**

`CodexOAuthChatModel` must become one of:

- A wrapper that delegates to `ChatGptCodexSseClient` and buffers for old `chat()` callers.
- A clearly marked legacy class with tests proving old behavior still works.

It must not keep a separate endpoint/parser implementation that diverges from the new client.

---

### Task 6: V3F Real GUI Adapter, Cancellation, And Timeout Lifecycle

**Files:**

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_agent_adapter.py`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_bridge.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_direct_oauth_sse_adapter.py`
- Add `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_gui_direct_oauth_cancel.py`

- [ ] **Step 6.1: Route connected OpenAI OAuth to direct SSE**

Required adapter behavior:

- If provider is disconnected, emit `provider_not_connected`.
- If runtime is `direct_sse`, never call Codex CLI.
- If runtime is `codex_cli`, emit `codex_cli_used=true` before calling Codex CLI.
- If selected model is unsupported, emit `model_not_available`.

- [ ] **Step 6.2: Add cancellation contract**

Cancellation must:

- Close the active HTTP response.
- Emit `turn_cancelled`.
- Preserve partial assistant text as cancelled output.
- Treat completion-before-cancel as completed, not failed.

- [ ] **Step 6.3: Add timeout diagnostics**

Emit timeout class:

- `connect_timeout`
- `first_byte_timeout`
- `idle_stream_timeout`
- `total_turn_timeout`

Run:

```powershell
pytest learning_agent/tests/test_gui_direct_oauth_sse_adapter.py learning_agent/tests/test_gui_direct_oauth_cancel.py -q
```

Expected:

```text
direct mode emits codex_cli_used=false
cancel closes active stream and emits turn_cancelled
```

---

### Task 7: Frontend Provider, Account, Model, And Composer Integration

**Files:**

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\Composer.tsx`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\AppShell.tsx`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\components\settings\SettingsDialog.tsx`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\api\guiClient.ts`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\api\guiProviderTypes.ts`
- Modify `H:\codexworkplace\sofeware\OpenHarness-main\apps\desktop\src\state\providerSettingsStore.ts`

- [ ] **Step 7.1: Submit structured payload**

Composer submit must send:

```json
{
  "prompt": "user text",
  "providerId": "openai",
  "modelId": "gpt-5.5",
  "reasoningEffort": "high",
  "permissionMode": "full_access"
}
```

- [ ] **Step 7.2: Reset model on disconnect**

When OpenAI disconnects:

- selected model becomes `null`.
- model dropdown label becomes `选择模型`.
- composer submit omits provider/model until reconnect.

- [ ] **Step 7.3: Show account and route status safely**

Settings should show:

- connected account hint, redacted.
- direct route status.
- probe state per model.
- no token values.

Run:

```powershell
cd apps/desktop
npm test -- --run
npm run lint
npm run build
```

Expected:

```text
Composer submits selected provider and model
disconnect resets selected model
no frontend snapshot contains token-like values
```

---

### Task 8: Diagnostics, Documentation, And Operator Runbook

**Files:**

- Modify `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\gui_bridge.py`
- Create `H:\codexworkplace\sofeware\OpenHarness-main\docs\desktop\openai-chatgpt-oauth-direct-sse.md`
- Update `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\context.md`
- Update `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\progress.md`
- Update `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\bugs.md` if reproducible bugs are found.

- [ ] **Step 8.1: Emit runtime path before model call**

First turn event must include:

```json
{
  "event_type": "runtime_path",
  "provider_id": "openai",
  "model_id": "gpt-5.5",
  "runtime": "direct_sse",
  "transport": "https_sse",
  "websocket_enabled": false,
  "codex_cli_used": false,
  "oauth_client_source": "operator_configured"
}
```

- [ ] **Step 8.2: Add first-delta latency budget**

Healthy direct SSE target:

- first visible delta under 5 seconds after request send.
- if budget is exceeded, diagnostics record `first_delta_budget_exceeded=true`.

- [ ] **Step 8.3: Write runbook**

Runbook must include:

- Environment gates.
- Why the OpenCode observed client id is a research reference.
- How to connect OAuth.
- How to confirm direct SSE.
- How to interpret route states.
- How to disconnect and clear encrypted tokens.
- How to recover from DPAPI decryption failure.
- How to fall back explicitly to Codex CLI.

Run:

```powershell
python learning_agent/scripts/assert_no_real_provider_secret_leaks.py
rg -n "OPENHARNESS_OPENAI_RUNTIME|direct_sse|codex_cli|os_encrypted|observed_opencode_reference" docs agent_memory learning_agent
```

Expected:

```text
Provider secret leak scan passed.
runbook documents direct_sse and explicit fallback
```

---

### Task 9: Visible GUI Acceptance With Fake And Real Runtime

**Required skills:**

- Use `computer-use:computer-use` for visible GUI control.
- If any bug appears, use `superpowers:systematic-debugging`, fix root cause, and rerun the failed acceptance from the beginning.

**Mandatory visible GUI acceptance gate:**

验收需要使用肉眼可见的真实GUI界面进行验收，使用computer use技能确认和验证，如果验收时出现bug或发现bug时，请使用systematic debugging技能，修复bug，并重新测试，测试通过后继续执行下一个任务。

**Fake fixture acceptance first:**

```powershell
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse_fixture"
$env:OPENHARNESS_GUI_MODEL_TRACE = "1"
```

Acceptance steps:

1. Launch OpenHarness Desktop visible window.
2. Select OpenAI fixture provider and `gpt-5.5`.
3. Send `请输出 OPENHARNESS_OK`.
4. Confirm visible streaming delta appears before completion.
5. Confirm diagnostics show `runtime=direct_sse_fixture`.
6. Click cancel during a second long fixture stream.
7. Confirm visible `turn_cancelled`.

**Real direct SSE acceptance:**

```powershell
$env:OPENHARNESS_OPENAI_AUTH_MODE = "real_browser"
$env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1"
$env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted"
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse"
$env:OPENHARNESS_GUI_MODEL_TRACE = "1"
if (-not $env:OPENHARNESS_OPENAI_CLIENT_ID) { throw "OPENHARNESS_OPENAI_CLIENT_ID must be set explicitly by the operator." }
```

Acceptance steps:

1. Provider starts disconnected.
2. Open settings.
3. Open `提供商`.
4. Click OpenAI `连接`.
5. Choose `ChatGPT Pro/Plus (browser)`.
6. Open browser authorization URL.
7. Complete OAuth.
8. Confirm provider connected.
9. Confirm account hint is redacted.
10. Confirm model dropdown lists probed or last-known-good models.
11. Select one available model.
12. Send `请输出 OPENHARNESS_OK`.
13. Accept final text if it contains `OPENHARNESS_OK` or clearly contains `可用`.
14. Confirm at least one streaming delta arrived before completion.
15. Confirm diagnostics show `runtime=direct_sse`, `transport=https_sse`, `websocket_enabled=false`, and `codex_cli_used=false`.
16. Disconnect OpenAI.
17. Confirm model dropdown resets to `选择模型`.
18. Reconnect OpenAI without restarting the app.

Completion rule:

```text
真实可见 GUI OAuth 验收未完成，不能声明 V3 开发完成。
```

---

## 9. Final Verification Commands

Run these before real GUI acceptance:

```powershell
pytest learning_agent/tests/test_provider_secret_leak_scanner.py -q
pytest learning_agent/tests/test_gui_turn_payload_contract.py -q
pytest learning_agent/tests/test_gui_provider_os_secret_store.py learning_agent/tests/test_gui_provider_oauth_disconnect.py -q
pytest learning_agent/tests/test_gui_provider_openai_real_oauth_attempts.py learning_agent/tests/test_openai_provider_runtime_state.py -q
pytest learning_agent/tests/test_openai_model_registry.py -q
pytest learning_agent/tests/test_chatgpt_codex_sse_client.py learning_agent/tests/test_codex_oauth_legacy_wrapper.py -q
pytest learning_agent/tests/test_gui_direct_oauth_sse_adapter.py learning_agent/tests/test_gui_direct_oauth_cancel.py -q
python learning_agent/scripts/assert_no_real_provider_secret_leaks.py
cd apps/desktop
npm test -- --run
npm run lint
npm run build
```

---

## 10. Expected User-Visible Outcome

After upgraded V3:

- OpenAI provider connect behaves like the OpenCode-style browser OAuth screenshots.
- The connection panel can disconnect and reconnect without app restart.
- The bottom toolbar can select a real available model.
- Selected model id reaches backend and controls the direct SSE request.
- Real responses stream through direct HTTPS/SSE.
- Slow Codex CLI WebSocket retry fallback is no longer hidden in the default real OAuth path.
- Diagnostics make the runtime path visible.
- If the direct endpoint drifts or rejects the account, the GUI shows an actionable direct-route status instead of pretending success.

---

## 11. Final Completion Statement Template

Use this wording only after all automated tests and visible GUI acceptance pass:

```text
OpenHarness Desktop Direct ChatGPT OAuth SSE V3 已完成并通过验收：
- fake fixture vertical slice 证明 GUI selected model payload 和 streaming pipeline 可用。
- OpenAI browser OAuth 真实连接成功。
- 选中的 ChatGPT OAuth 模型通过 direct_sse 真实调用。
- GUI 诊断确认 websocket_enabled=false、codex_cli_used=false。
- cancel、disconnect、reconnect 均通过真实可见 GUI 验收。
```

If visible GUI acceptance cannot be completed, use:

```text
真实可见 GUI OAuth 验收未完成，不能声明 V3 开发完成。
```
