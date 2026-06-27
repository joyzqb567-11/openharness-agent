param([string]$ClientId = "", [int]$BridgePort = 8796, [int]$RendererPort = 5196, [int]$CallbackPort = 1455, [switch]$KeepAlive) # 新增代码+DirectOAuthVisibleQA：声明 direct OAuth 真实 GUI 验收需要的 client id、bridge 端口、renderer 端口、OAuth callback 端口和是否保留窗口；如果没有这行，脚本无法用明确配置启动 V1C 验收。
# 新增代码+DirectOAuthVisibleQA：ClientId 必须是 OpenHarness 自有或明确授权的本地实验 OAuth client id；如果没有这行说明，用户可能误以为脚本会默认复用 OpenCode client id。
# 新增代码+DirectOAuthVisibleQA：BridgePort 控制 OpenHarness GUI bridge 后端端口；如果没有这行说明，用户不知道如何避开端口冲突。
# 新增代码+DirectOAuthVisibleQA：RendererPort 控制 Vite renderer 前端端口；如果没有这行说明，用户不知道 GUI 页面从哪里加载。
# 新增代码+DirectOAuthVisibleQA：CallbackPort 控制 localhost OAuth callback 端口，默认遵循 OpenCode 风格的 1455；如果没有这行说明，用户不知道浏览器回调必须回到本机。
# 新增代码+DirectOAuthVisibleQA：KeepAlive 用于验收后保留真实窗口；如果没有这行说明，用户不知道如何继续肉眼查看现场。

$ErrorActionPreference = "Stop" # 新增代码+DirectOAuthVisibleQA：任何启动、截图、JSON 或断言失败都立即停止；如果没有这行，坏证据可能被后续步骤掩盖。
Set-StrictMode -Version Latest # 新增代码+DirectOAuthVisibleQA：启用严格变量检查；如果没有这行，拼错变量名可能生成不可信验收 JSON。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 新增代码+DirectOAuthVisibleQA：兼容不同 PowerShell 宿主读取当前脚本路径；如果没有这行，从其它目录启动时路径推导会不稳定。
$ScriptDir = Split-Path -Parent $ScriptPath # 新增代码+DirectOAuthVisibleQA：定位 scripts 目录；如果没有这行，后续无法稳定找到仓库根和断言脚本。
$Workspace = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path # 新增代码+DirectOAuthVisibleQA：定位当前 worktree 根目录；如果没有这行，后端和证据目录可能指向错误项目。
$DesktopRoot = Join-Path $Workspace "apps\desktop" # 新增代码+DirectOAuthVisibleQA：定位桌面应用目录；如果没有这行，npm 命令找不到 package.json。
$EvidenceDir = Join-Path $Workspace "learning_agent\test\provider_settings_v2_openai_connect\direct_oauth_evidence" # 新增代码+DirectOAuthVisibleQA：定位 direct OAuth 证据目录；如果没有这行，截图和 acceptance JSON 没有固定归档位置。
$Token = "openharness-desktop-dev-token" # 新增代码+DirectOAuthVisibleQA：统一本地 GUI bridge token；如果没有这行，前端和后端可能使用不同认证值导致 401。
$BridgeUrl = "http://127.0.0.1:$BridgePort" # 新增代码+DirectOAuthVisibleQA：生成 GUI bridge URL；如果没有这行，Electron preload 无法连接后端。
$RendererUrl = "http://127.0.0.1:$RendererPort" # 新增代码+DirectOAuthVisibleQA：生成 Vite renderer URL；如果没有这行，Electron 不知道加载哪个页面。
$Processes = @() # 新增代码+DirectOAuthVisibleQA：保存本脚本启动的进程对象；如果没有这行，finally 阶段无法清理进程树。
$ResolvedClientId = if ($ClientId) { $ClientId } elseif ($env:OPENHARNESS_OPENAI_CLIENT_ID) { $env:OPENHARNESS_OPENAI_CLIENT_ID } else { "" } # 新增代码+DirectOAuthVisibleQA：从参数或环境变量读取明确 client id；如果没有这行，脚本可能在缺少 OAuth client 的情况下误启动。
if ([string]::IsNullOrWhiteSpace($ResolvedClientId)) { throw "Direct OAuth visible QA requires -ClientId or OPENHARNESS_OPENAI_CLIENT_ID. Do not use OpenCode's client id unless you explicitly choose it for a local experiment." } # 新增代码+DirectOAuthVisibleQA：缺 client id 时立即停止并说明边界；如果没有这行，direct OAuth 会在更深处失败且原因不清楚。

