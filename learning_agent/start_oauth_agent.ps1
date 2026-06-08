param(  # 新增代码: 定义脚本参数区域，方便支持自检模式
    [switch]$SelfTest  # 新增代码: 如果传入 -SelfTest，就只运行单元测试，不启动真实 OAuth 模型
)  # 新增代码: 参数定义结束

$ErrorActionPreference = "Stop"  # 新增代码: 任何命令出错都立即停止，避免错误被静默吞掉

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # 新增代码: 获取当前脚本所在目录，也就是 learning_agent 文件夹
$RepoRoot = Split-Path -Parent $ScriptDir  # 新增代码: 获取项目根目录，也就是 OpenHarness-main
$Launcher = Join-Path $ScriptDir "learning_agent.py"  # 新增代码: 定义 agent 的 Python 入口文件
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"  # 新增代码: 定义 Codex 自带 Python 的常见路径

function Resolve-Python {  # 新增代码: 定义寻找 Python 的函数，避免用户手动配置 Python 路径
    if (Test-Path -LiteralPath $BundledPython) {  # 新增代码: 优先检查 Codex 自带 Python 是否存在
        return $BundledPython  # 新增代码: 找到后返回 Codex 自带 Python
    }  # 新增代码: Codex 自带 Python 检查结束

    $python = Get-Command python -ErrorAction SilentlyContinue  # 新增代码: 尝试从 PATH 中寻找 python 命令
    if ($python) {  # 新增代码: 如果找到了 python
        return $python.Source  # 新增代码: 返回 python 可执行文件路径
    }  # 新增代码: python 检查结束

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue  # 新增代码: 尝试从 PATH 中寻找 python3 命令
    if ($python3) {  # 新增代码: 如果找到了 python3
        return $python3.Source  # 新增代码: 返回 python3 可执行文件路径
    }  # 新增代码: python3 检查结束

    throw "找不到 Python。请安装 Python，或确认 Codex 自带 Python 存在：$BundledPython"  # 新增代码: 三种方式都找不到时，给出清晰错误
}  # 新增代码: Resolve-Python 函数结束

$Python = Resolve-Python  # 新增代码: 解析最终要使用的 Python 可执行文件
$env:PYTHONPATH = "$RepoRoot;$env:PYTHONPATH"  # 新增代码: 把项目根目录加入 Python 导入路径，确保 learning_agent 包可被导入
$env:LEARNING_AGENT_MODEL_PROVIDER = "codex-oauth"  # 新增代码: 告诉 learning_agent 使用 OAuth/API 直连模式，而不是 OPENAI_API_KEY 或 codex exec 模式
if (-not $env:CODEX_MODEL) {  # 新增代码: 如果用户没有显式指定 Codex 模型
    $env:CODEX_MODEL = "gpt-5.5"  # 新增代码: 默认使用 GPT-5.5，匹配你的学习目标
}  # 新增代码: 默认模型设置结束
if (-not $env:CODEX_OAUTH_TIMEOUT_SECONDS) {  # 新增代码: 如果用户没有显式指定网页登录等待时间
    $env:CODEX_OAUTH_TIMEOUT_SECONDS = "300"  # 新增代码: 默认等待 5 分钟，给网页登录留足时间
}  # 新增代码: 默认 OAuth 超时设置结束

Set-Location -LiteralPath $RepoRoot  # 新增代码: 切换到项目根目录，让 Python 在正确上下文里运行

if ($SelfTest) {  # 新增代码: 如果用户选择自检模式
    & $Python -m unittest discover learning_agent  # 修改代码+Stage14硬清理: 启动前运行模块化测试发现入口；若没有这行代码，脚本会继续指向已删除的旧单文件测试入口
    exit $LASTEXITCODE  # 新增代码: 把测试退出码返回给调用方，方便 bat 或终端判断是否成功
}  # 新增代码: 自检模式结束

