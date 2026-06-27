import { Eye, OctagonX, ShieldCheck } from "lucide-react"; // 新增代码+DesktopGUIComputerUseWorkbench：引入工作台按钮图标；如果没有这行，权限、观察和中止按钮缺少可扫描符号。

type ComputerUsePanelProps = { // 修改代码+DesktopGUIComputerUseWorkbench：定义 Computer Use 工作台入参；如果没有这段，右侧面板无法接收状态和按钮回调。
  panel?: Record<string, unknown>; // 修改代码+DesktopGUIComputerUseWorkbench：保存 Computer Use workbench payload；如果没有这行，模式、目标和最近结果都没有数据来源。
  permissions?: Record<string, unknown>; // 修改代码+DesktopGUIComputerUseWorkbench：保存权限摘要 payload；如果没有这行，Computer Use 面板无法展示待处理权限数量。
  onRequestAccess?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存申请访问回调；如果没有这行，申请权限按钮只能显示不能操作。
  onObserve?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存只读观察回调；如果没有这行，观察按钮无法刷新后端状态。
  onAbort?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存中止回调；如果没有这行，急停按钮无法复用后端 stop 状态机。
  actionPending?: boolean; // 新增代码+DesktopGUIComputerUseWorkbench：保存动作等待态；如果没有这行，用户可能重复点击造成多个 POST。
  lastActionResult?: Record<string, unknown>; // 新增代码+DesktopGUIComputerUseWorkbench：保存最近按钮结果；如果没有这行，点击反馈只能藏在事件流里。
}; // 修改代码+DesktopGUIComputerUseWorkbench：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 修改代码+DesktopGUIComputerUseWorkbench：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会让字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 修改代码+DesktopGUIComputerUseWorkbench：只接受普通对象，否则返回空对象；如果没有这行，前端会信任任意后端类型。
} // 修改代码+DesktopGUIComputerUseWorkbench：函数段结束，asRecord 到此结束；如果没有这个边界，类型防护范围不清楚。

function asText(value: unknown, fallback: string): string { // 修改代码+DesktopGUIComputerUseWorkbench：函数段开始，把任意字段变成安全文本；如果没有这段，undefined/null 会直接暴露在 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 修改代码+DesktopGUIComputerUseWorkbench：优先使用非空字符串，否则使用兜底文案；如果没有这行，状态文案会出现空白。
} // 修改代码+DesktopGUIComputerUseWorkbench：函数段结束，asText 到此结束；如果没有这个边界，文本兜底职责不清楚。

function asTextList(value: unknown): string[] { // 修改代码+DesktopGUIComputerUseWorkbench：函数段开始，把未知列表收敛成字符串列表；如果没有这段，allowed actions 可能把对象渲染成奇怪文本。
  return Array.isArray(value) ? value.map((item) => String(item)).filter((item) => item.length > 0) : []; // 修改代码+DesktopGUIComputerUseWorkbench：只保留非空字符串；如果没有这行，动作列表会混入空值或不可读对象。
} // 修改代码+DesktopGUIComputerUseWorkbench：函数段结束，asTextList 到此结束；如果没有这个边界，列表清洗范围不清楚。

function booleanText(value: unknown, trueText: string, falseText: string): string { // 修改代码+DesktopGUIComputerUseWorkbench：函数段开始，把布尔字段转成中文；如果没有这段，用户要读 true/false 猜含义。
  return value === true ? trueText : falseText; // 修改代码+DesktopGUIComputerUseWorkbench：根据布尔值选择文案；如果没有这行，状态摘要不够直观。
} // 修改代码+DesktopGUIComputerUseWorkbench：函数段结束，booleanText 到此结束；如果没有这个边界，布尔文案逻辑不清楚。

function numberText(value: unknown, fallback = "0"): string { // 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把数字字段转成稳定文本；如果没有这段，NaN 会出现在按钮反馈里。
  return typeof value === "number" && Number.isFinite(value) ? String(value) : fallback; // 新增代码+DesktopGUIComputerUseWorkbench：只接受有限数字；如果没有这行，坏 payload 会污染 UI 文案。
} // 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，numberText 到此结束；如果没有这个边界，数字兜底范围不清楚。

