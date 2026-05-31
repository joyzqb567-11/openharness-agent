# 问题与风险记录

## 2026-05-26 Prompt Architecture v1 Task 6 遗留风险

- Token Budget Report 当前使用粗略 token 估算，不等于真实模型 tokenizer；文档和报告只能作为预算近似值。
- Memory index 默认不读取全文；如果关键事实只在长文件中段，仍需要当前轮显式 read 对应文件。
- 历史设计文档不会自动影响模型；如果任务依赖旧设计，必须在当前轮明确读取并引用。
- Evidence Ledger bridge 当前依赖进程内 observation events 和已落盘工具结果摘要，不等于跨进程、跨会话的完整证据数据库。

## 2026-05-24 Browser Automation MCP 设计风险记录

- 当前已确认边界：第一阶段只启动独立 Playwright Chromium，不连接用户真实 Chrome，不读取真实 Chrome 登录态、cookie、扩展或历史记录。
- 当前依赖风险：bundled Python 当前未安装 `playwright`，实施阶段需要安装 Python `playwright` 包并执行 Chromium 浏览器安装；如果安装失败，浏览器自动化 MCP server 只能返回清晰依赖错误，不能假装可用。
- 当前环境风险：系统 `python` 命令指向 Microsoft Store 占位符，实施阶段应继续使用 Codex bundled Python：`<codex-bundled-python>`。
- 当前环境风险：本机可见 Node 版本为 `v24.14.0`，但 `npx` 当前不可用，因此第一阶段不采用 Node Playwright MCP 路线。
- 当前安全风险：`browser_evaluate` 能读取或修改页面状态，必须作为高风险工具处理；设计要求每次执行经过权限确认、结果截断，并明确不鼓励读取 cookie、localStorage、sessionStorage、token 或密码框内容。
- 当前文件边界：截图、下载和浏览器产物应限制在 `learning_agent/browser_artifacts/`；上传源文件必须限制在允许的工作区路径内。
- 当前无本轮新增已确认 bug；本轮只新增设计文档和 agent_memory 记录，未修改运行时代码。

## 2026-05-24 Prompt / Context Architecture v1 风险记录

- 当前已确认风险：旧提示词长期追加工具说明，容易变成长清单，导致系统身份、上下文优先级和工具选择策略混在一起。
- 当前已确认风险：如果系统提示词仍自称“最小私人 agent”，会和用户目标“升级成成熟 coding agent”冲突，导致后续决策继续偏向最小演示而不是成熟工程行为。
- 当前已确认风险：上下文优先级不清时，旧 memory、runtime rules 或历史建议可能压过用户本轮明确请求。
- 当前已确认风险：运行时规则重写时可能误删既有工具触发词，因此本轮保留并测试 `tool_search`、workspace tools、MCP resources/prompts、auth metadata、task/team、plan/worktree、LSP、REPL、Cron/Monitor 等关键关键词。
- 当前边界：本轮只升级提示词和上下文规则，不解决真实 MCP session lifecycle、真实 git worktree、真实 language server、真实调度器和完整 OAuth UI。
## 2026-05-24 MCP OAuth/auth metadata 风险记录

- 当前已确认边界：`mcp__server__authenticate` 是说明型伪工具，只解释 401、`WWW-Authenticate`、`resource_metadata`、`Authorization: Bearer` 和 `mcp_servers.json` headers 配置方式，不会自动完成 OAuth 登录。
- 当前安全边界：实现刻意不自动请求 `resource_metadata` URL，因为官方安全最佳实践指出 OAuth metadata discovery 可能引入 SSRF 风险；后续若自动请求 metadata，必须先做 HTTPS/localhost 规则、私网地址拦截、重定向限制和用户确认。
- 当前 token 边界：访问令牌只建议通过 `headers.Authorization` 配置；不要把 token 放进 URL 查询参数，不要把 token 填进 `mcp__server__authenticate` 工具参数或日志。
- 当前功能缺口：尚未实现完整 OAuth UI、动态客户端注册、PKCE、资源参数、授权服务器 metadata 获取、token 刷新、GET 监听流、DELETE 会话关闭、断线恢复和 Last-Event-ID。
- 当前测试状态：auth metadata 3 条红灯测试已转绿；语法检查、MCP/auth 10 条专项测试和完整 unittest 均已通过，完整结果为 `Ran 173 tests in 5.857s OK`。

