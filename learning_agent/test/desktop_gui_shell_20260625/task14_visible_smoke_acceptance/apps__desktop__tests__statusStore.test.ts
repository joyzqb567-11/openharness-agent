import { describe, expect, it } from "vitest"; // 新增代码+DesktopStatusStoreTest：引入 Vitest 工具；如果没有这行，状态事件 reducer 无法自动验证。
import { appendStatusEvents, initialStatusState, latestPermissionEvent, messageTextFromStatusEvent, normalizeStatusEvent } from "../src/state/statusStore"; // 修改代码+DesktopFailedEventTextTest：导入状态 store、权限事件 helper 和消息正文提取工具；如果没有这行，失败事件文本回归无法被测试发现。

describe("statusStore", () => { // 新增代码+DesktopStatusStoreTest：测试段开始，覆盖事件规范化和追加；如果没有这段，轮询状态容易回归。
  it("normalizes raw bridge events", () => { // 新增代码+DesktopStatusStoreTest：验证原始事件清洗；如果没有这段，组件可能直接吃坏数据。
    const event = normalizeStatusEvent({ sequence: "2", event_type: "gui_turn_started", payload: { summary: "running" } }); // 新增代码+DesktopStatusStoreTest：规范化一个最小事件；如果没有这行，无法验证默认字段。
    expect(event.sequence).toBe(2); // 新增代码+DesktopStatusStoreTest：确认序号转数字；如果没有这行，轮询游标可能是字符串。
    expect(event.payload.summary).toBe("running"); // 新增代码+DesktopStatusStoreTest：确认 payload 保留；如果没有这行，工具摘要可能丢失。
  }); // 新增代码+DesktopStatusStoreTest：规范化测试结束；如果没有这行，测试块语法不完整。

  it("appends, sorts, and deduplicates events", () => { // 新增代码+DesktopStatusStoreTest：验证追加排序和去重；如果没有这段，时间线可能重复或乱序。
    const state = appendStatusEvents(initialStatusState, [ // 新增代码+DesktopStatusStoreTest：追加第一批事件；如果没有这行，测试没有输入状态。
      { sequence: 2, event_type: "b", session_id: "", run_id: "", turn_id: "", payload: {} }, // 新增代码+DesktopStatusStoreTest：提供序号 2 事件；如果没有这行，无法验证排序。
      { sequence: 1, event_type: "a", session_id: "", run_id: "", turn_id: "", payload: {} }, // 新增代码+DesktopStatusStoreTest：提供序号 1 事件；如果没有这行，无法验证排序。
    ]); // 新增代码+DesktopStatusStoreTest：第一批追加结束；如果没有这行，数组语法不完整。
    const next = appendStatusEvents(state, [{ sequence: 2, event_type: "b2", session_id: "", run_id: "", turn_id: "", payload: {} }]); // 新增代码+DesktopStatusStoreTest：追加重复序号事件；如果没有这行，无法验证去重覆盖。
    expect(next.events.map((event) => event.event_type)).toEqual(["a", "b2"]); // 新增代码+DesktopStatusStoreTest：确认排序和去重结果；如果没有这行，重复显示可能漏检。
    expect(next.lastSequence).toBe(2); // 新增代码+DesktopStatusStoreTest：确认最新游标；如果没有这行，轮询位置错误可能漏检。
  }); // 新增代码+DesktopStatusStoreTest：追加测试结束；如果没有这行，测试块语法不完整。

  it("finds the latest permission event", () => { // 新增代码+DesktopGUIPermissionsTest：验证最新权限事件选择；如果没有这段，权限弹窗可能显示旧请求。
    const event = latestPermissionEvent([ // 新增代码+DesktopGUIPermissionsTest：调用权限事件 helper；如果没有这行，测试没有被测行为。
      { sequence: 1, event_type: "gui_turn_started", session_id: "", run_id: "", turn_id: "", payload: {} }, // 新增代码+DesktopGUIPermissionsTest：提供普通生命周期事件；如果没有这行，无法证明普通事件会被跳过。
      { sequence: 2, event_type: "permission_required", session_id: "", run_id: "", turn_id: "turn_a", payload: { request_id: "perm_a" } }, // 新增代码+DesktopGUIPermissionsTest：提供旧权限请求；如果没有这行，无法验证后续事件覆盖。
      { sequence: 3, event_type: "gui_turn_needs_permission", session_id: "", run_id: "", turn_id: "turn_b", payload: { request_id: "perm_b" } }, // 新增代码+DesktopGUIPermissionsTest：提供最新 GUI 权限等待事件；如果没有这行，无法验证 bridge 转换事件可触发弹窗。
    ]); // 新增代码+DesktopGUIPermissionsTest：事件数组结束；如果没有这行，函数调用语法不完整。
    expect(event?.payload.request_id).toBe("perm_b"); // 新增代码+DesktopGUIPermissionsTest：确认返回最新权限事件；如果没有这行，弹窗可能停留在旧请求。
  }); // 新增代码+DesktopGUIPermissionsTest：权限事件测试结束；如果没有这行，测试块语法不完整。

  it("uses non-empty error text when failed events carry an empty answer", () => { // 新增代码+DesktopFailedEventTextTest：验证失败事件正文选择；如果没有这段，空 answer 可能再次挡住 error。
    const text = messageTextFromStatusEvent({ // 新增代码+DesktopFailedEventTextTest：调用正文提取工具；如果没有这行，测试没有被测行为。
      sequence: 9, // 新增代码+DesktopFailedEventTextTest：提供事件序号；如果没有这行，事件对象不符合 StatusEvent 合同。
      event_type: "gui_turn_failed", // 新增代码+DesktopFailedEventTextTest：提供失败事件类型；如果没有这行，测试语义不清楚。
      session_id: "default", // 新增代码+DesktopFailedEventTextTest：提供会话 id；如果没有这行，事件对象不符合 StatusEvent 合同。
      run_id: "run_a", // 新增代码+DesktopFailedEventTextTest：提供运行 id；如果没有这行，事件对象不符合 StatusEvent 合同。
      turn_id: "turn_a", // 新增代码+DesktopFailedEventTextTest：提供 turn id；如果没有这行，事件对象不符合 StatusEvent 合同。
      payload: { answer: "", error: "GUI turn 运行失败：测试触发的 GUI turn 失败。" }, // 新增代码+DesktopFailedEventTextTest：模拟真实 bridge 失败 payload；如果没有这行，无法复现空 answer 挡住 error 的问题。
    }); // 新增代码+DesktopFailedEventTextTest：正文提取调用结束；如果没有这行，对象语法不完整。
    expect(text).toBe("GUI turn 运行失败：测试触发的 GUI turn 失败。"); // 新增代码+DesktopFailedEventTextTest：确认显示 error；如果没有这行，失败态正文回归不会被发现。
  }); // 新增代码+DesktopFailedEventTextTest：失败事件正文测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopStatusStoreTest：测试段结束；如果没有这行，describe 语法不完整。
