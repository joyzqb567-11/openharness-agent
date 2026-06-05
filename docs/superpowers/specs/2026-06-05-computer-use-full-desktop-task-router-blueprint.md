# Computer Use Full Desktop Task Router Root-Cause Blueprint

## 1. 背景

2026-06-05 的真实可见终端试运行暴露了一个关键问题：用户先输入 `/computer use --full`，再输入 `请使用本地电脑的画图软件画一个皮卡丘。` 后，agent 确实收到了中文提示词，也确实生成了皮卡丘图片并打开了 Windows 画图软件，但它没有通过 Computer Use 的真实 GUI 鼠标/键盘动作在画图窗口里绘制。

实际路径是：模型调用 `bash`，通过 PowerShell `System.Drawing` 生成 `pikachu_for_paint.png`，再用 `Start-Process mspaint.exe` 打开图片。这说明 `/computer use --full` 目前更像“权限状态开关”，还没有成为“普通自然语言桌面任务的默认执行体系”。

本蓝图的目标是治本：让 `/computer use --full` 打开后，涉及本机应用的普通自然语言任务必须进入通用 Computer Use GUI 闭环，不能用脚本生成最终成果冒充真实桌面操作。

## 2. 根因

根因不是 Paint 不支持，也不是皮卡丘任务特殊，而是任务路由层缺失。

当前系统存在以下结构性缺口：

- Full mode 已能申请、确认、显示状态和停止，但它没有接管后续普通用户提示词。
- 交互式 agent 仍然把 `read/write/edit/bash` 暴露给模型，桌面任务没有专属执行上下文。
- 模型会自然选择最省事路径，例如脚本生成图片、直接启动程序、直接写文件。
- 验收只看“最终回答和结果文件”，没有强制检查“真实 GUI 动作链路”。
- 现有 Computer Use 模块有通用观察、动作、安全、身份、清理等基础能力，但还没有被普通自然语言任务入口统一调用。

治本方案必须修“普通提示词进入 Computer Use GUI 闭环”这一层，而不是继续给某个应用补丁。

## 3. 产品目标

用户完成如下流程：

```text
/computer use --full
/computer use --full-confirm <token>
请使用本地电脑的画图软件画一个皮卡丘。
```

agent 必须执行以下产品行为：

1. 识别这是本机桌面应用任务。
2. 自动进入 Computer Use Desktop Task Router。
3. 发现并启动普通本机应用，例如 Paint。
4. 绑定 agent 自己启动的目标窗口，而不是接管用户已有窗口。
5. 对目标窗口执行 observe -> plan -> act -> verify 闭环。
6. 使用真实 GUI 动作完成任务，例如鼠标拖动、点击、快捷键、菜单、工具选择。
7. 每次动作前检查 mode、TTL、急停、目标窗口身份和风险边界。
8. 每次动作后重新观察并验证画面变化。
9. 最终回答只在 GUI 证据通过后输出。
10. `/computer stop` 可以中止后续动作并清理自有资源。

## 4. 非目标

以下做法不是治本，不允许作为最终成熟路径：

- 不为 Paint 单独写一个皮卡丘脚本。
- 不为每个应用写一个专用 controller。
- 不靠应用白名单证明“通用性”。
- 不用 `System.Drawing`、PIL、ImageMagick、Canvas、SVG 或脚本直接生成最终图像冒充画图操作。
- 不用 `Start-Process mspaint <file>` 打开预生成文件冒充“用画图画出来”。
- 不让模型在 full mode 桌面任务中自由选择 `bash` 完成最终动作。
- 不把“应用已打开”当成“GUI 任务完成”。
- 不把自动化单元测试替代真实可见终端交互验收。

## 5. 架构总览

治本架构如下：

```text
用户普通提示词
-> DesktopTaskIntentRouter
-> FullModeSessionGate
-> DesktopTaskToolPolicy
-> GenericAppDiscovery
-> OwnedWindowBinder
-> ObservationFusion
-> PromptTaskPlanner
-> ClosedLoopExecutor
-> GenericGuiActionLayer
-> VerifiedWindowActionGate
-> PostActionVerifier
-> AcceptanceEvidenceRecorder
```

核心设计原则：