- 当前已确认边界：`list_mcp_prompts` / `read_mcp_prompt` 只是 MCP prompts 的发现和读取入口，不会安装远程 skill、不会把 prompt 自动变成工具、不会自动执行 prompt。
- 当前风险：MCP prompt 内容来自外部 MCP server；读取前已要求权限确认，但后续是否按 prompt 执行仍依赖模型遵循上下文和用户目标，不能把外部 prompt 当成无条件可信指令。
- 当前风险：`prompt_arguments` 只做对象类型校验，不会根据 prompts/list 返回的 arguments 做强 schema 校验；后续如要更严格，需要按 prompt 元数据校验必填参数和类型。
- 当前无本轮新增已确认 bug；语法检查、MCP prompts 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`cron_create` / `cron_list` / `cron_delete` / `monitor` 只是教学版进程内记录工具，不会自动执行任务、不会创建系统定时器、不会跨进程常驻、不会推送通知、不会跨重启持久化。
- 当前风险：Cron/Monitor 记录都保存在当前 `LearningAgent` 实例内存中；重启 agent 后记录会消失，后续若要真实长期任务需要补持久化和权限确认流。
- 当前风险：`monitor action=record_result` 只记录调用方提供的观察结果，不会主动检查目标是否变化；后续若接真实监控，需要明确触发条件、执行权限和停止条件。
- 当前无本轮新增已确认 bug；语法检查、Cron/Monitor 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`repl` 是安全白名单批量编排工具，只执行只读、状态和符号类内置工具；它不是任意代码执行器，不会写文件、运行命令、调用外部 MCP、启动子 agent 或递归调用自身。
- 当前风险：`repl` 复用现有工具文本输出来判断子调用是否失败，主要识别首行里的“失败”、“未知工具”和“用户拒绝”；后续如果工具失败格式变化，需要同步更新 `_repl_child_failed`。
- 当前风险：`repl` 的安全白名单是静态集合；以后新增只读工具时需要明确评估是否加入白名单，避免遗漏可批量查询能力或误加入副作用工具。
- 当前无本轮新增已确认 bug；语法检查、REPL 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`lsp_symbols` / `lsp_definition` / `lsp_diagnostics` 是 Python 标准库 `ast` 实现的 LSP 最小版，只支持 `.py` 文件，不启动真实 language server，不做跨文件索引、类型检查或自动补全。
- 当前风险：语法错误文件中 `lsp_symbols` / `lsp_definition` 会返回解析失败；应先用 `lsp_diagnostics` 定位并修复 SyntaxError，再重试符号或定义查询。
- 当前无本轮新增已确认 bug；语法检查、LSP 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`enter_worktree` / `exit_worktree` 只记录轻量隔离状态，不创建真实 git worktree、不创建目录、不执行命令、不移动文件。
- 当前风险：`worktree_path` 只是状态提示，后续工具不会自动切换 cwd 或强制把写入限制到该目录；真实隔离仍需后续接入 git worktree 或工作区切换机制。
- 当前无本轮新增已确认 bug；语法检查、WorktreeIsolation 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`verify_plan_execution` 只做计划执行结果的结构化审计输出，不会自动执行测试、命令、文件写入或权限拦截。
- 当前风险：`status=verified` 依赖调用方提供的 `executed_steps` 和 `evidence`；它是审计摘要，不等于无需真实运行测试或人工复核。
- 当前无本轮新增已确认 bug；语法检查、PlanVerification 专项测试和完整 unittest 均已通过。
- 当前已确认边界：`team_start_task` 会复用当前进程内的后台 `task` 并把 `task_id` 绑定到 peer；它不是跨进程持久化 worker，也不会让 peer 独立于当前 LearningAgent 实例长期存在。
- 当前风险：如果删除已绑定 task 的 peer，当前最小版只删除 peer 记录，不自动停止后台 task；仍需使用 `task_stop` 管理后台任务。
- 当前已确认边界：`read_peer_messages` / `ack_peer_message` / `team_delete` 仍然只是当前进程内教学版工具；读取和确认消息不会触发真实 agent 执行，删除 peer 只删除内存记录和 inbox。
- 当前风险：`team_delete` 会丢弃 peer 的进程内 inbox，因此工具层要求 `confirm_delete=true`；已用测试覆盖缺少确认时拒绝删除。
- 当前无本轮新增已确认 bug；team 生命周期专项测试和完整 unittest 均已通过。
- 当前已确认边界：`team_create` / `send_message` / `list_peers` 是教学版进程内记录，不是真实并行 agent；已在 runtime instructions、README、差距矩阵和学习备份中说明，避免模型或用户误以为 peer 会自动处理消息。
- 当前无本轮新增已确认 bug；语法检查、team 通信专项测试和完整 unittest 均已通过。
- 当前无已确认 bug。
- 风险：用户要求的是用户级 skill，目标目录应使用 Codex 可自动发现的 `<codex-skills-dir>`，而不是项目内局部目录。
- 已处理：系统 `python` 命令指向 Microsoft Store 占位符，导致初始化脚本无法运行；已改用 Codex bundled Python：`<codex-bundled-python>`。
- 已处理：`quick_validate.py` 依赖 `yaml` 模块，bundled Python 未内置该模块；已将 `PyYAML` 安装到临时目录并通过 `PYTHONPATH` 仅用于本次校验。
- 验证边界：`writing-skills` 建议用子代理压力测试 skill；本任务没有要求实际启动子代理，且当前目标是配置固定内容，因此以本地结构校验为主。
- 已处理：完整测试时旧测试 `test_mcp_stdio_client_times_out_when_server_does_not_respond` 在 Windows 上偶发/稳定卡在 `initialize` 阶段超时；已确认根因是 `request_timeout_seconds=0.2` 太贴近 Python 子进程启动边界，已调整为 `0.5`，仍能验证 `tools/list` 不响应时的超时保护。
## 2026-05-24 Browser Automation MCP 第一阶段剩余风险

- 依赖边界：`browser_automation` 依赖 Python `playwright` 包和 Chromium 浏览器内核；缺少依赖时需要先运行 `python -m pip install playwright` 和 `python -m playwright install chromium`，不能假装浏览器可用。
- 登录态边界：第一阶段只使用独立 Playwright Chromium，不连接用户真实 Chrome，不继承真实 Chrome 登录态、cookie、扩展或历史记录；真实 Chrome 登录态仍未实现。
- JavaScript 风险：`browser_evaluate` 能读取或修改页面状态，必须继续作为高风险工具处理；默认避免读取 cookie、localStorage、sessionStorage、token、密码框内容或类似敏感数据，除非用户明确要求并清楚展示权限提示。
- Artifact 风险：截图、下载和浏览器运行产物应保留在 `learning_agent/browser_artifacts/` 或 `browser_artifacts/`；后续需要关注 artifact 清理策略，避免产物长期堆积或被误提交。
- 提交边界：`.gitignore` 已忽略 `learning_agent/browser_artifacts/` 和根目录 `browser_artifacts/`；后续如果新增其他浏览器产物目录，也需要同步忽略，避免截图或下载内容进入版本库。
- CLI 边界：当前 MCP Doctor 入口是 `learning_agent.py mcp-doctor` 或 `learning_agent.py doctor`，不是 `--mcp-doctor` 参数；后续文档或计划引用 doctor 时应使用当前真实 CLI 写法。

## 2026-05-24 MCP transport 风险记录

- 旧 `transport=sse` 当前不是完整支持，只是明确识别并报错；若用户必须连接 2024-11-05 旧 HTTP+SSE server，还需要后续实现 GET SSE endpoint + message POST endpoint 的兼容逻辑。
- `McpHttpClient` 当前覆盖 Streamable HTTP 的 JSON POST 主路径，并能解析简单 `text/event-stream` data 响应；尚未实现 GET 监听流、DELETE 会话关闭、断线恢复、Last-Event-ID、server-to-client requests、OAuth/auth metadata。
- HTTP header `headers` 直接来自 `mcp_servers.json`，适合本地学习版；后续若保存真实 token，应避免把敏感 header 提交到仓库。
- 本轮已完成完整 unittest：`Ran 170 tests in 5.781s OK`；当前剩余风险集中在未实现的 OAuth/auth、GET 监听流、DELETE 会话关闭和旧 SSE 双端点兼容。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 设计风险记录

- 当前协议风险：官方 MCP `2025-11-25` 稳定规范仍包含 `MCP-Session-Id`、GET SSE 监听、`Last-Event-ID` 恢复和 DELETE 会话关闭；但官方 draft changelog 已提出未来移除 protocol-level sessions、`MCP-Session-Id` 和 GET endpoint，因此本阶段设计必须把这些能力封装在 HTTP transport 内部，避免扩散到公开 agent 语义。
- 当前工程风险：如果直接做后台常驻 stream listener，会引入线程生命周期、取消、事件缓存、上下文注入和测试稳定性问题；设计已选择 bounded listen，先不做永久后台监听。
- 当前兼容风险：现有 `McpHttpClient` 默认协议版本仍偏向 `2025-06-18`，设计阶段已记录后续实施需要明确与 `2025-11-25` 的协商和回退策略。
- 当前安全边界：本设计不自动访问不可信 `resource_metadata` URL，不实现 OAuth 登录 UI，不把 Authorization token 写入日志，也不把 server notification 自动塞进模型上下文。
- 当前无本轮新增已确认 bug；本轮只新增设计文档和 agent_memory 记录，未修改运行时代码。

