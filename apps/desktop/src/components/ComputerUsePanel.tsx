type ComputerUsePanelProps = { // 新增代码+DesktopComputerUsePanel：定义 Computer Use 面板入参；如果没有这段，右侧面板无法接收后端运行时状态。
  panel?: Record<string, unknown>; // 新增代码+DesktopComputerUsePanel：保存 Computer Use V2 payload；如果没有这行，锁、急停和模式都没有数据来源。
  permissions?: Record<string, unknown>; // 新增代码+DesktopComputerUsePanel：保存权限摘要 payload；如果没有这行，Computer Use 面板无法展示待处理权限数量。
}; // 新增代码+DesktopComputerUsePanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopComputerUsePanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会让字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopComputerUsePanel：只接受普通对象，否则返回空对象；如果没有这行，前端会信任任意后端类型。
} // 新增代码+DesktopComputerUsePanel：函数段结束，asRecord 到此结束；如果没有这个边界，类型防护范围不清楚。

function asText(value: unknown, fallback: string): string { // 新增代码+DesktopComputerUsePanel：函数段开始，把任意字段变成安全文本；如果没有这段，undefined/null 会直接暴露在 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopComputerUsePanel：优先使用非空字符串，否则使用兜底文案；如果没有这行，状态文案会出现空白。
} // 新增代码+DesktopComputerUsePanel：函数段结束，asText 到此结束；如果没有这个边界，文本兜底职责不清楚。

function asTextList(value: unknown): string[] { // 新增代码+DesktopComputerUsePanel：函数段开始，把未知列表收敛成字符串列表；如果没有这段，allowed actions 可能把对象渲染成奇怪文本。
  return Array.isArray(value) ? value.map((item) => String(item)).filter((item) => item.length > 0) : []; // 新增代码+DesktopComputerUsePanel：只保留非空字符串；如果没有这行，动作列表会混入空值或不可读对象。
} // 新增代码+DesktopComputerUsePanel：函数段结束，asTextList 到此结束；如果没有这个边界，列表清洗范围不清楚。

function booleanText(value: unknown, trueText: string, falseText: string): string { // 新增代码+DesktopComputerUsePanel：函数段开始，把布尔字段转成中文；如果没有这段，用户要读 true/false 猜含义。
  return value === true ? trueText : falseText; // 新增代码+DesktopComputerUsePanel：根据布尔值选择文案；如果没有这行，状态摘要不够直观。
} // 新增代码+DesktopComputerUsePanel：函数段结束，booleanText 到此结束；如果没有这个边界，布尔文案逻辑不清楚。

