$ErrorActionPreference = "Stop" # 新增代码+DirectOAuthEvidence：遇到缺文件或字段错误立即失败；如果没有这行，direct OAuth 验收坏证据可能继续通过。
Set-StrictMode -Version Latest # 新增代码+DirectOAuthEvidence：启用严格变量检查；如果没有这行，字段拼写错误可能被当成空值。
$ScriptPath = $MyInvocation.MyCommand.Path # 新增代码+DirectOAuthEvidence：读取当前脚本路径；如果没有这行，脚本无法稳定定位仓库根。
$ScriptDir = Split-Path -Parent $ScriptPath # 新增代码+DirectOAuthEvidence：定位 scripts 目录；如果没有这行，证据目录推导没有起点。
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path # 新增代码+DirectOAuthEvidence：从 scripts 目录推导仓库根；如果没有这行，从其它目录运行会找错位置。
$EvidenceDir = Join-Path $RepoRoot "learning_agent\test\provider_settings_v2_openai_connect\direct_oauth_evidence" # 新增代码+DirectOAuthEvidence：定位 direct OAuth 证据目录；如果没有这行，脚本不知道读取哪些文件。
$AcceptancePath = Join-Path $EvidenceDir "direct_oauth_acceptance.json" # 新增代码+DirectOAuthEvidence：定位机器可读验收 JSON；如果没有这行，release gate 无法检查验收字段。

if (-not (Test-Path $AcceptancePath)) { # 新增代码+DirectOAuthEvidence：检查 acceptance JSON 是否存在；如果没有这行，缺真实验收也可能被误判成功。
  Write-Host "Direct OAuth acceptance failed: missing $AcceptancePath" # 新增代码+DirectOAuthEvidence：输出缺文件原因；如果没有这行，用户不知道需要先跑真实 GUI 验收。
  exit 1 # 新增代码+DirectOAuthEvidence：缺 JSON 时失败；如果没有这行，release gate 会误过。
} # 新增代码+DirectOAuthEvidence：JSON 存在性判断结束；如果没有这行，PowerShell 条件块不完整。

$RawJson = Get-Content -Raw -Encoding UTF8 -Path $AcceptancePath # 新增代码+DirectOAuthEvidence：读取验收 JSON 原文；如果没有这行，无法做敏感词和字段检查。
$ForbiddenPattern = 'access_token|refresh_token|id_token|secret_ref|api_key\s*[:=]|Bearer\s+|sk-[A-Za-z0-9]{12,}' # 新增代码+DirectOAuthEvidence：定义禁止出现在证据中的敏感模式；如果没有这行，raw token 可能进入交付材料。
if ($RawJson -match $ForbiddenPattern) { # 新增代码+DirectOAuthEvidence：检查证据 JSON 是否疑似泄密；如果没有这行，token 泄露不会阻断验收。
  Write-Host "Direct OAuth acceptance failed: acceptance JSON contains forbidden secret-like text." # 新增代码+DirectOAuthEvidence：输出敏感词失败原因；如果没有这行，排查不知道是证据污染。
  exit 1 # 新增代码+DirectOAuthEvidence：敏感词命中时失败；如果没有这行，受污染证据会通过。
} # 新增代码+DirectOAuthEvidence：敏感词判断结束；如果没有这行，PowerShell 条件块不完整。

