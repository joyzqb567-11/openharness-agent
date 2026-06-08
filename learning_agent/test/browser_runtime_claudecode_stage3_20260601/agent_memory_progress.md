# 当前任务进度

## 2026-05-31 Long-Task Harness v1 执行记录

状态：核心代码、文档、学习备份、自动化验证和真实可见终端验收均已完成。

完成内容：
- 已按用户要求先生成 8 阶段任务文档：`task_plan.md`、`findings.md`、`progress.md`、`agent_memory/long_task_harness_plan.md`，并把计划备份到 `learning_agent/test/long_task_harness_20260531/task_plan.md`。
- 已新增 `learning_agent/tests/test_harness_long_task.py`，覆盖持久化 store、JSONL 事件、队列租约、heartbeat、完成/失败落盘、marker/artifact 阶段验收、可恢复失败重试、checkpoint resume、状态渲染和 CLI。
- 已完成独立 `learning_agent/harness/` 模块：`models.py`、`store.py`、`queue.py`、`verifier.py`、`recovery.py`、`runner.py`、`status.py`、`cli.py`、`__main__.py`、`__init__.py`。
- 已新增 `learning_agent/harness/README.md`，并更新 `learning_agent/README.md` 与 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，说明其他 agent 如何检查和接入长任务 harness。

当前验证：
- 红灯已确认：新增测试首次因 `learning_agent.harness` 不存在失败。
- 绿灯已确认：`python -m unittest learning_agent.tests.test_harness_long_task` 当前 5 tests OK。
- 完整回归已确认：`python -m unittest discover learning_agent` 当前 395 tests OK，skipped=1。
- 编译检查已确认：`python -m compileall learning_agent` 通过。
- MCP doctor 已确认：退出码 0，三个 MCP server 启动成功，模型可见 MCP 工具 30 个；当前真实 Chrome 正在运行导致 profile 诊断为 `needs_user_action`，但本轮 harness 验收不依赖真实 Chrome。
- 真实可见终端验收已确认：`learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/result.json` 显示 `completed=true`、`assertion.passed=true`，最终回答包含 `HarnessRun`、`HarnessQueue`、`StageVerifier`、`render_harness_status` 和 `LONG_TASK_HARNESS_READY`。
- 终端截图已目视确认：`learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/03_final.png` 中真实 Windows Terminal 显示了该回答。

下一步：
- 后续如果继续增强，可把 `LearningAgent.run_events()` 的长任务执行接入 `HarnessRunner`，并补 `enqueue/run` CLI。

## 2026-05-31 Harness CLI Agent Execution 执行记录

状态：已完成计划、TDD 红绿、CLI `enqueue/run`、`AgentStageExecutor`、文档同步、学习备份、自动化验证和真实可见终端验收。

完成内容：
- 已新增任务文档 `task_plan_harness_cli_agent_execution.md` 和进度文档 `progress_harness_cli_agent_execution.md`。
- 已扩展 `learning_agent/tests/test_harness_long_task.py`，新增 CLI enqueue、CLI run echo 和 `AgentStageExecutor` 三类回归测试。
- 已新增 `learning_agent/harness/agent_executor.py`，让 `HarnessRunner` 可以通过 `AgentStageExecutor` 调用真实 `LearningAgent.run(stage.prompt)`。
- 已扩展 `learning_agent/harness/cli.py`，新增 `enqueue` 和 `run` 子命令；`run` 支持 `--executor echo` 和 `--executor agent`。
- 已更新 `learning_agent/harness/README.md`、`learning_agent/README.md` 和 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`。

当前验证：
- 红灯已确认：新增测试首次因缺少 `learning_agent.harness.agent_executor` 失败。
- 绿灯已确认：`python -m unittest learning_agent.tests.test_harness_long_task` 当前 8 tests OK。
- 完整回归已确认：`python -m unittest discover learning_agent` 当前 398 tests OK，skipped=1。
- 编译检查已确认：`python -m compileall learning_agent` 通过。
- MCP doctor 已确认：退出码 0，三个 MCP server 启动成功，模型可见 MCP 工具 30 个；真实 Chrome 仍因本机 Chrome 正在运行显示 `needs_user_action`，但本轮 harness CLI 验收不依赖真实 Chrome。
- 真实可见终端验收已确认：`learning_agent/acceptance_controller/runs/harness_cli_echo_run-20260531_154459/result.json` 显示 `completed=true`、`assertion.passed=true`，最终回答包含 `HARNESS_CLI_AGENT_EXECUTION_OK`、`visible-cli`、`status=completed`、`acceptance=passed`、`VISIBLE_HARNESS_CLI_OK`、`AgentStageExecutor`。

下一步：
- 后续如果继续增强，可增加 JSON 计划文件输入、文件锁和把 `LearningAgent.run_events()` 的长期任务调度纳入 harness。

## 2026-05-31 断言验证器审计检查

状态：已完成代码阅读和聚焦验证；本轮没有修改生产代码。

检查结论：
- learning_agent 当前已经有可用的真实验收断言验证器，核心实现位于 `learning_agent/acceptance_controller/controller.ps1` 的 `Test-ScenarioAssertions` 函数。
- 该验证器会读取 `events.jsonl`、最终回答事件、最新 debug log 和权限响应计数，并生成 `state_checks`、`event_answer_checks`、`debug_log_checks`、`marker_passed`、`permission_count_passed`。
- 每轮验收会输出 `result.json`，保存 `completed`、`assertion`、事件序列、事件日志路径、启动截图、prompt 截图、最终截图、归档 debug log 和权限决策记录。
- 当前实现是“嵌在 PowerShell controller 里的场景断言器”，还不是独立 Python 包或独立 `verify-run` 命令。

验证结果：
- `python -m unittest learning_agent.tests.test_observability_acceptance`：9 tests OK。
- PowerShell `[scriptblock]::Create(...)` 解析 `learning_agent/acceptance_controller/controller.ps1`：通过。
- 场景统计确认 8 个 JSON 场景均配置了事件断言、最终回答断言和 debug log 证据断言；真实自然浏览器场景还配置了 `max_permission_sent_count=0`。

## 2026-05-31 H 盘路径二次清理与真实终端 smoke 验收

状态：已完成路径二次清理、自动化验证和真实可见终端 smoke 验收。

完成内容：
- 已清理当前 OpenHarness 项目相关的旧盘符残留，`rg` 搜索确认旧 OpenHarness 绝对路径和旧测试样例不再出现。
- 保留 `D:\ClaudeCode-main\ClaudeCode-main` 外部源码路径，因为本机实测该路径存在，而 `H:\ClaudeCode-main\ClaudeCode-main` 不存在；强行改为 H 盘会制造假路径。
- 已把 `learning_agent/tests/test_models_codex_oauth.py` 中无副作用示例路径改为 `H:/demo`。
- 已把 `learning_agent/README.md`、`learning_agent/change/oauth.txt` 和阶段 15H 备份 README 中的 opencode2-main 说明改为不写死盘符。
- 已修正 `learning_agent/acceptance_controller/scenarios/smoke.json`，让 smoke 场景按当前客户模式等待 `permission_auto_approved`，不再等待旧人工权限事件。
- 已按学习规则备份修改说明和关键文件到 `learning_agent/test/h_drive_cleanup_20260531/`。

验证结果：
- `python -m unittest learning_agent.tests.test_models_codex_oauth`：46 tests OK。
- `python -m compileall learning_agent`：通过。

## 2026-05-31 千问真实 Chrome 拟人操作测试

状态：用户目标已跑通，严格场景断言未通过。

测试目标：
- 由 `learning_agent` 通过 `browser_connect_real_chrome` 连接真实 Google Chrome。
- 打开 `https://www.qianwen.com/`。
- 拟人点击输入框、输入“请查询明天鄞州区的天气预报”、按 Enter 提交。
- 把真实浏览器上看到的千问回答告诉用户。

运行结果：
- 第一次 run：`learning_agent/acceptance_controller/runs/real_chrome_qianwen_yinzhou_weather-20260531_225006`。
- 第一次已连接真实 Chrome 并打开千问，但模型在输入框定位后遇到 Codex OAuth/API HTTP 503，中断于点击输入前。
- 第二次 run：`learning_agent/acceptance_controller/runs/real_chrome_qianwen_yinzhou_weather-20260531_225525`。
- 第二次日志确认 `browser_connect_real_chrome 成功`、`real_chrome_connected=true`、`browser_open 成功`、`browser_click 成功`、`browser_type 成功`、`browser_press_key 成功`、`browser_wait 成功`。
- 第二次真实 Chrome 页面可见千问回答：明天 6月1日 鄞州区天气晴，23℃～32℃，西北风 <3级，并提示防晒补水。

严格验收未通过原因：
- learning_agent 最终回答没有包含场景要求的固定标记和工具名清单。
- learning_agent 漏掉了场景要求的 `browser_screenshot` 工具调用。
- learning_agent 在已有 `browser_snapshot` 可见内容的情况下额外调用了 `browser_evaluate` 读取 `document.body.innerText`，这不符合真实 Chrome 默认隐私边界的最佳实践。

结论：
- 当前 agent 具备真实 Chrome 拟人点击、输入、提交并读取网页结果的能力。
- 但复杂真实浏览器任务的“严格按验收格式收尾”和“禁止 evaluate 的策略约束”还需要继续强化。
- `python -m unittest learning_agent.tests.test_observability_acceptance`：9 tests OK。
- `python -m unittest discover learning_agent`：387 tests OK，skipped=1。
- `python learning_agent\learning_agent.py mcp-doctor`：退出码 0，工作区和配置文件均为 H 盘，三个 MCP server 启动成功，模型可见 30 个 MCP 工具。
- 真实可见终端 smoke 验收第二次通过：`learning_agent/acceptance_controller/runs/smoke-20260531_140112/result.json` 显示 `completed=true`、`prompt_received=true`、`final_printed=true`，最终回答为 `ACCEPTANCE_HARNESS_OK`。
- 最终截图 `learning_agent/acceptance_controller/runs/smoke-20260531_140112/03_final.png` 已目视确认真实终端中显示 `Agent > ACCEPTANCE_HARNESS_OK`。

## 2026-05-31 H 盘运行路径修复

状态：已完成文件修改和主要验证。

证据：
- 用户确认当前实际运行目录是 `H:\codexworkplace\sofeware\OpenHarness-main`。
- 搜索确认 `learning_agent/mcp_servers.json` 曾把三个 MCP server 参数指向旧盘符下的 OpenHarness `learning_agent` 目录。
- 搜索确认 `AGENTS.md` 的学习备份路径和真实终端验收脚本路径曾指向旧盘符。
- 搜索确认 `agent_memory/context.md` 的项目根目录曾记录为旧盘符路径。

本次改动：
- 已把 `learning_agent/mcp_servers.json` 的 `browser_search`、`workspace_tools`、`browser_automation` 三组启动参数改为 H 盘当前项目路径。
- 已把 `AGENTS.md` 中学习备份目录和 `start_oauth_agent.bat` 强制验收路径改为 H 盘当前项目路径。
- 已把 `agent_memory/context.md` 当前项目根目录改为 H 盘当前项目路径。
- 历史 `debug_logs/` 和 `acceptance_controller/runs/` 中的历史盘符路径保留不改，因为它们是旧验收现场证据，不是当前运行配置。

验证结果：
- `learning_agent/mcp_servers.json` 已可被 PowerShell `ConvertFrom-Json` 正常解析，三个 MCP server 参数均显示为 H 盘路径。
- 三个 MCP server 文件路径均通过 `Test-Path`，说明 H 盘目标文件存在。
- 活跃运行配置与启动脚本范围内已搜不到旧盘符下的 OpenHarness 路径。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码为 0，工作区和配置文件均显示为 H 盘路径，`browser_search`、`workspace_tools`、`browser_automation` 三个 MCP server 启动成功，模型可见 30 个 MCP 工具。
- `python -m unittest learning_agent.tests.test_compat_cleanup` 通过，结果为 5 tests OK。

残留验证限制：
- `learning_agent.tests.test_mcp_registry` 全套测试在系统 Python 下剩余 2 个错误，错误原因是 `No module named 'playwright'`；这不是本次 D/H 路径修复导致。
- 沙盒内运行同一测试时，大量失败来自 `tempfile.TemporaryDirectory` 子目录写入被拒绝；沙盒外重跑后该类权限错误消失，只剩 Playwright 依赖缺失。

## 2026-05-30 阶段 13B 旧脚本入口收紧执行记录

状态：已完成代码改造、学习备份、自动化回归和 mcp-doctor；真实可见终端验收已启动但被 Codex OAuth/API HTTP 429 额度限制阻塞，尚不能声明开发完成。

完成内容：
- 扩展 `learning_agent/tests/test_compat_cleanup.py`，新增活跃测试/辅助脚本不再导入旧入口的扫描，以及 `learning_agent.py` 不再批量 re-export `core.agent` 的扫描。
- 红灯确认：新增保护测试最初失败，失败点分别是 `tests_support/legacy_learning_agent_suite.py` 仍导入旧入口、`learning_agent.py` 仍使用 `vars(agent_module).items()` 和 `globals()[exported_name]` 批量导出。
- 修改 `learning_agent/tests_support/legacy_learning_agent_suite.py`，把原来的旧入口大导入拆成 `app/core/models/mcp/tools` 分层导入。
- 修改 `learning_agent/fake_model_repl.py`，改为从 `core.agent` 和 `core.messages` 导入。
- 重写 `learning_agent/learning_agent.py`，仅保留路径兜底、`__path__` 脚本模式兜底、`app.cli.main` 导入和直接启动逻辑。
- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，补充阶段 13B 当前状态和后续导入导航。

已完成阶段性验证：
- 阶段 13B 保护测试通过：`python -m unittest learning_agent.tests.test_compat_cleanup`，4 tests OK。
- 语法检查通过：`learning_agent.py`、`fake_model_repl.py`、`tests_support/legacy_learning_agent_suite.py`、`tests/test_compat_cleanup.py`。
- 核心运行测试通过：`python -m unittest learning_agent.tests.test_core_run_loop`，40 tests OK。
- 假模型 REPL 自检通过：`python learning_agent\fake_model_repl.py --self-test` 退出码 0。
- 顶层 discovery 导入复现通过：在 `learning_agent` 目录执行 `python -c "import app"` 输出 `app import ok`。
- 完整回归通过：`python -m unittest discover learning_agent`，365 tests OK，skipped=1。
- MCP Doctor 通过：`python learning_agent\learning_agent.py mcp-doctor` 退出码 0，三个 MCP server 均启动成功，模型可见 30 个 MCP 工具。
- 真实可见终端验收已尝试：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_111154/result.json` 显示 `completed=false`、`permission_sent_count=0`、`marker_passed=true`，失败原因为模型首轮返回 HTTP 429 `usage_limit_reached`，未进入真实浏览器工具调用阶段。
- 继续尝试备用模型链路：本机 `codex.exe` 可用，版本为 `codex-cli 0.130.0-alpha.5`；但 `LEARNING_AGENT_MODEL_PROVIDER=codex` 的一次性 run 在 `codex exec` 90 秒超时，不能作为本轮验收替代。

## 2026-05-30 阶段 13 去兼容化第一刀执行记录

状态：阶段 13 第一刀已完成，并已通过自动化测试、mcp-doctor 和真实可见终端交互验收。

完成内容：
- 新增 `learning_agent/tools/schemas.py`，承载 `TOOL_SCHEMAS`、`KERNEL_TOOL_NAMES`、`DYNAMIC_SKILL_CAPABILITY_PACKS`、`BUILTIN_TOOL_CAPABILITY_PACKS`。
- 修改 `learning_agent/core/agent.py`，删除内置工具 schema 大块常量，改为从 `tools.schemas` 导入。
- 修改 `learning_agent/tools/catalog.py`，移除 `_main_entry_module()` 和 `_main_attr()` 旧入口回连。
- 修改 `learning_agent/mcp/runtime.py`，移除旧入口代理，直接依赖 `tools.catalog` 与 `tools.schemas`。
- 修改 `learning_agent/models/adapters.py`，默认输出 schema 改为读取 `DEFAULT_TOOL_SCHEMAS`。
- 修改 `learning_agent/app/cli.py` 和 `learning_agent/__init__.py`，让 app 层和包门面直接接新模块。
- 新增 `learning_agent/tests/test_compat_cleanup.py`，扫描生产模块禁止回流旧入口。
- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`，补充阶段 13 当前状态和 `tools/schemas.py` 修 bug 索引。
- 已按用户学习备份规则，把本轮新增/修改文件复制到 `learning_agent/test/stage13_tool_schema_split_20260530/`。

已完成验证：
- `py_compile` 通过：`tools/schemas.py`、`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py`、`core/agent.py`、`__init__.py`、`tests/test_compat_cleanup.py`。
- 生产模块旧入口回流扫描通过：`tools/catalog.py`、`mcp/runtime.py`、`models/adapters.py`、`app/cli.py`、`__init__.py` 中没有 `learning_agent.learning_agent` 导入。
- 新增回归通过：`python -m unittest learning_agent.tests.test_compat_cleanup`，2 tests OK。
- 工具层回归通过：`python -m unittest learning_agent.tests.test_tools_policy`，82 tests OK。
- MCP 层回归通过：`python -m unittest learning_agent.tests.test_mcp_registry`，108 tests OK。
- 模型层回归通过：`python -m unittest learning_agent.tests.test_models_codex_oauth`，46 tests OK。
- 聚焦组合回归通过：`python -m unittest learning_agent.tests.test_compat_cleanup learning_agent.tests.test_tools_policy learning_agent.tests.test_mcp_registry learning_agent.tests.test_models_codex_oauth`，238 tests OK。
- 完整回归通过：`python -m unittest discover learning_agent`，363 tests OK，skipped=1。
- MCP Doctor 通过：`python learning_agent\learning_agent.py mcp-doctor` 退出码 0，模型可见 30 个 MCP 工具，真实 Chrome profile 诊断为 available。
- 真实可见终端交互验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_104237/result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`，最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`、`real_chrome_connected=true`、`browser_click`、`browser_type`、`browser_press_key`、`browser_screenshot`。

## 2026-05-29 learning_agent 模块化重构阶段 11 测试拆分

状态：阶段 11 已完成；旧 `learning_agent/test_learning_agent.py` 已瘦身为兼容入口，新 `learning_agent/tests/` 包提供按领域运行的测试入口。

