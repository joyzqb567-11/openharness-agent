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

最新相关提交：`659b7c0 feat: return model-visible zoom screenshots`。

## 仍需完成

按照 AGENTS 规则十七，最终回答前还必须完成真实可见终端交互验收：启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`，在真实可见终端内输入接近真实用户习惯的 prompt，观察 agent 输出并确认 Computer Use 功能可用。自动化测试不能替代这个验收。
