# 项目上下文
## 2026-05-30 Stage 13B Legacy Entry Cut 当前事实

- 本轮继续执行阶段 13B：把活跃测试和开发辅助脚本从旧脚本入口迁到分层入口，并把 `learning_agent/learning_agent.py` 收紧成只启动 `app.cli.main()` 的脚本文件。
- `learning_agent/tests_support/legacy_learning_agent_suite.py` 已改为从 `app/core/models/mcp/tools` 等分层模块导入，不再依赖旧脚本入口的大量重导出。
- `learning_agent/fake_model_repl.py` 已改为从 `core.agent` 与 `core.messages` 导入，避免开发辅助脚本继续示范旧入口用法。
- `learning_agent/learning_agent.py` 现在只保留路径兜底、`__path__` 脚本模式兜底和 `main()` 启动转发；业务对象导入应走具体分层模块。
- `learning_agent/tests/test_compat_cleanup.py` 已新增阶段 13B 保护测试，防止活跃文件回流旧入口或脚本入口重新批量 re-export。
- 阶段 13B 自动化验证已通过：`unittest discover learning_agent` 为 365 tests OK、`mcp-doctor` 退出码 0、模型可见 30 个 MCP 工具。
- 阶段 13B 真实可见终端验收已尝试：`real_chrome_natural_weather_travel-20260530_111154/result.json` 显示 `completed=false`，原因是可见终端里的模型调用返回 HTTP 429 `usage_limit_reached`，agent 未进入真实浏览器工具调用阶段。
- 已测试合法备用 provider：本机存在 `codex.exe`，但 `LEARNING_AGENT_MODEL_PROVIDER=codex` 的一次性 run 在 `codex exec` 90 秒超时，暂不能替代 OAuth/API 完成本轮真实终端验收。

## 2026-05-30 Stage 13 Tool Schema Split 当前事实

- 本轮开始执行“去兼容化 + core 再拆分”的阶段 13 第一刀，目标是减少生产模块对旧 `learning_agent.learning_agent` 入口的依赖。
- `learning_agent/tools/schemas.py` 已成为内置工具 schema 和能力包映射的唯一事实源；`core/agent.py` 已经不再保存大块 `TOOL_SCHEMAS` 定义。
- `tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py` 和 `learning_agent/__init__.py` 已经改为读取新模块，不再导入旧 `learning_agent.learning_agent`。
- 新增 `learning_agent/tests/test_compat_cleanup.py`，用于阻止上述生产模块重新回流旧入口。
- 本轮验证已完成：完整 `unittest discover learning_agent` 通过 363 tests、`mcp-doctor` 退出码 0、真实可见终端验收 `real_chrome_natural_weather_travel-20260530_104237` 通过且 `permission_sent_count=0`。
- 本轮学习备份位于 `learning_agent/test/stage13_tool_schema_split_20260530/`。
- 旧记录更新：阶段 13B 已迁移 `tests_support/legacy_learning_agent_suite.py` 的旧导入面，并把 `learning_agent/learning_agent.py` 收紧成只启动 `app.cli.main()` 的脚本入口。
## 2026-05-30 Modular Core Agent 当前事实

