import { ArrowUp, ChevronDown, Mic, Plus, ShieldCheck, X } from "lucide-react"; // 修改代码+ComposerModelToolbar：引入 Codex 底部栏需要的图标；如果没有这行，附件、权限、模型、语音和发送入口会缺少成熟 GUI 的视觉锚点。
import { useState } from "react"; // 修改代码+ComposerModelToolbar：引入本地输入和提交状态；如果没有这行，textarea 无法受控，发送后也无法安全清空草稿。
import { ModelCallStatus, type ModelCallStatusView } from "./ModelCallStatus"; // 新增代码+RealModelLatencyV2：引入真实模型调用状态条；如果没有这行，底部无法显示连接、fallback 和首响应状态。

export type ComposerPermissionMode = "full-access" | "ask" | "read-only"; // 新增代码+ComposerModelToolbar：定义底部权限模式；如果没有这行，完全访问/请求确认/只读会变成散落字符串。
export type ComposerReasoningEffort = "low" | "medium" | "high" | "ultra"; // 新增代码+ComposerModelToolbar：定义推理强度档位；如果没有这行，Codex 式推理菜单没有稳定合同。
export type ComposerModelFailure = { errorKind: string; message: string; failedAt: number }; // 新增代码+ModelFailureState：定义模型最近失败摘要；如果没有这行，Composer 只能收到真假不明的原始失败对象。
export type ComposerModelOption = { id: string; label: string; providerId: string; providerName: string; supportsTools: boolean; supportsVision: boolean; recentFailure: ComposerModelFailure | null }; // 修改代码+ModelFailureState：定义底部模型选项并带最近失败；如果没有这行，模型下拉无法提示刚刚失败的 OAuth 模型。
export type ComposerSubmitOptions = { providerId?: string; modelId?: string; reasoningEffort: ComposerReasoningEffort; permissionMode: ComposerPermissionMode }; // 新增代码+ComposerModelToolbar：定义随 prompt 一起提交的运行上下文；如果没有这行，后端不知道用户选了哪个模型和权限。
export type ComposerSubmitHandler = (prompt: string, options?: ComposerSubmitOptions) => void | Promise<void>; // 修改代码+ComposerModelToolbar：让提交回调接收模型上下文；如果没有这行，底部菜单只是视觉摆设。
export type ComposerKeyIntent = { shouldSubmit: boolean; shouldInsertNewline: boolean; shouldPreventDefault: boolean }; // 新增代码+DesktopComposerV2：定义键盘意图结构；如果没有这行，Enter/Shift+Enter 行为难以单独测试。
export type ComposerButtonState = { mode: "send" | "cancel"; disabled: boolean; title: string; ariaLabel: string }; // 新增代码+DesktopComposerV2：定义底部按钮状态；如果没有这行，运行中禁用原因会散落在 JSX 里。

