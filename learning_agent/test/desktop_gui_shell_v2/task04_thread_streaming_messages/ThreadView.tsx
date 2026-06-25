import type { StatusEvent } from "../state/statusStore"; // 修改代码+DesktopThreadStreaming：引入状态事件类型；如果没有这行，工具卡片 props 的数据来源不清楚。
import type { ThreadMessage } from "../state/threadStore"; // 修改代码+DesktopThreadStreaming：引入线程消息类型；如果没有这行，组件 props 会退化成不透明对象。
import { RefreshCcw, X } from "lucide-react"; // 修改代码+DesktopThreadStreaming：引入重试和取消图标；如果没有这行，生命周期按钮会缺少成熟桌面工具感。
import { ToolCallCard } from "./ToolCallCard"; // 修改代码+DesktopThreadStreaming：引入工具调用卡片；如果没有这行，工具事件只能显示成普通文本。

const fallbackMessages: ThreadMessage[] = [ // 修改代码+DesktopThreadStreaming：定义首屏默认消息；如果没有这段，尚未连接后端时线程区会空白。
  { // 修改代码+DesktopThreadStreaming：默认助手消息开始；如果没有这行，数组里没有可渲染对象。
    id: "welcome-assistant", // 修改代码+DesktopThreadStreaming：给默认消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "assistant", // 修改代码+DesktopThreadStreaming：标记默认消息来自助手；如果没有这行，样式无法判断消息来源。
    text: "桌面 GUI 外壳已连接到 OpenHarness 后端蓝图，工具事件和运行状态会在这里逐步显示。", // 修改代码+DesktopThreadStreaming：显示默认说明；如果没有这行，首屏会显得空。
    kind: "normal", // 新增代码+DesktopThreadStreaming：显式声明普通消息语义；如果没有这行，ThreadView 需要额外猜测默认类型。
  }, // 修改代码+DesktopThreadStreaming：默认助手消息结束；如果没有这行，对象语法不完整。
  { // 修改代码+DesktopThreadStreaming：默认系统消息开始；如果没有这行，数组里缺少状态提示。
    id: "welcome-system", // 修改代码+DesktopThreadStreaming：给系统消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "system", // 修改代码+DesktopThreadStreaming：标记默认消息为系统状态；如果没有这行，状态提示无法区别渲染。
    text: "事件轮询、取消、重试、权限提示和恢复会按蓝图继续接上。", // 修改代码+DesktopThreadStreaming：说明后续接入点；如果没有这行，能力边界不清楚。
    kind: "normal", // 新增代码+DesktopThreadStreaming：显式声明普通系统消息；如果没有这行，语义字段可能缺失。
  }, // 修改代码+DesktopThreadStreaming：默认系统消息结束；如果没有这行，对象语法不完整。
]; // 修改代码+DesktopThreadStreaming：默认消息数组结束；如果没有这行，TypeScript 语法不完整。

const roleLabels: Record<ThreadMessage["role"], string> = { // 修改代码+DesktopThreadStreaming：定义角色显示名；如果没有这段，UI 会直接暴露英文角色值。
  assistant: "OpenHarness", // 修改代码+DesktopThreadStreaming：助手角色显示名；如果没有这行，助手消息标题不友好。
  system: "状态", // 修改代码+DesktopThreadStreaming：系统角色显示名；如果没有这行，状态消息标题不清楚。
  user: "你", // 修改代码+DesktopThreadStreaming：用户角色显示名；如果没有这行，用户消息来源不明确。
}; // 修改代码+DesktopThreadStreaming：角色显示名结束；如果没有这行，对象语法不完整。

const cancellableStatuses = new Set(["queued", "running", "needs_permission", "cancelling"]); // 修改代码+DesktopThreadStreaming：定义可取消状态集合；如果没有这行，取消按钮规则会散落在 JSX 里。
const retryableStatuses = new Set(["completed", "failed", "cancelled"]); // 修改代码+DesktopThreadStreaming：定义可重试状态集合；如果没有这行，终态消息的重试入口不稳定。

