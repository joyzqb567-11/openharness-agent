# 项目上下文

## 2026-06-03 Phase 62 Computer Use High-Level Tools Snapshot

- Phase62 已完成 `learning_agent/computer_use/high_level_tools.py`，新增高层 Windows Computer Tool API。
- 当前高层操作包括 `observe_screen`、`find_control`、`click_control`、`type_into_control`、`wait_for_change`、`verify_screen`。
- 高层写动作仍必须经过 Phase60 持久授权、Phase31/50 桌面锁、Phase58 安全窗口目标守卫和 Phase61 abort-aware sender。
- 只读高层批量操作不会接管桌面写锁；写动作仍严格串行。
- `/computer high-level-tools` 和 `/computer status` 已显示 Phase62 marker、operation 清单、progress 路径、artifact 目录和 UIA candidate summary 支持。
- 真实可见终端验收证据：`learning_agent/acceptance_controller/runs/agent_capability_phase62_high_level_tools-20260603_185258/result.json`。
- Phase62 保持 `actions_expanded=false`，这是高层编排/API 升级，不是扩大真实桌面动作权限。

---

## 2026-06-03 Phase 38 Windows ComputerUseApproval Model

- Phase38 新增 `learning_agent/computer_use/approval.py`，提供 `WindowsComputerUseApprovalModel`、session app allowlist、grant flags、禁止目标分类、终端状态摘要和 CLI 合同。
- `ComputerUseController` 现在支持可选 `approval_model` 注入，并在后端执行前通过 `_reject_unapproved_action()` 拦截未授权 app、禁止目标和缺失 grant flag 的动作。
- `/computer status` 现在追加 `Computer Use Approval` 摘要，默认显示 `approval_model=phase38_windows_computer_approval`、`approval_granted_app_count=0`、grant flags 和 `actions_expanded=false`。
- PowerShell/cmd/Windows Terminal/Codex UI/security/password/auth/OTP/captcha/login 相关窗口仍是禁止自动化目标。
- `press_key` 中的 `ctrl+alt+delete`、`win+`、`alt+tab`、`ctrl+shift+esc` 等系统组合键需要 `systemKeyCombos=true`。
- Phase38 验证已通过：聚焦 6 tests OK、Phase30-38 邻近回归 45 OK、全量 670 OK skipped=1、真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_phase38_windows_computer_approval-20260603_105641` 和独立 verifier 通过。
- Phase38 不代表图形化审批 UI、真实 SendInput、真实 WGC 或真实 UIA 已成熟；后续 Phase39 应继续补 DPI/多显示器/坐标模型。

---

## 2026-06-03 Phase 37 Windows SendInput Executor

- Phase37 已把 Windows 写动作从旧 `SetCursorPos + mouse_event` 路径收口到 `learning_agent/computer_use/sendinput_executor.py` 的 `WindowsSendInputExecutor` 合同。
- `WindowsComputerUseBackend` 现在可注入 `action_executor`，并在 `status()` 中暴露 `action_executor_backend` 和完整执行器状态。
- 默认边界仍是安全关闭：没有真实底层实现注入时，Phase37 不会触碰鼠标键盘。
- `type_text` 在执行器层继续脱敏，只保留长度、短哈希和 `text_redacted=true`。
- Phase37 仍不代表真实 `ctypes.SendInput` 已成熟；后续 Phase38 先补 approval 模型，再继续做坐标/DPI/abort/image result/E2E。

---

## 2026-06-03 Phase 30 Windows OS Computer Use Safe Action Gate

- Phase 30 正在补 OS Computer Use 真实动作前的安全门禁，不扩大真实鼠标键盘能力。
- 新模块 `learning_agent/computer_use/lock.py` 负责 durable desktop control lock、owner session、release 和 abort flag。
- 新模块 `learning_agent/computer_use/action_policy.py` 负责窗口相对坐标转换、敏感文本脱敏、目标窗口摘要和 action evidence envelope。
- `ComputerUseController` 现在支持注入 `lock_manager`、`owner_session_id` 和生产默认 `auto_acquire_lock`。
- 显式注入锁管理器的动作必须由当前 session 持锁；abort flag 会在后端执行前阻止下一次动作。
- `MemoryComputerUseBackend`、controller audit、action evidence 和 `_computer_action` 权限/拒绝记录都不应保存原始 `type_text` 文本，只保留长度和短哈希。
- 提供 `window` 时，`computer_action` 的 x/y 表示窗口相对坐标；controller 会转换为屏幕坐标后传给后端。
- Phase 30 验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase30_windows_action_gate.json`。
- 当前边界：仍未实现真实 Windows native SendInput、Windows.Graphics.Capture、UIAutomationClient helper 或动作前后真实截图链。

---

## 2026-06-02 Phase 27 Windows OS Computer Use Protocol

- Phase 27 已完成 typed Computer Use 协议层，不包含真实 Windows 窗口枚举、截图保存、UIA 文本树或新增 SendInput 动作。
- 新的只读工具是 `computer_observe`，动作集合为 `list_apps`、`list_windows`、`get_active_window`、`get_window_state`。
- `computer_observe` 在 catalog 中是 `risk_level=low`、`is_read_only=true`、`is_concurrency_safe=true`、`permission_mode=auto_allow`。
- 高风险工具仍是 `computer_action`，仍必须 `confirm_desktop_control=true` 并经过权限通道。
- 窗口身份最小合同位于 `learning_agent/computer_use/models.py`：`app_id + window_id` 是可信窗口目标的必要身份字段。
- `ComputerUseController.execute()` 现在仅在参数包含 `window` 时进行未知窗口校验；旧的 Phase 20 坐标动作不带 `window` 时保持兼容。
- 内存后端现在支持注入 `windows=[...]`，用于协议测试和安全验收；它不会控制真实桌面。
- `WindowsComputerUseBackend.observe()` 当前明确返回“Phase 28 接入真实窗口枚举”的占位失败结果，避免误报真实 Windows 观察已完成。
- 真实可见终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase27_windows_computer_use_protocol.json`。
- 成功验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase27_windows_computer_use_protocol-20260602_233224`。
- 最新全量测试基线：`python -m unittest discover -s learning_agent\tests`，617 tests OK，skipped=1。
- Phase 28 推荐方向：只读窗口枚举、窗口截图证据、UI Automation 摘要、窗口相对坐标数据；不要先扩大真实动作。

---

## 2026-06-02 Phase 26 Windows OS Computer Use Blueprint

- Windows OS Computer Use 的下一步已编号为 Phase 26，因为 Phase 25 已被真实 Chrome extension/native-host 连接后续占用。
- Phase 26 只交付蓝图，不改运行时代码。
- 正式蓝图路径：`docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`。
- 记忆记录路径：`agent_memory/agent_capability_phase26_windows_computer_use_blueprint_20260602.md`。
- 学习备份路径：`learning_agent/test/agent_capability_phase26_windows_computer_use_blueprint_20260602/phase26_blueprint.md`。
- 核心方案：参考 ClaudeCode 的权限、锁、MCP、audit 架构；参考 Codex Computer Use 的 Windows app/window targeting、UI Automation、SendInput、Windows.Graphics.Capture；保留 learning_agent 的默认安全关闭、harness、verifier 和真实可见终端验收体系。
- 后续推荐 Phase 27-33：协议测试、只读窗口发现、窗口截图/UIA、窗口相对动作、锁/中止/证据链、`/computer` UI、真实端到端验收。

---

## 2026-06-01 Browser Dual Track Stage 8-12 当前结论
- 浏览器双轨架构已完成本轮核心闭环：统一 `browser_*` 工具表面、provider router/adapters、tabs context 合同、Chrome extension 状态/权限、action executor、observation、recording/GIF、replay、fallback/recovery、harness 投影和真实可见浏览器总验收。
- Stage 11 新增 `learning_agent/browser/harness_integration.py`，浏览器 run 现在会同步成同 id harness run/stage/event/verifier；状态快照可在 `browser.runs[*].harness` 和 `browser.harness.latest_verifier` 看到验收结果。
- Stage 12 通过 `browser_dual_track_stage12_acceptance.json` 真实可见终端验收，debug log 证明可见 Chromium 窗口执行了 launch/open/snapshot/screenshot/flow_run/plugin_status。
- 最新自动化总回归：`python -m unittest discover -s learning_agent\tests`，Ran 546 tests OK，skipped=1。
- 最新报告：`docs/superpowers/reports/2026-06-01-browser-dual-track-stage12-acceptance-report.md`。

## 2026-06-01 BrowserActionExecutor 执行层当前事实

