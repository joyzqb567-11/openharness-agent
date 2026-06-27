# Direct OAuth SSE Probe Evidence

Result: gated and not enabled by default.

The probe requires all of these explicit runtime conditions before it can claim the direct SSE path is available:

- `OPENHARNESS_OPENAI_AUTH_MODE=direct_oauth`
- `OPENHARNESS_OPENAI_EXPERIMENTAL` set to a true value
- `OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`
- a non-empty OpenAI client identifier configured by the user

Current safe conclusion:

- Without the full gate, probe status is `not_configured`.
- HTTP 401 maps to `unavailable_unauthorized`.
- HTTP 403 maps to `unavailable_forbidden`.
- Output delta or completed output payload maps to `available`.
- Unknown payloads stay unavailable instead of being treated as streaming.

Automated coverage:

- `learning_agent/tests/test_codex_oauth_streaming_probe.py`
- `learning_agent/tests/test_gui_model_latency_secret_redaction.py`

No raw browser session values, credential values, callback values, or provider secrets are stored in this evidence folder.

