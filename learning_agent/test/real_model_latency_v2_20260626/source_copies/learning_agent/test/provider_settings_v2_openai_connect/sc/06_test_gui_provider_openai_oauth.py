import re  # 新增代码+DirectOAuthFlowTest：用于检查 PKCE verifier/challenge 字符格式；如果没有这行代码，格式断言会变成脆弱字符串比较。
import socket  # 新增代码+DirectOAuthFlowTest：用于占用临时端口测试 port preflight；如果没有这行代码，端口冲突行为无法复现。
import tempfile  # 新增代码+DirectOAuthFlowTest：用于创建隔离 token store 目录；如果没有这行代码，callback 测试会污染仓库目录。
import unittest  # 新增代码+DirectOAuthFlowTest：沿用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
import urllib.parse  # 新增代码+DirectOAuthFlowTest：用于解析授权 URL query；如果没有这行代码，测试只能做不可靠字符串包含判断。


class OpenAIProviderOAuthHelperTests(unittest.TestCase):  # 新增代码+DirectOAuthFlowTest：测试类段开始，锁定 direct OAuth helper 的安全合同；如果没有这个类，PKCE/callback 可能未经测试直接接入 GUI。
    def test_pkce_verifier_challenge_and_state_are_url_safe(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证 PKCE 和 state 格式；如果没有这段，OAuth URL 可能生成不合法参数。
        from learning_agent.app.gui_provider_openai_oauth import generate_pkce_pair, generate_state  # 新增代码+DirectOAuthFlowTest：导入待测随机 helper；如果没有这行代码，测试没有被测目标。

        first_pkce = generate_pkce_pair()  # 新增代码+DirectOAuthFlowTest：生成第一组 PKCE；如果没有这行代码，无法检查 verifier/challenge。
        second_state = generate_state()  # 新增代码+DirectOAuthFlowTest：生成第一个 state；如果没有这行代码，无法检查随机 state。
        third_state = generate_state()  # 新增代码+DirectOAuthFlowTest：生成第二个 state；如果没有这行代码，无法确认 state 不是固定值。

        self.assertRegex(first_pkce["verifier"], re.compile(r"^[A-Za-z0-9_-]{43,128}$"))  # 新增代码+DirectOAuthFlowTest：确认 verifier 符合 PKCE URL-safe 长度；如果没有这行代码，短 verifier 可能进入真实登录。
        self.assertRegex(first_pkce["challenge"], re.compile(r"^[A-Za-z0-9_-]{43,128}$"))  # 新增代码+DirectOAuthFlowTest：确认 challenge 符合 base64url；如果没有这行代码，授权服务器可能拒绝请求。
        self.assertNotEqual(first_pkce["verifier"], first_pkce["challenge"])  # 新增代码+DirectOAuthFlowTest：确认 challenge 不是直接复用 verifier；如果没有这行代码，PKCE 安全性会退化。
        self.assertNotEqual(second_state, third_state)  # 新增代码+DirectOAuthFlowTest：确认 state 具有随机性；如果没有这行代码，CSRF 防护可能是假实现。
    # 新增代码+DirectOAuthFlowTest：测试段结束，PKCE/state 格式合同到此结束；如果没有边界说明，用户不容易看出这里只测参数生成。

    def test_authorize_url_uses_openharness_originator_and_configured_client(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证授权 URL 不默认借用 OpenCode client；如果没有这段，OpenHarness 可能依赖外部项目 client id。
        from learning_agent.app.gui_provider_openai_oauth import build_authorize_url  # 新增代码+DirectOAuthFlowTest：导入授权 URL helper；如果没有这行代码，测试没有被测目标。

        url = build_authorize_url(client_id="openharness-local-test", redirect_uri="http://localhost:1455/auth/callback", code_challenge="challenge-test", state="state-test")  # 新增代码+DirectOAuthFlowTest：构造 direct OAuth 授权 URL；如果没有这行代码，query 参数无法验证。
        parsed = urllib.parse.urlparse(url)  # 新增代码+DirectOAuthFlowTest：解析 URL 主体；如果没有这行代码，host/path 无法稳定断言。
        params = urllib.parse.parse_qs(parsed.query)  # 新增代码+DirectOAuthFlowTest：解析 query 参数；如果没有这行代码，参数顺序变化会导致测试脆弱。

        self.assertEqual(parsed.scheme, "https")  # 新增代码+DirectOAuthFlowTest：确认走 HTTPS 授权站点；如果没有这行代码，错误协议可能进入浏览器。
        self.assertEqual(parsed.netloc, "auth.openai.com")  # 新增代码+DirectOAuthFlowTest：确认授权服务器是 OpenAI auth；如果没有这行代码，URL 可能被错误 base URL 污染。
        self.assertEqual(params["client_id"], ["openharness-local-test"])  # 新增代码+DirectOAuthFlowTest：确认使用显式 OpenHarness client id；如果没有这行代码，默认 OpenCode client id 会漏过。
        self.assertEqual(params["originator"], ["openharness"])  # 新增代码+DirectOAuthFlowTest：确认 originator 是 OpenHarness；如果没有这行代码，审计无法区分发起方。
        self.assertEqual(params["code_challenge_method"], ["S256"])  # 新增代码+DirectOAuthFlowTest：确认 PKCE 使用 S256；如果没有这行代码，OAuth 安全强度可能下降。
        self.assertNotIn("app_EMoamEEZ73f0CkXaXp7hrann", url)  # 新增代码+DirectOAuthFlowTest：确认不包含 OpenCode client id；如果没有这行代码，研究值可能误入默认实现。
    # 新增代码+DirectOAuthFlowTest：测试段结束，授权 URL 合同到此结束；如果没有边界说明，用户不容易看出 client id 必须显式传入。

    def test_preflight_reports_occupied_port(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证端口冲突有结构化错误；如果没有这段，localhost callback 可能静默失败。
        from learning_agent.app.gui_provider_openai_oauth import OpenAIProviderOAuthError, preflight_oauth_port  # 新增代码+DirectOAuthFlowTest：导入端口预检和错误类；如果没有这行代码，测试没有被测目标。

        occupied_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 新增代码+DirectOAuthFlowTest：创建占位 socket；如果没有这行代码，无法制造端口被占用状态。
        occupied_socket.bind(("127.0.0.1", 0))  # 新增代码+DirectOAuthFlowTest：绑定随机可用端口；如果没有这行代码，测试可能碰撞固定端口。
        occupied_socket.listen(1)  # 新增代码+DirectOAuthFlowTest：让端口进入监听状态；如果没有这行代码，preflight 可能仍能绑定。
        occupied_port = occupied_socket.getsockname()[1]  # 新增代码+DirectOAuthFlowTest：读取真实占用端口；如果没有这行代码，无法传给 preflight。
        try:  # 新增代码+DirectOAuthFlowTest：确保测试结束释放 socket；如果没有这行代码，失败时端口可能残留。
            with self.assertRaises(OpenAIProviderOAuthError) as error_context:  # 新增代码+DirectOAuthFlowTest：捕获预期端口错误；如果没有这行代码，异常会直接中断测试。
                preflight_oauth_port(port=occupied_port)  # 新增代码+DirectOAuthFlowTest：对已占用端口执行预检；如果没有这行代码，冲突路径不会运行。
        finally:  # 新增代码+DirectOAuthFlowTest：无论断言如何都释放 socket；如果没有这行代码，Windows 端口会短时间占用。
            occupied_socket.close()  # 新增代码+DirectOAuthFlowTest：关闭占位 socket；如果没有这行代码，后续测试可能受影响。
        self.assertEqual(error_context.exception.code, "oauth_port_in_use")  # 新增代码+DirectOAuthFlowTest：确认错误码稳定；如果没有这行代码，前端无法给出可读端口冲突提示。
    # 新增代码+DirectOAuthFlowTest：测试段结束，端口冲突合同到此结束；如果没有边界说明，用户不容易看出 preflight 是 callback 前置门禁。

    def test_callback_state_mismatch_fails_without_token_exchange(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证 state mismatch 不能交换 token；如果没有这段，CSRF 防护可能失效。
        from learning_agent.app.gui_provider_openai_oauth import OpenAIProviderOAuthAttempt  # 新增代码+DirectOAuthFlowTest：导入 callback 状态机；如果没有这行代码，测试没有被测目标。

        exchanges: list[dict[str, str]] = []  # 新增代码+DirectOAuthFlowTest：记录 token exchange 调用；如果没有这行代码，无法确认 mismatch 没有触发交换。
        attempt = OpenAIProviderOAuthAttempt(client_id="openharness-local-test", token_exchanger=lambda **kwargs: exchanges.append(kwargs) or {})  # 新增代码+DirectOAuthFlowTest：创建 direct OAuth attempt；如果没有这行代码，callback 无状态可测。
        attempt.handle_callback({"code": "auth-code", "state": "wrong-state"})  # 新增代码+DirectOAuthFlowTest：传入错误 state callback；如果没有这行代码，mismatch 分支不会运行。

        self.assertEqual(attempt.status, "failed")  # 新增代码+DirectOAuthFlowTest：确认 attempt 标记失败；如果没有这行代码，等待页可能继续 pending。
        self.assertEqual(attempt.error_code, "oauth_state_mismatch")  # 新增代码+DirectOAuthFlowTest：确认错误码稳定；如果没有这行代码，前端无法解释 state 失败。
        self.assertEqual(exchanges, [])  # 新增代码+DirectOAuthFlowTest：确认没有交换 token；如果没有这行代码，攻击 callback 可能触发后端请求。
    # 新增代码+DirectOAuthFlowTest：测试段结束，state mismatch 合同到此结束；如果没有边界说明，用户不容易看出这里是安全失败路径。

    def test_duplicate_callback_is_ignored_after_success(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证重复 callback 不会重复写 token；如果没有这段，浏览器刷新成功页可能导致二次写入。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthFlowTest：导入 fake token store；如果没有这行代码，测试需要真实 DPAPI。
        from learning_agent.app.gui_provider_openai_oauth import OpenAIProviderOAuthAttempt  # 新增代码+DirectOAuthFlowTest：导入 callback 状态机；如果没有这行代码，测试没有被测目标。

        exchange_count = {"value": 0}  # 新增代码+DirectOAuthFlowTest：记录 token exchange 次数；如果没有这行代码，重复 callback 是否重入不可见。

        def exchanger(**_kwargs: str) -> dict[str, object]:  # 新增代码+DirectOAuthFlowTest：函数段开始，模拟 token exchange 成功；如果没有这段，callback 成功路径无法验证。
            exchange_count["value"] += 1  # 新增代码+DirectOAuthFlowTest：累加调用次数；如果没有这行代码，重复交换无法断言。
            return {"access_token": "a", "refresh_token": "r", "id_token": "i", "expires_at": 1782500000000, "account_id": "acct"}  # 新增代码+DirectOAuthFlowTest：返回 token 样本；如果没有这行代码，store 无法保存 connected 状态。
        # 新增代码+DirectOAuthFlowTest：函数段结束，exchanger 到此结束；如果没有边界说明，用户不容易看出它是 fake 网络层。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthFlowTest：创建隔离 token store 目录；如果没有这行代码，测试会在仓库里留下 token 文件。
            store = make_fake_token_store(config_dir=directory)  # 新增代码+DirectOAuthFlowTest：创建隔离 fake store；如果没有这行代码，token 保存没有测试替身。
            attempt = OpenAIProviderOAuthAttempt(client_id="openharness-local-test", token_exchanger=exchanger, token_store=store)  # 新增代码+DirectOAuthFlowTest：创建带 fake exchanger/store 的 attempt；如果没有这行代码，callback 无法保存 token。
            callback = {"code": "auth-code", "state": attempt.state}  # 新增代码+DirectOAuthFlowTest：构造合法 callback 参数；如果没有这行代码，成功路径无法触发。
            first_page = attempt.handle_callback(callback)  # 新增代码+DirectOAuthFlowTest：第一次处理 callback；如果没有这行代码，attempt 不会 complete。
            second_page = attempt.handle_callback(callback)  # 新增代码+DirectOAuthFlowTest：重复处理同一 callback；如果没有这行代码，幂等行为无法验证。

        self.assertEqual(attempt.status, "complete")  # 新增代码+DirectOAuthFlowTest：确认最终状态 complete；如果没有这行代码，重复 callback 可能破坏状态。
        self.assertEqual(exchange_count["value"], 1)  # 新增代码+DirectOAuthFlowTest：确认只交换一次 token；如果没有这行代码，刷新成功页会重复写入。
        self.assertIn("Authorization Successful", first_page)  # 新增代码+DirectOAuthFlowTest：确认第一次 callback 返回成功页；如果没有这行代码，用户浏览器没有成功反馈。
        self.assertIn("Authorization Successful", second_page)  # 新增代码+DirectOAuthFlowTest：确认重复 callback 仍给安全成功页；如果没有这行代码，刷新页面可能显示误导失败。
    # 新增代码+DirectOAuthFlowTest：测试段结束，重复 callback 合同到此结束；如果没有边界说明，用户不容易看出成功页是幂等的。

    def test_expired_attempt_callback_returns_expired_page(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证用户关闭 dialog 后 callback 不保存 token；如果没有这段，取消后的浏览器回调可能重新登录。
        from learning_agent.app.gui_provider_openai_oauth import OpenAIProviderOAuthAttempt  # 新增代码+DirectOAuthFlowTest：导入 callback 状态机；如果没有这行代码，测试没有被测目标。

        attempt = OpenAIProviderOAuthAttempt(client_id="openharness-local-test", token_exchanger=lambda **_kwargs: {})  # 新增代码+DirectOAuthFlowTest：创建 attempt；如果没有这行代码，callback 无状态可测。
        attempt.cancel()  # 新增代码+DirectOAuthFlowTest：模拟用户关闭连接弹窗；如果没有这行代码，expired 分支不会运行。
        page = attempt.handle_callback({"code": "auth-code", "state": attempt.state})  # 新增代码+DirectOAuthFlowTest：取消后收到浏览器 callback；如果没有这行代码，过期页面无法断言。

        self.assertEqual(attempt.status, "expired")  # 新增代码+DirectOAuthFlowTest：确认状态保持 expired；如果没有这行代码，取消后 callback 可能改成 complete。
        self.assertIn("Authorization Expired", page)  # 新增代码+DirectOAuthFlowTest：确认浏览器显示过期页；如果没有这行代码，用户不知道要回 GUI 重新开始。
    # 新增代码+DirectOAuthFlowTest：测试段结束，expired callback 合同到此结束；如果没有边界说明，用户不容易看出取消会阻止保存 token。

    def test_token_exchange_failure_marks_attempt_failed(self) -> None:  # 新增代码+DirectOAuthFlowTest：测试段开始，验证 token exchange 500 会失败；如果没有这段，后端错误可能让等待页永久 pending。
        from learning_agent.app.gui_provider_openai_oauth import OpenAIProviderOAuthAttempt  # 新增代码+DirectOAuthFlowTest：导入 callback 状态机；如果没有这行代码，测试没有被测目标。

        def failing_exchanger(**_kwargs: str) -> dict[str, object]:  # 新增代码+DirectOAuthFlowTest：函数段开始，模拟 token exchange 失败；如果没有这段，远端 500 无法复现。
            raise RuntimeError("HTTP 500")  # 新增代码+DirectOAuthFlowTest：抛出远端失败；如果没有这行代码，失败路径不会运行。
        # 新增代码+DirectOAuthFlowTest：函数段结束，failing_exchanger 到此结束；如果没有边界说明，用户不容易看出它是网络失败替身。

        attempt = OpenAIProviderOAuthAttempt(client_id="openharness-local-test", token_exchanger=failing_exchanger)  # 新增代码+DirectOAuthFlowTest：创建 attempt；如果没有这行代码，callback 无状态可测。
        page = attempt.handle_callback({"code": "auth-code", "state": attempt.state})  # 新增代码+DirectOAuthFlowTest：处理合法 state 但失败 exchange；如果没有这行代码，失败路径无法断言。

        self.assertEqual(attempt.status, "failed")  # 新增代码+DirectOAuthFlowTest：确认 attempt 标记失败；如果没有这行代码，GUI 可能继续轮询。
        self.assertEqual(attempt.error_code, "oauth_token_exchange_failed")  # 新增代码+DirectOAuthFlowTest：确认错误码稳定；如果没有这行代码，前端无法给出可读失败说明。
        self.assertIn("Authorization Failed", page)  # 新增代码+DirectOAuthFlowTest：确认浏览器显示失败页；如果没有这行代码，用户不知道登录没有成功。
    # 新增代码+DirectOAuthFlowTest：测试段结束，token exchange 失败合同到此结束；如果没有边界说明，用户不容易看出远端失败不会伪装成功。


if __name__ == "__main__":  # 新增代码+DirectOAuthFlowTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+DirectOAuthFlowTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
