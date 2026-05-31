# 问题与风险记录

## 2026-05-31 H 盘运行路径错位风险

状态：已修复当前路径错位；仍需另行处理浏览器测试环境中的 Playwright 依赖缺失。

已确认风险：
- 当前项目实际运行目录为 `H:\codexworkplace\sofeware\OpenHarness-main`，但 `learning_agent/mcp_servers.json` 仍指向 `D:\codexworkplace\software\OpenHarness-main\learning_agent`。
- 如果不修复，`mcp-doctor` 或真实 agent 启动 MCP server 时会尝试执行 D 盘旧路径，导致当前 H 盘项目的 browser/search/workspace tools 可能启动失败或启动到旧副本。
- `AGENTS.md` 和 `agent_memory/context.md` 中的 D 盘路径会误导后续 agent 把学习备份、真实终端验收或项目根定位到错误目录。

处理策略：
- 只改当前运行配置和协作上下文路径。
- 不批量改历史验收日志，因为旧日志中的 D 盘路径代表历史运行证据，改掉会污染证据。

验证结果：
- `mcp-doctor` 已确认当前工作区、配置文件和 MCP server 启动路径均来自 H 盘项目。
- 当前活跃配置范围内已搜不到旧 OpenHarness D 盘路径。

剩余环境风险：
- `learning_agent.tests.test_mcp_registry` 中 2 个浏览器自动化测试仍失败，失败原因是运行环境缺少 Playwright：`No module named 'playwright'`。
- 该风险会影响浏览器自动化单元测试，但本次 `mcp-doctor` 已证明 H 盘 MCP 配置本身能解析并启动。

## 2026-05-30 阶段 13B 旧脚本入口收紧风险记录

已处理风险：
- 旧风险：`tests_support/legacy_learning_agent_suite.py` 继续从旧脚本入口大导入，导致测试套件会倒逼 `learning_agent.py` 保留批量 re-export。
- 已处理：遗留测试套件已改为按 `app/core/models/mcp/tools` 分层导入，测试关注点不再绑定旧脚本入口。
- 旧风险：`fake_model_repl.py` 继续示范从旧脚本入口导入 `LearningAgent` 和消息对象，后续开发者容易照抄旧路径。
- 已处理：假模型 REPL 已改为从 `core.agent` 与 `core.messages` 导入。
- 旧风险：`learning_agent.py` 用 `vars(agent_module).items()` 和 `globals()[exported_name]` 批量导出 `core.agent`，让薄入口继续看起来像巨型公共 API。
- 已处理：`learning_agent.py` 已收紧为只启动 `app.cli.main()` 的脚本入口，`__all__` 只公开 `main`。

剩余风险：
- `core/agent.py` 仍然很大，下一阶段应继续拆 run loop、状态对象和工具调度委托，避免只是把巨型入口转移到核心文件。
- 历史学习备份目录 `learning_agent/test/**` 仍保留旧入口字符串，这是归档学习材料，不应作为活跃生产路径修改；扫描活跃代码时需要排除备份目录。
- 当前验收阻塞：真实可见终端验收 `real_chrome_natural_weather_travel-20260530_111154` 被 Codex OAuth/API HTTP 429 `usage_limit_reached` 阻塞，agent 没有机会调用真实浏览器工具；需要额度恢复后重跑验收。
- 备用链路风险：`LEARNING_AGENT_MODEL_PROVIDER=codex` 可找到本机 `codex.exe`，但一次性 run 在 `codex exec` 90 秒超时；当前不能依赖该 provider 绕过 OAuth/API 429 完成真实终端验收。

## 2026-05-30 阶段 13 旧入口回流风险记录

已处理风险：
- 旧风险：`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py` 和包门面仍导入 `learning_agent.learning_agent`，导致“已经拆模块”但生产路径仍回到旧入口。
- 已确认根因：工具 schema 和工具包装 helper 的事实源仍在旧入口/核心文件附近，导致多个模块为了拿 `TOOL_SCHEMAS` 或 helper 只能回连旧入口。
- 已处理：把内置工具 schema 与能力包映射迁移到 `tools/schemas.py`，并让生产模块直接依赖新事实源。
- 已处理：新增 `tests/test_compat_cleanup.py`，静态扫描上述生产模块，防止它们再次出现 `learning_agent.learning_agent` 导入。

剩余风险更新：
- 阶段 13B 已处理 `learning_agent/learning_agent.py` 批量 re-export 和 `tests_support/legacy_learning_agent_suite.py` 旧入口导入问题。
- `core/agent.py` 仍很大，虽然 schema 和脚本入口已收紧，但 `LearningAgent` 主类仍承载大量 run loop、工具调度、观测和兼容方法；后续应继续拆 `core/run_loop.py`、`core/state.py`、`observability` 委托方法和剩余死代码。
## 2026-05-30 Stage12 Core Agent Split 风险与处理

