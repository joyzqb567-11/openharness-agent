from pathlib import Path  # 新增代码+DesktopOAuthOneClickLaunchTest：读取仓库中的启动脚本；如果没有这一行，测试无法定位一键启动入口。


REPO_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+DesktopOAuthOneClickLaunchTest：计算仓库根目录；如果没有这一行，测试会依赖当前工作目录。


def _script_text(relative_path: str) -> str:  # 新增代码+DesktopOAuthOneClickLaunchTest：函数段开始，统一读取脚本文本；如果没有这段函数，多个测试会重复路径拼接和编码选择。
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8-sig")  # 新增代码+DesktopOAuthOneClickLaunchTest：用 utf-8-sig 兼容批处理 BOM；如果没有这一行，带 BOM 的脚本可能读出异常字符。
# 新增代码+DesktopOAuthOneClickLaunchTest：函数段结束，_script_text 到此结束；如果没有这个边界说明，用户不容易看出 helper 只负责读文件。


def test_root_batch_delegates_to_oauth_powershell_launcher() -> None:  # 新增代码+DesktopOAuthOneClickLaunchTest：测试段开始，锁定用户双击入口；如果没有这段测试，根目录可能没有真正可手动运行的一键脚本。
    batch_text = _script_text("start_openharness_desktop_oauth.bat")  # 新增代码+DesktopOAuthOneClickLaunchTest：读取根目录 bat；如果没有这一行，测试无法确认用户入口存在。

    assert "start-openharness-desktop-oauth.ps1" in batch_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认 bat 委托到真实 PowerShell 启动器；如果没有这一行，bat 可能只剩空壳。
    assert "-ExecutionPolicy" in batch_text and "Bypass" in batch_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认脚本可在默认 Windows 策略下运行；如果没有这一行，用户双击可能被执行策略挡住。
    assert "pause" in batch_text.lower()  # 新增代码+DesktopOAuthOneClickLaunchTest：确认失败或成功信息会停留给用户看；如果没有这一行，双击窗口会闪退。
# 新增代码+DesktopOAuthOneClickLaunchTest：测试段结束，根目录 bat 合同到此结束；如果没有这个边界说明，用户不容易看出覆盖范围。


def test_oauth_launcher_sets_real_openai_runtime_contract() -> None:  # 新增代码+DesktopOAuthOneClickLaunchTest：测试段开始，锁定真实 OAuth 启动环境；如果没有这段测试，一键脚本可能退回 mock 或 API key 单一路径。
    launcher_text = _script_text("apps/desktop/scripts/start-openharness-desktop-oauth.ps1")  # 新增代码+DesktopOAuthOneClickLaunchTest：读取 PowerShell 启动器；如果没有这一行，测试无法检查真实链路变量。

    assert "OPENHARNESS_OPENAI_AUTH_MODE" in launcher_text and "real_browser" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认启动真实浏览器 OAuth；如果没有这一行，OpenAI 链接可能仍是 mock。
    assert "OPENHARNESS_OPENAI_RUNTIME" in launcher_text and "direct_sse" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认消息窗口走 Direct SSE；如果没有这一行，模型调用可能退回慢路径或假回复。
    assert "OPENHARNESS_PROVIDER_SECRET_STORE" in launcher_text and "os_encrypted" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认真实 token 使用系统加密存储；如果没有这一行，refresh token 可能落到开发 JSON。
    assert "OPENHARNESS_OPENAI_EXPERIMENTAL" in launcher_text and "\"1\"" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认真实 OAuth 需要显式实验开关；如果没有这一行，安全门禁不会被满足。
    assert "OPENHARNESS_OPENAI_CLIENT_ID" in launcher_text and "app_EMoamEEZ73f0CkXaXp7hrann" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认沿用当前已验证的 OpenCode 参考 client；如果没有这一行，授权官网可能打不开。
    assert "OPENHARNESS_OPENAI_CALLBACK_PORT" in launcher_text and "1455" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认回调端口和当前成功链路一致；如果没有这一行，浏览器认证后可能回不到 GUI。
# 新增代码+DesktopOAuthOneClickLaunchTest：测试段结束，真实 OAuth 环境合同到此结束；如果没有这个边界说明，用户不容易看出覆盖范围。


def test_oauth_launcher_reuses_existing_backend_and_desktop_scripts_with_verification() -> None:  # 新增代码+DesktopOAuthOneClickLaunchTest：测试段开始，锁定一键脚本复用当前链路并做启动后检查；如果没有这段测试，新脚本可能绕过成熟脚本。
    launcher_text = _script_text("apps/desktop/scripts/start-openharness-desktop-oauth.ps1")  # 新增代码+DesktopOAuthOneClickLaunchTest：读取 PowerShell 启动器；如果没有这一行，测试无法检查启动命令。

    assert "start-backend.ps1" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认复用现有 GUI bridge 启动脚本；如果没有这一行，后端链路会分叉。
    assert "start-desktop-dev.ps1" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认复用现有 renderer/Electron 启动脚本；如果没有这一行，前端链路会分叉。
    assert "/v2/gui/provider-settings/providers" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认启动后读取 provider catalog；如果没有这一行，脚本无法发现提供商加载失败。
    assert "auth.openai.com" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认验收真实授权域名；如果没有这一行，脚本可能只验证 bridge 活着。
    assert "chatgpt-browser" in launcher_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认验收浏览器登录方式；如果没有这一行，OAuth 入口可能仍然丢失。
# 新增代码+DesktopOAuthOneClickLaunchTest：测试段结束，复用链路和启动验证合同到此结束；如果没有这个边界说明，用户不容易看出覆盖范围。


def test_existing_dev_scripts_allow_temp_launch_log_override() -> None:  # 新增代码+DesktopOAuthOneClickLaunchTest：测试段开始，锁定日志目录覆盖口；如果没有这段测试，一键脚本会持续污染仓库运行日志。
    backend_text = _script_text("apps/desktop/scripts/start-backend.ps1")  # 新增代码+DesktopOAuthOneClickLaunchTest：读取后端启动脚本；如果没有这一行，测试无法检查 bridge 日志覆盖。
    desktop_text = _script_text("apps/desktop/scripts/start-desktop-dev.ps1")  # 新增代码+DesktopOAuthOneClickLaunchTest：读取桌面启动脚本；如果没有这一行，测试无法检查 renderer 日志覆盖。

    assert "OPENHARNESS_DESKTOP_LAUNCH_LOG_DIR" in backend_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认后端日志目录可由一键脚本覆盖；如果没有这一行，启动 bridge 会制造未跟踪仓库文件。
    assert "OPENHARNESS_DESKTOP_LAUNCH_LOG_DIR" in desktop_text  # 新增代码+DesktopOAuthOneClickLaunchTest：确认桌面日志目录可由一键脚本覆盖；如果没有这一行，启动 Electron 会制造未跟踪仓库文件。
# 新增代码+DesktopOAuthOneClickLaunchTest：测试段结束，日志覆盖合同到此结束；如果没有这个边界说明，用户不容易看出覆盖范围。
