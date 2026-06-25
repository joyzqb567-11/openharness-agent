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

  return { // 新增代码+DesktopGuiClient：返回面向 UI 的 client 方法；如果没有这行，调用方无法使用封装能力。
    bootstrap(): Promise<GuiBootstrapPayload> { // 新增代码+DesktopGuiClient：读取 GUI 启动数据；如果没有这段，桌面首屏无法加载后端状态。
      return requestJson<GuiBootstrapPayload>("/v1/gui/bootstrap"); // 新增代码+DesktopGuiClient：请求 bootstrap endpoint；如果没有这行，窗口只能显示静态假数据。
    }, // 新增代码+DesktopGuiClient：bootstrap 方法结束；如果没有这行，返回对象语法不完整。
    events(sinceSequence: number | null, limit = 50): Promise<GuiEventPayload> { // 新增代码+DesktopGuiClient：读取状态事件；如果没有这段，工具进度和运行状态无法刷新。
      const query = sinceSequence === null ? `limit=${limit}` : `since_sequence=${sinceSequence}&limit=${limit}`; // 新增代码+DesktopGuiClient：构造事件轮询 query；如果没有这行，后端不知道从哪个游标开始返回。
      return requestJson<GuiEventPayload>(`/v1/gui/events?${query}`); // 新增代码+DesktopGuiClient：请求事件 endpoint；如果没有这行，状态时间线没有后端事件来源。
    }, // 新增代码+DesktopGuiClient：events 方法结束；如果没有这行，返回对象语法不完整。
  }; // 新增代码+DesktopGuiClient：client 对象返回结束；如果没有这行，createGuiClient 没有返回值。
} // 新增代码+DesktopGuiClient：函数段结束，createGuiClient 到此结束；如果没有这个边界，用户不容易看出 API client 范围。
