import { useEffect, useMemo, useReducer, useState } from "react"; // 修改代码+DesktopGUISessions：引入 React 状态、副作用和本地 state 工具；如果没有这行，主壳无法保存项目名、会话列表和轮询状态。
import { createGuiClient } from "../api/guiClient"; // 修改代码+DesktopToolTimeline：引入 GUI bridge 客户端工厂；如果没有这行，前端无法向本地 bridge 发送消息或读取事件。
import { reduceGuiEventToThreadActions } from "../state/eventReducer"; // 新增代码+DesktopThreadStreaming：引入 V2 事件到线程动作的纯转换器；如果没有这行，AppShell 会继续手写旧事件同步逻辑。
import { appendStatusEvents, initialStatusState, latestPermissionEvent, normalizeStatusEvent, type StatusEvent } from "../state/statusStore"; // 修改代码+DesktopThreadStreaming：引入状态时间线、权限事件和事件规范化工具；如果没有这行，轮询数据无法进入 UI。
import { initialThreadState, threadReducer, type ThreadMessage, type ThreadRole, type TurnStatus } from "../state/threadStore"; // 修改代码+DesktopGUISessions：引入对话 reducer 和消息类型；如果没有这行，恢复消息无法被安全转换。
import { Composer } from "./Composer"; // 修改代码+DesktopToolTimeline：引入底部输入组件；如果没有这行，用户没有输入 prompt 的入口。
import { PermissionBanner } from "./PermissionBanner"; // 新增代码+DesktopGUIPermissions：引入权限提示条；如果没有这行，用户可能错过待处理权限请求。
import { PermissionDialog } from "./PermissionDialog"; // 新增代码+DesktopGUIPermissions：引入权限确认弹窗；如果没有这行，用户无法在 GUI 中允许或拒绝权限。
import { SearchPanel, type SearchPanelResult } from "./SearchPanel"; // 新增代码+DesktopGUISessionSearch：引入会话搜索面板和结果类型；如果没有这行，搜索入口无法渲染真实 GUI。
import { Sidebar, type SidebarSession } from "./Sidebar"; // 修改代码+DesktopGUISessions：引入左侧导航组件和会话类型；如果没有这行，项目名和 session 列表无法传入侧栏。
import { StatusInspector } from "./StatusInspector"; // 新增代码+DesktopToolTimeline：引入右侧状态面板；如果没有这行，用户看不到 bridge 事件时间线。
import { ThreadView } from "./ThreadView"; // 修改代码+DesktopToolTimeline：引入主对话组件；如果没有这行，消息和工具卡片没有渲染位置。

type DesktopBridgeConfig = { // 修改代码+DesktopToolTimeline：定义 preload 注入的 bridge 配置；如果没有这段，window.openHarnessDesktop 的结构会不清楚。
  baseUrl?: string; // 修改代码+DesktopToolTimeline：保存 bridge 地址；如果没有这行，前端不知道请求哪个本地端口。
  token?: string; // 修改代码+DesktopToolTimeline：保存 bridge token；如果没有这行，安全端点会拒绝 GUI 请求。
}; // 修改代码+DesktopToolTimeline：bridge 配置类型结束；如果没有这行，TypeScript 类型语法不完整。

declare global { // 修改代码+DesktopToolTimeline：声明桌面 preload 全局对象；如果没有这段，TypeScript 不认识 window.openHarnessDesktop。
  interface Window { // 修改代码+DesktopToolTimeline：扩展浏览器 Window 类型；如果没有这行，访问 preload 字段会报类型错误。
    openHarnessDesktop?: { // 修改代码+DesktopToolTimeline：声明 OpenHarness 桌面对象；如果没有这行，前端无法安全读取桌面注入信息。
      version: string; // 修改代码+DesktopToolTimeline：保存桌面壳版本；如果没有这行，诊断信息缺少版本来源。
      bridge?: DesktopBridgeConfig; // 修改代码+DesktopToolTimeline：保存可选 bridge 配置；如果没有这行，前端无法读取 token/baseUrl。
    }; // 修改代码+DesktopToolTimeline：openHarnessDesktop 对象结束；如果没有这行，TypeScript 接口语法不完整。
  } // 修改代码+DesktopToolTimeline：Window 接口结束；如果没有这行，global 声明语法不完整。
} // 修改代码+DesktopToolTimeline：全局声明结束；如果没有这行，TypeScript 声明块不完整。

function projectNameFromWorkspace(workspace: string): string { // 新增代码+DesktopGUISessions：函数段开始，从 workspace 路径提取项目名；如果没有这段，侧栏只能显示完整磁盘路径或硬编码项目名。
  const normalized = workspace.replace(/\\/g, "/"); // 新增代码+DesktopGUISessions：把 Windows 反斜杠转成统一分隔符；如果没有这行，按斜杠切分在 Windows 路径上会失败。
  const parts = normalized.split("/").filter(Boolean); // 新增代码+DesktopGUISessions：切分并移除空片段；如果没有这行，盘符或尾部斜杠会导致空项目名。
  return parts.at(-1) ?? "OpenHarness"; // 新增代码+DesktopGUISessions：返回最后一段作为项目名；如果没有这行，侧栏没有稳定 fallback。
} // 新增代码+DesktopGUISessions：函数段结束，projectNameFromWorkspace 到此结束；如果没有这个边界，初学者不容易看出项目名提取范围。

function normalizeSidebarSessions(rawSessions: Array<Record<string, unknown> | string>): SidebarSession[] { // 新增代码+DesktopGUISessions：函数段开始，把后端 sessions 转成侧栏条目；如果没有这段，Sidebar 需要直接理解后端混合数据形状。
  return rawSessions.map((session) => { // 新增代码+DesktopGUISessions：遍历后端会话列表；如果没有这行，真实 sessions 无法进入 UI。
    if (typeof session === "string") { // 新增代码+DesktopGUISessions：处理当前状态快照返回的 session id 字符串；如果没有这行，字符串 session 会显示成空对象。
      return { id: session, title: session }; // 新增代码+DesktopGUISessions：把字符串转成可点击条目；如果没有这行，侧栏无法选择该 session。
    } // 新增代码+DesktopGUISessions：字符串分支结束；如果没有这行，条件块语法不完整。
    const id = String(session.session_id ?? session.id ?? ""); // 新增代码+DesktopGUISessions：兼容 session_id/id 字段；如果没有这行，不同后端来源的会话无法统一定位。
    const title = String(session.title ?? session.user_input ?? id); // 新增代码+DesktopGUISessions：优先使用标题或用户输入；如果没有这行，列表项可能没有可读名称。
    const subtitle = typeof session.subtitle === "string" && session.subtitle.length > 0 ? session.subtitle : typeof session.status === "string" ? session.status : undefined; // 修改代码+DesktopGUISessionSearch：优先读取后端摘要再兜底状态；如果没有这行，搜索/侧栏会丢失最近消息片段。
    const pinned = Boolean(session.pinned); // 新增代码+DesktopGUISessionSearch：读取固定状态；如果没有这行，Sidebar 无法显示 pinned 标记。
    const archived = Boolean(session.archived); // 新增代码+DesktopGUISessionSearch：读取归档状态；如果没有这行，搜索和归档视图无法复用条目。
    return { id, title: title || id || "未命名会话", subtitle, pinned, archived }; // 修改代码+DesktopGUISessionSearch：返回规范化条目；如果没有这行，map 回调没有稳定输出。
  }).filter((session) => session.id.length > 0); // 新增代码+DesktopGUISessions：过滤没有 id 的坏数据；如果没有这行，点击无效会话会调用空 session。
} // 新增代码+DesktopGUISessions：函数段结束，normalizeSidebarSessions 到此结束；如果没有这个边界，初学者不容易看出会话适配范围。

function normalizeSearchResults(rawResults: Array<Record<string, unknown>>): SearchPanelResult[] { // 新增代码+DesktopGUISessionSearch：函数段开始，把后端搜索结果转成面板条目；如果没有这段，SearchPanel 需要直接理解原始 JSON。
  return rawResults.map((result) => { // 新增代码+DesktopGUISessionSearch：遍历后端搜索结果；如果没有这行，搜索结果不会进入 UI。
    const sessionId = String(result.session_id ?? result.id ?? ""); // 新增代码+DesktopGUISessionSearch：读取 session id；如果没有这行，点击结果无法恢复会话。
    const title = String(result.title ?? sessionId); // 新增代码+DesktopGUISessionSearch：读取结果标题；如果没有这行，结果列表没有主文本。
    const snippet = String(result.snippet ?? ""); // 新增代码+DesktopGUISessionSearch：读取命中片段；如果没有这行，结果缺少上下文。
    const archived = Boolean(result.archived); // 新增代码+DesktopGUISessionSearch：读取归档状态；如果没有这行，面板无法提示归档来源。
    return { sessionId, title, snippet, archived }; // 新增代码+DesktopGUISessionSearch：返回规范化搜索条目；如果没有这行，map 回调没有稳定输出。
  }).filter((result) => result.sessionId.length > 0); // 新增代码+DesktopGUISessionSearch：过滤没有 session id 的坏结果；如果没有这行，点击空结果会调用无效恢复。
} // 新增代码+DesktopGUISessionSearch：函数段结束，normalizeSearchResults 到此结束；如果没有边界说明，初学者不易看出搜索适配范围。

function normalizeThreadRole(role: unknown): ThreadRole { // 新增代码+DesktopGUISessions：函数段开始，把恢复消息角色收敛到 UI 支持值；如果没有这段，坏 role 会破坏 ThreadView 样式映射。
  return role === "user" || role === "assistant" || role === "system" ? role : "system"; // 新增代码+DesktopGUISessions：只允许三种角色并兜底 system；如果没有这行，未知角色会导致 roleLabels 读取失败。
} // 新增代码+DesktopGUISessions：函数段结束，normalizeThreadRole 到此结束；如果没有这个边界，初学者不容易看出角色清洗范围。

function normalizeTurnStatus(status: unknown): TurnStatus | undefined { // 新增代码+DesktopGUISessions：函数段开始，把恢复消息状态收敛到 UI 支持值；如果没有这段，坏 status 会污染状态标签。
  const allowedStatuses: TurnStatus[] = ["idle", "queued", "running", "needs_permission", "cancelling", "completed", "failed", "cancelled"]; // 新增代码+DesktopGUISessions：列出允许状态；如果没有这行，类型守卫没有事实来源。
  return allowedStatuses.includes(status as TurnStatus) ? (status as TurnStatus) : undefined; // 新增代码+DesktopGUISessions：返回合法状态或 undefined；如果没有这行，恢复消息状态可能变成任意字符串。
} // 新增代码+DesktopGUISessions：函数段结束，normalizeTurnStatus 到此结束；如果没有这个边界，初学者不容易看出状态清洗范围。

