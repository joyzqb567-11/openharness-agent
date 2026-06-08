# learning_agent 双轨真实浏览器架构改造蓝图

日期：2026-06-01

状态：设计蓝图，尚未进入代码实现。

## 1. 蓝图目标

把 learning_agent 当前的真实浏览器能力升级为“双轨底层、单轨模型表面”的 Browser Runtime 架构。

这里的“双轨底层”是指底层同时支持：

1. Playwright / CDP / 可见 Chromium 路线：适合公开网页查询、本地前端调试、自动化验收、无登录态任务。
2. Chrome 插件 / Native Host / MCP Bridge 路线：适合当前用户 Chrome、登录态网站、OAuth、复杂表单、需要站点权限管控的真实浏览器任务。

这里的“单轨模型表面”是指大模型不直接选择“插件版浏览器”或“CDP 版浏览器”。模型只看到统一工具，例如 `browser_open`、`browser_click`、`browser_type`、`browser_snapshot`、`browser_tabs_context`。真正选择哪条底层路线，由代码里的 `BrowserProviderRouter` 负责。

最终目标不是机械复制 ClaudeCode，而是在 learning_agent 里实现一个可审计、可恢复、可回放、可验收，并且比纯 prompt 选择更不容易跑偏的真实浏览器架构。

## 2. ClaudeCode 源码事实边界

本蓝图基于已读取的 ClaudeCode 源码接入层：

1. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\setup.ts`
   - 负责启用 `claude-in-chrome` MCP、安装 native host、生成 allowed tools。
2. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\mcpServer.ts`
   - 负责创建 Chrome MCP context、bridge/native socket、权限模式、扩展配对信息。
3. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\chromeNativeHost.ts`
   - 负责 Chrome native messaging host 和 MCP client socket 转发。
4. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\prompt.ts`
   - 要求浏览器任务先调用 `tabs_context_mcp`，并规定 GIF、console、失败停止等规则。
5. `D:\ClaudeCode-main\ClaudeCode-main\skills\bundled\claudeInChrome.ts`
   - 把 Chrome 浏览器能力注册成 skill，并要求激活后先读 tab context。
6. `D:\ClaudeCode-main\ClaudeCode-main\commands\chrome\chrome.tsx`
   - 提供 `/chrome` 状态、安装、重连、权限说明。
7. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\toolRendering.tsx`
   - 确认可用工具族包含 `navigate`、`read_page`、`find`、`form_input`、`computer`、`gif_creator`、`read_console_messages`、`read_network_requests`、`tabs_context_mcp` 等。

重要边界：ClaudeCode 的核心浏览器包 `@ant/claude-for-chrome-mcp` 不在当前本地源码树里，因此不能把该包内部执行逻辑当作已读证据。本蓝图只参考可见源码中的架构方向，不依赖闭源包。

## 3. 当前 learning_agent 基线

learning_agent 已经具备以下能力：

1. `learning_agent/browser_automation_mcp_server.py`
   - 已有 `browser_open`、`browser_launch_visible`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_tabs`、`browser_console`、`browser_network`、`browser_upload_file`、`browser_downloads`、`browser_evaluate`、`browser_recover_page`、`browser_visual_locate`、`browser_flow_run`、`browser_replay`、`browser_plugin_status`、`browser_site_grant`、`browser_connect_real_chrome` 等工具。
2. `learning_agent/browser_real_chrome.py`
   - 已有真实 Chrome profile 检测、CDP 启动/连接、127.0.0.1 约束、敏感脚本拦截、审计日志。
3. `learning_agent/browser/action_executor.py`
   - 已有浏览器动作执行器、动作生命周期、重试、进度事件、只读批量并发、写动作串行。
4. `learning_agent/browser/runtime_store.py`
   - 已有 durable browser run、action、observation、event JSON/JSONL 持久化。
5. `learning_agent/browser/session_manager.py`
   - 已有 session、tab、visible/headless/real_chrome 状态管理。