- `learning_agent/browser/action_executor.py` 的 `BrowserActionExecutor.execute_action()` 现在不再只是记录动作生命周期，而是统一包住真实浏览器工具 handler 的开始、执行、重试、progress、完成和失败。
- `learning_agent/browser_automation_mcp_server.py` 的公开 `call()` 入口已经把 browser runtime run、action id、旧 action log、observation id 和 retry/error 分类回调交给 `BrowserActionExecutor.execute_action()` 编排。
- 浏览器写操作串行锁已从普通 `Lock` 改成可重入 `RLock`，因为 `browser_flow_run` 这类外层工具会在同一线程里递归调用 `browser_wait`、`browser_type_secret` 等内层工具；普通锁会导致真实长流程自锁超时。
- `BrowserActionExecutor.execute_action()` 现在支持 `on_result_chunk`，当 handler 返回非字符串可迭代片段时，会把每个片段写成 `browser_action_progress` 的 `result_chunk`，同时返回合并后的文本保持 MCP 兼容。
- `BrowserActionExecutor.execute_batch()` 现在支持基础批量调度：全是并发安全读工具时用线程池并发执行并按输入顺序返回；只要包含写工具则保守串行，避免点击、输入、导航污染同一页面。
- 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/browser_action_executor_execute_layer_acceptance.json`，用于确认 `browser_launch_visible`、`browser_open`、`browser_wait` 后 durable event log 同时包含 `browser_action_started`、`browser_action_progress`、`browser_action_completed`。
- 最新真实可见终端验收通过记录为 `learning_agent/acceptance_controller/runs/browser_action_executor_execute_layer_acceptance-20260601_124337/result.json`，独立 verifier 也显示 `completed=true`、`assertion.passed=true`。
- 批量并发与流式结果的真实可见终端验收通过记录为 `learning_agent/acceptance_controller/runs/browser_action_batch_stream_acceptance-20260601_125349/result.json`，独立 verifier 显示 `completed=true`、`assertion.passed=true`。

## 2026-05-31 Long-Task Harness v1 当前事实

- `learning_agent` 已新增独立 `learning_agent/harness/` 模块，用于长任务持久化、队列租约、阶段验收、失败恢复、checkpoint 和状态输出。
- 当前 harness 是独立底座，不直接替换 `LearningAgent.run()` 或 `LearningAgent.run_events()`；后续接入主循环时，应优先复用 `HarnessRun`、`HarnessQueue`、`HarnessRunner` 和 `StageVerifier`，不要再在 `core/agent.py` 内堆新的长任务状态。
- 推荐真实任务状态目录是 `learning_agent/memory/harness/`；测试和外部 agent 可以传入独立 store 目录，避免污染真实任务。
- 外部 agent 可用 `python -m learning_agent.harness status --store <目录> --run-id <任务ID>` 查看状态，可用 `python -m learning_agent.harness list --store <目录>` 列出任务。
- 外部 agent 现在也可用 `python -m learning_agent.harness enqueue --store <目录> --run-id <ID> --prompt <总任务> --stage "name::prompt" --success-marker "name=MARKER"` 创建任务。
- 外部 agent 可用 `python -m learning_agent.harness run --store <目录> --executor echo` 做无模型确定性 smoke，也可用 `--executor agent --workspace H:\codexworkplace\sofeware\OpenHarness-main\learning_agent` 走真实 `LearningAgent.run(stage.prompt)`。
- `learning_agent/harness/agent_executor.py` 是当前 harness 接入真实 agent 的薄适配层；后续不要在 CLI 里直接堆 LearningAgent 构造逻辑。
- 聚焦 harness 回归入口是 `python -m unittest learning_agent.tests.test_harness_long_task`。
- 本轮任务最终完成条件仍包括真实可见 `learning_agent/start_oauth_agent.bat` 终端交互验收；自动化测试不能替代该门禁。

## 2026-05-31 H 盘路径与真实终端验收当前事实

- 当前 OpenHarness 项目根目录是 `H:\codexworkplace\sofeware\OpenHarness-main`，当前 learning_agent 工作区是 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent`。
- `learning_agent/mcp_servers.json` 当前三个 MCP server 参数均指向 H 盘当前项目。
- 当前 OpenHarness 项目相关的旧盘符绝对路径已清理；若全文搜索仍看到 `D:\ClaudeCode-main\ClaudeCode-main`，它是外部 ClaudeCode 源码基线，不是 OpenHarness 运行路径。
- 真实可见终端 smoke 验收最新通过记录为 `learning_agent/acceptance_controller/runs/smoke-20260531_140112/result.json`，事件链为 `permission_auto_approved -> agent_ready_for_user_prompt -> user_prompt_received -> final_answer_printed -> agent_ready_for_user_prompt`。
- `learning_agent/acceptance_controller/scenarios/smoke.json` 已按客户模式更新为等待 `permission_auto_approved`，因为内置 MCP server 启动会自动授权，不再产生旧的 `permission_required` / `permission_answered`。

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

## 2026-05-31 Stage 15A event runtime context

- Stage 15A is being implemented in isolated worktree `.worktrees/stage15a-event-runtime`.
- The branch name is `stage15a-event-runtime`.
- Initial baseline commit on `main` is `3c657e5 chore: establish learning agent baseline`.
- New event foundation files:
  - `learning_agent/core/events.py`
  - `learning_agent/observability/transcript.py`
  - `learning_agent/tests/test_runtime_events.py`
- Stage 15A currently only adds standalone event/transcript primitives and does not yet integrate `LearningAgent.run()` or `run_events()`.
- `AgentEvent` is immutable and serializes to one JSONL line with `event_type`, `run_id`, `sequence`, `session_id`, `timestamp`, and `payload`.
- `TranscriptWriter` writes to `<base_dir>/<session_id>/events.jsonl` in append mode.
- New code backup for user learning is in `learning_agent/test/stage15a_event_runtime_20260531/`.

## 2026-05-31 Stage 15 event runtime current context

- Stage 15B added `ModelStreamEvent`, `StreamingChatModel`, and `stream_chat_events()` in `learning_agent/models/base.py`; old `chat()` models remain compatible.
- Stage 15C added `LearningAgent.run_events()` and transcript writes under `memory/sessions/<session_id>/events.jsonl`; old `run()` still returns plain text.
- Stage 15D extended `AgentTool` with Tool Protocol v3 metadata: concurrency safety, user interaction, interrupt behavior, permission mode, result policy, and timeout.
- Stage 15E added Tool Executor v2 lifecycle: permission_decided, pre_tool_use, post_tool_use, permission_denied, and tool_error observations.
- Stage 15F added `learning_agent/tools/orchestrator.py`; only consecutive read-only and concurrency-safe tools run in parallel, while writes, bash, browser side effects, and unknown tools stay serial.
- Stage 15G added `learning_agent/core/session.py`; session summaries are saved as `summary.json`, raw event transcript evidence is preserved, and compact creates a summary plus recent tail messages.
- Stage-specific learning backups are under `learning_agent/test/stage15*_20260531/`.

## 2026-05-31 Acceptance verifier and controller focus context

- Independent acceptance replay verifier lives at `learning_agent/acceptance/verifier.py`.
- CLI usage: `python -m learning_agent.acceptance.verifier <run_dir> <scenario.json>`.
- The verifier rereads `result.json`, `events.jsonl`, archived debug log, screenshots, required event states, final-answer contains checks, debug-log contains checks, and permission count limits.
- It reads PowerShell UTF-8 BOM JSON using `utf-8-sig`.
- The acceptance controller now verifies terminal focus with Win32 `GetForegroundWindow` and `GetWindowThreadProcessId` before sending prompt text.
- The controller uses Windows Terminal focus reinforcement through show, foreground, switch, temporary topmost, and an interior click.
- Latest successful smoke evidence: `learning_agent/acceptance_controller/runs/smoke-20260531_143929/result.json`.
- That run has `completed=true`, `prompt_send_attempts=1`, `prompt_received=true`, `final_printed=true`, and final answer `ACCEPTANCE_HARNESS_OK`.
- Learning backup for this work is `learning_agent/test/acceptance_verifier_20260531/`.

## 2026-05-31 ClaudeCode-aligned harness runtime context

- Active branch/workspace path: `H:\codexworkplace\sofeware\OpenHarness-main`, branch `feature/harness-claudecode-alignment`.
- Main runtime package: `learning_agent/runtime/`.
- `RuntimeCommandQueue` persists prompt, task notification, and resume commands under `memory/runtime`.
- `run_agent_with_harness_session()` wraps `LearningAgent.run()` and mirrors every `run_events()` event into `memory/harness`.
- `TaskRegistry`, `TaskOutputStore`, and `TaskPoller` persist task/background-command state and can enqueue task notifications.
- `HarnessStore` and `HarnessQueue` now use file locks, atomic JSON writes, JSONL helpers, and corrupt-state quarantine.
- Harness CLI now exposes `queue`, `tasks`, `events`, `resume`, and `poll`.
- Stage verifier now checks marker, artifact existence, artifact content, JSON required fields, command exit codes, event sequence, and acceptance-controller result JSON.
- Important bug fixed during real terminal acceptance: because `HarnessRun.create()` deep-copies stages, `session_runtime.py` must update `run.stages[0]`; otherwise the top-level run can complete while the stage stays pending.
- Final visible-terminal acceptance evidence: `learning_agent/acceptance_controller/runs/harness_runtime_alignment_status-20260531_165630/result.json`.
- Latest durable run evidence after the fix: `learning_agent/memory/harness/runs/runtime_275e3c33ad6ec332.json` has `status=completed`, `stages[0].status=completed`, and `stages[0].acceptance.passed=true`.
- Learning backup for this pass is `learning_agent/test/harness_claudecode_alignment_20260531/`.

## 2026-05-31 Harness final alignment context

- `LearningAgent.run()` now uses `learning_agent/runtime/session_runtime.py` to enqueue the real terminal prompt, drain durable runtime commands, build model-visible input, and mirror `run_events()` into `memory/harness`.
- `RuntimeCommandQueue` now feeds `prompt`, `task_notification`, and `resume_interrupted` commands into the real model turn instead of leaving them as side queues.
- Dynamic skill loading now maps all skill directories to their capability packs in `learning_agent/tools/schemas.py`; especially `long_running_work` unlocks both `execution` and `long_running_work`.
- Reading `learning_agent/skills/tool_list.md` then `learning_agent/skills/long_running_work/SKILL.md` makes `start_background_command`, `read_background_command`, `stop_background_command`, and `monitor` visible in the next tool schema.
- Background shell commands are now durable tasks: completion is written under `memory/tasks`, output goes under `memory/tasks/outputs`, and completion enqueues a `task_notification` without requiring `read_background_command`.
- Real visible terminal acceptance evidence:
  - `learning_agent/acceptance_controller/runs/harness_task_notification_seed-20260531_175937/result.json`
  - `learning_agent/acceptance_controller/runs/harness_task_notification-20260531_180044/result.json`
  - `learning_agent/acceptance_controller/runs/harness_runtime_resume-20260531_180202/result.json`
  - `learning_agent/acceptance_controller/runs/harness_background_shell_watchdog-20260531_180225/result.json`
  - `learning_agent/acceptance_controller/runs/harness_background_shell_notification-20260531_180359/result.json`
- All above result files have `completed=true` and `assertion.passed=true`.
- Final runtime queue check after visible-terminal acceptance reported `NO_QUEUED_COMMANDS`, so the test notifications were consumed rather than left to pollute future turns.

## 2026-05-31 Compact/Resume and status ecosystem context

- Compact/resume alignment now centers on `learning_agent/core/transcript_v2.py`, `learning_agent/core/turn_ledger.py`, `learning_agent/core/compact.py`, and `learning_agent/core/resume_loader.py`.
- The real `LearningAgent.run_events()` path writes transcript v2 entries, turn ledger checkpoints, compact boundary events, and unified status events under `learning_agent/memory`.
- Status ecosystem surfaces share one source: `learning_agent/runtime/status_events.py` and `learning_agent/runtime/status_snapshot.py`.
- Human terminal status uses `learning_agent/app/status_renderer.py` and interactive `/status`.
- SDK status uses `learning_agent/sdk/status.py`.
- HTTP bridge status uses GET `/status`, GET `/v1/status`, GET `/events`, and GET `/v1/events`.
- Harness CLI status snapshot uses `python -m learning_agent.harness.cli snapshot --workspace <path>`; `learning_agent/harness/cli.py` now has a real `__main__` entrypoint so this command prints output instead of silently exiting.
- Model-callable status tools are `status_snapshot`, `task_status`, `session_list`, `session_resume`, `compact_status`, and `event_tail`.
- New real-terminal acceptance scenario is `learning_agent/acceptance_controller/scenarios/compact_resume_status_ecosystem.json`.