function normalizeThreadMessages(rawMessages: Array<Record<string, unknown>>): ThreadMessage[] { // 新增代码+DesktopGUISessions：函数段开始，把 resume 返回消息转成 ThreadMessage；如果没有这段，恢复会话无法重建主线程。
  return rawMessages.map((message, index) => ({ // 新增代码+DesktopGUISessions：遍历后端消息并转换；如果没有这行，消息列表不会进入 UI。
    id: String(message.id ?? `resumed_${index}`), // 新增代码+DesktopGUISessions：保证每条消息都有 id；如果没有这行，React 列表 key 不稳定。
    role: normalizeThreadRole(message.role), // 新增代码+DesktopGUISessions：规范化消息角色；如果没有这行，未知角色会破坏渲染。
    text: String(message.text ?? message.content ?? ""), // 新增代码+DesktopGUISessions：读取正文并兜底空字符串；如果没有这行，恢复消息没有可显示文本。
    turnId: typeof message.turn_id === "string" && message.turn_id.length > 0 ? message.turn_id : undefined, // 新增代码+DesktopGUISessions：恢复可选 turn id；如果没有这行，消息和后续事件无法对齐。
    status: normalizeTurnStatus(message.status), // 新增代码+DesktopGUISessions：恢复可选状态；如果没有这行，已完成或失败消息不会带状态标签。
  })); // 新增代码+DesktopGUISessions：消息转换结束；如果没有这行，map 表达式不完整。
} // 新增代码+DesktopGUISessions：函数段结束，normalizeThreadMessages 到此结束；如果没有这个边界，初学者不容易看出恢复消息转换范围。

