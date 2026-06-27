import type { StatusEvent } from "../state/statusStore"; // 新增代码+RealModelObservability：导入 GUI 状态事件类型；如果没有这一行，本组件会和真实事件合同脱节。

export type ModelCallEventType = "model_call_started" | "model_call_status" | "model_first_delta" | "model_call_completed" | "model_call_failed"; // 新增代码+RealModelObservability：定义模型调用事件类型；如果没有这一行，前端无法稳定识别后端新增阶段事件。

export type ModelCallPhase = "started" | "connecting" | "auth_checking" | "websocket_timeout" | "https_fallback" | "streaming" | "first_delta" | "completed" | "cancel_requested" | "cancelled" | "failed"; // 新增代码+RealModelObservability：定义可展示阶段白名单；如果没有这一行，坏 payload 会把机器码直接显示到 GUI。

export type ModelCallStatusView = { // 新增代码+RealModelObservability：类型段开始，定义 UI 可消费的模型调用状态；如果没有这段，Composer 和右侧状态栏会各自解析 payload。
  eventType: ModelCallEventType; // 新增代码+RealModelObservability：保存来源事件类型；如果没有这一行，排查时无法知道状态来自哪个后端事件。
  phase: ModelCallPhase; // 新增代码+RealModelObservability：保存归一化阶段；如果没有这一行，文案 helper 无法判断显示内容。
  message: string; // 新增代码+RealModelObservability：保存后端低敏消息；如果没有这一行，失败或 fallback 细节会丢失。
  modelId: string; // 新增代码+RealModelObservability：保存模型 id；如果没有这一行，用户不知道慢调用对应哪个模型。
  providerId: string; // 新增代码+RealModelObservability：保存 provider id；如果没有这一行，多 provider 诊断无法定位来源。
  elapsedMs: number; // 新增代码+RealModelObservability：保存阶段耗时；如果没有这一行，用户只能看到“慢”但没有数字证据。
}; // 新增代码+RealModelObservability：类型段结束，ModelCallStatusView 到此结束；如果没有这一行，TypeScript 对象类型语法不完整。

const MODEL_CALL_EVENT_TYPES: ModelCallEventType[] = [ // 新增代码+RealModelObservability：数组段开始，集中列出模型调用事件；如果没有这段，helper 和 reducer 会各写一套白名单。
  "model_call_started", // 新增代码+RealModelObservability：列入调用开始事件；如果没有这一行，请求离开前端的瞬间不可见。
  "model_call_status", // 新增代码+RealModelObservability：列入中间状态事件；如果没有这一行，连接和 fallback 阶段不会显示。
  "model_first_delta", // 新增代码+RealModelObservability：列入首响应事件；如果没有这一行，首包延迟结束点不可见。
  "model_call_completed", // 新增代码+RealModelObservability：列入完成事件；如果没有这一行，状态条无法收尾。
  "model_call_failed", // 新增代码+RealModelObservability：列入失败事件；如果没有这一行，模型错误无法进入状态条。
]; // 新增代码+RealModelObservability：数组段结束，MODEL_CALL_EVENT_TYPES 到此结束；如果没有这一行，数组语法不完整。

const MODEL_CALL_PHASES: ModelCallPhase[] = [ // 新增代码+RealModelObservability：数组段开始，集中列出合法阶段；如果没有这段，payload 里的未知 phase 会污染 UI。
  "started", // 新增代码+RealModelObservability：允许开始阶段；如果没有这一行，开始事件会被错误降级。
  "connecting", // 新增代码+RealModelObservability：允许连接阶段；如果没有这一行，连接状态不能显示。
  "auth_checking", // 新增代码+RealModelObservability：允许认证检查阶段；如果没有这一行，OAuth 检查无法表达。
  "websocket_timeout", // 新增代码+RealModelObservability：允许 WebSocket 超时阶段；如果没有这一行，旧慢路径原因会变成未知。
  "https_fallback", // 新增代码+RealModelObservability：允许 HTTPS fallback 阶段；如果没有这一行，降级路径无法表达。
  "streaming", // 新增代码+RealModelObservability：允许流式传输阶段；如果没有这一行，已进入流式但未完成的状态不可见。
  "first_delta", // 新增代码+RealModelObservability：允许首响应阶段；如果没有这一行，TTFT 成功信号不可见。
  "completed", // 新增代码+RealModelObservability：允许完成阶段；如果没有这一行，状态条无法显示收尾。
  "cancel_requested", // 新增代码+RealModelObservability：允许取消请求阶段；如果没有这一行，用户点击停止后的后端反馈不可见。
  "cancelled", // 新增代码+RealModelObservability：允许取消终态；如果没有这一行，状态条无法结束为已取消。
  "failed", // 新增代码+RealModelObservability：允许失败终态；如果没有这一行，模型错误无法展示。
]; // 新增代码+RealModelObservability：数组段结束，MODEL_CALL_PHASES 到此结束；如果没有这一行，数组语法不完整。

