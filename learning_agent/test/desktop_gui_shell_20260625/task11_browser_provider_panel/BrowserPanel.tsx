type BrowserPanelProps = { // 新增代码+DesktopGUIBrowserPanel：定义浏览器面板 props；如果没有这段，调用方不知道要传入哪类 provider 状态。
  providerStatus: Record<string, unknown>; // 新增代码+DesktopGUIBrowserPanel：保存后端 provider_status 对象；如果没有这行，面板没有浏览器状态来源。
}; // 新增代码+DesktopGUIBrowserPanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIBrowserPanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏状态会让 Object.keys 或字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIBrowserPanel：只接受普通对象并兜底空对象；如果没有这行，前端会直接信任后端任意类型。
} // 新增代码+DesktopGUIBrowserPanel：函数段结束，asRecord 到此结束；如果没有这个边界，初学者不容易看出类型收敛范围。

function providerNameLabel(name: string): string { // 新增代码+DesktopGUIBrowserPanel：函数段开始，把 provider key 转成人类可读名；如果没有这段，UI 会暴露难扫读的内部下划线名称。
  return name.replace(/_/g, " "); // 新增代码+DesktopGUIBrowserPanel：把下划线替换为空格；如果没有这行，provider 名称会显得像内部字段。
} // 新增代码+DesktopGUIBrowserPanel：函数段结束，providerNameLabel 到此结束；如果没有这个边界，初学者不容易看出名称格式化范围。

function statusLabel(provider: Record<string, unknown>): string { // 新增代码+DesktopGUIBrowserPanel：函数段开始，生成 provider 可用状态文案；如果没有这段，用户只能从布尔值猜健康状态。
  return provider.available === true ? "可用" : "未连接"; // 新增代码+DesktopGUIBrowserPanel：把 available 布尔值转成中文状态；如果没有这行，浏览器轨道状态不够直观。
} // 新增代码+DesktopGUIBrowserPanel：函数段结束，statusLabel 到此结束；如果没有这个边界，初学者不容易看出状态格式化范围。

