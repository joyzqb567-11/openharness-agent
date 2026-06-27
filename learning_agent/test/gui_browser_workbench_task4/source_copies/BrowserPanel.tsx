import { ExternalLink, RefreshCw } from "lucide-react"; // 新增代码+DesktopGUIBrowserWorkbench：引入打开和刷新图标；如果没有这行，浏览器工作台按钮会缺少可扫描符号。
import { useState } from "react"; // 新增代码+DesktopGUIBrowserWorkbench：引入本地输入状态；如果没有这行，URL 输入框无法受控保存用户输入。

type BrowserPanelProps = { // 修改代码+DesktopGUIBrowserWorkbench：定义浏览器工作台入参；如果没有这段，右侧页签无法同时接收状态、按钮和最近结果。
  providerStatus?: Record<string, unknown>; // 修改代码+DesktopGUIBrowserWorkbench：保留旧 provider_status 兜底；如果没有这行，旧 bridge 或旧测试数据会直接显示为空。
  panel?: Record<string, unknown>; // 修改代码+DesktopGUIBrowserWorkbench：接收 V2 runtime browser/workbench 面板；如果没有这行，tabs、console、network 和 replay 无法进入界面。
  onOpenUrl?: (url: string) => void; // 新增代码+DesktopGUIBrowserWorkbench：接收记录打开 URL 的回调；如果没有这行，记录打开按钮不能调用后端。
  onRefreshStatus?: () => void; // 新增代码+DesktopGUIBrowserWorkbench：接收刷新 Browser 状态的回调；如果没有这行，刷新按钮只能是装饰。
  actionPending?: boolean; // 新增代码+DesktopGUIBrowserWorkbench：保存按钮等待态；如果没有这行，用户可能重复提交刷新或打开请求。
  lastActionResult?: Record<string, unknown>; // 新增代码+DesktopGUIBrowserWorkbench：保存最近 Browser 动作结果；如果没有这行，按钮点击后缺少可见反馈。
}; // 修改代码+DesktopGUIBrowserWorkbench：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会让字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 修改代码+DesktopGUIBrowserWorkbench：只接受普通对象，否则返回空对象；如果没有这行，前端会信任任意后端类型。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，asRecord 到此结束；如果没有这个边界，类型防护范围不清楚。

