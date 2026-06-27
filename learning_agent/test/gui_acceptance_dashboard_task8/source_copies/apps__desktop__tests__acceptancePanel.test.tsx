import { createElement } from "react"; // 新增代码+DesktopGUIAcceptancePanelTest：导入 React 元素工厂；如果没有这行，测试无法构造 AcceptancePanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUIAcceptancePanelTest：导入静态渲染工具；如果没有这行，测试无法检查真实 HTML 文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUIAcceptancePanelTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面端测试运行器识别。
import { AcceptancePanel } from "../src/components/AcceptancePanel"; // 新增代码+DesktopGUIAcceptancePanelTest：导入待测验收面板；如果没有这行，测试无法约束验收页签 UI。

const acceptancePayload = { // 新增代码+DesktopGUIAcceptancePanelTest：定义验收 payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  ok: true, // 新增代码+DesktopGUIAcceptancePanelTest：模拟后端成功响应；如果没有这行，payload 形状不完整。
  schema_version: 2, // 新增代码+DesktopGUIAcceptancePanelTest：保存协议版本；如果没有这行，payload 形状不完整。
  scenario_count: 1, // 新增代码+DesktopGUIAcceptancePanelTest：保存场景总数；如果没有这行，摘要区没有数量输入。
  run_count: 1, // 新增代码+DesktopGUIAcceptancePanelTest：保存运行总数；如果没有这行，摘要区没有证据规模。
  controller: { controller_ps1_exists: true, visible_terminal_required: true }, // 新增代码+DesktopGUIAcceptancePanelTest：模拟可见终端控制器存在；如果没有这行，摘要区无法显示门禁状态。
  safe_error: "", // 新增代码+DesktopGUIAcceptancePanelTest：保存空安全错误；如果没有这行，payload 形状不完整。
  raw_secret: "SECRET_ACCEPTANCE_SHOULD_NOT_RENDER", // 新增代码+DesktopGUIAcceptancePanelTest：放入不应渲染的未知字段；如果没有这行，测试无法证明面板不会盲目展开原始 payload。
  scenarios: [ // 新增代码+DesktopGUIAcceptancePanelTest：保存场景列表；如果没有这段，面板只能显示空态。
    { // 新增代码+DesktopGUIAcceptancePanelTest：场景卡片开始；如果没有这个对象，列表没有可见条目。
      id: "smoke", // 新增代码+DesktopGUIAcceptancePanelTest：保存场景 id；如果没有这行，运行按钮没有目标。
      name: "smoke", // 新增代码+DesktopGUIAcceptancePanelTest：保存场景名；如果没有这行，用户无法识别场景。
      category: "smoke", // 新增代码+DesktopGUIAcceptancePanelTest：保存分类；如果没有这行，面板无法显示安全 smoke 场景。
      max_seconds: 30, // 新增代码+DesktopGUIAcceptancePanelTest：保存最大秒数；如果没有这行，耗时提示无法验证。
      prompt_preview: "请回复 ACCEPTANCE_HARNESS_OK", // 新增代码+DesktopGUIAcceptancePanelTest：保存 prompt 预览；如果没有这行，场景摘要无法验证。
      run_supported: true, // 新增代码+DesktopGUIAcceptancePanelTest：保存运行能力；如果没有这行，运行按钮可能被禁用。
      last_result: { // 新增代码+DesktopGUIAcceptancePanelTest：保存最近运行；如果没有这段，状态和证据无法验证。
        status: "passed", // 新增代码+DesktopGUIAcceptancePanelTest：保存通过状态；如果没有这行，状态徽标没有输入。
        evidence: [ // 新增代码+DesktopGUIAcceptancePanelTest：保存证据列表；如果没有这段，证据渲染无法验证。
          { kind: "result", label: "result.json", relative_path: "learning_agent/acceptance_controller/runs/smoke/result.json", exists: true }, // 新增代码+DesktopGUIAcceptancePanelTest：保存结果证据；如果没有这行，result 链接无法验证。
          { kind: "screenshot", label: "final screenshot", relative_path: "learning_agent/acceptance_controller/runs/smoke/final.png", exists: true }, // 新增代码+DesktopGUIAcceptancePanelTest：保存截图证据；如果没有这行，肉眼证据索引无法验证。
        ], // 新增代码+DesktopGUIAcceptancePanelTest：证据列表结束；如果没有这行，payload 语法不完整。
      }, // 新增代码+DesktopGUIAcceptancePanelTest：最近运行结束；如果没有这行，payload 语法不完整。
    }, // 新增代码+DesktopGUIAcceptancePanelTest：场景卡片结束；如果没有这行，数组对象语法不完整。
  ], // 新增代码+DesktopGUIAcceptancePanelTest：场景列表结束；如果没有这行，payload 语法不完整。
  recent_runs: [ // 新增代码+DesktopGUIAcceptancePanelTest：保存最近运行列表；如果没有这段，Recent Runs 区无法验证。
    { id: "smoke_run", scenario_name: "smoke", status: "passed", updated_at: "2026-06-27T00:00:00Z", evidence: [] }, // 新增代码+DesktopGUIAcceptancePanelTest：保存运行摘要；如果没有这行，最近运行区没有条目。
  ], // 新增代码+DesktopGUIAcceptancePanelTest：最近运行列表结束；如果没有这行，payload 语法不完整。
}; // 新增代码+DesktopGUIAcceptancePanelTest：payload 夹具结束；如果没有这行，常量定义不完整。

