param([int]$BridgePort = 8776, [int]$RendererPort = 5177, [int]$CdpPort = 9223, [switch]$KeepAlive) # 新增代码+ProviderSettingsVisualQA：参数块定义 bridge、renderer、CDP 端口和是否保留窗口；如果没有这行，脚本只能使用硬编码且无法做人工窗口验收。
# 新增代码+ProviderSettingsVisualQA：BridgePort 是 GUI bridge 端口；如果没有这行注释，用户不清楚第一个参数控制后端监听。
# 新增代码+ProviderSettingsVisualQA：RendererPort 是 Vite renderer 端口；如果没有这行注释，用户不清楚第二个参数控制前端页面。
# 新增代码+ProviderSettingsVisualQA：CdpPort 是 Electron 调试端口；如果没有这行注释，用户不清楚自动截图如何连接窗口。
# 新增代码+ProviderSettingsVisualQA：KeepAlive 会在验收后保留真实窗口；如果没有这行注释，用户不清楚何时需要手动清理进程。

$ErrorActionPreference = "Stop" # 新增代码+ProviderSettingsVisualQA：遇到错误立即停止；如果没有这行，启动失败可能被后续步骤掩盖。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 新增代码+ProviderSettingsVisualQA：获取当前脚本路径；如果没有这行，不同宿主下路径推导不稳定。
$ScriptDir = Split-Path -Parent $ScriptPath # 新增代码+ProviderSettingsVisualQA：定位 scripts 目录；如果没有这行，后续无法推导仓库根。
$Workspace = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path # 新增代码+ProviderSettingsVisualQA：定位 worktree 根目录；如果没有这行，后端启动和证据目录会指向错误位置。
$DesktopRoot = Join-Path $Workspace "apps\desktop" # 新增代码+ProviderSettingsVisualQA：定位桌面应用目录；如果没有这行，npm 命令无法找到 package.json。
$EvidenceDir = Join-Path $Workspace "learning_agent\test\provider_settings_v1\task09_visual_qa" # 新增代码+ProviderSettingsVisualQA：定位截图证据目录；如果没有这行，Task 9 图片没有固定位置。
$DriverPath = Join-Path $ScriptDir "provider_settings_visual_qa_driver.mjs" # 新增代码+ProviderSettingsVisualQA：定位 Node CDP driver；如果没有这行，PowerShell 无法调用自动截图逻辑。
$Token = "openharness-desktop-dev-token" # 新增代码+ProviderSettingsVisualQA：统一使用开发 token；如果没有这行，前端和 bridge token 可能不一致。
$BridgeUrl = "http://127.0.0.1:$BridgePort" # 新增代码+ProviderSettingsVisualQA：生成 bridge URL；如果没有这行，Electron preload 无法连接后端。
$RendererUrl = "http://127.0.0.1:$RendererPort" # 新增代码+ProviderSettingsVisualQA：生成 renderer URL；如果没有这行，Electron 无法加载 Vite 页面。
$Processes = @() # 新增代码+ProviderSettingsVisualQA：保存启动的进程列表；如果没有这行，finally 阶段无法统一清理。

function Test-PortAvailable { # 新增代码+ProviderSettingsVisualQA：函数段开始，检查端口是否可用；如果没有这段，端口占用会变成隐蔽启动失败。
  param([int]$PortNumber) # 新增代码+ProviderSettingsVisualQA：声明待检查端口；如果没有这行，函数没有输入。
  $Listener = $null # 新增代码+ProviderSettingsVisualQA：准备 listener 变量；如果没有这行，finally 无法安全释放。
  try { # 新增代码+ProviderSettingsVisualQA：尝试绑定端口；如果没有这行，端口异常无法转成布尔值。
    $Address = [System.Net.IPAddress]::Parse("127.0.0.1") # 新增代码+ProviderSettingsVisualQA：固定检查本机回环地址；如果没有这行，端口检查范围不清楚。
    $Listener = [System.Net.Sockets.TcpListener]::new($Address, $PortNumber) # 新增代码+ProviderSettingsVisualQA：创建临时监听器；如果没有这行，无法判断端口占用。
    $Listener.Start() # 新增代码+ProviderSettingsVisualQA：实际绑定端口；如果没有这行，检查不会触碰系统端口表。
    return $true # 新增代码+ProviderSettingsVisualQA：绑定成功说明端口可用；如果没有这行，可用端口会被误判。
  } catch { # 新增代码+ProviderSettingsVisualQA：捕获绑定失败；如果没有这行，端口占用会抛复杂异常。
    return $false # 新增代码+ProviderSettingsVisualQA：绑定失败说明端口不可用；如果没有这行，调用方无法提前失败。
  } finally { # 新增代码+ProviderSettingsVisualQA：释放临时监听器；如果没有这行，检查本身可能占住端口。
    if ($null -ne $Listener) { # 新增代码+ProviderSettingsVisualQA：确认 listener 已创建；如果没有这行，Stop 可能访问空对象。
      $Listener.Stop() # 新增代码+ProviderSettingsVisualQA：停止临时监听器；如果没有这行，真正进程可能无法绑定端口。
    } # 新增代码+ProviderSettingsVisualQA：listener 释放判断结束；如果没有这行，条件块语法不完整。
  } # 新增代码+ProviderSettingsVisualQA：finally 结束；如果没有这行，try/catch/finally 语法不完整。
} # 新增代码+ProviderSettingsVisualQA：函数段结束，Test-PortAvailable 到此结束；如果没有这行，函数语法不完整。

