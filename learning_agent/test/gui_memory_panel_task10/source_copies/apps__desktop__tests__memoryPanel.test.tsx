import { createElement } from "react"; // 新增代码+DesktopGUIMemoryPanelTest：导入 React 元素工厂；如果没有这行，测试无法在无浏览器环境构造 MemoryPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIMemoryPanelTest：导入静态 HTML 渲染工具；如果没有这行，测试无法检查肉眼可见文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIMemoryPanelTest：导入 Vitest 测试 API；如果没有这行，测试块和断言无法运行。
import { MemoryPanel } from "../src/components/MemoryPanel"; // 新增代码+DesktopGUIMemoryPanelTest：导入被测记忆面板；如果没有这行，测试没有目标组件。

describe("MemoryPanel", () => { // 新增代码+DesktopGUIMemoryPanelTest：测试套件开始，覆盖记忆与预算面板；如果没有这段，记忆页签可见性没有自动化保护。
  it("renders memory, prompt, token, notebook status, and hides unknown secret fields", () => { // 新增代码+DesktopGUIMemoryPanelTest：测试方法开始，验证核心可见信息和字段白名单；如果没有这段，面板可能漏显示或误渲染 secret。
    const memoryPayload = { // 新增代码+DesktopGUIMemoryPanelTest：构造组合 payload；如果没有这行，组件没有输入数据。
      memory: { // 新增代码+DesktopGUIMemoryPanelTest：构造 memory 子 payload；如果没有这行，Context/Progress/Bugs 无法断言。
        ok: true, // 新增代码+DesktopGUIMemoryPanelTest：模拟成功响应；如果没有这行，payload 形状不完整。
        status_degraded: false, // 新增代码+DesktopGUIMemoryPanelTest：模拟正常读取状态；如果没有这行，降级分支默认不清楚。
        context_summary: { status: "ready" }, // 新增代码+DesktopGUIMemoryPanelTest：模拟 Context 快捷状态；如果没有这行，摘要栏无法断言。
        progress_summary: { status: "ready" }, // 新增代码+DesktopGUIMemoryPanelTest：模拟 Progress 快捷状态；如果没有这行，摘要栏无法断言。
        bugs_summary: { status: "ready" }, // 新增代码+DesktopGUIMemoryPanelTest：模拟 Bugs 快捷状态；如果没有这行，摘要栏无法断言。
        files: [{ id: "context", label: "Context", relative_path: "agent_memory/context.md", status: "ready", line_count: 3, size_bytes: 120, preview_lines: ["当前目标：接入 GUI 记忆面板"], headings: ["项目上下文"], raw_secret: "SECRET_MEMORY_SHOULD_NOT_RENDER" }, { id: "progress", label: "Progress", relative_path: "agent_memory/progress.md", status: "ready", line_count: 5, size_bytes: 180, preview_lines: ["Task 10 in progress"], headings: ["当前任务"] }, { id: "bugs", label: "Bugs", relative_path: "agent_memory/bugs.md", status: "ready", line_count: 2, size_bytes: 80, preview_lines: ["暂无阻塞 bug"], headings: ["风险"] }], // 新增代码+DesktopGUIMemoryPanelTest：模拟记忆文件并放入未知 secret 字段；如果没有这行，无法验证文件渲染和白名单。
      }, // 新增代码+DesktopGUIMemoryPanelTest：memory 子 payload 结束；如果没有这行，测试数据语法不完整。
      prompt: { // 新增代码+DesktopGUIMemoryPanelTest：构造 prompt 子 payload；如果没有这行，prompt/token 区无法断言。
        ok: true, // 新增代码+DesktopGUIMemoryPanelTest：模拟成功响应；如果没有这行，payload 形状不完整。
        available_tool_count: 2, // 新增代码+DesktopGUIMemoryPanelTest：模拟可用工具数；如果没有这行，标题统计无法断言。
        tool_count: 2, // 新增代码+DesktopGUIMemoryPanelTest：模拟工具总数；如果没有这行，标题统计无法断言。
        context_budget: { max_messages: 18, max_chars: 24000, source: "OPENHARNESS_GUI_CONTEXT_*" }, // 新增代码+DesktopGUIMemoryPanelTest：模拟上下文预算；如果没有这行，预算区无法断言。
        snapshot_summary: { status: "ready", compact: { status: "idle" }, resume: { status: "ready" } }, // 新增代码+DesktopGUIMemoryPanelTest：模拟 compact/resume 摘要；如果没有这行，快照区无法断言。
        tools: [{ name: "prompt_surface_report", status: "ready", available: true, read_only: true }, { name: "token_budget_report", status: "ready", available: true, read_only: true }], // 新增代码+DesktopGUIMemoryPanelTest：模拟 prompt/token 工具；如果没有这行，工具区无法断言。
      }, // 新增代码+DesktopGUIMemoryPanelTest：prompt 子 payload 结束；如果没有这行，测试数据语法不完整。
      notebook: { // 新增代码+DesktopGUIMemoryPanelTest：构造 notebook 子 payload；如果没有这行，notebook 区无法断言。
        ok: true, // 新增代码+DesktopGUIMemoryPanelTest：模拟成功响应；如果没有这行，payload 形状不完整。
        read_only_first_pass: true, // 新增代码+DesktopGUIMemoryPanelTest：模拟只读优先策略；如果没有这行，策略卡片无法断言。
        edit_exposed_in_gui: false, // 新增代码+DesktopGUIMemoryPanelTest：模拟编辑入口关闭；如果没有这行，风险边界无法断言。
        notebook_count: 1, // 新增代码+DesktopGUIMemoryPanelTest：模拟 notebook 数量；如果没有这行，摘要栏无法断言。
        notebooks: ["research/demo.ipynb"], // 新增代码+DesktopGUIMemoryPanelTest：模拟 notebook 路径；如果没有这行，路径展示无法断言。
        tools: [{ name: "notebook_read", status: "ready", available: true, read_only: true }, { name: "notebook_edit", status: "deferred", available: true, read_only: false }], // 新增代码+DesktopGUIMemoryPanelTest：模拟 notebook 工具；如果没有这行，read/edit 状态无法断言。
      }, // 新增代码+DesktopGUIMemoryPanelTest：notebook 子 payload 结束；如果没有这行，测试数据语法不完整。
    }; // 新增代码+DesktopGUIMemoryPanelTest：组合 payload 结束；如果没有这行，测试数据语法不完整。
    const markup = renderToStaticMarkup(createElement(MemoryPanel, { payload: memoryPayload })); // 新增代码+DesktopGUIMemoryPanelTest：静态渲染记忆面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("记忆与预算"); // 新增代码+DesktopGUIMemoryPanelTest：确认面板标题可见；如果没有这行，页签主体可能渲染错组件。
    expect(markup).toContain("Context"); // 新增代码+DesktopGUIMemoryPanelTest：确认 Context 可见；如果没有这行，context 文件可能未渲染。
    expect(markup).toContain("Progress"); // 新增代码+DesktopGUIMemoryPanelTest：确认 Progress 可见；如果没有这行，progress 文件可能未渲染。
    expect(markup).toContain("Bugs"); // 新增代码+DesktopGUIMemoryPanelTest：确认 Bugs 可见；如果没有这行，bugs 文件可能未渲染。
    expect(markup).toContain("prompt_surface_report"); // 新增代码+DesktopGUIMemoryPanelTest：确认 prompt 工具可见；如果没有这行，prompt 工具区可能未渲染。
    expect(markup).toContain("token_budget_report"); // 新增代码+DesktopGUIMemoryPanelTest：确认 token 工具可见；如果没有这行，token 工具区可能未渲染。
    expect(markup).toContain("max messages"); // 新增代码+DesktopGUIMemoryPanelTest：确认消息预算可见；如果没有这行，预算区可能缺字段。
    expect(markup).toContain("max chars"); // 新增代码+DesktopGUIMemoryPanelTest：确认字符预算可见；如果没有这行，预算区可能缺字段。
    expect(markup).toContain("notebook_read"); // 新增代码+DesktopGUIMemoryPanelTest：确认 notebook_read 可见；如果没有这行，notebook 工具区可能未渲染。
    expect(markup).toContain("notebook_edit"); // 新增代码+DesktopGUIMemoryPanelTest：确认 notebook_edit 可见；如果没有这行，编辑边界不可见。
    expect(markup).toContain("read-only first pass"); // 新增代码+DesktopGUIMemoryPanelTest：确认只读优先策略可见；如果没有这行，风险边界可能消失。
    expect(markup).toContain("research/demo.ipynb"); // 新增代码+DesktopGUIMemoryPanelTest：确认 notebook 路径可见；如果没有这行，用户无法定位 notebook。
    expect(markup).not.toContain("SECRET_MEMORY_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUIMemoryPanelTest：确认未知 secret 不渲染；如果没有这行，白名单渲染回归无法发现。
  }); // 新增代码+DesktopGUIMemoryPanelTest：测试方法结束；如果没有这行，测试块语法不完整。

  it("renders clear empty states for empty memory data", () => { // 新增代码+DesktopGUIMemoryPanelTest：测试方法开始，验证空态不是空白；如果没有这段，真实首次启动时用户可能误以为坏了。
    const markup = renderToStaticMarkup(createElement(MemoryPanel, { payload: { memory: { files: [] }, prompt: { tools: [], context_budget: {} }, notebook: { tools: [], notebooks: [] } } })); // 新增代码+DesktopGUIMemoryPanelTest：渲染空 payload；如果没有这行，空态断言没有 HTML 输入。
    expect(markup).toContain("暂无记忆文件数据。"); // 新增代码+DesktopGUIMemoryPanelTest：确认记忆文件空态可见；如果没有这行，空 memory 会像加载失败。
    expect(markup).toContain("暂无工具数据。"); // 新增代码+DesktopGUIMemoryPanelTest：确认工具空态可见；如果没有这行，空工具会像加载失败。
    expect(markup).toContain("暂无 notebook 文件。"); // 新增代码+DesktopGUIMemoryPanelTest：确认 notebook 空态可见；如果没有这行，空 notebook 会像加载失败。
  }); // 新增代码+DesktopGUIMemoryPanelTest：空态测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIMemoryPanelTest：测试套件结束；如果没有这行，describe 语法不完整。
