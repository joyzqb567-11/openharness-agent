import { describe, expect, it } from "vitest"; // 新增代码+DesktopThreadStateTest：引入 Vitest 断言工具；如果没有这行，线程 reducer 无法自动验证。
import { threadReducer } from "../src/state/threadStore"; // 新增代码+DesktopThreadStateTest：导入线程 reducer；如果没有这行，测试无法锁定状态机行为。

describe("threadReducer", () => { // 新增代码+DesktopThreadStateTest：测试段开始，覆盖线程消息和 turn 状态；如果没有这段，GUI 状态容易回归。
  it("adds user and assistant messages", () => { // 新增代码+DesktopThreadStateTest：验证消息追加；如果没有这段，消息列表最核心行为没有保障。
    const afterUser = threadReducer(undefined, { // 新增代码+DesktopThreadStateTest：从初始状态追加用户消息；如果没有这行，无法验证默认状态。
      type: "message_added", // 新增代码+DesktopThreadStateTest：声明追加消息动作；如果没有这行，reducer 不知道要执行什么。
      message: { id: "m1", role: "user", text: "你好" }, // 新增代码+DesktopThreadStateTest：提供用户消息；如果没有这行，测试没有实际数据。
    }); // 新增代码+DesktopThreadStateTest：用户消息 reducer 调用结束；如果没有这行，对象语法不完整。

    const afterAssistant = threadReducer(afterUser, { // 新增代码+DesktopThreadStateTest：继续追加助手消息；如果没有这行，无法验证多消息顺序。
      type: "message_added", // 新增代码+DesktopThreadStateTest：声明追加消息动作；如果没有这行，reducer 不会添加消息。
      message: { id: "m2", role: "assistant", text: "你好，我在。", turnId: "turn_a" }, // 新增代码+DesktopThreadStateTest：提供助手消息；如果没有这行，测试无法验证角色和文本。
    }); // 新增代码+DesktopThreadStateTest：助手消息 reducer 调用结束；如果没有这行，对象语法不完整。

    expect(afterAssistant.messages).toHaveLength(2); // 新增代码+DesktopThreadStateTest：确认消息数量；如果没有这行，追加失败可能漏检。
    expect(afterAssistant.messages[0]?.role).toBe("user"); // 新增代码+DesktopThreadStateTest：确认第一条是用户；如果没有这行，消息顺序可能被破坏。
    expect(afterAssistant.messages[1]?.text).toBe("你好，我在。"); // 新增代码+DesktopThreadStateTest：确认助手文本保留；如果没有这行，中文消息可能丢失或乱码。
  }); // 新增代码+DesktopThreadStateTest：消息追加测试结束；如果没有这行，测试块语法不完整。

  it("tracks a running turn and then finishes it", () => { // 新增代码+DesktopThreadStateTest：验证 turn 生命周期状态；如果没有这段，composer 禁用和取消逻辑没有状态基础。
    const withAssistant = threadReducer(undefined, { // 新增代码+DesktopThreadStateTest：先加入助手占位消息；如果没有这行，状态同步没有目标消息。
      type: "message_added", // 新增代码+DesktopThreadStateTest：声明追加消息；如果没有这行，reducer 不会加入占位消息。
      message: { id: "m1", role: "assistant", text: "", turnId: "turn_a", status: "queued" }, // 新增代码+DesktopThreadStateTest：提供关联 turn 的助手消息；如果没有这行，后续状态无法映射。
    }); // 新增代码+DesktopThreadStateTest：占位消息 reducer 调用结束；如果没有这行，对象语法不完整。
    const running = threadReducer(withAssistant, { type: "turn_started", turnId: "turn_a", status: "running" }); // 新增代码+DesktopThreadStateTest：进入运行状态；如果没有这行，无法验证 isRunning。
    const completed = threadReducer(running, { type: "turn_finished", status: "completed" }); // 新增代码+DesktopThreadStateTest：结束 turn；如果没有这行，无法验证终态退出运行。

    expect(running.isRunning).toBe(true); // 新增代码+DesktopThreadStateTest：确认运行中；如果没有这行，运行态错误可能漏检。
    expect(running.activeTurnId).toBe("turn_a"); // 新增代码+DesktopThreadStateTest：确认 active turn；如果没有这行，取消目标可能丢失。
    expect(completed.isRunning).toBe(false); // 新增代码+DesktopThreadStateTest：确认已退出运行；如果没有这行，发送按钮可能一直禁用。
    expect(completed.messages[0]?.status).toBe("completed"); // 新增代码+DesktopThreadStateTest：确认消息状态同步终态；如果没有这行，消息卡片可能停在 queued。
  }); // 新增代码+DesktopThreadStateTest：turn 生命周期测试结束；如果没有这行，测试块语法不完整。

  it("appends streaming deltas to the matching assistant message", () => { // 新增代码+DesktopThreadStreamingTest：验证流式增量追加；如果没有这段，message_delta 可能只被 eventReducer 测到而 state 层回归。
    const baseState = threadReducer(undefined, { type: "message_added", message: { id: "assistant_turn_a", role: "assistant", text: "开头", turnId: "turn_a", status: "running" } }); // 新增代码+DesktopThreadStreamingTest：建立已有助手消息；如果没有这行，测试没有可追加目标。
    const nextState = threadReducer(baseState, { type: "message_delta_received", turnId: "turn_a", textDelta: "继续" }); // 新增代码+DesktopThreadStreamingTest：派发增量动作；如果没有这行，无法验证新增 reducer 分支。
    expect(nextState.messages[0]?.text).toBe("开头继续"); // 新增代码+DesktopThreadStreamingTest：确认增量被追加；如果没有这行，流式文本丢失不会被发现。
    expect(nextState.isRunning).toBe(true); // 新增代码+DesktopThreadStreamingTest：确认收到增量后保持运行态；如果没有这行，composer 可能过早解锁。
  }); // 新增代码+DesktopThreadStreamingTest：流式增量测试结束；如果没有这行，测试块语法不完整。

  it("upserts assistant terminal messages by turn id", () => { // 新增代码+DesktopThreadStreamingTest：验证助手终态消息 upsert；如果没有这段，完成或错误事件可能生成重复消息。
    const baseState = threadReducer(undefined, { type: "message_added", message: { id: "assistant_turn_a", role: "assistant", text: "草稿", turnId: "turn_a", status: "running" } }); // 新增代码+DesktopThreadStreamingTest：建立已有流式草稿；如果没有这行，无法验证覆盖行为。
    const nextState = threadReducer(baseState, { type: "assistant_message_upserted", message: { id: "assistant_turn_a", role: "assistant", text: "最终", turnId: "turn_a", status: "completed", kind: "normal" } }); // 新增代码+DesktopThreadStreamingTest：派发终态 upsert；如果没有这行，无法验证新增动作。
    expect(nextState.messages).toHaveLength(1); // 新增代码+DesktopThreadStreamingTest：确认没有追加重复消息；如果没有这行，重复气泡问题可能漏掉。
    expect(nextState.messages[0]?.text).toBe("最终"); // 新增代码+DesktopThreadStreamingTest：确认最终文本覆盖草稿；如果没有这行，message_completed 可能停留在旧 delta。
    expect(nextState.messages[0]?.status).toBe("completed"); // 新增代码+DesktopThreadStreamingTest：确认消息终态完成；如果没有这行，重试和状态标签可能错误。
  }); // 新增代码+DesktopThreadStreamingTest：助手 upsert 测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopThreadStateTest：测试段结束；如果没有这行，describe 块语法不完整。
