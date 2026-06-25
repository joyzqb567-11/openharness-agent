import { Composer } from "./Composer"; // 新增代码+DesktopShellLayout：引入底部输入组件；如果没有这行，主界面没有用户输入入口。
import { Sidebar } from "./Sidebar"; // 新增代码+DesktopShellLayout：引入左侧导航组件；如果没有这行，项目和功能入口会散落在页面里。
import { ThreadView } from "./ThreadView"; // 新增代码+DesktopShellLayout：引入线程显示组件；如果没有这行，消息内容没有独立渲染区域。

export function AppShell(): JSX.Element { // 新增代码+DesktopShellLayout：函数段开始，组织桌面 GUI 主壳；如果没有这段，各组件无法组合成 Codex 风格窗口。
  return ( // 新增代码+DesktopShellLayout：返回主界面结构；如果没有这行，组件不会输出任何 UI。
    <main className="app-shell"> {/* 新增代码+DesktopShellLayout：定义全窗口网格容器；如果没有这行，侧栏和线程区无法稳定并排。 */}
      <Sidebar /> {/* 新增代码+DesktopShellLayout：渲染项目导航侧栏；如果没有这行，用户无法看到 quick chat/search/plugins/settings 等入口。 */}
      <section className="thread-panel" aria-label="当前对话"> {/* 新增代码+DesktopShellLayout：定义当前对话主区域；如果没有这行，读屏器和布局都缺少对话容器。 */}
        <header className="thread-header"> {/* 新增代码+DesktopShellLayout：定义顶部会话栏；如果没有这行，用户无法确认当前会话标题。 */}
          <div className="thread-title">快速对话</div> {/* 新增代码+DesktopShellLayout：显示当前会话名；如果没有这行，主面板上下文不清楚。 */}
          <div className="thread-subtitle">OpenHarness Desktop Shell</div> {/* 新增代码+DesktopShellLayout：显示当前壳版本语境；如果没有这行，用户难以区分 CLI 和桌面壳。 */}
        </header> {/* 新增代码+DesktopShellLayout：顶部会话栏结束；如果没有这行，JSX 结构不完整。 */}
        <ThreadView /> {/* 新增代码+DesktopShellLayout：渲染消息线程；如果没有这行，主面板没有对话内容。 */}
        <Composer /> {/* 新增代码+DesktopShellLayout：渲染输入区；如果没有这行，用户无法看到后续发送入口。 */}
      </section> {/* 新增代码+DesktopShellLayout：当前对话主区域结束；如果没有这行，JSX 结构不完整。 */}
    </main> /* 新增代码+DesktopShellLayout：全窗口网格容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopShellLayout：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopShellLayout：函数段结束，AppShell 到此结束；如果没有这个边界，用户不容易看出主壳组合范围。
