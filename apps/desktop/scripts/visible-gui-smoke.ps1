param( # 新增代码+DesktopVisibleSmoke：参数块开始，允许只生成指令或同时启动 GUI；如果没有这段，release gate 和人工验收无法共用脚本。
  [switch]$InstructionsOnly, # 新增代码+DesktopVisibleSmoke：只生成 smoke 指令不启动进程；如果没有这行，自动 release gate 会被 Electron 窗口阻塞。
  [switch]$Launch # 新增代码+DesktopVisibleSmoke：允许人工验收时启动 bridge 和桌面壳；如果没有这行，脚本只能写说明不能打开 GUI。
) # 新增代码+DesktopVisibleSmoke：参数块结束；如果没有这行，PowerShell 参数语法不完整。

$ErrorActionPreference = "Stop" # 新增代码+DesktopVisibleSmoke：遇到错误立即停止脚本；如果没有这行，启动失败可能仍写出看似成功的日志。
$scriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 新增代码+DesktopVisibleSmoke：用当前脚本路径兼容不同 PowerShell 宿主；如果没有这行，脚本目录可能解析为空。
$scriptRoot = Split-Path -Parent $scriptPath # 新增代码+DesktopVisibleSmoke：定位 scripts 目录；如果没有这行，后端和桌面启动脚本路径无法计算。
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..\..\..")).Path # 新增代码+DesktopVisibleSmoke：定位仓库根目录；如果没有这行，证据目录无法稳定落到 learning_agent/test。
$backendScript = Join-Path $scriptRoot "start-backend.ps1" # 新增代码+DesktopVisibleSmoke：定位 bridge 启动脚本；如果没有这行，Launch 模式无法启动后端。
$desktopScript = Join-Path $scriptRoot "start-desktop-dev.ps1" # 新增代码+DesktopVisibleSmoke：定位桌面壳启动脚本；如果没有这行，Launch 模式无法打开 Electron GUI。
$evidenceDir = Join-Path $repoRoot "learning_agent\test\desktop_gui_shell_v2\visible_gui_smoke" # 新增代码+DesktopVisibleSmoke：定义 smoke 证据目录；如果没有这行，人工验收日志没有固定位置。
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss" # 新增代码+DesktopVisibleSmoke：生成日志时间戳；如果没有这行，多次运行会覆盖同一个日志。
$smokeLogPath = Join-Path $evidenceDir "visible_gui_smoke_$timestamp.txt" # 新增代码+DesktopVisibleSmoke：生成本次 smoke 日志路径；如果没有这行，脚本无法告诉用户记录写在哪里。
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null # 新增代码+DesktopVisibleSmoke：确保 smoke 证据目录存在；如果没有这行，写日志会失败。

