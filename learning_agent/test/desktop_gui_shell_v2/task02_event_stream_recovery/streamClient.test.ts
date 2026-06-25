import { describe, expect, it, vi } from "vitest"; // 新增代码+GuiV2StreamClientTest：引入 Vitest 测试工具；如果没有这一行，stream client 合同无法自动验证。
import { connectGuiEventStream } from "../src/api/streamClient"; // 新增代码+GuiV2StreamClientTest：导入待实现事件流 client；如果没有这一行，测试没有被测对象。
import type { GuiV2Event } from "../src/api/guiTypes"; // 新增代码+GuiV2StreamClientTest：导入 V2 事件类型；如果没有这一行，测试事件样本会是不透明对象。

class FakeEventSource { // 新增代码+GuiV2StreamClientTest：类段开始，模拟浏览器 EventSource；如果没有这个 fake，单测会依赖真实浏览器。
  static instances: FakeEventSource[] = []; // 新增代码+GuiV2StreamClientTest：记录创建过的实例；如果没有这一行，测试无法检查连接 URL。
  url: string; // 新增代码+GuiV2StreamClientTest：保存 EventSource URL；如果没有这一行，测试无法确认 query token 和 since_sequence。
  closed = false; // 新增代码+GuiV2StreamClientTest：记录 close 是否被调用；如果没有这一行，测试无法确认清理。
  listeners = new Map<string, Array<(event: MessageEvent<string>) => void>>(); // 新增代码+GuiV2StreamClientTest：保存事件监听器；如果没有这一行，测试无法手动触发 V2 事件。
  onerror: ((event: Event) => void) | null = null; // 新增代码+GuiV2StreamClientTest：保存错误回调；如果没有这一行，client 的 onerror 分支无法挂载。

  constructor(url: string) { // 新增代码+GuiV2StreamClientTest：函数段开始，保存 EventSource 构造参数；如果没有这段，测试无法看到连接 URL。
    this.url = url; // 新增代码+GuiV2StreamClientTest：记录 URL；如果没有这一行，断言没有输入。
    FakeEventSource.instances.push(this); // 新增代码+GuiV2StreamClientTest：记录实例；如果没有这一行，测试找不到 fake 实例。
  } // 新增代码+GuiV2StreamClientTest：函数段结束，FakeEventSource.constructor 到此结束；如果没有这一行，类构造函数语法不完整。

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void { // 新增代码+GuiV2StreamClientTest：函数段开始，模拟 EventSource.addEventListener；如果没有这段，client 无法注册事件回调。
    const listeners = this.listeners.get(type) ?? []; // 新增代码+GuiV2StreamClientTest：读取当前类型监听器；如果没有这一行，多监听器会覆盖彼此。
    listeners.push(listener); // 新增代码+GuiV2StreamClientTest：追加监听器；如果没有这一行，emit 时没有回调。
    this.listeners.set(type, listeners); // 新增代码+GuiV2StreamClientTest：写回监听器数组；如果没有这一行，监听器不会被保存。
  } // 新增代码+GuiV2StreamClientTest：函数段结束，addEventListener 到此结束；如果没有这一行，函数语法不完整。

  emit(type: string, event: GuiV2Event): void { // 新增代码+GuiV2StreamClientTest：函数段开始，手动触发 SSE 事件；如果没有这段，测试无法模拟后端推送。
    for (const listener of this.listeners.get(type) ?? []) { // 新增代码+GuiV2StreamClientTest：遍历当前类型监听器；如果没有这一行，事件不会送到 client。
      listener({ data: JSON.stringify(event) } as MessageEvent<string>); // 新增代码+GuiV2StreamClientTest：用 JSON data 调用监听器；如果没有这一行，onEvent 不会被触发。
    } // 新增代码+GuiV2StreamClientTest：监听器循环结束；如果没有这一行，for 循环语法不完整。
  } // 新增代码+GuiV2StreamClientTest：函数段结束，emit 到此结束；如果没有这一行，函数语法不完整。

  close(): void { // 新增代码+GuiV2StreamClientTest：函数段开始，模拟关闭连接；如果没有这段，client.close 无法被验证。
    this.closed = true; // 新增代码+GuiV2StreamClientTest：记录已关闭；如果没有这一行，测试无法确认资源释放。
  } // 新增代码+GuiV2StreamClientTest：函数段结束，close 到此结束；如果没有这一行，函数语法不完整。
} // 新增代码+GuiV2StreamClientTest：类段结束，FakeEventSource 到此结束；如果没有这一行，TypeScript 类语法不完整。

