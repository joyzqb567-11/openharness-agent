import { useEffect, useMemo, useReducer, useState } from "react"; // 修改代码+DesktopGUISessions：引入 React 状态、副作用和本地 state 工具；如果没有这行，主壳无法保存项目名、会话列表和轮询状态。
import { createGuiClient } from "../api/guiClient"; // 修改代码+DesktopToolTimeline：引入 GUI bridge 客户端工厂；如果没有这行，前端无法向本地 bridge 发送消息或读取事件。
import { appendStatusEvents, initialStatusState, normalizeStatusEvent, type StatusEvent } from "../state/statusStore"; // 新增代码+DesktopToolTimeline：引入状态时间线数据工具；如果没有这行，右侧面板会缺少去重后的事件来源。
import { initialThreadState, threadReducer, type ThreadMessage, type ThreadRole, type TurnStatus } from "../state/threadStore"; // 修改代码+DesktopGUISessions：引入对话 reducer 和消息类型；如果没有这行，恢复消息无法被安全转换。
import { Composer } from "./Composer"; // 修改代码+DesktopToolTimeline：引入底部输入组件；如果没有这行，用户没有输入 prompt 的入口。
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

function statusFromEventType(eventType: string): TurnStatus | null { // 新增代码+DesktopToolTimeline：函数段开始，把 bridge 事件类型翻译成 UI turn 状态；如果没有这段，事件只能显示在右栏，不能更新消息状态。
  const statusMap: Record<string, TurnStatus> = { // 新增代码+DesktopToolTimeline：建立事件到状态的映射表；如果没有这行，每个事件都要写重复判断。
    gui_turn_queued: "queued", // 新增代码+DesktopToolTimeline：把排队事件映射为 queued；如果没有这行，刚提交的消息无法显示排队状态。
    gui_turn_started: "running", // 新增代码+DesktopToolTimeline：把开始事件映射为 running；如果没有这行，用户看不到任务已经开始运行。
    gui_turn_needs_permission: "needs_permission", // 新增代码+DesktopToolTimeline：把权限事件映射为 needs_permission；如果没有这行，后续权限面板难以复用同一状态机。
    gui_turn_cancel_requested: "cancelling", // 新增代码+DesktopToolTimeline：把取消请求映射为 cancelling；如果没有这行，点击取消后 UI 会缺少中间反馈。
    gui_turn_completed: "completed", // 新增代码+DesktopToolTimeline：把完成事件映射为 completed；如果没有这行，助手消息不会进入完成态。
    gui_turn_failed: "failed", // 新增代码+DesktopToolTimeline：把失败事件映射为 failed；如果没有这行，错误不会同步到消息卡片。
    gui_turn_cancelled: "cancelled", // 新增代码+DesktopToolTimeline：把已取消事件映射为 cancelled；如果没有这行，取消结果不会显示为终态。
  }; // 新增代码+DesktopToolTimeline：映射表结束；如果没有这行，对象语法不完整。
  return statusMap[eventType] ?? null; // 新增代码+DesktopToolTimeline：返回匹配状态或空值；如果没有这行，调用方无法知道事件是否需要同步到消息。
} // 新增代码+DesktopToolTimeline：函数段结束，statusFromEventType 到此结束；如果没有这个边界，初学者不容易看出事件翻译范围。

function textFromEvent(event: StatusEvent): string | undefined { // 新增代码+DesktopToolTimeline：函数段开始，从事件 payload 中提取可显示文本；如果没有这段，完成和失败事件无法把最终内容写回消息。
  if (typeof event.payload.answer === "string") { // 新增代码+DesktopToolTimeline：优先读取 answer 字段；如果没有这行，成功回答不会更新到助手消息正文。
    return event.payload.answer; // 新增代码+DesktopToolTimeline：返回成功回答；如果没有这行，消息会一直停在等待占位文本。
  } // 新增代码+DesktopToolTimeline：answer 分支结束；如果没有这行，条件块语法不完整。
  if (typeof event.payload.error === "string") { // 新增代码+DesktopToolTimeline：读取 error 字段；如果没有这行，失败原因不会显示在对话里。
    return event.payload.error; // 新增代码+DesktopToolTimeline：返回失败文本；如果没有这行，用户看不到任务失败原因。
  } // 新增代码+DesktopToolTimeline：error 分支结束；如果没有这行，条件块语法不完整。
  return undefined; // 新增代码+DesktopToolTimeline：没有可显示文本时返回 undefined；如果没有这行，调用方可能误把空字符串写回消息。
} // 新增代码+DesktopToolTimeline：函数段结束，textFromEvent 到此结束；如果没有这个边界，初学者不容易看出文本提取范围。

