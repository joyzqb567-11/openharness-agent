import type { GuiCustomProviderCta, GuiModelInfo, GuiProviderAuthMethod, GuiProviderInfo, GuiProviderSettingsPayload } from "../api/guiProviderTypes"; // 新增代码+ProviderSettingsStore：导入后端 provider 类型；如果没有这行，store 只能消费不透明对象。

export type ProviderAuthMethodView = { id: string; label: string; enabled: boolean; status: string; methodType: string; mode: string; fields: string[]; helpText: string; experimental: boolean }; // 修改代码+OpenAIConnectStore：定义前端认证方式 view model 并保留 methodType/mode/experimental；如果没有这行，方法选择器无法决定渲染 API key 还是 OAuth。

export type ProviderModelView = { id: string; displayName: string; providerId: string; visible: boolean; supportsTools: boolean; supportsVision: boolean; state: string; source: string; message: string }; // 修改代码+ComposerRouteControls：定义前端模型 view model 并保留探针状态；如果没有这行，Models 页和底部下拉无法解释模型是否可用。

export type ProviderRowView = { id: string; displayName: string; kind: string; source: string; connected: boolean; maskedKey: string; accountLabel: string; directRouteStatus: string; oauthClientSource: string; description: string; authMethods: ProviderAuthMethodView[]; models: ProviderModelView[]; primaryActionLabel: string; primaryActionDisabled: boolean }; // 修改代码+ComposerRouteControls：定义 provider 行 view model 并保留账号摘要和路由状态；如果没有这行，Provider 页无法显示 Direct SSE 事实。

export type ModelGroupView = { providerId: string; providerName: string; connected: boolean; models: ProviderModelView[] }; // 新增代码+ProviderSettingsStore：定义模型分组 view model；如果没有这行，Models 页每次渲染都要重新分组。

export type ProviderSettingsViewModel = { defaultTab: "providers"; schemaVersion: number; secretStoreWarning: string; providers: ProviderRowView[]; customProviderCta: { id: string; displayName: string; description: string }; defaultProviderId: string; defaultModelId: string }; // 新增代码+ProviderSettingsStore：定义设置弹窗消费的总 view model；如果没有这行，SettingsDialog 会直接依赖后端 payload。

const POPULAR_PROVIDER_ORDER = ["openai", "github-copilot", "google", "openrouter", "vercel"]; // 新增代码+ProviderSettingsStore：定义内置 provider 稳定排序；如果没有这行，列表顺序会随后端数组抖动。

const UNSAFE_KEYS = new Set(["api_key", "apikey", "authorization", "bearer", "secret_ref", "access_token", "refresh_token", "id_token"]); // 修改代码+OpenAIConnectStore：定义 renderer 禁止保留的字段名并加入 OAuth token/secret 引用；如果没有这行，后端 bug 可能把 token 带进状态。

function isRecord(value: unknown): value is Record<string, unknown> { // 新增代码+ProviderSettingsStore：函数段开始，判断未知值是否是普通对象；如果没有这段，递归脱敏会访问非对象字段。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 新增代码+ProviderSettingsStore：只接受非数组对象；如果没有这行，数组会被误当对象处理。
} // 新增代码+ProviderSettingsStore：函数段结束，isRecord 到此结束；如果没有这行，函数语法不完整。

export function isUnsafeProviderPayloadKey(key: string): boolean { // 新增代码+ProviderSettingsStore：函数段开始，判断字段名是否危险；如果没有这段，测试和脱敏逻辑无法共享规则。
  return UNSAFE_KEYS.has(key.toLowerCase()); // 修改代码+OpenAIConnectStore：按小写字段名判断危险键；如果没有这行，Authorization/apiKey 这类大小写变体可能绕过脱敏。
} // 新增代码+ProviderSettingsStore：函数段结束，isUnsafeProviderPayloadKey 到此结束；如果没有这行，函数语法不完整。

export function redactedProviderPayload<T>(payload: T): T { // 新增代码+ProviderSettingsStore：函数段开始，递归移除危险字段；如果没有这段，renderer state 可能保留 raw secret。
  if (Array.isArray(payload)) { // 新增代码+ProviderSettingsStore：处理数组；如果没有这行，列表中的危险字段不会被递归清理。
    return payload.map((item) => redactedProviderPayload(item)) as T; // 新增代码+ProviderSettingsStore：递归清理数组元素；如果没有这行，provider 列表内的泄露会漏过。
  } // 新增代码+ProviderSettingsStore：数组分支结束；如果没有这行，条件块语法不完整。
  if (isRecord(payload)) { // 新增代码+ProviderSettingsStore：处理普通对象；如果没有这行，对象字段不会被检查。
    const safeEntries = Object.entries(payload).filter(([key]) => !isUnsafeProviderPayloadKey(key)); // 新增代码+ProviderSettingsStore：过滤危险字段；如果没有这行，api_key 等字段会进入结果。
    return Object.fromEntries(safeEntries.map(([key, value]) => [key, redactedProviderPayload(value)])) as T; // 新增代码+ProviderSettingsStore：递归清理剩余字段；如果没有这行，嵌套泄露可能漏过。
  } // 新增代码+ProviderSettingsStore：对象分支结束；如果没有这行，条件块语法不完整。
  return payload; // 新增代码+ProviderSettingsStore：普通值原样返回；如果没有这行，字符串/布尔值会丢失。
} // 新增代码+ProviderSettingsStore：函数段结束，redactedProviderPayload 到此结束；如果没有这行，函数语法不完整。

