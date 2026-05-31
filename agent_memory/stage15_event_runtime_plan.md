# Stage 15 Event Runtime and Tool Executor v2 Plan

记录日期：2026-05-31

## 目标

把 learning_agent 从“同步主循环 + 简单工具分发”升级为更接近 ClaudeCode 的运行时骨架。

本计划覆盖五个核心能力：

1. 主循环事件流。
2. 工具协议。
3. 工具执行器。
4. 权限 hook。
5. 会话恢复。

## 小白解释

当前 learning_agent 像一个会干活的助手，但大多数流程还是“模型先说完整计划，再一个个工具执行，再把结果塞回去”。

Stage 15 的目标是让它更像成熟 agent：

- 能边运行边吐出进度事件。
- 能知道每个工具危险不危险、能不能并发、要不要用户确认。
- 能在工具执行前后插入检查点。
- 能把每轮对话、工具调用、权限决定和结果保存下来。
- 中断后可以恢复，而不是从头再来。

## 当前代码依据

后续实施时优先看这些文件：

- `learning_agent/core/agent.py`
  - 当前 `LearningAgent.run()` 同步主循环在这里。
  - 当前 `_execute_tool()` 委托工具执行器。
- `learning_agent/models/base.py`
  - 当前只有 `ChatModel.chat()` 协议。
  - 后续需要增加流式协议，但必须保留旧 `chat()` 兼容。
- `learning_agent/models/adapters.py`
  - 当前 OpenAI、Codex CLI、Codex OAuth 模型适配器在这里。
- `learning_agent/tools/types.py`
  - 当前 `AgentTool` 已经有工具元数据雏形。
  - 后续应继续扩展，而不是重建另一套类型。
- `learning_agent/tools/executor.py`
  - 当前工具分发入口。
  - 后续升级为 Tool Executor v2。
- `learning_agent/tools/policy.py`
  - 当前工具策略层。
  - 后续权限 hook 应该接在这里附近。
- `learning_agent/observability/`
  - 当前 debug log、acceptance event、run record 在这里。
  - 后续事件流和 transcript 应尽量复用这个目录。
- `learning_agent/tests/`
  - 当前模块化测试入口。
  - 后续每个阶段必须增加对应测试。

## 范围边界

本计划要做：

- 新增事件类型。
- 新增流式模型接口。
- 新增 `run_events()`，保留旧 `run()`。
- 扩展工具协议。
- 增加工具执行器 v2。
- 增加 hook 和权限事件。
- 增加会话 transcript、resume、compact 的最小版。

本计划暂时不做：

- 不做复杂终端 UI。
- 不做插件市场。
- 不做完整 MCP OAuth 产品化。
- 不做真正分布式多 agent。
- 不做 GitHub PR 产品工作流。

## 总阶段数

建议分 8 个实施阶段完成。

原因：

- 如果少于 5 个阶段，会把主循环、工具、安全、会话全揉在一起，风险很高。
- 如果超过 10 个阶段，推进会太碎，用户很难看到阶段性收益。
- 8 个阶段可以做到每阶段都有清楚验收点。

## 阶段 15A：事件类型和 transcript 基础

目标：先定义“agent 运行时发生了什么”的统一事件格式。

要做的事：

- 新建 `learning_agent/core/events.py`。
- 定义事件类型，例如：
  - `run_started`
  - `model_request_started`
  - `model_message_delta`
  - `model_message_completed`
  - `tool_call_started`
  - `tool_call_completed`
  - `permission_requested`
  - `permission_decided`
  - `session_saved`
  - `run_completed`
  - `run_failed`
- 新建 `learning_agent/observability/transcript.py`。
- 提供最小 transcript writer，可以把事件按 JSONL 写入磁盘。

为什么先做这一阶段：

- 没有事件格式，后面流式主循环、工具执行器、权限 hook、会话恢复都会各写各的日志。
- 先定事件格式，后面所有阶段都能往同一个地方记录。

成功标准：

