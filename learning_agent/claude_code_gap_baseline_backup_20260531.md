# ClaudeCode 与 learning_agent 差距基线备份

记录日期：2026-05-31

备份来源：`agent_memory/claude_code_gap_baseline.md`

用途：这份文件是给人和后续 agent 对齐方向用的稳定备份。主工作入口仍然建议读取 `agent_memory/claude_code_gap_baseline.md`。

## 总体判断

learning_agent 已经具备本地 coding agent 的核心骨架，包括模型主循环、基础工具、MCP 基础运行时、真实 Chrome 验收、prompt/memory/context 基础设施、task/team/cron/monitor/lsp/repl/worktree 等最小能力。

但是 learning_agent 与 ClaudeCode 的产品级差距仍然明显。ClaudeCode 强在流式运行时、并发工具调度、权限和 hook、会话持久化、MCP 完整生命周期、多 agent 协调、终端 UI、slash commands、插件生态和工程工作流。

## 差距估算

| 对比口径 | learning_agent 当前水平 | 剩余差距 |
|---|---:|---:|
| 公开可复现的核心 agent 思路 | 55%-65% | 35%-45% |
| 面向本地自我开发的长期 agent | 50%-60% | 40%-50% |
| ClaudeCode 产品级完整度 | 25%-35% | 65%-75% |

## 主要差距

| 维度 | ClaudeCode | learning_agent | 差距 |
|---|---|---|---|
| 主循环 | 异步生成器、流式响应、自动 compact、异常恢复 | 同步 `model.chat()` 为主 | 高 |
| 工具接口 | 完整 Tool 协议，含权限、并发、安全、UI、结果限制 | schema + executor 为主 | 高 |
| 工具执行 | 支持 hook、权限决策、并发批处理、流式工具执行 | 基础执行和权限询问 | 高 |
| MCP | 多 transport、OAuth、重连、缓存、resources、prompts、插件 | 基础 stdio/http、resources、prompts | 高 |
| 会话系统 | transcript、resume、rewind、compact、历史恢复 | 当前轮状态和 memory 为主 | 高 |
| 多 agent | coordinator、background worker、SendMessage、TaskStop、TaskOutput | 教学版 task/team/peer | 高 |
| Memory | 项目/team/private memory、frontmatter、相关记忆选择 | memory.md、agent_memory、context assembler | 中高 |
| UI/命令 | Ink UI、slash commands、权限弹窗、任务视图、插件管理 | 简单 CLI/bat/bridge | 高 |
| Git/PR | commit、review、PR、worktree、GitHub app 工作流 | 基础 shell/git 能力 | 中高 |

## 后续优先路线

1. `Stage 15: Event Stream Runtime and Tool Executor v2`
2. 工具协议正式化，补齐只读、危险、并发安全、中断行为、权限检查。
3. 会话 transcript、resume、rewind、compact 系统。
4. 权限规则、hook、bash 风险分析和拒绝记忆。
5. task/team 升级为真实后台 worker 和独立 transcript。
6. MCP 升级为完整 connection manager，补 OAuth、重连、list_changed、resources/prompts 索引。
7. memory directory、frontmatter、相关 memory 选择。
8. 最小 slash command 和插件系统。

## 后续 agent 注意事项

- 不要只看工具名是否存在，要看能力是否产品级等价。
- 不要把教学版 task/team/cron/monitor 当作 ClaudeCode 等价实现。
- 不要先做复杂 UI，先补运行时和工具执行地基。
- 不要绕过 `start_oauth_agent.bat` 真实可见终端验收规则。
- 不要为了追赶 ClaudeCode 私有能力而破坏 learning_agent 的可理解性。

完整基线请读取：`agent_memory/claude_code_gap_baseline.md`

