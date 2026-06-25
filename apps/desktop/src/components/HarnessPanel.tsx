import { AlertTriangle, ListChecks, Pause, Play } from "lucide-react"; // 新增代码+DesktopGUIHarnessPanel：引入长任务、警告和控制按钮图标；如果没有这行，右侧任务面板缺少可扫描符号。

type HarnessPanelProps = { // 新增代码+DesktopGUIHarnessPanel：类型段开始，定义 HarnessPanel 入参；如果没有这段，调用方不知道要传哪些状态和回调。
  payload: Record<string, unknown>; // 新增代码+DesktopGUIHarnessPanel：保存后端 Harness 状态 payload；如果没有这行，面板没有事实源。
  onPause?: () => void; // 新增代码+DesktopGUIHarnessPanel：保存可选暂停回调；如果没有这行，后端支持暂停时按钮无法接线。
  onResume?: () => void; // 新增代码+DesktopGUIHarnessPanel：保存可选恢复回调；如果没有这行，后端支持恢复时按钮无法接线。
  controlPending?: boolean; // 新增代码+DesktopGUIHarnessPanel：保存控制请求是否进行中；如果没有这行，按钮无法避免重复点击。
}; // 新增代码+DesktopGUIHarnessPanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIHarnessPanel：函数段开始，把未知值收敛成对象；如果没有这段，坏 payload 会导致字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIHarnessPanel：只接受普通对象；如果没有这行，数组或 null 会被误当对象。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，asRecord 到此结束；如果没有这行，函数语法不完整。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIHarnessPanel：函数段开始，把未知值收敛成对象数组；如果没有这段，队列和 checkpoint 渲染会信任坏类型。
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null && !Array.isArray(item)) : []; // 新增代码+DesktopGUIHarnessPanel：只保留普通对象项；如果没有这行，字符串项会让渲染读取字段时报错。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，asRecordArray 到此结束；如果没有这行，函数语法不完整。

