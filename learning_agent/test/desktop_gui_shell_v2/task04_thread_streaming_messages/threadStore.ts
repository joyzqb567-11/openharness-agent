export type ThreadRole = "user" | "assistant" | "system"; // 修改代码+DesktopThreadStreaming：定义消息角色白名单；如果没有这行，消息来源会退化成任意字符串，界面样式无法稳定匹配。
export type TurnStatus = "idle" | "queued" | "running" | "needs_permission" | "cancelling" | "completed" | "failed" | "cancelled"; // 修改代码+DesktopThreadStreaming：定义 turn 生命周期状态；如果没有这行，运行、权限、取消和终态无法被类型系统约束。
export type ThreadMessageKind = "normal" | "refusal" | "error"; // 新增代码+DesktopThreadStreaming：定义消息语义类型；如果没有这行，安全拒绝和错误只能伪装成普通文本，ThreadView 无法显示专门标签。

export type ThreadMessage = { // 修改代码+DesktopThreadStreaming：类型段开始，定义主线程消息结构；如果没有这段，前端消息列表没有稳定数据合同。
  id: string; // 修改代码+DesktopThreadStreaming：保存消息唯一标识；如果没有这行，React 列表更新会缺少稳定 key。
  role: ThreadRole; // 修改代码+DesktopThreadStreaming：保存消息来源角色；如果没有这行，用户、助手和系统消息无法区分渲染。
  text: string; // 修改代码+DesktopThreadStreaming：保存消息正文；如果没有这行，线程里没有可显示内容。
  turnId?: string; // 修改代码+DesktopThreadStreaming：保存可选后端 turn id；如果没有这行，流式事件、取消和重试无法定位对应消息。
  status?: TurnStatus; // 修改代码+DesktopThreadStreaming：保存可选生命周期状态；如果没有这行，queued/running/failed 等标签无法显示在消息上。
  kind?: ThreadMessageKind; // 新增代码+DesktopThreadStreaming：保存消息语义；如果没有这行，拒绝和错误消息无法成为一等 UI 状态。
}; // 修改代码+DesktopThreadStreaming：类型段结束，ThreadMessage 到此结束；如果没有这行，TypeScript 类型语法不完整。

export type ThreadState = { // 修改代码+DesktopThreadStreaming：类型段开始，定义线程整体状态；如果没有这段，组件之间无法共享对话状态。
  messages: ThreadMessage[]; // 修改代码+DesktopThreadStreaming：保存消息数组；如果没有这行，对话历史无法渲染。
  activeTurnId: string | null; // 修改代码+DesktopThreadStreaming：保存当前活动 turn；如果没有这行，取消按钮和运行状态无法定位目标。
  activeTurnStatus: TurnStatus; // 修改代码+DesktopThreadStreaming：保存当前 turn 状态；如果没有这行，composer 无法判断是否处于运行中。
  isRunning: boolean; // 修改代码+DesktopThreadStreaming：保存是否仍在运行；如果没有这行，用户可能重复提交同一轮请求。
  errorMessage: string | null; // 修改代码+DesktopThreadStreaming：保存当前错误摘要；如果没有这行，失败原因无法在状态层保留。
}; // 修改代码+DesktopThreadStreaming：类型段结束，ThreadState 到此结束；如果没有这行，TypeScript 类型语法不完整。

export type ThreadAction = // 修改代码+DesktopThreadStreaming：定义 reducer 支持的动作集合；如果没有这段，状态变化会散落在组件里难以测试。
  | { type: "message_added"; message: ThreadMessage } // 修改代码+DesktopThreadStreaming：追加消息动作；如果没有这行，本地用户消息和系统提示无法进入线程。
  | { type: "assistant_message_upserted"; message: ThreadMessage } // 新增代码+DesktopThreadStreaming：按 turn/id 插入或更新助手消息；如果没有这行，完成、拒绝和错误事件无法安全创建可见消息。
  | { type: "message_delta_received"; turnId: string; textDelta: string } // 新增代码+DesktopThreadStreaming：追加流式文本增量；如果没有这行，GUI 只能等最终答案，缺少 Codex 风格的实时输出。
  | { type: "turn_started"; turnId: string; status?: TurnStatus } // 修改代码+DesktopThreadStreaming：记录 turn 启动动作；如果没有这行，UI 无法进入运行态。
  | { type: "turn_status_changed"; turnId: string; status: TurnStatus; text?: string; errorMessage?: string | null } // 修改代码+DesktopThreadStreaming：更新 turn 状态动作；如果没有这行，取消、权限和旧事件无法同步到消息卡。
  | { type: "turn_finished"; status?: TurnStatus; text?: string; errorMessage?: string | null } // 修改代码+DesktopThreadStreaming：结束当前 turn 动作；如果没有这行，UI 无法退出运行态。
  | { type: "thread_reset"; messages?: ThreadMessage[] }; // 修改代码+DesktopThreadStreaming：重置线程动作；如果没有这行，恢复 session 时无法替换消息列表。

