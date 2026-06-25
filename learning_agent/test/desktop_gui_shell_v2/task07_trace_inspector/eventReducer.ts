import type { StatusEvent } from "./statusStore"; // 新增代码+DesktopEventReducer：引入后端状态事件类型；如果没有这行，事件 reducer 会和轮询数据合同分裂。
import type { ThreadAction, ThreadMessage, ThreadMessageKind, TurnStatus } from "./threadStore"; // 新增代码+DesktopEventReducer：引入线程动作和消息类型；如果没有这行，事件输出无法被 threadReducer 类型检查。

type EventReduction = { // 新增代码+DesktopEventReducer：类型段开始，定义事件转换结果；如果没有这段，调用方无法同时拿到动作和诊断。
  actions: ThreadAction[]; // 新增代码+DesktopEventReducer：保存要交给 threadReducer 的动作；如果没有这行，事件无法驱动主线程 UI。
  diagnostics: string[]; // 新增代码+DesktopEventReducer：保存未知或坏事件诊断；如果没有这行，后端新增事件会静默消失难以排查。
}; // 新增代码+DesktopEventReducer：类型段结束，EventReduction 到此结束；如果没有这行，TypeScript 类型语法不完整。

const legacyStatusByEventType: Record<string, TurnStatus> = { // 新增代码+DesktopEventReducer：建立旧 bridge 事件到线程状态的映射；如果没有这段，现有 gui_turn_* 事件会在迁移中失效。
  gui_turn_queued: "queued", // 新增代码+DesktopEventReducer：兼容旧排队事件；如果没有这行，刚提交的消息不会显示 queued。
  gui_turn_started: "running", // 新增代码+DesktopEventReducer：兼容旧开始事件；如果没有这行，用户看不到任务已开始。
  gui_turn_needs_permission: "needs_permission", // 新增代码+DesktopEventReducer：兼容旧权限事件；如果没有这行，权限等待态无法同步到消息。
  gui_turn_cancel_requested: "cancelling", // 新增代码+DesktopEventReducer：兼容旧取消中事件；如果没有这行，取消按钮点击后缺少中间反馈。
  gui_turn_completed: "completed", // 新增代码+DesktopEventReducer：兼容旧完成事件；如果没有这行，最终答案无法进入 completed。
  gui_turn_failed: "failed", // 新增代码+DesktopEventReducer：兼容旧失败事件；如果没有这行，失败只会留在右侧时间线。
  gui_turn_cancelled: "cancelled", // 新增代码+DesktopEventReducer：兼容旧已取消事件；如果没有这行，取消终态不会显示。
  turn_queued: "queued", // 新增代码+DesktopEventReducer：兼容 V2 原生排队事件；如果没有这行，原生事件流无法驱动排队状态。
  turn_started: "running", // 新增代码+DesktopEventReducer：兼容 V2 原生开始事件；如果没有这行，SSE 开始事件无法更新 UI。
  turn_needs_permission: "needs_permission", // 新增代码+DesktopEventReducer：兼容 V2 原生权限事件；如果没有这行，权限流式事件无法更新消息。
  turn_cancel_requested: "cancelling", // 新增代码+DesktopEventReducer：兼容 V2 原生取消中事件；如果没有这行，SSE 取消反馈会丢失。
  turn_completed: "completed", // 新增代码+DesktopEventReducer：兼容 V2 原生完成事件；如果没有这行，原生终态无法完成消息。
  turn_cancelled: "cancelled", // 新增代码+DesktopEventReducer：兼容 V2 原生取消终态；如果没有这行，取消消息无法进入终态。
}; // 新增代码+DesktopEventReducer：映射表结束；如果没有这行，对象语法不完整。

