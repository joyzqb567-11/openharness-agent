# Task 10 Visible GUI Acceptance - Memory / Prompt / Token / Notebook

## Runtime

- Workspace: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\gui-toolchain-control-center`
- Backend: `http://127.0.0.1:8876`
- Renderer: `http://127.0.0.1:5277`
- Desktop window title: `OpenHarness Desktop`
- Token header used for direct checks: `X-OpenHarness-Desktop-Token`

## Direct Endpoint Evidence

- `GET /v2/gui/memory/summary` returned `MemoryFiles = 4` and `MemoryDegraded = False`.
- `GET /v2/gui/prompt/status` returned `PromptTools = 2` and `PromptDegraded = False`.
- `GET /v2/gui/notebook/status` returned `NotebookTools = 2`, `NotebookCount = 0`, and `NotebookDegraded = False`.
- A first manual check with a Bearer header returned `unauthorized`; this confirmed the GUI bridge is enforcing the existing `X-OpenHarness-Desktop-Token` gate rather than accepting an unrelated auth shape.

## Computer-Use Visible GUI Evidence

- The real `OpenHarness Desktop` Electron window exposed a right-side `记忆` tab.
- After clicking `记忆`, the visible panel showed `记忆与预算`.
- The accessibility tree and screenshot confirmed the panel rendered `Context`, `Progress`, `Bugs`, `max messages`, `max chars`, and `notebooks`.
- The same visible window exposed memory file summaries for `agent_memory/context.md`, `agent_memory/progress.md`, and `agent_memory/bugs.md`.
- The lower workbench text contained `Context Budget`, `Compact / Resume`, `prompt_surface_report`, `token_budget_report`, `read-only first pass`, `notebook_read`, and `notebook_edit`.
- `notebook_edit` appeared as `deferred write destructive`, which matches the intended first-pass read-only boundary.
- No blank panel, crash screen, or unreadable major text overlap was observed in the real GUI screenshot.

## Result

- Task 10 real GUI acceptance passed.