6. `learning_agent/core/agent.py`
   - 已有真实 Chrome 意图识别、可见浏览器工具预加载、workflow 状态推进。
7. `learning_agent/acceptance_controller`
   - 已有真实可见终端验收控制器和 verifier 体系。

当前主要不足：

1. 没有 Chrome 插件和 native host，因此不能像 ClaudeCode 一样在浏览器内部管理当前标签页、站点权限和插件连接。
2. 缺少类似 `tabs_context_mcp` 的强制首步 tab context 合同。
3. CDP 真实 Chrome 和可见 Chromium 已可用，但 provider 边界不够清晰，未来加入插件后容易产生工具选择冲突。
4. 当前状态 UI/API 能力已有基础，但还没有 ClaudeCode `/chrome` 那种安装、连接、权限、当前 tab、View Tab 体验。
5. 缺少 GIF/录屏级过程证据，当前主要依赖截图、action log、event log。

## 4. 核心架构决策

### 4.1 不让模型直接选轨道

模型不应该看到两套同名能力，例如：

- `chrome_extension_open`
- `cdp_real_chrome_open`
- `visible_chromium_open`

这种设计会让模型在长任务里反复选错路线。

正确方式是只暴露统一工具：

- `browser_open`
- `browser_click`
- `browser_type`
- `browser_snapshot`
- `browser_tabs_context`
- `browser_submit`
- `browser_screenshot`
- `browser_console`
- `browser_network`
- `browser_provider_status`

工具内部调用 `BrowserProviderRouter`，由代码根据任务意图、权限状态、插件状态、登录态需求和用户显式要求选择 provider。

### 4.2 Provider 负责执行，Router 负责选择

新增抽象：

```text
BrowserProvider
  - kind
  - capabilities()
  - health()
  - tabs_context()
  - open()
  - snapshot()
  - click()
  - type_text()
  - press_key()
  - screenshot()
  - console()
  - network()
  - upload_file()
  - close()
```

Provider 实现：

1. `VisibleChromiumProvider`
   - 包装当前可见独立 Chromium / Playwright 能力。
2. `RealChromeCdpProvider`
   - 包装当前 `browser_connect_real_chrome` 和 CDP 能力。
3. `ChromeExtensionProvider`
   - 新增，包装 Chrome extension / native host / MCP bridge 能力。

Router 实现：

```text
BrowserProviderRouter
  - classify_intent(user_input, tool_name, arguments)
  - inspect_provider_health()
  - decide_provider()
  - enforce_permission()
  - record_decision()
  - execute_via_provider()
```

每次路由必须写入 event log：

```text
browser_provider_decision
  provider=chrome_extension
  reason=用户要求当前 Chrome 登录态
  fallback=real_chrome_cdp
  permission=site_granted
```

这样其他 agent 和 verifier 可以复盘为什么走某条轨道。

## 5. 路由规则

### 5.1 默认路线

公开网页查询、天气、旅游攻略、普通搜索、无登录态资料读取，默认走 `VisibleChromiumProvider`。

理由：它可见、隔离、风险低，不需要碰用户真实 Chrome profile。

### 5.2 当前 Chrome / 登录态路线

用户出现以下意图时，优先走 `ChromeExtensionProvider`：

- 当前 Chrome
- 我的浏览器
- 已登录网站
- 登录态
- OAuth
- 继续我当前页面
- 使用现有标签页
- 真实 Chrome 插件

如果插件不可用，Router 不能静默改走 CDP。必须按策略：

1. 如果用户已允许降级，走 `RealChromeCdpProvider`。
2. 如果没有允许降级，返回需要用户确认或安装插件的状态。

### 5.3 CDP 显式调试路线

用户明确要求以下内容时，走 `RealChromeCdpProvider`：

- `browser_connect_real_chrome`
- CDP
- remote debugging
- 调试端口
- 隔离 debug profile
- 危险调试模式

### 5.4 本地开发路线

本地前端、localhost、127.0.0.1、file 页面、开发服务器验收，默认走 `VisibleChromiumProvider` 或 Playwright。