## 2026-05-24 MCP HTTP session/stream lifecycle v1 实施风险记录

- 当前已确认边界：`listen_mcp_stream` 是有界同步读取工具，不是永久后台 listener，不会自动把所有 server notification 注入模型上下文。
- 当前已确认边界：旧 `transport=sse` / HTTP+SSE 双端点仍未实现；当前建议继续优先使用 `transport=http` 的 Streamable HTTP endpoint。
- 当前已确认边界：本轮只实现 session/stream lifecycle v1，不实现完整 server-to-client capabilities、`tools/list_changed` 自动刷新、server requests、完整 OAuth UI、动态客户端注册或 PKCE。
- 当前协议风险：官方 draft changelog 已记录未来可能移除 protocol-level sessions、`MCP-Session-Id` 和 GET endpoint；本轮已把 session/stream 逻辑封装在 HTTP transport 内，后续迁移时应优先改 transport 层。
- 当前已处理 bug：`listen_mcp_stream` wrapper 曾在 `max_events=float("inf")` 时抛裸 `OverflowError`；已新增 `test_listen_mcp_stream_falls_back_for_non_finite_limits` 并捕获 `OverflowError` 回退默认 `5`。
- 当前已处理边界：`timeout_seconds=float("nan")` / 正负无穷会回退默认 `2.0`，避免非有限值流入 registry 或底层 HTTP 超时。
- 当前验证状态：最终 `py_compile`、11 条 MCP HTTP lifecycle 聚焦测试和完整 `learning_agent.test_learning_agent` 均已通过；完整 unittest 结果为 `Ran 188 tests in 9.512s OK`。

## 2026-05-25 Real Chrome profile automation risk notes

- 真实 Chrome 模式必须保持显式确认，不得默认启用。
- Chrome 正在运行时第一版必须阻断，不抢占日常 profile。
- `browser_evaluate` 在真实 Chrome 模式默认拒绝 cookie、storage、token、password、Authorization 等敏感读取。
- 调试端口只能绑定 `127.0.0.1`。
- `browser_disconnect_real_chrome` 默认不关闭用户 Chrome；只有明确 `close_browser=true` 且进程由 agent 启动时才允许结束进程。
- `browser_profile_status` 只读模式、连接状态、页面数量和最近安全拒绝，不读取真实 profile 敏感数据。
- 验证记录中的本机用户目录已用 `<codex-bundled-python>`、`<codex-skills-dir>` 和 `<user-home>` 这类占位符脱敏，避免把个人路径写进长期上下文。

## 2026-05-25 Codex OAuth 过期恢复与 timeout 边界

- 已确认并修复：`CodexOAuthChatModel` 旧逻辑在 refresh token 被拒绝时不会自动重新网页登录，只会把异常变成 `Codex OAuth/API 调用失败`。
- 已确认并修复：Codex API 返回 `401/403` 这类运行中鉴权失败时，旧逻辑不会重新登录，也不会重试本轮请求。
- 已确认边界：`The read operation timed out` 是响应读取超时信号，不是 OAuth 过期的 100% 证据；修复后不会因 timeout 自动弹网页登录，避免把网络/API 慢响应误判为登录过期。
- 当前残余风险：鉴权失败识别基于标准库 HTTPError 转出的状态码和错误文本，例如 `invalid_grant`、`401/403`、`unauthorized`、`forbidden`、`invalid_token`；如果 OpenAI 后端未来改变错误格式，可能需要同步更新 marker。
- 验证状态：OAuth 聚焦测试和完整 `learning_agent.test_learning_agent` 均已通过，完整结果为 `Ran 231 tests in 23.916s OK (skipped=1)`。

## 2026-05-25 Codex response_format strict schema bug

- 已确认并修复：`Codex OAuth/API 调用失败：HTTP 400 invalid_json_schema` 的根因是输出 schema 中 `tool_calls[].arguments.todos.items.required` 没有覆盖 `properties` 的全部键，缺少 `id` 和 `priority`。
- 已确认边界：该错误发生在 Codex 后端校验 `text.format.schema` 阶段，请求尚未进入模型推理；它不是 OAuth 登录过期，也不是模型回答错。
- 已处理：`_nullable_argument_schema()` 现在会先调用 `_strict_response_format_schema()`，递归修正嵌套对象 schema，避免 `todos.items` 这类数组对象再次缺 required。
- 当前残余风险：如果未来新增工具参数里包含更复杂的 JSON Schema 组合关键字，例如 `anyOf`、`oneOf` 或自由对象映射，仍需要补充 strict schema 兼容测试。
- 验证状态：本地 schema 扫描 `problems 0`；完整 `learning_agent.test_learning_agent` 通过，完整结果为 `Ran 232 tests in 24.951s OK (skipped=1)`。

## 2026-05-25 Codex strict schema open object bug

- 已确认并修复：新截图中的 `prompt_arguments ... additionalProperties is required to be supplied and to be false` 是开放对象 schema 被 Codex strict response_format 拒绝。
- 已确认同类风险：`repl.calls[].arguments` 也曾是 `additionalProperties=true` 的开放对象，如果不一起修，可能成为下一次 `HTTP 400 invalid_json_schema`。
- 已处理：`_strict_response_format_schema()` 现在会把没有固定 properties 的 object 改成空对象 strict schema，显式设置 `properties={}`、`required=[]`、`additionalProperties=false`。
- 当前残余风险：这种保守修复会让模型结构化输出暂时不能自由生成任意 `prompt_arguments` 或 `repl.calls[].arguments` 键；后续若要完整支持，需要设计新的参数编码或按具体工具动态生成专用 schema。
- 验证状态：本地 schema 扫描 `problems 0`；完整 `learning_agent.test_learning_agent` 通过，完整结果为 `Ran 233 tests in 25.767s OK (skipped=1)`。

## 2026-05-25 Codex OAuth SSE stream read hang bug

