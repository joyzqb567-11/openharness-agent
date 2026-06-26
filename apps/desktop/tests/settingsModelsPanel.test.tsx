import { isValidElement, type ChangeEvent, type ReactElement, type ReactNode } from "react"; // 新增代码+SettingsModelsPanelTest：导入 React 元素和事件类型；如果没有这行，测试无法安全遍历组件树或模拟 switch 事件。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+SettingsModelsPanelTest：导入静态渲染工具；如果没有这行，模型面板文案无法在无浏览器环境断言。
import { describe, expect, it, vi } from "vitest"; // 新增代码+SettingsModelsPanelTest：导入 Vitest 工具；如果没有这行，模型面板没有自动测试入口。
import { SettingsModelsPanel } from "../src/components/settings/SettingsModelsPanel"; // 新增代码+SettingsModelsPanelTest：导入模型设置面板；如果没有这行，Task 8 没有被测组件。
import type { ProviderSettingsViewModel } from "../src/state/providerSettingsStore"; // 新增代码+SettingsModelsPanelTest：导入 view model 类型；如果没有这行，fixture 字段含义不清楚。

function flattenChildren(children: ReactNode): ReactElement[] { // 新增代码+SettingsModelsPanelTest：函数段开始，递归展开 JSX children；如果没有这段，测试找不到嵌套 switch。
  const values = Array.isArray(children) ? children : [children]; // 新增代码+SettingsModelsPanelTest：把单个 child 也转成数组；如果没有这行，遍历逻辑无法统一。
  return values.flatMap((child) => Array.isArray(child) ? flattenChildren(child) : isValidElement(child) ? [child] : []); // 新增代码+SettingsModelsPanelTest：递归展开数组并只保留 React 元素；如果没有这行，map 产生的行数组会被漏掉。
} // 新增代码+SettingsModelsPanelTest：函数段结束，flattenChildren 到此结束；如果没有这行，函数语法不完整。

