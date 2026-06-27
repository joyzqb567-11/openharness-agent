import { GUI_V2_TOKEN_HEADER } from "./guiTypes"; // 修改代码+DesktopRuntimePanelsClient：复用 V2 token header 常量；如果没有这行，client 会继续硬编码协议字段。
import type { GuiV2ErrorResponse } from "./guiTypes"; // 修改代码+DesktopRuntimePanelsClient：导入结构化错误响应类型；如果没有这行，错误解析会退回不透明对象。
import type { CustomProviderRequest, GuiProviderSettingsPayload, ProviderAuthAttemptPayload, ProviderConnectionProbePayload } from "./guiProviderTypes"; // 修改代码+OpenAIConnectClient：导入 Provider Settings 和 auth-attempt 类型；如果没有这行，连接向导轮询只能返回不透明对象。

export type GuiBootstrapPayload = { // 修改代码+DesktopRuntimePanelsClient：定义 bootstrap 响应类型；如果没有这段，前端首屏数据会变成不透明对象。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记 bridge 成功响应；如果没有这行，调用方无法用类型判断成功形状。
  workspace: string; // 修改代码+DesktopRuntimePanelsClient：保存当前项目路径；如果没有这行，侧栏无法显示当前工作区。
  app: { // 修改代码+DesktopRuntimePanelsClient：保存后端应用元信息；如果没有这段，前端无法检查协议版本。
    name: string; // 修改代码+DesktopRuntimePanelsClient：保存应用名称；如果没有这行，首屏标题无法来自后端事实。
    schema_version: number; // 修改代码+DesktopRuntimePanelsClient：保存协议版本；如果没有这行，后续兼容判断没有依据。
  }; // 修改代码+DesktopRuntimePanelsClient：app 元信息结束；如果没有这行，类型语法不完整。
  snapshot: Record<string, unknown>; // 修改代码+DesktopRuntimePanelsClient：保存统一状态快照；如果没有这行，状态面板没有启动数据。
  feature_flags: Record<string, boolean>; // 修改代码+DesktopRuntimePanelsClient：保存后端能力开关；如果没有这行，UI 无法按能力启用功能。
}; // 修改代码+DesktopRuntimePanelsClient：bootstrap 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiEventPayload = { // 修改代码+DesktopRuntimePanelsClient：定义事件轮询响应类型；如果没有这段，工具卡片无法稳定消费事件。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记事件响应成功；如果没有这行，调用方无法区分错误响应。
  events: Array<Record<string, unknown>>; // 修改代码+DesktopRuntimePanelsClient：保存事件列表；如果没有这行，状态时间线没有数据来源。
  since_sequence: number | null; // 修改代码+DesktopRuntimePanelsClient：保存本次请求游标；如果没有这行，前端无法确认轮询边界。
  limit: number; // 修改代码+DesktopRuntimePanelsClient：保存本次请求限制；如果没有这行，前端无法调试事件批量大小。
}; // 修改代码+DesktopRuntimePanelsClient：事件 payload 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiSessionsPayload = { // 修改代码+DesktopRuntimePanelsClient：定义 sessions 响应类型；如果没有这段，侧栏拿到的会话列表会是不透明对象。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记 sessions 请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version?: number; // 新增代码+DesktopGUISessionSearchClient：保存 V2 sessions schema 版本；如果没有这行，前端无法识别后端会话合同版本。
  sessions: Array<Record<string, unknown> | string>; // 修改代码+DesktopRuntimePanelsClient：保存最近会话列表；如果没有这行，侧栏没有真实数据来源。
  archived_count?: number; // 新增代码+DesktopGUISessionSearchClient：保存归档会话计数；如果没有这行，侧栏归档入口只能显示假数字。
  resume: Record<string, unknown>; // 修改代码+DesktopRuntimePanelsClient：保存恢复状态摘要；如果没有这行，侧栏无法显示恢复风险或最近恢复状态。
}; // 修改代码+DesktopRuntimePanelsClient：sessions 响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiSearchPayload = { // 新增代码+DesktopGUISessionSearchClient：定义 V2 搜索响应类型；如果没有这段，搜索面板只能接收不透明对象。
  ok: true; // 新增代码+DesktopGUISessionSearchClient：标记搜索请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUISessionSearchClient：保存搜索 schema 版本；如果没有这行，前端无法识别搜索合同版本。
  query: string; // 新增代码+DesktopGUISessionSearchClient：保存后端实际搜索词；如果没有这行，面板无法确认当前结果对应哪个输入。
  results: Array<Record<string, unknown>>; // 新增代码+DesktopGUISessionSearchClient：保存搜索结果列表；如果没有这行，搜索面板没有可点击数据来源。
}; // 新增代码+DesktopGUISessionSearchClient：V2 搜索响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiSessionMutationPayload = { // 新增代码+DesktopGUISessionSearchClient：定义会话改名/归档响应类型；如果没有这段，前端写入操作拿不到稳定结果。
  ok: true; // 新增代码+DesktopGUISessionSearchClient：标记写入请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUISessionSearchClient：保存写入响应 schema 版本；如果没有这行，前端无法识别合同版本。
  session: Record<string, unknown>; // 新增代码+DesktopGUISessionSearchClient：保存更新后的会话条目；如果没有这行，前端需要自己猜测新状态。
  archived?: boolean; // 新增代码+DesktopGUISessionSearchClient：保存归档结果；如果没有这行，archive 调用方无法确认是否隐藏。
}; // 新增代码+DesktopGUISessionSearchClient：会话写入响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiBrowserProvidersPayload = { // 修改代码+DesktopRuntimePanelsClient：定义旧浏览器 provider 响应类型；如果没有这段，旧面板调用缺少类型兜底。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记浏览器 provider 请求成功；如果没有这行，调用方无法区分错误响应。
  provider_status: Record<string, unknown>; // 修改代码+DesktopRuntimePanelsClient：保存浏览器 provider 健康状态；如果没有这行，BrowserPanel 没有旧数据来源。
  browser: Record<string, unknown>; // 修改代码+DesktopRuntimePanelsClient：保存浏览器 runtime 总览；如果没有这行，后续兼容面板无法扩展。
}; // 修改代码+DesktopRuntimePanelsClient：浏览器 provider 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiRuntimePanelsPayload = { // 新增代码+DesktopRuntimePanelsClient：定义 V2 runtime panels 响应类型；如果没有这段，浏览器和 Computer Use 面板只能靠散落接口拼数据。
  ok: true; // 新增代码+DesktopRuntimePanelsClient：标记 V2 面板请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopRuntimePanelsClient：保存面板 payload 版本；如果没有这行，后续演进没有兼容依据。
  browser: Record<string, unknown>; // 新增代码+DesktopRuntimePanelsClient：保存浏览器面板数据；如果没有这行，BrowserPanel 拿不到 V2 状态。
  computer_use: Record<string, unknown>; // 新增代码+DesktopRuntimePanelsClient：保存 Computer Use 面板数据；如果没有这行，锁和急停状态没有来源。
  permissions: Record<string, unknown>; // 新增代码+DesktopRuntimePanelsClient：保存权限摘要数据；如果没有这行，Computer Use 面板无法显示待处理权限。
  status_degraded: boolean; // 新增代码+DesktopRuntimePanelsClient：保存整体降级状态；如果没有这行，前端无法判断状态是否可信。
  safe_error: string; // 新增代码+DesktopRuntimePanelsClient：保存安全错误文案；如果没有这行，降级时可能暴露原始异常。
}; // 新增代码+DesktopRuntimePanelsClient：runtime panels 类型结束；如果没有这行，TypeScript 类型语法不完整。
export type GuiToolchainPayload = { // 新增代码+DesktopGUIToolchainClient：定义 V2 工具链清单响应类型；如果没有这段，前端只能把工具链当成不透明对象。
  ok: true; // 新增代码+DesktopGUIToolchainClient：标记工具链请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUIToolchainClient：保存工具链协议版本；如果没有这行，后续合同演进没有兼容依据。
  workspace: string; // 新增代码+DesktopGUIToolchainClient：保存后端工作区路径；如果没有这行，清单来源无法定位到当前项目。
  generated_at: string; // 新增代码+DesktopGUIToolchainClient：保存清单生成时间；如果没有这行，用户无法判断清单是否来自最新后端事实。
  tool_count: number; // 新增代码+DesktopGUIToolchainClient：保存工具总数；如果没有这行，GUI 无法展示接入规模。
  group_count: number; // 新增代码+DesktopGUIToolchainClient：保存分组总数；如果没有这行，GUI 无法展示能力域覆盖。
  groups: Array<Record<string, unknown>>; // 新增代码+DesktopGUIToolchainClient：保存分组和工具列表；如果没有这行，面板没有主体清单。
  status_degraded: boolean; // 新增代码+DesktopGUIToolchainClient：保存工具链读取是否降级；如果没有这行，前端无法提示清单可信度。
  safe_error: string; // 新增代码+DesktopGUIToolchainClient：保存安全错误文案；如果没有这行，异常时可能暴露原始错误。
}; // 新增代码+DesktopGUIToolchainClient：工具链清单类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiMcpInventoryPayload = { // 新增代码+DesktopGUIMcpClient：定义 MCP 管理总览响应类型；如果没有这段，前端只能把 MCP 状态当成不透明对象。
  ok: true; // 新增代码+DesktopGUIMcpClient：标记 MCP 请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUIMcpClient：保存 MCP 管理协议版本；如果没有这行，后续合同演进没有兼容依据。
  workspace: string; // 新增代码+DesktopGUIMcpClient：保存当前工作区路径；如果没有这行，用户无法确认 MCP 配置来自哪个项目。
  config_path: string; // 新增代码+DesktopGUIMcpClient：保存 mcp_servers.json 路径；如果没有这行，用户无法定位配置来源。
  generated_at: string; // 新增代码+DesktopGUIMcpClient：保存生成时间；如果没有这行，用户无法判断 MCP 状态是否新鲜。
  server_count: number; // 新增代码+DesktopGUIMcpClient：保存 server 数量；如果没有这行，MCP 页签无法显示接入规模。
  resource_count: number; // 新增代码+DesktopGUIMcpClient：保存 resource 数量；如果没有这行，MCP 页签无法显示资源规模。
  prompt_count: number; // 新增代码+DesktopGUIMcpClient：保存 prompt 数量；如果没有这行，MCP 页签无法显示提示词规模。
  servers: Array<Record<string, unknown>>; // 新增代码+DesktopGUIMcpClient：保存 server 卡片列表；如果没有这行，MCP 面板没有主体数据。
  resources: Array<Record<string, unknown>>; // 新增代码+DesktopGUIMcpClient：保存 resource 列表；如果没有这行，资源集合无法渲染。
  prompts: Array<Record<string, unknown>>; // 新增代码+DesktopGUIMcpClient：保存 prompt 列表；如果没有这行，提示词集合无法渲染。
  status_degraded: boolean; // 新增代码+DesktopGUIMcpClient：保存整体降级状态；如果没有这行，前端无法提示 MCP 读取是否可信。
  safe_error: string; // 新增代码+DesktopGUIMcpClient：保存脱敏错误文案；如果没有这行，失败时可能显示原始异常。
}; // 新增代码+DesktopGUIMcpClient：MCP 管理总览类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiMcpCollectionPayload = GuiMcpInventoryPayload & { // 新增代码+DesktopGUIMcpClient：定义 MCP 集合响应类型；如果没有这段，resources/prompts 单独请求没有类型。
  kind: "servers" | "resources" | "prompts" | string; // 新增代码+DesktopGUIMcpClient：保存集合类型；如果没有这行，调用方无法确认返回数据属于哪个 endpoint。
  status: string; // 新增代码+DesktopGUIMcpClient：保存集合状态；如果没有这行，unsupported/ready 无法稳定显示。
  data: Array<Record<string, unknown>>; // 新增代码+DesktopGUIMcpClient：保存当前集合数据；如果没有这行，调用方必须手动从总览字段里取数据。
}; // 新增代码+DesktopGUIMcpClient：MCP 集合响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiPlanningPayload = { // 新增代码+DesktopGUIPlanningClient：定义计划协作响应类型；如果没有这段，前端只能把 todo/task/team 状态当成不透明对象。
  ok: true; // 新增代码+DesktopGUIPlanningClient：标记 planning 请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUIPlanningClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  workspace: string; // 新增代码+DesktopGUIPlanningClient：保存当前工作区路径；如果没有这行，用户无法确认计划状态来自哪个项目。
  generated_at: string; // 新增代码+DesktopGUIPlanningClient：保存生成时间；如果没有这行，用户无法判断状态是否新鲜。
  reuse_module: string; // 新增代码+DesktopGUIPlanningClient：保存后端复用模块；如果没有这行，用户无法验收 GUI 没有另造任务系统。
  tool_count: number; // 新增代码+DesktopGUIPlanningClient：保存计划工具总数；如果没有这行，面板无法显示接入规模。
  available_tool_count: number; // 新增代码+DesktopGUIPlanningClient：保存可用计划工具数；如果没有这行，缺工具状态不易发现。
  tools: Array<Record<string, unknown>>; // 新增代码+DesktopGUIPlanningClient：保存计划/委派工具摘要；如果没有这行，工具区没有事实来源。
  todo_count: number; // 新增代码+DesktopGUIPlanningClient：保存 todo 数量；如果没有这行，摘要栏缺少计划规模。
  todos: Array<Record<string, unknown>>; // 新增代码+DesktopGUIPlanningClient：保存 todo 条目；如果没有这行，计划清单无法显示。
  task_count: number; // 新增代码+DesktopGUIPlanningClient：保存任务总数；如果没有这行，摘要栏缺少子任务规模。
  active_task_count: number; // 新增代码+DesktopGUIPlanningClient：保存活动任务数；如果没有这行，用户无法快速判断后台任务。
  tasks: Array<Record<string, unknown>>; // 新增代码+DesktopGUIPlanningClient：保存任务摘要；如果没有这行，任务区没有主体数据。
  peer_count: number; // 新增代码+DesktopGUIPlanningClient：保存 peer 数量；如果没有这行，摘要栏缺少团队规模。
  active_peer_count: number; // 新增代码+DesktopGUIPlanningClient：保存活跃 peer 数量；如果没有这行，团队状态无法快速判断。
  peer_message_count: number; // 新增代码+DesktopGUIPlanningClient：保存 peer 消息数；如果没有这行，协作消息规模不可见。
  pending_peer_message_count: number; // 新增代码+DesktopGUIPlanningClient：保存待确认消息数；如果没有这行，用户不知道是否有协作待办。
  peers: Array<Record<string, unknown>>; // 新增代码+DesktopGUIPlanningClient：保存 peer 摘要；如果没有这行，团队区没有主体数据。
  peer_messages: Array<Record<string, unknown>>; // 新增代码+DesktopGUIPlanningClient：保存最近 peer 消息；如果没有这行，消息区无法显示。
  status_degraded: boolean; // 新增代码+DesktopGUIPlanningClient：保存整体降级状态；如果没有这行，前端无法提示数据可信度。
  safe_error: string; // 新增代码+DesktopGUIPlanningClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
}; // 新增代码+DesktopGUIPlanningClient：计划协作类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiCommandConsolePayload = { // 新增代码+DesktopGUICommandConsoleClient：定义后台命令控制台响应类型；如果没有这段，前端只能把命令状态当成不透明对象。
  ok: true; // 新增代码+DesktopGUICommandConsoleClient：标记命令列表请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUICommandConsoleClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  workspace: string; // 新增代码+DesktopGUICommandConsoleClient：保存当前工作区路径；如果没有这行，用户无法确认命令数据来自哪个项目。
  generated_at: string; // 新增代码+DesktopGUICommandConsoleClient：保存生成时间；如果没有这行，用户无法判断命令状态是否新鲜。
  reuse_module: string; // 新增代码+DesktopGUICommandConsoleClient：保存后端复用模块；如果没有这行，用户无法验收 GUI 没有另造后台命令系统。
  command_count: number; // 新增代码+DesktopGUICommandConsoleClient：保存命令总数；如果没有这行，摘要栏缺少命令规模。
  running_command_count: number; // 新增代码+DesktopGUICommandConsoleClient：保存活跃命令数；如果没有这行，用户要逐条判断是否仍在运行。
  stop_supported_count: number; // 新增代码+DesktopGUICommandConsoleClient：保存可真实停止的命令数；如果没有这行，GUI 能力边界不清楚。
  commands: Array<Record<string, unknown>>; // 新增代码+DesktopGUICommandConsoleClient：保存命令卡片列表；如果没有这行，命令页签没有主体数据。
  status_degraded: boolean; // 新增代码+DesktopGUICommandConsoleClient：保存读取是否降级；如果没有这行，前端无法提示数据可信度。
  safe_error: string; // 新增代码+DesktopGUICommandConsoleClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
}; // 新增代码+DesktopGUICommandConsoleClient：命令控制台类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiCommandTailPayload = { // 新增代码+DesktopGUICommandConsoleClient：定义单条命令 tail 响应；如果没有这段，前端按需刷新输出没有稳定类型。
  ok: true; // 新增代码+DesktopGUICommandConsoleClient：标记 tail 请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUICommandConsoleClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  command_id: string; // 新增代码+DesktopGUICommandConsoleClient：保存命令 id；如果没有这行，前端无法确认 tail 属于哪个命令。
  status: string; // 新增代码+DesktopGUICommandConsoleClient：保存 ready/not_found 等状态；如果没有这行，前端无法解释刷新结果。
  tail: string; // 新增代码+DesktopGUICommandConsoleClient：保存输出尾部；如果没有这行，命令详情看不到终端输出。
  line_count: number; // 新增代码+DesktopGUICommandConsoleClient：保存输出行数；如果没有这行，空输出和有输出不易区分。
  next_offset: number; // 新增代码+DesktopGUICommandConsoleClient：保存当前输出偏移；如果没有这行，未来增量刷新缺少位置线索。
  command: Record<string, unknown>; // 新增代码+DesktopGUICommandConsoleClient：保存命令摘要；如果没有这行，tail 刷新后状态不会同步。
  safe_error: string; // 新增代码+DesktopGUICommandConsoleClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
}; // 新增代码+DesktopGUICommandConsoleClient：命令 tail 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiCommandActionPayload = { // 新增代码+DesktopGUICommandConsoleClient：定义命令控制动作响应；如果没有这段，停止按钮结果无法稳定渲染。
  ok: true; // 新增代码+DesktopGUICommandConsoleClient：标记动作请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUICommandConsoleClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  action: "stop"; // 新增代码+DesktopGUICommandConsoleClient：保存动作名称；如果没有这行，面板无法解释最近执行了哪个按钮。
  command_id: string; // 新增代码+DesktopGUICommandConsoleClient：保存目标命令 id；如果没有这行，点击反馈缺少对象。
  supported: boolean; // 新增代码+DesktopGUICommandConsoleClient：保存后端是否真实支持该动作；如果没有这行，前端可能把不可用当失败。
  status: string; // 新增代码+DesktopGUICommandConsoleClient：保存结果状态；如果没有这行，用户看不到 unavailable/already_terminal 等语义。
  message: string; // 新增代码+DesktopGUICommandConsoleClient：保存可读说明；如果没有这行，按钮点击后缺少肉眼可见结果。
  safe_error: string; // 新增代码+DesktopGUICommandConsoleClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
  command: Record<string, unknown>; // 新增代码+DesktopGUICommandConsoleClient：保存动作后的命令摘要；如果没有这行，面板无法同步目标状态。
}; // 新增代码+DesktopGUICommandConsoleClient：命令动作类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiHarnessStatusPayload = { // 新增代码+DesktopGUIHarnessClient：定义 V2 Harness 状态响应类型；如果没有这段，任务面板只能接收不透明对象。
  ok: true; // 新增代码+DesktopGUIHarnessClient：标记 Harness 状态请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUIHarnessClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  active_goal: Record<string, unknown>; // 新增代码+DesktopGUIHarnessClient：保存当前长任务目标；如果没有这行，右侧面板不知道正在执行什么。
  queue: Array<Record<string, unknown>>; // 新增代码+DesktopGUIHarnessClient：保存队列条目；如果没有这行，用户看不到等待中的 prompt 或 run。
  checkpoints: Array<Record<string, unknown>>; // 新增代码+DesktopGUIHarnessClient：保存 checkpoint 时间线；如果没有这行，任务是否跑偏不可见。
  last_progress: string; // 新增代码+DesktopGUIHarnessClient：保存最近进展摘要；如果没有这行，空 checkpoint 时面板缺少上下文。
  blocked_reason: string; // 新增代码+DesktopGUIHarnessClient：保存阻塞原因；如果没有这行，卡住状态没有解释。
  safe_error: string; // 新增代码+DesktopGUIHarnessClient：保存安全错误文案；如果没有这行，降级时可能暴露原始异常。
  status_degraded: boolean; // 新增代码+DesktopGUIHarnessClient：保存状态是否降级；如果没有这行，前端无法提示数据可信度。
  controls: Record<string, unknown>; // 新增代码+DesktopGUIHarnessClient：保存 pause/resume 能力开关；如果没有这行，按钮可能误显示。
}; // 新增代码+DesktopGUIHarnessClient：Harness 状态类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiHarnessControlPayload = { // 新增代码+DesktopGUIHarnessClient：定义 V2 Harness 控制响应类型；如果没有这段，pause/resume 调用结果无法稳定渲染。
  ok: true; // 新增代码+DesktopGUIHarnessClient：标记控制请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUIHarnessClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  action: "pause" | "resume" | "stop" | "checkpoint"; // 修改代码+DesktopGUIHarnessControlsClient：保存四种控制动作；如果没有这行，前端无法区分停止和 checkpoint 响应。
  supported: boolean; // 新增代码+DesktopGUIHarnessClient：保存后端是否支持该动作；如果没有这行，按钮能力探测不可靠。
  status: string; // 新增代码+DesktopGUIHarnessClient：保存控制结果状态；如果没有这行，用户看不到 unsupported/accepted 等语义。
  message: string; // 新增代码+DesktopGUIHarnessClient：保存可读说明；如果没有这行，未支持状态只能显示机器码。
  safe_error: string; // 新增代码+DesktopGUIHarnessClient：保存安全错误文案；如果没有这行，异常详情可能进入 GUI。
}; // 新增代码+DesktopGUIHarnessClient：Harness 控制类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiComputerUseActionPayload = { // 新增代码+DesktopGUIComputerUseWorkbenchClient：定义 Computer Use 工作台动作响应；如果没有这段，三个按钮结果只能当不透明对象。
  ok: true; // 新增代码+DesktopGUIComputerUseWorkbenchClient：标记动作请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存协议版本；如果没有这行，后续合同演进没有兼容依据。
  action: "request-access" | "observe" | "abort"; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存动作名称；如果没有这行，面板无法解释最近执行了哪个按钮。
  status: string; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存后端状态码；如果没有这行，用户看不到 accepted/observed/stopped。
  message: string; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存人类可读反馈；如果没有这行，按钮点击后缺少肉眼可见结果。
  safe_error: string; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
  events_after_sequence: number; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存事件游标；如果没有这行，后续调试难以关联事件。
  low_level_event_count: number; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存低层事件数；如果没有这行，GUI 无法证明 observe/request 没有真实输入。
  computer_use: Record<string, unknown>; // 新增代码+DesktopGUIComputerUseWorkbenchClient：保存动作后的工作台状态；如果没有这行，前端要额外请求一次刷新。
}; // 新增代码+DesktopGUIComputerUseWorkbenchClient：Computer Use 动作类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiBrowserActionPayload = { // 新增代码+DesktopGUIBrowserWorkbenchClient：定义 Browser 工作台动作响应；如果没有这段，刷新和记录打开按钮只能拿到不透明对象。
  ok: true; // 新增代码+DesktopGUIBrowserWorkbenchClient：标记 Browser 动作请求成功；如果没有这行，调用方无法区分成功 payload 和错误 payload。
  schema_version: number; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存协议版本；如果没有这行，后续 Browser endpoint 演进没有兼容依据。
  action: "open" | "refresh-status"; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存动作名称；如果没有这行，面板无法解释最近执行的是刷新还是记录打开。
  status: string; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存后端状态码；如果没有这行，用户看不到 recorded/refreshed/invalid_url 等语义。
  message: string; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存人类可读反馈；如果没有这行，按钮点击后缺少肉眼可见结果。
  safe_error: string; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存安全错误文案；如果没有这行，失败时可能显示原始异常。
  events_after_sequence: number; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存事件游标；如果没有这行，前端无法补拉刚写入的 Browser 审计事件。
  browser: Record<string, unknown>; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存动作后的 Browser 工作台状态；如果没有这行，前端要额外请求一次刷新。
}; // 新增代码+DesktopGUIBrowserWorkbenchClient：Browser 动作类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiBrowserCollectionPayload = { // 新增代码+DesktopGUIBrowserWorkbenchClient：定义 Browser 只读集合响应；如果没有这段，tabs/console/network 调用只能当不透明对象。
  ok: true; // 新增代码+DesktopGUIBrowserWorkbenchClient：标记 Browser 集合请求成功；如果没有这行，调用方无法区分错误响应。
  schema_version: number; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存协议版本；如果没有这行，collection endpoint 演进没有兼容依据。
  kind: "tabs" | "console" | "network"; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存集合类型；如果没有这行，调用方无法确认返回数据属于哪个集合。
  status: string; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存集合状态；如果没有这行，unsupported/ready 无法稳定显示。
  safe_error: string; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存安全错误文案；如果没有这行，集合读取失败会缺少稳定提示。
  data: Record<string, unknown>; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存集合主体数据；如果没有这行，调用方无法直接读取 tabs 或摘要。
  browser: Record<string, unknown>; // 新增代码+DesktopGUIBrowserWorkbenchClient：保存完整 Browser 工作台状态；如果没有这行，单次集合请求无法刷新主面板。
}; // 新增代码+DesktopGUIBrowserWorkbenchClient：Browser 集合类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiHealthPayload = { // ????+DesktopDiagnosticsClient??? V2 health ??????????????????????????????
  ok: true; // ????+DesktopDiagnosticsClient??? health ????????????????????????
  backend_online: boolean; // ????+DesktopDiagnosticsClient??????????????????????????/???
  schema_version: number; // ????+DesktopDiagnosticsClient????????????????????? V2 ???
  uptime_seconds: number; // ????+DesktopDiagnosticsClient??? bridge ??????????????????? bridge ??????
  workspace: string; // ????+DesktopDiagnosticsClient????????????????????????????
  workspace_name: string; // ????+DesktopDiagnosticsClient??????????????????????????
  feature_flags: Record<string, boolean>; // ????+DesktopDiagnosticsClient???????????????????????????
  model_provider: Record<string, unknown>; // ????+DesktopDiagnosticsClient?????/??????????????????? provider/model?
}; // ????+DesktopDiagnosticsClient?health ????????????TypeScript ????????
export type GuiDiagnosticsPayload = { // ????+DesktopDiagnosticsClient??? V2 diagnostics ?????????????????????????????
  ok: true; // ????+DesktopDiagnosticsClient??? diagnostics ????????????????????????
  schema_version: number; // ????+DesktopDiagnosticsClient??????????????????????????????
  backend_online: boolean; // ????+DesktopDiagnosticsClient??????????????????????????/???
  health: Record<string, unknown>; // ????+DesktopDiagnosticsClient????????????????????????????
  status_degraded: boolean; // ????+DesktopDiagnosticsClient???????????????????????????
  safe_error: string; // ????+DesktopDiagnosticsClient?????????????????UI ?????????
  snapshot_summary: Record<string, unknown>; // ????+DesktopDiagnosticsClient??????????????????????/?????
  last_error: string; // ????+DesktopDiagnosticsClient????????????????????????????
  release_gate: Record<string, unknown>; // ????+DesktopDiagnosticsClient????? release gate ??????????????????????
  diagnostic_bundle: Record<string, unknown>; // ????+DesktopDiagnosticsClient????????????????????????????
}; // ????+DesktopDiagnosticsClient?diagnostics ????????????TypeScript ????????
export type SendMessageResponse = { // 修改代码+DesktopRuntimePanelsClient：定义发送消息响应；如果没有这段，前端无法类型化 turn/run id。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记提交成功；如果没有这行，调用方无法区分错误响应。
  conversation_id: string; // 修改代码+DesktopRuntimePanelsClient：保存会话 id；如果没有这行，UI 无法确认消息归属。
  turn_id: string; // 修改代码+DesktopRuntimePanelsClient：保存 turn id；如果没有这行，取消和重试无法定位目标。
  run_id: string; // 修改代码+DesktopRuntimePanelsClient：保存 run id；如果没有这行，状态面板无法按 run 聚合。
  status: "queued"; // 修改代码+DesktopRuntimePanelsClient：保存初始状态；如果没有这行，UI 不知道提交后应显示什么。
  answer: string; // 修改代码+DesktopRuntimePanelsClient：保存初始回答占位；如果没有这行，后续兼容同步回答不方便。
  events_after_sequence: number; // 修改代码+DesktopRuntimePanelsClient：保存事件游标；如果没有这行，前端无法从正确位置轮询。
}; // 修改代码+DesktopRuntimePanelsClient：发送消息响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiTurnRequestOptions = { // 新增代码+DirectSSEPayload：定义 GUI turn 可选路由字段；如果没有这段，sendMessage 无法类型化 provider/model/reasoning/permission。
  providerId?: string; // 新增代码+DirectSSEPayload：保存 providerId；如果没有这行，前端无法把 OpenAI 选择提交给 bridge。
  modelId?: string; // 新增代码+DirectSSEPayload：保存 modelId；如果没有这行，前端无法把模型下拉选择提交给 bridge。
  reasoningEffort?: "low" | "medium" | "high" | "ultra"; // 新增代码+DirectSSEPayload：保存推理强度；如果没有这行，Codex 式努力等级无法进入请求。
  permissionMode?: "read_only" | "workspace_write" | "full_access"; // 新增代码+DirectSSEPayload：保存权限模式；如果没有这行，底部权限选择无法进入请求。
}; // 新增代码+DirectSSEPayload：GUI turn 可选路由字段结束；如果没有这行，TypeScript 类型语法不完整。

