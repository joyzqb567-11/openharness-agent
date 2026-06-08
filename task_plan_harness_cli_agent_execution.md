# Harness CLI Agent Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a practical command path for creating and executing durable harness tasks, including an executor that can call the real `LearningAgent`.

**Architecture:** Keep `learning_agent/harness/` independent. Add `enqueue` and `run` commands to the harness CLI, add a small `AgentStageExecutor` adapter that wraps `LearningAgent.run(stage.prompt)`, and keep tests fast by injecting a deterministic echo executor into the CLI.

**Tech Stack:** Python standard library, existing `unittest`, existing `LearningAgent` app dependencies, JSON store, real visible terminal acceptance through `start_oauth_agent.bat`.

---

## Success Criteria

- `python -m learning_agent.harness enqueue ...` can create a durable run with one or more stages.
- `python -m learning_agent.harness run ... --executor echo` can execute queued stages deterministically for automated tests and smoke checks.
- `learning_agent.harness.agent_executor.AgentStageExecutor` can wrap a real `LearningAgent` instance and call `agent.run(stage.prompt)`.
- `python -m learning_agent.harness run ... --executor agent` has a real-agent execution path, while tests avoid real model calls.
- CLI `status` shows completed state, attempts, acceptance, and checkpoint after `run`.
- New and modified code has Chinese explanatory comments on every line.
- New and modified code is backed up under `learning_agent/test/harness_cli_agent_execution_20260531/`.
- Final completion requires automated tests, compile check, and real visible `learning_agent/start_oauth_agent.bat` interaction that exercises the new harness CLI.

## Scope Boundary

- In scope: harness CLI `enqueue`, harness CLI `run`, echo executor, real `AgentStageExecutor`, tests, docs, backups, real terminal acceptance.
- Out of scope: replacing `LearningAgent.run_events()` internals, multi-worker file locking, full dashboard UI, remote cloud queues.

## Stages

### Stage 1: TDD Red Tests

- [x] Add tests that `enqueue` creates a persisted run with stages and markers.
- [x] Add tests that `run --executor echo` executes a queued run and `status` reports `completed`.
- [x] Add tests that `AgentStageExecutor` calls `agent.run(stage.prompt, max_turns=...)` and returns the answer.
- [x] Run the new tests and confirm they fail for missing commands/classes.

### Stage 2: CLI Enqueue

- [x] Extend `learning_agent/harness/cli.py` parser with `enqueue`.
- [x] Parse repeated `--stage name::prompt` values.
- [x] Parse repeated `--success-marker stage=marker` values.
- [x] Save the run through `HarnessQueue.enqueue()`.
- [x] Print the run id for external agents.

### Stage 3: CLI Run

- [x] Extend `learning_agent/harness/cli.py` parser with `run`.
- [x] Add deterministic `echo` executor for tests and local smoke.
- [x] Add `agent` executor path that builds a real `LearningAgent`.
- [x] Print rendered final status after execution.

### Stage 4: Agent Executor

- [x] Add `learning_agent/harness/agent_executor.py`.
- [x] Implement `AgentStageExecutor` with an injectable agent instance.
- [x] Implement `build_default_learning_agent_executor()` for CLI agent mode.
- [x] Keep imports lazy so normal status/list/enqueue commands do not pay model startup cost.

### Stage 5: Docs And Backup

- [x] Update `learning_agent/harness/README.md` with enqueue/run examples.
- [x] Update `learning_agent/README.md` and `AGENT_ARCHITECTURE_INDEX.md` with the new CLI execution path.
- [x] Update `agent_memory/context.md`, `progress.md`, and `bugs.md`.
- [x] Copy all new/modified files and acceptance evidence to `learning_agent/test/harness_cli_agent_execution_20260531/`.

### Stage 6: Verification And Real Acceptance

- [x] Run focused harness tests.
- [x] Run full `python -m unittest discover learning_agent`.
- [x] Run `python -m compileall learning_agent`.
- [x] Start real visible `learning_agent/start_oauth_agent.bat`, ask the agent to exercise `python -m learning_agent.harness enqueue/run/status` with echo executor, observe output, and only then mark complete.