已处理风险：
- 旧风险：阶段 12 只删除部分不可达代码时，`learning_agent.py` 仍会保留几十万字节核心实现，排查者仍然需要翻主入口，瘦身目标不成立。
- 已处理：`LearningAgent` 主实现整体迁入 `learning_agent/core/agent.py`，`learning_agent.py` 现在只做路径兜底、兼容 re-export 和 `main()` 转发。
- 旧风险：同目录 MCP server 以脚本方式运行时，Python 可能先加载 `learning_agent.py` 顶层模块，导致 `learning_agent.browser_real_chrome` 等子模块导入失败。
- 已处理：薄入口设置 `__path__`，`core/__init__.py` 也保留脚本模式 fallback；已用 `browser_automation_mcp_server.py` 和 `mcp-doctor` 链路验证。
- 旧风险：`core/agent.py` 从包根迁到 `core/` 后，原先按 `Path(__file__).with_name("skills")` 找 packaged skills 的逻辑会误找 `learning_agent/core/skills`。
- 已处理：packaged skill fallback 改为从包根 `learning_agent/skills` 查找，`test_prompts_context` 与完整回归已覆盖。
- 旧风险：真实可见终端验收中，Windows 受限环境让 `tasklist` 返回 Access denied，`ChromeProfileManager.chrome_is_running()` 把检测失败误判为 Chrome 正在运行，导致 `browser_connect_real_chrome` 被阻断。
- 已处理：`chrome_is_running()` 在 `tasklist` 非零退出时改用 PowerShell `Get-Process chrome` 复查；如果 fallback 明确没输出，则不再误报 Chrome 运行中；新增回归测试覆盖该场景。
- 旧风险：同一环境下 Python `Path.exists()` 读取 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data` 抛 `PermissionError`，导致 `mcp-doctor` 误报 User Data 缺失。
- 已处理：`_existing_path()` 在 Python 路径检查被拒绝时调用 PowerShell `Test-Path` 只读确认，且修复了 `powershell -Command` 下 `$args[0]` 不能稳定传递带空格路径的问题；新增回归测试覆盖带空格 User Data 路径。
- 已验证：`mcp-doctor` 恢复为真实 Chrome profile `available`，并且真实可见终端验收 `real_chrome_natural_weather_travel-20260530_025500` 通过，`permission_sent_count=0`。

剩余风险：
- `core/agent.py` 仍是核心大文件，虽然主入口已经瘦身，但下一轮若继续追求更细颗粒度，可按工具副作用编排、run loop、权限交互、task 编排继续从 `core/agent.py` 内部拆出更小模块。
- 真实 Chrome 环境诊断仍依赖本机 Windows 权限、Chrome 是否正在运行、User Data 是否被锁定和调试端口是否可用；后续如果换机器或换 Windows 权限策略，仍应先跑 `mcp-doctor` 和真实可见终端验收确认。


## 2026-05-29 Modular Tests Layer 风险与处理

已处理风险：
- 旧风险：`learning_agent/test_learning_agent.py` 超过 1MB，所有测试都在一个类里，排查模型层、MCP 层、浏览器层、权限层或提示词层问题时必须翻巨大文件。
- 已处理：阶段 11 新增八个领域测试入口，日常可以按 `learning_agent.tests.test_mcp_registry`、`learning_agent.tests.test_browser_harness` 等路径聚焦运行。
- 旧风险：直接把旧测试文件搬到 `tests_support` 后，大量 `Path(__file__)` 会指向错误目录，导致 staticprompt、skills、MCP server 脚本和 README 文档测试找不到文件。
- 已处理：阶段 11 在 legacy suite 中新增 `LEGACY_TEST_ROOT` 和 `LEGACY_PROJECT_ROOT`，并机械替换旧路径表达式。
- 旧风险：`python -m unittest discover learning_agent` 以目录作为 start_dir 时，会把 `learning_agent.py` 当成顶层模块，遮蔽 `learning_agent` 包名，导致 `learning_agent.tests` 和 `learning_agent.tests_support` 导入失败。
- 已处理：新测试模块使用相对导入；legacy suite 在目录 discovery 模式下强制把项目根放到 `sys.path` 最前，并清理非包的 `learning_agent` 遮蔽模块。

剩余风险：
- 阶段 11 是“低风险分组入口拆分”，遗留测试方法主体仍集中在 `tests_support/legacy_learning_agent_suite.py`；以后若要做到真正每个测试方法物理迁移到对应文件，还需要进一步分批搬迁。
- 当前分组依赖测试方法名关键字，新增测试如果命名不清楚会落入 `core_run_loop` 兜底组；后续新增测试时应使用明确领域关键词。
- 旧入口和 discovery 已通过自动化测试，但阶段 12 完成后仍需要重新跑全量测试，因为删除主文件重复实现可能影响导入兼容。

## 2026-05-29 Modular App Layer 风险与处理

已处理风险：
- 旧风险：CLI 参数解析、OAuth/API 模型构造、`mcp-doctor`、HTTP command bridge 和真实终端主循环全部堆在 `learning_agent.py` 里，启动类问题很难判断属于 app 入口层、模型层、MCP 层还是浏览器层。
- 已处理：阶段 10 新增 `learning_agent/app/cli.py`、`learning_agent/app/doctor.py`、`learning_agent/app/http_bridge.py` 和 `learning_agent/app/interactive.py`，把应用入口编排从主文件迁出。
- 旧风险：如果 app 层直接导入 `LearningAgent`，会和 `learning_agent.py` 的兼容导出形成循环导入。
- 已处理：`app.cli.main()` 使用 `agent_cls` 和 `permission_callback` 参数注入，主文件只负责传入真实类和真实权限回调。
- 已处理：`python learning_agent\learning_agent.py --help`、`mcp-doctor`、`run --prompt "ping" --json --max-turns 1`、`-k command_bridge` 和完整 `unittest` 均已通过，说明旧入口兼容仍可用。

剩余风险：
- `learning_agent.py` 里仍保留 app/main/bridge/model/format 的旧实现体；它们现在位于早返回之后，不再作为真实执行路径，但阶段 12 瘦身时需要删除这些不可达重复代码。
- `mcp-doctor` 的真实 Chrome 诊断仍会受本机 Chrome 是否运行、User Data 是否可访问、9222 端口是否被占用影响；这属于本机环境状态，不是阶段 10 app 拆分导致的失败。
- 阶段 10 已完成自动化验收，但最终整体任务仍必须在阶段 12 后重新完成 `start_oauth_agent.bat` 真实可见终端交互验收，才能声明整体改造完成。

## 2026-05-27 Acceptance Harness 风险与处理

已处理风险：
- 旧风险：外部 agent 只能靠固定等待、SendKeys 和截图猜测 `learning_agent` 真实终端处于哪个阶段，容易把 prompt 输进权限提示或启动阶段。
- 已处理：新增 JSONL 状态事件和终端标记，外部 agent 可以等待 `permission_required`、`agent_ready_for_user_prompt`、`final_answer_printed` 后再行动。
- 旧风险：权限提示无法被外部 agent 稳定识别，脚本只能循环发送 `y`，可能污染主 prompt。
- 已处理：权限函数现在发出 `permission_required` 和 `permission_answered`，可见终端 smoke 脚本只对新权限请求发送一次 `y`。
- 已处理：第一次可见终端 smoke 中裸 `SendKeys("y~")` 没有进入 Windows Terminal 输入行；脚本已改为优先聚焦真实 Windows Terminal 窗口，并用剪贴板粘贴 `y` 再回车。
- 已处理：最终版可见终端 smoke 曾出现 ready 后 prompt 偶发没有进入 agent 的情况；脚本已改为等待 `user_prompt_received`，若 12 秒内未确认则最多重发 3 次 prompt。
- 已处理：PowerShell 5.1 会把无 BOM 的 UTF-8 中文脚本读坏；本轮 smoke 脚本已转换为 UTF-8 BOM 后运行。

剩余风险：
- 可见终端截图在 Windows Terminal 滚动缓冲区中仍可能停留在启动日志附近，未必总能直接截到最终回答；本轮已用真实窗口输入、`final_answer_printed` 事件、`answer_preview`、调试日志和结果 JSON 交叉确认最终输出。
- `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG` 开启后会记录 prompt 和 answer 的短预览；这是验收模式的有意设计，不应在含敏感内容的人工会话中随意开启。
- 浏览器上传/下载单测在一次完整回归中出现过空下载文件的偶发失败，随后单测连续复跑和完整回归均通过；后续若重复出现，应单独固化为浏览器下载时序问题排查。

## 2026-05-27 重庆天气真实可见终端验收风险记录

已确认的健康状态：
- `run_chongqing_weather_visible_terminal_acceptance.ps1` 已成功通过真实可见终端验收，不是 CLI run、HTTP bridge、stdin 管道或只看日志替代。
- 事件日志确认真实窗口中经历了启动 MCP 授权、ready、prompt received、`browser_open` 授权、`browser_snapshot` 授权和 final answer。
- 调试日志确认 `browser_open 成功` 和 `browser_snapshot 成功`，并读取到 Open-Meteo JSON。
- 结果 JSON 的 `log_checks` 全部为 `true`，包括 `browser_open`、`browser_snapshot`、目标日期、城市、来源和旅游攻略。

剩余风险：
- Open-Meteo 预报会随时间刷新，本轮 2026-05-27 22:50 左右读到的重庆 2026-05-30 数值以后可能变化。
- 可见终端截图受 Windows Terminal 滚动位置影响，可能不能完整展示长回答；本轮以事件日志、调试日志和结果 JSON 作为主要机器证据，截图作为可见窗口辅助证据。
- 脚本目前是验收脚本，不是长期产品化 UI 控制器；后续若要做多场景回归，应把窗口控制、事件等待、权限响应和结果断言继续抽成可复用测试库。

## 2026-05-27 Acceptance Controller 风险与处理

已处理风险：
- 旧风险：smoke 和重庆天气验收分别有独立 PowerShell 脚本，窗口控制、权限响应、截图和结果判断重复，后续场景越多维护越难。
- 已处理：新增 `acceptance_controller/controller.ps1`，把真实窗口控制和事件协议统一到一个控制器里。
- 已处理：新增场景 JSON，把任务 prompt、必需事件、调试日志断言和最终回答断言从脚本里抽出来。
- 已处理：新增测试锁定 controller 目录结构和场景 JSON 基本字段，防止后续又退回一堆专用脚本。
- 已处理：controller 版 smoke 和重庆天气场景均已通过真实可见终端验收，证明新控制器能替代旧专用脚本完成核心任务。

剩余风险：
- `controller.ps1` 仍是 PowerShell 实现，适合当前 Windows 可见终端验收；如果未来要跨平台或更复杂 UI 自动化，建议再抽一层 Python/Node 控制库或专用 MCP。
- 当前 controller 自动输入权限默认是对每个 `permission_required` 发送 `y`，适合受控验收场景；真实高风险场景需要给 scenario 增加允许/拒绝策略。
- 当前断言主要依赖事件日志和 debug log 的文本包含检查；后续可升级为结构化 tool-call ledger，让断言更精确。

## 2026-05-27 Real Chrome Profile Status 风险与处理

已处理风险：
- 旧风险：用户明确要求“桌面可见 Chrome、登录态、标签页和插件”后，如果直接让 agent 连接真实 Chrome，可能触碰 cookies、localStorage、sessionStorage、token、登录页面、隐私标签页或插件状态。
- 已处理：新增 `real_chrome_profile_status.json` 安全探针场景，本轮只允许读取真实 Chrome 规则和调用只读 `browser_profile_status`。
- 已处理：场景 prompt 明确禁止打开登录网站、读取 cookies/storage/token、访问隐私页面、读取标签页内容或插件内容。
- 已处理：结构测试要求 real Chrome 场景必须包含 `browser_profile_status` 和“不读取 cookies”等边界，避免后续场景被改成直接接管真实浏览器。
- 已处理：真实可见终端验收确认目标 agent 只调用了 `mcp__browser_automation__browser_profile_status`，最终回答也说明未连接真实 Chrome、未读取隐私内容。

剩余风险：
- 本轮证明的是 profile status 安全探针可用，不等于已经完成“使用用户登录态、已有标签页和插件”的端到端浏览器自动化。
- `mcp-doctor` 显示当前 Chrome 未运行；下一步若要真实连接日常 profile，需要用户明确确认高风险边界，并可能需要启动带本机 CDP 调试端口的 Chrome。
- 当前 controller 默认自动同意权限；真实 Chrome connect 属于高风险工具，后续场景应给权限策略增加“只自动同意 status，connect 必须人工确认或专门白名单”的保护。
- `browser_profile_status` 返回的是当前 MCP 会话状态摘要，不读取 Chrome profile 文件；它不能证明某个具体登录网站已可操作，只能证明安全前置流程和环境状态可用。

## 2026-05-28 Real Chrome Connect Public Page 风险与处理

已处理风险：
- 旧风险：controller 对每个 `permission_required` 都自动输入 `y`，一旦真实 Chrome 场景里模型请求 `browser_evaluate`、tabs、network、downloads 等权限，就可能越界读取敏感浏览器状态。
- 已处理：`controller.ps1` 已支持 `permission_policy`，connect 场景设置 `default_response=deny`，只对白名单权限自动输入 `y`。
- 已处理：`result.json` 现在记录 `permission_policy_decisions`，可复盘每个权限请求为什么被允许或拒绝。
- 已处理：`real_chrome_connect_public_page.json` 明确禁止 `browser_evaluate`，并在 deny list 中拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已处理：真实可见终端验收确认本轮只调用了 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，未调用 `browser_evaluate`。
- 已处理：第一次 connect 场景失败不是权限策略或 Chrome 连接失败，而是目标 agent 在 status 后的第 4 轮模型调用长时间无返回；已收窄 prompt，第二次验收通过。
- 已处理：本轮测试启动的 Chrome 进程已在验收后清理，避免后续真实 Chrome connect 因 Chrome 正在运行而失败。

剩余风险：
- 真实 Chrome connect 已能打开公开页面，但这仍不等于已经安全操作用户已有登录网站、已有标签页或插件；下一步若要接管已有标签页，需要单独设计更细的用户确认和标签页选择机制。
- 当前 `permission_policy` 是基于权限 action 文本包含匹配；它比无脑同意安全很多，但仍不如结构化 tool-call ledger 精确，后续可把工具名和参数单独写入 acceptance event 便于严格匹配。
- `browser_connect_real_chrome` 需要 Chrome 运行前为空；如果用户手动打开了 Chrome，工具会按设计拒绝并提示先关闭当前 Chrome。
- `browser_snapshot` 会读取当前公开页面文本；本轮 URL 是 `https://example.com`，后续如果 URL 换成登录站点或私人页面，必须重新评估隐私边界。

