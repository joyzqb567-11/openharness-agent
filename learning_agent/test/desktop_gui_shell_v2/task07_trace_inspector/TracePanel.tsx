import { useMemo } from "react"; // 新增代码+DesktopTraceInspector：引入 useMemo 缓存工具轨迹计算；如果没有这行，每次渲染都会重复归约全部事件。
import { Clipboard } from "lucide-react"; // 新增代码+DesktopTraceInspector：引入复制图标；如果没有这行，复制诊断按钮缺少清晰符号。
import { reduceGuiEventToTraceRows, type TraceToolRow } from "../state/eventReducer"; // 新增代码+DesktopTraceInspector：复用工具事件到 trace row 的纯 reducer；如果没有这行，组件会重复实现转换逻辑。
import type { StatusEvent } from "../state/statusStore"; // 新增代码+DesktopTraceInspector：引入状态事件类型；如果没有这行，TracePanel props 边界不清楚。

type TracePanelProps = { // 新增代码+DesktopTraceInspector：定义工具轨迹面板 props；如果没有这段，调用方不知道要传事件流。
  events: StatusEvent[]; // 新增代码+DesktopTraceInspector：保存完整事件流；如果没有这行，TracePanel 没有工具事件来源。
}; // 新增代码+DesktopTraceInspector：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function copyDiagnostic(row: TraceToolRow): void { // 新增代码+DesktopTraceInspector：函数段开始，复制单条工具诊断信息；如果没有这段，复制按钮没有动作。
  if (typeof navigator === "undefined" || !navigator.clipboard) { // 新增代码+DesktopTraceInspector：检查剪贴板 API 是否存在；如果没有这行，测试或旧环境会抛异常。
    return; // 新增代码+DesktopTraceInspector：无剪贴板时静默退出；如果没有这行，后续会访问不存在对象。
  } // 新增代码+DesktopTraceInspector：剪贴板能力判断结束；如果没有这行，条件块语法不完整。
  void navigator.clipboard.writeText(row.diagnosticText); // 新增代码+DesktopTraceInspector：写入脱敏诊断文本；如果没有这行，用户无法复制工具调用信息。
} // 新增代码+DesktopTraceInspector：函数段结束，copyDiagnostic 到此结束；如果没有这个边界，初学者不易看出复制动作范围。

function statusLabel(status: TraceToolRow["status"]): string { // 新增代码+DesktopTraceInspector：函数段开始，把工具状态转成中文标签；如果没有这段，UI 会直接显示英文内部值。
  if (status === "running") { // 新增代码+DesktopTraceInspector：判断运行中状态；如果没有这行，运行状态无法本地化。
    return "运行中"; // 新增代码+DesktopTraceInspector：返回运行中标签；如果没有这行，running 没有可读文本。
  } // 新增代码+DesktopTraceInspector：运行中分支结束；如果没有这行，条件块语法不完整。
  if (status === "failed") { // 新增代码+DesktopTraceInspector：判断失败状态；如果没有这行，失败状态无法突出。
    return "失败"; // 新增代码+DesktopTraceInspector：返回失败标签；如果没有这行，failed 没有可读文本。
  } // 新增代码+DesktopTraceInspector：失败分支结束；如果没有这行，条件块语法不完整。
  return "完成"; // 新增代码+DesktopTraceInspector：返回完成标签；如果没有这行，completed 没有可读文本。
} // 新增代码+DesktopTraceInspector：函数段结束，statusLabel 到此结束；如果没有这个边界，初学者不易看出状态标签范围。

