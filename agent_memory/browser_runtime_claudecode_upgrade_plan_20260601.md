# Browser Runtime ClaudeCode 对齐升级计划

日期：2026-06-01

## 目标

把 `learning_agent` 的真实浏览器能力，从“模型直接调用一批浏览器工具”升级成“可观察、可恢复、可回放、可验收、接入主循环的 Browser Runtime 子系统”。

这次计划参考 ClaudeCode 源码，但不把 README 或宣传文案当关键证据。ClaudeCode 能确认的成熟方向是：

1. 通过 `claude-in-chrome` MCP/Chrome 扩展桥接真实 Chrome。
2. 通过 skill 先加载浏览器能力，并要求先读取当前 tab 上下文。
3. 通过工具协议、权限模式、hook、流式执行器和状态 UI 管住工具执行。
4. 通过 Chrome 扩展管理站点级权限，决定哪些网站可以浏览、点击、输入。
5. 通过 console、network、GIF、tab link、MCP progress 等能力提升可观察性。

learning_agent 的升级目标不是复制 ClaudeCode 外部闭源包，而是在本项目内做一个可审计的等价设计，并在验收能力上争取超过 ClaudeCode：每个真实浏览器任务必须能留下可复现的 run、stage、event、artifact、replay 和 verifier 证据。

## ClaudeCode 源码证据

1. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\mcpServer.ts`
   - `createChromeContext()` 连接 Chrome bridge/native socket。
   - 支持 `CLAUDE_CHROME_PERMISSION_MODE=skip_all_permission_checks`。
   - 注释确认 ant-only 的 `browser_task` / `lightning_turn` 是浏览器任务子循环入口。

2. `D:\ClaudeCode-main\ClaudeCode-main\skills\bundled\claudeInChrome.ts`
   - `claude-in-chrome` 是一个 skill。
   - 允许工具来自 `@ant/claude-for-chrome-mcp` 的 `BROWSER_TOOLS`。
   - 激活后要求先调用 `tabs_context_mcp` 读取当前标签页上下文。

3. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\prompt.ts`
   - 规定 GIF 录制、console log 调试、避免 JS 弹窗、失败 2-3 次后停止并汇报、tab id 不能跨会话复用。

4. `D:\ClaudeCode-main\ClaudeCode-main\utils\claudeInChrome\toolRendering.tsx`
   - 可确认 Chrome 工具有 `navigate`、`read_page`、`find`、`form_input`、`computer`、`gif_creator`、`read_console_messages`、`read_network_requests`、`tabs_context_mcp`、`tabs_create_mcp` 等。

5. `D:\ClaudeCode-main\ClaudeCode-main\Tool.ts`
   - 工具协议包含输入校验、权限检查、hook 匹配、并发安全、进度、结果渲染、分组渲染、MCP metadata。

6. `D:\ClaudeCode-main\ClaudeCode-main\services\tools\toolOrchestration.ts`
   - 工具按并发安全性分批。
   - 只读/并发安全工具可并发，非并发安全工具串行。

7. `D:\ClaudeCode-main\ClaudeCode-main\services\tools\StreamingToolExecutor.ts`
   - 支持流式到达工具后立即执行。
   - 支持排队、互斥、进度、中断、兄弟工具失败取消。

8. `D:\ClaudeCode-main\ClaudeCode-main\services\mcp\client.ts`
   - Chrome MCP server 可以在进程内启动，减少额外进程成本。
   - MCP 工具调用会发送 started/completed progress。

9. `D:\ClaudeCode-main\ClaudeCode-main\commands\chrome\chrome.tsx`
   - UI 能显示 Chrome 集成状态、扩展是否安装、权限管理入口。
   - 站点级权限由 Chrome 扩展管理，决定 Claude 可浏览、点击、输入的网站。

10. `D:\ClaudeCode-main\ClaudeCode-main\services\api\claude.ts`
    - Chrome 工具搜索说明会按工具实际存在情况注入系统提示。

## learning_agent 当前基线

已经具备：

1. `learning_agent/browser_automation_mcp_server.py`
   - 有 `browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_type_secret`、`browser_press_key`、`browser_wait`、`browser_screenshot`、`browser_tabs`、`browser_console`、`browser_network`、`browser_recover_page`、`browser_visual_locate`、`browser_flow_run`、`browser_replay`、`browser_plugin_status`、`browser_connect_real_chrome` 等工具。

2. `learning_agent/browser_real_chrome.py`
   - 有真实 Chrome profile 检测、CDP 连接、敏感脚本拦截、审计日志。

