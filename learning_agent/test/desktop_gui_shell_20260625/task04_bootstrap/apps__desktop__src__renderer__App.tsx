export function App(): JSX.Element { // 新增代码+DesktopApp：函数段开始，提供第一版桌面应用根组件；如果没有这段，React 入口没有可渲染的 UI。
  return ( // 新增代码+DesktopApp：返回首屏结构；如果没有这行，组件不会输出界面。
    <main className="app-shell"> {/* 新增代码+DesktopApp：定义桌面主布局容器；如果没有这行，侧栏和线程区无法形成 Codex 风格外壳。 */}
      <aside className="left-rail">OpenHarness</aside> {/* 新增代码+DesktopApp：显示第一版左侧项目栏；如果没有这行，用户看不到桌面壳导航区域。 */}
      <section className="thread-panel"> {/* 新增代码+DesktopApp：定义主对话面板；如果没有这行，消息和输入区没有稳定容器。 */}
        <header className="thread-header">快速对话</header> {/* 新增代码+DesktopApp：显示当前会话标题；如果没有这行，用户不知道主区域是什么。 */}
        <div className="thread-body">桌面 GUI 外壳已启动。</div> {/* 新增代码+DesktopApp：显示启动成功提示；如果没有这行，窗口可能看起来像空白页。 */}
        <footer className="composer">要求后续变更</footer> {/* 新增代码+DesktopApp：放置第一版输入区占位；如果没有这行，后续 composer 没有布局基准。 */}
      </section> {/* 新增代码+DesktopApp：主对话面板结束；如果没有这行，JSX 结构不完整。 */}
    </main> /* 新增代码+DesktopApp：主布局容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopApp：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopApp：函数段结束，App 到此结束；如果没有这个边界，用户不容易看出根组件范围。