- 能创建一个 run id。
- 能把事件写入 `learning_agent/memory/sessions/<session_id>/events.jsonl`。
- 现有 `LearningAgent.run()` 行为不变。
- 单元测试覆盖事件序列化和 transcript 写入。

验证命令：

- `python -m unittest learning_agent.tests.test_runtime_events`
- `python -m unittest discover learning_agent`

## 阶段 15B：流式模型接口

目标：让模型适配器除了 `chat()`，还能提供 `stream_chat()`。

要做的事：

- 修改 `learning_agent/models/base.py`。
- 增加可选协议 `StreamingChatModel`。
- 新增统一模型流事件，例如：
  - 文本增量。
  - 工具调用增量。
  - 工具调用完成。
  - 模型消息完成。
- 先给 FakeModel 或测试模型实现流式模拟。
- 真实 OpenAI/OAuth 适配器可以先用兼容包装：内部仍调用 `chat()`，再一次性吐出 completed 事件。

为什么这么做：

- 不能一上来要求所有模型都支持真流式，否则会破坏现有入口。
- 先做协议和兼容层，后面再逐步让真实模型走真流式。

成功标准：

- 旧 `ChatModel.chat()` 仍然可用。
- 新 `stream_chat()` 在测试模型里可用。
- 没有真实流式能力的模型可以自动降级为一次性事件。

验证命令：

- `python -m unittest learning_agent.tests.test_models_streaming`
- `python -m unittest discover learning_agent`

## 阶段 15C：主循环事件流 run_events

目标：在不破坏旧 `run()` 的前提下，新增事件流主循环。

要做的事：

- 修改 `learning_agent/core/agent.py`。
- 新增 `LearningAgent.run_events(user_input, max_turns=None)`。
- 旧 `run()` 改为消费 `run_events()`，最后返回最终文本。
- 每个关键节点都 yield 事件：
  - 用户输入已接收。
  - 初始 messages 已构建。
  - 工具池已计算。
  - 模型请求开始。
  - 模型响应完成。
  - 工具调用开始。
  - 工具调用结束。
  - 最终回答。
- 事件同时写入 transcript。

为什么这么做：

- 这样外部 UI、HTTP bridge、真实终端以后都能看到实时进度。
- 旧入口仍能像以前一样只拿字符串，兼容用户习惯。

成功标准：

- `run()` 输出不变。
- `run_events()` 能产出稳定事件序列。
- 工具调用和最终回答都能记录到 transcript。
- 现有核心 run loop 测试仍通过。

验证命令：

- `python -m unittest learning_agent.tests.test_core_run_loop`
- `python -m unittest learning_agent.tests.test_runtime_events`
- `python -m unittest discover learning_agent`

## 阶段 15D：工具协议 v3

目标：把工具从“schema + 分发函数”升级为更完整的运行单元。

要做的事：

- 扩展 `learning_agent/tools/types.py` 的 `AgentTool`。
- 增加字段：
  - `is_concurrency_safe`
  - `requires_user_interaction`
  - `interrupt_behavior`
  - `permission_mode`
  - `result_policy`
  - `timeout_seconds`
- 明确默认值：
  - 默认不并发。
  - 默认不是破坏性工具。
  - 默认中断行为为 `block`。
  - 默认结果大小使用已有 `max_result_size_chars`。
- 更新 `learning_agent/tools/catalog.py`。
- 给四原子工具和常用只读工具补齐元数据。

为什么这么做：

- 没有工具协议，执行器无法安全判断哪些工具能并发，哪些工具必须询问权限。
- 这是追 ClaudeCode 工具系统的基础。

成功标准：

- 每个内置工具都有完整元数据。
- `read`、`read_file`、`grep/glob` 类工具可标记只读和并发安全。
- `write`、`edit`、`bash`、真实浏览器副作用工具默认不并发。
- 旧工具 schema 输出保持兼容。

验证命令：

- `python -m unittest learning_agent.tests.test_tools_policy`
- `python -m unittest learning_agent.tests.test_tool_protocol`
- `python -m unittest discover learning_agent`