3. `learning_agent/core/agent.py`
   - `run_events()` 已接入事件流、工具池、harness/session/status 部分能力。

4. `learning_agent/acceptance/verifier.py`
   - 已有独立 verifier，可复验 result、events、debug log、截图、最终文本和权限次数。

5. 真实验收证据
   - `learning_agent/acceptance_controller/runs/real_chrome_leishen_login_content-20260601_075721/result.json`
   - 已证明真实 Chrome 登录、密钥输入、截图、最终页面内容读取可以跑通。

主要缺口：

1. 浏览器能力仍集中在一个超大 MCP server 文件里，缺少独立 Browser Runtime 模块边界。
2. 浏览器任务没有完整状态机，stage/checkpoint/resume 与 harness 还没有一体化到浏览器任务层。
3. locator 还不够成熟，缺少 DOM、可访问性、视觉坐标、截图 OCR、候选评分的统一选择器。
4. 页面失败恢复目前偏工具级，缺少失败分类、恢复策略、重试预算和恢复证据。
5. 登录态安全已有基本护栏，但还没有 secret vault、站点权限策略、敏感输出策略的统一协议。
6. 回放已有雏形，但还没有和 verifier、checkpoint、artifact、stage resume 形成闭环。
7. 状态生态已有全局 status，但缺少浏览器专用 `/browser`、browser run/stage/event/artifact/status API。

## 总体架构

目标架构分成 8 层：

1. Browser Protocol
   - 定义浏览器 run、session、tab、action、observation、locator、recovery、assertion 的稳定数据结构。

2. Browser Runtime Store
   - 把浏览器任务状态持久化到 `learning_agent/memory/browser_runtime/`，不要只存在内存里。

3. Browser Controller
   - 统一管理独立 Chromium、真实 Chrome CDP、tab registry、page lifecycle。

4. Observation Engine
   - 统一产出 DOM 快照、可访问性摘要、可见文本、截图、console、network、视觉候选。

5. Locator Engine
   - 根据 selector、文本、role、label、坐标、视觉候选和历史 action 选择最可信的元素。

6. Action Executor
   - 执行点击、输入、按键、导航、等待、上传、下载、表单提交，并发控制和流式进度都在这里。

7. Recovery + Replay + Verifier
   - 分类失败，按策略恢复；写 action log；支持 dry-run replay；最终由 verifier 复验。

8. UI/SDK/CLI/Status
   - 让终端、controller、harness CLI、HTTP bridge、SDK、模型工具都能看见浏览器任务状态。

## 阶段 0：建立执行护栏和基线

产物：

1. 保留本计划文件。
2. 新建或更新 `task_plan.md`、`findings.md`、`progress.md` 时，必须记录当前阶段。
3. 记录 ClaudeCode 源码证据和 learning_agent 当前能力边界。

文件：

1. `agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`
2. `docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`
3. `learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`
4. `agent_memory/progress.md`

验收：

1. 三份计划文件内容一致。
2. 所有路径使用 `H:\codexworkplace\sofeware\OpenHarness-main` 作为 learning_agent 项目根路径。
3. 只在引用 ClaudeCode 源码时使用 `D:\ClaudeCode-main\ClaudeCode-main`。

## 阶段 1：拆出 Browser Runtime 协议层

目标：

把浏览器任务从“工具函数散落参数”升级为“稳定协议对象”。

建议新增文件：

1. `learning_agent/browser/runtime_models.py`
   - `BrowserRun`
   - `BrowserSession`
   - `BrowserTab`
   - `BrowserAction`
   - `BrowserObservation`
   - `BrowserLocator`
   - `BrowserRecoveryAttempt`
   - `BrowserAssertion`
   - `BrowserCapabilityReport`

2. `learning_agent/tests/test_browser_runtime_models.py`

成功标准：

1. 每个浏览器动作都有 `action_id`、`run_id`、`stage_id`、`tool_name`、`arguments_redacted`、`started_at`、`finished_at`、`status`、`error_type`。
2. 每个 observation 都能记录当前 URL、title、visible text 摘要、screenshot path、console/network 摘要。
3. 所有模型都能 JSON round-trip。
4. 单元测试覆盖正常序列化、敏感参数脱敏、旧 action log 兼容读取。

## 阶段 2：Browser Runtime Store 和 harness 事件接入

目标：

浏览器 run/stage/action/event 不能只在 MCP server 内存里存在，必须持久化并接入 harness event log。

建议新增文件：

