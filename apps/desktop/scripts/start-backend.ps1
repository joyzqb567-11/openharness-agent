param(
  [string]$Workspace = "",
  [int]$Port = 8776,
  [string]$Token = ""
)

# 新增代码+DesktopLaunchScripts：上面的参数块允许用户覆盖 Workspace 和 Port；如果没有这行说明，启动脚本的可配置入口不清楚。
# 修改代码+DesktopLaunchScripts：Workspace 空值时由脚本体从 scripts 目录向上三级计算仓库根；如果没有这行说明，默认路径策略不清楚。
# 新增代码+DesktopLaunchScripts：Port 默认 GUI bridge 端口 8776；如果没有这行说明，前端 preload 和后端端口约定不清楚。
# 新增代码+DesktopBridgeConfig：Token 允许后端和 Electron 使用同一个认证令牌；如果没有这行说明，GUI 会打开但安全端点无法通过认证。
Write-Host "Starting OpenHarness Desktop GUI bridge..." # 新增代码+DesktopBridgeConfig：显示后端启动提示；如果没有这行，用户无法判断脚本是否真正进入主体逻辑。
$ErrorActionPreference = "Stop" # 新增代码+DesktopLaunchScripts：遇到错误立即停止脚本；如果没有这行，后端启动失败可能被后续命令掩盖。
$Workspace = if ($Workspace) { (Resolve-Path $Workspace).Path } else { (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path } # 修改代码+DesktopLaunchScripts：解析仓库根 workspace 绝对路径；如果没有这行，默认启动会错误落到 apps 目录导致找不到 learning_agent 包。
$Token = if ($Token) { $Token } elseif ($env:OPENHARNESS_GUI_BRIDGE_TOKEN) { $env:OPENHARNESS_GUI_BRIDGE_TOKEN } else { "openharness-desktop-dev-token" } # 新增代码+DesktopBridgeConfig：统一后端默认 token；如果没有这行，后端随机 token 会让 GUI 默认无法连接。
Set-Location $Workspace # 新增代码+DesktopLaunchScripts：切换到仓库根目录；如果没有这行，python -m 可能找不到 learning_agent 包。
python -m learning_agent.app.cli desktop-bridge --workspace $Workspace --port $Port --token $Token # 修改代码+DesktopBridgeConfig：启动 GUI bridge 并显式传入 token；如果没有这行，Electron 默认 token 无法通过后端认证。