## 2026-05-31 Deep compact/resume and status ecosystem context

- `learning_agent/core/compact.py` now uses a layered compact model: long tool output snip, microcompact summary, context-collapse commit id, autocompact metadata, and optional artifact paths.
- `learning_agent/core/reactive_compact.py` is the one-retry recovery layer for prompt-too-long/media-too-large style model failures.
- `learning_agent/core/resume_loader.py` now delegates resume consistency risk analysis to `learning_agent/core/resume_repair.py`.
- `ResumeRepairReport` records bad transcript lines, missing tool results, orphan tool results, interrupted turns, tombstones, warnings, and the resulting resume state.
- `learning_agent/runtime/status_schema.py` is the central status protocol version/type list. Keep new status event names there first, then emit them from runtime code.
- `StatusEventStore.append()` should receive top-level `session_id`, `run_id`, and `turn_id` when the caller knows them. It can still infer old payload identity fields for legacy data.
- `learning_agent/runtime/status_snapshot.py` now exposes v2 sections: `current_run`, `current_turn`, `compact`, `resume`, `model`, `tools`, `health`, `verifiers`, and legacy list/count fields.
- HTTP bridge status API includes `/runs`, `/sessions`, `/resume?session_id=...`, `/health`, `/events?event_type=...`, and their `/v1/...` aliases.
- SDK status helpers include `get_runs`, `get_sessions`, `get_health`, `load_resume_report`, `list_status_events`, and `watch_status_events`.
- Interactive terminal commands include `/status`, `/events`, `/sessions`, `/resume <session_id>`, and `/compact`.
- Model-callable long-running status tools include `resume_report`, `run_status`, and `health_status` in addition to the prior status tools.
- Compatibility rule: legacy status events without top-level identity and legacy compact boundaries without schema v2 fields must remain readable.
- Current automated evidence: targeted compact/resume/status tests passed, `compileall` passed, and full `unittest discover learning_agent.tests` passed with 426 tests OK and 1 skipped.
- Real visible terminal proof for this pass is `learning_agent/acceptance_controller/runs/compact_resume_status_deep_alignment-20260531_200122`, verified by `python -m learning_agent.acceptance.verifier` with `completed=true` and `assertion.passed=true`.
- The deep terminal scenario is `learning_agent/acceptance_controller/scenarios/compact_resume_status_deep_alignment.json`.

## 2026-05-31 真实可见浏览器 runtime context

- Browser visible acceptance now uses `learning_agent/acceptance_controller/scenarios/browser_visible_runtime_acceptance.json`.
- `browser_launch_visible` starts independent Chromium with `headless=false` after explicit `confirm_visible_browser=true`; it does not connect to the user's daily Chrome profile.
- After `browser_launch_visible` returns `visible_browser=true` and `headless=false`, `LearningAgent` marks `visible_browser_launched` and reloads the `browser_automation` tool pack so `browser_open` and later page tools are visible even when the prompt contains “真实浏览器”.
- `browser_plugin_status` reports `capabilities=visible_browser,page_recovery,visual_locate,coordinate_click,flow_run,action_log,replay,site_grant,retry`, plus `visible_browser` and `headless`.
- `browser_visual_locate` now includes non-interactive text blocks such as headings and paragraphs, not only clickable elements.
- `browser_flow_run` auto-fills an empty `browser_wait` stage with `milliseconds=250` to make simple flow proofs robust.
- Runtime file writes use retrying atomic replace in `learning_agent/runtime/files.py` to survive short Windows sharing violations during visible terminal acceptance.
- Real visible terminal/browser proof: `learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260531_211805/result.json` has `completed=true` and `assertion.passed=true`.

## 2026-05-31 自然实时查询浏览器路由 context

- 当前已确认缺口：普通天气/旅游攻略实时查询会走 `browser_search`，不会自动打开可见浏览器。
- 精准失败证据：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_212955/result.json`。
- 修复边界：普通公开实时查询应该走可见独立 Chromium；明确要求登录态、日常 Chrome、当前浏览器或真实 Chrome profile 的任务仍走真实 Chrome workflow。
- 本轮计划：`agent_memory/visible_browser_natural_query_route_plan_20260531.md`。
- 当前修复结果：普通天气、旅游攻略、新闻、价格、官网、会议、酒店、航班等公开实时查询会触发 `detect_visible_browser_information_task()`，注入 `Visible Browser Task Harness`，并在首轮预加载 `browser_launch_visible`、`browser_open`、`browser_snapshot` 等可见浏览器工具。
- 权限边界：普通可见浏览器查询只自动允许独立 Chromium 的公开网页动作；`browser_evaluate`、非 http(s) URL、缺少 `confirm_visible_browser=true` 的窗口启动不自动允许。
- 成功验收证据：`learning_agent/acceptance_controller/runs/wuhan_weather_travel_exact_prompt-20260531_215353/result.json`，独立 verifier 已通过。
## 2026-05-31 危险调试权限与真实 Chrome 验收上下文

- 当前项目根目录按用户要求以 `H:\codexworkplace\sofeware\OpenHarness-main` 为准；涉及 OpenHarness 当前运行路径时不要再误用 D 盘。
- 为了方便用户本地调试 learning_agent，`learning_agent/start_oauth_agent.ps1` 普通启动默认设置 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1`，语义类似 ClaudeCode 的 `--dangerously-skip-permissions`。
- 该危险模式只跳过 learning_agent 的权限确认层：终端 y/N 和 MCP 工具权限会写入 `permission_auto_approved` 事件并自动允许。
- 工具自身的安全参数仍然必须满足，例如 `browser_connect_real_chrome` 仍要求 `confirm_real_profile=true`；危险模式不能伪造真实 Chrome 连接成功。
- 若用户日常 Chrome 已经普通运行且没有 CDP，`browser_connect_real_chrome` 在危险调试模式下会改用 `browser_artifacts/real_chrome_debug_profile` 隔离 profile 启动真实 Google Chrome 测试窗口；这不会读取用户日常登录态。
- 本轮真实验收应使用 `learning_agent/acceptance_controller/scenarios/real_chrome_dangerous_skip_connect_public_page.json`，并通过 `start_oauth_agent.bat` 打开的真实可见终端观察结果。

## 2026-06-01 真实 Chrome 登录、密钥输入与模型 JSON 修复上下文

- 真实登录类浏览器验收必须优先使用 `browser_type_secret`，由环境变量提供账号/密码等敏感值；日志、事件、截图说明和最终回答都不得回显明文密钥。
- `browser_flow_run` 可以通过 `stages_file` 读取 workspace 内的 Markdown/JSON 阶段文件，适合把长浏览器流程固定成可审计、可复现的验收脚本。
- 当前雷神 H5 登录场景文件为 `learning_agent/acceptance_controller/scenarios/real_chrome_leishen_login_content.json`，阶段文件为 `learning_agent/acceptance_controller/scenarios/real_chrome_leishen_login_flow.md`。
- 成功验收证据为 `learning_agent/acceptance_controller/runs/real_chrome_leishen_login_content-20260601_075721/result.json`，其中 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 页面可见结果为：登录成功，页面标题 `皇上快点`，可见内容包含 `欢迎回来`、脱敏用户信息和 `修改密码`。
- 登录后截图证据为 `learning_agent/browser_artifacts/leishen_after_account_login_v8.png`。
- `CodexCliChatModel` 和 `CodexOAuthChatModel` 现在都有一次性结构化 JSON 修复重试；该机制只修复“模型返回坏 JSON 导致无法解析”的情况，不会无限重试，也不会掩盖第二次仍失败的真实错误。

## 2026-06-01 Browser Runtime ClaudeCode 对齐计划上下文

- 最新真实浏览器治本计划文件：`agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`。
- 实施计划副本：`docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`。
- 学习备份：`learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`。
- 计划结论：不要继续只补零散 `browser_click`、`browser_type` 护栏，应先建立 Browser Protocol、Runtime Store、Session Manager、Observation Engine、Locator Engine、Action Executor、Recovery/Replay/Verifier、Status Ecosystem。
- ClaudeCode 可确认的参考点：`claude-in-chrome` MCP/Chrome 扩展桥接、skill 激活、tabs context、站点级权限、MCP progress、流式工具执行、并发安全、Chrome 状态 UI。
- ClaudeCode 当前本地源码无法确认的点：外部包 `@ant/claude-for-chrome-mcp` 和 Chrome 扩展内部实现细节；不能把不可见实现当作源码证据。
- 后续执行推荐从阶段 1-2 开始：先做浏览器协议对象和持久化 store，再拆 session/observation/locator，不先扩大单体 MCP server。

## 2026-06-01 Browser Runtime Stage 1-2 context

- `learning_agent/browser/runtime_models.py` 是新的浏览器运行时协议层，当前只负责稳定数据对象、脱敏和 JSON round-trip，不负责真实浏览器控制。
- `BrowserAction.create(...)` 会把工具参数存成 `arguments_redacted`；当工具名包含 `secret` 时，会额外把 `text`、`value`、`input` 脱敏为 `[已脱敏]`。
- `BrowserRun` 现在能记录 `current_stage_id`、`completed_stage_ids`、`action_ids`、`observation_ids`、`status`、`summary` 和错误信息，为后续 resume/checkpoint 做基础。
- `learning_agent/browser/runtime_events.py` 是 browser runtime 事件名事实源，后续 CLI/API/status/verifier 应优先复用这些常量。
- `learning_agent/browser/runtime_store.py` 是新的浏览器持久化 store，可把 run/action/observation/event 写到调用方指定目录；生产接入时目标目录应使用 `learning_agent/memory/browser_runtime/`。
- 当前 store 已通过单测证明进程重启后能恢复 completed stage、action id、observation id 和 event log。
- `learning_agent/browser_automation_mcp_server.py` 的统一 `call()` 包装层现在会为顶层浏览器工具调用创建 durable browser run，并为工具写 `browser_action_started`、`browser_action_completed`、`browser_action_failed`。
- `browser_flow_run` 这类嵌套调用会通过 `browser_runtime_call_depth` 共享同一个 active browser run，避免每个子阶段都创建独立 run。
- 当前 browser runtime 生产写入路径为 `<workspace>/learning_agent/memory/browser_runtime/`，单元测试用临时 workspace 验证该路径。
- `LearningAgent._execute_mcp_tool()` 现在会在 browser_automation MCP 工具完成或失败后调用 `_record_browser_runtime_status_after_mcp_tool()`，扫描最新 browser run 并写 `browser_runtime_event`。
- `browser_runtime_event` 已加入 `learning_agent/runtime/status_schema.py` 的 v2 状态事件类型；payload 包含 `browser_run_id`、`browser_run_status`、`browser_current_stage_id`、`browser_action_ids`、`browser_observation_ids`、`browser_event_types`、`mcp_tool_name`、`mirror_state`。
- 重要边界：browser runtime 事件已经进入统一 status event，但 status snapshot/CLI/API 还没有专门的 browser section，verifier 2.0 也还没有读取 browser runtime run。
- 按 AGENTS.md 规则，任何声称“开发完成”的浏览器 runtime 任务都必须再通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端交互验收；本次 Stage 1-2 尚未完成该门禁。

