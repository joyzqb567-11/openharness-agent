新增代码+ComputerUseClaudeCode源码对齐：本记录保存 2026-06-06 对 ClaudeCode 与 OpenHarness Computer Use 源码对比结论；如果没有这个记录，后续压缩上下文后容易忘记“截图必须作为模型可见 image block 回灌”这一核心差异。

新增代码+ComputerUseClaudeCode源码对齐：已读取 ClaudeCode 源码文件 D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\setup.ts、mcpServer.ts、wrapper.tsx、executor.ts、hostAdapter.ts、gates.ts、drainRunLoop.ts，以及 services\tools\toolExecution.ts、toolOrchestration.ts。

新增代码+ComputerUseClaudeCode源码对齐：ClaudeCode 通过 buildComputerUseTools 注册 mcp__computer-use__* 工具名，并在 wrapper.tsx 中把 MCP image content 转成 Anthropic API image block；如果没有这层，模型只能看到截图路径而看不到真实屏幕像素。

新增代码+ComputerUseClaudeCode源码对齐：OpenHarness 当前 learning_agent/core/agent.py 的 _tool_result_to_dict 只把工具输出作为字符串 content 回灌，computer_use/evidence.py 的 image_result 目前是文本路径协议，不是模型主循环可直接视觉理解的 image block。

新增代码+ComputerUseClaudeCode源码对齐：真实验收暴露的问题不是单纯鼠标动作缺失，而是目标应用生命周期与视觉回灌不成熟；模型会选择已有 Paint 窗口并操作，不能证明它按用户任务启动了本机画图软件。

新增代码+ComputerUseClaudeCode源码对齐：下一步治本方向应是先改主循环多模态 tool_result 回灌和 Computer Use 工具协议，而不是继续为具体图形添加硬编码 planner。
