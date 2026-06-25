import { Composer } from "./Composer"; // 新增代码+DesktopShellLayout：引入底部输入组件；如果没有这行，主界面没有用户输入入口。
import { Sidebar } from "./Sidebar"; // 新增代码+DesktopShellLayout：引入左侧导航组件；如果没有这行，项目和功能入口会散落在页面里。
import { ThreadView } from "./ThreadView"; // 新增代码+DesktopShellLayout：引入线程显示组件；如果没有这行，消息内容没有独立渲染区域。
import { useMemo, useReducer } from "react"; // 新增代码+DesktopGUILifecycleUI：引入 React 状态工具；如果没有这行，AppShell 无法维护消息和运行状态。
import { createGuiClient } from "../api/guiClient"; // 新增代码+DesktopGUILifecycleUI：引入 GUI bridge client；如果没有这行，composer 无法调用后端 lifecycle endpoint。
import { initialThreadState, threadReducer } from "../state/threadStore"; // 新增代码+DesktopGUILifecycleUI：引入线程初始状态和 reducer；如果没有这行，消息追加和 turn 状态会散落在组件里。

type DesktopBridgeConfig = { // 新增代码+DesktopGUILifecycleUI：定义 preload 暴露的 bridge 配置；如果没有这段，window.openHarnessDesktop 的结构不清楚。
  baseUrl?: string; // 新增代码+DesktopGUILifecycleUI：保存 bridge 地址；如果没有这行，前端不知道请求哪个本地端口。
  token?: string; // 新增代码+DesktopGUILifecycleUI：保存 bridge token；如果没有这行，安全端点会拒绝请求。
}; // 新增代码+DesktopGUILifecycleUI：bridge 配置类型结束；如果没有这行，TypeScript 类型语法不完整。

declare global { // 新增代码+DesktopGUILifecycleUI：声明桌面 preload 全局对象；如果没有这段，TypeScript 不认识 window.openHarnessDesktop。
  interface Window { // 新增代码+DesktopGUILifecycleUI：扩展浏览器 Window 类型；如果没有这行，全局对象字段无法类型化。
    openHarnessDesktop?: { // 新增代码+DesktopGUILifecycleUI：声明 OpenHarness 桌面对象；如果没有这行，访问 preload 对象会报类型错误。
      version: string; // 新增代码+DesktopGUILifecycleUI：保存桌面壳版本；如果没有这行，诊断信息缺少版本。
      bridge?: DesktopBridgeConfig; // 新增代码+DesktopGUILifecycleUI：保存可选 bridge 配置；如果没有这行，前端无法读取 token/baseUrl。
    }; // 新增代码+DesktopGUILifecycleUI：openHarnessDesktop 对象结束；如果没有这行，TypeScript 接口语法不完整。
  } // 新增代码+DesktopGUILifecycleUI：Window 接口结束；如果没有这行，global 声明语法不完整。
} // 新增代码+DesktopGUILifecycleUI：全局声明结束；如果没有这行，TypeScript 声明块不完整。