理由：本地开发不应该默认接入用户日常 Chrome 登录态。

### 5.5 高风险动作路线

提交表单、上传文件、登录、付款、删除、发布、发送消息等高风险动作必须满足：

1. Router 确认 provider 支持权限控制。
2. 站点 origin 已授权。
3. 动作类型被授权，例如 read/click/type/submit/upload。
4. event log 记录权限决策。
5. 真实 Chrome 登录态场景禁止自动 replay 写动作。

## 6. 新增模块蓝图

### 6.1 `learning_agent/browser/providers/`

建议新增目录：

```text
learning_agent/browser/providers/
  protocol.py
  router.py
  registry.py
  visible_chromium.py
  real_chrome_cdp.py
  chrome_extension.py
  permission_model.py
  provider_events.py
```

职责：

1. `protocol.py` 定义 provider 接口和标准结果对象。
2. `router.py` 实现 provider 选择规则。
3. `registry.py` 注册所有 provider，并读取健康状态。
4. `visible_chromium.py` 包装现有 Playwright/可见 Chromium。
5. `real_chrome_cdp.py` 包装现有 CDP 真实 Chrome。
6. `chrome_extension.py` 连接新增插件 bridge。
7. `permission_model.py` 定义 read/click/type/submit/upload 权限。
8. `provider_events.py` 写路由和 provider 生命周期事件。

### 6.2 Chrome 插件与 Native Host

建议新增：

```text
learning_agent/chrome_extension/
  manifest.json
  background.js
  content_script.js
  page_bridge.js
  options.html
  options.js

learning_agent/browser_extension_host/
  native_host.py
  bridge_server.py
  manifest_installer.py
  pairing_store.py
  message_protocol.py
```

插件最小职责：

1. 读取当前 tab 列表和 active tab。
2. 读取页面可见文本和可交互元素。
3. 执行 click/type/press_key/scroll/navigate。
4. 读取 console/network 摘要。
5. 管理站点级权限。
6. 把每次动作结果发回 native host。

Native Host 最小职责：

1. 通过 Chrome Native Messaging 与插件通信。
2. 通过本地 socket 或 stdio 与 learning_agent MCP server 通信。
3. 校验消息 schema。
4. 持久化 pairing 状态。
5. 不记录 cookie、localStorage、sessionStorage、token、password 原文。

### 6.3 统一状态命令

建议新增或扩展：

```text
browser_provider_status
browser_tabs_context
browser_permissions
browser_extension_status
browser_record_start
browser_record_stop
browser_gif_export
```

状态输出必须能看到：

1. 当前 provider。
2. provider 选择原因。
3. 插件是否安装。
4. native host 是否连接。
5. 当前 tab 数量。
6. active tab。
7. 当前 origin 权限。
8. 最近动作。
9. 最近失败和恢复。
10. 最近 observation / screenshot / replay artifact。

## 7. 分阶段实施计划

### Stage 0：蓝图确认与范围冻结

目标：冻结本蓝图，确认不是立即全量开改。

产物：

1. 本蓝图文档。
2. `agent_memory/progress.md` 记录。
3. 后续执行计划文件。

停止条件：

1. 用户确认蓝图。
2. 未进入代码实现。

### Stage 1：Provider Protocol 和 Router 空实现

目标：先建立 provider 抽象，不改变现有浏览器行为。

产物：

1. `BrowserProvider` 协议。
2. `BrowserProviderRouter`。
3. 路由规则单元测试。
4. `browser_provider_decision` event schema。

验收：

1. 现有 `browser_open` 等工具行为不变。
2. 单测证明公开网页、当前 Chrome、CDP 显式调试、本地开发四类意图能选出预期 provider。

### Stage 2：现有 Playwright/CDP 能力迁入 Provider

目标：把当前 `browser_automation_mcp_server.py` 中的执行逻辑逐步迁到 provider，但保持工具名不变。

产物：

1. `VisibleChromiumProvider`。
2. `RealChromeCdpProvider`。
3. adapter 兼容旧工具参数。

