# OpenHarness Desktop Direct ChatGPT OAuth SSE V3 Karpathy Review

说明：我以 Karpathy 视角做这个评估，基于公开表达蒸馏出的工程判断，不是本人发言。

## Verdict

先说结论：方向是对的，但蓝图现在还把几个“研究观察”写成了“产品契约”。这是最危险的地方。

我喜欢它把 OpenHarness 从 Codex CLI WebSocket retry 慢路径里拽出来，转向 OpenCode 证据支持的 Direct ChatGPT OAuth + HTTPS/SSE。这是正确的工程直觉。用户看到慢，不是因为 UI 不够漂亮，而是因为 runtime path 错了。要砍掉慢路径，而不是装饰慢路径。

但从 march of nines 的角度看，这份蓝图还没有到可以直接长任务执行的质量。它会很容易做出一个 demo：OAuth 能连、SSE 能回、GUI 能显示。然后在真实用户机器上被 account id、模型名、token refresh、endpoint drift、secret scan false positive、GUI cancellation 这些尾部问题吃掉。

这就是 90% 和 99.9% 的差距。

## Score

- 技术方向：8/10
- 可执行性：6/10
- 安全边界：6/10
- 真实 GUI 验收设计：7/10
- 抗未来漂移能力：4/10

我会把它评为：可以作为 V3 的骨架，但需要先升级成“实验快速通道 + 可回滚 runtime contract + 真实 fixture 驱动”的计划，再执行。

## What Is Good

### 1. It attacks the real bottleneck

蓝图没有继续试图优化 Codex CLI WebSocket fallback，而是把默认真实路径改成 direct HTTPS/SSE。这是正确抽象层。

用户报告的慢，是 transport/runtime 问题，不是 React 渲染问题。

### 2. It has a visible acceptance gate

要求 computer-use 做真实可见 GUI 验收，这是对的。AI 产品最容易骗自己：单元测试都绿，真实窗口一打开，按钮找不到、状态错、连接断不开。

### 3. It separates secret storage from provider UI

把 OS-encrypted secret store 单独列任务是对的。OAuth token 不是普通配置。它应该先有安全落盘契约，再有真实连接。

### 4. It explicitly rejects silent fallback

`direct_sse` 失败时不应静默走 `codex_cli`。这点非常重要。静默 fallback 会制造一种最坏的产品体验：用户以为修好了，其实只是把慢藏起来。

## Critical Issues

### P0: The OpenCode client id is being treated as a product constant

蓝图现在写死：

```powershell
$env:OPENHARNESS_OPENAI_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
```

这个对本地实验可能有用，但作为蓝图默认契约太危险。

OpenCode 里的 client id 是一个观察到的事实，不是 OpenHarness 拥有的产品接口。把它写进默认启动命令，会让未来执行者误以为这是 OpenHarness 的稳定配置。更糟的是，一旦 OpenAI 或 OpenCode 侧调整授权策略，整个 V3 会突然坏掉，而代码看起来没有变。

升级建议：

- 把 client id 改回“必须由环境配置提供”。
- 可以在“本地实验参考”里记录当前观察到的 OpenCode client id，但不能作为默认产品值。
- 加一个 startup warning：如果使用 OpenCode observed client id，GUI 诊断里标记 `oauth_client_source=observed_opencode_reference`。
- 增加 direct route probe，不通过 probe 就不能显示“健康连接”。

### P0: The direct endpoint is experimental but the plan makes it the default real path

`https://chatgpt.com/backend-api/codex/responses` 是 OpenCode 当前走的路径，但它不是 OpenHarness 自己控制的稳定 API。

这不是说不能用。可以用。只是要把它放在正确盒子里：

```text
default for experimental ChatGPT OAuth real mode
not default for all OpenAI provider usage
not a stable public API contract
```

蓝图现在说“默认真实 OAuth runtime 用 direct_sse”，这句话需要加限定：只在 `OPENHARNESS_OPENAI_EXPERIMENTAL=1` 且 `OPENHARNESS_OPENAI_RUNTIME=direct_sse` 时默认。普通 OpenAI provider 仍应支持 API key 或官方兼容路径。

### P0: Missing real golden fixtures for OAuth and SSE

现在的 SSE parser 测试是按我们想象的事件列表写的：

- `response.created`
- `response.output_text.delta`
- `response.output_item.done`
- `[DONE]`

这还不够。你需要真实 wire data。Sanitized fixture。

没有真实 fixture，parser 很容易“测试通过，真实失败”。这是 AI infra 里最常见的事故之一：你测试的是自己发明的协议，不是服务端真的返回的协议。

