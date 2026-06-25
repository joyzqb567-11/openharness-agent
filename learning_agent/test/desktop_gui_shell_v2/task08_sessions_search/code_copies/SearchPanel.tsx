import { Archive, Search, X } from "lucide-react"; // 新增代码+DesktopGUISessionSearch：引入搜索、关闭和归档图标；如果没有这行，搜索面板会退化成难扫读的纯文字按钮。

export type SearchPanelResult = { // 新增代码+DesktopGUISessionSearch：类型段开始，定义搜索结果条目；如果没有这段，AppShell 和 SearchPanel 会各自猜字段。
  sessionId: string; // 新增代码+DesktopGUISessionSearch：保存可恢复的 session id；如果没有这行，点击搜索结果无法定位会话。
  title: string; // 新增代码+DesktopGUISessionSearch：保存搜索结果标题；如果没有这行，结果列表没有可读主文本。
  snippet: string; // 新增代码+DesktopGUISessionSearch：保存命中片段；如果没有这行，用户不知道为什么这条结果命中。
  archived?: boolean; // 新增代码+DesktopGUISessionSearch：保存是否归档；如果没有这行，面板无法提示结果来自归档区。
}; // 新增代码+DesktopGUISessionSearch：搜索结果类型结束；如果没有这行，TypeScript 类型语法不完整。

type SearchPanelProps = { // 新增代码+DesktopGUISessionSearch：类型段开始，定义搜索面板入参；如果没有这段，组件边界不清楚。
  open: boolean; // 新增代码+DesktopGUISessionSearch：保存面板是否打开；如果没有这行，父组件无法控制显示。
  query: string; // 新增代码+DesktopGUISessionSearch：保存当前搜索词；如果没有这行，输入框无法受控。
  results: SearchPanelResult[]; // 新增代码+DesktopGUISessionSearch：保存搜索结果列表；如果没有这行，面板没有数据来源。
  isSearching: boolean; // 新增代码+DesktopGUISessionSearch：保存加载状态；如果没有这行，用户不知道搜索是否正在进行。
  onClose: () => void; // 新增代码+DesktopGUISessionSearch：保存关闭回调；如果没有这行，面板无法关闭。
  onQueryChange: (query: string) => void; // 新增代码+DesktopGUISessionSearch：保存输入变更回调；如果没有这行，用户输入不会触发搜索。
  onSelectSession: (sessionId: string) => void; // 新增代码+DesktopGUISessionSearch：保存结果点击回调；如果没有这行，搜索结果不能恢复会话。
}; // 新增代码+DesktopGUISessionSearch：搜索面板入参类型结束；如果没有这行，TypeScript 类型语法不完整。

