# 当前任务进度

## 2026-05-26 Prompt Architecture v1 Task 6 进度

- 已读取计划文件 `docs/superpowers/plans/2026-05-26-agent-prompt-architecture-v1.md`，确认本轮只执行 Task 6。
- 已在 `learning_agent/test_learning_agent.py` 新增文档测试：`test_runtime_instructions_mentions_prompt_architecture_v1_reports` 和 `test_readme_documents_prompt_registry_and_context_assembler`。
- 已更新 `learning_agent/runtime_instructions.md`、`learning_agent/README.md`、`learning_agent/claude_code_tool_gap_matrix.md` 和 `docs/superpowers/specs/claudecode_parity_checklist.md`，记录 Prompt Architecture v1 的 beyond-parity 边界与报告工具说明。
- 已覆盖 `learning_agent/test/75.md`，改为 Prompt Registry、Context Assembler、Memory index、Prompt Surface Report、Token Budget Report 和 Evidence Ledger bridge 的中文学习备份。
- 验证完成：文档测试输出为 `Ran 2 tests in 0.013s OK`。
- 验证完成：语法检查 `python -m py_compile learning_agent\test_learning_agent.py` 无输出，退出码为 0。
- 验证完成：相邻报告测试输出为 `Ran 4 tests in 0.031s OK`。

## 2026-05-24 Browser Automation MCP 设计阶段

- 2026-05-24：用户确认优先升级真实浏览器自动化，并选择混合路线：第一阶段使用独立 Playwright Chromium，第二阶段再考虑连接真实 Chrome。
- 2026-05-24：已确认第一版目标为成熟 agent 版工具清单，而不是只做基础打开、点击和截图。
- 2026-05-24：已确认允许安装 Python `playwright` 包并执行 Chromium 浏览器安装。
- 2026-05-24：已确认推荐架构：新增独立 `browser_automation` MCP server，不把 Playwright 直接塞进 `learning_agent.py`。
- 2026-05-24：已按用户要求把 `browser_evaluate` JavaScript 执行工具纳入第一版，并标记为高风险工具。
- 2026-05-24：早期设计阶段曾创建设计文档 `docs/superpowers/specs/2026-05-24-browser-automation-mcp-design.md`，当时只写设计、不进入代码实现；该条为历史记录。
- 2026-05-24：用户已确认设计文档。
- 2026-05-24：已创建实施计划 `docs/superpowers/plans/2026-05-24-browser-automation-mcp.md`，计划按依赖安装、红灯测试、MCP server scaffold、浏览器生命周期、交互/JS、截图上传下载日志、配置权限、文档记忆和最终验证推进。
- 2026-05-24：早期计划阶段当时尚未修改运行时代码，并等待用户选择执行方式；该条为历史记录，后续 Task 0-7 已推进完成。

## 2026-05-24 MCP OAuth/auth metadata 最小版

状态：已完成，红灯测试、专项测试和完整测试均已通过。

已完成：

- 按官方 MCP 授权规范确认最小边界：HTTP MCP server 可通过 `401` 的 `WWW-Authenticate` 暴露 `resource_metadata`，客户端应能识别并给出恢复路径。
- 新增红灯测试并确认失败：`test_mcp_http_401_exposes_authenticate_tool_with_metadata_hint`、`test_readme_explains_mcp_auth_metadata_boundaries`、`test_runtime_instructions_mentions_mcp_auth_metadata`。
- 新增 `McpAuthChallenge` 和 `McpAuthenticationRequired`，让 HTTP 401 不再只是普通 RuntimeError。
- 扩展 `McpHttpClient`：保存 401 鉴权挑战，解析 `resource_metadata`，并提供 `authenticate()` 说明文本。
- 扩展 `McpToolRegistry`：遇到 `McpAuthenticationRequired` 时注册 `mcp__server__authenticate` 伪工具，继续启动其他 MCP server，并允许 doctor 查询 auth challenge。
- 更新 MCP 工具风险分级，让 authenticate 工具显示为“鉴权说明/低风险”并提醒不要在参数里填写 access token。
- 更新 `runtime_instructions.md`、`README.md` 和 `claude_code_tool_gap_matrix.md`，说明 auth metadata、`WWW-Authenticate`、`Authorization: Bearer` 和不会自动 OAuth 的边界。

已通过：

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_401_exposes_authenticate_tool_with_metadata_hint learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_auth_metadata_boundaries learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_auth_metadata
```

结果：

```text
Ran 3 tests in 0.590s
OK
```

最终验证：

```powershell
<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py
```

结果：通过，无错误输出。

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_parses_http_and_sse_transport_fields learning_agent.test_learning_agent.LearningAgentTests.test_mcp_registry_creates_clients_by_transport learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_client_lists_calls_resources_and_prompts learning_agent.test_learning_agent.LearningAgentTests.test_mcp_sse_transport_fails_with_clear_boundary learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_401_exposes_authenticate_tool_with_metadata_hint learning_agent.test_learning_agent.LearningAgentTests.test_mcp_doctor_lists_visible_tools_from_configured_server learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_http_transport_boundaries learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_auth_metadata_boundaries learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_http_transport learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_auth_metadata
```

结果：

```text
Ran 10 tests in 1.233s
OK
```

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent
```

结果：

```text
Ran 173 tests in 5.857s
OK
```

备份：已创建 `learning_agent/test/42.md`。

下一步建议：

- 做 `MCP HTTP session/stream lifecycle` 最小版，优先补 GET 监听流、DELETE 会话关闭、断线恢复和 Last-Event-ID。

- 2026-05-24：已开始 `learning_agent` 的 `MCP prompts / MCP skills` 最小版任务，范围限定为已启动 stdio MCP server 的 prompts 发现和读取。
- 2026-05-24：已新增 MCP prompts 红灯测试并确认失败原因是工具未进入 schema、stdio client 未实现 prompts/list/get、registry 未实现 prompt 聚合读取、工具路由未实现、输出 schema 缺 `prompt_arguments`、运行规则未说明。
- 2026-05-24：已实现 `McpStdioClient.list_prompts` / `get_prompt`、prompt messages 文本转换、`McpToolRegistry.list_prompts` / `read_prompt`、`list_mcp_prompts` / `read_mcp_prompt` 工具 schema、权限确认和 agent 路由。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵和 `learning_agent_CONTEXT.md`；学习备份 `learning_agent\test\40.md` 已写入。
- 2026-05-24：验证命令 `py_compile learning_agent.py test_learning_agent.py` 已通过；MCP prompts 专项 `Ran 6 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 164 tests OK`。
- 2026-05-24：已完成 `learning_agent` 的 `cron_create` / `cron_list` / `cron_delete` / `monitor` Cron/Monitor 最小版，当前只保存进程内可审计记录。
- 2026-05-24：已新增 Cron/Monitor 红灯测试并确认失败原因是工具未进入 schema、路由未实现、输出 schema 缺 Cron/Monitor 参数、运行规则未说明。
- 2026-05-24：已实现 CronRecord / MonitorRecord 数据结构、工具 schema、工具路由、进程内记录表、创建/列表/删除/记录结果逻辑和删除确认门槛。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵和 `learning_agent_CONTEXT.md`；学习备份 `learning_agent\test\39.md` 正在写入。
- 2026-05-24：验证命令 `py_compile learning_agent.py test_learning_agent.py` 已通过；Cron/Monitor 专项 `Ran 5 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 158 tests OK`。
- 2026-05-24：已完成 `learning_agent` 的 `repl` REPL 最小版，可按顺序批量执行安全白名单内的只读、状态和符号工具。
- 2026-05-24：已新增 REPL 红灯测试并确认失败原因是工具未进入 schema、路由未实现、输出 schema 缺 `calls`/`stop_on_error`/`max_output_chars`、运行规则未说明。
- 2026-05-24：已实现 REPL 工具 schema、工具路由、安全白名单、批量大小限制、失败即停策略和单段输出截断。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵和 `learning_agent_CONTEXT.md`；学习备份 `learning_agent\test\38.md` 已写入。
- 2026-05-24：验证命令 `py_compile learning_agent.py test_learning_agent.py` 已通过；REPL 专项 `Ran 6 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 153 tests OK`。
- 2026-05-24：已完成 `learning_agent` 的 `lsp_symbols` / `lsp_definition` / `lsp_diagnostics` LSP 最小版，当前只支持 Python `.py` 文件并使用标准库 `ast`，不启动真实语言服务器。
- 2026-05-24：已新增 LSP 红灯测试并确认失败原因是工具未进入 schema、路由未实现、输出 schema 缺 `symbol`、运行规则未说明。
- 2026-05-24：已实现 LSP 工具 schema、工具路由、工作区内路径校验、Python 符号提取、定义定位和语法诊断输出。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵和 `learning_agent_CONTEXT.md`；学习备份 `learning_agent\test\37.md` 已写入。
- 2026-05-24：验证命令 `py_compile learning_agent.py test_learning_agent.py` 已通过；LSP 专项 `Ran 7 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 147 tests in 7.451s OK`。
- 2026-05-24：已完成 `learning_agent` 的 `enter_worktree` / `exit_worktree` 轻量工作区隔离状态工具最小版。
- 2026-05-24：已新增 WorktreeIsolation 红灯测试并确认失败原因是工具未进入 schema、路由未实现、输出 schema 缺参数、运行规则未说明。
- 2026-05-24：已实现 worktree 工具 schema、`self.worktree_state`、工具路由、进入/退出隔离状态方法和工作区内路径校验。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵和 `learning_agent_CONTEXT.md`；学习备份 `learning_agent\test\36.md` 已写入。
- 2026-05-24：验证命令 `py_compile` 已通过；WorktreeIsolation 专项 `Ran 6 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 140 tests in 5.604s OK`。
- 2026-05-24：已完成 `learning_agent` 的 `verify_plan_execution` Plan mode 执行验证工具最小版，可输出 `status=verified` 或 `status=incomplete`，并汇总执行步骤、证据和遗漏项。
- 2026-05-24：已按 TDD 先补红灯测试，专项测试初次失败原因已确认为工具缺失、路由缺失、输出 schema 缺参数、运行规则缺说明。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵、`learning_agent_CONTEXT.md` 和学习备份 `learning_agent\test\35.md`。
- 2026-05-24：验证命令 `py_compile` 已通过；PlanVerification 专项 `Ran 5 tests OK`；完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 134 tests in 4.739s OK`。
- 2026-05-24：已完成 `learning_agent` 的教学版 `team_start_task`，可为 peer 启动并绑定后台 `task`，`list_peers` 可展示 `bound_task_id` 和 `task_status`。
- 2026-05-24：已新增 peer 绑定后台 task 红灯测试并确认失败原因是工具、路由和运行规则未实现，随后完成最小实现。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵、`learning_agent_CONTEXT.md` 和学习备份 `learning_agent\test\34.md`。
- 2026-05-24：完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 132 tests in 4.834s OK`。
- 2026-05-24：已完成 `learning_agent` 的教学版 `read_peer_messages` / `ack_peer_message` / `team_delete` team 通信生命周期工具。
- 2026-05-24：已新增 team 生命周期红灯测试并确认失败原因是工具未实现，随后完成最小实现并让专项 `Ran 5 tests OK`。
- 2026-05-24：已更新 runtime instructions、README、Claude Code 工具差距矩阵、`learning_agent_CONTEXT.md` 和学习备份 `learning_agent\test\33.md`。
- 2026-05-24：完整验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 131 tests OK`。
- 2026-05-24：已完成 `learning_agent` 的教学版 `team_create` / `send_message` / `list_peers` 多 agent 通信工具。
- 2026-05-24：已新增 team 通信工具测试、运行规则测试、README 说明、Claude Code 工具差距矩阵更新和学习备份 `learning_agent\test\32.md`。
- 2026-05-24：验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 129 tests OK`。
- 2026-05-24：已开始配置用户级 `multi-agent` skill。
- 2026-05-24：已确认项目缺少 `agent_memory/`，按规则补齐基础记忆文件。
- 2026-05-24：下一步将初始化 `<codex-skills-dir>\multi-agent` 并写入 skill 内容。
- 2026-05-24：已完成用户级 `multi-agent` skill 初始化、内容写入、学习备份和结构校验。
- 2026-05-24：校验命令 `quick_validate.py <codex-skills-dir>\multi-agent` 已通过，输出为 `Skill is valid!`。
- 2026-05-24：已完成 `learning_agent` 的 `task_list` / `task_get` / `task_update` 子任务管理工具最小版。
- 2026-05-24：已新增任务管理工具测试、运行规则测试、README 说明、Claude Code 工具差距表更新和学习备份 `learning_agent\test\31.md`。
- 2026-05-24：最新验证命令 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 125 tests in 5.143s OK`。
## 2026-05-24 Prompt / Context Architecture v1 设计阶段

