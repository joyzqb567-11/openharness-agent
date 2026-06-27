import type { ModelCallEventType, ModelCallPhase } from "../api/guiProviderTypes"; // 新增代码+RealModelLatencyV2：引入模型调用事件和阶段类型；如果没有这行，状态组件会把关键阶段当成散落字符串。
import type { StatusEvent } from "../state/statusStore"; // 新增代码+RealModelLatencyV2：引入状态事件类型；如果没有这行，事件转换 helper 无法和轮询数据对齐。

export type ModelCallStatusView = { // 新增代码+RealModelLatencyV2：类型段开始，定义 UI 可展示的模型调用状态；如果没有这段，Composer 和右栏会各自解析 payload。
  eventType: ModelCallEventType; // 新增代码+RealModelLatencyV2：保存来源事件类型；如果没有这行，失败/完成/阶段更新无法追踪来源。
  phase: ModelCallPhase; // 新增代码+RealModelLatencyV2：保存模型调用阶段；如果没有这行，状态条不知道应该显示哪句中文。
  message: string; // 新增代码+RealModelLatencyV2：保存后端原始短消息；如果没有这行，失败原因和 title 诊断会丢失。
  modelId: string; // 新增代码+RealModelLatencyV2：保存模型 id；如果没有这行，用户不知道正在调用 GPT-5.5 还是其他模型。
  providerId: string; // 新增代码+RealModelLatencyV2：保存 provider id；如果没有这行，后续多 provider 排查缺少来源。
  elapsedMs: number; // 新增代码+RealModelLatencyV2：保存后端阶段耗时；如果没有这行，慢调用没有可见时间证据。
}; // 新增代码+RealModelLatencyV2：状态 view 类型结束；如果没有这行，TypeScript 类型语法不完整。

const MODEL_CALL_EVENT_TYPES: ModelCallEventType[] = [ // 新增代码+RealModelLatencyV2：集中列出模型调用事件；如果没有这段，helper 和 reducer 会各写一套白名单。
  "model_call_started", // 新增代码+RealModelLatencyV2：列入调用开始事件；如果没有这行，连接起点不会被状态条识别。
  "model_call_status", // 新增代码+RealModelLatencyV2：列入阶段更新事件；如果没有这行，fallback 等中间状态不会被识别。
  "model_first_delta", // 新增代码+RealModelLatencyV2：列入首增量事件；如果没有这行，首 token 反馈不会被识别。
  "model_call_completed", // 新增代码+RealModelLatencyV2：列入完成事件；如果没有这行，完成状态不会被识别。
  "model_call_failed", // 新增代码+RealModelLatencyV2：列入失败事件；如果没有这行，模型不可用不会被状态条识别。
]; // 新增代码+RealModelLatencyV2：模型调用事件列表结束；如果没有这行，数组语法不完整。

const MODEL_CALL_PHASES: ModelCallPhase[] = [ // 新增代码+RealModelLatencyV2：集中列出合法阶段；如果没有这段，payload 里的坏 phase 会直接污染 UI。
  "queued", // 新增代码+RealModelLatencyV2：允许排队阶段；如果没有这行，排队状态会被丢弃。
  "started", // 新增代码+RealModelLatencyV2：允许开始阶段；如果没有这行，起点状态会被丢弃。
  "connecting", // 新增代码+RealModelLatencyV2：允许连接阶段；如果没有这行，连接状态会被丢弃。
  "auth_checking", // 新增代码+RealModelLatencyV2：允许认证检查阶段；如果没有这行，OAuth 检查状态会被丢弃。
  "websocket_connecting", // 新增代码+RealModelLatencyV2：允许 WebSocket 连接阶段；如果没有这行，WebSocket 轨道不可见。
  "websocket_timeout", // 新增代码+RealModelLatencyV2：允许 WebSocket 超时阶段；如果没有这行，慢路径根因不可见。
  "https_fallback", // 新增代码+RealModelLatencyV2：允许 HTTPS fallback 阶段；如果没有这行，切换轨道不可见。
  "streaming", // 新增代码+RealModelLatencyV2：允许流式接收阶段；如果没有这行，输出中状态不可见。
  "first_delta", // 新增代码+RealModelLatencyV2：允许首个增量阶段；如果没有这行，TTFT 成功信号不可见。
  "completed", // 新增代码+RealModelLatencyV2：允许完成阶段；如果没有这行，完成终态不可见。
  "cancel_requested", // 新增代码+RealModelLatencyV2：允许取消请求阶段；如果没有这行，取消中不可见。
  "cancelled", // 新增代码+RealModelLatencyV2：允许已取消阶段；如果没有这行，取消终态不可见。
  "failed", // 新增代码+RealModelLatencyV2：允许失败阶段；如果没有这行，模型错误不可见。
]; // 新增代码+RealModelLatencyV2：合法阶段列表结束；如果没有这行，数组语法不完整。

