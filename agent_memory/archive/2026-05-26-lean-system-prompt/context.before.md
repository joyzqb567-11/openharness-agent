# 项目上下文

## 2026-05-26 Prompt Architecture v1 Task 6 当前事实

- Prompt Architecture v1 文档层已补充：Tool parity 已经在公开可复现 core 层完成，Prompt Architecture v1 是 beyond-parity 控制层。
- runtime instructions 和 README 已说明 `prompt_surface_report` 用来解释加载了什么和为什么加载，`token_budget_report` 用来解释 prompt/tool/context 预算。
- 文档已明确 long memory 和 project files 默认索引化，只有当前轮显式 read 才读取全文。
- 文档已明确历史设计文档、旧计划和 checklist 不会自动影响模型，除非当前轮显式读取。
- 文档已区分 Compact Summary 与 Evidence Ledger：前者是压缩边界，后者是 observation-backed 证据边界。

## 2026-05-24 Browser Automation MCP 设计上下文

- 当前目标：把 `learning_agent` 的网页能力从 `browser_search` 的搜索/抓取网页，升级为真实浏览器自动化能力。
- 已确认路线：第一阶段新增独立 `browser_automation` MCP server，使用 Python Playwright 启动独立 Chromium；第二阶段再设计连接用户真实 Chrome。
- 已确认第一版范围：包含打开页面、页面快照、点击、输入、键盘、等待、截图、多标签页、控制台日志、网络摘要、上传、下载、JavaScript 执行和关闭浏览器。
- 已确认安全边界：`browser_evaluate` 进入第一版，但必须按高风险工具处理；不鼓励读取 cookie、localStorage、sessionStorage、token 或密码框内容。
- 已确认依赖前提：用户允许安装 Python `playwright` 包并执行 Chromium 浏览器安装。
- 设计文档位置：`docs/superpowers/specs/2026-05-24-browser-automation-mcp-design.md`。
- 早期设计阶段记录：当时设计文档已创建，等待用户审阅确认后再写实施计划；该记录不是当前状态，后续实施已完成。

