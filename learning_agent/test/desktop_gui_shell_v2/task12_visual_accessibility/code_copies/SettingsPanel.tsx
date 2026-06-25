import { Clipboard, ServerCog } from "lucide-react"; // 新增代码+DesktopSettingsPanel：引入设置页图标；如果没有这行，复制和后端区域缺少熟悉符号。
import { buildSettingsViewModel } from "../state/settingsStore"; // 新增代码+DesktopSettingsPanel：引入设置 view model helper；如果没有这行，组件会直接揉后端 payload。

type SettingsPanelProps = { // 新增代码+DesktopSettingsPanel：类型段开始，定义设置面板输入；如果没有这段类型，调用方不知道要传哪些数据。
  bridgeBaseUrl?: string; // 新增代码+DesktopSettingsPanel：保存 bridge 基础地址；如果没有这行，面板无法显示 host/port。
  health?: unknown; // 新增代码+DesktopSettingsPanel：保存 V2 health payload；如果没有这行，设置页没有 provider 和 feature flags。
  diagnostics?: unknown; // 新增代码+DesktopSettingsPanel：保存 V2 diagnostics payload；如果没有这行，设置页拿不到日志和证据目录。
  themeChoice?: string; // 新增代码+DesktopSettingsPanel：保存主题选择；如果没有这行，设置页无法展示当前视觉偏好。
}; // 新增代码+DesktopSettingsPanel：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

function copyText(text: string): void { // 新增代码+DesktopSettingsPanel：函数段开始，复制设置里的路径文本；如果没有这段函数，复制按钮只有外观没有动作。
  if (typeof navigator === "undefined" || !navigator.clipboard) { // 新增代码+DesktopSettingsPanel：检查剪贴板 API；如果没有这行，测试或旧环境会抛异常。
    return; // 新增代码+DesktopSettingsPanel：剪贴板不可用时安静退出；如果没有这行，点击复制会报错。
  } // 新增代码+DesktopSettingsPanel：剪贴板保护结束；如果没有这行，条件块语法不完整。
  void navigator.clipboard.writeText(text); // 新增代码+DesktopSettingsPanel：写入剪贴板；如果没有这行，用户无法复制日志或证据路径。
} // 新增代码+DesktopSettingsPanel：函数段结束，copyText 到此结束；如果没有这个边界，初学者不容易看出复制动作范围。

