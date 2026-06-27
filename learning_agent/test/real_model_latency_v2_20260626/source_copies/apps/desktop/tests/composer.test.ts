import { createElement } from "react"; // 新增代码+ComposerModelToolbarTest：在 .ts 测试里创建 React 元素；如果没有这行，测试不能安全渲染 Composer。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+ComposerModelToolbarTest：导入静态渲染工具；如果没有这行，底部模型菜单只能靠肉眼发现回归。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopComposerV2Test：引入 Vitest 测试工具；如果没有这行，Composer 输入规则没有自动化验证入口。
import { canSubmitComposerDraft, Composer, composerButtonState, composerKeyIntent, composerModelMenuLabel, composerModelOptionLabel, composerModelOptionTitle, submitComposerDraft } from "../src/components/Composer"; // 修改代码+ModelFailureStateTest：导入 Composer、模型菜单和失败标记 helper；如果没有这行，测试无法锁定底部模型选择和最近失败提示。

describe("Composer input rules", () => { // 新增代码+DesktopComposerV2Test：测试段开始，覆盖底部输入体验；如果没有这段，中文多行和运行态容易回归。
  it("sends a non-empty prompt when Enter is pressed", async () => { // 新增代码+DesktopComposerV2Test：测试 Enter 发送；如果没有这段，普通回车可能只插入换行不提交。
    const intent = composerKeyIntent("Enter", false); // 新增代码+DesktopComposerV2Test：计算普通 Enter 意图；如果没有这行，测试没有键盘输入事实。
    const sentPrompts: string[] = []; // 新增代码+DesktopComposerV2Test：记录提交到父组件的 prompt；如果没有这行，无法确认提交内容。
    const result = await submitComposerDraft("请分析这个项目", false, (prompt) => { sentPrompts.push(prompt); }); // 新增代码+DesktopComposerV2Test：提交非空中文 prompt；如果没有这行，无法验证发送路径。
    expect(intent.shouldSubmit).toBe(true); // 新增代码+DesktopComposerV2Test：确认 Enter 代表发送；如果没有这行，键盘意图可能错误。
    expect(intent.shouldPreventDefault).toBe(true); // 新增代码+DesktopComposerV2Test：确认 Enter 阻止默认换行；如果没有这行，回车可能发送同时换行。
    expect(sentPrompts).toEqual(["请分析这个项目"]); // 新增代码+DesktopComposerV2Test：确认 prompt 被发送一次；如果没有这行，重复发送或未发送会漏掉。
    expect(result).toEqual({ submitted: true, nextDraft: "" }); // 新增代码+DesktopComposerV2Test：确认成功后清空草稿；如果没有这行，发送后输入残留会漏掉。
  }); // 新增代码+DesktopComposerV2Test：Enter 发送测试结束；如果没有这行，测试块语法不完整。

  it("keeps Shift+Enter as a newline instead of submit", () => { // 新增代码+DesktopComposerV2Test：测试 Shift+Enter 换行；如果没有这段，多行中文输入可能被误发送。
    const intent = composerKeyIntent("Enter", true); // 新增代码+DesktopComposerV2Test：计算 Shift+Enter 意图；如果没有这行，测试没有键盘输入事实。
    expect(intent.shouldSubmit).toBe(false); // 新增代码+DesktopComposerV2Test：确认 Shift+Enter 不发送；如果没有这行，多行编辑回归会漏掉。
    expect(intent.shouldInsertNewline).toBe(true); // 新增代码+DesktopComposerV2Test：确认 Shift+Enter 走换行；如果没有这行，用户无法写多行 prompt。
    expect(intent.shouldPreventDefault).toBe(false); // 新增代码+DesktopComposerV2Test：确认不阻止浏览器默认光标行为；如果没有这行，caret 行为可能不稳定。
  }); // 新增代码+DesktopComposerV2Test：Shift+Enter 测试结束；如果没有这行，测试块语法不完整。

  it("preserves Chinese multiline punctuation and newline exactly", async () => { // 新增代码+DesktopComposerV2Test：测试中文多行原样提交；如果没有这段，中文标点和换行可能被 trim 或替换。
    const prompt = "第一行：请分析项目。\n第二行：保留中文标点，继续。"; // 新增代码+DesktopComposerV2Test：准备带中文标点和换行的 prompt；如果没有这行，测试没有关键输入。
    const sentPrompts: string[] = []; // 新增代码+DesktopComposerV2Test：记录真实发送文本；如果没有这行，无法比较原样保留。
    await submitComposerDraft(prompt, false, async (submittedPrompt) => { sentPrompts.push(submittedPrompt); }); // 新增代码+DesktopComposerV2Test：异步提交多行 prompt；如果没有这行，无法验证 Promise 路径也保留文本。
    expect(sentPrompts[0]).toBe(prompt); // 新增代码+DesktopComposerV2Test：确认提交文本完全相等；如果没有这行，换行或中文标点损坏会漏掉。
  }); // 新增代码+DesktopComposerV2Test：中文多行测试结束；如果没有这行，测试块语法不完整。

  it("does not send empty or whitespace-only prompts", async () => { // 新增代码+DesktopComposerV2Test：测试空白不可发送；如果没有这段，空 prompt 可能进入后端。
    const sentPrompts: string[] = []; // 新增代码+DesktopComposerV2Test：记录误发送内容；如果没有这行，无法确认没有调用提交。
    const result = await submitComposerDraft("  \n\t  ", false, (prompt) => { sentPrompts.push(prompt); }); // 新增代码+DesktopComposerV2Test：尝试提交纯空白；如果没有这行，无法验证空白拦截。
    expect(canSubmitComposerDraft("  \n\t  ", false)).toBe(false); // 新增代码+DesktopComposerV2Test：确认发送条件为 false；如果没有这行，按钮禁用逻辑可能错误。
    expect(sentPrompts).toEqual([]); // 新增代码+DesktopComposerV2Test：确认没有调用提交；如果没有这行，空 prompt 误发送会漏掉。
    expect(result).toEqual({ submitted: false, nextDraft: "  \n\t  " }); // 新增代码+DesktopComposerV2Test：确认失败时保留草稿；如果没有这行，用户输入可能被误清空。
  }); // 新增代码+DesktopComposerV2Test：空白不可发送测试结束；如果没有这行，测试块语法不完整。

  it("disables send while a turn is running and exposes the reason", () => { // 新增代码+DesktopComposerV2Test：测试运行中禁用原因；如果没有这段，用户只能看到按钮灰掉却不知道为什么。
    const buttonState = composerButtonState("继续这个任务", true, false, false); // 新增代码+DesktopComposerV2Test：计算运行中无取消目标的发送按钮状态；如果没有这行，测试没有状态输入。
    expect(canSubmitComposerDraft("继续这个任务", true)).toBe(false); // 新增代码+DesktopComposerV2Test：确认运行中不能发送；如果没有这行，重复提交风险会漏掉。
    expect(buttonState.disabled).toBe(true); // 新增代码+DesktopComposerV2Test：确认按钮禁用；如果没有这行，UI 可能仍允许点击。
    expect(buttonState.title).toContain("正在运行"); // 新增代码+DesktopComposerV2Test：确认 title 给出简短原因；如果没有这行，禁用原因不可见。
    expect(buttonState.ariaLabel).toContain("暂不能发送"); // 新增代码+DesktopComposerV2Test：确认无障碍标签也说明原因；如果没有这行，读屏用户不知道状态。
  }); // 新增代码+DesktopComposerV2Test：运行中禁用测试结束；如果没有这行，测试块语法不完整。

  it("renders the bottom cancel button when a real turn is running", () => { // 新增代码+CodexCliCancelBridgeTest：测试运行中底部按钮必须切成取消按钮；如果没有这段，真实模型调用时用户可能找不到停止入口。
    const buttonState = composerButtonState("继续这个任务", true, false, true); // 新增代码+CodexCliCancelBridgeTest：计算有 active turn 时的按钮状态；如果没有这行，测试没有运行中可取消事实。
    const markup = renderToStaticMarkup(createElement(Composer, { isRunning: true, activeTurnId: "turn_running", onCancelActiveTurn: () => undefined })); // 新增代码+CodexCliCancelBridgeTest：渲染运行中的 Composer；如果没有这行，无法确认真实 HTML 是否有取消按钮。
    expect(buttonState.mode).toBe("cancel"); // 新增代码+CodexCliCancelBridgeTest：确认状态机进入取消模式；如果没有这行，按钮可能仍显示发送。
    expect(buttonState.disabled).toBe(false); // 新增代码+CodexCliCancelBridgeTest：确认取消按钮可点；如果没有这行，用户点击红色 X 可能没有效果。
    expect(markup).toContain("cancel-button"); // 新增代码+CodexCliCancelBridgeTest：确认运行态渲染红色取消按钮类名；如果没有这行，视觉按钮可能缺失。
    expect(markup).toContain("aria-label=\"取消本轮，正在运行时不能发送\""); // 新增代码+CodexCliCancelBridgeTest：确认无障碍标签说明取消语义；如果没有这行，读屏和自动化工具不容易定位停止按钮。
  }); // 新增代码+CodexCliCancelBridgeTest：运行中取消按钮渲染测试结束；如果没有这行，测试块语法不完整。

  it("renders Codex-style bottom controls for access, model, reasoning, voice, and send", () => { // 新增代码+ComposerModelToolbarTest：测试底部工具条必须有 Codex 风格关键入口；如果没有这段，OAuth 连接后用户仍找不到模型选择。
    const markup = renderToStaticMarkup(createElement(Composer, { modelOptions: [{ id: "gpt-4.1", label: "GPT-4.1", providerId: "openai", providerName: "OpenAI", supportsTools: true, supportsVision: true, recentFailure: null }], selectedModelId: "gpt-4.1" })); // 修改代码+ModelFailureStateTest：用 createElement 渲染带 OpenAI 模型的 Composer；如果没有这行，测试不会覆盖带失败字段的真实模型形状。
    expect(markup).toContain("data-testid=\"composer-access-select\""); // 新增代码+ComposerModelToolbarTest：确认权限下拉存在；如果没有这行，完全访问入口缺失不会被发现。
    expect(markup).toContain("data-testid=\"composer-model-select\""); // 新增代码+ComposerModelToolbarTest：确认模型下拉存在；如果没有这行，模型选择入口缺失不会被发现。
    expect(markup).toContain("GPT-4.1"); // 新增代码+ComposerModelToolbarTest：确认可见模型进入菜单；如果没有这行，OAuth 连接后的模型仍不可选。
    expect(markup).toContain("data-testid=\"composer-reasoning-select\""); // 新增代码+ComposerModelToolbarTest：确认推理强度下拉存在；如果没有这行，用户无法像 Codex 一样调整推理档位。
    expect(markup).toContain("aria-label=\"语音输入\""); // 新增代码+ComposerModelToolbarTest：确认语音按钮占位存在；如果没有这行，底部操作区不完整。
  }); // 新增代码+ComposerModelToolbarTest：底部工具条静态渲染测试结束；如果没有这行，测试块语法不完整。

  it("uses the selected model label and falls back to a clear empty state", () => { // 新增代码+ComposerModelToolbarTest：测试模型按钮文案规则；如果没有这段，空模型或选中模型显示可能退化。
    const options = [{ id: "gpt-4.1", label: "GPT-4.1", providerId: "openai", providerName: "OpenAI", supportsTools: true, supportsVision: true, recentFailure: null }]; // 修改代码+ModelFailureStateTest：准备一个无失败 OpenAI 模型选项；如果没有这行，helper 没有输入也无法验证新字段兼容。
    expect(composerModelMenuLabel(options, "gpt-4.1")).toBe("GPT-4.1"); // 新增代码+ComposerModelToolbarTest：确认选中模型显示模型名；如果没有这行，底部可能只显示机器 id。
    expect(composerModelMenuLabel([], "")).toBe("选择模型"); // 新增代码+ComposerModelToolbarTest：确认空状态可读；如果没有这行，未连接 provider 时用户看不懂模型区域。
  }); // 新增代码+ComposerModelToolbarTest：模型文案测试结束；如果没有这行，测试块语法不完整。

  it("marks a recently failed model in the bottom model menu without disabling it", () => { // 新增代码+ModelFailureStateTest：测试最近失败模型的可见提示；如果没有这段，用户会再次选择不支持模型却看不到原因。
    const failedOption = { id: "gpt-4.1", label: "GPT-4.1", providerId: "openai", providerName: "OpenAI", supportsTools: true, supportsVision: true, recentFailure: { errorKind: "model_unsupported", message: "所选模型 GPT-4.1 当前 ChatGPT OAuth 账号不支持", failedAt: 1782480000 } }; // 新增代码+ModelFailureStateTest：准备一个后端记录的失败模型；如果没有这行，测试没有真实失败摘要输入。
    const markup = renderToStaticMarkup(createElement(Composer, { modelOptions: [failedOption], selectedModelId: "gpt-4.1" })); // 新增代码+ModelFailureStateTest：渲染带失败模型的底部栏；如果没有这行，无法确认真实 select 文案是否可见。
    expect(composerModelOptionLabel(failedOption)).toBe("GPT-4.1（最近失败）"); // 新增代码+ModelFailureStateTest：确认单项文案追加失败标记；如果没有这行，菜单选项可能仍显示普通模型名。
    expect(composerModelMenuLabel([failedOption], "gpt-4.1")).toBe("GPT-4.1（最近失败）"); // 新增代码+ModelFailureStateTest：确认选中菜单文案也追加失败标记；如果没有这行，底部收起状态可能看不到失败。
    expect(composerModelOptionTitle(failedOption)).toContain("当前 ChatGPT OAuth 账号不支持"); // 新增代码+ModelFailureStateTest：确认 hover title 带具体原因；如果没有这行，短标签没有解释。
    expect(markup).toContain("GPT-4.1（最近失败）"); // 新增代码+ModelFailureStateTest：确认真实 HTML 里能看到失败标记；如果没有这行，helper 通过但 UI 可能没用上。
    expect(markup).toContain("value=\"gpt-4.1\""); // 新增代码+ModelFailureStateTest：确认失败模型仍然可选；如果没有这行，最近失败可能被误当成禁用或隐藏。
  }); // 新增代码+ModelFailureStateTest：最近失败模型测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopComposerV2Test：测试段结束；如果没有这行，describe 块语法不完整。