export const initialThreadState: ThreadState = { // 修改代码+DesktopThreadStreaming：定义初始线程状态；如果没有这段，reducer 首次调用没有可靠基准。
  messages: [], // 修改代码+DesktopThreadStreaming：初始消息为空；如果没有这行，消息数组可能变成 undefined。
  activeTurnId: null, // 修改代码+DesktopThreadStreaming：初始没有活动 turn；如果没有这行，取消逻辑可能误判已有目标。
  activeTurnStatus: "idle", // 修改代码+DesktopThreadStreaming：初始状态为空闲；如果没有这行，界面无法区分未开始和运行中。
  isRunning: false, // 修改代码+DesktopThreadStreaming：初始不在运行；如果没有这行，发送按钮可能被错误禁用。
  errorMessage: null, // 修改代码+DesktopThreadStreaming：初始没有错误；如果没有这行，旧错误可能污染新线程。
}; // 修改代码+DesktopThreadStreaming：初始状态结束；如果没有这行，对象语法不完整。

const runningStatuses = new Set<TurnStatus>(["queued", "running", "needs_permission", "cancelling"]); // 修改代码+DesktopThreadStreaming：集中定义运行中状态；如果没有这行，多个分支会重复写容易漂移的状态判断。

function assistantMessageId(turnId: string): string { // 新增代码+DesktopThreadStreaming：函数段开始，生成助手消息稳定 id；如果没有这段，缺少占位消息时无法为流式事件创建稳定容器。
  return `assistant_${turnId}`; // 新增代码+DesktopThreadStreaming：按 turn id 生成消息 id；如果没有这行，同一 turn 的增量可能生成多个消息。
} // 新增代码+DesktopThreadStreaming：函数段结束，assistantMessageId 到此结束；如果没有这个边界，用户不容易看出 id 规则范围。

function messageMatchesTurn(message: ThreadMessage, turnId: string): boolean { // 新增代码+DesktopThreadStreaming：函数段开始，判断消息是否属于某个 turn；如果没有这段，upsert 和 delta 会重复写匹配条件。
  return typeof message.turnId === "string" && message.turnId === turnId; // 新增代码+DesktopThreadStreaming：只按明确 turnId 匹配；如果没有这行，普通消息可能被误更新。
} // 新增代码+DesktopThreadStreaming：函数段结束，messageMatchesTurn 到此结束；如果没有这个边界，用户不容易看出匹配规则范围。

function mergeAssistantMessage(existing: ThreadMessage, incoming: ThreadMessage): ThreadMessage { // 新增代码+DesktopThreadStreaming：函数段开始，合并同一助手消息；如果没有这段，最终事件可能覆盖掉已有 id、turnId 或正文。
  return { // 新增代码+DesktopThreadStreaming：返回合并后的新对象；如果没有这行，函数没有输出。
    ...existing, // 新增代码+DesktopThreadStreaming：先保留旧消息字段；如果没有这行，已有正文和本地 id 可能丢失。
    ...incoming, // 新增代码+DesktopThreadStreaming：再写入新事件字段；如果没有这行，完成、拒绝或错误语义无法更新。
    text: incoming.text.length > 0 ? incoming.text : existing.text, // 新增代码+DesktopThreadStreaming：只用非空文本覆盖；如果没有这行，空完成事件会把正在显示的流式文本清掉。
    kind: incoming.kind ?? existing.kind ?? "normal", // 新增代码+DesktopThreadStreaming：保留或补齐消息语义；如果没有这行，错误/拒绝标签可能消失。
  }; // 新增代码+DesktopThreadStreaming：合并对象结束；如果没有这行，对象语法不完整。
} // 新增代码+DesktopThreadStreaming：函数段结束，mergeAssistantMessage 到此结束；如果没有这个边界，用户不容易看出合并规则范围。