function authMethodView(method: GuiProviderAuthMethod): ProviderAuthMethodView { // 新增代码+ProviderSettingsStore：函数段开始，把后端认证方式转成前端字段；如果没有这段，组件要理解 snake_case。
  return { id: method.id, label: method.label, enabled: Boolean(method.enabled), status: String(method.status), methodType: String(method.type ?? ""), mode: String(method.mode ?? ""), fields: Array.isArray(method.fields) ? method.fields : [], helpText: String(method.help_text ?? ""), experimental: Boolean(method.experimental) }; // 修改代码+OpenAIConnectStore：返回认证方式 view model 并保留方法类型、交互模式和实验标记；如果没有这行，连接向导无法选择正确步骤。
} // 新增代码+ProviderSettingsStore：函数段结束，authMethodView 到此结束；如果没有这行，函数语法不完整。

function modelView(model: GuiModelInfo): ProviderModelView { // 新增代码+ProviderSettingsStore：函数段开始，把后端模型转成前端字段；如果没有这段，Models 页要理解 snake_case。
  return { id: model.id, displayName: model.display_name, providerId: model.provider_id, visible: Boolean(model.visible), supportsTools: Boolean(model.supports_tools), supportsVision: Boolean(model.supports_vision), state: String(model.state ?? "unknown"), source: String(model.source ?? ""), message: String(model.message ?? "") }; // 修改代码+ComposerRouteControls：返回模型 view model 并带探针状态；如果没有这行，模型字段名和可用状态无法统一。
} // 新增代码+ProviderSettingsStore：函数段结束，modelView 到此结束；如果没有这行，函数语法不完整。

function primaryActionLabel(provider: GuiProviderInfo, authMethods: ProviderAuthMethodView[]): string { // 新增代码+ProviderSettingsStore：函数段开始，计算 provider 主按钮文案；如果没有这段，按钮状态会散落在组件里。
  if (provider.connected) { // 新增代码+ProviderSettingsStore：处理已连接 provider；如果没有这行，已连接状态可能仍显示连接。
    return "断开"; // 新增代码+ProviderSettingsStore：已连接时显示断开；如果没有这行，用户无法断开连接。
  } // 新增代码+ProviderSettingsStore：已连接分支结束；如果没有这行，条件块语法不完整。
  return authMethods.some((method) => method.enabled) ? "+ 连接" : "暂未支持"; // 新增代码+ProviderSettingsStore：按认证方式决定连接或暂未支持；如果没有这行，Copilot 会被误导连接。
} // 新增代码+ProviderSettingsStore：函数段结束，primaryActionLabel 到此结束；如果没有这行，函数语法不完整。

function providerRowView(provider: GuiProviderInfo): ProviderRowView { // 新增代码+ProviderSettingsStore：函数段开始，把后端 provider 转成前端行；如果没有这段，Provider 页组件会重复转换。
  const authMethods = Array.isArray(provider.auth_methods) ? provider.auth_methods.map(authMethodView) : []; // 新增代码+ProviderSettingsStore：转换认证方式数组；如果没有这行，缺失 auth_methods 会让组件崩溃。
  const models = Array.isArray(provider.models) ? provider.models.map(modelView) : []; // 新增代码+ProviderSettingsStore：转换模型数组并容忍缺失；如果没有这行，缺 models 的 provider 会崩溃。
  const label = primaryActionLabel(provider, authMethods); // 新增代码+ProviderSettingsStore：计算按钮文案；如果没有这行，禁用状态无法统一。
  return { id: provider.id, displayName: provider.display_name, kind: provider.kind, source: provider.source, connected: Boolean(provider.connected), maskedKey: provider.masked_key, accountLabel: String(provider.account_label ?? ""), directRouteStatus: String(provider.direct_route_status ?? ""), oauthClientSource: String(provider.oauth_client_source ?? ""), description: provider.description, authMethods, models, primaryActionLabel: label, primaryActionDisabled: label === "暂未支持" }; // 修改代码+ComposerRouteControls：返回 provider 行 view model 并带账号摘要和路由状态；如果没有这行，设置页拿不到 Direct SSE 事实。
} // 新增代码+ProviderSettingsStore：函数段结束，providerRowView 到此结束；如果没有这行，函数语法不完整。

