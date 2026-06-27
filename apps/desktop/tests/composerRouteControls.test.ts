import { describe, expect, it } from "vitest"; // 新增代码+ComposerRouteControlsTest：导入 Vitest 测试工具；如果没有这行，底部路由纯函数没有自动化验证入口。
import { composerModelOptionsFromProviderSettings, nextComposerRouteAfterProviderSettings, type ComposerRouteState } from "../src/components/AppShell"; // 新增代码+ComposerRouteControlsTest：导入 AppShell 路由派生 helper；如果没有这行，断开 provider 和模型重置规则无法单测。
import type { ProviderSettingsViewModel } from "../src/state/providerSettingsStore"; // 新增代码+ComposerRouteControlsTest：导入 provider settings view model 类型；如果没有这行，fixture 字段含义不清楚。

const baseRoute: ComposerRouteState = { selectedProviderId: "", selectedModelId: "", reasoningEffort: "ultra", permissionMode: "full_access" }; // 新增代码+ComposerRouteControlsTest：定义默认 composer 路由；如果没有这行，每个断言都要重复写权限和推理字段。

function openAiViewModel(connected: boolean): ProviderSettingsViewModel { // 新增代码+ComposerRouteControlsTest：函数段开始，生成 OpenAI provider fixture；如果没有这段，多个测试会重复手写复杂对象。
  return { // 新增代码+ComposerRouteControlsTest：返回完整 view model；如果没有这行，函数没有输出。
    defaultTab: "providers", // 新增代码+ComposerRouteControlsTest：声明默认设置页；如果没有这行，view model 形状不完整。
    schemaVersion: 3, // 新增代码+ComposerRouteControlsTest：声明 provider settings schema；如果没有这行，fixture 与真实 V3 合同不一致。
    secretStoreWarning: "", // 新增代码+ComposerRouteControlsTest：声明无 secret store 警告；如果没有这行，view model 形状不完整。
    defaultProviderId: "openai", // 新增代码+ComposerRouteControlsTest：声明默认 provider 是 OpenAI；如果没有这行，自动选择规则没有默认来源。
    defaultModelId: "gpt-5.5", // 新增代码+ComposerRouteControlsTest：声明默认模型；如果没有这行，自动选择规则无法验证 gpt-5.5。
    customProviderCta: { id: "custom-provider-cta", displayName: "自定义提供商", description: "添加兼容 provider" }, // 新增代码+ComposerRouteControlsTest：声明自定义 CTA；如果没有这行，view model 形状不完整。
    providers: [{ id: "openai", displayName: "OpenAI", kind: "built_in", source: connected ? "oauth" : "none", connected, maskedKey: connected ? "ChatGPT OAuth" : "", accountLabel: connected ? "jo***@example.com" : "", directRouteStatus: connected ? "direct_sse_ready" : "", oauthClientSource: connected ? "operator_configured" : "", description: "OpenAI", authMethods: [], primaryActionLabel: connected ? "断开" : "+ 连接", primaryActionDisabled: false, models: [{ id: "gpt-5.5", displayName: "GPT-5.5", providerId: "openai", visible: true, supportsTools: true, supportsVision: true, state: "available", source: "probe_available_models", message: "" }, { id: "gpt-4.1", displayName: "GPT-4.1", providerId: "openai", visible: true, supportsTools: true, supportsVision: true, state: "not_supported_for_account", source: "probe_available_models", message: "当前账号不支持" }] }], // 新增代码+ComposerRouteControlsTest：声明 OpenAI 模型列表含可用和不支持模型；如果没有这行，禁用和自动选择规则没有事实输入。
  }; // 新增代码+ComposerRouteControlsTest：view model 返回对象结束；如果没有这行，对象语法不完整。
} // 新增代码+ComposerRouteControlsTest：函数段结束，openAiViewModel 到此结束；如果没有这行，函数语法不完整。

