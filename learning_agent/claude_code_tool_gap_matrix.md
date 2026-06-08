# Claude Code 工具清单与 learning_agent 差距矩阵

更新时间：2026-05-26

## 结论

## Prompt Architecture v1 beyond-parity note

- Tool parity 已经在公开可复现 core 层完成：Tool Catalog、Tool Pool、ToolPolicy、deferred `tool_search`、per-tool output protocol、MCP lifecycle、Real Chrome workflow gate、Plan mode guard、Observation 和长工具结果落盘都属于已落地的 core parity。
- Prompt Architecture v1 是 beyond-parity 控制层，不是继续补单个工具；它把 Prompt Registry、Context Assembler、Memory index、Prompt Surface Report、Token Budget Report、Compact Summary 和 Evidence Ledger bridge 放到工具层之上。
- `prompt_surface_report` 解释本轮加载了什么、为什么加载、来源和加载策略是什么，以及内容是 loaded、indexed、compacted 还是 truncated。
- `token_budget_report` 解释 prompt/tool/context 预算，尤其是 Prompt blocks、Current Tool Pool 和 estimated_total_tokens。
- long memory 和 project files 默认索引化；需要全文时必须在当前轮显式 read。历史设计文档和旧计划不会自动影响模型，除非当前轮显式读取。
- Compact Summary 只负责压缩上下文并保留来源边界；Evidence Ledger bridge 只负责把 observation events 变成证据索引，二者边界不同。

Claude Code 的工具体系不是“把所有工具一次性塞进模型上下文”这么简单。它更像一个工具操作系统：

1. 内置工具先由 `tools.ts` 注册成基础工具池。
2. 权限系统按用户设置、模式和风险过滤工具。
3. MCP server 启动后通过 `tools/list` 动态发现外部工具，并包装成 `mcp__server__tool` 形式。
4. 工具过多时，`ToolSearch` 负责延迟发现，避免上下文被工具 schema 撑爆。
5. 子 agent、team、cron、worktree、skills、MCP resources/prompts 等能力都围绕这个工具池扩展。

learning_agent 已经完成了最小可用的工具循环、MCP stdio 接入、MCP Streamable HTTP JSON POST 最小版、MCP HTTP session/stream lifecycle v1、MCP OAuth/auth metadata 说明入口、旧 SSE transport 明确边界、浏览器搜索 MCP、工作区 MCP、后台命令、Todo、Notebook 读写、MCP resources、MCP prompts、本地 Skill、结构化澄清、子 agent 雏形、任务生命周期最小版、任务管理视图、教学版 team/peer 通信生命周期、peer 绑定后台 task、Plan mode 执行验证闭环、Worktree 隔离状态最小版、LSP 最小版、REPL 安全批量编排最小版、Cron/Monitor 进程内记录最小版，Tool Architecture v2 核心主干，Phase 1 ToolPolicy/Permission v2、Phase 2 per-tool output protocol、Phase 3 MCP Lifecycle Parity、Phase 4 Real Chrome workflow gate、Phase 5 Plan/Task/Worktree hardening、Phase 6 observation/result persistence，以及 Phase 7 parity checklist 与回归测试收口。Phase 1 已覆盖工具 metadata 扩展、MCP annotations 与 `_meta` 映射、deny rule、skill/workflow gate、`tool_search select` policy、执行前 policy guard、用户拒绝记忆、子 agent policy 继承；Phase 2 已把 `tool_calls[].arguments` 从共享大对象改成按 `tool_call.name` 绑定的 per-tool `anyOf` 分支，避免同一 Tool Pool 内不同工具参数串味；Phase 3 已捕获 stdio/HTTP SSE JSON-RPC notifications，并让 `tools/list_changed` 刷新 registry 与 ToolSearch catalog，让 `prompts/list_changed` / `resources/list_changed` 进入生命周期事件和 MCP skills/search 索引失效挂点；Phase 4 已把真实浏览器需求和独立 Chromium 默认路径分开；Phase 5 已让计划确认前副作用工具被执行层硬拦截，并明确 worktree 当前是状态型 fallback；Phase 6 已把 MCP call progress、策略阻断、skill/workflow 事件和长工具结果落盘纳入结构化 observation。当前可以把 learning_agent 的公开可复现 agent core 视为已基本追平 ClaudeCode/Codex 的成熟工具架构思路，但不声称复制 ClaudeCode 私有产品能力。

## 主要源码依据

