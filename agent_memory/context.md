# 项目上下文摘要（2026-06-16）

历史全文归档：`agent_memory/archive/2026-06-16-computer-use-mcp-v2-parity/`。

## 当前任务

用户要求把 OpenHarness 的 Computer Use 功能对齐 ClaudeCode。用户已选择“B. 完全对齐版”，并确认 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp` 是用于反推 ClaudeCode 外部 `@ant/computer-use-mcp` 包的目录。

已确认边界：ClaudeCode 是 macOS native package 接口，OpenHarness 是 Windows in-tree runtime，底层接口天然不同，不能要求代码级完全一致。除这个差异外，模型可见工具、参数 schema、分发链路、结果结构、错误语义、图片结果、动作能力和安全边界都按 ClaudeCode 可观察行为补齐。

## 当前设计分层

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/`：反推外部 MCP 包合同层，负责工具名、schema、运行时分发、错误结构、host 合同和旧入口隔离。
- `learning_agent/computer_use_mcp_v2/claudecode_bridge/`：保留 ClaudeCode 风格命名和桥接入口，用来让上层更容易理解来源。
- `learning_agent/computer_use_mcp_v2/openharness_bridge/`：保留 OpenHarness agent/终端主循环接线。
- `learning_agent/computer_use_mcp_v2/windows_runtime/`：Windows 真实运行时，负责截图、坐标映射、controller、SendInput、artifact 和 runtime trace。

## Computer Use MCP v2 总链路

模型选择 `mcp__computer-use__*` 工具后，先进入 `inferred_ant_mcp/build_tools.py` 定义的公开工具面，再由 `inferred_ant_mcp/runtime.py` 统一分发。只读观察走 `observation.py`，动作走 `actions.py`，批量走 `batch.py`，授权和剪贴板分别走 `permissions.py`、`clipboard.py`。agent-side 运行时通过 `legacy_ports.py` 构造 host adapter，再交给 `windows_runtime/mcp_session_adapter.py`，最终复用 OpenHarness Windows controller、截图证据链、SendInput 执行链和 agent 事件记录链。

## 已完成关键能力

- 旧聚合工具、shell 工具和文件工具不再进入 Computer Use MCP 工具面。
- 公开工具已补齐：`middle_click`、`triple_click`、`left_mouse_down`、`left_mouse_up`、`hold_key`、`left_click_drag`、`zoom`。
- 写动作无 host 时失败，不再 no-op 假成功。
- `left_mouse_up` schema 要求坐标，避免释放动作丢证据。
- `hold_key` 已对齐 keys 数组、真实执行、异常清理和 batch 失败传播。
- `observe`、`screenshot` 和 `zoom` 已走只读观察语义。
- `zoom` 已在 Windows adapter 层尝试生成局部裁剪 PNG，并把裁剪图作为模型可见 `image_result` 返回。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/README.md` 已补充反推包定位、文件职责、接口合同、总链路和对齐结论。
- `docs/computer_use_mcp_v2_architecture.md` 已补充 MCP v2 架构文档，记录 24 个公开工具、agent-side wrapper、standalone_stdio_diagnostic 和 Windows runtime 边界。
- `learning_agent/mcp_servers.json` 已注册 `computer-use` 独立 stdio server，真实配置不再只存在于测试里。
- `learning_agent/acceptance_controller/probes/computer_use_independent_mcp_server_probe.py` 和对应可见终端场景已补齐，用于真实终端验收时复跑独立 MCP server 自检。

## 最新验证状态

最近一次聚焦自动化验证：

`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_v2_sendinput_parity_task4 learning_agent.tests.test_computer_use_mcp_v2_primary_paths learning_agent.tests.test_computer_use_mcp_v2_internal_adapter_fence learning_agent.tests.test_computer_use_mcp_agent_side_binding learning_agent.tests.test_computer_use_mcp_batch_safety learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_v2_architecture_docs learning_agent.tests.test_computer_use_mcp_v2_state_observe_action_loop learning_agent.tests.test_computer_use_tool_scope learning_agent.tests.test_windows_computer_use_image_results_phase41 learning_agent.tests.test_windows_computer_use_real_screenshot_phase56`

结果：77 个测试通过。

补充验证：`python learning_agent\acceptance_controller\probes\computer_use_independent_mcp_server_probe.py` 输出 `COMPUTER_USE_MCP_V2_READY`；`python -m py_compile learning_agent\acceptance_controller\probes\computer_use_independent_mcp_server_probe.py learning_agent\tests\test_computer_use_mcp_v2_architecture_docs.py` 通过。

真实可见终端验收：已使用安全场景调用 `/computer use --full`，再让模型只调用一次 `mcp__computer-use__list_granted_applications`，最终回答 `COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK`。worktree run 和原项目精确 `start_oauth_agent.bat` run 均通过；原项目 run 路径为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_smoke_visible_terminal-20260616_092030\result.json`。

