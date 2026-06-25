import { Archive, Bot, Folder, Pin, Plug, Search, Settings, Zap } from "lucide-react"; // 修改代码+DesktopGUISessionSearch：引入侧栏所需图标；如果没有这行，导航和会话状态会退化成难扫读的纯文字。

export type SidebarSession = { // 修改代码+DesktopGUISessionSearch：类型段开始，定义侧栏会话条目；如果没有这段，AppShell 和 Sidebar 会对 session 字段各自猜测。
  id: string; // 修改代码+DesktopGUISessionSearch：保存可恢复 session id；如果没有这行，点击历史会话无法定位后端会话。
  title: string; // 修改代码+DesktopGUISessionSearch：保存侧栏显示标题；如果没有这行，会话列表没有可读文本。
  subtitle?: string; // 修改代码+DesktopGUISessionSearch：保存可选摘要；如果没有这行，最近 prompt 或状态没有展示位置。
  active?: boolean; // 新增代码+DesktopGUISessionSearch：保存是否当前选中；如果没有这行，用户看不出自己正在查看哪个会话。
  pinned?: boolean; // 新增代码+DesktopGUISessionSearch：保存是否固定；如果没有这行，重点会话无法在侧栏形成稳定标记。
  archived?: boolean; // 新增代码+DesktopGUISessionSearch：保存是否归档；如果没有这行，归档视图和搜索结果无法复用同一条目类型。
}; // 修改代码+DesktopGUISessionSearch：SidebarSession 类型结束；如果没有这行，TypeScript 类型语法不完整。

type SidebarProps = { // 修改代码+DesktopGUISessionSearch：类型段开始，定义 Sidebar props；如果没有这段，侧栏无法接收真实项目、会话和操作回调。
  projectName: string; // 修改代码+DesktopGUISessionSearch：保存当前项目名；如果没有这行，侧栏只能显示硬编码项目。
  sessions: SidebarSession[]; // 修改代码+DesktopGUISessionSearch：保存最近会话列表；如果没有这行，侧栏仍只能显示假数据。
  activeSessionId: string; // 新增代码+DesktopGUISessionSearch：保存当前 active 会话 id；如果没有这行，侧栏无法高亮当前会话。
  archivedCount: number; // 新增代码+DesktopGUISessionSearch：保存归档会话计数；如果没有这行，归档入口只能显示静态文案。
  onNewConversation: () => void; // 新增代码+DesktopGUISessionSearch：保存新对话回调；如果没有这行，快速对话按钮无法创建新会话。
  onOpenSearch: () => void; // 新增代码+DesktopGUISessionSearch：保存打开搜索回调；如果没有这行，搜索按钮没有真实 GUI 行为。
  onOpenArchived: () => void; // 新增代码+DesktopGUISessionSearch：保存打开归档视图回调；如果没有这行，归档入口无法真正过滤归档会话。
  onSelectSession: (sessionId: string) => void; // 修改代码+DesktopGUISessionSearch：保存会话点击回调；如果没有这行，用户无法从侧栏恢复会话。
}; // 修改代码+DesktopGUISessionSearch：Sidebar props 类型结束；如果没有这行，TypeScript 类型语法不完整。

const passiveItems = [ // 修改代码+DesktopGUISessionSearch：定义暂未接入的稳定入口；如果没有这段，插件和自动化位置会散落在 JSX 里。
  { label: "插件", icon: Plug }, // 修改代码+DesktopGUISessionSearch：保留插件入口；如果没有这行，后续插件模块没有固定导航位置。
  { label: "自动化", icon: Zap }, // 修改代码+DesktopGUISessionSearch：保留自动化入口；如果没有这行，后续后台任务入口没有固定导航位置。
]; // 修改代码+DesktopGUISessionSearch：暂未接入口数组结束；如果没有这行，TypeScript 语法不完整。

