type MemoryPanelProps = { // 新增代码+DesktopGUIMemoryPanel：定义记忆面板入参；如果没有这段，右侧页签不知道要接收 memory/prompt/notebook 汇总 payload。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUIMemoryPanel：保存组合后的后端 payload；如果没有这行，面板只能显示硬编码假数据。
}; // 新增代码+DesktopGUIMemoryPanel：入参类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会导致字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIMemoryPanel：只接受普通对象，否则返回空对象；如果没有这行，数组或 null 会被误当成对象。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asRecord 到此结束；如果没有这行，类型防护范围不清楚。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知列表安全收敛成对象数组；如果没有这段，记忆文件和工具列表会信任任意类型。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUIMemoryPanel：逐项转对象，非数组返回空数组；如果没有这行，map 渲染可能访问非法字段。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asRecordArray 到此结束；如果没有这行，列表防护范围不清楚。

function asText(value: unknown, fallback = ""): string { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知字段转成可显示短文本；如果没有这段，undefined/null 会直接污染 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIMemoryPanel：优先使用非空字符串，否则用兜底；如果没有这行，空字段会让卡片缺标题。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asText 到此结束；如果没有这行，文本兜底逻辑范围不清楚。

function asNumber(value: unknown, fallback = 0): number { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知字段转成数字；如果没有这段，token 和 notebook 计数可能显示 NaN。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopGUIMemoryPanel：只接受有限数字；如果没有这行，坏计数会污染统计栏。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asNumber 到此结束；如果没有这行，数字兜底逻辑范围不清楚。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知字段转成布尔值；如果没有这段，降级和只读状态无法稳定判断。
  return value === true; // 新增代码+DesktopGUIMemoryPanel：只有明确 true 才算真；如果没有这行，字符串 true 可能被误判。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asBoolean 到此结束；如果没有这行，布尔兜底逻辑范围不清楚。

function asStringArray(value: unknown): string[] { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知列表收敛成短文本数组；如果没有这段，预览行和 notebook 路径会直接信任后端。
  return Array.isArray(value) ? value.map((item) => asText(item)).filter((item) => item.length > 0) : []; // 新增代码+DesktopGUIMemoryPanel：清洗列表并去掉空文本；如果没有这行，空值可能出现在 GUI 列表里。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，asStringArray 到此结束；如果没有这行，文本数组清洗范围不清楚。

function statusClass(status: string): string { // 新增代码+DesktopGUIMemoryPanel：函数段开始，把状态映射到安全 class；如果没有这段，ready、missing 和 failed 不易扫视。
  if (["unreadable", "not_file", "unavailable", "failed", "degraded"].includes(status)) { // 新增代码+DesktopGUIMemoryPanel：识别失败或降级状态；如果没有这行，高风险状态不会突出。
    return "planning-status-danger"; // 新增代码+DesktopGUIMemoryPanel：返回危险状态样式；如果没有这行，失败条目没有视觉提醒。
  } // 新增代码+DesktopGUIMemoryPanel：危险状态分支结束；如果没有这行，条件块语法不完整。
  if (["ready", "available"].includes(status)) { // 新增代码+DesktopGUIMemoryPanel：识别可用状态；如果没有这行，正常工具会和空态混在一起。
    return "planning-status-active"; // 新增代码+DesktopGUIMemoryPanel：返回活动状态样式；如果没有这行，用户不易发现已接入能力。
  } // 新增代码+DesktopGUIMemoryPanel：可用状态分支结束；如果没有这行，条件块语法不完整。
  return "planning-status-muted"; // 新增代码+DesktopGUIMemoryPanel：返回默认状态样式；如果没有这行，函数可能返回 undefined。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，statusClass 到此结束；如果没有这行，状态样式范围不清楚。

function renderEmpty(message: string): JSX.Element { // 新增代码+DesktopGUIMemoryPanel：函数段开始，渲染统一空态；如果没有这段，暂无数据会被误看成坏布局。
  return <p className="planning-empty">{message}</p>; // 新增代码+DesktopGUIMemoryPanel：返回空态文本；如果没有这行，空列表会显示空白。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，renderEmpty 到此结束；如果没有这行，空态渲染范围不清楚。

function renderMemoryFiles(files: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIMemoryPanel：函数段开始，渲染 agent_memory 文件摘要；如果没有这段，context/progress/bugs 无法肉眼查看。
  const visibleFiles = files.slice(0, 6); // 新增代码+DesktopGUIMemoryPanel：限制可见记忆文件数量；如果没有这行，未来新增文件可能撑爆右侧面板。
  return ( // 新增代码+DesktopGUIMemoryPanel：返回记忆文件区块；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIMemoryPanel：记忆文件区块容器；如果没有这一层，文件列表没有稳定分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIMemoryPanel：记忆文件标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Memory Files</h3> {/* 新增代码+DesktopGUIMemoryPanel：显示记忆文件区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{files.length}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示记忆文件总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIMemoryPanel：记忆文件标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleFiles.length === 0 ? renderEmpty("暂无记忆文件数据。") : visibleFiles.map((file, index) => { // 新增代码+DesktopGUIMemoryPanel：渲染空态或文件卡片；如果没有这行，memory 区会空白。
        const status = asText(file.status, "missing"); // 新增代码+DesktopGUIMemoryPanel：读取文件状态；如果没有这行，状态胶囊没有输入。
        const previewLines = asStringArray(file.preview_lines); // 新增代码+DesktopGUIMemoryPanel：读取脱敏预览行；如果没有这行，用户看不到最新上下文片段。
        const headingLines = asStringArray(file.headings); // 新增代码+DesktopGUIMemoryPanel：读取最近标题；如果没有这行，长文档结构不可见。
        return ( // 新增代码+DesktopGUIMemoryPanel：返回单个记忆文件卡片；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-list-item" key={asText(file.id, `memory_${index}`)}> {/* 新增代码+DesktopGUIMemoryPanel：文件卡片容器；如果没有这一层，文件字段会散乱。 */}
            <strong>{asText(file.label, "Memory")}</strong> {/* 新增代码+DesktopGUIMemoryPanel：显示文件标签；如果没有这一行，用户无法区分 Context/Progress/Bugs。 */}
            <p>{asText(file.relative_path, "agent_memory")}</p> {/* 新增代码+DesktopGUIMemoryPanel：显示相对路径；如果没有这一行，用户不知道数据来源文件。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIMemoryPanel：文件元信息行；如果没有这一层，状态、行数和大小不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示文件状态；如果没有这一行，缺失或不可读状态不可见。 */}
              <small>{asNumber(file.line_count, 0)} lines</small> {/* 新增代码+DesktopGUIMemoryPanel：显示行数；如果没有这一行，记忆规模不可见。 */}
              <small>{asNumber(file.size_bytes, 0)} bytes</small> {/* 新增代码+DesktopGUIMemoryPanel：显示字节数；如果没有这一行，大文件风险不可见。 */}
            </div> {/* 新增代码+DesktopGUIMemoryPanel：文件元信息行结束；如果没有这一层，JSX 结构不完整。 */}
            {headingLines.length > 0 ? <p>Headings: {headingLines.join(" / ")}</p> : null} {/* 新增代码+DesktopGUIMemoryPanel：显示最近标题；如果没有这一行，长文档只有零散预览。 */}
            {previewLines.length > 0 ? <p>Preview: {previewLines.join(" | ")}</p> : renderEmpty("暂无可显示预览。")} {/* 新增代码+DesktopGUIMemoryPanel：显示脱敏预览或空态；如果没有这一行，用户不知道当前记忆内容是否为空。 */}
          </article> // 新增代码+DesktopGUIMemoryPanel：文件卡片结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIMemoryPanel：文件卡片返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIMemoryPanel：记忆文件条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIMemoryPanel：记忆文件区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMemoryPanel：记忆文件区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，renderMemoryFiles 到此结束；如果没有这行，记忆文件渲染范围不清楚。

function renderTools(title: string, tools: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIMemoryPanel：函数段开始，渲染工具可用性；如果没有这段，用户看不到 GUI 复用了哪些 agent 工具。
  return ( // 新增代码+DesktopGUIMemoryPanel：返回工具区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIMemoryPanel：工具区块容器；如果没有这一层，工具可用性没有分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIMemoryPanel：工具标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>{title}</h3> {/* 新增代码+DesktopGUIMemoryPanel：显示工具区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{tools.length}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示工具总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIMemoryPanel：工具标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {tools.length === 0 ? renderEmpty("暂无工具数据。") : tools.map((tool, index) => { // 新增代码+DesktopGUIMemoryPanel：渲染空态或工具条目；如果没有这行，工具区会空白。
        const status = asText(tool.status, asBoolean(tool.available) ? "available" : "unavailable"); // 新增代码+DesktopGUIMemoryPanel：读取工具状态；如果没有这行，可用性不可见。
        const reason = asText(tool.safe_unavailable_reason, ""); // 新增代码+DesktopGUIMemoryPanel：读取不可用原因；如果没有这行，缺工具时没有解释。
        return ( // 新增代码+DesktopGUIMemoryPanel：返回单个工具条目；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-tool-item" key={asText(tool.name, `tool_${index}`)}> {/* 新增代码+DesktopGUIMemoryPanel：工具条目容器；如果没有这一层，工具字段会散乱。 */}
            <strong>{asText(tool.name, "tool")}</strong> {/* 新增代码+DesktopGUIMemoryPanel：显示工具名；如果没有这一行，用户不知道是哪条能力。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIMemoryPanel：工具元信息行；如果没有这一层，状态和读写性质不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示工具状态；如果没有这一行，可用性不可见。 */}
              <small>{asBoolean(tool.read_only) ? "read" : "write"}</small> {/* 新增代码+DesktopGUIMemoryPanel：显示读写性质；如果没有这一行，notebook_edit 风险不可见。 */}
              <small>{asBoolean(tool.destructive) ? "destructive" : "safe"}</small> {/* 新增代码+DesktopGUIMemoryPanel：显示破坏性标记；如果没有这一行，用户无法识别危险工具。 */}
            </div> {/* 新增代码+DesktopGUIMemoryPanel：工具元信息行结束；如果没有这一层，JSX 结构不完整。 */}
            {reason ? <p>{reason}</p> : null} {/* 新增代码+DesktopGUIMemoryPanel：显示不可用原因；如果没有这一行，缺工具时用户只看到 unavailable。 */}
          </article> // 新增代码+DesktopGUIMemoryPanel：工具条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIMemoryPanel：工具条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIMemoryPanel：工具条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIMemoryPanel：工具区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMemoryPanel：工具区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，renderTools 到此结束；如果没有这行，工具渲染范围不清楚。

export function MemoryPanel({ payload = {} }: MemoryPanelProps): JSX.Element { // 新增代码+DesktopGUIMemoryPanel：函数段开始，渲染记忆、提示词、token 和 notebook 状态；如果没有这段，右侧 GUI 无法查看长任务防跑偏上下文。
  const panel = asRecord(payload); // 新增代码+DesktopGUIMemoryPanel：收敛组合 payload；如果没有这行，坏数据会让面板崩溃。
  const memory = asRecord(panel.memory); // 新增代码+DesktopGUIMemoryPanel：读取 memory 子 payload；如果没有这行，context/progress/bugs 区无法渲染。
  const prompt = asRecord(panel.prompt); // 新增代码+DesktopGUIMemoryPanel：读取 prompt/token 子 payload；如果没有这行，预算和工具状态无法渲染。
  const notebook = asRecord(panel.notebook); // 新增代码+DesktopGUIMemoryPanel：读取 notebook 子 payload；如果没有这行，notebook 状态无法渲染。
  const files = asRecordArray(memory.files); // 新增代码+DesktopGUIMemoryPanel：读取记忆文件列表；如果没有这行，文件摘要区没有输入。
  const promptTools = asRecordArray(prompt.tools); // 新增代码+DesktopGUIMemoryPanel：读取 prompt/token 工具列表；如果没有这行，prompt_surface_report 和 token_budget_report 不可见。
  const notebookTools = asRecordArray(notebook.tools); // 新增代码+DesktopGUIMemoryPanel：读取 notebook 工具列表；如果没有这行，notebook_read/edit 不可见。
  const budget = asRecord(prompt.context_budget); // 新增代码+DesktopGUIMemoryPanel：读取上下文预算；如果没有这行，max messages/max chars 无法显示。
  const snapshot = asRecord(prompt.snapshot_summary); // 新增代码+DesktopGUIMemoryPanel：读取运行快照摘要；如果没有这行，compact/resume 状态不可见。
  const compact = asRecord(snapshot.compact); // 新增代码+DesktopGUIMemoryPanel：读取 compact 子摘要；如果没有这行，压缩状态只能显示空白。
  const resume = asRecord(snapshot.resume); // 新增代码+DesktopGUIMemoryPanel：读取 resume 子摘要；如果没有这行，恢复状态只能显示空白。
  const notebooks = asStringArray(notebook.notebooks); // 新增代码+DesktopGUIMemoryPanel：读取 notebook 路径示例；如果没有这行，用户不知道 notebook 文件在哪里。
  const degraded = asBoolean(memory.status_degraded) || asBoolean(prompt.status_degraded) || asBoolean(notebook.status_degraded); // 新增代码+DesktopGUIMemoryPanel：合并三类降级状态；如果没有这行，面板无法整体提示数据可信度。
  const safeError = asText(memory.safe_error) || asText(prompt.safe_error) || asText(notebook.safe_error) || "记忆状态暂时不可读。"; // 新增代码+DesktopGUIMemoryPanel：合并脱敏错误；如果没有这行，降级提示可能空白。
  return ( // 新增代码+DesktopGUIMemoryPanel：返回记忆面板 JSX；如果没有这行，组件没有 UI 输出。
    <section className="planning-panel" aria-label="记忆提示词和 Token 状态"> {/* 新增代码+DesktopGUIMemoryPanel：面板根容器；如果没有这一层，样式和验收无法稳定定位。 */}
      <div className="planning-header"> {/* 新增代码+DesktopGUIMemoryPanel：标题行；如果没有这一层，标题和工具统计会混乱。 */}
        <div> {/* 新增代码+DesktopGUIMemoryPanel：标题文本容器；如果没有这一层，标题和说明无法垂直排列。 */}
          <h2>记忆与预算</h2> {/* 新增代码+DesktopGUIMemoryPanel：显示面板标题；如果没有这一行，用户不知道当前页签用途。 */}
          <p>复用 agent_memory、prompt report、token budget 和 notebook 工具的只读状态</p> {/* 新增代码+DesktopGUIMemoryPanel：说明数据来源；如果没有这一行，用户无法确认 GUI 没有重写记忆系统。 */}
        </div> {/* 新增代码+DesktopGUIMemoryPanel：标题文本容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{asNumber(prompt.available_tool_count, promptTools.length)}/{asNumber(prompt.tool_count, promptTools.length)} prompt tools</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 prompt 工具接入数；如果没有这一行，用户无法快速判断报告能力覆盖。 */}
      </div> {/* 新增代码+DesktopGUIMemoryPanel：标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="planning-summary"> {/* 新增代码+DesktopGUIMemoryPanel：摘要行；如果没有这一层，记忆、预算和 notebook 统计缺少固定位置。 */}
        <span>{asText(asRecord(memory.context_summary).status, "missing")} Context</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 Context 状态；如果没有这一行，用户无法判断主上下文是否存在。 */}
        <span>{asText(asRecord(memory.progress_summary).status, "missing")} Progress</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 Progress 状态；如果没有这一行，长任务进度是否可读不可见。 */}
        <span>{asText(asRecord(memory.bugs_summary).status, "missing")} Bugs</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 Bugs 状态；如果没有这一行，风险记录是否可读不可见。 */}
        <span>{asNumber(budget.max_messages, 0)} max messages</span> {/* 新增代码+DesktopGUIMemoryPanel：显示消息预算；如果没有这一行，压缩边界不可见。 */}
        <span>{asNumber(budget.max_chars, 0)} max chars</span> {/* 新增代码+DesktopGUIMemoryPanel：显示字符预算；如果没有这一行，token 近似边界不可见。 */}
        <span>{asNumber(notebook.notebook_count, notebooks.length)} notebooks</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 notebook 数量；如果没有这一行，notebook 可用性规模不可见。 */}
      </div> {/* 新增代码+DesktopGUIMemoryPanel：摘要行结束；如果没有这一层，JSX 结构不完整。 */}
      {degraded ? <p className="planning-warning">{safeError}</p> : null} {/* 新增代码+DesktopGUIMemoryPanel：显示降级提示；如果没有这一行，读取失败会被误认为正常空态。 */}
      <div className="planning-grid"> {/* 新增代码+DesktopGUIMemoryPanel：内容网格；如果没有这一层，各 section 会缺少稳定间距。 */}
        {renderMemoryFiles(files)} {/* 新增代码+DesktopGUIMemoryPanel：渲染记忆文件区；如果没有这一行，context/progress/bugs 摘要不可见。 */}
        <section className="planning-section"> {/* 新增代码+DesktopGUIMemoryPanel：prompt/token 区块容器；如果没有这一层，预算和快照缺少稳定分区。 */}
          <div className="planning-section-header"> {/* 新增代码+DesktopGUIMemoryPanel：prompt/token 标题行；如果没有这一层，标题和状态无法对齐。 */}
            <h3>Prompt & Token</h3> {/* 新增代码+DesktopGUIMemoryPanel：显示 prompt/token 区标题；如果没有这一行，用户不知道预算区用途。 */}
            <span>{asText(snapshot.status, "ready")}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示快照状态；如果没有这一行，compact/resume 数据可信度不可见。 */}
          </div> {/* 新增代码+DesktopGUIMemoryPanel：prompt/token 标题行结束；如果没有这一层，JSX 结构不完整。 */}
          <article className="planning-list-item"> {/* 新增代码+DesktopGUIMemoryPanel：预算卡片容器；如果没有这一层，预算字段会散乱。 */}
            <strong>Context Budget</strong> {/* 新增代码+DesktopGUIMemoryPanel：显示预算卡片标题；如果没有这一行，用户不知道 max 字段含义。 */}
            <p>{asText(budget.source, "OPENHARNESS_GUI_CONTEXT_*")}</p> {/* 新增代码+DesktopGUIMemoryPanel：显示预算来源；如果没有这一行，用户不知道预算来自环境变量。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIMemoryPanel：预算元信息行；如果没有这一层，max messages/max chars 不好扫描。 */}
              <span className="planning-status-active">{asNumber(budget.max_messages, 0)} max messages</span> {/* 新增代码+DesktopGUIMemoryPanel：显示最大消息数；如果没有这一行，长任务压缩阈值不可见。 */}
              <small>{asNumber(budget.max_chars, 0)} max chars</small> {/* 新增代码+DesktopGUIMemoryPanel：显示最大字符数；如果没有这一行，上下文字符边界不可见。 */}
            </div> {/* 新增代码+DesktopGUIMemoryPanel：预算元信息行结束；如果没有这一层，JSX 结构不完整。 */}
          </article> {/* 新增代码+DesktopGUIMemoryPanel：预算卡片结束；如果没有这一层，JSX 结构不完整。 */}
          <article className="planning-list-item"> {/* 新增代码+DesktopGUIMemoryPanel：快照卡片容器；如果没有这一层，compact/resume 字段会散乱。 */}
            <strong>Compact / Resume</strong> {/* 新增代码+DesktopGUIMemoryPanel：显示快照卡片标题；如果没有这一行，用户不知道状态来自哪里。 */}
            <p>compact: {asText(compact.status, "unknown")} · resume: {asText(resume.status, "unknown")}</p> {/* 新增代码+DesktopGUIMemoryPanel：显示压缩和恢复状态；如果没有这一行，长任务防跑偏状态不可见。 */}
          </article> {/* 新增代码+DesktopGUIMemoryPanel：快照卡片结束；如果没有这一层，JSX 结构不完整。 */}
        </section> {/* 新增代码+DesktopGUIMemoryPanel：prompt/token 区块结束；如果没有这一层，JSX 结构不完整。 */}
        {renderTools("Prompt Tools", promptTools)} {/* 新增代码+DesktopGUIMemoryPanel：渲染 prompt_surface_report 和 token_budget_report；如果没有这一行，报告工具状态不可见。 */}
        <section className="planning-section"> {/* 新增代码+DesktopGUIMemoryPanel：notebook 区块容器；如果没有这一层，notebook 文件和策略缺少稳定分区。 */}
          <div className="planning-section-header"> {/* 新增代码+DesktopGUIMemoryPanel：notebook 标题行；如果没有这一层，标题和数量无法对齐。 */}
            <h3>Notebook</h3> {/* 新增代码+DesktopGUIMemoryPanel：显示 notebook 区标题；如果没有这一行，用户不知道列表类型。 */}
            <span>{asNumber(notebook.notebook_count, notebooks.length)}</span> {/* 新增代码+DesktopGUIMemoryPanel：显示 notebook 数量；如果没有这一行，扫描结果规模不可见。 */}
          </div> {/* 新增代码+DesktopGUIMemoryPanel：notebook 标题行结束；如果没有这一层，JSX 结构不完整。 */}
          <article className="planning-list-item"> {/* 新增代码+DesktopGUIMemoryPanel：notebook 策略卡片容器；如果没有这一层，只读策略不可见。 */}
            <strong>{asBoolean(notebook.read_only_first_pass) ? "read-only first pass" : "edit mode"}</strong> {/* 新增代码+DesktopGUIMemoryPanel：显示只读优先策略；如果没有这一行，用户不知道 notebook_edit 是否暴露给 GUI。 */}
            <p>edit exposed in GUI: {asBoolean(notebook.edit_exposed_in_gui) ? "yes" : "no"}</p> {/* 新增代码+DesktopGUIMemoryPanel：显示编辑入口是否开放；如果没有这一行，风险边界不清楚。 */}
          </article> {/* 新增代码+DesktopGUIMemoryPanel：notebook 策略卡片结束；如果没有这一层，JSX 结构不完整。 */}
          {notebooks.length === 0 ? renderEmpty("暂无 notebook 文件。") : notebooks.slice(0, 8).map((path) => <article className="planning-list-item" key={path}><strong>{path}</strong></article>)} {/* 新增代码+DesktopGUIMemoryPanel：显示 notebook 路径或空态；如果没有这一行，用户看不到 notebook 位置。 */}
        </section> {/* 新增代码+DesktopGUIMemoryPanel：notebook 区块结束；如果没有这一层，JSX 结构不完整。 */}
        {renderTools("Notebook Tools", notebookTools)} {/* 新增代码+DesktopGUIMemoryPanel：渲染 notebook_read 和 notebook_edit 状态；如果没有这一行，notebook 工具链是否接入不可见。 */}
      </div> {/* 新增代码+DesktopGUIMemoryPanel：内容网格结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIMemoryPanel：面板根容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIMemoryPanel：组件返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIMemoryPanel：函数段结束，MemoryPanel 到此结束；如果没有这行，面板职责范围不清楚。
