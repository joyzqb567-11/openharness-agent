import { createElement } from "react"; // 新增代码+RealModelObservabilityTest：导入 React 元素工厂；如果没有这一行，测试无法在无浏览器环境构造组件。
import { renderToStaticMarkup } from "react-dom/server"; // 新增代码+RealModelObservabilityTest：导入静态渲染工具；如果没有这一行，状态条是否肉眼可见无法被自动测试锁定。
import { describe, expect, it } from "vitest"; // 新增代码+RealModelObservabilityTest：导入 Vitest 测试工具；如果没有这一行，本文件不会被桌面测试运行器识别。
import { Composer } from "../src/components/Composer"; // 新增代码+RealModelObservabilityTest：导入底部输入框组件；如果没有这一行，测试无法确认 Codex 式输入区显示模型调用状态。
import { ModelCallStatus, latestModelCallStatus, modelCallStatusLabel, type ModelCallStatusView } from "../src/components/ModelCallStatus"; // 新增代码+RealModelObservabilityTest：导入待实现的模型状态工具；如果没有这一行，测试无法先红后绿地约束新模块。
import { reduceGuiEventToThreadActions } from "../src/state/eventReducer"; // 新增代码+RealModelObservabilityTest：导入事件 reducer；如果没有这一行，测试无法确认模型状态事件不会污染主消息流。
import type { StatusEvent } from "../src/state/statusStore"; // 新增代码+RealModelObservabilityTest：导入状态事件类型；如果没有这一行，测试夹具容易偏离真实轮询事件形状。

function statusEvent(eventType: string, sequence: number, payload: Record<string, unknown>): StatusEvent { // 新增代码+RealModelObservabilityTest：函数段开始，创建最小状态事件夹具；如果没有这段，每个测试都会重复无关字段。
  return { sequence, event_type: eventType, session_id: "session_test", run_id: "run_test", turn_id: "turn_test", payload }; // 新增代码+RealModelObservabilityTest：返回符合前端合同的事件；如果没有这一行，helper 没有实际输出。
} // 新增代码+RealModelObservabilityTest：函数段结束，statusEvent 到此结束；如果没有这一行，函数语法不完整。

const fallbackStatus: ModelCallStatusView = { // 新增代码+RealModelObservabilityTest：定义 HTTPS fallback 状态夹具；如果没有这段，多个断言会重复构造相同输入。
  eventType: "model_call_status", // 新增代码+RealModelObservabilityTest：保存来源事件类型；如果没有这一行，组件无法保留诊断来源。
  phase: "https_fallback", // 新增代码+RealModelObservabilityTest：保存慢路径阶段；如果没有这一行，文案 helper 无法输出降级提示。
  message: "falling back to HTTPS", // 新增代码+RealModelObservabilityTest：保存原始诊断消息；如果没有这一行，title 无法保留后端细节。
  modelId: "gpt-5.5", // 新增代码+RealModelObservabilityTest：保存模型 id；如果没有这一行，用户不知道慢的是哪个模型。
  providerId: "openai", // 新增代码+RealModelObservabilityTest：保存 provider id；如果没有这一行，多 provider 场景无法定位来源。
  elapsedMs: 3200, // 新增代码+RealModelObservabilityTest：保存阶段耗时；如果没有这一行，用户无法看到慢调用证据。
}; // 新增代码+RealModelObservabilityTest：fallback 状态夹具结束；如果没有这一行，对象语法不完整。