type ComposerProps = { // 修改代码+ComposerModelToolbar：props 类型段开始，定义输入组件可接收的运行状态、模型菜单和提交回调；如果没有这段，父组件无法注入真实 provider/model 状态。
  isRunning?: boolean; // 修改代码+DesktopComposerV2：允许父组件告知运行中；如果没有这行，发送按钮无法避免重复提交。
  activeTurnId?: string | null; // 修改代码+DesktopComposerV2：保存当前可取消的 turn id；如果没有这行，底部取消按钮不知道应该取消哪一轮。
  modelOptions?: ComposerModelOption[]; // 新增代码+ComposerModelToolbar：接收已连接 provider 的可见模型；如果没有这行，OAuth 连接后底部仍没有模型来源。
  selectedModelId?: string; // 新增代码+ComposerModelToolbar：接收当前选中的模型 id；如果没有这行，模型下拉无法保持父组件状态。
  reasoningEffort?: ComposerReasoningEffort; // 新增代码+ComposerModelToolbar：接收当前推理强度；如果没有这行，推理档位只能写死。
  permissionMode?: ComposerPermissionMode; // 新增代码+ComposerModelToolbar：接收当前权限模式；如果没有这行，完全访问菜单无法被父组件控制。
  modelCallStatus?: ModelCallStatusView | null; // 新增代码+RealModelLatencyV2：接收最新模型调用状态；如果没有这行，Composer 无法在输入区展示真实慢调用阶段。
  onCancelActiveTurn?: (turnId: string) => void; // 修改代码+DesktopComposerV2：允许底部按钮调用父组件取消逻辑；如果没有这行，取消按钮只能显示不能真正请求后端。
  onModelChange?: (modelId: string) => void; // 新增代码+ComposerModelToolbar：通知父组件模型选择变化；如果没有这行，用户选择不会被保存到 AppShell。
  onReasoningEffortChange?: (value: ComposerReasoningEffort) => void; // 新增代码+ComposerModelToolbar：通知父组件推理强度变化；如果没有这行，推理菜单不会影响提交上下文。
  onPermissionModeChange?: (value: ComposerPermissionMode) => void; // 新增代码+ComposerModelToolbar：通知父组件权限模式变化；如果没有这行，完全访问菜单不会影响提交上下文。
  onSubmit?: ComposerSubmitHandler; // 修改代码+ComposerModelToolbar：允许父组件接收 prompt 和上下文；如果没有这行，输入框只能是静态装饰。
}; // 修改代码+ComposerModelToolbar：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

const COMPOSER_PERMISSION_OPTIONS: Array<{ value: ComposerPermissionMode; label: string; title: string }> = [ // 新增代码+ComposerModelToolbar：定义权限菜单文案；如果没有这段，权限菜单选项会散落在 JSX 中。
  { value: "full-access", label: "完全访问", title: "允许 OpenHarness 在本机范围内执行需要的操作" }, // 新增代码+ComposerModelToolbar：定义完全访问选项；如果没有这行，用户找不到 Codex 截图里的完全访问入口。
  { value: "ask", label: "请求确认", title: "高风险操作前先询问用户" }, // 新增代码+ComposerModelToolbar：定义确认模式；如果没有这行，用户无法选择更保守的执行方式。
  { value: "read-only", label: "只读", title: "只允许读取和分析，不执行写入动作" }, // 新增代码+ComposerModelToolbar：定义只读模式；如果没有这行，安全查看项目时缺少低风险模式。
]; // 新增代码+ComposerModelToolbar：权限菜单文案结束；如果没有这行，数组语法不完整。

const COMPOSER_REASONING_OPTIONS: Array<{ value: ComposerReasoningEffort; label: string }> = [ // 新增代码+ComposerModelToolbar：定义推理强度菜单；如果没有这段，Codex 式低/中/高/超高菜单没有事实源。
  { value: "low", label: "低" }, // 新增代码+ComposerModelToolbar：定义低推理；如果没有这行，快速低成本任务无法表达。
  { value: "medium", label: "中" }, // 新增代码+ComposerModelToolbar：定义中推理；如果没有这行，默认平衡档位缺失。
  { value: "high", label: "高" }, // 新增代码+ComposerModelToolbar：定义高推理；如果没有这行，复杂任务无法选择更强推理。
  { value: "ultra", label: "超高" }, // 新增代码+ComposerModelToolbar：定义超高推理；如果没有这行，用户截图里的超高档位缺失。
]; // 新增代码+ComposerModelToolbar：推理菜单文案结束；如果没有这行，数组语法不完整。

export function canSubmitComposerDraft(draft: string, sendBlocked: boolean): boolean { // 新增代码+DesktopComposerV2：函数段开始，判断草稿是否可发送；如果没有这段，按钮、Enter 和测试会各写一套规则。
  return draft.trim().length > 0 && !sendBlocked; // 新增代码+DesktopComposerV2：非空且未被运行/提交状态阻塞才可发送；如果没有这行，空白 prompt 或运行中 prompt 可能误入后端。
} // 新增代码+DesktopComposerV2：函数段结束，canSubmitComposerDraft 到此结束；如果没有这个边界，用户不容易看出发送条件范围。