function canCancelMessage(message: ThreadMessage): boolean { // 修改代码+DesktopThreadStreaming：函数段开始，判断消息是否能取消；如果没有这段，ThreadView 需要在 JSX 里写复杂条件。
  return message.role === "assistant" && typeof message.turnId === "string" && cancellableStatuses.has(message.status ?? ""); // 修改代码+DesktopThreadStreaming：只允许运行中助手 turn 取消；如果没有这行，用户消息或终态消息可能误显示取消。
} // 修改代码+DesktopThreadStreaming：函数段结束，canCancelMessage 到此结束；如果没有这个边界，用户不容易看出取消规则范围。

function canRetryMessage(message: ThreadMessage): boolean { // 修改代码+DesktopThreadStreaming：函数段开始，判断消息是否能重试；如果没有这段，ThreadView 需要在 JSX 里写复杂条件。
  return message.role === "assistant" && typeof message.turnId === "string" && retryableStatuses.has(message.status ?? ""); // 修改代码+DesktopThreadStreaming：只允许带 turnId 的终态助手消息重试；如果没有这行，运行中消息可能误显示重试。
} // 修改代码+DesktopThreadStreaming：函数段结束，canRetryMessage 到此结束；如果没有这个边界，用户不容易看出重试规则范围。

type ThreadViewProps = { // 修改代码+DesktopThreadStreaming：类型段开始，定义组件 props；如果没有这段，父组件无法安全传入消息和事件。
  messages?: ThreadMessage[]; // 修改代码+DesktopThreadStreaming：允许传入消息数组；如果没有这行，ThreadView 只能显示硬编码内容。
  events?: StatusEvent[]; // 修改代码+DesktopThreadStreaming：允许传入状态事件；如果没有这行，线程区无法显示工具调用卡片。
  onCancelTurn?: (turnId: string) => void; // 修改代码+DesktopThreadStreaming：允许父组件处理取消；如果没有这行，取消按钮只能显示不能调用 bridge。
  onRetryTurn?: (turnId: string) => void; // 修改代码+DesktopThreadStreaming：允许父组件处理重试；如果没有这行，重试按钮只能显示不能调用 bridge。
}; // 修改代码+DesktopThreadStreaming：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function summarizeToolEvent(event: StatusEvent): string { // 修改代码+DesktopThreadStreaming：函数段开始，提取工具事件摘要；如果没有这段，工具卡片正文会散落在 JSX 里难维护。
  if (typeof event.payload.summary === "string") { // 修改代码+DesktopThreadStreaming：优先读取 summary 字段；如果没有这行，后端提供的摘要会被忽略。
    return event.payload.summary; // 修改代码+DesktopThreadStreaming：返回后端摘要；如果没有这行，工具卡片没有人话说明。
  } // 修改代码+DesktopThreadStreaming：summary 分支结束；如果没有这行，条件块语法不完整。
  if (typeof event.payload.error === "string") { // 修改代码+DesktopThreadStreaming：读取错误字段；如果没有这行，失败工具不会展示原因。
    return event.payload.error; // 修改代码+DesktopThreadStreaming：返回错误摘要；如果没有这行，工具失败只能看到事件类型。
  } // 修改代码+DesktopThreadStreaming：error 分支结束；如果没有这行，条件块语法不完整。
  return event.event_type; // 修改代码+DesktopThreadStreaming：兜底显示事件类型；如果没有这行，缺少摘要的事件会显示空白。
} // 修改代码+DesktopThreadStreaming：函数段结束，summarizeToolEvent 到此结束；如果没有这个边界，用户不容易看出摘要逻辑范围。

