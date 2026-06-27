import { createElement } from "react"; // 新增代码+DesktopGUIMcpPanelTest：导入 React 元素工厂；如果没有这行，测试无法在无浏览器环境构造 McpPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIMcpPanelTest：导入静态 HTML 渲染工具；如果没有这行，测试无法检查肉眼可见文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIMcpPanelTest：导入 Vitest 测试 API；如果没有这行，测试块和断言无法运行。
import { McpPanel } from "../src/components/McpPanel"; // 新增代码+DesktopGUIMcpPanelTest：导入被测 MCP 面板；如果没有这行，测试没有目标组件。

describe("McpPanel", () => { // 新增代码+DesktopGUIMcpPanelTest：测试套件开始，覆盖 MCP 管理面板；如果没有这段，MCP 页签可见性没有自动化保护。
  it("renders MCP servers, resources, prompts, and hides unknown secret fields", () => { // 新增代码+DesktopGUIMcpPanelTest：测试方法开始，验证可见信息和脱敏边界；如果没有这段，面板可能显示不出核心状态或误渲染 secret。
    const mcpPayload = { // 新增代码+DesktopGUIMcpPanelTest：构造 MCP 管理 payload；如果没有这行，组件没有输入数据。
      ok: true, // 新增代码+DesktopGUIMcpPanelTest：模拟成功响应；如果没有这行，payload 形状不完整。
      schema_version: 2, // 新增代码+DesktopGUIMcpPanelTest：模拟 schema 版本；如果没有这行，schema 文本无法断言。
      server_count: 2, // 新增代码+DesktopGUIMcpPanelTest：模拟 server 数量；如果没有这行，标题统计无法断言。
      resource_count: 1, // 新增代码+DesktopGUIMcpPanelTest：模拟 resource 数量；如果没有这行，资源统计无法断言。
      prompt_count: 1, // 新增代码+DesktopGUIMcpPanelTest：模拟 prompt 数量；如果没有这行，prompt 统计无法断言。
      status_degraded: true, // 新增代码+DesktopGUIMcpPanelTest：模拟降级状态；如果没有这行，警告渲染无法覆盖。
      safe_error: "remote connection failed", // 新增代码+DesktopGUIMcpPanelTest：模拟脱敏错误；如果没有这行，警告文本无法断言。
      servers: [ // 新增代码+DesktopGUIMcpPanelTest：模拟 server 列表；如果没有这行，server 卡片无法渲染。
        { name: "alpha", transport: "stdio", status: "available", resource_count: 1, prompt_count: 1, last_error: "", stream_state: { connected: true }, config_summary: { connection: { command: "python" } }, raw_secret: "SECRET_TOKEN_SHOULD_NOT_RENDER" }, // 新增代码+DesktopGUIMcpPanelTest：模拟可用 server 并放入未知 secret 字段；如果没有这行，无法验证白名单渲染。
        { name: "remote", transport: "http", status: "failed", resource_count: 0, prompt_count: 0, last_error: "connection_failed", stream_state: { status: "failed" }, config_summary: { connection: { origin: "https://example.com" } } }, // 新增代码+DesktopGUIMcpPanelTest：模拟失败 server；如果没有这行，失败状态和错误文案无法断言。
      ], // 新增代码+DesktopGUIMcpPanelTest：server 列表结束；如果没有这行，payload 语法不完整。
      resources: [{ server: "alpha", name: "Repo Docs", uri: "file://repo" }], // 新增代码+DesktopGUIMcpPanelTest：模拟 resource 列表；如果没有这行，资源集合无法断言。
      prompts: [{ server: "alpha", name: "Review", argument_count: 1 }], // 新增代码+DesktopGUIMcpPanelTest：模拟 prompt 列表；如果没有这行，prompt 集合无法断言。
    }; // 新增代码+DesktopGUIMcpPanelTest：MCP payload 结束；如果没有这行，测试数据语法不完整。
    const markup = renderToStaticMarkup(createElement(McpPanel, { payload: mcpPayload })); // 新增代码+DesktopGUIMcpPanelTest：静态渲染 MCP 面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("MCP"); // 新增代码+DesktopGUIMcpPanelTest：确认面板标题可见；如果没有这行，页签主体可能渲染错组件。
    expect(markup).toContain("2 servers"); // 新增代码+DesktopGUIMcpPanelTest：确认 server 数量可见；如果没有这行，统计栏可能丢失。
    expect(markup).toContain("Repo Docs"); // 新增代码+DesktopGUIMcpPanelTest：确认 resource 名称可见；如果没有这行，资源集合可能未渲染。
    expect(markup).toContain("Review"); // 新增代码+DesktopGUIMcpPanelTest：确认 prompt 名称可见；如果没有这行，提示词集合可能未渲染。
    expect(markup).toContain("connection_failed"); // 新增代码+DesktopGUIMcpPanelTest：确认失败错误可见；如果没有这行，用户看不到 server 失败原因。
    expect(markup).not.toContain("SECRET_TOKEN_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUIMcpPanelTest：确认未知 secret 字段不会渲染；如果没有这行，白名单渲染回归无法发现。
  }); // 新增代码+DesktopGUIMcpPanelTest：测试方法结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIMcpPanelTest：测试套件结束；如果没有这行，describe 语法不完整。
