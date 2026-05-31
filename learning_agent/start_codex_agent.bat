@echo off
set SCRIPT_DIR=%~dp0
set PS_SCRIPT=%SCRIPT_DIR%start_codex_agent.ps1
if not exist "%PS_SCRIPT%" (
    echo Cannot find startup script: %PS_SCRIPT%
    pause
    exit /b 1
)
if /I "%1"=="selftest" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -SelfTest
    exit /b %ERRORLEVEL%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -File "%PS_SCRIPT%"
