param(  # 新增代码+AcceptanceController: 定义控制器参数入口；若没有这行代码，外部 agent 无法指定不同场景文件
    [string]$ScenarioPath = "",  # 新增代码+AcceptanceController: 接收场景 JSON 路径；若没有这行代码，控制器只能跑写死场景
    [string]$RunRoot = "",  # 新增代码+AcceptanceController: 允许外部指定结果根目录；若没有这行代码，所有结果只能写到默认 runs 目录
    [switch]$KeepWindowOpen  # 新增代码+AcceptanceController: 控制成功后是否保留真实终端窗口；若没有这行代码，调试时无法保留现场
)  # 新增代码+AcceptanceController: 结束参数定义；若没有这行代码，PowerShell 无法解析脚本参数
$ErrorActionPreference = "Stop"  # 新增代码+AcceptanceController: 遇到错误立即停止；若没有这行代码，窗口控制或文件写入失败可能被误判为通过
Add-Type -AssemblyName System.Windows.Forms  # 新增代码+AcceptanceController: 加载剪贴板和键盘发送能力；若没有这行代码，控制器无法向真实终端输入 prompt
Add-Type -AssemblyName System.Drawing  # 新增代码+AcceptanceController: 加载截图图形库；若没有这行代码，控制器无法保存可见终端截图证据
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # 新增代码+AcceptanceController: 获取 controller.ps1 所在目录；若没有这行代码，默认场景和结果路径会依赖调用目录
$LearningAgentDir = Split-Path -Parent $ScriptDir  # 新增代码+AcceptanceController: 获取 learning_agent 目录；若没有这行代码，控制器找不到 start_oauth_agent.bat
$RepoRoot = Split-Path -Parent $LearningAgentDir  # 新增代码+AcceptanceController: 获取 OpenHarness-main 根目录；若没有这行代码，启动 bat 时工作区可能错误
$DefaultScenarioPath = Join-Path $ScriptDir "scenarios\smoke.json"  # 新增代码+AcceptanceController: 定义默认 smoke 场景；若没有这行代码，用户不传参数时无法快速自检
if ([string]::IsNullOrWhiteSpace($ScenarioPath)) {  # 新增代码+AcceptanceController: 检查用户是否没有传场景路径；若没有这行代码，空路径会导致读取失败
    $ScenarioPath = $DefaultScenarioPath  # 新增代码+AcceptanceController: 空场景路径时使用默认 smoke；若没有这行代码，控制器默认不可运行
}  # 新增代码+AcceptanceController: 结束默认场景分支；若没有这行代码，PowerShell 语法不完整
if (-not [System.IO.Path]::IsPathRooted($ScenarioPath)) {  # 新增代码+AcceptanceController: 检查场景路径是否是相对路径；若没有这行代码，相对路径会按未知目录解析
    $ScenarioPath = Join-Path $ScriptDir $ScenarioPath  # 新增代码+AcceptanceController: 相对路径按 controller 目录解析；若没有这行代码，外部 agent 传 scenarios/foo.json 可能找不到
}  # 新增代码+AcceptanceController: 结束相对路径处理；若没有这行代码，PowerShell 语法不完整
if (-not (Test-Path -LiteralPath $ScenarioPath)) {  # 新增代码+AcceptanceController: 检查场景文件是否存在；若没有这行代码，后续读取会抛出不友好的异常
    throw "找不到验收场景文件：$ScenarioPath"  # 新增代码+AcceptanceController: 给出清楚的缺文件错误；若没有这行代码，用户不知道该修哪个路径
}  # 新增代码+AcceptanceController: 结束场景存在性检查；若没有这行代码，PowerShell 语法不完整
$Scenario = Get-Content -Raw -Encoding UTF8 -LiteralPath $ScenarioPath | ConvertFrom-Json  # 新增代码+AcceptanceController: 读取并解析场景 JSON；若没有这行代码，控制器无法获得 prompt 和断言
$ScenarioName = [string]$Scenario.name  # 新增代码+AcceptanceController: 读取场景名；若没有这行代码，结果目录和窗口标题无法按场景区分
if ([string]::IsNullOrWhiteSpace($ScenarioName)) {  # 新增代码+AcceptanceController: 检查场景名是否为空；若没有这行代码，空名字会导致路径和报告难以识别
    throw "场景 JSON 缺少 name 字段。"  # 新增代码+AcceptanceController: 明确提示缺少 name；若没有这行代码，用户不知道 JSON 哪里不对
}  # 新增代码+AcceptanceController: 结束场景名检查；若没有这行代码，PowerShell 语法不完整
$OutputPrefix = [string]$Scenario.output_prefix  # 新增代码+AcceptanceController: 读取输出文件名前缀；若没有这行代码，不同场景的证据文件命名不直观
if ([string]::IsNullOrWhiteSpace($OutputPrefix)) {  # 新增代码+AcceptanceController: 检查场景是否没有输出前缀；若没有这行代码，空前缀会生成难看的文件名
    $OutputPrefix = $ScenarioName  # 新增代码+AcceptanceController: 没有前缀时用场景名兜底；若没有这行代码，结果文件可能无法区分场景
}  # 新增代码+AcceptanceController: 结束输出前缀兜底；若没有这行代码，PowerShell 语法不完整
$RunId = (Get-Date).ToString("yyyyMMdd_HHmmss")  # 新增代码+AcceptanceController: 生成本轮运行编号；若没有这行代码，多次运行会互相覆盖证据
if ([string]::IsNullOrWhiteSpace($RunRoot)) {  # 新增代码+AcceptanceController: 检查外部是否未指定结果根目录；若没有这行代码，默认路径无法生效
    $RunRoot = Join-Path $ScriptDir "runs"  # 新增代码+AcceptanceController: 默认把结果写到 acceptance_controller/runs；若没有这行代码，证据会散落在脚本目录
}  # 新增代码+AcceptanceController: 结束默认结果根目录分支；若没有这行代码，PowerShell 语法不完整
if (-not [System.IO.Path]::IsPathRooted($RunRoot)) {  # 新增代码+AcceptanceController: 检查结果根目录是否是相对路径；若没有这行代码，相对结果目录会依赖调用目录
    $RunRoot = Join-Path $ScriptDir $RunRoot  # 新增代码+AcceptanceController: 相对结果目录按 controller 目录解析；若没有这行代码，外部 agent 很难找到输出
}  # 新增代码+AcceptanceController: 结束结果根目录解析；若没有这行代码，PowerShell 语法不完整
$RunDir = Join-Path $RunRoot "$ScenarioName-$RunId"  # 新增代码+AcceptanceController: 拼出本轮独立结果目录；若没有这行代码，本轮事件和截图会覆盖旧证据
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null  # 新增代码+AcceptanceController: 创建结果目录；若没有这行代码，写 result.json 和截图会失败
$BatPath = Join-Path $LearningAgentDir "start_oauth_agent.bat"  # 新增代码+AcceptanceController: 定位真实可见终端启动 bat；若没有这行代码，规则十七要求的入口不会被启动
$DebugLog = Join-Path $LearningAgentDir "debug_logs\latest_run_readable.md"  # 新增代码+AcceptanceController: 定位 agent 最新可读调试日志；若没有这行代码，控制器无法核对工具调用证据
$EventLog = Join-Path $RunDir "events.jsonl"  # 新增代码+AcceptanceController: 定义 acceptance harness 事件日志路径；若没有这行代码，控制器无法稳定观察状态
$ResultJson = Join-Path $RunDir "result.json"  # 新增代码+AcceptanceController: 定义统一结果 JSON 路径；若没有这行代码，外部 agent 没有固定结果入口
$StartupScreenshot = Join-Path $RunDir "01_startup.png"  # 新增代码+AcceptanceController: 定义启动截图路径；若没有这行代码，无法证明窗口真实启动
$PromptScreenshot = Join-Path $RunDir "02_prompt_sent.png"  # 新增代码+AcceptanceController: 定义 prompt 输入截图路径；若没有这行代码，无法证明真实窗口输入
$FinalScreenshot = Join-Path $RunDir "03_final.png"  # 新增代码+AcceptanceController: 定义最终截图路径；若没有这行代码，无法人工复核终端状态
$CopiedDebugLog = Join-Path $RunDir "latest_run_readable.md"  # 新增代码+AcceptanceController: 定义调试日志归档路径；若没有这行代码，latest 日志后续可能被覆盖
$WindowTitlePrefix = [string]$Scenario.window_title_prefix  # 新增代码+AcceptanceController: 读取窗口标题前缀；若没有这行代码，窗口标题无法按场景区分
if ([string]::IsNullOrWhiteSpace($WindowTitlePrefix)) {  # 新增代码+AcceptanceController: 检查场景是否没有标题前缀；若没有这行代码，空标题会影响窗口聚焦
    $WindowTitlePrefix = "LearningAgent-Acceptance"  # 新增代码+AcceptanceController: 使用通用标题兜底；若没有这行代码，窗口查找不稳定
}  # 新增代码+AcceptanceController: 结束窗口标题兜底；若没有这行代码，PowerShell 语法不完整
$WindowTitle = "$WindowTitlePrefix-$((Get-Date).ToString('HHmmss'))"  # 新增代码+AcceptanceController: 生成本轮唯一窗口标题；若没有这行代码，多窗口时容易找错对象
$Prompt = @($Scenario.prompt_lines) -join " "  # 新增代码+AcceptanceController: 把场景 prompt_lines 拼成单行输入；若没有这行代码，终端 input() 会把换行当成多轮输入
if ([string]::IsNullOrWhiteSpace($Prompt)) {  # 新增代码+AcceptanceController: 检查场景 prompt 是否为空；若没有这行代码，空任务可能被误提交
    throw "场景 JSON 的 prompt_lines 不能为空。"  # 新增代码+AcceptanceController: 给出清楚的空 prompt 错误；若没有这行代码，失败原因不明确
}  # 新增代码+AcceptanceController: 结束 prompt 检查；若没有这行代码，PowerShell 语法不完整
$MaxSeconds = [int]$Scenario.max_seconds  # 新增代码+AcceptanceController: 读取场景超时时间；若没有这行代码，长任务和短任务无法分别控制等待时间
if ($MaxSeconds -le 0) {  # 新增代码+AcceptanceController: 检查场景超时是否非法；若没有这行代码，0 秒或负数会让脚本立刻失败
    $MaxSeconds = 300  # 新增代码+AcceptanceController: 非法超时时使用 300 秒兜底；若没有这行代码，场景小错误会导致验收不可用
}  # 新增代码+AcceptanceController: 结束超时兜底；若没有这行代码，PowerShell 语法不完整
$FinalLogWaitSeconds = [int]$Scenario.final_log_wait_seconds  # 新增代码+AcceptanceController: 读取最终回答后等待日志落盘的秒数；若没有这行代码，日志写入稍慢时可能误判失败
if ($FinalLogWaitSeconds -le 0) {  # 新增代码+AcceptanceController: 检查最终等待时间是否非法；若没有这行代码，0 秒会让日志断言不稳定
    $FinalLogWaitSeconds = 30  # 新增代码+AcceptanceController: 使用 30 秒兜底；若没有这行代码，默认场景没有稳定日志缓冲
}  # 新增代码+AcceptanceController: 结束最终等待兜底；若没有这行代码，PowerShell 语法不完整
$PostSuccessWaitSeconds = [int]$Scenario.post_success_wait_seconds  # 新增代码+GoogleHumanVisible: 读取成功后继续停留的秒数；若没有这行代码，拟人演示窗口可能一闪而过
if ($PostSuccessWaitSeconds -lt 0) {  # 新增代码+GoogleHumanVisible: 检查停留秒数是否为负数；若没有这行代码，负数会让 Start-Sleep 报错
    $PostSuccessWaitSeconds = 0  # 新增代码+GoogleHumanVisible: 负数时按 0 秒处理；若没有这行代码，场景小错误会导致验收失败
}  # 新增代码+GoogleHumanVisible: 结束停留秒数兜底；若没有这行代码，PowerShell 语法不完整
$SuccessMarker = [string]$Scenario.success_marker  # 新增代码+AcceptanceController: 读取最终回答成功标记；若没有这行代码，控制器无法确认回答属于本轮场景
$RequiredEventStates = @($Scenario.required_event_states)  # 新增代码+AcceptanceController: 读取必需事件状态列表；若没有这行代码，场景无法表达事件门槛
$DebugLogContains = @($Scenario.debug_log_contains)  # 新增代码+AcceptanceController: 读取调试日志必含文本；若没有这行代码，场景无法证明工具调用或目标内容
$EventAnswerContains = @($Scenario.event_answer_contains)  # 新增代码+AcceptanceController: 读取最终回答事件预览必含文本；若没有这行代码，场景无法只靠事件确认核心输出
$PermissionPolicy = $Scenario.permission_policy  # 新增代码+RealChromeConnect: 读取场景级权限策略；若没有这行代码，真实 Chrome connect 场景无法限制自动同意范围
$MaxPermissionSentCount = $null  # 新增代码+真实浏览器客户模式: 初始化权限响应次数上限为空；若没有这行代码，未声明上限的旧场景会被错误限制
if ($Scenario.PSObject.Properties.Name -contains "max_permission_sent_count") {  # 新增代码+真实浏览器客户模式: 只在场景显式声明时启用无 y 次数门禁；若没有这行代码，空字段和 0 无法区分
    $MaxPermissionSentCount = [int]$Scenario.max_permission_sent_count  # 新增代码+真实浏览器客户模式: 读取允许的最大权限响应次数；若没有这行代码，controller 无法验证用户是否还被要求输入 y
}  # 新增代码+真实浏览器客户模式: 结束权限响应上限读取；若没有这行代码，PowerShell 语法不完整
$PermissionDefaultResponse = "allow"  # 新增代码+RealChromeConnect: 没有策略时保持旧场景默认允许；若没有这行代码，smoke 和天气场景会因为缺策略而卡住权限
$PermissionAllowContains = @()  # 新增代码+RealChromeConnect: 初始化允许匹配词列表；若没有这行代码，权限判断函数无法区分显式白名单和旧默认行为
$PermissionDenyContains = @()  # 新增代码+RealChromeConnect: 初始化拒绝匹配词列表；若没有这行代码，高风险工具无法通过场景规则阻断
$PermissionAllowToolNames = @()  # 新增代码+StructuredPermissionLedger: 初始化结构化工具白名单；若没有这行代码，controller 仍只能靠 action 文本 contains 放行工具
$PermissionDenyToolNames = @()  # 新增代码+StructuredPermissionLedger: 初始化结构化工具拒绝表；若没有这行代码，controller 无法按准确工具名拒绝高风险工具
$PermissionAllowUrlPrefixes = @()  # 新增代码+StructuredPermissionLedger: 初始化 URL 前缀白名单；若没有这行代码，browser_open 无法被限制到指定公开来源
if ($PermissionPolicy) {  # 新增代码+RealChromeConnect: 只有场景声明权限策略时才启用白名单/黑名单；若没有这行代码，旧场景会被空策略误伤
    $CandidateDefaultResponse = [string]$PermissionPolicy.default_response  # 新增代码+RealChromeConnect: 读取场景配置的默认权限响应；若没有这行代码，默认拒绝策略无法表达
    if ($CandidateDefaultResponse -in @("allow", "deny")) {  # 新增代码+RealChromeConnect: 只接受 allow/deny 两种安全明确的值；若没有这行代码，拼写错误会变成不可预测行为
        $PermissionDefaultResponse = $CandidateDefaultResponse  # 新增代码+RealChromeConnect: 应用场景默认响应；若没有这行代码，connect 场景的默认拒绝不会生效
    }  # 新增代码+RealChromeConnect: 结束默认响应合法性检查；若没有这行代码，PowerShell 语法不完整
    $PermissionAllowContains = @($PermissionPolicy.allow_contains) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }  # 新增代码+RealChromeConnect: 读取并清理允许匹配词；若没有这行代码，空字符串可能误匹配所有权限
    $PermissionDenyContains = @($PermissionPolicy.deny_contains) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }  # 新增代码+RealChromeConnect: 读取并清理拒绝匹配词；若没有这行代码，拒绝策略可能被空值污染
    $PermissionAllowToolNames = @($PermissionPolicy.allow_tool_names) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }  # 新增代码+StructuredPermissionLedger: 读取结构化工具白名单；若没有这行代码，allow_tool_names 场景不会生效
    $PermissionDenyToolNames = @($PermissionPolicy.deny_tool_names) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }  # 新增代码+StructuredPermissionLedger: 读取结构化工具拒绝表；若没有这行代码，deny_tool_names 场景不会生效
    $PermissionAllowUrlPrefixes = @($PermissionPolicy.allow_url_prefixes) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }  # 新增代码+StructuredPermissionLedger: 读取 URL 前缀白名单；若没有这行代码，browser_open 参数 URL 无法精确限制
}  # 新增代码+RealChromeConnect: 结束权限策略读取；若没有这行代码，PowerShell 语法不完整
$PermissionSentCount = 0  # 新增代码+AcceptanceController: 记录已经处理的权限请求数量；若没有这行代码，控制器可能对同一权限重复输入 y
$PermissionPolicyDecisions = @()  # 新增代码+RealChromeConnect: 记录每次权限 y/n 的原因；若没有这行代码，真实 Chrome 验收后无法复盘是否误放行
$PromptSent = $false  # 新增代码+AcceptanceController: 记录 prompt 是否已发送；若没有这行代码，控制器无法避免重复提交
$PromptReceived = $false  # 新增代码+AcceptanceController: 记录 agent 是否确认收到 prompt；若没有这行代码，终端漏输入会被误判为已提交
$PromptSendAttempts = 0  # 新增代码+AcceptanceController: 记录 prompt 发送次数；若没有这行代码，重试次数无法限制
$PromptLastSentAt = $null  # 新增代码+AcceptanceController: 记录上次发送 prompt 的时间；若没有这行代码，控制器无法判断何时重试
$FinalPrinted = $false  # 新增代码+AcceptanceController: 记录最终回答事件是否出现；若没有这行代码，结果无法区分模型未答和断言失败
$FinalPrintedAt = $null  # 新增代码+AcceptanceController: 记录最终回答出现时间；若没有这行代码，最终日志等待无法计算
$ScenarioPassed = $false  # 新增代码+AcceptanceController: 保存场景断言是否通过；若没有这行代码，最终退出码没有统一来源
$LastAssertion = [ordered]@{}  # 新增代码+AcceptanceController: 保存最近一次断言详情；若没有这行代码，失败时 result.json 缺少定位信息
$RunStartedAt = Get-Date  # 新增代码+AcceptanceController: 记录本轮开始时间；若没有这行代码，旧 debug log 可能造成假通过