完成内容：
- 新增 `learning_agent/tests/` 包，包含 `test_core_run_loop.py`、`test_models_codex_oauth.py`、`test_mcp_registry.py`、`test_tools_policy.py`、`test_browser_intent.py`、`test_browser_harness.py`、`test_prompts_context.py`、`test_observability_acceptance.py`。
- 新增 `learning_agent/tests/_legacy_groups.py`，把遗留测试类按测试名关键字稳定分组，保证每条测试只有一个归属。
- 新增 `learning_agent/tests_support/legacy_learning_agent_suite.py`，承载原 112 万字节测试主体，并修复搬迁后的 `Path(__file__)` 资产定位。
- 修改 `learning_agent/test_learning_agent.py` 为旧入口兼容层；`python -m unittest learning_agent.test_learning_agent` 仍跑完整 359 条测试。
- 为 `python -m unittest discover learning_agent` 增加双导入兼容，避免目录 discovery 时 `learning_agent.py` 顶层模块遮蔽 `learning_agent` 包名。
- 已更新正式实施计划文档中阶段 11 的 Step 11.1-11.4 为完成。

验证记录：
- `py_compile` 覆盖新旧测试入口和 legacy suite，结果通过。
- 8 个分类入口分别通过：观测验收 9 条、浏览器意图 7 条、模型/OAuth 46 条、提示词上下文 36 条、工具策略 82 条、MCP registry 108 条、浏览器执行层 31 条（skipped=1）、核心兜底 40 条。
- 旧兼容入口通过：`Ran 359 tests in 25.301s OK (skipped=1)`。
- discovery 入口通过：`Ran 359 tests in 24.796s OK (skipped=1)`。

下一步：
- 进入阶段 12，删除 `learning_agent.py` 中已经委托到新模块后的不可达重复实现，把主文件收束成薄入口和兼容导出层。

## 2026-05-30 learning_agent 模块化重构阶段 12 瘦身入口

状态：阶段 12 已完成；代码瘦身、README/架构索引同步、自动化验收、MCP Doctor 和 `start_oauth_agent.bat` 真实可见终端验收均已通过，整体模块化改造阶段 0 到阶段 12 满足最终完成条件。

完成内容：
- `learning_agent/learning_agent.py` 已从约 1MB 巨型主文件收束为约 4.7KB 薄兼容入口，只负责脚本模式路径兜底、旧导入 re-export 和 `main()` 转发。
- `LearningAgent`、`ToolCallingFakeModel`、`TOOL_SCHEMAS`、工具循环、权限兼容入口和旧公开符号已经迁入 `learning_agent/core/agent.py`。
- `learning_agent/core/__init__.py` 已补充脚本模式 fallback，避免本地 MCP server 直接运行时因为 `learning_agent.py` 被当作顶层模块而导入失败。
- `core/agent.py` 的 packaged skill fallback 已改为从包根目录 `learning_agent/skills` 读取，避免迁移后误找 `learning_agent/core/skills`。
- `learning_agent/README.md` 已说明薄入口、`core/agent.py`、`app/`、`browser/`、`observability/` 和 `tests/` 的定位。
- `learning_agent/AGENT_ARCHITECTURE_INDEX.md` 已更新为当前落地架构地图，作为以后修 bug 的索引入口。
- 正式实施计划中 Step 12.1、12.2、12.3、12.4、12.5 已全部勾选完成。
- 本轮修复了真实 Chrome 环境探测误判：当 Windows 受限环境让 `Path.exists()` 或 `tasklist` 返回权限拒绝时，会用 PowerShell 只读 fallback 复查，避免误判 Chrome 正在运行或 User Data 缺失。

自动化验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\core\agent.py learning_agent\core\__init__.py learning_agent\browser_real_chrome.py` 退出码 0。
- `python -m unittest learning_agent.test_learning_agent` 结果为 `Ran 361 tests in 38.256s OK (skipped=1)`。
- `python -m unittest discover learning_agent` 结果为 `Ran 361 tests in 33.759s OK (skipped=1)`。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码 0，真实 Chrome profile 诊断为 `available`，Chrome 路径、User Data、进程状态和 9222 端口均识别正常；`browser_search`、`workspace_tools`、`browser_automation` 三个 MCP server 均启动成功，模型可见 MCP 工具 30 个。

真实可见终端验收记录：
- 命令：`powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\real_chrome_natural_weather_travel.json`。
- 结果文件：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_025500/result.json`。
- 验收结果：`completed=true`、`final_printed=true`、`prompt_sent=true`、`prompt_received=true`、`permission_sent_count=0`、`permission_count_passed=true`、`marker_passed=true`。
- 最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK` 和 `real_chrome_connected=true`。
- 动作链包含 `browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot`。
- 截图证据：`learning_agent/browser_artifacts/real_chrome_chongqing_weather_travel_2026-05-31.png`。
- 阶段 12 修改文件和验收证据已备份到 `learning_agent/test/modular_refactor_stage12_20260529/`。

最终结论：
- 阶段 0 到阶段 12 的实施计划已完成，最终验收清单全部通过。

## 2026-05-27 Acceptance Harness 执行记录

状态：已完成最小验收协议模块、终端入口接入、自动化测试、MCP doctor、学习备份和真实可见终端 smoke 验收；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/acceptance_harness.py`，提供 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG`、`::learning-agent-acceptance ` 终端标记、JSONL 事件构造与写入。
- 已修改 `learning_agent/learning_agent.py`，让终端权限确认和交互主循环发出可观测状态事件。
- 已修改 `learning_agent/test_learning_agent.py`，新增 3 条回归测试覆盖默认静默、JSONL 写入和权限事件顺序。
- 已新增 `learning_agent/test/acceptance_harness_20260527/run_event_log_visible_terminal_smoke.ps1`，用于真实可见窗口 smoke 验收。
- 已把最终版 `acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`、计划文档和可见终端证据归档到 `learning_agent/test/acceptance_harness_20260527/`。

验证记录：
- 红灯验证：新增测试首次因 `ModuleNotFoundError: No module named 'learning_agent.acceptance_harness'` 失败；模块实现后权限事件测试又因事件文件不存在失败。
- 聚焦绿灯：3 条 Acceptance Harness 测试通过，输出 `Ran 3 tests in 0.030s OK`。
- 语法检查：`py_compile` 覆盖 `acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py` 通过。
- 完整回归：首次完整回归中浏览器下载测试出现一次空文件偶发失败；该单测单独复跑 1 次和连续 3 次均通过，随后完整回归重新通过：`Ran 335 tests in 22.247s OK (skipped=1)`。
- `mcp-doctor`：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 真实可见终端 smoke：通过 `start_oauth_agent.bat` 打开真实窗口，事件序列为 `permission_required -> permission_answered -> agent_ready_for_user_prompt -> user_prompt_received -> final_answer_printed -> agent_ready_for_user_prompt`，目标 agent 回复 `ACCEPTANCE_HARNESS_OK`。
- 最终版真实可见终端事件日志包含 `prompt_preview` 和 `answer_preview`，其中 `answer_preview` 为 `ACCEPTANCE_HARNESS_OK`。
- 可见终端结果文件：`learning_agent/test/acceptance_harness_20260527/event_log_visible_terminal_result.json` 显示 `completed=true`。

## 2026-05-27 重庆天气真实可见终端验收记录

状态：已完成 `start_oauth_agent.bat` 真实可见终端验收；目标 agent 成功调用浏览器自动化 MCP 查询重庆 2026-05-30 天气并生成旅游攻略；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/test/acceptance_harness_20260527/run_chongqing_weather_visible_terminal_acceptance.ps1`。
- 脚本会启动真实可见 `start_oauth_agent.bat` 窗口，设置 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG`，按事件日志等待权限、ready、prompt received 和 final answer。
- 脚本会自动同意启动 MCP server、`browser_open` 和 `browser_snapshot` 权限，并通过调试日志核验真实工具调用。
- 脚本会检查 `VISIBLE_WEATHER_ACCEPTANCE_OK`、`browser_open 成功`、`browser_snapshot 成功`、`2026-05-30`、`重庆`、`api.open-meteo.com`、`旅游攻略` 等证据。

验证记录：
- PowerShell 脚本解析检查通过，脚本已转换为 UTF-8 BOM 以兼容 Windows PowerShell 5.1。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- Acceptance Harness 聚焦测试通过：`Ran 3 tests in 0.041s OK`。
- 完整单元测试通过：`Ran 335 tests in 22.500s OK (skipped=1)`。
- `mcp-doctor` 通过：`browser_search`、`workspace_tools`、`browser_automation` 启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 真实可见终端天气验收通过：`CHONGQING_WEATHER_VISIBLE_TERMINAL_COMPLETED=True`，结果文件 `weather_visible_terminal_result.json` 显示 `completed=true`。
- 目标 agent 调用 `browser_open` 打开 Open-Meteo URL，并调用 `browser_snapshot` 读取 JSON。
- 本轮读取到的天气：重庆 2026-05-30 天气代码 51（毛毛雨），最高 28.3°C，最低 22.2°C，最大降水概率 25%，最大风速 4.0 km/h，紫外线指数 8.60。
- 目标 agent 最终生成了穿衣携带建议、重庆一日旅游攻略、下雨或高温备选方案和来源 URL。

## 2026-05-27 Acceptance Controller 执行记录

状态：已完成通用真实可见终端控制器、两个场景 JSON、结构回归测试、自动化回归、MCP doctor、真实可见终端 smoke 场景和重庆天气场景验收；未 stage，未 commit。

完成内容：
- 已新增 `learning_agent/acceptance_controller/controller.ps1`，统一处理真实窗口启动、事件等待、权限输入、prompt 重试、截图、事件日志、调试日志归档和 `result.json`。
- 已新增 `learning_agent/acceptance_controller/scenarios/smoke.json`，用于固定一行回答 smoke 验收。
- 已新增 `learning_agent/acceptance_controller/scenarios/chongqing_weather_browser.json`，用于重庆 2026-05-30 天气、浏览器 MCP 和旅游攻略验收。
- 已新增 `learning_agent/acceptance_controller/README.md`，说明运行方式和场景字段职责。
- 已修改 `learning_agent/test_learning_agent.py`，新增 2 条 Acceptance Controller 结构测试，锁定 controller 文件、场景 JSON 结构和通用事件协议关键字。
- 已将最终版 controller、场景、README、测试副本和本轮结果复制到 `learning_agent/test/acceptance_controller_20260527/`。

验证记录：
- 红灯验证：新增 controller 结构测试首次失败，失败点为缺少 `learning_agent/acceptance_controller/controller.ps1` 和相关场景文件。
- 聚焦绿灯：2 条 controller 结构测试通过；5 条 Acceptance 相关聚焦测试通过，输出 `Ran 5 tests in 0.041s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.048s OK (skipped=1)`。
- `mcp-doctor` 通过：`browser_search`、`workspace_tools`、`browser_automation` 启动成功；真实 Chrome profile 诊断 `available`；模型可见 MCP 工具 30 个。
- 新 controller smoke 场景真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/smoke-20260527_230534/result.json` 显示 `completed=true`。
- 新 controller 重庆天气场景真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/chongqing_weather_browser-20260527_230607/result.json` 显示 `completed=true`。
- controller 版重庆天气日志确认 `browser_open 成功`、`browser_snapshot 成功`，读取到 `temperature_2m_max=28.3`、`temperature_2m_min=22.2`、`weather_code=51`。

## 2026-05-27 Real Chrome Profile Status 安全探针记录

状态：已完成真实 Chrome/profile 状态场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/test_learning_agent.py`，把 `real_chrome_profile_status.json` 纳入 Acceptance Controller 场景契约测试，并断言 prompt 必须包含 `real_chrome/SKILL.md`、`browser_profile_status` 和“不读取 cookies”的隐私边界。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_profile_status.json`，用于只读检查真实 Chrome/profile 状态，不连接真实 Chrome、不读取隐私网页内容。
- 已更新 `learning_agent/acceptance_controller/README.md`，补充 real Chrome profile status 场景运行命令。
- 已按学习备份规则复制 README、场景 JSON、测试副本和验收证据到 `learning_agent/test/real_chrome_profile_status_20260527/`。

验证记录：
- 红灯验证：`test_acceptance_controller_files_and_scenarios_are_valid` 先失败，失败点为缺少 `real_chrome_profile_status.json` 场景文件。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.011s OK`。
- Acceptance 聚焦回归：4 条相关测试通过，输出 `Ran 4 tests in 0.062s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 23.102s OK (skipped=1)`。
- `mcp-doctor` 通过：真实 Chrome profile 诊断为 `available`，Chrome 路径为 `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`，User Data 为 `C:\Users\joyzq\AppData\Local\Google\Chrome\User Data`，当前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_profile_status-20260527_232424/result.json` 显示 `completed=true`。
- 目标 agent 在真实终端中读取了 `learning_agent/skills/tool_list.md` 与 `learning_agent/skills/real_chrome/SKILL.md`，并调用 `mcp__browser_automation__browser_profile_status`。
- 状态工具返回：`mode=independent_chromium`、`real_chrome_connected=false`、`chrome_started_by_agent=false`、`endpoint=`、`profile=`、`pages=0`、最近安全拒绝为无；最终回答包含 `REAL_CHROME_PROFILE_STATUS_OK`。

## 2026-05-28 Real Chrome Connect Public Page 验收记录

状态：已完成场景级权限策略、真实 Chrome 连接公开页场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/acceptance_controller/controller.ps1`，新增 `permission_policy` 读取、大小写不敏感匹配、`Get-PermissionResponse` 决策函数，以及 `permission_policy_decisions` 结果审计。
- 已保持旧场景兼容：未配置 `permission_policy` 时默认继续输入 `y`，避免破坏 smoke、天气和 profile status 场景。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_connect_public_page.json`，默认拒绝未白名单权限，只允许启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 已修改 `learning_agent/acceptance_controller/README.md`，补充 connect 公开页场景运行命令和 `permission_policy` 字段说明。
- 已修改 `learning_agent/test_learning_agent.py`，新增场景结构和权限策略断言，锁定 connect 场景必须包含 `confirm_real_profile=true`、公开 URL、隐私边界、connect/open/snapshot 日志证据。
- 已按学习备份规则复制 controller、README、测试副本、场景 JSON 和验收证据到 `learning_agent/test/real_chrome_connect_public_page_20260528/`。

验证记录：
- 红灯验证：新增测试先失败，失败点为缺少 `real_chrome_connect_public_page.json` 和 controller 不包含 `permission_policy` / `Get-PermissionResponse` / `permission_policy_decisions`。
- 聚焦绿灯：2 条 Acceptance Controller 测试通过，输出 `Ran 2 tests in 0.047s OK`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.708s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，Chrome 路径和 User Data 均可识别，最终 Chrome 正在运行状态为 `false`，默认端口可用为 `true`。
- 第一次真实可见终端 connect 场景未通过：目标 agent 在 `browser_profile_status` 后的第 4 轮模型调用长时间无返回，未打印最终答案；失败证据位于 `runs/real_chrome_connect_public_page-20260528_053422/result.json`。
- 已基于失败根因收窄场景 prompt：减少第三个规则文件读取，并明确 status 后下一轮只调用 connect、connect 后只打开公开页、open 后只 snapshot。
- 第二次真实可见终端 connect 场景通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_connect_public_page-20260528_055137/result.json` 显示 `completed=true`。
- 真实终端事件序列包含 5 次权限请求并全部命中白名单：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 目标 agent 成功连接真实 Chrome：`browser_connect_real_chrome 成功`、`mode=real_chrome`、`real_chrome_connected=true`、`profile=Default`、`endpoint=http://127.0.0.1:9222`。
- 目标 agent 成功打开真实 Chrome 公开页：`browser_open 成功`，标题 `Example Domain`，URL `https://example.com/`。
- 目标 agent 成功读取公开页快照：`browser_snapshot 成功`，正文摘要包含 `Example Domain`。
- 最终回答包含 `REAL_CHROME_CONNECT_PUBLIC_PAGE_OK`，并声明未调用 `browser_evaluate`，未读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容或插件内容。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-28 Real Chrome Chongqing Weather Travel 验收记录

状态：已完成真实 Chrome 重庆天气攻略场景、TDD 红绿验证、自动化回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/test_learning_agent.py`，把 `real_chrome_chongqing_weather_travel.json` 纳入 Acceptance Controller 场景契约测试，并断言默认拒绝权限、真实 Chrome connect、Open-Meteo URL、2026-05-31、重庆、旅游攻略和隐私边界。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_chongqing_weather_travel.json`，只允许启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`，拒绝 `browser_evaluate`、tabs、console、network、downloads。
- 已更新 `learning_agent/acceptance_controller/README.md`，补充真实 Chrome 重庆天气攻略场景运行命令。
- 已按学习备份规则复制 README、测试副本、场景 JSON 和验收证据到 `learning_agent/test/real_chrome_chongqing_weather_travel_20260528/`。

验证记录：
- 红灯验证：`test_acceptance_controller_files_and_scenarios_are_valid` 先失败，失败点为缺少 `real_chrome_chongqing_weather_travel.json` 场景文件。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.012s OK`。
- Acceptance Controller 结构测试通过：`Ran 2 tests in 0.005s OK`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- 完整单元测试通过：`Ran 337 tests in 22.140s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，验收前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_061032/result.json` 显示 `completed=true`。
- 真实终端事件序列包含 5 次权限请求并全部命中白名单：启动 MCP、`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_snapshot`。
- 目标 agent 成功连接真实 Chrome：`browser_connect_real_chrome 成功`、`mode=real_chrome`、`real_chrome_connected=true`、`profile=Default`、`endpoint=http://127.0.0.1:9222`。
- 目标 agent 成功打开 Open-Meteo 公开天气 URL，并通过 `browser_snapshot` 读取重庆 2026-05-31 JSON。
- 本轮读取到的天气：重庆 2026-05-31 天气代码 51（毛毛雨），最高 31.0°C，最低 22.5°C，最大降水概率 39%，最大风速 6.4 km/h，紫外线指数 8.55。
- 目标 agent 最终输出 `REAL_CHROME_CHONGQING_WEATHER_TRAVEL_OK`，并生成穿衣携带建议、重庆一日旅游攻略、下雨或高温备选方案和来源 URL。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-28 Structured Permission Ledger 执行记录

状态：已完成结构化权限事件、controller 精确工具/URL 策略、TDD 红绿验证、完整回归、MCP doctor、真实可见终端验收、Chrome 清理和学习备份；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，新增 `build_permission_event_payload()` 及辅助解析函数，把 MCP 工具权限文本解析为 `permission_kind`、`tool_name`、`arguments`、`risk_level`、`risk_summary`。
- 已修改 `ask_permission_from_terminal()`，让 `permission_required` 和 `permission_answered` 都写入结构化 payload，同时保留旧 `action` 字段兼容 controller 和历史日志。
- 已修改 `learning_agent/acceptance_controller/controller.ps1`，新增 `allow_tool_names`、`deny_tool_names`、`allow_url_prefixes` 读取和匹配逻辑。
- 已让 controller 的 `permission_policy_decisions` 写入 `tool_name`、`arguments`、`risk_level`、`risk_summary`、`url`，形成可审计 tool-call ledger。
- 已修改 `real_chrome_chongqing_weather_travel.json`，启动 MCP 仍用 `allow_contains`，真实 Chrome 和浏览器工具改用 `allow_tool_names`；`browser_open` 额外要求 URL 前缀 `https://api.open-meteo.com/v1/forecast`。
- 已更新 `learning_agent/acceptance_controller/README.md`，说明结构化权限策略字段。
- 已修改 `learning_agent/test_learning_agent.py`，新增结构化权限事件测试，并扩展 controller/场景契约测试。

