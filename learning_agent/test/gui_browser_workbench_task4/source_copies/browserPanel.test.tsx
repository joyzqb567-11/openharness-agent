import { createElement } from "react"; // 新增代码+DesktopGUIBrowserWorkbenchTest：导入 React 元素工厂；如果没有这行，测试无法构造 BrowserPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIBrowserWorkbenchTest：导入静态 HTML 渲染工具；如果没有这行，测试无法检查肉眼可见文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIBrowserWorkbenchTest：导入 Vitest 测试工具；如果没有这行，本文不会被桌面测试运行器识别。
import { BrowserPanel } from "../src/components/BrowserPanel"; // 新增代码+DesktopGUIBrowserWorkbenchTest：导入被测 Browser 面板；如果没有这行，测试没有 UI 目标。

const browserPayload = { // 新增代码+DesktopGUIBrowserWorkbenchTest：定义 Browser workbench payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  providers: { visible_chromium: { available: true, reason: "ready" }, chrome_extension: { available: false, reason: "未连接扩展" } }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 provider 状态；如果没有这行，轨道 chips 无法被渲染验证。
  extension: { connected: false, pending_command_count: 2 }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟扩展状态；如果没有这行，扩展连接摘要无法被测试覆盖。
  native_host: { connected: true }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 native host 状态；如果没有这行，本地桥接摘要无法被测试覆盖。
  tabs: { tab_count: 2, tabs: [{ title: "OpenHarness Console", url: "https://example.com/app", page_id: "page_1" }] }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 tab 摘要；如果没有这行，标签页列表无法被测试覆盖。
  active_target: { kind: "tab", title: "OpenHarness Console", host: "example.com" }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟活跃目标；如果没有这行，当前页面摘要无法被测试覆盖。
  console: { available: true, latest_message: "console error: boom", entry_count: 3, error_count: 1 }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 Console 摘要；如果没有这行，console 错误文本无法被测试覆盖。
  network: { available: true, latest_message: "network 500 error", entry_count: 4, error_count: 2 }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 Network 摘要；如果没有这行，network 错误文本无法被测试覆盖。
  downloads: { available: true, latest_message: "browser_downloads 最近 1 条记录", entry_count: 1, error_count: 0 }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 Downloads 摘要；如果没有这行，下载记录文本无法被测试覆盖。
  recordings: { recording_count: 1, latest: { recording_id: "rec_a" } }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟录制证据；如果没有这行，回放证据数量无法被测试覆盖。
  replay: { available: true, mode: "dry_run_only", reason: "只生成安全回放计划" }, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟 replay 能力；如果没有这行，dry_run_only 边界无法被测试覆盖。
  status_degraded: false, // 新增代码+DesktopGUIBrowserWorkbenchTest：模拟正常状态；如果没有这行，降级提示分支可能干扰测试。
  safe_error: "", // 新增代码+DesktopGUIBrowserWorkbenchTest：提供空安全错误；如果没有这行，payload 形状不完整。
}; // 新增代码+DesktopGUIBrowserWorkbenchTest：Browser payload 夹具结束；如果没有这行，常量定义不完整。

const lastActionResult = { // 新增代码+DesktopGUIBrowserWorkbenchTest：定义最近动作反馈夹具；如果没有这段，点击反馈区域无法被测试覆盖。
  action: "open", // 新增代码+DesktopGUIBrowserWorkbenchTest：保存最近动作名；如果没有这行，反馈标题没有输入。
  status: "recorded", // 新增代码+DesktopGUIBrowserWorkbenchTest：保存最近动作状态；如果没有这行，反馈状态无法被断言。
  message: "已记录打开 https://example.com 的请求；GUI 不绕过现有 Browser/agent 权限策略直接控制网页。", // 新增代码+DesktopGUIBrowserWorkbenchTest：保存后端反馈文案；如果没有这行，记录打开安全边界无法被断言。
}; // 新增代码+DesktopGUIBrowserWorkbenchTest：最近动作反馈夹具结束；如果没有这行，常量定义不完整。

function noop(): void { // 新增代码+DesktopGUIBrowserWorkbenchTest：函数段开始，提供测试用空回调；如果没有这段，按钮 props 需要重复匿名函数。
  return undefined; // 新增代码+DesktopGUIBrowserWorkbenchTest：明确空回调不做任何事；如果没有这行，初学者不易理解测试只关心渲染。
} // 新增代码+DesktopGUIBrowserWorkbenchTest：函数段结束，noop 到此结束；如果没有这行，函数语法不完整。

describe("BrowserPanel", () => { // 新增代码+DesktopGUIBrowserWorkbenchTest：测试组开始，覆盖 Browser 工作台肉眼可见 UI；如果没有这段，按钮和调试摘要回归不会被自动发现。
  it("renders browser controls, debug summaries, replay, tabs, and latest action result", () => { // 新增代码+DesktopGUIBrowserWorkbenchTest：测试 Browser 工作台完整渲染；如果没有这段，Task 4 前端合同没有单测保护。
    const markup = renderToStaticMarkup(createElement(BrowserPanel, { panel: browserPayload, providerStatus: {}, onRefreshStatus: noop, onOpenUrl: noop, actionPending: false, lastActionResult })); // 新增代码+DesktopGUIBrowserWorkbenchTest：静态渲染 BrowserPanel；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("刷新"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认刷新按钮可见；如果没有这行，刷新入口缺失不会被发现。
    expect(markup).toContain("记录打开"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认记录打开按钮可见；如果没有这行，open 入口缺失不会被发现。
    expect(markup).toContain("Console"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 Console 卡片可见；如果没有这行，console 摘要缺失不会被发现。
    expect(markup).toContain("Network"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 Network 卡片可见；如果没有这行，network 摘要缺失不会被发现。
    expect(markup).toContain("Downloads"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 Downloads 卡片可见；如果没有这行，downloads 摘要缺失不会被发现。
    expect(markup).toContain("Replay"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 Replay 卡片可见；如果没有这行，replay 边界缺失不会被发现。
    expect(markup).toContain("console error: boom"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 console 错误文本可见；如果没有这行，调试线索丢失不会被发现。
    expect(markup).toContain("network 500 error"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 network 错误文本可见；如果没有这行，网络线索丢失不会被发现。
    expect(markup).toContain("browser_downloads 最近 1 条记录"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认下载摘要可见；如果没有这行，下载线索丢失不会被发现。
    expect(markup).toContain("dry_run_only"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认 replay 安全模式可见；如果没有这行，用户可能误解回放会直接操作网页。
    expect(markup).toContain("OpenHarness Console"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认活跃目标或 tab 标题可见；如果没有这行，页面上下文丢失不会被发现。
    expect(markup).toContain("recorded"); // 新增代码+DesktopGUIBrowserWorkbenchTest：确认最近动作状态可见；如果没有这行，按钮点击反馈缺失不会被发现。
  }); // 新增代码+DesktopGUIBrowserWorkbenchTest：完整渲染测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIBrowserWorkbenchTest：BrowserPanel 测试组结束；如果没有这行，describe 语法不完整。
