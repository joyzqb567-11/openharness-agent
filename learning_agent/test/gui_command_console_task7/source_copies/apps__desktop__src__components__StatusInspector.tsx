import { latestModelCallStatus, ModelCallStatus } from "./ModelCallStatus"; // 新增代码+RealModelObservability：引入模型调用摘要组件；如果没有这一行，右侧状态页无法解释慢调用阶段。
import { useMemo, useState } from "react"; // 修改代码+DesktopDiagnosticsPanel：引入缓存和页签状态工具；如果没有这行，右侧检查器无法稳定切换多个面板。
import { Activity, Boxes, Bug, Globe2, ListChecks, Network, Settings, Terminal, Wrench, type LucideIcon } from "lucide-react"; // 修改代码+DesktopGUICommandConsolePanel：引入命令页签 Terminal 图标；如果没有这行，后台命令入口缺少可扫描符号。
import type { StatusEvent } from "../state/statusStore"; // 修改代码+DesktopDiagnosticsPanel：引入状态事件类型；如果没有这行，右侧检查器 props 不清楚。
import { BrowserPanel } from "./BrowserPanel"; // 修改代码+DesktopDiagnosticsPanel：引入浏览器状态面板；如果没有这行，浏览器页签无法显示 provider 健康。
import { CommandPanel } from "./CommandPanel"; // 新增代码+DesktopGUICommandConsolePanel：引入后台命令控制台面板；如果没有这行，右侧检查器无法展示后台命令和输出。
import { ComputerUsePanel } from "./ComputerUsePanel"; // 修改代码+DesktopDiagnosticsPanel：引入 Computer Use 状态面板；如果没有这行，桌面自动化锁和急停不可见。
import { DiagnosticsPanel } from "./DiagnosticsPanel"; // 新增代码+DesktopDiagnosticsPanel：引入真实诊断面板；如果没有这行，诊断页签只能显示旧占位信息。
import { HarnessPanel } from "./HarnessPanel"; // 新增代码+DesktopGUIHarnessPanel：引入长任务面板；如果没有这行，任务页签没有内容。
import { McpPanel } from "./McpPanel"; // 新增代码+DesktopGUIMcpPanel：引入 MCP 管理面板；如果没有这行，右侧检查器无法展示 MCP server/resource/prompt 状态。
import { PlanningPanel } from "./PlanningPanel"; // 新增代码+DesktopGUIPlanningPanel：引入计划协作面板；如果没有这行，右侧检查器无法展示 todo/task/team 状态。
import { SettingsPanel } from "./SettingsPanel"; // 新增代码+DesktopSettingsPanel：引入真实设置面板；如果没有这行，设置页签只能显示旧占位信息。
import { ToolchainPanel } from "./ToolchainPanel"; // 新增代码+DesktopGUIToolchainPanel：引入工具链清单面板；如果没有这行，右侧 GUI 无法展示可复用工具链。
import { TracePanel } from "./TracePanel"; // 修改代码+DesktopDiagnosticsPanel：引入工具轨迹面板；如果没有这行，工具页签没有内容。

