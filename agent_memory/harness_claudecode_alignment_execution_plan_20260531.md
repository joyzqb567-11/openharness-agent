# Harness ClaudeCode Core Alignment Execution Plan

> For agentic workers: REQUIRED SUB-SKILL: use `superpowers:executing-plans` to implement this plan task-by-task. Do not claim completion until every hard gate and visible-terminal acceptance scenario passes.

Goal: make `learning_agent` core harness behavior genuinely align with ClaudeCode's core harness loop by making the real main loop consume durable runtime commands, persist unified events, restore interrupted runs, and feed task notifications into the next model turn.

Architecture: keep the existing `learning_agent/harness/` and `learning_agent/runtime/` foundations, but move the real source of truth into a harness-driven runtime loop. `LearningAgent.run()`, `run_events()`, runtime command queue, task registry, harness event log, and session transcript must become one connected path instead of separate side systems.

Tech Stack: Python stdlib, existing `unittest`, existing `LearningAgent` model/test fakes, existing JSON/JSONL durable stores, existing PowerShell acceptance controller, existing `start_oauth_agent.bat`.

---

## Hard Gates

- [ ] A real terminal prompt must create or continue a durable harness run.
- [ ] `LearningAgent.run()`, `LearningAgent.run_events()`, session transcript, and harness event log must share the same turn/run/command evidence.
- [ ] `RuntimeCommandQueue` commands must be consumed by the real main loop, not only by tests or CLI helpers.
- [ ] Task notification commands must become model-visible context on the next real model turn without manual `task_output`.
- [ ] Resume-interrupted commands must be consumed by the real main loop and must not merely sit in the queue.
- [ ] `task`, background command, and team peer state must not rely on only in-memory dictionaries as the source of truth.
- [ ] A process interruption must recover from durable checkpoint/session/queue without rerunning completed stages.
- [ ] CLI/API status must show run, stage, task, event, output path, and verifier result.
- [ ] Final acceptance must launch the real visible `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat` terminal and pass task-notification and resume scenarios.
- [ ] README or docs are never key evidence for completion; source, tests, durable state files, and visible-terminal result JSON are required evidence.

---

## Phase 0: Freeze Current Gap And Redefine Completion

Files:
- Modify: `agent_memory/harness_claudecode_alignment_plan_20260531.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

Steps:
- [ ] Add the Hard Gates section above to the original alignment plan.
- [ ] Replace any wording that implies the previous implementation is complete with "partial foundation, incomplete until main-loop queue drain passes".
- [ ] Record that a status-only terminal scenario is insufficient evidence.
- [ ] Run source search to confirm current gap before code work:
  - `rg -n "dequeue_next\\(|enqueue_task_notification\\(|run_agent_with_harness_session|run_events\\(" learning_agent`
- [ ] Expected current finding: `dequeue_next()` is not used by the real `LearningAgent.run()` execution path.

Acceptance:
- [ ] A future agent reading `agent_memory/harness_claudecode_alignment_plan_20260531.md` cannot reasonably conclude that files plus unit tests are enough.
- [ ] `agent_memory/bugs.md` contains the false-completion risk and required fix.

---

## Phase 1: Red Tests For Real Main-Loop Command Drain

Files:
- Modify: `learning_agent/tests/test_harness_runtime_alignment.py`
- Possibly create: `learning_agent/tests/support` helpers only if existing fake model helpers are insufficient.

Tests to add first:
- [ ] `test_real_run_drains_task_notification_into_next_model_turn_without_task_output`
- [ ] `test_real_run_consumes_resume_interrupted_command`
- [ ] `test_runtime_prompt_command_is_model_visible_before_mark_completed`
- [ ] `test_run_events_and_harness_event_log_share_turn_identity`
- [ ] `test_completed_stage_is_not_rerun_when_resume_command_is_consumed`

Expected red behavior:
- [ ] Task notification is persisted but not injected into the next model prompt.
- [ ] Resume command is persisted but not consumed by the next real `run()`.
- [ ] Queue command state is not tied to model-visible attachment evidence.

Commands:
- [ ] Run focused red test command:
  - `python -m unittest learning_agent.tests.test_harness_runtime_alignment`
- [ ] Expected before implementation: at least the new queue-drain tests fail for real behavior reasons, not import errors.

Acceptance:
- [ ] Every red test failure message must name the missing user-visible behavior.
- [ ] Do not implement until the red tests prove the current gap.

---

## Phase 2: Runtime Command Drain Design

Files:
- Modify: `learning_agent/runtime/command_queue.py`
- Create or modify: `learning_agent/runtime/session_runtime.py`
- Modify tests: `learning_agent/tests/test_harness_runtime_alignment.py`

Design:
- [ ] Add a small command-drain layer that can select commands for one model turn.
- [ ] Drain order must mirror ClaudeCode priority semantics: `now`, then `next`, then `later` when allowed.
- [ ] Current user prompt is first persisted into the queue before model execution.
- [ ] Drained `prompt` commands become the user prompt text for the turn.
- [ ] Drained `task_notification` commands become a clearly delimited model-visible notification block.
- [ ] Drained `resume_interrupted` commands become a clearly delimited continuation block.
- [ ] Commands must not be marked completed merely because they were written to disk.
- [ ] Commands must be marked completed only after the turn has terminal evidence in harness/session events.

Acceptance:
- [ ] Unit tests prove drain order.
- [ ] Unit tests prove task notifications do not overwrite user prompt text.
- [ ] Unit tests prove failed turns do not silently lose commands.

---

## Phase 3: Make `LearningAgent.run()` Harness-Driven

Files:
- Modify: `learning_agent/runtime/session_runtime.py`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/app/interactive.py` only if the interactive entry still bypasses the runtime.