## 2026-06-01 Browser Runtime Stage 3 context

- `learning_agent/browser/tab_registry.py` 是新的浏览器 tab registry，负责稳定 tab id、Playwright `page_id` 到 tab id 的映射、active tab 切换、关闭清理和 tab 健康报告。
- `learning_agent/browser/session_manager.py` 是新的浏览器 session manager，负责 `independent_chromium`、`visible_chromium`、`real_chrome_cdp` 的 session 状态、可见性、headless 状态、tab_count、active_tab_id 和脱敏 profile 摘要。
- `BrowserAutomationServer.session_manager` 现在是生产入口，不只是测试对象；`ensure_browser()`、`_register_page()`、`_forget_page()`、`browser_tabs switch/new`、`browser_open()`、真实 Chrome 连接和断开都会同步 manager。
- `browser_plugin_status` 现在输出 `session_mode`、`connected`、`visible`、`session_headless`、`tab_count`、`active_tab_id`，用于外部 agent/CLI/API 判断真实浏览器 session 状态。
- `browser_profile_status` 现在输出 `session_mode`、`session_connected`、`session_visible`、`session_tab_count`，用于真实 Chrome 和可见 Chromium 状态排查。
- 真实 Chrome profile 摘要仍必须保持脱敏：允许保存 `Default (debug_profile_fallback)`，不允许保存完整 `C:\Users\...\Chrome\User Data`。
- Stage 3 备份目录：`learning_agent/test/browser_runtime_claudecode_stage3_20260601/`。
- 当前自动化证据：浏览器相关 126 tests OK，skipped=1；Stage 3 新增文件和 server 通过 `py_compile`。
- 当前真实可见终端证据：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_105840/result.json` 中 `completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier 已复验同一 run，并且 `latest_run_readable.md` 明确包含 `session_mode=visible_chromium`、`connected=true`、`visible=true`、`tab_count=1`、`active_tab_id=browser_session_1_fa131c86-tab-1`。
- 当前门禁：Stage 3 已通过真实可见终端验收，但整套 12 阶段 Browser Runtime 尚未完成；后续仍需 Stage 4-12。

## 2026-06-01 Browser Runtime Stage 4-12 context

- `learning_agent/browser/observation.py` 是 Stage 4 Observation Engine，负责把页面 URL、title、visible_text、console、network、elements、screenshot_path 规范化成 `BrowserObservation`，并对 console/network 做敏感信息脱敏。
- `BrowserObservation` 协议现在包含 `artifact_paths`，用于保存超长 visible_text 等补充证据。
- `browser_snapshot` 成功后会调用 `_record_browser_runtime_observation(...)`，保存 observation 并在工具输出里返回 `observation_id`。
- `browser_screenshot` 成功后会保存 observation，并通过 `BrowserScreenshotIndex` 写入 `browser_artifacts/browser_screenshot_index.jsonl`。
- `learning_agent/browser/locator.py` 是 Stage 5 Locator Engine，输出 `BrowserLocator` 候选、置信度、selector、box 和 reason；坐标定位会按元素中心点距离评分。
- `learning_agent/browser/action_policy.py` 区分 read/write browser tools；`browser_snapshot`、`browser_screenshot`、`browser_console`、`browser_network` 等只读工具可并发，`browser_click`、`browser_type`、`browser_open` 等写工具必须串行。
- `learning_agent/browser/action_executor.py` 是动作生命周期事件工具，当前作为独立执行协议模块，后续可继续替换 server 内部手写 action wrapper。
- `learning_agent/browser/recovery.py` 是 Stage 7 错误分类和重试预算模块；`BrowserAutomationServer._fail_browser_runtime_action()` 现在使用 `classify_browser_error()` 写标准错误类型。
- `browser_flow_run` 已接入 `BrowserFlowRuntime` 和 `parse_browser_flow()`；如果调用方传 `flow_id` 或 `stages_file`，checkpoint 可用于跳过已完成阶段。
- `learning_agent/browser/secret_vault.py` 和 `site_permissions.py` 是 Stage 9 独立安全模型；server 旧的 secret/site_grant 逻辑仍存在，后续可进一步替换为这两个模块。
- `learning_agent/browser/assertions.py` 是浏览器验收断言引擎；支持 `url_contains`、`title_contains`、`visible_text_contains`、`screenshot_exists`、`secret_not_leaked`、`console_no_severe_error`。
- `learning_agent/browser/replay.py` 是基于 `BrowserRuntimeStore` 的 dry-run 回放计划器，会跳过 secret 输入和高风险工具。
- `learning_agent/acceptance/verifier.py` 现在是 schema_version=2；场景可配置 `browser_observation_path` 和 `browser_assertions`，浏览器断言失败会让总验收失败。
- `learning_agent/runtime/status_snapshot.py` 现在返回 `browser` 区块；SDK/HTTP/CLI/终端渲染都应优先读取这个统一事实源。
- Stage 4-12 自动化验证已全量通过：`python -m unittest discover -s learning_agent\tests` 为 483 tests OK，skipped=1。
- Stage 4-12 备份目录：`learning_agent/test/browser_runtime_stage4_12_20260601/`。
- 当前剩余门禁：还需要 `start_oauth_agent.bat` 真实可见终端验收；未完成前不能声明开发完成。

## 2026-06-01 Browser Runtime Stage 4-12 verified context

- Stage 12 已通过真实可见终端交互验收，入口是 `learning_agent/start_oauth_agent.bat`，controller 场景是 `learning_agent/acceptance_controller/scenarios/browser_visible_runtime_acceptance.json`。
- 成功 run 目录是 `learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_114746`。
- 该 run 的 `result.json` 显示 `completed=true`、`assertion.passed=true`、`final_printed=true`、`prompt_received=true`、`permission_sent_count=0`。
- 该 run 的 debug log 显示真实可见浏览器链路完成：`browser_launch_visible`、`browser_open`、`browser_snapshot`、`browser_screenshot`、`browser_flow_run`、`browser_plugin_status`。
- 该 run 的 debug log 显示 runtime 关键证据：`visible_browser=true`、`headless=false`、`observation_id=`、`flow_checkpoint`、`status_browser_runtime`、`browser_runtime_store=`、`compatible=true`。
- 独立 verifier 命令为 `python -m learning_agent.acceptance.verifier .\learning_agent\acceptance_controller\runs\browser_visible_runtime_acceptance-20260601_114746 .\learning_agent\acceptance_controller\scenarios\browser_visible_runtime_acceptance.json`，输出 `schema_version=2` 和 `completed=true`。
- 后续浏览器 runtime 任务应优先复用 `BrowserRuntimeStore`、`BrowserObservation`、`BrowserFlowRuntime`、`BrowserAssertionEngine` 和 `status_snapshot.browser`，避免再新增旁路状态。

## 2026-06-01 BrowserActionExecutor delegation context

- `BrowserActionExecutor.begin_action(...)` 现在支持可选 `action_id` 参数，生产 server 可以继续使用 `<browser_run_id>-action-<序号>` 这种稳定可读 id。
- `BrowserAutomationServer.__init__()` 现在创建 `self.browser_action_executor = BrowserActionExecutor(store=self.browser_runtime_store)`，动作生命周期事件不再直接散落在 server helper 内。
- `_start_browser_runtime_action()` 现在委托 `browser_action_executor.begin_action(...)` 写 `browser_action_started`。
- `_complete_browser_runtime_action()` 现在委托 `browser_action_executor.complete_action(...)` 写 `browser_action_completed`，并继续回填 observation id。
- `_fail_browser_runtime_action()` 现在委托 `browser_action_executor.fail_action(...)` 写 `browser_action_failed`，失败分类仍由 `classify_browser_error(...)` 产生。
- 本轮红灯测试覆盖了 executor 稳定 action id 和 server 委托 executor 两个行为，避免以后又回到双轨 action 生命周期。
- 当前仍未把工具实际执行函数放进 `BrowserActionExecutor.write_lock`；这是后续做“工具流式并发执行”时的下一层工作，不应和本轮生命周期收敛混在一起。
- 本轮真实可见终端验收使用聚焦场景 `learning_agent/acceptance_controller/scenarios/browser_action_executor_delegation_acceptance.json`。
- 成功 run 目录是 `learning_agent/acceptance_controller/runs/browser_action_executor_delegation_acceptance-20260601_122229`。
- 该 run 的 bash 检查输出 `ACTION_EXECUTOR_STORE_OK started=True completed=True`，说明 durable browser runtime events 中能看到 `browser_action_started` 和 `browser_action_completed`。
- 独立 verifier 对该 run 输出 `completed=true` 和 `assertion.passed=true`。
- 旧的大型可见浏览器场景本轮两次失败的原因是模型跳过 `browser_plugin_status` 并提前最终回答；后续如果继续使用该场景，应考虑把最终回答检查放宽或拆成更小的验收场景，避免把模型格式波动误判成浏览器 runtime 失败。
## 2026-06-01 ClaudeCode 本地真实浏览器对比上下文