export function TracePanel({ events }: TracePanelProps): JSX.Element { // 新增代码+DesktopTraceInspector：函数段开始，渲染工具轨迹面板；如果没有这段，用户看不到工具调用树和诊断信息。
  const traceRows = useMemo(() => events.reduce(reduceGuiEventToTraceRows, [] as TraceToolRow[]).slice(-30).reverse(), [events]); // 新增代码+DesktopTraceInspector：从事件流归约最近工具轨迹；如果没有这行，TracePanel 没有可渲染数据。
  return ( // 新增代码+DesktopTraceInspector：返回工具轨迹结构；如果没有这行，组件不会输出 UI。
    <section className="trace-panel" aria-label="工具轨迹"> {/* 新增代码+DesktopTraceInspector：定义工具轨迹区域；如果没有这行，读屏器无法识别工具面板。 */}
      <div className="inspector-header"> {/* 新增代码+DesktopTraceInspector：定义工具面板标题区；如果没有这行，工具数量和标题没有稳定布局。 */}
        <h2>工具</h2> {/* 新增代码+DesktopTraceInspector：显示工具面板标题；如果没有这行，用户不知道当前页签内容。 */}
        <span>{traceRows.length} calls</span> {/* 新增代码+DesktopTraceInspector：显示工具调用数量；如果没有这行，用户无法判断是否有工具事件。 */}
      </div> {/* 新增代码+DesktopTraceInspector：工具面板标题区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="trace-list"> {/* 新增代码+DesktopTraceInspector：定义工具轨迹列表；如果没有这行，多条工具事件没有滚动容器。 */}
        {traceRows.length === 0 ? ( // 新增代码+DesktopTraceInspector：处理无工具事件状态；如果没有这行，空工具页会显得坏掉。
          <p className="empty-inspector">等待工具事件。</p> // 新增代码+DesktopTraceInspector：显示工具空状态；如果没有这行，用户不知道当前只是暂无工具调用。
        ) : ( // 新增代码+DesktopTraceInspector：工具事件存在分支；如果没有这行，条件渲染语法不完整。
          traceRows.map((row) => ( // 新增代码+DesktopTraceInspector：遍历工具轨迹；如果没有这行，轨迹不会渲染。
            <article className={`trace-row trace-row-${row.status}`} key={row.id}> {/* 新增代码+DesktopTraceInspector：渲染单条工具轨迹；如果没有这行，工具调用没有独立卡片。 */}
              <div className="trace-row-title"> {/* 新增代码+DesktopTraceInspector：定义工具标题行；如果没有这行，工具名、状态和复制按钮布局不稳。 */}
                <strong>{row.toolName}</strong> {/* 新增代码+DesktopTraceInspector：显示工具名；如果没有这行，用户不知道哪个工具被调用。 */}
                <span>{statusLabel(row.status)}</span> {/* 新增代码+DesktopTraceInspector：显示状态标签；如果没有这行，用户不知道工具执行结果。 */}
                <button type="button" className="trace-copy-button" title="复制诊断信息" aria-label="复制诊断信息" onClick={() => { copyDiagnostic(row); }}><Clipboard size={13} aria-hidden="true" /></button> {/* 新增代码+DesktopTraceInspector：渲染复制诊断按钮；如果没有这行，用户无法复制脱敏工具信息。 */}
              </div> {/* 新增代码+DesktopTraceInspector：工具标题行结束；如果没有这行，JSX 结构不完整。 */}
              <div className="trace-row-meta"> {/* 新增代码+DesktopTraceInspector：定义 run/turn/耗时元信息；如果没有这行，工具归属不易扫描。 */}
                <span>{row.runId || "run"}</span> {/* 新增代码+DesktopTraceInspector：显示 run id；如果没有这行，工具调用无法归属运行。 */}
                <span>{row.turnId || "turn"}</span> {/* 新增代码+DesktopTraceInspector：显示 turn id；如果没有这行，工具调用无法归属对话轮次。 */}
                <span>{row.durationMs === undefined ? "duration" : `${row.durationMs}ms`}</span> {/* 新增代码+DesktopTraceInspector：显示耗时；如果没有这行，用户无法发现慢工具。 */}
              </div> {/* 新增代码+DesktopTraceInspector：元信息行结束；如果没有这行，JSX 结构不完整。 */}
              <pre className="trace-args">{row.argsPreview || "{}"}</pre> {/* 新增代码+DesktopTraceInspector：显示脱敏参数预览；如果没有这行，用户看不到工具输入。 */}
              <p>{row.resultSummary || (row.status === "running" ? "等待结果。" : "无结果摘要。")}</p> {/* 新增代码+DesktopTraceInspector：显示结果或等待文案；如果没有这行，工具完成状态缺少正文。 */}
              {row.errorCode ? <small className="trace-error-code">{row.errorCode}</small> : null} {/* 新增代码+DesktopTraceInspector：显示错误码；如果没有这行，失败工具缺少机器可读线索。 */}
            </article> // 新增代码+DesktopTraceInspector：单条工具轨迹结束；如果没有这行，JSX 结构不完整。
          )) // 新增代码+DesktopTraceInspector：工具轨迹遍历结束；如果没有这行，map 表达式不完整。
        )} {/* 新增代码+DesktopTraceInspector：工具列表条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopTraceInspector：工具轨迹列表结束；如果没有这行，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopTraceInspector：工具轨迹区域结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopTraceInspector：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopTraceInspector：函数段结束，TracePanel 到此结束；如果没有这个边界，初学者不易看出工具轨迹面板范围。