- 已确认并修复：用户请求真实浏览器查天气后界面停住，根因不是 browser_automation MCP，而是模型首轮 `model_request` 后没有返回 `model_response`。
- 已确认根因：`CodexOAuthChatModel._post_json_request()` 在 Codex Responses `stream=true` 时调用 `response.read()`，这会等待整个 SSE 连接结束；如果后端保持流连接，agent 会在任何工具调用前卡住。
- 已处理：新增 `_read_sse_response_until_done()`，按行读取 SSE，遇到 `response.output_text.done`、`response.completed` 或 `[DONE]` 后立即解析返回，避免等待 EOF。
- 当前残余风险：如果后端既不发送 done/completed/[DONE]，也不关闭连接，仍会依赖 urllib 的 socket timeout；这类情况应继续显示“响应读取超时”，不能直接判断为 OAuth 过期。
- 当前观察项：完整 unittest 第一次出现一次 `test_browser_automation_mcp_server_operates_local_page` 的 browser_automation stdio 超时；该测试单独重跑通过，第二次全量也通过，暂记为浏览器启动抖动而非本次 OAuth 流读取修复引入的确定回归。
- 验证状态：新增回归测试先红后绿；OAuth/strict schema 聚焦 9 条测试通过；`py_compile` 通过；最新完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 234 tests in 22.403s OK (skipped=1)`。

## 2026-05-25 browser_open 参数串味与工具后模型 timeout

- 已确认：用户截图里 `mcp__browser_automation__browser_open` 的授权提示包含 `status`、`state`、`action`、`result_status`、`confirm_real_profile`，这些字段不属于 `browser_open` schema；它们来自模型输出协议里其他工具参数名混入，不是 browser_automation server 要求这些参数。
- 已确认：debug 日志中 `browser_open` 两次都返回了工具结果，第二次 Bing 搜索页成功打开；因此“真实浏览器自动化工具卡住”这一轮的确定根因不是 browser_open 不返回。
- 已确认：真正失败发生在工具结果返回后的下一次 Codex OAuth/API 模型调用，报 `The read operation timed out`；这仍不是 OAuth 过期的 100% 证据，也不应自动弹网页登录。
- 已处理：MCP registry 现在缓存每个工具的参数 schema，并在授权提示和真实调用前按 `properties` 清洗未声明字段，避免 `browser_open` 收到或展示串味参数。
- 已处理：`browser_automation` stdio client 工厂超时提升到 `35.0` 秒，覆盖浏览器工具自身 `30000ms` 页面等待，避免外层 5 秒超时误伤慢页面。
- 已处理：Codex OAuth/API read timeout 会用同一 token 自动重试一次；只有明确 `401/403` 等鉴权失败才触发网页登录。
- 当前残余风险：当前输出协议仍是“所有工具参数聚合到一个严格 JSON schema”，模型仍可能生成其他工具字段；本次在执行层做了清洗兜底，后续若要根治可设计每个 `tool_call.arguments` 按工具名分支的输出协议。
- 验证状态：新增 4 条测试均先红后绿；`py_compile` 通过；完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 238 tests in 24.580s OK (skipped=1)`。

## 2026-05-25 Codex OAuth/API 远端断连 bug

- 已确认：用户最新截图里的 `Remote end closed connection without response` 发生在第 0 轮 Codex OAuth/API 模型调用阶段，日志中没有任何 `tool_calls`，因此这一次不是 `browser_automation` MCP 工具本身卡住或报错。
- 已确认根因边界：该错误表示 Codex 后端或中间网络在返回响应前关闭了 HTTP 连接；它不等于 OAuth 登录过期，也不应该自动弹出网页登录。
- 已确认旧缺陷：旧逻辑只把 `timed out` 当成临时 API 错误自动重试一次，没有覆盖 `RemoteDisconnected` / `Remote end closed connection without response`，所以用户会直接看到英文底层错误。
- 已处理：`CodexOAuthChatModel.chat()` 现在通过 `_is_transient_api_error()` 同时识别 timeout 与远端断连，并用同一 token 自动重试一次；只有明确 `401/403`、`invalid_token` 等鉴权失败才触发网页登录。
- 已处理：连续远端断连时，错误文案会显示“远端连接关闭”，并明确说明这通常是临时网络/API 连接问题，不一定是 OAuth 登录过期。
- 已处理：直接构造 `McpStdioClient(browser_automation)` 时也会默认使用 `35.0` 秒请求超时，避免绕过 registry 工厂后退回 5 秒造成浏览器测试抖动。
- 当前残余风险：如果自动重试后仍然远端断连，剩余原因更可能是外部网络、代理、TLS 中间层或 Codex 后端临时断开；本地 agent 能给出清晰提示，但不能保证外部连接一定恢复。
- 验证状态：OAuth 远端断连聚焦测试、README 边界测试、browser_automation timeout 聚焦测试、`py_compile`、完整 `learning_agent.test_learning_agent` 和 `git diff --check` 均已通过；完整 unittest 结果为 `Ran 241 tests in 20.177s OK (skipped=1)`。

## 2026-05-25 Tool Architecture v2 架构风险

- 已确认：当前工具调用顶层结构未完全对齐 ClaudeCode；现有 `tool_search` 不是 deferred tool loading，而只是搜索当前可见工具。
- 已确认：当前输出协议仍有“所有工具参数聚合到一个 strict JSON schema”的结构性风险；执行层参数清洗只能兜底，不能从根上减少模型误生成其他工具字段。
- 已确认：如果继续只补单个工具或提示词，真实 Chrome、独立 Chromium、网页搜索、workspace MCP 等能力仍可能被模型混用。
- 已确认：v2 实施前必须先设计并确认 `AgentTool`、`ToolCatalog`、`ToolPool`、ToolSearch v2、skill gate 和输出协议重构，否则容易继续堆叠局部补丁。
- 当前缓解：已创建设计文档 `docs/superpowers/specs/2026-05-25-tool-architecture-v2-claudecode-codex-alignment-design.md`，并把“至少对齐 ClaudeCode 后再谈超越”写入设计目标。
- 当前剩余风险：设计尚未进入实施计划和代码修改，运行时仍保持旧工具架构。

## 2026-05-25 Tool Architecture v2 core spine 剩余风险

- 已处理：`tool_search` 已从“只搜当前可见工具”升级为搜索完整 Tool Catalog，并支持 `select:<tool_name>` 加载 deferred 工具。
- 已处理：MCP 工具默认 deferred，未加载时不会进入首轮 Tool Pool；直接调用未加载 deferred 工具会被执行门禁拒绝。
- 已处理：输出 schema 已从“所有已发现 MCP 工具参数都可能混入”收窄为“当前 Tool Pool 的工具参数”，未加载的真实 Chrome 或其他 MCP 参数不会默认进入输出 schema。
- 当前剩余风险：输出 schema 仍是当前 Tool Pool 内参数的合并对象，不是按 `tool_call.name` 精确分支的 per-tool schema；如果同一 Tool Pool 内多个工具参数重名，后续仍需要更严格的 discriminated/oneOf 风格输出协议。
- 当前剩余风险：真实 Chrome workflow/skill gate 还未实现；本阶段只提供 `skill_gate`、`workflow_gate` 这类元数据挂点，尚未强制真实 Chrome 请求先走 profile 状态检查和真实 Chrome 专用工作流。
- 当前剩余风险：MCP tool annotations 尚未完整映射到 `readOnly/destructive/openWorld/search` 风险策略；当前仍主要靠现有风险摘要和工具名分类。
- 当前剩余风险：MCP `tools/list_changed`、server notifications 和 catalog 自动刷新尚未实现；外部 server 动态变化后仍需要后续补刷新机制。
- 当前验证：完整 `learning_agent.test_learning_agent` 通过，结果为 `Ran 252 tests in 20.823s OK (skipped=1)`。