function messageKindLabel(message: ThreadMessage): string { // 新增代码+DesktopThreadStreaming：函数段开始，计算消息语义标签；如果没有这段，拒绝和错误标签逻辑会写进 JSX。
  if (message.kind === "refusal") { // 新增代码+DesktopThreadStreaming：判断是否安全拒绝；如果没有这行，拒绝消息无法单独标识。
    return "安全拒绝"; // 新增代码+DesktopThreadStreaming：返回安全拒绝标签；如果没有这行，用户不知道这是安全边界而不是普通失败。
  } // 新增代码+DesktopThreadStreaming：安全拒绝分支结束；如果没有这行，条件块语法不完整。
  if (message.kind === "error") { // 新增代码+DesktopThreadStreaming：判断是否错误消息；如果没有这行，错误消息无法单独标识。
    return "错误"; // 新增代码+DesktopThreadStreaming：返回错误标签；如果没有这行，用户无法快速扫到失败原因。
  } // 新增代码+DesktopThreadStreaming：错误分支结束；如果没有这行，条件块语法不完整。
  return ""; // 新增代码+DesktopThreadStreaming：普通消息不显示额外标签；如果没有这行，所有消息都会多余占位。
} // 新增代码+DesktopThreadStreaming：函数段结束，messageKindLabel 到此结束；如果没有这个边界，用户不容易看出标签规则范围。

function renderMessageText(text: string): JSX.Element[] { // 新增代码+DesktopThreadStreaming：函数段开始，把消息正文渲染为文本和代码块；如果没有这段，代码片段无法使用 pre/code 横向滚动。
  const parts = text.split("```"); // 新增代码+DesktopThreadStreaming：按 Markdown 代码围栏切分；如果没有这行，代码块无法和普通文本分开。
  return parts.map((part, index) => { // 新增代码+DesktopThreadStreaming：遍历文本片段；如果没有这行，无法生成多段 JSX。
    if (index % 2 === 1) { // 新增代码+DesktopThreadStreaming：奇数片段代表代码围栏内部；如果没有这行，代码会被当普通段落显示。
      const code = part.replace(/^[a-zA-Z0-9_-]+\n/, "").trim(); // 新增代码+DesktopThreadStreaming：去掉可选语言行并清理边界空白；如果没有这行，代码块顶部可能多出语言名或空行。
      return <pre className="message-code" key={`code-${index}`}><code>{code}</code></pre>; // 新增代码+DesktopThreadStreaming：渲染可滚动代码块；如果没有这行，长代码会撑破消息宽度。
    } // 新增代码+DesktopThreadStreaming：代码片段分支结束；如果没有这行，条件块语法不完整。
    return <span key={`text-${index}`}>{part}</span>; // 新增代码+DesktopThreadStreaming：渲染普通文本片段；如果没有这行，非代码内容会丢失。
  }); // 新增代码+DesktopThreadStreaming：片段遍历结束；如果没有这行，map 调用语法不完整。
} // 新增代码+DesktopThreadStreaming：函数段结束，renderMessageText 到此结束；如果没有这个边界，用户不容易看出正文渲染范围。

