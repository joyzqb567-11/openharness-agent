import { describe, expect, it } from "vitest"; // 修改代码+ProviderSettingsStoreTest：导入 Vitest 工具；如果没有这行，provider store 合同无法自动验证。
import type { GuiProviderInfo, GuiProviderSettingsPayload } from "../src/api/guiProviderTypes"; // 修改代码+ProviderSettingsStoreTest：导入后端 provider 类型；如果没有这行，污染 payload 的测试输入无法被清晰标注。
import { buildProviderSettingsViewModel, modelGroupsForDisplay, providerRowsForDisplay, redactedProviderPayload } from "../src/state/providerSettingsStore"; // 修改代码+ProviderSettingsStoreTest：导入 provider settings 纯函数；如果没有这行，测试没有被测目标。

type PollutedProviderInfo = GuiProviderInfo & Record<string, unknown>; // 修改代码+ProviderSettingsStoreTest：定义可能夹带危险字段的 provider 类型；如果没有这行，安全测试无法表达后端 bug 场景。
type PollutedProviderSettingsPayload = Omit<GuiProviderSettingsPayload, "providers"> & { providers: PollutedProviderInfo[] }; // 修改代码+ProviderSettingsStoreTest：定义可能被污染的后端 payload；如果没有这行，测试只能传完全干净的合同对象。

const openAiAuthMethods: GuiProviderInfo["auth_methods"] = [ // 修改代码+OpenAIConnectStoreTest：定义 OpenAI 三方法 fixture；如果没有这段，store 测试无法模拟后端 V3 catalog。
  { id: "chatgpt-browser", label: "ChatGPT Pro/Plus (browser)", enabled: true, status: "mock_available", type: "oauth", mode: "auto", fields: [], help_text: "browser", experimental: true }, // 新增代码+OpenAIConnectStoreTest：模拟 browser OAuth 方法；如果没有这行，方法选择器无法验证浏览器登录元数据。
  { id: "chatgpt-headless", label: "ChatGPT Pro/Plus (headless)", enabled: true, status: "mock_available", type: "oauth", mode: "auto", fields: [], help_text: "headless", experimental: true }, // 新增代码+OpenAIConnectStoreTest：模拟 headless OAuth 方法；如果没有这行，方法选择器无法验证设备码登录元数据。
  { id: "api-key", label: "API 密钥", enabled: true, status: "available", type: "api", mode: "form", fields: ["secret"], help_text: "help", experimental: false }, // 新增代码+OpenAIConnectStoreTest：模拟稳定 API key 方法；如果没有这行，真实密钥表单路径无法被 store 测试覆盖。
]; // 修改代码+OpenAIConnectStoreTest：结束 OpenAI 三方法 fixture；如果没有这行，测试 fixture 语法不完整。

const providerPayload: PollutedProviderSettingsPayload = { // 修改代码+ProviderSettingsStoreTest：定义后端 provider settings fixture；如果没有这段，多个测试会重复构造 payload。
  ok: true, // 修改代码+ProviderSettingsStoreTest：模拟成功响应；如果没有这行，view model 无法识别 payload。
  schema_version: 3, // 修改代码+OpenAIConnectStoreTest：模拟 OpenAI 三方法 V3 schema；如果没有这行，前端不会发现旧 schema 被误用。
  secret_store: { kind: "dev_json", label: "本地开发密钥存储", warning: "开发警告" }, // 修改代码+ProviderSettingsStoreTest：模拟 dev secret store；如果没有这行，warning copy 无法测试。
  custom_provider_cta: { id: "custom-provider-cta", display_name: "自定义提供商", description: "添加兼容 provider" }, // 修改代码+ProviderSettingsStoreTest：模拟虚拟 CTA；如果没有这行，自定义入口无法测试。
  default_provider_id: "", // 修改代码+ProviderSettingsStoreTest：模拟默认 provider；如果没有这行，payload 形状不完整。
  default_model_id: "", // 修改代码+ProviderSettingsStoreTest：模拟默认模型；如果没有这行，payload 形状不完整。
  providers: [ // 修改代码+ProviderSettingsStoreTest：开始 provider 列表；如果没有这行，排序和分组没有输入。
    { id: "openrouter", display_name: "OpenRouter", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "api-key", label: "API 密钥", enabled: true, status: "available", type: "api", mode: "form", fields: ["secret"], help_text: "help", experimental: false }], description: "OpenRouter", models: [] }, // 修改代码+OpenAIConnectStoreTest：模拟未连接 provider 的新 auth method 形状；如果没有这行，排序无法比较连接状态。
    { id: "openai", display_name: "OpenAI", kind: "built_in", source: "config", connected: true, masked_key: "sk••••xx", auth_methods: openAiAuthMethods, description: "OpenAI", api_key: "unit-test-secret-value", secret_ref: "secret-ref-should-not-render", models: [{ id: "gpt-4.1", display_name: "GPT-4.1", provider_id: "openai", visible: true, supports_tools: true, supports_vision: true }] }, // 修改代码+OpenAIConnectStoreTest：模拟已连接 OpenAI 三方法且夹带危险字段；如果没有这行，脱敏和方法元数据测试不真实。
    { id: "github-copilot", display_name: "GitHub Copilot", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "device-code", label: "设备码", enabled: false, status: "unsupported_v1", type: "oauth", mode: "auto", fields: [], help_text: "unsupported", experimental: true }], description: "Copilot", models: undefined }, // 修改代码+OpenAIConnectStoreTest：模拟 unsupported auth 的新 auth method 形状；如果没有这行，禁用按钮和空数组兼容无法测试。
  ], // 修改代码+ProviderSettingsStoreTest：provider 列表结束；如果没有这行，fixture 语法不完整。
}; // 修改代码+ProviderSettingsStoreTest：fixture 结束；如果没有这行，常量语法不完整。

