import { createElement } from "react"; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：导入 React 元素工厂；如果没有这行，测试无法构造 DiagnosticsPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：导入静态渲染工具；如果没有这行，测试无法检查面板最终 HTML 文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面测试运行器识别。
import { DiagnosticsPanel } from "../src/components/DiagnosticsPanel"; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：导入待测诊断面板；如果没有这行，测试没有被测 UI。
import type { StatusEvent } from "../src/state/statusStore"; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：导入状态事件类型；如果没有这行，events fixture 形状不受约束。

const events: StatusEvent[] = [ // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：定义事件游标夹具；如果没有这段，面板标题无法显示最新序号。
  { sequence: 9, event_type: "resume_needs_review", session_id: "session_a", run_id: "run_a", turn_id: "turn_a", payload: {} }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：模拟最近事件；如果没有这行，事件序号断言没有输入。
]; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：事件夹具结束；如果没有这行，数组语法不完整。

const diagnosticsPayload = { // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：定义扩展诊断 payload 夹具；如果没有这段，测试无法覆盖 Trace/Compact/Resume/LSP/REPL。
  ok: true, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：模拟后端成功响应；如果没有这行，状态 helper 输入不完整。
  schema_version: 2, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存协议版本；如果没有这行，Schema 行没有输入。
  backend_online: true, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存后端在线状态；如果没有这行，后端行没有输入。
  status_degraded: false, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存未降级状态；如果没有这行，状态横幅无法走正常分支。
  safe_error: "", // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存空安全错误；如果没有这行，最近错误行可能显示 undefined。
  last_error: "", // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存空最近错误；如果没有这行，最近错误行没有稳定输入。
  release_gate: { status: "passed" }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：模拟最近验收通过；如果没有这行，Release Gate 行无法断言。
  snapshot_summary: { event_count: 3 }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存快照摘要；如果没有这行，Trace 事件数量无法兜底。
  trace_summary: { latest_event_type: "resume_needs_review", latest_event_sequence: 3, event_count: 3, recent_event_types: ["run_started", "compact_completed", "resume_needs_review"] }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 Trace 摘要；如果没有这行，Trace 行没有事实输入。
  compact_status: { state: "compact_completed", latest_boundary_uuid: "boundary_a" }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 Compact 摘要；如果没有这行，Compact 行无法显示边界。
  resume_report_summary: { state: "resume_needs_review", latest_session_id: "session_a", requires_attention: true }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 Resume 摘要；如果没有这行，恢复风险无法显示。
  health_status_summary: { ok: false, warning_count: 2 }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 health_status 摘要；如果没有这行，健康警告无法显示。
  lsp_diagnostics_summary: { available: true, tool_names: ["lsp_symbols", "lsp_definition", "lsp_diagnostics"] }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 LSP 摘要；如果没有这行，代码理解工具行没有输入。
  repl_summary: { available: true, allowed_tool_count: 12, max_calls: 5 }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存 REPL 摘要；如果没有这行，批量编排行没有输入。
  diagnostic_bundle: { copy_text: "{\"redacted\":true}" }, // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：保存可复制诊断包；如果没有这行，复制按钮没有输入。
  raw_secret: "SECRET_DIAGNOSTIC_SHOULD_NOT_RENDER", // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：放入不应渲染的未知字段；如果没有这行，测试无法证明面板不会盲目展开原始 payload。
}; // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：扩展诊断 payload 夹具结束；如果没有这行，常量语法不完整。

describe("DiagnosticsPanel", () => { // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：测试组开始，覆盖诊断页签可见 UI；如果没有这段，诊断面板回归不会被自动发现。
  it("renders Trace, Compact, Resume, LSP, and REPL summaries safely", () => { // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：测试核心工具摘要可见；如果没有这段，GUI 可能只显示旧 health/release gate。
    const markup = renderToStaticMarkup(createElement(DiagnosticsPanel, { events, diagnostics: diagnosticsPayload, health: { schema_version: 2 } })); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：静态渲染诊断面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("诊断"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认面板标题可见；如果没有这行，诊断页可能渲染为空。
    expect(markup).toContain("Trace"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 Trace 行可见；如果没有这行，事件流摘要可能丢失。
    expect(markup).toContain("resume_needs_review"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认最新事件和恢复状态可见；如果没有这行，关键风险状态可能丢失。
    expect(markup).toContain("boundary_a"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 compact 边界可见；如果没有这行，压缩状态可能不可见。
    expect(markup).toContain("session_a"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 resume session 可见；如果没有这行，恢复报告入口可能不可见。
    expect(markup).toContain("需关注"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认恢复风险文案可见；如果没有这行，用户可能忽略需要人工检查的状态。
    expect(markup).toContain("lsp_diagnostics"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 LSP 工具名可见；如果没有这行，代码理解接入状态可能不可见。
    expect(markup).toContain("12 tools"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 REPL 只读工具数量可见；如果没有这行，批量编排规模不可见。
    expect(markup).toContain("5 calls"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 REPL 调用上限可见；如果没有这行，用户不知道批量边界。
    expect(markup).not.toContain("SECRET_DIAGNOSTIC_SHOULD_NOT_RENDER"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认未知敏感字段不会被盲目渲染；如果没有这行，原始 payload 可能泄漏。
  }); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：核心摘要测试结束；如果没有这行，测试块语法不完整。

  it("renders stable fallbacks for missing diagnostic sections", () => { // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：测试缺字段兜底；如果没有这段，后端降级时 UI 可能显示 undefined。
    const markup = renderToStaticMarkup(createElement(DiagnosticsPanel, { events: [], diagnostics: {}, health: {} })); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：静态渲染空 payload；如果没有这行，空态断言没有 HTML 输入。
    expect(markup).toContain("not_run"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 Compact/Resume 缺省状态可见；如果没有这行，空态可能显示空白。
    expect(markup).toContain("no boundary"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 compact 边界缺省文案可见；如果没有这行，用户不知道只是暂无边界。
    expect(markup).toContain("缺失"); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：确认 LSP/REPL 缺失状态可见；如果没有这行，工具目录缺失时不可理解。
  }); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：兜底测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopDiagnosticsToolSurfacePanelTest：测试组结束；如果没有这行，describe 语法不完整。