function bridgeConfigFromLocationHash(): DesktopBridgeConfig | undefined { // 新增代码+DesktopBridgeConfig：函数段开始，从 URL hash 读取 bridge 配置兜底；如果没有这段，preload 注入失败时 GUI 无法连接后端。
  const hashText = window.location.hash.replace(/^#/, ""); // 新增代码+DesktopBridgeConfig：去掉 hash 开头的井号；如果没有这行，URLSearchParams 会把第一个 key 读错。
  const params = new URLSearchParams(hashText); // 新增代码+DesktopBridgeConfig：解析 hash 参数；如果没有这行，baseUrl/token 只能用脆弱字符串切割。
  const baseUrl = params.get("openharnessBridgeUrl") ?? ""; // 新增代码+DesktopBridgeConfig：读取 hash 中的 bridge 地址；如果没有这行，GUI 不知道后端 API 地址。
  const token = params.get("openharnessBridgeToken") ?? ""; // 新增代码+DesktopBridgeConfig：读取 hash 中的 bridge token；如果没有这行，安全端点会拒绝 GUI 请求。
  return baseUrl && token ? { baseUrl, token } : undefined; // 新增代码+DesktopBridgeConfig：配置完整时返回，否则返回空；如果没有这行，半配置会造成循环失败。
} // 新增代码+DesktopBridgeConfig：函数段结束，bridgeConfigFromLocationHash 到此结束；如果没有这个边界，用户不容易看出 hash 兜底范围。

type PermissionViewModel = { // 新增代码+DesktopGUIPermissions：定义权限弹窗可显示数据；如果没有这段，AppShell 会直接把后端 payload 形状泄漏给 UI。
  requestId: string; // 新增代码+DesktopGUIPermissions：保存后端权限 request_id；如果没有这行，approve/deny 无法定位请求。
  turnId: string; // 新增代码+DesktopGUIPermissions：保存关联 turn id；如果没有这行，后端无法校验权限回答归属。
  toolName: string; // 新增代码+DesktopGUIPermissionsV2：保存具体工具名；如果没有这行，弹窗无法说明是哪条工具轨道在请求权限。
  appName: string; // 新增代码+DesktopGUIPermissions：保存应用或工具名；如果没有这行，用户不知道谁在请求权限。
  actionSummary: string; // 新增代码+DesktopGUIPermissionsV2：保存后端整理的动作摘要；如果没有这行，前端需要自己猜权限请求含义。
  reason: string; // 新增代码+DesktopGUIPermissions：保存请求原因；如果没有这行，用户无法判断是否允许。
  riskSummary: string; // 新增代码+DesktopGUIPermissions：保存风险摘要；如果没有这行，权限弹窗缺少安全上下文。
  answered: boolean; // 新增代码+DesktopGUIPermissions：标记该权限是否已经回答；如果没有这行，permission_answered 事件可能继续打开弹窗。
}; // 新增代码+DesktopGUIPermissions：权限 view model 类型结束；如果没有这行，TypeScript 类型语法不完整。

function safePermissionText(value: unknown, fallback: string): string { // 新增代码+DesktopGUIPermissions：函数段开始，生成权限弹窗安全文本；如果没有这段，未知 payload 可能以非字符串或超长文本进入 UI。
  const text = typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIPermissions：只接受非空字符串并提供兜底；如果没有这行，undefined/null 会显示成奇怪文本。
  return text.length > 180 ? `${text.slice(0, 177)}...` : text; // 新增代码+DesktopGUIPermissions：截断长文本；如果没有这行，后端 reason 过长会撑破弹窗。
} // 新增代码+DesktopGUIPermissions：函数段结束，safePermissionText 到此结束；如果没有这个边界，初学者不易看出文本防护范围。

function permissionFromEvent(event: StatusEvent | null): PermissionViewModel | null { // 新增代码+DesktopGUIPermissions：函数段开始，把状态事件转成权限弹窗数据；如果没有这段，UI 要到处猜 payload 字段。
  if (event === null) { // 新增代码+DesktopGUIPermissions：处理没有权限事件的情况；如果没有这行，空事件会导致字段读取错误。
    return null; // 新增代码+DesktopGUIPermissions：没有事件时不显示权限 UI；如果没有这行，调用方无法区分无权限请求。
  } // 新增代码+DesktopGUIPermissions：空事件判断结束；如果没有这行，条件块语法不完整。
  const requestId = safePermissionText(event.payload.request_id, "unknown_permission_request"); // 新增代码+DesktopGUIPermissions：读取 request_id；如果没有这行，权限按钮无法调用后端决策 endpoint。
  const turnId = safePermissionText(event.payload.turn_id ?? event.turn_id, event.turn_id); // 新增代码+DesktopGUIPermissions：读取 turn id；如果没有这行，后端无法校验回答归属。
  const appName = safePermissionText(event.payload.app_name ?? event.payload.tool_name ?? event.payload.permission_kind, "OpenHarness"); // 新增代码+DesktopGUIPermissions：读取应用或工具名；如果没有这行，用户不知道权限来源。
  const toolName = safePermissionText(event.payload.tool_name, appName); // 新增代码+DesktopGUIPermissionsV2：读取具体工具名并兜底到应用名；如果没有这行，V2 弹窗会丢失工具来源。
  const actionSummary = safePermissionText(event.payload.action_summary, `${appName} 请求继续执行`); // 新增代码+DesktopGUIPermissionsV2：读取动作摘要并兜底；如果没有这行，banner 和弹窗只能显示零散字段。
  const reason = safePermissionText(event.payload.reason ?? event.payload.risk_summary ?? event.payload.risk_summary_text, "后端请求继续执行需要用户确认。"); // 新增代码+DesktopGUIPermissions：读取脱敏原因；如果没有这行，弹窗无法解释为什么要权限。
  const riskSummary = safePermissionText(event.payload.risk_summary ?? event.payload.risk_level, "请确认该操作符合你的预期。"); // 新增代码+DesktopGUIPermissions：读取风险摘要；如果没有这行，用户缺少安全判断依据。
  const answered = event.event_type === "permission_answered" || event.payload.status === "approved" || event.payload.status === "denied"; // 新增代码+DesktopGUIPermissions：识别已回答事件；如果没有这行，回答后的事件仍会打开弹窗。
  return { requestId, turnId, toolName, appName, actionSummary, reason, riskSummary, answered }; // 修改代码+DesktopGUIPermissionsV2：返回权限 view model；如果没有这行，调用方拿不到可渲染数据。
} // 新增代码+DesktopGUIPermissions：函数段结束，permissionFromEvent 到此结束；如果没有这个边界，初学者不易看出事件适配范围。

export function AppShell(): JSX.Element { // 修改代码+DesktopToolTimeline：函数段开始，组织桌面 GUI 主壳；如果没有这段，各组件无法组合成 Codex 风格窗口。
  const [threadState, dispatchThread] = useReducer(threadReducer, initialThreadState); // 修改代码+DesktopToolTimeline：创建对话线程状态；如果没有这行，用户消息和助手消息无法进入 UI。
  const [statusState, dispatchStatus] = useReducer(appendStatusEvents, initialStatusState); // 新增代码+DesktopToolTimeline：创建状态时间线状态；如果没有这行，轮询事件无法去重和保存游标。
  const [projectName, setProjectName] = useState("OpenHarness-main"); // 新增代码+DesktopGUISessions：保存侧栏当前项目名；如果没有这行，侧栏只能显示硬编码名称，换工作区后会误导用户。
  const [sidebarSessions, setSidebarSessions] = useState<SidebarSession[]>([]); // 新增代码+DesktopGUISessions：保存最近会话列表；如果没有这行，后端 session 数据没有 UI 容器。
  const [archivedCount, setArchivedCount] = useState(0); // 新增代码+DesktopGUISessionSearch：保存归档会话数量；如果没有这行，归档入口无法显示真实计数。
  const [activeConversationId, setActiveConversationId] = useState("default"); // 新增代码+DesktopGUISessions：保存当前提交要写入的会话 id；如果没有这行，点击历史会话后新 prompt 仍会写回 default 会话。
  const [searchOpen, setSearchOpen] = useState(false); // 新增代码+DesktopGUISessionSearch：保存搜索面板是否打开；如果没有这行，侧栏搜索按钮无法控制弹层。
  const [searchArchivedMode, setSearchArchivedMode] = useState(false); // 新增代码+DesktopGUISessionSearch：保存搜索是否处于归档过滤模式；如果没有这行，归档入口会退化成普通搜索。
  const [searchQuery, setSearchQuery] = useState(""); // 新增代码+DesktopGUISessionSearch：保存当前搜索词；如果没有这行，搜索输入框无法受控。
  const [searchResults, setSearchResults] = useState<SearchPanelResult[]>([]); // 新增代码+DesktopGUISessionSearch：保存搜索结果；如果没有这行，搜索面板没有数据容器。
  const [searchLoading, setSearchLoading] = useState(false); // 新增代码+DesktopGUISessionSearch：保存搜索加载状态；如果没有这行，用户不知道搜索是否正在进行。
  const [browserProviderStatus, setBrowserProviderStatus] = useState<Record<string, unknown>>({}); // 修改代码+DesktopRuntimePanels：保存浏览器 provider 兜底状态；如果没有这行，右侧 BrowserPanel 在旧 payload 下没有真实后端数据。
  const [runtimePanels, setRuntimePanels] = useState<Record<string, unknown>>({}); // 新增代码+DesktopRuntimePanels：保存 V2 runtime panels 状态；如果没有这行，浏览器和 Computer Use 成熟面板无法拿到统一后端事实。
  const [harnessPayload, setHarnessPayload] = useState<Record<string, unknown>>({}); // 新增代码+DesktopGUIHarnessPanel：保存 V2 Harness 状态；如果没有这行，任务页签没有 active goal、queue 和 checkpoint。
  const [harnessControlPending, setHarnessControlPending] = useState(false); // 新增代码+DesktopGUIHarnessPanel：保存 Harness 控制请求等待态；如果没有这行，控制按钮无法避免重复点击。
  const [healthPayload, setHealthPayload] = useState<Record<string, unknown>>({}); // ????+DesktopDiagnosticsPanel??? V2 health payload??????????????? uptime?provider ? feature flags?
  const [diagnosticsPayload, setDiagnosticsPayload] = useState<Record<string, unknown>>({}); // ????+DesktopDiagnosticsPanel??? V2 diagnostics payload??????????????? release gate ???????
  const [bridgeIssue, setBridgeIssue] = useState(""); // 新增代码+DesktopBridgeOfflineBanner：保存 bridge 离线或降级提示；如果没有这一行，轮询失败只会留在控制台。
  const [answeredPermissionIds, setAnsweredPermissionIds] = useState<string[]>([]); // 新增代码+DesktopGUIPermissions：保存本地已点击过的权限请求；如果没有这行，等待 permission_answered 轮询期间弹窗可能重复出现。
  const [pendingPermissionDecisionId, setPendingPermissionDecisionId] = useState<string>(""); // 新增代码+DesktopGUIPermissionsV2：保存正在提交的权限请求 id；如果没有这行，按钮无法在后端确认前禁用。
  const bridgeConfig = window.openHarnessDesktop?.bridge ?? bridgeConfigFromLocationHash(); // 修改代码+DesktopBridgeConfig：优先读取 preload bridge，失败时读取本地 hash 兜底；如果没有这行，Electron preload 异常会让 GUI 完全离线。
  const guiClient = useMemo(() => { // 修改代码+DesktopToolTimeline：缓存 GUI client；如果没有这段，每次渲染都会创建新 client。
    if (!bridgeConfig?.baseUrl || !bridgeConfig.token) { // 修改代码+DesktopToolTimeline：检查 bridge 配置是否完整；如果没有这行，空 token 请求会反复失败。
      return null; // 修改代码+DesktopToolTimeline：配置缺失时不创建 client；如果没有这行，后续调用可能访问无效 client。
    } // 修改代码+DesktopToolTimeline：配置检查结束；如果没有这行，条件块语法不完整。
    return createGuiClient(bridgeConfig.baseUrl, bridgeConfig.token); // 修改代码+DesktopToolTimeline：创建带 token 的 client；如果没有这行，composer 和轮询无法访问 bridge。
  }, [bridgeConfig?.baseUrl, bridgeConfig?.token]); // 修改代码+DesktopToolTimeline：按 bridge 配置缓存 client；如果没有这行，useMemo 依赖不完整。
  const permissionEvent = useMemo(() => latestPermissionEvent(statusState.events), [statusState.events]); // 新增代码+DesktopGUIPermissions：从事件流中取最新权限事件；如果没有这行，权限 UI 无法跟随轮询更新。
  const permissionRequest = useMemo(() => permissionFromEvent(permissionEvent), [permissionEvent]); // 新增代码+DesktopGUIPermissions：把权限事件转成弹窗数据；如果没有这行，渲染层要直接解析后端 payload。
  const permissionDialogOpen = permissionRequest !== null && !permissionRequest.answered && !answeredPermissionIds.includes(permissionRequest.requestId); // 新增代码+DesktopGUIPermissions：计算弹窗是否打开；如果没有这行，已回答或已点击的权限请求仍可能弹出。
  const permissionDecisionPending = permissionRequest !== null && pendingPermissionDecisionId === permissionRequest.requestId; // 新增代码+DesktopGUIPermissionsV2：计算当前权限是否正在提交；如果没有这行，弹窗按钮无法进入等待态。

  function syncTurnEventsToThread(events: StatusEvent[]): void { // 修改代码+DesktopThreadStreaming：函数段开始，把后端事件重放到消息线程；如果没有这段代码，快速失败、流式增量和安全拒绝不会进入主线程。
    for (const event of events) { // 修改代码+DesktopThreadStreaming：逐条处理事件；如果没有这行代码，多个连续事件只能处理其中一个。
      const reduction = reduceGuiEventToThreadActions(event); // 新增代码+DesktopThreadStreaming：把事件转换成线程动作；如果没有这行代码，AppShell 会重新散落旧同步规则。
      for (const action of reduction.actions) { // 新增代码+DesktopThreadStreaming：逐条派发转换动作；如果没有这行代码，一个事件产生的多个动作无法全部应用。
        dispatchThread(action); // 新增代码+DesktopThreadStreaming：把动作交给 threadReducer；如果没有这行代码，事件不会改变主线程消息。
      } // 新增代码+DesktopThreadStreaming：动作派发循环结束；如果没有这行代码，for 循环语法不完整。
    } // 修改代码+DesktopThreadStreaming：事件重放循环结束；如果没有这行代码，for 循环语法不完整。
  } // 修改代码+DesktopThreadStreaming：函数段结束，syncTurnEventsToThread 到此结束；如果没有这个边界，初学者不易看出事件重放范围。

  async function refreshEventsAfter(sequence: number): Promise<void> { // 新增代码+DesktopFastEventReplay：函数段开始，从后端游标补拉事件；如果没有这段代码，send/retry 后的快速终态只能等下一轮轮询且可能错过消息占位。
    if (guiClient === null) { // 新增代码+DesktopFastEventReplay：没有 client 时不能补拉；如果没有这行代码，空 client 会导致运行时异常。
      return; // 新增代码+DesktopFastEventReplay：没有 client 直接退出；如果没有这行代码，后续会访问 null。
    } // 新增代码+DesktopFastEventReplay：client 检查结束；如果没有这行代码，条件块语法不完整。
    const payload = await guiClient.events(sequence, 50); // 新增代码+DesktopFastEventReplay：从后端读取指定游标后的事件；如果没有这行代码，无法追回快速完成或失败事件。
    const normalizedEvents = payload.events.map((event) => normalizeStatusEvent(event)); // 新增代码+DesktopFastEventReplay：规范化事件形状；如果没有这行代码，reducer 需要面对原始后端对象。
    if (normalizedEvents.length === 0) { // 新增代码+DesktopFastEventReplay：无新事件时不更新；如果没有这行代码，空数组也会触发不必要渲染。
      return; // 新增代码+DesktopFastEventReplay：空事件直接返回；如果没有这行代码，后续会做无意义 dispatch。
    } // 新增代码+DesktopFastEventReplay：空事件判断结束；如果没有这行代码，条件块语法不完整。
    dispatchStatus(normalizedEvents); // 新增代码+DesktopFastEventReplay：把补拉事件写入右侧时间线；如果没有这行代码，时间线可能晚于消息卡。
    syncTurnEventsToThread(normalizedEvents); // 新增代码+DesktopFastEventReplay：把补拉事件同步到主对话；如果没有这行代码，错误正文仍可能不显示。
    window.setTimeout(() => { syncTurnEventsToThread(normalizedEvents); }, 0); // 新增代码+DesktopFastEventReplay：在下一轮浏览器事件循环里再重放一次事件；如果没有这行代码，React 还没提交助手占位消息时，快速失败正文仍可能写不进去。
  } // 新增代码+DesktopFastEventReplay：函数段结束，refreshEventsAfter 到此结束；如果没有这个边界，初学者不易看出补拉范围。

  useEffect(() => { // 新增代码+DesktopGUISessions：副作用段开始，加载项目名和最近会话；如果没有这段，侧栏无法从真实 bridge 获取项目上下文。
    if (guiClient === null) { // 新增代码+DesktopGUISessions：没有 client 时跳过加载；如果没有这行，缺少 baseUrl/token 会持续请求失败。
      return undefined; // 新增代码+DesktopGUISessions：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUISessions：client 检查结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 修改代码+DesktopGUISessions：把本次副作用使用的 client 固定到局部常量；如果没有这行，TypeScript 会担心异步加载时 client 变成 null。
    let disposed = false; // 新增代码+DesktopGUISessions：记录组件是否已经卸载；如果没有这行，异步加载返回后可能更新已卸载组件。
    async function loadSidebarData(): Promise<void> { // 新增代码+DesktopGUISessions：函数段开始，集中读取 bootstrap 和 sessions；如果没有这段，侧栏数据加载逻辑会散落到渲染层。
      try { // 新增代码+DesktopGUISessions：捕获侧栏加载失败；如果没有这行，bridge 暂时不可用会让界面副作用抛错。
        const [bootstrapPayload, sessionsPayload, runtimePanelsPayload, healthPayloadResult, diagnosticsPayloadResult, harnessPayloadResult] = await Promise.all([activeClient.bootstrap(), activeClient.sessions(), activeClient.runtimePanels(), activeClient.health(), activeClient.diagnostics(), activeClient.harnessStatus()]); // 修改代码+DesktopGUIHarnessPanel：首屏同时读取 Harness 状态；如果没有这行，任务页签要等轮询后才有事实源。
        if (disposed) { // 新增代码+DesktopGUISessions：检查组件是否已卸载；如果没有这行，迟到响应可能继续 setState。
          return; // 新增代码+DesktopGUISessions：卸载后停止处理；如果没有这行，React 可能提示卸载组件被更新。
        } // 新增代码+DesktopGUISessions：卸载检查结束；如果没有这行，条件块语法不完整。
        setProjectName(projectNameFromWorkspace(bootstrapPayload.workspace)); // 新增代码+DesktopGUISessions：把 workspace 转成侧栏项目名；如果没有这行，项目身份不会显示真实目录。
        setSidebarSessions(normalizeSidebarSessions(sessionsPayload.sessions)); // 新增代码+DesktopGUISessions：把后端 sessions 转成可点击条目；如果没有这行，最近会话列表会一直为空。
        setArchivedCount(typeof sessionsPayload.archived_count === "number" ? sessionsPayload.archived_count : 0); // 新增代码+DesktopGUISessionSearch：保存归档会话计数；如果没有这行，侧栏归档入口无法显示真实数量。
        setBrowserProviderStatus(runtimePanelsPayload.browser); // 修改代码+DesktopRuntimePanels：把 V2 浏览器子面板作为旧 provider 兜底；如果没有这行，BrowserPanel 旧入参会停留在空状态。
        setRuntimePanels(runtimePanelsPayload); // 新增代码+DesktopRuntimePanels：保存完整 V2 面板 payload；如果没有这行，Computer Use 面板没有锁、急停和权限数据。
        setHarnessPayload(harnessPayloadResult); // 新增代码+DesktopGUIHarnessPanel：保存首屏 Harness payload；如果没有这行，任务页签初次打开会空白。
        setHealthPayload(healthPayloadResult); // ????+DesktopDiagnosticsPanel??? V2 health payload????????SettingsPanel ??????????
        setDiagnosticsPayload(diagnosticsPayloadResult); // ????+DesktopDiagnosticsPanel??? V2 diagnostics payload????????DiagnosticsPanel ????????
        setBridgeIssue(""); // 新增代码+DesktopBridgeOfflineBanner：首屏加载成功后清除离线提示；如果没有这一行，bridge 恢复后旧 banner 会继续显示。
      } catch (error) { // 新增代码+DesktopGUISessions：处理加载异常；如果没有这行，侧栏数据失败会变成未捕获错误。
        console.warn("GUI bridge sidebar load failed", error); // 新增代码+DesktopGUISessions：把失败留给开发者诊断；如果没有这行，侧栏为空时难以判断原因。
        if (!disposed) { // 新增代码+DesktopBridgeOfflineBanner：只在本轮加载仍有效时显示离线提示；如果没有这一行，卸载后的请求可能更新旧界面。
          setBridgeIssue("GUI bridge 暂时离线，正在等待本地后端恢复。"); // 新增代码+DesktopBridgeOfflineBanner：把离线状态显示到 GUI；如果没有这一行，用户看不到 bridge offline 验收面。
        } // 新增代码+DesktopBridgeOfflineBanner：离线提示保护结束；如果没有这一行，条件块语法不完整。
      } // 新增代码+DesktopGUISessions：异常处理结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+DesktopGUISessions：函数段结束，loadSidebarData 到此结束；如果没有这个边界，初学者不容易看出侧栏加载范围。
    void loadSidebarData(); // 新增代码+DesktopGUISessions：挂载后立即加载侧栏数据；如果没有这行，定义好的函数不会执行。
    return () => { // 新增代码+DesktopGUISessions：定义副作用清理逻辑；如果没有这行，卸载后无法标记异步任务失效。
      disposed = true; // 新增代码+DesktopGUISessions：标记异步任务已失效；如果没有这行，迟到响应可能继续更新状态。
    }; // 新增代码+DesktopGUISessions：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient]); // 新增代码+DesktopGUISessions：当 client 变化时重新加载侧栏数据；如果没有这行，换 bridge 配置后仍显示旧项目。

  useEffect(() => { // 新增代码+DesktopGUISessionSearch：副作用段开始，按输入词搜索历史会话；如果没有这段，搜索面板不会连接后端。
    if (!searchOpen) { // 新增代码+DesktopGUISessionSearch：面板关闭时停止搜索；如果没有这行，隐藏面板仍会发请求。
      setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：关闭时清理加载态；如果没有这行，下次打开可能显示旧的搜索中状态。
      return undefined; // 新增代码+DesktopGUISessionSearch：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUISessionSearch：关闭判断结束；如果没有这行，条件块语法不完整。
    if (guiClient === null) { // 新增代码+DesktopGUISessionSearch：没有 client 时不能搜索；如果没有这行，缺少 baseUrl/token 会持续报错。
      setSearchResults([]); // 新增代码+DesktopGUISessionSearch：清空结果；如果没有这行，离线状态可能显示过期结果。
      setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：清理加载态；如果没有这行，离线状态可能一直转圈。
      return undefined; // 新增代码+DesktopGUISessionSearch：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUISessionSearch：client 检查结束；如果没有这行，条件块语法不完整。
    const trimmedQuery = searchQuery.trim(); // 新增代码+DesktopGUISessionSearch：清理搜索词；如果没有这行，纯空格会触发无意义搜索。
    if (trimmedQuery.length === 0 && !searchArchivedMode) { // 修改代码+DesktopGUISessionSearch：普通搜索空查询直接清空，归档模式保留归档列表；如果没有这行，归档入口会被空 query 清掉。
      setSearchResults([]); // 新增代码+DesktopGUISessionSearch：清理结果；如果没有这行，空查询仍可能显示旧结果。
      setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：清理加载态；如果没有这行，空查询可能显示正在搜索。
      return undefined; // 新增代码+DesktopGUISessionSearch：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUISessionSearch：空查询判断结束；如果没有这行，条件块语法不完整。
    if (trimmedQuery.length === 0 && searchArchivedMode) { // 新增代码+DesktopGUISessionSearch：归档模式空查询不自动搜索；如果没有这行，打开归档视图会被搜索副作用覆盖。
      return undefined; // 新增代码+DesktopGUISessionSearch：保留 handleOpenArchived 填充的归档列表；如果没有这行，归档结果会被清空或重复请求。
    } // 新增代码+DesktopGUISessionSearch：归档空查询判断结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 新增代码+DesktopGUISessionSearch：固定本轮搜索使用的 client；如果没有这行，异步返回时 TypeScript 会担心 client 变成 null。
    let disposed = false; // 新增代码+DesktopGUISessionSearch：记录本轮搜索是否失效；如果没有这行，旧 query 的迟到结果可能覆盖新 query。
    setSearchLoading(true); // 新增代码+DesktopGUISessionSearch：进入加载态；如果没有这行，用户输入后没有反馈。
    async function runSearch(): Promise<void> { // 新增代码+DesktopGUISessionSearch：函数段开始，执行一次后端搜索；如果没有这段，副作用里的异步逻辑会散落。
      try { // 新增代码+DesktopGUISessionSearch：捕获搜索失败；如果没有这行，bridge 暂时不可用会抛出未捕获 Promise。
        const payload = await activeClient.searchSessions(trimmedQuery, searchArchivedMode); // 修改代码+DesktopGUISessionSearch：调用 V2 搜索接口并按模式包含归档；如果没有这行，归档视图输入关键词会漏掉归档会话。
        if (disposed) { // 新增代码+DesktopGUISessionSearch：检查本轮请求是否失效；如果没有这行，旧结果可能覆盖新输入。
          return; // 新增代码+DesktopGUISessionSearch：失效后退出；如果没有这行，仍会 setState。
        } // 新增代码+DesktopGUISessionSearch：失效判断结束；如果没有这行，条件块语法不完整。
        setSearchResults(normalizeSearchResults(payload.results)); // 新增代码+DesktopGUISessionSearch：保存规范化搜索结果；如果没有这行，SearchPanel 不会显示后端结果。
      } catch (error) { // 新增代码+DesktopGUISessionSearch：处理搜索异常；如果没有这行，临时断线会打断 React 副作用。
        console.warn("GUI bridge search failed", error); // 新增代码+DesktopGUISessionSearch：把搜索失败留给开发者诊断；如果没有这行，用户看到空结果时难以排查。
        if (!disposed) { // 新增代码+DesktopGUISessionSearch：只在本轮仍有效时清空结果；如果没有这行，旧请求可能改写新状态。
          setSearchResults([]); // 新增代码+DesktopGUISessionSearch：失败时清空结果；如果没有这行，界面可能显示过期结果。
        } // 新增代码+DesktopGUISessionSearch：失败清理判断结束；如果没有这行，条件块语法不完整。
      } finally { // 新增代码+DesktopGUISessionSearch：无论成功失败都退出加载态；如果没有这行，失败后会一直显示正在搜索。
        if (!disposed) { // 新增代码+DesktopGUISessionSearch：只更新有效请求；如果没有这行，旧请求可能关闭新请求的加载态。
          setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：清理加载态；如果没有这行，搜索按钮反馈不会停止。
        } // 新增代码+DesktopGUISessionSearch：加载态清理判断结束；如果没有这行，条件块语法不完整。
      } // 新增代码+DesktopGUISessionSearch：搜索异常处理结束；如果没有这行，try/catch/finally 语法不完整。
    } // 新增代码+DesktopGUISessionSearch：函数段结束，runSearch 到此结束；如果没有边界说明，初学者不易看出搜索请求范围。
    const timeoutId = window.setTimeout(() => { void runSearch(); }, 160); // 新增代码+DesktopGUISessionSearch：给输入增加轻量防抖；如果没有这行，快速输入会连续打后端。
    return () => { // 新增代码+DesktopGUISessionSearch：定义副作用清理逻辑；如果没有这行，旧请求无法标记失效。
      disposed = true; // 新增代码+DesktopGUISessionSearch：标记本轮搜索失效；如果没有这行，迟到响应会覆盖新输入。
      window.clearTimeout(timeoutId); // 新增代码+DesktopGUISessionSearch：清理防抖计时器；如果没有这行，关闭面板后仍可能发请求。
    }; // 新增代码+DesktopGUISessionSearch：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient, searchOpen, searchQuery, searchArchivedMode]); // 修改代码+DesktopGUISessionSearch：按 client、面板状态、搜索词和归档模式重新搜索；如果没有这行，搜索会使用过期输入。

  useEffect(() => { // 新增代码+DesktopToolTimeline：副作用段开始，定时读取 bridge 事件；如果没有这段，右侧时间线和消息状态不会自动刷新。
    if (guiClient === null) { // 新增代码+DesktopToolTimeline：没有 client 时跳过轮询；如果没有这行，缺少配置时会持续报网络错误。
      return undefined; // 新增代码+DesktopToolTimeline：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopToolTimeline：client 检查结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 修改代码+DesktopToolTimeline：把本次副作用使用的 client 固定到局部常量；如果没有这行，TypeScript 会担心异步轮询时 client 变成 null。
    let disposed = false; // 新增代码+DesktopToolTimeline：记录组件是否已卸载；如果没有这行，异步请求返回后可能更新已卸载组件。
    async function pollEvents(): Promise<void> { // 新增代码+DesktopToolTimeline：函数段开始，执行一次事件轮询；如果没有这段，setInterval 没有可复用任务。
      try { // 新增代码+DesktopToolTimeline：捕获轮询失败；如果没有这行，临时断线会打断 React 副作用。
        const payload = await activeClient.events(statusState.lastSequence, 50); // 修改代码+DesktopToolTimeline：请求 lastSequence 之后的事件；如果没有这行，前端拿不到 bridge 最新状态。
        if (disposed) { // 新增代码+DesktopToolTimeline：检查组件是否已经卸载；如果没有这行，卸载后仍可能 dispatch。
          return; // 新增代码+DesktopToolTimeline：卸载后停止处理；如果没有这行，可能产生 React 状态更新警告。
        } // 新增代码+DesktopToolTimeline：卸载检查结束；如果没有这行，条件块语法不完整。
        const normalizedEvents = payload.events.map((event) => normalizeStatusEvent(event)); // 新增代码+DesktopToolTimeline：规范化后端原始事件；如果没有这行，UI 组件会直接面对不稳定对象。
        setBridgeIssue(""); // 修改代码+DesktopBridgeOfflineBanner：只要轮询成功就清除离线提示；如果没有这一行，无新事件的恢复场景仍会显示离线。
        if (normalizedEvents.length === 0) { // 新增代码+DesktopToolTimeline：没有新事件时直接返回；如果没有这行，空数组也会触发不必要渲染。
          return; // 新增代码+DesktopToolTimeline：结束空轮询；如果没有这行，后续逻辑会做无意义工作。
        } // 新增代码+DesktopToolTimeline：空事件判断结束；如果没有这行，条件块语法不完整。
        dispatchStatus(normalizedEvents); // 新增代码+DesktopToolTimeline：把新事件写入状态时间线；如果没有这行，右侧面板不会刷新。
        syncTurnEventsToThread(normalizedEvents); // 修改代码+DesktopFastEventReplay：复用统一事件重放逻辑；如果没有这行代码，轮询和发送后补拉会出现两套不同同步规则。
      } catch (error) { // 新增代码+DesktopToolTimeline：处理轮询异常；如果没有这行，bridge 暂时不可用会让副作用抛出未捕获错误。
        console.warn("GUI bridge event polling failed", error); // 新增代码+DesktopToolTimeline：把失败留给开发者诊断；如果没有这行，轮询失败会静默到难以排查。
        if (!disposed) { // 新增代码+DesktopBridgeOfflineBanner：只在组件仍挂载时显示离线提示；如果没有这一行，旧轮询可能更新已卸载界面。
          setBridgeIssue("GUI bridge 暂时离线，正在等待本地后端恢复。"); // 新增代码+DesktopBridgeOfflineBanner：把轮询失败变成顶部可见 banner；如果没有这一行，bridge offline 验收没有视觉证据。
        } // 新增代码+DesktopBridgeOfflineBanner：轮询离线提示保护结束；如果没有这一行，条件块语法不完整。
      } // 新增代码+DesktopToolTimeline：异常处理结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+DesktopToolTimeline：函数段结束，pollEvents 到此结束；如果没有这个边界，初学者不容易看出轮询范围。
    void pollEvents(); // 新增代码+DesktopToolTimeline：挂载后立即轮询一次；如果没有这行，用户要等到下一个 interval 才看到事件。
    const intervalId = window.setInterval(() => { void pollEvents(); }, 1500); // 新增代码+DesktopToolTimeline：每 1.5 秒轮询一次；如果没有这行，长任务进度不会持续刷新。
    return () => { // 新增代码+DesktopToolTimeline：定义副作用清理逻辑；如果没有这行，组件卸载时轮询计时器会泄漏。
      disposed = true; // 新增代码+DesktopToolTimeline：标记异步任务已失效；如果没有这行，迟到响应可能继续更新状态。
      window.clearInterval(intervalId); // 新增代码+DesktopToolTimeline：清理轮询计时器；如果没有这行，窗口关闭后仍可能保留定时任务。
    }; // 新增代码+DesktopToolTimeline：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient, statusState.lastSequence]); // 新增代码+DesktopToolTimeline：按 client 和事件游标重建轮询；如果没有这行，轮询会使用过期游标。

  useEffect(() => { // 新增代码+DesktopGUIHarnessPanel：副作用段开始，定时刷新 Harness 状态；如果没有这段，长任务面板会停留在首屏快照。
    if (guiClient === null) { // 新增代码+DesktopGUIHarnessPanel：没有 client 时跳过轮询；如果没有这行，缺少配置时会持续报网络错误。
      return undefined; // 新增代码+DesktopGUIHarnessPanel：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUIHarnessPanel：client 检查结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 新增代码+DesktopGUIHarnessPanel：固定本次副作用使用的 client；如果没有这行，异步返回时 TypeScript 会担心 client 变成 null。
    let disposed = false; // 新增代码+DesktopGUIHarnessPanel：记录组件是否已卸载；如果没有这行，迟到响应可能更新已卸载组件。
    async function pollHarness(): Promise<void> { // 新增代码+DesktopGUIHarnessPanel：函数段开始，执行一次 Harness 状态刷新；如果没有这段，interval 没有复用任务。
      try { // 新增代码+DesktopGUIHarnessPanel：捕获轮询失败；如果没有这行，bridge 暂时不可用会打断副作用。
        const payload = await activeClient.harnessStatus(); // 新增代码+DesktopGUIHarnessPanel：请求后端 Harness 状态；如果没有这行，任务页签没有实时事实。
        if (disposed) { // 新增代码+DesktopGUIHarnessPanel：检查组件是否已经卸载；如果没有这行，卸载后仍可能 setState。
          return; // 新增代码+DesktopGUIHarnessPanel：卸载后停止处理；如果没有这行，可能产生 React 状态更新警告。
        } // 新增代码+DesktopGUIHarnessPanel：卸载检查结束；如果没有这行，条件块语法不完整。
        setHarnessPayload(payload); // 新增代码+DesktopGUIHarnessPanel：保存最新 Harness payload；如果没有这行，面板不会更新。
      } catch (error) { // 新增代码+DesktopGUIHarnessPanel：处理轮询异常；如果没有这行，断线会变成未捕获 Promise。
        console.warn("GUI bridge harness polling failed", error); // 新增代码+DesktopGUIHarnessPanel：把失败留给开发者诊断；如果没有这行，任务面板不刷新时难以排查。
      } // 新增代码+DesktopGUIHarnessPanel：异常处理结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+DesktopGUIHarnessPanel：函数段结束，pollHarness 到此结束；如果没有边界说明，初学者不易看出轮询范围。
    void pollHarness(); // 新增代码+DesktopGUIHarnessPanel：挂载后立即刷新一次；如果没有这行，用户要等到 interval 才看到状态。
    const intervalId = window.setInterval(() => { void pollHarness(); }, 3000); // 新增代码+DesktopGUIHarnessPanel：每 3 秒刷新 Harness 状态；如果没有这行，长任务进展不会持续可见。
    return () => { // 新增代码+DesktopGUIHarnessPanel：定义清理函数；如果没有这行，组件卸载时轮询计时器会泄漏。
      disposed = true; // 新增代码+DesktopGUIHarnessPanel：标记异步任务已失效；如果没有这行，迟到响应可能继续更新状态。
      window.clearInterval(intervalId); // 新增代码+DesktopGUIHarnessPanel：清理轮询计时器；如果没有这行，窗口关闭后仍可能保留定时任务。
    }; // 新增代码+DesktopGUIHarnessPanel：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient]); // 新增代码+DesktopGUIHarnessPanel：按 client 变化重建 Harness 轮询；如果没有这行，换 bridge 后会使用旧连接。

  function handleOpenSearch(): void { // 新增代码+DesktopGUISessionSearch：函数段开始，打开普通历史搜索；如果没有这段，搜索入口无法重置归档模式。
    setSearchArchivedMode(false); // 新增代码+DesktopGUISessionSearch：关闭归档过滤；如果没有这行，普通搜索可能继续只看归档范围。
    setSearchOpen(true); // 新增代码+DesktopGUISessionSearch：打开搜索面板；如果没有这行，搜索入口点击没有可见结果。
    setSearchQuery(""); // 新增代码+DesktopGUISessionSearch：清空旧搜索词；如果没有这行，普通搜索会残留上次输入。
    setSearchResults([]); // 新增代码+DesktopGUISessionSearch：清空旧搜索结果；如果没有这行，面板刚打开会显示过期结果。
  } // 新增代码+DesktopGUISessionSearch：函数段结束，handleOpenSearch 到此结束；如果没有边界说明，初学者不易看出普通搜索范围。

  async function handleOpenArchived(): Promise<void> { // 新增代码+DesktopGUISessionSearch：函数段开始，打开归档会话过滤视图；如果没有这段，归档入口只是普通搜索按钮。
    setSearchArchivedMode(true); // 新增代码+DesktopGUISessionSearch：启用归档过滤；如果没有这行，归档视图输入关键词会漏掉归档会话。
    setSearchOpen(true); // 新增代码+DesktopGUISessionSearch：打开搜索面板；如果没有这行，归档入口点击没有可见面板。
    setSearchQuery(""); // 新增代码+DesktopGUISessionSearch：清空搜索词以展示归档列表；如果没有这行，归档入口会沿用普通搜索词。
    setSearchLoading(true); // 新增代码+DesktopGUISessionSearch：进入归档加载态；如果没有这行，拉取归档时没有反馈。
    if (guiClient === null) { // 新增代码+DesktopGUISessionSearch：处理 bridge 未配置；如果没有这行，归档入口会访问空 client。
      setSearchResults([]); // 新增代码+DesktopGUISessionSearch：清空结果；如果没有这行，离线时可能显示过期归档。
      setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：结束加载态；如果没有这行，离线时会一直显示搜索中。
      return; // 新增代码+DesktopGUISessionSearch：没有 client 时退出；如果没有这行，后续会访问 null。
    } // 新增代码+DesktopGUISessionSearch：client 检查结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopGUISessionSearch：捕获归档加载失败；如果没有这行，bridge 暂时不可用会变成未捕获 Promise。
      const payload = await guiClient.sessions(true); // 新增代码+DesktopGUISessionSearch：读取包含归档的 sessions；如果没有这行，归档入口拿不到隐藏会话。
      const archivedResults = normalizeSidebarSessions(payload.sessions).filter((session) => session.archived).map((session) => ({ sessionId: session.id, title: session.title, snippet: session.subtitle ?? "", archived: true })); // 新增代码+DesktopGUISessionSearch：把归档会话转成搜索面板结果；如果没有这行，归档视图无法复用结果列表。
      setSearchResults(archivedResults); // 新增代码+DesktopGUISessionSearch：显示归档会话列表；如果没有这行，归档入口打开后仍是空面板。
      setArchivedCount(typeof payload.archived_count === "number" ? payload.archived_count : archivedResults.length); // 新增代码+DesktopGUISessionSearch：同步归档计数；如果没有这行，侧栏数字可能落后。
    } catch (error) { // 新增代码+DesktopGUISessionSearch：处理归档加载异常；如果没有这行，用户看不到失败后的稳定状态。
      console.warn("GUI bridge archived sessions load failed", error); // 新增代码+DesktopGUISessionSearch：把失败留给开发者诊断；如果没有这行，归档为空时难以排查。
      setSearchResults([]); // 新增代码+DesktopGUISessionSearch：失败时清空归档结果；如果没有这行，旧归档列表会误导用户。
    } finally { // 新增代码+DesktopGUISessionSearch：无论成功失败都退出加载态；如果没有这行，失败后会一直显示正在搜索。
      setSearchLoading(false); // 新增代码+DesktopGUISessionSearch：清理加载态；如果没有这行，归档面板会一直转圈。
    } // 新增代码+DesktopGUISessionSearch：归档加载异常处理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+DesktopGUISessionSearch：函数段结束，handleOpenArchived 到此结束；如果没有边界说明，初学者不易看出归档视图范围。

  async function refreshSidebarSessions(): Promise<void> { // 新增代码+DesktopGUISessionSearch：函数段开始，刷新最近会话和归档计数；如果没有这段，新消息提交后侧栏会落后。
    if (guiClient === null) { // 新增代码+DesktopGUISessionSearch：没有 client 时不能刷新；如果没有这行，缺少 bridge 配置会访问 null。
      return; // 新增代码+DesktopGUISessionSearch：没有 client 直接退出；如果没有这行，后续会抛运行时错误。
    } // 新增代码+DesktopGUISessionSearch：client 检查结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopGUISessionSearch：捕获刷新失败；如果没有这行，临时断线会变成未捕获 Promise。
      const payload = await guiClient.sessions(); // 新增代码+DesktopGUISessionSearch：读取 V2 sessions；如果没有这行，侧栏无法拿到最新会话。
      setSidebarSessions(normalizeSidebarSessions(payload.sessions)); // 新增代码+DesktopGUISessionSearch：更新最近会话列表；如果没有这行，新消息不会出现在侧栏。
      setArchivedCount(typeof payload.archived_count === "number" ? payload.archived_count : 0); // 新增代码+DesktopGUISessionSearch：更新归档计数；如果没有这行，归档数字会落后。
    } catch (error) { // 新增代码+DesktopGUISessionSearch：处理刷新异常；如果没有这行，刷新失败会打断用户流程。
      console.warn("GUI bridge sessions refresh failed", error); // 新增代码+DesktopGUISessionSearch：把失败留给开发者诊断；如果没有这行，侧栏不刷新时难以排查。
    } // 新增代码+DesktopGUISessionSearch：刷新异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopGUISessionSearch：函数段结束，refreshSidebarSessions 到此结束；如果没有边界说明，初学者不易看出刷新范围。

  function handleNewConversation(): void { // 新增代码+DesktopGUISessionSearch：函数段开始，创建新的本地会话上下文；如果没有这段，快速对话按钮无法切出历史会话。
    const nextSessionId = `desktop_${Date.now()}`; // 新增代码+DesktopGUISessionSearch：生成新的会话 id；如果没有这行，新对话可能继续写入旧 session。
    setActiveConversationId(nextSessionId); // 新增代码+DesktopGUISessionSearch：把后续 prompt 指向新会话；如果没有这行，用户以为新对话但后端仍写旧会话。
    setSearchArchivedMode(false); // 新增代码+DesktopGUISessionSearch：退出归档模式；如果没有这行，新对话后搜索仍可能停在归档过滤。
    setSearchOpen(false); // 新增代码+DesktopGUISessionSearch：关闭搜索面板；如果没有这行，新对话后搜索弹层仍会遮住主界面。
    setSearchQuery(""); // 新增代码+DesktopGUISessionSearch：清空搜索词；如果没有这行，下次打开搜索会残留旧输入。
    setSearchResults([]); // 新增代码+DesktopGUISessionSearch：清空搜索结果；如果没有这行，下次打开搜索会残留旧结果。
    dispatchThread({ type: "thread_reset", messages: [] }); // 新增代码+DesktopGUISessionSearch：清空主线程消息；如果没有这行，新对话仍显示旧历史。
  } // 新增代码+DesktopGUISessionSearch：函数段结束，handleNewConversation 到此结束；如果没有边界说明，初学者不易看出新会话范围。

  async function handleSelectSession(sessionId: string): Promise<void> { // 修改代码+DesktopGUISessionSearch：函数段开始，处理侧栏或搜索会话点击；如果没有这段，最近会话只是静态列表不能恢复上下文。
    setActiveConversationId(sessionId); // 新增代码+DesktopGUISessions：记录当前会话 id；如果没有这行，后续新 prompt 不会发送到用户选中的会话。
    setSearchArchivedMode(false); // 新增代码+DesktopGUISessionSearch：选择会话后退出归档模式；如果没有这行，下次搜索可能仍在归档过滤。
    setSearchOpen(false); // 新增代码+DesktopGUISessionSearch：选中会话后关闭搜索面板；如果没有这行，搜索弹层会挡住恢复后的对话。
    if (guiClient === null) { // 新增代码+DesktopGUISessions：处理 bridge 未配置；如果没有这行，点击会话会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_resume_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法恢复历史会话。", status: "failed" } }); // 新增代码+DesktopGUISessions：把恢复失败原因显示给用户；如果没有这行，用户不知道为什么点击无效。
      return; // 新增代码+DesktopGUISessions：没有 client 时停止恢复；如果没有这行，会继续执行空 client 请求。
    } // 新增代码+DesktopGUISessions：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopGUISessions：捕获恢复失败；如果没有这行，后端异常会变成未捕获 Promise。
      const response = await guiClient.resumeSession(sessionId); // 新增代码+DesktopGUISessions：请求后端恢复指定 session；如果没有这行，主线程不会拿到历史消息。
      dispatchThread({ type: "thread_reset", messages: normalizeThreadMessages(response.messages) }); // 新增代码+DesktopGUISessions：用恢复消息重置主线程；如果没有这行，点击历史会话不会改变对话内容。
    } catch (error) { // 新增代码+DesktopGUISessions：处理恢复异常；如果没有这行，恢复失败没有 UI 反馈。
      dispatchThread({ type: "message_added", message: { id: `local_resume_error_${Date.now()}`, role: "system", text: `会话恢复失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopGUISessions：把错误显示到线程；如果没有这行，用户看不到失败原因。
    } // 新增代码+DesktopGUISessions：异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopGUISessions：函数段结束，handleSelectSession 到此结束；如果没有这个边界，初学者不容易看出恢复流程范围。

  async function handlePermissionDecision(decision: "approve" | "deny"): Promise<void> { // 新增代码+DesktopGUIPermissions：函数段开始，处理权限允许或拒绝按钮；如果没有这段，PermissionDialog 按钮没有后端动作。
    if (permissionRequest === null) { // 新增代码+DesktopGUIPermissions：没有权限请求时直接退出；如果没有这行，空状态点击会访问不存在字段。
      return; // 新增代码+DesktopGUIPermissions：退出无请求分支；如果没有这行，后续会继续执行错误请求。
    } // 新增代码+DesktopGUIPermissions：无请求判断结束；如果没有这行，条件块语法不完整。
    if (pendingPermissionDecisionId === permissionRequest.requestId) { // 新增代码+DesktopGUIPermissionsV2：拦截同一权限的重复点击；如果没有这行，快速双击可能发出两次决策请求。
      return; // 新增代码+DesktopGUIPermissionsV2：已有提交在路上时直接退出；如果没有这行，后端会收到无意义重复请求。
    } // 新增代码+DesktopGUIPermissionsV2：重复提交判断结束；如果没有这行，条件块语法不完整。
    if (guiClient === null) { // 新增代码+DesktopGUIPermissions：处理 bridge 未配置；如果没有这行，按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_permission_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法提交权限决定。", status: "failed" } }); // 新增代码+DesktopGUIPermissions：显示配置缺失提示；如果没有这行，用户不知道按钮为什么无效。
      return; // 新增代码+DesktopGUIPermissions：没有 client 时停止提交；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopGUIPermissions：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    setPendingPermissionDecisionId(permissionRequest.requestId); // 新增代码+DesktopGUIPermissionsV2：标记当前权限正在提交；如果没有这行，按钮不会在后端确认前禁用。
    try { // 新增代码+DesktopGUIPermissions：捕获权限决策失败；如果没有这行，404/409 会变成未捕获 Promise。
      await guiClient.decidePermission(permissionRequest.requestId, permissionRequest.turnId, decision, decision === "approve" ? "用户在 GUI 中点击允许" : "用户在 GUI 中点击拒绝"); // 新增代码+DesktopGUIPermissions：把允许/拒绝意图提交给后端；如果没有这行，前端会绕过真实权限 machinery。
      setAnsweredPermissionIds((current) => current.includes(permissionRequest.requestId) ? current : [...current, permissionRequest.requestId]); // 新增代码+DesktopGUIPermissions：本地标记该请求已点击；如果没有这行，等待轮询期间弹窗可能继续打开。
    } catch (error) { // 新增代码+DesktopGUIPermissions：处理权限提交异常；如果没有这行，用户看不到后端拒绝原因。
      dispatchThread({ type: "message_added", message: { id: `local_permission_error_${Date.now()}`, role: "system", text: `权限决定提交失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopGUIPermissions：把错误写入主线程；如果没有这行，404/409 只会留在控制台。
    } finally { // 新增代码+DesktopGUIPermissionsV2：无论成功失败都清理提交态；如果没有这行，失败后按钮会一直禁用。
      setPendingPermissionDecisionId(""); // 新增代码+DesktopGUIPermissionsV2：清空正在提交的权限 id；如果没有这行，下一次权限请求可能被误判为 pending。
    } // 新增代码+DesktopGUIPermissions：异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopGUIPermissions：函数段结束，handlePermissionDecision 到此结束；如果没有这个边界，初学者不容易看出权限决策流程范围。

  async function handleHarnessControl(action: "pause" | "resume"): Promise<void> { // 新增代码+DesktopGUIHarnessPanel：函数段开始，处理长任务暂停或恢复请求；如果没有这段，任务页签即使后端支持控制也无法触发动作。
    if (guiClient === null) { // 新增代码+DesktopGUIHarnessPanel：处理 bridge 未配置；如果没有这行，控制按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_harness_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法控制长任务。", status: "failed" } }); // 新增代码+DesktopGUIHarnessPanel：把配置缺失写到主线程；如果没有这行，用户不知道暂停或恢复为什么无效。
      return; // 新增代码+DesktopGUIHarnessPanel：没有 client 时停止控制流程；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopGUIHarnessPanel：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    setHarnessControlPending(true); // 新增代码+DesktopGUIHarnessPanel：标记控制请求正在提交；如果没有这行，按钮可能被重复点击。
    try { // 新增代码+DesktopGUIHarnessPanel：捕获暂停或恢复失败；如果没有这行，后端未支持会变成未捕获 Promise。
      if (action === "pause") { // 新增代码+DesktopGUIHarnessPanel：判断当前请求是否为暂停；如果没有这行，暂停和恢复会走同一条错误路径。
        await guiClient.pauseHarness(); // 新增代码+DesktopGUIHarnessPanel：调用后端暂停端点；如果没有这行，暂停按钮没有真实后端动作。
      } else { // 新增代码+DesktopGUIHarnessPanel：处理恢复分支；如果没有这行，恢复请求没有独立路径。
        await guiClient.resumeHarness(); // 新增代码+DesktopGUIHarnessPanel：调用后端恢复端点；如果没有这行，恢复按钮没有真实后端动作。
      } // 新增代码+DesktopGUIHarnessPanel：暂停或恢复分支结束；如果没有这行，条件块语法不完整。
      const payload = await guiClient.harnessStatus(); // 新增代码+DesktopGUIHarnessPanel：控制请求后刷新 Harness 状态；如果没有这行，面板会停留在旧事实。
      setHarnessPayload(payload); // 新增代码+DesktopGUIHarnessPanel：把最新状态写入页面；如果没有这行，用户看不到控制后的结果。
    } catch (error) { // 新增代码+DesktopGUIHarnessPanel：处理控制异常；如果没有这行，未支持或断线只会留在控制台。
      const actionLabel = action === "pause" ? "暂停" : "恢复"; // 新增代码+DesktopGUIHarnessPanel：把动作转成中文文案；如果没有这行，错误消息不够直观。
      dispatchThread({ type: "message_added", message: { id: `local_harness_${action}_error_${Date.now()}`, role: "system", text: `长任务${actionLabel}请求失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopGUIHarnessPanel：把后端控制错误显示到主线程；如果没有这行，用户无法理解控制失败原因。
    } finally { // 新增代码+DesktopGUIHarnessPanel：无论成功失败都清理等待态；如果没有这行，失败后按钮可能一直禁用。
      setHarnessControlPending(false); // 新增代码+DesktopGUIHarnessPanel：结束控制请求等待态；如果没有这行，后续控制按钮无法恢复点击。
    } // 新增代码+DesktopGUIHarnessPanel：异常处理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+DesktopGUIHarnessPanel：函数段结束，handleHarnessControl 到此结束；如果没有这个边界，初学者不容易看出长任务控制范围。

  async function handleCancelTurn(turnId: string): Promise<void> { // 新增代码+DesktopTurnActions：函数段开始，处理 GUI 取消按钮；如果没有这段，消息卡取消按钮不会调用后端 cancel。
    if (turnId.length === 0) { // 新增代码+DesktopTurnActions：防御空 turnId；如果没有这行，错误按钮状态可能发出无意义请求。
      return; // 新增代码+DesktopTurnActions：空 turnId 直接退出；如果没有这行，后续会打到错误 endpoint。
    } // 新增代码+DesktopTurnActions：空 turnId 判断结束；如果没有这行，条件块语法不完整。
    if (guiClient === null) { // 新增代码+DesktopTurnActions：处理 bridge 未配置；如果没有这行，取消按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_cancel_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法取消本轮。", status: "failed" } }); // 新增代码+DesktopTurnActions：把配置缺失显示给用户；如果没有这行，点击取消会静默失败。
      return; // 新增代码+DesktopTurnActions：没有 client 时停止取消；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopTurnActions：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopTurnActions：捕获取消请求失败；如果没有这行，404/409 会变成未捕获 Promise。
      const response = await guiClient.cancelTurn(turnId); // 新增代码+DesktopTurnActions：调用后端 cancel endpoint；如果没有这行，GUI 取消按钮只有装饰效果。
      dispatchThread({ type: "turn_status_changed", turnId: response.turn_id, status: response.status }); // 新增代码+DesktopTurnActions：立即把消息切到 cancelling；如果没有这行，用户要等下一次轮询才看到反馈。
    } catch (error) { // 新增代码+DesktopTurnActions：处理取消异常；如果没有这行，用户看不到失败原因。
      dispatchThread({ type: "message_added", message: { id: `local_cancel_error_${Date.now()}`, role: "system", text: `取消本轮失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopTurnActions：把取消错误写入线程；如果没有这行，错误只会留在控制台。
    } // 新增代码+DesktopTurnActions：取消异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopTurnActions：函数段结束，handleCancelTurn 到此结束；如果没有这个边界，用户不容易看出取消流程范围。

  async function handleRetryTurn(turnId: string): Promise<void> { // 新增代码+DesktopTurnActions：函数段开始，处理 GUI 重试按钮；如果没有这段，消息卡重试按钮不会调用后端 retry。
    if (turnId.length === 0) { // 新增代码+DesktopTurnActions：防御空 turnId；如果没有这行，错误按钮状态可能发出无意义请求。
      return; // 新增代码+DesktopTurnActions：空 turnId 直接退出；如果没有这行，后续会打到错误 endpoint。
    } // 新增代码+DesktopTurnActions：空 turnId 判断结束；如果没有这行，条件块语法不完整。
    if (guiClient === null) { // 新增代码+DesktopTurnActions：处理 bridge 未配置；如果没有这行，重试按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_retry_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法重试本轮。", status: "failed" } }); // 新增代码+DesktopTurnActions：把配置缺失显示给用户；如果没有这行，点击重试会静默失败。
      return; // 新增代码+DesktopTurnActions：没有 client 时停止重试；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopTurnActions：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopTurnActions：捕获重试请求失败；如果没有这行，busy/404 会变成未捕获 Promise。
      const response = await guiClient.retryTurn(turnId); // 新增代码+DesktopTurnActions：调用后端 retry endpoint；如果没有这行，GUI 重试按钮只有装饰效果。
      dispatchThread({ type: "message_added", message: { id: `assistant_${response.turn_id}`, role: "assistant", text: response.answer, turnId: response.turn_id, status: response.status } }); // 新增代码+DesktopTurnActions：为新 turn 创建助手占位消息；如果没有这行，重试后的运行状态没有消息容器。
      dispatchThread({ type: "turn_started", turnId: response.turn_id, status: response.status }); // 新增代码+DesktopTurnActions：记录新 active turn；如果没有这行，composer 和后续取消不知道当前 turn。
      await refreshEventsAfter(response.events_after_sequence); // 新增代码+DesktopFastEventReplay：重试后立刻补拉生命周期事件；如果没有这行代码，快速完成或失败的重试可能只更新右栏不更新消息正文。
      await refreshSidebarSessions(); // 新增代码+DesktopGUISessionSearch：重试成功后刷新侧栏；如果没有这行，最近会话状态和更新时间可能落后。
    } catch (error) { // 新增代码+DesktopTurnActions：处理重试异常；如果没有这行，用户看不到失败原因。
      dispatchThread({ type: "message_added", message: { id: `local_retry_error_${Date.now()}`, role: "system", text: `重试本轮失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopTurnActions：把重试错误写入线程；如果没有这行，错误只会留在控制台。
    } // 新增代码+DesktopTurnActions：重试异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopTurnActions：函数段结束，handleRetryTurn 到此结束；如果没有这个边界，用户不容易看出重试流程范围。

  async function handleSubmit(prompt: string): Promise<void> { // 修改代码+DesktopToolTimeline：函数段开始，处理用户提交 prompt；如果没有这段，Composer 输入不会进入线程或后端。
    const userMessageId = `local_user_${Date.now()}`; // 修改代码+DesktopToolTimeline：生成本地用户消息 id；如果没有这行，React 列表 key 不稳定。
    dispatchThread({ type: "message_added", message: { id: userMessageId, role: "user", text: prompt, status: "completed" } }); // 修改代码+DesktopToolTimeline：立即显示用户消息；如果没有这行，用户点击发送后界面没有反馈。
    if (guiClient === null) { // 修改代码+DesktopToolTimeline：处理 bridge 未配置；如果没有这行，用户只会看到网络失败。
      dispatchThread({ type: "message_added", message: { id: `local_system_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，请通过桌面启动脚本打开应用。", status: "failed" } }); // 修改代码+DesktopToolTimeline：显示配置缺失提示；如果没有这行，用户不知道应该启动后端 bridge。
      return; // 修改代码+DesktopToolTimeline：配置缺失时停止提交；如果没有这行，会继续访问 null client。
    } // 修改代码+DesktopToolTimeline：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 修改代码+DesktopToolTimeline：捕获提交失败；如果没有这行，busy 或断线会变成未捕获错误。
      const response = await guiClient.sendMessage(prompt, activeConversationId); // 修改代码+DesktopGUISessions：向当前会话提交 prompt；如果没有这行，用户选中历史会话后新消息仍会错误写入 default。
      dispatchThread({ type: "message_added", message: { id: `assistant_${response.turn_id}`, role: "assistant", text: response.answer, turnId: response.turn_id, status: response.status } }); // 修改代码+DesktopToolTimeline：显示助手占位消息；如果没有这行，运行中状态没有消息容器。
      dispatchThread({ type: "turn_started", turnId: response.turn_id, status: response.status }); // 修改代码+DesktopToolTimeline：记录 active turn；如果没有这行，composer 无法禁用重复发送。
      await refreshEventsAfter(response.events_after_sequence); // 新增代码+DesktopFastEventReplay：发送后立刻补拉生命周期事件；如果没有这行代码，快速 failed 事件可能早于助手占位消息而丢失错误正文。
      await refreshSidebarSessions(); // 新增代码+DesktopGUISessionSearch：提交成功后刷新侧栏；如果没有这行，新会话不会及时进入最近对话。
    } catch (error) { // 修改代码+DesktopToolTimeline：处理提交异常；如果没有这行，busy/断线会变成未捕获错误。
      dispatchThread({ type: "message_added", message: { id: `local_error_${Date.now()}`, role: "system", text: `GUI bridge 提交失败：${String(error)}`, status: "failed" } }); // 修改代码+DesktopToolTimeline：把错误显示到线程；如果没有这行，用户看不到失败原因。
      dispatchThread({ type: "turn_finished", status: "failed", errorMessage: String(error) }); // 修改代码+DesktopToolTimeline：退出运行态；如果没有这行，发送按钮可能一直禁用。
    } // 修改代码+DesktopToolTimeline：异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 修改代码+DesktopToolTimeline：函数段结束，handleSubmit 到此结束；如果没有这个边界，初学者不容易看出提交流程范围。

  async function handleUnknownRouteProbe(): Promise<void> { // 新增代码+DesktopUnknownRouteProbe：函数段开始，执行诊断页 unknown route 可见验收；如果没有这段，404 结构化错误只能靠外部命令验证。
    if (guiClient === null) { // 新增代码+DesktopUnknownRouteProbe：没有 client 时不能发探针；如果没有这一行，按钮会访问空对象。
      dispatchThread({ type: "message_added", message: { id: `local_unknown_route_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法执行未知路由检查。", status: "failed" } }); // 新增代码+DesktopUnknownRouteProbe：把配置缺失显示到主线程；如果没有这一行，用户不知道按钮为什么无效。
      return; // 新增代码+DesktopUnknownRouteProbe：缺少 client 时结束；如果没有这一行，后续会继续访问 null client。
    } // 新增代码+DesktopUnknownRouteProbe：client 缺失分支结束；如果没有这一行，条件块语法不完整。
    try { // 新增代码+DesktopUnknownRouteProbe：捕获预期的结构化 404；如果没有这一行，Promise 错误会进入控制台。
      await guiClient.probeUnknownRoute(); // 新增代码+DesktopUnknownRouteProbe：请求不存在的 V2 路由；如果没有这一行，诊断按钮没有实际验收动作。
      dispatchThread({ type: "message_added", message: { id: `local_unknown_route_unexpected_success_${Date.now()}`, role: "system", text: "未知 GUI 路由检查异常成功，请检查 bridge 路由表。", status: "failed" } }); // 新增代码+DesktopUnknownRouteProbe：处理异常成功；如果没有这一行，路由表误放行会静默。
    } catch (error) { // 新增代码+DesktopUnknownRouteProbe：处理结构化错误；如果没有这一行，404 不会进入可见线程。
      dispatchThread({ type: "message_added", message: { id: `local_unknown_route_error_${Date.now()}`, role: "system", text: `未知 GUI 路由检查：${String(error)}`, status: "failed" } }); // 新增代码+DesktopUnknownRouteProbe：把 unknown route 错误显示到主对话；如果没有这一行，矩阵无法截图验收。
    } // 新增代码+DesktopUnknownRouteProbe：异常处理结束；如果没有这一行，try/catch 语法不完整。
  } // 新增代码+DesktopUnknownRouteProbe：函数段结束，handleUnknownRouteProbe 到此结束；如果没有这个边界说明，用户不容易看出诊断探针范围。

  const activeSidebarSession = sidebarSessions.find((session) => session.id === activeConversationId); // 新增代码+DesktopGUISessionSearch：查找当前会话侧栏条目；如果没有这行，顶部标题无法显示真实会话名。
  const activeThreadTitle = activeSidebarSession?.title ?? "快速对话"; // 新增代码+DesktopGUISessionSearch：生成当前对话标题；如果没有这行，新会话和历史会话标题会混在一起。
  const activeThreadSubtitle = activeSidebarSession?.subtitle ?? "OpenHarness Desktop Shell"; // 新增代码+DesktopGUISessionSearch：生成当前对话副标题；如果没有这行，主区缺少最近摘要或默认上下文。

  return ( // 修改代码+DesktopToolTimeline：返回主界面结构；如果没有这行，组件不会输出任何 UI。
    <main className="app-shell"> {/* 修改代码+DesktopToolTimeline：定义三栏窗口网格容器；如果没有这行，侧栏、线程区和状态区无法稳定并排。 */}
      <Sidebar projectName={projectName} sessions={sidebarSessions} activeSessionId={activeConversationId} archivedCount={archivedCount} onNewConversation={handleNewConversation} onOpenSearch={handleOpenSearch} onOpenArchived={() => { void handleOpenArchived(); }} onSelectSession={(sessionId) => { void handleSelectSession(sessionId); }} /> {/* 修改代码+DesktopGUISessionSearch：渲染带项目、会话、active、搜索、归档和新对话入口的侧栏；如果没有这行，Sidebar 拿不到真实操作回调。 */}
      <section className="thread-panel" aria-label="当前对话"> {/* 修改代码+DesktopToolTimeline：定义当前对话主区域；如果没有这行，读屏器和布局都缺少对话容器。 */}
        <header className="thread-header"> {/* 修改代码+DesktopToolTimeline：定义顶部会话栏；如果没有这行，用户无法确认当前会话标题。 */}
          <div className="thread-title">{activeThreadTitle}</div> {/* 修改代码+DesktopGUISessionSearch：显示当前会话名；如果没有这行，主面板上下文不清楚。 */}
          <div className="thread-subtitle">{activeThreadSubtitle}</div> {/* 修改代码+DesktopGUISessionSearch：显示当前会话摘要或默认桌面壳语境；如果没有这行，用户难以区分 CLI 和桌面壳。 */}
        </header> {/* 修改代码+DesktopToolTimeline：顶部会话栏结束；如果没有这行，JSX 结构不完整。 */}
        <div className="thread-content"> {/* 新增代码+DesktopGUIPermissions：包裹权限提示和消息视图；如果没有这行，banner 会破坏主面板三段布局。 */}
          {bridgeIssue.length > 0 ? <div className="bridge-offline-banner" role="status">{bridgeIssue}</div> : null} {/* 新增代码+DesktopBridgeOfflineBanner：显示 bridge 离线横幅；如果没有这一行，离线状态只会藏在 console。 */}
          {permissionDialogOpen && permissionRequest ? <PermissionBanner title="等待权限确认" toolName={permissionRequest.toolName} actionSummary={permissionRequest.actionSummary} riskSummary={permissionRequest.riskSummary} decisionPending={permissionDecisionPending} /> : null} {/* 修改代码+DesktopGUIPermissionsV2：渲染 V2 权限等待提示条；如果没有这行，用户可能只看到消息停在 needs_permission。 */}
          <ThreadView messages={threadState.messages.length > 0 ? threadState.messages : undefined} events={statusState.events} onCancelTurn={(turnId) => { void handleCancelTurn(turnId); }} onRetryTurn={(turnId) => { void handleRetryTurn(turnId); }} /> {/* 修改代码+DesktopTurnActions：把消息、事件、取消和重试回调交给主线程视图；如果没有这行，消息卡按钮无法触发生命周期端点。 */}
        </div> {/* 新增代码+DesktopGUIPermissions：权限提示和消息视图包裹层结束；如果没有这行，JSX 结构不完整。 */}
        <Composer isRunning={threadState.isRunning} activeTurnId={threadState.activeTurnId} onCancelActiveTurn={(turnId) => { void handleCancelTurn(turnId); }} onSubmit={(prompt) => { void handleSubmit(prompt); }} /> {/* 修改代码+DesktopComposerCancel：把运行态、活动 turn、取消回调和提交回调交给 composer；如果没有这行代码，底部输入区无法稳定触发发送或取消生命周期。 */}
      </section> {/* 修改代码+DesktopToolTimeline：当前对话主区域结束；如果没有这行，JSX 结构不完整。 */}
      <StatusInspector events={statusState.events} browserProviderStatus={browserProviderStatus} runtimePanels={runtimePanels} harnessPayload={harnessPayload} bridgeBaseUrl={bridgeConfig?.baseUrl ?? ""} healthPayload={healthPayload} diagnosticsPayload={diagnosticsPayload} onProbeUnknownRoute={() => { void handleUnknownRouteProbe(); }} onPauseHarness={() => { void handleHarnessControl("pause"); }} onResumeHarness={() => { void handleHarnessControl("resume"); }} harnessControlPending={harnessControlPending} /> {/* 修改代码+DesktopUnknownRouteProbe：把 unknown route 探针交给右侧诊断页；如果没有这行，诊断按钮无法把结构化 404 写入主线程。 */}
      <SearchPanel open={searchOpen} query={searchQuery} results={searchResults} isSearching={searchLoading} onClose={() => setSearchOpen(false)} onQueryChange={setSearchQuery} onSelectSession={(sessionId) => { void handleSelectSession(sessionId); }} /> {/* 新增代码+DesktopGUISessionSearch：渲染 V2 会话搜索面板；如果没有这行，搜索入口无法显示结果并恢复会话。 */}
      <PermissionDialog open={permissionDialogOpen} requestId={permissionRequest?.requestId ?? ""} toolName={permissionRequest?.toolName ?? ""} appName={permissionRequest?.appName ?? ""} actionSummary={permissionRequest?.actionSummary ?? ""} reason={permissionRequest?.reason ?? ""} riskSummary={permissionRequest?.riskSummary ?? ""} decisionPending={permissionDecisionPending} onApprove={() => { void handlePermissionDecision("approve"); }} onDeny={() => { void handlePermissionDecision("deny"); }} /> {/* 修改代码+DesktopGUIPermissionsV2：渲染 V2 权限确认弹窗并提交后端决策；如果没有这行，用户无法在 GUI 中允许或拒绝。 */}
    </main> // 修改代码+DesktopToolTimeline：全窗口网格容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopToolTimeline：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopToolTimeline：函数段结束，AppShell 到此结束；如果没有这个边界，用户不容易看出主壳组合范围。