- 2026-05-24：用户确认先不直接写代码、不修改任何提示词，先按推荐创建正式设计文档。
- 2026-05-24：已创建设计文档 `docs/superpowers/specs/2026-05-24-prompt-context-architecture-v1-design.md`，范围限定为成熟 coding agent 的提示词与上下文架构设计。
- 2026-05-24：本阶段未修改系统提示词、规则提示词、`runtime_instructions.md`、模型 adapter instructions 或任何工具实现。
- 2026-05-24：设计文档已完成轻量自查，范围聚焦 Prompt / Context Architecture v1，等待用户确认后再进入实施计划。
- 2026-05-24：用户已确认设计文档，并要求执行前必须先呈现最终建议修改版的所有提示词再次确认。
- 2026-05-24：已创建实施计划 `docs/superpowers/plans/2026-05-24-prompt-context-architecture-v1.md`，计划把提示词预览确认写成 Task 0 硬门槛。
- 2026-05-24：实施计划已完成占位扫描，未发现 TBD、TODO 或待填写占位；当前仍未修改任何提示词文件。
- 2026-05-24：已执行 Task 0，生成提示词预览 `docs/superpowers/specs/2026-05-24-prompt-context-architecture-v1-prompt-preview.md`，等待用户确认后才进入实际修改。
- 2026-05-24：Task 0 预览文件已检查包含 5 个指定区块，未发现 TBD、TODO 或待填写占位；当前仍未修改任何现有提示词文件。
- 2026-05-24：用户回复“确认执行”，已进入 Prompt / Context Architecture v1 实施阶段。
- 2026-05-24：已按 TDD 新增 PromptContextV1 红灯测试，确认旧 system prompt、旧 context policy 和旧 runtime instructions 分层测试按预期失败。
- 2026-05-24：已更新 `learning_agent/learning_agent.py` 的 system prompt 分层结构和 Codex adapter instructions，相关专项测试已通过。
- 2026-05-24：已将 `learning_agent/runtime_instructions.md` 重写为 Operating Principles、Context Policy、Tool Policy、Response Policy 分层结构，并通过 runtime 专项测试。
- 2026-05-24：正在同步 README、Claude Code 工具差距矩阵、agent_memory 和学习备份。
- 2026-05-24：已完成 Prompt / Context Architecture v1 实施，更新 README、Claude Code 工具差距矩阵、agent_memory 和学习备份 `learning_agent/test/43.md`。
- 2026-05-24：最终验证已通过：`py_compile learning_agent.py test_learning_agent.py` 无错误；PromptContextV1 专项 `Ran 4 tests OK`；完整 `python -m unittest learning_agent.test_learning_agent` 结果为 `Ran 177 tests in 6.830s OK`。
## 2026-05-24 MCP HTTP/SSE transport 最小版

状态：已完成，专项测试和完整测试均已通过。

已完成：

- 用 TDD 先新增并确认失败：配置解析、registry transport 分派、HTTP tools/resources/prompts 端到端、SSE 明确边界、README 和 runtime instructions 文档测试。
- 扩展 `McpServerConfig`：新增 `transport`、`url`、`headers`。
- 扩展 `load_mcp_server_configs`：stdio 保持旧写法，HTTP/SSE 按 `transport` + `url` 解析，自定义 `headers` 转字符串。
- 新增 `McpHttpClient`：复用 stdio 结果格式化，使用 Streamable HTTP JSON POST，支持初始化、工具、资源和 prompt。
- 新增 `McpSseClient`：只提供清晰未实现边界，避免把旧 HTTP+SSE 误当作已支持。
- 更新 `McpToolRegistry.from_configs`：按 `stdio/http/sse` 创建对应 client。
- 更新 `format_mcp_startup_status` 和 `run_mcp_doctor`：报告 server transport，并给出 stdio/HTTP/SSE 分支建议。
- 更新 `runtime_instructions.md`、`README.md`、`claude_code_tool_gap_matrix.md`、`learning_agent_CONTEXT.md` 和 `agent_memory/context.md`。

已通过专项命令：

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_parses_http_and_sse_transport_fields learning_agent.test_learning_agent.LearningAgentTests.test_mcp_registry_creates_clients_by_transport learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_client_lists_calls_resources_and_prompts learning_agent.test_learning_agent.LearningAgentTests.test_mcp_sse_transport_fails_with_clear_boundary learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_http_transport_boundaries learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_http_transport
```

结果：

```text
Ran 6 tests in 0.644s
OK
```

最终验证：

```powershell
<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py
```

结果：通过，无错误输出。

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_file_is_parsed_into_server_configs learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_parses_http_and_sse_transport_fields learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_invalid_json_returns_empty_server_list learning_agent.test_learning_agent.LearningAgentTests.test_mcp_config_skips_invalid_server_entries learning_agent.test_learning_agent.LearningAgentTests.test_mcp_registry_can_be_created_from_workspace_config learning_agent.test_learning_agent.LearningAgentTests.test_mcp_registry_creates_clients_by_transport learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_client_lists_calls_resources_and_prompts learning_agent.test_learning_agent.LearningAgentTests.test_mcp_sse_transport_fails_with_clear_boundary learning_agent.test_learning_agent.LearningAgentTests.test_mcp_doctor_lists_visible_tools_from_configured_server
```

结果：

```text
Ran 9 tests in 0.753s
OK
```

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent
```

结果：

```text
Ran 170 tests in 5.781s
OK
```

备份：已创建 `learning_agent/test/41.md`。

下一步建议：

- 做 `MCP OAuth/auth metadata` 最小版，让需要登录的远程 MCP server 有可发现、可解释的鉴权入口。

## 2026-05-24 Browser Automation MCP Task 7

状态：Task 0-6 已按交接说明完成并通过审查；本轮执行 Task 7，范围为 runtime instructions、README、gap matrix、agent memory 和两个文档回归测试。

已完成：

- 新增 `test_runtime_instructions_mentions_browser_automation_usage`，覆盖 `mcp__browser_automation__...`、`mcp__browser_search__web_search`、`mcp__browser_search__fetch_url`、`browser_evaluate`、cookie/localStorage/sessionStorage、`browser_artifacts` 和真实 Chrome 边界。
- 新增 `test_readme_explains_browser_automation_mcp_boundaries`，覆盖 `browser_automation`、`python -m pip install playwright`、`playwright install chromium`、open/snapshot/type/click/wait/screenshot、`browser_evaluate`、`browser_artifacts` 和真实 Chrome 边界。
- 红灯测试已确认失败：新增两个文档测试在更新文档前失败，失败点分别是 runtime instructions 缺少 `mcp__browser_automation__`，README 缺少 `browser_automation`。
- 已更新 `runtime_instructions.md`、`README.md`、`claude_code_tool_gap_matrix.md`、`agent_memory/context.md`、`agent_memory/progress.md` 和 `agent_memory/bugs.md`，记录第一阶段独立 Chromium 边界、工具清单、依赖命令和风险。

最终验证：

- 指定两个文档测试已通过：`Ran 2 tests in 0.018s OK`。
- 因本轮修改了 `learning_agent/test_learning_agent.py`，已运行 `py_compile learning_agent\test_learning_agent.py`，结果为退出码 0、无错误输出。

## 2026-05-24 Browser Automation MCP Task 8

状态：已完成学习备份和最终验证。

已完成：

- 2026-05-24：已创建学习备份 `learning_agent/test/46.md`，记录修改文件、`browser_automation_mcp_server.py` 关键片段、`learning_agent.py` 风险分级片段、测试片段、`.gitignore` 忽略 browser artifacts 的原因和最终验证结果。
- 2026-05-24：依赖状态已确认，当前 bundled Python 可导入并运行 Playwright，真实浏览器聚焦测试能启动独立 Chromium 并完成页面操作、截图、上传和下载记录验证。

最终验证：

```powershell
& '<codex-bundled-python>' -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\browser_automation_mcp_server.py
```

结果：通过，无错误输出。

```powershell
& '<codex-bundled-python>' -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_browser_automation_mcp_server_lists_mature_tools learning_agent.test_learning_agent.LearningAgentTests.test_browser_automation_mcp_server_operates_local_page learning_agent.test_learning_agent.LearningAgentTests.test_browser_automation_mcp_server_uploads_and_downloads learning_agent.test_learning_agent.LearningAgentTests.test_default_mcp_config_enables_browser_automation_server learning_agent.test_learning_agent.LearningAgentTests.test_mcp_permission_risk_classifies_browser_automation_tools learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_browser_automation_usage learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_browser_automation_mcp_boundaries learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_browser_boundaries
```

结果：`Ran 8 tests in 5.966s OK`。

```powershell
& '<codex-bundled-python>' -m unittest learning_agent.test_learning_agent
```

结果：`Ran 196 tests in 15.427s OK`。

```powershell
& '<codex-bundled-python>' learning_agent\learning_agent.py mcp-doctor
```

结果：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功；MCP Doctor 显示模型可见 MCP 工具 27 个，包含 `mcp__browser_automation__browser_open`、`mcp__browser_automation__browser_evaluate`、`mcp__browser_automation__browser_screenshot`、`mcp__browser_automation__browser_downloads` 等工具。计划草案中的 `--mcp-doctor` 不是当前 CLI 参数，当前实际入口是位置命令 `mcp-doctor` 或 `doctor`。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 设计阶段

- 2026-05-24：用户要求按建议执行下一步，当前下一步限定为创建正式设计文档，不直接修改运行时代码。
- 2026-05-24：已读取 `learning_agent_CONTEXT.md`、`agent_memory/context.md`、`learning_agent/learning_agent.py` 中 `McpHttpClient` / `McpSseClient` 相关实现，以及 HTTP MCP 相关测试。
- 2026-05-24：已核对官方 MCP `2025-11-25` transports / lifecycle / authorization 稳定规范，并记录 draft changelog 中未来可能移除 session 和 GET endpoint 的协议风险。
- 2026-05-24：已创建设计文档 `docs/superpowers/specs/2026-05-24-mcp-http-session-stream-lifecycle-v1-design.md`。
- 2026-05-24：设计推荐方案为“有界生命周期增强”：先做 bounded GET 监听、SSE event 解析、`Last-Event-ID` 恢复、DELETE close 和 404 session 过期重建，不做永久后台 listener。
- 2026-05-24：设计文档已扫描 `TBD` / `TODO` / `待定` / `占位` 等占位词，未发现未完成占位；下一步等待用户确认设计后再写实施计划。
- 2026-05-24：用户要求按推荐执行下一步，已视为确认进入实施计划阶段，未修改运行时代码。
- 2026-05-24：已创建实施计划 `docs/superpowers/plans/2026-05-24-mcp-http-session-stream-lifecycle-v1.md`，计划按 TDD 拆成红灯测试、SSE parser、GET listen、DELETE close、404 session rebuild、agent 工具暴露、文档记忆和最终验证。
- 2026-05-24：实施计划已扫描 `TBD` / `TODO` / `待定` / `占位` / `Replace` / `during implementation` 等占位或偷懒表达，未发现残留；下一步等待用户选择执行方式后再开始改代码。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 实施阶段

状态：代码、测试、文档和审查主流程已完成；最终全量验证仍在下一步执行。

已完成：

- 2026-05-24：用户选择方案 1，按 subagent-driven development 执行实施计划。
- 2026-05-24：Task 1 已补红灯测试，覆盖 POST SSE、GET listen、DELETE close、404 session rebuild、runtime/README 文档断言，并通过规格与质量审查。
- 2026-05-24：Task 2 已实现 SSE event/state 解析与 `stream_state`，并修复 `recent_events` 深拷贝问题。
- 2026-05-24：Task 3 已实现有界 GET `listen_stream`、`Last-Event-ID`、非 SSE/405 边界和 SSE 注释心跳过滤。
- 2026-05-24：Task 4 已实现 DELETE session close 与一次性 404 session rebuild，并通过 Task 4 聚焦测试和双审查。
- 2026-05-24：Task 5 已暴露模型可见 `listen_mcp_stream` 工具，补齐 wrapper、dispatch、权限确认和非有限数值兜底测试。
- 2026-05-24：Task 6 已更新 `runtime_instructions.md`、`README.md`、`claude_code_tool_gap_matrix.md`，并通过文档专项测试、规格审查和质量复审。

已通过的关键专项验证：

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_falls_back_for_non_finite_limits learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_tool_schema_is_available learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_wrapper_validates_server learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_execute_tool_dispatch_validates_server
```

