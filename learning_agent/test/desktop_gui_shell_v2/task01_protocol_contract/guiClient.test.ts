import { describe, expect, it, vi } from "vitest"; // 新增代码+DesktopGuiClientTest：引入 Vitest 测试工具；如果没有这行，API client 合同无法自动验证。
import { GuiClientError, createGuiClient } from "../src/api/guiClient"; // 修改代码+GuiV2ClientErrors：导入 GUI client 工厂和结构化错误类；如果没有这行，测试无法验证 V2 错误字段不丢失。

describe("createGuiClient", () => { // 新增代码+DesktopGuiClientTest：测试段开始，覆盖 GUI bridge 前端客户端；如果没有这段，后续改动容易漏掉 token header。
  it("loads bootstrap payload from the GUI bridge", async () => { // 新增代码+DesktopGuiClientTest：验证 bootstrap 请求；如果没有这段，桌面首屏可能拿不到后端启动数据。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGuiClientTest：创建假的 fetch；如果没有这行，单元测试会依赖真实后端端口。
      ok: true, // 新增代码+DesktopGuiClientTest：模拟 HTTP 成功；如果没有这行，client 会走失败分支。
      status: 200, // 新增代码+DesktopGuiClientTest：模拟成功状态码；如果没有这行，错误消息测试缺少稳定字段。
      json: async () => ({ // 新增代码+DesktopGuiClientTest：模拟 JSON 响应；如果没有这行，client 无法解析 payload。
        ok: true, // 新增代码+DesktopGuiClientTest：模拟 bridge 成功字段；如果没有这行，payload 不符合后端合同。
        workspace: "H:/repo", // 新增代码+DesktopGuiClientTest：模拟项目路径；如果没有这行，测试无法确认字段透传。
        app: { name: "OpenHarness Desktop", schema_version: 2 }, // 修改代码+GuiV2ProtocolTypes：模拟 V2 应用信息；如果没有这行，前端测试会继续停留在 V1 schema。
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

  it("loads browser provider status for the desktop inspector", async () => { // 新增代码+DesktopGUIBrowserPanelClientTest：验证浏览器 provider 请求；如果没有这段，右侧浏览器面板可能打错 endpoint。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGUIBrowserPanelClientTest：创建 provider 请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGUIBrowserPanelClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopGUIBrowserPanelClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, provider_status: { providers: { visible_chromium: { available: true } } }, browser: {} }), // 新增代码+DesktopGUIBrowserPanelClientTest：模拟 provider payload；如果没有这行，client 无法返回浏览器状态。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUIBrowserPanelClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUIBrowserPanelClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.browserProviders(); // 新增代码+DesktopGUIBrowserPanelClientTest：执行浏览器 provider 调用；如果没有这行，无法验证请求行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/browser/providers", { // 新增代码+DesktopGUIBrowserPanelClientTest：确认 browser providers URL；如果没有这行，client 可能打到旧状态接口。
      headers: { "X-OpenHarness-Desktop-Token": "test-token" }, // 新增代码+DesktopGUIBrowserPanelClientTest：确认 token header；如果没有这行，安全端点会拒绝。
    }); // 新增代码+DesktopGUIBrowserPanelClientTest：请求断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.provider_status).toEqual({ providers: { visible_chromium: { available: true } } }); // 新增代码+DesktopGUIBrowserPanelClientTest：确认 provider_status 透传；如果没有这行，右栏数据可能丢失。
  }); // 新增代码+DesktopGUIBrowserPanelClientTest：浏览器 provider 测试结束；如果没有这行，测试块语法不完整。

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

  it("calls cancel, retry, and resume lifecycle endpoints", async () => { // 新增代码+DesktopTurnActionsClientTest：验证 GUI 生命周期按钮依赖的端点；如果没有这段，取消/重试/恢复可能打错 URL。
    const fetchMock = vi.fn(async (url: string) => ({ // 新增代码+DesktopTurnActionsClientTest：创建按 URL 返回不同 payload 的 fetch mock；如果没有这行，测试无法覆盖多个 endpoint。
      ok: true, // 新增代码+DesktopTurnActionsClientTest：模拟 HTTP 成功；如果没有这行，client 会走错误分支。
      status: 200, // 新增代码+DesktopTurnActionsClientTest：模拟成功状态码；如果没有这行，错误消息缺少稳定字段。
      json: async () => { // 新增代码+DesktopTurnActionsClientTest：根据 URL 返回 JSON；如果没有这段，三个调用无法获得各自响应形状。
        if (url.endsWith("/cancel")) { // 新增代码+DesktopTurnActionsClientTest：识别 cancel 请求；如果没有这行，取消响应无法单独断言。
          return { ok: true, turn_id: "turn_a", run_id: "run_a", status: "cancelling", events_after_sequence: 2 }; // 新增代码+DesktopTurnActionsClientTest：返回取消响应；如果没有这行，client.cancelTurn 没有 payload。
        } // 新增代码+DesktopTurnActionsClientTest：cancel 分支结束；如果没有这行，条件块语法不完整。
        if (url.endsWith("/retry")) { // 新增代码+DesktopTurnActionsClientTest：识别 retry 请求；如果没有这行，重试响应无法单独断言。
          return { ok: true, conversation_id: "default", turn_id: "turn_b", run_id: "run_b", status: "queued", answer: "", events_after_sequence: 3 }; // 新增代码+DesktopTurnActionsClientTest：返回重试新 turn 响应；如果没有这行，client.retryTurn 没有 payload。
        } // 新增代码+DesktopTurnActionsClientTest：retry 分支结束；如果没有这行，条件块语法不完整。
        return { ok: true, session_id: "default", messages: [], events_after_sequence: 4 }; // 新增代码+DesktopTurnActionsClientTest：返回 resume 响应；如果没有这行，client.resumeSession 没有 payload。
      }, // 新增代码+DesktopTurnActionsClientTest：JSON 函数结束；如果没有这行，模拟对象语法不完整。
    })) as unknown as typeof fetch; // 新增代码+DesktopTurnActionsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopTurnActionsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const cancel = await client.cancelTurn("turn_a"); // 新增代码+DesktopTurnActionsClientTest：执行取消调用；如果没有这行，无法验证 cancel endpoint。
    const retry = await client.retryTurn("turn_a"); // 新增代码+DesktopTurnActionsClientTest：执行重试调用；如果没有这行，无法验证 retry endpoint。
    const resume = await client.resumeSession("default"); // 新增代码+DesktopTurnActionsClientTest：执行恢复调用；如果没有这行，无法验证 resume endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v1/gui/turns/turn_a/cancel", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 新增代码+DesktopTurnActionsClientTest：确认取消请求形状；如果没有这行，按钮可能调用错误 endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v1/gui/turns/turn_a/retry", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 新增代码+DesktopTurnActionsClientTest：确认重试请求形状；如果没有这行，按钮可能绕过后端 retry 合同。
    expect(fetchMock).toHaveBeenNthCalledWith(3, "http://127.0.0.1:8776/v1/gui/sessions/default/resume", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 新增代码+DesktopTurnActionsClientTest：确认恢复请求形状；如果没有这行，侧栏恢复可能打错 endpoint。
    expect(cancel.status).toBe("cancelling"); // 新增代码+DesktopTurnActionsClientTest：确认取消状态透传；如果没有这行，UI 可能收不到 cancelling。
    expect(retry.turn_id).toBe("turn_b"); // 新增代码+DesktopTurnActionsClientTest：确认重试新 turn id 透传；如果没有这行，UI 无法显示新助手占位。
    expect(resume.session_id).toBe("default"); // 新增代码+DesktopTurnActionsClientTest：确认恢复 session 透传；如果没有这行，侧栏恢复结果可能丢失。
  }); // 新增代码+DesktopTurnActionsClientTest：生命周期端点测试结束；如果没有这行，测试块语法不完整。

  it("submits permission decisions through the backend contract", async () => { // 新增代码+DesktopGUIPermissionsClientTest：验证权限决策 POST；如果没有这段，权限弹窗可能绕过后端审计。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopGUIPermissionsClientTest：创建权限决策请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGUIPermissionsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopGUIPermissionsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, request_id: "perm_a", turn_id: "turn_a", decision: "approve", status: "approved", events_after_sequence: 4 }), // 新增代码+DesktopGUIPermissionsClientTest：模拟权限决策响应；如果没有这行，client 无法返回审计游标。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUIPermissionsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUIPermissionsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.decidePermission("perm_a", "turn_a", "approve", "用户在 GUI 中点击允许"); // 新增代码+DesktopGUIPermissionsClientTest：提交 approve 决策；如果没有这行，无法验证 POST 行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/permissions/perm_a/decision", { // 新增代码+DesktopGUIPermissionsClientTest：确认权限决策 URL；如果没有这行，client 可能打错 endpoint。
      method: "POST", // 新增代码+DesktopGUIPermissionsClientTest：确认使用 POST；如果没有这行，权限决策可能被错误地 GET。
      headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, // 新增代码+DesktopGUIPermissionsClientTest：确认 token 和 JSON header；如果没有这行，后端会拒绝或无法解析。
      body: JSON.stringify({ turn_id: "turn_a", decision: "approve", reason: "用户在 GUI 中点击允许" }), // 新增代码+DesktopGUIPermissionsClientTest：确认请求体；如果没有这行，后端无法审计 turn 和理由。
    }); // 新增代码+DesktopGUIPermissionsClientTest：权限决策请求断言结束；如果没有这行，expect 调用语法不完整。
    expect(payload.status).toBe("approved"); // 新增代码+DesktopGUIPermissionsClientTest：确认响应状态透传；如果没有这行，前端无法确认后端处理结果。
  }); // 新增代码+DesktopGUIPermissionsClientTest：权限决策测试结束；如果没有这行，测试块语法不完整。

  it("preserves structured V2 error code, message, and request id", async () => { // 新增代码+GuiV2ClientErrors：验证 V2 错误响应解析；如果没有这段，client 可能重新只抛 HTTP 状态码。
    const fetchMock = vi.fn(async () => ({ // 新增代码+GuiV2ClientErrors：创建失败响应 mock；如果没有这行，测试会依赖真实 bridge 错误。
      ok: false, // 新增代码+GuiV2ClientErrors：模拟 HTTP 失败；如果没有这行，client 不会进入错误解析分支。
      status: 409, // 新增代码+GuiV2ClientErrors：模拟 busy 冲突状态码；如果没有这行，错误对象没有稳定 status。
      json: async () => ({ ok: false, code: "agent_busy", message: "当前已有 GUI turn 正在运行。", request_id: "request_busy" }), // 新增代码+GuiV2ClientErrors：模拟 V2 结构化错误 payload；如果没有这行，无法证明 code/message/request_id 被保留。
    })) as unknown as typeof fetch; // 新增代码+GuiV2ClientErrors：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试 fetch。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+GuiV2ClientErrors：创建测试 client；如果没有这行，测试没有被测对象。
    try { // 新增代码+GuiV2ClientErrors：捕获预期错误；如果没有这行，无法对错误对象逐字段断言。
      await client.sendMessage("第二个 prompt", "default"); // 新增代码+GuiV2ClientErrors：触发失败 POST；如果没有这行，client 不会解析错误响应。
      throw new Error("expected structured GUI client error"); // 新增代码+GuiV2ClientErrors：防止请求意外成功；如果没有这行，测试可能静默通过。
    } catch (error) { // 新增代码+GuiV2ClientErrors：接住 client 抛出的错误；如果没有这行，断言无法运行。
      expect(error).toBeInstanceOf(GuiClientError); // 新增代码+GuiV2ClientErrors：确认错误类型是结构化 GUI 错误；如果没有这行，普通 Error 也会误过。
      const guiError = error as GuiClientError; // 新增代码+GuiV2ClientErrors：收窄错误类型；如果没有这行，TypeScript 不允许读取 code/requestId。
      expect(guiError.status).toBe(409); // 新增代码+GuiV2ClientErrors：确认 HTTP 状态码保留；如果没有这行，UI 无法分支处理冲突。
      expect(guiError.code).toBe("agent_busy"); // 新增代码+GuiV2ClientErrors：确认机器错误码保留；如果没有这行，busy 提示会退化。
      expect(guiError.message).toBe("当前已有 GUI turn 正在运行。"); // 新增代码+GuiV2ClientErrors：确认可读错误文本保留；如果没有这行，用户只能看到状态码。
      expect(guiError.requestId).toBe("request_busy"); // 新增代码+GuiV2ClientErrors：确认 request id 保留；如果没有这行，日志排查无法关联。
    } // 新增代码+GuiV2ClientErrors：错误捕获分支结束；如果没有这行，try/catch 语法不完整。
  }); // 新增代码+GuiV2ClientErrors：结构化错误测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGuiClientTest：测试段结束；如果没有这行，describe 块语法不完整。
