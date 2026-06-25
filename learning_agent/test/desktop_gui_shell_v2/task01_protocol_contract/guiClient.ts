import { GUI_V2_TOKEN_HEADER } from "./guiTypes"; // 新增代码+GuiV2ClientErrors：复用 V2 token header 常量；如果没有这一行，client 会继续硬编码协议字段。
import type { GuiV2ErrorResponse } from "./guiTypes"; // 新增代码+GuiV2ClientErrors：导入结构化错误响应类型；如果没有这一行，错误解析会退回不透明对象。

export type GuiBootstrapPayload = { // 新增代码+DesktopGuiClient：定义 bootstrap 响应类型；如果没有这段，前端首屏数据会变成不透明对象。
  ok: true; // 新增代码+DesktopGuiClient：标记 bridge 成功响应；如果没有这行，调用方无法用类型判断成功形状。
  workspace: string; // 新增代码+DesktopGuiClient：保存当前项目路径；如果没有这行，侧栏无法显示当前工作区。
  app: { // 新增代码+DesktopGuiClient：保存后端应用元信息；如果没有这段，前端无法检查协议版本。
    name: string; // 新增代码+DesktopGuiClient：保存应用名称；如果没有这行，首屏标题无法来自后端事实。
    schema_version: number; // 新增代码+DesktopGuiClient：保存协议版本；如果没有这行，后续兼容判断没有依据。
  }; // 新增代码+DesktopGuiClient：app 元信息结束；如果没有这行，类型语法不完整。
  snapshot: Record<string, unknown>; // 新增代码+DesktopGuiClient：保存统一状态快照；如果没有这行，状态面板没有启动数据。
  feature_flags: Record<string, boolean>; // 新增代码+DesktopGuiClient：保存后端能力开关；如果没有这行，UI 无法按能力启用功能。
}; // 新增代码+DesktopGuiClient：bootstrap 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiEventPayload = { // 新增代码+DesktopGuiClient：定义事件轮询响应类型；如果没有这段，工具卡片无法稳定消费事件。
  ok: true; // 新增代码+DesktopGuiClient：标记事件响应成功；如果没有这行，调用方无法区分错误响应。
  events: Array<Record<string, unknown>>; // 新增代码+DesktopGuiClient：保存事件列表；如果没有这行，状态时间线没有数据来源。
  since_sequence: number | null; // 新增代码+DesktopGuiClient：保存本次请求游标；如果没有这行，前端无法确认轮询边界。
  limit: number; // 新增代码+DesktopGuiClient：保存本次请求限制；如果没有这行，前端无法调试事件批量大小。
}; // 新增代码+DesktopGuiClient：事件 payload 类型结束；如果没有这行，TypeScript 类型语法不完整。
export type GuiSessionsPayload = { // 新增代码+DesktopGUISessionsClient：定义 sessions 响应类型；如果没有这段，侧栏拿到的会话列表会是不透明对象。
  ok: true; // 新增代码+DesktopGUISessionsClient：标记 sessions 请求成功；如果没有这行，调用方无法区分错误响应。
  sessions: Array<Record<string, unknown> | string>; // 新增代码+DesktopGUISessionsClient：保存最近会话列表；如果没有这行，侧栏没有真实数据来源。
  resume: Record<string, unknown>; // 新增代码+DesktopGUISessionsClient：保存恢复状态摘要；如果没有这行，侧栏无法显示恢复风险或最近恢复状态。
}; // 新增代码+DesktopGUISessionsClient：sessions 响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiBrowserProvidersPayload = { // 新增代码+DesktopGUIBrowserPanelClient：定义浏览器 provider 响应类型；如果没有这段，右栏拿到的 provider_status 会是不透明对象。
  ok: true; // 新增代码+DesktopGUIBrowserPanelClient：标记浏览器 provider 请求成功；如果没有这行，调用方无法区分错误响应。
  provider_status: Record<string, unknown>; // 新增代码+DesktopGUIBrowserPanelClient：保存浏览器 provider 健康状态；如果没有这行，BrowserPanel 没有数据来源。
  browser: Record<string, unknown>; // 新增代码+DesktopGUIBrowserPanelClient：保存浏览器 runtime 总览；如果没有这行，后续面板无法扩展 run/action 摘要。
}; // 新增代码+DesktopGUIBrowserPanelClient：浏览器 provider 响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type SendMessageResponse = { // 新增代码+DesktopGUILifecycleClient：定义发送消息响应；如果没有这段，前端无法类型化 turn/run id。
  ok: true; // 新增代码+DesktopGUILifecycleClient：标记提交成功；如果没有这行，调用方无法区分错误响应。
  conversation_id: string; // 新增代码+DesktopGUILifecycleClient：保存会话 id；如果没有这行，UI 无法确认消息归属。
  turn_id: string; // 新增代码+DesktopGUILifecycleClient：保存 turn id；如果没有这行，取消/重试无法定位目标。
  run_id: string; // 新增代码+DesktopGUILifecycleClient：保存 run id；如果没有这行，状态面板无法按 run 聚合。
  status: "queued"; // 新增代码+DesktopGUILifecycleClient：保存初始状态；如果没有这行，UI 不知道提交后应显示什么。
  answer: string; // 新增代码+DesktopGUILifecycleClient：保存初始回答占位；如果没有这行，后续兼容同步回答不方便。
  events_after_sequence: number; // 新增代码+DesktopGUILifecycleClient：保存事件游标；如果没有这行，前端无法从正确位置轮询。
}; // 新增代码+DesktopGUILifecycleClient：发送消息响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type CancelTurnResponse = { // 新增代码+DesktopGUILifecycleClient：定义取消响应；如果没有这段，取消按钮无法类型化后端结果。
  ok: true; // 新增代码+DesktopGUILifecycleClient：标记取消请求成功；如果没有这行，调用方无法区分错误响应。
  turn_id: string; // 新增代码+DesktopGUILifecycleClient：保存被取消 turn；如果没有这行，UI 无法确认目标。
  run_id: string; // 新增代码+DesktopGUILifecycleClient：保存 run id；如果没有这行，状态面板无法关联 run。
  status: "cancelling"; // 新增代码+DesktopGUILifecycleClient：保存取消中状态；如果没有这行，UI 无法立即切换按钮。
  events_after_sequence: number; // 新增代码+DesktopGUILifecycleClient：保存事件游标；如果没有这行，前端可能错过取消事件。
}; // 新增代码+DesktopGUILifecycleClient：取消响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type ResumeSessionResponse = { // 新增代码+DesktopGUILifecycleClient：定义恢复 session 响应；如果没有这段，窗口重启恢复数据没有类型约束。
  ok: true; // 新增代码+DesktopGUILifecycleClient：标记恢复成功；如果没有这行，调用方无法区分错误响应。
  session_id: string; // 新增代码+DesktopGUILifecycleClient：保存恢复的 session；如果没有这行，UI 无法确认会话身份。
  messages: Array<Record<string, unknown>>; // 新增代码+DesktopGUILifecycleClient：保存恢复消息；如果没有这行，线程无法重建历史。
  events_after_sequence: number; // 新增代码+DesktopGUILifecycleClient：保存恢复后的事件游标；如果没有这行，前端不知道从哪继续轮询。
}; // 新增代码+DesktopGUILifecycleClient：恢复响应类型结束；如果没有这行，TypeScript 类型语法不完整。

