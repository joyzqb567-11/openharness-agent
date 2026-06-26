# OpenHarness Desktop OpenCode-Style OpenAI Connect V1 Karpathy-Style Review

评估对象：

```text
H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1\docs\superpowers\plans\2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md
```

## 结论

这个蓝图方向是对的。

它最好的地方是没有只复制 OpenCode 的 UI，而是看到了背后的状态机：method list、API key、OAuth attempt、status、complete、cancel。这是成熟 provider 系统应该长出来的骨架。

但我会给它 **B+**。

不是因为它不够完整。恰恰相反，它有点太完整了。它现在试图在一个 V1 里同时完成：OpenCode 风格 UI、真实 API Key、真实 browser OAuth、真实 headless device flow、callback server、polling worker、secret store、视觉 QA、token leak scan。这个组合很容易从 90% demo 掉进 deployment reliability 的沼泽。

Don't be a hero.

把它拆成更小的垂直闭环，会更像一个能真的长大的系统。

## 做得好的地方

1. **证据链是对的**

蓝图先读了 OpenCode 的真实源代码：`packages/core/src/plugin/provider/openai.ts`、`dialog-connect-provider.tsx`、`packages/protocol/src/groups/integration.ts`、`packages/schema/src/integration.ts`。这比照着截图猜要好很多。

2. **产品边界是对的**

它明确说：API Key 可以真实连接后端，ChatGPT OAuth attempt 可以先建立连接层，但不宣称完整模型 runtime 已经能吃 OAuth token。这个切分很重要。很多 AI 产品就是在这里开始撒谎的。

3. **attempt 状态机方向是对的**

OpenCode 的新协议不是“点一下按钮然后祈祷”，而是 `start -> status -> complete/cancel`。OpenHarness 复制这个抽象是正确的。这个 abstraction 会撑住后续 provider 扩展。

4. **安全意识已经进入系统**

蓝图反复说 raw key、access token、refresh token 不进 renderer、不进截图、不进 catalog。这是必要的。不是 nice-to-have。

5. **GUI 验收不是假验收**

计划里要求真实 Electron、CDP visual QA、手动肉眼验收、bug 后 systematic debugging。这个很好。UI 系统只靠 unit test 是不够的。

## 主要问题

### P0: 真实 OAuth refresh token 不能落进 DevJsonSecretStore

蓝图说不升级到 Windows Credential Manager 或 OS keychain，同时又计划真实 browser/headless OAuth，并保存 `refresh_token`。

这两件事放在一起不成熟。

API key 走 dev JSON，我还能接受，因为当前 V1 已经明确是开发存储，并且 UI 可以警告。ChatGPT OAuth refresh token 不一样。它像一个长期会话钥匙。真实接入时如果还是 JSON 文件，后续一旦用户填真账号，就会形成安全债。

建议加一个硬门禁：

```text
如果 OPENHARNESS_PROVIDER_SECRET_STORE != os_encrypted
真实 OpenAI OAuth 只能运行 mock/test mode
不能保存真实 refresh_token
```

也就是说：

- dev JSON 可以跑 UI 和 mock OAuth。
- API Key 可以继续作为当前稳定路径。
- 真 OAuth token 必须等 `OsEncryptedSecretStore` 或同等安全存储完成后打开。

这是红线。

### P0: V1 范围太胖，应该拆成 4 个 vertical slices

现在 Task 1 到 Task 12 是一个大雪球。每一步看起来都合理，但组合起来失败面太大。

我会把它改成这样：

```text
Slice A: Method picker + API Key real path
Slice B: OAuth attempt contract + mock headless server
Slice C: Real headless device flow behind experimental flag
Slice D: Real browser PKCE callback behind encrypted store gate
```

每个 slice 都必须有：

- 后端 contract test
- 前端 interaction test
- visible GUI screenshot
- secret leak scan
- 明确 stop condition

不要先实现 browser callback server。先做 headless mock。它更小，更容易观察，更少 Windows 端口/浏览器/防火墙变量。

### P0: 不要 cargo-cult OpenCode 的 clientID 和 auth endpoint

蓝图计划复用 OpenCode 里的：

```text
clientID = app_EMoamEEZ73f0CkXaXp7hrann
issuer = https://auth.openai.com
callbackPort = 1455
```

这个要非常小心。

OpenCode 源代码能这么做，不等于 OpenHarness 可以长期产品化这么做。这里至少需要一个 `OpenAIAuthConfig`：

```text
auth_base_url
client_id
callback_host
preferred_callback_port
experimental_enabled
```

默认状态下真实 OAuth 应该是 disabled，除非：

- 用户显式打开 experimental flag。
- 配置了允许使用的 client id。
- secret store 是加密存储。
- mock/real mode 在日志和 UI 中清楚显示。

否则我们会把一个研究实现伪装成产品能力。

### P1: `confirmation_code` 字段语义混了

OpenCode 的 UI 会把 browser mode 的 instructions 显示在“确认码”框里。截图里也是这样。但从 OpenHarness 合同设计角度，直接把它命名成 `confirmation_code` 会让后续代码变脆。

headless 的值是真 user code。

browser 的值不是 code，是 instruction text。

建议改成：

```json
{
  "mode": "auto",
  "url": "...",
  "instructions": "...",
  "display_code": "...",
  "display_code_copyable": true,
  "display_code_kind": "device_code | instruction"
}
```

