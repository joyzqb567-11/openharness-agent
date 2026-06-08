# Phase 53-64 Windows Computer Use Parity Plus Blueprint

> 本文件是书面升级蓝图，不是运行时代码实现。用户确认后，才能按 Phase 53 到 Phase 64 逐项执行。

## 总目标

把 learning_agent 的 Windows Computer Use 从当前约 80% ClaudeCode 成熟度，推进到 100% 对齐 ClaudeCode 的架构成熟度，并在 Windows 专用能力、外部 agent 接管调试、真实端到端验收矩阵上超过 ClaudeCode。

## 当前基线

- ClaudeCode 本地 `utils/computerUse/executor.ts` 是 macOS-only，`process.platform !== 'darwin'` 时会拒绝执行。
- ClaudeCode 成熟点主要是架构和产品化链路：MCP session binding、AppState、React approval、file lock、Escape abort、turn cleanup、OS notification、tool rendering、image/text result mapping。
- learning_agent 已完成 Phase 43-52：native capability matrix、native host、screenshot runtime、UIA tree、SendInput dispatcher、security policy、tool surface、recovery runtime、status UI、真实可见终端验收矩阵。
- learning_agent Phase52 通过真实终端验收，但仍明确 `actions_expanded=false`，说明默认生产动作面仍保持安全收敛。

## 剩余 20% 差距拆解

- 真实 Windows 原生依赖和 native helper 还需要从合同层推进到可重复验收的生产层。
- WGC/UIA/SendInput 需要摆脱主要依赖 fake/injected provider 的验收方式。
- ClaudeCode 风格 session context、AppState、approval UI、display state、screenshot state 还需要统一事实源。
- 全局 abort/cleanup 需要深入 streaming/tool lifecycle，而不仅是独立命令。
- 截图像素校验、裁剪校验、坐标落点校验还需要形成强验收。
- 外部 agent 接管 controller 需要成为正式能力，方便 Codex 输入真实 prompt、观察输出、复现问题。

## 总体架构路线

1. 先锁定不可造假的验收合同，再接真实 native 能力。
2. Windows native helper 采用 out-of-process 边界，主 agent 只通过稳定协议调用。
3. 所有真实动作都必须经过 observe -> approve -> lock -> target verify -> action -> after observe -> audit chain。
4. 所有能力都必须在 `/computer status`、机器可读 status、acceptance verifier 中有同一事实源。
5. 所有阶段必须保留禁止目标边界：终端、Codex UI、安全设置、密码管理器、认证弹窗、验证码、Windows Run、管理员安全窗口。

## Phase 53: Parity Gap Lock And Non-Fake Acceptance Contract

目标：把“剩余 20%”固化为机器可读矩阵，防止后续把 fake provider 验收误报成真实能力。

交付：
- 新增 `phase53_parity_gap_matrix`，列出 ClaudeCode 成熟点、learning_agent 当前状态、补齐阶段、真实验收方式。
- 新增 `real_provider_required` 字段，区分 contract test、fake provider test、real Windows provider test。
- 新增 `/computer parity` 或等价 CLI 自检输出。

验收：
- 自动化测试证明每个差距项都有 owner phase。
- 真实可见终端输入自然 prompt 后，输出 Phase53 matrix marker。
- 不允许声明任何新真实动作能力。

## Phase 54: Windows Native Dependency And Permission Reality Gate

目标：建立 Windows 原生依赖的诚实门禁，明确当前机器能否运行真实 UIA、WGC、SendInput、低层 hotkey、toast notification。

交付：
- 检测 `uiautomation`、`comtypes`、`winrt/winsdk`、PowerShell/.NET、Windows build、screen capture capability、input permission。
- 生成 `native_dependency_report.json`，记录依赖是否安装、是否启用、缺失时下一步。
- 所有安装依赖或改系统设置必须单独请求用户确认，不能在本阶段自动安装。

验收：
- 缺依赖时必须诚实输出 blocked/missing，不得 fallback 成“真实已通过”。
- 真实终端能看到每个 native capability 的可用性和下一步。

## Phase 55: Out-Of-Process Windows Native Helper V2

目标：把 Windows 原生能力从 in-process 合同升级为独立 native helper 进程，提供稳定 JSON-RPC 或 stdio 协议。

