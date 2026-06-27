import { useEffect, useMemo, useReducer, useState } from "react"; // 修改代码+DesktopGUISessions：引入 React 状态、副作用和本地 state 工具；如果没有这行，主壳无法保存项目名、会话列表和轮询状态。
import { createGuiClient, type GuiBrowserActionPayload, type GuiComputerUseActionPayload, type GuiHarnessControlPayload } from "../api/guiClient"; // 修改代码+DesktopGUIBrowserWorkbench：引入 GUI bridge 客户端工厂、Browser、Computer Use 和 Harness 控制响应类型；如果没有这行，前端无法类型化真实按钮结果。
import { reduceGuiEventToThreadActions } from "../state/eventReducer"; // 新增代码+DesktopThreadStreaming：引入 V2 事件到线程动作的纯转换器；如果没有这行，AppShell 会继续手写旧事件同步逻辑。
import { appendStatusEvents, initialStatusState, latestPermissionEvent, normalizeStatusEvent, type StatusEvent } from "../state/statusStore"; // 修改代码+DesktopThreadStreaming：引入状态时间线、权限事件和事件规范化工具；如果没有这行，轮询数据无法进入 UI。
import { buildProviderSettingsViewModel, providerRowsForDisplay, type ProviderRowView, type ProviderSettingsViewModel } from "../state/providerSettingsStore"; // 新增代码+ComposerRouteControls：引入 provider catalog view model；如果没有这行，底部模型下拉只能依赖硬编码状态。
import { initialThreadState, threadReducer, type ThreadMessage, type ThreadRole, type TurnStatus } from "../state/threadStore"; // 修改代码+DesktopGUISessions：引入对话 reducer 和消息类型；如果没有这行，恢复消息无法被安全转换。
import { Composer, type ComposerModelOption, type ComposerPermissionMode, type ComposerReasoningEffort, type ComposerSubmitPayload } from "./Composer"; // 修改代码+ComposerRouteControls：引入底部输入组件、模型选项和结构化提交类型；如果没有这行，用户没有输入 prompt 的入口且无法类型化模型路由字段。
import { PermissionBanner } from "./PermissionBanner"; // 新增代码+DesktopGUIPermissions：引入权限提示条；如果没有这行，用户可能错过待处理权限请求。
import { PermissionDialog } from "./PermissionDialog"; // 新增代码+DesktopGUIPermissions：引入权限确认弹窗；如果没有这行，用户无法在 GUI 中允许或拒绝权限。
import { SearchPanel, type SearchPanelResult } from "./SearchPanel"; // 新增代码+DesktopGUISessionSearch：引入会话搜索面板和结果类型；如果没有这行，搜索入口无法渲染真实 GUI。
import { Sidebar, type SidebarSession } from "./Sidebar"; // 修改代码+DesktopGUISessions：引入左侧导航组件和会话类型；如果没有这行，项目名和 session 列表无法传入侧栏。
import { latestModelCallStatus } from "./ModelCallStatus"; // 新增代码+RealModelObservability：引入最新模型调用状态选择器；如果没有这一行，底部输入区无法跟随后端真实调用阶段。
import { StatusInspector } from "./StatusInspector"; // 新增代码+DesktopToolTimeline：引入右侧状态面板；如果没有这行，用户看不到 bridge 事件时间线。
import { ThreadView } from "./ThreadView"; // 修改代码+DesktopToolTimeline：引入主对话组件；如果没有这行，消息和工具卡片没有渲染位置。
import { SettingsDialog } from "./settings/SettingsDialog"; // 新增代码+ProviderSettingsShell：导入桌面设置弹窗；如果没有这行，AppShell 无法渲染左下角设置入口对应的成熟设置界面。

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

export type ComposerRouteState = { selectedProviderId: string; selectedModelId: string; reasoningEffort: ComposerReasoningEffort; permissionMode: ComposerPermissionMode }; // 新增代码+ComposerRouteControls：定义底部模型路由状态；如果没有这行，provider/model/权限/推理会继续分散成难同步的多个 state。

const INITIAL_COMPOSER_ROUTE: ComposerRouteState = { selectedProviderId: "", selectedModelId: "", reasoningEffort: "ultra", permissionMode: "full_access" }; // 新增代码+ComposerRouteControls：定义底部路由默认值；如果没有这行，断开 provider 后无法稳定回到“选择模型”。

function modelIsComposerSelectable(model: ProviderRowView["models"][number]): boolean { // 新增代码+ComposerRouteControls：函数段开始，判断模型是否能成为提交目标；如果没有这段，账号不支持的模型可能被自动选中并导致慢失败。
  return model.visible && model.state !== "not_supported_for_account"; // 新增代码+ComposerRouteControls：可见且不是账号不支持才允许提交；如果没有这行，Direct SSE 会反复请求已知不可用模型。
} // 新增代码+ComposerRouteControls：函数段结束，modelIsComposerSelectable 到此结束；如果没有这行，函数语法不完整。

function visibleModelsForProvider(provider: ProviderRowView): ComposerModelOption[] { // 新增代码+ComposerRouteControls：函数段开始，把单个 provider 的可见模型转成下拉选项；如果没有这段，模型菜单会重复理解 provider store。
  if (!provider.connected) { // 新增代码+ComposerRouteControls：未连接 provider 不进入可提交菜单；如果没有这行，用户可能选择无法调用的模型。
    return []; // 新增代码+ComposerRouteControls：未连接时返回空列表；如果没有这行，后续仍可能显示不可用模型。
  } // 新增代码+ComposerRouteControls：未连接 provider 分支结束；如果没有这行，条件块语法不完整。
  return provider.models.filter((model) => model.visible).map((model) => ({ providerId: provider.id, modelId: model.id, label: `${provider.displayName} / ${model.displayName}`, disabled: model.state === "not_supported_for_account" })); // 新增代码+ComposerRouteControls：只把可见模型转成选项并禁用账号不支持模型；如果没有这行，隐藏或不支持模型会进入可提交路径。
} // 新增代码+ComposerRouteControls：函数段结束，visibleModelsForProvider 到此结束；如果没有这行，函数语法不完整。