export function isModelCallEventType(eventType: string): eventType is ModelCallEventType { // 新增代码+RealModelObservability：函数段开始，判断事件是否属于模型调用状态；如果没有这段，reducer 无法安静忽略这些诊断事件。
  return MODEL_CALL_EVENT_TYPES.includes(eventType as ModelCallEventType); // 新增代码+RealModelObservability：返回白名单判断结果；如果没有这一行，函数没有输出。
} // 新增代码+RealModelObservability：函数段结束，isModelCallEventType 到此结束；如果没有这一行，函数语法不完整。

function isModelCallPhase(value: unknown): value is ModelCallPhase { // 新增代码+RealModelObservability：函数段开始，判断 payload phase 是否合法；如果没有这段，未知 phase 会直接显示。
  return typeof value === "string" && MODEL_CALL_PHASES.includes(value as ModelCallPhase); // 新增代码+RealModelObservability：只接受白名单字符串；如果没有这一行，函数无法过滤坏数据。
} // 新增代码+RealModelObservability：函数段结束，isModelCallPhase 到此结束；如果没有这一行，函数语法不完整。

function fallbackPhaseForEventType(eventType: ModelCallEventType): ModelCallPhase { // 新增代码+RealModelObservability：函数段开始，为缺 phase 的事件兜底；如果没有这段，旧后端事件会显示空状态。
  if (eventType === "model_call_started") { // 新增代码+RealModelObservability：识别调用开始事件；如果没有这一行，开始事件无法兜底。
    return "connecting"; // 新增代码+RealModelObservability：开始事件默认显示连接中；如果没有这一行，函数没有开始事件输出。
  } // 新增代码+RealModelObservability：开始事件分支结束；如果没有这一行，条件块语法不完整。
  if (eventType === "model_first_delta") { // 新增代码+RealModelObservability：识别首响应事件；如果没有这一行，首响应事件无法兜底。
    return "first_delta"; // 新增代码+RealModelObservability：首响应事件默认显示 first_delta；如果没有这一行，函数没有首响应输出。
  } // 新增代码+RealModelObservability：首响应分支结束；如果没有这一行，条件块语法不完整。
  if (eventType === "model_call_completed") { // 新增代码+RealModelObservability：识别完成事件；如果没有这一行，完成事件无法兜底。
    return "completed"; // 新增代码+RealModelObservability：完成事件默认显示 completed；如果没有这一行，函数没有完成输出。
  } // 新增代码+RealModelObservability：完成分支结束；如果没有这一行，条件块语法不完整。
  if (eventType === "model_call_failed") { // 新增代码+RealModelObservability：识别失败事件；如果没有这一行，失败事件无法兜底。
    return "failed"; // 新增代码+RealModelObservability：失败事件默认显示 failed；如果没有这一行，函数没有失败输出。
  } // 新增代码+RealModelObservability：失败分支结束；如果没有这一行，条件块语法不完整。
  return "streaming"; // 新增代码+RealModelObservability：普通状态默认显示 streaming；如果没有这一行，函数没有默认输出。
} // 新增代码+RealModelObservability：函数段结束，fallbackPhaseForEventType 到此结束；如果没有这一行，函数语法不完整。