export type CancelTurnResponse = { // 修改代码+DesktopRuntimePanelsClient：定义取消响应；如果没有这段，取消按钮无法类型化后端结果。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记取消请求成功；如果没有这行，调用方无法区分错误响应。
  turn_id: string; // 修改代码+DesktopRuntimePanelsClient：保存被取消 turn；如果没有这行，UI 无法确认目标。
  run_id: string; // 修改代码+DesktopRuntimePanelsClient：保存 run id；如果没有这行，状态面板无法关联 run。
  status: "cancelling"; // 修改代码+DesktopRuntimePanelsClient：保存取消中状态；如果没有这行，UI 无法立即切换按钮。
  events_after_sequence: number; // 修改代码+DesktopRuntimePanelsClient：保存事件游标；如果没有这行，前端可能错过取消事件。
}; // 修改代码+DesktopRuntimePanelsClient：取消响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type ResumeSessionResponse = { // 修改代码+DesktopRuntimePanelsClient：定义恢复 session 响应；如果没有这段，窗口重启恢复数据没有类型约束。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记恢复成功；如果没有这行，调用方无法区分错误响应。
  session_id: string; // 修改代码+DesktopRuntimePanelsClient：保存恢复的 session；如果没有这行，UI 无法确认会话身份。
  messages: Array<Record<string, unknown>>; // 修改代码+DesktopRuntimePanelsClient：保存恢复消息；如果没有这行，线程无法重建历史。
  events_after_sequence: number; // 修改代码+DesktopRuntimePanelsClient：保存恢复后的事件游标；如果没有这行，前端不知道从哪继续轮询。
}; // 修改代码+DesktopRuntimePanelsClient：恢复响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type PermissionDecisionResponse = { // 修改代码+DesktopRuntimePanelsClient：定义权限决策响应；如果没有这段，弹窗按钮拿到的结果会是不透明对象。
  ok: true; // 修改代码+DesktopRuntimePanelsClient：标记权限决策成功；如果没有这行，调用方无法区分错误响应。
  request_id: string; // 修改代码+DesktopRuntimePanelsClient：保存已回答的权限 request_id；如果没有这行，前端无法确认关闭的是哪个弹窗。
  turn_id: string; // 修改代码+DesktopRuntimePanelsClient：保存关联 turn；如果没有这行，状态时间线难以关联权限回答。
  decision: "approve" | "deny"; // 修改代码+DesktopRuntimePanelsClient：保存 approve/deny 决策；如果没有这行，前端无法类型化按钮结果。
  status: "approved" | "denied"; // 修改代码+DesktopRuntimePanelsClient：保存后端最终状态；如果没有这行，重复回答或审计状态不清楚。
  events_after_sequence: number; // 修改代码+DesktopRuntimePanelsClient：保存事件游标；如果没有这行，前端可能错过 permission_answered 事件。
}; // 修改代码+DesktopRuntimePanelsClient：权限决策响应类型结束；如果没有这行，TypeScript 类型语法不完整。

