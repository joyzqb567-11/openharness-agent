export type StatusEvent = { // 新增代码+DesktopStatusStore：定义 GUI 可消费的状态事件；如果没有这段，工具卡片和状态栏会使用不透明对象。
  sequence: number; // 新增代码+DesktopStatusStore：保存事件递增序号；如果没有这行，前端无法增量轮询和去重。
  event_type: string; // 新增代码+DesktopStatusStore：保存事件类型；如果没有这行，UI 无法区分 tool、run、permission 事件。
  session_id: string; // 新增代码+DesktopStatusStore：保存 session id；如果没有这行，事件无法和会话关联。
  run_id: string; // 新增代码+DesktopStatusStore：保存 run id；如果没有这行，右侧面板无法按 run 聚合。
  turn_id: string; // 新增代码+DesktopStatusStore：保存 turn id；如果没有这行，事件无法更新对应消息状态。
  payload: Record<string, unknown>; // 新增代码+DesktopStatusStore：保存事件正文；如果没有这行，工具名、摘要和错误详情无法展示。
}; // 新增代码+DesktopStatusStore：StatusEvent 类型结束；如果没有这行，TypeScript 类型语法不完整。

export type StatusState = { // 新增代码+DesktopStatusStore：定义状态时间线整体状态；如果没有这段，轮询结果没有稳定存放位置。
  lastSequence: number; // 新增代码+DesktopStatusStore：保存最后事件序号；如果没有这行，轮询会重复拉全量事件。
  events: StatusEvent[]; // 新增代码+DesktopStatusStore：保存最近事件列表；如果没有这行，时间线没有可渲染数据。
}; // 新增代码+DesktopStatusStore：StatusState 类型结束；如果没有这行，TypeScript 类型语法不完整。

export const initialStatusState: StatusState = { // 新增代码+DesktopStatusStore：定义初始状态；如果没有这段，reducer 首次运行没有基准。
  lastSequence: 0, // 新增代码+DesktopStatusStore：初始游标为 0；如果没有这行，第一次轮询不知道从哪里开始。
  events: [], // 新增代码+DesktopStatusStore：初始没有事件；如果没有这行，事件列表可能是 undefined。
}; // 新增代码+DesktopStatusStore：初始状态结束；如果没有这行，对象语法不完整。

export function normalizeStatusEvent(rawEvent: Record<string, unknown>): StatusEvent { // 新增代码+DesktopStatusStore：函数段开始，把 bridge 原始事件规范成 UI 类型；如果没有这段，组件要重复做防御转换。
  return { // 新增代码+DesktopStatusStore：返回规范化事件；如果没有这行，函数没有输出。
    sequence: Number(rawEvent.sequence ?? 0), // 新增代码+DesktopStatusStore：转换序号为数字；如果没有这行，Math.max 和排序可能出错。
    event_type: String(rawEvent.event_type ?? ""), // 新增代码+DesktopStatusStore：转换事件类型为字符串；如果没有这行，UI 分支可能遇到 undefined。
    session_id: String(rawEvent.session_id ?? ""), // 新增代码+DesktopStatusStore：转换 session id；如果没有这行，事件归属字段不稳定。
    run_id: String(rawEvent.run_id ?? ""), // 新增代码+DesktopStatusStore：转换 run id；如果没有这行，状态面板无法稳定显示 run。
    turn_id: String(rawEvent.turn_id ?? ""), // 新增代码+DesktopStatusStore：转换 turn id；如果没有这行，消息状态更新无法匹配。
    payload: typeof rawEvent.payload === "object" && rawEvent.payload !== null ? (rawEvent.payload as Record<string, unknown>) : {}, // 新增代码+DesktopStatusStore：安全读取 payload；如果没有这行，坏事件会拖垮渲染。
  }; // 新增代码+DesktopStatusStore：规范化事件对象结束；如果没有这行，对象语法不完整。
} // 新增代码+DesktopStatusStore：函数段结束，normalizeStatusEvent 到此结束；如果没有这个边界，初学者不易看出事件清洗范围。