function stringFromPayload(payload: Record<string, unknown>, keys: string[]): string { // 新增代码+RealModelObservability：函数段开始，从多个候选字段提取文本；如果没有这段，字段兼容逻辑会散落。
  for (const key of keys) { // 新增代码+RealModelObservability：遍历候选字段；如果没有这一行，只能支持一个固定字段名。
    const value = payload[key]; // 新增代码+RealModelObservability：读取当前字段值；如果没有这一行，无法判断字段是否可用。
    if (typeof value === "string" && value.length > 0) { // 新增代码+RealModelObservability：只接受非空字符串；如果没有这一行，空字段可能覆盖有效信息。
      return value; // 新增代码+RealModelObservability：返回第一个可用字符串；如果没有这一行，函数没有匹配输出。
    } // 新增代码+RealModelObservability：可用字符串判断结束；如果没有这一行，条件块语法不完整。
  } // 新增代码+RealModelObservability：字段遍历结束；如果没有这一行，for 循环语法不完整。
  return ""; // 新增代码+RealModelObservability：没有文本时返回空字符串；如果没有这一行，调用方要处理 undefined。
} // 新增代码+RealModelObservability：函数段结束，stringFromPayload 到此结束；如果没有这一行，函数语法不完整。

function elapsedMsFromPayload(payload: Record<string, unknown>): number { // 新增代码+RealModelObservability：函数段开始，提取毫秒耗时；如果没有这段，状态条不能显示 3.2s 证据。
  const value = payload.elapsed_ms ?? payload.elapsedMs ?? payload.first_delta_latency_ms ?? payload.total_turn_latency_ms; // 新增代码+RealModelObservability：兼容多种后端耗时字段；如果没有这一行，Direct SSE 现有指标无法复用。
  return typeof value === "number" && Number.isFinite(value) ? Math.max(0, Math.round(value)) : 0; // 新增代码+RealModelObservability：返回非负整数毫秒；如果没有这一行，坏数字会进入 UI。
} // 新增代码+RealModelObservability：函数段结束，elapsedMsFromPayload 到此结束；如果没有这一行，函数语法不完整。

function compactElapsed(elapsedMs: number): string { // 新增代码+RealModelObservability：函数段开始，把毫秒转成短文案；如果没有这段，UI 会显示冗长毫秒值。
  if (elapsedMs <= 0) { // 新增代码+RealModelObservability：处理无耗时输入；如果没有这一行，0ms 会显示成噪音。
    return ""; // 新增代码+RealModelObservability：无耗时时不显示；如果没有这一行，状态条会出现多余数字。
  } // 新增代码+RealModelObservability：无耗时判断结束；如果没有这一行，条件块语法不完整。
  if (elapsedMs < 1000) { // 新增代码+RealModelObservability：处理一秒以内耗时；如果没有这一行，短耗时会被过度小数化。
    return `${elapsedMs}ms`; // 新增代码+RealModelObservability：返回毫秒文案；如果没有这一行，用户看不到短耗时。
  } // 新增代码+RealModelObservability：毫秒分支结束；如果没有这一行，条件块语法不完整。
  return `${(elapsedMs / 1000).toFixed(1)}s`; // 新增代码+RealModelObservability：返回一位小数秒；如果没有这一行，长耗时显示不够紧凑。
} // 新增代码+RealModelObservability：函数段结束，compactElapsed 到此结束；如果没有这一行，函数语法不完整。

function displayModelName(modelId: string): string { // 新增代码+RealModelObservability：函数段开始，把模型 id 转成短显示名；如果没有这段，连接文案会大小写不统一。
  return modelId.length > 0 ? modelId.toUpperCase() : "模型"; // 新增代码+RealModelObservability：有模型名时大写显示，否则兜底“模型”；如果没有这一行，空模型会显示空白。
} // 新增代码+RealModelObservability：函数段结束，displayModelName 到此结束；如果没有这一行，函数语法不完整。

