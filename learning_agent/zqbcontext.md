# zqbcontext 上下文恢复档案

更新时间：2026-06-01

说明：本文件用于让后续 agent 或 Codex 会话快速恢复当前窗口的项目上下文。这里保存项目事实、用户要求、已完成事项、源码比较结论、验收证据和后续风险。不保存内部推理过程；涉及用户账号、密码、登录态等敏感内容时已脱敏。

---

## 1. 当前项目路径

- 当前 OpenHarness / learning_agent 项目根目录：
  - `H:\codexworkplace\sofeware\OpenHarness-main`
- 当前 learning_agent 目录：
  - `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent`
- ClaudeCode 源码参考目录：
  - `D:\ClaudeCode-main\ClaudeCode-main`
- 重要路径规则：
  - 当前项目运行路径以 H 盘为准。
  - 后续不要再把当前 OpenHarness 项目误判为 D 盘路径。
  - 只有 ClaudeCode 参考源码仍在 `D:\ClaudeCode-main\ClaudeCode-main`。

---

## 2. 用户长期目标

用户正在打造一个成熟的 AI agent 项目，核心目标是：

- learning_agent 要具备接近或超过 ClaudeCode 的 agent 能力。
- learning_agent 要能被 Codex、ClaudeCode 或其他 agent 调试、控制和验收。
- learning_agent 要具备超长任务不跑偏的 harness 能力。
- learning_agent 要具备真实可见终端验收能力。
- learning_agent 要具备真实浏览器能力，包括可见浏览器、真实 Chrome、页面观察、点击、输入、登录态安全、任务回放和断言验证。
- 最终目标是形成一个可以自我开发、调试、升级另一个 agent 项目的 AI agent 闭环。

---

## 3. AGENTS.md 中需要长期遵守的项目规则摘要

以下规则来自用户在当前窗口提供的 AGENTS.md 指令，后续继续开发时必须优先遵守：

- 用户是代码小白、agent 小白，解释必须通俗易懂，说人话。
- 新写或修改代码时，用户要求每一行代码都要有中文注释，说明这行代码的作用、意图，以及没有这行代码会导致什么问题。
- 新写或修改的代码和中文注释，需要另存一份到 `learning_agent\test` 下，方便用户学习和查看。
- 新增或修改代码的注释开头需要包含类似 `新增代码+名称` 或 `修改代码+名称`，名称用于说明这段代码的目的。
- 非简单任务必须先读相关文件，再决定改动方案。
- 涉及多文件、运行时逻辑、公开接口、复杂排查或跨多轮任务时，需要先给出计划，再开始修改。
- 多步骤或长期任务要先转成可验证的成功标准、范围边界、停止条件和验证方式。
- 项目级上下文维护在：
  - `agent_memory/context.md`
  - `agent_memory/progress.md`
  - `agent_memory/bugs.md`
  - 必要时 `agent_memory/experience.md`
- 修 bug 时不能把猜测当结论，需要先用源码和证据确认。
- agent 设计采用极简提示词原则，让模型注意力不漂移，同时保持功能完善。
- 每次开发 agent 功能后，最终回答前必须完成真实可见终端交互验收。

真实可见终端交互验收的定义：

