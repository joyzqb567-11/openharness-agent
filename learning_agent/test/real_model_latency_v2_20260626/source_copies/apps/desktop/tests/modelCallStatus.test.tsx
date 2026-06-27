import { createElement } from "react"; // 新增代码+ModelCallStatusTest：导入 React 元素工厂；如果没有这行，.tsx 测试不能用 createElement 做静态渲染。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+ModelCallStatusTest：导入服务端静态渲染；如果没有这行，状态条文案不能在无浏览器环境断言。
import { describe, expect, it } from "vitest"; // 新增代码+ModelCallStatusTest：导入 Vitest 工具；如果没有这行，模型调用状态组件没有测试入口。
import { Composer } from "../src/components/Composer"; // 新增代码+ModelCallStatusTest：导入底部输入框；如果没有这行，测试无法确认状态条挂到 Codex 式 Composer 里。
import { ModelCallStatus, modelCallStatusLabel } from "../src/components/ModelCallStatus"; // 新增代码+ModelCallStatusTest：导入状态组件和文案 helper；如果没有这行，测试无法锁定慢调用可见文案。
import type { ModelCallStatusView } from "../src/components/ModelCallStatus"; // 新增代码+ModelCallStatusTest：导入状态 view 类型；如果没有这行，fixture 字段含义不清楚。

const fallbackStatus: ModelCallStatusView = { // 新增代码+ModelCallStatusTest：定义 HTTPS fallback fixture；如果没有这段，多个断言会重复构造状态。
  eventType: "model_call_status", // 新增代码+ModelCallStatusTest：保存来源事件类型；如果没有这行，组件无法区分阶段来源。
  phase: "https_fallback", // 新增代码+ModelCallStatusTest：保存 fallback 阶段；如果没有这行，文案 helper 无法输出慢路径提示。
  message: "falling back to HTTPS", // 新增代码+ModelCallStatusTest：保存后端原始消息；如果没有这行，title 无法保留诊断细节。
  modelId: "gpt-5.5", // 新增代码+ModelCallStatusTest：保存模型 id；如果没有这行，连接文案无法显示模型。
  providerId: "openai", // 新增代码+ModelCallStatusTest：保存 provider id；如果没有这行，后续状态诊断无法知道来源。
  elapsedMs: 3200, // 新增代码+ModelCallStatusTest：保存耗时；如果没有这行，慢调用状态缺少时间证据。
}; // 新增代码+ModelCallStatusTest：fallback fixture 结束；如果没有这行，对象语法不完整。

describe("ModelCallStatus", () => { // 新增代码+ModelCallStatusTest：测试组开始，覆盖真实模型调用状态条；如果没有这段，用户只能凭肉眼发现慢调用黑盒回归。
  it("maps known phases to compact Chinese labels", () => { // 新增代码+ModelCallStatusTest：测试阶段文案映射；如果没有这段，连接、fallback、首 token 和失败状态可能显示机器码。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "connecting" })).toBe("正在连接 GPT-5.5"); // 新增代码+ModelCallStatusTest：确认连接阶段显示模型名；如果没有这行，用户不知道正在连哪个模型。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "websocket_timeout" })).toBe("WebSocket 超时，正在切换 HTTPS"); // 新增代码+ModelCallStatusTest：确认 WebSocket 超时有明确 fallback 提示；如果没有这行，慢 120 秒会像卡死。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "first_delta" })).toBe("已收到首个响应"); // 新增代码+ModelCallStatusTest：确认首个响应有正反馈；如果没有这行，用户不知道模型已经开始输出。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "cancelled" })).toBe("已取消"); // 新增代码+ModelCallStatusTest：确认取消终态清晰；如果没有这行，取消后可能仍像运行中。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "failed", message: "当前模型不可用" })).toBe("调用失败：当前模型不可用"); // 新增代码+ModelCallStatusTest：确认失败原因进入短文案；如果没有这行，模型不支持会被隐藏。
  }); // 新增代码+ModelCallStatusTest：阶段文案测试结束；如果没有这行，测试块语法不完整。

  it("renders a stable compact status line", () => { // 新增代码+ModelCallStatusTest：测试组件静态渲染；如果没有这段，CSS 类和文案可能被重构弄丢。
    const markup = renderToStaticMarkup(createElement(ModelCallStatus, { status: fallbackStatus, compact: true })); // 新增代码+ModelCallStatusTest：渲染紧凑状态条；如果没有这行，断言没有 HTML 输入。
    expect(markup).toContain("model-call-status"); // 新增代码+ModelCallStatusTest：确认组件根类存在；如果没有这行，CSS 无法稳定命中。
    expect(markup).toContain("WebSocket 超时，正在切换 HTTPS"); // 新增代码+ModelCallStatusTest：确认 fallback 文案可见；如果没有这行，慢路径提示可能不可见。
    expect(markup).toContain("3.2s"); // 新增代码+ModelCallStatusTest：确认耗时被压缩显示；如果没有这行，用户缺少延迟证据。
  }); // 新增代码+ModelCallStatusTest：组件静态渲染测试结束；如果没有这行，测试块语法不完整。

  it("keeps Composer model call status in a fixed slot above the toolbar", () => { // 新增代码+ModelCallStatusTest：测试 Composer 集成位置；如果没有这段，状态条可能挤压底部按钮或消失。
    const markup = renderToStaticMarkup(createElement(Composer, { modelCallStatus: fallbackStatus, modelOptions: [{ id: "gpt-5.5", label: "GPT-5.5", providerId: "openai", providerName: "OpenAI", supportsTools: true, supportsVision: true, recentFailure: null }], selectedModelId: "gpt-5.5" })); // 修改代码+ModelFailureStateTest：渲染带状态和模型的 Composer；如果没有这行，无法证明底部真实可见，也无法覆盖最新模型选项形状。
    expect(markup).toContain("composer-model-status-slot"); // 新增代码+ModelCallStatusTest：确认固定状态槽存在；如果没有这行，状态条可能改变输入框高度。
    expect(markup).toContain("WebSocket 超时，正在切换 HTTPS"); // 新增代码+ModelCallStatusTest：确认状态文案在 Composer 内可见；如果没有这行，用户仍需要去右栏猜慢在哪里。
    expect(markup).toContain("data-testid=\"composer-model-select\""); // 新增代码+ModelCallStatusTest：确认模型菜单仍保留；如果没有这行，状态条可能破坏 Codex 底部控件。
  }); // 新增代码+ModelCallStatusTest：Composer 集成测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+ModelCallStatusTest：测试组结束；如果没有这行，describe 块语法不完整。