验证记录：
- 红灯验证：新增测试先失败，失败点为 `permission_required` 缺少 `permission_kind`、天气场景缺少 `allow_tool_names`、controller 缺少 `allow_tool_names` / `allow_url_prefixes` / `payload.tool_name` / `payload.arguments`。
- 聚焦绿灯：同一组 3 条测试通过，输出 `Ran 3 tests in 0.094s OK`。
- Acceptance 聚焦回归：4 条相关测试通过，输出 `Ran 4 tests in 0.040s OK`。
- Python 语法检查通过：`acceptance_harness.py`、`learning_agent.py`、`test_learning_agent.py`。
- PowerShell 解析检查通过：`controller.ps1` 可被 `[scriptblock]::Create()` 解析。
- 完整单元测试通过：`Ran 338 tests in 22.214s OK (skipped=1)`。
- `mcp-doctor` 验证通过：真实 Chrome profile 诊断为 `available`，验收前 Chrome 正在运行为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`ACCEPTANCE_CONTROLLER_COMPLETED=True`，结果文件 `learning_agent/acceptance_controller/runs/real_chrome_chongqing_weather_travel-20260528_062749/result.json` 显示 `completed=true`。
- 本轮 `permission_policy_decisions` 记录了结构化字段；`browser_open` 的 `reason` 为 `allow_tool_name_and_url_prefix`，`matched_text` 为 `https://api.open-meteo.com/v1/forecast`。
- 目标 agent 成功连接真实 Chrome 并读取 Open-Meteo 重庆 2026-05-31 天气 JSON，最终输出 `REAL_CHROME_CHONGQING_WEATHER_TRAVEL_OK`。
- 验收后已清理本轮测试启动的 Chrome 进程，并重新运行 `mcp-doctor` 确认 Chrome 未运行且环境可继续复测。

## 2026-05-27 重庆天气浏览器自动化功能测试记录

状态：已完成 CLI 入口真实大模型浏览器工具链测试、日志核对、py_compile 和 MCP doctor；本轮未修改业务代码，未 stage，未 commit。当前 Codex 环境未完成用户本地可见 `start_oauth_agent.bat` 交互窗口验收，因此不能把本轮表述为开发验收完成。

完成内容：
- 已确认当前日期为 2026-05-27，3 天后为 2026-05-30。
- 已通过目标 `learning_agent` 的 `run --prompt --json` 入口执行重庆 2026-05-30 天气查询和旅游攻略生成任务。
- 已要求目标 agent 先读取 `learning_agent/skills/tool_list.md`，再读取 `learning_agent/skills/browser_automation/SKILL.md`，随后必须调用浏览器自动化 MCP 工具。
- 最新 `learning_agent/debug_logs/latest_run_readable.md` 确认目标 agent 调用了 `mcp__browser_automation__browser_open` 打开 Open-Meteo URL，并调用 `mcp__browser_automation__browser_snapshot` 读取页面正文 JSON。
- 测试输出已保存到 `learning_agent/test/chongqing_weather_browser_20260527/cli_run_output.txt`，本次摘要另存到 `learning_agent/test/chongqing_weather_browser_20260527/summary.md`。

验证记录：
- `py_compile`：`learning_agent.py`、`test_learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py` 编译通过。
- 完整单元测试：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 332 tests in 22.105s OK (skipped=1)`。
- `mcp-doctor`：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功；真实 Chrome profile 诊断为 `available`；模型可见 MCP 工具 30 个。
- 浏览器快照读取到 Open-Meteo JSON：重庆 2026-05-30 最高 28.9°C、最低 21.9°C、最大降水概率 29%、weather_code=3、最大风速 5.2 km/h、紫外线指数 8.50。
- 日志证据位置：`learning_agent/debug_logs/latest_run_readable.md` 中 `browser_open 成功`、`browser_snapshot 成功` 和最终中文攻略均可核对。

## 2026-05-27 learning_agent 项目水平分析记录

状态：已完成只读分析、源码抽样核对、测试验证和 MCP doctor 验证；未修改业务代码，未 stage，未 commit。

完成内容：
- 已读取 `agent_memory/context.md`、`progress.md`、`bugs.md`、`learning_agent/README.md`、`staticprompt/staticprompt.md`、`dynamicprompt/dynamicprompt.md`、`skills/tool_list.md`。
- 已抽查 `learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py`、启动脚本和 MCP 配置，确认文档中的四原子工具面、ToolPolicy、Prompt Architecture、MCP、浏览器、计划模式和任务管理等能力有源码落点。
- 已确认 `learning_agent/test_learning_agent.py` 当前包含 332 条 unittest 测试。
- 已用 Codex 自带 Python 执行语法检查，目标文件包括 `learning_agent.py`、`test_learning_agent.py`、`tool_policy.py`、`prompt_registry.py`、`context_assembler.py`，结果通过。
- 已用 Codex 自带 Python 执行完整测试：`Ran 332 tests in 28.030s OK (skipped=1)`。
- 已执行 `learning_agent.py mcp-doctor`，确认 `browser_search`、`workspace_tools`、`browser_automation` 均启动成功，真实 Chrome profile 诊断为 `available`，模型可见 MCP 工具 30 个。

结论摘要：
- 当前 `learning_agent` 已达到“成熟 coding agent core 原型/教学版”的水平：核心架构、工具治理、提示词治理、MCP 接入、浏览器闭环和测试覆盖已经明显超过普通 demo。
- 当前仍不应宣称完整产品化或完全追平商业 Codex / Claude Code：真实可见终端交互验收不是本轮开发验收；真实 Chrome 登录态端到端、远程多用户安全、真实 git worktree、持久化定时任务和完整 UI 仍是边界。

## 2026-05-26 Prompt Files v3 执行记录

状态：实现已完成，聚焦测试和完整回归均已通过；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已将包内旧 `learning_agent/runtime_instructions.md` 重命名迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，旧文件路径不再保留。
- 已新增 `learning_agent/staticprompt/staticprompt.md`，承载每轮常驻的静态系统提示词，包含当前工作区占位符 `{{CURRENT_WORKSPACE}}`。
- 已修改 `learning_agent/learning_agent.py`，新增 `static_prompt_path` / `dynamic_prompt_path` 解析；`_build_initial_messages()` 改为读取 `staticprompt.md`，不再依赖 Python helper 拼系统提示词。
- 已删除源码中分散的静态系统提示词 helper，Python 只负责读取、占位符替换、兜底和动态规则发现。
- 已把 `dynamicprompt.md` 暴露为 `skill_load` 可读取的 `dynamicprompt` 伪 skill，保持动态规则按需加载。
- 已更新 `PromptRegistry`，把旧 `context.runtime_instructions` 元数据改为 `context.dynamic_prompt_index` 且标记为 `on_demand`。
- 已更新 `learning_agent/README.md` 和 `learning_agent/skills/prompt_architecture/SKILL.md`，说明新静态/动态提示词路径。
- 已新增/调整测试覆盖：静态提示词文件常驻加载、包内新文件存在、旧 runtime 文件删除、动态提示词不进首轮、动态提示词可通过 `skill_load` 按需加载。

验证记录：
- 红灯验证：新增聚焦测试先失败，失败点覆盖缺少 `static_prompt_path` / `dynamic_prompt_path`、默认提示词文件不存在。
- 聚焦绿灯：`Ran 6 tests in 0.100s OK`，覆盖本次文件化提示词迁移主路径。

## 2026-05-26 Lean System Prompt v2 执行记录

状态：已完成实现和完整回归验证，未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已将 `learning_agent/learning_agent.py` 的 `_build_core_identity_prompt()` 改为短核心身份，标题为 `Prompt Surface Architecture v2`。
- 已将 `_build_operating_principles_prompt()` 改为精简行为原则，保留工具可见文本、权限模式、Prompt Injection、Hooks、上下文压缩、先读代码、避免时间预估、失败诊断、安全和范围边界。
- 已将 `_build_context_policy_prompt()` 改为更明确的上下文优先级，纳入 `runtime_instructions.md`、`agent_memory` 三件套、`memory.md`、任务相关文件、工具 schema/MCP 说明和工具验证证据。
- 已从 `_build_initial_messages()` 的 `block_contents` 中移除 `prompt.policy.tool_boundary` 和 `prompt.policy.response`，避免每轮重复加载两块细节规则。
- 已重写 `learning_agent/runtime_instructions.md` 为短 Runtime Kernel，并把工具细节、skill router、capability pack、MCP/browser/real Chrome/delegation/diagnostics/cron/response policy 放入运行规则层。
- 已更新 `learning_agent/test_learning_agent.py` 的提示词回归测试，锁定新核心身份、精简 block 边界和 runtime skill router。
- 已把旧 `agent_memory/context.md`、`progress.md`、`bugs.md` 归档到 `agent_memory/archive/2026-05-26-lean-system-prompt/`，并将活跃三件套压缩为短摘要。

验证记录：
- 红灯验证：`test_system_prompt_uses_mature_coding_agent_identity` 首次失败，证明旧系统提示词仍在生效。
- 聚焦绿灯：`Ran 3 tests in 0.029s OK`，覆盖新系统身份、动态 compact 旧断言调整、短 runtime skill router。
- 完整回归首次只剩 1 个旧断言失败，原因是缺少 `知识与实时信息策略` 明确锚点。
- 已在 `runtime_instructions.md` 增加 `知识与实时信息策略` 小标题，保持核心系统提示词精简，同时满足实时信息策略锚点。
- 完整测试套件通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 313 tests in 21.527s OK (skipped=1)`。

下一步建议：
- 继续用 `prompt_surface_report` 和 `token_budget_report` 观察真实每轮提示词和工具池预算。
- 后续若再增长 runtime 关键词，应优先沉淀到 skill，而不是重新加回系统提示词。

## 2026-05-26 Dynamic Runtime Rules 执行记录

状态：已完成实现和完整回归验证，未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，让 `_build_initial_messages()` 不再把 `runtime_instructions.md` 作为 `context.runtime_instructions` 自动注入每轮 system prompt。
- 已把必要首轮底线上移到静态系统提示词：默认中文、证据边界、实时信息工具优先、动态规则加载路由、`skill_list`、`skill_load`、`tool_search`、`select_pack:<pack_name>`。
- 已修改 `skill_list` / `skill_load` 的发现范围，同时扫描工作区 `skills/` 和包内 `learning_agent/skills/`，让能力包规则可按需加载。
- 已把 `learning_agent/runtime_instructions.md` 改成动态运行规则索引，保留测试需要的工具关键词和规则入口，但不再作为每轮正文。
- 已更新 `learning_agent/skills/prompt_architecture/SKILL.md` 和 `learning_agent/README.md`，说明 runtime 现在是动态索引，不是常驻 prompt 正文。
- 已新增/调整测试覆盖 runtime 不再自动注入、静态 kernel 动态规则路由、包内 skills 可发现和可加载。

验证记录：
- 红灯验证：新增/调整的 5 条聚焦测试先失败，失败点覆盖 runtime 常驻注入、静态路由缺失、包内 skills 不可发现。
- 聚焦绿灯：同一组 5 条测试通过，输出 `Ran 5 tests in 0.064s OK`。
- 邻近 runtime/skill/prompt 回归通过，输出 `Ran 35 tests in 0.099s OK`。
- 完整测试套件通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 315 tests in 22.481s OK (skipped=1)`。
- 当时真实构造检查显示不包含 `context.runtime_instructions`；后续 Agent Memory Boundary 已进一步移除 `context.project_memory_index`。

## 2026-05-26 Prompt Files v3 最新状态

- 最新实现已把每轮静态系统提示词文件化到 `learning_agent/staticprompt/staticprompt.md`。
- 最新实现已把旧 runtime 文件迁移为 `learning_agent/dynamicprompt/dynamicprompt.md`，该文件只按需通过 `skill_load name=dynamicprompt` 或相关能力流程读取。
- 最新 `_build_initial_messages()` 加载块为：`prompt.kernel.identity`、`context.long_term_memory_index`。
- 本轮完整回归已通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 318 tests in 28.624s OK (skipped=1)`。
- 本轮学习备份已写入 `learning_agent/test/prompt_files_v3_20260526/`。

## 2026-05-26 Agent Memory Boundary 执行记录

状态：已完成实现、聚焦验证和完整回归；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已确认用户指出的问题成立：`agent_memory/context.md`、`progress.md`、`bugs.md` 是 Codex 开发本项目时的上下文，不应默认进入目标 `learning_agent` 的每轮 system prompt。
- 已修改 `learning_agent/learning_agent.py`，删除 `_read_project_agent_memory()` / `_find_project_agent_memory_dir()` 自动查找链路，并从 `_build_initial_messages()` 移除 `context.project_memory_index`。
- 已修改 `learning_agent/prompt_registry.py`，移除默认 `context.project_memory_index` prompt block。
- 已修改 `learning_agent/staticprompt/staticprompt.md`，删除 `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md` 的静态提示词关联。
- 已修改 `learning_agent/README.md`，说明目标 agent 每轮只默认读取 `staticprompt/staticprompt.md`、`memory.md` 和用户输入；`dynamicprompt.md` / skills 按需加载。

验证记录：
- 红灯验证：4 条聚焦测试先失败，失败点包含 `Project Memory Index` 仍进入 system prompt、静态提示词仍出现 `agent_memory/context.md`。
- 聚焦绿灯：同一组 4 条测试通过，输出 `Ran 4 tests in 0.032s OK`。
- 邻近回归：10 条 prompt/registry/预算测试通过，输出 `Ran 10 tests in 0.077s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 318 tests in 23.232s OK (skipped=1)`。
- 真实加载确认：`loaded_blocks=prompt.kernel.identity,context.long_term_memory_index`，`HAS_AGENT_MEMORY=False`，`HAS_MEMORY_INDEX=True`。

## 2026-05-26 Four Atom Tool Surface 执行记录

状态：已完成实现、README 同步、完整回归和语法检查；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已修改 `learning_agent/learning_agent.py`，新增首轮模型可见的 `read`、`write`、`edit`、`bash` 四个原子工具 schema。
- 已将 `KERNEL_TOOL_NAMES` 收敛为四原子工具；`tool_search`、`skill_load`、MCP 工具和其他内置工具继续保留在内部 catalog，但默认 deferred，不再进入首轮 Tool Pool。
- 已新增 `_read_atom()`、`_write_atom()`、`_edit_atom()`、`_bash_atom()` 执行路径，并在 `_execute_tool()` 中分发这四个原子工具。
- 已新增 `learning_agent/skills/tool_list.md`，作为模型通过 `read` 发现能力和 skill 文件路径的入口。
- 已更新 `learning_agent/staticprompt/staticprompt.md`、`learning_agent/dynamicprompt/dynamicprompt.md`、`learning_agent/README.md`，统一说明 read-based skill discovery 和四原子工具面。
- 已更新 `learning_agent/test_learning_agent.py`，把旧首轮 `tool_search` / `skill_load` / `select_pack` 预期改为 `read / write / edit / bash` 与 `tool_list.md`。
- 已修正 static prompt 兜底文案，避免静态提示词文件损坏时重新提示旧工具搜索和能力包语法。

验证记录：
- 红灯验证：新增四原子聚焦测试先失败，失败点覆盖旧 kernel 工具仍首轮可见、`tool_list.md` 不存在、dynamicprompt 仍旧路由。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 321 tests in 22.497s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。

## 2026-05-26 CLI / HTTP Command Bridge 执行记录

状态：已完成实现、README 同步、完整回归和语法检查；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已扩展 `MainArgs` 和 `parse_main_args()`，新增 `run` 命令、`--prompt`、`--json`、`bridge` 命令、`--bridge-host`、`--bridge-port`、`--bridge-token`。
- 已新增 `format_cli_run_response()`，让 CLI 一次性运行可以输出 Codex 易解析的 JSON。
- 已新增 `LearningAgentCommandBridgeServer`、`LearningAgentCommandBridgeHandler` 和 `create_command_bridge_server()`。
- HTTP bridge 支持 `GET /health` / `/v1/health`，返回 `ok`、`agent`、`workspace` 和 `visible_tools`。
- HTTP bridge 支持 `POST /run` / `/command` / `/v1/run` / `/v1/command`，接收 JSON `prompt` 和可选 `max_turns`，返回 JSON `answer`、`workspace`、`visible_tools` 和 `max_turns`。
- 已在 `main()` 中接入一次性 CLI run 和 bridge serve 模式，同时保持原交互模式和 `doctor/mcp-doctor` 兼容。
- 已更新 `learning_agent/README.md`，补充 CLI run 和 HTTP command bridge 的启动命令、认证方式和请求示例。

验证记录：
- 红灯验证：新增 3 条聚焦测试先失败，失败点为无法导入 `create_command_bridge_server`。
- 聚焦绿灯：同一组 3 条测试通过，输出 `Ran 3 tests in 0.540s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最新输出 `Ran 324 tests in 26.883s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。

## 2026-05-26 Dynamic Prompt Tree 执行记录

状态：已完成实现、README 同步、完整回归、语法检查和 CLI 真实入口验证；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已把 `learning_agent/skills/*/SKILL.md` 改成第二层轻入口，只保留能力判断、边界和 `rules/*.md` 子规则索引。
- 已新增 `learning_agent/skills/*/rules/*.md` 第三层子规则，承载 MCP、浏览器、真实 Chrome、文件、执行、计划、诊断、记忆、Notebook、委派和长期任务细节。
- 已从包内 skills 清理 `tool_search` / `select_pack` 旧路由文案，避免动态规则把模型拉回旧工具搜索架构。
- 已修改 `learning_agent/learning_agent.py`，让 `read` 记录已读取的动态提示词层级，并阻止模型跳过 `tool_list.md` 和父 `SKILL.md` 直接读取 `rules/*.md`。
- 已更新 `learning_agent/staticprompt/staticprompt.md`、`dynamicprompt/dynamicprompt.md`、`skills/tool_list.md` 和 README，统一描述 `tool_list.md -> SKILL.md -> rules/*.md` 三级加载顺序。
- 已更新 `learning_agent/test_learning_agent.py`，新增三级动态规则树和 read 层级门控回归测试，并调整旧 MCP skill 断言。

