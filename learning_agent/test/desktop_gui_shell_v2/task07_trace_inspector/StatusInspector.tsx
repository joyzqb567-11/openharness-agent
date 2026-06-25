import { useMemo, useState } from "react"; // 修改代码+DesktopTraceInspector：引入缓存和页签状态工具；如果没有这行，右侧检查器无法稳定切换多个面板。
import { Activity, Bug, Globe2, Settings, Wrench, type LucideIcon } from "lucide-react"; // 新增代码+DesktopTraceInspector：引入紧凑页签图标；如果没有这行，右侧页签会缺少可扫描的符号。
import type { StatusEvent } from "../state/statusStore"; // 修改代码+DesktopTraceInspector：引入状态事件类型；如果没有这行，右侧检查器 props 不清楚。
import { BrowserPanel } from "./BrowserPanel"; // 修改代码+DesktopTraceInspector：引入浏览器状态面板；如果没有这行，浏览器页签无法显示 provider 健康。
import { TracePanel } from "./TracePanel"; // 新增代码+DesktopTraceInspector：引入工具轨迹面板；如果没有这行，工具页签没有内容。

type StatusInspectorProps = { // 修改代码+DesktopTraceInspector：定义右侧检查器 props；如果没有这段，调用方不知道要传哪些数据。
  events: StatusEvent[]; // 修改代码+DesktopTraceInspector：保存事件流；如果没有这行，状态、工具和诊断页都没有数据来源。
  browserProviderStatus: Record<string, unknown>; // 修改代码+DesktopTraceInspector：保存浏览器 provider 状态；如果没有这行，浏览器页签无法接收后端健康信息。
}; // 修改代码+DesktopTraceInspector：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

type InspectorTabId = "status" | "tools" | "browser" | "settings" | "diagnostics"; // 新增代码+DesktopTraceInspector：限定右侧检查器页签 id；如果没有这行，页签状态可能变成任意字符串。

type InspectorTab = { // 新增代码+DesktopTraceInspector：定义页签配置结构；如果没有这段，页签按钮会散落硬编码。
  id: InspectorTabId; // 新增代码+DesktopTraceInspector：保存页签唯一 id；如果没有这行，点击时无法定位要显示哪个面板。
  label: string; // 新增代码+DesktopTraceInspector：保存中文页签名；如果没有这行，按钮没有可见文字。
  title: string; // 新增代码+DesktopTraceInspector：保存悬停说明；如果没有这行，紧凑按钮缺少提示。
  Icon: LucideIcon; // 新增代码+DesktopTraceInspector：保存 lucide 图标组件；如果没有这行，页签无法统一渲染图标。
}; // 新增代码+DesktopTraceInspector：页签配置类型结束；如果没有这行，TypeScript 类型语法不完整。

const inspectorTabs: InspectorTab[] = [ // 新增代码+DesktopTraceInspector：集中声明右侧五个页签；如果没有这段，用户无法在状态、工具、浏览器、设置和诊断之间切换。
  { id: "status", label: "状态", title: "运行状态", Icon: Activity }, // 新增代码+DesktopTraceInspector：声明状态页签；如果没有这行，原始事件时间线没有入口。
  { id: "tools", label: "工具", title: "工具轨迹", Icon: Wrench }, // 新增代码+DesktopTraceInspector：声明工具页签；如果没有这行，TracePanel 没有可见入口。
  { id: "browser", label: "浏览器", title: "浏览器状态", Icon: Globe2 }, // 新增代码+DesktopTraceInspector：声明浏览器页签；如果没有这行，provider 健康会继续挤在状态列表上方。
  { id: "settings", label: "设置", title: "本地设置", Icon: Settings }, // 新增代码+DesktopTraceInspector：声明设置页签；如果没有这行，右侧检查器缺少基础配置视图。
  { id: "diagnostics", label: "诊断", title: "诊断信息", Icon: Bug }, // 新增代码+DesktopTraceInspector：声明诊断页签；如果没有这行，事件游标和总量缺少专门查看位置。
]; // 新增代码+DesktopTraceInspector：页签配置结束；如果没有这行，数组语法不完整。