export function composerKeyIntent(key: string, shiftKey: boolean): ComposerKeyIntent { // 新增代码+DesktopComposerV2：函数段开始，解释键盘输入意图；如果没有这段，Enter 和 Shift+Enter 行为不易回归测试。
  if (key !== "Enter") { // 新增代码+DesktopComposerV2：非 Enter 键不特殊处理；如果没有这行，普通输入可能被误拦截。
    return { shouldSubmit: false, shouldInsertNewline: false, shouldPreventDefault: false }; // 新增代码+DesktopComposerV2：返回普通按键意图；如果没有这行，函数对普通键没有输出。
  } // 新增代码+DesktopComposerV2：非 Enter 分支结束；如果没有这行，条件块语法不完整。
  if (shiftKey) { // 新增代码+DesktopComposerV2：识别 Shift+Enter；如果没有这行，多行输入会被误当发送。
    return { shouldSubmit: false, shouldInsertNewline: true, shouldPreventDefault: false }; // 新增代码+DesktopComposerV2：让浏览器保留默认换行；如果没有这行，中文多行编辑会不稳定。
  } // 新增代码+DesktopComposerV2：Shift+Enter 分支结束；如果没有这行，条件块语法不完整。
  return { shouldSubmit: true, shouldInsertNewline: false, shouldPreventDefault: true }; // 新增代码+DesktopComposerV2：普通 Enter 发送并阻止换行；如果没有这行，回车会既发送又插入换行。
} // 新增代码+DesktopComposerV2：函数段结束，composerKeyIntent 到此结束；如果没有这个边界，用户不容易看出键盘规则范围。

export function selectedComposerModelOption(options: ComposerModelOption[], selectedModelId = ""): ComposerModelOption | null { // 新增代码+ComposerModelToolbar：函数段开始，找出当前模型选项；如果没有这段，空模型和无效模型 fallback 会散落在 JSX。
  return options.find((option) => option.id === selectedModelId) ?? options[0] ?? null; // 新增代码+ComposerModelToolbar：优先返回选中模型，否则返回第一个可用模型；如果没有这行，菜单可能显示空值但实际又提交另一个模型。
} // 新增代码+ComposerModelToolbar：函数段结束，selectedComposerModelOption 到此结束；如果没有这个边界，用户不容易看出模型 fallback 范围。

export function composerModelMenuLabel(options: ComposerModelOption[], selectedModelId = ""): string { // 新增代码+ComposerModelToolbar：函数段开始，计算模型菜单显示文案；如果没有这段，空状态和选中状态无法被单测锁住。
  const selectedModel = selectedComposerModelOption(options, selectedModelId); // 修改代码+ModelFailureState：先拿到选中模型；如果没有这行，失败标记和空状态会混在一条表达式里难以维护。
  return selectedModel === null ? "选择模型" : composerModelOptionLabel(selectedModel); // 修改代码+ModelFailureState：显示模型名并追加最近失败标记；如果没有这行，用户看不到哪个模型刚刚被 ChatGPT OAuth 拒绝。
} // 新增代码+ComposerModelToolbar：函数段结束，composerModelMenuLabel 到此结束；如果没有这个边界，用户不容易看出文案规则范围。

export function composerModelOptionLabel(option: ComposerModelOption): string { // 新增代码+ModelFailureState：函数段开始，计算单个模型在菜单中的可见文案；如果没有这段，select 和测试会各自拼接失败标记。
  return option.recentFailure === null ? option.label : `${option.label}（最近失败）`; // 新增代码+ModelFailureState：有最近失败时追加短标签；如果没有这行，用户仍会反复选择刚失败的模型却不知道原因。
} // 新增代码+ModelFailureState：函数段结束，composerModelOptionLabel 到此结束；如果没有这个边界，用户不容易看出失败标签规则范围。