最新相关提交：`659b7c0 feat: return model-visible zoom screenshots`。

## 真实终端验收

按照 AGENTS 规则十七，真实可见终端交互验收已经完成：原项目路径 controller 启动了 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实终端中输入 `/computer use --full` 和只读 MCP 工具验证 prompt，观察到 `list_granted_applications ok=true`，最终输出 `COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK`。

## 2026-06-16 Lifecycle Parity 当前状态

本轮长任务已完成 `docs/superpowers/plans/2026-06-16-computer-use-claudecode-lifecycle-parity.md` 的代码、测试、CodeGraph、学习备份和真实终端验收闭环。代码层四项主体任务已完成：Esc acquire 后注册全局 Escape 急停、session cleanup 统一走 `run_turn_cleanup()`、standalone `tools/list` disabled 返回空工具列表、外部 `displayResolvedForApps` 改为 ClaudeCode string key 且 rich records 保留。

当前稳定验收事实：92 个 v2 computer use 相关测试通过；关键文件与学习备份 `py_compile` 通过；真实可见终端 run `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal-20260616_234022\result.json` 通过；CodeGraph 已执行 `codegraph index --force .` 并显示 `[OK] Index is up to date`，统计为 `Files 1,260`、`Nodes 48,491`、`Edges 159,608`。

后续若继续做 ClaudeCode parity，优先基于当前主目录和最新 CodeGraph，不再从旧 `.worktrees` 或历史备份目录取实现。

## 2026-06-17 Computer Use ClaudeCode Windows Parity 蓝图范围

已创建正式书面蓝图：`docs/superpowers/plans/2026-06-17-computer-use-claudecode-windows-parity-blueprint.md`。本蓝图用于继续对齐当前审计中值得推进的差异：Windows 系统剪贴板桥接、ClaudeCode-compatible 权限审批语义补强、CA07/CA13/CA14 矩阵证据硬化、真实可见终端门禁。明确排除外部 MCP 包内部实现、macOS TCC/Swift helper、`pbcopy/pbpaste` 等 macOS 专属机制，以及 Windows/macOS 系统差异导致的不可比行为。

## Computer Use ClaudeCode Windows Parity Scope - 2026-06-17

- 目标：让 OpenHarness Computer Use 在 Windows 上对齐 ClaudeCode 的可观察协议、权限、剪贴板、真实输入证据和可见终端验收。
- 排除：外部 MCP 包内部实现、macOS TCC、Swift helper、macOS `pbcopy/pbpaste`、Windows/macOS 系统差异导致的不可比行为。
- 当前矩阵基线：执行前以 `claudecode_alignment_matrix` 为准，已知上一轮审计为 11/14 aligned，CA07/CA13/CA14 为 partial，CA14 的 visible terminal gate 为 false。
- 优先级：先补真实系统剪贴板和权限语义测试，再补矩阵证据和真实可见终端验收。

## 2026-06-17 Tool Surface ClaudeCode Parity Context

- 用户要求先对齐两项工具暴露差异：`tool_search` 首轮常驻，以及 `bash` 在代码开发模式像 `read/edit/write` 一样首轮直接暴露给大模型。
- 当前设计调整后，普通代码开发模式首轮模型工具面应为 `read / write / edit / bash / tool_search`。
- Computer Use 操作/debug 模式仍应隐藏顶层文件和 shell 工具，继续只暴露 `mcp__computer-use__*` 原子桌面工具，避免真实桌面任务被 bash 或文件工具抢走。

