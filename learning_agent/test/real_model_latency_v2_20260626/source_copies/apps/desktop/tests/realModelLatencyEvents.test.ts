import { describe, expect, it } from "vitest"; // 新增代码+RealModelLatencyEventsTest：引入 Vitest 测试工具；如果没有这行，真实模型阶段事件没有自动化验收入口。
import { latestModelCallStatus, modelCallStatusFromEvent } from "../src/components/ModelCallStatus"; // 新增代码+RealModelLatencyEventsTest：导入模型调用状态 helper；如果没有这行，测试无法锁定前端如何解释后端阶段事件。
import { reduceGuiEventToThreadActions } from "../src/state/eventReducer"; // 新增代码+RealModelLatencyEventsTest：导入主线程事件 reducer；如果没有这行，测试无法证明模型阶段事件不会被误报 unsupported。
import type { StatusEvent } from "../src/state/statusStore"; // 新增代码+RealModelLatencyEventsTest：导入状态事件类型；如果没有这行，测试 fixture 字段含义不清楚。

function statusEvent(event_type: string, sequence: number, payload: Record<string, unknown>): StatusEvent { // 新增代码+RealModelLatencyEventsTest：函数段开始，创建最小状态事件 fixture；如果没有这段，每个测试都会重复无关字段。
  return { sequence, event_type, session_id: "session_1", run_id: "run_1", turn_id: "turn_1", payload }; // 新增代码+RealModelLatencyEventsTest：返回带固定归属和可变 payload 的事件；如果没有这行，helper 没有输出。
} // 新增代码+RealModelLatencyEventsTest：函数段结束，statusEvent 到此结束；如果没有这行，函数语法不完整。

describe("real model latency events", () => { // 新增代码+RealModelLatencyEventsTest：测试组开始，覆盖真实模型慢调用的前端事件解释；如果没有这段，慢调用 UI 容易再次退回黑盒等待。
  it("keeps model call events out of unsupported diagnostics", () => { // 新增代码+RealModelLatencyEventsTest：测试模型阶段事件不会变成 unsupported；如果没有这段，右侧会误导用户以为后端发了坏事件。
    const reduction = reduceGuiEventToThreadActions(statusEvent("model_call_status", 7, { phase: "websocket_timeout", message: "WebSocket timeout", model_id: "gpt-5.5" })); // 新增代码+RealModelLatencyEventsTest：把 WebSocket 超时阶段事件交给 reducer；如果没有这行，断言没有真实输入。
    expect(reduction.actions).toEqual([]); // 新增代码+RealModelLatencyEventsTest：确认模型阶段事件不直接改主消息；如果没有这行，状态事件可能误写入对话正文。
    expect(reduction.diagnostics).toEqual([]); // 新增代码+RealModelLatencyEventsTest：确认不会产生 unsupported 诊断；如果没有这行，新增事件会被当成异常噪音。
  }); // 新增代码+RealModelLatencyEventsTest：unsupported 诊断测试结束；如果没有这行，测试块语法不完整。

  it("extracts the newest visible model call phase from status events", () => { // 新增代码+RealModelLatencyEventsTest：测试从事件流取最新阶段；如果没有这段，Composer 和右栏可能显示过期状态。
    const events = [ // 新增代码+RealModelLatencyEventsTest：准备按时间递增的事件流；如果没有这行，latest helper 没有输入集合。
      statusEvent("model_call_started", 1, { phase: "connecting", model_id: "gpt-5.5", provider_id: "openai", elapsed_ms: 0 }), // 新增代码+RealModelLatencyEventsTest：放入连接开始事件；如果没有这行，测试覆盖不到初始状态。
      statusEvent("message_delta", 2, { text_delta: "你" }), // 新增代码+RealModelLatencyEventsTest：放入普通消息增量作为噪音；如果没有这行，helper 可能只在纯模型事件列表里才有效。
      statusEvent("model_call_status", 3, { phase: "https_fallback", message: "falling back", model_id: "gpt-5.5", provider_id: "openai", elapsed_ms: 3200 }), // 新增代码+RealModelLatencyEventsTest：放入 HTTPS fallback 事件；如果没有这行，慢路径状态无法被测到。
    ]; // 新增代码+RealModelLatencyEventsTest：事件流结束；如果没有这行，数组语法不完整。
    const status = latestModelCallStatus(events); // 新增代码+RealModelLatencyEventsTest：提取最新模型状态；如果没有这行，后续断言没有实际对象。
    expect(status?.phase).toBe("https_fallback"); // 新增代码+RealModelLatencyEventsTest：确认最新阶段来自最后一个模型事件；如果没有这行，过期状态问题会漏掉。
    expect(status?.modelId).toBe("gpt-5.5"); // 新增代码+RealModelLatencyEventsTest：确认模型 id 被保留；如果没有这行，底部无法显示用户选中的模型。
  }); // 新增代码+RealModelLatencyEventsTest：最新阶段测试结束；如果没有这行，测试块语法不完整。

  it("turns failed model call events into a compact failure status", () => { // 新增代码+RealModelLatencyEventsTest：测试失败事件文案来源；如果没有这段，模型不可用时用户只会看到泛化等待。
    const status = modelCallStatusFromEvent(statusEvent("model_call_failed", 4, { phase: "failed", error: "当前模型不可用", model_id: "gpt-4.1" })); // 新增代码+RealModelLatencyEventsTest：把失败事件转换为状态；如果没有这行，失败 helper 没有输入。
    expect(status?.phase).toBe("failed"); // 新增代码+RealModelLatencyEventsTest：确认失败阶段被识别；如果没有这行，错误可能被当成普通状态。
    expect(status?.message).toBe("当前模型不可用"); // 新增代码+RealModelLatencyEventsTest：确认错误正文进入状态；如果没有这行，用户看不到真实失败原因。
  }); // 新增代码+RealModelLatencyEventsTest：失败状态测试结束；如果没有这行，测试块语法不完整。

  it("maps cancel requested events to visible cancelling feedback without diagnostics", () => { // 新增代码+RealModelCancellationTest：测试取消请求事件会马上变成可见 cancelling；如果没有这段，500ms 内取消反馈可能再次退化成等轮询。
    const reduction = reduceGuiEventToThreadActions(statusEvent("gui_turn_cancel_requested", 9, { status: "cancelling" })); // 新增代码+RealModelCancellationTest：构造后端取消请求事件；如果没有这一行，reducer 没有真实取消输入样本。
    expect(reduction.actions).toEqual([{ type: "turn_status_changed", turnId: "turn_1", status: "cancelling" }]); // 新增代码+RealModelCancellationTest：确认主消息立即切到 cancelling；如果没有这一行，取消按钮是否有即时反馈没有测试保障。
    expect(reduction.diagnostics).toEqual([]); // 新增代码+RealModelCancellationTest：确认取消请求不是 unsupported 噪声；如果没有这一行，右侧诊断可能误报正常取消事件。
  }); // 新增代码+RealModelCancellationTest：取消请求测试结束；如果没有这一行，测试块语法不完整。
}); // 新增代码+RealModelLatencyEventsTest：测试组结束；如果没有这行，describe 块语法不完整。
