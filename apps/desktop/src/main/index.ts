import { app, BrowserWindow, ipcMain } from "electron"; // 修改代码+DesktopBridgeConfig：引入 Electron 应用、窗口对象和 IPC 主进程；如果没有 ipcMain，preload 无法在 sandbox 下可靠读取 bridge 配置。
import path from "node:path"; // 新增代码+DesktopMain：引入路径工具；如果没有这行，Windows 和 macOS/Linux 的 preload 路径会难以兼容。
import { fileURLToPath } from "node:url"; // 新增代码+DesktopMain：把 ESM 文件 URL 转成本地路径；如果没有这行，主进程无法定位 dist 目录。

const currentFile = fileURLToPath(import.meta.url); // 新增代码+DesktopMain：得到当前主进程文件路径；如果没有这行，后续无法计算 preload 和 renderer 的位置。
const currentDir = path.dirname(currentFile); // 新增代码+DesktopMain：得到当前主进程目录；如果没有这行，loadFile 会找不到打包后的 index.html。
const bridgeBaseUrl = process.env.OPENHARNESS_GUI_BRIDGE_URL ?? "http://127.0.0.1:8776"; // 新增代码+DesktopBridgeConfig：读取 GUI bridge 地址并给出本地默认值；如果没有这行，preload 没有稳定后端地址可注入。
const bridgeToken = process.env.OPENHARNESS_GUI_BRIDGE_TOKEN ?? "openharness-desktop-dev-token"; // 新增代码+DesktopBridgeConfig：读取 GUI bridge token 并给出开发默认值；如果没有这行，后端和 GUI 默认 token 会对不上。
const bridgeArguments = [ // 新增代码+DesktopBridgeConfig：准备传给 preload 的 Electron 附加参数；如果没有这段，sandbox preload 无法安全得到主进程环境配置。
  `--openharness-gui-bridge-url=${encodeURIComponent(bridgeBaseUrl)}`, // 新增代码+DesktopBridgeConfig：传递编码后的 bridge 地址；如果没有这行，React 无法知道后端 baseUrl。
  `--openharness-gui-bridge-token=${encodeURIComponent(bridgeToken)}`, // 新增代码+DesktopBridgeConfig：传递编码后的 bridge token；如果没有这行，React 请求会缺少认证令牌。
]; // 新增代码+DesktopBridgeConfig：附加参数列表结束；如果没有这行，数组语法不完整。
const bridgeHash = new URLSearchParams({ openharnessBridgeUrl: bridgeBaseUrl, openharnessBridgeToken: bridgeToken }).toString(); // 新增代码+DesktopBridgeConfig：把 bridge 配置编码进窗口 URL hash 作为 preload 失败兜底；如果没有这行，preload 不可用时 React 没有任何配置来源。
ipcMain.on("openharness:get-bridge-config", (event) => { // 新增代码+DesktopBridgeConfig：注册同步 IPC 读取 bridge 配置；如果没有这段，sandbox preload 在拿不到 argv/env 时无法连接后端。
  event.returnValue = { baseUrl: bridgeBaseUrl, token: bridgeToken }; // 新增代码+DesktopBridgeConfig：把主进程掌握的 baseUrl/token 返回给 preload；如果没有这行，React 仍会缺少认证配置。
}); // 新增代码+DesktopBridgeConfig：IPC 配置读取监听结束；如果没有这行，事件注册语法不完整。