$Payload = $RawJson | ConvertFrom-Json # 新增代码+DirectOAuthEvidence：解析验收 JSON；如果没有这行，后续只能做脆弱字符串匹配。
if ($Payload.ok -ne $true) { # 新增代码+DirectOAuthEvidence：要求 ok=true；如果没有这行，失败验收 JSON 也可能通过。
  Write-Host "Direct OAuth acceptance failed: ok is not true." # 新增代码+DirectOAuthEvidence：输出 ok 字段失败；如果没有这行，用户不知道哪项没过。
  exit 1 # 新增代码+DirectOAuthEvidence：ok 非真时失败；如果没有这行，release gate 会忽略失败状态。
} # 新增代码+DirectOAuthEvidence：ok 判断结束；如果没有这行，PowerShell 条件块不完整。
if ([string]$Payload.provider_source -ne "direct_oauth_experimental") { # 新增代码+DirectOAuthEvidence：要求 provider 来源是 direct OAuth；如果没有这行，codex_cli 或 mock 证据可能冒充 V1C。
  Write-Host "Direct OAuth acceptance failed: provider_source is not direct_oauth_experimental." # 新增代码+DirectOAuthEvidence：输出 provider 来源错误；如果没有这行，排查不知道连接来源不对。
  exit 1 # 新增代码+DirectOAuthEvidence：来源错误时失败；如果没有这行，验收目标会漂移。
} # 新增代码+DirectOAuthEvidence：provider source 判断结束；如果没有这行，PowerShell 条件块不完整。
if ([string]$Payload.adapter_mode -ne "real") { # 新增代码+DirectOAuthEvidence：要求主聊天走 real adapter；如果没有这行，fake streaming 可能冒充成功。
  Write-Host "Direct OAuth acceptance failed: adapter_mode is not real." # 新增代码+DirectOAuthEvidence：输出 adapter 模式错误；如果没有这行，用户不知道仍是 fake。
  exit 1 # 新增代码+DirectOAuthEvidence：adapter 模式错误时失败；如果没有这行，真实模型目标无法保证。
} # 新增代码+DirectOAuthEvidence：adapter mode 判断结束；如果没有这行，PowerShell 条件块不完整。
if ($Payload.fake_text_detected -ne $false) { # 新增代码+DirectOAuthEvidence：要求没有 fake 文案；如果没有这行，模拟回答会通过。
  Write-Host "Direct OAuth acceptance failed: fake_text_detected is not false." # 新增代码+DirectOAuthEvidence：输出 fake 文案失败；如果没有这行，排查不知道是假回答污染。
  exit 1 # 新增代码+DirectOAuthEvidence：fake 命中时失败；如果没有这行，用户会误以为真实模型已接通。
} # 新增代码+DirectOAuthEvidence：fake 文案判断结束；如果没有这行，PowerShell 条件块不完整。
if ($Payload.secret_leak_detected -ne $false) { # 新增代码+DirectOAuthEvidence：要求没有 secret 泄露；如果没有这行，证据包泄露风险不会阻断。
  Write-Host "Direct OAuth acceptance failed: secret_leak_detected is not false." # 新增代码+DirectOAuthEvidence：输出 secret 检查失败；如果没有这行，用户不知道证据被污染。
  exit 1 # 新增代码+DirectOAuthEvidence：secret 命中时失败；如果没有这行，release gate 会放过风险。
} # 新增代码+DirectOAuthEvidence：secret 判断结束；如果没有这行，PowerShell 条件块不完整。

$EventKinds = @($Payload.event_kinds) # 新增代码+DirectOAuthEvidence：把事件列表转成数组；如果没有这行，单元素列表可能被当成字符串。
$RequiredKinds = @("turn_started", "message_delta", "message_completed") # 新增代码+DirectOAuthEvidence：定义真实回答必须出现的事件；如果没有这行，事件检查没有标准。
foreach ($Kind in $RequiredKinds) { # 新增代码+DirectOAuthEvidence：逐项检查必需事件；如果没有这行，缺事件可能漏过。
  if ($EventKinds -notcontains $Kind) { # 新增代码+DirectOAuthEvidence：判断当前事件是否缺失；如果没有这行，foreach 没有实际断言。
    Write-Host "Direct OAuth acceptance failed: missing event kind $Kind." # 新增代码+DirectOAuthEvidence：输出缺失事件；如果没有这行，排查不知道事件流哪里断。
    exit 1 # 新增代码+DirectOAuthEvidence：缺事件时失败；如果没有这行，状态流不完整也会通过。
  } # 新增代码+DirectOAuthEvidence：事件缺失判断结束；如果没有这行，PowerShell 条件块不完整。
} # 新增代码+DirectOAuthEvidence：事件检查循环结束；如果没有这行，foreach 语法不完整。

$ExpectedScreenshots = @("direct_oauth_login_success.png", "direct_oauth_provider_connected.png", "direct_oauth_model_answer.png", "direct_oauth_event_stream.png") # 新增代码+DirectOAuthEvidence：定义 direct OAuth 必须截图；如果没有这行，只有 JSON 没有肉眼证据也可能通过。
foreach ($Screenshot in $ExpectedScreenshots) { # 新增代码+DirectOAuthEvidence：逐张检查截图存在；如果没有这行，缺图不会失败。
  $ScreenshotPath = Join-Path $EvidenceDir $Screenshot # 新增代码+DirectOAuthEvidence：拼接截图路径；如果没有这行，Test-Path 没有目标。
  if (-not (Test-Path $ScreenshotPath)) { # 新增代码+DirectOAuthEvidence：判断截图是否缺失；如果没有这行，缺图不会被发现。
    Write-Host "Direct OAuth acceptance failed: missing screenshot $ScreenshotPath" # 新增代码+DirectOAuthEvidence：输出缺图路径；如果没有这行，用户不知道补哪张。
    exit 1 # 新增代码+DirectOAuthEvidence：缺图时失败；如果没有这行，肉眼验收要求无法落实。
  } # 新增代码+DirectOAuthEvidence：截图存在判断结束；如果没有这行，PowerShell 条件块不完整。
} # 新增代码+DirectOAuthEvidence：截图检查循环结束；如果没有这行，foreach 语法不完整。

Write-Host 'Direct OAuth acceptance evidence passed.' # 新增代码+DirectOAuthEvidence：输出成功摘要；如果没有这行，人工运行不知道证据已通过。

