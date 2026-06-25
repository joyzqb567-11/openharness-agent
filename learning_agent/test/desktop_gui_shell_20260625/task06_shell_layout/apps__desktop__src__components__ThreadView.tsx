export function ThreadView(): JSX.Element { // 新增代码+DesktopThreadView：函数段开始，渲染当前对话消息区；如果没有这段，主面板没有消息内容。
  return ( // 新增代码+DesktopThreadView：返回消息列表结构；如果没有这行，组件不会输出 UI。
    <div className="thread-body"> {/* 新增代码+DesktopThreadView：定义可滚动消息区域；如果没有这行，长对话无法独立滚动。 */}
      <article className="message assistant-message"> {/* 新增代码+DesktopThreadView：渲染助手消息卡；如果没有这行，启动状态没有可读呈现。 */}
        <div className="message-role">OpenHarness</div> {/* 新增代码+DesktopThreadView：显示消息角色；如果没有这行，用户难以区分助手和用户消息。 */}
        <p>桌面 GUI 外壳已连接到 OpenHarness 后端蓝图，下一步会接入真实消息生命周期。</p> {/* 新增代码+DesktopThreadView：显示当前进度说明；如果没有这行，首屏会显得空。 */}
      </article> {/* 新增代码+DesktopThreadView：助手消息卡结束；如果没有这行，JSX 结构不完整。 */}
      <article className="message system-message"> {/* 新增代码+DesktopThreadView：渲染系统状态消息；如果没有这行，用户看不到 bridge-first 的实现方向。 */}
        <div className="message-role">状态</div> {/* 新增代码+DesktopThreadView：显示状态角色；如果没有这行，状态消息和普通回答会混淆。 */}
        <p>事件轮询、权限提示、取消、重试和恢复会在后续任务逐项接上。</p> {/* 新增代码+DesktopThreadView：说明后续 UI 接入点；如果没有这行，V1 外壳能力边界不清楚。 */}
      </article> {/* 新增代码+DesktopThreadView：系统状态消息结束；如果没有这行，JSX 结构不完整。 */}
    </div> /* 新增代码+DesktopThreadView：消息区域结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopThreadView：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopThreadView：函数段结束，ThreadView 到此结束；如果没有这个边界，用户不容易看出消息区范围。