结果：

```text
Ran 4 tests in 0.014s
OK
```

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_http_session_stream_lifecycle learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_http_session_stream_lifecycle learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_http_transport learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_http_transport_boundaries
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

已完成：

- 2026-05-24：已创建学习备份 `learning_agent/test/44.md`。

最终验证：

```powershell
<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py
```

结果：通过，无错误输出。

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_client_parses_post_sse_events_and_records_stream_state learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_listen_stream_sends_last_event_id_and_handles_405 learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_listen_stream_ignores_sse_comment_heartbeats learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_close_sends_delete_when_session_exists_and_ignores_405 learning_agent.test_learning_agent.LearningAgentTests.test_mcp_http_request_reinitializes_once_when_session_returns_404 learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_falls_back_for_non_finite_limits learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_tool_schema_is_available learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_wrapper_validates_server learning_agent.test_learning_agent.LearningAgentTests.test_listen_mcp_stream_execute_tool_dispatch_validates_server learning_agent.test_learning_agent.LearningAgentTests.test_runtime_instructions_mentions_mcp_http_session_stream_lifecycle learning_agent.test_learning_agent.LearningAgentTests.test_readme_explains_mcp_http_session_stream_lifecycle
```

结果：

```text
Ran 11 tests in 3.727s
OK
```

```powershell
<codex-bundled-python> -m unittest learning_agent.test_learning_agent
```

结果：

```text
Ran 188 tests in 9.512s
OK
```

## 2026-05-25 Real Chrome profile automation implementation

状态：已完成真实 Chrome profile 自动化第一版实现计划中的代码、测试、文档和学习备份。
验证：
- `py_compile` 通过。
- Real Chrome 聚焦测试通过，手动集成测试默认跳过。
- 全量 `learning_agent.test_learning_agent` 通过，结果为 `Ran 227 tests in 24.040s OK (skipped=1)`。
- `learning_agent.py mcp-doctor` 输出真实 Chrome profile 诊断和新的 browser_automation MCP 工具。
当前边界：默认仍使用独立 Chromium；真实 Chrome profile 只在用户显式确认后作为高风险模式启用。
记录脱敏：验证记录中的本机用户目录已用 `<codex-bundled-python>`、`<codex-skills-dir>` 和 `<user-home>` 这类占位符脱敏，避免把个人路径写进长期上下文。

## 2026-05-25 Codex OAuth relogin and timeout handling

状态：已完成 OAuth/API 直连登录过期恢复与 timeout 解释修复。

已完成：

- 已确认旧逻辑只在无 token 或缺少 refresh token 时打开浏览器，refresh token 被拒绝和 Codex API `401/403` 都没有重新登录兜底。
- 已新增红灯测试覆盖 refresh token `invalid_grant` 后重新登录、API `401` 后重新登录并重试一次、`The read operation timed out` 不触发网页登录且显示中文超时提示。
- 已实现 `_refresh_tokens_or_login()`、refresh/API 鉴权错误识别、timeout 中文格式化提示。
- 已更新 `learning_agent/README.md`，说明 refresh token 失效、`401/403` 和响应读取超时的边界。
- 已创建学习备份 `learning_agent/test/49.md`。

验证：

- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- OAuth/README 聚焦 6 条测试通过，结果为 `Ran 6 tests in 0.003s OK`。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 231 tests in 23.916s OK (skipped=1)`。

## 2026-05-25 Codex response_format strict schema fix

状态：已完成 Codex OAuth/API 直连模式 `HTTP 400 invalid_json_schema` 修复。

已完成：

- 已确认截图中的 `Invalid schema for response_format ... todos.items ... Missing 'id'` 不是 OAuth 登录过期，而是 `CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)` 生成的 `text.format.schema` 不符合 Codex Responses strict JSON Schema。
- 已新增红灯测试 `test_codex_output_schema_requires_all_nested_todo_item_properties_for_responses_api`，复现 `todos.items.required` 缺少 `id` 和 `priority`。
- 已实现 `_strict_response_format_schema()`，在 `_nullable_argument_schema()` 中递归补齐嵌套对象的 `required` 并设置 `additionalProperties=false`。
- 已创建学习备份 `learning_agent/test/50.md`。

验证：

- 本地 schema 扫描结果为 `problems 0`。
- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- strict schema/OAuth 聚焦 6 条测试通过，结果为 `Ran 6 tests in 0.005s OK`。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 232 tests in 24.951s OK (skipped=1)`。

## 2026-05-25 Codex strict schema open object fix

状态：已完成第二个 Codex strict schema `HTTP 400 invalid_json_schema` 修复。

已完成：

- 已确认新截图中的 `prompt_arguments ... additionalProperties is required to be supplied and to be false` 是开放对象 schema 问题，不是 OAuth 登录过期。
- 已新增红灯测试 `test_codex_output_schema_sets_additional_properties_false_for_all_object_nodes`，覆盖所有 object schema 都必须关闭 `additionalProperties`。
- 已确认本地扫描原先发现两个问题路径：`prompt_arguments` 和 `calls.items.arguments`。
- 已更新 `_strict_response_format_schema()`，让没有固定 `properties` 的 object 降级为 `properties={}`、`required=[]`、`additionalProperties=false`。
- 已创建学习备份 `learning_agent/test/51.md`。

验证：

- 本地 schema 扫描结果为 `problems 0`。
- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- strict schema/OAuth 聚焦 8 条测试通过，结果为 `Ran 8 tests in 0.006s OK`。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 233 tests in 25.767s OK (skipped=1)`。

## 2026-05-25 Codex OAuth SSE stream read fix

状态：已完成用户“真实浏览器查天气”请求卡在模型首轮响应前的问题排查与修复。

已完成：

- 已读取最新 debug 日志，确认本轮只记录到 `model_request`，没有 `model_response` 或任何浏览器工具调用，因此不是 browser_automation MCP 卡住。
- 已确认根因是 `_post_json_request()` 对 `stream=true` 的 Codex SSE 响应使用 `response.read()` 等待整条响应结束，遇到长连接流式响应时可能一直等不到 EOF。
- 已新增红灯测试 `test_codex_oauth_stream_request_reads_until_done_without_full_response_read`，先确认旧实现会调用整包 `read()`。
- 已实现 `_read_sse_response_until_done()`，让 OAuth/API 流式响应按行读取并在 done/completed/[DONE] 时返回。
- 已创建学习备份 `learning_agent/test/52.md`。

验证：

- 新增回归测试先红后绿：旧实现失败于 `fake_response.read_called is True`，修复后通过。
- OAuth/strict schema 聚焦 9 条测试通过，结果为 `Ran 9 tests in 0.011s OK`。
- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整 `learning_agent.test_learning_agent` 第一次出现一次 browser_automation stdio 超时；单独重跑失败用例通过。
- 最新完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 234 tests in 22.403s OK (skipped=1)`。

## 2026-05-25 Browser automation 参数清洗与 timeout hardening

状态：已完成用户“真实浏览器自动化工具好像卡住”的第二轮排查与修复。

已完成：

- 已读取最新 debug 日志，确认 `mcp__browser_automation__browser_open` 已经成功返回两次，卡点在工具结果后的 Codex OAuth/API 第 2 轮模型调用超时。
- 已新增红灯测试覆盖：MCP registry 按 schema 清洗多余参数、授权提示清洗多余参数、browser_automation 外层 stdio timeout 至少 35 秒、Codex OAuth/API read timeout 自动重试一次。
- 已实现 `McpToolRegistry` 参数 schema 缓存与 `sanitize_tool_arguments()`，并在 `call_tool()` 前兜底清洗。
- 已实现 `LearningAgent._execute_mcp_tool()` 授权前参数清洗，保证用户确认的参数和真实调用参数一致。
- 已实现 `McpToolRegistry.from_configs()` 对 `browser_automation` stdio client 使用 35 秒请求超时，避免 5 秒外层超时早于页面加载超时。
- 已实现 Codex OAuth/API read timeout 同 token 自动重试一次，不误触发网页登录。
- 已创建学习备份 `learning_agent/test/53.md`。

验证：

- 红灯确认：4 条新增测试在修复前分别失败于参数未清洗、timeout 仍为 5 秒、授权提示仍含 `"status"`、OAuth timeout 未重试。
- 修复后聚焦测试通过：`Ran 4 tests in 0.008s OK`。
- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 238 tests in 24.580s OK (skipped=1)`。

## 2026-05-25 Codex OAuth remote disconnected fix

状态：已完成用户新截图 `Remote end closed connection without response` 的排查与修复。

已完成：

- 已读取最新 debug 日志，确认本轮停在第 0 轮模型调用，没有任何浏览器 MCP 工具调用，因此不是 browser_automation 工具错误。
- 已新增红灯测试覆盖 `http.client.RemoteDisconnected("Remote end closed connection without response")` 第一次失败、第二次成功时应自动重试一次。
- 已新增红灯测试覆盖连续远端断连时应显示中文“远端连接关闭”，且不触发网页登录。
- 已新增文档红灯测试，要求 README 说明“远端连接关闭”边界。
- 已新增直接构造 `McpStdioClient` 的 browser_automation 长超时测试，修复完整测试里偶发 5 秒 stdio 超时风险。
- 已实现 `_is_transient_api_error()`、`_is_remote_closed_error()`，并把远端断连纳入同 token 自动重试一次。
- 已更新 `learning_agent/README.md` 的 OAuth/API 直连说明。
- 已创建学习备份 `learning_agent/test/54.md`。

验证：