export type PermissionDecisionResponse = { // 新增代码+DesktopGUIPermissionsClient：定义权限决策响应；如果没有这段，弹窗按钮拿到的结果会是不透明对象。
  ok: true; // 新增代码+DesktopGUIPermissionsClient：标记权限决策成功；如果没有这行，调用方无法区分错误响应。
  request_id: string; // 新增代码+DesktopGUIPermissionsClient：保存已回答的权限请求 id；如果没有这行，前端无法确认关闭的是哪个弹窗。
  turn_id: string; // 新增代码+DesktopGUIPermissionsClient：保存关联 turn；如果没有这行，状态时间线难以关联权限回答。
  decision: "approve" | "deny"; // 新增代码+DesktopGUIPermissionsClient：保存 approve/deny 决策；如果没有这行，前端无法类型化按钮结果。
  status: "approved" | "denied"; // 新增代码+DesktopGUIPermissionsClient：保存后端最终状态；如果没有这行，重复回答或审计状态不清楚。
  events_after_sequence: number; // 新增代码+DesktopGUIPermissionsClient：保存事件游标；如果没有这行，前端可能错过 permission_answered 事件。
}; // 新增代码+DesktopGUIPermissionsClient：权限决策响应类型结束；如果没有这行，TypeScript 类型语法不完整。

