$ErrorActionPreference = "Stop" # 修改代码+DesktopReleaseGateV2：遇到任何命令失败就立即停止；如果没有这行代码，失败的测试可能被后续命令淹没。
$scriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 修改代码+DesktopReleaseGateV2：用当前脚本路径兼容不同 PowerShell 宿主；如果没有这行，脚本目录可能解析为空。
$scriptRoot = Split-Path -Parent $scriptPath # 修改代码+DesktopReleaseGateV2：定位脚本所在目录；如果没有这行代码，脚本从不同目录启动时会找错项目根目录。
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..\..\..")).Path # 修改代码+DesktopReleaseGateV2：从 apps/desktop/scripts 回到仓库根目录；如果没有这行代码，Python 测试无法稳定找到 learning_agent 包。
$desktopRoot = Join-Path $repoRoot "apps\desktop" # 修改代码+DesktopReleaseGateV2：定位桌面前端目录；如果没有这行代码，npm 命令需要依赖调用者手动 cd。
$visibleSmokeScript = Join-Path $scriptRoot "visible-gui-smoke.ps1" # 新增代码+DesktopReleaseGateV2：定位可见 GUI smoke 脚本；如果没有这行，release gate 无法生成 Layer A 人工验收指令。
Write-Host "Running OpenHarness desktop GUI release gate V2..." # 修改代码+DesktopReleaseGateV2：输出门禁开始提示；如果没有这行代码，用户看不出当前脚本在执行什么。

Push-Location $repoRoot # 修改代码+DesktopReleaseGateV2：切到仓库根目录运行 Python GUI 测试；如果没有这行代码，模块导入路径可能不稳定。
try { # 修改代码+DesktopReleaseGateV2：保护仓库根目录工作位置；如果没有这行代码，失败后可能停留在错误目录。
  python -m unittest discover -s learning_agent/tests -p "test_gui*.py" # 修改代码+DesktopReleaseGateV2：运行 GUI V1/V2 后端合同、安全、生命周期、权限、诊断、会话和 Harness 测试；如果没有这行，后端 GUI 回归会漏过。
  Write-Host "Python GUI tests OK." # 新增代码+DesktopReleaseGateV2：输出 Python GUI 测试成功标记；如果没有这行，release gate 输出不符合 V2 蓝图。
} finally { # 修改代码+DesktopReleaseGateV2：无论 Python 测试成功失败都恢复目录；如果没有这行代码，后续 shell 状态会被污染。
  Pop-Location # 修改代码+DesktopReleaseGateV2：回到调用脚本前的目录；如果没有这行代码，用户终端会停在仓库根目录。
} # 修改代码+DesktopReleaseGateV2：仓库根目录保护结束；如果没有这行代码，try/finally 语法不完整。

Push-Location $desktopRoot # 修改代码+DesktopReleaseGateV2：切到桌面前端目录运行 npm 门禁；如果没有这行代码，npm 找不到 apps/desktop/package.json。
try { # 修改代码+DesktopReleaseGateV2：保护桌面目录工作位置；如果没有这行代码，失败后可能停留在 apps/desktop。
  npm run lint # 修改代码+DesktopReleaseGateV2：运行 TypeScript 类型检查；如果没有这行代码，main/preload/renderer 类型错误会漏过。
  Write-Host "Frontend lint passed." # 新增代码+DesktopReleaseGateV2：输出前端 lint 成功标记；如果没有这行，release gate 输出不符合 V2 蓝图。
  npm test -- --run # 修改代码+DesktopReleaseGateV2：运行 Vitest 单元测试；如果没有这行代码，renderer 状态和 client 合同回归会漏过。
  Write-Host "Frontend unit tests passed." # 新增代码+DesktopReleaseGateV2：输出前端单元测试成功标记；如果没有这行，release gate 输出不符合 V2 蓝图。
  npm run build # 修改代码+DesktopReleaseGateV2：构建 Electron main/preload/renderer 输出；如果没有这行代码，发布前无法确认打包入口可生成。
  Write-Host "Frontend production build passed." # 新增代码+DesktopReleaseGateV2：输出生产构建成功标记；如果没有这行，release gate 输出不符合 V2 蓝图。
} finally { # 修改代码+DesktopReleaseGateV2：无论 npm 门禁成功失败都恢复目录；如果没有这行代码，用户终端会停在 apps/desktop。
  Pop-Location # 修改代码+DesktopReleaseGateV2：回到调用脚本前的目录；如果没有这行代码，脚本副作用会污染工作目录。
} # 修改代码+DesktopReleaseGateV2：桌面目录保护结束；如果没有这行代码，try/finally 语法不完整。

& $visibleSmokeScript -InstructionsOnly # 新增代码+DesktopReleaseGateV2：生成 Layer A 可见 GUI smoke 指令但不自动宣称通过；如果没有这行，release gate 缺少人工视觉验收入口。
Write-Host "Layer A visible GUI smoke instructions generated." # 新增代码+DesktopReleaseGateV2：输出可见 GUI smoke 预检标记；如果没有这行，release gate 输出不符合 V2 蓝图。
$layerCDecision = "Layer C trigger decision: not required for GUI-only gate unless agent runtime, MCP routing, model calls, browser automation, Computer Use, or backend permission enforcement changed." # 新增代码+DesktopReleaseGateV2：声明真实后端 agent 终端门禁触发条件；如果没有这行，用户无法判断是否还要跑 start_oauth_agent.bat。
Write-Host $layerCDecision # 新增代码+DesktopReleaseGateV2：打印 Layer C 判定；如果没有这行，release gate 缺少后端终端门禁说明。
Write-Host "Layer C trigger decision printed." # 新增代码+DesktopReleaseGateV2：输出 Layer C 判定已打印标记；如果没有这行，release gate 输出不符合 V2 蓝图。
Write-Host "OpenHarness desktop GUI release gate V2 passed automated checks." # 修改代码+DesktopReleaseGateV2：输出自动门禁成功提示；如果没有这行，用户不容易确认自动检查已完成。