- 红灯确认：新增 2 条 OAuth 断连测试修复前失败，分别失败于未重试和未输出中文“远端连接关闭”。
- 修复后 OAuth/README 聚焦 3 条测试通过，结果为 `Ran 3 tests in 0.002s OK`。
- browser_automation 直接构造长超时与本地页面聚焦 2 条测试通过，结果为 `Ran 2 tests in 3.857s OK`。
- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 241 tests in 20.177s OK (skipped=1)`。
- `git diff --check` 仅显示 LF/CRLF 提示，没有空白错误。

## 2026-05-25 Tool Architecture v2 设计阶段

状态：已进入顶层工具架构重构设计阶段，当前只写设计，不修改运行时代码。

已完成：

- 已确认用户补充目标：工具调用顶层设计至少要对齐 ClaudeCode，后续再考虑升级到比 ClaudeCode 更先进的 agent。
- 已核对 ClaudeCode 工具架构证据，包括 Tool 对象模型、tool pool、ToolSearch deferred loading、`shouldDefer`、`alwaysLoad`、Chrome skill gate 和 tabs context workflow。
- 已核对当前 `learning_agent` 的差距，包括 `TOOL_SCHEMAS + MCP tools/list` 直接合并、`tool_search` 只搜索可见工具、输出协议聚合所有工具参数、执行层参数清洗只是兜底。
- 已创建设计文档 `docs/superpowers/specs/2026-05-25-tool-architecture-v2-claudecode-codex-alignment-design.md`。
- 已在设计中明确 v2 分层：`AgentTool`、`ToolCatalog`、`ToolPolicy`、`ToolPool`、`ToolSearch v2`、输出协议、执行层和观察层。

下一步：

- 等待用户审阅并确认设计文档。
- 用户确认后，再进入实施计划阶段，拆分为 TDD 可验证任务。

## 2026-05-25 Tool Architecture v2 实施计划阶段

状态：用户已经确认 Tool Architecture v2 设计文档，当前已创建第一份核心主干实施计划，尚未修改运行时代码。

已完成：

- 已按 confirmed design 进入 writing-plans 阶段。
- 已完成 Scope Check：完整 v2 设计覆盖多个子系统，因此第一份计划限定为 `Tool Architecture v2 Core Spine`。
- 已创建实施计划 `docs/superpowers/plans/2026-05-25-tool-architecture-v2-core-spine.md`。
- 计划范围包括 `AgentTool`、内置工具 catalog、MCP deferred catalog、当前 Tool Pool、ToolSearch `search/select`、未加载 deferred 工具执行门禁、输出 schema 跟随当前 pool 的回归测试、文档和最终验证。
- 已创建本阶段学习备份 `learning_agent/test/57.md`。

下一步：

- 等待用户选择执行方式：Subagent-Driven 或 Inline Execution。

## 2026-05-25 Tool Architecture v2 core spine 实施完成

状态：用户选择 Subagent-Driven 执行方式后，第一阶段核心主干已完成代码、测试、文档、记忆和学习备份收尾。

已完成：

- 已新增 `AgentTool` 统一工具对象，并把内置工具包装成 builtin catalog。
- 已让 MCP registry 暴露 `agent_tools()`，把已发现 MCP 工具包装成默认 deferred 的 catalog 条目。
- 已让 `LearningAgent` 区分完整 `Tool Catalog` 与当前 `Tool Pool`，并用 `loaded_tool_names` 记录 select 后加载的 deferred 工具。
- 已升级 `tool_search`：现在搜索完整 catalog，输出 source、state、参数和 `加载提示：select:<tool_name>`，并支持 `query="select:<tool_name>"` 把工具加载进后续 Tool Pool。
- 已新增执行门禁：未通过 select 加载的 deferred 工具直接调用时会被拒绝，并提示先用 `tool_search` select。
- 已让输出 schema 只基于当前 Tool Pool 生成，避免未加载 MCP/真实 Chrome 参数继续混入默认结构化输出。
- 已调整旧 MCP 测试契约：不再期待 MCP 工具启动后直接暴露给模型，而是先 select 再执行或断言默认隐藏。
- 已让 task 子 agent 只继承父 agent 已 select 且 allowed_tools 允许的 deferred 工具。
- 已同步 `runtime_instructions.md`、`README.md` 和 `claude_code_tool_gap_matrix.md`。
- 已创建学习备份 `learning_agent/test/58.md`。

验证：

- `<codex-bundled-python> -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- ToolArchitectureV2 聚焦 7 条测试通过。
- 旧 MCP 契约迁移后的 9 条回归测试通过。
- 完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 252 tests in 20.823s OK (skipped=1)`。

下一步：

- 进入 Tool Architecture v2 第二阶段：真实 Chrome workflow/skill gate、风险策略、MCP annotations 映射、`tools/list_changed`/notifications 刷新和更严格的 per-tool 输出协议。

## 2026-05-25 ClaudeCode agent core parity master design

状态：已按用户要求开始“至少完全追平 ClaudeCode”的顶层路线图阶段，并完成 master design。

已完成：

- 已说明“有 ClaudeCode 源码可参考”不等于单次补丁即可完全追平，必须拆成可验收阶段。
- 已采用 agent core parity 定义：追平工具架构、权限、MCP、skills/workflow、真实 Chrome workflow、输出协议、子 agent、worktree、context 和 observation；不把 ClaudeCode 私有产品能力列为 P0。
- 已核对 ClaudeCode `Tool.ts` 中的 `searchHint`、`shouldDefer`、`alwaysLoad`、MCP info、权限和 validation/progress 结构。
- 已核对 ClaudeCode `tools.ts` 中的基础工具、模式过滤、deny rules、MCP 合并和 tool pool 组装。
- 已核对 ClaudeCode MCP client 中的 annotations、`anthropic/searchHint`、`anthropic/alwaysLoad` 和 MCP permissions。
- 已核对 ClaudeCode MCP connection manager 中的 `tools/list_changed`、`prompts/list_changed`、`resources/list_changed` 刷新逻辑。
- 已创建 master design：`docs/superpowers/specs/2026-05-25-claudecode-agent-core-parity-master-design.md`。
- 已创建学习备份 `learning_agent/test/59.md`。

下一步：

- 等待用户确认 master design。
- 用户确认后，创建 Phase 1 `Tool Policy / Permission v2` 实施计划。

## 2026-05-25 Tool Policy / Permission v2 实施计划

状态：用户已确认 ClaudeCode agent core parity master design，当前已创建 Phase 1 详细实施计划，尚未修改运行时代码。

已完成：

- 已使用 writing-plans skill 创建计划：`docs/superpowers/plans/2026-05-25-claudecode-parity-phase1-tool-policy-permission-v2.md`。
- 计划范围限定为 Phase 1：ToolPolicy、allow/deny rules、MCP annotations、`anthropic/searchHint`、`anthropic/alwaysLoad`、skill/workflow gate、ToolSearch select policy、执行 policy guard、权限拒绝记忆和子 agent policy 继承。
- 已明确不包含 per-tool output protocol、MCP list_changed、真实 Chrome workflow、真实 git worktree、真实 LSP 或持久 Cron；这些留给后续阶段。
- 已创建学习备份 `learning_agent/test/60.md`。

下一步：

- 等待用户选择执行方式：Subagent-Driven 或 Inline Execution。
## 2026-05-25 ToolPolicyV2 Task 1 实现进度

状态：已完成，当前只处理 Phase 1 Task 1 `Add ToolPolicy Core Module`。

范围边界：
- 新增独立模块 `learning_agent/tool_policy.py`。
- 在 `learning_agent/test_learning_agent.py` 的 ToolArchitectureV2 测试附近新增两条测试。
- 不接入执行层、select 流程、权限弹窗、MCP annotations 或后续 Task 2-6。

成功标准：
- `ToolPolicy.decide()` 对 deny、skill gate、workflow gate、deferred、loaded 五类状态返回符合规格的 `ToolPolicyDecision`。
- deny 规则支持 `tool_name`、`server_name`、`source` 精确匹配，空规则不会匹配所有工具。
- 新模块不 import `learning_agent.learning_agent`，避免循环依赖。
- 用户指定的两条 unittest 用例通过。

验证方式：
- 先新增测试并运行指定命令确认因缺少 `learning_agent.tool_policy` 或行为缺失而失败。
- 实现最小策略模块后再次运行用户指定命令。

完成记录：
- 已新增 `learning_agent/tool_policy.py`，定义 `ToolPolicyRule`、`ToolPolicyContext`、`ToolPolicyDecision` 和 `ToolPolicy.decide()`。
- 已在 ToolArchitectureV2 测试附近新增 `test_tool_policy_blocks_denied_tool_before_pool_exposure` 与 `test_tool_policy_requires_skill_and_workflow_gates`。
- 已创建学习备份 `learning_agent/test/61.md`。
- 红灯验证：指定 unittest 首次失败于 `ModuleNotFoundError: No module named 'learning_agent.tool_policy'`。
- 绿灯验证：同一指定 unittest 后续通过，结果为 `Ran 2 tests in 0.004s OK`。

## 2026-05-25 ToolPolicyV2 Task 1 With fixes 覆盖补强

状态：已完成质量审查返回的测试覆盖修复，只修改 Task 1 测试和学习备份，不修改运行时集成。

补强内容：
- 新增 deferred/loaded/always_load 决策测试，覆盖 `loaded=False` 的 deferred、`loaded=True` 的 loaded，以及 `always_load=True` 绕过 deferred。
- 新增 `ToolPolicyRule(server_name=...)` 与 `ToolPolicyRule(source=...)` 的 deny 命中测试。
- 新增空 `ToolPolicyRule()` 不会匹配所有工具的测试。
- 补强 skill/workflow gate 成功路径，断言 `state/visible/selectable/executable` 都为 loaded 可用状态。
- 已同步学习备份 `learning_agent/test/61.md`。

验证：
- Task 1 聚焦测试 4 条通过，结果为 `Ran 4 tests in 0.007s OK`。

## 2026-05-25 ToolPolicyV2 Task 2 实现进度

状态：已完成 Phase 1 Task 2 `Extend AgentTool Metadata and MCP Annotation Mapping`，未接入 pool/search/execute。

范围边界：
- 扩展 `AgentTool` 元数据字段：aliases、search_hint、input_json_schema、output_schema、is_open_world、strict、max_result_size_chars。
- 扩展 `agent_tool_from_schema(...)` 关键字参数并保持旧调用默认兼容。
- 在 `McpToolRegistry` 中缓存 MCP 原始 annotations、_meta、inputSchema、outputSchema，并在 `agent_tools()` 包装为 AgentTool 时映射。
- 仅新增 Task 2 指定测试，不做 ToolPolicy 到工具池、搜索选择或执行层集成。

成功标准：
- `annotations.readOnlyHint` 映射到 `AgentTool.is_read_only`。
- `annotations.destructiveHint` 映射到 `AgentTool.is_destructive`。
- `annotations.openWorldHint` 映射到 `AgentTool.is_open_world`。
- `_meta["anthropic/searchHint"]` 映射到 `AgentTool.search_hint`。
- `_meta["anthropic/alwaysLoad"]` 映射到 `AgentTool.always_load`。
- `input_json_schema` 与 `output_schema` 保存 MCP 原始 schema 深拷贝。
- `server_name` 继续保留 MCP server 名。

验证记录：
- 红灯：新增测试首次失败于 `AssertionError: False is not true`，确认 `readOnlyHint` 尚未映射。
- 绿灯：用户指定命令通过，结果为 `Ran 1 test in 0.000s OK`。
- 已创建学习备份 `learning_agent/test/62.md`。

## 2026-05-25 ToolPolicyV2 Task 2 注释前缀审查修复

状态：已处理规格审查指出的 Task 2 注释前缀问题。

处理内容：
- 仅将 Task 2 本次扩展过的两个多行调用收口注释改为 `修改代码+ToolPolicyV2`。
- 未批量修改上一阶段既有的 `ToolArchitectureV2` 注释，例如 `AgentTool` 旧字段、`to_model_schema()`、`build_builtin_tool_catalog()`、ToolSearch v2 主干和未改动的 `original_name/server_name` 传参。
- 已同步学习备份 `learning_agent/test/62.md`。

## 2026-05-25 ToolPolicyV2 Task 2 With fixes 严格布尔解析

状态：已完成代码质量审查返回的 With fixes，只修复 Task 2 MCP metadata 布尔解析与测试覆盖。

处理内容：
- 新增 `McpToolRegistry._metadata_bool(value)`，只有 `value is True` 返回 True，其余字符串、数字、None 和普通真值都返回 False。
- 将 `anthropic/alwaysLoad`、`readOnlyHint`、`destructiveHint`、`openWorldHint`、`strict/anthropic/strict/顶层 strict` 切换为严格布尔解析。
- 新增字符串 `"false"`、`"0"`、`"no"` 元数据测试，覆盖 `bool("false")` 误判风险。
- 新增 annotations/_meta 非 dict 容错测试。
- 新增 input_json_schema/output_schema 深拷贝隔离测试。
- 已同步学习备份 `learning_agent/test/62.md`。

验证记录：
- 红灯：新增聚焦测试首次失败于 `AssertionError: True is not false`，确认字符串 `"false"` 被旧 `bool()` 误判。
- 绿灯：Task 2 聚焦 4 条测试通过，结果为 `Ran 4 tests in 0.001s OK`。

## 2026-05-25 ToolPolicyV2 Task 3 实现进度

状态：已完成 Phase 1 Task 3 `Integrate ToolPolicy into Tool Pool and ToolSearch`，只接入工具池、tool_search 展示和 tool_search select，未做执行层 policy guard 或 permission denial tracking。

成功标准：
- `LearningAgent` 持有 `ToolPolicy` 与 `ToolPolicyContext`。
- `_current_tool_pool()` 通过统一 ToolPolicy decision 控制可见性。
- `_tool_search()` 搜索完整 catalog，并展示 `ToolPolicyDecision.state` 和清楚的阻断原因。
- `_tool_search_select()` 在加入 `loaded_tool_names` 前检查 `decision.selectable`，不可选择时返回含 state/reason 的失败信息。
- 用户指定的两条 unittest 通过。

验证方式：
- 先新增两条 Task 3 测试并运行用户指定命令确认红灯。
- 再实现最小运行时代码并重跑同一命令确认绿灯。

完成记录：
- 已在 `LearningAgent.__init__` 增加 `tool_policy`、`tool_policy_context` 和 catalog 对象缓存。
- 已新增 `_tool_policy_decision()`，统一把 `loaded_tool_names`/`always_load` 转成 ToolPolicy loaded 输入。
- 已把 `_current_tool_pool()` 改为按 `decision.visible` 决定是否进入当前工具池。
- 已把 `_tool_search()` 改为使用 `ToolPolicyDecision.state`，并在 `decision.reason` 非空时输出“阻断原因”。
- 已把 `_tool_search_select()` 改为 select 前检查 `decision.selectable`，不可选时返回 state/reason，且不会写入 `loaded_tool_names`。
- 已新增测试 `test_tool_search_reports_blocked_tools_from_policy` 和 `test_tool_search_select_refuses_tools_missing_skill_gate`。
- 已创建学习备份 `learning_agent/test/63.md`。
- 红灯验证：新增两条测试首次失败于 `LearningAgent` 缺少 `tool_policy_context`，以及缺 skill gate 工具仍被 select 加载。
- 绿灯验证：用户指定两条测试通过，结果为 `Ran 2 tests in 0.015s OK`。
- 额外验证：`py_compile learning_agent.py test_learning_agent.py` 通过；相邻 ToolSearch 回归 2 条通过，结果为 `Ran 2 tests in 0.018s OK`；`git diff --check` 无空白错误，仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-25 ToolPolicyV2 Task 3 With fixes 实现进度

状态：已完成质量审查返回的同轮 select 生效问题；范围仍限制在 Task 3 工具池、tool_search/select 与 run 工具池刷新，未做 Task 4 permission denial tracking。

成功标准：
- 普通直接调用 `_execute_tool(tool_search select:...)` 仍可立即加入 `loaded_tool_names`，保留现有测试便利。
- `run()` 处理同一批 `tool_calls` 时，select 只进入 pending 集合，批次结束后才合并到 `loaded_tool_names`。
- 同一批 `tool_calls` 里 select 后立刻调用目标 deferred MCP 工具仍应被“尚未通过 tool_search select 加载”拒绝，fake MCP client 不应被调用。
- 下一轮模型请求前重新计算 `tools = self._available_tool_schemas()`，让上一批合并后的工具进入下一轮 schema。

验证方式：
- 先新增 `test_tool_search_select_does_not_allow_same_turn_deferred_tool_execution` 并运行确认红灯。
- 实现 pending select 和 run 每轮刷新后，运行新测试、Task3 两条测试和相邻 ToolArchitectureV2 回归。

完成记录：
- 已新增 `pending_loaded_tool_names` 和 `defer_tool_select_until_next_turn`，用于区分普通直接 select 与 run 批次内 select。
- 已让 `run()` 在每轮模型请求前重新计算 `tools = self._available_tool_schemas()`。
- 已让 `run()` 当前批次 tool_calls 处理时先把 select 放入 pending，批次结束后合并到 `loaded_tool_names`。
- 已保持普通 `_execute_tool(tool_search select:...)` 直接调用时立即加入 `loaded_tool_names`。
- 已新增 `SequentialRecordingToolNameFakeModel` 和 `test_tool_search_select_does_not_allow_same_turn_deferred_tool_execution`。
- 已创建学习备份 `learning_agent/test/64.md`。
- 红灯验证：新测试首次失败于 fake MCP client 被同批第二个工具调用执行，`fake_client.calls == [('echo', {'text': '同轮不应执行'})]`。
- 绿灯验证：新测试通过，结果为 `Ran 1 test in 0.039s OK`。
- Task3 两条测试通过，结果为 `Ran 2 tests in 0.018s OK`。
- 相邻回归两条通过，结果为 `Ran 2 tests in 0.017s OK`。
- 额外验证：`py_compile learning_agent.py test_learning_agent.py` 通过；`git diff --check` 无空白错误，仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-25 ToolPolicyV2 Task 4 实现进度

状态：已完成 Phase 1 Task 4 `Add Execution Guard and Permission Denial Tracking`，只实现执行层二次校验和 MCP 权限拒绝记忆，未实现 Task 5 子 agent 继承，未修改真实 Chrome gating，未更新 docs。

成功标准：
- `_execute_tool()` 在具体工具分发前对 catalog 中存在的工具执行 ToolPolicy 二次校验。
- `blocked` / `needs_skill` / `needs_workflow` 等非 deferred 且不可执行工具直接返回 `policy 阻断`，不会进入 MCP 工具权限弹窗。
- deferred 工具仍交给既有未加载 deferred guard，保持 Task 3 同轮 select pending 语义不变。
- `_execute_mcp_tool()` 先按 schema 清洗参数，再基于清洗后的 `ToolCall` 生成稳定拒绝 key。
- 同一 MCP 工具和清洗后参数被用户拒绝后，后续相同请求直接返回“之前已被用户拒绝”，不再重复 `ask_permission`。

完成记录：
- 已新增 `LearningAgent.permission_denials: set[str]`。
- 已新增 `_tool_denial_key()`，使用工具名和按 key 排序的清洗后参数 JSON 生成稳定指纹。
- 已在 `_execute_tool()` 顶部加入 ToolPolicy 执行层二次校验，并保留 `state == "deferred"` 继续走旧 deferred guard。
- 已在 `_execute_mcp_tool()` 中使用清洗后的 `safe_tool_call` 计算拒绝 key，并在权限拒绝时写入 `permission_denials`。
- 已新增测试 `test_policy_blocked_tool_call_is_rejected_before_permission_prompt`。
- 已新增测试 `test_repeated_permission_denial_is_remembered_for_same_tool_and_arguments`。
- 已创建学习备份 `learning_agent/test/65.md`。

验证记录：
- 红灯验证：新增两条测试首次失败；blocked 工具先命中旧 deferred guard，重复拒绝第二次仍进入 `ask_permission`。
- 绿灯验证：Task 4 指定两条测试通过，最终复核结果为 `Ran 2 tests in 0.018s OK`。
- 相邻回归：`test_tool_search_select_does_not_allow_same_turn_deferred_tool_execution` 和 `test_deferred_mcp_tool_call_is_rejected_until_selected` 通过，最终复核结果为 `Ran 2 tests in 0.055s OK`。
- 额外验证：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过，exit code 0。

## 2026-05-26 ToolPolicyV2 Task 4 With fixes 测试覆盖

状态：已完成质量审查返回的测试覆盖缺口，只新增不同参数重新请求权限的回归测试，未修改生产逻辑，未实现 Task 5。

成功标准：
- 同一 MCP 工具 `mcp__demo__echo` 第一次用 `{"text": "deny"}` 被拒绝后，会写入拒绝记忆。
- 第二次同一工具改用不同清洗后参数 `{"text": "different"}` 时，必须重新进入 `ask_permission`。
- 第二次权限允许后必须真实调用 fake MCP client，并返回 `called echo: different`。
- 如果 `_tool_denial_key()` 将来退化成只按工具名记录拒绝，新测试会失败。

完成记录：
- 新增测试 `test_permission_denial_allows_different_arguments_to_request_again`。
- 测试中的权限回调允许启动 MCP server，拒绝 `text=deny`，允许 `text=different`。
- 断言具体 MCP 工具权限请求出现 2 次，证明不同参数不会被旧拒绝记忆吞掉。
- 断言 `fake_client.calls == [("echo", {"text": "different"})]`，证明第二次不同参数真实执行。
- 已创建学习备份 `learning_agent/test/66.md`。

验证记录：
- 红灯：新增测试名前置运行失败于 `AttributeError: type object 'LearningAgentTests' has no attribute 'test_permission_denial_allows_different_arguments_to_request_again'`，确认覆盖缺失。
- Task 4 With fixes 三条测试通过，结果为 `Ran 3 tests in 0.023s OK`。
- 相邻回归两条通过，结果为 `Ran 2 tests in 0.040s OK`。

## 2026-05-26 ToolPolicyV2 Task 5 子 agent 策略继承

状态：已完成计划文件 `Task 5: Child Agent Policy Inheritance`，未执行 Task 6 文档/full verification，未修改真实 Chrome gating，未 stage/commit/revert。

成功标准：
- 父 agent 先通过 `tool_search select` 加载 `mcp__demo__echo`。
- 父 agent 后续添加 `ToolPolicyRule(tool_name="mcp__demo__echo")` deny。
- `_task()` 创建子 agent 后，子 agent 继承父 agent 的 `allow_rules`、`deny_rules`、`loaded_skills`、`completed_workflows`。
- 既有 `loaded_tool_names` 继承逻辑保留，子 agent 最终模型工具池仍经过自己的 ToolPolicy 决策过滤。

完成记录：
- 新增测试 `test_child_agent_inherits_policy_denials_for_allowed_mcp_tools`。
- 测试捕获 `_task()` 内创建的真实子 agent，断言 `deny_rules` 中含有 `mcp__demo__echo`。
- 测试读取子 agent 自己的 `_available_tool_schemas()`，断言 `mcp__demo__echo` 不进入模型工具池。
- 在 `_task()` 构造 `child_agent` 后复制父 agent ToolPolicy context 四个字段。
- 已创建学习备份 `learning_agent/test/67.md`。

验证记录：
- 初始红灯：指定测试名运行失败于 `AttributeError: type object 'LearningAgentTests' has no attribute 'test_child_agent_inherits_policy_denials_for_allowed_mcp_tools'`。
- 补测试后的红灯：失败于 `AssertionError: 'mcp__demo__echo' not found in []`，确认子 agent 未继承父 `deny_rules`。
- 目标测试绿灯：`Ran 1 test in 0.018s OK`。
- 相邻回归：`test_task_child_agent_can_inherit_allowed_mcp_tool`、`test_task_runs_child_agent_with_allowed_tools`、`test_policy_blocked_tool_call_is_rejected_before_permission_prompt` 通过，结果为 `Ran 3 tests in 0.060s OK`。

## 2026-05-26 ToolPolicyV2 Task 5 With fixes 显式 allowed_tools 边界修复

状态：已完成质量审查返修；未执行 Task 6，未 stage/commit/revert，未修改真实 Chrome gating。

成功标准：
- 显式传入 `allowed_tools=["mcp__demo__echo"]` 时，即使父 agent 当前 deny 让该工具从 visible schema 消失，也不能提前把该工具清空。
- 子 agent 必须继承父 agent 的 `deny_rules`，并且 `loaded_tool_names` 仍包含已加载的 `mcp__demo__echo`。
- 子 agent 最终 `_available_tool_schemas()` 不包含 `mcp__demo__echo`，证明是 child 自己的 ToolPolicy deny 在过滤。
- 省略 `allowed_tools` 的默认场景仍使用父当前 visible 工具池作为继承边界。
- `task/task_output/task_stop/task_list/task_get/task_update` 仍禁止下放给子 agent。

完成记录：
- 更新 `test_child_agent_inherits_policy_denials_for_allowed_mcp_tools`，新增对子 agent `loaded_tool_names` 包含 `mcp__demo__echo` 的断言。
- 修改 `_task_allowed_tool_names()`：默认路径继续使用 `self._tool_schema_names()`；显式路径改用完整 `_tool_catalog()` 工具名与 `self.loaded_tool_names` 的并集做合法性判断。
- 保留禁止递归 task 和任务管理工具的规则，并集中到 `blocked_task_tool_names`。
- 已创建学习备份 `learning_agent/test/68.md`。

验证记录：
- 红灯：补充 loaded 继承断言后，目标测试失败于 `AssertionError: 'mcp__demo__echo' not found in set()`。
- 单测绿灯：目标测试通过，结果为 `Ran 1 test in 0.017s OK`。
- 指定四条验证通过：`test_child_agent_inherits_policy_denials_for_allowed_mcp_tools`、`test_task_child_agent_can_inherit_allowed_mcp_tool`、`test_task_runs_child_agent_with_allowed_tools`、`test_policy_blocked_tool_call_is_rejected_before_permission_prompt`，结果为 `Ran 4 tests in 0.075s OK`。

## 2026-05-26 ToolPolicyV2 Task 6 文档、记忆、备份和验证收口

状态：已完成计划文件 `Task 6: Documentation, Memory, Backup, and Full Verification`；未修改真实 Chrome gating，未 stage/commit/revert。

成功标准：
- `runtime_instructions.md` 说明 Tool Policy v2、`tool_search select` 可能因 `blocked` / `needs_skill` / `needs_workflow` 失败、`deny rule` 暴露前和执行前硬拦截、`skill gate` / `workflow gate` 满足后才能 select、重复拒绝不要盲目重试。
- `README.md` 说明 Tool Policy v2 是 Tool Architecture v2 core spine 后的第二层，并解释 MCP annotations、`_meta`、`anthropic/alwaysLoad` / `alwaysLoad` 的作用。
- `claude_code_tool_gap_matrix.md` 将 Phase 1 状态更新为已完成 ToolPolicy/Permission v2：metadata、deny、skill/workflow gate、select policy、执行 guard、拒绝记忆、子 agent policy 继承。
- `agent_memory/context.md`、`progress.md`、`bugs.md` 已记录当前事实、进度和剩余风险。
- 学习备份已创建为 `learning_agent/test/69.md`，没有覆盖已有 `60.md` 到 `68.md`。

验证记录：
- 新增测试 `test_runtime_instructions_mentions_tool_policy_v2` 先红后绿；红灯失败于缺少 `Tool Policy v2`，绿灯结果为 `Ran 1 test in 0.009s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\tool_policy.py` exit code 0。
- 聚焦测试通过：10 条 ToolPolicyV2 相关测试最终复核结果为 `Ran 10 tests in 0.057s OK`。
- Full suite 通过：`learning_agent.test_learning_agent` 最终复核结果为 `Ran 268 tests in 20.854s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-26 Phase 3 MCP Lifecycle Parity

