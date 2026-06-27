import { createElement } from "react"; // 新增代码+DesktopGUIHarnessControlsPanelTest：导入 React 元素工厂；如果没有这行，测试无法构造 HarnessPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIHarnessControlsPanelTest：导入静态渲染工具；如果没有这行，测试无法检查真实 HTML 文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIHarnessControlsPanelTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面端测试运行器识别。
import { HarnessPanel } from "../src/components/HarnessPanel"; // 新增代码+DesktopGUIHarnessControlsPanelTest：导入待测任务面板；如果没有这行，测试无法约束 Task 页签 UI。

const harnessPayload = { // 新增代码+DesktopGUIHarnessControlsPanelTest：定义 Harness payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  active_goal: { run_id: "goal_gui_v2", prompt: "打造 Codex 风格成熟 GUI agent", status: "running", running_step: "接入真实控制" }, // 新增代码+DesktopGUIHarnessControlsPanelTest：保存当前目标样本；如果没有这行，面板没有可见主任务。
  queue: [{ id: "goal_gui_v2", status: "running", summary: "真实长任务正在执行" }], // 新增代码+DesktopGUIHarnessControlsPanelTest：保存队列样本；如果没有这行，队列区域无法被渲染验证。
  checkpoints: [{ source: "stage", stage_name: "接入真实控制", checkpoint: "已有阶段恢复点" }], // 新增代码+DesktopGUIHarnessControlsPanelTest：保存 checkpoint 样本；如果没有这行，恢复点区域无法被渲染验证。
  last_progress: "已有阶段恢复点", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存最近进展；如果没有这行，目标摘要会缺少进展文本。
  blocked_reason: "", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存空阻塞原因；如果没有这行，payload 形状不完整。
  safe_error: "", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存空安全错误；如果没有这行，payload 形状不完整。
  controls: { pause_supported: true, resume_supported: true, stop_supported: true, checkpoint_supported: true }, // 新增代码+DesktopGUIHarnessControlsPanelTest：声明四个真实控制能力；如果没有这行，按钮不会出现在面板上。
}; // 新增代码+DesktopGUIHarnessControlsPanelTest：Harness payload 夹具结束；如果没有这行，常量定义不完整。

const lastControlResult = { // 新增代码+DesktopGUIHarnessControlsPanelTest：定义最近控制结果夹具；如果没有这段，测试无法证明按钮点击反馈可见。
  ok: true, // 新增代码+DesktopGUIHarnessControlsPanelTest：标记控制请求成功；如果没有这行，结果形状不完整。
  schema_version: 2, // 新增代码+DesktopGUIHarnessControlsPanelTest：保存协议版本；如果没有这行，结果形状不完整。
  action: "checkpoint", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存最近动作；如果没有这行，用户看不到刚执行了什么控制。
  supported: true, // 新增代码+DesktopGUIHarnessControlsPanelTest：保存后端支持状态；如果没有这行，反馈无法区分真实支持和占位。
  status: "checkpointed", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存控制结果状态；如果没有这行，用户看不到 checkpoint 是否写入。
  message: "手动 checkpoint 已写入。", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存可读反馈；如果没有这行，GUI 点击后没有肉眼可见结果。
  safe_error: "", // 新增代码+DesktopGUIHarnessControlsPanelTest：保存空安全错误；如果没有这行，结果形状不完整。
}; // 新增代码+DesktopGUIHarnessControlsPanelTest：最近控制结果夹具结束；如果没有这行，常量定义不完整。

function noop(): void { // 新增代码+DesktopGUIHarnessControlsPanelTest：函数段开始，提供测试用空回调；如果没有这段，按钮 props 需要重复匿名函数。
  return undefined; // 新增代码+DesktopGUIHarnessControlsPanelTest：明确什么也不做；如果没有这行，函数会隐式返回但初学者不易理解。
} // 新增代码+DesktopGUIHarnessControlsPanelTest：函数段结束，noop 到此结束；如果没有这行，函数语法不完整。

describe("HarnessPanel", () => { // 新增代码+DesktopGUIHarnessControlsPanelTest：测试组开始，覆盖 Task 页签可见控制；如果没有这段，按钮回归不会被自动发现。
  it("renders pause resume stop checkpoint controls and latest result", () => { // 新增代码+DesktopGUIHarnessControlsPanelTest：测试四个控制按钮和反馈文本；如果没有这段，GUI 可能只有部分控制。
    const markup = renderToStaticMarkup(createElement(HarnessPanel, { payload: harnessPayload, onPause: noop, onResume: noop, onStop: noop, onCheckpoint: noop, controlPending: false, lastControlResult })); // 新增代码+DesktopGUIHarnessControlsPanelTest：静态渲染任务面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("暂停"); // 新增代码+DesktopGUIHarnessControlsPanelTest：确认暂停按钮可见；如果没有这行，暂停按钮缺失不会被发现。
    expect(markup).toContain("恢复"); // 新增代码+DesktopGUIHarnessControlsPanelTest：确认恢复按钮可见；如果没有这行，恢复按钮缺失不会被发现。
    expect(markup).toContain("停止"); // 新增代码+DesktopGUIHarnessControlsPanelTest：确认停止按钮可见；如果没有这行，急停入口缺失不会被发现。
    expect(markup).toContain("Checkpoint"); // 新增代码+DesktopGUIHarnessControlsPanelTest：确认 checkpoint 按钮可见；如果没有这行，恢复点入口缺失不会被发现。
    expect(markup).toContain("手动 checkpoint 已写入。"); // 新增代码+DesktopGUIHarnessControlsPanelTest：确认最近控制反馈可见；如果没有这行，用户点击后可能没有肉眼反馈。
  }); // 新增代码+DesktopGUIHarnessControlsPanelTest：控制按钮渲染测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIHarnessControlsPanelTest：测试组结束；如果没有这行，describe 语法不完整。