describe("providerSettingsStore", () => { // 修改代码+ProviderSettingsStoreTest：测试段开始，覆盖 provider settings view model；如果没有这段，设置页会直接消费后端原始 JSON。
  it("redacts unsafe backend fields before building the view model", () => { // 修改代码+ProviderSettingsStoreTest：测试段开始，验证危险字段脱敏；如果没有这段，后端 bug 可能把 secret 带进 renderer state。
    const safePayload = redactedProviderPayload(providerPayload); // 修改代码+ProviderSettingsStoreTest：执行 payload 脱敏；如果没有这行，后续断言没有输入。
    const serialized = JSON.stringify(safePayload); // 修改代码+ProviderSettingsStoreTest：序列化脱敏结果；如果没有这行，嵌套字段泄露可能漏过。
    expect(serialized).not.toContain("api_key"); // 修改代码+ProviderSettingsStoreTest：确认 snake_case secret 字段移除；如果没有这行，renderer 可能持有 raw key。
    expect(serialized).not.toContain("unit-test-secret-value"); // 修改代码+ProviderSettingsStoreTest：确认 raw secret 值移除；如果没有这行，截图或日志可能泄密。
    expect(serialized).not.toContain("secret_ref"); // 新增代码+OpenAIConnectStoreTest：确认后端 secret 引用不会进入 renderer state；如果没有这行，前端可能间接泄露密钥定位信息。
  }); // 修改代码+ProviderSettingsStoreTest：脱敏测试结束；如果没有这行，测试块语法不完整。

  it("redacts OAuth token-shaped fields recursively", () => { // 新增代码+OpenAIConnectStoreTest：测试段开始，验证 OAuth token 字段递归脱敏；如果没有这段，mock/real OAuth payload bug 可能把 token 留在前端。
    const polluted = { providers: [{ id: "openai", access_token: "unit-test-access-token", nested: { refresh_token: "unit-test-refresh-token", id_token: "unit-test-id-token" } }] }; // 新增代码+OpenAIConnectStoreTest：构造嵌套 token 污染 payload；如果没有这行，递归脱敏无法覆盖 OAuth 风险。
    const serialized = JSON.stringify(redactedProviderPayload(polluted)); // 新增代码+OpenAIConnectStoreTest：执行脱敏并序列化；如果没有这行，后续断言没有实际输入。
    expect(serialized).not.toContain("access_token"); // 新增代码+OpenAIConnectStoreTest：确认 access token 字段被移除；如果没有这行，真实 OAuth access token 可能进 renderer。
    expect(serialized).not.toContain("refresh_token"); // 新增代码+OpenAIConnectStoreTest：确认 refresh token 字段被移除；如果没有这行，长期凭据可能泄漏。
    expect(serialized).not.toContain("id_token"); // 新增代码+OpenAIConnectStoreTest：确认 id token 字段被移除；如果没有这行，身份 token 可能泄漏。
    expect(serialized).not.toContain("unit-test-refresh-token"); // 新增代码+OpenAIConnectStoreTest：确认嵌套 token 值被移除；如果没有这行，仅移除键名但保留值的 bug 会漏过。
  }); // 新增代码+OpenAIConnectStoreTest：OAuth token 脱敏测试结束；如果没有这行，测试块语法不完整。

  it("sorts providers, keeps custom CTA separate, and groups models", () => { // 修改代码+ProviderSettingsStoreTest：测试段开始，验证排序、CTA 和模型分组；如果没有这段，Provider/Models 页会出现顺序和空状态错误。
    const viewModel = buildProviderSettingsViewModel(providerPayload); // 修改代码+ProviderSettingsStoreTest：构建 view model；如果没有这行，后续断言没有输入。
    const rows = providerRowsForDisplay(viewModel); // 修改代码+ProviderSettingsStoreTest：获取展示 provider 行；如果没有这行，无法验证排序。
    const groups = modelGroupsForDisplay(viewModel); // 修改代码+ProviderSettingsStoreTest：获取模型分组；如果没有这行，无法验证 Models 页输入。
    expect(rows.map((row) => row.id)).toEqual(["openai", "github-copilot", "openrouter"]); // 修改代码+ProviderSettingsStoreTest：确认已连接 provider 在前且 popular 顺序稳定；如果没有这行，列表会抖动。
    expect(viewModel.customProviderCta.id).toBe("custom-provider-cta"); // 修改代码+ProviderSettingsStoreTest：确认 CTA 单独存在；如果没有这行，custom CTA 可能被误当 provider。
    expect(rows[1].primaryActionDisabled).toBe(true); // 修改代码+ProviderSettingsStoreTest：确认 Copilot V1 操作禁用；如果没有这行，用户会被误导去连接。
    expect(rows[1].models).toEqual([]); // 修改代码+ProviderSettingsStoreTest：确认缺 models 会转成空数组；如果没有这行，Models 页可能崩溃。
    expect(groups[0].providerId).toBe("openai"); // 修改代码+ProviderSettingsStoreTest：确认模型按 provider 分组；如果没有这行，模型页无法显示来源。
    expect(groups[0].models[0].displayName).toBe("GPT-4.1"); // 修改代码+ProviderSettingsStoreTest：确认 snake_case 转 camelCase；如果没有这行，组件字段名会对不上。
  }); // 修改代码+ProviderSettingsStoreTest：排序和分组测试结束；如果没有这行，测试块语法不完整。

  it("keeps OpenAI auth method metadata for the method picker", () => { // 新增代码+OpenAIConnectStoreTest：测试段开始，验证方法选择器所需元数据；如果没有这段，UI 只能看到 id/label 而不知道渲染哪种流程。
    const viewModel = buildProviderSettingsViewModel(providerPayload); // 新增代码+OpenAIConnectStoreTest：构建 view model；如果没有这行，后续断言没有输入。
    const openai = providerRowsForDisplay(viewModel)[0]; // 新增代码+OpenAIConnectStoreTest：读取排序后的 OpenAI 行；如果没有这行，无法断言 OpenAI 三方法。
    expect(openai.authMethods.map((method) => method.id)).toEqual(["chatgpt-browser", "chatgpt-headless", "api-key"]); // 新增代码+OpenAIConnectStoreTest：确认三方法顺序被保留；如果没有这行，连接向导会显示错误顺序。
    expect(openai.authMethods[0].methodType).toBe("oauth"); // 修改代码+OpenAIConnectStoreTest：确认 browser 方法保留 oauth 类型；如果没有这行，前端无法进入自动授权 UI。
    expect(openai.authMethods[0].mode).toBe("auto"); // 修改代码+OpenAIConnectStoreTest：确认 browser 方法保留 auto 模式；如果没有这行，前端不会启动 attempt 轮询。
    expect(openai.authMethods[0].experimental).toBe(true); // 修改代码+OpenAIConnectStoreTest：确认 browser 方法保留实验标记；如果没有这行，UI 会弱化 mock/实验边界。
    expect(openai.authMethods[2].methodType).toBe("api"); // 修改代码+OpenAIConnectStoreTest：确认 API key 方法保留 api 类型；如果没有这行，真实密钥表单无法被可靠识别。
    expect(openai.authMethods[2].mode).toBe("form"); // 修改代码+OpenAIConnectStoreTest：确认 API key 方法保留 form 模式；如果没有这行，前端可能误启动 OAuth flow。
  }); // 新增代码+OpenAIConnectStoreTest：方法元数据测试结束；如果没有这行，测试块语法不完整。
}); // 修改代码+ProviderSettingsStoreTest：测试段结束；如果没有这行，describe 语法不完整。
