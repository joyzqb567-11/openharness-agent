import { AlertTriangle, CheckCircle2, Clipboard } from "lucide-react"; // 新增代码+DesktopDiagnosticsPanel：引入诊断状态和复制图标；如果没有这行，诊断页缺少可扫描符号。
import { diagnosticBundleCopyText, diagnosticsStatusLabel } from "../state/settingsStore"; // 新增代码+DesktopDiagnosticsPanel：复用诊断状态和复制文本 helper；如果没有这行，组件会重复解析 payload。
import type { StatusEvent } from "../state/statusStore"; // 新增代码+DesktopDiagnosticsPanel：引入状态事件类型；如果没有这行，events props 会变成不透明数组。

type DiagnosticsPanelProps = { // 新增代码+DesktopDiagnosticsPanel：类型段开始，定义诊断面板输入；如果没有这段类型，调用方不知道需要传哪些状态。
  events: StatusEvent[]; // 新增代码+DesktopDiagnosticsPanel：保存事件时间线；如果没有这行，诊断页无法显示事件游标。
  health?: unknown; // 新增代码+DesktopDiagnosticsPanel：保存 health payload；如果没有这行，schema fallback 不稳定。
  diagnostics?: unknown; // 新增代码+DesktopDiagnosticsPanel：保存 diagnostics payload；如果没有这行，诊断页没有后端事实。
  onProbeUnknownRoute?: () => void; // 新增代码+DesktopUnknownRouteProbe：保存 unknown route 探针回调；如果没有这一行，诊断页无法主动验收结构化 404。
}; // 新增代码+DesktopDiagnosticsPanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function isRecord(value: unknown): value is Record<string, unknown> { // 新增代码+DesktopDiagnosticsPanel：函数段开始，判断未知值是否为对象；如果没有这段函数，payload 字段读取会不安全。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 新增代码+DesktopDiagnosticsPanel：只接受普通对象；如果没有这行，数组或 null 会导致异常。
} // 新增代码+DesktopDiagnosticsPanel：函数段结束，isRecord 到此结束；如果没有这个边界，初学者不容易看出类型保护范围。

function textFrom(value: unknown, fallback: string): string { // 新增代码+DesktopDiagnosticsPanel：函数段开始，安全读取文本；如果没有这段函数，undefined 会显示到 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopDiagnosticsPanel：返回非空文本或兜底；如果没有这行，诊断行会出现空白。
} // 新增代码+DesktopDiagnosticsPanel：函数段结束，textFrom 到此结束；如果没有这个边界，初学者不容易看出文本兜底范围。

function numberFrom(value: unknown, fallback: number): number { // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段开始，安全读取数字；如果没有这段函数，未知 payload 可能把 undefined 显示到指标里。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopDiagnosticsToolSurfacePanel：只接受有限数字并兜底；如果没有这行，NaN 或字符串会污染 UI。
} // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段结束，numberFrom 到此结束；如果没有这个边界，初学者不容易看出数字兜底范围。

function booleanLabel(value: unknown, trueText: string, falseText: string): string { // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段开始，把布尔值转成人话；如果没有这段函数，JSX 会重复三元判断。
  return value === true ? trueText : falseText; // 新增代码+DesktopDiagnosticsToolSurfacePanel：只有明确 true 才显示真文案；如果没有这行，未知值可能被误当可用。
} // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段结束，booleanLabel 到此结束；如果没有这个边界，初学者不容易看出布尔文案范围。

function textListFrom(value: unknown, fallback: string, limit = 4): string { // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段开始，安全读取短文本列表；如果没有这段函数，工具名和事件类型列表会直接依赖未知 JSON。
  const items = Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0).slice(0, limit) : []; // 新增代码+DesktopDiagnosticsToolSurfacePanel：只保留短列表里的字符串；如果没有这行，数组中的对象可能显示成 [object Object]。
  return items.length > 0 ? items.join(", ") : fallback; // 新增代码+DesktopDiagnosticsToolSurfacePanel：返回逗号分隔文本或兜底；如果没有这行，空列表会让诊断行空白。
} // 新增代码+DesktopDiagnosticsToolSurfacePanel：函数段结束，textListFrom 到此结束；如果没有这个边界，初学者不容易看出列表文本范围。