export function SettingsPanel({ bridgeBaseUrl = "", health = {}, diagnostics = {}, themeChoice = "跟随系统" }: SettingsPanelProps): JSX.Element { // 新增代码+DesktopSettingsPanel：函数段开始，渲染右侧设置页；如果没有这段，Task 11 的设置 UI 不存在。
  const model = buildSettingsViewModel({ bridgeBaseUrl, health, diagnostics, themeChoice }); // 新增代码+DesktopSettingsPanel：把后端 payload 合成稳定 view model；如果没有这行，JSX 会到处做兜底判断。
  return ( // 新增代码+DesktopSettingsPanel：返回设置面板结构；如果没有这行，组件不会输出 UI。
    <section className="settings-panel" aria-label="设置"> {/* 新增代码+DesktopSettingsPanel：设置面板语义容器；如果没有这一层，读屏器无法识别设置区域。 */}
      <div className="inspector-header"> {/* 新增代码+DesktopSettingsPanel：设置标题行；如果没有这一层，标题和状态无法稳定对齐。 */}
        <h2>设置</h2> {/* 新增代码+DesktopSettingsPanel：显示设置标题；如果没有这行，用户不知道当前页签用途。 */}
        <span>{model.themeChoice}</span> {/* 新增代码+DesktopSettingsPanel：显示当前主题选择；如果没有这行，主题设置没有可见状态。 */}
      </div> {/* 新增代码+DesktopSettingsPanel：标题行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="settings-section"> {/* 新增代码+DesktopSettingsPanel：模型和 bridge 区域容器；如果没有这一层，信息块会堆成散文。 */}
        <div className="settings-section-title"> {/* 新增代码+DesktopSettingsPanel：区域标题行；如果没有这一层，后端设置缺少层级。 */}
          <ServerCog size={14} aria-hidden="true" /> {/* 新增代码+DesktopSettingsPanel：后端图标；如果没有这行，设置页扫描性下降。 */}
          <strong>后端</strong> {/* 新增代码+DesktopSettingsPanel：区域标题文字；如果没有这行，用户无法区分后端配置。 */}
        </div> {/* 新增代码+DesktopSettingsPanel：区域标题行结束；如果没有这行，JSX 结构不完整。 */}
        <div className="diagnostic-list"> {/* 新增代码+DesktopSettingsPanel：设置键值列表；如果没有这一层，字段没有统一排版。 */}
          <div className="diagnostic-row"><strong>Provider</strong><span>{model.provider}</span></div> {/* 新增代码+DesktopSettingsPanel：显示 provider；如果没有这行，用户不知道当前后端来源。 */}
          <div className="diagnostic-row"><strong>Model</strong><span>{model.model}</span></div> {/* 新增代码+DesktopSettingsPanel：显示 model；如果没有这行，用户不知道当前模型。 */}
          <div className="diagnostic-row"><strong>Bridge</strong><span>{model.bridge.host}:{model.bridge.port}</span></div> {/* 新增代码+DesktopSettingsPanel：显示脱敏 bridge host/port；如果没有这行，用户无法确认连接端口。 */}
        </div> {/* 新增代码+DesktopSettingsPanel：设置键值列表结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopSettingsPanel：模型和 bridge 区域结束；如果没有这行，JSX 结构不完整。 */}
      <div className="settings-section"> {/* 新增代码+DesktopSettingsPanel：功能开关区域容器；如果没有这一层，feature flags 缺少分组。 */}
        <div className="settings-section-title"><strong>功能开关</strong></div> {/* 新增代码+DesktopSettingsPanel：功能开关标题；如果没有这行，用户不知道 chips 的含义。 */}
        <div className="settings-flags"> {/* 新增代码+DesktopSettingsPanel：功能开关 chips 容器；如果没有这一层，开关会纵向拥挤。 */}
          {model.featureFlags.length === 0 ? <span className="settings-flag settings-flag-muted">暂无开关</span> : model.featureFlags.map((flag) => ( // 新增代码+DesktopSettingsPanel：渲染空态或开关 chips；如果没有这行，空 payload 会显示空白。
            <span className={`settings-flag${flag.enabled ? "" : " settings-flag-muted"}`} key={flag.name}>{flag.name} · {flag.label}</span> // 新增代码+DesktopSettingsPanel：显示单个功能开关；如果没有这行，用户看不到能力状态。
          ))} {/* 新增代码+DesktopSettingsPanel：功能开关遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </div> {/* 新增代码+DesktopSettingsPanel：功能开关 chips 容器结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopSettingsPanel：功能开关区域结束；如果没有这行，JSX 结构不完整。 */}
      <div className="settings-section"> {/* 新增代码+DesktopSettingsPanel：诊断目录区域容器；如果没有这一层，复制路径按钮缺少分组。 */}
        <div className="settings-section-title"><strong>文件</strong></div> {/* 新增代码+DesktopSettingsPanel：文件区域标题；如果没有这行，用户不知道下面是目录路径。 */}
        <button className="settings-copy-row" type="button" onClick={() => { copyText(model.logPath); }} title="复制日志目录" aria-label="复制日志目录"> {/* 新增代码+DesktopSettingsPanel：日志目录复制按钮；如果没有这行，用户无法一键复制日志路径。 */}
          <span><strong>日志</strong><small>{model.logPath}</small></span> {/* 新增代码+DesktopSettingsPanel：日志目录文本；如果没有这行，用户不知道要复制什么。 */}
          <Clipboard size={13} aria-hidden="true" /> {/* 新增代码+DesktopSettingsPanel：复制图标；如果没有这行，按钮意图不够直观。 */}
        </button> {/* 新增代码+DesktopSettingsPanel：日志复制按钮结束；如果没有这行，JSX 结构不完整。 */}
        <button className="settings-copy-row" type="button" onClick={() => { copyText(model.evidencePath); }} title="复制证据目录" aria-label="复制证据目录"> {/* 新增代码+DesktopSettingsPanel：证据目录复制按钮；如果没有这行，用户无法一键复制验收材料路径。 */}
          <span><strong>证据</strong><small>{model.evidencePath}</small></span> {/* 新增代码+DesktopSettingsPanel：证据目录文本；如果没有这行，用户不知道验收材料位置。 */}
          <Clipboard size={13} aria-hidden="true" /> {/* 新增代码+DesktopSettingsPanel：复制图标；如果没有这行，按钮意图不够直观。 */}
        </button> {/* 新增代码+DesktopSettingsPanel：证据复制按钮结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+DesktopSettingsPanel：诊断目录区域结束；如果没有这行，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopSettingsPanel：设置面板容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopSettingsPanel：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopSettingsPanel：函数段结束，SettingsPanel 到此结束；如果没有这个边界，设置面板范围不清楚。
