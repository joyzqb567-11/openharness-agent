$ErrorActionPreference = "Stop" # 新增代码+真实模型验收门禁：遇到文件缺失或字段错误立即失败；如果没有这行，验收 JSON 坏掉也可能继续通过。
Set-StrictMode -Version Latest # 新增代码+真实模型验收门禁：启用严格变量检查；如果没有这行，字段名拼错可能被 PowerShell 当成空值。
$ScriptPath = $MyInvocation.MyCommand.Path # 修改代码+真实模型验收门禁：使用 MyInvocation 定位当前脚本路径；如果没有这行，脚本无法找到证据目录。
$ScriptDir = Split-Path -Parent $ScriptPath # 新增代码+真实模型验收门禁：定位 scripts 目录；如果没有这行，仓库根目录推导没有起点。
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..\..\..")).Path # 新增代码+真实模型验收门禁：从 scripts 目录定位仓库根；如果没有这行，从其他目录运行会找错证据文件。
$EvidenceDir = Join-Path $RepoRoot "learning_agent\test\provider_settings_v2_openai_connect\real_codex_login_evidence" # 新增代码+真实模型验收门禁：定位真实 Codex 登录证据目录；如果没有这行，验收脚本不知道读取哪里。
$AcceptancePath = Join-Path $EvidenceDir "real_codex_login_acceptance.json" # 新增代码+真实模型验收门禁：定位机器可读验收 JSON；如果没有这行，无法检查真实 GUI 验收结果。

# 新增代码+真实模型验收门禁：检查验收 JSON 是否存在；如果没有这行，缺证据也可能被误认为通过。
if (-not (Test-Path $AcceptancePath)) {
  # 新增代码+真实模型验收门禁：输出缺文件原因；如果没有这行，用户不知道要先跑真实 GUI 验收。
  Write-Host "Real model acceptance failed: missing $AcceptancePath"
  # 新增代码+真实模型验收门禁：缺证据时失败；如果没有这行，release gate 会误过。
  exit 1
}

$RawJson = Get-Content -Raw -Encoding UTF8 -Path $AcceptancePath # 新增代码+真实模型验收门禁：读取验收 JSON 原文；如果没有这行，后续无法做敏感词扫描和字段解析。
$ForbiddenPattern = 'access_token|refresh_token|id_token|secret_ref|api_key\s*[:=]|Bearer\s+|sk-[A-Za-z0-9]{12,}' # 修改代码+真实模型验收门禁：定义证据 JSON 禁止出现的敏感字段和值形态；如果没有这行，token 或 key 字段可能进入交付证据。
if ($RawJson -match $ForbiddenPattern) { # 新增代码+真实模型验收门禁：检查 JSON 是否含敏感模式；如果没有这行，raw token 泄露不会阻断验收。
  Write-Host "Real model acceptance failed: acceptance JSON contains forbidden secret-like text." # 新增代码+真实模型验收门禁：输出敏感词失败原因；如果没有这行，排查不知道是证据污染。
  exit 1 # 新增代码+真实模型验收门禁：敏感词命中时失败；如果没有这行，受污染证据会进入 release。
} # 新增代码+真实模型验收门禁：敏感词判断结束；如果没有这行，PowerShell 语法不完整。