验证记录：
- 红灯验证：新增 2 条聚焦测试先失败，失败点覆盖所有旧 SKILL 缺少三级结构、`read` 可直接读取子规则。
- 聚焦绿灯：同一组 2 条测试通过，输出 `Ran 2 tests in 0.040s OK`。
- 相关回归：动态 prompt、skill、首轮工具池和 HTTP bridge 相关测试通过，输出 `Ran 4 tests in 0.604s OK` 与 `Ran 6 tests in 0.041s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 326 tests in 28.877s OK (skipped=1)`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- CLI 真实入口验证：通过 `LEARNING_AGENT_MODEL_PROVIDER=codex-cli` 执行 `learning_agent.py --max-turns 1 --prompt ... --json run`，返回 `ok=true`，回答确认采用 `tool_list.md -> SKILL.md -> rules/*.md` 分层，当前可见工具为 `read/write/edit/bash`。

## 2026-05-26 Current Date Prompt 执行记录

状态：已完成实现、单测回归、语法检查、CLI 真实入口验证和学习备份；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已新增 `learning_agent/learning_agent.py` 的 `get_local_iso_date()`，用本地日期生成 `YYYY-MM-DD`，作为系统提示词日期来源。
- 已修改 `_read_static_prompt()`，每轮读取 staticprompt 时替换 `{{CURRENT_DATE}}`，让 agent 每轮都能看到当天真实日期。
- 已修改 fallback static prompt，在静态提示词文件缺失、为空或路径异常时仍写入当前日期。
- 已修改 `learning_agent/staticprompt/staticprompt.md`，新增 `当前日期：{{CURRENT_DATE}}`，保持静态文件不写死日期。
- 已新增 `learning_agent/test_learning_agent.py` 聚焦测试，验证第一轮和第二轮 system prompt 都包含当天日期且不泄漏 `{{CURRENT_DATE}}`。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/current_date_prompt_20260526/`。

验证记录：
- 红灯验证：`python -m unittest learning_agent.test_learning_agent.LearningAgentTests.test_static_prompt_renders_current_date_each_turn` 先失败，失败点为 system prompt 仍包含 `{{CURRENT_DATE}}` 而非 `2026-05-26`。
- 聚焦绿灯：同一条测试通过，输出 `Ran 1 test in 0.011s OK`。
- 相关回归：`test_static_prompt_file_is_loaded_into_system_prompt`、`test_static_prompt_renders_current_date_each_turn`、`test_system_prompt_contains_current_info_policy` 三条通过，输出 `Ran 3 tests in 0.048s OK`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 最终单独重跑输出 `Ran 329 tests in 23.137s OK (skipped=1)`。
- CLI 真实入口验证：通过 `LEARNING_AGENT_MODEL_PROVIDER=codex-cli` 执行 `learning_agent.py run --max-turns 1 --prompt "请只回答你在系统提示词中看到的当前日期..." --json`，返回 `ok=true` 且 `answer` 为 `2026-05-26`。

## 2026-05-26 Browser Automation 执行记录

状态：已完成实现、动态提示词同步、单测回归、完整回归、MCP doctor、HTTP command bridge 真实浏览器闭环和学习备份；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已新增 read-based dynamic skill unlock：读取 `browser_automation/SKILL.md` 后自动加载 `browser_automation` MCP 工具包。
- 已新增 real Chrome read-based 准备逻辑：读取 `real_chrome/SKILL.md` 后准备 `real_chrome` 和后续页面操作工具，但 connect 仍受 `browser_profile_status` workflow gate 保护。
- 已让读取 `real_chrome/SKILL.md` 自动设置 `real_chrome_requested=True`，防止真实 Chrome 路线在连接前误走独立 Chromium。
- 已让 `_resolve_workspace_path()` 兼容 CLI 默认 `learning_agent` 工作区下的 `learning_agent/skills/...` 项目根风格路径。
- 已同步更新 `browser_automation`、`real_chrome` 两个 SKILL.md 和子规则，说明读取 skill 后工具解锁与 profile status 前置边界。
- 已新增 3 条回归测试，覆盖 browser skill 解锁、real Chrome workflow 解锁、CLI 包目录路径兼容。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/browser_automation_20260526/`。

验证记录：
- 红灯验证：新增 2 条浏览器聚焦测试先失败，失败点为读取 skill 后 `browser_open` / `browser_connect_real_chrome` 仍未进入 Tool Pool。
- 聚焦绿灯：新增浏览器与路径兼容测试通过，输出 `Ran 3 tests in 0.030s OK`。
- 语法检查：`python -m py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 330 tests in 21.752s OK (skipped=1)`。
- MCP doctor：`learning_agent.py mcp-doctor` 显示 browser_search、workspace_tools、browser_automation 均启动成功，真实 Chrome profile 诊断为 `available`。
- HTTP command bridge 真实闭环：通过本地 bridge POST `/run` 下发真实 prompt，agent 读取 browser skill 后调用真实 MCP `browser_open` 和 `browser_snapshot`，返回 `ok=true`。

## 2026-05-26 Browser Weather Travel 真实验收执行记录

状态：已完成真实大模型端到端验收、CLI 入口验收、完整回归和启动脚本 selftest；未 stage，未 commit，未清理用户或历史改动。

完成内容：
- 已按用户要求让目标 agent 查询 2026-05-29 北京天气并生成旅游攻略；该日期是当前日期 2026-05-26 的 3 天后。
- 已修复 `real browser automation` 被 `_detect_real_chrome_intent()` 误判为真实 Chrome/profile 请求的问题，避免普通 Playwright browser task 隐藏 `browser_open`。
- 已补齐 `_final_answer_retry_message()`，修复 HTTP bridge 在最终回答阶段因缺失方法返回 500 的问题。
- 已通过 HTTP command bridge 让真实 `CodexCliChatModel` 驱动目标 agent：先读取 `learning_agent/skills/tool_list.md`，再读取 `learning_agent/skills/browser_automation/SKILL.md`，随后调用 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- 已通过 CLI `learning_agent.py run --prompt ... --json` 再跑一次真实浏览器任务，权限输入自动喂 `y`，最新调试日志确认同样完成 `browser_open` 和 `browser_snapshot`。
- 已运行 `cmd /c learning_agent\start_oauth_agent.bat selftest`，验证用户指定启动脚本的自检路径可用。

验证记录：
- 聚焦回归：真实浏览器误判、browser skill 解锁、real Chrome workflow、Codex adapter 指令测试通过，输出 `Ran 6 tests in 0.665s OK`。
- 缺失方法修复回归：`test_run_retries_final_answer_when_required_markdown_headings_are_missing` 等 4 条通过，输出 `Ran 4 tests in 0.040s OK`。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 332 tests in 22.082s OK (skipped=1)`。
- 启动脚本 selftest：`cmd /c learning_agent\start_oauth_agent.bat selftest` 输出 `Ran 332 tests in 21.613s OK (skipped=1)`。
- HTTP bridge 真实验收结果保存到 `learning_agent/test/browser_weather_travel_20260526/result.json`，其中 `completed_browser_calls` 为 `mcp__browser_automation__browser_open` 和 `mcp__browser_automation__browser_snapshot`。
- CLI 真实验收输出保存到 `learning_agent/test/browser_weather_travel_20260526/cli_run_output.txt`；该文件因 Windows 管道编码显示中文乱码，但 `learning_agent/debug_logs/latest_run_readable.md` 保留了可读中文调试证据。
- 最新浏览器快照读取到 Open-Meteo JSON：最高 30.5°C、最低 17.0°C、最大降水概率 0%、weather_code=1、最大风速 14.6 km/h。

## 2026-05-28 Real Chrome Google Human Visible 执行记录

状态：已完成实现、红绿灯回归、完整单测、MCP Doctor、真实可见终端交互验收和截图验证；未 stage，未 commit。

完成内容：
- 新增 `real_chrome_google_human_search.json` 场景，用于验证真实桌面 Chrome 打开 Google 后执行点击、输入、回车、等待、截图和快照读取。
- 修改 `controller.ps1`，新增 `post_success_wait_seconds`，场景成功后可保留真实窗口 20 秒让用户肉眼观察。
- 修改 `learning_agent.py`，让 `final_answer_printed` 事件保留 `answer_text` 完整回答，同时继续保留 `answer_preview`。
- 修改 `controller.ps1`，事件回答断言优先检查完整 `answer_text`，旧事件没有该字段时再退回 `answer_preview`。
- 新增/更新 `test_learning_agent.py` 回归测试，锁定 Google 拟人场景、成功后停留字段、完整回答事件字段和 controller 完整回答断言。

验证记录：
- 红灯验证：`test_acceptance_controller_script_uses_generic_event_protocol` 与 `test_interactive_acceptance_event_includes_full_final_answer_text` 先失败，证明旧 controller 不认识 `answer_text`，旧交互事件只写 `answer_preview`。
- 聚焦绿灯：同两条测试通过，输出 `Ran 2 tests in 0.037s OK`。
- 语法检查：`python -m py_compile learning_agent\acceptance_harness.py learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- PowerShell 解析：`[scriptblock]::Create($text)` 检查 `controller.ps1` 通过。
- 完整回归：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 339 tests in 21.962s OK (skipped=1)`。
- MCP Doctor：`learning_agent.py mcp-doctor` 显示 browser_search、workspace_tools、browser_automation 均启动成功，真实 Chrome profile `available`，运行前 Chrome 正在运行为 `false`。
- 第一次真实可见终端验收实际完成了 Google 点击输入截图，但因为 `answer_preview` 截断在 `- br`，`event_answer_checks.browser_screenshot=false`，控制器误判失败；该根因已修复。
- 第二次真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_google_human_search-20260528_064903/result.json` 显示 `completed=true`。
- Google 搜索结果页截图已目视验证非空，路径为 `learning_agent/browser_artifacts/real_chrome_google_human_search_20260528.png`。

## 2026-05-28 Real Browser Task Harness 执行记录

状态：已完成通用真实浏览器查询 harness、自然短 prompt 验收场景、红绿灯回归、完整单测、MCP Doctor、真实可见终端交互验收、截图验证、Chrome 清理；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`：补充 `真实浏览器` 触发词，新增 `_detect_real_browser_information_task()` 和 `_build_real_browser_task_harness_message()`，并在 `_build_initial_messages()` 中按需拼接 `Real Browser Task Harness`。
- 已修改 `learning_agent/skills/real_chrome/SKILL.md`：新增 `search_task_workflow.md` 子规则索引。
- 已新增 `learning_agent/skills/real_chrome/rules/search_task_workflow.md`：沉淀会议、酒店、航班、资料、天气、旅游攻略等公开查询的通用真实 Chrome Google 搜索流程。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_weather_travel.json`：使用自然短 prompt 触发真实浏览器查询，不把 `browser_click` / `browser_type` 等工具步骤写进用户 prompt。
- 已修改 `learning_agent/acceptance_controller/README.md`：补充自然短 prompt 真实浏览器验收场景运行命令。
- 已修改 `learning_agent/test_learning_agent.py`：新增短语识别、harness 注入、real_chrome 通用规则、自然短 prompt 场景契约回归测试。

验证记录：
- 红灯验证：4 条新增测试先失败，失败点分别为“真实浏览器”短语漏判、首轮没有 `Real Browser Task Harness`、`real_chrome` skill 未索引 `search_task_workflow.md`、自然短 prompt 场景文件不存在。
- 聚焦绿灯：同 4 条测试转绿，输出 `Ran 4 tests in 0.044s OK`。
- 第一次真实可见终端验收实际完成了真实 Chrome Google 搜索、点击、输入、回车、截图和攻略回答，但最终回答缺少机器可读 `real_chrome_connected=true` / `browser_click` 等工具名，导致 `event_answer_checks` 失败。
- 根因修复：harness 和 `search_task_workflow.md` 已要求最终回答包含 `real_chrome_connected=true` 和关键工具名；新增聚焦断言先失败再转绿。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\acceptance_harness.py`。
- PowerShell 解析通过：`[scriptblock]::Create($text)` 检查 `controller.ps1` 成功。
- 完整单测通过：`Ran 342 tests in 25.124s OK (skipped=1)`。
- MCP Doctor 通过：browser_search、workspace_tools、browser_automation 均启动成功；真实 Chrome profile `available`；最终清理后 Chrome 正在运行状态为 `false`，默认端口可用为 `true`。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260528_073250/result.json` 显示 `completed=true`。
- 验收结果确认：权限策略默认拒绝，实际放行 11 次；日志断言和最终回答断言全部为 true；最终回答含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`、`real_chrome_connected=true`、关键工具名和截图路径。
- 截图目视确认：`learning_agent/browser_artifacts/real_chrome_chongqing_weather_travel_20260531.png` 是 Google 搜索结果页，搜索词为“重庆 2026年5月31日 天气 旅游攻略”。

## 2026-05-28 Real Browser Customer Mode 执行记录

状态：已完成红灯测试、实现、聚焦回归、完整单测、MCP Doctor、真实可见终端交互验收、截图验证和 Chrome 清理；未 stage，未 commit。

完成内容：
- 已新增 `ask_permission_from_terminal_customer_mode()`，项目内置 MCP 启动默认自动允许并发送 `permission_auto_approved` 事件，不再调用 `input()`。
- 已修改 `main()` 使用客户模式权限入口；JSON 一次性运行时会关闭启动进度文本，避免污染机器可读输出。
- 已新增 `real_browser_information_task_requested`，只在真实浏览器公开信息查询任务中启用自动授权。
- 已新增真实浏览器工具自动授权白名单和进度提示，用户会看到 `Agent > 正在检查真实 Chrome 状态...`、`Agent > 正在输入搜索词...` 等操作说明。
- 已更新 `controller.ps1`，支持 `max_permission_sent_count` 与 `permission_count_passed`，可自动证明客户模式没有 y/N 权限输入。
- 已更新自然短 prompt 真实浏览器验收场景，要求 `max_permission_sent_count` 为 0，并移除 `permission_required` / `permission_answered` 必需事件。
- 已按学习备份规则复制本次改动文件到 `learning_agent/test/real_browser_customer_mode_20260528/`。

验证记录：
- 红灯验证：新增测试最初因 `ask_permission_from_terminal_customer_mode` 不存在而失败，证明旧实现没有客户模式权限入口。
- 聚焦绿灯：客户模式 MCP 启动、白名单浏览器工具自动授权、敏感 `browser_evaluate` 不自动授权、验收场景和 controller 协议 5 条测试通过，输出 `Ran 5 tests in 0.066s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py learning_agent\acceptance_harness.py`；PowerShell `[scriptblock]::Create($text)` 解析 `controller.ps1` 通过。
- 完整单测通过：`Ran 345 tests in 27.780s OK (skipped=1)`。
- MCP Doctor 初次发现 9222 调试 Chrome 残留；已确认根进程命令行含 `--remote-debugging-port=9222 about:blank`，仅清理该自动化 Chrome 根进程。
- 清理后 MCP Doctor 通过：真实 Chrome profile `available`，Chrome 正在运行 `false`，默认端口可用 `true`，browser_search/workspace_tools/browser_automation 均启动成功。
- 真实可见终端交互验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260528_082044/result.json` 显示 `completed=true`。
- 无 y 验收关键结果：`permission_sent_count=0`、`max_permission_sent_count=0`、`permission_count_passed=true`；事件序列只有 `permission_auto_approved`、`agent_ready_for_user_prompt`、`user_prompt_received`、`final_answer_printed`、`agent_ready_for_user_prompt`，没有 `permission_required` 或 `permission_answered`。
- 真实浏览器截图已目视确认：`learning_agent/browser_artifacts/chongqing_weather_travel_2026-05-31.png` 为 Google 搜索结果页，搜索词是“重庆 2026年5月31日 天气 旅…”。
- 验收后已清理本次调试 Chrome 根进程，再次 MCP Doctor 确认 Chrome 未运行且 9222 端口可用。

## 2026-05-28 Real Browser YouTube Customer Mode 执行记录

状态：已完成根因确认、红灯测试、实现、聚焦回归、真实可见终端验收、截图验证、Chrome 清理和 MCP Doctor 复查；未 stage，未 commit。

完成内容：
- 已修改 `learning_agent/learning_agent.py`：把 YouTube/视频/评论/排行/有哪些等自然公开查询表达纳入 `_detect_real_browser_information_task()`。
- 已修改 `learning_agent/test_learning_agent.py`：新增 YouTube 自然短 prompt 识别测试，并把 YouTube 真实终端场景加入场景有效性检查列表。
- 已新增 `learning_agent/acceptance_controller/scenarios/real_chrome_natural_youtube_video_comments.json`：复现用户截图 prompt，要求真实终端验收中 `permission_sent_count=0`。
- 已清理用户截图旧会话残留的自动化 Chrome/MCP 子进程，用于释放 9222 端口；未杀掉用户可见终端主进程，但旧终端不会热加载新代码，需要重启 `start_oauth_agent.bat`。

验证记录：
- 红灯验证：`test_real_browser_youtube_video_question_is_customer_information_task` 先失败，失败点为 `_detect_real_browser_information_task(youtube_prompt)` 返回 `False`。
- 聚焦绿灯：YouTube 识别、客户模式自动授权、敏感工具拒绝、场景结构 4 条测试通过，输出 `Ran 4 tests in 0.041s OK`。
- 语法检查通过：`py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py`。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_youtube_video_comments-20260528_091026/result.json` 显示 `completed=true`。
- 无 y 验收关键结果：`permission_sent_count=0`、`max_permission_sent_count=0`、`permission_count_passed=true`；事件序列没有 `permission_required` 或 `permission_answered`。
- 验收日志确认真实浏览器动作：`browser_profile_status`、`browser_connect_real_chrome`、`browser_open`、`browser_click`、`browser_type`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_snapshot` 全部命中断言。
- 真实终端截图已目视确认：`learning_agent/acceptance_controller/runs/real_chrome_natural_youtube_video_comments-20260528_091026/03_final.png` 展示最终回答和验收事件。
- 验收后已清理本次调试 Chrome 根进程，再次 MCP Doctor 确认 Chrome 正在运行 `false`，默认端口可用 `true`，3 个 MCP server 均启动成功。

## 2026-05-29 learning_agent 模块化重构实施计划记录

状态：已完成完整蓝图固化为正式实施计划文档；本轮未开始拆代码，未修改业务逻辑，未运行单元测试或真实终端功能验收。

