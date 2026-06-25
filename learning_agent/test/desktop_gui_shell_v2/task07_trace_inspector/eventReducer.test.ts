import { describe, expect, it } from "vitest"; // 新增代码+DesktopEventReducerTest：引入 Vitest 测试工具；如果没有这一行，V2 事件 reducer 没有自动化断言入口。
import { reduceGuiEventToThreadActions, reduceGuiEventToTraceRows } from "../src/state/eventReducer"; // 修改代码+DesktopTraceInspectorTest：导入线程 reducer 和工具 trace reducer；如果没有这一行，工具轨迹测试无法驱动真实实现。
import { initialThreadState, threadReducer } from "../src/state/threadStore"; // 修改代码+DesktopEventReducerTest：导入初始状态和线程 reducer；如果没有这一行，空动作列表无法验证状态保持不变。
import type { StatusEvent } from "../src/state/statusStore"; // 新增代码+DesktopEventReducerTest：复用现有状态事件类型；如果没有这一行，测试事件形状容易和实际轮询数据分裂。

function makeEvent(eventType: string, payload: Record<string, unknown>, turnId = "turn_a", sequence = 1): StatusEvent { // 修改代码+DesktopTraceInspectorTest：helper 段开始，构造可复用状态事件；如果没有这段，每个测试都会重复大量样板字段。
  return { sequence, event_type: eventType, session_id: "session_a", run_id: "run_a", turn_id: turnId, payload }; // 修改代码+DesktopTraceInspectorTest：返回最小合法 StatusEvent；如果没有这一行，eventReducer 输入不稳定。
} // 新增代码+DesktopEventReducerTest：helper 段结束，makeEvent 到此结束；如果没有边界说明，用户不容易看出测试事件来源。