export function composerModelOptionTitle(option: ComposerModelOption | null): string { // 新增代码+ModelFailureState：函数段开始，计算模型下拉 hover 提示；如果没有这段，最近失败只能看到短标签看不到具体原因。
  if (option === null) { // 新增代码+ModelFailureState：处理没有模型的空状态；如果没有这行，未连接 provider 时 title 会访问空对象。
    return "请先在设置里连接提供商"; // 新增代码+ModelFailureState：返回连接提示；如果没有这行，未连接时用户不知道下一步去哪里。
  } // 新增代码+ModelFailureState：空状态分支结束；如果没有这行，条件块语法不完整。
  if (option.recentFailure !== null && option.recentFailure.message.length > 0) { // 新增代码+ModelFailureState：处理带错误消息的失败模型；如果没有这行，用户看不到后端返回的可读失败原因。
    return `${option.providerName} · ${option.label} · ${option.recentFailure.message}`; // 新增代码+ModelFailureState：把 provider、模型和失败说明放进 title；如果没有这行，最近失败只剩一个模糊标签。
  } // 新增代码+ModelFailureState：失败消息分支结束；如果没有这行，条件块语法不完整。
  return `${option.providerName} · ${option.label}`; // 新增代码+ModelFailureState：正常模型显示 provider 和名称；如果没有这行，title 会空白。
} // 新增代码+ModelFailureState：函数段结束，composerModelOptionTitle 到此结束；如果没有这个边界，用户不容易看出 title 规则范围。

export function composerSubmitOptions(model: ComposerModelOption | null, reasoningEffort: ComposerReasoningEffort, permissionMode: ComposerPermissionMode): ComposerSubmitOptions { // 新增代码+ComposerModelToolbar：函数段开始，构造随 prompt 传给后端的上下文；如果没有这段，提交协议会遗漏模型和权限。
  return { providerId: model?.providerId, modelId: model?.id, reasoningEffort, permissionMode }; // 新增代码+ComposerModelToolbar：把模型来源、模型 id、推理档位和权限模式放进一个对象；如果没有这行，bridge 只能收到 prompt。
} // 新增代码+ComposerModelToolbar：函数段结束，composerSubmitOptions 到此结束；如果没有这个边界，用户不容易看出提交上下文范围。

export async function submitComposerDraft(draft: string, sendBlocked: boolean, onSubmit?: ComposerSubmitHandler, options?: ComposerSubmitOptions): Promise<{ submitted: boolean; nextDraft: string }> { // 修改代码+ComposerModelToolbar：函数段开始，提交草稿并携带模型上下文；如果没有这段，组件无法保证后端接收后再清空输入。
  if (!canSubmitComposerDraft(draft, sendBlocked) || onSubmit === undefined) { // 修改代码+ComposerModelToolbar：拦截不可发送或没有提交回调的情况；如果没有这行，空白或无人接收的 prompt 会被清空。
    return { submitted: false, nextDraft: draft }; // 修改代码+ComposerModelToolbar：保留原草稿；如果没有这行，失败前输入会丢失。
  } // 修改代码+ComposerModelToolbar：不可发送判断结束；如果没有这行，条件块语法不完整。
  await onSubmit(draft, options); // 修改代码+ComposerModelToolbar：等待父组件或后端接收 prompt 和上下文；如果没有这行，异步失败时输入也会被提前清空。
  return { submitted: true, nextDraft: "" }; // 修改代码+ComposerModelToolbar：提交成功后清空草稿；如果没有这行，成功发送后旧内容会残留。
} // 修改代码+ComposerModelToolbar：函数段结束，submitComposerDraft 到此结束；如果没有这个边界，用户不容易看出提交清空规则范围。