describe("ModelCallStatus", () => { // 新增代码+RealModelObservabilityTest：测试组开始，覆盖真实模型调用状态可视化；如果没有这段，慢调用 UI 容易回归成黑盒。
  it("maps known phases to compact Chinese labels", () => { // 新增代码+RealModelObservabilityTest：测试阶段到中文短文案的映射；如果没有这段，UI 可能显示英文机器码。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "connecting" })).toBe("正在连接 GPT-5.5"); // 新增代码+RealModelObservabilityTest：确认连接阶段显示模型名；如果没有这一行，用户不知道正在连接哪个模型。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "websocket_timeout" })).toBe("WebSocket 超时，正在切换 HTTPS"); // 新增代码+RealModelObservabilityTest：确认 WebSocket 超时有明确说明；如果没有这一行，慢等待会像界面卡死。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "first_delta" })).toBe("已收到首个响应"); // 新增代码+RealModelObservabilityTest：确认首响应阶段有正反馈；如果没有这一行，用户不知道真实模型已经开始返回。
    expect(modelCallStatusLabel({ ...fallbackStatus, phase: "failed", message: "当前模型不可用" })).toBe("调用失败：当前模型不可用"); // 新增代码+RealModelObservabilityTest：确认失败原因进入短文案；如果没有这一行，账号不支持模型会被隐藏。
  }); // 新增代码+RealModelObservabilityTest：阶段文案测试结束；如果没有这一行，测试块语法不完整。

  it("selects the latest model call status from the event stream", () => { // 新增代码+RealModelObservabilityTest：测试从状态流提取最新模型阶段；如果没有这段，底部可能显示过期状态。
    const status = latestModelCallStatus([ // 新增代码+RealModelObservabilityTest：创建包含多个模型阶段的事件列表；如果没有这一行，后续断言没有输入。
      statusEvent("model_call_started", 1, { phase: "connecting", model_id: "gpt-5.5", provider_id: "openai", elapsed_ms: 0 }), // 新增代码+RealModelObservabilityTest：放入连接开始事件；如果没有这一行，测试覆盖不到初始阶段。
      statusEvent("message_delta", 2, { text_delta: "hi" }), // 新增代码+RealModelObservabilityTest：放入普通文本事件；如果没有这一行，测试无法证明 helper 会跳过非模型状态。
      statusEvent("model_call_status", 3, { phase: "https_fallback", message: "falling back", model_id: "gpt-5.5", provider_id: "openai", elapsed_ms: 3200 }), // 新增代码+RealModelObservabilityTest：放入最新 fallback 事件；如果没有这一行，测试没有目标状态。
    ]); // 新增代码+RealModelObservabilityTest：事件列表结束；如果没有这一行，数组语法不完整。
    expect(status?.phase).toBe("https_fallback"); // 新增代码+RealModelObservabilityTest：确认最新阶段被选中；如果没有这一行，helper 可能返回旧阶段。
    expect(status?.elapsedMs).toBe(3200); // 新增代码+RealModelObservabilityTest：确认耗时被保留；如果没有这一行，状态条可能丢失延迟证据。
  }); // 新增代码+RealModelObservabilityTest：最新状态测试结束；如果没有这一行，测试块语法不完整。

  it("renders the compact status in Composer without treating it as a message event", () => { // 新增代码+RealModelObservabilityTest：测试 Composer 集成和 reducer 忽略行为；如果没有这段，模型状态可能污染主聊天内容。
    const markup = renderToStaticMarkup(createElement(Composer, { modelCallStatus: fallbackStatus })); // 新增代码+RealModelObservabilityTest：静态渲染带状态的 Composer；如果没有这一行，断言没有真实 HTML 输入。
    const reduction = reduceGuiEventToThreadActions(statusEvent("model_call_status", 7, { phase: "websocket_timeout", message: "timeout", model_id: "gpt-5.5" })); // 新增代码+RealModelObservabilityTest：把模型状态交给消息 reducer；如果没有这一行，无法证明它不会变成聊天消息。
    expect(markup).toContain("composer-model-status-slot"); // 新增代码+RealModelObservabilityTest：确认 Composer 内有固定状态槽；如果没有这一行，状态条可能挤压底部按钮。
    expect(markup).toContain("WebSocket 超时，正在切换 HTTPS"); // 新增代码+RealModelObservabilityTest：确认用户可见 fallback 文案；如果没有这一行，慢路径提示可能不可见。
    expect(reduction.actions).toHaveLength(0); // 新增代码+RealModelObservabilityTest：确认模型状态不产生消息动作；如果没有这一行，右侧诊断事件会污染主线程。
    expect(reduction.diagnostics).toHaveLength(0); // 新增代码+RealModelObservabilityTest：确认模型状态不是 unsupported；如果没有这一行，诊断面板会把正常事件误报成未知。
  }); // 新增代码+RealModelObservabilityTest：Composer 集成测试结束；如果没有这一行，测试块语法不完整。
}); // 新增代码+RealModelObservabilityTest：测试组结束；如果没有这一行，describe 块语法不完整。