type StatusInspectorProps = { // 修改代码+DesktopDiagnosticsPanel：类型段开始，定义右侧检查器 props；如果没有这段，调用方不知道要传哪些数据。
  events: StatusEvent[]; // 修改代码+DesktopDiagnosticsPanel：保存事件流；如果没有这行，状态、工具和诊断页都没有数据来源。
  browserProviderStatus: Record<string, unknown>; // 修改代码+DesktopDiagnosticsPanel：保存旧浏览器 provider 状态；如果没有这行，旧 payload 无法兜底。
  runtimePanels?: Record<string, unknown>; // 修改代码+DesktopDiagnosticsPanel：保存 V2 runtime panels payload；如果没有这行，浏览器和 Computer Use 无法共享统一状态。
  toolchainPayload?: Record<string, unknown>; // 新增代码+DesktopGUIToolchainPanel：保存 V2 工具链清单 payload；如果没有这行，工具链页签无法显示后端可用工具。
  mcpPayload?: Record<string, unknown>; // 新增代码+DesktopGUIMcpPanel：保存 V2 MCP 管理 payload；如果没有这行，MCP 页签无法显示 server/resource/prompt 状态。
  planningPayload?: Record<string, unknown>; // 新增代码+DesktopGUIPlanningPanel：保存 V2 planning payload；如果没有这行，计划页签无法显示 todo/task/team 状态。
  commandPayload?: Record<string, unknown>; // 新增代码+DesktopGUICommandConsolePanel：保存 V2 commands payload；如果没有这行，命令页签无法显示后台命令状态。
  harnessPayload?: Record<string, unknown>; // 新增代码+DesktopGUIHarnessPanel：保存 V2 Harness payload；如果没有这行，任务页签无法显示长任务状态。
  bridgeBaseUrl?: string; // 新增代码+DesktopSettingsPanel：保存 bridge URL；如果没有这行，设置页无法显示脱敏 host/port。
  healthPayload?: Record<string, unknown>; // 新增代码+DesktopSettingsPanel：保存 V2 health payload；如果没有这行，设置页无法显示 uptime、provider 和 feature flags。
  diagnosticsPayload?: Record<string, unknown>; // 新增代码+DesktopDiagnosticsPanel：保存 V2 diagnostics payload；如果没有这行，诊断页无法显示 release gate 和复制诊断包。
  onProbeUnknownRoute?: () => void; // 新增代码+DesktopUnknownRouteProbe：保存未知路由探针回调；如果没有这一行，诊断页按钮无法触发结构化 404 验收。
  onPauseHarness?: () => void; // 新增代码+DesktopGUIHarnessPanel：保存可选暂停回调；如果没有这行，后端支持时按钮无法接线。
  onResumeHarness?: () => void; // 新增代码+DesktopGUIHarnessPanel：保存可选恢复回调；如果没有这行，后端支持时按钮无法接线。
  onStopHarness?: () => void; // 新增代码+DesktopGUIHarnessControlsPanel：保存可选停止回调；如果没有这行，后端支持时停止按钮无法接线。
  onCheckpointHarness?: () => void; // 新增代码+DesktopGUIHarnessControlsPanel：保存可选 checkpoint 回调；如果没有这行，后端支持时恢复点按钮无法接线。
  harnessControlPending?: boolean; // 新增代码+DesktopGUIHarnessPanel：保存控制请求等待态；如果没有这行，按钮无法避免重复点击。
  lastHarnessControlResult?: Record<string, unknown>; // 新增代码+DesktopGUIHarnessControlsPanel：保存最近控制结果；如果没有这行，Task 面板无法展示点击反馈。
  onStopCommand?: (commandId: string) => void; // 新增代码+DesktopGUICommandConsolePanel：保存后台命令停止回调；如果没有这行，命令页签按钮无法接线。
  commandActionPending?: boolean; // 新增代码+DesktopGUICommandConsolePanel：保存命令控制请求等待态；如果没有这行，停止按钮无法避免重复点击。
  lastCommandActionResult?: Record<string, unknown>; // 新增代码+DesktopGUICommandConsolePanel：保存最近命令控制结果；如果没有这行，命令面板无法展示点击反馈。
  onRequestComputerUseAccess?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存 Computer Use 申请权限回调；如果没有这行，浏览器页签按钮无法触发后端。
  onObserveComputerUse?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存 Computer Use 观察回调；如果没有这行，观察按钮只能显示不能刷新。
  onAbortComputerUse?: () => void; // 新增代码+DesktopGUIComputerUseWorkbench：保存 Computer Use 中止回调；如果没有这行，GUI 无法调用 stop 状态机。
  computerUseActionPending?: boolean; // 新增代码+DesktopGUIComputerUseWorkbench：保存 Computer Use 动作等待态；如果没有这行，三个按钮无法避免重复提交。
  lastComputerUseActionResult?: Record<string, unknown>; // 新增代码+DesktopGUIComputerUseWorkbench：保存最近 Computer Use 按钮结果；如果没有这行，点击反馈不会进入右侧面板。
  onRefreshBrowserStatus?: () => void; // 新增代码+DesktopGUIBrowserWorkbench：保存 Browser 刷新回调；如果没有这行，浏览器工作台刷新按钮无法接到后端。
  onOpenBrowserUrl?: (url: string) => void; // 新增代码+DesktopGUIBrowserWorkbench：保存 Browser 记录打开回调；如果没有这行，URL 输入无法进入 bridge。
  browserActionPending?: boolean; // 新增代码+DesktopGUIBrowserWorkbench：保存 Browser 动作等待态；如果没有这行，刷新和记录打开按钮无法避免重复提交。
  lastBrowserActionResult?: Record<string, unknown>; // 新增代码+DesktopGUIBrowserWorkbench：保存最近 Browser 按钮结果；如果没有这行，点击反馈不会进入右侧面板。
}; // 修改代码+DesktopDiagnosticsPanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

