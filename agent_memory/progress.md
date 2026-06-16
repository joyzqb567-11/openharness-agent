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