- 当前项目根目录仍以 `H:\codexworkplace\sofeware\OpenHarness-main` 为准，不再使用 D 盘 OpenHarness 路径作为当前项目路径。
- ClaudeCode 源码路径为 `D:\ClaudeCode-main\ClaudeCode-main`，本次对比读取的是源码入口、Chrome 扩展 MCP、Computer Use、MCP client/config、工具执行、权限、终端 UI 和插件相关文件。
- learning_agent 当前真实浏览器能力已经从早期单一工具升级为双轨架构：可见 Chromium、真实 Chrome CDP、Chrome extension provider、provider router、runtime store、action executor、flow checkpoint/replay、status snapshot、acceptance verifier/controller。
- 后续若继续对齐 ClaudeCode，优先补生产级 Chrome 扩展安装/配对、OS 级 computer-use、StreamingToolExecutor 级别工具调度、Chrome 发起 prompt/session sync、`/chrome` 类状态 UI，而不是继续零散修单个 click/type。
## 2026-06-03 Phase 32 Windows OS Computer Use Native Observation Helper Context

- Phase32 新增 `learning_agent/computer_use/native_helper.py`，作为 Windows 只读 native observation helper 桥接层。
- 新 helper 的统一入口是 `WindowsNativeWindowObservationHelper`，输出仍是 Phase29 的 `WindowObservationPayload`，因此会自动进入现有 evidence store 和 Phase31 before/after evidence chain。
- 默认生产后端只有在显式设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE=1` 时才会注入 native helper；只设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE=1` 仍只做窗口 inventory。
- `Win32GdiWindowCaptureProvider` 是 GDI `PrintWindow`/`BitBlt` fallback，用于生成 BMP 截图 artifact；它不是完整 Windows.Graphics.Capture。
- `Win32WindowTextProvider` 是 Win32 标题/子控件文本 fallback；它不是完整 UIAutomationClient 文本树。
- Phase32 自动化测试使用 fake provider 验证 native helper 合同和 evidence 脱敏，不读取真实桌面。
- 当前自动化测试、全量回归和真实可见终端验收均已通过；成功 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase32_windows_native_helper-20260603_081430`。

---

## 2026-06-03 Phase 33 Windows OS Computer Use Native Diagnostics Context

- Phase33 在 Phase32 native helper 上新增 `learning_agent/computer_use/native_diagnostics.py`，只负责解释 provider 状态，不执行真实桌面动作。
- `WindowsNativeWindowObservationHelper.status()` 现在包含 `diagnostics`，诊断版本为 `phase33_windows_native_diagnostics`。
- `WindowsComputerUseBackend.status()` 现在包含 `native_observation_diagnostics`，供 `/computer`、SDK、HTTP、验收脚本和其他 agent 读取同一事实源。
- Phase33 诊断会同时列出 `windows_graphics_capture`、`win32_gdi_printwindow`、`uiautomation_client` 和 `win32_window_text`，并标明 active provider。
- Phase33 明确报告 `safe_observe_only=true` 和 `real_input_actions_expanded=false`，因此本阶段没有扩大真实鼠标键盘动作。
- Phase33 的 native 内容读取仍受 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE` 单独 opt-in 保护。
- 当前 Phase33 聚焦测试、邻近回归、全量回归、真实可见终端验收和独立 verifier 均已通过；成功 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase33_windows_native_diagnostics-20260603_082834`。

---

## 2026-06-03 Phase 34 Windows OS Computer Use UIAutomation Text Provider Context

- Phase34 在 `learning_agent/computer_use/native_helper.py` 中新增 `WindowsUiautomationTextProvider`，用于可选读取 UIAutomation 控件树文本。
- Phase34 新增 `FallbackNativeWindowTextProvider`，默认先尝试 UIA，失败或缺依赖时降级到 `Win32WindowTextProvider`。
- `WindowsNativeWindowObservationHelper` 默认文本 provider 已从纯 Win32 文本改成 UIA 优先组合 provider；显式注入 `text_provider` 的测试/验收路径保持兼容。
- UIA 树读取有 `max_depth` 和 `max_nodes` 上限，避免复杂窗口输出过多文本。
- UIA 文本仍进入现有 `ComputerUseEvidenceStore`，敏感行过滤继续负责去掉 password/token/credential/密码 等内容。
- Phase34 仍是只读观察增强，没有扩大真实鼠标键盘动作。
- 当前 Phase34 聚焦测试、邻近回归、全量回归、真实可见终端验收和独立 verifier 均已通过；成功 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase34_windows_uia_text_provider-20260603_090056`。

---

## 2026-06-03 Phase 31 Windows OS Computer Use Lock/Abort/Evidence Context

- Phase31 正在把 Windows OS Computer Use 从 Phase30 的动作门禁推进到“可中断、可恢复、可落盘复盘”的安全控制层。
- 新文件 `learning_agent/computer_use/audit.py` 负责保存 `memory/computer_use/audit/events.jsonl` 和 `memory/computer_use/audit/chains/<audit_id>.json`。
- `ComputerUseController` 现在可注入 `ComputerUseAuditStore`；生产默认 controller 在未注入测试后端时会启用落盘审计。
- 成功动作的 `action_evidence` 现在包含 `before_evidence`、`after_evidence`、`audit_id` 和可选 `chain_path`。
- `ComputerUseLockManager` 现在有 stale lock TTL，且用 `calendar.timegm(...)` 按 UTC 解析锁文件时间，避免东八区误判新锁为陈旧锁。
- 真实终端交互层新增 `/computer` 命令族，并在执行后写 `computer_status_printed` acceptance event，payload 里包含真实输出文本。
- Phase31 的真实可见终端场景是 `learning_agent/acceptance_controller/scenarios/agent_capability_phase31_windows_lock_abort_evidence.json`。
- 当前自动化测试、全量回归和真实可见终端验收均已通过；成功 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase31_windows_lock_abort_evidence-20260603_075659`。

---

## 2026-06-03 Phase 29 Windows OS Computer Use Observe Evidence

- Phase 29 已完成窗口状态 evidence store 和 helper contract。
- 新文件 `learning_agent/computer_use/evidence.py` 负责保存截图 artifact、metadata JSON、bounded UIA 摘要和敏感行过滤。
- 新文件 `learning_agent/computer_use/helper_client.py` 负责定义 `WindowObservationPayload`、`StaticWindowObservationHelper` 和 `NullWindowObservationHelper`。
- `WindowsComputerUseBackend.get_window_state` 现在会返回 `screenshot_id`、`screenshot_path`、`screenshot_captured`、`evidence_id`、`evidence_path`、`accessibility_excerpt`、`accessibility_truncated`、`accessibility_filtered_line_count`。
- `WindowsComputerUseBackend.status()` 现在暴露 `evidence_root`、`evidence_mode`、`observation_helper`、`observation_helper_available` 和 `observation_helper_reason`。
- UIA 摘要会过滤 password/token/credential/验证码/密码等敏感行，并限制 `accessibility_excerpt` 长度。
- 真实可见终端验收场景是 `learning_agent/acceptance_controller/scenarios/agent_capability_phase29_windows_observe_evidence.json`。
- 成功验收 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase29_windows_observe_evidence-20260603_062659`。
- 最新全量测试基线：`python -m unittest discover -s learning_agent\tests`，625 tests OK，skipped=1。
- 重要边界：Phase 29 验收使用静态安全 helper 证明 artifact/过滤合同；默认 helper 仍诚实说明未配置真实 native Windows.Graphics.Capture/UIAutomationClient helper。
- 下一步推荐 Phase 30：先补 durable lock、abort flag、action evidence envelope，再做极窄窗口相对动作。

---

## 2026-06-02 Phase 28 Windows OS Computer Use Read-Only Inventory

- Phase 28 已完成 Windows OS Computer Use 只读窗口枚举，不包含真实鼠标键盘动作扩展。
- 新文件 `learning_agent/computer_use/windows_backend.py` 是 Phase 28 的主要实现，包含 `StaticWindowsWindowInventory`、`WindowsWindowInventoryProbe` 和 `WindowsWindowInventorySnapshot`。
- `WindowsComputerUseBackend.observe()` 现在支持 `list_windows`、`list_apps`、`get_active_window`、`get_window_state`。
- 默认状态仍不观察真实桌面；只读观察 opt-in 环境变量是 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE`。
- 真实动作 opt-in 仍是 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`，与只读观察分离。
- Phase 28 的安全边界是：可以枚举安全窗口元数据，可以返回窗口矩形状态，但不能执行鼠标、键盘、窗口动作。
- `get_window_state` 的截图尺寸来自窗口 rect，`screenshot_id`、`evidence_path`、UIA 文本仍是 Phase 29 占位。
- 真实可见终端验收场景是 `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`。
- 成功验收 run 是 `learning_agent/acceptance_controller/runs/agent_capability_phase28_windows_inventory-20260602_234801`。
- 最新全量测试基线：`python -m unittest discover -s learning_agent\tests`，622 tests OK，skipped=1。
- 下一步推荐 Phase 29：真实截图证据文件、UI Automation 文本摘要、evidence_path，可继续避免真实动作扩展。

---
## 2026-06-03 Phase 35-42 Windows Computer Use ClaudeCode Alignment Context

- 用户要求先把后续 Windows Computer Use 对齐建议制作成升级蓝图，再逐项执行，避免复杂任务跑偏。
- 新主控蓝图文件：`docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`。
- 新 agent_memory 蓝图记录：`agent_memory/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603.md`。
- 新学习备份：`learning_agent/test/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603/phase35_42_blueprint.md`。
- Phase 35-42 顺序：真实安全窗口 UIA smoke harness、WGC provider 合同、SendInput executor、ComputerUseApproval 模型、DPI/多显示器坐标、global abort/cleanup/notification、截图结果 image/artifact、最终 E2E 矩阵。
- 当前依赖事实：本机没有 `uiautomation`、`comtypes`、`winrt/winsdk Windows.Graphics.Capture` Python 绑定；Phase 35 不能假装真实 UIA 已验收通过，必须先做真实 smoke harness 和诚实诊断。
- ClaudeCode 本地源码的 computer-use executor 是 macOS-only；后续只能参考架构，不能照搬为 Windows 成熟实现。

---
---

## 2026-06-03 Phase 39 Windows OS Computer Use Coordinate Context

