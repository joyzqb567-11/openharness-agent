import React from "react"; // 新增代码+DesktopRenderer：引入 React；如果没有这行，TSX 渲染入口无法创建组件树。
import ReactDOM from "react-dom/client"; // 新增代码+DesktopRenderer：引入 React 18 根节点 API；如果没有这行，页面无法挂载到 DOM。
import { App } from "./App"; // 新增代码+DesktopRenderer：引入桌面应用根组件；如果没有这行，渲染入口没有可显示内容。
import "../styles/theme.css"; // 新增代码+DesktopRenderer：加载全局主题样式；如果没有这行，字体、颜色和背景会退回浏览器默认值。
import "../styles/layout.css"; // 新增代码+DesktopRenderer：加载布局样式；如果没有这行，侧栏、线程和输入框会堆成普通文档流。
import "../styles/runtime-panels.css"; // 新增代码+DesktopRuntimePanelsStyle：加载浏览器和 Computer Use 成熟面板样式；如果没有这行，V2 面板会退回普通文档流。
import "../styles/settings-diagnostics.css"; // ????+DesktopSettingsDiagnosticsStyle????????????????????Task 11 ????????????
import "../styles/settings-dialog.css"; // 新增代码+ProviderSettingsShellStyle：加载 Provider Settings 弹窗样式；如果没有这行，真实 Electron 中设置弹窗会退回未排版的文档流。

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render( // 新增代码+DesktopRenderer：把 React 应用挂载到 index.html 的 root；如果没有这段，窗口会是空白。
  <React.StrictMode> {/* 新增代码+DesktopRenderer：启用 React 严格模式；如果没有这行，开发时更难发现副作用问题。 */}
    <App /> {/* 新增代码+DesktopRenderer：渲染桌面应用根组件；如果没有这行，页面没有业务 UI。 */}
  </React.StrictMode>, // 新增代码+DesktopRenderer：严格模式包裹结束；如果没有这行，React 节点结构不完整。
); // 新增代码+DesktopRenderer：React 渲染调用结束；如果没有这行，TypeScript 语法不完整。
