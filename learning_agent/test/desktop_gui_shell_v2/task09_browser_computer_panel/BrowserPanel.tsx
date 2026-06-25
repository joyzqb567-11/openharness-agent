type BrowserPanelProps = { // 修改代码+DesktopRuntimePanels：定义浏览器运行时面板入参；如果没有这段，右侧页签无法同时兼容旧 provider 状态和 V2 面板 payload。
  providerStatus?: Record<string, unknown>; // 修改代码+DesktopRuntimePanels：保留旧 provider_status 兜底；如果没有这行，旧 bridge 或旧测试数据会直接显示为空。
  panel?: Record<string, unknown>; // 新增代码+DesktopRuntimePanels：接收 V2 runtime browser 面板；如果没有这行，active target、降级提示和 provider chips 无法进入界面。
}; // 修改代码+DesktopRuntimePanels：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 修改代码+DesktopRuntimePanels：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会让 Object.keys 或字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 修改代码+DesktopRuntimePanels：只接受普通对象，否则返回空对象；如果没有这行，前端会信任任意后端类型。
} // 修改代码+DesktopRuntimePanels：函数段结束，asRecord 到此结束；如果没有这个边界，初学者不容易看出类型防护范围。

function asText(value: unknown, fallback: string): string { // 新增代码+DesktopRuntimePanels：函数段开始，把任意字段变成安全短文本；如果没有这段，undefined/null 会直接暴露在 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopRuntimePanels：优先使用非空字符串，否则使用兜底文案；如果没有这行，面板会出现空白状态。
} // 新增代码+DesktopRuntimePanels：函数段结束，asText 到此结束；如果没有这个边界，文本清洗职责不清楚。

function providerNameLabel(name: string): string { // 修改代码+DesktopRuntimePanels：函数段开始，把 provider key 转成人类可读名称；如果没有这段，UI 会暴露难扫读的内部下划线名称。
  return name.replace(/_/g, " "); // 修改代码+DesktopRuntimePanels：把下划线替换成空格；如果没有这行，provider 名称会显得像内部字段。
} // 修改代码+DesktopRuntimePanels：函数段结束，providerNameLabel 到此结束；如果没有这个边界，名称格式化范围不清楚。

function statusLabel(provider: Record<string, unknown>): string { // 修改代码+DesktopRuntimePanels：函数段开始，生成 provider 可用状态文案；如果没有这段，用户只能从布尔值猜健康状态。
  return provider.available === true ? "可用" : "未连接"; // 修改代码+DesktopRuntimePanels：把 available 布尔值转成中文状态；如果没有这行，浏览器轨道状态不够直观。
} // 修改代码+DesktopRuntimePanels：函数段结束，statusLabel 到此结束；如果没有这个边界，状态格式化范围不清楚。

function providerReason(provider: Record<string, unknown>): string { // 新增代码+DesktopRuntimePanels：函数段开始，生成 provider 原因摘要；如果没有这段，失败原因会缺少稳定兜底。
  return asText(provider.reason, provider.available === true ? "ready" : "no reason"); // 新增代码+DesktopRuntimePanels：优先显示后端原因，缺失时按状态给出兜底；如果没有这行，provider 卡片会出现空原因。
} // 新增代码+DesktopRuntimePanels：函数段结束，providerReason 到此结束；如果没有这个边界，原因兜底逻辑不易定位。

