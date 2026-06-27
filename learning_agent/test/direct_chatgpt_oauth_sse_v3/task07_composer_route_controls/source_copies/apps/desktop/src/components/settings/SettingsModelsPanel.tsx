import { modelGroupsForDisplay, type ModelGroupView, type ProviderModelView, type ProviderSettingsViewModel } from "../../state/providerSettingsStore"; // 新增代码+SettingsModelsPanel：导入模型分组 helper 和类型；如果没有这行，模型面板会重复实现排序和分组逻辑。

type SettingsModelsPanelProps = { // 新增代码+SettingsModelsPanel：类型段开始，定义模型面板输入；如果没有这段，SettingsDialog 无法安全驱动模型页。
  viewModel: ProviderSettingsViewModel | null; // 新增代码+SettingsModelsPanel：保存 provider settings view model；如果没有这行，模型面板拿不到 provider 和模型数据。
  pendingModelKey: string; // 新增代码+SettingsModelsPanel：保存正在保存的模型 key；如果没有这行，开关无法进入等待禁用状态。
  errorMessage: string; // 新增代码+SettingsModelsPanel：保存可见性保存错误文案；如果没有这行，失败无法反馈给用户。
  onToggleModel: (providerId: string, modelId: string, visible: boolean) => void; // 新增代码+SettingsModelsPanel：保存开关回调；如果没有这行，模型可见性无法写入后端。
}; // 新增代码+SettingsModelsPanel：SettingsModelsPanelProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function modelVisibilityKey(providerId: string, modelId: string): string { // 新增代码+SettingsModelsPanel：函数段开始，生成模型等待态 key；如果没有这段，父子组件可能使用不同 key 规则。
  return `${providerId}:${modelId}`; // 新增代码+SettingsModelsPanel：用 provider 和 model 组合成唯一 key；如果没有这行，同名模型会互相影响等待态。
} // 新增代码+SettingsModelsPanel：函数段结束，modelVisibilityKey 到此结束；如果没有这行，函数语法不完整。

function modelSwitchTestId(providerId: string, modelId: string): string { // 新增代码+SettingsModelsPanel：函数段开始，生成测试 id；如果没有这段，测试只能依赖脆弱 DOM 顺序。
  return `model-switch-${providerId}-${modelId}`; // 新增代码+SettingsModelsPanel：返回稳定 data-testid；如果没有这行，自动测试无法定位具体模型开关。
} // 新增代码+SettingsModelsPanel：函数段结束，modelSwitchTestId 到此结束；如果没有这行，函数语法不完整。

export function modelProbeStateLabel(state: string): string { // 新增代码+ComposerRouteControls：函数段开始，把模型探针状态转成可读文案；如果没有这段，模型页只能显示机器码。
  if (state === "available") { // 新增代码+ComposerRouteControls：识别可用模型；如果没有这行，成功探针无法显示友好状态。
    return "可用"; // 新增代码+ComposerRouteControls：返回可用文案；如果没有这行，用户不知道模型已验证。
  } // 新增代码+ComposerRouteControls：可用分支结束；如果没有这行，条件块语法不完整。
  if (state === "not_supported_for_account") { // 新增代码+ComposerRouteControls：识别账号不支持状态；如果没有这行，用户可能继续选择会失败的模型。
    return "当前账号不支持"; // 新增代码+ComposerRouteControls：返回账号不支持文案；如果没有这行，模型失败原因不直观。
  } // 新增代码+ComposerRouteControls：账号不支持分支结束；如果没有这行，条件块语法不完整。
  if (state === "auth_failed") { // 新增代码+ComposerRouteControls：识别认证失败状态；如果没有这行，OAuth 失效时状态不清楚。
    return "认证失败"; // 新增代码+ComposerRouteControls：返回认证失败文案；如果没有这行，用户不知道需要重新连接。
  } // 新增代码+ComposerRouteControls：认证失败分支结束；如果没有这行，条件块语法不完整。
  if (state === "rate_limited") { // 新增代码+ComposerRouteControls：识别限流状态；如果没有这行，慢或失败可能被误解成代码错误。
    return "被限流"; // 新增代码+ComposerRouteControls：返回限流文案；如果没有这行，用户不知道要等待或换模型。
  } // 新增代码+ComposerRouteControls：限流分支结束；如果没有这行，条件块语法不完整。
  if (state === "probe_failed") { // 新增代码+ComposerRouteControls：识别探针失败状态；如果没有这行，未知错误会没有安全文案。
    return "探针失败"; // 新增代码+ComposerRouteControls：返回探针失败文案；如果没有这行，用户看不出这是验证失败。
  } // 新增代码+ComposerRouteControls：探针失败分支结束；如果没有这行，条件块语法不完整。
  return "待验证"; // 新增代码+ComposerRouteControls：默认显示待验证；如果没有这行，静态候选模型会缺少状态。
} // 新增代码+ComposerRouteControls：函数段结束，modelProbeStateLabel 到此结束；如果没有这行，函数语法不完整。