type FetchLike = typeof fetch; // 修改代码+DesktopRuntimePanelsClient：抽象 fetch 形状；如果没有这行，测试无法注入假的网络层。

export class GuiClientError extends Error { // 修改代码+DesktopRuntimePanelsClient：类段开始，承载 GUI bridge 的结构化错误；如果没有这个类，UI 只能得到普通 Error 字符串。
  status: number; // 修改代码+DesktopRuntimePanelsClient：保存 HTTP 状态码；如果没有这行，前端无法区分 401、404、409。
  code: string; // 修改代码+DesktopRuntimePanelsClient：保存后端机器码；如果没有这行，前端无法针对 agent_busy 等错误做专门提示。
  requestId: string; // 修改代码+DesktopRuntimePanelsClient：保存后端 request id；如果没有这行，用户反馈和日志无法对应。
  constructor(status: number, code: string, message: string, requestId: string) { // 修改代码+DesktopRuntimePanelsClient：函数段开始，初始化结构化 client 错误；如果没有这段，错误对象无法携带 V2 字段。
    super(message); // 修改代码+DesktopRuntimePanelsClient：把后端 message 交给 Error；如果没有这行，String(error) 不会显示可读原因。
    this.name = "GuiClientError"; // 修改代码+DesktopRuntimePanelsClient：设置错误名；如果没有这行，日志中看不出错误来自 GUI client。
    this.status = status; // 修改代码+DesktopRuntimePanelsClient：保存 HTTP 状态码；如果没有这行，调用方不能判断网络层状态。
    this.code = code; // 修改代码+DesktopRuntimePanelsClient：保存后端错误码；如果没有这行，调用方会丢掉最重要的机器语义。
    this.requestId = requestId; // 修改代码+DesktopRuntimePanelsClient：保存 request id；如果没有这行，排查时无法定位后端同一次请求。
  } // 修改代码+DesktopRuntimePanelsClient：构造函数结束；如果没有这行，类构造函数语法不完整。
} // 修改代码+DesktopRuntimePanelsClient：类段结束，GuiClientError 到此结束；如果没有这行，TypeScript 类语法不完整。

