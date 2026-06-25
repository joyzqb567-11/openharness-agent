import { ArrowUp, Paperclip, X } from "lucide-react"; // 修改代码+DesktopComposerV2：引入发送、附件和取消图标；如果没有这行代码，底部工具条缺少成熟桌面 GUI 的可识别按钮。
import { useState } from "react"; // 修改代码+DesktopComposerV2：引入本地输入和提交状态；如果没有这行，textarea 无法受控、发送后清空或显示提交中状态。

export type ComposerSubmitHandler = (prompt: string) => void | Promise<void>; // 新增代码+DesktopComposerV2：定义可同步或异步的提交回调；如果没有这行，组件无法等后端接受后再清空输入。
export type ComposerKeyIntent = { shouldSubmit: boolean; shouldInsertNewline: boolean; shouldPreventDefault: boolean }; // 新增代码+DesktopComposerV2：定义键盘意图结果；如果没有这行，Enter/Shift+Enter 行为难以单独测试。
export type ComposerButtonState = { mode: "send" | "cancel"; disabled: boolean; title: string; ariaLabel: string }; // 新增代码+DesktopComposerV2：定义底部按钮状态；如果没有这行，运行中禁用原因会散落在 JSX 里。

type ComposerProps = { // 修改代码+DesktopComposerV2：类型段开始，定义输入组件 props；如果没有这段，父组件无法注入运行状态、活动 turn 和提交回调。
  isRunning?: boolean; // 修改代码+DesktopComposerV2：允许父组件告知运行中；如果没有这行，发送按钮无法避免重复提交。
  activeTurnId?: string | null; // 修改代码+DesktopComposerV2：保存当前可取消的 turn id；如果没有这行，底部取消按钮不知道应该取消哪一轮。
  onCancelActiveTurn?: (turnId: string) => void; // 修改代码+DesktopComposerV2：允许底部按钮调用父组件取消逻辑；如果没有这行，取消按钮只能显示不能真正请求后端。
  onSubmit?: ComposerSubmitHandler; // 修改代码+DesktopComposerV2：允许父组件接收 prompt；如果没有这行，输入框只能是静态装饰。
}; // 修改代码+DesktopComposerV2：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function canSubmitComposerDraft(draft: string, sendBlocked: boolean): boolean { // 新增代码+DesktopComposerV2：函数段开始，判断草稿是否可发送；如果没有这段，按钮、Enter 和测试会各写一套规则。
  return draft.trim().length > 0 && !sendBlocked; // 新增代码+DesktopComposerV2：非空且未被运行/提交状态阻塞才可发送；如果没有这行，空白 prompt 或运行中 prompt 可能误入后端。
} // 新增代码+DesktopComposerV2：函数段结束，canSubmitComposerDraft 到此结束；如果没有这个边界，用户不容易看出发送条件范围。

export function composerKeyIntent(key: string, shiftKey: boolean): ComposerKeyIntent { // 新增代码+DesktopComposerV2：函数段开始，解释键盘输入意图；如果没有这段，Enter 和 Shift+Enter 行为不易回归测试。
  if (key !== "Enter") { // 新增代码+DesktopComposerV2：非 Enter 键不特殊处理；如果没有这行，普通输入可能被误拦截。
    return { shouldSubmit: false, shouldInsertNewline: false, shouldPreventDefault: false }; // 新增代码+DesktopComposerV2：返回普通按键意图；如果没有这行，函数对普通键没有输出。
  } // 新增代码+DesktopComposerV2：非 Enter 分支结束；如果没有这行，条件块语法不完整。
  if (shiftKey) { // 新增代码+DesktopComposerV2：识别 Shift+Enter；如果没有这行，多行输入会被误当发送。
    return { shouldSubmit: false, shouldInsertNewline: true, shouldPreventDefault: false }; // 新增代码+DesktopComposerV2：让浏览器保留默认换行和光标行为；如果没有这行，中文多行编辑会不稳定。
  } // 新增代码+DesktopComposerV2：Shift+Enter 分支结束；如果没有这行，条件块语法不完整。
  return { shouldSubmit: true, shouldInsertNewline: false, shouldPreventDefault: true }; // 新增代码+DesktopComposerV2：普通 Enter 发送并阻止换行；如果没有这行，回车会既发送又插入换行。
} // 新增代码+DesktopComposerV2：函数段结束，composerKeyIntent 到此结束；如果没有这个边界，用户不容易看出键盘规则范围。

