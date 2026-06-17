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