export function BrowserPanel({ providerStatus = {}, panel = {} }: BrowserPanelProps): JSX.Element { // 修改代码+DesktopRuntimePanels：函数段开始，渲染浏览器 provider、active target 和降级状态；如果没有这段，用户看不到 Playwright/CDP/Extension 健康。
  const runtimePanel = asRecord(panel); // 新增代码+DesktopRuntimePanels：读取 V2 browser 面板对象；如果没有这行，后续无法从统一 endpoint 取数据。
  const legacyStatus = asRecord(providerStatus); // 修改代码+DesktopRuntimePanels：读取旧 provider 状态对象；如果没有这行，旧 payload 无法作为兜底。
  const providers = asRecord(runtimePanel.providers ?? legacyStatus.providers); // 修改代码+DesktopRuntimePanels：优先使用 V2 providers，再兜底旧 providers；如果没有这行，provider chips 没有数据来源。
  const providerNames = Object.keys(providers); // 修改代码+DesktopRuntimePanels：提取 provider 名称列表；如果没有这行，后续无法 map 渲染条目。
  const extension = asRecord(runtimePanel.extension ?? legacyStatus.chrome_extension); // 修改代码+DesktopRuntimePanels：读取 Chrome 扩展状态；如果没有这行，扩展连接和命令队列摘要无法显示。
  const tabs = asRecord(runtimePanel.tabs ?? legacyStatus.tabs); // 修改代码+DesktopRuntimePanels：读取标签页状态；如果没有这行，面板无法显示当前 tab 数量。
  const activeTarget = asRecord(runtimePanel.active_target); // 新增代码+DesktopRuntimePanels：读取当前活跃目标摘要；如果没有这行，用户不知道浏览器正在指向哪个页面。
  const degraded = runtimePanel.status_degraded === true || legacyStatus.status_degraded === true; // 新增代码+DesktopRuntimePanels：计算浏览器面板是否降级；如果没有这行，后端快照失败时 UI 会假装一切正常。
  const safeError = asText(runtimePanel.safe_error ?? legacyStatus.safe_error, "浏览器状态暂时不可读。"); // 新增代码+DesktopRuntimePanels：读取安全错误文案；如果没有这行，降级提示可能泄露原始异常。
  const pendingCommandCount = Number(extension.pending_command_count ?? 0); // 修改代码+DesktopRuntimePanels：读取待执行命令数量；如果没有这行，插件卡住时用户看不到队列迹象。
  const tabCount = Number(tabs.tab_count ?? 0); // 修改代码+DesktopRuntimePanels：读取 tab 数量；如果没有这行，浏览器连接是否有页面上下文不直观。
  const activeTitle = asText(activeTarget.title, "暂无活跃目标"); // 新增代码+DesktopRuntimePanels：读取活跃页面标题；如果没有这行，active target 区域会缺少主信息。
  const activeHost = asText(activeTarget.host, asText(activeTarget.url, "未提供地址")); // 新增代码+DesktopRuntimePanels：读取活跃页面主机或地址；如果没有这行，用户无法判断页面来源。
  const activeKind = asText(activeTarget.kind, "browser_target"); // 新增代码+DesktopRuntimePanels：读取目标类型；如果没有这行，多浏览器目标难以区分。
  return ( // 修改代码+DesktopRuntimePanels：返回浏览器状态面板结构；如果没有这行，组件不会输出 UI。
    <section className="browser-panel" aria-label="浏览器状态"> {/* 修改代码+DesktopRuntimePanels：定义浏览器状态区域；如果没有这行，右侧栏缺少浏览器 provider 分区。 */}
      <div className="browser-panel-header"> {/* 修改代码+DesktopRuntimePanels：定义面板标题区；如果没有这行，浏览器状态和事件列表层级会混在一起。 */}
        <h2>浏览器</h2> {/* 修改代码+DesktopRuntimePanels：显示浏览器面板标题；如果没有这行，用户不知道这块状态的用途。 */}
        <span>{tabCount} tabs</span> {/* 修改代码+DesktopRuntimePanels：显示 tab 数量摘要；如果没有这行，用户要展开状态才知道页面上下文规模。 */}
      </div> {/* 修改代码+DesktopRuntimePanels：面板标题区结束；如果没有这行，JSX 结构不完整。 */}
      {degraded ? <p className="browser-runtime-alert">{safeError}</p> : null} {/* 新增代码+DesktopRuntimePanels：显示安全降级提示；如果没有这行，后端不可读时用户看不到可信状态。 */}
      <div className="browser-provider-chips" aria-label="浏览器 provider 轨道"> {/* 新增代码+DesktopRuntimePanels：定义 provider chips 容器；如果没有这行，三条浏览器轨道缺少紧凑扫描布局。 */}
        {providerNames.length === 0 ? ( // 修改代码+DesktopRuntimePanels：处理无 provider 状态；如果没有这行，空状态会显示成空白区域。
          <p className="browser-empty">暂无 provider 状态。</p> // 修改代码+DesktopRuntimePanels：显示 provider 空状态；如果没有这行，用户不知道是未连接还是未加载。
        ) : ( // 修改代码+DesktopRuntimePanels：处理有 provider 状态；如果没有这行，条件渲染语法不完整。
          providerNames.map((name) => { // 修改代码+DesktopRuntimePanels：遍历 provider 名称；如果没有这行，各浏览器轨道不会渲染出来。
            const provider = asRecord(providers[name]); // 修改代码+DesktopRuntimePanels：读取当前 provider 状态；如果没有这行，条目无法显示 available/reason。
            const available = provider.available === true; // 修改代码+DesktopRuntimePanels：计算可用状态；如果没有这行，样式无法区分在线和未连接。
            return ( // 修改代码+DesktopRuntimePanels：返回单个 provider chip；如果没有这行，map 不会生成 JSX。
              <div className={`browser-provider-chip ${available ? "browser-provider-ready" : "browser-provider-muted"}`} key={name}> {/* 修改代码+DesktopRuntimePanels：渲染 provider chip；如果没有这行，用户看不到单条浏览器轨道。 */}
                <span>{providerNameLabel(name)}</span> {/* 修改代码+DesktopRuntimePanels：显示 provider 名称；如果没有这行，用户不知道是哪条浏览器轨道。 */}
                <strong>{statusLabel(provider)}</strong> {/* 修改代码+DesktopRuntimePanels：显示 provider 可用状态；如果没有这行，用户只能猜当前轨道是否可用。 */}
                <small>{providerReason(provider)}</small> {/* 修改代码+DesktopRuntimePanels：显示 provider 原因；如果没有这行，未连接时缺少下一步诊断线索。 */}
              </div> // 修改代码+DesktopRuntimePanels：单个 provider chip 结束；如果没有这行，JSX 结构不完整。
            ); // 修改代码+DesktopRuntimePanels：单个 provider 返回结束；如果没有这行，map 回调语法不完整。
          }) // 修改代码+DesktopRuntimePanels：provider 遍历结束；如果没有这行，JSX 表达式不完整。
        )} {/* 修改代码+DesktopRuntimePanels：provider 条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopRuntimePanels：provider chips 容器结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-active-target"> {/* 新增代码+DesktopRuntimePanels：定义活跃目标摘要区；如果没有这行，用户看不到当前浏览器目标。 */}
        <strong>{activeTitle}</strong> {/* 新增代码+DesktopRuntimePanels：显示活跃目标标题；如果没有这行，目标摘要缺少主标题。 */}
        <span>{activeHost}</span> {/* 新增代码+DesktopRuntimePanels：显示活跃目标地址或主机；如果没有这行，用户难以确认页面来源。 */}
        <small>{activeKind}</small> {/* 新增代码+DesktopRuntimePanels：显示目标类型；如果没有这行，多种 browser target 难以区分。 */}
      </div> {/* 新增代码+DesktopRuntimePanels：活跃目标摘要区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="browser-provider-summary"> {/* 修改代码+DesktopRuntimePanels：定义浏览器 provider 摘要；如果没有这行，扩展队列和连接状态没有固定位置。 */}
        <span>扩展连接：{extension.connected === true ? "已连接" : "未连接"}</span> {/* 修改代码+DesktopRuntimePanels：显示扩展连接状态；如果没有这行，Chrome Extension 轨道是否在线不明显。 */}
        <span>待执行命令：{pendingCommandCount}</span> {/* 修改代码+DesktopRuntimePanels：显示待执行命令数量；如果没有这行，命令堆积时缺少可见告警。 */}
      </div> {/* 修改代码+DesktopRuntimePanels：provider 摘要结束；如果没有这行，JSX 结构不完整。 */}
    </section> // 修改代码+DesktopRuntimePanels：浏览器状态区域结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopRuntimePanels：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopRuntimePanels：函数段结束，BrowserPanel 到此结束；如果没有这个边界，初学者不容易看出面板范围。
