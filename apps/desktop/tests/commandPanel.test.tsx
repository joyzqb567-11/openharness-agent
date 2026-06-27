import { createElement } from "react"; // 新增代码+DesktopGUICommandConsolePanelTest：导入 React 元素工厂；如果没有这行，测试无法构造 CommandPanel。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+DesktopGUICommandConsolePanelTest：导入静态渲染工具；如果没有这行，测试无法检查真实 HTML 文本。
import { describe, expect, it } from "vitest"; // 新增代码+DesktopGUICommandConsolePanelTest：导入 Vitest 测试工具；如果没有这行，本文件不会被桌面端测试运行器识别。
import { CommandPanel } from "../src/components/CommandPanel"; // 新增代码+DesktopGUICommandConsolePanelTest：导入待测命令面板；如果没有这行，测试无法约束命令页签 UI。

const commandPayload = { // 新增代码+DesktopGUICommandConsolePanelTest：定义后台命令 payload 夹具；如果没有这段，每个断言都要重复构造后端数据。
  ok: true, // 新增代码+DesktopGUICommandConsolePanelTest：模拟后端成功响应；如果没有这行，面板可能走降级分支。
  schema_version: 2, // 新增代码+DesktopGUICommandConsolePanelTest：保存协议版本；如果没有这行，payload 形状不完整。
  command_count: 1, // 新增代码+DesktopGUICommandConsolePanelTest：保存命令总数；如果没有这行，摘要区没有数量输入。
  running_command_count: 1, // 新增代码+DesktopGUICommandConsolePanelTest：保存运行中数量；如果没有这行，摘要区无法显示活跃命令。
  stop_supported_count: 0, // 新增代码+DesktopGUICommandConsolePanelTest：保存可停止数量；如果没有这行，能力边界摘要无法验证。
  safe_error: "", // 新增代码+DesktopGUICommandConsolePanelTest：保存空安全错误；如果没有这行，payload 形状不完整。
  raw_secret: "SECRET_COMMAND_SHOULD_NOT_RENDER", // 新增代码+DesktopGUICommandConsolePanelTest：放入不应渲染的未知字段；如果没有这行，测试无法证明面板不会盲目展开原始 payload。
  commands: [ // 新增代码+DesktopGUICommandConsolePanelTest：保存命令列表；如果没有这段，面板只能显示空态。
    { // 新增代码+DesktopGUICommandConsolePanelTest：命令卡片开始；如果没有这个对象，列表没有可见条目。
      command_id: "bg_test", // 新增代码+DesktopGUICommandConsolePanelTest：保存命令 id；如果没有这行，停止按钮没有目标。
      label: "Dev server", // 新增代码+DesktopGUICommandConsolePanelTest：保存友好名称；如果没有这行，用户只能看较长命令行。
      command_text: "npm run dev --api-key [REDACTED]", // 新增代码+DesktopGUICommandConsolePanelTest：保存已脱敏命令；如果没有这行，面板无法显示执行内容。
      status: "running", // 新增代码+DesktopGUICommandConsolePanelTest：保存运行状态；如果没有这行，状态徽标没有输入。
      cwd_display: "apps/desktop", // 新增代码+DesktopGUICommandConsolePanelTest：保存相对工作目录；如果没有这行，用户不知道命令在哪运行。
      exit_code: null, // 新增代码+DesktopGUICommandConsolePanelTest：保存未知退出码；如果没有这行，运行中命令形状不完整。
      tail: "line one\nline two", // 新增代码+DesktopGUICommandConsolePanelTest：保存终端输出尾部；如果没有这行，命令面板没有可见输出。
      can_stop: false, // 新增代码+DesktopGUICommandConsolePanelTest：保存按钮禁用条件；如果没有这行，测试无法约束不做假停止能力。
      stop_supported: false, // 新增代码+DesktopGUICommandConsolePanelTest：保存后端停止能力；如果没有这行，按钮说明没有依据。
      stop_unavailable_reason: "当前后端没有 live process 句柄，不能安全停止。", // 新增代码+DesktopGUICommandConsolePanelTest：保存禁用原因；如果没有这行，用户不知道按钮为什么不可用。
    }, // 新增代码+DesktopGUICommandConsolePanelTest：命令卡片结束；如果没有这行，数组对象语法不完整。
  ], // 新增代码+DesktopGUICommandConsolePanelTest：命令列表结束；如果没有这行，payload 语法不完整。
}; // 新增代码+DesktopGUICommandConsolePanelTest：payload 夹具结束；如果没有这行，常量定义不完整。

