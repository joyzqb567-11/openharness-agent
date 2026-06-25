import { describe, expect, it, vi } from "vitest"; // 新增代码+DesktopGuiClientTest：引入 Vitest 测试工具；如果没有这行，API client 合同无法自动验证。
import { createGuiClient } from "../src/api/guiClient"; // 新增代码+DesktopGuiClientTest：导入 GUI client 工厂；如果没有这行，测试无法锁定前端和 bridge 的调用形状。

describe("createGuiClient", () => { // 新增代码+DesktopGuiClientTest：测试段开始，覆盖 GUI bridge 前端客户端；如果没有这段，后续改动容易漏掉 token header。
  it("loads bootstrap payload from the GUI bridge", async () => { // 新增代码+DesktopGuiClientTest：验证 bootstrap 请求；如果没有这段，桌面首屏可能拿不到后端启动数据。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGuiClientTest：创建假的 fetch；如果没有这行，单元测试会依赖真实后端端口。
      ok: true, // 新增代码+DesktopGuiClientTest：模拟 HTTP 成功；如果没有这行，client 会走失败分支。
      status: 200, // 新增代码+DesktopGuiClientTest：模拟成功状态码；如果没有这行，错误消息测试缺少稳定字段。
      json: async () => ({ // 新增代码+DesktopGuiClientTest：模拟 JSON 响应；如果没有这行，client 无法解析 payload。
        ok: true, // 新增代码+DesktopGuiClientTest：模拟 bridge 成功字段；如果没有这行，payload 不符合后端合同。
        workspace: "H:/repo", // 新增代码+DesktopGuiClientTest：模拟项目路径；如果没有这行，测试无法确认字段透传。
        app: { name: "OpenHarness Desktop", schema_version: 1 }, // 新增代码+DesktopGuiClientTest：模拟应用信息；如果没有这行，首屏无法判断协议版本。
        snapshot: {}, // 新增代码+DesktopGuiClientTest：模拟状态快照；如果没有这行，bootstrap payload 形状不完整。
        feature_flags: { event_polling: true }, // 新增代码+DesktopGuiClientTest：模拟功能开关；如果没有这行，前端无法知道是否轮询事件。
      }), // 新增代码+DesktopGuiClientTest：JSON 响应函数结束；如果没有这行，模拟对象语法不完整。
    })) as unknown as typeof fetch; // 新增代码+DesktopGuiClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 会拒绝注入测试 fetch。

    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGuiClientTest：创建带 token 的 client；如果没有这行，测试没有被测对象。
    const payload = await client.bootstrap(); // 新增代码+DesktopGuiClientTest：执行 bootstrap 调用；如果没有这行，无法验证请求和返回值。

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/bootstrap", { // 新增代码+DesktopGuiClientTest：确认请求 URL；如果没有这行，client 可能打到错误 endpoint。
      headers: { "X-OpenHarness-Desktop-Token": "test-token" }, // 新增代码+DesktopGuiClientTest：确认 token header；如果没有这行，安全合同可能被破坏。
    }); // 新增代码+DesktopGuiClientTest：请求断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.workspace).toBe("H:/repo"); // 新增代码+DesktopGuiClientTest：确认 payload 透传；如果没有这行，client 可能丢失 workspace 字段。
  }); // 新增代码+DesktopGuiClientTest：bootstrap 测试结束；如果没有这行，测试块语法不完整。

  it("loads events with a bounded polling query", async () => { // 新增代码+DesktopGuiClientTest：验证事件轮询请求；如果没有这段，工具事件刷新可能使用错误游标。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGuiClientTest：创建事件请求 mock；如果没有这行，事件测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGuiClientTest：模拟 HTTP 成功；如果没有这行，client 会抛出错误。
      status: 200, // 新增代码+DesktopGuiClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, events: [], since_sequence: 7, limit: 25 }), // 新增代码+DesktopGuiClientTest：模拟事件 payload；如果没有这行，client 无法返回事件列表。
    })) as unknown as typeof fetch; // 新增代码+DesktopGuiClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。

    const client = createGuiClient("http://127.0.0.1:8776/", "test-token", fetchMock); // 新增代码+DesktopGuiClientTest：使用带尾斜杠的 baseUrl；如果没有这行，无法验证 URL 规范化。
    const payload = await client.events(7, 25); // 新增代码+DesktopGuiClientTest：执行事件轮询；如果没有这行，无法验证 query 参数。

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/events?since_sequence=7&limit=25", { // 新增代码+DesktopGuiClientTest：确认事件 URL；如果没有这行，前端可能重复拉旧事件。
      headers: { "X-OpenHarness-Desktop-Token": "test-token" }, // 新增代码+DesktopGuiClientTest：确认事件请求同样带 token；如果没有这行，安全 endpoint 会拒绝。
    }); // 新增代码+DesktopGuiClientTest：事件请求断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.limit).toBe(25); // 新增代码+DesktopGuiClientTest：确认 limit 透传；如果没有这行，轮询批量大小可能失控。
  }); // 新增代码+DesktopGuiClientTest：事件测试结束；如果没有这行，测试块语法不完整。

  it("loads sessions for the project sidebar", async () => { // 新增代码+DesktopGUISessionsClientTest：验证 sessions 请求；如果没有这段，侧栏会话列表可能打错 endpoint。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGUISessionsClientTest：创建 sessions 请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGUISessionsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopGUISessionsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, sessions: ["session_a"], resume: {} }), // 新增代码+DesktopGUISessionsClientTest：模拟 sessions payload；如果没有这行，client 无法返回会话列表。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUISessionsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUISessionsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.sessions(); // 新增代码+DesktopGUISessionsClientTest：执行 sessions 调用；如果没有这行，无法验证请求行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/sessions", { // 新增代码+DesktopGUISessionsClientTest：确认 sessions URL；如果没有这行，client 可能打到旧 /sessions。
      headers: { "X-OpenHarness-Desktop-Token": "test-token" }, // 新增代码+DesktopGUISessionsClientTest：确认 token header；如果没有这行，安全端点会拒绝。
    }); // 新增代码+DesktopGUISessionsClientTest：请求断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.sessions).toEqual(["session_a"]); // 新增代码+DesktopGUISessionsClientTest：确认 sessions 透传；如果没有这行，侧栏数据可能丢失。
  }); // 新增代码+DesktopGUISessionsClientTest：sessions 测试结束；如果没有这行，测试块语法不完整。

  it("sends messages through a token-protected POST request", async () => { // 新增代码+DesktopGUILifecycleClientTest：验证发送消息 POST；如果没有这段，composer 可能漏带 token 或 body。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGUILifecycleClientTest：创建发送请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGUILifecycleClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopGUILifecycleClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, conversation_id: "default", turn_id: "turn_a", run_id: "run_a", status: "queued", answer: "", events_after_sequence: 0 }), // 新增代码+DesktopGUILifecycleClientTest：模拟发送响应；如果没有这行，client 无法返回 turn id。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUILifecycleClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。

    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUILifecycleClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.sendMessage("你好", "default"); // 新增代码+DesktopGUILifecycleClientTest：发送测试 prompt；如果没有这行，无法验证 POST 行为。

    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/messages", { // 新增代码+DesktopGUILifecycleClientTest：确认 POST URL；如果没有这行，client 可能打错 endpoint。
      method: "POST", // 新增代码+DesktopGUILifecycleClientTest：确认使用 POST；如果没有这行，消息可能被错误地 GET。
      headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, // 新增代码+DesktopGUILifecycleClientTest：确认 token 和 JSON header；如果没有这行，后端会拒绝或无法解析。
      body: JSON.stringify({ conversation_id: "default", prompt: "你好" }), // 新增代码+DesktopGUILifecycleClientTest：确认请求体；如果没有这行，prompt 可能没有传给后端。
    }); // 新增代码+DesktopGUILifecycleClientTest：POST 断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.turn_id).toBe("turn_a"); // 新增代码+DesktopGUILifecycleClientTest：确认 turn id 透传；如果没有这行，取消/重试无法定位目标。
  }); // 新增代码+DesktopGUILifecycleClientTest：发送消息测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGuiClientTest：测试段结束；如果没有这行，describe 块语法不完整。
