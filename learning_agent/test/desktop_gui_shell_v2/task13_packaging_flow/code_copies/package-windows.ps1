param() # 新增代码+DesktopPackaging：保留空参数块作为未来扩展入口；如果没有这行，后续新增版本号或输出目录参数时需要重写脚本形状。

$ErrorActionPreference = "Stop" # 新增代码+DesktopPackaging：让任何构建或文件错误立即失败；如果没有这行，包装失败可能继续写出假 summary。
$ScriptPath = if ($PSCommandPath) { $PSCommandPath } else { $MyInvocation.MyCommand.Path } # 修改代码+DesktopPackaging：用当前脚本路径兼容不同 PowerShell 宿主；如果没有这行，某些宿主下 `$PSScriptRoot` 为空会导致启动失败。
$ScriptDir = Split-Path -Parent $ScriptPath # 修改代码+DesktopPackaging：定位 scripts 目录；如果没有这行，后续无法稳定推导 apps/desktop。
$DesktopRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path # 修改代码+DesktopPackaging：定位 apps/desktop 目录；如果没有这行，从仓库根运行脚本时找不到 package.json。
$Workspace = (Resolve-Path (Join-Path $DesktopRoot "..\..")).Path # 新增代码+DesktopPackaging：定位仓库根目录；如果没有这行，summary 无法写到 learning_agent/test。
$PackageRoot = Join-Path $DesktopRoot "dist\package-windows" # 新增代码+DesktopPackaging：定义 Windows 包装输出父目录；如果没有这行，artifact 位置不稳定。
$ArtifactDir = Join-Path $PackageRoot "openharness-desktop-windows-dev" # 新增代码+DesktopPackaging：定义本次清晰 artifact 目录；如果没有这行，用户不知道打包产物在哪。
$SummaryDir = Join-Path $Workspace "learning_agent\test\desktop_gui_shell_v2" # 新增代码+DesktopPackaging：定义测试证据目录；如果没有这行，package summary 无法被后续验收找到。
$SummaryPath = Join-Path $SummaryDir "package_summary.txt" # 新增代码+DesktopPackaging：定义打包摘要文件；如果没有这行，脚本无法留下可读证据。
$ResolvedDesktop = [System.IO.Path]::GetFullPath($DesktopRoot) # 新增代码+DesktopPackaging：解析桌面目录绝对路径；如果没有这行，删除安全检查只能比较相对路径。
$ResolvedArtifact = [System.IO.Path]::GetFullPath($ArtifactDir) # 新增代码+DesktopPackaging：解析 artifact 绝对路径；如果没有这行，无法确认清理目标在项目内。
$DesktopPrefix = $ResolvedDesktop.TrimEnd("\") + "\" # 新增代码+DesktopPackaging：生成目录前缀用于安全比较；如果没有这行，`apps/desktop-other` 这类相似路径可能误通过。
if (-not $ResolvedArtifact.StartsWith($DesktopPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { # 新增代码+DesktopPackaging：确认 artifact 位于 apps/desktop 内；如果没有这行，递归删除可能误伤项目外目录。
  throw "Refusing to package outside desktop root: $ResolvedArtifact" # 新增代码+DesktopPackaging：安全检查失败时停止；如果没有这行，错误路径会继续执行文件操作。
} # 新增代码+DesktopPackaging：artifact 安全检查结束；如果没有这行，PowerShell 条件块语法不完整。

Set-Location $DesktopRoot # 新增代码+DesktopPackaging：切换到桌面应用目录；如果没有这行，npm 命令会在错误目录执行。
$env:ELECTRON_MIRROR = if ($env:ELECTRON_MIRROR) { $env:ELECTRON_MIRROR } else { "https://npmmirror.com/mirrors/electron/" } # 新增代码+DesktopPackaging：给 Electron 下载设置镜像兜底；如果没有这行，新机器可能拉不到 electron.exe。
if (-not (Test-Path -LiteralPath (Join-Path $DesktopRoot "node_modules"))) { # 新增代码+DesktopPackaging：检查依赖是否存在；如果没有这行，缺依赖时 build 会报不清楚的模块错误。
  npm ci # 新增代码+DesktopPackaging：按 lockfile 安装依赖；如果没有这行，新环境无法完成生产构建。
} # 新增代码+DesktopPackaging：依赖安装判断结束；如果没有这行，PowerShell 条件块语法不完整。

npm run build # 新增代码+DesktopPackaging：执行 Electron main 和 Vite renderer 生产构建；如果没有这行，artifact 可能包含旧构建产物。
if (Test-Path -LiteralPath $ArtifactDir) { # 新增代码+DesktopPackaging：检查旧 artifact 是否存在；如果没有这行，清理命令可能对不存在目录报错。
  Remove-Item -LiteralPath $ArtifactDir -Recurse -Force # 新增代码+DesktopPackaging：清理旧 artifact；如果没有这行，新旧文件可能混在一起导致验收误判。
} # 新增代码+DesktopPackaging：旧 artifact 清理判断结束；如果没有这行，PowerShell 条件块语法不完整。
New-Item -ItemType Directory -Force -Path (Join-Path $ArtifactDir "dist") | Out-Null # 新增代码+DesktopPackaging：创建 artifact 的 dist 目录；如果没有这行，后续复制 main/renderer 会失败。
Copy-Item -LiteralPath (Join-Path $DesktopRoot "dist\main") -Destination (Join-Path $ArtifactDir "dist\main") -Recurse -Force # 新增代码+DesktopPackaging：复制 Electron main 构建产物；如果没有这行，artifact 无法启动主进程。
Copy-Item -LiteralPath (Join-Path $DesktopRoot "dist\renderer") -Destination (Join-Path $ArtifactDir "dist\renderer") -Recurse -Force # 新增代码+DesktopPackaging：复制 Vite renderer 构建产物；如果没有这行，artifact 没有可见 GUI 页面。
Copy-Item -LiteralPath (Join-Path $DesktopRoot "package.json") -Destination (Join-Path $ArtifactDir "package.json") -Force # 新增代码+DesktopPackaging：复制 package manifest；如果没有这行，artifact 缺少应用入口声明。
Copy-Item -LiteralPath (Join-Path $DesktopRoot "package-lock.json") -Destination (Join-Path $ArtifactDir "package-lock.json") -Force # 新增代码+DesktopPackaging：复制 lockfile；如果没有这行，用户无法按同一依赖版本复现包装产物。

$GitCommit = "unknown" # 新增代码+DesktopPackaging：准备默认 commit 文本；如果没有这行，非 git 环境下 summary 会缺字段。
try { # 新增代码+DesktopPackaging：尝试读取当前 git commit；如果没有这行，git 不可用时会打断包装。
  $GitCommit = (git -C $Workspace rev-parse --short HEAD).Trim() # 新增代码+DesktopPackaging：记录短 commit；如果没有这行，summary 无法追踪产物来源。
} catch { # 新增代码+DesktopPackaging：处理 git 不可用；如果没有这行，非 git 目录会失败。
  $GitCommit = "unknown" # 新增代码+DesktopPackaging：保持安全兜底值；如果没有这行，summary 字段会为空。
} # 新增代码+DesktopPackaging：git commit 读取结束；如果没有这行，PowerShell try/catch 语法不完整。

# 新增代码+DesktopPackaging：下面的哈希表创建 artifact manifest 数据；如果没有这段，产物缺少机器可读说明。
$Manifest = [ordered]@{
  name = "OpenHarness Desktop GUI Shell" # 新增代码+DesktopPackaging：记录产物名称；如果没有这行，manifest 不知道自己描述哪个应用。
  kind = "windows-dev-artifact" # 新增代码+DesktopPackaging：声明这是 Windows 开发包装产物；如果没有这行，用户可能误以为是正式安装器。
  created_at = [DateTimeOffset]::Now.ToString("o") # 新增代码+DesktopPackaging：记录创建时间；如果没有这行，验收无法判断产物新旧。
  git_commit = $GitCommit # 新增代码+DesktopPackaging：记录代码版本；如果没有这行，产物无法追溯到提交。
  artifact_dir = $ResolvedArtifact # 新增代码+DesktopPackaging：记录产物目录；如果没有这行，用户需要猜输出位置。
  launch_note = "Run from apps/desktop with npm run start after backend bridge is running." # 新增代码+DesktopPackaging：记录启动边界；如果没有这行，用户可能把 artifact 当作独立安装包。
} # 新增代码+DesktopPackaging：artifact manifest 数据结束；如果没有这行，PowerShell 哈希表语法不完整。
$Manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ArtifactDir "package-manifest.json") # 新增代码+DesktopPackaging：写入机器可读 manifest；如果没有这行，artifact 缺少可审计元数据。
New-Item -ItemType Directory -Force -Path $SummaryDir | Out-Null # 新增代码+DesktopPackaging：确保 summary 目录存在；如果没有这行，写 evidence 文件会失败。
# 新增代码+DesktopPackaging：下面的数组准备可读 summary 内容；如果没有这段，用户只能读 JSON manifest。
$SummaryLines = @(
  "Desktop package artifact created." # 新增代码+DesktopPackaging：写入成功标记；如果没有这行，release gate 无法扫到明确结果。
  "Artifact: $ResolvedArtifact" # 新增代码+DesktopPackaging：写入 artifact 目录；如果没有这行，用户不知道产物位置。
  "Commit: $GitCommit" # 新增代码+DesktopPackaging：写入 commit；如果没有这行，产物缺少版本来源。
  "Build: npm run build passed" # 新增代码+DesktopPackaging：写入构建结果；如果没有这行，summary 无法证明 build 已执行。
  "Type: Windows development artifact, not a signed installer" # 新增代码+DesktopPackaging：写入包装类型边界；如果没有这行，成熟度边界会被误读。
) # 新增代码+DesktopPackaging：summary 内容数组结束；如果没有这行，PowerShell 数组语法不完整。
$SummaryLines | Set-Content -Encoding UTF8 -LiteralPath $SummaryPath # 新增代码+DesktopPackaging：写入学习验收 summary；如果没有这行，蓝图要求的证据文件不会生成。
Write-Host "Desktop package artifact created." # 新增代码+DesktopPackaging：在终端输出成功标记；如果没有这行，用户不容易确认包装完成。
Write-Host "Artifact: $ResolvedArtifact" # 新增代码+DesktopPackaging：输出 artifact 目录；如果没有这行，用户需要手动查找产物。
Write-Host "Summary: $SummaryPath" # 新增代码+DesktopPackaging：输出 summary 路径；如果没有这行，验收证据位置不清楚。
