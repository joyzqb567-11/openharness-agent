import { createElement } from "react"; // 新增代码+DesktopGUIComputerUseWorkbenchTest：导入 React 元素工厂；如果没有这行，测试无法构造 ComputerUsePanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIComputerUseWorkbenchTest：导入静态 HTML 渲染工具；如果没有这行，测试无法检查肉眼可见文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIComputerUseWorkbenchTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面测试运行器识别。
import { ComputerUsePanel } from "../src/components/ComputerUsePanel"; // 新增代码+DesktopGUIComputerUseWorkbenchTest：导入被测 Computer Use 面板；如果没有这行，测试没有 UI 目标。

const computerUsePayload = { // 新增代码+DesktopGUIComputerUseWorkbenchTest：定义 Computer Use workbench payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  mode: "observe", // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟只读观察模式；如果没有这行，模式标签无法被测试覆盖。
  permission_mode: "manual", // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟手动权限模式；如果没有这行，权限行无法被测试覆盖。
  allowed_action_classes: ["observe_screen", "list_windows"], // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟允许动作列表；如果没有这行，动作 chip 区无法被测试覆盖。
  target_app_state: { selected_display: "Display 1", last_screenshot: { width: 1920, height: 1080 }, allowed_app_count: 1, hidden_window_count: 0 }, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟目标应用状态；如果没有这行，目标状态区无法被测试覆盖。
  last_observation: { event_type: "computer_use_observe", tool_name: "observe", message: "窗口已观察" }, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟最近观察摘要；如果没有这行，观察证据区无法被测试覆盖。
  last_action_result: { event_type: "gui_computer_use_action", action: "observe", message: "动作成功", low_level_event_count: 0 }, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟后端最近动作；如果没有这行，动作证据区无法被测试覆盖。
  abort_available: true, // 新增代码+DesktopGUIComputerUseWorkbenchTest：声明中止可用；如果没有这行，中止按钮可能被禁用且测试覆盖不足。
  lock: { locked: false, safe_state: "unlocked" }, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟未锁定状态；如果没有这行，锁状态行无法被测试覆盖。
  abort: { requested: false, terminal_abort_fallback: true }, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟急停未触发且终端兜底可用；如果没有这行，急停状态行无法被测试覆盖。
}; // 新增代码+DesktopGUIComputerUseWorkbenchTest：workbench payload 夹具结束；如果没有这行，常量定义不完整。

const permissionsPayload = { // 新增代码+DesktopGUIComputerUseWorkbenchTest：定义权限摘要夹具；如果没有这段，权限行待处理数量没有输入。
  pending_count: 0, // 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟没有待处理权限；如果没有这行，权限行会缺少稳定数字。
}; // 新增代码+DesktopGUIComputerUseWorkbenchTest：权限夹具结束；如果没有这行，常量定义不完整。

const lastActionResult = { // 新增代码+DesktopGUIComputerUseWorkbenchTest：定义最近按钮结果夹具；如果没有这段，点击反馈块无法被测试覆盖。
  action: "observe", // 新增代码+DesktopGUIComputerUseWorkbenchTest：保存最近按钮动作；如果没有这行，反馈块标题没有输入。
  message: "动作成功", // 新增代码+DesktopGUIComputerUseWorkbenchTest：保存按钮结果文案；如果没有这行，反馈块没有可见说明。
  low_level_event_count: 0, // 新增代码+DesktopGUIComputerUseWorkbenchTest：保存低层事件数；如果没有这行，安全验收数字无法显示。
}; // 新增代码+DesktopGUIComputerUseWorkbenchTest：最近按钮结果夹具结束；如果没有这行，常量定义不完整。

function noop(): void { // 新增代码+DesktopGUIComputerUseWorkbenchTest：函数段开始，提供测试用空回调；如果没有这段，按钮 props 需要重复匿名函数。
  return undefined; // 新增代码+DesktopGUIComputerUseWorkbenchTest：明确空回调不做任何事；如果没有这行，初学者不易理解测试只关心渲染。
} // 新增代码+DesktopGUIComputerUseWorkbenchTest：函数段结束，noop 到此结束；如果没有这行，函数语法不完整。

describe("ComputerUsePanel", () => { // 新增代码+DesktopGUIComputerUseWorkbenchTest：测试组开始，覆盖 Computer Use 工作台肉眼可见 UI；如果没有这段，按钮和证据回归不会被自动发现。
  it("renders request observe abort controls, target state, and latest evidence", () => { // 新增代码+DesktopGUIComputerUseWorkbenchTest：测试按钮、目标状态和证据文本；如果没有这段，工作台可能只剩旧锁/急停摘要。
    const markup = renderToStaticMarkup(createElement(ComputerUsePanel, { panel: computerUsePayload, permissions: permissionsPayload, onRequestAccess: noop, onObserve: noop, onAbort: noop, actionPending: false, lastActionResult })); // 新增代码+DesktopGUIComputerUseWorkbenchTest：静态渲染 ComputerUsePanel；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("申请权限"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认申请权限按钮可见；如果没有这行，授权入口缺失不会被发现。
    expect(markup).toContain("观察"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认观察按钮和观察证据可见；如果没有这行，只读刷新入口缺失不会被发现。
    expect(markup).toContain("中止"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认中止按钮可见；如果没有这行，急停入口缺失不会被发现。
    expect(markup).toContain("目标状态"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认目标状态块可见；如果没有这行，桌面上下文可能仍不可见。
    expect(markup).toContain("Display 1"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认显示器摘要可见；如果没有这行，多屏状态可能丢失。
    expect(markup).toContain("1920×1080"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认截图尺寸可见；如果没有这行，观察证据缺少尺度。
    expect(markup).toContain("observe_screen"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认允许动作 chip 可见；如果没有这行，模式能力范围可能丢失。
    expect(markup).toContain("窗口已观察"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认最近观察摘要可见；如果没有这行，观察按钮结果可能不可见。
    expect(markup).toContain("动作成功"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认最近动作和按钮反馈可见；如果没有这行，点击反馈可能丢失。
    expect(markup).toContain("低层事件：0"); // 新增代码+DesktopGUIComputerUseWorkbenchTest：确认低层事件数可见；如果没有这行，安全验收无法肉眼确认只读行为。
  }); // 新增代码+DesktopGUIComputerUseWorkbenchTest：渲染测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIComputerUseWorkbenchTest：测试组结束；如果没有这行，describe 语法不完整。