function stringFromPayload(payload: Record<string, unknown>, keys: string[]): string { // 新增代码+DesktopEventReducer：函数段开始，从 payload 多个候选字段中取文本；如果没有这段，不同后端字段名会反复写分支。
  for (const key of keys) { // 新增代码+DesktopEventReducer：遍历候选字段；如果没有这行，只能读取一个固定字段。
    const value = payload[key]; // 新增代码+DesktopEventReducer：读取当前字段值；如果没有这行，无法判断该字段是否可用。
    if (typeof value === "string" && value.length > 0) { // 新增代码+DesktopEventReducer：只接受非空字符串；如果没有这行，空字段可能覆盖已有流式文本。
      return value; // 新增代码+DesktopEventReducer：返回第一个可用文本；如果没有这行，函数无法输出匹配结果。
    } // 新增代码+DesktopEventReducer：字段可用判断结束；如果没有这行，条件块语法不完整。
  } // 新增代码+DesktopEventReducer：候选字段遍历结束；如果没有这行，for 循环语法不完整。
  return ""; // 新增代码+DesktopEventReducer：没有文本时返回空字符串；如果没有这行，调用方要处理 undefined。
} // 新增代码+DesktopEventReducer：函数段结束，stringFromPayload 到此结束；如果没有这个边界，用户不容易看出字段提取范围。

function diagnostic(message: string): EventReduction { // 新增代码+DesktopEventReducer：函数段开始，生成无动作诊断结果；如果没有这段，异常事件处理会重复样板代码。
  return { actions: [], diagnostics: [message] }; // 新增代码+DesktopEventReducer：返回诊断结果；如果没有这行，调用方无法知道事件为什么被忽略。
} // 新增代码+DesktopEventReducer：函数段结束，diagnostic 到此结束；如果没有这个边界，用户不容易看出诊断结构。

function ok(actions: ThreadAction[]): EventReduction { // 新增代码+DesktopEventReducer：函数段开始，生成成功转换结果；如果没有这段，正常事件也要重复写 diagnostics 空数组。
  return { actions, diagnostics: [] }; // 新增代码+DesktopEventReducer：返回动作和空诊断；如果没有这行，调用方无法统一处理转换结果。
} // 新增代码+DesktopEventReducer：函数段结束，ok 到此结束；如果没有这个边界，用户不容易看出成功结构。

function assistantMessage(event: StatusEvent, text: string, status: TurnStatus, kind: ThreadMessageKind = "normal"): ThreadMessage { // 新增代码+DesktopEventReducer：函数段开始，构造标准助手消息；如果没有这段，完成、拒绝和错误事件会各自拼装不同形状。
  return { // 新增代码+DesktopEventReducer：返回助手消息对象；如果没有这行，函数没有输出。
    id: `assistant_${event.turn_id}`, // 新增代码+DesktopEventReducer：按 turn id 生成稳定消息 id；如果没有这行，同一 turn 的消息无法被 upsert。
    role: "assistant", // 新增代码+DesktopEventReducer：把事件产物声明为助手消息；如果没有这行，ThreadView 无法按助手样式渲染。
    text, // 新增代码+DesktopEventReducer：写入可见正文；如果没有这行，用户看不到最终答案、拒绝或错误。
    turnId: event.turn_id, // 新增代码+DesktopEventReducer：保留后端 turn id；如果没有这行，重试和后续事件无法定位。
    status, // 新增代码+DesktopEventReducer：写入生命周期状态；如果没有这行，消息标签和重试入口无法判断。
    kind, // 新增代码+DesktopEventReducer：写入消息语义；如果没有这行，拒绝和错误无法显示专门标签。
  }; // 新增代码+DesktopEventReducer：助手消息对象结束；如果没有这行，对象语法不完整。
} // 新增代码+DesktopEventReducer：函数段结束，assistantMessage 到此结束；如果没有这个边界，用户不容易看出消息构造范围。

function requireTurnId(event: StatusEvent): string | null { // 新增代码+DesktopEventReducer：函数段开始，校验事件是否带 turn id；如果没有这段，坏事件可能创建无法重试的消息。
  return event.turn_id.length > 0 ? event.turn_id : null; // 新增代码+DesktopEventReducer：返回有效 turn id 或空；如果没有这行，调用方无法统一拦截坏事件。
} // 新增代码+DesktopEventReducer：函数段结束，requireTurnId 到此结束；如果没有这个边界，用户不容易看出 turn 校验范围。

