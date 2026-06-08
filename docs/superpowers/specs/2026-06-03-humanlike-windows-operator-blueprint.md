# Humanlike Windows Operator Phase65-75 Blueprint

> 本蓝图是 Phase65 到 Phase75 的执行锚点。后续实现必须围绕这里的成功标准推进，不能退化成只控制测试窗口，也不能退化成给每个软件写固定脚本。

## Final Success Standard

最终目标是拟人级 Windows Computer Use：用户能在电脑上手动操作的普通应用程序，`learning_agent` 的 agent 也能通过 prompt 自主观察、理解、点击、输入、拖拽、滚动、切换窗口、等待结果、校验结果、失败恢复，并完成任务。

这个标准不等于绕过安全边界。密码、验证码、支付、登录认证、管理员权限、UAC、终端危险命令、系统安全设置、个人隐私数据读取等高风险动作必须暂停并请求用户确认。

## Core Principle

Phase65-75 不做“每个应用一个脚本”的路线。正确路线是建立通用拟人操作闭环：

1. 观察屏幕、窗口、控件树、OCR/视觉结果。
2. 根据用户 prompt 生成当前任务计划。
3. 选择最小安全动作。
4. 通过真实鼠标键盘或窗口焦点动作执行。
5. 再次观察并校验结果。
6. 如果失败，尝试恢复、重定位、重新计划。
7. 如果遇到高风险或权限不清，停止并请求确认。

代表性 E2E 场景用于证明通用性，而不是替代通用能力。不能要求每个应用都写专用验收脚本才能控制。

## Architecture

Phase65-75 的目标架构由七层组成：

- Universal Operator Contract：定义拟人操作、可控普通应用、高风险动作、作弊路径和验收 token。
- Observation Fusion：融合截图、UIA 控件树、窗口状态、OCR/视觉摘要。
- Task Planner：把自然语言 prompt 拆成可验证步骤。
- Closed-Loop Executor：执行 observe -> decide -> act -> observe -> verify -> recover 循环。
- Generic Action Layer：提供通用点击、输入、热键、滚动、拖拽、菜单、窗口切换、文件保存动作。
- Safety Boundary：把 Phase58 的自有安全窗口限制升级为“用户授权的真实普通应用窗口”，同时保留高风险默认拒绝。
- App Memory：记录应用启动方式、常见控件线索、失败恢复经验，但不把 app memory 当成硬编码脚本。

## Phase Plan

### Phase65: Universal Operator Contract

目标：把“拟人操作所有普通本机应用”的定义写成机器可验证合同。

验收点：
- `humanlike_operator_contract=true`
- `prompt_to_normal_windows_app=true`
- `per_app_scripts_required=false`
- `high_risk_confirmation_required=true`
- `direct_file_cheat_blocked=true`

### Phase66: Observation Fusion

目标：把截图、UIA、窗口枚举、OCR/视觉摘要汇合成一个稳定 observation object。

验收点：
- `screenshot_observation=true`
- `uia_tree_observation=true`
- `ocr_or_vision_slot=true`
- `window_state_observation=true`
- `sensitive_text_boundary=true`

说明：如果 OCR/视觉依赖需要安装，必须先停止并请求用户确认，不能自动安装或改系统设置。

### Phase67: Prompt Task Planner

目标：把用户 prompt 拆成步骤、预期结果、风险等级和可恢复检查点。

验收点：
- `prompt_task_plan=true`
- `expected_result_per_step=true`
- `risk_level_per_step=true`
- `checkpoint_per_step=true`

### Phase68: Closed-Loop Executor

目标：建立 observe -> decide -> act -> observe -> verify -> recover 的拟人闭环。

验收点：
- `closed_loop_execution=true`
- `post_action_verification=true`
- `failure_recovery=true`
- `blind_coordinate_chain_blocked=true`

### Phase69: App Launch, Focus, And Window Switching

目标：能启动普通 Windows 应用、识别目标窗口、切换焦点、确认当前操作对象。

验收点：
- `app_launch=true`
- `window_focus=true`
- `target_window_identity=true`
- `target_drift_blocked=true`

### Phase70: Generic Click, Type, And Control Actions

目标：支持通用控件点击、文本输入、按钮点击、文本框定位、视觉坐标兜底。

验收点：
- `generic_click=true`
- `generic_type=true`
- `control_locator=true`
- `visual_fallback=true`
- `before_after_evidence=true`

### Phase71: Generic Hotkey, Menu, Scroll, And Drag

目标：补齐用户真实操作常用动作：热键、菜单、滚动、拖拽、画图类连续鼠标动作。