type InspectorTabId = "status" | "tools" | "toolchain" | "mcp" | "planning" | "commands" | "browser" | "harness" | "settings" | "diagnostics"; // 修改代码+DesktopGUICommandConsolePanel：限定右侧检查器页签 id 并加入命令页；如果没有这行，后台命令页无法被选中。

type InspectorTab = { // 修改代码+DesktopDiagnosticsPanel：类型段开始，定义页签配置结构；如果没有这段，页签按钮会散落硬编码。
  id: InspectorTabId; // 修改代码+DesktopDiagnosticsPanel：保存页签唯一 id；如果没有这行，点击时无法定位面板。
  label: string; // 修改代码+DesktopDiagnosticsPanel：保存中文页签名；如果没有这行，按钮没有可见文字。
  title: string; // 修改代码+DesktopDiagnosticsPanel：保存悬停说明；如果没有这行，紧凑按钮缺少提示。
  Icon: LucideIcon; // 修改代码+DesktopDiagnosticsPanel：保存 lucide 图标组件；如果没有这行，页签无法统一渲染图标。
}; // 修改代码+DesktopDiagnosticsPanel：页签配置类型结束；如果没有这行，TypeScript 类型语法不完整。

const inspectorTabs: InspectorTab[] = [ // 修改代码+DesktopDiagnosticsPanel：集中声明右侧五个页签；如果没有这段，用户无法在状态、工具、浏览器、设置和诊断之间切换。
  { id: "status", label: "状态", title: "运行状态", Icon: Activity }, // 修改代码+DesktopDiagnosticsPanel：声明状态页签；如果没有这行，原始事件时间线没有入口。
  { id: "tools", label: "工具", title: "工具轨迹", Icon: Wrench }, // 修改代码+DesktopDiagnosticsPanel：声明工具页签；如果没有这行，TracePanel 没有可见入口。
  { id: "toolchain", label: "链路", title: "工具链清单", Icon: Boxes }, // 新增代码+DesktopGUIToolchainPanel：声明工具链页签；如果没有这行，用户看不到所有可复用工具和来源。
  { id: "mcp", label: "MCP", title: "MCP 管理", Icon: Network }, // 新增代码+DesktopGUIMcpPanel：声明 MCP 页签；如果没有这行，用户看不到 server、resource 和 prompt 状态。
  { id: "planning", label: "计划", title: "计划协作", Icon: ListChecks }, // 新增代码+DesktopGUIPlanningPanel：声明计划协作页签；如果没有这行，用户看不到 todo、task 和 peer 状态。
  { id: "commands", label: "命令", title: "后台命令", Icon: Terminal }, // 新增代码+DesktopGUICommandConsolePanel：声明后台命令页签；如果没有这行，用户看不到长任务终端输出。
  { id: "browser", label: "浏览器", title: "浏览器和桌面自动化状态", Icon: Globe2 }, // 修改代码+DesktopDiagnosticsPanel：声明浏览器页签；如果没有这行，provider 和 Computer Use 健康没有入口。
  { id: "harness", label: "任务", title: "长任务 Harness", Icon: ListChecks }, // 新增代码+DesktopGUIHarnessPanel：声明任务页签；如果没有这行，goal、queue 和 checkpoint 没有可见入口。
  { id: "settings", label: "设置", title: "本地设置", Icon: Settings }, // 修改代码+DesktopDiagnosticsPanel：声明设置页签；如果没有这行，用户找不到配置视图。
  { id: "diagnostics", label: "诊断", title: "诊断信息", Icon: Bug }, // 修改代码+DesktopDiagnosticsPanel：声明诊断页签；如果没有这行，事件游标和诊断包没有专门位置。
]; // 修改代码+DesktopDiagnosticsPanel：页签配置结束；如果没有这行，数组语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 修改代码+DesktopDiagnosticsPanel：函数段开始，把未知 payload 安全收敛成对象；如果没有这段，后端返回坏数据会拖垮右侧栏。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 修改代码+DesktopDiagnosticsPanel：只接受普通对象，否则返回空对象；如果没有这行，字段读取会信任任意类型。
} // 修改代码+DesktopDiagnosticsPanel：函数段结束，asRecord 到此结束；如果没有这个边界，类型防护范围不清楚。

