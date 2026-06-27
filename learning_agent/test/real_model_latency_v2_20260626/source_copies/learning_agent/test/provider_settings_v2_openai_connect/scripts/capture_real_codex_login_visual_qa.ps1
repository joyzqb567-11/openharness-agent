param([int]$BridgePort = 8776, [int]$RendererPort = 5177, [switch]$KeepAlive) # 新增代码+真实模型可见验收：声明 bridge、renderer 端口和是否保留窗口；如果没有这行，脚本只能使用硬编码且不方便人工验收。
# 新增代码+真实模型可见验收：BridgePort 控制 GUI bridge 后端端口；如果没有这行注释，用户不清楚后端端口用途。
# 新增代码+真实模型可见验收：RendererPort 控制 Vite 前端端口；如果没有这行注释，用户不清楚前端端口用途。
# 新增代码+真实模型可见验收：KeepAlive 会在脚本结束后保留 Electron 窗口；如果没有这行注释，用户不清楚怎么继续观察界面。

$ErrorActionPreference = "Stop" # 新增代码+真实模型可见验收：遇到启动或截图失败立即停止；如果没有这行，失败可能被后续 JSON 生成掩盖。
Set-StrictMode -Version Latest # 新增代码+真实模型可见验收：启用严格变量检查；如果没有这行，拼错变量名可能导致证据不完整。
$ScriptPath = $MyInvocation.MyCommand.Path # 修改代码+真实模型可见验收：使用 MyInvocation 定位当前脚本路径；如果没有这行，截图脚本无法推导仓库根。
$ScriptDir = Split-Path -Parent $ScriptPath # 新增代码+真实模型可见验收：定位 scripts 目录；如果没有这行，无法推导仓库根。
$Workspace = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path # 新增代码+真实模型可见验收：定位当前 worktree 根目录；如果没有这行，启动命令会找错项目。
$DesktopRoot = Join-Path $Workspace "apps\desktop" # 新增代码+真实模型可见验收：定位桌面应用目录；如果没有这行，npm 命令找不到 package.json。
$EvidenceDir = Join-Path $Workspace "learning_agent\test\provider_settings_v2_openai_connect\real_codex_login_evidence" # 新增代码+真实模型可见验收：定位真实 Codex 登录证据目录；如果没有这行，截图和 JSON 没有固定位置。
$Token = "openharness-desktop-dev-token" # 新增代码+真实模型可见验收：统一使用开发 token；如果没有这行，前端和后端认证值可能不一致。
$BridgeUrl = "http://127.0.0.1:$BridgePort" # 新增代码+真实模型可见验收：生成 bridge URL；如果没有这行，Electron preload 无法连接后端。
$RendererUrl = "http://127.0.0.1:$RendererPort" # 新增代码+真实模型可见验收：生成 renderer URL；如果没有这行，Electron 不知道加载哪个 Vite 页面。
$Processes = @() # 新增代码+真实模型可见验收：保存本脚本启动的进程；如果没有这行，finally 阶段无法清理进程树。

function Test-PortAvailable { # 新增代码+真实模型可见验收：函数段开始，检查端口是否可绑定；如果没有这段，端口占用会变成隐蔽启动失败。
  param([int]$PortNumber) # 新增代码+真实模型可见验收：声明待检查端口；如果没有这行，函数没有输入。
  $Listener = $null # 新增代码+真实模型可见验收：准备临时监听器变量；如果没有这行，finally 无法安全释放。
  try { # 新增代码+真实模型可见验收：尝试绑定端口；如果没有这行，端口异常无法转成布尔值。
    $Address = [System.Net.IPAddress]::Parse("127.0.0.1") # 新增代码+真实模型可见验收：固定检查本机回环地址；如果没有这行，检查范围不清楚。
    $Listener = [System.Net.Sockets.TcpListener]::new($Address, $PortNumber) # 新增代码+真实模型可见验收：创建临时监听器；如果没有这行，无法检测端口占用。
    $Listener.Start() # 新增代码+真实模型可见验收：实际绑定端口；如果没有这行，检查不会触碰系统端口表。
    return $true # 新增代码+真实模型可见验收：绑定成功表示端口可用；如果没有这行，可用端口会被误判。
  } catch { # 新增代码+真实模型可见验收：捕获端口绑定失败；如果没有这行，占用端口会抛复杂异常。
    return $false # 新增代码+真实模型可见验收：绑定失败表示端口不可用；如果没有这行，调用方无法提前失败。
  } finally { # 新增代码+真实模型可见验收：释放临时监听器；如果没有这行，端口检查本身可能占住端口。
    if ($null -ne $Listener) { # 新增代码+真实模型可见验收：确认监听器存在；如果没有这行，Stop 可能访问空对象。
      $Listener.Stop() # 新增代码+真实模型可见验收：停止临时监听器；如果没有这行，真正服务可能无法绑定端口。
    } # 新增代码+真实模型可见验收：监听器释放判断结束；如果没有这行，PowerShell 条件块不完整。
  } # 新增代码+真实模型可见验收：finally 结束；如果没有这行，try/catch/finally 语法不完整。
} # 新增代码+真实模型可见验收：函数段结束，Test-PortAvailable 到此结束；如果没有这行，函数语法不完整。