function copyDiagnostics(text: string): void { // 新增代码+DesktopDiagnosticsPanel：函数段开始，复制诊断包；如果没有这段函数，复制按钮没有实际动作。
  if (typeof navigator === "undefined" || !navigator.clipboard) { // 新增代码+DesktopDiagnosticsPanel：检查剪贴板 API；如果没有这行，测试或旧环境会抛异常。
    return; // 新增代码+DesktopDiagnosticsPanel：剪贴板不可用时退出；如果没有这行，点击按钮会报错。
  } // 新增代码+DesktopDiagnosticsPanel：剪贴板保护结束；如果没有这行，条件块语法不完整。
  void navigator.clipboard.writeText(text); // 新增代码+DesktopDiagnosticsPanel：写入诊断文本；如果没有这行，用户无法把诊断包发给开发者。
} // 新增代码+DesktopDiagnosticsPanel：函数段结束，copyDiagnostics 到此结束；如果没有这个边界，初学者不容易看出复制动作范围。

export function DiagnosticsPanel({ events, health = {}, diagnostics = {}, onProbeUnknownRoute }: DiagnosticsPanelProps): JSX.Element { // 修改代码+DesktopUnknownRouteProbe：函数段开始，渲染诊断页并接入 unknown route 探针；如果没有这段，Task 11 的诊断 UI 不存在。
  const diagnosticsRecord = isRecord(diagnostics) ? diagnostics : {}; // 新增代码+DesktopDiagnosticsPanel：保护 diagnostics payload；如果没有这行，字段读取可能崩溃。
  const healthRecord = isRecord(health) ? health : {}; // 新增代码+DesktopDiagnosticsPanel：保护 health payload；如果没有这行，schema fallback 可能崩溃。
  const releaseGate = isRecord(diagnosticsRecord.release_gate) ? diagnosticsRecord.release_gate : {}; // 新增代码+DesktopDiagnosticsPanel：读取 release gate 摘要；如果没有这行，验收状态无法稳定显示。
  const snapshotSummary = isRecord(diagnosticsRecord.snapshot_summary) ? diagnosticsRecord.snapshot_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取快照摘要；如果没有这行，运行指标行无法稳定显示。
  const traceSummary = isRecord(diagnosticsRecord.trace_summary) ? diagnosticsRecord.trace_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 Trace 摘要；如果没有这行，read_trace 状态无法渲染。
  const compactStatus = isRecord(diagnosticsRecord.compact_status) ? diagnosticsRecord.compact_status : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 Compact 摘要；如果没有这行，压缩边界无法渲染。
  const resumeReport = isRecord(diagnosticsRecord.resume_report_summary) ? diagnosticsRecord.resume_report_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 Resume 摘要；如果没有这行，恢复风险无法渲染。
  const healthStatus = isRecord(diagnosticsRecord.health_status_summary) ? diagnosticsRecord.health_status_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 health_status 摘要；如果没有这行，健康警告无法渲染。
  const lspSummary = isRecord(diagnosticsRecord.lsp_diagnostics_summary) ? diagnosticsRecord.lsp_diagnostics_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 LSP 摘要；如果没有这行，代码理解工具状态无法渲染。
  const replSummary = isRecord(diagnosticsRecord.repl_summary) ? diagnosticsRecord.repl_summary : {}; // 新增代码+DesktopDiagnosticsToolSurfacePanel：读取 REPL 摘要；如果没有这行，批量编排状态无法渲染。
  const latestSequence = events.at(-1)?.sequence ?? 0; // 新增代码+DesktopDiagnosticsPanel：读取最近事件序号；如果没有这行，诊断页无法显示事件游标。
  const statusLabel = diagnosticsStatusLabel(diagnosticsRecord); // 新增代码+DesktopDiagnosticsPanel：生成状态标签；如果没有这行，在线/降级/正常判断会散在 JSX。
  const copyText = diagnosticBundleCopyText(diagnosticsRecord); // 新增代码+DesktopDiagnosticsPanel：读取可复制诊断包；如果没有这行，复制按钮没有内容。
  const degraded = diagnosticsRecord.status_degraded === true; // 新增代码+DesktopDiagnosticsPanel：判断是否降级；如果没有这行，图标和警告无法稳定切换。
  const StatusIcon = degraded ? AlertTriangle : CheckCircle2; // 新增代码+DesktopDiagnosticsPanel：选择状态图标；如果没有这行，降级和正常状态无法一眼区分。
  return ( // 新增代码+DesktopDiagnosticsPanel：返回诊断面板结构；如果没有这行，组件不会输出 UI。
    <section className="diagnostics-panel" aria-label="诊断"> {/* 新增代码+DesktopDiagnosticsPanel：诊断语义容器；如果没有这一层，读屏器无法识别诊断区域。 */}
      <div className="inspector-header"> {/* 新增代码+DesktopDiagnosticsPanel：诊断标题行；如果没有这一层，标题和游标无法稳定对齐。 */}
        <h2>诊断</h2> {/* 新增代码+DesktopDiagnosticsPanel：显示诊断标题；如果没有这行，用户不知道当前页签用途。 */}
        <span>#{latestSequence}</span> {/* 新增代码+DesktopDiagnosticsPanel：显示最近事件序号；如果没有这行，用户无法判断事件流位置。 */}
      </div> {/* 新增代码+DesktopDiagnosticsPanel：标题行结束；如果没有这行，JSX 结构不完整。 */}
      <div className={`diagnostics-state${degraded ? " diagnostics-state-warning" : ""}`}> {/* 新增代码+DesktopDiagnosticsPanel：诊断状态横幅；如果没有这一层，降级状态不够醒目。 */}
        <StatusIcon size={15} aria-hidden="true" /> {/* 新增代码+DesktopDiagnosticsPanel：状态图标；如果没有这行，用户只能读文字判断状态。 */}
        <strong>{statusLabel}</strong> {/* 新增代码+DesktopDiagnosticsPanel：状态文案；如果没有这行，用户无法知道后端是否正常。 */}
      </div> {/* 新增代码+DesktopDiagnosticsPanel：状态横幅结束；如果没有这行，JSX 结构不完整。 */}
      <div className="diagnostic-list"> {/* 新增代码+DesktopDiagnosticsPanel：诊断键值列表；如果没有这一层，诊断行没有统一排版。 */}
        <div className="diagnostic-row"><strong>后端</strong><span>{diagnosticsRecord.backend_online === false ? "离线" : "在线"}</span></div> {/* 新增代码+DesktopDiagnosticsPanel：显示后端在线状态；如果没有这行，用户不知道 bridge 是否可达。 */}
        <div className="diagnostic-row"><strong>Schema</strong><span>{String(diagnosticsRecord.schema_version ?? healthRecord.schema_version ?? "-")}</span></div> {/* 新增代码+DesktopDiagnosticsPanel：显示 schema 版本；如果没有这行，协议兼容问题不好排查。 */}
        <div className="diagnostic-row"><strong>降级</strong><span>{degraded ? "是" : "否"}</span></div> {/* 新增代码+DesktopDiagnosticsPanel：显示降级状态；如果没有这行，用户无法确认 snapshot 是否完整。 */}
        <div className="diagnostic-row"><strong>最近错误</strong><span>{textFrom(diagnosticsRecord.last_error, textFrom(diagnosticsRecord.safe_error, "无"))}</span></div> {/* 新增代码+DesktopDiagnosticsPanel：显示已脱敏最近错误；如果没有这行，排查线索不可见。 */}
        <div className="diagnostic-row"><strong>Release Gate</strong><span>{textFrom(releaseGate.status, "not_run")}</span></div> {/* 新增代码+DesktopDiagnosticsPanel：显示最近验收状态；如果没有这行，用户不知道最后 gate 结果。 */}
        <div className="diagnostic-row"><strong>Trace</strong><span>{textFrom(traceSummary.latest_event_type, "none")} · #{numberFrom(traceSummary.latest_event_sequence, 0)} · {numberFrom(traceSummary.event_count ?? snapshotSummary.event_count, 0)} events</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示事件流摘要；如果没有这行，用户看不到 read_trace 状态。 */}
        <div className="diagnostic-row"><strong>Trace Tail</strong><span>{textListFrom(traceSummary.recent_event_types, "无事件", 5)}</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示最近事件类型；如果没有这行，用户需要翻日志才能看到运行脉络。 */}
        <div className="diagnostic-row"><strong>Compact</strong><span>{textFrom(compactStatus.state, "not_run")} · {textFrom(compactStatus.latest_boundary_uuid, "no boundary")}</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示上下文压缩状态；如果没有这行，用户看不到 compact_status 入口。 */}
        <div className="diagnostic-row"><strong>Resume</strong><span>{textFrom(resumeReport.state, "not_run")} · {textFrom(resumeReport.latest_session_id, "no session")} · {booleanLabel(resumeReport.requires_attention, "需关注", "正常")}</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示恢复报告状态；如果没有这行，恢复风险在 GUI 不可见。 */}
        <div className="diagnostic-row"><strong>Health</strong><span>{booleanLabel(healthStatus.ok, "正常", "有警告")} · {numberFrom(healthStatus.warning_count, 0)} warnings</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示 health_status 摘要；如果没有这行，状态生态健康不可见。 */}
        <div className="diagnostic-row"><strong>LSP</strong><span>{booleanLabel(lspSummary.available, "可用", "缺失")} · {textListFrom(lspSummary.tool_names, "未注册", 3)}</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示 LSP 工具三件套；如果没有这行，代码理解工具接入不可见。 */}
        <div className="diagnostic-row"><strong>REPL</strong><span>{booleanLabel(replSummary.available, "可用", "缺失")} · {numberFrom(replSummary.allowed_tool_count, 0)} tools · {numberFrom(replSummary.max_calls, 0)} calls</span></div> {/* 新增代码+DesktopDiagnosticsToolSurfacePanel：显示 REPL 批量编排能力；如果没有这行，安全批量工具链不可见。 */}
      </div> {/* 新增代码+DesktopDiagnosticsPanel：诊断键值列表结束；如果没有这行，JSX 结构不完整。 */}
      <button className="diagnostics-copy-button" type="button" onClick={() => { copyDiagnostics(copyText); }} title="复制诊断包"> {/* 新增代码+DesktopDiagnosticsPanel：复制诊断包按钮；如果没有这行，用户无法快速提供排查材料。 */}
        <Clipboard size={13} aria-hidden="true" /> {/* 新增代码+DesktopDiagnosticsPanel：复制图标；如果没有这行，按钮意图不够直观。 */}
        <span>复制诊断包</span> {/* 新增代码+DesktopDiagnosticsPanel：按钮文字；如果没有这行，只靠图标不够清楚。 */}
      </button> {/* 新增代码+DesktopDiagnosticsPanel：复制按钮结束；如果没有这行，JSX 结构不完整。 */}
      <button className="diagnostics-copy-button diagnostics-secondary-button" type="button" onClick={() => { onProbeUnknownRoute?.(); }} title="测试未知路由错误"> {/* 新增代码+DesktopUnknownRouteProbe：渲染 unknown route 探针按钮；如果没有这一行，结构化 404 无法在 GUI 内触发。 */}
        <AlertTriangle size={13} aria-hidden="true" /> {/* 新增代码+DesktopUnknownRouteProbe：显示警告图标；如果没有这一行，按钮意图不够直观。 */}
        <span>测试未知路由</span> {/* 新增代码+DesktopUnknownRouteProbe：显示按钮文字；如果没有这一行，用户不知道按钮会验证什么。 */}
      </button> {/* 新增代码+DesktopUnknownRouteProbe：unknown route 按钮结束；如果没有这一行，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopDiagnosticsPanel：诊断面板容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopDiagnosticsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopDiagnosticsPanel：函数段结束，DiagnosticsPanel 到此结束；如果没有这个边界，诊断面板范围不清楚。
