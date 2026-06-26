import { Plus, RefreshCw, TestTube2 } from "lucide-react"; // 新增代码+ProviderSettingsPanel：导入 Provider 面板按钮图标；如果没有这行，连接、重试和测试连接按钮会缺少视觉提示。
import { providerRowsForDisplay, type ProviderRowView, type ProviderSettingsViewModel } from "../../state/providerSettingsStore"; // 新增代码+ProviderSettingsPanel：导入 Provider view model 和排序 helper；如果没有这行，面板会直接消费后端原始 payload。
import { ProviderIcon } from "./ProviderIcon"; // 新增代码+ProviderSettingsPanel：导入 provider 图标组件；如果没有这行，列表左侧缺少可扫描锚点。

type SettingsProvidersPanelProps = { // 新增代码+ProviderSettingsPanel：类型段开始，定义 Provider 面板输入；如果没有这段，SettingsDialog 不知道如何驱动列表。
  viewModel: ProviderSettingsViewModel | null; // 新增代码+ProviderSettingsPanel：保存 provider settings view model；如果没有这行，面板无法渲染 provider rows。
  loading: boolean; // 新增代码+ProviderSettingsPanel：保存加载状态；如果没有这行，用户不知道 catalog 是否正在读取。
  errorMessage: string; // 新增代码+ProviderSettingsPanel：保存加载错误文案；如果没有这行，失败只能留在控制台。
  busyProviderId: string; // 新增代码+ProviderSettingsPanel：保存正在操作的 provider；如果没有这行，按钮无法避免重复点击。
  probeResults: Record<string, string>; // 新增代码+ProviderSettingsPanel：保存 provider 探针状态；如果没有这行，测试连接结果无法显示在对应行。
  onRetry: () => void; // 新增代码+ProviderSettingsPanel：保存重试加载回调；如果没有这行，错误状态没有恢复入口。
  onConnectProvider: (provider: ProviderRowView) => void; // 新增代码+ProviderSettingsPanel：保存连接回调；如果没有这行，连接按钮无法打开连接弹窗。
  onDisconnectProvider: (provider: ProviderRowView) => void; // 新增代码+ProviderSettingsPanel：保存断开回调；如果没有这行，已连接 provider 无法断开。
  onTestProvider: (provider: ProviderRowView) => void; // 新增代码+ProviderSettingsPanel：保存测试连接回调；如果没有这行，测试连接按钮没有后端动作。
  onOpenCustomProvider: () => void; // 新增代码+ProviderSettingsPanel：保存自定义 provider 入口回调；如果没有这行，虚拟 CTA 可能被误当 provider mutation。
}; // 新增代码+ProviderSettingsPanel：SettingsProvidersPanelProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function probeStatusLabel(status: string): string { // 新增代码+ProviderSettingsPanel：函数段开始，把探针状态转成安全文案；如果没有这段，UI 可能显示底层错误码或敏感细节。
  if (status === "ok") { // 新增代码+ProviderSettingsPanel：识别成功状态；如果没有这行，成功测试无法显示友好文案。
    return "连接测试通过"; // 新增代码+ProviderSettingsPanel：返回成功文案；如果没有这行，用户不知道连接已通过。
  } // 新增代码+ProviderSettingsPanel：成功分支结束；如果没有这行，条件块语法不完整。
  if (status === "auth_failed") { // 新增代码+ProviderSettingsPanel：识别认证失败状态；如果没有这行，认证失败会落入通用错误。
    return "认证失败"; // 新增代码+ProviderSettingsPanel：返回认证失败文案；如果没有这行，用户不知道应检查 API key。
  } // 新增代码+ProviderSettingsPanel：认证失败分支结束；如果没有这行，条件块语法不完整。
  if (status === "missing_secret") { // 新增代码+ProviderSettingsPanel：识别缺少密钥状态；如果没有这行，缺密钥会落入通用错误。
    return "缺少密钥"; // 新增代码+ProviderSettingsPanel：返回缺密钥文案；如果没有这行，用户不知道应先连接。
  } // 新增代码+ProviderSettingsPanel：缺密钥分支结束；如果没有这行，条件块语法不完整。
  if (status === "network_failed") { // 新增代码+ProviderSettingsPanel：识别网络失败状态；如果没有这行，网络问题可能显示底层异常。
    return "网络不可达"; // 新增代码+ProviderSettingsPanel：返回网络失败文案；如果没有这行，用户不知道是连通性问题。
  } // 新增代码+ProviderSettingsPanel：网络失败分支结束；如果没有这行，条件块语法不完整。
  if (status === "unsupported") { // 新增代码+ProviderSettingsPanel：识别暂不支持状态；如果没有这行，Copilot/Google 等场景会显示奇怪错误。
    return "暂不支持测试"; // 新增代码+ProviderSettingsPanel：返回暂不支持文案；如果没有这行，用户会误以为配置错误。
  } // 新增代码+ProviderSettingsPanel：暂不支持分支结束；如果没有这行，条件块语法不完整。
  if (status === "invalid_config") { // 新增代码+ProviderSettingsPanel：识别配置无效状态；如果没有这行，自定义 provider 配置问题无法说明。
    return "配置无效"; // 新增代码+ProviderSettingsPanel：返回配置无效文案；如果没有这行，用户不知道要检查 base URL 或模型。
  } // 新增代码+ProviderSettingsPanel：配置无效分支结束；如果没有这行，条件块语法不完整。
  return "连接测试失败"; // 新增代码+ProviderSettingsPanel：未知状态使用安全兜底；如果没有这行，未知错误码可能直接暴露。
} // 新增代码+ProviderSettingsPanel：函数段结束，probeStatusLabel 到此结束；如果没有这行，函数语法不完整。