export function composerModelOptionsFromProviderSettings(viewModel: ProviderSettingsViewModel | null): ComposerModelOption[] { // 新增代码+ComposerRouteControls：函数段开始，从 provider settings 生成底部模型选项；如果没有这段，AppShell 会手写不可测的派生逻辑。
  if (viewModel === null) { // 新增代码+ComposerRouteControls：处理 provider catalog 未加载；如果没有这行，首次渲染会访问空对象。
    return []; // 新增代码+ComposerRouteControls：未加载时不显示模型；如果没有这行，底部可能展示旧硬编码模型。
  } // 新增代码+ComposerRouteControls：未加载判断结束；如果没有这行，条件块语法不完整。
  return providerRowsForDisplay(viewModel).flatMap((provider) => visibleModelsForProvider(provider)); // 新增代码+ComposerRouteControls：按 provider 排序生成模型选项；如果没有这行，下拉顺序会和设置页不一致。
} // 新增代码+ComposerRouteControls：函数段结束，composerModelOptionsFromProviderSettings 到此结束；如果没有这行，函数语法不完整。

function firstConnectedProviderModel(viewModel: ProviderSettingsViewModel): { providerId: string; modelId: string } { // 新增代码+ComposerRouteControls：函数段开始，寻找默认连接模型；如果没有这段，OAuth 成功后底部无法自动选中可用模型。
  const preferredProvider = providerRowsForDisplay(viewModel).find((provider) => provider.connected && provider.id === viewModel.defaultProviderId); // 新增代码+ComposerRouteControls：优先找后端默认 provider；如果没有这行，用户保存的 OpenAI 默认选择会被忽略。
  const fallbackProvider = preferredProvider ?? providerRowsForDisplay(viewModel).find((provider) => provider.connected); // 新增代码+ComposerRouteControls：没有默认 provider 时选择第一个已连接 provider；如果没有这行，API key 自定义 provider 初次连接后不会自动进入菜单。
  const preferredModel = fallbackProvider?.models.find((model) => modelIsComposerSelectable(model) && model.id === viewModel.defaultModelId); // 修改代码+ComposerRouteControls：优先使用后端默认且可提交的模型；如果没有这行，已知账号不支持模型会被自动选中。
  const fallbackModel = preferredModel ?? fallbackProvider?.models.find((model) => modelIsComposerSelectable(model)); // 修改代码+ComposerRouteControls：没有默认模型时退到第一个可提交模型；如果没有这行，只有不可用模型时仍会显示可发送状态。
  return { providerId: fallbackProvider?.id ?? "", modelId: fallbackModel?.id ?? "" }; // 新增代码+ComposerRouteControls：返回安全 provider/model 组合；如果没有这行，调用方无法更新 route state。
} // 新增代码+ComposerRouteControls：函数段结束，firstConnectedProviderModel 到此结束；如果没有这行，函数语法不完整。

