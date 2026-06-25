import { GUI_V2_TOKEN_HEADER } from "./guiTypes"; // 修改代码+DesktopRuntimePanelsClient：复用 V2 token header 常量；如果没有这行，client 会继续硬编码协议字段。
import type { GuiV2ErrorResponse } from "./guiTypes"; // 修改代码+DesktopRuntimePanelsClient：导入结构化错误响应类型；如果没有这行，错误解析会退回不透明对象。
import type { CustomProviderRequest, GuiProviderSettingsPayload, ProviderConnectionProbePayload } from "./guiProviderTypes"; // 新增代码+ProviderSettingsClient：导入 Provider Settings 类型；如果没有这行，新增 client 方法只能返回不透明对象。

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
  action: "pause" | "resume"; // 新增代码+DesktopGUIHarnessClient：保存控制动作；如果没有这行，前端无法区分暂停和恢复响应。
  supported: boolean; // 新增代码+DesktopGUIHarnessClient：保存后端是否支持该动作；如果没有这行，按钮能力探测不可靠。
  status: string; // 新增代码+DesktopGUIHarnessClient：保存控制结果状态；如果没有这行，用户看不到 unsupported/accepted 等语义。
  message: string; // 新增代码+DesktopGUIHarnessClient：保存可读说明；如果没有这行，未支持状态只能显示机器码。
  safe_error: string; // 新增代码+DesktopGUIHarnessClient：保存安全错误文案；如果没有这行，异常详情可能进入 GUI。
}; // 新增代码+DesktopGUIHarnessClient：Harness 控制类型结束；如果没有这行，TypeScript 类型语法不完整。

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
    harnessStatus(): Promise<GuiHarnessStatusPayload> { // 新增代码+DesktopGUIHarnessClient：读取 V2 Harness 状态；如果没有这段，任务面板无法从 bridge 获取目标、队列和 checkpoint。
      return requestJson<GuiHarnessStatusPayload>("/v2/gui/harness/status"); // 新增代码+DesktopGUIHarnessClient：请求 Harness 状态 endpoint；如果没有这行，右侧任务页签没有事实源。
    }, // 新增代码+DesktopGUIHarnessClient：harnessStatus 方法结束；如果没有这行，返回对象语法不完整。
    pauseHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessClient：请求暂停长任务；如果没有这段，按钮无法进行能力探测或提交暂停意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/pause", {}); // 新增代码+DesktopGUIHarnessClient：请求 pause endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessClient：pauseHarness 方法结束；如果没有这行，返回对象语法不完整。
    resumeHarness(): Promise<GuiHarnessControlPayload> { // 新增代码+DesktopGUIHarnessClient：请求恢复长任务；如果没有这段，按钮无法进行能力探测或提交恢复意图。
      return postJson<GuiHarnessControlPayload>("/v2/gui/harness/resume", {}); // 新增代码+DesktopGUIHarnessClient：请求 resume endpoint；如果没有这行，前端只能收到 404。
    }, // 新增代码+DesktopGUIHarnessClient：resumeHarness 方法结束；如果没有这行，返回对象语法不完整。
    providerSettings(): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：读取 Provider Settings catalog；如果没有这段，设置页无法从 bridge 获取 provider 列表。
      return requestJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/providers"); // 新增代码+ProviderSettingsClient：请求 provider catalog endpoint；如果没有这行，前端会停留在静态 provider 列表。
    }, // 新增代码+ProviderSettingsClient：providerSettings 方法结束；如果没有这行，返回对象语法不完整。
    connectProvider(providerId: string, authMethodId: string, fields: Record<string, string>): Promise<GuiProviderSettingsPayload> { // 新增代码+ProviderSettingsClient：提交 Provider 连接凭据；如果没有这段，连接按钮没有后端动作。
      return postJson<GuiProviderSettingsPayload>("/v2/gui/provider-settings/auth", { provider_id: providerId, auth_method_id: authMethodId, fields }); // 新增代码+ProviderSettingsClient：请求 auth endpoint；如果没有这行，API key 不会进入后端 secret store。
    }, // 新增代码+ProviderSettingsClient：connectProvider 方法结束；如果没有这行，返回对象语法不完整。
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
    sendMessage(prompt: string, conversationId = "default"): Promise<SendMessageResponse> { // 修改代码+DesktopRuntimePanelsClient：发送用户 prompt；如果没有这段，composer 无法创建后端 turn。
      return postJson<SendMessageResponse>("/v1/gui/messages", { conversation_id: conversationId, prompt }); // 修改代码+DesktopRuntimePanelsClient：请求 messages endpoint；如果没有这行，用户输入不会进入 bridge。
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