function sourceLabel(source: string): string { // 新增代码+ProviderSettingsPanel：函数段开始，把 provider 来源转成 badge 文案；如果没有这段，source 只能显示机器码。
  if (source === "env") { // 新增代码+ProviderSettingsPanel：识别环境变量来源；如果没有这行，env provider 无法解释为什么不能断开。
    return "ENV"; // 新增代码+ProviderSettingsPanel：返回环境变量 badge；如果没有这行，用户不知道凭据来自环境。
  } // 新增代码+ProviderSettingsPanel：环境变量分支结束；如果没有这行，条件块语法不完整。
  if (source === "config") { // 新增代码+ProviderSettingsPanel：识别配置来源；如果没有这行，配置文件 provider 会显示机器码。
    return "API"; // 新增代码+ProviderSettingsPanel：返回 API badge；如果没有这行，用户不知道凭据来自设置。
  } // 新增代码+ProviderSettingsPanel：配置来源分支结束；如果没有这行，条件块语法不完整。
  if (source === "custom") { // 新增代码+ProviderSettingsPanel：识别自定义来源；如果没有这行，自定义 provider 无法区分。
    return "自定义"; // 新增代码+ProviderSettingsPanel：返回自定义 badge；如果没有这行，用户不知道这是自己添加的 provider。
  } // 新增代码+ProviderSettingsPanel：自定义来源分支结束；如果没有这行，条件块语法不完整。
  return ""; // 新增代码+ProviderSettingsPanel：无来源不显示 badge；如果没有这行，none 会作为噪音显示。
} // 新增代码+ProviderSettingsPanel：函数段结束，sourceLabel 到此结束；如果没有这行，函数语法不完整。

function providerActionDisabled(provider: ProviderRowView, busyProviderId: string): boolean { // 新增代码+ProviderSettingsPanel：函数段开始，计算主按钮禁用状态；如果没有这段，按钮禁用逻辑会散落在 JSX 中。
  return provider.primaryActionDisabled || busyProviderId === provider.id; // 新增代码+ProviderSettingsPanel：禁用 unsupported 或正在操作的 provider；如果没有这行，用户可能重复提交或点击未支持项。
} // 新增代码+ProviderSettingsPanel：函数段结束，providerActionDisabled 到此结束；如果没有这行，函数语法不完整。

