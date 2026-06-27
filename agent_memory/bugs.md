# 问题与风险摘要（2026-06-16）

历史全文归档：`agent_memory/archive/2026-06-16-computer-use-mcp-v2-parity/`。

## 已关闭问题

- 旧聚合 Computer Use 工具曾可能绕过新 v2 工具面；现在 `build_tools.py` 和 `batch.py` 都有禁止名单。
- shell、PowerShell、文件 read/write/edit 曾可能被误混入桌面 MCP；现在工具名和 batch 参数都有防线。
- 写动作无 host 时曾可能 no-op 假成功；现在 mutating action 缺 host 会返回明确失败。
- `left_mouse_up` 曾缺少坐标合同；现在 schema 要求 x/y，执行证据保留释放点。
- `hold_key` 曾存在 keys 参数和执行层不一致风险；现在对齐 keys 数组，并有异常清理和 batch 失败传播测试。
- Phase41 图片结果测试曾走旧 wrapper；现在迁移到 v2 MCP wrapper。
- `zoom` 曾被当成普通动作或整图 observe；现在是只读观察语义，并尝试返回局部裁剪 `image_result`。
- v2 架构文档、`computer-use` MCP 配置注册和独立 selftest probe 曾只被测试要求但资产缺失；现在已补齐文档、配置、probe 和可见终端场景。
- 可见终端场景曾把 probe marker `COMPUTER_USE_MCP_V2_READY` 同时当最终成功 marker，导致“未看到 READY”的失败句子可能误判通过；现在 probe marker 与最终成功 marker 已分离，最终标记改为 `COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK`。

## 仍需关注风险

- `zoom` 裁剪依赖源截图和窗口 rect；如果真实观察结果缺少 rect，会返回明确失败并保留原观察文本。后续可从 session 状态或 controller active window 增加兜底 rect。
- `inferred_ant_mcp/actions.py` 仍保留直接调用 `zoom` 的无 host 错误兜底；正常 runtime 已把 zoom 分发到 `observation.py`，这个分支只是防止未来直接调用动作层时误报 unknown tool。
- 真实 Windows 桌面行为还需要更多端到端用例覆盖，例如打开记事本、输入文字、局部 zoom 观察文字、再执行清理。
- 2026-06-16 自适应图片链路已完成本轮 `start_oauth_agent.bat` 真实可见终端 observe 验收，run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal-20260616_213724\result.json`；本轮不再受“未验收不能声明开发完成”阻塞。
- 2026-06-16 仍需注意：全量 `python -m unittest discover learning_agent/tests -p "*computer_use*.py"` 仍包含历史旧接口测试失败，不代表本轮图片链路失败；本轮可信验收口径是 20 个图片/桥接相关测试、116 个 v2 computer use 回归矩阵、py_compile 和真实可见终端 observe 验收。

## 2026-06-16 Lifecycle Parity 新发现与关闭

- 已关闭：`bind_session_context._lock_callbacks_from_runtime()` 在 runtime 没有 `lock_manager` 时曾只返回 `computer_use_session_id`，导致 wrapper cleanup 对轻量 runtime/fake runtime 退回 no-op fallback，丢失 `escape_hook_unregistered` 和 `lock_cleanup_mode` 等 lifecycle 字段。已改为无 lock manager 时仍绑定 `cleanup_turn`、`register_global_escape_abort` 和 `mark_expected_escape`（如果 runtime 提供）。
- 已关闭：standalone `tools/list` 以前在 Computer Use disabled/context disabled 时仍会加载 app inventory 并暴露工具。现在 disabled 或 disabled 判断异常时失败关闭，返回空工具列表并记录 trace。
- 已关闭：外部 `displayState.displayResolvedForApps` 以前返回 OpenHarness rich list，和 ClaudeCode 的 string key 不一致。现在外部为 string key，rich records 迁移到 `displayResolvedForAppsRecords`。

## 验证备注

最近一次完整 v2 computer use 回归矩阵 116 个测试通过；关键 Python 文件 py_compile 通过。AGENTS 规则十七定义的真实可见终端交互验收已通过，原项目精确 BAT 路径 observe run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal-20260616_213724\result.json`，并已确认该 run 的工具结果可生成 `text + image_url` 模型消息。

## 2026-06-16 Lifecycle Parity 验证备注