function ctaView(cta: GuiCustomProviderCta): { id: string; displayName: string; description: string } { // 新增代码+ProviderSettingsStore：函数段开始，转换虚拟 CTA；如果没有这段，组件要理解 snake_case。
  return { id: cta.id, displayName: cta.display_name, description: cta.description }; // 新增代码+ProviderSettingsStore：返回 camelCase CTA；如果没有这行，自定义 provider 入口字段会对不上。
} // 新增代码+ProviderSettingsStore：函数段结束，ctaView 到此结束；如果没有这行，函数语法不完整。

export function buildProviderSettingsViewModel(payload: GuiProviderSettingsPayload): ProviderSettingsViewModel { // 新增代码+ProviderSettingsStore：函数段开始，构建设置弹窗 view model；如果没有这段，SettingsDialog 会直接消费后端 JSON。
  const safePayload = redactedProviderPayload(payload); // 新增代码+ProviderSettingsStore：先清理危险字段；如果没有这行，后端 bug 可能把 secret 留在 renderer state。
  const providers = (Array.isArray(safePayload.providers) ? safePayload.providers : []).map(providerRowView); // 新增代码+ProviderSettingsStore：转换 provider rows；如果没有这行，Provider 页没有可渲染数据。
  return { defaultTab: "providers", schemaVersion: safePayload.schema_version, secretStoreWarning: safePayload.secret_store?.kind === "dev_json" ? String(safePayload.secret_store.warning || "") : "", providers, customProviderCta: ctaView(safePayload.custom_provider_cta), defaultProviderId: safePayload.default_provider_id || "", defaultModelId: safePayload.default_model_id || "" }; // 新增代码+ProviderSettingsStore：返回总 view model；如果没有这行，设置弹窗缺少默认页、warning、provider 和 CTA。
} // 新增代码+ProviderSettingsStore：函数段结束，buildProviderSettingsViewModel 到此结束；如果没有这行，函数语法不完整。

export function providerRowsForDisplay(viewModel: ProviderSettingsViewModel): ProviderRowView[] { // 新增代码+ProviderSettingsStore：函数段开始，排序 provider 行；如果没有这段，Provider 列表顺序会不稳定。
  return [...viewModel.providers].sort((left, right) => { // 新增代码+ProviderSettingsStore：复制后排序避免污染 state；如果没有这行，调用排序会修改原数组。
    if (left.connected !== right.connected) { // 新增代码+ProviderSettingsStore：优先比较连接状态；如果没有这行，已连接 provider 不会靠前。
      return left.connected ? -1 : 1; // 新增代码+ProviderSettingsStore：已连接排前；如果没有这行，用户难以快速看到当前连接。
    } // 新增代码+ProviderSettingsStore：连接状态分支结束；如果没有这行，条件块语法不完整。
    const leftOrder = POPULAR_PROVIDER_ORDER.indexOf(left.id); // 新增代码+ProviderSettingsStore：读取左侧 provider 内置顺序；如果没有这行，popular 排序无法计算。
    const rightOrder = POPULAR_PROVIDER_ORDER.indexOf(right.id); // 新增代码+ProviderSettingsStore：读取右侧 provider 内置顺序；如果没有这行，popular 排序无法计算。
    return (leftOrder === -1 ? 99 : leftOrder) - (rightOrder === -1 ? 99 : rightOrder); // 新增代码+ProviderSettingsStore：按内置顺序排序，自定义靠后；如果没有这行，列表会按后端返回抖动。
  }); // 新增代码+ProviderSettingsStore：排序结束；如果没有这行，sort 回调语法不完整。
} // 新增代码+ProviderSettingsStore：函数段结束，providerRowsForDisplay 到此结束；如果没有这行，函数语法不完整。

export function modelGroupsForDisplay(viewModel: ProviderSettingsViewModel): ModelGroupView[] { // 新增代码+ProviderSettingsStore：函数段开始，构建模型分组；如果没有这段，Models 页要重复遍历 provider。
  return providerRowsForDisplay(viewModel).filter((provider) => provider.models.length > 0).map((provider) => ({ providerId: provider.id, providerName: provider.displayName, connected: provider.connected, models: provider.models })); // 新增代码+ProviderSettingsStore：返回有模型的 provider 分组；如果没有这行，模型页会显示空 provider 或丢排序。
} // 新增代码+ProviderSettingsStore：函数段结束，modelGroupsForDisplay 到此结束；如果没有这行，函数语法不完整。