## 2026-06-17 ToolToAPISchema Naming Context

- 用户要求按 ClaudeCode 的 `toolToAPISchema` 名字给 OpenHarness 增加更清楚的工具 schema 总入口，方便代码小白记忆和对照。
- 本次设计边界：只增加清楚命名包装入口，不改变 `AgentTool.to_model_schema()` 的实际 schema 结构，也不改变 `current_tool_pool`、`should_defer`、`always_load` 和 `tool_search` 动态加载行为。
- 当前对应关系：ClaudeCode 的 `toolToAPISchema()` 对应 OpenHarness 新增的 `learning_agent.tools.types.toolToAPISchema()`；OpenHarness 的 `available_tool_schemas()` 已改为通过该入口生成 OpenAI-compatible 工具 schema。

## 2026-06-17 FilteredTools Naming Context

- 用户要求把 OpenHarness 的 `current_tool_pool()` 改成和 ClaudeCode 更容易对照的 `filteredTools()` 名字，方便代码小白理解“先过滤当前可用工具，再生成 schema，再发给模型”的链路。
- 本次设计边界：新增 `filteredTools()` 作为主记忆入口，不删除 `current_tool_pool()`；旧入口保留为兼容包装并委托 `filteredTools()`，避免项目里已有调用断裂。
- 当前对应关系：ClaudeCode 的 `filteredTools` 对应 OpenHarness 新增的 `learning_agent.tools.pool.filteredTools()` 和 `learning_agent.tools.catalog_runtime.filteredTools()`。
- 当前 OpenHarness schema 链路可读作：完整工具目录 `tool_catalog()` → 当前可见工具过滤 `filteredTools()` → 工具 schema 转换 `toolToAPISchema()` → `available_tool_schemas()` → OpenAI adapter 的 `tools` 参数。

## 2026-06-17 OpenAI defer_loading Context

- OpenAI 官方文档已确认：现代 OpenAI Responses API 支持 `tool_search`，并能在 namespace 里的 function tool 上使用 `defer_loading: true`。
- 当前 OpenHarness 仍主要走 Chat Completions 风格的 function tools 结构：`{"type": "function", "function": {...}}`，不是 Responses API 的 namespace + `{"type": "tool_search"}` 结构。
- 因此当前 OpenHarness 不把 `defer_loading` 字段直接塞进现有 Chat Completions schema，不算简单“不合理”；它是在避免把 Responses API 专属/新式结构混进旧式工具发送链路。
- 但若目标是继续对齐 ClaudeCode 和 OpenAI 最新工具搜索能力，后续值得单独做一条 Responses API tool_search/namespace 链路，而不是在现有 Chat Completions `tools=tools` 上直接加字段。

## 2026-06-17 FilteredTools Only Context

- 用户进一步指出：既然目标是让代码小白更清楚，保留 `current_tool_pool()` 旧名字反而会造成两个入口的理解负担。
- 已按用户建议先创建书面迁移记录：`docs/superpowers/plans/2026-06-17-current-tool-pool-removal-record.md`，记录旧调用审计、替换范围、排除历史备份和成功标准。
- 当前 active 生产链路已只保留 `filteredTools()`：`learning_agent.tools.pool.filteredTools()` 和 `learning_agent.tools.catalog_runtime.filteredTools()`。
- `current_tool_pool()` 不再作为 active 生产函数公开；历史学习备份 `learning_agent/test/**` 和归档 `agent_memory/archive/**` 保留旧文本作为历史证据，不视为当前调用链。
## 2026-06-17 OAuth Native Tools ClaudeCode Parity Blueprint