export function SearchPanel({ open, query, results, isSearching, onClose, onQueryChange, onSelectSession }: SearchPanelProps): JSX.Element | null { // 新增代码+DesktopGUISessionSearch：函数段开始，渲染 Codex 式会话搜索面板；如果没有这段，搜索入口没有可见 GUI。
  if (!open) { // 新增代码+DesktopGUISessionSearch：关闭时不渲染面板；如果没有这行，隐藏状态仍会占用焦点和点击区域。
    return null; // 新增代码+DesktopGUISessionSearch：返回空 UI；如果没有这行，关闭状态会继续显示搜索弹层。
  } // 新增代码+DesktopGUISessionSearch：关闭判断结束；如果没有这行，条件块语法不完整。
  const trimmedQuery = query.trim(); // 新增代码+DesktopGUISessionSearch：清理搜索词用于空状态判断；如果没有这行，纯空格会被当成有效查询。
  return ( // 新增代码+DesktopGUISessionSearch：返回搜索面板结构；如果没有这行，组件不会输出 UI。
    <div className="search-panel-backdrop" role="presentation"> {/* 新增代码+DesktopGUISessionSearch：定义弹层背景；如果没有这行，面板会和主界面混在一起。 */}
      <section className="search-panel" aria-label="搜索会话"> {/* 新增代码+DesktopGUISessionSearch：定义搜索弹层主体；如果没有这行，读屏器不知道这是搜索区域。 */}
        <header className="search-panel-header"> {/* 新增代码+DesktopGUISessionSearch：定义搜索顶部栏；如果没有这行，输入框和关闭按钮无法稳定排布。 */}
          <div className="search-panel-input-wrap"> {/* 新增代码+DesktopGUISessionSearch：包裹图标和输入框；如果没有这行，搜索图标和输入文字不易对齐。 */}
            <Search aria-hidden={true} size={16} /> {/* 新增代码+DesktopGUISessionSearch：显示搜索图标；如果没有这行，输入框意图不够清楚。 */}
            <input autoFocus={true} aria-label="搜索历史会话" value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="搜索对话、回答或工具结果" /> {/* 新增代码+DesktopGUISessionSearch：渲染受控搜索输入；如果没有这行，用户无法输入查询词。 */}
          </div> {/* 新增代码+DesktopGUISessionSearch：输入包裹层结束；如果没有这行，JSX 结构不完整。 */}
          <button className="search-panel-close" type="button" aria-label="关闭搜索" onClick={onClose}> {/* 新增代码+DesktopGUISessionSearch：渲染关闭按钮；如果没有这行，用户无法退出搜索面板。 */}
            <X aria-hidden={true} size={16} /> {/* 新增代码+DesktopGUISessionSearch：显示关闭图标；如果没有这行，按钮含义不够直观。 */}
          </button> {/* 新增代码+DesktopGUISessionSearch：关闭按钮结束；如果没有这行，JSX 结构不完整。 */}
        </header> {/* 新增代码+DesktopGUISessionSearch：搜索顶部栏结束；如果没有这行，JSX 结构不完整。 */}
        <div className="search-panel-body"> {/* 新增代码+DesktopGUISessionSearch：定义结果滚动区；如果没有这行，长结果列表会撑破窗口。 */}
          {isSearching ? <div className="search-panel-empty">正在搜索...</div> : null} {/* 新增代码+DesktopGUISessionSearch：显示搜索中状态；如果没有这行，用户输入后没有等待反馈。 */}
          {!isSearching && trimmedQuery.length === 0 && results.length === 0 ? <div className="search-panel-empty">输入关键词后搜索历史会话</div> : null} {/* 修改代码+DesktopGUISessionSearch：只在没有预置结果时显示初始空状态；如果没有这行，归档视图会同时显示提示和归档列表。 */}
          {!isSearching && trimmedQuery.length > 0 && results.length === 0 ? <div className="search-panel-empty">没有找到匹配会话</div> : null} {/* 新增代码+DesktopGUISessionSearch：显示无结果状态；如果没有这行，用户不知道搜索已经完成。 */}
          {!isSearching && results.map((result) => ( // 新增代码+DesktopGUISessionSearch：遍历搜索结果；如果没有这行，后端结果不会进入 UI。
            <button className="search-panel-result" key={result.sessionId} type="button" onClick={() => onSelectSession(result.sessionId)}> {/* 新增代码+DesktopGUISessionSearch：渲染可点击结果；如果没有这行，用户无法从搜索回到会话。 */}
              <span className="search-panel-result-title">{result.title}</span> {/* 新增代码+DesktopGUISessionSearch：显示结果标题；如果没有这行，结果列表不可读。 */}
              {result.archived ? <span className="search-panel-result-archived"><Archive aria-hidden={true} size={12} />归档</span> : null} {/* 新增代码+DesktopGUISessionSearch：显示归档标记；如果没有这行，用户分不清结果是否来自隐藏会话。 */}
              <small>{result.snippet}</small> {/* 新增代码+DesktopGUISessionSearch：显示命中片段；如果没有这行，搜索结果缺少上下文。 */}
            </button> // 新增代码+DesktopGUISessionSearch：搜索结果按钮结束；如果没有这行，JSX 结构不完整。
          ))} {/* 新增代码+DesktopGUISessionSearch：搜索结果遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </div> {/* 新增代码+DesktopGUISessionSearch：结果滚动区结束；如果没有这行，JSX 结构不完整。 */}
      </section> {/* 新增代码+DesktopGUISessionSearch：搜索弹层主体结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+DesktopGUISessionSearch：弹层背景结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUISessionSearch：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUISessionSearch：函数段结束，SearchPanel 到此结束；如果没有这个边界，初学者不易看出搜索面板范围。
