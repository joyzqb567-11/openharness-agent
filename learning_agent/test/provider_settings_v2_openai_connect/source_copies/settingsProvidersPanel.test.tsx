import { isValidElement, type ReactElement, type ReactNode } from "react"; // 新增代码+ProviderSettingsPanelTest：导入 React 元素判断工具；如果没有这行，测试无法安全遍历组件树。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+ProviderSettingsPanelTest：导入服务端渲染工具；如果没有这行，测试无法在无浏览器环境检查 Provider UI 文案。
import { describe, expect, it, vi } from "vitest"; // 新增代码+ProviderSettingsPanelTest：导入 Vitest 工具；如果没有这行，Provider 面板行为无法自动验证。
import { ProviderConnectDialog } from "../src/components/settings/ProviderConnectDialog"; // 新增代码+ProviderSettingsPanelTest：导入连接弹窗；如果没有这行，API key 输入和提交状态无法测试。
import { SettingsProvidersPanel, probeStatusLabel } from "../src/components/settings/SettingsProvidersPanel"; // 新增代码+ProviderSettingsPanelTest：导入 Provider 面板和探针文案 helper；如果没有这行，列表和连接测试文案没有被测对象。
import type { ProviderRowView, ProviderSettingsViewModel } from "../src/state/providerSettingsStore"; // 新增代码+ProviderSettingsPanelTest：导入 Provider view model 类型；如果没有这行，fixture 字段含义不清楚。

function flattenChildren(children: ReactNode): ReactElement[] { // 新增代码+ProviderSettingsPanelTest：函数段开始，把 JSX children 展平成元素数组；如果没有这段，测试很难找到嵌套按钮。
  const values = Array.isArray(children) ? children : [children]; // 新增代码+ProviderSettingsPanelTest：把单个 child 也转成数组；如果没有这行，单节点 children 无法统一遍历。
  return values.flatMap((child) => Array.isArray(child) ? flattenChildren(child) : isValidElement(child) ? [child] : []); // 修改代码+ProviderSettingsPanelTest：递归展开 rows.map 产生的数组并只保留 React 元素；如果没有这行，provider 行按钮会被测试辅助函数漏掉。
} // 新增代码+ProviderSettingsPanelTest：函数段结束，flattenChildren 到此结束；如果没有这行，函数语法不完整。

