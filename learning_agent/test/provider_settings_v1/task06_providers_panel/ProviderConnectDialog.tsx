import type { FormEvent } from "react"; // 新增代码+ProviderConnectDialog：导入表单事件类型；如果没有这行，提交处理函数只能使用不透明 any。
import type { ProviderRowView } from "../../state/providerSettingsStore"; // 新增代码+ProviderConnectDialog：导入 provider 行类型；如果没有这行，连接弹窗不知道要展示和提交哪个 provider。

type ProviderConnectDialogProps = { // 新增代码+ProviderConnectDialog：类型段开始，定义连接弹窗输入；如果没有这段，父组件无法受控管理 API key。
  open: boolean; // 新增代码+ProviderConnectDialog：保存弹窗是否打开；如果没有这行，关闭状态无法移除 DOM。
  provider: ProviderRowView | null; // 新增代码+ProviderConnectDialog：保存当前 provider；如果没有这行，弹窗无法显示标题或提交 provider id。
  apiKey: string; // 新增代码+ProviderConnectDialog：保存受控 API key 输入；如果没有这行，本地密钥状态无法由父组件成功后清空。
  pending: boolean; // 新增代码+ProviderConnectDialog：保存提交等待态；如果没有这行，用户可能重复点击连接。
  errorMessage: string; // 新增代码+ProviderConnectDialog：保存安全错误文案；如果没有这行，后端失败只能留在控制台。
  onApiKeyChange: (value: string) => void; // 新增代码+ProviderConnectDialog：保存输入变化回调；如果没有这行，API key 输入框无法受控。
  onClose: () => void; // 新增代码+ProviderConnectDialog：保存关闭回调；如果没有这行，用户无法取消连接。
  onSubmit: () => void; // 新增代码+ProviderConnectDialog：保存提交回调；如果没有这行，连接按钮没有后端动作。
}; // 新增代码+ProviderConnectDialog：ProviderConnectDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

function canSubmitApiKey(provider: ProviderRowView | null, apiKey: string, pending: boolean): boolean { // 新增代码+ProviderConnectDialog：函数段开始，判断能否提交 API key；如果没有这段，禁用逻辑会散落在 JSX 中。
  const hasEnabledAuth = provider?.authMethods.some((method) => method.enabled) ?? false; // 新增代码+ProviderConnectDialog：检查是否有可用认证方式；如果没有这行，Copilot 未支持状态可能被提交。
  return hasEnabledAuth && apiKey.trim().length > 0 && !pending; // 新增代码+ProviderConnectDialog：只有可认证、非空且不等待时允许提交；如果没有这行，空 key 或重复请求会打到后端。
} // 新增代码+ProviderConnectDialog：函数段结束，canSubmitApiKey 到此结束；如果没有这行，函数语法不完整。