- 较早阶段记录：`learning_agent` 曾进入 `Prompt / Context Architecture v1` 升级，路线已从单纯补最小工具转向成熟 coding agent 的系统提示词、上下文策略和运行时规则分层。
- 较早阶段记录：Prompt / Context Architecture v1 目标是默认身份升级为成熟 coding agent；系统提示词包含 Core Identity、Operating Principles、Context Policy、Tool Boundary 和 Response Policy；`runtime_instructions.md` 按 Operating Principles、Context Policy、Tool Policy、Response Policy 分层。
- 较早阶段边界（已过期）：当时只升级提示词与上下文架构，不实现 MCP HTTP session lifecycle；现在 MCP HTTP session/stream lifecycle v1 已完成，最新状态见下方实施结果。
- 当前用户偏好：保留中文教学解释，但工程可靠性、先读后改、证据优先和验证后再声称完成优先于单纯教学演示。
- 当前任务阶段：`learning_agent` 已完成 `MCP OAuth/auth metadata` 最小版；远程 Streamable HTTP MCP server 返回 `401` 和 `WWW-Authenticate` 时，会解析 `resource_metadata` 并暴露 `mcp__server__authenticate` 说明型伪工具。
- 当前 MCP auth 边界：只做 401 auth challenge 解析、doctor 报告和 `Authorization: Bearer` / `mcp_servers.json` headers 配置说明；不会自动打开浏览器、不会自动请求 metadata URL、不会自动交换 OAuth token，也不会把 token 放进 URL。
- 当前 MCP transport 边界（较早阶段记录）：HTTP 当时已支持 initialize、tools/list、tools/call、resources/list/read、prompts/list/get 和 auth-required 说明入口；旧 SSE / HTTP+SSE 双端点当时仍未实现，GET 监听流、DELETE 会话关闭、断线恢复和 Last-Event-ID 的最新状态请以下方 `MCP HTTP session/stream lifecycle v1 实施结果` 为准。
- 当前下一步（较早阶段记录，已过期）：当时建议补 `MCP HTTP session/stream lifecycle` 最小版；现在该 v1 已完成，最新下一步以本文件后续最新条目为准。
- 当前验证：`py_compile learning_agent.py test_learning_agent.py` 已通过；MCP/auth 专项 `Ran 10 tests in 1.233s OK`；完整 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 173 tests in 5.857s OK`。
- 说明：较早条目里的“当前下一步”保留当时阶段语境，最新有效建议以本文件最新日期和最新章节为准。
- 当前任务阶段：`learning_agent` 已完成 `Cron/Monitor` 最小版，新增 `cron_create` / `cron_list` / `cron_delete` / `monitor`，可登记、列出、回收进程内定时任务记录，并登记、列出、删除和记录监控结果。
- 当前 Cron/Monitor 边界：只保存当前 `LearningAgent` 实例进程内可审计记录，不会自动执行任务，不创建系统定时器，不跨进程常驻，不推送通知，不跨重启持久化。
- 上一阶段建议：Cron/Monitor 完成后曾建议补 `MCP prompts / MCP skills` 最小版；该建议已在当前阶段完成。
- 当前验证：`py_compile learning_agent.py test_learning_agent.py` 已通过；Cron/Monitor 专项 5 个测试已通过；完整 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 158 tests OK`。
- 当前任务阶段：`learning_agent` 已完成 `REPL` 最小版，新增 `repl`，可把最多 5 个安全白名单内的只读、状态或符号工具调用组织成一批可审计步骤。
- 当前 REPL 边界：`repl` 不是任意代码执行器，不允许写文件、运行命令、调用外部 MCP、启动子 agent，也不允许递归调用 `repl`。
- 当前下一步：适合补 `Cron/Monitor` 最小版，用本进程内、可审计、无推送依赖的方式登记持续观察或定时检查任务。
- 当前验证：`py_compile learning_agent.py test_learning_agent.py` 已通过；REPL 专项 6 个测试已通过；完整 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 153 tests OK`。
- 当前任务阶段：`learning_agent` 已完成 `LSP` 最小版，新增 `lsp_symbols` / `lsp_definition` / `lsp_diagnostics`，可用 Python 标准库 `ast` 对工作区内 `.py` 文件读取符号、定位定义和查看语法诊断。
- 当前下一步：适合补 `REPL` 最小版，用于把多次只读检查、符号查询或工具查询组织成批量可审计步骤，减少多轮工具调用开销。
- 当前验证：`py_compile learning_agent.py test_learning_agent.py` 已通过；LSP 专项 7 个测试已通过；完整 `python -m unittest learning_agent.test_learning_agent` 已通过，结果为 `Ran 147 tests in 7.451s OK`。
- 当前任务阶段：`learning_agent` 已完成 `EnterWorktree` / `ExitWorktree` 最小版，`enter_worktree` / `exit_worktree` 可记录轻量工作区隔离状态、隔离目录、原因、目标、总结和遗漏项。
- 当前下一步：适合补 `LSP` 最小版，让 agent 获得轻量符号、定义或诊断读取能力，提升后续代码理解质量。
- 当前验证：`py_compile`、WorktreeIsolation 专项 6 个测试和完整 `python -m unittest learning_agent.test_learning_agent` 均已通过，完整结果为 `Ran 140 tests in 5.604s OK`。
- 上一阶段：`VerifyPlanExecution` 已完成，`verify_plan_execution` 可汇总计划、已执行步骤、验证证据、遗漏项和最终状态。
- 当前任务阶段：`learning_agent` 已完成教学版 `read_peer_messages` / `ack_peer_message` / `team_delete`，team 通信层现在支持登记、留言、列出、读取、确认和删除 peer。
- 当前下一步：适合把 peer 与后台 `task` 绑定，让 team 从进程内登记和消息队列升级成可运行、可查询、可停止的协作成员。
- 当前任务阶段：`learning_agent` 已完成教学版 `team_create` / `send_message` / `list_peers`，用于登记 peer、向 peer inbox 留消息、查看 peer 总览。
- 当前边界：team 通信层只保存当前进程内状态，不启动真实独立 agent，不跨进程持久化；`ack_peer_message` 只是教学版确认标记，不代表真实 agent 自动完成工作。
- 当前任务：配置用户级 Codex skill，名称为 `multi-agent`，内容参考用户提供的 zqb Multi-Agent skills 方案。
- 项目规则：非简单任务开始前维护 `agent_memory/`，并将当前任务进度和风险记录在对应文件。
- 用户偏好：涉及新增或修改代码时，需要中文解释并在 `learning_agent/test` 目录保留学习备份。
## 2026-05-24 MCP transport 当前事实

- learning_agent 已支持 MCP stdio 和 Streamable HTTP 最小链路。
- `McpServerConfig` 现在包含 `transport`、`url`、`headers`；旧配置不写 `transport` 时默认 `stdio`，继续使用 `command` + `args`。
- `transport=http` 使用 `McpHttpClient`，通过单 endpoint JSON-RPC POST 支持 initialize、tools/list、tools/call、resources/list、resources/read、prompts/list、prompts/get。
- HTTP 请求会发送 `Accept: application/json, text/event-stream`，初始化后携带 `MCP-Protocol-Version`，并继承 server 返回的 `Mcp-Session-Id`。
- `transport=sse` 可被解析和注册，但当前只通过 `McpSseClient` 明确报错，提示旧 HTTP+SSE 暂未实现并建议改用 `transport=http`。
- `mcp-doctor`、`runtime_instructions.md`、`README.md`、`claude_code_tool_gap_matrix.md` 和 `learning_agent_CONTEXT.md` 已同步这个边界。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 设计上下文

- 当前任务阶段：已创建 `docs/superpowers/specs/2026-05-24-mcp-http-session-stream-lifecycle-v1-design.md`，本阶段只做设计确认，不修改运行时代码。
- 当前设计目标：以官方 MCP `2025-11-25` 稳定规范为目标，补齐 Streamable HTTP 的 bounded GET 监听、SSE event 结构化解析、`Last-Event-ID` 恢复、HTTP DELETE 会话关闭和 404 session 过期重建策略。
- 当前设计选择：推荐“有界生命周期增强”，不启动永久后台 listener，避免当前教学版 agent 引入隐藏线程、上下文自动注入和难排查状态。
- 当前协议风险：官方 draft changelog 已提出未来可能移除 protocol-level sessions、`MCP-Session-Id` 和 GET endpoint；因此设计要求把 session/stream 细节封装在 HTTP transport 内部，后续便于迁移。
- 当前确认点：等待用户确认是否采用推荐方案 A，再进入实施计划；实施前还需列出将新增/修改的测试、代码、文档和学习备份文件。
- 当前实施计划：`docs/superpowers/plans/2026-05-24-mcp-http-session-stream-lifecycle-v1.md` 已创建，建议执行方式为 subagent-driven development；若用户更希望本会话直接做，可改用 inline executing-plans。
- 当前代码状态：本阶段只新增实施计划和更新 agent_memory，尚未修改 `learning_agent.py`、测试或文档运行时内容。

## 2026-05-24 Browser Automation MCP 第一阶段实施结果

- `learning_agent` 已注册并文档化 `browser_automation` MCP server，第一阶段使用独立 Playwright Chromium，不连接用户真实 Chrome，不继承真实 Chrome 登录态、cookie、扩展或历史记录。
- 已实现/记录的工具名包括：`browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_tabs`、`browser_console`、`browser_network`、`browser_upload_file`、`browser_downloads`、`browser_evaluate`、`browser_close`。
- 使用边界：真实交互、截图、console/network、上传下载和页面 JavaScript 使用 `mcp__browser_automation__...`；普通搜索或 URL 正文读取仍优先使用 `mcp__browser_search__web_search` / `mcp__browser_search__fetch_url`。
- 产物边界：截图、下载和浏览器运行产物放入 `learning_agent/browser_artifacts/` 或 `browser_artifacts/`。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 实施结果

- 当前任务阶段：`MCP HTTP session/stream lifecycle v1` 已完成代码、测试、文档和审查主流程，下一步只剩最终全量验证和收尾汇报。
- 当前已实现能力：HTTP POST 可解析 `text/event-stream` SSE 响应并记录 `last_event_id`、`retry_ms`、最近事件和累计事件数。
- 当前已实现能力：`McpHttpClient.listen_stream()` 支持有界 `GET` SSE 监听，可发送 `Last-Event-ID` 恢复游标，并对 `405` 返回清晰非致命边界。
- 当前已实现能力：`McpHttpClient.close()` 在存在 HTTP session 时会尝试无 body、无 `Content-Type` 的 `DELETE`，并在本地清理 `_started`、`_session_id`、stream state 和最近事件缓存。
- 当前已实现能力：带 session 的 HTTP 请求遇到 `404` 时会清理旧 session、重新 initialize，并最多重试一次原请求，避免无限递归。
- 当前已实现能力：`LearningAgent` 新增内置工具 `listen_mcp_stream`，模型可在权限确认后按 `server`、`max_events`、`timeout_seconds`、`resume` 有界读取 MCP HTTP stream。
- 当前文档状态：`runtime_instructions.md`、`README.md`、`claude_code_tool_gap_matrix.md` 已同步 v1 能力，并明确仍不是后台常驻 listener。
- 当前边界：仍未实现旧 HTTP+SSE 双端点兼容、永久后台 listener、完整 server-to-client capabilities、完整 MCP OAuth UI、动态客户端注册或 PKCE。
- 当前审查状态：Task 1 到 Task 6 均已经过子代理实现、规格审查和质量审查；Task 7 正在更新记忆和学习备份。

## 2026-05-25 Codex OAuth 重新登录兜底

- 当前任务阶段：已修复 `CodexOAuthChatModel` 在 refresh token 被拒绝或 Codex API 返回 `401/403` 时不会自动重新网页登录的问题。
- 当前已实现能力：access token 快过期时仍优先使用 refresh token 静默刷新；如果 refresh token 失效并出现 `invalid_grant`、`HTTP 400`、`HTTP 401` 或 `unauthorized`，会重新打开浏览器登录并保存新 token。
- 当前已实现能力：Codex responses API 首次请求返回 `401/403`、`unauthorized`、`forbidden`、`invalid_token` 或 `invalid bearer` 时，会重新打开浏览器并只重试一次本轮请求，避免无限登录循环。
- 当前边界：`The read operation timed out` / 响应读取超时不等于已确认 OAuth 过期；这种情况不会自动弹网页登录，会提示用户这是网络或 Codex 后端流式响应读取超时。
- 当前验证：`py_compile` 通过；OAuth 聚焦 6 条测试通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 231 tests in 23.916s OK (skipped=1)`。

