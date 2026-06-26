$ErrorActionPreference = "Stop" # 新增代码+ProviderSecretLeakGate：让脚本遇到不可恢复错误立即失败；如果没有这行，rg 执行失败可能被误当作扫描通过。
Set-StrictMode -Version Latest # 新增代码+ProviderSecretLeakGate：启用严格变量检查；如果没有这行，拼错变量名可能导致漏扫。
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path # 新增代码+ProviderSecretLeakGate：从脚本目录定位仓库根目录；如果没有这行，从别的目录运行会找不到 learning_agent 和 apps/desktop。
Set-Location $RepoRoot # 新增代码+ProviderSecretLeakGate：切到仓库根目录执行 rg；如果没有这行，rg 输出路径和扫描范围会不稳定。

$DangerousMatches = & rg -n --glob '!*.png' --glob '!*.map' 'sk-[A-Za-z0-9]{12,}|Authorization:\s*Bearer|api_key.*sk-' learning_agent apps/desktop 2>&1 # 新增代码+ProviderSecretLeakGate：执行蓝图要求的危险密钥模式扫描；如果没有这行，真实 key 泄漏不会被 release gate 抓住。
$DangerousExitCode = $LASTEXITCODE # 新增代码+ProviderSecretLeakGate：保存危险扫描退出码；如果没有这行，后续命令会覆盖 rg 的结果。
if ($DangerousExitCode -gt 1) { # 新增代码+ProviderSecretLeakGate：处理 rg 自身错误；如果没有这行，扫描器故障可能被误当作零命中。
  Write-Host "Provider secret leak scan failed: rg returned $DangerousExitCode during dangerous pattern scan." # 新增代码+ProviderSecretLeakGate：输出扫描器错误；如果没有这行，排查不知道是工具失败。
  $DangerousMatches | ForEach-Object { Write-Host $_ } # 新增代码+ProviderSecretLeakGate：输出 rg 错误详情；如果没有这行，路径或语法问题难以定位。
  exit 1 # 新增代码+ProviderSecretLeakGate：扫描器异常时失败；如果没有这行，release gate 可能漏过。
} # 新增代码+ProviderSecretLeakGate：rg 错误分支结束；如果没有这行，PowerShell 语法不完整。

