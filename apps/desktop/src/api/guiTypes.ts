export const GUI_V2_TOKEN_HEADER = "X-OpenHarness-Desktop-Token"; // 新增代码+GuiV2ProtocolTypes：集中声明桌面 GUI V2 token header；如果没有这一行，前端 client 和后端协议可能再次写出不同字段。

export type GuiV2EventKind = // 新增代码+GuiV2ProtocolTypes：类型段开始，声明 V2 GUI 事件 kind 联合类型；如果没有这段，前端状态机只能接受任意字符串。
  | "turn_started" // 新增代码+GuiV2ProtocolTypes：表示 turn 开始；如果没有这一项，运行起点事件无法类型化。
  | "message_delta" // 新增代码+GuiV2ProtocolTypes：表示流式文本增量；如果没有这一项，打字式输出无法类型化。
  | "message_completed" // 新增代码+GuiV2ProtocolTypes：表示消息完成；如果没有这一项，完成态事件无法类型化。
  | "tool_started" // 新增代码+GuiV2ProtocolTypes：表示工具开始；如果没有这一项，TracePanel 起点无法类型化。
  | "tool_finished" // 新增代码+GuiV2ProtocolTypes：表示工具结束；如果没有这一项，TracePanel 结果无法类型化。
  | "permission_requested" // 新增代码+GuiV2ProtocolTypes：表示权限请求；如果没有这一项，权限弹窗来源无法类型化。
  | "permission_answered" // 新增代码+GuiV2ProtocolTypes：表示权限已回答；如果没有这一项，权限闭合事件无法类型化。
  | "safety_refusal" // 新增代码+GuiV2ProtocolTypes：表示安全拒绝；如果没有这一项，拒绝消息无法作为一等事件。
  | "turn_failed" // 新增代码+GuiV2ProtocolTypes：表示 turn 失败；如果没有这一项，失败态无法类型化。
  | "turn_cancelled" // 新增代码+GuiV2ProtocolTypes：表示 turn 取消；如果没有这一项，取消终态无法类型化。
  | "heartbeat"; // 新增代码+GuiV2ProtocolTypes：表示长任务保活；如果没有这一项，前端无法区分沉默和仍在运行。

export type GuiV2MessagePartKind = // 新增代码+GuiV2ProtocolTypes：类型段开始，声明 V2 消息片段 kind；如果没有这段，文本、拒绝、工具和错误片段会继续散成未知字符串。
  | "text_delta" // 新增代码+GuiV2ProtocolTypes：表示流式文本增量片段；如果没有这一项，增量消息无法类型化。
  | "final_text" // 新增代码+GuiV2ProtocolTypes：表示最终文本片段；如果没有这一项，完成消息无法类型化。
  | "refusal" // 新增代码+GuiV2ProtocolTypes：表示安全拒绝片段；如果没有这一项，拒绝正文无法类型化。
  | "tool_call" // 新增代码+GuiV2ProtocolTypes：表示工具调用片段；如果没有这一项，工具请求无法类型化。
  | "tool_result" // 新增代码+GuiV2ProtocolTypes：表示工具结果片段；如果没有这一项，工具输出无法类型化。
  | "error"; // 新增代码+GuiV2ProtocolTypes：表示错误片段；如果没有这一项，失败正文无法类型化。

export type GuiV2Event = { // 新增代码+GuiV2ProtocolTypes：类型段开始，描述后端 V2 事件形状；如果没有这段，renderer 只能把事件当未知对象。
  sequence: number; // 新增代码+GuiV2ProtocolTypes：事件序号；如果没有这一行，前端无法排序和增量回放。
  event_id: string; // 新增代码+GuiV2ProtocolTypes：事件唯一 id；如果没有这一行，去重和 React key 不稳定。
  kind: GuiV2EventKind; // 新增代码+GuiV2ProtocolTypes：事件类型；如果没有这一行，状态机无法按事件 kind 收窄。
  created_at: string; // 新增代码+GuiV2ProtocolTypes：事件创建时间；如果没有这一行，诊断时间线缺少时间依据。
  run_id: string; // 新增代码+GuiV2ProtocolTypes：运行 id；如果没有这一行，状态面板无法按 run 聚合。
  turn_id: string; // 新增代码+GuiV2ProtocolTypes：turn id；如果没有这一行，事件无法关联消息。
  payload: Record<string, unknown>; // 新增代码+GuiV2ProtocolTypes：事件业务载荷；如果没有这一行，工具、权限和消息详情都没有类型入口。
}; // 新增代码+GuiV2ProtocolTypes：事件类型结束；如果没有这一行，TypeScript 类型语法不完整。

export type GuiV2MessagePart = { // 新增代码+GuiV2ProtocolTypes：类型段开始，描述消息片段形状；如果没有这段，流式消息 reducer 没有统一输入。
  kind: GuiV2MessagePartKind; // 新增代码+GuiV2ProtocolTypes：消息片段类型；如果没有这一行，renderer 无法决定片段渲染方式。
  payload: Record<string, unknown>; // 新增代码+GuiV2ProtocolTypes：消息片段载荷；如果没有这一行，文本、工具或错误详情会丢失。
}; // 新增代码+GuiV2ProtocolTypes：消息片段类型结束；如果没有这一行，TypeScript 类型语法不完整。

export type GuiV2ErrorResponse = { // 新增代码+GuiV2ProtocolTypes：类型段开始，描述 V2 结构化错误响应；如果没有这段，client 只能抛泛化 Error。
  ok: false; // 新增代码+GuiV2ProtocolTypes：固定失败标记；如果没有这一行，前端无法用统一字段识别错误 payload。
  code: string; // 新增代码+GuiV2ProtocolTypes：机器可读错误码；如果没有这一行，UI 无法区分 busy、not_found、unauthorized。
  message: string; // 新增代码+GuiV2ProtocolTypes：人类可读错误文本；如果没有这一行，线程里只能显示 HTTP 状态码。
  error?: string; // 新增代码+GuiV2ProtocolTypes：兼容 V1 的错误别名；如果没有这一行，旧 error 字段过渡期会被类型排除。
  request_id: string; // 新增代码+GuiV2ProtocolTypes：请求关联 id；如果没有这一行，前端提示和后端日志无法对齐。
}; // 新增代码+GuiV2ProtocolTypes：错误响应类型结束；如果没有这一行，TypeScript 类型语法不完整。