## 2026-05-28 Real Chrome Chongqing Weather Travel 风险与处理

已处理风险：
- 旧风险：真实 Chrome connect 只在 `example.com` 公开页 smoke 级别跑通，还不能证明目标 agent 能在真实 Chrome 中完成有实际信息查询价值的任务。
- 已处理：新增 `real_chrome_chongqing_weather_travel.json`，在真实桌面 Chrome 中连接 profile 后打开公开 Open-Meteo URL，读取重庆 2026-05-31 天气 JSON 并生成旅游攻略。
- 已处理：场景继续使用 `permission_policy default_response=deny`，只对白名单工具自动输入 `y`，拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已处理：真实可见终端验收确认本轮只调用了 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，没有读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容或插件内容。
- 已处理：验收前 `mcp-doctor` 确认 Chrome 未运行，验收后清理本轮测试启动的 Chrome 进程，并再次确认 Chrome 正在运行为 `false`。

剩余风险：
- Open-Meteo 预报会随时间刷新，本轮 2026-05-28 06:10 左右读到的重庆 2026-05-31 数值以后可能变化。
- 当前场景访问的是公开天气 API，不是用户登录网站；它证明真实 Chrome 可以执行受控公开查询任务，但仍不等于已经安全操作用户已有登录态页面、已有标签页或插件。
- 权限策略仍基于 action 文本包含匹配；对当前白名单场景足够可审计，但后续更复杂登录态任务仍建议升级为结构化 tool-call ledger 匹配工具名和参数。

## 2026-05-28 Structured Permission Ledger 风险与处理

已处理风险：
- 旧风险：`permission_policy` 主要基于 action 文本包含匹配，`browser_open` 一旦被 contains 放行，就难以精确限制 URL 参数。
- 已处理：`permission_required` / `permission_answered` 事件现在带结构化 `tool_name`、`arguments`、`risk_level`、`risk_summary`，controller 可以按工具名和参数做决策。
- 已处理：`real_chrome_chongqing_weather_travel.json` 已改为结构化工具白名单，`browser_open` 必须同时命中工具名白名单和 Open-Meteo URL 前缀。
- 已处理：真实可见终端验收确认 `browser_open` 决策原因为 `allow_tool_name_and_url_prefix`，不是旧的 `allow_contains`。
- 已处理：`permission_policy_decisions` 已记录结构化参数和风险摘要，后续可复盘每个 `y/n` 为什么发生。

剩余风险：
- 当前结构化 payload 是从人类可读权限文本解析出来的，而不是从 `_execute_mcp_tool()` 直接传对象到权限函数；它已经满足当前控制器精确匹配，但未来最好把权限回调升级为对象接口，避免依赖提示文本格式。
- `allow_url_prefixes` 目前只对 `mcp__browser_automation__browser_open` 做前缀校验；以后若其它工具也带 URL 或路径参数，需要扩展通用参数规则。
- 结构化策略已经适合公开网站查询验收，但进入真实登录网站、已有标签页或插件控制前，仍需要新增人工选择目标页和更严格的字段级白名单。

## 2026-05-27 重庆天气浏览器自动化测试风险记录

已确认的健康状态：
- 目标 agent 在 CLI 真实大模型路径中成功读取 `tool_list.md` 和 `browser_automation/SKILL.md`。
- 目标 agent 成功调用 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- `mcp-doctor` 显示 `browser_automation` MCP server 启动成功，模型可见 MCP 工具 30 个。

剩余风险：
- 本轮通过 CLI `run --prompt --json` 驱动目标 agent，并通过日志确认浏览器 MCP 工具调用；这不能替代用户本地可见终端窗口中的 `start_oauth_agent.bat` 人工交互验收。
- CLI 输出文件 `learning_agent/test/chongqing_weather_browser_20260527/cli_run_output.txt` 可能因为 Windows 管道编码显示中文乱码；可信中文证据以 `learning_agent/debug_logs/latest_run_readable.md` 为准。
- Open-Meteo 预报会随时间刷新，2026-05-30 重庆天气数值代表本轮查询时返回结果，后续复测可能有小幅变化。

## 2026-05-27 learning_agent 当前剩余风险评估

已确认的健康状态：
- 当前完整单元测试通过：`Ran 332 tests in 28.030s OK (skipped=1)`。
- 当前 MCP doctor 通过：`browser_search`、`workspace_tools`、`browser_automation` 均可启动，真实 Chrome profile 诊断为 `available`。