- Claude Code 基础工具注册：`D:\ClaudeCode-main\ClaudeCode-main\tools.ts`
- Claude Code agent/subagent 工具权限分组：`D:\ClaudeCode-main\ClaudeCode-main\constants\tools.ts`
- Claude Code MCP 工具发现和调用：`D:\ClaudeCode-main\ClaudeCode-main\services\mcp\client.ts`
- Claude Code MCP 工具命名：`D:\ClaudeCode-main\ClaudeCode-main\services\mcp\mcpStringUtils.ts`
- Claude Code MCP 配置类型：`D:\ClaudeCode-main\ClaudeCode-main\services\mcp\types.ts`
- learning_agent 主体：`<repo-root>\learning_agent\learning_agent.py`
- learning_agent browser/search MCP：`<repo-root>\learning_agent\browser_search_mcp_server.py`
- learning_agent workspace MCP：`<repo-root>\learning_agent\workspace_tools_mcp_server.py`

## Claude Code 工具清单

### 默认或核心内置工具

| Claude Code 工具 | 作用 | learning_agent 当前对应能力 |
|---|---|---|
| `Agent` / legacy `Task` | 启动子 agent 执行独立任务 | 已实现最小版：`task` 可启动同进程子 agent，支持 prompt、allowed_tools、max_turns、background=true |
| `TaskOutput` | 读取子任务输出 | 已实现最小版：`task_output` 可按 `task_id` 读取同步或后台子 agent 的状态、元信息和输出 |
| `Bash` | 执行 shell 命令 | 部分对应：`start_background_command` 与 MCP `run_powershell` |
| `Glob` | 文件模式查找 | 已有 MCP `mcp__workspace_tools__glob` |
| `Grep` | 内容搜索 | 已有 MCP `mcp__workspace_tools__grep` |
| `Read` | 读取文件 | 已有内置 `read_file` 与 MCP `mcp__workspace_tools__read_file` |
| `Edit` | 精确编辑文件 | 已有 MCP `mcp__workspace_tools__edit_file` |
| `Write` | 写文件 | 已有内置 `write_file` 与 MCP `mcp__workspace_tools__write_file/create_file` |
| `NotebookEdit` | 编辑 notebook cell | 已有内置 `notebook_edit`；另有 `notebook_read` |
| `WebFetch` | 读取 URL 内容 | 已有 MCP `mcp__browser_search__fetch_url` |
| `WebSearch` | 网络搜索 | 已有 MCP `mcp__browser_search__web_search` |
| `TodoWrite` | 维护任务清单 | 已有 `todo_read` / `todo_write`，但命名和行为还不是 Claude Code 同款 |
| `Skill` | 加载技能说明和技能资源 | 已实现最小版：`skill_list` 扫描本地 `skills/*/SKILL.md`，`skill_load` 按名称加载说明 |
| `EnterPlanMode` | 进入计划模式 | 已实现最小版：`enter_plan_mode` 可记录 reason、goal、steps 并提示只计划不执行 |
| `ExitPlanMode` | 退出计划模式并请求用户确认 | 已实现最小版：`exit_plan_mode` 可输出 plan、steps 并提示等待用户确认 |
| `VerifyPlanExecution` | 验证计划执行 | 已实现最小版：`verify_plan_execution` 可汇总 plan、executed_steps、evidence、open_items 和最终 status |
| `AskUserQuestion` | 结构化向用户提问 | 已实现最小版：`ask_user_question` 可输出 1-3 个结构化澄清问题，每题带 2-4 个选项 |
| `TaskStop` | 停止任务/子 agent | 已实现最小版：`task_stop` 可处理已完成任务，也可对后台子 agent 发出协作取消信号并标记 stopped |
| `TaskList` / `TaskGet` / `TaskUpdate` | 管理多个子任务记录 | 已实现最小版：`task_list` 可按状态列任务，`task_get` 可读任务详情，`task_update` 可更新 label/notes 元信息 |
| `SendMessage` | 向其他 agent 发消息 | 已实现教学最小版：`send_message` 可把消息写入指定 peer 的进程内 inbox，`read_peer_messages` 可读取，`ack_peer_message` 可确认处理；`team_start_task` 可把 peer 绑定到后台子任务 |
| `SendUserMessage` / legacy `Brief` | 给用户发送最终可见消息 | 未实现，learning_agent 目前直接打印回答 |
| `ListMcpResourcesTool` | 列 MCP resources | 已实现最小版：`list_mcp_resources` 可列出已启动 MCP server 暴露的 resources |
| `ReadMcpResourceTool` | 读 MCP resource | 已实现最小版：`read_mcp_resource` 可按 `server` + `uri` 读取资源正文 |
| MCP prompts | 读取 MCP server 暴露的提示词和轻量规程 | 已实现最小版：`list_mcp_prompts` 可列 prompts，`read_mcp_prompt` 可按 `server` + `name` + `prompt_arguments` 读取正文 |
| `ToolSearch` | 延迟搜索可用工具 | Phase 1 已完成 ToolPolicy/Permission v2：`tool_search` 可搜索完整 Tool Catalog，并用 `select:<tool_name>` 把允许的 deferred 工具加入后续 Tool Pool；`blocked`、`needs_skill`、`needs_workflow` 会拒绝 select |