## 2026-05-25 Codex strict response_format 当前事实

- `CodexCliChatModel._output_schema(tools=...)` 生成的 schema 会被 Codex OAuth/API 直连模式放入 `text.format.schema`。
- Codex Responses strict schema 要求嵌套对象的 `required` 必须包含该对象 `properties` 中的每一个键；否则会返回 `HTTP 400 invalid_json_schema`，例如 `todos.items` 缺少 `id`。
- 当前已实现 `_strict_response_format_schema()`，会递归修正工具参数 schema 中的嵌套 `properties`、`required`、`additionalProperties` 和数组 `items`。
- 当前验证：本地 schema 扫描 `problems 0`；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 232 tests in 24.951s OK (skipped=1)`。

## 2026-05-25 Codex strict schema 开放对象边界

- Codex strict response_format 不接受开放对象，例如 `{"type":"object","additionalProperties":true}`；object schema 必须显式关闭 `additionalProperties=false`。
- 当前已处理 `prompt_arguments` 和 `repl.calls[].arguments` 这类开放对象：在模型输出 schema 中降级为空对象 strict schema，以保证 OAuth/API 主链路可用。
- 当前边界：模型结构化输出暂时不能自由生成任意未知键的对象参数；如需完整支持 MCP prompt 任意参数或 REPL 子调用任意参数，需要后续改造输出协议。
- 当前验证：本地 schema 扫描 `problems 0`；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 233 tests in 25.767s OK (skipped=1)`。

## 2026-05-25 Codex OAuth SSE 流式读取卡住修复

