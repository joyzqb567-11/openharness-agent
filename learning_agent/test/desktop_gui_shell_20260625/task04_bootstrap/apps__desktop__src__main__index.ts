import { app, BrowserWindow } from "electron"; // 新增代码+DesktopMain：引入 Electron 应用和窗口对象；如果没有这行，桌面壳无法创建真实窗口。
import path from "node:path"; // 新增代码+DesktopMain：引入路径工具；如果没有这行，Windows 和 macOS/Linux 的 preload 路径会难以兼容。
import { fileURLToPath } from "node:url"; // 新增代码+DesktopMain：把 ESM 文件 URL 转成本地路径；如果没有这行，主进程无法定位 dist 目录。

const currentFile = fileURLToPath(import.meta.url); // 新增代码+DesktopMain：得到当前主进程文件路径；如果没有这行，后续无法计算 preload 和 renderer 的位置。
const currentDir = path.dirname(currentFile); // 新增代码+DesktopMain：得到当前主进程目录；如果没有这行，loadFile 会找不到打包后的 index.html。

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
      sandbox: true, // 新增代码+DesktopMain：开启渲染沙箱；如果没有这行，桌面 GUI 的攻击面会更大。
    }, // 新增代码+DesktopMain：webPreferences 配置结束；如果没有这行，窗口配置语法不完整。
  }); // 新增代码+DesktopMain：窗口对象创建结束；如果没有这行，BrowserWindow 构造调用不完整。

  const devServerUrl = process.env.OPENHARNESS_DESKTOP_DEV_URL; // 新增代码+DesktopMain：读取开发模式渲染地址；如果没有这行，开发时 Electron 不能连接 Vite 热更新页面。
  if (devServerUrl) { // 新增代码+DesktopMain：判断是否处于开发模式；如果没有这行，开发和生产加载路径会混在一起。
    void window.loadURL(devServerUrl); // 新增代码+DesktopMain：开发模式加载 Vite 页面；如果没有这行，npm run desktop:dev 打不开热更新页面。
    return; // 新增代码+DesktopMain：开发加载后提前返回；如果没有这行，窗口会继续尝试加载生产文件并产生冲突。
  } // 新增代码+DesktopMain：开发模式分支结束；如果没有这行，TypeScript 语法不完整。

  void window.loadFile(path.join(currentDir, "../renderer/index.html")); // 新增代码+DesktopMain：生产模式加载构建产物；如果没有这行，打包后桌面窗口会空白。
} // 新增代码+DesktopMain：函数段结束，createWindow 到此结束；如果没有这个边界，用户不容易看出窗口创建逻辑范围。

void app.whenReady().then(createWindow); // 新增代码+DesktopMain：Electron 准备好后创建窗口；如果没有这行，应用启动后不会显示窗口。

app.on("window-all-closed", () => { // 新增代码+DesktopMain：监听所有窗口关闭事件；如果没有这段，Windows 关闭窗口后进程可能残留。
  if (process.platform !== "darwin") { // 新增代码+DesktopMain：保留 macOS 常见行为；如果没有这行，macOS 上关闭窗口会直接退出应用。
    app.quit(); // 新增代码+DesktopMain：非 macOS 平台关闭应用；如果没有这行，Windows 上关闭窗口后后台进程会继续占用资源。
  } // 新增代码+DesktopMain：平台判断结束；如果没有这行，条件块语法不完整。
}); // 新增代码+DesktopMain：窗口关闭监听结束；如果没有这行，事件注册语法不完整。