1. `learning_agent/browser/runtime_store.py`
2. `learning_agent/browser/runtime_events.py`
3. `learning_agent/tests/test_browser_runtime_store.py`

建议修改：

1. `learning_agent/browser_automation_mcp_server.py`
   - 工具调用开始和结束时写 Browser Runtime Store。
   - 后续阶段逐步把逻辑迁移出去。

2. `learning_agent/core/agent.py`
   - 当检测到浏览器任务时，在主 run 中挂载 browser run id。

成功标准：

1. 每次真实浏览器任务自动创建 `learning_agent/memory/browser_runtime/runs/<browser_run_id>.json`。
2. 每次工具调用追加 `learning_agent/memory/browser_runtime/events/<browser_run_id>.jsonl`。
3. harness event log 能看到 `browser_run_created`、`browser_action_started`、`browser_action_completed`、`browser_observation_recorded`。
4. 进程中断后，能从 browser run 文件知道上次停在第几步。

## 阶段 3：浏览器 session manager 对齐 ClaudeCode Chrome bridge 思路

目标：

把真实 Chrome、独立 Chromium、tab registry、profile scope、site grant 从零散逻辑升级为 session manager。

建议新增文件：

1. `learning_agent/browser/session_manager.py`
2. `learning_agent/browser/tab_registry.py`
3. `learning_agent/tests/test_browser_session_manager.py`

建议修改：

1. `learning_agent/browser_real_chrome.py`
2. `learning_agent/browser_automation_mcp_server.py`

成功标准：

1. 支持 `independent_chromium`、`visible_chromium`、`real_chrome_cdp` 三种 session mode。
2. tab id 不允许跨 browser run 复用。
3. 连接真实 Chrome 时记录 profile scope，但不记录本机完整敏感路径。
4. session manager 能恢复当前 tabs、当前 active tab、session health。
5. `browser_plugin_status` 或新的 `browser_status` 能显示 session mode、connected、visible、headless、tab count。

## 阶段 4：Observation Engine

目标：

让 agent “看见页面”不只靠一段 DOM 文本，而是 DOM + 可见文本 + 截图 + console + network + 元素框的统一 observation。

建议新增文件：

1. `learning_agent/browser/observation.py`
2. `learning_agent/browser/screenshot_index.py`
3. `learning_agent/tests/test_browser_observation.py`

建议修改：

1. `browser_snapshot`
2. `browser_screenshot`
3. `browser_console`
4. `browser_network`

成功标准：

1. `browser_snapshot` 返回结构化元素列表：`element_id`、`role`、`label`、`text`、`selector`、`box`、`center_x`、`center_y`、`visible`。
2. observation 默认限制输出长度，长文本进入 artifact 文件。
3. 每次截图都能关联 browser run、stage、action。
4. console/network 默认脱敏 token、cookie、authorization。
5. verifier 能读取 observation artifact 做复验。

## 阶段 5：Locator Engine

目标：

解决换一个网站就失败的问题。模型给高层意图，locator 负责找最可信的元素。

建议新增文件：

1. `learning_agent/browser/locator.py`
2. `learning_agent/tests/test_browser_locator.py`

Locator 输入：

1. `selector`
2. `text`
3. `role`
4. `label`
5. `placeholder`
6. `near_text`
7. `element_id`
8. `coordinate`
9. `visual_query`

Locator 输出：

1. 候选列表。
2. 每个候选包含 score、reason、selector、box、center。
3. 最终选择包含 `confidence`，低于阈值时不自动点击，而是要求观察或恢复。

成功标准：

1. 同一按钮即使 selector 改变，只要文本/role/box 还在，就能定位。
2. 输入框可通过 placeholder、label、附近文本定位。
3. 对多个同名按钮，必须给出候选并说明选择原因。
4. 坐标点击必须记录截图证据和候选来源。

## 阶段 6：Action Executor 和流式工具执行

目标：

对齐 ClaudeCode `StreamingToolExecutor` 的成熟方向：浏览器动作要有排队、互斥、进度、中断、失败取消。

建议新增文件：

1. `learning_agent/browser/action_executor.py`
2. `learning_agent/browser/action_policy.py`
3. `learning_agent/tests/test_browser_action_executor.py`

建议修改：

1. `learning_agent/tools/orchestrator.py`
2. `learning_agent/browser_automation_mcp_server.py`

成功标准：

1. 浏览器写操作默认串行：click/type/press/upload/download/evaluate/submit。
2. 只读观察操作可在安全条件下并发：snapshot/console/network/status。
3. 每个 action 发出 started/progress/completed/failed 事件。
4. 用户中断时，正在执行的浏览器动作能写入 `interrupted` 状态。
5. action result 自动回灌到下一轮模型上下文，而不是只打印在工具层。