function Save-ScreenShot {  # 新增代码+AcceptanceController: 定义截图函数；若没有这行代码，三处截图会重复复杂图形代码
    param([string]$Path)  # 新增代码+AcceptanceController: 接收截图保存路径；若没有这行代码，函数不知道输出到哪里
    $Bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds  # 新增代码+AcceptanceController: 获取主屏幕边界；若没有这行代码，截图不知道屏幕尺寸
    $Bitmap = New-Object System.Drawing.Bitmap $Bounds.Width, $Bounds.Height  # 新增代码+AcceptanceController: 创建屏幕大小图片对象；若没有这行代码，屏幕像素没有承载对象
    $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)  # 新增代码+AcceptanceController: 创建绘图对象；若没有这行代码，无法复制屏幕内容
    $Graphics.CopyFromScreen($Bounds.Location, [System.Drawing.Point]::Empty, $Bounds.Size)  # 新增代码+AcceptanceController: 把真实屏幕复制到图片；若没有这行代码，截图会是空白
    $Bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)  # 新增代码+AcceptanceController: 保存 PNG 截图；若没有这行代码，用户无法查看真实终端画面
    $Graphics.Dispose()  # 新增代码+AcceptanceController: 释放绘图资源；若没有这行代码，长时间运行可能占用图形句柄
    $Bitmap.Dispose()  # 新增代码+AcceptanceController: 释放图片资源；若没有这行代码，图片文件可能被占用
}  # 新增代码+AcceptanceController: 结束截图函数；若没有这行代码，后续代码会被错误当成函数体