- 一个通用桌面任务路由器，不是多个应用专用控制器。
- 一个通用 GUI 动作层，不是每个应用一套动作实现。
- 代表性应用只用于验收通用能力，不作为架构本体。
- full mode 是高权限桌面任务模式，但仍保留急停、TTL、风险拦截、目标身份校验和审计。

## 6. 核心组件

### 6.1 DesktopTaskIntentRouter

职责：在每次普通用户提示词进入模型执行前，先判断它是否是本机桌面任务。

命中条件包括：

- 用户明确说“本机电脑”“本地电脑”“打开某软件”“使用某软件”。
- 用户要求点击、输入、拖动、画图、保存、复制粘贴、切换窗口。
- 用户要求操作 Windows 应用、桌面窗口、开始菜单、文件管理器、浏览器可见窗口。

输出：

```json
{
  "is_desktop_task": true,
  "reason": "local_app_operation_requested",
  "target_app_hint": "画图",
  "task_goal": "画一个皮卡丘",
  "requires_gui_actions": true
}
```

### 6.2 FullModeSessionGate

职责：确保桌面写动作只能在已确认的模式下执行。

规则：

- 未开启 `/computer use` 或 `/computer use --full` 时，桌面任务只能解释计划，不能真实动作。
- `/computer use --full` 只生成确认 token，不直接开启。
- `/computer use --full-confirm <token>` 成功后，写入 full session。
- full session 必须有 TTL，默认不超过 300 秒。
- 每个 GUI 动作前都必须重新检查 full session 是否仍有效。

### 6.3 DesktopTaskToolPolicy

职责：full mode 桌面任务中收窄工具选择，避免脚本绕路。

规则：

- `bash` 允许用于诊断，例如查找应用候选、读取日志、运行测试。
- `bash` 不允许完成桌面任务最终成果。
- 禁止桌面任务中出现 `System.Drawing`、PIL、ImageMagick、直接写 PNG、直接 `Start-Process mspaint <预生成图片>` 等绕路路径。
- 如果模型尝试用脚本完成最终成果，工具层必须拒绝，并返回 `desktop_task_requires_gui_route`。
- 模型只能通过 Computer Use 桌面执行器完成最终动作。

### 6.4 GenericAppDiscovery

职责：通用发现普通 Windows 应用，不依赖每个应用预置白名单。

发现来源：

- Start Menu 快捷方式。
- Windows App Paths。
- PATH 中可执行文件。
- 常见系统应用别名解析。
- 已安装应用索引。

安全边界：

- 普通应用可作为候选。
- 终端、管理员工具、UAC、安全中心、注册表、系统设置、支付、登录、凭据窗口必须拦截或二次确认。
- 发现候选不是授权，真实动作仍要通过 FullModeSessionGate 和 VerifiedWindowActionGate。

### 6.5 OwnedWindowBinder

职责：只操作 agent 自己启动并登记的窗口。

流程：

1. 启动目标应用。
2. 记录 pid、process path hash、window handle、窗口标题摘要。
3. 截图或 UIA 确认窗口可见。
4. 生成 target identity。
5. 动作前后都重新验证目标没有漂移。

如果发现焦点变成用户已有窗口、其它应用窗口、系统窗口或高风险窗口，必须停止动作并输出 `target_drift_blocks_action`。

### 6.6 ObservationFusion

职责：每次动作前后融合观察证据。

证据来源：

- 当前窗口列表。
- 目标窗口矩形。
- 屏幕截图。
- UIA 控件树。
- OCR 文本。
- 像素变化摘要。
- 动作前后差异。

验收要求：

- 不能只记录“动作已发送”。
- 必须记录“动作后画面或状态确实变化”。
- 对画图类任务，至少要记录画布区域的非空像素变化和目标窗口截图路径。

### 6.7 PromptTaskPlanner

职责：把普通自然语言任务变成通用 GUI 步骤。

示例：

