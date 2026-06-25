import { useEffect, useState, type KeyboardEvent } from "react"; // 新增代码+ProviderSettingsShell：导入弹窗状态和键盘副作用工具；如果没有这行，标签切换和 Escape 关闭都无法实现。
import { Cpu, Keyboard, Monitor, Server, ShieldAlert, SlidersHorizontal, X } from "lucide-react"; // 新增代码+ProviderSettingsShell：导入设置导航需要的图标；如果没有这行，设置页扫描性会退化成纯文字。
import packageInfo from "../../../package.json"; // 新增代码+ProviderSettingsShell：读取桌面 package 版本；如果没有这行，footer 无法自动显示真实版本。

type SettingsTabId = "general" | "shortcuts" | "server" | "providers" | "models"; // 新增代码+ProviderSettingsShell：定义设置页签 id；如果没有这行，active tab 会变成不受约束的字符串。

type SettingsTab = { // 新增代码+ProviderSettingsShell：类型段开始，描述左侧设置页签；如果没有这段，导航数组字段含义不清楚。
  id: SettingsTabId; // 新增代码+ProviderSettingsShell：保存页签 id；如果没有这行，点击后无法定位内容。
  label: string; // 新增代码+ProviderSettingsShell：保存页签显示名；如果没有这行，导航只剩机器码。
  section: "desktop" | "server"; // 新增代码+ProviderSettingsShell：保存页签所属分区；如果没有这行，桌面和服务器分组无法稳定渲染。
  Icon: typeof Monitor; // 新增代码+ProviderSettingsShell：保存页签图标组件；如果没有这行，导航图标无法类型化。
}; // 新增代码+ProviderSettingsShell：SettingsTab 类型结束；如果没有这行，TypeScript 类型语法不完整。

type SettingsDialogProps = { // 新增代码+ProviderSettingsShell：类型段开始，定义设置弹窗输入；如果没有这段，AppShell 不知道如何控制弹窗。
  open: boolean; // 新增代码+ProviderSettingsShell：保存弹窗是否打开；如果没有这行，关闭状态无法从 DOM 移除。
  onClose: () => void; // 新增代码+ProviderSettingsShell：保存关闭回调；如果没有这行，关闭按钮和 Escape 无法把状态交回 AppShell。
  version?: string; // 新增代码+ProviderSettingsShell：允许测试或打包流程覆盖版本；如果没有这行，测试只能依赖 package JSON。
  secretStoreWarning?: string; // 新增代码+ProviderSettingsShell：保存开发密钥存储警告；如果没有这行，dev_json 风险无法在设置页展示。
}; // 新增代码+ProviderSettingsShell：SettingsDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

const settingsTabs: SettingsTab[] = [ // 新增代码+ProviderSettingsShell：定义设置页签顺序；如果没有这段，左侧导航会散落在 JSX 中。
  { id: "general", label: "通用", section: "desktop", Icon: SlidersHorizontal }, // 新增代码+ProviderSettingsShell：声明通用页签；如果没有这行，桌面设置缺少基础入口。
  { id: "shortcuts", label: "快捷键", section: "desktop", Icon: Keyboard }, // 新增代码+ProviderSettingsShell：声明快捷键页签；如果没有这行，后续快捷键设置没有固定位置。
  { id: "server", label: "服务器", section: "server", Icon: Server }, // 新增代码+ProviderSettingsShell：声明服务器页签；如果没有这行，后端连接配置没有固定位置。
  { id: "providers", label: "提供商", section: "server", Icon: Cpu }, // 新增代码+ProviderSettingsShell：声明提供商页签；如果没有这行，大模型提供商管理没有默认入口。
  { id: "models", label: "模型", section: "server", Icon: Monitor }, // 新增代码+ProviderSettingsShell：声明模型页签；如果没有这行，模型可见性管理没有位置。
]; // 新增代码+ProviderSettingsShell：设置页签数组结束；如果没有这行，TypeScript 数组语法不完整。

function tabButtonClassName(tabId: SettingsTabId, activeTab: SettingsTabId): string { // 新增代码+ProviderSettingsShell：函数段开始，生成页签按钮 class；如果没有这段，active 样式判断会散落在 JSX 中。
  return `settings-dialog-tab${tabId === activeTab ? " settings-dialog-tab-active" : ""}`; // 新增代码+ProviderSettingsShell：根据 active 状态返回 class；如果没有这行，当前页签无法高亮。
} // 新增代码+ProviderSettingsShell：函数段结束，tabButtonClassName 到此结束；如果没有这行，函数语法不完整。