describe("composer route controls", () => { // 新增代码+ComposerRouteControlsTest：测试组开始，覆盖底部模型/权限/推理路由；如果没有这段，断开后旧模型可能回归。
  it("builds model options from connected providers and disables unsupported models", () => { // 新增代码+ComposerRouteControlsTest：测试模型下拉选项；如果没有这段，不支持模型可能仍可提交。
    const options = composerModelOptionsFromProviderSettings(openAiViewModel(true)); // 新增代码+ComposerRouteControlsTest：从 connected catalog 派生下拉选项；如果没有这行，后续断言没有输入。
    expect(options.map((option) => option.modelId)).toEqual(["gpt-5.5", "gpt-4.1"]); // 新增代码+ComposerRouteControlsTest：确认可见模型进入菜单；如果没有这行，模型列表可能缺项。
    expect(options.find((option) => option.modelId === "gpt-4.1")?.disabled).toBe(true); // 新增代码+ComposerRouteControlsTest：确认账号不支持模型被禁用；如果没有这行，用户可能选中必失败模型。
  }); // 新增代码+ComposerRouteControlsTest：模型下拉选项测试结束；如果没有这行，测试块语法不完整。

  it("auto-selects the first available connected model", () => { // 新增代码+ComposerRouteControlsTest：测试 OAuth 成功后的自动选择；如果没有这段，连接后仍可能显示“选择模型”。
    const nextRoute = nextComposerRouteAfterProviderSettings(baseRoute, openAiViewModel(true)); // 新增代码+ComposerRouteControlsTest：用空路由和 connected catalog 计算下一状态；如果没有这行，自动选择没有被测结果。
    expect(nextRoute.selectedProviderId).toBe("openai"); // 新增代码+ComposerRouteControlsTest：确认自动选中 OpenAI；如果没有这行，provider 可能丢失。
    expect(nextRoute.selectedModelId).toBe("gpt-5.5"); // 新增代码+ComposerRouteControlsTest：确认自动选中可用默认模型；如果没有这行，后端可能收到空模型。
    expect(nextRoute.permissionMode).toBe("full_access"); // 新增代码+ComposerRouteControlsTest：确认权限选择不被 catalog 刷新覆盖；如果没有这行，用户授权可能被重置。
  }); // 新增代码+ComposerRouteControlsTest：自动选择测试结束；如果没有这行，测试块语法不完整。

  it("resets provider and model when OpenAI disconnects", () => { // 新增代码+ComposerRouteControlsTest：测试断开连接后的清空规则；如果没有这段，断开后仍可能提交旧模型。
    const currentRoute: ComposerRouteState = { ...baseRoute, selectedProviderId: "openai", selectedModelId: "gpt-5.5" }; // 新增代码+ComposerRouteControlsTest：模拟已选 OpenAI 模型；如果没有这行，断开场景没有输入。
    const nextRoute = nextComposerRouteAfterProviderSettings(currentRoute, openAiViewModel(false)); // 新增代码+ComposerRouteControlsTest：用 disconnected catalog 计算下一状态；如果没有这行，断开清理没有被测结果。
    expect(nextRoute.selectedProviderId).toBe(""); // 新增代码+ComposerRouteControlsTest：确认 provider 被清空；如果没有这行，提交可能继续带 openai。
    expect(nextRoute.selectedModelId).toBe(""); // 新增代码+ComposerRouteControlsTest：确认模型被清空；如果没有这行，下拉不会回到“选择模型”。
    expect(nextRoute.reasoningEffort).toBe("ultra"); // 新增代码+ComposerRouteControlsTest：确认推理档位保留；如果没有这行，断开 provider 会不必要重置用户偏好。
  }); // 新增代码+ComposerRouteControlsTest：断开清空测试结束；如果没有这行，测试块语法不完整。

  it("clears a selected model that is known unsupported for the account", () => { // 新增代码+ComposerRouteControlsTest：测试账号不支持模型的清理规则；如果没有这段，慢失败模型会反复进入后端。
    const currentRoute: ComposerRouteState = { ...baseRoute, selectedProviderId: "openai", selectedModelId: "gpt-4.1" }; // 新增代码+ComposerRouteControlsTest：模拟用户仍选着账号不支持模型；如果没有这行，unsupported 场景没有输入。
    const nextRoute = nextComposerRouteAfterProviderSettings(currentRoute, openAiViewModel(true)); // 新增代码+ComposerRouteControlsTest：用 connected catalog 重新校验路由；如果没有这行，unsupported 清理没有被测结果。
    expect(nextRoute.selectedProviderId).toBe("openai"); // 新增代码+ComposerRouteControlsTest：确认 provider 保留；如果没有这行，清模型会误断开 provider。
    expect(nextRoute.selectedModelId).toBe(""); // 新增代码+ComposerRouteControlsTest：确认不支持模型被清空；如果没有这行，Direct SSE 会重复撞已知不可用模型。
  }); // 新增代码+ComposerRouteControlsTest：unsupported 清理测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ComposerRouteControlsTest：测试组结束；如果没有这行，describe 语法不完整。