export function AppShell(): JSX.Element { // 新增代码+DesktopShellLayout：函数段开始，组织桌面 GUI 主壳；如果没有这段，各组件无法组合成 Codex 风格窗口。
  const [threadState, dispatchThread] = useReducer(threadReducer, initialThreadState); // 新增代码+DesktopGUILifecycleUI：创建线程状态；如果没有这行，用户消息和助手占位无法进入 UI。
  const bridgeConfig = window.openHarnessDesktop?.bridge; // 新增代码+DesktopGUILifecycleUI：读取 preload 注入的 bridge 配置；如果没有这行，GUI 不知道后端地址和 token。
  const guiClient = useMemo(() => { // 新增代码+DesktopGUILifecycleUI：缓存 GUI client；如果没有这段，每次渲染都会创建新 client。
    if (!bridgeConfig?.baseUrl || !bridgeConfig.token) { // 新增代码+DesktopGUILifecycleUI：检查 bridge 配置是否完整；如果没有这行，空 token 请求会反复失败。
      return null; // 新增代码+DesktopGUILifecycleUI：配置缺失时不创建 client；如果没有这行，后续调用会拿到无效 client。
    } // 新增代码+DesktopGUILifecycleUI：配置检查结束；如果没有这行，条件块语法不完整。
    return createGuiClient(bridgeConfig.baseUrl, bridgeConfig.token); // 新增代码+DesktopGUILifecycleUI：创建带 token 的 client；如果没有这行，composer 无法访问 bridge。
  }, [bridgeConfig?.baseUrl, bridgeConfig?.token]); // 新增代码+DesktopGUILifecycleUI：按 bridge 配置缓存 client；如果没有这行，useMemo 依赖不完整。

  async function handleSubmit(prompt: string): Promise<void> { // 新增代码+DesktopGUILifecycleUI：函数段开始，处理用户提交 prompt；如果没有这段，Composer 输入不会进入线程或后端。
    const userMessageId = `local_user_${Date.now()}`; // 新增代码+DesktopGUILifecycleUI：生成本地用户消息 id；如果没有这行，React 列表 key 不稳定。
    dispatchThread({ type: "message_added", message: { id: userMessageId, role: "user", text: prompt, status: "completed" } }); // 新增代码+DesktopGUILifecycleUI：立即显示用户消息；如果没有这行，用户点击发送后界面没有反馈。
    if (guiClient === null) { // 新增代码+DesktopGUILifecycleUI：处理 bridge 未配置；如果没有这行，用户只会看到网络失败。
      dispatchThread({ type: "message_added", message: { id: `local_system_${Date.now()}`, role: "system", text: "GUI bridge 尚未注入 baseUrl/token，请通过桌面启动脚本打开应用。", status: "failed" } }); // 新增代码+DesktopGUILifecycleUI：显示配置缺失提示；如果没有这行，用户不知道该启动后端 bridge。
      return; // 新增代码+DesktopGUILifecycleUI：配置缺失时停止提交；如果没有这行，会继续访问 null client。
    } // 新增代码+DesktopGUILifecycleUI：bridge 配置缺失分支结束；如果没有这行，条件块语法不完整。
    try { // 新增代码+DesktopGUILifecycleUI：捕获 bridge 提交失败；如果没有这行，网络错误会打断 React 事件。
      const response = await guiClient.sendMessage(prompt, "default"); // 新增代码+DesktopGUILifecycleUI：向后端提交 prompt；如果没有这行，GUI 不会创建真实 turn。
      dispatchThread({ type: "message_added", message: { id: `assistant_${response.turn_id}`, role: "assistant", text: response.answer, turnId: response.turn_id, status: response.status } }); // 新增代码+DesktopGUILifecycleUI：显示助手占位消息；如果没有这行，运行中状态没有消息容器。
      dispatchThread({ type: "turn_started", turnId: response.turn_id, status: response.status }); // 新增代码+DesktopGUILifecycleUI：记录 active turn；如果没有这行，composer 无法禁用重复发送。
    } catch (error) { // 新增代码+DesktopGUILifecycleUI：处理提交异常；如果没有这行，busy/断线会变成未捕获错误。
      dispatchThread({ type: "message_added", message: { id: `local_error_${Date.now()}`, role: "system", text: `GUI bridge 提交失败：${String(error)}`, status: "failed" } }); // 新增代码+DesktopGUILifecycleUI：把错误显示到线程；如果没有这行，用户看不到失败原因。
      dispatchThread({ type: "turn_finished", status: "failed", errorMessage: String(error) }); // 新增代码+DesktopGUILifecycleUI：退出运行态；如果没有这行，发送按钮可能一直禁用。
    } // 新增代码+DesktopGUILifecycleUI：异常处理结束；如果没有这行，try/catch 语法不完整。
  } // 新增代码+DesktopGUILifecycleUI：函数段结束，handleSubmit 到此结束；如果没有边界说明，初学者不易看出提交流程范围。

  return ( // 新增代码+DesktopShellLayout：返回主界面结构；如果没有这行，组件不会输出任何 UI。
    <main className="app-shell"> {/* 新增代码+DesktopShellLayout：定义全窗口网格容器；如果没有这行，侧栏和线程区无法稳定并排。 */}
      <Sidebar /> {/* 新增代码+DesktopShellLayout：渲染项目导航侧栏；如果没有这行，用户无法看到 quick chat/search/plugins/settings 等入口。 */}
      <section className="thread-panel" aria-label="当前对话"> {/* 新增代码+DesktopShellLayout：定义当前对话主区域；如果没有这行，读屏器和布局都缺少对话容器。 */}
        <header className="thread-header"> {/* 新增代码+DesktopShellLayout：定义顶部会话栏；如果没有这行，用户无法确认当前会话标题。 */}
          <div className="thread-title">快速对话</div> {/* 新增代码+DesktopShellLayout：显示当前会话名；如果没有这行，主面板上下文不清楚。 */}
          <div className="thread-subtitle">OpenHarness Desktop Shell</div> {/* 新增代码+DesktopShellLayout：显示当前壳版本语境；如果没有这行，用户难以区分 CLI 和桌面壳。 */}
        </header> {/* 新增代码+DesktopShellLayout：顶部会话栏结束；如果没有这行，JSX 结构不完整。 */}
        <ThreadView messages={threadState.messages.length > 0 ? threadState.messages : undefined} /> {/* 新增代码+DesktopGUILifecycleUI：把 reducer 消息传给线程视图；如果没有这行，用户提交后主面板不会变化。 */}
        <Composer isRunning={threadState.isRunning} onSubmit={(prompt) => { void handleSubmit(prompt); }} /> {/* 新增代码+DesktopGUILifecycleUI：把运行态和提交回调交给 composer；如果没有这行，输入区无法触发后端生命周期。 */}
      </section> {/* 新增代码+DesktopShellLayout：当前对话主区域结束；如果没有这行，JSX 结构不完整。 */}
    </main> /* 新增代码+DesktopShellLayout：全窗口网格容器结束；如果没有这行，JSX 结构不完整。 */
  ); // 新增代码+DesktopShellLayout：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopShellLayout：函数段结束，AppShell 到此结束；如果没有这个边界，用户不容易看出主壳组合范围。