```json
{
  "target_app": "mspaint",
  "goal": "draw_pikachu",
  "steps": [
    {"kind": "launch_app", "app_hint": "画图"},
    {"kind": "select_tool", "tool": "brush"},
    {"kind": "select_color", "color": "yellow"},
    {"kind": "draw_shape", "shape": "head_circle"},
    {"kind": "draw_shape", "shape": "ears"},
    {"kind": "draw_shape", "shape": "eyes"},
    {"kind": "draw_shape", "shape": "cheeks"},
    {"kind": "verify_canvas_nonblank"}
  ]
}
```

计划可以包含抽象绘制动作，但执行时必须落到通用 GUI 动作，例如 click、drag、hotkey、menu、type，而不是直接写图片文件。

### 6.8 GenericGuiActionLayer

职责：提供跨应用的 GUI 原子动作。

动作集合：

- focus_window
- click
- double_click
- drag
- move_mouse
- type_text
- hotkey
- menu_select
- scroll
- wait
- observe

绘图类任务可以使用 `drag_path`，它本质仍然是多个鼠标移动和拖动事件，必须被记录为真实 GUI 动作。

### 6.9 VerifiedWindowActionGate

职责：所有写动作进入底层发送前，必须通过目标窗口身份校验。

必须检查：

- full session 有效。
- abort 未触发。
- 目标窗口是 agent owned。
- 当前窗口身份与启动时身份一致。
- 动作类别被当前模式允许。
- 目标不是高风险窗口。
- 审计预写成功。

不满足任一条件，低层事件数必须保持 0。

### 6.10 AcceptanceEvidenceRecorder

职责：给真实验收留下可审计证据。

每次桌面任务必须输出：

- router 决策。
- 工具策略决策。
- app discovery 结果。
- owned window identity。
- before/after screenshots。
- low_level_event_count。
- gui_action_count。
- forbidden_script_path_used=false。
- target_drift_blocks_action 负例。
- `/computer stop` 清理结果。

## 7. Paint Pikachu 作为最终验收样本

Paint 皮卡丘不是架构本体，只是代表性验收样本。

它的价值是同时覆盖：

- 本机应用发现。
- 应用启动。
- 窗口绑定。
- 鼠标拖动。
- 颜色/工具选择。
- 画布变化验证。
- 禁止脚本伪造。
- 真实可见终端验收。

最终验收 prompt：

```text
请使用本地电脑的画图软件画一个皮卡丘。
```

通过条件：

- `desktop_task_router_used=true`
- `full_mode_session_used=true`
- `computer_use_gui_route_used=true`
- `bash_final_artifact_route_used=false`
- `forbidden_script_generation_used=false`
- `target_app=mspaint`
- `owned_window_verified=true`
- `gui_action_count>0`
- `low_level_event_count>0`
- `canvas_changed_after_actions=true`
- `post_action_screenshot_exists=true`
- `final_answer_printed=true`
- `computer_stop_passed=true`

失败条件：

- 生成 PNG 后打开 Paint。
- 直接用脚本绘制图片。
- 只打开 Paint 但没有 GUI 动作。
- GUI 动作没有绑定 agent 自己启动的 Paint 窗口。
- 没有动作后截图。
- 没有 `/computer stop`。
- 没有真实可见终端 controller 证据。

## 8. 实施路线

### M0: 冻结失败证据

目标：把 2026-06-05 的失败路径固化成负例。

产物：

- 添加回归测试：当前自然语言任务走 `bash + System.Drawing + Start-Process mspaint` 时必须判为失败。
- 添加验收断言：`forbidden_script_generation_used=false`。
- 更新成熟矩阵：full mode 未接管普通桌面任务时不能标记为“自然语言桌面任务成熟”。

### M1: Desktop Task Router

目标：普通提示词进入模型前先做桌面任务识别。

产物：

- 新增 DesktopTaskIntentRouter。
- 对“本地电脑画图软件画皮卡丘”返回桌面任务。
- 对普通代码问题、文档问题、搜索问题不误判。
- 交互入口把桌面任务交给 Computer Use 执行器。

### M2: Full Mode Tool Policy

目标：full mode 桌面任务中禁止脚本完成最终成果。

产物：

- 新增 DesktopTaskToolPolicy。
- 拦截 `System.Drawing`、直接写图片、直接打开预生成图片等路径。
- 保留诊断型 `bash` 能力，但不能完成最终桌面结果。
- 记录每次拒绝原因。