## 2026-05-25 ClaudeCode 完全追平风险记录

- 风险：如果把“完全追平 ClaudeCode”理解成一次性复制所有工具名，会继续造成假追平；真实差距在 Tool Policy、permissions、MCP lifecycle、skills/workflow、真实 Chrome workflow、输出协议和 observation。
- 风险：ClaudeCode 含有私有产品能力和内部工具，不能把这些全部列为 P0；否则 scope 会失控，且与 learning_agent 当前教学/演进目标不匹配。
- 风险：当前 v2 core spine 还没有完整读取 MCP annotations、`anthropic/searchHint`、`anthropic/alwaysLoad`，也没有 `tools/list_changed` 自动刷新；这些是 Phase 1 和 Phase 3 的关键缺口。
- 风险：真实 Chrome workflow 尚未强制 skill/workflow gate；当前仍不能声称真实浏览器能力已完全追平 ClaudeCode。
- 当前缓解：已创建 `docs/superpowers/specs/2026-05-25-claudecode-agent-core-parity-master-design.md`，将 parity 拆成 P0/P1/P2 和 Phase 0-7，下一步先做 Phase 1 `Tool Policy / Permission v2`。

## 2026-05-25 Tool Policy / Permission v2 计划风险

- 风险：Phase 1 会新增策略层，但还不会彻底解决统一大 `arguments` schema 的同池参数串味；per-tool output protocol 留到 Phase 2。
- 风险：Phase 1 会识别 skill/workflow gate，但不会完成真实 Chrome workflow 本身；真实 Chrome 强流程留到 Phase 4。
- 风险：Phase 1 会读取 MCP metadata，但不会实现 `tools/list_changed` 动态刷新；MCP lifecycle parity 留到 Phase 3。
- 当前缓解：计划文件已明确阶段边界，避免把 Phase 1 扩大成多个大系统同时修改。
## 2026-05-25 ToolPolicyV2 Task 1 风险记录

- 当前任务只新增核心策略对象和单元测试，不把策略接入 `LearningAgent` 工具池或执行层；因此测试通过不代表 deny/skill/workflow 已在真实运行时生效，后续 Task 才能完成端到端门禁。
- 仓库当前已有其他 agent 的未提交修改，本任务不会 revert、reset、checkout、stage 或 commit，只在必要文件上做增量编辑。
- `learning_agent/test_learning_agent.py` 已有大量中文逐行注释，本任务新增测试行必须继续使用 `新增代码+ToolPolicyV2` 前缀，避免破坏用户学习约定。

## 2026-05-25 ToolPolicyV2 Task 2 风险记录

- 当前任务只完成 MCP 元数据到 `AgentTool` 的保存和映射，不代表 deny、skill gate、workflow gate 已在真实工具池、搜索选择或执行前生效。
- `strict` 只读取 `_meta["strict"]`、`_meta["anthropic/strict"]` 或工具对象顶层 `strict` 这类合理标记；没有标记时保持默认 `False`，避免过度设计。
- `anthropic/alwaysLoad=True` 当前只体现在 `AgentTool.always_load` 元数据上；首轮工具池是否真正加载仍取决于后续 Task 的策略集成。

## 2026-05-25 ToolPolicyV2 Task 3 风险记录

- 本任务只把 ToolPolicy 接入工具池和 tool_search/select；直接执行工具前的统一 policy guard 属于后续 Task 4，本任务不得提前实现。
- blocked/needs_skill/needs_workflow 工具需要能被 tool_search 发现并解释原因，但不能给出 `select:` 可直接加载的误导提示。
- 仓库有多 agent 并行工作风险，本任务不执行 revert、reset、checkout、stage 或 commit，只做增量修改并验证指定测试。

## 2026-05-25 ToolPolicyV2 Task 3 With fixes 风险记录

- 同一批 `tool_calls` 内 select 立即生效会让模型在尚未收到下一轮 tools schema 前调用 deferred MCP 工具；这是工具池语义风险，不是权限拒绝审计问题。
- 修复必须保留普通 `_execute_tool()` 直接 select 的即时行为，否则已有单元测试和手动调试会变麻烦。
- `run()` 若只在 while 前计算一次 tools，select 后下一轮模型仍看不到新工具；修复时要避免只解决执行绕过却忘记 schema 刷新。

## 2026-05-25 ToolPolicyV2 Task 4 风险记录

- 已确认旧风险：执行层在 Task 4 前只先检查未加载 deferred 工具，`deny_rules` 导致的 `blocked` 状态没有在具体工具分发前硬拦截；这会让被策略拒绝的 MCP 工具可能继续走到权限询问或旧 guard。
- 已确认旧风险：MCP 工具权限被用户拒绝后没有记忆，同一工具和同一清洗后参数第二次仍会再次 `ask_permission`，用户会被重复打扰。
- 已处理：执行层现在先对 catalog 命中的工具读取 ToolPolicy decision，非 deferred 且 `executable == False` 时直接返回 `policy 阻断`。
- 已处理：MCP 权限拒绝现在按工具名和清洗后参数 JSON 写入进程内 `permission_denials`，重复请求直接返回“之前已被用户拒绝”。
- 当前剩余风险：拒绝记忆只保存在当前 `LearningAgent` 实例内，进程重启或新 agent 实例不会继承；持久化或子 agent 继承属于后续任务范围。
- 当前边界：本任务未实现 Task 5 子 agent 继承，未修改真实 Chrome gating，也未更新 docs。

## 2026-05-26 ToolPolicyV2 Task 4 With fixes 风险记录

- 已确认测试覆盖缺口：旧测试只证明同一工具加同一清洗后参数不会重复弹窗，无法防止 `_tool_denial_key()` 将来退化成只按工具名去重。
- 风险影响：如果拒绝 key 只按工具名记录，用户拒绝 `text=deny` 后，后续 `text=different` 这类不同参数的合法请求也会被误拒，且旧测试可能仍通过。
- 已处理：新增 `test_permission_denial_allows_different_arguments_to_request_again`，要求不同清洗后参数必须重新 `ask_permission`，并在允许后真实调用 fake MCP client。
- 当前边界：本次只补覆盖缺口，生产实现本身已经按工具名和清洗后参数 JSON 区分，因此没有修改 `_tool_denial_key()`。

## 2026-05-26 ToolPolicyV2 Task 5 风险记录

