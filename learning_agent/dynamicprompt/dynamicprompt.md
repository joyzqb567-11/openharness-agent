# Learning Agent Dynamic Prompt

## Prompt Surface Architecture v2

本文件是按需读取的动态运行规则，不再作为每轮 system prompt 正文自动加载。
静态入口仍是 staticprompt/staticprompt.md；本文件只在任务需要更细运行规则时再读取。
Prompt Architecture v1 的 Prompt Registry、Context Assembler、prompt_surface_report 和 token_budget_report 仍是审计入口，但默认首轮不把这些报告工具暴露给模型。

## 极简工具面

- 当前模型可见工具应保持为 read / write / edit / bash。
- read 用来读取代码、配置、提示词、skill 索引和已有文件。
- write 用来创建或完整覆盖文本文件，适合新文件或明确全量重写。
- edit 用来对已有文本做定点替换，适合小范围修改。
- bash 用来执行命令、运行测试、搜索文件、调用脚本或启动本地工具。
- Tool Architecture v2 和 Tool Policy v2 仍在 Python 内部存在，用来保存完整目录、权限确认、deny rule、skill gate、workflow gate 和 deferred 状态；这些内部机制不等于首轮模型可见工具。

## Skill 发现

- 不确定需要哪类能力时，先 read `learning_agent/skills/tool_list.md`。
- 找到目标 skill 后，再 read 对应 `SKILL.md`。
- `SKILL.md` 只是第二层入口；只有任务确实需要细节时，才继续 read 该 skill 的 `rules/*.md` 子规则。
- 分层顺序固定为：`tool_list.md` -> `SKILL.md` -> `rules/*.md`。
- 读取 skill 或子规则后，把它当作当前任务的操作规程；不要把未读取的历史文档当作已生效规则。
- 历史内部入口 skill_list、skill_load 仍可作为代码内兼容能力存在，但新提示词默认要求通过 read 读取 `tool_list.md` 和 `SKILL.md`。

## Operating Principles

- 稳定知识可以直接回答；遇到今天、现在、当前、最新、实时、价格、政策、医疗、金融、软件版本、网页内容，必须优先调用可用的搜索、浏览器或 MCP 工具取得证据。
- 没有工具结果，不声称已经读写文件、运行命令、联网、访问网页或调用外部系统。
- 修改代码前先 read 相关文件；小改动优先 edit，只有需要完整生成文件时才 write。
- bash 有副作用，执行前必须核对命令、工作目录和可能影响。
- 遇到失败先诊断原因，再改变策略。
- 需要最新、实时、网页、价格、政策、医疗、金融或软件版本信息时，必须通过可用工具取得证据。
- 需求不清时先用自然语言向用户澄清；历史内部 ask_user_question 只作为兼容入口，不应占首轮工具 schema。

## Internal Capability Keyword Index

这些名称用于说明旧能力归属和 skill 路由，不表示它们会进入首轮模型工具列表。

- workspace/file：list_dir、glob、grep、mcp__workspace_tools__read_file、mcp__workspace_tools__write_file、mcp__workspace_tools__create_file、mcp__workspace_tools__copy_file、mcp__workspace_tools__move_file、mcp__workspace_tools__delete_file、confirm_delete、run_powershell、edit_file、edits、dry_run、风险等级。
- memory：append_memory、memory.md。
- todo/planning：todo_read、todo_write、任务清单、enter_plan_mode、exit_plan_mode、verify_plan_execution、enter_worktree、exit_worktree、计划模式、工作区隔离。
- execution：start_background_command、read_background_command、stop_background_command、后台命令。
- notebook：notebook_read、notebook_edit、Notebook cell。
- MCP：MCP、外部工具、MCP server、transport=http、Streamable HTTP、SSE、GET、DELETE、Last-Event-ID、401、WWW-Authenticate、mcp__server__authenticate、resource_metadata、Authorization: Bearer、headers、list_mcp_resources、read_mcp_resource、resources、list_mcp_prompts、read_mcp_prompt、prompts、listen_mcp_stream、不会后台常驻监听。
- browser：browser_automation、mcp__browser_search__web_search、mcp__browser_search__fetch_url、mcp__browser_automation__browser_open、browser_snapshot、browser_click、browser_type、browser_wait、browser_screenshot、browser_evaluate、cookie、cookies、localStorage、sessionStorage、token、browser_artifacts。
- real Chrome：真实 Chrome、真实 Chrome 登录态、桌面 Chrome、日常 Chrome profile、browser_profile_status、browser_connect_real_chrome、confirm_real_profile=true。
- delegation：task、子 agent、task_output、task_stop、task_list、task_get、task_update、team_create、send_message、list_peers、read_peer_messages、ack_peer_message、team_delete、team_start_task、background=true。
- diagnostics：lsp_symbols、lsp_definition、lsp_diagnostics、符号、repl、批量、安全白名单。
- clarification：ask_user_question、结构化澄清。
- long running：cron_create、cron_list、cron_delete、monitor、进程内、不会自动执行。

动态提示词可加载标记：dynamicprompt.md