export async function submitComposerDraft(draft: string, sendBlocked: boolean, onSubmit?: ComposerSubmitHandler): Promise<{ submitted: boolean; nextDraft: string }> { // 新增代码+DesktopComposerV2：函数段开始，提交草稿并决定是否清空；如果没有这段，组件无法保证“后端接受后再清空”。
  if (!canSubmitComposerDraft(draft, sendBlocked) || onSubmit === undefined) { // 新增代码+DesktopComposerV2：拦截不可发送或没有提交回调的情况；如果没有这行，空白或无人接收的 prompt 会被清空。
    return { submitted: false, nextDraft: draft }; // 新增代码+DesktopComposerV2：保留原草稿；如果没有这行，失败前输入会丢失。
  } // 新增代码+DesktopComposerV2：不可发送判断结束；如果没有这行，条件块语法不完整。
  await onSubmit(draft); // 新增代码+DesktopComposerV2：等待父组件或后端接受 prompt；如果没有这行，异步失败时输入也会被提前清空。
  return { submitted: true, nextDraft: "" }; // 新增代码+DesktopComposerV2：提交成功后清空草稿；如果没有这行，成功发送后旧内容会残留。
} // 新增代码+DesktopComposerV2：函数段结束，submitComposerDraft 到此结束；如果没有这个边界，用户不容易看出提交清空规则范围。

export function composerButtonState(draft: string, isRunning: boolean, isSubmitting: boolean, canCancel: boolean): ComposerButtonState { // 新增代码+DesktopComposerV2：函数段开始，计算底部按钮状态；如果没有这段，运行中原因和 disabled 状态会难以测试。
  if (canCancel) { // 新增代码+DesktopComposerV2：运行中且有活动 turn 时优先显示取消；如果没有这行，用户无法从固定位置中断任务。
    return { mode: "cancel", disabled: false, title: "正在运行，点击取消本轮", ariaLabel: "取消本轮，正在运行时不能发送" }; // 新增代码+DesktopComposerV2：返回取消按钮状态和原因；如果没有这行，运行中按钮语义不清楚。
  } // 新增代码+DesktopComposerV2：取消分支结束；如果没有这行，条件块语法不完整。
  if (isSubmitting) { // 新增代码+DesktopComposerV2：识别本地提交中；如果没有这行，快速连点可能重复提交。
    return { mode: "send", disabled: true, title: "正在发送，请稍候", ariaLabel: "正在发送，暂不能重复发送" }; // 新增代码+DesktopComposerV2：返回提交中禁用原因；如果没有这行，用户不知道按钮为什么不可用。
  } // 新增代码+DesktopComposerV2：提交中分支结束；如果没有这行，条件块语法不完整。
  if (isRunning) { // 新增代码+DesktopComposerV2：识别后端运行中但没有可取消 turn 的状态；如果没有这行，运行中禁用原因不可见。
    return { mode: "send", disabled: true, title: "正在运行，暂不能发送", ariaLabel: "正在运行，暂不能发送" }; // 新增代码+DesktopComposerV2：返回运行中禁用原因；如果没有这行，用户只能看到按钮灰掉。
  } // 新增代码+DesktopComposerV2：运行中分支结束；如果没有这行，条件块语法不完整。
  if (draft.trim().length === 0) { // 新增代码+DesktopComposerV2：识别空白草稿；如果没有这行，空输入禁用原因不清楚。
    return { mode: "send", disabled: true, title: "请输入内容", ariaLabel: "发送，需要先输入内容" }; // 新增代码+DesktopComposerV2：返回空输入禁用原因；如果没有这行，用户不清楚为什么不能发送。
  } // 新增代码+DesktopComposerV2：空白草稿分支结束；如果没有这行，条件块语法不完整。
  return { mode: "send", disabled: false, title: "发送", ariaLabel: "发送" }; // 新增代码+DesktopComposerV2：返回可发送状态；如果没有这行，正常输入也无法启用按钮。
} // 新增代码+DesktopComposerV2：函数段结束，composerButtonState 到此结束；如果没有这个边界，用户不容易看出按钮状态范围。