### 条件启用或高级内置工具

| Claude Code 工具 | 启用条件/定位 | learning_agent 当前状态 |
|---|---|---|
| `Config` | ant 用户/配置管理 | 未实现，低优先级 |
| `Tungsten` | 内部终端/实验工具 | 未实现，低优先级 |
| `SuggestBackgroundPR` | 后台 PR 建议 | 未实现，低优先级 |
| `WebBrowser` | 真浏览器工具 | 已实现真实 Chrome workflow gate：默认仍用独立 Playwright Chromium；用户明确要求真实浏览器、桌面 Chrome、当前浏览器或登录态时，先走 `browser_profile_status`，再通过 `browser_connect_real_chrome` 且 `confirm_real_profile=true` 连接真实 Chrome 登录态，连接成功前阻断普通独立浏览器动作 |
| `TaskCreate` / `TaskGet` / `TaskUpdate` / `TaskList` | TodoV2 / team 内任务系统 | 未实现 |
| `OverflowTest` | 测试工具 | 不需要 |
| `CtxInspect` | 上下文检查 | 未实现，中低优先级 |
| `TerminalCapture` | 终端捕获 | 未实现，中优先级 |
| `LSP` | 语言服务能力 | 已实现最小版：`lsp_symbols` / `lsp_definition` / `lsp_diagnostics` 使用 Python 标准库 `ast` 支持 `.py` 文件符号、定义和语法诊断；尚不是真实 language server |
| `EnterWorktree` / `ExitWorktree` | 工作树隔离 | 已实现状态型 fallback：`enter_worktree` / `exit_worktree` 可记录轻量隔离状态、隔离目录、原因、目标、总结、遗漏项和 `mode=state_only_fallback`；尚不创建真实 git worktree |
| `ListPeers` | 多 agent peer 列表 | 已实现教学最小版：`list_peers` 可查看 peer 元信息、状态、inbox 数量、待确认数量、最新消息摘要、绑定 task id 和 task 状态 |
| `TeamCreate` / `TeamDelete` | 并行 agent team | 已实现教学最小版：`team_create` 可登记 peer；`team_start_task` 可为 peer 启动并绑定后台 task；`team_delete` 可在 `confirm_delete=true` 时删除 peer 和进程内 inbox |
| `VerifyPlanExecution` | 验证计划执行 | 已实现最小版：`verify_plan_execution` 可结构化输出执行步骤、证据、遗漏项和 verified/incomplete 状态 |
| `REPL` | 批量脚本式调用工具 | 已实现最小版：`repl` 可按顺序执行安全白名单内的只读、状态和符号工具批次；当前不是任意代码执行器，不执行写入、命令、外部 MCP 或子 agent 启动 |
| `Workflow` | workflow scripts | 未实现，低到中优先级 |
| `Sleep` | 等待/延迟 | 未实现，低优先级 |
| `CronCreate` / `CronDelete` / `CronList` | 定时任务 | 已实现最小版：`cron_create` / `cron_list` / `cron_delete` 可登记、列出和回收进程内定时任务记录；尚不创建系统定时器、不自动执行、不跨进程常驻 |
| `RemoteTrigger` | 远程触发 | 未实现，低优先级 |
| `Monitor` | 监控任务 | 已实现最小版：`monitor` 通过 `action=create/list/delete/record_result` 管理进程内监控记录和最近观察结果；尚不启动真实监听器、不自动检查、不推送通知 |
| `SendUserFile` | 发送文件给用户 | 未实现，低到中优先级 |
| `PushNotification` | 推送通知 | 未实现，低优先级 |
| `SubscribePR` | PR 订阅 | 未实现，低优先级 |
| `PowerShell` | Windows PowerShell 工具 | 部分对应：MCP `mcp__workspace_tools__run_powershell` |
| `Snip` | 截图/片段工具 | 未实现，中优先级 |
| `TestingPermission` | 测试权限工具 | 不需要 |

### Claude Code MCP 支持范围

