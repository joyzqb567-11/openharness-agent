# Karpathy-Style Review: OpenHarness Desktop GUI Context Compact V4

被评估蓝图：

- `docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4.md`

评估时间：2026-06-27

---

## 一句话结论

方向对，问题也抓对了：这是一个数据路径问题，不是模型能力问题。GUI 现在把真实模型调用做成了“只看最后一句 prompt”的形态，V4 蓝图要把 `GuiSession.messages` 接回 compact pipeline，这个方向是正确的。

但这份蓝图现在偏“重”。1017 行，很多可复制代码片段，长任务执行时有较高概率被局部代码片段牵着走。我的建议是保留架构和验收，压缩实现细节，把几个关键 contract 补强。

评分：7.4 / 10。

---

## 做得好的地方

1. 证据链是对的。

   蓝图先指出当前 GUI Direct SSE 路径没有调用 compact，而是 `_direct_sse_messages()` 从 `request.prompt` 构造单条消息。这是正确切入点。先定位数据流，再谈功能。这很好。

2. Source of truth 选得对。

   使用 `GuiSession.messages` 做 GUI 历史事实源，而不是新建一个内存 conversation object。这个选择很重要。否则应用重启、会话恢复、GUI 可见历史会互相打架。

3. 没有重写 compact。

   复用 `learning_agent.core.compact_pipeline.prepare_messages_before_model()` 和 `recover_from_context_overflow()`，这是正确工程判断。不要当英雄。已有模块能用就先接线。

4. 验收门槛比以前更真实。

   蓝图要求真实可见 GUI、Computer Use、右侧事件面板、真实 Direct SSE 路径、强制 compact 阈值。这接近 deployment reliability 的思路，不只是跑单测。

5. 把 `websocket_enabled=false` 和 `codex_cli_used=false` 固化为不变量。

   这是必要的。之前慢的问题本质上和 Codex CLI/WebSocket fallback 纠缠过，V4 不应该悄悄退回旧路。

---

## 主要问题

### 1. 蓝图太长，代码片段太具体

1017 行蓝图已经接近“半实现文件”。这有两个风险：

- 实现者会复制蓝图片段，而不是读取当前源码后适配。
- 当前代码一旦和片段有一点差异，长任务中段就会偏航。

更好的形态是：保留接口契约、测试断言、验收步骤；把完整实现片段减少到关键伪代码。实现阶段必须以当前源码为准。

这是典型的 “Don’t be a hero” 场景。复杂度不应该出现在计划文档里。

### 2. GUI 的 `TaskState` 构造逻辑有潜在目标污染

蓝图建议：

```python
original_request = user_messages[0] if user_messages else str(current_prompt)
task_state = TaskState.from_user_input(original_request, ...)
task_state.update_latest_user_input(latest_input)
```

这在聊天 GUI 里很危险。用户第一句经常是“你好”“帮我看一下”“最近怎么样”，真正任务可能在第 3 轮才出现。现有 `TaskState.update_latest_user_input()` 不一定会把 `current_goal` 从第一句切到最新任务。

结果：compact 摘要可能围绕“你好”组织任务状态。很小的 bug，很长的影子。

建议升级：

- GUI compact 的 `TaskState.current_goal` 必须优先使用当前 turn prompt。
- 历史消息只作为上下文事实，不应该把第一条用户消息永久钉成任务目标。
- 增加测试：第一轮“你好”，第二轮“记住 ALPHA_CONTEXT_927”，第三轮 recall，compact 摘要不能把“你好”当目标。

### 3. “当前 prompt 只出现一次”的不变量需要更强测试

蓝图写了不变量：Current user prompt must appear exactly once。很好。

但测试只覆盖了一个普通路径：当前 user message 已经在 `GuiSession.messages` 里。还缺两种关键路径：

- `GuiSession.messages` 已有当前 user message，builder 不能再 append 一次。
- `GuiSession.messages` 因异常未写入当前 user message，builder 必须 append 一次。

这应该变成两个单独测试，否则真实 GUI 下 duplicate prompt 很容易悄悄出现。

### 4. Direct SSE input schema 需要从现有 client 契约反推，不要假设

当前 `learning_agent/models/chatgpt_codex_sse.py` 的 client 会把调用方传入的 `messages` 直接放进 body 的 `"input"` 字段。蓝图的 `_to_responses_input()` 假设每条消息都是：

```python
{"role": role, "content": [{"type": "input_text", "text": text}]}
```

这个对 user 消息通常可行，但 assistant 历史是否应该用 `input_text`，还是需要兼容 `output_text` / 原生 response item，需要更严格确认。

建议升级：

- 增加一个 Direct SSE body schema contract test，直接断言真实 `ChatGptCodexSseClient.stream_responses()` 收到的 body。
- 明确 V4 只支持 text-only user/assistant history，不碰工具调用、reasoning item、图片 item。
- 如果后端接受 assistant `input_text`，测试名要写清楚：`test_direct_sse_accepts_text_only_assistant_history_contract`。

