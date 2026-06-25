import { Bot, Folder, Plug, Search, Settings, Zap } from "lucide-react"; // 修改代码+DesktopGUISessions：引入侧栏图标；如果没有这行，导航会变成难扫读的纯文字列表。

export type SidebarSession = { // 新增代码+DesktopGUISessions：定义侧栏会话条目；如果没有这段，AppShell 和 Sidebar 会对 session 字段各自猜测。
  id: string; // 新增代码+DesktopGUISessions：保存可恢复 session id；如果没有这行，点击会话时无法定位恢复目标。
  title: string; // 新增代码+DesktopGUISessions：保存侧栏显示标题；如果没有这行，会话列表没有可读文本。
  subtitle?: string; // 新增代码+DesktopGUISessions：保存可选辅助说明；如果没有这行，后续无法显示最近 prompt 或状态。
}; // 新增代码+DesktopGUISessions：SidebarSession 类型结束；如果没有这行，TypeScript 类型语法不完整。

type SidebarProps = { // 新增代码+DesktopGUISessions：定义 Sidebar props；如果没有这段，侧栏无法接收真实项目名和 sessions。
  projectName: string; // 新增代码+DesktopGUISessions：保存当前项目名；如果没有这行，侧栏只能硬编码 OpenHarness-main。
  sessions: SidebarSession[]; // 新增代码+DesktopGUISessions：保存最近会话列表；如果没有这行，侧栏仍然只能显示假会话。
  onSelectSession: (sessionId: string) => void; // 新增代码+DesktopGUISessions：保存会话点击回调；如果没有这行，用户无法从侧栏恢复会话。
}; // 新增代码+DesktopGUISessions：Sidebar props 类型结束；如果没有这行，TypeScript 类型语法不完整。

const primaryItems = [ // 修改代码+DesktopGUISessions：定义顶部常用入口；如果没有这段，侧栏按钮会散落重复写。
  { label: "快速对话", icon: Bot }, // 修改代码+DesktopGUISessions：提供主聊天入口；如果没有这行，用户找不到主要聊天动作。
  { label: "搜索", icon: Search }, // 修改代码+DesktopGUISessions：提供搜索占位入口；如果没有这行，Codex 风格的信息检索入口缺失。
  { label: "插件", icon: Plug }, // 修改代码+DesktopGUISessions：提供插件占位入口；如果没有这行，后续插件功能没有稳定位置。
  { label: "自动化", icon: Zap }, // 修改代码+DesktopGUISessions：提供自动化占位入口；如果没有这行，后台任务和定时功能没有导航位置。
]; // 修改代码+DesktopGUISessions：顶部入口数组结束；如果没有这行，TypeScript 语法不完整。

