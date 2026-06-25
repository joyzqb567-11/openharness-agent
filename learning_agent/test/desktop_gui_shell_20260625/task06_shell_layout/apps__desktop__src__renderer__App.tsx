import { AppShell } from "../components/AppShell"; // 新增代码+DesktopApp：引入完整桌面壳组件；如果没有这行，根组件只能保留临时占位布局。

export function App(): JSX.Element { // 新增代码+DesktopApp：函数段开始，提供 React 应用根组件；如果没有这段，渲染入口没有可显示的 UI。
  return <AppShell />; // 新增代码+DesktopApp：渲染 Codex 风格桌面主壳；如果没有这行，窗口不会显示侧栏、线程和 composer。
} // 新增代码+DesktopApp：函数段结束，App 到此结束；如果没有这个边界，用户不容易看出根组件范围。