describe("reduceGuiEventToThreadActions", () => { // 新增代码+DesktopEventReducerTest：测试段开始，锁定 V2 event 到 thread action 的转换；如果没有这段，流式消息 UI 容易回退。
  it("appends message_delta text to the active assistant message", () => { // 新增代码+DesktopEventReducerTest：测试流式增量追加；如果没有这段，GUI 可能只显示最终答案不显示 streaming。
    const baseState = threadReducer(undefined, { type: "message_added", message: { id: "assistant_turn_a", role: "assistant", text: "", turnId: "turn_a", status: "running" } }); // 新增代码+DesktopEventReducerTest：先建立助手占位消息；如果没有这一行，delta 没有可追加目标。
    const reduction = reduceGuiEventToThreadActions(makeEvent("message_delta", { text_delta: "第一段" })); // 新增代码+DesktopEventReducerTest：把 V2 message_delta 转成 thread actions；如果没有这一行，测试没有被测转换。
    const nextState = reduction.actions.reduce(threadReducer, baseState); // 新增代码+DesktopEventReducerTest：把转换动作真正应用到线程状态；如果没有这一行，无法验证 UI 状态结果。
    expect(reduction.diagnostics).toEqual([]); // 新增代码+DesktopEventReducerTest：确认正常事件没有诊断噪音；如果没有这一行，未知事件处理可能误伤正常事件。
    expect(nextState.messages[0]?.text).toBe("第一段"); // 新增代码+DesktopEventReducerTest：确认增量文本被追加；如果没有这一行，streaming 文本可能丢失。
  }); // 新增代码+DesktopEventReducerTest：流式增量测试结束；如果没有这一行，测试块语法不完整。

  it("finalizes message_completed text", () => { // 新增代码+DesktopEventReducerTest：测试完成事件写入最终文本；如果没有这段，完成态可能只改状态不改正文。
    const baseState = threadReducer(undefined, { type: "message_added", message: { id: "assistant_turn_a", role: "assistant", text: "草稿", turnId: "turn_a", status: "running" } }); // 新增代码+DesktopEventReducerTest：建立已有流式草稿；如果没有这一行，无法验证 final_text 覆盖。
    const reduction = reduceGuiEventToThreadActions(makeEvent("message_completed", { final_text: "最终答案" })); // 新增代码+DesktopEventReducerTest：转换 message_completed；如果没有这一行，测试没有完成事件输入。
    const nextState = reduction.actions.reduce(threadReducer, baseState); // 新增代码+DesktopEventReducerTest：应用转换动作；如果没有这一行，无法验证 reducer 结果。
    expect(nextState.messages[0]?.text).toBe("最终答案"); // 新增代码+DesktopEventReducerTest：确认最终文本覆盖草稿；如果没有这一行，完成消息可能停在旧 delta。
    expect(nextState.messages[0]?.status).toBe("completed"); // 新增代码+DesktopEventReducerTest：确认消息进入 completed；如果没有这一行，完成态标签可能仍是 running。
  }); // 新增代码+DesktopEventReducerTest：完成事件测试结束；如果没有这一行，测试块语法不完整。

  it("creates an assistant-visible safety refusal message", () => { // 新增代码+DesktopEventReducerTest：测试安全拒绝成为一等助手消息；如果没有这段，拒绝可能只藏在状态栏。
    const reduction = reduceGuiEventToThreadActions(makeEvent("safety_refusal", { text: "我不能帮助执行这个操作。" }, "turn_refusal")); // 新增代码+DesktopEventReducerTest：转换 safety_refusal；如果没有这一行，测试没有拒绝事件输入。
    const nextState = reduction.actions.reduce(threadReducer, initialThreadState); // 修改代码+DesktopEventReducerTest：从显式初始状态应用动作；如果没有这一行，TypeScript 会认为结果可能是 undefined。
    expect(nextState.messages[0]?.role).toBe("assistant"); // 新增代码+DesktopEventReducerTest：确认拒绝以助手消息显示；如果没有这一行，拒绝可能被误当系统消息。
    expect(nextState.messages[0]?.kind).toBe("refusal"); // 新增代码+DesktopEventReducerTest：确认消息带拒绝语义；如果没有这一行，ThreadView 无法显示安全标签。
    expect(nextState.messages[0]?.text).toContain("不能帮助"); // 新增代码+DesktopEventReducerTest：确认拒绝正文可见；如果没有这一行，用户看不到安全原因。
  }); // 新增代码+DesktopEventReducerTest：安全拒绝测试结束；如果没有这一行，测试块语法不完整。

  it("creates a visible error message for turn_failed", () => { // 新增代码+DesktopEventReducerTest：测试失败事件成为线程内错误；如果没有这段，失败可能只在右栏显示。
    const reduction = reduceGuiEventToThreadActions(makeEvent("turn_failed", { error: "adapter failed" }, "turn_failed_a")); // 新增代码+DesktopEventReducerTest：转换 turn_failed；如果没有这一行，测试没有失败事件输入。
    const nextState = reduction.actions.reduce(threadReducer, initialThreadState); // 修改代码+DesktopEventReducerTest：从显式初始状态应用失败动作；如果没有这一行，TypeScript 会认为结果可能是 undefined。
    expect(nextState.messages[0]?.kind).toBe("error"); // 新增代码+DesktopEventReducerTest：确认失败消息带错误语义；如果没有这一行，ThreadView 无法显示错误标签。
    expect(nextState.messages[0]?.status).toBe("failed"); // 新增代码+DesktopEventReducerTest：确认消息状态失败；如果没有这一行，重试入口无法出现。
    expect(nextState.messages[0]?.turnId).toBe("turn_failed_a"); // 新增代码+DesktopEventReducerTest：确认保留 turn id；如果没有这一行，错误消息无法重试。
  }); // 新增代码+DesktopEventReducerTest：失败消息测试结束；如果没有这一行，测试块语法不完整。

  it("ignores unknown events with diagnostics instead of crashing", () => { // 新增代码+DesktopEventReducerTest：测试未知事件防崩溃；如果没有这段，新增后端事件可能打坏前端。
    const reduction = reduceGuiEventToThreadActions(makeEvent("future_event", { value: 1 }, "")); // 新增代码+DesktopEventReducerTest：转换未知事件；如果没有这一行，测试没有未知输入。
    const nextState = reduction.actions.reduce(threadReducer, initialThreadState); // 修改代码+DesktopEventReducerTest：从显式初始状态应用空动作列表；如果没有这一行，空数组 reduce 会返回 undefined。
    expect(reduction.actions).toEqual([]); // 新增代码+DesktopEventReducerTest：确认未知事件不生成线程动作；如果没有这一行，未知事件可能污染消息。
    expect(reduction.diagnostics[0]).toContain("future_event"); // 新增代码+DesktopEventReducerTest：确认诊断记录事件名；如果没有这一行，排查未知事件会困难。
    expect(nextState.messages).toEqual([]); // 新增代码+DesktopEventReducerTest：确认线程状态未被污染；如果没有这一行，未知事件可能生成假消息。
  }); // 新增代码+DesktopEventReducerTest：未知事件测试结束；如果没有这一行，测试块语法不完整。
}); // 新增代码+DesktopEventReducerTest：测试段结束；如果没有这一行，describe 块语法不完整。