状态：已完成 ClaudeCode parity master design 的 Phase 3 第一轮可验证骨架；未 stage/commit/revert，未进入 Phase 4 真实 Chrome workflow。

成功标准：
- fake MCP client 工具列表变化并发送 `notifications/tools/list_changed` 后，registry 刷新后的 schema 必须移除旧工具并包含新工具。
- `tool_search` 在刷新后必须能搜到新的 MCP 工具，证明 ToolSearch 读取的是刷新后的 catalog。
- HTTP SSE 解析到 `notifications/tools/list_changed` 后，client 必须把 notification 放入 pending 队列。
- stdio client 必须能缓存无 `id` 的 JSON-RPC notification，并忽略普通 response。
- `prompts/list_changed` 和 `resources/list_changed` 必须形成生命周期事件，并递增 MCP skills/search 刷新版本挂点。
- Phase 1/2 的 ToolPolicy、ToolSearch、per-tool output protocol 邻近回归不能退化。

完成记录：
- 新增 Phase 3 计划文件 `docs/superpowers/plans/2026-05-26-claudecode-parity-phase3-mcp-lifecycle-parity.md`。
- `McpStdioClient` 新增 `_pending_notifications`、`pop_notifications()`、`_remember_notification()` 和 `_is_json_rpc_notification()`，并在 request 等待循环里保存非当前 response 的 notification。
- `McpHttpClient` 在 SSE event 解析路径里复用 `_remember_notification()`，并在 close 时清空 pending notifications。
- `McpToolRegistry` 新增 `_lifecycle_events`、`_mcp_skill_refresh_version`、`refresh_from_notifications()`、`lifecycle_events()`、`_drain_lifecycle_notifications()` 和 `_lifecycle_changed_kind()`。
- `LearningAgent` 新增 `_refresh_mcp_lifecycle_notifications()`，并让 `_tool_catalog()` 先消费 lifecycle notifications，再复用或重建 catalog。
- `learning_agent/test_learning_agent.py` 新增 5 条 Phase 3 回归测试，覆盖 tools/list_changed 刷新、ToolSearch 刷新、HTTP SSE notification、stdio notification、prompts/resources list_changed。
- `learning_agent/claude_code_tool_gap_matrix.md` 已更新 Phase 3 状态，不再把 MCP `tools/list_changed` 标成未支持。
- 已创建学习备份 `learning_agent/test/72.md`。