Implementation intent:
- [ ] `LearningAgent.run()` must enter `run_agent_with_harness_session()`.
- [ ] `run_agent_with_harness_session()` must enqueue the user prompt first for crash safety.
- [ ] It must drain runtime commands for the turn.
- [ ] It must build the model-visible turn input from drained commands.
- [ ] It must call `agent.run_events()` with that model-visible input.
- [ ] It must write one harness run event when commands are attached to the turn.
- [ ] It must write one harness run event for every `AgentEvent` yielded by `run_events()`.
- [ ] It must mark drained commands completed only after terminal run evidence is saved.
- [ ] On exception, it must preserve or requeue commands in a recoverable state.

Acceptance:
- [ ] Focused tests from Phase 1 turn green.
- [ ] Existing `run()` return value remains plain text for CLI compatibility.
- [ ] Latest durable run JSON shows completed run and completed stage acceptance.
- [ ] Runtime queue event log shows command queued, attached, and completed.

---

## Phase 4: Task Notification Feedback Loop

Files:
- Modify: `learning_agent/runtime/task_registry.py`
- Modify: `learning_agent/runtime/session_runtime.py`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/tests/test_harness_runtime_alignment.py`

Implementation intent:
- [ ] `complete_task()`, `fail_task()`, `stop_task()`, and `mark_needs_input()` must enqueue `task_notification`.
- [ ] Notification payload must include `task_id`, `status`, `summary`, `output_file`, and `usage`.
- [ ] The next real `run()` must drain that notification and inject it into the model context.
- [ ] Once injected and completed, the task must be marked `notified=true`.
- [ ] A repeated save of the same completed task must not duplicate notifications.

Acceptance:
- [ ] Test proves the fake model receives the task result in the next prompt without calling `task_output`.
- [ ] Test proves duplicate notifications are not generated.
- [ ] Test proves notification contains output file path for long output.

---

## Phase 5: Interrupted Resume Consumption

Files:
- Modify: `learning_agent/runtime/resume.py`
- Modify: `learning_agent/runtime/session_runtime.py`
- Modify: `learning_agent/harness/runner.py` only if stage checkpoint semantics need tightening.
- Modify: `learning_agent/tests/test_harness_runtime_alignment.py`

Implementation intent:
- [ ] Startup or explicit resume scan finds harness runs stuck in `running`.
- [ ] Current running stage becomes `needs_review` when side effects are uncertain.
- [ ] Completed stages remain completed and must not run again.
- [ ] A `resume_interrupted` command is queued.
- [ ] The next real `run()` drains the resume command and injects continuation context into the model turn.
- [ ] The harness event log records resume detection, command attachment, and final outcome.

Acceptance:
- [ ] Test proves completed stage executor count stays unchanged after resume.
- [ ] Test proves resume command is consumed by real `run()`.
- [ ] Test proves harness status shows the interrupted stage state and final resumed result.

---

## Phase 6: Durable Task/Background/Team Truth Source

Files:
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/tasks/task_runs.py`
- Modify: `learning_agent/tasks/background.py`
- Modify: `learning_agent/runtime/task_registry.py`
- Modify tests for task/background/team behavior.

Implementation intent:
- [ ] Existing `self.task_runs` can remain as a runtime cache only.
- [ ] Existing `self.background_commands` can remain as a process-handle cache only.
- [ ] Durable task registry must be the status source for task list/get/output/stop.
- [ ] Background command exit must update durable task status and output.
- [ ] Team peer task state, if active in current source, must create durable records or be explicitly marked unsupported with tests.