function isRecord(value: unknown): value is Record<string, unknown> { // 修改代码+DesktopRuntimePanelsClient：函数段开始，判断未知 JSON 是否是对象；如果没有这段，错误解析会对非对象响应读字段。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 修改代码+DesktopRuntimePanelsClient：只接受普通对象；如果没有这行，数组或 null 会导致字段读取异常。
} // 修改代码+DesktopRuntimePanelsClient：函数段结束，isRecord 到此结束；如果没有这行，函数语法不完整。

function stringFrom(value: unknown, fallback: string): string { // 修改代码+DesktopRuntimePanelsClient：函数段开始，安全读取字符串字段；如果没有这段，错误字段类型异常会拖垮 client。
  return typeof value === "string" && value.length > 0 ? value : fallback; // 修改代码+DesktopRuntimePanelsClient：返回非空字符串或兜底值；如果没有这行，空 message/code 会进入 UI。
} // 修改代码+DesktopRuntimePanelsClient：函数段结束，stringFrom 到此结束；如果没有这行，函数语法不完整。

async function makeClientError(response: Response): Promise<GuiClientError> { // 修改代码+DesktopRuntimePanelsClient：函数段开始，把 HTTP 错误响应转成结构化 GuiClientError；如果没有这段，GET/POST 会重复泛化错误。
  let rawPayload: unknown = {}; // 修改代码+DesktopRuntimePanelsClient：准备保存错误 JSON；如果没有这行，JSON 解析失败时没有兜底对象。
  try { // 修改代码+DesktopRuntimePanelsClient：尝试读取后端结构化错误；如果没有这行，非 JSON 错误会直接抛出到调用方。
    rawPayload = await response.json(); // 修改代码+DesktopRuntimePanelsClient：解析错误响应 JSON；如果没有这行，client 会丢失 code 和 message。
  } catch { // 修改代码+DesktopRuntimePanelsClient：处理后端返回非 JSON 的情况；如果没有这行，HTML 或空 body 会变成未捕获异常。
    rawPayload = {}; // 修改代码+DesktopRuntimePanelsClient：解析失败时使用空对象；如果没有这行，后续字段读取没有安全输入。
  } // 修改代码+DesktopRuntimePanelsClient：JSON 读取保护结束；如果没有这行，try/catch 语法不完整。
  const payload = isRecord(rawPayload) ? (rawPayload as Partial<GuiV2ErrorResponse>) : {}; // 修改代码+DesktopRuntimePanelsClient：只从对象 payload 中读取字段；如果没有这行，错误解析会信任任意 JSON 类型。
  const code = stringFrom(payload.code, `http_${response.status}`); // 修改代码+DesktopRuntimePanelsClient：读取后端错误码或生成 HTTP 兜底码；如果没有这行，调用方无法机器处理失败。
  const message = stringFrom(payload.message, stringFrom(payload.error, `GUI bridge request failed: ${response.status}`)); // 修改代码+DesktopRuntimePanelsClient：优先读取 V2 message，兼容 V1 error；如果没有这行，用户只能看到状态码。
  const requestId = stringFrom(payload.request_id, ""); // 修改代码+DesktopRuntimePanelsClient：读取 request_id；如果没有这行，诊断链路会丢关联 id。
  return new GuiClientError(response.status, code, message, requestId); // 修改代码+DesktopRuntimePanelsClient：返回结构化错误对象；如果没有这行，调用方拿不到统一错误类型。
} // 修改代码+DesktopRuntimePanelsClient：函数段结束，makeClientError 到此结束；如果没有这行，函数语法不完整。