- 阶段 12 已把 `learning_agent/learning_agent.py` 收束为薄兼容入口；后续排查入口启动、旧导入兼容和脚本模式路径问题时才优先看它。
- 主 agent 实现现在位于 `learning_agent/core/agent.py`；排查 `LearningAgent.run()`、模型工具循环、`TOOL_SCHEMAS`、客户模式权限、旧公开函数兼容时优先看这个文件。
- `learning_agent/learning_agent.py` 在脚本模式下设置 `__path__ = [PACKAGE_ROOT]`，这是为了让同目录 MCP server 把它误当顶层模块加载时，仍能继续解析 `learning_agent.browser_real_chrome` 等子模块。
- `learning_agent/core/__init__.py` 保留包模式和脚本模式两套导入 fallback；如果以后删除 fallback，必须先验证 `python learning_agent\browser_automation_mcp_server.py` 和 `mcp-doctor`。
- `learning_agent/core/agent.py` 中的 packaged skill fallback 需要从包根 `learning_agent/skills` 读取；迁移到 `core/` 后不能再用 `Path(__file__).with_name("skills")`，否则只会寻找不存在的 `learning_agent/core/skills`。
- 当前架构索引以 `learning_agent/AGENT_ARCHITECTURE_INDEX.md` 为准；README 的“文件说明”和“你应该重点看哪里”已经同步到薄入口 + core agent 的新结构。
- 当前自动化基线：`py_compile` 通过；兼容入口单测和 discover 均为 361 条、`skipped=1`；`mcp-doctor` 退出码 0 且三个 MCP server 均启动成功。
- 当前真实 Chrome 诊断基线：`mcp-doctor` 显示 profile 诊断 `available`，Chrome 路径为 `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`，User Data 为 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data`，Chrome 未运行，9222 端口可用。
- Windows 受限环境下，Python `Path.exists()` 读取真实 Chrome User Data 可能抛 `PermissionError`，`tasklist` 也可能被拒绝；当前 `browser_real_chrome.py` 会分别用 PowerShell `Test-Path` 和 `Get-Process chrome` 做只读 fallback，避免误判环境不可用。
- 阶段 12 最终真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_025500/result.json` 显示 `completed=true`、`permission_sent_count=0`、`permission_count_passed=true`，最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`。


## 2026-05-29 Modular Tests Layer 当前事实

- 阶段 11 已建立 `learning_agent/tests/` 测试入口层，用来按领域定位和运行测试。
- `learning_agent/tests/_legacy_groups.py` 是当前测试分组路由，负责把遗留测试方法分配到 core、models、mcp、tools、browser intent、browser harness、prompts 和 observability 八个入口。
- `learning_agent/tests_support/legacy_learning_agent_suite.py` 暂时承载从旧 `test_learning_agent.py` 搬出的完整遗留测试主体；这是阶段 11 的低风险过渡方案，避免一次性手搬 359 条测试时改变测试行为。
- `learning_agent/test_learning_agent.py` 现在是旧入口兼容层；使用包路径运行时会加载全部分组测试，使用 `discover learning_agent` 目录发现时会返回空套件，避免重复计数。
- `discover learning_agent` 目录模式会让 `learning_agent.py` 容易遮蔽 `learning_agent` 包名；阶段 11 已在测试兼容层里强制把项目根移动到 `sys.path` 最前并清理遮蔽模块。
- 当前测试总数仍为 359 条，`skipped=1`，没有因为拆分减少测试覆盖。

## 2026-05-29 Modular App Layer 当前事实

- 阶段 10 已建立 `learning_agent/app/` 应用入口层，用来承载 CLI、doctor、HTTP bridge 和交互式终端入口。
- `learning_agent/app/doctor.py` 现在提供 app 层 `run_mcp_doctor(workspace)`，真实诊断逻辑继续委托 `learning_agent.mcp.doctor.run_mcp_doctor`。
- `learning_agent/app/http_bridge.py` 现在承载 `LearningAgentCommandBridgeServer`、`LearningAgentCommandBridgeHandler`、`create_command_bridge_server()` 和 `serve_command_bridge()`。
- `learning_agent/app/interactive.py` 现在承载真实终端交互循环 `run_interactive_session()`，负责打印启动状态、读取用户 prompt、调用 agent、打印最终回答和验收事件。
- `learning_agent/app/cli.py` 现在承载 `build_model_from_env()`、`format_cli_run_response()`、运行时依赖装配和 `main()` 命令入口。
- 为避免循环导入，`app.cli.main()` 接受 `agent_cls` 和 `permission_callback` 注入；`learning_agent.py` 调用时传入 `LearningAgent` 和 `ask_permission_from_terminal_customer_mode`。
- `learning_agent.py` 中的旧 CLI、model factory、HTTP bridge 创建器和 main 入口已经改为兼容转发；真实执行路径优先进入 `learning_agent/app/`。
- 阶段 10 自动化验收通过：`py_compile`、`-k app_package`、`-k command_bridge`、`--help`、`mcp-doctor`、`run --prompt "ping" --json --max-turns 1` 和完整 `unittest` 均已通过。
- 阶段 10 备份目录为 `learning_agent/test/modular_refactor_stage10_20260529/`。

## 2026-05-27 Acceptance Harness 当前事实

- `learning_agent` 已新增最小可观测验收协议模块 `learning_agent/acceptance_harness.py`。
- 验收协议默认完全静默；只有设置 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG` 后才会写 UTF-8 JSONL 事件，并在真实终端打印 `::learning-agent-acceptance ` 前缀标记。
- 当前事件状态包括：`permission_required`、`permission_answered`、`agent_ready_for_user_prompt`、`user_prompt_received`、`final_answer_printed`。
- `ask_permission_from_terminal()` 已接入权限前后事件，主交互循环已接入 ready、收到 prompt、最终回答已打印事件。
- `user_prompt_received` 当前会在验收模式下记录输入长度和 `prompt_preview`；`final_answer_printed` 当前会记录回答长度和 `answer_preview`，便于外部 agent 确认真实输入和真实输出。
- 学习备份目录为 `learning_agent/test/acceptance_harness_20260527/`，包含最终版源码副本、测试副本、计划文档、可见终端 smoke 脚本、事件日志、结果 JSON、截图和本轮调试日志。
- 本轮真实可见终端 smoke 使用 `start_oauth_agent.bat` 启动本地可见窗口，通过事件日志等待权限与 ready 状态，输入短 prompt，目标 agent 最终回复 `ACCEPTANCE_HARNESS_OK`。
- 已新增真实天气验收脚本 `learning_agent/test/acceptance_harness_20260527/run_chongqing_weather_visible_terminal_acceptance.ps1`，用于驱动可见终端完成重庆天气和旅游攻略任务。
- 真实天气验收已通过：事件日志显示 `permission_required -> permission_answered -> agent_ready_for_user_prompt -> user_prompt_received -> browser_open 权限 -> browser_snapshot 权限 -> final_answer_printed`，结果 JSON 显示 `completed=true`。
- 本轮真实浏览器天气结果来自 Open-Meteo：重庆 2026-05-30 天气代码 51（毛毛雨），最高 28.3°C，最低 22.2°C，最大降水概率 25%，最大风速 4.0 km/h，紫外线指数 8.60。
- 天气验收证据文件：`weather_visible_terminal_result.json`、`weather_visible_terminal_events.jsonl`、`weather_latest_run_readable.md`、`weather_01_startup.png`、`weather_02_prompt_sent.png`、`weather_03_final.png` 均位于 `learning_agent/test/acceptance_harness_20260527/`。
- `learning_agent/acceptance_controller/` 已新增通用真实可见终端验收控制器，入口为 `controller.ps1`，场景文件位于 `acceptance_controller/scenarios/`。
- 当前控制器场景包括 `smoke.json`、`chongqing_weather_browser.json` 和 `real_chrome_profile_status.json`；场景 JSON 只描述 prompt、必需事件、调试日志断言和最终回答断言。
- 新 controller 已真实跑通两个场景：`runs/smoke-20260527_230534/result.json` 和 `runs/chongqing_weather_browser-20260527_230607/result.json` 均显示 `completed=true`。
- Acceptance Controller 学习备份位于 `learning_agent/test/acceptance_controller_20260527/`，包含 controller、README、场景 JSON、测试副本和本轮 result/debug 证据。
- `real_chrome_profile_status.json` 是真实 Chrome/profile 的安全探针场景：它只要求读取 `tool_list.md` 与 `real_chrome/SKILL.md`，调用只读 `browser_profile_status`，并明确禁止读取 cookies、localStorage、sessionStorage、token、登录网页、隐私页面、标签页内容或插件内容。
- 真实可见终端已跑通 `real_chrome_profile_status` 场景：`learning_agent/acceptance_controller/runs/real_chrome_profile_status-20260527_232424/result.json` 显示 `completed=true`。
- 本轮真实 Chrome 状态结果为：`mode=independent_chromium`、`real_chrome_connected=false`、`chrome_started_by_agent=false`、`endpoint=`、`profile=`、`pages=0`、最近安全拒绝为无；这证明 status 工具可用，但尚未连接用户真实 Chrome。
- 本轮真实 Chrome 安全探针学习备份位于 `learning_agent/test/real_chrome_profile_status_20260527/`，包含更新后的 README、测试副本、场景 JSON、result、events、debug log 和最终截图。
- `acceptance_controller/controller.ps1` 已新增 `permission_policy` 场景级权限策略：未配置策略的旧场景保持默认同意；配置策略后可用 `default_response`、`allow_contains`、`deny_contains` 控制自动输入 `y` 或 `n`，并把每次权限决策写入 `permission_policy_decisions`。
- 已新增 `real_chrome_connect_public_page.json` 场景，用于连接真实 Chrome profile 后只打开公开页面 `https://example.com`，并禁止 `browser_evaluate`、tabs、console、network、downloads 等非白名单权限。
- 真实可见终端已跑通 `real_chrome_connect_public_page` 场景：`learning_agent/acceptance_controller/runs/real_chrome_connect_public_page-20260528_055137/result.json` 显示 `completed=true`。
- 本轮真实 Chrome 公开页结果为：`browser_connect_real_chrome 成功`、`mode=real_chrome`、`real_chrome_connected=true`、`profile=Default`、`browser_open` 打开 `https://example.com`、`browser_snapshot` 读取到 `Example Domain`。
- 本轮 connect 场景权限审计显示只同意了 5 个白名单请求：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`；未调用 `browser_evaluate`，未读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容或插件内容。
- 本轮测试启动的 Chrome 进程已在验收后清理；最终 `mcp-doctor` 显示真实 Chrome 正在运行：`false`，profile 诊断仍为 `available`。
- 本轮真实 Chrome 连接公开页学习备份位于 `learning_agent/test/real_chrome_connect_public_page_20260528/`，包含 controller、README、测试副本、场景 JSON、result、events、debug log 和最终截图。
- 已新增 `real_chrome_chongqing_weather_travel.json` 场景，用于在真实桌面 Chrome 中连接真实 profile 后，只打开公开 Open-Meteo URL 查询重庆 2026-05-31 天气，并生成旅游攻略。
- 真实可见终端已跑通 `real_chrome_chongqing_weather_travel` 场景：`learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_061032/result.json` 显示 `completed=true`。
- 本轮真实 Chrome 天气攻略结果为：`browser_connect_real_chrome 成功`、`real_chrome_connected=true`、`browser_open` 打开 Open-Meteo 重庆 2026-05-31 URL、`browser_snapshot` 读取到公开 JSON。
- 本轮读取到的 Open-Meteo 结果为：重庆 2026-05-31 天气代码 51（毛毛雨），最高 31.0°C，最低 22.5°C，最大降水概率 39%，最大风速 6.4 km/h，紫外线指数 8.55。
- 本轮权限审计只同意 5 个白名单请求：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`；默认策略为 `deny`，未调用 `browser_evaluate`、tabs、console、network 或 downloads。
- 本轮测试启动的 Chrome 进程已在验收后清理；最终 `mcp-doctor` 显示真实 Chrome 正在运行：`false`。
- `ask_permission_from_terminal()` 已升级为结构化权限事件：`permission_required` 和 `permission_answered` 现在保留 `permission_kind`、`tool_name`、`arguments`、`risk_level`、`risk_summary` 等字段，同时继续保留旧 `action` 文本字段。
- `acceptance_controller/controller.ps1` 已支持结构化权限策略字段：`allow_tool_names`、`deny_tool_names`、`allow_url_prefixes`，并把每次决策的 `tool_name`、`arguments`、`risk_level`、`risk_summary`、`url` 写入 `permission_policy_decisions`。
- `real_chrome_chongqing_weather_travel.json` 已从纯文本 contains 白名单升级为结构化白名单：只用 `allow_contains` 放行启动 MCP，其余浏览器工具必须命中 `allow_tool_names`；`browser_open` 还必须命中 `https://api.open-meteo.com/v1/forecast` 前缀。
- 结构化权限审计版真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_062749/result.json` 显示 `completed=true`，其中 `browser_open` 决策原因是 `allow_tool_name_and_url_prefix`。
- 结构化权限审计版仍读取到重庆 2026-05-31 天气：天气代码 51（毛毛雨），最高 31.0°C，最低 22.5°C，最大降水概率 39%，最大风速 6.4 km/h，紫外线指数 8.55。

## 2026-05-27 重庆天气浏览器自动化当前事实

- 本轮功能测试使用当前日期 2026-05-27 推算 3 天后为 2026-05-30。
- 目标 `learning_agent` 已通过 CLI `run --prompt --json` 路径完成重庆 2026-05-30 天气查询和一日旅游攻略生成。
- 最新调试日志确认目标 agent 按 read-based skill discovery 流程先读 `learning_agent/skills/tool_list.md`，再读 `learning_agent/skills/browser_automation/SKILL.md`。
- 最新调试日志确认目标 agent 使用真实 MCP 工具 `mcp__browser_automation__browser_open` 打开 Open-Meteo URL，并用 `mcp__browser_automation__browser_snapshot` 读取页面 JSON。
- 本轮读取到的 Open-Meteo 结果为：重庆 2026-05-30 天气阴，最高 28.9°C，最低 21.9°C，最大降水概率 29%，最大风速 5.2 km/h，紫外线指数 8.50。
- 本轮没有修改业务代码；只新增测试摘要归档文件 `learning_agent/test/chongqing_weather_browser_20260527/summary.md`，并更新 Codex 开发协作记忆。

## 2026-05-27 learning_agent 当前水平评估

- 本轮只读分析确认：`learning_agent` 当前已经不是最小 demo，而是具备成熟 coding agent core 骨架的教学/二次开发版 agent。
- 已落地能力包括：四原子首轮工具面、Tool Catalog / Tool Pool / ToolPolicy、Prompt Registry / Context Assembler、`staticprompt` / `dynamicprompt` 文件化提示词、三级 skill 规则树、MCP stdio/HTTP/SSE 接入、浏览器自动化、真实 Chrome workflow gate、CLI run、HTTP command bridge、调试日志、子 agent/任务记录、计划模式、轻量 LSP/REPL/Cron/Monitor 教学能力。
- 当前验证基线：使用 Codex 自带 Python 执行 `py_compile` 通过；`python -m unittest learning_agent.test_learning_agent` 当前结果为 `Ran 332 tests in 28.030s OK (skipped=1)`；`learning_agent.py mcp-doctor` 显示 `browser_search`、`workspace_tools`、`browser_automation` 三个 MCP server 均启动成功，模型可见 MCP 工具 30 个。
- 当前边界判断：它已经达到“agent core 架构成熟、工程化验证较强、可继续扩展”的状态，但仍不是完整商业级 Codex / Claude Code 产品；远程多用户、安全认证、真实 git worktree、持久化调度、完整 UI、真实 Chrome 登录态端到端验收仍属于未完全产品化范围。

## 当前项目身份

- 项目根目录：`H:\codexworkplace\sofeware\OpenHarness-main`。
- 主要目标：把 `learning_agent` 演进为面向软件工程任务的成熟 coding agent，公开可复现 agent core 对齐 Codex / ClaudeCode，并在提示词表面、工具延迟加载、记忆索引和审计报告上继续增强。
- 用户偏好：默认中文解释；代码修改前先读相关文件；新写或修改代码需保留中文教学注释和 `learning_agent/test` 学习备份；非简单任务维护 `agent_memory/context.md`、`progress.md`、`bugs.md`。

## 已完成的核心架构事实

- Tool Architecture v2 已完成并进入四原子首轮工具面：`AgentTool` 元数据、Tool Catalog、Current Tool Pool、deferred MCP tools、内部兼容工具目录已落地；模型首轮默认只暴露 `read`、`write`、`edit`、`bash`。
- ToolPolicy v2 已完成：deny / allow rules、skill gate、workflow gate、执行前 guard、重复拒绝记忆、子 agent policy 继承已落地。
- Prompt Architecture v1 已完成：Prompt Registry、Context Assembler、Memory Index、Prompt Surface Report、Token Budget Report、Compact Summary、Evidence Ledger bridge 已落地。
- Capability Packs 方案 B 已进一步收敛为极简 read-based skill router：其他能力通过 `learning_agent/skills/tool_list.md` 和对应 `SKILL.md` 按需读取说明，再由四原子工具执行。
- PromptFiles v3 已完成：`LearningAgent` 每轮读取 `staticprompt/staticprompt.md` 作为静态系统提示词，`dynamicprompt/dynamicprompt.md` 只作为按需动态运行规则索引。
- 2026-05-29 阶段 6 已完成：PromptFiles 的读取、兜底、动态提示词元信息、PromptRegistry 入口、ContextAssembler 入口、token budget 入口和 PromptSurfaceReport 入口已经收拢到 `learning_agent/prompts/`；主文件改为委托新 prompts 层。

## 2026-05-26 Lean System Prompt v2 当前事实

- 本轮按用户确认的精简方案，把静态系统提示词从 `learning_agent.py` helper 提取到 `learning_agent/staticprompt/staticprompt.md`。
- 新静态提示词保留：核心身份、行为原则、上下文优先级、Prompt Surface Policy、当前工作区占位符和动态规则路由。
- 细节性工具流程和输出规范已迁移到 `learning_agent/dynamicprompt/dynamicprompt.md` 与 `learning_agent/skills/*/SKILL.md`，默认不作为每轮正文进入 system prompt。
- `_build_initial_messages()` 当前只给 `block_contents` 传入 `prompt.kernel.identity`、`context.long_term_memory_index`；目标 agent 不再默认读取 Codex 开发用 `agent_memory` 三件套。
- `dynamicprompt/dynamicprompt.md` 继续保留按需读取规则和内部能力关键词索引，但不再把 `tool_search` / `select_pack` 作为模型默认路由。
- 为兼容实时信息策略回归，`staticprompt/staticprompt.md` 和 `dynamicprompt/dynamicprompt.md` 都保留 `知识与实时信息策略` 相关锚点。
- 旧活跃记忆全文已归档到 `agent_memory/archive/2026-05-26-lean-system-prompt/`，活跃三件套改为短摘要，避免继续膨胀每轮上下文。

## 2026-05-26 Dynamic Runtime Rules 当前事实

- 本轮已按用户确认方向，把旧 `runtime_instructions.md` 重命名迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`。
- `_build_initial_messages()` 当前不再读取旧 `runtime_instructions.md`，每轮加载块只包含文件化静态系统提示词和 `memory.md` 长期记忆索引。
- 静态系统提示词已上移必要底线：默认中文、无工具结果不声称执行、实时/最新信息必须查工具、动态规则读取路由、首轮只暴露 `read / write / edit / bash`。
- `learning_agent/skills/*/SKILL.md` 是动态详细规则的主要承载层；默认发现路径是先用 `read` 读取 `learning_agent/skills/tool_list.md`，再读取对应 `SKILL.md` 或 `dynamicprompt/dynamicprompt.md`。
- `dynamicprompt/dynamicprompt.md` 仍保留关键词索引，方便测试和人工审计，但不是首轮 system prompt 的常驻正文。

## 重要边界

- 当前架构不声明复制 ClaudeCode 私有产品能力、商业账号体系、云协作、PR 订阅或完整图形产品 UI。
- Memory Index 默认不是全文读取；如果任务需要历史细节，必须显式读取归档文件或相关项目文件。
- Token 估算仍是粗略估算，不等价于真实 tokenizer。

## 2026-05-26 Four Atom Tool Surface 当前事实

- 用户确认继续执行参考 `pi-main` 的极简方案：目标 agent 首轮模型可见工具从旧的 kernel 工具改为 4 个原子工具：`read`、`write`、`edit`、`bash`。
- `learning_agent/learning_agent.py` 中旧内置工具、MCP 工具、skill 工具和 capability pack 逻辑仍保留在内部目录，用于兼容、测试和后续迁移，但默认不进入首轮 Tool Pool。
- `learning_agent/staticprompt/staticprompt.md` 和 fallback static prompt 都只指向 `learning_agent/skills/tool_list.md` 作为按需能力发现入口。
- `learning_agent/dynamicprompt/dynamicprompt.md` 是按需轻规则文件，保留内部能力关键词索引，但不包含旧 `tool_search` 或 `select_pack` 路由。
- `learning_agent/README.md` 已同步描述四原子工具面、read-based skill discovery 和旧工具入口的内部兼容边界。

## 2026-05-26 CLI / HTTP Command Bridge 当前事实

- `learning_agent.py` 已新增一次性 CLI 接口：`python learning_agent\learning_agent.py run --prompt "..." --json`，用于让 Codex 或脚本启动一次 agent 并接收 JSON 结果。
- `learning_agent.py` 已新增 HTTP command bridge：`python learning_agent\learning_agent.py bridge --bridge-host 127.0.0.1 --bridge-port 8765 --bridge-token <token>`。
- HTTP bridge 默认建议绑定 `127.0.0.1`；`GET /health` 返回 agent 状态和当前可见工具，`POST /run` 接收 JSON `prompt` 和可选 `max_turns`，返回 JSON `answer`。
- bridge token 是可选保护；配置后 `POST /run` 支持 `Authorization: Bearer <token>` 或 `X-Learning-Agent-Token`。
- bridge 使用同一个 `LearningAgent` 实例，并通过锁串行化 `agent.run()`，便于后续真实启动、调试、Codex 控制和结果接收测试。

## 2026-05-26 Dynamic Prompt Tree 当前事实

- 动态提示词已升级为三级加载树：`learning_agent/skills/tool_list.md` -> `learning_agent/skills/<skill>/SKILL.md` -> `learning_agent/skills/<skill>/rules/*.md`。
- 顶层 `SKILL.md` 现在只保留能力判断、边界和子规则索引，不再展开完整流程，也不再出现 `tool_search` / `select_pack` 旧路由。
- `learning_agent/learning_agent.py` 的 `read` 原子工具已新增动态提示词层级门控：读取 `rules/*.md` 前必须先读取 `tool_list.md` 和对应父 `SKILL.md`。
- `learning_agent/staticprompt/staticprompt.md`、`dynamicprompt/dynamicprompt.md`、`skills/tool_list.md` 和 README 已同步说明三级动态规则树。
- `dynamicprompt/dynamicprompt.md` 仍是按需动态规则索引，不进入每轮 system prompt；更细工具流程现在优先沉淀到各 skill 的 `rules/*.md`。

## 2026-05-26 Current Date Prompt 当前事实

- `learning_agent/learning_agent.py` 已参考 ClaudeCode 的运行时注入方式新增 `get_local_iso_date()`，每次渲染静态提示词时生成本机本地 `YYYY-MM-DD` 日期。
- `learning_agent/staticprompt/staticprompt.md` 已新增 `当前日期：{{CURRENT_DATE}}`，静态文件只保存占位符，不写死具体日期。
- `_read_static_prompt()` 当前会同时替换 `{{CURRENT_WORKSPACE}}` 和 `{{CURRENT_DATE}}`；fallback static prompt 也会写入当天日期，避免静态文件缺失或损坏时丢失日期上下文。
- `learning_agent/test_learning_agent.py` 已新增回归测试，验证每轮 `_build_initial_messages()` 的 system prompt 都把 `{{CURRENT_DATE}}` 渲染为当天真实日期。

## 2026-05-26 Browser Automation 当前事实

- `learning_agent` 已实现 read-based browser tool unlock：读取 `browser_automation/SKILL.md` 后，`browser_automation` MCP 工具包会进入当前 Tool Pool。
- 读取 `real_chrome/SKILL.md` 后，会准备 `real_chrome` 与后续页面操作需要的 `browser_automation` 工具，但 `browser_connect_real_chrome` 仍必须等待 `browser_profile_status` workflow 完成。
- `read` 路径解析已兼容两种工作区：项目根目录下的 `learning_agent/skills/...`，以及 CLI 默认 `learning_agent` 工作区下的同一写法。
- HTTP command bridge 真实闭环已通过：本地测试网页被真实 Playwright MCP 工具 `browser_open` 打开，并由 `browser_snapshot` 读取页面快照。
- 2026-05-26 已完成真实大模型端到端浏览器验收：HTTP command bridge 和 CLI `run --prompt --json` 都让目标 agent 先读取 `tool_list.md` 与 `browser_automation/SKILL.md`，再调用真实 MCP `browser_open` / `browser_snapshot` 读取 Open-Meteo 北京 2026-05-29 天气 JSON。
- 本次验收确认 Open-Meteo 返回：北京 2026-05-29 最高 30.5°C、最低 17.0°C、最大降水概率 0%、weather_code=1、最大风速 14.6 km/h；agent 已基于真实浏览器快照生成中文一日旅游攻略。
- 本次还修复了两个真实场景问题：`real browser automation` 英文短语不再误触发真实 Chrome/profile workflow；`LearningAgent._final_answer_retry_message()` 缺失导致 HTTP bridge 500 的问题已补齐。

## 2026-05-28 Real Chrome Google Human Visible 当前事实

- 已新增可复用真实桌面 Chrome Google 拟人搜索验收场景：`learning_agent/acceptance_controller/scenarios/real_chrome_google_human_search.json`。
- 场景目标是让用户肉眼看到桌面 Chrome 打开 `https://www.google.com/`，点击搜索框，输入 `重庆 2026-05-31 天气 旅游攻略`，按 Enter，等待结果页，保存截图并读取结果页快照。
- 场景权限策略默认拒绝未知权限，仅放行 MCP 启动、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`；显式拒绝 `browser_evaluate`、tabs、console、network、downloads、upload。
- `controller.ps1` 已支持 `post_success_wait_seconds`，本场景成功后保留真实窗口 20 秒，方便用户实际看到 Chrome 搜索结果。
- `final_answer_printed` 事件已新增 `answer_text` 完整回答字段；controller 优先用完整回答断言，避免 `answer_preview` 500 字截断导致真实成功被误判失败。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/real_chrome_google_human_search-20260528_064903/result.json` 显示 `completed=true`，Google 截图保存在 `learning_agent/browser_artifacts/real_chrome_google_human_search_20260528.png`。

## 2026-05-28 Real Browser Task Harness 当前事实

- 已新增通用真实浏览器查询 harness：当用户自然说“请使用真实浏览器，帮我查询/搜索/查找会议、酒店、航班、资料、天气、旅游攻略”等任务时，`LearningAgent._build_initial_messages()` 会额外注入紧凑的 `Real Browser Task Harness`。
- `_detect_real_chrome_intent()` 已补充 `真实浏览器`、`真实的浏览器`、`真实可见浏览器` 等中文短语，避免用户短 prompt 漏判。
- 新增 `_detect_real_browser_information_task()` 和 `_build_real_browser_task_harness_message()`，把自然查询任务导向真实桌面 Chrome，而不是依赖用户把工具步骤写进 prompt。
- harness 固定通用路线：读取 `tool_list.md` 和 `real_chrome/SKILL.md`，先 `browser_profile_status`，再 `browser_connect_real_chrome(confirm_real_profile=true)`，随后打开 `https://www.google.com/`，执行 `browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- `real_chrome/SKILL.md` 已新增子规则索引 `rules/search_task_workflow.md`；该规则把会议、酒店、航班、资料、天气、旅游攻略等公开查询统一到同一套真实 Chrome Google 可见搜索流程。
- 新增自然短 prompt 验收场景 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_weather_travel.json`，第一行 prompt 保留用户自然表达：“请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略。”
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260528_073250/result.json` 显示 `completed=true`；截图为 `learning_agent/browser_artifacts/real_chrome_chongqing_weather_travel_20260531.png`。

## 2026-05-28 Real Browser Customer Mode 当前事实

- 已新增真实浏览器客户模式自动授权：交互式 `main()` 改用 `ask_permission_from_terminal_customer_mode()`，项目内置 MCP server（`browser_search`、`workspace_tools`、`browser_automation`）启动时默认自动允许，不再要求用户输入 `y`。
- `LearningAgent` 新增 `real_browser_information_task_requested`，每轮识别“真实浏览器 + 查询/搜索/会议/酒店/航班/资料/天气/攻略”等公开信息查询任务后，才启用浏览器工具白名单自动授权。
- 白名单自动授权覆盖真实浏览器公开查询流程所需工具：`browser_profile_status`、`browser_connect_real_chrome(confirm_real_profile=true)`、`browser_open` 的 Google URL、`browser_snapshot`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_disconnect_real_chrome`。
- 敏感浏览器工具仍不默认放行：`browser_evaluate`、network、console、tabs、downloads、upload、任意非 Google URL 等继续走原权限层或策略阻断。
- 自动授权时终端显示 `Agent > 正在...` 进度提示，替代连续 `[y/N]` 授权问答；内部 `mcp_call_progress_events` 记录 `permission_auto_approved` 供审计。
- 自然短 prompt 验收场景 `real_chrome_natural_weather_travel.json` 已新增 `max_permission_sent_count: 0`，要求真实客户模式下权限输入次数必须为 0。

## 2026-05-28 Real Browser YouTube Customer Mode 当前事实

- 用户截图证明 YouTube 视频评论排行类自然短 prompt 仍会逐步弹 `y/N`，根因是 `_detect_real_browser_information_task()` 只覆盖“查询/搜索/天气/攻略/会议/酒店/航班/资料”等词，没有覆盖“网站/视频/评论/最多/有哪些/youtube”等公开查询表达。
- 已扩展公开信息查询关键词：`网站`、`视频`、`评论`、`最多`、`有哪些`、`哪些`、`哪个`、`排行`、`排名`、`榜单`、`介绍`、`youtube`。
- 已新增单元测试 `test_real_browser_youtube_video_question_is_customer_information_task`，锁定“请使用真实浏览器，youtube网站的视频关于ai agent介绍，评论最多的有哪些？”会进入真实浏览器客户模式。
- 已新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_youtube_video_comments.json`，要求同一 YouTube 自然 prompt 的 `max_permission_sent_count` 为 0。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_youtube_video_comments-20260528_091026/result.json` 显示 `completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。

## 2026-05-29 Modular Browser Layer 当前事实

- 阶段 7 已建立 `learning_agent/browser/` 真实浏览器层，包含 `intent.py`、`harness.py`、`permissions.py`、`search_workflow.py`、`artifacts.py`。
- `browser.intent` 是真实 Chrome/真实浏览器意图、公开信息查询意图和独立浏览器工具阻断的稳定入口。
- `browser.harness` 是自然短 prompt 真实浏览器查询任务约束文本的稳定入口。
- `browser.permissions` 是真实浏览器客户模式自动授权、终端 MCP 启动默认放行和客户可见进度文案的稳定入口。
- `browser.search_workflow` 保存 Google URL 白名单、客户模式固定工具白名单和最终回答动作名清单。
- `browser.artifacts` 保存浏览器截图/下载产物文件名清洗和路径越界防护。
- `learning_agent.py` 旧方法仍存在以保持兼容，但真实执行路径已经优先委托到 `browser/`；后续阶段 12 需要删除重复业务实现。
- 阶段 7 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260529_105333/result.json` 中 `completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。

## 2026-05-29 Modular Tasks Layer 当前事实

- 阶段 8 已建立 `learning_agent/tasks/` 任务层，包含 `background.py`、`task_runs.py`、`team.py`、`cron_monitor.py`。
- `tasks.background` 是 `BackgroundCommand`、后台输出队列读取和后台命令状态格式化的稳定入口。
- `tasks.task_runs` 是 `TaskRun`、子 agent 禁止继承工具集合、background 参数解析和子 agent prompt 构造的稳定入口。
- `tasks.team` 是 `TeamMessage`、`TeamPeer` 和 peer 状态计算的稳定入口。
- `tasks.cron_monitor` 是 `CronRecord`、`MonitorRecord`、cron/monitor 状态解析、列表长度解析、monitor 结果状态解析和记录格式化的稳定入口。
- 阶段 8 仍保持教学版边界：不创建系统定时器，不做持久化队列，不启动真实监控服务，不发送通知。
- `learning_agent.py` 仍负责实际副作用编排；后续阶段 12 需要删除已委托 helper 后留下的不可达旧代码。
## 2026-05-30 Stage 13C context: attach to already-running Chrome CDP

- Context: visible-terminal acceptance `real_chrome_natural_weather_travel-20260530_142210` proved the model/tool permission flow no longer spammed `Y`, but the agent stopped because `browser_connect_real_chrome` returned “检测到 Chrome 正在运行，请先关闭当前 Chrome”.
- Evidence: direct check of `http://127.0.0.1:9222/json/version` returned Chrome CDP metadata and a `webSocketDebuggerUrl`, so this machine already had a trustworthy local Chrome CDP endpoint.
- Root cause: `learning_agent/browser_automation_mcp_server.py` blocked every `manager.chrome_is_running()` case before checking whether the existing Chrome was already controllable through local CDP.
- Fix direction: keep blocking running Chrome when there is no trusted CDP, but allow attaching to the existing local CDP when `wait_for_cdp_endpoint(debug_port, timeout_seconds=1.0)` succeeds.
- Implementation: `browser_connect_real_chrome()` now passes `attach_existing_cdp=True` and `existing_debug_port=debug_port` into `_connect_real_chrome_after_checks()` when Chrome is already running and CDP is live.
- Safety boundary: attach mode does not call `subprocess.Popen`, keeps `chrome_process=None`, and therefore `browser_disconnect_real_chrome(close_browser=false)` cannot terminate the user’s already-open Chrome.
- Tests: added regression coverage for both attach-existing-CDP and still-block-without-CDP branches in `learning_agent/tests_support/legacy_learning_agent_suite.py`.
- Diagnostic follow-up: `diagnose_real_chrome_environment()` now treats “9222 occupied by trusted Chrome CDP” as `available`, so `mcp-doctor` no longer says users must close Chrome when the current visible browser is already attachable.
- Acceptance result: visible terminal run `real_chrome_natural_weather_travel-20260530_144214` completed successfully with `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`, `real_chrome_connected=true`, browser action evidence, and `permission_sent_count=0`.
- Maintenance note: future agents should preserve the distinction between unknown port conflict and trusted existing Chrome CDP; the former should remain a safety stop, the latter should attach without closing Chrome.

## 2026-05-30 Stage 14 hard cleanup context

- User goal: make the project look like pure new architecture for users and maintainers, with no old entry-point confusion.
- Current unique user-visible path: `start_oauth_agent.bat` -> `start_oauth_agent.ps1` -> `learning_agent.py` -> `app.cli.main()` -> `core.agent.LearningAgent`.
- Current test path: `python -m unittest discover learning_agent`; focused tests live under `learning_agent/tests/test_*.py`.
- Removed old surface: `learning_agent/test_learning_agent.py`, `learning_agent/tests/_legacy_groups.py`, `learning_agent/tests_support/legacy_learning_agent_suite.py`, `learning_agent/tests_support/`, and `learning_agent/acceptance_harness.py`.
- Removed source-tree artifact directories after validation: `learning_agent/test/`, `learning_agent/debug_logs/`, and `learning_agent/browser_artifacts/`.
- Stage 14 validation passed: compileall, AST unreachable scan, compat cleanup tests, full unittest discovery, and real visible terminal Chrome acceptance.
- Stage 14 acceptance evidence: `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/result.json` with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Browser screenshot evidence from the fresh run was copied into `browser_artifacts_snapshot` inside that run directory before the source-tree `browser_artifacts/` directory was deleted again.
