export type GuiProviderAuthMethodStatus = "available" | "mock_available" | "unsupported_v1" | string; // 修改代码+OpenAIConnectTypes：定义认证方式状态类型并加入 mock_available；如果没有这行，前端无法区分稳定 API key、mock OAuth 和 V1 未支持。

export type GuiProviderAuthMethodType = "api" | "oauth" | string; // 新增代码+OpenAIConnectTypes：定义认证方式大类；如果没有这行，前端无法决定渲染 API key 表单还是 OAuth 等待页。

export type GuiProviderAuthMethodMode = "form" | "auto" | string; // 新增代码+OpenAIConnectTypes：定义认证方式交互模式；如果没有这行，前端无法区分手动表单和自动 auth-attempt 轮询。

export type GuiProviderSource = "none" | "config" | "env" | "custom" | string; // 新增代码+ProviderSettingsTypes：定义 provider 来源类型；如果没有这行，来源 badge 会使用不透明字符串。

export type GuiProviderKind = "built_in" | "custom" | string; // 新增代码+ProviderSettingsTypes：定义 provider 类型；如果没有这行，内置和自定义 provider 无法稳定区分。

export type GuiSecretStoreInfo = { // 新增代码+ProviderSettingsTypes：类型段开始，描述后端密钥存储摘要；如果没有这段，UI 无法显示 dev_json 风险提示。
  kind: string; // 新增代码+ProviderSettingsTypes：保存存储类型；如果没有这行，前端不知道是否为开发存储。
  label: string; // 新增代码+ProviderSettingsTypes：保存存储显示名；如果没有这行，设置页只能显示机器码。
  warning: string; // 新增代码+ProviderSettingsTypes：保存风险提示；如果没有这行，用户不知道 dev_json 不是生产级凭据。
}; // 新增代码+ProviderSettingsTypes：GuiSecretStoreInfo 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiProviderAuthMethod = { // 新增代码+ProviderSettingsTypes：类型段开始，描述 provider 认证方式；如果没有这段，连接弹窗无法判断字段和状态。
  id: string; // 新增代码+ProviderSettingsTypes：认证方式 id；如果没有这行，提交时无法告诉后端使用哪种认证。
  label: string; // 新增代码+ProviderSettingsTypes：认证方式显示名；如果没有这行，UI 只能显示机器码。
  enabled: boolean; // 新增代码+ProviderSettingsTypes：认证方式是否启用；如果没有这行，Copilot 会误显示可连接。
  status: GuiProviderAuthMethodStatus; // 新增代码+ProviderSettingsTypes：认证方式状态；如果没有这行，UI 无法显示 unsupported_v1。
  type: GuiProviderAuthMethodType; // 新增代码+OpenAIConnectTypes：认证方式大类；如果没有这行，方法选择器无法判断点击后走 API key 还是 OAuth。
  mode: GuiProviderAuthMethodMode; // 新增代码+OpenAIConnectTypes：认证方式交互模式；如果没有这行，方法选择器无法判断是否启动 auth-attempt。
  fields: string[]; // 新增代码+ProviderSettingsTypes：认证字段代号；如果没有这行，表单不知道收集哪些字段。
  help_text?: string; // 新增代码+ProviderSettingsTypes：后端 snake_case 帮助文案；如果没有这行，raw payload 类型不完整。
  experimental?: boolean; // 新增代码+OpenAIConnectTypes：认证方式是否为实验路径；如果没有这行，mock OAuth 会被误显示成稳定真实能力。
}; // 新增代码+ProviderSettingsTypes：GuiProviderAuthMethod 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiModelInfo = { // 新增代码+ProviderSettingsTypes：类型段开始，描述后端模型信息；如果没有这段，模型页无法类型化 provider 分组。
  id: string; // 新增代码+ProviderSettingsTypes：模型 id；如果没有这行，开关保存无法定位模型。
  display_name: string; // 新增代码+ProviderSettingsTypes：后端 snake_case 模型名；如果没有这行，UI 没有可读模型名。
  provider_id: string; // 新增代码+ProviderSettingsTypes：所属 provider id；如果没有这行，模型无法分组。
  visible: boolean; // 新增代码+ProviderSettingsTypes：模型是否可见；如果没有这行，开关状态无法显示。
  supports_tools?: boolean; // 新增代码+ProviderSettingsTypes：工具能力标记；如果没有这行，后续模型能力 UI 无法扩展。
  supports_vision?: boolean; // 新增代码+ProviderSettingsTypes：视觉能力标记；如果没有这行，后续模型能力 UI 无法扩展。
}; // 新增代码+ProviderSettingsTypes：GuiModelInfo 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiProviderInfo = { // 新增代码+ProviderSettingsTypes：类型段开始，描述后端 provider 行；如果没有这段，Provider 设置页只能消费不透明对象。
  id: string; // 新增代码+ProviderSettingsTypes：provider 稳定 id；如果没有这行，mutation 无法定位目标。
  display_name: string; // 新增代码+ProviderSettingsTypes：后端 snake_case 显示名；如果没有这行，列表没有标题。
  kind: GuiProviderKind; // 新增代码+ProviderSettingsTypes：provider 类型；如果没有这行，UI 无法区分内置和自定义。
  source: GuiProviderSource; // 新增代码+ProviderSettingsTypes：provider 来源；如果没有这行，source badge 无法显示。
  connected: boolean; // 新增代码+ProviderSettingsTypes：连接状态；如果没有这行，按钮无法显示连接/断开。
  masked_key: string; // 新增代码+ProviderSettingsTypes：脱敏密钥摘要；如果没有这行，用户无法确认已连接 key。
  auth_methods: GuiProviderAuthMethod[]; // 新增代码+ProviderSettingsTypes：认证方式列表；如果没有这行，连接弹窗无法生成。
  description: string; // 新增代码+ProviderSettingsTypes：中文说明；如果没有这行，provider 行缺少解释。
  models?: GuiModelInfo[]; // 新增代码+ProviderSettingsTypes：模型列表；如果没有这行，Models 页没有输入。
}; // 新增代码+ProviderSettingsTypes：GuiProviderInfo 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiCustomProviderCta = { // 新增代码+ProviderSettingsTypes：类型段开始，描述虚拟自定义 provider 入口；如果没有这段，前端可能把 CTA 当 provider id。
  id: "custom-provider-cta" | string; // 新增代码+ProviderSettingsTypes：CTA id；如果没有这行，点击事件无法识别虚拟行。
  display_name: string; // 新增代码+ProviderSettingsTypes：CTA 显示名；如果没有这行，入口没有标题。
  description: string; // 新增代码+ProviderSettingsTypes：CTA 说明；如果没有这行，用户不知道入口用途。
}; // 新增代码+ProviderSettingsTypes：GuiCustomProviderCta 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type GuiProviderSettingsPayload = { // 新增代码+ProviderSettingsTypes：类型段开始，描述 Provider Settings GET 响应；如果没有这段，client 和 store 无法共享合同。
  ok: true; // 新增代码+ProviderSettingsTypes：标记成功响应；如果没有这行，调用方无法区分错误 payload。
  schema_version: number; // 新增代码+ProviderSettingsTypes：schema 版本；如果没有这行，后续升级无法兼容判断。
  secret_store: GuiSecretStoreInfo; // 新增代码+ProviderSettingsTypes：密钥存储摘要；如果没有这行，UI 无法显示 dev warning。
  providers: GuiProviderInfo[]; // 新增代码+ProviderSettingsTypes：真实 provider 列表；如果没有这行，Provider 页没有数据。
  custom_provider_cta: GuiCustomProviderCta; // 新增代码+ProviderSettingsTypes：虚拟自定义入口；如果没有这行，添加 provider 入口缺失。
  default_provider_id: string; // 新增代码+ProviderSettingsTypes：默认 provider id；如果没有这行，后续默认模型选择无法扩展。
  default_model_id: string; // 新增代码+ProviderSettingsTypes：默认 model id；如果没有这行，后续默认模型选择无法扩展。
}; // 新增代码+ProviderSettingsTypes：GuiProviderSettingsPayload 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type CustomProviderRequest = { // 新增代码+ProviderSettingsTypes：类型段开始，描述前端保存自定义 provider 请求；如果没有这段，client.saveCustomProvider 会接收不透明对象。
  providerId: string; // 新增代码+ProviderSettingsTypes：自定义 provider id；如果没有这行，后端无法保存 provider。
  displayName: string; // 新增代码+ProviderSettingsTypes：自定义 provider 显示名；如果没有这行，UI 会显示空标题。
  baseUrl: string; // 新增代码+ProviderSettingsTypes：OpenAI-compatible base URL；如果没有这行，连接探针没有目标。
  authMethodId: string; // 新增代码+ProviderSettingsTypes：认证方式 id；如果没有这行，后端无法判断字段语义。
  fields: Record<string, string>; // 新增代码+ProviderSettingsTypes：提交的 write-only 表单字段；如果没有这行，API key 无法传给后端。
  headers: Array<{ key: string; value: string }>; // 新增代码+ProviderSettingsTypes：自定义 header 行；如果没有这行，gateway 场景无法扩展。
  models: Array<{ id: string; displayName: string; visible?: boolean }>; // 新增代码+ProviderSettingsTypes：自定义模型行；如果没有这行，Models 页不会显示自定义 provider 模型。
}; // 新增代码+ProviderSettingsTypes：CustomProviderRequest 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type ProviderConnectionProbePayload = { // 新增代码+ProviderSettingsTypes：类型段开始，描述连接测试响应；如果没有这段，测试连接 UI 只能消费不透明对象。
  ok: boolean; // 新增代码+ProviderSettingsTypes：连接是否成功；如果没有这行，UI 无法显示通过/失败。
  schema_version: number; // 新增代码+ProviderSettingsTypes：schema 版本；如果没有这行，后续协议升级无法判断。
  provider_id: string; // 新增代码+ProviderSettingsTypes：被测试 provider；如果没有这行，异步结果无法对齐行。
  status: "ok" | "auth_failed" | "missing_secret" | "network_failed" | "unsupported" | "invalid_config" | string; // 新增代码+ProviderSettingsTypes：探针状态码；如果没有这行，UI 无法显示准确文案。
  message: string; // 新增代码+ProviderSettingsTypes：可读结果；如果没有这行，用户只能看到机器码。
  models_count: number; // 新增代码+ProviderSettingsTypes：探测到的模型数量；如果没有这行，成功结果缺少有用信息。
}; // 新增代码+ProviderSettingsTypes：ProviderConnectionProbePayload 类型结束；如果没有这行，TypeScript 类型语法不完整。