function Wait-PortOpen { # 新增代码+真实模型可见验收：函数段开始，等待服务监听端口；如果没有这段，后续请求可能太早发出。
  param([int]$PortNumber, [string]$Name) # 新增代码+真实模型可见验收：声明端口和服务名；如果没有这行，超时错误不清楚。
  for ($Attempt = 0; $Attempt -lt 80; $Attempt += 1) { # 新增代码+真实模型可见验收：最多等待约 40 秒；如果没有这行，慢启动会过早失败。
    if (-not (Test-PortAvailable -PortNumber $PortNumber)) { # 新增代码+真实模型可见验收：端口不可绑定说明服务已监听；如果没有这行，无法判断成功。
      return # 新增代码+真实模型可见验收：服务已监听后返回；如果没有这行，会继续等到超时。
    } # 新增代码+真实模型可见验收：端口打开判断结束；如果没有这行，条件块语法不完整。
    Start-Sleep -Milliseconds 500 # 新增代码+真实模型可见验收：短暂等待后重试；如果没有这行，会忙等。
  } # 新增代码+真实模型可见验收：等待循环结束；如果没有这行，for 语法不完整。
  throw "$Name did not open port $PortNumber." # 新增代码+真实模型可见验收：超时后抛清楚错误；如果没有这行，失败位置会更模糊。
} # 新增代码+真实模型可见验收：函数段结束，Wait-PortOpen 到此结束；如果没有这行，函数语法不完整。

function Stop-ProcessTree { # 新增代码+真实模型可见验收：函数段开始，递归停止进程树；如果没有这段，npm/Electron 子进程可能残留。
  param([int]$ProcessId) # 新增代码+真实模型可见验收：声明根进程 id；如果没有这行，函数不知道停止谁。
  $Children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ProcessId } # 新增代码+真实模型可见验收：查找子进程；如果没有这行，只停父进程会残留子进程。
  foreach ($Child in $Children) { # 新增代码+真实模型可见验收：遍历子进程；如果没有这行，递归清理不会执行。
    Stop-ProcessTree -ProcessId ([int]$Child.ProcessId) # 新增代码+真实模型可见验收：递归停止子进程；如果没有这行，孙进程可能残留。
  } # 新增代码+真实模型可见验收：子进程遍历结束；如果没有这行，foreach 语法不完整。
  $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue # 新增代码+真实模型可见验收：读取当前进程；如果没有这行，已退出进程会抛错。
  if ($null -ne $Process) { # 新增代码+真实模型可见验收：确认进程仍存在；如果没有这行，Stop-Process 可能报错。
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue # 新增代码+真实模型可见验收：强制停止进程；如果没有这行，端口可能残留占用。
  } # 新增代码+真实模型可见验收：停止当前进程判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+真实模型可见验收：函数段结束，Stop-ProcessTree 到此结束；如果没有这行，函数语法不完整。