describe("reduceGuiEventToTraceRows", () => { // 新增代码+DesktopTraceInspectorTest：测试段开始，锁定工具事件到 trace row 的转换；如果没有这段，TracePanel 没有可靠状态来源。
  it("creates a trace row when a tool starts", () => { // 新增代码+DesktopTraceInspectorTest：测试工具开始事件；如果没有这段，工具调用可能只出现在普通事件列表里。
    const rows = reduceGuiEventToTraceRows([], makeEvent("tool_started", { tool_call_id: "call_1", tool_name: "bash", args: { command: "npm test" } })); // 新增代码+DesktopTraceInspectorTest：把 tool_started 转成 trace row；如果没有这行，测试没有被测转换输入。
    expect(rows).toHaveLength(1); // 新增代码+DesktopTraceInspectorTest：确认创建一条工具轨迹；如果没有这行，工具开始事件可能被忽略。
    expect(rows[0]?.toolName).toBe("bash"); // 新增代码+DesktopTraceInspectorTest：确认工具名进入轨迹；如果没有这行，用户看不到哪个工具启动。
    expect(rows[0]?.status).toBe("running"); // 新增代码+DesktopTraceInspectorTest：确认状态为运行中；如果没有这行，TracePanel 无法显示正在执行。
    expect(rows[0]?.argsPreview).toContain("npm test"); // 新增代码+DesktopTraceInspectorTest：确认参数摘要可见；如果没有这行，诊断时看不到工具做什么。
  }); // 新增代码+DesktopTraceInspectorTest：工具开始测试结束；如果没有这行，测试块语法不完整。

  it("updates a trace row when a tool finishes", () => { // 新增代码+DesktopTraceInspectorTest：测试工具完成事件；如果没有这段，TracePanel 只会留下 running 状态。
    const startedRows = reduceGuiEventToTraceRows([], makeEvent("tool_started", { tool_call_id: "call_2", tool_name: "python", args: { module: "unittest" } }, "turn_a", 1)); // 新增代码+DesktopTraceInspectorTest：先创建运行中轨迹；如果没有这行，完成事件没有可更新目标。
    const finishedRows = reduceGuiEventToTraceRows(startedRows, makeEvent("tool_finished", { tool_call_id: "call_2", tool_name: "python", duration_ms: 42, result_summary: "4 tests passed" }, "turn_a", 2)); // 新增代码+DesktopTraceInspectorTest：用完成事件更新轨迹；如果没有这行，无法验证完成合并。
    expect(finishedRows[0]?.status).toBe("completed"); // 新增代码+DesktopTraceInspectorTest：确认状态变成完成；如果没有这行，工具结束不会更新 UI。
    expect(finishedRows[0]?.durationMs).toBe(42); // 新增代码+DesktopTraceInspectorTest：确认耗时保留；如果没有这行，用户无法判断慢工具。
    expect(finishedRows[0]?.resultSummary).toContain("4 tests passed"); // 新增代码+DesktopTraceInspectorTest：确认结果摘要可见；如果没有这行，工具输出缺少诊断价值。
  }); // 新增代码+DesktopTraceInspectorTest：工具完成测试结束；如果没有这行，测试块语法不完整。

  it("marks failed tools with code and readable message", () => { // 新增代码+DesktopTraceInspectorTest：测试工具失败事件；如果没有这段，失败只会显示泛化状态。
    const rows = reduceGuiEventToTraceRows([], makeEvent("tool_finished", { tool_call_id: "call_3", tool_name: "bash", ok: false, error_code: "ENOENT", error_message: "命令不存在" })); // 新增代码+DesktopTraceInspectorTest：把失败完成事件转成轨迹；如果没有这行，失败场景没有输入。
    expect(rows[0]?.status).toBe("failed"); // 新增代码+DesktopTraceInspectorTest：确认失败状态；如果没有这行，TracePanel 无法突出失败工具。
    expect(rows[0]?.errorCode).toBe("ENOENT"); // 新增代码+DesktopTraceInspectorTest：确认错误码保留；如果没有这行，排查只能看自然语言。
    expect(rows[0]?.resultSummary).toContain("命令不存在"); // 新增代码+DesktopTraceInspectorTest：确认可读错误进入摘要；如果没有这行，用户看不到失败原因。
  }); // 新增代码+DesktopTraceInspectorTest：工具失败测试结束；如果没有这行，测试块语法不完整。

  it("redacts sensitive fields in args preview", () => { // 新增代码+DesktopTraceInspectorTest：测试工具参数脱敏；如果没有这段，token 和本机路径可能出现在 GUI。
    const rows = reduceGuiEventToTraceRows([], makeEvent("tool_started", { tool_call_id: "call_4", tool_name: "mcp", args: { token: "sk-secret123456", path: "C:\\Users\\joyzq\\.ssh\\id_rsa", authorization: "Bearer abc123xyz" } })); // 新增代码+DesktopTraceInspectorTest：构造含敏感字段的工具参数；如果没有这行，脱敏测试没有危险样本。
    expect(rows[0]?.argsPreview).toContain("[redacted]"); // 新增代码+DesktopTraceInspectorTest：确认参数预览有脱敏标记；如果没有这行，脱敏可能没有生效。
    expect(rows[0]?.argsPreview).not.toContain("sk-secret123456"); // 新增代码+DesktopTraceInspectorTest：确认密钥不外泄；如果没有这行，API key 可能显示在 trace panel。
    expect(rows[0]?.argsPreview).not.toContain("C:\\Users\\joyzq"); // 新增代码+DesktopTraceInspectorTest：确认本机路径不外泄；如果没有这行，用户私有路径可能显示在 trace panel。
    expect(rows[0]?.argsPreview).not.toContain("Bearer abc123xyz"); // 新增代码+DesktopTraceInspectorTest：确认 bearer token 不外泄；如果没有这行，登录凭证可能显示在 trace panel。
  }); // 新增代码+DesktopTraceInspectorTest：脱敏测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopTraceInspectorTest：工具轨迹测试段结束；如果没有这行，describe 块语法不完整。