- 已确认用户输入“使用真实浏览器查询越南胡志明今天的天气”后，最新 debug 日志停在 `model_request`，没有 `model_response`、没有工具调用、也没有浏览器 MCP 权限请求，因此卡点发生在 Codex OAuth/API 模型响应读取阶段，而不是浏览器自动化工具本身。
- 根因：`CodexOAuthChatModel._post_json_request()` 在 `stream=true` 时仍然使用 `response.read()` 整包读取 SSE 响应；真实 Codex Responses 流可能保持连接或等待后续事件，导致 agent 在模型第一轮响应前卡住。
- 当前修复：`stream=true` 时改为 `_read_sse_response_until_done()`，按 `readline()` 增量读取 SSE 行，遇到 `response.output_text.done`、`response.completed` 或 `data: [DONE]` 就停止读取并复用现有 `_parse_sse_response()` 解析。
- 当前边界：这次只修复 Codex OAuth/API 的模型流读取，不改变 browser_automation MCP 工具；如果真实浏览器工具执行过程中卡住，需要单独看 `tool_call/tool_result` 日志。
- 当前验证：新增回归测试先红后绿；OAuth/strict schema 聚焦 9 条测试通过；`py_compile` 通过；最新完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 234 tests in 22.403s OK (skipped=1)`。第一次完整测试中 browser_automation 本地页面测试出现一次 stdio 超时，单独重跑和后续全量均通过，记录为环境/启动抖动观察项。

## 2026-05-25 Browser automation 调用后模型超时与 MCP 参数清洗

- 已确认用户截图中 `browser_open` 并非没有返回；debug 日志显示 Google 打开后进入 `sorry/index` 拦截页，随后 Bing 搜索页 `browser_open` 返回成功，真正失败发生在工具结果返回后的第 2 轮 Codex OAuth/API 模型调用。
- 当前已实现 `McpToolRegistry.sanitize_tool_arguments()`，会按每个 MCP 工具的 `inputSchema.properties` 清洗参数；`browser_open` 现在只会收到 `url`、`new_tab`、`timeout_ms` 这类 schema 声明字段，`status`、`state`、`action`、`result_status`、`confirm_real_profile` 会被丢弃。
- 当前已实现 `LearningAgent._execute_mcp_tool()` 在用户授权前先清洗参数，确保授权提示和真实调用使用同一份安全参数，避免截图里那种把 `browser_tabs`/真实 profile 字段混入 `browser_open` 的误导性提示。
- 当前已实现 `browser_automation` stdio client 工厂超时提升为 `35.0` 秒，覆盖浏览器工具自身最高 `30000ms` 页面加载等待并留通信余量；其他 MCP server 仍保持 `5.0` 秒快速失败。
- 当前已实现 Codex OAuth/API 第一次 read timeout 时用同一 token 重试一次，不触发网页登录；如果第二次仍 timeout，仍会返回中文超时说明。
- 当前验证：新增 4 条回归测试先红后绿；`py_compile` 通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 238 tests in 24.580s OK (skipped=1)`。

## 2026-05-25 Codex OAuth/API 远端断连处理

- 已确认用户最新截图中的 `Remote end closed connection without response` 发生在第 0 轮 Codex OAuth/API 模型调用，模型没有产生任何 `tool_calls`，因此不是 browser_automation MCP 工具调用错误。
- 当前已实现 `_is_transient_api_error()`，把 `The read operation timed out` 和 `RemoteDisconnected`/`Remote end closed connection without response` 都归类为可用同一 token 重试一次的临时 API 网络错误。
- 当前已实现 `_is_remote_closed_error()` 与中文错误格式化：如果重试后仍失败，会提示“远端连接关闭”，说明这通常是 Codex 后端或中间网络在返回响应前断开，不一定是 OAuth 登录过期，不会误触发网页登录。
- 当前已同步 README：OAuth/API 直连模式文档现在说明 `Remote end closed connection without response` 的边界和自动重试一次的行为。
- 当前已补强 `McpStdioClient` 默认超时策略：直接构造 `McpStdioClient(McpServerConfig(name="browser_automation", ...))` 时也默认使用 `35.0` 秒，避免绕过 registry 工厂后仍走 5 秒。
- 当前验证：新增断连重试、断连中文提示、直接构造 browser_automation 长超时测试先红后绿；`py_compile` 通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 241 tests in 20.177s OK (skipped=1)`。

## 2026-05-25 Tool Architecture v2 顶层设计上下文

- 当前用户已明确确认：`learning_agent` 后续升级目标是做成 ClaudeCode 和 Codex 一样的成熟 agent，工具调用顶层设计至少必须对齐 ClaudeCode；只有完成这层基础，后续才可能升级到比 ClaudeCode 更先进的 agent。
- 当前已确认架构差距：现有 `tool_search` 只是搜索当前可见工具；ClaudeCode 的 ToolSearch 结合 `defer_loading`、`tool_reference`、`shouldDefer` 和 `alwaysLoad`，属于工具池与延迟加载架构。
- 当前已确认根本问题：继续修改单个 MCP/browser 工具无法解决真实浏览器误选、工具暴露过早和参数串味问题；需要重建工具对象、工具目录、工具池、权限前置、延迟加载、skill gate 和输出协议。
- 当前已创建设计文档：`docs/superpowers/specs/2026-05-25-tool-architecture-v2-claudecode-codex-alignment-design.md`。
- 当前设计最低验收线：默认首轮不暴露全部 MCP/browser/workspace 工具；高风险工具必须 deferred；ToolSearch v2 能 search/select catalog；真实 Chrome 请求必须走 real Chrome workflow；输出协议不再把所有工具参数揉成统一大对象。
- 当前代码状态：本阶段只新增设计与记忆记录，尚未修改 `learning_agent.py`、测试或运行时代码。

## 2026-05-25 Tool Architecture v2 core spine 实施结果

- 已实现第一阶段核心主干：`AgentTool` 元数据对象、内置工具 catalog 包装、MCP 工具 catalog 出口、完整 `Tool Catalog`、当前 `Tool Pool`、`tool_search select:<tool_name>` 加载和未加载 deferred 工具执行门禁。
- 当前行为：内置工具保持默认可见，`tool_search` 始终可见；MCP 工具默认进入完整 catalog 但不进入首轮 Tool Pool，模型需要先通过 `tool_search` 搜索并 select 后才能看到和调用。
- 当前行为：拒绝启动 MCP 时，MCP 工具不会进入 catalog；部分 MCP server 启动失败时，成功 server 的工具仍可在 catalog 中被搜索并按需 select。
- 当前行为：输出 schema 现在基于当前 Tool Pool 生成；未加载 deferred 工具的参数不会进入模型输出 schema，select 后只加入已加载工具的参数。
- 当前行为：子 agent 只继承父 agent 已经 select 且被 `allowed_tools` 白名单允许的 deferred 工具，避免子任务越权看到未加载 MCP 工具。
- 已同步运行规则和 README，明确 Tool Architecture v2、Tool Catalog、Tool Pool、deferred loading、`select:<tool_name>` 和执行门禁。
- 已更新差距矩阵，把 `ToolSearch` 从“最小版搜索当前可见工具”改为“v2 core spine 已完成”，并把下一步转向真实 Chrome workflow/skill gate、风险策略和 MCP notifications/list_changed。
- 验证结果：`py_compile` 通过；ToolArchitectureV2 聚焦 7 条测试通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 252 tests in 20.823s OK (skipped=1)`。