$AllowedDangerousPathPatterns = @( # 新增代码+ProviderSecretLeakGate：定义危险模式允许出现的非生产路径；如果没有这段，历史文档示例和测试夹具会让门禁无法运行。
  "^learning_agent/test/", # 新增代码+ProviderSecretLeakGate：允许学习副本、视觉证据和蓝图归档；如果没有这行，Task 9 证据目录会误报。
  "^learning_agent/tests/", # 新增代码+ProviderSecretLeakGate：允许后端测试夹具；如果没有这行，脱敏测试里的危险样本会误报。
  "^apps/desktop/tests/", # 新增代码+ProviderSecretLeakGate：允许前端测试夹具；如果没有这行，trace 脱敏测试会误报。
  "^learning_agent/memory/", # 新增代码+ProviderSecretLeakGate：允许历史运行记忆；如果没有这行，旧任务 prompt 会污染本轮 provider release gate。
  "^learning_agent/acceptance_controller/scenarios/", # 新增代码+ProviderSecretLeakGate：允许验收场景 JSON；如果没有这行，task-notification 固定词会被 sk- 规则误报。
  "^learning_agent/.*\.md$", # 修改代码+ProviderSecretLeakGate：允许说明文档中的 Bearer 示例；如果没有这行，文档占位符会被当成真实密钥。
  "^learning_agent/dynamicprompt/", # 新增代码+ProviderSecretLeakGate：允许动态提示词知识文档；如果没有这行，MCP auth 关键词说明会误报。
  "^learning_agent/skills/", # 新增代码+ProviderSecretLeakGate：允许 skill 规则文档；如果没有这行，认证规范示例会误报。
  "^learning_agent/mcp/(agent_adapter|runtime)\.py$" # 修改代码+ProviderSecretLeakGate：允许 MCP 鉴权说明字符串；如果没有这行，非密钥的 Bearer 配置提示会误报。
) # 新增代码+ProviderSecretLeakGate：危险模式允许路径数组结束；如果没有这行，PowerShell 数组语法不完整。
$UnexpectedDangerousMatches = @() # 新增代码+ProviderSecretLeakGate：收集真正不允许的危险模式命中；如果没有这行，脚本无法在过滤后报告风险。
foreach ($MatchLine in $DangerousMatches) { # 新增代码+ProviderSecretLeakGate：逐行检查危险模式命中；如果没有这行，无法区分真实泄漏和旧文档示例。
  if ($MatchLine -notmatch "^(.+?):\d+:") { # 新增代码+ProviderSecretLeakGate：处理无法解析的 rg 输出；如果没有这行，异常输出可能绕过过滤。
    $UnexpectedDangerousMatches += $MatchLine # 新增代码+ProviderSecretLeakGate：把无法解析行按风险处理；如果没有这行，扫描异常会被忽略。
    continue # 新增代码+ProviderSecretLeakGate：跳过当前无法解析行；如果没有这行，后续 `$Matches` 可能沿用旧值。
  } # 新增代码+ProviderSecretLeakGate：无法解析分支结束；如果没有这行，PowerShell 语法不完整。
  $MatchPath = ($Matches[1] -replace "\\", "/") # 新增代码+ProviderSecretLeakGate：把 Windows 路径归一成正斜杠；如果没有这行，allowlist 在不同终端下不稳定。
  $IsAllowedPath = $false # 新增代码+ProviderSecretLeakGate：初始化危险命中是否允许；如果没有这行，上一条结果可能污染当前判断。
  foreach ($AllowedPattern in $AllowedDangerousPathPatterns) { # 新增代码+ProviderSecretLeakGate：遍历危险模式允许路径；如果没有这行，脚本无法处理多类历史夹具。
    if ($MatchPath -match $AllowedPattern) { # 新增代码+ProviderSecretLeakGate：判断当前命中是否属于允许路径；如果没有这行，所有命中都会失败。
      $IsAllowedPath = $true # 新增代码+ProviderSecretLeakGate：标记当前命中允许；如果没有这行，测试和文档样本会误报。
      break # 新增代码+ProviderSecretLeakGate：命中后停止遍历；如果没有这行，会做无意义的额外匹配。
    } # 新增代码+ProviderSecretLeakGate：允许路径命中分支结束；如果没有这行，PowerShell 语法不完整。
  } # 新增代码+ProviderSecretLeakGate：危险路径遍历结束；如果没有这行，PowerShell 语法不完整。
  if (($MatchLine -match "task-notification") -and ($MatchPath -match "^learning_agent/")) { # 新增代码+ProviderSecretLeakGate：识别 sk- 规则对 task-notification 的固定假阳性；如果没有这行，非密钥任务标签会误报。
    $IsAllowedPath = $true # 新增代码+ProviderSecretLeakGate：允许 task-notification 固定词；如果没有这行，旧 harness 验收记录会阻断 provider gate。
  } # 新增代码+ProviderSecretLeakGate：task-notification 假阳性分支结束；如果没有这行，PowerShell 语法不完整。
  if (-not $IsAllowedPath) { # 新增代码+ProviderSecretLeakGate：处理过滤后仍不允许的危险命中；如果没有这行，真实泄漏不会进入失败列表。
    $UnexpectedDangerousMatches += $MatchLine # 新增代码+ProviderSecretLeakGate：记录违规危险命中；如果没有这行，失败时缺少定位信息。
  } # 新增代码+ProviderSecretLeakGate：违规危险命中分支结束；如果没有这行，PowerShell 语法不完整。
} # 新增代码+ProviderSecretLeakGate：危险模式命中遍历结束；如果没有这行，PowerShell 语法不完整。
if ($UnexpectedDangerousMatches.Count -gt 0) { # 新增代码+ProviderSecretLeakGate：判断过滤后是否仍有危险命中；如果没有这行，真实泄漏不会失败。
  Write-Host "Provider secret leak scan failed: dangerous secret-like text was found outside allowed fixtures." # 新增代码+ProviderSecretLeakGate：输出失败摘要；如果没有这行，用户不知道失败原因。
  $UnexpectedDangerousMatches | ForEach-Object { Write-Host $_ } # 新增代码+ProviderSecretLeakGate：输出违规命中位置；如果没有这行，修复者无法定位泄漏文件。
  exit 1 # 新增代码+ProviderSecretLeakGate：用非零退出码阻断门禁；如果没有这行，release gate 会误过。
} # 新增代码+ProviderSecretLeakGate：危险命中失败分支结束；如果没有这行，PowerShell 语法不完整。