- `learning_agent/computer_use/coordinates.py` is now the shared coordinate model for Windows Computer Use.
- `build_coordinate_context(window, relative_x, relative_y)` converts from window-relative logical coordinates to logical screen, display-relative logical, and physical screen coordinates.
- The coordinate context includes `dpi_scale`, `display`, `window_logical_rect`, and `window_physical_rect` so later SendInput, screenshot, and verifier logic can read one fact source.
- `learning_agent/computer_use/action_policy.py` now sends backend `x` and `y` as physical screen coordinates while keeping old Phase30 evidence keys for compatibility.
- `learning_agent/computer_use/controller.py` adds coordinate context to `get_window_state`; `learning_agent/computer_use/windows_backend.py` preserves raw `display` and `displays` metadata from inventory records.
- Phase39 acceptance evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase39_windows_coordinates-20260603_111521`, verified independently with `completed=true` and `assertion.passed=true`.
- Current boundary: true monitor enumeration still depends on later real provider data; Phase39 makes the model ready and test-covered but does not claim broad real action expansion.
---

## 2026-06-03 Phase 40 Windows OS Computer Use Session Runtime Context

- `learning_agent/computer_use/session_runtime.py` is now the shared Phase40 runtime layer for global abort, turn cleanup, and notifications.
- `WindowsComputerUseSessionRuntime.request_global_abort(...)` writes the existing durable abort flag through `ComputerUseLockManager` and records a `computer_use_abort_requested` notification.
- `WindowsComputerUseSessionRuntime.cleanup_turn(...)` releases a selected session lock and records `computer_use_turn_cleanup_completed`.
- Notifications are persisted as `session_runtime_notifications.json` in the same Computer Use lock root, so `/computer notifications` can show history across commands.
- `/computer status` includes a `Computer Runtime` section, while `/computer cleanup [session_id]` and `/computer notifications` are now supported terminal commands.
- Phase40 acceptance evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase40_windows_abort_cleanup-20260603_112730`, verified independently with `completed=true` and `assertion.passed=true`.
- Current boundary: Phase40 does not expand the real action surface; `actions_expanded=false` remains intentional.

---

## 2026-06-03 Phase 41 Windows OS Computer Use Image Result Context

- `learning_agent/computer_use/evidence.py` now owns the Phase41 model-visible screenshot result protocol.
- Phase41 constants are `PHASE41_WINDOWS_IMAGE_RESULTS_READY`, `PHASE41_WINDOWS_IMAGE_RESULTS_OK`, and `phase41_model_visible_image_results`.
- `ComputerUseEvidenceStore.save_window_state(...)` returns and persists `image_results` and `image_result_count` whenever a screenshot artifact is captured.
- `ComputerUseActionResult.to_text(...)` appends `Computer Use Image Results` lines for image blocks, including artifact path, MIME type, size, marker, and sensitive-text boundary.
- `WindowsComputerUseBackend.get_window_state` exposes image results at both top-level response data and inside `state`.
- `LearningAgent._record_computer_use_image_artifacts(...)` records Computer Use screenshot artifacts into `active_artifacts` and emits `computer_use_image_result`.
- The image result collector deduplicates repeated top-level/nested blocks by `artifact_path`.
- Phase41 acceptance evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase41_windows_image_results-20260603_114516`, verified independently with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Current boundary: Phase41 does not expand real desktop actions and does not include raw UIA text in image result blocks.

---

## 2026-06-03 Phase 42 Windows OS Computer Use Final Matrix Context

- `learning_agent/computer_use/final_matrix.py` is now the Phase42 aggregate contract runner for Phase35-41.
- `learning_agent/acceptance_controller/final_acceptance_matrix_phase42_windows_computer_use.json` is the final matrix file for Windows Computer Use Phase35-41.
- The matrix covers UIA dependency/safe-window boundary, WGC provider contract, SendInput fake safe action, approval allowlist/forbidden target, coordinate/window state, abort/cleanup/notifications, and image artifact visibility.
- The Phase42 CLI marker is `PHASE42_WINDOWS_COMPUTER_USE_FINAL_READY PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK phase_count=7 matrix=true observe=true evidence=true approval=true gated_refusal=true safe_action=true abort_cleanup=true artifact_visibility=true actions_expanded=false`.
- Phase42 acceptance evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase42_windows_computer_use_final_matrix-20260603_115600`, verified independently with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- The Phase35-42 Windows Computer Use ClaudeCode-alignment blueprint is now complete.
- Current boundary: Phase42 is a safe contract matrix; it does not install missing native dependencies, register OS services, or enable broad real desktop actions.

---

## 2026-06-03 Phase 57 Windows Real UIA Locator Context

- `learning_agent/computer_use/real_uia_locator.py` is the Phase57 production-style UIA locator layer.
- The real provider uses PowerShell with .NET `System.Windows.Automation` and returns sanitized JSON for a bounded control tree.
- The safe real smoke target is now a dedicated temporary WinForms window with a unique exact title, not Notepad, to avoid reading existing user Notepad tabs.
- `WindowsRealUiaLocatorRuntime.observe_window(...)` enforces a Phase57 safe title guard and rejects terminals, Codex UI, authentication, password, security, and admin targets.
- `SemanticControlLocator.find(...)` supports role, text/title, automation_id, class_name, and bounds queries, and returns candidate count, confidence, reason, and the matched control.
- `WindowsNativeHelperV2Worker.read_uia_tree` now uses the Phase57 runtime summary and exposes `real_uia_tree`, `semantic_locator_available`, `raw_text_included=false`, and `actions_expanded=false`.
- Phase57 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase57_real_uia_locator-20260603_173235/result.json`.
- Current boundary: Phase57 only observes and locates controls. It does not perform SendInput actions; Phase58 owns the first tightly guarded real action path.

---

## 2026-06-03 Phase 58 Windows Real SendInput Guard Context

- `learning_agent/computer_use/real_sendinput_guard.py` is the Phase58 guarded real input layer.
- The runtime supports only `move_mouse`, `click`, and `type_text` and only for dedicated `LearningAgent-Phase58-*` safe windows.
- `WindowsRealSendInputGuardRuntime.execute_safe_action(...)` performs target guard verification, before observation, low-level SendInput dispatch, after observation, and sanitized result reporting.
- Forbidden, sensitive, terminal, changed-title, missing, or non-Windows targets return before low-level event construction with zero low-level events.
- The real Unicode SendInput path must keep the full INPUT union size; otherwise Windows can accept mouse events while rejecting keyboard text events with return count 0.
- `windows_backend.normalize_window_record(...)` now prefers protocol `title_preview` over raw `title`, matching `models.py` and making target drift checks reliable.
- Phase58 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase58_real_sendinput_guard-20260603_175339/result.json`.
- Current boundary: Phase58 proves tightly guarded real input in a self-owned safe window only; Phase59+ must connect this safely into session policy, high-level tools, status UI, and final matrix without broad uncontrolled desktop writes.

---

## 2026-06-03 Phase 59 Windows Session Context Context

- `learning_agent/computer_use/session_context.py` is the Phase59 unified session context/AppState store.
- Default persisted state directory is `learning_agent/memory/computer_use/session_state/`.
- The state model is `phase59_windows_session_context_appstate`.
- The key marker is `PHASE59_WINDOWS_SESSION_CONTEXT_APPSTATE_READY`.
- The store persists allowed apps, grant flags, selected display, last screenshot dimensions, hidden windows, last action, last error, cleanup status, and state path.
- `/computer status` now includes a `Computer Session Context` section from this store.
- Phase59 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase59_session_context_appstate-20260603_180404/result.json`.
- Current boundary: Phase59 does not expand real desktop actions; it gives later phases a single state source to bind action policy, high-level tools, streaming traces, and controller takeover.

---

## 2026-06-03 Phase 60 Windows Persistent Grants Context

- `learning_agent/computer_use/persistent_grants.py` is the Phase60 persistent grant lifecycle store.
- Default persisted state directory is `learning_agent/memory/computer_use/persistent_grants/`.
- The state model is `phase60_windows_persistent_grants`.
- The key marker is `PHASE60_WINDOWS_PERSISTENT_GRANTS_READY`.
- Grant records include `session_id`, `app`, `window_id`, `display_id`, `action_scope`, `grant_flags`, `reason`, `created_at`, `expires_at`, `expires_at_epoch`, and revoke metadata.
- `/computer approve <app> [flags] ttl=60 scope=click` creates evaluable persistent grants.
- `/computer deny <app>` records an auditable denial.
- `/computer grants` displays `Computer Persistent Grants`.
- `/computer revoke <app>` revokes Phase60 persistent grants and also removes Phase51 terminal UI grant drafts.
- `/computer status` now includes `Computer Persistent Grants` with active/revoked/expired counts plus state and audit paths.
- Phase60 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase60_persistent_grants-20260603_182033/result.json`.
- Current boundary: Phase60 does not expand real desktop actions; later high-level tool and streaming layers must call `WindowsComputerUsePersistentGrantStore.evaluate(...)` before real action dispatch.

---

## 2026-06-03 Phase 61 Windows Abort Streaming Hooks Context

- `learning_agent/computer_use/abort_streaming_hooks.py` is the Phase61 abort/cleanup/streaming hook layer.
- The state model is `phase61_windows_abort_streaming_hooks`.
- The key marker is `PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_READY`.
- `Phase61AbortAwareLowLevelSender` wraps Phase58 low-level senders and checks the durable abort flag immediately before dispatch.
- When abort is requested, the next real action path returns `low_level_event_count=0` and records `computer_use_aborted_before_low_level_send`.
- `WindowsComputerUseAbortStreamingHooks.run_with_cleanup(...)` catches exception/interruption-style exits and runs runtime cleanup plus audit flush recording.
- `recover_stale_lock(...)` verifies stale recovery and then releases the recovered owner so recovery does not leave a new lock.
- `/computer abort-hooks` displays the hook model, hotkey fallback, stream event count, stream event path, cleanup hook list, and `actions_expanded=false`.
- `/computer status` now includes a `Computer Abort Streaming Hooks` section and shows `/computer abort-hooks` in the command list.
- Phase61 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase61_abort_streaming_hooks-20260603_183549/result.json`.
- Current boundary: Phase61 does not register a global hotkey or low-level keyboard hook by default; it honestly reports `global_hotkey_registered=false` and uses `/computer abort` plus controller abort fallback.
## 2026-06-03 Phase 63 Windows Controller Takeover Context

- `learning_agent/computer_use/controller_takeover.py` is the Phase63 external agent controller takeover and debug surface.
- The state model is `phase63_windows_controller_takeover_debug_surface`.
- The key marker is `PHASE63_WINDOWS_CONTROLLER_TAKEOVER_READY`.
- The surface builds a controller launch plan that uses `learning_agent/acceptance_controller/controller.ps1` and keeps `learning_agent/start_oauth_agent.bat` as the visible terminal gate.
- The surface can read acceptance run evidence from `result.json`, `events.jsonl`, `latest_run_readable.md`, and screenshot paths.
- The surface can export a compact evidence package to `learning_agent/memory/computer_use/controller_takeover/`.
- `/computer controller` displays the controller takeover panel with visible-terminal requirement, loopback/token boundary, run directory, package directory, abort preview, and approval-bypass denial.
- `/computer status` now includes a `Computer Controller Takeover` section.
- Phase63 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase63_controller_takeover-20260603_190537/result.json`.
- Current boundary: Phase63 does not expand desktop actions, does not replace visible terminal acceptance, and does not bypass approval, lock, persistent grants, target guard, or abort hooks.

