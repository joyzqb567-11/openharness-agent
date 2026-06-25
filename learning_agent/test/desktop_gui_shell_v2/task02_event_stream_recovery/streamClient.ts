import { GUI_V2_TOKEN_HEADER } from "./guiTypes"; // 新增代码+GuiV2StreamClient：复用 V2 token header 常量；如果没有这一行，fallback 轮询可能和后端认证字段分裂。
import type { GuiV2Event, GuiV2EventKind } from "./guiTypes"; // 新增代码+GuiV2StreamClient：导入 V2 事件类型；如果没有这一行，stream client 只能传递不透明对象。

type FetchLike = typeof fetch; // 新增代码+GuiV2StreamClient：抽象 fetch 类型；如果没有这一行，测试无法注入假的 long polling 网络层。
type EventSourceListener = (event: MessageEvent<string>) => void; // 新增代码+GuiV2StreamClient：定义 EventSource listener 形状；如果没有这一行，fake EventSource 和浏览器类型边界不清楚。

export type GuiEventSourceLike = { // 新增代码+GuiV2StreamClient：类型段开始，描述 stream client 需要的 EventSource 子集；如果没有这段，测试 fake 必须实现完整浏览器接口。
  onerror: ((event: Event) => void) | null; // 新增代码+GuiV2StreamClient：保存错误回调；如果没有这一行，断线错误无法传给调用方。
  addEventListener(type: string, listener: EventSourceListener): void; // 新增代码+GuiV2StreamClient：注册事件监听；如果没有这一行，client 无法接收 named SSE events。
  close(): void; // 新增代码+GuiV2StreamClient：关闭连接；如果没有这一行，窗口卸载时会泄漏连接。
}; // 新增代码+GuiV2StreamClient：EventSource 子集类型结束；如果没有这一行，TypeScript 类型语法不完整。

export type GuiEventSourceConstructor = new (url: string) => GuiEventSourceLike; // 新增代码+GuiV2StreamClient：定义可注入 EventSource 构造器；如果没有这一行，单测无法替换浏览器全局对象。

export type GuiEventStreamOptions = { // 新增代码+GuiV2StreamClient：类型段开始，定义连接 V2 事件流所需参数；如果没有这段，调用方容易漏传 token 或游标。
  baseUrl: string; // 新增代码+GuiV2StreamClient：bridge base URL；如果没有这一行，client 不知道连接哪个后端。
  bridgeToken: string; // 新增代码+GuiV2StreamClient：本地 bridge token；如果没有这一行，后端会拒绝事件请求。
  sinceSequence: number; // 新增代码+GuiV2StreamClient：断线恢复游标；如果没有这一行，重连会重复读取旧事件。
  onEvent(event: GuiV2Event): void; // 新增代码+GuiV2StreamClient：事件回调；如果没有这一行，调用方拿不到后端事件。
  onError(error: unknown): void; // 新增代码+GuiV2StreamClient：错误回调；如果没有这一行，断线或坏 JSON 只能静默失败。
  EventSourceImpl?: GuiEventSourceConstructor; // 新增代码+GuiV2StreamClient：可注入 EventSource；如果没有这一行，测试和非浏览器环境无法控制主路径。
  fetcher?: FetchLike; // 新增代码+GuiV2StreamClient：可注入 fetch；如果没有这一行，fallback 测试会依赖真实网络。
  pollingIntervalMs?: number; // 新增代码+GuiV2StreamClient：fallback 轮询间隔；如果没有这一行，测试无法关闭重复计时器。
}; // 新增代码+GuiV2StreamClient：连接参数类型结束；如果没有这一行，TypeScript 类型语法不完整。