## 2026-05-25 ClaudeCode agent core parity master design

- 用户要求“至少完全追平 ClaudeCode”，已明确采用 agent core parity 定义，而不是复制 ClaudeCode 私有产品 UI、账号体系或内部 ant-only 工具。
- 已补读 ClaudeCode `Tool.ts`、`tools.ts`、`services/mcp/client.ts`、`useManageMCPConnections.ts` 等源码证据，确认完整追平必须覆盖 Tool 对象、Tool Pool、权限、MCP annotations/list_changed、skills/workflow、真实 Chrome workflow、输出协议、任务/worktree/context/observation。
- 已创建 master design：`docs/superpowers/specs/2026-05-25-claudecode-agent-core-parity-master-design.md`。
- 当前推荐下一阶段：Phase 1 `Tool Policy / Permission v2`，先补齐 policy、allow/deny、MCP annotations、`alwaysLoad/searchHint`、skill/workflow gate 和 select policy，再继续 per-tool output protocol 与真实 Chrome workflow。

## 2026-05-25 Tool Policy / Permission v2 plan context

- Phase 1 实施计划已创建：`docs/superpowers/plans/2026-05-25-claudecode-parity-phase1-tool-policy-permission-v2.md`。
- 计划将新增独立模块 `learning_agent/tool_policy.py`，避免继续把策略判断堆到 `learning_agent.py`。
- 计划要求 MCP annotations 映射到 `AgentTool`：`readOnlyHint`、`destructiveHint`、`openWorldHint`、`anthropic/searchHint`、`anthropic/alwaysLoad`。
- 计划要求 `tool_search select` 经过 ToolPolicy，不能绕过 deny rule、skill gate 或 workflow gate。
- 计划要求执行层在权限弹窗前执行 policy guard，并记住同一工具和参数的用户拒绝。
- 计划要求子 agent 继承父 agent 的 policy context，而不只是继承 loaded tool names。
## 2026-05-25 ToolPolicyV2 Task 1 当前事实

- `learning_agent/tool_policy.py` 已作为独立策略模块新增，不 import `learning_agent.learning_agent`，通过 `getattr()` 读取传入工具对象字段，避免循环依赖。
- `ToolPolicyRule` 支持 `tool_name`、`server_name`、`source` 三个匹配字段；空规则不会匹配所有工具，只有至少一个非空字段参与且全部命中才算匹配。
- `ToolPolicy.decide()` 当前实现 deny 优先，其次 skill gate、workflow gate、deferred，最后 loaded；返回 `ToolPolicyDecision` 的 `state/visible/selectable/executable/reason`。
- 当前 Task 1 只提供核心策略对象和测试，不把策略接入 Tool Pool、tool_search select 或执行层；这些属于后续 Task。

## 2026-05-25 ToolPolicyV2 Task 2 当前事实

- `AgentTool` 当前已新增 `aliases/search_hint/input_json_schema/output_schema/is_open_world/strict/max_result_size_chars` 字段，作为后续 ToolPolicy 和工具搜索策略的元数据挂点。
- `agent_tool_from_schema(...)` 当前已支持上述新增字段的关键字参数，并保留默认值以兼容既有调用。
- `McpToolRegistry.start()` 当前会按前缀工具名缓存 MCP 原始 `annotations`、`_meta`、`inputSchema`、`outputSchema` 和合理 `strict` 标记。
- `McpToolRegistry.agent_tools()` 当前会把 `readOnlyHint/destructiveHint/openWorldHint/anthropic/searchHint/anthropic/alwaysLoad` 映射进 `AgentTool`。
- 当前 Task 2 仍不把 ToolPolicy 接入 Tool Pool、ToolSearch select 或执行层；这些仍属于后续 Task。

## 2026-05-26 ToolPolicyV2 Phase 1 完成事实

- Phase 1 ToolPolicy/Permission v2 已完成 Task 1-6 收口：`tool_policy.py` 策略核心、工具 metadata、MCP annotations 与 `_meta` 映射、Tool Pool / `tool_search select` policy、执行前 guard、拒绝记忆、子 agent policy 继承、文档与学习备份都已落地。
- 当前 `tool_search select` 可能返回或触发 `blocked`、`needs_skill`、`needs_workflow` 等 policy 状态；模型运行规则已经提醒不要把 select 失败当作工具已加载。
- `deny rule` 当前在工具进入 Tool Pool 前和执行前都有硬拦截；被策略拒绝的工具不会继续走真实工具调用权限弹窗。
- MCP `readOnlyHint`、`destructiveHint`、`openWorldHint`、`anthropic/searchHint`、`anthropic/alwaysLoad` / `alwaysLoad` 已进入工具 metadata，用于风险、搜索和加载策略。
- 剩余风险：拒绝记忆仍是进程内状态，不持久化；MCP `tools/list_changed` / server notifications、真实 Chrome workflow、per-tool output protocol 仍属于后续阶段。

## 2026-05-26 ToolPolicyV2 Final Review Fixes 当前事实

