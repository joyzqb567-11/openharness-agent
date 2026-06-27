import { app, BrowserWindow, ipcMain, shell } from "electron"; // 修改代码+OAuthExternalBrowser：引入 shell 用系统浏览器打开 OAuth 外链；如果没有 shell，OpenAI 登录会卡在 Electron 自己的无登录态窗口。
import path from "node:path"; // 新增代码+DesktopMain：引入路径工具；如果没有这行，Windows 和 macOS/Linux 的 preload 路径会难以兼容。
import { fileURLToPath } from "node:url"; // 新增代码+DesktopMain：把 ESM 文件 URL 转成本地路径；如果没有这行，主进程无法定位 dist 目录。
import { shouldOpenExternalDesktopUrl } from "./externalLinks.js"; // 新增代码+OAuthExternalBrowser：导入外链判断 helper；如果没有这行，主进程和测试会各写一套规则。

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
  const devServerUrl = process.env.OPENHARNESS_DESKTOP_DEV_URL; // 修改代码+OAuthExternalBrowser：提前读取开发模式渲染地址；如果没有这行，外链判断不知道哪个 origin 是桌面壳自己。
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

  window.webContents.setWindowOpenHandler(({ url }) => { // 新增代码+OAuthExternalBrowser：拦截 target=_blank 新窗口；如果没有这段，OpenAI OAuth 会开在 Electron 内部窗口而不是系统浏览器。
    if (shouldOpenExternalDesktopUrl(url, devServerUrl)) { // 新增代码+OAuthExternalBrowser：判断目标是否为外部网页；如果没有这行，无法只拦截 OAuth/网页外链。
      void shell.openExternal(url); // 新增代码+OAuthExternalBrowser：用系统默认浏览器打开外链；如果没有这行，用户无法复用 Edge/Chrome 的 ChatGPT 登录态。
      return { action: "deny" }; // 新增代码+OAuthExternalBrowser：阻止 Electron 创建内部窗口；如果没有这行，仍会出现无登录态 OpenAI 弹窗。
    } // 新增代码+OAuthExternalBrowser：外链处理分支结束；如果没有这行，条件块语法不完整。
    return { action: "allow" }; // 新增代码+OAuthExternalBrowser：非外链保持 Electron 默认行为；如果没有这行，必要的内部新窗口会被全部拦截。
  }); // 新增代码+OAuthExternalBrowser：window.open 拦截器结束；如果没有这行，回调注册语法不完整。
  window.webContents.on("will-navigate", (event, url) => { // 新增代码+OAuthExternalBrowser：拦截当前窗口直接跳转外部网页；如果没有这段，普通链接可能把桌面壳导航到 OpenAI。
    if (shouldOpenExternalDesktopUrl(url, devServerUrl)) { // 新增代码+OAuthExternalBrowser：判断导航目标是否为外部网页；如果没有这行，无法保护主窗口。
      event.preventDefault(); // 新增代码+OAuthExternalBrowser：阻止桌面主窗口离开本应用；如果没有这行，OpenHarness UI 可能被授权页替换。
      void shell.openExternal(url); // 新增代码+OAuthExternalBrowser：把外部网页交给系统浏览器；如果没有这行，用户仍无法复用系统浏览器登录态。
    } // 新增代码+OAuthExternalBrowser：外部导航分支结束；如果没有这行，条件块语法不完整。
  }); // 新增代码+OAuthExternalBrowser：导航拦截器结束；如果没有这行，事件注册语法不完整。

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