export function ProviderConnectDialog({ open, provider, apiKey, pending, errorMessage, onApiKeyChange, onClose, onSubmit }: ProviderConnectDialogProps): JSX.Element | null { // 新增代码+ProviderConnectDialog：函数段开始，渲染 Provider API key 连接弹窗；如果没有这段，连接按钮无法收集密钥。
  if (!open || provider === null) { // 新增代码+ProviderConnectDialog：处理关闭或缺 provider 状态；如果没有这行，空 provider 会导致标题和字段读取异常。
    return null; // 新增代码+ProviderConnectDialog：关闭时不输出内容；如果没有这行，关闭弹窗仍会遮挡设置页。
  } // 新增代码+ProviderConnectDialog：关闭状态分支结束；如果没有这行，条件块语法不完整。
  const submitEnabled = canSubmitApiKey(provider, apiKey, pending); // 新增代码+ProviderConnectDialog：计算提交按钮是否可用；如果没有这行，按钮禁用逻辑会重复。
  function handleSubmit(event: FormEvent<HTMLFormElement>): void { // 新增代码+ProviderConnectDialog：函数段开始，处理表单提交；如果没有这段，Enter 键无法提交连接。
    event.preventDefault(); // 新增代码+ProviderConnectDialog：阻止浏览器默认刷新；如果没有这行，提交会刷新整个 Electron renderer。
    if (submitEnabled) { // 新增代码+ProviderConnectDialog：只在可提交时调用父回调；如果没有这行，空 key 仍可能提交。
      onSubmit(); // 新增代码+ProviderConnectDialog：调用父组件提交；如果没有这行，连接按钮没有后端动作。
    } // 新增代码+ProviderConnectDialog：提交分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+ProviderConnectDialog：函数段结束，handleSubmit 到此结束；如果没有这行，函数语法不完整。
  return ( // 新增代码+ProviderConnectDialog：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="provider-connect-overlay" role="presentation"> {/* 新增代码+ProviderConnectDialog：渲染连接弹窗遮罩；如果没有这层，连接表单无法覆盖 provider 列表。 */}
      <form className="provider-connect-dialog" onSubmit={handleSubmit} role="dialog" aria-modal="true" aria-label={`连接 ${provider.displayName}`}> {/* 新增代码+ProviderConnectDialog：渲染连接表单对话框；如果没有这行，读屏器无法识别连接流程。 */}
        <header className="provider-connect-header"> {/* 新增代码+ProviderConnectDialog：渲染连接弹窗标题栏；如果没有这层，标题和关闭按钮无法对齐。 */}
          <strong>连接 {provider.displayName}</strong> {/* 新增代码+ProviderConnectDialog：显示 provider 名称；如果没有这行，用户不知道正在连接谁。 */}
          <button aria-label="关闭连接弹窗" className="provider-connect-close" type="button" onClick={onClose}>×</button> {/* 新增代码+ProviderConnectDialog：渲染关闭按钮；如果没有这行，用户无法取消连接。 */}
        </header> {/* 新增代码+ProviderConnectDialog：标题栏结束；如果没有这行，JSX 结构不完整。 */}
        <label className="provider-connect-field"> {/* 新增代码+ProviderConnectDialog：渲染 API key 输入标签；如果没有这层，输入框缺少可访问名称。 */}
          <span>API Key</span> {/* 新增代码+ProviderConnectDialog：显示字段名；如果没有这行，用户不知道要填什么。 */}
          <input autoComplete="off" type="password" value={apiKey} onChange={(event) => onApiKeyChange(event.target.value)} /> {/* 新增代码+ProviderConnectDialog：使用密码输入收集 API key；如果没有这行，密钥会明文显示或无法输入。 */}
        </label> {/* 新增代码+ProviderConnectDialog：API key 输入标签结束；如果没有这行，JSX 结构不完整。 */}
        {errorMessage.length > 0 ? <div className="provider-connect-error" role="alert">{errorMessage}</div> : null} {/* 新增代码+ProviderConnectDialog：显示安全错误文案；如果没有这行，连接失败没有可见反馈。 */}
        <div className="provider-connect-actions"> {/* 新增代码+ProviderConnectDialog：渲染弹窗按钮区；如果没有这层，取消和连接按钮无法稳定对齐。 */}
          <button className="settings-provider-secondary-button" type="button" onClick={onClose}>取消</button> {/* 新增代码+ProviderConnectDialog：渲染取消按钮；如果没有这行，用户无法返回列表。 */}
          <button className="settings-provider-primary-button" disabled={!submitEnabled} type="submit">{pending ? "连接中" : "连接"}</button> {/* 新增代码+ProviderConnectDialog：渲染连接按钮；如果没有这行，API key 无法提交给 bridge。 */}
        </div> {/* 新增代码+ProviderConnectDialog：按钮区结束；如果没有这行，JSX 结构不完整。 */}
      </form> {/* 新增代码+ProviderConnectDialog：连接表单结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+ProviderConnectDialog：连接遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+ProviderConnectDialog：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+ProviderConnectDialog：函数段结束，ProviderConnectDialog 到此结束；如果没有这个边界，用户不容易看出连接弹窗范围。