export function ComputerUsePanel({ panel = {}, permissions = {} }: ComputerUsePanelProps): JSX.Element { // 新增代码+DesktopComputerUsePanel：函数段开始，渲染 Computer Use 锁、急停、权限和动作能力；如果没有这段，桌面自动化风险状态不可见。
  const computerUse = asRecord(panel); // 新增代码+DesktopComputerUsePanel：读取 Computer Use 面板对象；如果没有这行，后续状态都没有安全来源。
  const permissionPanel = asRecord(permissions); // 新增代码+DesktopComputerUsePanel：读取权限摘要对象；如果没有这行，待处理权限数量无法展示。
  const lock = asRecord(computerUse.lock); // 新增代码+DesktopComputerUsePanel：读取锁状态；如果没有这行，用户不知道桌面控制是否被占用。
  const abort = asRecord(computerUse.abort); // 新增代码+DesktopComputerUsePanel：读取急停状态；如果没有这行，用户无法确认是否有中断请求。
  const mode = asText(computerUse.mode, "off"); // 新增代码+DesktopComputerUsePanel：读取 Computer Use 模式；如果没有这行，面板无法显示当前权限范围。
  const permissionMode = asText(computerUse.permission_mode, "interactive"); // 新增代码+DesktopComputerUsePanel：读取权限模式；如果没有这行，用户不知道危险操作是否需要确认。
  const pendingPermissions = Number(permissionPanel.pending_count ?? 0); // 新增代码+DesktopComputerUsePanel：读取待处理权限数量；如果没有这行，用户要去别处找权限状态。
  const allowedActions = asTextList(computerUse.allowed_action_classes).slice(0, 4); // 新增代码+DesktopComputerUsePanel：读取并限制可用动作摘要；如果没有这行，长列表会挤爆右侧面板。
  const degraded = computerUse.status_degraded === true; // 新增代码+DesktopComputerUsePanel：计算是否降级；如果没有这行，Computer Use 状态读取失败时 UI 会假装正常。
  const disabled = mode === "off" || mode === "unavailable"; // 新增代码+DesktopComputerUsePanel：计算是否安全禁用；如果没有这行，用户难以判断桌面控制是否可用。
  const safeError = asText(computerUse.safe_error, "Computer Use 暂未启用。"); // 新增代码+DesktopComputerUsePanel：读取安全错误文案；如果没有这行，降级提示可能泄露原始异常。
  return ( // 新增代码+DesktopComputerUsePanel：返回 Computer Use 面板结构；如果没有这行，组件不会输出 UI。
    <section className="computer-use-panel" aria-label="Computer Use 状态"> {/* 新增代码+DesktopComputerUsePanel：定义 Computer Use 状态区；如果没有这行，右侧栏缺少桌面自动化风险分区。 */}
      <div className="computer-use-header"> {/* 新增代码+DesktopComputerUsePanel：定义标题区；如果没有这行，模式标签和标题会混在内容里。 */}
        <h2>Computer Use</h2> {/* 新增代码+DesktopComputerUsePanel：显示面板标题；如果没有这行，用户不知道这块状态的用途。 */}
        <span className={disabled ? "computer-use-state computer-use-state-muted" : "computer-use-state"}>{mode}</span> {/* 新增代码+DesktopComputerUsePanel：显示当前模式标签；如果没有这行，用户看不到桌面控制范围。 */}
      </div> {/* 新增代码+DesktopComputerUsePanel：标题区结束；如果没有这行，JSX 结构不完整。 */}
      {degraded || disabled ? <p className="computer-use-banner">{safeError}</p> : null} {/* 新增代码+DesktopComputerUsePanel：显示降级或禁用提示；如果没有这行，不可用状态会缺少解释。 */}
      <div className="computer-use-row"> {/* 新增代码+DesktopComputerUsePanel：定义锁状态行；如果没有这行，锁摘要没有稳定布局。 */}
        <strong>锁</strong> {/* 新增代码+DesktopComputerUsePanel：显示锁字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{lock.locked === true ? `已锁定：${asText(lock.owner, "未知持有者")}` : "未锁定"}</span> {/* 新增代码+DesktopComputerUsePanel：显示锁拥有者或未锁定；如果没有这行，用户无法判断是否可接管桌面。 */}
        <small>{asText(lock.safe_state, "unlocked")}</small> {/* 新增代码+DesktopComputerUsePanel：显示安全锁状态；如果没有这行，锁状态缺少机器可读摘要。 */}
      </div> {/* 新增代码+DesktopComputerUsePanel：锁状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-row"> {/* 新增代码+DesktopComputerUsePanel：定义急停状态行；如果没有这行，急停摘要没有稳定布局。 */}
        <strong>急停</strong> {/* 新增代码+DesktopComputerUsePanel：显示急停字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{booleanText(abort.requested, "正在中断", "未触发")}</span> {/* 新增代码+DesktopComputerUsePanel：显示急停是否触发；如果没有这行，用户无法判断桌面操作是否正在停止。 */}
        <small>{booleanText(abort.terminal_abort_fallback, "终端兜底可用", "终端兜底未知")}</small> {/* 新增代码+DesktopComputerUsePanel：显示终端急停兜底；如果没有这行，用户看不到安全后备路径。 */}
      </div> {/* 新增代码+DesktopComputerUsePanel：急停状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-row"> {/* 新增代码+DesktopComputerUsePanel：定义权限状态行；如果没有这行，权限摘要没有稳定布局。 */}
        <strong>权限</strong> {/* 新增代码+DesktopComputerUsePanel：显示权限字段名；如果没有这行，用户不知道该值含义。 */}
        <span>{permissionMode}</span> {/* 新增代码+DesktopComputerUsePanel：显示权限模式；如果没有这行，用户不知道操作是否需要确认。 */}
        <small>{pendingPermissions} 个待处理</small> {/* 新增代码+DesktopComputerUsePanel：显示待处理权限数量；如果没有这行，用户看不到阻塞点。 */}
      </div> {/* 新增代码+DesktopComputerUsePanel：权限状态行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="computer-use-actions"> {/* 新增代码+DesktopComputerUsePanel：定义允许动作摘要区；如果没有这行，可用动作会散落成难扫读文本。 */}
        {allowedActions.length > 0 ? allowedActions.map((action) => <span key={action}>{action}</span>) : <span>不可用</span>} {/* 新增代码+DesktopComputerUsePanel：渲染动作 chip 或不可用；如果没有这行，用户不知道桌面控制支持哪些动作。 */}
      </div> {/* 新增代码+DesktopComputerUsePanel：允许动作摘要区结束；如果没有这行，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopComputerUsePanel：Computer Use 状态区结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopComputerUsePanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopComputerUsePanel：函数段结束，ComputerUsePanel 到此结束；如果没有这个边界，初学者不容易看出面板范围。