export function createGuiClient(baseUrl: string, bridgeToken: string, fetcher: FetchLike = fetch) { // 修改代码+DesktopRuntimePanelsClient：函数段开始，创建 GUI bridge 客户端；如果没有这段，渲染进程会到处手写 fetch。
  const normalizedBaseUrl = baseUrl.replace(/\/$/, ""); // 修改代码+DesktopRuntimePanelsClient：去掉 baseUrl 末尾斜杠；如果没有这行，请求 URL 可能出现双斜杠。
  const headers = { [GUI_V2_TOKEN_HEADER]: bridgeToken }; // 修改代码+DesktopRuntimePanelsClient：统一使用 V2 token header 常量；如果没有这行，header 字段会和协议模块分裂。
  async function requestJson<T>(path: string): Promise<T> { // 修改代码+DesktopRuntimePanelsClient：函数段开始，封装 GET JSON 请求；如果没有这段，bootstrap/events/panels 会重复网络错误处理。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { headers }); // 修改代码+DesktopRuntimePanelsClient：发送带 token 的请求；如果没有这行，前端无法和 bridge 通信。
    if (!response.ok) { // 修改代码+DesktopRuntimePanelsClient：检查 HTTP 成功状态；如果没有这行，错误响应会被当成正常数据渲染。
      throw await makeClientError(response); // 修改代码+DesktopRuntimePanelsClient：抛出包含 code/message/requestId 的错误；如果没有这行，GUI 会丢掉后端结构化错误。
    } // 修改代码+DesktopRuntimePanelsClient：错误分支结束；如果没有这行，条件块语法不完整。
    return (await response.json()) as T; // 修改代码+DesktopRuntimePanelsClient：解析并返回 JSON；如果没有这行，调用方拿不到 bridge payload。
  } // 修改代码+DesktopRuntimePanelsClient：函数段结束，requestJson 到此结束；如果没有这个边界，GET 请求封装范围不清楚。
  async function postJson<T>(path: string, payload: Record<string, unknown>): Promise<T> { // 修改代码+DesktopRuntimePanelsClient：函数段开始，封装 POST JSON 请求；如果没有这段，send/cancel/retry 会重复网络逻辑。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(payload) }); // 修改代码+DesktopRuntimePanelsClient：发送带 token 的 JSON POST；如果没有这行，前端无法调用生命周期端点。
    if (!response.ok) { // 修改代码+DesktopRuntimePanelsClient：检查 HTTP 成功状态；如果没有这行，409 busy 会被当作正常响应。
      throw await makeClientError(response); // 修改代码+DesktopRuntimePanelsClient：抛出包含 code/message/requestId 的错误；如果没有这行，busy/not_found 的机器语义会丢失。
    } // 修改代码+DesktopRuntimePanelsClient：错误分支结束；如果没有这行，条件块语法不完整。
    return (await response.json()) as T; // 修改代码+DesktopRuntimePanelsClient：解析并返回 JSON；如果没有这行，调用方拿不到后端响应。
  } // 修改代码+DesktopRuntimePanelsClient：函数段结束，postJson 到此结束；如果没有这个边界，POST 请求封装范围不清楚。
  return { // 修改代码+DesktopRuntimePanelsClient：返回面向 UI 的 client 方法；如果没有这行，调用方无法使用封装能力。
    bootstrap(): Promise<GuiBootstrapPayload> { // 修改代码+DesktopRuntimePanelsClient：读取 GUI 启动数据；如果没有这段，桌面首屏无法加载后端状态。
      return requestJson<GuiBootstrapPayload>("/v1/gui/bootstrap"); // 修改代码+DesktopRuntimePanelsClient：请求 bootstrap endpoint；如果没有这行，窗口只能显示静态假数据。
    }, // 修改代码+DesktopRuntimePanelsClient：bootstrap 方法结束；如果没有这行，返回对象语法不完整。
    events(sinceSequence: number | null, limit = 50): Promise<GuiEventPayload> { // 修改代码+DesktopRuntimePanelsClient：读取状态事件；如果没有这段，工具进度和运行状态无法刷新。
      const query = sinceSequence === null ? `limit=${limit}` : `since_sequence=${sinceSequence}&limit=${limit}`; // 修改代码+DesktopRuntimePanelsClient：构造事件轮询 query；如果没有这行，后端不知道从哪个游标开始返回。
      return requestJson<GuiEventPayload>(`/v1/gui/events?${query}`); // 修改代码+DesktopRuntimePanelsClient：请求事件 endpoint；如果没有这行，状态时间线没有后端事件来源。
    }, // 修改代码+DesktopRuntimePanelsClient：events 方法结束；如果没有这行，返回对象语法不完整。
    sessions(includeArchived = false): Promise<GuiSessionsPayload> { // 修改代码+DesktopGUISessionSearchClient：读取项目会话列表并可包含归档；如果没有这段，侧栏和归档视图无法从后端加载真实 sessions。
      const query = includeArchived ? "?include_archived=true" : ""; // 新增代码+DesktopGUISessionSearchClient：按需拼接归档 query；如果没有这行，归档入口无法拉取隐藏会话。
      return requestJson<GuiSessionsPayload>(`/v2/gui/sessions${query}`); // 修改代码+DesktopGUISessionSearchClient：请求 V2 sessions endpoint；如果没有这行，侧栏拿不到归档、固定和更新时间字段。
    }, // 修改代码+DesktopRuntimePanelsClient：sessions 方法结束；如果没有这行，返回对象语法不完整。
    searchSessions(query: string, includeArchived = false): Promise<GuiSearchPayload> { // 新增代码+DesktopGUISessionSearchClient：搜索历史会话并可包含归档；如果没有这段，搜索面板只能停留在本地空壳。
      const archivedQuery = includeArchived ? "&include_archived=true" : ""; // 新增代码+DesktopGUISessionSearchClient：按需拼接归档搜索参数；如果没有这行，归档视图输入关键词仍会漏掉归档会话。
      return requestJson<GuiSearchPayload>(`/v2/gui/search?q=${encodeURIComponent(query)}${archivedQuery}`); // 新增代码+DesktopGUISessionSearchClient：请求 V2 搜索 endpoint；如果没有这行，搜索词不会进入后端事实源。
    }, // 新增代码+DesktopGUISessionSearchClient：searchSessions 方法结束；如果没有这行，返回对象语法不完整。
    renameSession(sessionId: string, title: string): Promise<GuiSessionMutationPayload> { // 新增代码+DesktopGUISessionSearchClient：重命名历史会话；如果没有这段，侧栏 rename 无法调用后端。
      return postJson<GuiSessionMutationPayload>(`/v2/gui/sessions/${encodeURIComponent(sessionId)}/rename`, { title }); // 新增代码+DesktopGUISessionSearchClient：请求 V2 rename endpoint；如果没有这行，标题修改不会落盘。
    }, // 新增代码+DesktopGUISessionSearchClient：renameSession 方法结束；如果没有这行，返回对象语法不完整。
    archiveSession(sessionId: string, archived = true): Promise<GuiSessionMutationPayload> { // 新增代码+DesktopGUISessionSearchClient：归档或恢复历史会话；如果没有这段，归档入口没有后端动作。
      return postJson<GuiSessionMutationPayload>(`/v2/gui/sessions/${encodeURIComponent(sessionId)}/archive`, { archived }); // 新增代码+DesktopGUISessionSearchClient：请求 V2 archive endpoint；如果没有这行，归档状态不会写入 bridge。
    }, // 新增代码+DesktopGUISessionSearchClient：archiveSession 方法结束；如果没有这行，返回对象语法不完整。
    browserProviders(): Promise<GuiBrowserProvidersPayload> { // 修改代码+DesktopRuntimePanelsClient：读取旧浏览器 provider 状态；如果没有这段，旧面板和旧测试无法保持兼容。
      return requestJson<GuiBrowserProvidersPayload>("/v1/gui/browser/providers"); // 修改代码+DesktopRuntimePanelsClient：请求 browser providers endpoint；如果没有这行，旧浏览器面板没有状态来源。
    }, // 修改代码+DesktopRuntimePanelsClient：browserProviders 方法结束；如果没有这行，返回对象语法不完整。
    runtimePanels(): Promise<GuiRuntimePanelsPayload> { // 新增代码+DesktopRuntimePanelsClient：读取 V2 runtime panels；如果没有这段，浏览器和 Computer Use 面板无法使用统一 payload。
      return requestJson<GuiRuntimePanelsPayload>("/v2/gui/runtime/panels"); // 新增代码+DesktopRuntimePanelsClient：请求 V2 runtime panels endpoint；如果没有这行，右侧成熟面板拿不到后端事实。
    }, // 新增代码+DesktopRuntimePanelsClient：runtimePanels 方法结束；如果没有这行，返回对象语法不完整。
    openBrowser(url: string): Promise<GuiBrowserActionPayload> { // 新增代码+DesktopGUIBrowserWorkbenchClient：提交 Browser 记录打开请求；如果没有这段，浏览器工作台按钮无法调用后端。
      return postJson<GuiBrowserActionPayload>("/v2/gui/browser/open", { url }); // 新增代码+DesktopGUIBrowserWorkbenchClient：请求 open endpoint 并只发送 URL 字段；如果没有这行，后端收不到用户输入的目标地址。
    }, // 新增代码+DesktopGUIBrowserWorkbenchClient：openBrowser 方法结束；如果没有这行，返回对象语法不完整。
    refreshBrowserStatus(): Promise<GuiBrowserActionPayload> { // 新增代码+DesktopGUIBrowserWorkbenchClient：提交 Browser 状态刷新请求；如果没有这段，刷新按钮只能等轮询。
      return postJson<GuiBrowserActionPayload>("/v2/gui/browser/refresh-status", {}); // 新增代码+DesktopGUIBrowserWorkbenchClient：请求 refresh-status endpoint；如果没有这行，前端会收到 404。
    }, // 新增代码+DesktopGUIBrowserWorkbenchClient：refreshBrowserStatus 方法结束；如果没有这行，返回对象语法不完整。
    browserTabs(): Promise<GuiBrowserCollectionPayload> { // 新增代码+DesktopGUIBrowserWorkbenchClient：读取 Browser tabs 集合；如果没有这段，按需 tabs 诊断没有 client 方法。
      return requestJson<GuiBrowserCollectionPayload>("/v2/gui/browser/tabs"); // 新增代码+DesktopGUIBrowserWorkbenchClient：请求 tabs endpoint；如果没有这行，tabs 集合无法被前端单独刷新。
    }, // 新增代码+DesktopGUIBrowserWorkbenchClient：browserTabs 方法结束；如果没有这行，返回对象语法不完整。
    browserConsole(): Promise<GuiBrowserCollectionPayload> { // 新增代码+DesktopGUIBrowserWorkbenchClient：读取 Browser console 摘要；如果没有这段，按需 console 诊断没有 client 方法。
      return requestJson<GuiBrowserCollectionPayload>("/v2/gui/browser/console"); // 新增代码+DesktopGUIBrowserWorkbenchClient：请求 console endpoint；如果没有这行，console 摘要无法被前端单独刷新。
    }, // 新增代码+DesktopGUIBrowserWorkbenchClient：browserConsole 方法结束；如果没有这行，返回对象语法不完整。
    browserNetwork(): Promise<GuiBrowserCollectionPayload> { // 新增代码+DesktopGUIBrowserWorkbenchClient：读取 Browser network 摘要；如果没有这段，按需 network 诊断没有 client 方法。
      return requestJson<GuiBrowserCollectionPayload>("/v2/gui/browser/network"); // 新增代码+DesktopGUIBrowserWorkbenchClient：请求 network endpoint；如果没有这行，network 摘要无法被前端单独刷新。
    }, // 新增代码+DesktopGUIBrowserWorkbenchClient：browserNetwork 方法结束；如果没有这行，返回对象语法不完整。
    toolchain(): Promise<GuiToolchainPayload> { // 新增代码+DesktopGUIToolchainClient：读取 V2 工具链清单；如果没有这段，GUI 工具链控制中心拿不到后端事实源。
      return requestJson<GuiToolchainPayload>("/v2/gui/toolchain"); // 新增代码+DesktopGUIToolchainClient：请求 V2 toolchain endpoint；如果没有这行，前端只能停在空面板或硬编码清单。
    }, // 新增代码+DesktopGUIToolchainClient：toolchain 方法结束；如果没有这行，返回对象语法不完整。
    mcpServers(): Promise<GuiMcpInventoryPayload> { // 新增代码+DesktopGUIMcpClient：读取 MCP server 管理总览；如果没有这段，MCP 页签拿不到后端 registry 状态。
      return requestJson<GuiMcpInventoryPayload>("/v2/gui/mcp/servers"); // 新增代码+DesktopGUIMcpClient：请求 MCP servers endpoint；如果没有这行，前端只能停在空面板或硬编码状态。
    }, // 新增代码+DesktopGUIMcpClient：mcpServers 方法结束；如果没有这行，返回对象语法不完整。
    mcpResources(): Promise<GuiMcpCollectionPayload> { // 新增代码+DesktopGUIMcpClient：读取 MCP resource 集合；如果没有这段，资源诊断无法按需刷新。
      return requestJson<GuiMcpCollectionPayload>("/v2/gui/mcp/resources"); // 新增代码+DesktopGUIMcpClient：请求 MCP resources endpoint；如果没有这行，resource 集合会收到 404。
    }, // 新增代码+DesktopGUIMcpClient：mcpResources 方法结束；如果没有这行，返回对象语法不完整。
    mcpPrompts(): Promise<GuiMcpCollectionPayload> { // 新增代码+DesktopGUIMcpClient：读取 MCP prompt 集合；如果没有这段，prompt 诊断无法按需刷新。
      return requestJson<GuiMcpCollectionPayload>("/v2/gui/mcp/prompts"); // 新增代码+DesktopGUIMcpClient：请求 MCP prompts endpoint；如果没有这行，prompt 集合会收到 404。
    }, // 新增代码+DesktopGUIMcpClient：mcpPrompts 方法结束；如果没有这行，返回对象语法不完整。
    planning(): Promise<GuiPlanningPayload> { // 新增代码+DesktopGUIPlanningClient：读取计划协作状态；如果没有这段，Planning 面板拿不到 todo/task/team 事实源。
      return requestJson<GuiPlanningPayload>("/v2/gui/planning"); // 新增代码+DesktopGUIPlanningClient：请求 V2 planning endpoint；如果没有这行，前端只能停在空面板或硬编码状态。
    }, // 新增代码+DesktopGUIPlanningClient：planning 方法结束；如果没有这行，返回对象语法不完整。
    commands(): Promise<GuiCommandConsolePayload> { // 新增代码+DesktopGUICommandConsoleClient：读取后台命令控制台状态；如果没有这段，命令页签拿不到 TaskRegistry 事实源。
      return requestJson<GuiCommandConsolePayload>("/v2/gui/commands"); // 新增代码+DesktopGUICommandConsoleClient：请求 V2 commands endpoint；如果没有这行，前端只能停在空面板或硬编码状态。
    }, // 新增代码+DesktopGUICommandConsoleClient：commands 方法结束；如果没有这行，返回对象语法不完整。
    commandTail(commandId: string): Promise<GuiCommandTailPayload> { // 新增代码+DesktopGUICommandConsoleClient：读取单条后台命令输出尾部；如果没有这段，长输出无法按命令刷新。
      return requestJson<GuiCommandTailPayload>(`/v2/gui/commands/${encodeURIComponent(commandId)}/tail`); // 新增代码+DesktopGUICommandConsoleClient：请求 tail endpoint 并编码命令 id；如果没有这行，特殊字符可能破坏路径。
    }, // 新增代码+DesktopGUICommandConsoleClient：commandTail 方法结束；如果没有这行，返回对象语法不完整。
    stopCommand(commandId: string): Promise<GuiCommandActionPayload> { // 新增代码+DesktopGUICommandConsoleClient：请求停止后台命令；如果没有这段，停止按钮无法得到后端真实能力反馈。
      return postJson<GuiCommandActionPayload>(`/v2/gui/commands/${encodeURIComponent(commandId)}/stop`, {}); // 新增代码+DesktopGUICommandConsoleClient：请求 stop endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUICommandConsoleClient：stopCommand 方法结束；如果没有这行，返回对象语法不完整。
    harnessStatus(): Promise<GuiHarnessStatusPayload> { // 新增代码+DesktopGUIHarnessClient：读取 V2 Harness 状态；如果没有这段，任务面板无法从 bridge 获取目标、队列和 checkpoint。
      return requestJson<GuiHarnessStatusPayload>("/v2/gui/harness/status"); // 新增代码+DesktopGUIHarnessClient：请求 Harness 状态 endpoint；如果没有这行，右侧任务页签没有事实源。
    }, // 新增代码+DesktopGUIHarnessClient：harnessStatus 方法结束；如果没有这行，返回对象语法不完整。
    pauseHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessClient：请求暂停长任务；如果没有这段，按钮无法进行能力探测或提交暂停意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/pause", {}); // 新增代码+DesktopGUIHarnessClient：请求 pause endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessClient：pauseHarness 方法结束；如果没有这行，返回对象语法不完整。
    resumeHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessClient：请求恢复长任务；如果没有这段，按钮无法进行能力探测或提交恢复意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/resume", {}); // 新增代码+DesktopGUIHarnessClient：请求 resume endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessClient：resumeHarness 方法结束；如果没有这行，返回对象语法不完整。
    stopHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessControlsClient：请求停止长任务；如果没有这段，停止按钮无法提交终止意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/stop", {}); // 新增代码+DesktopGUIHarnessControlsClient：请求 stop endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessControlsClient：stopHarness 方法结束；如果没有这行，返回对象语法不完整。
    checkpointHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessControlsClient：请求写入手动 checkpoint；如果没有这段，checkpoint 按钮无法提交恢复点意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/checkpoint", {}); // 新增代码+DesktopGUIHarnessControlsClient：请求 checkpoint endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessControlsClient：checkpointHarness 方法结束；如果没有这行，返回对象语法不完整。
    requestComputerUseAccess(): Promise<GuiComputerUseActionPayload> { // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求 Computer Use 只读访问；如果没有这段，申请权限按钮无法调用后端。
      return postJson<GuiComputerUseActionPayload>("/v2/gui/computer-use/request-access", { mode: "observe" }); // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求 request-access endpoint 并明确只读模式；如果没有这行，前端只能收到 404 或缺少意图。
    }, // 新增代码+DesktopGUIComputerUseWorkbenchClient：requestComputerUseAccess 方法结束；如果没有这行，返回对象语法不完整。
    observeComputerUse(): Promise<GuiComputerUseActionPayload> { // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求刷新 Computer Use 观察摘要；如果没有这段，观察按钮无法触发后端状态刷新。
      return postJson<GuiComputerUseActionPayload>("/v2/gui/computer-use/observe", {}); // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求 observe endpoint；如果没有这行，面板无法拿到最新观察反馈。
    }, // 新增代码+DesktopGUIComputerUseWorkbenchClient：observeComputerUse 方法结束；如果没有这行，返回对象语法不完整。
    abortComputerUse(): Promise<GuiComputerUseActionPayload> { // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求中止 Computer Use；如果没有这段，急停按钮无法调用现有 stop 状态机。
      return postJson<GuiComputerUseActionPayload>("/v2/gui/computer-use/abort", {}); // 新增代码+DesktopGUIComputerUseWorkbenchClient：请求 abort endpoint；如果没有这行，用户只能看状态不能停止。
    }, // 新增代码+DesktopGUIComputerUseWorkbenchClient：abortComputerUse 方法结束；如果没有这行，返回对象语法不完整。
    providerSettings(): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：读取 Provider Settings catalog；如果没有这段，设置页无法从 bridge 获取 provider 列表。
      return requestJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/providers"); // 新增代码+ProviderSettingsClient：请求 provider catalog endpoint；如果没有这行，前端会停留在静态 provider 列表。
    }, // 新增代码+ProviderSettingsClient：providerSettings 方法结束；如果没有这行，返回对象语法不完整。
    connectProvider(providerId: string, authMethodId: string, fields: Record<string, string>): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：提交 Provider 连接凭据；如果没有这段，连接按钮没有后端动作。
      return postJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/auth", { provider_id: providerId, auth_method_id: authMethodId, fields }); // 新增代码+ProviderSettingsClient：请求 auth endpoint；如果没有这行，API key 不会进入后端 secret store。
    }, // 新增代码+ProviderSettingsClient：connectProvider 方法结束；如果没有这行，返回对象语法不完整。
    startProviderAuthAttempt(providerId: string, authMethodId: string): Promise<ProviderAuthAttemptPayload> { // 新增代码+OpenAIConnectClient：启动 browser/headless auth-attempt；如果没有这段，OAuth 方法点击后不会连接后端。
      return postJson<ProviderAuthAttemptPayload>("/v2/gui/provider-settings/auth-attempt/start", { provider_id: providerId, auth_method_id: authMethodId }); // 新增代码+OpenAIConnectClient：请求 start endpoint；如果没有这行，等待授权页拿不到 attempt_id 和展示码。
    }, // 新增代码+OpenAIConnectClient：startProviderAuthAttempt 方法结束；如果没有这行，返回对象语法不完整。
    providerAuthAttemptStatus(attemptId: string): Promise<ProviderAuthAttemptPayload> { // 新增代码+OpenAIConnectClient：读取 auth-attempt 状态；如果没有这段，等待页无法轮询后端。
      return requestJson<ProviderAuthAttemptPayload>(`/v2/gui/provider-settings/auth-attempt/status?attempt_id=${encodeURIComponent(attemptId)}`); // 新增代码+OpenAIConnectClient：请求 status endpoint 并编码 attempt id；如果没有这行，特殊字符可能破坏 query。
    }, // 新增代码+OpenAIConnectClient：providerAuthAttemptStatus 方法结束；如果没有这行，返回对象语法不完整。
    completeProviderAuthAttempt(attemptId: string): Promise<ProviderAuthAttemptPayload> { // 新增代码+OpenAIConnectClient：完成 mock auth-attempt；如果没有这段，视觉 QA driver 无法模拟授权完成。
      return postJson<ProviderAuthAttemptPayload>("/v2/gui/provider-settings/auth-attempt/complete", { attempt_id: attemptId }); // 新增代码+OpenAIConnectClient：请求 complete endpoint；如果没有这行，mock 完成无法刷新后端状态。
    }, // 新增代码+OpenAIConnectClient：completeProviderAuthAttempt 方法结束；如果没有这行，返回对象语法不完整。
    cancelProviderAuthAttempt(attemptId: string): Promise<ProviderAuthAttemptPayload> { // 新增代码+OpenAIConnectClient：取消 auth-attempt；如果没有这段，关闭等待页后 pending 会残留。
      return postJson<ProviderAuthAttemptPayload>("/v2/gui/provider-settings/auth-attempt/cancel", { attempt_id: attemptId }); // 新增代码+OpenAIConnectClient：请求 cancel endpoint；如果没有这行，用户取消无法通知后端。
    }, // 新增代码+OpenAIConnectClient：cancelProviderAuthAttempt 方法结束；如果没有这行，返回对象语法不完整。
    disconnectProvider(providerId: string): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：断开 Provider；如果没有这段，断开按钮不会清理后端状态。
      return postJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/disconnect", { provider_id: providerId }); // 新增代码+ProviderSettingsClient：请求 disconnect endpoint；如果没有这行，secret_ref 会继续存在。
    }, // 新增代码+ProviderSettingsClient：disconnectProvider 方法结束；如果没有这行，返回对象语法不完整。
    saveCustomProvider(payload: CustomProviderRequest): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：保存自定义 Provider；如果没有这段，自定义表单无法落盘。
      return postJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/custom-provider", { provider_id: payload.providerId, display_name: payload.displayName, base_url: payload.baseUrl, auth_method_id: payload.authMethodId, fields: payload.fields, headers: payload.headers, models: payload.models.map((model) => ({ id: model.id, display_name: model.displayName, visible: model.visible ?? true })) }); // 新增代码+ProviderSettingsClient：转换 camelCase 请求为后端 snake_case；如果没有这行，后端收不到正确字段。
    }, // 新增代码+ProviderSettingsClient：saveCustomProvider 方法结束；如果没有这行，返回对象语法不完整。
    setModelVisibility(providerId: string, modelId: string, visible: boolean): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：保存模型可见性；如果没有这段，模型开关无法持久。
      return postJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/model-visibility", { provider_id: providerId, model_id: modelId, visible }); // 新增代码+ProviderSettingsClient：请求 model visibility endpoint；如果没有这行，隐藏模型会在刷新后丢失。
    }, // 新增代码+ProviderSettingsClient：setModelVisibility 方法结束；如果没有这行，返回对象语法不完整。
    testProviderConnection(providerId: string): Promise<ProviderConnectionProbePayload> { // 新增代码+ProviderSettingsClient：测试 Provider 连接；如果没有这段，测试连接按钮没有后端动作。
      return postJson<ProviderConnectionProbePayload>("/v2/gui/provider-settings/test-connection", { provider_id: providerId }); // 新增代码+ProviderSettingsClient：请求 test-connection endpoint；如果没有这行，保存 key 会被误当连接成功。
    }, // 新增代码+ProviderSettingsClient：testProviderConnection 方法结束；如果没有这行，返回对象语法不完整。
    health(): Promise<GuiHealthPayload> { // ????+DesktopDiagnosticsClient??? V2 health??????????????????????
      return requestJson<GuiHealthPayload>("/v2/gui/health"); // ????+DesktopDiagnosticsClient??? V2 health endpoint???????????????? V1 ???
    }, // ????+DesktopDiagnosticsClient?health ??????????????????????
    diagnostics(): Promise<GuiDiagnosticsPayload> { // ????+DesktopDiagnosticsClient??? V2 diagnostics?????????????????????
      return requestJson<GuiDiagnosticsPayload>("/v2/gui/diagnostics"); // ????+DesktopDiagnosticsClient??? V2 diagnostics endpoint?????????????? release gate ??????
    }, // ????+DesktopDiagnosticsClient?diagnostics ??????????????????????
    probeUnknownRoute(): Promise<never> { // 新增代码+DesktopUnknownRouteProbe：请求一个不存在的 V2 路由来验证结构化 404；如果没有这段，GUI 无法从诊断页主动验收 unknown route 错误面。
      return requestJson<never>("/v2/gui/__unknown_route_probe__"); // 新增代码+DesktopUnknownRouteProbe：使用现有 GET 错误解析路径；如果没有这一行，unknown route 验收只能靠外部 curl。
    }, // 新增代码+DesktopUnknownRouteProbe：unknown route 探针方法结束；如果没有这一行，client 返回对象语法不完整。
    sendMessage(prompt: string, conversationId = "default", options: GuiTurnRequestOptions = {}): Promise<SendMessageResponse> { // 修改代码+DirectSSEPayload：发送用户 prompt 和可选模型路由字段；如果没有这段，composer 无法创建带模型选择的后端 turn。
      return postJson<SendMessageResponse>("/v1/gui/messages", { conversation_id: conversationId, prompt, providerId: options.providerId ?? "", modelId: options.modelId ?? "", reasoningEffort: options.reasoningEffort ?? "high", permissionMode: options.permissionMode ?? "full_access" }); // 修改代码+DirectSSEPayload：请求 messages endpoint 并附带 provider/model/reasoning/permission；如果没有这行，用户选择不会进入 bridge。
    }, // 修改代码+DesktopRuntimePanelsClient：sendMessage 方法结束；如果没有这行，返回对象语法不完整。
    cancelTurn(turnId: string): Promise<CancelTurnResponse> { // 修改代码+DesktopRuntimePanelsClient：请求取消 turn；如果没有这段，取消按钮没有后端动作。
      return postJson<CancelTurnResponse>(`/v1/gui/turns/${turnId}/cancel`, {}); // 修改代码+DesktopRuntimePanelsClient：请求 cancel endpoint；如果没有这行，后端不会写取消事件。
    }, // 修改代码+DesktopRuntimePanelsClient：cancelTurn 方法结束；如果没有这行，返回对象语法不完整。
    retryTurn(turnId: string): Promise<SendMessageResponse> { // 修改代码+DesktopRuntimePanelsClient：请求重试 turn；如果没有这段，重试按钮没有后端动作。
      return postJson<SendMessageResponse>(`/v1/gui/turns/${turnId}/retry`, {}); // 修改代码+DesktopRuntimePanelsClient：请求 retry endpoint；如果没有这行，后端不会创建 linked turn。
    }, // 修改代码+DesktopRuntimePanelsClient：retryTurn 方法结束；如果没有这行，返回对象语法不完整。
    resumeSession(sessionId: string): Promise<ResumeSessionResponse> { // 修改代码+DesktopRuntimePanelsClient：恢复历史 session；如果没有这段，窗口重启无法重建消息。
      return postJson<ResumeSessionResponse>(`/v1/gui/sessions/${sessionId}/resume`, {}); // 修改代码+DesktopRuntimePanelsClient：请求 resume endpoint；如果没有这行，前端无法拿到后端恢复数据。
    }, // 修改代码+DesktopRuntimePanelsClient：resumeSession 方法结束；如果没有这行，返回对象语法不完整。
    decidePermission(requestId: string, turnId: string, decision: "approve" | "deny", reason: string): Promise<PermissionDecisionResponse> { // 修改代码+DesktopRuntimePanelsClient：提交权限允许或拒绝意图；如果没有这段，权限弹窗按钮无法进入后端审计。
      return postJson<PermissionDecisionResponse>(`/v1/gui/permissions/${requestId}/decision`, { turn_id: turnId, decision, reason }); // 修改代码+DesktopRuntimePanelsClient：请求权限决策 endpoint；如果没有这行，前端会绕过真实权限 machinery。
    }, // 修改代码+DesktopRuntimePanelsClient：decidePermission 方法结束；如果没有这行，返回对象语法不完整。
  }; // 修改代码+DesktopRuntimePanelsClient：client 对象返回结束；如果没有这行，createGuiClient 没有返回值。
} // 修改代码+DesktopRuntimePanelsClient：函数段结束，createGuiClient 到此结束；如果没有这个边界，API client 范围不清楚。
