import type { StatusEvent } from "../state/statusStore"; // 修改代码+DesktopToolTimeline：引入状态事件类型；如果没有这行，工具卡片 props 的数据来源不清楚。
import type { ThreadMessage } from "../state/threadStore"; // 修改代码+DesktopToolTimeline：引入线程消息类型；如果没有这行，组件 props 会退化成不透明对象。
import { ToolCallCard } from "./ToolCallCard"; // 新增代码+DesktopToolTimeline：引入工具调用卡片组件；如果没有这行，工具事件只能显示成普通文本。

const fallbackMessages: ThreadMessage[] = [ // 修改代码+DesktopToolTimeline：定义首屏默认消息；如果没有这段，尚未连接后端时线程区会空白。
  { // 修改代码+DesktopToolTimeline：默认助手消息开始；如果没有这行，数组里没有可渲染对象。
    id: "welcome-assistant", // 修改代码+DesktopToolTimeline：给默认消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "assistant", // 修改代码+DesktopToolTimeline：标记默认消息来自助手；如果没有这行，样式无法判断消息来源。
    text: "桌面 GUI 外壳已连接到 OpenHarness 后端蓝图，工具事件和运行状态会在这里逐步显示。", // 修改代码+DesktopToolTimeline：显示默认说明；如果没有这行，首屏会显得空。
  }, // 修改代码+DesktopToolTimeline：默认助手消息结束；如果没有这行，对象语法不完整。
  { // 修改代码+DesktopToolTimeline：默认系统消息开始；如果没有这行，数组里缺少状态提示。
    id: "welcome-system", // 修改代码+DesktopToolTimeline：给系统消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "system", // 修改代码+DesktopToolTimeline：标记默认消息为系统状态；如果没有这行，状态提示无法区别渲染。
    text: "事件轮询、取消、重试、权限提示和恢复会按蓝图继续接上。", // 修改代码+DesktopToolTimeline：说明后续接入点；如果没有这行，能力边界不清楚。
  }, // 修改代码+DesktopToolTimeline：默认系统消息结束；如果没有这行，对象语法不完整。
]; // 修改代码+DesktopToolTimeline：默认消息数组结束；如果没有这行，TypeScript 语法不完整。

const roleLabels: Record<ThreadMessage["role"], string> = { // 修改代码+DesktopToolTimeline：定义角色显示名；如果没有这段，UI 会直接暴露英文角色值。
  assistant: "OpenHarness", // 修改代码+DesktopToolTimeline：助手角色显示名；如果没有这行，助手消息标题不友好。
  system: "状态", // 修改代码+DesktopToolTimeline：系统角色显示名；如果没有这行，状态消息标题不清楚。
  user: "你", // 修改代码+DesktopToolTimeline：用户角色显示名；如果没有这行，用户消息来源不明确。
}; // 修改代码+DesktopToolTimeline：角色显示名结束；如果没有这行，对象语法不完整。

type ThreadViewProps = { // 修改代码+DesktopToolTimeline：定义组件 props；如果没有这段，父组件无法传入真实消息和事件。
  messages?: ThreadMessage[]; // 修改代码+DesktopToolTimeline：允许传入消息数组；如果没有这行，ThreadView 只能显示硬编码内容。
  events?: StatusEvent[]; // 新增代码+DesktopToolTimeline：允许传入状态事件；如果没有这行，线程区无法显示工具调用卡片。
}; // 修改代码+DesktopToolTimeline：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function summarizeToolEvent(event: StatusEvent): string { // 新增代码+DesktopToolTimeline：函数段开始，提取工具事件摘要；如果没有这段，工具卡片正文会散落在 JSX 里难以维护。
  if (typeof event.payload.summary === "string") { // 新增代码+DesktopToolTimeline：优先读取 summary 字段；如果没有这行，后端提供的摘要会被忽略。
    return event.payload.summary; // 新增代码+DesktopToolTimeline：返回后端摘要；如果没有这行，工具卡片没有人话说明。
  } // 新增代码+DesktopToolTimeline：summary 分支结束；如果没有这行，条件块语法不完整。
  if (typeof event.payload.error === "string") { // 新增代码+DesktopToolTimeline：读取错误字段；如果没有这行，失败工具不会展示原因。
    return event.payload.error; // 新增代码+DesktopToolTimeline：返回错误摘要；如果没有这行，工具失败只能看到事件类型。
  } // 新增代码+DesktopToolTimeline：error 分支结束；如果没有这行，条件块语法不完整。
  return event.event_type; // 新增代码+DesktopToolTimeline：兜底显示事件类型；如果没有这行，缺少摘要的事件会显示空白。
} // 新增代码+DesktopToolTimeline：函数段结束，summarizeToolEvent 到此结束；如果没有这个边界，初学者不容易看出摘要逻辑范围。