function panelTitle(activeTab: SettingsTabId): string { // 新增代码+ProviderSettingsShell：函数段开始，生成内容区标题；如果没有这段，标题会和页签数据重复手写。
  return settingsTabs.find((tab) => tab.id === activeTab)?.label ?? "提供商"; // 新增代码+ProviderSettingsShell：按 active tab 查找标题并提供兜底；如果没有这行，异常 tab 会让标题空白。
} // 新增代码+ProviderSettingsShell：函数段结束，panelTitle 到此结束；如果没有这行，函数语法不完整。

function panelContent(activeTab: SettingsTabId): JSX.Element { // 新增代码+ProviderSettingsShell：函数段开始，渲染当前页签占位内容；如果没有这段，Task 5 弹窗会只有导航没有内容区。
  if (activeTab === "providers") { // 新增代码+ProviderSettingsShell：处理默认提供商页；如果没有这行，默认页无法显示 Provider Settings 入口。
    return <div className="settings-dialog-placeholder">等待 Provider 数据</div>; // 新增代码+ProviderSettingsShell：渲染提供商数据占位；如果没有这行，真实数据接入前内容区会空白。
  } // 新增代码+ProviderSettingsShell：提供商分支结束；如果没有这行，条件块语法不完整。
  if (activeTab === "models") { // 新增代码+ProviderSettingsShell：处理模型页；如果没有这行，模型页没有独立占位。
    return <div className="settings-dialog-placeholder">等待模型数据</div>; // 新增代码+ProviderSettingsShell：渲染模型数据占位；如果没有这行，真实模型接入前内容区会空白。
  } // 新增代码+ProviderSettingsShell：模型分支结束；如果没有这行，条件块语法不完整。
  return <div className="settings-dialog-placeholder">OpenHarness Desktop</div>; // 新增代码+ProviderSettingsShell：渲染其他设置页占位；如果没有这行，非 Provider 页切换后会空白。
} // 新增代码+ProviderSettingsShell：函数段结束，panelContent 到此结束；如果没有这行，函数语法不完整。

