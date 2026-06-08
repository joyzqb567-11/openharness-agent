# Phase 43-52 Windows Computer Use Production Alignment Plan

## Goal

把 `learning_agent` 的 Windows OS 级 Computer Use 从 Phase 42 的安全合同矩阵，升级到更接近 ClaudeCode computer-use 成熟度的 Windows 生产路线。ClaudeCode 的 macOS 原生实现只作为架构参考，本计划不复制 macOS API，而是在 Windows 上补齐诊断、native host、截图、UIA、真实 SendInput、审批、兼容工具面、abort/cleanup、终端 UI 和真实端到端验收。

## Current Baseline

- Phase 27-42 已完成协议、只读窗口枚举、evidence、动作门禁、锁、native helper 合同、diagnostics、UIA text provider、WGC 合同、SendInput 合同、审批、坐标、abort/cleanup、image_result 和 final matrix。
- Phase 42 明确 `actions_expanded=false`，说明当前只是安全矩阵，不代表真实 Windows WGC/UIA/SendInput 已生产可用。
- 当前差距主要在真实 Windows native provider、helper 进程协议、真实截图、真实 UIA 树、真实 SendInput dispatcher、ClaudeCode 风格工具面和真实可见终端完整验收。

## Stop Conditions

- 未完成真实可见终端交互验收时，不允许声明“开发完成”或“验收通过”。
- 不自动安装系统依赖、不写注册表、不修改 Windows 安全策略，除非用户另行明确确认。
- 禁止控制终端、Codex UI、密码框、认证弹窗、验证码/OTP、Windows Run、管理员安全窗口、密码管理器和隐私安全设置。
- 如果同一个阻塞条件连续三次出现，并且不能通过本地证据继续推进，停止并向用户报告。
- 任何真实动作前必须经过 opt-in、允许列表、锁、abort、目标窗口校验和 evidence 记录。

## Phase Checklist

- [x] Phase 43: Windows 原生能力诊断升级。
- [x] Phase 44: Windows Native Host / Helper 架构。
- [x] Phase 45: 真实 Windows 截图能力。
- [x] Phase 46: 真实 UIA 窗口树观察。
- [x] Phase 47: 真实 SendInput 动作执行。
- [x] Phase 48: 权限审批和安全策略升级。
- [x] Phase 49: MCP / ClaudeCode 风格工具面兼容层。
- [x] Phase 50: 全局 Abort / Cleanup / Lock 恢复。
- [x] Phase 51: 类似 `/chrome` 的终端状态 UI。
- [x] Phase 52: 自动化与真实可见终端端到端验收。

## Phase 43 Success Criteria

- 新增或升级 Windows native diagnostics 聚合层。
- `/computer status` 能显示 native provider 能力矩阵。
- 诊断结果必须区分 `available`、`enabled`、`reason`、`next_step`。
- 自动化测试覆盖依赖存在/缺失两类路径。
- 记录 agent_memory、学习备份和验收场景。

## Phase 44 Success Criteria

- 新增 native host/helper 协议层，支持 `status`、`observe`、`capture`、`action`、`cleanup` 基础消息。
- helper 可启动、健康检查、返回版本和能力。
- helper 异常时主 agent 不崩溃。
- 默认只读，不开放真实动作。

## Phase 45 Success Criteria

- 接入真实截图 provider 优先级：WGC 优先，GDI fallback。
- 保存截图 artifact，返回 image_result。
- 返回显示器、DPI、窗口坐标和 provider 来源。
- 失败时给出明确 reason，不把失败伪装成成功。

## Phase 46 Success Criteria

- 接入真实 UIA 控件树 provider。
- 返回控件名称、角色、边界框、可点击/可输入摘要。
- 节点数、深度、文本长度都有上限。
- 敏感文本和危险目标必须过滤。

## Phase 47 Success Criteria

- 实现真实 SendInput dispatcher。
- 支持 move、click、double_click、scroll、press_key、type_text。
- 动作前校验目标窗口未变化。
- 默认仍受 opt-in、allowlist、lock、abort、approval 限制。

## Phase 48 Success Criteria

- 升级审批模型，区分 observe/action/system_key/clipboard 等 grant。
- 未批准应用拒绝控制。
- 高风险动作默认拒绝。
- 终端输出拒绝原因，用户能读懂。

## Phase 49 Success Criteria

- 增加 ClaudeCode 风格 `computer-use` 兼容工具面。
- 保留现有 `computer_status`、`computer_observe`、`computer_action`。
- 兼容工具走同一个 controller、安全策略和 evidence store。

## Phase 50 Success Criteria

- 强化 abort/cleanup/lock recovery。
- 崩溃或 stale lock 后可恢复。
- action journal 可回放最近动作链路。
- `/computer cleanup` 能释放状态。

## Phase 51 Success Criteria

- `/computer status` 输出紧凑状态面板。
- 增加或完善 `/computer grant`、`/computer revoke`、`/computer observe`、`/computer cleanup`、`/computer abort`。
- UI 不刷屏，清楚显示当前能力、授权、锁、最近截图、最近动作。

## 2026-06-03 Phase 52 自动化完成记录

- 新增 `learning_agent/computer_use/production_matrix.py`，作为 Phase43-51 的生产级总矩阵入口。
- 新增 `learning_agent/tests/test_windows_computer_use_production_matrix_phase52.py`，红测先确认 `learning_agent.computer_use.production_matrix` 缺失。
- 新增 `learning_agent/acceptance_controller/scenarios/agent_capability_phase52_windows_production_matrix.json`，固定真实终端可匹配 token。
- 修复 `learning_agent/app/computer_status_renderer.py` 的 Phase43 兼容输出：`/computer status` 继续显示 `Computer Native Capability Matrix`、Phase43 marker 和 `windows_sendinput` 关键能力。
- 自动化验证已通过：Phase52 focused 2 tests OK；Phase43-52 回归 39 tests OK；`py_compile` OK；Phase52 CLI self-check 输出 `PHASE52_WINDOWS_PRODUCTION_MATRIX_OK phase_count=9 ... dispatcher_actions_expanded=true actions_expanded=false`。
- 学习备份已复制到 `learning_agent/test/agent_capability_phase52_windows_production_matrix_20260603/`。
- 真实可见终端验收已通过：`learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/result.json` 记录 `completed=true`、`prompt_sent=true`、`prompt_received=true`、`final_printed=true`，最终截图 `03_final.png` 可见 Phase52 READY/OK 输出。

## Phase 52 Success Criteria

- 自动化测试通过。
- `py_compile` 通过。
- acceptance scenario 和 verifier 通过。
- 必须启动 `learning_agent/start_oauth_agent.bat` 的真实可见终端，并在 agent prompt 中输入真实用户风格测试 prompt。
- 若 Codex 当前环境无法观察或输入真实可见终端，必须明确说明真实可见终端交互验收未完成，不能声明开发完成。
