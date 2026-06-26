import { describe, expect, it } from "vitest"; // 新增代码+ProviderSettingsDialogModelTest：导入 Vitest 工具；如果没有这行，设置弹窗 view model 合同无法自动验证。
import { authAttemptPollDecision } from "../src/components/settings/SettingsDialog"; // 新增代码+OpenAIConnectPollRaceTest：导入 auth-attempt 轮询决策 helper；如果没有这行，测试无法锁住 complete 状态先刷新 catalog 的竞态规则。
import { buildProviderSettingsViewModel } from "../src/state/providerSettingsStore"; // 新增代码+ProviderSettingsDialogModelTest：导入 provider settings view model builder；如果没有这行，测试没有被测目标。


describe("provider settings dialog view model", () => { // 新增代码+ProviderSettingsDialogModelTest：测试段开始，覆盖设置弹窗需要的派生状态；如果没有这段，弹窗可能误显示 secret store 或 auth 状态。
  it("exposes dev secret warning and disabled auth methods for the dialog", () => { // 新增代码+ProviderSettingsDialogModelTest：测试段开始，验证 warning copy 和 disabled auth；如果没有这段，用户可能不知道当前密钥存储只是开发模式。
    const model = buildProviderSettingsViewModel({ ok: true, schema_version: 3, secret_store: { kind: "dev_json", label: "本地开发密钥存储", warning: "开发模式警告" }, providers: [{ id: "github-copilot", display_name: "GitHub Copilot", kind: "built_in", source: "none", connected: false, masked_key: "", auth_methods: [{ id: "device-code", label: "设备码", enabled: false, status: "unsupported_v1", type: "oauth", mode: "auto", fields: [], help_text: "暂未支持", experimental: true }], description: "Copilot", models: [] }], custom_provider_cta: { id: "custom-provider-cta", display_name: "自定义提供商", description: "添加 provider" }, default_provider_id: "", default_model_id: "" }); // 修改代码+OpenAIConnectStoreTest：构造 V3 弹窗输入 payload；如果没有这行，warning/disabled auth 没有输入。
    expect(model.defaultTab).toBe("providers"); // 新增代码+ProviderSettingsDialogModelTest：确认默认打开 provider 页；如果没有这行，设置按钮可能打开空页。
    expect(model.secretStoreWarning).toBe("开发模式警告"); // 新增代码+ProviderSettingsDialogModelTest：确认 dev_json warning 暴露给 UI；如果没有这行，用户可能误以为密钥是生产安全存储。
    expect(model.providers[0].primaryActionLabel).toBe("暂未支持"); // 新增代码+ProviderSettingsDialogModelTest：确认 unsupported provider 显示禁用文案；如果没有这行，Copilot 可能显示连接按钮。
    expect(model.customProviderCta.displayName).toBe("自定义提供商"); // 新增代码+ProviderSettingsDialogModelTest：确认自定义 CTA 可渲染；如果没有这行，添加 provider 入口可能丢失。
  }); // 新增代码+ProviderSettingsDialogModelTest：弹窗 view model 测试结束；如果没有这行，测试块语法不完整。
  it("refreshes provider catalog before exposing a completed auth-attempt to the dialog", () => { // 新增代码+OpenAIConnectPollRaceTest：测试段开始，复现 complete 状态先 set attempt 会触发 effect cleanup 的竞态；如果没有这段，视觉 QA 发现的连接后不关闭弹窗问题会回归。
    const decision = authAttemptPollDecision("complete"); // 新增代码+OpenAIConnectPollRaceTest：计算 complete 状态的轮询动作；如果没有这行，后续断言没有被测结果。
    expect(decision.refreshProviderSettings).toBe(true); // 新增代码+OpenAIConnectPollRaceTest：确认 complete 必须刷新 provider catalog；如果没有这行，OpenAI 行不会变成已连接。
    expect(decision.keepAttemptVisibleBeforeRefresh).toBe(false); // 新增代码+OpenAIConnectPollRaceTest：确认 complete 不能先写回本地 attempt；如果没有这行，React effect 会先清理旧轮询并阻断刷新落地。
    expect(decision.safeErrorMessage).toBe(""); // 新增代码+OpenAIConnectPollRaceTest：确认 complete 不是错误状态；如果没有这行，成功授权可能被误显示为失败。
  }); // 新增代码+OpenAIConnectPollRaceTest：complete 状态竞态测试结束；如果没有这行，测试块语法不完整。
  it("keeps pending auth-attempt visible and marks failed auth-attempts as safe errors", () => { // 新增代码+OpenAIConnectPollRaceTest：测试段开始，锁住 pending 和 failed 的原有行为；如果没有这段，修复 complete 时可能破坏等待态或失败态。
    expect(authAttemptPollDecision("pending")).toEqual({ refreshProviderSettings: false, keepAttemptVisibleBeforeRefresh: true, safeErrorMessage: "" }); // 新增代码+OpenAIConnectPollRaceTest：确认 pending 仍更新等待页；如果没有这行，用户看不到等待授权状态变化。
    expect(authAttemptPollDecision("failed")).toEqual({ refreshProviderSettings: false, keepAttemptVisibleBeforeRefresh: true, safeErrorMessage: "授权未完成" }); // 新增代码+OpenAIConnectPollRaceTest：确认 failed 显示固定安全错误；如果没有这行，用户看不到授权失败且底层错误可能泄露。
    expect(authAttemptPollDecision("expired")).toEqual({ refreshProviderSettings: false, keepAttemptVisibleBeforeRefresh: true, safeErrorMessage: "授权未完成" }); // 新增代码+OpenAIConnectPollRaceTest：确认 expired 显示固定安全错误；如果没有这行，取消或过期可能继续显示等待。
  }); // 新增代码+OpenAIConnectPollRaceTest：pending/failed/expired 行为测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsDialogModelTest：测试段结束；如果没有这行，describe 语法不完整。
