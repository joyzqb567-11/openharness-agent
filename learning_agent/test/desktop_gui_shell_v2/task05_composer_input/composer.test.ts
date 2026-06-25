import { describe, expect, it } from "vitest"; // 新增代码+DesktopComposerV2Test：引入 Vitest 测试工具；如果没有这行，Composer 输入规则没有自动化验证入口。
import { canSubmitComposerDraft, composerButtonState, composerKeyIntent, submitComposerDraft } from "../src/components/Composer"; // 新增代码+DesktopComposerV2Test：导入 Composer 纯规则；如果没有这行，测试无法锁定发送和键盘行为。

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
}); // 新增代码+DesktopComposerV2Test：测试段结束；如果没有这行，describe 块语法不完整。