---

## 2026-06-03 Phase 64 Windows Parity-Plus Matrix Context

- `learning_agent/computer_use/parity_plus_matrix.py` is the Phase64 final parity-plus production matrix for Phase53-63.
- The state model is `phase64_windows_parity_plus_production_matrix`.
- The key marker is `PHASE64_WINDOWS_PARITY_PLUS_MATRIX_READY`.
- The OK token is `PHASE64_WINDOWS_PARITY_PLUS_MATRIX_OK`.
- `run_phase64_parity_plus_matrix_contract(...)` executes the Phase53-63 contracts and returns `phase_flags`, `phase_results`, `phase_cli_lines`, `phase_reports`, and final gate booleans.
- `phase64_cli_line(...)` emits the stable token line used by the visible terminal scenario.
- The final required token line includes `phase_count=11`, all Phase53-63 flags as true, `all_phase_contracts_passed=true`, `non_fake_acceptance=true`, `visible_terminal_gate=true`, `approval_bypass_blocked=true`, `controlled_actions_expansion=true`, and `uncontrolled_actions_expanded=false`.
- Phase64 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase64_parity_plus_matrix-20260603_191743/result.json`.
- Current boundary: Phase64 is a matrix and does not itself control the desktop. Phase58 is the only expected action-expanded stage, and Phase64 treats it as safe only when target guard, persistent grants, abort hooks, and zero-event refusal are present.

---
---

## 2026-06-03 Phase65-75 Humanlike Windows Operator Blueprint Context

- 用户已把最终成功标准明确为拟人操作：用户可以在电脑上手动操作的普通应用程序，`learning_agent` 的 agent 都应能通过 prompt 操控。
- Phase65-75 最新蓝图已写入 `docs/superpowers/specs/2026-06-03-humanlike-windows-operator-blueprint.md`。
- Phase65-75 正式实施计划已写入 `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`。
- 蓝图明确不走“每个应用一个脚本”的路线，而走通用观察、任务规划、真实动作、后置校验和失败恢复闭环。
- Phase74 代表性真实应用 E2E 已加入真实 `mspaint.exe` 画图场景：打开本机画图软件，绘制简化版皮卡丘/黄色卡通电气鼠并保存。
- Paint 场景要求真实鼠标键盘操作画图软件，识别画布，选择颜色，绘制黄色主体、黑色耳尖、红色脸颊、眼睛、嘴巴、闪电尾巴，并保存视觉证据。
- Paint 场景明确禁止直接生成图片文件冒充画图操作结果。
- Phase75 最终矩阵必须包含 `mspaint_pikachu_scenario=true`、`real_paint_app_control=true`、`humanlike_drawing_actions=true`、`direct_image_file_cheat=false`。
- 当前步骤只落盘蓝图和记忆锚点，没有修改运行代码，也不声明功能开发完成；Phase65-75 实现时仍需自动化测试、编译检查和真实可见终端验收。

---

## 2026-06-03 Phase65 Humanlike Windows Operator Contract Context

- `learning_agent/computer_use/humanlike_operator_contract.py` is the Phase65 universal humanlike Windows Operator contract.
- The state model is `phase65_humanlike_windows_operator_contract`.
- The key marker is `PHASE65_HUMANLIKE_OPERATOR_READY`.
- The OK token is `PHASE65_HUMANLIKE_OPERATOR_OK`.
- `run_phase65_humanlike_operator_contract()` returns the stable contract facts for Phase65-75: humanlike operator contract enabled, prompt-to-normal-Windows-app target enabled, per-app scripts not required, high-risk confirmation required, direct file/image cheat blocked, and actions not expanded in Phase65.
- `phase65_cli_line(...)` emits the stable token line used by the visible terminal scenario.
- Phase65 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase65_humanlike_operator_contract-20260603_204739/result.json`.
- Current boundary: Phase65 is a contract foundation only. It does not yet launch, focus, click, type, drag, draw in Paint, or control arbitrary apps. Phase66 must start the observation fusion layer.

---

## 2026-06-03 Phase66 Observation Fusion Context

- `learning_agent/computer_use/observation_fusion.py` is the Phase66 fused observation runtime.
- The state model is `phase66_windows_observation_fusion`.
- The key marker is `PHASE66_OBSERVATION_FUSION_READY`.
- The OK token is `PHASE66_OBSERVATION_FUSION_OK`.
- `WindowsObservationFusionRuntime.observe(...)` fuses screenshot summaries, UIA safe node summaries, OCR/vision slot status, and window inventory state into one `FusedComputerObservation` dictionary.
- The OCR/vision slot is deliberately present even when no provider is installed: `provider_available=false`, `install_attempted=false`.
- The fused object keeps `raw_text_included=false` and filters sensitive UIA/OCR text before exposing fields to later planners.
- `run_phase66_observation_fusion_contract(...)` uses injected fake screenshot, UIA, and inventory inputs, so it does not touch real user windows.
- `phase66_cli_line(...)` emits the stable token line used by the visible terminal scenario.
- Phase66 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase66_observation_fusion-20260603_210148/result.json`.
- Current boundary: Phase66 does not expand desktop actions, does not install OCR/vision dependencies, and does not control real applications. Phase67 must build the prompt-to-task planner on top of this fused observation contract.

---

## 2026-06-03 Phase67 Prompt Task Planner Context

- `learning_agent/computer_use/prompt_task_planner.py` is the Phase67 deterministic prompt-to-task-plan layer.
- The state model is `phase67_windows_prompt_task_planner`.
- The key marker is `PHASE67_PROMPT_TASK_PLANNER_READY`.
- The OK token is `PHASE67_PROMPT_TASK_PLANNER_OK`.
- `WindowsPromptTaskPlanner.plan(...)` turns user prompts into structured steps containing `operation`, `target`, `expected_result`, `risk_level`, and `checkpoint`.
- Paint Pikachu prompts map to a representative generic plan for `mspaint`: launch, observe, identify canvas, select tool/color, draw body/face/cheeks/tail, save artifact, and verify visual result.
- Notepad prompts map to a generic text workflow: launch, observe, focus text area, type text, save document, and verify result.
- High-risk prompts containing password, payment, admin, captcha, login, security, credential, token, or Chinese equivalents are classified as `risk_level=high` and start with `request_user_confirmation`.
- Phase67 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase67_prompt_task_planner-20260603_212145/result.json`.
- Current boundary: Phase67 is a deterministic planner only. It does not launch apps, send input, click, draw, save files, or call an LLM. Phase68 must connect plans to a closed-loop fake execution runtime before real app control is broadened.

---

## 2026-06-03 Phase68 Closed-Loop Executor Context

- `learning_agent/computer_use/closed_loop_executor.py` is the Phase68 closed-loop execution discipline layer.
- The state model is `phase68_windows_closed_loop_executor`.
- The key marker is `PHASE68_CLOSED_LOOP_EXECUTOR_READY`.
- The OK token is `PHASE68_CLOSED_LOOP_EXECUTOR_OK`.
- `WindowsClosedLoopComputerExecutor.run(...)` executes injected fake observer, actor, verifier, and recoverer components in the order `observed`, `decided`, `acted`, `verified`, `recovered`, and `stopped`.
- Every step observes before action.
- Every write action verifies after action.
- Failed verification triggers recovery, a new observation, and a second verification.
- `blind_write_chain_detected(...)` detects two write actions without an intervening observation.
- `run_phase68_closed_loop_executor_contract()` proves closed-loop execution, post-action verification, failure recovery, blind write chain blocking, and `actions_expanded=false`.
- Phase68 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase68_closed_loop_executor-20260603_221434/result.json`.
- Current boundary: Phase68 does not expand desktop actions, does not launch apps, does not send real input, and does not control Paint. Phase69 must add safe app launch, focus, target identity, and target drift handling.

---

## 2026-06-03 Phase69 App Window Control Context

- `learning_agent/computer_use/app_window_control.py` is the Phase69 app launch, focus, and target window identity layer.
- The state model is `phase69_windows_app_window_control`.
- The key marker is `PHASE69_APP_WINDOW_CONTROL_READY`.
- The OK token is `PHASE69_APP_WINDOW_CONTROL_OK`.
- `build_launch_plan(...)` creates safe `Start-Process` style launch plans with `changes_registry=false`, `changes_system_settings=false`, `requires_admin=false`, and `uses_shell_string=false`.
- `Phase69RecordingLauncher` records launch plans and returns synthetic safe window identities without opening real user applications.
- `Phase69RecordingFocuser` records focus requests without changing the real foreground window.
- `WindowsAppWindowControlRuntime.verify_target_identity(...)` compares `app_id`, `window_id`, `pid`, and title hash to detect target drift.
- `run_phase69_app_window_control_contract(real_smoke=False)` proves app launch, window focus, target identity, target drift blocking, safe start process plan, recording launcher, and `actions_expanded=false`.
- Phase69 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase69_app_window_control-20260603_223344/result.json`.
- Current boundary: Phase69 does not expand desktop actions, does not open real apps in acceptance, does not click/type/drag/draw, and does not control Paint. Phase70 must add generic click/type/control actions behind these target identity guarantees.

---

## 2026-06-03 Phase70 Generic Control Actions Context

