$ErrorActionPreference = "Stop" # 新增代码+DesktopLaunchScripts：遇到错误立即停止脚本；如果没有这行，renderer 或 Electron 失败可能被静默忽略。

$DesktopRoot = Split-Path -Parent $PSScriptRoot # 新增代码+DesktopLaunchScripts：定位 apps/desktop 目录；如果没有这行，脚本从其它目录启动时会找不到 package.json。
Set-Location $DesktopRoot # 新增代码+DesktopLaunchScripts：切换到桌面应用目录；如果没有这行，npm 命令会在错误目录执行。

npm install # 新增代码+DesktopLaunchScripts：确保桌面依赖已安装；如果没有这行，新机器上 npm run start 会找不到 Electron/Vite。
npm run build:main # 新增代码+DesktopLaunchScripts：构建 Electron main/preload；如果没有这行，electron . 会找不到 dist/main/index.js。

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