- 本轮只制定书面蓝图，没有修改 OpenHarness 运行代码。
- 蓝图文件：`docs/superpowers/plans/2026-06-17-openharness-oauth-native-tools-claudecode-parity.md`。
- 蓝图依据：官方 Responses API tool_search/namespace/defer_loading 文档，以及本机 ChatGPT OAuth 后端对 native function、hosted tool_search、client tool_search 的真实探测结果。
- 后续执行边界：排除外部 MCP 包内部实现，排除 macOS TCC/Swift helper/pbcopy/pbpaste 与 Windows/macOS 系统差异；聚焦 OpenHarness OAuth 模型适配链路、Responses 原生 output 解析、工具执行回填和真实可见终端验收。
## OAuth Native Responses Tools Parity - 2026-06-17

- 目标：让 OpenHarness OAuth 模型对齐 ClaudeCode/Codex 风格的原生 Responses tools 链路。
- 官方格式：顶层 `tools` 支持 function、namespace、tool_search；`defer_loading: true` 放在 namespace 内部 function 上。
- 本机实测：`https://chatgpt.com/backend-api/codex/responses` 在 ChatGPT OAuth token 下接受 native function、hosted tool_search、client tool_search。
- 当前缺口：OpenHarness 仍用 `text.format=json_schema` + prompt 内工具清单，让模型输出自定义 JSON，而不是原生 Responses output items。
- 边界：不处理外部 MCP 包内部实现，不处理 macOS TCC/Swift helper/pbcopy/pbpaste，不处理 API key 路线默认切换。

## OAuth Native Task 9 Compatibility Context - 2026-06-18

- `LearningAgent` 现在保留 `_tool_catalog()`、`_available_tool_schemas()`、`_available_responses_tool_schemas()`、`_tool_schema_names()` 这几个旧私有入口，目的是兼容旧测试和旧调用方；真实工具过滤、schema 生成和命名提取仍统一委托 `learning_agent.tools.catalog_runtime`。
- 这不是恢复 `current_tool_pool()` 公开旧名字；active 生产链路仍以 `filteredTools()` 作为当前可用工具过滤入口。
- `tool_search` 当前按用户要求属于首轮/后续常驻工具，测试断言应检查它继续存在，而不是检查它隐藏。

## 2026-06-18 OAuth Native ClaudeCode Streaming Context

- 用户明确要求停止盲目修 bug，先参考 `D:\ClaudeCode-main\ClaudeCode-main` 的 CodeGraph，再修 OpenHarness。
- ClaudeCode 参考结论：它保留结构化 assistant tool_use/tool_result 对，并在流式输出中使用 accumulator 合并 start/delta/done，不会只保存一个空的 in-progress message 占位。
- OpenHarness 本轮定位到两个协议层根因：`store:false` 续轮未请求/回传 `reasoning.encrypted_content`，以及 SSE parser 在看到空 `message in_progress` output item 后优先返回 output 数组，吞掉后续 `output_text.done` 最终文本。
- 已按 ClaudeCode/Codex 风格修正：native 续轮会把 reasoning/tool_search/function_call 原生 item 与 function_call_output 一起回传；SSE parser 会把 `output_text.done` 合并进 message item；native 续轮 prompt 不再 dump 整段 `messages` JSON。
- 当前 OAuth native tools 和 OAuth native Computer Use 两个真实可见终端场景已经通过，但 native 模式仍保持显式开关 `CODEX_OAUTH_NATIVE_TOOLS=1`，是否默认开启应由后续产品决策单独确认。

## 2026-06-18 Windows Computer Use Permission UI Context

- 用户要求为值得对齐的第 1 项“权限 UI 体验”制定详细蓝图，目标是防止后续长任务跑偏。
- 当前 OpenHarness 已有 `request_access`、`list_granted_applications`、`apps`、`grantFlags` 和 `sentinelWarnings` 基础，但用户可见提示仍偏 JSON 化，不等同于 ClaudeCode 的清晰授权体验。
- 对齐方向不是复制 ClaudeCode 的 React/Ink 或 macOS TCC，而是在 Windows 真实终端中提供等价体验：显示目标应用、危险权限、sentinel 风险、申请原因、允许/拒绝选择和会话审计。
- 本项是 P0，因为 Computer Use 会真实操作用户电脑；没有清楚权限 UI，即使底层动作能执行，也不能算成熟 agent 能力。
- 正式蓝图文件：`docs/superpowers/plans/2026-06-18-computer-use-windows-permission-ui-claudecode-parity.md`。

