param(
  # 新增代码+DesktopOAuthOneClickLaunch：允许覆盖 GUI bridge 端口；如果没有这一行，后端端口只能硬编码。
  [int]$BridgePort = 8776,
  # 新增代码+DesktopOAuthOneClickLaunch：允许覆盖 Vite renderer 端口；如果没有这一行，前端端口只能硬编码。
  [int]$RendererPort = 5177,
  # 新增代码+DesktopOAuthOneClickLaunch：允许覆盖 OpenAI OAuth 回调端口；如果没有这一行，浏览器认证可能回不到本地 GUI。
  [int]$CallbackPort = 1455,
  # 新增代码+DesktopOAuthOneClickLaunch：允许覆盖 bridge token；如果没有这一行，前后端无法共享自定义认证令牌。
  [string]$BridgeToken = "",
  # 新增代码+DesktopOAuthOneClickLaunch：允许覆盖 OpenAI OAuth client id；如果没有这一行，未来批准的新 client id 无法接入。
  [string]$OpenAIClientId = "",
  # 新增代码+DesktopOAuthOneClickLaunch：允许保留旧进程只报错不清理；如果没有这一行，用户无法保守排查端口占用。
  [switch]$KeepExisting
)

# 新增代码+DesktopOAuthOneClickLaunch：遇到错误立即停止；如果没有这一行，脚本可能在后端失败后继续打开错误 GUI。
$ErrorActionPreference = "Stop"
# 新增代码+DesktopOAuthOneClickLaunch：兼容不同 PowerShell 宿主读取脚本路径；如果没有这一行，某些启动方式下无法定位仓库。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path }
# 新增代码+DesktopOAuthOneClickLaunch：定位 scripts 目录；如果没有这一行，后续无法找到旧启动脚本。
$ScriptDir = Split-Path -Parent $ScriptPath
# 新增代码+DesktopOAuthOneClickLaunch：定位 apps/desktop 目录；如果没有这一行，桌面脚本无法找到 package.json。
$DesktopRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
# 新增代码+DesktopOAuthOneClickLaunch：定位仓库根目录；如果没有这一行，后端 workspace 会指向错误位置。
$Workspace = (Resolve-Path (Join-Path $DesktopRoot "..\..")).Path
# 新增代码+DesktopOAuthOneClickLaunch：复用现有后端启动脚本；如果没有这一行，bridge 链路会分叉。
$BackendScript = Join-Path $ScriptDir "start-backend.ps1"
# 新增代码+DesktopOAuthOneClickLaunch：复用现有桌面启动脚本；如果没有这一行，renderer/Electron 链路会分叉。
$DesktopScript = Join-Path $ScriptDir "start-desktop-dev.ps1"
# 新增代码+DesktopOAuthOneClickLaunch：生成 bridge base URL；如果没有这一行，前端和验收请求不知道连接哪里。
$BridgeUrl = "http://127.0.0.1:$BridgePort"
# 新增代码+DesktopOAuthOneClickLaunch：生成 renderer URL；如果没有这一行，脚本无法等待前端页面上线。
$RendererUrl = "http://127.0.0.1:$RendererPort"
# 新增代码+DesktopOAuthOneClickLaunch：确定 bridge token；如果没有这一行，GUI 请求会被 401 拒绝。
$BridgeToken = if ($BridgeToken) { $BridgeToken } elseif ($env:OPENHARNESS_GUI_BRIDGE_TOKEN) { $env:OPENHARNESS_GUI_BRIDGE_TOKEN } else { "openharness-desktop-dev-token" }
# 新增代码+DesktopOAuthOneClickLaunch：沿用当前已验证的 OpenCode 参考 client id 并允许覆盖；如果没有这一行，OAuth 官网可能无法打开。
$OpenAIClientId = if ($OpenAIClientId) { $OpenAIClientId } elseif ($env:OPENHARNESS_OPENAI_CLIENT_ID) { $env:OPENHARNESS_OPENAI_CLIENT_ID } else { "app_EMoamEEZ73f0CkXaXp7hrann" }
# 新增代码+DesktopOAuthOneClickLaunch：生成日志时间戳；如果没有这一行，多次启动日志会互相覆盖。
$LaunchStamp = Get-Date -Format "yyyyMMdd_HHmmss"
# 新增代码+DesktopOAuthOneClickLaunch：把运行日志放入系统临时目录；如果没有这一行，用户双击会污染仓库未跟踪文件。
$LogDir = Join-Path $env:TEMP "openharness-desktop-oauth-$LaunchStamp"
# 新增代码+DesktopOAuthOneClickLaunch：确保临时日志目录存在；如果没有这一行，Start-Process 重定向日志会失败。
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Get-OpenHarnessPortOwners {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，读取指定端口的监听进程；如果没有这段，脚本无法判断旧链路是否占住端口。
  param([int]$PortNumber)
  # 新增代码+DesktopOAuthOneClickLaunch：读取监听该端口的 TCP 连接；如果没有这一行，脚本无法发现端口占用。
  $connections = @(Get-NetTCPConnection -LocalPort $PortNumber -State Listen -ErrorAction SilentlyContinue)
  # 新增代码+DesktopOAuthOneClickLaunch：提取唯一进程 id；如果没有这一行，同一进程多个监听会被重复处理。
  $processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 })
  # 新增代码+DesktopOAuthOneClickLaunch：准备返回的进程信息数组；如果没有这一行，函数没有稳定返回值。
  $owners = @()
  # 新增代码+DesktopOAuthOneClickLaunch：遍历端口 owner 进程；如果没有这一段，脚本无法逐个判断是否属于 OpenHarness。
  foreach ($processId in $processIds) {
    # 新增代码+DesktopOAuthOneClickLaunch：读取进程命令行和路径；如果没有这一行，脚本无法区分旧 GUI 和其它服务。
    $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    # 新增代码+DesktopOAuthOneClickLaunch：确认进程信息仍然存在；如果没有这一行，刚退出的进程会造成空对象访问。
    if ($null -ne $owner) { $owners += $owner }
  }
  # 新增代码+DesktopOAuthOneClickLaunch：返回 owner 列表；如果没有这一行，清理函数无法工作。
  return $owners
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Get-OpenHarnessPortOwners 到此结束；如果没有这个边界说明，用户不容易看出函数范围。

