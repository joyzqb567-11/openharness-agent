# OpenHarness Desktop Real Model Latency V2 Visible Evidence

## Real Model Answer Evidence

Prompt: 请只回答两个字：真实
Selected provider: OpenAI / ChatGPT OAuth connected source
Selected model: GPT-5.5
first_status_ms: <= 2000 observed in visible GUI status timeline
first_transport_warning_ms: not observed during the successful short real prompt
first_delta_ms: about 127900
completion_ms: about 127900
Observed transport: Codex CLI ChatGPT OAuth compatibility path; no verified token delta stream from CLI stdout
Visible result: assistant answered `真实`
Result: passed for visible real-model answer, with slow latency honestly shown

## Visible Cancel Evidence

Prompt: __slow__ 请写一段较长中文回答，用于测试点击取消后后端是否立即停止。
Selected provider: local slow GUI turn used for deterministic visible cancel acceptance after restart
Selected model: no model selected in the restarted shell
Turn id: turn_9e2630b351da4700
cancel_visible_ms: <= 2500 after clicking the bottom red cancel button
cancel_backend_stop_ms: <= 2500; event timeline showed `gui_turn_cancel_requested` followed by `gui_turn_cancelled`
Screenshot files: learning_agent/test/real_model_latency_v2_20260626/visible_evidence/gui_cancelled_turn_20260626.jpg
Result: passed for visible GUI cancel button and backend lifecycle closure

## Fast Visible Cancel Sample

Prompt: __slow__ 再次测试取消按钮，请在取消后不要继续输出。
Selected provider: local slow GUI turn used for deterministic visible cancel acceptance after restart
Selected model: no model selected in the restarted shell
Turn id: turn_69932d165ac54106
cancel_visible_ms: captured in the visible GUI fast sample after the bottom red cancel button was clicked
cancel_backend_stop_ms: event timeline showed `gui_turn_cancel_requested` followed by `gui_turn_cancelled`
Screenshot files: learning_agent/test/real_model_latency_v2_20260626/visible_evidence/gui_cancelled_turn_fast_sample_20260626.jpg
Result: passed for fast visible GUI cancel state; screenshot shows `cancelled` message status and event rows #19/#20

## Notes

The visible cancel test used the project slow-turn trigger because the restarted shell did not show the prior OpenAI connected provider state. The Codex CLI process-level cancel path is covered by automated tests in `learning_agent/tests/test_codex_cli_streaming_model.py`.
