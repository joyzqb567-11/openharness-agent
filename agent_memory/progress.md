# 当前任务进度摘要（2026-06-16）

## GUI 上下文压缩 V4 蓝图（2026-06-27）

- 用户追问 OpenHarness Desktop GUI 消息窗口是否已经接入原有上下文压缩模块；代码证据显示当前 Direct ChatGPT OAuth SSE 路径仍只把本轮 `prompt` 传给模型，没有把 `GuiSession.messages` 历史消息接入 compact pipeline。
- 已读取相关代码：`learning_agent/core/conversation_context.py`、`learning_agent/core/compact_pipeline.py`、`learning_agent/app/gui_bridge.py`、`learning_agent/app/gui_agent_adapter.py`、`learning_agent/tests/test_gui_direct_oauth_sse_adapter.py`、`learning_agent/tests/test_gui_turn_payload_contract.py`。
- 已按 `superpowers:writing-plans` 产出 V4 实施蓝图：`docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4.md`。
- 蓝图核心方案：新增 `learning_agent/app/gui_context.py`，以 GUI 持久化消息 `GuiSession.messages` 为唯一历史源，复用 `learning_agent.core.compact_pipeline.prepare_messages_before_model()` 进行主动压缩，并在 Direct SSE adapter 中支持压缩后的多消息输入和上下文过长后的单次反应式压缩重试。
- 蓝图验收门禁：自动化测试通过、Direct SSE 请求体可证明包含压缩历史、右侧运行事件面板可见 context/compact 事件、并通过 Computer Use 对真实可见 GUI 执行长上下文回忆验收。
- 已按 `andrej-karpathy-perspective` 产出评估报告：`docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4-karpathy-review.md`；评估结论是方向正确但计划过重，执行前应补强 TaskState 目标来源、current prompt exact-once、Direct SSE schema contract、reactive retry 状态机、事件隐私边界和真实 GUI 数据层证据。
- 已按评估报告升级原蓝图为 V4.1：同一文件 `docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4.md` 现在加入 Task 0 Evidence Lock、最小垂直切片、current prompt exact-once、Direct SSE body contract、两次尝试 reactive retry 状态机、隐私安全事件和真实 GUI 双层验收；蓝图从约 1017 行收紧到约 730 行。
- 已按用户要求补充 V4.1 蓝图的真实 GUI 验收门禁：每个影响 GUI 的任务必须使用 `computer-use` 在真实可见 OpenHarness Desktop GUI 窗口验证；发现 bug 时必须使用 `superpowers:systematic-debugging` 查询 root cause、修复并重新测试，通过后才允许继续执行蓝图下一个任务。

历史全文归档：`agent_memory/archive/2026-06-16-computer-use-mcp-v2-parity/`。

## 成功标准

- `inferred_ant_mcp` 明确作为 ClaudeCode Computer Use 外部 MCP 包反推层存在。
- 公开工具面、运行时分发、host adapter、Windows 执行链和返回结构尽量对齐 ClaudeCode 可观察行为。
- 自动化测试覆盖工具面、禁止旧入口、Windows adapter、SendInput parity、截图 artifact、坐标缩放和 zoom 图片结果。
- 真实可见终端交互验收通过后，才允许声明“开发完成”或“验收通过”。

## 已完成

- Task 1：锁定 Computer Use MCP v2 工具面和禁止旧入口，提交 `fd267a8`、`efb40c7`。
- Task 2：写动作无 host 时改为失败，避免假成功，提交 `7c8be81`。
- Task 3：把 ClaudeCode parity 工具映射到 Windows session action，提交 `eb0affc`、`d71c41b`、`edbaa3c`。
- Task 4：通过 Windows SendInput parity 执行链接通新增鼠标键盘动作，提交 `874eb66`、`2ab6095`。
- Task 5：把 Phase41 图片结果测试迁移到 v2 MCP wrapper，提交 `488146b`。
- Task 6：修正 `zoom` 观察语义，并返回模型可见的局部裁剪截图，提交 `659b7c0`。
- Task 7：补充 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/README.md`，并按规则把超长 `agent_memory/context.md`、`progress.md`、`bugs.md` 归档压缩。
- Task 8 自动化补强：补齐 `docs/computer_use_mcp_v2_architecture.md`、`computer-use` MCP 配置注册、独立 selftest probe 和可见终端场景；原失败的 3 个接入资产测试已修复。
- Task 8 可见终端验收：首次场景发现 `COMPUTER_USE_MCP_V2_READY` 可被失败句子误命中；已改用独立最终标记 `COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK`，并让模型只调用一次只读 `mcp__computer-use__list_granted_applications`。

## Task 6 关键细节

- 红测 1：`test_zoom_returns_cropped_model_visible_image_result` 证明原先 zoom 没有 `zoom_image_result_count`，也没有局部图片结果。
- 红测 2：`test_zoom_runtime_uses_observation_semantics` 证明原先 runtime 没有把 `zoom` 写入观察记录。
- 绿码：`runtime.py` 把 `zoom` 放入观察分支；`observation.py` 调用 `host.zoom`；`windows_runtime/mcp_session_adapter.py` 从源截图裁剪局部 PNG，并追加模型可见 `image_result`。
- 验证：47 个相关测试通过。

## 当前状态

Task 7 文档与项目记忆更新已完成。Task 8 自动化验证已通过：77 个相关测试通过，独立 probe 输出 `COMPUTER_USE_MCP_V2_READY`，新/改 Python 文件 py_compile 通过。真实可见终端验收已通过两次：worktree run `learning_agent/acceptance_controller/runs/agent_capability_computer_use_mcp_smoke_visible_terminal-20260616_091911/result.json`，原项目精确 BAT 路径 run `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_smoke_visible_terminal-20260616_092030\result.json`。

## 主目录同步与 CodeGraph 重建（2026-06-16）

- 用户确认选择“让主目录变成最新版项目”后，主目录 `codex/publish-main` 已从 `bf2bbb9` 快进到 `7c0542b`，与 `codex/computer-use-claudecode-parity` 的最新 computer use parity 提交对齐。
- 合并前，主目录原有脏改动已保存到 stash：`stash@{Tue Jun 16 12:36:32 2026}: On codex/publish-main: pre-parity-main-dirty-20260616-claudecode-parity`。该 stash 未删除，后续如需找回旧工作区内容可以再检查。
- 主目录旧 `.codegraph/` 曾被 CodeGraph MCP 进程锁住，`codegraph uninit -f .` 未能删除；随后停止锁进程、执行 `codegraph index -f .`，并清理残留锁。
- 当前主目录 CodeGraph 状态：`Files 1,228`、`Nodes 47,762`、`Edges 95,043`，`codegraph status .` 显示 `[OK] Index is up to date`。
- CodeGraph 抽样验证已能定位最新 computer use parity 符号：`_build_zoom_image_result`、`ZOOM_IMAGE_RESULT_MODEL`、`computer_use_mcp_tools`、`ComputerUseMcpSessionAdapter`。
- 主目录验证已通过：关键文件 `py_compile` 通过；`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_tool_scope` 共 43 个测试通过；`computer_use_independent_mcp_server_probe.py` 输出 `COMPUTER_USE_MCP_V2_READY`，公开工具数为 24。
- 用户指出 parity worktree 继续保留会干扰后续二次开发后，已删除 `.worktrees/computer-use-claudecode-parity` worktree，并删除已合并分支 `codex/computer-use-claudecode-parity`；主目录仍保留同一提交 `7c0542b`，所以这不是丢代码，而是清理重复源码副本。
- 用户继续确认清理剩余 worktree 后，已删除 `.worktrees/codex-computer-use-full-desktop-task-router` 与 `.worktrees/stage15a-event-runtime`，并删除对应分支 `codex/computer-use-full-desktop-task-router`、`stage15a-event-runtime`；复核 `git worktree list --porcelain` 只剩主目录，`.worktrees/` 目录当前没有子目录。
- 用户确认空的 `.worktrees/` 外壳目录也可以删除后，已删除 `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees`，复核结果为目录不存在。

## 停止条件

若无法打开、观察或向用户本地可见终端窗口输入内容，必须明确说明：真实可见终端交互验收未完成，不能声明开发完成。然后请求用户手动运行 `start_oauth_agent.bat` 并反馈输出或截图。

## ClaudeCode 协议级对齐蓝图（2026-06-16）

- 用户追问为什么不直接做“ClaudeCode 协议级完全对齐”，并确认需要把第 1 层协议层和第 2 层桥接层的补齐方案写成长期蓝图，避免上下文压缩后跑偏。
- 已按 `superpowers:writing-plans` 规则创建实施蓝图：`docs/superpowers/plans/2026-06-16-computer-use-claudecode-protocol-parity.md`。
- 蓝图明确：不推倒重写 Windows backend；通过 `inferred_ant_mcp` facade、protocol normalizer、ClaudeCode-compatible schema、权限 grant flags、content blocks、lock lifecycle、display state、dynamic tools/list 和 bridge wrapper 来对齐 ClaudeCode 可观察协议。
- 蓝图要求后续每个实现任务都先用 CodeGraph 复核 OpenHarness 与 ClaudeCode 相关链路，再按红测、实现、验证、提交的顺序推进。
- 蓝图的最终完成门禁仍然是：自动化测试通过、独立 MCP probe 输出 `COMPUTER_USE_MCP_V2_READY`、并完成 `start_oauth_agent.bat` 真实可见终端交互验收。

## ClaudeCode 协议级对齐执行进度（2026-06-16）

- Task 1-3 已完成第一组基础对齐：新增 `claudecode_protocol.py` 保存 ClaudeCode 字段、grant flags、sentinel 应用和 defers-lock 常量；新增 `protocol_normalizer.py` 把 `coordinate`、`start_coordinate`、`region`、`bundle_id`、`apps`、`actions`、`duration`、`text`、`direction/amount` 转成 Windows runtime 兼容字段。
- `build_tools.py` 已改为 ClaudeCode-compatible 主字段：鼠标坐标主推 `coordinate`，拖拽主推 `start_coordinate` + `coordinate`，zoom 主推 `region`，open_application 主推 `bundle_id`，request_access 主推 `apps`/`grantFlags`，computer_batch 主推 `actions`；旧 `x/y`、`app_name`、`applications`、`steps` 等字段仍保留兼容。
- `runtime.py` 已在分发入口先调用 `normalize_computer_use_arguments`，确保 agent-side 和 stdio-side 共用同一个协议转换边界。
- 已新增并通过测试：`test_computer_use_mcp_v2_claudecode_protocol_manifest`、`test_computer_use_mcp_v2_protocol_normalizer`。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope`，共 30 个测试通过。
- 已通过 py_compile：`claudecode_protocol.py`、`protocol_normalizer.py`、`build_tools.py`、`runtime.py`。
- Task 4 权限模型 parity 已完成：`ComputerUseMcpV2Context` 新增 `allowed_apps`、`grant_flags`、`sentinel_warnings`、`denied_apps`；`request_access` 支持 ClaudeCode 风格 `apps`、`grantFlags`、风险提示和拒绝记录；`list_granted_applications` 返回 `allowedApps`、`grantFlags`、`sentinelWarnings`、`deniedApps` 并保留旧 `grants` 兼容。
- 已新增并通过测试：`test_computer_use_mcp_v2_permission_grants`，共 3 个测试通过。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope`，共 30 个测试通过。
- 已通过 py_compile：`types.py`、`permissions.py`、`test_computer_use_mcp_v2_permission_grants.py`。
- Task 5 结果 content blocks parity 已完成：`result_blocks.py` 新增 `text_content_block`、`image_content_block`、显式 `content`/`debug` 支持，并让 `mcp_content_from_result` 在有显式 content 时直出 ClaudeCode-compatible blocks、无显式 content 时保留旧 JSON 文本回退。
- `observation.py` 已能从 `image_results`、`zoom_image_results`、`legacy_text`、嵌套 `legacy_result` 中收集截图 artifact，复用 Windows 图片读取/转码逻辑生成 base64 image content block，同时输出 `debug.artifact_path`、`debug.mime_type`、`debug.image_count`。
- `actions.py` 已透传 host payload 自带的 `content`/`debug`；`image_messages.py` 已能从新协议 JSON 的 `debug.artifact_path` 中提取图片引用，保持旧图片回灌链路可用。
- 已新增并通过测试：`test_computer_use_mcp_v2_result_blocks`，共 5 个测试通过。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks`，共 38 个测试通过。
- 已通过 py_compile：`result_blocks.py`、`observation.py`、`actions.py`、`image_messages.py`、`test_computer_use_mcp_v2_result_blocks.py`。
- Task 6 Lock lifecycle 与 cleanup parity 已完成：`ComputerUseMcpV2Context` 新增 `computer_use_session_id`、`check_computer_use_lock`、`acquire_computer_use_lock`、`release_computer_use_lock`、`cleanup_after_turn`、`is_lock_held_locally` 回调字段。
- `runtime.py` 已实现 ClaudeCode defers-lock 语义：`request_access`、`list_granted_applications` 只走 lock check；其它合法 Computer Use 工具先 acquire lock，失败时返回 `computer_use_lock_unavailable` 且 `desktop_action_performed=False`；成功/失败结果均写入 `debug.lock_mode`、`debug.lock_backend`。
- `bind_session_context.py` 已接入 agent 主循环现有 `_computer_use_cleanup_runtime()`，确保 v2 MCP lock、主循环 finally cleanup 和 `/computer` runtime 使用同一套 Windows lock 事实源。
- `WindowsComputerUseSessionRuntime` 已新增 `check_computer_use_lock`、`acquire_computer_use_lock`、`release_computer_use_lock`、`cleanup_after_turn`、`is_lock_held_locally` facade 回调方法；`turn_cleanup.py` 的报告新增 `claudecode_lock_lifecycle=True` 与 `lock_cleanup_mode=turn_cleanup`。
- 已新增并通过测试：`test_computer_use_mcp_v2_lock_lifecycle`，共 7 个测试通过。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle`，共 45 个测试通过。
- 已通过 py_compile：`types.py`、`runtime.py`、`bind_session_context.py`、`session_runtime.py`、`turn_cleanup.py`、`test_computer_use_mcp_v2_lock_lifecycle.py`。
- Task 7 Display state parity 已完成：`ComputerUseMcpV2Context` 新增 `selected_display_id`、`display_pinned_by_model`、`display_resolved_for_apps`、`last_screenshot_dims`，内部保存 snake_case，返回给模型时使用 ClaudeCode camelCase。
- `coordinates.py` 新增 `claudecode_display_state_from_payload`，只作为薄适配层从 Windows payload、坐标映射、图片结果和 legacy 嵌套 payload 中抽取 `selectedDisplayId`、`displayResolvedForApps`、`lastScreenshotDims`，不改 DPI、多屏和截图坐标核心算法。
- `observation.py` 已在 observe/screenshot/zoom 后更新 context 并把 `displayState` 写入返回 payload；模型显式传入 `selectedDisplayId` 时会设置临时 `displayPinnedByModel=True`，后端自动解析 display 时不会误设 pin。
- `bind_session_context.py` 已能从 agent 的 `computer_use_selected_display_id`、`computer_use_display_pinned_by_model`、`computer_use_display_resolved_for_apps`、`computer_use_last_screenshot_dims` 恢复 display 初始状态；`cleanup_computer_use_mcp_v2_turn` 会清理临时 pin，但保留 `last_screenshot_dims`。
- 已新增并通过测试：`test_computer_use_mcp_v2_display_state`，共 5 个测试通过；新增测试首次暴露 `_dims_from_mapping(None)` 无限递归，已按堆栈证据修复为只递归非空字典。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_tool_scope`，共 50 个测试通过。
- 已通过 py_compile：`types.py`、`runtime.py`、`bind_session_context.py`、`observation.py`、`coordinates.py`、`test_computer_use_mcp_v2_display_state.py`。
- Task 8 Dynamic tools/list app inventory 已完成：`build_tools.computer_use_mcp_tools(app_inventory_hint=...)` 允许把安全 Windows 应用候选追加到 `request_access.description`，无 hint 时保持静态 schema。
- `claudecode_bridge/mcpServer.py` 已在 `tools/list` 时用 daemon 线程读取 Windows app inventory，最多等待 `1.0` 秒；成功时动态注入 `request_access.description`，timeout 或 error 时回退静态 schema，并通过 `record_runtime_trace` 写入 `computer_use_tools_list_app_inventory` 事件。
- 已新增并通过测试：`test_computer_use_mcp_v2_dynamic_tools_list`，共 4 个测试通过，覆盖描述注入、JSON-RPC tools/list 注入、timeout 空 hint、异常静态回退。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_tool_scope`，共 76 个测试通过。
- 已通过 py_compile：`mcpServer.py`、`build_tools.py`、`test_computer_use_mcp_v2_dynamic_tools_list.py`。
- Task 9 Bridge wrapper parity 已完成：`claudecode_bridge/wrapper.py` 从薄 JSON 调用器升级为 ClaudeCode 风格 agent-side wrapper，记录 `current_tool_use_context`、透传 `call_id`、绑定同一 `ComputerUseMcpV2Context`、把 MCP `content` blocks 转成 agent model blocks，并在异常/中断路径调用同一 turn cleanup。
- `claudecode_bridge/toolRendering.py` 已补齐 ClaudeCode 风格工具消息渲染字段：`coordinate`、`start_coordinate`、`region`、`direction`、`amount`、`text`、`duration`、`bundle_id`、`apps`、`actions`，并给常见成功结果返回短摘要。
- `learning_agent/mcp/agent_adapter.py` 已改为向 wrapper 传入 `call_id`，并从 wrapper JSON 中记录 `agent_model_block_count`，方便主循环知道一次 computer use 调用向模型回灌了多少结果 block。
- 已新增并通过测试：`test_computer_use_mcp_v2_bridge_wrapper`，共 4 个测试通过，覆盖 call_id 上下文记录、截图 content block 到 agent model block 的映射、公开 JSON 不重复暴露 base64、大模型可见 block 保存在 agent 上、cleanup hook 复用同一绑定 context、ClaudeCode 字段名渲染。
- 已复跑通过：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_agent_side_binding learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper`，共 40 个测试通过。
- 已通过 py_compile：`wrapper.py`、`toolRendering.py`、`agent_adapter.py`、`test_computer_use_mcp_v2_bridge_wrapper.py`。
- Task 10 总验证和真实终端验收已完成：关键 Python 文件 `py_compile` 通过，完整 computer use 回归矩阵 84 个测试通过，独立 MCP probe 输出 `COMPUTER_USE_MCP_V2_READY` 且工具数为 24。
- 已更新 `docs/computer_use_mcp_v2_architecture.md`，记录最终协议链路：ClaudeCode-facing schema、`protocol_normalizer.py` 转换边界、权限 grant flags、MCP content blocks、lock lifecycle、display state、tools/list 动态 app inventory、agent-side wrapper 的 current tool use context 和 content block 映射。
- 真实可见终端验收已通过：控制器启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，在真实终端中输入 `/computer use --full` 和只读 MCP prompt，生成 run `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_smoke_visible_terminal-20260616_165645\result.json`。
- 本次真实终端 run 的关键断言：`completed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`、`computer_use_mcp_v2_tool=true`、工具调用为 `list_granted_applications`、最终回答为 `COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK`。

## 2026-06-16 Computer Use Adaptive Image Pipeline

- 用户确认采用“内部保真 + 外部自适应压缩”路线：内部 evidence 保留 Windows 原始截图格式，模型出口按图片规模和来源选择 PNG/JPEG。
- 已按 TDD 先补红灯测试：`test_agent_compresses_large_bmp_computer_use_screenshot_to_jpeg_model_image_block` 和 `test_evidence_store_preserves_bmp_payload_as_internal_artifact` 首次运行失败，证明旧链路仍是 BMP/PNG 固定路径。
- 已修改旧 `learning_agent/computer_use/evidence.py` 和 v2 `learning_agent/computer_use_mcp_v2/windows_runtime/evidence.py`：`normalize_screenshot_artifact_bytes` 不再把 BMP 源头转 PNG，只做格式清理并保留原始截图证据。
- 已修改 `learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py`：新增 `COMPUTER_USE_JPEG_QUALITY=75`、小图 PNG 阈值、zoom/crop/region 保真提示、自适应模型图片编码；小 PNG 原样保真，大 BMP/WebP 或超预算 PNG 走模型出口转码，大图默认 JPEG。
- 已修改 `observation.py` 传递图片 `source` 给编码层；已修改 `result_blocks.py` 和 `claudecode_bridge/wrapper.py` 的未知 MIME 兜底为 `image/jpeg`，更接近 ClaudeCode。
- 已通过聚焦测试：`python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41.WindowsComputerUseImageResultsPhase41Tests.test_agent_compresses_large_bmp_computer_use_screenshot_to_jpeg_model_image_block learning_agent.tests.test_windows_computer_use_image_results_phase41.WindowsComputerUseImageResultsPhase41Tests.test_evidence_store_preserves_bmp_payload_as_internal_artifact`，2 个测试通过。
- 已通过相关回归：`python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41 learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper`，19 个测试通过。
- 已按 AGENTS 规则三把本轮修改文件复制到 `learning_agent/test/computer_use_adaptive_image_20260616/`，作为用户学习备份。
- 尚未完成最终门禁：还需要 py_compile、完整 computer use 相关回归，以及 `start_oauth_agent.bat` 真实可见终端交互验收。

## 2026-06-16 Computer Use Adaptive Image Pipeline 验收补记

- 已修复真实 observe 链路发现的旧适配器路径漂移：工具结果里的 `mcp__computer-use__computer_batch\evidence` 路径可能不存在，而真实证据文件位于 `computer_use\evidence`；现在模型图片回灌前会自动修复到真实 artifact 路径。
- 已新增回归测试 `test_mcp_observe_image_block_repairs_legacy_adapter_evidence_path`，先复现 `block_count=0` 的问题，再验证修复后可生成模型可见图片块。
- 已通过相关回归：`python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41 learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper`，20 个测试通过。
- 已通过完整 v2 computer use 回归矩阵：`python -m unittest ...test_computer_use_mcp_v2_state_observe_action_loop`，116 个测试通过。
- 已通过 py_compile：`evidence.py`、`windows_runtime/evidence.py`、`image_messages.py`、`observation.py`、`result_blocks.py`、`wrapper.py`、`test_windows_computer_use_image_results_phase41.py`，以及 `learning_agent/test/computer_use_adaptive_image_20260616/` 下的 Python 备份文件。
- 真实可见终端验收已通过：控制器启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，在真实终端中输入 `/computer use --full` 和只读 observe prompt，生成 run `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal-20260616_213724\result.json`。
- 本次真实终端 run 的关键断言：`completed=true`、`assertion.passed=true`、`computer_use_mcp_v2_tool=true`、工具调用为 `mcp__computer-use__observe`、`permission_sent_count=0`、`real_desktop_touched=false`、`low_level_event_count=0`、最终回答为 `COMPUTER_USE_MCP_V2_OBSERVE_ADAPTIVE_IMAGE_OK`。
- 已复核最新工具结果 `learning_agent\debug_logs\tool_results\20260616_213741_mcp__computer-use__observe_eedb27cbc31b.txt`：可构建模型消息，`block_count=1`，内容类型为 `text + image_url`；当前窗口截图小于阈值，因此外发 PNG 保真，大图 JPEG 路径由自动化测试覆盖。
- CodeGraph 当前状态已复核为最新：`codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,245`、`Nodes 48,175`、`Edges 95,944`。

## 2026-06-16 Computer Use ClaudeCode Lifecycle Parity 蓝图

- 用户确认 Esc acquire/cleanup、完整 turn cleanup、standalone tools/list disabled 分支、displayResolvedForApps string key 四项都值得继续对齐 ClaudeCode。
- 已按 `superpowers:writing-plans` 创建长任务蓝图：`docs/superpowers/plans/2026-06-16-computer-use-claudecode-lifecycle-parity.md`。
- 蓝图明确不重写 Windows backend，只补 v2 MCP facade、ClaudeCode bridge 和 Windows session runtime 的连接处；内部保留 OpenHarness rich state，外部对齐 ClaudeCode 可观察协议字段。
- 蓝图包含 8 个执行任务：Esc 红测、Esc acquire lifecycle、统一 run_turn_cleanup、tools/list disabled、displayResolvedForApps key、wrapper cleanup 回归、文档/学习备份/记忆、自动化与真实可见终端验收。
- 蓝图自检已通过：UTF-8 正常，638 行，未发现 `TBD`、`TODO`、`implement later`、`fill in details`、`Modify later` 等占位词。

## 2026-06-16 Computer Use ClaudeCode Lifecycle Parity 执行记录

- 已完成 Esc acquire lifecycle：`ComputerUseMcpV2Context` 新增 Esc lifecycle 回调；`runtime.py` 在 acquire 成功后注册全局 Escape 急停；`WindowsComputerUseSessionRuntime` 接入 `GlobalEscapeAbortController`；`bind_session_context.py` 把 register/expected escape 回调传入 v2 context。
- 已完成统一 cleanup：`WindowsComputerUseSessionRuntime.cleanup_turn()` 改为委托 `run_turn_cleanup()`，覆盖 transient input release、hidden window restore、Esc hook unregister、lock release 和 abort clear，再合并 owned resource cleanup、residual check 和 notification。
- 已完成 standalone `tools/list` disabled：`mcpServer.py` 在 disabled/context-disabled 时返回 `tools: []`，不会加载 Windows app inventory，并记录 `computer_use_tools_list_app_inventory` trace，状态为 `disabled`。
- 已完成 `displayResolvedForApps` key 化：外部 `displayState.displayResolvedForApps` 为排序去重 string key，内部 rich records 保留在 `displayResolvedForAppsRecords` 与 context 的 `display_resolved_for_apps`。
- 已新增并通过聚焦测试：`test_computer_use_mcp_v2_escape_cleanup_parity`、`test_computer_use_mcp_v2_tools_list_disabled`、`test_computer_use_mcp_v2_display_resolved_key`；已更新并通过 `test_computer_use_mcp_v2_display_state`、`test_computer_use_mcp_v2_dynamic_tools_list`、`test_computer_use_mcp_v2_bridge_wrapper`。
- 执行中发现并修复一个 wrapper cleanup 接线缺口：轻量 runtime/fake runtime 没有 `lock_manager` 时，绑定层曾直接丢弃 `cleanup_turn`；现在即使无 lock manager，只要 runtime 暴露 `cleanup_turn`，也会绑定到 context。

## 2026-06-16 Computer Use ClaudeCode Lifecycle Parity 完成记录

- 已补齐真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal.json`，用于在真实 `start_oauth_agent.bat` 窗口中依次执行 `/computer use --full`、只读 `mcp__computer-use__observe`、`/computer cleanup learning-agent-default-session` 和最终标记确认。
- 已通过大范围 v2 computer use 回归：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_protocol_manifest learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_result_blocks learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_display_state learning_agent.tests.test_computer_use_mcp_v2_display_resolved_key learning_agent.tests.test_computer_use_mcp_v2_dynamic_tools_list learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled learning_agent.tests.test_computer_use_mcp_v2_escape_cleanup_parity learning_agent.tests.test_computer_use_mcp_v2_bridge_wrapper learning_agent.tests.test_computer_use_mcp_v2_contract learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_session_adapter learning_agent.tests.test_computer_use_mcp_agent_side_binding learning_agent.tests.test_computer_use_mcp_v2_architecture_docs learning_agent.tests.test_computer_use_mcp_v2_state_observe_action_loop learning_agent.tests.test_computer_use_tool_scope`，共 92 个测试通过。
- 已通过关键源码和学习备份 `py_compile`：覆盖 `types.py`、`runtime.py`、`bind_session_context.py`、`observation.py`、`session_runtime.py`、`coordinates.py`、`mcpServer.py`、新增/修改测试文件，以及 `learning_agent/test/computer_use_lifecycle_parity_20260616/` 下的 Python 备份。
- 已通过真实可见终端验收：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实输入 4 行 prompt，run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_computer_use_mcp_lifecycle_parity_visible_terminal-20260616_234022\result.json`。
- 本次真实终端 run 关键断言：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`、`computer_use_mcp_v2_tool=true`、`Computer Use Mode`、`full_mode=true`、`observe`、`Computer Runtime`、`cleanup_completed=true`、`Computer Recovery`、`computer_use_turn_cleanup_completed` 和最终回答 `COMPUTER_USE_MCP_V2_LIFECYCLE_PARITY_OK` 均出现。
- 已强制重建主目录 CodeGraph：`codegraph index --force .` 先清空旧索引再扫描 1260 个源码文件；随后 `codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,260`、`Nodes 48,491`、`Edges 159,608`。
- 已将本轮新增/修改文件、场景文件和真实终端验收结果复制到 `learning_agent/test/computer_use_lifecycle_parity_20260616/`，用于用户学习和后续复盘。

## 2026-06-17 Computer Use ClaudeCode 最新知识图谱对比审计

- 已按最新 CodeGraph 检查两个仓库：OpenHarness 为 `Files 1,260 / Nodes 48,491 / Edges 159,608`，ClaudeCode 为 `Files 1,902 / Nodes 43,685 / Edges 140,720`，两边 `codegraph status .` 均显示 `[OK] Index is up to date`。
- 已确认 ClaudeCode 仓库可见的 Computer Use 源码主要在 `utils/computerUse/`、`services/mcp/client.ts`、`components/permissions/ComputerUseApproval/ComputerUseApproval.tsx` 和 `state/AppStateStore.ts`；核心协议和调度仍来自外部 `@ant/computer-use-mcp`，该包源码不在当前 ClaudeCode 树内。
- 已确认 OpenHarness 当前总链路为：`mcp__computer-use__*` → `learning_agent/mcp/agent_adapter.py` → `claudecode_bridge/wrapper.py` → `inferred_ant_mcp/runtime.py` → `permissions/observation/actions/batch/clipboard/applications` → `legacy_ports.py` → `windows_runtime/mcp_session_adapter.py` → Windows controller / evidence / SendInput。
- 已运行 OpenHarness 内置 `claudecode_alignment_matrix`，当前输出为 `COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY level=CLAUDECODE_ALIGNMENT_PARTIAL aligned=11/14 partial=3 missing=0 visible_terminal_gate=false`。
- 本轮审计结论：OpenHarness 的公开 MCP 工具面、参数主字段、agent-side wrapper、content block 映射、lock/cleanup/display/tools-list disabled 等可观察协议已高度对齐 ClaudeCode；但不能声明“完全一致”，因为外部 `@ant/computer-use-mcp` 包内部不可逐行比对，且当前矩阵 CA07/CA13/CA14 仍为 partial。
- 本轮未做代码修改，也未执行规则十七真实可见终端交互验收；因此本轮只能输出审计结论，不能声明新的开发完成或验收通过。

## 2026-06-17 Computer Use ClaudeCode Windows Parity 书面蓝图

- 已按 `superpowers:writing-plans` 创建长任务防跑偏蓝图：`docs/superpowers/plans/2026-06-17-computer-use-claudecode-windows-parity-blueprint.md`。
- 蓝图确认优先继续对齐四类内容：真实 Windows 系统剪贴板读写、剪贴板 save/write/verify/paste/restore 合同、权限审批提示与拒绝路径、CA07/CA13/CA14 证据和可见终端 gate。
- 蓝图明确不做：复制外部 MCP 包内部实现、实现 macOS TCC/Swift helper、把 Windows 安全门禁改成 macOS 形态、一次性重写旧 v1/v2 所有适配层。
- 当前没有修改功能代码，也没有触发新的真实可见终端验收；下一步如果进入执行，应从蓝图 Task 1 冻结基线和 Task 2 剪贴板桥接失败测试开始。