$UnitTestSecretMatches = & rg -n 'unit-test-secret-value' learning_agent apps/desktop 2>&1 # 新增代码+ProviderSecretLeakGate：执行蓝图要求的固定测试值扫描；如果没有这行，测试密钥可能混入生产代码。
$UnitTestSecretExitCode = $LASTEXITCODE # 新增代码+ProviderSecretLeakGate：保存固定测试值扫描退出码；如果没有这行，后续判断拿不到 rg 结果。
if ($UnitTestSecretExitCode -gt 1) { # 新增代码+ProviderSecretLeakGate：处理固定测试值扫描器错误；如果没有这行，rg 故障会被误判为没有测试值。
  Write-Host "Provider secret leak scan failed: rg returned $UnitTestSecretExitCode during unit-test secret scan." # 新增代码+ProviderSecretLeakGate：输出扫描器错误摘要；如果没有这行，用户不知道扫描失败。
  $UnitTestSecretMatches | ForEach-Object { Write-Host $_ } # 新增代码+ProviderSecretLeakGate：输出 rg 错误详情；如果没有这行，修复者缺少上下文。
  exit 1 # 新增代码+ProviderSecretLeakGate：扫描器异常时失败；如果没有这行，release gate 会不可靠。
} # 新增代码+ProviderSecretLeakGate：固定测试值扫描器错误分支结束；如果没有这行，PowerShell 语法不完整。