export function Sidebar({ projectName, sessions, activeSessionId, archivedCount, onNewConversation, onOpenSearch, onOpenArchived, onSelectSession }: SidebarProps): JSX.Element { // 修改代码+DesktopGUISessionSearch：函数段开始，渲染 Codex 风格项目和会话侧栏；如果没有这段，桌面壳没有左侧工作区导航。
  return ( // 修改代码+DesktopGUISessionSearch：返回侧栏结构；如果没有这行，组件不会输出 UI。
    <aside className="sidebar" aria-label="项目和导航"> {/* 修改代码+DesktopGUISessionSearch：定义侧栏容器；如果没有这行，读屏器不知道这是导航区域。 */}
      <nav className="sidebar-section" aria-label="主要功能"> {/* 修改代码+DesktopGUISessionSearch：定义主要功能导航；如果没有这行，按钮组没有语义。 */}
        <button className="sidebar-item" type="button" onClick={onNewConversation}> {/* 新增代码+DesktopGUISessionSearch：渲染新对话按钮；如果没有这行，用户无法从侧栏开始新会话。 */}
          <Bot aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessionSearch：显示快速对话图标；如果没有这行，入口扫描速度会下降。 */}
          <span>快速对话</span> {/* 修改代码+DesktopGUISessionSearch：显示快速对话文本；如果没有这行，图标含义不够明确。 */}
        </button> {/* 修改代码+DesktopGUISessionSearch：新对话按钮结束；如果没有这行，JSX 结构不完整。 */}
        <button className="sidebar-item" type="button" onClick={onOpenSearch}> {/* 新增代码+DesktopGUISessionSearch：渲染搜索按钮；如果没有这行，搜索面板没有入口。 */}
          <Search aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessionSearch：显示搜索图标；如果没有这行，入口识别速度会下降。 */}
          <span>搜索</span> {/* 修改代码+DesktopGUISessionSearch：显示搜索文本；如果没有这行，图标含义不够明确。 */}
        </button> {/* 修改代码+DesktopGUISessionSearch：搜索按钮结束；如果没有这行，JSX 结构不完整。 */}
        {passiveItems.map((item) => { // 修改代码+DesktopGUISessionSearch：遍历保留入口；如果没有这行，插件和自动化按钮会重复手写。
          const Icon = item.icon; // 修改代码+DesktopGUISessionSearch：读取当前入口图标；如果没有这行，JSX 无法动态渲染图标组件。
          return ( // 修改代码+DesktopGUISessionSearch：返回当前保留按钮；如果没有这行，map 不会生成 UI。
            <button className="sidebar-item sidebar-item-muted" key={item.label} type="button"> {/* 修改代码+DesktopGUISessionSearch：渲染暂未接入按钮；如果没有这行，未来功能没有可见位置。 */}
              <Icon aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessionSearch：显示保留入口图标；如果没有这行，按钮扫描速度会下降。 */}
              <span>{item.label}</span> {/* 修改代码+DesktopGUISessionSearch：显示保留入口名称；如果没有这行，用户不知道按钮用途。 */}
            </button> // 修改代码+DesktopGUISessionSearch：保留入口按钮结束；如果没有这行，JSX 结构不完整。
          ); // 修改代码+DesktopGUISessionSearch：单个 map 返回结束；如果没有这行，回调语法不完整。
        })} {/* 修改代码+DesktopGUISessionSearch：保留入口遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </nav> {/* 修改代码+DesktopGUISessionSearch：主要功能导航结束；如果没有这行，JSX 结构不完整。 */}
      <section className="sidebar-section sidebar-projects" aria-label="项目"> {/* 修改代码+DesktopGUISessionSearch：定义项目和会话区；如果没有这行，当前项目和最近会话没有稳定位置。 */}
        <div className="sidebar-heading">项目</div> {/* 修改代码+DesktopGUISessionSearch：显示项目分区标题；如果没有这行，用户难以区分项目和功能导航。 */}
        <button className="sidebar-item sidebar-item-active" type="button"> {/* 修改代码+DesktopGUISessionSearch：显示当前项目按钮；如果没有这行，用户看不到当前工作区。 */}
          <Folder aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessionSearch：显示项目图标；如果没有这行，项目入口缺少视觉锚点。 */}
          <span>{projectName}</span> {/* 修改代码+DesktopGUISessionSearch：显示真实项目名；如果没有这行，侧栏无法表达工作区身份。 */}
        </button> {/* 修改代码+DesktopGUISessionSearch：当前项目按钮结束；如果没有这行，JSX 结构不完整。 */}
        <div className="sidebar-heading">最近对话</div> {/* 修改代码+DesktopGUISessionSearch：显示最近对话标题；如果没有这行，session 列表语义不清楚。 */}
        {sessions.length === 0 ? ( // 修改代码+DesktopGUISessionSearch：处理空会话列表；如果没有这行，首次启动时会留下没有解释的空白。
          <div className="sidebar-empty">暂无最近对话</div> // 修改代码+DesktopGUISessionSearch：显示空状态；如果没有这行，用户不知道是无会话还是加载失败。
        ) : ( // 修改代码+DesktopGUISessionSearch：处理有会话的分支；如果没有这行，条件渲染语法不完整。
          sessions.map((session) => ( // 修改代码+DesktopGUISessionSearch：遍历真实最近会话；如果没有这行，后端 sessions 不会出现在侧栏。
            <button className={`sidebar-session ${session.active || session.id === activeSessionId ? "sidebar-session-active" : ""}`} key={session.id} onClick={() => onSelectSession(session.id)} type="button"> {/* 修改代码+DesktopGUISessionSearch：渲染可点击会话按钮并标记 active；如果没有这行，用户无法恢复或辨认当前会话。 */}
              <span>{session.title}</span> {/* 修改代码+DesktopGUISessionSearch：显示会话标题；如果没有这行，列表项没有可读内容。 */}
              {session.pinned ? <small className="sidebar-session-badge"><Pin aria-hidden={true} size={11} />固定</small> : null} {/* 新增代码+DesktopGUISessionSearch：显示固定标记；如果没有这行，重点会话缺少视觉提示。 */}
              {session.subtitle ? <small>{session.subtitle}</small> : null} {/* 修改代码+DesktopGUISessionSearch：显示可选副标题；如果没有这行，prompt/status 摘要没有位置。 */}
            </button> // 修改代码+DesktopGUISessionSearch：会话按钮结束；如果没有这行，JSX 结构不完整。
          )) // 修改代码+DesktopGUISessionSearch：最近会话遍历结束；如果没有这行，map 表达式不完整。
        )} {/* 修改代码+DesktopGUISessionSearch：最近会话条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
        <button className="sidebar-archived" type="button" onClick={onOpenArchived}> {/* 修改代码+DesktopGUISessionSearch：渲染真实归档入口；如果没有这行，用户看不到被隐藏会话的去向。 */}
          <Archive aria-hidden={true} size={14} /> {/* 新增代码+DesktopGUISessionSearch：显示归档图标；如果没有这行，入口意图不够清楚。 */}
          <span>归档</span> {/* 新增代码+DesktopGUISessionSearch：显示归档文本；如果没有这行，图标含义不够明确。 */}
          <strong>{archivedCount}</strong> {/* 新增代码+DesktopGUISessionSearch：显示归档数量；如果没有这行，用户不知道归档区是否有内容。 */}
        </button> {/* 新增代码+DesktopGUISessionSearch：归档入口结束；如果没有这行，JSX 结构不完整。 */}
      </section> {/* 修改代码+DesktopGUISessionSearch：项目和会话区结束；如果没有这行，JSX 结构不完整。 */}
      <button className="sidebar-item sidebar-settings" type="button"> {/* 修改代码+DesktopGUISessionSearch：渲染设置入口；如果没有这行，用户无法找到配置区域。 */}
        <Settings aria-hidden={true} size={16} /> {/* 修改代码+DesktopGUISessionSearch：显示设置图标；如果没有这行，底部入口识别度下降。 */}
        <span>设置</span> {/* 修改代码+DesktopGUISessionSearch：显示设置文字；如果没有这行，图标含义不够明确。 */}
      </button> {/* 修改代码+DesktopGUISessionSearch：设置入口结束；如果没有这行，JSX 结构不完整。 */}
    </aside> // 修改代码+DesktopGUISessionSearch：侧栏容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUISessionSearch：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUISessionSearch：函数段结束，Sidebar 到此结束；如果没有这个边界，用户不容易看出侧栏范围。