## 阶段 7：Recovery Manager

目标：

把“页面失败恢复”从单个工具升级成失败分类 + 恢复策略 + 重试预算。

建议新增文件：

1. `learning_agent/browser/recovery.py`
2. `learning_agent/tests/test_browser_recovery.py`

失败分类：

1. `page_closed`
2. `context_closed`
3. `navigation_timeout`
4. `network_idle_timeout`
5. `locator_not_found`
6. `click_intercepted`
7. `stale_element`
8. `download_failed`
9. `chrome_disconnected`
10. `permission_denied`

恢复策略：

1. refresh 当前页。
2. back/forward。
3. 重新读取 tabs context。
4. 重新打开 URL。
5. 新建 tab。
6. 重新连接 CDP。
7. 停止并要求用户干预。

成功标准：

1. 每次失败都记录 error_type 和 recovery_attempt。
2. 同一个动作最多按策略重试，不能无限循环。
3. 恢复成功后必须重新 observation。
4. 恢复失败时最终回答要说清楚失败在哪一步、已尝试什么。

## 阶段 8：Browser Flow Runtime

目标：

把 `browser_flow_run` 从“顺序调用工具列表”升级成“可 checkpoint、可 resume、可阶段验收的浏览器流程运行器”。

建议新增文件：

1. `learning_agent/browser/flow_runtime.py`
2. `learning_agent/browser/flow_schema.py`
3. `learning_agent/tests/test_browser_flow_runtime.py`

建议修改：

1. `browser_flow_run`
2. `learning_agent/acceptance_controller/scenarios/*.json`

成功标准：

1. flow 支持 `stage_id`、`name`、`action`、`expect`、`on_failure`、`retry`。
2. 每完成一个 stage 就写 checkpoint。
3. 进程中断后恢复时，不重跑已完成 stage。
4. stage 验收失败时不会谎报 flow completed。
5. flow 最终能输出可读 summary 和机器可读 JSON。

## 阶段 9：Secret Vault 和登录态安全

目标：

真实登录态下，agent 可以帮用户填表，但不能泄露或回放敏感信息。

建议新增文件：

1. `learning_agent/browser/secret_vault.py`
2. `learning_agent/browser/site_permissions.py`
3. `learning_agent/tests/test_browser_secret_vault.py`

成功标准：

1. `browser_type_secret` 只能读取允许前缀的环境变量或 vault 引用。
2. action log 中只保存 secret ref，不保存明文。
3. replay 默认跳过 secret 输入。
4. console/network/action/result/debug log 都要脱敏。
5. cookie/localStorage/sessionStorage 默认不可读；如未来允许，必须显式权限、显式原因、显式脱敏。
6. 真实 Chrome 下的 submit 行为必须区分普通按钮和高风险提交。

## 阶段 10：Replay + Acceptance Verifier 2.0

目标：

让真实浏览器任务可审计、可复现、可证明，而不是“看起来跑过”。

建议新增文件：

1. `learning_agent/browser/replay.py`
2. `learning_agent/browser/assertions.py`
3. `learning_agent/tests/test_browser_assertions.py`

建议修改：

1. `learning_agent/acceptance/verifier.py`
2. `learning_agent/acceptance_controller/controller.ps1`

断言类型：

1. URL contains/exact/regex。
2. title contains/exact/regex。
3. visible text contains/regex。
4. selector visible/enabled/value。
5. screenshot exists。
6. console no severe error。
7. network request happened。
8. action sequence includes。
9. secret not leaked。
10. permission count limit。

成功标准：

1. 每个浏览器 acceptance scenario 可以声明 browser assertions。
2. verifier 不依赖 README，不依赖最终回答自夸。
3. verifier 能读取 browser runtime run、events、artifacts、action log。
4. 如果 verifier 不通过，不能声明开发完成。

## 阶段 11：浏览器状态生态

目标：

对齐 ClaudeCode 的 UI/SDK 状态生态，但更适合 learning_agent 的 harness。

建议新增或修改：

1. `learning_agent/harness/cli.py`
   - 增加 `browser-runs`、`browser-events`、`browser-artifacts`。

2. `learning_agent/runtime/status_snapshot.py`
   - 增加 `browser` section。

3. `learning_agent/sdk/status.py`
   - 增加 `get_browser_runs()`、`get_browser_events()`。

4. HTTP bridge
   - 增加 `/browser/runs`、`/browser/events`、`/browser/artifacts` 或 `/v1/browser/...`。

