# ClaudeCode Harness To OpenHarness Computer Use Mapping

## Studied ClaudeCode Paths

- `utils/agentContext.ts`
- `tools/AgentTool/agentToolUtils.ts`
- `tasks/LocalAgentTask/LocalAgentTask.tsx`
- `tasks/InProcessTeammateTask`
- `utils/computerUse/wrapper.tsx`
- `utils/computerUse/executor.ts`
- `utils/computerUse/computerUseLock.ts`
- `utils/computerUse/cleanup.ts`

## Borrowed Harness Ideas

- task-local context
- tool-use context
- permission state
- lock and cleanup
- tool result feedback
- task progress state
- failure result propagation
- abort boundary

## OpenHarness Computer Use Mapping

- `ComputerUseTaskContext` owns one desktop task.
- `DesktopTaskRunState` owns ordered stages and stage results.
- `ComputerUseToolUseContext` owns one action batch.
- `ObservationFacts` feed the next planner or verifier step.
- `ReflectionLearningResult` feeds bounded repair.
- `ActionBatch` remains deterministic and target-bound.

## Non-Portable ClaudeCode Ideas

- Code-task-specific assumptions are not copied.
- UI rendering details are not copied into Computer Use runtime.
- Desktop-specific window identity and screenshot/UIA facts are implemented by OpenHarness.
