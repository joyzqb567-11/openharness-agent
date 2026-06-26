import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+CustomProviderDialogTest：导入静态渲染工具；如果没有这行，测试无法检查弹窗初始字段是否可见。
import { describe, expect, it, vi } from "vitest"; // 新增代码+CustomProviderDialogTest：导入 Vitest 测试工具；如果没有这行，自定义 provider 弹窗没有自动验收入口。
import { buildCustomProviderRequest, customProviderValidationError, CustomProviderDialog, type CustomProviderDialogState } from "../src/components/settings/CustomProviderDialog"; // 新增代码+CustomProviderDialogTest：导入弹窗和纯校验 helper；如果没有这行，Task 7 的表单合同无法被测试固定。

const validState: CustomProviderDialogState = { // 新增代码+CustomProviderDialogTest：定义一份合法表单 fixture；如果没有这段，payload 构造测试没有稳定输入。
  providerId: "local-openai", // 新增代码+CustomProviderDialogTest：提供合法 provider id；如果没有这行，id 校验会阻止保存路径测试。
  displayName: "Local OpenAI", // 新增代码+CustomProviderDialogTest：提供显示名；如果没有这行，保存 payload 无法显示给用户。
  baseUrl: "http://127.0.0.1:8000/v1", // 新增代码+CustomProviderDialogTest：提供合法 base URL；如果没有这行，URL 校验会阻止保存路径测试。
  apiKey: "unit-test-secret-value", // 新增代码+CustomProviderDialogTest：提供测试密钥；如果没有这行，fields.api_key 无法验证。
  models: [{ id: "local-model", displayName: "Local Model" }], // 新增代码+CustomProviderDialogTest：提供至少一个模型；如果没有这行，模型校验会阻止保存。
  headers: [{ key: "X-Test", value: "yes" }, { key: "", value: "" }], // 新增代码+CustomProviderDialogTest：同时提供有效和空 header；如果没有这行，空 header 忽略规则无法验证。
}; // 新增代码+CustomProviderDialogTest：合法表单 fixture 结束；如果没有这行，对象语法不完整。

describe("CustomProviderDialog", () => { // 新增代码+CustomProviderDialogTest：测试组开始；如果没有这段，自定义 provider 弹窗缺少自动验收。
  it("renders the required fields and safe action labels", () => { // 新增代码+CustomProviderDialogTest：测试初始 UI 字段；如果没有这段，弹窗可能漏掉必要输入。
    const markup = renderToStaticMarkup(<CustomProviderDialog open={true} pending={false} errorMessage="" onClose={vi.fn()} onSave={vi.fn()} />); // 新增代码+CustomProviderDialogTest：渲染打开状态弹窗；如果没有这行，字段断言没有输入。
    expect(markup).toContain("自定义提供商"); // 新增代码+CustomProviderDialogTest：确认标题可见；如果没有这行，用户不知道当前弹窗用途。
    expect(markup).toContain("Provider ID"); // 新增代码+CustomProviderDialogTest：确认 provider id 字段可见；如果没有这行，用户无法填写稳定 id。
    expect(markup).toContain("Base URL"); // 新增代码+CustomProviderDialogTest：确认 base URL 字段可见；如果没有这行，自定义 OpenAI-compatible endpoint 无法输入。
    expect(markup).toContain("API Key"); // 新增代码+CustomProviderDialogTest：确认 API key 字段可见；如果没有这行，用户无法连接 provider。
    expect(markup).toContain("模型"); // 新增代码+CustomProviderDialogTest：确认模型区域可见；如果没有这行，自定义 provider 没有模型列表。
    expect(markup).toContain("Headers"); // 新增代码+CustomProviderDialogTest：确认 header 区域可见；如果没有这行，gateway header 场景无法配置。
    expect(markup).toContain("保存"); // 新增代码+CustomProviderDialogTest：确认保存按钮可见；如果没有这行，用户无法提交表单。
  }); // 新增代码+CustomProviderDialogTest：初始 UI 字段测试结束；如果没有这行，测试块语法不完整。

  it("returns exact validation messages for unsafe input", () => { // 新增代码+CustomProviderDialogTest：测试校验文案；如果没有这段，错误提示可能偏离蓝图要求。
    expect(customProviderValidationError({ ...validState, providerId: "OpenAI" })).toBe("Provider ID 只能使用小写字母、数字和短横线"); // 新增代码+CustomProviderDialogTest：验证非法 id 文案；如果没有这行，大小写错误可能进入后端。
    expect(customProviderValidationError({ ...validState, providerId: "openai" })).toBe("Provider ID 已被系统保留"); // 新增代码+CustomProviderDialogTest：验证保留 id 文案；如果没有这行，内置 provider 可能被覆盖。
    expect(customProviderValidationError({ ...validState, baseUrl: "ftp://localhost/v1" })).toBe("Base URL 必须以 http:// 或 https:// 开头"); // 新增代码+CustomProviderDialogTest：验证 base URL 文案；如果没有这行，非 HTTP endpoint 可能保存。
    expect(customProviderValidationError({ ...validState, models: [{ id: "", displayName: "" }] })).toBe("至少填写一个模型"); // 新增代码+CustomProviderDialogTest：验证模型缺失文案；如果没有这行，空模型 provider 会进入模型页。
  }); // 新增代码+CustomProviderDialogTest：校验文案测试结束；如果没有这行，测试块语法不完整。

  it("builds a sanitized save payload and ignores empty headers", () => { // 新增代码+CustomProviderDialogTest：测试保存 payload；如果没有这段，前端可能把空 header 或错误字段发给后端。
    const payload = buildCustomProviderRequest(validState); // 新增代码+CustomProviderDialogTest：构造保存请求；如果没有这行，后续断言没有对象。
    expect(payload?.providerId).toBe("local-openai"); // 新增代码+CustomProviderDialogTest：确认 provider id 传入 payload；如果没有这行，后端无法定位自定义 provider。
    expect(payload?.fields.api_key).toBe("unit-test-secret-value"); // 新增代码+CustomProviderDialogTest：确认 API key 写入 write-only fields；如果没有这行，provider 无法连接。
    expect(payload?.headers).toEqual([{ key: "X-Test", value: "yes" }]); // 新增代码+CustomProviderDialogTest：确认空 header 被忽略；如果没有这行，后端会保存无意义 header。
    expect(payload?.models).toEqual([{ id: "local-model", displayName: "Local Model", visible: true }]); // 新增代码+CustomProviderDialogTest：确认模型 visible 默认 true；如果没有这行，保存后模型可能默认不可见。
  }); // 新增代码+CustomProviderDialogTest：保存 payload 测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+CustomProviderDialogTest：测试组结束；如果没有这行，describe 语法不完整。