export function isModelCallEventType(eventType: string): eventType is ModelCallEventType { // 新增代码+RealModelLatencyV2：函数段开始，判断事件是否属于模型调用状态；如果没有这段，reducer 无法安全忽略这些非消息事件。
  return MODEL_CALL_EVENT_TYPES.includes(eventType as ModelCallEventType); // 新增代码+RealModelLatencyV2：按白名单识别事件类型；如果没有这行，未来新增事件可能被误判。
} // 新增代码+RealModelLatencyV2：函数段结束，isModelCallEventType 到此结束；如果没有这行，函数语法不完整。

function isModelCallPhase(value: unknown): value is ModelCallPhase { // 新增代码+RealModelLatencyV2：函数段开始，判断 payload phase 是否合法；如果没有这段，后端坏数据会变成 UI 机器码。
  return typeof value === "string" && MODEL_CALL_PHASES.includes(value as ModelCallPhase); // 新增代码+RealModelLatencyV2：只接受白名单里的字符串阶段；如果没有这行，任意字符串都可能进入样式类。
} // 新增代码+RealModelLatencyV2：函数段结束，isModelCallPhase 到此结束；如果没有这行，函数语法不完整。

function fallbackPhaseForEventType(eventType: ModelCallEventType): ModelCallPhase { // 新增代码+RealModelLatencyV2：函数段开始，为缺 phase 的事件给出阶段兜底；如果没有这段，后端旧事件会显示空状态。
  if (eventType === "model_call_started") { // 新增代码+RealModelLatencyV2：识别调用开始事件；如果没有这行，started 事件无法兜底。
    return "started"; // 新增代码+RealModelLatencyV2：开始事件兜底为 started；如果没有这行，连接前状态会丢失。
  } // 新增代码+RealModelLatencyV2：开始事件分支结束；如果没有这行，条件块语法不完整。
  if (eventType === "model_first_delta") { // 新增代码+RealModelLatencyV2：识别首增量事件；如果没有这行，TTFT 事件无法兜底。
    return "first_delta"; // 新增代码+RealModelLatencyV2：首增量兜底为 first_delta；如果没有这行，首 token 状态会丢失。
  } // 新增代码+RealModelLatencyV2：首增量分支结束；如果没有这行，条件块语法不完整。
  if (eventType === "model_call_completed") { // 新增代码+RealModelLatencyV2：识别完成事件；如果没有这行，完成事件无法兜底。
    return "completed"; // 新增代码+RealModelLatencyV2：完成事件兜底为 completed；如果没有这行，终态会丢失。
  } // 新增代码+RealModelLatencyV2：完成事件分支结束；如果没有这行，条件块语法不完整。
  if (eventType === "model_call_failed") { // 新增代码+RealModelLatencyV2：识别失败事件；如果没有这行，错误事件无法兜底。
    return "failed"; // 新增代码+RealModelLatencyV2：失败事件兜底为 failed；如果没有这行，错误状态会丢失。
  } // 新增代码+RealModelLatencyV2：失败事件分支结束；如果没有这行，条件块语法不完整。
  return "connecting"; // 新增代码+RealModelLatencyV2：普通阶段更新缺 phase 时兜底为 connecting；如果没有这行，状态条可能显示空白。
} // 新增代码+RealModelLatencyV2：函数段结束，fallbackPhaseForEventType 到此结束；如果没有这行，函数语法不完整。