## 阶段 15E：Tool Executor v2 和权限 hook

目标：把工具执行流程拆成清楚的步骤。

建议执行顺序：

1. 找到工具。
2. 校验输入。
3. 运行 PreToolUse hook。
4. 做权限决策。
5. 执行工具。
6. 运行 PostToolUse hook。
7. 处理结果大小。
8. 写入 transcript。
9. 返回 tool result。

要做的事：

- 修改 `learning_agent/tools/executor.py`。
- 新建 `learning_agent/tools/hooks.py`。
- 新建 `learning_agent/tools/permissions.py`，或在现有 policy 基础上扩展。
- hook 先支持最小版本：
  - `pre_tool_use`
  - `post_tool_use`
  - `permission_denied`
  - `tool_error`
- 权限决策统一输出：
  - `allow`
  - `deny`
  - `ask`
  - `auto_allow`
- 每个权限决定都写入事件和 observation。

为什么这么做：

- 后续所有危险操作都能从一个地方被拦截。
- 以后想加审计、日志、自动阻断、用户确认，都不用改每个工具。

成功标准：

- 旧工具仍能正常执行。
- 策略阻断、计划模式阻断、MCP 不可用、未知工具都能产生统一事件。
- 权限拒绝不会执行工具。
- hook 报错不能让 agent 直接崩溃，应转成 tool error 事件。

验证命令：

- `python -m unittest learning_agent.tests.test_tool_executor_v2`
- `python -m unittest learning_agent.tests.test_tools_policy`
- `python -m unittest discover learning_agent`

## 阶段 15F：安全并发工具批处理

目标：让多个安全只读工具可以并发执行，提高大项目分析速度。

要做的事：

- 新建 `learning_agent/tools/orchestrator.py`。
- 根据工具元数据把同一批 tool_calls 分组：
  - 只读且并发安全的工具可以并发。
  - 写文件、编辑、bash、浏览器副作用工具必须串行。
  - 不知道是否安全的工具默认串行。
- 初始并发上限建议为 3。
- 所有并发工具结果仍按原 tool_call 顺序回填 messages。

为什么这么做：

- 大项目分析时，多个 read/search 可以一起做，会明显加快。
- 但写文件和执行命令不能乱并发，否则容易互相影响。

成功标准：

- 并发只发生在明确只读且并发安全的工具上。
- 写入类工具永远串行。
- 结果顺序稳定。
- 某个并发工具失败时，不影响其他已完成只读工具结果返回。

验证命令：

- `python -m unittest learning_agent.tests.test_tool_orchestrator`
- `python -m unittest discover learning_agent`

## 阶段 15G：会话保存、恢复和最小 compact

目标：让长任务可以恢复，并减少上下文过长风险。

要做的事：

- 新建或扩展 `learning_agent/observability/transcript.py`。
- 新建 `learning_agent/core/session.py`。
- 每个 session 保存：
  - session id。
  - run id。
  - 用户输入。
  - messages。
  - tool calls。
  - tool results。
  - permission decisions。
  - final answer。
  - artifacts。
- 支持最小 resume：
  - 用户提供 session id。
  - agent 读取上次最终 messages 摘要。
  - 继续下一轮。
- 支持最小 compact：
  - 当 messages 超过软阈值，生成 compact summary。
  - 原始 transcript 不删除。
  - compact summary 回填上下文。

为什么这么做：

- 这是“长任务不跑偏”的关键。
- 没有会话恢复，agent 中途失败后只能靠人工重新描述。

成功标准：

- 每次 run 都有 session 文件。
- 可以列出最近 session。
- 可以读取一个 session 的摘要。
- 可以从 session 恢复上下文继续。
- compact 不会删除原始证据。

验证命令：

- `python -m unittest learning_agent.tests.test_sessions`
- `python -m unittest learning_agent.tests.test_runtime_events`
- `python -m unittest discover learning_agent`

## 阶段 15H：集成验收和文档更新

目标：把 Stage 15 做成真正可用的新运行时，而不是只通过局部测试。