export function SettingsDialog({ open, onClose, version = packageInfo.version, secretStoreWarning = "" }: SettingsDialogProps): JSX.Element | null { // 新增代码+ProviderSettingsShell：函数段开始，渲染 OpenHarness Desktop 设置弹窗；如果没有这段，左下角设置入口没有成熟 GUI 外壳。
  const [activeTab, setActiveTab] = useState<SettingsTabId>("providers"); // 新增代码+ProviderSettingsShell：保存当前页签并默认提供商页；如果没有这行，弹窗无法默认打开 Provider 设置。
  useEffect(() => { // 新增代码+ProviderSettingsShell：副作用段开始，绑定 Escape 关闭弹窗；如果没有这段，键盘关闭验收无法通过。
    if (!open) { // 新增代码+ProviderSettingsShell：弹窗关闭时不绑定事件；如果没有这行，隐藏弹窗也会监听键盘。
      return undefined; // 新增代码+ProviderSettingsShell：关闭状态返回空清理；如果没有这行，React 副作用返回值不清晰。
    } // 新增代码+ProviderSettingsShell：关闭状态分支结束；如果没有这行，条件块语法不完整。
    function handleWindowKeyDown(event: globalThis.KeyboardEvent): void { // 新增代码+ProviderSettingsShell：函数段开始，处理全局键盘事件；如果没有这段，Escape 键不会关闭弹窗。
      if (event.key === "Escape") { // 新增代码+ProviderSettingsShell：只响应 Escape；如果没有这行，任何按键都可能关闭设置页。
        onClose(); // 新增代码+ProviderSettingsShell：调用关闭回调；如果没有这行，键盘事件不会改变 AppShell 状态。
      } // 新增代码+ProviderSettingsShell：Escape 分支结束；如果没有这行，条件块语法不完整。
    } // 新增代码+ProviderSettingsShell：函数段结束，handleWindowKeyDown 到此结束；如果没有这行，函数语法不完整。
    window.addEventListener("keydown", handleWindowKeyDown); // 新增代码+ProviderSettingsShell：注册键盘监听；如果没有这行，Escape 键不会被捕获。
    return () => { // 新增代码+ProviderSettingsShell：返回清理函数；如果没有这行，弹窗关闭后监听器会泄漏。
      window.removeEventListener("keydown", handleWindowKeyDown); // 新增代码+ProviderSettingsShell：移除键盘监听；如果没有这行，反复打开会累积事件处理器。
    }; // 新增代码+ProviderSettingsShell：清理函数结束；如果没有这行，return 语法不完整。
  }, [onClose, open]); // 新增代码+ProviderSettingsShell：按打开状态和关闭回调更新副作用；如果没有这行，监听器会使用过期回调。
  if (!open) { // 新增代码+ProviderSettingsShell：处理关闭状态；如果没有这行，关闭后 overlay 仍会遮挡主界面。
    return null; // 新增代码+ProviderSettingsShell：关闭时不渲染任何内容；如果没有这行，关闭状态仍会输出 DOM。
  } // 新增代码+ProviderSettingsShell：关闭状态分支结束；如果没有这行，条件块语法不完整。
  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, tabId: SettingsTabId): void { // 新增代码+ProviderSettingsShell：函数段开始，处理页签键盘激活；如果没有这段，键盘用户只能用鼠标切换。
    if (event.key === "Enter" || event.key === " ") { // 新增代码+ProviderSettingsShell：识别 Enter 和 Space；如果没有这行，常见按钮键盘激活不稳定。
      event.preventDefault(); // 新增代码+ProviderSettingsShell：阻止 Space 滚动页面；如果没有这行，键盘切换可能带动背景滚动。
      setActiveTab(tabId); // 新增代码+ProviderSettingsShell：切换当前页签；如果没有这行，键盘事件不会改变内容区。
    } // 新增代码+ProviderSettingsShell：键盘激活分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+ProviderSettingsShell：函数段结束，handleTabKeyDown 到此结束；如果没有这行，函数语法不完整。
  return ( // 新增代码+ProviderSettingsShell：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="settings-dialog-overlay" role="presentation"> {/* 新增代码+ProviderSettingsShell：渲染全屏遮罩；如果没有这层，弹窗无法覆盖完整应用。 */}
      <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title"> {/* 新增代码+ProviderSettingsShell：渲染设置对话框语义容器；如果没有这行，读屏器无法识别模态弹窗。 */}
        <aside className="settings-dialog-sidebar" aria-label="设置分类"> {/* 新增代码+ProviderSettingsShell：渲染弹窗左侧导航；如果没有这行，设置分类无法接近 OpenCode 截图结构。 */}
          <div className="settings-dialog-nav-group"> {/* 新增代码+ProviderSettingsShell：渲染桌面分组容器；如果没有这层，桌面页签没有分组。 */}
            <div className="settings-dialog-nav-heading">桌面</div> {/* 新增代码+ProviderSettingsShell：显示桌面分区标题；如果没有这行，通用和快捷键缺少分组语义。 */}
            {settingsTabs.filter((tab) => tab.section === "desktop").map((tab) => { // 新增代码+ProviderSettingsShell：遍历桌面页签；如果没有这行，桌面分组不会生成按钮。
              const Icon = tab.Icon; // 新增代码+ProviderSettingsShell：读取当前页签图标；如果没有这行，JSX 无法动态渲染图标。
              return ( // 新增代码+ProviderSettingsShell：返回桌面页签按钮；如果没有这行，map 不会输出元素。
                <button aria-selected={activeTab === tab.id} className={tabButtonClassName(tab.id, activeTab)} key={tab.id} onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => handleTabKeyDown(event, tab.id)} role="tab" type="button"> {/* 新增代码+ProviderSettingsShell：渲染桌面导航按钮；如果没有这行，用户无法切换桌面设置页。 */}
                  <Icon aria-hidden={true} size={15} /> {/* 新增代码+ProviderSettingsShell：显示桌面页签图标；如果没有这行，导航扫描性下降。 */}
                  <span>{tab.label}</span> {/* 新增代码+ProviderSettingsShell：显示桌面页签文本；如果没有这行，图标含义不够明确。 */}
                </button> // 新增代码+ProviderSettingsShell：桌面页签按钮结束；如果没有这行，JSX 结构不完整。
              ); // 新增代码+ProviderSettingsShell：桌面页签返回结束；如果没有这行，回调语法不完整。
            })} {/* 新增代码+ProviderSettingsShell：桌面页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
          </div> {/* 新增代码+ProviderSettingsShell：桌面分组容器结束；如果没有这行，JSX 结构不完整。 */}
          <div className="settings-dialog-nav-group"> {/* 新增代码+ProviderSettingsShell：渲染服务器分组容器；如果没有这层，Provider 和 Models 页签没有分组。 */}
            <div className="settings-dialog-nav-heading">服务器</div> {/* 新增代码+ProviderSettingsShell：显示服务器分区标题；如果没有这行，Provider/模型设置缺少分组语义。 */}
            {settingsTabs.filter((tab) => tab.section === "server").map((tab) => { // 新增代码+ProviderSettingsShell：遍历服务器页签；如果没有这行，服务器分组不会生成按钮。
              const Icon = tab.Icon; // 新增代码+ProviderSettingsShell：读取当前页签图标；如果没有这行，JSX 无法动态渲染图标。
              return ( // 新增代码+ProviderSettingsShell：返回服务器页签按钮；如果没有这行，map 不会输出元素。
                <button aria-selected={activeTab === tab.id} className={tabButtonClassName(tab.id, activeTab)} key={tab.id} onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => handleTabKeyDown(event, tab.id)} role="tab" type="button"> {/* 新增代码+ProviderSettingsShell：渲染服务器导航按钮；如果没有这行，用户无法切换 Provider 或模型页。 */}
                  <Icon aria-hidden={true} size={15} /> {/* 新增代码+ProviderSettingsShell：显示服务器页签图标；如果没有这行，导航扫描性下降。 */}
                  <span>{tab.label}</span> {/* 新增代码+ProviderSettingsShell：显示服务器页签文本；如果没有这行，图标含义不够明确。 */}
                </button> // 新增代码+ProviderSettingsShell：服务器页签按钮结束；如果没有这行，JSX 结构不完整。
              ); // 新增代码+ProviderSettingsShell：服务器页签返回结束；如果没有这行，回调语法不完整。
            })} {/* 新增代码+ProviderSettingsShell：服务器页签遍历结束；如果没有这行，JSX 表达式不完整。 */}
          </div> {/* 新增代码+ProviderSettingsShell：服务器分组容器结束；如果没有这行，JSX 结构不完整。 */}
          <footer className="settings-dialog-footer"> {/* 新增代码+ProviderSettingsShell：渲染设置弹窗 footer；如果没有这行，产品名和版本没有固定位置。 */}
            <strong>OpenHarness Desktop</strong> {/* 新增代码+ProviderSettingsShell：显示桌面壳产品名；如果没有这行，弹窗身份不清楚。 */}
            <span>v{version}</span> {/* 新增代码+ProviderSettingsShell：显示 package 版本；如果没有这行，用户无法确认当前桌面版本。 */}
          </footer> {/* 新增代码+ProviderSettingsShell：footer 结束；如果没有这行，JSX 结构不完整。 */}
        </aside> {/* 新增代码+ProviderSettingsShell：左侧导航结束；如果没有这行，JSX 结构不完整。 */}
        <section className="settings-dialog-main"> {/* 新增代码+ProviderSettingsShell：渲染右侧内容区；如果没有这层，页签内容没有稳定布局。 */}
          <header className="settings-dialog-header"> {/* 新增代码+ProviderSettingsShell：渲染弹窗标题行；如果没有这层，标题和关闭按钮无法对齐。 */}
            <h2 id="settings-dialog-title">{panelTitle(activeTab)}</h2> {/* 新增代码+ProviderSettingsShell：显示当前页标题；如果没有这行，用户不知道当前设置页。 */}
            <button aria-label="关闭设置" className="settings-dialog-close" onClick={onClose} title="关闭设置" type="button"> {/* 新增代码+ProviderSettingsShell：渲染关闭按钮；如果没有这行，鼠标用户无法关闭弹窗。 */}
              <X aria-hidden={true} size={16} /> {/* 新增代码+ProviderSettingsShell：显示关闭图标；如果没有这行，关闭按钮意图不够直观。 */}
            </button> {/* 新增代码+ProviderSettingsShell：关闭按钮结束；如果没有这行，JSX 结构不完整。 */}
          </header> {/* 新增代码+ProviderSettingsShell：标题行结束；如果没有这行，JSX 结构不完整。 */}
          {secretStoreWarning.length > 0 ? ( // 新增代码+ProviderSettingsShell：只在 dev_json 场景显示密钥存储警告；如果没有这行，生产安全提示会常驻或缺失。
            <div className="settings-dialog-warning" role="status"> {/* 新增代码+ProviderSettingsShell：渲染密钥存储警告条；如果没有这层，开发密钥风险不够显眼。 */}
              <ShieldAlert aria-hidden={true} size={16} /> {/* 新增代码+ProviderSettingsShell：显示警告图标；如果没有这行，风险提示扫描性下降。 */}
              <span>{secretStoreWarning}</span> {/* 新增代码+ProviderSettingsShell：显示后端返回的风险文案；如果没有这行，用户不知道 dev_json 的安全含义。 */}
            </div> // 新增代码+ProviderSettingsShell：密钥存储警告条结束；如果没有这行，JSX 结构不完整。
          ) : null} {/* 新增代码+ProviderSettingsShell：警告条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
          <div className="settings-dialog-content" role="tabpanel"> {/* 新增代码+ProviderSettingsShell：渲染当前页签内容容器；如果没有这层，内容区无法稳定滚动。 */}
            {panelContent(activeTab)} {/* 新增代码+ProviderSettingsShell：渲染当前页签内容；如果没有这行，点击导航不会改变右侧内容。 */}
          </div> {/* 新增代码+ProviderSettingsShell：内容容器结束；如果没有这行，JSX 结构不完整。 */}
        </section> {/* 新增代码+ProviderSettingsShell：右侧内容区结束；如果没有这行，JSX 结构不完整。 */}
      </section> {/* 新增代码+ProviderSettingsShell：设置对话框结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+ProviderSettingsShell：全屏遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+ProviderSettingsShell：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+ProviderSettingsShell：函数段结束，SettingsDialog 到此结束；如果没有这个边界，用户不容易看出弹窗范围。