function modelSourceLabel(source: string): string { // 新增代码+ComposerRouteControls：函数段开始，把模型来源转成可读文案；如果没有这段，用户不知道模型为何出现在菜单里。
  if (source === "probe_available_models") { // 新增代码+ComposerRouteControls：识别探针发现模型；如果没有这行，真实账号模型来源不清楚。
    return "探针发现"; // 新增代码+ComposerRouteControls：返回探针来源；如果没有这行，用户无法区分静态和真实发现。
  } // 新增代码+ComposerRouteControls：探针来源分支结束；如果没有这行，条件块语法不完整。
  if (source === "last_known_good_models") { // 新增代码+ComposerRouteControls：识别最后成功模型；如果没有这行，缓存模型来源不清楚。
    return "上次成功"; // 新增代码+ComposerRouteControls：返回最后成功文案；如果没有这行，用户不知道这是回退显示。
  } // 新增代码+ComposerRouteControls：最后成功分支结束；如果没有这行，条件块语法不完整。
  if (source === "static_known_models") { // 新增代码+ComposerRouteControls：识别静态候选模型；如果没有这行，未探针模型会没有解释。
    return "静态候选"; // 新增代码+ComposerRouteControls：返回静态候选文案；如果没有这行，待验证模型来源不清楚。
  } // 新增代码+ComposerRouteControls：静态候选分支结束；如果没有这行，条件块语法不完整。
  return source; // 新增代码+ComposerRouteControls：未知来源原样显示安全文本；如果没有这行，未来来源会变成空白。
} // 新增代码+ComposerRouteControls：函数段结束，modelSourceLabel 到此结束；如果没有这行，函数语法不完整。