function reduceLegacyStatusEvent(event: StatusEvent, status: TurnStatus): EventReduction { // 新增代码+DesktopEventReducer：函数段开始，处理旧生命周期事件；如果没有这段，V1/V2 迁移期会断掉旧桥接行为。
  if (requireTurnId(event) === null) { // 新增代码+DesktopEventReducer：拦截缺少 turn id 的生命周期事件；如果没有这行，状态动作无法定位消息。
    return diagnostic(`ignored ${event.event_type}: missing turn_id`); // 新增代码+DesktopEventReducer：返回可读诊断；如果没有这行，缺字段事件会静默失败。
  } // 新增代码+DesktopEventReducer：turn id 校验结束；如果没有这行，条件块语法不完整。
  if (status === "completed") { // 新增代码+DesktopEventReducer：处理完成终态；如果没有这段，旧完成事件可能只改状态不写答案。
    const text = stringFromPayload(event.payload, ["answer", "final_text", "text"]); // 新增代码+DesktopEventReducer：读取最终答案；如果没有这行，完成消息没有正文来源。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "completed") }]); // 新增代码+DesktopEventReducer：生成完成消息 upsert；如果没有这行，主线程看不到最终回答。
  } // 新增代码+DesktopEventReducer：完成终态分支结束；如果没有这行，条件块语法不完整。
  if (status === "failed") { // 新增代码+DesktopEventReducer：处理失败终态；如果没有这段，旧失败事件无法成为线程内错误。
    const text = stringFromPayload(event.payload, ["error", "message", "error_message"]) || "本轮运行失败。"; // 新增代码+DesktopEventReducer：读取失败原因并兜底；如果没有这行，用户可能只看到空错误。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "failed", "error") }]); // 新增代码+DesktopEventReducer：生成错误消息 upsert；如果没有这行，失败只会藏在状态栏。
  } // 新增代码+DesktopEventReducer：失败终态分支结束；如果没有这行，条件块语法不完整。
  if (status === "cancelled") { // 新增代码+DesktopEventReducer：处理取消终态；如果没有这段，取消完成后消息状态无法终止。
    const text = stringFromPayload(event.payload, ["message", "error", "summary"]) || "本轮已取消。"; // 新增代码+DesktopEventReducer：读取取消说明并兜底；如果没有这行，取消消息可能没有正文。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "cancelled") }]); // 新增代码+DesktopEventReducer：生成取消消息 upsert；如果没有这行，取消终态可能丢失。
  } // 新增代码+DesktopEventReducer：取消终态分支结束；如果没有这行，条件块语法不完整。
  return ok([{ type: "turn_status_changed", turnId: event.turn_id, status }]); // 新增代码+DesktopEventReducer：非终态只同步状态；如果没有这行，queued/running/permission/cancelling 不会更新消息标签。
} // 新增代码+DesktopEventReducer：函数段结束，reduceLegacyStatusEvent 到此结束；如果没有这个边界，用户不容易看出兼容范围。

export type TraceToolStatus = "running" | "completed" | "failed"; // 新增代码+DesktopTraceInspector：定义工具轨迹状态类型；如果没有这行，TracePanel 会把状态当任意字符串。

export type TraceToolRow = { // 新增代码+DesktopTraceInspector：类型段开始，定义工具轨迹行；如果没有这段，工具面板字段会散落在组件里。
  id: string; // 新增代码+DesktopTraceInspector：保存工具调用稳定 id；如果没有这行，started/finished 事件无法合并。
  sequence: number; // 新增代码+DesktopTraceInspector：保存最新事件序号；如果没有这行，轨迹排序和诊断缺少事实。
  runId: string; // 新增代码+DesktopTraceInspector：保存 run id；如果没有这行，用户无法把工具调用归属到一次运行。
  turnId: string; // 新增代码+DesktopTraceInspector：保存 turn id；如果没有这行，用户无法把工具调用归属到一轮对话。
  toolName: string; // 新增代码+DesktopTraceInspector：保存工具名；如果没有这行，工具面板没有主标题。
  status: TraceToolStatus; // 新增代码+DesktopTraceInspector：保存工具状态；如果没有这行，用户无法区分运行、成功和失败。
  durationMs?: number; // 新增代码+DesktopTraceInspector：保存耗时；如果没有这行，慢工具无法被识别。
  argsPreview: string; // 新增代码+DesktopTraceInspector：保存脱敏参数摘要；如果没有这行，用户看不到工具输入上下文。
  resultSummary: string; // 新增代码+DesktopTraceInspector：保存结果摘要；如果没有这行，工具完成后没有可读输出。
  errorCode: string; // 新增代码+DesktopTraceInspector：保存错误码；如果没有这行，失败排查只能看自然语言。
  diagnosticText: string; // 新增代码+DesktopTraceInspector：保存可复制诊断文本；如果没有这行，复制按钮没有稳定内容。
}; // 新增代码+DesktopTraceInspector：工具轨迹行类型结束；如果没有这行，TypeScript 类型语法不完整。