完成内容：
- 已新增正式计划文档 `docs/superpowers/plans/2026-05-29-learning-agent-modular-refactor.md`。
- 计划覆盖阶段 0 到阶段 12：锁定基线、建立目录骨架、拆 core、拆 models、拆 mcp、拆 tools、拆 prompts、拆 browser、拆 tasks、拆 observability、整理 app、拆测试文件、瘦身 `learning_agent.py`。
- 已在计划中明确最终完成定义：阶段 12 完成后，必须同时满足结构完成、功能未回退、完整 unittest 通过、`mcp-doctor` 通过、真实可见终端验收通过、真实 Chrome 客户模式 `permission_sent_count=0`、文档同步完成，才算整体改造完成。
- 已新增学习备份 `learning_agent/test/modular_refactor_plan_20260529/IMPLEMENTATION_PLAN_BACKUP.md`。

下一步：
- 从阶段 0 开始执行，不直接跳到拆代码。
- 每阶段先读相关文件，再做聚焦迁移。
- 每阶段修改代码都需要逐行中文注释，并备份到 `learning_agent/test/<阶段名_日期>/`。
- 涉及 agent 行为变化的阶段必须完成真实可见终端 `start_oauth_agent.bat` 验收后，才能声明该阶段完成。

## 2026-05-29 learning_agent 模块化重构阶段 0 基线

状态：阶段 0 已完成；本阶段只做基线读取和验证，没有修改业务代码。

完成内容：
- 已记录 `learning_agent.py` 当前大小为 1056623 bytes。
- 已记录 `test_learning_agent.py` 当前大小为 1102954 bytes。
- 已创建基线文件 `learning_agent/test/modular_refactor_baseline_20260529/baseline.md`。
- 已把正式计划文档中的阶段 0 复选框标记为完成。

验证记录：
- 完整单元测试通过：`Ran 346 tests in 26.337s OK (skipped=1)`。
- MCP Doctor 通过：`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。
- 真实 Chrome profile 诊断为 `available`，Chrome 正在运行 `false`，默认端口可用 `true`。
- 历史真实 Chrome 天气旅游验收记录确认：`completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。
- 历史真实 Chrome YouTube 查询验收记录确认：`completed=true`、`permission_sent_count=0`、`permission_count_passed=true`。

下一步：
- 进入阶段 1：建立目录骨架和兼容导出。

## 2026-05-29 learning_agent 模块化重构阶段 1 目录骨架

状态：阶段 1 已完成；本阶段只新增目标目录和 `__init__.py`，没有迁移业务逻辑。

完成内容：
- 已新增 `learning_agent/app/__init__.py`。
- 已新增 `learning_agent/core/__init__.py`。
- 已新增 `learning_agent/models/__init__.py`。
- 已新增 `learning_agent/tools/__init__.py`。
- 已新增 `learning_agent/mcp/__init__.py`。
- 已新增 `learning_agent/browser/__init__.py`。
- 已新增 `learning_agent/prompts/__init__.py`。
- 已新增 `learning_agent/memory/__init__.py`。
- 已新增 `learning_agent/tasks/__init__.py`。
- 已新增 `learning_agent/observability/__init__.py`。
- 已新增 `learning_agent/tests_support/__init__.py`。
- 已新增学习备份说明 `learning_agent/test/modular_refactor_stage1_20260529/README.md`。
- 已把正式计划文档中的阶段 1 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\test_learning_agent.py` 通过。
- 完整单元测试通过：`Ran 346 tests in 22.125s OK (skipped=1)`。

下一步：
- 进入阶段 2：拆 `core/messages.py` 和 `core/config.py`。

## 2026-05-29 learning_agent 模块化重构阶段 2 core 拆分

状态：阶段 2 已完成；已把基础配置解析与模型消息结构迁移到 `learning_agent/core/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/core/messages.py`，承载 `ToolCall` 和 `ModelMessage`。
- 已新增 `learning_agent/core/config.py`，承载运行配置、CLI 参数解析、轮次策略、prompt 软预算和本地日期函数。
- 已修改 `learning_agent/learning_agent.py`：从 `core.config` 和 `core.messages` 导入上述对象，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_core_messages_exports_tool_call_and_model_message`、`test_core_config_exports_runtime_parsers`。
- 已新增/更新学习备份目录 `learning_agent/test/modular_refactor_stage2_20260529/`。
- 已把正式计划文档中的阶段 2 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\core\messages.py learning_agent\core\config.py learning_agent\test_learning_agent.py` 通过。
- 聚焦测试通过：`python -m unittest learning_agent.test_learning_agent -k core` 输出 `Ran 2 tests in 0.001s OK`。
- 完整单元测试通过：`Ran 349 tests in 22.847s OK (skipped=1)`。

验证中发现并处理的问题：
- `mcp-doctor` 访问真实 Chrome User Data 目录时，如果 Windows 返回 `PermissionError`，会直接崩溃；已修改 `browser_real_chrome.py` 让不可访问候选路径被跳过并继续生成诊断报告。
- 后台命令在 Windows sandbox 下 `taskkill` 可能返回 `Access denied`，导致子进程继续占用临时工作目录；已让后台命令在 Windows 使用独立进程组，并优先用 `CTRL_BREAK_EVENT` 收束进程组，同时关闭管道并等待 reader 线程退出。

下一步：
- 进入阶段 3：拆 `models/`。

## 2026-05-29 learning_agent 模块化重构阶段 3 models 拆分

状态：阶段 3 已完成；已把模型接口、OpenAI-compatible 模型、Codex CLI 模型、Codex OAuth/API 模型和 OAuth token 逻辑迁移到 `learning_agent/models/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/models/base.py`，承载 `ChatModel` 模型接口。
- 已新增 `learning_agent/models/adapters.py`，承载 `OpenAIChatModel`、`CodexCliChatModel`、`CodexOAuthTokens`、`CodexOAuthTokenStore`、`CodexOAuthChatModel`。
- 已新增 `learning_agent/models/openai_chat.py`、`codex_cli.py`、`oauth_tokens.py`、`codex_oauth.py` 作为稳定导入入口。
- 已修改 `learning_agent/learning_agent.py`：从 `models/` 导入模型类和回调类型，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_models_package_exports_chat_model_adapters`，锁定新模块导出和旧入口兼容。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage3_20260529/`。
- 已把正式计划文档中的阶段 3 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\models\base.py learning_agent\models\adapters.py learning_agent\models\openai_chat.py learning_agent\models\codex_cli.py learning_agent\models\oauth_tokens.py learning_agent\models\codex_oauth.py learning_agent\test_learning_agent.py` 通过。
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.models.base'`。
- 模型导入测试迁移后通过：`Ran 1 test in 0.000s OK`。
- 聚焦测试通过：`-k models` 输出 `Ran 1 test in 0.000s OK`。
- 聚焦测试通过：`-k oauth` 输出 `Ran 12 tests in 0.006s OK`。
- 聚焦测试通过：`-k codex_cli` 输出 `Ran 3 tests in 0.014s OK`。
- 完整单元测试通过：`Ran 350 tests in 21.976s OK (skipped=1)`。

验证中观察：
- 按计划没有改变模型请求 body、OAuth 刷新、重登录或远端断连判断，只改变代码所在文件。
- 完整测试第一次运行时，浏览器上传下载测试偶发读到空下载文件；随后单独复现通过，完整测试重跑通过。当前判断为浏览器下载异步落盘时序观察，已记录到 `agent_memory/bugs.md`，阶段 3 不修改该浏览器模块。

下一步：
- 进入阶段 4：拆 `mcp/`。

## 2026-05-29 learning_agent 模块化重构阶段 4 MCP 拆分

状态：阶段 4 已完成；已把 MCP 配置、客户端、registry、auth challenge 和 doctor 迁移到 `learning_agent/mcp/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/mcp/runtime.py`，承载 MCP 运行时主实现。
- 已新增 `learning_agent/mcp/config.py`、`auth.py`、`stdio_client.py`、`http_client.py`、`sse_client.py`、`registry.py`、`doctor.py`、`tool_adapter.py` 作为稳定导入入口。
- 已修改 `learning_agent/mcp/__init__.py`：统一 re-export MCP 公开对象。
- 已修改 `learning_agent/learning_agent.py`：从 `mcp/` 导入 MCP 对象，并保留直接脚本运行 fallback。
- 已修改 `learning_agent/test_learning_agent.py`：新增 `test_mcp_package_exports_config_and_registry`，锁定新模块导出和旧入口兼容。
- 已处理阶段 4 暴露的 doctor monkeypatch 兼容问题：`run_mcp_doctor()` 通过兼容层优先读取旧主入口诊断替身，再回退真实诊断。
- 已处理重复出现的浏览器下载落盘时序问题：上传下载测试现在等待两个下载文件内容都包含 `hello-download` 后才判定完成。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage4_20260529/`。
- 已把正式计划文档中的阶段 4 复选框标记为完成。

验证记录：
- `py_compile learning_agent\learning_agent.py learning_agent\mcp\runtime.py learning_agent\test_learning_agent.py` 通过。
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.mcp.config'`。
- MCP 导入测试迁移后通过：`Ran 1 test in 0.000s OK`。
- 聚焦 doctor 测试通过：`Ran 1 test in 0.007s OK`。
- 浏览器上传下载聚焦测试通过：`Ran 1 test in 3.124s OK`。
- MCP 全组测试通过：`Ran 105 tests in 16.259s OK`。
- `learning_agent\learning_agent.py mcp-doctor` 退出码为 0，并列出 30 个 MCP 工具。
- 完整单元测试通过：`Ran 351 tests in 22.502s OK (skipped=1)`。

下一步：
- 进入阶段 5：拆 `tools/`。

## 2026-05-29 learning_agent 模块化重构阶段 5 tools 拆分

状态：阶段 5 已完成；已把工具元数据、catalog、工具池过滤、执行分发、策略兼容入口、四原子轻量 helper 和长结果存储 helper 迁移到 `learning_agent/tools/`，旧入口仍兼容。

完成内容：
- 已新增 `learning_agent/tools/types.py`，承载 `AgentTool`。
- 已新增 `learning_agent/tools/catalog.py`，承载 `agent_tool_from_schema`、`builtin_tool_capability_pack`、`build_builtin_tool_catalog`。
- 已新增 `learning_agent/tools/pool.py`，承载当前工具池、allowed_tools 过滤、工具名提取和策略决策 helper。
- 已新增 `learning_agent/tools/executor.py`，承载 `_execute_tool` 的执行守卫和分发表。
- 已新增 `learning_agent/tools/policy.py`，作为 `ToolPolicy` 新命名空间兼容入口。
- 已新增 `learning_agent/tools/atom_tools.py`，承载四原子工具轻量 helper。
- 已新增 `learning_agent/tools/result_storage.py`，承载长工具结果文件名、inline limit 和摘要 helper。
- 已修改 `learning_agent/learning_agent.py`：删除本地 `AgentTool` 和 catalog builder 实现；`_execute_tool` 改为委托 `tools.executor`；工具池、结果存储和原子工具轻量逻辑改为委托 `tools/`。
- 已修改 `learning_agent/test_learning_agent.py`：新增/扩展工具层导入测试，覆盖 `types`、`catalog`、`pool` 和 `policy` 新入口。
- 已把正式计划文档中的阶段 5 复选框标记为完成。

验证记录：
- 红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.tools.catalog'`。
- `py_compile learning_agent\learning_agent.py learning_agent\tools\*.py learning_agent\test_learning_agent.py` 通过。
- 工具层新导入测试通过：`Ran 1 test in 0.009s OK`。
- 工具 catalog 聚焦测试通过：`Ran 2 tests in 0.013s OK`。
- 原子工具聚焦测试通过：`Ran 3 tests in 0.035s OK`。
- 长结果落盘聚焦测试通过：`Ran 1 test in 0.027s OK`。
- 权限测试通过：`Ran 20 tests in 0.251s OK`。
- 工具全组测试通过：`Ran 134 tests in 5.156s OK`。
- `learning_agent\learning_agent.py mcp-doctor` 退出码为 0，并列出 30 个 MCP 工具。
- 完整单元测试通过：`Ran 352 tests in 22.522s OK (skipped=1)`。

当前结构说明：
- `learning_agent.py` 仍保留大量具体工具实现方法，这是为了避免一次性搬动文件、后台命令、task、team、plan、lsp、cron 等多类副作用逻辑。
- 阶段 5 已完成“工具层边界”和“执行入口分发表”拆分；后续阶段 6-8 可以继续把 prompts/browser/app/session 相关具体实现迁出。

下一步：
- 进入阶段 6：拆 `prompts/`。

## 2026-05-29 learning_agent 模块化重构阶段 6 prompts 拆分

状态：阶段 6 已完成；已把静态提示词、动态提示词、提示词注册表、上下文装配、token 预算和提示词表面报告入口收拢到 `learning_agent/prompts/`，旧入口仍保持兼容。

完成内容：
- 已新增 `learning_agent/prompts/static_prompt.py`，承载 `staticprompt.md` 路径解析、读取、`{{CURRENT_WORKSPACE}}` 与 `{{CURRENT_DATE}}` 渲染、空文件/缺失文件/目录路径兜底。
- 已新增 `learning_agent/prompts/dynamic_prompt.py`，承载 `dynamicprompt.md` 路径解析和伪 skill 元信息生成，保持 dynamicprompt 按需读取，不进入常驻 system prompt。
- 已新增 `learning_agent/prompts/registry.py`，作为 `PromptRegistry`、`PromptBlock` 和 `build_default_prompt_registry` 的新命名空间兼容入口。
- 已新增 `learning_agent/prompts/context_assembler.py`，作为 `ContextAssembler`、`PromptSurfaceReport`、`build_long_term_memory_index` 等上下文装配对象的新命名空间兼容入口。
- 已新增 `learning_agent/prompts/token_budget.py` 和 `learning_agent/prompts/surface_report.py`，为后续预算和报告继续瘦身提供稳定入口。
- 已修改 `learning_agent/prompts/__init__.py`，统一 re-export prompts 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 prompts 层导入 prompt/context 对象，并把 `_read_static_prompt()`、`_fallback_static_prompt()`、`_resolve_static_prompt_path()`、`_resolve_dynamic_prompt_path()`、`_dynamic_prompt_skill_metadata()` 改成委托新模块。
- 已修改 `learning_agent/test_learning_agent.py`，新增 `test_prompts_package_exports_static_prompt_loader`，锁定新 prompts 包入口。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage6_20260529/`，保存阶段 6 修改后的主文件、测试文件、prompts 模块和实施计划快照。
- 已把正式实施计划文档中的阶段 6 四个步骤全部勾选完成。

验证记录：
- 红灯验证：新增 prompts 导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.prompts.static_prompt'`。
- 语法检查通过：`py_compile learning_agent.py prompts/*.py test_learning_agent.py`。
- 新增导入测试通过：`Ran 1 test in 0.000s OK`。
- prompt 专项回归通过：`python -m unittest learning_agent.test_learning_agent -k prompt` 输出 `Ran 46 tests in 1.012s OK`。
- context 专项回归通过：`python -m unittest learning_agent.test_learning_agent -k context` 输出 `Ran 7 tests in 0.017s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 353 tests in 27.346s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个；当前真实 Chrome 诊断为 `blocked`，原因为本机已有 Chrome 正在运行且未找到可用 User Data 路径，本阶段未触碰真实 Chrome 功能。

当前结构说明：
- `learning_agent.py` 仍保留提示词构建的编排职责，但文件化 prompt 的细节已经移入 `prompts/`。
- `prompt_registry.py` 和 `context_assembler.py` 目前作为旧兼容实现继续存在，`prompts/registry.py` 与 `prompts/context_assembler.py` 先作为稳定新入口重导出，避免一次性移动大段已测试代码造成风险。

下一步：
- 进入阶段 7：拆 `browser/`，重点迁移真实浏览器意图识别、真实 Chrome harness、客户模式授权白名单和搜索工作流。

## 2026-05-29 learning_agent 模块化重构阶段 7 browser 拆分

状态：阶段 7 已完成；已把真实浏览器意图识别、真实浏览器任务 harness、客户模式自动授权、Google 搜索流程常量和浏览器产物路径安全 helper 收拢到 `learning_agent/browser/`，旧入口仍保持兼容。

完成内容：
- 已新增 `learning_agent/browser/intent.py`，承载真实 Chrome 意图、真实浏览器公开信息查询意图、独立浏览器工具集合和真实 Chrome 前置阻断判断。
- 已新增 `learning_agent/browser/harness.py`，承载自然短 prompt 的真实浏览器查询任务约束文本。
- 已新增 `learning_agent/browser/permissions.py`，承载真实浏览器客户模式是否激活、MCP 工具自动授权原因、终端 MCP 启动自动授权和客户可见进度文案。
- 已新增 `learning_agent/browser/search_workflow.py`，承载 Google URL 白名单、客户模式固定工具白名单和最终回答动作名清单。
- 已新增 `learning_agent/browser/artifacts.py`，承载浏览器截图/下载产物文件名清洗和安全路径生成。
- 已修改 `learning_agent/browser/__init__.py`，统一 re-export browser 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 browser 层导入上述 helper，并让旧方法入口委托新模块。
- 已修改 `learning_agent/browser_automation_mcp_server.py`，让 `safe_artifact_path()` 先委托 `browser.artifacts.safe_browser_artifact_path()`。
- 已修改 `learning_agent/test_learning_agent.py`，新增真实浏览器意图、客户模式权限和产物路径 helper 的模块入口测试。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage7_20260529/`，保存阶段 7 修改后的主文件、测试文件、browser 模块、MCP server 和实施计划快照。
- 已把正式实施计划文档中的阶段 7 六个步骤全部勾选完成。

验证记录：
- 红灯验证：新增浏览器意图导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.browser.intent'`。
- 语法检查通过：`py_compile learning_agent.py browser/*.py browser_automation_mcp_server.py test_learning_agent.py`。
- 新增浏览器层导入/权限/产物路径测试通过：3 条测试均 OK。
- 浏览器专项回归通过：`-k real_browser` 输出 `Ran 7 tests in 0.042s OK`。
- 真实 Chrome 专项回归通过：`-k real_chrome` 输出 `Ran 36 tests in 3.862s OK (skipped=1)`。
- YouTube 客户模式专项回归通过：`-k youtube` 输出 `Ran 1 test in 0.003s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 356 tests in 22.521s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260529_105333/result.json` 显示 `completed=true`、`permission_sent_count=0`、`permission_count_passed=true`，最终回答包含 `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK`。

当前结构说明：
- browser 层已经成为真实浏览器意图、客户模式授权和产物路径安全的稳定入口。
- `learning_agent.py` 目前仍保留部分旧浏览器方法体作为兼容过渡，但执行路径已优先委托到 `learning_agent/browser/`；阶段 12 瘦身时应删除这些重复业务实现。
- `browser_real_chrome.py` 本阶段未做新改动；真实 Chrome profile 诊断仍属于独立 helper 文件职责。

