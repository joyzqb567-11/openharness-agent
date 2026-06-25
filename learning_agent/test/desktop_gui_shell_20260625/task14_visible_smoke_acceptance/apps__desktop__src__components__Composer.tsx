import { ArrowUp, Paperclip, X } from "lucide-react"; // 修改代码+DesktopComposerCancel：引入发送、附件和取消图标；如果没有这行代码，运行中取消只能靠消息卡片小按钮，真实桌面验收会很难稳定点击。
import { useState } from "react"; // 新增代码+DesktopComposer：引入本地输入状态；如果没有这行，textarea 无法在发送后清空或判断空输入。

type ComposerProps = { // 修改代码+DesktopComposerCancel：定义输入组件 props；如果没有这段代码，父组件无法把运行状态、活动 turn 和取消回调注入 composer。
  isRunning?: boolean; // 新增代码+DesktopComposer：允许父组件告知运行中；如果没有这行，发送按钮无法避免重复提交。
  activeTurnId?: string | null; // 新增代码+DesktopComposerCancel：保存当前可取消的 turn id；如果没有这行代码，底部取消按钮不知道应该取消哪一轮。
  onCancelActiveTurn?: (turnId: string) => void; // 新增代码+DesktopComposerCancel：允许底部按钮调用父组件取消逻辑；如果没有这行代码，取消按钮只能显示不能真正请求后端。
  onSubmit?: (prompt: string) => void; // 新增代码+DesktopComposer：允许父组件接收 prompt；如果没有这行，输入框只能是静态装饰。
}; // 修改代码+DesktopComposerCancel：props 类型结束；如果没有这行代码，TypeScript 类型语法不完整。

export function Composer({ isRunning = false, activeTurnId = null, onCancelActiveTurn, onSubmit }: ComposerProps): JSX.Element { // 修改代码+DesktopComposerCancel：函数段开始，渲染底部输入工具条和运行中取消入口；如果没有这段代码，用户看不到发送 prompt 或取消当前 turn 的入口。
  const [draft, setDraft] = useState(""); // 新增代码+DesktopComposer：保存当前输入草稿；如果没有这行，组件无法判断空 prompt 或清空输入。
  const canSend = draft.trim().length > 0 && !isRunning; // 新增代码+DesktopComposer：计算是否允许发送；如果没有这行，空输入或运行中都可能误触发发送。
  const canCancel = isRunning && typeof activeTurnId === "string" && activeTurnId.length > 0; // 新增代码+DesktopComposerCancel：计算当前是否可以取消；如果没有这行代码，底部按钮无法在发送和取消两种职责之间安全切换。

  function submitDraft(): void { // 新增代码+DesktopComposer：函数段开始，提交当前草稿；如果没有这段，按钮和 Enter 键会重复写提交逻辑。
    if (!canSend) { // 新增代码+DesktopComposer：拦截不可发送状态；如果没有这行，空 prompt 会进入后端。
      return; // 新增代码+DesktopComposer：不可发送时直接退出；如果没有这行，后续仍会调用 onSubmit。
    } // 新增代码+DesktopComposer：不可发送判断结束；如果没有这行，条件块语法不完整。
    onSubmit?.(draft); // 新增代码+DesktopComposer：把 prompt 交给父组件；如果没有这行，用户输入不会进入应用状态。
    setDraft(""); // 新增代码+DesktopComposer：发送后清空输入；如果没有这行，重复发送时容易误提交旧内容。
  } // 新增代码+DesktopComposer：函数段结束，submitDraft 到此结束；如果没有这个边界，用户不容易看出提交逻辑范围。

  function cancelActiveTurn(): void { // 新增代码+DesktopComposerCancel：函数段开始，处理底部取消按钮；如果没有这段代码，运行中状态只能禁用发送，用户无法从固定入口中断任务。
    if (!canCancel || activeTurnId === null) { // 新增代码+DesktopComposerCancel：拦截没有活动 turn 的取消请求；如果没有这行代码，按钮可能会向后端发送空 turn id。
      return; // 新增代码+DesktopComposerCancel：不可取消时直接退出；如果没有这行代码，后续仍可能调用无效回调。
    } // 新增代码+DesktopComposerCancel：不可取消判断结束；如果没有这行代码，条件块语法不完整。
    onCancelActiveTurn?.(activeTurnId); // 新增代码+DesktopComposerCancel：把当前 turn id 交给父组件取消；如果没有这行代码，用户点击取消不会触发后端生命周期。
  } // 新增代码+DesktopComposerCancel：函数段结束，cancelActiveTurn 到此结束；如果没有这个边界，用户不容易看出取消逻辑范围。

  return ( // 新增代码+DesktopComposer：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 新增代码+DesktopComposer：定义 composer 容器；如果没有这行，输入框和按钮没有稳定布局。 */}
      <button className="icon-button" type="button" aria-label="添加附件"> {/* 新增代码+DesktopComposer：渲染附件按钮；如果没有这行，后续附件功能没有明确入口。 */}
        <Paperclip aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示附件图标；如果没有这行，按钮含义不直观。 */}
      </button> {/* 新增代码+DesktopComposer：附件按钮结束；如果没有这行，JSX 结构不完整。 */}
      <textarea className="composer-input" rows={1} placeholder="要求后续变更" value={draft} onChange={(event) => setDraft(event.currentTarget.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitDraft(); } }} /> {/* 新增代码+DesktopComposer：渲染受控 prompt 输入框并支持 Enter 发送；如果没有这行，用户无法输入或提交任务。 */}
      {canCancel ? (
        <button className="send-button cancel-button" type="button" aria-label="取消本轮" onClick={cancelActiveTurn}> {/* 新增代码+DesktopComposerCancel：渲染固定位置的取消按钮；如果没有这行代码，可见 GUI 验收只能依赖消息卡片里的小按钮。 */}
          <X aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposerCancel：显示取消图标；如果没有这行代码，运行中按钮的含义不够直观。 */}
        </button>
      ) : (
        <button className="send-button" type="button" aria-label="发送" disabled={!canSend} onClick={submitDraft}> {/* 修改代码+DesktopComposerCancel：渲染发送按钮并绑定提交；如果没有这行代码，用户看不到提交入口。 */}
          <ArrowUp aria-hidden={true} size={18} /> {/* 新增代码+DesktopComposer：显示发送图标；如果没有这行代码，按钮不够符合常见聊天工具心智。 */}
        </button>
      )} {/* 新增代码+DesktopComposerCancel：按钮状态分支结束；如果没有这行代码，运行中取消和普通发送无法共享同一个固定位置。 */}
    </footer> /* 新增代码+DesktopComposer：composer 容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopComposer：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopComposer：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
