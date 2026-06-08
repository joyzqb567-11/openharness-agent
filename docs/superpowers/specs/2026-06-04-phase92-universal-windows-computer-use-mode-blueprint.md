# Phase92 Universal Windows Computer Use Mode Blueprint

## 背景纠偏

用户明确指出：Computer Use 的目标不是给本机每个软件单独写一个受控功能，也不是 Notepad 一个控制器、Paint 一个控制器、Explorer 一个控制器。

正确目标是：用户在 agent 里输入 prompt 打开 Computer Use 后，agent 使用同一套通用 Windows 操作能力，像人一样观察屏幕、理解任务、控制鼠标键盘、操作窗口、验证结果、失败恢复，从而控制用户本机普通应用程序。

代表性应用场景仍然需要，但它们只用于证明通用性，不是产品架构本体。

## 最终产品标准

用户输入类似：

```text
打开 computer use，帮我打开画图并画一只皮卡丘
```

或者：

```text
打开 computer use，帮我打开本机某个普通软件，完成我描述的操作
```

learning_agent 应该进入一个通用 Windows Computer Use session，并执行：

1. 观察当前桌面、窗口列表、截图、UIA 控件树和可见文本。
2. 解析 prompt，形成可验证步骤。
3. 识别目标普通应用和目标窗口。
4. 通过通用动作层执行点击、输入、热键、滚动、拖拽、菜单、窗口切换。
5. 每步动作后重新观察结果。
6. 如果结果不符合预期，重新定位、恢复或调整计划。
7. 如果遇到高风险窗口或动作，停止并请求确认或拒绝。

## 明确反模式

以下做法不允许作为最终架构：

- 为每个软件创建一个专用 Controller。
- 依赖每个应用都有独立 E2E 才能控制。
- 把 Notepad/Paint 代表性场景当成主架构。
- 让真实鼠标键盘动作绕过统一授权、急停、目标复验和证据链。
- 为了通过验收直接生成图片文件、直接写应用结果文件，冒充真实操作。

## 正确架构

Phase92 要建立一个单一的 `UniversalWindowsComputerUseRuntime`。

这个 runtime 不是新造所有能力，而是组合已有模块：

- Phase66 `WindowsObservationFusionRuntime`：统一观察事实。
- Phase67 `WindowsPromptTaskPlanner`：从 prompt 生成步骤和风险。
- Phase68 `WindowsClosedLoopComputerExecutor`：闭环执行思想。
- Phase69 `WindowsAppWindowControlRuntime`：应用启动、窗口聚焦、身份确认。
- Phase70 `WindowsGenericControlActionRuntime`：通用控件点击和文本输入。
- Phase71 `WindowsGenericInputActionRuntime`：热键、菜单、滚动、拖拽。
- Phase72 `WindowsRealAppSafetyBoundary`：持久授权、高风险拒绝、急停前置。
- Phase76-89 `WindowsProductionComputerUseHostAdapter`：生产 host adapter、权限、剪贴板、observe-act-verify。
- Phase90/91：只作为代表性验收样本，不作为主架构入口。

## Phase92 核心接口

建议新增：

```text
learning_agent/computer_use/universal_mode.py
```

核心类：

```text
UniversalWindowsComputerUseRuntime
```

核心方法：

```text
status()
run_prompt(prompt, real_actions=False)
build_session_plan(prompt)
observe()
act(step)
verify(step)
recover(step)
run_contract()
```

默认 `real_actions=False`，只运行安全 contract，不碰用户桌面。

真实动作必须同时满足：

- 用户明确打开 Computer Use。
- session 持有桌面 lock。
- 目标窗口属于普通应用。
- 目标窗口身份通过当前观察复验。
- 动作通过 Phase72 安全边界。
- 没有 abort。
- 高风险动作已经明确确认。
- 动作后有 before/after evidence。

## 成功 Token

Phase92 最终 token 应包括：

```text
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY
PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK
single_universal_runtime=true
prompt_to_any_normal_app=true
per_app_controller_required=false
representative_apps_are_acceptance_only=true
generic_observe_plan_act_verify_loop=true
uses_observation_fusion=true
uses_prompt_task_planner=true
uses_generic_action_layer=true
uses_real_app_safety_boundary=true
uses_production_host_adapter=true
high_risk_requires_confirmation=true
unauthorized_window_zero_events=true
target_drift_blocks_action=true
raw_text_hidden=true
default_real_actions_enabled=false
uncontrolled_actions_expanded=false
```

## 验收策略

Phase92 默认验收不证明真实软件已经被物理操作；它证明架构路线已经从 app-specific smoke 改成通用 runtime。

后续 Phase93+ 才应该逐步做真实可见桌面 smoke：

- Phase93：真实 Notepad，通过通用 runtime 完成，不允许调用 Notepad 专用 controller。
- Phase94：真实 Paint 皮卡丘，通过通用 runtime 完成，不允许调用 Paint 专用 controller。
- Phase95：真实 Explorer 文件操作，通过通用 runtime 完成。
- Phase96：真实普通第三方应用或浏览器，通过通用 runtime 完成。

这些场景的目的都是证明通用 runtime，而不是建立应用专用控制器。

## 停止条件

必须停止并汇报的情况：

- 需要安装 OCR、视觉模型、驱动、系统服务或全局 hook。
- 需要修改注册表、系统设置、UAC、安全策略或默认应用。
- 需要自动输入密码、验证码、支付信息、登录 token、API key、隐私内容。
- 目标窗口是终端、Codex 自身、Windows 安全、管理员、安全设置、UAC 或认证弹窗。
- 无法完成 `start_oauth_agent.bat` 真实可见终端验收。

## 设计结论

Phase92 的核心不是再新增一个 app smoke，而是把 Computer Use 的产品路线锁定为：

```text
一个通用 Windows Computer Use Runtime
+ 多个代表性验收样本
+ 统一安全边界
+ 可见终端真实验收
```

这才符合用户想要的“打开 Computer Use 后能控制本机普通应用程序”的目标。