type FetchLike = typeof fetch; // 新增代码+DesktopGuiClient：抽象 fetch 形状；如果没有这行，测试无法注入假的网络层。

export class GuiClientError extends Error { // 新增代码+GuiV2ClientErrors：类段开始，承载 GUI bridge 的结构化错误；如果没有这个类，UI 只能得到普通 Error 字符串。
  status: number; // 新增代码+GuiV2ClientErrors：保存 HTTP 状态码；如果没有这一行，前端无法区分 401、404、409。
  code: string; // 新增代码+GuiV2ClientErrors：保存后端机器码；如果没有这一行，前端无法针对 agent_busy 等错误做专门提示。
  requestId: string; // 新增代码+GuiV2ClientErrors：保存后端请求 id；如果没有这一行，用户反馈和日志无法对应。

  constructor(status: number, code: string, message: string, requestId: string) { // 新增代码+GuiV2ClientErrors：函数段开始，初始化结构化 client 错误；如果没有这段，错误对象无法携带 V2 字段。
    super(message); // 新增代码+GuiV2ClientErrors：把后端 message 交给 Error；如果没有这一行，String(error) 不会显示可读原因。
    this.name = "GuiClientError"; // 新增代码+GuiV2ClientErrors：设置错误名；如果没有这一行，日志中看不出错误来自 GUI client。
    this.status = status; // 新增代码+GuiV2ClientErrors：保存 HTTP 状态码；如果没有这一行，调用方不能判断网络层状态。
    this.code = code; // 新增代码+GuiV2ClientErrors：保存后端错误码；如果没有这一行，调用方会丢掉最重要的机器语义。
    this.requestId = requestId; // 新增代码+GuiV2ClientErrors：保存 request id；如果没有这一行，排查时无法定位后端同一次请求。
  } // 新增代码+GuiV2ClientErrors：函数段结束，GuiClientError.constructor 到此结束；如果没有这一行，类构造函数语法不完整。
} // 新增代码+GuiV2ClientErrors：类段结束，GuiClientError 到此结束；如果没有这一行，TypeScript 类语法不完整。

function isRecord(value: unknown): value is Record<string, unknown> { // 新增代码+GuiV2ClientErrors：函数段开始，判断未知 JSON 是否是对象；如果没有这段，错误解析会对非对象响应读字段。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 新增代码+GuiV2ClientErrors：只接受普通对象；如果没有这一行，数组或 null 会导致字段读取异常。
} // 新增代码+GuiV2ClientErrors：函数段结束，isRecord 到此结束；如果没有这一行，函数语法不完整。

function stringFrom(value: unknown, fallback: string): string { // 新增代码+GuiV2ClientErrors：函数段开始，安全读取字符串字段；如果没有这段，错误字段类型异常会拖垮 client。
  return typeof value === "string" && value.length > 0 ? value : fallback; // 新增代码+GuiV2ClientErrors：返回非空字符串或兜底值；如果没有这一行，空 message/code 会进入 UI。
} // 新增代码+GuiV2ClientErrors：函数段结束，stringFrom 到此结束；如果没有这一行，函数语法不完整。