剩余风险：
- 本轮是分析评估，不是新增功能开发；没有启动用户本地可见的 `start_oauth_agent.bat` 交互窗口做真实人工 prompt 验收，因此不能把本轮称为“开发完成验收”。
- `last_unittest_output.txt` 当前保存的是旧失败输出，和当前重新运行的测试结果不一致；后续若引用测试状态，应优先看新运行命令输出或重新生成该日志，不能把旧文件当当前事实。
- `learning_agent.py` 已超过 1MB，虽然有大量中文教学注释和测试保护，但长期维护成本较高；后续继续扩展时应优先拆模块或沉淀 skill/hook，不宜继续把新能力堆进主文件。
- `mcp-doctor` 证明真实 Chrome profile 环境可用，但不等于已在本轮实际连接用户真实 Chrome 登录态；涉及登录态时仍要走 profile status、明确授权和真实交互验收。

## 2026-05-26 Prompt Files v3 风险与处理

已处理风险：
- 旧风险：静态系统提示词仍散落在 `learning_agent.py` helper 中，用户后续编辑和审计都不方便。
- 已处理：静态系统提示词已迁移到 `learning_agent/staticprompt/staticprompt.md`，源码只负责读取和兜底。
- 旧风险：动态运行规则文件名仍叫 `runtime_instructions.md`，容易被误解为每轮 runtime 常驻提示词。
- 已处理：旧文件已迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，并通过测试锁定旧路径不再存在。
- 已处理：`dynamicprompt.md` 不进入首轮 system prompt，但可通过 `skill_load name=dynamicprompt` 按需加载，避免“动态规则不可见”的新风险。

剩余风险：
- 如果用户把 `staticprompt/staticprompt.md` 改得过长，仍可能重新增加每轮上下文；当前代码有 12000 字符兜底截断，但更好的做法是继续把流程规则下沉到 skill。
- 如果未来继续扩写 `dynamicprompt/dynamicprompt.md`，它虽然不常驻，但按需加载时仍可能过长；应优先拆分成更小的 skill 或 capability pack 说明。

## 2026-05-26 Lean System Prompt v2 风险与处理

已处理风险：
- 旧系统提示词过大，且 `Tool Boundary / 工具边界`、`Response Policy / 输出策略` 这类细节每轮固定加载，和用户希望精简 prompt surface 的方向冲突。
- 已处理：默认系统提示词只保留短核心身份、行为原则、上下文策略和 Prompt Surface Policy；细节规则迁移到 `dynamicprompt/dynamicprompt.md` 和 skill/capability pack。
- 已处理：旧测试依赖 `prompt.policy.response` 默认加载；当前已改为断言核心身份 block 加载，避免测试把旧大 prompt 形态固化。
- 已处理：完整回归发现 `知识与实时信息策略` 锚点丢失；当前把该锚点作为 runtime 小标题保留，不把实时信息细则重新塞回核心系统身份。
- 已处理：`agent_memory` 三件套过长；当前已复制旧全文到 `agent_memory/archive/2026-05-26-lean-system-prompt/`，活跃文件改为短摘要。

剩余风险：
- `prompt.policy.tool_boundary` 和 `prompt.policy.response` 的 helper 仍在源码中保留；这不影响默认每轮加载，但后续若注册表或测试误把它们重新加入 `block_contents`，提示词可能再次变大。
- `dynamicprompt/dynamicprompt.md` 仍承担很多工具关键词索引职责；如果继续往里堆长流程，应优先拆成独立 skill。
- `token_budget_report` 使用粗略 token 估算；最终预算判断仍应以真实模型 tokenizer 或运行时报告为准。
- 活跃 `agent_memory` 只保留摘要；需要旧细节时必须读取 `agent_memory/archive/2026-05-26-lean-system-prompt/` 下的归档文件。

## 2026-05-26 Dynamic Runtime Rules 风险与处理

已处理风险：
- 旧风险：`runtime_instructions.md` 虽然已缩短，但仍作为每轮 system prompt 正文加载，和用户希望“静态系统提示词 + 动态运行规则提示词”的结构不一致。
- 已处理：`_build_initial_messages()` 不再传入 `context.runtime_instructions`，运行时规则正文不再常驻。
- 已处理：必要底线已合并到静态系统提示词，避免 runtime 未加载时模型第一步走偏。
- 已处理：包内能力包 skills 以前不能被空工作区的 `skill_list` / `skill_load` 发现；当前已增加包内默认 skills fallback。

剩余风险：
- `dynamicprompt/dynamicprompt.md` 仍是单个动态索引文件；如果未来规则继续变长，应进一步把关键词索引拆到更小的 rule pack 或 skill metadata。
- 静态系统提示词仍需保留少量动态加载路由关键词；如果删得过狠，模型可能不知道何时调用 `skill_load` 或 `tool_search`。

## 2026-05-26 Prompt Files v3 最新风险

- 最新剩余风险：`staticprompt/staticprompt.md` 现在是每轮常驻入口，后续扩写它会直接增加每轮上下文。
- 最新剩余风险：`dynamicprompt/dynamicprompt.md` 虽然不常驻，但按需加载时仍可能过长，后续应优先拆成独立 skill。
- 最新已处理：旧 `runtime_instructions.md` 路径已删除，避免用户面对两个动态规则入口。

## 2026-05-26 Agent Memory Boundary 风险与处理

已处理风险：
- 旧风险：目标 `learning_agent` 会自动读取 Codex 开发用 `agent_memory/context.md`、`progress.md`、`bugs.md`，导致用户 agent 每轮 prompt 被开发会话记忆污染。
- 已处理：目标 agent 的 `_build_initial_messages()` 现在只默认加载 `staticprompt/staticprompt.md` 和 `memory.md` 索引，不再查找工作区或父目录的 `agent_memory`。
- 已处理：静态提示词已删除三件套路径说明，避免模型误以为这些文件属于目标 agent 的运行时上下文。

剩余风险：
- Codex 开发本项目仍会维护 `agent_memory` 三件套，但这只是开发协作记忆；后续不能再把它接回目标 agent 的默认 prompt surface。

## 2026-05-26 Four Atom Tool Surface 风险与处理

已处理风险：
- 旧风险：首轮仍暴露 `tool_search`、`skill_load` 等 kernel 工具，会让用户希望的极简 Tool Pool 继续膨胀。
- 已处理：`KERNEL_TOOL_NAMES` 已收敛为 `read`、`write`、`edit`、`bash`，完整测试锁定首轮 Tool Pool 只含四原子工具。
- 旧风险：`staticprompt.md`、`dynamicprompt.md`、README 和 fallback static prompt 仍可能把模型引回 `tool_search` / `select_pack` 旧路由。
- 已处理：静态提示词、动态提示词、README 和 fallback static prompt 都已改为通过 `learning_agent/skills/tool_list.md` 做 read-based skill discovery。
- 旧风险：README 与真实代码不一致，学习者会以为旧 select 流程仍是默认主路径。
- 已处理：README 已同步说明四原子首轮工具面，旧 skill/tool 入口只作为内部兼容能力保留。

剩余风险：
- `TOOL_SCHEMAS` 仍保存所有历史工具 schema，虽然默认不进首轮 Tool Pool，但后续维护者若误改 `KERNEL_TOOL_NAMES` 或 `build_builtin_tool_catalog()`，可能再次扩大模型首轮工具面。
- `dynamicprompt/dynamicprompt.md` 仍保留大量内部能力关键词索引；它不常驻，但按需读取时仍可能比较长，后续应继续拆成更小的 skill 文件。
- 四原子 `bash` 直接执行 shell 命令，虽然有权限确认、cwd 边界和超时限制，后续仍应持续强化命令风险提示和 Windows/类 Unix 兼容验证。

## 2026-05-26 CLI / HTTP Command Bridge 风险与处理

已处理风险：
- 旧风险：目标 agent 只有人工交互入口，Codex 难以稳定启动、下发任务和接收结果，真实调试场景无法闭环。
- 已处理：新增 CLI `run --prompt ... --json`，stdout 可返回结构化 JSON，方便 Codex 或脚本直接接收。
- 已处理：新增本机 HTTP command bridge，支持探活和运行命令，能复用同一个 agent 进程做连续调试。
- 已处理：bridge 默认建议绑定 `127.0.0.1`，并支持可选 token，避免一开始就把控制接口暴露成无保护远程入口。
- 已处理：HTTP `POST /run` 通过锁串行化 `agent.run()`，降低并发请求同时修改同一个 agent 状态的风险。

