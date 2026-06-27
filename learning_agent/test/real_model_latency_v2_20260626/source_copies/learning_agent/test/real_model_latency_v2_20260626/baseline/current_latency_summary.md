# Real Model Latency V2 Baseline

Prompt: 你好

Selected provider: openai

Selected model: gpt-5.5

queued_to_started_ms: 0

started_to_first_status_ms: not_available_before_v2

started_to_first_delta_ms: 123000

started_to_completed_ms: 123000

transport_warning_count: 2

Observed issue: OpenHarness Desktop GUI entered real mode quickly, but the first visible answer delta arrived about 123 seconds after `turn_started`. The visible logs showed Codex WebSocket timeout followed by HTTPS fallback, while the OpenHarness adapter still waited for the blocking model call to finish before emitting fake streaming chunks.