| MCP 能力 | Claude Code 状态 | learning_agent 当前状态 | 差距 |
|---|---|---|---|
| stdio server | 支持 | 已支持 | 基本完成 |
| SSE server | 支持 | 已识别配置并明确报错边界 | 当前未实现旧 HTTP+SSE 双端点协议；优先建议改用 Streamable HTTP |
| HTTP server | 支持 | 已实现 v1：`transport=http` + `url` + `headers`，支持 initialize、tools/list、tools/call、resources/list/read、prompts/list/get 的 JSON POST 路径，可解析 `text/event-stream` POST 响应，支持 `listen_mcp_stream` 有界 `GET` 读取 SSE、`Last-Event-ID` 恢复、关闭 session 时尝试 `DELETE`，并能把 401 鉴权挑战转成 authenticate 说明工具 | 仍缺永久后台 listener、旧 HTTP+SSE 双端点兼容和完整 server-to-client capabilities |
| WebSocket server | 支持 | 未支持 | 低到中优先级 |
| SDK server | 支持 | 未支持 | 低优先级 |
| claude.ai proxy server | 支持 | 未支持 | 低优先级 |
| OAuth / auth server metadata | 支持 | 已实现最小版：HTTP 401 时解析 `WWW-Authenticate` 的 `resource_metadata`，保存 auth challenge，并在 doctor / authenticate 工具里解释配置入口；不自动请求 metadata URL，不自动交换 token | 后续补完整 OAuth UI、动态客户端注册、PKCE、资源参数和安全 URL 校验 |
| `tools/list` | 支持 | 已支持 | 基本完成 |
| `tools/call` | 支持 | 已支持 | 基本完成 |
| `tools/list_changed` 通知刷新 | 支持 | Phase 3 已支持第一轮骨架：stdio/HTTP SSE 可缓存 JSON-RPC notification，registry 消费后重跑 `tools/list` 并清理 Tool Catalog cache，`tool_search` 能看到刷新后的 MCP 工具；MCP call progress 已记录 permission/start/completed/failed | 后续补长期监听、跨进程持久 stream 和更完整 server-to-client capabilities |
| MCP tool annotations | 支持 readOnly/destructive/openWorld/search 分类 | Phase 1 已读取 MCP annotations 与 `_meta`，并映射 `readOnlyHint`、`destructiveHint`、`openWorldHint`、`anthropic/searchHint`、`anthropic/alwaysLoad` / `alwaysLoad` 到工具 metadata | 后续继续细化风险评分和 UI 展示 |
| MCP resources | 支持列出和读取 | 已实现最小版：stdio client 支持 `resources/list`、`resources/read`，agent 暴露 `list_mcp_resources` / `read_mcp_resource`；Phase 3 已记录 `resources/list_changed` 生命周期事件并提供 MCP skills/search 失效挂点 | 后续补资源内容类型、订阅语义和长期监听 |
| MCP prompts | 支持转成命令/skills | 已实现最小版：stdio client 支持 `prompts/list`、`prompts/get`，agent 暴露 `list_mcp_prompts` / `read_mcp_prompt`；Phase 3 已记录 `prompts/list_changed` 生命周期事件并提供 MCP skills/search 失效挂点 | 后续补 prompt 命令化封装、完整 MCP skills 合并和权限策略 |
| MCP skills | 支持 | 部分覆盖：可通过 MCP prompts 读取轻量 skill 说明，但不支持远程 skill 安装、市场或权限策略 | 中高优先级 |
| MCP auth pseudo-tool | 支持 `mcp__server__authenticate` | 已实现最小版：auth-required server 暴露 `mcp__server__authenticate` 伪工具，返回 `Authorization: Bearer`、`mcp_servers.json` headers 和 `resource_metadata` 说明 | 后续补真实 OAuth 登录流程 |
| ToolSearch 中搜索 MCP 工具 | 支持 | Phase 1 已完成 deferred catalog 和 `select:<tool_name>`；Phase 2 已隔离输出参数；Phase 3 已让 `tools/list_changed` 后的刷新结果进入 ToolSearch | 后续补长期监听、call progress 和真实 Chrome workflow gate |

## learning_agent 已有工具清单

### 内置工具