export function nextComposerRouteAfterProviderSettings(current: ComposerRouteState, viewModel: ProviderSettingsViewModel | null): ComposerRouteState { // 新增代码+ComposerRouteControls：函数段开始，根据 provider catalog 修正当前路由；如果没有这段，断开 OpenAI 后底部仍会显示旧 gpt 模型。
  if (viewModel === null) { // 新增代码+ComposerRouteControls：provider catalog 不可用时保持当前路由；如果没有这行，短暂加载失败会把用户选择清空。
    return current; // 新增代码+ComposerRouteControls：返回原状态；如果没有这行，调用方拿不到稳定值。
  } // 新增代码+ComposerRouteControls：catalog 空判断结束；如果没有这行，条件块语法不完整。
  const selectedProvider = providerRowsForDisplay(viewModel).find((provider) => provider.id === current.selectedProviderId); // 新增代码+ComposerRouteControls：查找当前 provider 是否仍存在；如果没有这行，无法判断断开或删除 provider。
  if (current.selectedProviderId.length > 0 && (!selectedProvider || !selectedProvider.connected)) { // 新增代码+ComposerRouteControls：识别当前 provider 已断开；如果没有这行，断开后模型不会重置为“选择模型”。
    return { ...current, selectedProviderId: "", selectedModelId: "" }; // 新增代码+ComposerRouteControls：清空 provider 和 model 但保留权限/推理；如果没有这行，提交可能继续带旧 OAuth 模型。
  } // 新增代码+ComposerRouteControls：断开清理分支结束；如果没有这行，条件块语法不完整。
  const selectedModel = selectedProvider?.models.find((model) => model.id === current.selectedModelId && modelIsComposerSelectable(model)); // 修改代码+ComposerRouteControls：查找当前模型是否仍可提交；如果没有这行，账号不支持模型可能继续进入后端。
  if (current.selectedModelId.length > 0 && selectedProvider && !selectedModel) { // 新增代码+ComposerRouteControls：识别当前模型被隐藏或删除；如果没有这行，模型可见性设置不会影响底部下拉。
    return { ...current, selectedModelId: "" }; // 新增代码+ComposerRouteControls：只清空模型选择；如果没有这行，provider 仍连接时也会误清权限/推理。
  } // 新增代码+ComposerRouteControls：模型不可见分支结束；如果没有这行，条件块语法不完整。
  if (current.selectedProviderId.length === 0 && current.selectedModelId.length === 0) { // 新增代码+ComposerRouteControls：识别还没有选择任何模型；如果没有这行，OAuth 成功后不会自动填入默认模型。
    const next = firstConnectedProviderModel(viewModel); // 新增代码+ComposerRouteControls：寻找后端默认或第一个已连接模型；如果没有这行，无法生成初始选择。
    return next.providerId.length > 0 && next.modelId.length > 0 ? { ...current, selectedProviderId: next.providerId, selectedModelId: next.modelId } : current; // 新增代码+ComposerRouteControls：有可用模型时填入，没有则保留空选择；如果没有这行，未连接状态会误产生模型。
  } // 新增代码+ComposerRouteControls：初始选择分支结束；如果没有这行，条件块语法不完整。
  return current; // 新增代码+ComposerRouteControls：当前选择仍有效时保持不变；如果没有这行，函数没有默认输出。
} // 新增代码+ComposerRouteControls：函数段结束，nextComposerRouteAfterProviderSettings 到此结束；如果没有这行，函数语法不完整。

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
  const [settingsOpen, setSettingsOpen] = useState(false); // 新增代码+ProviderSettingsShell：保存设置弹窗是否打开；如果没有这行，侧栏设置按钮无法控制弹窗显示和关闭。
  const [searchArchivedMode, setSearchArchivedMode] = useState(false); // 新增代码+DesktopGUISessionSearch：保存搜索是否处于归档过滤模式；如果没有这行，归档入口会退化成普通搜索。
  const [searchQuery, setSearchQuery] = useState(""); // 新增代码+DesktopGUISessionSearch：保存当前搜索词；如果没有这行，搜索输入框无法受控。
  const [searchResults, setSearchResults] = useState<SearchPanelResult[]>([]); // 新增代码+DesktopGUISessionSearch：保存搜索结果；如果没有这行，搜索面板没有数据容器。
  const [searchLoading, setSearchLoading] = useState(false); // 新增代码+DesktopGUISessionSearch：保存搜索加载状态；如果没有这行，用户不知道搜索是否正在进行。
  const [browserProviderStatus, setBrowserProviderStatus] = useState<Record<string, unknown>>({}); // 修改代码+DesktopRuntimePanels：保存浏览器 provider 兜底状态；如果没有这行，右侧 BrowserPanel 在旧 payload 下没有真实后端数据。
  const [runtimePanels, setRuntimePanels] = useState<Record<string, unknown>>({}); // 新增代码+DesktopRuntimePanels：保存 V2 runtime panels 状态；如果没有这行，浏览器和 Computer Use 成熟面板无法拿到统一后端事实。
  const [browserActionPending, setBrowserActionPending] = useState(false); // 新增代码+DesktopGUIBrowserWorkbench：保存 Browser 工作台动作等待态；如果没有这行，刷新和记录打开按钮可能被重复点击。
  const [lastBrowserActionResult, setLastBrowserActionResult] = useState<GuiBrowserActionPayload | null>(null); // 新增代码+DesktopGUIBrowserWorkbench：保存最近 Browser 动作结果；如果没有这行，右侧工作台无法立刻显示点击反馈。
  const [toolchainPayload, setToolchainPayload] = useState<Record<string, unknown>>({}); // 新增代码+DesktopGUIToolchainPanel：保存 V2 工具链清单；如果没有这行，右侧工具链页签无法显示后端工具注册表。
  const [harnessPayload, setHarnessPayload] = useState<Record<string, unknown>>({}); // 新增代码+DesktopGUIHarnessPanel：保存 V2 Harness 状态；如果没有这行，任务页签没有 active goal、queue 和 checkpoint。
  const [harnessControlPending, setHarnessControlPending] = useState(false); // 新增代码+DesktopGUIHarnessPanel：保存 Harness 控制请求等待态；如果没有这行，控制按钮无法避免重复点击。
  const [lastHarnessControlResult, setLastHarnessControlResult] = useState<GuiHarnessControlPayload | null>(null); // 新增代码+DesktopGUIHarnessControlsShell：保存最近一次 Harness 控制结果；如果没有这行，用户点击按钮后右侧任务面板没有反馈。
  const [computerUseActionPending, setComputerUseActionPending] = useState(false); // 新增代码+DesktopGUIComputerUseWorkbench：保存 Computer Use 按钮请求等待态；如果没有这行，申请、观察、中止按钮可能被重复点击。
  const [lastComputerUseActionResult, setLastComputerUseActionResult] = useState<GuiComputerUseActionPayload | null>(null); // 新增代码+DesktopGUIComputerUseWorkbench：保存最近 Computer Use 按钮响应；如果没有这行，右侧工作台无法立刻显示点击结果。
  const [healthPayload, setHealthPayload] = useState<Record<string, unknown>>({}); // ????+DesktopDiagnosticsPanel??? V2 health payload??????????????? uptime?provider ? feature flags?
  const [diagnosticsPayload, setDiagnosticsPayload] = useState<Record<string, unknown>>({}); // ????+DesktopDiagnosticsPanel??? V2 diagnostics payload??????????????? release gate ???????
  const [bridgeIssue, setBridgeIssue] = useState(""); // 新增代码+DesktopBridgeOfflineBanner：保存 bridge 离线或降级提示；如果没有这一行，轮询失败只会留在控制台。
  const [providerSettingsViewModel, setProviderSettingsViewModel] = useState<ProviderSettingsViewModel | null>(null); // 新增代码+ComposerRouteControls：保存 provider catalog 派生 view model；如果没有这行，底部模型下拉无法跟随后端连接状态。
  const [composerRoute, setComposerRoute] = useState<ComposerRouteState>(INITIAL_COMPOSER_ROUTE); // 修改代码+ComposerRouteControls：保存当前 provider/model/推理/权限选择；如果没有这行，底部下拉只会停留在硬编码值。
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
  const composerModelOptions = useMemo(() => composerModelOptionsFromProviderSettings(providerSettingsViewModel), [providerSettingsViewModel]); // 新增代码+ComposerRouteControls：缓存底部模型选项；如果没有这行，每次渲染都会重新遍历 provider catalog。
  const latestComposerModelStatus = useMemo(() => latestModelCallStatus(statusState.events), [statusState.events]); // 新增代码+RealModelObservability：从事件流提取最新模型调用阶段；如果没有这一行，Composer 状态条不会更新。

  function handleProviderSettingsPayload(payload: Parameters<typeof buildProviderSettingsViewModel>[0]): void { // 新增代码+ComposerRouteControls：函数段开始，接收 provider catalog 并同步底部模型路由；如果没有这段，设置页连接/断开后 composer 不会更新。
    const nextViewModel = buildProviderSettingsViewModel(payload); // 新增代码+ComposerRouteControls：把后端 payload 转成前端 view model；如果没有这行，后续逻辑要直接消费 snake_case。
    setProviderSettingsViewModel(nextViewModel); // 新增代码+ComposerRouteControls：保存最新 provider view model；如果没有这行，模型下拉不会刷新。
    setComposerRoute((current) => nextComposerRouteAfterProviderSettings(current, nextViewModel)); // 新增代码+ComposerRouteControls：按连接状态修正模型选择；如果没有这行，断开后仍会带旧模型提交。
  } // 新增代码+ComposerRouteControls：函数段结束，handleProviderSettingsPayload 到此结束；如果没有这行，函数语法不完整。

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
        const [bootstrapPayload, sessionsPayload, runtimePanelsPayload, toolchainPayloadResult, healthPayloadResult, diagnosticsPayloadResult, harnessPayloadResult] = await Promise.all([activeClient.bootstrap(), activeClient.sessions(), activeClient.runtimePanels(), activeClient.toolchain(), activeClient.health(), activeClient.diagnostics(), activeClient.harnessStatus()]); // 修改代码+DesktopGUIToolchainPanel：首屏同时读取工具链清单；如果没有这行，工具链页签要等额外请求才有事实源。
        if (disposed) { // 新增代码+DesktopGUISessions：检查组件是否已卸载；如果没有这行，迟到响应可能继续 setState。
          return; // 新增代码+DesktopGUISessions：卸载后停止处理；如果没有这行，React 可能提示卸载组件被更新。
        } // 新增代码+DesktopGUISessions：卸载检查结束；如果没有这行，条件块语法不完整。
        setProjectName(projectNameFromWorkspace(bootstrapPayload.workspace)); // 新增代码+DesktopGUISessions：把 workspace 转成侧栏项目名；如果没有这行，项目身份不会显示真实目录。
        setSidebarSessions(normalizeSidebarSessions(sessionsPayload.sessions)); // 新增代码+DesktopGUISessions：把后端 sessions 转成可点击条目；如果没有这行，最近会话列表会一直为空。
        setArchivedCount(typeof sessionsPayload.archived_count === "number" ? sessionsPayload.archived_count : 0); // 新增代码+DesktopGUISessionSearch：保存归档会话计数；如果没有这行，侧栏归档入口无法显示真实数量。
        setBrowserProviderStatus(runtimePanelsPayload.browser); // 修改代码+DesktopRuntimePanels：把 V2 浏览器子面板作为旧 provider 兜底；如果没有这行，BrowserPanel 旧入参会停留在空状态。
        setRuntimePanels(runtimePanelsPayload); // 新增代码+DesktopRuntimePanels：保存完整 V2 面板 payload；如果没有这行，Computer Use 面板没有锁、急停和权限数据。
        setToolchainPayload(toolchainPayloadResult); // 新增代码+DesktopGUIToolchainPanel：保存工具链清单 payload；如果没有这行，工具链页签会一直显示空态。
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

  useEffect(() => { // 新增代码+ComposerRouteControls：副作用段开始，加载 provider catalog 供底部模型下拉使用；如果没有这段，模型选择不会跟随后端连接状态。
    if (guiClient === null) { // 新增代码+ComposerRouteControls：没有 bridge client 时不能加载 provider catalog；如果没有这行，离线状态会反复请求失败。
      setProviderSettingsViewModel(null); // 新增代码+ComposerRouteControls：清空 provider view model；如果没有这行，离线后可能继续显示过期模型。
      setComposerRoute((current) => ({ ...current, selectedProviderId: "", selectedModelId: "" })); // 新增代码+ComposerRouteControls：清空可提交模型路由；如果没有这行，bridge 离线时仍可能保留旧模型。
      return undefined; // 新增代码+ComposerRouteControls：没有 client 时结束副作用；如果没有这行，后续会访问 null。
    } // 新增代码+ComposerRouteControls：client 检查结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 新增代码+ComposerRouteControls：固定本轮 provider catalog 请求使用的 client；如果没有这行，异步返回时可能读到新 client。
    let disposed = false; // 新增代码+ComposerRouteControls：标记本轮请求是否失效；如果没有这行，关闭或重连后迟到响应会覆盖新状态。
    async function loadProviderCatalogForComposer(): Promise<void> { // 新增代码+ComposerRouteControls：函数段开始，为 composer 读取 provider catalog；如果没有这段，副作用里会散落异步逻辑。
      try { // 新增代码+ComposerRouteControls：捕获 provider catalog 加载失败；如果没有这行，设置端点短暂失败会打断 React 副作用。
        const payload = await activeClient.providerSettings(); // 新增代码+ComposerRouteControls：请求 provider catalog；如果没有这行，底部模型列表没有后端事实来源。
        if (disposed) { // 新增代码+ComposerRouteControls：丢弃失效响应；如果没有这行，旧请求可能覆盖新窗口状态。
          return; // 新增代码+ComposerRouteControls：请求失效时退出；如果没有这行，仍会 setState。
        } // 新增代码+ComposerRouteControls：失效判断结束；如果没有这行，条件块语法不完整。
        handleProviderSettingsPayload(payload); // 新增代码+ComposerRouteControls：同步 provider catalog 和底部 route；如果没有这行，模型下拉不会更新。
      } catch (error) { // 新增代码+ComposerRouteControls：处理 provider catalog 加载失败；如果没有这行，网络错误会变成未捕获 Promise。
        console.warn("GUI bridge provider catalog load failed", error); // 新增代码+ComposerRouteControls：保留开发诊断日志；如果没有这行，模型下拉为空时难以排查。
        if (!disposed) { // 新增代码+ComposerRouteControls：只在请求仍有效时清空；如果没有这行，旧失败可能覆盖新成功。
          setProviderSettingsViewModel(null); // 新增代码+ComposerRouteControls：失败时清空 provider view model；如果没有这行，过期模型可能继续显示。
          setComposerRoute((current) => ({ ...current, selectedProviderId: "", selectedModelId: "" })); // 新增代码+ComposerRouteControls：失败时清空 provider/model；如果没有这行，提交可能带过期路由。
        } // 新增代码+ComposerRouteControls：失败清理判断结束；如果没有这行，条件块语法不完整。
      } // 新增代码+ComposerRouteControls：provider catalog 加载保护结束；如果没有这行，try/catch 语法不完整。
    } // 新增代码+ComposerRouteControls：函数段结束，loadProviderCatalogForComposer 到此结束；如果没有这行，函数语法不完整。
    void loadProviderCatalogForComposer(); // 新增代码+ComposerRouteControls：启动 provider catalog 加载；如果没有这行，定义好的函数不会执行。
    return () => { // 新增代码+ComposerRouteControls：返回副作用清理函数；如果没有这行，旧请求无法标记失效。
      disposed = true; // 新增代码+ComposerRouteControls：标记本轮请求失效；如果没有这行，迟到响应可能更新已失效状态。
    }; // 新增代码+ComposerRouteControls：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient]); // 新增代码+ComposerRouteControls：当 bridge client 变化时重新加载 provider catalog；如果没有这行，重启 bridge 后模型列表会过期。

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

  async function handleHarnessControl(action: "pause" | "resume" | "stop" | "checkpoint"): Promise<void> { // 修改代码+DesktopGUIHarnessControlsShell：函数段开始，处理四种长任务控制请求；如果没有这段，任务页签即使后端支持控制也无法触发动作。
    if (guiClient === null) { // 新增代码+DesktopGUIHarnessPanel：处理 bridge 未配置；如果没有这行，控制按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_harness_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法控制长任务。", status: "failed" } }); // 新增代码+DesktopGUIHarnessPanel：把配置缺失写到主线程；如果没有这行，用户不知道暂停或恢复为什么无效。
      return; // 新增代码+DesktopGUIHarnessPanel：没有 client 时停止控制流程；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopGUIHarnessPanel：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    setHarnessControlPending(true); // 新增代码+DesktopGUIHarnessPanel：标记控制请求正在提交；如果没有这行，按钮可能被重复点击。
    try { // 修改代码+DesktopGUIHarnessControlsShell：捕获四种控制失败；如果没有这行，后端异常会变成未捕获 Promise。
      let controlResult: GuiHarnessControlPayload; // 新增代码+DesktopGUIHarnessControlsShell：保存本次控制响应；如果没有这行，成功后无法把结果显示到右侧面板。
      if (action === "pause") { // 新增代码+DesktopGUIHarnessPanel：判断当前请求是否为暂停；如果没有这行，暂停和恢复会走同一条错误路径。
        controlResult = await guiClient.pauseHarness(); // 修改代码+DesktopGUIHarnessControlsShell：调用后端暂停端点并保存响应；如果没有这行，暂停按钮没有真实后端动作。
      } else if (action === "resume") { // 修改代码+DesktopGUIHarnessControlsShell：处理恢复分支；如果没有这行，恢复请求没有独立路径。
        controlResult = await guiClient.resumeHarness(); // 修改代码+DesktopGUIHarnessControlsShell：调用后端恢复端点并保存响应；如果没有这行，恢复按钮没有真实后端动作。
      } else if (action === "stop") { // 新增代码+DesktopGUIHarnessControlsShell：处理停止分支；如果没有这行，停止请求没有独立路径。
        controlResult = await guiClient.stopHarness(); // 新增代码+DesktopGUIHarnessControlsShell：调用后端停止端点并保存响应；如果没有这行，停止按钮没有真实后端动作。
      } else { // 新增代码+DesktopGUIHarnessControlsShell：处理 checkpoint 分支；如果没有这行，恢复点请求没有独立路径。
        controlResult = await guiClient.checkpointHarness(); // 新增代码+DesktopGUIHarnessControlsShell：调用后端 checkpoint 端点并保存响应；如果没有这行，checkpoint 按钮没有真实后端动作。
      } // 修改代码+DesktopGUIHarnessControlsShell：四种控制分支结束；如果没有这行，条件块语法不完整。
      setLastHarnessControlResult(controlResult); // 新增代码+DesktopGUIHarnessControlsShell：保存最近控制结果；如果没有这行，Task 面板不会显示本次控制反馈。
      const payload = await guiClient.harnessStatus(); // 新增代码+DesktopGUIHarnessPanel：控制请求后刷新 Harness 状态；如果没有这行，面板会停留在旧事实。
      setHarnessPayload(payload); // 新增代码+DesktopGUIHarnessPanel：把最新状态写入页面；如果没有这行，用户看不到控制后的结果。
    } catch (error) { // 新增代码+DesktopGUIHarnessPanel：处理控制异常；如果没有这行，未支持或断线只会留在控制台。
      const actionLabel = action === "pause" ? "暂停" : action === "resume" ? "恢复" : action === "stop" ? "停止" : "写入 checkpoint"; // 修改代码+DesktopGUIHarnessControlsShell：把四种动作转成中文文案；如果没有这行，错误消息不够直观。
      dispatchThread({ type: "message_added", message: { id: `local_harness_${action}_error_${Date.now()}`, role: "system", text: `长任务${actionLabel}请求失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopGUIHarnessPanel：把后端控制错误显示到主线程；如果没有这行，用户无法理解控制失败原因。
    } finally { // 新增代码+DesktopGUIHarnessPanel：无论成功失败都清理等待态；如果没有这行，失败后按钮可能一直禁用。
      setHarnessControlPending(false); // 新增代码+DesktopGUIHarnessPanel：结束控制请求等待态；如果没有这行，后续控制按钮无法恢复点击。
    } // 新增代码+DesktopGUIHarnessPanel：异常处理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+DesktopGUIHarnessPanel：函数段结束，handleHarnessControl 到此结束；如果没有这个边界，初学者不容易看出长任务控制范围。

  async function handleBrowserAction(action: "refresh-status" | "open", url = ""): Promise<void> { // 新增代码+DesktopGUIBrowserWorkbench：函数段开始，处理 Browser 工作台刷新和记录打开；如果没有这段，右侧浏览器按钮无法从 GUI 调用后端工具链。
    const actionLabel = action === "refresh-status" ? "刷新状态" : "记录打开"; // 新增代码+DesktopGUIBrowserWorkbench：把机器动作名转成中文；如果没有这行，线程反馈对新手不够直观。
    if (guiClient === null) { // 新增代码+DesktopGUIBrowserWorkbench：处理 bridge 未配置；如果没有这行，按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_browser_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法控制 Browser 工作台。", status: "failed" } }); // 新增代码+DesktopGUIBrowserWorkbench：把配置缺失写入主线程；如果没有这行，用户不知道按钮为什么无效。
      return; // 新增代码+DesktopGUIBrowserWorkbench：没有 client 时停止请求；如果没有这行，后续会继续访问 null client。
    } // 新增代码+DesktopGUIBrowserWorkbench：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    setBrowserActionPending(true); // 新增代码+DesktopGUIBrowserWorkbench：标记 Browser 请求正在提交；如果没有这行，用户可能连续点出多个请求。
    try { // 新增代码+DesktopGUIBrowserWorkbench：捕获 Browser 按钮调用失败；如果没有这行，POST 失败会变成未捕获 Promise。
      let actionResult: GuiBrowserActionPayload; // 新增代码+DesktopGUIBrowserWorkbench：保存本次后端响应；如果没有这行，分支结果无法统一写入 UI。
      if (action === "refresh-status") { // 新增代码+DesktopGUIBrowserWorkbench：处理刷新状态分支；如果没有这行，刷新按钮不会走专门 endpoint。
        actionResult = await guiClient.refreshBrowserStatus(); // 新增代码+DesktopGUIBrowserWorkbench：调用 refresh-status endpoint；如果没有这行，刷新按钮没有真实后端动作。
      } else { // 新增代码+DesktopGUIBrowserWorkbench：处理记录打开分支；如果没有这行，open 动作没有独立路径。
        actionResult = await guiClient.openBrowser(url); // 新增代码+DesktopGUIBrowserWorkbench：调用 open endpoint；如果没有这行，URL 请求不会进入后端审计流。
      } // 新增代码+DesktopGUIBrowserWorkbench：两个动作分支结束；如果没有这行，条件块语法不完整。
      setLastBrowserActionResult(actionResult); // 新增代码+DesktopGUIBrowserWorkbench：保存最近按钮结果；如果没有这行，工作台不会显示本次点击反馈。
      setRuntimePanels((current) => ({ ...current, browser: actionResult.browser })); // 新增代码+DesktopGUIBrowserWorkbench：用响应里的最新 Browser workbench 更新右栏；如果没有这行，按钮成功后仍要等下一轮轮询。
      setBrowserProviderStatus(actionResult.browser); // 新增代码+DesktopGUIBrowserWorkbench：同步旧 provider 兜底状态；如果没有这行，旧 BrowserPanel 入参可能滞后。
      await refreshEventsAfter(actionResult.events_after_sequence); // 新增代码+DesktopGUIBrowserWorkbench：补拉本次动作写入的状态事件；如果没有这行，右侧时间线可能晚于按钮结果。
      dispatchThread({ type: "message_added", message: { id: `local_browser_${action}_${Date.now()}`, role: "system", text: `Browser ${actionLabel}：${actionResult.message}`, status: actionResult.status === "failed" || actionResult.status === "invalid_url" ? "failed" : "completed" } }); // 新增代码+DesktopGUIBrowserWorkbench：把按钮结果写入主线程；如果没有这行，用户只能在右栏找反馈。
    } catch (error) { // 新增代码+DesktopGUIBrowserWorkbench：处理 Browser 请求异常；如果没有这行，断线或 404 会只留在控制台。
      const message = `Browser ${actionLabel}请求失败：${String(error)}`; // 新增代码+DesktopGUIBrowserWorkbench：生成可见失败说明；如果没有这行，fallback 响应没有人话消息。
      const fallback: GuiBrowserActionPayload = { ok: true, schema_version: 2, action: action === "open" ? "open" : "refresh-status", status: "failed", message, safe_error: "Browser 请求失败。", events_after_sequence: 0, browser: {} }; // 新增代码+DesktopGUIBrowserWorkbench：构造前端失败结果；如果没有这行，右侧工作台不会显示失败反馈。
      setLastBrowserActionResult(fallback); // 新增代码+DesktopGUIBrowserWorkbench：保存失败结果到工作台；如果没有这行，按钮失败后 UI 会像没发生过。
      dispatchThread({ type: "message_added", message: { id: `local_browser_${action}_error_${Date.now()}`, role: "system", text: message, status: "failed" } }); // 新增代码+DesktopGUIBrowserWorkbench：把失败显示到主线程；如果没有这行，用户看不到请求失败原因。
    } finally { // 新增代码+DesktopGUIBrowserWorkbench：无论成功失败都清理等待态；如果没有这行，失败后按钮会一直禁用。
      setBrowserActionPending(false); // 新增代码+DesktopGUIBrowserWorkbench：结束 Browser 请求等待态；如果没有这行，两个按钮无法恢复点击。
    } // 新增代码+DesktopGUIBrowserWorkbench：异常处理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+DesktopGUIBrowserWorkbench：函数段结束，handleBrowserAction 到此结束；如果没有这个边界，用户不容易看出 GUI 如何接到 Browser 后端。

  async function handleComputerUseAction(action: "request-access" | "observe" | "abort"): Promise<void> { // 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，处理 Computer Use 三个安全按钮；如果没有这段，右侧工作台无法从 GUI 调用后端工具链。
    const actionLabel = action === "request-access" ? "申请权限" : action === "observe" ? "观察" : "中止"; // 新增代码+DesktopGUIComputerUseWorkbench：把机器动作名转成中文；如果没有这行，线程反馈对新手不够直观。
    if (guiClient === null) { // 新增代码+DesktopGUIComputerUseWorkbench：处理 bridge 未配置；如果没有这行，按钮会访问空 client。
      dispatchThread({ type: "message_added", message: { id: `local_computer_use_missing_bridge_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，暂时无法控制 Computer Use。", status: "failed" } }); // 新增代码+DesktopGUIComputerUseWorkbench：把配置缺失写入主线程；如果没有这行，用户不知道按钮为什么无效。
      return; // 新增代码+DesktopGUIComputerUseWorkbench：没有 client 时停止请求；如果没有这行，后续会继续访问 null client。
    } // 新增代码+DesktopGUIComputerUseWorkbench：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    setComputerUseActionPending(true); // 新增代码+DesktopGUIComputerUseWorkbench：标记 Computer Use 请求正在提交；如果没有这行，用户可能连续点出多个请求。
    try { // 新增代码+DesktopGUIComputerUseWorkbench：捕获 Computer Use 按钮调用失败；如果没有这行，POST 失败会变成未捕获 Promise。
      let actionResult: GuiComputerUseActionPayload; // 新增代码+DesktopGUIComputerUseWorkbench：保存本次后端响应；如果没有这行，分支结果无法统一写入 UI。
      if (action === "request-access") { // 新增代码+DesktopGUIComputerUseWorkbench：处理申请权限分支；如果没有这行，申请按钮不会走专门 endpoint。
        actionResult = await guiClient.requestComputerUseAccess(); // 新增代码+DesktopGUIComputerUseWorkbench：调用 request-access endpoint；如果没有这行，申请权限按钮没有真实后端动作。
      } else if (action === "observe") { // 新增代码+DesktopGUIComputerUseWorkbench：处理观察分支；如果没有这行，观察按钮不会刷新状态。
        actionResult = await guiClient.observeComputerUse(); // 新增代码+DesktopGUIComputerUseWorkbench：调用 observe endpoint；如果没有这行，右侧工作台无法主动更新观察摘要。
      } else { // 新增代码+DesktopGUIComputerUseWorkbench：处理中止分支；如果没有这行，abort 动作没有独立路径。
        actionResult = await guiClient.abortComputerUse(); // 新增代码+DesktopGUIComputerUseWorkbench：调用 abort endpoint；如果没有这行，中止按钮无法复用后端 stop 状态机。
      } // 新增代码+DesktopGUIComputerUseWorkbench：三个动作分支结束；如果没有这行，条件块语法不完整。
      setLastComputerUseActionResult(actionResult); // 新增代码+DesktopGUIComputerUseWorkbench：保存最近按钮结果；如果没有这行，工作台不会显示本次点击反馈。
      setRuntimePanels((current) => ({ ...current, computer_use: actionResult.computer_use })); // 新增代码+DesktopGUIComputerUseWorkbench：用响应里的最新 workbench 更新右栏；如果没有这行，按钮成功后仍要等下一轮轮询。
      await refreshEventsAfter(actionResult.events_after_sequence); // 新增代码+DesktopGUIComputerUseWorkbench：补拉本次动作写入的状态事件；如果没有这行，右侧时间线可能晚于按钮结果。
      dispatchThread({ type: "message_added", message: { id: `local_computer_use_${action}_${Date.now()}`, role: "system", text: `Computer Use ${actionLabel}：${actionResult.message}`, status: actionResult.status === "failed" ? "failed" : "completed" } }); // 新增代码+DesktopGUIComputerUseWorkbench：把按钮结果写入主线程；如果没有这行，用户只能在右栏找反馈。
    } catch (error) { // 新增代码+DesktopGUIComputerUseWorkbench：处理 Computer Use 请求异常；如果没有这行，断线或 404 会只留在控制台。
      const message = `Computer Use ${actionLabel}请求失败：${String(error)}`; // 新增代码+DesktopGUIComputerUseWorkbench：生成可见失败说明；如果没有这行，fallback 响应没有人话消息。
      const fallback: GuiComputerUseActionPayload = { ok: true, schema_version: 2, action, status: "failed", message, safe_error: "Computer Use 请求失败。", events_after_sequence: 0, low_level_event_count: 0, computer_use: {} }; // 新增代码+DesktopGUIComputerUseWorkbench：构造前端失败结果；如果没有这行，右侧工作台不会显示失败反馈。
      setLastComputerUseActionResult(fallback); // 新增代码+DesktopGUIComputerUseWorkbench：保存失败结果到工作台；如果没有这行，按钮失败后 UI 会像没发生过。
      dispatchThread({ type: "message_added", message: { id: `local_computer_use_${action}_error_${Date.now()}`, role: "system", text: message, status: "failed" } }); // 新增代码+DesktopGUIComputerUseWorkbench：把失败显示到主线程；如果没有这行，用户看不到请求失败原因。
    } finally { // 新增代码+DesktopGUIComputerUseWorkbench：无论成功失败都清理等待态；如果没有这行，失败后按钮会一直禁用。
      setComputerUseActionPending(false); // 新增代码+DesktopGUIComputerUseWorkbench：结束 Computer Use 请求等待态；如果没有这行，三个按钮无法恢复点击。
    } // 新增代码+DesktopGUIComputerUseWorkbench：异常处理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，handleComputerUseAction 到此结束；如果没有这个边界，用户不容易看出 GUI 如何接到后端。

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

  async function handleSubmit(payload: ComposerSubmitPayload): Promise<void> { // 修改代码+DirectSSEPayload：函数段开始，处理用户提交 prompt 和模型路由字段；如果没有这段，Composer 输入不会进入线程或后端。
    const prompt = payload.prompt; // 新增代码+DirectSSEPayload：从结构化 payload 中取出正文；如果没有这行，后续消息显示和后端提交拿不到用户输入。
    const userMessageId = `local_user_${Date.now()}`; // 修改代码+DesktopToolTimeline：生成本地用户消息 id；如果没有这行，React 列表 key 不稳定。
    dispatchThread({ type: "message_added", message: { id: userMessageId, role: "user", text: prompt, status: "completed" } }); // 修改代码+DesktopToolTimeline：立即显示用户消息；如果没有这行，用户点击发送后界面没有反馈。
    if (guiClient === null) { // 修改代码+DesktopToolTimeline：处理 bridge 未配置；如果没有这行，用户只会看到网络失败。
      dispatchThread({ type: "message_added", message: { id: `local_system_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，请通过桌面启动脚本打开应用。", status: "failed" } }); // 修改代码+DesktopToolTimeline：显示配置缺失提示；如果没有这行，用户不知道应该启动后端 bridge。
      return; // 修改代码+DesktopToolTimeline：配置缺失时停止提交；如果没有这行，会继续访问 null client。
    } // 修改代码+DesktopToolTimeline：bridge 缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 修改代码+DesktopToolTimeline：捕获提交失败；如果没有这行，busy 或断线会变成未捕获错误。
      const response = await guiClient.sendMessage(prompt, activeConversationId, { providerId: payload.providerId, modelId: payload.modelId, reasoningEffort: payload.reasoningEffort, permissionMode: payload.permissionMode }); // 修改代码+DirectSSEPayload：向当前会话提交 prompt 和模型路由字段；如果没有这行，用户选中模型后后端仍只收到 prompt。
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
      <Sidebar projectName={projectName} sessions={sidebarSessions} activeSessionId={activeConversationId} archivedCount={archivedCount} onNewConversation={handleNewConversation} onOpenSearch={handleOpenSearch} onOpenArchived={() => { void handleOpenArchived(); }} onSelectSession={(sessionId) => { void handleSelectSession(sessionId); }} onOpenSettings={() => setSettingsOpen(true)} /> {/* 修改代码+ProviderSettingsShell：渲染带设置打开回调的侧栏；如果没有这行，左下角设置按钮无法打开 Provider Settings 弹窗。 */}
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
        <Composer isRunning={threadState.isRunning} activeTurnId={threadState.activeTurnId} selectedProviderId={composerRoute.selectedProviderId} selectedModelId={composerRoute.selectedModelId} reasoningEffort={composerRoute.reasoningEffort} permissionMode={composerRoute.permissionMode} modelOptions={composerModelOptions} modelCallStatus={latestComposerModelStatus} onModelChange={(providerId, modelId) => setComposerRoute((current) => ({ ...current, selectedProviderId: providerId, selectedModelId: modelId }))} onReasoningEffortChange={(value) => setComposerRoute((current) => ({ ...current, reasoningEffort: value }))} onPermissionModeChange={(value) => setComposerRoute((current) => ({ ...current, permissionMode: value }))} onCancelActiveTurn={(turnId) => { void handleCancelTurn(turnId); }} onSubmit={(payload) => { void handleSubmit(payload); }} /> {/* 修改代码+RealModelObservability：把运行态、模型路由和最新模型调用状态交给 composer；如果没有这行代码，底部输入区无法显示真实模型阶段。 */}
      </section> {/* 修改代码+DesktopToolTimeline：当前对话主区域结束；如果没有这行，JSX 结构不完整。 */}
      <StatusInspector events={statusState.events} browserProviderStatus={browserProviderStatus} runtimePanels={runtimePanels} toolchainPayload={toolchainPayload} harnessPayload={harnessPayload} bridgeBaseUrl={bridgeConfig?.baseUrl ?? ""} healthPayload={healthPayload} diagnosticsPayload={diagnosticsPayload} onProbeUnknownRoute={() => { void handleUnknownRouteProbe(); }} onPauseHarness={() => { void handleHarnessControl("pause"); }} onResumeHarness={() => { void handleHarnessControl("resume"); }} onStopHarness={() => { void handleHarnessControl("stop"); }} onCheckpointHarness={() => { void handleHarnessControl("checkpoint"); }} harnessControlPending={harnessControlPending} lastHarnessControlResult={lastHarnessControlResult ?? undefined} onRefreshBrowserStatus={() => { void handleBrowserAction("refresh-status"); }} onOpenBrowserUrl={(url) => { void handleBrowserAction("open", url); }} browserActionPending={browserActionPending} lastBrowserActionResult={lastBrowserActionResult ?? undefined} onRequestComputerUseAccess={() => { void handleComputerUseAction("request-access"); }} onObserveComputerUse={() => { void handleComputerUseAction("observe"); }} onAbortComputerUse={() => { void handleComputerUseAction("abort"); }} computerUseActionPending={computerUseActionPending} lastComputerUseActionResult={lastComputerUseActionResult ?? undefined} /> {/* 修改代码+DesktopGUIBrowserWorkbench：把工具链清单、Browser、Harness 控制和 Computer Use 工作台按钮交给右侧检查器；如果没有这行，GUI 无法从可见界面刷新浏览器、记录打开、申请、观察和中止桌面自动化。 */}
      <SearchPanel open={searchOpen} query={searchQuery} results={searchResults} isSearching={searchLoading} onClose={() => setSearchOpen(false)} onQueryChange={setSearchQuery} onSelectSession={(sessionId) => { void handleSelectSession(sessionId); }} /> {/* 新增代码+DesktopGUISessionSearch：渲染 V2 会话搜索面板；如果没有这行，搜索入口无法显示结果并恢复会话。 */}
      <PermissionDialog open={permissionDialogOpen} requestId={permissionRequest?.requestId ?? ""} toolName={permissionRequest?.toolName ?? ""} appName={permissionRequest?.appName ?? ""} actionSummary={permissionRequest?.actionSummary ?? ""} reason={permissionRequest?.reason ?? ""} riskSummary={permissionRequest?.riskSummary ?? ""} decisionPending={permissionDecisionPending} onApprove={() => { void handlePermissionDecision("approve"); }} onDeny={() => { void handlePermissionDecision("deny"); }} /> {/* 修改代码+DesktopGUIPermissionsV2：渲染 V2 权限确认弹窗并提交后端决策；如果没有这行，用户无法在 GUI 中允许或拒绝。 */}
      <SettingsDialog guiClient={guiClient ?? undefined} open={settingsOpen} onClose={() => setSettingsOpen(false)} onProviderSettingsChanged={handleProviderSettingsPayload} /> {/* 修改代码+ComposerRouteControls：把真实 GUI bridge client 和 provider catalog 回调传给设置弹窗；如果没有这行，断开 provider 后底部模型不会重置。 */}
    </main> // 修改代码+DesktopToolTimeline：全窗口网格容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopToolTimeline：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopToolTimeline：函数段结束，AppShell 到此结束；如果没有这个边界，用户不容易看出主壳组合范围。
