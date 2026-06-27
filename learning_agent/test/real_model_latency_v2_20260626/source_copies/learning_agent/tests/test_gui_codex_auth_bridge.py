import subprocess  # 新增代码+CodexLoginBridgeTest：导入超时异常类型；如果没有这行，测试无法模拟 Codex CLI status 超时。
import unittest  # 新增代码+CodexLoginBridgeTest：使用项目现有 unittest 风格；如果没有这行，标准测试发现器不会运行本文件。


class CodexAuthBridgeTests(unittest.TestCase):  # 新增代码+CodexLoginBridgeTest：测试类段开始，锁定 Codex CLI 登录桥合同；如果没有这个类，官方登录桥可能误读 token 或误判登录态。
    def test_login_status_connected_when_codex_status_exits_zero(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证 codex login status 退出码 0 时显示已连接；如果没有这段，GUI 可能无法识别已登录用户。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge, CodexAuthStatus  # 新增代码+CodexLoginBridgeTest：导入待实现桥和状态对象；如果没有这行，测试没有被测目标。

        calls: list[list[str]] = []  # 新增代码+CodexLoginBridgeTest：记录 runner 收到的命令；如果没有这行，无法确认代码只调用官方 status 命令。
        def runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟 Codex CLI 成功状态；如果没有这段，测试会依赖本机真实 Codex 登录。
            calls.append(command)  # 新增代码+CodexLoginBridgeTest：保存调用命令；如果没有这行，测试无法断言没有读取 token 文件。
            return 0, "Logged in with ChatGPT", ""  # 新增代码+CodexLoginBridgeTest：返回成功状态和安全文本；如果没有这行，桥无法产生 connected 状态。
        # 新增代码+CodexLoginBridgeTest：函数段结束，runner 到此结束；如果没有边界说明，初学者不易看出这是测试替身。
        bridge = CodexAuthBridge(command="codex", runner=runner)  # 新增代码+CodexLoginBridgeTest：构造注入 runner 的登录桥；如果没有这行，测试会启动真实命令。
        status = bridge.login_status()  # 新增代码+CodexLoginBridgeTest：读取登录状态；如果没有这行，后续没有断言对象。
        self.assertEqual(CodexAuthStatus(available=True, connected=True, message="Logged in with ChatGPT"), status)  # 新增代码+CodexLoginBridgeTest：确认成功状态结构稳定；如果没有这行，catalog 可能显示错误状态。
        self.assertEqual([["codex", "login", "status"]], calls)  # 新增代码+CodexLoginBridgeTest：确认只调用官方 status 命令；如果没有这行，未来代码可能偷偷读取 token。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_login_status_connected_when_codex_status_exits_zero 到此结束；如果没有边界说明，用户不易看出成功态覆盖范围。

    def test_login_status_not_connected_when_codex_status_exits_nonzero(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证未登录时返回可用但未连接；如果没有这段，GUI 会把未登录误判为 CLI 缺失。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginBridgeTest：导入待实现桥；如果没有这行，测试没有被测目标。

        def runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟 Codex CLI 未登录；如果没有这段，测试需要真实退出码。
            return 1, "", "not logged in"  # 新增代码+CodexLoginBridgeTest：返回非零退出码和错误文本；如果没有这行，桥无法区分未登录。
        # 新增代码+CodexLoginBridgeTest：函数段结束，runner 到此结束；如果没有边界说明，初学者不易看出这是未登录替身。
        bridge = CodexAuthBridge(command="codex", runner=runner)  # 新增代码+CodexLoginBridgeTest：构造注入 runner 的登录桥；如果没有这行，测试会调用真实 CLI。
        status = bridge.login_status()  # 新增代码+CodexLoginBridgeTest：读取登录状态；如果没有这行，无法断言未连接语义。
        self.assertIs(status.available, True)  # 新增代码+CodexLoginBridgeTest：确认 CLI 本身可用；如果没有这行，前端无法给出登录按钮。
        self.assertIs(status.connected, False)  # 新增代码+CodexLoginBridgeTest：确认用户尚未登录；如果没有这行，provider 可能假显示 connected。
        self.assertEqual("not logged in", status.message)  # 新增代码+CodexLoginBridgeTest：确认保留安全错误信息；如果没有这行，用户不知道下一步该登录。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_login_status_not_connected_when_codex_status_exits_nonzero 到此结束；如果没有边界说明，用户不易看出未登录覆盖范围。

    def test_login_status_unavailable_when_codex_missing(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证本机没有 Codex CLI 时返回不可用；如果没有这段，设置页可能显示无效连接入口。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginBridgeTest：导入待实现桥；如果没有这行，测试没有被测目标。

        def runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟命令不存在；如果没有这段，测试无法稳定覆盖 FileNotFoundError。
            raise FileNotFoundError("codex")  # 新增代码+CodexLoginBridgeTest：抛出命令不存在；如果没有这行，桥不会进入 unavailable 分支。
        # 新增代码+CodexLoginBridgeTest：函数段结束，runner 到此结束；如果没有边界说明，初学者不易看出这是缺 CLI 替身。
        bridge = CodexAuthBridge(command="codex", runner=runner)  # 新增代码+CodexLoginBridgeTest：构造注入 runner 的登录桥；如果没有这行，测试会依赖本机 PATH。
        status = bridge.login_status()  # 新增代码+CodexLoginBridgeTest：读取登录状态；如果没有这行，无法断言不可用语义。
        self.assertIs(status.available, False)  # 新增代码+CodexLoginBridgeTest：确认 CLI 不可用；如果没有这行，前端无法提示安装 Codex。
        self.assertIs(status.connected, False)  # 新增代码+CodexLoginBridgeTest：确认不可用时不能 connected；如果没有这行，provider 可能假连接。
        self.assertEqual("codex_cli_not_found", status.message)  # 新增代码+CodexLoginBridgeTest：确认稳定错误码；如果没有这行，前端和日志无法识别根因。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_login_status_unavailable_when_codex_missing 到此结束；如果没有边界说明，用户不易看出缺 CLI 覆盖范围。

    def test_login_status_timeout_reports_safe_message(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证 status 命令超时会安全失败；如果没有这段，GUI 可能一直卡在加载中。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginBridgeTest：导入待实现桥；如果没有这行，测试没有被测目标。

        def runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟 Codex CLI status 卡住；如果没有这段，超时路径无法稳定测试。
            raise subprocess.TimeoutExpired(command, timeout_seconds)  # 新增代码+CodexLoginBridgeTest：抛出标准超时异常；如果没有这行，桥不会进入 timeout 分支。
        # 新增代码+CodexLoginBridgeTest：函数段结束，runner 到此结束；如果没有边界说明，初学者不易看出这是超时替身。
        bridge = CodexAuthBridge(command="codex", runner=runner)  # 新增代码+CodexLoginBridgeTest：构造注入 runner 的登录桥；如果没有这行，测试会真实等待。
        status = bridge.login_status()  # 新增代码+CodexLoginBridgeTest：读取登录状态；如果没有这行，无法断言超时语义。
        self.assertIs(status.available, True)  # 新增代码+CodexLoginBridgeTest：确认超时不等于命令缺失；如果没有这行，UI 会给错安装提示。
        self.assertIs(status.connected, False)  # 新增代码+CodexLoginBridgeTest：确认超时时不能假连接；如果没有这行，真实模型可能误启动。
        self.assertEqual("codex_login_status_timeout", status.message)  # 新增代码+CodexLoginBridgeTest：确认稳定超时消息；如果没有这行，用户看不到可排查原因。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_login_status_timeout_reports_safe_message 到此结束；如果没有边界说明，用户不易看出超时覆盖范围。

    def test_start_login_runs_codex_login_without_token_access(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证启动登录只调用 codex login；如果没有这段，代码可能绕过官方登录直接碰 token。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginBridgeTest：导入待实现桥；如果没有这行，测试没有被测目标。

        calls: list[list[str]] = []  # 新增代码+CodexLoginBridgeTest：记录 starter 收到的命令；如果没有这行，无法确认登录命令形状。
        def starter(command: list[str]) -> object:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟启动登录进程；如果没有这段，测试会真的打开浏览器。
            calls.append(command)  # 新增代码+CodexLoginBridgeTest：保存启动命令；如果没有这行，测试无法断言官方命令。
            return "process-started"  # 新增代码+CodexLoginBridgeTest：返回假进程对象；如果没有这行，桥的 start_login 没有启动结果。
        # 新增代码+CodexLoginBridgeTest：函数段结束，starter 到此结束；如果没有边界说明，初学者不易看出这是启动替身。
        bridge = CodexAuthBridge(command="codex", starter=starter)  # 新增代码+CodexLoginBridgeTest：构造注入 starter 的登录桥；如果没有这行，测试会启动真实登录。
        result = bridge.start_login()  # 新增代码+CodexLoginBridgeTest：启动官方登录；如果没有这行，无法断言结果 payload。
        self.assertIs(result["ok"], True)  # 新增代码+CodexLoginBridgeTest：确认启动成功；如果没有这行，前端无法进入等待页。
        self.assertEqual("codex_cli_login", result["mode"])  # 新增代码+CodexLoginBridgeTest：确认 mode 稳定；如果没有这行，前端无法识别官方登录方式。
        self.assertEqual([["codex", "login"]], calls)  # 新增代码+CodexLoginBridgeTest：确认只调用 codex login；如果没有这行，未来代码可能绕过官方登录。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_start_login_runs_codex_login_without_token_access 到此结束；如果没有边界说明，用户不易看出启动覆盖范围。

    def test_start_login_reports_missing_codex_without_secret_fields(self) -> None:  # 新增代码+CodexLoginBridgeTest：测试函数开始，验证启动登录时 CLI 缺失也不泄露敏感字段；如果没有这段，失败 payload 可能被前端截图泄露。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginBridgeTest：导入待实现桥；如果没有这行，测试没有被测目标。

        def starter(command: list[str]) -> object:  # 新增代码+CodexLoginBridgeTest：函数段开始，模拟启动命令不存在；如果没有这段，测试无法稳定覆盖 FileNotFoundError。
            raise FileNotFoundError("codex")  # 新增代码+CodexLoginBridgeTest：抛出命令不存在；如果没有这行，桥不会进入缺 CLI 分支。
        # 新增代码+CodexLoginBridgeTest：函数段结束，starter 到此结束；如果没有边界说明，初学者不易看出这是缺 CLI 启动替身。
        bridge = CodexAuthBridge(command="codex", starter=starter)  # 新增代码+CodexLoginBridgeTest：构造注入 starter 的登录桥；如果没有这行，测试会依赖本机 PATH。
        result = bridge.start_login()  # 新增代码+CodexLoginBridgeTest：尝试启动登录；如果没有这行，无法断言失败 payload。
        serialized = str(result).lower()  # 新增代码+CodexLoginBridgeTest：序列化响应做敏感词扫描；如果没有这行，嵌套字段泄露可能漏过。
        self.assertIs(result["ok"], False)  # 新增代码+CodexLoginBridgeTest：确认缺 CLI 时启动失败；如果没有这行，前端会误进入等待页。
        self.assertEqual("codex_cli_not_found", result["error_code"])  # 新增代码+CodexLoginBridgeTest：确认稳定错误码；如果没有这行，用户无法知道需要安装 Codex CLI。
        self.assertNotIn("access_token", serialized)  # 新增代码+CodexLoginBridgeTest：确认不暴露 access token 字段；如果没有这行，截图可能泄露敏感语义。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+CodexLoginBridgeTest：确认不暴露 refresh token 字段；如果没有这行，长期凭据语义可能进入 UI。
    # 新增代码+CodexLoginBridgeTest：测试函数结束，test_start_login_reports_missing_codex_without_secret_fields 到此结束；如果没有边界说明，用户不易看出失败安全覆盖范围。
# 新增代码+CodexLoginBridgeTest：测试类段结束，CodexAuthBridgeTests 到此结束；如果没有边界说明，用户不易看出本文件只测官方 Codex 登录桥。


if __name__ == "__main__":  # 新增代码+CodexLoginBridgeTest：允许直接运行本测试文件；如果没有这行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+CodexLoginBridgeTest：启动 unittest 主程序；如果没有这行，直接运行文件不会执行测试。