function Save-FullScreenShot { # 新增代码+真实模型可见验收：函数段开始，保存当前屏幕截图；如果没有这段，人工可见界面没有图片证据。
  param([string]$FileName) # 新增代码+真实模型可见验收：声明截图文件名；如果没有这行，函数不知道保存目标。
  Add-Type -AssemblyName System.Windows.Forms # 新增代码+真实模型可见验收：加载 Windows Forms 获取屏幕尺寸；如果没有这行，无法读取主屏幕边界。
  Add-Type -AssemblyName System.Drawing # 新增代码+真实模型可见验收：加载 Drawing 用于截图；如果没有这行，无法创建 Bitmap。
  $Bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds # 新增代码+真实模型可见验收：读取主屏幕区域；如果没有这行，截图范围不明确。
  $Bitmap = [System.Drawing.Bitmap]::new($Bounds.Width, $Bounds.Height) # 新增代码+真实模型可见验收：创建截图画布；如果没有这行，没有图片容器。
  $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap) # 新增代码+真实模型可见验收：创建绘图上下文；如果没有这行，无法从屏幕拷贝像素。
  try { # 新增代码+真实模型可见验收：保护截图资源释放；如果没有这行，异常时 Bitmap/Graphics 可能泄漏。
    $Graphics.CopyFromScreen($Bounds.Location, [System.Drawing.Point]::Empty, $Bounds.Size) # 新增代码+真实模型可见验收：把屏幕像素复制到 Bitmap；如果没有这行，截图是空白。
    $Bitmap.Save((Join-Path $EvidenceDir $FileName), [System.Drawing.Imaging.ImageFormat]::Png) # 新增代码+真实模型可见验收：保存 PNG 文件；如果没有这行，截图不会落盘。
  } finally { # 新增代码+真实模型可见验收：释放图形资源；如果没有这行，多次截图可能占用句柄。
    $Graphics.Dispose() # 新增代码+真实模型可见验收：释放绘图上下文；如果没有这行，GDI 资源可能泄漏。
    $Bitmap.Dispose() # 新增代码+真实模型可见验收：释放位图对象；如果没有这行，图片内存可能残留。
  } # 新增代码+真实模型可见验收：finally 结束；如果没有这行，try/finally 语法不完整。
} # 新增代码+真实模型可见验收：函数段结束，Save-FullScreenShot 到此结束；如果没有这行，函数语法不完整。

function Capture-Step { # 新增代码+真实模型可见验收：函数段开始，提示用户确认界面并截图；如果没有这段，人工步骤和截图会散落重复。
  param([string]$Prompt, [string]$FileName) # 新增代码+真实模型可见验收：声明提示文本和文件名；如果没有这行，函数没有输入。
  Read-Host "$Prompt 完成后按 Enter 截图" | Out-Null # 新增代码+真实模型可见验收：等待用户肉眼确认真实 GUI 状态；如果没有这行，脚本可能截到错误界面。
  Save-FullScreenShot -FileName $FileName # 新增代码+真实模型可见验收：保存当前屏幕截图；如果没有这行，该步骤没有图片证据。
} # 新增代码+真实模型可见验收：函数段结束，Capture-Step 到此结束；如果没有这行，函数语法不完整。

function Get-BridgeJson { # 新增代码+真实模型可见验收：函数段开始，读取 bridge JSON 端点；如果没有这段，acceptance JSON 只能手写。
  param([string]$Path) # 新增代码+真实模型可见验收：声明端点路径；如果没有这行，函数不知道请求哪个 URL。
  return Invoke-RestMethod -Method Get -Uri "$BridgeUrl$Path" -Headers @{ "X-OpenHarness-Desktop-Token" = $Token } # 新增代码+真实模型可见验收：发送带 token 的 GET 请求；如果没有这行，后端会返回 401 或没有数据。
} # 新增代码+真实模型可见验收：函数段结束，Get-BridgeJson 到此结束；如果没有这行，函数语法不完整。

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null # 新增代码+真实模型可见验收：确保证据目录存在；如果没有这行，截图和 JSON 写入会失败。
if (-not (Test-PortAvailable -PortNumber $BridgePort)) { throw "Bridge port $BridgePort is occupied." } # 新增代码+真实模型可见验收：检查 bridge 端口；如果没有这行，后端启动失败不清楚。
if (-not (Test-PortAvailable -PortNumber $RendererPort)) { throw "Renderer port $RendererPort is occupied." } # 新增代码+真实模型可见验收：检查 renderer 端口；如果没有这行，Vite 启动失败不清楚。