交付：
- `windows_native_helper_v2` 协议：status、list_windows、capture_window、read_uia_tree、send_input、hotkey、cleanup。
- helper 进程崩溃时主 agent 不崩溃，返回结构化错误。
- helper 响应不能包含原始敏感文本，截图 bytes 只写 artifact，不塞进 JSON。
- helper 有版本、capability、pid、started_at、health 状态。

验收：
- 单元测试覆盖 helper 启动、请求、超时、崩溃恢复、cleanup。
- 真实终端验收能看到 helper health。
- 不接真实动作前，send_input 仍默认拒绝。

## Phase 56: Real Windows Screenshot Pipeline With Pixel Guard

目标：把截图从 provider 合同推进到真实 Windows 截图验收，优先 WGC，失败时 GDI fallback，并增加像素级黑屏/空白/尺寸校验。

交付：
- 真实安全窗口截图 smoke，例如 Notepad 或专用测试窗口。
- WGC provider 真可用时走 WGC；不可用时明确 fallback 到 GDI。
- 对截图做 pixel guard：非空、非全黑、尺寸正确、窗口标题区域可见、artifact 可打开。
- 截图结果进入 image_result、active_artifacts、audit chain。

验收：
- 自动化测试覆盖 fake provider 和 pixel guard。
- 真实可见终端验收必须生成真实截图 artifact。
- verifier 检查 artifact 存在、尺寸、像素非空。

## Phase 57: Real UIA Control Tree And Semantic Locator

目标：把 UIA tree 从结构合同推进到真实安全窗口控件树，并提供语义定位器。

交付：
- 真实 UIA safe-window smoke，优先 Notepad/Calculator/专用测试窗口。
- 控件树包含 name、role、automation_id、class_name、bounds、enabled、clickable、editable。
- 新增 semantic locator：按标题、role、text、automation id、bounds 查找控件。
- locator 输出必须可解释：为什么选这个控件、候选数量、置信度。

验收：
- 缺 UIA 依赖时诚实 blocked。
- 有 UIA 依赖时真实读取安全窗口控件树。
- 禁止读取密码框、认证弹窗、终端、Codex UI。

## Phase 58: Real SendInput Action Path With Target Guard

目标：把 SendInput dispatcher 推进到受控真实动作，先只允许安全测试窗口、极窄动作集、强校验。

交付：
- ctypes SendInput 或 helper send_input 低层 sender。
- 动作前必须验证目标窗口仍是同一个 hwnd/process/title hash。
- 支持最小真实动作：move_mouse、click、type_text 到安全测试窗口。
- type_text 原文不得进入日志，只记录长度、短 hash、redacted=true。
- 动作后必须重新 observe 并保存 before/after evidence。

验收：
- 真实动作只能打到安全测试窗口。
- verifier 检查目标窗口文本或 UIA 状态确实变化。
- 任一门禁失败时发送 0 个低层事件。

## Phase 59: ClaudeCode-Style Session Context And AppState

目标：实现类似 ClaudeCode `bindSessionContext` 的统一 session context，让权限、显示器、截图尺寸、允许 app、hidden/cleanup 状态有同一事实源。

交付：
- `ComputerUseSessionContext`：allowed_apps、grant_flags、selected_display、last_screenshot_dims、hidden_windows、last_action、last_error。
- 持久化到 `learning_agent/memory/computer_use/session_state/`。
- 每个工具调用都绑定 current context，避免散落状态。
- 状态可被 `/computer status`、HTTP bridge、controller、verifier 同时读取。

验收：
- 多轮真实终端中 session state 可保持。
- cleanup 后 state 正确归零或标记完成。
- 并发 session 不能互相污染 lock 和 grants。

## Phase 60: Approval UX And Persistent Grants

目标：把当前 terminal grant draft 推进到更接近 ClaudeCode 的审批体验，并增加过期、撤销、作用域和审计。

交付：
- `/computer approve`、`/computer deny`、`/computer grants`、`/computer revoke` 形成完整闭环。
- grant 支持 app/window/display/action_scope/ttl/reason。
- 高风险 grant 如 clipboard/systemKeyCombos 默认拒绝，必须显式开启。
- 可选本地 UI 或终端 panel，先以终端为主，不强依赖前端。

验收：
- 未授权 app 动作必拒绝。
- 授权过期后动作必拒绝。
- revoke 后动作必拒绝。
- 真实终端中用户能看懂当前授权状态。

## Phase 61: Global Abort, Hotkey, Cleanup, And Streaming Hooks