function textFrom(value: unknown, fallback = ""): string { // 新增代码+DesktopGUIHarnessPanel：函数段开始，安全读取短文本；如果没有这段，undefined/null 会显示成奇怪字符串。
  const text = typeof value === "string" || typeof value === "number" ? String(value) : fallback; // 新增代码+DesktopGUIHarnessPanel：只接受字符串或数字；如果没有这行，对象会被渲染成 [object Object]。
  return text.trim().length > 0 ? text.trim() : fallback; // 新增代码+DesktopGUIHarnessPanel：空文本时使用兜底；如果没有这行，面板会出现空标签。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，textFrom 到此结束；如果没有这行，函数语法不完整。

function boolFrom(value: unknown): boolean { // 新增代码+DesktopGUIHarnessPanel：函数段开始，安全读取布尔值；如果没有这段，能力开关可能被字符串误判。
  return value === true; // 新增代码+DesktopGUIHarnessPanel：只把 true 当作真；如果没有这行，"false" 也可能被当作可用控制。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，boolFrom 到此结束；如果没有这行，函数语法不完整。

function itemKey(item: Record<string, unknown>, index: number): string { // 新增代码+DesktopGUIHarnessPanel：函数段开始，生成列表 key；如果没有这段，React 列表 key 会不稳定。
  return textFrom(item.id ?? item.sequence ?? item.checkpoint ?? item.stage_name, `harness_item_${index}`); // 新增代码+DesktopGUIHarnessPanel：优先使用后端字段再兜底索引；如果没有这行，重复渲染时可能产生 key 警告。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，itemKey 到此结束；如果没有这行，函数语法不完整。

export function HarnessPanel({ payload, onPause, onResume, controlPending = false }: HarnessPanelProps): JSX.Element { // 新增代码+DesktopGUIHarnessPanel：函数段开始，渲染长任务 Harness 状态；如果没有这段，右侧任务页签没有内容。
  const activeGoal = asRecord(payload.active_goal); // 新增代码+DesktopGUIHarnessPanel：读取当前目标对象；如果没有这行，面板无法展示 active goal。
  const controls = asRecord(payload.controls); // 新增代码+DesktopGUIHarnessPanel：读取后端控制能力；如果没有这行，按钮显示条件没有事实来源。
  const queue = asRecordArray(payload.queue); // 新增代码+DesktopGUIHarnessPanel：读取队列条目；如果没有这行，等待任务不可见。
  const checkpoints = asRecordArray(payload.checkpoints); // 新增代码+DesktopGUIHarnessPanel：读取 checkpoint 时间线；如果没有这行，阶段恢复点不可见。
  const status = textFrom(activeGoal.status, "idle"); // 新增代码+DesktopGUIHarnessPanel：读取目标状态；如果没有这行，标题行没有状态标签。
  const prompt = textFrom(activeGoal.prompt, "暂无活跃长任务。"); // 新增代码+DesktopGUIHarnessPanel：读取目标 prompt；如果没有这行，用户不知道当前目标。
  const runningStep = textFrom(activeGoal.running_step, "等待下一步"); // 新增代码+DesktopGUIHarnessPanel：读取当前步骤；如果没有这行，面板无法显示执行位置。
  const lastProgress = textFrom(payload.last_progress, "暂无进展记录。"); // 新增代码+DesktopGUIHarnessPanel：读取最近进展；如果没有这行，空 checkpoint 时缺少上下文。
  const blockedReason = textFrom(payload.blocked_reason, ""); // 新增代码+DesktopGUIHarnessPanel：读取阻塞原因；如果没有这行，警告块不知道是否显示。
  const safeError = textFrom(payload.safe_error, ""); // 新增代码+DesktopGUIHarnessPanel：读取安全错误；如果没有这行，降级状态没有可读提示。
  const pauseSupported = boolFrom(controls.pause_supported); // 新增代码+DesktopGUIHarnessPanel：读取暂停能力开关；如果没有这行，按钮可能误显示。
  const resumeSupported = boolFrom(controls.resume_supported); // 新增代码+DesktopGUIHarnessPanel：读取恢复能力开关；如果没有这行，按钮可能误显示。
  const showControls = pauseSupported || resumeSupported; // 新增代码+DesktopGUIHarnessPanel：计算是否显示控制区；如果没有这行，未支持能力也可能占空间。
  return ( // 新增代码+DesktopGUIHarnessPanel：返回面板 JSX；如果没有这行，组件不会输出 UI。
    <section className="harness-panel" aria-label="长任务 Harness"> {/* 新增代码+DesktopGUIHarnessPanel：面板语义容器；如果没有这一层，右侧任务区域缺少可访问标签。 */}
      <div className="harness-header"> {/* 新增代码+DesktopGUIHarnessPanel：标题行容器；如果没有这一层，标题和状态标签无法稳定对齐。 */}
        <h2><ListChecks size={14} aria-hidden="true" /> 长任务</h2> {/* 新增代码+DesktopGUIHarnessPanel：标题和图标；如果没有这一行，用户不容易识别当前页签内容。 */}
        <span className={`harness-status harness-status-${status}`}>{status}</span> {/* 新增代码+DesktopGUIHarnessPanel：状态标签；如果没有这一行，active goal 生命周期不可见。 */}
      </div> {/* 新增代码+DesktopGUIHarnessPanel：标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {safeError ? <p className="harness-warning"><AlertTriangle size={13} aria-hidden="true" /> {safeError}</p> : null} {/* 新增代码+DesktopGUIHarnessPanel：显示安全降级提示；如果没有这一行，快照读取失败会静默。 */}
      {blockedReason ? <p className="harness-warning"><AlertTriangle size={13} aria-hidden="true" /> {blockedReason}</p> : null} {/* 新增代码+DesktopGUIHarnessPanel：显示阻塞原因；如果没有这一行，任务卡住时用户只能猜。 */}
      <div className="harness-goal"> {/* 新增代码+DesktopGUIHarnessPanel：当前目标容器；如果没有这一层，prompt 和步骤会混进列表。 */}
        <span>当前目标</span> {/* 新增代码+DesktopGUIHarnessPanel：目标字段名；如果没有这一行，主文本语义不清。 */}
        <strong>{prompt}</strong> {/* 新增代码+DesktopGUIHarnessPanel：目标正文；如果没有这一行，用户看不到长任务目的。 */}
        <small>{runningStep} · {lastProgress}</small> {/* 新增代码+DesktopGUIHarnessPanel：步骤和进展摘要；如果没有这一行，任务进度不可扫描。 */}
        {showControls ? ( // 新增代码+DesktopGUIHarnessPanel：仅在后端支持时渲染控制按钮；如果没有这行，未支持动作会误导用户。
          <div className="harness-controls"> {/* 新增代码+DesktopGUIHarnessPanel：控制按钮容器；如果没有这一层，按钮布局不稳定。 */}
            {pauseSupported ? <button type="button" onClick={onPause} disabled={controlPending}><Pause size={13} aria-hidden="true" /> 暂停</button> : null} {/* 新增代码+DesktopGUIHarnessPanel：暂停按钮；如果没有这一行，后端支持暂停时用户无法操作。 */}
            {resumeSupported ? <button type="button" onClick={onResume} disabled={controlPending}><Play size={13} aria-hidden="true" /> 恢复</button> : null} {/* 新增代码+DesktopGUIHarnessPanel：恢复按钮；如果没有这一行，后端支持恢复时用户无法操作。 */}
          </div> // 新增代码+DesktopGUIHarnessPanel：控制按钮容器结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 新增代码+DesktopGUIHarnessPanel：控制区条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUIHarnessPanel：当前目标容器结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="harness-section"> {/* 新增代码+DesktopGUIHarnessPanel：队列区容器；如果没有这一层，队列和 checkpoint 难以区分。 */}
        <div className="harness-section-title"><span>队列</span><small>{queue.length}</small></div> {/* 新增代码+DesktopGUIHarnessPanel：队列标题和数量；如果没有这一行，用户看不到排队规模。 */}
        {queue.length === 0 ? <p className="harness-empty">没有等待中的条目。</p> : queue.map((item, index) => ( // 新增代码+DesktopGUIHarnessPanel：队列空态或列表；如果没有这行，队列不会渲染。
          <div className="harness-queue-row" key={itemKey(item, index)}> {/* 新增代码+DesktopGUIHarnessPanel：单条队列项；如果没有这一层，状态和摘要无法对齐。 */}
            <strong>{textFrom(item.status, "queued")}</strong> {/* 新增代码+DesktopGUIHarnessPanel：队列状态；如果没有这一行，用户不知道条目生命周期。 */}
            <span>{textFrom(item.summary, textFrom(item.kind, "任务"))}</span> {/* 新增代码+DesktopGUIHarnessPanel：队列摘要；如果没有这一行，用户不知道等待内容。 */}
          </div> // 新增代码+DesktopGUIHarnessPanel：单条队列项结束；如果没有这行，JSX 结构不完整。
        ))} {/* 新增代码+DesktopGUIHarnessPanel：队列渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUIHarnessPanel：队列区容器结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="harness-section"> {/* 新增代码+DesktopGUIHarnessPanel：checkpoint 区容器；如果没有这一层，恢复点时间线没有边界。 */}
        <div className="harness-section-title"><span>Checkpoints</span><small>{checkpoints.length}</small></div> {/* 新增代码+DesktopGUIHarnessPanel：checkpoint 标题和数量；如果没有这一行，用户看不到恢复点规模。 */}
        {checkpoints.length === 0 ? <p className="harness-empty">暂无 checkpoint。</p> : checkpoints.map((item, index) => ( // 新增代码+DesktopGUIHarnessPanel：checkpoint 空态或列表；如果没有这行，恢复点不会渲染。
          <div className="harness-checkpoint" key={itemKey(item, index)}> {/* 新增代码+DesktopGUIHarnessPanel：单条 checkpoint；如果没有这一层，阶段名和摘要无法分组。 */}
            <strong>{textFrom(item.stage_name, `checkpoint ${index + 1}`)}</strong> {/* 新增代码+DesktopGUIHarnessPanel：阶段名；如果没有这一行，用户不知道恢复点属于哪一步。 */}
            <span>{textFrom(item.checkpoint, "checkpoint")}</span> {/* 新增代码+DesktopGUIHarnessPanel：checkpoint 摘要；如果没有这一行，恢复证据不可见。 */}
          </div> // 新增代码+DesktopGUIHarnessPanel：单条 checkpoint 结束；如果没有这行，JSX 结构不完整。
        ))} {/* 新增代码+DesktopGUIHarnessPanel：checkpoint 渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopGUIHarnessPanel：checkpoint 区容器结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIHarnessPanel：Harness 面板结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIHarnessPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUIHarnessPanel：函数段结束，HarnessPanel 到此结束；如果没有这个边界，初学者不易看出面板范围。
