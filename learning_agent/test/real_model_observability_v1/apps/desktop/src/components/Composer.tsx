import { ArrowUp, Paperclip, X } from "lucide-react"; // 修改代码+DesktopComposerV2：引入发送、附件和取消图标；如果没有这行代码，底部工具条缺少成熟桌面 GUI 的可识别按钮。
import { useState } from "react"; // 修改代码+DesktopComposerV2：引入本地输入和提交状态；如果没有这行，textarea 无法受控、发送后清空或显示提交中状态。
import { ModelCallStatus, type ModelCallStatusView } from "./ModelCallStatus"; // 新增代码+RealModelObservability：引入真实模型调用状态条；如果没有这一行，Composer 无法显示连接、首包和 fallback 阶段。

export type ComposerReasoningEffort = "low" | "medium" | "high" | "ultra"; // 新增代码+DirectSSEPayload：定义 Codex 风格推理强度枚举；如果没有这行，Composer 无法类型化传给后端的 reasoningEffort。
export type ComposerPermissionMode = "read_only" | "workspace_write" | "full_access"; // 新增代码+DirectSSEPayload：定义 GUI 权限模式枚举；如果没有这行，Composer 无法类型化传给后端的 permissionMode。
export type ComposerSubmitPayload = { prompt: string; providerId: string; modelId: string; reasoningEffort: ComposerReasoningEffort; permissionMode: ComposerPermissionMode }; // 新增代码+DirectSSEPayload：定义结构化提交 payload；如果没有这行，底部输入只能继续传 prompt 字符串。
export type ComposerSubmitOptions = { providerId?: string; modelId?: string; reasoningEffort?: ComposerReasoningEffort; permissionMode?: ComposerPermissionMode }; // 新增代码+DirectSSEPayload：定义提交时可覆盖的模型路由字段；如果没有这行，纯函数测试无法注入模型选择。
export type ComposerSubmitHandler = (payload: ComposerSubmitPayload) => void | Promise<void>; // 修改代码+DirectSSEPayload：定义可同步或异步的结构化提交回调；如果没有这行，组件无法等后端接受后再清空输入。
export type ComposerKeyIntent = { shouldSubmit: boolean; shouldInsertNewline: boolean; shouldPreventDefault: boolean }; // 新增代码+DesktopComposerV2：定义键盘意图结果；如果没有这行，Enter/Shift+Enter 行为难以单独测试。
export type ComposerButtonState = { mode: "send" | "cancel"; disabled: boolean; title: string; ariaLabel: string }; // 新增代码+DesktopComposerV2：定义底部按钮状态；如果没有这行，运行中禁用原因会散落在 JSX 里。
export type ComposerModelOption = { providerId: string; modelId: string; label: string; disabled?: boolean }; // 新增代码+ComposerRouteControls：定义底部模型下拉选项；如果没有这行，AppShell 无法把 provider/model 组合安全传给 Composer。

