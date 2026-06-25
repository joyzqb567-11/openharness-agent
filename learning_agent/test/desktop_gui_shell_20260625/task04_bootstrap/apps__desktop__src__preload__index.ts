import { contextBridge } from "electron"; // 新增代码+DesktopPreload：引入 Electron 安全桥；如果没有这行，渲染进程无法通过受控方式拿到桌面 API。

contextBridge.exposeInMainWorld("openHarnessDesktop", { // 新增代码+DesktopPreload：向网页暴露最小桌面对象；如果没有这段，前端无法判断自己运行在 OpenHarness 桌面壳内。
  version: "0.1.0", // 新增代码+DesktopPreload：暴露桌面壳版本；如果没有这行，后续诊断无法快速确认 GUI 版本。
}); // 新增代码+DesktopPreload：预加载桥接对象结束；如果没有这行，contextBridge 调用语法不完整。
