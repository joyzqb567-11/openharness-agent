param(
  [string]$Workspace = "",
  [int]$Port = 8776
)

# 新增代码+DesktopLaunchScripts：上面的参数块允许用户覆盖 Workspace 和 Port；如果没有这行说明，启动脚本的可配置入口不清楚。
# 修改代码+DesktopLaunchScripts：Workspace 空值时由脚本体计算默认仓库根；如果没有这行说明，默认路径策略不清楚。
# 新增代码+DesktopLaunchScripts：Port 默认 GUI bridge 端口 8776；如果没有这行说明，前端 preload 和后端端口约定不清楚。
$ErrorActionPreference = "Stop" # 新增代码+DesktopLaunchScripts：遇到错误立即停止脚本；如果没有这行，后端启动失败可能被后续命令掩盖。
$Workspace = if ($Workspace) { (Resolve-Path $Workspace).Path } else { (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path } # 修改代码+DesktopLaunchScripts：解析 workspace 绝对路径；如果没有这行，python -m 可能从错误目录或相对路径启动。
Set-Location $Workspace # 新增代码+DesktopLaunchScripts：切换到仓库根目录；如果没有这行，python -m 可能找不到 learning_agent 包。
python -m learning_agent.app.cli desktop-bridge --workspace $Workspace --port $Port # 新增代码+DesktopLaunchScripts：启动 GUI bridge 后端；如果没有这行，桌面 GUI 没有本地 API 可连接。