- 已确认旧风险：`_task()` 创建子 agent 后只继承 `loaded_tool_names`，没有继承父 agent 的 ToolPolicy context；这会让子任务缺少父 agent 的 allow/deny/skill/workflow 策略上下文。
- 测试注意点：父侧 deny 会让 `_task_allowed_tool_names()` 先把 `allowed_tools` 收缩为空，因此只看 task 输出或模型工具池不足以证明子 agent 继承了 deny rule；本次测试额外捕获真实 child agent 并检查其 `tool_policy_context.deny_rules`。
- 已处理：子 agent 构造后复制 `allow_rules`、`deny_rules`、`loaded_skills`、`completed_workflows`，并保留既有 `loaded_tool_names` 继承逻辑。
- 当前边界：本任务未继承 `permission_denials`，未改真实 Chrome gating，未做 Task 6 文档和 full verification。

## 2026-05-26 ToolPolicyV2 Task 5 With fixes 风险记录

- 已确认旧风险：`_task_allowed_tool_names()` 用父 agent 当前 visible schema 校验显式 `allowed_tools`，导致父侧 deny 后 `mcp__demo__echo` 被提前收缩为空，测试无法证明 child policy deny 真正生效。
- 风险影响：显式请求允许某个完整 catalog 中存在且父 agent 已加载的 deferred MCP 工具时，子 agent 可能拿不到 `allowed_tool_names` 和 `loaded_tool_names`，从而把“父侧提前过滤”误认为“子侧策略过滤”。
- 已处理：省略 `allowed_tools` 时仍沿用父当前 visible 工具池；显式传入 `allowed_tools` 时改用完整 catalog 工具名和父 `loaded_tool_names` 并集做存在性边界。
- 已处理：测试现在同时断言子 agent 继承 `deny_rules`、继承 `loaded_tool_names`、但 `_available_tool_schemas()` 不暴露被 deny 的 MCP 工具。
- 当前边界：显式 `allowed_tools` 仍不会让未 loaded 的 deferred 工具直接可见；它只是允许名称通过合法性过滤，是否进入模型工具池仍由 child 的 `loaded_tool_names` 和 ToolPolicy 决策控制。

## 2026-05-26 ToolPolicyV2 Phase 1 收口剩余风险

- 已完成：Phase 1 ToolPolicy/Permission v2 已覆盖 metadata、deny、skill/workflow gate、select policy、执行 guard、拒绝记忆和子 agent policy 继承，并通过指定聚焦测试与 full suite。
- 当前剩余风险：用户拒绝记忆仍保存在当前 `LearningAgent` 进程内，不持久化到磁盘；进程重启、新 agent 实例或跨会话不会自动继承这些拒绝记录。
- 当前剩余风险：MCP `tools/list_changed`、server notifications 和 catalog 自动刷新仍未实现；外部 MCP server 动态新增、删除或修改工具后，仍需要后续阶段补刷新机制。
- 当前剩余风险：真实 Chrome workflow 仍未作为完整产品流程实现；本阶段只提供并记录 skill/workflow gate 的策略约束，不改真实 Chrome gating。
- 当前剩余风险：输出协议仍不是 per-tool output protocol；同一 Tool Pool 内工具参数仍可能需要后续通过更严格的按工具名分支 schema 收口。

## 2026-05-26 ToolPolicyV2 Final Review 风险与处理

- 已确认旧风险：`allowed_tools` 只过滤 `_available_tool_schemas()`，没有在 `_execute_tool()` 执行入口硬拦截；模型如果伪造隐藏工具名，理论上仍可能触发白名单外工具。
- 已处理：`_execute_tool()` 现在先检查 `self.allowed_tool_names`，白名单外工具直接返回失败，不进入 policy、权限弹窗或具体工具分发；新增 `test_allowed_tools_execution_guard_blocks_hidden_tool_call` 覆盖文件副作用和权限请求都不能发生。
- 已确认旧风险：`search_hint` 与 `aliases` 虽然存进 `AgentTool`，但旧 `_tool_search_score()` 没读取它们，导致 MCP server 提供的搜索线索对发现工具没有作用。
- 已处理：`_tool_search_score()` 现在把 alias 命中按 5 分、searchHint 命中按 4 分计入排序；新增 searchHint 和 aliases 两条召回测试。
- 已确认旧风险：README 和设计中提到兼容 `alwaysLoad`，但代码只读 `anthropic/alwaysLoad`。
- 已处理：MCP `_meta` 现在支持普通 `alwaysLoad` 与 `searchHint` fallback；新增兼容字段测试。
- 已确认旧风险：`allow_rules` 字段被继承但没有参与 `ToolPolicy.decide()`，属于“看起来有白名单，实际没白名单”的结构风险。
- 已处理：非空 `allow_rules` 现在要求工具命中至少一条允许规则，否则返回 `blocked`；新增 allow_rules 白名单测试。

## 2026-05-26 Phase 2 per-tool output protocol 风险与处理

- 已确认旧风险：即使 Phase 1 已把未加载 deferred 工具参数排除在当前 Tool Pool 外，当前 Tool Pool 内仍曾使用共享 `tool_calls[].arguments` 大对象，导致同池工具参数仍可能串味。
- 已处理：输出 schema 已改为 per-tool `anyOf` 分支，每个分支把单个 `name.enum` 和该工具自己的 strict `arguments` schema 绑定，不再让同一 Tool Pool 内工具共享参数对象。
- 已处理：`browser_open` 与 `browser_connect_real_chrome` 的同池隔离已有回归测试，`browser_open` 分支不包含 `confirm_real_profile`，真实 Chrome 分支也不继承 `url`。
- 已处理：第一次 full suite 暴露的旧共享路径测试已经迁移，避免测试继续鼓励“所有参数合成一个对象”的旧结构。
- 已处理：OAuth/API prompt 残留的旧“无关参数写 null”指令已清理，并用测试断言防止新旧提示词再次冲突。
- 当前剩余风险：MCP `tools/list_changed` / server notifications 仍未实现，外部 server 动态变化后 catalog 刷新仍属于 Phase 3。
- 当前剩余风险：真实 Chrome workflow 仍未强制成完整高风险流程；Phase 2 只解决输出参数分支，不等价于真实 Chrome 产品流程已完全追平。
- 当前剩余风险：如果未来工具参数 schema 引入更复杂的 `oneOf`、嵌套开放对象或自由 key-value 映射，还需要继续扩展 strict schema 编码策略；本次已覆盖当前工具集和 `anyOf` 分支对象。

## 2026-05-26 Phase 3 MCP Lifecycle Parity 风险与处理

