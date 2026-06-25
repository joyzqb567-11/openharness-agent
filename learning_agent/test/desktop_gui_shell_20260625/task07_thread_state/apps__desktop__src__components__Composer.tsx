import { ArrowUp, Paperclip } from "lucide-react"; // 新增代码+DesktopComposer：引入发送和附件图标；如果没有这行，composer 按钮只能用文字，扫描效率较低。
import { useState } from "react"; // 新增代码+DesktopComposer：引入本地输入状态；如果没有这行，textarea 无法在发送后清空或判断空输入。

type ComposerProps = { // 新增代码+DesktopComposer：定义输入组件 props；如果没有这段，后续后端发送逻辑无法从父组件注入。
  isRunning?: boolean; // 新增代码+DesktopComposer：允许父组件告知运行中；如果没有这行，发送按钮无法避免重复提交。
  onSubmit?: (prompt: string) => void; // 新增代码+DesktopComposer：允许父组件接收 prompt；如果没有这行，输入框只能是静态装饰。
}; // 新增代码+DesktopComposer：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function Composer({ isRunning = false, onSubmit }: ComposerProps): JSX.Element { // 新增代码+DesktopComposer：函数段开始，渲染底部输入工具条；如果没有这段，用户看不到发送 prompt 的入口。
  const [draft, setDraft] = useState(""); // 新增代码+DesktopComposer：保存当前输入草稿；如果没有这行，组件无法判断空 prompt 或清空输入。
  const canSend = draft.trim().length > 0 && !isRunning; // 新增代码+DesktopComposer：计算是否允许发送；如果没有这行，空输入或运行中都可能误触发发送。

  function submitDraft(): void { // 新增代码+DesktopComposer：函数段开始，提交当前草稿；如果没有这段，按钮和 Enter 键会重复写提交逻辑。
    if (!canSend) { // 新增代码+DesktopComposer：拦截不可发送状态；如果没有这行，空 prompt 会进入后端。
      return; // 新增代码+DesktopComposer：不可发送时直接退出；如果没有这行，后续仍会调用 onSubmit。
    } // 新增代码+DesktopComposer：不可发送判断结束；如果没有这行，条件块语法不完整。
    onSubmit?.(draft); // 新增代码+DesktopComposer：把 prompt 交给父组件；如果没有这行，用户输入不会进入应用状态。
    setDraft(""); // 新增代码+DesktopComposer：发送后清空输入；如果没有这行，重复发送时容易误提交旧内容。
  } // 新增代码+DesktopComposer：函数段结束，submitDraft 到此结束；如果没有这个边界，用户不容易看出提交逻辑范围。

  return ( // 新增代码+DesktopComposer：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 新增代码+DesktopComposer：定义 composer 容器；如果没有这行，输入框和按钮没有稳定布局。 */}
      <button className="icon-button" type="button" aria-label="添加附件"> {/* 新增代码+DesktopComposer：渲染附件按钮；如果没有这行，后续附件功能没有明确入口。 */}
        <Paperclip aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示附件图标；如果没有这行，按钮含义不直观。 */}
      </button> {/* 新增代码+DesktopComposer：附件按钮结束；如果没有这行，JSX 结构不完整。 */}
      <textarea className="composer-input" rows={1} placeholder="要求后续变更" value={draft} onChange={(event) => setDraft(event.currentTarget.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitDraft(); } }} /> {/* 新增代码+DesktopComposer：渲染受控 prompt 输入框并支持 Enter 发送；如果没有这行，用户无法输入或提交任务。 */}
      <button className="send-button" type="button" aria-label="发送" disabled={!canSend} onClick={submitDraft}> {/* 新增代码+DesktopComposer：渲染发送按钮并绑定提交；如果没有这行，用户看不到提交入口。 */}
        <ArrowUp aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示发送图标；如果没有这行，按钮不够符合常见聊天工具心智。 */}
      </button> {/* 新增代码+DesktopComposer：发送按钮结束；如果没有这行，JSX 结构不完整。 */}
    </footer> /* 新增代码+DesktopComposer：composer 容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopComposer：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopComposer：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
