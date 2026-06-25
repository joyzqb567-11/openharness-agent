import { describe, expect, it, vi } from "vitest"; // 修改代码+DesktopRuntimePanelsClientTest：导入 Vitest 测试工具；如果没有这行，API client 合同无法自动验证。
import { GuiClientError, createGuiClient } from "../src/api/guiClient"; // 修改代码+DesktopRuntimePanelsClientTest：导入 GUI client 工厂和结构化错误类；如果没有这行，测试无法创建被测对象。

describe("createGuiClient", () => { // 修改代码+DesktopRuntimePanelsClientTest：测试段开始，覆盖 GUI bridge 前端客户端；如果没有这段，后续改动容易漏掉 token header 或 endpoint。
  it("loads bootstrap payload from the GUI bridge", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证 bootstrap 请求；如果没有这段，桌面首屏可能拿不到后端启动数据。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建假的 fetch；如果没有这行，单元测试会依赖真实后端端口。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会走失败分支。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, workspace: "H:/repo", app: { name: "OpenHarness Desktop", schema_version: 2 }, snapshot: {}, feature_flags: { event_polling: true } }), // 修改代码+DesktopRuntimePanelsClientTest：模拟 bootstrap payload；如果没有这行，client 无法解析启动数据。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建带 token 的 client；如果没有这行，测试没有被测对象。
    const payload = await client.bootstrap(); // 修改代码+DesktopRuntimePanelsClientTest：执行 bootstrap 调用；如果没有这行，无法验证请求和返回值。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/bootstrap", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 修改代码+DesktopRuntimePanelsClientTest：确认请求 URL 和 token header；如果没有这行，client 可能打到错误 endpoint。
    expect(payload.workspace).toBe("H:/repo"); // 修改代码+DesktopRuntimePanelsClientTest：确认 payload 透传；如果没有这行，client 可能丢失 workspace 字段。
  }); // 修改代码+DesktopRuntimePanelsClientTest：bootstrap 测试结束；如果没有这行，测试块语法不完整。

  it("loads events with a bounded polling query", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证事件轮询请求；如果没有这段，工具事件刷新可能使用错误游标。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建事件请求 mock；如果没有这行，事件测试会依赖真实 bridge。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, events: [], since_sequence: 7, limit: 25 }), // 修改代码+DesktopRuntimePanelsClientTest：模拟事件 payload；如果没有这行，client 无法返回事件列表。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776/", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：使用带尾斜杠的 baseUrl；如果没有这行，无法验证 URL 规范化。
    const payload = await client.events(7, 25); // 修改代码+DesktopRuntimePanelsClientTest：执行事件轮询；如果没有这行，无法验证 query 参数。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/events?since_sequence=7&limit=25", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 修改代码+DesktopRuntimePanelsClientTest：确认事件 URL 和 token；如果没有这行，前端可能重复拉旧事件。
    expect(payload.limit).toBe(25); // 修改代码+DesktopRuntimePanelsClientTest：确认 limit 透传；如果没有这行，轮询批量大小可能失控。
  }); // 修改代码+DesktopRuntimePanelsClientTest：事件测试结束；如果没有这行，测试块语法不完整。

  it("loads sessions for the project sidebar", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证 sessions 请求；如果没有这段，侧栏会话列表可能打错 endpoint。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建 sessions 请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, schema_version: 2, sessions: ["session_a"], archived_count: 0, resume: {} }), // 修改代码+DesktopGUISessionSearchClientTest：模拟 V2 sessions payload；如果没有这行，client 无法返回会话列表和归档计数。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.sessions(); // 修改代码+DesktopRuntimePanelsClientTest：执行 sessions 调用；如果没有这行，无法验证请求行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v2/gui/sessions", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 修改代码+DesktopGUISessionSearchClientTest：确认 sessions URL 和 token；如果没有这行，client 可能继续打到缺字段的旧 endpoint。
    expect(payload.sessions).toEqual(["session_a"]); // 修改代码+DesktopRuntimePanelsClientTest：确认 sessions 透传；如果没有这行，侧栏数据可能丢失。
  }); // 修改代码+DesktopRuntimePanelsClientTest：sessions 测试结束；如果没有这行，测试块语法不完整。

  it("calls V2 search, rename, and archive session endpoints", async () => { // 新增代码+DesktopGUISessionSearchClientTest：测试段开始，验证搜索、改名和归档接口；如果没有这段，按钮可能打错 endpoint。
    const fetchMock = vi.fn(async (url: string) => ({ // 新增代码+DesktopGUISessionSearchClientTest：创建按 URL 返回不同 payload 的 fetch mock；如果没有这行，测试无法覆盖三个 V2 endpoint。
      ok: true, // 新增代码+DesktopGUISessionSearchClientTest：模拟 HTTP 成功；如果没有这行，client 会走失败分支。
      status: 200, // 新增代码+DesktopGUISessionSearchClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => { // 新增代码+DesktopGUISessionSearchClientTest：根据 URL 返回 JSON；如果没有这段，三个调用无法获得各自响应形状。
        if (url.includes("/v2/gui/search")) { // 新增代码+DesktopGUISessionSearchClientTest：识别搜索请求；如果没有这行，搜索响应无法单独断言。
          return { ok: true, schema_version: 2, query: "成熟外壳", results: [{ session_id: "session_a", snippet: "成熟外壳片段" }] }; // 新增代码+DesktopGUISessionSearchClientTest：返回搜索 payload；如果没有这行，client.searchSessions 没有数据。
        } // 新增代码+DesktopGUISessionSearchClientTest：搜索响应分支结束；如果没有这行，条件块语法不完整。
        return { ok: true, schema_version: 2, session: { session_id: "session_a", title: "新标题" }, archived: url.endsWith("/archive") }; // 新增代码+DesktopGUISessionSearchClientTest：返回改名或归档 payload；如果没有这行，写入方法没有结果。
      }, // 新增代码+DesktopGUISessionSearchClientTest：json 函数结束；如果没有这行，mock 对象语法不完整。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUISessionSearchClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUISessionSearchClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const search = await client.searchSessions("成熟外壳"); // 新增代码+DesktopGUISessionSearchClientTest：执行搜索调用；如果没有这行，无法验证 search endpoint。
    const rename = await client.renameSession("session_a", "新标题"); // 新增代码+DesktopGUISessionSearchClientTest：执行改名调用；如果没有这行，无法验证 rename endpoint。
    const archive = await client.archiveSession("session_a", true); // 新增代码+DesktopGUISessionSearchClientTest：执行归档调用；如果没有这行，无法验证 archive endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v2/gui/search?q=%E6%88%90%E7%86%9F%E5%A4%96%E5%A3%B3", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+DesktopGUISessionSearchClientTest：确认搜索 URL 和 token；如果没有这行，中文 query 编码错误不会被发现。
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v2/gui/sessions/session_a/rename", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ title: "新标题" }) }); // 新增代码+DesktopGUISessionSearchClientTest：确认改名 POST 形状；如果没有这行，rename 可能没有 body 或 token。
    expect(fetchMock).toHaveBeenNthCalledWith(3, "http://127.0.0.1:8776/v2/gui/sessions/session_a/archive", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ archived: true }) }); // 新增代码+DesktopGUISessionSearchClientTest：确认归档 POST 形状；如果没有这行，archive 可能没有写入意图。
    expect(search.results[0].session_id).toBe("session_a"); // 新增代码+DesktopGUISessionSearchClientTest：确认搜索结果透传；如果没有这行，搜索面板可能拿不到会话 id。
    expect(rename.session.title).toBe("新标题"); // 新增代码+DesktopGUISessionSearchClientTest：确认改名结果透传；如果没有这行，前端无法更新标题。
    expect(archive.archived).toBe(true); // 新增代码+DesktopGUISessionSearchClientTest：确认归档结果透传；如果没有这行，前端无法隐藏会话。
  }); // 新增代码+DesktopGUISessionSearchClientTest：搜索/改名/归档测试结束；如果没有这行，测试块语法不完整。

  it("loads browser provider status for the legacy desktop inspector", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证旧浏览器 provider 请求；如果没有这段，旧兼容入口可能被误删。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建 provider 请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, provider_status: { providers: { visible_chromium: { available: true } } }, browser: {} }), // 修改代码+DesktopRuntimePanelsClientTest：模拟 provider payload；如果没有这行，client 无法返回浏览器状态。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.browserProviders(); // 修改代码+DesktopRuntimePanelsClientTest：执行浏览器 provider 调用；如果没有这行，无法验证请求行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/browser/providers", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 修改代码+DesktopRuntimePanelsClientTest：确认 browser providers URL 和 token；如果没有这行，client 可能打到错误接口。
    expect(payload.provider_status).toEqual({ providers: { visible_chromium: { available: true } } }); // 修改代码+DesktopRuntimePanelsClientTest：确认 provider_status 透传；如果没有这行，右侧旧数据可能丢失。
  }); // 修改代码+DesktopRuntimePanelsClientTest：旧 provider 测试结束；如果没有这行，测试块语法不完整。

  it("loads V2 runtime panels for browser and Computer Use", async () => { // 新增代码+DesktopRuntimePanelsClientTest：验证 V2 runtime panels 请求；如果没有这段，前端可能没有真正接入成熟面板 endpoint。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopRuntimePanelsClientTest：创建 runtime panels 请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, schema_version: 2, browser: { providers: { visible_chromium: { available: true } } }, computer_use: { mode: "off" }, permissions: { pending_count: 0 }, status_degraded: false, safe_error: "" }), // 新增代码+DesktopRuntimePanelsClientTest：模拟 V2 面板 payload；如果没有这行，client 无法返回成熟面板数据。
    })) as unknown as typeof fetch; // 新增代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.runtimePanels(); // 新增代码+DesktopRuntimePanelsClientTest：执行 runtime panels 调用；如果没有这行，无法验证 V2 endpoint。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v2/gui/runtime/panels", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+DesktopRuntimePanelsClientTest：确认 V2 runtime panels URL 和 token；如果没有这行，前端可能仍在拼旧接口。
    expect(payload.computer_use).toEqual({ mode: "off" }); // 新增代码+DesktopRuntimePanelsClientTest：确认 Computer Use payload 透传；如果没有这行，新面板数据可能丢失。
  }); // 新增代码+DesktopRuntimePanelsClientTest：V2 runtime panels 测试结束；如果没有这行，测试块语法不完整。

  it("loads Harness status and structured pause resume controls", async () => { // 新增代码+DesktopGUIHarnessClientTest：验证 Harness 状态和控制接口；如果没有这段，任务面板可能打错 endpoint。
    const fetchMock = vi.fn(async (url: string) => ({ // 新增代码+DesktopGUIHarnessClientTest：创建按 URL 返回不同 payload 的 fetch mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+DesktopGUIHarnessClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 新增代码+DesktopGUIHarnessClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => { // 新增代码+DesktopGUIHarnessClientTest：根据请求 URL 返回 JSON；如果没有这段，三个调用无法获得各自响应。
        if (url.endsWith("/status")) { // 新增代码+DesktopGUIHarnessClientTest：识别 Harness status 请求；如果没有这行，状态响应无法单独断言。
          return { ok: true, schema_version: 2, active_goal: { run_id: "goal_a" }, queue: [], checkpoints: [], last_progress: "", blocked_reason: "", safe_error: "", status_degraded: false, controls: { pause_supported: false, resume_supported: false } }; // 新增代码+DesktopGUIHarnessClientTest：返回状态 payload；如果没有这行，client.harnessStatus 没有数据。
        } // 新增代码+DesktopGUIHarnessClientTest：status 分支结束；如果没有这行，条件块语法不完整。
        return { ok: true, schema_version: 2, action: url.endsWith("/resume") ? "resume" : "pause", supported: false, status: "unsupported", message: "not supported", safe_error: "" }; // 新增代码+DesktopGUIHarnessClientTest：返回 pause/resume 控制 payload；如果没有这行，控制方法没有稳定响应。
      }, // 新增代码+DesktopGUIHarnessClientTest：json 函数结束；如果没有这行，mock 对象语法不完整。
    })) as unknown as typeof fetch; // 新增代码+DesktopGUIHarnessClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopGUIHarnessClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const status = await client.harnessStatus(); // 新增代码+DesktopGUIHarnessClientTest：执行 Harness status 调用；如果没有这行，无法验证 GET endpoint。
    const pause = await client.pauseHarness(); // 新增代码+DesktopGUIHarnessClientTest：执行 pause 调用；如果没有这行，无法验证 pause endpoint。
    const resume = await client.resumeHarness(); // 新增代码+DesktopGUIHarnessClientTest：执行 resume 调用；如果没有这行，无法验证 resume endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v2/gui/harness/status", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+DesktopGUIHarnessClientTest：确认 status URL 和 token；如果没有这行，任务面板可能无法加载。
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v2/gui/harness/pause", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 新增代码+DesktopGUIHarnessClientTest：确认 pause POST 形状；如果没有这行，暂停意图可能漏 token 或 body。
    expect(fetchMock).toHaveBeenNthCalledWith(3, "http://127.0.0.1:8776/v2/gui/harness/resume", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 新增代码+DesktopGUIHarnessClientTest：确认 resume POST 形状；如果没有这行，恢复意图可能漏 token 或 body。
    expect(status.active_goal.run_id).toBe("goal_a"); // 新增代码+DesktopGUIHarnessClientTest：确认状态 payload 透传；如果没有这行，任务面板可能拿不到当前目标。
    expect(pause.supported).toBe(false); // 新增代码+DesktopGUIHarnessClientTest：确认 pause 能力字段透传；如果没有这行，按钮显示条件不可靠。
    expect(resume.action).toBe("resume"); // 新增代码+DesktopGUIHarnessClientTest：确认 resume 动作字段透传；如果没有这行，恢复响应可能被误判。
  }); // 新增代码+DesktopGUIHarnessClientTest：Harness client 测试结束；如果没有这行，测试块语法不完整。

  it("sends messages through a token-protected POST request", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证发送消息 POST；如果没有这段，composer 可能漏带 token 或 body。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建发送请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, conversation_id: "default", turn_id: "turn_a", run_id: "run_a", status: "queued", answer: "", events_after_sequence: 0 }), // 修改代码+DesktopRuntimePanelsClientTest：模拟发送响应；如果没有这行，client 无法返回 turn id。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.sendMessage("你好", "default"); // 修改代码+DesktopRuntimePanelsClientTest：发送测试 prompt；如果没有这行，无法验证 POST 行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/messages", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ conversation_id: "default", prompt: "你好" }) }); // 修改代码+DesktopRuntimePanelsClientTest：确认 POST URL、headers 和 body；如果没有这行，prompt 可能没有传给后端。
    expect(payload.turn_id).toBe("turn_a"); // 修改代码+DesktopRuntimePanelsClientTest：确认 turn id 透传；如果没有这行，取消和重试无法定位目标。
  }); // 修改代码+DesktopRuntimePanelsClientTest：发送消息测试结束；如果没有这行，测试块语法不完整。

  it("calls cancel, retry, and resume lifecycle endpoints", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证 GUI 生命周期按钮依赖的端点；如果没有这段，取消/重试/恢复可能打错 URL。
    const fetchMock = vi.fn(async (url: string) => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建按 URL 返回不同 payload 的 fetch mock；如果没有这行，测试无法覆盖多个 endpoint。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会走错误分支。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，错误消息缺少稳定字段。
      json: async () => { // 修改代码+DesktopRuntimePanelsClientTest：根据 URL 返回 JSON；如果没有这段，三个调用无法获得各自响应形状。
        if (url.endsWith("/cancel")) { // 修改代码+DesktopRuntimePanelsClientTest：识别 cancel 请求；如果没有这行，取消响应无法单独断言。
          return { ok: true, turn_id: "turn_a", run_id: "run_a", status: "cancelling", events_after_sequence: 2 }; // 修改代码+DesktopRuntimePanelsClientTest：返回取消响应；如果没有这行，client.cancelTurn 没有 payload。
        } // 修改代码+DesktopRuntimePanelsClientTest：cancel 分支结束；如果没有这行，条件块语法不完整。
        if (url.endsWith("/retry")) { // 修改代码+DesktopRuntimePanelsClientTest：识别 retry 请求；如果没有这行，重试响应无法单独断言。
          return { ok: true, conversation_id: "default", turn_id: "turn_b", run_id: "run_b", status: "queued", answer: "", events_after_sequence: 3 }; // 修改代码+DesktopRuntimePanelsClientTest：返回重试新 turn 响应；如果没有这行，client.retryTurn 没有 payload。
        } // 修改代码+DesktopRuntimePanelsClientTest：retry 分支结束；如果没有这行，条件块语法不完整。
        return { ok: true, session_id: "default", messages: [], events_after_sequence: 4 }; // 修改代码+DesktopRuntimePanelsClientTest：返回 resume 响应；如果没有这行，client.resumeSession 没有 payload。
      }, // 修改代码+DesktopRuntimePanelsClientTest：JSON 函数结束；如果没有这行，模拟对象语法不完整。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const cancel = await client.cancelTurn("turn_a"); // 修改代码+DesktopRuntimePanelsClientTest：执行取消调用；如果没有这行，无法验证 cancel endpoint。
    const retry = await client.retryTurn("turn_a"); // 修改代码+DesktopRuntimePanelsClientTest：执行重试调用；如果没有这行，无法验证 retry endpoint。
    const resume = await client.resumeSession("default"); // 修改代码+DesktopRuntimePanelsClientTest：执行恢复调用；如果没有这行，无法验证 resume endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v1/gui/turns/turn_a/cancel", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 修改代码+DesktopRuntimePanelsClientTest：确认取消请求形状；如果没有这行，按钮可能调用错误 endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v1/gui/turns/turn_a/retry", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 修改代码+DesktopRuntimePanelsClientTest：确认重试请求形状；如果没有这行，按钮可能绕过后端 retry 合同。
    expect(fetchMock).toHaveBeenNthCalledWith(3, "http://127.0.0.1:8776/v1/gui/sessions/default/resume", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({}) }); // 修改代码+DesktopRuntimePanelsClientTest：确认恢复请求形状；如果没有这行，侧栏恢复可能打错 endpoint。
    expect(cancel.status).toBe("cancelling"); // 修改代码+DesktopRuntimePanelsClientTest：确认取消状态透传；如果没有这行，UI 可能收不到 cancelling。
    expect(retry.turn_id).toBe("turn_b"); // 修改代码+DesktopRuntimePanelsClientTest：确认重试新 turn id 透传；如果没有这行，UI 无法显示新助手占位。
    expect(resume.session_id).toBe("default"); // 修改代码+DesktopRuntimePanelsClientTest：确认恢复 session 透传；如果没有这行，侧栏恢复结果可能丢失。
  }); // 修改代码+DesktopRuntimePanelsClientTest：生命周期端点测试结束；如果没有这行，测试块语法不完整。

  it("submits permission decisions through the backend contract", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证权限决策 POST；如果没有这段，权限弹窗可能绕过后端审计。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建权限决策请求 mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 成功；如果没有这行，client 会抛错。
      status: 200, // 修改代码+DesktopRuntimePanelsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, request_id: "perm_a", turn_id: "turn_a", decision: "approve", status: "approved", events_after_sequence: 4 }), // 修改代码+DesktopRuntimePanelsClientTest：模拟权限决策响应；如果没有这行，client 无法返回审计游标。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    const payload = await client.decidePermission("perm_a", "turn_a", "approve", "用户在 GUI 中点击允许"); // 修改代码+DesktopRuntimePanelsClientTest：提交 approve 决策；如果没有这行，无法验证 POST 行为。
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v1/gui/permissions/perm_a/decision", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ turn_id: "turn_a", decision: "approve", reason: "用户在 GUI 中点击允许" }) }); // 修改代码+DesktopRuntimePanelsClientTest：确认权限决策 URL 和 body；如果没有这行，后端无法审计 turn 和理由。
    expect(payload.status).toBe("approved"); // 修改代码+DesktopRuntimePanelsClientTest：确认响应状态透传；如果没有这行，前端无法确认后端处理结果。
  }); // 修改代码+DesktopRuntimePanelsClientTest：权限决策测试结束；如果没有这行，测试块语法不完整。

  it("preserves structured V2 error code, message, and request id", async () => { // 修改代码+DesktopRuntimePanelsClientTest：验证 V2 错误响应解析；如果没有这段，client 可能重新只抛 HTTP 状态码。
    const fetchMock = vi.fn(async () => ({ // 修改代码+DesktopRuntimePanelsClientTest：创建失败响应 mock；如果没有这行，测试会依赖真实 bridge 错误。
      ok: false, // 修改代码+DesktopRuntimePanelsClientTest：模拟 HTTP 失败；如果没有这行，client 不会进入错误解析分支。
      status: 409, // 修改代码+DesktopRuntimePanelsClientTest：模拟 busy 冲突状态码；如果没有这行，错误对象没有稳定 status。
      json: async () => ({ ok: false, code: "agent_busy", message: "当前已有 GUI turn 正在运行。", request_id: "request_busy" }), // 修改代码+DesktopRuntimePanelsClientTest：模拟 V2 结构化错误 payload；如果没有这行，无法证明 code/message/request_id 被保留。
    })) as unknown as typeof fetch; // 修改代码+DesktopRuntimePanelsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试 fetch。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 修改代码+DesktopRuntimePanelsClientTest：创建测试 client；如果没有这行，测试没有被测对象。
    try { // 修改代码+DesktopRuntimePanelsClientTest：捕获预期错误；如果没有这行，无法对错误对象逐字段断言。
      await client.sendMessage("第二个 prompt", "default"); // 修改代码+DesktopRuntimePanelsClientTest：触发失败 POST；如果没有这行，client 不会解析错误响应。
      throw new Error("expected structured GUI client error"); // 修改代码+DesktopRuntimePanelsClientTest：防止请求意外成功；如果没有这行，测试可能静默通过。
    } catch (error) { // 修改代码+DesktopRuntimePanelsClientTest：接住 client 抛出的错误；如果没有这行，断言无法运行。
      expect(error).toBeInstanceOf(GuiClientError); // 修改代码+DesktopRuntimePanelsClientTest：确认错误类型是结构化 GUI 错误；如果没有这行，普通 Error 也会误过。
      const guiError = error as GuiClientError; // 修改代码+DesktopRuntimePanelsClientTest：收窄错误类型；如果没有这行，TypeScript 不允许读取 code/requestId。
      expect(guiError.status).toBe(409); // 修改代码+DesktopRuntimePanelsClientTest：确认 HTTP 状态码保留；如果没有这行，UI 无法分支处理冲突。
      expect(guiError.code).toBe("agent_busy"); // 修改代码+DesktopRuntimePanelsClientTest：确认机器错误码保留；如果没有这行，busy 提示会退化。
      expect(guiError.message).toBe("当前已有 GUI turn 正在运行。"); // 修改代码+DesktopRuntimePanelsClientTest：确认可读错误文本保留；如果没有这行，用户只能看到状态码。
      expect(guiError.requestId).toBe("request_busy"); // 修改代码+DesktopRuntimePanelsClientTest：确认 request id 保留；如果没有这行，日志排查无法关联。
    } // 修改代码+DesktopRuntimePanelsClientTest：错误捕获分支结束；如果没有这行，try/catch 语法不完整。
  }); // 修改代码+DesktopRuntimePanelsClientTest：结构化错误测试结束；如果没有这行，测试块语法不完整。

  it("keeps structured not_found details for the unknown-route diagnostics probe", async () => { // 新增代码+DesktopUnknownRouteProbeTest：测试段开始，验证诊断页 unknown route 探针保留结构化错误；如果没有这段，GUI 可能只显示泛化 404。
    const fetchMock = vi.fn(async () => ({ // 新增代码+DesktopUnknownRouteProbeTest：创建未知路由失败响应 mock；如果没有这一行，测试会依赖真实 bridge。
      ok: false, // 新增代码+DesktopUnknownRouteProbeTest：模拟 HTTP 失败；如果没有这一行，client 不会进入错误解析分支。
      status: 404, // 新增代码+DesktopUnknownRouteProbeTest：模拟 unknown route 状态码；如果没有这一行，错误对象没有稳定 status。
      json: async () => ({ ok: false, code: "not_found", message: "未找到 GUI 路由。", request_id: "request_unknown" }), // 新增代码+DesktopUnknownRouteProbeTest：模拟 V2 结构化 404 payload；如果没有这一行，无法验证 code/message/request_id。
    })) as unknown as typeof fetch; // 新增代码+DesktopUnknownRouteProbeTest：把 mock 转成 fetch 类型；如果没有这一行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+DesktopUnknownRouteProbeTest：创建测试 client；如果没有这一行，测试没有被测对象。
    try { // 新增代码+DesktopUnknownRouteProbeTest：捕获预期 404；如果没有这一行，无法逐字段断言错误对象。
      await client.probeUnknownRoute(); // 新增代码+DesktopUnknownRouteProbeTest：执行 unknown route 探针；如果没有这一行，client 新方法没有行为验证。
      throw new Error("expected unknown route probe to fail"); // 新增代码+DesktopUnknownRouteProbeTest：防止请求意外成功；如果没有这一行，测试可能静默通过。
    } catch (error) { // 新增代码+DesktopUnknownRouteProbeTest：接住结构化错误；如果没有这一行，断言无法运行。
      expect(error).toBeInstanceOf(GuiClientError); // 新增代码+DesktopUnknownRouteProbeTest：确认仍是 GuiClientError；如果没有这一行，普通 Error 也会误过。
      const guiError = error as GuiClientError; // 新增代码+DesktopUnknownRouteProbeTest：收窄错误类型；如果没有这一行，TypeScript 不允许读取 code/requestId。
      expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8776/v2/gui/__unknown_route_probe__", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+DesktopUnknownRouteProbeTest：确认探针 URL 和 token；如果没有这一行，诊断按钮可能打错路径。
      expect(guiError.status).toBe(404); // 新增代码+DesktopUnknownRouteProbeTest：确认状态码保留；如果没有这一行，GUI 无法区分 not_found。
      expect(guiError.code).toBe("not_found"); // 新增代码+DesktopUnknownRouteProbeTest：确认机器码保留；如果没有这一行，未知路由会退化成泛化错误。
      expect(guiError.requestId).toBe("request_unknown"); // 新增代码+DesktopUnknownRouteProbeTest：确认 request id 保留；如果没有这一行，日志排查无法关联。
    } // 新增代码+DesktopUnknownRouteProbeTest：错误捕获分支结束；如果没有这一行，try/catch 语法不完整。
  }); // 新增代码+DesktopUnknownRouteProbeTest：unknown route 探针测试结束；如果没有这一行，测试块语法不完整。

  it("loads V2 health and diagnostics for settings panels", async () => { // ????+DesktopDiagnosticsClientTest??? V2 ??/????????????client ???? endpoint?
    const fetchMock = vi.fn(async (url: string) => ({ // ????+DesktopDiagnosticsClientTest???? URL ?? payload ? fetch mock??????????????? bridge?
      ok: true, // ????+DesktopDiagnosticsClientTest??? HTTP ??????????client ????????
      status: 200, // ????+DesktopDiagnosticsClientTest????????????????response ??????
      json: async () => { // ????+DesktopDiagnosticsClientTest??? URL ?? JSON???????????????????
        if (url.endsWith("/v2/gui/health")) { // ????+DesktopDiagnosticsClientTest??? health ??????????health ?????????
          return { ok: true, backend_online: true, schema_version: 2, uptime_seconds: 3, workspace: "H:/repo", workspace_name: "repo", feature_flags: { diagnostics: true }, model_provider: { provider: "OpenHarness", model: "desktop-gui-bridge" } }; // ????+DesktopDiagnosticsClientTest??? health payload????????client.health ?????
        } // ????+DesktopDiagnosticsClientTest?health ?????????????????????
        return { ok: true, schema_version: 2, backend_online: true, health: {}, status_degraded: false, safe_error: "", snapshot_summary: {}, last_error: "", release_gate: { status: "passed" }, diagnostic_bundle: { copy_text: "{}" } }; // ????+DesktopDiagnosticsClientTest??? diagnostics payload????????client.diagnostics ?????
      }, // ????+DesktopDiagnosticsClientTest?json ????????????mock ????????
    })) as unknown as typeof fetch; // ????+DesktopDiagnosticsClientTest?? mock ?? fetch ??????????TypeScript ????????
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // ????+DesktopDiagnosticsClientTest???? token ? client?????????????????
    const health = await client.health(); // ????+DesktopDiagnosticsClientTest??? health ?????????????? health endpoint?
    const diagnostics = await client.diagnostics(); // ????+DesktopDiagnosticsClientTest??? diagnostics ?????????????? diagnostics endpoint?
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v2/gui/health", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // ????+DesktopDiagnosticsClientTest??? health URL ? token??????????????????
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v2/gui/diagnostics", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // ????+DesktopDiagnosticsClientTest??? diagnostics URL ? token??????????????????
    expect(health.uptime_seconds).toBe(3); // ????+DesktopDiagnosticsClientTest??? health payload ???????????????????
    expect(diagnostics.release_gate).toEqual({ status: "passed" }); // ????+DesktopDiagnosticsClientTest??? diagnostics payload ??????????release gate ???????
  }); // ????+DesktopDiagnosticsClientTest?V2 health/diagnostics ?????????????????????
}); // 修改代码+DesktopRuntimePanelsClientTest：测试段结束；如果没有这行，describe 块语法不完整。