function Get-AcceptanceEvents {  # 新增代码+AcceptanceController: 读取 acceptance harness JSONL 事件；若没有这行代码，控制器只能靠盲等和截图猜状态
    if (-not (Test-Path -LiteralPath $EventLog)) {  # 新增代码+AcceptanceController: 检查事件日志是否已创建；若没有这行代码，读取不存在文件会报错
        return @()  # 新增代码+AcceptanceController: 没有事件时返回空数组；若没有这行代码，调用方需要处理异常
    }  # 新增代码+AcceptanceController: 结束事件日志存在性检查；若没有这行代码，PowerShell 语法不完整
    $Rows = @()  # 新增代码+AcceptanceController: 初始化事件对象数组；若没有这行代码，解析结果没有容器保存
    $Lines = Get-Content -LiteralPath $EventLog -Encoding UTF8  # 新增代码+AcceptanceController: 按 UTF-8 读取事件日志；若没有这行代码，中文 payload 可能乱码
    foreach ($Line in $Lines) {  # 新增代码+AcceptanceController: 遍历 JSONL 的每一行；若没有这行代码，只能读取单个事件
        if ([string]::IsNullOrWhiteSpace($Line)) {  # 新增代码+AcceptanceController: 跳过空行；若没有这行代码，空行会导致 JSON 解析失败
            continue  # 新增代码+AcceptanceController: 空行直接进入下一轮；若没有这行代码，解析流程会中断
        }  # 新增代码+AcceptanceController: 结束空行判断；若没有这行代码，PowerShell 语法不完整
        try {  # 新增代码+AcceptanceController: 捕获文件正在写入时的半行 JSON；若没有这行代码，读写竞争会让控制器失败
            $Rows += ($Line | ConvertFrom-Json)  # 新增代码+AcceptanceController: 把 JSON 行转成对象；若没有这行代码，后续无法按 state 判断
        } catch {  # 新增代码+AcceptanceController: 处理暂时解析失败的 JSON 行；若没有这行代码，半行事件会中断验收
            continue  # 新增代码+AcceptanceController: 跳过坏行等待下一次读取；若没有这行代码，控制器缺少容错
        }  # 新增代码+AcceptanceController: 结束 JSON 解析保护；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+AcceptanceController: 结束事件行遍历；若没有这行代码，PowerShell 语法不完整
    return $Rows  # 新增代码+AcceptanceController: 返回事件对象数组；若没有这行代码，调用方拿不到状态
}  # 新增代码+AcceptanceController: 结束事件读取函数；若没有这行代码，后续函数会被嵌套进去

function Count-State {  # 新增代码+AcceptanceController: 统计某个状态出现次数；若没有这行代码，权限和 ready 判断会重复复杂表达式
    param([object[]]$Events, [string]$State)  # 新增代码+AcceptanceController: 接收事件数组和目标状态；若没有这行代码，函数不知道统计哪个 state
    return @($Events | Where-Object { $_.state -eq $State }).Count  # 新增代码+AcceptanceController: 返回匹配状态数量；若没有这行代码，控制器无法判断新事件是否出现
}  # 新增代码+AcceptanceController: 结束状态统计函数；若没有这行代码，PowerShell 语法不完整

function Test-ContainsIgnoreCase {  # 新增代码+RealChromeConnect: 定义大小写不敏感的包含判断；若没有这行代码，权限匹配会被大小写差异绕过
    param([string]$Text, [string]$Needle)  # 新增代码+RealChromeConnect: 接收原文和要查找的片段；若没有这行代码，函数不知道比较哪两个字符串
    if ([string]::IsNullOrWhiteSpace($Needle)) {  # 新增代码+RealChromeConnect: 空匹配词直接视为不匹配；若没有这行代码，空字符串会匹配所有权限
        return $false  # 新增代码+RealChromeConnect: 返回不匹配保护策略边界；若没有这行代码，空 deny/allow 可能放大权限
    }  # 新增代码+RealChromeConnect: 结束空匹配词判断；若没有这行代码，PowerShell 语法不完整
    return $Text.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0  # 新增代码+RealChromeConnect: 执行大小写不敏感查找；若没有这行代码，工具名大小写变化可能导致白名单失效
}  # 新增代码+RealChromeConnect: 结束包含判断函数；若没有这行代码，后续函数会被错误嵌套

function Test-EqualsIgnoreCase {  # 新增代码+StructuredPermissionLedger: 定义大小写不敏感的精确相等判断；若没有这行代码，工具名白名单只能退回模糊 contains
    param([string]$Text, [string]$Expected)  # 新增代码+StructuredPermissionLedger: 接收实际工具名和期望工具名；若没有这行代码，函数不知道比较哪两个值
    if ([string]::IsNullOrWhiteSpace($Expected)) {  # 新增代码+StructuredPermissionLedger: 空期望值直接视为不匹配；若没有这行代码，空工具名可能误放行所有工具
        return $false  # 新增代码+StructuredPermissionLedger: 返回不匹配保护权限边界；若没有这行代码，空白名单项会污染判断
    }  # 新增代码+StructuredPermissionLedger: 结束空期望值判断；若没有这行代码，PowerShell 语法不完整
    return [string]::Equals($Text, $Expected, [System.StringComparison]::OrdinalIgnoreCase)  # 新增代码+StructuredPermissionLedger: 执行忽略大小写的精确匹配；若没有这行代码，工具名可能被子串误匹配
}  # 新增代码+StructuredPermissionLedger: 结束精确相等函数；若没有这行代码，后续函数会被错误嵌套

function Test-StartsWithIgnoreCase {  # 新增代码+StructuredPermissionLedger: 定义大小写不敏感的前缀判断；若没有这行代码，URL 白名单只能靠脆弱 contains
    param([string]$Text, [string]$Prefix)  # 新增代码+StructuredPermissionLedger: 接收实际 URL 和允许前缀；若没有这行代码，函数不知道比较哪两个字符串
    if ([string]::IsNullOrWhiteSpace($Prefix)) {  # 新增代码+StructuredPermissionLedger: 空前缀直接视为不匹配；若没有这行代码，空字符串会允许所有 URL
        return $false  # 新增代码+StructuredPermissionLedger: 返回不匹配防止空前缀越权；若没有这行代码，URL 策略会被空项绕过
    }  # 新增代码+StructuredPermissionLedger: 结束空前缀判断；若没有这行代码，PowerShell 语法不完整
    return $Text.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)  # 新增代码+StructuredPermissionLedger: 执行忽略大小写的 URL 前缀匹配；若没有这行代码，browser_open 无法限制来源域名
}  # 新增代码+StructuredPermissionLedger: 结束前缀判断函数；若没有这行代码，后续函数会被错误嵌套