function stringFromPayload(payload: Record<string, unknown>, keys: string[]): string { // 新增代码+RealModelLatencyV2：函数段开始，从 payload 多个字段取文本；如果没有这段，message/error/model 字段兼容会散落。
  for (const key of keys) { // 新增代码+RealModelLatencyV2：遍历候选字段；如果没有这行，只能支持一个后端字段名。
    const value = payload[key]; // 新增代码+RealModelLatencyV2：读取当前字段；如果没有这行，无法判断字段是否可用。
    if (typeof value === "string" && value.length > 0) { // 新增代码+RealModelLatencyV2：只接受非空字符串；如果没有这行，空消息会覆盖可读 fallback。
      return value; // 新增代码+RealModelLatencyV2：返回第一个可用文本；如果没有这行，函数无法输出命中文本。
    } // 新增代码+RealModelLatencyV2：字段可用判断结束；如果没有这行，条件块语法不完整。
  } // 新增代码+RealModelLatencyV2：候选字段遍历结束；如果没有这行，for 循环语法不完整。
  return ""; // 新增代码+RealModelLatencyV2：无文本时返回空字符串；如果没有这行，调用方要处理 undefined。
} // 新增代码+RealModelLatencyV2：函数段结束，stringFromPayload 到此结束；如果没有这行，函数语法不完整。

function elapsedMsFromPayload(payload: Record<string, unknown>): number { // 新增代码+RealModelLatencyV2：函数段开始，提取阶段耗时；如果没有这段，状态条不能显示 3.2s 这类证据。
  const value = payload.elapsed_ms; // 新增代码+RealModelLatencyV2：读取后端 elapsed_ms 字段；如果没有这行，无法得到耗时输入。
  return typeof value === "number" && Number.isFinite(value) ? value : 0; // 新增代码+RealModelLatencyV2：只接受有限数字并兜底 0；如果没有这行，NaN 会污染 UI。
} // 新增代码+RealModelLatencyV2：函数段结束，elapsedMsFromPayload 到此结束；如果没有这行，函数语法不完整。

function compactElapsed(elapsedMs: number): string { // 新增代码+RealModelLatencyV2：函数段开始，把毫秒压缩成人类可读短时间；如果没有这段，右栏会显示冗长毫秒值。
  if (elapsedMs <= 0) { // 新增代码+RealModelLatencyV2：处理无耗时数据；如果没有这行，0ms 会占用状态条空间。
    return ""; // 新增代码+RealModelLatencyV2：无耗时时返回空；如果没有这行，组件会显示无意义 0.0s。
  } // 新增代码+RealModelLatencyV2：无耗时分支结束；如果没有这行，条件块语法不完整。
  if (elapsedMs < 1000) { // 新增代码+RealModelLatencyV2：处理 1 秒以内耗时；如果没有这行，短耗时会被强行显示小数秒。
    return `${Math.round(elapsedMs)}ms`; // 新增代码+RealModelLatencyV2：毫秒级显示整数；如果没有这行，短耗时不可读。
  } // 新增代码+RealModelLatencyV2：毫秒分支结束；如果没有这行，条件块语法不完整。
  return `${(elapsedMs / 1000).toFixed(1)}s`; // 新增代码+RealModelLatencyV2：秒级显示一位小数；如果没有这行，3.2s 这类文案无法出现。
} // 新增代码+RealModelLatencyV2：函数段结束，compactElapsed 到此结束；如果没有这行，函数语法不完整。

function displayModelName(modelId: string): string { // 新增代码+RealModelLatencyV2：函数段开始，把模型 id 变成短显示名；如果没有这段，连接文案会显示空或大小写混乱。
  return modelId.length > 0 ? modelId.toUpperCase() : "模型"; // 新增代码+RealModelLatencyV2：有模型则大写显示，否则用中文兜底；如果没有这行，未选模型时文案会空缺。
} // 新增代码+RealModelLatencyV2：函数段结束，displayModelName 到此结束；如果没有这行，函数语法不完整。

