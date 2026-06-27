type McpPanelProps = { // 新增代码+DesktopGUIMcpPanel：定义 MCP 面板入参；如果没有这段，右侧页签不知道要接收哪个后端 payload。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUIMcpPanel：保存 MCP 管理总览 payload；如果没有这行，面板只能显示硬编码假数据。
}; // 新增代码+DesktopGUIMcpPanel：MCP 面板入参结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIMcpPanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会导致字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIMcpPanel：只接受普通对象，否则返回空对象；如果没有这行，数组或 null 会被误当成对象。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，asRecord 到此结束；如果没有这行，类型防护范围不清楚。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIMcpPanel：函数段开始，把未知列表安全收敛成对象数组；如果没有这段，server/resource/prompt 列表会信任任意类型。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUIMcpPanel：逐项转对象，非数组返回空数组；如果没有这行，map 渲染可能访问非法字段。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，asRecordArray 到此结束；如果没有这行，列表防护范围不清楚。

function asText(value: unknown, fallback: string): string { // 新增代码+DesktopGUIMcpPanel：函数段开始，把未知字段转成可显示短文本；如果没有这段，undefined/null 会直接污染 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIMcpPanel：优先使用非空字符串，否则用兜底；如果没有这行，空字段会让卡片缺标题。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，asText 到此结束；如果没有这行，文本兜底逻辑范围不清楚。

function asNumber(value: unknown, fallback: number): number { // 新增代码+DesktopGUIMcpPanel：函数段开始，把未知字段转成数字；如果没有这段，计数可能显示 NaN。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopGUIMcpPanel：只接受有限数字；如果没有这行，坏计数会污染统计栏。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，asNumber 到此结束；如果没有这行，数字兜底逻辑范围不清楚。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUIMcpPanel：函数段开始，把未知字段转成布尔值；如果没有这段，降级提示无法稳定判断。
  return value === true; // 新增代码+DesktopGUIMcpPanel：只有明确 true 才算真；如果没有这行，字符串 true 可能被误判。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，asBoolean 到此结束；如果没有这行，布尔兜底逻辑范围不清楚。

function statusLabel(status: string): string { // 新增代码+DesktopGUIMcpPanel：函数段开始，把 MCP 状态码转成中文；如果没有这段，用户只能看到机器状态。
  if (status === "available") { // 新增代码+DesktopGUIMcpPanel：识别可用状态；如果没有这行，可用 server 没有友好文案。
    return "可用"; // 新增代码+DesktopGUIMcpPanel：返回可用文案；如果没有这行，available 状态无法中文展示。
  } // 新增代码+DesktopGUIMcpPanel：可用分支结束；如果没有这行，条件块语法不完整。
  if (status === "degraded") { // 新增代码+DesktopGUIMcpPanel：识别降级状态；如果没有这行，局部失败无法突出。
    return "降级"; // 新增代码+DesktopGUIMcpPanel：返回降级文案；如果没有这行，用户看不出资源或 prompt 枚举失败。
  } // 新增代码+DesktopGUIMcpPanel：降级分支结束；如果没有这行，条件块语法不完整。
  if (status === "failed") { // 新增代码+DesktopGUIMcpPanel：识别失败状态；如果没有这行，启动失败会像普通配置一样展示。
    return "失败"; // 新增代码+DesktopGUIMcpPanel：返回失败文案；如果没有这行，用户看不到高风险状态。
  } // 新增代码+DesktopGUIMcpPanel：失败分支结束；如果没有这行，条件块语法不完整。
  return "已配置"; // 新增代码+DesktopGUIMcpPanel：返回兜底文案；如果没有这行，configured/unknown 状态会显示空白。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，statusLabel 到此结束；如果没有这行，状态映射范围不清楚。

function statusClass(status: string): string { // 新增代码+DesktopGUIMcpPanel：函数段开始，按状态生成样式 class；如果没有这段，失败和可用 server 难以扫视区分。
  if (status === "failed") { // 新增代码+DesktopGUIMcpPanel：识别失败状态；如果没有这行，失败卡片不会有高风险样式。
    return "mcp-server-failed"; // 新增代码+DesktopGUIMcpPanel：返回失败样式；如果没有这行，失败状态缺少视觉提醒。
  } // 新增代码+DesktopGUIMcpPanel：失败样式分支结束；如果没有这行，条件块语法不完整。
  if (status === "degraded") { // 新增代码+DesktopGUIMcpPanel：识别降级状态；如果没有这行，局部失败不会区别于可用。
    return "mcp-server-degraded"; // 新增代码+DesktopGUIMcpPanel：返回降级样式；如果没有这行，降级状态缺少视觉提醒。
  } // 新增代码+DesktopGUIMcpPanel：降级样式分支结束；如果没有这行，条件块语法不完整。
  return "mcp-server-available"; // 新增代码+DesktopGUIMcpPanel：返回默认可用样式；如果没有这行，正常卡片没有稳定 class。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，statusClass 到此结束；如果没有这行，样式映射范围不清楚。

function itemKey(prefix: string, item: Record<string, unknown>, index: number): string { // 新增代码+DesktopGUIMcpPanel：函数段开始，生成稳定 React key；如果没有这段，列表刷新时 React 难以跟踪条目。
  return `${prefix}:${asText(item.server, "server")}:${asText(item.name, "item")}:${index}`; // 新增代码+DesktopGUIMcpPanel：组合集合、server、名称和序号；如果没有这行，重复名称可能造成 key 冲突。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，itemKey 到此结束；如果没有这行，key 生成范围不清楚。

function renderServer(server: Record<string, unknown>, index: number): JSX.Element { // 新增代码+DesktopGUIMcpPanel：函数段开始，渲染单个 MCP server 卡片；如果没有这段，MCP 页签只有统计没有可操作诊断线索。
  const name = asText(server.name, `mcp_server_${index}`); // 新增代码+DesktopGUIMcpPanel：读取 server 名称；如果没有这行，卡片没有主标题。
  const status = asText(server.status, "configured"); // 新增代码+DesktopGUIMcpPanel：读取 server 状态；如果没有这行，卡片无法显示可用/失败。
  const transport = asText(server.transport, "runtime"); // 新增代码+DesktopGUIMcpPanel：读取 transport；如果没有这行，用户无法区分 stdio/http/sse。
  const resources = asNumber(server.resource_count, 0); // 新增代码+DesktopGUIMcpPanel：读取资源数量；如果没有这行，server 的资源覆盖不可见。
  const prompts = asNumber(server.prompt_count, 0); // 新增代码+DesktopGUIMcpPanel：读取 prompt 数量；如果没有这行，server 的提示词覆盖不可见。
  const lastError = asText(server.last_error, ""); // 新增代码+DesktopGUIMcpPanel：读取脱敏错误；如果没有这行，失败原因不会显示。
  const config = asRecord(server.config_summary); // 新增代码+DesktopGUIMcpPanel：读取安全配置摘要；如果没有这行，连接来源无法展示。
  const connection = asRecord(config.connection); // 新增代码+DesktopGUIMcpPanel：读取安全连接摘要；如果没有这行，origin/command 无法展示。
  const connectionLabel = asText(connection.origin, asText(connection.command, "runtime")); // 新增代码+DesktopGUIMcpPanel：优先展示 origin，否则展示命令名；如果没有这行，用户无法确认连接来源。
  const streamState = asRecord(server.stream_state); // 新增代码+DesktopGUIMcpPanel：读取 stream 状态；如果没有这行，长连接诊断不可见。
  const streamLabel = streamState.connected === true ? "stream on" : asText(streamState.status, "stream idle"); // 新增代码+DesktopGUIMcpPanel：生成 stream 简短标签；如果没有这行，stream_state 对象会难以扫读。
  return ( // 新增代码+DesktopGUIMcpPanel：返回 server 卡片 JSX；如果没有这行，函数没有 UI 输出。
    <article className={`mcp-server-card ${statusClass(status)}`} key={`${name}:${index}`}> {/* 新增代码+DesktopGUIMcpPanel：server 卡片容器；如果没有这一层，名称、状态、计数会混在一起。 */}
      <div className="mcp-server-main"> {/* 新增代码+DesktopGUIMcpPanel：server 主信息布局；如果没有这一层，标题和状态缺少稳定排版。 */}
        <strong>{name}</strong> {/* 新增代码+DesktopGUIMcpPanel：显示 server 名称；如果没有这一行，用户不知道是哪一个 MCP server。 */}
        <span>{transport}</span> {/* 新增代码+DesktopGUIMcpPanel：显示 transport；如果没有这一行，用户不知道 server 连接方式。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：server 主信息布局结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="mcp-server-metrics"> {/* 新增代码+DesktopGUIMcpPanel：server 计数布局；如果没有这一层，resource/prompt/status 不好扫描。 */}
        <small>{statusLabel(status)}</small> {/* 新增代码+DesktopGUIMcpPanel：显示中文状态；如果没有这一行，状态码不够友好。 */}
        <small>{resources} resources</small> {/* 新增代码+DesktopGUIMcpPanel：显示 resource 数量；如果没有这一行，资源规模不可见。 */}
        <small>{prompts} prompts</small> {/* 新增代码+DesktopGUIMcpPanel：显示 prompt 数量；如果没有这一行，提示词规模不可见。 */}
        <small>{streamLabel}</small> {/* 新增代码+DesktopGUIMcpPanel：显示 stream 简况；如果没有这一行，连接流状态不可见。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：server 计数布局结束；如果没有这一层，JSX 结构不完整。 */}
      <code className="mcp-connection-label">{connectionLabel}</code> {/* 新增代码+DesktopGUIMcpPanel：显示脱敏连接摘要；如果没有这一行，用户无法确认复用的是哪个外部入口。 */}
      {lastError ? <p className="mcp-server-error">{lastError}</p> : null} {/* 新增代码+DesktopGUIMcpPanel：显示脱敏错误；如果没有这一行，失败 server 没有原因。 */}
    </article> // 新增代码+DesktopGUIMcpPanel：server 卡片结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMcpPanel：server 卡片返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，renderServer 到此结束；如果没有这行，server 渲染范围不清楚。

function renderCollection(title: string, kind: "resources" | "prompts", items: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIMcpPanel：函数段开始，渲染 resource 或 prompt 摘要列表；如果没有这段，MCP 集合只能显示总数。
  const visibleItems = items.slice(0, 6); // 新增代码+DesktopGUIMcpPanel：限制可见条目数量；如果没有这行，大量 MCP 资源会撑爆右侧面板。
  return ( // 新增代码+DesktopGUIMcpPanel：返回集合 JSX；如果没有这行，函数没有 UI 输出。
    <section className="mcp-collection"> {/* 新增代码+DesktopGUIMcpPanel：集合容器；如果没有这一层，资源和 prompt 列表没有分区。 */}
      <div className="mcp-collection-header"> {/* 新增代码+DesktopGUIMcpPanel：集合标题行；如果没有这一层，标题和数量无法稳定排版。 */}
        <h3>{title}</h3> {/* 新增代码+DesktopGUIMcpPanel：显示集合标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{items.length}</span> {/* 新增代码+DesktopGUIMcpPanel：显示集合总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：集合标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleItems.length === 0 ? <p className="mcp-empty">暂无数据</p> : visibleItems.map((item, index) => ( // 新增代码+DesktopGUIMcpPanel：渲染空态或集合条目；如果没有这一行，集合内容会空白。
        <article className="mcp-collection-item" key={itemKey(kind, item, index)}> {/* 新增代码+DesktopGUIMcpPanel：集合条目容器；如果没有这一层，条目字段会混在一起。 */}
          <strong>{asText(item.name, kind === "resources" ? "resource" : "prompt")}</strong> {/* 新增代码+DesktopGUIMcpPanel：显示 resource/prompt 名称；如果没有这一行，条目没有主标识。 */}
          <span>{asText(item.server, "server")}</span> {/* 新增代码+DesktopGUIMcpPanel：显示条目归属 server；如果没有这一行，用户无法定位来源。 */}
          <small>{kind === "resources" ? asText(item.uri, "no uri") : `${asNumber(item.argument_count, 0)} args`}</small> {/* 新增代码+DesktopGUIMcpPanel：资源显示 URI，prompt 显示参数数；如果没有这一行，集合诊断信息不足。 */}
        </article> // 新增代码+DesktopGUIMcpPanel：集合条目结束；如果没有这行，JSX 结构不完整。
      ))} {/* 新增代码+DesktopGUIMcpPanel：集合条目渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIMcpPanel：集合容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMcpPanel：集合返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，renderCollection 到此结束；如果没有这行，集合渲染范围不清楚。

export function McpPanel({ payload = {} }: McpPanelProps): JSX.Element { // 新增代码+DesktopGUIMcpPanel：函数段开始，渲染 MCP 管理面板；如果没有这段，右侧 GUI 无法查看 MCP server/resource/prompt 状态。
  const panel = asRecord(payload); // 新增代码+DesktopGUIMcpPanel：收敛 payload；如果没有这行，坏数据会让面板崩溃。
  const servers = asRecordArray(panel.servers); // 新增代码+DesktopGUIMcpPanel：读取 server 列表；如果没有这行，server 卡片无法渲染。
  const resources = asRecordArray(panel.resources); // 新增代码+DesktopGUIMcpPanel：读取 resource 列表；如果没有这行，资源摘要无法渲染。
  const prompts = asRecordArray(panel.prompts); // 新增代码+DesktopGUIMcpPanel：读取 prompt 列表；如果没有这行，提示词摘要无法渲染。
  const serverCount = asNumber(panel.server_count, servers.length); // 新增代码+DesktopGUIMcpPanel：读取或计算 server 数量；如果没有这行，标题统计不稳定。
  const resourceCount = asNumber(panel.resource_count, resources.length); // 新增代码+DesktopGUIMcpPanel：读取或计算 resource 数量；如果没有这行，资源统计不稳定。
  const promptCount = asNumber(panel.prompt_count, prompts.length); // 新增代码+DesktopGUIMcpPanel：读取或计算 prompt 数量；如果没有这行，prompt 统计不稳定。
  const schemaVersion = asNumber(panel.schema_version, 0); // 新增代码+DesktopGUIMcpPanel：读取 schema 版本；如果没有这行，协议版本不可见。
  const degraded = asBoolean(panel.status_degraded); // 新增代码+DesktopGUIMcpPanel：读取整体降级状态；如果没有这行，失败摘要不会显示。
  const safeError = asText(panel.safe_error, "MCP 状态暂时不可读。"); // 新增代码+DesktopGUIMcpPanel：读取脱敏错误文案；如果没有这行，降级时可能显示空白。
  return ( // 新增代码+DesktopGUIMcpPanel：返回 MCP 面板 JSX；如果没有这行，组件没有 UI 输出。
    <section className="mcp-panel" aria-label="MCP 管理中心"> {/* 新增代码+DesktopGUIMcpPanel：MCP 面板根容器；如果没有这一层，样式和验收无法稳定定位。 */}
      <div className="mcp-header"> {/* 新增代码+DesktopGUIMcpPanel：MCP 标题行；如果没有这一层，标题和总数会混乱。 */}
        <div> {/* 新增代码+DesktopGUIMcpPanel：标题文本容器；如果没有这一层，标题和说明无法垂直排列。 */}
          <h2>MCP</h2> {/* 新增代码+DesktopGUIMcpPanel：显示 MCP 页签标题；如果没有这一行，用户不知道当前面板用途。 */}
          <p>复用后端 MCP registry 的 server、resource 和 prompt 只读状态</p> {/* 新增代码+DesktopGUIMcpPanel：说明数据来源；如果没有这一行，用户无法确认 GUI 没有重写 MCP 链路。 */}
        </div> {/* 新增代码+DesktopGUIMcpPanel：标题文本容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{serverCount} servers</span> {/* 新增代码+DesktopGUIMcpPanel：显示 server 总数；如果没有这一行，用户无法快速判断接入规模。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：MCP 标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="mcp-summary"> {/* 新增代码+DesktopGUIMcpPanel：MCP 摘要行；如果没有这一层，资源、提示词和 schema 缺少固定位置。 */}
        <span>{resourceCount} resources</span> {/* 新增代码+DesktopGUIMcpPanel：显示资源总数；如果没有这一行，resource 覆盖不可见。 */}
        <span>{promptCount} prompts</span> {/* 新增代码+DesktopGUIMcpPanel：显示 prompt 总数；如果没有这一行，提示词覆盖不可见。 */}
        <span>schema {schemaVersion}</span> {/* 新增代码+DesktopGUIMcpPanel：显示协议版本；如果没有这一行，合同演进不可见。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：MCP 摘要行结束；如果没有这一层，JSX 结构不完整。 */}
      {degraded ? <p className="mcp-warning">{safeError}</p> : null} {/* 新增代码+DesktopGUIMcpPanel：显示整体降级提示；如果没有这一行，MCP 读取失败会被误认为正常空态。 */}
      <div className="mcp-server-list"> {/* 新增代码+DesktopGUIMcpPanel：server 列表容器；如果没有这一层，server 卡片没有稳定间距。 */}
        {servers.length === 0 ? <p className="mcp-empty">暂无 MCP server 配置。</p> : servers.map((server, index) => renderServer(server, index))} {/* 新增代码+DesktopGUIMcpPanel：渲染 server 卡片或空态；如果没有这一行，MCP server 状态不可见。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：server 列表容器结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="mcp-collections"> {/* 新增代码+DesktopGUIMcpPanel：resource/prompt 集合区域；如果没有这一层，两个集合缺少统一布局。 */}
        {renderCollection("Resources", "resources", resources)} {/* 新增代码+DesktopGUIMcpPanel：渲染资源集合；如果没有这一行，resource 列表不可见。 */}
        {renderCollection("Prompts", "prompts", prompts)} {/* 新增代码+DesktopGUIMcpPanel：渲染 prompt 集合；如果没有这一行，prompt 列表不可见。 */}
      </div> {/* 新增代码+DesktopGUIMcpPanel：resource/prompt 集合区域结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIMcpPanel：MCP 面板根容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMcpPanel：组件返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMcpPanel：函数段结束，McpPanel 到此结束；如果没有这行，面板职责范围不清楚。
