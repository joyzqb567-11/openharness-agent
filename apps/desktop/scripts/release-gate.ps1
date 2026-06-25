$ErrorActionPreference = "Stop" # 新增代码+DesktopReleaseGate：遇到任何命令失败就立即停止；如果没有这行代码，失败的测试可能被后续命令淹没。
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path # 新增代码+DesktopReleaseGate：定位脚本所在目录；如果没有这行代码，脚本从不同目录启动时会找错项目根目录。
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..\..") # 新增代码+DesktopReleaseGate：从 apps/desktop/scripts 回到仓库根目录；如果没有这行代码，Python 测试无法稳定找到 learning_agent 包。
$desktopRoot = Join-Path $repoRoot "apps\desktop" # 新增代码+DesktopReleaseGate：定位桌面前端目录；如果没有这行代码，npm 命令需要依赖调用者手动 cd。
Write-Host "Running OpenHarness desktop GUI release gate..." # 新增代码+DesktopReleaseGate：输出门禁开始提示；如果没有这行代码，用户看不出当前脚本在执行什么。
Push-Location $repoRoot # 新增代码+DesktopReleaseGate：切到仓库根目录运行 Python 测试；如果没有这行代码，模块导入路径可能不稳定。
try { # 新增代码+DesktopReleaseGate：保护仓库根目录工作位置；如果没有这行代码，失败后可能停留在错误目录。
    python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_bridge_permission_contract # 新增代码+DesktopReleaseGate：运行 GUI bridge 后端合同、安全、生命周期、权限和事件测试；如果没有这行代码，后端 bridge 回归无法拦截。
} finally { # 新增代码+DesktopReleaseGate：无论 Python 测试成功失败都恢复目录；如果没有这行代码，后续 shell 状态会被污染。
    Pop-Location # 新增代码+DesktopReleaseGate：回到调用脚本前的目录；如果没有这行代码，用户终端会停在仓库根目录。
} # 新增代码+DesktopReleaseGate：仓库根目录保护结束；如果没有这行代码，try/finally 语法不完整。
Push-Location $desktopRoot # 新增代码+DesktopReleaseGate：切到桌面前端目录运行 npm 门禁；如果没有这行代码，npm 找不到 apps/desktop/package.json。
try { # 新增代码+DesktopReleaseGate：保护桌面目录工作位置；如果没有这行代码，失败后可能停留在 apps/desktop。
    npm run lint # 新增代码+DesktopReleaseGate：运行 TypeScript 类型检查；如果没有这行代码，main/preload/renderer 类型错误会漏过。
    npm test -- --run # 新增代码+DesktopReleaseGate：运行 Vitest 单元测试；如果没有这行代码，renderer 状态和 client 合同回归会漏过。
    npm run build # 新增代码+DesktopReleaseGate：构建 Electron main/preload/renderer 输出；如果没有这行代码，发布前无法确认打包入口可生成。
} finally { # 新增代码+DesktopReleaseGate：无论 npm 门禁成功失败都恢复目录；如果没有这行代码，用户终端会停在 apps/desktop。
    Pop-Location # 新增代码+DesktopReleaseGate：回到调用脚本前的目录；如果没有这行代码，脚本副作用会污染工作目录。
} # 新增代码+DesktopReleaseGate：桌面目录保护结束；如果没有这行代码，try/finally 语法不完整。
Write-Host "OpenHarness desktop GUI release gate passed." # 新增代码+DesktopReleaseGate：输出门禁成功提示；如果没有这行代码，用户不容易确认所有检查已完成。