验证记录：
- 红灯验证：新增 Phase 3 测试最初暴露 `McpToolRegistry` 缺少 `refresh_from_notifications()`、`McpHttpClient` 缺少 `pop_notifications()`，以及 ToolSearch 不能搜到刷新后的新 MCP 工具。
- 绿灯验证：Phase 3 聚焦 5 条测试通过，结果为 `Ran 5 tests in 0.015s OK`。
- 邻近回归：ToolSearch / ToolPolicy / MCP metadata / per-tool output protocol 7 条测试通过，结果为 `Ran 7 tests in 0.057s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\tool_policy.py` exit code 0。
- Full suite 通过：`learning_agent.test_learning_agent` 结果为 `Ran 281 tests in 21.153s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-26 ToolPolicyV2 Final Review Fixes

状态：已按最终代码审查修复 4 个缺口；未 stage/commit/revert，未修改真实 Chrome workflow，未进入 Phase 2。

成功标准：
- `allowed_tools` 不再只约束展示层，直接 `_execute_tool(write_file)` 这类白名单外调用必须被拒绝，且不能进入权限弹窗或产生文件副作用。
- `search_hint` 和 `aliases` 必须真正参与 `tool_search` 召回，并在结果里展示命中依据。
- MCP 普通 `_meta["alwaysLoad"]` / `_meta["searchHint"]` 必须作为兼容 fallback 被识别。
- `allow_rules` 一旦配置非空，就必须成为真实白名单；未命中允许规则的工具不可见、不可选、不可执行。

完成记录：
- `learning_agent/tool_policy.py`：给 `ToolPolicy.decide()` 增加 allow_rules 白名单判断。
- `learning_agent/learning_agent.py`：给 `_execute_tool()` 增加 `allowed_tool_names` 执行期 guard。
- `learning_agent/learning_agent.py`：把 `tool.search_hint` 和 `tool.aliases` 接入 `_tool_search_score()`，并在搜索结果展示。
- `learning_agent/learning_agent.py`：MCP metadata 映射支持普通 `alwaysLoad` 和 `searchHint` fallback。
- `learning_agent/test_learning_agent.py`：新增 5 条最终审查回归测试。
- 已创建学习备份 `learning_agent/test/70.md`。

验证记录：
- `python` 和 `py` 命令在当前 Windows 环境不可用；已改用 Codex runtime Python：`C:\Users\joyzq\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\tool_policy.py` exit code 0。
- 新增 5 条测试通过，结果为 `Ran 5 tests in 0.024s OK`。
- 相关回归 13 条测试通过，结果为 `Ran 13 tests in 0.154s OK`。
- Full suite 通过：`learning_agent.test_learning_agent` 结果为 `Ran 273 tests in 21.073s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-26 Phase 2 per-tool output protocol

状态：已完成 ClaudeCode parity master design 的 Phase 2；未 stage/commit/revert，未修改真实 Chrome workflow 或 MCP list_changed。

成功标准：
- `tool_calls.items` 不再是共享 `properties.arguments`，而是 per-tool `anyOf` 分支。
- 每个分支用单值 `name.enum` 绑定具体工具名，并让 `arguments` 只包含该工具自己的 strict 参数 schema。
- 同一 Tool Pool 内 `browser_open` 和 `browser_connect_real_chrome` 这类工具互不继承参数，`browser_open` 不再看到 `confirm_real_profile`。
- 解析器继续兼容旧 `arguments` dict，并额外支持 `arguments_by_tool[name]` fallback。
- 旧测试里依赖共享 arguments 路径的断言全部迁移到分支 helper 或分支参数汇总 helper。

完成记录：
- 新增 Phase 2 计划文件 `docs/superpowers/plans/2026-05-26-claudecode-parity-phase2-per-tool-output-protocol.md`。
- `learning_agent/learning_agent.py` 新增 `_output_tool_call_item_schema()`、`_output_tool_call_branch_schema()`、`_empty_tool_call_branch_schema()`、`_strict_tool_arguments_schema()`，并让 `_output_schema()` 使用 per-tool item schema。
- `learning_agent/learning_agent.py` 更新 CLI 和 OAuth prompt 文案，不再要求无关参数写 `null`，改为每个 `arguments` 只能写当前工具自己的参数。
- `learning_agent/learning_agent.py` 进一步清理 OAuth/API prompt 残留旧句，明确改成“不要输出不属于当前工具的参数”。
- `learning_agent/learning_agent.py` 更新 `_parse_model_message()`，优先读 `arguments` dict，缺失时按 `arguments_by_tool[name]` 取对应分支。
- `learning_agent/test_learning_agent.py` 新增 per-tool branch、browser_open 参数隔离、`arguments_by_tool` 解析兼容测试，并迁移旧输出 schema 测试 helper。
- `learning_agent/runtime_instructions.md`、`learning_agent/README.md`、`learning_agent/claude_code_tool_gap_matrix.md` 已写入 Phase 2 输出协议说明。
- 已创建学习备份 `learning_agent/test/71.md`。