async function makeClientError(response: Response): Promise<GuiClientError> { // 新增代码+GuiV2ClientErrors：函数段开始，把 HTTP 错误响应转成结构化 GuiClientError；如果没有这段，GET/POST 会继续重复抛泛化错误。
  let rawPayload: unknown = {}; // 新增代码+GuiV2ClientErrors：准备保存错误 JSON；如果没有这一行，JSON 解析失败时没有兜底对象。
  try { // 新增代码+GuiV2ClientErrors：尝试读取后端结构化错误；如果没有这一行，非 JSON 错误会直接抛出到调用方。
    rawPayload = await response.json(); // 新增代码+GuiV2ClientErrors：解析错误响应 JSON；如果没有这一行，client 会丢失 code 和 message。
  } catch { // 新增代码+GuiV2ClientErrors：处理后端返回非 JSON 的情况；如果没有这一行，HTML 或空 body 会变成未捕获异常。
    rawPayload = {}; // 新增代码+GuiV2ClientErrors：解析失败时使用空对象；如果没有这一行，后续字段读取没有安全输入。
  } // 新增代码+GuiV2ClientErrors：JSON 读取保护结束；如果没有这一行，try/catch 语法不完整。
  const payload = isRecord(rawPayload) ? (rawPayload as Partial<GuiV2ErrorResponse>) : {}; // 新增代码+GuiV2ClientErrors：只从对象 payload 中读取字段；如果没有这一行，错误解析会信任任意 JSON 类型。
  const code = stringFrom(payload.code, `http_${response.status}`); // 新增代码+GuiV2ClientErrors：读取后端错误码或生成 HTTP 兜底码；如果没有这一行，调用方无法机器处理失败。
  const message = stringFrom(payload.message, stringFrom(payload.error, `GUI bridge request failed: ${response.status}`)); // 新增代码+GuiV2ClientErrors：优先读取 V2 message，兼容 V1 error；如果没有这一行，用户只能看到状态码。
  const requestId = stringFrom(payload.request_id, ""); // 新增代码+GuiV2ClientErrors：读取 request_id；如果没有这一行，诊断链路会丢关联 id。
  return new GuiClientError(response.status, code, message, requestId); // 新增代码+GuiV2ClientErrors：返回结构化错误对象；如果没有这一行，调用方拿不到统一错误类型。
} // 新增代码+GuiV2ClientErrors：函数段结束，makeClientError 到此结束；如果没有这一行，函数语法不完整。

