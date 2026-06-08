# 2026-06-05 Project Size Audit

## Goal

Analyze why `H:\codexworkplace\sofeware\OpenHarness-main` is unusually large for an agent project and define a safe slimming plan.

## Facts Observed

- Total project size is about 953 MB.
- `.git` is about 582 MB and is the largest directory.
- `learning_agent` is about 346 MB and is the largest working-tree directory.
- `.git/objects` contains about 19,145 files, with `git count-objects -vH` reporting about 541 MiB of loose objects and about 40 MiB in packs.
- `git cat-file --batch-all-objects` shows blob objects dominate Git storage at about 557 MB.
- `git fsck --unreachable --no-reflogs` reports many unreachable objects, so a large part of `.git` is old or temporary object data no longer referenced by current refs.
- `learning_agent/acceptance_controller/runs` is about 145 MB and consists of visible-terminal acceptance run artifacts.
- `learning_agent/test` is about 82 MB and contains learning backups, screenshots, and copied source snippets required by the current project rules.
- `learning_agent/memory` is about 59 MB and contains sessions, evidence, status JSONL, and computer-use artifacts.
- `learning_agent/debug_logs` is about 20 MB.
- `learning_agent/browser_artifacts` is about 16 MB.
- `agent_memory/progress.md`, `agent_memory/bugs.md`, and `agent_memory/context.md` are growing and should be summarized/archived when they become too long.
- Compared with `H:\ClaudeCode-main`, the mature project keeps source directories small and puts dependency weight mostly in `node_modules`; OpenHarness puts much more weight into runtime evidence, learning backups, and Git objects.

## Root Cause

The project is large mainly because generated evidence, screenshots, transcripts, debug logs, learning backups, and unreachable Git objects accumulated in the repository. This is not normal source-code size growth.

## Safe Slimming Plan

1. First run non-destructive reporting commands and save a manifest of what would be removed.
2. Run `git gc --prune=now --aggressive` only after confirming no needed dangling object must be recovered.
3. Move old acceptance runs, debug logs, browser artifacts, and session transcripts to an external artifact archive outside the Git repository.
4. Replace bulky learning backups under `learning_agent/test` with compact markdown summaries plus only the exact modified snippets needed for study.
5. Archive long memory files under `agent_memory/archive`, then keep current `context.md`, `progress.md`, and `bugs.md` short.
6. Add or tighten retention tooling so future runs keep only recent or explicitly pinned artifacts.

## Stop Condition

Do not delete or rewrite anything automatically while the working tree is dirty and has many untracked files. Ask the user before destructive cleanup or Git history/object pruning.

## Cleanup Execution Notes

- 2026-06-05 cleanup started after user explicitly approved slimming.
- First archive target: `H:\codexworkplace\sofeware\OpenHarness_artifact_archive\slim_20260605_224524`.
- Directory archive phase moved about 260 MB of runtime artifacts out of the repository.
- A later per-file move phase failed once with PowerShell `Move-Item : Could not find a part of the path`; continue with safer path handling and do not repeat the same exact command.
- A second per-file move attempt using `[System.IO.File]::Move` hit the same path-class error, so the next attempt should log and skip failing paths instead of stopping the whole cleanup.
- Final archive size is about 270.31 MB across 3,282 files.
- Python `__pycache__` cleanup removed 122 cache directories, 1,363 files, and about 18.24 MB.
- `git gc --prune=now --aggressive` reduced `.git` from about 584 MB to about 35.9 MB.
- Final project size is about 126.17 MB, down from about 962.59 MB.
- Net reduction is about 836.42 MB.
- Added `.gitignore` retention rules for runtime evidence, harness events, root memory sessions/status, learning backup screenshots, and learning backup JSONL files.
- Verification passed with `git check-ignore -v`, `git count-objects -vH`, and final directory size measurement.