export type GuiEventStreamConnection = { // 新增代码+GuiV2StreamClient：类型段开始，描述 stream 连接句柄；如果没有这段，调用方无法关闭连接或读取最新游标。
  mode: "eventsource" | "polling"; // 新增代码+GuiV2StreamClient：记录实际连接模式；如果没有这一行，诊断时不知道是否退回轮询。
  ready: Promise<void>; // 新增代码+GuiV2StreamClient：暴露首次连接或首次轮询完成信号；如果没有这一行，测试和 UI 无法等待初始数据。
  close(): void; // 新增代码+GuiV2StreamClient：关闭连接；如果没有这一行，组件卸载会泄漏连接或定时器。
  lastSequence(): number; // 新增代码+GuiV2StreamClient：读取最新 sequence；如果没有这一行，手动重连无法从正确游标继续。
}; // 新增代码+GuiV2StreamClient：连接句柄类型结束；如果没有这一行，TypeScript 类型语法不完整。

const GUI_V2_EVENT_TYPES: GuiV2EventKind[] = [ // 新增代码+GuiV2StreamClient：数组段开始，列出 EventSource 要监听的 named events；如果没有这段，SSE 只会收到默认 message。
  "turn_started", // 新增代码+GuiV2StreamClient：监听 turn_started；如果没有这一项，运行起点不会派发。
  "message_delta", // 新增代码+GuiV2StreamClient：监听 message_delta；如果没有这一项，流式文本不会派发。
  "message_completed", // 新增代码+GuiV2StreamClient：监听 message_completed；如果没有这一项，完成消息不会派发。
  "tool_started", // 新增代码+GuiV2StreamClient：监听 tool_started；如果没有这一项，工具起点不会派发。
  "tool_finished", // 新增代码+GuiV2StreamClient：监听 tool_finished；如果没有这一项，工具结果不会派发。
  "permission_requested", // 新增代码+GuiV2StreamClient：监听 permission_requested；如果没有这一项，权限弹窗不会出现。
  "permission_answered", // 新增代码+GuiV2StreamClient：监听 permission_answered；如果没有这一项，权限弹窗不会闭合。
  "safety_refusal", // 新增代码+GuiV2StreamClient：监听 safety_refusal；如果没有这一项，安全拒绝不会作为消息事件。
  "turn_failed", // 新增代码+GuiV2StreamClient：监听 turn_failed；如果没有这一项，失败态不会派发。
  "turn_cancelled", // 新增代码+GuiV2StreamClient：监听 turn_cancelled；如果没有这一项，取消态不会派发。
  "heartbeat", // 新增代码+GuiV2StreamClient：监听 heartbeat；如果没有这一项，保活事件不会更新诊断。
]; // 新增代码+GuiV2StreamClient：数组段结束；如果没有这一行，TypeScript 数组语法不完整。

function normalizedBaseUrl(baseUrl: string): string { // 新增代码+GuiV2StreamClient：函数段开始，规范化 bridge base URL；如果没有这段，请求 URL 可能出现双斜杠。
  return baseUrl.replace(/\/$/, ""); // 新增代码+GuiV2StreamClient：去掉末尾斜杠；如果没有这一行，拼接路径会不稳定。
} // 新增代码+GuiV2StreamClient：函数段结束，normalizedBaseUrl 到此结束；如果没有这一行，函数语法不完整。

function buildStreamUrl(baseUrl: string, bridgeToken: string, sinceSequence: number): string { // 新增代码+GuiV2StreamClient：函数段开始，生成 EventSource URL；如果没有这段，query token 和游标拼接会散落。
  const query = new URLSearchParams({ since_sequence: String(sinceSequence), token: bridgeToken }); // 新增代码+GuiV2StreamClient：编码 since_sequence 和 token；如果没有这一行，空格或特殊字符会破坏 URL。
  return `${normalizedBaseUrl(baseUrl)}/v2/gui/events/stream?${query.toString()}`; // 新增代码+GuiV2StreamClient：返回完整 SSE URL；如果没有这一行，EventSource 无法连接后端。
} // 新增代码+GuiV2StreamClient：函数段结束，buildStreamUrl 到此结束；如果没有这一行，函数语法不完整。

