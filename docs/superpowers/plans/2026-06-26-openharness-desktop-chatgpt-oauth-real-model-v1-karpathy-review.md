# Karpathy-Style Review: OpenHarness Desktop ChatGPT OAuth Real Model V1

> 我以 Karpathy 视角和你聊，基于公开言论风格与工程框架推断，非本人。

评估对象：

- `docs/superpowers/plans/2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1.md`

参考事实：

- 已读取蓝图全文。
- 已读取 OpenCode 源码依据和 OpenHarness 当前实现摘要。
- 已核对 OpenAI 官方 Codex CLI 文档：`codex login` 支持 ChatGPT account、API key、access token；无参数时会打开浏览器走 ChatGPT OAuth flow。文档地址：<https://developers.openai.com/codex/cli/reference#codex-login>

---

## 总体判断

这个蓝图方向是对的。

但它还不是一个可以直接长任务执行的最优蓝图。它把三个不同风险层级的东西揉在一起了：

1. 官方支持的 Codex CLI ChatGPT OAuth 登录。
2. OpenCode 里观察到的 PKCE + localhost callback。
3. ChatGPT/Codex backend internal route 直连。

这三件事看起来很像，但工程可靠性完全不同。第一条是公开文档路径，第二条是可观察实现，第三条更像内部协议依赖。

Imo，这份计划现在是 7.5/10。它已经避免了“只做 UI 假连接”的大坑，但还没有把“可长期维护的认证产品”和“实验性 reverse-engineered 直连”隔离干净。

---

## 做得好的地方

### 1. 它抓住了真正的分界线

最重要的一句是：不能只复制前端外观。

这个判断是对的。设置页里出现“连接 OpenAI”没有意义。真正有意义的是：

- 后端管理 OAuth pending。
- 后端持有 token。
- 后端刷新 token。
- 后端调用真实模型。
- GUI 主聊天不再走 fake adapter。

这就是从 demo 到 product 的第一步。

### 2. 安全默认值是正确方向

蓝图要求：

- renderer 不拿 raw token。
- token 不进 repo/workspace memory/log/visual QA JSON。
- 真实 OAuth 需要显式 opt-in。
- 没有安全 token store 不启用真实 OAuth。
- 真实失败不回退 fake。

这些都是对的。尤其是“不回退 fake”。如果系统在真实模型失败时偷偷返回假回答，它就不是一个 agent harness，它是一个幻觉制造器，外面套了桌面壳。

### 3. 验收从自动化拉到了真实 GUI

Task 17 和 Task 18 把真实 OAuth 可见 GUI 验收与真实模型聊天验收拆开，这是正确的。

AI 产品评估里最容易被骗的是平均路径。这里至少开始看 tail behavior：登录失败、token 过期、刷新失败、secret 泄露、fake 回退。

这很好。

---

## 最大问题

### 1. 它把内部实现当成了产品契约

OpenCode 源码里有：

- `app_EMoamEEZ73f0CkXaXp7hrann`
- `localhost:1455/auth/callback`
- `https://chatgpt.com/backend-api/codex/responses`
- `codex_cli_simplified_flow=true`

这些是事实。但事实不等于契约。

官方文档稳定承认的是：Codex CLI 可以用 ChatGPT OAuth 登录。官方文档没有承诺第三方应用可以长期依赖 OpenCode 的 client id 或 ChatGPT internal backend route。

所以蓝图应该把实现路径分成两条：

- **官方路径**：调用/复用 Codex CLI login/auth cache/app-server 能力，作为 V1 默认真实连接路径。
- **实验路径**：OpenCode-style direct OAuth + Codex backend route，显式标记 unstable/private-backend，默认关闭。

现在蓝图把实验路径写成主路径。这会让后续执行非常容易跑进维护地狱。

Don't be a hero.

### 2. 任务颗粒度仍然太大

19 个任务跨了：

- OAuth config
- PKCE
- callback server
- token exchange
- encrypted token store
- provider catalog
- model adapter
- bridge adapter selection
- React UI
- visual QA
- real auth QA

