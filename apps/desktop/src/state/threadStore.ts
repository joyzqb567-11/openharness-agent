export type ThreadRole = "user" | "assistant" | "system"; // 新增代码+DesktopThreadState：定义消息角色枚举；如果没有这行，消息来源会变成随意字符串。

export type TurnStatus = "idle" | "queued" | "running" | "needs_permission" | "cancelling" | "completed" | "failed" | "cancelled"; // 新增代码+DesktopThreadState：定义 turn 生命周期状态；如果没有这行，UI 无法稳定显示运行、取消、失败等状态。

export type ThreadMessage = { // 新增代码+DesktopThreadState：定义线程消息结构；如果没有这段，消息列表没有稳定数据合同。
  id: string; // 新增代码+DesktopThreadState：保存消息唯一标识；如果没有这行，React 列表无法稳定更新。
  role: ThreadRole; // 新增代码+DesktopThreadState：保存消息角色；如果没有这行，用户消息和助手消息无法区别渲染。
  text: string; // 新增代码+DesktopThreadState：保存消息正文；如果没有这行，线程没有可显示内容。
  turnId?: string; // 新增代码+DesktopThreadState：可选关联 turn；如果没有这行，消息和后端运行事件难以对应。
  status?: TurnStatus; // 新增代码+DesktopThreadState：可选消息状态；如果没有这行，助手占位消息无法显示运行/失败状态。
}; // 新增代码+DesktopThreadState：ThreadMessage 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type ThreadState = { // 新增代码+DesktopThreadState：定义线程整体状态；如果没有这段，组件之间无法共享对话状态。
  messages: ThreadMessage[]; // 新增代码+DesktopThreadState：保存消息数组；如果没有这行，对话历史无法渲染。
  activeTurnId: string | null; // 新增代码+DesktopThreadState：保存当前运行 turn；如果没有这行，取消和重试无法定位目标。
  activeTurnStatus: TurnStatus; // 新增代码+DesktopThreadState：保存当前 turn 状态；如果没有这行，按钮和状态文案无法判断。
  isRunning: boolean; // 新增代码+DesktopThreadState：保存是否运行中；如果没有这行，composer 无法禁用重复发送。
  errorMessage: string | null; // 新增代码+DesktopThreadState：保存可读错误；如果没有这行，busy 或失败状态只能丢失。
}; // 新增代码+DesktopThreadState：ThreadState 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type ThreadAction = // 新增代码+DesktopThreadState：定义 reducer 支持的动作；如果没有这段，状态更新会变成不可控的临时写法。
  | { type: "message_added"; message: ThreadMessage } // 新增代码+DesktopThreadState：追加消息动作；如果没有这行，用户和助手消息无法进入线程。
  | { type: "turn_started"; turnId: string; status?: TurnStatus } // 新增代码+DesktopThreadState：开始 turn 动作；如果没有这行，UI 无法进入运行态。
  | { type: "turn_status_changed"; turnId: string; status: TurnStatus; errorMessage?: string | null } // 新增代码+DesktopThreadState：更新 turn 状态动作；如果没有这行，取消、失败、权限状态无法反映到 UI。
  | { type: "turn_finished"; status?: TurnStatus; errorMessage?: string | null } // 新增代码+DesktopThreadState：结束 turn 动作；如果没有这行，UI 无法离开运行态。
  | { type: "thread_reset"; messages?: ThreadMessage[] }; // 新增代码+DesktopThreadState：重置线程动作；如果没有这行，恢复 session 时很难替换消息列表。

export const initialThreadState: ThreadState = { // 新增代码+DesktopThreadState：定义初始线程状态；如果没有这段，reducer 首次调用没有基准。
  messages: [], // 新增代码+DesktopThreadState：初始没有消息；如果没有这行，消息数组可能是 undefined。
  activeTurnId: null, // 新增代码+DesktopThreadState：初始没有运行 turn；如果没有这行，取消按钮可能误认为有目标。
  activeTurnStatus: "idle", // 新增代码+DesktopThreadState：初始状态为空闲；如果没有这行，UI 无法区分未开始和运行中。
  isRunning: false, // 新增代码+DesktopThreadState：初始不在运行；如果没有这行，发送按钮可能被错误禁用。
  errorMessage: null, // 新增代码+DesktopThreadState：初始没有错误；如果没有这行，错误提示可能显示脏数据。
}; // 新增代码+DesktopThreadState：初始状态结束；如果没有这行，对象语法不完整。

const runningStatuses = new Set<TurnStatus>(["queued", "running", "needs_permission", "cancelling"]); // 新增代码+DesktopThreadState：定义运行中状态集合；如果没有这行，多个地方会重复判断状态。

function updateMessagesForTurn(messages: ThreadMessage[], turnId: string, status: TurnStatus): ThreadMessage[] { // 新增代码+DesktopThreadState：函数段开始，同步某个 turn 的消息状态；如果没有这段，助手占位消息不会跟随生命周期变化。
  return messages.map((message) => { // 新增代码+DesktopThreadState：遍历消息列表；如果没有这行，无法找到需要更新的消息。
    if (message.turnId !== turnId) { // 新增代码+DesktopThreadState：跳过不属于该 turn 的消息；如果没有这行，所有消息都会被误改状态。
      return message; // 新增代码+DesktopThreadState：原样返回无关消息；如果没有这行，无关消息会丢失。
    } // 新增代码+DesktopThreadState：无关消息判断结束；如果没有这行，条件块语法不完整。
    return { ...message, status }; // 新增代码+DesktopThreadState：更新目标消息状态；如果没有这行，UI 看不到 turn 状态变化。
  }); // 新增代码+DesktopThreadState：消息遍历结束；如果没有这行，map 调用语法不完整。
} // 新增代码+DesktopThreadState：函数段结束，updateMessagesForTurn 到此结束；如果没有这个边界，用户不容易看出消息同步范围。

