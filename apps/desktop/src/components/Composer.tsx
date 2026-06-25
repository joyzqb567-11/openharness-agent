import { ArrowUp, Paperclip } from "lucide-react"; // 新增代码+DesktopComposer：引入发送和附件图标；如果没有这行，composer 按钮只能用文字，扫描效率较低。

export function Composer(): JSX.Element { // 新增代码+DesktopComposer：函数段开始，渲染底部输入工具条；如果没有这段，用户看不到发送 prompt 的入口。
  return ( // 新增代码+DesktopComposer：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 新增代码+DesktopComposer：定义 composer 容器；如果没有这行，输入框和按钮没有稳定布局。 */}
      <button className="icon-button" type="button" aria-label="添加附件"> {/* 新增代码+DesktopComposer：渲染附件按钮；如果没有这行，后续附件功能没有明确入口。 */}
        <Paperclip aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示附件图标；如果没有这行，按钮含义不直观。 */}
      </button> {/* 新增代码+DesktopComposer：附件按钮结束；如果没有这行，JSX 结构不完整。 */}
      <textarea className="composer-input" rows={1} placeholder="要求后续变更" /> {/* 新增代码+DesktopComposer：渲染 prompt 输入框；如果没有这行，用户无法输入任务。 */}
      <button className="send-button" type="button" aria-label="发送"> {/* 新增代码+DesktopComposer：渲染发送按钮；如果没有这行，用户看不到提交入口。 */}
        <ArrowUp aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示发送图标；如果没有这行，按钮不够符合常见聊天工具心智。 */}
      </button> {/* 新增代码+DesktopComposer：发送按钮结束；如果没有这行，JSX 结构不完整。 */}
    </footer> /* 新增代码+DesktopComposer：composer 容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopComposer：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopComposer：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