1. 必须启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`。
2. 必须是用户本地电脑上可见的真实终端窗口。
3. 必须在该终端里的 agent 交互提示符中输入测试 prompt。
4. 必须观察该终端中的 agent 输出结果。
5. 必须确认真实终端场景下功能成功后，才允许说“开发完成”或“验收通过”。

以下方式不能替代真实可见终端验收：

- 单元测试通过不能替代。
- py_compile 通过不能替代。
- HTTP command bridge 调用不能替代。
- CLI run --prompt 调用不能替代。
- 管道输入 stdin 不能替代。
- selftest 不能替代。
- 只查看日志不能替代。
- 只证明 MCP 工具被调用不能替代。

如果 Codex 当前环境无法打开、观察或输入真实可见终端，必须明确说明：

> 真实可见终端交互验收未完成，不能声明开发完成。

---

## 4. 当前窗口中的历史任务脉络

本窗口里用户先后推动了以下任务：

1. 读取和分析当前 OpenHarness / learning_agent 项目，判断项目性质。
2. 将当前项目路径从 D 盘误判修正为 H 盘路径。
3. 为当前项目创建 git 仓库，方便后续使用 git 指令。
4. 仔细阅读 ClaudeCode 源码，比较 learning_agent 与 ClaudeCode agent 能力差距。
5. 将差距记录成 agent 能看懂的文档，并备份为 markdown 文档。
6. 解释 ClaudeCode 的优势：
   - 主循环：异步生成器、流式响应、自动 compact、异常恢复。
   - 工具接口：完整 Tool 协议，含权限、并发、安全、UI、结果限制。
   - 工具执行：支持 hook、权限决策、并发批处理、流式工具执行。
7. 制定并执行补齐计划：
   - 主循环事件流。
   - 工具协议。
   - 工具执行器。
   - 权限 hook。
   - 会话恢复。
8. 阅读 `learning_agent\acceptance_controller` 和 `learning_agent\core\agent.py`，确认 learning_agent 可以被其他 agent 控制输入 prompt 并观察输出。
9. 检查是否存在“断言验证器”，用于可审计、可复现的真实验收。
10. 分析 learning_agent 是否有独立 harness 模块，并参考 ClaudeCode 制定长任务 harness 对齐方案。
11. 分 8 个阶段执行长任务 harness 建设，要求最终必须真实启动 learning_agent 后验证。
12. 多次要求不要只完成文件和单测，必须真正接管主循环、事件日志、任务队列、恢复、状态 CLI/API 和真实终端验收。
13. 对 compact/resume 和 UI/SDK 状态生态进行对齐。
14. 开始强化真实浏览器能力：
    - 页面失败恢复。
    - 视觉定位。
    - 复杂网站流程。
    - 登录态安全。
    - 插件兼容。
    - 异常重试。
    - 任务回放。
15. 真实浏览器测试场景包括：
    - 查询 3 天后武汉天气并做旅游攻略。
    - 打开 `www.qianwen.com`，输入天气查询 prompt 并提交。
    - 打开雷神 H5 页面，输入用户提供的测试账号和密码，登录并观察内容。
16. 注意：用户曾提供真实登录测试账号和密码，本文件不保存明文密码。账号也已部分脱敏。
17. 用户进一步要求从治本角度升级真实浏览器能力，而不是不断补护栏和漏洞。
18. 参考 ClaudeCode 源码制定真实浏览器升级计划。
19. 执行 browser runtime / 双轨真实浏览器改造多个阶段。
20. 最新任务是比较 ClaudeCode 本地真实浏览器源码与 learning_agent 当前真实浏览器能力，并估算达到 ClaudeCode 的百分比。

---

## 5. ClaudeCode 已读源码证据摘要

本窗口中已经读取并分析过 ClaudeCode 以下关键源码，不应再把 README 当关键证据：

### 5.1 Chrome 浏览器集成

已读文件：

- `D:\ClaudeCode-main\ClaudeCode-main\entrypoints\cli.tsx`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\setup.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\mcpServer.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\prompt.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\toolRendering.tsx`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\common.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\skills\bundled\claudeInChrome.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\commands\chrome\chrome.tsx`
- `D:\ClaudeCode-main\ClaudeCode-main\hooks\usePromptsFromClaudeInChrome.tsx`

源码确认的 ClaudeCode Chrome 能力：

- 通过 `claude-in-chrome` MCP / Chrome 扩展 / native host / bridge 接入真实 Chrome。
- CLI 入口支持 `--claude-in-chrome-mcp` 和 `--chrome-native-host`。
- `setupClaudeInChrome()` 会构造动态 MCP 配置和允许工具名。
- 如果 session 是 bypass permission 模式，会设置 `CLAUDE_CHROME_PERMISSION_MODE=skip_all_permission_checks`。
- 支持检测 Chrome 扩展是否安装。
- Windows 下有 native host 注册逻辑，源码中存在 `registerWindowsNativeHosts(manifestPath)`。
- 支持 browser bridge/native socket、OAuth token、user id、device id、extension pairing。
- Chrome skill 会要求先调用 `tabs_context_mcp` 获取当前标签页上下文。
- Chrome 工具渲染中出现的工具包括：
  - `javascript_tool`
  - `read_page`
  - `find`
  - `form_input`
  - `computer`
  - `navigate`
  - `resize_window`
  - `gif_creator`
  - `upload_image`
  - `get_page_text`
  - `tabs_context_mcp`
  - `tabs_create_mcp`
  - `update_plan`
  - `read_console_messages`
  - `read_network_requests`
  - `shortcuts_list`
  - `shortcuts_execute`
- `/chrome` 命令提供扩展安装、重连、权限管理和默认启用状态切换。
- ClaudeCode 终端 UI 能显示 Chrome status、extension installed 状态、site permission 和 View Tab 链接。

重要边界：

- ClaudeCode 的很多核心浏览器细节在外部包 `@ant/claude-for-chrome-mcp` 中。
- 当前本地 ClaudeCode 源码只能确认集成方式、工具表面和生命周期，不能 100% 确认外部包内部视觉定位、页面恢复、browser_task/lightning_turn 的完整算法。

### 5.2 Computer Use

已读文件：

- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\setup.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\mcpServer.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\wrapper.tsx`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\executor.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\gates.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\components\permissions\ComputerUseApproval\ComputerUseApproval.tsx`

源码确认的 ClaudeCode Computer Use 能力：

- 通过 `computer-use` MCP 接入 OS 级操作。
- 有 app allowlist、permission approval、display selection、screenshot dims、global Escape abort、OS notification。
- 能做鼠标移动、点击、拖拽、滚轮、键盘输入、剪贴板读写、截图、缩放、应用管理。
- 使用 file lock 防止多个 computer-use 同时控制。
- 对工具结果图片和文本进行 Anthropic API content block 映射。

重要边界：

- `executor.ts` 源码显示该 Computer Use 执行器是 macOS 路线，非 Windows 通用能力。
- 因此对 Windows 上的 learning_agent 比较时，不能直接说 ClaudeCode Windows 已具备同等 OS 级 computer-use。

### 5.3 工具执行、MCP、权限和并发

已读文件：

- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\StreamingToolExecutor.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\toolExecution.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\services\mcp\client.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\services\mcp\config.ts`
- `D:\ClaudeCode-main\ClaudeCode-main\plugins\builtinPlugins.ts`