const sensitiveTraceKeyPattern = /token|secret|password|api[_-]?key|authorization|credential/i; // 新增代码+DesktopTraceInspector：定义敏感字段名规则；如果没有这行，token/password 等键可能原样显示。
const windowsTracePathPattern = /[A-Za-z]:\\(?:[^\s\\/:*?"<>|]+\\)*[^\s\\/:*?"<>|]+/g; // 新增代码+DesktopTraceInspector：定义 Windows 路径规则；如果没有这行，用户本机目录可能显示到 trace panel。
const secretTraceValuePattern = /(sk-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+)/gi; // 新增代码+DesktopTraceInspector：定义常见密钥值规则；如果没有这行，API key 或 bearer token 可能出现在参数预览。

function redactTraceValue(value: unknown, key = ""): unknown { // 新增代码+DesktopTraceInspector：函数段开始，递归脱敏 trace 值；如果没有这段，工具参数会把敏感内容带进 UI。
  if (sensitiveTraceKeyPattern.test(key)) { // 新增代码+DesktopTraceInspector：先按字段名判断敏感字段；如果没有这行，token 字段即使值不匹配正则也会外泄。
    return "[redacted]"; // 新增代码+DesktopTraceInspector：返回统一脱敏占位；如果没有这行，敏感字段没有替换结果。
  } // 新增代码+DesktopTraceInspector：敏感字段名判断结束；如果没有这行，条件块语法不完整。
  if (typeof value === "string") { // 新增代码+DesktopTraceInspector：处理字符串值；如果没有这行，路径和密钥正则无法执行。
    return value.replace(windowsTracePathPattern, "[redacted]").replace(secretTraceValuePattern, "[redacted]"); // 新增代码+DesktopTraceInspector：隐藏路径和凭证；如果没有这行，敏感字符串会原样显示。
  } // 新增代码+DesktopTraceInspector：字符串分支结束；如果没有这行，条件块语法不完整。
  if (Array.isArray(value)) { // 新增代码+DesktopTraceInspector：处理数组值；如果没有这行，数组里的敏感字符串不会被脱敏。
    return value.map((item) => redactTraceValue(item)); // 新增代码+DesktopTraceInspector：递归脱敏数组项；如果没有这行，嵌套参数会漏检。
  } // 新增代码+DesktopTraceInspector：数组分支结束；如果没有这行，条件块语法不完整。
  if (typeof value === "object" && value !== null) { // 新增代码+DesktopTraceInspector：处理对象值；如果没有这行，嵌套对象里的密钥字段会外泄。
    return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([entryKey, entryValue]) => [entryKey, redactTraceValue(entryValue, entryKey)])); // 新增代码+DesktopTraceInspector：递归脱敏对象字段；如果没有这行，args 里的敏感字段不会被替换。
  } // 新增代码+DesktopTraceInspector：对象分支结束；如果没有这行，条件块语法不完整。
  return value; // 新增代码+DesktopTraceInspector：非字符串标量原样返回；如果没有这行，数字和布尔值会丢失。
} // 新增代码+DesktopTraceInspector：函数段结束，redactTraceValue 到此结束；如果没有这个边界，用户不容易看出脱敏范围。

