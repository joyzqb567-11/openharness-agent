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
