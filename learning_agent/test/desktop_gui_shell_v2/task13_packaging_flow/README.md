# Desktop GUI Shell V2 Task 13 学习副本

本目录保存 Task 13 “打包和启动体验”涉及的新写和修改代码副本，方便后续逐行学习和对照。

- `code_copies/package.json`：新增 `package:windows` 命令。
- `code_copies/package-windows.ps1`：Windows 开发包装脚本，运行 build，生成 artifact 和 package summary。
- `code_copies/start-backend.ps1`：后端 bridge 启动脚本，打印 bridge URL、renderer 提示、证据目录和端口占用错误。
- `code_copies/start-desktop-dev.ps1`：桌面 dev shell 启动脚本，打印 bridge URL、renderer URL、证据目录和 renderer 端口占用错误。
- `code_copies/desktop_gui_shell_architecture.md`：架构文档新增 Windows Packaging And Startup 边界。
- `code_copies/package_summary.txt`：本轮包装脚本生成的打包摘要证据。

注意：本轮三个 `.ps1` 脚本必须保留 UTF-8 BOM + CRLF。Windows PowerShell 5.1 在无 BOM UTF-8 中文注释下会错误解析脚本。

本轮验证命令：

```powershell
cd apps/desktop
npm run build
cd ..\..
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\package-windows.ps1
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw -Encoding UTF8 '.\apps\desktop\scripts\start-backend.ps1')) | Out-Null; [scriptblock]::Create((Get-Content -Raw -Encoding UTF8 '.\apps\desktop\scripts\start-desktop-dev.ps1')) | Out-Null; 'startup scripts parse OK'"
```
