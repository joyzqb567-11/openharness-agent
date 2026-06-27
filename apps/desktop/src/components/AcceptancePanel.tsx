type AcceptancePanelProps = { // 新增代码+DesktopGUIAcceptancePanel：类型段开始，定义验收控制中心面板入参；如果没有这段，StatusInspector 不知道如何传递验收 payload 和运行回调。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUIAcceptancePanel：保存 /v2/gui/acceptance/scenarios 响应；如果没有这行，面板没有后端事实源。
  onRunScenario?: (scenarioId: string) => void; // 新增代码+DesktopGUIAcceptancePanel：保存运行场景回调；如果没有这行，运行按钮无法接到 AppShell。
  actionPending?: boolean; // 新增代码+DesktopGUIAcceptancePanel：保存按钮等待态；如果没有这行，用户可能重复点击启动验收。
  lastActionResult?: Record<string, unknown>; // 新增代码+DesktopGUIAcceptancePanel：保存最近启动请求结果；如果没有这行，按钮反馈只能停留在主线程里。
}; // 新增代码+DesktopGUIAcceptancePanel：类型段结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，把未知值安全收敛成对象；如果没有这段，后端坏 payload 会拖垮右侧栏。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIAcceptancePanel：只接受普通对象，否则返回空对象；如果没有这行，字段读取会信任任意类型。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，asRecord 到此结束；如果没有这行，函数语法不完整。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，把未知值安全收敛成对象数组；如果没有这段，scenarios/evidence 字段类型漂移会报错。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUIAcceptancePanel：数组逐项收敛，不是数组则返回空；如果没有这行，map 可能访问非数组。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，asRecordArray 到此结束；如果没有这行，函数语法不完整。