### 5. Reactive compact retry 的循环设计太容易写错

蓝图里的 retry 伪代码是 while/for/break/continue 混合。这个东西会很脆：

- 容易吞掉非 context error。
- 容易在 partial stream 后重试造成重复 delta。
- 容易让 cancellation 语义变模糊。

建议升级成两个小函数：

```text
run_direct_sse_once(messages) -> SseAttemptResult
maybe_recover_context_overflow(result, messages) -> RetryDecision
```

然后主流程只允许：

1. 第一次请求。
2. 如果明确是 context overflow，并且还没有输出用户可见 delta，做一次 reactive compact。
3. 第二次请求。
4. 第二次失败就失败，不再重试。

这比在 streaming loop 里做状态跳转安全很多。

### 6. 事件 payload 的隐私边界需要更硬

蓝图说不要泄漏 OAuth token，这当然对。但 context/compact 事件还有另一个风险：压缩摘要可能含用户隐私、文件路径、prompt 细节。

建议升级：

- 右侧 GUI runtime event 只显示计数、阈值、reason、generation、artifact 相对路径。
- 不在 GUI event payload 里放 raw compact summary。
- 如果需要调试摘要，写入本地 artifact，且 secret scan 覆盖 artifact。

不要把“可见调试”做成“可见泄漏”。

### 7. 真实 GUI 验收还需要一个非模型行为证据

让真实模型回答 `ALPHA_CONTEXT_927` 是必要验收，但它有概率性。模型可能啰嗦、可能拒绝只输出、可能压缩摘要不稳定。

建议把验收拆成两层：

- 数据层必过：Direct SSE 请求体里可以证明包含 `ALPHA_CONTEXT_927` 或 compact summary 中包含它。
- 行为层必过：真实模型最终回答 `ALPHA_CONTEXT_927`。

只有行为层没有通过时，不能直接判断 context builder 失败。先看数据层。

### 8. 这份计划缺少“最小垂直切片”阶段

现在 Task 1 到 Task 10 是大而全的链路。更稳的执行顺序应该先做一个极小闭环：

1. GUI manager spy adapter 能收到历史消息。
2. Direct SSE fake post body 能看到历史消息。
3. 真实 GUI 两轮 recall 能成功，不启用 compact。
4. 再打开 forced compact。
5. 最后做 reactive compact retry。

先让最小系统工作，再加压缩，再加恢复。这样调试成本最低。

---

## 必须升级的清单

- [ ] 把 `TaskState` 构造改成 GUI-specific：当前 turn prompt 优先成为 `current_goal`。
- [ ] 增加 current prompt exact-once 的两条测试：已有当前 user、不含当前 user。
- [ ] 增加“第一轮是寒暄，后面才是真任务”的 compact 测试。
- [ ] 把 Direct SSE input schema 写成明确 contract，不依赖默认想象。
- [ ] 把 reactive retry 从 streaming loop 里拆成小状态机。
- [ ] 限制 visible event payload，不展示 raw summary。
- [ ] 把真实 GUI 验收拆成数据层证据和模型行为证据。
- [ ] 在执行计划前增加一个 “Task 0: Evidence Lock”，先用失败测试固定 latest-prompt-only bug。

---

## 建议的新执行骨架

### Phase 0: Evidence Lock

证明当前 GUI -> adapter 只传最新 prompt，没有传历史。这个测试必须先红。

### Phase 1: Text-Only Multi-Turn Context

只做历史消息接入，不做 compact。目标是 spy adapter 和 Direct SSE body 都能看到多轮文本上下文。

### Phase 2: Proactive Compact

接入 `prepare_messages_before_model()`，强制小阈值触发 compact。验证 compact 后仍保留当前 prompt 和关键事实。

### Phase 3: Visible Events

只显示 budget/generation/reason/counts，不显示 raw summary。

### Phase 4: Reactive Context Overflow

只在明确 context overflow 且第一次请求未产生用户可见文本时做一次重试。

### Phase 5: Real GUI Acceptance

先不用 compact 做两轮 recall，再强制 compact 做多轮 recall。保存事件、请求体脱敏证据、截图。

---

## 最终判断

这份蓝图值得执行，但不应该原样执行。

它的核心方向是正确的：把 GUI 真实模型调用从 “last prompt only” 升级为 “session context + compact”。这是 OpenHarness Desktop 走向 Codex 级外壳的必要一步。

但要先把计划从“长代码菜单”改成“短 contract + 强测试 + 真实验收”。否则实现者会在细节里消耗太多注意力，真正的 bug 反而藏起来。

先压缩计划，再压缩上下文。这个顺序很有意思，也很工程。