下一步：
- 进入阶段 8：拆 `tasks/`，重点迁移后台命令、子任务、多 agent 教学版、cron/monitor 等长任务记录类和 helper。

## 2026-05-29 learning_agent 模块化重构阶段 8 tasks 拆分

状态：阶段 8 已完成；已把后台命令、task 子 agent、team 通信、cron 和 monitor 的记录类与纯 helper 迁移到 `learning_agent/tasks/`，旧工具输出和教学版边界保持兼容。

完成内容：
- 已新增 `learning_agent/tasks/background.py`，承载 `BackgroundCommand`、后台输出队列读取 helper 和后台命令状态格式化 helper。
- 已新增 `learning_agent/tasks/task_runs.py`，承载 `TaskRun`、禁止子 agent 继承的任务工具集合、`background` 参数解析和子 agent prompt 构造 helper。
- 已新增 `learning_agent/tasks/team.py`，承载 `TeamMessage`、`TeamPeer` 和根据待确认消息数计算 peer 状态的 helper。
- 已新增 `learning_agent/tasks/cron_monitor.py`，承载 `CronRecord`、`MonitorRecord`、cron/monitor 状态解析、结果数解析、monitor 结果状态解析和记录格式化 helper。
- 已修改 `learning_agent/tasks/__init__.py`，统一 re-export tasks 层公开 API。
- 已修改 `learning_agent/learning_agent.py`，从 tasks 层导入记录类和 helper，并让相关旧方法入口委托新模块。
- 已修改 `learning_agent/test_learning_agent.py`，新增 `test_tasks_package_exports_background_and_task_records`，锁定 tasks 包入口。
- 已新增学习备份目录 `learning_agent/test/modular_refactor_stage8_20260529/`，保存阶段 8 修改后的主文件、测试文件、tasks 模块和实施计划快照。
- 已把正式实施计划文档中的阶段 8 三个步骤全部勾选完成。

验证记录：
- 红灯验证：新增 tasks 导入测试最初失败，失败点为 `ModuleNotFoundError: No module named 'learning_agent.tasks.background'`。
- 语法检查通过：`py_compile learning_agent.py tasks/*.py test_learning_agent.py`。
- 新增导入测试通过：`Ran 1 test in 0.000s OK`。
- task 专项回归通过：`-k task` 输出 `Ran 24 tests in 0.315s OK`。
- background 专项回归通过：`-k background` 输出 `Ran 8 tests in 0.243s OK`。
- cron 专项回归通过：`-k cron` 输出 `Ran 4 tests in 0.019s OK`。
- 完整单元测试通过：`python -m unittest learning_agent.test_learning_agent` 输出 `Ran 357 tests in 28.619s OK (skipped=1)`。
- MCP Doctor 入口通过：`learning_agent.py mcp-doctor` 退出码为 0，`browser_search`、`workspace_tools`、`browser_automation` 均启动成功，模型可见 MCP 工具 30 个。

当前结构说明：
- tasks 层现在是长期任务记录类和纯 helper 的稳定入口。
- 实际副作用编排仍留在 `learning_agent.py`：例如创建子 agent、启动后台进程、权限确认、team 绑定 task、cron/monitor 工具输出编排；这是为了保持教学版行为兼容并避免一次性搬动高风险运行时逻辑。
- 本阶段未升级为产品级队列、真实系统定时器、持久化后台调度或真实通知系统。

下一步：
- 进入阶段 9：拆 `observability/`，重点迁移 debug log、验收事件、权限事件和 run record 的观测层入口。
## 2026-05-29 learning_agent 模块化重构阶段 10 app 拆分

状态：阶段 10 已完成；CLI、doctor、HTTP bridge 和交互式终端入口已经迁入 `learning_agent/app/`，`learning_agent.py` 保留兼容转发。

完成内容：
- 新增 `learning_agent/app/cli.py`：承载 `main()`、`build_model_from_env()`、`format_cli_run_response()`，并通过依赖注入避免直接循环导入 `LearningAgent`。
- 新增 `learning_agent/app/doctor.py`：承载 app 层 `run_mcp_doctor()`，委托 MCP 层真实诊断。
- 新增 `learning_agent/app/http_bridge.py`：承载 `LearningAgentCommandBridgeServer`、`LearningAgentCommandBridgeHandler`、`create_command_bridge_server()` 和 `serve_command_bridge()`。
- 新增 `learning_agent/app/interactive.py`：承载真实用户可见交互式终端循环和验收事件写入。
- 修改 `learning_agent/app/__init__.py`：导出 `main` 和 `run_mcp_doctor`。
- 修改 `learning_agent/learning_agent.py`：原 `main()` 现在转发到 `app.cli.main(agent_cls=LearningAgent, permission_callback=ask_permission_from_terminal_customer_mode)`；旧 `build_model_from_env()`、`format_cli_run_response()`、`create_command_bridge_server()` 保留兼容包装并委托 app 层。
- 修改 `learning_agent/test_learning_agent.py`：新增 `test_app_package_exports_main_entrypoints`。
- 已备份到 `learning_agent/test/modular_refactor_stage10_20260529/`。
- 已把正式实施计划文档中阶段 10 的 Step 10.1-10.4 勾选完成。

验证记录：
- app 入口红灯测试先失败：`ModuleNotFoundError: No module named 'learning_agent.app.cli'`。
- `py_compile learning_agent.py app/*.py test_learning_agent.py` 通过。
- `python -m unittest learning_agent.test_learning_agent -k app_package` 通过。
- `python -m unittest learning_agent.test_learning_agent -k command_bridge` 通过。
- `python learning_agent\learning_agent.py --help` 通过。
- `python learning_agent\learning_agent.py mcp-doctor` 退出码 0，三个 MCP server 均启动成功，模型可见 MCP 工具 30 个。
- `python learning_agent\learning_agent.py run --prompt "ping" --json --max-turns 1` 输出干净 JSON；当前无 `OPENAI_API_KEY` 时返回结构化模型错误，符合预期。
- 完整单元测试通过：`Ran 359 tests in 25.939s OK (skipped=1)`。

当前结构说明：
- app 层已经成为启动入口层，主文件不再需要直接承载完整 CLI/bridge/interactive 编排。
- `learning_agent.py` 中仍保留了旧 app 入口实现的不可达兼容代码，阶段 12 瘦身时需要删除。
- 下一步进入阶段 11：拆分 `test_learning_agent.py`，让测试按模块路径定位。
## 2026-05-30 Stage 13C progress: existing CDP attach for visible Chrome

Status: completed for Stage 13C; code, automated regression, MCP doctor, and visible-terminal acceptance all passed.

What changed:
- Updated `learning_agent/browser_automation_mcp_server.py` so `browser_connect_real_chrome()` checks the requested local CDP port when Chrome is already running.
- Added attach mode to `_connect_real_chrome_after_checks()` through `attach_existing_cdp` and `existing_debug_port`.
- In attach mode, the server does not launch a new Chrome process and keeps `chrome_process=None`, preserving the safety rule that disconnecting should not close the user’s already-open Chrome.
- Updated `learning_agent/browser_real_chrome.py` so `diagnose_real_chrome_environment()` reports `available` when 9222 is occupied by trusted Chrome CDP, preventing `mcp-doctor` and the model from treating an attachable Chrome as a blocker.
- Updated `learning_agent/tests_support/legacy_learning_agent_suite.py` with two RealChrome branch tests: allow attach when existing CDP is live, block when Chrome is running without trusted CDP.
- Updated `learning_agent/AGENT_ARCHITECTURE_INDEX.md` with Stage 13C notes so future agents can find this boundary quickly.

Red/green record:
- Red: `python -m unittest learning_agent.tests_support.legacy_learning_agent_suite.LearningAgentTests.test_browser_connect_real_chrome_attaches_when_running_chrome_has_cdp` failed under old code with the exact running-Chrome refusal.
- Green: the same test passed after the attach-mode implementation.
- Guard: `test_browser_connect_real_chrome_blocks_when_chrome_is_running_without_cdp` passed, proving the profile-lock protection is still present when no trusted CDP exists.
- Diagnostic red/green: `test_real_chrome_diagnostic_reports_available_when_running_chrome_has_cdp` first failed with `needs_user_action != available`, then passed after the diagnosis semantics were updated.

Verification completed so far:
- `python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\tests_support\legacy_learning_agent_suite.py` passed.
- `python -m unittest learning_agent.tests_support.legacy_learning_agent_suite -k real_chrome` passed: 40 tests OK, skipped=1.
- `python -m unittest learning_agent.tests.test_compat_cleanup` passed: 4 tests OK.
- `python -m unittest discover learning_agent` passed: 367 tests OK, skipped=1.
- `python learning_agent\learning_agent.py mcp-doctor` now reports real Chrome profile status as `available` on this machine because 9222 is trusted Chrome CDP.