function summaryText(summary: Record<string, unknown>, fallback: string): string { // 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把观察/动作摘要转成一行文本；如果没有这段，面板要展示生硬 JSON。
  const eventType = asText(summary.event_type, ""); // 新增代码+DesktopGUIComputerUseWorkbench：读取事件类型；如果没有这行，用户不知道反馈来自哪个事件。
  const toolName = asText(summary.tool_name, ""); // 新增代码+DesktopGUIComputerUseWorkbench：读取工具名；如果没有这行，Computer Use/MCP 来源不清楚。
  const message = asText(summary.message, ""); // 新增代码+DesktopGUIComputerUseWorkbench：读取后端可读消息；如果没有这行，用户看不到结果说明。
  const action = asText(summary.action, ""); // 新增代码+DesktopGUIComputerUseWorkbench：读取动作名；如果没有这行，最近动作摘要不完整。
  return [eventType, toolName, action, message].filter((item) => item.length > 0).join(" · ") || fallback; // 新增代码+DesktopGUIComputerUseWorkbench：拼成稳定短句并兜底；如果没有这行，空摘要会显示成空白。
} // 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，summaryText 到此结束；如果没有这个边界，摘要格式化范围不清楚。

export function ComputerUsePanel({ panel = {}, permissions = {}, onRequestAccess, onObserve, onAbort, actionPending = false, lastActionResult = {} }: ComputerUsePanelProps): JSX.Element { // 修改代码+DesktopGUIComputerUseWorkbench：函数段开始，渲染 Computer Use 状态、目标、授权、观察和中止；如果没有这段，桌面自动化无法成为真实 GUI 工作台。
  const computerUse = asRecord(panel); // 修改代码+DesktopGUIComputerUseWorkbench：读取 Computer Use 面板对象；如果没有这行，后续状态都没有安全来源。
  const permissionPanel = asRecord(permissions); // 修改代码+DesktopGUIComputerUseWorkbench：读取权限摘要对象；如果没有这行，待处理权限数量无法展示。
  const lock = asRecord(computerUse.lock); // 修改代码+DesktopGUIComputerUseWorkbench：读取锁状态；如果没有这行，用户不知道桌面控制是否被占用。
  const abort = asRecord(computerUse.abort); // 修改代码+DesktopGUIComputerUseWorkbench：读取急停状态；如果没有这行，用户无法确认是否有中断请求。
  const targetState = asRecord(computerUse.target_app_state); // 新增代码+DesktopGUIComputerUseWorkbench：读取目标应用状态；如果没有这行，用户看不到当前桌面上下文。
  const screenshot = asRecord(targetState.last_screenshot); // 新增代码+DesktopGUIComputerUseWorkbench：读取最近截图尺寸；如果没有这行，观察状态缺少视觉证据尺度。
  const lastObservation = asRecord(computerUse.last_observation); // 新增代码+DesktopGUIComputerUseWorkbench：读取最近观察摘要；如果没有这行，观察按钮结果不可见。
  const lastBackendAction = asRecord(computerUse.last_action_result); // 新增代码+DesktopGUIComputerUseWorkbench：读取后端最近动作摘要；如果没有这行，事件流里的动作结果不会进入工作台。
  const lastButtonResult = asRecord(lastActionResult); // 新增代码+DesktopGUIComputerUseWorkbench：读取前端最近按钮结果；如果没有这行，点击后不会马上显示反馈。
  const mode = asText(computerUse.mode, "off"); // 修改代码+DesktopGUIComputerUseWorkbench：读取 Computer Use 模式；如果没有这行，面板无法显示当前权限范围。
  const permissionMode = asText(computerUse.permission_mode, "manual"); // 修改代码+DesktopGUIComputerUseWorkbench：读取权限模式；如果没有这行，用户不知道危险操作是否需要确认。
  const pendingPermissions = Number(permissionPanel.pending_count ?? 0); // 修改代码+DesktopGUIComputerUseWorkbench：读取待处理权限数量；如果没有这行，用户要去别处找权限状态。
  const allowedActions = asTextList(computerUse.allowed_action_classes).slice(0, 6); // 修改代码+DesktopGUIComputerUseWorkbench：读取并限制可用动作摘要；如果没有这行，长列表会挤爆右侧面板。
  const degraded = computerUse.degraded === true || computerUse.status_degraded === true; // 修改代码+DesktopGUIComputerUseWorkbench：计算是否降级；如果没有这行，Computer Use 状态读取失败时 UI 会假装正常。
  const disabled = mode === "off" || mode === "unavailable"; // 修改代码+DesktopGUIComputerUseWorkbench：计算是否安全禁用；如果没有这行，用户难以判断桌面控制是否可用。
  const safeError = asText(computerUse.safe_error, "Computer Use 暂未启用。"); // 修改代码+DesktopGUIComputerUseWorkbench：读取安全错误文案；如果没有这行，降级提示可能泄露原始异常。
  const abortDisabled = actionPending || onAbort === undefined || computerUse.abort_available !== true; // 新增代码+DesktopGUIComputerUseWorkbench：计算中止按钮是否禁用；如果没有这行，用户可能点一个没有后端支持的急停。
  return ( // 修改代码+DesktopGUIComputerUseWorkbench：返回 Computer Use 工作台结构；如果没有这行，组件不会输出 UI。
    <section className="computer-use-panel" aria-label="Computer Use 工作台"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义 Computer Use 工作台区域；如果没有这行，右侧栏缺少桌面自动化操作分区。 */}
      <div className="computer-use-header"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义标题区；如果没有这行，模式标签和标题会混在内容里。 */}
        <h2>Computer Use</h2> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示面板标题；如果没有这行，用户不知道这块状态的用途。 */}
        <span className={disabled ? "computer-use-state computer-use-state-muted" : "computer-use-state"}>{mode}</span> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示当前模式标签；如果没有这行，用户看不到桌面控制范围。 */}
      </div> {/* 修改代码+DesktopGUIComputerUseWorkbench：标题区结束；如果没有这行，JSX 结构不完整。 */}
      {degraded || disabled ? <p className="computer-use-banner">{safeError}</p> : null} {/* 修改代码+DesktopGUIComputerUseWorkbench：显示降级或禁用提示；如果没有这行，不可用状态会缺少解释。 */}
      <div className="computer-use-workbench-controls" aria-label="Computer Use 操作"> {/* 新增代码+DesktopGUIComputerUseWorkbench：定义三个工作台按钮容器；如果没有这行，授权、观察和中止操作会散乱。 */}
        <button className="computer-use-workbench-button" type="button" title="申请只读观察权限" disabled={actionPending || onRequestAccess === undefined} onClick={onRequestAccess}> {/* 新增代码+DesktopGUIComputerUseWorkbench：渲染申请访问按钮；如果没有这行，用户无法从 GUI 触发安全授权路径。 */}
          <ShieldCheck size={14} aria-hidden="true" /> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示申请访问图标；如果没有这行，紧凑按钮可扫描性下降。 */}
          <span>申请权限</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示申请按钮文字；如果没有这行，小白用户不知道按钮含义。 */}
        </button> {/* 新增代码+DesktopGUIComputerUseWorkbench：申请按钮结束；如果没有这行，JSX 结构不完整。 */}
        <button className="computer-use-workbench-button" type="button" title="刷新只读观察状态" disabled={actionPending || onObserve === undefined} onClick={onObserve}> {/* 新增代码+DesktopGUIComputerUseWorkbench：渲染观察按钮；如果没有这行，用户无法主动刷新观察摘要。 */}
          <Eye size={14} aria-hidden="true" /> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示观察图标；如果没有这行，按钮语义不够直观。 */}
          <span>观察</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示观察按钮文字；如果没有这行，小白用户不知道按钮含义。 */}
        </button> {/* 新增代码+DesktopGUIComputerUseWorkbench：观察按钮结束；如果没有这行，JSX 结构不完整。 */}
        <button className="computer-use-workbench-button computer-use-workbench-button-danger" type="button" title="中止 Computer Use" disabled={abortDisabled} onClick={onAbort}> {/* 新增代码+DesktopGUIComputerUseWorkbench：渲染中止按钮；如果没有这行，用户无法从 GUI 触发 stop/abort。 */}
          <OctagonX size={14} aria-hidden="true" /> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示中止图标；如果没有这行，危险动作按钮不够醒目。 */}
          <span>中止</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示中止按钮文字；如果没有这行，小白用户不知道按钮含义。 */}
        </button> {/* 新增代码+DesktopGUIComputerUseWorkbench：中止按钮结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopGUIComputerUseWorkbench：按钮容器结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-target"> {/* 新增代码+DesktopGUIComputerUseWorkbench：定义目标应用状态块；如果没有这行，桌面上下文仍然不可见。 */}
        <strong>目标状态</strong> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示目标状态标题；如果没有这行，用户不知道下面数字代表什么。 */}
        <span>{asText(targetState.selected_display, "未固定显示器")}</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示选中显示器；如果没有这行，多屏上下文不可见。 */}
        <small>{numberText(screenshot.width)}×{numberText(screenshot.height)} · 已授权应用 {numberText(targetState.allowed_app_count)} 个 · 隐藏窗口 {numberText(targetState.hidden_window_count)} 个</small> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示截图尺寸、授权数和隐藏窗口数；如果没有这行，用户无法判断观察和 cleanup 状态。 */}
      </div> {/* 新增代码+DesktopGUIComputerUseWorkbench：目标状态块结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-row"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义锁状态行；如果没有这行，锁摘要没有稳定布局。 */}
        <strong>锁</strong> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示锁字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{lock.locked === true ? `已锁定：${asText(lock.owner, "未知持有者")}` : "未锁定"}</span> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示锁拥有者或未锁定；如果没有这行，用户无法判断是否可接管桌面。 */}
        <small>{asText(lock.safe_state, "unlocked")}</small> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示安全锁状态；如果没有这行，锁状态缺少机器可读摘要。 */}
      </div> {/* 修改代码+DesktopGUIComputerUseWorkbench：锁状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-row"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义急停状态行；如果没有这行，急停摘要没有稳定布局。 */}
        <strong>急停</strong> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示急停字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{booleanText(abort.requested, "正在中断", "未触发")}</span> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示急停是否触发；如果没有这行，用户无法判断桌面操作是否正在停止。 */}
        <small>{booleanText(abort.terminal_abort_fallback, "终端兜底可用", "终端兜底未知")}</small> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示终端急停兜底；如果没有这行，用户看不到安全后备路径。 */}
      </div> {/* 修改代码+DesktopGUIComputerUseWorkbench：急停状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-row"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义权限状态行；如果没有这行，权限摘要没有稳定布局。 */}
        <strong>权限</strong> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示权限字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{permissionMode}</span> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示权限模式；如果没有这行，用户不知道操作是否需要确认。 */}
        <small>{pendingPermissions} 个待处理</small> {/* 修改代码+DesktopGUIComputerUseWorkbench：显示待处理权限数量；如果没有这行，用户看不到阻塞点。 */}
      </div> {/* 修改代码+DesktopGUIComputerUseWorkbench：权限状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-actions"> {/* 修改代码+DesktopGUIComputerUseWorkbench：定义允许动作摘要区；如果没有这行，可用动作会散落成难扫读文本。 */}
        {allowedActions.length > 0 ? allowedActions.map((action) => <span key={action}>{action}</span>) : <span>不可用</span>} {/* 修改代码+DesktopGUIComputerUseWorkbench：渲染动作 chip 或不可用；如果没有这行，用户不知道桌面控制支持哪些动作。 */}
      </div> {/* 修改代码+DesktopGUIComputerUseWorkbench：允许动作摘要区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-evidence"> {/* 新增代码+DesktopGUIComputerUseWorkbench：定义证据区；如果没有这行，观察和动作结果仍然不可见。 */}
        <strong>最近观察</strong> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示最近观察标题；如果没有这行，用户不知道这条摘要来源。 */}
        <span>{summaryText(lastObservation, "暂无观察记录")}</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示最近观察摘要；如果没有这行，观察按钮结果不可见。 */}
      </div> {/* 新增代码+DesktopGUIComputerUseWorkbench：最近观察证据块结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-evidence"> {/* 新增代码+DesktopGUIComputerUseWorkbench：定义最近动作结果证据区；如果没有这行，动作反馈没有稳定布局。 */}
        <strong>最近动作</strong> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示最近动作标题；如果没有这行，用户不知道这条摘要来源。 */}
        <span>{summaryText(lastBackendAction, "暂无动作结果")}</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示后端最近动作摘要；如果没有这行，事件流反馈不可见。 */}
      </div> {/* 新增代码+DesktopGUIComputerUseWorkbench：最近动作证据块结束；如果没有这行，JSX 结构不完整。 */}
      {Object.keys(lastButtonResult).length > 0 ? ( // 新增代码+DesktopGUIComputerUseWorkbench：只有点击过按钮才显示按钮反馈；如果没有这行，初始空态会多一块噪音。
        <div className="computer-use-result"> {/* 新增代码+DesktopGUIComputerUseWorkbench：定义按钮结果块；如果没有这行，点击反馈没有稳定样式。 */}
          <strong>{asText(lastButtonResult.action, "Computer Use")}</strong> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示最近按钮动作；如果没有这行，用户不知道反馈对应哪个按钮。 */}
          <span>{asText(lastButtonResult.message, asText(lastButtonResult.status, "已提交"))}</span> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示按钮结果说明；如果没有这行，点击后没有肉眼反馈。 */}
          <small>低层事件：{numberText(lastButtonResult.low_level_event_count)}</small> {/* 新增代码+DesktopGUIComputerUseWorkbench：显示低层事件数；如果没有这行，安全验收无法肉眼确认没有鼠标键盘动作。 */}
        </div> // 新增代码+DesktopGUIComputerUseWorkbench：按钮结果块结束；如果没有这行，JSX 结构不完整。
      ) : null} {/* 新增代码+DesktopGUIComputerUseWorkbench：按钮结果条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 修改代码+DesktopGUIComputerUseWorkbench：Computer Use 工作台结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUIComputerUseWorkbench：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUIComputerUseWorkbench：函数段结束，ComputerUsePanel 到此结束；如果没有这个边界，初学者不容易看出面板范围。