export function SettingsProvidersPanel({ viewModel, loading, errorMessage, busyProviderId, probeResults, onRetry, onConnectProvider, onDisconnectProvider, onTestProvider, onOpenCustomProvider }: SettingsProvidersPanelProps): JSX.Element { // 新增代码+ProviderSettingsPanel：函数段开始，渲染 Provider Settings 列表；如果没有这段，设置弹窗无法管理大模型提供商。
  if (loading) { // 新增代码+ProviderSettingsPanel：处理加载状态；如果没有这行，catalog 请求期间界面会空白。
    return <div className="settings-dialog-placeholder">正在加载提供商</div>; // 新增代码+ProviderSettingsPanel：显示加载文本；如果没有这行，用户不知道列表正在读取。
  } // 新增代码+ProviderSettingsPanel：加载状态分支结束；如果没有这行，条件块语法不完整。
  if (errorMessage.length > 0) { // 新增代码+ProviderSettingsPanel：处理错误状态；如果没有这行，加载失败不会进入可见 UI。
    return ( // 新增代码+ProviderSettingsPanel：返回错误界面；如果没有这行，错误分支无法输出多个元素。
      <div className="settings-provider-error" role="alert"> {/* 新增代码+ProviderSettingsPanel：渲染错误容器；如果没有这层，读屏器无法识别加载失败。 */}
        <strong>提供商加载失败</strong> {/* 新增代码+ProviderSettingsPanel：显示固定错误标题；如果没有这行，用户看不出失败范围。 */}
        <span>{errorMessage}</span> {/* 新增代码+ProviderSettingsPanel：显示安全错误文案；如果没有这行，失败原因没有位置。 */}
        <button className="settings-provider-secondary-button" type="button" onClick={onRetry}> {/* 新增代码+ProviderSettingsPanel：渲染重试按钮；如果没有这行，用户无法重新加载 provider catalog。 */}
          <RefreshCw aria-hidden={true} size={14} /> {/* 新增代码+ProviderSettingsPanel：显示重试图标；如果没有这行，按钮意图不够直观。 */}
          <span>重试</span> {/* 新增代码+ProviderSettingsPanel：显示重试文字；如果没有这行，按钮只剩图标不清楚。 */}
        </button> {/* 新增代码+ProviderSettingsPanel：重试按钮结束；如果没有这行，JSX 结构不完整。 */}
      </div> // 新增代码+ProviderSettingsPanel：错误容器结束；如果没有这行，JSX 结构不完整。
    ); // 新增代码+ProviderSettingsPanel：错误分支返回结束；如果没有这行，return 语法不完整。
  } // 新增代码+ProviderSettingsPanel：错误状态分支结束；如果没有这行，条件块语法不完整。
  const rows = viewModel === null ? [] : providerRowsForDisplay(viewModel); // 新增代码+ProviderSettingsPanel：读取并排序 provider rows；如果没有这行，列表顺序会不稳定。
  if (rows.length === 0 || viewModel === null) { // 新增代码+ProviderSettingsPanel：处理空列表状态；如果没有这行，空 payload 会显示空白。
    return <div className="settings-dialog-placeholder">暂无提供商</div>; // 新增代码+ProviderSettingsPanel：显示空态文本；如果没有这行，用户不知道没有 provider。
  } // 新增代码+ProviderSettingsPanel：空列表分支结束；如果没有这行，条件块语法不完整。
  return ( // 新增代码+ProviderSettingsPanel：返回 provider 列表结构；如果没有这行，组件不会输出 UI。
    <div className="settings-provider-list"> {/* 新增代码+ProviderSettingsPanel：渲染 provider 列表容器；如果没有这层，行间距和滚动无法统一。 */}
      {rows.map((provider) => { // 新增代码+ProviderSettingsPanel：遍历 provider rows；如果没有这行，后端 provider 不会进入 UI。
        const badge = sourceLabel(provider.source); // 新增代码+ProviderSettingsPanel：计算来源 badge；如果没有这行，来源标签无法显示。
        const probeResult = probeResults[provider.id] ?? ""; // 新增代码+ProviderSettingsPanel：读取当前 provider 探针结果；如果没有这行，测试连接反馈无法对齐行。
        const disabled = providerActionDisabled(provider, busyProviderId); // 新增代码+ProviderSettingsPanel：计算主按钮禁用状态；如果没有这行，按钮可能重复点击。
        return ( // 新增代码+ProviderSettingsPanel：返回单个 provider 行；如果没有这行，map 不会输出元素。
          <section className="settings-provider-row" key={provider.id}> {/* 新增代码+ProviderSettingsPanel：渲染 provider 行容器；如果没有这层，图标、文本和按钮无法稳定对齐。 */}
            <ProviderIcon providerId={provider.id} displayName={provider.displayName} /> {/* 新增代码+ProviderSettingsPanel：显示 provider 图标；如果没有这行，列表左侧缺少视觉锚点。 */}
            <div className="settings-provider-copy"> {/* 新增代码+ProviderSettingsPanel：渲染 provider 文案区；如果没有这层，标题和描述会散落。 */}
              <div className="settings-provider-title-row"> {/* 新增代码+ProviderSettingsPanel：渲染标题和 badge 行；如果没有这层，状态标签无法对齐。 */}
                <strong>{provider.displayName}</strong> {/* 新增代码+ProviderSettingsPanel：显示 provider 名称；如果没有这行，用户不知道当前行是谁。 */}
                {provider.connected ? <span className="settings-provider-status">已连接</span> : null} {/* 新增代码+ProviderSettingsPanel：显示已连接状态；如果没有这行，当前连接不明显。 */}
                {badge.length > 0 ? <span className="settings-provider-badge">{badge}</span> : null} {/* 新增代码+ProviderSettingsPanel：显示来源 badge；如果没有这行，env/config/custom 来源不可见。 */}
              </div> {/* 新增代码+ProviderSettingsPanel：标题和 badge 行结束；如果没有这行，JSX 结构不完整。 */}
              <p>{provider.description}</p> {/* 新增代码+ProviderSettingsPanel：显示 provider 描述；如果没有这行，用户缺少连接方式上下文。 */}
              {provider.connected && provider.maskedKey.length > 0 ? <small>{provider.maskedKey}</small> : null} {/* 新增代码+ProviderSettingsPanel：显示脱敏 key 摘要；如果没有这行，用户无法确认连接凭据但也不会暴露 raw key。 */}
              {probeResult.length > 0 ? <small className="settings-provider-probe-result">{probeStatusLabel(probeResult)}</small> : null} {/* 新增代码+ProviderSettingsPanel：显示安全探针结果；如果没有这行，测试连接没有可见反馈。 */}
            </div> {/* 新增代码+ProviderSettingsPanel：provider 文案区结束；如果没有这行，JSX 结构不完整。 */}
            <div className="settings-provider-actions"> {/* 新增代码+ProviderSettingsPanel：渲染 provider 操作区；如果没有这层，按钮无法固定宽度。 */}
              {provider.connected ? ( // 新增代码+ProviderSettingsPanel：处理已连接 provider 操作；如果没有这行，已连接和未连接按钮会混在一起。
                <button className="settings-provider-secondary-button" data-testid={`provider-test-${provider.id}`} disabled={busyProviderId === provider.id} type="button" onClick={() => onTestProvider(provider)}> {/* 新增代码+ProviderSettingsPanel：渲染测试连接按钮；如果没有这行，用户无法执行 connection probe。 */}
                  <TestTube2 aria-hidden={true} size={14} /> {/* 新增代码+ProviderSettingsPanel：显示测试图标；如果没有这行，按钮意图不够直观。 */}
                  <span>测试连接</span> {/* 新增代码+ProviderSettingsPanel：显示测试连接文本；如果没有这行，按钮只剩图标不清楚。 */}
                </button> // 新增代码+ProviderSettingsPanel：测试连接按钮结束；如果没有这行，JSX 结构不完整。
              ) : null} {/* 新增代码+ProviderSettingsPanel：已连接测试按钮条件结束；如果没有这行，JSX 表达式不完整。 */}
              {provider.connected && provider.source === "env" ? ( // 新增代码+ProviderSettingsPanel：处理 env 来源连接；如果没有这行，环境变量 provider 会误显示断开 mutation。
                <button className="settings-provider-primary-button" disabled={true} type="button">环境变量</button> // 新增代码+ProviderSettingsPanel：显示不可断开的环境变量按钮；如果没有这行，用户不知道为什么不能断开。
              ) : ( // 新增代码+ProviderSettingsPanel：处理普通连接或断开按钮；如果没有这行，条件渲染语法不完整。
                <button className="settings-provider-primary-button" data-testid={`provider-action-${provider.id}`} disabled={disabled} type="button" onClick={() => { provider.connected ? onDisconnectProvider(provider) : onConnectProvider(provider); }}> {/* 新增代码+ProviderSettingsPanel：渲染主操作按钮；如果没有这行，连接和断开没有入口。 */}
                  <span>{busyProviderId === provider.id ? "处理中" : provider.primaryActionLabel}</span> {/* 新增代码+ProviderSettingsPanel：显示主操作文案；如果没有这行，用户不知道按钮动作。 */}
                </button> // 新增代码+ProviderSettingsPanel：主操作按钮结束；如果没有这行，JSX 结构不完整。
              )} {/* 新增代码+ProviderSettingsPanel：主操作条件结束；如果没有这行，JSX 表达式不完整。 */}
            </div> {/* 新增代码+ProviderSettingsPanel：provider 操作区结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 新增代码+ProviderSettingsPanel：provider 行结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+ProviderSettingsPanel：单个 provider 返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+ProviderSettingsPanel：provider rows 遍历结束；如果没有这行，JSX 表达式不完整。 */}
      <button className="settings-provider-row settings-provider-custom-row" data-testid="provider-custom-cta" type="button" onClick={onOpenCustomProvider}> {/* 新增代码+ProviderSettingsPanel：渲染虚拟自定义 provider 入口；如果没有这行，用户无法添加兼容 provider。 */}
        <span className="provider-icon provider-icon-custom"><Plus aria-hidden={true} size={15} /></span> {/* 新增代码+ProviderSettingsPanel：显示自定义入口图标；如果没有这行，CTA 缺少视觉锚点。 */}
        <span className="settings-provider-copy"> {/* 新增代码+ProviderSettingsPanel：渲染自定义入口文案区；如果没有这层，CTA 文案无法对齐 provider 行。 */}
          <strong>{viewModel.customProviderCta.displayName}</strong> {/* 新增代码+ProviderSettingsPanel：显示自定义入口标题；如果没有这行，用户不知道这是添加入口。 */}
          <small>{viewModel.customProviderCta.description}</small> {/* 新增代码+ProviderSettingsPanel：显示自定义入口描述；如果没有这行，入口用途不清楚。 */}
        </span> {/* 新增代码+ProviderSettingsPanel：自定义入口文案区结束；如果没有这行，JSX 结构不完整。 */}
      </button> {/* 新增代码+ProviderSettingsPanel：自定义 provider 入口结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+ProviderSettingsPanel：provider 列表容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+ProviderSettingsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+ProviderSettingsPanel：函数段结束，SettingsProvidersPanel 到此结束；如果没有这个边界，用户不容易看出列表组件范围。