剩余风险：
- HTTP bridge 当前是标准库最小实现，不是生产级认证、TLS 或多用户权限系统；真实远程使用前必须加外层安全边界。
- bridge 使用同一个进程内 agent 状态，适合调试和连续控制，但不适合无隔离的多租户并发任务。
- CLI `--json` 运行仍会真实构造模型和 MCP registry；如果真实模型或 MCP 配置有问题，JSON 结果可能返回错误或启动阶段失败，后续可继续强化错误 JSON 包装。

## 2026-05-26 Dynamic Prompt Tree 风险与处理

已处理风险：
- 旧风险：动态提示词虽然不常驻，但所有细节都堆到 `SKILL.md` 后，按需读取某个 skill 时仍可能把大量无关流程塞进上下文。
- 已处理：每个顶层 `SKILL.md` 已改成轻入口，细节下沉到 `rules/*.md`，只在具体场景需要时继续读取第三层。
- 旧风险：包内 skills 仍包含 `tool_search` / `select_pack` 旧路由，会和四原子首轮工具面冲突。
- 已处理：包内 skills 已清理旧路由文案，并用测试锁定顶层 `SKILL.md` 不再出现这两个关键词。
- 旧风险：模型知道路径时可以直接 `read learning_agent/skills/<skill>/rules/*.md`，绕过父索引，导致分层只停留在提示词约定。
- 已处理：`read` 原子工具已新增层级门控，未先读 `tool_list.md` 和父 `SKILL.md` 时会返回可恢复提示。

剩余风险：
- `dynamicprompt/dynamicprompt.md` 仍保留内部能力关键词索引，虽然不常驻，但用户若主动读取它仍会看到较多关键词；后续可以继续拆成更小的规则索引。
- `skill_load` 作为内部兼容工具仍可直接加载 `SKILL.md`，但它不在首轮模型可见工具池中；后续若完全移除旧兼容入口，需要同步清理相关历史测试。
- 当前 read 层级门控只覆盖 workspace 内 `learning_agent/skills` 或 `skills` 路径；MCP prompt 或外部资源的层级加载仍依赖各自工具规则。

## 2026-05-26 Current Date Prompt 风险与处理

已处理风险：
- 旧风险：`learning_agent/staticprompt/staticprompt.md` 只能写稳定文本，无法让 agent 每天自动知道真实日期。
- 已处理：静态提示词新增 `{{CURRENT_DATE}}` 占位符，运行时每轮由 `get_local_iso_date()` 替换成本机当天日期。
- 旧风险：如果只在静态提示词里写死某一天日期，第二天以后 agent 会拿到过期日期。
- 已处理：具体日期不写进静态文件，单测和 CLI 验证都确认 system prompt 中出现运行时日期 `2026-05-26`。
- 旧风险：静态提示词文件缺失或损坏时 fallback prompt 可能没有日期上下文。
- 已处理：fallback static prompt 同步写入当前日期。

剩余风险：
- 当前实现满足“每轮看到今天日期”，但没有实现 ClaudeCode 的 `date_change` attachment；如果未来要在超长会话里专门通知跨午夜变化，可以再增加 last emitted date 状态和日期变化附件。
- 日期使用本机本地时区的 `date.today()`；如果未来需要固定用户时区或 UTC，需要增加显式时区配置。

## 2026-05-26 Browser Automation 风险与处理

已处理风险：
- 旧风险：四原子工具面移除 `tool_search` 后，browser MCP 工具虽然在 catalog 中，但模型读取 browser skill 后没有办法把 `browser_open` 等工具加入 Tool Pool。
- 已处理：新增 read-based dynamic skill unlock，读取 `browser_automation/SKILL.md` 后加载 `browser_automation` 能力包，且单测覆盖实际 MCP 调用。
- 旧风险：真实 Chrome connect 如果只靠读取 skill 直接暴露，会跳过 profile status 安全检查。
- 已处理：读取 `real_chrome/SKILL.md` 只准备工具并满足 skill gate，connect 仍要等 `browser_profile_status` 完成后才可见。
- 旧风险：真实 Chrome 路线如果未设置 `real_chrome_requested`，可能在连接前误把普通 browser_open 当成替代路径。
- 已处理：读取 `real_chrome/SKILL.md` 会设置 `real_chrome_requested=True`，普通浏览器动作在 `real_chrome_connected` 前继续被 workflow gate 拦住。
- 旧风险：CLI 默认 workspace 是 `learning_agent` 目录，而静态提示词推荐 `learning_agent/skills/tool_list.md`，模型按提示读取会形成 `learning_agent/learning_agent/skills` 错路。
- 已处理：`_resolve_workspace_path()` 已兼容包目录工作区下的项目根风格 `learning_agent/...` 路径，并新增回归测试。
- 旧风险：用户或测试说 `real browser automation` 时，`_detect_real_chrome_intent()` 会把普通真实浏览器自动化误判成真实 Chrome/profile 请求，导致 `browser_open` 被 workflow gate 隐藏。
- 已处理：真实 Chrome 触发词已收窄为真实 Chrome、桌面/可见/当前浏览器或登录态；普通 `real browser automation` 保持走独立 Playwright browser 工具。
- 旧风险：`run()` 调用了不存在的 `_final_answer_retry_message()`，HTTP command bridge 在模型给出最终回答时会返回 500。
- 已处理：已补齐 `_final_answer_retry_message()`，仅在用户明确列出 Markdown 标题且最终回答漏标题时自动重写一次，避免影响普通任务。
- 旧风险：之前只用脚本化假模型验证浏览器工具链，不能证明真实大模型能按 read-based skill 路由完成天气查询和攻略生成。
- 已处理：HTTP bridge 和 CLI run 都已使用真实 `CodexCliChatModel` 完成 Open-Meteo 北京 2026-05-29 查询，日志确认真实调用 `browser_open` 和 `browser_snapshot`。

剩余风险：
- `real_chrome` 路线已通过策略和 doctor 验证 profile status/connect 门控，但本轮没有实际连接用户真实 Chrome profile，避免触碰登录态风险。
- 读取 browser skill 后 Tool Pool 会从四原子扩展到浏览器工具组；这是按需扩展，不影响首轮极简工具面，但浏览器任务期间 schema 会明显增大。
- CLI `--json` 路径在自动喂权限输入并重定向到文件时，Windows 管道输出里的中文权限提示可能出现乱码；真实调试日志 `latest_run_readable.md` 仍是 UTF-8 可读证据，后续可改进 CLI 权限提示和 JSON 输出分流。

## 2026-05-28 Real Chrome Google Human Visible 风险与处理

