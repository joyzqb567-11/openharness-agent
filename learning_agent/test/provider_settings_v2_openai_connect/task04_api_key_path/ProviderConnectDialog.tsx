import { type FormEvent, useEffect, useMemo, useState } from "react"; // 修改代码+OpenAIConnectDialog：导入表单事件和 React 状态工具；如果没有这行，方法选择器无法记住用户选中的登录方式。
import type { ProviderAuthMethodView, ProviderRowView } from "../../state/providerSettingsStore"; // 修改代码+OpenAIConnectDialog：导入 provider 与认证方式 view 类型；如果没有这行，连接弹窗不知道要展示和提交哪个方法。

type ProviderConnectDialogProps = { // 修改代码+OpenAIConnectDialog：类型段开始，定义连接弹窗输入；如果没有这段，父组件无法受控管理连接向导。
  open: boolean; // 新增代码+ProviderConnectDialog：保存弹窗是否打开；如果没有这行，关闭状态无法移除 DOM。
  provider: ProviderRowView | null; // 新增代码+ProviderConnectDialog：保存当前 provider；如果没有这行，弹窗无法显示标题或提交 provider id。
  apiKey: string; // 新增代码+ProviderConnectDialog：保存受控 API key 输入；如果没有这行，本地密钥状态无法由父组件成功后清空。
  pending: boolean; // 新增代码+ProviderConnectDialog：保存提交等待态；如果没有这行，用户可能重复点击连接。
  errorMessage: string; // 新增代码+ProviderConnectDialog：保存安全错误文案；如果没有这行，后端失败只能留在控制台。
  onApiKeyChange: (value: string) => void; // 新增代码+ProviderConnectDialog：保存输入变化回调；如果没有这行，API key 输入框无法受控。
  onClose: () => void; // 新增代码+ProviderConnectDialog：保存关闭回调；如果没有这行，用户无法取消连接。
  onSubmit: (authMethodId: string) => void; // 修改代码+OpenAIConnectApiKey：保存带认证方式 id 的提交回调；如果没有这行，父组件只能继续硬编码旧 API key 方法。
}; // 修改代码+OpenAIConnectDialog：ProviderConnectDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

function enabledAuthMethods(provider: ProviderRowView | null): ProviderAuthMethodView[] { // 新增代码+OpenAIConnectDialog：函数段开始，筛出可用认证方式；如果没有这段，方法选择器会展示未支持方法。
  return provider?.authMethods.filter((method) => method.enabled) ?? []; // 新增代码+OpenAIConnectDialog：只返回 enabled 方法；如果没有这行，Copilot 未支持入口可能被点击。
} // 新增代码+OpenAIConnectDialog：函数段结束，enabledAuthMethods 到此结束；如果没有这行，函数语法不完整。

function isApiKeyFormMethod(method: ProviderAuthMethodView | null): boolean { // 新增代码+OpenAIConnectDialog：函数段开始，判断是否为 API key 表单方法；如果没有这段，OAuth 方法可能误显示密码框。
  return method?.methodType === "api" && method.mode === "form"; // 新增代码+OpenAIConnectDialog：只有 api+form 才显示密钥表单；如果没有这行，自动授权和手动表单会混淆。
} // 新增代码+OpenAIConnectDialog：函数段结束，isApiKeyFormMethod 到此结束；如果没有这行，函数语法不完整。

function defaultSelectedMethod(methods: ProviderAuthMethodView[]): ProviderAuthMethodView | null { // 新增代码+OpenAIConnectDialog：函数段开始，决定默认选中的认证方式；如果没有这段，单一 API key provider 也会多一步选择。
  return methods.length === 1 ? methods[0] : null; // 新增代码+OpenAIConnectDialog：单方法 provider 直接进入对应步骤；如果没有这行，OpenRouter 这类 provider 会退化出多余点击。
} // 新增代码+OpenAIConnectDialog：函数段结束，defaultSelectedMethod 到此结束；如果没有这行，函数语法不完整。

