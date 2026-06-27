import { createElement } from "react"; // 新增代码+DesktopGUIPlanningPanelTest：导入 React 元素工厂；如果没有这行，测试无法在无浏览器环境构造 PlanningPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIPlanningPanelTest：导入静态 HTML 渲染工具；如果没有这行，测试无法检查肉眼可见文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIPlanningPanelTest：导入 Vitest 测试 API；如果没有这行，测试块和断言无法运行。
import { PlanningPanel } from "../src/components/PlanningPanel"; // 新增代码+DesktopGUIPlanningPanelTest：导入被测计划协作面板；如果没有这行，测试没有目标组件。

describe("PlanningPanel", () => { // 新增代码+DesktopGUIPlanningPanelTest：测试套件开始，覆盖计划协作面板；如果没有这段，计划页签可见性没有自动化保护。
  it("renders todos, tasks, peers, messages, tools, and hides unknown secret fields", () => { // 新增代码+DesktopGUIPlanningPanelTest：测试方法开始，验证可见信息和字段白名单；如果没有这段，面板可能显示不出核心状态或误渲染 secret。
    const planningPayload = { // 新增代码+DesktopGUIPlanningPanelTest：构造 planning payload；如果没有这行，组件没有输入数据。
      ok: true, // 新增代码+DesktopGUIPlanningPanelTest：模拟成功响应；如果没有这行，payload 形状不完整。
      schema_version: 2, // 新增代码+DesktopGUIPlanningPanelTest：模拟 schema 版本；如果没有这行，payload 缺少协议字段。
      tool_count: 2, // 新增代码+DesktopGUIPlanningPanelTest：模拟计划工具总数；如果没有这行，标题统计无法断言。
      available_tool_count: 2, // 新增代码+DesktopGUIPlanningPanelTest：模拟可用工具数；如果没有这行，标题统计无法断言。
      todo_count: 1, // 新增代码+DesktopGUIPlanningPanelTest：模拟 todo 数量；如果没有这行，摘要栏无法断言。
      active_task_count: 1, // 新增代码+DesktopGUIPlanningPanelTest：模拟活动任务数量；如果没有这行，摘要栏无法断言。
      peer_count: 1, // 新增代码+DesktopGUIPlanningPanelTest：模拟 peer 数量；如果没有这行，摘要栏无法断言。
      pending_peer_message_count: 1, // 新增代码+DesktopGUIPlanningPanelTest：模拟待确认消息数量；如果没有这行，摘要栏无法断言。
      status_degraded: false, // 新增代码+DesktopGUIPlanningPanelTest：模拟正常读取状态；如果没有这行，降级分支默认不清楚。
      todos: [{ id: "todo_a", content: "接入 planning GUI", status: "in_progress", priority: "high", raw_secret: "SECRET_TODO_SHOULD_NOT_RENDER" }], // 新增代码+DesktopGUIPlanningPanelTest：模拟 todo 并放入未知 secret 字段；如果没有这行，无法验证白名单渲染。
      tasks: [{ task_id: "task_a", label: "Planning Panel", prompt_summary: "实现计划协作面板", status: "running", kind: "agent", background: true, raw_secret: "SECRET_TASK_SHOULD_NOT_RENDER" }], // 新增代码+DesktopGUIPlanningPanelTest：模拟运行中任务；如果没有这行，任务区无法断言。
      peers: [{ peer_id: "peer_a", name: "Reviewer", role: "reviewer", status: "running", notes: "负责检查 GUI", pending_message_count: 1 }], // 新增代码+DesktopGUIPlanningPanelTest：模拟团队 peer；如果没有这行，团队区无法断言。
      peer_messages: [{ message_id: "message_a", sender: "planner", peer_name: "Reviewer", content_summary: "请检查 task_a", status: "pending", created_at: "2026-06-27T00:00:00Z" }], // 新增代码+DesktopGUIPlanningPanelTest：模拟 peer 消息；如果没有这行，消息区无法断言。
      tools: [{ name: "todo_read", category: "planning", status: "ready", available: true, read_only: true }, { name: "task_list", category: "delegation", status: "deferred", available: true, read_only: true }], // 新增代码+DesktopGUIPlanningPanelTest：模拟计划工具；如果没有这行，工具区无法断言。
    }; // 新增代码+DesktopGUIPlanningPanelTest：planning payload 结束；如果没有这行，测试数据语法不完整。
    const markup = renderToStaticMarkup(createElement(PlanningPanel, { payload: planningPayload })); // 新增代码+DesktopGUIPlanningPanelTest：静态渲染计划协作面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("计划协作"); // 新增代码+DesktopGUIPlanningPanelTest：确认面板标题可见；如果没有这行，页签主体可能渲染错组件。
    expect(markup).toContain("接入 planning GUI"); // 新增代码+DesktopGUIPlanningPanelTest：确认 todo 内容可见；如果没有这行，todo 区可能未渲染。
    expect(markup).toContain("Planning Panel"); // 新增代码+DesktopGUIPlanningPanelTest：确认任务 label 可见；如果没有这行，任务区可能未渲染。
    expect(markup).toContain("Reviewer"); // 新增代码+DesktopGUIPlanningPanelTest：确认 peer 名称可见；如果没有这行，团队区可能未渲染。
    expect(markup).toContain("请检查 task_a"); // 新增代码+DesktopGUIPlanningPanelTest：确认 peer 消息可见；如果没有这行，消息区可能未渲染。
    expect(markup).toContain("todo_read"); // 新增代码+DesktopGUIPlanningPanelTest：确认工具名可见；如果没有这行，工具区可能未渲染。
    expect(markup).not.toContain("SECRET_TODO_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUIPlanningPanelTest：确认未知 todo secret 不渲染；如果没有这行，白名单渲染回归无法发现。
    expect(markup).not.toContain("SECRET_TASK_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUIPlanningPanelTest：确认未知 task secret 不渲染；如果没有这行，白名单渲染回归无法发现。
  }); // 新增代码+DesktopGUIPlanningPanelTest：测试方法结束；如果没有这行，测试块语法不完整。

  it("renders clear empty states for empty planning data", () => { // 新增代码+DesktopGUIPlanningPanelTest：测试方法开始，验证空态不是空白；如果没有这段，真实首次启动时用户可能误以为坏了。
    const markup = renderToStaticMarkup(createElement(PlanningPanel, { payload: { ok: true, tool_count: 0, available_tool_count: 0, todos: [], tasks: [], peers: [], peer_messages: [], tools: [] } })); // 新增代码+DesktopGUIPlanningPanelTest：渲染空 payload；如果没有这行，空态断言没有 HTML 输入。
    expect(markup).toContain("暂无 todo 数据。"); // 新增代码+DesktopGUIPlanningPanelTest：确认 todo 空态可见；如果没有这行，空 todo 会像加载失败。
    expect(markup).toContain("暂无任务数据。"); // 新增代码+DesktopGUIPlanningPanelTest：确认任务空态可见；如果没有这行，空任务会像加载失败。
    expect(markup).toContain("暂无团队数据。"); // 新增代码+DesktopGUIPlanningPanelTest：确认团队空态可见；如果没有这行，空团队会像加载失败。
    expect(markup).toContain("暂无消息数据。"); // 新增代码+DesktopGUIPlanningPanelTest：确认消息空态可见；如果没有这行，空消息会像加载失败。
  }); // 新增代码+DesktopGUIPlanningPanelTest：空态测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIPlanningPanelTest：测试套件结束；如果没有这行，describe 语法不完整。
