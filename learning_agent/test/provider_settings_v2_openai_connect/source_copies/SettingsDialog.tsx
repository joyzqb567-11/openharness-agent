import { useEffect, useState, type KeyboardEvent } from "react"; // 修改代码+ProviderSettingsPanel：导入弹窗状态和键盘副作用工具；如果没有这行，标签切换、数据加载和 Escape 关闭都无法实现。
import { Cpu, Keyboard, Monitor, Server, ShieldAlert, SlidersHorizontal, X } from "lucide-react"; // 修改代码+ProviderSettingsPanel：导入设置导航需要的图标；如果没有这行，设置页扫描性会退化成纯文字。
import type { CustomProviderRequest, GuiProviderSettingsPayload, ProviderAuthAttemptInfo, ProviderAuthAttemptPayload, ProviderConnectionProbePayload } from "../../api/guiProviderTypes"; // 修改代码+OpenAIConnectDialog：导入 provider settings、自定义 provider 和 auth-attempt 合同；如果没有这行，弹窗容器无法类型化等待授权流程。
import { buildProviderSettingsViewModel, type ProviderRowView, type ProviderSettingsViewModel } from "../../state/providerSettingsStore"; // 新增代码+ProviderSettingsPanel：导入 provider view model builder；如果没有这行，弹窗会直接消费后端 snake_case payload。
import packageInfo from "../../../package.json"; // 修改代码+ProviderSettingsPanel：读取桌面 package 版本；如果没有这行，footer 无法自动显示真实版本。
import { CustomProviderDialog } from "./CustomProviderDialog"; // 新增代码+CustomProviderDialog：导入自定义 provider 弹窗；如果没有这行，虚拟 CTA 点击后没有真实表单。
import { ProviderConnectDialog } from "./ProviderConnectDialog"; // 新增代码+ProviderSettingsPanel：导入连接弹窗；如果没有这行，Provider 列表无法收集 API key。
import { modelVisibilityKey, SettingsModelsPanel } from "./SettingsModelsPanel"; // 新增代码+SettingsModelsPanel：导入模型可见性面板和 pending key helper；如果没有这行，模型页只能显示占位。
import { SettingsProvidersPanel } from "./SettingsProvidersPanel"; // 新增代码+ProviderSettingsPanel：导入 Provider 列表面板；如果没有这行，设置弹窗无法显示 provider catalog。

type SettingsTabId = "general" | "shortcuts" | "server" | "providers" | "models"; // 修改代码+ProviderSettingsPanel：定义设置页签 id；如果没有这行，active tab 会变成不受约束的字符串。

type SettingsTab = { // 修改代码+ProviderSettingsPanel：类型段开始，描述左侧设置页签；如果没有这段，导航数组字段含义不清楚。
  id: SettingsTabId; // 修改代码+ProviderSettingsPanel：保存页签 id；如果没有这行，点击后无法定位内容。
  label: string; // 修改代码+ProviderSettingsPanel：保存页签显示名；如果没有这行，导航只剩机器码。
  section: "desktop" | "server"; // 修改代码+ProviderSettingsPanel：保存页签所属分区；如果没有这行，桌面和服务器分组无法稳定渲染。
  Icon: typeof Monitor; // 修改代码+ProviderSettingsPanel：保存页签图标组件；如果没有这行，导航图标无法类型化。
}; // 修改代码+ProviderSettingsPanel：SettingsTab 类型结束；如果没有这行，TypeScript 类型语法不完整。

type ProviderSettingsClient = { // 新增代码+ProviderSettingsPanel：类型段开始，定义设置弹窗需要的 GUI client 子集；如果没有这段，组件会依赖完整大 client。
  providerSettings: () => Promise<GuiProviderSettingsPayload>; // 新增代码+ProviderSettingsPanel：声明读取 catalog 方法；如果没有这行，弹窗无法加载 provider 列表。
  connectProvider: (providerId: string, authMethodId: string, fields: Record<string, string>) => Promise<GuiProviderSettingsPayload>; // 新增代码+ProviderSettingsPanel：声明连接 provider 方法；如果没有这行，连接弹窗无法保存 API key。
  startProviderAuthAttempt: (providerId: string, authMethodId: string) => Promise<ProviderAuthAttemptPayload>; // 新增代码+OpenAIConnectDialog：声明启动 auth-attempt 方法；如果没有这行，browser/headless 入口无法调用后端。
  providerAuthAttemptStatus: (attemptId: string) => Promise<ProviderAuthAttemptPayload>; // 新增代码+OpenAIConnectDialog：声明读取 auth-attempt 状态方法；如果没有这行，等待页无法轮询。
  cancelProviderAuthAttempt: (attemptId: string) => Promise<ProviderAuthAttemptPayload>; // 新增代码+OpenAIConnectDialog：声明取消 auth-attempt 方法；如果没有这行，关闭弹窗无法清理 pending。
  disconnectProvider: (providerId: string) => Promise<GuiProviderSettingsPayload>; // 新增代码+ProviderSettingsPanel：声明断开 provider 方法；如果没有这行，已连接 provider 无法断开。
  saveCustomProvider: (payload: CustomProviderRequest) => Promise<GuiProviderSettingsPayload>; // 新增代码+CustomProviderDialog：声明保存自定义 provider 方法；如果没有这行，自定义表单无法写入后端配置。
  setModelVisibility: (providerId: string, modelId: string, visible: boolean) => Promise<GuiProviderSettingsPayload>; // 新增代码+SettingsModelsPanel：声明模型可见性保存方法；如果没有这行，模型开关无法持久化。
  testProviderConnection: (providerId: string) => Promise<ProviderConnectionProbePayload>; // 新增代码+ProviderSettingsPanel：声明测试连接方法；如果没有这行，测试按钮无法调用 bridge。
}; // 新增代码+ProviderSettingsPanel：ProviderSettingsClient 类型结束；如果没有这行，TypeScript 类型语法不完整。

type SettingsDialogProps = { // 修改代码+ProviderSettingsPanel：类型段开始，定义设置弹窗输入；如果没有这段，AppShell 不知道如何控制弹窗。
  open: boolean; // 修改代码+ProviderSettingsPanel：保存弹窗是否打开；如果没有这行，关闭状态无法从 DOM 移除。
  onClose: () => void; // 修改代码+ProviderSettingsPanel：保存关闭回调；如果没有这行，关闭按钮和 Escape 无法把状态交回 AppShell。
  version?: string; // 修改代码+ProviderSettingsPanel：允许测试或打包流程覆盖版本；如果没有这行，测试只能依赖 package JSON。
  secretStoreWarning?: string; // 修改代码+ProviderSettingsPanel：保存外部传入的开发密钥存储警告；如果没有这行，纯 shell 测试无法注入警告。
  guiClient?: ProviderSettingsClient; // 新增代码+ProviderSettingsPanel：保存可选 provider settings client；如果没有这行，弹窗无法通过 bridge 读取或修改 provider 状态。
}; // 修改代码+ProviderSettingsPanel：SettingsDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