验收点：
- `hotkey_action=true`
- `menu_navigation=true`
- `scroll_action=true`
- `drag_action=true`
- `continuous_mouse_path=true`

### Phase72: Safety Boundary For Real Apps

目标：把真实动作范围从自有安全窗口升级为“用户授权的真实普通应用窗口”。

验收点：
- `authorized_real_app_actions=true`
- `unauthorized_window_zero_events=true`
- `high_risk_default_refusal=true`
- `abort_before_low_level_send=true`
- `approval_bypass_blocked=true`

### Phase73: App Memory And Self-Learning

目标：记录不同应用的非敏感操作线索，帮助下一次更快定位，但不形成脆弱脚本。

验收点：
- `app_memory=true`
- `non_secret_memory=true`
- `memory_assists_not_scripts=true`
- `memory_can_be_revoked=true`

### Phase74: Representative Real App E2E Matrix

目标：用代表性真实应用证明通用能力，而不是为每个应用写专用控制器。

必须覆盖的代表性场景：
- Notepad：打开真实记事本，输入文本，保存到受控测试目录。
- Explorer：打开真实资源管理器，创建、定位、重命名或验证受控测试文件。
- Browser：打开真实浏览器，完成可见点击、输入、等待和结果读取。
- Window/Settings Style App：处理真实窗口切换、按钮、菜单或设置类控件，优先选择不会改系统状态的安全场景。
- Paint Pikachu：打开真实画图软件，绘制简化版皮卡丘/黄色卡通电气鼠并保存。

Paint Pikachu 场景要求：
- 必须启动真实 `mspaint.exe`。
- 必须通过真实鼠标/键盘动作操作画图软件。
- 必须识别画布区域，选择颜色，绘制或填充图形。
- 图中必须包含黄色主体、黑色耳尖、红色脸颊、眼睛、嘴巴、闪电尾巴等可识别元素。
- 保存路径必须在受控测试目录，例如 `learning_agent/memory/computer_use/e2e_paint/`。
- 必须保存截图或图片证据，确认不是空白画布。
- 不允许直接生成 PNG/JPG 文件冒充画图操作结果。
- 不要求临摹官方原图；验收目标是证明拟人控制真实画图软件完成开放式视觉任务。

Paint Pikachu 场景 token：
- `mspaint_pikachu_scenario=true`
- `real_paint_app_control=true`
- `humanlike_drawing_actions=true`
- `direct_image_file_cheat=false`
- `paint_canvas_not_blank=true`
- `pikachu_visual_elements=true`

### Phase75: Humanlike Windows Operator Final Matrix

目标：汇总 Phase65-74，并形成最终生产级拟人 Windows Computer Use 矩阵。

最终 token：

```text
PHASE75_HUMANLIKE_WINDOWS_OPERATOR_READY
prompt_to_any_normal_app=true
humanlike_observe_act_verify_loop=true
generic_windows_app_control=true
per_app_scripts_required=false
uia_ocr_vision_fusion=true
mouse_keyboard_window_control=true
failure_recovery=true
representative_real_apps_passed=true
mspaint_pikachu_scenario=true
real_paint_app_control=true
humanlike_drawing_actions=true
direct_image_file_cheat=false
abort_safety=true
high_risk_confirmation=true
```

## Stop Conditions

执行 Phase65-75 时遇到以下情况必须停止并汇报：

- 需要安装 OCR、视觉模型、驱动、全局 hook 或系统服务。
- 需要修改 Windows 设置、注册表、UAC、安全策略或默认应用。
- 任务会读取、输入或泄露密码、验证码、支付信息、登录 token、私人聊天、隐私文件。
- 目标窗口是终端、认证、管理员、安全、防病毒、支付或系统敏感窗口。
- 无法完成 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收。
- E2E 场景需要操作真实用户数据，而不是受控测试目录。

## Verification Standard

每个功能阶段都必须遵守：

- 先写失败测试，再写实现。
- 自动化测试通过。
- `py_compile` 或等价编译检查通过。
- 新写和修改的代码必须按项目规则加中文注释并备份到 `learning_agent/test/`。
- 涉及 agent 新功能后，必须通过 `learning_agent/start_oauth_agent.bat` 的真实可见终端交互验收。
- CLI、HTTP bridge、stdin、selftest、日志、MCP 调用都不能替代真实可见终端验收。

## Scope Boundary

本蓝图追求普通 Windows 应用的通用拟人操作能力。它不承诺自动绕过登录、验证码、付费墙、管理员权限、系统安全弹窗或用户没有授权的私密数据。

“能控制所有本机应用”的可落地解释是：对于用户本人可以正常手动操作、且不涉及高风险边界的普通应用，agent 应能通过观察和真实动作闭环完成任务。
