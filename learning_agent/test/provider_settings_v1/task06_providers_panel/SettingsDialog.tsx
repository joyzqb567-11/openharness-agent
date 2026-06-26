import { useEffect, useState, type KeyboardEvent } from "react"; // 修改代码+ProviderSettingsPanel：导入弹窗状态和键盘副作用工具；如果没有这行，标签切换、数据加载和 Escape 关闭都无法实现。
import { Cpu, Keyboard, Monitor, Server, ShieldAlert, SlidersHorizontal, X } from "lucide-react"; // 修改代码+ProviderSettingsPanel：导入设置导航需要的图标；如果没有这行，设置页扫描性会退化成纯文字。
import type { GuiProviderSettingsPayload, ProviderConnectionProbePayload } from "../../api/guiProviderTypes"; // 新增代码+ProviderSettingsPanel：导入 provider settings bridge 合同；如果没有这行，弹窗容器无法类型化后端响应。
import { buildProviderSettingsViewModel, type ProviderRowView, type ProviderSettingsViewModel } from "../../state/providerSettingsStore"; // 新增代码+ProviderSettingsPanel：导入 provider view model builder；如果没有这行，弹窗会直接消费后端 snake_case payload。
import packageInfo from "../../../package.json"; // 修改代码+ProviderSettingsPanel：读取桌面 package 版本；如果没有这行，footer 无法自动显示真实版本。
import { ProviderConnectDialog } from "./ProviderConnectDialog"; // 新增代码+ProviderSettingsPanel：导入连接弹窗；如果没有这行，Provider 列表无法收集 API key。
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
  disconnectProvider: (providerId: string) => Promise<GuiProviderSettingsPayload>; // 新增代码+ProviderSettingsPanel：声明断开 provider 方法；如果没有这行，已连接 provider 无法断开。
  testProviderConnection: (providerId: string) => Promise<ProviderConnectionProbePayload>; // 新增代码+ProviderSettingsPanel：声明测试连接方法；如果没有这行，测试按钮无法调用 bridge。
}; // 新增代码+ProviderSettingsPanel：ProviderSettingsClient 类型结束；如果没有这行，TypeScript 类型语法不完整。

type SettingsDialogProps = { // 修改代码+ProviderSettingsPanel：类型段开始，定义设置弹窗输入；如果没有这段，AppShell 不知道如何控制弹窗。
  open: boolean; // 修改代码+ProviderSettingsPanel：保存弹窗是否打开；如果没有这行，关闭状态无法从 DOM 移除。
  onClose: () => void; // 修改代码+ProviderSettingsPanel：保存关闭回调；如果没有这行，关闭按钮和 Escape 无法把状态交回 AppShell。
  version?: string; // 修改代码+ProviderSettingsPanel：允许测试或打包流程覆盖版本；如果没有这行，测试只能依赖 package JSON。
  secretStoreWarning?: string; // 修改代码+ProviderSettingsPanel：保存外部传入的开发密钥存储警告；如果没有这行，纯 shell 测试无法注入警告。
  guiClient?: ProviderSettingsClient; // 新增代码+ProviderSettingsPanel：保存可选 provider settings client；如果没有这行，弹窗无法通过 bridge 读取或修改 provider 状态。
}; // 修改代码+ProviderSettingsPanel：SettingsDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

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