验证记录：
- 红灯验证：新增 3 条 Phase 2 测试最初失败，分别暴露缺少 `anyOf`、找不到工具分支、`arguments_by_tool` 解析为空。
- 绿灯验证：新增 3 条 Phase 2 测试通过，结果为 `Ran 3 tests in 0.002s OK`。
- 第一次 full suite 暴露 3 个旧测试仍依赖共享 `arguments` 路径或旧“混入 path”断言，已迁移为 per-tool branch 语义。
- 复核聚焦测试通过：8 条 Phase 2/旧路径迁移/OAuth prompt 测试结果为 `Ran 8 tests in 0.022s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\tool_policy.py` exit code 0。
- Full suite 通过：`learning_agent.test_learning_agent` 结果为 `Ran 276 tests in 21.057s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。

## 2026-05-26 ClaudeCode Core Parity Phase 3-7 收口

状态：按用户要求继续原计划直到 Phase 7；当前 Phase 3 剩余、Phase 4、Phase 5、Phase 6 和 Phase 7 已完成代码与文档收口，尚未 stage/commit/revert。

成功标准：
- MCP call progress 必须记录权限、开始、完成、失败等状态，并进入统一 observation。
- 真实浏览器请求必须走真实 Chrome workflow，不得默认退回独立 Chromium。
- `browser_connect_real_chrome` 必须受 `real_chrome` skill gate 和 `real_chrome_profile_ready` workflow gate 控制。
- Plan mode 等待用户确认期间必须硬拦截写入、删除、命令、外部操作等副作用工具。
- Worktree 当前不是假装真实 git worktree，而是明确记录 `state_only_fallback`。
- 长工具结果必须保存完整输出到磁盘，只把摘要回填上下文。
- Phase 7 必须有 parity checklist、README/runtime/gap matrix 文档和 unittest 回归覆盖。

完成记录：
- `learning_agent/learning_agent.py` 新增 `mcp_call_progress_events`、`observation_events`、`real_chrome_requested`、`tool_result_artifact_dir`、`active_artifacts` 状态。
- `learning_agent/learning_agent.py` 新增 `_detect_real_chrome_intent()`、`_maybe_confirm_plan_from_user_input()`、`_record_observation()`、`_offload_tool_output_if_needed()` 等 helper。
- `_execute_mcp_tool()` 已记录 MCP permission/start/completed/failed 进度，并根据 `browser_profile_status`、`browser_connect_real_chrome`、`browser_disconnect_real_chrome` 推进真实 Chrome workflow。
- `McpToolRegistry.agent_tools()` 已给真实 Chrome 连接/断开工具补 skill/workflow gate，并把 authenticate 和 browser profile status 作为强制可发现入口。
- `_execute_tool()` 已在具体分发前执行 policy 阻断记录和 plan mode 副作用阻断。
- `skill_load` 已把加载成功的 skill 写入 `ToolPolicyContext.loaded_skills`。
- `enter_worktree` / `exit_worktree` 已输出和保存 `mode=state_only_fallback`。
- `learning_agent/test_learning_agent.py` 新增 MCP progress、真实 Chrome workflow、plan mode gate、result persistence、Phase 7 checklist 测试。
- `docs/superpowers/specs/claudecode_parity_checklist.md` 已新增 Phase 1-7 PASS 清单和私有产品能力边界。
- `learning_agent/README.md`、`learning_agent/runtime_instructions.md`、`learning_agent/claude_code_tool_gap_matrix.md` 已同步 Phase 4-7 当前状态。

验证记录：
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` exit code 0。
- 新增 Phase 3-6 聚焦 4 条测试通过，结果为 `Ran 4 tests in 0.048s OK`。
- 新增和邻近文档/运行时聚焦 8 条测试通过，结果为 `Ran 8 tests in 0.069s OK`。
- Full suite 通过：`learning_agent.test_learning_agent` 结果为 `Ran 286 tests in 21.270s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。
- 已创建学习备份 `learning_agent/test/73.md`。

## 2026-05-26 Prompt Surface v2 改造

状态：按用户纠偏后的范围执行，只改会影响模型判断的 prompt surface；当前代码实现和红灯转绿已完成，尚未 stage/commit/revert。

成功标准：
- system prompt 必须声明 `Prompt Surface Architecture v2`，并明确用户本轮纠偏高于历史计划。
- `LearningAgent._build_initial_messages()` 必须实际注入项目级 `agent_memory/context.md`、`progress.md`、`bugs.md`，不能只在提示词里口头声明优先级。
- CLI/OAuth 模型适配器提示词必须说明：用户明确要求工具或真实浏览器时，不能用普通回答、搜索、fetch_url 或独立 Chromium 替代。
- `runtime_instructions.md` 必须在靠前位置定义 Prompt Surface v2，避免文件过长时新规则被截断。
- MCP 浏览器/搜索工具描述必须写清：搜索和 fetch_url 不是可见浏览器；普通 `browser_open` 是独立 Chromium，不用于真实 Chrome 请求。

完成记录：
- `learning_agent/learning_agent.py` 已新增 Prompt Surface v2 system prompt、项目级 agent_memory 三件套读取与注入、显式工具请求不可替代规则。
- `learning_agent/learning_agent.py` 已同步更新 Codex CLI 与 OAuth/API 适配器提示词。
- `learning_agent/runtime_instructions.md` 已新增 Prompt Surface Architecture v2 章节，并同步真实浏览器不可替代规则。
- `learning_agent/browser_automation_mcp_server.py` 已更新 `browser_open` 工具描述，明确不用于真实 Chrome/真实浏览器/登录态请求。
- `learning_agent/browser_search_mcp_server.py` 已更新 `web_search` 和 `fetch_url` 工具描述，明确不是可见浏览器，不能替代真实浏览器 workflow。
- `learning_agent/test_learning_agent.py` 已新增/扩展 prompt surface 回归测试。

验证记录：
- 红灯验证：6 条 prompt surface 测试最初失败，覆盖 system prompt v2、agent_memory 注入、适配器提示词、runtime rules、browser_search 和 browser_open 描述。
- 绿灯验证：同一组 6 条测试通过，结果为 `Ran 6 tests in 1.439s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\browser_automation_mcp_server.py learning_agent\browser_search_mcp_server.py` exit code 0。
- 复核聚焦测试通过：6 条 Prompt Surface v2 测试结果为 `Ran 6 tests in 1.524s OK`。
- Full suite 通过：`learning_agent.test_learning_agent` 结果为 `Ran 289 tests in 21.541s OK (skipped=1)`。
- `git diff --check` 通过，无空白错误；仅提示多个工作区文件未来可能 LF 转 CRLF。
- 已创建学习备份 `learning_agent/test/74.md`。
## 2026-05-26 ClaudeCode Prompt Surface 对比分析

- 已按用户要求聚焦分析 `D:\codexworkplace\software\ClaudeCode-main` 的提示词分层、每轮自动加载上下文、工具 schema 加载方式、token 占用和截断/压缩机制。
- 已确认 ClaudeCode 的核心链路包括 `constants/prompts.ts`、`context.ts`、`utils/queryContext.ts`、`query.ts`、`services/api/claude.ts`、`utils/api.ts`、`utils/claudemd.ts`、`memdir/memdir.ts` 和 `tools/ToolSearchTool/prompt.ts`。
- 已确认当前 `learning_agent` 每轮固定 system prompt 约 19,453 字符，粗略约 4,864 tokens；首轮可见内置工具 schema pretty JSON 约 35,440 字符，粗略约 8,860 tokens；严格输出 schema 约 53,592 字符，粗略约 13,398 tokens。
- 待向用户汇报：当前 `learning_agent` 已有 Tool Catalog/Tool Pool/deferred MCP 的雏形，但和 ClaudeCode 的成熟 prompt cache、auto compact、CLAUDE.md 发现、API 原生 tool search/defer_loading 仍不完全一致。

## 2026-05-26 Agent Prompt Architecture v1 设计文档

- 已根据用户确认的方向新增设计文档：`docs/superpowers/specs/2026-05-26-agent-prompt-architecture-v1-design.md`。
- 文档明确了目标架构：Prompt Kernel、Prompt Registry、Context Assembler、Tool Surface Manager、Memory Manager、Compact Manager、Runtime Enforcement、Evidence Ledger。
- 文档明确每轮自动加载和按需加载边界，并记录 token 预算目标、工具暴露策略、记忆索引策略、compact 策略和 7 阶段实施路线。
- 已完成机械自查：未发现 `TODO`、`TBD`、`FIXME`、`placeholder`、`占位` 等占位内容；文件存在，约 339 行。

## 2026-05-26 Agent Prompt Architecture v1 实施计划

- 已按用户要求执行下一步，把已确认的顶层设计拆成可执行实施计划：`docs/superpowers/plans/2026-05-26-agent-prompt-architecture-v1.md`。
- 本计划没有重复实现已通过的 ClaudeCode core parity 工具阶段，而是在现有 Tool Architecture v2、ToolPolicy v2、real Chrome workflow gate、Observation v1 和 result persistence 之上增加 Prompt Registry / Context Assembler 控制层。
- 计划分为 7 个任务：Prompt Registry、Context Assembler、Memory/Project Rules Index、Prompt Surface Report、Token Budget Report、Compact Summary、Evidence Ledger bridge、文档和最终回归测试。
- 计划明确后续代码新增前缀为 `新增代码+PromptArchitectureV1` 或 `修改代码+PromptArchitectureV1`，并要求新改 Python 每行中文注释。
- 当前只新增实施计划文档和项目记忆记录，尚未修改运行时代码、尚未 stage、尚未 commit。

## 2026-05-26 Prompt Architecture v1 Task 2

- 已按用户指定范围完成 Task 2 的第一轮实现：新增 `learning_agent/context_assembler.py`，修改 `learning_agent/learning_agent.py` 和 `learning_agent/test_learning_agent.py`，未进入 Task 3-7。
- 已用 TDD 先新增两条 Task 2 测试并确认红灯：初次失败为缺少 `learning_agent.context_assembler`，第二次失败为 `LearningAgent` 缺少 `last_prompt_surface_report`。
- `ContextAssembler` 当前按 `PromptRegistry.blocks` 的 priority 顺序装配非空 block，生成 `ContextBlockLoad`、`ContextAssemblyResult` 和可保存的 `PromptSurfaceReport`。
- `LearningAgent._build_initial_messages()` 当前保留原 helper 文案，但把 helper 输出、runtime instructions、project agent memory、long-term memory 映射到注册表 block 后交给 `ContextAssembler` 装配。
- 已创建学习备份 `learning_agent/test/75.md`。
## 2026-05-26 Prompt Architecture v1 Task 3

状态：已完成 Task 3 `Replace Full Memory Injection With Indexed Context Sources` 的实现与指定验证。

- 已先添加并运行两条红灯测试：`test_project_agent_memory_is_loaded_as_index_with_source_metadata`、`test_long_memory_does_not_enter_system_prompt_as_full_text`，确认旧实现仍把项目记忆和长期记忆作为全文注入。
- 已在 `learning_agent/context_assembler.py` 增加 `build_text_index()`、`build_project_memory_index()`、`build_long_term_memory_index()`，索引包含 source path、original chars、included chars、estimated tokens、truncated、headings、latest tail summary、stable_fact_count。
- 已修改 `LearningAgent._build_initial_messages()`，让 `context.project_memory_index` 和 `context.long_term_memory_index` 注入索引文本而不是完整长正文。
- 已让 `PromptSurfaceReport.to_text()` 输出索引 note，因此 `stable_fact_count` 和来源元数据可从 `last_prompt_surface_report.to_text()` 审计。
- 已通过 Task 3 聚焦测试、py_compile 和邻近回归测试。
## 2026-05-26 Prompt Architecture v1 Task 4

状态：已完成 Task 4 `Add Prompt Surface Report And Token Budget Report Tools` 的实现；未 stage、未 commit、未 revert、未 clean。

完成记录：
- 先在 `learning_agent/test_learning_agent.py` 新增两条红灯测试：`test_prompt_surface_report_tool_lists_loaded_prompt_blocks` 与 `test_token_budget_report_tool_includes_prompt_and_tool_pool_budget`。
- 红灯验证输出：`Ran 2 tests in 0.113s FAILED (failures=2)`，两个失败均为未知工具，符合 Task 4 预期。
- 在 `learning_agent/learning_agent.py` 注册 `prompt_surface_report` 与 `token_budget_report` 两个内置只读工具 schema。
- 在 `_execute_tool()` 中新增两个工具分发分支。
- 新增 `_prompt_surface_report()`，输出已加载 prompt blocks 的 id、title、source、load_policy、priority、loaded/status、estimated_tokens、note，并说明历史设计文档/历史计划不会自动加载。
- 新增 `_token_budget_report()`，输出 Prompt blocks、`estimated_total_tokens`、Current Tool Pool、工具数量、工具 schema 粗略 token 和工具名称。
- 创建学习备份：`learning_agent/test/77.md`。

验证记录：
- 绿灯验证输出：`Ran 2 tests in 0.027s OK`。
## 2026-05-26 Prompt Architecture v1 Task 4 final verification

- 修改代码+PromptArchitectureV1: Task 4 聚焦测试最终通过，命令为 `python -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_prompt_surface_report_tool_lists_loaded_prompt_blocks learning_agent.test_learning_agent.LearningAgentTests.test_token_budget_report_tool_includes_prompt_and_tool_pool_budget`，输出摘要为 `Ran 2 tests in 0.020s OK`，如果没有这条记录，后续排查者就不知道本轮新增工具测试已经绿灯。
- 修改代码+PromptArchitectureV1: 语法检查通过，命令为 `python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py`，命令无输出且退出码为 0，如果没有这条记录，后续排查者就不知道本轮 Python 文件至少通过了解析检查。
- 修改代码+PromptArchitectureV1: 邻近回归测试通过，命令覆盖 project memory index、prompt surface report 记录、deferred MCP tool pool 三个测试，输出摘要为 `Ran 3 tests in 0.030s OK`，如果没有这条记录，后续排查者就不知道本轮改动没有破坏相邻 Prompt Architecture 行为。
# 2026-05-26 Prompt Architecture v1 Task 5

- 修改代码+PromptArchitectureV1: 已完成 Task 5 `Add Compact Summary And Evidence Ledger Bridge`，范围限定在 compact summary、Evidence Ledger bridge、对应测试和学习备份；如果没有这条记录，后续执行者不知道 Task 5 已经进入绿灯验证阶段。
- 修改代码+PromptArchitectureV1: `ContextAssembler` 现在支持 `soft_token_limit`，默认约 60K，超出软预算时只从动态、非 `built_in`、超过自身预算的低优先级 block 生成 `Compact Summary`，并保留 `block_id/title/source/original_chars/included_chars/reason/full_text_loaded=false`；如果没有这条记录，后续排查者不知道 compact 语义已落地且核心策略不会被误压缩。
- 修改代码+PromptArchitectureV1: `prompt_surface_report(include_evidence=True)` 现在读取 `self.observation_events` 输出 Evidence Ledger，并展示 `event_type`、分类 label、`artifact_path`、`raw_output_chars` 等关键 payload；如果没有这条记录，后续排查者不知道 Task 4 的 evidence 占位已被替换。
- 修改代码+PromptArchitectureV1: 已创建学习备份 `learning_agent/test/78.md`；如果没有这条记录，后续学习者不容易找到本次新增/修改代码的中文说明。

# 2026-05-26 Prompt Architecture v1 Task 7 Final Verification

- 修改代码+PromptArchitectureV1: 已完成 Phase 7 最终验证，未 stage、未 commit、未 revert、未 clean；如果没有这条记录，后续接手者不知道本次实施计划已经完整跑到收口阶段。
- 修改代码+PromptArchitectureV1: 语法检查通过，命令为 `python -m py_compile learning_agent\learning_agent.py learning_agent\prompt_registry.py learning_agent\context_assembler.py learning_agent\test_learning_agent.py`，命令无输出且退出码为 0；如果没有这条记录，后续排查者不知道核心 Python 文件已经通过解析检查。
- 修改代码+PromptArchitectureV1: Prompt Architecture v1 聚焦测试通过，输出为 `Ran 10 tests in 0.082s OK`；如果没有这条记录，后续维护者不知道 Prompt Registry、Context Assembler、Memory Index、报告工具、Compact Summary 和 Evidence Ledger 聚焦测试已绿。
- 修改代码+PromptArchitectureV1: 邻近 prompt surface、tool pool、real Chrome 回归通过，输出为 `Ran 4 tests in 0.049s OK`；如果没有这条记录，后续维护者不知道本次新增提示词架构没有破坏相邻工具架构行为。
- 修改代码+PromptArchitectureV1: 完整测试套件通过，输出为 `Ran 304 tests in 26.606s OK (skipped=1)`；如果没有这条记录，后续维护者不知道 full suite 已完成。
- 修改代码+PromptArchitectureV1: `git diff --check` 通过，无空白错误，仅有 LF 会在 Git 触碰时替换为 CRLF 的警告；如果没有这条记录，后续维护者可能误把换行提示当作本次空白错误。

# 2026-05-26 Prompt Architecture v1 Phase 7 审查修复

- 修改代码+PromptArchitectureV1: 代码审查发现两个 Important 风险：compact 可能压缩 `built_in` 核心策略，以及 `LearningAgent` 未传入真实可配置 prompt 预算；如果没有这条记录，后续维护者不知道为什么 Phase 7 后又补了一轮架构修复。
- 修改代码+PromptArchitectureV1: 已新增红灯测试覆盖动态 compact、内置策略不 compact、生产路径预算传入、`prompt_soft_token_limit` 配置读取；红灯输出为 `Ran 4 tests in 0.035s FAILED (failures=1, errors=2)`；如果没有这条记录，后续维护者不知道本次修复有失败先证据。
- 修改代码+PromptArchitectureV1: 已修复 `ContextAssembler` 压缩候选过滤、默认约 60K 软预算、`LearningAgent(prompt_soft_token_limit=...)`、`runtime_config.json` / `LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT` 配置入口，并新增 `PromptLoadDecision`；如果没有这条记录，后续维护者可能误以为 compact 仍是单元测试专用能力。
- 修改代码+PromptArchitectureV1: 审查修复聚焦测试已通过，输出为 `Ran 5 tests in 0.043s OK`；如果没有这条记录，后续维护者不知道子代理审查反馈已转成回归测试并绿灯。
- 修改代码+PromptArchitectureV1: 审查修复后的语法检查通过，命令为 `python -m py_compile learning_agent\learning_agent.py learning_agent\prompt_registry.py learning_agent\context_assembler.py learning_agent\test_learning_agent.py`，命令无输出且退出码为 0；如果没有这条记录，后续维护者不知道新增预算配置和 compact 过滤代码已通过 Python 解析。
- 修改代码+PromptArchitectureV1: Prompt Architecture v1 扩展聚焦测试通过，输出为 `Ran 15 tests in 0.101s OK`；如果没有这条记录，后续维护者不知道 registry、assembler、memory index、report、budget、compact、config 和 evidence 相关测试已一起通过。
- 修改代码+PromptArchitectureV1: 相邻 prompt surface、tool pool、real Chrome、README/runtime 文档回归通过，输出为 `Ran 6 tests in 0.045s OK`；如果没有这条记录，后续维护者不知道审查修复没有破坏相邻工具架构和文档入口。
- 修改代码+PromptArchitectureV1: 完整测试套件通过，输出为 `Ran 307 tests in 22.708s OK (skipped=1)`；如果没有这条记录，后续维护者不知道最新代码状态已经完成 full suite 验证。
- 修改代码+PromptArchitectureV1: `git diff --check` 通过且无空白错误，仅有 LF 将被 Git 触碰时替换为 CRLF 的警告；如果没有这条记录，后续维护者可能误把换行警告当作本次修复引入的 whitespace error。

# 2026-05-26 Capability Packs 方案 B 执行记录

- 修改代码+CapabilityPacks: 已完成首轮工具池瘦身，实现 `KERNEL_TOOL_NAMES`、工具 `capability_pack` 元数据、`select_pack:<pack_name>` 加载流程，以及内置/MCP 工具按能力包延迟暴露；如果没有这条记录，后续接手者不知道方案 B 已进入绿灯实现阶段。
- 修改代码+CapabilityPacks: 已新增 12 个能力包 skill 文件，覆盖 file_operations、memory、execution、notebook、mcp、browser_automation、real_chrome、delegation、planning、diagnostics、long_running_work、prompt_architecture；如果没有这条记录，后续接手者可能重复创建同类 skill。
- 修改代码+CapabilityPacks: 已将 `runtime_instructions.md` 压缩为短 kernel，并保留搜索/浏览器/MCP/真实 Chrome/工作区工具等关键触发词；如果没有这条记录，后续维护者不知道 runtime 已从长提示词迁移到 skill router。
- 修改代码+CapabilityPacks: 已创建实施计划 `docs/superpowers/plans/2026-05-26-capability-packs.md`；如果没有这条记录，后续维护者不容易追溯本轮范围、成功标准和验证方式。
- 修改代码+CapabilityPacks: 完整测试套件通过，命令为 `python -m unittest learning_agent.test_learning_agent`，输出为 `Ran 312 tests in 20.668s OK (skipped=1)`；如果没有这条记录，后续维护者不知道方案 B 改动已完成 full suite 验证。
- 修改代码+CapabilityPacks: `git diff --check` 通过且无空白错误，仅有 LF 将被 Git 触碰时替换为 CRLF 的警告；如果没有这条记录，后续维护者可能误把换行提示当作本轮空白错误。

# 2026-05-26 RuntimePathFix 执行记录

- 修改代码+RuntimePathFix: 已修复 `runtime_instructions.md` 查找路径，工作区文件存在时仍优先使用，工作区缺失时回退到 `learning_agent/runtime_instructions.md`；如果没有这条记录，后续维护者不知道为什么当前项目根目录运行能加载短 kernel。
- 修改代码+RuntimePathFix: 已新增回归测试 `test_runtime_instructions_falls_back_to_learning_agent_file`，并调整旧缺失占位测试为显式缺失路径；如果没有这条记录，后续维护者不知道新旧行为边界已经被测试锁定。
- 修改代码+RuntimePathFix: 已更新 `learning_agent/test/current_every_turn_prompt_surface.txt`，当前文件展示的 runtime path 为包内 `learning_agent/runtime_instructions.md`；如果没有这条记录，用户查看提示词时可能看到旧占位文件。
- 修改代码+RuntimePathFix: 聚焦测试通过，输出为 `Ran 2 tests in 0.013s OK`；如果没有这条记录，后续维护者不知道兜底与缺失占位两条路径都已验证。
- 修改代码+RuntimePathFix: 完整测试套件通过，输出为 `Ran 313 tests in 21.608s OK (skipped=1)`；如果没有这条记录，后续维护者不知道路径修复没有破坏现有回归。
