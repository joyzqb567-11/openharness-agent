param( # 修改代码+DesktopPackaging：参数块开始，允许用户覆盖工作区、端口和 token；如果没有这段，启动脚本只能使用硬编码默认值。
  [string]$Workspace = "", # 修改代码+DesktopPackaging：保存可选仓库根路径；如果没有这行，从其它目录启动时无法指定项目位置。
  [int]$Port = 8776, # 修改代码+DesktopPackaging：保存 GUI bridge 端口；如果没有这行，前端和后端端口约定无法调整。
  [string]$Token = "" # 修改代码+DesktopPackaging：保存可选认证 token；如果没有这行，Electron 和 bridge 无法共享非默认 token。
) # 修改代码+DesktopPackaging：参数块结束；如果没有这行，PowerShell 参数语法不完整。

function Test-OpenHarnessPortAvailable { # 新增代码+DesktopPackaging：函数段开始，检查端口是否可绑定；如果没有这段，端口占用只会在后端启动失败时暴露。
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
      $listener.Stop() # 新增代码+DesktopPackaging：释放临时端口绑定；如果没有这行，后续真正 bridge 无法使用该端口。
    } # 新增代码+DesktopPackaging：listener 释放判断结束；如果没有这行，PowerShell 条件块语法不完整。
  } # 新增代码+DesktopPackaging：端口检查 finally 结束；如果没有这行，PowerShell try/catch/finally 语法不完整。
} # 新增代码+DesktopPackaging：函数段结束，Test-OpenHarnessPortAvailable 到此结束；如果没有这行，端口检查逻辑范围不清楚。

$ErrorActionPreference = "Stop" # 修改代码+DesktopPackaging：遇到错误立即停止脚本；如果没有这行，后端启动失败可能被后续输出掩盖。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 修改代码+DesktopPackaging：用当前脚本路径兼容不同 PowerShell 宿主；如果没有这行，某些宿主下 `$PSScriptRoot` 为空会导致默认 workspace 失败。
$ScriptDir = Split-Path -Parent $ScriptPath # 修改代码+DesktopPackaging：定位 scripts 目录；如果没有这行，后续无法稳定推导仓库根。
$Workspace = if ($Workspace) { (Resolve-Path $Workspace).Path } else { (Resolve-Path (Join-Path $ScriptDir "..\..\..")).Path } # 修改代码+DesktopPackaging：解析仓库根 workspace 绝对路径；如果没有这行，python -m 可能找不到 learning_agent 包。
$Token = if ($Token) { $Token } elseif ($env:OPENHARNESS_GUI_BRIDGE_TOKEN) { $env:OPENHARNESS_GUI_BRIDGE_TOKEN } else { "openharness-desktop-dev-token" } # 修改代码+DesktopPackaging：统一后端默认 token；如果没有这行，GUI 默认请求会被 401 拒绝。
$BridgeUrl = "http://127.0.0.1:$Port" # 新增代码+DesktopPackaging：生成 bridge URL；如果没有这行，终端无法明确告诉用户后端监听地址。
$EvidenceFolder = Join-Path $Workspace "learning_agent\test\desktop_gui_shell_v2\launch_logs" # 新增代码+DesktopPackaging：生成启动证据目录；如果没有这行，日志和截图证据没有固定位置。
New-Item -ItemType Directory -Force -Path $EvidenceFolder | Out-Null # 新增代码+DesktopPackaging：确保启动证据目录存在；如果没有这行，后续验收证据可能无法落盘。
if (-not (Test-OpenHarnessPortAvailable -PortNumber $Port)) { # 新增代码+DesktopPackaging：启动前检查 bridge 端口；如果没有这行，端口占用时错误会很晚且不清楚。
  throw "Bridge port $Port is already occupied. Close the existing bridge or pass -Port <free-port>." # 新增代码+DesktopPackaging：输出清楚端口占用错误；如果没有这行，用户不知道如何修复启动失败。
} # 新增代码+DesktopPackaging：端口占用检查结束；如果没有这行，PowerShell 条件块语法不完整。
Write-Host "Starting OpenHarness Desktop GUI bridge..." # 修改代码+DesktopPackaging：显示后端启动提示；如果没有这行，用户无法判断脚本是否进入主体逻辑。
Write-Host "Bridge URL: $BridgeUrl" # 新增代码+DesktopPackaging：打印 bridge 地址；如果没有这行，前端或人工排查不知道该连哪里。
Write-Host "Renderer URL: start with apps/desktop/scripts/start-desktop-dev.ps1" # 新增代码+DesktopPackaging：说明 renderer 由另一个脚本负责；如果没有这行，用户可能误以为后端脚本会打开 GUI。
Write-Host "Evidence folder: $EvidenceFolder" # 新增代码+DesktopPackaging：打印证据目录；如果没有这行，用户找不到启动日志和验收材料。
Set-Location $Workspace # 修改代码+DesktopPackaging：切换到仓库根目录；如果没有这行，python -m 可能找不到 learning_agent 包。
python -m learning_agent.app.cli desktop-bridge --workspace $Workspace --port $Port --token $Token # 修改代码+DesktopPackaging：启动 GUI bridge 并显式传入 token；如果没有这行，Electron 默认 token 无法通过后端认证。