type AuthAttemptPollDecision = { // 新增代码+OpenAIConnectPollRaceFix：类型段开始，描述一次 auth-attempt 轮询结果该触发的 UI 动作；如果没有这段，complete/pending/error 状态的处理顺序容易再次散落成竞态。
  refreshProviderSettings: boolean; // 新增代码+OpenAIConnectPollRaceFix：标记是否需要先刷新 provider catalog；如果没有这行，complete 状态可能不会让 OpenAI 行变成已连接。
  keepAttemptVisibleBeforeRefresh: boolean; // 新增代码+OpenAIConnectPollRaceFix：标记是否可以把 attempt 写回等待页；如果没有这行，complete 状态可能先触发 React cleanup 并阻断刷新落地。
  safeErrorMessage: string; // 新增代码+OpenAIConnectPollRaceFix：保存可显示给用户的安全错误文案；如果没有这行，失败或过期状态可能没有明确反馈。
}; // 新增代码+OpenAIConnectPollRaceFix：AuthAttemptPollDecision 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function authAttemptPollDecision(status: ProviderAuthAttemptInfo["status"]): AuthAttemptPollDecision { // 新增代码+OpenAIConnectPollRaceFix：函数段开始，把 auth-attempt 状态转换成轮询动作；如果没有这段，complete 状态容易先 setState 触发旧 effect cleanup。
  if (status === "complete") { // 新增代码+OpenAIConnectPollRaceFix：识别授权完成状态；如果没有这行，完成状态会被当成普通等待态处理。
    return { refreshProviderSettings: true, keepAttemptVisibleBeforeRefresh: false, safeErrorMessage: "" }; // 新增代码+OpenAIConnectPollRaceFix：要求 complete 先刷新 catalog 且不先写回 attempt；如果没有这行，视觉 QA 会停在等待页而不会显示已连接。
  } // 新增代码+OpenAIConnectPollRaceFix：完成状态分支结束；如果没有这行，条件块语法不完整。
  if (status === "failed" || status === "expired") { // 新增代码+OpenAIConnectPollRaceFix：识别失败或过期状态；如果没有这行，终态错误会继续显示成等待中。
    return { refreshProviderSettings: false, keepAttemptVisibleBeforeRefresh: true, safeErrorMessage: "授权未完成" }; // 新增代码+OpenAIConnectPollRaceFix：失败或过期继续显示 attempt 并给安全错误；如果没有这行，用户不知道授权已经结束。
  } // 新增代码+OpenAIConnectPollRaceFix：失败或过期分支结束；如果没有这行，条件块语法不完整。
  return { refreshProviderSettings: false, keepAttemptVisibleBeforeRefresh: true, safeErrorMessage: "" }; // 新增代码+OpenAIConnectPollRaceFix：pending 保持等待页可见；如果没有这行，等待授权时用户看不到链接和确认码。
} // 新增代码+OpenAIConnectPollRaceFix：函数段结束，authAttemptPollDecision 到此结束；如果没有这个边界，用户不容易看出它只做状态决策。

export function shouldPollAuthAttempt(open: boolean, hasClient: boolean, attempt: Pick<ProviderAuthAttemptInfo, "status"> | null): boolean { // 新增代码+OpenAIConnectPollTail：函数段开始，判断当前是否应该轮询 auth-attempt；如果没有这段，关闭弹窗或终态 attempt 可能继续残留 timer。
  return open && hasClient && attempt !== null && attempt.status === "pending"; // 新增代码+OpenAIConnectPollTail：只有弹窗打开、有 client、有 pending attempt 时才轮询；如果没有这行，failed/expired/complete 或关闭状态会继续请求后端。
} // 新增代码+OpenAIConnectPollTail：函数段结束，shouldPollAuthAttempt 到此结束；如果没有这个边界，用户不容易看出它只负责轮询开关。

const settingsTabs: SettingsTab[] = [ // 修改代码+ProviderSettingsPanel：定义设置页签顺序；如果没有这段，左侧导航会散落在 JSX 中。
  { id: "general", label: "通用", section: "desktop", Icon: SlidersHorizontal }, // 修改代码+ProviderSettingsPanel：声明通用页签；如果没有这行，桌面设置缺少基础入口。
  { id: "shortcuts", label: "快捷键", section: "desktop", Icon: Keyboard }, // 修改代码+ProviderSettingsPanel：声明快捷键页签；如果没有这行，后续快捷键设置没有固定位置。
  { id: "server", label: "服务器", section: "server", Icon: Server }, // 修改代码+ProviderSettingsPanel：声明服务器页签；如果没有这行，后端连接配置没有固定位置。
  { id: "providers", label: "提供商", section: "server", Icon: Cpu }, // 修改代码+ProviderSettingsPanel：声明提供商页签；如果没有这行，大模型提供商管理没有默认入口。
  { id: "models", label: "模型", section: "server", Icon: Monitor }, // 修改代码+ProviderSettingsPanel：声明模型页签；如果没有这行，模型可见性管理没有位置。
]; // 修改代码+ProviderSettingsPanel：设置页签数组结束；如果没有这行，TypeScript 数组语法不完整。

function tabButtonClassName(tabId: SettingsTabId, activeTab: SettingsTabId): string { // 修改代码+ProviderSettingsPanel：函数段开始，生成页签按钮 class；如果没有这段，active 样式判断会散落在 JSX 中。
  return `settings-dialog-tab${tabId === activeTab ? " settings-dialog-tab-active" : ""}`; // 修改代码+ProviderSettingsPanel：根据 active 状态返回 class；如果没有这行，当前页签无法高亮。
} // 修改代码+ProviderSettingsPanel：函数段结束，tabButtonClassName 到此结束；如果没有这行，函数语法不完整。

function panelTitle(activeTab: SettingsTabId): string { // 修改代码+ProviderSettingsPanel：函数段开始，生成内容区标题；如果没有这段，标题会和页签数据重复手写。
  return settingsTabs.find((tab) => tab.id === activeTab)?.label ?? "提供商"; // 修改代码+ProviderSettingsPanel：按 active tab 查找标题并提供兜底；如果没有这行，异常 tab 会让标题空白。
} // 修改代码+ProviderSettingsPanel：函数段结束，panelTitle 到此结束；如果没有这行，函数语法不完整。

function safeProviderError(defaultMessage: string): string { // 新增代码+ProviderSettingsPanel：函数段开始，生成安全错误文案；如果没有这段，底层异常可能把 URL/header/raw key 带进 GUI。
  return defaultMessage; // 新增代码+ProviderSettingsPanel：只返回固定安全文案；如果没有这行，用户看不到失败但也不会泄露敏感信息。
} // 新增代码+ProviderSettingsPanel：函数段结束，safeProviderError 到此结束；如果没有这行，函数语法不完整。

function panelContent(activeTab: SettingsTabId, providerViewModel: ProviderSettingsViewModel | null, providerLoading: boolean, providerError: string, busyProviderId: string, probeResults: Record<string, string>, modelPendingKey: string, modelError: string, onRetry: () => void, onConnectProvider: (provider: ProviderRowView) => void, onDisconnectProvider: (provider: ProviderRowView) => void, onTestProvider: (provider: ProviderRowView) => void, onOpenCustomProvider: () => void, onToggleModel: (providerId: string, modelId: string, visible: boolean) => void): JSX.Element { // 修改代码+SettingsModelsPanel：函数段开始，渲染当前页签内容并注入 provider/model 操作；如果没有这段，右侧内容会散落在主组件中。
  if (activeTab === "providers") { // 修改代码+ProviderSettingsPanel：处理默认提供商页；如果没有这行，Provider Settings 面板不会显示。
    return <SettingsProvidersPanel viewModel={providerViewModel} loading={providerLoading} errorMessage={providerError} busyProviderId={busyProviderId} probeResults={probeResults} onRetry={onRetry} onConnectProvider={onConnectProvider} onDisconnectProvider={onDisconnectProvider} onTestProvider={onTestProvider} onOpenCustomProvider={onOpenCustomProvider} />; // 新增代码+ProviderSettingsPanel：渲染真实 provider 列表；如果没有这行，设置页无法展示或操作提供商。
  } // 修改代码+ProviderSettingsPanel：提供商分支结束；如果没有这行，条件块语法不完整。
  if (activeTab === "models") { // 修改代码+ProviderSettingsPanel：处理模型页；如果没有这行，模型页没有独立占位。
    return <SettingsModelsPanel viewModel={providerViewModel} pendingModelKey={modelPendingKey} errorMessage={modelError} onToggleModel={onToggleModel} />; // 新增代码+SettingsModelsPanel：渲染真实模型可见性面板；如果没有这行，模型页只能显示静态占位。
  } // 修改代码+ProviderSettingsPanel：模型分支结束；如果没有这行，条件块语法不完整。
  return <div className="settings-dialog-placeholder">OpenHarness Desktop</div>; // 修改代码+ProviderSettingsPanel：渲染其他设置页占位；如果没有这行，非 Provider 页切换后会空白。
} // 修改代码+ProviderSettingsPanel：函数段结束，panelContent 到此结束；如果没有这行，函数语法不完整。

