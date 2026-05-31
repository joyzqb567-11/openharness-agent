param(  # 新增代码: 定义脚本参数区域，方便支持自检模式
    [switch]$SelfTest  # 新增代码: 如果传入 -SelfTest，就只运行单元测试，不启动真实 GPT-5.5
)  # 新增代码: 参数定义结束

$ErrorActionPreference = "Stop"  # 新增代码: 任何命令出错都立即停止，避免错误被静默吞掉

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # 新增代码: 获取当前脚本所在目录，也就是 learning_agent 文件夹
$RepoRoot = Split-Path -Parent $ScriptDir  # 新增代码: 获取项目根目录，也就是 OpenHarness-main
$Launcher = Join-Path $ScriptDir "learning_agent.py"  # 新增代码: 定义真实模型版 agent 的 Python 入口文件
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"  # 新增代码: 定义 Codex 自带 Python 的常见路径
$CodexBinDir = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"  # 新增代码: 定义用户级 Codex CLI 目录，避开 WindowsApps 权限问题

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

if (Test-Path -LiteralPath $CodexBinDir) {  # 新增代码: 如果用户级 Codex CLI 目录存在
    $env:Path = "$CodexBinDir;$env:Path"  # 新增代码: 把它临时放到 PATH 最前面，避免误用 WindowsApps 里的 codex.exe
}  # 新增代码: Codex PATH 修正结束

$Codex = Get-Command codex -ErrorAction SilentlyContinue  # 新增代码: 检查当前终端是否能找到 codex 命令
if (-not $Codex) {  # 新增代码: 如果找不到 codex
    throw "找不到 codex 命令。请确认 Codex Desktop/CLI 已安装，或设置 CODEX_CLI_COMMAND 指向 codex.exe。"  # 新增代码: 给出修复提示
}  # 新增代码: codex 检查结束

$Python = Resolve-Python  # 新增代码: 解析最终要使用的 Python 可执行文件
$env:PYTHONPATH = "$RepoRoot;$env:PYTHONPATH"  # 新增代码: 把项目根目录加入 Python 导入路径，确保 learning_agent 包可被导入
$env:LEARNING_AGENT_MODEL_PROVIDER = "codex"  # 新增代码: 告诉 learning_agent 使用 Codex CLI 桥接模式，而不是 OPENAI_API_KEY 模式
if (-not $env:CODEX_MODEL) {  # 新增代码: 如果用户没有显式指定 Codex 模型
    $env:CODEX_MODEL = "gpt-5.5"  # 新增代码: 默认使用 GPT-5.5，匹配你的 Codex Pro/Coding plan 目标
}  # 新增代码: 默认模型设置结束
if (-not $env:CODEX_TIMEOUT_SECONDS) {  # 新增代码: 如果用户没有显式指定超时时间
    $env:CODEX_TIMEOUT_SECONDS = "600"  # 新增代码: 默认等待 10 分钟，避免 GPT-5.5 深度思考时过早超时
}  # 新增代码: 默认超时设置结束

Set-Location -LiteralPath $RepoRoot  # 新增代码: 切换到项目根目录，让 Python 和 Codex 都在正确上下文里运行

if ($SelfTest) {  # 新增代码: 如果用户选择自检模式
    & $Python -m unittest discover learning_agent  # 修改代码+Stage14硬清理: 使用模块化测试发现入口；若没有这行代码，selftest 会继续调用已经删除的旧单文件测试入口
    exit $LASTEXITCODE  # 新增代码: 把测试退出码返回给调用方，方便 bat 或终端判断是否成功
}  # 新增代码: 自检模式结束

Write-Host "Learning Agent Codex/GPT-5.5 模式已启动。"  # 新增代码: 打印启动提示，让用户知道这是 Codex 真实模型入口
Write-Host "说明：此模式通过本机 codex exec 使用你的 Codex 登录态，不需要 OPENAI_API_KEY。"  # 新增代码: 说明认证方式，避免和 API key 模式混淆
Write-Host "输入 exit 或 quit 退出。"  # 新增代码: 告诉用户退出方式

& $Python $Launcher  # 新增代码: 启动 learning_agent.py，进入交互式真实模型 agent
