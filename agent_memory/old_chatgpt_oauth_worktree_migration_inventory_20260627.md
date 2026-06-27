# 2026-06-27 Old ChatGPT OAuth Worktree Migration Inventory

## Scope

- Audited worktree: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\chatgpt-oauth-real-model-v1`
- Mainline: `H:\codexworkplace\sofeware\OpenHarness-main` on `codex/publish-main`
- Audit purpose: decide what, if anything, should be migrated before deleting the old worktree.
- Safety rule: do not copy, stash, commit, or quote local OAuth tokens, local secret files, runtime memory, or raw GUI logs.

## Evidence Snapshot

- Old branch commit `026d2ba0` is already an ancestor of `codex/publish-main`.
- Old worktree still has 34 tracked files with uncommitted modifications.
- Old worktree still has 87 untracked files.
- 83 untracked files are missing from mainline.
- 4 untracked files exist in mainline but differ in content.
- No real running process was found using the old worktree path; the blocker is unreviewed file content, not process ownership.

## Do Not Bulk Merge

- Do not merge the old worktree as a whole.
- Reason: mainline already contains later Direct ChatGPT OAuth SSE, callback handling, context compaction, provider settings, model registry, and real model observability work.
- Risk: bulk merge would mix older provider settings code with newer mainline code and can regress the working Desktop GUI path.

## Already Covered By Mainline

- `apps/desktop/src/components/ModelCallStatus.tsx`
  - Mainline now has a cleaner observability component from `codex/real-model-observability-v1`.
- `apps/desktop/tests/modelCallStatus.test.tsx`
  - Mainline now covers model call labels, latest status extraction, and reducer handling.
- `learning_agent/app/gui_provider_openai_oauth.py`
  - Mainline already has the production OAuth code exchange and token storage path through the current provider settings architecture.
- Direct SSE runtime events
  - Mainline already emits `runtime_path`, `model_call_started`, `model_first_delta`, `model_call_completed`, `model_call_failed`, `direct_sse_completed`, and message events.

## Candidate: Preserve As Reference, Not Direct Merge

- `learning_agent/app/gui_model_latency_diagnostics.py`
  - Value: contains an async transport diagnostics cache and parser for WebSocket timeout / HTTPS fallback text.
  - Current decision: do not merge now; mainline uses Direct SSE observability instead of old Codex CLI WebSocket fallback.
  - Future use: if a Diagnostics tab needs transport doctor snapshots, reimplement behind current mainline contracts with fresh TDD.

- `learning_agent/tests/test_gui_model_latency_diagnostics.py`
  - Value: good test ideas for non-blocking diagnostics cache, TTL refresh, and timeout safety.
  - Current decision: preserve as reference only.
  - Future use: adapt selected test cases if diagnostics cache becomes a mainline feature.

- `learning_agent/models/streaming.py`
  - Value: generic streaming chat model protocol.
  - Current decision: do not merge now; mainline Direct SSE adapter already has a concrete event contract.
  - Future use: revisit only if OpenHarness standardizes all providers behind one streaming interface.

- `learning_agent/models/codex_cli_stream.py`
  - Value: Codex CLI fallback runner with observable phases, final-output fallback, and cancellation tests.
  - Current decision: do not merge now; mainline V3 intentionally prefers direct ChatGPT OAuth SSE and leaves Codex CLI fallback explicit.
  - Future use: separate blueprint if the product wants a supported Codex CLI fallback runtime.

- `apps/desktop/tests/realModelLatencyEvents.test.ts`
  - Value: includes extra frontend tests for latency event interpretation and cancel-request feedback.
  - Current decision: partial idea only; compare against current `modelCallStatus.test.tsx` and event reducer tests before adding anything.

- `docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2.md`
  - Value: historical plan and rationale.
  - Current decision: migrated to mainline `docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2.md` on 2026-06-27 after strict token-shape scan found no real API key, bearer token, OAuth token, callback code, or client secret.

- `docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2-karpathy-review.md`
  - Value: historical review of the latency V2 plan.
  - Current decision: migrated to mainline `docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2-karpathy-review.md` on 2026-06-27 after strict token-shape scan found no real API key, bearer token, OAuth token, callback code, or client secret.

## Do Not Migrate Without Explicit User Confirmation

- `memory/gui_provider_settings/secrets.dev.json`
  - Reason: local secret/state file; must not be copied to Git or quoted.
- `memory/gui_provider_settings/providers.json`
  - Reason: local provider runtime state; may include local account metadata or stale environment-specific state.
- `memory/gui_bridge/state.json`
  - Reason: runtime bridge state; not source code.
- `learning_agent/test/provider_settings_v2_openai_connect/**/backend_*.log`
  - Reason: raw runtime logs can contain local paths, request traces, or sensitive context.
- `learning_agent/test/provider_settings_v2_openai_connect/**/electron_*.log`
  - Reason: GUI runtime logs, evidence only.
- `learning_agent/test/provider_settings_v2_openai_connect/**/renderer_*.log`
  - Reason: frontend runtime logs, evidence only.
- `learning_agent/test/provider_settings_v2_openai_connect/**/auto_pids.json`
  - Reason: local process evidence, not source.
- `learning_agent/test/provider_settings_v2_openai_connect/**/computer_use_pids.json`
  - Reason: local process evidence, not source.
- `learning_agent/test/provider_settings_v2_openai_connect/**/real_codex_login_acceptance.json`
  - Reason: GUI/OAuth acceptance evidence; review and redact before archival.
- `learning_agent/test/real_model_latency_v2_20260626/**`
  - Reason: mixed evidence, discovery outputs, and source copies; review subfolders individually before copying.

## Modified Tracked Files In Old Worktree

- Treat all 34 modified tracked files as old experiment state, not merge-ready code.
- The largest risk area is provider settings and GUI bridge files, because mainline has moved past this old branch.
- Any future migration must cherry-pick behavior by requirement, not by file.
- If a future feature needs old behavior, create a new clean worktree from `codex/publish-main`, write red tests first, then port the minimum code.

## Recommended Next Action

- The two low-risk plan documents have now been migrated to mainline.
- Next engineering task: if desired, write a new blueprint for "Transport Diagnostics Tab V1" using only the ideas from `gui_model_latency_diagnostics.py`, not the old implementation wholesale.
- User confirmed on 2026-06-27: old worktree remaining uncommitted contents can be abandoned.
- Cleanup completed on 2026-06-27:
  - removed `.worktrees/chatgpt-oauth-real-model-v1` with `git worktree remove --force`;
  - deleted branch `codex/chatgpt-oauth-real-model-v1`;
  - ran `git worktree prune`;
  - removed the now-empty `.worktrees` directory.

## Stop Condition

- Historical stop condition was satisfied by explicit user confirmation on 2026-06-27.
- Do not recreate or restore the old worktree unless a future task explicitly needs a new clean worktree from `codex/publish-main`.
- Do not recover old abandoned `memory/`, raw logs, OAuth acceptance evidence, or local state from filesystem backups unless the user explicitly asks for a separate forensic recovery task.