已处理风险：
- 旧风险：用户希望肉眼看到真实 Chrome 打开 Google、点击输入和回车搜索；之前的真实 Chrome 天气场景直接打开 Open-Meteo URL，不会展示 Google 搜索框里的拟人输入过程。
- 已处理：新增 `real_chrome_google_human_search.json` 场景，强制打开 `https://www.google.com/`，再调用 `browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 旧风险：controller 成功后立即关闭终端，用户可能错过桌面可见 Chrome 演示画面。
- 已处理：controller 新增 `post_success_wait_seconds`，Google 场景成功后停留 20 秒。
- 旧风险：第一次 Google 真实验收中 agent 实际完成了截图和最终回答，但 `final_answer_printed.answer_preview` 只有 500 字，截断在 `- br`，导致 `event_answer_checks.browser_screenshot=false` 并误判失败。
- 已处理：`final_answer_printed` 事件新增完整 `answer_text`；controller 的回答断言改为优先检查完整 `answer_text`，并保留 `answer_preview` 作为摘要。
- 已处理：新增回归测试锁定 `answer_text` 字段和 controller 完整回答断言，避免后续再退回截断预览。

剩余风险：
- Google 页面可能因地区、同意弹窗、异常流量或 CAPTCHA 改变 DOM；场景 prompt 已允许点击同意按钮，但不允许绕过 CAPTCHA，遇到 CAPTCHA 时必须截图并如实失败。
- 本场景只证明公开 Google 页面中的可见点击输入链路，不代表已经安全支持任意登录网站或读取用户私人标签页。
- 真实 Chrome 连接使用日常 profile，必须继续通过默认拒绝权限策略、URL 前缀白名单和禁止 cookies/storage/network/console/evaluate 的边界控制风险。

## 2026-05-28 Real Browser Task Harness 风险与处理

已处理风险：
- 旧风险：用户自然说“请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略”时，旧 `_detect_real_chrome_intent()` 不包含“真实浏览器”短语，会漏判真实 Chrome/profile workflow。
- 已处理：新增 `真实浏览器`、`真实的浏览器`、`真实可见浏览器` 触发词，并用单测锁定自然短 prompt 会进入真实 Chrome 路线。
- 旧风险：只有长 prompt 明确写 `browser_click`、`browser_type`、`browser_press_key` 时，agent 才稳定执行可见 Google 搜索；这不能复用到会议、酒店、航班、资料等普通用户场景。
- 已处理：新增 `Real Browser Task Harness`，在真实浏览器信息查询任务里自动注入通用 Google 首页搜索流程，覆盖会议、酒店、航班、资料、天气、旅游攻略等任务。
- 旧风险：真实 Chrome skill 只有 profile 安全规则，没有把公开信息查询的可见搜索流程沉淀成子规则。
- 已处理：新增 `learning_agent/skills/real_chrome/rules/search_task_workflow.md`，并在 `real_chrome/SKILL.md` 中索引。
- 旧风险：自然短 prompt 验收如果仍把工具步骤写进 prompt，就不能证明 harness 本身能发挥作用。
- 已处理：新增 `real_chrome_natural_weather_travel.json`，第一行保留自然短 prompt，场景测试断言 prompt 不包含“必须使用 browser_click / browser_type”。
- 旧风险：第一次自然短 prompt 真实终端验收中，真实 Chrome 操作已经成功，但最终回答只写中文摘要，没写 `real_chrome_connected=true` 和工具名，导致机器验收误判失败。
- 已处理：harness 和 `search_task_workflow.md` 都要求最终回答包含 `real_chrome_connected=true` 与 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 已处理：失败验收留下的 Chrome 调试进程已通过命令行识别，仅清理带 `--remote-debugging-port=9222` 的测试 Chrome 进程；最终 `mcp-doctor` 确认 Chrome 未运行且端口可用。

剩余风险：
- Google 页面、AI 概览、搜索结果排序和 DOM 会随地区、账号、时间和风控变化；当前场景通过快照、截图和宽松文本断言降低脆弱性，但遇到 CAPTCHA 时仍必须如实失败。
- 目前通用 harness 适合公开网页查询，不等于安全支持操作用户私人标签页、已登录后台、支付、预订或账号设置；这些场景需要更严格的目标页选择、字段级白名单和人工确认。
- 用户真实 Chrome profile 仍是高风险边界，必须继续默认拒绝未知权限，禁止 cookies/storage/token/password/network/console/evaluate，并优先只访问用户明确授权的公开 URL。

## 2026-05-28 Real Browser Customer Mode 风险与处理

已处理风险：
- 旧风险：真实浏览器自然查询任务会在启动 MCP、连接真实 Chrome、打开 Google、快照、点击、输入、回车、等待、截图等每一步都弹 `[y/N]`，真实客户体验很差。
- 已处理：交互式入口使用客户模式权限函数，项目内置 MCP 启动自动允许；真实浏览器公开查询白名单工具在任务级上下文中自动授权，不再调用 `input()`。
- 旧风险：取消所有 y/N 可能误放行 `browser_evaluate`、network、console、tabs、downloads、upload 或任意非授权 URL。
- 已处理：自动授权仅在“真实浏览器 + 公开信息查询”场景启用；只放行公开 Google 查询链路必需工具，敏感工具继续走权限层并可被拒绝。
- 旧风险：无 y 模式可能变成静默执行，用户看不到 agent 下一步在做什么。
- 已处理：自动授权时打印 `Agent > 正在...` 进度行，并记录 `permission_auto_approved` / `mcp_call_progress` 审计事件。

剩余风险：
- 自动授权当前默认允许项目内置 MCP server 启动；如果未来 `mcp_servers.json` 增加新的未知 server，客户模式不会自动允许，需要重新评估白名单。
- 当前 URL 自动授权仅覆盖 Google 公开入口；会议、酒店、航班等任务后续如果需要打开具体结果网站，应新增来源级白名单或短暂人工确认，而不是直接扩大到任意 URL。

## 2026-05-28 YouTube 自然查询仍弹 y/N 风险与处理

已处理风险：
- 旧风险：用户输入“请使用真实浏览器，youtube网站的视频关于ai agent介绍，评论最多的有哪些？”时，真实浏览器动作仍逐步弹 `[y/N]`，说明客户模式没有完全覆盖真实公开查询场景。
- 已确认根因：旧 `_detect_real_browser_information_task()` 未命中该 prompt，因为它没有“查询/搜索/天气/攻略/会议/酒店/航班/资料”等关键词，只包含“youtube网站/视频/评论最多/有哪些”。
- 已处理：将 `网站`、`视频`、`评论`、`最多`、`有哪些`、`哪些`、`哪个`、`排行`、`排名`、`榜单`、`介绍`、`youtube` 加入公开信息查询关键词。
- 已处理：新增 YouTube prompt 红灯测试，先观察到 `_detect_real_browser_information_task()` 返回 `False`，再修复到通过，避免把猜测当结论。
- 已处理：新增 YouTube 自然短 prompt 真实终端场景并完成验收，`permission_sent_count=0`，证明不会再让用户输入多次 `Y`。

剩余风险：
- 已经启动的旧 `start_oauth_agent.bat` 进程不会热加载新代码；用户必须关闭旧终端并重新启动，才能看到 YouTube 场景无 y 的新行为。
- 当前客户模式仍只自动打开 Google 公开入口；如果后续要直接打开 YouTube、酒店官网、航司官网等具体站点，需要按域名单独评估 URL 白名单，不能直接放开任意 URL。
- Google 结果页的评论数摘要可能随地区、账号、时间和搜索排序变化；真实浏览器功能已验收“能查且无 y”，但具体 YouTube 排名结果仍应以当次页面可见内容为准。

## 2026-05-29 模块化阶段 2 验证中发现的稳定性问题

已处理风险：
- 旧风险：`mcp-doctor` 会直接调用真实 Chrome profile 诊断；当 Windows 拒绝访问 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data` 时，`Path.exists()` 抛出 `PermissionError`，导致 doctor 退出码为 1。
- 已确认根因：`browser_real_chrome._existing_path()` 没有捕获路径候选检查期间的 `OSError/PermissionError`，一个不可访问候选会中断整个诊断。
- 已处理：`_existing_path()` 现在把不可访问候选视为不可用候选并继续检查，doctor 会返回结构化诊断而不是崩溃。
- 已新增回归测试：`test_real_chrome_profile_manager_skips_inaccessible_candidates`。
- 旧风险：后台命令测试停止长命令后，Windows 仍报告临时目录“另一个程序正在使用此文件”，导致 `TemporaryDirectory` 清理失败。
- 已确认根因：sandbox 环境下 `taskkill /F /T /PID` 对测试进程返回 `Access denied`；后备 `process.kill()` 只能杀外层 shell，Python 子进程继续持有工作目录和输出管道直到自然 sleep 结束。
- 已处理：后台命令在 Windows 下用 `CREATE_NEW_PROCESS_GROUP` 启动，并优先发送 `CTRL_BREAK_EVENT` 终止进程组；停止后主动关闭 stdio 管道并等待 reader 线程退出。
- 已验证：`test_agent_starts_reads_and_stops_background_command` 从约 30 秒自然结束降到 `Ran 1 test in 0.136s OK`。

剩余风险：
- Windows 受限环境下仍可能拒绝 `taskkill`、CIM 和其它进程枚举接口；后台命令停止逻辑应继续优先使用自身创建的进程组，不依赖全局进程枚举。
- Chrome profile 目录不可访问时，当前诊断会把该候选视为未找到；后续如需更精细用户提示，可以扩展诊断对象记录“存在但不可访问”的候选原因。