function selectedAuthMethod(methods: ProviderAuthMethodView[], selectedMethodId: string): ProviderAuthMethodView | null { // 新增代码+OpenAIConnectDialog：函数段开始，解析当前选中方法；如果没有这段，状态里的 method id 无法变成完整方法对象。
  return methods.find((method) => method.id === selectedMethodId) ?? defaultSelectedMethod(methods); // 新增代码+OpenAIConnectDialog：优先使用用户选择，否则单方法自动选择；如果没有这行，表单和方法列表无法稳定切换。
} // 新增代码+OpenAIConnectDialog：函数段结束，selectedAuthMethod 到此结束；如果没有这行，函数语法不完整。

function canSubmitApiKey(method: ProviderAuthMethodView | null, apiKey: string, pending: boolean): boolean { // 修改代码+OpenAIConnectDialog：函数段开始，判断能否提交 API key；如果没有这段，禁用逻辑会散落在 JSX 中。
  return isApiKeyFormMethod(method) && apiKey.trim().length > 0 && !pending; // 修改代码+OpenAIConnectDialog：只有 API key 表单、非空且非等待时允许提交；如果没有这行，空 key 或 OAuth 方法可能打到后端。
} // 修改代码+OpenAIConnectDialog：函数段结束，canSubmitApiKey 到此结束；如果没有这行，函数语法不完整。

function authMethodTestId(method: ProviderAuthMethodView): string { // 新增代码+OpenAIConnectDialog：函数段开始，生成方法按钮测试 id；如果没有这段，自动化测试很难稳定点击具体登录方式。
  return `provider-auth-method-${method.id}`; // 新增代码+OpenAIConnectDialog：把 method id 拼成稳定测试 id；如果没有这行，测试只能依赖脆弱文本顺序。
} // 新增代码+OpenAIConnectDialog：函数段结束，authMethodTestId 到此结束；如果没有这行，函数语法不完整。