UI 仍然可以显示成“确认码”。但合同不要撒谎。

### P1: attempt status enum 需要收紧

蓝图前面说状态是：

```text
pending, complete, failed, expired
```

后面 Task 3 又说 cancel 后变成：

```text
expired 或 cancelled
```

这个小不一致会在实现时变成测试抖动。

选一个。

我建议跟 OpenCode 保持一致：`pending | complete | failed | expired`。取消就是 `expired`，message 写 `cancelled_by_user`。如果一定要 `cancelled`，就从 schema 到测试到 UI 全部显式加上，不要“两者都行”。

### P1: `complete` endpoint 对 auto mode 的职责不清楚

Browser/headless auto mode 理论上由后端 callback/polling worker 完成。`complete` 更适合 code mode 或测试。

建议写清楚：

```text
auto mode:
  前端只 start、poll status、cancel
  不调用 complete

code mode:
  前端 start、用户粘贴 code、调用 complete

test/mock mode:
  可以调用 complete 或 mock server 触发 complete
```

这会让前端状态机简单很多。

### P1: bridge 重启后的 attempt 行为没有定义

当前 attempt registry 是 process 内存。开发阶段可以。

但成熟 GUI 需要定义窗口关闭、bridge 重启、renderer 刷新时发生什么：

- renderer 刷新后 poll 一个不存在的 attempt，应该得到 `expired`，不是 500。
- bridge 退出时必须关闭 callback server 和 polling worker。
- 新 attempt 启动时应取消同 provider 的旧 pending attempt。

这个不是 polish。否则 tail behavior 会很差。

### P2: Task 顺序应该更像训练循环

现在 Task 1 后端测试、Task 2 OAuth helper、Task 3 session、Task 4 catalog、Task 5 bridge、Task 6 前端 client、Task 8 UI。

这像 waterfall。

更好的顺序是每次构建一个端到端可见闭环：

```text
1. catalog 暴露 OpenAI 三个 methods
2. UI 显示三 methods
3. API Key 真实保存
4. mock OAuth start/status/cancel
5. mock OAuth complete
6. real headless
7. real browser
```

每一步都有 screenshot 和 tests。像训练模型一样：forward pass、loss、backprop。不要先写一堆底层模块，最后才看 UI。

### P2: 每行中文注释会放大复杂度

这是项目规则，必须遵守。但它意味着代码越多，维护成本越高。

所以更应该“少写代码”。把新模块做小，函数做短。不要做大而全的 `gui_provider_auth_sessions.py`。可以拆成：

```text
gui_provider_auth_attempts.py
gui_provider_openai_headless.py
gui_provider_openai_browser.py
```

每个文件只承担一种心智模型。

## 建议升级项

### 1. 增加 Milestone 0: Product And Safety Decisions

在 Implementation Tasks 前加一个 Milestone 0：

```text
- [ ] 决定 V1 stable path: API Key only
- [ ] 决定 OAuth path: experimental only
- [ ] 决定 real OAuth token requires encrypted secret store
- [ ] 决定 attempt status enum
- [ ] 决定 real OAuth config source and feature flag
- [ ] 决定 browser flow 是否先延后到 Slice D
```

这个 milestone 不写代码，但会省掉很多返工。

### 2. 把真实 OAuth 从默认任务改成 gated experimental task

把 Task 2/3 里的真实 browser/headless 改成：

```text
默认实现 mock-compatible attempt engine
真实 OpenAI network flow 必须满足 experimental flag + encrypted secret store
```

这不是变保守。是工程现实主义。

### 3. 先做 headless，再做 browser

Browser PKCE callback 有太多外部变量：端口、浏览器、系统默认浏览器、防火墙、redirect、state、callback server 生命周期。

Headless device flow 更小。先把它跑通。

### 4. 把 `auth-session` 改名为 `auth-attempt`

OpenCode 的概念是 attempt。这个词更准确。

建议 endpoint：

```text
POST /v2/gui/provider-settings/auth-attempt/start
GET  /v2/gui/provider-settings/auth-attempt/status?attempt_id=...
POST /v2/gui/provider-settings/auth-attempt/complete
POST /v2/gui/provider-settings/auth-attempt/cancel
```

“session”在这个项目里已经有会话含义，容易和聊天 session 混。

### 5. 增加 Tail Behavior Tests

加这些测试：

- start 两次同 provider，旧 attempt 被取消。
- cancel 两次，第二次是 idempotent。
- status 查不存在 attempt，返回 expired，不是 500。
- callback state 错误，不保存 token。
- token exchange 成功但 metadata 解析失败，仍安全保存 token。
- renderer 关闭 wizard，poll timer 被清理。
- visual QA JSON 不包含 `access_token`、`refresh_token`、`secret_ref`。

AI 产品的可靠性不是平均情况，是尾部行为。

## 推荐后的评分

如果按上面升级，我会给它 **A-**。

现在是一个很好的蓝图，但还带着一点“我们可以一次做完 OAuth”的乐观主义。真正成熟的桌面壳要慢一点。先 API Key，后 mock attempt，再 headless，再 browser。每一步都可见、可测、可回滚。

这就是 march of nines。前 90% 看起来像速度，后 9% 看起来像边界条件。最后 0.9% 全是安全、重启、取消、超时、端口冲突、用户关窗口。

就这样。
