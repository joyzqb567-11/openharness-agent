# Phase 43-52 Windows Computer Use Production Alignment

## 2026-06-03 Phase 52 真实可见终端验收完成记录

- Phase52 已通过 `learning_agent/acceptance_controller/controller.ps1` 接管真实可见 `learning_agent/start_oauth_agent.bat` 终端完成验收。
- 验收证据目录：`learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/`。
- `result.json` 记录 `completed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`、`permission_sent_count=0`、`max_permission_sent_count=0`。
- 最终回答和 debug log 均命中 `PHASE52_WINDOWS_PRODUCTION_MATRIX_READY`、`PHASE52_WINDOWS_PRODUCTION_MATRIX_OK`、`phase_count=9`、`native_capability=true`、`native_host=true`、`screenshot_runtime=true`、`uia_tree=true`、`sendinput_dispatcher=true`、`security_policy=true`、`tool_surface=true`、`recovery_runtime=true`、`status_ui=true`、`dispatcher_actions_expanded=true`、`actions_expanded=false`。
- 最终截图：`learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/03_final.png`，可见真实终端中的 Phase52 READY/OK 输出。

## 2026-06-03 Phase 52 自动化完成记录

- 新增 `learning_agent/computer_use/production_matrix.py`，汇总 Phase43-51 的生产级总矩阵。
- 新增 `learning_agent/tests/test_windows_computer_use_production_matrix_phase52.py` 和场景 `agent_capability_phase52_windows_production_matrix.json`。
- 红测先确认缺口：`ModuleNotFoundError: No module named 'learning_agent.computer_use.production_matrix'`。
- 修复 Phase43/Phase51 兼容回归：`/computer status` 继续显示 `Computer Native Capability Matrix`、Phase43 marker 和 `windows_sendinput`。
- 验证通过：Phase52 focused 2 tests OK；Phase43-52 regression 39 tests OK；`py_compile` OK；CLI self-check 输出 `PHASE52_WINDOWS_PRODUCTION_MATRIX_OK phase_count=9 ... dispatcher_actions_expanded=true actions_expanded=false`。
- 学习备份复制到 `learning_agent/test/agent_capability_phase52_windows_production_matrix_20260603/`。
- 已尝试启动真实可见 `learning_agent/start_oauth_agent.bat`，并在进程层面看到 `cmd`/`powershell`/`WindowsTerminal` 存在。
- 剩余门禁：当前 Codex 环境没有合法方式向真实可见终端输入 prompt 并观察输出，因此真实可见终端交互验收仍未完成，未完成前不能声明开发完成。

## 用户确认

用户已确认按蓝图从 Phase 43 执行到 Phase 52，中途不停止，直到所有阶段完成。

## 执行边界

- 本轮目标是把 Windows OS 级 Computer Use 从 Phase 42 的安全合同矩阵推进到更接近生产可用。
- ClaudeCode computer-use 源码作为架构参考，不复制 macOS Swift executor。
- 所有真实 Windows 动作必须经过 opt-in、allowlist、lock、abort、目标校验、审批和 evidence。
- 未完成真实可见终端交互验收时，不能声明开发完成。

## 阶段列表

- Phase 43: Windows 原生能力诊断升级。
- Phase 44: Windows Native Host / Helper 架构。
- Phase 45: 真实 Windows 截图能力。
- Phase 46: 真实 UIA 窗口树观察。
- Phase 47: 真实 SendInput 动作执行。
- Phase 48: 权限审批和安全策略升级。
- Phase 49: MCP / ClaudeCode 风格工具面兼容层。
- Phase 50: 全局 Abort / Cleanup / Lock 恢复。
- Phase 51: 类似 `/chrome` 的终端状态 UI。
- Phase 52: 自动化与真实可见终端端到端验收。

## 当前状态

Phase 43 已完成：新增 Windows native capability matrix，并接入 `WindowsComputerUseBackend.status()` 与 `/computer status`。自动化验证通过；真实可见终端总验收留到 Phase 52。

下一阶段进入 Phase 44：Windows Native Host / Helper 架构。
## 2026-06-03 Phase 44 完成记录

- Phase 44 已完成：新增 `learning_agent/computer_use/native_host.py`，建立 in-process Windows native host/client 合同。
- Host 支持 `status`、`observe`、`capture`、`action`、`cleanup` 五类消息。
- `action` 默认以 `real_action_refused_by_native_host` 拒绝，避免在架构阶段提前执行真实鼠标键盘动作。
- `capture` 只返回截图摘要和字节数量，不把原始截图 bytes 直接塞进 JSON 响应。
- 已新增 Phase44 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase44 focused 4 tests OK，Phase32/43/44 regression 14 tests OK，py_compile OK，CLI selftest 输出 `PHASE44_WINDOWS_NATIVE_HOST_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase44_windows_native_host_20260603/`。
- 下一阶段进入 Phase 45：真实 Windows 截图能力。

## 2026-06-03 Phase 45 完成记录

- Phase 45 已完成：新增 `learning_agent/computer_use/screenshot_runtime.py`，建立 WGC 优先、GDI fallback、evidence artifact 落盘的截图运行时。
- `WindowsScreenshotCaptureRuntime` 会记录 provider 尝试链，成功后通过 `ComputerUseEvidenceStore` 生成截图 artifact、metadata 和 `image_results`。
- 已修改 `learning_agent/computer_use/native_host.py`，让 native host 的 `capture` 消息可注入 Phase45 runtime，并继续保证响应中 `screenshot_bytes_included=false`。
- 已新增 Phase45 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase45 focused 4 tests OK，Phase32/36/44/45 regression 19 tests OK，py_compile OK，CLI selftest 输出 `PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase45_windows_screenshot_runtime_20260603/`。
- 下一阶段进入 Phase 46：真实 UIA 窗口树观察。