try { # 新增代码+真实模型可见验收：启动和验收主流程开始；如果没有这段，finally 无法可靠清理。
  $Backend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Workspace "apps\desktop\scripts\start-backend.ps1"), "-Workspace", $Workspace, "-Port", "$BridgePort", "-Token", $Token -WorkingDirectory $Workspace -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "backend_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "backend_stderr.log") -PassThru # 新增代码+真实模型可见验收：后台启动 GUI bridge；如果没有这行，Electron 没有后端数据源。
  $Processes += $Backend # 新增代码+真实模型可见验收：记录 backend 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $BridgePort -Name "GUI bridge" # 新增代码+真实模型可见验收：等待 bridge 端口打开；如果没有这行，renderer 会先遇到离线。
  Set-Location $DesktopRoot # 新增代码+真实模型可见验收：切换到桌面目录；如果没有这行，npm 命令找不到 package.json。
  npm run build:main # 新增代码+真实模型可见验收：构建 Electron main/preload；如果没有这行，Electron 可能加载旧主进程。
  $Renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer", "--", "--port", "$RendererPort" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "renderer_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "renderer_stderr.log") -PassThru # 新增代码+真实模型可见验收：后台启动 Vite renderer；如果没有这行，Electron 没有前端页面。
  $Processes += $Renderer # 新增代码+真实模型可见验收：记录 renderer 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $RendererPort -Name "Vite renderer" # 新增代码+真实模型可见验收：等待 renderer 端口打开；如果没有这行，Electron 可能白屏。
  $env:OPENHARNESS_GUI_BRIDGE_URL = $BridgeUrl # 新增代码+真实模型可见验收：把 bridge URL 传给 Electron；如果没有这行，preload 无法连接后端。
  $env:OPENHARNESS_GUI_BRIDGE_TOKEN = $Token # 新增代码+真实模型可见验收：把 bridge token 传给 Electron；如果没有这行，GUI 请求会 401。
  $env:OPENHARNESS_DESKTOP_DEV_URL = $RendererUrl # 新增代码+真实模型可见验收：把 renderer URL 传给 Electron；如果没有这行，Electron 会加载生产 HTML。
  $env:OPENHARNESS_OPENAI_AUTH_MODE = "codex_cli" # 新增代码+真实模型可见验收：启用官方 Codex CLI 登录状态作为 provider 来源；如果没有这行，设置页可能仍显示 mock auth。
  $env:OPENHARNESS_GUI_MODEL_MODE = "real" # 新增代码+真实模型可见验收：强制主聊天走真实模型 adapter；如果没有这行，主聊天可能保持 fake。
  $Electron = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "start" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "electron_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "electron_stderr.log") -PassThru # 新增代码+真实模型可见验收：启动真实可见 Electron 窗口；如果没有这行，无法肉眼验收 GUI。
  $Processes += $Electron # 新增代码+真实模型可见验收：记录 Electron 进程；如果没有这行，清理阶段无法停止它。
  Start-Sleep -Seconds 5 # 新增代码+真实模型可见验收：给窗口加载时间；如果没有这行，第一步提示可能早于界面出现。
  Capture-Step -Prompt "请在 OpenHarness Desktop 中打开 设置 -> 提供商 -> OpenAI -> 连接，并停在登录方式选择界面" -FileName "codex_login_method_picker.png" # 新增代码+真实模型可见验收：捕获登录方式选择界面；如果没有这行，method picker 没有肉眼证据。
  Capture-Step -Prompt "请选择 ChatGPT Pro/Plus (browser)，让界面停在等待浏览器授权状态" -FileName "codex_login_waiting.png" # 新增代码+真实模型可见验收：捕获 Codex 登录等待界面；如果没有这行，OAuth 等待页没有肉眼证据。
  Capture-Step -Prompt "完成浏览器中的 Codex/ChatGPT 登录后，回到 provider 列表并确认 OpenAI 已连接" -FileName "codex_provider_connected.png" # 新增代码+真实模型可见验收：捕获 provider connected 状态；如果没有这行，连接完成没有截图证据。
  Capture-Step -Prompt "关闭设置，在主聊天发送：请用一句话说明你是真实模型连接还是模拟回复，并等待回答完成" -FileName "codex_real_model_answer.png" # 新增代码+真实模型可见验收：捕获真实模型回答；如果没有这行，主聊天没有肉眼证据。
  Capture-Step -Prompt "打开右侧状态/事件流面板，让 turn_started/message_delta/message_completed 可见" -FileName "codex_real_event_stream.png" # 新增代码+真实模型可见验收：捕获事件流面板；如果没有这行，状态流没有肉眼证据。
  $ProvidersPayload = Get-BridgeJson -Path "/v2/gui/provider-settings/providers" # 新增代码+真实模型可见验收：读取 provider catalog；如果没有这行，acceptance JSON 无法确认 provider_source。
  $EventsPayload = Get-BridgeJson -Path "/v2/gui/events?limit=200" # 新增代码+真实模型可见验收：读取最近事件流；如果没有这行，acceptance JSON 无法确认 adapter 事件。
  $OpenAIProvider = $ProvidersPayload.providers | Where-Object { $_.id -eq "openai" } | Select-Object -First 1 # 修改代码+真实模型可见验收：安全找到 OpenAI provider；如果没有这行，provider_source 无法提取。
  $EventKinds = @($EventsPayload.events | ForEach-Object { [string]$_.event_type }) # 新增代码+真实模型可见验收：提取事件类型列表；如果没有这行，事件门禁无法判断。
  $TurnStarted = $EventsPayload.events | Where-Object { $_.event_type -eq "turn_started" } | Select-Object -Last 1 # 修改代码+真实模型可见验收：安全读取最后一个 turn_started；如果没有这行，adapter_mode 无法从事件 payload 提取。
  $EventsJson = $EventsPayload | ConvertTo-Json -Depth 20 # 新增代码+真实模型可见验收：序列化事件用于扫描；如果没有这行，fake/secret 检测没有文本来源。
  $FakeTextDetected = $EventsJson -match "fake streaming" # 新增代码+真实模型可见验收：检查事件中是否出现 fake 文案；如果没有这行，模拟回复可能混入验收。
  $SecretLeakDetected = $EventsJson -match "access_token|refresh_token|id_token|secret_ref|api_key\s*[:=]|Bearer\s+|sk-[A-Za-z0-9]{12,}" # 修改代码+真实模型可见验收：检查事件中是否出现敏感字段和值形态；如果没有这行，token 泄露不会进入 JSON。
  $AdapterMode = if ($null -ne $TurnStarted -and $null -ne $TurnStarted.payload.mode) { [string]$TurnStarted.payload.mode } else { "unknown" } # 新增代码+真实模型可见验收：读取真实 adapter mode；如果没有这行，验收无法证明主聊天走 real。
  $ProviderSource = if ($null -ne $OpenAIProvider) { [string]$OpenAIProvider.source } else { "missing" } # 新增代码+真实模型可见验收：读取 provider source；如果没有这行，验收无法证明来自 codex_cli。
  $HasRequiredEvents = ($EventKinds -contains "turn_started") -and ($EventKinds -contains "message_delta") -and ($EventKinds -contains "message_completed") # 新增代码+真实模型可见验收：检查核心事件是否存在；如果没有这行，事件流不完整也可能通过。
  $Acceptance = [ordered]@{ ok = (($ProviderSource -eq "codex_cli") -and ($AdapterMode -eq "real") -and $HasRequiredEvents -and (-not $FakeTextDetected) -and (-not $SecretLeakDetected)); provider_source = $ProviderSource; adapter_mode = $AdapterMode; event_kinds = $EventKinds; fake_text_detected = [bool]$FakeTextDetected; secret_leak_detected = [bool]$SecretLeakDetected } # 新增代码+真实模型可见验收：构造机器可读验收 JSON；如果没有这行，release gate 没有稳定证据。
  $Acceptance | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path (Join-Path $EvidenceDir "real_codex_login_acceptance.json") # 新增代码+真实模型可见验收：写入 acceptance JSON；如果没有这行，后续 assert 脚本没有输入。
  & (Join-Path $ScriptDir "assert_real_model_acceptance.ps1") # 新增代码+真实模型可见验收：立即执行验收门禁；如果没有这行，截图完成但 JSON 不合格可能不被发现。
} finally { # 新增代码+真实模型可见验收：清理流程开始；如果没有这段，失败后后台进程会残留。
  if (-not $KeepAlive) { # 新增代码+真实模型可见验收：默认清理，KeepAlive 时保留窗口；如果没有这行，用户无法继续查看验收现场。
    foreach ($Process in $Processes) { # 新增代码+真实模型可见验收：遍历本轮进程；如果没有这行，无法逐个清理。
      if ($null -ne $Process) { # 新增代码+真实模型可见验收：确认进程对象存在；如果没有这行，空值会报错。
        Stop-ProcessTree -ProcessId $Process.Id # 新增代码+真实模型可见验收：停止进程树；如果没有这行，npm/electron/vite 可能残留。
      } # 新增代码+真实模型可见验收：进程对象判断结束；如果没有这行，条件块语法不完整。
    } # 新增代码+真实模型可见验收：进程清理循环结束；如果没有这行，foreach 语法不完整。
  } # 新增代码+真实模型可见验收：KeepAlive 判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+真实模型可见验收：主流程结束；如果没有这行，try/finally 语法不完整。