function previewTraceValue(value: unknown): string { // 新增代码+DesktopTraceInspector：函数段开始，把 trace 值转成短文本；如果没有这段，TracePanel 要重复 JSON 预览逻辑。
  try { // 新增代码+DesktopTraceInspector：保护 JSON 序列化；如果没有这行，循环引用参数会打坏前端。
    const preview = JSON.stringify(redactTraceValue(value)); // 新增代码+DesktopTraceInspector：序列化脱敏后的值；如果没有这行，参数预览无法稳定显示。
    const safePreview = preview ?? ""; // 新增代码+DesktopTraceInspector：处理 undefined 序列化结果；如果没有这行，slice 可能访问 undefined。
    return safePreview.length > 220 ? `${safePreview.slice(0, 217)}...` : safePreview; // 新增代码+DesktopTraceInspector：限制预览长度；如果没有这行，超长参数会撑破右栏。
  } catch { // 新增代码+DesktopTraceInspector：捕获无法序列化的值；如果没有这行，坏参数会让整个 UI 崩溃。
    return "[unserializable]"; // 新增代码+DesktopTraceInspector：返回稳定兜底文本；如果没有这行，循环引用没有可显示结果。
  } // 新增代码+DesktopTraceInspector：序列化异常处理结束；如果没有这行，try/catch 语法不完整。
} // 新增代码+DesktopTraceInspector：函数段结束，previewTraceValue 到此结束；如果没有这个边界，用户不容易看出预览范围。

function traceStringFromPayload(payload: Record<string, unknown>, keys: string[]): string { // 新增代码+DesktopTraceInspector：函数段开始，从工具 payload 中读取字符串；如果没有这段，字段名兼容会重复散落。
  return redactTraceValue(stringFromPayload(payload, keys)) as string; // 新增代码+DesktopTraceInspector：复用通用文本读取并脱敏；如果没有这行，结果摘要可能暴露敏感值。
} // 新增代码+DesktopTraceInspector：函数段结束，traceStringFromPayload 到此结束；如果没有这个边界，用户不容易看出字符串提取范围。

function traceCallId(event: StatusEvent): string { // 新增代码+DesktopTraceInspector：函数段开始，提取工具调用 id；如果没有这段，started/finished 事件无法稳定合并。
  return traceStringFromPayload(event.payload, ["tool_call_id", "call_id", "id"]) || `${event.run_id}:${event.turn_id}:${event.sequence}`; // 新增代码+DesktopTraceInspector：返回 payload id 或事件兜底 id；如果没有这行，缺 id 工具事件会丢失。
} // 新增代码+DesktopTraceInspector：函数段结束，traceCallId 到此结束；如果没有这个边界，用户不容易看出 id 来源。

function traceToolName(event: StatusEvent): string { // 新增代码+DesktopTraceInspector：函数段开始，提取工具名；如果没有这段，工具标题字段会不一致。
  return traceStringFromPayload(event.payload, ["tool_name", "name", "tool", "server_tool_name"]) || "tool"; // 新增代码+DesktopTraceInspector：返回工具名或兜底；如果没有这行，空工具名会造成面板空标题。
} // 新增代码+DesktopTraceInspector：函数段结束，traceToolName 到此结束；如果没有这个边界，用户不容易看出工具名来源。

function traceDuration(payload: Record<string, unknown>): number | undefined { // 新增代码+DesktopTraceInspector：函数段开始，提取工具耗时；如果没有这段，duration 字段要在组件里猜。
  const duration = payload.duration_ms ?? payload.elapsed_ms; // 新增代码+DesktopTraceInspector：兼容 duration_ms 和 elapsed_ms；如果没有这行，不同后端字段无法复用。
  return typeof duration === "number" && Number.isFinite(duration) ? duration : undefined; // 新增代码+DesktopTraceInspector：只接受有限数字；如果没有这行，坏耗时可能污染 UI。
} // 新增代码+DesktopTraceInspector：函数段结束，traceDuration 到此结束；如果没有这个边界，用户不容易看出耗时提取范围。