## 2026-06-03 Phase 46 完成记录

- Phase 46 已完成：新增 `learning_agent/computer_use/uia_tree.py`，建立结构化 UIA 控件树 runtime。
- `WindowsUiaControlTreeRuntime` 会返回控件名称、角色、automation id、class、边界框、enabled、clickable、editable、层级和 children，并执行节点数/深度/文本长度限制。
- 已修改 `learning_agent/computer_use/native_host.py`，让 native host 的 `observe` 消息可注入 Phase46 runtime，并继续保证只读观察不扩大动作面。
- 已新增 Phase46 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase46 focused 4 tests OK，Phase34/44/45/46 regression 18 tests OK，py_compile OK，CLI selftest 输出 `PHASE46_WINDOWS_UIA_TREE_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase46_windows_uia_tree_20260603/`。
- 下一阶段进入 Phase 47：真实 SendInput 动作执行。

## 2026-06-03 Phase 47 完成记录

- Phase 47 已完成：新增 `learning_agent/computer_use/sendinput_dispatcher.py`，建立 Windows SendInput dispatcher。
- Dispatcher 会把 move、click、double_click、scroll、press_key、type_text 展开成低层事件，并在发送前执行目标窗口稳定校验。
- `type_text` 低层事件只保留长度、短哈希和 `text_redacted=true`，不会把原始文本交给 host 响应或低层事件记录。
- 已修改 `learning_agent/computer_use/native_host.py`，让 native host 的 `action` 消息在显式启用并注入 executor 时可走 Phase47 dispatcher；默认仍拒绝。
- 已新增 Phase47 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase47 focused 4 tests OK，Phase37/44/47 regression 13 tests OK，py_compile OK，CLI selftest 输出 `PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase47_windows_sendinput_dispatcher_20260603/`。
- 下一阶段进入 Phase 48：权限审批和安全策略升级。

## 2026-06-03 Phase 48 完成记录

- Phase 48 已完成：新增 `learning_agent/computer_use/security_policy.py`，建立 observe/action/system_key/clipboard grant 分类和高风险默认拒绝策略。
- 已修改 `learning_agent/computer_use/approval.py`，让审批模型可以注入 Phase48 安全策略，同时保持 Phase38 默认合同兼容。
- 已修改 `/computer status`，让真实终端能显示 `phase48_windows_security_policy`、grant class 和高风险默认拒绝状态。
- 已新增 Phase48 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase48 focused 4 tests OK，Phase38/48 regression 10 tests OK，py_compile OK，CLI selftest 输出 `PHASE48_WINDOWS_SECURITY_POLICY_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase48_windows_security_policy_20260603/`。
- 下一阶段进入 Phase 49：MCP / ClaudeCode 风格工具面兼容层。

## 2026-06-03 Phase 49 完成记录

- Phase 49 已完成：新增 `learning_agent/computer_use/tool_surface.py`，建立 `computer_use` 和 `computer-use` 兼容工具面。
- 已修改 `learning_agent/tools/schemas.py`、`learning_agent/tools/catalog.py`、`learning_agent/tools/executor.py` 和 `learning_agent/core/agent.py`，让兼容工具可见、高风险、按 `computer_use` 包加载，并转发到旧三工具。
- 兼容工具只做参数归一化，不扩展真实动作能力；`actions_expanded=false` 继续作为阶段边界。
- 已新增 Phase49 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase49 focused 4 tests OK，Phase27/48/49 regression 12 tests OK，py_compile OK，CLI selftest 输出 `PHASE49_COMPUTER_USE_TOOL_SURFACE_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase49_windows_tool_surface_20260603/`。
- 下一阶段进入 Phase 50：全局 Abort / Cleanup / Lock 恢复。

## 2026-06-03 Phase 50 完成记录

- Phase 50 已完成：升级 `learning_agent/computer_use/session_runtime.py`，加入 `PHASE50_WINDOWS_RECOVERY_READY`、stale lock 显式恢复、cleanup 同步清 abort 和 action journal 回放。
- 已修改 `learning_agent/app/interactive.py`，增加 `/computer recover`、`/computer journal`，并让 `/computer cleanup` 同时显示 Phase50 恢复摘要。
- 已新增 Phase50 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase50 focused 5 tests OK，Phase31/40/50 regression 14 tests OK，py_compile OK，CLI selftest 输出 `PHASE50_WINDOWS_RECOVERY_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase50_windows_recovery_runtime_20260603/`。
- 下一阶段进入 Phase 51：类似 `/chrome` 的终端状态 UI。

## 2026-06-03 Phase 51 完成记录

- Phase 51 已完成：新增 `learning_agent/app/computer_status_renderer.py`，让 `/computer status` 输出类似 `/chrome` 的紧凑状态 UI。
- 已新增 `learning_agent/computer_use/terminal_grants.py`，支持 `/computer grant` 和 `/computer revoke` 的终端 UI 授权草案状态，并明确 `terminal_ui_only` 边界。
- 已修改 `learning_agent/app/interactive.py`，接入 `/computer observe`、`/computer grant`、`/computer revoke` 和新 status renderer。
- 已新增 Phase51 聚焦测试和真实可见终端场景 JSON。
- 验证通过：Phase51 focused 4 tests OK，Phase21/38/48/50/51 regression 21 tests OK，py_compile OK，CLI selftest 输出 `PHASE51_COMPUTER_STATUS_UI_OK`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase51_computer_status_ui_20260603/`。
- 下一阶段进入 Phase 52：自动化与真实可见终端端到端验收。