$AllowedUnitTestSecretPathPatterns = @( # 新增代码+ProviderSecretLeakGate：定义固定测试值允许出现的位置；如果没有这段，测试值可能扩散到生产代码还不被发现。
  "^learning_agent/tests/", # 新增代码+ProviderSecretLeakGate：允许 Python 后端测试文件；如果没有这行，合同测试里的固定样本会误报。
  "^apps/desktop/tests/", # 新增代码+ProviderSecretLeakGate：允许桌面前端测试文件；如果没有这行，renderer 测试里的固定样本会误报。
  "^learning_agent/test/provider_settings_v1/", # 修改代码+ProviderSecretLeakGate：允许 Provider Settings V1 学习副本和视觉证据目录；如果没有这行，Task 9 evidence 会误报。
  "^learning_agent/test/provider_settings_v2_openai_connect/" # 新增代码+OpenAIConnectSecretGate：允许 OpenAI Connect V1 学习源码副本里的固定测试值；如果没有这行，学习副本会阻断运行产物扫描。
) # 新增代码+ProviderSecretLeakGate：允许路径数组结束；如果没有这行，PowerShell 数组语法不完整。
$UnexpectedUnitTestSecretMatches = @() # 新增代码+ProviderSecretLeakGate：收集不允许的固定测试值命中；如果没有这行，脚本无法一次性报告所有问题。
foreach ($MatchLine in $UnitTestSecretMatches) { # 新增代码+ProviderSecretLeakGate：逐行检查固定测试值命中；如果没有这行，无法按文件路径判断是否允许。
  if ($MatchLine -notmatch "^(.+?):\d+:") { # 新增代码+ProviderSecretLeakGate：处理无法解析的 rg 输出；如果没有这行，非标准输出可能绕过检查。
    $UnexpectedUnitTestSecretMatches += $MatchLine # 新增代码+ProviderSecretLeakGate：把无法解析的行作为风险记录；如果没有这行，异常输出会被忽略。
    continue # 新增代码+ProviderSecretLeakGate：跳过当前无法解析行；如果没有这行，后续 `$Matches` 可能沿用旧值。
  } # 新增代码+ProviderSecretLeakGate：无法解析分支结束；如果没有这行，PowerShell 语法不完整。
  $MatchPath = ($Matches[1] -replace "\\", "/") # 新增代码+ProviderSecretLeakGate：把 Windows 反斜杠路径统一成正斜杠；如果没有这行，路径 allowlist 在不同 shell 下不稳定。
  $IsAllowedPath = $false # 新增代码+ProviderSecretLeakGate：初始化当前命中是否允许；如果没有这行，上一轮判断可能污染本轮。
  foreach ($AllowedPattern in $AllowedUnitTestSecretPathPatterns) { # 新增代码+ProviderSecretLeakGate：遍历允许路径模式；如果没有这行，脚本无法支持多类测试目录。
    if ($MatchPath -match $AllowedPattern) { # 新增代码+ProviderSecretLeakGate：判断当前路径是否命中允许规则；如果没有这行，所有测试值都会被误报。
      $IsAllowedPath = $true # 新增代码+ProviderSecretLeakGate：标记当前命中允许；如果没有这行，合法测试样本会失败。
      break # 新增代码+ProviderSecretLeakGate：命中后停止遍历；如果没有这行，会做无意义的额外匹配。
    } # 新增代码+ProviderSecretLeakGate：允许路径命中分支结束；如果没有这行，PowerShell 语法不完整。
  } # 新增代码+ProviderSecretLeakGate：允许路径遍历结束；如果没有这行，PowerShell 语法不完整。
  if (-not $IsAllowedPath) { # 新增代码+ProviderSecretLeakGate：处理不在允许目录的测试值；如果没有这行，生产代码里的测试 key 会漏过。
    $UnexpectedUnitTestSecretMatches += $MatchLine # 新增代码+ProviderSecretLeakGate：记录违规命中；如果没有这行，失败时没有定位信息。
  } # 新增代码+ProviderSecretLeakGate：违规命中分支结束；如果没有这行，PowerShell 语法不完整。
} # 新增代码+ProviderSecretLeakGate：固定测试值命中遍历结束；如果没有这行，PowerShell 语法不完整。

if ($UnexpectedUnitTestSecretMatches.Count -gt 0) { # 新增代码+ProviderSecretLeakGate：判断是否存在违规测试值；如果没有这行，违规命中不会让脚本失败。
  Write-Host "Provider secret leak scan failed: unit-test-secret-value appeared outside allowed test/evidence paths." # 新增代码+ProviderSecretLeakGate：输出失败摘要；如果没有这行，用户不知道违规类型。
  $UnexpectedUnitTestSecretMatches | ForEach-Object { Write-Host $_ } # 新增代码+ProviderSecretLeakGate：输出违规命中位置；如果没有这行，修复者无法定位文件。
  exit 1 # 新增代码+ProviderSecretLeakGate：用非零退出码阻断门禁；如果没有这行，release gate 会误过。
} # 新增代码+ProviderSecretLeakGate：违规测试值分支结束；如果没有这行，PowerShell 语法不完整。