function traceResultSummary(payload: Record<string, unknown>, failed: boolean): string { // 新增代码+DesktopTraceInspector：函数段开始，提取结果摘要；如果没有这段，成功和失败摘要会各写一套。
  if (failed) { // 新增代码+DesktopTraceInspector：失败优先读取错误文案；如果没有这行，失败工具可能显示空摘要。
    return traceStringFromPayload(payload, ["error_message", "message", "error", "summary"]) || "工具调用失败。"; // 新增代码+DesktopTraceInspector：返回失败摘要并兜底；如果没有这行，用户看不到失败原因。
  } // 新增代码+DesktopTraceInspector：失败分支结束；如果没有这行，条件块语法不完整。
  return traceStringFromPayload(payload, ["result_summary", "output_summary", "summary", "stdout", "output", "result"]) || ""; // 新增代码+DesktopTraceInspector：返回成功摘要；如果没有这行，工具完成后没有输出上下文。
} // 新增代码+DesktopTraceInspector：函数段结束，traceResultSummary 到此结束；如果没有这个边界，用户不容易看出摘要来源。

function buildTraceDiagnostic(row: Omit<TraceToolRow, "diagnosticText">): string { // 新增代码+DesktopTraceInspector：函数段开始，生成可复制诊断文本；如果没有这段，复制按钮没有稳定格式。
  return [`tool=${row.toolName}`, `status=${row.status}`, `run_id=${row.runId}`, `turn_id=${row.turnId}`, `duration_ms=${row.durationMs ?? ""}`, `error_code=${row.errorCode}`, `args=${row.argsPreview}`, `result=${row.resultSummary}`].join("\n"); // 新增代码+DesktopTraceInspector：拼接关键诊断字段；如果没有这行，复制内容无法帮助排查。
} // 新增代码+DesktopTraceInspector：函数段结束，buildTraceDiagnostic 到此结束；如果没有这个边界，用户不容易看出诊断格式。

