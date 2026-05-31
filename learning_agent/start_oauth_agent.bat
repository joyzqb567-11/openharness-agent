@echo off
rem Added code: keep this BAT file ASCII-only so Windows cmd will not misread UTF-8 Chinese comments.
set SCRIPT_DIR=%~dp0
rem Added code: get the directory that contains this BAT file.
set PS_SCRIPT=%SCRIPT_DIR%start_oauth_agent.ps1
rem Added code: build the PowerShell launcher path.
if not exist "%PS_SCRIPT%" (
    rem Added code: show a clear error if the PowerShell launcher is missing.
    echo Cannot find startup script: %PS_SCRIPT%
    rem Added code: pause so the user can read the error after double-clicking.
    pause
    rem Added code: return a non-zero exit code.
    exit /b 1
)
if /I "%1"=="selftest" (
    rem Added code: run tests only when the first argument is selftest.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -SelfTest
    rem Added code: forward the PowerShell exit code.
    exit /b %ERRORLEVEL%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -File "%PS_SCRIPT%"
rem Added code: normal double-click starts the OAuth/API agent and keeps the window open.