function buildPollingUrl(baseUrl: string, sinceSequence: number): string { // 新增代码+GuiV2StreamClient：函数段开始，生成 long polling fallback URL；如果没有这段，重连游标拼接会重复。
  const query = new URLSearchParams({ since_sequence: String(sinceSequence), limit: "50" }); // 新增代码+GuiV2StreamClient：编码 since_sequence 和 limit；如果没有这一行，fallback 可能重复拉全量。
  return `${normalizedBaseUrl(baseUrl)}/v2/gui/events?${query.toString()}`; // 新增代码+GuiV2StreamClient：返回完整 fallback URL；如果没有这一行，fetch 不知道请求哪里。
} // 新增代码+GuiV2StreamClient：函数段结束，buildPollingUrl 到此结束；如果没有这一行，函数语法不完整。

function isRecord(value: unknown): value is Record<string, unknown> { // 新增代码+GuiV2StreamClient：函数段开始，判断未知 JSON 是否是对象；如果没有这段，坏事件会导致字段读取异常。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 新增代码+GuiV2StreamClient：只接受普通对象；如果没有这一行，数组或 null 会被误当事件。
} // 新增代码+GuiV2StreamClient：函数段结束，isRecord 到此结束；如果没有这一行，函数语法不完整。

function isGuiV2Event(value: unknown): value is GuiV2Event { // 新增代码+GuiV2StreamClient：函数段开始，校验未知数据是否像 V2 事件；如果没有这段，坏 JSON 会进入 UI reducer。
  return isRecord(value) && typeof value.sequence === "number" && typeof value.kind === "string" && isRecord(value.payload); // 新增代码+GuiV2StreamClient：检查最关键字段；如果没有这一行，事件类型和 payload 可能不稳定。
} // 新增代码+GuiV2StreamClient：函数段结束，isGuiV2Event 到此结束；如果没有这一行，函数语法不完整。

function parseStreamEvent(rawData: string): GuiV2Event { // 新增代码+GuiV2StreamClient：函数段开始，解析 SSE data JSON；如果没有这段，EventSource 事件无法转成 GUI 事件。
  const parsed = JSON.parse(rawData) as unknown; // 新增代码+GuiV2StreamClient：解析 JSON 字符串；如果没有这一行，onEvent 只能收到原始文本。
  if (!isGuiV2Event(parsed)) { // 新增代码+GuiV2StreamClient：验证解析结果；如果没有这一行，坏事件会悄悄进入 UI。
    throw new Error("Invalid GUI V2 stream event."); // 新增代码+GuiV2StreamClient：抛出可读错误；如果没有这一行，调用方不知道事件格式坏了。
  } // 新增代码+GuiV2StreamClient：事件校验分支结束；如果没有这一行，if 语法不完整。
  return parsed; // 新增代码+GuiV2StreamClient：返回类型化事件；如果没有这一行，调用方拿不到事件。
} // 新增代码+GuiV2StreamClient：函数段结束，parseStreamEvent 到此结束；如果没有这一行，函数语法不完整。