Visible terminal acceptance:
- Command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\real_chrome_natural_weather_travel.json`.
- Result: `learning_agent\acceptance_controller\runs\real_chrome_natural_weather_travel-20260530_144214\result.json`.
- Outcome: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, `marker_passed=true`, `permission_count_passed=true`.
- Evidence: final answer included `REAL_CHROME_NATURAL_WEATHER_TRAVEL_OK` and `real_chrome_connected=true`; debug checks confirmed `browser_connect_real_chrome 成功`, `browser_open 成功`, `browser_click 成功`, `browser_type 成功`, `browser_press_key 成功`, `browser_wait 成功`, `browser_screenshot 成功`, and `browser_snapshot 成功`.

## 2026-05-30 Stage 14 hard cleanup progress

Status: completed for code cleanup, documentation cleanup, automated tests, and visible-terminal acceptance.

What changed:
- Split the old large legacy test suite into real modules under `learning_agent/tests/`.
- Deleted the old test aggregator files and old acceptance forwarding entry.
- Removed same-block unreachable old implementations from `learning_agent/core/agent.py`.
- Updated `start_oauth_agent.ps1`, `start_codex_agent.ps1`, `README.md`, and `AGENT_ARCHITECTURE_INDEX.md` so user-visible docs and scripts point to the new architecture.
- Deleted source-tree historical artifact directories: `learning_agent/test/`, `learning_agent/debug_logs/`, `learning_agent/browser_artifacts/`, and `learning_agent/tests_support/`.
- Archived the fresh real-browser evidence from the acceptance run into `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/`.

Verification:
- `python -m compileall learning_agent` passed through bundled Codex Python.
- AST unreachable scan returned `NO_UNREACHABLE_SAME_BLOCK_CODE`.
- `python -m unittest learning_agent.tests.test_compat_cleanup` passed: 5 tests OK.
- `python -m unittest discover learning_agent` passed: 368 tests OK, skipped=1.
- Visible terminal acceptance passed at `learning_agent/acceptance_controller/runs/real_chrome_natural_weather_travel-20260530_210431/result.json`: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.

## 2026-05-31 ClaudeCode gap baseline documentation

Status: completed for documentation only; no runtime code changed.

What changed:
- Added `agent_memory/claude_code_gap_baseline.md` as the agent-readable baseline for comparing learning_agent with `D:\ClaudeCode-main\ClaudeCode-main`.
- Added `learning_agent/claude_code_gap_baseline_backup_20260531.md` as a stable markdown backup for later alignment.
- The baseline records the current estimate: learning_agent is about 55%-65% aligned with reproducible core agent ideas, about 50%-60% aligned with the local long-running self-development goal, and about 25%-35% aligned with ClaudeCode product-level completeness.

Important next direction:
- The recommended next engineering phase is `Stage 15: Event Stream Runtime and Tool Executor v2`.
- Main focus should be streaming agent loop, richer tool protocol, concurrent read-only tool execution, transcript/session persistence, permission hooks, and durable task/subagent runtime.

Verification:
- Documentation-only change; no automated tests or visible terminal acceptance were required.

## 2026-05-31 Stage 15 event runtime written plan

Status: completed for planning only; no runtime code changed.

What changed:
- Added `agent_memory/stage15_event_runtime_plan.md` as the detailed 8-stage plan for adding event-stream runtime, richer tool protocol, Tool Executor v2, permission hooks, safe concurrency, and session resume/compact.
- Added `learning_agent/stage15_event_runtime_plan_backup_20260531.md` as a stable backup copy.

Plan summary:
- Stage 15A: event types and transcript foundation.
- Stage 15B: streaming model interface.
- Stage 15C: `LearningAgent.run_events()` with old `run()` compatibility.
- Stage 15D: Tool Protocol v3 metadata.
- Stage 15E: Tool Executor v2 and permission hooks.
- Stage 15F: safe concurrent read-only tool batching.
- Stage 15G: session save/resume and minimal compact.
- Stage 15H: integration validation, docs, and real visible terminal acceptance.

Verification:
- Documentation-only change; no automated tests or visible terminal acceptance were required.

## 2026-05-31 Stage 15A event runtime foundation

Status: completed for Stage 15A foundation in isolated worktree `stage15a-event-runtime`.

Baseline setup:
- Created initial git baseline commit on `main`: `3c657e5 chore: establish learning agent baseline`.
- Created isolated worktree: `.worktrees/stage15a-event-runtime`.
- Installed missing local Python test dependency with `python -m pip install playwright`.
- Installed Playwright Chromium with `python -m playwright install chromium`.
- Restored baseline test fixtures required by existing tests:
  - `.gitignore` now includes `learning_agent/browser_profiles.json`.
  - `.gitignore` now includes `learning_agent/browser_artifacts/real_chrome_audit.jsonl`.
  - Added `docs/superpowers/specs/claudecode_parity_checklist.md`.

TDD record:
- Red: `python -m unittest learning_agent.tests.test_runtime_events` failed with `ModuleNotFoundError: No module named 'learning_agent.core.events'`.
- Green: after adding `learning_agent/core/events.py` and `learning_agent/observability/transcript.py`, the same command passed with 2 tests OK.

Implemented:
- Added `learning_agent/core/events.py` with immutable `AgentEvent`, UTC timestamp helper, event factory, and JSONL serializer.
- Added `learning_agent/observability/transcript.py` with `TranscriptWriter` that appends events to `<base_dir>/<session_id>/events.jsonl`.
- Added `learning_agent/tests/test_runtime_events.py` covering stable JSON event serialization and session-directory JSONL transcript writes.
- Backed up new Stage 15A code into `learning_agent/test/stage15a_event_runtime_20260531/`.

Verification:
- Focused baseline repair tests passed: `python -m unittest learning_agent.tests.test_browser_harness.BrowserHarnessTests.test_gitignore_ignores_real_chrome_local_files learning_agent.tests.test_core_run_loop.CoreRunLoopTests.test_claudecode_parity_checklist_records_phase_7_status`.
- Full baseline unittest passed after dependency and fixture repair: `python -m unittest discover learning_agent` -> 368 tests OK, skipped=1.
- Focused Stage 15A test passed: `python -m unittest learning_agent.tests.test_runtime_events` -> 2 tests OK.
- Final Stage 15A compile verification passed: `python -m compileall learning_agent`.
- Final Stage 15A full unittest passed: `python -m unittest discover learning_agent` -> 370 tests OK, skipped=1.

Acceptance note:
- Real visible terminal acceptance was not run for Stage 15A because this stage only adds standalone event/transcript primitives and does not integrate runtime behavior into `LearningAgent.run()`.
- Future stages that change the interactive run loop, tool execution behavior, or user-visible agent behavior must run `start_oauth_agent.bat` visible-terminal acceptance before claiming development complete.

## 2026-05-31 Stage 15B-15G event runtime implementation progress

Status: code implementation and automated regression completed through Stage 15G in worktree `stage15a-event-runtime`.

Completed:
- Stage 15B streaming model compatibility in `models/base.py`.
- Stage 15C `run_events()` event stream and transcript integration in `core/agent.py`.
- Stage 15D Tool Protocol v3 metadata in `tools/types.py` and `tools/catalog.py`.
- Stage 15E Tool Executor v2, permission decision object, hook manager, and executor observations.
- Stage 15F safe concurrent read-only tool orchestration and integration into `run()` / `run_events()`.
- Stage 15G transcript reading, session summary store, and minimal compact helper.

Focused verification passed:
- `python -m unittest learning_agent.tests.test_models_streaming`
- `python -m unittest learning_agent.tests.test_runtime_events`
- `python -m unittest learning_agent.tests.test_tool_protocol`
- `python -m unittest learning_agent.tests.test_tool_executor_v2`
- `python -m unittest learning_agent.tests.test_tool_orchestrator`
- `python -m unittest learning_agent.tests.test_sessions`

Full regression evidence during implementation:
- Stage 15D full discovery: 377 tests OK, skipped=1.
- Stage 15E full discovery: 381 tests OK, skipped=1.
- Stage 15F full discovery: 384 tests OK, skipped=1.
- Stage 15G full discovery: 387 tests OK, skipped=1.

Remaining Stage 15H gate:
- Run fresh final `compileall`, full unittest discovery, `--help`, and `mcp-doctor`.
- Perform or request real visible terminal interaction through `learning_agent/start_oauth_agent.bat`.

## 2026-05-31 独立验收 verifier 与终端焦点门禁

Status: completed for code, docs, backup, automated regression, independent verifier replay, and real visible terminal smoke acceptance.

What changed:
- Added `learning_agent/acceptance/__init__.py` and `learning_agent/acceptance/verifier.py`.
- Added `learning_agent/tests/test_acceptance_verifier.py`.
- Updated `learning_agent/acceptance_controller/README.md` with offline replay verification usage.
- Hardened `learning_agent/acceptance_controller/controller.ps1` so it verifies the foreground window belongs to the target terminal before pasting prompts.
- Updated `learning_agent/tests/test_observability_acceptance.py` to guard the new foreground-window validation requirements.
- Backed up changed files under `learning_agent/test/acceptance_verifier_20260531/`.

Verification:
- Red test first: verifier import test failed before `learning_agent.acceptance` existed.
- Focused verifier tests: `python -m unittest learning_agent.tests.test_acceptance_verifier` passed with 3 tests OK.
- Controller protocol guard: `python -m unittest learning_agent.tests.test_observability_acceptance.ObservabilityAcceptanceTests.test_acceptance_controller_script_uses_generic_event_protocol` passed.
- PowerShell parse check for `controller.ps1` passed.
- Full regression: `python -m unittest discover learning_agent` passed with 390 tests OK, skipped=1.
- Compile check: `python -m compileall learning_agent` passed.
- MCP doctor: `python learning_agent\learning_agent.py mcp-doctor` exited 0 and reported 30 visible MCP tools.

Real visible terminal acceptance:
- Successful run: `learning_agent/acceptance_controller/runs/smoke-20260531_143929/result.json`.
- Result: `completed=true`, `prompt_received=true`, `final_printed=true`, `prompt_send_attempts=1`, final answer `ACCEPTANCE_HARNESS_OK`.
- Independent replay: `python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\smoke-20260531_143929 learning_agent\acceptance_controller\scenarios\smoke.json` returned `completed=true` and `assertion.passed=true`.

## 2026-05-31 long-task harness source review

Status: analysis only; no runtime code changed.

Findings:
- `learning_agent` currently has acceptance/controller harness pieces, `run_events()` transcript/session primitives, and in-process task/background/cron/monitor records.
- It does not yet have an independent durable long-task harness module with endpoint recovery, persistent task queue, staged acceptance gates, automatic continuation after failure, durable task state, or task-state visualization.
- ClaudeCode source review confirms a mature harness is spread across `QueryEngine.ts`, `utils/sessionStorage.ts`, `tasks/*`, `utils/messageQueueManager.ts`, `services/compact/*`, `services/tools/*`, and `components/tasks/*`.
- Recommended direction: add `learning_agent/harness/` as a dedicated package with durable run/task/stage schemas, append-only event log, persistent queue leases, checkpoint/resume, retry policy, verifier gates, and a status API/UI bridge.

## 2026-05-31 harness 对齐 ClaudeCode 方案确认

Status: planning only; no runtime code changed.

Confirmed from source:
- `learning_agent/harness/` already provides durable run/stage/attempt models, JSON/JSONL store, lease queue, runner, verifier, CLI, and `AgentStageExecutor`.
- `learning_agent/core/agent.py` already has `run_events()`, transcript writing, session summary, streaming model event consumption, and orchestrated tool execution.
- Runtime entrypoint tracing shows `learning_agent/learning_agent.py` delegates to `learning_agent/app/cli.py`, interactive mode delegates to `learning_agent/app/interactive.py`, and that path calls `agent.run(...)` without importing or invoking `learning_agent.harness`; therefore the real terminal main loop is not yet harness-driven.
- ClaudeCode's comparable long-task capability is distributed across `QueryEngine.ts`, `cli/print.ts`, `utils/messageQueueManager.ts`, `tasks/LocalAgentTask`, `tasks/RemoteAgentTask`, `tasks/LocalShellTask`, `utils/task/framework.ts`, `utils/task/TaskOutput.ts`, and `utils/sessionStorage.ts`.

Output:
- Created `agent_memory/harness_claudecode_alignment_plan_20260531.md`.
- The plan defines 12 stages: source baseline tests, runtime command queue, session runtime integration, interrupted-turn resume, durable task registry, task notification feedback, poller/watchdog, task output management, file locks/atomic writes, CLI/API status, verifier upgrades, and real visible terminal acceptance.

Next recommended action:
- Start with Stage 1 from `agent_memory/harness_claudecode_alignment_plan_20260531.md`: write failing alignment tests that prove which ClaudeCode-equivalent behaviors are still missing before implementation.

## 2026-05-31 source-only evidence correction

Status: planning evidence corrected; no runtime code changed.

Correction:
- README files must not be treated as key evidence for harness capability conclusions.
- Updated `agent_memory/harness_claudecode_alignment_plan_20260531.md` and this progress entry so the key conclusion uses source entrypoint tracing and symbol-reference scans instead of README statements.

## 2026-05-31 ClaudeCode-aligned harness runtime implementation

Status: implementation in progress; final real visible terminal acceptance still pending.

Implemented:
- Added `learning_agent/tests/test_harness_runtime_alignment.py` as the source-behavior alignment suite.
- Added `learning_agent/runtime/` with durable command queue, atomic/locked file helpers, session runtime, interrupted run resumer, durable task registry, task output store, and task poller.
- Updated `LearningAgent.run()` to keep the old text-returning API while internally using `run_events()` and mirroring the real run into durable harness state.
- Updated task and background command paths so task records/output persist under `memory/tasks` and can generate task notifications.
- Upgraded `HarnessStore`/`HarnessQueue` to use atomic writes, queue locks, and corrupt JSON quarantine.
- Upgraded `StageVerifier`/`HarnessStage` for marker, artifact, artifact content, JSON required fields, command exit codes, event sequence, and acceptance result checks.
- Upgraded harness CLI with `queue`, `tasks`, `events`, `resume`, and `poll`.

Verification so far:
- Red test confirmed first: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` failed because `learning_agent.runtime` did not exist.
- Green focused suite: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` -> 9 tests OK.
- Regression checks: `python -m unittest learning_agent.tests.test_core_run_loop` -> 40 tests OK; `python -m unittest learning_agent.tests.test_runtime_events` -> 4 tests OK; `python -m unittest learning_agent.tests.test_harness_long_task` -> 8 tests OK.
- Full regression: `python -m unittest discover learning_agent` -> 407 tests OK, skipped=1.
- Compile check: `python -m compileall learning_agent` -> exit 0.
- MCP doctor: `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools; Chrome real-profile status needs user action because Chrome was already running.
- Backup: copied changed runtime/core/harness/test/planning files to `learning_agent/test/harness_claudecode_alignment_20260531/`.

Remaining gate:
- Completed: real visible terminal acceptance through `learning_agent/start_oauth_agent.bat` passed for `learning_agent/acceptance_controller/runs/harness_runtime_alignment_status-20260531_165630/result.json`.
- Completed: independent replay passed with `python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\harness_runtime_alignment_status-20260531_165630 learning_agent\acceptance_controller\scenarios\harness_runtime_alignment_status.json`.
- Completed: latest durable run evidence in `learning_agent/memory/harness/runs/runtime_275e3c33ad6ec332.json` shows top-level `status=completed`, `stages[0].status=completed`, and `stages[0].acceptance.passed=true`.
- Completed: runtime command evidence in `learning_agent/memory/runtime/events.jsonl` shows the real prompt command was queued and completed.

Bug found and fixed during real acceptance:
- Real terminal acceptance initially exposed a false-complete state where the top-level run was completed but the copied stage stayed pending.
- Added regression checks in `learning_agent/tests/test_harness_runtime_alignment.py`.
- Fixed `learning_agent/runtime/session_runtime.py` to update `run.stages[0]` after `HarnessRun.create(...)`, because `HarnessRun.create()` deep-copies stages.
- Re-ran full verification after the fix: `python -m unittest discover learning_agent` -> 407 tests OK, skipped=1; `python -m compileall learning_agent` -> exit 0; `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools.

## 2026-05-31 Harness ClaudeCode alignment status correction

Status: previous completion claim downgraded to incomplete after source-only comparison.

Correction:
- The existing implementation created durable harness files, runtime queue files, task registry files, verifier upgrades, CLI status commands, and a real visible terminal smoke acceptance.
- That is not enough to claim ClaudeCode core harness alignment.
- The hard gate from `agent_memory/harness_claudecode_alignment_plan_20260531.md` requires the real main loop to be harness-driven and to consume queued prompt/task-notification/resume commands as model-visible context.
- Current source review shows `LearningAgent.run()` records a prompt into `RuntimeCommandQueue`, but then directly calls `agent.run_events(user_input, ...)` in `learning_agent/runtime/session_runtime.py`; it does not drain `RuntimeCommandQueue` into the model loop the way ClaudeCode drains queued commands in `query.ts`.
- Therefore the current alignment estimate must be treated as partial foundation only, not task completion.

Updated remaining hard gates:
- Add failing tests proving task notifications are automatically injected into the next real model turn without manual `task_output`.
- Add failing tests proving `resume_interrupted` commands are consumed by the real run loop, not merely enqueued.
- Refactor the real run path so queued runtime commands become model-visible context and are marked consumed only after they are attached to the turn.
- Add real visible terminal scenarios for task notification feedback and interrupted resume before any future completion claim.

## 2026-05-31 Harness alignment execution plan rewrite

Status: planning completed for corrected execution scope; implementation not started in this entry.

What changed:
- Added `agent_memory/harness_claudecode_alignment_execution_plan_20260531.md`.
- The new plan turns the previous loose "next step" into ten phases with hard gates.
- The plan centers on the missing core behavior: real `LearningAgent.run()` must drain durable runtime commands into model-visible context.
- The plan explicitly blocks completion claims until task notification feedback, interrupted resume consumption, durable task truth source, CLI/status visibility, automated regression, and real visible terminal acceptance all pass.

Critical correction:
- The old implementation remains a partial foundation.
- The next implementation pass must start with red tests for queue-drain-to-model behavior before modifying production code.

## 2026-05-31 Harness ClaudeCode alignment completion pass

Status: implementation and verification completed.

Implemented after corrected plan:
- Added red/green tests proving real queue drain, task notification feedback, interrupted resume consumption, and background command auto-notification.
- Fixed background shell completion so it updates durable task registry and enqueues notifications without `read_background_command`.
- Extended harness CLI/status output so run/stage/task/event/output/verifier evidence is visible.
- Fixed dynamic skill capability loading so reading `long_running_work/SKILL.md` exposes the real execution and long-running-work tools in the next model turn.
- Added visible terminal scenarios for task notification seed, notification feedback, resume, background shell watchdog, and background shell notification.

Verification:
- Red test confirmed before fix: `test_reading_long_running_skill_loads_background_command_tools` failed because `start_background_command` was not visible after reading `long_running_work/SKILL.md`.
- Focused green tests passed: `learning_agent.tests.test_mcp_registry`, `learning_agent.tests.test_tools_policy`, `learning_agent.tests.test_harness_runtime_alignment`, and the background auto-notify core-run-loop test.
- Full regression passed: `python -m unittest discover learning_agent` -> 414 tests OK, skipped=1.
- Compile check passed: `python -m compileall learning_agent` -> exit 0.
- MCP doctor passed: `python learning_agent\learning_agent.py mcp-doctor` -> exit 0 and 30 model-visible MCP tools; Chrome profile diagnostic still reports `needs_user_action` only because Chrome is currently running.

Real visible terminal acceptance:
- `harness_task_notification_seed-20260531_175937/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_task_notification-20260531_180044/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_runtime_resume-20260531_180202/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_background_shell_watchdog-20260531_180225/result.json` -> `completed=true`, `assertion.passed=true`.
- `harness_background_shell_notification-20260531_180359/result.json` -> `completed=true`, `assertion.passed=true`.
- Independent replay verifier also passed for all five run directories with `python -m learning_agent.acceptance.verifier <run_dir> <scenario.json>`.
- Final runtime queue check returned `NO_QUEUED_COMMANDS`.

Conclusion:
- The previous false-completion risk is resolved for the planned ClaudeCode core harness subset: real terminal prompt creates a durable run, queued notifications/resume commands enter the real model context, background tasks persist and notify, status/CLI surfaces evidence, and the feature passed real visible terminal acceptance.

## 2026-05-31 run() unreachable legacy cleanup

Status: source cleanup and verification completed.

What changed:
- Removed the unreachable legacy `LearningAgent.run()` loop after `return run_agent_with_harness_session(...)`.
- Kept `run_events()` unchanged as the real event-stream implementation.
- Added learning backup at `learning_agent/test/run_unreachable_cleanup_20260531/modified_snippets.md`.

Why:
- The leftover code could not execute, but it made the project look like it still had two competing main loops.
- Cleaning it makes the source match the intended architecture: `run()` is a thin compatibility wrapper and `run_events()` is the real event runtime.

Verification:
- `python -m py_compile learning_agent\core\agent.py` passed.
- `python -m unittest learning_agent.tests.test_harness_runtime_alignment learning_agent.tests.test_core_run_loop` passed: 55 tests OK.
- `python -m unittest discover learning_agent` passed: 414 tests OK, skipped=1.
- Real visible terminal smoke acceptance passed via `learning_agent/acceptance_controller/controller.ps1` with run directory `learning_agent/acceptance_controller/runs/smoke-20260531_182223`.
- Independent verifier passed for `smoke-20260531_182223`: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.

## 2026-05-31 Compact/Resume and UI/SDK status ecosystem plan

Status: planning completed; no production code changed for this plan.

Created:
- `agent_memory/compact_resume_status_ecosystem_alignment_plan_20260531.md`.
- `learning_agent/test/compact_resume_status_ecosystem_plan_20260531/plan.md`.

Scope:
- Align compact/resume complexity with ClaudeCode using append-only transcript, compact boundary, turn ledger, resume loader, consistency checks, and real main-loop integration.
- Align UI/SDK status ecosystem with ClaudeCode using terminal status renderer, status event protocol, status snapshot, CLI/API/SDK access, and model-callable status tools.
- Explicitly excludes remote tasks and streaming tool execution from this plan so the task stays focused.

## 2026-05-31 Compact/Resume and UI/SDK status ecosystem execution

Status: implementation completed and fully verified.

Implemented:
- Added transcript v2, turn ledger, compact boundary, resume loader, status event store, status snapshot, terminal renderer, SDK status helpers, HTTP `/status` and `/events`, harness CLI `snapshot`, interactive `/status`, and model-callable status tools.
- Integrated transcript v2, turn ledger, compact boundary, and status events into the real `LearningAgent.run_events()` path so they are no longer standalone side systems.
- Added tool schema/catalog/executor routes for `status_snapshot`, `task_status`, `session_list`, `session_resume`, `compact_status`, and `event_tail`.
- Added acceptance scenario `learning_agent/acceptance_controller/scenarios/compact_resume_status_ecosystem.json`.

Verification so far:
- Red HTTP test failed first with `/status` returning 404.
- Focused HTTP status/event test now passes.
- Red CLI module-entry test failed first because `python -m learning_agent.harness.cli snapshot` printed no status output.
- Full compact/resume/status ecosystem test file passes: 6 tests OK.
- Related regression passed: 258 tests OK.
- Full regression passed: 420 tests OK, skipped=1.
- Compile checks passed for changed modules and `python -m compileall learning_agent`.
- Real visible terminal acceptance passed for `compact_resume_status_ecosystem-20260531_185954`, and independent verifier passed.
- Real latest session evidence after visible terminal run: `memory/sessions/session_20260531_190000_e71f387a` contains `events.jsonl`, `summary.json`, `transcript_v2.jsonl` with 35 lines, and `turns.json`; `memory/status/events.jsonl` has 34 status events.
- After the CLI entrypoint fix, real visible terminal acceptance was rerun and passed for `compact_resume_status_ecosystem-20260531_190357`; independent verifier passed.
- Final latest session evidence after rerun: `memory/sessions/session_20260531_190403_57d4274a` contains `events.jsonl`, `summary.json`, `transcript_v2.jsonl` with 35 lines, and `turns.json`; `memory/status/events.jsonl` has 68 status events.

Backup:
- Refreshed under `learning_agent/test/compact_resume_status_ecosystem_20260531/`.

## 2026-05-31 Deep ClaudeCode compact/resume and status ecosystem alignment plan

Status: planning completed; waiting for user confirmation before implementation.

Why this plan exists:
- The previous compact/resume and status ecosystem task produced a working foundation, but it did not fully match ClaudeCode's deeper compact/resume complexity.
- Source comparison showed ClaudeCode has layered snip/microcompact/context-collapse/autocompact/reactive-compact behavior, richer resume cleanup, tombstones, tool summaries, session metadata restoration, and tighter SDK/UI event integration.

Created:
- `agent_memory/compact_resume_status_claudecode_deep_alignment_plan_20260531.md`
- `learning_agent/test/compact_resume_status_claudecode_deep_alignment_plan_20260531/plan.md`

Scope:
- Plan only. No production runtime code changed in this step.
- Implementation must wait for explicit user confirmation.
- Final implementation will require automated tests, compile checks, real visible `start_oauth_agent.bat` terminal acceptance, and independent verifier replay before any completion claim.

## 2026-05-31 Deep ClaudeCode compact/resume and status ecosystem alignment execution

Status: implementation completed and verified with automated tests plus real visible terminal acceptance.

Implemented:
- Status event protocol v2 now has stable `schema_version`, `session_id`, `run_id`, and `turn_id` fields, plus lifecycle event names for model, tools, compact, resume, verifier, and status.
- Multi-layer compact now records `tool_output_snip`, `microcompact`, `context_collapse`, `autocompact`, artifact paths, archived ranges, character estimates, and collapse commit ids.
- Reactive compact now detects prompt-too-long/media-too-large style failures and retries once with a tighter compacted context.
- ResumeLoader v2 now reports bad transcript lines, missing tool results, orphan tool results, interrupted turns, tombstones, warnings, and `resume_safe`/`resume_needs_review`.
- `LearningAgent.run_events()` now emits v2 status events for accepted turns, model responses, tool use/result, proactive compact, and reactive compact retry.
- HTTP bridge now exposes `/runs`, `/sessions`, `/resume?session_id=...`, `/health`, and type-filtered `/events`, alongside existing `/status`.
- SDK status now exposes `get_runs`, `get_sessions`, `get_health`, and `load_resume_report`, and event watch/list support event type filtering.
- Terminal UI now supports `/status`, `/events`, `/sessions`, `/resume <session_id>`, and `/compact`.
- Model-callable status tools now include `resume_report`, `run_status`, and `health_status` in addition to the previous status tools.
- Compatibility tests prove legacy status events and legacy compact boundaries remain readable by the new snapshot/resume path.

Automated verification:
- `python -m unittest learning_agent.tests.test_compact_deep_alignment learning_agent.tests.test_resume_deep_alignment learning_agent.tests.test_status_ecosystem_deep_alignment learning_agent.tests.test_compact_resume_status_ecosystem learning_agent.tests.test_runtime_events` passed: 16 tests OK.
- `python -m compileall -q learning_agent` passed.
- `python -m unittest discover learning_agent.tests` passed: 426 tests OK, skipped=1.

Backup:
- Source backup for this execution is being refreshed under `learning_agent/test/compact_resume_status_claudecode_deep_alignment_20260531/`.

Real visible terminal verification:
- Scenario file: `learning_agent/acceptance_controller/scenarios/compact_resume_status_deep_alignment.json`.
- Controller run directory: `learning_agent/acceptance_controller/runs/compact_resume_status_deep_alignment-20260531_200122`.
- Controller result: `ACCEPTANCE_CONTROLLER_COMPLETED=True`.
- Independent verifier result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Verifier confirmed final answer contained `COMPACT_RESUME_STATUS_DEEP_READY`, `tool_output_snip`, `microcompact`, `context_collapse`, `reactive_compact_retry`, `ResumeRepairReport`, `resume_needs_review`, `STATUS_SCHEMA_VERSION`, `get_health`, `load_resume_report`, `resume_report`, `run_status`, `health_status`, `/events`, `/sessions`, and `/compact`.
# 2026-05-31 真实浏览器能力对齐 ClaudeCode

## 当前任务

用户要求继续增强 `learning_agent` 的真实浏览器能力，重点补齐页面失败恢复、视觉定位、复杂网站流程、登录态安全、插件兼容、异常重试和任务回放，并且要求再次阅读 `D:\ClaudeCode-main\ClaudeCode-main` 源码作为对照证据。

## 已完成

1. 已确认本轮不是只做报告，而是要补代码能力。
2. 已初步读取 `learning_agent` 的浏览器 MCP、真实 Chrome、安全策略、harness、权限和测试文件。
3. 已初步读取 ClaudeCode 的 Chrome 扩展入口、Claude in Chrome skill、Chrome prompt hook、computer-use MCP、权限 UI、流式工具执行、消息队列、会话恢复和插件系统源码。
4. 已创建书面计划：`agent_memory/browser_claudecode_alignment_plan_20260531.md`。

## 下一步

1. 已写新增浏览器运行层测试：`learning_agent/tests/test_browser_runtime_alignment.py`。
2. 已实现动作轨迹、回放、重试、恢复、视觉定位、复杂流程、安全边界和插件兼容状态。
3. 已备份修改到 `learning_agent/test/browser_runtime_alignment_20260531/`。
4. 已通过 `python -m unittest discover learning_agent.tests`，结果为 433 个测试通过，1 个手动真实 Chrome 测试跳过。
5. 第一次真实终端验收发现 `browser_flow_run` 的 array schema 缺少 items，导致 OpenAI response_format invalid_json_schema；已补 schema 并加测试。
6. 第二次真实终端验收通过：`learning_agent/acceptance_controller/runs/browser_runtime_alignment-20260531_204032/result.json` 中 `completed=true`，`assertion.passed=true`。

## 本次新增能力文件

1. `learning_agent/browser_automation_mcp_server.py`
2. `learning_agent/tests/test_browser_runtime_alignment.py`
3. `learning_agent/skills/browser_automation/SKILL.md`
4. `learning_agent/skills/real_chrome/SKILL.md`
5. `agent_memory/browser_claudecode_alignment_report_20260531.md`
6. `learning_agent/acceptance_controller/scenarios/browser_runtime_alignment.json`

# 2026-05-31 真实可见浏览器验收补齐

## 当前任务

用户要求所有真实浏览器新增能力必须经过肉眼可见的真实浏览器测试验收通过，才能算完成。

## 当前判断

上一轮已补核心浏览器工具能力，并通过真实终端状态验收；但独立 Chromium 默认还是 headless，缺少明确的“可见浏览器启动 + 可见浏览器完整链路验收”。

## 本轮计划

1. 新增 `browser_launch_visible` 工具。
2. 让 `ensure_browser()` 支持 `headless=false`。
3. 让状态工具输出 `visible_browser` 和 `headless` 状态。
4. 新增真实可见浏览器验收场景。
5. 跑自动化测试、完整测试和真实可见终端验收。

## 本轮完成

1. 已新增 `browser_launch_visible`，需要 `confirm_visible_browser=true` 才会启动可见独立 Chromium。
2. 已让 `browser_open`、`browser_snapshot`、`browser_visual_locate`、`browser_flow_run`、`browser_recover_page`、`browser_replay`、`browser_plugin_status` 在可见浏览器 workflow 中连贯可用。
3. 已修复 Windows 状态文件 `os.replace` 短暂拒绝访问问题：`atomic_write_text()` 现在会短退避重试并清理失败临时文件。
4. 已修复 `browser_visual_locate`：现在能定位不可点击的标题/正文文本块，并支持 `selector="h1"` 这类简写。
5. 已修复 `browser_flow_run`：阶段里的空 `browser_wait` 会自动补 `milliseconds=250`，避免模型小参数遗漏导致流程失败。
6. 已更新可见浏览器验收场景：`learning_agent/acceptance_controller/scenarios/browser_visible_runtime_acceptance.json`。

## 验证结果

1. `python -m unittest learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_intent learning_agent.tests.test_browser_harness learning_agent.tests.test_runtime_files` 通过：55 个测试 OK，1 个跳过。
2. `python -m py_compile learning_agent\browser_automation_mcp_server.py learning_agent\runtime\files.py learning_agent\browser\intent.py learning_agent\core\agent.py learning_agent\tests\test_runtime_files.py learning_agent\tests\test_browser_runtime_alignment.py` 通过。
3. `python -m unittest discover learning_agent.tests` 通过：439 个测试 OK，1 个跳过。
4. 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260531_211805/result.json` 中 `completed=true`、`assertion.passed=true`。
5. 真实验收日志确认：`browser_launch_visible 成功`、`visible_browser=true`、`headless=false`、`browser_open`、`browser_snapshot`、`browser_visual_locate 成功`、`browser_flow_run 完成`、`browser_recover_page 成功`、`browser_replay 计划`、`browser_plugin_status compatible=true`。
6. 独立验收复核通过：`python -m learning_agent.acceptance.verifier ...browser_visible_runtime_acceptance-20260531_211805 ...browser_visible_runtime_acceptance.json` 输出 `completed=true`、`assertion.passed=true`。

# 2026-05-31 自然实时查询可见浏览器路由修复

## 当前任务

用户指出本地桌面没有看到真实浏览器，要求重新测试精准 prompt：`帮我查询3天后武汉的天气，并帮我做一下旅游攻略。`

## 已确认

1. 精准 prompt 场景已经跑过一次：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_212955/result.json`。
2. 该 run 的最终回答已打印，但工具调用只有 `browser_search.web_search` 和 `browser_search.fetch_url`。
3. 没有看到 `browser_launch_visible`、`browser_open`、`browser_snapshot`，所以真实可见浏览器验收不成立。
4. 代码证据显示当前 `detect_real_browser_information_task()` 要求先命中“真实浏览器”等关键词，普通天气/攻略查询不会进入浏览器 harness。

## 本轮计划文件

已创建：`agent_memory/visible_browser_natural_query_route_plan_20260531.md`。

## 下一步

1. 写红灯测试锁定普通武汉天气/攻略 prompt 必须进入可见浏览器路由。
2. 实现自然实时查询意图、可见浏览器 harness 和首轮 `browser_launch_visible` 工具暴露。
3. 跑自动化测试和真实可见终端验收。

## 本轮完成

1. 已新增普通自然实时查询识别函数：`detect_visible_browser_information_task()`。
2. 已新增 `Visible Browser Task Harness`，精准 prompt 会要求可见独立 Chromium，而不是后台 `web_search/fetch_url`。
3. `LearningAgent.run_events()` 已在首轮工具池构造前预加载可见浏览器公开查询所需工具。
4. 已新增普通可见浏览器公开查询自动授权白名单，范围只包含独立 Chromium 的公开网页动作；`browser_evaluate`、`file://`、缺确认参数启动仍不自动放行。
5. 自动化测试通过：`python -m unittest discover learning_agent.tests`，444 tests OK，skipped=1。
6. 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_215353/result.json`。
7. 独立 verifier 通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
8. 最终回答包含 `browser_launch_visible`、`visible_browser=true`、`headless=false`，并给出武汉天气和旅游攻略。
## 2026-05-31 危险调试权限 + browser_connect_real_chrome 验收执行记录

状态：已完成。

已完成：
- 已确认权限拦截点位于 `learning_agent/browser/permissions.py`、`learning_agent/core/agent.py` 和 `learning_agent/start_oauth_agent.ps1`。
- 已新增 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS` 开关，危险模式下终端权限和 MCP 工具权限会自动写入 `permission_auto_approved` 并放行。
- 已让 `start_oauth_agent.ps1` 普通启动默认设置危险调试权限，并在终端打印清楚提示。
- 已新增单元测试覆盖任意 MCP 工具危险自动授权、终端权限不调用 input、启动脚本默认设置危险开关。
- 已新增真实可见终端验收场景 `real_chrome_dangerous_skip_connect_public_page.json`，要求调用 `browser_connect_real_chrome(confirm_real_profile=true)` 并打开 `https://example.com`。
- 首次真实可见终端验收已证明权限层通过，但 `browser_connect_real_chrome` 被工具自身的“日常 Chrome 正在运行且无 CDP”安全检查阻断。
- 已补充危险调试模式下的隔离 debug profile 兜底：不关闭用户 Chrome，不读取登录态，而是用真实 Google Chrome + `browser_artifacts/real_chrome_debug_profile` 完成可见浏览器连接测试。
- 已新增单元测试 `test_browser_connect_real_chrome_uses_debug_profile_fallback_in_dangerous_mode` 锁定上述兜底。

最终验收：
- 已更新学习备份到 `learning_agent/test/dangerous_skip_permissions_real_chrome_20260531/`。
- 已重新通过 `start_oauth_agent.bat` 的真实可见终端执行 controller 场景，确认 `browser_connect_real_chrome` 真实可见验收通过。
- 验收 run：`learning_agent/acceptance_controller/runs/real_chrome_dangerous_skip_connect_public_page-20260531_223149`。
- `result.json` 中 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`、`permission_auto_approved=true`。
- 最终截图 `03_final.png` 可见真实 Google Chrome 打开 `https://example.com`，并且终端输出包含 `REAL_CHROME_DANGEROUS_SKIP_CONNECT_OK`、`real_chrome_connected=true`、`real_chrome_profile_scope=debug_profile_fallback`。

当前验证：
- `python -m unittest learning_agent.tests.test_browser_harness learning_agent.tests.test_browser_intent learning_agent.tests.test_mcp_registry`：160 tests OK，skipped=1。
- `python -m unittest discover learning_agent.tests`：448 tests OK，skipped=1。
- `python -m compileall learning_agent`：通过。

## 2026-06-01 雷神 H5 登录真实 Chrome 拟人验收完成记录

任务目标：
- 用户要求由 `learning_agent` 通过 `browser_connect_real_chrome` 控制真实 Google Chrome，打开指定 H5 页面，输入已提供账号和密码，提交登录，并把登录后页面可见内容反馈给用户。
- 因为该任务涉及真实登录态和敏感输入，本轮实现和验收必须使用 `browser_type_secret` 从环境变量读取密钥，并在事件、日志、最终回答中脱敏。

本轮修复：
- 已补齐真实 Chrome 登录流的密钥输入能力：`browser_type_secret` 只从环境变量取值，不把明文密码写进 agent 最终回答或调试日志。
- 已让 `browser_flow_run` 支持从 workspace 内的 Markdown/JSON 阶段文件读取流程，避免长流程参数被模型写乱。
- 已修复 OAuth/API 模型结构化输出偶发损坏的问题：当模型返回不可解析 JSON 时，`CodexCliChatModel` 和 `CodexOAuthChatModel` 会追加一次“只修复 JSON”的重试提示，并只在修复后结构合法时继续执行工具。

自动化验证：
- `python -m unittest learning_agent.tests.test_models_codex_oauth`：47 tests OK。
- `python -m unittest learning_agent.tests.test_browser_runtime_alignment`：16 tests OK。
- `python -m py_compile learning_agent\models\adapters.py learning_agent\tests\test_models_codex_oauth.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_browser_runtime_alignment.py`：通过。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端执行 controller 场景。
- 验收 run：`learning_agent/acceptance_controller/runs/real_chrome_leishen_login_content-20260601_075721`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已通过：`python -m learning_agent.acceptance.verifier ...real_chrome_leishen_login_content-20260601_075721 ...real_chrome_leishen_login_content.json` 输出 `completed=true`、`assertion.passed=true`。
- 调试日志确认真实工具链：`browser_connect_real_chrome 成功`、`real_chrome_connected=true`、`browser_open 成功`、`browser_flow_run 完成`、`browser_type_secret 成功`、`browser_click 成功`、`browser_wait 成功`、`browser_screenshot 成功`、`browser_snapshot 成功`。
- 页面可见结果：登录成功，页面标题为 `皇上快点`，可见内容包含 `欢迎回来`、用户信息（已脱敏）和 `修改密码`。
- 页面截图证据：`learning_agent/browser_artifacts/leishen_after_account_login_v8.png`。

## 2026-06-01 Browser Runtime ClaudeCode 对齐升级计划

当前任务：
- 用户要求结合并参考 ClaudeCode 源码，先制定 `learning_agent` 真实浏览器能力的升级计划，不直接改运行时代码。

已完成：
- 已重新按源码证据归纳 ClaudeCode 可确认能力：`claude-in-chrome` MCP/Chrome 扩展桥接、skill 激活、tabs context、站点级权限、MCP progress、流式工具执行、并发安全、Chrome 状态 UI。
- 已把 learning_agent 当前能力边界写入计划：已有真实 Chrome/可见 Chromium/浏览器 MCP 工具/回放雏形/acceptance verifier，但缺少独立 Browser Runtime、状态机、locator、恢复策略、浏览器专用状态生态和 verifier 2.0 闭环。
- 已创建正式计划：`agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`。
- 已创建实施计划副本：`docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`。
- 已创建学习备份：`learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`。

下一步：
- 等用户确认后，从阶段 1 开始执行：先做 Browser Runtime 协议层和 Browser Runtime Store，不先堆更多零散浏览器工具。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 1-2

状态：部分完成，已完成底层协议层、持久化 store、浏览器 MCP server 工具执行入口接入、agent/status 状态镜像；整套 12 阶段任务尚未完成，真实可见终端验收尚未执行。

已完成：
- Stage 1：新增 `learning_agent/browser/runtime_models.py`，定义 `BrowserRun`、`BrowserSession`、`BrowserTab`、`BrowserAction`、`BrowserObservation`、`BrowserLocator`、`BrowserRecoveryAttempt`、`BrowserAssertion`、`BrowserCapabilityReport`。
- Stage 1：新增 `learning_agent/tests/test_browser_runtime_models.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.runtime_models'`，再实现协议层并通过测试。
- Stage 2：新增 `learning_agent/browser/runtime_events.py`，集中定义 `browser_run_created`、`browser_action_started`、`browser_action_completed`、`browser_observation_recorded` 等事件名。
- Stage 2：新增 `learning_agent/browser/runtime_store.py`，把 browser run/action/observation/event 持久化到调用方指定目录下的 `runs/`、`actions/`、`observations/`、`events/`。
- Stage 2：新增 `learning_agent/tests/test_browser_runtime_store.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.runtime_store'`，再实现 store 并通过测试。
- Stage 2：新增红灯测试锁定真实 `BrowserAutomationServer.call()` 必须自动创建 durable browser run 和 `browser_action_started/completed` 事件；红灯为 run 列表为空。
- Stage 2：已修改 `learning_agent/browser_automation_mcp_server.py` 的统一 `call()` 包装层，顶层工具调用会创建 browser run，嵌套 flow 阶段共享同一个 run，每个工具动作写 started/completed/failed。
- Stage 2：新增红灯测试锁定 `LearningAgent._execute_tool()` 调用 browser_automation MCP 工具后必须把 latest browser run 镜像到统一 status 事件；红灯为 `browser_runtime_event` 缺失。
- Stage 2：已修改 `learning_agent/core/agent.py`，浏览器 MCP 工具完成或失败后会扫描 `<workspace>/learning_agent/memory/browser_runtime/` 最新 run，写入 observation 和 `StatusEventStore(...).append("browser_runtime_event", ...)`。
- Stage 2：已修改 `learning_agent/runtime/status_schema.py`，把 `browser_runtime_event` 加入 v2 状态事件类型。
- 已把 Stage 1 代码备份到 `learning_agent/test/browser_runtime_claudecode_stage1_20260601/`。
- 已把 Stage 2 代码和 server 接入修改备份到 `learning_agent/test/browser_runtime_claudecode_stage2_20260601/`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：67 tests OK。
- `python -m py_compile learning_agent\core\agent.py learning_agent\runtime\status_schema.py learning_agent\browser_automation_mcp_server.py learning_agent\browser\runtime_models.py learning_agent\browser\runtime_events.py learning_agent\browser\runtime_store.py learning_agent\tests\test_browser_runtime_store.py`：通过。

未完成：
- browser runtime 事件已经镜像到统一 status event，但还没有在 status snapshot/CLI/API 中形成专门的 browser section。
- browser run id 还没有进入每一轮模型上下文的专用摘要，也没有和 verifier 2.0/acceptance scenario 完整闭环。
- 尚未完成 Stage 3-12。
- 尚未执行 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收；因此不能声明整套浏览器 runtime 对齐开发完成。

## 2026-06-01 Browser Runtime ClaudeCode 对齐执行记录：Stage 3

状态：Stage 3 已完成自动化测试和真实可见终端交互验收；整套 12 阶段任务仍未完成。

已完成：
- Stage 3：新增 `learning_agent/browser/tab_registry.py`，提供稳定 tab id、page_key 映射、active tab 切换、关闭清理和健康报告。
- Stage 3：新增 `learning_agent/browser/session_manager.py`，统一表示 `independent_chromium`、`visible_chromium`、`real_chrome_cdp` 三类浏览器 session。
- Stage 3：新增 `learning_agent/tests/test_browser_session_manager.py`，先观察红灯 `ModuleNotFoundError: No module named 'learning_agent.browser.session_manager'` 和 `BrowserAutomationServer` 缺少 `session_manager`，再实现通过。
- Stage 3：修改 `learning_agent/browser_automation_mcp_server.py`，在独立 Chromium 启动、可见 Chromium 启动、真实 Chrome CDP 连接、页面登记、页面关闭、标签切换、`browser_plugin_status`、`browser_profile_status` 中接入 `BrowserSessionManager`。
- Stage 3：真实 Chrome profile 状态只记录 `Default (scope)` 这类脱敏摘要，不保存完整 `User Data` 路径。
- Stage 3：已把本阶段代码备份到 `learning_agent/test/browser_runtime_claudecode_stage3_20260601/`。

自动化验证：
- `python -m unittest learning_agent.tests.test_browser_session_manager`：4 tests OK。
- `python -m unittest learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：68 tests OK。
- `python -m unittest learning_agent.tests.test_browser_session_manager learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_browser_intent learning_agent.tests.test_browser_harness learning_agent.tests.test_compact_resume_status_ecosystem learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment`：126 tests OK，skipped=1。
- `python -m py_compile learning_agent\browser\tab_registry.py learning_agent\browser\session_manager.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_browser_session_manager.py`：通过。

真实可见终端验收：
- 已通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端执行 controller 场景。
- 验收 run：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_105840`。
- `result.json` 显示 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已通过：`python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_visible_runtime_acceptance-20260601_105840 .\learning_agent\acceptance_controller\scenarios\browser_visible_runtime_acceptance.json`。
- 调试日志确认本次 Stage 3 新字段：`session_mode=visible_chromium`、`connected=true`、`visible=true`、`tab_count=1`、`active_tab_id=browser_session_1_fa131c86-tab-1`。

未完成：
- Stage 4-12 仍未完成，下一步应进入 Observation Engine / Locator Engine，而不是继续在 server 单体里堆零散工具。