function errorFromEvent(event: StatusEvent): string | null { // 新增代码+DesktopToolTimeline：函数段开始，从事件中提取错误信息；如果没有这段，thread reducer 的 errorMessage 字段无法统一更新。
  return typeof event.payload.error === "string" ? event.payload.error : null; // 新增代码+DesktopToolTimeline：返回错误或空值；如果没有这行，失败状态没有可读原因。
} // 新增代码+DesktopToolTimeline：函数段结束，errorFromEvent 到此结束；如果没有这个边界，初学者不容易看出错误提取范围。

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
    const subtitle = typeof session.status === "string" ? session.status : undefined; // 新增代码+DesktopGUISessions：读取可选状态副标题；如果没有这行，后续状态摘要没有展示入口。
    return { id, title: title || id || "未命名会话", subtitle }; // 新增代码+DesktopGUISessions：返回规范化条目；如果没有这行，map 回调没有稳定输出。
  }).filter((session) => session.id.length > 0); // 新增代码+DesktopGUISessions：过滤没有 id 的坏数据；如果没有这行，点击无效会话会调用空 session。
} // 新增代码+DesktopGUISessions：函数段结束，normalizeSidebarSessions 到此结束；如果没有这个边界，初学者不容易看出会话适配范围。

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

export function AppShell(): JSX.Element { // 修改代码+DesktopToolTimeline：函数段开始，组织桌面 GUI 主壳；如果没有这段，各组件无法组合成 Codex 风格窗口。
  const [threadState, dispatchThread] = useReducer(threadReducer, initialThreadState); // 修改代码+DesktopToolTimeline：创建对话线程状态；如果没有这行，用户消息和助手消息无法进入 UI。
  const [statusState, dispatchStatus] = useReducer(appendStatusEvents, initialStatusState); // 新增代码+DesktopToolTimeline：创建状态时间线状态；如果没有这行，轮询事件无法去重和保存游标。
  const [projectName, setProjectName] = useState("OpenHarness-main"); // 新增代码+DesktopGUISessions：保存侧栏当前项目名；如果没有这行，侧栏只能显示硬编码名称，换工作区后会误导用户。
  const [sidebarSessions, setSidebarSessions] = useState<SidebarSession[]>([]); // 新增代码+DesktopGUISessions：保存最近会话列表；如果没有这行，后端 session 数据没有 UI 容器。
  const [activeConversationId, setActiveConversationId] = useState("default"); // 新增代码+DesktopGUISessions：保存当前提交要写入的会话 id；如果没有这行，点击历史会话后新 prompt 仍会写回 default 会话。
  const [browserProviderStatus, setBrowserProviderStatus] = useState<Record<string, unknown>>({}); // 新增代码+DesktopGUIBrowserPanel：保存浏览器 provider 状态；如果没有这行，右侧 BrowserPanel 没有真实后端数据。
  const bridgeConfig = window.openHarnessDesktop?.bridge; // 修改代码+DesktopToolTimeline：读取 preload 注入的 bridge 配置；如果没有这行，GUI 不知道后端地址和 token。
  const guiClient = useMemo(() => { // 修改代码+DesktopToolTimeline：缓存 GUI client；如果没有这段，每次渲染都会创建新 client。
    if (!bridgeConfig?.baseUrl || !bridgeConfig.token) { // 修改代码+DesktopToolTimeline：检查 bridge 配置是否完整；如果没有这行，空 token 请求会反复失败。
      return null; // 修改代码+DesktopToolTimeline：配置缺失时不创建 client；如果没有这行，后续调用可能访问无效 client。
    } // 修改代码+DesktopToolTimeline：配置检查结束；如果没有这行，条件块语法不完整。
    return createGuiClient(bridgeConfig.baseUrl, bridgeConfig.token); // 修改代码+DesktopToolTimeline：创建带 token 的 client；如果没有这行，composer 和轮询无法访问 bridge。
  }, [bridgeConfig?.baseUrl, bridgeConfig?.token]); // 修改代码+DesktopToolTimeline：按 bridge 配置缓存 client；如果没有这行，useMemo 依赖不完整。

  useEffect(() => { // 新增代码+DesktopGUISessions：副作用段开始，加载项目名和最近会话；如果没有这段，侧栏无法从真实 bridge 获取项目上下文。
    if (guiClient === null) { // 新增代码+DesktopGUISessions：没有 client 时跳过加载；如果没有这行，缺少 baseUrl/token 会持续请求失败。
      return undefined; // 新增代码+DesktopGUISessions：返回空清理函数；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+DesktopGUISessions：client 检查结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 修改代码+DesktopGUISessions：把本次副作用使用的 client 固定到局部常量；如果没有这行，TypeScript 会担心异步加载时 client 变成 null。
    let disposed = false; // 新增代码+DesktopGUISessions：记录组件是否已经卸载；如果没有这行，异步加载返回后可能更新已卸载组件。
    async function loadSidebarData(): Promise<void> { // 新增代码+DesktopGUISessions：函数段开始，集中读取 bootstrap 和 sessions；如果没有这段，侧栏数据加载逻辑会散落到渲染层。
      try { // 新增代码+DesktopGUISessions：捕获侧栏加载失败；如果没有这行，bridge 暂时不可用会让界面副作用抛错。
        const [bootstrapPayload, sessionsPayload, browserProvidersPayload] = await Promise.all([activeClient.bootstrap(), activeClient.sessions(), activeClient.browserProviders()]); // 修改代码+DesktopGUIBrowserPanel：并行读取工作区、会话和浏览器状态；如果没有这行，右侧浏览器面板拿不到 provider_status。
        if (disposed) { // 新增代码+DesktopGUISessions：检查组件是否已卸载；如果没有这行，迟到响应可能继续 setState。
          return; // 新增代码+DesktopGUISessions：卸载后停止处理；如果没有这行，React 可能提示卸载组件被更新。
        } // 新增代码+DesktopGUISessions：卸载检查结束；如果没有这行，条件块语法不完整。
        setProjectName(projectNameFromWorkspace(bootstrapPayload.workspace)); // 新增代码+DesktopGUISessions：把 workspace 转成侧栏项目名；如果没有这行，项目身份不会显示真实目录。
        setSidebarSessions(normalizeSidebarSessions(sessionsPayload.sessions)); // 新增代码+DesktopGUISessions：把后端 sessions 转成可点击条目；如果没有这行，最近会话列表会一直为空。
        setBrowserProviderStatus(browserProvidersPayload.provider_status); // 新增代码+DesktopGUIBrowserPanel：保存浏览器 provider 状态；如果没有这行，BrowserPanel 会一直停留在空状态。
      } catch (error) { // 新增代码+DesktopGUISessions：处理加载异常；如果没有这行，侧栏数据失败会变成未捕获错误。
        console.warn("GUI bridge sidebar load failed", error); // 新增代码+DesktopGUISessions：把失败留给开发者诊断；如果没有这行，侧栏为空时难以判断原因。
      } // 新增代码+DesktopGUISessions：异常处理结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+DesktopGUISessions：函数段结束，loadSidebarData 到此结束；如果没有这个边界，初学者不容易看出侧栏加载范围。
    void loadSidebarData(); // 新增代码+DesktopGUISessions：挂载后立即加载侧栏数据；如果没有这行，定义好的函数不会执行。
    return () => { // 新增代码+DesktopGUISessions：定义副作用清理逻辑；如果没有这行，卸载后无法标记异步任务失效。
      disposed = true; // 新增代码+DesktopGUISessions：标记异步任务已失效；如果没有这行，迟到响应可能继续更新状态。
    }; // 新增代码+DesktopGUISessions：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient]); // 新增代码+DesktopGUISessions：当 client 变化时重新加载侧栏数据；如果没有这行，换 bridge 配置后仍显示旧项目。

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
        if (normalizedEvents.length === 0) { // 新增代码+DesktopToolTimeline：没有新事件时直接返回；如果没有这行，空数组也会触发不必要渲染。
          return; // 新增代码+DesktopToolTimeline：结束空轮询；如果没有这行，后续逻辑会做无意义工作。
        } // 新增代码+DesktopToolTimeline：空事件判断结束；如果没有这行，条件块语法不完整。
        dispatchStatus(normalizedEvents); // 新增代码+DesktopToolTimeline：把新事件写入状态时间线；如果没有这行，右侧面板不会刷新。
        for (const event of normalizedEvents) { // 新增代码+DesktopToolTimeline：逐条同步事件到对话状态；如果没有这行，消息卡片无法跟随生命周期变化。
          const status = statusFromEventType(event.event_type); // 新增代码+DesktopToolTimeline：把事件类型翻译为 turn 状态；如果没有这行，reducer 不知道要更新成什么状态。
          if (status === null || event.turn_id.length === 0) { // 新增代码+DesktopToolTimeline：跳过非 turn 事件；如果没有这行，系统事件可能错误修改消息状态。
            continue; // 新增代码+DesktopToolTimeline：继续处理下一条事件；如果没有这行，无关事件会落入更新逻辑。
          } // 新增代码+DesktopToolTimeline：跳过判断结束；如果没有这行，条件块语法不完整。
          dispatchThread({ type: "turn_status_changed", turnId: event.turn_id, status, text: textFromEvent(event), errorMessage: errorFromEvent(event) }); // 新增代码+DesktopToolTimeline：同步消息状态和最终文本；如果没有这行，完成/失败/取消不会反映到主对话。
        } // 新增代码+DesktopToolTimeline：事件同步循环结束；如果没有这行，for 循环语法不完整。
      } catch (error) { // 新增代码+DesktopToolTimeline：处理轮询异常；如果没有这行，bridge 暂时不可用会让副作用抛出未捕获错误。
        console.warn("GUI bridge event polling failed", error); // 新增代码+DesktopToolTimeline：把失败留给开发者诊断；如果没有这行，轮询失败会静默到难以排查。
      } // 新增代码+DesktopToolTimeline：异常处理结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+DesktopToolTimeline：函数段结束，pollEvents 到此结束；如果没有这个边界，初学者不容易看出轮询范围。
    void pollEvents(); // 新增代码+DesktopToolTimeline：挂载后立即轮询一次；如果没有这行，用户要等到下一个 interval 才看到事件。
    const intervalId = window.setInterval(() => { void pollEvents(); }, 1500); // 新增代码+DesktopToolTimeline：每 1.5 秒轮询一次；如果没有这行，长任务进度不会持续刷新。
    return () => { // 新增代码+DesktopToolTimeline：定义副作用清理逻辑；如果没有这行，组件卸载时轮询计时器会泄漏。
      disposed = true; // 新增代码+DesktopToolTimeline：标记异步任务已失效；如果没有这行，迟到响应可能继续更新状态。
      window.clearInterval(intervalId); // 新增代码+DesktopToolTimeline：清理轮询计时器；如果没有这行，窗口关闭后仍可能保留定时任务。
    }; // 新增代码+DesktopToolTimeline：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient, statusState.lastSequence]); // 新增代码+DesktopToolTimeline：按 client 和事件游标重建轮询；如果没有这行，轮询会使用过期游标。

  async function handleSelectSession(sessionId: string): Promise<void> { // 新增代码+DesktopGUISessions：函数段开始，处理侧栏会话点击；如果没有这段，最近会话只是静态列表不能恢复上下文。
    setActiveConversationId(sessionId); // 新增代码+DesktopGUISessions：记录当前会话 id；如果没有这行，后续新 prompt 不会发送到用户选中的会话。
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
    } catch (error) { // 修改代码+DesktopToolTimeline：处理提交异常；如果没有这行，busy/断线会变成未捕获错误。
      dispatchThread({ type: "message_added", message: { id: `local_error_${Date.now()}`, role: "system", text: `GUI bridge 提交失败：${String(error)}`, status: "failed" } }); // 修改代码+DesktopToolTimeline：把错误显示到线程；如果没有这行，用户看不到失败原因。
      dispatchThread({ type: "turn_finished", status: "failed", errorMessage: String(error) }); // 修改代码+DesktopToolTimeline：退出运行态；如果没有这行，发送按钮可能一直禁用。
    } // 修改代码+DesktopToolTimeline：异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 修改代码+DesktopToolTimeline：函数段结束，handleSubmit 到此结束；如果没有这个边界，初学者不容易看出提交流程范围。

  return ( // 修改代码+DesktopToolTimeline：返回主界面结构；如果没有这行，组件不会输出任何 UI。
    <main className="app-shell"> {/* 修改代码+DesktopToolTimeline：定义三栏窗口网格容器；如果没有这行，侧栏、线程区和状态区无法稳定并排。 */}
      <Sidebar projectName={projectName} sessions={sidebarSessions} onSelectSession={(sessionId) => { void handleSelectSession(sessionId); }} /> {/* 修改代码+DesktopGUISessions：渲染带项目名和最近会话的侧栏；如果没有这行，Sidebar 拿不到真实数据和恢复回调。 */}
      <section className="thread-panel" aria-label="当前对话"> {/* 修改代码+DesktopToolTimeline：定义当前对话主区域；如果没有这行，读屏器和布局都缺少对话容器。 */}
        <header className="thread-header"> {/* 修改代码+DesktopToolTimeline：定义顶部会话栏；如果没有这行，用户无法确认当前会话标题。 */}
          <div className="thread-title">快速对话</div> {/* 修改代码+DesktopToolTimeline：显示当前会话名；如果没有这行，主面板上下文不清楚。 */}
          <div className="thread-subtitle">OpenHarness Desktop Shell</div> {/* 修改代码+DesktopToolTimeline：显示当前桌面壳语境；如果没有这行，用户难以区分 CLI 和桌面壳。 */}
        </header> {/* 修改代码+DesktopToolTimeline：顶部会话栏结束；如果没有这行，JSX 结构不完整。 */}
        <ThreadView messages={threadState.messages.length > 0 ? threadState.messages : undefined} events={statusState.events} /> {/* 修改代码+DesktopToolTimeline：把消息和事件传给主线程视图；如果没有这行，工具卡片不会出现在对话流里。 */}
        <Composer isRunning={threadState.isRunning} onSubmit={(prompt) => { void handleSubmit(prompt); }} /> {/* 修改代码+DesktopToolTimeline：把运行态和提交回调交给 composer；如果没有这行，输入区无法触发生命周期。 */}
      </section> {/* 修改代码+DesktopToolTimeline：当前对话主区域结束；如果没有这行，JSX 结构不完整。 */}
      <StatusInspector events={statusState.events} browserProviderStatus={browserProviderStatus} /> {/* 修改代码+DesktopGUIBrowserPanel：渲染右侧状态时间线和浏览器 provider 面板；如果没有这行，用户看不到事件序列、运行状态和浏览器轨道健康。 */}
    </main> // 修改代码+DesktopToolTimeline：全窗口网格容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopToolTimeline：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopToolTimeline：函数段结束，AppShell 到此结束；如果没有这个边界，用户不容易看出主壳组合范围。