function Test-PortAvailable { # 新增代码+DirectOAuthVisibleQA：函数段开始，检查端口是否可绑定；如果没有这段，端口占用会变成隐蔽启动失败。
  param([int]$PortNumber) # 新增代码+DirectOAuthVisibleQA：声明待检查端口；如果没有这行，函数没有输入。
  $Listener = $null # 新增代码+DirectOAuthVisibleQA：准备临时 listener 变量；如果没有这行，finally 无法安全释放对象。
  try { # 新增代码+DirectOAuthVisibleQA：尝试绑定端口；如果没有这行，端口异常无法转成布尔结果。
    $Address = [System.Net.IPAddress]::Parse("127.0.0.1") # 新增代码+DirectOAuthVisibleQA：固定检查本机回环地址；如果没有这行，端口检查范围不清楚。
    $Listener = [System.Net.Sockets.TcpListener]::new($Address, $PortNumber) # 新增代码+DirectOAuthVisibleQA：创建临时监听器；如果没有这行，无法触碰系统端口表。
    $Listener.Start() # 新增代码+DirectOAuthVisibleQA：实际绑定端口；如果没有这行，检查不会发现占用。
    return $true # 新增代码+DirectOAuthVisibleQA：绑定成功说明端口可用；如果没有这行，可用端口会被误判。
  } catch { # 新增代码+DirectOAuthVisibleQA：捕获绑定失败；如果没有这行，占用端口会抛复杂异常。
    return $false # 新增代码+DirectOAuthVisibleQA：绑定失败说明端口不可用；如果没有这行，调用方无法提前报错。
  } finally { # 新增代码+DirectOAuthVisibleQA：释放临时 listener；如果没有这行，端口检查本身可能占住端口。
    if ($null -ne $Listener) { # 新增代码+DirectOAuthVisibleQA：确认 listener 已创建；如果没有这行，Stop 可能访问空对象。
      $Listener.Stop() # 新增代码+DirectOAuthVisibleQA：停止临时监听器；如果没有这行，真正服务可能无法绑定端口。
    } # 新增代码+DirectOAuthVisibleQA：listener 释放判断结束；如果没有这行，PowerShell 条件块不完整。
  } # 新增代码+DirectOAuthVisibleQA：端口检查 finally 结束；如果没有这行，try/catch/finally 语法不完整。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Test-PortAvailable 到此结束；如果没有这行，函数语法不完整。

function Wait-PortOpen { # 新增代码+DirectOAuthVisibleQA：函数段开始，等待服务监听端口；如果没有这段，后续 GUI 或 callback 连接可能太早发出。
  param([int]$PortNumber, [string]$Name) # 新增代码+DirectOAuthVisibleQA：声明端口和服务名；如果没有这行，超时错误不清楚。
  for ($Attempt = 0; $Attempt -lt 100; $Attempt += 1) { # 新增代码+DirectOAuthVisibleQA：最多等待约 50 秒；如果没有这行，慢启动会过早失败或无限等待。
    if (-not (Test-PortAvailable -PortNumber $PortNumber)) { # 新增代码+DirectOAuthVisibleQA：端口不可绑定说明服务已经监听；如果没有这行，无法判断启动成功。
      return # 新增代码+DirectOAuthVisibleQA：服务已监听后返回；如果没有这行，会继续等到超时。
    } # 新增代码+DirectOAuthVisibleQA：端口打开判断结束；如果没有这行，条件块语法不完整。
    Start-Sleep -Milliseconds 500 # 新增代码+DirectOAuthVisibleQA：短暂等待再重试；如果没有这行，会忙等浪费 CPU。
  } # 新增代码+DirectOAuthVisibleQA：等待循环结束；如果没有这行，for 循环语法不完整。
  throw "$Name did not open port $PortNumber." # 新增代码+DirectOAuthVisibleQA：超时后抛出清楚错误；如果没有这行，失败位置会更模糊。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Wait-PortOpen 到此结束；如果没有这行，函数语法不完整。

function Stop-ProcessTree { # 新增代码+DirectOAuthVisibleQA：函数段开始，递归停止进程树；如果没有这段，npm、Vite、Electron 子进程可能残留。
  param([int]$ProcessId) # 新增代码+DirectOAuthVisibleQA：声明根进程 id；如果没有这行，函数不知道停止谁。
  $Children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ProcessId } # 新增代码+DirectOAuthVisibleQA：查找子进程；如果没有这行，只停父进程会留下子进程。
  foreach ($Child in $Children) { # 新增代码+DirectOAuthVisibleQA：遍历子进程；如果没有这行，递归清理不会执行。
    Stop-ProcessTree -ProcessId ([int]$Child.ProcessId) # 新增代码+DirectOAuthVisibleQA：递归停止子进程；如果没有这行，孙进程可能残留。
  } # 新增代码+DirectOAuthVisibleQA：子进程遍历结束；如果没有这行，foreach 语法不完整。
  $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue # 新增代码+DirectOAuthVisibleQA：读取当前进程；如果没有这行，已退出进程会抛错。
  if ($null -ne $Process) { # 新增代码+DirectOAuthVisibleQA：确认进程仍存在；如果没有这行，Stop-Process 可能报错。
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue # 新增代码+DirectOAuthVisibleQA：强制停止进程；如果没有这行，端口可能残留占用。
  } # 新增代码+DirectOAuthVisibleQA：停止当前进程判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Stop-ProcessTree 到此结束；如果没有这行，函数语法不完整。

function Save-FullScreenShot { # 新增代码+DirectOAuthVisibleQA：函数段开始，保存当前屏幕截图；如果没有这段，真实可见 GUI 验收没有图片证据。
  param([string]$FileName) # 新增代码+DirectOAuthVisibleQA：声明截图文件名；如果没有这行，函数不知道保存目标。
  Add-Type -AssemblyName System.Windows.Forms # 新增代码+DirectOAuthVisibleQA：加载 Windows Forms 获取屏幕尺寸；如果没有这行，无法读取主屏幕边界。
  Add-Type -AssemblyName System.Drawing # 新增代码+DirectOAuthVisibleQA：加载 Drawing 用于截图；如果没有这行，无法创建 Bitmap。
  $Bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds # 新增代码+DirectOAuthVisibleQA：读取主屏幕区域；如果没有这行，截图范围不明确。
  $Bitmap = [System.Drawing.Bitmap]::new($Bounds.Width, $Bounds.Height) # 新增代码+DirectOAuthVisibleQA：创建截图画布；如果没有这行，没有图片容器。
  $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap) # 新增代码+DirectOAuthVisibleQA：创建绘图上下文；如果没有这行，无法从屏幕拷贝像素。
  try { # 新增代码+DirectOAuthVisibleQA：保护截图资源释放；如果没有这行，异常时 Bitmap 和 Graphics 可能泄漏。
    $Graphics.CopyFromScreen($Bounds.Location, [System.Drawing.Point]::Empty, $Bounds.Size) # 新增代码+DirectOAuthVisibleQA：把屏幕像素复制到 Bitmap；如果没有这行，截图会是空白。
    $Bitmap.Save((Join-Path $EvidenceDir $FileName), [System.Drawing.Imaging.ImageFormat]::Png) # 新增代码+DirectOAuthVisibleQA：保存 PNG 文件；如果没有这行，截图不会落盘。
  } finally { # 新增代码+DirectOAuthVisibleQA：释放图形资源；如果没有这行，多次截图可能占用句柄。
    $Graphics.Dispose() # 新增代码+DirectOAuthVisibleQA：释放绘图上下文；如果没有这行，GDI 资源可能泄漏。
    $Bitmap.Dispose() # 新增代码+DirectOAuthVisibleQA：释放位图对象；如果没有这行，图片内存可能残留。
  } # 新增代码+DirectOAuthVisibleQA：截图资源释放结束；如果没有这行，try/finally 语法不完整。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Save-FullScreenShot 到此结束；如果没有这行，函数语法不完整。

function Capture-Step { # 新增代码+DirectOAuthVisibleQA：函数段开始，等待用户肉眼确认并截图；如果没有这段，真实 OAuth 的人工步骤没有稳定证据。
  param([string]$Prompt, [string]$FileName) # 新增代码+DirectOAuthVisibleQA：声明提示文本和截图文件名；如果没有这行，函数没有输入。
  Read-Host "$Prompt 完成后按 Enter 截图" | Out-Null # 新增代码+DirectOAuthVisibleQA：暂停等待用户完成浏览器或 GUI 操作；如果没有这行，脚本可能截到错误状态。
  Save-FullScreenShot -FileName $FileName # 新增代码+DirectOAuthVisibleQA：保存当前屏幕截图；如果没有这行，该验收步骤没有图片证据。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Capture-Step 到此结束；如果没有这行，函数语法不完整。

function Get-BridgeJson { # 新增代码+DirectOAuthVisibleQA：函数段开始，读取 GUI bridge JSON 端点；如果没有这段，acceptance JSON 只能手工填写。
  param([string]$Path) # 新增代码+DirectOAuthVisibleQA：声明请求路径；如果没有这行，函数不知道请求哪个端点。
  return Invoke-RestMethod -Method Get -Uri "$BridgeUrl$Path" -Headers @{ "X-OpenHarness-Desktop-Token" = $Token } # 新增代码+DirectOAuthVisibleQA：发送带 token 的 GET 请求；如果没有这行，后端会返回 401 或没有数据。
} # 新增代码+DirectOAuthVisibleQA：函数段结束，Get-BridgeJson 到此结束；如果没有这行，函数语法不完整。

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null # 新增代码+DirectOAuthVisibleQA：确保证据目录存在；如果没有这行，截图和 JSON 写入会失败。
foreach ($Port in @($BridgePort, $RendererPort, $CallbackPort)) { # 新增代码+DirectOAuthVisibleQA：逐个检查 bridge、renderer、callback 端口；如果没有这行，端口占用会在更深处失败。
  if (-not (Test-PortAvailable -PortNumber $Port)) { throw "Port $Port is occupied before Direct OAuth visible QA starts." } # 新增代码+DirectOAuthVisibleQA：发现端口占用时立即停止；如果没有这行，OAuth callback 或 GUI 启动错误会很难排查。
} # 新增代码+DirectOAuthVisibleQA：端口检查循环结束；如果没有这行，foreach 语法不完整。

try { # 新增代码+DirectOAuthVisibleQA：启动和验收主流程开始；如果没有这段，finally 无法可靠清理进程。
  $env:OPENHARNESS_OPENAI_AUTH_MODE = "direct_oauth" # 新增代码+DirectOAuthVisibleQA：启用 experimental direct OAuth 路径；如果没有这行，provider 会走 codex_cli 或 mock 而不是 V1C。
  $env:OPENHARNESS_OPENAI_EXPERIMENTAL = "1" # 新增代码+DirectOAuthVisibleQA：显式打开实验开关；如果没有这行，安全配置会阻止 direct OAuth。
  $env:OPENHARNESS_PROVIDER_SECRET_STORE = "os_encrypted" # 新增代码+DirectOAuthVisibleQA：要求 OS 加密 token store；如果没有这行，direct OAuth 会因为不安全存储被拒绝。
  $env:OPENHARNESS_OPENAI_CLIENT_ID = $ResolvedClientId # 新增代码+DirectOAuthVisibleQA：传入明确 client id；如果没有这行，OAuth authorize URL 无法构造。
  $env:OPENHARNESS_OPENAI_OAUTH_CALLBACK_PORT = [string]$CallbackPort # 新增代码+DirectOAuthVisibleQA：传入 callback 端口；如果没有这行，GUI attempt 和浏览器回调端口可能不一致。
  $env:OPENHARNESS_GUI_MODEL_MODE = "real" # 新增代码+DirectOAuthVisibleQA：强制主聊天走 real adapter；如果没有这行，模型回答可能退回 fake。
  $Backend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Workspace "apps\desktop\scripts\start-backend.ps1"), "-Workspace", $Workspace, "-Port", "$BridgePort", "-Token", $Token -WorkingDirectory $Workspace -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "backend_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "backend_stderr.log") -PassThru # 新增代码+DirectOAuthVisibleQA：后台启动 GUI bridge；如果没有这行，Electron 没有 provider 和聊天后端。
  $Processes += $Backend # 新增代码+DirectOAuthVisibleQA：记录 backend 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $BridgePort -Name "GUI bridge" # 新增代码+DirectOAuthVisibleQA：等待 bridge 监听；如果没有这行，renderer 会先遇到离线状态。
  Set-Location $DesktopRoot # 新增代码+DirectOAuthVisibleQA：切换到桌面目录；如果没有这行，npm 命令找不到桌面 package.json。
  npm run build:main # 新增代码+DirectOAuthVisibleQA：构建 Electron main/preload；如果没有这行，Electron 可能加载旧主进程。
  $Renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer", "--", "--port", "$RendererPort" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "renderer_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "renderer_stderr.log") -PassThru # 新增代码+DirectOAuthVisibleQA：后台启动 Vite renderer；如果没有这行，Electron 没有前端页面。
  $Processes += $Renderer # 新增代码+DirectOAuthVisibleQA：记录 renderer 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $RendererPort -Name "Vite renderer" # 新增代码+DirectOAuthVisibleQA：等待 renderer 监听；如果没有这行，Electron 可能白屏。
  $env:OPENHARNESS_GUI_BRIDGE_URL = $BridgeUrl # 新增代码+DirectOAuthVisibleQA：把 bridge URL 传给 Electron；如果没有这行，preload 无法连接后端。
  $env:OPENHARNESS_GUI_BRIDGE_TOKEN = $Token # 新增代码+DirectOAuthVisibleQA：把 bridge token 传给 Electron；如果没有这行，GUI 请求会 401。
  $env:OPENHARNESS_DESKTOP_DEV_URL = $RendererUrl # 新增代码+DirectOAuthVisibleQA：把 renderer URL 传给 Electron；如果没有这行，Electron 会加载生产 HTML。
  $Electron = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "start" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "electron_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "electron_stderr.log") -PassThru # 新增代码+DirectOAuthVisibleQA：启动真实可见 Electron 窗口；如果没有这行，无法肉眼验收 direct OAuth GUI。
  $Processes += $Electron # 新增代码+DirectOAuthVisibleQA：记录 Electron 进程；如果没有这行，清理阶段无法停止它。
  Start-Sleep -Seconds 5 # 新增代码+DirectOAuthVisibleQA：给窗口加载时间；如果没有这行，用户提示可能早于界面出现。
  Capture-Step -Prompt "请在 OpenHarness Desktop 中打开 设置 -> 提供商 -> OpenAI -> 连接，选择 ChatGPT Pro/Plus (browser)，在浏览器完成 OpenAI 授权并看到 Authorization Successful" -FileName "direct_oauth_login_success.png" # 新增代码+DirectOAuthVisibleQA：捕获浏览器回调成功后的肉眼证据；如果没有这行，direct OAuth 登录成功没有截图证明。
  Capture-Step -Prompt "请回到 OpenHarness Desktop 设置 -> 提供商，确认 OpenAI 显示 direct OAuth experimental 已连接" -FileName "direct_oauth_provider_connected.png" # 新增代码+DirectOAuthVisibleQA：捕获 provider connected 状态；如果没有这行，GUI 连接状态没有图片证据。
  Capture-Step -Prompt "请关闭设置，在主聊天发送一句真实模型测试 prompt，并等待回答完成" -FileName "direct_oauth_model_answer.png" # 新增代码+DirectOAuthVisibleQA：捕获 direct OAuth 真实模型回答；如果没有这行，主聊天真实回答没有图片证据。
  Capture-Step -Prompt "请打开右侧状态/事件流面板，让 turn_started/message_delta/message_completed 可见" -FileName "direct_oauth_event_stream.png" # 新增代码+DirectOAuthVisibleQA：捕获事件流证据；如果没有这行，状态流没有图片证据。
  $ProvidersPayload = Get-BridgeJson -Path "/v2/gui/provider-settings/providers" # 新增代码+DirectOAuthVisibleQA：读取 provider catalog；如果没有这行，acceptance JSON 无法证明 provider_source。
  $EventsPayload = Get-BridgeJson -Path "/v2/gui/events?limit=200" # 新增代码+DirectOAuthVisibleQA：读取最近事件流；如果没有这行，acceptance JSON 无法证明 real adapter 事件。
  $OpenAIProvider = $ProvidersPayload.providers | Where-Object { $_.id -eq "openai" } | Select-Object -First 1 # 新增代码+DirectOAuthVisibleQA：定位 OpenAI provider；如果没有这行，provider source 无法提取。
  $EventKinds = @($EventsPayload.events | ForEach-Object { if ($_.event_type) { [string]$_.event_type } else { [string]$_.kind } }) # 新增代码+DirectOAuthVisibleQA：兼容 event_type 和 kind 两种事件字段；如果没有这行，真实事件可能被误判缺失。
  $TurnStarted = $EventsPayload.events | Where-Object { (($_.event_type) -eq "turn_started") -or (($_.kind) -eq "turn_started") } | Select-Object -Last 1 # 新增代码+DirectOAuthVisibleQA：读取最后一个 turn_started；如果没有这行，adapter mode 无法提取。
  $EventsJson = $EventsPayload | ConvertTo-Json -Depth 20 # 新增代码+DirectOAuthVisibleQA：序列化事件用于 fake 和 secret 扫描；如果没有这行，检测没有文本来源。
  $FakeTextDetected = $EventsJson -match "fake streaming" # 新增代码+DirectOAuthVisibleQA：检查是否出现 fake streaming；如果没有这行，模拟回复可能混入验收。
  $SecretLeakDetected = $EventsJson -match "access_token|refresh_token|id_token|secret_ref|api_key\s*[:=]|Bearer\s+|sk-[A-Za-z0-9]{12,}" # 新增代码+DirectOAuthVisibleQA：检查事件是否含敏感字段或密钥形态；如果没有这行，证据泄密不会阻断。
  $AdapterMode = if ($null -ne $TurnStarted -and $null -ne $TurnStarted.payload.mode) { [string]$TurnStarted.payload.mode } else { "unknown" } # 新增代码+DirectOAuthVisibleQA：读取 adapter mode；如果没有这行，不能证明主聊天走 real。
  $ProviderSource = if ($null -ne $OpenAIProvider) { [string]$OpenAIProvider.source } else { "missing" } # 新增代码+DirectOAuthVisibleQA：读取 provider source；如果没有这行，不能证明来自 direct OAuth。
  $HasRequiredEvents = ($EventKinds -contains "turn_started") -and ($EventKinds -contains "message_delta") -and ($EventKinds -contains "message_completed") # 新增代码+DirectOAuthVisibleQA：检查真实回答核心事件；如果没有这行，事件流不完整也可能通过。
  $Acceptance = [ordered]@{ ok = (($ProviderSource -eq "direct_oauth_experimental") -and ($AdapterMode -eq "real") -and $HasRequiredEvents -and (-not $FakeTextDetected) -and (-not $SecretLeakDetected)); provider_source = $ProviderSource; adapter_mode = $AdapterMode; event_kinds = $EventKinds; fake_text_detected = [bool]$FakeTextDetected; secret_leak_detected = [bool]$SecretLeakDetected } # 新增代码+DirectOAuthVisibleQA：构造 direct OAuth acceptance JSON；如果没有这行，release gate 没有机器可读证据。
  $Acceptance | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path (Join-Path $EvidenceDir "direct_oauth_acceptance.json") # 新增代码+DirectOAuthVisibleQA：写入 direct OAuth acceptance JSON；如果没有这行，assert_direct_oauth_acceptance.ps1 没有输入。
  & (Join-Path $ScriptDir "assert_direct_oauth_acceptance.ps1") # 新增代码+DirectOAuthVisibleQA：立即运行 direct OAuth 验收门禁；如果没有这行，截图或 JSON 不合格可能不被发现。
} finally { # 新增代码+DirectOAuthVisibleQA：清理流程开始；如果没有这段，失败后后台进程会残留。
  if (-not $KeepAlive) { # 新增代码+DirectOAuthVisibleQA：默认清理，KeepAlive 时保留窗口；如果没有这行，用户无法选择继续查看现场。
    foreach ($Process in $Processes) { # 新增代码+DirectOAuthVisibleQA：遍历本轮启动进程；如果没有这行，无法逐个清理。
      if ($null -ne $Process) { # 新增代码+DirectOAuthVisibleQA：确认进程对象存在；如果没有这行，空值会报错。
        Stop-ProcessTree -ProcessId $Process.Id # 新增代码+DirectOAuthVisibleQA：停止进程树；如果没有这行，npm/Electron/Vite 可能残留。
      } # 新增代码+DirectOAuthVisibleQA：进程对象判断结束；如果没有这行，条件块语法不完整。
    } # 新增代码+DirectOAuthVisibleQA：进程清理循环结束；如果没有这行，foreach 语法不完整。
  } # 新增代码+DirectOAuthVisibleQA：KeepAlive 判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+DirectOAuthVisibleQA：主流程结束；如果没有这行，try/finally 语法不完整。