升级建议新增任务 0：

1. 从 OpenCode 或真实 direct_sse 调用采集一份脱敏 SSE stream。
2. 保存到 `learning_agent/tests/fixtures/chatgpt_codex_sse/`.
3. 删除所有 token、account id、email。
4. 用 fixture 驱动 parser 测试。
5. 如果无法采集真实 fixture，不能声明 parser contract 完成。

### P0: Secret scan command will false positive

蓝图最终验证命令写的是：

```powershell
rg -n "access_token|refresh_token|id_token|Authorization: Bearer|code_verifier" memory apps/desktop/src learning_agent docs
```

这个命令会命中蓝图、源码、测试、文档里的字段名。它不能区分“安全字段名”和“真实 secret 值”。所以它要么总是失败，要么执行者会为了通过而删掉有用文档。

升级建议：

- 改成专用 secret scanner。
- 允许字段名出现。
- 禁止高熵 token value、Bearer 后跟长 token、真实 refresh token 格式、未脱敏 email。
- test fixture 必须使用明显假值，例如 `test_access_token_value`.

### P1: Model list is invented too early

蓝图列了：

- `gpt-5.5`
- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.3-codex-spark`

这可能符合当前 GUI 心智，但作为 backend allow-list 很脆弱。真实可用模型取决于账号、ChatGPT plan、后端路由、OpenAI 当前策略。

从工程上看，模型列表不能只靠本地 hardcode。至少需要三层：

1. `static_known_models`：用于 UI 初始展示。
2. `probe_available_models`：连接后逐个轻量探测。
3. `last_known_good_models`：本机缓存上次真实可用模型。

如果 `gpt-5.5` 不支持，GUI 应该显示“账号当前不支持此模型”，而不是让用户等一次失败的聊天。

### P1: Account id handling is underspecified

蓝图说 `ChatGPT-Account-Id` 仅在可用时发送。这个可能不够。

真实 ChatGPT OAuth 后端经常涉及 account、organization、subscription、workspace。OpenCode 代码里有 `ChatGPT-Account-Id`，说明这不是装饰字段。

需要补：

- 从 id_token 或 token response 中解析可用 account metadata。
- 如果返回多个 account，GUI 要能选择或默认第一个可用 account。
- 如果 endpoint 返回 account required，provider 状态不能只显示“连接失败”，要显示“需要选择账号”。
- token refresh 后 account id 仍要保持一致或重新发现。

### P1: Too many subsystems before first real vertical slice

现在 12 个任务是合理的，但执行顺序偏“横向搭楼”：

1. secret store
2. OAuth service
3. provider settings
4. SSE client
5. token refresh
6. adapter
7. composer

这会让长任务跑很久才第一次看到端到端结果。Better:

```text
Thin vertical slice first.
```

建议升级执行顺序：

1. Fake OAuth token + fake SSE server + real GUI selected model payload。
2. Real OS-encrypted token store。
3. Real browser OAuth。
4. Real direct_sse probe。
5. Real chat turn。
6. Hardening: refresh, account selection, disconnect, diagnostics, secret scan。

这样每一步都有一个可见端到端回路。

Don't be a hero.

### P1: Cancellation and stream lifecycle are not sharp enough

真实 GUI 里用户会点红色取消按钮。Direct SSE 必须能关闭 HTTP stream。

蓝图现在只说 convert events，没有定义：

- 取消时如何关闭 socket/response。
- 取消后是否写入 `turn_cancelled`。
- cancel race：模型刚完成时用户点取消怎么办。
- 401 后是否 retry refresh。
- 429/5xx 是否 retry。
- timeout 是 connect timeout、first byte timeout、idle timeout，还是 total timeout。

这些是尾部行为，不是细节。

### P1: The plan ignores existing `CodexOAuthChatModel` migration strategy

CodeGraph 显示当前 `learning_agent\models\adapters.py` 已有 `CodexOAuthChatModel`，里面已经有 token、endpoint、SSE 解析的一部分。但蓝图直接新增 `chatgpt_codex_sse.py` 和 `chatgpt_oauth_tokens.py`。

这可能是对的，因为 `adapters.py` 太大。但计划需要明确：

- 哪些逻辑迁移。
- 哪些逻辑废弃。
- 哪些 tests 保护旧行为。
- 旧 `CodexOAuthChatModel` 是否保留、封装、还是标记 legacy。

否则项目会有两套 ChatGPT OAuth 代码，半年后没人知道该改哪套。

### P2: DPAPI design needs recovery and migration details

Windows DPAPI 是合理选择。但还要补：

- 使用 CurrentUser scope 还是 LocalMachine scope。
- 加密文件是否绑定 Windows 用户。
- 换电脑后无法解密时 GUI 怎么提示。
- 发现旧 plaintext token 文件时如何处理。
- logout/disconnect 是否 shred 不重要，但必须删除 secret ref 和 encrypted blob。

这不是安全洁癖。这是用户会真实遇到的问题。

### P2: GUI acceptance target response is too brittle

验收要求模型回答 `可用`。这在真实 LLM 上不是 100% deterministic。模型可能答：

- `可用。`
- `可用`
- `可以`
- `可用\n`

验收应该检查：

- 有真实 streaming delta。
- 最终消息非 mock。
- diagnostics 是 `direct_sse`。
- 没有 WebSocket retry。
- 没有 fake streaming 标记。

文本可以使用宽松断言：包含 `可用` 或 `OPENHARNESS_OK`。不要因为标点让验收失败。

### P2: The frontend contract is still too implicit

CodeGraph 显示当前 `ComposerSubmitHandler` 仍然只是接收一个 `prompt` 字符串，并返回同步结果或异步 Promise 结果。

蓝图虽然说要加 `providerId/modelId/reasoningEffort/permissionMode`，但没有指定 bridge request schema 的兼容迁移。

需要补：

- 后端 `GuiAgentRunRequest` 新字段默认值。
- 旧前端只发 prompt 时后端如何处理。
- 新前端如何从 provider store 派生 selected model。
- settings disconnect 后如何通知 composer reset。

## The Core Rewrite I Want

我会把蓝图升级成这条路线：

```text
V3A: Prove the vertical slice with fake token + fake SSE + real GUI payload.
V3B: Add OS-encrypted token store and real disconnect semantics.
V3C: Add real browser OAuth and account discovery.
V3D: Add direct_sse probe using sanitized real fixtures.
V3E: Add real chat turn with model selection and streaming.
V3F: Harden tail behavior: refresh, cancel, timeout, 401, 429, endpoint drift, secret scan.
```

这不是更慢。反而更快。因为每一层都 produces data。

## Required Blueprint Edits Before Execution

### Must Change

1. Change hardcoded `OPENHARNESS_OPENAI_CLIENT_ID` from default command to explicit user-provided env, with OpenCode observed value moved to a research note.
2. Add Task 0: collect or create sanitized golden OAuth/SSE fixtures from real OpenCode/direct_sse behavior.
3. Replace raw `rg` secret scan with a structured secret scanner that distinguishes key names from secret values.
4. Replace fixed model allow-list with static + probe + last-known-good model registry.
5. Add account discovery and account-required error handling.
6. Add stream cancellation contract.
7. Add migration plan for existing `CodexOAuthChatModel`.
8. Reorder execution around a thin vertical slice.
9. Make direct endpoint explicitly experimental, with visible route capability status.
10. Make GUI acceptance tolerate harmless model wording variation while still proving real direct_sse.

### Should Change

1. Add a single `OpenAIProviderRuntimeState` dataclass so auth, model registry, diagnostics, and selected account do not scatter across dicts.
2. Add a local direct_sse fixture server for repeatable GUI acceptance without spending real auth every time.
3. Add a `runtime_path` event at turn start before any model call.
4. Add a `first_delta_ms` budget target, for example visible first delta under 5 seconds on a healthy direct_sse call.
5. Add a rollback rule: if direct_sse breaks because endpoint drifts, UI should degrade to “Direct route unavailable” instead of fake success.

## Suggested Upgraded Acceptance Gate

The visible GUI acceptance should prove these exact things:

1. Provider starts disconnected.
2. OpenAI browser OAuth opens real browser authorize URL.
3. Callback completes and provider shows connected.
4. GUI shows selected account hint without exposing email/token.
5. Model dropdown lists probed available models.
6. Selecting a model sends that model id in the backend request.
7. First GUI turn emits:
   - `runtime=direct_sse`
   - `transport=https_sse`
   - `codex_cli_used=false`
   - `websocket_enabled=false`
8. Message receives at least one streaming delta before completion.
9. Cancel closes an active stream.
10. Disconnect removes provider auth and resets model dropdown.
11. Reconnect works without restarting the app.

That is a real product test, not a demo.

## Final Recommendation

不要直接执行当前版本。

先升级蓝图。方向不用推翻，但要把它从“我们知道 OpenCode 怎么做，所以照着连”升级为“我们有一个可观测、可回滚、fixture 驱动的 direct_sse runtime”。

这就是差别。

一个是 demo。

一个是可以继续长任务构建的系统。
