import { describe, expect, it, vi } from "vitest"; // 新增代码+ProviderSettingsClientTest：导入 Vitest 工具；如果没有这行，provider client 合同无法自动验证。
import { createGuiClient } from "../src/api/guiClient"; // 新增代码+ProviderSettingsClientTest：导入 GUI client 工厂；如果没有这行，测试没有被测对象。


describe("provider settings GUI client", () => { // 新增代码+ProviderSettingsClientTest：测试段开始，覆盖 Provider Settings V1 client endpoint；如果没有这段，前端可能打错 provider 设置路由。
  it("calls every provider settings endpoint with the desktop token", async () => { // 新增代码+ProviderSettingsClientTest：测试段开始，验证 GET/POST 路径、token 和 body；如果没有这段，设置页按钮可能只有 UI 假状态。
    const fetchMock = vi.fn(async () => ({ // 新增代码+ProviderSettingsClientTest：创建成功 fetch mock；如果没有这行，测试会依赖真实 bridge。
      ok: true, // 新增代码+ProviderSettingsClientTest：模拟 HTTP 成功；如果没有这行，client 会进入错误分支。
      status: 200, // 新增代码+ProviderSettingsClientTest：模拟成功状态码；如果没有这行，response 类型不完整。
      json: async () => ({ ok: true, schema_version: 3, providers: [], custom_provider_cta: { id: "custom-provider-cta", display_name: "自定义提供商", description: "" }, secret_store: { kind: "dev_json", label: "本地开发密钥存储", warning: "warning" }, default_provider_id: "", default_model_id: "" }), // 修改代码+OpenAIConnectClientTest：返回 provider settings V3 payload；如果没有这行，client 方法没有可解析响应。
    })) as unknown as typeof fetch; // 新增代码+ProviderSettingsClientTest：把 mock 转成 fetch 类型；如果没有这行，TypeScript 不接受测试注入。
    const client = createGuiClient("http://127.0.0.1:8776", "test-token", fetchMock); // 新增代码+ProviderSettingsClientTest：创建带 token 的 client；如果没有这行，测试没有被测对象。

    await client.providerSettings(); // 新增代码+ProviderSettingsClientTest：调用 provider catalog；如果没有这行，GET endpoint 不会被验证。
    await client.connectProvider("openai", "api-key", { secret: "unit-test-secret-value" }); // 修改代码+OpenAIConnectApiKeyTest：调用新方法 id 的连接 provider；如果没有这行，auth POST 仍会停留在旧 api_key 形状。
    await client.disconnectProvider("openai"); // 新增代码+ProviderSettingsClientTest：调用断开 provider；如果没有这行，disconnect POST 不会被验证。
    await client.saveCustomProvider({ providerId: "local-openai-compatible", displayName: "Local", baseUrl: "http://127.0.0.1:11434/v1", authMethodId: "api_key", fields: { api_key: "unit-test-secret-value" }, headers: [{ key: "X-Test", value: "1" }], models: [{ id: "local-model", displayName: "Local Model", visible: true }] }); // 新增代码+ProviderSettingsClientTest：调用保存自定义 provider；如果没有这行，custom provider body 转换不会被验证。
    await client.setModelVisibility("openai", "gpt-4.1", false); // 新增代码+ProviderSettingsClientTest：调用模型可见性；如果没有这行，model visibility POST 不会被验证。
    await client.testProviderConnection("openai"); // 新增代码+ProviderSettingsClientTest：调用连接探针；如果没有这行，test-connection POST 不会被验证。
    await client.startProviderAuthAttempt("openai", "chatgpt-browser"); // 新增代码+OpenAIConnectClientTest：调用 auth-attempt start；如果没有这行，browser/headless 方法可能只有静态 UI 没有后端动作。
    await client.providerAuthAttemptStatus("auth_attempt_test"); // 新增代码+OpenAIConnectClientTest：调用 auth-attempt status；如果没有这行，等待页轮询路径不会被验证。
    await client.cancelProviderAuthAttempt("auth_attempt_test"); // 新增代码+OpenAIConnectClientTest：调用 auth-attempt cancel；如果没有这行，关闭等待页可能不取消后端 pending。

    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8776/v2/gui/provider-settings/providers", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+ProviderSettingsClientTest：确认 catalog GET；如果没有这行，providerSettings 可能打错路径。
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8776/v2/gui/provider-settings/auth", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "openai", auth_method_id: "api-key", fields: { secret: "unit-test-secret-value" } }) }); // 修改代码+OpenAIConnectApiKeyTest：确认 auth POST 使用新方法 id 和通用 secret 字段；如果没有这行，连接按钮可能漏字段或继续旧合同。
    expect(fetchMock).toHaveBeenNthCalledWith(3, "http://127.0.0.1:8776/v2/gui/provider-settings/disconnect", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "openai" }) }); // 新增代码+ProviderSettingsClientTest：确认 disconnect POST；如果没有这行，断开按钮可能不带 provider id。
    expect(fetchMock).toHaveBeenNthCalledWith(4, "http://127.0.0.1:8776/v2/gui/provider-settings/custom-provider", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "local-openai-compatible", display_name: "Local", base_url: "http://127.0.0.1:11434/v1", auth_method_id: "api_key", fields: { api_key: "unit-test-secret-value" }, headers: [{ key: "X-Test", value: "1" }], models: [{ id: "local-model", display_name: "Local Model", visible: true }] }) }); // 新增代码+ProviderSettingsClientTest：确认 custom provider POST；如果没有这行，camelCase 到 snake_case 转换可能错误。
    expect(fetchMock).toHaveBeenNthCalledWith(5, "http://127.0.0.1:8776/v2/gui/provider-settings/model-visibility", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "openai", model_id: "gpt-4.1", visible: false }) }); // 新增代码+ProviderSettingsClientTest：确认 model visibility POST；如果没有这行，模型开关可能不持久。
    expect(fetchMock).toHaveBeenNthCalledWith(6, "http://127.0.0.1:8776/v2/gui/provider-settings/test-connection", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "openai" }) }); // 新增代码+ProviderSettingsClientTest：确认 test-connection POST；如果没有这行，测试连接按钮可能打错接口。
    expect(fetchMock).toHaveBeenNthCalledWith(7, "http://127.0.0.1:8776/v2/gui/provider-settings/auth-attempt/start", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ provider_id: "openai", auth_method_id: "chatgpt-browser" }) }); // 新增代码+OpenAIConnectClientTest：确认 start POST 路径和 body；如果没有这行，browser/headless 方法可能打错 endpoint。
    expect(fetchMock).toHaveBeenNthCalledWith(8, "http://127.0.0.1:8776/v2/gui/provider-settings/auth-attempt/status?attempt_id=auth_attempt_test", { headers: { "X-OpenHarness-Desktop-Token": "test-token" } }); // 新增代码+OpenAIConnectClientTest：确认 status GET 带 attempt_id query；如果没有这行，轮询可能拿不到目标 attempt。
    expect(fetchMock).toHaveBeenNthCalledWith(9, "http://127.0.0.1:8776/v2/gui/provider-settings/auth-attempt/cancel", { method: "POST", headers: { "X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json" }, body: JSON.stringify({ attempt_id: "auth_attempt_test" }) }); // 新增代码+OpenAIConnectClientTest：确认 cancel POST 路径和 body；如果没有这行，关闭弹窗可能留下 pending attempt。
  }); // 新增代码+ProviderSettingsClientTest：endpoint 测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsClientTest：测试段结束；如果没有这行，describe 语法不完整。