## 2026-06-17 Computer Use ClaudeCode Windows Parity Blueprint

- 当前任务：按 `docs/superpowers/plans/2026-06-17-computer-use-claudecode-windows-parity-blueprint.md` 执行。
- 下一步：Task 1 冻结基线，Task 2 先写剪贴板桥接失败测试。
- 停止条件：真实系统剪贴板触及敏感内容、真实 GUI benchmark 需要操作用户私有数据、或可见终端无法人工确认。
- Task 1 已执行当前矩阵命令，输出为 `COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY level=CLAUDECODE_ALIGNMENT_PARTIAL aligned=11/14 partial=3 missing=0 visible_terminal_gate=false claudecode_parity=false claudecode_parity_or_better=false`。
- Task 1 已通过 CodeGraph 查询 `computer use clipboard request_access permissions alignment matrix visible terminal grantFlags WindowsProductionClipboardGuard`，确认 `clipboard.py` 仍是 context clipboard 为主，`permissions.py` 已有 `apps/grantFlags/sentinelWarnings` 基础结构，`claudecode_alignment_matrix.py` 的 CA07/CA13/CA14 仍需补证据和门禁。
- Task 2 已完成 Windows 系统剪贴板桥接：新增 `windows_runtime/system_clipboard.py`，`ComputerUseMcpV2Context` 增加 `clipboard_backend`，`bind_session_context.py` 默认绑定 `WindowsClipboardBackend`，`clipboard.py` 改为先检查 `clipboardRead/clipboardWrite` 再调用后端读写。
- Task 2 已通过聚焦测试：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_system_bridge`，3 个测试通过。
- Task 2 已通过相关回归：`python -m unittest learning_agent.tests.test_computer_use_mcp_batch_safety learning_agent.tests.test_computer_use_mcp_server learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_contract`，27 个测试通过。
- Task 2 已通过 py_compile：`system_clipboard.py`、`clipboard.py`、`types.py`、`bind_session_context.py`、`test_computer_use_mcp_v2_clipboard_system_bridge.py`。
- Task 2 已按规则三复制学习备份到 `learning_agent/test/computer_use_clipboard_system_bridge_20260617/`。
- Task 3 已完成剪贴板 save/write/verify/paste/restore 合同：`system_clipboard.py` 新增 `paste_text_with_restore()`，会先保存原剪贴板，写入临时文本，读回验证，验证通过才调用粘贴回调，最后无论成功失败都尽力恢复原文本。
- Task 3 已通过聚焦测试：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_restore_contract learning_agent.tests.test_computer_use_mcp_v2_clipboard_system_bridge`，5 个测试通过。
- Task 3 已用 CodeGraph 检查真实 SendInput 粘贴路径，确认 `real_sendinput_guard.py` 已有 `_clipboard_text/_set_clipboard_text/_paste_clipboard_text` 恢复链路；本任务暂不替换真实输入路径，避免扩大风险面。
- Task 3 已通过 py_compile：`system_clipboard.py`、`test_computer_use_mcp_v2_clipboard_restore_contract.py`。
- Task 3 已按规则三复制学习备份到 `learning_agent/test/computer_use_clipboard_restore_contract_20260617/`。
- Task 4 已完成权限审批提示对齐：新增 `inferred_ant_mcp/approval_prompt.py`，`permissions.py` 改为复用 `build_computer_use_approval_prompt()`，提示中稳定包含 `apps/applications/grantFlags/sentinelWarnings/reason`。
- Task 4 已通过聚焦测试和回归：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_permission_approval_prompt learning_agent.tests.test_computer_use_mcp_v2_permission_grants`，5 个测试通过。
- Task 4 已通过 py_compile：`approval_prompt.py`、`permissions.py`、`test_computer_use_mcp_v2_permission_approval_prompt.py`。
- Task 4 已按规则三复制学习备份到 `learning_agent/test/computer_use_permission_approval_prompt_20260617/`。
- Task 5 已完成 CA07/CA14 矩阵硬化测试：新增 `test_computer_use_mcp_v2_claudecode_alignment_matrix.py`，覆盖 CA07 两侧 token 对齐、CA14 无 gate 只能 partial、CA14 需要真实 run 目录才 aligned。
- Task 5 已在 `claudecode_alignment_matrix.py` 增加 `EXCLUDED_PLATFORM_DIFFERENCES`，把 macOS TCC、Swift helper、外部 MCP 包内部实现作为说明性排除项返回到机器报告和 Markdown 报告，但不改变 14 项矩阵分母。
- Task 5 已通过聚焦测试：`python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_alignment_matrix`，4 个测试通过。
- Task 5 已运行真实矩阵命令，当前仍为 `COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY level=CLAUDECODE_ALIGNMENT_PARTIAL aligned=11/14 partial=3 missing=0 visible_terminal_gate=false claudecode_parity=false claudecode_parity_or_better=false`，没有误升 parity。
- Task 5 已通过 py_compile：`claudecode_alignment_matrix.py`、`test_computer_use_mcp_v2_claudecode_alignment_matrix.py`。
- Task 5 已按规则三复制学习备份到 `learning_agent/test/computer_use_alignment_matrix_hardening_20260617/`。
- Task 6 已新增安全真实可见终端场景：`learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json`，场景只允许 `/computer use --full`、`request_access`、`list_granted_applications`、`write_clipboard`、`read_clipboard` 这一条安全链路，不允许登录页、用户文件、系统设置或真实窗口点击输入。
- Task 6 已验证场景 JSON 可解析：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json` 通过。
- Task 6 真实可见终端执行命令已确认：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath .\learning_agent\acceptance_controller\scenarios\agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json`；该命令将在 Task 7 最终验证门执行并生成 run 证据。

### Visible terminal acceptance steps

1. 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，或通过 `learning_agent\acceptance_controller\controller.ps1` 由控制器启动该 BAT。
2. 确认它是用户本地电脑上可见的真实终端窗口。
3. 在 agent 交互提示符输入场景 prompt，或由 controller 将 `prompt_lines` 逐行输入。
4. 观察终端输出是否出现 `COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK`。
5. 只有看到真实终端成功输出并生成 run 证据，才允许把 CA14 记为通过。

## 2026-06-17 Tool Surface ClaudeCode Parity

- 本轮按用户要求先改两点：`tool_search` 首轮常驻，`bash` 在代码开发模式首轮可见并可执行。
- 已按 TDD 先修改 `test_computer_use_tool_scope.py`，红灯确认当前代码模式和 Computer Use 源码开发模式缺少 `bash`、`tool_search`。
- 已修改 `learning_agent/tools/schemas.py`，把 `bash` 和 `tool_search` 加入 `KERNEL_TOOL_NAMES`。
- 已修改 `learning_agent/tools/tool_scope.py`，移除代码模式对 `bash` 的硬阻断，并把代码模式基础工具边界更新为 `read/write/edit/bash/tool_search`。
- 已同步 `learning_agent/tools/catalog.py`、`learning_agent/staticprompt/staticprompt.md`、`learning_agent/dynamicprompt/dynamicprompt.md`、`learning_agent/skills/tool_list.md`、相关 `SKILL.md` 和 README 里的旧四工具说明。
- 已通过聚焦验证：`python -m unittest learning_agent.tests.test_computer_use_tool_scope`，11 个测试通过。
- 已通过语法检查：`python -m py_compile learning_agent/tools/schemas.py learning_agent/tools/tool_scope.py learning_agent/tools/catalog.py learning_agent/tests/test_computer_use_tool_scope.py learning_agent/tests/test_tools_policy.py`。
- 已用真实 agent 快照确认普通代码模式首轮工具为 `bash,edit,read,tool_search,write`。
- 注意：`learning_agent.tests.test_tools_policy` 当前仍因既有导入错误 `ask_permission_from_terminal` 无法运行，不是本轮断言失败。
- 已完成规则十七真实可见终端交互验收：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，在真实终端输入工具面检查 prompt，run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_tool_surface_claudecode_parity_visible_terminal-20260617_103435\result.json`。
- 真实终端验收断言通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`、最终回答包含 `read/write/edit/bash/tool_search`，并明确 `mcp__computer-use__left_click` 在普通代码模式不可见，最终 marker 为 `TOOL_SURFACE_CLAUDECODE_PARITY_OK`。

## 2026-06-17 ToolToAPISchema Naming Entry

- 本轮按用户要求新增 ClaudeCode 同名记忆点：`toolToAPISchema`，让 OpenHarness 工具 schema 转换链路更容易被代码小白定位。
- 已按 TDD 先新增 `learning_agent/tests/test_tool_to_api_schema.py`，红灯确认 `learning_agent.tools.types` 和 `learning_agent.tools.pool` 原本都没有 `toolToAPISchema` 入口。
- 已在 `learning_agent/tools/types.py` 增加 `toolToAPISchema(tool)`，该函数只包装 `AgentTool.to_model_schema()`，不改变任何工具 schema 内容。
- 已在 `learning_agent/tools/pool.py` 将 `available_tool_schemas()` 改为调用 `toolToAPISchema(tool)`，让新名字进入真实 OpenAI API 工具 schema 发送链路。
- 已通过聚焦测试：`python -m unittest learning_agent.tests.test_tool_to_api_schema`，2 个测试通过。
- 已通过工具面回归：`python -m unittest learning_agent.tests.test_computer_use_tool_scope`，11 个测试通过；合并运行 `test_tool_to_api_schema + test_computer_use_tool_scope` 共 13 个测试通过。
- 已通过语法检查：`python -m py_compile learning_agent/tools/types.py learning_agent/tools/pool.py learning_agent/tests/test_tool_to_api_schema.py`。
- 已用真实 agent 快照确认首轮工具面仍为 `read,write,edit,bash,tool_search`，说明命名入口没有改变工具暴露行为。
- 已新增并校验真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_tool_to_api_schema_entry_visible_terminal.json`。
- 已完成规则十七真实可见终端交互验收：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实终端 run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_tool_to_api_schema_entry_visible_terminal-20260617_114025\result.json`。
- 真实终端验收断言通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`，最终回答包含 `toolToAPISchema`、`available_tool_schemas`、`read/write/edit/bash/tool_search` 和 marker `TOOL_TO_API_SCHEMA_ENTRY_OK`。

## 2026-06-17 FilteredTools Naming Entry

- 本轮按用户要求新增 ClaudeCode 同名记忆点：`filteredTools`，让 OpenHarness “过滤当前可用工具”的链路更容易和 ClaudeCode 的 `filteredTools` 对照。
- 已按 TDD 先新增 `learning_agent/tests/test_filtered_tools_naming.py`，红灯确认 `learning_agent.tools.pool` 和 `learning_agent.tools.catalog_runtime` 原本都没有 `filteredTools` 入口。
- 已在 `learning_agent/tools/pool.py` 增加 `filteredTools(catalog, decision_for_tool)`，并把旧 `current_tool_pool()` 改为委托 `filteredTools()` 的兼容包装。
- 已在 `learning_agent/tools/catalog_runtime.py` 增加 `filteredTools(agent)`，并把 `available_tool_schemas()` 改为先走 `filteredTools(agent)` 再转 schema。
- 已通过聚焦测试：`python -m unittest learning_agent.tests.test_filtered_tools_naming`，2 个测试通过。
- 已通过相关回归：`python -m unittest learning_agent.tests.test_filtered_tools_naming learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_computer_use_tool_scope`，15 个测试通过。
- 已通过语法检查：`python -m py_compile learning_agent/tools/pool.py learning_agent/tools/catalog_runtime.py learning_agent/tests/test_filtered_tools_naming.py`。
- 已用真实 agent 快照确认首轮工具面仍为 `read,write,edit,bash,tool_search`，并确认 `catalog_runtime.current_tool_pool(agent) == catalog_runtime.filteredTools(agent)`。
- OpenAI `defer_loading` 判断：官方 Responses API 支持 namespace/tool_search 形态的 `defer_loading`；当前 Chat Completions 链路暂不应直接混入该字段，后续若要完全对齐应新增 Responses API tool_search/namespace 链路。
- 已新增并校验真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_filtered_tools_entry_visible_terminal.json`。
- 已完成规则十七真实可见终端交互验收：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实终端 run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_filtered_tools_entry_visible_terminal-20260617_120011\result.json`。
- 真实终端验收断言通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`，最终回答包含 `filteredTools`、`current_tool_pool`、`available_tool_schemas`、`read/write/edit/bash/tool_search` 和 marker `FILTERED_TOOLS_ENTRY_OK`。
- 已按规则三复制学习备份到 `learning_agent/test/filtered_tools_naming_20260617/`。
- 已更新主目录 CodeGraph；最终 `codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,292`、`Nodes 49,002`、`Edges 60,471`。

## 2026-06-17 FilteredTools Only Removal Entry

- 本轮按用户进一步建议，删除 `current_tool_pool()` 旧名字，只保留 `filteredTools()`，避免同一功能两个名字让代码小白混淆。
- 已先创建书面迁移记录：`docs/superpowers/plans/2026-06-17-current-tool-pool-removal-record.md`。
- CodeGraph 审计结果：`codegraph callers current_tool_pool --limit 80` 返回 `No callers found for "current_tool_pool"`，说明 active 生产代码没有外部 caller。
- 已按 TDD 修改 `learning_agent/tests/test_filtered_tools_naming.py`，红灯确认 `learning_agent.tools.pool` 和 `learning_agent.tools.catalog_runtime` 仍公开旧名，然后删除生产旧名后绿灯通过。
- 已从 `learning_agent/tools/pool.py` 删除 `current_tool_pool(catalog, decision_for_tool)` 兼容包装，只保留 `filteredTools(catalog, decision_for_tool)`。
- 已从 `learning_agent/tools/catalog_runtime.py` 删除 `current_tool_pool(agent)` 兼容包装，只保留 `filteredTools(agent)`；`available_tool_schemas()` 继续使用 `filteredTools(agent)`。
- 已将 `learning_agent/tests/test_tools_policy.py` 的旧入口导入和调用替换为 `filteredTools`。
- 已更新真实终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_filtered_tools_entry_visible_terminal.json`，新 marker 为 `FILTERED_TOOLS_ONLY_ENTRY_OK`，验收目标改为确认旧名不再公开。
- 已通过相关回归：`python -m unittest learning_agent.tests.test_filtered_tools_naming learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_computer_use_tool_scope`，15 个测试通过。
- 已通过语法和场景校验：`python -m py_compile learning_agent/tools/pool.py learning_agent/tools/catalog_runtime.py learning_agent/tests/test_filtered_tools_naming.py learning_agent/tests/test_tools_policy.py`；`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_filtered_tools_entry_visible_terminal.json`。
- 已用真实 agent 快照确认首轮工具面仍为 `read,write,edit,bash,tool_search`，并确认 `pool_has_current_tool_pool=False`、`runtime_has_current_tool_pool=False`。
- 已用 active 路径搜索确认没有 `def current_tool_pool`、`import current_tool_pool` 或 `current_tool_pool as`。
- 已完成规则十七真实可见终端交互验收：controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，真实终端 run 为 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\agent_capability_filtered_tools_entry_visible_terminal-20260617_125615\result.json`。
- 真实终端验收断言通过：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`，最终回答确认 `current_tool_pool` 不再作为函数公开，`available_tool_schemas` 仍走 `filteredTools`，首轮工具面仍为 `read/write/edit/bash/tool_search`，marker 为 `FILTERED_TOOLS_ONLY_ENTRY_OK`。
- 已按规则三复制学习备份到 `learning_agent/test/filtered_tools_only_removal_20260617/`。
- 已更新主目录 CodeGraph；最终 `codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,296`、`Nodes 49,141`、`Edges 159,413`。
## 2026-06-17 OAuth Native Tools ClaudeCode Parity Blueprint

- 已创建书面蓝图：`docs/superpowers/plans/2026-06-17-openharness-oauth-native-tools-claudecode-parity.md`。
- 蓝图目标：让 OpenHarness 的 ChatGPT OAuth 后端链路对齐 ClaudeCode/Codex 风格原生 Responses tools，把工具真实放进顶层 `tools`，并解析 `function_call`、`tool_search_call`、`tool_search_output`。
- 当前只完成方案制定，尚未修改运行代码。
- 后续执行时必须先按蓝图 Task 1 冻结范围和证据，再逐项 TDD 执行。

## 2026-06-18 OAuth Native Tools Blueprint Strengthening

- 已按用户要求先补强蓝图，尚未执行代码修改。
- 补强文件：`docs/superpowers/plans/2026-06-17-openharness-oauth-native-tools-claudecode-parity.md`。
- 本次补强明确：该蓝图只负责 Computer Use 的模型协议层，不覆盖 Windows 桌面执行器、外部 MCP 包内部实现、macOS TCC/Swift helper。
- 已新增门禁：每轮重新计算 `filteredTools()`、deferred 工具集合和 Responses namespace；至少拆出 `computer_use` namespace；hosted `tool_search_call/tool_search_output` 必须被保留；Computer Use 图片/观察结果必须能进入下一轮 Responses `input_image`。
- 已新增 Task 2A：专门锁定 Computer Use namespace 和每轮 defer 判断。
- 已补强 Task 7 和 Task 8：真实 OAuth probe 必须看见原生 `tool_search_call/tool_search_output`，真实可见终端验收必须包含安全 Computer Use 权限类工具场景。
- 当前状态：等待用户确认蓝图后再执行实现任务。

## 2026-06-17 OAuth Native Tools ClaudeCode Parity Plan

- 计划文件：`docs/superpowers/plans/2026-06-17-openharness-oauth-native-tools-claudecode-parity.md`
- 当前阶段：Task 1，冻结协议证据和范围。
- 成功标准：OAuth native tools 模式下，工具真实出现在顶层 `tools`，模型返回原生 `function_call/tool_search_call/tool_search_output`，OpenHarness 能解析并执行 function_call。
- 停止条件：真实 OAuth 后端不再接受该格式、模型版本低于 `gpt-5.4`、或真实终端验收无法完成。

## 2026-06-18 OAuth Native Tools ClaudeCode Parity Execution

- 已完成 Task 1：把 OAuth native Responses tools 的范围、成功标准和停止条件写入 `agent_memory/context.md` 与本进度文件。
- 已完成 Task 2/2A：新增 `learning_agent/models/responses_native.py`，支持 Chat Completions function schema 转 Responses function、namespace、hosted `tool_search`、`defer_loading` 和 `computer_use` namespace。
- 已完成 Task 3/5：新增 Responses 原生 output item parser，并扩展 OAuth SSE parser 以保留 `response.output_item.done`、`response.function_call_arguments.delta`、`response.function_call_arguments.done` 和 `response.completed` 中的原生 output。
- 已完成 Task 4：`CodexOAuthChatModel` 增加 `CODEX_OAUTH_NATIVE_TOOLS` / `native_tools_enabled` 开关；开启时工具进入请求体顶层 `tools`，关闭时仍保留旧 `text.format=json_schema` 回退路径。
- 已完成 Task 6：`learning_agent/core/message_builders.py` 新增 native tool result builder，可生成 `function_call_output` 并把 Computer Use 图片消息转换为 Responses `input_image`。
- 已完成 Task 7 默认跳过 probe：`python -m unittest learning_agent.tests.test_codex_oauth_native_tools_probe` 结果为 `OK (skipped=1)`。
- 已完成 Task 7 真实 OAuth backend probe：`RUN_CODEX_OAUTH_NATIVE_TOOLS=1` 与 `CODEX_OAUTH_NATIVE_TOOLS=1` 下运行 `python -m unittest learning_agent.tests.test_codex_oauth_native_tools_probe`，结果为 `OK`，证明本机 ChatGPT OAuth 后端接受 hosted `tool_search` / namespace / `defer_loading` 并返回可解析的原生工具调用。
- 已完成 Task 8 验收资产：新增 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_tools_visible_terminal.json` 与 `learning_agent/acceptance_controller/scenarios/agent_capability_oauth_native_computer_use_visible_terminal.json`。
- 已补强 acceptance controller：`controller.ps1` 现在支持 scenario JSON 的 `environment` 字段，可以把 `CODEX_OAUTH_NATIVE_TOOLS=1` 传入真实可见终端启动链路。
- Task 8 真实可见终端自动验收未完成：controller 启动 `start_oauth_agent.bat` 后在聚焦真实终端窗口时失败，错误为 `无法聚焦真实终端窗口，停止发送文本。`，失败 run 目录为 `learning_agent/acceptance_controller/runs/agent_capability_oauth_native_tools_visible_terminal-20260618_101119/`。
- 已关闭本次半启动的 `LearningAgent-OAuthNativeTools-101119` cmd 窗口，避免后台继续等待输入。
- 已按规则三复制学习备份到 `learning_agent/test/oauth_native_tools_schema_20260617/`、`learning_agent/test/oauth_native_computer_use_namespace_20260617/`、`learning_agent/test/oauth_native_output_parser_20260617/`、`learning_agent/test/oauth_native_codex_body_20260617/`、`learning_agent/test/oauth_native_sse_parser_20260617/`、`learning_agent/test/oauth_native_tool_result_messages_20260617/`、`learning_agent/test/oauth_native_backend_probe_20260617/`、`learning_agent/test/oauth_native_visible_terminal_20260617/`。
- Task 9 稳定测试通过：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_responses_native_tool_result_messages learning_agent.tests.test_codex_oauth_native_tools_probe learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_filtered_tools_naming` 结果为 19 个测试通过，其中真实后端 probe 默认 skipped 1 个。
- Task 9 编译检查通过：`python -m py_compile learning_agent\models\responses_native.py learning_agent\models\adapters.py learning_agent\core\messages.py learning_agent\core\message_builders.py learning_agent\tests\test_responses_native_tool_schema.py learning_agent\tests\test_responses_native_output_parser.py learning_agent\tests\test_codex_oauth_native_tools_body.py learning_agent\tests\test_codex_oauth_native_sse_parser.py learning_agent\tests\test_responses_native_tool_result_messages.py learning_agent\tests\test_codex_oauth_native_tools_probe.py` 无输出。
- Task 9 controller 语法检查通过：PowerShell parser 对 `learning_agent/acceptance_controller/controller.ps1` 无语法错误。
- Task 9 蓝图原始门禁命令部分失败：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_models_codex_oauth` 中本轮 10 个 native 相关测试通过，但 `test_models_codex_oauth` 导入失败，错误是 `cannot import name 'ask_permission_from_terminal' from 'learning_agent.core.agent'`。
- Task 9 默认开关决策：不默认启用 OAuth native tools。理由是可见终端验收未完成，且蓝图原始大测试门禁仍受既有导入问题阻塞；当前必须继续显式设置 `CODEX_OAUTH_NATIVE_TOOLS=1` 才启用 native 模式。
- CodeGraph 状态：`codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,322`、`Nodes 49,700`、`Edges 158,044`。
- Commit 状态：本轮未执行 git commit。原因是当前工作树已有大量历史修改和未跟踪文件，直接提交会混入不属于本轮的改动；后续提交前应先由用户确认提交范围或在干净分支/工作树中整理。

## 2026-06-18 OAuth Native Debug Evidence Follow-up

- 已补齐模型响应 debug 证据链：`learning_agent/observability/debug_formatting.py` 的 `model_message_to_debug_dict()` 现在会把 `ModelMessage.native_output_items` 写入结构化 debug payload，避免 `tool_search_call` / `tool_search_output` 只停留在内存里。
- 已新增测试：`learning_agent/tests/test_responses_native_debug_logging.py`，先红灯确认缺少 `native_output_items` 字段，再绿灯确认原生 output items 和旧模式空列表都会进入 debug payload。
- 已通过 focused 回归：`python -m unittest learning_agent.tests.test_responses_native_debug_logging learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_probe`，结果为 5 个测试通过，其中真实后端 probe 默认 skipped 1 个。
- 已通过编译检查：`python -m py_compile learning_agent\observability\debug_formatting.py learning_agent\tests\test_responses_native_debug_logging.py` 无输出。
- 已按规则三复制学习备份到 `learning_agent/test/oauth_native_debug_logging_20260617/`。
- 已通过本轮最终 native 回归：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_responses_native_tool_result_messages learning_agent.tests.test_responses_native_debug_logging learning_agent.tests.test_codex_oauth_native_tools_probe learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_filtered_tools_naming`，结果为 21 个测试通过，其中真实后端 probe 默认 skipped 1 个。
- 已通过本轮最终编译检查：`python -m py_compile learning_agent\models\responses_native.py learning_agent\models\adapters.py learning_agent\core\messages.py learning_agent\core\message_builders.py learning_agent\observability\debug_formatting.py learning_agent\tests\test_responses_native_tool_schema.py learning_agent\tests\test_responses_native_output_parser.py learning_agent\tests\test_codex_oauth_native_tools_body.py learning_agent\tests\test_codex_oauth_native_sse_parser.py learning_agent\tests\test_responses_native_tool_result_messages.py learning_agent\tests\test_responses_native_debug_logging.py learning_agent\tests\test_codex_oauth_native_tools_probe.py` 无输出。
- 已恢复并刷新 CodeGraph：最终 `codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,325`、`Nodes 49,739`、`Edges 159,585`。
- 注意：真实可见终端交互验收仍未完成，原因仍是 controller 无法聚焦 `start_oauth_agent.bat` 启动的真实终端；因此仍不能声明本蓝图“开发完成/验收通过”，也不能默认开启 `CODEX_OAUTH_NATIVE_TOOLS`。

## 2026-06-18 OAuth Native Task 9 Compatibility Follow-up

- 已修复蓝图 Task 9 原始门禁中的既有导入阻塞：`learning_agent.core.agent` 重新兼容导出 `ask_permission_from_terminal`、`ask_permission_from_terminal_customer_mode`、`build_permission_event_payload`，真实实现仍委托 `learning_agent.app.terminal_permissions`。
- 已补齐 `LearningAgent` 旧私有工具 schema 兼容入口：`_tool_catalog()`、`_available_tool_schemas()`、`_available_responses_tool_schemas()`、`_tool_schema_names()`，真实逻辑仍委托 `learning_agent.tools.catalog_runtime`。
- 已更新 `learning_agent/tests/test_models_codex_oauth.py` 的过期断言：按用户已确认的新设计，`tool_search` 在 MCP select 后仍应常驻暴露给模型。
- Task 9 原始门禁已通过：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_models_codex_oauth`，结果为 59 个测试通过。
- Native 回归组已通过：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_responses_native_tool_result_messages learning_agent.tests.test_responses_native_debug_logging learning_agent.tests.test_codex_oauth_native_tools_probe learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_filtered_tools_naming`，结果为 21 个测试通过，其中真实后端 probe 默认 skipped 1 个。
- 编译检查已通过：`python -m py_compile learning_agent\core\agent.py learning_agent\models\responses_native.py learning_agent\models\adapters.py learning_agent\core\messages.py learning_agent\core\message_builders.py learning_agent\observability\debug_formatting.py` 无输出。
- 已按规则三复制学习备份到 `learning_agent/test/oauth_native_task9_compat_20260618/`。
- 当前剩余门禁：仍需重新执行 OAuth native tools 与 OAuth native Computer Use 两个真实可见终端场景；在该门禁通过前，不允许声明开发完成，也不允许默认开启 `CODEX_OAUTH_NATIVE_TOOLS`。

## 2026-06-18 OAuth Native ClaudeCode Streaming Follow-up