export function modelCallStatusFromEvent(event: StatusEvent): ModelCallStatusView | null { // 新增代码+RealModelLatencyV2：函数段开始，把状态事件转成模型调用状态；如果没有这段，Composer 和右栏无法共享同一解释规则。
  if (!isModelCallEventType(event.event_type)) { // 新增代码+RealModelLatencyV2：过滤非模型调用事件；如果没有这行，message_delta 等事件会误触发状态条。
    return null; // 新增代码+RealModelLatencyV2：非模型事件返回空；如果没有这行，调用方无法安全忽略。
  } // 新增代码+RealModelLatencyV2：非模型事件判断结束；如果没有这行，条件块语法不完整。
  const phase = isModelCallPhase(event.payload.phase) ? event.payload.phase : fallbackPhaseForEventType(event.event_type); // 新增代码+RealModelLatencyV2：读取合法 phase 或按事件类型兜底；如果没有这行，缺 phase 的事件会丢失。
  return { // 新增代码+RealModelLatencyV2：返回标准状态对象；如果没有这行，函数没有输出。
    eventType: event.event_type, // 新增代码+RealModelLatencyV2：保存事件类型；如果没有这行，UI 无法知道状态来源。
    phase, // 新增代码+RealModelLatencyV2：保存模型阶段；如果没有这行，状态文案无法计算。
    message: stringFromPayload(event.payload, ["message", "error", "error_message", "detail"]), // 新增代码+RealModelLatencyV2：读取可见诊断消息；如果没有这行，失败原因会丢失。
    modelId: stringFromPayload(event.payload, ["model_id", "model", "target_model"]), // 新增代码+RealModelLatencyV2：读取模型 id；如果没有这行，正在连接的模型不可见。
    providerId: stringFromPayload(event.payload, ["provider_id", "provider"]), // 新增代码+RealModelLatencyV2：读取 provider id；如果没有这行，多 provider 诊断缺少来源。
    elapsedMs: elapsedMsFromPayload(event.payload), // 新增代码+RealModelLatencyV2：读取阶段耗时；如果没有这行，延迟证据不可见。
  }; // 新增代码+RealModelLatencyV2：状态对象结束；如果没有这行，对象语法不完整。
} // 新增代码+RealModelLatencyV2：函数段结束，modelCallStatusFromEvent 到此结束；如果没有这行，函数语法不完整。

export function latestModelCallStatus(events: StatusEvent[]): ModelCallStatusView | null { // 新增代码+RealModelLatencyV2：函数段开始，从事件流取最新模型调用状态；如果没有这段，底部可能显示过期阶段。
  for (let index = events.length - 1; index >= 0; index -= 1) { // 新增代码+RealModelLatencyV2：从末尾向前找最新事件；如果没有这行，最新状态会被旧状态覆盖。
    const status = modelCallStatusFromEvent(events[index]); // 新增代码+RealModelLatencyV2：尝试把当前事件转成模型状态；如果没有这行，循环没有判断目标。
    if (status !== null) { // 新增代码+RealModelLatencyV2：判断是否命中模型事件；如果没有这行，找到后不会提前返回。
      return status; // 新增代码+RealModelLatencyV2：返回最新状态；如果没有这行，helper 总是走到空状态。
    } // 新增代码+RealModelLatencyV2：命中分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+RealModelLatencyV2：逆序遍历结束；如果没有这行，for 循环语法不完整。
  return null; // 新增代码+RealModelLatencyV2：没有模型状态时返回空；如果没有这行，调用方无法判断隐藏状态条。
} // 新增代码+RealModelLatencyV2：函数段结束，latestModelCallStatus 到此结束；如果没有这行，函数语法不完整。

export function modelCallStatusLabel(status: ModelCallStatusView): string { // 新增代码+RealModelLatencyV2：函数段开始，把模型阶段转成紧凑中文文案；如果没有这段，UI 会显示英文机器码。
  if (status.phase === "connecting" || status.phase === "started" || status.phase === "queued") { // 新增代码+RealModelLatencyV2：处理连接前后的常见阶段；如果没有这行，最初等待没有可读文案。
    return `正在连接 ${displayModelName(status.modelId)}`; // 新增代码+RealModelLatencyV2：显示正在连接的模型名；如果没有这行，用户不知道当前选中模型是否生效。
  } // 新增代码+RealModelLatencyV2：连接阶段分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "auth_checking") { // 新增代码+RealModelLatencyV2：处理认证检查阶段；如果没有这行，OAuth 检查慢时没有解释。
    return "正在检查 OpenAI 登录状态"; // 新增代码+RealModelLatencyV2：显示认证检查文案；如果没有这行，用户会误以为模型没启动。
  } // 新增代码+RealModelLatencyV2：认证检查分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "websocket_connecting") { // 新增代码+RealModelLatencyV2：处理 WebSocket 连接阶段；如果没有这行，传输轨道不可见。
    return "正在建立 WebSocket 连接"; // 新增代码+RealModelLatencyV2：显示 WebSocket 连接文案；如果没有这行，用户看不到慢在哪个传输层。
  } // 新增代码+RealModelLatencyV2：WebSocket 连接分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "websocket_timeout" || status.phase === "https_fallback") { // 新增代码+RealModelLatencyV2：处理 WebSocket 超时和 HTTPS fallback；如果没有这行，当前慢问题没有对应文案。
    return "WebSocket 超时，正在切换 HTTPS"; // 新增代码+RealModelLatencyV2：显示 fallback 文案；如果没有这行，用户只会看到卡住。
  } // 新增代码+RealModelLatencyV2：fallback 分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "streaming") { // 新增代码+RealModelLatencyV2：处理流式接收阶段；如果没有这行，输出中的状态不可见。
    return "正在接收模型响应"; // 新增代码+RealModelLatencyV2：显示流式接收文案；如果没有这行，用户不知道后端已经开始返回。
  } // 新增代码+RealModelLatencyV2：流式分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "first_delta") { // 新增代码+RealModelLatencyV2：处理首个增量阶段；如果没有这行，TTFT 成功信号不可见。
    return "已收到首个响应"; // 新增代码+RealModelLatencyV2：显示首响应文案；如果没有这行，用户看不到模型已经活过来。
  } // 新增代码+RealModelLatencyV2：首增量分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "completed") { // 新增代码+RealModelLatencyV2：处理完成阶段；如果没有这行，终态无法显示。
    return "模型调用完成"; // 新增代码+RealModelLatencyV2：显示完成文案；如果没有这行，状态条可能停在上一阶段。
  } // 新增代码+RealModelLatencyV2：完成分支结束；如果没有这行，条件块语法不完整。
  if (status.phase === "cancel_requested" || status.phase === "cancelled") { // 新增代码+RealModelLatencyV2：处理取消阶段；如果没有这行，取消后状态仍可能显示运行中。
    return "已取消"; // 新增代码+RealModelLatencyV2：显示取消文案；如果没有这行，用户无法确认中断成功。
  } // 新增代码+RealModelLatencyV2：取消分支结束；如果没有这行，条件块语法不完整。
  return `调用失败：${status.message || "当前模型不可用"}`; // 新增代码+RealModelLatencyV2：失败阶段显示后端原因或兜底；如果没有这行，错误只会藏在日志。
} // 新增代码+RealModelLatencyV2：函数段结束，modelCallStatusLabel 到此结束；如果没有这行，函数语法不完整。