- 最终审查确认并已修复：`allowed_tools` 以前只过滤模型可见 schema，不拦截执行层；现在 `_execute_tool()` 首行会拒绝白名单外工具，不进入权限弹窗或具体分发。
- 最终审查确认并已修复：`AgentTool.search_hint` 和 `AgentTool.aliases` 以前只保存不参与搜索；现在 `_tool_search_score()` 会按 search hint 和 aliases 加权召回，搜索结果也展示对应字段。
- 最终审查确认并已修复：MCP `_meta["alwaysLoad"]` / `_meta["searchHint"]` 兼容字段现在会作为 `anthropic/alwaysLoad` / `anthropic/searchHint` 的 fallback 被读取。
- 最终审查确认并已修复：`allow_rules` 以前只是上下文字段；现在一旦配置非空 allow rules，未命中允许规则的工具会被 `blocked`，形成真实白名单。
- 新增回归测试 5 条并通过，随后相关 ToolPolicy/MCP/子 agent 聚焦 13 条测试通过，完整 `learning_agent.test_learning_agent` 通过结果为 `Ran 273 tests in 21.073s OK (skipped=1)`。

## 2026-05-26 Phase 2 per-tool output protocol 当前事实

- Phase 2 已完成：`CodexCliChatModel._output_schema()` 不再给 `tool_calls[].arguments` 生成共享大对象，而是让 `tool_calls.items` 使用按工具名绑定的 `anyOf` 分支。
- 每个 per-tool 分支都把 `properties.name.enum` 固定为一个工具名，并把 `properties.arguments` 限制为该工具自己的 strict 参数 schema。
- 现在 `mcp__browser_automation__browser_open` 分支只会包含打开页面工具自己的参数，不会从 `mcp__browser_automation__browser_connect_real_chrome` 分支继承 `confirm_real_profile`。
- `_parse_model_message()` 保留旧 `arguments` dict 解析路径，并兼容 `arguments_by_tool[name]` 兜底；这只是解析兼容，不是 strict 输出 schema 的主路径。
- 运行规则、README、ClaudeCode 差距矩阵已同步说明 Phase 2：Tool Architecture v2 core spine 负责“工具是否进入 Tool Pool”，ToolPolicy v2 负责“能不能暴露/select/执行”，per-tool output protocol 负责“同一个 Tool Pool 内参数不串味”。
- 已确认并修正 OAuth/API prompt 残留的旧规则：不再提示“无关参数写 null”，改为“不要输出不属于当前工具的参数”。
- 当前验证：`py_compile` 通过；8 条 Phase 2/旧路径迁移/OAuth prompt 聚焦测试通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 276 tests in 21.057s OK (skipped=1)`。

## 2026-05-26 Phase 3 MCP Lifecycle Parity 当前事实

- Phase 3 已按 ClaudeCode `useManageMCPConnections.ts` 的生命周期 handler 思路完成第一轮骨架：MCP client 先缓存 server notifications，registry 再统一 drain、分类和刷新。
- stdio MCP client 现在会保存无 `id` 且带 `method` 的 JSON-RPC notification，不再在等待某个 request response 时直接丢弃 `notifications/tools/list_changed` 这类消息。
- HTTP MCP client 现在会把 SSE `data:` 中的 JSON-RPC notification 同步放入 pending notification 队列，避免 `tools/list_changed` 只进入 recent_events 而不能驱动刷新。
- `McpToolRegistry.refresh_from_notifications()` 会消费所有 client 的 pending notifications；遇到 `tools/list_changed` 时重跑 `start()`，刷新 MCP tool schemas、routes 和 metadata。
- `LearningAgent._tool_catalog()` 读取 catalog 前会先调用 `_refresh_mcp_lifecycle_notifications()`；如果 registry 刷新了 tools，会清理 `_tool_catalog_cache`，让 ToolSearch 和下一轮 Tool Pool 看到新工具。
- `prompts/list_changed` 和 `resources/list_changed` 现在会进入生命周期事件审计，并递增 `mcp_skill_refresh_version`，作为后续 MCP skills/search index 失效和刷新挂点。
- 当前边界：本阶段没有伪造永久后台 listener，没有实现完整 call progress UI，也没有复制 ClaudeCode 私有产品 channel；它实现的是“收到或轮询到 notification 后刷新”的可验证协议骨架。
- 当前验证：Phase 3 聚焦 5 条测试通过；Phase 1/2 邻近回归 7 条通过；`py_compile` 通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 281 tests in 21.153s OK (skipped=1)`；`git diff --check` 通过，仅有 LF/CRLF 提示。

## 2026-05-26 Phase 4-7 ClaudeCode Core Parity 当前事实

- Phase 4 已完成真实 Chrome workflow gate：`browser_profile_status` 被强制 always-load；`browser_connect_real_chrome` / `browser_disconnect_real_chrome` 会带 `real_chrome` skill gate 和 `real_chrome_profile_ready` workflow gate。
- 用户输入命中“真实浏览器、真实的浏览器、真实 Chrome、桌面 Chrome、当前浏览器、登录态、real browser、real chrome、desktop chrome、current browser”等表达时，agent 会把本轮标记为真实 Chrome 需求。
- 在真实 Chrome 已连接前，`browser_open`、`browser_click`、`browser_type`、`browser_screenshot`、`browser_evaluate` 等独立浏览器动作会被策略层判为 `needs_workflow`，避免继续误走独立 Chromium。
- MCP 调用现在会记录 `permission_requested`、`permission_denied`、`started`、`completed`、`failed` 等 progress 事件，并同步进入 `observation_events`。
- `skill_load` 成功后会把 skill 名和下划线别名写入 `ToolPolicyContext.loaded_skills`，使 skill gate 不再只是文档约定。
- Plan mode 已有执行层副作用闸门：`exit_plan_mode` 后等待用户确认期间，写文件、删除、命令、外部 MCP、task/team/worktree/cron/monitor 等副作用工具会被硬拦截；用户下一轮明确“确认/同意/按计划/继续执行”等语义后才解锁。
- `enter_worktree` / `exit_worktree` 现在明确输出并记录 `mode=state_only_fallback`，表示当前只是状态型隔离，不创建真实 git worktree。
- Phase 6 已新增 `observation_events`、`active_artifacts` 和 `learning_agent/debug_logs/tool_results/` 长工具结果落盘机制；超过回填阈值的工具输出会保存完整文件，只把头尾摘要放回模型上下文。
- Phase 7 已创建 `docs/superpowers/specs/claudecode_parity_checklist.md`，并同步更新 README、runtime instructions、ClaudeCode gap matrix 和 unittest 文档断言。
- 当前可诚实声明：learning_agent 的公开可复现 agent core 已基本追平 ClaudeCode/Codex 成熟工具架构思路；仍不声明复制 ClaudeCode 私有产品能力、商业账号体系、推送、PR 订阅、远程触发、云协作或完整图形产品 UI。