## 2026-06-18 Windows Computer Use Permission UI Implementation Context

- 已按蓝图开始执行 P0 权限 UI 体验对齐，范围只覆盖 Windows 终端权限体验、结构化权限决策、grant flags、sentinel 风险提示、授权审计和状态可观测字段，不处理外部 MCP 包、macOS TCC、Swift helper 或底层执行链重构。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py` 已从 JSON 化提示升级为终端面板：显示目标应用、进程/窗口摘要、申请原因、grant flags、sentinel 风险、中文安全建议和 y/n 决策。
- 新增 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_decision.py`，统一把旧 bool 回调和新结构化 dict 回调归一化为 `decision/source/promptVersion/timestampUtc/grantFlags`，并把无回调场景改为默认拒绝。
- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py` 已把 `request_access` 返回扩展为可审计 payload：保留旧字段，同时新增 `decision`、`source`、`promptVersion`、`timestampUtc`、`permissionDecision`、`permissionDecisions` 和 `lastPermissionDecision`。
- Windows runtime 状态层已补齐 `permission_prompt_version`、`last_permission_decision` 和 `denied_decision_count`，`/computer status` 能显示当前权限 UI 版本和最近决策，避免用户只看到底层安全策略。
- 本轮学习备份位置：`learning_agent/test/20260618_windows_permission_ui_claudecode_parity/`。
- 真实可见终端验收已通过：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实终端中输入 `/computer use --full`、安全 `request_access + list_granted_applications` prompt、`/computer status` 和最终 marker prompt；run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_permission_ui_visible_terminal-20260618_145426\result.json`。
- 该 run 证明：`permission_required` 与 `permission_answered` 都出现，权限面板正文包含 `[Computer Use 权限请求]`、Notepad、grant flags、安全建议和 y/n 选择；状态面板包含 `permission_prompt_version=windows-permission-ui-v1`；最终回答为 `COMPUTER_USE_PERMISSION_UI_VISIBLE_TERMINAL_OK`。

## 2026-06-18 Cua Driver Windows Computer Use 借鉴上下文
- Cua Driver 借鉴实现范围：元素索引缓存、UniversalRealObservationFrameRuntime 缓存输出、坐标合同、UIA Pattern 语义分发、UIPI 完整性诊断、MCP v2 element_index 语义动作短路、最终矩阵和可见终端 scenario。
- 明确边界：ClaudeCode 隐藏外部包内部行为不做逐行对齐；macOS 与 Windows 平台差异继续按等价能力处理。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收上下文
- 当前 production acceptance 场景为 learning_agent/acceptance_controller/scenarios/agent_capability_cua_driver_real_windows_production_visible_terminal.json。
- 场景意图：不只验证矩阵文件存在，而是在真实可见终端里让 agent 调用 bash 执行 Cua Driver 借鉴矩阵和受控 Notepad 真实编辑命令，确认 OpenHarness 的 Windows Computer Use 链路能触达真实桌面对象并保存受控项目证据。
- 成功 run 为 learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_172608/result.json。
- 该 run 的关键边界：仅允许受控 Notepad 测试目标和项目证据文件；不允许浏览器、登录页、支付页、系统设置、注册表、安装器、密码管理器或用户私人文档。
- 当前生产化验收标记为 CUA_DRIVER_WINDOWS_PRODUCTION_ACCEPTANCE_OK；同时要求 CUA_DRIVER_WINDOWS_BORROWING_OK、PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。
- 最终复验 run 为 learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_173128/result.json；后续引用本次生产化验收时优先引用该最新 run。

