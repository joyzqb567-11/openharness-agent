import { contextBridge, ipcRenderer } from "electron"; // 修改代码+DesktopBridgeConfig：引入 Electron 安全桥和 IPC 渲染端；如果没有 ipcRenderer，sandbox preload 无法从主进程读取 bridge 配置。
import { createDesktopBridgeConfig, type DesktopBridgeConfig } from "./bridgeConfig.js"; // 修改代码+DesktopBridgeConfig：引入 bridge 配置解析函数和类型；如果没有这行，preload 无法把后端地址和 token 注入给 React。

const bridgeFromMain = ipcRenderer.sendSync("openharness:get-bridge-config") as DesktopBridgeConfig | undefined; // 新增代码+DesktopBridgeConfig：从主进程同步读取 bridge 配置；如果没有这行，sandbox preload 只能依赖不稳定的 argv/env。
const bridgeConfig = bridgeFromMain ?? createDesktopBridgeConfig(process.argv, process.env); // 新增代码+DesktopBridgeConfig：主进程 IPC 失败时再使用 argv/env 兜底；如果没有这行，异常环境下没有后备连接方式。

contextBridge.exposeInMainWorld("openHarnessDesktop", { // 新增代码+DesktopPreload：向网页暴露最小桌面对象；如果没有这段，前端无法判断自己运行在 OpenHarness 桌面壳内。
  version: "0.1.0", // 新增代码+DesktopPreload：暴露桌面壳版本；如果没有这行，后续诊断无法快速确认 GUI 版本。
  bridge: bridgeConfig, // 修改代码+DesktopBridgeConfig：把最终 bridge 配置暴露给渲染层；如果没有这行，bootstrap、事件轮询和 composer 都无法访问后端。
}); // 新增代码+DesktopPreload：预加载桥接对象结束；如果没有这行，contextBridge 调用语法不完整。