$instructions = @( # 新增代码+DesktopVisibleSmoke：准备人工可见 GUI 验收步骤；如果没有这段，脚本只会启动窗口但没有检查清单。
  "OpenHarness Desktop GUI V2 visible smoke" # 新增代码+DesktopVisibleSmoke：写入 smoke 标题；如果没有这行，日志缺少用途说明。
  "Smoke log: $smokeLogPath" # 新增代码+DesktopVisibleSmoke：写入日志路径；如果没有这行，用户不知道要回填哪个文件。
  "Launch mode: $Launch" # 新增代码+DesktopVisibleSmoke：写入是否启动进程；如果没有这行，日志无法区分预检和真实启动。
  "Manual visible confirmation is required; this script never claims PASS automatically." # 新增代码+DesktopVisibleSmoke：写入人工确认边界；如果没有这行，用户可能把自动预检误认为视觉验收通过。
  "1. Streaming Chinese answer: submit 请分析当前项目是什么项目，并列出模块组成。 Confirm assistant text streams and completes." # 新增代码+DesktopVisibleSmoke：写入中文流式验收项；如果没有这行，GT-001 可见检查缺失。
  "2. Streaming English answer: submit Summarize this project in two concise sentences. Confirm no mojibake or layout jump." # 新增代码+DesktopVisibleSmoke：写入英文流式验收项；如果没有这行，GT-002 可见检查缺失。
  "3. Safety refusal: submit a clearly unsafe local-permission bypass request. Confirm refusal appears as assistant message." # 新增代码+DesktopVisibleSmoke：写入安全拒绝验收项；如果没有这行，拒绝消息可见性缺少检查。
  "4. Multiline Chinese persistence: submit a three-line Chinese prompt, restart window, confirm newlines remain." # 新增代码+DesktopVisibleSmoke：写入中文多行持久化验收项；如果没有这行，多行恢复缺少检查。
  "5. Shift+Enter newline: type first line, Shift+Enter, second line, then Enter. Confirm only final Enter sends." # 新增代码+DesktopVisibleSmoke：写入 Shift+Enter 验收项；如果没有这行，composer 手感缺少检查。
  "6. Structured token rejection GUI error: use an invalid bridge token session and confirm polished unauthorized error without token leak." # 新增代码+DesktopVisibleSmoke：写入 token 拒绝验收项；如果没有这行，认证错误可见性缺少检查。
  "7. Structured unknown route GUI error: trigger an unknown bridge route through diagnostics tooling and confirm readable JSON error." # 新增代码+DesktopVisibleSmoke：写入未知路由验收项；如果没有这行，404 错误可见性缺少检查。
  "8. Bridge offline banner: stop bridge while GUI is open and confirm UI explains offline state instead of freezing." # 新增代码+DesktopVisibleSmoke：写入 bridge 离线验收项；如果没有这行，断线体验缺少检查。
  "9. Tool trace row: submit a prompt that emits tool events and confirm the Tools tab shows name, status, args, result, and duration." # 新增代码+DesktopVisibleSmoke：写入工具轨迹验收项；如果没有这行，TracePanel 可见性缺少检查。
  "10. Permission approve/deny: trigger a permission request twice and confirm approve and deny paths both reach backend UI state." # 新增代码+DesktopVisibleSmoke：写入权限验收项；如果没有这行，权限流缺少人工检查。
  "11. Browser panel degraded state: inspect Browser tab and confirm provider/degraded messaging is readable and path-safe." # 新增代码+DesktopVisibleSmoke：写入浏览器面板验收项；如果没有这行，浏览器降级状态缺少检查。
  "12. Computer Use safe unavailable state: inspect Browser tab Computer Use section and confirm off/lock/permission status is readable." # 新增代码+DesktopVisibleSmoke：写入 Computer Use 面板验收项；如果没有这行，桌面自动化安全状态缺少检查。
  "13. Settings panel opens: inspect Settings tab and confirm bridge, provider, feature flags, and paths are readable." # 新增代码+DesktopVisibleSmoke：写入设置面板验收项；如果没有这行，设置页缺少人工检查。
  "14. Diagnostics copy: inspect Diagnostics tab, copy safe bundle, confirm no token or local secret leaks." # 新增代码+DesktopVisibleSmoke：写入诊断复制验收项；如果没有这行，诊断脱敏缺少人工检查。
  "15. Window restart restores latest V2 session: close and reopen Electron, confirm sidebar and latest thread resume." # 新增代码+DesktopVisibleSmoke：写入窗口恢复验收项；如果没有这行，会话恢复缺少人工检查。
) # 新增代码+DesktopVisibleSmoke：人工可见 GUI 验收步骤数组结束；如果没有这行，PowerShell 数组语法不完整。
$instructions | Set-Content -Encoding UTF8 -LiteralPath $smokeLogPath # 新增代码+DesktopVisibleSmoke：写入 smoke 日志；如果没有这行，release gate 无法留下人工验收指令证据。
Write-Host "Visible GUI smoke log: $smokeLogPath" # 新增代码+DesktopVisibleSmoke：输出 smoke 日志路径；如果没有这行，用户不知道检查清单写到哪里。

if ($Launch -and -not $InstructionsOnly) { # 新增代码+DesktopVisibleSmoke：只有人工选择 Launch 时才启动进程；如果没有这行，自动 gate 会被 GUI 启动阻塞。
  $backend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $backendScript -WindowStyle Hidden -PassThru # 新增代码+DesktopVisibleSmoke：后台启动 bridge；如果没有这行，Launch 模式没有后端事实源。
  Start-Sleep -Seconds 3 # 新增代码+DesktopVisibleSmoke：等待 bridge 监听端口；如果没有这行，桌面壳可能先打开并显示离线。
  $desktop = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $desktopScript -WindowStyle Hidden -PassThru # 新增代码+DesktopVisibleSmoke：启动桌面 dev shell；如果没有这行，Launch 模式不会打开 Electron GUI。
  Write-Host "Started backend process id: $($backend.Id)" # 新增代码+DesktopVisibleSmoke：输出后端进程 id；如果没有这行，用户无法定位需要关闭的后台进程。
  Write-Host "Started desktop launcher process id: $($desktop.Id)" # 新增代码+DesktopVisibleSmoke：输出桌面启动进程 id；如果没有这行，用户无法定位 GUI 启动器。
  Write-Host "Visible confirmation is still required before marking smoke PASS." # 新增代码+DesktopVisibleSmoke：强调仍需人工确认；如果没有这行，启动成功可能被误认为验收通过。
} else { # 新增代码+DesktopVisibleSmoke：处理只生成指令分支；如果没有这行，脚本输出无法说明没有启动 GUI。
  Write-Host "Instructions generated only. Re-run with -Launch for manual visible GUI smoke." # 新增代码+DesktopVisibleSmoke：说明预检模式；如果没有这行，release gate 使用者会以为 GUI 已启动。
} # 新增代码+DesktopVisibleSmoke：Launch 条件分支结束；如果没有这行，PowerShell 条件块语法不完整。