function Test-ListHasExactIgnoreCase {  # 新增代码+StructuredPermissionLedger: 检查列表是否精确包含某个值；若没有这行代码，allow/deny 工具名判断会重复循环
    param([object[]]$Items, [string]$Value)  # 新增代码+StructuredPermissionLedger: 接收候选列表和要查找的值；若没有这行代码，函数无法知道检查对象
    foreach ($Item in $Items) {  # 新增代码+StructuredPermissionLedger: 遍历每个候选项；若没有这行代码，只能检查第一项
        if (Test-EqualsIgnoreCase -Text $Value -Expected ([string]$Item)) {  # 新增代码+StructuredPermissionLedger: 判断候选项是否和目标值精确相等；若没有这行代码，工具名白名单不会命中
            return $true  # 新增代码+StructuredPermissionLedger: 命中后返回 true；若没有这行代码，白名单命中仍会继续走拒绝逻辑
        }  # 新增代码+StructuredPermissionLedger: 结束单项命中判断；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+StructuredPermissionLedger: 结束列表遍历；若没有这行代码，PowerShell 语法不完整
    return $false  # 新增代码+StructuredPermissionLedger: 遍历完没有命中则返回 false；若没有这行代码，调用方拿不到明确未命中结果
}  # 新增代码+StructuredPermissionLedger: 结束列表精确匹配函数；若没有这行代码，后续函数会被错误嵌套

function Get-PermissionArgumentValue {  # 新增代码+StructuredPermissionLedger: 从结构化 arguments 对象读取指定字段；若没有这行代码，URL 读取会散落在权限判断里
    param([object]$Arguments, [string]$Name)  # 新增代码+StructuredPermissionLedger: 接收参数对象和字段名；若没有这行代码，函数不知道读取哪个字段
    if ($null -eq $Arguments) {  # 新增代码+StructuredPermissionLedger: 处理没有 arguments 的旧事件；若没有这行代码，旧场景可能访问空对象报错
        return ""  # 新增代码+StructuredPermissionLedger: 没有参数时返回空字符串；若没有这行代码，调用方要重复写 null 判断
    }  # 新增代码+StructuredPermissionLedger: 结束空参数判断；若没有这行代码，PowerShell 语法不完整
    $Property = $Arguments.PSObject.Properties[$Name]  # 新增代码+StructuredPermissionLedger: 从 PSCustomObject 读取字段；若没有这行代码，不能兼容 ConvertFrom-Json 生成的对象
    if ($null -eq $Property) {  # 新增代码+StructuredPermissionLedger: 检查目标字段是否不存在；若没有这行代码，缺少 url 时会抛异常
        return ""  # 新增代码+StructuredPermissionLedger: 字段不存在时返回空字符串；若没有这行代码，URL 前缀判断缺少安全兜底
    }  # 新增代码+StructuredPermissionLedger: 结束字段存在性判断；若没有这行代码，PowerShell 语法不完整
    return [string]$Property.Value  # 新增代码+StructuredPermissionLedger: 返回字段值文本；若没有这行代码，URL 前缀判断拿不到实际 URL
}  # 新增代码+StructuredPermissionLedger: 结束参数字段读取函数；若没有这行代码，后续函数会被错误嵌套

function Get-PermissionResponse {  # 新增代码+RealChromeConnect: 根据场景权限策略计算本次应该输入 y 还是 n；若没有这行代码，controller 只能继续对所有权限输入 y
    param([object]$PermissionEvent)  # 修改代码+StructuredPermissionLedger: 接收完整 permission_required 事件；若没有这行代码，函数拿不到 payload.tool_name 和 payload.arguments
    $Action = [string]$PermissionEvent.payload.action  # 修改代码+StructuredPermissionLedger: 保留旧 action 文本供 contains 策略兼容；若没有这行代码，旧场景会失去匹配输入
    $ToolName = [string]$PermissionEvent.payload.tool_name  # 新增代码+StructuredPermissionLedger: 读取结构化工具名；若没有这行代码，allow_tool_names 无法精确生效
    $Arguments = $PermissionEvent.payload.arguments  # 新增代码+StructuredPermissionLedger: 读取结构化工具参数；若没有这行代码，URL 前缀白名单无法检查真实参数
    $Url = Get-PermissionArgumentValue -Arguments $Arguments -Name "url"  # 新增代码+StructuredPermissionLedger: 提取浏览器打开 URL；若没有这行代码，browser_open 不能限制到 Open-Meteo
    if (-not [string]::IsNullOrWhiteSpace($ToolName)) {  # 新增代码+StructuredPermissionLedger: 只有结构化工具名存在时进入精确工具策略；若没有这行代码，启动 MCP server 事件会被错误当成工具
        if (Test-ListHasExactIgnoreCase -Items $PermissionDenyToolNames -Value $ToolName) {  # 新增代码+StructuredPermissionLedger: 优先检查结构化工具拒绝表；若没有这行代码，高风险工具可能被宽泛文本白名单放行
            return [ordered]@{ response = "n"; reason = "deny_tool_name"; matched_text = $ToolName; tool_name = $ToolName; url = $Url }  # 新增代码+StructuredPermissionLedger: 命中拒绝工具时返回 n 和审计字段；若没有这行代码，result.json 无法说明拒绝哪个工具
        }  # 新增代码+StructuredPermissionLedger: 结束结构化拒绝命中判断；若没有这行代码，PowerShell 语法不完整
        if ($PermissionAllowToolNames.Count -gt 0) {  # 新增代码+StructuredPermissionLedger: 如果场景配置了结构化工具白名单；若没有这行代码，旧场景会被空白名单误伤
            if (-not (Test-ListHasExactIgnoreCase -Items $PermissionAllowToolNames -Value $ToolName)) {  # 新增代码+StructuredPermissionLedger: 检查当前工具是否不在白名单；若没有这行代码，未知工具可能继续走文本 allow 被误放行
                return [ordered]@{ response = "n"; reason = "not_in_allow_tool_names"; matched_text = ""; tool_name = $ToolName; url = $Url }  # 新增代码+StructuredPermissionLedger: 返回工具名白名单拒绝；若没有这行代码，未知工具缺少清楚拒绝原因
            }  # 新增代码+StructuredPermissionLedger: 结束不在白名单判断；若没有这行代码，PowerShell 语法不完整
            if ((Test-EqualsIgnoreCase -Text $ToolName -Expected "mcp__browser_automation__browser_open") -and ($PermissionAllowUrlPrefixes.Count -gt 0)) {  # 新增代码+StructuredPermissionLedger: 对 browser_open 额外检查 URL 前缀；若没有这行代码，允许 browser_open 就等于允许打开任意网站
                foreach ($UrlPrefix in $PermissionAllowUrlPrefixes) {  # 新增代码+StructuredPermissionLedger: 遍历允许的 URL 前缀；若没有这行代码，只能支持一个硬编码来源
                    if (Test-StartsWithIgnoreCase -Text $Url -Prefix ([string]$UrlPrefix)) {  # 新增代码+StructuredPermissionLedger: 检查实际 URL 是否位于允许前缀下；若没有这行代码，Open-Meteo 白名单不会生效
                        return [ordered]@{ response = "y"; reason = "allow_tool_name_and_url_prefix"; matched_text = [string]$UrlPrefix; tool_name = $ToolName; url = $Url }  # 新增代码+StructuredPermissionLedger: 返回工具名和 URL 前缀双命中允许；若没有这行代码，安全放行缺少审计证据
                    }  # 新增代码+StructuredPermissionLedger: 结束单个 URL 前缀命中判断；若没有这行代码，PowerShell 语法不完整
                }  # 新增代码+StructuredPermissionLedger: 结束 URL 前缀遍历；若没有这行代码，PowerShell 语法不完整
                return [ordered]@{ response = "n"; reason = "url_prefix_not_allowed"; matched_text = ""; tool_name = $ToolName; url = $Url }  # 新增代码+StructuredPermissionLedger: URL 不在白名单时拒绝；若没有这行代码，browser_open 可能打开未授权网站
            }  # 新增代码+StructuredPermissionLedger: 结束 browser_open URL 额外检查；若没有这行代码，PowerShell 语法不完整
            return [ordered]@{ response = "y"; reason = "allow_tool_name"; matched_text = $ToolName; tool_name = $ToolName; url = $Url }  # 新增代码+StructuredPermissionLedger: 非 URL 受限工具命中白名单后允许；若没有这行代码，profile/connect/snapshot 会被误拒绝
        }  # 新增代码+StructuredPermissionLedger: 结束结构化工具白名单处理；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+StructuredPermissionLedger: 结束结构化工具策略分支；若没有这行代码，PowerShell 语法不完整
    foreach ($DenyText in $PermissionDenyContains) {  # 新增代码+RealChromeConnect: 先检查拒绝列表，让黑名单优先于白名单；若没有这行代码，高风险工具可能被宽泛 allow 放行
        if (Test-ContainsIgnoreCase -Text $Action -Needle ([string]$DenyText)) {  # 新增代码+RealChromeConnect: 判断动作文本是否命中拒绝片段；若没有这行代码，拒绝规则不会生效
            return [ordered]@{ response = "n"; reason = "deny_contains"; matched_text = [string]$DenyText; tool_name = $ToolName; url = $Url }  # 修改代码+StructuredPermissionLedger: 命中文本拒绝时也返回结构化审计字段；若没有这行代码，result.json 会缺少工具名和 URL
        }  # 新增代码+RealChromeConnect: 结束拒绝命中判断；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+RealChromeConnect: 结束拒绝列表遍历；若没有这行代码，PowerShell 语法不完整
    foreach ($AllowText in $PermissionAllowContains) {  # 新增代码+RealChromeConnect: 再检查允许列表；若没有这行代码，白名单场景无法放行必要工具
        if (Test-ContainsIgnoreCase -Text $Action -Needle ([string]$AllowText)) {  # 新增代码+RealChromeConnect: 判断动作文本是否命中允许片段；若没有这行代码，显式白名单不会生效
            return [ordered]@{ response = "y"; reason = "allow_contains"; matched_text = [string]$AllowText; tool_name = $ToolName; url = $Url }  # 修改代码+StructuredPermissionLedger: 命中文本允许时也返回结构化审计字段；若没有这行代码，result.json 会缺少工具名和 URL
        }  # 新增代码+RealChromeConnect: 结束允许命中判断；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+RealChromeConnect: 结束允许列表遍历；若没有这行代码，PowerShell 语法不完整
    if ($PermissionAllowContains.Count -gt 0) {  # 新增代码+RealChromeConnect: 有白名单时，未命中任何 allow 的权限按拒绝处理；若没有这行代码，未知权限可能被默认 allow 放行
        return [ordered]@{ response = "n"; reason = "not_in_allow_list"; matched_text = ""; tool_name = $ToolName; url = $Url }  # 修改代码+StructuredPermissionLedger: 文本白名单未命中时也保留工具名和 URL；若没有这行代码，拒绝审计不完整
    }  # 新增代码+RealChromeConnect: 结束白名单兜底拒绝；若没有这行代码，PowerShell 语法不完整
    if ($PermissionDefaultResponse -eq "deny") {  # 新增代码+RealChromeConnect: 检查场景是否要求默认拒绝；若没有这行代码，显式默认拒绝不会生效
        return [ordered]@{ response = "n"; reason = "default_deny"; matched_text = ""; tool_name = $ToolName; url = $Url }  # 修改代码+StructuredPermissionLedger: 默认拒绝时保留结构化审计字段；若没有这行代码，result.json 难以复盘拒绝对象
    }  # 新增代码+RealChromeConnect: 结束默认拒绝判断；若没有这行代码，PowerShell 语法不完整
    return [ordered]@{ response = "y"; reason = "default_allow"; matched_text = ""; tool_name = $ToolName; url = $Url }  # 修改代码+StructuredPermissionLedger: 默认允许时也保留工具名和 URL；若没有这行代码，旧场景审计记录仍不完整
}  # 新增代码+RealChromeConnect: 结束权限响应函数；若没有这行代码，后续代码会被错误嵌套

function Activate-AgentWindow {  # 新增代码+AcceptanceController: 聚焦本轮真实终端窗口；若没有这行代码，键盘输入可能发到错误窗口
    $ActivatedByPid = $Shell.AppActivate($Process.Id)  # 新增代码+AcceptanceController: 优先按 cmd 进程 ID 聚焦；若没有这行代码，窗口标题变化时可能找不到
    if ($ActivatedByPid) {  # 新增代码+AcceptanceController: 判断 PID 聚焦是否成功；若没有这行代码，脚本不知道是否需要兜底
        return $true  # 新增代码+AcceptanceController: 成功时返回 true；若没有这行代码，调用方会误判聚焦失败
    }  # 新增代码+AcceptanceController: 结束 PID 聚焦分支；若没有这行代码，PowerShell 语法不完整
    $TerminalWindow = Get-Process | Where-Object { $_.MainWindowTitle -like "*$WindowTitle*" } | Select-Object -First 1  # 新增代码+AcceptanceController: 查找真正承载控制台的 Windows Terminal 窗口；若没有这行代码，cmd 子进程可能不是按键目标
    if ($TerminalWindow) {  # 新增代码+AcceptanceController: 判断是否找到目标终端窗口；若没有这行代码，脚本不知道是否可用窗口进程兜底
        return [bool]$Shell.AppActivate($TerminalWindow.Id)  # 新增代码+AcceptanceController: 用真实窗口进程 ID 聚焦；若没有这行代码，按键可能仍发不到 Windows Terminal
    }  # 新增代码+AcceptanceController: 结束 Windows Terminal 兜底分支；若没有这行代码，PowerShell 语法不完整
    return [bool]$Shell.AppActivate($WindowTitle)  # 新增代码+AcceptanceController: 最后用窗口标题兜底聚焦；若没有这行代码，PID 聚焦失败后没有备用方案
}  # 新增代码+AcceptanceController: 结束窗口聚焦函数；若没有这行代码，后续函数会被嵌套

function Send-TerminalKeys {  # 新增代码+AcceptanceController: 向真实终端发送快捷键；若没有这行代码，滚动和回车逻辑会散落重复
    param([string]$Keys)  # 新增代码+AcceptanceController: 接收 SendKeys 格式文本；若没有这行代码，函数不知道要发送什么
    if (-not (Activate-AgentWindow)) {  # 新增代码+AcceptanceController: 发送前确认窗口已聚焦；若没有这行代码，按键可能发到用户其他窗口
        throw "无法聚焦真实终端窗口，停止发送按键。"  # 新增代码+AcceptanceController: 聚焦失败时停止；若没有这行代码，测试可能污染其他窗口
    }  # 新增代码+AcceptanceController: 结束聚焦保护；若没有这行代码，PowerShell 语法不完整
    [System.Windows.Forms.SendKeys]::SendWait($Keys)  # 新增代码+AcceptanceController: 发送按键到当前窗口；若没有这行代码，控制器无法滚动或提交输入
}  # 新增代码+AcceptanceController: 结束按键发送函数；若没有这行代码，后续代码会被错误嵌套

function Send-TerminalTextLine {  # 新增代码+AcceptanceController: 向真实终端粘贴一整行文本并回车；若没有这行代码，中文长 prompt 很难稳定输入
    param([string]$Text)  # 新增代码+AcceptanceController: 接收要输入的文本；若没有这行代码，函数不知道 prompt 内容
    if (-not (Activate-AgentWindow)) {  # 新增代码+AcceptanceController: 粘贴前确认窗口聚焦；若没有这行代码，prompt 可能粘到别的应用
        throw "无法聚焦真实终端窗口，停止发送文本。"  # 新增代码+AcceptanceController: 聚焦失败时停止；若没有这行代码，风险会继续扩大
    }  # 新增代码+AcceptanceController: 结束聚焦保护；若没有这行代码，PowerShell 语法不完整
    [System.Windows.Forms.Clipboard]::SetText($Text)  # 新增代码+AcceptanceController: 把文本放到剪贴板；若没有这行代码，逐字发送中文容易失败
    Start-Sleep -Milliseconds 300  # 新增代码+AcceptanceController: 等待剪贴板内容就绪；若没有这行代码，终端可能粘贴旧内容
    [System.Windows.Forms.SendKeys]::SendWait("+{INSERT}")  # 新增代码+AcceptanceController: 用 Shift+Insert 粘贴到控制台；若没有这行代码，Ctrl+V 在某些终端配置下可能不生效
    [System.Windows.Forms.SendKeys]::SendWait("~")  # 新增代码+AcceptanceController: 发送回车提交输入；若没有这行代码，prompt 会停在输入行不执行
}  # 新增代码+AcceptanceController: 结束文本输入函数；若没有这行代码，PowerShell 语法不完整

function Test-ScenarioAssertions {  # 新增代码+AcceptanceController: 统一检查事件、最终回答预览和调试日志断言；若没有这行代码，每个场景会重复写判断逻辑
    $Events = @(Get-AcceptanceEvents)  # 新增代码+AcceptanceController: 读取当前事件列表；若没有这行代码，事件断言没有输入数据
    $StateChecks = [ordered]@{}  # 新增代码+AcceptanceController: 准备保存必需状态检查结果；若没有这行代码，result.json 无法显示缺哪个事件
    foreach ($State in $RequiredEventStates) {  # 新增代码+AcceptanceController: 遍历场景要求的事件状态；若没有这行代码，只能写死固定状态
        $StateChecks[$State] = ((Count-State -Events $Events -State $State) -gt 0)  # 新增代码+AcceptanceController: 记录每个状态是否出现；若没有这行代码，控制器无法判断事件门槛
    }  # 新增代码+AcceptanceController: 结束状态检查循环；若没有这行代码，PowerShell 语法不完整
    $FinalAnswerPreview = ""  # 修改代码+FullAnswerEvent: 初始化最终回答预览文本；若没有这行代码，result.json 缺少快速查看摘要
    $FinalAnswerText = ""  # 新增代码+FullAnswerEvent: 初始化完整最终回答文本；若没有这行代码，长回答只能用截断预览做断言
    foreach ($Event in $Events) {  # 修改代码+FullAnswerEvent: 遍历事件寻找 final_answer_printed；若没有这行代码，无法从事件里取最终回答
        if ($Event.state -eq "final_answer_printed") {  # 修改代码+FullAnswerEvent: 只处理最终回答事件；若没有这行代码，非最终事件可能被误用为答案
            if ($Event.payload.answer_preview) {  # 修改代码+FullAnswerEvent: 检查事件是否带短预览；若没有这行代码，旧事件缺字段时会访问空值
                $FinalAnswerPreview = [string]$Event.payload.answer_preview  # 修改代码+FullAnswerEvent: 保存最终回答预览；若没有这行代码，报告里无法快速显示答案开头
            }  # 修改代码+FullAnswerEvent: 结束短预览读取分支；若没有这行代码，PowerShell 语法不完整
            if ($Event.payload.answer_text) {  # 新增代码+FullAnswerEvent: 优先检查事件是否带完整回答；若没有这行代码，长回答后半段会继续无法断言
                $FinalAnswerText = [string]$Event.payload.answer_text  # 新增代码+FullAnswerEvent: 保存完整最终回答；若没有这行代码，browser_screenshot 等后半段字段会被截断误判缺失
            } elseif ($FinalAnswerText -eq "" -and $FinalAnswerPreview) {  # 新增代码+FullAnswerEvent: 兼容旧事件只有 answer_preview 的情况；若没有这行代码，旧场景回放会没有答案文本可查
                $FinalAnswerText = $FinalAnswerPreview  # 新增代码+FullAnswerEvent: 用预览兜底成答案文本；若没有这行代码，旧事件会全部回答断言失败
            }  # 新增代码+FullAnswerEvent: 结束完整回答兼容分支；若没有这行代码，PowerShell 语法不完整
        }  # 修改代码+FullAnswerEvent: 结束最终回答事件判断；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+AcceptanceController: 结束事件遍历；若没有这行代码，PowerShell 语法不完整
    $EventAnswerChecks = [ordered]@{}  # 新增代码+AcceptanceController: 准备保存事件回答断言结果；若没有这行代码，result.json 无法显示预览缺哪项
    foreach ($Text in $EventAnswerContains) {  # 新增代码+AcceptanceController: 遍历场景要求的最终回答片段；若没有这行代码，场景无法配置回答预览断言
        $EventAnswerChecks[$Text] = $FinalAnswerText.Contains([string]$Text)  # 修改代码+FullAnswerEvent: 检查完整最终回答是否包含目标片段；若没有这行代码，answer_preview 截断会导致真实成功被误判失败
    }  # 新增代码+AcceptanceController: 结束事件回答断言循环；若没有这行代码，PowerShell 语法不完整
    $LogText = ""  # 新增代码+AcceptanceController: 初始化调试日志文本；若没有这行代码，日志断言没有可检查内容
    $LogUpdated = $false  # 新增代码+AcceptanceController: 初始化日志是否属于本轮的标记；若没有这行代码，旧日志可能造成假通过
    if (Test-Path -LiteralPath $DebugLog) {  # 新增代码+AcceptanceController: 检查调试日志是否存在；若没有这行代码，读取不存在文件会报错
        $DebugItem = Get-Item -LiteralPath $DebugLog  # 新增代码+AcceptanceController: 获取日志元数据；若没有这行代码，无法比较更新时间
        $LogUpdated = $DebugItem.LastWriteTime -ge $RunStartedAt  # 新增代码+AcceptanceController: 判断日志是否本轮更新；若没有这行代码，旧日志可能被误用
        $LogText = Get-Content -Raw -Encoding UTF8 -LiteralPath $DebugLog  # 新增代码+AcceptanceController: 读取完整调试日志；若没有这行代码，无法证明工具调用和最终回答
    }  # 新增代码+AcceptanceController: 结束日志读取分支；若没有这行代码，PowerShell 语法不完整
    $DebugChecks = [ordered]@{}  # 新增代码+AcceptanceController: 准备保存调试日志断言结果；若没有这行代码，失败时不知道缺哪项
    foreach ($Text in $DebugLogContains) {  # 新增代码+AcceptanceController: 遍历场景要求的日志片段；若没有这行代码，场景无法配置工具调用证据
        $DebugChecks[$Text] = ($LogUpdated -and $LogText.Contains([string]$Text))  # 新增代码+AcceptanceController: 检查本轮日志是否包含目标片段；若没有这行代码，旧日志或缺失片段可能假通过
    }  # 新增代码+AcceptanceController: 结束日志断言循环；若没有这行代码，PowerShell 语法不完整
    $MarkerPassed = $true  # 新增代码+AcceptanceController: 默认无成功标记时视为通过；若没有这行代码，空 success_marker 会导致误判
    if (-not [string]::IsNullOrWhiteSpace($SuccessMarker)) {  # 新增代码+AcceptanceController: 如果场景配置了成功标记；若没有这行代码，所有场景都必须强制 marker
        $MarkerPassed = $FinalAnswerText.Contains($SuccessMarker) -or ($LogUpdated -and $LogText.Contains($SuccessMarker))  # 修改代码+FullAnswerEvent: 标记优先来自完整回答或调试日志；若没有这行代码，成功标记在长回答后段时可能误判
    }  # 新增代码+AcceptanceController: 结束成功标记检查；若没有这行代码，PowerShell 语法不完整
    $PermissionCountPassed = $true  # 新增代码+真实浏览器客户模式: 默认未声明权限次数上限时通过；若没有这行代码，旧场景会因为空上限被误判失败
    if ($MaxPermissionSentCount -ne $null) {  # 新增代码+真实浏览器客户模式: 只有场景显式声明上限才检查权限响应次数；若没有这行代码，无法把自然真实浏览器场景设置为 0 次 y
        $PermissionCountPassed = $PermissionSentCount -le $MaxPermissionSentCount  # 新增代码+真实浏览器客户模式: 比较已输入 y/n 次数是否超过上限；若没有这行代码，多弹权限也会被验收通过
    }  # 新增代码+真实浏览器客户模式: 结束权限次数检查；若没有这行代码，PowerShell 语法不完整
    $StatesPassed = -not ($StateChecks.Values -contains $false)  # 新增代码+AcceptanceController: 汇总必需事件是否全部出现；若没有这行代码，状态断言无法形成结论
    $EventAnswerPassed = -not ($EventAnswerChecks.Values -contains $false)  # 新增代码+AcceptanceController: 汇总最终回答预览断言；若没有这行代码，回答断言无法形成结论
    $DebugPassed = -not ($DebugChecks.Values -contains $false)  # 新增代码+AcceptanceController: 汇总调试日志断言；若没有这行代码，工具证据断言无法形成结论
    $Passed = $StatesPassed -and $EventAnswerPassed -and $DebugPassed -and $MarkerPassed -and $PermissionCountPassed  # 修改代码+真实浏览器客户模式: 汇总场景是否通过时纳入权限次数门禁；若没有这行代码，多次 y/N 仍可能被验收成通过
    return [ordered]@{ passed = $Passed; marker_passed = $MarkerPassed; permission_count_passed = $PermissionCountPassed; max_permission_sent_count = $MaxPermissionSentCount; permission_sent_count = $PermissionSentCount; log_updated = $LogUpdated; state_checks = $StateChecks; event_answer_checks = $EventAnswerChecks; debug_log_checks = $DebugChecks; final_answer_preview = $FinalAnswerPreview; final_answer_text_length = $FinalAnswerText.Length }  # 修改代码+真实浏览器客户模式: 返回完整断言报告并包含权限次数检查；若没有这行代码，外部 agent 无法定位是否因多弹 y 失败
}  # 新增代码+AcceptanceController: 结束断言函数；若没有这行代码，主流程会被错误嵌套

$Shell = New-Object -ComObject WScript.Shell  # 新增代码+AcceptanceController: 创建 Windows Shell 自动化对象；若没有这行代码，控制器不能聚焦窗口
$CmdLine = "/k title $WindowTitle && cd /d `"$RepoRoot`" && set `"LEARNING_AGENT_ACCEPTANCE_EVENT_LOG=$EventLog`" && call `"$BatPath`""  # 新增代码+AcceptanceController: 构造 cmd 命令设置事件日志并启动 bat；若没有这行代码，真实 bat 和 harness 事件不会同时启用
$Process = Start-Process -FilePath "cmd.exe" -ArgumentList $CmdLine -PassThru -WindowStyle Maximized  # 新增代码+AcceptanceController: 打开用户本地可见终端窗口；若没有这行代码，规则十七真实窗口验收不会发生
Start-Sleep -Seconds 4  # 新增代码+AcceptanceController: 等待窗口和启动文字出现；若没有这行代码，启动截图可能截不到 agent
Save-ScreenShot -Path $StartupScreenshot  # 新增代码+AcceptanceController: 保存启动截图；若没有这行代码，缺少真实窗口启动证据
$Deadline = (Get-Date).AddSeconds($MaxSeconds)  # 新增代码+AcceptanceController: 计算总超时点；若没有这行代码，等待循环没有停止条件
while ((Get-Date) -lt $Deadline) {  # 新增代码+AcceptanceController: 主循环按事件驱动授权、输入和断言；若没有这行代码，控制器无法自动完成验收
    $Events = @(Get-AcceptanceEvents)  # 新增代码+AcceptanceController: 读取当前事件列表；若没有这行代码，后续判断没有状态输入
    $PermissionEvents = @($Events | Where-Object { $_.state -eq "permission_required" })  # 修改代码+RealChromeConnect: 取出所有权限请求事件以便逐个按策略处理；若没有这行代码，只靠数量无法读取本次权限动作
    while ($PermissionSentCount -lt $PermissionEvents.Count) {  # 修改代码+RealChromeConnect: 逐个处理尚未响应的新权限请求；若没有这行代码，多权限场景可能漏响应或重复响应
        $PermissionEvent = $PermissionEvents[$PermissionSentCount]  # 新增代码+RealChromeConnect: 定位当前要处理的权限事件；若没有这行代码，控制器不知道本次应该根据哪个 action 决策
        $PermissionAction = [string]$PermissionEvent.payload.action  # 新增代码+RealChromeConnect: 读取权限动作文本；若没有这行代码，权限白名单和拒绝列表没有输入
        $PermissionToolName = [string]$PermissionEvent.payload.tool_name  # 新增代码+StructuredPermissionLedger: 读取结构化工具名供结果审计；若没有这行代码，result.json 只能保存 action 文本
        $PermissionArguments = $PermissionEvent.payload.arguments  # 新增代码+StructuredPermissionLedger: 读取结构化参数供结果审计；若没有这行代码，URL 等参数不会进入验收证据
        $PermissionRiskLevel = [string]$PermissionEvent.payload.risk_level  # 新增代码+StructuredPermissionLedger: 读取结构化风险等级供结果审计；若没有这行代码，验收证据缺少风险分类
        $PermissionRiskSummary = [string]$PermissionEvent.payload.risk_summary  # 新增代码+StructuredPermissionLedger: 读取结构化风险说明供结果审计；若没有这行代码，用户无法复盘工具为什么有风险
        $PermissionDecision = Get-PermissionResponse -PermissionEvent $PermissionEvent  # 修改代码+StructuredPermissionLedger: 用完整事件计算 y/n；若没有这行代码，工具名和 URL 前缀策略无法生效
        Send-TerminalTextLine -Text ([string]$PermissionDecision.response)  # 修改代码+RealChromeConnect: 按策略在真实终端输入 y 或 n；若没有这行代码，权限提示会卡住或继续无条件同意
        $PermissionPolicyDecisions += [ordered]@{ action_preview = $PermissionAction.Substring(0, [Math]::Min(500, $PermissionAction.Length)); tool_name = $PermissionToolName; arguments = $PermissionArguments; risk_level = $PermissionRiskLevel; risk_summary = $PermissionRiskSummary; url = [string]$PermissionDecision.url; response = [string]$PermissionDecision.response; reason = [string]$PermissionDecision.reason; matched_text = [string]$PermissionDecision.matched_text }  # 修改代码+StructuredPermissionLedger: 记录 action、工具名、参数、风险和决策原因；若没有这行代码，result.json 无法形成完整 tool-call ledger
        $PermissionSentCount = $PermissionSentCount + 1  # 修改代码+RealChromeConnect: 只推进一个已处理权限；若没有这行代码，多权限循环会重复处理同一事件
    }  # 修改代码+RealChromeConnect: 结束新权限处理循环；若没有这行代码，PowerShell 语法不完整
    $ReadyCount = Count-State -Events $Events -State "agent_ready_for_user_prompt"  # 新增代码+AcceptanceController: 统计 ready 事件数量；若没有这行代码，prompt 可能在错误阶段输入
    $PromptReceived = (Count-State -Events $Events -State "user_prompt_received") -gt 0  # 新增代码+AcceptanceController: 判断 agent 是否确认收到 prompt；若没有这行代码，终端漏输入会被误判提交成功
    $ShouldRetryPrompt = $PromptSent -and (-not $PromptReceived) -and ($PromptLastSentAt -ne $null) -and (((Get-Date) - $PromptLastSentAt).TotalSeconds -ge 12) -and ($PromptSendAttempts -lt 3)  # 新增代码+AcceptanceController: prompt 未确认时最多重试 3 次；若没有这行代码，一次粘贴失败会导致整轮超时
    if ((-not $PromptReceived) -and ($ReadyCount -gt 0) -and ((-not $PromptSent) -or $ShouldRetryPrompt)) {  # 新增代码+AcceptanceController: ready 后发送或重发 prompt；若没有这行代码，输入时机仍然不稳定
        Send-TerminalTextLine -Text $Prompt  # 新增代码+AcceptanceController: 把场景 prompt 输入真实终端；若没有这行代码，agent 不会执行场景任务
        $PromptSent = $true  # 新增代码+AcceptanceController: 标记 prompt 已发送；若没有这行代码，控制器无法记录输入状态
        $PromptSendAttempts = $PromptSendAttempts + 1  # 新增代码+AcceptanceController: 增加发送次数；若没有这行代码，重试上限无法生效
        $PromptLastSentAt = Get-Date  # 新增代码+AcceptanceController: 记录本次发送时间；若没有这行代码，控制器无法判断下一次重试时机
        Start-Sleep -Seconds 2  # 新增代码+AcceptanceController: 等待终端回显输入；若没有这行代码，截图可能截不到 prompt
        Save-ScreenShot -Path $PromptScreenshot  # 新增代码+AcceptanceController: 保存 prompt 截图；若没有这行代码，缺少真实输入证据
    }  # 新增代码+AcceptanceController: 结束 prompt 输入分支；若没有这行代码，PowerShell 语法不完整
    if ($PromptSent -and ((Count-State -Events $Events -State "final_answer_printed") -gt 0)) {  # 新增代码+AcceptanceController: 看到最终回答事件后开始断言；若没有这行代码，控制器不知道何时检查结果
        $FinalPrinted = $true  # 新增代码+AcceptanceController: 标记最终回答已打印；若没有这行代码，result.json 无法区分未回答和断言失败
        if ($FinalPrintedAt -eq $null) {  # 新增代码+AcceptanceController: 判断是否首次看到最终回答；若没有这行代码，最终时间会被每轮刷新
            $FinalPrintedAt = Get-Date  # 新增代码+AcceptanceController: 记录首次最终回答时间；若没有这行代码，日志等待时间无法计算
        }  # 新增代码+AcceptanceController: 结束首次最终回答判断；若没有这行代码，PowerShell 语法不完整
        $LastAssertion = Test-ScenarioAssertions  # 新增代码+AcceptanceController: 执行通用场景断言；若没有这行代码，final 事件可能假通过
        $ScenarioPassed = [bool]$LastAssertion.passed  # 新增代码+AcceptanceController: 保存断言通过状态；若没有这行代码，退出码没有依据
        if ($ScenarioPassed) {  # 新增代码+AcceptanceController: 如果场景断言已通过；若没有这行代码，成功后仍会继续等
            break  # 新增代码+AcceptanceController: 通过后退出主循环；若没有这行代码，脚本会无意义等到超时
        }  # 新增代码+AcceptanceController: 结束通过分支；若没有这行代码，PowerShell 语法不完整
        if (((Get-Date) - $FinalPrintedAt).TotalSeconds -ge $FinalLogWaitSeconds) {  # 新增代码+AcceptanceController: 最终回答后最多等场景配置秒数让日志落盘；若没有这行代码，失败会等满总超时
            break  # 新增代码+AcceptanceController: 超过最终等待后退出并保留失败证据；若没有这行代码，失败反馈太慢
        }  # 新增代码+AcceptanceController: 结束最终日志等待判断；若没有这行代码，PowerShell 语法不完整
    }  # 新增代码+AcceptanceController: 结束最终回答处理分支；若没有这行代码，PowerShell 语法不完整
    Start-Sleep -Seconds 2  # 新增代码+AcceptanceController: 降低轮询频率；若没有这行代码，控制器会高频读文件和抢焦点
}  # 新增代码+AcceptanceController: 结束主循环；若没有这行代码，PowerShell 语法不完整
Start-Sleep -Seconds 2  # 新增代码+AcceptanceController: 等终端最后刷新；若没有这行代码，最终截图可能截到回答前一刻
if ($FinalPrinted) {  # 新增代码+AcceptanceController: 只有最终回答已打印才尝试滚到底部；若没有这行代码，失败场景可能掩盖卡住位置
    Send-TerminalKeys -Keys "^{END}"  # 新增代码+AcceptanceController: 把 Windows Terminal 滚动到底部；若没有这行代码，截图可能停在启动日志附近
    Start-Sleep -Seconds 1  # 新增代码+AcceptanceController: 等待滚动重绘完成；若没有这行代码，最终截图可能仍是旧画面
}  # 新增代码+AcceptanceController: 结束滚动到底部分支；若没有这行代码，PowerShell 语法不完整
Save-ScreenShot -Path $FinalScreenshot  # 新增代码+AcceptanceController: 保存最终截图；若没有这行代码，缺少可见窗口最终证据
if (Test-Path -LiteralPath $DebugLog) {  # 新增代码+AcceptanceController: 检查是否有调试日志可归档；若没有这行代码，复制不存在文件会报错
    $DebugItemForCopy = Get-Item -LiteralPath $DebugLog  # 新增代码+AcceptanceController: 获取日志时间戳；若没有这行代码，无法判断日志是否属于本轮
    if ($DebugItemForCopy.LastWriteTime -ge $RunStartedAt) {  # 新增代码+AcceptanceController: 只复制本轮之后更新的日志；若没有这行代码，旧日志可能被归档为本轮证据
        Copy-Item -LiteralPath $DebugLog -Destination $CopiedDebugLog -Force  # 新增代码+AcceptanceController: 复制调试日志到结果目录；若没有这行代码，latest 日志后续可能被覆盖
    }  # 新增代码+AcceptanceController: 结束日志新旧判断；若没有这行代码，PowerShell 语法不完整
}  # 新增代码+AcceptanceController: 结束日志归档分支；若没有这行代码，PowerShell 语法不完整
if (-not $ScenarioPassed) {  # 新增代码+AcceptanceController: 如果主循环还没通过断言；若没有这行代码，失败结果可能缺少最后一次检查
    $LastAssertion = Test-ScenarioAssertions  # 新增代码+AcceptanceController: 最后再执行一次断言；若没有这行代码，刚落盘的日志可能没被记录
    $ScenarioPassed = [bool]$LastAssertion.passed  # 新增代码+AcceptanceController: 更新最终通过状态；若没有这行代码，结果可能停留在旧失败状态
}  # 新增代码+AcceptanceController: 结束最终补充断言；若没有这行代码，PowerShell 语法不完整
$FinalEvents = @(Get-AcceptanceEvents)  # 新增代码+AcceptanceController: 读取最终事件列表；若没有这行代码，result.json 缺少状态序列
$Result = [ordered]@{  # 新增代码+AcceptanceController: 构造统一 result.json 对象；若没有这行代码，外部 agent 无法稳定读取验收结果
    completed = $ScenarioPassed  # 新增代码+AcceptanceController: 记录场景是否通过；若没有这行代码，结果没有核心状态
    scenario = $ScenarioName  # 新增代码+AcceptanceController: 记录场景名；若没有这行代码，多场景结果难以区分
    scenario_path = $ScenarioPath  # 新增代码+AcceptanceController: 记录场景文件路径；若没有这行代码，后续复盘不知道用的是哪个配置
    run_dir = $RunDir  # 新增代码+AcceptanceController: 记录结果目录；若没有这行代码，外部 agent 难以定位证据文件
    final_printed = $FinalPrinted  # 新增代码+AcceptanceController: 记录最终回答事件是否出现；若没有这行代码，无法区分模型未答和断言失败
    prompt_sent = $PromptSent  # 新增代码+AcceptanceController: 记录 prompt 是否发送；若没有这行代码，失败时无法判断是否未 ready
    prompt_received = $PromptReceived  # 新增代码+AcceptanceController: 记录 prompt 是否被 agent 确认收到；若没有这行代码，失败时无法识别终端漏输入
    prompt_send_attempts = $PromptSendAttempts  # 新增代码+AcceptanceController: 记录 prompt 发送次数；若没有这行代码，用户不知道是否发生重试
    permission_sent_count = $PermissionSentCount  # 新增代码+AcceptanceController: 记录权限响应次数；若没有这行代码，用户不知道是否经历工具授权
    max_permission_sent_count = $MaxPermissionSentCount  # 新增代码+真实浏览器客户模式: 记录场景允许的最大权限响应次数；若没有这行代码，result.json 无法证明无 y 门禁配置
    permission_policy_default_response = $PermissionDefaultResponse  # 新增代码+RealChromeConnect: 记录本场景默认权限策略；若没有这行代码，复盘时不知道未命中规则会怎样处理
    permission_policy_decisions = $PermissionPolicyDecisions  # 新增代码+RealChromeConnect: 记录每次权限响应的 action、y/n 和规则原因；若没有这行代码，真实 Chrome 验收缺少授权审计
    post_success_wait_seconds = $PostSuccessWaitSeconds  # 新增代码+GoogleHumanVisible: 记录成功后可见停留秒数；若没有这行代码，result.json 无法证明本轮是否给用户观察窗口
    assertion = $LastAssertion  # 新增代码+AcceptanceController: 保存断言详情；若没有这行代码，失败时缺少定位信息
    event_count = $FinalEvents.Count  # 新增代码+AcceptanceController: 记录事件总数；若没有这行代码，无法判断 harness 是否持续写入
    states = @($FinalEvents | ForEach-Object { $_.state })  # 新增代码+AcceptanceController: 保存事件状态序列；若没有这行代码，无法复盘控制流程
    event_log = $EventLog  # 新增代码+AcceptanceController: 保存事件日志路径；若没有这行代码，外部 agent 不知道去哪里看 JSONL
    startup_screenshot = $StartupScreenshot  # 新增代码+AcceptanceController: 保存启动截图路径；若没有这行代码，result.json 缺少窗口证据索引
    prompt_screenshot = $PromptScreenshot  # 新增代码+AcceptanceController: 保存 prompt 截图路径；若没有这行代码，result.json 缺少输入证据索引
    final_screenshot = $FinalScreenshot  # 新增代码+AcceptanceController: 保存最终截图路径；若没有这行代码，result.json 缺少最终画面索引
    copied_debug_log = $CopiedDebugLog  # 新增代码+AcceptanceController: 保存归档调试日志路径；若没有这行代码，result.json 缺少文本证据索引
    process_id = $Process.Id  # 新增代码+AcceptanceController: 保存启动进程 ID；若没有这行代码，失败后不易定位残留窗口
    window_title = $WindowTitle  # 新增代码+AcceptanceController: 保存窗口标题；若没有这行代码，用户难以确认操作目标
}  # 新增代码+AcceptanceController: 结束结果对象；若没有这行代码，PowerShell 语法不完整
$Result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ResultJson -Encoding UTF8  # 新增代码+AcceptanceController: 写入统一 result.json；若没有这行代码，本轮验收状态无法落盘
if ($ScenarioPassed -and $PostSuccessWaitSeconds -gt 0) {  # 新增代码+GoogleHumanVisible: 成功后按场景要求保留窗口一段时间；若没有这行代码，用户可能来不及看到 Google 搜索画面
    Start-Sleep -Seconds $PostSuccessWaitSeconds  # 新增代码+GoogleHumanVisible: 暂停指定秒数让真实 Chrome/终端保持可见；若没有这行代码，可见演示缺少肉眼观察窗口
}  # 新增代码+GoogleHumanVisible: 结束成功后停留分支；若没有这行代码，PowerShell 语法不完整
if ((-not $KeepWindowOpen) -and $ScenarioPassed) {  # 新增代码+AcceptanceController: 成功且不要求保留窗口时清理；若没有这行代码，成功后窗口会残留
    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue  # 新增代码+AcceptanceController: 关闭 cmd 子进程；若没有这行代码，命令进程可能残留
    $TerminalWindowForCleanup = Get-Process | Where-Object { $_.MainWindowTitle -like "*$WindowTitle*" } | Select-Object -First 1  # 新增代码+AcceptanceController: 查找 Windows Terminal 外壳窗口；若没有这行代码，只关 cmd 可能仍残留标签页
    if ($TerminalWindowForCleanup) {  # 新增代码+AcceptanceController: 判断是否找到外壳窗口；若没有这行代码，空对象会导致关闭命令不明确
        Stop-Process -Id $TerminalWindowForCleanup.Id -Force -ErrorAction SilentlyContinue  # 新增代码+AcceptanceController: 关闭承载本轮测试的 Windows Terminal；若没有这行代码，成功后桌面可能残留窗口
    }  # 新增代码+AcceptanceController: 结束外壳窗口清理分支；若没有这行代码，PowerShell 语法不完整
}  # 新增代码+AcceptanceController: 结束窗口清理分支；若没有这行代码，PowerShell 语法不完整
Write-Host "ACCEPTANCE_CONTROLLER_COMPLETED=$ScenarioPassed"  # 新增代码+AcceptanceController: 输出机器可读完成状态；若没有这行代码，调用方要打开 JSON 才知道是否通过
Write-Host "RESULT_JSON=$ResultJson"  # 新增代码+AcceptanceController: 输出统一结果文件路径；若没有这行代码，调用方难以定位证据
if (-not $ScenarioPassed) {  # 新增代码+AcceptanceController: 失败时返回非零退出码；若没有这行代码，自动化系统会把失败当成功
    exit 2  # 新增代码+AcceptanceController: 用 2 表示场景验收未通过；若没有这行代码，失败边界不清楚
}  # 新增代码+AcceptanceController: 结束失败退出分支；若没有这行代码，PowerShell 语法不完整
exit 0  # 新增代码+AcceptanceController: 成功时返回 0；若没有这行代码，调用方无法用退出码判断通过