function Wait-PortOpen { # 新增代码+ProviderSettingsVisualQA：函数段开始，等待服务监听端口；如果没有这段，后续步骤可能太早连接。
  param([int]$PortNumber, [string]$Name) # 新增代码+ProviderSettingsVisualQA：声明端口和服务名；如果没有这行，超时错误不清楚。
  for ($Attempt = 0; $Attempt -lt 80; $Attempt += 1) { # 新增代码+ProviderSettingsVisualQA：最多等待约 40 秒；如果没有这行，服务慢启动会失败或无限等。
    if (-not (Test-PortAvailable -PortNumber $PortNumber)) { # 新增代码+ProviderSettingsVisualQA：端口不可绑定说明服务已监听；如果没有这行，无法判断成功。
      return # 新增代码+ProviderSettingsVisualQA：端口打开后返回；如果没有这行，会继续等待到超时。
    } # 新增代码+ProviderSettingsVisualQA：端口打开判断结束；如果没有这行，条件块语法不完整。
    Start-Sleep -Milliseconds 500 # 新增代码+ProviderSettingsVisualQA：等待后重试；如果没有这行，会忙等。
  } # 新增代码+ProviderSettingsVisualQA：等待循环结束；如果没有这行，for 循环语法不完整。
  throw "$Name did not open port $PortNumber." # 新增代码+ProviderSettingsVisualQA：超时后抛清楚错误；如果没有这行，后续会在更远处失败。
} # 新增代码+ProviderSettingsVisualQA：函数段结束，Wait-PortOpen 到此结束；如果没有这行，函数语法不完整。

function Stop-ProcessTree { # 新增代码+ProviderSettingsVisualQA：函数段开始，递归停止进程树；如果没有这段，npm 子进程可能残留。
  param([int]$ProcessId) # 新增代码+ProviderSettingsVisualQA：声明根进程 id；如果没有这行，函数不知道停止谁。
  $Children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ProcessId } # 新增代码+ProviderSettingsVisualQA：查找子进程；如果没有这行，Electron/Vite 子进程可能残留。
  foreach ($Child in $Children) { # 新增代码+ProviderSettingsVisualQA：遍历子进程；如果没有这行，只会停止父进程。
    Stop-ProcessTree -ProcessId ([int]$Child.ProcessId) # 新增代码+ProviderSettingsVisualQA：递归停止子进程；如果没有这行，孙进程会残留。
  } # 新增代码+ProviderSettingsVisualQA：子进程遍历结束；如果没有这行，foreach 语法不完整。
  $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue # 新增代码+ProviderSettingsVisualQA：读取当前进程；如果没有这行，已退出进程会抛错。
  if ($null -ne $Process) { # 新增代码+ProviderSettingsVisualQA：确认进程仍存在；如果没有这行，Stop-Process 可能报错。
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue # 新增代码+ProviderSettingsVisualQA：强制停止进程；如果没有这行，端口可能被占用到下一轮。
  } # 新增代码+ProviderSettingsVisualQA：停止当前进程判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+ProviderSettingsVisualQA：函数段结束，Stop-ProcessTree 到此结束；如果没有这行，函数语法不完整。

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null # 新增代码+ProviderSettingsVisualQA：确保证据目录存在；如果没有这行，日志和截图无法保存。
if (-not (Test-PortAvailable -PortNumber $BridgePort)) { throw "Bridge port $BridgePort is occupied." } # 新增代码+ProviderSettingsVisualQA：检查 bridge 端口；如果没有这行，后端启动失败不清楚。
if (-not (Test-PortAvailable -PortNumber $RendererPort)) { throw "Renderer port $RendererPort is occupied." } # 新增代码+ProviderSettingsVisualQA：检查 renderer 端口；如果没有这行，Vite 启动失败不清楚。
if (-not (Test-PortAvailable -PortNumber $CdpPort)) { throw "CDP port $CdpPort is occupied." } # 新增代码+ProviderSettingsVisualQA：检查 CDP 端口；如果没有这行，自动截图无法连接。