这不是一个 feature task。这是一个小认证平台加模型 runtime。

我会把它切成三个 release train：

- **V1A：官方 Codex login 桥接**，先让用户用 ChatGPT OAuth 登录后，GUI 真能回答。
- **V1B：OpenHarness provider catalog 与真实 adapter 联动**，把“已登录”变成可见 provider 状态。
- **V1C：direct OAuth experimental**，再做 OpenCode-style PKCE 直连。

现在这个蓝图试图一次性到 V1C。

### 3. RealModelGuiAgentAdapter 的合同太薄

蓝图里的 adapter 草图是：

```python
model_message = model.chat(...)
emit message_delta
emit message_completed
```

这能让测试绿，但不像 mature Codex shell。

至少要定义：

- 首 token latency。
- 长回答 chunking。
- cancel 时如何中断远端请求。
- token refresh 与当前 turn 的关系。
- model 返回 tool calls 时，是 fail、defer、还是进入 tool execution loop。
- streaming 解析错误时，是 retry、partial complete、还是 failed。
- GUI 关闭窗口后 backend turn 是否继续。

否则你会得到一个“真实但脆”的 adapter。

从 90% 到 99.9% 的爬坡，就藏在这里。

### 4. Token store 只写了“加密”，没写“生命周期”

DPAPI 是必要但不充分。

OAuth token store 至少还要覆盖：

- logout 删除 token。
- refresh token revoked。
- token 文件损坏。
- Windows 用户切换。
- token_ref 指向不存在。
- OpenHarness 升级后 schema migration。
- 截图、日志、事件流、错误消息的统一 redaction。
- crash 后 pending auth server 如何恢复或清理。

现在蓝图有 secret leak gate，但 token 生命周期不够完整。

### 5. Port 1455 是一个非常具体的 failure mode

OpenCode 使用 `localhost:1455`。用户机器上可能已经有 OpenCode 正在跑，也可能上一次 OpenHarness crash 后端口没释放。

这不是边角问题。这是第一天就会遇到的问题。

蓝图需要加：

- 启动前 port preflight。
- port 被占用时的可读错误。
- 如果 OAuth client redirect URI 固定为 1455，就不能动态换端口。
- 如果必须动态换端口，就需要自己的 OAuth client 配置支持多个 redirect URI。
- 用户同时运行 OpenCode 和 OpenHarness 时的策略。

没有这个，真实 GUI 验收会变成随机失败。

### 6. “真实模型测试回答”这个测试名会骗你

Task 11 用 fake model 返回 `真实模型测试回答` 来测 adapter 事件合同。这是单元测试层面可以的，但它不能证明真实模型连接。

蓝图应该显式区分：

- adapter contract test：fake model 可用。
- remote smoke test：必须打到真实远端。
- visible GUI acceptance：用户肉眼确认授权和回答。

现在有 Task 17/18，但 Task 11 的命名容易让后续执行者误判“测试通过=真实连接通过”。

### 7. 缺少一个“官方 CLI auth bridge”最小路径

官方文档给了一个很重要的信号：`codex login` 已经支持 ChatGPT OAuth。

所以最小可行路径不一定是重写 OpenCode OAuth：

1. GUI 检测 `codex login status`。
2. 未登录时，GUI 提供“打开 Codex 登录”。
3. 后端启动 `codex login` 或指导用户完成登录。
4. GUI adapter 先用 `CodexCliChatModel` 真实回答。
5. 然后再考虑直连 `CodexOAuthChatModel`。

这条路更少自研 auth surface，也更接近官方支持边界。

直接重写 OAuth 不是错，但不应该是第一条主线。

---

## 我会怎么改蓝图

### 改法 1：增加 V1A/V1B/V1C 分层

在任务清单前新增：

