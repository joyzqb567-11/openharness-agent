# Desktop GUI Shell V2 Task 14 学习副本

本目录保存 Task 14 “Release gate V2”涉及的新写和修改代码副本，方便后续逐行学习和对照。

- `code_copies/release-gate.ps1`：V2 自动 release gate，运行 Python GUI tests、前端 lint/test/build、visible smoke 指令生成和 Layer C 判定。
- `code_copies/visible-gui-smoke.ps1`：可见 GUI smoke 指令脚本，默认只生成清单，`-Launch` 才启动 GUI。
- `code_copies/gui-prompt-matrix.md`：新增 V2 visible GUI release rows。
- `code_copies/desktop_gui_shell_v2_acceptance.md`：V2 验收分层说明。
- `code_copies/visible_gui_smoke_latest.txt`：本轮 release gate 生成的最新人工 smoke 指令。

注意：`.ps1` 脚本必须保留 UTF-8 BOM + CRLF，避免 Windows PowerShell 5.1 误解析中文注释。

本轮验证命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

本轮 release gate 结果：

```text
Python GUI tests OK.
Frontend lint passed.
Frontend unit tests passed.
Frontend production build passed.
Layer A visible GUI smoke instructions generated.
Layer C trigger decision printed.
```