try { # 新增代码+ProviderSettingsVisualQA：启动和验收主流程开始；如果没有这段，finally 无法可靠清理。
  $Backend = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Workspace "apps\desktop\scripts\start-backend.ps1"), "-Workspace", $Workspace, "-Port", "$BridgePort", "-Token", $Token -WorkingDirectory $Workspace -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "backend_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "backend_stderr.log") -PassThru # 新增代码+ProviderSettingsVisualQA：后台启动真实 GUI bridge；如果没有这行，Electron 没有后端数据源。
  $Processes += $Backend # 新增代码+ProviderSettingsVisualQA：记录 backend 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $BridgePort -Name "GUI bridge" # 新增代码+ProviderSettingsVisualQA：等待 bridge 端口打开；如果没有这行，renderer 会先遇到离线状态。
  Set-Location $DesktopRoot # 新增代码+ProviderSettingsVisualQA：切换到桌面目录；如果没有这行，npm 命令会找不到 package.json。
  npm run build:main # 新增代码+ProviderSettingsVisualQA：构建 Electron main/preload；如果没有这行，electron start 会加载旧主进程。
  $Renderer = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev:renderer", "--", "--port", "$RendererPort" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "renderer_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "renderer_stderr.log") -PassThru # 新增代码+ProviderSettingsVisualQA：后台启动 Vite renderer；如果没有这行，Electron 没有前端页面可加载。
  $Processes += $Renderer # 新增代码+ProviderSettingsVisualQA：记录 renderer 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $RendererPort -Name "Vite renderer" # 新增代码+ProviderSettingsVisualQA：等待 renderer 端口打开；如果没有这行，Electron 可能打开白屏。
  $env:OPENHARNESS_GUI_BRIDGE_URL = $BridgeUrl # 新增代码+ProviderSettingsVisualQA：把 bridge URL 传给 Electron；如果没有这行，preload 无法注入正确后端地址。
  $env:OPENHARNESS_GUI_BRIDGE_TOKEN = $Token # 新增代码+ProviderSettingsVisualQA：把 token 传给 Electron；如果没有这行，GUI 请求会被 401 拒绝。
  $env:OPENHARNESS_DESKTOP_DEV_URL = $RendererUrl # 新增代码+ProviderSettingsVisualQA：把 renderer URL 传给 Electron；如果没有这行，Electron 会加载生产 HTML。
  $Electron = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "start", "--", "--remote-debugging-port=$CdpPort" -WorkingDirectory $DesktopRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $EvidenceDir "electron_stdout.log") -RedirectStandardError (Join-Path $EvidenceDir "electron_stderr.log") -PassThru # 新增代码+ProviderSettingsVisualQA：启动真实可见 Electron 窗口并开启 CDP；如果没有这行，无法完成肉眼 GUI 和自动截图验收。
  $Processes += $Electron # 新增代码+ProviderSettingsVisualQA：记录 Electron 进程；如果没有这行，清理阶段无法停止它。
  Wait-PortOpen -PortNumber $CdpPort -Name "Electron CDP" # 新增代码+ProviderSettingsVisualQA：等待 CDP 端口打开；如果没有这行，driver 会连接失败。
  node $DriverPath "--cdpPort=$CdpPort" "--evidenceDir=$EvidenceDir" # 新增代码+ProviderSettingsVisualQA：运行 Node CDP driver；如果没有这行，截图和 DOM 断言不会执行。
  $Runtime = @{ bridge = $Backend.Id; renderer = $Renderer.Id; electron = $Electron.Id; bridgePort = $BridgePort; rendererPort = $RendererPort; cdpPort = $CdpPort } # 新增代码+ProviderSettingsVisualQA：记录运行时 pid 和端口；如果没有这行，KeepAlive 后无法手动清理。
  $Runtime | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -Path (Join-Path $EvidenceDir "runtime_pids.json") # 新增代码+ProviderSettingsVisualQA：写入 pid 证据；如果没有这行，后续排查和清理不方便。
} finally { # 新增代码+ProviderSettingsVisualQA：清理流程开始；如果没有这段，失败后进程会残留。
  if (-not $KeepAlive) { # 新增代码+ProviderSettingsVisualQA：默认自动清理，KeepAlive 时保留真实窗口；如果没有这行，人工验收无法保持窗口。
    foreach ($Process in $Processes) { # 新增代码+ProviderSettingsVisualQA：遍历本轮启动进程；如果没有这行，无法逐个清理。
      if ($null -ne $Process) { # 新增代码+ProviderSettingsVisualQA：确认进程对象存在；如果没有这行，空值会报错。
        Stop-ProcessTree -ProcessId $Process.Id # 新增代码+ProviderSettingsVisualQA：停止进程树；如果没有这行，npm/electron/vite 可能残留。
      } # 新增代码+ProviderSettingsVisualQA：进程对象判断结束；如果没有这行，条件块语法不完整。
    } # 新增代码+ProviderSettingsVisualQA：进程清理循环结束；如果没有这行，foreach 语法不完整。
  } # 新增代码+ProviderSettingsVisualQA：KeepAlive 判断结束；如果没有这行，条件块语法不完整。
} # 新增代码+ProviderSettingsVisualQA：主流程结束；如果没有这行，try/finally 语法不完整。
