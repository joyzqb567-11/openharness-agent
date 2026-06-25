import { describe, expect, it } from "vitest"; // 新增代码+DesktopStatusStoreTest：引入 Vitest 工具；如果没有这行，状态事件 reducer 无法自动验证。
import { appendStatusEvents, initialStatusState, normalizeStatusEvent } from "../src/state/statusStore"; // 新增代码+DesktopStatusStoreTest：导入状态 store helper；如果没有这行，测试无法锁定事件追加合同。

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
}); // 新增代码+DesktopStatusStoreTest：测试段结束；如果没有这行，describe 语法不完整。
