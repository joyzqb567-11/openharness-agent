# OpenHarness Desktop Provider Settings V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an OpenCode-style Settings dialog for OpenHarness Desktop, with Provider and Model management mature enough to support real multi-provider connection experiments in a later runtime layer.

**Architecture:** The left-bottom Settings button opens a dedicated React Settings dialog. The dialog reads and writes provider/model state through the existing local GUI bridge. Provider secrets are write-only from the renderer, stored behind a backend secret-store interface, and never returned in bridge payloads, diagnostics, logs, screenshots, or tests. V1 builds the visible shell, provider catalog, auth contract, custom OpenAI-compatible providers, model visibility, and connection probe; real agent inference switching remains a separate Layer C plan.

**Tech Stack:** React 18, Electron, Vite, TypeScript, lucide-react, Python standard-library HTTP bridge, existing OpenHarness `learning_agent.app.gui_bridge`, Vitest, Python unittest/pytest-compatible tests, optional Playwright-style browser automation if available in the desktop QA environment.

---

## Upgrade Note

This blueprint has been upgraded from the Karpathy-style review report:

```text
H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\docs\superpowers\plans\2026-06-26-openharness-desktop-provider-settings-v1-karpathy-review.md
```

The upgrade changes the original plan in six important ways:

- Raw API keys are no longer stored in the main provider settings JSON.
- `custom` is no longer a real provider id. The UI renders a virtual `custom-provider-cta` row, while each saved custom provider gets its own stable id.
- Provider auth methods are object contracts, not string arrays.
- Provider settings include a `test-connection` endpoint before any real runtime switching.
- Visual QA becomes an automated screenshot and DOM assertion gate.
- Secret scanning becomes deterministic and must fail with a non-zero exit code on unsafe leaks.

## Execution Rules From AGENTS.md

All implementation tasks must obey these project rules:

- Read related files before editing.
- Every new or modified code line needs a Chinese comment explaining purpose and consequence.
- Every new or modified function/class block needs a Chinese block-level comment explaining intent, boundaries, and collaboration with other functions.
- Every new or modified code file must be copied into `learning_agent/test/provider_settings_v1/<task_name>/`.
- Maintain `agent_memory/progress.md` for progress and `agent_memory/bugs.md` for discovered risks.
- GUI acceptance must use a real, human-visible desktop GUI window. Automated screenshots, DOM assertions, unit tests, bridge calls, or logs can support acceptance, but they cannot replace the final visible GUI check.
- If any bug or unexpected behavior appears during visible GUI acceptance, immediately use `superpowers:systematic-debugging`: reproduce the issue, gather evidence, identify the root cause, create or update the smallest failing test when possible, fix the root cause, rerun the test, and repeat the visible GUI acceptance before moving to the next task.
- If a task touches the real agent runtime, stop this V1 plan and create a separate Layer C plan.

## Decision Summary

This feature is feasible and worth doing. `D:\opencode` shows a mature user-facing pattern: a vertical settings dialog with Desktop and Server sections, Provider and Model pages, provider catalog state, connected providers, custom OpenAI-compatible providers, and model visibility controls. OpenHarness should reuse the concepts and contracts, not copy the SolidJS implementation directly, because OpenHarness Desktop is React/Electron and uses its own `/v1/gui` and `/v2/gui` bridge.

The left-bottom Settings entry should become the primary settings surface. The existing right-side `SettingsPanel` should remain a diagnostics/local bridge view inside `StatusInspector`, because provider login and model selection need a larger, calmer modal layout.

## Source References