要做的事：

- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`。
- 更新 `learning_agent/README.md`。
- 更新 `agent_memory/context.md`。
- 更新 `agent_memory/progress.md`。
- 更新 `agent_memory/bugs.md` 中相关风险。
- 给真实终端入口验证兼容性。

必须通过的验证：

- `python -m compileall learning_agent`
- `python -m unittest discover learning_agent`
- `python learning_agent\learning_agent.py --help`
- `python learning_agent\learning_agent.py mcp-doctor`
- 真实可见终端交互验收：
  - 必须启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`
  - 必须在用户本地真实可见终端里输入测试 prompt
  - 必须观察 agent 输出
  - 未完成时不能声明开发完成

成功标准：

- 旧入口仍能使用。
- 新事件流有 transcript 证据。
- 权限事件有记录。
- 工具执行器 v2 没有破坏现有工具。
- 真实 Chrome 场景不退化。

## 预计阶段收益

| 阶段 | 用户能感受到什么 |
|---|---|
| 15A | agent 开始有统一运行事件记录。 |
| 15B | 模型层具备流式扩展口。 |
| 15C | 未来 UI 和终端可以显示实时进度。 |
| 15D | 工具知道自己危险不危险、能不能并发。 |
| 15E | 危险操作可以统一拦截、审计、询问。 |
| 15F | 分析大项目时只读工具可以更快。 |
| 15G | 长任务可以保存、恢复和压缩上下文。 |
| 15H | 用户入口、文档、验收闭环完成。 |

## 推荐实施顺序

必须按顺序做：

1. 15A
2. 15B
3. 15C
4. 15D
5. 15E
6. 15F
7. 15G
8. 15H

不要跳过 15A 直接改主循环。

不要跳过 15D 直接做并发。

不要跳过 15E 直接做会话恢复。

## 风险和控制

| 风险 | 控制方式 |
|---|---|
| 改主循环破坏旧入口 | `run()` 必须保持兼容，先新增 `run_events()`。 |
| 工具并发造成文件冲突 | 默认不并发，只有只读且明确安全的工具并发。 |
| 权限 hook 太复杂 | 先做最小四类 hook，不做插件化。 |
| session 文件太多 | 先保留最近索引，后续再做清理策略。 |
| compact 丢证据 | compact 只能生成摘要，不能删除原始 transcript。 |
| 真实浏览器验收退化 | 每个涉及 run loop 或工具执行的阶段都要保留真实 Chrome 回归意识。 |

## 执行前置要求

正式改代码前，建议先创建 git commit 基线。

原因：

- 当前仓库刚初始化，很多文件仍是未跟踪状态。
- 大阶段改造前需要一个可回滚的起点。

建议先执行：

- `git status --short`
- `git add AGENTS.md agent_memory learning_agent memory.md`
- `git commit -m "chore: establish learning agent baseline"`

如果用户不想提交，也至少要确认当前未跟踪文件是否都属于项目。

## 代码备份要求

执行 Stage 15 时，如果新增或修改代码，需要遵循项目 `AGENTS.md` 的中文注释和备份要求。

当前项目实际路径是：

- `H:\codexworkplace\sofeware\OpenHarness-main`

后续实现时，建议把阶段性新增/修改代码备份到：

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test\stage15_event_runtime\`

注意：

- Stage 14 曾删除源码树下历史 `learning_agent/test/` 目录。
- 如果执行者认为恢复 `learning_agent/test/` 会造成架构误导，需要先向用户确认是否改用 `agent_memory/archive/stage15_event_runtime/`。

## 最终完成定义

只有同时满足以下条件，Stage 15 才算完成：

1. 8 个阶段全部完成。
2. 所有新增/修改代码都有对应测试。
3. `python -m compileall learning_agent` 通过。
4. `python -m unittest discover learning_agent` 通过。
5. `start_oauth_agent.bat` 真实可见终端交互验收通过。
6. `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md` 已更新。
7. 文档说明新运行时怎么用、怎么排查、怎么恢复 session。

