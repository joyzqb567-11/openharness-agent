param(  # 新增代码+ProductionAcceptance：脚本参数段开始；如果没有这行代码，用户无法覆盖 manifest 或输出目录。
    [string]$ManifestPath = "",  # 新增代码+ProductionAcceptance：允许用户传入自定义 manifest 路径；如果没有这行代码，调试矩阵变体时只能改源码。
    [string]$OutputRoot = ""  # 新增代码+ProductionAcceptance：允许用户传入自定义输出根目录；如果没有这行代码，CI 或手动复验不方便分开放证据。
)  # 新增代码+ProductionAcceptance：脚本参数段结束；如果没有这行代码，PowerShell 参数语法不完整。
$ErrorActionPreference = "Stop"  # 新增代码+ProductionAcceptance：遇到脚本级错误立即停止；如果没有这行代码，runner 可能在半失败状态继续写假报告。
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path  # 新增代码+ProductionAcceptance：定位 acceptance_controller 目录；如果没有这行代码，相对路径会受当前工作目录影响。
if ([string]::IsNullOrWhiteSpace($ManifestPath)) {  # 新增代码+ProductionAcceptance：判断用户是否传入 manifest；如果没有这行代码，默认路径不会生效。
    $ManifestPath = Join-Path $ScriptRoot "windows_computer_use_production_matrix.json"  # 新增代码+ProductionAcceptance：使用默认生产矩阵 manifest；如果没有这行代码，runner 不知道要跑哪些场景。
}  # 新增代码+ProductionAcceptance：结束默认 manifest 判断；如果没有这行代码，PowerShell 语法不完整。
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {  # 新增代码+ProductionAcceptance：判断用户是否传入输出目录；如果没有这行代码，默认报告目录不会生效。
    $OutputRoot = Join-Path $ScriptRoot "runs"  # 新增代码+ProductionAcceptance：默认把矩阵报告写到 acceptance_controller/runs；如果没有这行代码，证据路径不统一。
}  # 新增代码+ProductionAcceptance：结束默认输出目录判断；如果没有这行代码，PowerShell 语法不完整。
$ManifestFullPath = (Resolve-Path -LiteralPath $ManifestPath).Path  # 新增代码+ProductionAcceptance：解析 manifest 绝对路径；如果没有这行代码，报告里只会有不稳定相对路径。
$Manifest = Get-Content -LiteralPath $ManifestFullPath -Raw -Encoding UTF8 | ConvertFrom-Json  # 新增代码+ProductionAcceptance：读取并解析 manifest；如果没有这行代码，runner 无法知道场景列表。
$ControllerPath = Join-Path $ScriptRoot "controller.ps1"  # 新增代码+ProductionAcceptance：定位现有 acceptance controller；如果没有这行代码，runner 可能调用错入口。
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"  # 新增代码+ProductionAcceptance：生成本轮矩阵时间戳；如果没有这行代码，多次运行会互相覆盖。
$MatrixRunDir = Join-Path $OutputRoot "windows_computer_use_production_matrix-$Timestamp"  # 新增代码+ProductionAcceptance：生成本轮矩阵证据目录；如果没有这行代码，汇总报告没有独立空间。
New-Item -ItemType Directory -Force -Path $MatrixRunDir | Out-Null  # 新增代码+ProductionAcceptance：创建矩阵证据目录；如果没有这行代码，后续日志和报告写入会失败。
$MatrixLogPath = Join-Path $MatrixRunDir "matrix_runner.log"  # 新增代码+ProductionAcceptance：定义 runner 总日志路径；如果没有这行代码，用户无法复盘每条 controller 输出。
$MatrixJsonPath = Join-Path $MatrixRunDir "matrix_result.json"  # 新增代码+ProductionAcceptance：定义矩阵 JSON 报告路径；如果没有这行代码，自动化系统没有结构化结果。
$MatrixMarkdownPath = Join-Path $MatrixRunDir "matrix_result.md"  # 新增代码+ProductionAcceptance：定义矩阵 Markdown 报告路径；如果没有这行代码，用户只能读机器 JSON。
$ScenarioResults = New-Object System.Collections.Generic.List[object]  # 新增代码+ProductionAcceptance：创建场景结果列表；如果没有这行代码，runner 无法累计每条结果。