function panelContent(activeTab: SettingsTabId, providerViewModel: ProviderSettingsViewModel | null, providerLoading: boolean, providerError: string, busyProviderId: string, probeResults: Record<string, string>, onRetry: () => void, onConnectProvider: (provider: ProviderRowView) => void, onDisconnectProvider: (provider: ProviderRowView) => void, onTestProvider: (provider: ProviderRowView) => void, onOpenCustomProvider: () => void): JSX.Element { // 修改代码+ProviderSettingsPanel：函数段开始，渲染当前页签内容；如果没有这段，右侧内容会散落在主组件中。
  if (activeTab === "providers") { // 修改代码+ProviderSettingsPanel：处理默认提供商页；如果没有这行，Provider Settings 面板不会显示。
    return <SettingsProvidersPanel viewModel={providerViewModel} loading={providerLoading} errorMessage={providerError} busyProviderId={busyProviderId} probeResults={probeResults} onRetry={onRetry} onConnectProvider={onConnectProvider} onDisconnectProvider={onDisconnectProvider} onTestProvider={onTestProvider} onOpenCustomProvider={onOpenCustomProvider} />; // 新增代码+ProviderSettingsPanel：渲染真实 provider 列表；如果没有这行，设置页无法展示或操作提供商。
  } // 修改代码+ProviderSettingsPanel：提供商分支结束；如果没有这行，条件块语法不完整。
  if (activeTab === "models") { // 修改代码+ProviderSettingsPanel：处理模型页；如果没有这行，模型页没有独立占位。
    return <div className="settings-dialog-placeholder">等待模型数据</div>; // 修改代码+ProviderSettingsPanel：渲染模型数据占位；如果没有这行，真实模型接入前内容区会空白。
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

  if (!open) { // 修改代码+ProviderSettingsPanel：处理关闭状态；如果没有这行，关闭后 overlay 仍会遮挡主界面。
    return null; // 修改代码+ProviderSettingsPanel：关闭时不渲染任何内容；如果没有这行，关闭状态仍会输出 DOM。
  } // 修改代码+ProviderSettingsPanel：关闭状态分支结束；如果没有这行，条件块语法不完整。

  async function handleConnectSubmit(): Promise<void> { // 新增代码+ProviderSettingsPanel：函数段开始，提交 API key 连接 provider；如果没有这段，连接弹窗没有后端动作。
    if (guiClient === undefined || connectProvider === null || connectApiKey.trim().length === 0) { // 新增代码+ProviderSettingsPanel：检查 client、provider 和非空 key；如果没有这行，空请求可能打到后端。
      return; // 新增代码+ProviderSettingsPanel：缺少必要输入时退出；如果没有这行，后续会访问无效状态。
    } // 新增代码+ProviderSettingsPanel：提交前置检查结束；如果没有这行，条件块语法不完整。
    setConnectPending(true); // 新增代码+ProviderSettingsPanel：进入连接等待态；如果没有这行，用户可能重复提交。
    setConnectError(""); // 新增代码+ProviderSettingsPanel：清空旧连接错误；如果没有这行，成功后旧错误仍显示。
    try { // 新增代码+ProviderSettingsPanel：捕获连接失败；如果没有这行，bridge 错误会变成未捕获 Promise。
      const payload = await guiClient.connectProvider(connectProvider.id, "api_key", { api_key: connectApiKey.trim() }); // 新增代码+ProviderSettingsPanel：提交 write-only API key；如果没有这行，凭据不会进入后端 secret store。
      setProviderPayload(payload); // 新增代码+ProviderSettingsPanel：用后端返回 payload 刷新列表；如果没有这行，连接成功后 UI 状态不会更新。
      setConnectApiKey(""); // 新增代码+ProviderSettingsPanel：成功后立即清空本地 API key；如果没有这行，renderer state 会继续持有密钥。
      setConnectProvider(null); // 新增代码+ProviderSettingsPanel：关闭连接弹窗；如果没有这行，成功后用户仍停在表单。
    } catch { // 新增代码+ProviderSettingsPanel：处理连接失败；如果没有这行，失败没有可见反馈。
      setConnectError(safeProviderError("连接提供商失败")); // 新增代码+ProviderSettingsPanel：显示安全连接失败文案；如果没有这行，底层异常可能泄露敏感信息。
    } finally { // 新增代码+ProviderSettingsPanel：无论成功失败都退出等待态；如果没有这行，按钮可能一直显示连接中。
      setConnectPending(false); // 新增代码+ProviderSettingsPanel：关闭连接等待态；如果没有这行，用户无法再次提交。
    } // 新增代码+ProviderSettingsPanel：连接清理结束；如果没有这行，try/catch/finally 语法不完整。
  } // 新增代码+ProviderSettingsPanel：函数段结束，handleConnectSubmit 到此结束；如果没有这个边界，用户不容易看出连接流程范围。

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
            {panelContent(activeTab, providerViewModel, providerLoading, providerError, busyProviderId, probeResults, () => { void refreshProviderSettings(); }, (provider) => { setConnectProvider(provider); setConnectError(""); }, (provider) => { void handleDisconnectProvider(provider); }, (provider) => { void handleTestProvider(provider); }, () => { setConnectError(""); })} {/* 修改代码+ProviderSettingsPanel：渲染当前页签内容并注入 provider 操作；如果没有这行，列表按钮无法调用 bridge。 */}
          </div> {/* 修改代码+ProviderSettingsPanel：内容容器结束；如果没有这行，JSX 结构不完整。 */}
        </section> {/* 修改代码+ProviderSettingsPanel：右侧内容区结束；如果没有这行，JSX 结构不完整。 */}
        <ProviderConnectDialog open={connectProvider !== null} provider={connectProvider} apiKey={connectApiKey} pending={connectPending} errorMessage={connectError} onApiKeyChange={setConnectApiKey} onClose={() => { setConnectProvider(null); setConnectApiKey(""); setConnectError(""); }} onSubmit={() => { void handleConnectSubmit(); }} /> {/* 新增代码+ProviderSettingsPanel：渲染受控连接弹窗；如果没有这行，连接按钮无法收集并提交 API key。 */}
      </section> {/* 修改代码+ProviderSettingsPanel：设置对话框结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 修改代码+ProviderSettingsPanel：全屏遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+ProviderSettingsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+ProviderSettingsPanel：函数段结束，SettingsDialog 到此结束；如果没有这个边界，用户不容易看出弹窗范围。