- OpenCode provider UI reference: `D:\opencode\packages\app\src\components\settings-v2\providers.tsx`
- OpenCode models UI reference: `D:\opencode\packages\app\src\components\settings-v2\models.tsx`
- OpenCode provider hook reference: `D:\opencode\packages\app\src\hooks\use-providers.ts`
- OpenCode custom provider flow: `D:\opencode\packages\app\src\components\dialog-custom-provider.tsx`
- OpenCode connect provider flow: `D:\opencode\packages\app\src\components\dialog-connect-provider.tsx`
- OpenHarness sidebar entry: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop\src\components\Sidebar.tsx`
- OpenHarness shell composition: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop\src\components\AppShell.tsx`
- OpenHarness existing diagnostics settings panel: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop\src\components\SettingsPanel.tsx`
- OpenHarness GUI client: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop\src\api\guiClient.ts`
- OpenHarness GUI bridge: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\learning_agent\app\gui_bridge.py`

## Scope Boundaries

In scope:

- Left-bottom Settings opens a dedicated dialog.
- Dialog layout mirrors the screenshots: left navigation, right content, footer version area.
- Navigation sections: Desktop (`通用`, `快捷键`) and Server (`服务器`, `提供商`, `模型`).
- Provider page includes GitHub Copilot, OpenAI, Google, OpenRouter, Vercel AI Gateway, saved custom providers, and one virtual custom-provider CTA row.
- Provider rows show icon, name, short Chinese connection description, source badge, connected state, auth availability, and action button.
- Connect dialog supports only enabled auth methods.
- Custom provider dialog supports provider id, display name, base URL, API key, model rows, and header rows.
- Models page shows provider groups and visibility switches.
- Backend exposes stable `/v2/gui/provider-settings/*` endpoints with `schema_version`.
- Backend redacts secrets in every response and event.
- Backend supports a connection probe endpoint that checks provider reachability without switching the real agent runtime.
- Tests cover provider catalog, secret-store references, auth set/disconnect, custom provider validation, model visibility, connection probe outcomes, client calls, view-model reducers, and visual acceptance.

Out of scope for V1:

- Switching the actual agent inference runtime to OpenAI, Google, OpenRouter, Vercel AI Gateway, Copilot, or custom providers.
- OAuth browser/device flows.
- Billing, token accounting, provider rate-limit management.
- Syncing provider configuration across machines.
- Marketplace discovery beyond the fixed V1 provider catalog.
- Production-grade OS credential storage on every platform.

Layer C trigger:

- If any task changes `GuiAgentAdapter`, `DefaultHarnessGuiAgentAdapter`, prompt execution, model request construction, or actual LLM calls, stop this V1 plan and create a separate real-model-runtime plan. That separate plan must include real provider smoke tests and the project-required visible acceptance gate.

## Provider Settings Invariants

These invariants are non-negotiable. Any task that breaks one of them must stop and repair the plan or implementation before continuing.

1. Raw secrets never leave the backend process after submission.
2. The renderer may send an API key in a POST body, but it must never store that key in React state after the submit resolves.
3. The main provider settings JSON may store `secret_ref`, never raw secret values.
4. `custom-provider-cta` is a virtual UI row, not a provider id.
5. Every saved custom provider uses a real stable id such as `local-openai-compatible`.
6. Provider ids are config keys. Display names are UI labels.
7. Every mutation returns a redacted provider catalog or a redacted mutation summary.
8. `test-connection` can probe provider reachability but cannot alter the real agent runtime.
9. Diagnostics, health, screenshots, event streams, and evidence folders must not contain raw API keys, bearer tokens, or custom header values.
10. If a secure OS credential store is unavailable, the backend must report `secret_store_kind: "dev_json"` so the UI can show a local-development warning.

## Contract Shape

Built-in provider ids:

```text
github-copilot
openai
google
openrouter
vercel
```

Virtual UI-only row id:

```text
custom-provider-cta
```

Provider catalog response:

```json
{
  "ok": true,
  "schema_version": 2,
  "secret_store": {
    "kind": "dev_json",
    "label": "本地开发密钥存储",
    "warning": "当前密钥仅适合本机开发实验，真实生产密钥需要接入系统凭据存储。"
  },
  "providers": [
    {
      "id": "openai",
      "display_name": "OpenAI",
      "kind": "built_in",
      "source": "none",
      "connected": false,
      "masked_key": "",
      "auth_methods": [
        {
          "id": "api_key",
          "label": "API 密钥",
          "enabled": true,
          "status": "available",
          "fields": ["api_key"],
          "help_text": "使用 ChatGPT Pro/Plus 或 API 密钥连接"
        }
      ],
      "description": "使用 ChatGPT Pro/Plus 或 API 密钥连接",
      "models": [
        {
          "id": "gpt-4.1",
          "display_name": "GPT-4.1",
          "provider_id": "openai",
          "visible": true,
          "supports_tools": true,
          "supports_vision": true
        }
      ]
    },
    {
      "id": "github-copilot",
      "display_name": "GitHub Copilot",
      "kind": "built_in",
      "source": "none",
      "connected": false,
      "masked_key": "",
      "auth_methods": [
        {
          "id": "device_code",
          "label": "设备码",
          "enabled": false,
          "status": "unsupported_v1",
          "fields": [],
          "help_text": "V1 只展示入口，不执行 Copilot 登录。"
        }
      ],
      "description": "使用 Copilot 或 API 密钥连接",
      "models": []
    }
  ],
  "custom_provider_cta": {
    "id": "custom-provider-cta",
    "display_name": "自定义提供商",
    "description": "通过基础 URL 添加与 OpenAI 兼容的提供商。"
  },
  "default_provider_id": "",
  "default_model_id": ""
}
```

Mutation request examples:

```json
{
  "provider_id": "openai",
  "auth_method_id": "api_key",
  "fields": {
    "api_key": "unit-test-secret-value"
  }
}
```

```json
{
  "provider_id": "local-openai-compatible",
  "display_name": "Local OpenAI Compatible",
  "base_url": "http://127.0.0.1:11434/v1",
  "auth_method_id": "api_key",
  "fields": {
    "api_key": "unit-test-secret-value"
  },
  "headers": [
    { "key": "X-Test-Header", "value": "unit-test-header-value" }
  ],
  "models": [
    { "id": "local-model", "display_name": "Local Model", "visible": true }
  ]
}
```

Persistence shape for non-secret provider settings:

```json
{
  "auth": {
    "openai": {
      "type": "api_key",
      "secret_ref": "provider:openai:api_key",
      "updated_at": 1782400000.0
    }
  },
  "custom_providers": {
    "local-openai-compatible": {
      "display_name": "Local OpenAI Compatible",
      "base_url": "http://127.0.0.1:11434/v1",
      "secret_ref": "provider:local-openai-compatible:api_key",
      "headers_ref": "provider:local-openai-compatible:headers",
      "models": [
        { "id": "local-model", "display_name": "Local Model", "visible": true }
      ]
    }
  },
  "model_visibility": {
    "openai:gpt-4.1": false
  }
}
```

Security rules:

- Renderer response types must not include `api_key`, `apiKey`, `authorization`, `bearer`, or raw custom header values.
- API key fields are write-only in connect forms.
- Backend responses may return `masked_key`, `connected`, `source`, and `secret_ref_exists`, but not the secret itself.
- Diagnostics and health payloads must not include raw keys, custom headers, or bearer tokens.
- Evidence screenshots may show connected state, but not key text after the user submits.

## File Structure

Create:

- `apps/desktop/src/api/guiProviderTypes.ts`
  Owns provider/model TypeScript types used by the renderer.
- `apps/desktop/src/state/providerSettingsStore.ts`
  Normalizes backend provider payloads into stable camelCase view models and strips unsafe fields.
- `apps/desktop/src/components/settings/SettingsDialog.tsx`
  Owns the modal shell and tab navigation.
- `apps/desktop/src/components/settings/SettingsProvidersPanel.tsx`
  Renders provider rows and opens connect/custom dialogs.
- `apps/desktop/src/components/settings/SettingsModelsPanel.tsx`
  Renders provider-grouped model switches.
- `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
  Collects enabled provider auth fields and submits them to the bridge.
- `apps/desktop/src/components/settings/CustomProviderDialog.tsx`
  Collects OpenAI-compatible custom provider configuration.
- `apps/desktop/src/components/settings/ProviderIcon.tsx`
  Maps provider ids to lucide icons or small text-safe glyphs.
- `apps/desktop/src/styles/settings-dialog.css`
  Defines the OpenCode-like modal layout and responsive behavior.
- `apps/desktop/tests/providerSettingsStore.test.ts`
  Tests renderer normalization, sorting, connected state, and secret redaction.
- `apps/desktop/tests/guiProviderClient.test.ts`
  Tests GUI client endpoint methods and error handling.
- `apps/desktop/tests/settingsDialogViewModel.test.ts`
  Tests tab defaults, disabled auth methods, custom CTA handling, and warning copy.
- `learning_agent/app/gui_provider_secret_store.py`
  Owns `GuiProviderSecretStore`, `DevJsonSecretStore`, secret refs, masking, and safe deletion.
- `learning_agent/app/gui_provider_settings.py`
  Owns provider catalog, custom provider validation, redacted payloads, connection probe orchestration, and local persistence helpers.
- `learning_agent/tests/test_gui_provider_settings_contract.py`
  Tests backend provider-settings routes.
- `learning_agent/tests/test_gui_provider_secret_store.py`
  Tests secret-store behavior without exposing raw secrets.
- `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`
  Runs deterministic leak scanning for release gates.
- `learning_agent/test/provider_settings_v1/scripts/capture_provider_settings_visual_qa.ps1`
  Starts the desktop shell or attaches to an existing renderer and captures visual evidence.

Modify:

- `apps/desktop/src/components/Sidebar.tsx`
  Add `onOpenSettings` prop and wire the bottom settings button.
- `apps/desktop/src/components/AppShell.tsx`
  Own `settingsOpen` state, fetch provider settings, and render `SettingsDialog`.
- `apps/desktop/src/api/guiClient.ts`
  Add provider-settings GET/POST methods.
- `apps/desktop/src/renderer/main.tsx`
  Import `settings-dialog.css`.
- `learning_agent/app/gui_bridge.py`
  Add GET/POST routes under `/v2/gui/provider-settings`.
- `agent_memory/progress.md`
  Record implementation checkpoints.
- `agent_memory/bugs.md`
  Record any secret-redaction or provider-contract risks discovered during implementation.

## Task 0: Provider Settings Invariants and Memory Setup

**Files:**

- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Evidence copy: `learning_agent/test/provider_settings_v1/task00_invariants/`

- [ ] **Step 1: Confirm project memory files exist**

Run:

```powershell
Test-Path agent_memory/context.md
Test-Path agent_memory/progress.md
Test-Path agent_memory/bugs.md
```

Expected: all three commands print `True`.

- [ ] **Step 2: Create missing memory files if any command prints `False`**

Create only the missing file with a short dated heading. Do not overwrite existing project memory.

- [ ] **Step 3: Record Provider Settings V1 invariants**

Append to `agent_memory/context.md`:

```markdown
## 2026-06-26 Provider Settings V1 Invariants

- Provider Settings V1 builds the GUI and bridge contract only.
- Real agent runtime model switching remains Layer C and must use a separate plan.
- Renderer never receives raw provider secrets.
- Main provider settings JSON stores `secret_ref`, not raw secret values.
- `custom-provider-cta` is a virtual UI row, not a provider id.
- Built-in provider ids are `github-copilot`, `openai`, `google`, `openrouter`, and `vercel`.
```

- [ ] **Step 4: Copy memory evidence**

Copy `agent_memory/context.md`, `agent_memory/progress.md`, and `agent_memory/bugs.md` into:

```text
learning_agent/test/provider_settings_v1/task00_invariants/
```

- [ ] **Step 5: Commit Task 0**

Run:

```powershell
git add agent_memory/context.md agent_memory/progress.md agent_memory/bugs.md learning_agent/test/provider_settings_v1/task00_invariants
git commit -m "docs: record provider settings invariants"
```

## Task 1: Backend Provider Catalog and Secret Store Contract

**Files:**

- Create: `learning_agent/app/gui_provider_secret_store.py`
- Create: `learning_agent/app/gui_provider_settings.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Test: `learning_agent/tests/test_gui_provider_secret_store.py`
- Test: `learning_agent/tests/test_gui_provider_settings_contract.py`
- Evidence copy: `learning_agent/test/provider_settings_v1/task01_backend_catalog_secret_store/`

- [ ] **Step 1: Write failing secret-store tests**

Add tests asserting:

- `DevJsonSecretStore.set_secret("provider:openai:api_key", "unit-test-secret-value")` returns a stable ref.
- `get_secret(ref)` returns the secret only inside backend tests.
- `delete_secret(ref)` removes the secret.
- `mask_secret(ref)` returns a masked string and never returns the raw value.
- Secret refs are stored under `memory/gui_provider_settings/secrets.dev.json`.

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py -q
```

Expected: fail with missing module.

- [ ] **Step 2: Write failing provider catalog route test**

Add a test that starts `GuiBridgeServer`, calls `GET /v2/gui/provider-settings/providers`, and asserts:

- HTTP status is 200 with the desktop token.
- Response contains `schema_version: 2`.
- Response contains built-in provider ids `github-copilot`, `openai`, `google`, `openrouter`, and `vercel`.
- Response contains `custom_provider_cta.id == "custom-provider-cta"`.
- Response does not include a real provider id named `custom`.
- Every provider has `connected`, `source`, `auth_methods`, and `models`.
- `github-copilot` has no enabled auth method in V1.
- Response text does not contain `api_key`, `unit-test-secret-value`, `Authorization`, or `Bearer`.

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: fail with route not found or import missing.

- [ ] **Step 3: Implement `gui_provider_secret_store.py`**

Implement:

- `GuiProviderSecretStore`
- `DevJsonSecretStore`
- `secret_settings_dir(workspace)`
- `safe_secret_ref(provider_id, secret_name)`
- `mask_secret_value(value)`

Required behavior:

- Write secrets to `memory/gui_provider_settings/secrets.dev.json`.
- Use atomic write: write to a temporary file, then replace the target file.
- Use a module-level `threading.Lock` for writes.
- Never print, log, or return raw secret values outside `get_secret()`.
- If the JSON file is corrupt, rename it to `secrets.dev.json.corrupt-<timestamp>` and continue with an empty store.

- [ ] **Step 4: Implement `gui_provider_settings.py` catalog helpers**

Implement:

- `GuiAuthMethodInfo`
- `GuiModelInfo`
- `GuiProviderInfo`
- `provider_settings_dir(workspace)`
- `provider_settings_file(workspace)`
- `load_provider_settings(workspace)`
- `save_provider_settings(workspace, data)`
- `build_provider_settings_payload(workspace)`
- `redact_provider_payload(payload)`

Required behavior:

- Built-in providers are returned even when no config file exists.
- `vercel` is the config id and `Vercel AI Gateway` is the display name.
- `custom_provider_cta` is returned separately from `providers`.
- Unknown fields in JSON files are ignored.
- `save_provider_settings()` uses atomic write and a module-level lock.
- JSON corruption creates `providers.json.corrupt-<timestamp>` and returns a safe empty config.

- [ ] **Step 5: Wire GET route in `gui_bridge.py`**

Add route:

```text
GET /v2/gui/provider-settings/providers
```

The route must:

- Require the same desktop token as other `/v2/gui/*` routes.
- Call `build_provider_settings_payload(self.server.workspace)`.
- Return JSON with `ok: true`.
- Return structured bridge errors if loading fails.

- [ ] **Step 6: Run backend catalog and secret-store tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: pass.

- [ ] **Step 7: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task01_backend_catalog_secret_store/
```

Commit:

```powershell
git add learning_agent/app/gui_provider_secret_store.py learning_agent/app/gui_provider_settings.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/test/provider_settings_v1/task01_backend_catalog_secret_store
git commit -m "feat: add provider settings catalog and secret store"
```

## Task 2: Provider Auth, Disconnect, Custom Provider, and Model Visibility

**Files:**

- Modify: `learning_agent/app/gui_provider_secret_store.py`
- Modify: `learning_agent/app/gui_provider_settings.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Test: `learning_agent/tests/test_gui_provider_secret_store.py`
- Test: `learning_agent/tests/test_gui_provider_settings_contract.py`
- Evidence copy: `learning_agent/test/provider_settings_v1/task02_provider_mutations/`

- [ ] **Step 1: Add failing tests for mutations**

Add tests for:

- `POST /v2/gui/provider-settings/auth` with `{ "provider_id": "openai", "auth_method_id": "api_key", "fields": { "api_key": "unit-test-secret-value" } }`.
- `POST /v2/gui/provider-settings/disconnect` with `{ "provider_id": "openai" }`.
- `POST /v2/gui/provider-settings/custom-provider` with provider id, display name, base URL, API key, model rows, and headers.
- `POST /v2/gui/provider-settings/model-visibility` with `{ "provider_id": "openai", "model_id": "gpt-4.1", "visible": false }`.

Assertions:

- Auth response returns `connected: true`.
- Main settings JSON contains `secret_ref` and does not contain `unit-test-secret-value`.
- Secret-store JSON is the only file allowed to contain the test secret.
- Catalog after auth returns `masked_key`, not the raw key.
- Disconnect returns `connected: false` and deletes the secret ref.
- Custom provider id `custom` returns 400 with code `reserved_provider_id`.
- Invalid custom provider id returns 400 with code `invalid_provider_id`.
- Invalid base URL returns 400 with code `invalid_base_url`.
- Model visibility persists across a new `GuiBridgeServer` instance using the same workspace.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: mutation routes fail because they do not exist.

- [ ] **Step 3: Implement backend mutation helpers**

Implement:

- `set_provider_auth(workspace, provider_id, auth_method_id, fields)`
- `disconnect_provider(workspace, provider_id)`
- `save_custom_provider(workspace, payload)`
- `set_model_visibility(workspace, provider_id, model_id, visible)`
- `validate_provider_id(value)`
- `validate_custom_provider_id(value)`
- `validate_base_url(value)`
- `sanitize_header_rows(rows, secret_store, provider_id)`
- `sanitize_model_rows(rows)`

Validation rules:

- Built-in provider ids are only `github-copilot`, `openai`, `google`, `openrouter`, and `vercel`.
- Custom provider id must match `^[a-z0-9][a-z0-9-]{1,62}$`.
- Custom provider id must not equal a built-in id.
- Custom provider id must not equal `custom` or `custom-provider-cta`.
- Base URL must start with `http://` or `https://`.
- Header keys must be non-empty printable strings without newline characters.
- At least one model row must contain both `id` and `display_name`.

- [ ] **Step 4: Wire POST routes in `gui_bridge.py`**

Add:

```text
POST /v2/gui/provider-settings/auth
POST /v2/gui/provider-settings/disconnect
POST /v2/gui/provider-settings/custom-provider
POST /v2/gui/provider-settings/model-visibility
```

Each route must:

- Parse JSON through the existing bridge body reader.
- Return structured errors through the existing GUI bridge error path.
- Return redacted provider payload or mutation summary.
- Require desktop token.

- [ ] **Step 5: Run backend mutation tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: pass.

- [ ] **Step 6: Update `agent_memory/bugs.md` if a redaction edge is found**

Add a dated note only if testing discovers a secret exposure path. The note must include endpoint, observed leak shape, root cause, and fix.

- [ ] **Step 7: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task02_provider_mutations/
```

Commit:

```powershell
git add learning_agent/app/gui_provider_secret_store.py learning_agent/app/gui_provider_settings.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/test/provider_settings_v1/task02_provider_mutations agent_memory/bugs.md
git commit -m "feat: persist desktop provider settings safely"
```

## Task 3: Provider Connection Probe Contract

**Files:**

- Modify: `learning_agent/app/gui_provider_settings.py`
- Modify: `learning_agent/app/gui_bridge.py`
- Test: `learning_agent/tests/test_gui_provider_settings_contract.py`
- Evidence copy: `learning_agent/test/provider_settings_v1/task03_connection_probe/`

- [ ] **Step 1: Add failing connection probe tests**

Add tests for:

- `POST /v2/gui/provider-settings/test-connection` with OpenAI-compatible provider and a fake local `/models` server returning 200.
- Unsupported GitHub Copilot probe returning `{ "ok": false, "status": "unsupported" }`.
- Missing secret returning `{ "ok": false, "status": "missing_secret" }`.
- Network failure returning `{ "ok": false, "status": "network_failed" }`.

Assertions:

- Probe never writes `default_provider_id`.
- Probe never changes model visibility.
- Probe response does not include raw secrets or request headers.

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: test-connection route fails because it does not exist.

- [ ] **Step 3: Implement probe helpers**

Implement:

- `test_provider_connection(workspace, provider_id)`
- `probe_openai_compatible_models(base_url, api_key, headers, timeout_seconds)`
- `build_probe_result(provider_id, status, message, models_count)`

Probe behavior:

- Built-in `openai`, `openrouter`, `vercel`, and custom providers use an OpenAI-compatible `GET /models` probe.
- `google` returns `unsupported` in V1 unless a Gemini-compatible probe is explicitly added in this task.
- `github-copilot` returns `unsupported`.
- Timeout is 5 seconds.
- Response statuses are exactly `ok`, `auth_failed`, `missing_secret`, `network_failed`, `unsupported`, and `invalid_config`.

- [ ] **Step 4: Wire POST route**

Add:

```text
POST /v2/gui/provider-settings/test-connection
```

Request shape:

```json
{ "provider_id": "openai" }
```

Response shape:

```json
{
  "ok": true,
  "schema_version": 2,
  "provider_id": "openai",
  "status": "ok",
  "message": "连接测试通过",
  "models_count": 42
}
```

- [ ] **Step 5: Run probe tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_settings_contract.py -q
```

Expected: pass.

- [ ] **Step 6: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task03_connection_probe/
```

Commit:

```powershell
git add learning_agent/app/gui_provider_settings.py learning_agent/app/gui_bridge.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/test/provider_settings_v1/task03_connection_probe
git commit -m "feat: add provider connection probe contract"
```

## Task 4: Renderer Provider Types, Client Methods, and Store

**Files:**

- Create: `apps/desktop/src/api/guiProviderTypes.ts`
- Modify: `apps/desktop/src/api/guiClient.ts`
- Create: `apps/desktop/src/state/providerSettingsStore.ts`
- Test: `apps/desktop/tests/guiProviderClient.test.ts`
- Test: `apps/desktop/tests/providerSettingsStore.test.ts`
- Test: `apps/desktop/tests/settingsDialogViewModel.test.ts`
- Evidence copy: `learning_agent/test/provider_settings_v1/task04_renderer_contract/`

- [ ] **Step 1: Write failing GUI client tests**

Test these client methods:

- `providerSettings()`
- `connectProvider(providerId, authMethodId, fields)`
- `disconnectProvider(providerId)`
- `saveCustomProvider(payload)`
- `setModelVisibility(providerId, modelId, visible)`
- `testProviderConnection(providerId)`

Each method must hit the exact `/v2/gui/provider-settings/*` path and include `X-OpenHarness-Desktop-Token`.

- [ ] **Step 2: Write failing store tests**

Test that the store:

- Sorts connected providers before popular disconnected providers.
- Keeps the virtual `customProviderCta` after real providers.
- Groups models by provider id.
- Converts missing `models` to an empty array.
- Converts backend snake_case to frontend camelCase.
- Rejects or strips `api_key`, `apiKey`, `authorization`, `Authorization`, `bearer`, and `Bearer` fields if a backend bug sends one.
- Marks `github-copilot` connection action disabled because its V1 auth method is unsupported.

- [ ] **Step 3: Run frontend tests and confirm failure**

Run:

```powershell
cd apps/desktop
npm test -- --run tests/guiProviderClient.test.ts tests/providerSettingsStore.test.ts tests/settingsDialogViewModel.test.ts
```

Expected: fail because files and methods do not exist.

- [ ] **Step 4: Add TypeScript provider types**

Create stable exported types:

- `GuiProviderAuthMethodStatus`
- `GuiProviderAuthMethod`
- `GuiProviderSource`
- `GuiProviderKind`
- `GuiSecretStoreInfo`
- `GuiModelInfo`
- `GuiProviderInfo`
- `GuiCustomProviderCta`
- `GuiProviderSettingsPayload`
- `ConnectProviderRequest`
- `CustomProviderRequest`
- `ModelVisibilityRequest`
- `ProviderConnectionProbePayload`

Renderer type rule:

- No response type may include a raw `apiKey` property.
- Request-only types may include `apiKey` only inside submitted form fields.
- React components consume camelCase view models, not raw snake_case backend objects.

- [ ] **Step 5: Extend `createGuiClient`**

Add methods to the returned client object:

```typescript
providerSettings(): Promise<GuiProviderSettingsPayload>
connectProvider(providerId: string, authMethodId: string, fields: Record<string, string>): Promise<GuiProviderSettingsPayload>
disconnectProvider(providerId: string): Promise<GuiProviderSettingsPayload>
saveCustomProvider(payload: CustomProviderRequest): Promise<GuiProviderSettingsPayload>
setModelVisibility(providerId: string, modelId: string, visible: boolean): Promise<GuiProviderSettingsPayload>
testProviderConnection(providerId: string): Promise<ProviderConnectionProbePayload>
```

- [ ] **Step 6: Implement store normalization**

Create functions:

- `buildProviderSettingsViewModel(payload)`
- `providerRowsForDisplay(viewModel)`
- `modelGroupsForDisplay(viewModel)`
- `redactedProviderPayload(payload)`
- `isUnsafeProviderPayloadKey(key)`

The store must never retain `api_key`, `apiKey`, `authorization`, `Authorization`, `bearer`, or `Bearer` fields from backend payloads.

- [ ] **Step 7: Run frontend tests**

Run:

```powershell
cd apps/desktop
npm test -- --run tests/guiProviderClient.test.ts tests/providerSettingsStore.test.ts tests/settingsDialogViewModel.test.ts
```

Expected: pass.

- [ ] **Step 8: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task04_renderer_contract/
```

Commit:

```powershell
git add apps/desktop/src/api/guiProviderTypes.ts apps/desktop/src/api/guiClient.ts apps/desktop/src/state/providerSettingsStore.ts apps/desktop/tests/guiProviderClient.test.ts apps/desktop/tests/providerSettingsStore.test.ts apps/desktop/tests/settingsDialogViewModel.test.ts learning_agent/test/provider_settings_v1/task04_renderer_contract
git commit -m "feat: add desktop provider settings renderer contract"
```

## Task 5: Settings Dialog Shell and Sidebar Trigger

**Files:**

- Modify: `apps/desktop/src/components/Sidebar.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Create: `apps/desktop/src/components/settings/SettingsDialog.tsx`
- Create: `apps/desktop/src/styles/settings-dialog.css`
- Modify: `apps/desktop/src/renderer/main.tsx`
- Evidence copy: `learning_agent/test/provider_settings_v1/task05_settings_shell/`

- [ ] **Step 1: Add `onOpenSettings` prop to `Sidebar`**

Acceptance:

- Bottom settings button calls `onOpenSettings`.
- Existing quick chat, search, archived, and session selection behavior remains unchanged.

- [ ] **Step 2: Add `settingsOpen` state in `AppShell`**

Acceptance:

- `AppShell` passes `onOpenSettings={() => setSettingsOpen(true)}` to `Sidebar`.
- `AppShell` renders `SettingsDialog` after `PermissionDialog`, so it overlays the full app.
- `Escape` and close button close the dialog.

- [ ] **Step 3: Build the dialog shell**

The dialog must include:

- Left nav width close to screenshots.
- Sections `桌面` and `服务器`.
- Tabs `通用`, `快捷键`, `服务器`, `提供商`, `模型`.
- Footer text `OpenHarness Desktop` and package version `v0.1.0` from `apps/desktop/package.json`.
- Default active tab `提供商`.
- Secret store warning area that appears only when `secret_store.kind === "dev_json"`.

- [ ] **Step 4: Add CSS**

CSS requirements:

- White/light panel with subtle border.
- No nested card-in-card layout.
- Fixed dialog max width around 980px and max height around 720px.
- Mobile width collapses nav above content.
- Buttons do not resize when labels change.
- Text does not overflow provider rows.

- [ ] **Step 5: Import CSS in renderer**

Import `../styles/settings-dialog.css` from `apps/desktop/src/renderer/main.tsx`.

- [ ] **Step 6: Run frontend build and lint**

Run:

```powershell
cd apps/desktop
npm run lint
npm run build
```

Expected: both pass.

- [ ] **Step 7: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task05_settings_shell/
```

Commit:

```powershell
git add apps/desktop/src/components/Sidebar.tsx apps/desktop/src/components/AppShell.tsx apps/desktop/src/components/settings/SettingsDialog.tsx apps/desktop/src/styles/settings-dialog.css apps/desktop/src/renderer/main.tsx learning_agent/test/provider_settings_v1/task05_settings_shell
git commit -m "feat: open desktop settings dialog from sidebar"
```

## Task 6: Providers Panel, Auth Method Handling, and Connect Dialog

**Files:**

- Create: `apps/desktop/src/components/settings/SettingsProvidersPanel.tsx`
- Create: `apps/desktop/src/components/settings/ProviderConnectDialog.tsx`
- Create: `apps/desktop/src/components/settings/ProviderIcon.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsDialog.tsx`
- Evidence copy: `learning_agent/test/provider_settings_v1/task06_providers_panel/`

- [ ] **Step 1: Render provider list from backend payload**

Provider row acceptance:

- Icon on the left.
- Provider display name in bold.
- Description below provider name.
- Connected provider shows `已连接`.
- Env/config/custom/API source shows a small badge.
- Disconnected provider with enabled auth method shows `+ 连接`.
- Provider without enabled auth method shows disabled `暂未支持`.
- Connected provider shows `断开` unless source is `env`.
- Virtual `customProviderCta` row opens the custom provider dialog and never calls mutation endpoints as a provider id.

- [ ] **Step 2: Add loading and error states**

States:

- Loading text: `正在加载提供商`
- Empty text: `暂无提供商`
- Error text: `提供商加载失败`
- Retry button calls `providerSettings()` again.

- [ ] **Step 3: Build connect dialog**

Dialog behavior:

- Title uses selected provider display name.
- Only enabled auth methods can be submitted.
- API key input type is `password`.
- Submit button disabled when trimmed key is empty.
- On submit, call `connectProvider(provider.id, "api_key", { api_key: apiKey })`.
- Clear local API key state immediately after successful submit.
- After success, return to provider list with refreshed payload.
- If backend fails, show structured message without logging the key.

- [ ] **Step 4: Add connection probe button**

Behavior:

- Connected providers show `测试连接`.
- Click calls `testProviderConnection(provider.id)`.
- Probe result shows one of these messages:
  - `连接测试通过`
  - `认证失败`
  - `缺少密钥`
  - `网络不可达`
  - `暂不支持测试`
  - `配置无效`
- Probe result must not display base URL headers or raw key text.

- [ ] **Step 5: Run frontend checks**

Run:

```powershell
cd apps/desktop
npm run lint
npm test -- --run tests/providerSettingsStore.test.ts tests/guiProviderClient.test.ts tests/settingsDialogViewModel.test.ts
```

Expected: pass.

- [ ] **Step 6: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task06_providers_panel/
```

Commit:

```powershell
git add apps/desktop/src/components/settings/SettingsProvidersPanel.tsx apps/desktop/src/components/settings/ProviderConnectDialog.tsx apps/desktop/src/components/settings/ProviderIcon.tsx apps/desktop/src/components/settings/SettingsDialog.tsx learning_agent/test/provider_settings_v1/task06_providers_panel
git commit -m "feat: add desktop provider connection panel"
```

## Task 7: Custom Provider Dialog

**Files:**

- Create: `apps/desktop/src/components/settings/CustomProviderDialog.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsProvidersPanel.tsx`
- Evidence copy: `learning_agent/test/provider_settings_v1/task07_custom_provider/`

- [ ] **Step 1: Build form state**

Fields:

- Provider ID
- Display name
- Base URL
- API key
- Models with id and display name
- Headers with key and value

Validation:

- Provider ID must match `^[a-z0-9][a-z0-9-]{1,62}$`.
- Provider ID must not be `custom`, `custom-provider-cta`, `github-copilot`, `openai`, `google`, `openrouter`, or `vercel`.
- Base URL must start with `http://` or `https://`.
- At least one model row must have id and display name.
- Empty header rows are ignored.

- [ ] **Step 2: Save through GUI client**

On save:

- Call `saveCustomProvider(payload)`.
- Clear API key and header value state after success.
- Close dialog and refresh provider catalog.

- [ ] **Step 3: Add visible error copy**

Use these exact messages:

- `Provider ID 只能使用小写字母、数字和短横线`
- `Provider ID 已被系统保留`
- `Base URL 必须以 http:// 或 https:// 开头`
- `至少填写一个模型`
- `保存自定义提供商失败`

- [ ] **Step 4: Run checks**

Run:

```powershell
cd apps/desktop
npm run lint
npm run build
```

Expected: pass.

- [ ] **Step 5: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task07_custom_provider/
```

Commit:

```powershell
git add apps/desktop/src/components/settings/CustomProviderDialog.tsx apps/desktop/src/components/settings/SettingsProvidersPanel.tsx learning_agent/test/provider_settings_v1/task07_custom_provider
git commit -m "feat: add custom desktop provider dialog"
```

## Task 8: Models Panel and Visibility Switches

**Files:**

- Create: `apps/desktop/src/components/settings/SettingsModelsPanel.tsx`
- Modify: `apps/desktop/src/components/settings/SettingsDialog.tsx`
- Evidence copy: `learning_agent/test/provider_settings_v1/task08_models_panel/`

- [ ] **Step 1: Render grouped models**

Acceptance:

- Group by provider display name.
- Connected providers appear before disconnected providers.
- Each model row shows model display name, model id, provider display name, and visibility switch.
- Empty state says `连接提供商后会在这里显示模型`.

- [ ] **Step 2: Wire visibility switch**

Behavior:

- Toggle calls `setModelVisibility(providerId, modelId, visible)`.
- Switch enters pending state while request is running.
- On success, refreshes provider payload.
- On failure, reverts visible state and shows `模型可见性保存失败`.

- [ ] **Step 3: Run checks**

Run:

```powershell
cd apps/desktop
npm run lint
npm run build
```

Expected: pass.

- [ ] **Step 4: Copy changed files and commit**

Copy changed files to:

```text
learning_agent/test/provider_settings_v1/task08_models_panel/
```

Commit:

```powershell
git add apps/desktop/src/components/settings/SettingsModelsPanel.tsx apps/desktop/src/components/settings/SettingsDialog.tsx learning_agent/test/provider_settings_v1/task08_models_panel
git commit -m "feat: add desktop model visibility settings"
```

## Task 9: Automated Settings Dialog Visual QA

**Files:**

- Modify: `apps/desktop/src/styles/settings-dialog.css`
- Create: `learning_agent/test/provider_settings_v1/scripts/capture_provider_settings_visual_qa.ps1`
- Create evidence screenshots under: `learning_agent/test/provider_settings_v1/task09_visual_qa/`

- [ ] **Step 1: Start backend and desktop shell**

Run:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1
apps\desktop\scripts\start-backend.ps1
```

Then run in another shell:

```powershell
cd H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\apps\desktop
npm run desktop:dev
```

- [ ] **Step 2: Create visual QA script**

The script must capture these viewports:

```text
1365x768
980x720
390x844
```

The script must assert:

- Settings dialog is visible after clicking left-bottom `设置`.
- Provider row count is at least 5.
- `custom-provider-cta` row is visible.
- GitHub Copilot action is disabled in V1.
- API key input has `type="password"`.
- No element text contains `unit-test-secret-value`.
- `document.documentElement.scrollWidth <= window.innerWidth + 2` for mobile viewport.

- [ ] **Step 3: Capture visual states**

Capture:

- Settings dialog default provider page.
- Connected OpenAI state after entering `unit-test-secret-value`.
- Custom provider dialog.
- Models tab with at least one provider group.
- Mobile-width rendering around 390px.

Save screenshots to:

```text
learning_agent/test/provider_settings_v1/task09_visual_qa/
```

- [ ] **Step 4: Visual acceptance checklist**

Pass criteria:

- Dialog resembles the attached OpenCode screenshots in structure.
- Provider rows align cleanly.
- Settings nav has selected state.
- No text overlaps on desktop or mobile.
- API key field is empty or masked after submit.
- No raw secret appears in screenshot, DOM text, console, or bridge response.

- [ ] **Step 5: Complete real human-visible GUI acceptance**

Acceptance method:

- Open the actual Electron desktop window on the local machine.
- Click the left-bottom `设置` button with the visible GUI.
- Inspect the `提供商` tab with human eyes.
- Open the connect dialog for an enabled provider and confirm the API key field is masked.
- Open the `自定义提供商` dialog and confirm fields, buttons, validation copy, and spacing are readable.
- Open the `模型` tab and confirm model rows and switches are visible without overlap.
- Resize the visible window to a narrow width close to mobile layout and confirm the dialog remains usable.

Bug handling rule:

- If any visible GUI bug, layout bug, interaction bug, error state, missing state, or unexpected behavior appears, stop the task immediately.
- Use `superpowers:systematic-debugging` before changing code.
- Record the reproduction steps, observed evidence, root cause, fix, and retest result in `learning_agent/test/provider_settings_v1/task09_visual_qa/gui_bug_notes.md`.
- Rerun the automated visual QA script and repeat the real visible GUI acceptance.
- Continue to the next task only after the automated checks and the real visible GUI acceptance both pass.

- [ ] **Step 6: Commit visual CSS and evidence**

Run:

```powershell
git add apps/desktop/src/styles/settings-dialog.css learning_agent/test/provider_settings_v1/scripts/capture_provider_settings_visual_qa.ps1 learning_agent/test/provider_settings_v1/task09_visual_qa
git commit -m "test: capture provider settings visual acceptance"
```

## Task 10: Full Release Gate

**Files:**

- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md` only if unresolved risks exist.
- Create: `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`
- Evidence copy: `learning_agent/test/provider_settings_v1/task10_release_gate/`

- [ ] **Step 1: Run backend tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_diagnostics_contract.py learning_agent/tests/test_gui_bridge_security_contract.py -q
```

Expected: pass.

- [ ] **Step 2: Run frontend tests**

Run:

```powershell
cd apps/desktop
npm test
```

Expected: pass.

- [ ] **Step 3: Run frontend lint and build**

Run:

```powershell
cd apps/desktop
npm run lint
npm run build
```

Expected: pass.

- [ ] **Step 4: Create deterministic secret leak scan**

Create `learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`.

The script must:

- Search `learning_agent` and `apps/desktop`.
- Fail on `sk-` followed by 12 or more alphanumeric characters.
- Fail on `Authorization:` followed by `Bearer`.
- Fail on `api_key` and `sk-` appearing on the same line.
- Ignore `.png` screenshots and `.map` files.
- Allow the literal string `unit-test-secret-value` only in test files and this plan's evidence folders.

Required commands inside the script:

```powershell
rg -n --glob '!*.png' --glob '!*.map' 'sk-[A-Za-z0-9]{12,}|Authorization:\s*Bearer|api_key.*sk-' learning_agent apps/desktop
rg -n 'unit-test-secret-value' learning_agent apps/desktop
```

The first command must have zero matches. The second command may match only test files, visual QA fixture files, or evidence copies.

- [ ] **Step 5: Run secret leak scan**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1
```

Expected: exit code 0.

- [ ] **Step 6: Run visual QA script**

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/capture_provider_settings_visual_qa.ps1
```

Expected: screenshots and assertion report are written to `learning_agent/test/provider_settings_v1/task09_visual_qa/`.

- [ ] **Step 7: Record progress**

Append to `agent_memory/progress.md`:

```markdown
## 2026-06-26 Provider Settings V1

- Completed OpenCode-style provider settings dialog.
- Completed provider catalog, auth, custom provider, disconnect, model visibility, and connection probe bridge contract.
- Completed backend secret-store abstraction with redacted renderer payloads.
- Completed renderer client/store/components and visual screenshots.
- Real model runtime switching remains Layer C and is intentionally not part of V1.
```

- [ ] **Step 8: Final commit**

Run:

```powershell
git add agent_memory/progress.md agent_memory/bugs.md learning_agent/test/provider_settings_v1
git commit -m "chore: complete provider settings v1 release gate"
```

## Final Acceptance Matrix

Layer A, visual:

- User clicks left-bottom `设置`.
- Settings dialog opens.
- Provider page visually matches the provided OpenCode-style screenshots.
- GitHub Copilot appears but is disabled for V1 login.
- OpenAI/OpenRouter/Vercel/custom API key flows are available through enabled auth methods.
- Models tab is visible and usable.
- Custom provider dialog is usable.
- Mobile viewport has no horizontal overflow.

Layer B, contract:

- `/v2/gui/provider-settings/providers` returns redacted catalog.
- Auth, disconnect, custom provider, model visibility, and test-connection routes pass tests.
- Main settings JSON stores `secret_ref`, not raw key text.
- Renderer client and store tests pass.
- Desktop build and lint pass.
- Automated visual QA passes.
- A real human-visible Electron GUI acceptance pass is completed after automated checks.
- Any bug found during visible GUI acceptance is handled through `superpowers:systematic-debugging`, fixed at root cause, retested, and recorded before proceeding.
- Secret leak scan exits with code 0.

Layer C, real model runtime:

- Not triggered in V1.
- Any real LLM request integration must be handled by a separate plan that changes the actual `GuiAgentAdapter` or model execution path.

## Self-Review

Spec coverage:

- OpenCode-style settings page is covered by Tasks 5, 6, 7, 8, and 9.
- Multi-provider future connection foundation is covered by Tasks 1, 2, 3, and 4.
- Secret safety is covered by Tasks 1, 2, 4, 6, 7, 9, and 10.
- Connection testing is covered by Task 3 and Task 6.
- Real model experimentation is scoped as a future Layer C plan, not mixed into V1.

Placeholder scan:

- This plan contains no forbidden placeholder markers and no undefined task owner.
- The plan avoids vague implementation language by naming validation rules, endpoint paths, commands, and expected outcomes.

Type consistency:

- Built-in provider ids are `github-copilot`, `openai`, `google`, `openrouter`, and `vercel`.
- `custom-provider-cta` is consistently virtual and never used as a provider id.
- Renderer and backend endpoints consistently use `/v2/gui/provider-settings/*`.
- Backend raw payloads use snake_case; frontend view models use camelCase after `providerSettingsStore.ts` normalization.