export function reduceGuiEventToTraceRows(rows: TraceToolRow[], event: StatusEvent): TraceToolRow[] { // 新增代码+DesktopTraceInspector：函数段开始，把工具事件转换为 trace row；如果没有这段，TracePanel 无法从事件流得到状态。
  if (event.event_type !== "tool_started" && event.event_type !== "tool_finished" && event.event_type !== "tool_failed") { // 新增代码+DesktopTraceInspector：只处理工具事件；如果没有这行，普通生命周期事件会污染工具轨迹。
    return rows; // 新增代码+DesktopTraceInspector：非工具事件保持原状态；如果没有这行，未知事件可能清空轨迹。
  } // 新增代码+DesktopTraceInspector：工具事件类型判断结束；如果没有这行，条件块语法不完整。
  const id = traceCallId(event); // 新增代码+DesktopTraceInspector：提取工具调用 id；如果没有这行，started/finished 无法合并。
  const existingRow = rows.find((row) => row.id === id); // 新增代码+DesktopTraceInspector：查找已有轨迹；如果没有这行，完成事件会重复创建新卡片。
  const failed = event.event_type === "tool_failed" || event.payload.ok === false || Boolean(event.payload.error_code ?? event.payload.error_message ?? event.payload.error); // 新增代码+DesktopTraceInspector：判断工具是否失败；如果没有这行，失败工具会被显示为完成。
  const status: TraceToolStatus = event.event_type === "tool_started" && !failed ? "running" : failed ? "failed" : "completed"; // 新增代码+DesktopTraceInspector：计算展示状态；如果没有这行，工具状态无法进入 UI。
  const baseRow = { // 新增代码+DesktopTraceInspector：构造无诊断版本的轨迹行；如果没有这段，后续字段合并会重复写对象。
    id, // 新增代码+DesktopTraceInspector：保存工具调用 id；如果没有这行，React key 和合并都不稳定。
    sequence: event.sequence, // 新增代码+DesktopTraceInspector：保存最新事件序号；如果没有这行，排序和复制诊断缺少序号。
    runId: event.run_id, // 新增代码+DesktopTraceInspector：保存 run id；如果没有这行，用户无法定位运行。
    turnId: event.turn_id, // 新增代码+DesktopTraceInspector：保存 turn id；如果没有这行，用户无法定位对话轮次。
    toolName: traceToolName(event), // 新增代码+DesktopTraceInspector：保存工具名；如果没有这行，工具卡片没有标题。
    status, // 新增代码+DesktopTraceInspector：保存计算后的状态；如果没有这行，工具卡片没有状态。
    durationMs: traceDuration(event.payload) ?? existingRow?.durationMs, // 新增代码+DesktopTraceInspector：保存耗时或沿用旧耗时；如果没有这行，完成事件的耗时会丢失。
    argsPreview: event.payload.args !== undefined ? previewTraceValue(event.payload.args) : existingRow?.argsPreview ?? "", // 新增代码+DesktopTraceInspector：保存脱敏参数预览；如果没有这行，用户看不到工具输入。
    resultSummary: event.event_type === "tool_started" ? existingRow?.resultSummary ?? "" : traceResultSummary(event.payload, failed), // 新增代码+DesktopTraceInspector：保存结果摘要；如果没有这行，完成和失败没有可读输出。
    errorCode: traceStringFromPayload(event.payload, ["error_code", "code"]) || (existingRow?.errorCode ?? ""), // 新增代码+DesktopTraceInspector：保存错误码；如果没有这行，失败排查少一个机器码。
  } satisfies Omit<TraceToolRow, "diagnosticText">; // 新增代码+DesktopTraceInspector：要求 baseRow 满足轨迹字段；如果没有这行，缺字段不会被 TypeScript 捕获。
  const nextRow: TraceToolRow = { ...baseRow, diagnosticText: buildTraceDiagnostic(baseRow) }; // 新增代码+DesktopTraceInspector：补上可复制诊断文本；如果没有这行，复制按钮没有内容。
  return existingRow ? rows.map((row) => row.id === id ? nextRow : row) : [...rows, nextRow]; // 新增代码+DesktopTraceInspector：更新已有行或追加新行；如果没有这行，工具轨迹不会进入状态。
} // 新增代码+DesktopTraceInspector：函数段结束，reduceGuiEventToTraceRows 到此结束；如果没有这个边界，用户不容易看出工具轨迹转换范围。