type ComposerProps = { // 修改代码+DesktopComposerV2：类型段开始，定义输入组件 props；如果没有这段，父组件无法注入运行状态、活动 turn 和提交回调。
  isRunning?: boolean; // 修改代码+DesktopComposerV2：允许父组件告知运行中；如果没有这行，发送按钮无法避免重复提交。
  activeTurnId?: string | null; // 修改代码+DesktopComposerV2：保存当前可取消的 turn id；如果没有这行，底部取消按钮不知道应该取消哪一轮。
  selectedProviderId?: string; // 新增代码+DirectSSEPayload：保存父组件选择的 provider；如果没有这行，Composer 无法把 OpenAI 选择放进提交 payload。
  selectedModelId?: string; // 新增代码+DirectSSEPayload：保存父组件选择的模型；如果没有这行，Composer 无法把 gpt-5.5 等选择放进提交 payload。
  reasoningEffort?: ComposerReasoningEffort; // 新增代码+DirectSSEPayload：保存父组件选择的推理强度；如果没有这行，底部“超高”等选择无法传后端。
  permissionMode?: ComposerPermissionMode; // 新增代码+DirectSSEPayload：保存父组件选择的权限模式；如果没有这行，底部“完全访问”等选择无法传后端。
  modelOptions?: ComposerModelOption[]; // 新增代码+ComposerRouteControls：保存可选模型列表；如果没有这行，底部模型下拉只能显示硬编码模型。
  modelCallStatus?: ModelCallStatusView | null; // 新增代码+RealModelObservability：保存最新模型调用状态；如果没有这一行，父组件无法把后端慢调用阶段传进输入区。
  onModelChange?: (providerId: string, modelId: string) => void; // 新增代码+ComposerRouteControls：保存模型选择回调；如果没有这行，用户切换模型不会更新提交 payload。
  onReasoningEffortChange?: (value: ComposerReasoningEffort) => void; // 新增代码+ComposerRouteControls：保存推理强度回调；如果没有这行，“低/中/高/超高”下拉只是装饰。
  onPermissionModeChange?: (value: ComposerPermissionMode) => void; // 新增代码+ComposerRouteControls：保存权限模式回调；如果没有这行，“完全访问”等选择不会进入后端。
  onCancelActiveTurn?: (turnId: string) => void; // 修改代码+DesktopComposerV2：允许底部按钮调用父组件取消逻辑；如果没有这行，取消按钮只能显示不能真正请求后端。
  onSubmit?: ComposerSubmitHandler; // 修改代码+DirectSSEPayload：允许父组件接收结构化提交 payload；如果没有这行，输入框只能是静态装饰。
}; // 修改代码+DesktopComposerV2：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function composerModelOptionValue(providerId: string, modelId: string): string { // 新增代码+ComposerRouteControls：函数段开始，生成模型下拉 value；如果没有这段，provider 和 model 拼接规则会散落在 JSX 和测试中。
  return providerId.length > 0 && modelId.length > 0 ? `${providerId}::${modelId}` : ""; // 新增代码+ComposerRouteControls：只有 provider/model 都存在才生成 value；如果没有这行，空选择可能伪装成真实模型。
} // 新增代码+ComposerRouteControls：函数段结束，composerModelOptionValue 到此结束；如果没有这行，函数语法不完整。

export function parseComposerModelOptionValue(value: string): { providerId: string; modelId: string } { // 新增代码+ComposerRouteControls：函数段开始，解析模型下拉 value；如果没有这段，onChange 会用脆弱字符串切割。
  const [providerId = "", modelId = ""] = value.split("::"); // 新增代码+ComposerRouteControls：按内部分隔符拆 provider 和 model；如果没有这行，父组件拿不到两段路由。
  return { providerId, modelId }; // 新增代码+ComposerRouteControls：返回结构化结果；如果没有这行，调用方无法更新 route state。
} // 新增代码+ComposerRouteControls：函数段结束，parseComposerModelOptionValue 到此结束；如果没有这行，函数语法不完整。

export function normalizeComposerSubmitOptions(options: ComposerSubmitOptions = {}): Omit<ComposerSubmitPayload, "prompt"> { // 新增代码+DirectSSEPayload：函数段开始，生成结构化提交默认值；如果没有这段，AppShell 和测试会各自拼默认字段。
  return { providerId: options.providerId ?? "", modelId: options.modelId ?? "", reasoningEffort: options.reasoningEffort ?? "high", permissionMode: options.permissionMode ?? "full_access" }; // 新增代码+DirectSSEPayload：返回安全默认路由字段；如果没有这行，后端可能收到 undefined 或非法空洞。
} // 新增代码+DirectSSEPayload：函数段结束，normalizeComposerSubmitOptions 到此结束；如果没有这个边界，用户不容易看出默认值范围。

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