export function Sidebar({ projectName, sessions, onSelectSession }: SidebarProps): JSX.Element { // 修改代码+DesktopGUISessions：函数段开始，渲染左侧导航和真实 session 列表；如果没有这段，桌面壳没有 Codex 风格左栏。
  return ( // 修改代码+DesktopGUISessions：返回侧栏结构；如果没有这行，组件不会输出 UI。
    <aside className="sidebar" aria-label="项目和导航"> {/* 修改代码+DesktopGUISessions：定义侧栏容器；如果没有这行，读屏器不知道这是导航区域。 */}
      <nav className="sidebar-section" aria-label="主要功能"> {/* 修改代码+DesktopGUISessions：定义主要功能导航；如果没有这行，按钮组没有语义。 */}
        {primaryItems.map((item) => { // 修改代码+DesktopGUISessions：遍历常用入口；如果没有这行，入口需要手写且难维护。
          const Icon = item.icon; // 修改代码+DesktopGUISessions：取出当前入口图标；如果没有这行，JSX 不能动态渲染图标组件。
          return ( // 修改代码+DesktopGUISessions：返回当前按钮；如果没有这行，map 不会生成 UI 元素。
            <button className="sidebar-item" key={item.label} type="button"> {/* 修改代码+DesktopGUISessions：渲染侧栏按钮；如果没有这行，用户无法点击功能入口。 */}
              <Icon aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessions：渲染功能图标；如果没有这行，导航扫描速度会变慢。 */}
              <span>{item.label}</span> {/* 修改代码+DesktopGUISessions：渲染功能名称；如果没有这行，图标含义不够明确。 */}
            </button> // 修改代码+DesktopGUISessions：侧栏按钮结束；如果没有这行，JSX 结构不完整。
          ); // 修改代码+DesktopGUISessions：单项返回结束；如果没有这行，map 回调语法不完整。
        })} {/* 修改代码+DesktopGUISessions：主要功能遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </nav> {/* 修改代码+DesktopGUISessions：主要功能导航结束；如果没有这行，JSX 结构不完整。 */}
      <section className="sidebar-section sidebar-projects" aria-label="项目"> {/* 修改代码+DesktopGUISessions：定义项目区；如果没有这行，当前项目和最近会话没有稳定位置。 */}
        <div className="sidebar-heading">项目</div> {/* 修改代码+DesktopGUISessions：显示项目标题；如果没有这行，用户难以区分项目列表和功能导航。 */}
        <button className="sidebar-item sidebar-item-active" type="button"> {/* 修改代码+DesktopGUISessions：显示当前项目按钮；如果没有这行，用户看不到当前工作区。 */}
          <Folder aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessions：显示项目图标；如果没有这行，项目入口缺少视觉锚点。 */}
          <span>{projectName}</span> {/* 修改代码+DesktopGUISessions：显示当前项目名；如果没有这行，侧栏无法表达工作区身份。 */}
        </button> {/* 修改代码+DesktopGUISessions：当前项目按钮结束；如果没有这行，JSX 结构不完整。 */}
        <div className="sidebar-heading">最近对话</div> {/* 修改代码+DesktopGUISessions：显示最近对话标题；如果没有这行，session 列表语义不清楚。 */}
        {sessions.length === 0 ? ( // 修改代码+DesktopGUISessions：处理空会话列表；如果没有这行，首启时最近对话区会显得断裂。
          <div className="sidebar-empty">暂无最近对话</div> // 新增代码+DesktopGUISessions：显示空状态；如果没有这行，用户不知道是否加载失败还是没有会话。
        ) : ( // 修改代码+DesktopGUISessions：处理有会话的分支；如果没有这行，条件渲染语法不完整。
          sessions.map((session) => ( // 修改代码+DesktopGUISessions：遍历真实最近会话；如果没有这行，后端 sessions 不会出现在侧栏。
            <button className="sidebar-session" key={session.id} onClick={() => onSelectSession(session.id)} type="button"> {/* 修改代码+DesktopGUISessions：渲染可点击会话按钮；如果没有这行，用户无法从侧栏选择历史对话。 */}
              <span>{session.title}</span> {/* 修改代码+DesktopGUISessions：显示会话标题；如果没有这行，列表项没有可读内容。 */}
              {session.subtitle ? <small>{session.subtitle}</small> : null} {/* 新增代码+DesktopGUISessions：显示可选副标题；如果没有这行，后续 prompt/status 摘要没有位置。 */}
            </button> // 修改代码+DesktopGUISessions：会话按钮结束；如果没有这行，JSX 结构不完整。
          )) // 修改代码+DesktopGUISessions：最近会话遍历结束；如果没有这行，map 表达式不完整。
        )} {/* 修改代码+DesktopGUISessions：最近会话条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
      </section> {/* 修改代码+DesktopGUISessions：项目区结束；如果没有这行，JSX 结构不完整。 */}
      <button className="sidebar-item sidebar-settings" type="button"> {/* 修改代码+DesktopGUISessions：渲染设置入口；如果没有这行，用户无法找到配置区域。 */}
        <Settings aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessions：显示设置图标；如果没有这行，底部入口识别度下降。 */}
        <span>设置</span> {/* 修改代码+DesktopGUISessions：显示设置文字；如果没有这行，图标含义不够明确。 */}
      </button> {/* 修改代码+DesktopGUISessions：设置入口结束；如果没有这行，JSX 结构不完整。 */}
    </aside> // 修改代码+DesktopGUISessions：侧栏容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUISessions：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUISessions：函数段结束，Sidebar 到此结束；如果没有这个边界，用户不容易看出侧栏范围。
