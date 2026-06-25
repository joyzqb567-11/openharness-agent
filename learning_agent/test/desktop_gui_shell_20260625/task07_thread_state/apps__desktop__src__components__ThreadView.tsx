import type { ThreadMessage } from "../state/threadStore"; // 新增代码+DesktopThreadView：引入线程消息类型；如果没有这行，组件 props 会退化成不清楚的对象。

const fallbackMessages: ThreadMessage[] = [ // 新增代码+DesktopThreadView：定义首屏默认消息；如果没有这段，尚未接入后端时线程区会空白。
  { // 新增代码+DesktopThreadView：默认助手消息开始；如果没有这行，数组里没有可渲染对象。
    id: "welcome-assistant", // 新增代码+DesktopThreadView：给默认消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "assistant", // 新增代码+DesktopThreadView：标记默认消息来自助手；如果没有这行，样式无法判断来源。
    text: "桌面 GUI 外壳已连接到 OpenHarness 后端蓝图，下一步会接入真实消息生命周期。", // 新增代码+DesktopThreadView：显示默认说明；如果没有这行，首屏会显得空。
  }, // 新增代码+DesktopThreadView：默认助手消息结束；如果没有这行，对象语法不完整。
  { // 新增代码+DesktopThreadView：默认系统消息开始；如果没有这行，数组里缺少状态提示。
    id: "welcome-system", // 新增代码+DesktopThreadView：给系统消息稳定 id；如果没有这行，React 列表 key 不稳定。
    role: "system", // 新增代码+DesktopThreadView：标记默认消息为系统状态；如果没有这行，状态提示无法区别渲染。
    text: "事件轮询、权限提示、取消、重试和恢复会在后续任务逐项接上。", // 新增代码+DesktopThreadView：说明后续接入点；如果没有这行，能力边界不清楚。
  }, // 新增代码+DesktopThreadView：默认系统消息结束；如果没有这行，对象语法不完整。
]; // 新增代码+DesktopThreadView：默认消息数组结束；如果没有这行，TypeScript 语法不完整。

const roleLabels: Record<ThreadMessage["role"], string> = { // 新增代码+DesktopThreadView：定义角色显示名；如果没有这段，UI 会直接暴露英文角色值。
  assistant: "OpenHarness", // 新增代码+DesktopThreadView：助手角色显示名；如果没有这行，助手消息标题不友好。
  system: "状态", // 新增代码+DesktopThreadView：系统角色显示名；如果没有这行，状态消息标题不清楚。
  user: "你", // 新增代码+DesktopThreadView：用户角色显示名；如果没有这行，用户消息来源不明确。
}; // 新增代码+DesktopThreadView：角色显示名结束；如果没有这行，对象语法不完整。

type ThreadViewProps = { // 新增代码+DesktopThreadView：定义组件 props；如果没有这段，父组件无法传入真实消息。
  messages?: ThreadMessage[]; // 新增代码+DesktopThreadView：允许传入消息数组；如果没有这行，ThreadView 只能显示硬编码内容。
}; // 新增代码+DesktopThreadView：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function ThreadView({ messages = fallbackMessages }: ThreadViewProps): JSX.Element { // 新增代码+DesktopThreadView：函数段开始，渲染当前对话消息区；如果没有这段，主面板没有消息内容。
  return ( // 新增代码+DesktopThreadView：返回消息列表结构；如果没有这行，组件不会输出 UI。
    <div className="thread-body"> {/* 新增代码+DesktopThreadView：定义可滚动消息区域；如果没有这行，长对话无法独立滚动。 */}
      {messages.map((message) => ( // 新增代码+DesktopThreadView：遍历消息数组；如果没有这行，真实对话历史无法渲染。
        <article className={`message ${message.role}-message`} key={message.id}> {/* 新增代码+DesktopThreadView：渲染单条消息；如果没有这行，用户看不到消息内容。 */}
          <div className="message-role"> {/* 新增代码+DesktopThreadView：渲染消息角色行；如果没有这行，消息来源不清楚。 */}
            <span>{roleLabels[message.role]}</span> {/* 新增代码+DesktopThreadView：显示中文角色名；如果没有这行，角色标题不友好。 */}
            {message.status ? <span className="message-status">{message.status}</span> : null} {/* 新增代码+DesktopThreadView：显示可选 turn 状态；如果没有这行，运行/失败/取消无法直接出现在消息上。 */}
          </div> {/* 新增代码+DesktopThreadView：消息角色行结束；如果没有这行，JSX 结构不完整。 */}
          <p>{message.text || "正在等待后端响应..."}</p> {/* 新增代码+DesktopThreadView：显示消息正文或占位；如果没有这行，空助手消息会看起来像渲染失败。 */}
        </article> /* 新增代码+DesktopThreadView：单条消息结束；如果没有这行，JSX 结构不完整。 */
      ))} {/* 新增代码+DesktopThreadView：消息遍历结束；如果没有这行，JSX 表达式不完整。 */}
    </div> /* 新增代码+DesktopThreadView：消息区域结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopThreadView：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopThreadView：函数段结束，ThreadView 到此结束；如果没有这个边界，用户不容易看出消息区范围。
