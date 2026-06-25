import { Bot, Folder, Plug, Search, Settings, Zap } from "lucide-react"; // 新增代码+DesktopSidebar：引入侧栏图标；如果没有这行，导航会变成难扫读的纯文字列表。

const primaryItems = [ // 新增代码+DesktopSidebar：定义顶部常用入口；如果没有这段，侧栏按钮会散落重复写。
  { label: "快速对话", icon: Bot }, // 新增代码+DesktopSidebar：提供新对话入口；如果没有这行，用户找不到主要聊天动作。
  { label: "搜索", icon: Search }, // 新增代码+DesktopSidebar：提供搜索占位入口；如果没有这行，Codex 风格的信息检索入口缺失。
  { label: "插件", icon: Plug }, // 新增代码+DesktopSidebar：提供插件占位入口；如果没有这行，后续插件功能没有稳定位置。
  { label: "自动化", icon: Zap }, // 新增代码+DesktopSidebar：提供自动化占位入口；如果没有这行，后台任务和定时功能没有导航位置。
]; // 新增代码+DesktopSidebar：顶部入口数组结束；如果没有这行，TypeScript 语法不完整。

const recentSessions = [ // 新增代码+DesktopSidebar：定义第一版最近会话占位；如果没有这段，侧栏项目区会显得空，后续接真实 sessions 时也缺少 UI 形状。
  "GUI 外壳蓝图执行", // 新增代码+DesktopSidebar：显示当前任务会话；如果没有这行，用户无法看到最近对话列表样式。
  "浏览器模块分析", // 新增代码+DesktopSidebar：显示浏览器分析会话；如果没有这行，列表密度无法提前验收。
  "项目知识图谱梳理", // 新增代码+DesktopSidebar：显示知识图谱会话；如果没有这行，中文长文本截断无法提前发现。
]; // 新增代码+DesktopSidebar：最近会话数组结束；如果没有这行，TypeScript 语法不完整。

export function Sidebar(): JSX.Element { // 新增代码+DesktopSidebar：函数段开始，渲染左侧导航和项目列表；如果没有这段，桌面壳没有 Codex 风格左栏。
  return ( // 新增代码+DesktopSidebar：返回侧栏结构；如果没有这行，组件不会输出 UI。
    <aside className="sidebar" aria-label="项目和导航"> {/* 新增代码+DesktopSidebar：定义侧栏容器；如果没有这行，读屏器不知道这是导航区域。 */}
      <nav className="sidebar-section" aria-label="主要功能"> {/* 新增代码+DesktopSidebar：定义主要功能导航；如果没有这行，按钮组没有语义。 */}
        {primaryItems.map((item) => { /* 新增代码+DesktopSidebar：遍历常用入口；如果没有这行，入口需要手写且难维护。 */
          const Icon = item.icon; // 新增代码+DesktopSidebar：取出当前入口图标；如果没有这行，JSX 不能动态渲染图标组件。
          return ( // 新增代码+DesktopSidebar：返回当前按钮；如果没有这行，map 不会生成 UI 元素。
            <button className="sidebar-item" key={item.label} type="button"> {/* 新增代码+DesktopSidebar：渲染侧栏按钮；如果没有这行，用户无法点击功能入口。 */}
              <Icon aria-hidden={true} size={16} /> {/* 新增代码+DesktopSidebar：渲染功能图标；如果没有这行，导航扫描速度会变慢。 */}
              <span>{item.label}</span> {/* 新增代码+DesktopSidebar：渲染功能名称；如果没有这行，图标含义不够明确。 */}
            </button> /* 新增代码+DesktopSidebar：侧栏按钮结束；如果没有这行，JSX 结构不完整。 */
          ); // 新增代码+DesktopSidebar：单项返回结束；如果没有这行，map 回调语法不完整。
        })} {/* 新增代码+DesktopSidebar：主要功能遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </nav> {/* 新增代码+DesktopSidebar：主要功能导航结束；如果没有这行，JSX 结构不完整。 */}
      <section className="sidebar-section sidebar-projects" aria-label="项目"> {/* 新增代码+DesktopSidebar：定义项目区；如果没有这行，当前项目和最近会话没有稳定位置。 */}
        <div className="sidebar-heading">项目</div> {/* 新增代码+DesktopSidebar：显示项目标题；如果没有这行，用户难以区分项目列表和功能导航。 */}
        <button className="sidebar-item sidebar-item-active" type="button"> {/* 新增代码+DesktopSidebar：显示当前项目按钮；如果没有这行，用户看不到当前工作区。 */}
          <Folder aria-hidden={true} size={16} /> {/* 新增代码+DesktopSidebar：显示项目图标；如果没有这行，项目入口缺少视觉锚点。 */}
          <span>OpenHarness-main</span> {/* 新增代码+DesktopSidebar：显示当前项目名；如果没有这行，侧栏无法表达工作区身份。 */}
        </button> {/* 新增代码+DesktopSidebar：当前项目按钮结束；如果没有这行，JSX 结构不完整。 */}
        <div className="sidebar-heading">最近对话</div> {/* 新增代码+DesktopSidebar：显示最近对话标题；如果没有这行，session 列表语义不清楚。 */}
        {recentSessions.map((session) => ( // 新增代码+DesktopSidebar：遍历最近会话；如果没有这行，后续真实 sessions 没有渲染模板。
          <button className="sidebar-session" key={session} type="button"> {/* 新增代码+DesktopSidebar：渲染会话按钮；如果没有这行，用户无法从侧栏选择历史对话。 */}
            {session} {/* 新增代码+DesktopSidebar：显示会话名称；如果没有这行，列表项没有可读内容。 */}
          </button> /* 新增代码+DesktopSidebar：会话按钮结束；如果没有这行，JSX 结构不完整。 */
        ))} {/* 新增代码+DesktopSidebar：最近会话遍历结束；如果没有这行，JSX 表达式不完整。 */}
      </section> {/* 新增代码+DesktopSidebar：项目区结束；如果没有这行，JSX 结构不完整。 */}
      <button className="sidebar-item sidebar-settings" type="button"> {/* 新增代码+DesktopSidebar：渲染设置入口；如果没有这行，用户无法找到配置区域。 */}
        <Settings aria-hidden={true} size={16} /> {/* 新增代码+DesktopSidebar：显示设置图标；如果没有这行，底部入口识别度下降。 */}
        <span>设置</span> {/* 新增代码+DesktopSidebar：显示设置文字；如果没有这行，图标含义不够明确。 */}
      </button> {/* 新增代码+DesktopSidebar：设置入口结束；如果没有这行，JSX 结构不完整。 */}
    </aside> /* 新增代码+DesktopSidebar：侧栏容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopSidebar：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopSidebar：函数段结束，Sidebar 到此结束；如果没有这个边界，用户不容易看出侧栏范围。