$RuntimeArtifactRoots = @( # 新增代码+OpenAIConnectSecretGate：定义需要严格扫描的运行产物目录；如果没有这段，visual QA JSON/log 泄露字段名不会被单独拦截。
  "learning_agent/test/provider_settings_v1/task09_visual_qa", # 新增代码+OpenAIConnectSecretGate：扫描 Provider Settings V1 视觉验收产物；如果没有这行，旧视觉证据可能藏入测试密钥。
  "learning_agent/test/provider_settings_v2_openai_connect/task08_visual_qa", # 新增代码+OpenAIConnectSecretGate：扫描 OpenAI Connect V1 视觉验收产物；如果没有这行，本轮 OAuth 视觉证据可能出现 token 字段。
  "learning_agent/test/provider_settings_v2_openai_connect/visual_evidence" # 新增代码+OpenAIConnectSecretGate：扫描 Task 10 最终肉眼验收证据目录；如果没有这行，最终交付截图 JSON 可能绕过泄露门禁。
) # 新增代码+OpenAIConnectSecretGate：运行产物目录数组结束；如果没有这行，PowerShell 数组语法不完整。
$ExistingRuntimeArtifactRoots = $RuntimeArtifactRoots | Where-Object { Test-Path $_ } # 新增代码+OpenAIConnectSecretGate：只扫描当前存在的证据目录；如果没有这行，未生成的目录会让 rg 报错。
if ($ExistingRuntimeArtifactRoots.Count -gt 0) { # 新增代码+OpenAIConnectSecretGate：仅在存在运行产物目录时执行严格扫描；如果没有这行，空项目会误失败。
  $RuntimeSecretPattern = 'access_token|refresh_token|id_token|secret_ref|oauth-secret-test-value|unit-test-secret-value|sk-[A-Za-z0-9]{12,}|Authorization:\s*Bearer|api_key.*sk-' # 新增代码+OpenAIConnectSecretGate：定义运行产物禁止出现的敏感模式；如果没有这行，OAuth 字段名和测试密钥无法被抓住。
  $RuntimeSecretMatches = @(& rg -n --glob '!*.png' --glob '!*.map' --glob '!**/source_copies/**' $RuntimeSecretPattern $ExistingRuntimeArtifactRoots 2>&1) # 修改代码+OpenAIConnectSecretGate：扫描 JSON/log/text 运行产物并把无命中结果固定成空数组；如果没有这行，StrictMode 下零命中会因为 `$null.Count` 直接失败。
  $RuntimeSecretExitCode = $LASTEXITCODE # 新增代码+OpenAIConnectSecretGate：保存运行产物扫描退出码；如果没有这行，后续命令会覆盖 rg 结果。
  if ($RuntimeSecretExitCode -gt 1) { # 新增代码+OpenAIConnectSecretGate：处理 rg 自身错误；如果没有这行，扫描器故障可能被误当没有泄漏。
    Write-Host "Provider secret leak scan failed: rg returned $RuntimeSecretExitCode during runtime artifact scan." # 新增代码+OpenAIConnectSecretGate：输出扫描器错误摘要；如果没有这行，排查不知道是工具失败。
    $RuntimeSecretMatches | ForEach-Object { Write-Host $_ } # 新增代码+OpenAIConnectSecretGate：输出 rg 错误详情；如果没有这行，路径或 glob 问题难以定位。
    exit 1 # 新增代码+OpenAIConnectSecretGate：扫描器异常时失败；如果没有这行，release gate 可能误过。
  } # 新增代码+OpenAIConnectSecretGate：运行产物扫描器错误分支结束；如果没有这行，PowerShell 语法不完整。
  if ($RuntimeSecretMatches.Count -gt 0) { # 新增代码+OpenAIConnectSecretGate：判断运行产物是否命中禁止模式；如果没有这行，visual QA JSON 泄露字段名不会失败。
    Write-Host "Provider secret leak scan failed: runtime visual evidence contains token, secret locator, or raw test secret text." # 新增代码+OpenAIConnectSecretGate：输出运行产物失败摘要；如果没有这行，用户不知道是证据文件污染。
    $RuntimeSecretMatches | ForEach-Object { Write-Host $_ } # 新增代码+OpenAIConnectSecretGate：输出违规运行产物位置；如果没有这行，修复者无法定位 JSON/log。
    exit 1 # 新增代码+OpenAIConnectSecretGate：用非零退出码阻断门禁；如果没有这行，受污染证据会进入 release gate。
  } # 新增代码+OpenAIConnectSecretGate：运行产物违规分支结束；如果没有这行，PowerShell 语法不完整。
} # 新增代码+OpenAIConnectSecretGate：运行产物扫描分支结束；如果没有这行，PowerShell 语法不完整。

Write-Host "Provider secret leak scan passed." # 新增代码+ProviderSecretLeakGate：输出成功摘要；如果没有这行，人工运行时不知道扫描已完成。