- 已确认旧风险：MCP 工具目录以前只在 registry start 时读取一次；如果外部 MCP server 后续发出 `tools/list_changed` 并新增、删除或修改工具，ToolSearch 和 Tool Pool 仍可能继续使用旧 catalog。
- 已处理：stdio client 现在会缓存无 `id` 的 JSON-RPC notification，HTTP SSE client 也会把 `data:` 中的 JSON-RPC notification 放入 pending 队列，避免 notification 在传输层被解析后丢弃。
- 已处理：registry 现在通过 `refresh_from_notifications()` 统一 drain notification，并在 `tools/list_changed` 时重跑 tools/list，刷新 schema、routes 和 metadata。
- 已处理：LearningAgent 读取 Tool Catalog 前会先消费 MCP lifecycle notifications；当 tools 真的刷新后，会清空 `_tool_catalog_cache`，避免 ToolSearch 继续返回旧 MCP 工具。
- 已处理：`prompts/list_changed` 和 `resources/list_changed` 虽然当前还没有完整 MCP skills 合并实现，但已经进入生命周期审计，并通过 `mcp_skill_refresh_version` 留出技能搜索索引失效挂点。
- 当前剩余风险：本阶段没有实现永久后台 listener；如果没有任何后续工具查询或显式 refresh 入口，pending notification 不会主动唤醒一个长期运行任务。
- 当前剩余风险：call progress、完整 OAuth UI、动态客户端注册、PKCE、长期 stream 恢复和 ClaudeCode 私有 channel 能力仍不在本阶段范围内。
- 当前剩余风险：Phase 4 真实 Chrome workflow / skill gate 还未完成；Phase 3 只解决 MCP 生命周期刷新，不等价于真实桌面 Chrome 行为已经完全追平。

## 2026-05-26 ClaudeCode Core Parity Phase 4-7 风险与处理

- 已确认旧风险：用户明确要求“真实浏览器/真实 Chrome”时，模型仍可能默认选择 `browser_open` 并启动独立 Chromium；这不是单个工具 bug，而是缺少真实 Chrome workflow gate 的顶层结构问题。
- 已处理：真实浏览器意图现在由 `_detect_real_chrome_intent()` 识别；连接成功前，独立浏览器动作会被 `_real_chrome_request_blocks_independent_browser()` 判为 `needs_workflow`。
- 已处理：`browser_profile_status` 被强制 always-load；`browser_connect_real_chrome` / `browser_disconnect_real_chrome` 会带 `real_chrome` skill gate 和 `real_chrome_profile_ready` workflow gate。
- 已确认旧风险：MCP 工具调用只有最终文本，缺少 permission/start/completed/failed 结构化进度，用户无法审计工具到底是否执行过。
- 已处理：`_record_mcp_call_progress()` 会记录 MCP 进度并同步到 `observation_events`。
- 已确认旧风险：Plan mode 以前主要依赖模型自觉“不要执行”，没有执行层硬拦截；模型可能输出计划后直接写文件或跑命令。
- 已处理：`_plan_mode_blocks_tool_call()` 在执行分发前阻断未确认计划期间的副作用工具；自然语言确认会写入 `plan_confirmed` observation。
- 已确认旧风险：Worktree 工具如果只说“进入隔离状态”，容易让模型误以为已经创建真实 git worktree。
- 已处理：Worktree 进入/退出都记录并输出 `mode=state_only_fallback` 和 fallback reason。
- 已确认旧风险：长文件、日志或网页结果直接回填模型上下文会造成上下文膨胀、截断和后续推理不稳定。
- 已处理：长工具结果会保存到 `learning_agent/debug_logs/tool_results/`，上下文只回填摘要和完整路径。
- 当前剩余风险：真实 Chrome workflow 仍依赖 MCP server 的可用性和用户确认，不能保证桌面一定已打开可见 Chrome；连接失败时必须以工具结果为准。
- 当前剩余风险：Worktree 仍只是状态型 fallback，不创建真实 git worktree；后续若要完全等价 ClaudeCode，需要实现真实 git worktree 创建、切换、清理和失败回滚。
- 当前剩余风险：Observation 当前保存在进程内列表和 debug/tool result 文件中，还不是跨进程可恢复的完整事件数据库。
- 当前剩余风险：Phase 7 parity 只覆盖公开可复现 agent core，不覆盖 ClaudeCode 私有产品能力、内部账号体系、云端协作和商业 UI。

## 2026-05-26 Prompt Surface v2 风险与处理

- 已确认旧风险：系统提示词只声明 `agent_memory/context.md`、`progress.md`、`bugs.md` 的优先级，但 `_build_initial_messages()` 实际没有自动注入这三份项目级上下文，导致模型判断仍可能看不到当前项目事实、进度和风险。
- 已处理：新增项目级 agent_memory 查找与注入逻辑，支持 workspace 是项目根或 `learning_agent` 子目录两种路径；长文件按首尾摘要注入，避免撑爆 system prompt。
- 已确认旧风险：用户明确要求真实浏览器时，模型可能认为“搜索到答案”就满足要求，而没有打开用户要求的真实浏览器。
- 已处理：system prompt、runtime rules、CLI/OAuth 适配器 prompt、browser_search 工具描述都写入“真实浏览器请求不能由搜索结果、fetch_url 或独立 Chromium 替代”。
- 已确认旧风险：`browser_open` 工具描述只写“独立 Chromium”，但没有明确“不用于真实 Chrome 请求”，模型仍可能把它当成真实桌面浏览器入口。
- 已处理：`browser_open` MCP 描述已明确不用于真实 Chrome、真实浏览器、桌面可见浏览器或登录态请求，必须先走 `browser_profile_status` 和 `browser_connect_real_chrome` workflow。
- 已确认旧风险：`runtime_instructions.md` 文件较长，而 `_read_runtime_instructions()` 只注入前 8000 字符；如果新增关键规则放在后面，模型实际看不到。
- 已处理：Prompt Surface v2 章节放在 `runtime_instructions.md` 顶部，确保优先进入 system prompt。
- 当前剩余风险：项目级 agent_memory 采用首尾摘要，不等价于完整全文注入；如果中间内容很关键，仍需要任务中显式读取对应文件。
- 当前剩余风险：MCP server 外部工具如果来自远程 server，仍依赖远程 server 自身的 description/searchHint 质量；本次只修正本项目内置 browser/search/workflow 相关描述。

## 2026-05-26 Prompt Architecture v1 计划风险

- 当前已确认风险：`LearningAgent._build_initial_messages()` 仍主要依赖多个 `_build_*_prompt()` helper 和直接字符串拼接，虽然已经比最初更清楚，但还没有正式 Prompt Registry 元数据层。
- 当前已确认风险：`agent_memory` 和 `memory.md` 已能进入 system prompt，但仍不是完整的 Memory Index 架构；长文件仍可能因为首尾摘要遗漏中段关键事实。
- 当前已确认风险：当前 debug log 能记录 initial messages 和 tool names，但用户还不能通过稳定只读工具直接拿到“本轮自动加载了哪些提示词、为什么加载、各占多少 token”的报告。
- 当前已确认风险：Observation v1 已存在，但 Evidence Ledger 仍是分散事件列表，尚未成为最终回答和 prompt surface 报告可直接引用的证据索引。
- 当前处理计划：执行 `docs/superpowers/plans/2026-05-26-agent-prompt-architecture-v1.md`，优先补 Prompt Registry、Context Assembler、Prompt Surface Report、Token Budget Report、Compact Summary 和 Evidence Ledger bridge。

