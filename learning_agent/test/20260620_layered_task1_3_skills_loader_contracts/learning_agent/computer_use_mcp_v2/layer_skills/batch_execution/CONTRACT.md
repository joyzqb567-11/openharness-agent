# Deterministic Batch Execution Contract

The batch executor is not a reasoning layer.

It executes validated `ActionBatch` objects only.

Rules:

- Every write batch must have exactly one `target_ref`.
- The focused window must match the batch target before critical actions.
- Batches above configured low-level event limits must be refused.
- The executor must not load prompt files.
- The executor must not ask a model to decide arbitrary next low-level actions.
- The executor reports structured action results back to the stage verifier.
