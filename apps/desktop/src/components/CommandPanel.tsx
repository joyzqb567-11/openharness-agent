type CommandPanelProps = { // 新增代码+DesktopGUICommandConsolePanel：类型段开始，定义命令控制台面板入参；如果没有这段，StatusInspector 不知道如何传递命令状态和停止回调。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUICommandConsolePanel：保存 /v2/gui/commands 响应；如果没有这行，面板没有后端事实源。
  onStopCommand?: (commandId: string) => void; // 新增代码+DesktopGUICommandConsolePanel：保存停止命令回调；如果没有这行，停止按钮无法接到 AppShell。
  actionPending?: boolean; // 新增代码+DesktopGUICommandConsolePanel：保存按钮等待态；如果没有这行，用户可能重复点击停止。
  lastActionResult?: Record<string, unknown>; // 新增代码+DesktopGUICommandConsolePanel：保存最近停止请求结果；如果没有这行，按钮反馈只能出现在主线程里。
}; // 新增代码+DesktopGUICommandConsolePanel：类型段结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，把未知值安全收敛成对象；如果没有这段，后端坏 payload 会拖垮右侧栏。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUICommandConsolePanel：只接受普通对象，否则返回空对象；如果没有这行，字段读取会信任任意类型。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，asRecord 到此结束；如果没有这行，函数语法不完整。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，把未知值安全收敛成对象数组；如果没有这段，commands 字段类型漂移会报错。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUICommandConsolePanel：数组逐项收敛，不是数组则返回空；如果没有这行，map 可能访问非数组。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，asRecordArray 到此结束；如果没有这行，函数语法不完整。