```markdown
## Release Split

### V1A: Official Codex Login Bridge
- 使用官方 `codex login` / `codex login status` 作为真实 ChatGPT OAuth 入口。
- GUI provider 显示 Codex/ChatGPT 登录状态。
- GUI 主聊天通过 `CodexCliChatModel` 或受控 adapter 得到真实回答。
- 不读取、不复制、不解析 Codex auth token。

### V1B: Provider-Aware Real Adapter
- provider catalog 与 real adapter 联动。
- no-token、expired-token、fake-fallback forbidden 都有测试。

### V1C: Experimental Direct OAuth
- OpenCode-style PKCE + localhost callback。
- 使用 OpenHarness 自己的 OAuth client id。
- 默认关闭，作为 experimental backend。
```

这会把风险压下去。

### 改法 2：把 Task 7 token store 前置

现在计划先写 OAuth helper，再写 token store。更好的顺序是：

1. threat model
2. token store
3. redaction gate
4. OAuth callback

安全系统不要先拿到 token 再想怎么存。先建保险箱，再开门。

### 改法 3：加一组 tail behavior tests

增加任务：

- port 1455 已占用。
- 用户关闭 auth 弹窗但浏览器后来回调。
- callback 收到重复 code。
- callback state 不匹配。
- exchange token 500。
- refresh token revoked。
- ChatGPT account id 缺失。
- remote SSE 中断。
- GUI cancel 时远端请求仍在跑。
- app 重启后 provider catalog 不显示假 connected。

这就是 March of Nines。不是 happy path。

### 改法 4：明确“不依赖 OpenCode client id”的产品原则

蓝图应该写：

```markdown
OpenCode client id 只作为源码研究依据，不能作为 OpenHarness 默认生产 client id。
若没有 OpenHarness 自有 OAuth client id，则 direct OAuth 只能作为本地实验模式，不能声明稳定功能。
```

这很重要。否则你是在把别人的实现细节当地基。

### 改法 5：真实 GUI 验收要有证据包

Task 17/18 现在是肉眼步骤，但还缺证据输出：

- `real_oauth_login_success.png`
- `real_provider_connected.png`
- `real_model_answer.png`
- `real_event_stream.png`
- `real_oauth_acceptance.json`

JSON 中保存：

- timestamp
- provider source
- adapter mode
- event kinds
- fake_text_detected=false
- secret_leak_detected=false
- 不保存 prompt 里的敏感信息

这会让验收从“我看到了”变成“可以复盘”。

### 改法 6：给 adapter 加真实 streaming contract

把 Task 12 改成：

- 先支持 non-streaming real answer，但 UI 显示 `message_delta`。
- 再支持 real SSE streaming。
- cancel 必须中断后端请求或至少标记 abandoned。
- 远端失败不能产生 completed。
- tool calls 暂时 fail fast，但错误文案必须说“真实模型已连接，工具循环尚未接入”，不能说模型失败。

这能防止把第一版写死。

---

## 建议评分

| 维度 | 分数 | 评语 |
|---|---:|---|
| 问题定义 | 9/10 | 准确抓住 fake adapter 是核心问题 |
| OpenCode 源码理解 | 8/10 | 读到了关键链路，但对“实现事实 vs 稳定契约”区分不够 |
| 安全设计 | 7/10 | 方向对，token 生命周期还不够 |
| 任务可执行性 | 6/10 | 颗粒度偏大，一次性跨太多系统 |
| 验收设计 | 8/10 | 真实 GUI 门禁很好，但需要证据包和 tail tests |
| 长期可维护性 | 6/10 | direct OAuth/internal backend 需要 experimental 隔离 |

综合：7.5/10。

---

## 结论

我会执行这个方向，但不会照这个版本直接开工。

先把它升级成“三层路线图”：

1. 官方 Codex login bridge 先跑通真实回答。
2. Provider 状态与 real adapter 联动。
3. OpenCode-style direct OAuth 作为实验路径。

这不是保守。这是减少表面积。

最好的工程计划不是把所有正确的事情都塞进第一版，而是找到最短路径证明核心风险已经消失。这里的核心风险只有一个：

用户完成 ChatGPT OAuth 后，GUI 是否真的由真实模型回答。

先证明这个。别的都往后排。
