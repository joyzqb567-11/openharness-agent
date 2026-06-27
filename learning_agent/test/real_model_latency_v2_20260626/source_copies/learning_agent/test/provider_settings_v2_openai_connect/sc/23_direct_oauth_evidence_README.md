# OpenHarness Desktop Direct OAuth Evidence

新增文档+DirectOAuthEvidence：这个目录用于保存 V1C direct OAuth 的真实可见 GUI 验收截图和 JSON 证据；如果没有这个目录，release gate 无法区分 direct OAuth 是否真的通过肉眼验收。

新增文档+DirectOAuthEvidence：验收前必须显式设置 `OPENHARNESS_OPENAI_AUTH_MODE=direct_oauth`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1`、`OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`、`OPENHARNESS_OPENAI_CLIENT_ID=<OpenHarness-owned-or-explicit-test-client-id>`、`OPENHARNESS_GUI_MODEL_MODE=real`；如果缺少这些环境变量，OpenHarness 会阻止真实 direct OAuth，避免误用 OpenCode client id 或明文 token 存储。

新增文档+DirectOAuthEvidence：通过验收后应保存 `direct_oauth_login_success.png`、`direct_oauth_provider_connected.png`、`direct_oauth_model_answer.png`、`direct_oauth_event_stream.png`、`direct_oauth_acceptance.json`；如果缺少这些文件，不能声明 direct OAuth 真实模型连接完成。