function upsertAssistantMessage(messages: ThreadMessage[], incoming: ThreadMessage): ThreadMessage[] { // 新增代码+DesktopThreadStreaming：函数段开始，按 turn/id 更新或新增助手消息；如果没有这段，事件驱动消息会出现重复或丢失。
  const turnId = incoming.turnId ?? ""; // 新增代码+DesktopThreadStreaming：读取传入消息 turnId；如果没有这行，后续匹配要反复处理 undefined。
  const index = messages.findIndex((message) => (turnId.length > 0 && messageMatchesTurn(message, turnId)) || message.id === incoming.id); // 新增代码+DesktopThreadStreaming：寻找已有消息位置；如果没有这行，每个完成事件都会追加重复消息。
  if (index === -1) { // 新增代码+DesktopThreadStreaming：判断是否没有旧消息；如果没有这行，无法区分新增和更新。
    return [...messages, { ...incoming, kind: incoming.kind ?? "normal" }]; // 新增代码+DesktopThreadStreaming：追加新助手消息；如果没有这行，孤立失败或拒绝事件不会在主线程可见。
  } // 新增代码+DesktopThreadStreaming：新增分支结束；如果没有这行，条件块语法不完整。
  return messages.map((message, messageIndex) => (messageIndex === index ? mergeAssistantMessage(message, incoming) : message)); // 新增代码+DesktopThreadStreaming：替换匹配消息并保留其他消息；如果没有这行，已有消息列表会被破坏。
} // 新增代码+DesktopThreadStreaming：函数段结束，upsertAssistantMessage 到此结束；如果没有这个边界，用户不容易看出 upsert 范围。

function appendDeltaToMessages(messages: ThreadMessage[], turnId: string, textDelta: string): ThreadMessage[] { // 新增代码+DesktopThreadStreaming：函数段开始，把流式增量追加到助手消息；如果没有这段，message_delta 不能驱动实时显示。
  const index = messages.findIndex((message) => messageMatchesTurn(message, turnId)); // 新增代码+DesktopThreadStreaming：查找当前 turn 的助手消息；如果没有这行，增量不知道追加到哪里。
  if (index === -1) { // 新增代码+DesktopThreadStreaming：判断是否还没有占位消息；如果没有这行，快速 delta 会静默丢失。
    return [...messages, { id: assistantMessageId(turnId), role: "assistant", text: textDelta, turnId, status: "running", kind: "normal" }]; // 新增代码+DesktopThreadStreaming：创建流式助手消息；如果没有这行，先于 send 响应的流式事件没有可见容器。
  } // 新增代码+DesktopThreadStreaming：无占位分支结束；如果没有这行，条件块语法不完整。
  return messages.map((message, messageIndex) => (messageIndex === index ? { ...message, text: `${message.text}${textDelta}`, status: message.status ?? "running", kind: message.kind ?? "normal" } : message)); // 新增代码+DesktopThreadStreaming：追加增量并保留原状态；如果没有这行，流式正文无法逐步增长。
} // 新增代码+DesktopThreadStreaming：函数段结束，appendDeltaToMessages 到此结束；如果没有这个边界，用户不容易看出增量范围。

function updateMessagesForTurn(messages: ThreadMessage[], turnId: string, status: TurnStatus, text?: string): ThreadMessage[] { // 修改代码+DesktopThreadStreaming：函数段开始，同步旧生命周期事件到消息；如果没有这段，旧 gui_turn_* 事件无法更新消息状态。
  return messages.map((message) => { // 修改代码+DesktopThreadStreaming：遍历消息列表；如果没有这行，无法找到目标消息。
    if (!messageMatchesTurn(message, turnId)) { // 修改代码+DesktopThreadStreaming：跳过不属于该 turn 的消息；如果没有这行，所有消息都会被误改状态。
      return message; // 修改代码+DesktopThreadStreaming：原样返回无关消息；如果没有这行，无关消息会丢失。
    } // 修改代码+DesktopThreadStreaming：跳过分支结束；如果没有这行，条件块语法不完整。
    return { ...message, status, text: text && text.length > 0 ? text : message.text, kind: message.kind ?? "normal" }; // 修改代码+DesktopThreadStreaming：更新目标消息状态和可选文本；如果没有这行，完成或失败正文无法回写。
  }); // 修改代码+DesktopThreadStreaming：消息遍历结束；如果没有这行，map 调用语法不完整。
} // 修改代码+DesktopThreadStreaming：函数段结束，updateMessagesForTurn 到此结束；如果没有这个边界，用户不容易看出旧事件同步范围。