export function Composer({ isRunning = false, activeTurnId = null, onCancelActiveTurn, onSubmit }: ComposerProps): JSX.Element { // 修改代码+DesktopComposerV2：函数段开始，渲染底部输入工具条和运行中取消入口；如果没有这段，用户看不到发送 prompt 或取消当前 turn 的入口。
  const [draft, setDraft] = useState(""); // 修改代码+DesktopComposerV2：保存当前输入草稿；如果没有这行，组件无法判断空 prompt 或清空输入。
  const [isSubmitting, setIsSubmitting] = useState(false); // 新增代码+DesktopComposerV2：保存本地提交中状态；如果没有这行，异步发送期间可能重复提交。
  const sendBlocked = isRunning || isSubmitting; // 新增代码+DesktopComposerV2：统一计算发送是否被阻塞；如果没有这行，按钮和提交函数可能判断不一致。
  const canCancel = isRunning && typeof activeTurnId === "string" && activeTurnId.length > 0; // 修改代码+DesktopComposerV2：计算当前是否可以取消；如果没有这行，底部按钮无法在发送和取消两种职责之间安全切换。
  const buttonState = composerButtonState(draft, isRunning, isSubmitting, canCancel); // 新增代码+DesktopComposerV2：计算按钮 UI 状态；如果没有这行，title、disabled 和模式会散落在 JSX。

  async function submitDraft(): Promise<void> { // 修改代码+DesktopComposerV2：函数段开始，提交当前草稿；如果没有这段，按钮和 Enter 键会重复写提交逻辑。
    const currentDraft = draft; // 新增代码+DesktopComposerV2：冻结本次提交的文本；如果没有这行，异步等待期间用户编辑可能影响发送内容。
    if (!canSubmitComposerDraft(currentDraft, sendBlocked)) { // 修改代码+DesktopComposerV2：拦截不可发送状态；如果没有这行，空 prompt 或运行中 prompt 会进入后端。
      return; // 修改代码+DesktopComposerV2：不可发送时直接退出；如果没有这行，后续仍会调用 onSubmit。
    } // 修改代码+DesktopComposerV2：不可发送判断结束；如果没有这行，条件块语法不完整。
    setIsSubmitting(true); // 新增代码+DesktopComposerV2：标记正在提交；如果没有这行，用户可以在等待后端时重复点击。
    try { // 新增代码+DesktopComposerV2：保护异步提交；如果没有这行，失败时无法恢复提交中状态。
      const result = await submitComposerDraft(currentDraft, false, onSubmit); // 新增代码+DesktopComposerV2：等待提交规则执行；如果没有这行，组件不会复用已测试的纯提交逻辑。
      if (result.submitted) { // 新增代码+DesktopComposerV2：只在提交成功后清空；如果没有这行，后端拒绝时输入也会被清掉。
        setDraft(result.nextDraft); // 新增代码+DesktopComposerV2：清空或保留草稿；如果没有这行，成功发送后旧内容会残留。
      } // 新增代码+DesktopComposerV2：成功清空分支结束；如果没有这行，条件块语法不完整。
    } finally { // 新增代码+DesktopComposerV2：无论成功失败都恢复按钮；如果没有这行，异常后按钮可能一直禁用。
      setIsSubmitting(false); // 新增代码+DesktopComposerV2：结束本地提交状态；如果没有这行，发送按钮可能永久显示正在发送。
    } // 新增代码+DesktopComposerV2：提交清理结束；如果没有这行，finally 块语法不完整。
  } // 修改代码+DesktopComposerV2：函数段结束，submitDraft 到此结束；如果没有这个边界，用户不容易看出提交逻辑范围。

  function cancelActiveTurn(): void { // 修改代码+DesktopComposerV2：函数段开始，处理底部取消按钮；如果没有这段，运行中状态只能禁用发送，用户无法从固定入口中断任务。
    if (!canCancel || activeTurnId === null) { // 修改代码+DesktopComposerV2：拦截没有活动 turn 的取消请求；如果没有这行，按钮可能会向后端发送空 turn id。
      return; // 修改代码+DesktopComposerV2：不可取消时直接退出；如果没有这行，后续仍可能调用无效回调。
    } // 修改代码+DesktopComposerV2：不可取消判断结束；如果没有这行，条件块语法不完整。
    onCancelActiveTurn?.(activeTurnId); // 修改代码+DesktopComposerV2：把当前 turn id 交给父组件取消；如果没有这行，用户点击取消不会触发后端生命周期。
  } // 修改代码+DesktopComposerV2：函数段结束，cancelActiveTurn 到此结束；如果没有这个边界，用户不容易看出取消逻辑范围。

  return ( // 修改代码+DesktopComposerV2：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 修改代码+DesktopComposerV2：定义 composer 容器；如果没有这行，输入框和按钮没有稳定布局。 */}
      <button className="icon-button" type="button" aria-label="添加附件"> {/* 修改代码+DesktopComposerV2：渲染附件按钮；如果没有这行，后续附件功能没有明确入口。 */}
        <Paperclip aria-hidden={true} size={18} /> {/* 修改代码+DesktopComposerV2：显示附件图标；如果没有这行，按钮含义不直观。 */}
      </button> {/* 修改代码+DesktopComposerV2：附件按钮结束；如果没有这行，JSX 结构不完整。 */}
      <textarea className="composer-input" rows={1} placeholder="要求后续变更" value={draft} onChange={(event) => setDraft(event.currentTarget.value)} onKeyDown={(event) => { const intent = composerKeyIntent(event.key, event.shiftKey); if (intent.shouldPreventDefault) { event.preventDefault(); void submitDraft(); } }} /> {/* 修改代码+DesktopComposerV2：渲染受控输入框并让 Shift+Enter 保持原生换行；如果没有这行，用户无法稳定输入中文多行 prompt。 */}
      {buttonState.mode === "cancel" ? ( // 修改代码+DesktopComposerV2：运行中优先渲染取消按钮；如果没有这行，用户无法从固定位置中断任务。
        <button className="send-button cancel-button" type="button" aria-label={buttonState.ariaLabel} title={buttonState.title} onClick={cancelActiveTurn}> {/* 修改代码+DesktopComposerV2：渲染取消按钮和运行中原因；如果没有这行，可见 GUI 验收只能依赖消息卡片里的小按钮。 */}
          <X aria-hidden={true} size={18} /> {/* 修改代码+DesktopComposerV2：显示取消图标；如果没有这行，运行中按钮的含义不够直观。 */}
        </button> // 修改代码+DesktopComposerV2：取消按钮结束；如果没有这行，JSX 结构不完整。
      ) : ( // 修改代码+DesktopComposerV2：普通状态渲染发送按钮；如果没有这行，非运行态没有提交入口。
        <button className="send-button" type="button" aria-label={buttonState.ariaLabel} title={buttonState.title} disabled={buttonState.disabled} onClick={() => { void submitDraft(); }}> {/* 修改代码+DesktopComposerV2：渲染发送按钮并绑定提交；如果没有这行，用户看不到提交入口。 */}
          <ArrowUp aria-hidden={true} size={18} /> {/* 修改代码+DesktopComposerV2：显示发送图标；如果没有这行，按钮不够符合常见聊天工具心智。 */}
        </button> // 修改代码+DesktopComposerV2：发送按钮结束；如果没有这行，JSX 结构不完整。
      )} {/* 修改代码+DesktopComposerV2：按钮状态分支结束；如果没有这行，运行中取消和普通发送无法共享同一个固定位置。 */}
    </footer> // 修改代码+DesktopComposerV2：composer 容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopComposerV2：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopComposerV2：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