export function reduceGuiEventToThreadActions(event: StatusEvent): EventReduction { // 新增代码+DesktopEventReducer：函数段开始，把 GUI 事件转换为线程动作；如果没有这段，后端事件无法驱动 Codex 风格主线程。
  if (event.event_type === "message_delta") { // 新增代码+DesktopEventReducer：处理流式增量事件；如果没有这段，实时输出不会进入消息区。
    if (requireTurnId(event) === null) { // 新增代码+DesktopEventReducer：校验增量事件 turn id；如果没有这行，delta 无法定位消息。
      return diagnostic("ignored message_delta: missing turn_id"); // 新增代码+DesktopEventReducer：返回缺 turn 诊断；如果没有这行，坏 delta 难排查。
    } // 新增代码+DesktopEventReducer：增量 turn 校验结束；如果没有这行，条件块语法不完整。
    const textDelta = stringFromPayload(event.payload, ["text_delta", "delta", "text"]); // 新增代码+DesktopEventReducer：读取增量正文；如果没有这行，后端字段名差异会导致 streaming 丢失。
    return textDelta.length > 0 ? ok([{ type: "message_delta_received", turnId: event.turn_id, textDelta }]) : diagnostic("ignored message_delta: empty text_delta"); // 新增代码+DesktopEventReducer：输出增量动作或空文本诊断；如果没有这行，空事件可能污染消息。
  } // 新增代码+DesktopEventReducer：message_delta 分支结束；如果没有这行，条件块语法不完整。
  if (event.event_type === "message_completed") { // 新增代码+DesktopEventReducer：处理最终消息事件；如果没有这段，完成文本无法覆盖流式草稿。
    if (requireTurnId(event) === null) { // 新增代码+DesktopEventReducer：校验完成事件 turn id；如果没有这行，完成消息无法 upsert。
      return diagnostic("ignored message_completed: missing turn_id"); // 新增代码+DesktopEventReducer：返回缺 turn 诊断；如果没有这行，坏完成事件难排查。
    } // 新增代码+DesktopEventReducer：完成 turn 校验结束；如果没有这行，条件块语法不完整。
    const text = stringFromPayload(event.payload, ["final_text", "answer", "text"]); // 新增代码+DesktopEventReducer：读取最终正文；如果没有这行，完成消息没有可见内容。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "completed") }]); // 新增代码+DesktopEventReducer：输出最终消息动作；如果没有这行，主线程不会进入完成态。
  } // 新增代码+DesktopEventReducer：message_completed 分支结束；如果没有这行，条件块语法不完整。
  if (event.event_type === "safety_refusal") { // 新增代码+DesktopEventReducer：处理安全拒绝事件；如果没有这段，拒绝会藏在状态流里。
    if (requireTurnId(event) === null) { // 新增代码+DesktopEventReducer：校验拒绝事件 turn id；如果没有这行，拒绝消息无法重试或定位。
      return diagnostic("ignored safety_refusal: missing turn_id"); // 新增代码+DesktopEventReducer：返回缺 turn 诊断；如果没有这行，坏拒绝事件难排查。
    } // 新增代码+DesktopEventReducer：拒绝 turn 校验结束；如果没有这行，条件块语法不完整。
    const text = stringFromPayload(event.payload, ["text", "refusal", "message"]) || "出于安全原因，我不能帮助完成这个请求。"; // 新增代码+DesktopEventReducer：读取拒绝正文并兜底；如果没有这行，用户看不到安全原因。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "completed", "refusal") }]); // 新增代码+DesktopEventReducer：输出拒绝消息动作；如果没有这行，拒绝不是一等消息。
  } // 新增代码+DesktopEventReducer：safety_refusal 分支结束；如果没有这行，条件块语法不完整。
  if (event.event_type === "turn_failed") { // 新增代码+DesktopEventReducer：处理 V2 原生失败事件；如果没有这段，adapter 错误无法进入主线程。
    if (requireTurnId(event) === null) { // 新增代码+DesktopEventReducer：校验失败事件 turn id；如果没有这行，错误消息无法重试。
      return diagnostic("ignored turn_failed: missing turn_id"); // 新增代码+DesktopEventReducer：返回缺 turn 诊断；如果没有这行，坏失败事件难排查。
    } // 新增代码+DesktopEventReducer：失败 turn 校验结束；如果没有这行，条件块语法不完整。
    const text = stringFromPayload(event.payload, ["error", "message", "error_message"]) || "本轮运行失败。"; // 新增代码+DesktopEventReducer：读取失败正文并兜底；如果没有这行，失败消息可能为空。
    return ok([{ type: "assistant_message_upserted", message: assistantMessage(event, text, "failed", "error") }]); // 新增代码+DesktopEventReducer：输出错误消息动作；如果没有这行，失败只显示在右栏。
  } // 新增代码+DesktopEventReducer：turn_failed 分支结束；如果没有这行，条件块语法不完整。
  const legacyStatus = legacyStatusByEventType[event.event_type]; // 新增代码+DesktopEventReducer：读取兼容生命周期状态；如果没有这行，旧事件无法复用统一转换。
  if (legacyStatus !== undefined) { // 新增代码+DesktopEventReducer：判断是否是已知生命周期事件；如果没有这行，无法进入兼容分支。
    return reduceLegacyStatusEvent(event, legacyStatus); // 新增代码+DesktopEventReducer：委托兼容处理；如果没有这行，状态事件不会生成线程动作。
  } // 新增代码+DesktopEventReducer：兼容分支结束；如果没有这行，条件块语法不完整。
  return diagnostic(`ignored ${event.event_type}: unsupported event_type`); // 新增代码+DesktopEventReducer：未知事件返回诊断；如果没有这行，未来事件可能无声失败或抛错。
} // 新增代码+DesktopEventReducer：函数段结束，reduceGuiEventToThreadActions 到此结束；如果没有这个边界，用户不容易看出事件转换范围。