export function ThreadView({ messages = fallbackMessages, events = [], onCancelTurn, onRetryTurn }: ThreadViewProps): JSX.Element { // 修改代码+DesktopThreadStreaming：函数段开始，渲染对话消息、工具事件和生命周期动作；如果没有这段，主面板没有消息内容。
  const toolEvents = events.filter((event) => event.event_type.includes("tool") || typeof event.payload.tool_name === "string").slice(-12); // 修改代码+DesktopThreadStreaming：筛选最近工具相关事件；如果没有这行，线程区会被所有状态事件淹没。
  return ( // 修改代码+DesktopThreadStreaming：返回消息列表结构；如果没有这行，组件不会输出 UI。
    <div className="thread-body"> {/* 修改代码+DesktopThreadStreaming：定义可滚动消息区域；如果没有这行，长对话无法独立滚动。 */}
      {messages.map((message) => { // 修改代码+DesktopThreadStreaming：遍历真实对话消息；如果没有这行，消息历史无法渲染。
        const canCancel = canCancelMessage(message); // 修改代码+DesktopThreadStreaming：计算是否显示取消按钮；如果没有这行，JSX 会重复判断。
        const canRetry = canRetryMessage(message); // 修改代码+DesktopThreadStreaming：计算是否显示重试按钮；如果没有这行，JSX 会重复判断。
        const kindLabel = messageKindLabel(message); // 新增代码+DesktopThreadStreaming：计算拒绝/错误标签；如果没有这行，消息语义不会在标题行出现。
        const messageText = message.text || "正在等待后端响应..."; // 修改代码+DesktopThreadStreaming：准备正文或等待占位；如果没有这行，空助手消息会像渲染失败。
        return ( // 修改代码+DesktopThreadStreaming：返回单条消息结构；如果没有这行，map 回调没有 JSX 结果。
          <article className={`message ${message.role}-message message-kind-${message.kind ?? "normal"}`} key={message.id}> {/* 修改代码+DesktopThreadStreaming：渲染单条消息并带语义 class；如果没有这行，用户看不到消息内容。 */}
            <div className="message-role"> {/* 修改代码+DesktopThreadStreaming：渲染消息角色、状态和动作行；如果没有这行，消息来源和按钮会混在正文里。 */}
              <span>{roleLabels[message.role]}</span> {/* 修改代码+DesktopThreadStreaming：显示中文角色名；如果没有这行，角色标题不友好。 */}
              {kindLabel.length > 0 ? <span className={`message-label message-label-${message.kind ?? "normal"}`}>{kindLabel}</span> : null} {/* 新增代码+DesktopThreadStreaming：显示安全拒绝或错误标签；如果没有这行，一等消息语义不可见。 */}
              {message.status ? <span className="message-status">{message.status}</span> : null} {/* 修改代码+DesktopThreadStreaming：显示可选 turn 状态；如果没有这行，运行/失败/取消无法直接出现在消息上。 */}
              {canCancel && message.turnId ? <button className="message-action-button" type="button" title="取消本轮" aria-label="取消本轮" onClick={() => onCancelTurn?.(message.turnId ?? "")}><X aria-hidden={true} size={13} /></button> : null} {/* 修改代码+DesktopThreadStreaming：渲染取消按钮并把 turnId 交给父组件；如果没有这行，用户无法在 GUI 中触发后端 cancel。 */}
              {canRetry && message.turnId ? <button className="message-action-button" type="button" title="重试本轮" aria-label="重试本轮" onClick={() => onRetryTurn?.(message.turnId ?? "")}><RefreshCcw aria-hidden={true} size={13} /></button> : null} {/* 修改代码+DesktopThreadStreaming：渲染重试按钮并把 turnId 交给父组件；如果没有这行，用户无法在 GUI 中触发后端 retry。 */}
            </div> {/* 修改代码+DesktopThreadStreaming：消息角色和动作行结束；如果没有这行，JSX 结构不完整。 */}
            <div className="message-text">{renderMessageText(messageText)}</div> {/* 修改代码+DesktopThreadStreaming：渲染正文和代码块；如果没有这行，消息内容不会显示。 */}
          </article> // 修改代码+DesktopThreadStreaming：单条消息结束；如果没有这行，JSX 结构不完整。
        ); // 修改代码+DesktopThreadStreaming：map 回调返回结束；如果没有这行，JSX return 语法不完整。
      })} {/* 修改代码+DesktopThreadStreaming：消息遍历结束；如果没有这行，JSX 表达式不完整。 */}
      {toolEvents.map((event) => ( // 修改代码+DesktopThreadStreaming：遍历工具事件；如果没有这行，工具调用不会显示在主线程里。
        <ToolCallCard key={event.sequence} eventType={event.event_type} toolName={String(event.payload.tool_name ?? "GUI event")} summary={summarizeToolEvent(event)} /> // 修改代码+DesktopThreadStreaming：渲染工具事件卡片；如果没有这行，用户看不到工具进展摘要。
      ))} {/* 修改代码+DesktopThreadStreaming：工具事件遍历结束；如果没有这行，JSX 表达式不完整。 */}
    </div> // 修改代码+DesktopThreadStreaming：消息区域结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopThreadStreaming：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopThreadStreaming：函数段结束，ThreadView 到此结束；如果没有这个边界，用户不容易看出消息区范围。