if (-not $env:LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS) {  # 新增代码+危险调试权限: 普通启动默认进入本地危险调试放行模式；若没有这行代码，真实浏览器调试仍会被 y/N 权限确认打断
    $env:LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS = "1"  # 新增代码+危险调试权限: 设置类似 ClaudeCode dangerously-skip-permissions 的开关；若没有这行代码，Python 权限层无法知道要自动允许
}  # 新增代码+危险调试权限: 结束默认危险模式设置，并允许用户提前设置 0/false/off 来覆盖；若没有这行代码，PowerShell 语法不完整
if (-not $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE) {  # 新增代码+真实ComputerUse入口: 普通 OAuth 可见终端默认启用真实 Windows 鼠标键盘动作；若没有这行代码，/computer use --full 只会开启模式但真实动作后端仍关闭
    $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE = "1"  # 新增代码+真实ComputerUse入口: 设置真实动作开关；若没有这行代码，模型调用 click/drag/type/launch 后会被 Windows 后端拒绝
}  # 新增代码+真实ComputerUse入口: 结束真实动作默认设置，并允许用户提前设置 0/false/off 覆盖；若没有这行代码，PowerShell 语法不完整
if (-not $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE) {  # 新增代码+真实ComputerUse入口: 普通 OAuth 可见终端默认启用 Windows 窗口枚举观察；若没有这行代码，模型启动应用后无法获取可信窗口目录
    $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE = "1"  # 新增代码+真实ComputerUse入口: 设置只读观察开关；若没有这行代码，computer_observe/list_windows 会继续返回后端未启用
}  # 新增代码+真实ComputerUse入口: 结束只读观察默认设置，并允许用户提前覆盖；若没有这行代码，PowerShell 语法不完整
if (-not $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE) {  # 新增代码+真实ComputerUse入口: 普通 OAuth 可见终端默认启用 native 截图/文本观察；若没有这行代码，模型无法收到真实屏幕截图回灌
    $env:LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE = "1"  # 新增代码+真实ComputerUse入口: 设置 native 观察开关；若没有这行代码，Computer Use Image Results 不会稳定产生 image/png 截图
}  # 新增代码+真实ComputerUse入口: 结束 native 观察默认设置，并允许用户提前覆盖；若没有这行代码，PowerShell 语法不完整
if (-not $env:LEARNING_AGENT_PHASE105_ENABLE_FULL_MODE_CONTROLLED_REAL_LAUNCH) {  # 新增代码+真实ComputerUse入口: 普通 OAuth 可见终端默认启用 launch_app 真实启动门；若没有这行代码，/computer use --full 会生成占位窗口而不真正打开本机软件
    $env:LEARNING_AGENT_PHASE105_ENABLE_FULL_MODE_CONTROLLED_REAL_LAUNCH = "1"  # 新增代码+真实ComputerUse入口: 设置 Phase105 受控真实启动开关；若没有这行代码，controller 的 UniversalTargetSessionRuntime 会停留在 recording 模式
}  # 新增代码+真实ComputerUse入口: 结束真实启动门默认设置，并允许用户提前覆盖；若没有这行代码，PowerShell 语法不完整

Write-Host "Learning Agent OAuth/API 模式已启动。"  # 新增代码: 打印启动提示，让用户知道这是 OAuth 直连入口
Write-Host "说明：此模式参考 opencode2，通过 OpenAI 网页 OAuth 登录，不需要 OPENAI_API_KEY，也不再调用 codex exec。"  # 新增代码: 说明认证方式和区别
Write-Host "首次运行会自动打开浏览器登录；后续会复用本机 token，并在过期时自动刷新。"  # 新增代码: 说明 token 复用和刷新行为
Write-Host "危险调试权限：默认已开启 LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1，会自动允许权限请求。"  # 新增代码+危险调试权限: 启动时清楚提示当前处于全放开调试模式；若没有这行代码，用户可能不知道权限已被跳过
Write-Host "真实 Computer Use：默认已开启 Windows 真实动作、窗口观察、native 截图观察和 launch_app 真实启动。"  # 修改代码+真实ComputerUse入口: 启动时明确提示真实应用启动也已放开；若没有这行代码，用户会误以为 launch_app 已真实接通但实际可能仍是占位 session
Write-Host "输入 exit 或 quit 退出。"  # 新增代码: 告诉用户退出方式

& $Python $Launcher  # 新增代码: 启动 learning_agent.py，进入交互式 OAuth/API agent