## 2026-06-18 Windows Computer Use 生产验收矩阵蓝图上下文
- 当前蓝图文件：docs/superpowers/plans/2026-06-18-windows-computer-use-production-acceptance-matrix.md。
- 蓝图的核心定位：不是继续新增底层 Computer Use 功能，而是把 acceptance controller 已经证明可行的真实可见终端能力，升级成每次发布前可运行的 Windows Computer Use 出厂检测线。
- 后续执行时优先使用 superpowers:subagent-driven-development 或 superpowers:executing-plans，按蓝图逐项执行，不要跳过 Task 1 的 CLI token 审计。
- 特别注意：现有 Phase148C 多个场景仍包含 real_gui_backing=true；执行蓝图时必须先用真实 controlled CLI 输出确认是否应保留该 token。

## 2026-06-18 Windows Computer Use 生产验收矩阵执行上下文
- Task 1 的真实 CLI 审计结论：Notepad、Calculator、local_browser 不输出 real_gui_backing=true；Explorer、multi_app_transfer、failure_recovery、long_task_resume 输出 real_gui_backing=true。
- Calculator 受控 driver 已切到 UIA InvokePattern 优先路径，成功证据 token 是 uia_invoke_sequence_used=true 和 observed_result_matches_expected=true。
- 后续矩阵 manifest 与场景断言必须按每条 CLI 当前真实输出建模，不允许为了统一格式强行要求某个模块没有输出的 token。

## 2026-06-18 Windows Computer Use 生产验收矩阵完成上下文
- 当前 Windows Computer Use 生产验收矩阵入口是 learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1。
- 当前生产矩阵 manifest 是 learning_agent/acceptance_controller/windows_computer_use_production_matrix.json，包含 10 条受控真实可见终端场景。
- 最新通过矩阵结果是 learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-20260618_183954/matrix_result.json，结果为 passed=true、scenario_count=10、passed_count=10、failed_count=0。
- 后续声明 Windows Computer Use 生产验收通过时，应优先引用该矩阵 result，而不是只引用单条 Cua Driver Notepad 验收。
- runner 文件必须保留 UTF-8 BOM，因为 Windows PowerShell 5.1 直接 -File 执行带中文注释的无 BOM 脚本会解析失败。
- 连续真实 GUI 验收需要保留场景前后短等待，避免 Windows Terminal、Explorer、Calculator 等窗口刚关闭或刚启动时造成焦点漂移。

## 2026-06-18 OAuth Native Tools 默认策略
- 真实 OAuth 终端入口 learning_agent/start_oauth_agent.ps1 现在默认开启 CODEX_OAUTH_NATIVE_TOOLS=1，目标是让 start_oauth_agent.bat 默认使用 Responses 顶层 tools、原生 function_call、hosted tool_search 和原生 function_call_output 回填链路。
- 该策略只作用于真实 OAuth 启动脚本，不改变 CodexOAuthChatModel 类的全局默认值；测试、旧调用方和非 OAuth provider 仍可按原有方式运行。
- 若后端 native tools 协议出现临时兼容问题，用户可在启动前显式设置 CODEX_OAUTH_NATIVE_TOOLS=0 或其它非空关闭值，脚本不会覆盖该设置。

## 2026-06-18 Computer Use v2 目录边界
- 当前 Computer Use 主代码目录是 learning_agent/computer_use_mcp_v2；learning_agent/computer_use 旧目录已删除，不应作为当前 agent 能力来源。
- 元素索引缓存、坐标/目标身份合同、UIA Pattern 语义分发均位于 learning_agent/computer_use_mcp_v2/windows_runtime。
- Cua Driver 借鉴矩阵和 UIPI 完整性诊断合同也已迁入 learning_agent/computer_use_mcp_v2/windows_runtime，仅作为验收/诊断支持，不表示旧目录仍存在。
- 后续新增或修复 Windows Computer Use 功能时，禁止新增 learning_agent.computer_use.* 或 computer_use.* 导入；应使用 learning_agent.computer_use_mcp_v2.windows_runtime.*。
- 该边界已由真实可见终端 acceptance controller 场景验证通过：agent_capability_computer_use_mcp_v2_legacy_folder_removed_visible_terminal-20260618_202959。

## 2026-06-25 Desktop GUI Shell V2