export async function submitComposerDraft(draft: string, sendBlocked: boolean, onSubmit?: ComposerSubmitHandler, options: ComposerSubmitOptions = {}): Promise<{ submitted: boolean; nextDraft: string }> { // 修改代码+DirectSSEPayload：函数段开始，提交草稿和模型路由字段；如果没有这段，组件无法保证“后端接受后再清空”。
  if (!canSubmitComposerDraft(draft, sendBlocked) || onSubmit === undefined) { // 新增代码+DesktopComposerV2：拦截不可发送或没有提交回调的情况；如果没有这行，空白或无人接收的 prompt 会被清空。
    return { submitted: false, nextDraft: draft }; // 新增代码+DesktopComposerV2：保留原草稿；如果没有这行，失败前输入会丢失。
  } // 新增代码+DesktopComposerV2：不可发送判断结束；如果没有这行，条件块语法不完整。
  await onSubmit({ prompt: draft, ...normalizeComposerSubmitOptions(options) }); // 修改代码+DirectSSEPayload：等待父组件接收结构化 payload；如果没有这行，provider/model 选择不会随 prompt 提交。
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

export function Composer({ isRunning = false, activeTurnId = null, selectedProviderId = "", selectedModelId = "", reasoningEffort = "high", permissionMode = "full_access", modelOptions = [], modelCallStatus = null, onModelChange, onReasoningEffortChange, onPermissionModeChange, onCancelActiveTurn, onSubmit }: ComposerProps): JSX.Element { // 修改代码+RealModelObservability：函数段开始，渲染底部输入工具条、模型选择和模型调用状态；如果没有这段，用户看不到真实模型阶段。
  const [draft, setDraft] = useState(""); // 修改代码+DesktopComposerV2：保存当前输入草稿；如果没有这行，组件无法判断空 prompt 或清空输入。
  const [isSubmitting, setIsSubmitting] = useState(false); // 新增代码+DesktopComposerV2：保存本地提交中状态；如果没有这行，异步发送期间可能重复提交。
  const sendBlocked = isRunning || isSubmitting; // 新增代码+DesktopComposerV2：统一计算发送是否被阻塞；如果没有这行，按钮和提交函数可能判断不一致。
  const canCancel = isRunning && typeof activeTurnId === "string" && activeTurnId.length > 0; // 修改代码+DesktopComposerV2：计算当前是否可以取消；如果没有这行，底部按钮无法在发送和取消两种职责之间安全切换。
  const buttonState = composerButtonState(draft, isRunning, isSubmitting, canCancel); // 新增代码+DesktopComposerV2：计算按钮 UI 状态；如果没有这行，title、disabled 和模式会散落在 JSX。
  const selectedModelValue = composerModelOptionValue(selectedProviderId, selectedModelId); // 新增代码+ComposerRouteControls：把当前 provider/model 转成下拉 value；如果没有这行，模型下拉无法显示当前选择。

  async function submitDraft(): Promise<void> { // 修改代码+DesktopComposerV2：函数段开始，提交当前草稿；如果没有这段，按钮和 Enter 键会重复写提交逻辑。
    const currentDraft = draft; // 新增代码+DesktopComposerV2：冻结本次提交的文本；如果没有这行，异步等待期间用户编辑可能影响发送内容。
    if (!canSubmitComposerDraft(currentDraft, sendBlocked)) { // 修改代码+DesktopComposerV2：拦截不可发送状态；如果没有这行，空 prompt 或运行中 prompt 会进入后端。
      return; // 修改代码+DesktopComposerV2：不可发送时直接退出；如果没有这行，后续仍会调用 onSubmit。
    } // 修改代码+DesktopComposerV2：不可发送判断结束；如果没有这行，条件块语法不完整。
    setIsSubmitting(true); // 新增代码+DesktopComposerV2：标记正在提交；如果没有这行，用户可以在等待后端时重复点击。
    try { // 新增代码+DesktopComposerV2：保护异步提交；如果没有这行，失败时无法恢复提交中状态。
      const result = await submitComposerDraft(currentDraft, false, onSubmit, { providerId: selectedProviderId, modelId: selectedModelId, reasoningEffort, permissionMode }); // 修改代码+DirectSSEPayload：等待提交规则执行并附带模型路由字段；如果没有这行，父组件选择不会进入提交 payload。
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

  function selectModel(value: string): void { // 新增代码+ComposerRouteControls：函数段开始，处理模型下拉变化；如果没有这段，用户选择模型后不会更新后端路由字段。
    const parsed = parseComposerModelOptionValue(value); // 新增代码+ComposerRouteControls：解析 provider/model 组合值；如果没有这行，回调只能拿到难读字符串。
    onModelChange?.(parsed.providerId, parsed.modelId); // 新增代码+ComposerRouteControls：把模型选择交回 AppShell；如果没有这行，提交 payload 仍会带旧模型。
  } // 新增代码+ComposerRouteControls：函数段结束，selectModel 到此结束；如果没有这行，函数语法不完整。

  return ( // 修改代码+DesktopComposerV2：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 修改代码+DesktopComposerV2：定义 composer 容器；如果没有这行，输入框和按钮没有稳定布局。 */}
      <div className="composer-input-row"> {/* 新增代码+ComposerRouteControls：包裹附件、输入框和发送按钮；如果没有这行，新增下拉行会破坏原三列布局。 */}
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
      </div> {/* 新增代码+ComposerRouteControls：输入按钮行结束；如果没有这行，JSX 结构不完整。 */}
      <div className="composer-model-status-slot" aria-live="polite"> {/* 新增代码+RealModelObservability：渲染模型调用状态固定槽；如果没有这一行，状态出现时会挤压底部按钮或跳动布局。 */}
        <ModelCallStatus status={modelCallStatus} compact={true} /> {/* 新增代码+RealModelObservability：显示紧凑模型状态；如果没有这一行，用户仍要去右侧时间线猜后端卡在哪里。 */}
      </div> {/* 新增代码+RealModelObservability：模型状态固定槽结束；如果没有这一行，JSX 结构不完整。 */}
      <div className="composer-route-row" aria-label="模型和执行设置"> {/* 新增代码+ComposerRouteControls：渲染底部模型路由条；如果没有这行，OAuth 连接后用户仍找不到模型、权限和推理强度。 */}
        <select className="composer-route-select composer-model-select" aria-label="选择模型" value={selectedModelValue} onChange={(event) => selectModel(event.currentTarget.value)}> {/* 新增代码+ComposerRouteControls：渲染模型下拉；如果没有这行，用户无法选择 gpt-5.5 等 OAuth 模型。 */}
          <option value="">选择模型</option> {/* 新增代码+ComposerRouteControls：提供断开或未连接时的空选择；如果没有这行，断开后下拉仍可能显示旧模型。 */}
          {modelOptions.map((option) => ( // 新增代码+ComposerRouteControls：遍历后端 provider catalog 派生的模型；如果没有这行，下拉无法反映真实可用列表。
            <option disabled={option.disabled} key={composerModelOptionValue(option.providerId, option.modelId)} value={composerModelOptionValue(option.providerId, option.modelId)}>{option.label}</option> // 新增代码+ComposerRouteControls：渲染单个模型选项；如果没有这行，用户看不到具体模型。
          ))} {/* 新增代码+ComposerRouteControls：模型选项遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </select> {/* 新增代码+ComposerRouteControls：模型下拉结束；如果没有这行，JSX 结构不完整。 */}
        <select className="composer-route-select" aria-label="推理强度" value={reasoningEffort} onChange={(event) => onReasoningEffortChange?.(event.currentTarget.value as ComposerReasoningEffort)}> {/* 新增代码+ComposerRouteControls：渲染推理强度下拉；如果没有这行，用户无法像 Codex 一样调低或调高推理。 */}
          <option value="low">低</option> {/* 新增代码+ComposerRouteControls：低推理选项；如果没有这行，轻量任务不能走低成本路径。 */}
          <option value="medium">中</option> {/* 新增代码+ComposerRouteControls：中推理选项；如果没有这行，用户缺少折中档位。 */}
          <option value="high">高</option> {/* 新增代码+ComposerRouteControls：高推理选项；如果没有这行，复杂任务缺少默认强档。 */}
          <option value="ultra">超高</option> {/* 新增代码+ComposerRouteControls：超高推理选项；如果没有这行，用户看不到 Codex 截图同款档位。 */}
        </select> {/* 新增代码+ComposerRouteControls：推理强度下拉结束；如果没有这行，JSX 结构不完整。 */}
        <select className="composer-route-select" aria-label="权限模式" value={permissionMode} onChange={(event) => onPermissionModeChange?.(event.currentTarget.value as ComposerPermissionMode)}> {/* 新增代码+ComposerRouteControls：渲染权限模式下拉；如果没有这行，完全访问/只读选择无法进入后端。 */}
          <option value="read_only">只读</option> {/* 新增代码+ComposerRouteControls：只读权限选项；如果没有这行，低风险查看任务不能声明权限边界。 */}
          <option value="workspace_write">工作区写入</option> {/* 新增代码+ComposerRouteControls：工作区写入选项；如果没有这行，中等权限任务无法选择。 */}
          <option value="full_access">完全访问</option> {/* 新增代码+ComposerRouteControls：完全访问选项；如果没有这行，真实 Codex 风格任务无法显式授权。 */}
        </select> {/* 新增代码+ComposerRouteControls：权限模式下拉结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+ComposerRouteControls：底部模型路由条结束；如果没有这行，JSX 结构不完整。 */}
    </footer> // 修改代码+DesktopComposerV2：composer 容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopComposerV2：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopComposerV2：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