function findByTestId(node: ReactElement, testId: string): ReactElement | null { // 新增代码+SettingsModelsPanelTest：函数段开始，按 data-testid 查找元素；如果没有这段，测试只能依赖脆弱 JSX 下标。
  if (node.props["data-testid"] === testId) { // 新增代码+SettingsModelsPanelTest：检查当前节点是否命中；如果没有这行，目标 switch 无法被识别。
    return node; // 新增代码+SettingsModelsPanelTest：命中时返回当前节点；如果没有这行，查找会错过目标元素。
  } // 新增代码+SettingsModelsPanelTest：当前节点命中分支结束；如果没有这行，条件块语法不完整。
  for (const child of flattenChildren(node.props.children)) { // 新增代码+SettingsModelsPanelTest：遍历子元素；如果没有这行，嵌套 switch 不会被找到。
    const found = findByTestId(child, testId); // 新增代码+SettingsModelsPanelTest：递归查找子树；如果没有这行，查找只能停留一层。
    if (found !== null) { // 新增代码+SettingsModelsPanelTest：判断子树是否命中；如果没有这行，找到后不会提前返回。
      return found; // 新增代码+SettingsModelsPanelTest：返回子树命中节点；如果没有这行，测试会继续遍历并最终失败。
    } // 新增代码+SettingsModelsPanelTest：子树命中分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+SettingsModelsPanelTest：子元素遍历结束；如果没有这行，for 循环语法不完整。
  return null; // 新增代码+SettingsModelsPanelTest：找不到时返回 null；如果没有这行，函数返回值不稳定。
} // 新增代码+SettingsModelsPanelTest：函数段结束，findByTestId 到此结束；如果没有这行，函数语法不完整。

const viewModel: ProviderSettingsViewModel = { // 新增代码+SettingsModelsPanelTest：定义模型面板 fixture；如果没有这段，分组和 switch 测试没有输入。
  defaultTab: "providers", // 新增代码+SettingsModelsPanelTest：声明默认页签；如果没有这行，view model 形状不完整。
  schemaVersion: 2, // 新增代码+SettingsModelsPanelTest：声明 schema 版本；如果没有这行，view model 形状不完整。
  secretStoreWarning: "", // 新增代码+SettingsModelsPanelTest：声明无 secret warning；如果没有这行，view model 形状不完整。
  defaultProviderId: "", // 新增代码+SettingsModelsPanelTest：声明默认 provider；如果没有这行，view model 形状不完整。
  defaultModelId: "", // 新增代码+SettingsModelsPanelTest：声明默认模型；如果没有这行，view model 形状不完整。
  customProviderCta: { id: "custom-provider-cta", displayName: "自定义提供商", description: "添加兼容 provider" }, // 新增代码+SettingsModelsPanelTest：声明自定义 CTA；如果没有这行，view model 形状不完整。
  providers: [ // 新增代码+SettingsModelsPanelTest：声明 provider 列表；如果没有这行，模型分组没有来源。
    { id: "custom-gateway", displayName: "Custom Gateway", kind: "custom", source: "custom", connected: false, maskedKey: "", description: "自定义", authMethods: [], primaryActionLabel: "+ 连接", primaryActionDisabled: false, models: [{ id: "custom-1", displayName: "Custom One", providerId: "custom-gateway", visible: false, supportsTools: false, supportsVision: false }] }, // 新增代码+SettingsModelsPanelTest：放入未连接 provider；如果没有这行，连接排序无法验证。
    { id: "openai", displayName: "OpenAI", kind: "built_in", source: "config", connected: true, maskedKey: "sk-***", description: "OpenAI", authMethods: [], primaryActionLabel: "断开", primaryActionDisabled: false, models: [{ id: "gpt-4.1", displayName: "GPT 4.1", providerId: "openai", visible: true, supportsTools: true, supportsVision: true }] }, // 新增代码+SettingsModelsPanelTest：放入已连接 provider；如果没有这行，已连接优先排序无法验证。
  ], // 新增代码+SettingsModelsPanelTest：provider 列表结束；如果没有这行，数组语法不完整。
}; // 新增代码+SettingsModelsPanelTest：模型面板 fixture 结束；如果没有这行，对象语法不完整。

describe("SettingsModelsPanel", () => { // 新增代码+SettingsModelsPanelTest：测试组开始；如果没有这段，Task 8 没有自动验收。
  it("renders grouped models with connected providers first", () => { // 新增代码+SettingsModelsPanelTest：测试分组和字段文案；如果没有这段，模型页可能丢字段或排序错误。
    const markup = renderToStaticMarkup(<SettingsModelsPanel viewModel={viewModel} pendingModelKey="" errorMessage="" onToggleModel={vi.fn()} />); // 新增代码+SettingsModelsPanelTest：渲染模型面板；如果没有这行，后续断言没有输入。
    expect(markup.indexOf("OpenAI")).toBeLessThan(markup.indexOf("Custom Gateway")); // 新增代码+SettingsModelsPanelTest：确认已连接 provider 排在前面；如果没有这行，用户难以先看到可用模型。
    expect(markup).toContain("GPT 4.1"); // 新增代码+SettingsModelsPanelTest：确认模型显示名可见；如果没有这行，模型行缺少主文本。
    expect(markup).toContain("gpt-4.1"); // 新增代码+SettingsModelsPanelTest：确认模型 id 可见；如果没有这行，用户无法区分同名模型。
    expect(markup).toContain("OpenAI"); // 新增代码+SettingsModelsPanelTest：确认 provider 名称可见；如果没有这行，模型来源不清楚。
    expect(markup).toContain("role=\"switch\""); // 新增代码+SettingsModelsPanelTest：确认可见性开关语义；如果没有这行，模型可见性无法被可访问工具识别。
  }); // 新增代码+SettingsModelsPanelTest：分组和字段文案测试结束；如果没有这行，测试块语法不完整。

  it("renders the empty state when no model rows exist", () => { // 新增代码+SettingsModelsPanelTest：测试空态；如果没有这段，没有模型时界面可能空白。
    const emptyMarkup = renderToStaticMarkup(<SettingsModelsPanel viewModel={{ ...viewModel, providers: [] }} pendingModelKey="" errorMessage="" onToggleModel={vi.fn()} />); // 新增代码+SettingsModelsPanelTest：渲染空 provider 模型面板；如果没有这行，空态断言没有输入。
    expect(emptyMarkup).toContain("连接提供商后会在这里显示模型"); // 新增代码+SettingsModelsPanelTest：确认蓝图指定空态文案；如果没有这行，用户不知道下一步要连接 provider。
  }); // 新增代码+SettingsModelsPanelTest：空态测试结束；如果没有这行，测试块语法不完整。

  it("calls visibility callback with provider, model, and next state", () => { // 新增代码+SettingsModelsPanelTest：测试 switch 回调；如果没有这段，开关可能调用错误 mutation。
    const onToggleModel = vi.fn(); // 新增代码+SettingsModelsPanelTest：创建回调 spy；如果没有这行，无法验证开关行为。
    const panel = SettingsModelsPanel({ viewModel, pendingModelKey: "", errorMessage: "", onToggleModel }); // 新增代码+SettingsModelsPanelTest：直接构建组件树；如果没有这行，无法读取 switch props。
    const switchNode = findByTestId(panel, "model-switch-openai-gpt-4.1"); // 新增代码+SettingsModelsPanelTest：查找 OpenAI 模型 switch；如果没有这行，后续无法模拟切换。
    const event = { target: { checked: false } } as ChangeEvent<HTMLInputElement>; // 新增代码+SettingsModelsPanelTest：构造关闭 switch 的事件；如果没有这行，onChange 没有新状态输入。
    switchNode?.props.onChange(event); // 新增代码+SettingsModelsPanelTest：触发 switch change；如果没有这行，回调不会被调用。
    expect(onToggleModel).toHaveBeenCalledWith("openai", "gpt-4.1", false); // 新增代码+SettingsModelsPanelTest：确认回调参数完整；如果没有这行，provider/model/visible 可能传错。
  }); // 新增代码+SettingsModelsPanelTest：switch 回调测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+SettingsModelsPanelTest：测试组结束；如果没有这行，describe 语法不完整。
