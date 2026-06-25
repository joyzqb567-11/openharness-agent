import { describe, expect, it } from "vitest"; // 新增代码+ProviderSettingsDialogModelTest：导入 Vitest 工具；如果没有这行，设置弹窗 view model 合同无法自动验证。
import { buildProviderSettingsViewModel } from "../src/state/providerSettingsStore"; // 新增代码+ProviderSettingsDialogModelTest：导入 provider settings view model builder；如果没有这行，测试没有被测目标。


describe("provider settings dialog view model", () => { // 新增代码+ProviderSettingsDialogModelTest：测试段开始，覆盖设置弹窗需要的派生状态；如果没有这段，弹窗可能误显示 secret store 或 auth 状态。
  it("exposes dev secret warning and disabled auth methods for the dialog", () => { // 新增代码+ProviderSettingsDialogModelTest：测试段开始，验证 warning copy 和 disabled auth；如果没有这段，用户可能不知道当前密钥存储只是开发模式。
    const model = buildProviderSettingsViewModel({ ok: true, schema_version: 2, secret_store: { kind: "dev_json", label: "本地开发密钥存储", warning: "开发模式警告" }, providers: [{ id: "github-copilot", display_name: "GitHub Copilot", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "device-code", label: "设备码", enabled: false, status: "unsupported_v1", fields: [], help_text: "暂未支持" }], description: "Copilot", models: [] }], custom_provider_cta: { id: "custom-provider-cta", display_name: "自定义提供商", description: "添加 provider" }, default_provider_id: "", default_model_id: "" }); // 新增代码+ProviderSettingsDialogModelTest：构造弹窗输入 payload；如果没有这行，warning/disabled auth 没有输入。
    expect(model.defaultTab).toBe("providers"); // 新增代码+ProviderSettingsDialogModelTest：确认默认打开 provider 页；如果没有这行，设置按钮可能打开空页。
    expect(model.secretStoreWarning).toBe("开发模式警告"); // 新增代码+ProviderSettingsDialogModelTest：确认 dev_json warning 暴露给 UI；如果没有这行，用户可能误以为密钥是生产安全存储。
    expect(model.providers[0].primaryActionLabel).toBe("暂未支持"); // 新增代码+ProviderSettingsDialogModelTest：确认 unsupported provider 显示禁用文案；如果没有这行，Copilot 可能显示连接按钮。
    expect(model.customProviderCta.displayName).toBe("自定义提供商"); // 新增代码+ProviderSettingsDialogModelTest：确认自定义 CTA 可渲染；如果没有这行，添加 provider 入口可能丢失。
  }); // 新增代码+ProviderSettingsDialogModelTest：弹窗 view model 测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsDialogModelTest：测试段结束；如果没有这行，describe 语法不完整。