## 2026-05-29 模块化阶段 3 验证中观察到的浏览器下载时序风险

已观察风险：
- 完整单元测试第一次运行时，`test_browser_automation_mcp_server_uploads_and_downloads` 失败一次：`downloaded_files[0]` 已出现但文件内容暂时为空，断言未读到 `hello-download`。
- 该测试单独复现立即通过，随后完整 `python -m unittest learning_agent.test_learning_agent` 重跑也通过，说明当前不是阶段 3 模型拆分导致的稳定回归。

当前结论：
- 现有证据更符合 Playwright/Chromium 下载事件和 Windows 文件落盘之间的偶发时序差异：测试轮询条件只要求文件存在和下载记录出现，没有额外确认文件内容非空。
- 因阶段 3 的修改范围是模型代码迁移，且重跑完整测试已通过，本阶段未修改浏览器下载模块，避免把无关修复混入模型拆分。

剩余风险：
- 如果后续完整测试再次出现同类空文件失败，应在浏览器下载测试或 server 下载保存处增加“文件内容/大小稳定后再判定完成”的条件式等待，而不是固定 sleep。
- 该风险属于浏览器自动化层，后续阶段 7 拆 `browser/` 时更适合纳入专项处理和回归测试。

## 2026-05-29 模块化阶段 4 验证中发现并处理的问题

已处理风险：
- 旧风险：`run_mcp_doctor()` 拆到 `learning_agent/mcp/runtime.py` 后，测试仍 patch `learning_agent.learning_agent.diagnose_real_chrome_environment`，导致 doctor 读取真实本机 Chrome 状态并让测试不稳定。
- 已确认根因：阶段 4 迁移改变了诊断函数的读取位置，旧入口兼容导入存在，但 doctor 内部没有经过旧入口兼容层读取可替换诊断函数。
- 已处理：新增 `_diagnose_real_chrome_environment()` 兼容层，优先使用旧主入口上的诊断替身，再回退到真实 `browser_real_chrome` 诊断。
- 已验证：`test_mcp_doctor_reports_real_chrome_profile_diagnostic` 通过，`-k mcp` 通过，`mcp-doctor` 脚本入口通过。
- 旧风险：阶段 3 记录的浏览器下载空文件时序问题在阶段 4 `-k mcp` 中再次出现，说明它不是一次性偶发观察。
- 已确认根因：上传下载测试的轮询条件只要求下载记录出现且文件数量达到 2，没有确认文件内容已经写完整。
- 已处理：测试轮询现在每轮读取下载文本，只在两个文件都包含 `hello-download` 后停止等待。
- 已验证：上传下载聚焦测试通过，`-k mcp` 通过，完整单元测试通过。

剩余风险：
- `run_mcp_doctor()` 仍在阶段 4 临时依赖旧主入口的 `TOOL_SCHEMAS` 和工具包装 helper；阶段 5 拆 `tools/` 后应移除这类临时回连。
- 浏览器下载模块本身仍可能在真实机器上受浏览器、杀毒软件或文件锁影响；当前修复是让测试等待真实内容完整，而不是改变用户下载行为。

## 2026-05-29 模块化阶段 5 tools 拆分风险记录

已处理风险：
- 旧风险：阶段 4 的 MCP runtime 仍通过旧主入口读取 `agent_tool_from_schema`、`builtin_tool_capability_pack` 和 `TOOL_SCHEMAS`，阶段 5 如果只移动类型不保留旧入口兼容，会导致 MCP 工具包装断开。
- 已处理：`learning_agent.py` 从 `learning_agent/tools/catalog.py` 重导入 `agent_tool_from_schema`、`builtin_tool_capability_pack`、`build_builtin_tool_catalog`，旧入口名称继续存在；MCP runtime 的临时读取仍能工作。
- 旧风险：把 `_execute_tool` 长 if 链移出后，allowed_tools、ToolPolicy、plan mode、deferred MCP 的执行期守卫可能漏掉。
- 已处理：`learning_agent/tools/executor.py` 先执行统一守卫，再走内置分发表和 MCP 分发；`-k tool`、`-k permission`、`-k plan_mode` 均通过。
- 旧风险：长工具结果落盘摘要如果拆错，会导致模型下一轮拿不到 `Full output saved to` 或 artifact 观察事件。
- 已处理：只迁移文件名、inline limit 和摘要格式 helper，落盘写文件与 observation 仍由主 agent 保持原行为；`-k offload` 通过。

剩余风险：
- `TOOL_SCHEMAS` 和具体工具实现方法仍在 `learning_agent.py`，阶段 5 只是先拆出工具层边界、catalog、pool、executor 和 helper；后续如果继续细拆具体工具实现，应按能力域逐步迁移，避免一次性移动所有副作用工具。
- MCP runtime 仍通过旧主入口临时读取 `TOOL_SCHEMAS`；等内置 schema 常量完全迁入 `tools/catalog.py` 后，应移除这条临时回连。

## 2026-05-29 模块化阶段 6 prompts 拆分风险记录

已处理风险：
- 旧风险：`learning_agent.py` 同时承载 staticprompt 路径解析、读取、兜底、日期渲染和 dynamicprompt 伪 skill 元信息，导致 prompt 行为排查仍要翻主文件。
- 已处理：`static_prompt.py` 和 `dynamic_prompt.py` 已接管这些职责，主文件只保留委托调用。
- 旧风险：新目录 `learning_agent/prompts/` 在阶段 1 只有空骨架，无法作为真实 prompt 层入口使用。
- 已处理：阶段 6 新增 `registry.py`、`context_assembler.py`、`token_budget.py`、`surface_report.py` 和包入口 re-export，并用导入测试锁定。
- 旧风险：迁移 staticprompt 读取时可能丢失 `{{CURRENT_DATE}}` 或 `{{CURRENT_WORKSPACE}}` 渲染。
- 已处理：`read_static_prompt()` 显式接收 `workspace` 与 `current_date`，专项 prompt 测试和完整单测已通过。
- 旧风险：dynamicprompt 可能被误放进常驻 system prompt，重新撑大每轮上下文。
- 已处理：阶段 6 只迁移路径和伪 skill 元信息，`_build_initial_messages()` 仍只装配 staticprompt 与 memory index。

剩余风险：
- `prompt_registry.py` 和 `context_assembler.py` 的真实实现目前仍在根目录旧模块，新 `prompts/registry.py` 与 `prompts/context_assembler.py` 是兼容重导出；后续如果要完全移动实现，需要再做一轮更细的红绿测试，避免破坏旧 import。
- `token_budget.py` 目前只是预算入口和下限 helper，真实 token 估算仍复用 `ContextAssembler` 的粗略字符估算；如果后续接入真实 tokenizer，需要单独设计模型相关预算边界。
- `static_prompt.py`、`dynamic_prompt.py` 保留了大量逐行中文教学注释，适合用户学习，但文件本身偏长；后续稳定后可以把解释性材料同步到架构索引文档，代码注释保持必要密度。
- 本阶段额外运行 `mcp-doctor` 时，MCP server 均启动成功但真实 Chrome 诊断显示 `blocked`，原因是检测到 Chrome 正在运行且 User Data 路径未可用；这属于本机真实 Chrome 当前状态，不是阶段 6 prompts 拆分导致的回归。

## 2026-05-29 模块化阶段 7 browser 拆分风险记录

已处理风险：
- 旧风险：真实浏览器意图、公开查询识别、客户模式授权白名单和 Google URL 限制都堆在 `learning_agent.py`，排查“为什么还弹 y/N”或“为什么误用独立浏览器”时需要翻主文件大段逻辑。
- 已处理：阶段 7 新增 `browser/intent.py`、`browser/harness.py`、`browser/permissions.py`、`browser/search_workflow.py`，并让旧主入口优先委托这些模块。
- 旧风险：取消连续 `y/N` 的客户模式如果拆错，可能误放行非 Google URL 或敏感工具。
- 已处理：`browser.permissions` 保持原边界，只自动允许公开 Google 查询链路所需工具；`browser_evaluate`、network、console、tabs、downloads、upload 和非 Google URL 仍不自动放行。
- 旧风险：浏览器截图/下载产物路径清洗只存在于 MCP server 类内部，后续难以单独测试路径越界防护。
- 已处理：新增 `browser/artifacts.py` 并加模块测试，`browser_automation_mcp_server.safe_artifact_path()` 先委托新 helper。
- 旧风险：真实浏览器自然短 prompt 的无 y 客户模式可能在重构后退化。
- 已处理：真实可见终端验收 `real_chrome_natural_weather_travel-20260529_105333` 通过，`permission_sent_count=0`，动作链包含 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。