验收：

1. 现有浏览器单测全部通过。
2. 真实可见 Chromium 验收通过。
3. CDP 真实 Chrome 既有验收不退化。

### Stage 3：统一工具表面和模型防误选

目标：确保模型只看到统一工具，不看到 provider-specific 工具。

产物：

1. 统一 `browser_*` schema。
2. provider-specific 工具标记为 internal 或 advanced。
3. prompt/harness 改成“调用统一浏览器工具，不选择底层 provider”。

验收：

1. 模型首轮工具池不同时暴露“插件 open”和“CDP open”。
2. event log 记录 provider 决策原因。

### Stage 4：`browser_tabs_context` 合同

目标：对齐 ClaudeCode `tabs_context_mcp` 的关键能力。

产物：

1. `browser_tabs_context`。
2. 真实 Chrome 登录态任务强制首步读 tab context。
3. tab id 不能跨 session 复用。
4. tab closed/navigation error 后自动刷新 context。

验收：

1. 当前 Chrome/登录态任务未读 tab context 时，Router 不允许直接 click/type。
2. 状态输出可见 tab 列表、active tab、URL、title、provider。

### Stage 5：Chrome 插件 MVP，只读能力

目标：先实现插件只读闭环，不做点击输入。

产物：

1. Chrome extension manifest。
2. native host installer。
3. 插件连接状态。
4. 当前 tab 列表。
5. active tab 文本读取。
6. screenshot 或可见区域摘要。

验收：

1. 插件可安装。
2. native host 可连接。
3. learning_agent 能通过统一 `browser_tabs_context` 和 `browser_snapshot` 读到当前 Chrome 页面。
4. 不读取 cookie/localStorage/sessionStorage/token/password。

### Stage 6：Chrome 插件写动作

目标：让插件 provider 能完成拟人化 click/type/key/navigate。

产物：

1. click。
2. type。
3. press_key。
4. navigate。
5. form_input。
6. scroll。
7. element locator。

验收：

1. 插件 provider 能在真实 Chrome 当前页面点击和输入。
2. 每个动作进入 `BrowserActionExecutor`。
3. 每个动作有 action/event/observation 证据。

### Stage 7：插件站点权限

目标：插件侧管理站点级权限，超过纯 CDP 的安全边界。

权限类型：

1. read。
2. click。
3. type。
4. submit。
5. upload。
6. console。
7. network。

验收：

1. 未授权 origin 只能读状态，不能点击输入。
2. 授权 origin 后才能执行对应动作。
3. 权限变更写入 event log。
4. 高风险提交前需要明确权限或用户确认。

### Stage 8：状态 UI / CLI / API 生态

目标：对齐 ClaudeCode `/chrome` 的状态体验。

产物：

1. `browser_provider_status`。
2. `browser_extension_status`。
3. 终端状态渲染。
4. HTTP/status API。
5. 最近 tab、run、action、permission、observation 输出。

验收：

1. CLI/API 能看到 provider、插件连接、native host、tab、权限、最近动作。
2. 其他 agent 能通过状态 API 判断当前真实浏览器是否可用。

### Stage 9：GIF/录屏/视觉证据

目标：补 ClaudeCode `gif_creator` 方向的可视化过程证据。

产物：

1. `browser_record_start`。
2. `browser_record_stop`。
3. `browser_gif_export`。
4. action 自动关联截图帧。

验收：

1. 多步骤表单流程能生成可查看 GIF 或帧序列。
2. verifier 能确认 GIF/帧序列 artifact 存在。

### Stage 10：失败恢复和 fallback 策略

目标：插件不可用、tab 丢失、页面卡死、权限不足时不乱跑。

规则：

1. 插件不可用，当前 Chrome/登录态任务不能静默退到可见 Chromium。
2. 用户允许降级时，才可退到 CDP。
3. 普通公开网页任务可从插件/CDP 降级到可见 Chromium。
4. tab 无效时先刷新 `browser_tabs_context`。
5. 连续 2-3 次浏览器动作失败后停止并汇报。