export function ProviderConnectDialog({ open, provider, apiKey, pending, errorMessage, onApiKeyChange, onClose, onSubmit }: ProviderConnectDialogProps): JSX.Element | null { // 修改代码+OpenAIConnectDialog：函数段开始，渲染 Provider 连接向导；如果没有这段，连接按钮无法收集密钥或选择登录方式。
  const [selectedMethodId, setSelectedMethodId] = useState(""); // 新增代码+OpenAIConnectDialog：保存用户当前选择的方法 id；如果没有这行，点击 API key 后无法进入表单步骤。
  useEffect(() => { // 新增代码+OpenAIConnectDialog：副作用段开始，打开新 provider 时重置选择；如果没有这段，上一次选择会污染下一次弹窗。
    if (open) { // 新增代码+OpenAIConnectDialog：只在弹窗打开时重置；如果没有这行，关闭状态也会反复清空无关状态。
      setSelectedMethodId(""); // 新增代码+OpenAIConnectDialog：清空选中方法；如果没有这行，OpenAI 再次打开可能直接跳过方法列表。
    } // 新增代码+OpenAIConnectDialog：打开状态分支结束；如果没有这行，条件块语法不完整。
  }, [open, provider?.id]); // 新增代码+OpenAIConnectDialog：按打开状态和 provider id 变化重置；如果没有这行，切换 provider 后状态会过期。
  const methods = useMemo(() => enabledAuthMethods(provider), [provider]); // 新增代码+OpenAIConnectDialog：缓存可用认证方法；如果没有这行，每次渲染都会重复过滤列表。
  const currentMethod = selectedAuthMethod(methods, selectedMethodId); // 新增代码+OpenAIConnectDialog：解析当前步骤对应方法；如果没有这行，表单无法知道是否可提交。
  if (!open || provider === null) { // 新增代码+ProviderConnectDialog：处理关闭或缺 provider 状态；如果没有这行，空 provider 会导致标题和字段读取异常。
    return null; // 新增代码+ProviderConnectDialog：关闭时不输出内容；如果没有这行，关闭弹窗仍会遮挡设置页。
  } // 新增代码+ProviderConnectDialog：关闭状态分支结束；如果没有这行，条件块语法不完整。
  const showMethodPicker = methods.length > 1 && selectedMethodId.length === 0; // 新增代码+OpenAIConnectDialog：判断是否展示方法列表；如果没有这行，OpenAI 会直接跳进旧 API key 表单。
  const showApiKeyForm = isApiKeyFormMethod(currentMethod) && !showMethodPicker; // 新增代码+OpenAIConnectDialog：判断是否展示 API key 表单；如果没有这行，密码框可能在方法选择阶段出现。
  const submitEnabled = canSubmitApiKey(currentMethod, apiKey, pending); // 修改代码+OpenAIConnectDialog：计算提交按钮是否可用；如果没有这行，按钮禁用逻辑会重复。
  function handleSubmit(event: FormEvent<HTMLFormElement>): void { // 修改代码+OpenAIConnectDialog：函数段开始，处理表单提交；如果没有这段，Enter 键无法提交连接。
    event.preventDefault(); // 新增代码+ProviderConnectDialog：阻止浏览器默认刷新；如果没有这行，提交会刷新整个 Electron renderer。
    if (submitEnabled && currentMethod !== null) { // 修改代码+OpenAIConnectApiKey：只在有当前方法且可提交时调用父回调；如果没有这行，空 key 或无方法仍可能提交。
      onSubmit(currentMethod.id); // 修改代码+OpenAIConnectApiKey：把真实选中方法 id 交给父组件；如果没有这行，父组件会继续写死旧 auth_method_id。
    } // 新增代码+ProviderConnectDialog：提交分支结束；如果没有这行，条件块语法不完整。
  } // 修改代码+OpenAIConnectDialog：函数段结束，handleSubmit 到此结束；如果没有这行，函数语法不完整。
  return ( // 修改代码+OpenAIConnectDialog：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="provider-connect-overlay" role="presentation"> {/* 新增代码+ProviderConnectDialog：渲染连接弹窗遮罩；如果没有这层，连接表单无法覆盖 provider 列表。 */}
      <form className="provider-connect-dialog" data-active-auth-method={currentMethod?.id ?? ""} onSubmit={handleSubmit} role="dialog" aria-modal="true" aria-label={`连接 ${provider.displayName}`}> {/* 修改代码+OpenAIConnectApiKey：渲染连接向导表单并标记当前方法；如果没有这行，测试和父组件都难以确认 API key 对应的 auth method。 */}
        <header className="provider-connect-header"> {/* 新增代码+ProviderConnectDialog：渲染连接弹窗标题栏；如果没有这层，标题和关闭按钮无法对齐。 */}
          <strong>连接 {provider.displayName}</strong> {/* 新增代码+ProviderConnectDialog：显示 provider 名称；如果没有这行，用户不知道正在连接谁。 */}
          <button aria-label="关闭连接弹窗" className="provider-connect-close" type="button" onClick={onClose}>×</button> {/* 新增代码+ProviderConnectDialog：渲染关闭按钮；如果没有这行，用户无法取消连接。 */}
        </header> {/* 新增代码+ProviderConnectDialog：标题栏结束；如果没有这行，JSX 结构不完整。 */}
        {showMethodPicker ? ( // 新增代码+OpenAIConnectDialog：方法选择分支开始；如果没有这行，OpenAI 三方法无法作为第一屏展示。
          <section className="provider-connect-method-picker" aria-label="选择登录方式"> {/* 新增代码+OpenAIConnectDialog：渲染方法选择区域；如果没有这层，方法按钮缺少语义容器。 */}
            <p className="provider-connect-method-title">选择 {provider.displayName} 的登录方式</p> {/* 新增代码+OpenAIConnectDialog：显示方法选择标题；如果没有这行，用户不知道当前步骤目的。 */}
            <div className="provider-connect-method-list"> {/* 新增代码+OpenAIConnectDialog：渲染方法按钮列表；如果没有这层，多个方法无法稳定纵向排列。 */}
              {methods.map((method) => ( // 新增代码+OpenAIConnectDialog：遍历可用认证方法；如果没有这行，方法列表不会生成按钮。
                <button className="provider-connect-method-button" data-testid={authMethodTestId(method)} key={method.id} type="button" onClick={() => setSelectedMethodId(method.id)}> {/* 新增代码+OpenAIConnectDialog：渲染单个方法按钮；如果没有这行，用户无法选择 browser/headless/API key。 */}
                  <span className="provider-connect-method-label">{method.label}</span> {/* 新增代码+OpenAIConnectDialog：显示方法名称；如果没有这行，用户只能看到空按钮。 */}
                  <span className="provider-connect-method-help">{method.helpText}</span> {/* 新增代码+OpenAIConnectDialog：显示方法帮助文案；如果没有这行，用户不知道该方法会做什么。 */}
                  {method.experimental ? <span className="provider-connect-method-badge">实验</span> : null} {/* 新增代码+OpenAIConnectDialog：显示实验标记；如果没有这行，mock OAuth 边界不够明确。 */}
                </button> // 新增代码+OpenAIConnectDialog：方法按钮结束；如果没有这行，JSX 结构不完整。
              ))} {/* 新增代码+OpenAIConnectDialog：方法遍历结束；如果没有这行，JSX 表达式不完整。 */}
            </div> {/* 新增代码+OpenAIConnectDialog：方法按钮列表结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 新增代码+OpenAIConnectDialog：方法选择区域结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 新增代码+OpenAIConnectDialog：方法选择分支结束；如果没有这行，条件渲染语法不完整。 */}
        {showApiKeyForm ? ( // 修改代码+OpenAIConnectDialog：API key 表单分支开始；如果没有这行，单方法 provider 和已选择 API key 的 OpenAI 无法输入密钥。
          <label className="provider-connect-field"> {/* 新增代码+ProviderConnectDialog：渲染 API key 输入标签；如果没有这层，输入框缺少可访问名称。 */}
            <span>API Key</span> {/* 新增代码+ProviderConnectDialog：显示字段名；如果没有这行，用户不知道要填什么。 */}
            <input autoComplete="off" type="password" value={apiKey} onChange={(event) => onApiKeyChange(event.target.value)} /> {/* 新增代码+ProviderConnectDialog：使用密码输入收集 API key；如果没有这行，密钥会明文显示或无法输入。 */}
          </label> // 新增代码+ProviderConnectDialog：API key 输入标签结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 修改代码+OpenAIConnectDialog：API key 表单分支结束；如果没有这行，条件渲染语法不完整。 */}
        {errorMessage.length > 0 ? <div className="provider-connect-error" role="alert">{errorMessage}</div> : null} {/* 新增代码+ProviderConnectDialog：显示安全错误文案；如果没有这行，连接失败没有可见反馈。 */}
        <div className="provider-connect-actions"> {/* 新增代码+ProviderConnectDialog：渲染弹窗按钮区；如果没有这层，取消和连接按钮无法稳定对齐。 */}
          {currentMethod !== null && methods.length > 1 && !showMethodPicker ? <button className="settings-provider-secondary-button" type="button" onClick={() => setSelectedMethodId("")}>返回</button> : null} {/* 新增代码+OpenAIConnectDialog：渲染返回方法列表按钮；如果没有这行，用户选错方法后只能关闭重来。 */}
          <button className="settings-provider-secondary-button" type="button" onClick={onClose}>取消</button> {/* 新增代码+ProviderConnectDialog：渲染取消按钮；如果没有这行，用户无法返回列表。 */}
          {showApiKeyForm ? <button className="settings-provider-primary-button" disabled={!submitEnabled} type="submit">{pending ? "连接中" : "连接"}</button> : null} {/* 修改代码+OpenAIConnectDialog：只在 API key 表单步骤显示连接按钮；如果没有这行，方法选择阶段会出现无法提交的旧按钮。 */}
        </div> {/* 新增代码+ProviderConnectDialog：按钮区结束；如果没有这行，JSX 结构不完整。 */}
      </form> {/* 修改代码+OpenAIConnectDialog：连接向导表单结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+ProviderConnectDialog：连接遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+OpenAIConnectDialog：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+OpenAIConnectDialog：函数段结束，ProviderConnectDialog 到此结束；如果没有这个边界，用户不容易看出连接向导范围。