export function threadReducer(state: ThreadState = initialThreadState, action: ThreadAction): ThreadState { // 修改代码+DesktopThreadStreaming：函数段开始，统一更新线程状态；如果没有这段，GUI 状态会散落且难以验收。
  if (action.type === "message_added") { // 修改代码+DesktopThreadStreaming：处理追加消息动作；如果没有这段，本地消息无法进入线程。
    return { ...state, messages: [...state.messages, { ...action.message, kind: action.message.kind ?? "normal" }] }; // 修改代码+DesktopThreadStreaming：追加带默认 kind 的消息；如果没有这行，ThreadView 需要防御缺失语义。
  } // 修改代码+DesktopThreadStreaming：追加消息分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "assistant_message_upserted") { // 新增代码+DesktopThreadStreaming：处理助手消息 upsert；如果没有这段，完成、拒绝和错误事件无法一等呈现。
    const status = action.message.status ?? state.activeTurnStatus; // 新增代码+DesktopThreadStreaming：读取新消息状态或沿用当前状态；如果没有这行，isRunning 判断缺少依据。
    const isRunning = runningStatuses.has(status); // 新增代码+DesktopThreadStreaming：计算是否仍运行；如果没有这行，终态消息可能继续禁用 composer。
    return { // 新增代码+DesktopThreadStreaming：返回 upsert 后的新状态；如果没有这行，reducer 没有输出。
      ...state, // 新增代码+DesktopThreadStreaming：保留未变化字段；如果没有这行，会话状态会被清空。
      activeTurnId: isRunning ? action.message.turnId ?? state.activeTurnId : state.activeTurnId, // 新增代码+DesktopThreadStreaming：运行中时记录活动 turn；如果没有这行，取消目标可能丢失。
      activeTurnStatus: status, // 新增代码+DesktopThreadStreaming：同步最新状态；如果没有这行，消息状态和线程状态会不一致。
      isRunning, // 新增代码+DesktopThreadStreaming：同步运行布尔值；如果没有这行，发送按钮状态会错误。
      errorMessage: action.message.kind === "error" ? action.message.text : null, // 新增代码+DesktopThreadStreaming：错误消息同步到状态层；如果没有这行，状态栏无法知道失败原因。
      messages: upsertAssistantMessage(state.messages, action.message), // 新增代码+DesktopThreadStreaming：插入或更新助手消息；如果没有这行，事件不会改变消息列表。
    }; // 新增代码+DesktopThreadStreaming：upsert 返回对象结束；如果没有这行，对象语法不完整。
  } // 新增代码+DesktopThreadStreaming：upsert 分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "message_delta_received") { // 新增代码+DesktopThreadStreaming：处理流式增量动作；如果没有这段，message_delta 无法显示在主线程。
    return { ...state, activeTurnId: action.turnId, activeTurnStatus: "running", isRunning: true, errorMessage: null, messages: appendDeltaToMessages(state.messages, action.turnId, action.textDelta) }; // 新增代码+DesktopThreadStreaming：追加 delta 并保持运行态；如果没有这行，流式文本不会实时增长。
  } // 新增代码+DesktopThreadStreaming：流式增量分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "turn_started") { // 修改代码+DesktopThreadStreaming：处理 turn 开始；如果没有这段，运行状态不会被记录。
    const status = action.status ?? "queued"; // 修改代码+DesktopThreadStreaming：默认进入 queued；如果没有这行，调用方每次都要传初始状态。
    return { ...state, activeTurnId: action.turnId, activeTurnStatus: status, isRunning: true, errorMessage: null }; // 修改代码+DesktopThreadStreaming：记录活动 turn；如果没有这行，composer 和取消按钮无法跟随运行。
  } // 修改代码+DesktopThreadStreaming：turn_started 分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "turn_status_changed") { // 修改代码+DesktopThreadStreaming：处理旧生命周期状态变化；如果没有这段，gui_turn_* 事件无法继续兼容。
    const isRunning = runningStatuses.has(action.status); // 修改代码+DesktopThreadStreaming：根据状态判断是否运行中；如果没有这行，终态会错误保持 busy。
    return { // 修改代码+DesktopThreadStreaming：返回状态变化后的对象；如果没有这行，reducer 没有输出。
      ...state, // 修改代码+DesktopThreadStreaming：保留未变化字段；如果没有这行，消息和会话状态会丢失。
      activeTurnId: isRunning ? action.turnId : state.activeTurnId, // 修改代码+DesktopThreadStreaming：运行中更新活动 turn；如果没有这行，取消按钮可能没有目标。
      activeTurnStatus: action.status, // 修改代码+DesktopThreadStreaming：记录最新状态；如果没有这行，状态标签会滞后。
      isRunning, // 修改代码+DesktopThreadStreaming：记录是否运行中；如果没有这行，发送按钮启停会错误。
      errorMessage: action.errorMessage ?? null, // 修改代码+DesktopThreadStreaming：保存错误或清空；如果没有这行，失败原因会丢失或污染。
      messages: updateMessagesForTurn(state.messages, action.turnId, action.status, action.text), // 修改代码+DesktopThreadStreaming：同步关联消息；如果没有这行，消息卡不会显示最新状态。
    }; // 修改代码+DesktopThreadStreaming：状态变化对象结束；如果没有这行，对象语法不完整。
  } // 修改代码+DesktopThreadStreaming：turn_status_changed 分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "turn_finished") { // 修改代码+DesktopThreadStreaming：处理当前 turn 结束；如果没有这段，UI 会停留在运行中。
    const status = action.status ?? "completed"; // 修改代码+DesktopThreadStreaming：默认成功完成；如果没有这行，调用方每次都要传 completed。
    const turnId = state.activeTurnId; // 修改代码+DesktopThreadStreaming：读取当前活动 turn；如果没有这行，消息状态同步没有目标。
    return { // 修改代码+DesktopThreadStreaming：返回结束后的状态；如果没有这行，reducer 没有输出。
      ...state, // 修改代码+DesktopThreadStreaming：保留消息和其他字段；如果没有这行，对话历史会丢失。
      activeTurnStatus: status, // 修改代码+DesktopThreadStreaming：记录终态；如果没有这行，状态标签不会更新。
      isRunning: false, // 修改代码+DesktopThreadStreaming：退出运行态；如果没有这行，发送按钮会一直禁用。
      errorMessage: action.errorMessage ?? null, // 修改代码+DesktopThreadStreaming：保存终态错误或清空；如果没有这行，失败原因无法保留。
      messages: turnId === null ? state.messages : updateMessagesForTurn(state.messages, turnId, status, action.text), // 修改代码+DesktopThreadStreaming：同步当前 turn 消息终态；如果没有这行，助手占位会停在 running。
    }; // 修改代码+DesktopThreadStreaming：turn_finished 返回对象结束；如果没有这行，对象语法不完整。
  } // 修改代码+DesktopThreadStreaming：turn_finished 分支结束；如果没有这行，条件块语法不完整。
  if (action.type === "thread_reset") { // 修改代码+DesktopThreadStreaming：处理线程重置；如果没有这段，恢复 session 时无法替换消息。
    return { ...initialThreadState, messages: (action.messages ?? []).map((message) => ({ ...message, kind: message.kind ?? "normal" })) }; // 修改代码+DesktopThreadStreaming：回到干净状态并补齐 kind；如果没有这行，旧 session 消息可能缺少语义字段。
  } // 修改代码+DesktopThreadStreaming：thread_reset 分支结束；如果没有这行，条件块语法不完整。
  return state; // 修改代码+DesktopThreadStreaming：未知动作返回原状态；如果没有这行，reducer 可能返回 undefined。
} // 修改代码+DesktopThreadStreaming：函数段结束，threadReducer 到此结束；如果没有这个边界，用户不容易看出状态机范围。
