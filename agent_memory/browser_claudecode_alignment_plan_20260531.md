# learning_agent 真实浏览器能力对齐 ClaudeCode 计划

日期：2026-05-31

## 任务目标

把 `learning_agent` 的真实浏览器能力从“能打开、点击、输入、截图、读取快照”的基础 Playwright/MCP 工具，升级为更接近 ClaudeCode 浏览器生态的可恢复、可审计、可回放、可控权限、可处理复杂网站流程的浏览器执行层。

## 关键结论边界

1. 本计划只把源码中能确认的 ClaudeCode 能力作为对齐目标，不把 README、宣传文字或猜测当关键证据。
2. ClaudeCode 的真实浏览器能力主要由 `Claude in Chrome` 扩展、Chrome MCP 工具、computer-use MCP、权限 UI、消息队列、流式工具执行、插件系统和会话恢复系统共同支撑。
3. `learning_agent` 已经有真实 Chrome 连接、Playwright 浏览器工具、敏感脚本阻断、安全审计和公开搜索 harness，但浏览器任务本身还缺少更强的恢复、视觉定位、复杂流程、回放和权限生态。

## ClaudeCode 源码证据

1. `D:\ClaudeCode-main\ClaudeCode-main\commands\chrome\chrome.tsx`
   - 证明 ClaudeCode 有 `Claude in Chrome` 扩展入口、安装状态、站点级权限管理、`--chrome` 和 `--no-chrome` 运行模式提示。
2. `D:\ClaudeCode-main\ClaudeCode-main\skills\bundled\claudeInChrome.ts`
   - 证明 ClaudeCode 把 Chrome 浏览器自动化能力作为 skill 激活，并通过 `mcp__claude-in-chrome__tabs_context_mcp` 先读取当前浏览器 tab 上下文。
3. `D:\ClaudeCode-main\ClaudeCode-main\hooks\usePromptsFromClaudeInChrome.tsx`
   - 证明 ClaudeCode 可以从 Chrome 扩展接收 prompt、图片、tabId，并把浏览器侧请求排入主消息队列。
4. `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\mcpServer.ts`
   - 证明 ClaudeCode 有 computer-use MCP 层，可用于坐标、屏幕和桌面级交互。
5. `D:\ClaudeCode-main\ClaudeCode-main\components\permissions\ComputerUseApproval\ComputerUseApproval.tsx`
   - 证明 ClaudeCode 有面向用户的 computer-use 权限审批、应用允许列表和系统权限恢复提示。
6. `D:\ClaudeCode-main\ClaudeCode-main\services\tools\StreamingToolExecutor.ts`
   - 证明 ClaudeCode 工具执行支持流式、并发安全、非并发互斥和中断处理。
7. `D:\ClaudeCode-main\ClaudeCode-main\services\tools\toolExecution.ts`
   - 证明 ClaudeCode 工具执行有权限决策、hook、MCP 错误状态、工具结果处理。
8. `D:\ClaudeCode-main\ClaudeCode-main\utils\messageQueueManager.ts`
   - 证明 ClaudeCode 把用户输入、命令、任务通知和权限事件统一放进消息队列。
9. `D:\ClaudeCode-main\ClaudeCode-main\utils\conversationRecovery.ts`
   - 证明 ClaudeCode 有会话反序列化、恢复、过滤未完成工具调用、恢复技能和 hooks 的机制。
10. `D:\ClaudeCode-main\ClaudeCode-main\plugins\builtinPlugins.ts`
    - 证明 ClaudeCode 有插件启用、工具允许、hooks、MCP server 配置和插件命令生态。

## learning_agent 当前源码能力

1. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\browser_automation_mcp_server.py`
   - 已有 `browser_open`、`browser_snapshot`、`browser_click`、`browser_type`、`browser_wait`、`browser_screenshot`、`browser_tabs`、`browser_console`、`browser_network`、`browser_evaluate`、真实 Chrome 连接和 profile 状态工具。
2. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\browser_real_chrome.py`
   - 已有真实 Chrome profile 路径校验、CDP 端点校验、敏感脚本阻断和审计日志。
3. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\browser\harness.py`
   - 已有公开搜索场景的真实浏览器任务提示词注入。
4. `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\browser\permissions.py`
   - 已有部分公开 Google 搜索任务的浏览器权限自动批准逻辑。

## 主要缺口

1. 页面失败恢复
   - 当前只有浏览器连接级健康检查和打开失败时的清理，没有统一的页面 reload、reopen、back、new page 恢复工具，也没有把恢复动作写入浏览器任务轨迹。
2. 视觉定位
   - 当前 DOM 快照主要返回文本、selector、label，不返回稳定边框、中心点、截图关联信息，也没有坐标点击和视觉候选定位。
3. 复杂网站流程
   - 当前 harness 主要面向公开搜索，没有可持久化的多阶段浏览器流程、阶段状态、失败后续跑和动作轨迹。
4. 登录态安全
   - 当前能阻断敏感 JS 和审计，但没有 ClaudeCode 那种站点级授权、当前 tab 权限上下文、敏感输入默认不回放、真实 profile 下更严格的动作记录策略。
5. 插件兼容
   - 当前有 skill 文件夹和 MCP 工具，但没有浏览器插件兼容状态、工具声明检查、权限声明检查和兼容性报告。
6. 异常重试
   - 当前各工具有局部 try/except，但没有统一的浏览器工具重试、错误分类、退避、恢复建议和审计。
7. 任务回放
   - 当前没有浏览器动作 JSONL 轨迹和安全回放工具，无法复现一次浏览器任务每一步做了什么。

## 执行阶段

阶段 1：建立证据和计划文档
- 产物：本文件、根目录任务计划、agent_memory 进度记录、备份文档。
- 验收：每个结论都能指向源码文件。

阶段 2：先写失败测试
- 产物：新增或扩展浏览器测试，覆盖视觉元素边框、坐标点击、失败恢复、统一重试、安全回放、插件兼容状态。
- 验收：测试在实现前能暴露当前缺口。

阶段 3：浏览器动作轨迹和安全回放
- 产物：浏览器动作 JSONL 记录器、`browser_replay` 工具、安全参数脱敏和真实 Chrome 敏感输入默认不回放。
- 验收：能查看和安全回放非敏感浏览器任务。

阶段 4：页面失败恢复和异常重试
- 产物：统一浏览器工具执行包装器、可配置重试、失败分类、`browser_recover_page` 工具。
- 验收：页面关闭、导航超时、临时失败时能恢复或给出明确恢复建议。

阶段 5：视觉定位和坐标操作
- 产物：快照元素返回 bounding box 和中心点、`browser_visual_locate` 工具、`browser_click` 支持坐标点击。
- 验收：无需稳定 selector 时，也能根据文字、标签、可见区域找到点击点。

阶段 6：复杂网站流程执行器
- 产物：`browser_flow_run` 工具，支持阶段化动作、阶段结果、失败位置和动作轨迹。
- 验收：多步浏览器流程能按阶段执行，失败时能定位到具体阶段。

阶段 7：登录态安全和权限边界
- 产物：真实 profile 下站点级授权检查、敏感字段脱敏、真实 Chrome 回放限制、状态报告。
- 验收：不会默认读取 cookie/token/localStorage，不会默认记录真实 profile 敏感输入。

阶段 8：插件兼容状态
- 产物：`browser_plugin_status` 工具或状态字段，报告浏览器工具、权限、安全、回放、视觉定位的兼容性。
- 验收：其他 agent 能用结构化输出判断当前浏览器能力是否可用。

阶段 9：文档备份、自动化验证和真实终端验收
- 产物：修改代码备份到 `learning_agent/test/`，运行 pytest/py_compile，并尝试 `start_oauth_agent.bat` 真实可见终端验收。
- 验收：代码修改完成、自动化测试通过、真实可见终端交互通过后，才允许声明任务完成。

## 停止条件

1. 如果 ClaudeCode 源码证据无法确认某项能力，只标为“无法从源码确认”，不把它作为已对齐结论。
2. 如果真实可见终端无法由当前环境打开、输入和观察，最终必须明确说明“真实可见终端交互验收未完成，不能声明开发完成”。
3. 如果实现会读取、保存或回放真实登录态敏感数据，必须停止并改成默认脱敏或拒绝。
