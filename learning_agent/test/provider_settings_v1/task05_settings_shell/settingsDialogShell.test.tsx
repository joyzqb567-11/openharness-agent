import { isValidElement, type ReactElement, type ReactNode } from "react"; // 新增代码+ProviderSettingsShellTest：导入 React 元素判断工具；如果没有这行，测试无法安全遍历 Sidebar 返回的 JSX。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+ProviderSettingsShellTest：导入服务端渲染工具；如果没有这行，测试无法在无浏览器环境检查弹窗 HTML。
import { describe, expect, it, vi } from "vitest"; // 新增代码+ProviderSettingsShellTest：导入 Vitest 测试工具；如果没有这行，设置弹窗 shell 行为无法自动验证。
import { SettingsDialog } from "../src/components/settings/SettingsDialog"; // 新增代码+ProviderSettingsShellTest：导入待实现的设置弹窗；如果没有这行，测试不会约束真实组件。
import { Sidebar } from "../src/components/Sidebar"; // 新增代码+ProviderSettingsShellTest：导入侧栏组件；如果没有这行，设置入口回调无法自动验证。

function flattenChildren(children: ReactNode): ReactElement[] { // 新增代码+ProviderSettingsShellTest：函数段开始，把 JSX children 展平成元素数组；如果没有这段，测试很难找到嵌套的设置按钮。
  const values = Array.isArray(children) ? children : [children]; // 新增代码+ProviderSettingsShellTest：把单个 child 也转成数组；如果没有这行，单节点 children 无法统一遍历。
  return values.filter(isValidElement); // 新增代码+ProviderSettingsShellTest：只保留 React 元素；如果没有这行，字符串和空节点会导致 props 读取异常。
} // 新增代码+ProviderSettingsShellTest：函数段结束，flattenChildren 到此结束；如果没有这行，函数语法不完整。

