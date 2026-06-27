type ToolchainPanelProps = { // 新增代码+DesktopGUIToolchainPanel：定义工具链面板入参；如果没有这段，右侧页签不知道要接收哪个后端 payload。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUIToolchainPanel：保存后端工具链清单；如果没有这行，面板只能显示硬编码假数据。
}; // 新增代码+DesktopGUIToolchainPanel：工具链面板入参结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会让字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIToolchainPanel：只接受普通对象并兜底空对象；如果没有这行，数组或 null 会被误当成对象。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，asRecord 到此结束；如果没有这行，类型防护范围不清楚。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把未知列表安全收敛成对象数组；如果没有这段，groups/tools 的渲染会信任任意类型。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUIToolchainPanel：数组逐项转对象，否则返回空数组；如果没有这行，map 渲染可能访问非法字段。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，asRecordArray 到此结束；如果没有这行，列表防护范围不清楚。

function asText(value: unknown, fallback: string): string { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把未知字段转成短文本；如果没有这段，undefined/null 会直接暴露到 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIToolchainPanel：优先使用非空字符串，否则使用兜底；如果没有这行，空字段会导致界面空白。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，asText 到此结束；如果没有这行，文本兜底逻辑范围不清楚。

function asNumber(value: unknown, fallback: number): number { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把未知字段转成数字；如果没有这段，计数可能显示 NaN。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopGUIToolchainPanel：只接受有限数字，否则使用兜底；如果没有这行，坏计数会污染面板。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，asNumber 到此结束；如果没有这行，数字兜底逻辑范围不清楚。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把未知字段转成布尔值；如果没有这段，风险徽标无法稳定判断真假。
  return value === true; // 新增代码+DesktopGUIToolchainPanel：只有明确 true 才算真；如果没有这行，字符串 true 等脏数据会被误判。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，asBoolean 到此结束；如果没有这行，布尔兜底逻辑范围不清楚。

function toolStatusLabel(status: string): string { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把内部状态转成中文短文案；如果没有这段，用户只能看到机器状态码。
  if (status === "ready") { // 新增代码+DesktopGUIToolchainPanel：识别已预加载工具；如果没有这行，核心工具不会有明确成熟状态。
    return "已就绪"; // 新增代码+DesktopGUIToolchainPanel：返回 ready 文案；如果没有这行，预加载状态无法可读展示。
  } // 新增代码+DesktopGUIToolchainPanel：ready 分支结束；如果没有这行，条件块语法不完整。
  if (status === "deferred") { // 新增代码+DesktopGUIToolchainPanel：识别延迟加载工具；如果没有这行，用户不知道哪些工具按需加载。
    return "按需加载"; // 新增代码+DesktopGUIToolchainPanel：返回 deferred 文案；如果没有这行，延迟加载状态不直观。
  } // 新增代码+DesktopGUIToolchainPanel：deferred 分支结束；如果没有这行，条件块语法不完整。
  return "可用"; // 新增代码+DesktopGUIToolchainPanel：返回默认可用文案；如果没有这行，普通工具会显示空状态。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，toolStatusLabel 到此结束；如果没有这行，状态映射范围不清楚。

function riskToneClass(tool: Record<string, unknown>): string { // 新增代码+DesktopGUIToolchainPanel：函数段开始，按风险字段生成样式 class；如果没有这段，破坏性工具和只读工具难以区分。
  if (asBoolean(tool.destructive)) { // 新增代码+DesktopGUIToolchainPanel：优先识别破坏性工具；如果没有这行，删除/写入类能力可能看起来像普通工具。
    return "toolchain-risk-high"; // 新增代码+DesktopGUIToolchainPanel：返回高风险样式；如果没有这行，高风险工具缺少醒目标记。
  } // 新增代码+DesktopGUIToolchainPanel：破坏性判断结束；如果没有这行，条件块语法不完整。
  if (asBoolean(tool.read_only)) { // 新增代码+DesktopGUIToolchainPanel：识别只读工具；如果没有这行，安全只读能力无法与写入能力区分。
    return "toolchain-risk-low"; // 新增代码+DesktopGUIToolchainPanel：返回低风险样式；如果没有这行，只读工具缺少低风险提示。
  } // 新增代码+DesktopGUIToolchainPanel：只读判断结束；如果没有这行，条件块语法不完整。
  return "toolchain-risk-medium"; // 新增代码+DesktopGUIToolchainPanel：返回默认中风险样式；如果没有这行，普通工具没有稳定样式。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，riskToneClass 到此结束；如果没有这行，风险样式逻辑范围不清楚。

function riskLabel(tool: Record<string, unknown>): string { // 新增代码+DesktopGUIToolchainPanel：函数段开始，把工具风险转成可读文案；如果没有这段，用户无法快速判断权限风险。
  if (asBoolean(tool.destructive)) { // 新增代码+DesktopGUIToolchainPanel：识别破坏性工具；如果没有这行，高风险行为可能被弱化。
    return "破坏性"; // 新增代码+DesktopGUIToolchainPanel：返回破坏性文案；如果没有这行，危险工具没有明确提示。
  } // 新增代码+DesktopGUIToolchainPanel：破坏性文案分支结束；如果没有这行，条件块语法不完整。
  if (asBoolean(tool.read_only)) { // 新增代码+DesktopGUIToolchainPanel：识别只读工具；如果没有这行，读操作不会被标记成低风险。
    return "只读"; // 新增代码+DesktopGUIToolchainPanel：返回只读文案；如果没有这行，用户不知道该工具不会写入。
  } // 新增代码+DesktopGUIToolchainPanel：只读文案分支结束；如果没有这行，条件块语法不完整。
  return asText(tool.risk_level, "受控"); // 新增代码+DesktopGUIToolchainPanel：展示后端风险等级并兜底；如果没有这行，中风险工具会缺少说明。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，riskLabel 到此结束；如果没有这行，风险文案逻辑范围不清楚。

function toolKey(groupId: string, tool: Record<string, unknown>, index: number): string { // 新增代码+DesktopGUIToolchainPanel：函数段开始，生成稳定 React key；如果没有这段，列表重排时 React 会难以跟踪条目。
  return `${groupId}:${asText(tool.name, "tool")}:${index}`; // 新增代码+DesktopGUIToolchainPanel：组合分组、工具名和索引；如果没有这行，重复工具名可能产生 key 冲突。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，toolKey 到此结束；如果没有这行，key 生成范围不清楚。

function renderTool(groupId: string, tool: Record<string, unknown>, index: number): JSX.Element { // 新增代码+DesktopGUIToolchainPanel：函数段开始，渲染单个工具条目；如果没有这段，工具清单只能显示分组空壳。
  const name = asText(tool.name, "unknown_tool"); // 新增代码+DesktopGUIToolchainPanel：读取工具名并兜底；如果没有这行，坏 payload 会导致空标题。
  const description = asText(tool.description, "暂无说明"); // 新增代码+DesktopGUIToolchainPanel：读取工具说明并兜底；如果没有这行，用户不知道工具用途。
  const source = asText(tool.source, "unknown"); // 新增代码+DesktopGUIToolchainPanel：读取工具来源；如果没有这行，用户无法判断是不是复用原工具。
  const status = toolStatusLabel(asText(tool.status, "available")); // 新增代码+DesktopGUIToolchainPanel：读取并翻译状态；如果没有这行，工具成熟度不清楚。
  const permissionMode = asText(tool.permission_mode, "默认"); // 新增代码+DesktopGUIToolchainPanel：读取权限模式；如果没有这行，用户无法判断 GUI 调用是否需要确认。
  const reuseModule = asText(tool.reuse_module, "未标注复用模块"); // 新增代码+DesktopGUIToolchainPanel：读取复用模块来源；如果没有这行，蓝图要求的“尽量复用原代码”不可见。
  return ( // 新增代码+DesktopGUIToolchainPanel：返回单个工具条目 JSX；如果没有这行，函数没有 UI 输出。
    <article className="toolchain-tool" key={toolKey(groupId, tool, index)}> {/* 新增代码+DesktopGUIToolchainPanel：工具条目容器；如果没有这一层，工具名、描述和元信息会混在一起。 */}
      <div className="toolchain-tool-main"> {/* 新增代码+DesktopGUIToolchainPanel：工具主信息布局；如果没有这一层，标题和说明没有稳定间距。 */}
        <strong>{name}</strong> {/* 新增代码+DesktopGUIToolchainPanel：显示工具名；如果没有这一行，用户看不到具体可用工具。 */}
        <span>{description}</span> {/* 新增代码+DesktopGUIToolchainPanel：显示工具说明；如果没有这一行，工具清单无法指导使用场景。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：工具主信息结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="toolchain-tool-meta"> {/* 新增代码+DesktopGUIToolchainPanel：工具元信息布局；如果没有这一层，状态、权限和复用来源无法快速扫描。 */}
        <small>{source}</small> {/* 新增代码+DesktopGUIToolchainPanel：显示工具来源；如果没有这一行，用户无法知道条目来自 builtin 还是外部能力。 */}
        <small>{status}</small> {/* 新增代码+DesktopGUIToolchainPanel：显示工具状态；如果没有这一行，用户不知道工具是否已就绪。 */}
        <small>{permissionMode}</small> {/* 新增代码+DesktopGUIToolchainPanel：显示权限模式；如果没有这一行，用户不知道调用前是否需要确认。 */}
        <small className={riskToneClass(tool)}>{riskLabel(tool)}</small> {/* 新增代码+DesktopGUIToolchainPanel：显示风险徽标；如果没有这一行，高风险和只读工具无法区分。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：工具元信息结束；如果没有这一层，JSX 结构不完整。 */}
      <code className="toolchain-reuse-module">{reuseModule}</code> {/* 新增代码+DesktopGUIToolchainPanel：显示复用模块路径；如果没有这一行，用户无法验收是否复用了原模块。 */}
    </article> // 新增代码+DesktopGUIToolchainPanel：工具条目容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIToolchainPanel：单个工具条目返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，renderTool 到此结束；如果没有这行，工具渲染范围不清楚。

function renderGroup(group: Record<string, unknown>, index: number): JSX.Element { // 新增代码+DesktopGUIToolchainPanel：函数段开始，渲染一个工具分组；如果没有这段，工具链无法按能力域组织。
  const id = asText(group.id, `group_${index}`); // 新增代码+DesktopGUIToolchainPanel：读取分组 id 并兜底；如果没有这行，React key 和语义身份不稳定。
  const label = asText(group.label, id); // 新增代码+DesktopGUIToolchainPanel：读取分组显示名；如果没有这行，用户只能看到内部 id。
  const tools = asRecordArray(group.tools); // 新增代码+DesktopGUIToolchainPanel：读取分组工具列表；如果没有这行，分组内工具无法渲染。
  const toolCount = asNumber(group.tool_count, tools.length); // 新增代码+DesktopGUIToolchainPanel：读取分组工具数并兜底真实列表长度；如果没有这行，数量可能为空或错误。
  return ( // 新增代码+DesktopGUIToolchainPanel：返回分组 JSX；如果没有这行，函数没有 UI 输出。
    <section className="toolchain-group" key={id}> {/* 新增代码+DesktopGUIToolchainPanel：分组容器；如果没有这一层，工具分组边界不可见。 */}
      <div className="toolchain-group-header"> {/* 新增代码+DesktopGUIToolchainPanel：分组标题行；如果没有这一层，分组名和数量无法稳定排列。 */}
        <h3>{label}</h3> {/* 新增代码+DesktopGUIToolchainPanel：显示分组名；如果没有这一行，用户看不到能力域。 */}
        <span>{toolCount} tools</span> {/* 新增代码+DesktopGUIToolchainPanel：显示分组工具数；如果没有这一行，用户无法快速判断分组规模。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：分组标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="toolchain-tool-list"> {/* 新增代码+DesktopGUIToolchainPanel：分组工具列表容器；如果没有这一层，工具条目没有滚动和间距基础。 */}
        {tools.length === 0 ? <p className="toolchain-empty">暂无工具</p> : tools.map((tool, toolIndex) => renderTool(id, tool, toolIndex))} {/* 新增代码+DesktopGUIToolchainPanel：按工具列表渲染条目或空态；如果没有这一行，分组内容会空白。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：分组工具列表结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIToolchainPanel：分组容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIToolchainPanel：分组返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，renderGroup 到此结束；如果没有这行，分组渲染范围不清楚。

export function ToolchainPanel({ payload = {} }: ToolchainPanelProps): JSX.Element { // 新增代码+DesktopGUIToolchainPanel：函数段开始，渲染 GUI 工具链控制中心；如果没有这段，右侧 GUI 无法展示后端真实工具链。
  const panel = asRecord(payload); // 新增代码+DesktopGUIToolchainPanel：把 payload 收敛成对象；如果没有这行，坏数据会让面板崩溃。
  const groups = asRecordArray(panel.groups); // 新增代码+DesktopGUIToolchainPanel：读取工具分组列表；如果没有这行，工具链清单没有主体内容。
  const toolCount = asNumber(panel.tool_count, groups.reduce((total, group) => total + asNumber(group.tool_count, asRecordArray(group.tools).length), 0)); // 新增代码+DesktopGUIToolchainPanel：读取或计算工具总数；如果没有这行，面板无法展示工具规模。
  const groupCount = asNumber(panel.group_count, groups.length); // 新增代码+DesktopGUIToolchainPanel：读取或计算分组总数；如果没有这行，面板无法展示能力域数量。
  const schemaVersion = asNumber(panel.schema_version, 0); // 新增代码+DesktopGUIToolchainPanel：读取 schema 版本；如果没有这行，协议版本不可见。
  const degraded = asBoolean(panel.status_degraded); // 新增代码+DesktopGUIToolchainPanel：读取降级状态；如果没有这行，后端清单不可信时用户看不到提示。
  const safeError = asText(panel.safe_error, "工具链清单暂时不可读。"); // 新增代码+DesktopGUIToolchainPanel：读取安全错误文案；如果没有这行，降级时可能显示空白或原始异常。
  return ( // 新增代码+DesktopGUIToolchainPanel：返回工具链面板 JSX；如果没有这行，组件没有 UI 输出。
    <section className="toolchain-panel" aria-label="工具链控制中心"> {/* 新增代码+DesktopGUIToolchainPanel：工具链面板根容器；如果没有这一层，样式和验收无法稳定定位。 */}
      <div className="toolchain-header"> {/* 新增代码+DesktopGUIToolchainPanel：面板标题行；如果没有这一层，标题和统计信息会混乱。 */}
        <div> {/* 新增代码+DesktopGUIToolchainPanel：标题文本容器；如果没有这一层，标题和说明无法垂直排列。 */}
          <h2>工具链</h2> {/* 新增代码+DesktopGUIToolchainPanel：显示工具链标题；如果没有这一行，用户不知道当前页签用途。 */}
          <p>复用后端工具注册表生成的 GUI 控制清单</p> {/* 新增代码+DesktopGUIToolchainPanel：说明数据来源；如果没有这一行，用户无法确认不是前端硬编码。 */}
        </div> {/* 新增代码+DesktopGUIToolchainPanel：标题文本容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{toolCount} tools</span> {/* 新增代码+DesktopGUIToolchainPanel：显示工具总数；如果没有这一行，用户无法快速判断接入规模。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：面板标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="toolchain-summary"> {/* 新增代码+DesktopGUIToolchainPanel：面板摘要行；如果没有这一层，schema 和分组数量缺少固定位置。 */}
        <span>{groupCount} groups</span> {/* 新增代码+DesktopGUIToolchainPanel：显示分组数量；如果没有这一行，用户无法判断能力域覆盖。 */}
        <span>schema {schemaVersion}</span> {/* 新增代码+DesktopGUIToolchainPanel：显示协议版本；如果没有这一行，合同演进不可见。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：面板摘要行结束；如果没有这一层，JSX 结构不完整。 */}
      {degraded ? <p className="toolchain-warning">{safeError}</p> : null} {/* 新增代码+DesktopGUIToolchainPanel：显示降级提示；如果没有这一行，工具链读取失败会被误认为正常空态。 */}
      <div className="toolchain-group-list"> {/* 新增代码+DesktopGUIToolchainPanel：分组列表容器；如果没有这一层，分组缺少稳定滚动布局。 */}
        {groups.length === 0 ? <p className="toolchain-empty">等待工具链清单。</p> : groups.map((group, groupIndex) => renderGroup(group, groupIndex))} {/* 新增代码+DesktopGUIToolchainPanel：渲染工具分组或空态；如果没有这一行，面板不会显示真实工具清单。 */}
      </div> {/* 新增代码+DesktopGUIToolchainPanel：分组列表容器结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIToolchainPanel：工具链面板根容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIToolchainPanel：组件返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIToolchainPanel：函数段结束，ToolchainPanel 到此结束；如果没有这行，面板职责范围不清楚。
