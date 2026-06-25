import type { StatusEvent } from "../state/statusStore"; // 新增代码+DesktopStatusInspector：引入状态事件类型；如果没有这行，右侧面板 props 不清楚。
import { BrowserPanel } from "./BrowserPanel"; // 新增代码+DesktopGUIBrowserPanel：引入浏览器状态面板；如果没有这行，右侧栏无法展示 provider_status。

type StatusInspectorProps = { // 新增代码+DesktopStatusInspector：定义右侧状态面板 props；如果没有这段，调用方不知道要传哪些数据。
  events: StatusEvent[]; // 新增代码+DesktopStatusInspector：保存事件列表；如果没有这行，状态面板没有时间线来源。
  browserProviderStatus: Record<string, unknown>; // 新增代码+DesktopGUIBrowserPanel：保存浏览器 provider 状态；如果没有这行，StatusInspector 无法把后端浏览器状态传给 BrowserPanel。
}; // 新增代码+DesktopStatusInspector：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function StatusInspector({ events, browserProviderStatus }: StatusInspectorProps): JSX.Element { // 修改代码+DesktopGUIBrowserPanel：函数段开始，渲染右侧运行状态和浏览器状态；如果没有这段，用户看不到生命周期、工具事件和浏览器 provider 健康。
  const visibleEvents = events.slice(-20).reverse(); // 新增代码+DesktopStatusInspector：只显示最近 20 条并倒序；如果没有这行，长任务事件会淹没面板。
  return ( // 新增代码+DesktopStatusInspector：返回状态面板结构；如果没有这行，组件不会输出 UI。
    <aside className="status-inspector" aria-label="运行状态"> {/* 新增代码+DesktopStatusInspector：定义右侧检查器；如果没有这行，状态信息没有独立区域。 */}
      <BrowserPanel providerStatus={browserProviderStatus} /> {/* 新增代码+DesktopGUIBrowserPanel：渲染浏览器 provider 状态；如果没有这行，用户无法确认 Playwright/CDP/Extension 哪条轨道可用。 */}
      <div className="inspector-header"> {/* 新增代码+DesktopStatusInspector：定义面板标题区；如果没有这行，右侧栏缺少层级。 */}
        <h2>运行状态</h2> {/* 新增代码+DesktopStatusInspector：显示面板标题；如果没有这行，用户不知道右栏用途。 */}
        <span>{events.length} events</span> {/* 新增代码+DesktopStatusInspector：显示事件数量；如果没有这行，用户无法判断是否正在收到事件。 */}
      </div> {/* 新增代码+DesktopStatusInspector：面板标题区结束；如果没有这行，JSX 结构不完整。 */}
      <div className="status-event-list"> {/* 新增代码+DesktopStatusInspector：定义事件列表容器；如果没有这行，事件项没有滚动区域。 */}
        {visibleEvents.length === 0 ? ( // 新增代码+DesktopStatusInspector：处理空事件状态；如果没有这行，右侧栏会显得空白。
          <p className="empty-inspector">等待 bridge 事件。</p> // 新增代码+DesktopStatusInspector：显示空状态；如果没有这行，用户不知道是否尚未连接。
        ) : ( // 新增代码+DesktopStatusInspector：事件存在分支；如果没有这行，条件渲染语法不完整。
          visibleEvents.map((event) => ( // 新增代码+DesktopStatusInspector：遍历最近事件；如果没有这行，事件不会渲染出来。
            <div className="status-event" key={event.sequence}> {/* 新增代码+DesktopStatusInspector：渲染单个事件行；如果没有这行，用户看不到事件细节。 */}
              <span>#{event.sequence}</span> {/* 新增代码+DesktopStatusInspector：显示事件序号；如果没有这行，排查轮询游标更困难。 */}
              <strong>{event.event_type}</strong> {/* 新增代码+DesktopStatusInspector：显示事件类型；如果没有这行，用户不知道发生了什么。 */}
              <small>{event.turn_id || event.run_id || "system"}</small> {/* 新增代码+DesktopStatusInspector：显示事件归属；如果没有这行，多 turn 情况难以区分。 */}
            </div> // 新增代码+DesktopStatusInspector：单个事件行结束；如果没有这行，JSX 结构不完整。
          )) // 新增代码+DesktopStatusInspector：事件遍历结束；如果没有这行，map 表达式不完整。
        )} {/* 新增代码+DesktopStatusInspector：条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </div> {/* 新增代码+DesktopStatusInspector：事件列表容器结束；如果没有这行，JSX 结构不完整。 */}
    </aside> // 新增代码+DesktopStatusInspector：右侧检查器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopStatusInspector：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopStatusInspector：函数段结束，StatusInspector 到此结束；如果没有这个边界，初学者不易看出右侧栏范围。