function Resolve-MatrixPath {  # 新增代码+ProductionAcceptance：函数段开始，把 manifest 里的相对路径解析成绝对路径；如果没有这段函数，runner 会受启动目录影响。
    param([string]$PathText)  # 新增代码+ProductionAcceptance：声明待解析路径参数；如果没有这行代码，函数拿不到 manifest 里的路径。
    if ([System.IO.Path]::IsPathRooted($PathText)) {  # 新增代码+ProductionAcceptance：判断是否已经是绝对路径；如果没有这行代码，绝对路径会被错误拼接。
        return $PathText  # 新增代码+ProductionAcceptance：绝对路径原样返回；如果没有这行代码，用户自定义路径会失效。
    }  # 新增代码+ProductionAcceptance：结束绝对路径判断；如果没有这行代码，PowerShell 语法不完整。
    return (Join-Path $ScriptRoot $PathText)  # 新增代码+ProductionAcceptance：相对路径按 acceptance_controller 目录解析；如果没有这行代码，runner 找不到 scenario 文件。
}  # 新增代码+ProductionAcceptance：函数段结束，Resolve-MatrixPath 到此结束；如果没有这个边界说明，初学者不容易看出路径解析范围。

function Get-ExistingText {  # 新增代码+ProductionAcceptance：函数段开始，读取存在的文本证据文件；如果没有这段函数，token 校验要重复写容错逻辑。
    param([string]$PathText)  # 新增代码+ProductionAcceptance：声明待读取文件路径；如果没有这行代码，函数不知道要读哪个文件。
    if ([string]::IsNullOrWhiteSpace($PathText)) {  # 新增代码+ProductionAcceptance：检查空路径；如果没有这行代码，空字符串会触发不必要的文件错误。
        return ""  # 新增代码+ProductionAcceptance：空路径返回空文本；如果没有这行代码，缺少可选日志会导致整条场景失败。
    }  # 新增代码+ProductionAcceptance：结束空路径判断；如果没有这行代码，PowerShell 语法不完整。
    if (-not (Test-Path -LiteralPath $PathText)) {  # 新增代码+ProductionAcceptance：检查文件是否存在；如果没有这行代码，读取缺失文件会抛异常。
        return ""  # 新增代码+ProductionAcceptance：缺失文件返回空文本；如果没有这行代码，失败场景可能因为缺日志掩盖真实原因。
    }  # 新增代码+ProductionAcceptance：结束文件存在判断；如果没有这行代码，PowerShell 语法不完整。
    return (Get-Content -LiteralPath $PathText -Raw -Encoding UTF8)  # 新增代码+ProductionAcceptance：读取 UTF-8 文本；如果没有这行代码，token 校验无法使用日志内容。
}  # 新增代码+ProductionAcceptance：函数段结束，Get-ExistingText 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。

function Test-RequiredTokens {  # 新增代码+ProductionAcceptance：函数段开始，检查 manifest 要求的 token 是否都出现在证据文本中；如果没有这段函数，矩阵会只相信 controller 断言。
    param([object[]]$RequiredTokens, [string]$EvidenceText)  # 新增代码+ProductionAcceptance：声明 token 列表和证据文本参数；如果没有这行代码，函数无法执行比对。
    $MissingTokens = New-Object System.Collections.Generic.List[string]  # 新增代码+ProductionAcceptance：创建缺失 token 列表；如果没有这行代码，失败报告无法说明缺了什么。
    foreach ($Token in @($RequiredTokens)) {  # 新增代码+ProductionAcceptance：逐个检查必需 token；如果没有这行代码，只能检查整个列表对象。
        $TokenText = [string]$Token  # 新增代码+ProductionAcceptance：把 token 转成字符串；如果没有这行代码，JSON 值类型可能影响 contains。
        if (-not $EvidenceText.Contains($TokenText)) {  # 新增代码+ProductionAcceptance：判断证据文本是否包含 token；如果没有这行代码，缺失证据不会被发现。
            $MissingTokens.Add($TokenText) | Out-Null  # 新增代码+ProductionAcceptance：记录缺失 token；如果没有这行代码，报告无法定位失败证据。
        }  # 新增代码+ProductionAcceptance：结束单 token 缺失判断；如果没有这行代码，PowerShell 语法不完整。
    }  # 新增代码+ProductionAcceptance：结束 token 遍历；如果没有这行代码，PowerShell 语法不完整。
    return [ordered]@{ passed = ($MissingTokens.Count -eq 0); missing = @($MissingTokens) }  # 新增代码+ProductionAcceptance：返回 token 校验摘要；如果没有这行代码，调用方拿不到校验结果。
}  # 新增代码+ProductionAcceptance：函数段结束，Test-RequiredTokens 到此结束；如果没有这个边界说明，初学者不容易看出 token 校验范围。

"WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_START=$Timestamp" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出矩阵开始标记；如果没有这行代码，用户无法在终端快速确认 runner 已启动。
foreach ($Entry in @($Manifest.scenarios)) {  # 新增代码+ProductionAcceptance：逐条运行 manifest 场景；如果没有这行代码，矩阵不会执行任何验收。
    $ScenarioId = [string]$Entry.id  # 新增代码+ProductionAcceptance：读取场景 id；如果没有这行代码，报告无法区分不同 workflow。
    $ScenarioFamily = [string]$Entry.family  # 新增代码+ProductionAcceptance：读取场景 family；如果没有这行代码，报告无法按能力分类。
    $ScenarioPath = Resolve-MatrixPath ([string]$Entry.scenario_path)  # 新增代码+ProductionAcceptance：解析场景文件路径；如果没有这行代码，controller 找不到 JSON 场景。
    $ScenarioLogPath = Join-Path $MatrixRunDir "$ScenarioId-controller.log"  # 新增代码+ProductionAcceptance：定义本场景 controller 输出日志；如果没有这行代码，单场景失败不易复盘。
    "SCENARIO_START id=$ScenarioId family=$ScenarioFamily path=$ScenarioPath" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出场景开始信息；如果没有这行代码，长矩阵运行中用户不知道进行到哪里。
    Start-Sleep -Seconds 3  # 新增代码+ProductionAcceptance：每条真实 GUI 场景启动前短暂停顿；如果没有这行代码，上一条终端或 Explorer 关闭动画可能抢走下一条焦点。
    $ExitCode = 9001  # 新增代码+ProductionAcceptance：初始化退出码为异常值；如果没有这行代码，controller 未启动时退出码不明确。
    $OutputLines = @()  # 新增代码+ProductionAcceptance：初始化 controller 输出数组；如果没有这行代码，失败路径可能访问未定义变量。
    $ResultJson = ""  # 新增代码+ProductionAcceptance：初始化 result.json 路径；如果没有这行代码，场景缺结果时报告字段不稳定。
    $ResultObject = $null  # 新增代码+ProductionAcceptance：初始化 result 对象；如果没有这行代码，读取失败时后续字段访问不安全。
    $FailureReason = ""  # 新增代码+ProductionAcceptance：初始化失败原因；如果没有这行代码，报告里会缺少人类可读原因。
    if (-not (Test-Path -LiteralPath $ScenarioPath)) {  # 新增代码+ProductionAcceptance：先检查场景文件存在；如果没有这行代码，controller 会以更难懂的错误失败。
        $FailureReason = "scenario_file_missing"  # 新增代码+ProductionAcceptance：记录场景文件缺失原因；如果没有这行代码，用户不知道是配置文件没创建。
    } else {  # 新增代码+ProductionAcceptance：场景存在时才运行 controller；如果没有这行代码，缺文件场景仍会尝试执行。
        try {  # 新增代码+ProductionAcceptance：捕获 controller 启动或执行异常；如果没有这行代码，一个场景异常会打断整个矩阵报告。
            $OutputLines = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ControllerPath -ScenarioPath $ScenarioPath 2>&1  # 新增代码+ProductionAcceptance：调用现有 controller 启动真实可见终端；如果没有这行代码，矩阵不会执行真实验收。
            $ExitCode = $LASTEXITCODE  # 新增代码+ProductionAcceptance：保存 controller 退出码；如果没有这行代码，报告无法区分通过和失败。
        } catch {  # 新增代码+ProductionAcceptance：处理 PowerShell 调用异常；如果没有这行代码，异常会阻止后续场景继续运行。
            $OutputLines = @($_.Exception.Message)  # 新增代码+ProductionAcceptance：把异常消息放入输出；如果没有这行代码，失败日志没有错误内容。
            $ExitCode = 9002  # 新增代码+ProductionAcceptance：用专门退出码表示 runner 调用异常；如果没有这行代码，异常和普通失败难以区分。
        }  # 新增代码+ProductionAcceptance：结束 controller 调用异常处理；如果没有这行代码，PowerShell 语法不完整。
        $OutputLines | Set-Content -LiteralPath $ScenarioLogPath -Encoding UTF8  # 新增代码+ProductionAcceptance：保存 controller 输出日志；如果没有这行代码，矩阵汇总后无法回看每条 stdout。
        $ResultLine = @($OutputLines | Where-Object { ([string]$_).StartsWith("RESULT_JSON=") } | Select-Object -Last 1)  # 新增代码+ProductionAcceptance：从 controller 输出中寻找 result.json；如果没有这行代码，runner 不知道证据目录。
        if ($ResultLine.Count -gt 0) {  # 新增代码+ProductionAcceptance：判断是否找到了 result 行；如果没有这行代码，空结果会触发 substring 错误。
            $ResultJson = ([string]$ResultLine[0]).Substring("RESULT_JSON=".Length)  # 新增代码+ProductionAcceptance：截取 result.json 路径；如果没有这行代码，无法读取 controller 结构化结果。
        }  # 新增代码+ProductionAcceptance：结束 result 行解析；如果没有这行代码，PowerShell 语法不完整。
        if ((-not [string]::IsNullOrWhiteSpace($ResultJson)) -and (Test-Path -LiteralPath $ResultJson)) {  # 新增代码+ProductionAcceptance：确认 result.json 路径可读；如果没有这行代码，读取缺失结果会抛异常。
            $ResultObject = Get-Content -LiteralPath $ResultJson -Raw -Encoding UTF8 | ConvertFrom-Json  # 新增代码+ProductionAcceptance：解析 controller result.json；如果没有这行代码，报告无法读取 completed 和 screenshot 字段。
        } else {  # 新增代码+ProductionAcceptance：没有可读 result.json 时进入失败原因分支；如果没有这行代码，失败场景缺少解释。
            $FailureReason = "result_json_missing"  # 新增代码+ProductionAcceptance：记录结果文件缺失；如果没有这行代码，用户不知道 controller 是否写出证据。
        }  # 新增代码+ProductionAcceptance：结束 result.json 读取分支；如果没有这行代码，PowerShell 语法不完整。
    }  # 新增代码+ProductionAcceptance：结束场景存在判断；如果没有这行代码，PowerShell 语法不完整。
    $Completed = ($ResultObject -ne $null) -and ([bool]$ResultObject.completed)  # 新增代码+ProductionAcceptance：读取 completed 状态；如果没有这行代码，报告没有 controller 通过事实。
    $AssertionPassed = ($ResultObject -ne $null) -and ($ResultObject.assertion -ne $null) -and ([bool]$ResultObject.assertion.passed)  # 新增代码+ProductionAcceptance：读取 assertion.passed；如果没有这行代码，报告无法体现断言是否通过。
    $MarkerPassed = ($ResultObject -ne $null) -and ($ResultObject.assertion -ne $null) -and ([bool]$ResultObject.assertion.marker_passed)  # 新增代码+ProductionAcceptance：读取 marker_passed；如果没有这行代码，报告无法确认最终 marker。
    $RunDir = if ($ResultObject -ne $null) { [string]$ResultObject.run_dir } else { "" }  # 新增代码+ProductionAcceptance：读取场景 run_dir；如果没有这行代码，用户找不到 controller 证据目录。
    $ReadableLogPath = if (-not [string]::IsNullOrWhiteSpace($RunDir)) { Join-Path $RunDir "latest_run_readable.md" } else { "" }  # 新增代码+ProductionAcceptance：定位 readable log；如果没有这行代码，token 校验会漏掉用户可读日志。
    $DebugLogPath = if ($ResultObject -ne $null) { [string]$ResultObject.copied_debug_log } else { "" }  # 新增代码+ProductionAcceptance：读取归档 debug log；如果没有这行代码，token 校验会少一份关键证据。
    $PermissionLedgerText = ""  # 新增代码+ProductionAcceptance：初始化权限决策文本；如果没有这行代码，response=n 这类 controller ledger 证据无法加入 token 校验。
    if (($ResultObject -ne $null) -and ($ResultObject.permission_policy_decisions -ne $null)) {  # 新增代码+ProductionAcceptance：检查 result.json 是否包含权限决策列表；如果没有这行代码，非权限场景会访问空字段。
        foreach ($Decision in @($ResultObject.permission_policy_decisions)) {  # 新增代码+ProductionAcceptance：逐条展开权限决策；如果没有这行代码，多权限场景只能看到最后一次或完全看不到。
            $PermissionLedgerText = $PermissionLedgerText + "`npermission_decision response=$([string]$Decision.response) reason=$([string]$Decision.reason) tool=$([string]$Decision.tool_name)"  # 新增代码+ProductionAcceptance：生成 response=n/response=y 可搜索证据；如果没有这行代码，矩阵无法证明 controller 实际输入了拒绝。
        }  # 新增代码+ProductionAcceptance：结束权限决策遍历；如果没有这行代码，PowerShell 语法不完整。
    }  # 新增代码+ProductionAcceptance：结束权限 ledger 判断；如果没有这行代码，PowerShell 语法不完整。
    $EvidenceText = (@($OutputLines) -join "`n") + "`n" + (Get-ExistingText $ResultJson) + "`n" + (Get-ExistingText $DebugLogPath) + "`n" + (Get-ExistingText $ReadableLogPath) + "`n" + $PermissionLedgerText  # 新增代码+ProductionAcceptance：合并 stdout、result、debug、readable log 和权限 ledger；如果没有这行代码，manifest token 校验不完整。
    $TokenCheck = Test-RequiredTokens -RequiredTokens @($Entry.required_tokens) -EvidenceText $EvidenceText  # 新增代码+ProductionAcceptance：执行 manifest token 校验；如果没有这行代码，矩阵无法发现证据词缺失。
    $StartupScreenshot = if ($ResultObject -ne $null) { [string]$ResultObject.startup_screenshot } else { "" }  # 新增代码+ProductionAcceptance：读取启动截图路径；如果没有这行代码，截图门禁无法验证。
    $PromptScreenshot = if ($ResultObject -ne $null) { [string]$ResultObject.prompt_screenshot } else { "" }  # 新增代码+ProductionAcceptance：读取 prompt 截图路径；如果没有这行代码，输入证据无法验证。
    $FinalScreenshot = if ($ResultObject -ne $null) { [string]$ResultObject.final_screenshot } else { "" }  # 新增代码+ProductionAcceptance：读取最终截图路径；如果没有这行代码，最终画面证据无法验证。
    $ScreenshotPassed = (-not [string]::IsNullOrWhiteSpace($StartupScreenshot)) -and (Test-Path -LiteralPath $StartupScreenshot) -and (-not [string]::IsNullOrWhiteSpace($PromptScreenshot)) -and (Test-Path -LiteralPath $PromptScreenshot) -and (-not [string]::IsNullOrWhiteSpace($FinalScreenshot)) -and (Test-Path -LiteralPath $FinalScreenshot)  # 新增代码+ProductionAcceptance：确认三张截图存在且路径非空；如果没有这行代码，真实可见终端证据可能缺失。
    if ([string]::IsNullOrWhiteSpace($FailureReason) -and ($ExitCode -ne 0)) {  # 新增代码+ProductionAcceptance：controller 非零退出时补失败原因；如果没有这行代码，报告只显示数字退出码。
        $FailureReason = "controller_exit_code_$ExitCode"  # 新增代码+ProductionAcceptance：记录 controller 退出码；如果没有这行代码，用户不知道失败层级。
    }  # 新增代码+ProductionAcceptance：结束退出码失败原因补充；如果没有这行代码，PowerShell 语法不完整。
    if ([string]::IsNullOrWhiteSpace($FailureReason) -and (-not [bool]$TokenCheck.passed)) {  # 新增代码+ProductionAcceptance：token 缺失时补失败原因；如果没有这行代码，证据缺失不够醒目。
        $FailureReason = "required_tokens_missing"  # 新增代码+ProductionAcceptance：记录 token 缺失原因；如果没有这行代码，用户要打开 JSON 才能看出缺词。
    }  # 新增代码+ProductionAcceptance：结束 token 失败原因补充；如果没有这行代码，PowerShell 语法不完整。
    if ([string]::IsNullOrWhiteSpace($FailureReason) -and (-not $ScreenshotPassed)) {  # 新增代码+ProductionAcceptance：截图缺失时补失败原因；如果没有这行代码，可见证据缺失不够醒目。
        $FailureReason = "required_screenshots_missing"  # 新增代码+ProductionAcceptance：记录截图缺失原因；如果没有这行代码，用户不知道是证据门禁失败。
    }  # 新增代码+ProductionAcceptance：结束截图失败原因补充；如果没有这行代码，PowerShell 语法不完整。
    $ScenarioPassed = ($ExitCode -eq 0) -and $Completed -and $AssertionPassed -and $MarkerPassed -and ([bool]$TokenCheck.passed) -and $ScreenshotPassed  # 新增代码+ProductionAcceptance：合成矩阵级通过条件；如果没有这行代码，报告无法统一判定单场景结果。
    if ($ScenarioPassed) {  # 新增代码+ProductionAcceptance：判断场景是否通过；如果没有这行代码，日志不会显示单场景结果。
        "SCENARIO_PASS id=$ScenarioId result=$ResultJson" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出场景通过信息；如果没有这行代码，长矩阵运行中用户无法确认进度。
    } else {  # 新增代码+ProductionAcceptance：场景失败时进入失败日志分支；如果没有这行代码，失败不会有醒目标记。
        "SCENARIO_FAIL id=$ScenarioId reason=$FailureReason result=$ResultJson" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出场景失败信息；如果没有这行代码，用户要等总报告才知道失败。
    }  # 新增代码+ProductionAcceptance：结束单场景日志分支；如果没有这行代码，PowerShell 语法不完整。
    $ScenarioResults.Add([pscustomobject][ordered]@{ id = $ScenarioId; family = $ScenarioFamily; scenario_path = $ScenarioPath; exit_code = $ExitCode; completed = $Completed; assertion_passed = $AssertionPassed; marker_passed = $MarkerPassed; token_passed = [bool]$TokenCheck.passed; missing_tokens = @($TokenCheck.missing); screenshot_passed = $ScreenshotPassed; passed = $ScenarioPassed; failure_reason = $FailureReason; run_dir = $RunDir; result_json = $ResultJson; final_screenshot = $FinalScreenshot; controller_log = $ScenarioLogPath }) | Out-Null  # 修改代码+ProductionAcceptance：把单场景摘要以对象形式写入列表；如果没有这行代码，最终 JSON/Markdown 的属性筛选会被 OrderedDictionary 类型绊倒。
    Start-Sleep -Seconds 6  # 新增代码+ProductionAcceptance：每条真实 GUI 场景结束后等待桌面沉淀；如果没有这行代码，连续矩阵会更容易遇到窗口残留、焦点漂移或 Explorer 快捷键丢采样。
}  # 新增代码+ProductionAcceptance：结束 manifest 场景遍历；如果没有这行代码，PowerShell 语法不完整。
$ScenarioArray = @($ScenarioResults.ToArray())  # 新增代码+ProductionAcceptance：把泛型列表转换成普通数组；如果没有这行代码，PowerShell 管道计数在泛型列表上可能出现类型不匹配。
$PassedScenarios = @($ScenarioArray | Where-Object { [bool]$_.passed })  # 新增代码+ProductionAcceptance：筛出通过场景；如果没有这行代码，报告无法稳定计算 passed_count。
$FailedScenarios = @($ScenarioArray | Where-Object { -not [bool]$_.passed })  # 新增代码+ProductionAcceptance：筛出失败场景；如果没有这行代码，报告无法稳定计算 failed_count。
$OverallPassed = ($FailedScenarios.Count -eq 0)  # 修改代码+ProductionAcceptance：用失败数量计算矩阵总通过状态；如果没有这行代码，runner 不知道最终退出码。
$MatrixResult = [ordered]@{ schema_version = 1; matrix_id = [string]$Manifest.matrix_id; matrix_name = [string]$Manifest.matrix_name; started_at = $Timestamp; completed_at = (Get-Date -Format "yyyyMMdd_HHmmss"); manifest_path = $ManifestFullPath; run_dir = $MatrixRunDir; passed = $OverallPassed; scenario_count = $ScenarioArray.Count; passed_count = $PassedScenarios.Count; failed_count = $FailedScenarios.Count; scenarios = @($ScenarioArray) }  # 修改代码+ProductionAcceptance：构造矩阵 JSON 结果并使用稳定计数；如果没有这行代码，外部系统无法稳定读取总状态。
$MatrixResult | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $MatrixJsonPath -Encoding UTF8  # 新增代码+ProductionAcceptance：写入矩阵 JSON 报告；如果没有这行代码，成功或失败都没有结构化证据。
$MarkdownLines = New-Object System.Collections.Generic.List[string]  # 新增代码+ProductionAcceptance：创建 Markdown 行列表；如果没有这行代码，用户可读报告无法生成。
$MarkdownLines.Add("# Windows Computer Use Production Matrix") | Out-Null  # 新增代码+ProductionAcceptance：写入 Markdown 标题；如果没有这行代码，报告打开后不清楚用途。
$MarkdownLines.Add("") | Out-Null  # 新增代码+ProductionAcceptance：插入空行提升可读性；如果没有这行代码，标题和正文会挤在一起。
$MarkdownLines.Add("- passed: $OverallPassed") | Out-Null  # 新增代码+ProductionAcceptance：写入总通过状态；如果没有这行代码，用户要读 JSON 才知道结论。
$MarkdownLines.Add("- run_dir: $MatrixRunDir") | Out-Null  # 新增代码+ProductionAcceptance：写入矩阵证据目录；如果没有这行代码，用户找不到截图和日志。
$MarkdownLines.Add("- scenario_count: $($ScenarioResults.Count)") | Out-Null  # 新增代码+ProductionAcceptance：写入场景数量；如果没有这行代码，用户不知道本轮覆盖范围。
$MarkdownLines.Add("") | Out-Null  # 新增代码+ProductionAcceptance：插入表格前空行；如果没有这行代码，Markdown 表格可能和列表粘在一起。
$MarkdownLines.Add("| id | family | passed | failure_reason | result_json | final_screenshot |") | Out-Null  # 新增代码+ProductionAcceptance：写入表头；如果没有这行代码，用户可读报告没有明细结构。
$MarkdownLines.Add("|---|---|---:|---|---|---|") | Out-Null  # 新增代码+ProductionAcceptance：写入表格分隔行；如果没有这行代码，Markdown 不会渲染成表格。
foreach ($Scenario in @($ScenarioArray)) {  # 修改代码+ProductionAcceptance：逐条写入已转换数组中的 Markdown 明细；如果没有这行代码，泛型列表会在 Windows PowerShell 下触发类型不匹配。
    $MarkdownLines.Add("| $($Scenario.id) | $($Scenario.family) | $($Scenario.passed) | $($Scenario.failure_reason) | $($Scenario.result_json) | $($Scenario.final_screenshot) |") | Out-Null  # 新增代码+ProductionAcceptance：写入单场景表格行；如果没有这行代码，用户不能快速定位失败场景。
}  # 新增代码+ProductionAcceptance：结束 Markdown 明细遍历；如果没有这行代码，PowerShell 语法不完整。
$MarkdownLines | Set-Content -LiteralPath $MatrixMarkdownPath -Encoding UTF8  # 新增代码+ProductionAcceptance：写入 Markdown 报告；如果没有这行代码，用户缺少易读总结。
"WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED=$OverallPassed" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出机器可读总状态；如果没有这行代码，调用方难以判断矩阵是否通过。
"MATRIX_RESULT_JSON=$MatrixJsonPath" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出矩阵 JSON 路径；如果没有这行代码，调用方要自己找结果文件。
"MATRIX_RESULT_MD=$MatrixMarkdownPath" | Tee-Object -FilePath $MatrixLogPath -Append | Out-Host  # 新增代码+ProductionAcceptance：输出矩阵 Markdown 路径；如果没有这行代码，用户不容易打开可读报告。
if (-not $OverallPassed) {  # 新增代码+ProductionAcceptance：矩阵失败时返回非零；如果没有这行代码，自动化会把失败当成功。
    exit 2  # 新增代码+ProductionAcceptance：用 2 表示矩阵验收失败；如果没有这行代码，失败边界不清楚。
}  # 新增代码+ProductionAcceptance：结束失败退出分支；如果没有这行代码，PowerShell 语法不完整。
exit 0  # 新增代码+ProductionAcceptance：矩阵通过时返回 0；如果没有这行代码，调用方无法用退出码判断通过。

