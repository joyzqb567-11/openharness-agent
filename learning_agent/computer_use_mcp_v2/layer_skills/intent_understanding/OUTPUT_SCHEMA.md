# IntentUnderstandingResult Schema

Required fields:

- `objective`: short sanitized objective
- `task_kind`: generic task kind
- `target_app_hints`: user-provided software hints
- `required_targets`: target descriptors
- `content_payloads`: requested content snippets
- `artifact_requests`: requested output artifacts
- `success_criteria`: evidence-based success criteria
- `requires_fresh_resource`: boolean
- `allows_existing_user_window`: boolean
- `risk_level`: low, medium, or high
- `needs_clarification`: boolean
- `layer_skill_metadata`: prompt metadata, never prompt content