$Payload = $RawJson | ConvertFrom-Json # 新增代码+真实模型验收门禁：把 JSON 转成对象；如果没有这行，后续字段只能靠脆弱字符串匹配。
if ($Payload.ok -ne $true) { # 新增代码+真实模型验收门禁：要求真实 GUI 验收 ok=true；如果没有这行，失败 JSON 也可能通过。
  Write-Host "Real model acceptance failed: ok is not true." # 新增代码+真实模型验收门禁：输出 ok 字段错误；如果没有这行，用户不知道哪项失败。
  exit 1 # 新增代码+真实模型验收门禁：ok 非真时失败；如果没有这行，release gate 会忽略失败状态。
} # 新增代码+真实模型验收门禁：ok 判断结束；如果没有这行，PowerShell 语法不完整。
if ([string]$Payload.provider_source -ne "codex_cli") { # 新增代码+真实模型验收门禁：要求 provider 来源为官方 Codex CLI；如果没有这行，mock/API key 证据可能冒充 ChatGPT OAuth。
  Write-Host "Real model acceptance failed: provider_source is not codex_cli." # 新增代码+真实模型验收门禁：输出 provider 来源错误；如果没有这行，排查不知道连接来源不对。
  exit 1 # 新增代码+真实模型验收门禁：来源不对时失败；如果没有这行，验收目标会漂移。
} # 新增代码+真实模型验收门禁：provider_source 判断结束；如果没有这行，PowerShell 语法不完整。
if ([string]$Payload.adapter_mode -ne "real") { # 新增代码+真实模型验收门禁：要求 adapter_mode 为 real；如果没有这行，fake streaming 可能冒充通过。
  Write-Host "Real model acceptance failed: adapter_mode is not real." # 新增代码+真实模型验收门禁：输出 adapter 模式错误；如果没有这行，用户不知道主聊天仍是 fake。
  exit 1 # 新增代码+真实模型验收门禁：adapter 模式错误时失败；如果没有这行，真实连接目标无法保证。
} # 新增代码+真实模型验收门禁：adapter_mode 判断结束；如果没有这行，PowerShell 语法不完整。
if ($Payload.fake_text_detected -ne $false) { # 新增代码+真实模型验收门禁：要求没有 fake 文案；如果没有这行，假回答会通过。
  Write-Host "Real model acceptance failed: fake_text_detected is not false." # 新增代码+真实模型验收门禁：输出 fake 文案检查错误；如果没有这行，排查不知道是假回答污染。
  exit 1 # 新增代码+真实模型验收门禁：fake 文案命中时失败；如果没有这行，用户会误以为真实模型已接通。
} # 新增代码+真实模型验收门禁：fake 文案判断结束；如果没有这行，PowerShell 语法不完整。
if ($Payload.secret_leak_detected -ne $false) { # 新增代码+真实模型验收门禁：要求没有 secret 泄露；如果没有这行，证据包泄露风险不会阻断。
  Write-Host "Real model acceptance failed: secret_leak_detected is not false." # 新增代码+真实模型验收门禁：输出 secret 检查错误；如果没有这行，用户不知道证据包被污染。
  exit 1 # 新增代码+真实模型验收门禁：secret 命中时失败；如果没有这行，release gate 会放过风险。
} # 新增代码+真实模型验收门禁：secret 判断结束；如果没有这行，PowerShell 语法不完整。

$EventKinds = @($Payload.event_kinds) # 新增代码+真实模型验收门禁：把事件列表转成 PowerShell 数组；如果没有这行，单项数组可能被当成字符串。
$RequiredKinds = @("turn_started", "message_delta", "message_completed") # 新增代码+真实模型验收门禁：定义真实回答必须出现的事件；如果没有这行，事件检查没有标准。
foreach ($Kind in $RequiredKinds) { # 新增代码+真实模型验收门禁：逐项检查必需事件；如果没有这行，缺 delta 或 completed 可能漏过。
  if ($EventKinds -notcontains $Kind) { # 新增代码+真实模型验收门禁：判断当前事件是否缺失；如果没有这行，foreach 没有实际断言。
    Write-Host "Real model acceptance failed: missing event kind $Kind." # 新增代码+真实模型验收门禁：输出缺失事件名；如果没有这行，排查不知道事件流哪里断。
    exit 1 # 新增代码+真实模型验收门禁：缺事件时失败；如果没有这行，状态流不完整也会通过。
  } # 新增代码+真实模型验收门禁：事件缺失判断结束；如果没有这行，PowerShell 语法不完整。
} # 新增代码+真实模型验收门禁：事件检查循环结束；如果没有这行，foreach 语法不完整。

# 新增代码+真实模型验收门禁：定义真实 GUI 验收应留下的截图；如果没有这段，只有 JSON 没有肉眼证据也可能通过。
$ExpectedScreenshots = @("codex_login_method_picker.png", "codex_login_waiting.png", "codex_provider_connected.png", "codex_real_model_answer.png", "codex_real_event_stream.png")
# 新增代码+真实模型验收门禁：逐张检查截图存在；如果没有这行，截图缺失不会失败。
foreach ($Screenshot in $ExpectedScreenshots) {
  # 新增代码+真实模型验收门禁：拼接截图路径；如果没有这行，Test-Path 没有目标。
  $ScreenshotPath = Join-Path $EvidenceDir $Screenshot
  # 新增代码+真实模型验收门禁：判断截图是否存在；如果没有这行，缺图不会被发现。
  if (-not (Test-Path $ScreenshotPath)) {
    # 新增代码+真实模型验收门禁：输出缺图路径；如果没有这行，用户不知道补哪张。
    Write-Host "Real model acceptance failed: missing screenshot $ScreenshotPath"
    # 新增代码+真实模型验收门禁：缺图时失败；如果没有这行，肉眼验收要求无法落实。
    exit 1
  }
}

# 新增代码+真实模型验收门禁：输出成功摘要；如果没有这行，人工运行不知道证据已通过。
Write-Host 'Real model acceptance evidence passed.'