const lastActionResult = { // 新增代码+DesktopGUICommandConsolePanelTest：定义最近控制结果夹具；如果没有这段，测试无法证明 stop 反馈区域可见。
  ok: true, // 新增代码+DesktopGUICommandConsolePanelTest：标记请求成功到达后端；如果没有这行，结果形状不完整。
  action: "stop", // 新增代码+DesktopGUICommandConsolePanelTest：保存最近动作；如果没有这行，反馈区不知道是哪种控制。
  status: "unavailable", // 新增代码+DesktopGUICommandConsolePanelTest：保存诚实不可用状态；如果没有这行，用户看不到 stop 失败原因。
  message: "GUI bridge 当前没有 live process 句柄。", // 新增代码+DesktopGUICommandConsolePanelTest：保存可读反馈；如果没有这行，点击后没有肉眼可见结果。
}; // 新增代码+DesktopGUICommandConsolePanelTest：最近控制结果夹具结束；如果没有这行，常量定义不完整。

function noop(): void { // 新增代码+DesktopGUICommandConsolePanelTest：函数段开始，提供测试用空回调；如果没有这段，按钮 props 需要重复匿名函数。
  return undefined; // 新增代码+DesktopGUICommandConsolePanelTest：明确什么也不做；如果没有这行，函数会隐式返回但初学者不易理解。
} // 新增代码+DesktopGUICommandConsolePanelTest：函数段结束，noop 到此结束；如果没有这行，函数语法不完整。

describe("CommandPanel", () => { // 新增代码+DesktopGUICommandConsolePanelTest：测试组开始，覆盖命令页签可见 UI；如果没有这段，命令面板回归不会被自动发现。
  it("renders command list, terminal tail, disabled stop reason, and latest result", () => { // 新增代码+DesktopGUICommandConsolePanelTest：测试命令列表、输出、停止说明和反馈；如果没有这段，GUI 可能只有部分内容。
    const markup = renderToStaticMarkup(createElement(CommandPanel, { payload: commandPayload, onStopCommand: noop, actionPending: false, lastActionResult })); // 新增代码+DesktopGUICommandConsolePanelTest：静态渲染命令面板；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("后台命令"); // 新增代码+DesktopGUICommandConsolePanelTest：确认面板标题可见；如果没有这行，命令页签可能渲染成空白。
    expect(markup).toContain("Dev server"); // 新增代码+DesktopGUICommandConsolePanelTest：确认命令友好名称可见；如果没有这行，用户无法快速识别命令。
    expect(markup).toContain("line two"); // 新增代码+DesktopGUICommandConsolePanelTest：确认终端输出可见；如果没有这行，tail 区域可能丢失。
    expect(markup).toContain("当前后端没有 live process 句柄"); // 新增代码+DesktopGUICommandConsolePanelTest：确认停止不可用原因可见；如果没有这行，禁用按钮缺少解释。
    expect(markup).toContain("GUI bridge 当前没有 live process 句柄。"); // 新增代码+DesktopGUICommandConsolePanelTest：确认最近动作反馈可见；如果没有这行，点击结果可能没有肉眼反馈。
    expect(markup).not.toContain("SECRET_COMMAND_SHOULD_NOT_RENDER"); // 新增代码+DesktopGUICommandConsolePanelTest：确认未知敏感字段不会被盲目渲染；如果没有这行，原始 payload 可能泄漏。
  }); // 新增代码+DesktopGUICommandConsolePanelTest：命令列表渲染测试结束；如果没有这行，测试块语法不完整。

  it("renders a stable empty state", () => { // 新增代码+DesktopGUICommandConsolePanelTest：测试空状态；如果没有这段，无命令场景可能显示空白。
    const markup = renderToStaticMarkup(createElement(CommandPanel, { payload: { commands: [], command_count: 0, running_command_count: 0, stop_supported_count: 0 }, actionPending: false, lastActionResult: {} })); // 新增代码+DesktopGUICommandConsolePanelTest：静态渲染空 payload；如果没有这行，空态断言没有 HTML 输入。
    expect(markup).toContain("暂无后台命令数据。"); // 新增代码+DesktopGUICommandConsolePanelTest：确认空态文案可见；如果没有这行，用户不知道是否仍在加载。
  }); // 新增代码+DesktopGUICommandConsolePanelTest：空态测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopGUICommandConsolePanelTest：测试组结束；如果没有这行，describe 语法不完整。