export function ModelCallStatus({ status, compact = false }: { status: ModelCallStatusView | null; compact?: boolean }): JSX.Element | null { // 新增代码+RealModelLatencyV2：函数段开始，渲染模型调用状态条；如果没有这段，用户看不到慢调用卡在哪一层。
  if (status === null) { // 新增代码+RealModelLatencyV2：处理无状态；如果没有这行，空事件流会渲染无意义占位。
    return null; // 新增代码+RealModelLatencyV2：无状态不渲染；如果没有这行，底部会出现空白文案。
  } // 新增代码+RealModelLatencyV2：无状态判断结束；如果没有这行，条件块语法不完整。
  const label = modelCallStatusLabel(status); // 新增代码+RealModelLatencyV2：计算紧凑中文文案；如果没有这行，JSX 会重复文案映射。
  const elapsed = compactElapsed(status.elapsedMs); // 新增代码+RealModelLatencyV2：计算短耗时；如果没有这行，组件无法显示 3.2s 证据。
  return ( // 新增代码+RealModelLatencyV2：返回状态条结构；如果没有这行，组件没有 UI 输出。
    <div className={`model-call-status model-call-status-${status.phase}${compact ? " model-call-status-compact" : ""}`} title={status.message || label} role="status"> {/* 新增代码+RealModelLatencyV2：状态条根节点带阶段类和 title；如果没有这行，CSS 和诊断悬停都无法工作。 */}
      <span className="model-call-status-dot" aria-hidden="true" /> {/* 新增代码+RealModelLatencyV2：显示小状态点；如果没有这行，阶段状态缺少可扫描视觉锚点。 */}
      <span className="model-call-status-text">{label}</span> {/* 新增代码+RealModelLatencyV2：显示中文阶段文案；如果没有这行，用户看不到慢调用原因。 */}
      {elapsed.length > 0 ? <span className="model-call-status-elapsed">{elapsed}</span> : null} {/* 新增代码+RealModelLatencyV2：有耗时时显示短时间；如果没有这行，慢路径没有可见延迟证据。 */}
    </div> // 新增代码+RealModelLatencyV2：状态条根节点结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+RealModelLatencyV2：返回语句结束；如果没有这行，组件返回边界不清楚。
} // 新增代码+RealModelLatencyV2：函数段结束，ModelCallStatus 到此结束；如果没有这行，组件语法不完整。