| learning_agent 工具 | 作用 |
|---|---|
| `read_file` | 读取 learning_agent 工作区内文本文件 |
| `write_file` | 权限确认后写入 learning_agent 工作区内文件 |
| `append_memory` | 权限确认后追加长期记忆 |
| `todo_read` | 读取当前任务清单 |
| `todo_write` | 完整覆盖当前任务清单 |
| `start_background_command` | 权限确认后启动后台命令 |
| `read_background_command` | 读取后台命令增量输出 |
| `stop_background_command` | 权限确认后停止后台命令 |
| `notebook_read` | 读取 `.ipynb` notebook cell 摘要或指定 cell |
| `notebook_edit` | 权限确认后替换 `.ipynb` 指定 cell source |
| `tool_search` | 搜索完整 Tool Catalog，并用 `select:<tool_name>` 把 deferred 工具加载进后续 Tool Pool |
| `list_mcp_resources` | 权限确认后列出已启动 MCP server 暴露的 resources |
| `read_mcp_resource` | 权限确认后按 `server` + `uri` 读取 MCP resource 正文 |
| `list_mcp_prompts` | 权限确认后列出已启动 MCP server 暴露的 prompts |
| `read_mcp_prompt` | 权限确认后按 `server` + `name` 读取 MCP prompt，可传 `prompt_arguments` |
| `skill_list` | 列出工作区本地 `skills/*/SKILL.md` |
| `skill_load` | 按名称读取本地 skill 说明书 |
| `ask_user_question` | 输出结构化澄清问题和选项，等待用户下一轮回答 |
| `task` | 启动同进程子 agent 执行边界清楚的子任务，并可用 `allowed_tools` 限制工具范围 |
| `task_output` | 按 `task_id` 读取子任务状态、元信息和输出 |
| `task_stop` | 按 `task_id` 停止或标记停止子任务 |
| `task_list` | 列出当前 agent 进程内的同步或后台子任务，并可按状态筛选 |
| `task_get` | 按 `task_id` 读取子任务详情、prompt、标签、备注和输出摘要 |
| `task_update` | 按 `task_id` 更新子任务 label/notes 元信息，不修改运行状态或输出 |
| `team_create` | 登记教学版 peer 的名称、角色、状态和职责备注 |
| `send_message` | 向指定 peer 的进程内 inbox 写入一条可审计消息 |
| `team_start_task` | 为指定 peer 启动后台 `task`，把返回的 `task_id` 绑定到 peer，并继续通过 `task_output` / `task_stop` 管理 |
| `list_peers` | 列出 peer 总览、角色、状态、inbox 数量、待确认消息数量、最新消息摘要、绑定任务 id 和任务状态 |
| `read_peer_messages` | 读取指定 peer 的进程内 inbox，默认只返回待确认消息，可包含已确认历史 |
| `ack_peer_message` | 标记指定 peer 的某条消息已处理，并保存确认时间和备注 |
| `team_delete` | 显式确认后删除教学版 peer，并丢弃它的进程内 inbox |
| `enter_plan_mode` | 进入计划模式，保存原因、目标和初步步骤 |
| `exit_plan_mode` | 输出最终计划并提示等待用户确认 |
| `verify_plan_execution` | 汇总计划执行后的已执行步骤、验证证据、遗漏项和最终状态 |
| `enter_worktree` | 进入轻量工作区隔离状态，保存隔离目录、原因和目标，不创建真实 git worktree |
| `exit_worktree` | 退出轻量工作区隔离状态，汇总结果、遗漏项和最终状态 |
| `lsp_symbols` | 读取 Python `.py` 文件的类、方法和函数符号 |
| `lsp_definition` | 按符号名定位 Python `.py` 文件中的类、方法或函数定义 |
| `lsp_diagnostics` | 读取 Python `.py` 文件的语法诊断 |
| `repl` | 按顺序批量执行安全白名单内的只读、状态和符号工具，最多 5 个子调用 |
| `cron_create` | 登记教学版进程内定时任务记录，不创建真实系统定时器 |
| `cron_list` | 列出教学版进程内定时任务记录，可按 active/deleted/all 筛选 |
| `cron_delete` | 显式确认后回收教学版进程内定时任务记录 |
| `monitor` | 通过 create/list/delete/record_result 管理教学版进程内监控记录和最近观察结果 |
| `observation_events` / `tool_results` | 结构化记录 MCP progress、策略阻断、workflow 进展和长工具结果落盘路径 |

### 当前 MCP server