当前长任务目标是逐项完成 `docs/superpowers/plans/2026-06-25-codex-style-desktop-gui-shell-v2.md`。执行顺序按蓝图分为 `V2-Core`、`V2-Trust`、`V2-Product`，先建立 golden traces 和可回归 UI 状态基线，再推进真实桥接、安全、诊断、搜索、插件入口和最终可见 GUI 验收。

Task Core-0 的边界是只建立 20 条 `GT-001` 到 `GT-020` golden traces、后端 fixture 合同测试、前端 fixture 消费测试和 prompt matrix 记录。它不代表 20 个场景都已经在可见 GUI 中跑通；可见 GUI 执行会在后续 V2-Core、V2-Trust、V2-Product 任务中逐项完成。

Task 3 已把 GUI run 默认路径切到 deterministic fake streaming adapter。真实 agent/harness 接线当前只做 CodeGraph 映射，不在 V2-Core 启用；未来 V2-Trust 应从 `LearningAgent.run(...) -> run_agent_with_harness_session(...) -> agent.run_events(...)` 接入，并通过 `event_callback`、`StatusEventStore`、`stop_event` 和 GUI permission handshake 形成真实 adapter。

Task 4 已把 V2 adapter 事件接入前端主线程状态：`eventReducer.ts` 是唯一事件翻译边界，`threadStore.ts` 负责 `message_delta` 追加、`message_completed` 终态、`safety_refusal` 拒绝消息和 `turn_failed` 错误消息；`ThreadView.tsx` 只消费 `ThreadMessage.kind/status/text` 渲染，不再自行理解后端事件。

Task 5 已把 Composer 输入规则抽成可测试纯函数：普通 Enter 发送，Shift+Enter 保持原生换行，中文多行和标点不做 trim/改写；`submitComposerDraft()` 只有在 `onSubmit` 成功后才返回清空草稿，运行中/提交中通过按钮状态说明不能发送。

Task 6 已把 GUI 权限流升级到 V2：`gui_permissions.py` 是权限请求字段清洗、脱敏、动作摘要和决策规范化的唯一后端 helper；`gui_bridge.py` 继续拥有权限事实源，但不再手写 payload 字段。前端权限 UI 的数据流是 `StatusEventStore -> latestPermissionEvent() -> permissionFromEvent() -> PermissionBanner/PermissionDialog`，按钮提交期间由 `pendingPermissionDecisionId` 禁用，后端确认后再通过 `answeredPermissionIds` 隐藏弹窗。

Task 7 已把工具轨迹收敛到前端纯 reducer 边界：`reduceGuiEventToTraceRows()` 负责从 GUI events 生成 `TraceToolRow`，并在这里做参数预览、结果摘要、错误码和敏感字段脱敏。`TracePanel.tsx` 只消费 trace rows 渲染工具轨迹，不直接理解后端原始 payload。右侧 `StatusInspector.tsx` 当前拥有五个页签：状态、工具、浏览器、设置、诊断；后续 Task 11 诊断页应复用这个页签框架继续扩展，而不是再新增第二个右侧检查器。

Task 9 已建立 V2 运行时面板边界：`learning_agent/app/gui_bridge.py` 中的 `build_gui_runtime_panels_payload(workspace)` 是 `/v2/gui/runtime/panels` 的唯一 payload 生成点，输出 `browser/computer_use/permissions/status_degraded/safe_error`。浏览器状态继续从 `build_status_snapshot(workspace)` 取事实，失败时只返回安全文案，不泄露本机路径。Computer Use 面板当前以安全摘要为主，锁和急停是 GUI 层可显示字段，真实 lock owner/abort runtime 后续接入时必须沿用该 payload 形状。

前端 Task 9 的数据流是：`createGuiClient().runtimePanels()` 拉取 `/v2/gui/runtime/panels`，`AppShell.tsx` 保存到 `runtimePanels` state，`StatusInspector.tsx` 在“浏览器”页签中把 `runtimePanels.browser` 传给 `BrowserPanel`，把 `runtimePanels.computer_use` 和 `runtimePanels.permissions` 传给 `ComputerUsePanel`。后续不要再新增独立右侧栏；Task 11 诊断导出应继续扩展 `StatusInspector` 的“诊断”页签。