describe("connectGuiEventStream", () => { // 新增代码+GuiV2StreamClientTest：测试段开始，覆盖 V2 GUI stream client；如果没有这段，Vitest 不会组织这些断言。
  it("uses EventSource with query token and dispatches typed events", () => { // 新增代码+GuiV2StreamClientTest：验证 EventSource 主路径；如果没有这段，query token 和 SSE 监听可能回归。
    FakeEventSource.instances = []; // 新增代码+GuiV2StreamClientTest：清空 fake 实例；如果没有这一行，前一个测试会污染当前断言。
    const onEvent = vi.fn(); // 新增代码+GuiV2StreamClientTest：创建事件回调 spy；如果没有这一行，无法确认事件被派发。
    const onError = vi.fn(); // 新增代码+GuiV2StreamClientTest：创建错误回调 spy；如果没有这一行，无法确认正常事件不报错。
    const connection = connectGuiEventStream({ baseUrl: "http://127.0.0.1:8776/", bridgeToken: "test token", sinceSequence: 7, onEvent, onError, EventSourceImpl: FakeEventSource }); // 新增代码+GuiV2StreamClientTest：建立 EventSource 连接；如果没有这一行，测试没有行为。
    const source = FakeEventSource.instances[0]; // 新增代码+GuiV2StreamClientTest：读取 fake EventSource 实例；如果没有这一行，无法检查 URL 或触发事件。
    expect(connection.mode).toBe("eventsource"); // 新增代码+GuiV2StreamClientTest：确认使用 EventSource 模式；如果没有这一行，主路径可能退回轮询。
    expect(source.url).toBe("http://127.0.0.1:8776/v2/gui/events/stream?since_sequence=7&token=test+token"); // 新增代码+GuiV2StreamClientTest：确认 query token 和游标被编码；如果没有这一行，EventSource 认证或断线恢复会失败。
    source.emit("turn_started", { sequence: 8, event_id: "event_8", kind: "turn_started", created_at: "now", run_id: "run_a", turn_id: "turn_a", payload: { status: "running" } }); // 新增代码+GuiV2StreamClientTest：模拟后端推送 turn_started；如果没有这一行，无法验证 onEvent。
    expect(onEvent).toHaveBeenCalledWith(expect.objectContaining({ sequence: 8, kind: "turn_started" })); // 新增代码+GuiV2StreamClientTest：确认事件被传给调用方；如果没有这一行，stream client 可能吞事件。
    expect(connection.lastSequence()).toBe(8); // 新增代码+GuiV2StreamClientTest：确认 lastSequence 更新；如果没有这一行，重连游标会停在旧位置。
    connection.close(); // 新增代码+GuiV2StreamClientTest：关闭连接；如果没有这一行，测试无法验证清理。
    expect(source.closed).toBe(true); // 新增代码+GuiV2StreamClientTest：确认 fake source 被关闭；如果没有这一行，EventSource 可能泄漏。
  }); // 新增代码+GuiV2StreamClientTest：EventSource 测试结束；如果没有这一行，测试块语法不完整。

  it("falls back to long polling and updates reconnect sequence", async () => { // 新增代码+GuiV2StreamClientTest：验证无 EventSource 时的 long polling；如果没有这段，桌面壳在不能传 header 的环境会断流。
    const onEvent = vi.fn(); // 新增代码+GuiV2StreamClientTest：创建事件回调 spy；如果没有这一行，无法确认轮询事件被派发。
    const fetchMock = vi.fn(async () => ({ // 新增代码+GuiV2StreamClientTest：创建 fallback fetch mock；如果没有这一行，测试会请求真实后端。
      ok: true, // 新增代码+GuiV2StreamClientTest：模拟 HTTP 成功；如果没有这一行，client 会走错误分支。
      status: 200, // 新增代码+GuiV2StreamClientTest：模拟成功状态码；如果没有这一行，响应形状不完整。
      json: async () => ({ ok: true, events: [{ sequence: 9, event_id: "event_9", kind: "message_completed", created_at: "now", run_id: "run_a", turn_id: "turn_a", payload: { final_text: "done" } }], since_sequence: 8, limit: 50 }), // 新增代码+GuiV2StreamClientTest：模拟 V2 fallback payload；如果没有这一行，无法验证断线恢复游标。
    })) as unknown as typeof fetch; // 新增代码+GuiV2StreamClientTest：把 mock 转成 fetch 类型；如果没有这一行，TypeScript 不接受测试 fetch。
    const connection = connectGuiEventStream({ baseUrl: "http://127.0.0.1:8776", bridgeToken: "test-token", sinceSequence: 8, onEvent, onError: vi.fn(), EventSourceImpl: undefined, fetcher: fetchMock, pollingIntervalMs: 0 }); // 新增代码+GuiV2StreamClientTest：建立 fallback 连接且不启用重复计时器；如果没有这一行，测试没有行为。
    await connection.ready; // 新增代码+GuiV2StreamClientTest：等待首次轮询完成；如果没有这一行，断言可能早于异步请求。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v2/gui/events?since_sequence=8&limit=50", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+GuiV2StreamClientTest：确认 fallback 使用 header token 和 since_sequence；如果没有这一行，重连请求可能错位。
    expect(onEvent).toHaveBeenCalledWith(expect.objectContaining({ sequence: 9, kind: "message_completed" })); // 新增代码+GuiV2StreamClientTest：确认 fallback 事件派发；如果没有这一行，轮询可能拿到数据但不更新 UI。
    expect(connection.lastSequence()).toBe(9); // 新增代码+GuiV2StreamClientTest：确认轮询后更新 lastSequence；如果没有这一行，下一次请求会重复旧事件。
    connection.close(); // 新增代码+GuiV2StreamClientTest：关闭 fallback 连接；如果没有这一行，计时器可能泄漏。
  }); // 新增代码+GuiV2StreamClientTest：fallback 测试结束；如果没有这一行，测试块语法不完整。
}); // 新增代码+GuiV2StreamClientTest：测试段结束；如果没有这一行，describe 语法不完整。