function statusOwner(event: StatusEvent): string { // 新增代码+DesktopTraceInspector：函数段开始，提取事件归属文本；如果没有这段，状态列表会重复写兜底逻辑。
  return event.turn_id || event.run_id || "system"; // 新增代码+DesktopTraceInspector：优先显示 turn，再显示 run，最后显示 system；如果没有这行，多轮事件难以区分归属。
} // 新增代码+DesktopTraceInspector：函数段结束，statusOwner 到此结束；如果没有这个边界，初学者不易看出事件归属逻辑范围。

export function StatusInspector({ events, browserProviderStatus }: StatusInspectorProps): JSX.Element { // 修改代码+DesktopTraceInspector：函数段开始，渲染右侧多页签检查器；如果没有这段，用户看不到运行、工具和诊断信息。
  const [activeTab, setActiveTab] = useState<InspectorTabId>("status"); // 新增代码+DesktopTraceInspector：保存当前页签；如果没有这行，点击页签后界面不会变化。
  const visibleEvents = useMemo(() => events.slice(-20).reverse(), [events]); // 修改代码+DesktopTraceInspector：缓存最近 20 条事件；如果没有这行，长任务事件会淹没右侧状态页。
  const latestSequence = events.at(-1)?.sequence ?? 0; // 新增代码+DesktopTraceInspector：读取最新事件序号；如果没有这行，诊断页缺少游标线索。
  return ( // 修改代码+DesktopTraceInspector：返回右侧检查器结构；如果没有这行，组件不会输出 UI。
    <aside className="status-inspector" aria-label="运行检查器"> {/* 修改代码+DesktopTraceInspector：定义右侧检查器容器；如果没有这行，状态区域没有独立语义。 */}
      <div className="inspector-tabs" role="tablist" aria-label="右侧检查器页签"> {/* 新增代码+DesktopTraceInspector：定义页签按钮组；如果没有这行，五个面板缺少切换入口。 */}
        {inspectorTabs.map((tab) => { // 新增代码+DesktopTraceInspector：遍历页签配置生成按钮；如果没有这行，页签配置不会渲染。
          const Icon = tab.Icon; // 新增代码+DesktopTraceInspector：取出当前页签图标组件；如果没有这行，JSX 无法用变量渲染图标。
          const selected = tab.id === activeTab; // 新增代码+DesktopTraceInspector：判断当前按钮是否选中；如果没有这行，按钮无法显示 active 状态。
          return ( // 新增代码+DesktopTraceInspector：返回单个页签按钮；如果没有这行，map 回调没有 UI 输出。
            <button className={`inspector-tab${selected ? " inspector-tab-active" : ""}`} type="button" role="tab" aria-selected={selected} title={tab.title} key={tab.id} onClick={() => { setActiveTab(tab.id); }}> {/* 新增代码+DesktopTraceInspector：渲染可点击页签；如果没有这行，用户无法切换面板。 */}
              <Icon size={14} aria-hidden="true" /> {/* 新增代码+DesktopTraceInspector：显示页签图标；如果没有这行，紧凑栏可扫描性下降。 */}
              <span>{tab.label}</span> {/* 新增代码+DesktopTraceInspector：显示页签中文名；如果没有这行，图标含义不够明确。 */}
            </button> // 新增代码+DesktopTraceInspector：单个页签按钮结束；如果没有这行，JSX 结构不完整。
          ); // 新增代码+DesktopTraceInspector：页签按钮返回结束；如果没有这行，map 回调语法不完整。
        })} {/* 新增代码+DesktopTraceInspector：页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopTraceInspector：页签按钮组结束；如果没有这行，JSX 结构不完整。 */}
      <div className="inspector-panel"> {/* 新增代码+DesktopTraceInspector：定义当前页签内容容器；如果没有这行，面板内容没有独立滚动边界。 */}
        {activeTab === "status" ? ( // 新增代码+DesktopTraceInspector：渲染状态页签分支；如果没有这行，状态列表会和其他面板同时显示。
          <section className="status-tab-panel" aria-label="运行状态"> {/* 新增代码+DesktopTraceInspector：定义状态面板；如果没有这行，读屏器无法识别状态页内容。 */}
            <div className="inspector-header"> {/* 修改代码+DesktopTraceInspector：定义状态标题行；如果没有这行，状态标题和事件数量没有稳定布局。 */}
              <h2>运行状态</h2> {/* 修改代码+DesktopTraceInspector：显示状态标题；如果没有这行，用户不知道当前页签内容。 */}
              <span>{events.length} events</span> {/* 修改代码+DesktopTraceInspector：显示事件总数；如果没有这行，用户无法判断 bridge 是否还在产生日志。 */}
            </div> {/* 修改代码+DesktopTraceInspector：状态标题行结束；如果没有这行，JSX 结构不完整。 */}
            <div className="status-event-list"> {/* 修改代码+DesktopTraceInspector：定义状态事件列表；如果没有这行，事件没有滚动容器。 */}
              {visibleEvents.length === 0 ? ( // 修改代码+DesktopTraceInspector：处理空事件状态；如果没有这行，刚启动时右侧会空白。
                <p className="empty-inspector">等待 bridge 事件。</p> // 修改代码+DesktopTraceInspector：显示空状态；如果没有这行，用户不知道当前只是尚未连接或尚无事件。
              ) : ( // 修改代码+DesktopTraceInspector：事件存在分支；如果没有这行，条件渲染语法不完整。
                visibleEvents.map((event) => ( // 修改代码+DesktopTraceInspector：遍历最近事件；如果没有这行，事件不会渲染。
                  <div className="status-event" key={event.sequence}> {/* 修改代码+DesktopTraceInspector：渲染单条状态事件；如果没有这行，用户看不到事件细节。 */}
                    <span>#{event.sequence}</span> {/* 修改代码+DesktopTraceInspector：显示事件序号；如果没有这行，排查轮询游标更困难。 */}
                    <strong>{event.event_type}</strong> {/* 修改代码+DesktopTraceInspector：显示事件类型；如果没有这行，用户不知道发生了什么。 */}
                    <small>{statusOwner(event)}</small> {/* 修改代码+DesktopTraceInspector：显示事件归属；如果没有这行，多 turn 情况难以区分。 */}
                  </div> // 修改代码+DesktopTraceInspector：单条状态事件结束；如果没有这行，JSX 结构不完整。
                )) // 修改代码+DesktopTraceInspector：事件遍历结束；如果没有这行，map 表达式不完整。
              )} {/* 修改代码+DesktopTraceInspector：状态列表条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
            </div> {/* 修改代码+DesktopTraceInspector：状态事件列表结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 新增代码+DesktopTraceInspector：状态面板结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 新增代码+DesktopTraceInspector：状态页签分支结束；如果没有这行，条件渲染语法不完整。 */}
        {activeTab === "tools" ? <TracePanel events={events} /> : null} {/* 新增代码+DesktopTraceInspector：渲染工具轨迹页签；如果没有这行，用户看不到工具名、耗时、参数和结果。 */}
        {activeTab === "browser" ? <BrowserPanel providerStatus={browserProviderStatus} /> : null} {/* 修改代码+DesktopTraceInspector：渲染浏览器状态页签；如果没有这行，Playwright/CDP/Extension 健康没有入口。 */}
        {activeTab === "settings" ? ( // 新增代码+DesktopTraceInspector：渲染设置页签分支；如果没有这行，设置页签点击后没有内容。
          <section className="diagnostics-panel" aria-label="设置"> {/* 新增代码+DesktopTraceInspector：定义设置面板；如果没有这行，设置内容没有语义区域。 */}
            <div className="inspector-header"> {/* 新增代码+DesktopTraceInspector：定义设置标题行；如果没有这行，设置面板缺少层级。 */}
              <h2>设置</h2> {/* 新增代码+DesktopTraceInspector：显示设置标题；如果没有这行，用户不知道当前面板用途。 */}
              <span>local</span> {/* 新增代码+DesktopTraceInspector：显示本地模式标签；如果没有这行，用户不知道设置来源是桌面壳本地配置。 */}
            </div> {/* 新增代码+DesktopTraceInspector：设置标题行结束；如果没有这行，JSX 结构不完整。 */}
            <div className="diagnostic-list"> {/* 新增代码+DesktopTraceInspector：定义设置列表；如果没有这行，设置项没有可扫描布局。 */}
              <div className="diagnostic-row"><strong>Bridge</strong><span>由桌面启动脚本注入</span></div> {/* 新增代码+DesktopTraceInspector：显示 bridge 配置来源；如果没有这行，用户不知道连接配置从哪里来。 */}
              <div className="diagnostic-row"><strong>权限</strong><span>高风险动作需要 GUI 确认</span></div> {/* 新增代码+DesktopTraceInspector：显示权限策略摘要；如果没有这行，设置页缺少安全状态。 */}
            </div> {/* 新增代码+DesktopTraceInspector：设置列表结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 新增代码+DesktopTraceInspector：设置面板结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 新增代码+DesktopTraceInspector：设置页签分支结束；如果没有这行，条件渲染语法不完整。 */}
        {activeTab === "diagnostics" ? ( // 新增代码+DesktopTraceInspector：渲染诊断页签分支；如果没有这行，诊断页签点击后没有内容。
          <section className="diagnostics-panel" aria-label="诊断"> {/* 新增代码+DesktopTraceInspector：定义诊断面板；如果没有这行，诊断内容没有语义区域。 */}
            <div className="inspector-header"> {/* 新增代码+DesktopTraceInspector：定义诊断标题行；如果没有这行，诊断面板缺少层级。 */}
              <h2>诊断</h2> {/* 新增代码+DesktopTraceInspector：显示诊断标题；如果没有这行，用户不知道当前面板用途。 */}
              <span>#{latestSequence}</span> {/* 新增代码+DesktopTraceInspector：显示最新事件游标；如果没有这行，排查断流时缺少关键编号。 */}
            </div> {/* 新增代码+DesktopTraceInspector：诊断标题行结束；如果没有这行，JSX 结构不完整。 */}
            <div className="diagnostic-list"> {/* 新增代码+DesktopTraceInspector：定义诊断列表；如果没有这行，诊断指标没有可扫描布局。 */}
              <div className="diagnostic-row"><strong>事件总数</strong><span>{events.length}</span></div> {/* 新增代码+DesktopTraceInspector：显示事件总数；如果没有这行，用户无法判断事件流是否推进。 */}
              <div className="diagnostic-row"><strong>最新序号</strong><span>{latestSequence}</span></div> {/* 新增代码+DesktopTraceInspector：显示最新序号；如果没有这行，用户难以确认轮询游标。 */}
            </div> {/* 新增代码+DesktopTraceInspector：诊断列表结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 新增代码+DesktopTraceInspector：诊断面板结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 新增代码+DesktopTraceInspector：诊断页签分支结束；如果没有这行，条件渲染语法不完整。 */}
      </div> {/* 新增代码+DesktopTraceInspector：当前页签内容容器结束；如果没有这行，JSX 结构不完整。 */}
    </aside> // 修改代码+DesktopTraceInspector：右侧检查器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopTraceInspector：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopTraceInspector：函数段结束，StatusInspector 到此结束；如果没有这个边界，初学者不易看出右侧检查器范围。
