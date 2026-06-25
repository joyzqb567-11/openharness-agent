param( # 修改代码+DesktopPackaging：参数块开始，允许覆盖 bridge 地址和 token；如果没有这段，桌面壳只能连接默认后端。
  [string]$BridgeUrl = "", # 修改代码+DesktopPackaging：保存可选 bridge 地址；如果没有这行，用户无法连接非默认端口。
  [string]$BridgeToken = "" # 修改代码+DesktopPackaging：保存可选 bridge token；如果没有这行，用户无法使用非默认认证令牌。
) # 修改代码+DesktopPackaging：参数块结束；如果没有这行，PowerShell 参数语法不完整。

function Test-OpenHarnessPortAvailable { # 新增代码+DesktopPackaging：函数段开始，检查端口是否可绑定；如果没有这段，renderer 端口占用只会在 Vite 失败时暴露。
  param( # 新增代码+DesktopPackaging：端口检查函数参数块开始；如果没有这段，函数不知道要检查哪个端口。
    [int]$PortNumber # 新增代码+DesktopPackaging：保存待检查端口；如果没有这行，检查逻辑没有输入。
  ) # 新增代码+DesktopPackaging：端口检查函数参数块结束；如果没有这行，PowerShell 参数语法不完整。
  $listener = $null # 新增代码+DesktopPackaging：准备 TCP listener 变量；如果没有这行，finally 中无法安全释放对象。
  try { # 新增代码+DesktopPackaging：尝试绑定端口；如果没有这行，端口占用异常无法转成清楚布尔值。
    $address = [System.Net.IPAddress]::Parse("127.0.0.1") # 新增代码+DesktopPackaging：固定检查本机回环地址；如果没有这行，端口检查目标不明确。
    $listener = [System.Net.Sockets.TcpListener]::new($address, $PortNumber) # 新增代码+DesktopPackaging：创建临时 listener；如果没有这行，无法确认端口是否已被占用。
    $listener.Start() # 新增代码+DesktopPackaging：实际尝试绑定端口；如果没有这行，检查永远不会触碰系统端口表。
    return $true # 新增代码+DesktopPackaging：绑定成功说明端口可用；如果没有这行，可用端口会被误判失败。
  } catch { # 新增代码+DesktopPackaging：捕获绑定失败；如果没有这行，端口占用会输出难懂异常。
    return $false # 新增代码+DesktopPackaging：绑定失败说明端口不可用；如果没有这行，脚本不能给出清楚占用提示。
  } finally { # 新增代码+DesktopPackaging：确保临时 listener 被释放；如果没有这行，端口检查本身可能占住端口。
    if ($null -ne $listener) { # 新增代码+DesktopPackaging：确认 listener 已创建；如果没有这行，空对象 Stop 会报错。
      $listener.Stop() # 新增代码+DesktopPackaging：释放临时端口绑定；如果没有这行，后续 Vite 无法使用该端口。
    } # 新增代码+DesktopPackaging：listener 释放判断结束；如果没有这行，PowerShell 条件块语法不完整。
  } # 新增代码+DesktopPackaging：端口检查 finally 结束；如果没有这行，PowerShell try/catch/finally 语法不完整。
} # 新增代码+DesktopPackaging：函数段结束，Test-OpenHarnessPortAvailable 到此结束；如果没有这行，端口检查逻辑范围不清楚。

$ErrorActionPreference = "Stop" # 修改代码+DesktopPackaging：遇到错误立即停止脚本；如果没有这行，renderer 或 Electron 失败可能被静默忽略。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 修改代码+DesktopPackaging：用当前脚本路径兼容不同 PowerShell 宿主；如果没有这行，某些宿主下 `$PSScriptRoot` 为空会导致桌面目录失败。
$ScriptDir = Split-Path -Parent $ScriptPath # 修改代码+DesktopPackaging：定位 scripts 目录；如果没有这行，后续无法稳定推导 apps/desktop。
$DesktopRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path # 修改代码+DesktopPackaging：定位 apps/desktop 目录；如果没有这行，脚本从其它目录启动时会找不到 package.json。
$Workspace = (Resolve-Path (Join-Path $DesktopRoot "..\..")).Path # 新增代码+DesktopPackaging：定位仓库根目录；如果没有这行，证据目录无法稳定计算。
$RendererPort = 5177 # 新增代码+DesktopPackaging：声明 Vite renderer 端口；如果没有这行，端口检查和 URL 输出会散落硬编码。
$RendererUrl = "http://127.0.0.1:$RendererPort" # 新增代码+DesktopPackaging：生成 renderer URL；如果没有这行，用户不知道 Electron 会加载哪个页面。
$BridgeUrl = if ($BridgeUrl) { $BridgeUrl } elseif ($env:OPENHARNESS_GUI_BRIDGE_URL) { $env:OPENHARNESS_GUI_BRIDGE_URL } else { "http://127.0.0.1:8776" } # 修改代码+DesktopPackaging：确定 Electron 要连接的 bridge 地址；如果没有这行，preload 没有稳定 baseUrl。
$BridgeToken = if ($BridgeToken) { $BridgeToken } elseif ($env:OPENHARNESS_GUI_BRIDGE_TOKEN) { $env:OPENHARNESS_GUI_BRIDGE_TOKEN } else { "openharness-desktop-dev-token" } # 修改代码+DesktopPackaging：确定 Electron 要注入的 token；如果没有这行，GUI 请求会被后端 401 拒绝。
$EvidenceFolder = Join-Path $Workspace "learning_agent\test\desktop_gui_shell_v2\launch_logs" # 新增代码+DesktopPackaging：生成启动证据目录；如果没有这行，GUI smoke 日志没有固定位置。
New-Item -ItemType Directory -Force -Path $EvidenceFolder | Out-Null # 新增代码+DesktopPackaging：确保启动证据目录存在；如果没有这行，后续截图或日志可能无法落盘。
if (-not (Test-OpenHarnessPortAvailable -PortNumber $RendererPort)) { # 新增代码+DesktopPackaging：启动前检查 renderer 端口；如果没有这行，端口占用会让 Vite 报复杂错误。
  throw "Renderer port $RendererPort is already occupied. Close the existing Vite server or change dev:renderer port." # 新增代码+DesktopPackaging：输出清楚 renderer 端口占用错误；如果没有这行，用户不知道如何修复白屏或启动失败。
} # 新增代码+DesktopPackaging：renderer 端口检查结束；如果没有这行，PowerShell 条件块语法不完整。