function findByClassName(node: ReactElement, className: string): ReactElement | null { // 新增代码+ProviderSettingsShellTest：函数段开始，按 className 查找 React 元素；如果没有这段，测试只能依赖脆弱的数组下标。
  const nodeClassName = typeof node.props.className === "string" ? node.props.className : ""; // 新增代码+ProviderSettingsShellTest：读取当前节点 className；如果没有这行，非字符串 className 会让查找报错。
  if (nodeClassName.split(" ").includes(className)) { // 新增代码+ProviderSettingsShellTest：判断当前节点是否包含目标类名；如果没有这行，设置按钮无法被识别。
    return node; // 新增代码+ProviderSettingsShellTest：找到目标节点后返回；如果没有这行，查找会错过当前节点。
  } // 新增代码+ProviderSettingsShellTest：当前节点匹配分支结束；如果没有这行，条件块语法不完整。
  for (const child of flattenChildren(node.props.children)) { // 新增代码+ProviderSettingsShellTest：遍历子元素；如果没有这行，嵌套按钮不会被找到。
    const found = findByClassName(child, className); // 新增代码+ProviderSettingsShellTest：递归查找子树；如果没有这行，查找只能停在一层。
    if (found !== null) { // 新增代码+ProviderSettingsShellTest：判断子树是否命中；如果没有这行，找到结果也不会提前返回。
      return found; // 新增代码+ProviderSettingsShellTest：返回子树命中节点；如果没有这行，测试会继续遍历并最终失败。
    } // 新增代码+ProviderSettingsShellTest：子树命中分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+ProviderSettingsShellTest：子元素遍历结束；如果没有这行，for 循环语法不完整。
  return null; // 新增代码+ProviderSettingsShellTest：没有找到时返回 null；如果没有这行，函数返回值不稳定。
} // 新增代码+ProviderSettingsShellTest：函数段结束，findByClassName 到此结束；如果没有这行，函数语法不完整。

describe("settings dialog shell", () => { // 新增代码+ProviderSettingsShellTest：测试段开始，覆盖设置弹窗 shell 和侧栏入口；如果没有这段，Task 5 没有自动验收。
  it("opens from the sidebar settings button", () => { // 新增代码+ProviderSettingsShellTest：测试段开始，验证左下角设置入口；如果没有这段，按钮可能只有外观没有行为。
    const onOpenSettings = vi.fn(); // 新增代码+ProviderSettingsShellTest：创建设置入口回调 mock；如果没有这行，测试无法知道按钮是否触发。
    const sidebar = Sidebar({ projectName: "OpenHarness", sessions: [], activeSessionId: "", archivedCount: 0, onNewConversation: vi.fn(), onOpenSearch: vi.fn(), onOpenArchived: vi.fn(), onSelectSession: vi.fn(), onOpenSettings }); // 新增代码+ProviderSettingsShellTest：渲染 Sidebar 元素树；如果没有这行，测试没有被测对象。
    const settingsButton = findByClassName(sidebar, "sidebar-settings"); // 新增代码+ProviderSettingsShellTest：查找底部设置按钮；如果没有这行，测试会依赖具体 JSX 层级。
    expect(settingsButton).not.toBeNull(); // 新增代码+ProviderSettingsShellTest：确认设置按钮存在；如果没有这行，入口缺失不会被发现。
    settingsButton?.props.onClick(); // 新增代码+ProviderSettingsShellTest：直接触发按钮点击处理；如果没有这行，回调行为不会被验证。
    expect(onOpenSettings).toHaveBeenCalledTimes(1); // 新增代码+ProviderSettingsShellTest：确认只触发一次打开回调；如果没有这行，重复触发或未触发都可能漏过。
  }); // 新增代码+ProviderSettingsShellTest：侧栏入口测试结束；如果没有这行，测试块语法不完整。

  it("renders provider settings shell with version and dev secret warning", () => { // 新增代码+ProviderSettingsShellTest：测试段开始，验证设置弹窗默认视觉骨架；如果没有这段，弹窗可能缺少关键导航和警告。
    const markup = renderToStaticMarkup(<SettingsDialog open={true} onClose={() => {}} version="0.1.0" secretStoreWarning="开发模式警告" />); // 新增代码+ProviderSettingsShellTest：渲染打开状态的设置弹窗；如果没有这行，后续断言没有 HTML 输入。
    expect(markup).toContain("role=\"dialog\""); // 新增代码+ProviderSettingsShellTest：确认弹窗语义角色；如果没有这行，读屏器支持可能退化。
    expect(markup).toContain("提供商"); // 新增代码+ProviderSettingsShellTest：确认默认 provider 标签存在；如果没有这行，用户找不到 Provider 设置页。
    expect(markup).toContain("模型"); // 新增代码+ProviderSettingsShellTest：确认模型标签存在；如果没有这行，后续模型管理没有入口。
    expect(markup).toContain("OpenHarness Desktop"); // 新增代码+ProviderSettingsShellTest：确认 footer 产品名；如果没有这行，弹窗缺少桌面壳身份。
    expect(markup).toContain("v0.1.0"); // 新增代码+ProviderSettingsShellTest：确认 package 版本展示；如果没有这行，用户无法确认当前桌面版本。
    expect(markup).toContain("开发模式警告"); // 新增代码+ProviderSettingsShellTest：确认 dev secret warning 可见；如果没有这行，开发密钥存储风险会被隐藏。
  }); // 新增代码+ProviderSettingsShellTest：打开弹窗测试结束；如果没有这行，测试块语法不完整。

  it("does not render the dialog when closed", () => { // 新增代码+ProviderSettingsShellTest：测试段开始，验证关闭状态；如果没有这段，关闭弹窗可能仍遮挡主界面。
    const markup = renderToStaticMarkup(<SettingsDialog open={false} onClose={() => {}} version="0.1.0" secretStoreWarning="" />); // 新增代码+ProviderSettingsShellTest：渲染关闭状态；如果没有这行，后续断言没有输入。
    expect(markup).toBe(""); // 新增代码+ProviderSettingsShellTest：确认关闭状态完全不输出；如果没有这行，overlay 可能残留在 DOM。
  }); // 新增代码+ProviderSettingsShellTest：关闭状态测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ProviderSettingsShellTest：测试段结束；如果没有这行，describe 语法不完整。