function renderModelRow(group: ModelGroupView, model: ProviderModelView, pendingModelKey: string, onToggleModel: SettingsModelsPanelProps["onToggleModel"]): JSX.Element { // 新增代码+SettingsModelsPanel：函数段开始，渲染单个模型行；如果没有这段，模型行 JSX 会塞进主循环难以阅读。
  const rowKey = modelVisibilityKey(group.providerId, model.id); // 新增代码+SettingsModelsPanel：计算当前模型等待 key；如果没有这行，开关无法判断自己是否 pending。
  const pending = pendingModelKey === rowKey; // 新增代码+SettingsModelsPanel：判断当前模型是否保存中；如果没有这行，所有开关都会缺少等待态。
  return ( // 新增代码+SettingsModelsPanel：返回模型行 JSX；如果没有这行，函数没有 UI 输出。
    <div className="settings-model-row" key={rowKey}> {/* 新增代码+SettingsModelsPanel：渲染模型行容器；如果没有这层，模型文本和开关无法稳定对齐。 */}
      <div className="settings-model-copy"> {/* 新增代码+SettingsModelsPanel：渲染模型文案区；如果没有这层，模型名、id 和 provider 会散落。 */}
        <strong>{model.displayName}</strong> {/* 新增代码+SettingsModelsPanel：显示模型显示名；如果没有这行，用户看不到模型主名称。 */}
        <span>{model.id}</span> {/* 新增代码+SettingsModelsPanel：显示模型 id；如果没有这行，用户无法区分同名或相似模型。 */}
        <small>{group.providerName}</small> {/* 新增代码+SettingsModelsPanel：显示 provider 名称；如果没有这行，模型来源不清楚。 */}
        <small>{modelProbeStateLabel(model.state)} · {modelSourceLabel(model.source)}</small> {/* 新增代码+ComposerRouteControls：显示模型探针状态和来源；如果没有这行，用户不知道模型是可用、静态候选还是账号不支持。 */}
        {model.message.length > 0 ? <small>{model.message}</small> : null} {/* 新增代码+ComposerRouteControls：显示安全模型状态说明；如果没有这行，unsupported 或 probe 失败缺少上下文。 */}
      </div> {/* 新增代码+SettingsModelsPanel：模型文案区结束；如果没有这行，JSX 结构不完整。 */}
      <label className="settings-model-switch"> {/* 新增代码+SettingsModelsPanel：渲染可见性开关标签；如果没有这层，开关缺少可点击文本区域。 */}
        <input aria-label={`切换 ${model.displayName} 可见性`} checked={model.visible} data-testid={modelSwitchTestId(group.providerId, model.id)} disabled={pending} role="switch" type="checkbox" onChange={(event) => onToggleModel(group.providerId, model.id, event.target.checked)} /> {/* 新增代码+SettingsModelsPanel：渲染受控 switch 并调用可见性回调；如果没有这行，模型可见性无法修改。 */}
        <span>{pending ? "保存中" : model.visible ? "可见" : "隐藏"}</span> {/* 新增代码+SettingsModelsPanel：显示开关状态文本；如果没有这行，用户不容易判断当前模型是否可见。 */}
      </label> {/* 新增代码+SettingsModelsPanel：可见性开关标签结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+SettingsModelsPanel：模型行容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+SettingsModelsPanel：模型行返回结束；如果没有这行，函数没有返回边界。
} // 新增代码+SettingsModelsPanel：函数段结束，renderModelRow 到此结束；如果没有这行，函数语法不完整。

export function SettingsModelsPanel({ viewModel, pendingModelKey, errorMessage, onToggleModel }: SettingsModelsPanelProps): JSX.Element { // 新增代码+SettingsModelsPanel：函数段开始，渲染模型可见性面板；如果没有这段，设置页模型标签只能显示占位。
  const groups = viewModel === null ? [] : modelGroupsForDisplay(viewModel); // 新增代码+SettingsModelsPanel：从 view model 构建有模型的 provider 分组；如果没有这行，模型无法按 provider 显示。
  if (groups.length === 0) { // 新增代码+SettingsModelsPanel：处理没有模型的空态；如果没有这行，未连接 provider 时内容区会空白。
    return <div className="settings-dialog-placeholder">连接提供商后会在这里显示模型</div>; // 新增代码+SettingsModelsPanel：显示蓝图指定空态文案；如果没有这行，用户不知道下一步要连接 provider。
  } // 新增代码+SettingsModelsPanel：空态分支结束；如果没有这行，条件块语法不完整。
  return ( // 新增代码+SettingsModelsPanel：返回模型分组列表；如果没有这行，组件没有 UI 输出。
    <div className="settings-model-list"> {/* 新增代码+SettingsModelsPanel：渲染模型列表容器；如果没有这层，模型分组缺少统一布局。 */}
      {errorMessage.length > 0 ? <div className="settings-model-error" role="alert">{errorMessage}</div> : null} {/* 新增代码+SettingsModelsPanel：显示模型可见性保存错误；如果没有这行，保存失败没有可见反馈。 */}
      {groups.map((group) => ( // 新增代码+SettingsModelsPanel：遍历 provider 模型分组；如果没有这行，模型数据不会进入 UI。
        <section className="settings-model-group" key={group.providerId}> {/* 新增代码+SettingsModelsPanel：渲染单个 provider 分组；如果没有这层，模型无法按 provider 聚合。 */}
          <header className="settings-model-group-header"> {/* 新增代码+SettingsModelsPanel：渲染分组标题行；如果没有这层，provider 名和连接状态无法对齐。 */}
            <strong>{group.providerName}</strong> {/* 新增代码+SettingsModelsPanel：显示 provider 名称；如果没有这行，用户不知道这一组模型来源。 */}
            {group.connected ? <span className="settings-provider-status">已连接</span> : <span className="settings-provider-badge">未连接</span>} {/* 新增代码+SettingsModelsPanel：显示 provider 连接状态；如果没有这行，用户无法区分当前可用模型来源。 */}
          </header> {/* 新增代码+SettingsModelsPanel：分组标题行结束；如果没有这行，JSX 结构不完整。 */}
          <div className="settings-model-group-body"> {/* 新增代码+SettingsModelsPanel：渲染分组模型行容器；如果没有这层，行分隔和圆角无法控制。 */}
            {group.models.map((model) => renderModelRow(group, model, pendingModelKey, onToggleModel))} {/* 新增代码+SettingsModelsPanel：渲染当前 provider 的所有模型；如果没有这行，模型行不会显示。 */}
          </div> {/* 新增代码+SettingsModelsPanel：分组模型行容器结束；如果没有这行，JSX 结构不完整。 */}
        </section> // 新增代码+SettingsModelsPanel：单个 provider 分组结束；如果没有这行，JSX 结构不完整。
      ))} {/* 新增代码+SettingsModelsPanel：provider 模型分组遍历结束；如果没有这行，JSX 表达式不完整。 */}
    </div> // 新增代码+SettingsModelsPanel：模型列表容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+SettingsModelsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+SettingsModelsPanel：函数段结束，SettingsModelsPanel 到此结束；如果没有这个边界，用户不容易看出模型面板范围。