剩余风险：
- `learning_agent.py` 目前仍保留旧浏览器方法体作为过渡死代码，执行路径已经委托新模块，但文件体积和阅读噪音尚未完全下降；阶段 12 瘦身时应删除重复实现。
- `mcp-doctor` 仍可能显示真实 Chrome 诊断 `blocked`，如果本机 Chrome 正在运行或 User Data 路径不可用；这不阻断本阶段测试，但真实客户验收依赖 controller 能启动/连接本机可见 Chrome。
- 当前客户模式仍只自动打开 Google 公开入口；后续如果要直接打开会议官网、酒店官网、航司官网、YouTube 等站点，需要按域名和风险重新设计白名单，而不是扩大为任意 URL。

## 2026-05-29 模块化阶段 8 tasks 拆分风险记录

已处理风险：
- 旧风险：后台命令、task 子 agent、team、cron 和 monitor 的记录类全部堆在 `learning_agent.py` 顶部，长期任务排查时需要先穿过大量无关定义。
- 已处理：阶段 8 新增 `tasks/background.py`、`tasks/task_runs.py`、`tasks/team.py`、`tasks/cron_monitor.py`，并把记录类迁入这些模块。
- 旧风险：后台输出队列读取、后台命令状态、task background 解析、子 agent prompt、cron/monitor 状态和格式化规则都只能从主文件间接复用。
- 已处理：上述纯 helper 已迁移到 tasks 层，主文件旧方法优先委托新 helper。
- 旧风险：迁移 task 记录类时可能破坏后台 task、team_start_task、cron/monitor 的旧文本输出或生命周期状态。
- 已处理：`-k task`、`-k background`、`-k cron` 和完整单元测试均通过，说明旧工具输出与生命周期行为保持兼容。

剩余风险：
- `learning_agent.py` 仍保留 task/team/cron/monitor 的副作用编排方法，例如真正创建子 agent、启动后台进程、权限确认和 team 绑定 task；阶段 8 只迁移低风险记录类和纯 helper。
- `_task_background_enabled`、`_task_child_prompt`、`_cron_monitor_state` 等旧方法体中还存在委托后的不可达旧代码；阶段 12 瘦身时应删除这些重复实现。
- `mcp-doctor` 运行时观察到真实 Chrome 默认端口 9222 被占用，这是刚完成真实 Chrome 验收后的本机环境状态提示，不是 tasks 拆分导致的 MCP 启动失败。
## 2026-05-30 Stage 13C bug record: running Chrome was blocked even when CDP was available

Status: resolved in Stage 13C; automated tests and real visible terminal acceptance passed.

Symptom:
- Visible terminal acceptance run `real_chrome_natural_weather_travel-20260530_142210` stopped with a final answer telling the user to close Chrome.
- The run had `permission_sent_count=0`, so the old repeated `Y` issue was not the blocker.
- Required browser actions did not happen because `browser_connect_real_chrome` refused the already-running Chrome state.

Confirmed evidence:
- `Invoke-WebRequest http://127.0.0.1:9222/json/version` returned Chrome CDP metadata and a `webSocketDebuggerUrl`.
- Therefore the local visible Chrome was not merely “running”; it was already exposing a trusted local CDP endpoint that Playwright can attach to.
- Existing code in `browser_connect_real_chrome()` raised immediately on `manager.chrome_is_running()` and never checked the live CDP endpoint.

Root cause:
- The running-Chrome guard was too broad.
- It correctly protected profile locks when no CDP endpoint exists, but incorrectly blocked the valid case where the user has already launched Chrome with local remote debugging enabled.

Fix:
- When Chrome is running, check `wait_for_cdp_endpoint(preferred_port, timeout_seconds=1.0)`.
- If true, call `_connect_real_chrome_after_checks(..., attach_existing_cdp=True, existing_debug_port=preferred_port)`.
- If false, keep the old refusal path to protect the user’s daily profile.
- Attach mode never starts or owns a Chrome process, so cleanup must only disconnect CDP and must not terminate Chrome.
- Update `diagnose_real_chrome_environment()` with the same distinction, so “9222 is occupied by trusted Chrome CDP” is reported as `available` rather than `needs_user_action`.

Regression protection:
- `test_browser_connect_real_chrome_attaches_when_running_chrome_has_cdp`.
- `test_browser_connect_real_chrome_blocks_when_chrome_is_running_without_cdp`.
- `test_real_chrome_diagnostic_reports_available_when_running_chrome_has_cdp`.
- RealChrome focused suite: 40 tests OK, skipped=1.
- Full unittest discovery: 367 tests OK, skipped=1.

Acceptance closure:
- Visible terminal run: `learning_agent\acceptance_controller\runs\real_chrome_natural_weather_travel-20260530_144214\result.json`.
- Outcome: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Evidence checks passed for `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`, `real_chrome_connected=true`, `browser_click`, `browser_type`, `browser_press_key`, and `browser_screenshot`.

Residual risk:
- If the endpoint disappears during a future run, the correct behavior is to fail with a clear “已有 Chrome CDP endpoint 未就绪” or fall back to the safe running-Chrome refusal, not to kill Chrome.

## 2026-05-30 Stage 14 cleanup risk record

Status: resolved for this pass.

Risk handled:
- Old user-visible entry points could confuse maintainers after the new layered architecture was built.
- `learning_agent/core/agent.py` still contained same-block unreachable old code after wrapper returns, making future debugging more expensive.
- Old artifact directories in the source tree made it look like historical debug output was still part of the active architecture.

Resolution:
- Removed the old test aggregator files, old acceptance forwarding file, and old `tests_support` directory.
- Replaced startup selftest commands with `python -m unittest discover learning_agent`.
- Rewrote the architecture index around unique new entry points, deleted old entry points, module ownership, and bug-routing guidance.
- Removed historical artifact directories after copying the fresh Stage 14 acceptance evidence into the run directory.

Regression guard:
- `learning_agent/tests/test_compat_cleanup.py` now checks that the deleted old files stay deleted and that active tests do not import the old routing names.

Maintenance caution:
- Avoid line-number bulk deletion in `core/agent.py`; use AST/function-boundary checks and small patches so wrapper cleanup does not damage neighboring method bodies.

## 2026-05-31 Stage 15A baseline test blockers

Status: resolved for this pass in worktree `stage15a-event-runtime`.

Symptoms:
- Initial `python -m unittest discover learning_agent` in the fresh worktree failed with 4 failures and 4 errors.
- Playwright was missing from the default Python 3.13 environment, causing browser automation tests to fail.
- Existing tests expected `.gitignore` to include `learning_agent/browser_profiles.json` and `learning_agent/browser_artifacts/real_chrome_audit.jsonl`, but the new baseline `.gitignore` did not include those exact sensitive local-file paths.
- Existing parity checklist test expected `docs/superpowers/specs/claudecode_parity_checklist.md`, but the file was absent from the first git baseline.

Confirmed evidence:
- `python -m pip show playwright` reported package not found.
- Focused tests reproduced the `.gitignore` and parity checklist failures.
- After installing Playwright/Chromium and restoring the missing fixture/document entries, `python -m unittest discover learning_agent` passed with 368 tests OK, skipped=1.

Resolution:
- Installed Playwright with `python -m pip install playwright`.
- Installed Chromium browser binaries with `python -m playwright install chromium`.
- Added the missing `.gitignore` entries.
- Added the missing parity checklist document.

Residual risk:
- The Playwright installation is an environment dependency, not a repository file. A different machine may still fail browser automation tests until Playwright and browser binaries are installed.
- Future setup docs should eventually explain the exact Python environment and Playwright install command used for local baseline tests.