function createWindow(): void { // 新增代码+DesktopMain：函数段开始，创建 OpenHarness 桌面窗口；如果没有这段，Electron 启动后没有可见 GUI。
  const window = new BrowserWindow({ // 新增代码+DesktopMain：创建一个真实桌面窗口；如果没有这行，用户不会看到 Codex 风格外壳。
    width: 1280, // 新增代码+DesktopMain：设置默认窗口宽度；如果没有这行，窗口可能太窄导致三栏布局挤压。
    height: 820, // 新增代码+DesktopMain：设置默认窗口高度；如果没有这行，首屏内容可能显示不完整。
    minWidth: 980, // 新增代码+DesktopMain：设置最小宽度；如果没有这行，用户缩小时文字和控件容易重叠。
    minHeight: 640, // 新增代码+DesktopMain：设置最小高度；如果没有这行，composer 和线程区容易被压没。
    title: "OpenHarness Desktop", // 新增代码+DesktopMain：设置窗口标题；如果没有这行，系统任务栏里很难识别这个应用。
    webPreferences: { // 新增代码+DesktopMain：配置渲染进程安全选项；如果没有这段，桌面壳的安全边界不清晰。
      preload: path.join(currentDir, "../preload/index.js"), // 新增代码+DesktopMain：加载预加载脚本；如果没有这行，主进程无法安全暴露有限 API。
      contextIsolation: true, // 新增代码+DesktopMain：隔离网页上下文和 preload 上下文；如果没有这行，页面脚本更容易碰到敏感对象。
      nodeIntegration: false, // 新增代码+DesktopMain：禁止渲染页直接使用 Node；如果没有这行，前端页面可能直接读写本地文件。
      sandbox: false, // 修改代码+DesktopBridgeConfig：关闭 Electron sandbox 以允许 preload 稳定使用 IPC 读取 bridge 配置；如果没有这行，当前 Windows Electron 环境下 GUI 会无法注入 baseUrl/token。
      additionalArguments: bridgeArguments, // 新增代码+DesktopBridgeConfig：把 bridge 地址和 token 传给 preload；如果没有这行，渲染层无法加载真实后端数据。
    }, // 新增代码+DesktopMain：webPreferences 配置结束；如果没有这行，窗口配置语法不完整。
  }); // 新增代码+DesktopMain：窗口对象创建结束；如果没有这行，BrowserWindow 构造调用不完整。

  const devServerUrl = process.env.OPENHARNESS_DESKTOP_DEV_URL; // 新增代码+DesktopMain：读取开发模式渲染地址；如果没有这行，开发时 Electron 不能连接 Vite 热更新页面。
  if (devServerUrl) { // 新增代码+DesktopMain：判断是否处于开发模式；如果没有这行，开发和生产加载路径会混在一起。
    void window.loadURL(`${devServerUrl}#${bridgeHash}`); // 修改代码+DesktopBridgeConfig：开发模式加载 Vite 页面并携带本地 hash 配置；如果没有这行，preload 失败时 GUI 无法连接后端。
    return; // 新增代码+DesktopMain：开发加载后提前返回；如果没有这行，窗口会继续尝试加载生产文件并产生冲突。
  } // 新增代码+DesktopMain：开发模式分支结束；如果没有这行，TypeScript 语法不完整。

  void window.loadFile(path.join(currentDir, "../renderer/index.html"), { hash: bridgeHash }); // 修改代码+DesktopBridgeConfig：生产模式加载构建产物并携带本地 hash 配置；如果没有这行，打包窗口可能无法连接 bridge。
} // 新增代码+DesktopMain：函数段结束，createWindow 到此结束；如果没有这个边界，用户不容易看出窗口创建逻辑范围。

void app.whenReady().then(createWindow); // 新增代码+DesktopMain：Electron 准备好后创建窗口；如果没有这行，应用启动后不会显示窗口。

app.on("window-all-closed", () => { // 新增代码+DesktopMain：监听所有窗口关闭事件；如果没有这段，Windows 关闭窗口后进程可能残留。
  if (process.platform !== "darwin") { // 新增代码+DesktopMain：保留 macOS 常见行为；如果没有这行，macOS 上关闭窗口会直接退出应用。
    app.quit(); // 新增代码+DesktopMain：非 macOS 平台关闭应用；如果没有这行，Windows 上关闭窗口后后台进程会继续占用资源。
  } // 新增代码+DesktopMain：平台判断结束；如果没有这行，条件块语法不完整。
}); // 新增代码+DesktopMain：窗口关闭监听结束；如果没有这行，事件注册语法不完整。
