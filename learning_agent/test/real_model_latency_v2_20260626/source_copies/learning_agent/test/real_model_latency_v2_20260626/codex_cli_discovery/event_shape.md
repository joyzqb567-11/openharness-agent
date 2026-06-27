# Codex CLI Event Shape Discovery

Prompt:
请只回复：pong

Command:
codex exec --json --skip-git-repo-check --sandbox read-only --model gpt-5.5 "请只回复：pong"

Observed date:
2026-06-26

Result summary:
The command produced JSONL lifecycle events, then timed out at the 180 second discovery guard. It did not produce a final assistant answer during the guard window.

Does stdout contain JSONL:
Yes. `sanitized_stdout.jsonl` contains JSON objects such as `thread.started`, `turn.started`, and `item.completed`.

Does stdout contain token deltas:
No. This discovery did not show token delta events or assistant text chunks before timeout.

Does stderr contain transport warnings:
Partially. It contains plugin and shell snapshot warnings plus the discovery timeout marker, but this run did not expose `Responses WebSocket timed out` or `Falling back from WebSockets to HTTPS transport`.

Where does final answer appear:
Not observed in this run. There is no final `pong` answer in stdout, stderr, or a captured final-output file before timeout.

Can OpenHarness show real token streaming from Codex CLI:
No, not from this observed event shape. OpenHarness must not claim true token streaming for Codex CLI until a later discovery proves token delta events exist.

Can OpenHarness at least show transport status from Codex CLI:
Yes, with limits. OpenHarness can show lifecycle status, stderr warnings, and timeout/cancellation status. It should label this as CLI observability, not verified token streaming.

Security note:
The stored stdout and stderr are sanitized. No raw browser session values, credential values, callback values, email addresses, or local user paths are intentionally stored.