export function SettingsDialog({ open, onClose, version = packageInfo.version, secretStoreWarning = "", guiClient }: SettingsDialogProps): JSX.Element | null { // 修改代码+ProviderSettingsPanel：函数段开始，渲染 OpenHarness Desktop 设置弹窗；如果没有这段，左下角设置入口没有成熟 GUI 外壳。
  const [activeTab, setActiveTab] = useState<SettingsTabId>("providers"); // 修改代码+ProviderSettingsPanel：保存当前页签并默认提供商页；如果没有这行，弹窗无法默认打开 Provider 设置。
  const [providerPayload, setProviderPayload] = useState<GuiProviderSettingsPayload | null>(null); // 新增代码+ProviderSettingsPanel：保存 bridge 返回的 provider catalog；如果没有这行，列表刷新后没有状态容器。
  const [providerLoading, setProviderLoading] = useState(false); // 新增代码+ProviderSettingsPanel：保存 provider catalog 加载态；如果没有这行，加载过程没有可见反馈。
  const [providerError, setProviderError] = useState(""); // 新增代码+ProviderSettingsPanel：保存 provider catalog 错误；如果没有这行，失败状态无法显示。
  const [busyProviderId, setBusyProviderId] = useState(""); // 新增代码+ProviderSettingsPanel：保存当前 provider 操作等待态；如果没有这行，重复点击无法被抑制。
  const [probeResults, setProbeResults] = useState<Record<string, string>>({}); // 新增代码+ProviderSettingsPanel：保存测试连接结果；如果没有这行，探针反馈无法贴到 provider 行。
  const [connectProvider, setConnectProvider] = useState<ProviderRowView | null>(null); // 新增代码+ProviderSettingsPanel：保存正在连接的 provider；如果没有这行，连接弹窗不知道标题和 id。
  const [connectApiKey, setConnectApiKey] = useState(""); // 新增代码+ProviderSettingsPanel：保存连接弹窗本地 API key；如果没有这行，输入框无法受控并在成功后清空。
  const [connectPending, setConnectPending] = useState(false); // 新增代码+ProviderSettingsPanel：保存连接提交等待态；如果没有这行，用户可能重复提交密钥。
  const [connectError, setConnectError] = useState(""); // 新增代码+ProviderSettingsPanel：保存连接错误文案；如果没有这行，后端失败没有可见反馈。
  const [connectAuthAttempt, setConnectAuthAttempt] = useState<ProviderAuthAttemptInfo | null>(null); // 新增代码+OpenAIConnectDialog：保存当前 browser/headless 授权尝试；如果没有这行，等待页无法显示轮询状态。
  const [customProviderOpen, setCustomProviderOpen] = useState(false); // 新增代码+CustomProviderDialog：保存自定义 provider 弹窗是否打开；如果没有这行，虚拟 CTA 无法控制表单显示。
  const [customProviderPending, setCustomProviderPending] = useState(false); // 新增代码+CustomProviderDialog：保存自定义 provider 保存等待态；如果没有这行，用户可能重复提交配置。
  const [customProviderError, setCustomProviderError] = useState(""); // 新增代码+CustomProviderDialog：保存自定义 provider 安全错误文案；如果没有这行，保存失败没有可见反馈。
  const [modelPendingKeyValue, setModelPendingKeyValue] = useState(""); // 新增代码+SettingsModelsPanel：保存正在保存的模型开关 key；如果没有这行，模型开关无法进入 pending 状态。
  const [modelError, setModelError] = useState(""); // 新增代码+SettingsModelsPanel：保存模型可见性保存错误；如果没有这行，保存失败没有可见反馈。
  const providerViewModel = providerPayload === null ? null : buildProviderSettingsViewModel(providerPayload); // 新增代码+ProviderSettingsPanel：把后端 payload 转成 view model；如果没有这行，Provider 面板会消费 snake_case 原始数据。
  const visibleSecretWarning = providerViewModel?.secretStoreWarning ?? secretStoreWarning; // 新增代码+ProviderSettingsPanel：优先使用后端 dev_json warning；如果没有这行，真实 catalog 的 secret store 风险不会显示。

  async function refreshProviderSettings(): Promise<void> { // 新增代码+ProviderSettingsPanel：函数段开始，重新读取 provider catalog；如果没有这段，打开弹窗和重试按钮无法加载数据。
    if (guiClient === undefined) { // 新增代码+ProviderSettingsPanel：检查 bridge client 是否可用；如果没有这行，缺 client 时会抛运行时异常。
      setProviderError(""); // 新增代码+ProviderSettingsPanel：无 client 时不显示加载失败；如果没有这行，纯 shell 测试会看到不必要错误。
      return; // 新增代码+ProviderSettingsPanel：缺 client 直接退出；如果没有这行，后续会访问 undefined client。
    } // 新增代码+ProviderSettingsPanel：client 检查结束；如果没有这行，条件块语法不完整。
    setProviderLoading(true); // 新增代码+ProviderSettingsPanel：进入加载态；如果没有这行，用户不知道 catalog 正在刷新。
    setProviderError(""); // 新增代码+ProviderSettingsPanel：清空旧错误；如果没有这行，成功重试后旧错误仍可见。
    try { // 新增代码+ProviderSettingsPanel：捕获 catalog 加载失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const payload = await guiClient.providerSettings(); // 新增代码+ProviderSettingsPanel：调用 bridge 读取 provider catalog；如果没有这行，列表没有后端事实源。
      setProviderPayload(payload); // 新增代码+ProviderSettingsPanel：保存最新 provider payload；如果没有这行，界面不会刷新 provider 列表。
    } catch { // 新增代码+ProviderSettingsPanel：处理 catalog 加载异常；如果没有这行，失败原因只会进控制台。
      setProviderError(safeProviderError("提供商加载失败")); // 新增代码+ProviderSettingsPanel：显示安全失败文案；如果没有这行，用户不知道加载失败。
    } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都退出加载态；如果没有这行，失败后会一直显示加载。
      setProviderLoading(false); // 新增代码+ProviderSettingsPanel：关闭加载态；如果没有这行，按钮和空态不会恢复。
    } // 新增代码+ProviderSettingsPanel：加载清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+ProviderSettingsPanel：函数段结束，refreshProviderSettings 到此结束；如果没有这个边界，用户不容易看出加载流程范围。

  useEffect(() => { // 修改代码+ProviderSettingsPanel：副作用段开始，绑定 Escape 关闭弹窗；如果没有这段，键盘关闭验收无法通过。
    if (!open) { // 修改代码+ProviderSettingsPanel：弹窗关闭时不绑定事件；如果没有这行，隐藏弹窗也会监听键盘。
      return undefined; // 修改代码+ProviderSettingsPanel：关闭状态返回空清理；如果没有这行，React 副作用返回值不清晰。
    } // 修改代码+ProviderSettingsPanel：关闭状态分支结束；如果没有这行，条件块语法不完整。
    function handleWindowKeyDown(event: globalThis.KeyboardEvent): void { // 修改代码+ProviderSettingsPanel：函数段开始，处理全局键盘事件；如果没有这段，Escape 键不会关闭弹窗。
      if (event.key === "Escape") { // 修改代码+ProviderSettingsPanel：只响应 Escape；如果没有这行，任何按键都可能关闭设置页。
        onClose(); // 修改代码+ProviderSettingsPanel：调用关闭回调；如果没有这行，键盘事件不会改变 AppShell 状态。
      } // 修改代码+ProviderSettingsPanel：Escape 分支结束；如果没有这行，条件块语法不完整。
    } // 修改代码+ProviderSettingsPanel：函数段结束，handleWindowKeyDown 到此结束；如果没有这行，函数语法不完整。
    window.addEventListener("keydown", handleWindowKeyDown); // 修改代码+ProviderSettingsPanel：注册键盘监听；如果没有这行，Escape 键不会被捕获。
    return () => { // 修改代码+ProviderSettingsPanel：返回清理函数；如果没有这行，弹窗关闭后监听器会泄漏。
      window.removeEventListener("keydown", handleWindowKeyDown); // 修改代码+ProviderSettingsPanel：移除键盘监听；如果没有这行，反复打开会累积事件处理器。
    }; // 修改代码+ProviderSettingsPanel：清理函数结束；如果没有这行，return 语法不完整。
  }, [onClose, open]); // 修改代码+ProviderSettingsPanel：按打开状态和关闭回调更新副作用；如果没有这行，监听器会使用过期回调。

  useEffect(() => { // 新增代码+ProviderSettingsPanel：副作用段开始，弹窗打开时读取 provider catalog；如果没有这段，Provider 列表不会自动加载。
    if (!open || guiClient === undefined) { // 新增代码+ProviderSettingsPanel：只在打开且 client 可用时加载；如果没有这行，关闭状态或测试环境会发请求。
      return undefined; // 新增代码+ProviderSettingsPanel：无需加载时返回空清理；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+ProviderSettingsPanel：加载前置判断结束；如果没有这行，条件块语法不完整。
    const activeClient = guiClient; // 修改代码+ProviderSettingsPanel：固定本轮副作用使用的 bridge client；如果没有这行，异步函数里 TypeScript 会认为 client 可能变成 undefined。
    let disposed = false; // 新增代码+ProviderSettingsPanel：记录本轮加载是否失效；如果没有这行，关闭弹窗后迟到响应可能 setState。
    async function loadProviderSettings(): Promise<void> { // 新增代码+ProviderSettingsPanel：函数段开始，执行一次 provider catalog 加载；如果没有这段，副作用里的异步逻辑会散落。
      setProviderLoading(true); // 新增代码+ProviderSettingsPanel：进入加载态；如果没有这行，打开弹窗时没有正在加载反馈。
      setProviderError(""); // 新增代码+ProviderSettingsPanel：清空旧错误；如果没有这行，重新打开仍显示旧错误。
      try { // 新增代码+ProviderSettingsPanel：捕获 catalog 加载失败；如果没有这行，bridge 错误会打断 React 副作用。
        const payload = await activeClient.providerSettings(); // 修改代码+ProviderSettingsPanel：用本轮固定 client 调用 provider catalog endpoint；如果没有这行，Provider 列表没有后端数据且类型检查会失败。
        if (!disposed) { // 新增代码+ProviderSettingsPanel：只在本轮仍有效时更新状态；如果没有这行，关闭后可能更新已卸载组件。
          setProviderPayload(payload); // 新增代码+ProviderSettingsPanel：保存 provider payload；如果没有这行，列表不会显示后端 provider。
        } // 新增代码+ProviderSettingsPanel：有效性判断结束；如果没有这行，条件块语法不完整。
      } catch { // 新增代码+ProviderSettingsPanel：处理加载异常；如果没有这行，失败不会进入可见 UI。
        if (!disposed) { // 新增代码+ProviderSettingsPanel：只在本轮仍有效时显示错误；如果没有这行，关闭后可能更新状态。
          setProviderError(safeProviderError("提供商加载失败")); // 新增代码+ProviderSettingsPanel：显示安全错误文案；如果没有这行，用户不知道加载失败。
        } // 新增代码+ProviderSettingsPanel：错误有效性判断结束；如果没有这行，条件块语法不完整。
      } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都退出加载态；如果没有这行，加载状态可能卡住。
        if (!disposed) { // 新增代码+ProviderSettingsPanel：只在本轮仍有效时更新加载态；如果没有这行，关闭后可能更新状态。
          setProviderLoading(false); // 新增代码+ProviderSettingsPanel：关闭加载态；如果没有这行，列表会一直显示正在加载。
        } // 新增代码+ProviderSettingsPanel：加载态有效性判断结束；如果没有这行，条件块语法不完整。
      } // 新增代码+ProviderSettingsPanel：加载清理结束；如果没有这行，try/catch/finally 语法不完整。
    } // 新增代码+ProviderSettingsPanel：函数段结束，loadProviderSettings 到此结束；如果没有这个边界，用户不容易看出自动加载范围。
    void loadProviderSettings(); // 新增代码+ProviderSettingsPanel：启动 provider catalog 加载；如果没有这行，定义好的加载函数不会执行。
    return () => { // 新增代码+ProviderSettingsPanel：返回清理函数；如果没有这行，关闭弹窗后无法标记请求失效。
      disposed = true; // 新增代码+ProviderSettingsPanel：标记本轮请求失效；如果没有这行，迟到响应可能覆盖新状态。
    }; // 新增代码+ProviderSettingsPanel：清理函数结束；如果没有这行，return 语法不完整。
  }, [guiClient, open]); // 新增代码+ProviderSettingsPanel：按 client 和打开状态重新加载；如果没有这行，换 bridge 后 provider 列表会过期。

  useEffect(() => { // 新增代码+OpenAIConnectDialog：副作用段开始，轮询当前 auth-attempt 状态；如果没有这段，等待授权页不会自动更新。
    const activeClient = guiClient; // 修改代码+OpenAIConnectPollTail：先固定本轮轮询使用的 client；如果没有这行，TypeScript 无法确认异步回调里 client 不会变成 undefined。
    const activeAttempt = connectAuthAttempt; // 修改代码+OpenAIConnectPollTail：先固定本轮轮询使用的 attempt；如果没有这行，TypeScript 无法确认后续 attempt 不会变成 null。
    if (!shouldPollAuthAttempt(open, activeClient !== undefined, activeAttempt) || activeClient === undefined || activeAttempt === null) { // 修改代码+OpenAIConnectPollTail：只在打开、有 client、有 pending attempt 时轮询并显式窄化类型；如果没有这行，关闭弹窗或终态 attempt 也会继续请求且 lint 会失败。
      return undefined; // 新增代码+OpenAIConnectDialog：不需要轮询时返回空清理；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+OpenAIConnectDialog：轮询前置判断结束；如果没有这行，条件块语法不完整。
    const pollingClient: ProviderSettingsClient = activeClient; // 修改代码+OpenAIConnectPollTail：把已确认存在的 client 固定成非可选类型；如果没有这行，TypeScript 在嵌套异步函数里仍会认为 client 可能为 undefined。
    const activeAttemptId = activeAttempt.attempt_id; // 修改代码+OpenAIConnectPollTail：固定本轮轮询的 attempt id；如果没有这行，异步回调可能读到过期状态。
    let disposed = false; // 新增代码+OpenAIConnectDialog：记录本轮轮询是否失效；如果没有这行，关闭弹窗后迟到响应可能 setState。
    async function pollAuthAttempt(): Promise<void> { // 新增代码+OpenAIConnectDialog：函数段开始，执行一次 auth-attempt 状态刷新；如果没有这段，轮询逻辑会散落在定时器里。
      try { // 新增代码+OpenAIConnectDialog：捕获 status 请求失败；如果没有这行，网络错误会变成未捕获 Promise。
        const payload = await pollingClient.providerAuthAttemptStatus(activeAttemptId); // 修改代码+OpenAIConnectPollTail：用非可选 client 读取后端 auth-attempt 状态；如果没有这行，等待页没有事实源且 lint 会继续失败。
        if (disposed) { // 新增代码+OpenAIConnectDialog：丢弃已经失效的响应；如果没有这行，关闭弹窗后仍可能更新状态。
          return; // 新增代码+OpenAIConnectDialog：失效时直接退出；如果没有这行，后续仍会 setState。
        } // 新增代码+OpenAIConnectDialog：失效判断结束；如果没有这行，条件块语法不完整。
        const decision = authAttemptPollDecision(payload.attempt.status); // 新增代码+OpenAIConnectPollRaceFix：根据状态计算轮询动作；如果没有这行，complete/pending/error 的顺序会继续写死在副作用里。
        if (decision.refreshProviderSettings) { // 新增代码+OpenAIConnectPollRaceFix：complete 状态先进入 catalog 刷新分支；如果没有这行，授权完成后 provider 行不会同步已连接状态。
          const nextPayload = await pollingClient.providerSettings(); // 修改代码+OpenAIConnectPollTail：用非可选 client 重新读取 provider catalog；如果没有这行，已连接状态不会显示且 lint 会继续失败。
          if (!disposed) { // 新增代码+OpenAIConnectDialog：完成刷新也要检查本轮是否仍有效；如果没有这行，关闭后可能更新状态。
            setProviderPayload(nextPayload); // 新增代码+OpenAIConnectDialog：保存刷新后的 catalog；如果没有这行，Provider 行状态不变。
            setConnectAuthAttempt(null); // 新增代码+OpenAIConnectDialog：清空完成的 attempt；如果没有这行，下次打开可能看到旧状态。
            setConnectProvider(null); // 新增代码+OpenAIConnectDialog：完成后关闭连接弹窗；如果没有这行，用户会停留在已完成等待页。
          } // 新增代码+OpenAIConnectDialog：完成有效性判断结束；如果没有这行，条件块语法不完整。
          return; // 新增代码+OpenAIConnectPollRaceFix：complete 已处理完毕后退出本轮轮询；如果没有这行，后续可能把完成态重新写回等待页。
        } // 新增代码+OpenAIConnectPollRaceFix：catalog 刷新分支结束；如果没有这行，条件块语法不完整。
        if (decision.keepAttemptVisibleBeforeRefresh) { // 新增代码+OpenAIConnectPollRaceFix：只在非 complete 状态写回 attempt；如果没有这行，complete 会先触发 effect cleanup 并阻断 catalog 刷新落地。
          setConnectAuthAttempt(payload.attempt); // 修改代码+OpenAIConnectPollRaceFix：保存仍需展示的 attempt 状态；如果没有这行，pending/failed/expired 的状态文案不会变化。
        } // 新增代码+OpenAIConnectPollRaceFix：attempt 写回判断结束；如果没有这行，条件块语法不完整。
        if (decision.safeErrorMessage.length > 0) { // 新增代码+OpenAIConnectPollRaceFix：只在失败或过期状态显示错误；如果没有这行，终态可能继续静默等待。
          setConnectError(safeProviderError(decision.safeErrorMessage)); // 修改代码+OpenAIConnectPollRaceFix：显示安全失败文案；如果没有这行，用户不知道 flow 已结束。
        } // 新增代码+OpenAIConnectPollRaceFix：安全错误显示分支结束；如果没有这行，条件块语法不完整。
      } catch { // 新增代码+OpenAIConnectDialog：处理轮询异常；如果没有这行，bridge 断开会打断 React 副作用。
        if (!disposed) { // 新增代码+OpenAIConnectDialog：只在轮询仍有效时显示错误；如果没有这行，关闭后可能更新状态。
          setConnectError(safeProviderError("授权状态刷新失败")); // 新增代码+OpenAIConnectDialog：显示固定安全错误；如果没有这行，底层网络或 URL 细节可能进入 GUI。
        } // 新增代码+OpenAIConnectDialog：错误有效性判断结束；如果没有这行，条件块语法不完整。
      } // 新增代码+OpenAIConnectDialog：轮询 try/catch 结束；如果没有这行，语法不完整。
    } // 新增代码+OpenAIConnectDialog：函数段结束，pollAuthAttempt 到此结束；如果没有边界说明，用户不容易看出它只轮询 status。
    void pollAuthAttempt(); // 新增代码+OpenAIConnectDialog：立即执行一次状态刷新；如果没有这行，用户至少等一个定时周期才看到变化。
    const intervalId = window.setInterval(() => { void pollAuthAttempt(); }, 1000); // 新增代码+OpenAIConnectDialog：每秒轮询一次状态；如果没有这行，等待页不会自动跟随后端完成或过期。
    return () => { // 新增代码+OpenAIConnectDialog：返回轮询清理函数；如果没有这行，弹窗关闭后定时器会泄漏。
      disposed = true; // 新增代码+OpenAIConnectDialog：标记本轮轮询失效；如果没有这行，迟到响应可能更新旧状态。
      window.clearInterval(intervalId); // 新增代码+OpenAIConnectDialog：清理定时器；如果没有这行，重复打开会累积轮询请求。
    }; // 新增代码+OpenAIConnectDialog：轮询清理函数结束；如果没有这行，return 语法不完整。
  }, [connectAuthAttempt?.attempt_id, connectAuthAttempt?.status, guiClient, open]); // 新增代码+OpenAIConnectDialog：按 attempt、client 和打开状态重建轮询；如果没有这行，切换 attempt 后会轮询旧 id。

  if (!open) { // 修改代码+ProviderSettingsPanel：处理关闭状态；如果没有这行，关闭后 overlay 仍会遮挡主界面。
    return null; // 修改代码+ProviderSettingsPanel：关闭时不渲染任何内容；如果没有这行，关闭状态仍会输出 DOM。
  } // 修改代码+ProviderSettingsPanel：关闭状态分支结束；如果没有这行，条件块语法不完整。

  async function handleConnectSubmit(authMethodId: string): Promise<void> { // 修改代码+OpenAIConnectApiKey：函数段开始，按选中的认证方式提交 API key；如果没有这段，连接弹窗会继续硬编码旧方法。
    if (guiClient === undefined || connectProvider === null || connectApiKey.trim().length === 0) { // 新增代码+ProviderSettingsPanel：检查 client、provider 和非空 key；如果没有这行，空请求可能打到后端。
      return; // 新增代码+ProviderSettingsPanel：缺少必要输入时退出；如果没有这行，后续会访问无效状态。
    } // 新增代码+ProviderSettingsPanel：提交前置检查结束；如果没有这行，条件块语法不完整。
    setConnectPending(true); // 新增代码+ProviderSettingsPanel：进入连接等待态；如果没有这行，用户可能重复提交。
    setConnectError(""); // 新增代码+ProviderSettingsPanel：清空旧连接错误；如果没有这行，成功后旧错误仍显示。
    try { // 新增代码+ProviderSettingsPanel：捕获连接失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const payload = await guiClient.connectProvider(connectProvider.id, authMethodId, { secret: connectApiKey.trim() }); // 修改代码+OpenAIConnectApiKey：提交选中方法 id 和 write-only secret 字段；如果没有这行，凭据不会按新方法选择合同进入后端 secret store。
      setProviderPayload(payload); // 新增代码+ProviderSettingsPanel：用后端返回 payload 刷新列表；如果没有这行，连接成功后 UI 状态不会更新。
      setConnectApiKey(""); // 新增代码+ProviderSettingsPanel：成功后立即清空本地 API key；如果没有这行，renderer state 会继续持有密钥。
      setConnectProvider(null); // 新增代码+ProviderSettingsPanel：关闭连接弹窗；如果没有这行，成功后用户仍停在表单。
    } catch { // 新增代码+ProviderSettingsPanel：处理连接失败；如果没有这行，失败没有可见反馈。
      setConnectError(safeProviderError("连接提供商失败")); // 新增代码+ProviderSettingsPanel：显示安全连接失败文案；如果没有这行，底层异常可能泄露敏感信息。
    } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都退出等待态；如果没有这行，按钮可能一直显示连接中。
      setConnectPending(false); // 新增代码+ProviderSettingsPanel：关闭连接等待态；如果没有这行，用户无法再次提交。
    } // 新增代码+ProviderSettingsPanel：连接清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+ProviderSettingsPanel：函数段结束，handleConnectSubmit 到此结束；如果没有这个边界，用户不容易看出连接流程范围。

  async function handleStartAuthAttempt(authMethodId: string): Promise<void> { // 新增代码+OpenAIConnectDialog：函数段开始，启动 browser/headless auth-attempt；如果没有这段，OAuth 方法点击后没有后端生命周期。
    if (guiClient === undefined || connectProvider === null) { // 新增代码+OpenAIConnectDialog：检查 client 和 provider；如果没有这行，空 provider 可能发出无效请求。
      return; // 新增代码+OpenAIConnectDialog：缺少必要上下文时退出；如果没有这行，后续会访问 undefined。
    } // 新增代码+OpenAIConnectDialog：启动前置检查结束；如果没有这行，条件块语法不完整。
    setConnectPending(true); // 新增代码+OpenAIConnectDialog：进入启动等待态；如果没有这行，用户可能重复点击 OAuth 方法。
    setConnectError(""); // 新增代码+OpenAIConnectDialog：清空旧授权错误；如果没有这行，重新尝试仍显示旧错误。
    setConnectAuthAttempt(null); // 新增代码+OpenAIConnectDialog：清空旧 attempt；如果没有这行，等待页可能短暂显示上一次确认码。
    try { // 新增代码+OpenAIConnectDialog：捕获启动失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const payload = await guiClient.startProviderAuthAttempt(connectProvider.id, authMethodId); // 新增代码+OpenAIConnectDialog：调用 start endpoint 创建 pending attempt；如果没有这行，等待页没有 attempt_id。
      setConnectAuthAttempt(payload.attempt); // 新增代码+OpenAIConnectDialog：保存后端返回的授权尝试；如果没有这行，等待页无法显示链接和确认码。
    } catch { // 新增代码+OpenAIConnectDialog：处理启动异常；如果没有这行，失败没有可见反馈。
      setConnectError(safeProviderError("启动授权失败")); // 新增代码+OpenAIConnectDialog：显示固定安全错误文案；如果没有这行，底层 URL 或 token 细节可能泄露。
    } finally { // 新增代码+OpenAIConnectDialog：无论成功失败都退出启动等待态；如果没有这行，按钮可能一直等待。
      setConnectPending(false); // 新增代码+OpenAIConnectDialog：清理启动等待态；如果没有这行，用户无法重新选择方法。
    } // 新增代码+OpenAIConnectDialog：启动清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+OpenAIConnectDialog：函数段结束，handleStartAuthAttempt 到此结束；如果没有边界说明，用户不容易看出它只启动状态机。

  async function handleCancelAuthAttempt(): Promise<void> { // 新增代码+OpenAIConnectDialog：函数段开始，取消当前 pending auth-attempt；如果没有这段，关闭或返回后后端会残留 pending。
    const attempt = connectAuthAttempt; // 新增代码+OpenAIConnectDialog：固定当前 attempt 引用；如果没有这行，异步取消可能读到被清空后的状态。
    setConnectAuthAttempt(null); // 新增代码+OpenAIConnectDialog：先清空本地等待状态；如果没有这行，用户返回方法列表时仍看到旧等待页。
    if (guiClient === undefined || attempt === null || attempt.status !== "pending") { // 新增代码+OpenAIConnectDialog：只有 pending attempt 才需要通知后端取消；如果没有这行，complete/expired 可能被重复取消。
      return; // 新增代码+OpenAIConnectDialog：无需取消时退出；如果没有这行，后续可能请求空 attempt id。
    } // 新增代码+OpenAIConnectDialog：取消前置判断结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+OpenAIConnectDialog：捕获取消请求失败；如果没有这行，关闭弹窗可能因为网络错误产生未捕获 Promise。
      await guiClient.cancelProviderAuthAttempt(attempt.attempt_id); // 新增代码+OpenAIConnectDialog：通知后端把 pending 收敛为 expired；如果没有这行，状态机会残留等待。
    } catch { // 新增代码+OpenAIConnectDialog：忽略取消异常；如果没有这行，用户关闭弹窗会被网络失败阻塞。
      setConnectError(""); // 新增代码+OpenAIConnectDialog：取消失败不显示底层错误；如果没有这行，关闭路径可能泄露无关网络细节。
    } // 新增代码+OpenAIConnectDialog：取消异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+OpenAIConnectDialog：函数段结束，handleCancelAuthAttempt 到此结束；如果没有边界说明，用户不容易看出它只负责清理 pending。

  function handleCloseConnectDialog(): void { // 新增代码+OpenAIConnectDialog：函数段开始，关闭连接弹窗并清理本地状态；如果没有这段，关闭按钮会留下 API key 或 auth attempt 状态。
    void handleCancelAuthAttempt(); // 新增代码+OpenAIConnectDialog：关闭时异步取消 pending attempt；如果没有这行，后端可能继续轮询旧尝试。
    setConnectProvider(null); // 新增代码+OpenAIConnectDialog：关闭当前 provider 弹窗；如果没有这行，弹窗不会消失。
    setConnectApiKey(""); // 新增代码+OpenAIConnectDialog：清空本地 API key；如果没有这行，renderer state 会继续持有密钥。
    setConnectError(""); // 新增代码+OpenAIConnectDialog：清空错误文案；如果没有这行，下次打开会看到旧错误。
    setConnectAuthAttempt(null); // 新增代码+OpenAIConnectDialog：清空授权尝试；如果没有这行，下次打开会看到旧确认码。
  } // 新增代码+OpenAIConnectDialog：函数段结束，handleCloseConnectDialog 到此结束；如果没有边界说明，用户不容易看出关闭清理范围。

  async function handleDisconnectProvider(provider: ProviderRowView): Promise<void> { // 新增代码+ProviderSettingsPanel：函数段开始，断开 provider；如果没有这段，已连接 provider 没有断开动作。
    if (guiClient === undefined || provider.source === "env") { // 新增代码+ProviderSettingsPanel：禁止缺 client 或 env 来源断开；如果没有这行，环境变量凭据可能被误当可删除配置。
      return; // 新增代码+ProviderSettingsPanel：不可断开时退出；如果没有这行，后续会调用错误 mutation。
    } // 新增代码+ProviderSettingsPanel：断开前置检查结束；如果没有这行，条件块语法不完整。
    setBusyProviderId(provider.id); // 新增代码+ProviderSettingsPanel：标记 provider 忙碌；如果没有这行，用户可能重复点击断开。
    try { // 新增代码+ProviderSettingsPanel：捕获断开失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const payload = await guiClient.disconnectProvider(provider.id); // 新增代码+ProviderSettingsPanel：调用断开 provider endpoint；如果没有这行，后端 secret_ref 不会清理。
      setProviderPayload(payload); // 新增代码+ProviderSettingsPanel：刷新 provider 列表；如果没有这行，断开后 UI 不会更新。
    } catch { // 新增代码+ProviderSettingsPanel：处理断开失败；如果没有这行，失败没有可见反馈。
      setProviderError(safeProviderError("提供商操作失败")); // 新增代码+ProviderSettingsPanel：显示安全操作失败文案；如果没有这行，用户不知道断开失败。
    } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都清理忙碌态；如果没有这行，按钮会一直禁用。
      setBusyProviderId(""); // 新增代码+ProviderSettingsPanel：清空忙碌 provider；如果没有这行，后续操作被阻塞。
    } // 新增代码+ProviderSettingsPanel：断开清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+ProviderSettingsPanel：函数段结束，handleDisconnectProvider 到此结束；如果没有这个边界，用户不容易看出断开流程范围。

  async function handleTestProvider(provider: ProviderRowView): Promise<void> { // 新增代码+ProviderSettingsPanel：函数段开始，测试 provider 连接；如果没有这段，测试连接按钮没有后端动作。
    if (guiClient === undefined) { // 新增代码+ProviderSettingsPanel：检查 client 是否存在；如果没有这行，缺 bridge 时会抛运行时异常。
      return; // 新增代码+ProviderSettingsPanel：缺 client 直接退出；如果没有这行，后续会访问 undefined client。
    } // 新增代码+ProviderSettingsPanel：client 检查结束；如果没有这行，条件块语法不完整。
    setBusyProviderId(provider.id); // 新增代码+ProviderSettingsPanel：标记 provider 忙碌；如果没有这行，用户可能重复点击测试。
    try { // 新增代码+ProviderSettingsPanel：捕获探针失败；如果没有这行，网络异常会变成未捕获 Promise。
      const result = await guiClient.testProviderConnection(provider.id); // 新增代码+ProviderSettingsPanel：调用 test-connection endpoint；如果没有这行，保存 key 会被误当连接成功。
      setProbeResults((current) => ({ ...current, [provider.id]: result.status })); // 新增代码+ProviderSettingsPanel：保存安全状态码；如果没有这行，测试结果不会显示在 provider 行。
    } catch { // 新增代码+ProviderSettingsPanel：处理探针请求异常；如果没有这行，失败没有可见反馈。
      setProbeResults((current) => ({ ...current, [provider.id]: "network_failed" })); // 新增代码+ProviderSettingsPanel：用安全网络失败状态兜底；如果没有这行，底层异常可能显示到 GUI。
    } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都清理忙碌态；如果没有这行，按钮会一直禁用。
      setBusyProviderId(""); // 新增代码+ProviderSettingsPanel：清空忙碌 provider；如果没有这行，后续操作被阻塞。
    } // 新增代码+ProviderSettingsPanel：探针清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+ProviderSettingsPanel：函数段结束，handleTestProvider 到此结束；如果没有这个边界，用户不容易看出测试连接流程范围。

  async function handleSaveCustomProvider(payload: CustomProviderRequest): Promise<boolean> { // 新增代码+CustomProviderDialog：函数段开始，保存自定义 provider；如果没有这段，自定义表单无法调用后端。
    if (guiClient === undefined) { // 新增代码+CustomProviderDialog：检查 client 是否存在；如果没有这行，离线状态会抛运行时异常。
      setCustomProviderError(safeProviderError("保存自定义提供商失败")); // 新增代码+CustomProviderDialog：显示安全失败文案；如果没有这行，用户不知道保存没有执行。
      return false; // 新增代码+CustomProviderDialog：缺 client 时返回失败；如果没有这行，弹窗可能误以为保存成功并清空。
    } // 新增代码+CustomProviderDialog：client 检查结束；如果没有这行，条件块语法不完整。
    setCustomProviderPending(true); // 新增代码+CustomProviderDialog：进入保存等待态；如果没有这行，用户可能重复点击保存。
    setCustomProviderError(""); // 新增代码+CustomProviderDialog：清空旧错误；如果没有这行，成功后旧错误仍可能显示。
    try { // 新增代码+CustomProviderDialog：捕获保存失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const nextPayload = await guiClient.saveCustomProvider(payload); // 新增代码+CustomProviderDialog：调用保存自定义 provider endpoint；如果没有这行，配置不会落盘。
      setProviderPayload(nextPayload); // 新增代码+CustomProviderDialog：用后端返回 catalog 刷新列表；如果没有这行，保存成功后列表不会出现新 provider。
      return true; // 新增代码+CustomProviderDialog：通知弹窗保存成功；如果没有这行，弹窗不会清理 API key/header 并关闭。
    } catch { // 新增代码+CustomProviderDialog：处理保存异常；如果没有这行，失败没有可见反馈。
      setCustomProviderError(safeProviderError("保存自定义提供商失败")); // 新增代码+CustomProviderDialog：显示固定安全错误；如果没有这行，底层 URL/header/key 可能暴露到界面。
      return false; // 新增代码+CustomProviderDialog：通知弹窗保存失败；如果没有这行，失败时用户输入会被误清空。
    } finally { // 新增代码+CustomProviderDialog：无论成功失败都退出等待态；如果没有这行，保存按钮可能一直禁用。
      setCustomProviderPending(false); // 新增代码+CustomProviderDialog：清理保存等待态；如果没有这行，用户无法再次提交。
    } // 新增代码+CustomProviderDialog：保存清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+CustomProviderDialog：函数段结束，handleSaveCustomProvider 到此结束；如果没有这个边界，用户不容易看出保存流程范围。

  async function handleToggleModelVisibility(providerId: string, modelId: string, visible: boolean): Promise<void> { // 新增代码+SettingsModelsPanel：函数段开始，保存模型可见性；如果没有这段，模型开关没有后端动作。
    if (guiClient === undefined) { // 新增代码+SettingsModelsPanel：检查 client 是否存在；如果没有这行，离线状态会抛运行时异常。
      setModelError(safeProviderError("模型可见性保存失败")); // 新增代码+SettingsModelsPanel：显示安全失败文案；如果没有这行，用户不知道保存没有执行。
      return; // 新增代码+SettingsModelsPanel：缺 client 时退出；如果没有这行，后续会访问 undefined client。
    } // 新增代码+SettingsModelsPanel：client 检查结束；如果没有这行，条件块语法不完整。
    const pendingKey = modelVisibilityKey(providerId, modelId); // 新增代码+SettingsModelsPanel：计算当前模型 pending key；如果没有这行，面板无法禁用对应开关。
    setModelPendingKeyValue(pendingKey); // 新增代码+SettingsModelsPanel：标记当前模型保存中；如果没有这行，用户可能重复切换同一模型。
    setModelError(""); // 新增代码+SettingsModelsPanel：清空旧错误；如果没有这行，成功后旧错误仍会显示。
    try { // 新增代码+SettingsModelsPanel：捕获保存失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const nextPayload = await guiClient.setModelVisibility(providerId, modelId, visible); // 新增代码+SettingsModelsPanel：调用模型可见性 endpoint；如果没有这行，开关状态不会持久化。
      setProviderPayload(nextPayload); // 新增代码+SettingsModelsPanel：用后端返回 catalog 刷新模型列表；如果没有这行，成功后 UI 不会同步真实状态。
    } catch { // 新增代码+SettingsModelsPanel：处理保存异常；如果没有这行，失败没有可见反馈。
      setModelError(safeProviderError("模型可见性保存失败")); // 新增代码+SettingsModelsPanel：显示固定安全错误；如果没有这行，用户看不到保存失败。
    } finally { // 新增代码+SettingsModelsPanel：无论成功失败都清理等待态；如果没有这行，开关可能一直禁用。
      setModelPendingKeyValue(""); // 新增代码+SettingsModelsPanel：清空 pending key；如果没有这行，后续开关会被阻塞。
    } // 新增代码+SettingsModelsPanel：保存清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+SettingsModelsPanel：函数段结束，handleToggleModelVisibility 到此结束；如果没有这个边界，用户不容易看出模型保存流程范围。

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, tabId: SettingsTabId): void { // 修改代码+ProviderSettingsPanel：函数段开始，处理页签键盘激活；如果没有这段，键盘用户只能用鼠标切换。
    if (event.key === "Enter" || event.key === " ") { // 修改代码+ProviderSettingsPanel：识别 Enter 和 Space；如果没有这行，常见按钮键盘激活不稳定。
      event.preventDefault(); // 修改代码+ProviderSettingsPanel：阻止 Space 滚动页面；如果没有这行，键盘切换可能带动背景滚动。
      setActiveTab(tabId); // 修改代码+ProviderSettingsPanel：切换当前页签；如果没有这行，键盘事件不会改变内容区。
    } // 修改代码+ProviderSettingsPanel：键盘激活分支结束；如果没有这行，条件块语法不完整。
  } // 修改代码+ProviderSettingsPanel：函数段结束，handleTabKeyDown 到此结束；如果没有这行，函数语法不完整。

  return ( // 修改代码+ProviderSettingsPanel：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="settings-dialog-overlay" role="presentation"> {/* 修改代码+ProviderSettingsPanel：渲染全屏遮罩；如果没有这层，弹窗无法覆盖完整应用。 */}
      <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title"> {/* 修改代码+ProviderSettingsPanel：渲染设置对话框语义容器；如果没有这行，读屏器无法识别模态弹窗。 */}
        <aside className="settings-dialog-sidebar" aria-label="设置分类"> {/* 修改代码+ProviderSettingsPanel：渲染弹窗左侧导航；如果没有这行，设置分类无法接近 OpenCode 截图结构。 */}
          <div className="settings-dialog-nav-group"> {/* 修改代码+ProviderSettingsPanel：渲染桌面分组容器；如果没有这层，桌面页签没有分组。 */}
            <div className="settings-dialog-nav-heading">桌面</div> {/* 修改代码+ProviderSettingsPanel：显示桌面分区标题；如果没有这行，通用和快捷键缺少分组语义。 */}
            {settingsTabs.filter((tab) => tab.section === "desktop").map((tab) => { // 修改代码+ProviderSettingsPanel：遍历桌面页签；如果没有这行，桌面分组不会生成按钮。
              const Icon = tab.Icon; // 修改代码+ProviderSettingsPanel：读取当前页签图标；如果没有这行，JSX 无法动态渲染图标。
              return ( // 修改代码+ProviderSettingsPanel：返回桌面页签按钮；如果没有这行，map 不会输出元素。
                <button aria-selected={activeTab === tab.id} className={tabButtonClassName(tab.id, activeTab)} key={tab.id} onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => handleTabKeyDown(event, tab.id)} role="tab" type="button"> {/* 修改代码+ProviderSettingsPanel：渲染桌面导航按钮；如果没有这行，用户无法切换桌面设置页。 */}
                  <Icon aria-hidden={true} size={15} /> {/* 修改代码+ProviderSettingsPanel：显示桌面页签图标；如果没有这行，导航扫描性下降。 */}
                  <span>{tab.label}</span> {/* 修改代码+ProviderSettingsPanel：显示桌面页签文本；如果没有这行，图标含义不够明确。 */}
                </button> // 修改代码+ProviderSettingsPanel：桌面页签按钮结束；如果没有这行，JSX 结构不完整。
              ); // 修改代码+ProviderSettingsPanel：桌面页签返回结束；如果没有这行，回调语法不完整。
            })} {/* 修改代码+ProviderSettingsPanel：桌面页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
          </div> {/* 修改代码+ProviderSettingsPanel：桌面分组容器结束；如果没有这行，JSX 结构不完整。 */}
          <div className="settings-dialog-nav-group"> {/* 修改代码+ProviderSettingsPanel：渲染服务器分组容器；如果没有这层，Provider 和 Models 页签没有分组。 */}
            <div className="settings-dialog-nav-heading">服务器</div> {/* 修改代码+ProviderSettingsPanel：显示服务器分区标题；如果没有这行，Provider/模型设置缺少分组语义。 */}
            {settingsTabs.filter((tab) => tab.section === "server").map((tab) => { // 修改代码+ProviderSettingsPanel：遍历服务器页签；如果没有这行，服务器分组不会生成按钮。
              const Icon = tab.Icon; // 修改代码+ProviderSettingsPanel：读取当前页签图标；如果没有这行，JSX 无法动态渲染图标。
              return ( // 修改代码+ProviderSettingsPanel：返回服务器页签按钮；如果没有这行，map 不会输出元素。
                <button aria-selected={activeTab === tab.id} className={tabButtonClassName(tab.id, activeTab)} key={tab.id} onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => handleTabKeyDown(event, tab.id)} role="tab" type="button"> {/* 修改代码+ProviderSettingsPanel：渲染服务器导航按钮；如果没有这行，用户无法切换 Provider 或模型页。 */}
                  <Icon aria-hidden={true} size={15} /> {/* 修改代码+ProviderSettingsPanel：显示服务器页签图标；如果没有这行，导航扫描性下降。 */}
                  <span>{tab.label}</span> {/* 修改代码+ProviderSettingsPanel：显示服务器页签文本；如果没有这行，图标含义不够明确。 */}
                </button> // 修改代码+ProviderSettingsPanel：服务器页签按钮结束；如果没有这行，JSX 结构不完整。
              ); // 修改代码+ProviderSettingsPanel：服务器页签返回结束；如果没有这行，回调语法不完整。
            })} {/* 修改代码+ProviderSettingsPanel：服务器页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
          </div> {/* 修改代码+ProviderSettingsPanel：服务器分组容器结束；如果没有这行，JSX 结构不完整。 */}
          <footer className="settings-dialog-footer"> {/* 修改代码+ProviderSettingsPanel：渲染设置弹窗 footer；如果没有这行，产品名和版本没有固定位置。 */}
            <strong>OpenHarness Desktop</strong> {/* 修改代码+ProviderSettingsPanel：显示桌面壳产品名；如果没有这行，弹窗身份不清楚。 */}
            <span>v{version}</span> {/* 修改代码+ProviderSettingsPanel：显示 package 版本；如果没有这行，用户无法确认当前桌面版本。 */}
          </footer> {/* 修改代码+ProviderSettingsPanel：footer 结束；如果没有这行，JSX 结构不完整。 */}
        </aside> {/* 修改代码+ProviderSettingsPanel：左侧导航结束；如果没有这行，JSX 结构不完整。 */}
        <section className="settings-dialog-main"> {/* 修改代码+ProviderSettingsPanel：渲染右侧内容区；如果没有这层，页签内容没有稳定布局。 */}
          <header className="settings-dialog-header"> {/* 修改代码+ProviderSettingsPanel：渲染弹窗标题行；如果没有这层，标题和关闭按钮无法对齐。 */}
            <h2 id="settings-dialog-title">{panelTitle(activeTab)}</h2> {/* 修改代码+ProviderSettingsPanel：显示当前页标题；如果没有这行，用户不知道当前设置页。 */}
            <button aria-label="关闭设置" className="settings-dialog-close" onClick={onClose} title="关闭设置" type="button"> {/* 修改代码+ProviderSettingsPanel：渲染关闭按钮；如果没有这行，鼠标用户无法关闭弹窗。 */}
              <X aria-hidden={true} size={16} /> {/* 修改代码+ProviderSettingsPanel：显示关闭图标；如果没有这行，关闭按钮意图不够直观。 */}
            </button> {/* 修改代码+ProviderSettingsPanel：关闭按钮结束；如果没有这行，JSX 结构不完整。 */}
          </header> {/* 修改代码+ProviderSettingsPanel：标题行结束；如果没有这行，JSX 结构不完整。 */}
          {visibleSecretWarning.length > 0 ? ( // 修改代码+ProviderSettingsPanel：只在 dev_json 场景显示密钥存储警告；如果没有这行，生产安全提示会常驻或缺失。
            <div className="settings-dialog-warning" role="status"> {/* 修改代码+ProviderSettingsPanel：渲染密钥存储警告条；如果没有这层，开发密钥风险不够显眼。 */}
              <ShieldAlert aria-hidden={true} size={16} /> {/* 修改代码+ProviderSettingsPanel：显示警告图标；如果没有这行，风险提示扫描性下降。 */}
              <span>{visibleSecretWarning}</span> {/* 修改代码+ProviderSettingsPanel：显示后端返回的风险文案；如果没有这行，用户不知道 dev_json 的安全含义。 */}
            </div> // 修改代码+ProviderSettingsPanel：密钥存储警告条结束；如果没有这行，JSX 结构不完整。
          ) : null} {/* 修改代码+ProviderSettingsPanel：警告条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
          <div className="settings-dialog-content" role="tabpanel"> {/* 修改代码+ProviderSettingsPanel：渲染当前页签内容容器；如果没有这层，内容区无法稳定滚动。 */}
            {panelContent(activeTab, providerViewModel, providerLoading, providerError, busyProviderId, probeResults, modelPendingKeyValue, modelError, () => { void refreshProviderSettings(); }, (provider) => { setConnectProvider(provider); setConnectError(""); setConnectAuthAttempt(null); }, (provider) => { void handleDisconnectProvider(provider); }, (provider) => { void handleTestProvider(provider); }, () => { setCustomProviderOpen(true); setCustomProviderError(""); }, (providerId, modelId, visible) => { void handleToggleModelVisibility(providerId, modelId, visible); })} {/* 修改代码+OpenAIConnectDialog：渲染当前页签内容并打开 provider 连接时清空旧 attempt；如果没有这行，模型开关无法调用 bridge 或连接弹窗可能显示旧确认码。 */}
          </div> {/* 修改代码+ProviderSettingsPanel：内容容器结束；如果没有这行，JSX 结构不完整。 */}
        </section> {/* 修改代码+ProviderSettingsPanel：右侧内容区结束；如果没有这行，JSX 结构不完整。 */}
        <ProviderConnectDialog open={connectProvider !== null} provider={connectProvider} apiKey={connectApiKey} pending={connectPending} errorMessage={connectError} authAttempt={connectAuthAttempt} onApiKeyChange={setConnectApiKey} onClose={handleCloseConnectDialog} onSubmit={(authMethodId) => { void handleConnectSubmit(authMethodId); }} onStartAuthAttempt={(authMethodId) => { void handleStartAuthAttempt(authMethodId); }} onCancelAuthAttempt={() => { void handleCancelAuthAttempt(); }} /> {/* 修改代码+OpenAIConnectDialog：渲染受控连接弹窗并接入 API key 与 auth-attempt 两条路径；如果没有这行，browser/headless 等待页无法启动或取消后端状态机。 */}
        <CustomProviderDialog open={customProviderOpen} pending={customProviderPending} errorMessage={customProviderError} onClose={() => { setCustomProviderOpen(false); setCustomProviderError(""); }} onSave={(payload) => handleSaveCustomProvider(payload)} /> {/* 新增代码+CustomProviderDialog：渲染自定义 provider 受控弹窗；如果没有这行，自定义入口不会显示字段或保存配置。 */}
      </section> {/* 修改代码+ProviderSettingsPanel：设置对话框结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 修改代码+ProviderSettingsPanel：全屏遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+ProviderSettingsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+ProviderSettingsPanel：函数段结束，SettingsDialog 到此结束；如果没有这个边界，用户不容易看出弹窗范围。