export function createGuiClient(baseUrl: string, bridgeToken: string, fetcher: FetchLike = fetch) { // 新增代码+DesktopGuiClient：函数段开始，创建 GUI bridge 客户端；如果没有这段，渲染进程会到处手写 fetch。
  const normalizedBaseUrl = baseUrl.replace(/\/$/, ""); // 新增代码+DesktopGuiClient：去掉 baseUrl 末尾斜杠；如果没有这行，请求 URL 可能出现双斜杠。
  const headers = { [GUI_V2_TOKEN_HEADER]: bridgeToken }; // 修改代码+GuiV2ClientErrors：统一使用 V2 token header 常量；如果没有这一行，header 字段会和协议模块分裂。

  async function requestJson<T>(path: string): Promise<T> { // 新增代码+DesktopGuiClient：函数段开始，封装 GET JSON 请求；如果没有这段，bootstrap 和 events 会重复网络错误处理。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { headers }); // 新增代码+DesktopGuiClient：发送带 token 的请求；如果没有这行，前端无法和 bridge 通信。
    if (!response.ok) { // 新增代码+DesktopGuiClient：检查 HTTP 成功状态；如果没有这行，错误响应会被当成正常数据渲染。
      throw await makeClientError(response); // 修改代码+GuiV2ClientErrors：抛出包含 code/message/requestId 的错误；如果没有这一行，GUI 会丢掉后端结构化错误。
    } // 新增代码+DesktopGuiClient：错误分支结束；如果没有这行，条件块语法不完整。
    return (await response.json()) as T; // 新增代码+DesktopGuiClient：解析并返回 JSON；如果没有这行，调用方拿不到 bridge payload。
  } // 新增代码+DesktopGuiClient：函数段结束，requestJson 到此结束；如果没有这个边界，用户不容易看出 GET 请求封装范围。

  async function postJson<T>(path: string, payload: Record<string, unknown>): Promise<T> { // 新增代码+DesktopGUILifecycleClient：函数段开始，封装 POST JSON 请求；如果没有这段，send/cancel/retry 会重复写网络逻辑。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(payload) }); // 新增代码+DesktopGUILifecycleClient：发送带 token 的 JSON POST；如果没有这行，前端无法调用生命周期端点。
    if (!response.ok) { // 新增代码+DesktopGUILifecycleClient：检查 HTTP 成功状态；如果没有这行，409 busy 会被当作正常响应。
      throw await makeClientError(response); // 修改代码+GuiV2ClientErrors：抛出包含 code/message/requestId 的错误；如果没有这一行，busy/not_found 的机器语义会丢失。
    } // 新增代码+DesktopGUILifecycleClient：错误分支结束；如果没有这行，条件块语法不完整。
    return (await response.json()) as T; // 新增代码+DesktopGUILifecycleClient：解析并返回 JSON；如果没有这行，调用方拿不到后端响应。
  } // 新增代码+DesktopGUILifecycleClient：函数段结束，postJson 到此结束；如果没有这个边界，用户不容易看出 POST 请求封装范围。

  return { // 新增代码+DesktopGuiClient：返回面向 UI 的 client 方法；如果没有这行，调用方无法使用封装能力。
    bootstrap(): Promise<GuiBootstrapPayload> { // 新增代码+DesktopGuiClient：读取 GUI 启动数据；如果没有这段，桌面首屏无法加载后端状态。
      return requestJson<GuiBootstrapPayload>("/v1/gui/bootstrap"); // 新增代码+DesktopGuiClient：请求 bootstrap endpoint；如果没有这行，窗口只能显示静态假数据。
    }, // 新增代码+DesktopGuiClient：bootstrap 方法结束；如果没有这行，返回对象语法不完整。
    events(sinceSequence: number | null, limit = 50): Promise<GuiEventPayload> { // 新增代码+DesktopGuiClient：读取状态事件；如果没有这段，工具进度和运行状态无法刷新。
      const query = sinceSequence === null ? `limit=${limit}` : `since_sequence=${sinceSequence}&limit=${limit}`; // 新增代码+DesktopGuiClient：构造事件轮询 query；如果没有这行，后端不知道从哪个游标开始返回。
      return requestJson<GuiEventPayload>(`/v1/gui/events?${query}`); // 新增代码+DesktopGuiClient：请求事件 endpoint；如果没有这行，状态时间线没有后端事件来源。
    }, // 新增代码+DesktopGuiClient：events 方法结束；如果没有这行，返回对象语法不完整。
    sessions(): Promise<GuiSessionsPayload> { // 新增代码+DesktopGUISessionsClient：读取项目会话列表；如果没有这段，侧栏无法从后端加载真实 sessions。
      return requestJson<GuiSessionsPayload>("/v1/gui/sessions"); // 新增代码+DesktopGUISessionsClient：请求 sessions endpoint；如果没有这行，最近会话只能是静态占位。
    }, // 新增代码+DesktopGUISessionsClient：sessions 方法结束；如果没有这行，返回对象语法不完整。
    browserProviders(): Promise<GuiBrowserProvidersPayload> { // 新增代码+DesktopGUIBrowserPanelClient：读取浏览器 provider 状态；如果没有这段，右侧浏览器面板无法加载真实 provider_status。
      return requestJson<GuiBrowserProvidersPayload>("/v1/gui/browser/providers"); // 新增代码+DesktopGUIBrowserPanelClient：请求 browser providers endpoint；如果没有这行，浏览器面板只能显示静态占位。
    }, // 新增代码+DesktopGUIBrowserPanelClient：browserProviders 方法结束；如果没有这行，返回对象语法不完整。
    sendMessage(prompt: string, conversationId = "default"): Promise<SendMessageResponse> { // 新增代码+DesktopGUILifecycleClient：发送用户 prompt；如果没有这段，composer 无法创建后端 turn。
      return postJson<SendMessageResponse>("/v1/gui/messages", { conversation_id: conversationId, prompt }); // 新增代码+DesktopGUILifecycleClient：请求 messages endpoint；如果没有这行，用户输入不会进入 bridge。
    }, // 新增代码+DesktopGUILifecycleClient：sendMessage 方法结束；如果没有这行，返回对象语法不完整。
    cancelTurn(turnId: string): Promise<CancelTurnResponse> { // 新增代码+DesktopGUILifecycleClient：请求取消 turn；如果没有这段，取消按钮没有后端动作。
      return postJson<CancelTurnResponse>(`/v1/gui/turns/${turnId}/cancel`, {}); // 新增代码+DesktopGUILifecycleClient：请求 cancel endpoint；如果没有这行，后端不会写取消事件。
    }, // 新增代码+DesktopGUILifecycleClient：cancelTurn 方法结束；如果没有这行，返回对象语法不完整。
    retryTurn(turnId: string): Promise<SendMessageResponse> { // 新增代码+DesktopGUILifecycleClient：请求重试 turn；如果没有这段，重试按钮没有后端动作。
      return postJson<SendMessageResponse>(`/v1/gui/turns/${turnId}/retry`, {}); // 新增代码+DesktopGUILifecycleClient：请求 retry endpoint；如果没有这行，后端不会创建 linked turn。
    }, // 新增代码+DesktopGUILifecycleClient：retryTurn 方法结束；如果没有这行，返回对象语法不完整。
    resumeSession(sessionId: string): Promise<ResumeSessionResponse> { // 新增代码+DesktopGUILifecycleClient：恢复历史 session；如果没有这段，窗口重启无法重建消息。
      return postJson<ResumeSessionResponse>(`/v1/gui/sessions/${sessionId}/resume`, {}); // 新增代码+DesktopGUILifecycleClient：请求 resume endpoint；如果没有这行，前端无法拿到后端恢复数据。
    }, // 新增代码+DesktopGUILifecycleClient：resumeSession 方法结束；如果没有这行，返回对象语法不完整。
    decidePermission(requestId: string, turnId: string, decision: "approve" | "deny", reason: string): Promise<PermissionDecisionResponse> { // 新增代码+DesktopGUIPermissionsClient：提交权限允许或拒绝意图；如果没有这段，权限弹窗按钮无法进入后端审计。
      return postJson<PermissionDecisionResponse>(`/v1/gui/permissions/${requestId}/decision`, { turn_id: turnId, decision, reason }); // 新增代码+DesktopGUIPermissionsClient：请求权限决策 endpoint；如果没有这行，前端会绕过真实权限 machinery。
    }, // 新增代码+DesktopGUIPermissionsClient：decidePermission 方法结束；如果没有这行，返回对象语法不完整。
  }; // 新增代码+DesktopGuiClient：client 对象返回结束；如果没有这行，createGuiClient 没有返回值。
} // 新增代码+DesktopGuiClient：函数段结束，createGuiClient 到此结束；如果没有这个边界，用户不容易看出 API client 范围。
