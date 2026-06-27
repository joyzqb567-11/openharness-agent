# OpenHarness Desktop OpenAI ChatGPT OAuth Direct SSE Runbook

This runbook describes the V3 route for OpenHarness Desktop to call ChatGPT OAuth models through direct HTTPS/SSE instead of the slow Codex CLI WebSocket fallback.

## Environment Gates

Use these environment variables before launching the desktop bridge for the real OAuth route:

```powershell
$env:OPENHARNESS_OPENAI_AUTH_MODE = "real_browser"
$env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1"
$env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted"
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse"
$env:OPENHARNESS_GUI_MODEL_TRACE = "1"
```

`OPENHARNESS_OPENAI_CLIENT_ID` must be set explicitly by the operator. Do not hard-code the observed OpenCode client id into source code or docs. The `observed_opencode_reference` label is only a research reference for comparing OpenCode behavior, not a bundled credential.

For fixture-only GUI acceptance, use:

```powershell
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse_fixture"
$env:OPENHARNESS_GUI_MODEL_TRACE = "1"
```

To use the old path on purpose, set:

```powershell
$env:OPENHARNESS_OPENAI_RUNTIME = "codex_cli"
```

That path must be treated as an explicit fallback. It is not the default V3 real OAuth route.

## OAuth Connection Flow

1. Launch OpenHarness Desktop from the current code version.
2. Open `设置`.
3. Open `提供商`.
4. Click `OpenAI` -> `连接`.
5. Choose `ChatGPT Pro/Plus (browser)`.
6. Open the authorization link in the browser.
7. Complete the OpenAI authorization flow.
8. Return to OpenHarness Desktop and wait for the provider row to show connected.

The connected row should show a redacted account hint such as `jo***@example.com`, a route state, and the OAuth client source. It must never show access tokens, refresh tokens, id tokens, secret references, bearer headers, or raw API keys.

## Confirm Direct SSE

Send a short prompt from the composer, for example:

```text
请输出 OPENHARNESS_OK
```

The first diagnostic event for the turn must be `runtime_path` with:

```json
{
  "provider_id": "openai",
  "runtime": "direct_sse",
  "transport": "https_sse",
  "websocket_enabled": false,
  "codex_cli_used": false
}
```

The response should produce at least one visible streaming delta before completion. A healthy first visible delta target is under 5 seconds. If the first delta is slower than that, diagnostics should include:

```json
{
  "first_delta_budget_ms": 5000,
  "first_delta_budget_exceeded": true
}
```

## Route States

`direct_sse_ready` means the OpenAI ChatGPT OAuth token is present in the configured secret store and the GUI can attempt direct HTTPS/SSE.

`mock_only` means the provider is connected only for GUI flow testing. It must not be treated as a real model connection.

`api_key_route` means an OpenAI-compatible API key path is configured. It is not the ChatGPT OAuth Direct SSE path.

`account_selection_required` means the OAuth callback produced an account state that still needs operator action before reliable model calls.

`disconnected` means the provider row or token references are not sufficient for a real model call.

## Model Selection

The composer model dropdown is derived from Provider Settings. If OpenAI disconnects, the dropdown must reset to `选择模型`, and submitted payloads must omit provider/model until reconnect.

Models marked `not_supported_for_account` may be displayed for transparency, but they are disabled in the composer and should not be auto-selected.

Successful Direct SSE calls record the model as last-known-good. Unsupported model errors record the model state so later requests can fail fast without waiting on a slow remote rejection.

## Disconnect And Clear Tokens

Use `设置 -> 提供商 -> OpenAI -> 断开`.

Disconnect must:

- remove the OpenAI auth record from provider settings,
- delete all associated encrypted token entries,
- clear selected OpenAI account fields,
- clear selected OpenAI model fields,
- reset the composer model dropdown to `选择模型`.

After disconnect, a new turn should emit `provider_not_connected` unless the operator reconnects.

## Recover From DPAPI Or OS Secret Store Failure

If `os_encrypted` cannot decrypt the stored value, disconnect OpenAI from the GUI first. Then reconnect through the browser flow.

If the GUI cannot open Provider Settings because the bridge is stale, stop the old desktop bridge process and restart the current worktree bridge. A stale bridge commonly presents as `提供商加载失败` even when the frontend code is correct.

Use `dev_json` only for local tests and fixtures. Real OAuth acceptance should use `os_encrypted`.

## Explicit Codex CLI Fallback

The V3 default real OAuth path is `direct_sse`. The Codex CLI path is available only as an explicit fallback using:

```powershell
$env:OPENHARNESS_OPENAI_RUNTIME = "codex_cli"
```

When selected, diagnostics must show `codex_cli_used=true`. Slow WebSocket retry/fallback behavior should not be hidden as a successful Direct SSE path.

## Acceptance Checklist

- Provider Settings loads without `提供商加载失败`.
- OpenAI connects through `ChatGPT Pro/Plus (browser)`.
- Account hint is redacted.
- Composer dropdown lists available or last-known-good models.
- Submitting a prompt sends the selected provider, model, reasoning effort, and permission mode.
- First diagnostic event is `runtime_path`.
- Direct SSE diagnostics show `transport=https_sse`, `websocket_enabled=false`, and `codex_cli_used=false`.
- At least one visible delta arrives before completion.
- Disconnect resets the model dropdown to `选择模型`.
- Reconnect works without restarting the desktop app.