export function BrowserPanel({ providerStatus }: BrowserPanelProps): JSX.Element { // 新增代码+DesktopGUIBrowserPanel：函数段开始，渲染右侧浏览器 provider 状态；如果没有这段，用户看不到 Playwright/CDP/Extension 三条轨道。
  const providers = asRecord(providerStatus.providers); // 新增代码+DesktopGUIBrowserPanel：读取 provider 集合；如果没有这行，面板无法列出浏览器能力轨道。
  const providerNames = Object.keys(providers); // 新增代码+DesktopGUIBrowserPanel：提取 provider 名称列表；如果没有这行，后续无法 map 渲染条目。
  const extension = asRecord(providerStatus.chrome_extension); // 新增代码+DesktopGUIBrowserPanel：读取 Chrome 扩展状态；如果没有这行，面板无法显示连接和命令队列摘要。
  const tabs = asRecord(providerStatus.tabs); // 新增代码+DesktopGUIBrowserPanel：读取标签页状态；如果没有这行，面板无法显示当前 tab 数量。
  const pendingCommandCount = Number(extension.pending_command_count ?? 0); // 新增代码+DesktopGUIBrowserPanel：读取待执行命令数量；如果没有这行，插件卡住时用户看不到队列迹象。
  const tabCount = Number(tabs.tab_count ?? 0); // 新增代码+DesktopGUIBrowserPanel：读取 tab 数量；如果没有这行，浏览器连接是否有页面上下文不直观。
  return ( // 新增代码+DesktopGUIBrowserPanel：返回浏览器状态面板结构；如果没有这行，组件不会输出 UI。
    <section className="browser-panel" aria-label="浏览器状态"> {/* 新增代码+DesktopGUIBrowserPanel：定义浏览器状态区域；如果没有这行，右侧栏缺少浏览器 provider 分区。 */}
      <div className="browser-panel-header"> {/* 新增代码+DesktopGUIBrowserPanel：定义面板标题区；如果没有这行，浏览器状态和事件列表层级会混在一起。 */}
        <h2>浏览器</h2> {/* 新增代码+DesktopGUIBrowserPanel：显示浏览器面板标题；如果没有这行，用户不知道这块状态的用途。 */}
        <span>{tabCount} tabs</span> {/* 新增代码+DesktopGUIBrowserPanel：显示 tab 数量摘要；如果没有这行，用户要展开状态才能知道页面上下文规模。 */}
      </div> {/* 新增代码+DesktopGUIBrowserPanel：面板标题区结束；如果没有这行，JSX 结构不完整。 */}
      {providerNames.length === 0 ? ( // 新增代码+DesktopGUIBrowserPanel：处理无 provider 状态；如果没有这行，空状态会显示成空白区域。
        <p className="browser-empty">暂无 provider 状态。</p> // 新增代码+DesktopGUIBrowserPanel：显示 provider 空状态；如果没有这行，用户不知道是未连接还是未加载。
      ) : ( // 新增代码+DesktopGUIBrowserPanel：处理有 provider 状态；如果没有这行，条件渲染语法不完整。
        <div className="browser-provider-list"> {/* 新增代码+DesktopGUIBrowserPanel：定义 provider 列表容器；如果没有这行，多条轨道没有稳定布局。 */}
          {providerNames.map((name) => { // 新增代码+DesktopGUIBrowserPanel：遍历 provider 名称；如果没有这行，各浏览器轨道不会渲染出来。
            const provider = asRecord(providers[name]); // 新增代码+DesktopGUIBrowserPanel：读取当前 provider 状态；如果没有这行，条目无法显示 available/reason。
            const available = provider.available === true; // 新增代码+DesktopGUIBrowserPanel：计算可用状态；如果没有这行，样式无法区分在线和未连接。
            return ( // 新增代码+DesktopGUIBrowserPanel：返回单个 provider 条目；如果没有这行，map 不会生成 JSX。
              <div className={`browser-provider ${available ? "browser-provider-ready" : "browser-provider-muted"}`} key={name}> {/* 新增代码+DesktopGUIBrowserPanel：渲染 provider 卡片；如果没有这行，用户看不到单条浏览器轨道。 */}
                <span>{providerNameLabel(name)}</span> {/* 新增代码+DesktopGUIBrowserPanel：显示 provider 名称；如果没有这行，用户不知道是哪条浏览器轨道。 */}
                <strong>{statusLabel(provider)}</strong> {/* 新增代码+DesktopGUIBrowserPanel：显示 provider 可用状态；如果没有这行，用户只能猜当前轨道是否可用。 */}
                <small>{String(provider.reason ?? "no reason")}</small> {/* 新增代码+DesktopGUIBrowserPanel：显示 provider 原因；如果没有这行，未连接时缺少下一步诊断线索。 */}
              </div> // 新增代码+DesktopGUIBrowserPanel：单个 provider 卡片结束；如果没有这行，JSX 结构不完整。
            ); // 新增代码+DesktopGUIBrowserPanel：单个 provider 返回结束；如果没有这行，map 回调语法不完整。
          })} {/* 新增代码+DesktopGUIBrowserPanel：provider 遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </div> // 新增代码+DesktopGUIBrowserPanel：provider 列表容器结束；如果没有这行，JSX 结构不完整。
      )} {/* 新增代码+DesktopGUIBrowserPanel：provider 条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      <div className="browser-provider-summary"> {/* 新增代码+DesktopGUIBrowserPanel：定义浏览器 provider 摘要；如果没有这行，扩展队列和连接状态没有固定位置。 */}
        <span>扩展连接：{extension.connected === true ? "已连接" : "未连接"}</span> {/* 新增代码+DesktopGUIBrowserPanel：显示扩展连接状态；如果没有这行，Chrome Extension 轨道是否在线不明显。 */}
        <span>待执行命令：{pendingCommandCount}</span> {/* 新增代码+DesktopGUIBrowserPanel：显示待执行命令数量；如果没有这行，命令堆积时缺少可见告警。 */}
      </div> {/* 新增代码+DesktopGUIBrowserPanel：provider 摘要结束；如果没有这行，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIBrowserPanel：浏览器状态区域结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIBrowserPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUIBrowserPanel：函数段结束，BrowserPanel 到此结束；如果没有这个边界，初学者不容易看出面板范围。