## 2026-05-26 Prompt Surface v2 当前事实

- 用户明确纠偏：本阶段目标不是继续列功能路线，而是修改所有会影响 Codex/LearningAgent 判断的系统提示词、运行规则提示词、模型适配器提示词和加载上下文提示词。
- 已确认真实加载链路：`LearningAgent._build_initial_messages()` 自动注入代码内置 system prompt、`runtime_instructions.md`、`memory.md`；本次新增项目级 `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md` 首尾摘要注入。
- 已确认工具选择也受 prompt surface 影响：内置 `TOOL_SCHEMAS`、MCP server `TOOLS` 描述、参数说明、searchHint、aliases 都会影响模型选工具。
- 已升级系统提示词为 `Prompt Surface Architecture v2`，加入用户本轮明确纠偏优先、自动加载入口清单、显式工具请求不可被替代、真实浏览器请求不能由搜索/fetch_url/独立 Chromium 冒充。
- 已升级 CLI/OAuth 模型适配器提示词：用户明确要求使用工具、真实浏览器、真实 Chrome、桌面可见浏览器或登录态时，不能用普通回答、`web_search`、`fetch_url` 或独立 Chromium 替代。
- 已升级 `runtime_instructions.md` 顶部 Prompt Surface v2 规则，确保即使运行规则文件被 8000 字符截断，新规则仍能进入 system prompt。
- 已升级 MCP 工具描述：`browser_open` 明确是独立 Chromium 且不用于真实 Chrome；`web_search` 与 `fetch_url` 明确不是可见浏览器，不能替代真实浏览器 workflow。
## 2026-05-26 Prompt Architecture v1 顶层设计事实

- 用户已确认先做成熟 agent 顶层提示词架构设计，再进入代码实现。
- 当前正式设计文档为：`docs/superpowers/specs/2026-05-26-agent-prompt-architecture-v1-design.md`。
- 已确认推荐路线是 `ClaudeCode-compatible + Prompt Registry`：先追平 ClaudeCode 的 system prompt 分层、项目规则加载、ToolSearch、deferred tools、compact、prompt cache、memory 分层，再增加 Prompt Surface Report、Token Budget Report、Evidence Ledger 和 Tool Exposure Audit。
- 设计中固定的目标模块为：Prompt Kernel、Prompt Registry、Context Assembler、Tool Surface Manager、Memory Manager、Compact Manager、Runtime Enforcement、Evidence Ledger。
- 后续实现不应继续只改单个工具描述或单句提示词，应围绕上述 Prompt Architecture 分阶段推进。

## 2026-05-26 Prompt Architecture v1 实施计划事实

- 当前实施计划文件为：`docs/superpowers/plans/2026-05-26-agent-prompt-architecture-v1.md`。
- 计划基于现有事实：`docs/superpowers/specs/claudecode_parity_checklist.md` 已标记公开可复现 agent core parity Phase 1-7 PASS，因此新计划不重复工具架构实现。
- 新计划的核心落点是把当前分散在 `learning_agent.py` helper、`runtime_instructions.md`、`memory.md` 和 `agent_memory` 注入逻辑中的 prompt surface，升级为可注册、可装配、可预算、可报告的 Prompt Architecture v1。
- 计划拟新增 `learning_agent/prompt_registry.py` 和 `learning_agent/context_assembler.py`，并在 `LearningAgent._build_initial_messages()` 中用 Context Assembler 替代直接拼接。
- 计划拟新增只读报告工具 `prompt_surface_report` 和 `token_budget_report`，让用户能直接询问当前每轮自动加载了哪些提示词和上下文。

## 2026-05-26 Prompt Architecture v1 Task 2 当前事实

- Task 2 已新增 `learning_agent/context_assembler.py`，包含 `ContextBlockLoad`、`ContextAssemblyResult`、`PromptSurfaceReport`、`estimate_tokens_from_text()` 和 `ContextAssembler`。
- `ContextAssembler.assemble_static_blocks()` 当前只装配传入 `block_contents` 中存在且非空的 block，并按 `PromptRegistry.blocks` priority 顺序输出 system prompt。
- `LearningAgent` 当前在初始化时创建 `self.prompt_registry = build_default_prompt_registry()`，并设置 `self.last_prompt_surface_report = PromptSurfaceReport.empty()`。
- `LearningAgent._build_initial_messages()` 当前保留已有 helper 文案，把各 helper 输出、runtime instructions、project agent memory 和 long-term memory 映射为 block contents 后交给 ContextAssembler 装配。
- 当前报告只保存进程内 `last_prompt_surface_report`，尚未实现公开只读工具；公开工具属于后续 Task 4 范围。
## 2026-05-26 Prompt Architecture v1 Task 3 当前事实

