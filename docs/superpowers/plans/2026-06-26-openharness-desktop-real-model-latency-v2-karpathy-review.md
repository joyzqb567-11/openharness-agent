# OpenHarness Desktop Real Model Latency V2 Karpathy-Style Review

## Verdict

我会给这份蓝图 **7.5/10**。

它抓住了真正的问题：不是“前端看起来慢”，而是后端真实模型链路现在是 blocking call，GUI 再把最终文本 fake streaming。这个判断是对的，而且有事件时间、`codex doctor`、源码三个层面的证据。

但现在它还有一个典型的工程风险：把两个不同层级的问题合在一个计划里。

1. **必须马上修的产品可靠性问题**：2 秒内给用户可见状态、可取消、错误可读、阶段可诊断。
2. **更深的真实低延迟问题**：Direct OAuth SSE 或经过验证的 Codex transport 快路径。

这两个都重要，但执行顺序不能混。先把系统变得 observable，再优化 transport。Don't be a hero.

## What Is Strong

### 1. 问题定义很干净

蓝图没有把“慢”泛化成一个模糊体验问题，而是给出了明确瓶颈：

```text
gui_turn_queued -> turn_started: same second
turn_started -> first message_delta: about 123 seconds
```

这很好。工程里最重要的一步永远是先定位慢在哪里。这里已经排除了 bridge 排队和前端输入，聚焦到模型调用阶段。

### 2. 它诚实地区分了 fake streaming 和真实 streaming

当前代码是：

- `CodexCliChatModel.chat()` 等完整结果。
- `RealModelGuiAgentAdapter.run()` 等 `chat()` 返回。
- GUI adapter 再把最终文本拆成 chunk。

这不是 streaming。这只是 UI 上的动画。蓝图把这个说清楚了，这一点很重要。很多 AI 产品死在这里：demo 看起来像 stream，生产里用户等 120 秒。

### 3. Non-goals 写得比较成熟

尤其是这几条是对的：

- 不承诺在 Codex CLI WebSocket timeout 时神奇变快。
- 不把未验证的 Codex CLI 配置项当解决方案。
- 不泄露 token、authorization code、refresh token、cookie。

这就是 deployment reality。系统不是靠愿望跑起来的。

### 4. 真实 GUI 验收门禁是必要的

这个项目是 Desktop GUI，不是纯 backend library。单元测试只能证明局部逻辑，不能证明用户看到的体验。真实可见 GUI 验收必须保留。

## Main Problems

### Problem 1: 蓝图缺少 Task 0，也就是 measurement harness

现在蓝图有 baseline evidence，但执行任务从“新增事件合同”开始。这里少了一步：

先把现有链路的 latency measurement 固化成可重复脚本或测试。

应该新增 Task 0：

- 读取最近 N 条 GUI events。
- 自动计算：
  - queued_to_started_ms
  - started_to_first_status_ms
  - started_to_first_delta_ms
  - started_to_completed_ms
  - transport_warning_count
- 输出 JSON 证据。
- 保存到 `learning_agent/test/real_model_latency_v2_20260626/baseline/`。

没有这个，后续很容易出现“我感觉变好了”。这不够。要有 before/after 数字。

### Problem 2: Codex CLI streaming 方案需要先 discovery，不要直接设计 parser

蓝图 Task 3 说：

> stdout 如果是 JSONL，按行解析，提取可见文本 delta。

这里有一个小危险：你还没有证明 `codex exec --json` 在当前真实 ChatGPT OAuth 路径下会输出 token delta，还是只输出 lifecycle events，或者最终结果。

应该把 Task 3 拆成：

1. **Task 3A: Codex CLI event shape discovery**
   - 用真实 `codex exec --json` 对一个最小 prompt 做采样。
   - 保存 stdout/stderr 原始脱敏样本。
   - 明确它有没有 token delta。
2. **Task 3B: Codex CLI observable runner**
   - 如果有 delta，解析 delta。
   - 如果没有 delta，只解析 stderr/status/fallback，并把最终文本作为 completion。

这就是 march of nines。不要在未知协议上写一个漂亮 parser。

### Problem 3: Direct OAuth SSE Task 太 assertive

Task 4 写得像已经知道 SSE endpoint 和 payload shape 一样。但 Direct ChatGPT OAuth 是最敏感、最容易踩边界的部分。

这里要更谨慎：

- 不能复用 OpenCode client id。
- 不能把私有 token 或 callback code 写进 evidence。
- 不能假设 ChatGPT OAuth token 一定可用于目标 API。
- 不能在没有 endpoint/payload 证据时承诺真实 token streaming。

建议把 Task 4 改成 gated slice：

```text
Task 4A: Direct OAuth SSE capability probe
Task 4B: Direct OAuth SSE stream implementation, only if probe passes
Task 4C: If probe fails, keep Direct OAuth as connected/authenticated provider but do not claim low-latency stream
```

这不是保守，这是工程现实主义。

### Problem 4: 事件模型需要有限状态机，不只是 event_type 字符串

`ModelStreamEvent` 只有 `event_type` 太弱。需要明确 phase enum，否则后续前端、测试、日志会慢慢发散。

建议固定这些 phase：

```text
queued
started
connecting
auth_checking
websocket_connecting
websocket_timeout
https_fallback
streaming
first_delta
completed
cancel_requested
cancelled
failed
```

并且每个 GUI turn 必须有：