Acceptance:
- [ ] A fresh `LearningAgent` instance can inspect old task records.
- [ ] A completed background command appears as completed in durable task registry.
- [ ] `task_stop` can stop or mark a durable task after process restart.

---

## Phase 7: Output, Status, And Verifier Closure

Files:
- Modify: `learning_agent/runtime/task_output.py`
- Modify: `learning_agent/harness/status.py`
- Modify: `learning_agent/harness/cli.py`
- Modify: `learning_agent/harness/verifier.py`
- Modify related tests.

Implementation intent:
- [ ] Task output supports append, tail, delta offset, flush, and evict.
- [ ] CLI `queue`, `tasks`, `events`, `resume`, and `poll` show enough information for Codex/controller auditing.
- [ ] Status output includes run, stage, task, event, output path, and verifier result.
- [ ] Verifier can read acceptance controller `result.json`.

Acceptance:
- [ ] `python -m learning_agent.harness queue ...` shows runtime commands and harness runs.
- [ ] `python -m learning_agent.harness tasks ...` shows durable task status and output path.
- [ ] `python -m learning_agent.harness events ...` shows recent event sequence.
- [ ] Verifier tests prove marker, artifact, event sequence, command exit code, and acceptance result checks.

---

## Phase 8: Automated Regression Gate

Commands:
- [ ] `python -m unittest learning_agent.tests.test_harness_runtime_alignment`
- [ ] `python -m unittest learning_agent.tests.test_harness_long_task`
- [ ] `python -m unittest learning_agent.tests.test_runtime_events`
- [ ] `python -m unittest learning_agent.tests.test_core_run_loop`
- [ ] `python -m unittest discover learning_agent`
- [ ] `python -m compileall learning_agent`
- [ ] `python learning_agent\learning_agent.py mcp-doctor`

Acceptance:
- [ ] All commands pass.
- [ ] If any command fails, update `agent_memory/bugs.md` with root cause and do not proceed to visible-terminal final acceptance.

---

## Phase 9: Real Visible Terminal Acceptance

Files:
- Create or modify: `learning_agent/acceptance_controller/scenarios/harness_task_notification.json`
- Create or modify: `learning_agent/acceptance_controller/scenarios/harness_runtime_resume.json`
- Create or modify: `learning_agent/acceptance_controller/scenarios/harness_background_shell_watchdog.json`

Required scenarios:
- [ ] Task notification scenario: create a background/subtask result, then prove the next agent answer references the result without manual `task_output`.
- [ ] Resume scenario: create or simulate interrupted durable state, restart or trigger resume, then prove the real terminal agent continues from checkpoint.
- [ ] Background shell/watchdog scenario: create a background command state and prove durable task/output/status/notification behavior is visible.

Commands:
- [ ] Launch through `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`.
- [ ] Use acceptance controller to type prompts into the real visible terminal.
- [ ] Replay each `result.json` with `python -m learning_agent.acceptance.verifier`.

Acceptance:
- [ ] Each scenario result has `completed=true`.
- [ ] Each scenario assertion has `passed=true`.
- [ ] Screenshots show the real terminal, not a hidden stdin/pipe run.
- [ ] The final answer must not claim completion if this phase is skipped or blocked.

---

## Phase 10: Source-Only Final Comparison

Files:
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Optionally modify architecture index only after source evidence is true.

Checks:
- [ ] Source search confirms real `run()` path drains runtime queue.
- [ ] Source search confirms task notifications are transformed into model-visible context.
- [ ] Source search confirms resume-interrupted commands are consumed by real run path.
- [ ] Source search confirms task/background/team status has durable registry path.
- [ ] Source search confirms CLI/API can display run, stage, task, event, output, verifier result.
- [ ] No README claim is used as primary evidence.

Final claim allowed only if:
- [ ] Phase 1 red tests turned green.
- [ ] Phase 8 automated regression passed.
- [ ] Phase 9 real visible terminal acceptance passed.
- [ ] Phase 10 source-only comparison confirms the real main loop is harness-driven.

---

## Stop Conditions

- [ ] Stop if a new test cannot be made red for the claimed missing behavior.
- [ ] Stop if real terminal acceptance cannot be opened, observed, or controlled.
- [ ] Stop if a design choice would change user-facing terminal interaction semantics without approval.
- [ ] Stop if a dependency or background service is required beyond the current project stack.
- [ ] Stop if the same blocker repeats three times; record it in `agent_memory/bugs.md` and ask the user.
