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

type FetchLike = typeof fetch; // 新增代码+DesktopGuiClient：抽象 fetch 形状；如果没有这行，测试无法注入假的网络层。

export function createGuiClient(baseUrl: string, bridgeToken: string, fetcher: FetchLike = fetch) { // 新增代码+DesktopGuiClient：函数段开始，创建 GUI bridge 客户端；如果没有这段，渲染进程会到处手写 fetch。
  const normalizedBaseUrl = baseUrl.replace(/\/$/, ""); // 新增代码+DesktopGuiClient：去掉 baseUrl 末尾斜杠；如果没有这行，请求 URL 可能出现双斜杠。
  const headers = { "X-OpenHarness-Desktop-Token": bridgeToken }; // 新增代码+DesktopGuiClient：统一 token header；如果没有这行，安全 endpoint 会拒绝 GUI 请求。

  async function requestJson<T>(path: string): Promise<T> { // 新增代码+DesktopGuiClient：函数段开始，封装 GET JSON 请求；如果没有这段，bootstrap 和 events 会重复网络错误处理。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { headers }); // 新增代码+DesktopGuiClient：发送带 token 的请求；如果没有这行，前端无法和 bridge 通信。
    if (!response.ok) { // 新增代码+DesktopGuiClient：检查 HTTP 成功状态；如果没有这行，错误响应会被当成正常数据渲染。
      throw new Error(`GUI bridge request failed: ${response.status}`); // 新增代码+DesktopGuiClient：抛出可读错误；如果没有这行，调用方只会看到后续字段访问异常。
    } // 新增代码+DesktopGuiClient：错误分支结束；如果没有这行，条件块语法不完整。
    return (await response.json()) as T; // 新增代码+DesktopGuiClient：解析并返回 JSON；如果没有这行，调用方拿不到 bridge payload。
  } // 新增代码+DesktopGuiClient：函数段结束，requestJson 到此结束；如果没有这个边界，用户不容易看出 GET 请求封装范围。

  async function postJson<T>(path: string, payload: Record<string, unknown>): Promise<T> { // 新增代码+DesktopGUILifecycleClient：函数段开始，封装 POST JSON 请求；如果没有这段，send/cancel/retry 会重复写网络逻辑。
    const response = await fetcher(`${normalizedBaseUrl}${path}`, { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(payload) }); // 新增代码+DesktopGUILifecycleClient：发送带 token 的 JSON POST；如果没有这行，前端无法调用生命周期端点。
    if (!response.ok) { // 新增代码+DesktopGUILifecycleClient：检查 HTTP 成功状态；如果没有这行，409 busy 会被当作正常响应。
      throw new Error(`GUI bridge request failed: ${response.status}`); // 新增代码+DesktopGUILifecycleClient：抛出可读错误；如果没有这行，调用方只会看到 JSON 字段异常。
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
  }; // 新增代码+DesktopGuiClient：client 对象返回结束；如果没有这行，createGuiClient 没有返回值。
} // 新增代码+DesktopGuiClient：函数段结束，createGuiClient 到此结束；如果没有这个边界，用户不容易看出 API client 范围。