源码确认的 ClaudeCode 工具执行优势：

- 工具流式输入时可以边收到边入队执行。
- 并发安全工具可以并行执行。
- 非并发安全工具会串行或独占执行。
- 结果按顺序缓冲返回。
- Bash sibling 工具失败时可以 abort。
- 工具生命周期包含：
  - schema validation。
  - input validation。
  - permission classifier。
  - pre-tool hook。
  - permission decision。
  - denied result。
  - execution span / telemetry。
  - result truncate。
  - post-tool hook。
  - MCP auth error state。
  - post-tool failure hook。
- `claude-in-chrome` 和 `computer-use` 是保留 MCP server name，避免用户自定义 MCP 同名冲突。

---

## 6. learning_agent 已读源码证据摘要

本窗口中已经读取并分析过 learning_agent 以下关键源码：

### 6.1 真实浏览器 MCP server

关键文件：

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\browser_automation_mcp_server.py`

源码确认的工具能力包括：

- `browser_launch_visible`
- `browser_open`
- `browser_snapshot`
- `browser_click`
- `browser_type`
- `browser_type_secret`
- `browser_press_key`
- `browser_wait`
- `browser_screenshot`
- `browser_tabs`
- `browser_tabs_context`
- `browser_console`
- `browser_network`
- `browser_upload_file`
- `browser_downloads`
- `browser_evaluate`
- `browser_close`
- `browser_recover_page`
- `browser_visual_locate`
- `browser_flow_run`
- `browser_replay`
- `browser_plugin_status`
- `browser_provider_status`
- `browser_extension_status`
- `browser_site_grant`
- `browser_connect_real_chrome`
- `browser_disconnect_real_chrome`
- `browser_profile_status`

源码确认的边界：

- `browser_open` 默认是独立 Chromium，不等同用户日常 Chrome。
- 真实 Chrome 需要通过 `browser_profile_status` / `browser_connect_real_chrome` 进入。
- 真实 Chrome CDP fallback 需要显式允许，不能静默降级。
- 敏感输入工具 `browser_type_secret` 禁止回放，避免密码重复输入或泄露。
- `browser_evaluate` 在真实 Chrome 模式下会拦截 cookie、storage、token、password 等敏感脚本。

### 6.2 Browser Provider 双轨/多轨架构

关键文件：

- `learning_agent\browser\providers\protocol.py`
- `learning_agent\browser\providers\router.py`
- `learning_agent\browser\providers\registry.py`
- `learning_agent\browser\providers\visible_chromium.py`
- `learning_agent\browser\providers\real_chrome_cdp.py`
- `learning_agent\browser\providers\chrome_extension.py`
- `learning_agent\browser\providers\tool_surface.py`

源码确认的 provider：

- `visible_chromium`
- `real_chrome_cdp`
- `chrome_extension`
- `unavailable`

Router 规则：

- 显式 CDP / 调试端口 / `browser_connect_real_chrome` 类意图走 `real_chrome_cdp`。
- 当前 Chrome、登录态、当前 tab 等意图优先走 `chrome_extension`。
- 插件不可用时，只有显式 `allow_cdp_fallback=true` 才降级到 CDP。
- 本地开发和普通公开网页默认走可见 Chromium。
- 模型不应直接选择 provider-specific 重复工具，而应调用统一 `browser_*` 工具。

### 6.3 Chrome Extension / Native Host scaffold

关键文件：

- `learning_agent\chrome_extension\manifest.json`
- `learning_agent\chrome_extension\background.js`
- `learning_agent\chrome_extension\content_script.js`
- `learning_agent\chrome_extension\page_bridge.js`
- `learning_agent\browser_extension_host\bridge_server.py`
- `learning_agent\browser_extension_host\native_host.py`
- `learning_agent\browser_extension_host\message_protocol.py`
- `learning_agent\browser_extension_host\manifest_installer.py`
- `learning_agent\browser_extension_host\pairing_store.py`

源码确认的能力：

- 已有 Chrome extension 文件结构。
- 已有 native messaging host 入口。
- 已有 bridge state 文件。
- 支持 `tabs_context`、`read_page`、`status` 只读消息。
- 支持写动作 pending command：
  - `poll_commands`
  - `action_result`
- Chrome extension provider 支持：
  - `browser_tabs_context`
  - `browser_snapshot`
  - `browser_extension_status`
  - `browser_click`
  - `browser_type`
  - `browser_press_key`
  - `browser_open`
  - `browser_wait`
  - `browser_visual_locate`
- 支持 origin + action 级别站点权限：
  - `read`
  - `click`
  - `type`
  - `submit`
  - `upload`
  - `console`
  - `network`

重要差距：

- `manifest_installer.py` 当前只生成 manifest 文件，不像 ClaudeCode 那样自动写 Windows registry 完成生产级 native host 注册。
- 当前插件路线已经有 scaffold 和测试，但还没有达到 ClaudeCode 生产级扩展安装、配对和 UI 管理成熟度。

### 6.4 Browser Runtime、session、action、flow、replay、status

关键文件：

- `learning_agent\browser\runtime_models.py`
- `learning_agent\browser\runtime_store.py`
- `learning_agent\browser\runtime_events.py`
- `learning_agent\browser\session_manager.py`
- `learning_agent\browser\tab_registry.py`
- `learning_agent\browser\observation.py`
- `learning_agent\browser\locator.py`
- `learning_agent\browser\action_executor.py`
- `learning_agent\browser\flow_runtime.py`
- `learning_agent\browser\harness_integration.py`
- `learning_agent\browser\recovery.py`
- `learning_agent\browser\replay.py`
- `learning_agent\browser\recording.py`
- `learning_agent\browser\assertions.py`
- `learning_agent\runtime\status_snapshot.py`

源码确认的能力：

- Browser runtime store 可以保存：
  - browser run。
  - browser action。
  - browser observation。
  - browser event log。
- Session manager 管理：
  - session mode。
  - visible/headless 状态。
  - tab count。
  - active tab id。
  - profile summary。
  - profile scope。
- Tab registry 提供稳定 tab id，避免跨 session 重复。
- Observation engine 保存：
  - URL。
  - title。
  - visible text。
  - console。
  - network。
  - elements。
  - screenshot path。
  - artifact paths。
- Locator engine 支持按文本、aria、placeholder、selector、element_id、坐标等候选评分。
- Action executor 支持：
  - started/completed/failed 事件。
  - 写动作串行锁。
  - 只读批处理并发。
  - retry attempts。
  - result chunk/progress 事件。
- Flow runtime 支持：
  - flow_id。
  - stages_file。
  - 每阶段 checkpoint。
  - 中断后跳过已完成阶段。
  - failed_stage 记录。
- Harness integration 把 browser runtime 映射到长任务 harness：
  - run。
  - stage。
  - checkpoint。
  - verifier_result。
  - provider decision。
- Replay 会跳过 secret 输入和高风险工具。
- Recording 支持：
  - PNG frames。
  - recording manifest。
  - GIF export。
- BrowserAssertionEngine 支持：
  - `url_contains`
  - `title_contains`
  - `visible_text_contains`
  - `screenshot_exists`
  - `secret_not_leaked`
  - `console_no_severe_error`
- `status_snapshot.py` 已有 browser 区块，可供 terminal、SDK、HTTP、CLI、agent 工具统一读取。

---

## 7. 长任务 harness 对齐上下文

历史目标：

- learning_agent 长任务 harness 要至少对齐 ClaudeCode 的核心 harness 能力。
- 不能只是完成文件和单元测试。
- 真实终端输入 prompt 后必须自动创建 durable harness run。
- `agent.run()`、`run_events()`、harness event log 必须统一。
- task、background command、team peer 不能只存在内存字典里。
- 后台任务完成后必须能自动回灌到下一轮模型上下文。
- 进程中断后必须能从 checkpoint/session/queue 恢复，不重跑已完成阶段。
- 状态 CLI/API 必须能看见 run、stage、task、event、output、verifier 结果。
- 最终必须通过 `start_oauth_agent.bat` 真实可见终端验收。

当前已记录的能力：

- `LearningAgent.run()` 已接入 runtime/session_runtime，把真实终端 prompt 进入 durable runtime queue。
- `RuntimeCommandQueue` 已把 prompt、task_notification、resume_interrupted 进入真实模型轮次。
- Background shell commands 已变成 durable tasks。
- Completion 会写入 memory/tasks，并 enqueue task_notification。
- `run_events()` 与 status event store、transcript、harness mirror 有过对齐工作。
- Compact/resume 已有 transcript v2、turn ledger、compact boundary、resume repair report。
- Status ecosystem 已有：
  - terminal `/status`
  - SDK status
  - HTTP status endpoints
  - CLI snapshot
  - model-callable status tools

仍需记住：

- 后续如果继续评估 harness 是否“完全对齐 ClaudeCode”，必须继续查源码和真实验收，不能只凭过去结论猜。
- 若只是新增文件和单测，但没有接管真实主循环和真实终端场景，不算真正对齐。

---

## 8. 真实浏览器能力建设历史阶段

以下是本窗口中已推进过的真实浏览器建设方向：

### 8.1 早期真实浏览器补强

用户指出缺失：

- 页面失败恢复。
- 视觉定位。
- 复杂网站流程。
- 登录态安全。
- 插件兼容。
- 异常重试。
- 任务回放。

曾执行的真实浏览器验收场景：

- 武汉天气和旅游攻略。
- qianwen.com 输入天气查询 prompt。
- 雷神 H5 登录并观察页面内容。

敏感信息处理：

- 用户曾提供真实登录测试账号和密码。
- 本文件不保存明文密码。
- 脱敏账号示例：`138****4225`。
- 密码字段：`[已脱敏，不写入上下文文件]`。

### 8.2 Browser Runtime / 双轨架构阶段

已完成的设计方向：

- 不继续只在 `browser_click` / `browser_type` 上补零散护栏。
- 建立 Browser Protocol。
- 建立 Runtime Store。
- 建立 Session Manager。
- 建立 Observation Engine。
- 建立 Locator Engine。
- 建立 Action Executor。
- 建立 Recovery / Replay / Verifier。
- 建立 Status Ecosystem。
- 建立 Chrome Extension provider scaffold。

已记录的阶段能力：

- Stage 1：BrowserProviderRouter。
- Stage 2：VisibleChromiumProvider / RealChromeCdpProvider 接入真实 server call 路径。
- Stage 3：统一工具表面，不暴露 provider-specific 重复动作工具。
- Stage 4：`browser_tabs_context` 合同，真实 Chrome / 登录态写动作前必须先读 tab context。
- Stage 5：Chrome extension 只读 MVP。
- Stage 6：Chrome extension 写动作命令队列。
- Stage 7：Chrome extension origin + action 级站点权限。
- Stage 8：provider/native host/tab/permission/action/observation 状态生态。
- Stage 9：浏览器视觉证据、帧序列和 GIF。
- Stage 10：fallback/recovery，不静默降级 CDP，连续失败停止。
- Stage 11：浏览器 runtime 与 long-task harness 集成。
- Stage 12：双轨真实浏览器总体验收。

历史验收记录中出现过的证据：

- `learning_agent\acceptance_controller\scenarios\browser_dual_track_stage12_acceptance.json`
- `learning_agent\acceptance_controller\scenarios\browser_harness_integration_stage11_acceptance.json`
- `learning_agent\acceptance_controller\scenarios\real_chrome_qianwen_yinzhou_weather.json`
- `learning_agent\acceptance_controller\scenarios\real_chrome_leishen_login_content.json`
- `learning_agent\acceptance_controller\scenarios\browser_visible_runtime_acceptance.json`

历史记忆中记录过一次 Stage 12 fresh verification：

- `python -m unittest discover -s learning_agent\tests`
- 结果曾记录为 `Ran 546 tests ... OK (skipped=1)`。
- Controller 曾记录 `ACCEPTANCE_CONTROLLER_COMPLETED=True`。
- Verifier 曾记录 `completed=true`、`assertion.passed=true`。

注意：

- 后续如果要再次声明通过，必须重新按当前代码真实验证，不能只引用旧记录。

---

## 9. 最新 ClaudeCode vs learning_agent 本地真实浏览器对比结论

用户最新要求：

> 仔细阅读和分析 ClaudeCode 中可以调用本地真实浏览器的源码，然后与 learning_agent 当前可以调用本地真实浏览器比较，差距还有多少，大概目前达到 ClaudeCode 的百分之多少。

已完成的回答结论：

- learning_agent 当前本地真实浏览器能力大约达到 ClaudeCode 的 `70% 到 78%`。
- 中位估算约 `72%`。
- 如果只看 Windows 上可验证的真实 Chrome / 可见浏览器任务，可接近 `75% 到 80%`。
- 如果把 ClaudeCode 的生产级 Chrome 插件安装、native host 配对、外部 `@ant/claude-for-chrome-mcp` 能力、macOS computer-use、终端 UI 和成熟工具执行器全部算进去，learning_agent 大约是 `65% 到 70%`。

分维度估算：

| 维度 | learning_agent 当前情况 | 估算对齐度 |
|---|---|---|
| 可见浏览器基础操作 | 已有可见 Chromium、真实 Chrome CDP、点击、输入、截图、console/network | 85% 到 90% |
| 当前 Chrome / 登录态控制 | 有 `browser_connect_real_chrome` 和插件 provider scaffold | 65% 到 75% |
| Browser task flow / replay / harness / status | 有 flow checkpoint、runtime store、replay、verifier、status | 80% 到 85% |
| 插件 / extension 生态 | 有 scaffold、native host 协议、site permission，但生产安装弱 | 50% 到 60% |
| OS 级拟人鼠标键盘 | 主要是浏览器内 CDP/Playwright/插件动作 | 35% 到 45% |
| 工具执行 runtime / permissions / hooks / concurrency | 有 BrowserActionExecutor，但没有 ClaudeCode 那么成熟 | 60% 到 70% |
| 终端 UI / SDK 状态生态 | 有 status snapshot、CLI/API/SDK/controller，但 UI 不如 ClaudeCode | 65% 到 75% |

最重要的结论：

- learning_agent 已经不是早期“几个浏览器工具”的玩具版。
- 它已经有比较完整的双轨浏览器 runtime。
- 但它还没有达到 ClaudeCode 那种生产级插件生态、成熟工具执行器、OS 级 computer-use 和终端 UI 的水平。

---

## 10. learning_agent 当前相对优势

learning_agent 已经具备的一些强项：

- 有明确的 acceptance_controller，可驱动真实可见终端并收集截图、事件和 result.json。
- 有独立 verifier，可验证 event log、debug log、screenshots、success markers、browser assertions。
- 有 browser runtime store，能把 browser run/action/observation/event 落盘。
- 有 flow checkpoint 和 replay，适合复杂网站多阶段任务。
- 有 `browser_type_secret`，适合敏感输入脱敏。
- 有真实浏览器视觉证据、PNG frames 和 GIF。
- 有 status snapshot，把 provider、browser runtime、recordings、harness 等状态聚合。
- 有明确的项目门禁：代码修改 + 自动化测试 + 真实可见终端验收。

这部分在“可审计、可复现、可验收”的 agent 开发方向上很重要。

---

## 11. learning_agent 与 ClaudeCode 的主要差距

### 11.1 生产级 Chrome 扩展安装和 native host 注册

ClaudeCode：

- 有扩展检测。
- 有 Windows native host 注册。
- 有浏览器 native messaging 路径。
- 有配对、OAuth、device id、bridge config。

learning_agent：

- 有 extension scaffold。
- 有 native host 协议和 manifest 生成。
- 但 `manifest_installer.py` 目前只生成 manifest，不写 Windows registry。
- 缺少成熟安装/卸载/重连/配对流程。

### 11.2 Chrome 发起 prompt / session sync

ClaudeCode：

- `usePromptsFromClaudeInChrome.tsx` 显示有从 Chrome extension 接收 prompt、图片、tabId 的设计。

learning_agent：

- 主要是 agent 主动控制浏览器。
- 还缺少浏览器插件主动把页面任务推回 agent 主循环的成熟机制。

### 11.3 专门浏览器工具表面

ClaudeCode：

- 有 `form_input`、`computer`、`shortcuts_list`、`shortcuts_execute`、`gif_creator` 等更高层工具。

learning_agent：

- 有通用 `browser_click`、`browser_type`、`browser_visual_locate`、`browser_flow_run`。
- 但缺少等价的高层表单输入策略、快捷键生态和插件内 computer 工具成熟度。

### 11.4 OS 级 computer-use

ClaudeCode：

- 源码中有 macOS computer-use，支持鼠标、键盘、截图、display、clipboard、app allowlist、Escape abort。

learning_agent：

- 主要是浏览器内自动化。
- 还没有成熟的 OS 级拟人鼠标键盘控制模块。

### 11.5 StreamingToolExecutor 级工具执行

ClaudeCode：

- 可以边流式收到工具调用，边排队执行。
- 并发安全工具可并行。
- 非安全工具串行。
- hook、权限、MCP auth、post-tool failure 都完整。

learning_agent：

- 有 BrowserActionExecutor。
- 有写动作串行、只读批处理、重试和分段事件。
- 但还没达到 ClaudeCode 全局工具执行器成熟度。

### 11.6 终端 UI / SDK 状态生态

ClaudeCode：

- 有 `/chrome` 菜单。
- 有 extension installed / enabled 状态。
- 有权限管理 UI。
- 有 View Tab 链接。
- 有 ComputerUseApproval UI。

learning_agent：

- 有 status snapshot、terminal renderer、SDK、HTTP、CLI。
- 但 UI 体验和用户操作闭环仍不如 ClaudeCode。

---

## 12. 后续建议路线

如果继续对齐 ClaudeCode 本地真实浏览器能力，建议优先顺序如下：

1. 生产级 Chrome extension 安装器。
   - 生成 manifest。
   - 写 Windows registry。
   - 检测安装状态。
   - 支持重连。
   - 支持卸载或禁用。

2. Chrome extension 配对和 session sync。
   - extension id。
   - device id。
   - paired device。
   - tab context push。
   - 从 Chrome 发起 prompt 到 learning_agent。

3. 高层浏览器工具。
   - `browser_form_input`。
   - `browser_shortcuts_list`。
   - `browser_shortcuts_execute`。
   - 更强的页面语义定位。

4. 全局 StreamingToolExecutor。
   - 不只浏览器工具，而是所有工具统一执行。
   - read/write 工具并发策略。
   - 权限 hook。
   - pre/post tool hook。
   - progress event。
   - result limit。

5. OS 级 Computer Use。
   - Windows 鼠标键盘。
   - 屏幕截图。
   - 应用窗口管理。
   - allowlist。
   - Escape abort。
   - 可见安全提示。

6. `/chrome` 类状态 UI。
   - extension 状态。
   - native host 状态。
   - active tab。
   - site permission。
   - pending command。
   - View Tab / screenshot / GIF 入口。

7. 真实端到端验收。
   - 必须用 `start_oauth_agent.bat`。
   - 必须可见终端。
   - 必须真实浏览器。
   - 必须 verifier 独立复验。

---

## 13. 当前文档和记忆文件

本窗口中已经更新过以下文件：

- `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\progress.md`
- `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\context.md`
- `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\bugs.md`
- `H:\codexworkplace\sofeware\OpenHarness-main\findings.md`

本次用户要求新增/保存的上下文文件：

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\zqbcontext.md`

---

## 14. 后续 agent 接手时的注意事项

后续任何 agent 接手本项目时，应先读：

1. `H:\codexworkplace\sofeware\OpenHarness-main\AGENTS.md`
2. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\zqbcontext.md`
3. `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\context.md`
4. `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\progress.md`
5. `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\bugs.md`
6. 需要 browser 对齐时读 `H:\codexworkplace\sofeware\OpenHarness-main\findings.md`

后续继续开发时，不要直接开改。应先：

- 查源码。
- 查测试。
- 查验收场景。
- 明确成功标准。
- 写阶段计划。
- 用自动化测试验证。
- 最后通过真实可见终端验收。

---

## 15. 当前状态一句话总结

learning_agent 已经具备比较完整的长任务 harness 和双轨真实浏览器 runtime 基础，浏览器能力大约达到 ClaudeCode 的 70% 到 78%；下一步真正拉近差距的重点不是继续修单个点击或输入，而是补齐生产级 Chrome 插件/native host 生态、全局流式工具执行器、OS 级 computer-use、Chrome 发起任务同步和更成熟的终端状态 UI。