- `turn_id`
- `provider_id`
- `model_id`
- `phase`
- `elapsed_ms`
- `sequence`

没有 `sequence`，取消后旧子进程的残留 delta 可能追加到新 turn。这个 bug 很常见。

### Problem 5: cancellation 需要定义 Windows process tree 行为

Task 8 说“终止 Codex CLI 子进程”，但 Windows 上这件事不只是 `process.terminate()`。

需要在蓝图里明确：

- 创建子进程时是否使用新的 process group。
- 取消时先 soft terminate，再 kill。
- stdout/stderr reader threads 如何退出。
- 取消后是否 drain queue。
- 如果子进程已经结束，cancel 应该幂等。

否则取消按钮可能只是 UI 取消，后台 `codex.exe` 还在跑。用户会再次遇到“我点了取消，但机器还在忙”的体验。

### Problem 6: diagnostics 不能变成新的 2 分钟阻塞

Task 5 说从 `codex doctor` 解析状态，并设置 TTL。这方向对。

但需要明确：

- diagnostics 必须后台异步运行。
- 不能在发送 prompt 的同步路径上跑 `codex doctor`。
- 如果诊断缓存过期，发送 prompt 仍然立即开始，同时显示“正在刷新连接诊断”。

否则你把模型调用慢，换成 doctor 慢。只是把问题换了个名字。

### Problem 7: 验收指标还需要分成“首状态”和“首 token”

现在 Success Criteria 有：

- 2 秒内显示模型调用阶段。
- Direct OAuth SSE 下真实 token/delta 到达立即显示。

建议更精确：

```text
first_status_ms <= 2000
first_transport_warning_ms <= 30000 when WebSocket timeout happens
first_delta_ms measured separately and not conflated with first_status_ms
cancel_visible_ms <= 500
cancel_backend_stop_ms <= 3000
```

关键是不要把“首状态”当“首 token”。这两个是不同指标。

## Required Blueprint Upgrades

我建议升级蓝图时直接做以下改动。

### 1. 新增 Task 0: Baseline Latency Measurement

放在所有实现任务之前。

产物：

```text
learning_agent/test/real_model_latency_v2_20260626/baseline/current_latency_events.json
learning_agent/test/real_model_latency_v2_20260626/baseline/current_latency_summary.md
```

验收：

```text
baseline summary includes queued_to_started_ms, started_to_first_delta_ms, completed_ms
```

### 2. 新增 Task 3A: Codex CLI JSON/stderr Discovery

放在 Codex CLI runner 实现之前。

产物：

```text
learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/sanitized_stdout.jsonl
learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/sanitized_stderr.txt
learning_agent/test/real_model_latency_v2_20260626/codex_cli_discovery/event_shape.md
```

验收：

```text
event_shape.md states whether token deltas are observable from Codex CLI
```

### 3. 把 Task 4 改成 gated experimental slice

不要直接写“Add Direct ChatGPT OAuth SSE Fast Path”。改成：

```text
Task 4: Probe And Gate Direct ChatGPT OAuth SSE Fast Path
```

只有 probe 通过，才进入 SSE 实现。否则不声明真实低延迟 token streaming。

### 4. 为 ModelStreamEvent 增加 phase、elapsed_ms、sequence

建议 schema：

```python
@dataclass(frozen=True)
class ModelStreamEvent:
    event_type: ModelStreamEventType
    phase: ModelStreamPhase
    message: str
    timestamp: float
    elapsed_ms: int
    sequence: int
    metadata: dict[str, Any] = field(default_factory=dict)
```

`metadata` 继续严格脱敏。

### 5. 增加 secret redaction automated gate

蓝图现在有“不泄露”的验收，但还不够自动化。

新增测试：

```powershell
python -m pytest learning_agent/tests/test_gui_model_latency_secret_redaction.py -q
powershell -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1 learning_agent/test/real_model_latency_v2_20260626
```

### 6. 增加 stale event / cancellation race 测试

必须覆盖：

- turn A 取消后，turn A 的 late delta 不能进入 turn B。
- cancel request 重复发送不崩。
- 子进程已退出后 cancel 不报错。
- 前端取消后 500ms 内 UI 状态变化。

### 7. 调整执行顺序

推荐顺序改成：

1. Task 0: baseline measurement。
2. Task 1: stream event contract。
3. Task 2: backend adapter emits phases。
4. Task 6: frontend visible model status。
5. Task 8: real cancellation。
6. Task 3A: Codex CLI discovery。
7. Task 3B: Codex CLI observable runner。
8. Task 5: async diagnostics cache。
9. Task 7: honest model gating。
10. Task 4A/4B: Direct OAuth SSE gated fast path。
11. Task 9/10: visible GUI acceptance and docs。

先让用户不再盲等，再追求真正低延迟。

## Go / No-Go

**Go, but upgrade the plan first.**

这份蓝图不是错的。方向很好。它已经比“我们去优化一下速度”强很多，因为它知道：

- 当前速度问题有外部 transport 因素。
- 内部 fake streaming 是产品问题。
- 可见 GUI 验收不能省。

但如果现在直接执行，容易在 Direct OAuth SSE 上花太多时间，最后用户仍然面对空白等待。

最小正确路径是：

```text
instrument -> visible status -> real cancellation -> observable CLI -> gated SSE fast path
```

先把系统变成可观察的。然后再让它更快。

这就是唯一重要的事。