function Test-OpenHarnessOwnedProcess {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，判断端口 owner 是否属于本项目旧链路；如果没有这段，脚本可能误杀无关服务。
  param([object]$ProcessInfo)
  # 新增代码+DesktopOAuthOneClickLaunch：读取进程命令行；如果没有这一行，无法识别 python/npm/electron 是否来自本项目。
  $commandLine = [string]$ProcessInfo.CommandLine
  # 新增代码+DesktopOAuthOneClickLaunch：读取进程可执行文件路径；如果没有这一行，命令行为空时缺少辅助证据。
  $executablePath = [string]$ProcessInfo.ExecutablePath
  # 新增代码+DesktopOAuthOneClickLaunch：把可搜索文本规范成小写；如果没有这一行，路径大小写会影响判断。
  $haystack = ("$commandLine $executablePath").ToLowerInvariant()
  # 新增代码+DesktopOAuthOneClickLaunch：把当前仓库路径规范成小写；如果没有这一行，脚本无法识别本仓库旧进程。
  $workspaceNeedle = $Workspace.ToLowerInvariant()
  # 新增代码+DesktopOAuthOneClickLaunch：命令行包含当前仓库时判定为本项目；如果没有这一行，本项目旧进程可能无法自动清理。
  if ($haystack.Contains($workspaceNeedle)) { return $true }
  # 新增代码+DesktopOAuthOneClickLaunch：识别 GUI bridge 后端；如果没有这一行，旧 Python bridge 可能占住 8776。
  if ($haystack.Contains("learning_agent.app.cli") -and $haystack.Contains("desktop-bridge")) { return $true }
  # 新增代码+DesktopOAuthOneClickLaunch：识别本项目 renderer dev server；如果没有这一行，旧 Vite 可能占住 5177。
  if ($haystack.Contains("vite") -and $haystack.Contains("$RendererPort")) { return $true }
  # 新增代码+DesktopOAuthOneClickLaunch：识别 Electron 桌面进程；如果没有这一行，旧桌面壳可能残留。
  if ($haystack.Contains("openharness-desktop")) { return $true }
  # 新增代码+DesktopOAuthOneClickLaunch：其余占用视为非本项目进程；如果没有这一行，脚本可能误清理用户其它服务。
  return $false
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Test-OpenHarnessOwnedProcess 到此结束；如果没有这个边界说明，用户不容易看出安全判断范围。

function Clear-OpenHarnessPorts {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，清理或拒绝端口占用；如果没有这段，旧链路会让新 GUI 连接到错误后端。
  $ports = @($BridgePort, $RendererPort, $CallbackPort)
  # 新增代码+DesktopOAuthOneClickLaunch：逐个检查端口；如果没有这一段，只能检查单个端口。
  foreach ($port in $ports) {
    # 新增代码+DesktopOAuthOneClickLaunch：读取当前端口 owner；如果没有这一行，后续不知道谁占用端口。
    $owners = @(Get-OpenHarnessPortOwners -PortNumber $port)
    # 新增代码+DesktopOAuthOneClickLaunch：逐个处理 owner；如果没有这一段，多进程占用不会被完整处理。
    foreach ($owner in $owners) {
      # 新增代码+DesktopOAuthOneClickLaunch：保守模式下直接停止；如果没有这一行，用户选择保留旧进程也会被清理。
      if ($KeepExisting) { throw "端口 $port 已被进程 $($owner.ProcessId) 占用；当前使用 -KeepExisting，脚本不会清理旧链路。" }
      # 新增代码+DesktopOAuthOneClickLaunch：拒绝清理无关服务；如果没有这一行，脚本可能误杀其它本地应用。
      if (-not (Test-OpenHarnessOwnedProcess -ProcessInfo $owner)) { throw "端口 $port 被非 OpenHarness 进程 $($owner.ProcessId) 占用：$($owner.CommandLine)" }
      # 新增代码+DesktopOAuthOneClickLaunch：告知用户正在清理旧链路；如果没有这一行，窗口可能看起来卡住。
      Write-Host "正在关闭旧 OpenHarness 进程 $($owner.ProcessId)，释放端口 $port。"
      # 新增代码+DesktopOAuthOneClickLaunch：关闭本项目旧进程；如果没有这一行，新 bridge/renderer 可能无法绑定端口。
      Stop-Process -Id ([int]$owner.ProcessId) -Force -ErrorAction SilentlyContinue
      # 新增代码+DesktopOAuthOneClickLaunch：等待端口释放；如果没有这一行，后续启动可能撞上刚关闭的 socket。
      Start-Sleep -Milliseconds 600
    }
  }
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Clear-OpenHarnessPorts 到此结束；如果没有这个边界说明，用户不容易看出清理范围。

function Wait-OpenHarnessHttpJson {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，等待本地 HTTP 接口可用；如果没有这段，脚本可能在 bridge 未就绪时继续验证。
  param([string]$Url, [hashtable]$Headers = @{}, [int]$Attempts = 40)
  # 新增代码+DesktopOAuthOneClickLaunch：按次数重试请求；如果没有这一段，慢启动场景会误报失败。
  for ($attempt = 1; $attempt -le $Attempts; $attempt += 1) {
    # 新增代码+DesktopOAuthOneClickLaunch：捕获服务尚未就绪的连接错误；如果没有这一段，第一次失败会直接终止脚本。
    try { return Invoke-RestMethod -Uri $Url -Headers $Headers -TimeoutSec 2 } catch { Start-Sleep -Milliseconds 750 }
  }
  # 新增代码+DesktopOAuthOneClickLaunch：超过重试次数后报错；如果没有这一行，失败会被误当成空结果。
  throw "等待 $Url 超时。"
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Wait-OpenHarnessHttpJson 到此结束；如果没有这个边界说明，用户不容易看出等待范围。

function Invoke-OpenHarnessPostJson {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，调用带 token 的 GUI bridge POST；如果没有这段，OAuth 验收无法创建 auth-attempt。
  param([string]$Path, [hashtable]$Body)
  # 新增代码+DesktopOAuthOneClickLaunch：准备 V2 token header；如果没有这一行，bridge 会返回 401。
  $headers = @{ "X-OpenHarness-Desktop-Token" = $BridgeToken }
  # 新增代码+DesktopOAuthOneClickLaunch：把请求体编码成 JSON；如果没有这一行，后端读不到 provider_id。
  $jsonBody = $Body | ConvertTo-Json -Depth 8
  # 新增代码+DesktopOAuthOneClickLaunch：发送 POST 并返回 payload；如果没有这一行，验收无法驱动后端状态机。
  return Invoke-RestMethod -Uri "$BridgeUrl$Path" -Method Post -Headers $headers -Body $jsonBody -ContentType "application/json" -TimeoutSec 5
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Invoke-OpenHarnessPostJson 到此结束；如果没有这个边界说明，用户不容易看出请求范围。

function Test-ProviderCatalogReady {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，验证 provider catalog 保留 OpenAI OAuth 入口；如果没有这段，脚本可能打开没有提供商能力的空壳。
  $headers = @{ "X-OpenHarness-Desktop-Token" = $BridgeToken }
  # 新增代码+DesktopOAuthOneClickLaunch：读取 provider catalog；如果没有这一行，脚本无法确认提供商加载成功。
  $catalog = Wait-OpenHarnessHttpJson -Url "$BridgeUrl/v2/gui/provider-settings/providers" -Headers $headers -Attempts 20
  # 新增代码+DesktopOAuthOneClickLaunch：定位 OpenAI provider 行；如果没有这一行，后续认证方式检查没有目标。
  $openai = @($catalog.providers | Where-Object { $_.id -eq "openai" }) | Select-Object -First 1
  # 新增代码+DesktopOAuthOneClickLaunch：缺 OpenAI 时立即失败；如果没有这一行，用户会打开无法连接 OpenAI 的 GUI。
  if ($null -eq $openai) { throw "Provider catalog 中没有 OpenAI 行。" }
  # 新增代码+DesktopOAuthOneClickLaunch：定位浏览器 OAuth 方法；如果没有这一行，脚本无法确认原界面已经恢复。
  $browserMethod = @($openai.auth_methods | Where-Object { $_.id -eq "chatgpt-browser" }) | Select-Object -First 1
  # 新增代码+DesktopOAuthOneClickLaunch：缺浏览器登录方式时失败；如果没有这一行，用户仍找不到 OAuth 官网入口。
  if ($null -eq $browserMethod) { throw "OpenAI Provider 中缺少 chatgpt-browser OAuth 方法。" }
  # 新增代码+DesktopOAuthOneClickLaunch：方法未启用时失败；如果没有这一行，按钮可能显示但不能使用。
  if (-not [bool]$browserMethod.enabled) { throw "chatgpt-browser OAuth 方法未启用。" }
  # 新增代码+DesktopOAuthOneClickLaunch：返回 catalog 供未来扩展使用；如果没有这一行，调用方无法复用验收结果。
  return $catalog
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Test-ProviderCatalogReady 到此结束；如果没有这个边界说明，用户不容易看出 provider 验收范围。

function Test-OpenAIRealOAuthAttempt {
  # 新增代码+DesktopOAuthOneClickLaunch：函数段开始，验证后端会生成真实 OpenAI OAuth URL；如果没有这段，脚本只能证明 provider 列表存在。
  $started = Invoke-OpenHarnessPostJson -Path "/v2/gui/provider-settings/auth-attempt/start" -Body @{ provider_id = "openai"; auth_method_id = "chatgpt-browser" }
  # 新增代码+DesktopOAuthOneClickLaunch：读取 attempt 对象；如果没有这一行，后续无法解析授权 URL。
  $attempt = $started.attempt
  # 新增代码+DesktopOAuthOneClickLaunch：把授权地址转成 URI；如果没有这一行，域名和 query 检查会变成脆弱字符串。
  $authUri = [System.Uri]$attempt.url
  # 新增代码+DesktopOAuthOneClickLaunch：确认授权域名是 OpenAI 官网；如果没有这一行，mock URL 也可能误过验收。
  if ($authUri.Host -ne "auth.openai.com") { throw "OpenAI OAuth URL 域名不正确：$($authUri.Host)" }
  # 新增代码+DesktopOAuthOneClickLaunch：确认当前不是 mock；如果没有这一行，假授权会误当真实链路。
  if ([string]$attempt.mode -ne "real_browser") { throw "OpenAI OAuth attempt 不是 real_browser：$($attempt.mode)" }
  # 新增代码+DesktopOAuthOneClickLaunch：确认 URL 使用脚本配置的 client id；如果没有这一行，可能连接到旧 client。
  if ([string]$attempt.url -notmatch "client_id=$([Regex]::Escape($OpenAIClientId))") { throw "OpenAI OAuth URL 未使用当前 client id。" }
  # 新增代码+DesktopOAuthOneClickLaunch：取消预验收产生的 pending attempt；如果没有这一行，用户打开设置时可能看到旧等待态。
  Invoke-OpenHarnessPostJson -Path "/v2/gui/provider-settings/auth-attempt/cancel" -Body @{ attempt_id = [string]$attempt.attempt_id } | Out-Null
  # 新增代码+DesktopOAuthOneClickLaunch：返回 attempt 摘要；如果没有这一行，调用方无法输出可审计事实。
  return $attempt
}
# 新增代码+DesktopOAuthOneClickLaunch：函数段结束，Test-OpenAIRealOAuthAttempt 到此结束；如果没有这个边界说明，用户不容易看出真实 OAuth 验收范围。

# 新增代码+DesktopOAuthOneClickLaunch：把 token 传给后端和 Electron；如果没有这一行，前后端认证令牌会不一致。
$env:OPENHARNESS_GUI_BRIDGE_TOKEN = $BridgeToken
# 新增代码+DesktopOAuthOneClickLaunch：开启真实浏览器 OAuth 模式；如果没有这一行，OpenAI 连接会回到 mock。
$env:OPENHARNESS_OPENAI_AUTH_MODE = "real_browser"
# 新增代码+DesktopOAuthOneClickLaunch：开启 Direct SSE 模型调用路径；如果没有这一行，消息窗口可能走慢路径或假回复。
$env:OPENHARNESS_OPENAI_RUNTIME = "direct_sse"
# 新增代码+RealHarnessOneClickLaunch：开启真实 GUI agent harness adapter；如果没有这一行，带 `__real_harness__` 的 GUI 验收会进入 adapter_unavailable 失败。
$env:OPENHARNESS_GUI_AGENT_RUNTIME = "real"
# 新增代码+GuiToolchainReuse：让一键启动的普通 GUI prompt 默认进入真实 Agent Mode；如果没有这一行，用户仍要输入隐藏标记才能接入 core/agent.py 和工具链路。
$env:OPENHARNESS_GUI_AGENT_DEFAULT_MODE = "agent"
# 新增代码+DesktopOAuthOneClickLaunch：强制真实 OAuth token 使用 OS 加密存储；如果没有这一行，真实 token 保存会被安全门禁阻断。
$env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted"
# 新增代码+DesktopOAuthOneClickLaunch：显式同意真实 OAuth 实验路径；如果没有这一行，后端会拒绝真实 OAuth。
$env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1"
# 新增代码+DesktopOAuthOneClickLaunch：设置当前可用的 OAuth client id；如果没有这一行，授权 URL 无法构造。
$env:OPENHARNESS_OPENAI_CLIENT_ID = $OpenAIClientId
# 新增代码+DesktopOAuthOneClickLaunch：设置 OpenAI 回调端口；如果没有这一行，网页登录后可能回调到错误端口。
$env:OPENHARNESS_OPENAI_CALLBACK_PORT = [string]$CallbackPort
# 新增代码+DesktopOAuthOneClickLaunch：让旧启动脚本把日志写到临时目录；如果没有这一行，仓库会被运行日志污染。
$env:OPENHARNESS_DESKTOP_LAUNCH_LOG_DIR = $LogDir

# 新增代码+DesktopOAuthOneClickLaunch：输出启动摘要；如果没有这一段，用户不知道脚本正在启动哪个链路。
Write-Host "OpenHarness Desktop OAuth 一键启动开始。"
Write-Host "Workspace: $Workspace"
Write-Host "Bridge: $BridgeUrl"
Write-Host "Renderer: $RendererUrl"
Write-Host "OAuth callback port: $CallbackPort"
Write-Host "Logs: $LogDir"

# 新增代码+DesktopOAuthOneClickLaunch：清理旧 OpenHarness 端口占用；如果没有这一行，新脚本可能连到旧后端。
Clear-OpenHarnessPorts
# 新增代码+DesktopOAuthOneClickLaunch：定义后端 stdout 日志；如果没有这一行，后端输出没有保存位置。
$backendOut = Join-Path $LogDir "backend_stdout.log"
# 新增代码+DesktopOAuthOneClickLaunch：定义后端 stderr 日志；如果没有这一行，后端错误没有保存位置。
$backendErr = Join-Path $LogDir "backend_stderr.log"
# 新增代码+DesktopOAuthOneClickLaunch：后台启动现有 GUI bridge；如果没有这一行，前端没有后端可连。
$backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $BackendScript, "-Workspace", $Workspace, "-Port", ([string]$BridgePort), "-Token", $BridgeToken -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru
# 新增代码+DesktopOAuthOneClickLaunch：输出后端进程号；如果没有这一行，用户无法手动结束后台 bridge。
Write-Host "GUI bridge process id: $($backendProcess.Id)"
# 新增代码+DesktopOAuthOneClickLaunch：等待轻量 health 可用；如果没有这一行，provider 验收可能抢在后端启动前执行。
Wait-OpenHarnessHttpJson -Url "$BridgeUrl/health" -Attempts 40 | Out-Null
# 新增代码+DesktopOAuthOneClickLaunch：验证 Provider catalog 已加载且包含 OpenAI OAuth；如果没有这一行，用户会打开提供商加载失败的 GUI。
Test-ProviderCatalogReady | Out-Null
# 新增代码+DesktopOAuthOneClickLaunch：验证真实 OAuth URL 指向 auth.openai.com；如果没有这一行，OAuth 官网打不开的问题可能再次漏过。
$oauthAttempt = Test-OpenAIRealOAuthAttempt
# 新增代码+DesktopOAuthOneClickLaunch：输出真实 OAuth 验收摘要；如果没有这一行，用户无法知道脚本检查了什么。
Write-Host "OpenAI OAuth verified: mode=$($oauthAttempt.mode), host=auth.openai.com"

# 新增代码+DesktopOAuthOneClickLaunch：定义桌面启动 stdout 日志；如果没有这一行，Electron 启动输出没有保存位置。
$desktopOut = Join-Path $LogDir "desktop_stdout.log"
# 新增代码+DesktopOAuthOneClickLaunch：定义桌面启动 stderr 日志；如果没有这一行，Electron 错误没有保存位置。
$desktopErr = Join-Path $LogDir "desktop_stderr.log"
# 新增代码+DesktopOAuthOneClickLaunch：后台启动现有 renderer 和 Electron；如果没有这一行，用户看不到桌面 GUI。
$desktopProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $DesktopScript, "-BridgeUrl", $BridgeUrl, "-BridgeToken", $BridgeToken -WindowStyle Hidden -RedirectStandardOutput $desktopOut -RedirectStandardError $desktopErr -PassThru
# 新增代码+DesktopOAuthOneClickLaunch：输出桌面启动器进程号；如果没有这一行，用户无法定位桌面启动链路。
Write-Host "Desktop launcher process id: $($desktopProcess.Id)"
# 新增代码+DesktopOAuthOneClickLaunch：尝试等待 renderer 页面上线；如果没有这一段，脚本可能太早声称窗口已启动。
try {
  Wait-OpenHarnessHttpJson -Url $RendererUrl -Attempts 80 | Out-Null
} catch {
  Write-Host "Renderer 等待超时，但桌面启动器仍在运行；请查看日志：$LogDir"
}
# 新增代码+DesktopOAuthOneClickLaunch：输出完成提示；如果没有这一行，用户不知道可以开始操作 GUI。
Write-Host "OpenHarness Desktop GUI 已拉起，请在可见窗口中继续连接 OpenAI。"
# 新增代码+DesktopOAuthOneClickLaunch：输出后续使用方式；如果没有这一行，用户不知道入口文件名。
Write-Host "以后手动启动：双击 start_openharness_desktop_oauth.bat。"