### M3: Generic App Discovery and Launch

目标：通用发现和启动目标应用。

产物：

- 扩展 GenericAppDiscovery。
- 支持中文应用 hint，例如“画图”映射到候选 Paint。
- 不依赖长期 per-app allowlist。
- 启动后登记 owned process。

### M4: Owned Window Binding

目标：只操作 agent 自己启动的窗口。

产物：

- 记录 pid、窗口句柄、标题摘要、进程路径哈希。
- 动作前后复验目标身份。
- 漂移时阻断动作且低层事件数保持 0。

### M5: GUI Action Loop

目标：普通桌面任务通过 observe -> plan -> act -> verify 闭环执行。

产物：

- 桌面任务计划进入 ClosedLoopExecutor。
- 每步写动作后必须观察和验证。
- 失败时重新观察或停止，不盲目连发坐标。

### M6: Drawing Primitive

目标：用通用鼠标动作支持画图类任务。

产物：

- 新增 `drag_path` 或等价通用动作，不绑定 Paint。
- 支持圆、线、折线、简单填充区域等高层计划落地为鼠标轨迹。
- 验证画布区域像素变化。

### M7: Strict Paint Pikachu Acceptance

目标：用真实可见终端证明最终用户任务真的完成。

产物：

- controller 场景输入 `/computer use --full`。
- 自动读取 token 并输入 `/computer use --full-confirm <token>`。
- 输入 `请使用本地电脑的画图软件画一个皮卡丘。`。
- 检查 GUI route token、禁用脚本 token、截图、低层事件、画布变化。
- 输入 `/computer stop` 并检查停止成功。

### M8: Final Maturity Matrix

目标：把新成熟边界写入 `/computer maturity`。

新增矩阵字段：

- `desktop_task_router=true`
- `natural_language_desktop_tasks_route_to_computer_use=true`
- `forbidden_script_artifact_route_blocked=true`
- `owned_window_gui_actions_verified=true`
- `paint_pikachu_visible_terminal_acceptance=true`

## 9. 停止条件

遇到以下情况必须停止实施并汇报，不允许用临时补丁绕过：

- 需要安装驱动、全局 hook、OCR 引擎、视觉模型或系统服务。
- 需要修改注册表、UAC、安全策略或系统默认设置。
- 无法稳定识别 agent 自己启动的目标窗口。
- 低层输入事件可能落到非目标窗口。
- 需要处理密码、验证码、支付、登录 token、私钥、API key。
- 真实可见终端 controller 无法启动、观察或输入。
- 验收只能靠脚本生成结果，而无法证明 GUI 动作。

## 10. 最终完成定义

只有同时满足以下条件，才能声明 `/computer use --full` 的自然语言桌面任务能力成熟：

1. 自动化测试证明桌面任务会路由到 Computer Use，而不是 `bash` 最终成果路径。
2. 自动化测试证明脚本伪造路径会被拒绝。
3. 自动化测试证明目标窗口身份漂移会阻断动作。
4. 自动化测试证明 GUI 动作后必须重新观察和验证。
5. 真实可见终端 controller 通过 Paint Pikachu 场景。
6. 真实验收结果包含动作前后截图和画布变化证据。
7. `/computer stop` 真实可见终端验收通过。
8. `/computer maturity` 明确显示自然语言桌面任务成熟字段。

最终成功 token 建议：

```text
COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY
COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK
desktop_task_router=true
natural_language_desktop_tasks_route_to_computer_use=true
computer_use_gui_route_used=true
forbidden_script_artifact_route_blocked=true
owned_window_gui_actions_verified=true
paint_pikachu_visible_terminal_acceptance=true
computer_stop_passed=true
```

## 11. 结论

真正的治本方案不是“禁止这一次的脚本”，也不是“给 Paint 写专用 controller”，而是把 `/computer use --full` 从权限状态升级成自然语言桌面任务执行体系。

本蓝图完成后，用户输入“使用本地电脑的某个普通软件完成任务”时，agent 必须走统一 Computer Use GUI 闭环。Paint 皮卡丘只是第一块硬验收石头：它通过，才能说明系统真的跨过了“打开权限但不接管任务路由”的结构性缺口。