function asText(value: unknown, fallback = ""): string { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，安全读取可见文本；如果没有这段，数字/null 字段会直接污染 JSX。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIAcceptancePanel：只接受非空字符串，否则返回兜底；如果没有这行，空字段会显示成 undefined。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，asText 到此结束；如果没有这行，函数语法不完整。

function asNumber(value: unknown, fallback = 0): number { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，安全读取数字字段；如果没有这段，统计可能显示 NaN。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopGUIAcceptancePanel：只接受有限数字；如果没有这行，NaN 或字符串会进入 UI。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，asNumber 到此结束；如果没有这行，函数语法不完整。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，安全读取布尔字段；如果没有这段，运行按钮可能把任意 truthy 值当许可。
  return value === true; // 新增代码+DesktopGUIAcceptancePanel：只有明确 true 才视为真；如果没有这行，字符串 true 可能误启用按钮。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，asBoolean 到此结束；如果没有这行，函数语法不完整。

function statusClass(status: string): string { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，把验收状态映射为 planning 徽标样式；如果没有这段，passed/failed/planned 不易扫描。
  if (status === "failed" || status === "unavailable" || status === "not_found") { // 新增代码+DesktopGUIAcceptancePanel：识别失败或不可用状态；如果没有这行，验收失败不会突出。
    return "planning-status-danger"; // 新增代码+DesktopGUIAcceptancePanel：返回危险样式；如果没有这行，失败场景看起来像普通信息。
  } // 新增代码+DesktopGUIAcceptancePanel：错误状态分支结束；如果没有这行，条件块语法不完整。
  if (status === "passed" || status === "launched" || status === "planned") { // 新增代码+DesktopGUIAcceptancePanel：识别通过或已启动状态；如果没有这行，成功闭环不够醒目。
    return "planning-status-active"; // 新增代码+DesktopGUIAcceptancePanel：返回活跃样式；如果没有这行，用户难以快速找到可用结果。
  } // 新增代码+DesktopGUIAcceptancePanel：通过状态分支结束；如果没有这行，条件块语法不完整。
  return "planning-status-muted"; // 新增代码+DesktopGUIAcceptancePanel：其它状态使用普通样式；如果没有这行，函数可能返回 undefined。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，statusClass 到此结束；如果没有这行，函数语法不完整。

function evidenceText(evidence: Record<string, unknown>): string { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，生成证据短文本；如果没有这段，证据渲染逻辑会散在 JSX。
  const label = asText(evidence.label, asText(evidence.kind, "evidence")); // 新增代码+DesktopGUIAcceptancePanel：优先显示 label；如果没有这行，证据类型不可读。
  const path = asText(evidence.relative_path, "missing"); // 新增代码+DesktopGUIAcceptancePanel：读取相对路径；如果没有这行，用户不知道证据在哪里。
  return `${label}: ${path}`; // 新增代码+DesktopGUIAcceptancePanel：组合显示文本；如果没有这行，证据条目没有输出。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，evidenceText 到此结束；如果没有这行，函数语法不完整。

function renderEvidence(evidence: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，渲染证据链接摘要；如果没有这段，result/events/screenshot 不会肉眼可见。
  const visibleEvidence = evidence.slice(0, 4); // 新增代码+DesktopGUIAcceptancePanel：限制证据数量；如果没有这行，长证据列表会撑爆右侧栏。
  return ( // 新增代码+DesktopGUIAcceptancePanel：返回证据列表 JSX；如果没有这行，函数没有 UI 输出。
    <ul className="acceptance-evidence"> {/* 新增代码+DesktopGUIAcceptancePanel：证据列表容器；如果没有这一层，证据文本缺少语义结构。 */}
      {visibleEvidence.length === 0 ? <li>暂无证据</li> : visibleEvidence.map((item, index) => ( // 新增代码+DesktopGUIAcceptancePanel：渲染空态或证据项；如果没有这行，证据区会空白。
        <li key={`${asText(item.kind, "evidence")}_${index}`} className={asBoolean(item.exists) ? "acceptance-evidence-ready" : "acceptance-evidence-missing"}>{evidenceText(item)}</li> // 新增代码+DesktopGUIAcceptancePanel：显示证据文本和存在状态；如果没有这一行，用户无法判断证据是否落盘。
      ))} {/* 新增代码+DesktopGUIAcceptancePanel：证据项遍历结束；如果没有这行，JSX 表达式不完整。 */}
    </ul> // 新增代码+DesktopGUIAcceptancePanel：证据列表结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIAcceptancePanel：证据列表返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，renderEvidence 到此结束；如果没有这行，证据渲染范围不清楚。

export function AcceptancePanel({ payload = {}, onRunScenario, actionPending = false, lastActionResult = {} }: AcceptancePanelProps): JSX.Element { // 新增代码+DesktopGUIAcceptancePanel：函数段开始，渲染验收控制中心；如果没有这段，右侧检查器没有验收页签内容。
  const panel = asRecord(payload); // 新增代码+DesktopGUIAcceptancePanel：规范化总 payload；如果没有这行，后续字段读取可能访问坏类型。
  const scenarios = asRecordArray(panel.scenarios); // 新增代码+DesktopGUIAcceptancePanel：读取场景列表；如果没有这行，场景卡片没有数据来源。
  const recentRuns = asRecordArray(panel.recent_runs); // 新增代码+DesktopGUIAcceptancePanel：读取最近运行列表；如果没有这行，证据区没有数据来源。
  const controller = asRecord(panel.controller); // 新增代码+DesktopGUIAcceptancePanel：读取控制器状态；如果没有这行，可见终端门禁状态不可见。
  const scenarioCount = asNumber(panel.scenario_count, scenarios.length); // 新增代码+DesktopGUIAcceptancePanel：读取场景总数并兜底列表长度；如果没有这行，摘要数字可能为空。
  const runCount = asNumber(panel.run_count, recentRuns.length); // 新增代码+DesktopGUIAcceptancePanel：读取运行总数；如果没有这行，证据规模不可见。
  const statusDegraded = asBoolean(panel.status_degraded); // 新增代码+DesktopGUIAcceptancePanel：读取降级状态；如果没有这行，读取失败无法提示。
  const safeError = asText(panel.safe_error); // 新增代码+DesktopGUIAcceptancePanel：读取脱敏错误；如果没有这行，降级时没有可见原因。
  const actionResult = asRecord(lastActionResult); // 新增代码+DesktopGUIAcceptancePanel：规范化最近动作结果；如果没有这行，按钮反馈可能访问坏类型。
  const actionMessage = asText(actionResult.message); // 新增代码+DesktopGUIAcceptancePanel：读取最近启动动作说明；如果没有这行，运行请求结果不会显示。
  return ( // 新增代码+DesktopGUIAcceptancePanel：返回验收面板结构；如果没有这行，组件不会输出 UI。
    <section className="planning-panel acceptance-panel" aria-label="验收控制器"> {/* 新增代码+DesktopGUIAcceptancePanel：复用 planning 容器并加验收语义；如果没有这一层，验收页签没有独立定位点。 */}
      <div className="planning-header"> {/* 新增代码+DesktopGUIAcceptancePanel：标题行容器；如果没有这一层，标题和计数布局不稳定。 */}
        <div> {/* 新增代码+DesktopGUIAcceptancePanel：标题文字容器；如果没有这一层，标题和副标题无法纵向排列。 */}
          <h2>验收控制器</h2> {/* 新增代码+DesktopGUIAcceptancePanel：面板标题；如果没有这一行，用户不知道当前页签内容。 */}
          <p>复用 acceptance_controller、controller.ps1 和运行证据目录。</p> {/* 新增代码+DesktopGUIAcceptancePanel：说明复用来源；如果没有这一行，用户无法验收 GUI 没有另造验收系统。 */}
        </div> {/* 新增代码+DesktopGUIAcceptancePanel：标题文字容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{runCount} runs</span> {/* 新增代码+DesktopGUIAcceptancePanel：标题区运行数量；如果没有这一行，证据规模不够醒目。 */}
      </div> {/* 新增代码+DesktopGUIAcceptancePanel：标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="planning-summary" aria-label="验收摘要"> {/* 新增代码+DesktopGUIAcceptancePanel：摘要指标区；如果没有这一层，验收规模需要逐条数。 */}
        <span>{scenarioCount} scenarios</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示场景总数；如果没有这一行，用户看不到接入规模。 */}
        <span>{asBoolean(controller.controller_ps1_exists) ? "controller ready" : "controller missing"}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示 controller.ps1 状态；如果没有这一行，运行按钮失败原因不明显。 */}
        <span>{asBoolean(controller.visible_terminal_required) ? "visible gate" : "gate unknown"}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示可见终端门禁；如果没有这一行，规则十七验收边界不可见。 */}
      </div> {/* 新增代码+DesktopGUIAcceptancePanel：摘要指标区结束；如果没有这一层，JSX 结构不完整。 */}
      {statusDegraded ? <p className="planning-warning">{safeError || "验收状态暂时降级。"}</p> : null} {/* 新增代码+DesktopGUIAcceptancePanel：显示降级提示；如果没有这一行，读取失败会像正常空态。 */}
      {actionMessage ? <p className="harness-control-result">{actionMessage}</p> : null} {/* 新增代码+DesktopGUIAcceptancePanel：显示最近运行请求结果；如果没有这一行，按钮点击缺少反馈。 */}
      <div className="planning-section"> {/* 新增代码+DesktopGUIAcceptancePanel：场景列表区域；如果没有这一层，列表缺少分组边界。 */}
        <div className="planning-section-header"> {/* 新增代码+DesktopGUIAcceptancePanel：场景列表标题行；如果没有这一层，数量和标题无法稳定对齐。 */}
          <h3>Scenarios</h3> {/* 新增代码+DesktopGUIAcceptancePanel：场景列表标题；如果没有这一行，列表内容语义不清。 */}
          <span>{scenarios.length}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示当前渲染数量；如果没有这一行，数量不可见。 */}
        </div> {/* 新增代码+DesktopGUIAcceptancePanel：场景列表标题行结束；如果没有这一层，JSX 结构不完整。 */}
        {scenarios.length === 0 ? ( // 新增代码+DesktopGUIAcceptancePanel：处理无场景空态；如果没有这行，首次启动会显示空白。
          <p className="planning-empty">暂无验收场景。</p> // 新增代码+DesktopGUIAcceptancePanel：空态文案；如果没有这行，用户可能误以为面板坏了。
        ) : scenarios.map((scenario) => { // 新增代码+DesktopGUIAcceptancePanel：遍历场景卡片；如果没有这行，列表不会渲染。
          const scenarioId = asText(scenario.id); // 新增代码+DesktopGUIAcceptancePanel：读取场景 id；如果没有这行，运行按钮没有目标。
          const lastResult = asRecord(scenario.last_result); // 新增代码+DesktopGUIAcceptancePanel：读取最近结果；如果没有这行，场景卡片无法显示上次成败。
          const lastStatus = asText(lastResult.status, "not_run"); // 新增代码+DesktopGUIAcceptancePanel：读取最近状态；如果没有这行，状态徽标没有输入。
          const evidence = asRecordArray(lastResult.evidence); // 新增代码+DesktopGUIAcceptancePanel：读取最近证据；如果没有这行，证据列表无法渲染。
          const canRun = asBoolean(scenario.run_supported) && Boolean(onRunScenario) && scenarioId.length > 0; // 新增代码+DesktopGUIAcceptancePanel：计算运行按钮可用性；如果没有这行，按钮可能对不可运行场景启用。
          const runReason = asText(scenario.run_unavailable_reason, canRun ? "启动真实可见终端验收" : "当前场景无法从 GUI 启动。"); // 新增代码+DesktopGUIAcceptancePanel：读取按钮说明；如果没有这行，禁用按钮没有解释。
          return ( // 新增代码+DesktopGUIAcceptancePanel：返回单条场景卡片；如果没有这行，map 回调没有输出。
            <article className="planning-list-item acceptance-scenario" key={scenarioId || asText(scenario.file_name, "scenario")}> {/* 新增代码+DesktopGUIAcceptancePanel：场景卡片容器；如果没有这一层，场景字段没有层级。 */}
              <strong>{asText(scenario.name, "未命名场景")}</strong> {/* 新增代码+DesktopGUIAcceptancePanel：场景标题；如果没有这一行，用户无法快速识别场景。 */}
              <p>{asText(scenario.prompt_preview, asText(scenario.relative_path, "未记录场景摘要"))}</p> {/* 新增代码+DesktopGUIAcceptancePanel：场景 prompt 或路径摘要；如果没有这一行，用户不知道场景测什么。 */}
              <div className="planning-item-meta"> {/* 新增代码+DesktopGUIAcceptancePanel：元信息行；如果没有这一层，分类、时长、状态会混在正文里。 */}
                <span>{asText(scenario.category, "general")}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示分类；如果没有这一行，场景域不可见。 */}
                <small>{asNumber(scenario.max_seconds, 0)}s</small> {/* 新增代码+DesktopGUIAcceptancePanel：显示最长耗时；如果没有这一行，用户无法预估运行时间。 */}
                <span className={statusClass(lastStatus)}>{lastStatus}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示最近状态；如果没有这一行，最新成败不醒目。 */}
              </div> {/* 新增代码+DesktopGUIAcceptancePanel：元信息行结束；如果没有这一层，JSX 结构不完整。 */}
              {renderEvidence(evidence)} {/* 新增代码+DesktopGUIAcceptancePanel：显示最近证据链接；如果没有这一行，result/events/screenshot 不可见。 */}
              <div className="harness-controls"> {/* 新增代码+DesktopGUIAcceptancePanel：复用控制按钮区；如果没有这一层，运行按钮布局不稳定。 */}
                <button type="button" title={runReason} disabled={!canRun || actionPending} onClick={() => { if (canRun && onRunScenario) { onRunScenario(scenarioId); } }}>运行</button> {/* 新增代码+DesktopGUIAcceptancePanel：运行按钮调用后端 controller.ps1；如果没有这一行，用户无法从 GUI 启动验收。 */}
              </div> {/* 新增代码+DesktopGUIAcceptancePanel：控制按钮区结束；如果没有这一层，JSX 结构不完整。 */}
            </article> // 新增代码+DesktopGUIAcceptancePanel：场景卡片结束；如果没有这行，map 回调语法不完整。
          ); // 新增代码+DesktopGUIAcceptancePanel：场景卡片返回结束；如果没有这行，map 回调语法不完整。
        })} {/* 新增代码+DesktopGUIAcceptancePanel：场景列表条件结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUIAcceptancePanel：场景列表区域结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="planning-section"> {/* 新增代码+DesktopGUIAcceptancePanel：最近运行区域；如果没有这一层，证据历史缺少分组边界。 */}
        <div className="planning-section-header"> {/* 新增代码+DesktopGUIAcceptancePanel：最近运行标题行；如果没有这一层，标题和数量无法稳定对齐。 */}
          <h3>Recent Runs</h3> {/* 新增代码+DesktopGUIAcceptancePanel：最近运行标题；如果没有这一行，证据历史语义不清。 */}
          <span>{recentRuns.length}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示最近运行数量；如果没有这一行，历史规模不可见。 */}
        </div> {/* 新增代码+DesktopGUIAcceptancePanel：最近运行标题行结束；如果没有这一层，JSX 结构不完整。 */}
        {recentRuns.length === 0 ? <p className="planning-empty">暂无运行记录。</p> : recentRuns.slice(0, 4).map((run) => ( // 新增代码+DesktopGUIAcceptancePanel：渲染空态或最近运行；如果没有这行，历史证据会空白。
          <article className="planning-list-item" key={asText(run.id, asText(run.relative_path, "run"))}> {/* 新增代码+DesktopGUIAcceptancePanel：运行卡片容器；如果没有这一层，运行字段会散乱。 */}
            <strong>{asText(run.scenario_name, "scenario")}</strong> {/* 新增代码+DesktopGUIAcceptancePanel：显示运行场景名；如果没有这一行，证据归属不可见。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIAcceptancePanel：运行元信息行；如果没有这一层，状态和时间会混在正文里。 */}
              <span className={statusClass(asText(run.status, "unknown"))}>{asText(run.status, "unknown")}</span> {/* 新增代码+DesktopGUIAcceptancePanel：显示运行状态；如果没有这一行，通过失败不醒目。 */}
              <small>{asText(run.updated_at, "no time")}</small> {/* 新增代码+DesktopGUIAcceptancePanel：显示更新时间；如果没有这一行，证据新旧不可见。 */}
            </div> {/* 新增代码+DesktopGUIAcceptancePanel：运行元信息行结束；如果没有这一层，JSX 结构不完整。 */}
            {renderEvidence(asRecordArray(run.evidence))} {/* 新增代码+DesktopGUIAcceptancePanel：显示运行证据；如果没有这一行，历史 result/events/screenshot 不可见。 */}
          </article> // 新增代码+DesktopGUIAcceptancePanel：运行卡片结束；如果没有这行，JSX 结构不完整。
        ))} {/* 新增代码+DesktopGUIAcceptancePanel：最近运行条件结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUIAcceptancePanel：最近运行区域结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIAcceptancePanel：验收面板结束；如果没有这行，组件返回结构不完整。
  ); // 新增代码+DesktopGUIAcceptancePanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUIAcceptancePanel：函数段结束，AcceptancePanel 到此结束；如果没有这个边界，用户不容易看出面板范围。
