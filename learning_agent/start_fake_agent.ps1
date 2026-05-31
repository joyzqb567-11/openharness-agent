param(
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Launcher = Join-Path $ScriptDir "fake_model_repl.py"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

function Resolve-Python {
    if (Test-Path -LiteralPath $BundledPython) {
        return $BundledPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return $python3.Source
    }

    throw "找不到 Python。请安装 Python，或确认 Codex 自带 Python 存在：$BundledPython"
}

$Python = Resolve-Python
$env:PYTHONPATH = "$RepoRoot;$env:PYTHONPATH"
Set-Location -LiteralPath $RepoRoot

if ($SelfTest) {
    & $Python $Launcher --self-test
    exit $LASTEXITCODE
}

& $Python $Launcher