function asText(value: unknown, fallback = ""): string { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，安全读取可见文本；如果没有这段，数字/null 字段会直接污染 JSX。
  return typeof value === "string" && value.length > 0 ? value : fallback; // 新增代码+DesktopGUICommandConsolePanel：只接受非空字符串，否则返回兜底；如果没有这行，空字段会显示成 undefined。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，asText 到此结束；如果没有这行，函数语法不完整。

function asNumber(value: unknown): number | null { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，安全读取数字字段；如果没有这段，退出码和统计会混入字符串。
  return typeof value === "number" && Number.isFinite(value) ? value : null; // 新增代码+DesktopGUICommandConsolePanel：只接受有限数字；如果没有这行，NaN 或字符串会进入 UI。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，asNumber 到此结束；如果没有这行，函数语法不完整。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，安全读取布尔字段；如果没有这段，停止按钮可能把任意 truthy 值当许可。
  return value === true; // 新增代码+DesktopGUICommandConsolePanel：只有明确 true 才视为真；如果没有这行，字符串 true 可能误启用危险按钮。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，asBoolean 到此结束；如果没有这行，函数语法不完整。

function statusClass(status: string): string { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，把命令状态映射为 planning 徽标样式；如果没有这段，状态颜色会散落在 JSX。
  if (status === "failed" || status === "unavailable" || status === "not_found") { // 新增代码+DesktopGUICommandConsolePanel：识别失败或不可用状态；如果没有这行，错误状态不会突出。
    return "planning-status-danger"; // 新增代码+DesktopGUICommandConsolePanel：返回危险样式；如果没有这行，失败命令看起来像普通信息。
  } // 新增代码+DesktopGUICommandConsolePanel：错误状态分支结束；如果没有这行，条件块语法不完整。
  if (status === "running" || status === "queued" || status === "pending" || status === "needs_input") { // 新增代码+DesktopGUICommandConsolePanel：识别活跃状态；如果没有这行，运行中命令不会突出。
    return "planning-status-active"; // 新增代码+DesktopGUICommandConsolePanel：返回活跃样式；如果没有这行，用户难以快速找到仍在运行的命令。
  } // 新增代码+DesktopGUICommandConsolePanel：活跃状态分支结束；如果没有这行，条件块语法不完整。
  return "planning-status-muted"; // 新增代码+DesktopGUICommandConsolePanel：其它状态使用普通样式；如果没有这行，函数可能返回 undefined。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，statusClass 到此结束；如果没有这行，函数语法不完整。

function commandTitle(command: Record<string, unknown>): string { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，生成命令卡片标题；如果没有这段，标题兜底逻辑会散在 JSX。
  return asText(command.label, asText(command.command_id, "未命名命令")); // 新增代码+DesktopGUICommandConsolePanel：优先显示 label，再显示 id；如果没有这行，命令列表可能没有主标题。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，commandTitle 到此结束；如果没有这行，函数语法不完整。

function commandTailPreview(command: Record<string, unknown>): string { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，生成命令输出预览；如果没有这段，长 tail 会直接撑满面板。
  const tail = asText(command.tail, "暂无输出。"); // 新增代码+DesktopGUICommandConsolePanel：读取 tail 或空态；如果没有这行，空输出会显示成空白。
  return tail.split("\n").slice(-10).join("\n"); // 新增代码+DesktopGUICommandConsolePanel：只显示最后 10 行；如果没有这行，长任务输出会淹没其它命令。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，commandTailPreview 到此结束；如果没有这行，函数语法不完整。

export function CommandPanel({ payload = {}, onStopCommand, actionPending = false, lastActionResult = {} }: CommandPanelProps): JSX.Element { // 新增代码+DesktopGUICommandConsolePanel：函数段开始，渲染后台命令控制台；如果没有这段，右侧检查器没有命令页签内容。
  const panel = asRecord(payload); // 新增代码+DesktopGUICommandConsolePanel：规范化总 payload；如果没有这行，后续字段读取可能访问坏类型。
  const commands = asRecordArray(panel.commands); // 新增代码+DesktopGUICommandConsolePanel：读取命令列表；如果没有这行，命令卡片没有数据来源。
  const commandCount = asNumber(panel.command_count) ?? commands.length; // 新增代码+DesktopGUICommandConsolePanel：读取命令总数并兜底列表长度；如果没有这行，摘要数字可能为空。
  const runningCount = asNumber(panel.running_command_count) ?? 0; // 新增代码+DesktopGUICommandConsolePanel：读取活跃命令数；如果没有这行，用户无法快速判断是否还有命令在跑。
  const stoppableCount = asNumber(panel.stop_supported_count) ?? 0; // 新增代码+DesktopGUICommandConsolePanel：读取可停止命令数；如果没有这行，GUI 能力边界不明显。
  const statusDegraded = asBoolean(panel.status_degraded); // 新增代码+DesktopGUICommandConsolePanel：读取降级状态；如果没有这行，读取失败无法提示。
  const safeError = asText(panel.safe_error); // 新增代码+DesktopGUICommandConsolePanel：读取脱敏错误；如果没有这行，降级时没有可见原因。
  const actionResult = asRecord(lastActionResult); // 新增代码+DesktopGUICommandConsolePanel：规范化最近动作结果；如果没有这行，按钮反馈可能访问坏类型。
  const actionMessage = asText(actionResult.message); // 新增代码+DesktopGUICommandConsolePanel：读取最近动作说明；如果没有这行，停止请求结果不会显示。
  return ( // 新增代码+DesktopGUICommandConsolePanel：返回命令面板结构；如果没有这行，组件不会输出 UI。
    <section className="planning-panel" aria-label="后台命令"> {/* 新增代码+DesktopGUICommandConsolePanel：复用 planning 面板容器；如果没有这一层，命令页签没有独立语义。 */}
      <div className="planning-header"> {/* 新增代码+DesktopGUICommandConsolePanel：标题行容器；如果没有这一层，标题和计数布局不稳定。 */}
        <div> {/* 新增代码+DesktopGUICommandConsolePanel：标题文字容器；如果没有这一层，标题和副标题无法纵向排列。 */}
          <h2>后台命令</h2> {/* 新增代码+DesktopGUICommandConsolePanel：面板标题；如果没有这一行，用户不知道当前页签内容。 */}
          <p>复用 TaskRegistry 和后台命令输出记录。</p> {/* 新增代码+DesktopGUICommandConsolePanel：说明复用来源；如果没有这一行，用户无法验收没有另造系统。 */}
        </div> {/* 新增代码+DesktopGUICommandConsolePanel：标题文字容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{runningCount}/{commandCount} running</span> {/* 新增代码+DesktopGUICommandConsolePanel：标题区运行中计数；如果没有这一行，长命令状态不够醒目。 */}
      </div> {/* 新增代码+DesktopGUICommandConsolePanel：标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="planning-summary" aria-label="后台命令摘要"> {/* 新增代码+DesktopGUICommandConsolePanel：摘要指标区；如果没有这一层，命令规模需要逐条数。 */}
        <span>{commandCount} commands</span> {/* 新增代码+DesktopGUICommandConsolePanel：显示命令总数；如果没有这一行，用户看不到接入规模。 */}
        <span>{runningCount} active</span> {/* 新增代码+DesktopGUICommandConsolePanel：显示活跃命令数；如果没有这一行，用户不能快速判断是否仍有后台执行。 */}
        <span>{stoppableCount} stoppable</span> {/* 新增代码+DesktopGUICommandConsolePanel：显示可真实停止数；如果没有这一行，停止能力边界不清楚。 */}
      </div> {/* 新增代码+DesktopGUICommandConsolePanel：摘要指标区结束；如果没有这一层，JSX 结构不完整。 */}
      {statusDegraded ? <p className="planning-warning">{safeError || "后台命令状态暂时降级。"}</p> : null} {/* 新增代码+DesktopGUICommandConsolePanel：显示降级提示；如果没有这一行，读取失败会像正常空态。 */}
      {actionMessage ? <p className="harness-control-result">{actionMessage}</p> : null} {/* 新增代码+DesktopGUICommandConsolePanel：显示最近停止请求结果；如果没有这一行，按钮点击缺少反馈。 */}
      <div className="planning-section"> {/* 新增代码+DesktopGUICommandConsolePanel：命令列表区域；如果没有这一层，列表缺少分组边界。 */}
        <div className="planning-section-header"> {/* 新增代码+DesktopGUICommandConsolePanel：命令列表标题行；如果没有这一层，数量和标题无法稳定对齐。 */}
          <h3>Commands</h3> {/* 新增代码+DesktopGUICommandConsolePanel：命令列表标题；如果没有这一行，列表内容语义不清。 */}
          <span>{commands.length}</span> {/* 新增代码+DesktopGUICommandConsolePanel：显示当前渲染数量；如果没有这一行，筛选后数量不可见。 */}
        </div> {/* 新增代码+DesktopGUICommandConsolePanel：命令列表标题行结束；如果没有这一层，JSX 结构不完整。 */}
        {commands.length === 0 ? ( // 新增代码+DesktopGUICommandConsolePanel：处理无命令空态；如果没有这行，首次启动会显示空白。
          <p className="planning-empty">暂无后台命令数据。</p> // 新增代码+DesktopGUICommandConsolePanel：空态文案；如果没有这行，用户可能误以为面板坏了。
        ) : ( // 新增代码+DesktopGUICommandConsolePanel：命令列表非空分支；如果没有这行，条件表达式不完整。
          commands.map((command) => { // 新增代码+DesktopGUICommandConsolePanel：遍历命令卡片；如果没有这行，列表不会渲染。
            const commandId = asText(command.command_id); // 新增代码+DesktopGUICommandConsolePanel：读取命令 id；如果没有这行，按钮和 key 没有目标。
            const status = asText(command.status, "unknown"); // 新增代码+DesktopGUICommandConsolePanel：读取命令状态；如果没有这行，徽标无法显示真实状态。
            const exitCode = asNumber(command.exit_code); // 新增代码+DesktopGUICommandConsolePanel：读取退出码；如果没有这行，完成命令缺少结果线索。
            const canStop = asBoolean(command.can_stop); // 新增代码+DesktopGUICommandConsolePanel：读取真实停止能力；如果没有这行，按钮可能误启用。
            const stopReason = asText(command.stop_unavailable_reason, canStop ? "停止后台命令" : "当前后端不支持从 GUI 真实停止这个命令。"); // 新增代码+DesktopGUICommandConsolePanel：读取禁用原因；如果没有这行，禁用按钮没有解释。
            return ( // 新增代码+DesktopGUICommandConsolePanel：返回单条命令卡片；如果没有这行，map 回调没有输出。
              <div className="planning-list-item" key={commandId || commandTitle(command)}> {/* 新增代码+DesktopGUICommandConsolePanel：命令卡片容器；如果没有这一层，命令字段没有层级。 */}
                <strong>{commandTitle(command)}</strong> {/* 新增代码+DesktopGUICommandConsolePanel：命令标题；如果没有这一行，用户无法快速识别命令。 */}
                <p>{asText(command.command_text, commandId || "未记录命令文本")}</p> {/* 新增代码+DesktopGUICommandConsolePanel：脱敏命令文本；如果没有这一行，用户不知道实际命令。 */}
                <div className="planning-item-meta"> {/* 新增代码+DesktopGUICommandConsolePanel：元信息行；如果没有这一层，状态、cwd、退出码会混在正文里。 */}
                  <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUICommandConsolePanel：状态徽标；如果没有这一行，运行/失败状态不醒目。 */}
                  {asText(command.cwd_display) ? <span>{asText(command.cwd_display)}</span> : null} {/* 新增代码+DesktopGUICommandConsolePanel：显示脱敏 cwd；如果没有这一行，用户不知道命令在哪运行。 */}
                  {exitCode !== null ? <span>exit {exitCode}</span> : null} {/* 新增代码+DesktopGUICommandConsolePanel：显示退出码；如果没有这一行，成功失败需要读输出判断。 */}
                </div> {/* 新增代码+DesktopGUICommandConsolePanel：元信息行结束；如果没有这一层，JSX 结构不完整。 */}
                <pre className="command-tail">{commandTailPreview(command)}</pre> {/* 新增代码+DesktopGUICommandConsolePanel：显示最后几行输出；如果没有这一行，用户看不到终端证据。 */}
                <div className="harness-controls"> {/* 新增代码+DesktopGUICommandConsolePanel：复用控制按钮区；如果没有这一层，停止按钮布局不稳定。 */}
                  <button type="button" title={stopReason} disabled={!canStop || actionPending || !onStopCommand} onClick={() => { if (canStop && onStopCommand) { onStopCommand(commandId); } }}>停止</button> {/* 新增代码+DesktopGUICommandConsolePanel：停止按钮只在真实可停时触发；如果没有这一行，用户无法尝试停止后台命令或会误触假停止。 */}
                </div> {/* 新增代码+DesktopGUICommandConsolePanel：控制按钮区结束；如果没有这一层，JSX 结构不完整。 */}
              </div> // 新增代码+DesktopGUICommandConsolePanel：命令卡片结束；如果没有这行，map 回调语法不完整。
            ); // 新增代码+DesktopGUICommandConsolePanel：命令卡片返回结束；如果没有这行，map 回调语法不完整。
          }) // 新增代码+DesktopGUICommandConsolePanel：命令遍历结束；如果没有这行，map 表达式不完整。
        )} {/* 新增代码+DesktopGUICommandConsolePanel：命令列表条件结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUICommandConsolePanel：命令列表区域结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUICommandConsolePanel：命令面板结束；如果没有这行，组件返回结构不完整。
  ); // 新增代码+DesktopGUICommandConsolePanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUICommandConsolePanel：函数段结束，CommandPanel 到此结束；如果没有这个边界，用户不容易看出面板范围。