function asText(value: unknown, fallback: string): string { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，把任意字段变成安全短文本；如果没有这段，undefined/null 会直接暴露在 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 修改代码+DesktopGUIBrowserWorkbench：优先使用非空字符串，否则使用兜底文案；如果没有这行，面板会出现空白状态。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，asText 到此结束；如果没有这个边界，文本清洗职责不清楚。

function asNumber(value: unknown, fallback = 0): number { // 新增代码+DesktopGUIBrowserWorkbench：函数段开始，把后端计数字段收敛成数字；如果没有这段，坏 count 会在 UI 显示 NaN。
  const parsed = Number(value); // 新增代码+DesktopGUIBrowserWorkbench：尝试用浏览器数字转换；如果没有这行，字符串数字无法被正常展示。
  return Number.isFinite(parsed) ? parsed : fallback; // 新增代码+DesktopGUIBrowserWorkbench：合法数字直接返回，否则兜底；如果没有这行，Infinity 或 NaN 会进入界面。
} // 新增代码+DesktopGUIBrowserWorkbench：函数段结束，asNumber 到此结束；如果没有这个边界，数字防护范围不清楚。

function providerNameLabel(name: string): string { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，把 provider key 转成人类可读名称；如果没有这段，UI 会暴露难扫读的内部下划线名称。
  return name.replace(/_/g, " "); // 修改代码+DesktopGUIBrowserWorkbench：把下划线替换成空格；如果没有这行，provider 名称会显得像内部字段。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，providerNameLabel 到此结束；如果没有这个边界，名称格式化范围不清楚。

function statusLabel(provider: Record<string, unknown>): string { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，生成 provider 可用状态文案；如果没有这段，用户只能从布尔值猜健康状态。
  return provider.available === true ? "可用" : "未连接"; // 修改代码+DesktopGUIBrowserWorkbench：把 available 布尔值转成中文状态；如果没有这行，浏览器轨道状态不够直观。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，statusLabel 到此结束；如果没有这个边界，状态格式化范围不清楚。

function providerReason(provider: Record<string, unknown>): string { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，生成 provider 原因摘要；如果没有这段，失败原因会缺少稳定兜底。
  return asText(provider.reason, provider.available === true ? "ready" : "no reason"); // 修改代码+DesktopGUIBrowserWorkbench：优先显示后端原因，缺失时按状态给出兜底；如果没有这行，provider 卡片会出现空原因。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，providerReason 到此结束；如果没有这个边界，原因兜底逻辑不易定位。

function debugMessage(summary: Record<string, unknown>, fallback: string): string { // 新增代码+DesktopGUIBrowserWorkbench：函数段开始，提取调试摘要主文案；如果没有这段，Console/Network/Downloads 卡片会重复兜底逻辑。
  return asText(summary.latest_message ?? summary.message, fallback); // 新增代码+DesktopGUIBrowserWorkbench：优先显示后端最新消息，否则用空态；如果没有这行，调试卡片可能空白。
} // 新增代码+DesktopGUIBrowserWorkbench：函数段结束，debugMessage 到此结束；如果没有这个边界，调试文案来源不清楚。

function debugMeta(summary: Record<string, unknown>, unitLabel: string): string { // 新增代码+DesktopGUIBrowserWorkbench：函数段开始，生成调试卡片数量摘要；如果没有这段，错误数和条目数会重复拼接。
  const entryCount = asNumber(summary.entry_count); // 新增代码+DesktopGUIBrowserWorkbench：读取条目数；如果没有这行，用户不知道摘要覆盖了多少记录。
  const errorCount = asNumber(summary.error_count); // 新增代码+DesktopGUIBrowserWorkbench：读取错误数；如果没有这行，用户无法快速看到异常规模。
  return `${entryCount} ${unitLabel} · ${errorCount} errors`; // 新增代码+DesktopGUIBrowserWorkbench：返回紧凑元信息；如果没有这行，卡片缺少可扫描指标。
} // 新增代码+DesktopGUIBrowserWorkbench：函数段结束，debugMeta 到此结束；如果没有这个边界，数量摘要范围不清楚。

export function BrowserPanel({ providerStatus = {}, panel = {}, onOpenUrl, onRefreshStatus, actionPending = false, lastActionResult = {} }: BrowserPanelProps): JSX.Element { // 修改代码+DesktopGUIBrowserWorkbench：函数段开始，渲染 Browser provider、控制按钮和调试摘要；如果没有这段，用户看不到浏览器工具链控制中心。
  const [urlInput, setUrlInput] = useState("https://example.com"); // 新增代码+DesktopGUIBrowserWorkbench：保存打开请求输入框内容；如果没有这行，输入框无法稳定编辑。
  const runtimePanel = asRecord(panel); // 修改代码+DesktopGUIBrowserWorkbench：读取 V2 browser 面板对象；如果没有这行，后续无法从统一 endpoint 取数据。
  const legacyStatus = asRecord(providerStatus); // 修改代码+DesktopGUIBrowserWorkbench：读取旧 provider 状态对象；如果没有这行，旧 payload 无法作为兜底。
  const providers = asRecord(runtimePanel.providers ?? legacyStatus.providers); // 修改代码+DesktopGUIBrowserWorkbench：优先使用 V2 providers，再兜底旧 providers；如果没有这行，provider chips 没有数据来源。
  const providerNames = Object.keys(providers); // 修改代码+DesktopGUIBrowserWorkbench：提取 provider 名称列表；如果没有这行，后续无法 map 渲染条目。
  const extension = asRecord(runtimePanel.extension ?? legacyStatus.chrome_extension); // 修改代码+DesktopGUIBrowserWorkbench：读取 Chrome 扩展状态；如果没有这行，扩展连接和命令队列摘要无法显示。
  const nativeHost = asRecord(runtimePanel.native_host ?? legacyStatus.native_host); // 新增代码+DesktopGUIBrowserWorkbench：读取 native host 状态；如果没有这行，用户无法区分扩展与 native host 连接问题。
  const tabs = asRecord(runtimePanel.tabs ?? legacyStatus.tabs); // 修改代码+DesktopGUIBrowserWorkbench：读取标签页状态；如果没有这行，面板无法显示当前 tab 数量。
  const tabList = Array.isArray(tabs.tabs) ? tabs.tabs.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null && !Array.isArray(item)) : []; // 新增代码+DesktopGUIBrowserWorkbench：收敛可显示 tab 列表；如果没有这行，坏 tabs 数据会拖垮渲染。
  const activeTarget = asRecord(runtimePanel.active_target); // 修改代码+DesktopGUIBrowserWorkbench：读取当前活跃目标摘要；如果没有这行，用户不知道浏览器正在指向哪个页面。
  const consoleSummary = asRecord(runtimePanel.console); // 新增代码+DesktopGUIBrowserWorkbench：读取 Console 摘要；如果没有这行，console 错误无法进入面板。
  const networkSummary = asRecord(runtimePanel.network); // 新增代码+DesktopGUIBrowserWorkbench：读取 Network 摘要；如果没有这行，网络错误无法进入面板。
  const downloadsSummary = asRecord(runtimePanel.downloads); // 新增代码+DesktopGUIBrowserWorkbench：读取 Downloads 摘要；如果没有这行，下载记录无法进入面板。
  const recordings = asRecord(runtimePanel.recordings); // 新增代码+DesktopGUIBrowserWorkbench：读取录制证据摘要；如果没有这行，视觉回放证据不可见。
  const replay = asRecord(runtimePanel.replay); // 新增代码+DesktopGUIBrowserWorkbench：读取 replay 能力边界；如果没有这行，用户不知道回放是否会真实操作网页。
  const actionResult = asRecord(lastActionResult); // 新增代码+DesktopGUIBrowserWorkbench：读取最近按钮结果；如果没有这行，点击反馈无法展示。
  const degraded = runtimePanel.status_degraded === true || legacyStatus.status_degraded === true; // 修改代码+DesktopGUIBrowserWorkbench：计算浏览器面板是否降级；如果没有这行，后端快照失败时 UI 会假装一切正常。
  const safeError = asText(runtimePanel.safe_error ?? legacyStatus.safe_error, "浏览器状态暂时不可读。"); // 修改代码+DesktopGUIBrowserWorkbench：读取安全错误文案；如果没有这行，降级提示可能泄露原始异常。
  const pendingCommandCount = asNumber(extension.pending_command_count); // 修改代码+DesktopGUIBrowserWorkbench：读取待执行命令数量；如果没有这行，插件卡住时用户看不到队列迹象。
  const tabCount = asNumber(tabs.tab_count); // 修改代码+DesktopGUIBrowserWorkbench：读取 tab 数量；如果没有这行，浏览器连接是否有页面上下文不直观。
  const recordingCount = asNumber(recordings.recording_count); // 新增代码+DesktopGUIBrowserWorkbench：读取录制数量；如果没有这行，回放证据规模不可见。
  const activeTitle = asText(activeTarget.title, "暂无活跃目标"); // 修改代码+DesktopGUIBrowserWorkbench：读取活跃页面标题；如果没有这行，active target 区域会缺少主信息。
  const activeHost = asText(activeTarget.host, asText(activeTarget.url, "未提供地址")); // 修改代码+DesktopGUIBrowserWorkbench：读取活跃页面主机或地址；如果没有这行，用户无法判断页面来源。
  const activeKind = asText(activeTarget.kind, "browser_target"); // 修改代码+DesktopGUIBrowserWorkbench：读取目标类型；如果没有这行，多浏览器目标难以区分。
  const replayMode = asText(replay.mode, replay.available === true ? "available" : "unavailable"); // 新增代码+DesktopGUIBrowserWorkbench：读取 replay 模式；如果没有这行，dry_run_only 边界不可见。
  const replayReason = asText(replay.reason, "未提供 replay 说明。"); // 新增代码+DesktopGUIBrowserWorkbench：读取 replay 原因说明；如果没有这行，用户不知道回放能力来源。
  const canOpenUrl = Boolean(onOpenUrl) && urlInput.trim().length > 0 && !actionPending; // 新增代码+DesktopGUIBrowserWorkbench：计算记录打开按钮是否可点；如果没有这行，空 URL 或等待态可能重复提交。
  const actionMessage = asText(actionResult.message, ""); // 新增代码+DesktopGUIBrowserWorkbench：读取最近动作消息；如果没有这行，结果卡片无法判断是否显示。
  function handleOpenClick(): void { // 新增代码+DesktopGUIBrowserWorkbench：函数段开始，处理记录打开按钮；如果没有这段，URL 输入不会提交到父组件。
    const trimmedUrl = urlInput.trim(); // 新增代码+DesktopGUIBrowserWorkbench：清理 URL 输入；如果没有这行，前后空格会进入后端。
    if (trimmedUrl.length === 0 || onOpenUrl === undefined) { // 新增代码+DesktopGUIBrowserWorkbench：拦截空 URL 或未接回调；如果没有这行，按钮可能触发无效请求。
      return; // 新增代码+DesktopGUIBrowserWorkbench：无效输入直接退出；如果没有这行，后续会调用不存在的回调。
    } // 新增代码+DesktopGUIBrowserWorkbench：无效输入判断结束；如果没有这行，条件块语法不完整。
    onOpenUrl(trimmedUrl); // 新增代码+DesktopGUIBrowserWorkbench：把 URL 交给父组件调用 bridge；如果没有这行，记录打开按钮没有真实效果。
  } // 新增代码+DesktopGUIBrowserWorkbench：函数段结束，handleOpenClick 到此结束；如果没有这个边界，按钮处理范围不清楚。
  return ( // 修改代码+DesktopGUIBrowserWorkbench：返回浏览器工作台结构；如果没有这行，组件不会输出 UI。
    <section className="browser-panel" aria-label="浏览器状态"> {/* 修改代码+DesktopGUIBrowserWorkbench：定义浏览器工作台区域；如果没有这行，右侧栏缺少 Browser 分区。 */}
      <div className="browser-panel-header"> {/* 修改代码+DesktopGUIBrowserWorkbench：定义面板标题区；如果没有这行，浏览器状态和调试摘要层级会混在一起。 */}
        <h2>浏览器</h2> {/* 修改代码+DesktopGUIBrowserWorkbench：显示浏览器面板标题；如果没有这行，用户不知道这块状态的用途。 */}
        <span>{tabCount} tabs</span> {/* 修改代码+DesktopGUIBrowserWorkbench：显示 tab 数量摘要；如果没有这行，用户要展开状态才知道页面上下文规模。 */}
      </div> {/* 修改代码+DesktopGUIBrowserWorkbench：面板标题区结束；如果没有这行，JSX 结构不完整。 */}
      {degraded ? <p className="browser-runtime-alert">{safeError}</p> : null} {/* 修改代码+DesktopGUIBrowserWorkbench：显示安全降级提示；如果没有这行，后端不可读时用户看不到可信状态。 */}
      <div className="browser-provider-chips" aria-label="浏览器 provider 轨道"> {/* 修改代码+DesktopGUIBrowserWorkbench：定义 provider chips 容器；如果没有这行，三条浏览器轨道缺少紧凑扫描布局。 */}
        {providerNames.length === 0 ? ( // 修改代码+DesktopGUIBrowserWorkbench：处理无 provider 状态；如果没有这行，空状态会显示成空白区域。
          <p className="browser-empty">暂无 provider 状态。</p> // 修改代码+DesktopGUIBrowserWorkbench：显示 provider 空状态；如果没有这行，用户不知道是未连接还是未加载。
        ) : ( // 修改代码+DesktopGUIBrowserWorkbench：处理有 provider 状态；如果没有这行，条件渲染语法不完整。
          providerNames.map((name) => { // 修改代码+DesktopGUIBrowserWorkbench：遍历 provider 名称；如果没有这行，各浏览器轨道不会渲染出来。
            const provider = asRecord(providers[name]); // 修改代码+DesktopGUIBrowserWorkbench：读取当前 provider 状态；如果没有这行，条目无法显示 available/reason。
            const available = provider.available === true; // 修改代码+DesktopGUIBrowserWorkbench：计算可用状态；如果没有这行，样式无法区分在线和未连接。
            return ( // 修改代码+DesktopGUIBrowserWorkbench：返回单个 provider chip；如果没有这行，map 不会生成 JSX。
              <div className={`browser-provider-chip ${available ? "browser-provider-ready" : "browser-provider-muted"}`} key={name}> {/* 修改代码+DesktopGUIBrowserWorkbench：渲染 provider chip；如果没有这行，用户看不到单条浏览器轨道。 */}
                <span>{providerNameLabel(name)}</span> {/* 修改代码+DesktopGUIBrowserWorkbench：显示 provider 名称；如果没有这行，用户不知道是哪条浏览器轨道。 */}
                <strong>{statusLabel(provider)}</strong> {/* 修改代码+DesktopGUIBrowserWorkbench：显示 provider 可用状态；如果没有这行，用户只能猜当前轨道是否可用。 */}
                <small>{providerReason(provider)}</small> {/* 修改代码+DesktopGUIBrowserWorkbench：显示 provider 原因；如果没有这行，未连接时缺少下一步诊断线索。 */}
              </div> // 修改代码+DesktopGUIBrowserWorkbench：单个 provider chip 结束；如果没有这行，JSX 结构不完整。
            ); // 修改代码+DesktopGUIBrowserWorkbench：单个 provider 返回结束；如果没有这行，map 回调语法不完整。
          }) // 修改代码+DesktopGUIBrowserWorkbench：provider 遍历结束；如果没有这行，JSX 表达式不完整。
        )} {/* 修改代码+DesktopGUIBrowserWorkbench：provider 条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 修改代码+DesktopGUIBrowserWorkbench：provider chips 容器结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-active-target"> {/* 修改代码+DesktopGUIBrowserWorkbench：定义活跃目标摘要区；如果没有这行，用户看不到当前浏览器目标。 */}
        <strong>{activeTitle}</strong> {/* 修改代码+DesktopGUIBrowserWorkbench：显示活跃目标标题；如果没有这行，目标摘要缺少主标题。 */}
        <span>{activeHost}</span> {/* 修改代码+DesktopGUIBrowserWorkbench：显示活跃目标地址或主机；如果没有这行，用户难以确认页面来源。 */}
        <small>{activeKind}</small> {/* 修改代码+DesktopGUIBrowserWorkbench：显示目标类型；如果没有这行，多种 browser target 难以区分。 */}
      </div> {/* 修改代码+DesktopGUIBrowserWorkbench：活跃目标摘要区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-workbench-controls"> {/* 新增代码+DesktopGUIBrowserWorkbench：定义 Browser 控制区；如果没有这行，刷新和记录打开入口没有稳定布局。 */}
        <button className="browser-workbench-button" type="button" title="刷新 Browser 状态" onClick={onRefreshStatus} disabled={onRefreshStatus === undefined || actionPending}> {/* 新增代码+DesktopGUIBrowserWorkbench：刷新按钮；如果没有这行，用户无法从 GUI 主动读取最新状态。 */}
          <RefreshCw size={13} aria-hidden="true" /> {/* 新增代码+DesktopGUIBrowserWorkbench：刷新图标；如果没有这行，按钮扫描性下降。 */}
          <span>{actionPending ? "处理中" : "刷新"}</span> {/* 新增代码+DesktopGUIBrowserWorkbench：刷新按钮文字；如果没有这行，图标含义不够明确。 */}
        </button> {/* 新增代码+DesktopGUIBrowserWorkbench：刷新按钮结束；如果没有这行，JSX 结构不完整。 */}
        <div className="browser-open-row"> {/* 新增代码+DesktopGUIBrowserWorkbench：定义 URL 输入和打开按钮行；如果没有这行，输入框和按钮会错位。 */}
          <input className="browser-url-input" aria-label="浏览器 URL" value={urlInput} onChange={(event) => setUrlInput(event.target.value)} placeholder="https://example.com" /> {/* 新增代码+DesktopGUIBrowserWorkbench：URL 输入框；如果没有这行，用户无法指定要记录的目标地址。 */}
          <button className="browser-workbench-button" type="button" title="记录打开 URL 请求" onClick={handleOpenClick} disabled={!canOpenUrl}> {/* 新增代码+DesktopGUIBrowserWorkbench：记录打开按钮；如果没有这行，open 请求无法进入后端审计流。 */}
            <ExternalLink size={13} aria-hidden="true" /> {/* 新增代码+DesktopGUIBrowserWorkbench：打开图标；如果没有这行，按钮扫描性下降。 */}
            <span>记录打开</span> {/* 新增代码+DesktopGUIBrowserWorkbench：打开按钮文字；如果没有这行，图标含义不够明确。 */}
          </button> {/* 新增代码+DesktopGUIBrowserWorkbench：记录打开按钮结束；如果没有这行，JSX 结构不完整。 */}
        </div> {/* 新增代码+DesktopGUIBrowserWorkbench：URL 输入和按钮行结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopGUIBrowserWorkbench：Browser 控制区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-provider-summary"> {/* 修改代码+DesktopGUIBrowserWorkbench：定义浏览器 provider 摘要；如果没有这行，扩展队列和连接状态没有固定位置。 */}
        <span>扩展连接：{extension.connected === true ? "已连接" : "未连接"}</span> {/* 修改代码+DesktopGUIBrowserWorkbench：显示扩展连接状态；如果没有这行，Chrome Extension 轨道是否在线不明显。 */}
        <span>Native Host：{nativeHost.connected === true ? "已连接" : "未连接"}</span> {/* 新增代码+DesktopGUIBrowserWorkbench：显示 native host 连接状态；如果没有这行，用户无法判断本地桥接是否在线。 */}
        <span>待执行命令：{pendingCommandCount}</span> {/* 修改代码+DesktopGUIBrowserWorkbench：显示待执行命令数量；如果没有这行，命令堆积时缺少可见告警。 */}
      </div> {/* 修改代码+DesktopGUIBrowserWorkbench：provider 摘要结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-debug-grid" aria-label="浏览器调试摘要"> {/* 新增代码+DesktopGUIBrowserWorkbench：定义调试摘要网格；如果没有这行，console/network/downloads/replay 会散乱。 */}
        <article className="browser-debug-card"> {/* 新增代码+DesktopGUIBrowserWorkbench：Console 调试卡片；如果没有这行，console 摘要没有视觉容器。 */}
          <h3>Console</h3> {/* 新增代码+DesktopGUIBrowserWorkbench：Console 标题；如果没有这行，用户不知道卡片来源。 */}
          <strong>{debugMessage(consoleSummary, "最近没有捕获到 console 输出。")}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：Console 最新消息；如果没有这行，错误线索不可见。 */}
          <small>{debugMeta(consoleSummary, "entries")}</small> {/* 新增代码+DesktopGUIBrowserWorkbench：Console 数量摘要；如果没有这行，错误规模不可见。 */}
        </article> {/* 新增代码+DesktopGUIBrowserWorkbench：Console 调试卡片结束；如果没有这行，JSX 结构不完整。 */}
        <article className="browser-debug-card"> {/* 新增代码+DesktopGUIBrowserWorkbench：Network 调试卡片；如果没有这行，network 摘要没有视觉容器。 */}
          <h3>Network</h3> {/* 新增代码+DesktopGUIBrowserWorkbench：Network 标题；如果没有这行，用户不知道卡片来源。 */}
          <strong>{debugMessage(networkSummary, "最近没有捕获到网络请求或响应。")}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：Network 最新消息；如果没有这行，网络错误线索不可见。 */}
          <small>{debugMeta(networkSummary, "records")}</small> {/* 新增代码+DesktopGUIBrowserWorkbench：Network 数量摘要；如果没有这行，网络记录规模不可见。 */}
        </article> {/* 新增代码+DesktopGUIBrowserWorkbench：Network 调试卡片结束；如果没有这行，JSX 结构不完整。 */}
        <article className="browser-debug-card"> {/* 新增代码+DesktopGUIBrowserWorkbench：Downloads 调试卡片；如果没有这行，下载摘要没有视觉容器。 */}
          <h3>Downloads</h3> {/* 新增代码+DesktopGUIBrowserWorkbench：Downloads 标题；如果没有这行，用户不知道卡片来源。 */}
          <strong>{debugMessage(downloadsSummary, "最近没有捕获到下载。")}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：Downloads 最新消息；如果没有这行，下载记录不可见。 */}
          <small>{debugMeta(downloadsSummary, "records")}</small> {/* 新增代码+DesktopGUIBrowserWorkbench：Downloads 数量摘要；如果没有这行，下载规模不可见。 */}
        </article> {/* 新增代码+DesktopGUIBrowserWorkbench：Downloads 调试卡片结束；如果没有这行，JSX 结构不完整。 */}
        <article className="browser-debug-card"> {/* 新增代码+DesktopGUIBrowserWorkbench：Replay 调试卡片；如果没有这行，回放能力没有视觉容器。 */}
          <h3>Replay</h3> {/* 新增代码+DesktopGUIBrowserWorkbench：Replay 标题；如果没有这行，用户不知道卡片来源。 */}
          <strong>{replayMode}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：Replay 模式；如果没有这行，dry_run_only 边界不可见。 */}
          <small>{recordingCount} recordings · {replayReason}</small> {/* 新增代码+DesktopGUIBrowserWorkbench：录制数量和 replay 原因；如果没有这行，证据链和安全边界不可见。 */}
        </article> {/* 新增代码+DesktopGUIBrowserWorkbench：Replay 调试卡片结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopGUIBrowserWorkbench：调试摘要网格结束；如果没有这行，JSX 结构不完整。 */}
      {tabList.length > 0 ? ( // 新增代码+DesktopGUIBrowserWorkbench：仅在有 tab 列表时显示标签页列表；如果没有这行，空列表会占空间。
        <div className="browser-tab-list" aria-label="最近浏览器标签页"> {/* 新增代码+DesktopGUIBrowserWorkbench：定义 tab 列表容器；如果没有这行，用户看不到当前页面集合。 */}
          {tabList.slice(0, 3).map((tab, index) => ( // 新增代码+DesktopGUIBrowserWorkbench：只显示前三个 tab 防止右栏过长；如果没有这行，大量 tab 会淹没面板。
            <div className="browser-tab-item" key={`${asText(tab.page_id, "tab")}_${index}`}> {/* 新增代码+DesktopGUIBrowserWorkbench：渲染单个 tab 条目；如果没有这行，tab 数据不会进入 UI。 */}
              <strong>{asText(tab.title, "Untitled")}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：显示 tab 标题；如果没有这行，用户无法识别页面。 */}
              <span>{asText(tab.url, "未提供地址")}</span> {/* 新增代码+DesktopGUIBrowserWorkbench：显示 tab 地址；如果没有这行，页面来源不可见。 */}
            </div> // 新增代码+DesktopGUIBrowserWorkbench：单个 tab 条目结束；如果没有这行，JSX 结构不完整。
          ))} {/* 新增代码+DesktopGUIBrowserWorkbench：tab 列表遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </div> // 新增代码+DesktopGUIBrowserWorkbench：tab 列表容器结束；如果没有这行，JSX 结构不完整。
      ) : null} {/* 新增代码+DesktopGUIBrowserWorkbench：tab 列表条件结束；如果没有这行，JSX 表达式不完整。 */}
      {actionMessage.length > 0 ? ( // 新增代码+DesktopGUIBrowserWorkbench：仅在有最近动作时显示反馈；如果没有这行，空反馈卡会干扰扫描。
        <div className="browser-action-result" role="status"> {/* 新增代码+DesktopGUIBrowserWorkbench：定义最近动作反馈区；如果没有这行，按钮结果没有肉眼可见位置。 */}
          <strong>{asText(actionResult.action, "browser")} · {asText(actionResult.status, "unknown")}</strong> {/* 新增代码+DesktopGUIBrowserWorkbench：显示动作和状态；如果没有这行，用户不知道执行了哪个按钮。 */}
          <span>{actionMessage}</span> {/* 新增代码+DesktopGUIBrowserWorkbench：显示后端反馈消息；如果没有这行，成功或失败原因不可见。 */}
        </div> // 新增代码+DesktopGUIBrowserWorkbench：最近动作反馈区结束；如果没有这行，JSX 结构不完整。
      ) : null} {/* 新增代码+DesktopGUIBrowserWorkbench：最近动作条件结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 修改代码+DesktopGUIBrowserWorkbench：浏览器工作台区域结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUIBrowserWorkbench：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUIBrowserWorkbench：函数段结束，BrowserPanel 到此结束；如果没有这个边界，浏览器工作台范围不清楚。