function statusOwner(event: StatusEvent): string { // 修改代码+DesktopDiagnosticsPanel：函数段开始，提取事件归属文本；如果没有这段，状态列表会重复写兜底逻辑。
  return event.turn_id || event.run_id || "system"; // 修改代码+DesktopDiagnosticsPanel：优先显示 turn，再显示 run，最后显示 system；如果没有这行，多轮事件难以区分归属。
} // 修改代码+DesktopDiagnosticsPanel：函数段结束，statusOwner 到此结束；如果没有这个边界，事件归属逻辑范围不清楚。

export function StatusInspector({ events, browserProviderStatus, runtimePanels = {}, toolchainPayload = {}, mcpPayload = {}, planningPayload = {}, commandPayload = {}, harnessPayload = {}, bridgeBaseUrl = "", healthPayload = {}, diagnosticsPayload = {}, onProbeUnknownRoute, onPauseHarness, onResumeHarness, onStopHarness, onCheckpointHarness, harnessControlPending = false, lastHarnessControlResult = {}, onStopCommand, commandActionPending = false, lastCommandActionResult = {}, onRequestComputerUseAccess, onObserveComputerUse, onAbortComputerUse, computerUseActionPending = false, lastComputerUseActionResult = {}, onRefreshBrowserStatus, onOpenBrowserUrl, browserActionPending = false, lastBrowserActionResult = {} }: StatusInspectorProps): JSX.Element { // 修改代码+DesktopGUICommandConsolePanel：函数段开始，渲染右侧多页签检查器并接入命令控制台；如果没有这段，命令页签无法拿到 payload 和停止回调。
  const [activeTab, setActiveTab] = useState<InspectorTabId>("status"); // 修改代码+DesktopDiagnosticsPanel：保存当前页签；如果没有这行，点击页签后界面不会变化。
  const visibleEvents = useMemo(() => events.slice(-20).reverse(), [events]); // 修改代码+DesktopDiagnosticsPanel：缓存最近 20 条事件；如果没有这行，长任务事件会淹没右侧状态页。
  const latestModelStatus = useMemo(() => latestModelCallStatus(events), [events]); // 新增代码+RealModelObservability：缓存最新模型调用状态；如果没有这一行，右侧状态页无法展示连接/fallback/首响应摘要。
  const runtimePanelRecord = asRecord(runtimePanels); // 修改代码+DesktopDiagnosticsPanel：读取 V2 runtime panels 总对象；如果没有这行，后续子面板没有统一入口。
  const browserPanel = asRecord(runtimePanelRecord.browser); // 修改代码+DesktopDiagnosticsPanel：读取浏览器子面板；如果没有这行，BrowserPanel 只能显示旧状态。
  const computerUsePanel = asRecord(runtimePanelRecord.computer_use); // 修改代码+DesktopDiagnosticsPanel：读取 Computer Use 子面板；如果没有这行，桌面控制状态无法渲染。
  const permissionsPanel = asRecord(runtimePanelRecord.permissions); // 修改代码+DesktopDiagnosticsPanel：读取权限子面板；如果没有这行，Computer Use 无法显示待处理权限数量。
  return ( // 修改代码+DesktopDiagnosticsPanel：返回右侧检查器结构；如果没有这行，组件不会输出 UI。
    <aside className="status-inspector" aria-label="运行检查器"> {/* 修改代码+DesktopDiagnosticsPanel：右侧检查器容器；如果没有这一层，状态区域没有独立语义。 */}
      <div className="inspector-tabs" role="tablist" aria-label="右侧检查器页签"> {/* 修改代码+DesktopDiagnosticsPanel：页签按钮组；如果没有这一层，五个面板缺少切换入口。 */}
        {inspectorTabs.map((tab) => { // 修改代码+DesktopDiagnosticsPanel：遍历页签配置生成按钮；如果没有这行，页签配置不会渲染。
          const Icon = tab.Icon; // 修改代码+DesktopDiagnosticsPanel：取出当前页签图标组件；如果没有这行，JSX 无法用变量渲染图标。
          const selected = tab.id === activeTab; // 修改代码+DesktopDiagnosticsPanel：判断当前按钮是否选中；如果没有这行，按钮无法显示 active 状态。
          return ( // 修改代码+DesktopDiagnosticsPanel：返回单个页签按钮；如果没有这行，map 回调没有 UI 输出。
            <button className={`inspector-tab${selected ? " inspector-tab-active" : ""}`} type="button" role="tab" aria-selected={selected} title={tab.title} key={tab.id} onClick={() => { setActiveTab(tab.id); }}> {/* 修改代码+DesktopDiagnosticsPanel：可点击页签按钮；如果没有这一行，用户无法切换面板。 */}
              <Icon size={14} aria-hidden="true" /> {/* 修改代码+DesktopDiagnosticsPanel：页签图标；如果没有这一行，紧凑栏可扫描性下降。 */}
              <span>{tab.label}</span> {/* 修改代码+DesktopDiagnosticsPanel：页签中文名；如果没有这一行，图标含义不够明确。 */}
            </button> // 修改代码+DesktopDiagnosticsPanel：页签按钮结束；如果没有这行，map 回调语法不完整。
          ); // 修改代码+DesktopDiagnosticsPanel：页签按钮返回结束；如果没有这行，map 回调语法不完整。
        })} {/* 修改代码+DesktopDiagnosticsPanel：页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 修改代码+DesktopDiagnosticsPanel：页签按钮组结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="inspector-panel"> {/* 修改代码+DesktopDiagnosticsPanel：当前页签内容容器；如果没有这一层，面板内容没有独立滚动边界。 */}
        {activeTab === "status" ? ( // 修改代码+DesktopDiagnosticsPanel：按需渲染状态页签；如果没有这行，状态内容会一直占用空间。
          <section className="status-tab-panel" aria-label="运行状态"> {/* 修改代码+DesktopDiagnosticsPanel：状态面板；如果没有这一层，读屏器无法识别状态页内容。 */}
            <div className="inspector-header"> {/* 修改代码+DesktopDiagnosticsPanel：状态标题行；如果没有这一层，状态标题和事件数量没有稳定布局。 */}
              <h2>运行状态</h2> {/* 修改代码+DesktopDiagnosticsPanel：状态标题；如果没有这一行，用户不知道当前页签内容。 */}
              <span>{events.length} events</span> {/* 修改代码+DesktopDiagnosticsPanel：事件总数；如果没有这一行，用户无法判断 bridge 是否还在产生日志。 */}
            </div> {/* 修改代码+DesktopDiagnosticsPanel：状态标题行结束；如果没有这行，JSX 结构不完整。 */}
            <div className="status-model-call-summary"> {/* 新增代码+RealModelObservability：渲染模型调用摘要区域；如果没有这一层，用户只能逐条读事件判断慢调用阶段。 */}
              <ModelCallStatus status={latestModelStatus} /> {/* 新增代码+RealModelObservability：显示最新模型调用状态；如果没有这一行，右侧状态页缺少连接/fallback/失败摘要。 */}
            </div> {/* 新增代码+RealModelObservability：模型调用摘要区域结束；如果没有这一行，JSX 结构不完整。 */}
            <div className="status-event-list"> {/* 修改代码+DesktopDiagnosticsPanel：状态事件列表；如果没有这一层，事件没有滚动容器。 */}
              {visibleEvents.length === 0 ? ( // 修改代码+DesktopDiagnosticsPanel：渲染事件空态；如果没有这行，空列表会显示空白。
                <p className="empty-inspector">等待 bridge 事件。</p> // 修改代码+DesktopDiagnosticsPanel：空态文案；如果没有这行，用户不知道状态页是否仍在加载。
              ) : ( // 修改代码+DesktopDiagnosticsPanel：事件非空分支；如果没有这行，条件表达式不完整。
                visibleEvents.map((event) => ( // 修改代码+DesktopDiagnosticsPanel：遍历最近事件；如果没有这行，事件不会进入 UI。
                  <div className="status-event" key={event.sequence}> {/* 修改代码+DesktopDiagnosticsPanel：单条状态事件；如果没有这一层，用户看不到事件细节。 */}
                    <span>#{event.sequence}</span> {/* 修改代码+DesktopDiagnosticsPanel：事件序号；如果没有这一行，排查轮询游标更困难。 */}
                    <strong>{event.event_type}</strong> {/* 修改代码+DesktopDiagnosticsPanel：事件类型；如果没有这一行，用户不知道发生了什么。 */}
                    <small>{statusOwner(event)}</small> {/* 修改代码+DesktopDiagnosticsPanel：事件归属；如果没有这一行，多 turn 情况难以区分。 */}
                  </div> // 修改代码+DesktopDiagnosticsPanel：单条状态事件结束；如果没有这行，JSX 结构不完整。
                )) // 修改代码+DesktopDiagnosticsPanel：事件遍历结束；如果没有这行，map 表达式不完整。
              )} {/* 修改代码+DesktopDiagnosticsPanel：事件条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
            </div> {/* 修改代码+DesktopDiagnosticsPanel：状态事件列表结束；如果没有这行，JSX 结构不完整。 */}
          </section> // 修改代码+DesktopDiagnosticsPanel：状态面板结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 修改代码+DesktopDiagnosticsPanel：状态页签条件结束；如果没有这行，JSX 表达式不完整。 */}
        {activeTab === "tools" ? <TracePanel events={events} /> : null} {/* 修改代码+DesktopDiagnosticsPanel：工具轨迹页签；如果没有这一行，用户看不到工具名、耗时、参数和结果。 */}
        {activeTab === "toolchain" ? <ToolchainPanel payload={toolchainPayload} /> : null} {/* 新增代码+DesktopGUIToolchainPanel：工具链清单页签；如果没有这一行，用户看不到后端可用工具和复用模块。 */}
        {activeTab === "mcp" ? <McpPanel payload={mcpPayload} /> : null} {/* 新增代码+DesktopGUIMcpPanel：MCP 管理页签；如果没有这一行，用户看不到 MCP server、resource 和 prompt 状态。 */}
        {activeTab === "planning" ? <PlanningPanel payload={planningPayload} /> : null} {/* 新增代码+DesktopGUIPlanningPanel：计划协作页签；如果没有这一行，用户看不到 todo、task、peer 和消息状态。 */}
        {activeTab === "commands" ? <CommandPanel payload={commandPayload} onStopCommand={onStopCommand} actionPending={commandActionPending} lastActionResult={lastCommandActionResult} /> : null} {/* 新增代码+DesktopGUICommandConsolePanel：后台命令页签；如果没有这一行，用户看不到后台命令状态、输出和停止能力。 */}
        {activeTab === "browser" ? ( // 修改代码+DesktopDiagnosticsPanel：按需渲染浏览器页签；如果没有这行，浏览器和 Computer Use 面板会一直占用空间。
          <div className="runtime-panels"> {/* 修改代码+DesktopDiagnosticsPanel：运行时面板组；如果没有这一层，浏览器和 Computer Use 会缺少统一滚动布局。 */}
            <BrowserPanel providerStatus={browserProviderStatus} panel={browserPanel} onRefreshStatus={onRefreshBrowserStatus} onOpenUrl={onOpenBrowserUrl} actionPending={browserActionPending} lastActionResult={lastBrowserActionResult} /> {/* 修改代码+DesktopGUIBrowserWorkbench：把 Browser 刷新、记录打开和最近结果传给面板；如果没有这一行，浏览器工作台只能看状态不能操作。 */}
            <ComputerUsePanel panel={computerUsePanel} permissions={permissionsPanel} onRequestAccess={onRequestComputerUseAccess} onObserve={onObserveComputerUse} onAbort={onAbortComputerUse} actionPending={computerUseActionPending} lastActionResult={lastComputerUseActionResult} /> {/* 修改代码+DesktopGUIComputerUseWorkbench：把 Computer Use 三个安全按钮和最近结果传给面板；如果没有这一行，工作台只能看状态不能操作。 */}
          </div> // 修改代码+DesktopDiagnosticsPanel：运行时面板组结束；如果没有这行，JSX 结构不完整。
        ) : null} {/* 修改代码+DesktopDiagnosticsPanel：浏览器页签条件结束；如果没有这行，JSX 表达式不完整。 */}
        {activeTab === "harness" ? <HarnessPanel payload={harnessPayload} onPause={onPauseHarness} onResume={onResumeHarness} onStop={onStopHarness} onCheckpoint={onCheckpointHarness} controlPending={harnessControlPending} lastControlResult={lastHarnessControlResult} /> : null} {/* 修改代码+DesktopGUIHarnessControlsPanel：渲染长任务页签并传入真实控制回调；如果没有这一行，任务面板无法显示 active goal、queue、checkpoint 和控制结果。 */}
        {activeTab === "settings" ? <SettingsPanel bridgeBaseUrl={bridgeBaseUrl} health={healthPayload} diagnostics={diagnosticsPayload} /> : null} {/* 新增代码+DesktopSettingsPanel：渲染真实设置面板；如果没有这行，设置页签拿不到 provider、bridge、feature flags 和路径复制。 */}
        {activeTab === "diagnostics" ? <DiagnosticsPanel events={events} health={healthPayload} diagnostics={diagnosticsPayload} onProbeUnknownRoute={onProbeUnknownRoute} /> : null} {/* 修改代码+DesktopUnknownRouteProbe：渲染诊断面板并传入 unknown route 探针；如果没有这行，诊断页无法把结构化 404 写入主线程。 */}
      </div> {/* 修改代码+DesktopDiagnosticsPanel：当前页签内容容器结束；如果没有这一层，JSX 结构不完整。 */}
    </aside> // 修改代码+DesktopDiagnosticsPanel：右侧检查器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopDiagnosticsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopDiagnosticsPanel：函数段结束，StatusInspector 到此结束；如果没有这个边界，右侧检查器范围不清楚。