export function connectGuiEventStream(options: GuiEventStreamOptions): GuiEventStreamConnection { // 新增代码+GuiV2StreamClient：函数段开始，连接 GUI V2 事件流；如果没有这段，renderer 只能继续手写轮询。
  let closed = false; // 新增代码+GuiV2StreamClient：记录连接是否已关闭；如果没有这一行，异步轮询可能在关闭后继续派发。
  let latestSequence = options.sinceSequence; // 新增代码+GuiV2StreamClient：保存当前重连游标；如果没有这一行，断线恢复不知道最后事件。
  const fetcher = options.fetcher ?? fetch; // 新增代码+GuiV2StreamClient：选择注入 fetch 或全局 fetch；如果没有这一行，fallback 无法发请求。
  const pollingIntervalMs = options.pollingIntervalMs ?? 1000; // 新增代码+GuiV2StreamClient：设置默认轮询间隔；如果没有这一行，fallback 重复请求没有节奏。
  const EventSourceImpl = options.EventSourceImpl ?? (typeof EventSource === "undefined" ? undefined : EventSource); // 新增代码+GuiV2StreamClient：选择注入 EventSource 或浏览器全局；如果没有这一行，非浏览器环境会抛 ReferenceError。

  const dispatchEvent = (event: GuiV2Event): void => { // 新增代码+GuiV2StreamClient：函数段开始，统一派发事件并更新游标；如果没有这段，EventSource 和 polling 会重复逻辑。
    latestSequence = Math.max(latestSequence, event.sequence); // 新增代码+GuiV2StreamClient：更新最新 sequence；如果没有这一行，下一次重连会重复旧事件。
    options.onEvent(event); // 新增代码+GuiV2StreamClient：把事件交给调用方；如果没有这一行，UI 收不到更新。
  }; // 新增代码+GuiV2StreamClient：函数段结束，dispatchEvent 到此结束；如果没有这一行，箭头函数语法不完整。

  if (EventSourceImpl) { // 新增代码+GuiV2StreamClient：优先使用 EventSource；如果没有这一行，支持 SSE 的环境也会退回轮询。
    const source = new EventSourceImpl(buildStreamUrl(options.baseUrl, options.bridgeToken, latestSequence)); // 新增代码+GuiV2StreamClient：创建 SSE 连接；如果没有这一行，事件流不会启动。
    for (const eventType of GUI_V2_EVENT_TYPES) { // 新增代码+GuiV2StreamClient：注册所有 V2 named events；如果没有这一行，只有默认 message 事件会被处理。
      source.addEventListener(eventType, (messageEvent) => { // 新增代码+GuiV2StreamClient：给当前事件类型注册回调；如果没有这一行，该类型事件不会派发。
        try { // 新增代码+GuiV2StreamClient：保护 JSON 解析；如果没有这一行，单个坏事件会抛到全局。
          dispatchEvent(parseStreamEvent(messageEvent.data)); // 新增代码+GuiV2StreamClient：解析并派发事件；如果没有这一行，SSE data 不会进入 UI。
        } catch (error) { // 新增代码+GuiV2StreamClient：捕获坏事件错误；如果没有这一行，onError 收不到解析失败。
          options.onError(error); // 新增代码+GuiV2StreamClient：上报解析错误；如果没有这一行，坏事件会静默失败。
        } // 新增代码+GuiV2StreamClient：解析保护结束；如果没有这一行，try/catch 语法不完整。
      }); // 新增代码+GuiV2StreamClient：当前事件类型监听结束；如果没有这一行，addEventListener 调用语法不完整。
    } // 新增代码+GuiV2StreamClient：事件类型循环结束；如果没有这一行，for 循环语法不完整。
    source.onerror = (event) => { // 新增代码+GuiV2StreamClient：注册 EventSource 错误回调；如果没有这一行，断线错误无法进入 UI。
      options.onError(event); // 新增代码+GuiV2StreamClient：把错误交给调用方；如果没有这一行，连接失败只会在浏览器内部发生。
    }; // 新增代码+GuiV2StreamClient：错误回调结束；如果没有这一行，赋值语法不完整。
    return { mode: "eventsource", ready: Promise.resolve(), close: () => { closed = true; source.close(); }, lastSequence: () => latestSequence }; // 新增代码+GuiV2StreamClient：返回 SSE 连接句柄；如果没有这一行，调用方无法关闭或读取游标。
  } // 新增代码+GuiV2StreamClient：EventSource 分支结束；如果没有这一行，条件块语法不完整。

  let timer: ReturnType<typeof setInterval> | undefined; // 新增代码+GuiV2StreamClient：保存 fallback 轮询计时器；如果没有这一行，close 无法清理重复请求。
  const pollOnce = async (): Promise<void> => { // 新增代码+GuiV2StreamClient：函数段开始，执行一次 fallback 轮询；如果没有这段，无 EventSource 环境无法更新事件。
    if (closed) { // 新增代码+GuiV2StreamClient：关闭后不再请求；如果没有这一行，组件卸载后仍可能派发事件。
      return; // 新增代码+GuiV2StreamClient：已关闭时直接返回；如果没有这一行，仍会继续 fetch。
    } // 新增代码+GuiV2StreamClient：关闭检查结束；如果没有这一行，if 语法不完整。
    try { // 新增代码+GuiV2StreamClient：保护网络请求；如果没有这一行，fetch 错误会变成未处理 promise。
      const response = await fetcher(buildPollingUrl(options.baseUrl, latestSequence), { headers: { [GUI_V2_TOKEN_HEADER]: options.bridgeToken } }); // 新增代码+GuiV2StreamClient：请求 V2 fallback 事件；如果没有这一行，轮询没有数据来源。
      if (!response.ok) { // 新增代码+GuiV2StreamClient：检查 HTTP 成功状态；如果没有这一行，错误响应会被当成事件 payload。
        throw new Error(`GUI V2 event polling failed: ${response.status}`); // 新增代码+GuiV2StreamClient：抛出可读轮询错误；如果没有这一行，调用方不知道状态码。
      } // 新增代码+GuiV2StreamClient：HTTP 状态检查结束；如果没有这一行，if 语法不完整。
      const payload = (await response.json()) as unknown; // 新增代码+GuiV2StreamClient：解析 fallback JSON；如果没有这一行，client 拿不到事件数组。
      const events = isRecord(payload) && Array.isArray(payload.events) ? payload.events : []; // 新增代码+GuiV2StreamClient：安全读取 events 数组；如果没有这一行，坏 payload 会拖垮 UI。
      for (const event of events) { // 新增代码+GuiV2StreamClient：遍历 fallback 事件；如果没有这一行，轮询数据不会派发。
        if (isGuiV2Event(event)) { // 新增代码+GuiV2StreamClient：只派发合法 V2 事件；如果没有这一行，坏事件会进入 reducer。
          dispatchEvent(event); // 新增代码+GuiV2StreamClient：派发合法事件；如果没有这一行，UI 收不到 fallback 更新。
        } // 新增代码+GuiV2StreamClient：事件校验分支结束；如果没有这一行，if 语法不完整。
      } // 新增代码+GuiV2StreamClient：事件循环结束；如果没有这一行，for 循环语法不完整。
    } catch (error) { // 新增代码+GuiV2StreamClient：捕获网络或 JSON 错误；如果没有这一行，fallback 错误会变成未处理 promise。
      if (!closed) { // 新增代码+GuiV2StreamClient：只在未关闭时上报错误；如果没有这一行，关闭后的预期中断也会打扰 UI。
        options.onError(error); // 新增代码+GuiV2StreamClient：上报 fallback 错误；如果没有这一行，用户看不到断线问题。
      } // 新增代码+GuiV2StreamClient：关闭判断结束；如果没有这一行，if 语法不完整。
    } // 新增代码+GuiV2StreamClient：轮询保护结束；如果没有这一行，try/catch 语法不完整。
  }; // 新增代码+GuiV2StreamClient：函数段结束，pollOnce 到此结束；如果没有这一行，箭头函数语法不完整。
  const ready = pollOnce(); // 新增代码+GuiV2StreamClient：立即执行首次 fallback 轮询；如果没有这一行，UI 要等一个间隔才看到事件。
  if (pollingIntervalMs > 0) { // 新增代码+GuiV2StreamClient：只有正间隔才开启重复轮询；如果没有这一行，测试无法禁用计时器。
    timer = setInterval(() => { void pollOnce(); }, pollingIntervalMs); // 新增代码+GuiV2StreamClient：定时重复轮询；如果没有这一行，fallback 只能拿到首次事件。
  } // 新增代码+GuiV2StreamClient：计时器判断结束；如果没有这一行，if 语法不完整。
  return { mode: "polling", ready, close: () => { closed = true; if (timer) { clearInterval(timer); } }, lastSequence: () => latestSequence }; // 新增代码+GuiV2StreamClient：返回 fallback 连接句柄；如果没有这一行，调用方无法关闭轮询或读取游标。
} // 新增代码+GuiV2StreamClient：函数段结束，connectGuiEventStream 到此结束；如果没有这一行，函数语法不完整。
