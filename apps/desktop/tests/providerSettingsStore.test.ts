import { describe, expect, it } from "vitest"; // 新增代码+ProviderSettingsStoreTest：导入 Vitest 工具；如果没有这行，provider store 合同无法自动验证。
import { buildProviderSettingsViewModel, modelGroupsForDisplay, providerRowsForDisplay, redactedProviderPayload } from "../src/state/providerSettingsStore"; // 新增代码+ProviderSettingsStoreTest：导入 provider settings 纯函数；如果没有这行，测试没有被测目标。


const providerPayload = { // 新增代码+ProviderSettingsStoreTest：定义后端 provider settings fixture；如果没有这段，多个测试会重复构造 payload。
  ok: true, // 新增代码+ProviderSettingsStoreTest：模拟成功响应；如果没有这行，view model 无法识别 payload。
  schema_version: 2, // 新增代码+ProviderSettingsStoreTest：模拟 V2 schema；如果没有这行，版本字段缺失不会被发现。
  secret_store: { kind: "dev_json", label: "本地开发密钥存储", warning: "开发警告" }, // 新增代码+ProviderSettingsStoreTest：模拟 dev secret store；如果没有这行，warning copy 无法测试。
  custom_provider_cta: { id: "custom-provider-cta", display_name: "自定义提供商", description: "添加兼容 provider" }, // 新增代码+ProviderSettingsStoreTest：模拟虚拟 CTA；如果没有这行，自定义入口无法测试。
  default_provider_id: "", // 新增代码+ProviderSettingsStoreTest：模拟默认 provider；如果没有这行，payload 形状不完整。
  default_model_id: "", // 新增代码+ProviderSettingsStoreTest：模拟默认模型；如果没有这行，payload 形状不完整。
  providers: [ // 新增代码+ProviderSettingsStoreTest：开始 provider 列表；如果没有这行，排序和分组没有输入。
    { id: "openrouter", display_name: "OpenRouter", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "api-key", label: "API 密钥", enabled: true, status: "available", fields: ["secret"], help_text: "help" }], description: "OpenRouter", models: [] }, // 新增代码+ProviderSettingsStoreTest：模拟未连接 provider；如果没有这行，排序无法比较连接状态。
    { id: "openai", display_name: "OpenAI", kind: "built_in", source: "config", connected: true, masked_key: "sk••••xx", auth_methods: [{ id: "api-key", label: "API 密钥", enabled: true, status: "available", fields: ["secret"], help_text: "help" }], description: "OpenAI", api_key: "unit-test-secret-value", models: [{ id: "gpt-4.1", display_name: "GPT-4.1", provider_id: "openai", visible: true, supports_tools: true, supports_vision: true }] }, // 新增代码+ProviderSettingsStoreTest：模拟已连接 provider 且夹带危险字段；如果没有这行，脱敏测试不真实。
    { id: "github-copilot", display_name: "GitHub Copilot", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "device-code", label: "设备码", enabled: false, status: "unsupported_v1", fields: [], help_text: "unsupported" }], description: "Copilot", models: undefined }, // 新增代码+ProviderSettingsStoreTest：模拟 unsupported auth 和缺 models；如果没有这行，禁用按钮和空数组兼容无法测试。
  ], // 新增代码+ProviderSettingsStoreTest：provider 列表结束；如果没有这行，fixture 语法不完整。
}; // 新增代码+ProviderSettingsStoreTest：fixture 结束；如果没有这行，常量语法不完整。


describe("providerSettingsStore", () => { // 新增代码+ProviderSettingsStoreTest：测试段开始，覆盖 provider settings view model；如果没有这段，设置页会直接消费后端原始 JSON。
  it("redacts unsafe backend fields before building the view model", () => { // 新增代码+ProviderSettingsStoreTest：测试段开始，验证危险字段脱敏；如果没有这段，后端 bug 可能把 secret 带进 renderer state。
    const safePayload = redactedProviderPayload(providerPayload); // 新增代码+ProviderSettingsStoreTest：执行 payload 脱敏；如果没有这行，后续断言没有输入。
    const serialized = JSON.stringify(safePayload); // 新增代码+ProviderSettingsStoreTest：序列化脱敏结果；如果没有这行，嵌套字段泄露可能漏过。
    expect(serialized).not.toContain("api_key"); // 新增代码+ProviderSettingsStoreTest：确认 snake_case secret 字段移除；如果没有这行，renderer 可能持有 raw key。
    expect(serialized).not.toContain("unit-test-secret-value"); // 新增代码+ProviderSettingsStoreTest：确认 raw secret 值移除；如果没有这行，截图/日志可能泄密。
  }); // 新增代码+ProviderSettingsStoreTest：脱敏测试结束；如果没有这行，测试块语法不完整。

  it("sorts providers, keeps custom CTA separate, and groups models", () => { // 新增代码+ProviderSettingsStoreTest：测试段开始，验证排序、CTA 和模型分组；如果没有这段，Provider/Models 页会出现顺序和空状态错误。
    const viewModel = buildProviderSettingsViewModel(providerPayload); // 新增代码+ProviderSettingsStoreTest：构建 view model；如果没有这行，后续断言没有输入。
    const rows = providerRowsForDisplay(viewModel); // 新增代码+ProviderSettingsStoreTest：获取展示 provider 行；如果没有这行，无法验证排序。
    const groups = modelGroupsForDisplay(viewModel); // 新增代码+ProviderSettingsStoreTest：获取模型分组；如果没有这行，无法验证 Models 页输入。
    expect(rows.map((row) => row.id)).toEqual(["openai", "github-copilot", "openrouter"]); // 新增代码+ProviderSettingsStoreTest：确认已连接 provider 在前且 popular 顺序稳定；如果没有这行，列表会抖动。
    expect(viewModel.customProviderCta.id).toBe("custom-provider-cta"); // 新增代码+ProviderSettingsStoreTest：确认 CTA 单独存在；如果没有这行，custom CTA 可能被误当 provider。
    expect(rows[1].primaryActionDisabled).toBe(true); // 新增代码+ProviderSettingsStoreTest：确认 Copilot V1 操作禁用；如果没有这行，用户会被误导去连接。
    expect(rows[1].models).toEqual([]); // 新增代码+ProviderSettingsStoreTest：确认缺 models 会转成空数组；如果没有这行，Models 页可能崩溃。
    expect(groups[0].providerId).toBe("openai"); // 新增代码+ProviderSettingsStoreTest：确认模型按 provider 分组；如果没有这行，模型页无法显示来源。
    expect(groups[0].models[0].displayName).toBe("GPT-4.1"); // 新增代码+ProviderSettingsStoreTest：确认 snake_case 转 camelCase；如果没有这行，组件字段名会对不上。
  }); // 新增代码+ProviderSettingsStoreTest：排序和分组测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsStoreTest：测试段结束；如果没有这行，describe 语法不完整。