const lastActionResult = { // 新增代码+DesktopGUIAcceptancePanelTest：定义最近启动结果夹具；如果没有这段，测试无法证明运行反馈区域可见。
  ok: true, // 新增代码+DesktopGUIAcceptancePanelTest：标记请求成功到达后端；如果没有这行，结果形状不完整。
  action: "run", // 新增代码+DesktopGUIAcceptancePanelTest：保存最近动作；如果没有这行，反馈区不知道是哪种控制。
  scenario_id: "smoke", // 新增代码+DesktopGUIAcceptancePanelTest：保存目标场景；如果没有这行，反馈形状不完整。
  status: "planned", // 新增代码+DesktopGUIAcceptancePanelTest：保存 dry-run 状态；如果没有这行，用户看不到启动计划。
  supported: true, // 新增代码+DesktopGUIAcceptancePanelTest：保存支持状态；如果没有这行，动作结果形状不完整。
  launched: false, // 新增代码+DesktopGUIAcceptancePanelTest：保存未启动进程；如果没有这行，测试无法区分 dry-run。
  message: "已生成真实可见终端验收启动计划。", // 新增代码+DesktopGUIAcceptancePanelTest：保存可读反馈；如果没有这行，点击后没有肉眼可见结果。
  safe_error: "", // 新增代码+DesktopGUIAcceptancePanelTest：保存空安全错误；如果没有这行，结果形状不完整。
  run: {}, // 新增代码+DesktopGUIAcceptancePanelTest：保存 run 摘要占位；如果没有这行，结果形状不完整。
}; // 新增代码+DesktopGUIAcceptancePanelTest：最近启动结果夹具结束；如果没有这行，常量定义不完整。

function noop(): void { // 新增代码+DesktopGUIAcceptancePanelTest：函数段开始，提供测试用空回调；如果没有这段，按钮 props 需要重复匿名函数。
  return undefined; // 新增代码+DesktopGUIAcceptancePanelTest：明确什么也不做；如果没有这行，函数会隐式返回但初学者不易理解。
} // 新增代码+DesktopGUIAcceptancePanelTest：函数段结束，noop 到此结束；如果没有这行，函数语法不完整。

describe("AcceptancePanel", () => { // 新增代码+DesktopGUIAcceptancePanelTest：测试组开始，覆盖验收页签可见 UI；如果没有这段，验收面板回归不会被自动发现。
  it("renders scenarios, evidence, visible gate state, and latest action result", () => { // 新增代码+DesktopGUIAcceptancePanelTest：测试场景、证据、门禁状态和反馈；如果没有这段，GUI 可能只有部分内容。
    const markup = renderToStaticMarkup(createElement(AcceptancePanel, { payload: acceptancePayload, onRunScenario: noop, actionPending: false, lastActionResult })); // 新增代码+DesktopGUIAcceptancePanelTest：静态渲染验收面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("验收控制器"); // 新增代码+DesktopGUIAcceptancePanelTest：确认面板标题可见；如果没有这行，验收页签可能渲染成空白。
    expect(markup).toContain("smoke"); // 新增代码+DesktopGUIAcceptancePanelTest：确认 smoke 场景可见；如果没有这行，安全样例可能丢失。
    expect(markup).toContain("visible gate"); // 新增代码+DesktopGUIAcceptancePanelTest：确认可见终端门禁状态可见；如果没有这行，规则十七边界可能不可见。
    expect(markup).toContain("final screenshot"); // 新增代码+DesktopGUIAcceptancePanelTest：确认截图证据可见；如果没有这行，肉眼验收证据索引可能丢失。
    expect(markup).toContain("已生成真实可见终端验收启动计划。"); // 新增代码+DesktopGUIAcceptancePanelTest：确认最近动作反馈可见；如果没有这行，点击结果可能没有肉眼反馈。
    expect(markup).not.toContain("SECRET_ACCEPTANCE_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUIAcceptancePanelTest：确认未知敏感字段不会被盲目渲染；如果没有这行，原始 payload 可能泄漏。
  }); // 新增代码+DesktopGUIAcceptancePanelTest：场景渲染测试结束；如果没有这行，测试块语法不完整。

  it("renders a stable empty state", () => { // 新增代码+DesktopGUIAcceptancePanelTest：测试空状态；如果没有这段，无场景场景可能显示空白。
    const markup = renderToStaticMarkup(createElement(AcceptancePanel, { payload: { scenarios: [], recent_runs: [], scenario_count: 0, run_count: 0, controller: {} }, actionPending: false, lastActionResult: {} })); // 新增代码+DesktopGUIAcceptancePanelTest：静态渲染空 payload；如果没有这行，空态断言没有 HTML 输入。
    expect(markup).toContain("暂无验收场景。"); // 新增代码+DesktopGUIAcceptancePanelTest：确认空态文案可见；如果没有这行，用户不知道是否仍在加载。
    expect(markup).toContain("暂无运行记录。"); // 新增代码+DesktopGUIAcceptancePanelTest：确认运行空态可见；如果没有这行，证据历史空白难解释。
  }); // 新增代码+DesktopGUIAcceptancePanelTest：空态测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUIAcceptancePanelTest：测试组结束；如果没有这行，describe 语法不完整。