export function modelCallStatusFromEvent(event: StatusEvent): ModelCallStatusView | null { // 新增代码+RealModelObservability：函数段开始，把状态事件转成模型状态 view；如果没有这段，Composer 和右栏无法共享解释规则。
  if (!isModelCallEventType(event.event_type)) { // 新增代码+RealModelObservability：过滤非模型事件；如果没有这一行，普通 message_delta 会误触发状态条。
    return null; // 新增代码+RealModelObservability：非模型事件返回空；如果没有这一行，函数会继续解析错误事件。
  } // 新增代码+RealModelObservability：非模型事件判断结束；如果没有这一行，条件块语法不完整。
  const phase = isModelCallPhase(event.payload.phase) ? event.payload.phase : fallbackPhaseForEventType(event.event_type); // 新增代码+RealModelObservability：读取或兜底阶段；如果没有这一行，缺 phase 的事件无法显示。
  return { // 新增代码+RealModelObservability：开始构造状态 view；如果没有这一行，函数没有返回对象。
    eventType: event.event_type, // 新增代码+RealModelObservability：保存事件类型；如果没有这一行，来源信息会丢失。
    phase, // 新增代码+RealModelObservability：保存归一化阶段；如果没有这一行，文案 helper 无法工作。
    message: stringFromPayload(event.payload, ["message", "error", "status"]), // 新增代码+RealModelObservability：读取低敏消息；如果没有这一行，失败提示会变空。
    modelId: stringFromPayload(event.payload, ["model_id", "modelId"]), // 新增代码+RealModelObservability：读取模型 id；如果没有这一行，状态条不知道目标模型。
    providerId: stringFromPayload(event.payload, ["provider_id", "providerId"]), // 新增代码+RealModelObservability：读取 provider id；如果没有这一行，状态条无法定位来源 provider。
    elapsedMs: elapsedMsFromPayload(event.payload), // 新增代码+RealModelObservability：读取耗时；如果没有这一行，状态条没有延迟证据。
  }; // 新增代码+RealModelObservability：状态 view 构造结束；如果没有这一行，对象语法不完整。
} // 新增代码+RealModelObservability：函数段结束，modelCallStatusFromEvent 到此结束；如果没有这一行，函数语法不完整。

export function latestModelCallStatus(events: StatusEvent[]): ModelCallStatusView | null { // 新增代码+RealModelObservability：函数段开始，从事件流提取最新模型状态；如果没有这段，底部可能显示旧状态。
  for (let index = events.length - 1; index >= 0; index -= 1) { // 新增代码+RealModelObservability：从后往前扫描；如果没有这一行，最新状态提取会变慢或错误。
    const status = modelCallStatusFromEvent(events[index]); // 新增代码+RealModelObservability：尝试解析当前事件；如果没有这一行，循环没有判断对象。
    if (status !== null) { // 新增代码+RealModelObservability：找到模型状态时停止；如果没有这一行，函数会继续扫描旧事件。
      return status; // 新增代码+RealModelObservability：返回最新状态；如果没有这一行，调用方拿不到结果。
    } // 新增代码+RealModelObservability：找到状态分支结束；如果没有这一行，条件块语法不完整。
  } // 新增代码+RealModelObservability：倒序扫描结束；如果没有这一行，for 循环语法不完整。
  return null; // 新增代码+RealModelObservability：没有模型状态时返回空；如果没有这一行，函数没有默认输出。
} // 新增代码+RealModelObservability：函数段结束，latestModelCallStatus 到此结束；如果没有这一行，函数语法不完整。