目标：把 abort/cleanup 从命令层深入到工具流执行和异常中断路径，接近 ClaudeCode turn-end cleanup。

交付：
- Windows 全局热键或低层键盘 hook 方案评估，优先安全可撤销。
- streaming tool executor、tool abort、模型中断、用户 Ctrl+C、异常退出都触发 cleanup。
- cleanup 包含 release lock、clear active helper session、flush audit、write notification。
- 如果无法注册全局热键，必须降级为终端命令和 controller abort，不假装成功。

验收：
- 工具执行中 abort 后，下一次真实动作发送 0 个低层事件。
- 异常退出后 stale lock 可恢复。
- 真实终端验收覆盖 abort during action。

## Phase 62: High-Level Computer Tool API And Streaming Integration

目标：超越单步 click/type，把 Computer Use 变成高层浏览器/桌面任务工具，同时接入全局 StreamingToolExecutor。

交付：
- 新增高层操作：observe_screen、find_control、click_control、type_into_control、wait_for_change、verify_screen。
- 高层操作内部仍走底层安全链。
- 只读 observe 可并发，写动作严格串行。
- 工具结果支持 streaming progress、image artifact、UIA candidate summary。

验收：
- 批量只读观察不会阻塞写锁。
- 写动作不会并发污染桌面。
- 真实终端能看到进度事件和最终 artifact。

## Phase 63: External Agent Controller Takeover And Debug Surface

目标：把“可被 Codex 等其他 agent 控制和调试”做成正式生产能力，超过 ClaudeCode 的本地单体体验。

交付：
- controller 支持启动 agent、等待 ready、输入真实 prompt、读取输出、截图、导出 result.json。
- 支持 HTTP/stdio 两种可选控制面，默认本地、带 token、只允许 loopback。
- 支持外部 agent 查询 `/computer status`、发送 `/computer abort`、读取 acceptance run。
- controller 不能绕过 approval、lock、security policy。

验收：
- Codex 能通过 controller 输入自然 prompt，让 learning_agent 调用 Computer Use 安全能力。
- controller 复现失败时能导出完整证据包。
- 真实可见终端仍是最终验收门禁，HTTP/stdio 不能替代它。

## Phase 64: Final Parity Plus Production Matrix

目标：建立最终总验收，证明 learning_agent 对齐 ClaudeCode，并在 Windows 原生能力、外部接管验收、可审计矩阵上超过 ClaudeCode。

交付：
- `phase64_windows_computer_use_parity_plus_matrix`。
- 覆盖 Phase53-63 所有成果。
- 输出三类结论：claudecode_parity=true、windows_native_real=true、controller_takeover=true。
- 自动生成对比报告：ClaudeCode 有什么、learning_agent 已对齐什么、learning_agent 超越点是什么。

验收：
- 自动化测试通过。
- py_compile 通过。
- JSON scenario 校验通过。
- 真实可见 `learning_agent/start_oauth_agent.bat` 终端验收通过。
- 独立 verifier 复验通过。
- 如果真实可见终端验收未完成，最终回答必须写明：真实可见终端交互验收未完成，不能声明开发完成。

## 成功标准

- learning_agent 能在 Windows 上完成真实安全窗口 observe、capture、UIA locate、受控 SendInput、after-action verification。
- 所有真实动作都能被用户、controller、audit store、acceptance verifier 复盘。
- `/computer status` 能解释当前能力、授权、锁、helper、截图、UIA、SendInput、last action、next command。
- 外部 agent 可以接管和调试 learning_agent，但不能绕过安全门禁。
- 最终矩阵可以诚实输出 100% parity，并列出超过 ClaudeCode 的 Windows-first 能力。

## 停止条件

- 未经用户明确确认，不安装系统依赖、不写注册表、不改 Windows 安全设置。
- 真实目标是终端、Codex UI、安全设置、密码管理器、认证弹窗、验证码、Windows Run、管理员窗口时立即停止。
- 任何阶段如果只能通过 fake provider，则只能声明 contract passed，不能声明 real native passed。
- 任何运行时代码阶段未通过自动化测试和真实可见终端验收，不能声明开发完成。

## 推荐执行方式

用户确认后，从 Phase 53 开始逐项执行到 Phase 64。每个阶段都按 TDD 红灯、实现、聚焦测试、邻近回归、py_compile、场景 JSON、真实可见终端验收、独立 verifier、学习备份、agent_memory 记录的顺序推进。