export function threadReducer(state: ThreadState = initialThreadState, action: ThreadAction): ThreadState { // 新增代码+DesktopThreadState：函数段开始，统一更新线程状态；如果没有这段，UI 状态会分散难测。
  if (action.type === "message_added") { // 新增代码+DesktopThreadState：处理追加消息；如果没有这段，用户输入和助手输出都无法进入线程。
    return { ...state, messages: [...state.messages, action.message] }; // 新增代码+DesktopThreadState：返回追加后的新状态；如果没有这行，React 无法感知消息变化。
  } // 新增代码+DesktopThreadState：追加消息分支结束；如果没有这行，条件块语法不完整。

  if (action.type === "turn_started") { // 新增代码+DesktopThreadState：处理 turn 开始；如果没有这段，运行状态不会被记录。
    const status = action.status ?? "queued"; // 新增代码+DesktopThreadState：默认进入 queued；如果没有这行，调用方每次都要传初始状态。
    return { ...state, activeTurnId: action.turnId, activeTurnStatus: status, isRunning: true, errorMessage: null }; // 新增代码+DesktopThreadState：记录运行中 turn；如果没有这行，取消和状态栏找不到当前 turn。
  } // 新增代码+DesktopThreadState：turn 开始分支结束；如果没有这行，条件块语法不完整。

  if (action.type === "turn_status_changed") { // 新增代码+DesktopThreadState：处理 turn 状态变化；如果没有这段，运行/权限/取消状态无法更新。
    const isRunning = runningStatuses.has(action.status); // 新增代码+DesktopThreadState：根据状态判断是否仍运行；如果没有这行，按钮启用状态会不准。
    return { // 新增代码+DesktopThreadState：返回状态变化后的新对象；如果没有这行，reducer 无法输出更新。
      ...state, // 新增代码+DesktopThreadState：保留未变化字段；如果没有这行，消息和其他状态会被清空。
      activeTurnId: isRunning ? action.turnId : state.activeTurnId, // 新增代码+DesktopThreadState：运行中保持 active turn；如果没有这行，取消按钮可能找不到目标。
      activeTurnStatus: action.status, // 新增代码+DesktopThreadState：记录最新 turn 状态；如果没有这行，UI 状态文案会落后。
      isRunning, // 新增代码+DesktopThreadState：记录是否运行中；如果没有这行，发送按钮无法判断是否禁用。
      errorMessage: action.errorMessage ?? null, // 新增代码+DesktopThreadState：保存错误消息或清空；如果没有这行，失败原因无法展示。
      messages: updateMessagesForTurn(state.messages, action.turnId, action.status), // 新增代码+DesktopThreadState：同步关联消息状态；如果没有这行，消息卡片不会显示终态。
    }; // 新增代码+DesktopThreadState：状态变化返回对象结束；如果没有这行，对象语法不完整。
  } // 新增代码+DesktopThreadState：turn 状态变化分支结束；如果没有这行，条件块语法不完整。

  if (action.type === "turn_finished") { // 新增代码+DesktopThreadState：处理 turn 结束；如果没有这段，UI 会一直停留在运行中。
    const status = action.status ?? "completed"; // 新增代码+DesktopThreadState：默认成功完成；如果没有这行，调用方每次都要传 completed。
    const turnId = state.activeTurnId; // 新增代码+DesktopThreadState：读取当前 turn id；如果没有这行，消息状态同步没有目标。
    return { // 新增代码+DesktopThreadState：返回结束后的状态；如果没有这行，reducer 无法退出运行态。
      ...state, // 新增代码+DesktopThreadState：保留消息和其他字段；如果没有这行，对话历史会丢失。
      activeTurnStatus: status, // 新增代码+DesktopThreadState：记录终态；如果没有这行，UI 不知道是完成、失败还是取消。
      isRunning: false, // 新增代码+DesktopThreadState：退出运行态；如果没有这行，发送按钮会一直禁用。
      errorMessage: action.errorMessage ?? null, // 新增代码+DesktopThreadState：保存终态错误；如果没有这行，失败原因无法显示。
      messages: turnId === null ? state.messages : updateMessagesForTurn(state.messages, turnId, status), // 新增代码+DesktopThreadState：同步当前 turn 消息终态；如果没有这行，助手占位状态会停在 running。
    }; // 新增代码+DesktopThreadState：turn 结束返回对象结束；如果没有这行，对象语法不完整。
  } // 新增代码+DesktopThreadState：turn 结束分支结束；如果没有这行，条件块语法不完整。

  if (action.type === "thread_reset") { // 新增代码+DesktopThreadState：处理线程重置；如果没有这段，窗口重启恢复 session 时无法替换消息。
    return { ...initialThreadState, messages: action.messages ?? [] }; // 新增代码+DesktopThreadState：返回干净状态和可选消息；如果没有这行，旧运行状态可能污染新 session。
  } // 新增代码+DesktopThreadState：线程重置分支结束；如果没有这行，条件块语法不完整。

  return state; // 新增代码+DesktopThreadState：未知动作返回原状态；如果没有这行，reducer 可能返回 undefined。
} // 新增代码+DesktopThreadState：函数段结束，threadReducer 到此结束；如果没有这个边界，用户不容易看出状态机范围。
