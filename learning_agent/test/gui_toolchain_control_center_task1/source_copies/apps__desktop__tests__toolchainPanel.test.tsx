import { createElement } from "react"; // 新增代码+DesktopGUIToolchainPanelTest：导入 React 元素工厂；如果没有这行，测试无法在无浏览器环境中构造组件。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIToolchainPanelTest：导入静态渲染工具；如果没有这行，测试无法检查肉眼可见的 HTML 文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIToolchainPanelTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面端测试运行器识别。
import { ToolchainPanel } from "../src/components/ToolchainPanel"; // 新增代码+DesktopGUIToolchainPanelTest：导入待实现的工具链面板；如果没有这行，测试无法先红后绿地约束新 UI。

const toolchainPayload = { // 新增代码+DesktopGUIToolchainPanelTest：定义工具链 payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  ok: true, // 新增代码+DesktopGUIToolchainPanelTest：标记后端响应成功；如果没有这行，面板无法显示成功合同形状。
  schema_version: 2, // 新增代码+DesktopGUIToolchainPanelTest：保存 schema 版本；如果没有这行，面板无法展示协议来源。
  tool_count: 3, // 新增代码+DesktopGUIToolchainPanelTest：保存工具总数；如果没有这行，面板无法显示控制中心规模。
  group_count: 2, // 新增代码+DesktopGUIToolchainPanelTest：保存分组总数；如果没有这行，面板无法显示工具链组织情况。
  groups: [ // 新增代码+DesktopGUIToolchainPanelTest：保存工具分组列表；如果没有这行，面板没有可渲染内容。
    { // 新增代码+DesktopGUIToolchainPanelTest：定义 Computer Use 分组；如果没有这段，测试无法覆盖桌面控制链路。
      id: "computer_use", // 新增代码+DesktopGUIToolchainPanelTest：保存分组 id；如果没有这行，UI 无法稳定标识分组。
      label: "Computer Use", // 新增代码+DesktopGUIToolchainPanelTest：保存分组展示名；如果没有这行，用户只能看到内部 id。
      tool_count: 2, // 新增代码+DesktopGUIToolchainPanelTest：保存分组工具数；如果没有这行，面板无法展示分组规模。
      tools: [ // 新增代码+DesktopGUIToolchainPanelTest：保存 Computer Use 工具列表；如果没有这行，面板无法列出可复用工具。
        { name: "read_last_observation", description: "读取最近一帧桌面观察", source: "builtin", status: "ready", risk_level: "low", permission_mode: "read_only", read_only: true, destructive: false, reuse_module: "learning_agent.tools.catalog" }, // 新增代码+DesktopGUIToolchainPanelTest：定义观察工具；如果没有这行，测试无法证明 Computer Use 真实工具可见。
        { name: "assert_last_action", description: "断言最近动作结果", source: "builtin", status: "available", risk_level: "medium", permission_mode: "on_request", read_only: false, destructive: false, reuse_module: "learning_agent.tools.catalog" }, // 新增代码+DesktopGUIToolchainPanelTest：定义动作断言工具；如果没有这行，测试无法覆盖非只读状态。
      ], // 新增代码+DesktopGUIToolchainPanelTest：Computer Use 工具列表结束；如果没有这行，数组语法不完整。
    }, // 新增代码+DesktopGUIToolchainPanelTest：Computer Use 分组结束；如果没有这行，对象语法不完整。
    { // 新增代码+DesktopGUIToolchainPanelTest：定义 Planning 分组；如果没有这段，测试无法覆盖非桌面工具分组。
      id: "planning", // 新增代码+DesktopGUIToolchainPanelTest：保存 planning 分组 id；如果没有这行，分组身份不稳定。
      label: "Planning", // 新增代码+DesktopGUIToolchainPanelTest：保存 planning 展示名；如果没有这行，UI 缺少可读标题。
      tool_count: 1, // 新增代码+DesktopGUIToolchainPanelTest：保存 planning 工具数；如果没有这行，分组计数不完整。
      tools: [{ name: "update_plan", description: "更新任务计划", source: "builtin", status: "ready", risk_level: "low", permission_mode: "none", read_only: false, destructive: false, reuse_module: "learning_agent.tools.catalog" }], // 新增代码+DesktopGUIToolchainPanelTest：定义计划工具；如果没有这行，测试无法证明计划工具进入面板。
    }, // 新增代码+DesktopGUIToolchainPanelTest：Planning 分组结束；如果没有这行，对象语法不完整。
  ], // 新增代码+DesktopGUIToolchainPanelTest：分组列表结束；如果没有这行，payload 语法不完整。
}; // 新增代码+DesktopGUIToolchainPanelTest：工具链 payload 夹具结束；如果没有这行，常量定义不完整。

describe("ToolchainPanel", () => { // 新增代码+DesktopGUIToolchainPanelTest：测试组开始，覆盖工具链清单可见性；如果没有这段，新面板缺少自动验收。
  it("renders grouped toolchain inventory with reuse source", () => { // 新增代码+DesktopGUIToolchainPanelTest：测试分组、工具名和复用来源；如果没有这段，GUI 可能只显示空壳而不是真实工具链。
    const markup = renderToStaticMarkup(createElement(ToolchainPanel, { payload: toolchainPayload })); // 新增代码+DesktopGUIToolchainPanelTest：静态渲染工具链面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("toolchain-panel"); // 新增代码+DesktopGUIToolchainPanelTest：确认面板根 class 可见；如果没有这行，样式和验收定位可能失效。
    expect(markup).toContain("Computer Use"); // 新增代码+DesktopGUIToolchainPanelTest：确认桌面自动化分组可见；如果没有这行，用户看不到 computer use 链路。
    expect(markup).toContain("read_last_observation"); // 新增代码+DesktopGUIToolchainPanelTest：确认现有工具名可见；如果没有这行，GUI 可能没有真正接入工具清单。
    expect(markup).toContain("learning_agent.tools.catalog"); // 新增代码+DesktopGUIToolchainPanelTest：确认复用模块来源可见；如果没有这行，用户无法判断是否复用原代码。
  }); // 新增代码+DesktopGUIToolchainPanelTest：工具链面板渲染测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIToolchainPanelTest：测试组结束；如果没有这行，describe 语法不完整。