## 2026-05-26 Prompt Architecture v1 Task 2 风险与处理

- 已处理风险：`LearningAgent._build_initial_messages()` 不再只靠手工字符串拼接，当前已通过 `ContextAssembler(self.prompt_registry).assemble_static_blocks(...)` 按注册表 priority 装配静态 block。
- 已处理风险：`LearningAgent.last_prompt_surface_report` 以前不存在，当前已在初始化时设置为空报告，并在每次 `_build_initial_messages()` 后记录 loaded blocks。
- 当前剩余风险：Task 2 只实现最小 Context Assembler 和静态 block 装配，尚未实现 Task 3-7 的 Memory Index、公开报告工具、Token Budget Report、Compact Summary 或 Evidence Ledger bridge。
- 当前剩余风险：token 估算仍是第一版 `max(1, len(text) // 4)` 粗略算法，适合测试和报告占位，不等价于真实模型 tokenizer。
## 2026-05-26 Prompt Architecture v1 Task 3 风险记录

- 已处理风险：旧实现会把 `agent_memory` 和超长 `memory.md` 作为大段正文放入 system prompt，容易挤占上下文并让报告无法说明来源元数据；当前已改为索引形式。
- 剩余风险：`stable_fact_count` 当前是基于非空非标题行的粗略计数，不等价于语义级事实抽取；后续如果需要更精确事实管理，应升级 Memory Manager。
- 剩余风险：索引只保留标题和最新尾部摘要，中段关键信息不会自动全文进入 system prompt；需要任务中显式读取对应文件才能获得完整内容。
## 2026-05-26 Prompt Architecture v1 Task 4 风险记录

- 已处理风险：`prompt_surface_report` 和 `token_budget_report` 在 Task 4 前不存在，模型请求这两个审计入口会返回未知工具；当前已注册 schema 并在 `_execute_tool()` 中分发。
- 已处理风险：提示词表面报告可能默认泄露完整提示词正文；当前 `include_block_text` 默认 false，报告默认只输出元数据，不输出完整提示词正文。
- 已处理风险：用户可能误以为历史设计文档或历史计划会自动影响当前模型判断；当前 `prompt_surface_report` 明确说明这些历史文档不会自动加载，除非本轮显式读取。
- 剩余风险：`include_evidence` 当前只是 Task 5 预留入口，还没有真正接入 Observation/Evidence Ledger。
- 剩余风险：token 估算仍是字符数除以四的粗略估算，不等价于真实模型 tokenizer。
- 剩余风险：`include_block_text=True` 当前不会输出完整正文缓存，只提示需要显式读取来源；这是为了避免伪造正文审计，后续若要展示正文需要 ContextAssembler 保存可控片段。
# 2026-05-26 Prompt Architecture v1 Task 5 风险记录

- 修改代码+PromptArchitectureV1: 已处理 Task 5 旧风险：`include_evidence` 以前只是占位文本，现在会读取 `observation_events` 输出 Evidence Ledger；如果没有这条记录，后续排查者可能误以为 evidence bridge 仍未落地。
- 修改代码+PromptArchitectureV1: 剩余风险：`soft_token_limit` 使用字符数除以四的粗略 token 估算，不等于真实模型 tokenizer；如果没有这条记录，后续维护者可能把当前预算数字误认为精确 token。
- 修改代码+PromptArchitectureV1: 剩余风险：Compact Summary 只保留 head/tail 摘录和元数据，不等于完整内容；如果没有这条记录，后续使用者可能误以为 compact 后仍可基于完整正文推理。
- 修改代码+PromptArchitectureV1: 剩余风险：Evidence Ledger 当前只展示进程内最近 observation events，尚不是跨进程持久化证据数据库；如果没有这条记录，后续使用者可能误以为重启后仍能恢复完整证据账本。

# 2026-05-26 Prompt Architecture v1 Phase 7 审查修复风险

- 修改代码+PromptArchitectureV1: 已处理风险：compact 曾经会从所有低优先级 block 中选择候选，可能把 `prompt.policy.response`、`prompt.policy.tool_boundary` 等 `built_in` 核心策略压成摘要；当前只允许动态、非 `built_in` 且超过自身预算的 block compact，并有回归测试锁定。
- 修改代码+PromptArchitectureV1: 已处理风险：`LearningAgent` 曾经没有把真实 prompt 软预算传给 `ContextAssembler`，导致 compact 更像单独测试能力；当前已有实例参数、配置文件字段和环境变量入口，并有生产路径回归测试锁定。

# 2026-05-26 Prompt Architecture v1 Task 7 剩余风险

- 修改代码+PromptArchitectureV1: 剩余风险：`token_budget_report` 和 `ContextAssembler` 仍使用字符数除以四的粗略 token 估算，不等价于真实 tokenizer；如果没有这条记录，后续使用者可能把估算数字当成精确模型 token。
- 修改代码+PromptArchitectureV1: 剩余风险：Memory Index 默认不会把长文件中段全文放入 system prompt；如果没有这条记录，后续任务可能误以为索引已经等价于读过完整 `memory.md` 或完整 `agent_memory` 文件。
- 修改代码+PromptArchitectureV1: 剩余风险：本次完成的是 Prompt Architecture v1 控制层，不等于复制 ClaudeCode 私有产品能力或实现真正自我意识；如果没有这条记录，后续目标评估可能把架构透明度误解成产品级完整等价。
# 2026-05-26 Capability Packs 方案 B 风险记录

- 修改代码+CapabilityPacks: 本轮未发现阻断性 bug，主要残余风险是后续继续扩写 `runtime_instructions.md` 或 agent_memory 摘要时可能重新突破 1900 token 预算；如果没有这条记录，后续维护者可能只看测试通过而忽略预算回归风险。
- 修改代码+CapabilityPacks: 已用 `test_default_prompt_budget_stays_under_capability_pack_target` 锁定首轮 prompt 预算，并把项目记忆索引压到每文件约 220 字符；如果没有这条记录，后续排查预算失败时不容易定位到记忆索引和 runtime 关键词的平衡点。

# 2026-05-26 RuntimePathFix 问题记录

- 修改代码+RuntimePathFix: 已确认根因是 `LearningAgent.__init__` 只用 `self.workspace / "runtime_instructions.md"`，导致项目根目录运行时找不到实际位于 `learning_agent/runtime_instructions.md` 的短 kernel；如果没有这条记录，后续排查者可能把问题误判成 runtime 文件内容为空。
- 修改代码+RuntimePathFix: 已修复为工作区覆盖优先、包内默认兜底，并保留显式缺失路径的可读占位；如果没有这条记录，后续维护者可能误删缺失占位或破坏用户覆盖能力。