export function modelCallStatusLabel(status: ModelCallStatusView): string { // 新增代码+RealModelObservability：函数段开始，把阶段转成人类短文案；如果没有这段，UI 会显示英文机器码。
  const modelName = displayModelName(status.modelId); // 新增代码+RealModelObservability：生成可读模型名；如果没有这一行，连接文案不能包含目标模型。
  if (status.phase === "connecting" || status.phase === "started") { // 新增代码+RealModelObservability：识别连接/开始阶段；如果没有这一行，开始状态没有专门文案。
    return `正在连接 ${modelName}`; // 新增代码+RealModelObservability：返回连接文案；如果没有这一行，用户不知道请求正在连哪个模型。
  } // 新增代码+RealModelObservability：连接分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "auth_checking") { // 新增代码+RealModelObservability：识别认证检查阶段；如果没有这一行，OAuth 检查不清楚。
    return "正在检查 OAuth 连接"; // 新增代码+RealModelObservability：返回认证检查文案；如果没有这一行，用户不知道卡在认证。
  } // 新增代码+RealModelObservability：认证检查分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "websocket_timeout" || status.phase === "https_fallback") { // 新增代码+RealModelObservability：识别 WebSocket 超时和 HTTPS fallback；如果没有这一行，慢路径不会有清楚提示。
    return "WebSocket 超时，正在切换 HTTPS"; // 新增代码+RealModelObservability：返回降级文案；如果没有这一行，用户会以为 GUI 卡死。
  } // 新增代码+RealModelObservability：fallback 分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "streaming") { // 新增代码+RealModelObservability：识别流式传输阶段；如果没有这一行，传输中状态没有文案。
    return "正在接收模型响应"; // 新增代码+RealModelObservability：返回流式传输文案；如果没有这一行，用户不知道后端仍在接收。
  } // 新增代码+RealModelObservability：流式分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "first_delta") { // 新增代码+RealModelObservability：识别首响应阶段；如果没有这一行，首包成功没有正反馈。
    return "已收到首个响应"; // 新增代码+RealModelObservability：返回首响应文案；如果没有这一行，测试和 UI 都看不到 TTFT 结束。
  } // 新增代码+RealModelObservability：首响应分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "completed") { // 新增代码+RealModelObservability：识别完成阶段；如果没有这一行，完成状态没有专门文案。
    return "模型调用完成"; // 新增代码+RealModelObservability：返回完成文案；如果没有这一行，状态条无法收尾。
  } // 新增代码+RealModelObservability：完成分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "cancel_requested") { // 新增代码+RealModelObservability：识别取消请求阶段；如果没有这一行，取消中没有中间反馈。
    return "正在取消模型调用"; // 新增代码+RealModelObservability：返回取消中文案；如果没有这一行，用户不知道停止请求是否送达。
  } // 新增代码+RealModelObservability：取消请求分支结束；如果没有这一行，条件块语法不完整。
  if (status.phase === "cancelled") { // 新增代码+RealModelObservability：识别已取消阶段；如果没有这一行，取消终态没有文案。
    return "已取消"; // 新增代码+RealModelObservability：返回已取消文案；如果没有这一行，状态条无法终止为取消。
  } // 新增代码+RealModelObservability：已取消分支结束；如果没有这一行，条件块语法不完整。
  return status.message.length > 0 ? `调用失败：${status.message}` : "模型调用失败"; // 新增代码+RealModelObservability：返回失败文案并优先带原因；如果没有这一行，失败状态没有默认输出。
} // 新增代码+RealModelObservability：函数段结束，modelCallStatusLabel 到此结束；如果没有这一行，函数语法不完整。

export function ModelCallStatus({ status, compact = false }: { status: ModelCallStatusView | null; compact?: boolean }): JSX.Element | null { // 新增代码+RealModelObservability：组件段开始，渲染模型调用状态条；如果没有这段，用户看不到真实调用卡在哪一层。
  if (status === null) { // 新增代码+RealModelObservability：没有状态时不渲染；如果没有这一行，Composer 会出现空状态条。
    return null; // 新增代码+RealModelObservability：返回空渲染；如果没有这一行，组件会继续访问 null。
  } // 新增代码+RealModelObservability：空状态判断结束；如果没有这一行，条件块语法不完整。
  const label = modelCallStatusLabel(status); // 新增代码+RealModelObservability：生成短文案；如果没有这一行，JSX 会重复计算。
  const elapsed = compactElapsed(status.elapsedMs); // 新增代码+RealModelObservability：生成短耗时；如果没有这一行，耗时展示会散落。
  return ( // 新增代码+RealModelObservability：返回状态条 JSX；如果没有这一行，组件没有输出。
    <span className={`model-call-status model-call-status-${status.phase}${compact ? " model-call-status-compact" : ""}`} title={status.message || label}> {/* 新增代码+RealModelObservability：状态条容器；如果没有这一层，文案、耗时和颜色没有统一样式。 */}
      <span className="model-call-status-dot" aria-hidden="true" /> {/* 新增代码+RealModelObservability：阶段颜色点；如果没有这一行，用户扫视时难区分成功、失败、fallback。 */}
      <span className="model-call-status-text">{label}</span> {/* 新增代码+RealModelObservability：主状态文案；如果没有这一行，用户看不到当前模型阶段。 */}
      {elapsed.length > 0 ? <span className="model-call-status-elapsed">{elapsed}</span> : null} {/* 新增代码+RealModelObservability：可选耗时标签；如果没有这一行，延迟证据不会显示。 */}
    </span> // 新增代码+RealModelObservability：状态条容器结束；如果没有这一行，JSX 结构不完整。
  ); // 新增代码+RealModelObservability：返回语句结束；如果没有这一行，组件没有返回边界。
} // 新增代码+RealModelObservability：组件段结束，ModelCallStatus 到此结束；如果没有这一行，组件语法不完整。
