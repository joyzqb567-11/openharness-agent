import json  # 新增代码+DesktopGUISecurityTest: 解析 GUI bridge JSON 响应；如果没有这行代码，测试无法检查结构化错误。
import tempfile  # 新增代码+DesktopGUISecurityTest: 创建隔离工作区；如果没有这行代码，测试会污染真实项目目录。
import threading  # 新增代码+DesktopGUISecurityTest: 后台启动 HTTP server；如果没有这行代码，测试请求会阻塞。
import unittest  # 新增代码+DesktopGUISecurityTest: 使用 unittest 让计划命令能发现测试；如果没有这行代码，安全合同不会执行。
import urllib.error  # 新增代码+DesktopGUISecurityTest: 捕获 HTTPError；如果没有这行代码，拒绝场景无法读取响应体。
import urllib.request  # 新增代码+DesktopGUISecurityTest: 使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+DesktopGUISecurityTest: 使用 Path 传入工作区；如果没有这行代码，路径语义不清楚。


class GuiBridgeSecurityContractTests(unittest.TestCase):  # 新增代码+DesktopGUISecurityTest: 测试类段开始，锁定 GUI bridge 安全合同；如果没有这个类，安全门禁不会被 unittest 执行。
    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUISecurityTest: helper 段开始，启动带 token 的测试 server；如果没有这个 helper，每个测试会重复端口和线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUISecurityTest: 导入 GUI bridge server 构造器；如果没有这行代码，安全测试无法启动目标服务。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUISecurityTest: 绑定随机端口并设置 token；如果没有这行代码，测试无法验证认证。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUISecurityTest: 创建后台服务线程；如果没有这行代码，测试无法发 HTTP 请求。
        thread.start()  # 新增代码+DesktopGUISecurityTest: 启动服务线程；如果没有这行代码，后续连接会失败。
        return server  # 新增代码+DesktopGUISecurityTest: 返回 server 供测试读取端口和关闭；如果没有这行代码，调用方拿不到服务对象。
    # 新增代码+DesktopGUISecurityTest: helper 段结束，_start_server 到此结束；如果没有这个边界说明，用户不容易看出它只负责启动测试服务。

    def _url(self, server, path: str) -> str:  # 新增代码+DesktopGUISecurityTest: helper 段开始，拼接测试 URL；如果没有这段函数，端口读取会散落在各测试中。
        host, port = server.server_address  # 新增代码+DesktopGUISecurityTest: 读取 server 实际地址；如果没有这行代码，随机端口无法用于请求。
        return f"http://{host}:{port}{path}"  # 新增代码+DesktopGUISecurityTest: 返回完整 URL；如果没有这行代码，urllib 无法连接目标端点。
    # 新增代码+DesktopGUISecurityTest: helper 段结束，_url 到此结束；如果没有这个边界说明，用户不容易看出它只负责 URL 拼接。

    def _read_http_error(self, error: urllib.error.HTTPError) -> dict[str, object]:  # 新增代码+DesktopGUISecurityTest: helper 段开始，读取结构化错误响应；如果没有这段函数，拒绝测试只能看状态码。
        return json.loads(error.read().decode("utf-8"))  # 新增代码+DesktopGUISecurityTest: 把错误响应解析为 JSON；如果没有这行代码，无法确认错误不泄漏路径。
    # 新增代码+DesktopGUISecurityTest: helper 段结束，_read_http_error 到此结束；如果没有这个边界说明，用户不容易看出它只负责错误读取。

    def test_health_does_not_require_token(self) -> None:  # 新增代码+DesktopGUISecurityTest: 验证健康检查不要求 token；如果没有这段测试，Electron 启动前探活会被认证挡住。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISecurityTest: 创建临时工作区；如果没有这行代码，测试会写入真实 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUISecurityTest: 启动测试 server；如果没有这行代码，测试没有目标。
            try:  # 新增代码+DesktopGUISecurityTest: 确保服务关闭；如果没有这行代码，失败时端口会泄漏。
                with urllib.request.urlopen(self._url(server, "/health"), timeout=5) as response:  # 新增代码+DesktopGUISecurityTest: 无 token 请求 health；如果没有这行代码，无法验证例外端点。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUISecurityTest: 解析 health 响应；如果没有这行代码，无法断言 ok 字段。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUISecurityTest: 确认 health 成功；如果没有这行断言，错误响应可能误过。
            finally:  # 新增代码+DesktopGUISecurityTest: 清理 server；如果没有这行代码，后台线程可能残留。
                server.shutdown()  # 新增代码+DesktopGUISecurityTest: 停止 serve_forever；如果没有这行代码，测试进程可能等待。
                server.server_close()  # 新增代码+DesktopGUISecurityTest: 释放 socket；如果没有这行代码，Windows 端口可能残留占用。
    # 新增代码+DesktopGUISecurityTest: 测试方法结束；如果没有这个边界说明，用户不容易看出 health 例外范围。

    def test_bootstrap_requires_correct_token(self) -> None:  # 新增代码+DesktopGUISecurityTest: 验证 bootstrap 需要正确 token；如果没有这段测试，本机其它进程可能读取 GUI 状态。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISecurityTest: 创建临时工作区；如果没有这行代码，测试会污染真实目录。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUISecurityTest: 启动测试 server；如果没有这行代码，测试没有目标。
            try:  # 新增代码+DesktopGUISecurityTest: 确保 server 关闭；如果没有这行代码，失败时端口会泄漏。
                with self.assertRaises(urllib.error.HTTPError) as missing_token:  # 新增代码+DesktopGUISecurityTest: 断言缺 token 被拒；如果没有这行代码，未授权访问可能误过。
                    urllib.request.urlopen(self._url(server, "/v1/gui/bootstrap"), timeout=5)  # 新增代码+DesktopGUISecurityTest: 发起缺 token 请求；如果没有这行代码，无法触发拒绝路径。
                self.assertEqual(missing_token.exception.code, 401)  # 新增代码+DesktopGUISecurityTest: 确认状态码为 401；如果没有这行断言，错误类型可能不对。
                self.assertEqual(self._read_http_error(missing_token.exception)["code"], "unauthorized")  # 新增代码+DesktopGUISecurityTest: 确认错误码结构化；如果没有这行断言，前端无法稳定展示。
                wrong_request = urllib.request.Request(self._url(server, "/v1/gui/bootstrap"), headers={"X-OpenHarness-Desktop-Token": "wrong"})  # 新增代码+DesktopGUISecurityTest: 构造错误 token 请求；如果没有这行代码，无法验证错误 token。
                with self.assertRaises(urllib.error.HTTPError) as wrong_token:  # 新增代码+DesktopGUISecurityTest: 断言错误 token 被拒；如果没有这行代码，认证判断可能失效。
                    urllib.request.urlopen(wrong_request, timeout=5)  # 新增代码+DesktopGUISecurityTest: 发起错误 token 请求；如果没有这行代码，无法触发拒绝路径。
                self.assertEqual(wrong_token.exception.code, 401)  # 新增代码+DesktopGUISecurityTest: 确认错误 token 状态码；如果没有这行断言，安全错误可能不一致。
                good_request = urllib.request.Request(self._url(server, "/v1/gui/bootstrap"), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUISecurityTest: 构造正确 token 请求；如果没有这行代码，无法验证允许路径。
                with urllib.request.urlopen(good_request, timeout=5) as response:  # 新增代码+DesktopGUISecurityTest: 发起正确 token 请求；如果没有这行代码，无法证明授权可用。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUISecurityTest: 解析成功响应；如果没有这行代码，无法断言 ok 字段。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUISecurityTest: 确认授权成功；如果没有这行断言，正确 token 可能仍失败。
            finally:  # 新增代码+DesktopGUISecurityTest: 清理 server；如果没有这行代码，后台线程可能残留。
                server.shutdown()  # 新增代码+DesktopGUISecurityTest: 停止 server；如果没有这行代码，测试进程可能等待。
                server.server_close()  # 新增代码+DesktopGUISecurityTest: 释放 socket；如果没有这行代码，端口可能残留占用。
    # 新增代码+DesktopGUISecurityTest: 测试方法结束；如果没有这个边界说明，用户不容易看出 token 合同范围。

    def test_unexpected_origin_is_rejected_without_path_leak(self) -> None:  # 新增代码+DesktopGUISecurityTest: 验证异常 Origin 被拒且不泄漏路径；如果没有这段测试，恶意本机页面可能调用 bridge。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISecurityTest: 创建临时工作区；如果没有这行代码，测试会污染真实目录。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUISecurityTest: 启动测试 server；如果没有这行代码，测试没有目标。
            try:  # 新增代码+DesktopGUISecurityTest: 确保 server 关闭；如果没有这行代码，失败时端口会泄漏。
                request = urllib.request.Request(self._url(server, "/v1/gui/bootstrap"), headers={"X-OpenHarness-Desktop-Token": "test-token", "Origin": "http://evil.local"})  # 新增代码+DesktopGUISecurityTest: 构造异常 Origin 请求；如果没有这行代码，无法验证 Origin 门禁。
                with self.assertRaises(urllib.error.HTTPError) as rejected:  # 新增代码+DesktopGUISecurityTest: 断言异常 Origin 被拒；如果没有这行代码，Origin 检查可能失效。
                    urllib.request.urlopen(request, timeout=5)  # 新增代码+DesktopGUISecurityTest: 发起异常 Origin 请求；如果没有这行代码，无法触发拒绝路径。
                payload = self._read_http_error(rejected.exception)  # 新增代码+DesktopGUISecurityTest: 读取结构化错误；如果没有这行代码，无法检查错误内容。
                self.assertEqual(rejected.exception.code, 403)  # 新增代码+DesktopGUISecurityTest: 确认状态码为 403；如果没有这行断言，前端无法区分认证和来源错误。
                self.assertEqual(payload["code"], "origin_forbidden")  # 新增代码+DesktopGUISecurityTest: 确认错误码稳定；如果没有这行断言，UI 难以给出清楚提示。
                self.assertNotIn(str(Path(directory)), json.dumps(payload, ensure_ascii=False))  # 新增代码+DesktopGUISecurityTest: 确认错误不泄漏工作区路径；如果没有这行断言，安全错误可能暴露本机路径。
            finally:  # 新增代码+DesktopGUISecurityTest: 清理 server；如果没有这行代码，后台线程可能残留。
                server.shutdown()  # 新增代码+DesktopGUISecurityTest: 停止 server；如果没有这行代码，测试进程可能等待。
                server.server_close()  # 新增代码+DesktopGUISecurityTest: 释放 socket；如果没有这行代码，端口可能残留占用。
    # 新增代码+DesktopGUISecurityTest: 测试方法结束；如果没有这个边界说明，用户不容易看出 Origin 合同范围。

    def test_allowed_vite_origin_receives_cors_headers_and_preflight(self) -> None:  # 新增代码+DesktopGUICorsTest: 测试方法开始，验证真实 Vite 前端来源能通过 CORS；如果没有这段测试，GUI 可见验收可能再次被浏览器跨源策略挡住。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUICorsTest: 创建临时工作区；如果没有这行代码，测试会污染真实项目 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUICorsTest: 启动测试 bridge；如果没有这行代码，预检和 bootstrap 请求没有目标服务。
            try:  # 新增代码+DesktopGUICorsTest: 确保 server 最终关闭；如果没有这行代码，失败时后台线程可能残留。
                options_request = urllib.request.Request(self._url(server, "/v1/gui/messages"), method="OPTIONS", headers={"Origin": "http://127.0.0.1:5177", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type, x-openharness-desktop-token"})  # 新增代码+DesktopGUICorsTest: 构造浏览器会先发的 POST 预检请求；如果没有这行代码，无法证明真实 GUI 的 messages 请求会被允许。
                with urllib.request.urlopen(options_request, timeout=5) as options_response:  # 新增代码+DesktopGUICorsTest: 执行 OPTIONS 预检；如果没有这行代码，测试只覆盖不到浏览器关键路径。
                    self.assertEqual(options_response.status, 204)  # 新增代码+DesktopGUICorsTest: 确认预检无响应体成功；如果没有这行断言，错误状态可能误过。
                    self.assertEqual(options_response.getheader("Access-Control-Allow-Origin"), "http://127.0.0.1:5177")  # 新增代码+DesktopGUICorsTest: 确认只回写允许来源；如果没有这行断言，浏览器仍可能拦截响应。
                    self.assertIn("X-OpenHarness-Desktop-Token", options_response.getheader("Access-Control-Allow-Headers", ""))  # 新增代码+DesktopGUICorsTest: 确认 token header 被允许；如果没有这行断言，POST 会在预检阶段失败。
                    self.assertIn("POST", options_response.getheader("Access-Control-Allow-Methods", ""))  # 新增代码+DesktopGUICorsTest: 确认 POST 方法被允许；如果没有这行断言，消息提交不会真正发出。
                bootstrap_request = urllib.request.Request(self._url(server, "/v1/gui/bootstrap"), headers={"X-OpenHarness-Desktop-Token": "test-token", "Origin": "http://127.0.0.1:5177"})  # 新增代码+DesktopGUICorsTest: 构造带合法 Origin 和 token 的 bootstrap 请求；如果没有这行代码，无法验证普通响应也会带 CORS 头。
                with urllib.request.urlopen(bootstrap_request, timeout=5) as bootstrap_response:  # 新增代码+DesktopGUICorsTest: 执行 bootstrap 请求；如果没有这行代码，测试无法证明首屏 fetch 能读响应。
                    payload = json.loads(bootstrap_response.read().decode("utf-8"))  # 新增代码+DesktopGUICorsTest: 解析 bootstrap JSON；如果没有这行代码，无法确认响应仍是业务 payload。
                    self.assertEqual(bootstrap_response.getheader("Access-Control-Allow-Origin"), "http://127.0.0.1:5177")  # 新增代码+DesktopGUICorsTest: 确认业务响应携带 CORS 允许头；如果没有这行断言，前端读取会失败。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUICorsTest: 确认 CORS 修复没有破坏 bootstrap 合同；如果没有这行断言，响应内容错误可能被忽略。
            finally:  # 新增代码+DesktopGUICorsTest: 清理 server；如果没有这行代码，测试失败后端口可能残留。
                server.shutdown()  # 新增代码+DesktopGUICorsTest: 停止后台 HTTP server；如果没有这行代码，测试进程可能等待。
                server.server_close()  # 新增代码+DesktopGUICorsTest: 释放 socket；如果没有这行代码，Windows 随机端口可能短暂占用。
    # 新增代码+DesktopGUICorsTest: 测试方法结束；如果没有这个边界说明，用户不容易看出本测试只锁定 CORS 浏览器合同。
# 新增代码+DesktopGUISecurityTest: 测试类段结束，GuiBridgeSecurityContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测安全合同。


if __name__ == "__main__":  # 新增代码+DesktopGUISecurityTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时不会执行测试。
    unittest.main()  # 新增代码+DesktopGUISecurityTest: 启动 unittest；如果没有这行代码，直接运行文件不会进入测试 runner。