| MCP server | 暴露工具 |
|---|---|
| `browser_search` | `mcp__browser_search__web_search`, `mcp__browser_search__fetch_url` |
| `browser_automation` | 默认独立 Playwright Chromium，并提供可选高风险真实 Chrome 登录态连接：`browser_open`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_press_key`, `browser_wait`, `browser_screenshot`, `browser_tabs`, `browser_console`, `browser_network`, `browser_upload_file`, `browser_downloads`, `browser_evaluate`, `browser_close`, `browser_connect_real_chrome`, `browser_disconnect_real_chrome`, `browser_profile_status` |
| `workspace_tools` | `mcp__workspace_tools__list_dir`, `mcp__workspace_tools__glob`, `mcp__workspace_tools__grep`, `mcp__workspace_tools__read_file`, `mcp__workspace_tools__write_file`, `mcp__workspace_tools__create_file`, `mcp__workspace_tools__copy_file`, `mcp__workspace_tools__move_file`, `mcp__workspace_tools__delete_file`, `mcp__workspace_tools__run_powershell`, `mcp__workspace_tools__edit_file` |

## 差距分层

### 已基本追平的能力

| 能力 | 状态 |
|---|---|
| 文件读取/写入 | 已有，但 Claude Code 的 Read/Edit/Write 用户体验更成熟 |
| Glob/Grep | 已有 MCP 版本 |
| WebSearch/WebFetch | 已有 browser_search MCP 版本 |
| NotebookEdit | 已有最小版，且额外补了 NotebookRead |
| TodoWrite | 已有最小版 todo_read/todo_write |
| MCP stdio tools/list/tools/call | 已有 |
| 后台命令 | 已有最小版后台三件套 |
| 工具循环轮次 | 已改成默认不写死固定 8 轮 |
| 结构化澄清提问 | 已有 `ask_user_question` 最小版 |
| 子 agent 委派 | 已有 `task` 最小版：单进程子 agent、工具白名单、文本 summary、background=true 后台启动 |
| 子任务生命周期 | 已有 `task_output` / `task_stop` 最小版：同步/后台子任务可查询输出，后台任务可协作取消 |
| 子任务管理视图 | 已有 `task_list` / `task_get` / `task_update` 最小版：可列任务、读详情、更新 label/notes |
| 多 agent team 通信生命周期 | 已有 `team_create` / `send_message` / `team_start_task` / `list_peers` / `read_peer_messages` / `ack_peer_message` / `team_delete` 教学最小版：可登记 peer、写入 peer inbox、为 peer 绑定后台 task、查看 peer 总览、读取消息、确认消息、删除 peer |
| Plan mode | 已有 `enter_plan_mode` / `exit_plan_mode` / `verify_plan_execution` 最小闭环：复杂改动前先计划、等待确认，执行后结构化验证 |
| Worktree 隔离状态 | 已有 `enter_worktree` / `exit_worktree` 最小版：大范围改动前记录隔离上下文，结束时结构化交接 |
| LSP 最小版 | 已有 `lsp_symbols` / `lsp_definition` / `lsp_diagnostics`：用 Python 标准库 `ast` 支持 `.py` 文件符号列表、定义定位和语法诊断 |
| REPL 安全批量编排 | 已有 `repl` 最小版：可把最多 5 个安全只读、状态或符号工具调用组织成一批可审计步骤 |
| Cron/Monitor 进程内记录 | 已有 `cron_create` / `cron_list` / `cron_delete` / `monitor` 最小版：可登记、列出、回收定时任务和监控记录，并为监控保存最近观察结果 |
| MCP prompts / 轻量 MCP skills | 已有 `list_mcp_prompts` / `read_mcp_prompt` 最小版：可发现并读取 MCP server 暴露的 prompts 或轻量规程 |
| MCP HTTP session/stream lifecycle | 已实现 v1：POST 可解析 `text/event-stream`，`listen_mcp_stream` 可有界 `GET` 读取 SSE，支持 `Last-Event-ID` 恢复和关闭 session 时尝试 `DELETE`；仍不是永久后台 listener |
| per-tool output protocol | 已实现 Phase 2：`tool_calls.items` 使用按工具名绑定的 `anyOf` 分支，每个 `arguments` 只包含该工具自己的参数，不再依赖同一 Tool Pool 共享大参数对象 |

### 高优先级缺口

| 缺口 | 为什么重要 | 推荐实现 |
|---|---|---|
| `ToolSearch` / 工具延迟发现 | Claude Code 能承载大量工具而不把所有 schema 塞进上下文；这是扩展到很多 MCP server 的关键 | 已完成 Phase 1 ToolPolicy/Permission v2：Tool Catalog / Tool Pool 分层、MCP deferred、metadata、deny、skill/workflow gate、select policy、执行 guard、拒绝记忆和子 agent policy 继承 |
| per-tool output protocol | 同一 Tool Pool 内可见工具越来越多时，共享 `arguments` schema 会让模型把 A 工具参数误塞进 B 工具，例如把真实 Chrome 确认字段塞进 `browser_open` | 已完成 Phase 2：每个 tool_call 分支把 `name` 单值 enum 与该工具自己的 strict arguments schema 绑定，并保留解析器兼容兜底 |
| `ListMcpResourcesTool` / `ReadMcpResourceTool` | MCP 不只有工具，还有资源；很多 server 会把文件、schema、上下文暴露成 resources | 已完成最小版；后续可补 `resources/list_changed` 刷新和更多内容类型 |
| `Skill` | skill 是 Claude Code 把“说明书/操作规程/领域能力”低成本接入模型的核心方式 | 已完成本地最小版和 MCP prompts 读取最小版；后续再补完整 MCP skills 安装和权限策略 |
| `AskUserQuestion` / 结构化提问 | 让 agent 在不确定时提出选项，而不是乱猜 | 已完成最小版；后续可接入更完整的交互 UI 或 plan mode |
| `Agent` / `Task` 子 agent 雏形 | Claude Code 的复杂任务能力来自子 agent 分工，不只是工具数量 | 已完成最小版：输入 prompt、可选 allowed_tools、返回 summary、记录 task_id，并支持 `task_output` / `task_stop` 的同步与后台生命周期查询 |
| Plan mode | Claude Code 复杂改动前会先计划、再请求确认，并在执行后核对证据 | 已完成 `enter_plan_mode` / `exit_plan_mode` / `verify_plan_execution`，并已在执行层硬拦截确认前的写入、删除、命令和外部副作用工具；后续可补更完整 UI 确认流 |

### 中优先级缺口

| 缺口 | 为什么重要 | 推荐实现 |
|---|---|---|
| 真浏览器自动化 `WebBrowser` | 搜索/fetch 只能读网页，不能登录、点击、截图、操作页面 | 已实现真实 Chrome workflow gate；默认仍走独立 Playwright Chromium，真实浏览器/登录态需求会先要求 `browser_profile_status`，再连接真实 Chrome，连接成功前阻断独立浏览器动作 |
| Worktree 隔离 | 避免 agent 大改动污染主工作区 | 已完成进入/退出轻量隔离状态并明确 `state_only_fallback`；后续可接真实 git worktree 创建、切换和清理 |
| LSP | 让 agent 能做符号级理解、跳转、诊断 | 已完成 Python `.py` 最小版；后续可接真实 language server、跨文件索引和 TypeScript |
| Cron/Monitor | 让 agent 能持续观察和定时执行 | 已完成进程内记录最小版；后续可接真正调度器、持久化、通知和权限确认流 |
| REPL | 批量调用工具，减少多轮开销 | 已完成安全白名单最小版；后续可扩展更真实的会话式脚本能力和更细粒度权限 |
| MCP prompts / MCP skills | 让 MCP server 不只给工具，还给可调用提示词和技能 | 已完成 MCP prompts 发现/读取最小版；后续补完整 MCP skills 安装、权限市场和自动刷新 |
| MCP HTTP/SSE | 连接远程 MCP server | 已完成 Streamable HTTP transport 与 session/stream lifecycle v1；仍缺旧 HTTP+SSE 双端点兼容、永久后台 listener 和完整 server-to-client capabilities |

### 低优先级或暂不需要

| 工具/能力 | 原因 |
|---|---|
| `Tungsten`、`OverflowTest`、`TestingPermission` | 偏内部或测试，不是最小 agent 进化主线 |
| `PushNotification`、`SubscribePR`、`RemoteTrigger` | 依赖产品形态和账号体系，当前收益低 |
| `claude.ai proxy` | Claude Code 自身生态能力，当前 learning_agent 不必优先复刻 |

## 下一步推荐

当前进度：`tool_search`、Tool Architecture v2 core spine、Phase 1 ToolPolicy/Permission v2、Phase 2 per-tool output protocol、`list_mcp_resources`、`read_mcp_resource`、`list_mcp_prompts`、`read_mcp_prompt`、`skill_list`、`skill_load`、`ask_user_question`、`task`、`task_output`、`task_stop`、`task_list`、`task_get`、`task_update`、`team_create`、`send_message`、`team_start_task`、`list_peers`、`read_peer_messages`、`ack_peer_message`、`team_delete`、`enter_plan_mode`、`exit_plan_mode`、`verify_plan_execution`、`enter_worktree`、`exit_worktree`、`lsp_symbols`、`lsp_definition`、`lsp_diagnostics`、`repl`、`cron_create`、`cron_list`、`cron_delete`、`monitor`、MCP `transport=http`、MCP HTTP session/stream lifecycle v1 和 MCP `mcp__server__authenticate` 鉴权说明入口已经完成最小实现；agent 现在能搜索完整 Tool Catalog、把允许的 deferred MCP 工具按需 select 进当前 Tool Pool、用 deny rule / skill gate / workflow gate 拒绝不满足策略的 select、在执行前做 policy guard、记住同一工具和参数的用户拒绝、让子 agent 继承父 agent policy context，并且用按工具名分支的结构化输出协议约束每个 tool_call 只能携带本工具参数，读取 MCP resources、读取 MCP prompts 或轻量远程规程、加载本地 skill 说明书、结构化澄清需求，也能把边界清楚的子任务交给同进程子 agent 同步或后台执行、查询子任务输出、停止后台子任务、列出多个任务、读取任务详情、更新任务标签和备注，登记教学版 peer、向 peer inbox 留消息、为 peer 绑定后台 task、查看 peer 总览、读取 peer 消息、确认消息处理、删除 peer，并能在复杂改动前先输出待确认计划、执行后结构化汇总验证证据和遗漏项，在大范围改动前进入轻量工作区隔离状态并在结束时交接，还能对 Python `.py` 文件读取符号、定位定义和查看语法诊断，把多次安全只读、状态或符号查询组织成一批可审计的 REPL 批量步骤，登记进程内定时任务和监控记录，通过 Streamable HTTP 链路连接远程 MCP server、解析 SSE POST 响应、用 `listen_mcp_stream` 有界读取 GET stream、用 `Last-Event-ID` 恢复、关闭 session 时尝试 `DELETE`，并在远程 server 要求鉴权时给出可发现、可解释的配置入口。

当前最推荐优先完成 Phase 3 之后的下一层：真实 Chrome workflow / skill gate、call progress、auth/OAuth 边界升级，以及更完整的 MCP server-to-client capabilities。

Phase 3 当前状态：已完成 MCP lifecycle 第一轮可验证骨架，包含 stdio notification 捕获、HTTP SSE notification 捕获、`tools/list_changed` 后重建 MCP registry、清理 `LearningAgent` Tool Catalog cache、让 ToolSearch 搜到刷新后的 MCP 工具，以及 prompts/resources list_changed 的生命周期审计和 MCP skills/search 刷新版本挂点。该阶段尚未实现永久后台 listener、完整 call progress UI 或完整 OAuth 产品流程。

推荐第一批实现顺序：

1. Tool Architecture v2 core spine：`AgentTool`、Tool Catalog、Tool Pool、MCP deferred、`tool_search select:<tool_name>` 和执行门禁。已完成核心主干。
2. ToolPolicy/Permission v2：metadata、deny、skill/workflow gate、select policy、执行 guard、拒绝记忆、子 agent policy 继承。已完成 Phase 1。
3. per-tool output protocol：`tool_calls.items` 用 per-tool `anyOf` 分支绑定工具名和专属参数。已完成 Phase 2。
4. `list_mcp_resources` / `read_mcp_resource`：补齐 MCP resources。已完成最小版。
5. `skill_list` / `skill_load`：先做本地 skills。已完成最小版。
6. `ask_user_question`：让 agent 可以结构化澄清需求。已完成最小版。
7. `task` / 子 agent 雏形：开始进入 Claude Code 的多 agent 能力。已完成最小版。
8. Plan mode：复杂改动前先计划并请求确认。已完成最小版。
9. `TaskOutput` / `TaskStop`：让子 agent 任务具备可查询、可停止的生命周期。已完成同步与后台最小版。
10. 异步 `task` / 后台子 agent：让子任务不阻塞主 agent，并让 `task_stop` 真正可以取消运行中的子任务。已完成最小版。
11. `task_list` / `task_get` / `task_update`：为多个同步/后台子任务提供任务列表、详情读取和元信息更新。已完成最小版。
12. `team_create` / `send_message` / `list_peers`：在任务管理视图之后补多 agent 通信和登记。已完成教学最小版。
13. `team_delete` / `read_peer_messages` / `ack_peer_message`：让 team 从“登记和留言”升级成“可读取、可确认、可回收”的协作结构。已完成教学最小版。
14. `team_start_task` / peer 绑定后台 `task`：让 team 从“进程内登记和消息队列”升级成“可运行、可查询、可停止”的协作成员。已完成教学最小版。
15. `VerifyPlanExecution`：让计划模式不只输出计划，还能结构化验证执行证据、遗漏项和停止条件。已完成最小版。
16. `EnterWorktree` / `ExitWorktree`：让大改动进入隔离工作区状态，降低污染主工作区的风险。已完成轻量状态版。
17. `LSP`：补语言服务最小版，先提供符号列表、定义定位或诊断读取。已完成 Python `.py` 最小版。
18. `REPL`：补批量脚本式调用工具能力，减少重复多轮开销。已完成安全白名单最小版。
19. `Cron/Monitor`：补持续观察和定时检查的最小任务记录能力。已完成进程内记录最小版。
20. `MCP prompts / MCP skills`：让 MCP server 暴露的提示词或技能说明进入 agent 可发现、可加载的工作流。已完成 prompts 发现/读取最小版。
21. `MCP HTTP/SSE transport`：让当前 MCP 能力从本地 stdio 扩展到远程 server。已完成 Streamable HTTP JSON POST 最小版与 session/stream lifecycle v1；旧 SSE 双端点仍是明确未实现边界。
22. `MCP OAuth/auth metadata`：让需要登录的远程 MCP server 有可发现、可解释的鉴权入口。已完成最小版。
23. `Prompt / Context Architecture v1`：升级成熟 coding agent 系统提示词、上下文策略和运行时规则分层。已完成 v1。
24. `MCP HTTP session/stream lifecycle`：已完成 v1，包含 `GET` 有界监听流、`DELETE` 会话关闭尝试、断线恢复和 `Last-Event-ID`；后续只保留永久后台 listener、旧 HTTP+SSE 双端点兼容和完整 server-to-client capabilities 作为缺口。

这样推进的好处是：先把“工具越来越多时还能找得到、用得准”的基础打牢，再补更复杂的子 agent。如果直接补全所有具体工具，短期看数量很多，但模型上下文会更快膨胀，工具选择也会更混乱。