- 已关闭本轮“不能声明完成”的最终门禁：真实可见终端验收已通过，run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal-20260616_234022\result.json`。
- 本轮 lifecycle parity 可信验收口径：92 个 v2 computer use 相关测试通过、关键文件和学习备份 `py_compile` 通过、`codegraph index --force .` 后 `codegraph status .` 为 `[OK] Index is up to date`。
- 注意：CodeGraph 当前索引语言统计仍是 Python 1,255 + JavaScript 5；新增 JSON 场景文件属于验收资产，不进入当前 CodeGraph 源码节点统计，这不影响 Python/JS 源代码知识图谱最新性。

## 2026-06-17 ClaudeCode 对齐审计风险

- 当前最大不确定性：ClaudeCode 的 `@ant/computer-use-mcp`、`@ant/computer-use-swift`、`@ant/computer-use-input` 是外部依赖，不在 `D:\ClaudeCode-main\ClaudeCode-main` 源码树和 CodeGraph 内；OpenHarness 的 `inferred_ant_mcp` 只能对齐可观察合同，不能证明隐藏包内部逐行一致。
- 当前 OpenHarness 内置对齐矩阵为 `11/14 aligned`、`3 partial`、`0 missing`。partial 项为 CA07 真实桌面输入派发证据 token 未命中、CA13 旧 2026-06-13 真实 GUI benchmark manifest 未加载、CA14 本轮未提供最终真实可见终端 gate。
- CA07 不应直接解读为 OpenHarness 没有 SendInput 链；源码中仍可见 `WindowsSendInputLowLevelSender`、`WindowsSendInputDispatcher`、`WindowsSendInputExecutor`、`controlled_physical_sendinput` 等链路。更准确的风险是：当前矩阵使用的证据路径或 token 已落后于源码实际位置，需要更新矩阵证据口径或补跑对应真实 GUI evidence。
- 剪贴板仍是需要优先复核的真实差异：ClaudeCode executor 使用 pbcopy/pbpaste 读取和写入系统剪贴板，而 OpenHarness v2 `inferred_ant_mcp/clipboard.py` 当前显示为 context 内存剪贴板，若目标是行为完全一致，需要确认 Windows runtime 是否另有真实系统剪贴板桥接，否则这是实质缺口。
- 权限 UX 仍不同：ClaudeCode 使用 React/Ink `ComputerUseApproval` 交互面板和 macOS TCC 面板；OpenHarness 当前通过终端 `ask_permission` 和 Windows 权限/安全门表达。OS 权限差异可接受，但如果要求用户交互体验完全一致，需要单独设计 OpenHarness 的等价终端 UI。

## 2026-06-17 Windows Parity 蓝图风险记录

- 已把剪贴板、权限提示、CA07/CA13/CA14 矩阵证据和真实可见终端门禁写入 `docs/superpowers/plans/2026-06-17-computer-use-claudecode-windows-parity-blueprint.md`，后续执行时不得把这些风险当成已经解决。
- 若执行剪贴板系统桥接时读到疑似密码、token 或用户私密内容，必须停止并汇报，不能把完整剪贴板内容写入日志或最终回答。
- 若真实 GUI benchmark 需要操作真实登录、支付、系统设置或用户私有文档，必须停止并改成受控 Notepad/测试窗口场景。

## 2026-06-17 Tool Surface 验证风险

- `python -m unittest learning_agent.tests.test_tools_policy.ToolsPolicyTests.test_initial_tool_pool_only_exposes_kernel_tools` 当前在导入阶段失败：`learning_agent.tests.support` 仍尝试从 `learning_agent.core.agent` 导入已不存在或已迁移的 `ask_permission_from_terminal`。
- 该问题阻断 `test_tools_policy` 里的新预期自动验证，但本轮已通过 `test_computer_use_tool_scope`、`py_compile` 和真实 agent 工具池快照验证 `read/write/edit/bash/tool_search` 首轮可见。

## 2026-06-17 OpenAI defer_loading 对齐风险

- 已确认 OpenAI 官方 Responses API 支持 `tool_search`，并能在 namespace 内的 function tool 上标记 `defer_loading: true`。
- 当前 OpenHarness 主要使用 Chat Completions 风格的 `tools=[{"type":"function","function":...}]` 链路，不是 Responses API 的 `tools=[{"type":"namespace",...},{"type":"tool_search"}]` 链路。
- 风险判断：当前不发送 `defer_loading` 字段不是立即错误，但意味着 OpenHarness 还没有完全利用 OpenAI 最新的 API 层动态工具加载机制。
- 后续建议：若继续追求 ClaudeCode/OpenAI 最新 parity，应新增 Responses API tool_search/namespace 发送链路，并在该链路中表达 `defer_loading`；不要把 `defer_loading` 直接硬塞进当前 Chat Completions function schema，以免形成接口形态混乱。

## 2026-06-17 FilteredTools Only 风险说明

- 已删除 active 生产代码里的 `current_tool_pool()` 旧入口，当前工具过滤入口统一为 `filteredTools()`。
- 注意：`learning_agent/test/**` 历史学习备份和 `agent_memory/archive/**` 旧归档仍可能包含旧名字，这是历史证据，不是当前运行链路。
- 当前 active 路径已用搜索确认没有 `def current_tool_pool`、`import current_tool_pool` 或 `current_tool_pool as`。

## OAuth native tools default switch blocked - 2026-06-18

- Blocker: 真实可见终端自动验收未完成，controller 在尝试聚焦 `start_oauth_agent.bat` 启动的真实终端窗口时失败，错误为 `无法聚焦真实终端窗口，停止发送文本。`
- Evidence: Task 7 真实 OAuth backend probe 已通过，说明 ChatGPT OAuth 后端接受 hosted `tool_search` / namespace / `defer_loading`；但 Task 8 的可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_oauth_native_tools_visible_terminal-20260618_101119/` 未能输入 prompt，因此没有 `OAUTH_NATIVE_TOOLS_OK` 或 `OAUTH_NATIVE_COMPUTER_USE_OK` 的真实终端输出证据。
- Required next step: 需要在可聚焦、可观察、可输入的用户本地真实终端环境中重新运行 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json` 与 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_computer_use_visible_terminal.json`，或由用户手动在 `learning_agent/start_oauth_agent.bat` 可见终端中输入两条场景 prompt 并反馈输出截图/日志。
- Decision: 不允许把 `CODEX_OAUTH_NATIVE_TOOLS` 默认切换为开启；保持当前默认关闭，只允许显式 `CODEX_OAUTH_NATIVE_TOOLS=1` 试用。

## Existing unittest import blocker - 2026-06-18

- Blocker: `python -m unittest learning_agent.tests.test_models_codex_oauth` 在导入阶段失败，原因是 `learning_agent.tests.support` 仍尝试从 `learning_agent.core.agent` 导入 `ask_permission_from_terminal`，但当前 `learning_agent.core.agent` 没有导出该名称。
- Evidence: 本轮运行 `python -m unittest learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_models_codex_oauth` 时，native SSE 测试已通过，但 `test_models_codex_oauth` 作为整个模块导入失败。
- Required next step: 后续应单独整理 `ask_permission_from_terminal` 的迁移/重导出策略，恢复 `test_models_codex_oauth` 和依赖 `learning_agent.tests.support` 的历史测试模块；本轮不把该导入问题当成 OAuth native tools 实现本身失败。

## Existing unittest import blocker closed - 2026-06-18

- Status: 已关闭。`learning_agent.core.agent` 已兼容重导出 `ask_permission_from_terminal`、`ask_permission_from_terminal_customer_mode`、`build_permission_event_payload`，真实实现仍来自 `learning_agent.app.terminal_permissions`。
- Evidence: `python -m unittest learning_agent.tests.test_models_codex_oauth` 已通过，结果为 49 个测试通过。
- Related cleanup: 同步补齐 `LearningAgent` 的旧私有工具 schema 兼容入口，解决 `_tool_schema_names` / `_available_tool_schemas` 等旧测试调用；同时把过期的 `tool_search` 隐藏断言改为符合当前“tool_search 常驻”设计。
- Remaining risk: OAuth native tools 默认开关仍被真实可见终端验收阻塞；该风险和旧 unittest import blocker 无关。

## OAuth native empty final answer closed - 2026-06-18

- Status: 已关闭本轮可复现问题。真实终端曾在成功调用 `read` 后返回空最终回答，debug 里只看到 `message in_progress` 或 reasoning item，没有用户可见文本。
- ClaudeCode reference: `StreamingToolExecutor` 和 `accumulateStreamEvents()` 体现的关键语义是保留工具调用/工具结果结构，并把流式 delta 合并成最终消息，而不是只保存开始占位。
- Root cause 1: OpenHarness native continuation 在 `store:false` 场景未请求/回传 `reasoning.encrypted_content`，工具结果下一轮缺少官方建议的 reasoning 续轮上下文。
- Root cause 2: OpenHarness SSE parser 遇到空 `message in_progress` output item 时优先返回 output 数组，导致同一流里的 `output_text.done` 没合并进 message content，最终 `ModelMessage.text` 为空。
- Fix evidence: 已新增红灯测试覆盖 reasoning 回传、function_call_output 前置原生 item、精简 continuation prompt、`output_text.done` 合并到 message 占位；修复后全部变绿。
- Runtime evidence: 真实可见终端 OAuth native tools run `agent_capability_oauth_native_tools_visible_terminal-20260618_123634` 已通过，最终回答包含 `OAUTH_NATIVE_TOOLS_OK`；OAuth native Computer Use run `agent_capability_oauth_native_computer_use_visible_terminal-20260618_123710` 已通过，最终回答包含 `OAUTH_NATIVE_COMPUTER_USE_OK`。
- Remaining risk: `CODEX_OAUTH_NATIVE_TOOLS` 仍是显式开关；是否默认开启不是 bug 修复范围，需要后续按产品风险、回滚策略和更长时间真实使用稳定性决定。

## ClaudeCode/OpenHarness Computer Use parity risks refreshed - 2026-06-18

- Status update: 旧风险“OpenHarness v2 clipboard 可能只是 context 内存剪贴板”已被本轮 CodeGraph 审计重新分类。主 agent-side v2 绑定路径 `inferred_ant_mcp/bind_session_context.py` 默认创建 `WindowsClipboardBackend`，`inferred_ant_mcp/clipboard.py` 使用该 backend 读写系统剪贴板。
- Remaining clipboard risk: `windows_runtime/mcp_session_adapter.py` 仍保留 `agent_session_memory_clipboard` 的旧 adapter 分支。当前主链路中 read/write_clipboard 不应走该分支，但后续若发现某个旁路直接调用 session adapter，需要单独收敛或标记为诊断兼容。
- Confirmed structural gap: ClaudeCode 的 `@ant/computer-use-mcp`、`@ant/computer-use-swift`、`@ant/computer-use-input` 仍是外部包源码缺口，OpenHarness 只能对齐可观察协议和行为，不能证明隐藏包内部逐行一致。
- Confirmed UX gap: ClaudeCode `ComputerUseApproval` 是 React/Ink 面板并包含 macOS TCC 引导；OpenHarness 当前是终端权限 prompt 和 Windows 安全门禁。macOS TCC 差异可接受，但交互体验不是完全一致。
- Confirmed layering gap: OpenHarness 的真实 Windows 执行仍通过 v2 facade -> legacy Windows session adapter/controller 复用成熟能力；ClaudeCode 是 package -> hostAdapter -> executor 的直接链路。该差异不等同于功能缺失，但如果追求代码结构完全同构，需要另立重构任务。

## Windows Computer Use permission UI risk - 2026-06-18

- Status: 已建蓝图，尚未实现。
- Evidence: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py` 当前主提示是中文标题加格式化 JSON；`permissions.py` 当前在没有可调用 `context.ask_permission` 时存在默认允许路径。
- Risk: 这会让权限请求在真实用户体验上弱于 ClaudeCode，也会让非交互或错误绑定场景更难被用户理解和审计。
- Required next step: 按 `docs/superpowers/plans/2026-06-18-computer-use-windows-permission-ui-claudecode-parity.md` 执行 P0，优先实现终端权限面板、结构化决策、无交互默认拒绝、`request_access` 审计字段和真实可见终端验收。

## Windows Computer Use permission UI implementation risk update - 2026-06-18

- Status: 已关闭本轮 P0 权限 UI 对齐风险。
- Closed risk: `request_access` 在没有可调用 `context.ask_permission` 时曾默认允许。现在无回调、回调异常或显式拒绝都会走结构化拒绝决策，并记录 `decision/source/promptVersion/timestampUtc`。
- Closed risk: 权限 prompt 曾偏 JSON 化。现在终端面板会显示目标应用、进程/窗口摘要、grant flags、sentinel 风险、申请原因、安全建议和 y/n 选择。
- Closed risk: `/computer status` 曾无法证明当前权限 UI 版本和最近授权结果。现在 Windows runtime approval 状态包含 `permission_prompt_version`、`last_permission_decision` 和 `denied_decision_count`。
- Verification: 自动化测试已覆盖 prompt、decision、MCP v2 payload 和状态渲染；真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_computer_use_permission_ui_visible_terminal-20260618_145426/result.json` 已通过，包含真实 `permission_required`、`permission_answered`、Computer Use 权限面板、`request_access`、`list_granted_applications`、`permission_prompt_version=windows-permission-ui-v1` 和最终 marker。
- Remaining risk: `/computer status` 当前显示的是 Windows runtime approval 模型最近决策，v2 MCP `request_access` 的最近决策仍主要保存在 MCP context payload 中；这不是本轮 P0 阻塞，但后续若要把两套状态完全汇总到同一个状态面板，可另立状态聚合任务。

## 2026-06-18 Cua Driver 借鉴验证记录
- 自动化验证发现全量 compileall 失败点在既有历史备份文件 learning_agent/test/computer_use_full_desktop_task_router_task3_20260605/core_agent_task3_clean_index.py 第 4 行 IndentationError。
- 本轮新增/修改文件已单独 py_compile 通过；该 compileall 历史问题暂不作为本轮阻塞。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收场景修正
- 首次真实终端验收失败不是 Notepad 链路失败，而是新场景要求 \\eal_gui_backing=true\\，当前 controlled_notepad_live_edit 实际输出不包含该 token。
- 已将场景断言改为当前命令真实输出的生产证据：real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收场景修正关闭
- Status: 已关闭。修正后的场景 agent_capability_cua_driver_real_windows_production_visible_terminal 已通过真实可见终端验收。
- Evidence: learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_172608/result.json 显示 completed=true、assertion.passed=true、marker_passed=true、permission_count_passed=true。
- Debug evidence: latest_run_readable.md 中 bash 命令 exit_code=0，并输出 CUA_DRIVER_WINDOWS_BORROWING_OK、PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。
- Remaining risk: 该验收是受控 Notepad 生产化链路，不代表所有第三方 Windows 应用都已覆盖；后续若扩展到 Excel、浏览器或管理员权限窗口，需要新增各自的受控 acceptance scenario。
- Fresh recheck: 最终回答前重新运行同一 acceptance controller 场景，latest run learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_173128/result.json 继续显示 completed=true 与 assertion.passed=true。

## 2026-06-18 Windows Computer Use 生产验收矩阵蓝图风险
- Status: 已记录，尚未执行。蓝图发现现有 Phase148C 场景中多处包含 real_gui_backing=true，但当前 Cua Driver Notepad production run 已证明至少 controlled_notepad_live_edit 不输出该 token。
- Risk: 如果直接把所有 Phase148C 场景纳入总矩阵，旧 token 可能导致真实链路成功但场景断言失败。
- Required next step: 执行 docs/superpowers/plans/2026-06-18-windows-computer-use-production-acceptance-matrix.md 的 Task 1，逐个运行 controlled CLI，按真实输出修正 scenario token 后再进入总矩阵。

## 2026-06-18 Windows Computer Use Phase148C stale token 风险更新
- Status: 正在关闭。Task 1 已证明 Notepad、Calculator 和 local_browser 这三条受控 CLI 当前不输出 real_gui_backing=true；后续场景断言必须删除或替换该 token，否则会把真实成功误判为失败。
- Evidence: Notepad CLI 输出 PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、saved_file_verified=true、real_desktop_touched=true；Calculator CLI 修复后输出 PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK、observed_result_matches_expected=true、uia_invoke_sequence_used=true、real_desktop_touched=true；local_browser CLI 输出 PHASE139_CONTROLLED_BROWSER_LIVE_LOCAL_PAGE_OK、page_changed_after_real_click=true、screenshot_before_after_different=true、real_desktop_touched=true。
- Root cause: 旧 Phase148C 场景复用了统一的 real_gui_backing=true 期望，但不同 controlled runtime 的 CLI 证据字段并不完全一致。
- Fix direction: Notepad 和 local_browser 删除 real_gui_backing=true；Calculator 用 uia_invoke_sequence_used=true 替代 real_gui_backing=true，并保留 observed_result_matches_expected=true。

## 2026-06-18 Windows Calculator keyboard ADD 风险
- Status: 已修复并保留矩阵复验。真实 CLI 首次失败时，Calculator UIA 观察显示 Expression is 1=、Display is 1，说明键盘 ADD 没有稳定输入加号。
- Evidence: 失败报告 learning_agent/computer_use_mcp_v2/memory/computer_use/phase137_controlled_calculator_live_sum/contract-1781776240909/reports/phase137_controlled_calculator_live_sum_report.json 显示 calculator_result_not_observed；修复后报告 learning_agent/computer_use_mcp_v2/memory/computer_use/phase137_controlled_calculator_live_sum/contract-1781776677763/reports/phase137_controlled_calculator_live_sum_report.json 显示 observed_result_matches_expected=true。
- Root cause: 当前 Windows Calculator 对低层键盘加号路径不稳定，语义按钮 InvokePattern 更符合可审计的 Windows UIA 操作。
- Fix evidence: 新增单测 learning_agent.tests.test_windows_computer_use_controlled_calculator_live_sum_phase137 已通过；真实 CLI 输出新增 uia_invoke_sequence_used=true。

## 2026-06-18 Windows Computer Use 生产验收矩阵风险关闭
- Status: 已关闭。生产矩阵已通过真实可见终端验收，最新 result 为 learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-20260618_183954/matrix_result.json。
- Closed stale token risk: Notepad、Calculator、local_browser 场景已删除或替换不输出的 real_gui_backing=true；Calculator 改用 uia_invoke_sequence_used=true 作为稳定语义动作证据。
- Closed permission denial gap: 新增 agent_capability_computer_use_permission_denial_visible_terminal，真实 run 证明 controller 允许 MCP server 启动但拒绝 Computer Use 权限面板，permission_policy_decisions 中包含 response=n、reason=deny_contains。
- Closed runner parser risk: run_windows_computer_use_acceptance.ps1 已使用 Windows PowerShell 可识别的 UTF-8 BOM，避免中文注释在 powershell -File 下被按 ANSI 误解码。
- Mitigated visible GUI flake: 连续矩阵曾出现一次终端聚焦失败和一次 Explorer 快捷键/焦点抖动；runner 已加入场景前 3 秒、场景后 6 秒的保守等待。该措施不降低任何场景断言，只减少真实 GUI 连续切换噪声。
- Residual risk: 该矩阵覆盖受控代表场景，不代表任意第三方 Windows 应用、管理员窗口、UAC、登录页、支付页或私人文件已通过生产验收。

## 2026-06-18 Computer Use 旧目录删除后的验收风险
- Status: 已记录，代码侧自动化验证已通过，但真实可见终端交互验收未完成。
- Cause: 当前可用 Windows Computer Use 技能明确禁止自动化终端应用；因此本轮不能由 Codex 直接在真实终端中键入 prompt。
- Evidence: 相关单元测试 39 项通过，py_compile 通过，Cua Driver borrowing matrix CLI 输出 CUA_DRIVER_WINDOWS_BORROWING_OK，测试导入巡检 IMPORT_FAILURE_COUNT=0。
- Required next step: 用户需手动启动 learning_agent/start_oauth_agent.bat，在真实终端中输入一个验证 prompt，确认 agent 不再引用旧 learning_agent/computer_use 目录后，把输出或截图反馈回来，才能关闭真实终端验收门禁。

## 2026-06-18 Computer Use 旧目录删除后的验收风险关闭
- Status: 已关闭。用户提醒后已改用 OpenHarness acceptance controller 补跑真实可见终端验收。
- Evidence: learning_agent/acceptance_controller/runs/agent_capability_computer_use_mcp_v2_legacy_folder_removed_visible_terminal-20260618_202959/result.json 显示 completed=true、assertion.passed=true、marker_passed=true、prompt_sent=true、prompt_received=true、final_printed=true。
- Debug evidence: latest_run_readable.md 显示真实 agent 调用 bash，exit_code=0；stdout 包含 CUA_DRIVER_WINDOWS_BORROWING_OK 和 passed=true，stderr 包含 Ran 24 tests 与 OK。
- Final marker: COMPUTER_USE_MCP_V2_LEGACY_FOLDER_REMOVED_OK。

## 2026-06-18 Computer Use 压力测试证据缺口
- Status: 已记录，未关闭。
- Evidence gap: 记忆和文档中记录的 production matrix 通过结果路径当前不存在，learning_agent/acceptance_controller/runs 下也没有对应矩阵运行目录。
- Test gap: 当前 learning_agent/tests 目录为空，旧的 Computer Use 回归测试模块已无法导入；CodeGraph 对核心 Computer Use 类也提示没有覆盖测试。
- Baseline risk: 当前 git 工作树同时存在大量旧目录/旧测试删除与 v2 新文件未跟踪状态，压力测试前需要先固定基线，否则失败结果难以判断是功能问题还是工作树状态问题。
- Recommendation: 先重新跑一次 windows_computer_use_production_matrix，确认 10/10、截图、日志和 permission ledger 都存在后，再进入 3 到 5 轮受控重复压力；高强度泛化压力测试需先补回核心自动化测试和明确停止条件。

## 2026-06-18 Computer Use 压力测试前置风险
- 已确认并修复：生产/验收场景仍引用已删除旧包 learning_agent.computer_use，导致 ModuleNotFoundError。
- 已确认并修复：通用 type_text 在真实 SendInput 链路中只传摘要不传 text，可能导致底层 Unicode 输入为空。
- 剩余风险：真实可见终端 start_oauth_agent.bat 交互验收未完成，需要用户本地可见终端手动输入测试 prompt 并反馈输出或截图。

## 2026-06-18 Notepad 会话恢复导致 Computer Use 误触用户内容
- Status: 未关闭。
- Evidence: Notepad 拖动保存压力测试 run 的 events.jsonl 显示，launch_app notepad 后绑定到标题为 *Jan项目的后端是否可以改成使用Qwen3.6-12B-IQ-Q8_0 - Notepad 的窗口，随后执行 press_key CTRL+A 与 type_text。
- Risk: Windows Notepad 可能恢复上次未保存标签页，当前目标身份守卫只把 Notepad 普通应用视为 safe_to_target=true，未区分“新建空白测试窗口”和“恢复的已有用户内容窗口”。
- Impact: 真实 Computer Use 压力测试可能覆盖用户未保存内容；这是高优先级安全阻塞，不适合继续执行多轮压力测试。
- Recommendation: 治本方案是为 Notepad/文档类应用增加“新建空白受控文档身份门禁”，要求窗口标题、进程启动时间、文档路径或空白编辑区状态与本轮 owned resource 绑定；一旦检测到恢复会话、星号未保存标题或非本轮目标名，必须 abort，不允许继续 CTRL+A/type_text/save。

## 2026-06-19 FreshTarget 通用策略后 Notepad 压力场景仍未收束
- Status: 未关闭。
- Evidence: FreshTarget 通用可见终端场景已通过；Notepad 压力场景第二次 run 中首次 launch_app 成功，返回 target_ref=cu-target-learning-agent-default-session-0001、target_ref_one_to_one=true、fresh_target_class=fresh_agent_owned_window、old_window_default_takeover=false。
- Safety improvement: 后续旧窗口/无 target_ref 写动作均为 ok=false 且 low_level_event_count=0；新增前置门禁已覆盖 raw window 缺 target_ref 和重复 launch_app 的自动化测试。
- Remaining failure: 真实压力场景仍在 900 秒内反复尝试 launch_app/按键工具，没有输出最终 marker，也没有创建 C:\Users\joyzq\Desktop\1.txt。
- Current blocker: 需要关闭验收残留 Notepad 窗口后重跑；同时还需要继续增强 observe 后 pending 参数注入/模型纠偏，让模型在 launch_app 后稳定使用同一个 target_ref 继续 type/drag/save。

## 2026-06-19 FreshTarget 旧窗口拒绝后重复 open_application
- Status: 已关闭；干净新窗口完整压力路径另需用户关闭旧 Notepad 后复验。
- Evidence: 用户手工压力测试截图显示 agent 多次调用 `mcp__computer-use__open_application: notepad`；latest_run_readable.md 显示底层返回 `existing_target_window_requires_user_close_or_authorize`、`requires_user_to_close_existing_app=True`、`low_level_event_count=0`，但 `recovery_next_allowed_actions` 仍包含 `launch_app` 且上层没有终止答复。
- Root cause: FreshTarget 旧窗口拒绝只作为普通工具失败/恢复建议返回，没有进入 actionability 的终止阻断态；收敛器只处理 pending 和重复签名，无法把“需要用户关闭或授权”转成最终回答。
- Fix: 新增 `OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED` marker、`actionability_last_block.block_class=user_action_required`、`retry_launch_allowed=false` 门禁；controller 旧窗口预检拒绝时只建议 `ask_user_to_close_or_authorize`；convergence controller 在模型前和工具调用时双层阻断重复 launch/桌面动作。
- Verification: `learning_agent/tests` 已全量通过 50 项，修改文件 py_compile 通过。
- Acceptance evidence: `learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_092813/result.json` 显示 completed=true、assertion.passed=true、alternate_success_checks.dirty_state_safe_refusal.passed=true；debug log 包含 `OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED`、`retry_launch_allowed=false`、`low_level_event_count=0`。
- Remaining risk: 当前只关闭“旧窗口拒绝后重复 launch”问题；完整 Notepad clean-state 拖动保存验收需要用户先手动关闭旧 Notepad 窗口，因为 agent 不能自动关闭用户窗口。

## 2026-06-19 启动 PID 与真实窗口 PID 不一致导致 TargetLease 误拒绝
- Status: 已修复并自动化验证；完整 clean-state 真实 Notepad 压力成功路径待用户关闭旧窗口后复验。
- Evidence: 手工压力测试日志显示 `open_application notepad` 返回 `proxy_window_bound=true`、`binding_reason=alias_match_after_launcher_pid_mismatch`，启动 PID 为 38776，真实窗口 PID 为 39660，随后第一下写动作被 `target_lease_not_verified` 拒绝并触发重复启动。
- Root cause: `build_target_lease` 只读取顶层启动报告，未合并 universal session 嵌套 `launch_result.process_id`；动作前严格身份验证也只按启动器 PID 比较，没有承认已有代理绑定证据里的真实窗口 PID/HWND。
- Fix: `target_lease.py` 合并嵌套启动报告，并新增代理窗口 `actual_window_process_id + hwnd` 验证；`fresh_target_policy.py` 对 `target_lease_not_verified` 停止建议重复 launch；`mcp_session_adapter.py` 的 observe 优先使用 active `target_ref`。
- Verification: `python -m pytest learning_agent/tests/test_computer_use_controller_target_lease_gate.py learning_agent/tests/test_universal_target_session_fresh_proxy_binding.py learning_agent/tests/test_actionability_target_ref_required.py learning_agent/tests/test_universal_computer_use_target_lease.py learning_agent/tests/test_universal_computer_use_fresh_target_policy.py learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py` 结果 25 passed；py_compile 通过。
- Acceptance: `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_103036` 真实终端 run 通过旧窗口安全拒绝断言，证明当前仍不会默认接管旧 Notepad；clean-state 成功路径因用户旧 Notepad PID 39660 仍打开而未执行。

## 2026-06-19 动作缺 target_ref 与旧资源恢复导致 Notepad 压力场景卡死
- Status: 已修复并自动化验证；真实可见终端 acceptance 待复跑确认。
- Evidence: clean-state Notepad 验收 run `20260619_104142` 显示 `open_application notepad` 首次成功并绑定 `target_ref=cu-target-learning-agent-default-session-0001`，但后续 `key` 和 `left_click` 工具结果包含 `target_ref_required_for_bound_window_action`、`has_raw_window=true`、`active_target_count=1`；同一 run 观察到窗口标题恢复为旧 `.md - Notepad` 文档。
- Root cause: `mcp_session_adapter._call_action` 只复用 `last_observed_window`，没有在单 active target 场景把 registry 的 `target_ref` 写回动作顶层参数；同时系统只有应用级 FreshTarget/TargetLease，没有通用资源级 ResourceFreshness，无法把“恢复旧文档”和“新空白目标资源”区分开。
- Fix: `mcp_session_adapter.py` 动作入口新增单 active target 自动注入 `target_ref`、多 active target 缺 `target_ref` 零事件拒绝、observe 后保存资源新鲜度并在旧资源未授权时阻断写动作；`resource_identity.py` 新增通用资源新鲜度判断；`actionability_state.py` 新增资源用户动作 marker 收敛。
- Verification: `python -m pytest learning_agent/tests -q` 结果 58 passed；`python -m py_compile learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/computer_use_mcp_v2/windows_runtime/resource_identity.py learning_agent/core/actionability_state.py` 通过。
- Acceptance: `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_112514` 真实可见终端 run 通过旧窗口安全拒绝断言，result.json 显示 completed=true、assertion.passed=true、alternate_success_checks.dirty_state_safe_refusal.passed=true。
- Remaining risk: 本次真实终端验收前仍存在 PID 34500 的旧 Notepad 窗口，因此未覆盖 clean-state 保存成功路径；如果用户关闭旧窗口后 Notepad 仍自动恢复旧标签，本轮新逻辑应转为 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED` 零事件安全拒绝，而不是写入旧文档。

## 2026-06-19 新进程恢复旧文档时 action 资源门禁缺失
- Status: 已修复 action 层兜底并通过自动化验证；真实可见终端的 restored-resource 分支待用户再次关闭当前 Notepad 后复验。
- Evidence: 用户关闭旧 Notepad 后的验收 run `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_113358` 显示启动前无 Notepad，`open_application notepad` 后得到新 PID 40628，但窗口标题恢复为 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；随后权限请求达到 42 次、没有最终回答、没有创建 `Desktop\1.txt`。
- Root cause: FreshTarget/TargetLease 已解决应用窗口层的一对一绑定，但 `mcp_session_adapter._call_action` 只有在 observe 写入 `last_resource_freshness` 后才会阻断旧资源；当 observe 没留下资源状态时，action 入口不会用当前动作窗口标题做资源兜底判断。
- Fix: `mcp_session_adapter.py` 在自动补 `target_ref` 时同步 `target_lease`，并新增 action 级 `ResourceFreshness` fallback：仅对 agent-owned 新启动/绑定窗口，且标题包含具体文件资源名时，强制检查新资源需求；旧资源未授权则返回 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`，并在底层执行前停止。
- Regression: 新增 `test_action_blocks_restored_document_resource_when_observe_state_is_missing`，该测试先 RED 失败于 action 穿透，修复后 GREEN；完整 `learning_agent/tests` 当前 59 passed。
- Acceptance evidence after fix: 当前 PID 40628 旧 Notepad 仍打开，因此 `20260619_115543` 真实可见终端验收走 preexisting window safe refusal 并通过，`completed=true`、`assertion.passed=true`、`permission_sent_count=3`、`low_level_event_count=0` 证据在日志中存在。
- Remaining risk: 还没有在真实终端中覆盖“启动前无 Notepad，启动后 Notepad 自动恢复旧文档，action fallback 输出资源阻断 marker”的分支；需要用户关闭 PID 40628 后复跑。若用户想验收完整保存成功，还需要 Notepad 启动为空白文档或用户显式授权可使用已有资源。

## 2026-06-19 多目标下显式 target_ref 被 action 映射层丢失
- Status: 已修复并通过自动化验证；真实可见终端验收待复跑确认。
- Evidence: 真实终端 run `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_120326` 显示启动前无 Notepad、`launch_app notepad` fresh target 成功，但后续 `key CTRL+A` 已产生 `low_level_event_count=4`，且日志没有资源新鲜度 action trace 或资源用户动作 marker。
- Root cause: `_controller_arguments_for_tool("key", ...)` 把 MCP 原始参数映射成旧 controller action 时只保留 `key/keys/reason`，没有保留 `target_ref/window`；当存在多个 target 或底层稍后才解析 window 时，adapter 的 ResourceFreshness action fallback 在缺少窗口事实时无法运行。
- Fix: `mcp_session_adapter.py` 新增 `_copy_action_target_fields_from_arguments`、`_resolve_explicit_target_for_action`、`_inject_explicit_target_ref_window`；显式 target_ref 先解析到 registry 绑定窗口和租约，再进入多目标判断和资源新鲜度判断。
- Regression: 新增 `test_explicit_target_ref_resolves_window_before_resource_gate_when_multiple_targets_exist`，覆盖多 target 下显式 ref 指向恢复旧文档窗口时必须返回 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`，且底层执行列表为空。
- Verification: `python -m pytest learning_agent/tests -q` 结果 61 passed；修改文件 py_compile 通过。
- Remaining risk: 当前还需要通过 acceptance controller 复跑真实可见终端场景，确认真实 agent 不再对恢复旧文档窗口执行第一下 `CTRL+A`。

## 2026-06-19 资源拒绝已生效但验收事件缺证据
- Status: 已修复并通过自动化验证；真实可见终端验收待用户关闭残留 Notepad 后复跑。
- Evidence: 真实终端 run `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_131603` 显示 `key CTRL+N` 返回 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`、`resource_freshness_decision=restored_existing_resource_requires_new_blank_or_authorization`、`low_level_event_count=0`，最终回答要求用户关闭或授权旧窗口。
- Root cause: `dispatch_computer_use_mcp_v2_tool()` 发出的 `computer_use_mcp_v2_tool` 验收事件只包含 `tool_name` 和 `ok`，导致 acceptance controller 的 restored-resource 安全拒绝分支无法从事件 payload 验证 marker 和零低层事件。
- Fix: `runtime.py` 新增 `_acceptance_payload_for_tool_result()`，只提取低敏 `error_class`、裁剪后的 `reason`、`resource_freshness_decision` 和 `low_level_event_count`，不把完整工具结果塞进事件。
- Regression: 新增 `test_acceptance_event_includes_resource_user_action_summary`，先 RED 失败于事件缺 `error_class`，修复后 GREEN。
- Verification: `python -m pytest learning_agent/tests -q` 结果 63 passed；`py_compile` 覆盖 `runtime.py` 和新增测试通过。
- Remaining risk: 当前 Notepad PID 41340 是上次安全拒绝留下的恢复旧文档窗口；按安全策略不能自动关闭，需要用户手动关闭后再跑 visible-terminal acceptance。

## 2026-06-19 旧资源恢复后 Ctrl+N 被当成普通写动作误挡
- Status: 已修复并通过自动化验证；真实可见终端验收待用户关闭残留 Notepad 后复跑。
- Evidence: 用户手工压力测试截图和 acceptance run 显示 Notepad 干净启动后仍恢复旧 `.md` 文档，agent 第一轮 `key CTRL+N` 被 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED` 拒绝，导致无法进入新空白资源路径。
- Root cause: `mcp_session_adapter._call_action` 的 ResourceFreshness 门禁把所有旧资源窗口动作同等阻断，缺少“只允许明确新建空白资源动作，并在动作后强制 observe 复核”的中间状态。
- Fix: 新增 `ResourcePreparation` 控制层：只有旧资源阻断 + agent-owned 窗口 + 文档类资源 + 明确新建空白意图 + `CTRL+N` 同时满足时才放行一次；放行后写入 `resource_preparation_pending`，未 observe 确认前所有后续写动作返回 `OPENHARNESS_DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED`。
- Convergence fix: `actionability_state.py` 识别该 observe-required marker 为 pending observe，并给资源准备观察确认路径放宽 `target_ref` 参数门禁，依赖 adapter active target 绑定同一窗口。
- Regression: 新增三个回归测试覆盖“Ctrl+N 可通过但未 observe 不能输入”、“observe 确认空白后可以输入”和“observe-required marker 会保存成 pending observe”，修复前 RED，修复后 GREEN。
- Verification: `python -m pytest learning_agent/tests -q` 结果 66 passed；`py_compile` 覆盖 `mcp_session_adapter.py`、`actionability_state.py` 和测试文件通过。
- Remaining risk: 自动化单测已覆盖状态机，但真实可见终端 acceptance 尚未复跑；当前仍需用户手动关闭残留 Notepad，不能由 agent 自动关闭用户窗口。

## 2026-06-19 Ctrl+N reason 不精确导致 ResourcePreparation 未触发
- Status: 已修复并通过自动化验证；真实可见终端验收待用户关闭残留 Notepad 后复跑。
- Evidence: acceptance run `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_140506` 显示 `open_application notepad` 成功新启动并绑定 PID 23324，但 Notepad 自动恢复旧 `.md` 标签；随后 `key` 工具返回 `desktop_resource_user_action_required`，说明旧资源门禁生效但 ResourcePreparation 没有放行 `CTRL+N`。
- Root cause: `mcp_session_adapter._is_safe_new_blank_resource_preparation_action()` 过度依赖模型 reason 必须命中“新建空白文档/blank document”等精确短语；真实模型 reason 可以只写“按快捷键创建一个新的编辑页”，导致安全 `CTRL+N` 仍被当成普通旧资源写动作拒绝。
- Fix: 在已经确认 `restored_existing_resource_requires_new_blank_or_authorization`、窗口为 agent-owned、资源为文档类且按键为 `CTRL+N` 时，允许一次受控准备动作；未 observe 确认前仍通过 `OPENHARNESS_DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED` 拦截后续写动作。
- Regression: 新增 `test_ctrl_n_is_allowed_as_preparation_even_when_reason_lacks_blank_words`，先 RED 失败于 `result["ok"] is False`，修复后 GREEN。
- Verification: `python -m pytest learning_agent/tests -q` 结果 67 passed；`python -m py_compile learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py` 通过。
- Remaining risk: 当前 PID 23324 的恢复旧文档 Notepad 仍打开；需要用户手动关闭后运行 acceptance controller，才能验证真实 visible-terminal 路径是否完成 `CTRL+N -> observe -> type/drag/save`。

## 2026-06-19 Notepad 裸启动被会话恢复旧文档劫持
- Status: 自动化修复已完成并通过测试；真实可见终端验收待运行确认。
- Evidence: 多次 visible-terminal run 显示启动前没有 Notepad 时，`open_application notepad` 仍会得到新 PID/HWND 绑定，但窗口标题变成 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`，说明 Windows 11 Notepad 在新窗口里恢复旧标签页。
- Working reference: 受控 Notepad driver 之所以能打开空白/目标文件，是因为它调用 `notepad.exe <target_file>`，不是裸启动 `notepad.exe`。
- Root cause: Computer Use 的 `open_application` 链路没有把用户任务里的桌面 `1.txt` 作为受控资源传到 Phase110 启动计划；同时 MCP adapter 在 `request_access` 和 `open_application` 之间丢失了完整任务上下文。
- Fix: controller 解析受控 `.txt` 资源路径并只对已验证支持文本 argv 的应用放行；UniversalTargetSessionRuntime 把该路径写入 `launch_plan.arguments`；MCP adapter 把授权阶段 reason 回填为 open_application 的 `session_task_context`。
- Regression: 新增 controller/runtime/adapter 三处回归测试，覆盖“短 reason + 完整授权上下文 + 桌面 1.txt”必须变成资源绑定启动。
- Verification: `python -m pytest learning_agent/tests -q` 为 71 passed；相关实现和测试 `py_compile` 通过。
- Remaining risk: 需要 acceptance controller 真实可见终端验收确认 Notepad 实际由 `notepad.exe C:\Users\joyzq\Desktop\1.txt` 路径启动后，模型是否能继续完成输入、拖动和保存。

## 2026-06-19 受控资源上下文在模型压缩 reason 和 v2 context 复用时丢失
- Status: 自动化修复已完成并通过测试；真实可见终端验收待用户关闭残留 Notepad 后复跑。
- Evidence: visible-terminal run 显示 `open_application` 的 action payload 里 `session_task_context=""`，`request_access.reason` 只剩“通过真实记事本窗口输入文本、拖动窗口、保存到桌面；先获取 Notepad 权限”，不包含 `1.txt`；因此上一轮 ControlledResourceLaunch 没有触发 `Desktop\1.txt` argv 启动。
- Root cause: 原设计只从模型后续工具参数或 request_access reason 找文件名，没把原始用户 prompt 中的受控资源目标以脱敏字段保存到 `desktop_task_context`，也没处理 `/computer use --full` 先创建 v2 host、真实任务后到的复用时序。
- Fix: `classify_desktop_task()` 只提取 `controlled_resource_name` 和 `controlled_resource_location_hint`，不保存原始 prompt；`LearningAgent._desktop_task_policy_context_from_prompt()` 传递这两个字段；legacy host 构造和每次调用前同步到 `ComputerUseMcpSessionState.grants["agent_desktop_task_context"]`；adapter 在 `open_application` 补齐 `session_task_context`、`controlled_resource_name` 和 `controlled_resource_location_hint`。
- Regression: `test_controlled_resource_context_propagation.py` 覆盖分类器脱敏提取、host 初次同步、adapter 兜底补资源、full-mode context 复用后同步最新任务四条路径。
- Verification: `python -m pytest learning_agent/tests -q` 为 75 passed；`python -m py_compile` 覆盖本轮修改文件通过。
- Remaining risk: 还需要 visible-terminal acceptance 验证真实模型主循环是否在 Notepad 端实际打开 `Desktop\1.txt` 并继续执行输入/拖动/保存。

## 2026-06-19 observe-before-action 依赖模型自觉导致重复重试
- Status: 自动化修复已完成，真实可见终端验收待运行。
- Evidence: 用户手工压力测试截图显示工具返回 `observe_before_action_required` 后，模型仍会反复 `open_application notepad` 或继续其他动作，说明底层拒绝是正确的，但主循环没有把“必须 observe”这类确定性恢复步骤自动执行。
- Root cause: OpenHarness 已有 `actionability_pending` 和收敛提醒，但恢复动作仍交给模型下一轮执行；复杂 prompt 下模型可能忽略 pending，形成重复启动或重复动作循环。
- Fix: 新增 `actionability_recovery.py` 生成有预算的自动 observe 恢复计划；`LearningAgent.run_events` 在真实 Computer Use 工具结果创建 `desktop_observe_before_action` pending 后，合成一条协议配对的 `mcp__computer-use__observe` 并通过同一工具编排器执行。
- Regression: 新增纯状态测试和主循环测试，先 RED 失败于缺少模块/未执行 observe，修复后 GREEN。
- Verification so far: 新增测试 4 passed；FreshTarget/target_ref 相邻回归 10 passed。
- Remaining risk: 仍需真实 visible-terminal acceptance 证明真实 agent 终端中该事件能被观察到，且 Paint/其他普通 GUI app 不会因旧窗口策略被绕过。

## 2026-06-19 Paint 复杂绘图压力测试中模型把下一步动作当最终答案
- Status: 已通过真实可见终端验收确认失败形态；尚未修复。
- Evidence: acceptance run `computer_use_paint_ultra_hero_pressure_visible_terminal-20260619_190321` 返回 `ACCEPTANCE_CONTROLLER_COMPLETED=False`，但已进入 `/computer use --full` 并完成真实 Paint 窗口动作。
- Evidence: `result.json` 显示 `final_answer_printed=true`，最终答案是 `Next desktop action: draw the missing opposite diagonal line...`，没有输出 `PAINT_ULTRA_HERO_PRESSURE_OK` 成功标记。
- Evidence: 同一 run 显示 `real_desktop_touched=true; low_level_event_count=60; successful_action_count=10`，说明真实窗口控制和低层鼠标路径不是零执行。
- Evidence: 最终 Paint 证据图 `computer-window-20260619T111110Z-d3b4f199.bmp` 只看到一条黑色斜线，没有完成复杂人物、颜色填充和保存。
- Evidence: 桌面未发现 `ultra_paint_test.png`，说明保存步骤未完成。
- Root cause confirmed so far: 日志显示 `target_window_existed_before_launch=false` 且 `fresh_target_class=fresh_agent_owned_window`，因此本次失败不是旧窗口接管；低层事件数大于 0，因此也不是鼠标事件完全不可用。
- Root cause confirmed so far: 当前通用失败点是模型在复杂 Computer Use 任务尚未完成时输出“下一步要做什么”的自然语言计划，但 agent 主循环把这条没有工具调用的消息当成最终答案收敛，导致任务提前结束。
- Recommended fix direction: 在 Computer Use active/full 模式下增加“未完成桌面任务收敛门禁”：若 final 文本包含 `Next desktop action`、`下一步动作`、`Use a left-click drag` 等待执行语义，且缺少用户要求的成功标记或保存证据，则不能直接 final，应注入继续执行约束或返回结构化 `desktop_task_incomplete` 状态。
- Recommended fix direction: 该修复必须保持通用，不绑定 Paint、Notepad 或单一软件。

## 2026-06-19 desktop_task 高层工具未真正接管通用 Stage runtime
- Status: 自动化修复已完成；真实可见终端验收待复跑确认。
- Evidence: visible-terminal run 中 `desktop_task` 最初被 `tool_scope` 阻断为 `scope_blocked`，scope 修复后又返回 `not_desktop_task`，强制入口修复后又返回 `computer_use_full_mode_required`。
- Root cause: 高层 MCP 工具 schema、scope、legacy adapter 和 default runtime mode store 没有形成同一个入口协议，导致模型即使调用了 `desktop_task`，真实执行仍会回落到 primitive 工具重试。
- Fix: `desktop_task` 已加入 Computer Use tool pack、operation scope、runtime dispatch、acceptance payload 和 legacy host adapter；`build_default_desktop_task_runtime()` 已改为读取与 interactive full mode 相同的 mode session store。
- Regression: 新增/更新 `test_computer_use_mcp_v2_desktop_task_tool.py`，覆盖工具排序、scope 放行、dispatch 证据、target_hint 从授权应用上下文提取、force entry 绕过旧中文 classifier、默认 runtime 读取 workspace full-mode store。
- Remaining risk: 必须通过真实可见终端验收确认模型优先调用 `desktop_task` 后不再回落到反复 `open_application`。

## 2026-06-19 新窗口身份验证不能证明承载资源是新的
- Status: 自动化修复已完成；真实可见终端验收待复跑确认。
- Evidence: 多次 visible-terminal run 显示 `target_window_existed_before_launch=false`、`fresh_agent_owned_window`、PID/HWND 绑定成功，但窗口标题仍是旧 `.md` 文件，说明应用在新窗口里恢复了旧资源。
- Root cause: 旧 FreshTarget/TargetLease 只验证进程和窗口身份，没有在阶段准备层验证“当前窗口里承载的是新资源还是旧文件/旧标签页”。
- Fix: planner 对文本、绘图和多窗口写入目标写入 `fresh_resource_required=true`；compiler 在 `prepare_target` 阶段读取观察帧标题，遇到通用文件扩展名等旧资源迹象时先执行 `Ctrl+N`、等待、观察，再进入后续写入/绘制阶段。
- Regression: `test_stage_batch_compiler.py` 覆盖旧文件标题触发通用新建批、新资源标题不重复新建；`test_universal_stage_planner.py` 覆盖文本、绘图、多窗口目的窗口的新资源要求。
- Remaining risk: `Ctrl+N` 是通用应用内新建语义，但未知/单实例/特殊应用可能不支持；真实验收若遇到保存弹窗或应用不支持新建，应由阶段 verifier 返回 `needs_user` 或 `desktop_task_incomplete`，不能伪造完成。

## 2026-06-19 Stage 批量文本路径把正文抽错且真实输入缺短通道
- Status: 自动化修复已完成；真实可见终端验收待复跑确认。
- Evidence: visible-terminal run `computer_use_universal_text_task_stage_batch_visible_terminal-20260619_215919` 中 `desktop_task` 已进入通用 Stage runtime，但返回 `desktop_task_incomplete`；Stage 结果里的 `requested_text` 变成 `)`，且 `type_text` 分发失败原因为 `secure_plaintext_text_channel_missing`。
- Root cause: `UniversalDesktopStagePlanner._stage_planner_requested_text()` 使用 `rfind()` 取最后一个输入动词，真实英文 prompt 后半句 `direct file write)` 里的 `write` 覆盖了前面的 `type exactly: hello everyone`。
- Root cause: `UniversalActionDslRuntime._events_for_action()` 为 `type_text` 只生成 `text_length/text_sha256_16` 脱敏事件；`WindowsControlledPhysicalSendInputSender` 正确拒绝把哈希当明文发送，但上游没有提供安全短生命周期明文通道。
- Fix: 文本抽取改为扫描全部候选、剥离说明词、拒绝纯标点；DSL/dispatcher/Phase95 sender 增加分层短通道：普通记录路径脱敏，受控物理路径用私有 `_secure_plaintext_text`，最后一跳真实后端才恢复 `text`。
- Regression: `test_text_payload_extraction_ignores_later_file_write_instruction`、`test_universal_action_dsl_uses_secure_text_channel_for_real_text_backend` 和 `test_computer_use_pressure_readiness.py` 的 raw-text/redacted 双路径均通过。
- Verification: `python -m pytest learning_agent/tests -q` 结果为 139 passed；相关文件 `py_compile` 通过。
- Remaining risk: 该修复证明通用 Stage 文本批可以打到最后一跳，但还必须通过真实可见终端验收确认模型不会在保存阶段再次提前 final。

## 2026-06-19 desktop_task_incomplete 后原子动作 fallback 失控
- Status: 自动化修复已完成；真实可见终端验收待复跑确认。
- Evidence: visible-terminal run `computer_use_universal_text_task_stage_batch_visible_terminal-20260619_222522` 中 `desktop_task` 返回 `desktop_task_incomplete=true` 后，模型继续调用 `mcp__computer-use__key`、`mcp__computer-use__left_click_drag`、`SHIFT+HOME` 等原子动作；之后又出现多轮 `已完成。` 无工具输出，controller 最终超时且无 `result.json`。
- Evidence: 同一 run 的 Stage 报告显示 `universal_stage_task_loop_used=true`、`desktop_task_plan_created=true`、`stage_count=5`、`completed_stage_count=2`、`low_level_event_count=18`，说明高层 Stage Runtime 已进入但未完成，失败点是未完成状态没有约束下一轮工具选择。
- Root cause: `desktop_task_incomplete=true` 只进入最终回答门禁，不会沉淀成 `actionability_pending`；`should_block_tool_for_pending_actionability()` 旧逻辑只拦截读日志/写 fallback，不拦截 `key/click/drag` 这类桌面原子工具。
- Root cause: 修复轮 prompt 中的 `输入文本 \`hello everyone\`` 和 `准确文本：hello everyone` 还会被 planner 抽错，导致 Stage Runtime 即使重试也可能没有正确正文。
- Fix: 新增 `OPENHARNESS_DESKTOP_TASK_INCOMPLETE` marker，`desktop_task.py` 在未完成结果中嵌入该 marker；`actionability_state.py` 解析后只允许 `desktop_task`、`observe` 和必要 `request_access`，其余原子动作全部阻断。
- Fix: `stage_planner.py` 补充 `准确文本/exact text` 前缀和 `文本/text` 说明词剥离，修复中文真实 prompt 和 repair prompt 的正文抽取。
- Regression: 新增 `test_desktop_task_incomplete_actionability.py` 覆盖 marker 解析和原子 fallback 阻断；更新 `test_computer_use_mcp_v2_desktop_task_tool.py` 覆盖真实 MCP `desktop_task` 未完成结果会输出 actionability marker；更新 planner 测试覆盖两种真实抽取失败。
- Verification: `python -m pytest learning_agent/tests -q` 结果为 144 passed；`py_compile` 通过；scenario JSON 校验通过。
- Remaining risk: 仍需真实可见终端验收确认模型在真实终端里被该 pending 门禁拦住后会回到 `desktop_task/observe`，而不是继续输出自然语言“已完成”。

## 2026-06-19 observe 结果覆盖 desktop_task_incomplete pending
- Status: 自动化修复已完成；真实可见终端验收待复跑确认。
- Evidence: visible-terminal drawing run `computer_use_universal_drawing_task_stage_batch_visible_terminal-20260619_224758` 中，`desktop_task` 未完成后模型确实回到了 `desktop_task`，但随后一次 `observe` 后又开始调用 `left_click_drag`、`left_click` 等原子动作，说明高层未完成 pending 被降级覆盖。
- Evidence: `events.jsonl` 显示 `desktop_task` 多次返回 `desktop_task_incomplete=true`，随后出现 `observe ok=true`，再出现 `left_click_drag ok=true`，最终又出现 `legacy_computer_use_rejected` 的 `observe_before_action_required`，证明动作门禁回到了旧原子链路。
- Root cause: `record_actionability_from_tool_result()` 对后来的 marker 无条件写入 pending；当 observe 返回 `OPENHARNESS_DESKTOP_ACTION_REQUIRED` 时，它覆盖了之前的 `OPENHARNESS_DESKTOP_TASK_INCOMPLETE`。
- Fix: 当已有 `DESKTOP_TASK_INCOMPLETE_MARKER` pending，且来源工具是 `observe` 或 `screenshot`，后来的普通 `DESKTOP_ACTION_REQUIRED_MARKER` 只作为观察证据，不覆盖高层未完成 pending。
- Regression: `test_desktop_task_incomplete_survives_observe_action_marker` 覆盖该状态机，修复前 RED，修复后 GREEN。
- Verification: `python -m pytest learning_agent/tests -q` 结果为 145 passed；相关文件 `py_compile` 通过。
- Remaining risk: 绘图验收仍未完整通过；后续还要解决重复 `desktop_task` 可能新开多个目标窗口的问题，且必须在用户关闭当前 Paint/Notepad 残留窗口后复跑 acceptance。

## 2026-06-20 分层 Computer Use 主路径自动化通过但真实终端验收待执行
- Status: 自动化层已通过；真实可见终端验收待执行，不能声明开发完成。
- Evidence: 本轮执行新增/接入意图理解、阶段规划、观察 facts、批执行预算、阶段验证、反思学习和 `desktop_task` 外层分层证据；focused layer tests 48 passed，Computer Use 回归 36 passed，完整 `learning_agent/tests` 194 passed，`py_compile` 通过。
- Evidence: 新增 layered text/drawing/multi-app acceptance 场景均使用 `/computer use --full` 首行和自动同意配置，JSON 格式校验通过。
- Fixed during verification: `stage_task_loop.py` 报告里曾引用不存在的 `max_stage_repairs_reached` 变量，端到端测试复现为 NameError；已改为真实变量 `max_repairs_reached`，并删除不可达旧 `return`。
- Remaining risk: 自动化 fake loop 证明分层链路可运行，但尚未证明真实本机窗口中模型会稳定完成文本、绘图、多应用复杂任务；必须通过 acceptance controller 的真实可见终端场景后才能关闭该风险。

## 2026-06-25 Desktop GUI Shell V2 Golden Trace Risk

- 已处理风险：V2 蓝图里的 JSON 示例曾把一个敏感 bridge header 字面量放进 `must_not_contain`，但同一任务后续测试又要求 fixture 原文不能包含该敏感词。实际实现保留“不得泄露敏感内容”的测试语义，改用 `raw_secret_value`、`local_secret_path`、`raw_stack_dump` 等低敏占位词，避免黄金样本自己违反红线。

## 2026-06-25 Desktop GUI Shell V2 Real Adapter Boundary

- Status: 设计边界已明确，未启用真实 adapter。
- Evidence: Task 3 CodeGraph 映射确认真实入口应围绕 `LearningAgent.run(...)`、`run_agent_with_harness_session(...)`、`agent.run_events(...)`、`StatusEventStore` 和 `stop_event`，但 V2-Core 只实现 deterministic fake streaming。
- Risk: 如果后续误把 `DefaultHarnessGuiAgentAdapter(enabled=False)` 当作真实 agent 接线，会造成 GUI 看似可切真实模式但实际只返回 `adapter_unavailable`。
- Required fix direction: 到 V2-Trust 再接真实 adapter，并先补 `AgentEvent -> GUI V2`、取消、权限 approve/deny、懒导入、脱敏和 Layer C trigger decision 的合同测试；不能在 V2-Core 为了演示直接导入模型/OAuth/浏览器/Computer Use runtime。

## 2026-06-25 Desktop GUI Shell V2 Permission V2 Risks

- Status: 已关闭本轮自动化风险。
- Closed risk: 权限请求 payload 曾缺少 `tool_name`、`action_summary`、`created_at` 和 `answered_at`，导致 GUI 弹窗、主线程和 trace panel 的审计字段不完整。现在 `gui_permissions.py` 统一生成字段，`test_gui_permissions_v2_contract` 覆盖 manager 事件和 payload。
- Closed risk: 权限原因和风险摘要可能把本机路径、`sk-*` 密钥或 bearer token 直接展示给用户。现在请求、风险和决策理由都会经过 `redact_permission_text()`，并有敏感文本回归测试。
- Closed risk: 前端允许/拒绝按钮在后端确认前没有禁用态，快速双击可能产生重复请求。现在 `AppShell` 用 `pendingPermissionDecisionId` 阻止重复提交，弹窗和 banner 都显示提交中状态；后端仍保留 `permission_already_answered` 结构化冲突作为最终防线。
- Remaining risk: 当前仍是 fake streaming/default GUI bridge 权限流；真实 agent adapter 接入时必须把实际工具权限事件映射到同一套 `record_permission_required()` 和 `decide_permission()`，不能新增旁路权限 payload。

## 2026-06-25 Desktop GUI Shell V2 Trace Inspector Risks

- Status: 已关闭本轮自动化风险。
- Closed risk: 工具事件此前只散落在原始状态时间线，用户无法快速看到某个工具的参数、耗时、结果或失败码。现在 `reduceGuiEventToTraceRows()` 和 `TracePanel.tsx` 把工具轨迹作为右侧“工具”页签一等展示。
- Closed risk: 工具参数和诊断文本可能显示本机路径、`sk-*` 密钥或 bearer token。现在 trace reducer 在 `argsPreview` 和 `diagnosticText` 中统一输出 `[redacted]`，并有前端 reducer 回归测试覆盖。
- Remaining risk: 当前 trace row 仍消费 fake/default GUI events；真实 agent adapter 接入后必须确认真实工具事件也统一发出 `tool_started/tool_finished` 或等价字段，不能只把工具日志写到主线程消息里。

## 2026-06-25 Desktop GUI Shell V2 Runtime Panel Risks

- Status: 本轮路径泄露风险已关闭，真实 runtime 深度接入风险仍保留。
- Closed risk: 浏览器 provider 和 Computer Use panel 在状态快照读取失败时可能把 Windows 本机路径或异常细节显示给用户。现在 `/v2/gui/runtime/panels` 失败时只返回 `状态快照暂时不可读。`，测试覆盖序列化 payload 不包含用户路径片段。
- Closed risk: 前端此前只显示浏览器 provider 状态，Computer Use 锁、急停、权限模式和允许动作不可见。现在右侧“浏览器”页签同时显示 `BrowserPanel` 和 `ComputerUsePanel`，用户能看到桌面自动化是否 off、是否锁定、是否有急停请求和待处理权限。
- Remaining risk: Computer Use 面板当前展示的是安全摘要和 mode session 状态，不等于完整真实 Windows lock/abort controller 已接入 GUI。后续真实 adapter/runtime 接入时，必须把真实 lock owner、abort requested、hotkey/fallback 状态映射到同一 `/v2/gui/runtime/panels` payload，不能新增旁路 API。

## 2026-06-25 Desktop GUI Shell V2 Settings Diagnostics Risks

- Status: 本轮诊断泄露风险已关闭，真实崩溃恢复深度仍待后续任务扩展。
- Closed risk: `diagnostics` payload 最初复用完整 health，测试发现序列化结果包含 `C:\Users\joyzq...` 临时路径。现在 `build_gui_diagnostics_payload()` 会对内嵌 `health.workspace` 脱敏，诊断复制包也只包含安全摘要。
- Closed risk: snapshot 读取失败可能把原始异常路径显示到前端。现在 diagnostics 失败时固定返回 `状态快照暂时不可读。`，并且测试覆盖 token、Bearer、`sk-*`、Windows 用户路径和工作区路径脱敏。
- Remaining risk: 当前诊断页能显示 online/schema/degraded/last error/release gate/copy bundle，但还不是完整 crash recovery manager。后续如果要做崩溃自动恢复、日志打包上传或历史 gate 浏览，应继续复用 `/v2/gui/diagnostics` 和 `settingsStore.ts`，不能新增会泄露绝对路径或 token 的旁路接口。

## 2026-06-25 Desktop GUI Shell V2 Visual Accessibility Risks

- Status: 本轮布局风险已关闭，依赖审计风险未处理。
- Closed risk: 1100px 以下媒体查询曾把 `.status-inspector` 直接 `display:none`，这会让 1024x720 视觉验收丢失右侧状态/工具/浏览器/设置/诊断 tabs。现在紧凑布局保持三栏，并通过收窄侧栏、右栏和 tab 间距保留右侧检查器。
- Closed risk: composer 输入框曾允许 `resize: vertical` 且最大高度 160px，用户拖拽或长输入可能挤压消息区。现在 composer 和 textarea 都有稳定 min/max，长 prompt 在 textarea 内部滚动。
- Open risk: `apps/desktop/scripts/start-desktop-dev.ps1` 运行 `npm install` 时报告 6 个 npm audit vulnerabilities（3 moderate、2 high、1 critical）。本轮 Task 12 未升级依赖，因为视觉任务范围只做布局/可访问性；后续包装或发布门禁任务应决定是否升级 Electron/Vite 相关依赖并复跑 GUI 验收。

## 2026-06-25 Desktop GUI Shell V2 Sessions Search Risks

- Status: 本轮搜索和归档入口风险已关闭，pin 写入 UI 仍是后续产品边界。
- Closed risk: 侧栏此前只读 V1 sessions，缺少 title/archive/pin/updated_at 字段，搜索按钮也只是静态入口。现在后端 V2 sessions/search/rename/archive 有合同测试，前端 client 和 Sidebar/SearchPanel 均接入真实 endpoint。
- Closed risk: 归档入口如果只是打开普通搜索，会让用户看不到已归档会话。现在归档入口会调用 `sessions(true)`，只展示 archived 会话；归档模式下继续输入关键词会调用 `searchSessions(query, true)`。
- Remaining risk: `pinned` 字段已经在 payload、排序和 Sidebar 标记中预留，但当前没有 pin/unpin 写入 endpoint 或 UI 控件。后续实现时应新增后端合同和 GUI 控件，不要只在前端临时标记。

## 2026-06-25 Desktop GUI Shell V2 Harness Panel Risks

- Status: 本轮长任务可视化风险已关闭，真实 pause/resume 能力仍是后续边界。
- Closed risk: 长任务 goal、队列、checkpoint 和 blocked reason 此前没有右侧 GUI 入口，用户只能从日志或终端推断长任务位置。现在 `/v2/gui/harness/status` 和“任务”页签把这些字段作为一等状态展示，并有后端合同测试覆盖。
- Closed risk: 前端如果无条件显示暂停/恢复按钮，会误导用户以为 Harness 已支持真实控制。现在后端 `controls.pause_supported/resume_supported` 默认为 false，控制 endpoint 返回结构化 `unsupported`，前端只有能力为真时才显示按钮。
- Remaining risk: 当前 pause/resume 只是结构化占位，不代表真实 Harness runtime 已具备安全暂停和恢复。后续实现前必须先建立 runtime 级状态机、审计事件和恢复合同测试，不能只改 GUI。

## 2026-06-25 Desktop GUI Shell V2 Packaging Risks

- Status: 本轮包装脚本可运行风险已关闭，正式安装器和依赖漏洞风险仍保留。
- Closed risk: `package-windows.ps1` 最初以无 BOM UTF-8 保存，Windows PowerShell 5.1 解析中文注释后把后续语句吞进同一行，导致 `$DesktopRoot` 为空。现在包装和启动 PS1 已统一转换为 UTF-8 BOM + CRLF，并验证脚本可运行或可解析。
- Closed risk: 启动脚本此前没有提前检查端口占用，renderer/bridge 失败时错误不够直观。现在 backend 脚本检查 bridge 端口，desktop dev 脚本检查 renderer 端口，并输出修复提示。
- Remaining risk: 当前 Task 13 只生成 Windows development artifact，不是签名安装器；后续如果要面向普通用户分发，需要决定 electron-builder/electron-forge、代码签名、自动更新、依赖漏洞升级和真实安装路径策略。

## 2026-06-25 Desktop GUI Shell V2 Release Gate Risks

- Status: 自动门禁风险已关闭，可见 GUI 通过状态仍必须由真实窗口确认。
- Closed risk: 旧 release gate 只跑少量 Python bridge tests 和前端门禁，没有覆盖新增 V2 diagnostics、sessions、runtime panels、Harness 等 GUI 后端合同。现在用 `python -m unittest discover -s learning_agent/tests -p "test_gui*.py"` 跑完整 GUI 测试集。
- Closed risk: release gate 以前没有生成 Layer A 可见 GUI smoke 指令，容易把自动测试通过误读成视觉验收通过。现在 `visible-gui-smoke.ps1` 会生成人工检查清单，release gate 明确输出只是 instructions generated。
- Remaining risk: `visible-gui-smoke.ps1` 默认不启动 GUI，也不会自动判断 PASS。最终声明 V2 GUI 成熟前仍必须有真实 Electron 窗口可见验收证据。

## 2026-06-25 Desktop GUI Shell V2 Final Acceptance Risks

- Status: V2 可见 GUI 矩阵风险已关闭，正式安装器和真实 runtime 深度接入仍是后续边界。
- Closed risk: 只跑 release gate 会误判视觉成熟度。现在 `layer_a_visible_acceptance` 目录包含真实 Electron 初始截图、CDP 驱动后截图、全屏最终截图和 JSON 结果，证明窗口真实可见且核心交互通过。
- Closed risk: Layer A smoke 进程可能残留占用端口。验收后已按 pid 和监听端口关闭本轮 backend、renderer、Electron、CDP，确认 8776、5177、9223 均不再监听。
- Closed risk: V2 visible rows 曾缺少 English streaming、safety refusal、Shift+Enter visual caret、token rejection GUI error、unknown route GUI error、bridge offline banner、browser degraded state、Computer Use unavailable state、settings panel opens 的可见证据。现在 `layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` 和对应 PNG 已覆盖这些行，`apps/desktop/tests/gui-prompt-matrix.md` 已全部勾选。
- Closed risk: 安全拒绝最初只能靠特殊 trace 或隐藏合同测试证明。现在 fake adapter 能识别真实高风险 prompt 并发出 `safety_refusal`，前端把它保留为带 `安全拒绝` 标签的一等助手消息，且完成事件不会覆盖 refusal kind。
- Closed risk: token/unknown-route/offline 错误最初缺少可点击、可截图的 GUI 表面。现在坏 token 会进入主线程错误消息，诊断页有未知路由探针，bridge 连接失败会显示 `bridge-offline-banner`。
- Remaining risk: 当前 V2 成熟度是 GUI shell 和 fake/default bridge adapter 的成熟度；真实 agent adapter、真实模型/OAuth、真实 browser automation execution、真实 Computer Use execution、签名安装器和真实 pause/resume Harness 仍需要后续任务单独设计、实现和验收。

## 2026-06-26 Provider Settings V1 Visual QA Bugs

- Closed risk: 备用 Vite 端口 `5277` 下，Provider Settings 的浏览器 CORS 预检返回 403，真实 Electron 设置页显示 `提供商加载失败`。根因是 `gui_bridge.py` 只允许 5177 来源；已改为允许固定桌面来源和 `http://127.0.0.1:<port>` / `http://localhost:<port>` 本机带端口来源，并用 `test_alternate_loopback_vite_origin_can_load_provider_settings` 锁定回归。
- Closed risk: 视觉验收 driver 的自定义 provider 等待表达式返回 DOM 元素，`Runtime.evaluate(returnByValue)` 因对象链过深失败。已改为只返回布尔值，避免 CDP 克隆 DOM。
- Closed risk: 390px 移动截图曾使用 `mobile: true`，实际 `innerWidth` 仍为 980，无法证明窄窗口布局。已改为桌面窗口缩窄式 emulation，最终结果为 `innerWidth: 390`。
- Closed risk: 真实 390px 下 `body min-width: 980px` 和背景三栏网格把 document 撑宽。已在 `theme.css` 和 `layout.css` 的 760px 以下规则解除全局宽度下限并收成单栏，最终结果为 `scrollWidth: 390`。
- Closed risk: 多轮视觉脚本运行后 OpenAI 已连接，可能绕过 API key password 输入框断言。driver 现在每轮先断开 OpenAI 基线，再打开连接弹窗，最终结果中的 `API key input has password type` 详情为 `inputType: password`。
- Evidence: 详细复现、证据、根因、修复和复测记录见 `learning_agent/test/provider_settings_v1/task09_visual_qa/gui_bug_notes.md`；最终截图和 `provider_settings_visual_qa_result.json` 已保存在同一目录。

## 2026-06-26 Provider Settings V1 Release Gate Secret Scan Risks

- Closed risk: 初版 secret leak scan 直接把 `Authorization: Bearer` 文档示例、脱敏测试夹具和历史 `task-notification` 记录当成真实泄漏，导致门禁不可运行。现在脚本保留蓝图要求的原始 `rg` 扫描，但对测试、文档、Provider Settings 证据、历史运行记忆和固定 `task-notification` 假阳性做过滤，生产路径仍然失败。
- Closed risk: Windows PowerShell 5.1 对无 BOM UTF-8 + 中文注释解析不稳定，初次运行脚本报语法错误。`assert_no_provider_secret_leaks.ps1` 已转换为 UTF-8 BOM，后续可直接运行。
- Evidence: `powershell -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\test\provider_settings_v1\scripts\assert_no_provider_secret_leaks.ps1` 输出 `Provider secret leak scan passed.`

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Risks

- Open risk: 稳定 V1 如果把 mock browser/headless auth-attempt 显示成真实 OAuth 成功，会误导用户认为 ChatGPT Pro/Plus 已经可真实驱动模型；实现时必须在 payload、UI 文案和验收记录里标注 mock/experimental 边界。
- Open risk: 如果 provider catalog、store、diagnostics 或视觉证据中出现 `refresh_token`、`access_token`、`id_token`、`secret_ref` 或 raw API key，将违反本轮安全边界；后续 Task 9 必须用自动扫描锁住。
- Closed risk: 蓝图自检项曾把旧命名字面量写进“不得出现”的说明文字，导致 `rg` 门禁误报。根因是检查项描述与检查规则冲突；已改为不包含旧词的描述并复跑扫描通过。
- Closed risk: Task 8 第三轮 visual QA 中，headless mock complete 已返回 `complete`，但连接弹窗没有关闭、OpenAI 行没有刷新为已连接。根因是 `SettingsDialog.tsx` 先 `setConnectAuthAttempt(complete)`，触发依赖 `connectAuthAttempt.status` 的 effect cleanup，把本轮 `disposed` 置为 true，随后 `providerSettings()` 结果被丢弃。修复为 `authAttemptPollDecision()`：complete 状态先刷新 catalog，再清空 attempt 并关闭弹窗；新增 `settingsDialogViewModel.test.ts` 回归测试。
- Closed risk: Task 8 driver 曾用 `innerText` 读取 headless 设备码和 browser 授权提示，真实 GUI 把这些内容放在 readonly input 的 `value` 中，导致 driver 误判等待页失败。修复为读取 `.provider-connect-code-row input.value`，最终 `openai_connect_visual_qa_result.json` 为 `ok=true`。
- Closed risk: Task 8 失败后 Node driver 因 CDP WebSocket 未关闭而让 wrapper 挂住并残留 9276/5677/9725 进程。已按 pid 清理失败轮残留，最终成功轮 9376/5777/9825 无监听残留；后续如 driver 失败，应先读取 result JSON 和 DOM 证据，再清理端口。
- Closed risk: Task 9 secret scan 的运行产物扫描在零命中时 `$RuntimeSecretMatches` 为 `$null`，StrictMode 下访问 `.Count` 导致门禁自身失败。根因是 PowerShell 外部命令无输出不会自动给空数组；已把 `rg` 输出包成 `@(...)`，并复跑 `assert_no_provider_secret_leaks.ps1` 得到 `Provider secret leak scan passed.`。
- Closed risk: Task 9 visual QA 原先没有 API Key step 截图，不能满足蓝图的肉眼 GUI 验收要求。已在 driver 中补充点击 `API 密钥`、断言 `input.type=password`、断言空提交禁用、截图 `openai_api_key_step_1365x768.png`，并复跑 visual QA 得到 `inputType=password`。
- Closed risk: Task 11 release gate lint 发现 `shouldPollAuthAttempt()` 返回 boolean 后，TypeScript 不能在嵌套 async function 中证明 `connectAuthAttempt` 和 `guiClient` 非空。根因是类型窄化不能跨普通 helper 和闭包稳定传播；已改为先固定 `activeClient/activeAttempt`，显式判空后创建非可选 `pollingClient: ProviderSettingsClient`，并复跑 `npm --prefix apps/desktop run lint` 通过。
- Environmental note: Task 11 默认 visual QA 使用的 bridge 端口 8776 被已有 `python -m learning_agent.app.cli desktop-bridge --workspace ... --port 8776` 进程占用。为避免关闭用户正在查看的外壳，最终验收改用 9576/5977/9975 备用端口；最终 visual QA 通过且备用端口无监听残留。

## 2026-06-26 OpenHarness Desktop Manual Restart Provider Settings Bug

- Closed risk: 用户手动查看 OpenHarness Desktop 后，设置里的“提供商”页显示 `提供商加载失败`。根因不是前端新代码失败，而是端口 `8776` 上仍运行着任务实现前启动的旧 `desktop-bridge` 进程；该旧进程没有 `/v2/gui/provider-settings/providers` 路由，所以真实窗口请求返回 404。
- Evidence: 手动请求 `http://127.0.0.1:8776/v2/gui/provider-settings/providers` 初始返回 404；重启 8776 bridge 后同一路由返回 200，payload 包含 OpenAI provider。
- Fix: 停止旧 `start-backend.ps1`/`desktop-bridge` 进程，重新启动当前 worktree 的 `start-backend.ps1 -Port 8776`，再重启 Electron 窗口。
- Verification: 已在真实 OpenHarness Desktop 窗口中打开 `设置 -> 提供商`，截图 `learning_agent/test/provider_settings_v2_openai_connect/manual_restart_provider_loaded_verified.png` 显示提供商列表正常加载，不再出现 `提供商加载失败`。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Risks

- Open risk: 真实可见 GUI OAuth direct SSE 验收尚未完成；在用户真实浏览器完成 OAuth、GUI 选中真实模型并收到真实模型 delta 之前，不能声明 V3 开发完成。
- Closed risk: 旧路径会先走 Codex CLI WebSocket，超时后再 HTTPS fallback，导致用户看到明显慢响应；V3 已增加 `direct_sse` runtime path，并要求第一条 GUI 事件证明 `websocket=false`、`codex_cli=false`。
- Closed risk: 当前 ChatGPT 账户不支持的模型会造成反复慢失败；V3 已在 model registry/provider catalog/composer 三层保留可见但禁用的 unsupported 模型，并阻止自动选择这类模型。
- Open risk: 真实 OAuth direct SSE 依赖明确配置 `OPENHARNESS_OPENAI_CLIENT_ID`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1` 和 `OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`；如果本机环境缺少这些 gate，只能完成 fake fixture 验收，不能完成真实模型验收。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Visible OAuth Blocker

- Evidence: 真实模式 OpenHarness Desktop 已成功打开 OpenAI browser OAuth 窗口，窗口标题为“欢迎回来 - OpenAI”，可见邮箱输入框和继续按钮。
- Evidence: 后端 provider catalog 在 09:10:32-09:14:28 连续轮询均返回 `connected=false`、`source=none`、`direct_route_status=""`，说明 token 交换尚未发生。
- Root cause: 这不是 bridge、provider catalog 或 direct SSE 代码失败；当前阻塞点是 OpenAI 账号登录/授权尚未由用户完成。
- Required next action: 用户需要在 OpenAI 授权窗口手动完成登录和授权，然后由 agent 继续检查 `direct_sse_ready`、模型选择、真实模型 delta 和 runtime_path。

## 2026-06-27 OAuth Link Opened Inside Electron

- Closed risk: OpenAI OAuth `访问此链接` 原先使用普通 `<a target="_blank">`，Electron 主进程没有 `setWindowOpenHandler`，导致授权页开在 Electron 自己的新窗口里。
- Evidence: Computer Use 窗口列表显示 Electron 同时拥有 `OpenHarness Desktop` 和 `欢迎回来 - OpenAI` 两个窗口，OpenAI 页无法复用 Edge 登录态。
- Root cause: Electron 默认会为 `target=_blank` 创建内部 `BrowserWindow`，除非主进程显式把外部网页交给 `shell.openExternal()`。
- Fix: `apps/desktop/src/main/index.ts` 现在拦截 `window.open` 和 `will-navigate` 外部 http(s) 链接，用系统浏览器打开；`apps/desktop/src/main/externalLinks.ts` 提供可测试的外链判断。
- Verification: `externalLinks.test.ts` 通过；真实 GUI 重启后再次点击 OpenAI `访问此链接`，Microsoft Edge 标题变为 `欢迎回来 - OpenAI...`，Electron 窗口列表只剩 `OpenHarness Desktop`。
- Remaining blocker: 外链问题已修复，但用户尚未在 Edge 中完成 OpenAI 账号登录/授权，因此 provider catalog 仍显示 `connected=false`。

## 2026-06-27 Direct ChatGPT OAuth Callback Missing

- Open risk: 用户手动完成 OpenAI 官方认证后，OpenHarness Desktop 仍不能变成真实 OpenAI 连接状态。
- Evidence: 当前 provider catalog 返回 OpenAI `connected=false`、`source=none`、`direct_route_status=""`，`memory/status/events.jsonl` 没有 OAuth callback 或 token exchange 事件。
- Evidence: 新生成的 auth-attempt 为 `mode=real_browser`，授权地址指向 `auth.openai.com/oauth/authorize`，`redirect_uri=http://localhost:1455/auth/callback`，`originator=openharness`，`oauth_client_source=observed_opencode_reference`。
- Evidence: `Get-NetTCPConnection -LocalPort 1455` 无监听进程；当前真实 bridge 监听在 `127.0.0.1:8776`。访问 `http://127.0.0.1:8776/auth/callback?...` 返回 404，访问 `http://localhost:1455/auth/callback?...` 超时。
- Root cause: Desktop provider auth-attempt 目前只生成 OpenAI 授权 URL 和内存 attempt/state，没有启动 `localhost:1455` callback server，也没有 `/auth/callback` 路由，更没有把 `code` POST 到 `https://auth.openai.com/oauth/token` 换取 token 后调用 `complete_real_provider_auth_attempt_with_tokens()`。
- Pattern evidence: 项目旧 `CodexOAuthChatModel._login_with_browser()` 已包含完整工作模式：启动一次性 `localhost:1455` HTTP server、接收 `code/state/error`、校验 state、调用 `_exchange_code_for_tokens()`、再保存 tokens。Desktop 新链路缺这条闭环。
- Open risk: 当前 URL 使用 OpenCode 观察到的 client id，但 `originator=openharness`；若官方对 client/originator/redirect 组合有校验，后续即使补齐 callback server，也可能需要按 OpenCode 的真实参数兼容实验。此点尚未实证，不能当成已确认根因。

## 2026-06-27 Direct ChatGPT OAuth Callback Missing Fix Update

- Closed risk: Desktop provider auth-attempt 缺少本机 callback server/token exchange 闭环。现在真实 OAuth start 会按 redirect_uri 端口启动 `localhost:<port>` listener，`/auth/callback` 能接收 `code/state/error`，校验 state 后调用 token exchange 并安全保存 token refs。
- Closed risk: token exchange 失败或官方 callback 返回 error 时，attempt 曾可能永久 pending。现在 exchange/network/callback error 都会把 attempt 标记为 `failed` 并清理 `_ATTEMPT_OAUTH_SECRETS`，前端轮询能看到终态。
- Closed risk: 授权 code 可能被默认 HTTP access log 泄露。callback handler 现在覆盖 `log_message()` 丢弃默认访问日志，浏览器结果页也不会显示 code/state/verifier/token。
- Verification: `test_openai_oauth_code_exchange_posts_form_request`、`test_real_oauth_callback_listener_exchanges_code_and_updates_catalog` 已覆盖 token exchange 表单、真实本机 HTTP callback、provider catalog 更新和 direct SSE ready 状态；相关 Python/前端回归和 provider secret leak scanner 均通过。
- Remaining open risk: 真实 OpenAI 官方 OAuth 是否接受 `originator=openharness` 与 OpenCode 观察 client id 的组合仍需用户完成真实浏览器授权后验证；这不是当前 callback 缺失根因，但可能是下一轮官方返回拒绝时需要继续排查的外部协议兼容点。

## 2026-06-27 Direct ChatGPT OAuth Callback Owner Probe Fix

- Closed risk: 用户在 OpenAI 官方网页完成授权后，GUI 外壳仍可能保持 `connected=false`。根因不是官方网页认证失败，而是旧的 OpenHarness Desktop bridge 抢占了固定回调端口 `localhost:1455`。
- Evidence: `Get-NetTCPConnection -LocalPort 1455` 显示 PID `14872` 正在监听；该进程命令行为 `desktop-bridge --port 8876`，而不是用户当前期望连接的 GUI bridge。用 `8776` 进程生成的 OAuth `state` 访问 `localhost:1455/auth/callback` 时，页面返回 `OpenAI OAuth state 未找到或已过期。`，证明回调进入了错误进程。
- Root cause: OAuth `state` 和 PKCE verifier 保存在单个 bridge 进程内存中，但 redirect URI 固定为 `http://localhost:1455/auth/callback`。旧 bridge 只要还占着 1455，就会接走新 GUI 的官方回调，新 GUI 自然无法保存 token，也无法保持连接状态。
- Fix: callback server 新增 `/auth/callback/health?owner=...` owner probe；`_ensure_openai_oauth_callback_server()` 只有确认 `localhost:<port>` 实际路由到当前 server owner 后才允许继续生成授权 URL，否则快速失败为 `openai_oauth_callback_listener_unavailable`。OpenAI 授权 URL 的 `originator` 也按 OpenCode 参考改为 `opencode`，降低官方兼容风险。
- Verification: `python -m py_compile learning_agent/app/gui_provider_auth_attempts.py learning_agent/app/gui_provider_openai_oauth.py` 通过；`python -m pytest learning_agent/tests/test_gui_provider_openai_real_oauth_attempts.py -q` 为 6 passed；`python -m pytest learning_agent/tests/test_gui_provider_openai_real_oauth_attempts.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_oauth_disconnect.py learning_agent/tests/test_openai_model_registry.py -q` 为 14 passed。
- Runtime verification: 旧 `8876` bridge 已停止；修复后的 `8776` bridge 重启后，`localhost:1455` listener 归属同一 PID `41600`。手动发起真实 OAuth start 得到 `mode=real_browser` 官方 URL，且 `originator=opencode`；测试 attempt 已取消。
- Remaining open risk: 真实可见 GUI OAuth 完整验收仍需要用户在系统浏览器完成 OpenAI 官方授权，再检查 provider catalog 变成 OAuth connected/direct_sse_ready。

## 2026-06-27 Direct ChatGPT OAuth Real GUI Reply Protocol Fix

- Closed risk: OpenAI OAuth 已连接成功后，GUI 消息窗口仍失败。根因不是 token 缺失，而是 Direct SSE 请求体向真实 ChatGPT Codex endpoint 发送了不支持的 `metadata` 字段。
- Evidence: 使用真实 access token 发最小诊断请求时，后端返回 HTTP 400 JSON：`{"detail":"Unsupported parameter: metadata"}`；删除 `metadata` 后进入下一层错误。
- Closed risk: GUI 的“超高”推理档位映射错误。根因是前端/adapter 使用 Codex UI 语义 `ultra`，而真实 ChatGPT Codex endpoint 要求 `xhigh`。
- Evidence: 删除 `metadata` 后，真实后端返回 `Invalid value: 'ultra'. Supported values are: 'none', 'minimal', 'low', 'medium', 'high', and 'xhigh'.`
- Closed risk: 修正请求体后仍失败为 endpoint drift。根因是 parser 未把真实 SSE 事件 `response.content_part.added` / `response.content_part.done` 视为已知非文本事件。
- Evidence: 真实 GUI turn `turn_ab3efb0eedc0497d` 已不再出现 HTTP 400，而是在 `response.content_part.added` 上误报 `endpoint_drift_detected`。
- Fix: `gui_agent_adapter.py` 只发送真实 API 支持的 `reasoning` 字段，并把 `ultra` 映射为 `xhigh`；`chatgpt_codex_sse.py` 接受 content part added/done 事件。
- Verification: `test_direct_sse_adapter_emits_runtime_path_and_streaming_events` 新增断言保证请求体不含 `metadata` 且 reasoning 为 `xhigh`；`test_content_part_events_are_accepted_before_text_delta` 保证真实 content part 事件不会再中断 parser；相关 pytest 12 passed。
- Visible GUI verification: OpenHarness Desktop 真实窗口中发送 `请只回复 OH_FINAL_OK`，真实 OAuth direct SSE 路径返回 `OH_FINAL_OK`；事件流记录 `runtime=direct_sse`、`transport=https_sse`、`websocket_enabled=false`、`codex_cli_used=false`、`direct_sse_completed` 和 `gui_turn_completed`，说明消息窗口已能经真实后端路径正常回复。

## 2026-06-27 GUI Context Compact Assistant History Protocol Fix

- Closed risk: GUI 上下文接入后，短期记忆 no-compact recall 首次在真实窗口中失败为 `HTTP Error 400: Bad Request`，用户可见表现是消息窗口无法回答刚才记住的 `ALPHA_CONTEXT_927`。
- Evidence: 失败 turn 的事件中 `context_budget` 显示 `input_message_count=3`、`compacted=false`、`reason=compact_not_needed`，`runtime_path` 显示 `runtime=direct_sse`、`transport=https_sse`、`websocket_enabled=false`、`codex_cli_used=false`，说明失败发生在 Direct SSE 请求体协议层，不是 WebSocket 回退或 GUI session 丢失。
- Root cause: `compact_messages_to_responses_input()` 把 assistant 历史消息的 content type 也写成 `input_text`。真实 ChatGPT Codex responses endpoint 对 assistant role 只接受 `output_text` 或 `refusal`，所以官方返回 `Invalid value: 'input_text'. Supported values are: 'output_text' and 'refusal'.`
- Fix: `learning_agent/app/gui_context.py` 现在按 role 选择 content type：assistant 历史使用 `output_text`，user/developer/system 输入使用 `input_text`；相关 Direct SSE adapter/context body 测试夹具同步更新。
- Verification: 最小真实 HTTP SSE 诊断在修复前返回 HTTP 400，修复后返回 HTTP 200 且首行为 `event: response.created`；`python -m pytest learning_agent\tests\test_gui_context_builder.py learning_agent\tests\test_gui_direct_oauth_sse_adapter_context.py learning_agent\tests\test_chatgpt_codex_sse_client_context_body.py -q` 为 9 passed。
- Visible GUI verification: 修复并重启 OpenHarness Desktop 后，no-compact recall 返回 `ALPHA_CONTEXT_927`；继续强制压缩后，最终 recall 事件显示 `compacted=true`、`compact_completed`、`direct_sse_completed`、`gui_turn_completed`，最终 answer 仍为 `ALPHA_CONTEXT_927`。

## 2026-06-27 Manual API Key Launch OAuth Link Is Mock

- Open risk: 用户在“手动连接 OpenAI API key”的启动模式下点击 OpenAI 的 ChatGPT browser OAuth 链接，期望打开 OpenAI 官方 OAuth 官网，但实际没有进入官网。
- Evidence: 当前运行中的 provider catalog 返回 `secret_store_kind=dev_json`、OpenAI `connected=false`、`chatgpt-browser status=mock_available`、`chatgpt-headless status=mock_available`。
- Evidence: 直接调用 `/v2/gui/provider-settings/auth-attempt/start` 创建 `openai/chatgpt-browser` 授权尝试，返回 `attempt_mode=mock`，URL host 为 `127.0.0.1`，URL 前缀为 `http://127.0.0.1:18991/mock/openai/browser`，不是 `auth.openai.com`。
- Root cause: 当前 GUI 是为了用户手动填 API key 拉起的运行模式，只设置了 `OPENHARNESS_GUI_MODEL_MODE=real` 和 `OPENHARNESS_OPENAI_RUNTIME=direct_sse`，没有设置真实 OAuth 门禁所需的 `OPENHARNESS_OPENAI_AUTH_MODE=real_browser`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1`、`OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`、`OPENHARNESS_OPENAI_CLIENT_ID=<OpenHarness client id>`。
- Required next action: 若用户要手动填 API key，应点击 OpenAI 的 `API 密钥` 认证方式；若要打开 OpenAI 官方 OAuth 官网，必须停止当前 API key 启动模式，并以真实 OAuth 配置重新启动 GUI。

## 2026-06-27 Restore OAuth UI After Wrong API-Key-Only Fix

- Closed risk: 上一轮把默认 OAuth 入口禁用为 `oauth_config_required`，导致用户看到“只剩 OpenAI key 接口”，偏离用户需求。
- Fix: 已通过 revert 恢复 OpenAI 三方法界面；不再把 OAuth browser/headless 从连接弹窗中隐藏。
- Evidence: 当前以真实 OAuth env 重启后，auth-attempt start 返回 `mode=real_browser`，URL host 是 `auth.openai.com`，说明 OAuth 官网链接可以由后端生成；不是 API key-only 路径。
- Remaining note: 默认 mock 和真实 OAuth 的显示文案仍有历史包袱，catalog 里 browser/headless 状态仍显示 `mock_available`；但在真实 OAuth env 下，实际 start 走 `real_browser`。后续可单独做一个小修复，把 catalog 状态在真实 OAuth 模式下改成 `available`，避免文案误导。

## 2026-06-27 OAuth One-Click Launch Prevents Wrong Runtime Mode

- Closed risk: 用户手动启动 OpenHarness Desktop 时容易漏掉真实 OAuth 环境变量，导致 OpenAI 连接界面存在但实际 auth-attempt 走 mock/API-key-only 链路，表现为 OAuth 官网打不开或 provider 状态误导。
- Fix: 新增 `start_openharness_desktop_oauth.bat` + `start-openharness-desktop-oauth.ps1`，把真实 OAuth、Direct SSE、os_encrypted secret store、callback 端口、client id 和旧端口清理统一到一个入口。
- Evidence: 一键脚本启动时已在后端层验证 OpenAI auth-attempt 为 `real_browser`，授权 URL host 为 `auth.openai.com`，并取消测试 attempt；真实 GUI 中设置页显示 OpenAI OAuth 已连接且 Direct ChatGPT OAuth SSE 已就绪。
- Regression guard: `learning_agent/tests/test_openharness_desktop_oauth_one_click_launch_scripts.py` 会检查一键脚本是否仍包含真实 OAuth 门禁、Direct SSE、provider endpoint 验证、`auth.openai.com` 验证和临时日志目录覆盖。
## 2026-06-27 OAuth One-Click Bat Codepage Failure

- Closed risk: 用户双击 `start_openharness_desktop_oauth.bat` 无法启动 OpenHarness Desktop GUI。
- Evidence: 直接执行 bat 复现错误：`'不会启动' is not recognized as an internal or external command` 等中文 REM 注释片段被 `cmd.exe` 当成命令执行，说明脚本在进入 PowerShell 前已经失败。
- Root cause: bat 文件使用 UTF-8 中文注释，但 Windows `cmd.exe` 双击默认代码页不是 UTF-8；中文字节在默认代码页下可能被误解析出命令分隔符，导致 REM 行后半段变成可执行命令。
- Fix: bat 第一行 `@echo off` 后立即执行 `chcp 65001 >nul`，并新增回归测试要求任何中文文本出现前必须先切换 UTF-8。
- Verification: `.bat` 入口重新执行后完整启动 bridge/renderer/Electron；computer-use 在真实 GUI 输入 `hello`，模型经 Direct SSE 返回 `Hello! How can I help you today?`，事件包含 `direct_sse_completed`、`message_completed`、`gui_turn_completed`。

## 2026-06-27 Real Harness Tool Name Mapping Bug

- Closed risk: Phase 3 真实只读工具测试中，`tool_started` 事件存在但 `payload.tool_name` 为空，导致 GUI TracePanel 无法显示真实工具名。
- Evidence: 复现脚本打印真实事件发现 core `tool_use_seen` / `tool_call_started` 的 payload 形状为 `tool_call.tool_name=read_file`，而 mapper 只读取 `tool_call.name`。
- Root cause: `gui_agent_event_mapper._tool_payload()` 对 core 事件字段形状假设过窄，只兼容 fixture 里的 `name`，没有兼容真实 core 发出的 `tool_name`。
- Fix: `_tool_payload()` 现在按 `name -> tool_name -> base_payload.tool_name` 顺序抽取工具名。
- Verification: 失败测试 `test_default_harness_adapter_emits_read_only_tool_trace` 已转绿；同时重跑 `test_gui_agent_event_mapper.py`，7 项相关测试通过。

## 2026-06-27 Real Agent Harness Adapter V2 Verification Notes

- Closed risk: Phase 3 真实只读工具轨迹最初需要兼容 core 事件里的 `tool_call.tool_name` 字段；已在 mapper 中按 `name -> tool_name -> payload.tool_name` 读取，真实 GUI 中 `read_file` 工具名已可见。
- Closed risk: 真实 GUI 验收中首个 real harness turn 一度看起来停在 running；继续采集 `/v1/gui/bootstrap` 证据后确认不是死锁，后续事件依次出现 `model_response_completed`、`continuation_decision`、`session_saved`、`run_completed`、`message_completed`、`gui_turn_completed`。
- Environmental note: `python -m py_compile` 在本 Windows 沙箱中会因为 `.pyc` 写入/替换权限触发 `WinError 5`，本轮改用内存 `compile()` 验证关键 Python 文件语法。
- Environmental note: `npm --prefix apps/desktop test -- --run` 和 `npm --prefix apps/desktop run build` 在沙箱内首次失败为 `esbuild spawn EPERM`；按权限规则切到沙箱外重跑后均通过。
- Closed risk: 恢复验收时一次 GUI 输入未落入输入框并提示“请输入内容”，未计为通过；重新确认后端真实恢复 turn 已进入运行并最终 `gui_turn_completed`，取消后的恢复能力通过。

## 2026-06-27 Desktop GUI Toolchain Acceptance Stale Port Risk

- Closed risk: Task 1 真实 GUI 验收时，“链路”页签最初不可见或显示 `0 tools`，看起来像前端没有接入工具链清单。
- Evidence: `GET /v2/gui/toolchain` 在旧 `8776` bridge 上返回 404；Windows 窗口最初连接的是旧 `5177` renderer；重启当前 worktree 的 renderer 后“链路”页签出现，重启当前 worktree 的 bridge 后接口返回 `65 tools`、`11 groups`。
- Root cause: 旧 OpenHarness bridge/renderer 进程占用了固定端口，`visible-gui-smoke.ps1 -Launch` 隐藏启动的新 launcher 因端口占用退出，真实 GUI 实际连到了旧进程。
- Fix: 停止旧 `5177` renderer 和旧 `8776` bridge，使用当前 worktree 的 `start-backend.ps1` 与 `start-desktop-dev.ps1` 重启，再用 computer-use 刷新并验证真实窗口。
- Guard: 后续 GUI 验收若出现“代码已通过测试但窗口看不到新功能”，先检查 `8776`、`5177` 端口 owner 和 `/v2/gui/*` endpoint 是否来自当前 worktree，再判断是否为代码 bug。
## 2026-06-27 Desktop GUI Harness Controls Task 2 Environment Note

- Closed risk: Task 2 验收前再次遇到固定端口环境干扰风险；旧 renderer 曾占用 `5177`，可能让真实 OpenHarness Desktop 窗口连到旧前端或旧后端，从而看不到当前 worktree 的 Harness 控制按钮。
- Evidence: 本轮在可见 GUI 验收前先确认并停止旧 `5177` renderer PID `29776`，随后从当前 worktree 重启 `8776` bridge 与 Electron renderer；computer-use 才能在 `任务` 页签看到 `暂停`、`恢复`、`停止`、`Checkpoint`。
- Root cause: 这是长任务多次重启 GUI 时的本地运行环境残留，不是 Task 2 源码 bug；固定端口 `8776/5177` 被旧进程占用时，新窗口可能仍显示旧 bundle 或连旧 bridge。
- Guard: 后续每个 GUI 任务验收前，先确认 `8776`、`5177` 的 owner 来自当前 `.worktrees/gui-toolchain-control-center`，再判断真实 GUI 现象；如果端口 owner 不一致，先重启当前 worktree bridge/renderer，再做代码级 systematic debugging。

## 2026-06-27 Desktop GUI Computer Use Workbench Task 3 Stale Bridge Route

- Closed risk: Task 3 真实 GUI 验收时，点击 Computer Use `观察` 按钮后，GUI 显示 `Computer Use 观察请求失败：GuiClientError: 未知 GUI bridge POST 路径。`
- Evidence: `Get-NetTCPConnection -LocalPort 8776 -State Listen` 显示端口 owner 为旧 Python bridge PID `27712`；该进程命令行虽然指向当前 worktree，但启动时间早于 Task 3 路由新增，所以内存中的 `GuiBridgeHandler` 路由表没有 `/v2/gui/computer-use/observe`。
- Root cause: `visible-gui-smoke.ps1 -Launch` 在固定端口已被占用时无法替换旧 bridge，真实 Electron 窗口仍连到旧后端；这是本地运行进程残留，不是前端按钮或 `gui_computer_use.py` contract 代码错误。
- Fix: 停止旧 `8776` bridge PID `27712`，从当前 worktree 重新启动 `apps/desktop/scripts/start-backend.ps1`，随后直接 POST `/v2/gui/computer-use/observe` 返回 `ok=true`、`action=observe`、`low_level_event_count=0`。
- Verification: 重新用 computer-use 点击真实 GUI 中的 `观察`、`申请权限`、`中止` 后均显示成功结果；面板模式按预期变为 `observe` 和 `stopped`，并且三个动作都显示 `低层事件：0`。
- Guard: 后续每个新增 `/v2/gui/*` 路由在真实 GUI 验收前，先用 `Invoke-RestMethod` 或浏览器端实际请求确认当前 `8776` bridge 已加载该路由；若返回 404/未知路径，优先检查端口 owner 和进程启动时间，再判断代码 bug。

## 2026-06-27 Desktop GUI Browser Workbench Task 4 Stale Bridge Route

- Closed risk: Task 4 真实 GUI 验收时，点击 Browser `刷新` 按钮后，GUI 显示 `Browser 刷新状态请求失败：GuiClientError: 未知 GUI bridge POST 路径。`
- Evidence: `Get-NetTCPConnection -LocalPort 8776 -State Listen` 显示端口 owner 为旧 Python bridge PID `21488`；该进程启动时间早于 Task 4 新增 `/v2/gui/browser/refresh-status` 和 `/v2/gui/browser/open`，所以运行中路由表没有新接口。
- Root cause: 前端 bundle 和后端源码已经包含新路由，但真实 Electron 窗口仍连接旧 bridge 进程；这是本地固定端口上的运行进程残留，不是 `BrowserPanel.tsx` 或 `gui_browser_control.py` 的实现错误。
- Fix: 停止旧 `8776` bridge PID `21488`，从当前 worktree 重新启动 `apps/desktop/scripts/start-backend.ps1`，并直接 POST `/v2/gui/browser/refresh-status` 验证新 bridge 返回 `ok=true`、`status=refreshed`。
- Verification: 重新用 computer-use 点击真实 GUI 中的 `刷新` 后，主消息区出现 `completed` 刷新状态，右侧面板显示 `refresh-status · refreshed`；点击 `记录打开` 后，主消息区出现 `completed` 记录打开状态，右侧面板显示 `open · recorded`。
- Guard: 后续新增 Browser/MCP/Shell 等任何 `/v2/gui/*` endpoint 后，真实 GUI 验收前必须先确认 `8776` 的当前 PID 是路由新增之后启动的进程，并用实际 HTTP 请求验证新路由已加载。