- `LearningAgent._build_initial_messages()` 现在仍通过 `ContextAssembler` 装配提示词，但项目级 `agent_memory` 与长期 `memory.md` 已改为索引形式进入 system prompt。
- 项目记忆 block 标题包含 `Project Memory Index`，并保留旧识别文本 `Project Agent Memory / 项目级上下文` 以兼容邻近测试和用户审计习惯。
- 长期记忆 block 标题包含 `Long-Term Memory Index`，超长 `memory.md` 不再以重复全文进入 system prompt，而是保留标题、来源元数据和去重后的最新尾部摘要。
- `PromptSurfaceReport.to_text()` 现在会显示 memory index note，至少包含 `stable_fact_count`，方便用户检查本轮自动加载了哪些记忆来源。
## 2026-05-26 Prompt Architecture v1 Task 4 当前事实

- `TOOL_SCHEMAS` 现在新增两个只读内置报告工具：`prompt_surface_report` 和 `token_budget_report`。
- `prompt_surface_report` 支持 `include_block_text`（默认 false）和预留的 `include_evidence`（默认 false），会输出 block id、title、source、load_policy、priority、loaded/status、estimated_tokens 和 note。
- `prompt_surface_report` 默认不输出完整提示词正文，并明确说明历史设计文档/历史计划不会自动加载，除非本轮显式读取。
- `token_budget_report` 支持 `include_tools`（默认 true），会输出 Prompt blocks、`estimated_total_tokens`、Current Tool Pool、工具数量、工具 schema 粗略 token 估算和当前工具池名称。
- `build_builtin_tool_catalog()` 现在让 `tool_search`、`prompt_surface_report`、`token_budget_report` 都作为 always-load 内置工具进入当前工具池。
# 2026-05-26 Prompt Architecture v1 Task 5 当前事实

- 修改代码+PromptArchitectureV1: `ContextAssembler` 已支持 `soft_token_limit`，默认约 60K，并且 `LearningAgent` 会把实例级预算传入装配器；如果没有这条记录，后续任务不知道 compact 预算已进入生产装配路径。
- 修改代码+PromptArchitectureV1: 当装配估算 token 超过软预算时，只允许低优先级、动态、非 `built_in` 且超过自身预算的 block 转换为 `Compact Summary`；摘要保留 block id、title、source、original chars、included chars、reason，并明确 `full_text_loaded=false`；如果没有这条记录，后续任务可能重复引入核心策略被压缩的风险。
- 修改代码+PromptArchitectureV1: `prompt_surface_report(include_evidence=True)` 已桥接 `observation_events`，会输出 Evidence Ledger 和事件分类；如果没有这条记录，后续任务可能仍把 evidence 入口当成占位。

# 2026-05-26 Prompt Architecture v1 完成事实

- 修改代码+PromptArchitectureV1: Prompt Architecture v1 已完成 Phase 1 到 Phase 7，实现范围包括 Prompt Registry、Context Assembler、Memory Index、Prompt Surface Report、Token Budget Report、Compact Summary、Evidence Ledger bridge、文档同步和最终验证；如果没有这条记录，后续任务可能误以为该计划仍停在中间阶段。
- 修改代码+PromptArchitectureV1: `prompt_surface_report` 与 `token_budget_report` 是当前可见的只读审计工具，用来回答“模型本轮看到了什么、为什么加载、预算多少”；如果没有这条记录，后续模型可能继续靠猜测解释 prompt surface。
- 修改代码+PromptArchitectureV1: 历史设计文档、旧计划和学习备份不会自动影响模型，除非当前轮显式读取；如果没有这条记录，后续任务可能把未加载文档当作当前上下文证据。
- 修改代码+PromptArchitectureV1: Phase 7 审查修复后，Prompt compact 的生产路径默认约 60K 软预算，并可通过 `runtime_config.json` 的 `prompt_soft_token_limit` 或环境变量 `LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT` 调整；如果没有这条记录，后续任务可能误以为 compact 仍是不可配置测试能力。
- 修改代码+PromptArchitectureV1: Phase 7 审查修复后，`built_in` 核心策略不会被 compact，只有动态、非 `built_in`、超过自身预算的上下文块会转成 `Compact Summary`；如果没有这条记录，后续任务可能再次引入压缩核心系统规则的风险。

# 2026-05-26 Capability Packs 方案 B 当前事实

- 修改代码+CapabilityPacks: `LearningAgent` 当前首轮默认只暴露 kernel 工具池，包含 `prompt_surface_report`、`token_budget_report`、`tool_search`、`skill_list`、`skill_load`、`ask_user_question`；如果没有这条记录，后续任务可能误以为 read/write/memory 等工具仍应首轮常驻。
- 修改代码+CapabilityPacks: 内置工具已按 capability pack 分类并默认延迟，模型可通过 `tool_search` 的 `select_pack:<pack_name>` 加载 `file_operations`、`memory`、`execution`、`notebook`、`mcp`、`browser_automation`、`real_chrome`、`delegation`、`planning`、`diagnostics`、`long_running_work`、`prompt_architecture`；如果没有这条记录，后续任务可能继续把 47 个工具全部塞回首轮 schema。
- 修改代码+CapabilityPacks: `learning_agent/runtime_instructions.md` 已压缩为短 kernel + skill router，具体流程迁移到 `learning_agent/skills/*/SKILL.md`；如果没有这条记录，后续任务可能把长流程说明重新写回常驻 runtime。
- 修改代码+CapabilityPacks: `ContextAssembler` 的项目记忆索引当前每个 agent_memory 文件限制约 220 字符，以保证首轮 prompt 预算测试稳定低于 1900 tokens；如果没有这条记录，后续扩写记忆摘要可能让方案 B 预算回归。
- 修改代码+RuntimePathFix: `LearningAgent` 现在优先读取工作区根目录 `runtime_instructions.md`，缺失时回退到 `learning_agent/runtime_instructions.md`；如果没有这条记录，后续任务可能误以为项目根目录缺 runtime 时仍应显示缺失占位。
