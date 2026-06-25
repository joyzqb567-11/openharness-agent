param(
  [string]$BridgeUrl = "",
  [string]$BridgeToken = ""
)

# 新增代码+DesktopBridgeConfig：上面的参数块允许用户覆盖 GUI bridge 地址和 token；如果没有这段说明，前后端认证联动不清楚。
$ErrorActionPreference = "Stop" # 新增代码+DesktopLaunchScripts：遇到错误立即停止脚本；如果没有这行，renderer 或 Electron 失败可能被静默忽略。

$DesktopRoot = Split-Path -Parent $PSScriptRoot # 新增代码+DesktopLaunchScripts：定位 apps/desktop 目录；如果没有这行，脚本从其它目录启动时会找不到 package.json。
Set-Location $DesktopRoot # 新增代码+DesktopLaunchScripts：切换到桌面应用目录；如果没有这行，npm 命令会在错误目录执行。

$env:ELECTRON_MIRROR = if ($env:ELECTRON_MIRROR) { $env:ELECTRON_MIRROR } else { "https://npmmirror.com/mirrors/electron/" } # 新增代码+DesktopLaunchScripts：给 Electron 二进制下载设置镜像兜底；如果没有这行，国内网络下 electron.exe 可能安装不完整。
npm install # 新增代码+DesktopLaunchScripts：确保桌面依赖已安装；如果没有这行，新机器上 npm run start 会找不到 Electron/Vite。
npm rebuild electron # 新增代码+DesktopLaunchScripts：强制修复缺失的 Electron dist 二进制；如果没有这行，node_modules 已存在但 electron.exe 缺失时窗口仍无法启动。
npm run build:main # 新增代码+DesktopLaunchScripts：构建 Electron main/preload；如果没有这行，electron . 会找不到 dist/main/index.js。

$BridgeUrl = if ($BridgeUrl) { $BridgeUrl } elseif ($env:OPENHARNESS_GUI_BRIDGE_URL) { $env:OPENHARNESS_GUI_BRIDGE_URL } else { "http://127.0.0.1:8776" } # 新增代码+DesktopBridgeConfig：确定 Electron 要连接的 bridge 地址；如果没有这行，preload 没有稳定 baseUrl。
$BridgeToken = if ($BridgeToken) { $BridgeToken } elseif ($env:OPENHARNESS_GUI_BRIDGE_TOKEN) { $env:OPENHARNESS_GUI_BRIDGE_TOKEN } else { "openharness-desktop-dev-token" } # 新增代码+DesktopBridgeConfig：确定 Electron 要注入的 token；如果没有这行，GUI 请求会被后端 401 拒绝。
$env:OPENHARNESS_GUI_BRIDGE_URL = $BridgeUrl # 新增代码+DesktopBridgeConfig：把 bridge 地址传给 Electron 主进程；如果没有这行，main 进程读不到后端地址。
$env:OPENHARNESS_GUI_BRIDGE_TOKEN = $BridgeToken # 新增代码+DesktopBridgeConfig：把 token 传给 Electron 主进程；如果没有这行，preload 无法注入认证令牌。
$env:OPENHARNESS_DESKTOP_DEV_URL = "http://127.0.0.1:5177" # 新增代码+DesktopLaunchScripts：让 Electron 加载 Vite dev server；如果没有这行，Electron 会加载旧的打包 HTML。
$renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer" -WindowStyle Hidden -PassThru # 新增代码+DesktopLaunchScripts：后台启动 renderer dev server；如果没有这行，Electron 无法加载开发页面。
try { # 新增代码+DesktopLaunchScripts：保护 renderer 进程清理；如果没有这行，Electron 退出后 Vite 可能残留。
  Start-Sleep -Seconds 3 # 新增代码+DesktopLaunchScripts：等待 Vite 监听端口；如果没有这行，Electron 可能太早打开导致白屏。
  npm run start # 新增代码+DesktopLaunchScripts：启动 Electron 桌面壳；如果没有这行，用户看不到 GUI 窗口。
} # 新增代码+DesktopLaunchScripts：try 块结束；如果没有这行，PowerShell 语法不完整。
finally { # 新增代码+DesktopLaunchScripts：无论 Electron 如何退出都执行清理；如果没有这行，renderer 进程可能遗留。
  if ($renderer -and -not $renderer.HasExited) { # 新增代码+DesktopLaunchScripts：确认 renderer 仍在运行；如果没有这行，Stop-Process 可能误操作空对象或已退出进程。
    Stop-Process -Id $renderer.Id -Force # 新增代码+DesktopLaunchScripts：关闭 renderer dev server；如果没有这行，端口 5177 可能被长期占用。
  } # 新增代码+DesktopLaunchScripts：renderer 清理判断结束；如果没有这行，PowerShell 条件块语法不完整。
} # 新增代码+DesktopLaunchScripts：finally 块结束；如果没有这行，PowerShell 语法不完整。