Write-Host "Starting OpenHarness Desktop GUI shell..." # 新增代码+DesktopPackaging：显示桌面壳启动提示；如果没有这行，用户无法判断脚本是否进入主体逻辑。
Write-Host "Bridge URL: $BridgeUrl" # 新增代码+DesktopPackaging：打印后端 bridge 地址；如果没有这行，连接失败时用户不知道请求目标。
Write-Host "Renderer URL: $RendererUrl" # 新增代码+DesktopPackaging：打印 renderer 地址；如果没有这行，用户无法单独打开前端排查。
Write-Host "Evidence folder: $EvidenceFolder" # 新增代码+DesktopPackaging：打印证据目录；如果没有这行，验收材料位置不清楚。

Set-Location $DesktopRoot # 修改代码+DesktopPackaging：切换到桌面应用目录；如果没有这行，npm 命令会在错误目录执行。
$env:ELECTRON_MIRROR = if ($env:ELECTRON_MIRROR) { $env:ELECTRON_MIRROR } else { "https://npmmirror.com/mirrors/electron/" } # 修改代码+DesktopPackaging：给 Electron 二进制下载设置镜像兜底；如果没有这行，国内网络下 electron.exe 可能安装不完整。
if (-not (Test-Path -LiteralPath (Join-Path $DesktopRoot "node_modules"))) { # 修改代码+DesktopPackaging：检查依赖目录是否存在；如果没有这行，新机器缺依赖时错误不清楚。
  npm install # 修改代码+DesktopPackaging：安装桌面依赖；如果没有这行，新机器上 npm run start 会找不到 Electron/Vite。
} else { # 新增代码+DesktopPackaging：处理依赖已存在分支；如果没有这行，脚本无法输出为什么跳过安装。
  Write-Host "Dependencies already installed; skipping npm install." # 新增代码+DesktopPackaging：提示依赖复用；如果没有这行，启动耗时变化不透明。
} # 修改代码+DesktopPackaging：依赖检查结束；如果没有这行，PowerShell 条件块语法不完整。
npm rebuild electron # 修改代码+DesktopPackaging：强制修复缺失的 Electron dist 二进制；如果没有这行，node_modules 已存在但 electron.exe 缺失时窗口仍无法启动。
npm run build:main # 修改代码+DesktopPackaging：构建 Electron main/preload；如果没有这行，electron . 会找不到 dist/main/index.js。

$env:OPENHARNESS_GUI_BRIDGE_URL = $BridgeUrl # 修改代码+DesktopPackaging：把 bridge 地址传给 Electron 主进程；如果没有这行，main 进程读不到后端地址。
$env:OPENHARNESS_GUI_BRIDGE_TOKEN = $BridgeToken # 修改代码+DesktopPackaging：把 token 传给 Electron 主进程；如果没有这行，preload 无法注入认证令牌。
$env:OPENHARNESS_DESKTOP_DEV_URL = $RendererUrl # 修改代码+DesktopPackaging：让 Electron 加载 Vite dev server；如果没有这行，Electron 会加载旧的打包 HTML。
$renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer" -WindowStyle Hidden -PassThru # 修改代码+DesktopPackaging：后台启动 renderer dev server；如果没有这行，Electron 无法加载开发页面。
try { # 修改代码+DesktopPackaging：保护 renderer 进程清理；如果没有这行，Electron 退出后 Vite 可能残留。
  Start-Sleep -Seconds 3 # 修改代码+DesktopPackaging：等待 Vite 监听端口；如果没有这行，Electron 可能太早打开导致白屏。
  npm run start # 修改代码+DesktopPackaging：启动 Electron 桌面壳；如果没有这行，用户看不到 GUI 窗口。
} finally { # 修改代码+DesktopPackaging：无论 Electron 如何退出都执行清理；如果没有这行，renderer 进程可能遗留。
  if ($renderer -and -not $renderer.HasExited) { # 修改代码+DesktopPackaging：确认 renderer 仍在运行；如果没有这行，Stop-Process 可能误操作空对象或已退出进程。
    Stop-Process -Id $renderer.Id -Force # 修改代码+DesktopPackaging：关闭 renderer dev server；如果没有这行，端口 5177 可能被长期占用。
  } # 修改代码+DesktopPackaging：renderer 清理判断结束；如果没有这行，PowerShell 条件块语法不完整。
} # 修改代码+DesktopPackaging：finally 块结束；如果没有这行，PowerShell 语法不完整。