5. 模型工具
   - 增加 `browser_status`、`browser_event_tail`、`browser_artifacts`。

成功标准：

1. 用户能用 CLI 看见 browser run/stage/action/verifier 状态。
2. 其他 agent 能用 SDK/API 读到浏览器任务证据。
3. 真实终端 `/status` 能显示当前浏览器任务状态。
4. 状态来自同一个 store，不出现三套旁路系统。

## 阶段 12：真实可见终端和真实浏览器验收矩阵

目标：

按用户 AGENTS.md 规则，最终必须通过 `start_oauth_agent.bat` 真实可见终端验收。

自动化测试：

1. `python -m py_compile` 覆盖新增和修改文件。
2. `python -m unittest learning_agent.tests.test_browser_runtime_models`
3. `python -m unittest learning_agent.tests.test_browser_runtime_store`
4. `python -m unittest learning_agent.tests.test_browser_session_manager`
5. `python -m unittest learning_agent.tests.test_browser_observation`
6. `python -m unittest learning_agent.tests.test_browser_locator`
7. `python -m unittest learning_agent.tests.test_browser_action_executor`
8. `python -m unittest learning_agent.tests.test_browser_recovery`
9. `python -m unittest learning_agent.tests.test_browser_flow_runtime`
10. `python -m unittest learning_agent.tests.test_browser_secret_vault`
11. `python -m unittest learning_agent.tests.test_browser_assertions`
12. `python -m unittest discover learning_agent.tests`

真实可见终端验收：

1. 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`。
2. 通过 controller 或用户肉眼操作，在真实终端输入测试 prompt。
3. 必须观察真实终端输出。
4. 必须观察真实浏览器窗口。
5. 必须运行独立 verifier 复验。

建议验收场景：

1. 公网页面恢复
   - 打开一个公共页面，故意触发超时或 page close，确认 recovery event 和最终恢复。

2. 视觉定位
   - 打开静态测试页面，要求按可见文字和坐标点击。

3. 复杂流程
   - 多阶段打开页面、输入、点击、等待、截图、断言。

4. 真实 Chrome 登录态
   - 使用 `browser_type_secret` 从环境变量输入，不回显明文。

5. 回放和 verifier
   - 先 dry-run replay，再执行安全 replay，最后 verifier 检查 action sequence。

6. 状态生态
   - 终端 `/status`、harness CLI、SDK/API 都能看到同一个 browser run。

完成判定：

1. 代码修改完成。
2. 自动化测试通过。
3. 真实可见终端交互验收通过。
4. 真实浏览器窗口肉眼可见。
5. 独立 verifier 通过。
6. 所有修改备份到 `learning_agent/test/<本次任务目录>/`。

如果当前 Codex 环境无法打开、观察或向用户本地可见终端窗口输入内容，最终必须明确说明：

`真实可见终端交互验收未完成，不能声明开发完成。`

## 停止条件

1. ClaudeCode 源码不能确认的能力，不写成“ClaudeCode 已具备”，只能写成“外部包或扩展可能具备，但当前源码无法确认”。
2. 任意实现如果会保存明文密码、token、cookie、authorization、localStorage、sessionStorage，必须停止并改为脱敏或拒绝。
3. 任意阶段如果只做了单测，没有接入 `LearningAgent.run_events()`、harness event log、browser runtime store，不能算完成。
4. 任意阶段如果无法通过真实可见终端验收，不能声明开发完成。

## 推荐执行顺序

1. 先做阶段 1-2，把浏览器任务状态持久化和事件接入立住。
2. 再做阶段 3-5，把 session、observation、locator 从大文件拆出来。
3. 然后做阶段 6-8，把执行、恢复、flow runtime 变成可恢复状态机。
4. 接着做阶段 9-11，把安全、回放、verifier、状态生态闭环补齐。
5. 最后做阶段 12 的真实验收矩阵，所有验收通过后才能说完成。

## 面向小白的解释

现在 learning_agent 像是有一堆浏览器按钮：打开、点击、输入、截图。能用，但遇到复杂网站就容易靠运气。

升级后要变成一个“浏览器驾驶系统”：

1. 它知道自己开的是哪个浏览器、哪个标签页。
2. 它每点一步都会记账。
3. 页面坏了会知道怎么恢复。
4. 输入密码不会写进日志。
5. 失败后能从上次成功的阶段继续。
6. 其他 agent 能查它到底做了什么。
7. 最后能用 verifier 证明它真的完成了任务，而不是嘴上说完成。
