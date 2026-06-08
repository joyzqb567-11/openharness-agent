# Learning Agent Long-Task Harness Plan

## Objective

Build an independent long-task harness for `learning_agent` that can persist tasks, resume after interruption, run staged acceptance checks, automatically retry recoverable failures, and expose status for Codex/controller inspection.

## Why This Is Needed

`learning_agent` currently has useful acceptance and event-stream pieces, but its task/background/cron/monitor records are mostly process-memory structures. That means long work can become hard to recover after a crash, terminal close, endpoint failure, or machine sleep.

## Eight Stages

1. Planning and inventory.
2. Durable state schema.
3. Persistent store and event log.
4. Durable queue with leases.
5. Stage verifier and acceptance gates.
6. Runner, checkpoint, and recovery.
7. Status API and CLI.
8. Documentation, backup, automated verification, and real visible terminal acceptance.

## Final Acceptance Rule

The harness work is not complete until code is implemented, automated verification passes, and `learning_agent/start_oauth_agent.bat` is launched in a real visible terminal where a test prompt confirms the installed agent can explain or inspect the new harness.