export function messageTextFromStatusEvent(event: StatusEvent): string | undefined { // 新增代码+DesktopFailedEventText：函数段开始，从状态事件里提取可写回消息卡的正文；如果没有这段代码，失败事件里的错误原因容易被空 answer 字段挡住。
  const answer = event.payload.answer; // 新增代码+DesktopFailedEventText：先读取后端 answer 字段；如果没有这行代码，成功完成事件无法复用同一提取逻辑。
  if (typeof answer === "string" && answer.length > 0) { // 新增代码+DesktopFailedEventText：只有非空 answer 才能作为正文；如果没有这行代码，空字符串会误覆盖真正的错误文本。
    return answer; // 新增代码+DesktopFailedEventText：返回成功回答；如果没有这行代码，完成消息会继续显示等待占位。
  } // 新增代码+DesktopFailedEventText：answer 判断结束；如果没有这行代码，条件块语法不完整。
  const error = event.payload.error; // 新增代码+DesktopFailedEventText：读取后端 error 字段；如果没有这行代码，失败事件无法展示可读原因。
  if (typeof error === "string" && error.length > 0) { // 新增代码+DesktopFailedEventText：只有非空 error 才能作为正文；如果没有这行代码，空错误会覆盖已有消息。
    return error; // 新增代码+DesktopFailedEventText：返回失败原因；如果没有这行代码，用户只能看到 failed 状态看不到为什么失败。
  } // 新增代码+DesktopFailedEventText：error 判断结束；如果没有这行代码，条件块语法不完整。
  return undefined; // 新增代码+DesktopFailedEventText：没有可显示文本时返回 undefined；如果没有这行代码，调用方无法保留原消息文本。
} // 新增代码+DesktopFailedEventText：函数段结束，messageTextFromStatusEvent 到此结束；如果没有这个边界，用户不容易看出事件正文提取范围。

export function appendStatusEvents(state: StatusState, events: StatusEvent[]): StatusState { // 新增代码+DesktopStatusStore：函数段开始，追加并去重状态事件；如果没有这段，轮询会重复显示旧事件。
  const mergedBySequence = new Map<number, StatusEvent>(); // 新增代码+DesktopStatusStore：按 sequence 建立去重表；如果没有这行，重复轮询会产生重复行。
  for (const event of state.events) { // 新增代码+DesktopStatusStore：先加入旧事件；如果没有这行，追加时会丢历史。
    mergedBySequence.set(event.sequence, event); // 新增代码+DesktopStatusStore：保存旧事件；如果没有这行，去重表没有基准。
  } // 新增代码+DesktopStatusStore：旧事件循环结束；如果没有这行，for 语法不完整。
  for (const event of events) { // 新增代码+DesktopStatusStore：再加入新事件；如果没有这行，轮询结果不会进入状态。
    mergedBySequence.set(event.sequence, event); // 新增代码+DesktopStatusStore：用新事件覆盖同序号旧事件；如果没有这行，重复事件无法去重。
  } // 新增代码+DesktopStatusStore：新事件循环结束；如果没有这行，for 语法不完整。
  const mergedEvents = [...mergedBySequence.values()].sort((left, right) => left.sequence - right.sequence).slice(-300); // 新增代码+DesktopStatusStore：排序并限制最多 300 条；如果没有这行，长任务会让前端越来越慢。
  const lastSequence = mergedEvents.reduce((current, event) => Math.max(current, event.sequence), state.lastSequence); // 新增代码+DesktopStatusStore：计算最新游标；如果没有这行，下一次轮询位置不准。
  return { lastSequence, events: mergedEvents }; // 新增代码+DesktopStatusStore：返回新状态；如果没有这行，React 无法感知事件变化。
} // 新增代码+DesktopStatusStore：函数段结束，appendStatusEvents 到此结束；如果没有这个边界，初学者不易看出事件追加范围。

export function latestPermissionEvent(events: StatusEvent[]): StatusEvent | null { // 新增代码+DesktopGUIPermissions：函数段开始，查找最新权限相关事件；如果没有这段，AppShell 需要手写事件过滤逻辑。
  const permissionEventTypes = new Set(["permission_required", "permission_requested", "permission_answered", "computer_use_permission_required", "gui_turn_needs_permission"]); // 修改代码+RealHarnessPermission：集中列出权限事件类型并包含真实 agent 请求；如果没有这行，permission_requested 不会驱动弹窗状态。
  const permissionEvents = events.filter((event) => permissionEventTypes.has(event.event_type)); // 新增代码+DesktopGUIPermissions：过滤权限事件；如果没有这行，弹窗可能被普通生命周期事件触发。
  return permissionEvents.at(-1) ?? null; // 新增代码+DesktopGUIPermissions：返回最新权限事件或空；如果没有这行，调用方无法判断是否要显示 banner/dialog。
} // 新增代码+DesktopGUIPermissions：函数段结束，latestPermissionEvent 到此结束；如果没有这个边界，初学者不易看出权限事件选择范围。
