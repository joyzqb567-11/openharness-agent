# StagePlanningResult Schema

Required fields:

- `objective`
- `task_kind`
- `stages`
- `success_criteria`
- `layer_skill_metadata`

Each stage should include:

- `stage_id`
- `stage_kind`
- `target_ref`
- `input_contract`
- `output_contract`
- `observation_policy`
- `batch_intent`
- `verification_contract`
- `repair_policy`