export function ThreadView({ messages = fallbackMessages, events = [] }: ThreadViewProps): JSX.Element { // 修改代码+DesktopToolTimeline：函数段开始，渲染当前对话消息和工具事件；如果没有这段，主面板没有消息内容。
  const toolEvents = events.filter((event) => event.event_type.includes("tool") || typeof event.payload.tool_name === "string").slice(-12); // 新增代码+DesktopToolTimeline：挑选最近工具相关事件；如果没有这行，线程区会被所有状态事件淹没。
  return ( // 修改代码+DesktopToolTimeline：返回消息列表结构；如果没有这行，组件不会输出 UI。
    <div className="thread-body"> {/* 修改代码+DesktopToolTimeline：定义可滚动消息区域；如果没有这行，长对话无法独立滚动。 */}
      {messages.map((message) => ( // 修改代码+DesktopToolTimeline：遍历消息数组；如果没有这行，真实对话历史无法渲染。
        <article className={`message ${message.role}-message`} key={message.id}> {/* 修改代码+DesktopToolTimeline：渲染单条消息；如果没有这行，用户看不到消息内容。 */}
          <div className="message-role"> {/* 修改代码+DesktopToolTimeline：渲染消息角色行；如果没有这行，消息来源不清楚。 */}
            <span>{roleLabels[message.role]}</span> {/* 修改代码+DesktopToolTimeline：显示中文角色名；如果没有这行，角色标题不友好。 */}
            {message.status ? <span className="message-status">{message.status}</span> : null} {/* 修改代码+DesktopToolTimeline：显示可选 turn 状态；如果没有这行，运行/失败/取消无法直接出现在消息上。 */}
          </div> {/* 修改代码+DesktopToolTimeline：消息角色行结束；如果没有这行，JSX 结构不完整。 */}
          <p>{message.text || "正在等待后端响应..."}</p> {/* 修改代码+DesktopToolTimeline：显示消息正文或占位；如果没有这行，空助手消息会看起来像渲染失败。 */}
        </article> // 修改代码+DesktopToolTimeline：单条消息结束；如果没有这行，JSX 结构不完整。
      ))} {/* 修改代码+DesktopToolTimeline：消息遍历结束；如果没有这行，JSX 表达式不完整。 */}
      {toolEvents.map((event) => ( // 新增代码+DesktopToolTimeline：遍历工具事件；如果没有这行，工具调用不会显示在主线程里。
        <ToolCallCard key={event.sequence} eventType={event.event_type} toolName={String(event.payload.tool_name ?? "GUI event")} summary={summarizeToolEvent(event)} /> // 新增代码+DesktopToolTimeline：渲染工具事件卡片；如果没有这行，用户看不到工具进展摘要。
      ))} {/* 新增代码+DesktopToolTimeline：工具事件遍历结束；如果没有这行，JSX 表达式不完整。 */}
    </div> // 修改代码+DesktopToolTimeline：消息区域结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopToolTimeline：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopToolTimeline：函数段结束，ThreadView 到此结束；如果没有这个边界，用户不容易看出消息区范围。
