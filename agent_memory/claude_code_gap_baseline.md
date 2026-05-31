# ClaudeCode 与 learning_agent 差距基线

记录日期：2026-05-31

## 给后续 agent 的读取说明

这份文档是后续对齐 ClaudeCode 能力时的基线，不是一次性结论。

后续 agent 进入项目后，优先读取本文件，再读取：

- `learning_agent/AGENT_ARCHITECTURE_INDEX.md`
- `learning_agent/README.md`
- `learning_agent/claude_code_tool_gap_matrix.md`
- `agent_memory/context.md`
- `agent_memory/progress.md`
- `agent_memory/bugs.md`

当前实际项目路径：

- ClaudeCode 源码：`D:\ClaudeCode-main\ClaudeCode-main`
- learning_agent 项目：`H:\codexworkplace\sofeware\OpenHarness-main\learning_agent`

注意：旧文档里可能出现 `D:\codexworkplace\software\ClaudeCode-main` 之类历史路径，后续分析以本文件记录的实际路径为准。

## 总体判断

learning_agent 已经不是玩具项目，已经具备本地 coding agent 的核心骨架：

- 有模型调用主循环。
- 有基础工具调用能力。
- 有 MCP stdio/http 基础运行时。
- 有真实 Chrome 验收链路。
- 有 prompt、memory、context assembler、token budget 相关基础设施。
- 有 task、team、cron、monitor、lsp、repl、worktree 等最小形态能力。
- 有单元测试、acceptance_controller 和项目级架构文档。

但是 learning_agent 和 ClaudeCode 的差距仍然很大。最关键的问题是：learning_agent 很多功能已经有了名字和最小实现，但 ClaudeCode 是产品级运行系统，具备流式执行、并发工具调度、权限体系、hook、持久会话、多 agent 调度、插件命令系统、完整 MCP 生命周期和成熟终端 UI。

## 差距估算

这些百分比不是数学精确值，是工程判断，供排优先级使用。

| 对比口径 | learning_agent 当前水平 | 剩余差距 |
|---|---:|---:|
| 公开可复现的核心 agent 思路 | 55%-65% | 35%-45% |
| 面向本地自我开发的长期 agent | 50%-60% | 40%-50% |
| ClaudeCode 产品级完整度 | 25%-35% | 65%-75% |

后续开发时不要只看工具名是否存在。名字相同不代表能力等价。比如 `task`、`team`、`monitor`、`cron`、`lsp`、`repl`、`worktree` 在 learning_agent 中多数仍是教学版、最小版或状态型实现。

## ClaudeCode 关键源码入口

后续 agent 分析 ClaudeCode 时，优先看这些文件：

- `D:\ClaudeCode-main\ClaudeCode-main\QueryEngine.ts`
  - 会话级 agent 引擎。
  - 管理消息、配置、权限拒绝、token usage、已发现 skill、嵌套 memory 等跨轮状态。
- `D:\ClaudeCode-main\ClaudeCode-main\query.ts`
  - 主 query loop。
  - 负责模型调用、上下文压缩、工具调用、自动 compact、恢复逻辑、stream 处理。
- `D:\ClaudeCode-main\ClaudeCode-main\Tool.ts`
  - ClaudeCode 工具接口定义。
  - 包含工具 schema、权限、并发属性、是否只读、是否危险、UI 渲染、MCP/LSP 标记、结果大小限制等。
- `D:\ClaudeCode-main\ClaudeCode-main\tools.ts`
  - 内置工具池注册和 MCP 工具装配。
  - 负责按权限和模式过滤工具。
- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\toolExecution.ts`
  - 工具执行主逻辑。
  - 负责输入校验、hook、权限判断、拒绝处理、执行、结果映射和错误处理。
- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\toolOrchestration.ts`
  - 工具批处理和并发调度。
  - 只读或并发安全工具可以并行，非安全工具串行。
- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\StreamingToolExecutor.ts`
  - 流式工具执行器。
  - 支持模型还在流式输出时就开始执行工具。
- `D:\ClaudeCode-main\ClaudeCode-main\services\mcp\client.ts`
  - MCP 客户端核心。
  - 支持 stdio、SSE、HTTP、IDE、OAuth、重连、缓存、resources、prompts、tools。
- `D:\ClaudeCode-main\ClaudeCode-main\memdir\memdir.ts`
  - memory 目录和长期记忆提示。
- `D:\ClaudeCode-main\ClaudeCode-main\coordinator\coordinatorMode.ts`
  - 多 agent 协调模式。

## learning_agent 关键源码入口

后续 agent 修改 learning_agent 时，优先看这些文件：

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\AGENT_ARCHITECTURE_INDEX.md`
  - 当前架构索引。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\README.md`
  - 项目定位、启动方式和已声明能力。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\claude_code_tool_gap_matrix.md`
  - 旧的 ClaudeCode 工具差距矩阵。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py`
  - 当前 LearningAgent 主循环。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tools\schemas.py`
  - 工具 schema。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\models\adapters.py`
  - 模型适配器。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\mcp\runtime.py`
  - MCP 运行时。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\`
  - 真实终端和真实 Chrome 验收控制器。

## 已经对齐或部分对齐的能力

| 能力 | learning_agent 当前状态 |
|---|---|
| 基础 agent 主循环 | 已有 Python 实现，能构造消息、调用模型、执行工具、追加 tool result。 |
| 核心工具 | 已有 `read`、`write`、`edit`、`bash` 四个原子工具方向。 |
| 工具目录 | 已有 Tool Catalog / Tool Pool / ToolPolicy 的方向。 |
| 延迟工具 | 已有 `tool_search` 和 deferred tool 的方向。 |
| MCP | 已有 stdio/http 基础工具调用、resources、prompts、list_changed 相关方向。 |
| Prompt 架构 | 已有 prompt registry、context assembler、prompt surface report、token budget report。 |
| 长输出处理 | 已有长工具结果落盘和 observation 记录方向。 |
| 真实浏览器 | 已有真实 Chrome workflow gate、客户模式自动授权、真实终端验收。 |
| Plan/Worktree | 已有计划确认、worktree 状态型 fallback。 |
| Task/Team | 已有教学版子任务、peer 消息和后台任务绑定。 |
| LSP/REPL/Cron/Monitor | 已有最小能力或接口形态。 |
| 测试 | 已有 unittest discovery、compileall、acceptance_controller。 |

## 核心差距清单

### 1. 主循环和流式运行时差距很大

ClaudeCode 的 query loop 是异步生成器，支持流式模型输出、工具流式执行、上下文自动压缩、token budget 恢复、prompt too long 处理和多种异常恢复。

learning_agent 当前主循环主要是同步的 `model.chat()` 形态，通常等模型完整返回工具调用后再逐个执行工具。

差距等级：高。

建议优先级：P0。

建议目标：

- 把主循环升级为 event stream。
- 模型适配器支持 token/message/tool_call 流式事件。
- 工具执行器能在模型流式输出期间提前启动安全工具。
- 把最终回答、工具调用、权限询问、错误恢复都变成统一事件。

### 2. 工具接口差距很大

ClaudeCode 的工具不是普通函数，而是带完整元数据的运行单元。工具接口包含：

- 输入 schema。
- 输出 schema。
- 权限检查。
- 输入校验。
- 是否只读。
- 是否危险。
- 是否可并发。
- 是否需要用户交互。
- 中断行为。
- MCP/LSP 标记。
- UI 渲染。
- 最大结果大小。
- 是否延迟加载。

learning_agent 当前工具层已经有 schema 和 policy 方向，但整体还不够统一，也没有把工具运行时属性全部正式化。

差距等级：高。

建议优先级：P0。

建议目标：

- 建立统一 `AgentTool` 协议。
- 每个工具显式声明 `is_read_only`、`is_destructive`、`is_concurrency_safe`、`requires_user_interaction`、`interrupt_behavior`。
- 每个工具都有 `validate_input`、`check_permissions`、`call`、`map_result`。

### 3. 工具执行和并发调度差距很大

ClaudeCode 会把工具调用分批：

- 只读工具或并发安全工具可以并行。
- 非安全工具串行。
- 流式工具执行器可以边接收模型输出边执行工具。
- sibling tool 失败、中断、用户取消都有专门处理。

learning_agent 当前偏顺序执行，缺少成熟的批处理、并发、中断和 sibling error 机制。

差距等级：高。

建议优先级：P0。

建议目标：

- 实现工具批处理器。
- 先只允许只读工具并发。
- 默认并发上限建议从 3 或 5 开始，不要一开始追求 10。
- 对写文件、bash、浏览器副作用工具保持串行。

### 4. 权限系统差距很大

ClaudeCode 有完整权限上下文：

- allow/deny/ask 规则。
- 不同 permission mode。
- bypass/auto 模式。
- bash 风险分析。
- hook 决策。
- 用户拒绝记忆。
- pre-plan mode 限制。
- 工具级权限 matcher。

learning_agent 有 ToolPolicy、权限询问、真实浏览器白名单和部分硬门禁，但还没有产品级权限系统。

差距等级：高。

建议优先级：P0。

建议目标：

- 正式引入 allow/deny/ask 规则文件。
- 建立 PreToolUse / PostToolUse / PermissionDenied hook。
- bash 工具加入风险分类。
- 写文件、删除、移动、网络、浏览器登录态相关操作全部走统一权限层。

### 5. 会话持久化差距很大

ClaudeCode 支持 transcript、resume、rewind、compact、历史恢复、会话级消息流和状态恢复。

learning_agent 当前更多依赖 memory、agent_memory 和单次运行状态，还没有成熟的会话数据库或 transcript 生命周期。

差距等级：高。

建议优先级：P0。

建议目标：

- 每次用户会话落盘 transcript。
- 每个 tool call 和 tool result 都有 id、时间、输入、输出、错误、权限记录。
- 支持 `resume session`。
- 支持 `rewind to message/tool call`。
- 支持自动 compact 后保留 compact 前证据索引。

### 6. MCP 完整度差距很大

ClaudeCode MCP 客户端支持多 transport、OAuth、重连、server cache、工具发现、resources、prompts、auth pseudo tool、插件 MCPB、IDE server 等复杂生命周期。

learning_agent 已有 stdio/http 基础 MCP，但还没有完整产品级生命周期。

差距等级：高。

建议优先级：P1。

建议目标：

- MCP connection manager 常驻化。
- 完整支持 reconnect、timeout、server cache、list_changed。
- OAuth/auth 流程产品化。
- prompts 可以转成 agent 命令或 skill。
- resources 可以进入 memory/context 索引。

### 7. 多 agent 和后台任务差距很大

ClaudeCode 的 coordinator mode 可以把任务拆给 worker，支持 background task、SendMessage、TaskStop、TaskOutput、任务状态和恢复。

learning_agent 有 task/team/peer 的教学版能力，但多数还不是独立进程、持久化 worker 或真正可恢复执行单元。

差距等级：高。

建议优先级：P1。

建议目标：

- 子 agent 独立 session。
- 子 agent 独立 transcript。
- 子 agent 可停止、可恢复、可读取输出。
- coordinator 可以明确分派、检查、合并结果。
- 支持 verification worker。

### 8. Memory 系统差距较大

ClaudeCode 有 memory directory、项目/team/private memory、memory scan、frontmatter、相关记忆检索、历史上下文搜索。

learning_agent 有 memory.md、agent_memory 和 prompt assembler，但还缺少成熟的记忆目录协议和模型辅助记忆选择。

差距等级：中高。

建议优先级：P1。

建议目标：

- 建立 `memory/` 目录规范。
- 每个 memory 文件有 frontmatter。
- 模型先选择相关 memory，再加载全文。
- 把历史 transcript 也纳入可检索上下文。

### 9. 终端 UI、命令系统和插件生态差距很大

ClaudeCode 有复杂 Ink UI、slash commands、插件系统、权限弹窗、任务视图、MCP 管理、memory/context/compact/resume 等命令。

learning_agent 当前主要是简单终端、bat/ps1 启动、HTTP bridge 和部分工具命令。

差距等级：高。

建议优先级：P2。

建议目标：

- 先补核心运行时，不急着做复杂 UI。
- 后续建立最小 slash command 层。
- 插件系统要等 Tool 协议稳定后再做。

### 10. Git、PR、审查和工程工作流差距较大

ClaudeCode 有 commit、review、PR、worktree、GitHub app 相关命令和流程。

learning_agent 当前能通过 shell/git 做基础操作，但没有把 Git 工作流产品化为 agent 原生能力。

差距等级：中高。

建议优先级：P2。

建议目标：

- 先做本地 git status/diff/commit helper。
- 再做 review helper。
- 最后接 PR/GitHub 流程。

## 后续推荐路线图

### 阶段 A：运行时主干升级

目标：让 learning_agent 从同步工具循环升级成事件流 agent。

成功标准：

- 主循环可以输出事件：`message_delta`、`tool_call_started`、`tool_call_finished`、`permission_requested`、`error_recovered`、`final_answer`。
- 模型适配器至少有一个支持流式。
- 只读工具可以并发执行。
- 现有 368 个左右单元测试仍通过。
- 真实可见终端验收仍通过。

停止条件：

- 不能破坏 `start_oauth_agent.bat` 用户入口。
- 不能绕过真实终端验收规则。
- 不能让副作用工具默认并发。

### 阶段 B：工具协议和权限系统升级

目标：把工具从 schema 列表升级成正式工具运行时对象。

成功标准：

- 每个工具声明只读、危险、并发安全、中断行为。
- 权限统一走 ToolPolicy v2。
- bash、write、edit、browser 相关工具有更明确风险分类。
- 拒绝、阻断、自动允许都进入 observation。

### 阶段 C：会话和 transcript 系统

目标：让 agent 可以长任务不跑偏，也能恢复。

成功标准：

- 每轮消息、工具调用、权限、错误、最终回答全部落盘。
- 可以按 session id resume。
- 可以 compact 后保留证据索引。
- 可以查看历史 session 摘要。

### 阶段 D：多 agent 和后台 worker

目标：把 task/team 从教学版升级到真正可用。

成功标准：

- 子 agent 有独立 transcript。
- 子 agent 可以后台运行。
- 主 agent 可以发送消息、读取输出、停止任务。
- 可以启动 verification worker 对结果做独立检查。

### 阶段 E：MCP 产品化

目标：把 MCP 从可调用升级成稳定生态入口。

成功标准：

- 多 MCP server 生命周期稳定。
- reconnect、timeout、list_changed、resources、prompts、auth 都有测试。
- prompts/resources 能进入 tool_search 或 context index。

### 阶段 F：UI、命令和插件

目标：在核心稳定后补产品体验。

成功标准：

- 有最小 slash commands。
- 有权限查看和修改命令。
- 有 session/resume/compact 命令。
- 有插件或 skill 安装规范。

## 当前不要做的事

后续 agent 不要一上来就做这些：

- 不要先做复杂 UI。
- 不要先做插件市场。
- 不要把所有 ClaudeCode 工具名硬塞进 learning_agent。
- 不要把教学版 task/team 误判为已经产品级完成。
- 不要绕过用户要求的真实可见终端验收。
- 不要为了追赶 ClaudeCode 私有产品能力而牺牲 learning_agent 的可理解性。

## 下一步最推荐任务

最推荐的下一步是：

先做“事件流主循环 + 工具执行器 v2”的设计文档和最小实现。

原因：

- 这是后续并发工具、权限 hook、会话 transcript、多 agent、UI 状态显示的共同地基。
- 如果主循环仍是同步阻塞形态，后续功能会越堆越复杂。
- 这一步最接近 ClaudeCode 的核心差距。

建议任务标题：

`Stage 15: Event Stream Runtime and Tool Executor v2`

建议第一批验收：

- `python -m compileall learning_agent`
- `python -m unittest discover learning_agent`
- 启动 `learning_agent\start_oauth_agent.bat` 做真实可见终端交互验收
- 真实 Chrome 相关验收场景不得退化