验收：

1. 单测覆盖 fallback。
2. 真实终端验收覆盖插件断开场景。

### Stage 11：长任务 harness 接入

目标：确保浏览器 provider 不是旁路系统。

必须接入：

1. harness run。
2. stage。
3. task queue。
4. event log。
5. action executor。
6. observation store。
7. replay。
8. verifier。
9. resume/checkpoint。

验收：

1. 进程中断后，已完成浏览器 stage 不重跑。
2. 状态 CLI/API 能看到 provider 决策、tab context、action、verifier 结果。

### Stage 12：真实可见终端总验收

目标：只有通过真实终端和真实浏览器，才算任务完成。

必须使用：

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

验收场景：

1. 普通公开网页查询：应走可见 Chromium。
2. 用户要求“当前 Chrome 登录态”：应走 Chrome 插件 provider。
3. 用户明确要求 CDP 调试：应走 RealChromeCdpProvider。
4. 插件不可用但用户未允许降级：应停止并说明。
5. 复杂表单：站点授权后才能 click/type/submit。
6. 中断恢复：已完成阶段不重跑。
7. 状态检查：CLI/API 能看到 run、stage、task、event、output、verifier、provider、tab、permission。

完成标准：

1. 代码修改完成。
2. 自动化测试通过。
3. 独立 verifier 通过。
4. `start_oauth_agent.bat` 真实可见终端交互验收通过。
5. 浏览器实际可见、可点、可输入、可读页面结果。

## 8. 成功标准

任务最终完成时，必须同时满足：

1. 模型只看到统一浏览器工具，不直接面对 provider 混乱。
2. Router 能稳定选择 `visible_chromium`、`real_chrome_cdp`、`chrome_extension`。
3. 当前 Chrome/登录态任务默认插件优先。
4. 插件不可用时不会静默走错轨道。
5. 公开网页和本地调试不会默认污染用户真实 Chrome profile。
6. 每次 provider 决策都进入 event log。
7. 每个浏览器动作都进入 `BrowserActionExecutor`。
8. 每个真实浏览器任务都有 run/action/observation/replay/verifier 证据。
9. 状态 CLI/API 能让其他 agent 看懂当前浏览器能力和任务状态。
10. 真实可见终端验收通过后才允许声明开发完成。

## 9. 不做事项

第一轮不做：

1. 不直接复刻 ClaudeCode 闭源 `@ant/claude-for-chrome-mcp`。
2. 不让模型同时看到插件版和 CDP 版重复工具。
3. 不默认读取用户 cookie、localStorage、sessionStorage。
4. 不默认对登录态页面做 replay 写动作。
5. 不跳过真实可见终端验收。
6. 不把 README 当作关键证据。

## 10. 风险与控制

风险一：模型选错浏览器轨道。

控制：模型表面单轨，Router 代码级选择，provider 决策写日志。

风险二：插件模式增加系统复杂度。

控制：先只读 MVP，再写动作，再权限，再状态生态。

风险三：真实 Chrome 登录态隐私风险。

控制：插件侧站点权限、敏感字段禁止、事件脱敏、真实 Chrome replay 禁写。

风险四：长任务中断后状态分裂。

控制：所有 provider 动作必须接入现有 `BrowserRuntimeStore`、harness event log 和 resume checkpoint。

风险五：CDP 和插件同时连接同一页面造成冲突。

控制：同一个 browser run 只能有一个 active provider；切换 provider 必须产生 `browser_provider_switch` 事件，并关闭或冻结旧 provider 的写能力。

## 11. 推荐下一步

下一步不是直接写插件，而是先写实施计划：

```text
docs/superpowers/plans/2026-06-01-browser-dual-track-architecture-implementation.md
```

实施计划应从 Stage 1 开始，先实现 Provider Protocol 和 Router 空实现，用测试锁死“模型表面单轨、代码选择 provider”的核心原则。只有这个原则稳定后，才进入 Chrome 插件和 native host 实现。