- 已按用户纠偏先读取 ClaudeCode CodeGraph：重点参考 `utils/api.ts::toolToAPISchema()`、`services/api/claude.ts` 的 `normalizeMessagesForAPI(messages, filteredTools)`、`utils/messages.ts::normalizeMessagesForAPI()`、`services/tools/toolExecution.ts::addToolResult()`、`StreamingToolExecutor` 和 `cli/transports/ccrClient.ts::accumulateStreamEvents()`。
- 已按 TDD 新增续轮协议测试：`test_native_tools_body_requests_encrypted_reasoning_for_stateless_turns`、`test_native_input_carries_reasoning_item_before_matching_function_call_output`、`test_native_tools_input_uses_concise_continuation_prompt_after_tool_result`。
- 已修复 `learning_agent/models/adapters.py`：native body 增加 `include: ["reasoning.encrypted_content"]`；native input 会按 call_id 回放 reasoning/tool_search/function_call 原生 item，再追加 `function_call_output`。
- 已修复 native 续轮 prompt：不再把整段 `messages` JSON dump 给模型，而是给出 `Original user request`、`Tool results` 和轻量 readable summary，避免工具返回后模型只输出空 reasoning。
- 已按 ClaudeCode accumulator 思路新增并修复 SSE parser 测试：`test_sse_parser_attaches_output_text_done_to_message_placeholder`，现在空 `message in_progress` 占位会合并 `output_text.done`，最终 `ModelMessage.text` 不再丢失。
- 聚焦测试通过：`python -m unittest learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_responses_native_tool_result_messages`，14 个测试通过。
- Native 回归通过：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_codex_oauth_native_sse_parser learning_agent.tests.test_responses_native_tool_result_messages learning_agent.tests.test_responses_native_debug_logging learning_agent.tests.test_codex_oauth_native_tools_probe learning_agent.tests.test_tool_to_api_schema learning_agent.tests.test_filtered_tools_naming learning_agent.tests.test_core_run_loop.CoreRunLoopTests.test_run_retries_empty_final_answer_once`，29 个测试通过，其中真实后端 probe 默认 skipped 1 个。
- 更大 OAuth/native 组合回归通过：`python -m unittest learning_agent.tests.test_responses_native_tool_schema learning_agent.tests.test_responses_native_output_parser learning_agent.tests.test_codex_oauth_native_tools_body learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_responses_native_tool_result_messages`，67 个测试通过。
- 编译检查通过：`python -m py_compile learning_agent\models\adapters.py learning_agent\models\responses_native.py learning_agent\core\message_builders.py learning_agent\core\agent.py learning_agent\tests\test_codex_oauth_native_tools_body.py learning_agent\tests\test_responses_native_tool_result_messages.py learning_agent\tests\test_codex_oauth_native_sse_parser.py`。
- 真实可见终端 OAuth native tools 验收已通过：`learning_agent/acceptance_controller/runs/agent_capability_oauth_native_tools_visible_terminal-20260618_123634/result.json`，最终回答包含 `Read README.md successfully.` 和 `OAUTH_NATIVE_TOOLS_OK`。
- 真实可见终端 OAuth native Computer Use 验收已通过：`learning_agent/acceptance_controller/runs/agent_capability_oauth_native_computer_use_visible_terminal-20260618_123710/result.json`，调用 `list_granted_applications`，最终回答 `OAUTH_NATIVE_COMPUTER_USE_OK`。
- 已按规则三复制学习备份到 `learning_agent/test/oauth_native_reasoning_sse_20260618/`。
- 已刷新并修复 CodeGraph：期间遇到一次 `database is locked` 和一次全量索引超时，已停止项目相关 CodeGraph daemon、移除陈旧锁并执行 `codegraph sync .`；最终 `codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,331`、`Nodes 50,132`、`Edges 50,608`。
# 2026-06-18 ClaudeCode vs OpenHarness Computer Use CodeGraph Audit

- 当前任务：基于最新 CodeGraph 审计 ClaudeCode Computer Use 与 OpenHarness Computer Use 的文件、源码、接口、数据和总链路，并输出对齐差异报告。
- ClaudeCode CodeGraph 状态：`Files 1,902 / Nodes 43,685 / Edges 140,720`，状态为最新。
- OpenHarness CodeGraph 状态：`Files 1,331 / Nodes 50,132 / Edges 50,608`，状态为最新。
- 当前执行边界：只做审计报告，不修改运行代码；如果后续进入开发修复，才需要按规则十七执行真实可见终端交互验收。
- 已完成 ClaudeCode 源码链路审计：`utils/computerUse/setup.ts`、`mcpServer.ts`、`wrapper.tsx`、`hostAdapter.ts`、`executor.ts`、`computerUseLock.ts`、`cleanup.ts`、`escHotkey.ts`、`toolRendering.tsx`、`services/mcp/client.ts` 和 `ComputerUseApproval.tsx`。
- 已完成 OpenHarness 源码链路审计：`inferred_ant_mcp/build_tools.py`、`runtime.py`、`types.py`、`bind_session_context.py`、`clipboard.py`、`permissions.py`、`observation.py`、`legacy_ports.py`、`claudecode_bridge/wrapper.py`、`mcpServer.py`、`learning_agent/mcp/agent_adapter.py`、`windows_runtime/mcp_session_adapter.py`、`session_runtime.py`、`turn_cleanup.py` 和锁实现。
- 本轮结论：OpenHarness 对齐了模型可见 24 工具面、`mcp__computer-use__` 前缀、主要 ClaudeCode 参数字段、MCP text/image content block、disabled tools/list 空结果、锁/cleanup/Esc 生命周期、display state 和旧接口禁止面；仍未完全一致的是隐藏外部包内部、权限 UI 体验、macOS TCC 与 Windows 权限差异、以及 Windows 侧 v2 facade 下仍复用 legacy session adapter/controller 的实现分层。

## 2026-06-18 Windows Computer Use Permission UI ClaudeCode Parity Blueprint

- 已按用户要求为“权限 UI 体验”单独制定 P0 对齐蓝图，文件为 `docs/superpowers/plans/2026-06-18-computer-use-windows-permission-ui-claudecode-parity.md`。
- 本轮只写蓝图和项目记忆，不修改运行代码；因此没有触发规则十七的真实可见终端开发验收。
- 蓝图结论：该项值得对齐，且优先级最高，因为它直接决定真实桌面控制前的用户可理解性、可拒绝性、可审计性和安全信任。
- 蓝图范围：只对齐 Windows 终端权限体验、结构化权限决策、grant flags、sentinel 风险提示、授权审计和真实终端验收；明确排除外部 MCP 包、macOS TCC、Swift helper 和底层执行链路重构。
- 后续执行顺序：先做 prompt UI 面板、结构化 decision、无交互默认拒绝、`request_access` payload 和真实终端验收；再做状态面板和深度审计增强。

## 2026-06-18 Windows Computer Use Permission UI ClaudeCode Parity Execution

- 已完成阶段 A：用 CodeGraph 和运行探针冻结旧链路，确认旧 `request_access` 成功/拒绝 payload 缺少 `decision/source/promptVersion/timestampUtc`，且无 `ask_permission` 回调时会默认允许。
- 已完成阶段 B：先写红灯测试 `test_computer_use_permission_ui_prompt.py`、`test_computer_use_permission_decision.py`，并扩展 `test_computer_use_mcp_v2_permission_grants.py`，覆盖终端权限面板、结构化决策、无回调默认拒绝和审计字段。
- 已完成阶段 C/D：实现终端权限面板与结构化权限决策模型，兼容旧 bool 回调，同时支持新 dict 决策、降权 grant flags、未知 flag 过滤和错误回调默认拒绝。
- 已完成阶段 E/F：`request_access`、`list_granted_applications`、Windows runtime approval 和 `/computer status` 已接入 `permission_prompt_version`、最近决策和拒绝计数。
- 已完成自动化验证：`python -m unittest learning_agent.tests.test_computer_use_permission_ui_prompt learning_agent.tests.test_computer_use_permission_decision learning_agent.tests.test_computer_use_mcp_v2_permission_grants learning_agent.tests.test_computer_use_mcp_v2_permission_approval_prompt learning_agent.tests.test_computer_use_mcp_v2_lock_lifecycle learning_agent.tests.test_computer_use_mcp_v2_primary_paths learning_agent.tests.test_computer_use_mcp_v2_tools_list_disabled learning_agent.tests.test_computer_use_mcp_v2_protocol_normalizer learning_agent.tests.test_windows_computer_use_approval_phase38 learning_agent.tests.test_windows_computer_use_security_policy_phase48 learning_agent.tests.test_computer_use_mcp_v2_sendinput_parity_task4`，结果为 45 个测试通过。
- 已完成编译检查：`python -m py_compile` 覆盖本轮修改的权限 prompt、decision、permissions、types、Windows runtime approval、旧 approval、status renderer 和新增/修改测试文件，结果无输出。
- 已按规则三复制学习备份到 `learning_agent/test/20260618_windows_permission_ui_claudecode_parity/`。
- 已完成真实可见终端验收：`powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_computer_use_permission_ui_visible_terminal.json` 通过，结果文件为 `learning_agent/acceptance_controller/runs/agent_capability_computer_use_permission_ui_visible_terminal-20260618_145426/result.json`。
- 本轮真实终端验收关键事实：`completed=true`、`permission_required=true`、`permission_answered=true`、`computer_use_mcp_v2_tool=true`、`request_access` 和 `list_granted_applications` 均出现、`permission_prompt_version=windows-permission-ui-v1` 出现在 `/computer status`、最终回答为 `COMPUTER_USE_PERMISSION_UI_VISIBLE_TERMINAL_OK`。
- CodeGraph 已刷新并确认最新：`codegraph sync .` 显示 Already up to date，`codegraph status .` 显示 `[OK] Index is up to date`，统计为 `Files 1,345`、`Nodes 50,356`、`Edges 51,545`。

## 2026-06-18 ClaudeCode Computer Use Source Recheck

- 已按用户要求重新基于 `D:\ClaudeCode-main\ClaudeCode-main` 的 CodeGraph 复核 ClaudeCode Computer Use 源码，确认该仓库 CodeGraph 状态为 `[OK] Index is up to date`，统计为 `Files 1,902 / Nodes 43,685 / Edges 140,720`。
- 本轮结论边界：ClaudeCode 源码内可确认 `utils/computerUse/*`、`ComputerUseApproval.tsx`、`main.tsx`、`services/mcp/client.ts`、`services/mcp/config.ts`、`state/AppStateStore.ts`、`query.ts`、`query/stopHooks.ts` 等链路；`@ant/computer-use-mcp`、`@ant/computer-use-input`、`@ant/computer-use-swift` 内部实现不在该目录源码内，不能逐行确认。
- 已修正对齐判断：权限 UI、锁/清理/Esc、MCP 名称与工具渲染、session state、多显示器状态、app 名称过滤、macOS 执行器都能在源码中找到；持久化授权、独立状态命令、完整审计账本、Windows 底层控制、外部包内部 tool schema/dispatch 只能作为 OpenHarness 对齐目标或接口痕迹，不能说是 ClaudeCode 当前源码已有完整实现。

## 2026-06-18 Hermes Computer Use CodeGraph Borrowing Audit

- 已按用户要求读取 `D:\hermes-agent-main` 的 CodeGraph，确认该项目 `.codegraph` 存在且状态为 `[OK] Index is up to date`，统计为 `Files 3,479 / Nodes 96,525 / Edges 238,893`。
- Hermes Computer Use 主要源码链路为 `tools/computer_use_tool.py`、`tools/computer_use/schema.py`、`tools/computer_use/tool.py`、`tools/computer_use/backend.py`、`tools/computer_use/cua_backend.py`、`tools/computer_use/vision_routing.py`、`agent/prompt_builder.py`、`cli.py::_computer_use_approval_callback` 和对应测试/文档。
- 关键边界：Hermes 自己的模型可见 schema、调度、安全审批、截图多模态回传、辅助视觉路由和 backend 抽象都在仓库源码内；但底层 macOS 执行依赖外部 `cua-driver mcp`，这属于外部驱动/运行时依赖，不等同于 ClaudeCode 那类无法逐行验证的隐藏完整 MCP 包。
- 借鉴方向初判：OpenHarness 不应替换现有 ClaudeCode 风格 24 个 MCP 工具面和权限层；更值得借鉴 Hermes 的 SOM/AX 编号元素观察、`capture_after` 动作后复查、`max_elements` 输出上限、`app` scoped 观察、辅助视觉路由、统一 backend result 数据模型和模型提示词工作流。

## 2026-06-18 Cua Driver Windows Computer Use Borrowing Blueprint

- 已按用户要求把 Hermes 外部 `cua-driver` 源码可借鉴点整理成书面长任务蓝图，文件为 `docs/superpowers/plans/2026-06-18-cua-driver-windows-computer-use-borrowing.md`。
- 蓝图核心结论：`cua-driver` 在角色上类似外部 Computer Use MCP driver，但现在源码已下载并进入 `D:\hermes-agent-main` CodeGraph，因此不是不可验证黑盒；OpenHarness 可以借鉴其 Windows 底层执行思想，但不应替换 ClaudeCode-compatible 24 工具面。
- 蓝图范围：元素索引缓存、UIA/MSAA 语义动作、窗口本地坐标契约、严格 `pid + window_id` 校验、后台/no-focus dispatch 诊断、UIPI/integrity 诊断、observe-act-verify 证据链。
- 蓝图边界：不引入 `cua-driver` 作为强依赖，不照搬 macOS Swift/SkyLight，不绕过 OpenHarness 权限 UI、lock、abort、cleanup 和审计，不声称 ClaudeCode 隐藏外部包内部已完全确认。
- 蓝图验收门禁：每阶段先 CodeGraph 复核，先写失败测试，再实现，再跑自动化测试和编译检查；最终必须通过 `learning_agent/start_oauth_agent.bat` 真实可见终端验收，否则不能声明开发完成。

## 2026-06-18 Cua Driver Borrowing Execution Phase 0

- 已启动长期目标：逐项完成 `docs/superpowers/plans/2026-06-18-cua-driver-windows-computer-use-borrowing.md` 的所有任务。
- 已按 `executing-plans` 技能复读蓝图，并按 `using-git-worktrees` 技能检查隔离工作区要求；当前分支为 `codex/publish-main`，不是 `main/master`，且当前工作区已有大量历史未提交改动，因此本轮继续在当前工作区小范围修改，避免创建不含当前变更的新 worktree 导致基线丢失。
- OpenHarness CodeGraph 状态：`Files 1,345 / Nodes 50,356 / Edges 51,545`，结果为 `[OK] Index is up to date`。
- Hermes CodeGraph 状态：`Files 3,828 / Nodes 103,394 / Edges 260,538`，结果为 `[OK] Index is up to date`；提示索引由旧版本构建，但当前查询可用。
- 已用 CodeGraph 重新探索 OpenHarness 目标链路：`legacy_ports.py`、`mode_session.py`、`real_sendinput_guard.py` 等仍是当前 Computer Use v2/Windows runtime 关键路径。
- 已用 CodeGraph 重新探索 Cua Driver 参考链路：确认 `ToolRegistry`、MCP protocol/server、Windows `get_window_state`、元素缓存、点击/输入/set_value、UIPI/输入诊断仍是主要参考对象。

## 2026-06-18 Cua Driver 借鉴 Phase 3
- 已完成 Windows 坐标合同与目标身份严格匹配模块。
- 新增并通过 learning_agent.tests.test_computer_use_windows_coordinate_contract。
- 已回归 Phase 1/2 元素索引缓存与观察帧集成测试。
- 已备份 Phase 3 新增文件到 learning_agent/test/cua_driver_borrowing_phase3_coordinate_identity_20260618。

## 2026-06-18 Cua Driver 借鉴 Phase 4
- 已完成 Windows UIA Pattern 语义分发模块，覆盖 Invoke、Toggle、Value、RangeValue 后备路径。
- 新增并通过 learning_agent.tests.test_computer_use_windows_uia_patterns。
- 已回归 Phase 1-3 相关测试。
- 已备份 Phase 4 新增文件到 learning_agent/test/cua_driver_borrowing_phase4_uia_patterns_20260618。

## 2026-06-18 Cua Driver 借鉴 Phase 5
- 已完成 Windows UIPI/完整性等级诊断模块，覆盖等级排序、低权限到高权限后台派发阻断、目标不可用优先解释。
- 新增并通过 learning_agent.tests.test_computer_use_windows_integrity。
- 已回归 Phase 1-4 相关测试。
- 已备份 Phase 5 新增文件到 learning_agent/test/cua_driver_borrowing_phase5_integrity_20260618。

## 2026-06-18 Cua Driver 借鉴 Phase 6
- 已扩展 ComputerUseMcpV2Context，新增 element_cache、semantic_action_dispatcher、integrity_diagnostic_provider、last_observation_target。
- 已在 MCP v2 actions.perform_action 中接入 element_index 缓存命中后的 UIA 语义 Pattern 优先路径，成功时返回 before/after evidence 与 verified 字段。
- 新增并通过 learning_agent.tests.test_computer_use_cua_driver_observe_act_verify。
- 已回归 MCP v2 权限、displayResolvedForApps、Esc cleanup 相关测试。
- 已备份 Phase 6 修改文件到 learning_agent/test/cua_driver_borrowing_phase6_observe_act_verify_20260618。

## 2026-06-18 Cua Driver 借鉴 Phase 7/8
- Phase 7 鼠标热区/录制类 UI 调试增强为可选项，已按蓝图边界暂不接入；核心行为链路优先完成。
- 已新增 Cua Driver Windows Computer Use 借鉴最终矩阵、manifest、Markdown 报告和真实可见终端 scenario。
- 已修正 MCP stdio registry 测试：用只读 list_granted_applications 替代无交互 request_access，避免与当前权限 UI 默认拒绝策略冲突。
- 已通过本轮最终自动化测试 53 项和本轮文件 py_compile。
- 全量 compileall learning_agent 仍受既有历史备份文件 learning_agent/test/computer_use_full_desktop_task_router_task3_20260605/core_agent_task3_clean_index.py 第 4 行缩进错误影响，不属于本轮改动。
- 已备份 Phase 8 新增/修改文件到 learning_agent/test/cua_driver_borrowing_phase8_matrix_visible_terminal_20260618。

## 2026-06-18 Cua Driver 借鉴最终验收
- 真实可见终端验收已完成并通过：learning_agent/acceptance_controller/runs/agent_capability_cua_driver_borrowing_visible_terminal-20260618_170814/result.json。
- 矩阵已回填 visible_terminal_gate=true，并记录 final_visible_run_dir。
- 最终源码、测试、场景、报告、manifest、蓝图和 result 已备份到 learning_agent/test/cua_driver_borrowing_final_20260618。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收准备
- 已新增真实可见终端场景：learning_agent/acceptance_controller/scenarios/agent_capability_cua_driver_real_windows_production_visible_terminal.json。
- 场景组合验证 Cua Driver 借鉴矩阵与受控真实 Notepad 编辑链路，最终要求 CUA_DRIVER_WINDOWS_PRODUCTION_ACCEPTANCE_OK、CUA_DRIVER_WINDOWS_BORROWING_OK、PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、saved_file_verified=true、real_desktop_touched=true、real_gui_backing=true 同时出现。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收结果
- 已按用户确认执行真实 Windows 链路生产化验收：使用 acceptance controller 启动 learning_agent/start_oauth_agent.bat 可见终端窗口，并由 controller 向真实 agent 交互提示符输入生产化验收 prompt。
- 第一次 run 证明 Cua Driver 矩阵和受控 Notepad 真实编辑命令均执行成功，但场景误要求当前命令不会输出的 real_gui_backing=true，因此断言失败；该问题已记录为场景断言错误，不是底层 Windows 链路失败。
- 已修正场景断言，改为校验当前命令真实输出的生产证据：real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。
- 修正后真实可见终端验收已通过：learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_172608/result.json。
- 本次通过证据：completed=true、prompt_sent=true、prompt_received=true、final_printed=true、assertion.passed=true、marker_passed=true、permission_sent_count=0。
- 最终回答和可读日志均包含：CUA_DRIVER_WINDOWS_PRODUCTION_ACCEPTANCE_OK、CUA_DRIVER_WINDOWS_BORROWING_OK、PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。

## 2026-06-18 Cua Driver 真实 Windows 生产化验收复验
- 为避免只复述旧 run，本轮最终回答前重新执行 acceptance controller，命令为 powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_cua_driver_real_windows_production_visible_terminal.json。
- 复验已通过，最新结果文件为 learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_173128/result.json。
- 最新复验证据：completed=true、prompt_sent=true、prompt_received=true、final_printed=true、assertion.passed=true、marker_passed=true、permission_count_passed=true、permission_sent_count=0。
- 最新可读日志显示真实 agent 调用 bash，命令 exit_code=0，并输出 CUA_DRIVER_WINDOWS_BORROWING_OK、PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、real_notepad_edit_executed=true、notepad_process_verified=true、saved_file_verified=true、real_desktop_touched=true。

## 2026-06-18 Windows Computer Use 生产验收矩阵蓝图
- 已按用户要求制作书面详细蓝图，文件为 docs/superpowers/plans/2026-06-18-windows-computer-use-production-acceptance-matrix.md。
- 蓝图目标：把当前单点真实 Windows 验收扩展为可重复执行的 production acceptance matrix，覆盖 Cua Driver Notepad 链路、权限允许、权限拒绝、Notepad、Calculator、Explorer、本地浏览器、多应用传递、失败恢复和长任务恢复。
- 蓝图关键决策：先审计现有 controlled CLI 的真实输出，再修正 Phase148C 场景中的 stale token，尤其不能继续要求 CLI 未输出的 real_gui_backing=true。
- 蓝图新增产物范围：matrix manifest、PowerShell matrix runner、安全权限拒绝 scenario、manifest 单元测试、用户说明文档、学习归档和项目记忆更新。
- 已完成蓝图自检：搜索 TBD、TODO、implement later、placeholder 等计划占位词，无匹配。

## 2026-06-18 Windows Computer Use 生产验收矩阵 Task 1 审计
- 已启动长期目标：逐项完成 docs/superpowers/plans/2026-06-18-windows-computer-use-production-acceptance-matrix.md 的所有任务，直到矩阵实现、真实可见终端验收、学习归档和项目记忆更新全部完成。
- 已按 CodeGraph 审计 acceptance controller、受控 Windows runtime 和 Phase148C 场景入口；当前工作区继续在 codex/publish-main 上小范围修改，因为当前任务依赖本工作区已有未提交的 Computer Use 前置成果。
- 已真实运行 Notepad controlled CLI，通过且输出 PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK、real_notepad_edit_executed=true、notepad_process_verified=true、target_rechecked_before_input=true、target_rechecked_before_save=true、saved_file_verified=true、real_desktop_touched=true；该 CLI 不输出 real_gui_backing=true。
- 已真实运行 Calculator controlled CLI，首次发现当前 Windows Calculator 对键盘 ADD 路径不稳定，表现为 Expression is 1=、Display is 1，根因不是场景断言而是派发路径与当前 Calculator UIA/键盘语义不匹配。
- 已修正 Calculator controlled driver：优先使用 UIA InvokePattern 点击 One、Plus、One、Equals；新增并通过 learning_agent.tests.test_windows_computer_use_controlled_calculator_live_sum_phase137，随后真实 CLI 输出 PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK、observed_result_matches_expected=true、uia_invoke_sequence_used=true、real_desktop_touched=true。
- 已真实运行 Explorer controlled CLI，通过且输出 real_gui_backing=true、filesystem_changed_after_real_actions=true、cleanup_completed=true。
- 已真实运行 local_browser controlled CLI，通过且输出 PHASE139_CONTROLLED_BROWSER_LIVE_LOCAL_PAGE_OK、page_changed_after_real_click=true、screenshot_before_after_different=true、browser_automation_used=false、real_desktop_touched=true；该 CLI 不输出 real_gui_backing=true。
- 已真实运行 multi_app_transfer、failure_recovery、long_task_resume controlled CLI，三者均通过并输出 real_gui_backing=true；这些场景当前可保留 real_gui_backing=true 断言。

## 2026-06-18 Windows Computer Use 生产验收矩阵完成
- 已完成蓝图全部任务：修正 Phase148C stale token、新增 Calculator UIA Invoke 优先路径、新增生产矩阵 manifest、新增一键 runner、新增权限拒绝真实终端场景、新增用户说明文档、新增单元测试，并完成学习归档。
- 新增矩阵入口：learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1。
- 新增矩阵 manifest：learning_agent/acceptance_controller/windows_computer_use_production_matrix.json。
- 新增权限拒绝场景：learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_permission_denial_visible_terminal.json。
- 新增用户文档：docs/computer_use_windows_production_acceptance.md。
- 最新真实可见终端矩阵已通过：learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-20260618_183954/matrix_result.json。
- 通过证据：passed=true、scenario_count=10、passed_count=10、failed_count=0；10 条场景覆盖 Cua Driver Notepad、权限允许、权限拒绝、Notepad、Calculator、Explorer、本地浏览器、多应用传递、失败恢复和长任务恢复。
- runner 曾遇到两个基础设施问题并已收敛：Windows PowerShell 5.1 读取无 BOM 中文注释导致解析失败，已转换为 UTF-8 BOM；连续 GUI 场景过快切换导致焦点/Explorer 抖动，已在 runner 场景前后加入保守沉淀等待，不降低任何断言。
- 最终自动化验证已通过：python -m unittest learning_agent.tests.test_windows_computer_use_controlled_calculator_live_sum_phase137 learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v，共 8 项通过；py_compile、JSON 解析和 runner parser 均通过。

## 2026-06-18 OAuth Native Tools 默认开启
- 用户确认为了提升 OpenHarness agent 能力，值得把 Codex OAuth Responses 原生 tools 链路设为真实终端默认开启。
- 已修改 learning_agent/start_oauth_agent.ps1：当用户未显式设置 CODEX_OAUTH_NATIVE_TOOLS 时，默认设置为 1；如果用户提前设置 0/false/off 等非空值，脚本不会覆盖，保留旧 JSON 工具协议回退能力。
- 已新增学习摘录 learning_agent/test/oauth_native_default_enabled_20260618.md，记录新增 PowerShell 代码和设计原因。

## 2026-06-18 OAuth Native + Computer Use 真实终端验收
- 用户要求使用 acceptance controller 控制真实可见终端窗口，输入真实 prompt 验收 OAuth native tools 与 Computer Use 回填链路。
- 已执行 agent_capability_oauth_native_tools_visible_terminal，结果为 completed=true、assertion.passed=true、marker_passed=true，run 为 learning_agent/acceptance_controller/runs/agent_capability_oauth_native_tools_visible_terminal-20260618_195120/result.json。
- 已执行 agent_capability_oauth_native_computer_use_visible_terminal，结果为 completed=true、assertion.passed=true、marker_passed=true，证明真实终端进入 Computer Use full mode 后可调用 list_granted_applications，run 为 learning_agent/acceptance_controller/runs/agent_capability_oauth_native_computer_use_visible_terminal-20260618_195146/result.json。
- 已执行 agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal，结果为 completed=true、assertion.passed=true、marker_passed=true，证明真实终端可调用 mcp__computer-use__observe 并产出 screenshot_path 与 image_result_count=1，run 为 learning_agent/acceptance_controller/runs/agent_capability_computer_use_mcp_observe_adaptive_image_visible_terminal-20260618_195224/result.json。
- 三个场景的 startup_screenshot、prompt_screenshot、final_screenshot 均已生成；最后一张 final screenshot 已人工视觉检查，确认是目标 LearningAgent 真实终端窗口而非空截图。

## 2026-06-18 Computer Use 旧目录删除与 v2 内聚迁移
- 已按用户要求删除 learning_agent/computer_use 旧目录，避免后续调试时模型继续误读旧实现为当前主链路。
- 已将仍被 v2 主链路消费的三个模块迁入 learning_agent/computer_use_mcp_v2/windows_runtime：windows_element_cache.py、windows_coordinate_contract.py、windows_uia_patterns.py。
- 为保持既有 Cua Driver 借鉴矩阵与完整性合同测试可运行，额外从学习副本恢复并迁入 v2 内部：cua_driver_borrowing_matrix.py、windows_integrity.py；它们不是主动作链路活依赖，但属于当前验收合同支持模块。
- 已更新 v2 生产导入点：inferred_ant_mcp/actions.py 与 windows_runtime/universal_real_observation.py 不再引用 learning_agent.computer_use 或 computer_use.*。
- 已新增迁移护栏测试 learning_agent/tests/test_computer_use_mcp_v2_legacy_folder_removed.py，门禁旧目录不存在、三个 v2 模块可导入、v2 主链路无旧导入。
- 已批量迁移 learning_agent/tests 中旧 computer_use 导入、动态 importlib 字符串、mock patch 字符串和场景断言字符串到 learning_agent.computer_use_mcp_v2.windows_runtime。
- 自动化验证已通过：39 项相关单元测试通过、py_compile 通过、cua_driver_borrowing_matrix CLI 输出 CUA_DRIVER_WINDOWS_BORROWING_OK。
- 测试模块导入巡检显示 IMPORT_FAILURE_COUNT=0；主代码和测试旧路径扫描只剩护栏测试中的禁止片段。
- 按 Windows Computer Use 技能安全规则，本轮未自动化真实终端输入；真实可见终端交互验收未完成，不能声明开发完成。

## 2026-06-18 Computer Use v2 旧目录删除真实终端补验
- 用户提醒应使用 OpenHarness 自带 acceptance controller，而不是 Windows Computer Use 插件去控制终端；该提醒正确，本轮已补跑真实可见终端验收。
- 新增场景：learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_mcp_v2_legacy_folder_removed_visible_terminal.json。
- acceptance controller 已启动 learning_agent/start_oauth_agent.bat 真实可见终端窗口，并向 agent 输入真实 prompt。
- 最新通过 run：learning_agent/acceptance_controller/runs/agent_capability_computer_use_mcp_v2_legacy_folder_removed_visible_terminal-20260618_202959/result.json。
- 通过证据：completed=true、prompt_sent=true、prompt_received=true、final_printed=true、assertion.passed=true、marker_passed=true、permission_sent_count=0。
- agent 在真实终端中调用 bash，命令 exit_code=0；输出包含 Ran 24 tests、OK、CUA_DRIVER_WINDOWS_BORROWING_OK、passed=true、cua_inspired_element_cache_present=true、uia_semantic_dispatch_present=true、coordinate_contract_present=true。
- 最终回答最后一行是 COMPUTER_USE_MCP_V2_LEGACY_FOLDER_REMOVED_OK，本轮真实可见终端交互验收已通过。

## 2026-06-18 Computer Use 压力测试适配性检查
- 本轮按项目规则先使用 CodeGraph 检查 Computer Use 当前主链路，确认当前索引状态为 up to date：files=359、nodes=7990、edges=21191。
- 当前源码静态检查通过：python -m compileall -q learning_agent\computer_use_mcp_v2 learning_agent\acceptance_controller 返回成功。
- 当前生产矩阵 manifest 仍存在 10 条受控场景，且所有场景文件均能在 learning_agent/acceptance_controller/scenarios 下找到；manifest 仍要求 visible_terminal_required=true 与 screenshot_artifacts_required=true。
- 当前磁盘没有找到历史记录中提到的 latest matrix result：learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-20260618_183954/matrix_result.json；runs 目录当前未列出 production matrix 运行目录。
- 当前 learning_agent/tests 目录为空，历史记录中提到的 Computer Use 单元测试模块导入失败，说明当前工作树的回归测试证据链已经断开。
- 结论：当前适合先做受控预压力测试或重新跑生产矩阵，不适合直接做高强度、泛化、多应用或长时间 soak 压力测试。

## 2026-06-18 Computer Use 压力测试前置修复
- 已基于 CodeGraph 和当前源码修复场景旧包路径：acceptance_controller/scenarios 中 learning_agent.computer_use. 已迁移到 learning_agent.computer_use_mcp_v2.windows_runtime.
- 已修复通用 type_text 链路：只有底层 sender 明确 requires_raw_text=True 时才把原文传到内存低层事件，公开结果仍保持脱敏。
- 已新增 learning_agent/tests/test_computer_use_pressure_readiness.py 回归测试，并复制学习副本到 learning_agent/test/1.py、2.py、3.py、4.md。
- 自动化验证已通过：旧路径扫描、compileall、unittest、Phase37、Phase47、Phase52、CUA borrowing。
- 真实可见终端交互验收尚未完成，不能声明开发完成。

## 2026-06-18 Notepad 拖动保存压力测试执行
- 已完成：桌面 C:\Users\joyzq\Desktop\1.txt 预检通过，执行前不存在。
- 已完成：新增 Notepad 拖动保存压力测试 scenario、验证器与单元测试；相关 unittest 5 项通过，compileall 通过。
- 已启动：acceptance_controller 真实可见终端 run，路径为 learning_agent/acceptance_controller/runs/codex_notepad_drag_save_20260618_223255/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260618_223256。
- 已停止：本轮真实验收触发安全停止条件。Notepad 启动后恢复了标题为 *Jan项目的后端是否可以改成使用Qwen3.6-12B-IQ-Q8_0 - Notepad 的已有窗口，agent 随后对该窗口执行了 CTRL+A 与 type_text。
- 当前结论：本轮压力测试失败，未进入 3 轮连续压力、焦点扰动或已有文件失败门禁。

## 2026-06-19 通用 Computer Use FreshTarget/TargetLease 治本方案执行
- 已完成通用 FreshTarget 策略模块、controller 预检、多目标 registry、TargetLease 新鲜度字段、UniversalTargetSession 启动后分类、漂移失效恢复、actionability 输出、重复 launch_app 前置拒绝和缺 target_ref 写动作前置拒绝。
- 已新增/更新目标测试：FreshTarget policy、controller gate、多目标 registry、proxy binding、TargetLease gate、action gate target_ref、agent_tools redundant launch gate；最新目标 pytest 结果为 31 passed。
- 已完成 py_compile：fresh_target_policy.py、controller.py、universal_target_session.py、target_lease.py、target_registry.py、agent_tools.py、action_gates.py 均通过。
- 已更新动态提示词、架构文档、FreshTarget 可见终端场景、Notepad 拖动保存压力场景、Windows Computer Use 生产矩阵；相关 JSON 均通过解析。
- 已将本轮核心代码、测试、场景和文档副本复制到 learning_agent/test，便于用户学习对照。
- CodeGraph 已同步，最新状态：files=415、nodes=9165、edges=24827、status=OK/up to date。
- 真实可见终端验收：agent_capability_computer_use_fresh_target_policy_visible_terminal 已通过，result.json 路径为 learning_agent/acceptance_controller/runs/agent_capability_computer_use_fresh_target_policy_visible_terminal-20260619_072430/result.json。
- Notepad 拖动保存压力场景仍未通过：第一次 run 证明 FreshTarget/TargetLease 已零事件拒绝旧窗口动作，但最终回答未输出验收 marker；第二次 run 首次 launch_app 成功并返回 target_ref_one_to_one=true，后续模型反复 launch_app，压力场景超时，未创建 Desktop\1.txt。
- 当前阻塞：真实 Notepad 压力场景未通过，因此不能声明开发完成；需要在用户关闭当前 Notepad 残留窗口后，重跑压力场景并确认最终 marker 与 Desktop\1.txt 文件证据。

## 2026-06-19 FreshTarget 旧窗口用户动作阻断收敛修复
- 已确认真实失败证据：latest_run_readable.md 中 `open_application notepad` 返回 `existing_target_window_requires_user_close_or_authorize`、`low_level_event_count=0`，但上层模型继续重复调用 `open_application`，说明底层 FreshTarget 正确、收敛层未把结果转成“必须用户关闭或授权”的终止态。
- 已新增回归测试 `learning_agent/tests/test_fresh_target_user_action_required_convergence.py`，覆盖用户动作 marker 记录为 `actionability_last_block`、不保存 pending、重复 `open_application` 被 `fresh_target_user_action_required` 阻断。
- 已更新 `learning_agent/core/actionability_state.py`：新增 `OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED` marker、用户动作阻断状态、重复桌面工具阻断判断和最终答复提示。
- 已更新 `learning_agent/core/convergence_controller.py`：模型调用前遇到用户动作阻断会注入“不要继续工具，最终回答用户”的提醒；模型仍调用同一应用启动/桌面动作时会返回合成阻断输出。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/controller.py`：FreshTarget 预检拒绝旧窗口时输出用户动作 marker，并把恢复动作改为 `ask_user_to_close_or_authorize`，不再建议继续 `observe`/`launch_app`。
- 自动化验证已通过：新增收敛测试 2 passed；FreshTarget controller 与新增收敛测试 6 passed；Computer Use 相关目标测试 36 passed；完整 `learning_agent/tests` 50 passed；修改文件 py_compile 退出码 0。
- CodeGraph 已同步，最新状态：files=432、nodes=9587、edges=26076、status=OK/up to date。
- 真实可见终端旧窗口安全拒绝验收已通过：acceptance controller run `learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_092813/result.json` 显示 completed=true、assertion.passed=true、alternate_success_checks.dirty_state_safe_refusal.passed=true。
- 验收证据：最终回答包含“不能默认接管”“明确授权”“low_level_event_count=0”“successful_action_count=0”；debug log 中 `open_application` 输出 `OPENHARNESS_DESKTOP_USER_ACTION_REQUIRED`、`retry_launch_allowed=false`、`recovery_next_allowed_actions=['ask_user_to_close_or_authorize']`、`low_level_event_count=0`。
- 干净新窗口完整拖动保存路径未执行：当前用户旧 Notepad 窗口仍打开，按安全策略不能由 agent 自动关闭；需要用户手动关闭后才能跑创建 Desktop\1.txt 的 clean-state 压力验收。

## 2026-06-19 Proxy PID TargetLease 与 observe target_ref 修复
- 已修复启动 PID 与真实窗口 PID 不一致导致的租约误拒绝：`target_lease.py` 现在会从嵌套 `launch_result` 补齐进程身份，并对 `agent_owned_proxy_window` 使用真实窗口 `pid + hwnd` 做一对一动作前验证。
- 已修复 `target_lease_not_verified` 后仍允许反复 `launch_app` 的恢复建议：`fresh_target_policy.py` 对该原因只允许 `observe` 与错误报告，不再建议直接重启应用。
- 已修复 `observe` 默认窗口被前台终端带偏的问题：`mcp_session_adapter.py` 现在优先读取 controller `target_registry.get_active_target()`，并把 `target_ref` 注入 legacy observe 参数。
- 新增/更新回归测试：proxy pid 租约测试、target_lease_not_verified 停止重复启动测试、observe active target_ref 测试。
- 自动化验证已通过：新增目标测试 15 passed；相关 Computer Use 目标测试 25 passed；修改文件与学习副本 py_compile 均通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_proxy_pid_*`。
- 真实可见终端验收已通过旧窗口安全拒绝路径：`learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_103036/result.json` 显示 `completed=true`、`assertion.passed=true`；最终回答要求用户关闭或授权当前旧 Notepad，未默认接管旧窗口。
- 干净新窗口完整拖动保存路径仍未跑通：当前仍有 PID 39660、标题 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad` 的旧 Notepad 窗口打开；按安全策略不能由 agent 自动关闭，需要用户手动关闭后重跑 clean-state 验收。

## 2026-06-19 通用 ResourceFreshness 与 target_ref 动作链修复
- 已确认真实失败证据：clean-state Notepad 验收 run `20260619_104142` 中 `launch_app` 首次成功并返回 `target_ref_one_to_one=true`，但后续 `key/left_click` 因动作参数缺 `target_ref` 被 `target_ref_required_for_bound_window_action` 拒绝，模型随后反复 `open_application`，未创建 Desktop\1.txt。
- 已新增 RED/GREEN 回归测试：单 active target 自动补 `target_ref`、恢复旧文档资源时后续写动作零事件阻断、多 active target 漏 `target_ref` 零事件拒绝、资源新鲜度 helper 区分旧文档与新空白文档。
- 已更新 `mcp_session_adapter.py`：动作路径接入 registry 单目标隐式解析，单 active target 自动补顶层 `target_ref`；多 active target 时直接返回 `multiple_active_targets_require_target_ref`，不触发底层事件；observe 保存 `last_resource_freshness`，旧资源状态会阻断后续 type/key/click。
- 已更新 `resource_identity.py`：新增通用 `build_resource_freshness` 和 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED` marker，不做 Notepad 专用逻辑，只按文档类应用、目标资源 hint、空白标题和是否要求新资源判断。
- 已更新 `actionability_state.py`：收敛层识别资源用户动作 marker，并把 `resource_freshness_decision` 纳入低敏字段白名单。
- 自动化验证已通过：新增/相关测试 6 passed；完整 `python -m pytest learning_agent/tests -q` 为 58 passed；`py_compile` 覆盖 mcp_session_adapter.py、resource_identity.py、actionability_state.py 均通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_resource_freshness_*`。
- 真实可见终端验收已通过旧窗口安全拒绝路径：`learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_112514/result.json` 显示 completed=true、assertion.passed=true、alternate_success_checks.dirty_state_safe_refusal.passed=true。
- 验收前置事实：桌面 `1.txt` 不存在，但仍有 PID 34500、标题 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad` 的旧 Notepad 窗口；因此本次验收不是 clean-state 保存成功，而是证明 agent 未默认接管旧窗口且 `low_level_event_count=0`。
- CodeGraph 已同步，最新状态：files=445、nodes=9950、edges=26969、status=OK/up to date。
- 当前状态：代码修改、自动化测试和旧窗口安全拒绝可见终端验收完成；clean-state 创建/拖动/保存 Desktop\1.txt 成功路径仍需用户关闭旧 Notepad 后复跑。

## 2026-06-19 ResourceFreshness action 兜底修复
- 已按用户手动关闭旧 Notepad 后重跑真实可见终端验收：run `learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_113358/result.json` 失败，`completed=false`、`permission_sent_count=42`、`Desktop\1.txt` 未创建。
- 失败证据：验收前没有 Notepad 进程且桌面 `1.txt` 不存在；`open_application notepad` 后绑定新窗口 PID 40628，但窗口标题恢复为 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`，说明问题不是启动 PID/真实 PID，而是新进程恢复旧文档资源。
- 根因定位：`mcp_session_adapter._call_action` 只读取 `state.last_resource_freshness`；当 observe 没写入资源新鲜度状态时，后续 `key/type/click` 不会根据动作窗口标题兜底判断旧资源，导致动作可穿透。
- 已新增 RED/GREEN 回归测试：`test_action_blocks_restored_document_resource_when_observe_state_is_missing` 先失败于 `result["ok"] is True`，修复后通过，证明测试覆盖真实穿透缺口。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：单 active target 自动补 `target_ref` 时同步 registry `target_lease`；action 入口在缺少 observe 资源状态时，根据 agent-owned 目标上下文和窗口标题文件名重新计算 `ResourceFreshness`，旧文件资源未授权时返回 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`，`low_level_event_count=0`。
- 已更新 Notepad 拖动保存压力验收场景：新增 `restored_resource_safe_refusal` 备用安全分支，只在日志/事件包含资源阻断 marker、`resource_freshness_decision=restored_existing_resource_requires_new_blank_or_authorization` 和 `low_level_event_count=0` 时通过；完整保存成功路径仍必须输出 `NOTEPAD_DRAG_SAVE_PRESSURE_OK`。
- 自动化验证已通过：新增单测先 RED 后 GREEN；相邻测试 7 passed；完整 `python -m pytest learning_agent/tests -q` 为 59 passed；`py_compile` 通过；场景 JSON 通过 `python -m json.tool`。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_action_resource_freshness_mcp_session_adapter.py`、`20260619_action_resource_freshness_test_mcp_session_adapter_observe_target_ref.py`、`20260619_action_resource_freshness_notepad_drag_save_pressure_scenario.json`。
- CodeGraph 已同步，最新状态：files=447、nodes=10061、edges=27259、status=OK/up to date。
- 当前可见终端验收：因为上一轮失败验收留下 PID 40628 的 Notepad 旧文档窗口，本轮 `20260619_115543` 走“已有旧窗口安全拒绝”分支并通过，`completed=true`、`assertion.passed=true`、`permission_sent_count=3`、`event_count=17`、未创建 `Desktop\1.txt`。
- 剩余门禁：要验证新修的“关闭后新启动但恢复旧资源”真实可见终端分支，需要用户再次手动关闭当前 PID 40628 Notepad 后重跑；若 Notepad 仍恢复旧 `.md` 文档，应通过新增 `restored_resource_safe_refusal` 分支；若 Notepad 打开空白文档，才可能继续完整拖动保存成功路径。

## 2026-06-19 显式 target_ref 多目标资源门禁修复
- 用户已手动关闭旧 Notepad 后，重跑真实可见终端验收 `20260619_120326` 失败：`completed=false`、`permission_sent_count=41`、`Desktop\1.txt` 未创建，验收残留窗口标题为 `2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`。
- 失败证据：本轮日志显示 `launch_app` 已绑定 fresh target，后续第一步 `key CTRL+A` 对旧资源标题窗口产生 `low_level_event_count=4`；日志中没有 `computer_use_mcp_resource_freshness_action_checked` 或 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`，说明 action 级资源门禁没有拿到动作窗口。
- 已新增 RED/GREEN 回归测试：`test_explicit_target_ref_resolves_window_before_resource_gate_when_multiple_targets_exist` 先失败于资源 marker 缺失，修复后通过；该测试覆盖“多个 active target + 模型显式 target_ref 指向旧资源窗口”的真实绕行路径。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：MCP 原始 action 参数会保留 `target_ref/window/target_window`；显式 `target_ref` 会先通过 registry 解析成一对一窗口并注入 `target_lease`，再进入多目标门禁和 `ResourceFreshness` 门禁。
- 自动化验证已通过：新增单测 RED 后 GREEN；`python -m pytest learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py -q` 为 7 passed；完整 `python -m pytest learning_agent/tests -q` 为 61 passed；`python -m py_compile learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py` 通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_explicit_target_ref_resource_fallback_mcp_session_adapter.py` 和 `learning_agent/test/20260619_explicit_target_ref_resource_fallback_test_mcp_session_adapter_observe_target_ref.py`。
- 下一步：需要同步 CodeGraph，并在用户已关闭 Notepad 的前置条件下重跑 acceptance controller 真实可见终端验收；只有验收通过后才可声明开发完成。

## 2026-06-19 observe 真实窗口标题刷新与 action 资源门禁重判修复
- 已确认真实失败证据：clean-state 验收 run `20260619_123050` 首次 `open_application notepad` 成功绑定新窗口 PID 40268，launch 快照标题为 `Notepad`，但后续 observe 已看到标题变成 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；adapter 仍保存旧 launch 快照，导致后续 action 没有用真实标题触发 ResourceFreshness 阻断。
- 已新增 RED/GREEN 回归测试：`test_observe_actual_window_title_replaces_launch_snapshot_before_action_resource_gate` 先失败于 `last_observed_window["title_preview"] == "Untitled - Notepad"`，修复后通过，证明 observe 返回的真实窗口标题会覆盖启动快照。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：从旧 observe 文本的 `数据：{...}` 安全解析真实 `state.window`，再合并 target_ref/target_lease 上下文；action 前对空资源报告或普通 observe 报告重新执行 ResourceFreshness 判断，避免“普通允许状态”盖住后续旧资源标题。
- 自动化验证已通过：定向新测 1 passed；`python -m pytest learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py -q` 为 8 passed；完整 `python -m pytest learning_agent/tests -q` 为 62 passed；`py_compile` 通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_observed_window_refresh_resource_gate_mcp_session_adapter.py` 和 `learning_agent/test/20260619_observed_window_refresh_resource_gate_test_mcp_session_adapter_observe_target_ref.py`。
- CodeGraph 已同步，最新状态：files=451、nodes=10317、edges=27936、status=OK/up to date。
- 真实可见终端 clean-state 验收未执行：前置检查发现仍有 Notepad PID 40268，标题为 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；桌面 `1.txt` 不存在。按安全策略不自动关闭用户 Notepad，需要用户手动关闭后复跑 acceptance controller。

## 2026-06-19 Acceptance Event 资源拒绝证据增强
- 用户关闭 Notepad 后重跑真实可见终端验收 `agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_131603`，功能行为已符合安全预期：启动前无 Notepad，启动后 Notepad 自动恢复旧 `.md` 文档，第一下 `key CTRL+N` 被 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED` 拒绝，`low_level_event_count=0`，最终回答要求用户关闭或明确授权旧窗口。
- 本轮失败点不是底层安全门禁，而是验收事件 payload 证据不足：`events.jsonl` 的 `computer_use_mcp_v2_tool` 只包含 `tool_name` 和 `ok=false`，scenario 的 `restored_resource_safe_refusal.event_payload_contains` 无法看到资源 marker。
- 已新增 RED/GREEN 回归测试：`test_acceptance_event_includes_resource_user_action_summary` 先失败于 `KeyError: 'error_class'`，修复后通过，覆盖资源用户动作拒绝时验收事件必须包含 `error_class`、`reason`、`resource_freshness_decision` 和 `low_level_event_count`。
- 已更新 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`：新增低敏事件摘要 helper，只裁剪记录失败 reason 和 key=value 字段，不改变工具执行、权限或窗口控制逻辑。
- 自动化验证已通过：新增单测 1 passed；相关回归 9 passed；完整 `python -m pytest learning_agent/tests -q` 为 63 passed；`py_compile` 通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_acceptance_event_evidence_runtime.py` 和 `learning_agent/test/20260619_acceptance_event_evidence_test_computer_use_mcp_v2_runtime_acceptance_event.py`。
- 当前真实验收前置阻塞：上一轮安全拒绝留下 Notepad PID 41340，标题为 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；需要用户手动关闭后复跑 acceptance controller。
- 用户再次手动关闭 Notepad 后，真实可见终端验收 `learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_133024/result.json` 已通过，`completed=true`、`assertion.passed=true`、`alternate_success_checks.restored_resource_safe_refusal.passed=true`。
- 验收结论：当前 Notepad 在干净启动后仍自动恢复旧 `.md` 文档，agent 按安全策略拒绝 `key CTRL+N` 写动作，event payload 包含 `OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED`、`resource_freshness_decision=restored_existing_resource_requires_new_blank_or_authorization`、`low_level_event_count=0`，最终回答要求用户关闭或授权旧窗口。
- 注意：本次通过的是 restored-resource 安全拒绝验收，不是完整创建/拖动/保存 `Desktop\1.txt` 成功路径；若后续要验收完整保存，需要 Notepad 真正打开空白文档，或用户明确授权使用当前旧文档窗口。
- 用户再次手动关闭 Notepad 后复跑 `learning_agent/acceptance_controller/runs/agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal-20260619_133557/result.json`，结果仍为 `completed=true`、`assertion.passed=true`、`dirty_state_safe_refusal.passed=true`、`restored_resource_safe_refusal.passed=true`。
- 复验证据：启动前无 Notepad、桌面 `1.txt` 不存在；启动后 Notepad 再次自动恢复 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`，agent 拒绝写动作并输出 `low_level_event_count=0`、`successful_action_count=0`；桌面 `1.txt` 仍不存在。

## 2026-06-19 ResourcePreparation 通用新空白资源控制层
- 已按用户确认的通用治本方案实施：不再把 `Ctrl+N` 当普通写动作一律拒绝，而是在旧资源恢复阻断状态下，仅允许带“新建空白资源”明确意图的 `CTRL+N` 作为受控准备动作。
- 新增状态机 `resource_preparation_pending`：准备动作成功后，后续任何输入/点击/保存动作都会被零事件拒绝，直到 agent 先调用 `observe` 确认同一个 target_ref/window 已经变成新空白资源。
- 该方案不是 Notepad 特判：核心判断位于 `mcp_session_adapter.py`，以 `ResourceFreshness`、`target_ref`、agent-owned lease、窗口身份、标题从旧文件资源变为通用空白候选等事实做通用确认。
- 已新增 RED/GREEN 回归测试：`test_safe_new_blank_shortcut_runs_on_restored_resource_then_blocks_typing_until_observe` 与 `test_typing_after_safe_new_blank_shortcut_is_allowed_after_observe_confirms_blank_resource`；修复前失败于 `Ctrl+N` 被旧资源门禁误挡，修复后通过。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：新增 `OPENHARNESS_DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED` marker、Ctrl+N 安全准备动作识别、pending 匹配、observe 参数补强、空白/标题变化确认和 observe-required 结果。
- 已更新 `learning_agent/core/actionability_state.py`：收敛层识别 `OPENHARNESS_DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED` 为 pending observe，不把它当用户终止阻断；并允许 observe 走 adapter active target 自动绑定，避免缺 `target_ref` 被过度拦截。
- 自动化验证已通过：新测试 3 passed；`test_mcp_session_adapter_observe_target_ref.py` 回归 10 passed；完整 `python -m pytest learning_agent/tests -q` 为 66 passed；`py_compile` 覆盖修改实现、收敛层和测试文件通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_resource_preparation_mcp_session_adapter.py`、`20260619_resource_preparation_test_mcp_session_adapter_observe_target_ref.py`、`20260619_resource_preparation_actionability_state.py` 和 `20260619_resource_preparation_test_fresh_target_user_action_required_convergence.py`。
- 下一步：同步 CodeGraph，并在用户手动关闭当前 Notepad 后，用 acceptance controller 跑真实可见终端验收，确认 agent 能在 Notepad 自动恢复旧 `.md` 后执行受控 `Ctrl+N`、observe 空白、再输入/拖动/保存或给出可收敛安全结果。

## 2026-06-19 ResourcePreparation Ctrl+N reason 兜底修复
- 已确认真实失败证据：visible-terminal run `20260619_140506` 中启动前无 Notepad，`open_application notepad` 新启动 PID 23324 并返回 `fresh_target_ready`，但 Windows 11 Notepad 自动恢复 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；随后 `key` 被 `desktop_resource_user_action_required` 拒绝，未进入 ResourcePreparation。
- 根因已修复：`mcp_session_adapter._is_safe_new_blank_resource_preparation_action()` 之前要求 reason 必须包含“新建空白/blank document”等精确词；真实模型常只写“按快捷键创建一个新的编辑页”，导致 `CTRL+N` 在旧资源恢复门禁下仍被误挡。
- 本轮修改：在 `restored_existing_resource_requires_new_blank_or_authorization` + 文档类资源 + agent-owned 窗口 + `CTRL+N` 同时成立时，把 `CTRL+N` 本身视为受控新空白资源准备动作；动作成功后仍会写入 `resource_preparation_pending`，要求下一步必须 `observe` 确认，不能直接输入。
- 新增 RED/GREEN 回归测试：`test_ctrl_n_is_allowed_as_preparation_even_when_reason_lacks_blank_words` 先失败于 `result["ok"] is False`，修复后通过。
- 自动化验证已通过：`python -m pytest learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py -q -k reason_lacks_blank_words` 为 1 passed；完整相关文件 11 passed；完整 `python -m pytest learning_agent/tests -q` 为 67 passed；`py_compile` 通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_resource_preparation_reason_fallback_mcp_session_adapter.py` 和 `learning_agent/test/20260619_resource_preparation_reason_fallback_test_mcp_session_adapter_observe_target_ref.py`。
- 真实可见终端验收仍未完成：当前仍有 Notepad PID 23324，标题为 `*2026-06-18-computer-use-notepad-drag-save-pressure-test.md - Notepad`；按安全策略不能由 agent 自动关闭，需要用户手动关闭后重跑 acceptance controller。

## 2026-06-19 ControlledResourceLaunch 源头资源绑定启动修复
- 已确认根因不是 Notepad 被判定为危险应用，也不是 PID/HWND 一对一绑定失效；真实失败证据显示 `open_application notepad` 能启动并绑定新窗口，但 Windows 11 Notepad 会在新窗口里恢复旧 `.md` 标签页。
- 治本方向改为复用受控 Notepad driver 的成功模式：文档类任务如果明确要求桌面 `1.txt`，启动层必须执行“应用 + 受控文件路径”的 argv 启动，而不是先裸启动再依赖模型 `Ctrl+N` 补救。
- 已新增 RED/GREEN 回归测试：controller 必须把 `C:\Users\joyzq\Desktop\1.txt` 传给 target runtime；UniversalTargetSessionRuntime 必须把受控路径写入 Phase108 `launch_plan.arguments`；MCP session adapter 必须把 request_access 的完整任务上下文补给 open_application。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/controller.py`：新增 `ControlledResourceLaunch` 资源路径解析，只对已验证支持文本 argv 的应用放行，未知应用保持原通用启动方式。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/universal_target_session.py`：新增受控资源注入函数，把文件路径写入 `launch_plan.arguments`，让 Phase110 后端从源头按文件启动。
- 已更新 `learning_agent/computer_use_mcp_v2/windows_runtime/mcp_session_adapter.py`：保存 request_access 授权原因，并在模型调用 open_application 时补齐 `session_task_context`，避免短 reason 丢失“保存到桌面 1.txt”的真实意图。
- 自动化验证已通过：新增测试先 RED 后 GREEN；`python -m pytest learning_agent/tests -q` 结果为 71 passed；修改文件 `py_compile` 通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_controlled_resource_launch_*`。
- 下一步：同步 CodeGraph，并在确认没有残留 Notepad 窗口后，通过 acceptance controller 运行真实可见终端验收；只有真实终端路径也通过，才可声明开发完成。

## 2026-06-19 ControlledResourceContext 脱敏资源上下文贯通修复
- 已确认上一轮源头资源绑定仍未覆盖真实终端失败：visible-terminal run 中 `request_access.reason` 被模型压缩成“不含 1.txt”的授权理由，`open_application` 的 `session_task_context` 为空，导致 controller 没机会生成 `Desktop\1.txt` argv 启动。
- 已补充 RED/GREEN 回归测试：分类器必须从真实中文 prompt 脱敏提取 `controlled_resource_name=1.txt` 和 `controlled_resource_location_hint=desktop`；legacy host 必须把 agent 上下文同步进 MCP session state；adapter 必须在模型短 reason 丢文件名时仍把资源字段传到底层启动参数。
- 已额外覆盖真实时序缺口：`/computer use --full` 可能先创建并复用 v2 context，真实任务 prompt 后到；`ComputerUseMcpV2LegacyHostAdapter` 现在每次调用旧 adapter 前都会从当前 agent 刷新脱敏资源上下文。
- 已更新 `desktop_task_router.py`、`core/agent.py`、`legacy_ports.py`、`mcp_session_adapter.py` 和新增 `test_controlled_resource_context_propagation.py`；学习副本已复制到 `learning_agent/test/20260619_controlled_resource_context_*`。
- 自动化验证已通过：新增测试 4 passed；相邻 Computer Use 回归 20 passed；完整 `python -m pytest learning_agent/tests -q` 为 75 passed；`py_compile` 覆盖本轮修改文件通过。
- 下一步：同步 CodeGraph；真实可见终端验收仍需在用户手动关闭当前残留 Notepad 后运行 acceptance controller，确认真实主循环从源头打开受控桌面 `1.txt` 而不是旧 `.md` 标签页。

## 2026-06-19 AutoObserveRecovery 主循环自动观察恢复
- 已按 `2026-06-19-claudecode-inspired-computer-use-runtime-recovery-and-cleanup.md` 的通用方案实施第一阶段：不再只靠动态提示词要求模型下一轮 observe，而是在 `LearningAgent.run_events` 工具结果回填阶段检测 `desktop_observe_before_action` pending 并合成一次协议合法的 `mcp__computer-use__observe`。
- 本轮新增 `learning_agent/core/actionability_recovery.py`，只做纯状态决策和预算计数；它拒绝用户动作阻断、缺 `target_ref`、非 observe pending 和超过预算的重复恢复，避免绕过 FreshTarget 或多窗口绑定。
- 本轮更新 `learning_agent/core/agent.py`：自动恢复会先追加 assistant tool_call，再执行 observe，再回填 tool result 和截图来源，保持模型工具协议配对；恢复事件通过 `computer_use_auto_recovery_observe`、标准 `tool_use_seen/tool_result_seen` 和 runtime trace 暴露。
- 已新增 RED/GREEN 测试：`test_actionability_auto_observe_recovery.py` 覆盖恢复计划、用户阻断硬停止和预算；`test_agent_auto_observe_recovery_loop.py` 覆盖模型只请求 `key` 时主循环自动补 `observe`。
- 当前自动化验证已通过：新增测试 4 passed；FreshTarget/target_ref 相邻回归 10 passed。下一步继续运行更完整测试、`compileall`、CodeGraph sync/status 和 acceptance controller 真实可见终端验收。

## 2026-06-19 Computer Use 验收默认自动同意权限
- 用户确认可承受风险，希望 Computer Use 压力测试不要反复输入 `Y`。
- 证据确认 `start_oauth_agent.ps1` 已默认设置 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1`，但多个 acceptance scenario 又显式覆盖成 `0`，导致 controller 反复代输 `Y`。
- 已将普通 Computer Use 压力测试场景的 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS` 改为 `1`，仅保留 `permission_ui` 和 `permission_denial` 专用场景为 `0`。
- 新增回归测试 `test_non_permission_ui_computer_use_scenarios_default_to_auto_approval`，防止普通压力测试场景重新关闭自动同意。
- 新增可见终端 smoke 场景 `computer_use_auto_approval_visible_terminal_smoke.json`；真实验收 run `computer_use_auto_approval_visible_terminal_smoke-20260619_192920` 通过，`permission_sent_count=0`、`permission_required=false`、`permission_auto_approved=true`。

## 2026-06-19 Universal Stage Planner 书面方案
- 已根据用户确认的方向新增通用 Computer Use 书面实施方案：`docs/superpowers/plans/2026-06-19-universal-computer-use-stage-planner-observer-batch-executor.md`。
- 方案明确以 ClaudeCode 风格的权限、锁、清理、底层执行器作为运行时底座，以 OpenHarness 的通用阶段规划、阶段边界观察、批量执行、阶段验收和最终门禁作为上层能力。
- 方案刻意禁止在核心实现里按 Notepad、Paint、浏览器、微信、WPS 等单个应用写特判；这些应用只能作为代表性验收样本或启动别名，不作为产品架构分支。
- 当前尚未改运行时代码；下一步若用户确认执行，应使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 按方案逐项实现，并在完成后做真实可见终端验收。

## 2026-06-19 Universal Stage Runtime 执行进度
- 已按书面方案实现通用 Stage 数据模型：`ActionBatch`、`StagePlan`、`DesktopTaskPlan`、`StageResult` 和 `DesktopTaskRunState`，并补充 JSON round-trip 测试。
- 已新增通用能力画像层：从观察帧抽象文本输入、画布、菜单、工具栏、保存界面、浏览导航、弹窗和未知能力，不在核心逻辑里按 Notepad/Paint/浏览器做分支。
- 已新增通用阶段规划器、阶段批编译器、批执行器和阶段验证器，支持文本、绘图、导航、多目标和未知 GUI 的通用阶段表示。
- 已将 `UniversalDesktopExecutionLoopAdapter` 的真实 full-mode 路径接入 `UniversalStageTaskLoop`，旧 `UniversalObservePlanActVerifyLoop` 保留为兼容路径。
- 已新增最终回答门禁：当 Computer Use 阶段任务未完成、阶段数量不一致、出现 `Next desktop action` 或需要用户处理时，模型不能把任务直接 final 成完成。
- 已新增多目标阶段测试和三份 representative acceptance scenario，scenario 使用具体本地软件作为验收样本，但运行时仍保持通用目标窗口/能力/阶段设计。
- 下一步继续运行完整方案要求的 focused/regression/full 测试、CodeGraph sync/status 和真实可见终端 acceptance controller 验收。

## 2026-06-19 Universal Stage Runtime desktop_task 桥接与新资源门禁补强
- 已补齐 `desktop_task` 高层 MCP 工具链路：工具 schema 暴露、scope 放行、runtime dispatch、acceptance 证据复制、legacy host adapter 和默认 runtime mode store 对齐。
- 已修复高层工具被模型调用后返回 `scope_blocked`、`not_desktop_task`、`computer_use_full_mode_required` 的三段源头问题：`desktop_task` 现在由显式工具入口强制进入通用 Stage runtime，并读取与 `/computer use --full` 相同的 mode session store。
- 已保持通用设计：`desktop_task` 的 `target_hint` 从授权应用上下文中提取，但 stage planner/compiler 不写 Notepad、Paint、浏览器或其它单软件分支。
- 已新增通用 FreshResource 门禁：文本、绘图和多窗口写入目标的 `prepare_target` 阶段声明 `fresh_resource_required=true`；编译器根据观察到的窗口标题判断是否承载旧文件，必要时执行通用 `Ctrl+N` 新建资源批。
- 已新增 RED/GREEN 回归测试覆盖：旧文件标题会编译为 `focus_window -> hotkey CTRL+N -> wait -> observe`；新资源标题只聚焦；文本、绘图、多窗口目的窗口都会声明新资源要求。
- 自动化聚焦测试已通过：`python -m pytest learning_agent/tests/test_stage_batch_compiler.py learning_agent/tests/test_universal_stage_planner.py learning_agent/tests/test_stage_task_loop.py learning_agent/tests/test_computer_use_mcp_v2_desktop_task_tool.py -q` 结果为 23 passed。
- 当前真实可见终端验收仍未完成；上一次 visible-terminal run 因旧 Notepad 恢复窗口残留和高层工具 mode store 不一致失败，后续必须在用户手动关闭残留窗口后复跑 acceptance controller。

## 2026-06-19 Universal Stage Runtime 文本抽取与短通道修复
- 已用 visible-terminal acceptance 失败证据确认两个新源头问题：`UniversalDesktopStagePlanner` 把英文真实 prompt 里的 `direct file write)` 抽成待输入正文 `)`；`UniversalActionDslRuntime -> WindowsSendInputDispatcher -> WindowsControlledPhysicalSendInputSender` 的批量文本路径只有哈希，没有给真实 Unicode 后端提供安全短生命周期明文。
- 已新增并跑通 RED/GREEN 回归：`test_text_payload_extraction_ignores_later_file_write_instruction` 覆盖 `hello everyone` 不被后续 `write)` 覆盖；`test_universal_action_dsl_uses_secure_text_channel_for_real_text_backend` 覆盖 Stage 批量文本输入能到达需要明文的最后一跳，同时公开结果不泄露原文。
- 已修复 `stage_planner.py`：文本正文抽取改为扫描所有候选、剥离 `exactly` 等说明词，并拒绝纯标点候选。
- 已修复 `universal_action_dsl.py`、`sendinput_dispatcher.py`、`controlled_physical_sendinput.py`：通用 DSL 只在低层 sender 声明需要时开启短通道；dispatcher 对受控 sender 使用 `_secure_plaintext_text` 私有字段；Phase95 只在最后一跳真实后端需要时恢复 `text`，普通记录型 sender 仍保持脱敏。
- 已兼容旧压力测试合同：直接接入 `requires_raw_text=true` 的非 Phase95 sender 时仍可收到 `text` 字段；受控 Phase95 sender 明确声明 `accepts_secure_plaintext_text_channel=true`，避免公开明文字段进入 Phase95 验证层。
- 自动化验证已通过：新回归 12 passed；Stage/MCP 聚焦回归 29 passed；压力前置回归 9 passed；完整 `python -m pytest learning_agent/tests -q` 为 139 passed；相关文件 `py_compile` 通过。
- 学习副本已复制到 `learning_agent/test/20260619_224500_secure_text_payload_stage_fix_*` 六个文件。
- 下一步：继续运行 acceptance scenario JSON 校验；在用户确认残留 Notepad/Paint 等旧窗口已关闭后复跑真实可见终端 acceptance controller。

## 2026-06-19 Universal Stage Runtime CodeGraph 同步状态
- 已执行 `codegraph sync "H:\codexworkplace\sofeware\OpenHarness-main"`，结果为 `Already up to date`。
- 已执行 `codegraph status "H:\codexworkplace\sofeware\OpenHarness-main"`，当前索引状态为 `[OK] Index is up to date`。
- 当前索引统计：Files=550，Nodes=13,789，Edges=38,473，Backend=`node:sqlite - built-in (full WAL)`。
- 注意：如果后续真实可见终端验收失败并继续修改源码，需要在最终完成前再次执行 CodeGraph sync/status。

## 2026-06-19 Universal Stage Runtime desktop_task_incomplete 收敛门禁修复
- 已基于 visible-terminal acceptance run `computer_use_universal_text_task_stage_batch_visible_terminal-20260619_222522` 的证据确认两处通用源头问题：`输入文本 \`hello everyone\`` 被抽成 `文本 \`hello everyone`，`准确文本：hello everyone` 在修复轮被抽成空；`desktop_task_incomplete=true` 后模型还能退回 `key/left_click_drag` 等原子动作，绕开 Stage Runtime。
- 已修复 `stage_planner.py`：补充 `准确文本/exact text` 前缀和 `文本/text` 说明词剥离，确保真实用户提示和修复提示都抽取出 `hello everyone`，不把标签词写进应用。
- 已修复 `actionability_state.py`：新增 `OPENHARNESS_DESKTOP_TASK_INCOMPLETE` 协议和字段白名单；当高层桌面任务未完成时，只允许 `desktop_task`、`observe` 和必要 `request_access`，阻断 `key/click/drag` 等原子动作 fallback。
- 已修复 `desktop_task.py`：未完成工具结果会自动嵌入可解析 actionability marker，下一轮主循环能从真实 MCP 输出里沉淀 pending，而不是依赖模型自觉。
- 已新增/更新 RED-GREEN 回归：`test_text_payload_extraction_handles_input_text_label`、`test_text_payload_extraction_handles_exact_text_label`、`test_desktop_task_incomplete_actionability.py` 和 `test_desktop_task_incomplete_result_contains_actionability_marker`。
- 自动化验证已通过：Stage/final gate/MCP 聚焦测试 52 passed；Computer Use 旧回归 47 passed；多目标/acceptance schema 回归 7 passed；完整 `python -m pytest learning_agent/tests -q` 为 144 passed；相关文件 `py_compile` 通过；新三份 universal stage scenario 严格 UTF-8 校验通过，全目录 scenario `utf-8-sig` 兼容校验通过。
- 已按项目规则复制学习副本到 `learning_agent/test/20260619_231500_desktop_task_incomplete_gate_*` 六个文件。
- 已执行最新 CodeGraph 同步与状态检查：`codegraph sync` 为 `Already up to date`，`codegraph status` 为 `[OK] Index is up to date`；当前索引 Files=557、Nodes=13,936、Edges=38,770、DB Size=36.11 MB。
- 下一步：需要在用户关闭当前残留 Notepad/Paint 等测试窗口后，使用 acceptance controller 做真实可见终端验收；当前 Notepad PID 36524 仍有未保存内容，不能由 agent 自动关闭。

## 2026-06-19 Universal Drawing visible-terminal 验收暴露的 pending 覆盖修复
- 已尝试运行真实可见终端绘图验收：`computer_use_universal_drawing_task_stage_batch_visible_terminal-20260619_224758`。controller 命令超时，无 `result.json`，但 `events.jsonl` 已证明进入 `/computer use --full`、自动授权 Paint、调用 `desktop_task` 并触达真实 Paint 窗口。
- 验收证据显示本轮代码的第一层修复生效：`desktop_task` 未完成后，模型多次回到 `desktop_task`，事件包含 `desktop_task_incomplete=true`、`stage_count=5`、`completed_stage_count=2`、`batch_execution_used=true`、`low_level_event_count=66`。
- 新问题已确认：允许 `observe` 后，observe 返回的旧 `OPENHARNESS_DESKTOP_ACTION_REQUIRED` marker 会覆盖原来的 `OPENHARNESS_DESKTOP_TASK_INCOMPLETE` pending，随后模型又能调用 `left_click_drag` 等原子动作。
- 已新增 RED/GREEN 测试 `test_desktop_task_incomplete_survives_observe_action_marker`，修复前失败于 pending 从 `desktop_task_incomplete` 变成 `desktop_observe_before_action`；修复后通过。
- 已修复 `actionability_state.record_actionability_from_tool_result()`：当已有 `DESKTOP_TASK_INCOMPLETE_MARKER` pending 且来源工具是 `observe/screenshot` 时，普通桌面动作 marker 不再覆盖高层未完成 pending。
- 自动化验证已重新通过：desktop_task incomplete 测试 3 passed；相邻收敛测试 9 passed；Stage/MCP 聚焦 53 passed；完整 `python -m pytest learning_agent/tests -q` 为 145 passed；`py_compile` 通过；scenario JSON `utf-8-sig` 校验通过。
- 学习副本已复制到 `learning_agent/test/20260619_232500_desktop_task_incomplete_preserve_pending_*`。
- 真实可见终端验收仍未通过：当前有 Notepad PID 36524 未保存窗口，以及本次绘图验收创建的 3 个 Paint 窗口。需要用户手动关闭/保存这些窗口后才能继续文本或绘图验收。

## 2026-06-19 Universal Computer Use 分层 skill/prompt 准确率方案
- 已根据用户最新确认新增书面方案：`docs/superpowers/plans/2026-06-19-universal-computer-use-layered-skills-prompts-accuracy.md`。
- 方案方向从“失败后兜底”改为“提高主路径准确率”：意图理解、阶段规划、结构化观察、阶段批执行、阶段验证、反思学习分层处理。
- 方案明确所有 Computer Use 内部 skill/prompt 只能放在 `learning_agent/computer_use_mcp_v2/layer_skills/`，不得修改全局 agent 系统提示词或污染其它功能。
- 方案明确执行层只接收结构化 `ActionBatch`，不读取自由 prompt，不让模型在执行层自由决定低层鼠标键盘动作。
- 当前只写方案，尚未修改运行时代码；如果用户确认执行，下一步应按该方案使用目标长任务/执行计划技能逐项实现，并重新做自动化测试、CodeGraph 同步和真实可见终端验收。

## 2026-06-20 Universal Computer Use ClaudeCode harness 补强方案
- 已按用户要求补强 `docs/superpowers/plans/2026-06-19-universal-computer-use-layered-skills-prompts-accuracy.md`。
- 新增 `4.1 ClaudeCode Harness Reference Scope` 和 `4.2 OpenHarness Mapping From ClaudeCode Harness`，明确学习 ClaudeCode 的 agent context、tool-use context、task state、tool result feedback、permission、lock、cleanup、failure propagation 等 harness 机制。
- 新增 `Task 0: Study ClaudeCode Harness And Map It To OpenHarness Computer Use`，要求实现前先用 CodeGraph 检查 `D:\ClaudeCode-main\ClaudeCode-main` 的 harness 相关路径，并产出 `learning_agent/computer_use_mcp_v2/harness_research/claudecode_harness_mapping.md`。
- 方案新增 `harness_context.py` 与 `test_computer_use_harness_context.py`，把 Computer Use 明确建模成挂在主 agent 下的专用桌面任务 harness，而不是只靠 prompt 或单应用脚本推进。
- 当前仍只是方案补充，未修改运行时代码；后续执行时必须从 Task 0 开始，不能跳过 ClaudeCode harness 映射直接写 Computer Use prompt。

## 2026-06-20 GitHub 备份尝试
- 用户要求在继续修改前把当前 OpenHarness 项目上传到 GitHub 仓库 `joyzqb567-11/openharness-agent.git`，防止后续代码修改后无法复原。
- 已新增 GitHub 上传瘦身忽略规则，排除 `.codegraph/`、`.pytest_cache/`、`learning_agent/computer_use_mcp_v2/memory/`、`learning_agent/memory/compact_artifacts/`、`learning_agent/memory/harness/runs/`、`learning_agent/memory/runtime/` 和嵌套验收 runs，避免本机运行日志、截图索引和 runtime 轨迹进入备份仓库。
- 已确认 staged 快照没有超过 90MB 的文件，也没有 `.env/.pem/.key/id_rsa` 这类明显密钥文件。
- 已创建本地 Git 快照提交：`chore: snapshot openharness before computer use refactor`。
- 已添加远端 `openharness-agent=https://github.com/joyzqb567-11/openharness-agent.git`，但当前机器无法连通 GitHub 443，`Test-NetConnection github.com -Port 443` 为 `False`，`curl https://github.com` 超时，push 暂未完成。
- 已生成本地可恢复 bundle：`H:\codexworkplace\sofeware\openharness-agent-snapshot-20260620.bundle`，用于网络恢复前的临时保护。
- 用户提示浏览器可访问 GitHub 后，已确认浏览器使用系统代理 `127.0.0.1:7890`，而 Git/curl 原先没有代理配置；已将当前仓库 Git 代理设置为 `http://127.0.0.1:7890`。
- 已成功执行 `git push -u openharness-agent codex/publish-main:main`，远端 `refs/heads/main` 当前指向 `ad31a03b8a18ffd45945d14896a1175aedd3161e`。

## 2026-06-20 Universal Computer Use 分层 skill/prompt 准确率方案执行
- 已在隔离 worktree `codex/computer-use-layered-harness` 中逐项执行 `docs/superpowers/plans/2026-06-19-universal-computer-use-layered-skills-prompts-accuracy.md` 的 Task 0 到 Task 12。
- 已新增 Computer Use 专用分层目录 `learning_agent/computer_use_mcp_v2/layer_skills/`，覆盖意图理解、阶段规划、观察、批执行契约、验证、反思学习，保持在 Computer Use 模块内部，不改全局 agent 系统提示词。
- 已新增 harness mapping 与 `harness_context.py`，把 ClaudeCode 风格的任务上下文、权限、target ref、验证状态、反思状态映射到 OpenHarness Computer Use 专用桌面任务 harness。
- 已接入分层主路径：独立意图理解层、结构化观察事实层、阶段规划契约、事件预算批执行、成功标准验证、反思学习层、`desktop_task` 分层证据透传。
- 已新增三个真实可见终端 acceptance 场景：`computer_use_layered_text_task_visible_terminal.json`、`computer_use_layered_drawing_task_visible_terminal.json`、`computer_use_layered_multi_app_task_visible_terminal.json`，均首行输入 `/computer use --full`，并启用 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1` 与 `max_permission_sent_count=0`。
- 自动化验证已通过：focused layer tests 为 48 passed；Computer Use 回归为 36 passed；完整 `python -m pytest learning_agent/tests -q` 为 194 passed；修改过的 Python 文件 `py_compile` 通过；三个新增 scenario JSON 均通过 `python -m json.tool`。
- 学习副本已复制到 `learning_agent/test/20260620_layered_task7_13_full_archive/`，共 45 个文件。
- 剩余任务：将 worktree 改动合入主工作区后同步 CodeGraph，并用 acceptance controller 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat` 做真实可见终端文本、绘图、多应用验收；未完成前不能声明开发完成。
# 2026-06-25 Codex 风格桌面 GUI 外壳长期目标执行

- Status: 已在隔离 worktree `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1` 开始执行 `docs/superpowers/plans/2026-06-25-codex-style-desktop-gui-shell.md`。
- 当前目标：逐项完成蓝图 15 个任务，优先完成 V1 Bridge-First Vertical Slice，而不是先堆宽 UI。
- 当前分支：`codex/desktop-gui-shell-v1`。
- 执行技能：已使用 `superpowers:executing-plans` 和 `superpowers:using-git-worktrees`。
- 基线风险：`python -m unittest discover learning_agent.tests -q` 在 Python 3.13 下因 unittest discovery 处理测试包 `__file__ None` 失败；后续使用蓝图中明确测试模块作为验证入口。
- 已完成 Task 1-3：`learning_agent/app/gui_bridge.py` 支持 bootstrap、HTTP server、token/origin 安全、events polling；目标测试 `7 tests OK`，语法检查通过；提交 `8b065638`、`73824a67`、`8fc04dc4`。
- 已完成 Task 4：新增 `apps/desktop` Electron + React + Vite 桌面骨架，包含主进程、preload、渲染入口、主题和基础两栏布局；`npm install` 首次卡在 Electron 默认下载源，改用 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` 后安装完成；`npm run lint` 和 `npm run build` 均通过，确认 `dist/main/index.js`、`dist/preload/index.js`、`dist/renderer/index.html` 存在；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task04_bootstrap/`。
- 已完成 Task 5：新增 `apps/desktop/src/api/guiClient.ts` 和 `apps/desktop/tests/guiClient.test.ts`，锁定 bootstrap/events 请求的 baseUrl 规范化、token header 和事件 query 合同；`npm test` 为 1 个文件 2 个测试通过，`npm run lint` 通过；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task05_gui_client/`。
- 已完成 Task 6：新增 `AppShell`、`Sidebar`、`ThreadView`、`Composer`，把首屏升级为 Codex 风格侧栏、当前项目/最近会话、线程消息区和底部 composer；更新 `layout.css` 的侧栏、消息和输入区样式；`npm run lint` 和 `npm test` 通过；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task06_shell_layout/`。
- 已完成 Task 7：新增 `threadStore.ts` 和 `threadStore.test.ts`，覆盖消息追加、active turn、运行态和终态同步；`ThreadView` 改为可接收消息数组并显示状态标签，`Composer` 改为受控输入并支持 Enter 发送/Shift+Enter 换行基础行为；`npm test` 为 2 个文件 4 个测试通过，`npm run lint` 通过；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task07_thread_state/`。
- 已完成 Task 8：重写 `learning_agent/app/gui_bridge.py` 为清晰的 GUI bridge 模块，保留 bootstrap/events/security，并新增 `GuiRunManager`、`POST /v1/gui/messages`、`POST /v1/gui/turns/{turn_id}/cancel`、`POST /v1/gui/turns/{turn_id}/retry`、`POST /v1/gui/sessions/{session_id}/resume`；支持单 active turn busy 门禁、cancelled/completed/failed 终态、retry linkage、session messages 落盘恢复、生命周期事件写入 `StatusEventStore`；前端 `guiClient` 增加 send/cancel/retry/resume，`AppShell` 接入 reducer 和 composer 提交流程；Python GUI bridge 合同 8 tests OK，`py_compile` 通过，前端 `npm run lint` 和 5 tests OK；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task08_chat_lifecycle/`。
- 已完成 Task 9：新增 `statusStore.ts`、`StatusInspector.tsx`、`ToolCallCard.tsx` 和 `statusStore.test.ts`，把 bridge events 规范化、去重、游标化，并在 `AppShell` 中每 1.5 秒轮询事件；生命周期事件会同步更新 `ThreadView` 消息状态和最终 answer/error 文本；主界面扩展为左导航、中对话、右状态三栏，主线程也能渲染工具调用卡片；前端 `npm run lint`、`npm test -- --run`、`npm run build` 均通过；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task09_status_timeline/`。
- 已完成 Task 10：后端新增 `GET /v1/gui/sessions` 与 `build_gui_sessions_payload()`，复用 status snapshot 输出 `{ ok, sessions, resume }`；前端 `guiClient.sessions()`、`Sidebar` 和 `AppShell` 已串起真实项目名、最近会话列表、侧栏点击恢复和当前会话提交；侧栏补充空状态、长标题截断和副标题样式；验证通过 `python -m py_compile learning_agent\app\gui_bridge.py learning_agent\tests\test_gui_bridge_contract.py`、`python -m unittest learning_agent.tests.test_gui_bridge_contract`、`npm run lint`、`npm test -- --run`、`npm run build`；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task10_project_session_sidebar/`。
- 已完成 Task 11：后端新增 `GET /v1/gui/browser/providers` 与 `build_gui_browser_providers_payload()`，复用 `snapshot["browser"]["provider_status"]` 输出 `{ ok, provider_status, browser }`；前端新增 `guiClient.browserProviders()`、`BrowserPanel.tsx`，并在 `StatusInspector` 顶部展示 visible_chromium、real_chrome_cdp、chrome_extension 等 provider 可用状态、reason、tab 数量、扩展连接和待执行命令数；`AppShell` 启动时并行加载浏览器状态；验证通过 `python -m py_compile learning_agent\app\gui_bridge.py learning_agent\tests\test_gui_bridge_contract.py`、`python -m unittest learning_agent.tests.test_gui_bridge_contract`、`npm run lint`、`npm test -- --run`、`npm run build`；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task11_browser_provider_panel/`。
- 已完成 Task 12：后端新增 `GuiPermissionRequest`、`record_permission_required()`、`decide_permission()` 和 `POST /v1/gui/permissions/{request_id}/decision`，支持 approve/deny、未知 request 结构化 `404 permission_not_found`、重复回答结构化 `409 permission_already_answered`，并写入 `gui_turn_needs_permission`、`permission_required`、`permission_answered` 审计事件；拒绝权限会把关联 turn 置为 failed 并释放 active turn。前端新增 `latestPermissionEvent()`、`PermissionBanner.tsx`、`PermissionDialog.tsx`、`guiClient.decidePermission()`，`AppShell` 会显示 request_id、应用/工具、原因、风险摘要，并只向后端提交允许/拒绝意图；验证通过 `python -m py_compile learning_agent\app\gui_bridge.py learning_agent\tests\test_gui_bridge_permission_contract.py`、`python -m unittest learning_agent.tests.test_gui_bridge_permission_contract`、`python -m unittest learning_agent.tests.test_gui_bridge_contract`、`npm run lint`、`npm test -- --run`、`npm run build`；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task12_permission_surfaces/`。
- 已完成 Task 13：新增 `apps/desktop/scripts/start-backend.ps1` 和 `apps/desktop/scripts/start-desktop-dev.ps1`，`package.json` 增加 `backend` 与 `desktop:dev` 脚本；后端脚本会切到仓库根目录启动 `python -m learning_agent.app.cli desktop-bridge`，桌面开发脚本会安装依赖、构建 main/preload、隐藏启动 Vite renderer 并打开 Electron；README 已补充桌面 GUI 启动与验证命令。验证通过 PowerShell parser 解析两个脚本、`npm run lint`、`npm run build`；学习副本已保存到 `learning_agent/test/desktop_gui_shell_20260625/task13_launch_scripts/`。
- 已完成 Task 14 主要验收闭环：补齐 `apps/desktop/tests/smoke.md`、`apps/desktop/tests/gui-prompt-matrix.md`、`docs/desktop_gui_shell_architecture.md` 和 `learning_agent/test/desktop_gui_shell_20260625/README.md`；真实 Electron 窗口可见验证通过启动、中文/英文 prompt、运行态、工具卡片、浏览器 provider、权限允许/拒绝、取消、失败可读错误、重试、最近会话侧栏和点击恢复。
- Task 14 期间修复三个 GUI 真实验收暴露的问题：CORS/预检与 preload bridge 配置必须保证 renderer 能连本地 bridge；失败事件 payload 中空 `answer` 不能挡住 `error`，已抽到 `messageTextFromStatusEvent()` 并加前端单测；Windows runtime lock 读取失败不能让 bootstrap/browser provider traceback，已加入降级 payload 和路径不泄露测试。
- Task 14 最新验证：`python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_bridge_permission_contract` 为 24 tests OK；`npm run lint` 通过；`npm test -- --run` 为 16 tests passed；可见 GUI 截图归档在 `learning_agent/test/desktop_gui_shell_20260625/`。
- Task 14 剩余后续矩阵项已明确记录为非本切片完成项：安全拒绝一等消息、多行中文持久化、Shift+Enter 可见光标行为、token/unknown route 的 polished in-thread GUI 错误面；未伪装为已完成。
- 已完成 Task 15：新增 `apps/desktop/scripts/release-gate.ps1`，串联 Python GUI bridge 合同/事件/安全/生命周期/权限测试、前端 lint、Vitest 和生产 build；PowerShell parser 通过，完整 release gate 已通过：24 Python tests OK、16 frontend tests passed、lint/build passed；学习副本保存到 `learning_agent/test/desktop_gui_shell_20260625/task15_release_gate/`。

## 2026-06-25 Codex 风格桌面 GUI 外壳 V2 蓝图

- Status: 已新增 V2 书面蓝图，尚未开始修改运行时代码。
- 蓝图文件：`docs/superpowers/plans/2026-06-25-codex-style-desktop-gui-shell-v2.md`。
- 目标：把 V1 可见垂直切片升级为接近 Codex 桌面体验的成熟外壳，覆盖流式输出、真实 Agent Adapter、会话恢复、工具轨迹、权限与安全、浏览器/Computer Use 面板、项目搜索、长任务 Harness、设置诊断、打包和分层验收。
- 推荐执行方式：使用 `superpowers:subagent-driven-development` 逐任务执行，主 agent 负责审核、release gate 和真实可见 GUI 验收。
- 当前未触发 Layer C 真实终端 gate：本次只写方案和进度记录，没有修改 agent runtime、MCP routing、模型调用、浏览器自动化、Computer Use 执行或后端权限 enforcement。

## 2026-06-25 Codex 风格桌面 GUI 外壳 V2 蓝图升级

- Status: 已按 Karpathy 风格评估报告升级 V2 蓝图，尚未开始修改运行时代码。
- 核心变化：V2 从单条 15 任务大长线升级为 `V2-Core / V2-Trust / V2-Product` 三段式交付，要求先把核心流式对话与恢复闭环做硬，再扩展宽功能。
- 新增门禁：加入 `Task Core-0: Golden Traces And Eval Corpus`，要求先定义 20 条 GUI golden traces，并用后端 fixture 合同测试与前端 reducer 测试锁定尾部失败分布。
- 风险收敛：Task 3 从“直接接真实 Agent Adapter”改成“deterministic fake streaming adapter 先行，真实 harness 接线进入 V2-Trust”，避免真实 runtime 不确定性污染 V2-Core。
- 当前未触发 Layer C 真实终端 gate：本次只升级方案和进度记录，没有修改 agent runtime、MCP routing、模型调用、浏览器自动化、Computer Use 执行或后端权限 enforcement。

## 2026-06-25 Desktop GUI Shell V2 Execution

- 当前目标：逐项完成 `2026-06-25-codex-style-desktop-gui-shell-v2.md`，先过 V2-Core，再过 V2-Trust，最后过 V2-Product。
- 当前进度：Task Core-0 已新增 golden trace 文档、20 条 JSON fixture、后端合同测试、前端 fixture 测试、prompt matrix 更新，并已复制到 `learning_agent/test/desktop_gui_shell_v2/task_core_0_golden_traces/`。
- 已验证：`python -m unittest learning_agent.tests.test_gui_golden_trace_contract` 通过；`npm test -- --run goldenTraceReducer.test.ts` 通过；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 1

- Task 1：V2 协议合同已完成。新增 `learning_agent/app/gui_protocol.py`、`apps/desktop/src/api/guiTypes.ts`，并让 `gui_bridge.py` 暴露 schema_version 2、V2 token header 和结构化错误响应。
- 前端 client 已能把 V2 错误解析成 `GuiClientError(status, code, message, requestId)`，避免只显示 HTTP 状态码。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task01_protocol_contract/`。
- 已验证：`python -m unittest learning_agent.tests.test_gui_protocol_contract learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_bridge_permission_contract` 通过；`npm test -- --run guiClient.test.ts` 通过；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 2

- Task 2：V2 事件流和断线恢复已完成。新增 `learning_agent/app/gui_stream.py`、`apps/desktop/src/api/streamClient.ts`，并在 `gui_bridge.py` 增加 `/v2/gui/events` JSON fallback 与 `/v2/gui/events/stream` SSE 路由。
- 事件流支持空事件 heartbeat、旧 status event 到 V2 kind 的映射、query token 的 EventSource 认证入口，以及 fallback long polling 的 lastSequence 更新。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task02_event_stream_recovery/`。
- 已验证：`python -m unittest learning_agent.tests.test_gui_stream_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_security_contract` 通过；`npm test -- --run streamClient.test.ts guiClient.test.ts` 通过；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 3

- Task 3：Agent Adapter 边界和 fake streaming 默认路径已完成。新增 `learning_agent/app/gui_agent_adapter.py`，包含 `GuiAgentRunRequest`、`GuiAgentRunResult`、`GuiAgentAdapter`、`FakeStreamingGuiAgentAdapter`、`DefaultHarnessGuiAgentAdapter(enabled=False)`。
- `GuiRunManager` 默认在未显式注入 `answer_runner` 时走 fake streaming adapter，并把 `turn_started`、`message_delta`、`message_completed`、`turn_failed`、`turn_cancelled` 等 adapter 事件写入统一 `StatusEventStore`；同时继续补写 `gui_turn_completed/failed/cancelled` 兼容旧 GUI lifecycle。
- `gui_stream.py` 已补齐 V2 原生事件名透传，避免 adapter 事件在 SSE/long-poll fallback 中被降级成 heartbeat。
- 真实 harness adapter 只保留 feature-flagged shell；显式真实模式触发词会返回结构化 `adapter_unavailable`，没有在 V2-Core 中导入模型、OAuth、浏览器或 Computer Use runtime。
- 已使用主仓库 CodeGraph 调查真实接线点，并记录到 `docs/desktop_gui_shell_v2_agent_adapter_mapping.md`：未来真实入口应围绕 `LearningAgent.run(...) -> run_agent_with_harness_session(...) -> agent.run_events(...)`，通过 `event_callback` 和 `StatusEventStore` 映射到 GUI V2 events。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task03_fake_agent_adapter/`。
- 已验证：红灯阶段 `test_gui_agent_adapter_contract` 最初失败在默认 manager 没有 `message_delta`；修复后 `python -m unittest learning_agent.tests.test_gui_agent_adapter_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_stream_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_events_contract` 为 19 tests OK；`python -m py_compile learning_agent\app\gui_agent_adapter.py learning_agent\app\gui_bridge.py learning_agent\app\gui_stream.py learning_agent\tests\test_gui_agent_adapter_contract.py` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 4

- Task 4：Thread 流式渲染和一等消息已完成。新增 `apps/desktop/src/state/eventReducer.ts`，把 `message_delta`、`message_completed`、`safety_refusal`、`turn_failed`、V2 原生 turn 事件和旧 `gui_turn_*` 事件统一转换成 `ThreadAction`。
- `threadStore.ts` 已扩展 `ThreadMessage.kind`、`assistant_message_upserted`、`message_delta_received`，支持按 `turnId` 更新助手消息、增量追加文本、创建孤立失败/拒绝消息，并保留旧生命周期 reducer 兼容。
- `ThreadView.tsx` 已把拒绝和错误渲染为线程内一等助手消息：显示“安全拒绝/错误”标签，错误终态保留重试入口，消息正文支持 Markdown 代码围栏转 `<pre><code>` 并横向滚动。
- `AppShell.tsx` 已移除本地旧事件映射函数，轮询和补拉统一调用 `reduceGuiEventToThreadActions()`；`layout.css` 已补齐消息正文、语义标签和代码块样式。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task04_thread_streaming_messages/`。
- 已验证：先跑红灯 `npm test -- --run threadStore.test.ts eventReducer.test.ts` 失败于 `eventReducer` 不存在；实现后 `npm test -- --run threadStore.test.ts eventReducer.test.ts` 为 9 tests passed；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 5

- Task 5：Composer 多行中文和发送体验已完成。`Composer.tsx` 已抽出 `composerKeyIntent()`、`canSubmitComposerDraft()`、`submitComposerDraft()`、`composerButtonState()` 纯规则，并由 React 组件复用。
- 发送行为已改为支持同步/异步 `onSubmit`，只在提交成功后清空草稿；Shift+Enter 不阻止浏览器默认换行，保留原生 caret 行为；运行中或提交中禁用发送并通过按钮 `title/aria-label` 给出简短原因。
- 新增 `apps/desktop/tests/composer.test.ts` 覆盖 Enter 发送、Shift+Enter 换行、中文多行标点和换行原样提交、空白不可发送、运行中禁用原因；`gui-prompt-matrix.md` 已增加 V2 Composer 自动合同覆盖项。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task05_composer_input/`。
- 已验证：`npm test -- --run composer.test.ts` 为 5 tests passed；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 6

- Task 6：权限与安全 V2 已完成。新增 `learning_agent/app/gui_permissions.py`，统一处理权限请求字段规范化、`tool_name`、`action_summary`、`created_at/answered_at` 审计字段、approve/deny 决策别名和本机路径/API token 脱敏。
- `learning_agent/app/gui_bridge.py` 已把 `GuiPermissionRequest` 扩展到 V2 字段，并让 `record_permission_required()` 和 `decide_permission()` 复用权限 helper；重复回答仍返回结构化 `permission_already_answered`，拒绝权限仍会写入 `gui_turn_failed` 和 `permission_answered`，确保主线程和 trace panel 都可见。
- 前端 `PermissionDialog.tsx`、`PermissionBanner.tsx`、`AppShell.tsx` 和 `layout.css` 已显示应用、工具、动作摘要、风险摘要，并在允许/拒绝提交期间禁用按钮，等待后端确认后再关闭本地请求。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task06_permission_v2_flow/`。
- 已验证：红灯阶段新 V2 测试首先失败于缺少 `gui_permissions.py` 和 `tool_name` 参数；实现后 `python -m unittest learning_agent.tests.test_gui_permissions_v2_contract learning_agent.tests.test_gui_bridge_permission_contract learning_agent.tests.test_gui_bridge_security_contract` 为 14 tests OK；`python -m py_compile learning_agent\app\gui_permissions.py learning_agent\app\gui_bridge.py learning_agent\tests\test_gui_permissions_v2_contract.py` 通过；`npm test -- --run` 为 33 tests passed；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 7

- Task 7：Trace Inspector 已完成。`apps/desktop/src/state/eventReducer.ts` 新增 `TraceToolRow` 与 `reduceGuiEventToTraceRows()`，把 `tool_started`、`tool_finished`、失败工具事件和敏感参数统一归约为可渲染工具轨迹。
- 前端新增 `TracePanel.tsx`，右侧工具页签显示 run id、turn id、工具名、状态、耗时、脱敏 args preview、结果摘要、错误码和复制诊断按钮。
- `StatusInspector.tsx` 已从单一状态列表升级为五个页签：状态、工具、浏览器、设置、诊断；页签使用 lucide 图标，浏览器状态移动到“浏览器”页签，诊断页显示事件总数和最新游标。
- `layout.css` 已补齐右侧页签栏、工具轨迹卡片、失败/完成/运行中状态、参数代码块、复制按钮和诊断列表样式，所有卡片圆角保持 6px。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task07_trace_inspector/`。
- 已验证：红灯阶段 `npm test -- --run eventReducer.test.ts` 首先失败于缺少 `reduceGuiEventToTraceRows`；实现后 `npm test -- --run` 为 37 tests passed；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 9

- Task 9：浏览器和 Computer Use 成熟面板已完成。后端新增 `/v2/gui/runtime/panels`，统一返回 `browser`、`computer_use`、`permissions`、`status_degraded` 和 `safe_error`。
- 后端面板 payload 已做安全降级：当状态快照读取失败时只返回安全错误文案，不泄露本机路径；Computer Use 当前暴露安全字段 `mode/full_mode/stopped/expired/allowed_action_classes/permission_mode/lock/abort`，不暴露 state file 路径。
- 前端 `guiClient.runtimePanels()` 已接入 V2 endpoint；`AppShell.tsx` 启动时与 bootstrap/sessions 并行读取 runtime panels，并把完整 payload 传给右侧 `StatusInspector`。
- `StatusInspector.tsx` 保持五页签不变，在“浏览器”页签中同时渲染 `BrowserPanel` 和新增 `ComputerUsePanel`；浏览器面板显示 provider chips、active target、扩展队列和降级 banner，Computer Use 面板显示锁、急停、权限模式和允许动作摘要。
- 新增样式文件 `apps/desktop/src/styles/runtime-panels.css`，由 `apps/desktop/src/renderer/main.tsx` 引入，避免继续膨胀主 `layout.css`。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task09_browser_computer_panel/`。
- 已验证：红灯阶段 `python -m unittest learning_agent.tests.test_gui_browser_computer_panel_contract` 首先失败于缺少 `build_gui_runtime_panels_payload` 和 `/v2/gui/runtime/panels` 路由；实现后相关后端测试通过；前端 `npm test -- --run` 为 38 tests passed；`npm run lint` 通过；`python -m unittest learning_agent.tests.test_gui_browser_computer_panel_contract learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_security_contract` 为 16 tests OK。

## 2026-06-25 Desktop GUI Shell V2 Task 11

- Task 11：设置、诊断和崩溃恢复已完成。后端新增 `learning_agent/app/gui_diagnostics.py`，提供 `build_gui_health_payload()`、`build_gui_diagnostics_payload()`、`redact_diagnostic_text()`。
- `gui_bridge.py` 已接入 `/v2/gui/health` 与 `/v2/gui/diagnostics`，V2 health 需要 token 并返回 schema、uptime、workspace、feature flags、model/provider；V2 diagnostics 返回脱敏健康摘要、snapshot 摘要、release gate 状态、safe_error 和可复制诊断包。
- 前端新增 `settingsStore.ts`、`SettingsPanel.tsx`、`DiagnosticsPanel.tsx` 和 `settings-diagnostics.css`；`StatusInspector.tsx` 继续保持五页签，把“设置/诊断”替换为真实面板；`AppShell.tsx` 启动时并行读取 bootstrap、sessions、runtime panels、health、diagnostics。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task11_settings_diagnostics/`。
- 已验证：红灯阶段 `python -m unittest learning_agent.tests.test_gui_diagnostics_contract` 首先失败于缺少 `gui_diagnostics.py` 和 `/v2/gui/health` 路由；实现后该测试 5 tests OK；`npm test -- --run settingsStore.test.ts guiClient.test.ts` 为 14 tests passed；`npm test -- --run` 为 9 files / 43 tests passed；`npm run lint` 通过；相关后端 bridge 合同 21 tests OK。

## 2026-06-25 Desktop GUI Shell V2 Task 12

- Task 12：视觉成熟度和可访问性已完成。`layout.css` 已把 1100px 以下从隐藏右侧检查器改为三栏紧凑布局，1024x720 仍保留侧栏、主线程、右侧状态/工具/浏览器/设置/诊断 tabs。
- `theme.css` 已补全 keyboard focus 可见描边和 `prefers-reduced-motion` 规则；`SettingsPanel.tsx` 已给路径复制按钮补显式 `aria-label`；`settings-diagnostics.css` 已让设置页在右栏内部滚动。
- `apps/desktop/tests/smoke.md` 已增加并勾选 V2 视觉验收清单，覆盖 1280x800、1024x720、按钮可访问标签、右侧 tabs、composer 稳定高度、工具卡片布局和内部滚动。
- 学习副本和截图证据已保存到 `learning_agent/test/desktop_gui_shell_v2/task12_visual_accessibility/`。
- 已验证：`npm test -- --run` 为 9 files / 43 tests passed；`npm run lint` 通过；`git diff --check` 无空白错误；真实 Electron GUI 已打开并截图验证 1280x800 与 1024x720 两种窗口尺寸。

## 2026-06-25 Desktop GUI Shell V2 Task 8

- Task 8：项目、会话和搜索入口已完成。`learning_agent/app/gui_bridge.py` 已扩展 `GuiSession`，新增 `title/archived/pinned/updated_at` 字段，并提供 `sessions_payload(include_archived)`、`rename_session()`、`archive_session()`、`search_sessions()`。
- 后端已接入 `/v2/gui/sessions`、`/v2/gui/search?q=...`、`/v2/gui/sessions/{session_id}/rename`、`/v2/gui/sessions/{session_id}/archive`；V1 sessions/resume 保持兼容。
- 前端 `guiClient.ts` 已切到 V2 sessions，并新增 `searchSessions()`、`renameSession()`、`archiveSession()`；`Sidebar.tsx` 已支持新对话、搜索、active 会话、固定标记和真实归档计数；新增 `SearchPanel.tsx` 显示搜索结果并可恢复会话。
- `AppShell.tsx` 已维护 `archivedCount/searchOpen/searchArchivedMode/searchQuery/searchResults/searchLoading`，普通搜索和归档过滤分开处理；提交或重试成功后会刷新侧栏 sessions。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task08_sessions_search/`。
- 已验证：`python -m unittest learning_agent.tests.test_gui_sessions_search_contract` 为 4 tests OK；`npm test -- --run` 为 9 files / 44 tests passed；`npm run lint` 通过；`python -m unittest learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_sessions_search_contract` 为 7 tests OK。

## 2026-06-25 Desktop GUI Shell V2 Task 10

- Task 10：长任务 Harness GUI 面板已完成。后端 `learning_agent/app/gui_bridge.py` 新增 `/v2/gui/harness/status`、`/v2/gui/harness/pause`、`/v2/gui/harness/resume`，状态 payload 包含 `active_goal`、`queue`、`checkpoints`、`last_progress`、`blocked_reason`、`safe_error` 和 `controls`。
- 当前 pause/resume 是结构化 unsupported 响应，不伪造真实暂停能力；前端 `HarnessPanel.tsx` 只有在 `controls.pause_supported` 或 `controls.resume_supported` 为真时才显示控制按钮。
- 前端 `guiClient.ts` 已新增 `harnessStatus()`、`pauseHarness()`、`resumeHarness()`；`AppShell.tsx` 启动时和 3 秒轮询读取 Harness 状态，并把 payload 与控制回调传给 `StatusInspector.tsx` 的“任务”页签。
- `runtime-panels.css` 已增加 Harness 面板样式，覆盖当前目标、队列、checkpoint、阻塞警告和控制按钮，避免长 prompt 或路径撑破右侧栏。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task10_harness_panel/`。
- 已验证：`python -m unittest learning_agent.tests.test_gui_harness_panel_contract` 为 2 tests OK；`npm test -- --run` 为 9 files / 45 tests passed；`npm run lint` 通过。

## 2026-06-25 Desktop GUI Shell V2 Task 13

- Task 13：打包和启动体验已完成。`apps/desktop/package.json` 新增 `package:windows` 脚本，调用 `apps/desktop/scripts/package-windows.ps1`。
- 新增 `package-windows.ps1`：缺少 `node_modules` 时运行 `npm ci`，随后运行 `npm run build`，生成 `apps/desktop/dist/package-windows/openharness-desktop-windows-dev`，写入 `package-manifest.json` 和 `learning_agent/test/desktop_gui_shell_v2/package_summary.txt`。
- `start-backend.ps1` 已打印 bridge URL、renderer 启动提示、证据目录，并在 bridge 端口被占用时提前给出清楚错误。
- `start-desktop-dev.ps1` 已打印 bridge URL、renderer URL、证据目录，并在 renderer 端口被占用时提前给出清楚错误；依赖已存在时跳过 `npm install`，仍保留 `npm rebuild electron`。
- `docs/desktop_gui_shell_architecture.md` 已增加 Windows Packaging And Startup 章节，明确当前产物是 Windows development artifact，不是签名安装器。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task13_packaging_flow/`。
- 已验证：`npm run build` 通过；`powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\package-windows.ps1` 通过并输出 `Desktop package artifact created.`；两个启动脚本 `scriptblock` 语法解析通过。

## 2026-06-25 Desktop GUI Shell V2 Task 14

- Task 14：Release gate V2 已完成。`apps/desktop/scripts/release-gate.ps1` 已升级为 V2 自动门禁，运行 Python GUI V1/V2 tests、前端 lint、Vitest、production build、visible GUI smoke 指令生成和 Layer C trigger decision 输出。
- 新增 `apps/desktop/scripts/visible-gui-smoke.ps1`，默认只生成人工可见 GUI smoke 指令和日志；传 `-Launch` 时才启动 bridge 和桌面 dev shell，且仍不会自动宣称视觉通过。
- `apps/desktop/tests/gui-prompt-matrix.md` 已新增 `V2 Visible GUI Release Rows`，覆盖中文/英文流式、安全拒绝、多行、Shift+Enter、token/unknown route、bridge offline、工具轨迹、权限、浏览器、Computer Use、设置、诊断和会话恢复。
- 新增 `docs/desktop_gui_shell_v2_acceptance.md`，定义 Layer A 可见 GUI smoke、Layer B 自动 release gate、Layer C 条件真实后端终端门禁。
- 学习副本已保存到 `learning_agent/test/desktop_gui_shell_v2/task14_release_gate_v2/`。
- 已验证：`powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1` 通过，输出 58 个 Python GUI tests OK、45 个前端 tests passed、lint passed、production build passed、visible GUI smoke instructions generated、Layer C trigger decision printed。

## 2026-06-25 Desktop GUI Shell V2 Task 15

- Task 15：V2 最终验收和归档已完成。新增 `learning_agent/test/desktop_gui_shell_v2/README.md`，记录分支、提交范围、Layer B 命令、Layer A 证据、prompt matrix 结果、已知限制和 Layer C 判定。
- `docs/desktop_gui_shell_architecture.md` 已新增 V2 Acceptance Result，说明自动门禁通过、真实 Electron 核心 smoke 证据位置和剩余未勾选的负向/错误 GUI 行。
- `apps/desktop/tests/gui-prompt-matrix.md` 已把本轮真实 Electron 证明的 V2 行勾选并链接证据：中文流式、多行中文、工具轨迹、权限 approve/deny、诊断面板、窗口重启恢复。
- Layer A 真实 Electron smoke 证据保存到 `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/`，包含 `electron_initial.png`、`electron_cdp_after_smoke.png`、`electron_final_fullscreen.png`、`layer_a_cdp_smoke_result.json` 和 `runtime_pids.json`。
- 已验证：Layer B release gate 通过；Layer A CDP 驱动真实 Electron 窗口完成中文流式、多行、工具卡、权限允许、取消、重试、诊断页打开；验收后已关闭本轮 8776/5177/9223 进程。
- Layer C 判定：未触发。原因是本轮 V2 改动属于 GUI shell、bridge display contracts、diagnostics、release gate、packaging 和 visual acceptance；未修改 agent runtime、MCP routing、model call path、browser automation execution、Computer Use execution 或 backend permission enforcement。

## 2026-06-25 Desktop GUI Shell V2 Task 15 Matrix Completion

- Task 15 补充验收：已完成剩余 V2 visible GUI release rows，证据保存到 `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/`。
- 新增可见证据：`layer_a_round2_completion_result.json`、`english_streaming.png`、`safety_refusal_visible_final.png`、`shift_enter_newline_final.png`、`token_rejection_error_final.png`、`unknown_route_gui_error_final.png`、`bridge_offline_banner_final.png`、`browser_computer_panel_final.png`、`settings_panel_final.png`。
- `apps/desktop/tests/gui-prompt-matrix.md` 已把 streaming English、安全拒绝、Shift+Enter、token rejection、unknown route、bridge offline、browser degraded、Computer Use unavailable、settings panel 等 V2 行全部勾选并链接证据。
- 本轮补齐中发现并修复两个 GUI 可见验收缺口：fake streaming adapter 现在能把高风险 prompt 映射成 `safety_refusal` 事件；前端现在能显示 bridge offline banner，并提供诊断页未知路由探针，让结构化错误能在 GUI 主线程中截图验收。
- 已验证：`python -m unittest learning_agent.tests.test_gui_agent_adapter_contract` 为 7 tests OK；`python -m unittest discover -s learning_agent/tests -p "test_gui*.py"` 为 59 tests OK；`npm test -- --run` 为 46 tests passed；`npm run lint` 通过；`npm run build` 通过；`powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1` 通过；可见 Electron CDP 证据显示 `bodyHasTraceback=false` 且 `bodyHasToken=false`。
## 2026-06-26 OpenHarness Desktop Provider Settings V1 Blueprint

- 已根据 OpenCode Desktop 设置页截图和 `D:\opencode` 知识图谱，制定 OpenHarness Desktop provider/model 设置蓝图。
- 蓝图主文件：`docs/superpowers/plans/2026-06-26-openharness-desktop-provider-settings-v1.md`。
- 本次只新增书面方案和学习副本，未修改运行代码，未触发真实模型调用链路。

## 2026-06-26 Provider Settings V1 Karpathy Review

- 已使用 andrej-karpathy-perspective 评估 provider settings V1 蓝图。
- 评估报告主文件：`docs/superpowers/plans/2026-06-26-openharness-desktop-provider-settings-v1-karpathy-review.md`。
- 关键结论：方向正确，但执行前应修正 raw key JSON 落盘、custom provider 语义、auth methods、test connection、自动视觉 QA 和 secret scan gate。

## 2026-06-26 Provider Settings V1 Blueprint Upgrade

- 已按 Karpathy-style 评估报告升级 `docs/superpowers/plans/2026-06-26-openharness-desktop-provider-settings-v1.md`。
- 升级后的蓝图明确：主 provider settings JSON 只保存 `secret_ref`，`custom-provider-cta` 是虚拟 UI 行，内置 provider id 使用 `github-copilot/openai/google/openrouter/vercel`。
- 蓝图新增 `GuiProviderSecretStore`、`DevJsonSecretStore`、`test-connection` 合同、自动视觉 QA、确定性 secret leak scan、Provider Settings invariants 和 Layer C 停止条件。
- 学习副本已同步到 `learning_agent/test/provider_settings_v1/2026-06-26-openharness-desktop-provider-settings-v1.md`；本次仍只修改书面蓝图和项目记忆，未执行代码实现。

## 2026-06-26 Provider Settings V1 Visible GUI Acceptance Rule

- 已按用户要求补充蓝图：Provider Settings V1 验收必须包含肉眼可见的真实 Electron GUI 界面验收。
- 蓝图已明确：自动截图、DOM 断言、单元测试、bridge 调用和日志只能辅助验收，不能替代最终可见 GUI 检查。
- 蓝图已明确：可见 GUI 验收发现 bug 或异常行为时，必须使用 `superpowers:systematic-debugging` 先复现、定位根因、修复、重新测试，通过后才能继续下一个任务。

## 2026-06-26 Provider Settings V1 Task 1

- Task 1 已完成后端 Provider catalog 和开发密钥存储合同。
- 新增 `learning_agent/app/gui_provider_secret_store.py`，提供 `GuiProviderSecretStore`、`DevJsonSecretStore`、`safe_secret_ref()` 和 `mask_secret_value()`。
- 新增 `learning_agent/app/gui_provider_settings.py`，提供 provider catalog、secret store 摘要、内置 provider、虚拟 `custom-provider-cta` 和响应脱敏。
- `learning_agent/app/gui_bridge.py` 已接入 `GET /v2/gui/provider-settings/providers`，沿用现有 V2 token 门禁。
- 红灯验证先失败于缺少 `gui_provider_secret_store` 和 route 404；实现后 `python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q` 为 2 passed。

## 2026-06-26 Provider Settings V1 Task 2

- Task 2 已完成 Provider auth、disconnect、自定义 provider 和模型可见性持久化。
- `gui_provider_settings.py` 新增结构化错误、provider id/base URL/model/header 校验、`set_provider_auth()`、`disconnect_provider()`、`save_custom_provider()` 和 `set_model_visibility()`。
- `gui_bridge.py` 已接入 `/v2/gui/provider-settings/auth`、`/disconnect`、`/custom-provider`、`/model-visibility` 四个 POST 路由，并把 provider 校验错误转换为结构化 V2 错误响应。
- 测试覆盖：主配置只保存 `secret_ref`、raw key 只进入 `secrets.dev.json`、保留 id `custom` 返回 `reserved_provider_id`、非法 base URL 返回 `invalid_base_url`、模型可见性跨 server 重启持久。
- 已验证：`python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q` 为 3 passed。

## 2026-06-26 Provider Settings V1 Task 3

- Task 3 已完成 Provider connection probe 合同。
- `gui_provider_settings.py` 新增 `test_provider_connection()`、`probe_openai_compatible_models()`、`build_probe_result()` 和 header secret 读取 helper。
- `gui_bridge.py` 已接入 `POST /v2/gui/provider-settings/test-connection`，只做 `/models` metadata 探针，不切换真实 agent runtime。
- 测试使用本地假 `/v1/models` HTTP server 验证成功探针，并覆盖 `unsupported`、`missing_secret`、`network_failed` 三类失败状态。
- 已验证：`python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py -q` 为 4 passed。

## 2026-06-26 Provider Settings V1 Task 4

- Task 4 已完成 Renderer Provider Types、GUI client methods 和 provider settings store。
- `apps/desktop/src/api/guiProviderTypes.ts` 新增 Provider Settings 后端响应、连接请求和探针响应 TypeScript 类型。
- `apps/desktop/src/api/guiClient.ts` 新增 `providerSettings()`、`connectProvider()`、`disconnectProvider()`、`saveCustomProvider()`、`setModelVisibility()` 和 `testProviderConnection()`，统一把前端 camelCase 请求转换为 bridge snake_case 合同。
- `apps/desktop/src/state/providerSettingsStore.ts` 新增纯 view model builder，负责 provider 排序、unsupported 状态、dev secret warning、模型分组和危险字段脱敏。
- 学习副本已保存到 `learning_agent/test/provider_settings_v1/task04_renderer_contract/`。
- 已验证：`npm test -- --run tests/guiProviderClient.test.ts tests/providerSettingsStore.test.ts tests/settingsDialogViewModel.test.ts` 为 3 files / 4 tests passed。

## 2026-06-26 Provider Settings V1 Task 5

- Task 5 已完成 Settings Dialog shell 和 Sidebar 左下角设置入口。
- `Sidebar.tsx` 已把左下角 `设置` 按钮接入 `onOpenSettings` 回调，同时保持快速对话、搜索、归档和会话选择行为。
- `AppShell.tsx` 新增 `settingsOpen` 状态，并在 `PermissionDialog` 后渲染 `SettingsDialog`，让设置弹窗覆盖完整应用。
- 新增 `apps/desktop/src/components/settings/SettingsDialog.tsx`，包含桌面/服务器左侧导航、默认提供商页、关闭按钮、Escape 关闭、dev secret warning 区和 `OpenHarness Desktop v0.1.0` footer。
- 新增 `apps/desktop/src/styles/settings-dialog.css` 并在 `renderer/main.tsx` 导入，满足约 980px 宽、720px 高、窄屏导航折叠、按钮固定尺寸和文本截断要求。
- 新增 `apps/desktop/tests/settingsDialogShell.test.tsx`，先红灯失败于缺少 `SettingsDialog`，实现后转绿；同时修正 provider store 安全测试 fixture 的 TypeScript 类型边界。
- 学习副本已保存到 `learning_agent/test/provider_settings_v1/task05_settings_shell/`。
- 已验证：`npm test -- --run tests/settingsDialogShell.test.tsx` 为 3 passed；相关前端测试 4 files / 7 tests passed；`npm run lint` 通过；`npm run build` 通过。

## 2026-06-26 Provider Settings V1 Task 6

- Task 6 已完成 Providers Panel、连接弹窗、断开入口和测试连接反馈。
- 新增 `SettingsProvidersPanel.tsx`，支持 provider 行、连接状态、来源 badge、unsupported 禁用态、测试连接按钮、安全探针文案、加载/空/错误/重试状态和自定义 provider CTA。
- 新增 `ProviderConnectDialog.tsx`，使用 password 输入 API key，空 key 禁用提交，成功后由父组件清空 key，失败时只显示安全错误文案。
- 新增 `ProviderIcon.tsx`，为 provider 列表提供稳定左侧图标列，避免列表退化成纯文字。
- `SettingsDialog.tsx` 已接入 `guiClient.providerSettings()`、`connectProvider()`、`disconnectProvider()` 和 `testProviderConnection()`，并把后端 payload 转成 renderer view model 后再渲染。
- `AppShell.tsx` 已把真实 `guiClient` 传入设置弹窗，避免桌面 GUI 只显示静态外壳。
- `settings-dialog.css` 已补齐 provider 列表、状态 badge、按钮、错误块和连接弹窗样式；连接弹窗定位在设置窗口内部。
- 新增 `settingsProvidersPanel.test.tsx`，先红灯失败于缺少组件；实现后覆盖列表安全文案、按钮回调、password 输入、空 key 禁用和 probe 状态映射。
- 本轮 lint 首次发现 `guiClient` 在异步副作用中可能为 `undefined`；已按证据定位并改用 `activeClient` 固定本轮引用。
- 学习副本已保存到 `learning_agent/test/provider_settings_v1/task06_providers_panel/`。
- 已验证：`npm test -- --run tests/providerSettingsStore.test.ts tests/guiProviderClient.test.ts tests/settingsDialogViewModel.test.ts tests/settingsProvidersPanel.test.tsx tests/settingsDialogShell.test.tsx` 为 5 files / 11 tests passed；`npm run lint` 通过；`npm run build` 通过。

## 2026-06-26 Provider Settings V1 Task 7

- Task 7 已完成 Custom Provider Dialog。
- 新增 `CustomProviderDialog.tsx`，管理 Provider ID、显示名称、Base URL、API key、模型行和 header 行；API key 与 header value 均使用 password 输入。
- `customProviderValidationError()` 已实现蓝图要求的四类精确校验文案：Provider ID 格式、系统保留 id、Base URL 协议和至少一个模型。
- `buildCustomProviderRequest()` 会构造 `saveCustomProvider()` payload，空 header 行会被忽略，模型默认 `visible: true`。
- `SettingsDialog.tsx` 已新增 `saveCustomProvider` client 合同，点击 `自定义提供商` CTA 后打开弹窗，保存成功后使用后端返回 catalog 刷新 provider 列表，失败只显示 `保存自定义提供商失败`。
- `SettingsProvidersPanel.tsx` 已给自定义 CTA 补 `aria-label="添加自定义提供商"`，避免虚拟行被误理解为真实 provider mutation。
- `settings-dialog.css` 已补齐自定义 provider 弹窗、两列基础字段、模型/header 行、内部滚动和窄屏单列样式。
- 新增 `customProviderDialog.test.tsx`，先红灯失败于缺少 `CustomProviderDialog`，实现后覆盖字段可见性、精确校验文案、payload 构造和空 header 忽略。
- 学习副本已保存到 `learning_agent/test/provider_settings_v1/task07_custom_provider/`。
- 已验证：`npm test -- --run tests/customProviderDialog.test.tsx tests/settingsProvidersPanel.test.tsx tests/settingsDialogShell.test.tsx` 为 3 files / 10 tests passed；`npm run lint` 通过；`npm run build` 通过。

## 2026-06-26 Provider Settings V1 Task 8

- Task 8 已完成 Models Panel 和模型可见性开关。
- 新增 `SettingsModelsPanel.tsx`，按 provider 显示模型分组，复用 `modelGroupsForDisplay()` 保证已连接 provider 排在未连接 provider 前面。
- 每个模型行显示模型显示名、模型 id、provider 名称和 `role="switch"` 的可见性开关；无模型时显示 `连接提供商后会在这里显示模型`。
- `SettingsDialog.tsx` 已把 `models` 页签从占位改为真实模型面板，并新增 `setModelVisibility` client 合同。
- `handleToggleModelVisibility()` 会调用 `setModelVisibility(providerId, modelId, visible)`，保存中禁用当前模型开关，成功用返回 catalog 刷新 payload，失败保持旧 payload 并显示 `模型可见性保存失败`。
- `settings-dialog.css` 已补齐模型分组、模型行、状态 badge、错误条和 switch 样式。
- 新增 `settingsModelsPanel.test.tsx`，先红灯失败于缺少 `SettingsModelsPanel`，实现后覆盖分组排序、模型字段、空态和 switch 回调参数。
- 学习副本已保存到 `learning_agent/test/provider_settings_v1/task08_models_panel/`。
- 已验证：`npm test -- --run tests/settingsModelsPanel.test.tsx tests/customProviderDialog.test.tsx tests/settingsProvidersPanel.test.tsx tests/settingsDialogShell.test.tsx tests/providerSettingsStore.test.ts tests/guiProviderClient.test.ts tests/settingsDialogViewModel.test.ts` 为 7 files / 17 tests passed；`npm run lint` 通过；`npm run build` 通过。

## 2026-06-26 Provider Settings V1 Task 9

- Task 9 已完成真实 Electron 可见 GUI 视觉验收脚本和证据采集。
- 新增 `capture_provider_settings_visual_qa.ps1`，自动启动本地 GUI bridge、Vite renderer 和真实 Electron 窗口，并调用 CDP driver 抓取视觉证据。
- 新增 `provider_settings_visual_qa_driver.mjs`，覆盖左下角设置入口、Provider 行数、自定义 provider CTA、Copilot V1 禁用、OpenAI API key password 输入、raw secret 不泄露、模型页和 390px 窄窗口无横向溢出。
- 本轮可见 GUI 验收发现并修复 4 个问题：备用 Vite 端口 CORS 预检 403、CDP 表达式返回 DOM 元素链过深、移动缩放未真实测试 390px、全局 980px 最小宽度撑破窄窗口。
- `gui_bridge.py` 已把 CORS 来源判断升级为固定桌面来源 + 本机带端口 Vite 来源，并新增 `test_alternate_loopback_vite_origin_can_load_provider_settings` 回归测试。
- `theme.css` 和 `layout.css` 已补 760px 以下真实窄窗口规则，避免背景三栏和 body 最小宽度撑破设置弹窗。
- 视觉证据已保存到 `learning_agent/test/provider_settings_v1/task09_visual_qa/`，源码学习副本已保存到 `learning_agent/test/provider_settings_v1/task09_visual_qa/source_copies/`。
- 已验证：`python -m pytest learning_agent/tests/test_gui_bridge_security_contract.py learning_agent/tests/test_gui_provider_settings_contract.py -q` 为 8 passed；最终 `provider_settings_visual_qa_result.json` 为 `ok: true`，且 `inputType: password`、`scrollWidth: 390`、`innerWidth: 390`。

## 2026-06-26 Provider Settings V1 Task 10

- Task 10 已完成 Provider Settings V1 release gate。
- 新增 `assert_no_provider_secret_leaks.ps1`，执行蓝图要求的 `rg` 危险模式扫描和 `unit-test-secret-value` 扫描，并过滤既有测试、文档、视觉证据与历史运行记忆中的非生产示例。
- Secret leak scan 已通过：`Provider secret leak scan passed.`
- 后端 release gate 已通过：`python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_diagnostics_contract.py learning_agent/tests/test_gui_bridge_security_contract.py -q` 为 14 passed。
- 前端 release gate 已通过：`npm test` 为 16 files / 63 tests passed；`npm run lint` 通过；`npm run build` 通过。
- 最终可见 GUI 验收已通过：默认端口 8776/5177 被现有进程占用，本轮使用 8876/5277/9323 启动真实 Electron 窗口；`provider_settings_visual_qa_result.json` 为 `ok: true`，断言包含 `inputType: password`、raw secret 不泄露、390px 无横向溢出。
- V1 明确不切换真实模型 runtime；真实大模型请求和 GUI agent adapter 接线仍属于后续 Layer C 计划。

## 2026-06-26 OpenCode-Style OpenAI Connect Blueprint

- 已按用户要求先读取 `D:\opencode` 相关 CodeGraph 和源代码，再制定 OpenHarness Desktop 的 OpenCode 风格 OpenAI 连接向导蓝图。
- 关键 OpenCode 证据：`packages/core/src/plugin/provider/openai.ts` 注册 `ChatGPT Pro/Plus (browser)` 与 `ChatGPT Pro/Plus (headless)`，`packages/app/src/components/dialog-connect-provider.tsx` 提供方法选择、API Key、OAuth auto/code UI，`packages/protocol/src/groups/integration.ts` 定义 key/oauth/attempt status/complete/cancel 路由。
- 新蓝图已保存到 `docs/superpowers/plans/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。
- 蓝图明确验收边界：API Key 路径必须真实连后端和 `/models` 探针；browser/headless OAuth 路径必须实现 attempt 生命周期和真实 GUI 可见验收；完整模型 runtime 使用 OAuth token 不在本蓝图内冒进声明完成。

## 2026-06-26 OpenCode-Style OpenAI Connect Karpathy Review

- 已使用 `andrej-karpathy-perspective` skill 评估 `2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。
- 评估结论为 B+：方向正确、证据链扎实、attempt 状态机抽象正确，但 V1 范围偏胖，真实 OAuth token 存储和 OpenCode OAuth client 配置存在成熟度风险。
- 核心升级建议：增加 Milestone 0 安全/产品决策；把真实 OAuth 改成 gated experimental path；先做 API Key，再做 mock attempt，再做 headless，最后做 browser；把 `auth-session` 命名收敛为 `auth-attempt`；补 tail behavior tests。
- 评估报告已保存到 `docs/superpowers/plans/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1-karpathy-review.md`。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1-karpathy-review.md`。

## 2026-06-26 OpenCode-Style OpenAI Connect Blueprint Upgrade

- 已按 Karpathy-style review 升级原蓝图 `docs/superpowers/plans/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。
- 升级后稳定 V1 只承诺 `Slice A + Slice B`：OpenCode 风格 method picker、API Key 真实路径、mock auth-attempt 状态机、视觉 QA 和 secret leak gate。
- 真实 headless/browser OAuth 已移动到 Post-V1 gated slices：必须满足 `os_encrypted secret store + OPENHARNESS_OPENAI_EXPERIMENTAL=1 + approved client id` 才能保存真实 OAuth refresh token。
- 合同命名已收敛：使用 `auth-attempt` endpoints；使用 `display_code/display_code_kind`；status enum 固定为 `pending | complete | failed | expired`；auto mode 前端不调用 `complete`。
- 学习副本已同步到 `learning_agent/test/provider_settings_v2_openai_connect/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`，哈希与主蓝图一致。
- 自检通过：蓝图中未发现旧词 `auth-session`、`confirmation_code`、`TBD`、`TODO`、`implement later`。

## 2026-06-26 OpenCode-Style OpenAI Connect GUI Acceptance Requirement

- 已按用户要求把强制验收文字加入 `docs/superpowers/plans/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。
- 新增要求原文：`验收需要使用肉眼可见的真实GUI界面进行验收，验收时出现bug或发现bug时，请使用systematic debugging技能，修复bug，并重新测试，测试通过后继续执行下一个任务。`
- 该要求已写入 Product Boundary 和 Task 10 Real Visible GUI Acceptance Gate 两处，学习副本也已同步到 `learning_agent/test/provider_settings_v2_openai_connect/2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 0

- Task 0 已启动：按 `superpowers:executing-plans` 建立长任务目标，并把本轮稳定 V1 的产品与安全边界写入 `agent_memory/context.md`。
- 本轮停止条件：如果自动化测试、密钥扫描、真实可见 GUI 验收或用户可见设置流程任一失败，必须先使用 systematic debugging 查明根因、修复并复测，不能跳过到下一个任务。
- 已确认当前实现 worktree `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1` 没有 `.codegraph/`；后续实现读取以该 worktree 的真实文件为准。
- Task 0 自检发现蓝图检查项本身包含旧命名字面量，会让 `rg` 门禁误报；已按 systematic debugging 追到根因并改成不含旧词的检查描述。
- 已复跑蓝图门禁：`rg -n "auth-session|confirmation_code|TBD|TODO|implement later" docs\superpowers\plans\2026-06-26-openharness-desktop-opencode-style-openai-connect-v1.md` 无命中，学习副本已同步。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 1

- Task 1 已完成后端 Provider Catalog 合同升级。
- 红测：`test_provider_settings_catalog_route_returns_redacted_catalog` 先要求 schema v3、OpenAI `chatgpt-browser/chatgpt-headless/api-key` 三方法、`type/mode/experimental` 字段和 catalog 不含 `secret_ref`，初次运行失败于 `2 != 3`。
- 实现：`gui_provider_settings.py` 将 `PROVIDER_SETTINGS_SCHEMA_VERSION` 升到 3，`GuiAuthMethodInfo` 新增 `type/mode/experimental`，OpenAI catalog 改为 `_openai_auth_methods()` 统一输出 browser/headless/api-key。
- 验证：`python -m pytest learning_agent\tests\test_gui_provider_settings_contract.py -q` 为 3 passed；`python -m py_compile learning_agent\app\gui_provider_settings.py learning_agent\tests\test_gui_provider_settings_contract.py` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task01_backend_catalog/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 2

- Task 2 已完成前端类型和 provider settings store 升级。
- 红测：`providerSettingsStore.test.ts` 先要求 `secret_ref/access_token/refresh_token/id_token` 递归脱敏，并要求 OpenAI auth method view model 保留 `methodType/mode/experimental`；初次运行 3 个断言失败。
- 实现：`guiProviderTypes.ts` 新增 `GuiProviderAuthMethodType`、`GuiProviderAuthMethodMode` 和 method `type/mode/experimental` 字段；`providerSettingsStore.ts` 新增 method metadata 映射，并把危险字段判断改为小写归一化。
- 相关测试夹具已升级到 schema v3 和新 auth method 形状，避免旧合同继续藏在测试里。
- 验证：`npm test -- --run tests/providerSettingsStore.test.ts tests/guiProviderClient.test.ts tests/settingsDialogViewModel.test.ts tests/settingsProvidersPanel.test.tsx` 为 4 files / 10 tests passed；`npm run lint` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task02_frontend_store/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 3

- Task 3 已完成 OpenCode 风格方法选择 UI 的第一屏。
- 红测：`settingsProvidersPanel.test.tsx` 要求 OpenAI 三方法 provider 打开连接弹窗时先显示 `选择 OpenAI 的登录方式`，并显示 browser、headless、API 密钥三行；初次运行失败，因为旧弹窗直接显示 `type="password"`。
- 实现：`ProviderConnectDialog.tsx` 增加 method picker 状态，多方法 provider 初始显示方法列表，单方法 provider 保持直接显示 API key 表单；方法列表保留实验 badge 和帮助文案。
- 样式：`settings-dialog.css` 新增方法列表、按钮、帮助文案、实验 badge 的紧凑设置页样式。
- 验证：`npm test -- --run tests/settingsProvidersPanel.test.tsx tests/providerSettingsStore.test.ts` 为 2 files / 9 tests passed；`npm run lint` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task03_method_picker_ui/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 4

- Task 4 已完成 API Key step 的新方法 id 提交路径。
- 红测：`settingsProvidersPanel.test.tsx` 要求 API key 表单带有 `data-active-auth-method="api-key"`，初次运行失败，因为旧表单没有暴露 active method。
- 实现：`ProviderConnectDialog.tsx` 的 `onSubmit` 改为传出 `authMethodId`；`SettingsDialog.tsx` 改为使用选中的 `api-key` 和 write-only `secret` 字段调用 `connectProvider()`，不再硬编码旧 `api_key`。
- 后端合同测试也改为用 `auth_method_id: "api-key"` 和 `fields.secret` 写入 OpenAI API key，确认后端兼容新前端请求。
- 验证：`python -m pytest learning_agent\tests\test_gui_provider_settings_contract.py -q` 为 3 passed；`npm test -- --run tests/settingsProvidersPanel.test.tsx tests/guiProviderClient.test.ts tests/providerSettingsStore.test.ts` 为 3 files / 10 tests passed；`npm run lint` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task04_api_key_path/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 5

- Task 5 已完成 OpenAI Auth 配置门禁 helper。
- 红测：`test_gui_provider_openai_auth_config.py` 先要求默认 `mock`、真实 OAuth 必须满足 `os_encrypted + experimental flag + client id`、阻断时抛 `openai_real_oauth_blocked` 结构化错误；初次运行失败于模块不存在。
- 实现：新增 `gui_provider_openai_auth_config.py`，提供 `build_openai_auth_config()`、`OpenAIAuthConfig`、`OpenAIAuthConfigError` 和 `assert_real_oauth_allowed()`。
- 安全边界：默认开发环境只启用 mock auth-attempt；真实 OAuth 只有 `OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1`、`OPENHARNESS_OPENAI_CLIENT_ID` 同时满足时才允许。
- 验证：`python -m pytest learning_agent\tests\test_gui_provider_openai_auth_config.py -q` 为 3 passed；`python -m py_compile learning_agent\app\gui_provider_openai_auth_config.py learning_agent\tests\test_gui_provider_openai_auth_config.py` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task05_openai_auth_config/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 6

- Task 6 已完成 OpenAI mock auth-attempt 后端生命周期。
- 红测：新增 `test_gui_provider_auth_attempts_contract.py`，先要求 `chatgpt-browser/chatgpt-headless` 支持 `start/status/complete/cancel`，且响应和落盘设置不泄露 `refresh_token/access_token/id_token/secret_ref`；初次运行失败于模块缺失和 bridge 路由 404。
- 实现：新增 `gui_provider_auth_attempts.py`，提供 pending/complete/expired 状态机、确认码 payload、同 provider pending 自动取消、mock complete 落盘为 `oauth_mock` 且不写入任何真实 token。
- Bridge：`gui_bridge.py` 新增 `/v2/gui/provider-settings/auth-attempt/start`、`/status`、`/complete`、`/cancel` 路由；`gui_provider_settings.py` 能把 `oauth_mock` 显示为已连接且 `source="mock"`。
- 验证：`python -m pytest learning_agent\tests\test_gui_provider_auth_attempts_contract.py -q` 为 2 passed；`python -m pytest learning_agent\tests\test_gui_provider_settings_contract.py learning_agent\tests\test_gui_provider_openai_auth_config.py learning_agent\tests\test_gui_provider_auth_attempts_contract.py -q` 为 8 passed；`python -m py_compile learning_agent\app\gui_provider_auth_attempts.py learning_agent\app\gui_provider_settings.py learning_agent\app\gui_bridge.py learning_agent\tests\test_gui_provider_auth_attempts_contract.py` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task06_auth_attempt_backend/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 7

- Task 7 已完成前端 OAuth auto 等待、轮询、取消 UI。
- 红测：`guiProviderClient.test.ts` 先要求 client 支持 `auth-attempt/start/status/cancel`；`settingsProvidersPanel.test.tsx` 先要求弹窗显示“访问此链接”、设备码和“等待授权”，且不渲染 `refresh_token/access_token/secret_ref`；初次运行失败于 client 方法缺失和等待页未渲染。
- 实现：`guiProviderTypes.ts` 新增 `ProviderAuthAttemptInfo/Payload`；`guiClient.ts` 新增 start/status/complete/cancel 方法；`ProviderConnectDialog.tsx` 支持 OAuth auto 等待页、复制确认码、返回时取消；`SettingsDialog.tsx` 支持启动 attempt、每秒轮询 status、完成后刷新 catalog、关闭时取消 pending。
- 样式：`settings-dialog.css` 新增 auth-attempt 等待页、授权链接、确认码输入/复制按钮、状态文案样式，保持 OpenCode 风格紧凑设置弹窗。
- 验证：`npm test -- --run tests/guiProviderClient.test.ts tests/settingsProvidersPanel.test.tsx` 为 2 files / 7 tests passed；`npm test -- --run tests/providerSettingsStore.test.ts tests/guiProviderClient.test.ts tests/settingsDialogViewModel.test.ts tests/settingsProvidersPanel.test.tsx tests/settingsDialogShell.test.tsx` 为 5 files / 15 tests passed；`npm run lint` 通过。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task07_frontend_auth_attempt_ui/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 8

- Task 8 已完成 mock OAuth visual QA，并在真实 Electron GUI 窗口中生成可见截图证据。
- 视觉验收暴露的 React 竞态已按 TDD 修复：新增 `authAttemptPollDecision()`，要求 `complete` 状态先刷新 provider catalog，不能先把 complete attempt 写回本地等待页，否则 React effect cleanup 会让 `providerSettings()` 结果无法落地。
- 红测：`npm --prefix apps/desktop test -- --run tests/settingsDialogViewModel.test.ts` 初次失败于 `authAttemptPollDecision is not a function`；修复后该测试为 3 passed。
- 回归验证：`npm --prefix apps/desktop test -- --run tests/guiProviderClient.test.ts tests/providerSettingsStore.test.ts tests/settingsDialogViewModel.test.ts tests/settingsProvidersPanel.test.tsx` 为 4 files / 14 tests passed；`npm --prefix apps/desktop run lint` 通过。
- Visual QA driver 同步修复两个断言问题：headless 和 browser 的 `display_code` 实际渲染在 readonly input 的 `value` 中，不会进入 `innerText`，因此 driver 改为读取 `.provider-connect-code-row input.value`。
- 最终视觉验收命令：`powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1 -BridgePort 9376 -RendererPort 5777 -CdpPort 9825`，退出码 0。
- 最终结果：`learning_agent/test/provider_settings_v2_openai_connect/task08_visual_qa/openai_connect_visual_qa_result.json` 中 `ok=true`，截图包含 `openai_method_picker_1365x768.png`、`openai_headless_waiting_1365x768.png`、`openai_mock_connected_1365x768.png`、`openai_browser_waiting_1365x768.png`、`openai_method_picker_mobile_390x844.png`。
- 肉眼检查截图确认：OpenAI 三方法可见、browser/headless 等待页可见、mock complete 后 provider 行显示已连接、390px 窄屏无横向溢出。
- 本轮进程清理已确认：9376、5777、9825 无残留 Listen/Established 连接。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task08_visual_qa/source_copies/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 9

- Task 9 已完成 tail behavior tests 与 secret leak gate。
- 后端 tail tests：`test_gui_provider_auth_attempts_contract.py` 增加重复 start、重复 cancel、未知 attempt、过期 attempt、重复 complete 不重复保存等合同；初次红测暴露未知 attempt 仍抛 404，已改为返回 `expired + auth_attempt_not_found` 的结构化占位 attempt。
- 前端 tail tests：`settingsDialogViewModel.test.ts` 增加 `shouldPollAuthAttempt()`，覆盖 renderer 关闭、无 client、无 attempt、failed/expired/complete 状态都不能继续轮询；初次红测失败于 helper 缺失，已补实现并让 effect 复用该判断。
- Secret scan：`assert_no_provider_secret_leaks.ps1` 增加运行产物严格扫描，禁止 `access_token`、`refresh_token`、`id_token`、`secret_ref`、测试密钥样本文本和 Bearer/key 形态进入 visual QA JSON/log/text；源码学习副本用 `!**/source_copies/**` 递归排除，避免把允许的教学副本误判为运行证据。
- Systematic debugging 修复：secret scan 在零命中时曾因 `$RuntimeSecretMatches` 为 `$null` 且 StrictMode 下访问 `.Count` 报错；根因确认后把 rg 输出包成数组，零命中现在稳定通过。
- Visual QA driver 增强：补上 API Key step 真实截图和 JSON 顶层字段 `methodCount/inputType/waitingVisible/rawSecretLeakFound`，并复跑真实 Electron visual QA。
- 验证：`python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_bridge_security_contract.py -q` 为 15 passed。
- 验证：`npm --prefix apps/desktop test` 为 16 files / 70 tests passed。
- 验证：`powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1` 输出 `Provider secret leak scan passed.`。
- 视觉回归：`powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1 -BridgePort 9476 -RendererPort 5877 -CdpPort 9925` 退出码 0，结果 JSON 为 `ok=true`、`methodCount=3`、`inputType=password`、`waitingVisible=true`、`rawSecretLeakFound=false`。
- 学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/task09_tail_secret_gate/source_copies/`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 10

- Task 10 已完成真实可见 GUI 验收证据整理。
- 证据来源：真实 Electron visual QA 生成的 `learning_agent/test/provider_settings_v2_openai_connect/task08_visual_qa/` 截图与 JSON，命令为 `powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1 -BridgePort 9476 -RendererPort 5877 -CdpPort 9925`，退出码 0。
- 最终证据包已保存到 `learning_agent/test/provider_settings_v2_openai_connect/visual_evidence/`：`openai-method-selection.png`、`openai-api-key-step.png`、`openai-oauth-auto-waiting.png`、`openai-connect-complete.png`、`openai_connect_visual_qa_result.json`。
- 肉眼检查确认：方法选择页显示 browser/headless/API 密钥三种方式；API Key step 使用空密码框且空提交按钮禁用；headless mock OAuth step 显示授权链接、确认码、复制按钮和等待授权；mock complete 后 OpenAI provider 行显示已连接并带 `Mock ChatGPT auth`。
- Secret scan 已把 `visual_evidence/` 加入运行产物扫描根目录，并复跑 `powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1`，输出 `Provider secret leak scan passed.`。

## 2026-06-26 OpenCode-Style OpenAI Connect Execution Task 11

- Task 11 已完成文档、学习副本和 release gate。
- `agent_memory/context.md` 已记录稳定 V1 完成边界：API Key 是当前唯一真实连接路径，browser/headless 是 mock auth-attempt，真实 OAuth 仍需 Post-V1 gate。
- 总学习副本已保存到 `learning_agent/test/provider_settings_v2_openai_connect/source_copies/`，包含后端 provider/auth-attempt/config/bridge、前端 types/client/store/dialog/style、测试和 visual QA/secret scan 脚本。
- 蓝图和 Karpathy review 副本已同步到 `learning_agent/test/provider_settings_v2_openai_connect/`。
- 最终 release gate 后端：`python -m pytest learning_agent/tests/test_gui_provider_secret_store.py learning_agent/tests/test_gui_provider_settings_contract.py learning_agent/tests/test_gui_provider_auth_attempts_contract.py learning_agent/tests/test_gui_provider_openai_auth_config.py learning_agent/tests/test_gui_bridge_security_contract.py -q` 为 15 passed。
- 最终 release gate 前端测试：`npm --prefix apps/desktop test` 为 16 files / 70 tests passed。
- 最终 release gate lint：`npm --prefix apps/desktop run lint` 退出码 0。
- 最终 release gate build：`npm --prefix apps/desktop run build` 退出码 0，Vite production build 成功。
- 最终 release gate secret scan：`powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v1/scripts/assert_no_provider_secret_leaks.ps1` 输出 `Provider secret leak scan passed.`。
- 蓝图默认 visual QA 命令因当前已有 `desktop-bridge --port 8776` 用户进程监听而失败；未关闭该用户可见外壳进程，改用备用端口执行最终 visual QA。
- 最终 release gate visual QA：`powershell -NoProfile -ExecutionPolicy Bypass -File learning_agent/test/provider_settings_v2_openai_connect/scripts/capture_openai_connect_visual_qa.ps1 -BridgePort 9576 -RendererPort 5977 -CdpPort 9975` 退出码 0，结果 JSON 为 `ok=true`、`methodCount=3`、`inputType=password`、`waitingVisible=true`、`rawSecretLeakFound=false`。
- 最终 `visual_evidence/` 已用 9576/5977/9975 这一轮截图和 JSON 覆盖，并再次复跑 secret scan 通过。

## 2026-06-26 ChatGPT OAuth Real Model Blueprint

- 已按用户要求先读取 `D:\opencode` 的 CodeGraph 和 OpenCode 关键源码，再制定 OpenHarness Desktop 真实 ChatGPT OAuth 模型连接蓝图。
- OpenCode 重点源码依据包括：`packages/opencode/src/plugin/openai/codex.ts`、`packages/core/src/plugin/provider/openai.ts`、`packages/opencode/src/provider/auth.ts`、`packages/app/src/components/dialog-connect-provider.tsx`。
- 已确认 OpenCode 的真实链路是 PKCE + `localhost:1455/auth/callback` + token exchange + `https://chatgpt.com/backend-api/codex/responses`，不是普通 OpenAI API key 路径。
- 已对照 OpenHarness 当前实现：provider UI 已有 OpenAI browser/headless/API key 三方法，但 browser/headless 仍是 mock；主聊天默认仍走 `FakeStreamingGuiAgentAdapter`。
- 新蓝图已保存到 `docs/superpowers/plans/2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1.md`，执行重点是把真实 OAuth 状态机、加密 token store、`CodexOAuthChatModel` 和 GUI real adapter 接起来。

## 2026-06-26 ChatGPT OAuth Real Model Karpathy Review

- 已使用 `andrej-karpathy-perspective` 评估 `2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1.md`。
- 已额外核对 OpenAI 官方 Codex CLI 文档：`codex login` 支持 ChatGPT account OAuth；这说明官方路径应优先于 OpenCode-style direct OAuth。
- 评估报告已保存到 `docs/superpowers/plans/2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1-karpathy-review.md`。
- 主要结论：蓝图方向正确，但不能把 OpenCode client id、`localhost:1455`、`chatgpt.com/backend-api/codex/responses` 当成稳定产品契约；需要升级为 V1A 官方 Codex login bridge、V1B provider-aware real adapter、V1C experimental direct OAuth 三层路线。
- 重点风险：任务颗粒度过大、token 生命周期不足、port 1455 冲突未覆盖、adapter streaming/cancel/tool-call 合同过薄、真实 GUI 验收缺证据包。

## 2026-06-26 ChatGPT OAuth Real Model Blueprint Upgrade

- 已按 Karpathy 评估报告升级 `docs/superpowers/plans/2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1.md`。
- 蓝图路线已从“直接复刻 OpenCode OAuth”改为三层：V1A 使用官方 `codex login` / `codex login status` 桥接 ChatGPT OAuth 并通过 `CodexCliChatModel` 跑通真实 GUI 回答；V1B 加固 provider-aware real adapter、事件流、取消、错误和证据包；V1C 才把 OpenCode-style PKCE + localhost callback + Codex backend route 作为显式 experimental direct OAuth。
- 已把 OpenCode client id、`localhost:1455` 和 `chatgpt.com/backend-api/codex/responses` 标为研究参考或 V1C 实验路径，不能作为默认稳定产品契约。
- 已补充 port 1455 冲突、token lifecycle、streaming/cancel/tool-call tail behavior、secret scan、真实可见 GUI OAuth 验收证据包和失败时必须 systematic debugging 的门禁。
- 已完成蓝图自检：`rg -n "TBD|TODO|待定|占位|implement later|\\.\\.\\." docs\superpowers\plans\2026-06-26-openharness-desktop-chatgpt-oauth-real-model-v1.md` 无命中。
- 已按用户补充要求把“验收需要使用肉眼可见的真实 GUI 界面进行验收，发现 bug 时使用 systematic debugging 修复并复测，通过后才继续下一个任务”写入蓝图的安全原则和 Release Gate。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Blueprint

- 已根据 OpenCode CodeGraph 和源码证据重新确定路线：OpenCode 的主路径是 ChatGPT OAuth token + `https://chatgpt.com/backend-api/codex/responses` + HTTPS/SSE；WebSocket 是实验路径，不应成为 OpenHarness Desktop 默认真实模型调用路径。
- 已把 OpenHarness Desktop V3 建议落成书面执行蓝图：默认使用 `direct_sse`，绕开 Codex CLI WebSocket 重试慢路径；Codex CLI 只作为显式 fallback。
- 新蓝图已保存到 `docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 学习副本已保存到 `learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 蓝图包含成功标准、范围边界、停止条件、真实 OAuth 环境契约、12 个实施任务、测试命令、secret redaction gate、computer-use 真实可见 GUI 验收脚本。
- 已完成蓝图占位符自检：`rg -n "TBD|TODO|待定|占位|implement later|\\.\\.\\.|<[^>]+>|pass$" docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md` 无命中。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Karpathy Review

- 已按用户要求使用 `andrej-karpathy-perspective` 评估 Direct ChatGPT OAuth SSE V3 蓝图。
- 评估前已用 UTF-8 读取 skill 指令和蓝图全文，并用 CodeGraph 核对当前关键代码现状：Composer 仍只提交 prompt、OpenAI auth-attempt 仍是 mock、secret store 仍缺 OS 加密实现、`CodexOAuthChatModel` 有直连雏形但需要迁移策略。
- 评估报告已保存到 `docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3-karpathy-review.md`。
- 学习副本已保存到 `learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3-karpathy-review.md`。
- 主要结论：方向正确，但当前蓝图把 OpenCode client id、direct endpoint 和模型列表等研究观察写得过于像产品契约；执行前应升级为实验快速通道、真实 fixture 驱动、可回滚 runtime contract。
- P0 升级点包括：client id 不应硬编码为默认产品值；补真实 OAuth/SSE golden fixtures；替换会误报的 `rg` secret scan；明确 direct endpoint 是 experimental runtime；模型列表改为 static + probe + last-known-good。
- P1/P2 升级点包括：补 account discovery、stream cancellation、`CodexOAuthChatModel` 迁移策略、DPAPI 恢复/迁移、GUI 验收宽松文本断言和 composer/bridge payload 兼容迁移。
- 已完成评估报告占位符自检，正式报告和学习副本 SHA256 一致。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Blueprint Upgrade

- 已按 Karpathy 评估报告升级 `docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 学习副本已同步升级到 `learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 蓝图路线已从“直接实现 OpenCode-style direct SSE”升级为 V3A-V3F 纵向切片：fake token + fake SSE + real GUI payload、OS 加密存储、真实 browser OAuth、account discovery、model probe、direct_sse probe、真实 streaming、cancel/timeout、诊断、secret scanner、可见 GUI 验收。
- 已把 OpenCode observed client id `app_EMoamEEZ73f0CkXaXp7hrann` 从默认产品契约降级为本地实验研究参考；正式 runtime 要求 operator 显式设置 `OPENHARNESS_OPENAI_CLIENT_ID`。
- 已补充 direct endpoint experimental gate：只有 `OPENHARNESS_OPENAI_EXPERIMENTAL=1` 且 `OPENHARNESS_OPENAI_RUNTIME=direct_sse` 时才启用 direct ChatGPT OAuth SSE；失败时必须显示 direct-route 状态，不能静默 fallback 到 Codex CLI。
- 已补充 sanitized golden SSE/OAuth fixtures、结构化 secret scanner、static + probe + last-known-good 模型注册表、account-required 状态、stream cancellation 合同、timeout 分类、`CodexOAuthChatModel` 迁移策略和宽松真实 GUI 验收断言。
- 已完成升级蓝图占位符自检：`rg -n "TBD|TODO|待定|占位|implement later|\\.\\.\\.|<[^>]+>|pass$" docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md` 无命中。
- 正式蓝图和学习副本 SHA256 一致。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 GUI Acceptance Gate Addendum

- 已按用户原文要求，把“验收需要使用肉眼可见的真实GUI界面进行验收，使用computer use技能确认和验证，如果验收时出现bug或发现bug时，请使用systematic debugging技能，修复bug，并重新测试，测试通过后继续执行下一个任务。”加入 V3 蓝图 Task 9 的强制可见 GUI 验收门禁。
- 正式蓝图路径：`docs/superpowers/plans/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 学习副本路径：`learning_agent/test/20260627_openharness_desktop_direct_chatgpt_oauth_sse_v3/2026-06-27-openharness-desktop-direct-chatgpt-oauth-sse-v3.md`。
- 已验证正式蓝图与学习副本 SHA256 一致，且占位符扫描无命中。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Progress

- 已在 worktree `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\direct-chatgpt-oauth-sse-v3` 执行 V3 蓝图，当前分支为 `codex/direct-chatgpt-oauth-sse-v3`。
- Task 0-7 已完成：创建隔离 worktree、实现 ChatGPT OAuth token 解析与 os_encrypted 存储、接入直接 SSE client、接入 GUI turn payload、接入 provider/model/composer 状态联动。
- Task 7 targeted gate 已通过：`python -m py_compile learning_agent\app\gui_provider_settings.py` 成功；`python -m pytest learning_agent\tests\test_gui_provider_settings_contract.py learning_agent\tests\test_gui_provider_oauth_disconnect.py learning_agent\tests\test_openai_provider_runtime_state.py learning_agent\tests\test_openai_model_registry.py -q` 为 10 passed；`npm test -- --run composer.test.ts composerRouteControls.test.ts providerSettingsStore.test.ts settingsProvidersPanel.test.tsx settingsModelsPanel.test.tsx` 为 5 files / 24 tests passed。
- Task 8 已补充 direct SSE 首事件诊断、首 delta 5 秒预算标记和 runbook 文档；`python -m py_compile learning_agent\app\gui_agent_adapter.py learning_agent\tests\test_gui_direct_oauth_sse_adapter.py` 成功，`python -m pytest learning_agent\tests\test_gui_direct_oauth_sse_adapter.py learning_agent\tests\test_gui_direct_oauth_cancel.py -q` 为 7 passed。
- 剩余门禁：完整 pytest/npm/lint/build/secret scan 还需要统一跑一遍；fake fixture 与真实 ChatGPT OAuth direct SSE 还需要使用真实可见 OpenHarness Desktop GUI 进行验收。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 Verification Update

- 完整自动化门禁已通过：provider secret leak scanner、GUI turn payload、OS secret store、OAuth disconnect、real OAuth attempt、provider runtime state、model registry、ChatGPT Codex SSE client、legacy wrapper、direct OAuth SSE adapter、cancel 测试均通过。
- 前端完整门禁已通过：`npm test -- --run` 为 17 files / 76 tests passed，`npm run lint` 退出码 0，`npm run build` 成功生成 Vite production renderer。
- 真实可见 GUI fake fixture 验收已通过：OpenHarness Desktop 窗口中输入 `请输出 OPENHARNESS_OK` 后，主线程显示 `OPENHARNESS_OK`，右侧事件流可见 `direct_sse_route_selected`、`message_delta`、`message_completed`、`direct_sse_completed`、`gui_turn_completed`。
- 真实 OAuth direct SSE 验收未完成：已用 `real_browser + experimental + os_encrypted + direct_sse + GUI trace` 启动真实模式，并打开 OpenAI 登录窗口；窗口停在“欢迎回来/电子邮件地址”页面，4 分钟轮询 provider catalog 均为 `connected=false`。
- 当前停止条件：由于 OpenAI 账号登录/授权属于用户认证动作，agent 不能代替用户输入账号或点击认证步骤；用户手动完成 OAuth 后，需要继续验证 provider 变为 `direct_sse_ready`、底部模型可选、真实 prompt 返回模型 delta。

## 2026-06-27 Direct ChatGPT OAuth SSE V3 External Browser Fix

- 真实 GUI 验收继续推进时发现 OAuth 链接最初会打开到 Electron 内部 `欢迎回来 - OpenAI` 窗口，无法复用用户 Edge/系统浏览器中的 ChatGPT 登录态。
- 已新增 `apps/desktop/src/main/externalLinks.ts`，并在 `apps/desktop/src/main/index.ts` 里拦截 `target=_blank` 和外部导航：OpenAI/OAuth/http(s) 外链交给系统浏览器，Vite renderer 自身仍留在 Electron 内部。
- 已新增 `apps/desktop/tests/externalLinks.test.ts`，覆盖 OpenAI OAuth 外链、renderer 同源保留、坏 URL 不崩溃三条规则；`npm test -- --run externalLinks.test.ts` 为 3 passed，`npm run lint` 通过。
- 已用真实可见 GUI 验证修复效果：点击 OpenAI `访问此链接` 后，授权页打开在 Microsoft Edge，Electron 窗口只保留 OpenHarness Desktop 主窗口。
- 剩余真实 OAuth 验收仍未完成：provider catalog 当前仍为 `connected=false`，需要用户在 Edge 中完成 OpenAI 登录/授权后继续验证真实 direct SSE 模型调用。

## 2026-06-27 Direct ChatGPT OAuth Callback Debugging

- 用户反馈已手动点击认证，但 OpenAI 官方认证返回后被拒绝；本轮按 systematic debugging 只做证据收集，没有先改代码。
- 运行时证据：`/v2/gui/provider-settings/providers` 显示 OpenAI 仍为 `connected=false`，secret store 为 `os_encrypted`，但没有账号标签或 direct route 状态。
- 事件证据：`memory/status/events.jsonl` 只有上一轮 fake fixture `direct_sse_route_selected/message_delta/direct_sse_completed` 事件，没有任何 OAuth callback/token exchange 事件。
- 路由证据：当前 `gui_bridge.py` 有 `auth-attempt/start/status/complete/cancel`，但没有 `/auth/callback` GET 路由；`complete_real_provider_auth_attempt_with_tokens()` 虽已存在，但没有生产 HTTP callback 调用它。
- 端口证据：`localhost:1455` 没有监听，`127.0.0.1:8776` 是当前 bridge；`8776/auth/callback` 返回 404，`1455/auth/callback` 超时。
- 生成 URL 证据：新 auth-attempt 为 `real_browser`，redirect 到 `http://localhost:1455/auth/callback`，client id 来源为 `observed_opencode_reference`，originator 当前为 `openharness`。
- 当前结论：真实 OAuth 连接失败的已确认根因是 Desktop 新链路缺少 callback server/token exchange 闭环；下一步应按旧 `CodexOAuthChatModel._login_with_browser()` 的工作模式补齐 callback 接收、state 校验、token exchange、状态落盘和 GUI 可见错误面。

## 2026-06-27 Direct ChatGPT OAuth Callback Loop Fix

- 已按 TDD 补齐两个红灯测试：`test_openai_oauth_code_exchange_posts_form_request` 证明 callback code 必须 POST 到 `https://auth.openai.com/oauth/token`，`test_real_oauth_callback_listener_exchanges_code_and_updates_catalog` 证明本机 callback listener 收到 `code/state` 后必须交换 token 并把 OpenAI provider 刷新为 `connected=true`、`source=oauth`、`direct_route_status=direct_sse_ready`。
- 已实现 `exchange_openai_oauth_code_for_tokens()`，使用标准 OAuth form body 携带 `grant_type=authorization_code`、`code`、`redirect_uri`、`client_id`、`code_verifier`，并把 HTTP/network/bad JSON 错误收敛为 GUI 可显示的结构化错误。
- 已实现 Desktop provider auth-attempt 的本机 callback 闭环：真实 OAuth start 后启动 `localhost:<callback_port>` listener，`/auth/callback` 校验 state、接收 code、交换 token、复用 `complete_real_provider_auth_attempt_with_tokens()` 安全落盘；失败、取消和端口不可用都会清理进程内 PKCE verifier/state，避免永久 pending。
- 安全边界：callback handler 关闭默认 HTTP 访问日志，避免 authorization code 进入日志；错误页面只显示短错误消息；主 provider settings 仍只保存 secret refs，不保存明文 access/refresh/id token。
- 自动化验证已通过：`python -m pytest learning_agent\tests\test_gui_provider_openai_real_oauth_attempts.py -q` 为 4 passed；provider/settings/model/direct SSE 相关 pytest 为 15 passed；`python -m py_compile learning_agent\app\gui_provider_auth_attempts.py learning_agent\app\gui_provider_openai_oauth.py` 通过；`python learning_agent\scripts\assert_no_real_provider_secret_leaks.py` 输出 `Provider secret leak scan passed.`；`apps/desktop` 的 `npm test` 为 18 files / 79 tests passed，`npm run lint` 通过。
- 真实可见 GUI smoke 已完成：使用隔离端口启动 `bridge=http://127.0.0.1:8876`、`renderer=http://127.0.0.1:5477` 的 OpenHarness Desktop 窗口，设置 -> 提供商页面能正常加载 provider 列表；调用 `auth-attempt/start` 后返回 `mode=real_browser` 的 OpenAI 官方授权 URL，并确认 `localhost:1455` 由 bridge 进程监听；随后取消测试 attempt 并关闭测试连接弹窗，窗口保留在 provider 列表页。
- 仍未声明真实模型连接最终完成：当前自动化已经证明 callback/token exchange 闭环可用，但真实 OpenAI 官方 OAuth 页面仍需要用户在浏览器中完成授权；完成后还需要真实可见 OpenHarness Desktop GUI 验证 provider 变为 `direct_sse_ready`、底部模型可选、真实 prompt 产生 direct SSE delta。

## 2026-06-27 Direct ChatGPT OAuth Callback Owner Probe Progress

- 已按 systematic debugging 找到“网页认证后 GUI 连接状态无法保持”的更具体根因：旧测试 bridge `8876` 仍占用 `localhost:1455`，官方回调会落到旧进程，当前 GUI bridge 的 OAuth `state` 无法匹配。
- 已按 TDD 增加回归测试 `test_real_oauth_start_rejects_when_localhost_routes_to_another_callback_owner`，模拟 `localhost:<callback_port>` 被其他 listener 接走时，OpenHarness 必须拒绝开始 OAuth，而不是生成一个必然失败的官方授权 URL。
- 已实现 callback owner health probe：callback listener 启动后必须通过 `/auth/callback/health?owner=<token>` 证明当前 server 才是真正接收 `localhost:<port>` 的进程；旧进程、错误 listener、HTTP 404/500 都会快速失败。
- 已把 OpenAI OAuth URL 的 `originator` 从 `openharness` 改为 `opencode`，与 `D:\opencode` 参考实现保持一致。
- 已保存本次修改学习副本到 `learning_agent/test/openai_oauth_callback_owner_probe_fix/source_copies/`。
- 自动化验证已通过：`python -m py_compile learning_agent/app/gui_provider_auth_attempts.py learning_agent/app/gui_provider_openai_oauth.py`；`python -m pytest learning_agent/tests/test_gui_provider_openai_real_oauth_attempts.py -q` 为 6 passed；相关 provider/model/OAuth backend group 为 14 passed。
- 运行时清理已完成：旧 `8876` bridge、`5477` renderer 和对应 Electron smoke 窗口已停止；`Get-NetTCPConnection` 确认没有 `8876/5477` listener。
- 修复版 OpenHarness Desktop 已重新启动：当前 `8776` listener 为 PID `41600`，`5177` listener 为 PID `16932`，`1455` listener 也归 PID `41600`，说明官方 OAuth callback 会回到当前 bridge。
- 已用真实后端合同验证：`/v2/gui/provider-settings/providers` 可返回 OpenAI provider；`/v2/gui/provider-settings/auth-attempt/start` 可生成 `mode=real_browser` 的 OpenAI 官方授权 URL，URL 包含 `originator=opencode` 和 `redirect_uri=http://localhost:1455/auth/callback`；测试 attempt 已取消，避免遗留 pending。
- Remaining open risk: 真实可见 OpenAI 官方网页登录/授权仍需用户手动完成；完成后还要检查 provider catalog 变成 `connected=true/source=oauth/direct_sse_ready`，再发真实 prompt 验证 direct SSE delta。

## 2026-06-27 Direct ChatGPT OAuth SSE Real GUI Reply Fix

- 用户已手动完成 OpenAI OAuth 后，真实 GUI 消息窗口仍不能正常回复；本轮使用真实可见 OpenHarness Desktop 窗口发送 `请只回复 OH_FIXED_OK` 复现问题。
- 已确认 provider catalog 不是问题：OpenAI provider 返回 `connected=true`、`source=oauth`、`direct_route_status=direct_sse_ready`，说明后端 token 连接成功。
- 第一层根因：GUI adapter 把 OpenHarness 内部 `metadata` 字段发送给 `https://chatgpt.com/backend-api/codex/responses`，真实后端返回 `{"detail":"Unsupported parameter: metadata"}`。
- 第二层根因：GUI 底部“超高/ultra”被原样传为 `reasoning.effort=ultra`，真实后端返回 `Invalid value: 'ultra'. Supported values are: 'none', 'minimal', 'low', 'medium', 'high', and 'xhigh'.`
- 第三层根因：修正请求体后，真实 SSE 进入 HTTP 200，但 parser 不认识 `response.content_part.added` / `response.content_part.done`，误报 `endpoint_drift_detected`。
- 已按 TDD 修复：`_direct_sse_extra_body()` 现在把 `ultra` 映射为 `xhigh`，并只向真实 ChatGPT Codex API 发送支持的 `reasoning` 字段；`KNOWN_NON_TEXT_EVENT_TYPES` 现在接受真实 content part 事件。
- 自动化验证通过：`python -m pytest learning_agent\tests\test_gui_direct_oauth_sse_adapter.py learning_agent\tests\test_chatgpt_codex_sse_client.py learning_agent\tests\test_gui_turn_payload_contract.py -q` 为 12 passed。
- 学习副本已保存到 `learning_agent/test/direct_sse_real_gui_reply_fix/`，包含 `gui_agent_adapter.py`、`chatgpt_codex_sse.py` 和两份相关测试。
- 当前 GUI 已用新代码重启到 `bridge=8776`、`renderer=5177`；真实可见 GUI 最终验收已通过：在 OpenHarness Desktop 消息窗口发送 `请只回复 OH_FINAL_OK` 后，主消息区返回 `OH_FINAL_OK`，右侧事件流出现 `runtime_path`、`message_delta`、`direct_sse_completed`、`message_completed`、`gui_turn_completed`，且 `runtime_path` 显示 `runtime=direct_sse`、`transport=https_sse`、`websocket_enabled=false`、`codex_cli_used=false`。

## 2026-06-27 OpenHarness Desktop GUI Context Compact V4 Progress

- 已按 `docs/superpowers/plans/2026-06-27-openharness-desktop-gui-context-compact-v4.md` 完成 GUI 消息窗口上下文接入：`gui_bridge.py` 从真实 GUI session messages 构建上下文，`gui_agent_adapter.py` 把完整 context messages 传入 direct SSE，`gui_context.py` 负责按 `OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES` 与 `OPENHARNESS_GUI_CONTEXT_MAX_CHARS` 做可测试压缩。
- 已接入隐私安全事件：真实 GUI turn 会输出 `context_budget`、必要时输出 `compact_completed`，事件只记录消息数量、字符预算、压缩代数和原因，不输出原文 compact summary、OAuth token、secret ref 或 raw access token。
- 自动化门禁已通过：上下文 builder、Direct SSE context body、GUI turn payload、ChatGPT Codex SSE client、provider/model runtime、frontend test/lint、py_compile 和 provider secret leak scanner 均完成过验证；最后一轮协议修复后，`test_gui_context_builder.py`、`test_gui_direct_oauth_sse_adapter_context.py`、`test_chatgpt_codex_sse_client_context_body.py` 为 9 passed。
- 真实可见 GUI no-compact 验收已通过：在 OpenHarness Desktop 输入 `请记住这个测试代码：ALPHA_CONTEXT_927。只回复：已记住。` 后返回 `已记住。`；随后输入 `刚才的测试代码是什么？只输出代码。`，事件显示 `compacted=false`、`reason=compact_not_needed`，模型返回 `ALPHA_CONTEXT_927`。
- 真实可见 GUI forced-compact 验收已通过：使用 `OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES=5`、`OPENHARNESS_GUI_CONTEXT_MAX_CHARS=900` 启动，连续发送 5 条补充上下文后右侧事件流可见 `compact_completed`；最终输入 `刚才我让你记住的测试代码是什么？只输出代码。`，事件显示 `compacted=true`、`reason=compacted_before_model`、`runtime=direct_sse`、`websocket_enabled=false`、`codex_cli_used=false`，模型返回 `ALPHA_CONTEXT_927`。
- 验收期间按 systematic debugging 发现并修复真实协议 bug：assistant 历史消息不能以 `input_text` 发送到 ChatGPT Codex endpoint，必须使用 `output_text`；修复后最小真实 HTTP SSE 诊断从 HTTP 400 变为 HTTP 200，并在真实 GUI 中复测通过。
- 学习副本已保存到 `learning_agent/test/gui_context_compact_v4/` 根目录和 `learning_agent/test/gui_context_compact_v4/source_copies/`，包含 `gui_context.py`、`gui_agent_adapter.py`、`gui_bridge.py`、`gui_protocol.py`、`chatgpt_codex_sse.py` 和相关测试文件。
- 最终 release gate 已通过：上下文/Direct SSE 相关 `pytest` 为 25 passed；provider/model runtime 相关 `pytest` 为 13 passed；`py_compile` 通过；`assert_no_real_provider_secret_leaks.py` 输出 `Provider secret leak scan passed.`；`npm --prefix apps/desktop test -- --run` 为 18 files / 79 tests passed；`npm --prefix apps/desktop run lint` 通过；`npm --prefix apps/desktop run build` 成功生成 production renderer。

## 2026-06-27 Real Model Observability V1 Safe Worktree Progress

- 已按“只迁移安全可并入主链路的真实模型状态观测能力”创建隔离 worktree：`H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\real-model-observability-v1`，分支为 `codex/real-model-observability-v1`，基线为 `codex/publish-main`。
- 已先写红灯测试并确认失败原因符合预期：前端 `modelCallStatus.test.tsx` 最初因缺少 `ModelCallStatus` 失败；后端协议测试最初因 `model_call_started` 未进 GUI V2 白名单失败；Direct SSE adapter 测试最初因缺少 `model_call_started/model_first_delta/model_call_completed` 失败。
- 已新增 `ModelCallStatus` 组件，把 `model_call_started`、`model_call_status`、`model_first_delta`、`model_call_completed`、`model_call_failed` 渲染为底部 composer 小状态条和右侧状态面板摘要，状态只展示模型名、阶段和耗时，不暴露 OAuth token 或请求体。
- 已把上述事件加入 GUI V2 协议白名单，并让 Direct SSE 真实路径在开始、首字、完成和失败时发出模型调用状态事件；原有 `runtime_path`、`message_delta`、`direct_sse_completed`、`message_completed` 事件继续保留。
- 已保存学习副本到 `learning_agent/test/real_model_observability_v1/`，包含本轮新增/修改的前端组件、样式、测试、后端协议和 Direct SSE adapter 文件。
- 自动化验证已通过：`npm --prefix apps/desktop test -- --run tests/modelCallStatus.test.tsx` 为 3 passed；`python -m pytest learning_agent\tests\test_gui_protocol_contract.py learning_agent\tests\test_gui_direct_oauth_sse_adapter.py::test_direct_sse_adapter_emits_runtime_path_and_streaming_events -q` 为 6 passed；桌面完整 `npm --prefix apps/desktop test -- --run` 为 19 files / 82 tests passed；相关后端 pytest 为 17 passed；`npm --prefix apps/desktop run lint`、`python -m py_compile learning_agent\app\gui_protocol.py learning_agent\app\gui_agent_adapter.py`、`npm --prefix apps/desktop run build` 均通过。
- 真实可见 GUI smoke 已通过：使用隔离端口启动 `bridge=http://127.0.0.1:8891` 和 `renderer=http://127.0.0.1:5177` 的 OpenHarness Desktop；窗口可见、底部 composer 没有被新增状态槽挤坏，设置 -> 提供商页面可正常加载 OpenAI/GitHub Copilot/Google/OpenRouter/Vercel AI Gateway/自定义提供商列表，没有出现“提供商加载失败”；验收后已关闭 Electron、停止测试 bridge，并清理残留 renderer dev server。
- 当时尚未合并入主链路：该 worktree 改动已收束且进入人工 diff review / staged merge；实际合并结果见下一节，旧 `.worktrees/chatgpt-oauth-real-model-v1` 仍未删除，建议单独审计后再清理。

## 2026-06-27 Real Model Observability V1 Mainline Merge

- `codex/real-model-observability-v1` 已通过快进合并进入主链路 `codex/publish-main`，合并提交为 `4023652b Add real model observability status`；如果没有这条记录，后续排查会误以为该能力仍停留在隔离 worktree。
- 主链路自动化验证已通过：`npm --prefix apps/desktop test -- --run` 为 19 files / 82 tests passed；Direct SSE/GUI protocol 相关 pytest 为 17 passed；`python learning_agent\scripts\assert_no_real_provider_secret_leaks.py` 输出 `Provider secret leak scan passed.`；`npm --prefix apps/desktop run lint`、`npm --prefix apps/desktop run build`、`python -m py_compile learning_agent\app\gui_protocol.py learning_agent\app\gui_agent_adapter.py` 均通过。
- 主链路真实可见 GUI smoke 已通过：使用 `bridge=http://127.0.0.1:8891` 和 `renderer=http://127.0.0.1:5177` 启动 OpenHarness Desktop，底部 composer 布局正常，设置 -> 提供商页面成功加载 OpenAI/GitHub Copilot/Google/OpenRouter/Vercel AI Gateway/自定义提供商列表，没有出现“提供商加载失败”。
- 验收清理已完成：主链路 smoke 后已关闭 Electron、停止 bridge，并确认 `8891` 与 `5177` 没有 listener；旧 `.worktrees/chatgpt-oauth-real-model-v1` 仍保留，建议下一步单独审计后再决定是否删除。

## 2026-06-27 Old ChatGPT OAuth Worktree Audit

- 已审计旧 worktree `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\chatgpt-oauth-real-model-v1`：分支提交 `026d2ba0` 已经是主链路 `codex/publish-main` 的祖先，因此已提交历史本身不再阻止清理。
- 不能直接删除该 worktree：工作区仍有 34 个 tracked 文件未提交修改、87 个 untracked 文件；其中 83 个 untracked 文件在主链路不存在，4 个同路径文件存在但内容不同。
- 风险文件包括本地运行状态与敏感状态路径，例如 `memory/gui_provider_settings/secrets.dev.json`；本轮没有 stash、提交或复制这些内容，避免把本地 secret/令牌状态写入 Git 历史。
- 旧 worktree 未发现真实运行进程占用，查询到的匹配进程只是本轮审计命令本身；因此当前阻塞不是进程占用，而是未审阅的工作区内容。
- 当前停止条件：需要用户或后续任务明确选择“迁移剩余独有文件”“脱敏归档证据文件”或“确认放弃旧工作区未提交内容”之一；在此之前不删除 `.worktrees/chatgpt-oauth-real-model-v1`，也不删除 `codex/chatgpt-oauth-real-model-v1` 分支。

## 2026-06-27 Old ChatGPT OAuth Worktree Migration Inventory

- 已生成迁移/放弃清单：`agent_memory/old_chatgpt_oauth_worktree_migration_inventory_20260627.md`。
- 清单结论：旧 worktree 不可整体合并，不可直接删除；主链路已经覆盖 ModelCallStatus、Direct SSE/OAuth 生产路径和真实模型观测事件。
- 可参考但不直接迁移：`gui_model_latency_diagnostics.py`、`test_gui_model_latency_diagnostics.py`、`models/streaming.py`、`models/codex_cli_stream.py`、`realModelLatencyEvents.test.ts`。
- 可低风险归档候选：两份 `2026-06-26-openharness-desktop-real-model-latency-v2*.md` 计划/评估文档，但仍需人工确认没有敏感运行细节。
- 明确不迁移：旧 worktree 的 `memory/`、OAuth/provider 本地状态、raw stdout/stderr logs、PID/evidence JSON，除非用户单独要求脱敏归档。
- 下一步建议：若继续推进，先归档两份计划文档；若要做工程功能，则另起干净蓝图 `Transport Diagnostics Tab V1`，只借鉴旧诊断缓存思想，不复制旧实现。

## 2026-06-27 Old ChatGPT OAuth Worktree Plan Docs Migration

- 已从旧 worktree 迁移两份低风险历史设计资料到主链路：`docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2.md` 和 `docs/superpowers/plans/2026-06-26-openharness-desktop-real-model-latency-v2-karpathy-review.md`。
- 迁移前已做两层检查：先查找敏感关键词，再用更严格的 token 形态扫描真实 API key、Bearer token、OAuth token、callback code、client secret；未发现真实凭据形态。
- 本轮没有迁移旧 worktree 的实验代码、`memory/`、raw logs、PID/evidence JSON；这些内容仍按风险内容处理，不能直接提交或复制。
- 当前清理状态：低风险计划文档已保留；若用户确认放弃旧 worktree 的剩余未提交内容，下一步可以用 `git worktree remove --force .worktrees/chatgpt-oauth-real-model-v1` 做正式清理。

## 2026-06-27 Old Worktree Final Cleanup

- 用户已明确确认放弃旧 worktree 剩余未提交内容。
- 已在删除前确认 `.worktrees/chatgpt-oauth-real-model-v1` 路径位于当前项目 `.worktrees` 下，避免误删项目外目录。
- 已确认旧分支 `codex/chatgpt-oauth-real-model-v1` 的提交 `026d2ba0` 是当前主链路祖先，已提交历史不再阻止清理。
- 已执行正式 Git 清理：`git worktree remove --force .worktrees/chatgpt-oauth-real-model-v1`、`git branch -D codex/chatgpt-oauth-real-model-v1`、`git worktree prune`。
- `.worktrees` 目录在清理后为空，已删除空目录；当前 `git worktree list` 只剩主工作区 `H:/codexworkplace/sofeware/OpenHarness-main`。

## 2026-06-27 CodeGraph Refresh After Worktree Cleanup

- 已在主工作区执行 `codegraph sync .`，CodeGraph 返回 `Already up to date`。
- 已复查 `codegraph status .`：索引状态为 `[OK] Index is up to date`，当前统计为 1,154 files、30,114 nodes、41,300 edges。
- 已用 `codegraph query ModelCallStatus --limit 10` 验证新近主链路符号可被查询到，结果包含 `apps/desktop/src/components/ModelCallStatus.tsx`。
- 已确认 `.worktrees` 目录不存在，`git worktree list` 只剩主工作区；知识图谱已经对齐到旧 worktree 删除后的当前主链路。

## 2026-06-27 Restore OpenAI OAuth Connect UI

- 用户指出上一轮把默认 OpenAI OAuth 入口禁用为只剩 API key 的方向不对；真实需求是恢复 Codex/OpenCode 风格 OAuth 界面，并修复 OAuth 官网打不开。
- 已用 `git revert ce510b38` 恢复上一轮隐藏 OAuth 入口的代码和测试改动，OpenAI 连接弹窗重新保留 `ChatGPT Pro/Plus (browser)`、`ChatGPT Pro/Plus (headless)`、`API 密钥` 三种方式。
- 已重新用真实 OAuth 环境启动 OpenHarness Desktop：`OPENHARNESS_OPENAI_AUTH_MODE=real_browser`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1`、`OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`、`OPENHARNESS_OPENAI_CLIENT_ID=app_EMoamEEZ73f0CkXaXp7hrann`、`OPENHARNESS_OPENAI_RUNTIME=direct_sse`。
- 运行时验证：调用 `/v2/gui/provider-settings/auth-attempt/start` 创建 OpenAI browser attempt，返回 `mode=real_browser`，授权 URL host 为 `auth.openai.com`，callback 端口 `1455` 已监听；测试 attempt 已取消，用户可在 GUI 中重新点击正式连接。
- 当前 GUI 已重新拉起：bridge 监听 `8776`，renderer 监听 `5177`，Electron renderer 连接 `http://127.0.0.1:8776`。

## 2026-06-27 OpenHarness Desktop OAuth One-Click Launch Script

- 已新增根目录双击入口 `start_openharness_desktop_oauth.bat`，它会调用 `apps/desktop/scripts/start-openharness-desktop-oauth.ps1`，统一启动真实 OAuth/Direct SSE 版本的 OpenHarness Desktop GUI。
- 一键脚本会设置真实 OAuth 链路所需环境：`OPENHARNESS_OPENAI_AUTH_MODE=real_browser`、`OPENHARNESS_OPENAI_RUNTIME=direct_sse`、`OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted`、`OPENHARNESS_OPENAI_EXPERIMENTAL=1`、OpenCode 参考 client id、callback 端口 1455 和 bridge token。
- 一键脚本会在启动前检查并清理当前仓库旧 OpenHarness 进程占用的 8776/5177/1455 端口；若端口属于非 OpenHarness 进程则拒绝误杀并报错。
- 已修改 `start-backend.ps1` 与 `start-desktop-dev.ps1` 支持 `OPENHARNESS_DESKTOP_LAUNCH_LOG_DIR`，一键脚本默认把日志写入 `%TEMP%\openharness-desktop-oauth-*`，避免普通用户双击启动污染仓库未跟踪文件。
- 已保存学习副本到 `learning_agent/test/openharness_desktop_oauth_one_click_launch_20260627/source_copies/`，包含新增脚本、被修改启动脚本和测试。
- 自动化验证已通过：一键启动脚本静态合同测试 4 passed；provider/OAuth 回归 12 passed；桌面前端 vitest 19 files / 82 tests passed；PowerShell parser 和 Python py_compile 均通过。
- 真实可见 GUI 验收已用 computer-use 完成：脚本真实拉起 OpenHarness Desktop，设置 -> 提供商页面可见 OpenAI `已连接`、`ChatGPT OAuth`、`Direct ChatGPT OAuth SSE 已就绪`，右侧事件流可见 `direct_sse_completed` 和 `model_call_completed`。
## 2026-06-27 OpenHarness Desktop OAuth One-Click Bat Codepage Fix

- 已复现用户反馈的双击失败：bat 中 UTF-8 中文 REM 在默认 cmd 代码页下被误解析成命令，输出 `'不会启动' is not recognized as an internal or external command`。
- 已按 TDD 新增 `test_root_batch_sets_utf8_codepage_before_chinese_text`，先确认红灯失败，再在 bat 第二行加入 `chcp 65001 >nul` 并转绿。
- 已用同一个 bat 入口重新执行启动：脚本释放旧 8776/5177 端口，启动 bridge，验证 OpenAI OAuth URL 为 `auth.openai.com`，启动 Desktop launcher。
- 已用 computer-use 在真实 OpenHarness Desktop GUI 输入 `hello` 并发送，模型返回 `Hello! How can I help you today?`，事件流显示 `direct_sse_completed`、`message_completed`、`gui_turn_completed`。
- 学习副本已同步到 `learning_agent/test/openharness_desktop_oauth_one_click_launch_20260627/source_copies/`。

## 2026-06-27 OpenHarness Desktop Real Agent Harness Adapter Blueprint V2

- 已根据 Karpathy-style 工程评估升级书面蓝图：`docs/superpowers/plans/2026-06-27-openharness-desktop-real-agent-harness-adapter.md`。
- V2 蓝图核心变化：不再先铺满完整架构，而是新增 Phase 0 模型工厂与 `AgentEvent` 探针，先证明 GUI provider 凭据能创建 `LearningAgent` 可用的 `ChatModel`，并记录真实 `run_events()` JSONL 轨迹。
- V2 蓝图把 Phase 1 收敛为最小真实闭环：GUI Agent mode prompt -> `RealHarnessGuiAgentAdapter` -> `LearningAgent.run(...)` -> `LearningAgent.run_events(...)` -> GUI `message_completed`，明确不接写文件、shell、MCP、Computer Use 或复杂恢复。
- V2 蓝图要求事件映射来自 `learning_agent/tests/fixtures/gui_agent_traces/*.jsonl` 轨迹语料，而不是靠猜测事件名；`gui_agent_event_mapper.py` 负责中心化脱敏、稳定事件名和未知安全事件诊断。
- V2 蓝图把 GUI 权限握手前置为写能力门禁：没有 `permission_requested` / `permission_answered` 可见闭环前，不允许上线写文件、shell、MCP 或 Computer Use。
- V2 蓝图最终阶段才接受控 Computer Use agent mode，并要求沿用现有 Computer Use MCP v2 权限、lock、abort、trace 和真实可见 GUI 验收边界。
- 已按用户补充要求加入 Mandatory Visible GUI Acceptance Rule：所有可见 GUI 验收必须使用肉眼可见的真实 OpenHarness Desktop GUI，并用 `computer-use` 确认；若验收发现 bug，必须先用 `superpowers:systematic-debugging` 查根因、修复、重新测试，通过后才继续下一个任务。
- 本轮只修改书面蓝图和进度记录，没有改运行代码；占位词和旧乱码中文 prompt 扫描已通过。

## 2026-06-27 Real Agent Harness Adapter V2 Execution

- 已在隔离 worktree `.worktrees/real-agent-harness-adapter-v2` 创建分支 `codex/real-agent-harness-adapter-v2`，按蓝图逐项执行 Phase 0-6。
- Phase 0/1 已完成：新增 `gui_model_factory.py`、`gui_harness_adapter.py`、`gui_agent_event_mapper.py`，GUI 真实模式可通过 `DefaultHarnessGuiAgentAdapter(enabled=True)` 进入 `LearningAgent.run(...)` 主循环，第一条事件为 `runtime_path runtime=agent_harness`。
- Phase 2 已完成：新增 `learning_agent/tests/fixtures/gui_agent_traces/*.jsonl` 五类轨迹样本和 `test_gui_agent_event_mapper.py`，覆盖无工具成功、模型失败、中途取消、权限拒绝、只读工具成功，并加入长 stdout/stderr 截断门禁。
- Phase 3 已完成：真实 `LearningAgent` 主循环可在只读白名单下执行 `read_file`，并把 `tool_started` / `tool_finished` 写入 GUI 事件流。
- Phase 4 已完成：真实 adapter 的 `ask_permission` 已接入 GUI `permission_requested` / `permission_answered` 事件，approve 返回 True，deny/cancel 返回 False；`write_file` 被拒绝时测试确认目标文件不落盘。
- Phase 5 已完成：`GuiRunManager._run_turn_worker()` 不再持锁执行长 adapter，取消和权限决策可并发进入；重启后遗留 `queued/running/needs_permission/cancelling` turn 会自动收敛为 failed，并释放 active turn。
- Phase 6 已完成：默认真实 agent harness 不暴露 Computer Use 工具，模型伪造 `mcp__computer-use__click` 会被 allowed_tools 门禁拒绝，只留下可见工具拒绝轨迹，不执行桌面动作。
- 自动化验证已阶段性通过：`test_gui_agent_event_mapper.py` 6 passed；`test_gui_agent_permission_handshake.py` 4 passed；`test_gui_agent_cancellation_recovery.py` 2 passed；`test_gui_agent_computer_use_guard.py` 1 passed；`test_gui_real_harness_adapter.py` 包含真实主循环和只读工具测试。
- 待完成最终门禁：同步学习副本、运行更宽测试集、执行 provider secret leak scan、运行前端测试，并使用真实可见 OpenHarness Desktop GUI + computer-use 完成验收。

## 2026-06-27 Real Agent Harness Adapter V2 Final Completion

- Phase 0/1 最小真实闭环已在真实 OpenHarness Desktop GUI 中通过：发送 `__real_harness__ AGENT_HARNESS_SMOKE` 后，主消息区显示 `AGENT_HARNESS_SMOKE_OK`，右侧事件包含 `runtime_path`、`run_completed`、`message_completed`、`gui_turn_completed`。
- Phase 3 只读工具轨迹已在真实 GUI 中通过：发送 `__real_harness__ __read_only_tool__ READ_ONLY_TOOL_TRACE` 后，事件流出现 `read_file` 的 `tool_started/tool_finished`，最终回答为 `READ_ONLY_TOOL_TRACE_OK`。
- Phase 4 权限握手已在真实 GUI 中通过：发送 `__real_harness__ __permission__ AGENT_HARNESS_SMOKE` 后，事件出现 `permission_requested`、`permission_answered`，决策为 `approve/approved`，随后 real harness 完成。
- Phase 5 取消恢复已在真实 GUI 中通过：发送 `__real_harness__ __slow__ AGENT_HARNESS_SMOKE` 后点击红色取消按钮，后端写出 `gui_turn_cancel_requested` 与 `gui_turn_cancelled`；之后再次发送普通 real harness smoke 可正常完成。
- Phase 6 Computer Use 安全门禁已在真实 GUI 中通过：右侧“浏览器”页签显示 `visible_chromium`、`real_chrome_cdp` 可用，Computer Use 区块显示 `mode=off`、`permission_mode=off`、`lock=unlocked`、`abort requested=false`，说明默认未放开桌面动作。
- 最终自动化门禁通过：后端 real harness 相关 pytest 19 passed；provider secret leak scan passed；关键 Python 文件内存 compile syntax ok；桌面 Vitest 19 files / 82 tests passed；桌面 lint/typecheck passed；桌面 production build passed。
- 验收期间启动的 bridge 为 `http://127.0.0.1:8776`，真实可见 Electron 窗口标题为 `OpenHarness Desktop`；最终证据 JSON 位于 `learning_agent/test/real_agent_harness_adapter_v2/visible_gui_acceptance_20260627.json`。

## 2026-06-27 Real Agent Harness Adapter V2 Branch Closeout

- 按“先收口分支、再验证、再提交/合并”的下一步执行：清理 worktree 临时调试产物后，只保留蓝图任务相关代码、测试、证据、学习副本和 agent_memory 记录。
- 重新运行提交前门禁并通过：`git diff --check` clean；后端 real harness 相关 pytest 19 passed；provider secret leak scan passed；关键 Python 文件内存 compile syntax ok。
- 重新运行桌面前端门禁并通过：`npm --prefix apps/desktop test -- --run` 为 19 files / 82 tests passed；`npm --prefix apps/desktop run lint` passed；`npm --prefix apps/desktop run build` passed。
- 当前准备提交的范围已精确限定为 real agent harness adapter V2 所需文件，下一步是创建 feature commit，再评估主工作区脏改动是否允许安全合并。

## 2026-06-27 AGENTS Visible Acceptance Gate Hardening

- 按当前下一步建议，先收紧 `AGENTS.md` 的真实可见验收规则，避免主链路后续开发只用单元测试、日志或命令桥接替代真实终端/真实 GUI 验收。
- 已把规则十七升级为“真实终端和真实 GUI 场景验收强制门禁”：终端能力必须走用户可见终端入口，GUI 能力必须用 `computer-use` 观察和操作真实 OpenHarness Desktop 窗口。
- 已修正技能名为 `systematic-debugging`，并明确验收发现 bug 或异常时必须先查根因、修复、重新执行真实可见验收。
- 已补回规则二十二：简单 bug 直接修复，复杂 bug 必须给治本方案，不允许只给治标补丁。