- `learning_agent/computer_use/generic_control_actions.py` is the Phase70 generic click/type/control action wrapper.
- The state model is `phase70_windows_generic_control_actions`.
- The key marker is `PHASE70_GENERIC_CONTROL_ACTIONS_READY`.
- The OK token is `PHASE70_GENERIC_CONTROL_ACTIONS_OK`.
- `WindowsGenericControlActionRuntime.click_by_query(...)` uses the Phase57 `SemanticControlLocator` to map a query to a UIA control, then delegates `click_control` to a Phase62-style high-level tool.
- `WindowsGenericControlActionRuntime.type_by_query(...)` prefers `role=Edit`, delegates `type_into_control`, and reports only text length/hash rather than raw text.
- `WindowsGenericControlActionRuntime.click_by_visual_point(...)` converts a visual point into a synthetic control so canvas-like areas can still flow through the high-level click interface.
- Missing targets return zero-event refusal with no high-level or low-level events.
- Phase70 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase70_generic_control_actions-20260603_224944/result.json`.
- Current boundary: Phase70 uses a recording high-level tool for contract acceptance and does not add hotkeys, menu navigation, scroll, drag, drawing paths, real Paint control, or real app authorization. Phase71 must add generic input actions.

---

## 2026-06-03 Phase71 Generic Input Actions Context

- `learning_agent/computer_use/generic_input_actions.py` is the Phase71 hotkey, menu, scroll, and drag event builder layer.
- The state model is `phase71_windows_generic_input_actions`.
- The key marker is `PHASE71_GENERIC_INPUT_ACTIONS_READY`.
- The OK token is `PHASE71_GENERIC_INPUT_ACTIONS_OK`.
- `build_hotkey_events(...)` emits ordered `key_down` and reverse `key_up` events for normal app hotkeys such as `ctrl+s`.
- `build_menu_sequence(...)` emits `menu_open`, `menu_item`, and `menu_commit` events for future menu navigation.
- `build_scroll_events(...)` emits `mouse_move` and `mouse_wheel` events.
- `build_drag_path(...)` emits a continuous drag path with mouse move/down/move/up events, needed for later Paint drawing workflows.
- `WindowsGenericInputActionRuntime` sends all events to `Phase71RecordingInputSender` in contract mode.
- Every Phase71 event has `real_dispatch_allowed=false`; real dispatch must be enabled only after Phase72 policy.
- Phase71 blocks `ctrl+alt+delete`, `win+r`, `win+x`, `ctrl+shift+esc`, and all Windows-key combinations with zero events.
- Phase71 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase71_generic_input_actions-20260603_230243/result.json`.
- Current boundary: Phase71 does not send real input, does not authorize real applications, and does not draw in Paint. Phase72 must add the real-app safety boundary.

---

## 2026-06-03 Phase72 Real App Safety Boundary Context

- `learning_agent/computer_use/real_app_safety_boundary.py` is the Phase72 final policy gate before ordinary real Windows app actions may reach a low-level sender.
- The state model is `phase72_windows_real_app_safety_boundary`.
- The key marker is `PHASE72_REAL_APP_SAFETY_BOUNDARY_READY`.
- The OK token is `PHASE72_REAL_APP_SAFETY_BOUNDARY_OK`.
- `WindowsRealAppSafetyBoundary.evaluate(window, action, grant_store, session_id)` refuses dangerous windows first, then requires a Phase60 active persistent grant, then checks a Phase61-compatible abort gate immediately before low-level send.
- The boundary refuses terminal windows, Codex UI, login/auth/captcha/payment/admin/security/private-data windows, Windows Run, and system management windows by default.
- Any refusal returns `low_level_event_count=0`, `ready_for_low_level_send=false`, and a stable `decision`.
- Approval-bypass hints such as `approval_bypass=True` or `previous_approval={"allowed": true}` do not replace Phase60 persistent grants.
- Phase72 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase72_real_app_safety_boundary-20260603_231727/result.json`.
- Current boundary: Phase72 expands only controlled real-app action eligibility. It does not directly dispatch input, implement app memory, draw in Paint, or generate the final Phase75 matrix. Phase73 must add non-secret app memory and self-learning hints.

---

## 2026-06-03 Phase73 App Memory Context

- `learning_agent/computer_use/app_memory.py` is the Phase73 non-secret app memory and self-learning hint store.
- The state model is `phase73_windows_app_memory`.
- The key marker is `PHASE73_APP_MEMORY_READY`.
- The OK token is `PHASE73_APP_MEMORY_OK`.
- `WindowsComputerUseAppMemoryStore.remember_app_hint(...)` stores only safe hint types: `window_class`, `role_hint`, `safe_control_name`, `menu_label`, and `last_successful_strategy`.
- `WindowsComputerUseAppMemoryStore.list_app_hints(app)` returns active non-revoked hints sorted by confidence.
- `WindowsComputerUseAppMemoryStore.revoke_app_memory(app)` marks only that app's active hints revoked.
- Phase73 rejects password, token, cookie, API key, captcha, OTP, 2FA, verification, payment, banking, private key, long sensitive number patterns, terminal commands, and script-like hint types.
- Rejected inputs are audited with `redacted=true` and a short hash, not raw sensitive text.
- Phase73 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase73_app_memory-20260603_233154/result.json`.
- Current boundary: Phase73 does not expand desktop actions, does not dispatch input, and does not prove real application E2E. Phase74 must prove representative real app workflows, including Paint Pikachu, on controlled files/artifacts only.

---

## 2026-06-04 Phase74 Representative E2E Context

- `learning_agent/computer_use/representative_e2e_matrix.py` is the Phase74 representative real-app E2E matrix.
- The state model is `phase74_windows_representative_e2e_matrix`.
- The key marker is `PHASE74_REPRESENTATIVE_E2E_READY`.
- The OK token is `PHASE74_REPRESENTATIVE_E2E_OK`.
- The matrix covers Notepad text edit/save, Explorer controlled folder navigation, Browser safe blank page flow, standard window/dialog style, and Paint Pikachu.
- The Paint Pikachu scenario targets `mspaint.exe`, builds 13 humanlike drag strokes, includes yellow body, black ear tips, eyes, mouth, red cheeks, arms, and lightning tail, and writes interaction evidence to `learning_agent/memory/computer_use/representative_e2e/e2e_paint/paint_pikachu_interaction_evidence.json`.
- Phase74 explicitly reports `direct_image_file_cheat=false`; it plans a controlled PNG save target but does not write bitmap pixels directly in safe contract mode.
- Phase74 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase74_representative_e2e-20260604_062842/result.json`.
- Current boundary: Phase74 proves safe-contract representative workflows and Paint action evidence. It does not open Paint live or dispatch real input during tests/acceptance. Phase75 must aggregate Phase65-74 into the final Humanlike Windows Operator matrix.

---

## 2026-06-04 Phase75 Humanlike Windows Operator Final Matrix Context

- `learning_agent/computer_use/humanlike_operator_matrix.py` is the Phase75 final rollup matrix for Phase65 through Phase74.
- The state model is `phase75_humanlike_windows_operator_final_matrix`.
- The key marker is `PHASE75_HUMANLIKE_WINDOWS_OPERATOR_READY`.
- The OK token is `PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK`.
- The final matrix covers exactly ten input phases: Phase65, Phase66, Phase67, Phase68, Phase69, Phase70, Phase71, Phase72, Phase73, and Phase74.
- The matrix artifact is `learning_agent/memory/computer_use/humanlike_operator_matrix/phase75_humanlike_operator_matrix.json`.
- Phase75 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase75_humanlike_operator_matrix-20260604_065138/result.json`.
- Verified final tokens include `prompt_to_any_normal_app=true`, `humanlike_observe_act_verify_loop=true`, `generic_windows_app_control=true`, `per_app_scripts_required=false`, `mspaint_pikachu_scenario=true`, `direct_image_file_cheat=false`, `approval_bypass_blocked=true`, and `uncontrolled_actions_expanded=false`.
- Current boundary: Phase75 is a safe-contract final matrix. It proves the designed capability chain and visible terminal gate, but it does not open Paint live, dispatch real input, or claim unlimited arbitrary-app perfection. Live app-control smoke should be a separately planned production phase.

---

## 2026-06-04 Phase76-89 Windows Production Live-Control Context

- `learning_agent/computer_use/production_live_control.py` is the Phase76-89 production live-control closure for Windows Computer Use.
- The key marker is `PHASE76_89_WINDOWS_LIVE_CONTROL_READY`.
- The OK token is `PHASE76_89_WINDOWS_LIVE_CONTROL_OK`.
- The covered phases are exactly Phase76 through Phase89, `phase_count=14`.
- The baseline gap recorded for this batch is `35%`, inherited from the ClaudeCode comparison discussion.
- The module adds a unified `WindowsProductionComputerUseHostAdapter`, `WindowsLiveControlPermissionGate`, and `WindowsProductionClipboardGuard`.
- The contract covers ClaudeCode parity matrix, observation fusion, display coordinate model, SendInput production gate, clipboard save/verify/restore, app launch/focus plan, allowlist/sentinel permissions, global abort, turn cleanup, high-level tool surface, observe-act-verify loop, representative E2E matrix, and visible terminal gate.
- The representative E2E matrix includes Notepad, Paint Pikachu, Calculator, Explorer, Browser, and security-window denial.
- Paint Pikachu remains humanlike-stroke based with `direct_image_file_cheat=false`.
- Phase76-89 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase76_89_windows_live_control-20260604_092149/result.json`.
- Current boundary: Phase76-89 is a production structure and safety-gated contract closure. It does not claim uncontrolled arbitrary-app dispatch; live input remains gated behind explicit environment/safety checks.

---

## 2026-06-04 Phase90 Live App Dispatcher Context

- `learning_agent/computer_use/live_app_dispatcher.py` is the Phase90 controlled live app dispatcher.
- The key marker is `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_READY`.
- The OK token is `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK`.
- The dispatcher composes Phase60 persistent grants, Phase69 app/window control, Phase71 input events, Phase72 real app safety boundary, Phase74 Paint Pikachu plan, and optional Phase58 safe-window real SendInput smoke.
- The representative apps are Notepad, Paint, Calculator, Explorer, and Browser.
- Default real dispatch is disabled and requires `LEARNING_AGENT_PHASE90_ENABLE_REAL_DISPATCH=1`.
- The current Phase90 acceptance proves the dispatcher path with recording dispatch, not uncontrolled live arbitrary-app control.
- Phase90 visible terminal evidence is `learning_agent/acceptance_controller/runs/agent_capability_phase90_live_app_dispatcher-20260604_093939/result.json`.
- Current boundary: Phase90 can route an authorized app action into the controlled dispatch path and block unauthorized or dangerous targets with zero events. It still does not claim perfect operation of all Windows apps.
