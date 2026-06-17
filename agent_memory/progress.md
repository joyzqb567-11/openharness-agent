# 当前任务进度摘要（2026-06-16）

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