function findByTestId(node: ReactElement, testId: string): ReactElement | null { // 新增代码+ProviderSettingsPanelTest：函数段开始，按 data-testid 查找元素；如果没有这段，测试只能依赖脆弱的 JSX 下标。
  if (node.props["data-testid"] === testId) { // 新增代码+ProviderSettingsPanelTest：检查当前节点是否命中；如果没有这行，目标按钮无法被识别。
    return node; // 新增代码+ProviderSettingsPanelTest：命中时返回当前节点；如果没有这行，查找会错过当前节点。
  } // 新增代码+ProviderSettingsPanelTest：当前节点命中分支结束；如果没有这行，条件块语法不完整。
  for (const child of flattenChildren(node.props.children)) { // 新增代码+ProviderSettingsPanelTest：遍历子元素；如果没有这行，嵌套按钮不会被找到。
    const found = findByTestId(child, testId); // 新增代码+ProviderSettingsPanelTest：递归查找子树；如果没有这行，查找只能停在一层。
    if (found !== null) { // 新增代码+ProviderSettingsPanelTest：判断子树是否命中；如果没有这行，找到结果不会提前返回。
      return found; // 新增代码+ProviderSettingsPanelTest：返回子树命中节点；如果没有这行，测试会继续遍历并最终失败。
    } // 新增代码+ProviderSettingsPanelTest：子树命中分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+ProviderSettingsPanelTest：子元素遍历结束；如果没有这行，for 循环语法不完整。
  return null; // 新增代码+ProviderSettingsPanelTest：没有找到时返回 null；如果没有这行，函数返回值不稳定。
} // 新增代码+ProviderSettingsPanelTest：函数段结束，findByTestId 到此结束；如果没有这行，函数语法不完整。

const providerRows: ProviderRowView[] = [ // 新增代码+ProviderSettingsPanelTest：定义 provider 行 fixture；如果没有这段，列表状态没有输入。
  { id: "openai", displayName: "OpenAI", kind: "built_in", source: "config", connected: true, maskedKey: "sk••••xx", description: "使用 ChatGPT Pro/Plus 或 API 密钥连接", authMethods: [{ id: "api-key", label: "API 密钥", enabled: true, status: "available", methodType: "api", mode: "form", fields: ["secret"], helpText: "help", experimental: false }], models: [], primaryActionLabel: "断开", primaryActionDisabled: false }, // 修改代码+OpenAIConnectPanelTest：模拟已连接 provider 的新 auth method view；如果没有这行，断开和测试连接按钮无法验证。
  { id: "github-copilot", displayName: "GitHub Copilot", kind: "built_in", source: "none", connected: false, maskedKey: "", description: "使用 Copilot 或 API 密钥连接", authMethods: [{ id: "device-code", label: "设备码", enabled: false, status: "unsupported_v1", methodType: "oauth", mode: "auto", fields: [], helpText: "unsupported", experimental: true }], models: [], primaryActionLabel: "暂未支持", primaryActionDisabled: true }, // 修改代码+OpenAIConnectPanelTest：模拟 V1 未支持 provider 的新 auth method view；如果没有这行，禁用按钮无法验证。
  { id: "openrouter", displayName: "OpenRouter", kind: "built_in", source: "none", connected: false, maskedKey: "", description: "使用 OpenRouter 账号或 API 密钥连接", authMethods: [{ id: "api-key", label: "API 密钥", enabled: true, status: "available", methodType: "api", mode: "form", fields: ["secret"], helpText: "help", experimental: false }], models: [], primaryActionLabel: "+ 连接", primaryActionDisabled: false }, // 修改代码+OpenAIConnectPanelTest：模拟可连接 provider 的新 auth method view；如果没有这行，连接按钮无法验证。
]; // 新增代码+ProviderSettingsPanelTest：provider 行 fixture 结束；如果没有这行，数组语法不完整。

const viewModel: ProviderSettingsViewModel = { // 新增代码+ProviderSettingsPanelTest：定义 Provider Settings view model；如果没有这段，面板没有完整输入。
  defaultTab: "providers", // 新增代码+ProviderSettingsPanelTest：声明默认页签；如果没有这行，view model 形状不完整。
  schemaVersion: 3, // 修改代码+OpenAIConnectPanelTest：声明 provider settings V3 schema；如果没有这行，view model 形状不完整。
  secretStoreWarning: "开发警告", // 新增代码+ProviderSettingsPanelTest：声明 dev secret warning；如果没有这行，view model 形状不完整。
  providers: providerRows, // 新增代码+ProviderSettingsPanelTest：注入 provider 行；如果没有这行，面板会显示空态。
  customProviderCta: { id: "custom-provider-cta", displayName: "自定义提供商", description: "通过基础 URL 添加与 OpenAI 兼容的提供商。" }, // 新增代码+ProviderSettingsPanelTest：注入虚拟自定义入口；如果没有这行，自定义 provider 入口无法测试。
  defaultProviderId: "", // 新增代码+ProviderSettingsPanelTest：声明默认 provider；如果没有这行，view model 形状不完整。
  defaultModelId: "", // 新增代码+ProviderSettingsPanelTest：声明默认模型；如果没有这行，view model 形状不完整。
}; // 新增代码+ProviderSettingsPanelTest：view model fixture 结束；如果没有这行，对象语法不完整。

const openAiPickerProvider: ProviderRowView = { id: "openai", displayName: "OpenAI", kind: "built_in", source: "none", connected: false, maskedKey: "", description: "使用 ChatGPT Pro/Plus 或 API 密钥连接", authMethods: [{ id: "chatgpt-browser", label: "ChatGPT Pro/Plus (browser)", enabled: true, status: "mock_available", methodType: "oauth", mode: "auto", fields: [], helpText: "browser", experimental: true }, { id: "chatgpt-headless", label: "ChatGPT Pro/Plus (headless)", enabled: true, status: "mock_available", methodType: "oauth", mode: "auto", fields: [], helpText: "headless", experimental: true }, { id: "api-key", label: "API 密钥", enabled: true, status: "available", methodType: "api", mode: "form", fields: ["secret"], helpText: "help", experimental: false }], models: [], primaryActionLabel: "+ 连接", primaryActionDisabled: false }; // 新增代码+OpenAIConnectPanelTest：定义 OpenAI 三方法连接 fixture；如果没有这行，方法选择器无法被独立测试。
const openAiHeadlessOnlyProvider: ProviderRowView = { id: "openai", displayName: "OpenAI", kind: "built_in", source: "none", connected: false, maskedKey: "", description: "使用 ChatGPT Pro/Plus 或 API 密钥连接", authMethods: [{ id: "chatgpt-headless", label: "ChatGPT Pro/Plus (headless)", enabled: true, status: "mock_available", methodType: "oauth", mode: "auto", fields: [], helpText: "headless", experimental: true }], models: [], primaryActionLabel: "+ 连接", primaryActionDisabled: false }; // 新增代码+OpenAIConnectPanelTest：定义单一 headless 方法 provider；如果没有这行，静态渲染很难直接进入等待授权步骤。
const pendingOpenAiAuthAttempt = { attempt_id: "auth_attempt_test", provider_id: "openai", auth_method_id: "chatgpt-headless", mode: "mock", url: "https://auth.openai.test/device", instructions: "访问此链接并输入设备码，以完成 mock ChatGPT 授权。", display_code: "MOCK-OPENAI-123456", display_code_kind: "device_code", display_code_copyable: true, status: "pending", message: "", created_at: 1, expires_at: 2 }; // 新增代码+OpenAIConnectPanelTest：定义 pending auth-attempt fixture；如果没有这行，等待页无法验证链接、确认码和状态文案。

describe("SettingsProvidersPanel", () => { // 新增代码+ProviderSettingsPanelTest：测试段开始，覆盖 Provider 列表和连接弹窗；如果没有这段，Task 6 没有自动验收。
  it("renders provider rows with connection actions and safe probe labels", () => { // 新增代码+ProviderSettingsPanelTest：测试段开始，验证 provider 列表视觉文案；如果没有这段，列表状态可能退化。
    const panel = <SettingsProvidersPanel viewModel={viewModel} loading={false} errorMessage="" busyProviderId="" probeResults={{ openai: "ok" }} onRetry={vi.fn()} onConnectProvider={vi.fn()} onDisconnectProvider={vi.fn()} onTestProvider={vi.fn()} onOpenCustomProvider={vi.fn()} />; // 新增代码+ProviderSettingsPanelTest：渲染 Provider 面板；如果没有这行，后续断言没有输入。
    const markup = renderToStaticMarkup(panel); // 新增代码+ProviderSettingsPanelTest：把面板转为静态 HTML；如果没有这行，文本状态无法断言。
    expect(markup).toContain("OpenAI"); // 新增代码+ProviderSettingsPanelTest：确认 provider 名称显示；如果没有这行，列表可能缺少主标题。
    expect(markup).toContain("已连接"); // 新增代码+ProviderSettingsPanelTest：确认连接状态显示；如果没有这行，用户不知道当前 provider 是否已连接。
    expect(markup).toContain("断开"); // 新增代码+ProviderSettingsPanelTest：确认已连接 provider 显示断开；如果没有这行，断开入口可能缺失。
    expect(markup).toContain("+ 连接"); // 新增代码+ProviderSettingsPanelTest：确认可连接 provider 显示连接；如果没有这行，新 provider 无法引导连接。
    expect(markup).toContain("暂未支持"); // 新增代码+ProviderSettingsPanelTest：确认 unsupported provider 显示禁用文案；如果没有这行，用户会被误导。
    expect(markup).toContain("连接测试通过"); // 新增代码+ProviderSettingsPanelTest：确认探针成功文案安全显示；如果没有这行，测试连接反馈不明确。
    expect(markup).not.toContain("unit-test-secret-value"); // 新增代码+ProviderSettingsPanelTest：确认 UI 不显示测试密钥；如果没有这行，截图可能泄露 secret。
  }); // 新增代码+ProviderSettingsPanelTest：列表文案测试结束；如果没有这行，测试块语法不完整。

  it("calls row callbacks without treating the custom CTA as a provider", () => { // 新增代码+ProviderSettingsPanelTest：测试段开始，验证按钮回调；如果没有这段，虚拟 CTA 可能误调 provider mutation。
    const onConnectProvider = vi.fn(); // 新增代码+ProviderSettingsPanelTest：创建连接回调；如果没有这行，连接按钮行为无法验证。
    const onOpenCustomProvider = vi.fn(); // 新增代码+ProviderSettingsPanelTest：创建自定义入口回调；如果没有这行，CTA 行行为无法验证。
    const panel = SettingsProvidersPanel({ viewModel, loading: false, errorMessage: "", busyProviderId: "", probeResults: {}, onRetry: vi.fn(), onConnectProvider, onDisconnectProvider: vi.fn(), onTestProvider: vi.fn(), onOpenCustomProvider }); // 新增代码+ProviderSettingsPanelTest：直接构建面板元素树；如果没有这行，无法调用按钮 props。
    findByTestId(panel, "provider-action-openrouter")?.props.onClick(); // 新增代码+ProviderSettingsPanelTest：触发 OpenRouter 连接按钮；如果没有这行，连接回调不会被验证。
    findByTestId(panel, "provider-custom-cta")?.props.onClick(); // 新增代码+ProviderSettingsPanelTest：触发自定义 provider CTA；如果没有这行，虚拟入口行为不会被验证。
    expect(onConnectProvider).toHaveBeenCalledWith(providerRows[2]); // 新增代码+ProviderSettingsPanelTest：确认真实 provider 行传给连接回调；如果没有这行，按钮可能传错对象。
    expect(onOpenCustomProvider).toHaveBeenCalledTimes(1); // 新增代码+ProviderSettingsPanelTest：确认自定义入口只打开自定义对话；如果没有这行，CTA 可能误走 mutation。
  }); // 新增代码+ProviderSettingsPanelTest：按钮回调测试结束；如果没有这行，测试块语法不完整。

  it("keeps API key entry password-only and disables empty submit", () => { // 新增代码+ProviderSettingsPanelTest：测试段开始，验证连接弹窗 API key 安全输入；如果没有这段，密钥输入可能明文或空提交。
    const markup = renderToStaticMarkup(<ProviderConnectDialog open={true} provider={providerRows[2]} apiKey="" pending={false} errorMessage="" onApiKeyChange={vi.fn()} onClose={vi.fn()} onSubmit={vi.fn()} />); // 新增代码+ProviderSettingsPanelTest：渲染空 API key 连接弹窗；如果没有这行，后续断言没有输入。
    expect(markup).toContain("OpenRouter"); // 新增代码+ProviderSettingsPanelTest：确认标题使用 provider 名称；如果没有这行，用户不知道正在连接谁。
    expect(markup).toContain("data-active-auth-method=\"api-key\""); // 新增代码+OpenAIConnectApiKeyTest：确认 API key 表单携带真实方法 id；如果没有这行，父组件可能继续硬编码旧 auth 方法。
    expect(markup).toContain("type=\"password\""); // 新增代码+ProviderSettingsPanelTest：确认 API key 使用密码输入；如果没有这行，密钥会在屏幕上明文显示。
    expect(markup).toContain("disabled=\"\""); // 新增代码+ProviderSettingsPanelTest：确认空 key 禁用提交；如果没有这行，空密钥会打到后端。
  }); // 新增代码+ProviderSettingsPanelTest：连接弹窗测试结束；如果没有这行，测试块语法不完整。

  it("renders OpenAI method picker before showing the API key field", () => { // 新增代码+OpenAIConnectPanelTest：测试段开始，验证 OpenCode 风格方法选择初始态；如果没有这段，OpenAI 会继续直接弹 API key 表单。
    const markup = renderToStaticMarkup(<ProviderConnectDialog open={true} provider={openAiPickerProvider} apiKey="" pending={false} errorMessage="" onApiKeyChange={vi.fn()} onClose={vi.fn()} onSubmit={vi.fn()} />); // 新增代码+OpenAIConnectPanelTest：渲染 OpenAI 三方法连接弹窗；如果没有这行，后续断言没有输入。
    expect(markup).toContain("选择 OpenAI 的登录方式"); // 新增代码+OpenAIConnectPanelTest：确认弹窗显示方法选择标题；如果没有这行，用户不知道当前是在选登录方式。
    expect(markup).toContain("ChatGPT Pro/Plus (browser)"); // 新增代码+OpenAIConnectPanelTest：确认 browser 方法可见；如果没有这行，OpenCode 同款浏览器入口缺失。
    expect(markup).toContain("ChatGPT Pro/Plus (headless)"); // 新增代码+OpenAIConnectPanelTest：确认 headless 方法可见；如果没有这行，设备码入口缺失。
    expect(markup).toContain("API 密钥"); // 新增代码+OpenAIConnectPanelTest：确认 API key 方法仍可见；如果没有这行，稳定真实连接路径缺失。
    expect(markup).not.toContain("type=\"password\""); // 新增代码+OpenAIConnectPanelTest：确认初始态不直接显示密码框；如果没有这行，方法选择器会被旧 API key 表单绕过。
  }); // 新增代码+OpenAIConnectPanelTest：方法选择初始态测试结束；如果没有这行，测试块语法不完整。

  it("renders OpenAI auth-attempt waiting state without token fields", () => { // 新增代码+OpenAIConnectPanelTest：测试段开始，验证 browser/headless 等待授权页；如果没有这段，OAuth 方法可能只停在静态方法按钮。
    const markup = renderToStaticMarkup(<ProviderConnectDialog open={true} provider={openAiHeadlessOnlyProvider} apiKey="" pending={false} errorMessage="" authAttempt={pendingOpenAiAuthAttempt} onApiKeyChange={vi.fn()} onClose={vi.fn()} onSubmit={vi.fn()} onStartAuthAttempt={vi.fn()} onCancelAuthAttempt={vi.fn()} />); // 新增代码+OpenAIConnectPanelTest：渲染带 pending attempt 的连接弹窗；如果没有这行，后续断言没有等待页输入。
    expect(markup).toContain("访问此链接"); // 新增代码+OpenAIConnectPanelTest：确认等待页显示访问链接提示；如果没有这行，用户不知道去哪里完成授权。
    expect(markup).toContain("MOCK-OPENAI-123456"); // 新增代码+OpenAIConnectPanelTest：确认等待页显示设备码；如果没有这行，headless flow 无法手动输入确认码。
    expect(markup).toContain("等待授权"); // 新增代码+OpenAIConnectPanelTest：确认等待页显示轮询状态；如果没有这行，用户不知道当前仍在等待。
    expect(markup).not.toContain("refresh_token"); // 新增代码+OpenAIConnectPanelTest：确认等待页不渲染 refresh token 字段；如果没有这行，截图验收可能漏掉敏感泄露。
    expect(markup).not.toContain("access_token"); // 新增代码+OpenAIConnectPanelTest：确认等待页不渲染 access token 字段；如果没有这行，短期凭据可能进入 GUI。
    expect(markup).not.toContain("secret_ref"); // 新增代码+OpenAIConnectPanelTest：确认等待页不渲染 secret_ref 字段；如果没有这行，renderer 可能暴露后端密钥定位信息。
  }); // 新增代码+OpenAIConnectPanelTest：等待授权页测试结束；如果没有这行，测试块语法不完整。

  it("maps probe status codes to user-facing safe text", () => { // 新增代码+ProviderSettingsPanelTest：测试段开始，验证探针状态文案；如果没有这段，错误状态可能显示底层细节。
    expect(probeStatusLabel("auth_failed")).toBe("认证失败"); // 新增代码+ProviderSettingsPanelTest：确认认证失败文案；如果没有这行，auth 错误可能难懂。
    expect(probeStatusLabel("missing_secret")).toBe("缺少密钥"); // 新增代码+ProviderSettingsPanelTest：确认缺密钥文案；如果没有这行，用户不知道应补凭据。
    expect(probeStatusLabel("network_failed")).toBe("网络不可达"); // 新增代码+ProviderSettingsPanelTest：确认网络失败文案；如果没有这行，连接错误可能暴露底层异常。
    expect(probeStatusLabel("unsupported")).toBe("暂不支持测试"); // 新增代码+ProviderSettingsPanelTest：确认暂不支持文案；如果没有这行，unsupported 状态会不清楚。
    expect(probeStatusLabel("invalid_config")).toBe("配置无效"); // 新增代码+ProviderSettingsPanelTest：确认配置无效文案；如果没有这行，配置错误没有可读解释。
  }); // 新增代码+ProviderSettingsPanelTest：探针状态文案测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsPanelTest：测试段结束；如果没有这行，describe 语法不完整。
