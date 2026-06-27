@echo off
chcp 65001 >nul
REM 修改代码+DesktopOAuthBatCodepageFix：先把 cmd 切到 UTF-8 再读取中文注释；如果没有这一行，双击 bat 时中文 REM 可能被默认代码页误解析成命令。
REM 新增代码+DesktopOAuthOneClickLaunch：关闭命令回显，让用户看到的启动信息更清楚；如果没有这一行，批处理每条命令都会刷屏。
setlocal
REM 新增代码+DesktopOAuthOneClickLaunch：开启局部环境，避免临时变量污染用户终端；如果没有这一行，OPENHARNESS_ROOT 可能泄漏到后续命令。
set "OPENHARNESS_ROOT=%~dp0"
REM 新增代码+DesktopOAuthOneClickLaunch：调用真正的一键启动 PowerShell 脚本；如果没有这一行，双击入口不会启动 OpenHarness Desktop。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OPENHARNESS_ROOT%apps\desktop\scripts\start-openharness-desktop-oauth.ps1"
REM 新增代码+DesktopOAuthOneClickLaunch：根据 PowerShell 退出码提示成功或失败；如果没有这一段，用户双击后不知道启动是否出错。
if errorlevel 1 (
  echo OpenHarness Desktop OAuth GUI 启动失败，请查看上方错误和临时日志路径。
) else (
  echo OpenHarness Desktop OAuth GUI 已启动。
)
REM 新增代码+DesktopOAuthOneClickLaunch：暂停窗口等待用户查看信息；如果没有这一行，双击运行后的窗口会立即关闭。
pause
REM 新增代码+DesktopOAuthOneClickLaunch：释放局部环境；如果没有这一行，脚本结束边界不清楚。
endlocal