export function composerButtonState(draft: string, isRunning: boolean, isSubmitting: boolean, canCancel: boolean): ComposerButtonState { // 新增代码+DesktopComposerV2：函数段开始，计算底部按钮状态；如果没有这段，运行中原因和 disabled 状态会难以测试。
  if (canCancel) { // 新增代码+DesktopComposerV2：运行中且有活动 turn 时优先显示取消；如果没有这行，用户无法从固定位置中断任务。
    return { mode: "cancel", disabled: false, title: "正在运行，点击取消本轮", ariaLabel: "取消本轮，正在运行时不能发送" }; // 新增代码+DesktopComposerV2：返回取消按钮状态和原因；如果没有这行，运行中按钮语义不清晰。
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

export function Composer({ isRunning = false, activeTurnId = null, modelOptions = [], selectedModelId = "", reasoningEffort = "ultra", permissionMode = "full-access", modelCallStatus = null, onCancelActiveTurn, onModelChange, onReasoningEffortChange, onPermissionModeChange, onSubmit }: ComposerProps): JSX.Element { // 修改代码+RealModelLatencyV2：函数段开始，渲染 Codex 风格底部输入、模型工具条和真实调用状态；如果没有这段，用户看不到 prompt、模型、推理、权限和慢调用阶段。
  const [draft, setDraft] = useState(""); // 修改代码+DesktopComposerV2：保存当前输入草稿；如果没有这行，组件无法判断空 prompt 或清空输入。
  const [isSubmitting, setIsSubmitting] = useState(false); // 修改代码+DesktopComposerV2：保存本地提交中状态；如果没有这行，异步发送期间可能重复提交。
  const sendBlocked = isRunning || isSubmitting; // 修改代码+DesktopComposerV2：统一计算发送是否被阻塞；如果没有这行，按钮和提交函数可能判断不一致。
  const canCancel = isRunning && typeof activeTurnId === "string" && activeTurnId.length > 0; // 修改代码+DesktopComposerV2：计算当前是否可以取消；如果没有这行，底部按钮无法安全切换取消模式。
  const activeModel = selectedComposerModelOption(modelOptions, selectedModelId); // 新增代码+ComposerModelToolbar：读取当前模型或第一个可用模型；如果没有这行，提交时无法知道模型来源。
  const activeModelId = activeModel?.id ?? ""; // 新增代码+ComposerModelToolbar：把当前模型转成 select value；如果没有这行，空模型状态会和有效模型混在一起。
  const submitOptions = composerSubmitOptions(activeModel, reasoningEffort, permissionMode); // 新增代码+ComposerModelToolbar：准备随 prompt 提交的上下文；如果没有这行，用户菜单选择不会进入后端。
  const buttonState = composerButtonState(draft, isRunning, isSubmitting, canCancel); // 修改代码+DesktopComposerV2：计算按钮 UI 状态；如果没有这行，title、disabled 和模式会散落在 JSX。

  async function submitDraft(): Promise<void> { // 修改代码+ComposerModelToolbar：函数段开始，提交当前草稿和底部菜单上下文；如果没有这段，按钮和 Enter 键会重复写提交逻辑。
    const currentDraft = draft; // 修改代码+DesktopComposerV2：冻结本次提交的文本；如果没有这行，异步等待期间用户编辑可能影响发送内容。
    if (!canSubmitComposerDraft(currentDraft, sendBlocked)) { // 修改代码+DesktopComposerV2：拦截不可发送状态；如果没有这行，空 prompt 或运行中 prompt 会进入后端。
      return; // 修改代码+DesktopComposerV2：不可发送时直接退出；如果没有这行，后续仍会调用 onSubmit。
    } // 修改代码+DesktopComposerV2：不可发送判断结束；如果没有这行，条件块语法不完整。
    setIsSubmitting(true); // 修改代码+DesktopComposerV2：标记正在提交；如果没有这行，用户可以在等待后端时重复点击。
    try { // 修改代码+DesktopComposerV2：保护异步提交；如果没有这行，失败时无法恢复提交中状态。
      const result = await submitComposerDraft(currentDraft, false, onSubmit, submitOptions); // 修改代码+ComposerModelToolbar：等待提交规则执行并携带模型上下文；如果没有这行，组件不会复用已测试的纯提交逻辑。
      if (result.submitted) { // 修改代码+DesktopComposerV2：只在提交成功后清空；如果没有这行，后端拒绝时输入也会被清掉。
        setDraft(result.nextDraft); // 修改代码+DesktopComposerV2：清空或保留草稿；如果没有这行，成功发送后旧内容会残留。
      } // 修改代码+DesktopComposerV2：成功清空分支结束；如果没有这行，条件块语法不完整。
    } finally { // 修改代码+DesktopComposerV2：无论成功失败都恢复按钮；如果没有这行，异常后按钮可能一直禁用。
      setIsSubmitting(false); // 修改代码+DesktopComposerV2：结束本地提交状态；如果没有这行，发送按钮可能永久显示正在发送。
    } // 修改代码+DesktopComposerV2：提交清理结束；如果没有这行，finally 块语法不完整。
  } // 修改代码+ComposerModelToolbar：函数段结束，submitDraft 到此结束；如果没有这个边界，用户不容易看出提交逻辑范围。

  function cancelActiveTurn(): void { // 修改代码+DesktopComposerV2：函数段开始，处理底部取消按钮；如果没有这段，运行中状态只能禁用发送，用户无法中断任务。
    if (!canCancel || activeTurnId === null) { // 修改代码+DesktopComposerV2：拦截没有活动 turn 的取消请求；如果没有这行，按钮可能会向后端发送空 turn id。
      return; // 修改代码+DesktopComposerV2：不可取消时直接退出；如果没有这行，后续仍可能调用无效回调。
    } // 修改代码+DesktopComposerV2：不可取消判断结束；如果没有这行，条件块语法不完整。
    onCancelActiveTurn?.(activeTurnId); // 修改代码+DesktopComposerV2：把当前 turn id 交给父组件取消；如果没有这行，用户点击取消不会触发后端生命周期。
  } // 修改代码+DesktopComposerV2：函数段结束，cancelActiveTurn 到此结束；如果没有这个边界，用户不容易看出取消逻辑范围。

  return ( // 修改代码+ComposerModelToolbar：返回输入区结构；如果没有这行，组件不会输出 UI。
    <footer className="composer"> {/* 修改代码+ComposerModelToolbar：定义底部 composer 容器；如果没有这行，输入框和工具条没有稳定布局。 */}
      <div className="composer-frame"> {/* 新增代码+ComposerModelToolbar：定义 Codex 式圆角输入框外壳；如果没有这行，底部控件会分散成普通表单。 */}
        <textarea className="composer-input" rows={1} placeholder="要求后续变更" value={draft} onChange={(event) => setDraft(event.currentTarget.value)} onKeyDown={(event) => { const intent = composerKeyIntent(event.key, event.shiftKey); if (intent.shouldPreventDefault) { event.preventDefault(); void submitDraft(); } }} /> {/* 修改代码+ComposerModelToolbar：渲染受控输入框并保留 Shift+Enter 换行；如果没有这行，用户无法稳定输入中文多行 prompt。 */}
        <div className="composer-model-status-slot" aria-live="polite"> {/* 新增代码+RealModelLatencyV2：为模型调用状态预留固定高度；如果没有这行，连接/fallback 文案会挤压工具条或导致按钮跳动。 */}
          <ModelCallStatus status={modelCallStatus} compact={true} /> {/* 新增代码+RealModelLatencyV2：渲染紧凑状态条；如果没有这行，用户只能去右侧时间线猜模型调用卡在哪里。 */}
        </div> {/* 新增代码+RealModelLatencyV2：固定状态槽结束；如果没有这行，JSX 结构不完整。 */}
        <div className="composer-toolbar"> {/* 新增代码+ComposerModelToolbar：定义底部工具条；如果没有这行，权限、模型、推理和语音入口没有容器。 */}
          <div className="composer-toolbar-left"> {/* 新增代码+ComposerModelToolbar：定义左侧工具组；如果没有这行，添加按钮和权限模式无法贴近 Codex 截图位置。 */}
            <button className="icon-button composer-plus-button" type="button" aria-label="添加附件或上下文" title="添加附件或上下文"> {/* 修改代码+ComposerModelToolbar：渲染添加入口；如果没有这行，后续文件/上下文功能没有固定按钮。 */}
              <Plus aria-hidden={true} size={18} /> {/* 修改代码+ComposerModelToolbar：显示加号图标；如果没有这行，按钮含义不如 Codex 截图直观。 */}
            </button> {/* 修改代码+ComposerModelToolbar：添加按钮结束；如果没有这行，JSX 结构不完整。 */}
            <label className="composer-select-shell composer-access-shell" title={COMPOSER_PERMISSION_OPTIONS.find((option) => option.value === permissionMode)?.title ?? ""}> {/* 新增代码+ComposerModelToolbar：渲染权限下拉外壳；如果没有这行，完全访问入口缺少 Codex 式包裹。 */}
              <ShieldCheck aria-hidden={true} size={16} /> {/* 新增代码+ComposerModelToolbar：显示权限图标；如果没有这行，完全访问菜单不够可识别。 */}
              <select data-testid="composer-access-select" aria-label="权限模式" value={permissionMode} onChange={(event) => onPermissionModeChange?.(event.currentTarget.value as ComposerPermissionMode)}> {/* 新增代码+ComposerModelToolbar：渲染权限 select；如果没有这行，用户无法切换完全访问/请求确认/只读。 */}
                {COMPOSER_PERMISSION_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)} {/* 新增代码+ComposerModelToolbar：渲染权限选项；如果没有这行，权限菜单会是空的。 */}
              </select> {/* 新增代码+ComposerModelToolbar：权限 select 结束；如果没有这行，JSX 结构不完整。 */}
              <ChevronDown aria-hidden={true} size={14} /> {/* 新增代码+ComposerModelToolbar：显示下拉箭头；如果没有这行，菜单可展开性不明显。 */}
            </label> {/* 新增代码+ComposerModelToolbar：权限下拉外壳结束；如果没有这行，JSX 结构不完整。 */}
          </div> {/* 新增代码+ComposerModelToolbar：左侧工具组结束；如果没有这行，JSX 结构不完整。 */}
          <div className="composer-toolbar-right"> {/* 新增代码+ComposerModelToolbar：定义右侧工具组；如果没有这行，模型、推理、语音和发送无法靠右排列。 */}
            <label className="composer-select-shell composer-model-shell" title={composerModelOptionTitle(activeModel)}> {/* 修改代码+ModelFailureState：渲染模型下拉外壳并显示失败原因 title；如果没有这行，用户无法在 OAuth 后选择模型或理解失败模型。 */}
              <select data-testid="composer-model-select" aria-label="选择模型" value={activeModelId} disabled={modelOptions.length === 0} onChange={(event) => onModelChange?.(event.currentTarget.value)}> {/* 新增代码+ComposerModelToolbar：渲染模型 select；如果没有这行，provider catalog 模型无法被用户选择。 */}
                {modelOptions.length === 0 ? <option value="">选择模型</option> : modelOptions.map((option) => <option key={`${option.providerId}:${option.id}`} value={option.id}>{composerModelOptionLabel(option)}</option>)} {/* 修改代码+ModelFailureState：渲染模型空态或带最近失败标记的真实模型列表；如果没有这行，未连接、已连接和失败模型状态都不可见。 */}
              </select> {/* 新增代码+ComposerModelToolbar：模型 select 结束；如果没有这行，JSX 结构不完整。 */}
              <ChevronDown aria-hidden={true} size={14} /> {/* 新增代码+ComposerModelToolbar：显示模型菜单箭头；如果没有这行，用户不容易发现可展开。 */}
            </label> {/* 新增代码+ComposerModelToolbar：模型下拉外壳结束；如果没有这行，JSX 结构不完整。 */}
            <label className="composer-select-shell composer-reasoning-shell" title="推理强度"> {/* 新增代码+ComposerModelToolbar：渲染推理下拉外壳；如果没有这行，低/中/高/超高没有固定位置。 */}
              <select data-testid="composer-reasoning-select" aria-label="推理强度" value={reasoningEffort} onChange={(event) => onReasoningEffortChange?.(event.currentTarget.value as ComposerReasoningEffort)}> {/* 新增代码+ComposerModelToolbar：渲染推理 select；如果没有这行，用户无法调整推理档位。 */}
                {COMPOSER_REASONING_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)} {/* 新增代码+ComposerModelToolbar：渲染推理选项；如果没有这行，推理菜单会是空的。 */}
              </select> {/* 新增代码+ComposerModelToolbar：推理 select 结束；如果没有这行，JSX 结构不完整。 */}
              <ChevronDown aria-hidden={true} size={14} /> {/* 新增代码+ComposerModelToolbar：显示推理菜单箭头；如果没有这行，用户不容易发现可展开。 */}
            </label> {/* 新增代码+ComposerModelToolbar：推理下拉外壳结束；如果没有这行，JSX 结构不完整。 */}
            <button className="icon-button composer-mic-button" type="button" aria-label="语音输入" title="语音输入"> {/* 新增代码+ComposerModelToolbar：渲染语音按钮占位；如果没有这行，Codex 截图里的麦克风入口缺失。 */}
              <Mic aria-hidden={true} size={17} /> {/* 新增代码+ComposerModelToolbar：显示麦克风图标；如果没有这行，语音入口含义不直观。 */}
            </button> {/* 新增代码+ComposerModelToolbar：语音按钮结束；如果没有这行，JSX 结构不完整。 */}
            {buttonState.mode === "cancel" ? ( // 修改代码+ComposerModelToolbar：运行中优先渲染取消按钮；如果没有这行，用户无法从固定位置中断任务。
              <button className="send-button cancel-button" type="button" aria-label={buttonState.ariaLabel} title={buttonState.title} onClick={cancelActiveTurn}> {/* 修改代码+DesktopComposerV2：渲染取消按钮和运行中原因；如果没有这行，可见 GUI 验收只能依赖消息卡片里的小按钮。 */}
                <X aria-hidden={true} size={18} /> {/* 修改代码+DesktopComposerV2：显示取消图标；如果没有这行，运行中按钮含义不够直观。 */}
              </button> // 修改代码+DesktopComposerV2：取消按钮结束；如果没有这行，JSX 结构不完整。
            ) : ( // 修改代码+ComposerModelToolbar：普通状态渲染发送按钮；如果没有这行，非运行态没有提交入口。
              <button className="send-button" type="button" aria-label={buttonState.ariaLabel} title={buttonState.title} disabled={buttonState.disabled} onClick={() => { void submitDraft(); }}> {/* 修改代码+DesktopComposerV2：渲染发送按钮并绑定提交；如果没有这行，用户看不到提交入口。 */}
                <ArrowUp aria-hidden={true} size={18} /> {/* 修改代码+DesktopComposerV2：显示发送图标；如果没有这行，按钮不够符合常见聊天工具心智。 */}
              </button> // 修改代码+DesktopComposerV2：发送按钮结束；如果没有这行，JSX 结构不完整。
            )} {/* 修改代码+DesktopComposerV2：按钮状态分支结束；如果没有这行，运行中取消和普通发送无法共享同一个固定位置。 */}
          </div> {/* 新增代码+ComposerModelToolbar：右侧工具组结束；如果没有这行，JSX 结构不完整。 */}
        </div> {/* 新增代码+ComposerModelToolbar：底部工具条结束；如果没有这行，JSX 结构不完整。 */}
      </div> {/* 新增代码+ComposerModelToolbar：composer 外壳结束；如果没有这行，JSX 结构不完整。 */}
    </footer> // 修改代码+ComposerModelToolbar：composer 容器结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+ComposerModelToolbar：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+ComposerModelToolbar：函数段结束，Composer 到此结束；如果没有这个边界，用户不容易看出输入区范围。
